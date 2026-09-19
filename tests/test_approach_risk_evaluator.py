"""!
@file test_approach_risk_evaluator.py
@brief IU-0011(ARC-0011 접근위험 평가) 함수 계약 검증(ENG-SWE3-001 5.5절/6.10절/7장 결정표 F,
       SWR-005/SWR-009 좌우 완전 독립).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.domain.constants import (
    PRIORITY_APPROACH_RISK,
    REASON_CODE_APPROACH_RISK_LEFT,
    REASON_CODE_APPROACH_RISK_RIGHT,
)
from ngv.domain.types import ArbitrationCommand, Door, FieldValidationResult
from ngv.core.approach_risk_evaluator import ApproachRiskEvaluator


def validField(value):
    """테스트 헬퍼 — 유효한 FieldValidationResult[bool]을 만든다."""
    return FieldValidationResult(value=value, valid=True, rawValue=value)


def invalidField(rawValue, errorReason="TYPE_ERROR"):
    """테스트 헬퍼 — 무효한 FieldValidationResult를 만든다."""
    return FieldValidationResult(value=None, valid=False, rawValue=rawValue, errorReason=errorReason)


class TestApproachRiskEvaluatorEvaluate(unittest.TestCase):
    """IU-0011.evaluate() 결정표 F/좌우 독립성 계약 검증."""

    def testLeftTrueRightFalseActivatesOnlyLeftSuppressCandidate(self):
        """!
        @brief (True, False) 조합에서는 좌측만 활성화되고 우측은 영향받지 않는다.
        @technique 동등분할(Equivalence Partitioning) — SWR-009 4조합(FF/FT/TF/TT) 중 TF
        @case Positive — 좌측 활성 경로와 우측 무교차를 동시에 검증
        @breaks 좌측 판정이 우측 결과에 영향을 주는 회귀(SWR-009 위반)
        """
        result = ApproachRiskEvaluator().evaluate(validField(True), validField(False))

        self.assertTrue(result.leftRiskActive)
        self.assertIsNotNone(result.leftSuppressCandidate)
        self.assertEqual(result.leftSuppressCandidate.door, Door.LEFT)
        self.assertEqual(result.leftSuppressCandidate.command, ArbitrationCommand.LOCK)
        self.assertEqual(result.leftSuppressCandidate.priority, PRIORITY_APPROACH_RISK)
        self.assertEqual(result.leftReasonCode, REASON_CODE_APPROACH_RISK_LEFT)
        self.assertFalse(result.rightRiskActive)
        self.assertIsNone(result.rightSuppressCandidate)
        self.assertIsNone(result.rightReasonCode)

    def testRightTrueLeftFalseActivatesOnlyRightSuppressCandidate(self):
        """!
        @brief (False, True) 조합에서는 우측만 활성화되고 좌측은 영향받지 않는다.
        @technique 동등분할(Equivalence Partitioning) — SWR-009 4조합 중 FT
        @case Positive — 우측 활성 경로와 좌측 무교차를 동시에 검증
        @breaks 우측 판정이 좌측 결과에 영향을 주는 회귀(SWR-009 위반)
        """
        result = ApproachRiskEvaluator().evaluate(validField(False), validField(True))

        self.assertFalse(result.leftRiskActive)
        self.assertIsNone(result.leftSuppressCandidate)
        self.assertTrue(result.rightRiskActive)
        self.assertIsNotNone(result.rightSuppressCandidate)
        self.assertEqual(result.rightSuppressCandidate.door, Door.RIGHT)
        self.assertEqual(result.rightReasonCode, REASON_CODE_APPROACH_RISK_RIGHT)

    def testBothTrueActivatesBothSidesIndependently(self):
        """!
        @brief (True, True) 조합에서는 좌우 모두 독립적으로 활성화된다.
        @technique 동등분할(Equivalence Partitioning) — SWR-009 4조합 중 TT
        @case Positive — 양측 동시 활성이 서로 간섭 없이 성립하는지 검증
        @breaks 한쪽만 활성화되거나 서로의 reasonCode가 뒤섞이는 회귀
        """
        result = ApproachRiskEvaluator().evaluate(validField(True), validField(True))

        self.assertTrue(result.leftRiskActive)
        self.assertTrue(result.rightRiskActive)
        self.assertEqual(result.leftReasonCode, REASON_CODE_APPROACH_RISK_LEFT)
        self.assertEqual(result.rightReasonCode, REASON_CODE_APPROACH_RISK_RIGHT)

    def testBothFalseActivatesNeitherSide(self):
        """!
        @brief (False, False) 조합에서는 양측 모두 비활성이다.
        @technique 동등분할(Equivalence Partitioning) — SWR-009 4조합 중 FF
        @case Positive — 위험 없음 기본 상태를 검증
        @breaks 위험이 없는데도 후보가 생성되는 회귀
        """
        result = ApproachRiskEvaluator().evaluate(validField(False), validField(False))

        self.assertFalse(result.leftRiskActive)
        self.assertFalse(result.rightRiskActive)
        self.assertIsNone(result.leftSuppressCandidate)
        self.assertIsNone(result.rightSuppressCandidate)

    def testInvalidLeftFieldRejectsWithoutGeneratingCandidate(self):
        """!
        @brief 좌측 필드가 valid=False이면 leftRiskActive=False로 거절된다(10.4절, 우측은 무관).
        @technique 오류추측(Error Guessing) — 손상된 좌측 입력이 우측에 영향을 주지 않는지 확인
        @case Negative — 신뢰할 수 없는 데이터로 새 LOCK 후보를 생성하지 않는 방어 원칙을 검증
        @breaks 손상된 좌측 입력에서도 LOCK 후보가 생성되는 회귀
        """
        result = ApproachRiskEvaluator().evaluate(invalidField("bad"), validField(True))

        self.assertFalse(result.leftRiskActive)
        self.assertIsNone(result.leftSuppressCandidate)
        self.assertTrue(result.rightRiskActive)

    def testRaisesValueErrorWhenEitherFieldIsNone(self):
        """!
        @brief 두 인자 중 하나라도 None이면 ValueError를 던진다(사전조건 위반 방어).
        @technique 오류추측(Error Guessing) — 필수 인자 누락
        @case Negative — 사전조건(두 인자 모두 not None) 위반 시 방어적 예외를 검증
        @breaks None 인자가 예외 없이 통과되어 AttributeError로 이어지는 회귀
        """
        with self.assertRaises(ValueError):
            ApproachRiskEvaluator().evaluate(None, validField(True))
        with self.assertRaises(ValueError):
            ApproachRiskEvaluator().evaluate(validField(True), None)


if __name__ == "__main__":
    unittest.main()
