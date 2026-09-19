"""!
@file test_it_step4_command_arbiter.py
@brief 통합 4단계 — ARC-0005(Command Arbiter, 게이트 골격), IF-0008 인터페이스 계약 검증.

테스트 베이시스: ENG-SWE2-001 6.1절(IF-0008), 11장 순서표 4행("단위시험 하네스").
Phase 2(ENG-SWE3-001 v0.2 5.2절)부터 candidateCommands는 문(door)별 우선순위 후보 선택
알고리즘으로 처리된다 — Phase1의 "candidateCommands가 비어있지 않으면 NotImplementedError"
계약은 완전히 대체되었다(하위호환 아님). IT-0020은 이 신규 계약(정상 처리)을 검증하도록 갱신됨.
"""

import unittest

from tests_integration.it_helpers import ArbitrationCommand, SystemState, buildStateResult
from ngv.core.command_arbiter import CommandArbiter
from ngv.domain.types import CandidateCommand, Door


class TestIT0017StateFaultBlocksRegardlessOfInputValid(unittest.TestCase):
    """IT-0017 — Trace: IF-0008 / SWR-021(a), 결정표 D"""

    def testFaultStateBlocksEvenWhenInputValid(self):
        """!
        @brief state==FAULT면 inputValid==True여도 blocked=True/STATE_FAULT여야 한다
               (상태 우선순위가 입력유효성보다 앞선다, 결정표 D).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 D 행 1(FAULT 우선)
        @case Positive
        @breaks FAULT 상태인데도 입력이 유효하면 차단이 풀리는 회귀
        """
        arbiter = CommandArbiter()

        result = arbiter.arbitrate(buildStateResult(SystemState.FAULT), True, [])

        self.assertTrue(result.blocked)
        self.assertEqual(result.blockReason, "STATE_FAULT")
        self.assertEqual(result.leftCommand, ArbitrationCommand.NO_CHANGE)
        self.assertEqual(result.rightCommand, ArbitrationCommand.NO_CHANGE)


class TestIT0018InputInvalidBlocksWhenStateNotFault(unittest.TestCase):
    """IT-0018 — Trace: IF-0008 / SWR-013(b), 결정표 D"""

    def testInputInvalidBlocksWithNormalState(self):
        """!
        @brief state!=FAULT이지만 inputValid==False면 blocked=True/INPUT_INVALID여야 한다
               (결정표 D 행 2).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 D 행 2
        @case Negative
        @breaks 입력 무효 상태에서도 신규 명령이 통과(blocked=False)되는 회귀
        """
        arbiter = CommandArbiter()

        result = arbiter.arbitrate(buildStateResult(SystemState.NORMAL), False, [])

        self.assertTrue(result.blocked)
        self.assertEqual(result.blockReason, "INPUT_INVALID")


class TestIT0019NormalAndValidPassesGate(unittest.TestCase):
    """IT-0019 — Trace: IF-0008, 결정표 D"""

    def testNormalStateAndValidInputIsNotBlocked(self):
        """!
        @brief state!=FAULT이고 inputValid==True이면 blocked=False, 두 축 모두 NO_CHANGE여야
               한다(Phase1 최소 계약 — 우선순위 규칙 체인 미구현).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 D 행 3(정상 통과)
        @case Positive
        @breaks 정상 조건에서도 blocked=True가 반환되는 회귀(게이트 과잉 차단)
        """
        arbiter = CommandArbiter()

        result = arbiter.arbitrate(buildStateResult(SystemState.NORMAL), True, [])

        self.assertFalse(result.blocked)
        self.assertIsNone(result.blockReason)
        self.assertEqual(result.leftCommand, ArbitrationCommand.NO_CHANGE)
        self.assertEqual(result.rightCommand, ArbitrationCommand.NO_CHANGE)


class TestIT0020CandidateCommandsAreArbitratedByPriority(unittest.TestCase):
    """IT-0020 — Trace: IF-0008/IF-0016~0019, ENG-SWE3-001 v0.2 5.2절/6.8절(Phase2 갱신)"""

    def testNonEmptyCandidateCommandsAreResolvedByMinimumPriority(self):
        """!
        @brief 비어있지 않은 candidateCommands는 더 이상 거부되지 않고 문별 최소-priority
               후보 선택으로 정상 처리된다(Phase1 NotImplementedError 계약의 완전한 대체).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 I, 단일 BOTH 후보 정상 처리
        @case Positive — Phase2 신규 계약(우선순위 중재)이 통합 경계에서도 성립하는지 검증
        @breaks 비어있지 않은 candidateCommands에서 여전히 NotImplementedError가 발생하거나
                후보가 무시되는 회귀(Phase1 계약으로의 역행)
        """
        arbiter = CommandArbiter()
        candidates = [
            CandidateCommand(door=Door.BOTH, command=ArbitrationCommand.RELEASE, priority=1, reasonCode="R")
        ]

        result = arbiter.arbitrate(buildStateResult(SystemState.NORMAL), True, candidates)

        self.assertFalse(result.blocked)
        self.assertEqual(result.leftCommand, ArbitrationCommand.RELEASE)
        self.assertEqual(result.rightCommand, ArbitrationCommand.RELEASE)


if __name__ == "__main__":
    unittest.main()
