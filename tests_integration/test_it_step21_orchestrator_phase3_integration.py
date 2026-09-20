"""!
@file test_it_step21_orchestrator_phase3_integration.py
@brief 통합 21단계 — ARC-0009(오케스트레이터, ARC-0014~0016 호출·candidateCommands 조립 확장,
       ignitionOnField를 ARC-0003에 전달), IF-0021~IF-0023 + IF-0007/IF-0008 확장 전체를
       15~20단계 실물 컴포넌트와 통합(Phase3 신규).

테스트 베이시스: ENG-SWE2-001 6장, 7장 시나리오 8~11, 11장 순서표 21행("15~20단계 실물
컴포넌트와 통합"). 회귀 범위: 1~20단계 전체 회귀 + Phase1/2 인수시나리오 재실행 + Phase3
인수시나리오(SWR-003/018/020) 신규 실행. mock을 쓰지 않고 실물 협력 객체만 조립한다
(buildRealAdapterWithOrchestrator()는 testsupport.orchestrator_factory를 통해 Phase3 3개
협력객체까지 이미 실물로 배선되어 있다 — coding 게이트가 기계적으로 동기화한 배선을 여기서
재확인한다).
"""

import unittest

from tests_integration.it_helpers import (
    SystemState,
    buildPhase3NormalizedInput,
    buildPhase3RawCycleInput,
    buildRealAdapterWithOrchestrator,
    buildRecordedBaseCollaboratorsKwargs,
    recordCalls,
    validField,
)
from ngv.app.safety_kernel_orchestrator import SafetyKernelOrchestrator
from ngv.core.approach_risk_evaluator import ApproachRiskEvaluator
from ngv.core.approach_risk_override_manager import ApproachRiskOverrideManager
from ngv.core.crash_monitor import CrashMonitor
from ngv.core.fire_overtemp_occupant_monitor import FireOvertempOccupantMonitor
from ngv.core.ignition_off_release_monitor import IgnitionOffReleaseMonitor
from ngv.core.isofix_forced_lock_monitor import IsofixForcedLockMonitor
from ngv.core.vehicle_speed_auto_lock_monitor import VehicleSpeedAutoLockMonitor
from ngv.domain.types import LockCommand


class TestIT0131AutoDriveLockFullChainLocksBothDoors(unittest.TestCase):
    """IT-0131 — Trace: IF-0001~IF-0009, IF-0021 / SWR-003 인수기준, 7장 시나리오 8"""

    def testVehicleSpeedAtThresholdFlipsPreviousReleaseBackToLockThroughFullChain(self):
        """!
        @brief 직전 주기에 ignition-off로 RELEASE가 확정된 상태에서, 다음 주기에 ignition이
               다시 ON이고 vehicle_speed_kph=3.0(임계 이상)이면 자동주행잠금 후보(priority=6)
               만으로 좌/우가 다시 LOCK으로 전환되어야 한다(SWR-003a 인수기준, 7장 시나리오 8).
               직전값이 RELEASE였다가 후보에 의해 실제로 LOCK으로 바뀌는 것을 관찰해 부팅
               기본값(LOCK)과의 우연한 일치가 아님을 증명한다.
        @technique 요구사항 기반 시험(Requirements-based Test) — SWR-003 인수 시나리오 재사용
        @case Positive
        @breaks 전체 체인 중 한 연결이 잘못돼 차속 임계가 LOCK으로 반영되지 않는 회귀
        """
        adapter, _ = buildRealAdapterWithOrchestrator()
        firstInput = it_build(1.000, False)
        adapter.handleCycle(firstInput, 1.000)

        secondInput = it_build(1.050, True, rawVehicleSpeedKph=3.0)
        result = adapter.handleCycle(secondInput, 1.050)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


class TestIT0132IsofixFullChainLocksLeftIndependentlyOfRight(unittest.TestCase):
    """IT-0132 — Trace: IF-0001~IF-0009, IF-0020, IF-0022 / SWR-018 인수기준, 7장 시나리오 9"""

    def testLeftIsofixFlipsOnlyLeftDoorBackToLockThroughFullChain(self):
        """!
        @brief 직전 주기에 ignition-off로 좌/우 모두 RELEASE가 확정된 상태에서, 다음 주기에
               ignition ON + isofix_left=True(우측은 미제공)이면 LEFT만 ISOFIX 강제잠금 후보
               (priority=5)에 의해 LOCK으로 전환되고 RIGHT는 후보가 없어 RELEASE를 그대로
               유지해야 한다(SWR-018 인수기준, 좌우 독립, 7장 시나리오 9).
        @technique 요구사항 기반 시험(Requirements-based Test) — SWR-018 인수 시나리오 재사용, 좌우 독립
        @case Positive
        @breaks 좌측 ISOFIX가 우측에도 영향을 주거나 반영되지 않는 회귀(독립성 붕괴)
        """
        adapter, _ = buildRealAdapterWithOrchestrator()
        firstInput = it_build(1.000, False)
        adapter.handleCycle(firstInput, 1.000)

        secondInput = it_build(1.050, True, rawIsofixLeft=True)
        result = adapter.handleCycle(secondInput, 1.050)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestIT0133IgnitionOffFullChainReleasesBothDoorsAndEntersOffState(unittest.TestCase):
    """IT-0133 — Trace: IF-0001~IF-0009, IF-0011, IF-0023 / SWR-020 인수기준, 7장 시나리오 10"""

    def testIgnitionOffRawInputYieldsBothDoorReleaseAndOffStateThroughFullChain(self):
        """!
        @brief ignition_on=False 원시 입력이 전체 체인을 거쳐 좌/우 RELEASE로 확정되고, 동시에
               state=OFF와 warningReasonCode="IGNITION_OFF"가 함께 산출되어야 한다(SWR-020a/b
               인수기준, 7장 시나리오 10).
        @technique 요구사항 기반 시험(Requirements-based Test) — SWR-020 인수 시나리오 재사용
        @case Positive
        @breaks 전체 체인 중 한 연결이 잘못돼 ignition-off가 RELEASE/OFF로 반영되지 않는 회귀
        """
        adapter, _ = buildRealAdapterWithOrchestrator()
        rawInput = it_build(1.000, False)

        result = adapter.handleCycle(rawInput, 1.000)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.stateResult.state, SystemState.OFF)
        self.assertEqual(result.stateResult.warningReasonCode, "IGNITION_OFF")
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestIT0134IsofixVsIgnitionOffPriorityMediationFullChain(unittest.TestCase):
    """IT-0134 — Trace: IF-0021~IF-0023, IF-0008 / 9장 "Phase 3 우선순위 체인 확정", 7장 시나리오 11"""

    def testIgnitionOffReleaseWinsOverIsofixLockOnLeftDoorThroughFullChain(self):
        """!
        @brief isofix_left=True(priority=5, LOCK)와 ignition_on=False(priority=4, RELEASE)가
               동일 주기에 동시 성립하면, 전체 체인을 거쳐 LEFT/RIGHT 모두 RELEASE로 확정되어야
               한다(9장 근거 — entrapment 방지 취지상 ignition-off가 LOCK 계열보다 우선, 7장
               시나리오 11 재현).
        @technique 유스케이스 테스트(Use Case Testing) — 7장 시나리오 11(LOCK계열/RELEASE계열 상충) 재현
        @case Positive
        @breaks 우선순위 중재가 실제 전체 체인에서 어긋나 LOCK이 선택되는 회귀
        """
        adapter, _ = buildRealAdapterWithOrchestrator()
        rawInput = it_build(1.000, False, rawIsofixLeft=True)

        result = adapter.handleCycle(rawInput, 1.000)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestIT0135ApproachRiskVsIgnitionOffCurrentBehaviorFullChain(unittest.TestCase):
    """IT-0135 — Trace: IF-0017, IF-0023, IF-0008 / 누적 갭 16(해소되지 않음, 현재 동작 문서화)"""

    def testApproachRiskSuppressionCurrentlyWinsOverIgnitionOffOnLeftDoorFullChain(self):
        """!
        @brief rear_left_approach_risk=True(priority=2, ASIL B)와 ignition_on=False(priority=4,
               QM)가 동일 주기 동일 도어에서 상충하면, 현재 전체 체인 구현은 LEFT를 LOCK으로
               확정한다(접근위험 우선이라는 잠정 기본값). 이 관계는 OEM-A 확인 없이 최종 확정된
               것이 아니므로(누적 갭 16), 이 시험은 "현재 동작 문서화" 성격이다.
        @technique 유스케이스 테스트(Use Case Testing) — 갭 16 전체 체인 수준 재확인
        @case Positive — 현재 코드 동작을 회귀 고정(갭 16은 임의로 해소된 것으로 단정하지 않음)
        @breaks 이 우선순위 관계가 의도치 않게 뒤바뀌는(코드 변경) 회귀 — 뒤바뀌면 갭 16 재검토 필요
        """
        adapter, _ = buildRealAdapterWithOrchestrator()
        rawInput = it_build(1.000, False, rawLeftApproachRisk=True)

        result = adapter.handleCycle(rawInput, 1.000)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestIT0136FixedCallOrderAcrossPhase3RealComponents(unittest.TestCase):
    """IT-0136 — Trace: IF-0006~IF-0023 / 11장 통합 순서, 3.1절 고정 호출 순서(Phase3 확장)"""

    def testAllFourteenSubComponentsCalledInArchitectureOrder(self):
        """!
        @brief IU-0002->0003->0010->0011->0012->0013->0016->0015->0014->0005->0004->0006->0007->
               0008 고정 순서(3.1절, "fire monitor 이후 arbitrate 이전"에 ignitionOff->isofix->
               vehicleSpeed 순서로 삽입)로 각 인터페이스가 정확히 1회씩 호출되어야 한다(Call
               커버리지 직접 증명 — Phase2 IT-0087을 Phase3 3개 신규 리프로 확장).
        @technique 유스케이스 테스트(Use Case Testing) — 3.1절 상세 호출관계(Phase3 확장)
        @case Positive
        @breaks Phase3 신규 리프 호출 순서가 뒤바뀌거나 생략/중복되는 회귀
        """
        callLog = []
        orchestrator = SafetyKernelOrchestrator(
            **buildRecordedBaseCollaboratorsKwargs(callLog),
            crashMonitor=recordCalls(CrashMonitor(), "evaluate", "IF-0016", callLog),
            approachRiskEvaluator=recordCalls(ApproachRiskEvaluator(), "evaluate", "IF-0017", callLog),
            overrideManager=recordCalls(ApproachRiskOverrideManager(), "decide", "IF-0018", callLog),
            fireMonitor=recordCalls(FireOvertempOccupantMonitor(), "evaluate", "IF-0019", callLog),
            ignitionOffReleaseMonitor=recordCalls(
                IgnitionOffReleaseMonitor(), "evaluate", "IF-0023", callLog
            ),
            isofixMonitor=recordCalls(IsofixForcedLockMonitor(), "evaluate", "IF-0022", callLog),
            vehicleSpeedMonitor=recordCalls(VehicleSpeedAutoLockMonitor(), "evaluate", "IF-0021", callLog),
        )
        cycleInput = buildPhase3NormalizedInput(validField(1.000), validField(True), validField(False))

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
                "IF-0023",
                "IF-0022",
                "IF-0021",
                "IF-0008",
                "IF-0009",
                "IF-0010",
                "IF-0011",
                "IF-0012",
            ],
        )


class TestIT0137InvalidVehicleSpeedFieldDoesNotBlockUnrelatedCrashCandidateFullChain(unittest.TestCase):
    """IT-0137 — Trace: IF-0005(확장)/IF-0008 결정표 D 근거, 오류주입"""

    def testInvalidVehicleSpeedFieldDoesNotSuppressCrashConfirmedReleaseFullChain(self):
        """!
        @brief vehicle_speed_kph가 형식 오류(무효)여도, crash_status=CONFIRMED 후보는 무관하게
               그대로 적용되어야 한다(결정표 D 근거 — 관련 없는 다른 컴포넌트의 정당한 후보까지
               함께 차단해서는 안 됨. 작업 지침의 "vehicleSpeedField invalid" 오류 주입 항목).
        @technique 오류주입(Fault Injection Test) — 결정표 D 근거(무관 필드 무효가 다른 후보를 차단하지 않음)
        @case Negative
        @breaks 무관한 필드의 무효가 다른 컴포넌트의 정당한 후보까지 차단하는 회귀(과도한 결합)
        """
        adapter, _ = buildRealAdapterWithOrchestrator()
        rawInput = it_build(
            1.000, True, rawCrashStatus="CONFIRMED", rawVehicleSpeedKph="not-a-number"
        )

        result = adapter.handleCycle(rawInput, 1.000)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestIT0138InvalidIsofixFieldDoesNotBlockUnrelatedCrashCandidateFullChain(unittest.TestCase):
    """IT-0138 — Trace: IF-0005(확장)/IF-0008 결정표 D 근거, 오류주입"""

    def testInvalidIsofixFieldDoesNotSuppressCrashConfirmedReleaseFullChain(self):
        """!
        @brief isofix_left가 형식 오류(무효)여도, crash_status=CONFIRMED 후보는 무관하게 그대로
               적용되어야 한다(작업 지침의 "isofix 필드 invalid" 오류 주입 항목).
        @technique 오류주입(Fault Injection Test) — 결정표 D 근거 재확인
        @case Negative
        @breaks 무관한 필드의 무효가 다른 컴포넌트의 정당한 후보까지 차단하는 회귀(과도한 결합)
        """
        adapter, _ = buildRealAdapterWithOrchestrator()
        rawInput = it_build(1.000, True, rawCrashStatus="CONFIRMED", rawIsofixLeft="not-a-bool")

        result = adapter.handleCycle(rawInput, 1.000)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestIT0139InvalidIgnitionOnFieldDoesNotForceOffFullChain(unittest.TestCase):
    """IT-0139 — Trace: IF-0005, IF-0007, IF-0008 / ENG-SWE3-001 8.8절, 오류주입, 회귀"""

    def testInvalidIgnitionOnFieldBlocksCycleAndDoesNotJudgeOffFullChain(self):
        """!
        @brief ignition_on이 형식 오류(불리언이 아님)이면, 전체 체인 수준에서도 state는 OFF로
               판정되지 않고(8.8절 SW 설계 재량 확정), composeInputValid()가 False가 되어
               사이클이 INPUT_INVALID로 차단되어야 한다(작업 지침의 "ignitionOnField invalid →
               OFF 미판정 회귀" 확인 항목). 첫 주기이므로 확정 출력은 부팅 기본값(LOCK/LOCK)이
               그대로 유지된다(차단으로 NO_CHANGE).
        @technique 오류주입(Fault Injection Test) — ENG-SWE3-001 8.8절 전체 체인 수준 재확인
        @case Negative
        @breaks 형식 오류 ignition_on에서도 state=OFF로 잘못 판정되는 회귀(8.8절 결정 붕괴)
        """
        adapter, _ = buildRealAdapterWithOrchestrator()
        rawInput = it_build(1.000, "not-a-bool")

        result = adapter.handleCycle(rawInput, 1.000)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.stateResult.state, SystemState.NORMAL)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


class TestIT0140Phase1And2AcceptanceStillPassThroughPhase3ExtendedOrchestrator(unittest.TestCase):
    """IT-0140 — Trace: IF-0001,IF-0002,IF-0005,IF-0007,IF-0009 / SWR-021/007 인수기준 재실행, 회귀"""

    def testSensorFaultAndCrashAcceptanceUnaffectedByPhase3Extension(self):
        """!
        @brief Phase3 원시 필드를 전혀 제공하지 않는 Phase1/2 스타일 호출도(하위호환) 여전히
               SWR-021(fail-freeze) 인수기준을 충족해야 한다 — 확장된 생성자/12필드 정규화가
               Phase1/2 동작을 훼손하지 않았는지 재확인(11장 21단계 "Phase1/2 인수시나리오
               재실행").
        @technique 요구사항 기반 시험(Requirements-based Test) — SWR-021 인수 시나리오 재사용, 회귀
        @case Positive
        @breaks Phase3 확장이 Phase1/2 sensor_fault 경로를 훼손하는 회귀
        """
        adapter, _ = buildRealAdapterWithOrchestrator()
        normalInput = it_build(1.000, True)
        adapter.handleCycle(normalInput, 1.000)

        faultInput = it_build(1.050, True, rawSensorFault=True)
        result = adapter.handleCycle(faultInput, 1.050)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.stateResult.state, SystemState.FAULT)
        self.assertIsNotNone(result.stateResult.warningReasonCode)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


def it_build(rawSourceTimestamp, rawIgnitionOn, rawSensorFault=False, **phase3RawFields):
    """!
    @brief 이 파일의 전체 체인 시험이 공통으로 쓰는 RawCycleInput 생성 축약(중복 코드 제거).
           tests_integration.it_helpers.buildPhase3RawCycleInput()에 위임한다.
    """
    return buildPhase3RawCycleInput(rawSourceTimestamp, rawIgnitionOn, rawSensorFault, **phase3RawFields)


if __name__ == "__main__":
    unittest.main()
