"""!
@file test_command_arbiter.py
@brief IU-0005(ARC-0005 Command Arbiter) Phase1 최소 계약 검증(ENG-SWE3-001 5장, 게이트만).

Phase1 범위: state==FAULT 또는 inputValid==False일 때만 게이트. candidateCommands가 있으면
NotImplementedError(우선순위 규칙 체인은 Phase2 이후). 그 외 로직은 만들지 않는다(YAGNI).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.domain.constants import BLOCK_REASON_INPUT_INVALID, BLOCK_REASON_STATE_FAULT
from ngv.domain.types import ArbitrationCommand, StateResult, SystemState
from ngv.core.command_arbiter import CommandArbiter


def state(systemState):
    """테스트 헬퍼 — StateResult를 만든다."""
    warningCode = "FAULT" if systemState == SystemState.FAULT else None
    return StateResult(state=systemState, changedToFault=False, warningReasonCode=warningCode)


class TestCommandArbiterArbitrate(unittest.TestCase):
    """IU-0005.arbitrate() Phase1 게이트 계약 검증."""

    def testBlocksWhenStateIsFault(self):
        """!
        @brief state==FAULT이면 blocked=True, 두 축 모두 NO_CHANGE, blockReason=STATE_FAULT를 반환한다.
        @technique 결정테이블 테스트(Decision Table Testing) — Phase1 게이트 조건(state==FAULT)
        @case Negative — FAULT 상태에서 출력 후보를 차단하는 게이트 동작을 검증
        @breaks FAULT임에도 blocked=False를 반환하는 회귀
        """
        arbiter = CommandArbiter()
        result = arbiter.arbitrate(state(SystemState.FAULT), True, [])

        self.assertTrue(result.blocked)
        self.assertEqual(result.leftCommand, ArbitrationCommand.NO_CHANGE)
        self.assertEqual(result.rightCommand, ArbitrationCommand.NO_CHANGE)
        self.assertEqual(result.blockReason, BLOCK_REASON_STATE_FAULT)

    def testBlocksWhenInputInvalid(self):
        """!
        @brief inputValid==False이면 blocked=True, blockReason=INPUT_INVALID를 반환한다.
        @technique 결정테이블 테스트(Decision Table Testing) — Phase1 게이트 조건(inputValid==False)
        @case Negative — 입력 무효 상태에서 출력 후보를 차단하는 게이트 동작을 검증
        @breaks inputValid=False인데도 blocked=False를 반환하는 회귀
        """
        arbiter = CommandArbiter()
        result = arbiter.arbitrate(state(SystemState.NORMAL), False, [])

        self.assertTrue(result.blocked)
        self.assertEqual(result.blockReason, BLOCK_REASON_INPUT_INVALID)

    def testNotBlockedWhenNormalAndInputValid(self):
        """!
        @brief state!=FAULT이고 inputValid==True이면 blocked=False, NO_CHANGE를 반환한다(규칙 체인 없음).
        @technique 동등분할(Equivalence Partitioning) — 게이트 조건 모두 미성립인 대표값
        @case Positive — Phase1 최소 동작(규칙 체인 없이 항상 NO_CHANGE)을 검증
        @breaks 규칙 체인이 없음에도 임의로 LOCK/RELEASE를 반환하는 회귀(Phase1 범위 초과)
        """
        arbiter = CommandArbiter()
        result = arbiter.arbitrate(state(SystemState.NORMAL), True, [])

        self.assertFalse(result.blocked)
        self.assertIsNone(result.blockReason)
        self.assertEqual(result.leftCommand, ArbitrationCommand.NO_CHANGE)
        self.assertEqual(result.rightCommand, ArbitrationCommand.NO_CHANGE)

    def testRaisesNotImplementedErrorWhenCandidateCommandsProvided(self):
        """!
        @brief candidateCommands가 비어있지 않으면 NotImplementedError를 던진다(Phase1 범위 밖).
        @technique 오류추측(Error Guessing) — Phase 경계 위반을 조기 검출하는 방어적 예외
        @case Negative — 아직 구현되지 않은 우선순위 규칙 체인 사용을 명시적으로 거부하는지 검증
        @breaks candidateCommands를 조용히 무시하고 정상 처리해 Phase 경계 위반을 감추는 회귀
        """
        arbiter = CommandArbiter()

        with self.assertRaises(NotImplementedError):
            arbiter.arbitrate(state(SystemState.NORMAL), True, [ArbitrationCommand.LOCK])


if __name__ == "__main__":
    unittest.main()
