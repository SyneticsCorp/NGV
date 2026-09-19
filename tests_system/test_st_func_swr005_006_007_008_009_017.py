"""!
@file test_st_func_swr005_006_007_008_009_017.py
@brief 시스템 테스트(SWE.6) — Phase 2 안전 긴급 대응(SWR-005, SWR-006, SWR-007, SWR-008,
       SWR-009, SWR-017). 테스트 베이시스는
       Deliverables/Engineering/SoftwareRequirementsAnalysis/ENG-SWE1-001(SW 요구사항 명세서)
       4.2절/4.1절이며, 아키텍처/상세설계 문서가 아니다. 진입점은 InputValidationAdapter.handleCycle()
       (원시 Vehicle 입력 -> CycleResult, st_helpers.buildSystemUnderTest() 참조, ledger 갭 9 방침).

각 테스트 클래스는 ENG-SWE6-001의 Test ID(ST-FUNC-0014~0030)와 1:1 대응한다.

@par 시스템 경계 공통 한계(모든 케이스에 적용, ENG-SWE1-001 8장 가정 5/12/13, ledger 갭 10)
CycleResult{confirmedOutput, stateResult, errorOccurred}는 ArbitrationResult의
leftReasonCode/rightReasonCode(Phase2 이유코드)를 노출하지 않는다(Display/Web 발행 경로
미확장). 따라서 이 파일의 모든 케이스는 이유코드/원인 "기록" 여부를 handleCycle() 경계에서
직접 관측하지 못하며, 오직 confirmedOutput(LOCK/RELEASE)과 stateResult만으로 판정한다 —
이유코드 자체는 하위 계층(IU-0010~0013/IU-0005 실물)에서 이미 단위/통합시험으로 검증되었다
(ENG-SWE5-002 IT-0044~0093 참조).
"""

import unittest

from tests_system.st_helpers import LockCommand, SystemState, buildPhase2RawInput, buildSystemUnderTest


class TestSTFUNC0014ApproachRiskLocksSingleDoor(unittest.TestCase):
    """ST-FUNC-0014 — SWR-005(a), 요구사항 기반 시험(단일 도어 TRUE)"""

    def testLeftApproachRiskTrueLocksLeftDoor(self):
        """!
        @brief rear_left_approach_risk가 유효한 TRUE로 확인되면 좌측 도어 출력이 LOCK으로
               설정되어야 한다(SWR-005a).
        @technique 요구사항 기반 시험(Requirements-based Test) — SWR-005 인수 시나리오
        @case Positive
        @breaks 접근위험 TRUE인데도 좌측 출력이 LOCK으로 설정되지 않는 회귀
        """
        system = buildSystemUnderTest()

        result = system.handleCycle(
            buildPhase2RawInput(1.000, True, False, rawLeftApproachRisk=True), 1.000
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.stateResult.state, SystemState.NORMAL)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)


class TestSTFUNC0015ApproachRiskSuppressesCompetingReleaseCandidate(unittest.TestCase):
    """ST-FUNC-0015 — SWR-005(b), 결정표기반/오류추측(우선순위 상충) — 적용 한계 있음"""

    def testLeftApproachRiskKeepsLockDespiteSimultaneousFireReleaseCandidate(self):
        """!
        @brief 좌측 접근위험이 TRUE인 동안에는 해제(RELEASE) 요청을 적용하지 않고 LOCK을
               유지해야 한다(SWR-005b). [적용 한계] 원문의 "해제 요청"은 통상 운전자 수동
               명령(OEM-FR-001)을 의미하나 이 채널은 Phase 2 범위 밖(ENG-SWE1-001 1.3절)이라
               원시 입력으로 직접 주입할 수 없다 — 대신 우선순위가 더 낮은 다른 RELEASE
               후보(SWR-017 화재, priority=3)와 동시 발생시켜, 접근위험 억제(priority=2)가
               그 RELEASE 후보를 이긴다는 것으로 "해제 요청 억제"를 간접 검증한다(ENG-SWE1-001
               3장 우선순위 관계, 그림 4-4).
        @technique 결정표기반 시험(우선순위 결정표) + 오류추측(상충 조건) — 10초 override와
                   무관한 우선순위 상충 시나리오
        @case Negative
        @breaks 경쟁하는 RELEASE 후보(낮은 우선순위)에 밀려 좌측이 LOCK을 유지하지 못하는 회귀
        """
        system = buildSystemUnderTest()

        result = system.handleCycle(
            buildPhase2RawInput(
                1.000, True, False, rawLeftApproachRisk=True, rawFireDetected=True
            ),
            1.000,
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestSTFUNC0016OverrideWithinTenSecondsUnreachableAtSystemBoundary(unittest.TestCase):
    """ST-FUNC-0016 — SWR-006(a), 경계값분석(10초 이내 경계, elapsed=10.000s) — 적용 한계/구조적 갭"""

    def testReinputAtExactlyTenSecondsDoesNotProduceObservableOverrideEffect(self):
        """!
        @brief 요구사항 원문(SWR-006a): "최초 억제 시점으로부터 10초 이하 경과한 시점에
               운전자가 동일 도어에 대해 동일한 해제 명령을 재입력하면, override 상태와
               이유코드를 생성해야 한다." [적용 한계/구조적 갭] (1) RawCycleInput에는 운전자
               "재입력(해제 명령)" 채널 자체가 없다(OEM-FR-001 미분석, ledger 갭 7 —
               SafetyKernelOrchestrator.composeReleaseReRequested()가 항상 (False,False)를
               반환하는 placeholder). (2) CycleResult는 override 상태/이유코드 필드를 노출하지
               않는다(ledger 갭 10). (3) 설계상 override가 성립하더라도 좌측에 대해 별도
               RELEASE 후보가 생성되지 않아(assembleCandidateCommands) 출력이 바뀌지 않는다
               (ledger 갭 5). 이 세 겹의 구조적 제약으로, 10초 이내(elapsed=10.000s, 경계값)
               재입력 시나리오를 흉내낸 이 시험은 시스템 경계에서 override 성립의 유일한 관측
               가능 대리 신호(좌측 출력이 LOCK에서 벗어남)를 전혀 관측하지 못한다 — 좌측은
               LOCK을 계속 유지한다. 요구사항 원문의 문언적 기준(override 상태 생성)을
               시스템 경계에서 충족한다고 판정할 수 없으므로 Fail로 기록한다(근본 원인은
               이미 식별된 구조적 갭 5/7/10이며 이번 시험이 이를 시스템 수준에서 재확인함).
        @technique 경계값분석(Boundary Value Analysis) — 10초 이내 경계(elapsed=10.000s, "이하")
        @case Negative
        @breaks (해당 없음 — 현재 구조에서는 항상 이 결과가 관측됨. 향후 releaseReRequested
                채널이 실제 신호에 연결되면 이 시험은 재설계되어야 한다.)
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildPhase2RawInput(1.000, True, False, rawLeftApproachRisk=True), 1.000)

        result = system.handleCycle(
            buildPhase2RawInput(11.000, True, False, rawLeftApproachRisk=True), 11.000
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)


class TestSTFUNC0017SuppressionMaintainedAfterTenSecondWindow(unittest.TestCase):
    """ST-FUNC-0017 — SWR-006(b), 경계값분석(10초 초과 경계, elapsed=10.100s)"""

    def testReinputAfterTenPointOneSecondsKeepsSuppressionApplied(self):
        """!
        @brief 최초 억제 시점으로부터 10초를 초과(elapsed=10.100s)하여 재입력되면, override로
               처리하지 않고 SWR-005의 억제(LOCK)를 그대로 적용해야 한다(SWR-006b). 이 경계
               (10초 초과)는 releaseReRequested 채널 부재와 무관하게 원문 그대로 검증 가능하다
               — override가 성립하지 않아야 하는 부정 경로이므로, 애초에 override를 유발하는
               채널이 없다는 사실이 오히려 이 수용기준(억제 유지)과 일치한다.
        @technique 경계값분석(Boundary Value Analysis) — 10초 초과 경계(elapsed=10.100s, unit
                   시험 test_approach_risk_override_manager.py의 10.0s/10.1s 경계와 정합)
        @case Positive
        @breaks 10초를 초과했는데도 좌측 출력이 LOCK에서 벗어나는 회귀
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildPhase2RawInput(1.000, True, False, rawLeftApproachRisk=True), 1.000)

        result = system.handleCycle(
            buildPhase2RawInput(11.100, True, False, rawLeftApproachRisk=True), 11.100
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)


class TestSTFUNC0018CrashConfirmedReleasesWithinBudgetUnderCycleGapStress(unittest.TestCase):
    """ST-FUNC-0018 — SWR-007(a), 경계값분석(300ms 예산, 평가주기 간격 스트레스)"""

    def testCrashConfirmedObservedAtThreeHundredMsGapStillYieldsImmediateRelease(self):
        """!
        @brief crash_status가 CONFIRMED로 확인되면 300 ms 이내에 후석 좌, 우 출력을 RELEASE로
               전환해야 한다(SWR-007a). [비고] IU-0010(CrashMonitor)은 경과시간을 판정에
               사용하지 않으며(nowS 미사용, ENG-SWE3-001 6.9절) CONFIRMED가 관측된 평가주기
               자체에서 즉시 RELEASE 후보를 만든다 — 300ms 예산과 무관하게 지연이 없다. 이
               시험은 최악 근접 시나리오(직전 비-충돌 평가주기로부터 300ms나 떨어진 시점에야
               CONFIRMED가 관측되는 상황)에서도 그 주기 자체에서 즉시 RELEASE가 관측됨을
               확인해, 300ms 예산이 항상 여유를 두고 충족됨을 보인다.
        @technique 경계값분석(Boundary Value Analysis) — 300ms 예산 상한, 평가주기 간격 스트레스
        @case Positive
        @breaks CONFIRMED 관측 주기에 RELEASE가 지연되거나 반영되지 않는 회귀
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildPhase2RawInput(0.000, True, False, rawCrashStatus="NONE"), 0.000)

        result = system.handleCycle(
            buildPhase2RawInput(0.300, True, False, rawCrashStatus="CONFIRMED"), 0.300
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestSTFUNC0019CrashConfirmedOutranksApproachRisk(unittest.TestCase):
    """ST-FUNC-0019 — SWR-007(a), 결정표기반 시험(우선순위, 동시 발생)"""

    def testCrashConfirmedReleasesLeftDoorEvenWhileApproachRiskRequestsLock(self):
        """!
        @brief crash_status가 CONFIRMED이면 다른 모든 명령(해제 억제, 잠금 명령 등)보다
               우선하여 RELEASE로 전환해야 한다(SWR-007a). 동일 평가주기에 좌측 접근위험이
               TRUE(LOCK 요구, SWR-005)와 crash_status=CONFIRMED(RELEASE 요구, SWR-007)가
               동시에 발생해도, 충돌 긴급해제가 우선한다(ENG-SWE1-001 3장 우선순위 관계:
               "충돌 긴급해제 > 접근위험 억제").
        @technique 결정표기반 시험(우선순위 결정표 E/F/I) — 상충 조건 동시발생
        @case Negative
        @breaks 접근위험 LOCK 요구에 밀려 좌측이 RELEASE로 전환되지 않는 회귀(우선순위 역전)
        """
        system = buildSystemUnderTest()

        result = system.handleCycle(
            buildPhase2RawInput(
                1.000, True, False, rawLeftApproachRisk=True, rawCrashStatus="CONFIRMED"
            ),
            1.000,
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestSTFUNC0020CrashConfirmedReleaseSustainedAcrossCycles(unittest.TestCase):
    """ST-FUNC-0020 — SWR-007(b), 상태전이 테스트(지속성, 후속 경쟁 조건 등장)"""

    def testReleaseRemainsWhileConfirmedPersistsEvenWhenApproachRiskAppearsLater(self):
        """!
        @brief crash_status가 CONFIRMED인 "동안"(상태 기반), SW는 이후 입력 주기에도 좌, 우
               출력을 RELEASE로 유지해야 한다(SWR-007b). 두 번째 평가주기(300ms 경과)에
               좌측 접근위험이 새로 TRUE가 되어도, 충돌 긴급해제가 여전히 우선하므로 RELEASE가
               유지되어야 한다.
        @technique 상태전이 테스트(State Transition Testing) — RELEASE 지속 연속성 + 우선순위
        @case Positive
        @breaks 두 번째 평가주기에서 RELEASE가 유지되지 않거나 접근위험에 밀려 LOCK으로 되돌아가는 회귀
        """
        system = buildSystemUnderTest()
        baseline = system.handleCycle(
            buildPhase2RawInput(1.000, True, False, rawCrashStatus="CONFIRMED"), 1.000
        )

        result = system.handleCycle(
            buildPhase2RawInput(
                1.300, True, False, rawCrashStatus="CONFIRMED", rawLeftApproachRisk=True
            ),
            1.300,
        )

        self.assertEqual(baseline.confirmedOutput.left, LockCommand.RELEASE)
        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestSTFUNC0021CrashPendingDoesNotPrematurelyRelease(unittest.TestCase):
    """ST-FUNC-0021 — SWR-008, 동등분할(crash_status=PENDING 클래스)"""

    def testCrashPendingAloneKeepsBootDefaultLockedOutput(self):
        """!
        @brief crash_status가 PENDING인 동안(CONFIRMED로 확인되기 전), SW는 SWR-007의
               긴급해제를 개시하지 않아야 한다(SWR-008). 다른 트리거가 전혀 없으므로 부팅
               기본값(LOCK, LOCK)이 그대로 유지되어야 한다.
        @technique 동등분할(Equivalence Partitioning) — crash_status 3값 열거형 중 PENDING 클래스
        @case Negative
        @breaks PENDING만으로도 RELEASE가 조기 개시되는 회귀(SWR-007 오탐 개시)
        """
        system = buildSystemUnderTest()

        result = system.handleCycle(
            buildPhase2RawInput(1.000, True, False, rawCrashStatus="PENDING"), 1.000
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


class TestSTFUNC0022CrashPendingDoesNotBlockOtherIndependentLogic(unittest.TestCase):
    """ST-FUNC-0022 — SWR-008, 요구사항 기반 시험(무관한 다른 SWR 로직 계속 적용)"""

    def testCrashPendingWithFireDetectedStillReleasesViaFireNotCrash(self):
        """!
        @brief crash_status가 PENDING인 동안, SW는 crash_status 판정과 무관한 기존 출력 결정
               로직(예: SWR-017)에 따른 출력을 유지해야 한다(SWR-008). PENDING과 fire_detected
               가 동시에 있을 때, RELEASE는 crash_status(PENDING은 releaseCandidate=None)가
               아니라 fire_detected(SWR-017, 독립적 후보)로부터 비롯되며, PENDING이 이 독립
               로직을 차단하지 않아야 한다.
        @technique 요구사항 기반 시험(Requirements-based Test) — SWR-008/SWR-017 상호작용
        @case Positive
        @breaks PENDING이 존재한다는 이유만으로 fire_detected에 의한 RELEASE가 차단되는 회귀
        """
        system = buildSystemUnderTest()

        result = system.handleCycle(
            buildPhase2RawInput(
                1.000, True, False, rawCrashStatus="PENDING", rawFireDetected=True
            ),
            1.000,
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestSTFUNC0023ApproachRiskBothFalseLeavesBothDoorsUnaffected(unittest.TestCase):
    """ST-FUNC-0023 — SWR-009, 전 조건 조합(FF) — 좌우 독립 4조합 중 1"""

    def testBothRiskFalseKeepsBothDoorsAtPriorReleasedState(self):
        """!
        @brief 좌/우 접근위험이 모두 FALSE이면 접근위험 로직이 양쪽 도어 모두에 영향을 주지
               않아야 한다(SWR-009). 화재로 먼저 양쪽을 RELEASE로 만든 뒤, 접근위험을 모두
               FALSE로 주입해도 RELEASE가 그대로 유지되는지 확인한다(FF 조합).
        @technique 전 조건 조합(Exhaustive Combination) — 좌/우 접근위험 2x2 조합 중 FF
        @case Negative
        @breaks 접근위험이 모두 FALSE인데도 도어 출력이 임의로 바뀌는 회귀
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildPhase2RawInput(1.000, True, False, rawFireDetected=True), 1.000)

        result = system.handleCycle(
            buildPhase2RawInput(
                1.050,
                True,
                False,
                rawFireDetected=False,
                rawLeftApproachRisk=False,
                rawRightApproachRisk=False,
            ),
            1.050,
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestSTFUNC0024ApproachRiskLeftTrueRightFalseAffectsOnlyLeft(unittest.TestCase):
    """ST-FUNC-0024 — SWR-009, 전 조건 조합(TF) — 좌우 독립 4조합 중 2"""

    def testLeftRiskTrueLocksLeftOnlyWhileRightStaysReleased(self):
        """!
        @brief 좌측 접근위험만 TRUE이면 좌측 도어만 LOCK으로 전환되고, 우측 도어는 좌측
               판정의 영향을 받지 않아야 한다(SWR-009, SWR-005a 겸용). 화재로 먼저 양쪽을
               RELEASE로 만든 뒤 좌측만 TRUE로 주입한다(TF 조합).
        @technique 전 조건 조합(Exhaustive Combination) — 좌/우 접근위험 2x2 조합 중 TF
        @case Positive
        @breaks 좌측 판정이 우측 도어 출력에 영향을 주는 회귀(교차 오염)
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildPhase2RawInput(1.000, True, False, rawFireDetected=True), 1.000)

        result = system.handleCycle(
            buildPhase2RawInput(
                1.050,
                True,
                False,
                rawFireDetected=False,
                rawLeftApproachRisk=True,
                rawRightApproachRisk=False,
            ),
            1.050,
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestSTFUNC0025ApproachRiskRightTrueLeftFalseAffectsOnlyRight(unittest.TestCase):
    """ST-FUNC-0025 — SWR-009, 전 조건 조합(FT) — 좌우 독립 4조합 중 3"""

    def testRightRiskTrueLocksRightOnlyWhileLeftStaysReleased(self):
        """!
        @brief 우측 접근위험만 TRUE이면 우측 도어만 LOCK으로 전환되고, 좌측 도어는 우측
               판정의 영향을 받지 않아야 한다(SWR-009, SWR-005a 겸용). FT 조합(좌우 대칭 확인).
        @technique 전 조건 조합(Exhaustive Combination) — 좌/우 접근위험 2x2 조합 중 FT
        @case Positive
        @breaks 우측 판정이 좌측 도어 출력에 영향을 주는 회귀(교차 오염, 대칭성 위반)
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildPhase2RawInput(1.000, True, False, rawFireDetected=True), 1.000)

        result = system.handleCycle(
            buildPhase2RawInput(
                1.050,
                True,
                False,
                rawFireDetected=False,
                rawLeftApproachRisk=False,
                rawRightApproachRisk=True,
            ),
            1.050,
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


class TestSTFUNC0026ApproachRiskBothTrueLocksBothDoors(unittest.TestCase):
    """ST-FUNC-0026 — SWR-009, 전 조건 조합(TT) — 좌우 독립 4조합 중 4"""

    def testBothRiskTrueLocksBothDoorsIndependently(self):
        """!
        @brief 좌/우 접근위험이 모두 TRUE이면 양쪽 도어 모두 독립적으로 LOCK으로 전환되어야
               한다(SWR-009). TT 조합(전 조건 조합의 마지막 경우).
        @technique 전 조건 조합(Exhaustive Combination) — 좌/우 접근위험 2x2 조합 중 TT
        @case Positive
        @breaks 한쪽만 LOCK되고 다른 쪽이 반영되지 않는 회귀
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildPhase2RawInput(1.000, True, False, rawFireDetected=True), 1.000)

        result = system.handleCycle(
            buildPhase2RawInput(
                1.050,
                True,
                False,
                rawFireDetected=False,
                rawLeftApproachRisk=True,
                rawRightApproachRisk=True,
            ),
            1.050,
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


class TestSTFUNC0027FireDetectedAloneReleasesBothDoors(unittest.TestCase):
    """ST-FUNC-0027 — SWR-017(a), 동등분할(fire_detected 단독 클래스)"""

    def testFireDetectedTrueAloneReleasesBothDoors(self):
        """!
        @brief fire_detected가 유효한 TRUE로 확인되면 다음 평가주기 내에 좌, 우 출력을 모두
               RELEASE로 전환해야 한다(SWR-017a). 부팅 기본값(LOCK, LOCK)에서 단독 트리거로
               전환됨을 확인한다.
        @technique 동등분할(Equivalence Partitioning) — fire_detected=TRUE 단독 클래스
        @case Positive
        @breaks fire_detected 단독 TRUE인데도 RELEASE로 전환되지 않는 회귀
        """
        system = buildSystemUnderTest()

        result = system.handleCycle(
            buildPhase2RawInput(1.000, True, False, rawFireDetected=True), 1.000
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestSTFUNC0028OvertemperatureDetectedAloneReleasesBothDoors(unittest.TestCase):
    """ST-FUNC-0028 — SWR-017(a), 동등분할(overtemperature_detected 단독 클래스)"""

    def testOvertemperatureDetectedTrueAloneReleasesBothDoors(self):
        """!
        @brief overtemperature_detected가 유효한 TRUE로 확인되면 다음 평가주기 내에 좌, 우
               출력을 모두 RELEASE로 전환해야 한다(SWR-017a).
        @technique 동등분할(Equivalence Partitioning) — overtemperature_detected=TRUE 단독 클래스
        @case Positive
        @breaks overtemperature_detected 단독 TRUE인데도 RELEASE로 전환되지 않는 회귀
        """
        system = buildSystemUnderTest()

        result = system.handleCycle(
            buildPhase2RawInput(1.000, True, False, rawOvertemperatureDetected=True), 1.000
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestSTFUNC0029AdultPresentAloneReleasesBothDoors(unittest.TestCase):
    """ST-FUNC-0029 — SWR-017(a), 동등분할(adult_present 단독 클래스)"""

    def testAdultPresentTrueAloneReleasesBothDoors(self):
        """!
        @brief adult_present가 유효한 TRUE로 확인되면 다음 평가주기 내에 좌, 우 출력을 모두
               RELEASE로 전환해야 한다(SWR-017a).
        @technique 동등분할(Equivalence Partitioning) — adult_present=TRUE 단독 클래스
        @case Positive
        @breaks adult_present 단독 TRUE인데도 RELEASE로 전환되지 않는 회귀
        """
        system = buildSystemUnderTest()

        result = system.handleCycle(
            buildPhase2RawInput(1.000, True, False, rawAdultPresent=True), 1.000
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestSTFUNC0030AllThreeForcedReleaseTriggersSimultaneously(unittest.TestCase):
    """ST-FUNC-0030 — SWR-017(b), 전 조건 조합(복수 입력 동시 대표값)"""

    def testFireOvertemperatureAdultAllTrueSimultaneouslyStillReleasesBothDoors(self):
        """!
        @brief fire_detected, overtemperature_detected, adult_present 중 하나 이상이 TRUE이면
               RELEASE해야 하며, 복수 입력이 동시에 TRUE여도 출력이 RELEASE로 유지되어야
               한다(SWR-017a/b). fire_detected/overtemperature_detected/adult_present 각각의
               단독 클래스는 ST-FUNC-0027~0029에서 이미 검증했으므로, 여기서는 "3개 모두
               TRUE" 대표값만으로 복수 입력 동시발생 클래스를 대표한다(의미 없는 조합 전수
               나열을 피함).
        @technique 전 조건 조합(Exhaustive Combination) — 복수 입력 동시발생 대표값(전부 TRUE)
        @case Positive
        @breaks 복수 트리거 동시발생 시 RELEASE가 아닌 다른 값으로 오판정되는 회귀
        """
        system = buildSystemUnderTest()

        result = system.handleCycle(
            buildPhase2RawInput(
                1.000,
                True,
                False,
                rawFireDetected=True,
                rawOvertemperatureDetected=True,
                rawAdultPresent=True,
            ),
            1.000,
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


if __name__ == "__main__":
    unittest.main()
