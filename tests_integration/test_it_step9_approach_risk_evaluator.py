"""!
@file test_it_step9_approach_risk_evaluator.py
@brief 통합 9단계 — ARC-0011(접근위험 평가), IF-0017 인터페이스 계약 검증(신규, Phase2).

테스트 베이시스: ENG-SWE2-001 6.1절(IF-0017), 11장 순서표 9행("단위시험 하네스, 좌우 4조합
FF/FT/TF/TT 시험벡터"). ENG-SWE3-001 7장 결정표 F(좌측 예시, 우측 대칭)를 그대로 사용한다.
"""

import unittest

from tests_integration.it_helpers import invalidField, validField
from ngv.core.approach_risk_evaluator import ApproachRiskEvaluator
from ngv.domain.types import ArbitrationCommand, Door


class TestIT0049BothFalseYieldsNoCandidateOnEitherDoor(unittest.TestCase):
    """IT-0049 — Trace: IF-0017 / SWR-005, SWR-009, 결정표 F(FF 조합)"""

    def testFalseFalseCombinationYieldsNoRiskOnEitherSide(self):
        """!
        @brief left=False, right=False(FF)이면 양쪽 모두 riskActive=False, 후보/이유코드 없음.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 F, FF 조합
        @case Negative
        @breaks 위험이 없는데도 후보가 생성되는 회귀
        """
        evaluator = ApproachRiskEvaluator()

        result = evaluator.evaluate(validField(False), validField(False))

        self.assertFalse(result.leftRiskActive)
        self.assertFalse(result.rightRiskActive)
        self.assertIsNone(result.leftSuppressCandidate)
        self.assertIsNone(result.rightSuppressCandidate)


class TestIT0050LeftTrueRightFalseYieldsOnlyLeftCandidate(unittest.TestCase):
    """IT-0050 — Trace: IF-0017 / SWR-005, SWR-009, 결정표 F(FT 조합)"""

    def testLeftTrueRightFalseCombination(self):
        """!
        @brief left=True, right=False(FT)이면 LEFT만 LOCK 억제 후보(priority=2)를 생성하고
               RIGHT는 영향받지 않아야 한다(SWR-009 좌우 독립).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 F, FT 조합
        @case Positive
        @breaks 좌측 판정이 우측 결과에 영향을 주는 회귀(독립성 위반)
        """
        evaluator = ApproachRiskEvaluator()

        result = evaluator.evaluate(validField(True), validField(False))

        self.assertTrue(result.leftRiskActive)
        self.assertFalse(result.rightRiskActive)
        self.assertIsNotNone(result.leftSuppressCandidate)
        self.assertEqual(result.leftSuppressCandidate.door, Door.LEFT)
        self.assertEqual(result.leftSuppressCandidate.command, ArbitrationCommand.LOCK)
        self.assertEqual(result.leftSuppressCandidate.priority, 2)
        self.assertEqual(result.leftReasonCode, "APPROACH_RISK_LEFT")
        self.assertIsNone(result.rightSuppressCandidate)
        self.assertIsNone(result.rightReasonCode)


class TestIT0051RightTrueLeftFalseYieldsOnlyRightCandidate(unittest.TestCase):
    """IT-0051 — Trace: IF-0017 / SWR-005, SWR-009, 결정표 F(TF 조합)"""

    def testRightTrueLeftFalseCombination(self):
        """!
        @brief left=False, right=True(TF)이면 RIGHT만 LOCK 억제 후보를 생성하고 LEFT는
               영향받지 않아야 한다(우측 대칭 확인).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 F, TF 조합
        @case Positive
        @breaks 우측 판정이 좌측 결과에 영향을 주는 회귀(독립성 위반)
        """
        evaluator = ApproachRiskEvaluator()

        result = evaluator.evaluate(validField(False), validField(True))

        self.assertFalse(result.leftRiskActive)
        self.assertTrue(result.rightRiskActive)
        self.assertIsNone(result.leftSuppressCandidate)
        self.assertIsNotNone(result.rightSuppressCandidate)
        self.assertEqual(result.rightSuppressCandidate.door, Door.RIGHT)
        self.assertEqual(result.rightReasonCode, "APPROACH_RISK_RIGHT")


class TestIT0052BothTrueYieldsIndependentCandidatesOnBothDoors(unittest.TestCase):
    """IT-0052 — Trace: IF-0017 / SWR-005, SWR-009, 결정표 F(TT 조합)"""

    def testTrueTrueCombination(self):
        """!
        @brief left=True, right=True(TT)이면 양쪽 모두 각자의 LOCK 억제 후보를 독립적으로
               생성해야 한다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 F, TT 조합
        @case Positive
        @breaks 한쪽 판정이 다른 쪽 후보 생성을 누락시키는 회귀
        """
        evaluator = ApproachRiskEvaluator()

        result = evaluator.evaluate(validField(True), validField(True))

        self.assertTrue(result.leftRiskActive)
        self.assertTrue(result.rightRiskActive)
        self.assertIsNotNone(result.leftSuppressCandidate)
        self.assertIsNotNone(result.rightSuppressCandidate)
        self.assertEqual(result.leftSuppressCandidate.door, Door.LEFT)
        self.assertEqual(result.rightSuppressCandidate.door, Door.RIGHT)


class TestIT0053InvalidFieldTreatedAsNoRisk(unittest.TestCase):
    """IT-0053 — Trace: IF-0017 / 9장 확인 필요 항목, 오류주입"""

    def testInvalidLeftFieldYieldsNoRiskWithoutRaising(self):
        """!
        @brief leftApproachRiskField.valid=False는 예외 없이 riskActive=False(후보 미생성)로
               방어적으로 처리되어야 한다(10.4절 신규 원칙).
        @technique 오류주입(Fault Injection Test) — ENG-SWE2-001 9장 "확인 필요" 항목 실제 동작 검증
        @case Negative
        @breaks 무효 필드에서 예외가 발생하거나 잘못된 후보가 생성되는 회귀
        """
        evaluator = ApproachRiskEvaluator()

        result = evaluator.evaluate(invalidField(None, errorReason="MISSING"), validField(False))

        self.assertFalse(result.leftRiskActive)
        self.assertIsNone(result.leftSuppressCandidate)


class TestIT0054FieldNoneContractViolationRaises(unittest.TestCase):
    """IT-0054 — Trace: IF-0017 / 방어적 계약, 오류주입"""

    def testEitherFieldNoneRaisesValueError(self):
        """!
        @brief leftApproachRiskField/rightApproachRiskField 중 하나라도 None(상위 계약 위반)이면
               ValueError를 발생시켜야 한다.
        @technique 오류주입(Fault Injection Test) — 상위 계약 위반(None) 주입
        @case Negative
        @breaks None 입력에서 예외 없이 조용히 통과되는 회귀(방어적 계약 붕괴)
        """
        evaluator = ApproachRiskEvaluator()

        with self.assertRaises(ValueError):
            evaluator.evaluate(None, validField(False))


if __name__ == "__main__":
    unittest.main()
