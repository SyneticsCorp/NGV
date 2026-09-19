"""!
@file test_it_step12_command_arbiter_priority_chain.py
@brief 통합 12단계 — ARC-0005(Command Arbiter, 우선순위 규칙 체인 확장), IF-0008 인터페이스
       계약 검증(Phase2 갱신).

테스트 베이시스: ENG-SWE2-001 6.1절(IF-0008), 11장 순서표 12행("단위시험 하네스, 8~11단계
결과를 모사한 candidateCommands 합성 주입 — 우선순위 충돌·문별 독립성 시험 포함"). 8~11단계
실물은 불필요(파라미터로 합성 입력). ENG-SWE3-001 7장 결정표 I(문별 후보 선택)를 그대로
사용하며, 12장/6장이 요구한 "1~4단계(Phase1 게이트 로직) 회귀" — 신규 규칙 추가가
FAULT/inputInvalid 게이트를 깨지 않는지도 함께 확인한다.
"""

import unittest

from tests_integration.it_helpers import (
    ArbitrationCommand,
    Door,
    SystemState,
    buildCandidateCommand,
    buildStateResult,
)
from ngv.core.command_arbiter import CommandArbiter


class TestIT0069CrashPriorityWinsOverApproachRiskOnBothDoors(unittest.TestCase):
    """IT-0069 — Trace: IF-0008/IF-0016/IF-0017 / SWR-005, SWR-007, 결정표 I, 7장 시나리오 7"""

    def testCrashCandidateOverridesLeftApproachRiskSuppression(self):
        """!
        @brief 충돌(priority=1, BOTH, RELEASE)과 접근위험 억제(priority=2, LEFT, LOCK)가 동시에
               존재하면 LEFT/RIGHT 모두 RELEASE가 선택되어야 한다(3장 우선순위: 충돌 > 접근위험,
               7장 시나리오 7과 동일한 구도를 합성 입력으로 재현).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 I, 우선순위 충돌(1 vs 2)
        @case Positive
        @breaks 낮은 우선순위(접근위험 억제)가 잘못 선택되거나 RIGHT가 영향받지 않는 회귀
        """
        arbiter = CommandArbiter()
        candidates = [
            buildCandidateCommand(Door.BOTH, ArbitrationCommand.RELEASE, 1, "CRASH_CONFIRMED"),
            buildCandidateCommand(Door.LEFT, ArbitrationCommand.LOCK, 2, "APPROACH_RISK_LEFT"),
        ]

        result = arbiter.arbitrate(buildStateResult(SystemState.NORMAL), True, candidates)

        self.assertFalse(result.blocked)
        self.assertEqual(result.leftCommand, ArbitrationCommand.RELEASE)
        self.assertEqual(result.rightCommand, ArbitrationCommand.RELEASE)
        self.assertEqual(result.leftReasonCode, "CRASH_CONFIRMED")
        self.assertEqual(result.rightReasonCode, "CRASH_CONFIRMED")


class TestIT0070ApproachRiskPriorityWinsOverFireOnLeftDoor(unittest.TestCase):
    """IT-0070 — Trace: IF-0008/IF-0017/IF-0019 / SWR-005, SWR-017, 결정표 I"""

    def testApproachRiskCandidateOverridesFireOnLeftButNotRight(self):
        """!
        @brief 접근위험 억제(priority=2, LEFT, LOCK)와 화재 강제해제(priority=3, BOTH, RELEASE)가
               동시에 존재하면 LEFT는 LOCK(우선순위 2가 승리), RIGHT는 RELEASE(priority=3만
               적용 가능)여야 한다(3장 우선순위: 접근위험 > 화재 등).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 I, 우선순위 충돌(2 vs 3)
        @case Positive
        @breaks LEFT에도 화재 후보(RELEASE)가 잘못 적용되는 회귀
        """
        arbiter = CommandArbiter()
        candidates = [
            buildCandidateCommand(Door.LEFT, ArbitrationCommand.LOCK, 2, "APPROACH_RISK_LEFT"),
            buildCandidateCommand(Door.BOTH, ArbitrationCommand.RELEASE, 3, "FORCED_RELEASE"),
        ]

        result = arbiter.arbitrate(buildStateResult(SystemState.NORMAL), True, candidates)

        self.assertEqual(result.leftCommand, ArbitrationCommand.LOCK)
        self.assertEqual(result.leftReasonCode, "APPROACH_RISK_LEFT")
        self.assertEqual(result.rightCommand, ArbitrationCommand.RELEASE)
        self.assertEqual(result.rightReasonCode, "FORCED_RELEASE")


class TestIT0071DoorSpecificCandidateDoesNotAffectOtherDoor(unittest.TestCase):
    """IT-0071 — Trace: IF-0008/IF-0017 / SWR-009, 결정표 I(문별 독립성)"""

    def testLeftOnlyCandidateLeavesRightAsNoChange(self):
        """!
        @brief LEFT 전용 후보만 존재하면 LEFT만 반영되고 RIGHT는 적용 가능한 후보가 없어
               NO_CHANGE로 남아야 한다(문별 독립성).
        @technique 동등분할(Equivalence Partitioning) — 문별 적용 가능 후보 유/무 대표값
        @case Positive
        @breaks LEFT 전용 후보가 RIGHT에도 잘못 적용되는 회귀(door 필터링 결함)
        """
        arbiter = CommandArbiter()
        candidates = [buildCandidateCommand(Door.LEFT, ArbitrationCommand.LOCK, 2, "APPROACH_RISK_LEFT")]

        result = arbiter.arbitrate(buildStateResult(SystemState.NORMAL), True, candidates)

        self.assertEqual(result.leftCommand, ArbitrationCommand.LOCK)
        self.assertEqual(result.rightCommand, ArbitrationCommand.NO_CHANGE)
        self.assertIsNone(result.rightReasonCode)


class TestIT0072DuplicateMinimumPriorityOnSameDoorRaises(unittest.TestCase):
    """IT-0072 — Trace: IF-0008 / 결정표 I 비고(설계상 불변조건), 오류주입"""

    def testTwoCandidatesWithSamePriorityOnSameDoorRaisesValueError(self):
        """!
        @brief 동일 문에 동일 최소 priority 후보가 2개 이상 존재하면 설계상 발생 불가한 내부
               불변조건 위반으로 간주해 ValueError를 발생시켜야 한다(ENG-SWE3-001 5.2절/결정표 I).
        @technique 오류주입(Fault Injection Test) — 불변조건 위반(중복 priority) 주입
        @case Negative
        @breaks 충돌하는 두 후보 중 하나가 임의로 선택되고 예외가 발생하지 않는 회귀
        """
        arbiter = CommandArbiter()
        candidates = [
            buildCandidateCommand(Door.BOTH, ArbitrationCommand.RELEASE, 1, "CRASH_CONFIRMED"),
            buildCandidateCommand(Door.BOTH, ArbitrationCommand.LOCK, 1, "DUPLICATE_PRIORITY"),
        ]

        with self.assertRaises(ValueError):
            arbiter.arbitrate(buildStateResult(SystemState.NORMAL), True, candidates)


class TestIT0073FaultGateBlocksAllPhase2Candidates(unittest.TestCase):
    """IT-0073 — Trace: IF-0008 / 8장 Phase2 확인 필요 항목(3) 확정 재확인, 회귀(1~4단계)"""

    def testFaultStateBlocksEvenWithNonEmptyPhase2Candidates(self):
        """!
        @brief state==FAULT이면 충돌/접근위험/화재 후보가 모두 존재해도 blocked=True/
               STATE_FAULT로 전부 차단되어야 한다(8장 Phase2 확정 — FAULT가 Phase2 후보보다
               항상 우선). Phase1 게이트 로직 회귀 확인을 겸한다(11장 12단계 회귀 범위).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 D 유지 + 결정표 I 무관 확인
        @case Negative
        @breaks 신규 우선순위 규칙 추가가 FAULT 게이트를 깨서 후보가 통과되는 회귀
        """
        arbiter = CommandArbiter()
        candidates = [
            buildCandidateCommand(Door.BOTH, ArbitrationCommand.RELEASE, 1, "CRASH_CONFIRMED"),
            buildCandidateCommand(Door.LEFT, ArbitrationCommand.LOCK, 2, "APPROACH_RISK_LEFT"),
            buildCandidateCommand(Door.BOTH, ArbitrationCommand.RELEASE, 3, "FORCED_RELEASE"),
        ]

        result = arbiter.arbitrate(buildStateResult(SystemState.FAULT), True, candidates)

        self.assertTrue(result.blocked)
        self.assertEqual(result.blockReason, "STATE_FAULT")
        self.assertEqual(result.leftCommand, ArbitrationCommand.NO_CHANGE)
        self.assertEqual(result.rightCommand, ArbitrationCommand.NO_CHANGE)
        self.assertIsNone(result.leftReasonCode)
        self.assertIsNone(result.rightReasonCode)


class TestIT0074InputInvalidGateBlocksAllPhase2Candidates(unittest.TestCase):
    """IT-0074 — Trace: IF-0008 / 결정표 D 유지, 회귀(1~4단계)"""

    def testInputInvalidBlocksEvenWithNonEmptyPhase2Candidates(self):
        """!
        @brief state!=FAULT이지만 inputValid==False이면 Phase2 후보가 존재해도 blocked=True/
               INPUT_INVALID로 차단되어야 한다(결정표 D 유지, Phase1 게이트 로직 회귀 확인).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 D 행 2, 결정표 I 무관 확인
        @case Negative
        @breaks 입력 무효 상태에서도 Phase2 후보가 통과되는 회귀
        """
        arbiter = CommandArbiter()
        candidates = [buildCandidateCommand(Door.BOTH, ArbitrationCommand.RELEASE, 3, "FORCED_RELEASE")]

        result = arbiter.arbitrate(buildStateResult(SystemState.NORMAL), False, candidates)

        self.assertTrue(result.blocked)
        self.assertEqual(result.blockReason, "INPUT_INVALID")


if __name__ == "__main__":
    unittest.main()
