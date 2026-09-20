"""!
@file test_st_func_swr003_018_020.py
@brief 시스템 테스트(SWE.6) — Phase 3 차량상태 기반 잠금/해제 + ISOFIX 강제잠금(SWR-003,
       SWR-018, SWR-020). 테스트 베이시스는
       Deliverables/Engineering/SoftwareRequirementsAnalysis/ENG-SWE1-001(SW 요구사항 명세서
       v0.3) 4.1절이며, 아키텍처/상세설계 문서가 아니다. 진입점은 InputValidationAdapter.
       handleCycle()(원시 Vehicle 입력 -> CycleResult, st_helpers.buildSystemUnderTest() 참조,
       ledger 누적 갭 9 방침).

각 테스트 클래스는 ENG-SWE6-001의 Test ID(ST-FUNC-0031~0047)와 1:1 대응한다.

@par 시스템 경계 공통 한계(ENG-SWE1-001 8장 가정, ledger 갭 10)
CycleResult{confirmedOutput, stateResult, errorOccurred}는 stateResult.warningReasonCode를
노출하므로(SWR-020(a)의 "ignition_off 이유코드 제공" 수용기준은 이 필드로 직접 관측 가능
하다) Phase2와 달리 이번 Phase는 이유코드 관측에 구조적 한계가 없다. 다만 ArbitrationResult의
leftReasonCode/rightReasonCode(SWR-005/006/017 계열, Phase2 이유코드)는 여전히 노출되지
않으므로(갭 10), 이번 파일의 우선순위 결정표 케이스도 confirmedOutput(LOCK/RELEASE)과
stateResult만으로 판정한다.

@par 다루지 않는 범위(ENG-SWE1-001 8장 가정, 검증 범위 제외 — 임의 해석 금지)
- SWR-003 비고: 차속이 3 km/h 미만으로 재하강했을 때의 동작(가정 20) — 코드에 해당 로직
  자체가 없어(ARC-0014는 조건 미성립 시 후보 미생성만 함) 검증 범위에서 제외한다.
- SWR-018 비고: isofix TRUE인 동안 해제요청을 SWR-005처럼 명시적으로 억제하는지 여부(가정
  16) — 억제 메커니즘 자체가 설계/코드에 없어 검증 범위에서 제외한다(SWR-005와 달리 재입력
  채널을 통한 "해제요청" 자극 자체가 시스템 경계에 없다는 점도 Phase2 ST-FUNC-0016과 동일).
- SWR-020 비고: OFF와 DEGRADED/FAULT의 동시성 시나리오(가정 17), 접근위험(ASIL B)과
  ignition-off(QM)의 최종 확정 여부(가정 18) — 아래 우선순위 결정표 케이스(ST-FUNC-0044~
  0047)는 "현재 동작을 재확인"하는 성격으로만 다루며, OEM-A 확인 없이 최종 확정되었다고
  단정하지 않는다(ledger 갭 16, IT-0112/IT-0135와 교차 참조).
"""

import unittest

from tests_system.st_helpers import LockCommand, SystemState, buildPhase3RawInput, buildSystemUnderTest


class TestSTFUNC0031VehicleSpeedBelowThresholdDoesNotLock(unittest.TestCase):
    """ST-FUNC-0031 — SWR-003(a), 경계값분석(2.9km/h, 임계 미만)"""

    def testSpeedJustBelowThresholdKeepsReleasedOutputUnlocked(self):
        """!
        @brief 유효한 vehicle_speed_kph가 3km/h 미만(2.9km/h)이면 자동주행잠금 후보가
               생성되지 않아야 한다(SWR-003a 부정 경로). 먼저 ignition-off로 양쪽을
               RELEASE로 만든 뒤(부팅 기본값 LOCK과 구분하기 위한 사전조건), ignition을 다시
               켜고 2.9km/h를 주입해도 LOCK으로 전환되지 않고 RELEASE가 유지되는지 확인한다.
        @technique 경계값분석(Boundary Value Analysis) — 3km/h 임계 미만 경계(2.9km/h)
        @case Negative
        @breaks 임계값 미만인데도 LOCK 후보가 생성되어 출력이 LOCK으로 바뀌는 회귀
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildPhase3RawInput(1.000, False, False), 1.000)

        result = system.handleCycle(
            buildPhase3RawInput(1.050, True, False, rawVehicleSpeedKph=2.9), 1.050
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestSTFUNC0032VehicleSpeedAtThresholdLocksImmediately(unittest.TestCase):
    """ST-FUNC-0032 — SWR-003(a), 경계값분석(3.0km/h, 임계 정확히 일치)"""

    def testSpeedExactlyAtThresholdLocksFromFirstCycle(self):
        """!
        @brief 유효한 vehicle_speed_kph가 3km/h 이상으로 확인되는 첫 평가주기부터 좌, 우
               출력을 LOCK으로 설정해야 한다(SWR-003a). 정확히 3.0km/h(경계값)로 전이시켜
               "이상" 조건이 경계값 자체를 포함함을 확인한다.
        @technique 경계값분석(Boundary Value Analysis) — 3km/h 임계값 자체(3.0km/h)
        @case Positive
        @breaks 정확히 3.0km/h에서는 LOCK으로 전환되지 않는 경계 오류(<= vs < 부호 오류)
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildPhase3RawInput(1.000, False, False), 1.000)

        result = system.handleCycle(
            buildPhase3RawInput(1.050, True, False, rawVehicleSpeedKph=3.0), 1.050
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


class TestSTFUNC0033VehicleSpeedAboveThresholdLocks(unittest.TestCase):
    """ST-FUNC-0033 — SWR-003(a), 경계값분석(3.1km/h, 임계 초과)"""

    def testSpeedJustAboveThresholdLocksFromFirstCycle(self):
        """!
        @brief 유효한 vehicle_speed_kph가 3km/h를 초과(3.1km/h)해도 첫 평가주기부터 LOCK으로
               설정되어야 한다(SWR-003a).
        @technique 경계값분석(Boundary Value Analysis) — 3km/h 임계 초과 경계(3.1km/h)
        @case Positive
        @breaks 임계값을 초과했는데도 LOCK으로 전환되지 않는 회귀
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildPhase3RawInput(1.000, False, False), 1.000)

        result = system.handleCycle(
            buildPhase3RawInput(1.050, True, False, rawVehicleSpeedKph=3.1), 1.050
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


class TestSTFUNC0034VehicleSpeedLockSustainedAcrossCycles(unittest.TestCase):
    """ST-FUNC-0034 — SWR-003(b), 상태전이 테스트(LOCK 유지 지속성)"""

    def testLockMaintainedWhileSpeedStaysAtOrAboveThreshold(self):
        """!
        @brief vehicle_speed_kph가 유효한 값 3km/h 이상으로 유지되는 동안 좌, 우 출력을
               LOCK으로 유지해야 한다(SWR-003b). 두 번째 평가주기에도 임계 이상 속도가
               유지되면 LOCK이 그대로 유지되는지 확인한다.
        @technique 상태전이 테스트(State Transition Testing) — LOCK 지속 연속성
        @case Positive
        @breaks 두 번째 평가주기에서 LOCK이 임의로 풀리는 회귀
        """
        system = buildSystemUnderTest()
        baseline = system.handleCycle(
            buildPhase3RawInput(1.000, True, False, rawVehicleSpeedKph=10.0), 1.000
        )

        result = system.handleCycle(
            buildPhase3RawInput(1.050, True, False, rawVehicleSpeedKph=10.0), 1.050
        )

        self.assertEqual(baseline.confirmedOutput.left, LockCommand.LOCK)
        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


class TestSTFUNC0035VehicleSpeedOutOfRangeDoesNotLock(unittest.TestCase):
    """ST-FUNC-0035 — SWR-003, 오류추측 + 동등분할(범위 오류 무효 클래스)"""

    def testOutOfRangeSpeedValueProducesNoLockCandidate(self):
        """!
        @brief vehicle_speed_kph가 정의된 유효 범위(0.0~300.0)를 벗어나면(301.0) 자동주행
               잠금 후보가 생성되지 않아야 한다(SWR-013b 형식/범위 오류 거절 원칙이 SWR-003
               입력에도 적용됨을 재확인). 먼저 ignition-off로 RELEASE를 만든 뒤 범위 오류
               속도를 주입해도 LOCK으로 바뀌지 않는지 확인한다.
        @technique 오류추측(Error Guessing) + 동등분할(Equivalence Partitioning) — 범위 오류
                   무효 클래스(301.0 > VEHICLE_SPEED_MAX_KPH)
        @case Negative
        @breaks 범위 오류 값이 그대로 통과해 LOCK 후보를 생성하는 회귀
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildPhase3RawInput(1.000, False, False), 1.000)

        result = system.handleCycle(
            buildPhase3RawInput(1.050, True, False, rawVehicleSpeedKph=301.0), 1.050
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestSTFUNC0036IsofixBothFalseLeavesBothDoorsUnaffected(unittest.TestCase):
    """ST-FUNC-0036 — SWR-018(b), 전 조건 조합(FF) — 좌우 독립 4조합 중 1"""

    def testBothIsofixFalseKeepsBothDoorsAtPriorReleasedState(self):
        """!
        @brief 좌/우 isofix가 모두 FALSE이면 ISOFIX 강제잠금 로직이 양쪽 도어 모두에 영향을
               주지 않아야 한다(SWR-018, ISOFIXLockResult 좌우 독립 불변조건). ignition-off로
               먼저 RELEASE를 만든 뒤 FF를 주입해도 RELEASE가 그대로 유지되는지 확인한다.
        @technique 전 조건 조합(Exhaustive Combination) — 좌/우 isofix 2x2 조합 중 FF
        @case Negative
        @breaks isofix가 모두 FALSE인데도 도어 출력이 임의로 바뀌는 회귀
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildPhase3RawInput(1.000, False, False), 1.000)

        result = system.handleCycle(
            buildPhase3RawInput(
                1.050, True, False, rawIsofixLeft=False, rawIsofixRight=False
            ),
            1.050,
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestSTFUNC0037IsofixLeftFalseRightTrueLocksOnlyRight(unittest.TestCase):
    """ST-FUNC-0037 — SWR-018(a)/(b), 전 조건 조합(FT) — 좌우 독립 4조합 중 2"""

    def testRightIsofixTrueLocksRightOnlyWhileLeftStaysReleased(self):
        """!
        @brief isofix_right만 유효한 TRUE이면 우측 도어만 LOCK으로 전환되고, 좌측 도어는
               반대쪽 도어의 판정 결과대로(이 요구사항과 무관하게) 유지되어야 한다(SWR-018a/b).
        @technique 전 조건 조합(Exhaustive Combination) — 좌/우 isofix 2x2 조합 중 FT
        @case Positive
        @breaks 우측 판정이 좌측 도어 출력에 영향을 주는 회귀(교차 오염)
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildPhase3RawInput(1.000, False, False), 1.000)

        result = system.handleCycle(
            buildPhase3RawInput(
                1.050, True, False, rawIsofixLeft=False, rawIsofixRight=True
            ),
            1.050,
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


class TestSTFUNC0038IsofixLeftTrueRightFalseLocksOnlyLeft(unittest.TestCase):
    """ST-FUNC-0038 — SWR-018(a)/(b), 전 조건 조합(TF) — 좌우 독립 4조합 중 3"""

    def testLeftIsofixTrueLocksLeftOnlyWhileRightStaysReleased(self):
        """!
        @brief isofix_left만 유효한 TRUE이면 좌측 도어만 LOCK으로 전환되고, 우측 도어는
               반대쪽(SWR-018) 판정의 영향을 받지 않아야 한다(SWR-018a/b, 좌우 대칭 확인).
        @technique 전 조건 조합(Exhaustive Combination) — 좌/우 isofix 2x2 조합 중 TF
        @case Positive
        @breaks 좌측 판정이 우측 도어 출력에 영향을 주는 회귀(교차 오염, 대칭성 위반)
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildPhase3RawInput(1.000, False, False), 1.000)

        result = system.handleCycle(
            buildPhase3RawInput(
                1.050, True, False, rawIsofixLeft=True, rawIsofixRight=False
            ),
            1.050,
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestSTFUNC0039IsofixBothTrueLocksBothDoors(unittest.TestCase):
    """ST-FUNC-0039 — SWR-018(a), 전 조건 조합(TT) — 좌우 독립 4조합 중 4"""

    def testBothIsofixTrueLocksBothDoorsIndependently(self):
        """!
        @brief isofix_left, isofix_right가 모두 유효한 TRUE이면 양쪽 도어 모두 독립적으로
               LOCK으로 전환되어야 한다(SWR-018a). TT 조합(전 조건 조합의 마지막 경우).
        @technique 전 조건 조합(Exhaustive Combination) — 좌/우 isofix 2x2 조합 중 TT
        @case Positive
        @breaks 한쪽만 LOCK되고 다른 쪽이 반영되지 않는 회귀
        """
        system = buildSystemUnderTest()

        result = system.handleCycle(
            buildPhase3RawInput(
                1.000, True, False, rawIsofixLeft=True, rawIsofixRight=True
            ),
            1.000,
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


class TestSTFUNC0040IsofixLeftInvalidProducesNoCandidateWhileRightIndependent(unittest.TestCase):
    """ST-FUNC-0040 — SWR-018, 오류추측(형식 오류) + 좌우 독립 재확인"""

    def testInvalidLeftIsofixFieldDoesNotLockLeftWhileRightStillLocksFromValidTrue(self):
        """!
        @brief isofix_left에 형식 오류(불리언이 아닌 값)가 포함되면 해당 도어의 강제잠금
               후보가 생성되지 않아야 하며(SWR-013b 형식 오류 거절 원칙의 SWR-018 재확인),
               이 오류가 반대쪽(우측, 유효한 TRUE)의 독립적 판정에 영향을 주지 않아야 한다
               (SWR-018b 좌우 독립).
        @technique 오류추측(Error Guessing) — 형식 오류 무효 클래스(non-bool) + 좌우 독립 결합
        @case Negative
        @breaks 좌측 형식 오류가 좌측을 임의로 LOCK시키거나 우측 판정에 영향을 주는 회귀
        """
        system = buildSystemUnderTest()
        system.handleCycle(buildPhase3RawInput(1.000, False, False), 1.000)

        result = system.handleCycle(
            buildPhase3RawInput(
                1.050, True, False, rawIsofixLeft="TRUE", rawIsofixRight=True
            ),
            1.050,
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


class TestSTFUNC0041IgnitionOffReleasesAndTransitionsToOffWithReasonCode(unittest.TestCase):
    """ST-FUNC-0041 — SWR-020(a), 요구사항 기반 시험(이벤트 기반 전이 + 이유코드)"""

    def testIgnitionOnFalseTransitionReleasesBothDoorsSetsOffStateAndReasonCode(self):
        """!
        @brief ignition_on이 유효한 값 FALSE로 전이되는 첫 평가주기에, 좌, 우 출력을
               RELEASE로 전환하고 시스템 상태를 OFF로 전이하며 ignition_off 이유코드를
               제공해야 한다(SWR-020a). 이유코드는 CycleResult.stateResult.warningReasonCode
               로 직접 관측 가능하다(Phase2의 ArbitrationResult 이유코드와 달리 구조적 한계
               없음).
        @technique 요구사항 기반 시험(Requirements-based Test) — SWR-020(a) 인수 시나리오
        @case Positive
        @breaks ignition-off 전이 시 RELEASE/OFF/이유코드 중 하나라도 반영되지 않는 회귀
        """
        system = buildSystemUnderTest()
        baseline = system.handleCycle(buildPhase3RawInput(1.000, True, False), 1.000)

        result = system.handleCycle(buildPhase3RawInput(1.050, False, False), 1.050)

        self.assertEqual(baseline.stateResult.state, SystemState.NORMAL)
        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)
        self.assertEqual(result.stateResult.state, SystemState.OFF)
        self.assertIsInstance(result.stateResult.warningReasonCode, str)
        self.assertTrue(len(result.stateResult.warningReasonCode) > 0)


class TestSTFUNC0042IgnitionOffSustainedAcrossCycles(unittest.TestCase):
    """ST-FUNC-0042 — SWR-020(b), 상태전이 테스트(RELEASE/OFF 유지 지속성)"""

    def testReleaseAndOffStateMaintainedWhileIgnitionStaysFalse(self):
        """!
        @brief ignition_on이 유효한 값 FALSE로 유지되는 동안, 좌, 우 출력을 RELEASE로,
               시스템 상태를 OFF로 유지해야 한다(SWR-020b).
        @technique 상태전이 테스트(State Transition Testing) — RELEASE/OFF 지속 연속성
        @case Positive
        @breaks 두 번째 평가주기에서 RELEASE/OFF가 유지되지 않는 회귀
        """
        system = buildSystemUnderTest()
        baseline = system.handleCycle(buildPhase3RawInput(1.000, False, False), 1.000)

        result = system.handleCycle(buildPhase3RawInput(1.050, False, False), 1.050)

        self.assertEqual(baseline.stateResult.state, SystemState.OFF)
        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)
        self.assertEqual(result.stateResult.state, SystemState.OFF)


class TestSTFUNC0043IgnitionOnFieldInvalidDoesNotJudgeOff(unittest.TestCase):
    """ST-FUNC-0043 — SWR-020/SWR-013(b), 오류추측(형식 오류) — SW 설계 재량 확정 사항 회귀"""

    def testInvalidIgnitionOnFieldDoesNotTransitionToOffAndBlocksArbitration(self):
        """!
        @brief ignition_on 필드에 형식 오류(불리언이 아닌 값)가 포함되면 SW는 OFF를 판정하지
               않아야 한다(ENG-SWE3-001 8.8절 SW 설계 재량 확정 — IU-0003/IU-0016 대칭 미판정).
               동시에 SWR-013(b)에 따라 이 형식 오류 입력은 명령 평가 이전에 거절되므로
               (IF-0008 게이트, composeInputValid), 이번 평가주기의 출력은 어떤 후보도 반영하지
               않고 직전 확정값(부팅 기본값 LOCK, LOCK)을 그대로 유지해야 한다.
        @technique 오류추측(Error Guessing) — 형식 오류 무효 클래스(non-bool ignition_on)
        @case Negative
        @breaks 형식 오류 ignition_on이 OFF로 오판정되거나, 거절되지 않고 출력에 반영되는 회귀
        """
        system = buildSystemUnderTest()

        result = system.handleCycle(buildPhase3RawInput(1.000, "FALSE", False), 1.000)

        self.assertFalse(result.errorOccurred)
        self.assertNotEqual(result.stateResult.state, SystemState.OFF)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.LOCK)


class TestSTFUNC0044CrashConfirmedOutranksAutoDriveLock(unittest.TestCase):
    """ST-FUNC-0044 — SWR-003 vs SWR-007, 결정표기반 시험(우선순위 1 vs 6)"""

    def testCrashConfirmedReleasesEvenWhileVehicleSpeedRequestsLock(self):
        """!
        @brief crash_status가 CONFIRMED(priority=1, RELEASE, SWR-007a "다른 모든 명령보다
               우선")이면, vehicle_speed_kph가 임계 이상(priority=6, LOCK, SWR-003)이어도
               RELEASE가 승리해야 한다. 이 우선순위 관계는 SWR-007(a) 원문에 직접 근거하며
               (ENG-SWE1-001 3장 우선순위 관계 확장), OEM-A 확인이 추가로 필요한 사항이 아니다.
        @technique 결정표기반 시험(Command Arbiter 우선순위 결정표, priority 1 vs 6) — 상충
                   조건 동시발생
        @case Negative
        @breaks 자동주행잠금(LOCK)에 밀려 출력이 RELEASE로 전환되지 않는 우선순위 역전 회귀
        """
        system = buildSystemUnderTest()

        result = system.handleCycle(
            buildPhase3RawInput(
                1.000, True, False, rawCrashStatus="CONFIRMED", rawVehicleSpeedKph=20.0
            ),
            1.000,
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestSTFUNC0045FireForcedReleaseOutranksIsofixForcedLock(unittest.TestCase):
    """ST-FUNC-0045 — SWR-018 vs SWR-017, 결정표기반 시험(우선순위 3 vs 5) — SW 설계 추론"""

    def testFireDetectedReleasesEvenWhileIsofixRequestsLock(self):
        """!
        @brief fire_detected(priority=3, RELEASE, SWR-017)와 isofix_left/right(priority=5,
               LOCK, SWR-018)가 동시에 성립하면 RELEASE가 승리해야 한다. [적용 한계] 이
               상대적 순서(화재 등 강제해제가 ISOFIX 강제잠금보다 우선)는 OEM 원문이 직접
               규정하지 않으며, 탑승자 탈출/구조 보장 취지에 따른 SW 설계 추론이다(
               ENG-SWE1-001 3장 우선순위 관계 확장, 8장 가정 15 — 완전한 OEM 확인은 아님).
               이 시험은 "현재 구현된 우선순위 체인이 설계 그대로 동작함"을 확인하는 것이며,
               이 순서 자체가 OEM-A에 의해 최종 확정되었다고 단정하지 않는다.
        @technique 결정표기반 시험(Command Arbiter 우선순위 결정표, priority 3 vs 5) — 상충
                   조건 동시발생
        @case Negative
        @breaks ISOFIX 강제잠금(LOCK)에 밀려 출력이 RELEASE로 전환되지 않는 우선순위 역전 회귀
        """
        system = buildSystemUnderTest()

        result = system.handleCycle(
            buildPhase3RawInput(
                1.000, True, False, rawFireDetected=True, rawIsofixLeft=True, rawIsofixRight=True
            ),
            1.000,
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)


class TestSTFUNC0046IgnitionOffOutranksIsofixAndAutoDriveLock(unittest.TestCase):
    """ST-FUNC-0046 — SWR-020 vs SWR-018/SWR-003, 결정표기반 시험(우선순위 4 vs 5,6)"""

    def testIgnitionOffReleasesEvenWhileIsofixAndSpeedBothRequestLock(self):
        """!
        @brief ignition_on=FALSE(priority=4, RELEASE, SWR-020)가 isofix_left/right(priority=5,
               LOCK, SWR-018)와 vehicle_speed_kph 임계 이상(priority=6, LOCK, SWR-003)에
               동시에 우선하는지 확인한다(ledger 누적 갭 13 대부분 해소 사항의 시스템 수준
               재확인 — entrapment 방지 취지에 따른 SW 설계 재량, ENG-SWE2-001 9장). 상태값도
               OFF로 전이됨을 함께 확인해, "state==OFF가 candidateCommands를 제한하지 않고
               ignition-off 후보 자체의 우선순위 승리로 RELEASE가 달성됨"이라는 설계 결정을
               시스템 경계에서 재확인한다.
        @technique 결정표기반 시험(Command Arbiter 우선순위 결정표, priority 4 vs 5/6) — 상충
                   조건 동시발생, 3중 동시발생
        @case Negative
        @breaks ISOFIX/자동주행잠금(LOCK)에 밀려 출력이 RELEASE로 전환되지 않는 우선순위 역전 회귀
        """
        system = buildSystemUnderTest()

        result = system.handleCycle(
            buildPhase3RawInput(
                1.000,
                False,
                False,
                rawIsofixLeft=True,
                rawIsofixRight=True,
                rawVehicleSpeedKph=20.0,
            ),
            1.000,
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.RELEASE)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)
        self.assertEqual(result.stateResult.state, SystemState.OFF)


class TestSTFUNC0047ApproachRiskCurrentlyOutranksIgnitionOffOnAffectedDoor(unittest.TestCase):
    """ST-FUNC-0047 — SWR-005/006 vs SWR-020, 결정표기반 시험(우선순위 2 vs 4) — 갭16 재확인 전용"""

    def testLeftApproachRiskKeepsLockOnLeftWhileIgnitionOffReleasesRightAndSetsOffState(self):
        """!
        @brief 좌측 접근위험(priority=2, LOCK, ASIL B, SWR-005)과 ignition_on=FALSE(
               priority=4, RELEASE, QM, SWR-020)이 동시에 성립하는 경우의 현재 구현 동작을
               재확인한다: 좌측 도어는 접근위험이 이겨 LOCK을 유지하고, 접근위험이 없는
               우측 도어는 ignition-off가 RELEASE로 전환한다. 시스템 상태는 접근위험과 무관하게
               OFF로 전이된다(state==OFF가 candidateCommands를 제한하지 않는다는 설계 결정).
               [단정 금지] 이 우선순위(ASIL B 접근위험이 QM ignition-off보다 항상 이긴다)는
               Command Arbiter의 잠정 기본값일 뿐이며(ENG-SWE2-001 9장), OEM-A의 명시적 확인
               없이 이 관계가 최종 확정되었다고 단정하지 않는다(ENG-SWE1-001 8장 가정 18,
               ledger 누적 갭 16). 이 시험은 "현재 동작을 회귀 고정"하는 목적이며, 이 동작이
               요구사항 수용기준이라고 주장하지 않는다 — ENG-SWE5-002의 IT-0112(단위 수준)·
               IT-0135(통합 전체 체인 수준)와 동일한 성격의 시스템 수준 재확인이다.
        @technique 결정표기반 시험(Command Arbiter 우선순위 결정표, priority 2 vs 4) — 상충
                   조건 동시발생(현재 동작 재확인 전용, 인수기준 확정 아님)
        @case Negative
        @breaks 좌측이 LOCK을 유지하지 못하거나(우선순위 역전), 우측이 RELEASE로 전환되지
                않거나(ignition-off 무시), 상태가 OFF로 전이되지 않는 회귀
        """
        system = buildSystemUnderTest()

        result = system.handleCycle(
            buildPhase3RawInput(1.000, False, False, rawLeftApproachRisk=True), 1.000
        )

        self.assertFalse(result.errorOccurred)
        self.assertEqual(result.confirmedOutput.left, LockCommand.LOCK)
        self.assertEqual(result.confirmedOutput.right, LockCommand.RELEASE)
        self.assertEqual(result.stateResult.state, SystemState.OFF)


if __name__ == "__main__":
    unittest.main()
