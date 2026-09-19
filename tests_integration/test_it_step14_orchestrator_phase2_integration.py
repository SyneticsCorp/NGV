"""!
@file test_it_step14_orchestrator_phase2_integration.py
@brief 통합 14단계 — ARC-0009(오케스트레이터, ARC-0010~0013 호출 및 candidateCommands 조립
       추가), IF-0016~IF-0019 + IF-0008 전체를 8~13단계 실물 컴포넌트와 통합(Phase2 갱신).

테스트 베이시스: ENG-SWE2-001 6장, 11장 순서표 14행("8~13단계 실물 컴포넌트와 통합"). 회귀
범위: 1~13단계 전체 회귀 + Phase1 인수시나리오(SWR-013/021) 재실행 + Phase2 인수시나리오
(SWR-005/006/007/008/009/017) 신규 실행. mock을 쓰지 않고 실물 협력 객체만 조립한다.
"""

import unittest

from tests_integration.it_helpers import (
    SystemState,
    buildPhase2NormalizedInput,
    buildPhase2RawCycleInput,
    buildRealAdapterWithOrchestrator,
    buildRealOrchestrator,
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


class TestIT0082CrashConfirmedFullChainReleasesBothDoors(unittest.TestCase):
    """IT-0082 — Trace: IF-0001~IF-0009, IF-0013, IF-0016 / SWR-007 인수기준, 7장 시나리오 4"""

    def testCrashConfirmedRawInputYieldsBothDoorReleaseThroughFullChain(self):
        """!
        @brief crash_status=CONFIRMED 원시 입력이 ARC-0001->ARC-0009->ARC-0010->ARC-0005->
               ARC-0004 전체 체인을 거쳐 좌/우 RELEASE로 확정되어야 한다(SWR-007 인수기준,
               7장 시나리오 4). 평가주기(50ms)가 300ms 예산보다 짧아 이 단일 호출 자체가
               이미 예산 이내다(9장 근거).
        @technique 요구사항 기반 시험(Requirements-based Test) — SWR-007 인수 시나리오 재사용
        @case Positive
        @breaks 전체 체인 중 한 연결이 잘못돼 CONFIRMED가 RELEASE로 반영되지 않는 회귀
        """
        adapter, _ = buildRealAdapterWithOrchestrator()
        rawInput = buildPhase2RawCycleInput(1.000, True, False, rawCrashStatus="CONFIRMED")

        result = adapter.handleCycle(rawInput, 1.000)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestIT0083ApproachRiskFullChainLocksBothDoorsIndependently(unittest.TestCase):
    """IT-0083 — Trace: IF-0001~IF-0009, IF-0014, IF-0017 / SWR-005, SWR-009 인수기준, 7장 시나리오 5"""

    def testLeftAndRightApproachRiskYieldsIndependentLockThroughFullChain(self):
        """!
        @brief rear_left/right_approach_risk=True(둘 다)가 전체 체인을 거쳐 좌/우 모두 LOCK
               억제로 확정되어야 한다(SWR-005/009 인수기준, 7장 시나리오 5 전반부).
        @technique 요구사항 기반 시험(Requirements-based Test) — SWR-005/009 인수 시나리오 재사용
        @case Positive
        @breaks 좌/우 중 한쪽만 반영되거나 반대쪽에 영향을 주는 회귀(독립성 붕괴)
        """
        adapter, _ = buildRealAdapterWithOrchestrator()
        rawInput = buildPhase2RawCycleInput(
            1.000, True, False, rawLeftApproachRisk=True, rawRightApproachRisk=True
        )

        result = adapter.handleCycle(rawInput, 1.000)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


class TestIT0084OverrideNeverActivatesThroughFullChainDueToPlaceholder(unittest.TestCase):
    """IT-0084 — Trace: IF-0018 / SWR-006, ledger 갭 7(적용 한계), 오류주입"""

    def testSuppressionPersistsBeyondTenSecondsBecauseReleaseReRequestedPlaceholderIsAlwaysFalse(
        self,
    ):
        """!
        @brief composeReleaseReRequested()가 항상 (False, False)를 반환하는 placeholder이므로
               (OEM-FR-001 미분석, ledger 갭 7), 전체 체인에서는 아무리 시간이 지나도(10초 초과)
               override가 성립하지 않고 LEFT LOCK 억제가 계속 유지되어야 한다 — 이 한계를 통합
               수준에서 명시적으로 문서화한다.
        @technique 오류주입(Fault Injection Test) — 구조적 placeholder 한계 문서화
        @case Negative
        @breaks releaseReRequested 채널이 실제 신호에 연결된 것처럼 override가 성립하는 회귀
                (플레이스홀더 상태에서는 발생해서는 안 됨)
        """
        adapter, _ = buildRealAdapterWithOrchestrator()
        firstInput = buildPhase2RawCycleInput(1.000, True, False, rawLeftApproachRisk=True)
        adapter.handleCycle(firstInput, 1.000)

        secondInput = buildPhase2RawCycleInput(15.000, True, False, rawLeftApproachRisk=True)
        result = adapter.handleCycle(secondInput, 15.000)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)


class TestIT0085FireFullChainReleasesBothDoors(unittest.TestCase):
    """IT-0085 — Trace: IF-0001~IF-0009, IF-0015, IF-0019 / SWR-017 인수기준, 7장 시나리오 6"""

    def testFireDetectedRawInputYieldsBothDoorReleaseThroughFullChain(self):
        """!
        @brief fire_detected=True 원시 입력이 전체 체인을 거쳐 좌/우 RELEASE로 확정되어야 한다
               (SWR-017 인수기준, 7장 시나리오 6).
        @technique 요구사항 기반 시험(Requirements-based Test) — SWR-017 인수 시나리오 재사용
        @case Positive
        @breaks 전체 체인 중 한 연결이 잘못돼 화재 트리거가 RELEASE로 반영되지 않는 회귀
        """
        adapter, _ = buildRealAdapterWithOrchestrator()
        rawInput = buildPhase2RawCycleInput(1.000, True, False, rawFireDetected=True)

        result = adapter.handleCycle(rawInput, 1.000)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestIT0086MultiConditionPriorityMediationFullChain(unittest.TestCase):
    """IT-0086 — Trace: IF-0016~IF-0019, IF-0008 / SWR-005/007/017 우선순위 중재, 7장 시나리오 7"""

    def testCrashApproachRiskAndFireSimultaneouslyYieldsCrashPriorityOnBothDoors(self):
        """!
        @brief crash_status=CONFIRMED, rear_left_approach_risk=True, fire_detected=True가
               동일 평가주기에 동시 성립하면(7장 시나리오 7), 충돌(priority=1)이 접근위험
               (priority=2)·화재(priority=3)보다 우선해 좌/우 모두 RELEASE로 확정되어야 한다.
        @technique 유스케이스 테스트(Use Case Testing) — 7장 시나리오 7(복수 조건 동시 발생) 재현
        @case Positive
        @breaks 우선순위 중재가 실제 전체 체인에서 어긋나는 회귀
        """
        adapter, _ = buildRealAdapterWithOrchestrator()
        rawInput = buildPhase2RawCycleInput(
            1.000,
            True,
            False,
            rawCrashStatus="CONFIRMED",
            rawLeftApproachRisk=True,
            rawFireDetected=True,
        )

        result = adapter.handleCycle(rawInput, 1.000)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestIT0087FixedCallOrderAcrossPhase2RealComponents(unittest.TestCase):
    """IT-0087 — Trace: IF-0006~IF-0019 / 11장 통합 순서, 3장/7장 고정 호출 순서"""

    def testAllElevenSubComponentsCalledInArchitectureOrder(self):
        """!
        @brief IU-0002->0003->0010->0011->0012->0013->0005->0004->0006->0007->0008 고정
               순서로 각 인터페이스가 정확히 1회씩 호출되어야 한다(3장/11장 통합 순서, Call
               커버리지 직접 증명 — Phase1 IT-0029를 Phase2 4개 신규 리프로 확장).
        @technique 유스케이스 테스트(Use Case Testing) — 3장 상세 호출관계(Phase2 확장)
        @case Positive
        @breaks Phase2 신규 리프 호출 순서가 뒤바뀌거나 생략/중복되는 회귀
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
            crashMonitor=recordCalls(CrashMonitor(), "evaluate", "IF-0016", callLog),
            approachRiskEvaluator=recordCalls(ApproachRiskEvaluator(), "evaluate", "IF-0017", callLog),
            overrideManager=recordCalls(ApproachRiskOverrideManager(), "decide", "IF-0018", callLog),
            fireMonitor=recordCalls(FireOvertempOccupantMonitor(), "evaluate", "IF-0019", callLog),
        )
        cycleInput = buildPhase2NormalizedInput(validField(1.000), validField(True), validField(False))

        orchestrator.evaluateCycle(cycleInput, 1.000)

        self.assertEqual(
            callLog,
            [
                "IF-0006",
                "IF-0007",
                "IF-0016",
                "IF-0017",
                "IF-0018",
                "IF-0019",
                "IF-0008",
                "IF-0009",
                "IF-0010",
                "IF-0011",
                "IF-0012",
            ],
        )


class TestIT0088FaultGateOverridesSimultaneousCrashCandidateFullChain(unittest.TestCase):
    """IT-0088 — Trace: IF-0007~IF-0009, IF-0016 / 8장 Phase2 확정 사항, 오류주입, 회귀"""

    def testSensorFaultTrueForcesFailFreezeEvenWithCrashConfirmedSimultaneously(self):
        """!
        @brief sensor_fault=True(ASIL B FAULT 경로)와 crash_status=CONFIRMED가 동일 주기에
               동시 성립해도, FAULT 게이트가 Phase2 후보보다 항상 우선해 fail-freeze(직전
               확정값 유지)가 적용되어야 한다(8장 Phase2 확정: "FAULT가 Phase2 후보보다 항상
               우선"). ASIL B 안전 경로 오류 주입 + 전체 체인 회귀를 겸한다.
        @technique 오류주입(Fault Injection Test) — ASIL B 게이트 우선순위(FAULT > Phase2 후보)
        @case Negative
        @breaks FAULT임에도 crash 후보가 RELEASE로 반영되는 회귀(안전 게이트 붕괴)
        """
        adapter, _ = buildRealAdapterWithOrchestrator()
        normalInput = buildPhase2RawCycleInput(1.000, True, False)
        adapter.handleCycle(normalInput, 1.000)

        faultInput = buildPhase2RawCycleInput(1.050, True, True, rawCrashStatus="CONFIRMED")
        result = adapter.handleCycle(faultInput, 1.050)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.stateResult.state, SystemState.FAULT)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


class TestIT0089DegradedDoesNotBlockPhase2CandidatesFullChain(unittest.TestCase):
    """IT-0089 — Trace: IF-0006, IF-0007, IF-0016 / 8장 Phase2 확정 사항(갭 4), 회귀"""

    def testStaleFreshnessDoesNotPreventCrashConfirmedReleaseFullChain(self):
        """!
        @brief freshness가 200ms를 초과해 DEGRADED로 전이돼도(정보성 상태), crash_status=
               CONFIRMED 후보는 제한 없이 그대로 적용되어야 한다(8장 Phase2 확정 — DEGRADED가
               Phase2 후보를 제한하지 않음, 실제 안전 적정성은 OEM 근거 부재로 별도 갭 유지).
        @technique 결정테이블 테스트(Decision Table Testing) — 8장 Phase2 확정 사항 재확인, 회귀
        @case Positive
        @breaks DEGRADED가 Phase2 후보를 잘못 차단하는 회귀(설계 결정과 불일치)
        """
        adapter, _ = buildRealAdapterWithOrchestrator()
        firstInput = buildPhase2RawCycleInput(1.000, True, False)
        adapter.handleCycle(firstInput, 1.000)

        # 두 번째 주기도 동일한(=갱신되지 않은) 유효 timestamp를 그대로 재전송한다 — 필드 자체는
        # valid=True를 유지해 inputValid 게이트를 통과시키면서, nowS만 200ms 넘게 전진시켜
        # elapsedS>0.200(SWR-013a)을 성립시킨다(무효 필드로 인한 INPUT_INVALID 차단과는 구분).
        secondInput = buildPhase2RawCycleInput(1.000, True, False, rawCrashStatus="CONFIRMED")
        result = adapter.handleCycle(secondInput, 1.300)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.stateResult.state, SystemState.DEGRADED)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestIT0090Phase1AcceptanceStillPassesThroughExtendedOrchestrator(unittest.TestCase):
    """IT-0090 — Trace: IF-0001,IF-0002,IF-0005,IF-0007,IF-0009 / SWR-021 인수기준 재실행, 회귀"""

    def testSensorFaultTrueFullChainAcceptanceUnaffectedByPhase2Extension(self):
        """!
        @brief Phase2 원시 필드를 전혀 제공하지 않는 Phase1 스타일 호출도(하위호환, RawCycleInput
               기본값 None->MISSING) 여전히 SWR-021 인수기준(fail-freeze + FAULT 경고)을
               충족해야 한다 — 확장된 생성자/9필드 정규화가 Phase1 동작을 훼손하지 않았는지
               재확인(11장 14단계 "Phase1 인수시나리오 재실행").
        @technique 요구사항 기반 시험(Requirements-based Test) — SWR-021 인수 시나리오 재사용, 회귀
        @case Positive
        @breaks Phase2 확장이 Phase1 sensor_fault 경로를 훼손하는 회귀
        """
        adapter, _ = buildRealAdapterWithOrchestrator()
        normalInput = buildPhase2RawCycleInput(1.000, True, False)
        adapter.handleCycle(normalInput, 1.000)

        faultInput = buildPhase2RawCycleInput(1.050, True, True)
        result = adapter.handleCycle(faultInput, 1.050)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.stateResult.state, SystemState.FAULT)
        self.assertIsNotNone(result.stateResult.warningReasonCode)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


class TestIT0091ResetCascadesToOverrideManagerAtOrchestratorLevel(unittest.TestCase):
    """IT-0091 — Trace: IF-0012(내부 reset 경로) / 8.6절, 13장 자원 경계(재시작 시 억제 이력 없음)"""

    def testOrchestratorResetCallsOverrideManagerReset(self):
        """!
        @brief orchestrator.reset()은 IU-0012(overrideManager)의 reset()도 호출해야 한다
               (Phase2 확장 — IU-0002/0003/0004에 더해 IU-0012 추가, 13장 "재시작 시 이 타이머는
               초기화되며 fail-safe 방향과 일치").
        @technique 상태전이 테스트(State Transition Testing) — reset() 계단식 호출 확인(Call 커버리지)
        @case Positive
        @breaks orchestrator.reset()이 overrideManager.reset()을 호출하지 않는 회귀
        """
        callLog = []
        orchestrator = buildRealOrchestrator()
        orchestrator.overrideManager = recordCalls(orchestrator.overrideManager, "reset", "IF-0018-RESET", callLog)

        orchestrator.reset()

        self.assertEqual(callLog, ["IF-0018-RESET"])


class TestIT0092InvalidFireFieldDoesNotBlockUnrelatedCrashCandidateFullChain(unittest.TestCase):
    """IT-0092 — Trace: IF-0005(확장)/IF-0008 결정표 D 근거, 오류주입"""

    def testInvalidFireFieldDoesNotSuppressCrashConfirmedReleaseFullChain(self):
        """!
        @brief fire_detected가 형식 오류(무효)여도, crash_status=CONFIRMED 후보는 무관하게
               그대로 적용되어야 한다(ENG-SWE3-001 7장 결정표 D 근거 — 관련 없는 다른 컴포넌트의
               정당한 후보까지 함께 차단해서는 안 됨).
        @technique 오류주입(Fault Injection Test) — 결정표 D 근거(무관 필드 무효가 다른 후보를
                   차단하지 않음) 실제 동작 검증
        @case Negative
        @breaks 무관한 필드의 무효가 다른 컴포넌트의 정당한 후보까지 차단하는 회귀(과도한 결합)
        """
        adapter, _ = buildRealAdapterWithOrchestrator()
        rawInput = buildPhase2RawCycleInput(
            1.000, True, False, rawCrashStatus="CONFIRMED", rawFireDetected="not-a-bool"
        )

        result = adapter.handleCycle(rawInput, 1.000)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


if __name__ == "__main__":
    unittest.main()
