"""!
@file test_safety_kernel_orchestrator.py
@brief IU-0009(ARC-0009 안전 커널 평가 오케스트레이터) 함수 계약 검증
       (ENG-SWE3-001 5장/6.6절/10.2절, SWR-013/SWR-021 조율).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.domain.constants import WARNING_CODE_ORCHESTRATION_ERROR
from ngv.domain.types import (
    ArbitrationCommand,
    CrashStatus,
    FieldValidationResult,
    LockCommand,
    NormalizedSafetyInput,
    SystemState,
)
from ngv.core.approach_risk_evaluator import ApproachRiskEvaluator
from ngv.core.approach_risk_override_manager import ApproachRiskOverrideManager
from ngv.core.command_arbiter import CommandArbiter
from ngv.core.crash_monitor import CrashMonitor
from ngv.core.fire_overtemp_occupant_monitor import FireOvertempOccupantMonitor
from ngv.core.freshness_monitor import FreshnessMonitor
from ngv.core.output_hold_actuator import OutputHoldActuator
from ngv.core.state_manager import StateManager
from ngv.adapters.decision_logger_stub import DecisionLoggerStub
from ngv.adapters.notification_adapter import NotificationAdapter
from ngv.adapters.output_actuator_adapter import OutputActuatorAdapter
from ngv.app.safety_kernel_orchestrator import SafetyKernelOrchestrator

from testsupport.orchestrator_factory import buildOrchestrator


def validField(value):
    """테스트 헬퍼 — 유효한 FieldValidationResult를 만든다."""
    return FieldValidationResult(value=value, valid=True, rawValue=value)


def invalidField(rawValue, errorReason="TYPE_ERROR"):
    """테스트 헬퍼 — 무효한 FieldValidationResult를 만든다."""
    return FieldValidationResult(value=None, valid=False, rawValue=rawValue, errorReason=errorReason)


def normalizedInput(
    timestampField,
    ignitionField,
    sensorFaultField,
    crashStatusField=None,
    leftApproachRiskField=None,
    rightApproachRiskField=None,
    fireField=None,
    overtempField=None,
    adultField=None,
):
    """테스트 헬퍼 — NormalizedSafetyInput을 만든다(Phase2 6필드는 기본값을 그대로 사용 가능)."""
    kwargs = {
        "sourceTimestampField": timestampField,
        "ignitionOnField": ignitionField,
        "sensorFaultField": sensorFaultField,
    }
    optionalFields = {
        "crashStatusField": crashStatusField,
        "leftApproachRiskField": leftApproachRiskField,
        "rightApproachRiskField": rightApproachRiskField,
        "fireField": fireField,
        "overtempField": overtempField,
        "adultField": adultField,
    }
    for name, value in optionalFields.items():
        if value is not None:
            kwargs[name] = value
    return NormalizedSafetyInput(**kwargs)


def recordCalls(instance, methodName, tag, callLog):
    """!
    @brief 실제 인스턴스의 메서드를 감싸 호출 순서만 기록하고 원본 로직에 그대로 위임한다.

    mock 라이브러리를 쓰지 않고 실제 프로덕션 객체의 실제 메서드를 그대로 실행시키면서
    호출 순서만 부가로 관찰하기 위한 최소 계측(instrumentation)이다.
    """
    original = getattr(instance, methodName)

    def wrapped(*args, **kwargs):
        callLog.append(tag)
        return original(*args, **kwargs)

    setattr(instance, methodName, wrapped)
    return instance


class RaisingFreshnessMonitor(FreshnessMonitor):
    """2-1~2-4단계 예외 강제 시나리오 전용 — evaluate() 호출 시 항상 예외를 던진다."""

    def evaluate(self, sourceTimestampField, nowS):
        raise RuntimeError("freshness monitor failure (test double)")


class RaisingOutputActuatorAdapter(OutputActuatorAdapter):
    """2-5단계 예외 격리 시나리오 전용 — publish() 호출 시 항상 예외를 던진다."""

    def publish(self, confirmedOutput):
        raise RuntimeError("publish failure (test double)")


class RaisingNotificationAdapter(NotificationAdapter):
    """2-6단계 예외 격리 시나리오 전용 — publishWarning() 호출 시 항상 예외를 던진다."""

    def publishWarning(self, stateResult):
        raise RuntimeError("publishWarning failure (test double)")


class RaisingDecisionLogger(DecisionLoggerStub):
    """2-7단계 예외 격리 시나리오 전용 — log() 호출 시 항상 예외를 던진다."""

    def log(self, entry):
        raise RuntimeError("log failure (test double)")


class TestSafetyKernelOrchestratorEvaluateCycleNormalPath(unittest.TestCase):
    """IU-0009.evaluateCycle() 정상 경로 계약 검증."""

    def testNormalPathReturnsNormalStateWithoutError(self):
        """!
        @brief 유효하고 신선한 입력에서는 NORMAL 상태, errorOccurred=False를 반환한다.
        @technique 유스케이스 테스트(Use Case Testing) — 기본 흐름(정상 평가주기)
        @case Positive — 정상 경로 전체 조율이 올바른 CycleResult를 산출하는지 검증
        @breaks 정상 입력에서도 errorOccurred=True나 FAULT를 반환하는 회귀
        """
        orchestrator = buildOrchestrator()
        input1 = normalizedInput(validField(1.000), validField(True), validField(False))

        result = orchestrator.evaluateCycle(input1, 1.000)

        self.assertEqual(result.stateResult.state, SystemState.NORMAL)
        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)

    def testSensorFaultInputForcesFaultAndFreezesOutput(self):
        """!
        @brief sensor_fault=True가 실제 StateManager/OutputHoldActuator를 거쳐 fail-freeze로 이어진다.
        @technique 유스케이스 테스트(Use Case Testing) — SWR-021(b) 대안 흐름(고장 신호)
        @case Negative — 하위 컴포넌트 연계(freshness->state->confirm)가 올바르게 배선됐는지 검증
        @breaks sensor_fault=True에도 NORMAL이 반환되거나 출력이 바뀌는 회귀
        """
        orchestrator = buildOrchestrator()
        input1 = normalizedInput(validField(1.000), validField(True), validField(True))

        result = orchestrator.evaluateCycle(input1, 1.000)

        self.assertEqual(result.stateResult.state, SystemState.FAULT)
        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)

    def testFixedCallOrderAcrossAllSubComponents(self):
        """!
        @brief IU-0002->0003->0010->0011->0012->0013->0005->0004->0006->0007->0008 고정 순서로
               정확히 1회씩 호출한다(Phase2 갱신, 3장 상세 호출관계).
        @technique 유스케이스 테스트(Use Case Testing) — 3장 상세 호출관계의 고정 순서 계약
        @case Positive — 통합 순서(ENG-SWE2-001 11장/ENG-SWE3-001 3장)를 그대로 구현했는지 검증
        @breaks 호출 순서가 뒤바뀌거나 Phase2 신규 단계가 생략/중복되는 회귀
        """
        callLog = []
        freshnessMonitor = recordCalls(FreshnessMonitor(), "evaluate", "IU-0002", callLog)
        stateManager = recordCalls(StateManager(), "evaluate", "IU-0003", callLog)
        crashMonitor = recordCalls(CrashMonitor(), "evaluate", "IU-0010", callLog)
        approachRiskEvaluator = recordCalls(ApproachRiskEvaluator(), "evaluate", "IU-0011", callLog)
        overrideManager = recordCalls(ApproachRiskOverrideManager(), "decide", "IU-0012", callLog)
        fireMonitor = recordCalls(FireOvertempOccupantMonitor(), "evaluate", "IU-0013", callLog)
        commandArbiter = recordCalls(CommandArbiter(), "arbitrate", "IU-0005", callLog)
        outputHoldActuator = recordCalls(OutputHoldActuator(), "confirm", "IU-0004", callLog)
        outputAdapter = recordCalls(OutputActuatorAdapter(), "publish", "IU-0006", callLog)
        notificationAdapter = recordCalls(NotificationAdapter(), "publishWarning", "IU-0007", callLog)
        decisionLogger = recordCalls(DecisionLoggerStub(), "log", "IU-0008", callLog)
        orchestrator = buildOrchestrator(
            freshnessMonitor=freshnessMonitor,
            stateManager=stateManager,
            outputHoldActuator=outputHoldActuator,
            commandArbiter=commandArbiter,
            outputAdapter=outputAdapter,
            notificationAdapter=notificationAdapter,
            decisionLogger=decisionLogger,
            crashMonitor=crashMonitor,
            approachRiskEvaluator=approachRiskEvaluator,
            overrideManager=overrideManager,
            fireMonitor=fireMonitor,
        )
        input1 = normalizedInput(validField(1.000), validField(True), validField(False))

        orchestrator.evaluateCycle(input1, 1.000)

        self.assertEqual(
            callLog,
            [
                "IU-0002",
                "IU-0003",
                "IU-0010",
                "IU-0011",
                "IU-0012",
                "IU-0013",
                "IU-0005",
                "IU-0004",
                "IU-0006",
                "IU-0007",
                "IU-0008",
            ],
        )

    def testComposesInputValidFromTimestampAndIgnitionFieldsForArbiter(self):
        """!
        @brief 7장 결정표 D대로 sourceTimestampField.valid AND ignitionOnField.valid를 합성해 Arbiter에 전달한다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 D(무효 timestamp -> inputValid=False)
        @case Negative — sensorFaultField.valid를 합성에서 제외하고 나머지 두 필드만 사용하는지 검증
        @breaks inputValid을 항상 True로 고정하거나 sensorFaultField까지 잘못 합성하는 회귀
        """
        receivedInputValid = []
        commandArbiter = CommandArbiter()
        originalArbitrate = commandArbiter.arbitrate

        def spyArbitrate(stateResult, inputValid, candidateCommands=None):
            receivedInputValid.append(inputValid)
            return originalArbitrate(stateResult, inputValid, candidateCommands)

        commandArbiter.arbitrate = spyArbitrate
        orchestrator = buildOrchestrator(commandArbiter=commandArbiter)
        input1 = normalizedInput(invalidField(None), validField(True), validField(False))

        orchestrator.evaluateCycle(input1, 1.000)

        self.assertEqual(receivedInputValid, [False])


class TestSafetyKernelOrchestratorEvaluateCycleErrorHandling(unittest.TestCase):
    """IU-0009.evaluateCycle() 10.2절 오류 처리 정책 검증."""

    def testCoreStageExceptionForcesFaultAndDoesNotPropagate(self):
        """!
        @brief 2-1~2-4단계 예외 발생 시 StateResult를 FAULT로 강제하고 예외를 전파하지 않는다.
        @technique 오류추측(Error Guessing) — 핵심 판정 경로 컴포넌트 실패 주입
        @case Negative — 10.2절 방어적 정책(강제 FAULT, errorOccurred=True)을 검증
        @breaks 하위 컴포넌트 예외가 evaluateCycle() 밖으로 전파되는 회귀(안전 커널 전체 중단)
        """
        orchestrator = buildOrchestrator(freshnessMonitor=RaisingFreshnessMonitor())
        input1 = normalizedInput(validField(1.000), validField(True), validField(False))

        result = orchestrator.evaluateCycle(input1, 1.000)

        self.assertEqual(result.stateResult.state, SystemState.FAULT)
        self.assertEqual(result.stateResult.warningReasonCode, WARNING_CODE_ORCHESTRATION_ERROR)
        self.assertTrue(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)

    def testPublishStageExceptionsDoNotAffectAlreadyConfirmedSafeOutput(self):
        """!
        @brief 2-5~2-7단계(발행/로깅) 예외는 개별 격리되어 2-1~2-4단계 결과에 영향을 주지 않는다.
        @technique 오류추측(Error Guessing) — QM 어댑터(발행/로깅) 실패 동시 주입
        @case Negative — 발행 실패가 이미 확정된 안전 출력을 무효화하지 않는지 검증
        @breaks 발행 단계 예외가 evaluateCycle() 밖으로 전파되거나 판정 결과를 훼손하는 회귀
        """
        orchestrator = buildOrchestrator(
            outputAdapter=RaisingOutputActuatorAdapter(),
            notificationAdapter=RaisingNotificationAdapter(),
            decisionLogger=RaisingDecisionLogger(),
        )
        input1 = normalizedInput(validField(1.000), validField(True), validField(False))

        result = orchestrator.evaluateCycle(input1, 1.000)

        self.assertEqual(result.stateResult.state, SystemState.NORMAL)
        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


class TestSafetyKernelOrchestratorPhase2Wiring(unittest.TestCase):
    """IU-0009 Phase2 신규 호출/조립 단계 종단 검증(실제 IU-0010~0013 협력 객체 사용)."""

    def testCrashConfirmedProducesReleaseOnBothDoors(self):
        """!
        @brief crash_status=CONFIRMED는 실제 체인을 거쳐 양쪽 문 모두 RELEASE로 확정된다.
        @technique 유스케이스 테스트(Use Case Testing) — SWR-007(a) 긴급해제 종단 경로
        @case Positive — IU-0010->assembleCandidateCommands->IU-0005->IU-0004 실제 배선을 검증
        @breaks CONFIRMED 입력에도 LOCK이 유지되는 회귀(긴급해제 배선 누락)
        """
        orchestrator = buildOrchestrator()
        input1 = normalizedInput(
            validField(1.000),
            validField(True),
            validField(False),
            crashStatusField=validField(CrashStatus.CONFIRMED),
        )

        result = orchestrator.evaluateCycle(input1, 1.000)

        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)

    def testLeftApproachRiskLocksOnlyLeftDoor(self):
        """!
        @brief 좌측 접근위험만 True이면 좌측만 LOCK 유지, 우측은 영향받지 않는다(SWR-009 종단 검증).
        @technique 유스케이스 테스트(Use Case Testing) — SWR-005 좌측 억제 종단 경로
        @case Positive — IU-0011->assembleCandidateCommands->IU-0005 실제 배선을 검증
        @breaks 좌측 접근위험이 우측 출력에까지 영향을 주는 회귀
        """
        orchestrator = buildOrchestrator()
        input1 = normalizedInput(
            validField(1.000),
            validField(True),
            validField(False),
            leftApproachRiskField=validField(True),
            rightApproachRiskField=validField(False),
        )

        result = orchestrator.evaluateCycle(input1, 1.000)

        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)

    def testFireDetectedProducesReleaseOnBothDoors(self):
        """!
        @brief fire_detected=True는 실제 체인을 거쳐 양쪽 문 모두 RELEASE로 확정된다(SWR-017a).
        @technique 유스케이스 테스트(Use Case Testing) — SWR-017 강제해제 종단 경로
        @case Positive — IU-0013->assembleCandidateCommands->IU-0005->IU-0004 실제 배선을 검증
        @breaks fire_detected=True에도 LOCK이 유지되는 회귀(강제해제 배선 누락)
        """
        orchestrator = buildOrchestrator()
        input1 = normalizedInput(
            validField(1.000),
            validField(True),
            validField(False),
            fireField=validField(True),
            overtempField=validField(False),
            adultField=validField(False),
        )

        result = orchestrator.evaluateCycle(input1, 1.000)

        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)

    def testStateFaultBlocksPhase2CandidatesEvenWithCrashConfirmed(self):
        """!
        @brief state==FAULT이면 crash_status=CONFIRMED 후보도 전부 차단된다(8.5절 FAULT 최우선 확정).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 I, FAULT와 강한 Phase2 신호 동시 발생
        @case Negative — FAULT가 Phase2 후보보다 항상 우선한다는 종단 배선을 검증
        @breaks FAULT 상태에서도 강한 Phase2 신호가 출력을 바꿔버리는 회귀
        """
        orchestrator = buildOrchestrator()
        input1 = normalizedInput(
            validField(1.000),
            validField(True),
            validField(True),
            crashStatusField=validField(CrashStatus.CONFIRMED),
        )

        result = orchestrator.evaluateCycle(input1, 1.000)

        self.assertEqual(result.stateResult.state, SystemState.FAULT)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


class TestSafetyKernelOrchestratorAssembleCandidateCommands(unittest.TestCase):
    """IU-0009.assembleCandidateCommands() 결정표 J 조립 계약 검증(정적 메서드, 6.7절)."""

    def testIncludesCrashCandidateWhenPresent(self):
        """!
        @brief crashResult.releaseCandidate가 있으면 조립 결과에 포함된다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 J, IU-0010 행
        @case Positive — 충돌 후보가 조립 리스트에 항상 포함되는지 검증
        @breaks crashResult에 후보가 있는데도 조립 결과에서 누락되는 회귀
        """
        crashMonitor = CrashMonitor()
        approachRiskEvaluator = ApproachRiskEvaluator()
        overrideManager = ApproachRiskOverrideManager()
        fireMonitor = FireOvertempOccupantMonitor()
        crashResult = crashMonitor.evaluate(validField(CrashStatus.CONFIRMED), 1.0)
        approachResult = approachRiskEvaluator.evaluate(validField(False), validField(False))
        overrideDecision = overrideManager.decide(False, False, False, False, 1.0)
        forcedReleaseResult = fireMonitor.evaluate(validField(False), validField(False), validField(False))

        candidates = SafetyKernelOrchestrator.assembleCandidateCommands(
            crashResult, approachResult, overrideDecision, forcedReleaseResult
        )

        self.assertEqual(candidates, [crashResult.releaseCandidate])

    def testExcludesLeftSuppressCandidateWhenLeftOverrideActive(self):
        """!
        @brief leftOverrideActive=True이면 leftSuppressCandidate가 조립 결과에서 철회된다(결정표 J).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 J, override 철회 행
        @case Negative — override가 LOCK 후보를 "철회"만 하는 6.7절 계약을 검증
        @breaks override가 활성인데도 LOCK 후보가 여전히 조립 결과에 남는 회귀
        """
        approachRiskEvaluator = ApproachRiskEvaluator()
        overrideManager = ApproachRiskOverrideManager()
        crashMonitor = CrashMonitor()
        fireMonitor = FireOvertempOccupantMonitor()
        crashResult = crashMonitor.evaluate(validField(CrashStatus.NONE), 1.0)
        approachResult = approachRiskEvaluator.evaluate(validField(True), validField(False))
        overrideManager.decide(True, False, False, False, 0.0)
        overrideDecision = overrideManager.decide(True, False, True, False, 5.0)
        forcedReleaseResult = fireMonitor.evaluate(validField(False), validField(False), validField(False))

        candidates = SafetyKernelOrchestrator.assembleCandidateCommands(
            crashResult, approachResult, overrideDecision, forcedReleaseResult
        )

        self.assertEqual(candidates, [])

    def testIncludesForcedReleaseCandidateWhenTriggered(self):
        """!
        @brief forcedReleaseResult.releaseCandidate가 있으면 조립 결과에 포함된다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 J, IU-0013 행
        @case Positive — 강제해제 후보가 조립 리스트에 항상 포함되는지 검증
        @breaks forcedReleaseResult에 후보가 있는데도 조립 결과에서 누락되는 회귀
        """
        crashMonitor = CrashMonitor()
        approachRiskEvaluator = ApproachRiskEvaluator()
        overrideManager = ApproachRiskOverrideManager()
        fireMonitor = FireOvertempOccupantMonitor()
        crashResult = crashMonitor.evaluate(validField(CrashStatus.NONE), 1.0)
        approachResult = approachRiskEvaluator.evaluate(validField(False), validField(False))
        overrideDecision = overrideManager.decide(False, False, False, False, 1.0)
        forcedReleaseResult = fireMonitor.evaluate(validField(True), validField(False), validField(False))

        candidates = SafetyKernelOrchestrator.assembleCandidateCommands(
            crashResult, approachResult, overrideDecision, forcedReleaseResult
        )

        self.assertEqual(candidates, [forcedReleaseResult.releaseCandidate])


class TestSafetyKernelOrchestratorComposeReleaseReRequested(unittest.TestCase):
    """IU-0009.composeReleaseReRequested() 계약 검증(placeholder, ledger 갭 7)."""

    def testAlwaysReturnsFalseFalsePlaceholder(self):
        """!
        @brief OEM-FR-001 미분석으로 항상 (False, False)를 반환한다(5.3절 명시적 placeholder).
        @technique 동등분할(Equivalence Partitioning) — 인자 없는 함수의 유일한 반환값
        @case Positive — placeholder가 실제로 (False, False) 고정값인지 검증
        @breaks 반환값이 (False, False) 외의 값으로 바뀌는 회귀(연결되지 않은 채널을 잘못 활성화)
        """
        result = SafetyKernelOrchestrator.composeReleaseReRequested()

        self.assertEqual(result, (False, False))


class TestSafetyKernelOrchestratorReset(unittest.TestCase):
    """IU-0009.reset() 계약 검증."""

    def testResetRestoresWholeSystemToBootDefaults(self):
        """!
        @brief reset()은 IU-0002/0003/0004의 reset()을 호출해 부팅 기본값으로 복귀시킨다.
        @technique 상태전이 테스트(State Transition Testing) — FAULT 누적 이후 reset -> 재평가
        @case Positive — 하위 3개 단위가 실제로 초기화되는지(합성 동작)를 검증
        @breaks reset()이 일부 하위 단위만 초기화하거나 아무 효과가 없는 회귀
        """
        orchestrator = buildOrchestrator()
        faultInput = normalizedInput(validField(1.000), validField(True), validField(True))
        orchestrator.evaluateCycle(faultInput, 1.000)

        orchestrator.reset()

        normalInput = normalizedInput(validField(2.000), validField(True), validField(False))
        result = orchestrator.evaluateCycle(normalInput, 2.000)

        self.assertEqual(result.stateResult.state, SystemState.NORMAL)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)

    def testResetClearsOverrideManagerSuppressionTimer(self):
        """!
        @brief reset()은 IU-0012.reset()도 호출해 억제 타이머 이력을 지운다(8.6절/13장).
        @technique 상태전이 테스트(State Transition Testing) — 오래된 억제 이력 이후 reset -> 재진입
        @case Positive — IU-0012가 다른 3개 단위와 함께 reset() 대상에 실제로 포함되는지 검증
        @breaks reset()이 IU-0012를 초기화하지 않아 오래된 억제 시각이 override 판정을 오염시키는 회귀
        """
        orchestrator = buildOrchestrator()
        leftRiskInput = normalizedInput(
            validField(1.000), validField(True), validField(False), leftApproachRiskField=validField(True)
        )
        orchestrator.evaluateCycle(leftRiskInput, 0.0)
        orchestrator.evaluateCycle(leftRiskInput, 50.0)

        orchestrator.reset()

        overrideDecision = orchestrator.overrideManager.decide(True, False, True, False, 50.05)

        self.assertTrue(overrideDecision.leftOverrideActive)


if __name__ == "__main__":
    unittest.main()
