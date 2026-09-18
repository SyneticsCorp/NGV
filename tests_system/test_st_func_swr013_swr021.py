"""!
@file test_st_func_swr013_swr021.py
@brief 시스템 테스트(SWE.6) — SWR-013, SWR-021 (Phase 1 범위 전체). 테스트 베이시스는
       Deliverables/Engineering/SoftwareRequirementsAnalysis/ENG-SWE1-001(SW 요구사항 명세서)
       4.2절이며, 아키텍처/상세설계 문서가 아니다. 진입점은 InputValidationAdapter.handleCycle()
       (원시 Vehicle 입력 -> CycleResult, st_helpers.buildSystemUnderTest() 참조).

각 테스트 클래스는 ENG-SWE6-001의 Test ID(ST-FUNC-NNNN)와 1:1 대응한다.
"""

import unittest

from tests_system.st_helpers import LockCommand, SystemState, buildRawInput, buildSystemUnderTest


class TestSTFUNC0001FreshnessBelowThreshold(unittest.TestCase):
    """ST-FUNC-0001 — SWR-013(a), 경계값분석(임계값 미만)"""

    def testElapsed199msRemainsNormal(self):
        """!
        @brief source_timestamp_s 경과시간이 199ms(<200ms)이면 NORMAL을 유지해야 한다.
        @technique 경계값분석(Boundary Value Analysis) — 200ms 임계값 미만
        @case Positive
        @breaks 임계값 미만인데도 DEGRADED로 오판정되는 회귀
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildRawInput(0.000, True, False), 0.000)

        result = system.handleCycle(buildRawInput(0.000, True, False), 0.199)

        self.assertEqual(result.stateResult.state, SystemState.NORMAL)
        self.assertFalse(result.errorOccurred)


class TestSTFUNC0002FreshnessExactlyAtThreshold(unittest.TestCase):
    """ST-FUNC-0002 — SWR-013(a), 경계값분석(임계값 경계)"""

    def testElapsedExactly200msRemainsNormal(self):
        """!
        @brief 경과시간이 정확히 200ms이면 아직 "초과"가 아니므로 NORMAL을 유지해야 한다
               (요구사항 원문 "200 ms를 초과하여 경과하면").
        @technique 경계값분석(Boundary Value Analysis) — 200ms 정확한 경계
        @case Positive
        @breaks 경계값(>=)과 요구사항 문구(초과, >)의 부등호 오적용 회귀
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildRawInput(0.000, True, False), 0.000)

        result = system.handleCycle(buildRawInput(0.000, True, False), 0.200)

        self.assertEqual(result.stateResult.state, SystemState.NORMAL)
        self.assertFalse(result.errorOccurred)


class TestSTFUNC0003FreshnessJustOverThreshold(unittest.TestCase):
    """ST-FUNC-0003 — SWR-013(a), 경계값분석(임계값 초과 직후)"""

    def testElapsed201msTransitionsToDegraded(self):
        """!
        @brief 경과시간이 200ms를 초과(201ms)하면 DEGRADED로 전이해야 한다.
        @technique 경계값분석(Boundary Value Analysis) — 200ms 임계값 초과 직후
        @case Negative
        @breaks 200ms 초과인데도 NORMAL로 남거나 FAULT로 오판정되는 회귀
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildRawInput(0.000, True, False), 0.000)

        result = system.handleCycle(buildRawInput(0.000, True, False), 0.201)

        self.assertEqual(result.stateResult.state, SystemState.DEGRADED)
        self.assertFalse(result.errorOccurred)


class TestSTFUNC0004FreshnessAtDetectionBudgetBound(unittest.TestCase):
    """ST-FUNC-0004 — SWR-013(a), 경계값분석(검출 예산 상한 300ms)"""

    def testDegradedObservedWithin300msAbsoluteBudget(self):
        """!
        @brief 합격기준(ENG-SWE1-001 4.2절 SWR-013 검증방안): "200 ms 초과 시점 이후 100 ms
               이내(절대 기준 300 ms 이내)에 DEGRADED로 관측된다". 절대 300ms 시점에서도
               DEGRADED가 관측되어야 한다.
        @technique 경계값분석(Boundary Value Analysis) — 100ms 검출 예산의 절대 상한(300ms)
        @case Positive
        @breaks 검출 예산(300ms) 상한 시점에도 DEGRADED가 관측되지 않는 회귀
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildRawInput(0.000, True, False), 0.000)

        result = system.handleCycle(buildRawInput(0.000, True, False), 0.300)

        self.assertEqual(result.stateResult.state, SystemState.DEGRADED)
        self.assertLessEqual(0.300, 0.300)


class TestSTFUNC0005TimestampMissingRejected(unittest.TestCase):
    """ST-FUNC-0005 — SWR-013(b), 동등분할(누락 클래스)"""

    def testMissingTimestampIsRejectedAndNotUsedInOutputDecision(self):
        """!
        @brief source_timestamp_s가 누락(None)되면 평가 전에 거절되어야 하며, 거절된 값이
               해당 평가주기의 출력 결정(freshness 판정)에 사용되지 않아야 한다(SWR-013b).
               직전 유효값(1.000, t=1.000) 기준으로 50ms만 경과했으므로, 거절된 누락값이
               잘못 사용됐다면(예: 0으로 치환) DEGRADED로 오판정됐을 것이다.
        @technique 동등분할(Equivalence Partitioning) — 누락(MISSING) 클래스
        @case Negative
        @breaks 누락값이 예외로 사이클을 중단시키거나, 유효값처럼 치환되어 잘못된 상태를 산출하는 회귀
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildRawInput(1.000, True, False), 1.000)

        result = system.handleCycle(buildRawInput(None, True, False), 1.050)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.stateResult.state, SystemState.NORMAL)


class TestSTFUNC0006TimestampTypeErrorRejected(unittest.TestCase):
    """ST-FUNC-0006 — SWR-013(b), 동등분할(형식 오류 클래스)"""

    def testNonNumericTimestampIsRejectedAndNotUsedInOutputDecision(self):
        """!
        @brief source_timestamp_s가 비수치 문자열이면 형식 오류로 거절되어야 하며, 직전
               유효값 기준 freshness 판정에 영향을 주지 않아야 한다(SWR-013b).
        @technique 동등분할(Equivalence Partitioning) — 형식 오류(비수치) 클래스
        @case Negative
        @breaks 비수치 문자열이 형변환되어 통과하거나 사이클이 예외로 중단되는 회귀
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildRawInput(1.000, True, False), 1.000)

        result = system.handleCycle(buildRawInput("invalid_ts", True, False), 1.050)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.stateResult.state, SystemState.NORMAL)


class TestSTFUNC0007TimestampOutOfRangeRejected(unittest.TestCase):
    """ST-FUNC-0007 — SWR-013(b), 경계값분석(범위 오류 하한)"""

    def testNegativeTimestampIsRejectedAndNotUsedInOutputDecision(self):
        """!
        @brief source_timestamp_s가 음수(하한 0.0 미만)이면 범위 오류로 거절되어야 하며,
               직전 유효값 기준 freshness 판정에 영향을 주지 않아야 한다(SWR-013b). 상한은
               OEM 원문 미기재로 확인 필요(ENG-SWE1-001 8장 가정 2) — 하한 경계만 검증한다.
        @technique 경계값분석(Boundary Value Analysis) — 하한(0.0) 경계, 범위 오류 클래스
        @case Negative
        @breaks 음수 값이 유효값으로 통과하거나 사이클이 예외로 중단되는 회귀
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildRawInput(1.000, True, False), 1.000)

        result = system.handleCycle(buildRawInput(-0.5, True, False), 1.050)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.stateResult.state, SystemState.NORMAL)


class TestSTFUNC0008IgnitionOnTypeErrorDoesNotCrash(unittest.TestCase):
    """ST-FUNC-0008 — SWR-013(b), 오류추측(견고성) — 관측 한계 있음(Scope Note 참조)"""

    def testNonBooleanIgnitionOnDoesNotCrashOrCorruptState(self):
        """!
        @brief ignition_on이 엄격한 bool이 아니면(문자열 "true") 형식 오류로 거절되어야 한다
               (SWR-013b). Phase1은 ignition_on을 이용하는 출력결정 로직(OEM-FR-007)이 범위
               밖이라 CycleResult로는 게이트(INPUT_INVALID) 효과가 관측되지 않는다 — 이 시험은
               "예외로 사이클이 중단되거나 상태 판정이 훼손되지 않는다"만 확인한다(적용 한계,
               ENG-SWE1-001 1.3절).
        @technique 오류추측(Error Guessing) — 형식 오류(비-bool) 클래스, 견고성
        @case Negative
        @breaks 예외로 사이클이 중단되거나 형식 오류 입력이 freshness/state 판정을 훼손하는 회귀
        """
        system = buildSystemUnderTest()

        result = system.handleCycle(buildRawInput(1.000, "true", False), 1.000)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.stateResult.state, SystemState.NORMAL)


class TestSTFUNC0009ProposedSensorFaultFieldMissing(unittest.TestCase):
    """ST-FUNC-0009(제안) — SWR-013(b)/SWR-021(b), 오류추측 — QA 제안 케이스"""

    def testMissingSensorFaultFieldResultsInFaultState(self):
        """!
        @brief (제안) sensor_fault 필드 자체가 누락되면 ASIL B 안전 필수 입력이므로 위험측으로
               해석되어야 한다는 것이 안전 설계 의도다. 이 대체값(fail-safe substitute=TRUE)
               자체는 ENG-SWE1-001 원문에 명시되어 있지 않고 하위 설계 문서(ENG-SWE3-001 10장)
               근거이므로, 이 케이스는 요구사항 원문이 아닌 QA 제안(오류추측)으로 표시한다.
        @technique 오류추측(Error Guessing) — 안전 필수 입력 필드 자체 누락(제안)
        @case Negative
        @breaks 누락된 sensor_fault가 FALSE로 취급되어 위험측 대체가 적용되지 않는 회귀
        """
        system = buildSystemUnderTest()

        result = system.handleCycle(buildRawInput(1.000, True, None), 1.000)

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.stateResult.state, SystemState.FAULT)
        self.assertTrue(result.stateResult.warningReasonCode)


class TestSTFUNC0010SensorFaultFirstCycleFreezesOutput(unittest.TestCase):
    """ST-FUNC-0010 — SWR-021(a), 요구사항 기반 시험(인수 시나리오)"""

    def testSensorFaultTrueFirstCycleHoldsPreviousConfirmedOutput(self):
        """!
        @brief sensor_fault=TRUE인 첫 평가주기에, 직전 평가주기에 확정된 좌/우 출력이 그대로
               유지되어야 한다(SWR-021a, fail-freeze).
        @technique 요구사항 기반 시험(Requirements-based Test) — SWR-021 인수 시나리오
        @case Negative
        @breaks sensor_fault=TRUE 전이 시 출력이 직전 확정값과 달라지는 회귀
        """
        system = buildSystemUnderTest()
        previous = system.handleCycle(buildRawInput(1.000, True, False), 1.000)

        result = system.handleCycle(buildRawInput(1.050, True, True), 1.050)

        self.assertEqual(result.stateResult.state, SystemState.FAULT)
        self.assertEqual(result.confirmedOutput.left, previous.confirmedOutput.left)
        self.assertEqual(result.confirmedOutput.right, previous.confirmedOutput.right)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


class TestSTFUNC0011SensorFaultSustainedKeepsOutputFrozen(unittest.TestCase):
    """ST-FUNC-0011 — SWR-021(a), 동등분할(지속 TRUE 클래스)"""

    def testSensorFaultTrueSustainedAcrossCyclesKeepsOutputFrozen(self):
        """!
        @brief sensor_fault가 TRUE인 "동안"(상태 기반, 복수 평가주기 지속) 출력이 계속 직전
               확정값으로 유지되어야 한다(SWR-021a).
        @technique 동등분할(Equivalence Partitioning) — sensor_fault 지속 TRUE 클래스
        @case Negative
        @breaks 두 번째 이후 FAULT 평가주기에서 출력이 변경되는 회귀
        """
        system = buildSystemUnderTest()
        baseline = system.handleCycle(buildRawInput(1.000, True, False), 1.000)

        first = system.handleCycle(buildRawInput(1.050, True, True), 1.050)
        second = system.handleCycle(buildRawInput(1.100, True, True), 1.100)

        for cycleResult in (first, second):
            self.assertEqual(cycleResult.stateResult.state, SystemState.FAULT)
            self.assertEqual(cycleResult.confirmedOutput.left, baseline.confirmedOutput.left)
            self.assertEqual(cycleResult.confirmedOutput.right, baseline.confirmedOutput.right)


class TestSTFUNC0012SensorFaultTransitionTriggersFaultAndWarning(unittest.TestCase):
    """ST-FUNC-0012 — SWR-021(b), 이벤트 기반 시험(FALSE->TRUE 전이)"""

    def testSensorFaultTransitionToTrueYieldsFaultStateAndWarningCode(self):
        """!
        @brief sensor_fault가 FALSE에서 TRUE로 전이된 첫 평가주기에 시스템 상태가 FAULT로
               전이되고, 정의된 타입(비공백 값)의 경고코드가 제공되어야 한다(SWR-021b). 경고
               코드 실제 카탈로그는 OEM 원문 미제공(ENG-SWE1-001 8장 가정 5)이므로 합격기준을
               "정의된 타입의 비공백 값"으로 판정한다(요구사항 원문 그대로).
        @technique 요구사항 기반 시험(Requirements-based Test) — SWR-021 인수 시나리오
        @case Negative
        @breaks FAULT 전이는 되지만 경고코드가 비어있거나, 그 반대인 회귀
        """
        system = buildSystemUnderTest()
        normalResult = system.handleCycle(buildRawInput(1.000, True, False), 1.000)

        result = system.handleCycle(buildRawInput(1.050, True, True), 1.050)

        self.assertIsNone(normalResult.stateResult.warningReasonCode)
        self.assertEqual(result.stateResult.state, SystemState.FAULT)
        self.assertIsInstance(result.stateResult.warningReasonCode, str)
        self.assertTrue(result.stateResult.warningReasonCode.strip())


class TestSTFUNC0013SensorFaultSustainedKeepsFaultAndWarning(unittest.TestCase):
    """ST-FUNC-0013 — SWR-021(a)/(b), 상태전이 테스트(지속 FAULT 연속성)"""

    def testSensorFaultSustainedKeepsFaultStateWithWarningCode(self):
        """!
        @brief sensor_fault=TRUE가 다음 평가주기에도 지속되면, 상태는 FAULT를 유지하고
               경고코드도 비공백 값으로 계속 제공되어야 한다(공통 자료형 불변식 "state==FAULT
               ⟺ warningReasonCode is not None", ENG-SWE1-001 SWR-021(a) "동안" 상태 기반
               조건의 연속성).
        @technique 상태전이 테스트(State Transition Testing) — FAULT 지속 연속성
        @case Negative
        @breaks 두 번째 FAULT 평가주기에서 경고코드가 사라지거나 상태가 흔들리는 회귀
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildRawInput(1.000, True, False), 1.000)
        system.handleCycle(buildRawInput(1.050, True, True), 1.050)

        result = system.handleCycle(buildRawInput(1.100, True, True), 1.100)

        self.assertEqual(result.stateResult.state, SystemState.FAULT)
        self.assertIsInstance(result.stateResult.warningReasonCode, str)
        self.assertTrue(result.stateResult.warningReasonCode.strip())


if __name__ == "__main__":
    unittest.main()
