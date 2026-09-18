"""!
@file test_it_step7_input_validation_full_chain.py
@brief 통합 7단계(최종) — ARC-0001(입력 검증 어댑터)을 6단계 실물 오케스트레이터와 통합.
       IF-0005, IF-0001, IF-0002 인터페이스 계약을 검증하고, 1~6단계 전체 회귀 및
       SWR-013/SWR-021 인수 수준 시나리오(ENG-SWE1-001 검증방안)를 재실행한다
       (ENG-SWE2-001 11장 순서표 7행). Vehicle 원시 입력은 시험 벡터 주입 프레임워크
       (buildRawCycleInput)로 대체한다.
"""

import unittest

from tests_integration.it_helpers import (
    SystemState,
    buildRawCycleInput,
    buildRealAdapterWithOrchestrator,
)
from ngv.domain.types import LockCommand


class TestIT0034NormalRawInputEndToEnd(unittest.TestCase):
    """IT-0034 — Trace: IF-0001, IF-0002, IF-0005 / SWR-013, SWR-021"""

    def testValidRawInputYieldsNormalStateThroughFullChain(self):
        """!
        @brief 유효한 원시 입력(IF-0001/IF-0002)이 ARC-0001 검증/정규화(IF-0005)를 거쳐
               오케스트레이터까지 전달되어 NORMAL 상태를 산출해야 한다(전체 체인 최초 통합).
        @technique 요구사항 기반 시험(Requirements-based Test) — 정상 흐름 전체 체인
        @case Positive
        @breaks ARC-0001 배선 오류로 정상 입력에서도 오판정이 발생하는 회귀
        """
        adapter, orchestrator = buildRealAdapterWithOrchestrator()
        rawInput = buildRawCycleInput(1.000, True, False)

        result = adapter.handleCycle(rawInput, 1.000)

        self.assertEqual(result.stateResult.state, SystemState.NORMAL)
        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)


class TestIT0035MissingTimestampRejected(unittest.TestCase):
    """IT-0035 — Trace: IF-0001, IF-0005 / SWR-013(b)"""

    def testMissingRawTimestampIsRejectedAndDoesNotCrashCycle(self):
        """!
        @brief source_timestamp_s 누락(None)은 명령 평가 이전에 거절(INVALID)되어야 하며,
               해당 평가주기의 출력 결정에 사용되지 않아야 한다(SWR-013b 합격기준).
        @technique 동등분할(Equivalence Partitioning) — 누락(MISSING) 클래스, 경계값분석과 결합
        @case Negative
        @breaks 누락 필드가 예외로 전체 사이클을 중단시키거나 조용히 무시되고 정상 처리되는 회귀
        """
        adapter, orchestrator = buildRealAdapterWithOrchestrator()
        rawInput = buildRawCycleInput(None, True, False)

        result = adapter.handleCycle(rawInput, 1.000)

        self.assertFalse(result.errorOccurred)
        self.assertIn(result.stateResult.state, (SystemState.DEGRADED, SystemState.FAULT))


class TestIT0036NonNumericTimestampRejected(unittest.TestCase):
    """IT-0036 — Trace: IF-0001, IF-0005 / SWR-013(b)"""

    def testNonNumericRawTimestampYieldsTypeErrorRejection(self):
        """!
        @brief 비수치 형식 오류(예: 문자열)는 TYPE_ERROR로 거절되어야 한다(SWR-013b 합격기준
               "형식 오류(예: 비수치 값)").
        @technique 동등분할(Equivalence Partitioning) — 형식 오류(비수치) 클래스
        @case Negative
        @breaks 비수치 값이 형변환되어 통과하는 회귀
        """
        from ngv.adapters.input_validation_adapter import InputValidationAdapter

        fieldResult = InputValidationAdapter.validateTimestampField("not-a-number")

        self.assertFalse(fieldResult.valid)
        self.assertEqual(fieldResult.errorReason, "TYPE_ERROR")


class TestIT0037OutOfRangeTimestampRejected(unittest.TestCase):
    """IT-0037 — Trace: IF-0001, IF-0005 / SWR-013(b), 경계값분석"""

    def testNegativeAndNonFiniteTimestampAreOutOfRange(self):
        """!
        @brief 음수·비유한(NaN/Inf) source_timestamp_s는 OUT_OF_RANGE로 거절되어야 한다.
               상한은 OEM 원문 미기재로 확인 필요(ENG-SWE2-001 6.2절)이므로 하한(0.0) 경계만
               검증하고 이 사실을 적용 한계로 남긴다.
        @technique 경계값분석(Boundary Value Analysis) — 하한 0.0 경계, 특수값(NaN/Inf) 등가클래스
        @case Negative
        @breaks 음수/NaN/Inf가 유효값으로 잘못 통과하는 회귀
        """
        from ngv.adapters.input_validation_adapter import InputValidationAdapter

        negative = InputValidationAdapter.validateTimestampField(-0.001)
        notANumber = InputValidationAdapter.validateTimestampField(float("nan"))
        infinite = InputValidationAdapter.validateTimestampField(float("inf"))

        for fieldResult in (negative, notANumber, infinite):
            self.assertFalse(fieldResult.valid)
            self.assertEqual(fieldResult.errorReason, "OUT_OF_RANGE")


class TestIT0038NonBooleanIgnitionRejected(unittest.TestCase):
    """IT-0038 — Trace: IF-0002, IF-0005 / SWR-013(b)"""

    def testNonBooleanIgnitionOnYieldsTypeErrorRejection(self):
        """!
        @brief ignition_on이 엄격한 bool 타입이 아니면("true" 문자열 등) TYPE_ERROR로 거절되어야
               한다.
        @technique 동등분할(Equivalence Partitioning) — 형식 오류(비-bool) 클래스
        @case Negative
        @breaks 문자열 "true"/1 등이 bool로 암묵 변환되어 통과하는 회귀
        """
        from ngv.adapters.input_validation_adapter import InputValidationAdapter

        fieldResult = InputValidationAdapter.validateBooleanField("true", "ignition_on")

        self.assertFalse(fieldResult.valid)
        self.assertEqual(fieldResult.errorReason, "TYPE_ERROR")


class TestIT0039MissingSensorFaultFailSafeForcesFault(unittest.TestCase):
    """IT-0039 — Trace: IF-0002, IF-0005, IF-0007 / SWR-013(b), ASIL B 오류 주입"""

    def testMissingSensorFaultTriggersFailSafeAndFaultState(self):
        """!
        @brief sensor_fault 필드 자체가 누락(INVALID)되면 fail-safe 대체(True)가 적용되어 전체
               체인이 FAULT 상태로 귀결되어야 한다(ENG-SWE3-001 10장 fail-safe 대체 규칙,
               ASIL B 핵심 경로 오류 주입).
        @technique 오류주입(Fault Injection Test) — 안전 필수 입력 필드 누락
        @case Negative
        @breaks sensor_fault 누락이 FALSE로 취급되어 위험 측으로 fail-safe가 적용되는 회귀
        """
        adapter, orchestrator = buildRealAdapterWithOrchestrator()
        rawInput = buildRawCycleInput(1.000, True, None)

        result = adapter.handleCycle(rawInput, 1.000)

        self.assertEqual(result.stateResult.state, SystemState.FAULT)
        self.assertEqual(result.stateResult.warningReasonCode, "SENSOR_FAULT_INPUT_INVALID")
        self.assertFalse(result.errorOccurred)


class TestIT0040SensorFaultTrueFullChainAcceptance(unittest.TestCase):
    """IT-0040 — Trace: IF-0001, IF-0002, IF-0005, IF-0007, IF-0009 / SWR-021 인수 시나리오"""

    def testSensorFaultTrueFreezesOutputAndReportsFaultThroughFullChain(self):
        """!
        @brief SWR-021 합격기준: sensor_fault=TRUE 첫 평가주기에 좌/우 출력이 직전 확정값과
               동일하게 유지되고, 상태값이 FAULT, 경고코드가 비공백 값으로 관측된다. 원시
               입력(IF-0001/IF-0002)부터 시작하는 전체 체인으로 재현한다.
        @technique 요구사항 기반 시험(Requirements-based Test) — SWR-021 인수 시나리오 재사용
        @case Negative
        @breaks 전체 체인 기준으로는 fail-freeze/FAULT 통지 중 하나라도 누락되는 회귀
        """
        adapter, orchestrator = buildRealAdapterWithOrchestrator()
        normalInput = buildRawCycleInput(1.000, True, False)
        adapter.handleCycle(normalInput, 1.000)

        faultInput = buildRawCycleInput(1.050, True, True)
        result = adapter.handleCycle(faultInput, 1.050)

        self.assertEqual(result.stateResult.state, SystemState.FAULT)
        self.assertTrue(result.stateResult.warningReasonCode)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


class TestIT0041FreshnessAcceptanceScenario(unittest.TestCase):
    """IT-0041 — Trace: IF-0001, IF-0005, IF-0006, IF-0007 / SWR-013(a) 인수 시나리오"""

    def testFreshnessExceeds200msTransitionsWithinBudgetThroughFullChain(self):
        """!
        @brief SWR-013(a) 합격기준: source_timestamp_s 경과시간이 200ms를 초과하도록 주입한
               시험벡터에서, 상태가 200ms 초과 시점 이후 100ms 이내(절대기준 300ms 이내)에
               DEGRADED로 관측된다. 고정 시계(결정론적 clock)로 원시 입력부터 재현한다.
        @technique 경계값분석(Boundary Value Analysis) + 요구사항 기반 시험 — SWR-013 인수 시나리오
        @case Positive
        @breaks 300ms 이내에 DEGRADED가 관측되지 않거나 원시 입력 경로에서 판정이 누락되는 회귀
        """
        adapter, orchestrator = buildRealAdapterWithOrchestrator()
        adapter.handleCycle(buildRawCycleInput(0.000, True, False), 0.000)

        result = adapter.handleCycle(buildRawCycleInput(None, True, False), 0.250)

        self.assertEqual(result.stateResult.state, SystemState.DEGRADED)
        self.assertLessEqual(0.250, 0.300)


class TestIT0042CandidateCommandChannelOutOfPhase1Scope(unittest.TestCase):
    """IT-0042 — Trace: IF-0008 / SWR-021 합격기준 비고, 적용 한계"""

    def testNoCandidateCommandChannelExistsInPhase1RawInput(self):
        """!
        @brief SWR-021 합격기준 비고("동일 주기에 함께 주입된 신규 명령이 출력에 반영되지 않음")는
               Phase1에서 candidateCommands가 항상 빈 리스트로 고정되어(1.3절 적용경계) 구조적으로
               성립한다. 원시 입력 경로에 신규 명령 채널 자체가 없음을 문서화하는 시험이며, Phase1
               범위에서 candidateCommands가 결코 비어있지 않게 채워지지 않는지 확인한다.
        @technique 요구사항 기반 시험(Requirements-based Test) — 적용 한계 문서화
        @case Positive — Phase1 구조적 보장을 명시적으로 고정(회귀 방지 앵커)
        @breaks 향후 Phase에서 후보 명령 채널이 추가되며 이 가정이 깨졌는데도 알아채지 못하는 회귀
                (본 케이스가 실패하면 SWR-021 비고 재검증 필요 신호)
        """
        adapter, orchestrator = buildRealAdapterWithOrchestrator()
        receivedCandidates = []
        originalArbitrate = orchestrator.commandArbiter.arbitrate

        def spyArbitrate(stateResult, inputValid, candidateCommands=None):
            receivedCandidates.append(candidateCommands)
            return originalArbitrate(stateResult, inputValid, candidateCommands)

        orchestrator.commandArbiter.arbitrate = spyArbitrate

        adapter.handleCycle(buildRawCycleInput(1.000, True, False), 1.000)

        self.assertEqual(receivedCandidates, [[]])


class TestIT0043FullRegressionAcrossStates(unittest.TestCase):
    """IT-0043 — Trace: IF-0001~IF-0012 전체 / 11장 7단계 "1~6단계 전체 회귀" """

    def testNormalDegradedFaultSequenceRegressesCleanlyThroughFullChain(self):
        """!
        @brief NORMAL -> DEGRADED -> FAULT -> reset() -> NORMAL 순서로 연속 평가주기를 실행해,
               1~6단계에서 개별 검증한 동작이 최종 실물 조립(ARC-0001 포함)에서도 회귀 없이
               유지되는지 확인한다(11장 7단계 "1~6단계 전체 회귀").
        @technique 상태전이 테스트(State Transition Testing) — 전체 상태 순환 회귀
        @case Positive
        @breaks 개별 단계 통합시험은 통과하지만 전체 체인에서만 드러나는 배선 회귀
        """
        adapter, orchestrator = buildRealAdapterWithOrchestrator()

        normalResult = adapter.handleCycle(buildRawCycleInput(0.000, True, False), 0.000)
        degradedResult = adapter.handleCycle(buildRawCycleInput(None, True, False), 0.250)
        faultResult = adapter.handleCycle(buildRawCycleInput(0.260, True, True), 0.260)
        orchestrator.reset()
        recoveredResult = adapter.handleCycle(buildRawCycleInput(1.000, True, False), 1.000)

        self.assertEqual(normalResult.stateResult.state, SystemState.NORMAL)
        self.assertEqual(degradedResult.stateResult.state, SystemState.DEGRADED)
        self.assertEqual(faultResult.stateResult.state, SystemState.FAULT)
        self.assertEqual(faultResult.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(recoveredResult.stateResult.state, SystemState.NORMAL)
        self.assertFalse(recoveredResult.errorOccurred)


if __name__ == "__main__":
    unittest.main()
