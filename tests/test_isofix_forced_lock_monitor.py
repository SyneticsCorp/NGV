"""!
@file test_isofix_forced_lock_monitor.py
@brief IU-0015(ARC-0015 ISOFIX 강제잠금 감시) 함수 계약 검증(ENG-SWE3-001 5.13절/6.15절/
       7장 결정표 M, SWR-018).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.domain.constants import (
    PRIORITY_ISOFIX_FORCED_LOCK,
    REASON_CODE_ISOFIX_LEFT,
    REASON_CODE_ISOFIX_RIGHT,
)
from ngv.domain.types import ArbitrationCommand, Door, FieldValidationResult
from ngv.core.isofix_forced_lock_monitor import IsofixForcedLockMonitor


def validField(value):
    """테스트 헬퍼 — 유효한 FieldValidationResult[bool]를 만든다."""
    return FieldValidationResult(value=value, valid=True, rawValue=value)


def invalidField(rawValue, errorReason="TYPE_ERROR"):
    """테스트 헬퍼 — 무효한 FieldValidationResult를 만든다."""
    return FieldValidationResult(value=None, valid=False, rawValue=rawValue, errorReason=errorReason)


class TestIsofixForcedLockMonitorEvaluate(unittest.TestCase):
    """IU-0015.evaluate() 결정표 M 계약 검증(좌우 4조합 FF/FT/TF/TT 전수)."""

    def testBothFalseProducesNoLockOnEitherDoor(self):
        """!
        @brief 좌우 모두 False(FF)이면 양쪽 모두 lockActive=False, lockCandidate=None이다.
        @technique 결정테이블 테스트(Decision Table Testing) — 좌우 4조합 중 FF
        @case Positive — 탑승 없음 기본 상태를 검증
        @breaks FF 조합에서도 어느 한쪽이 lockActive=True로 오판정되는 회귀
        """
        result = IsofixForcedLockMonitor().evaluate(validField(False), validField(False))

        self.assertFalse(result.leftLockActive)
        self.assertFalse(result.rightLockActive)
        self.assertIsNone(result.leftLockCandidate)
        self.assertIsNone(result.rightLockCandidate)

    def testLeftTrueRightFalseLocksOnlyLeftDoor(self):
        """!
        @brief 좌측만 True(TF)이면 좌측만 LOCK 후보가 생성되고 우측은 영향받지 않는다.
        @technique 결정테이블 테스트(Decision Table Testing) — 좌우 4조합 중 TF, 독립성 검증
        @case Positive — SWR-018(b) 좌우 독립 요구사항을 검증
        @breaks 좌측 판정이 우측 결과에 영향을 주는 회귀(독립성 붕괴)
        """
        result = IsofixForcedLockMonitor().evaluate(validField(True), validField(False))

        self.assertTrue(result.leftLockActive)
        self.assertIsNotNone(result.leftLockCandidate)
        self.assertEqual(result.leftLockCandidate.door, Door.LEFT)
        self.assertEqual(result.leftLockCandidate.command, ArbitrationCommand.LOCK)
        self.assertEqual(result.leftLockCandidate.priority, PRIORITY_ISOFIX_FORCED_LOCK)
        self.assertEqual(result.leftReasonCode, REASON_CODE_ISOFIX_LEFT)
        self.assertFalse(result.rightLockActive)
        self.assertIsNone(result.rightLockCandidate)

    def testLeftFalseRightTrueLocksOnlyRightDoor(self):
        """!
        @brief 우측만 True(FT)이면 우측만 LOCK 후보가 생성되고 좌측은 영향받지 않는다.
        @technique 결정테이블 테스트(Decision Table Testing) — 좌우 4조합 중 FT, 독립성 검증
        @case Positive — SWR-018(b) 좌우 독립 요구사항을 검증(우측 대칭)
        @breaks 우측 판정이 좌측 결과에 영향을 주는 회귀(독립성 붕괴)
        """
        result = IsofixForcedLockMonitor().evaluate(validField(False), validField(True))

        self.assertFalse(result.leftLockActive)
        self.assertIsNone(result.leftLockCandidate)
        self.assertTrue(result.rightLockActive)
        self.assertIsNotNone(result.rightLockCandidate)
        self.assertEqual(result.rightLockCandidate.door, Door.RIGHT)
        self.assertEqual(result.rightReasonCode, REASON_CODE_ISOFIX_RIGHT)

    def testBothTrueLocksBothDoorsIndependently(self):
        """!
        @brief 좌우 모두 True(TT)이면 양쪽 모두 각자 독립적으로 LOCK 후보가 생성된다.
        @technique 결정테이블 테스트(Decision Table Testing) — 좌우 4조합 중 TT
        @case Positive — 두 카시트가 동시에 탑승한 경우 양쪽 모두 잠기는지 검증
        @breaks TT 조합에서 한쪽만 잠기거나 둘 다 잠기지 않는 회귀
        """
        result = IsofixForcedLockMonitor().evaluate(validField(True), validField(True))

        self.assertTrue(result.leftLockActive)
        self.assertTrue(result.rightLockActive)
        self.assertIsNotNone(result.leftLockCandidate)
        self.assertIsNotNone(result.rightLockCandidate)

    def testInvalidLeftFieldRejectsWithoutAffectingRightDoor(self):
        """!
        @brief 좌측 필드가 valid=False이면 좌측만 미판정 처리되고 우측은 영향받지 않는다(10.4절/10.7절).
        @technique 오류주입(Fault Injection Test) — 좌측 필드만 무효화한 독립성 검증
        @case Negative — 신뢰할 수 없는 좌측 데이터가 우측 판정을 오염시키지 않는지 검증
        @breaks 좌측 무효 입력이 우측 lockActive까지 함께 무효화하는 회귀
        """
        result = IsofixForcedLockMonitor().evaluate(invalidField("bad"), validField(True))

        self.assertFalse(result.leftLockActive)
        self.assertIsNone(result.leftLockCandidate)
        self.assertTrue(result.rightLockActive)
        self.assertIsNotNone(result.rightLockCandidate)

    def testRaisesValueErrorWhenLeftFieldIsNone(self):
        """!
        @brief isofixLeftField가 None이면 ValueError를 던진다(상위 계약 위반 방어).
        @technique 오류추측(Error Guessing) — IU-0011 선례와 동일한 방어적 예외 패턴
        @case Negative — 사전조건(not None) 위반 시 방어적 예외를 검증
        @breaks None 입력이 예외 없이 통과되어 하류에서 AttributeError로 이어지는 회귀
        """
        with self.assertRaises(ValueError):
            IsofixForcedLockMonitor().evaluate(None, validField(False))

    def testRaisesValueErrorWhenRightFieldIsNone(self):
        """!
        @brief isofixRightField가 None이면 ValueError를 던진다(상위 계약 위반 방어).
        @technique 오류추측(Error Guessing) — 좌측과 대칭인 방어적 예외 경로
        @case Negative — 우측 인자에 대해서도 동일한 사전조건 위반 방어를 검증
        @breaks 우측 None 입력만 예외 없이 통과되는 회귀(좌우 비대칭 방어 결함)
        """
        with self.assertRaises(ValueError):
            IsofixForcedLockMonitor().evaluate(validField(False), None)


if __name__ == "__main__":
    unittest.main()
