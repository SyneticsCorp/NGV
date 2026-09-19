"""!
@file test_command_arbiter.py
@brief IU-0005(ARC-0005 Command Arbiter) 함수 계약 검증(ENG-SWE3-001 5.2절/6.8절/7장 결정표 I).

Phase2 갱신: Phase1의 "candidateCommands가 있으면 NotImplementedError" 계약은 완전히 폐기되고
문(door)별 우선순위 후보 선택 알고리즘으로 대체되었다(5.2절 "경고(호환성)"). 이 파일은 더 이상
그 폐기된 계약을 검증하지 않는다 — 아래는 전부 Phase2 신규 계약에 대한 테스트다.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.domain.constants import BLOCK_REASON_INPUT_INVALID, BLOCK_REASON_STATE_FAULT
from ngv.domain.types import ArbitrationCommand, CandidateCommand, Door, StateResult, SystemState
from ngv.core.command_arbiter import CommandArbiter


def state(systemState):
    """테스트 헬퍼 — StateResult를 만든다."""
    warningCode = "FAULT" if systemState == SystemState.FAULT else None
    return StateResult(state=systemState, changedToFault=False, warningReasonCode=warningCode)


def candidate(door, command, priority, reasonCode="REASON"):
    """테스트 헬퍼 — CandidateCommand를 만든다."""
    return CandidateCommand(door=door, command=command, priority=priority, reasonCode=reasonCode)


class TestCommandArbiterArbitrateGates(unittest.TestCase):
    """IU-0005.arbitrate() FAULT/inputValid 게이트 계약 검증(Phase1 원칙 유지)."""

    def testBlocksWhenStateIsFaultEvenWithCandidates(self):
        """!
        @brief state==FAULT이면 candidateCommands가 있어도 전부 차단된다(FAULT 최우선, 8.5절).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 I, FAULT 행
        @case Negative — FAULT가 Phase2 후보보다 항상 우선한다는 8.5절 확정 사항을 검증
        @breaks FAULT임에도 강한 신호(CONFIRMED 등) 후보가 그대로 통과되는 회귀
        """
        candidates = [candidate(Door.BOTH, ArbitrationCommand.RELEASE, 1)]
        result = CommandArbiter().arbitrate(state(SystemState.FAULT), True, candidates)

        self.assertTrue(result.blocked)
        self.assertEqual(result.blockReason, BLOCK_REASON_STATE_FAULT)
        self.assertEqual(result.leftCommand, ArbitrationCommand.NO_CHANGE)
        self.assertEqual(result.rightCommand, ArbitrationCommand.NO_CHANGE)
        self.assertIsNone(result.leftReasonCode)
        self.assertIsNone(result.rightReasonCode)

    def testBlocksWhenInputInvalid(self):
        """!
        @brief inputValid==False이면 blocked=True, blockReason=INPUT_INVALID를 반환한다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 I, inputInvalid 행
        @case Negative — 입력 무효 상태에서 출력 후보를 차단하는 게이트 동작을 검증
        @breaks inputValid=False인데도 blocked=False를 반환하는 회귀
        """
        result = CommandArbiter().arbitrate(state(SystemState.NORMAL), False, [])

        self.assertTrue(result.blocked)
        self.assertEqual(result.blockReason, BLOCK_REASON_INPUT_INVALID)

    def testNotBlockedWithEmptyCandidatesReturnsNoChange(self):
        """!
        @brief 게이트를 통과하고 candidateCommands가 비어있으면 NO_CHANGE/None을 반환한다.
        @technique 동등분할(Equivalence Partitioning) — 후보 없음 클래스의 대표값
        @case Positive — Phase1 "빈 리스트" 동작과 동일한 결과(하위 호환)를 검증
        @breaks 후보가 없는데도 임의로 LOCK/RELEASE를 반환하는 회귀
        """
        result = CommandArbiter().arbitrate(state(SystemState.NORMAL), True, [])

        self.assertFalse(result.blocked)
        self.assertIsNone(result.blockReason)
        self.assertEqual(result.leftCommand, ArbitrationCommand.NO_CHANGE)
        self.assertEqual(result.rightCommand, ArbitrationCommand.NO_CHANGE)
        self.assertIsNone(result.leftReasonCode)
        self.assertIsNone(result.rightReasonCode)

    def testDefaultsToEmptyCandidatesWhenArgumentOmitted(self):
        """!
        @brief candidateCommands를 생략(None)하면 빈 리스트로 취급된다(5.2절 계약).
        @technique 동등분할(Equivalence Partitioning) — 인자 생략(None) 클래스
        @case Positive — candidateCommands=None 기본값 처리 경로를 검증
        @breaks None을 순회하려다 TypeError가 발생하는 회귀
        """
        result = CommandArbiter().arbitrate(state(SystemState.NORMAL), True)

        self.assertFalse(result.blocked)
        self.assertEqual(result.leftCommand, ArbitrationCommand.NO_CHANGE)


class TestCommandArbiterArbitratePrioritySelection(unittest.TestCase):
    """IU-0005.arbitrate() 문별 우선순위 후보 선택 계약 검증(Phase2 신규, 6.8절)."""

    def testSelectsHighestPriorityCandidateForBothDoorsScope(self):
        """!
        @brief door=BOTH 후보는 좌/우 양쪽 모두에 적용된다(단일 최소 priority 후보).
        @technique 동등분할(Equivalence Partitioning) — BOTH 범위 후보 1개만 있는 대표값
        @case Positive — CandidateCommand.door==BOTH가 두 문 모두를 포함하는지 검증
        @breaks BOTH 후보가 한쪽 문에만 적용되는 회귀
        """
        candidates = [candidate(Door.BOTH, ArbitrationCommand.RELEASE, 1, "CRASH_CONFIRMED")]
        result = CommandArbiter().arbitrate(state(SystemState.NORMAL), True, candidates)

        self.assertEqual(result.leftCommand, ArbitrationCommand.RELEASE)
        self.assertEqual(result.rightCommand, ArbitrationCommand.RELEASE)
        self.assertEqual(result.leftReasonCode, "CRASH_CONFIRMED")
        self.assertEqual(result.rightReasonCode, "CRASH_CONFIRMED")

    def testLowerPriorityNumberWinsOverHigherPriorityNumber(self):
        """!
        @brief 같은 문에 priority가 다른 후보 2개가 있으면 값이 더 작은(=우선순위가 높은) 쪽이 이긴다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 I, 다중 후보 최소-priority 선택
        @case Positive — 충돌(1) > 접근위험(2) 우선순위 정량 구현을 검증
        @breaks priority가 낮은(우선순위 높은) 후보 대신 높은 번호가 선택되는 회귀
        """
        candidates = [
            candidate(Door.LEFT, ArbitrationCommand.LOCK, 2, "APPROACH_RISK_LEFT"),
            candidate(Door.LEFT, ArbitrationCommand.RELEASE, 1, "CRASH_CONFIRMED"),
        ]
        result = CommandArbiter().arbitrate(state(SystemState.NORMAL), True, candidates)

        self.assertEqual(result.leftCommand, ArbitrationCommand.RELEASE)
        self.assertEqual(result.leftReasonCode, "CRASH_CONFIRMED")

    def testDoorsAreSelectedIndependently(self):
        """!
        @brief LEFT 전용 후보는 RIGHT 결과에 영향을 주지 않는다(문별 독립 선택).
        @technique 동등분할(Equivalence Partitioning) — 문별로 다른 후보 집합의 대표값
        @case Positive — selectForDoor()가 문별로 독립 적용되는지 검증
        @breaks 한쪽 문의 후보가 반대쪽 문 결과를 오염시키는 회귀
        """
        candidates = [candidate(Door.LEFT, ArbitrationCommand.LOCK, 2, "APPROACH_RISK_LEFT")]
        result = CommandArbiter().arbitrate(state(SystemState.NORMAL), True, candidates)

        self.assertEqual(result.leftCommand, ArbitrationCommand.LOCK)
        self.assertEqual(result.rightCommand, ArbitrationCommand.NO_CHANGE)
        self.assertIsNone(result.rightReasonCode)

    def testRaisesValueErrorOnTiedMinimumPriorityForSameDoor(self):
        """!
        @brief 동일 문에 동일 최소 priority 후보가 2개 이상이면 ValueError를 던진다(설계상 불변조건).
        @technique 오류추측(Error Guessing) — 정상 경로에서 발생 불가한 내부 불변조건 위반 주입
        @case Negative — 결정표 I "동일 priority 충돌" 방어적 예외를 검증
        @breaks 충돌 시 임의로 하나를 선택해버려 불변조건 위반을 감추는 회귀
        """
        candidates = [
            candidate(Door.LEFT, ArbitrationCommand.LOCK, 2, "A"),
            candidate(Door.LEFT, ArbitrationCommand.RELEASE, 2, "B"),
        ]
        with self.assertRaises(ValueError):
            CommandArbiter().arbitrate(state(SystemState.NORMAL), True, candidates)


class TestCommandArbiterSelectForDoor(unittest.TestCase):
    """IU-0005.selectForDoor() 내부 헬퍼 독립 계약 검증(6.8절, 정적 메서드로 단위시험 가능)."""

    def testReturnsNoChangeWhenNoApplicableCandidate(self):
        """!
        @brief 해당 문에 적용 가능한 후보가 없으면 (NO_CHANGE, None)을 반환한다.
        @technique 동등분할(Equivalence Partitioning) — 적용 불가 후보만 있는 대표값(다른 문 전용)
        @case Positive — 후보 없음 기본 반환값을 검증
        @breaks 적용 불가 후보를 잘못 적용해버리는 회귀
        """
        candidates = [candidate(Door.RIGHT, ArbitrationCommand.LOCK, 2)]

        command, reasonCode = CommandArbiter.selectForDoor(candidates, Door.LEFT)

        self.assertEqual(command, ArbitrationCommand.NO_CHANGE)
        self.assertIsNone(reasonCode)

    def testTreatsBothDoorCandidateAsApplicableToEitherDoor(self):
        """!
        @brief door=BOTH인 후보는 LEFT 조회에도, RIGHT 조회에도 적용 가능하다.
        @technique 동등분할(Equivalence Partitioning) — BOTH 범위 판정 대표값
        @case Positive — "door==해당 문 또는 BOTH" 적용 가능 조건을 검증
        @breaks BOTH 후보가 특정 문 조회에서 누락되는 회귀
        """
        candidates = [candidate(Door.BOTH, ArbitrationCommand.RELEASE, 1, "FORCED_RELEASE")]

        leftResult = CommandArbiter.selectForDoor(candidates, Door.LEFT)
        rightResult = CommandArbiter.selectForDoor(candidates, Door.RIGHT)

        self.assertEqual(leftResult, (ArbitrationCommand.RELEASE, "FORCED_RELEASE"))
        self.assertEqual(rightResult, (ArbitrationCommand.RELEASE, "FORCED_RELEASE"))


if __name__ == "__main__":
    unittest.main()
