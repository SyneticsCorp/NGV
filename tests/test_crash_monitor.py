"""!
@file test_crash_monitor.py
@brief IU-0010(ARC-0010 충돌 감시) 함수 계약 검증(ENG-SWE3-001 5.4절/6.9절/7장 결정표 E,
       SWR-007/SWR-008).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.domain.constants import PRIORITY_CRASH, REASON_CODE_CRASH_CONFIRMED
from ngv.domain.types import ArbitrationCommand, CrashStatus, Door, FieldValidationResult
from ngv.core.crash_monitor import CrashMonitor


def validField(value):
    """테스트 헬퍼 — 유효한 FieldValidationResult[CrashStatus]를 만든다."""
    return FieldValidationResult(value=value, valid=True, rawValue=value)


def invalidField(rawValue, errorReason="TYPE_ERROR"):
    """테스트 헬퍼 — 무효한 FieldValidationResult를 만든다."""
    return FieldValidationResult(value=None, valid=False, rawValue=rawValue, errorReason=errorReason)


class TestCrashMonitorEvaluate(unittest.TestCase):
    """IU-0010.evaluate() 결정표 E 계약 검증."""

    def testConfirmedStatusProducesBothDoorsReleaseCandidateAtPriorityOne(self):
        """!
        @brief value==CONFIRMED이면 door=BOTH, command=RELEASE, priority=1인 긴급해제 후보를 만든다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 E, valid=True/CONFIRMED 행
        @case Positive — SWR-007(a) 긴급해제 후보 생성 경로를 검증
        @breaks CONFIRMED임에도 releaseCandidate가 None으로 남는 회귀
        """
        result = CrashMonitor().evaluate(validField(CrashStatus.CONFIRMED), 1.0)

        self.assertEqual(result.status, CrashStatus.CONFIRMED)
        self.assertFalse(result.pendingHoldApplied)
        self.assertIsNotNone(result.releaseCandidate)
        self.assertEqual(result.releaseCandidate.door, Door.BOTH)
        self.assertEqual(result.releaseCandidate.command, ArbitrationCommand.RELEASE)
        self.assertEqual(result.releaseCandidate.priority, PRIORITY_CRASH)
        self.assertEqual(result.releaseCandidate.reasonCode, REASON_CODE_CRASH_CONFIRMED)

    def testPendingStatusAppliesHoldWithoutReleaseCandidate(self):
        """!
        @brief value==PENDING이면 releaseCandidate는 None이고 pendingHoldApplied=True다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 E, valid=True/PENDING 행
        @case Positive — SWR-008(추론 요구사항, ledger 갭 4) PENDING 미개시 경로를 검증
        @breaks PENDING에서도 releaseCandidate가 생성되는 회귀(조기 해제)
        """
        result = CrashMonitor().evaluate(validField(CrashStatus.PENDING), 1.0)

        self.assertEqual(result.status, CrashStatus.PENDING)
        self.assertIsNone(result.releaseCandidate)
        self.assertTrue(result.pendingHoldApplied)

    def testNoneStatusProducesNoCandidateAndNoHold(self):
        """!
        @brief value==NONE이면 releaseCandidate=None, pendingHoldApplied=False다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 E, valid=True/NONE 행
        @case Positive — 충돌 없음 기본 상태를 검증
        @breaks NONE에서도 후보나 hold가 생성되는 회귀
        """
        result = CrashMonitor().evaluate(validField(CrashStatus.NONE), 1.0)

        self.assertEqual(result.status, CrashStatus.NONE)
        self.assertIsNone(result.releaseCandidate)
        self.assertFalse(result.pendingHoldApplied)

    def testInvalidFieldRejectsWithoutGeneratingNewCandidate(self):
        """!
        @brief valid=False이면 status=NONE, releaseCandidate=None, pendingHoldApplied=False다(10.4절).
        @technique 동등분할(Equivalence Partitioning) — 무효 입력 클래스의 대표값
        @case Negative — 신뢰할 수 없는 데이터로 새 RELEASE 후보를 생성하지 않는 방어 원칙을 검증
        @breaks 손상된 입력에서도 RELEASE 후보를 생성해 불필요한 해제를 유발하는 회귀
        """
        result = CrashMonitor().evaluate(invalidField("bogus"), 1.0)

        self.assertEqual(result.status, CrashStatus.NONE)
        self.assertIsNone(result.releaseCandidate)
        self.assertFalse(result.pendingHoldApplied)

    def testRaisesValueErrorWhenFieldIsNone(self):
        """!
        @brief crashStatusField가 None이면 ValueError를 던진다(상위 계약 위반 방어).
        @technique 오류추측(Error Guessing) — IU-0003 선례와 동일한 방어적 예외 패턴
        @case Negative — 사전조건(not None) 위반 시 방어적 예외를 검증
        @breaks None 입력이 예외 없이 통과되어 하류에서 AttributeError로 이어지는 회귀
        """
        with self.assertRaises(ValueError):
            CrashMonitor().evaluate(None, 1.0)


if __name__ == "__main__":
    unittest.main()
