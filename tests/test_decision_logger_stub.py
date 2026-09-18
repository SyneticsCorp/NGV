"""!
@file test_decision_logger_stub.py
@brief IU-0008(ARC-0008 결정 로거 스텁) Phase1 최소 계약(no-op) 검증(ENG-SWE3-001 5장).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.domain.types import ConfirmedOutput, DecisionLogEntry, LockCommand, SystemState
from ngv.adapters.decision_logger_stub import DecisionLoggerStub


class TestDecisionLoggerStubLog(unittest.TestCase):
    """IU-0008.log() 계약 검증(Phase1 no-op)."""

    def testLogReturnsNoneAndDoesNotRaise(self):
        """!
        @brief log()는 어떤 입력에도 예외 없이 None을 반환한다(Phase1 no-op).
        @technique 동등분할(Equivalence Partitioning) — 유효한 DecisionLogEntry 대표값
        @case Positive — Phase1 계약(사후조건 없음, no-op)을 검증
        @breaks log()가 예외를 던지거나 None이 아닌 값을 반환하는 회귀
        """
        logger = DecisionLoggerStub()
        entry = DecisionLogEntry(
            cycleId=1,
            nowS=0.05,
            state=SystemState.NORMAL,
            confirmedOutput=ConfirmedOutput(left=LockCommand.LOCK, right=LockCommand.LOCK),
            blocked=False,
            blockReason=None,
        )

        result = logger.log(entry)

        self.assertIsNone(result)

    def testLogAcceptsEntryWithBlockReasonWithoutSideEffect(self):
        """!
        @brief blockReason이 채워진 항목에도 부작용 없이 동작한다(Phase1 저장/검증 없음).
        @technique 오류추측(Error Guessing) — 차단(blocked=True) 항목이라는 비정상성 높은 입력
        @case Negative — 입력을 검증·저장하지 않는다는 명시적 계약(부작용 없음)을 검증
        @breaks Phase1임에도 내부에 값을 저장하거나 검증 예외를 던지는 회귀(Phase 경계 위반)
        """
        logger = DecisionLoggerStub()
        entry = DecisionLogEntry(
            cycleId=2,
            nowS=0.10,
            state=SystemState.FAULT,
            confirmedOutput=ConfirmedOutput(left=LockCommand.LOCK, right=LockCommand.LOCK),
            blocked=True,
            blockReason="STATE_FAULT",
        )

        result = logger.log(entry)

        self.assertIsNone(result)
        self.assertEqual(vars(logger), {})


if __name__ == "__main__":
    unittest.main()
