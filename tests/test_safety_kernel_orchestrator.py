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
from ngv.domain.types import FieldValidationResult, LockCommand, NormalizedSafetyInput, SystemState
from ngv.core.command_arbiter import CommandArbiter
from ngv.core.freshness_monitor import FreshnessMonitor
from ngv.core.output_hold_actuator import OutputHoldActuator
from ngv.core.state_manager import StateManager
from ngv.adapters.decision_logger_stub import DecisionLoggerStub
from ngv.adapters.notification_adapter import NotificationAdapter
from ngv.adapters.output_actuator_adapter import OutputActuatorAdapter
from ngv.app.safety_kernel_orchestrator import SafetyKernelOrchestrator


def validField(value):
    """테스트 헬퍼 — 유효한 FieldValidationResult를 만든다."""
    return FieldValidationResult(value=value, valid=True, rawValue=value)


def invalidField(rawValue, errorReason="TYPE_ERROR"):
    """테스트 헬퍼 — 무효한 FieldValidationResult를 만든다."""
    return FieldValidationResult(value=None, valid=False, rawValue=rawValue, errorReason=errorReason)


def normalizedInput(timestampField, ignitionField, sensorFaultField):
    """테스트 헬퍼 — NormalizedSafetyInput을 만든다."""
    return NormalizedSafetyInput(
        sourceTimestampField=timestampField,
        ignitionOnField=ignitionField,
        sensorFaultField=sensorFaultField,
    )


def buildOrchestrator():
    """테스트 헬퍼 — 실제(real) 협력 객체로 구성된 오케스트레이터를 만든다."""
    return SafetyKernelOrchestrator(
        freshnessMonitor=FreshnessMonitor(),
        stateManager=StateManager(),
        outputHoldActuator=OutputHoldActuator(),
        commandArbiter=CommandArbiter(),
        outputAdapter=OutputActuatorAdapter(),
        notificationAdapter=NotificationAdapter(),
        decisionLogger=DecisionLoggerStub(),
    )


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
        @brief IU-0002->0003->0005->0004->0006->0007->0008 고정 순서로 정확히 1회씩 호출한다.
        @technique 유스케이스 테스트(Use Case Testing) — 3장 상세 호출관계의 고정 순서 계약
        @case Positive — 통합 순서(ENG-SWE2-001 11장/ENG-SWE3-001 3장)를 그대로 구현했는지 검증
        @breaks 호출 순서가 뒤바뀌거나 특정 단계가 생략/중복되는 회귀
        """
        callLog = []
        freshnessMonitor = recordCalls(FreshnessMonitor(), "evaluate", "IU-0002", callLog)
        stateManager = recordCalls(StateManager(), "evaluate", "IU-0003", callLog)
        commandArbiter = recordCalls(CommandArbiter(), "arbitrate", "IU-0005", callLog)
        outputHoldActuator = recordCalls(OutputHoldActuator(), "confirm", "IU-0004", callLog)
        outputAdapter = recordCalls(OutputActuatorAdapter(), "publish", "IU-0006", callLog)
        notificationAdapter = recordCalls(NotificationAdapter(), "publishWarning", "IU-0007", callLog)
        decisionLogger = recordCalls(DecisionLoggerStub(), "log", "IU-0008", callLog)
        orchestrator = SafetyKernelOrchestrator(
            freshnessMonitor=freshnessMonitor,
            stateManager=stateManager,
            outputHoldActuator=outputHoldActuator,
            commandArbiter=commandArbiter,
            outputAdapter=outputAdapter,
            notificationAdapter=notificationAdapter,
            decisionLogger=decisionLogger,
        )
        input1 = normalizedInput(validField(1.000), validField(True), validField(False))

        orchestrator.evaluateCycle(input1, 1.000)

        self.assertEqual(
            callLog, ["IU-0002", "IU-0003", "IU-0005", "IU-0004", "IU-0006", "IU-0007", "IU-0008"]
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
        orchestrator = SafetyKernelOrchestrator(
            freshnessMonitor=FreshnessMonitor(),
            stateManager=StateManager(),
            outputHoldActuator=OutputHoldActuator(),
            commandArbiter=commandArbiter,
            outputAdapter=OutputActuatorAdapter(),
            notificationAdapter=NotificationAdapter(),
            decisionLogger=DecisionLoggerStub(),
        )
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
        orchestrator = SafetyKernelOrchestrator(
            freshnessMonitor=RaisingFreshnessMonitor(),
            stateManager=StateManager(),
            outputHoldActuator=OutputHoldActuator(),
            commandArbiter=CommandArbiter(),
            outputAdapter=OutputActuatorAdapter(),
            notificationAdapter=NotificationAdapter(),
            decisionLogger=DecisionLoggerStub(),
        )
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
        orchestrator = SafetyKernelOrchestrator(
            freshnessMonitor=FreshnessMonitor(),
            stateManager=StateManager(),
            outputHoldActuator=OutputHoldActuator(),
            commandArbiter=CommandArbiter(),
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


if __name__ == "__main__":
    unittest.main()
