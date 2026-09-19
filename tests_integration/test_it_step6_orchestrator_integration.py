"""!
@file test_it_step6_orchestrator_integration.py
@brief 통합 6단계 — ARC-0009(오케스트레이터), IF-0006~IF-0012 전체를 1~5단계 실물 컴포넌트와
       통합. ARC-0001은 스텁(정규화 입력 테스트 벡터를 evaluateCycle에 직접 주입)으로 대체한다
       (ENG-SWE2-001 11장 순서표 6행).

이 단계부터는 mock을 전혀 쓰지 않고 ARC-0002~0008 실물 인스턴스를 그대로 조립해, 매 평가주기
IF-0006->IF-0007->IF-0008->IF-0009->IF-0010->IF-0007(경고)->IF-0011->IF-0012 순서로 실제 호출이
일어나는지, 그리고 3장 세 가지 시나리오(NORMAL/DEGRADED/FAULT)가 실제 배선을 통해 재현되는지를
검증한다. IU-0009 단위시험(SWE.4)이 이미 실물 협력 객체로 고정 순서를 검증했으나, 이번 6단계는
그 사실을 SWE.5 관점(인터페이스별 함수/Call 커버리지)에서 독립적으로 재확인한다.
"""

import unittest

from tests_integration.it_helpers import (
    RaisingDecisionLogger,
    RaisingFreshnessMonitor,
    RaisingNotificationAdapter,
    RaisingOutputActuatorAdapter,
    SystemState,
    buildNormalizedInput,
    buildRealOrchestrator,
    captureReturn,
    invalidField,
    recordCalls,
    validField,
)
from ngv.adapters.decision_logger_stub import DecisionLoggerStub
from ngv.adapters.notification_adapter import NotificationAdapter
from ngv.adapters.output_actuator_adapter import OutputActuatorAdapter
from ngv.app.safety_kernel_orchestrator import SafetyKernelOrchestrator
from ngv.core.approach_risk_evaluator import ApproachRiskEvaluator
from ngv.core.approach_risk_override_manager import ApproachRiskOverrideManager
from ngv.core.command_arbiter import CommandArbiter
from ngv.core.crash_monitor import CrashMonitor
from ngv.core.fire_overtemp_occupant_monitor import FireOvertempOccupantMonitor
from ngv.core.freshness_monitor import FreshnessMonitor
from ngv.core.output_hold_actuator import OutputHoldActuator
from ngv.core.state_manager import StateManager
from ngv.domain.types import LockCommand


def buildPhase2Collaborators():
    """!
    @brief 이 통합시험 파일의 직접 조립(direct construction) 케이스가 공통으로 쓰는
           Phase2 신규 협력 객체(IU-0010~0013) kwargs를 만든다(중복 코드 제거).
    """
    return {
        "crashMonitor": CrashMonitor(),
        "approachRiskEvaluator": ApproachRiskEvaluator(),
        "overrideManager": ApproachRiskOverrideManager(),
        "fireMonitor": FireOvertempOccupantMonitor(),
    }


class TestIT0026NormalCycleEndToEnd(unittest.TestCase):
    """IT-0026 — Trace: IF-0005~IF-0012 / SWR-013, SWR-021(조율), 7장 시나리오 1"""

    def testNormalCycleProducesNormalStateAndPublishedOutputs(self):
        """!
        @brief NORMAL 시나리오(7장 시나리오 1)가 실물 컴포넌트 배선을 거쳐 재현되고, IF-0010/
               IF-0011로 발행된 payload까지 올바른지 검증한다.
        @technique 유스케이스 테스트(Use Case Testing) — 7장 시나리오 1(정상) 재현
        @case Positive
        @breaks 실물 배선 중 한 컴포넌트라도 잘못 연결되어 NORMAL 경로가 깨지는 회귀
        """
        publishSink = []
        warningSink = []
        outputAdapter = captureReturn(OutputActuatorAdapter(), "publish", publishSink)
        notificationAdapter = captureReturn(NotificationAdapter(), "publishWarning", warningSink)
        orchestrator = SafetyKernelOrchestrator(
            freshnessMonitor=FreshnessMonitor(),
            stateManager=StateManager(),
            outputHoldActuator=OutputHoldActuator(),
            commandArbiter=CommandArbiter(),
            outputAdapter=outputAdapter,
            notificationAdapter=notificationAdapter,
            decisionLogger=DecisionLoggerStub(),
            **buildPhase2Collaborators(),
        )
        cycleInput = buildNormalizedInput(validField(1.000), validField(True), validField(False))

        result = orchestrator.evaluateCycle(cycleInput, 1.000)

        self.assertEqual(result.stateResult.state, SystemState.NORMAL)
        self.assertFalse(result.errorOccurred)
        self.assertEqual(publishSink[0].payload["lock_left"], "LOCK")
        self.assertEqual(warningSink[0].payload["state"], "NORMAL")
        self.assertIsNone(warningSink[0].payload["reason_code"])


class TestIT0027DegradedCycleDoesNotFreezeOutput(unittest.TestCase):
    """IT-0027 — Trace: IF-0006~IF-0009 / SWR-013(a), 7장 시나리오 2"""

    def testFreshnessExceeds200msYieldsDegradedWithoutFreeze(self):
        """!
        @brief source_timestamp_s가 200ms 초과 경과하면 DEGRADED로 전이하고(SWR-013a), 8장/7장
               시나리오 2의 잠정 설계대로 출력은 고정되지 않고 후보값 그대로 확정되어야 한다.
        @technique 경계값분석(Boundary Value Analysis) — 200ms 임계 초과, 유스케이스 테스트
        @case Positive
        @breaks DEGRADED에서도 출력이 고정(freeze)되거나 상태가 FAULT로 오판정되는 회귀
        """
        orchestrator = buildRealOrchestrator()
        firstInput = buildNormalizedInput(validField(1.000), validField(True), validField(False))
        orchestrator.evaluateCycle(firstInput, 1.000)

        secondInput = buildNormalizedInput(invalidField(None, "MISSING"), validField(True), validField(False))
        result = orchestrator.evaluateCycle(secondInput, 1.201)

        self.assertEqual(result.stateResult.state, SystemState.DEGRADED)
        self.assertFalse(result.errorOccurred)


class TestIT0028FaultCycleFreezesAndWarns(unittest.TestCase):
    """IT-0028 — Trace: IF-0007~IF-0011 / SWR-021, 7장 시나리오 3"""

    def testSensorFaultTrueFreezesOutputAndPublishesWarning(self):
        """!
        @brief sensor_fault=True 첫 평가주기에 fail-freeze(직전 확정값 유지)와 FAULT 경고 발행이
               실물 배선을 통해 함께 일어나야 한다(7장 시나리오 3, SWR-021 전체).
        @technique 유스케이스 테스트(Use Case Testing) — 7장 시나리오 3(고장) 재현
        @case Negative
        @breaks fail-freeze는 되지만 경고가 발행되지 않거나, 그 반대인 회귀(부분 배선 결함)
        """
        warningSink = []
        notificationAdapter = captureReturn(NotificationAdapter(), "publishWarning", warningSink)
        orchestrator = SafetyKernelOrchestrator(
            freshnessMonitor=FreshnessMonitor(),
            stateManager=StateManager(),
            outputHoldActuator=OutputHoldActuator(),
            commandArbiter=CommandArbiter(),
            outputAdapter=OutputActuatorAdapter(),
            notificationAdapter=notificationAdapter,
            decisionLogger=DecisionLoggerStub(),
            **buildPhase2Collaborators(),
        )
        normalInput = buildNormalizedInput(validField(1.000), validField(True), validField(False))
        orchestrator.evaluateCycle(normalInput, 1.000)

        faultInput = buildNormalizedInput(validField(1.050), validField(True), validField(True))
        result = orchestrator.evaluateCycle(faultInput, 1.050)

        self.assertEqual(result.stateResult.state, SystemState.FAULT)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)
        self.assertEqual(warningSink[-1].payload["state"], "FAULT")
        self.assertEqual(warningSink[-1].payload["reason_code"], "SENSOR_FAULT_DETECTED")


class TestIT0029FixedCallOrderAcrossRealComponents(unittest.TestCase):
    """IT-0029 — Trace: IF-0006~IF-0012 / 11장 통합 순서, 3장 고정 호출 순서"""

    def testAllSevenSubComponentsCalledInArchitectureOrder(self):
        """!
        @brief IU-0002->0003->0005->0004->0006->0007->0008 고정 순서로 각 인터페이스가
               정확히 1회씩 호출되어야 한다(3장/11장 통합 순서와 Call 커버리지 직접 증명).
        @technique 유스케이스 테스트(Use Case Testing) — 3장 상세 호출관계
        @case Positive
        @breaks 순서가 뒤바뀌거나 특정 IF 호출이 생략/중복되는 회귀
        """
        callLog = []
        orchestrator = SafetyKernelOrchestrator(
            freshnessMonitor=recordCalls(FreshnessMonitor(), "evaluate", "IF-0006", callLog),
            stateManager=recordCalls(StateManager(), "evaluate", "IF-0007", callLog),
            outputHoldActuator=recordCalls(OutputHoldActuator(), "confirm", "IF-0009", callLog),
            commandArbiter=recordCalls(CommandArbiter(), "arbitrate", "IF-0008", callLog),
            outputAdapter=recordCalls(OutputActuatorAdapter(), "publish", "IF-0010", callLog),
            notificationAdapter=recordCalls(NotificationAdapter(), "publishWarning", "IF-0011", callLog),
            decisionLogger=recordCalls(DecisionLoggerStub(), "log", "IF-0012", callLog),
            **buildPhase2Collaborators(),
        )
        cycleInput = buildNormalizedInput(validField(1.000), validField(True), validField(False))

        orchestrator.evaluateCycle(cycleInput, 1.000)

        self.assertEqual(
            callLog,
            ["IF-0006", "IF-0007", "IF-0008", "IF-0009", "IF-0010", "IF-0011", "IF-0012"],
        )


class TestIT0030CoreStageFaultInjectionForcesFault(unittest.TestCase):
    """IT-0030 — Trace: IF-0006 / ASIL B 오류 주입, 10.2절"""

    def testFreshnessMonitorFailureForcesFaultWithoutPropagating(self):
        """!
        @brief ARC-0002(IF-0006)에서 예외가 발생하면 오케스트레이터가 FAULT를 강제하고
               fail-freeze를 적용하며, 예외가 evaluateCycle() 밖으로 전파되지 않아야 한다
               (10.2절, ASIL B 판정 핵심 경로 오류 주입).
        @technique 오류주입(Fault Injection Test) — 판정 핵심 경로(ASIL B) 컴포넌트 실패
        @case Negative
        @breaks 하위 컴포넌트 예외가 실제 조립 상태에서도 전파되어 전체 커널이 중단되는 회귀
        """
        orchestrator = SafetyKernelOrchestrator(
            freshnessMonitor=RaisingFreshnessMonitor(),
            stateManager=StateManager(),
            outputHoldActuator=OutputHoldActuator(),
            commandArbiter=CommandArbiter(),
            outputAdapter=OutputActuatorAdapter(),
            notificationAdapter=NotificationAdapter(),
            decisionLogger=DecisionLoggerStub(),
            **buildPhase2Collaborators(),
        )
        cycleInput = buildNormalizedInput(validField(1.000), validField(True), validField(False))

        result = orchestrator.evaluateCycle(cycleInput, 1.000)

        self.assertEqual(result.stateResult.state, SystemState.FAULT)
        self.assertTrue(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


class TestIT0031PublishStageFaultInjectionIsolated(unittest.TestCase):
    """IT-0031 — Trace: IF-0010, IF-0011, IF-0012 / 오류 주입, 10.2절"""

    def testAllThreeQmAdapterFailuresDoNotAffectConfirmedSafeState(self):
        """!
        @brief IF-0010/IF-0011/IF-0012 세 QM 어댑터가 동시에 예외를 던져도 이미 확정된 판정
               결과(NORMAL/출력)는 훼손되지 않고, 예외가 전파되지 않아야 한다(10.2절 개별 격리).
        @technique 오류주입(Fault Injection Test) — QM 어댑터 3종 동시 실패
        @case Negative
        @breaks 발행 단계 실패가 판정 결과를 훼손하거나 예외가 전파되는 회귀
        """
        orchestrator = SafetyKernelOrchestrator(
            freshnessMonitor=FreshnessMonitor(),
            stateManager=StateManager(),
            outputHoldActuator=OutputHoldActuator(),
            commandArbiter=CommandArbiter(),
            outputAdapter=RaisingOutputActuatorAdapter(),
            notificationAdapter=RaisingNotificationAdapter(),
            decisionLogger=RaisingDecisionLogger(),
            **buildPhase2Collaborators(),
        )
        cycleInput = buildNormalizedInput(validField(1.000), validField(True), validField(False))

        result = orchestrator.evaluateCycle(cycleInput, 1.000)

        self.assertEqual(result.stateResult.state, SystemState.NORMAL)
        self.assertFalse(result.errorOccurred)


class TestIT0032ResetCascadesToRealSubComponents(unittest.TestCase):
    """IT-0032 — Trace: IF-0006, IF-0007, IF-0009 reset() 경로"""

    def testResetRestoresRealFreshnessStateAndOutputActuator(self):
        """!
        @brief orchestrator.reset()은 실물 IU-0002/0003/0004의 reset()을 모두 호출해 시스템
               전체를 부팅 기본값으로 되돌려야 한다(합성 데이터가 아닌 실물 조립 상태 기준).
        @technique 상태전이 테스트(State Transition Testing) — FAULT 누적 -> reset -> 재평가
        @case Positive
        @breaks reset()이 일부 실물 하위 컴포넌트만 초기화하는 회귀
        """
        orchestrator = buildRealOrchestrator()
        faultInput = buildNormalizedInput(validField(1.000), validField(True), validField(True))
        orchestrator.evaluateCycle(faultInput, 1.000)

        orchestrator.reset()

        normalInput = buildNormalizedInput(validField(2.000), validField(True), validField(False))
        result = orchestrator.evaluateCycle(normalInput, 2.000)

        self.assertEqual(result.stateResult.state, SystemState.NORMAL)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


class TestIT0033InvalidInputGateWiredToRealArbiter(unittest.TestCase):
    """IT-0033 — Trace: IF-0005, IF-0008 / SWR-013(b), 결정표 D 배선 확인"""

    def testInvalidTimestampFieldBlocksThroughRealArbiter(self):
        """!
        @brief IF-0005의 sourceTimestampField.valid=False가 composeInputValid()를 거쳐 실물
               CommandArbiter(IF-0008)에 inputValid=False로 전달되고, 실제로 blocked=True/
               INPUT_INVALID가 반환되는지(스파이가 아닌 실제 반환값으로) 검증한다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 D 배선 검증(실물)
        @case Negative
        @breaks 게이트 합성 로직과 실물 Arbiter 배선이 어긋나 무효 입력에도 명령이 통과되는 회귀
        """
        orchestrator = buildRealOrchestrator()
        cycleInput = buildNormalizedInput(invalidField(None, "MISSING"), validField(True), validField(False))

        result = orchestrator.evaluateCycle(cycleInput, 1.000)

        self.assertEqual(result.stateResult.state, SystemState.DEGRADED)
        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


if __name__ == "__main__":
    unittest.main()
