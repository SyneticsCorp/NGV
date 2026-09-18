"""!
@file test_it_step4_command_arbiter.py
@brief 통합 4단계 — ARC-0005(Command Arbiter, 게이트 골격), IF-0008 인터페이스 계약 검증.

테스트 베이시스: ENG-SWE2-001 6.1절(IF-0008), 11장 순서표 4행("단위시험 하네스").
Phase 1은 상태/입력유효성 게이트만 구현하며 candidateCommands는 항상 빈 리스트로 호출된다
(1.3절 적용경계). 이 경계를 벗어난 호출(candidateCommands 비어있지 않음)에 대한 방어 동작도
ASIL B 관련 게이트 경로이므로 오류 주입으로 검증한다.
"""

import unittest

from tests_integration.it_helpers import ArbitrationCommand, SystemState, buildStateResult
from ngv.core.command_arbiter import CommandArbiter


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


class TestIT0020CandidateCommandsOutOfPhase1ScopeRaises(unittest.TestCase):
    """IT-0020 — Trace: IF-0008, Phase1 적용경계(1.3절) 오류 주입"""

    def testNonEmptyCandidateCommandsRaisesNotImplementedError(self):
        """!
        @brief Phase1 적용경계를 벗어난 호출(candidateCommands 비어있지 않음)은
               NotImplementedError로 명시적으로 거부되어야 한다(우선순위 규칙 체인은 Phase2+).
        @technique 오류주입(Fault Injection Test) — 계약 경계 위반 호출
        @case Negative — 조용히 무시되지 않고 명시적으로 실패하는지 검증(silent failure 방지)
        @breaks 비어있지 않은 candidateCommands가 조용히 무시되어 Phase1 범위를 벗어난 값이
                반환되는 회귀
        """
        arbiter = CommandArbiter()

        with self.assertRaises(NotImplementedError):
            arbiter.arbitrate(buildStateResult(SystemState.NORMAL), True, ["some-command"])


if __name__ == "__main__":
    unittest.main()
