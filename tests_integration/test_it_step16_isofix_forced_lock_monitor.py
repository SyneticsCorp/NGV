"""!
@file test_it_step16_isofix_forced_lock_monitor.py
@brief 통합 16단계 — ARC-0015(ISOFIX 강제잠금 감시), IF-0022 인터페이스 계약 검증(신규, Phase3).

테스트 베이시스: ENG-SWE2-001 6.1절(IF-0022), 11장 순서표 16행("단위시험 하네스, 좌우 4조합
FF/FT/TF/TT 시험벡터 — ARC-0011과 동일 패턴"). ENG-SWE3-001 7장 결정표 M(IU-0015 좌우 ISOFIX
판정)을 그대로 시험벡터 도출에 사용한다.
"""

import unittest

from tests_integration.it_helpers import invalidField, validField
from ngv.core.isofix_forced_lock_monitor import IsofixForcedLockMonitor
from ngv.domain.types import ArbitrationCommand, Door


class TestIT0098BothFalseYieldsNoCandidateOnEitherDoor(unittest.TestCase):
    """IT-0098 — Trace: IF-0022 / SWR-018(a)/(b), 결정표 M(FF 조합)"""

    def testFalseFalseCombinationYieldsNoLockOnEitherSide(self):
        """!
        @brief left=False, right=False(FF)이면 양쪽 모두 lockActive=False, 후보/이유코드 없음.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 M, FF 조합
        @case Negative
        @breaks ISOFIX 미연결인데도 후보가 생성되는 회귀
        """
        monitor = IsofixForcedLockMonitor()

        result = monitor.evaluate(validField(False), validField(False))

        self.assertFalse(result.leftLockActive)
        self.assertFalse(result.rightLockActive)
        self.assertIsNone(result.leftLockCandidate)
        self.assertIsNone(result.rightLockCandidate)


class TestIT0099LeftTrueRightFalseYieldsOnlyLeftCandidate(unittest.TestCase):
    """IT-0099 — Trace: IF-0022 / SWR-018(a)/(b), 결정표 M(FT 조합)"""

    def testLeftTrueRightFalseCombination(self):
        """!
        @brief left=True, right=False(FT)이면 LEFT만 LOCK 강제잠금 후보(priority=5)를 생성하고
               RIGHT는 영향받지 않아야 한다(SWR-018b 좌우 독립).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 M, FT 조합
        @case Positive
        @breaks 좌측 판정이 우측 결과에 영향을 주는 회귀(독립성 위반)
        """
        monitor = IsofixForcedLockMonitor()

        result = monitor.evaluate(validField(True), validField(False))

        self.assertTrue(result.leftLockActive)
        self.assertFalse(result.rightLockActive)
        self.assertIsNotNone(result.leftLockCandidate)
        self.assertEqual(result.leftLockCandidate.door, Door.LEFT)
        self.assertEqual(result.leftLockCandidate.command, ArbitrationCommand.LOCK)
        self.assertEqual(result.leftLockCandidate.priority, 5)
        self.assertEqual(result.leftReasonCode, "ISOFIX_FORCED_LOCK_LEFT")
        self.assertIsNone(result.rightLockCandidate)
        self.assertIsNone(result.rightReasonCode)


class TestIT0100RightTrueLeftFalseYieldsOnlyRightCandidate(unittest.TestCase):
    """IT-0100 — Trace: IF-0022 / SWR-018(a)/(b), 결정표 M(TF 조합)"""

    def testRightTrueLeftFalseCombination(self):
        """!
        @brief left=False, right=True(TF)이면 RIGHT만 LOCK 강제잠금 후보를 생성하고 LEFT는
               영향받지 않아야 한다(우측 대칭 확인).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 M, TF 조합
        @case Positive
        @breaks 우측 판정이 좌측 결과에 영향을 주는 회귀(독립성 위반)
        """
        monitor = IsofixForcedLockMonitor()

        result = monitor.evaluate(validField(False), validField(True))

        self.assertFalse(result.leftLockActive)
        self.assertTrue(result.rightLockActive)
        self.assertIsNone(result.leftLockCandidate)
        self.assertIsNotNone(result.rightLockCandidate)
        self.assertEqual(result.rightLockCandidate.door, Door.RIGHT)
        self.assertEqual(result.rightLockCandidate.priority, 5)
        self.assertEqual(result.rightReasonCode, "ISOFIX_FORCED_LOCK_RIGHT")


class TestIT0101BothTrueYieldsIndependentCandidatesOnBothDoors(unittest.TestCase):
    """IT-0101 — Trace: IF-0022 / SWR-018(a)/(b), 결정표 M(TT 조합)"""

    def testTrueTrueCombination(self):
        """!
        @brief left=True, right=True(TT)이면 양쪽 모두 각자의 LOCK 강제잠금 후보를 독립적으로
               생성해야 한다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 M, TT 조합
        @case Positive
        @breaks 한쪽 판정이 다른 쪽 후보 생성을 누락시키는 회귀
        """
        monitor = IsofixForcedLockMonitor()

        result = monitor.evaluate(validField(True), validField(True))

        self.assertTrue(result.leftLockActive)
        self.assertTrue(result.rightLockActive)
        self.assertIsNotNone(result.leftLockCandidate)
        self.assertIsNotNone(result.rightLockCandidate)
        self.assertEqual(result.leftLockCandidate.door, Door.LEFT)
        self.assertEqual(result.rightLockCandidate.door, Door.RIGHT)


class TestIT0102InvalidLeftFieldTreatedAsNoLockWithoutException(unittest.TestCase):
    """IT-0102 — Trace: IF-0022 / 9장 확인 필요 항목, 오류주입"""

    def testInvalidLeftFieldYieldsNoLockWithoutRaising(self):
        """!
        @brief isofixLeftField.valid=False는 예외 없이 leftLockActive=False(후보 미생성)로
               방어적으로 처리되어야 한다(ARC-0011/ARC-0013과 동일한 9장 원칙 적용).
        @technique 오류주입(Fault Injection Test) — ENG-SWE2-001 9장 "확인 필요" 항목 실제 동작 검증
        @case Negative
        @breaks 무효 필드에서 예외가 발생하거나 잘못된 후보가 생성되는 회귀
        """
        monitor = IsofixForcedLockMonitor()

        result = monitor.evaluate(invalidField(None, errorReason="MISSING"), validField(False))

        self.assertFalse(result.leftLockActive)
        self.assertIsNone(result.leftLockCandidate)


class TestIT0103IsofixFieldNoneContractViolationRaises(unittest.TestCase):
    """IT-0103 — Trace: IF-0022 / 방어적 계약, 오류주입"""

    def testEitherFieldNoneRaisesValueError(self):
        """!
        @brief isofixLeftField/isofixRightField 중 하나라도 None(상위 계약 위반)이면 ValueError를
               발생시켜야 한다.
        @technique 오류주입(Fault Injection Test) — 상위 계약 위반(None) 주입
        @case Negative
        @breaks None 입력에서 예외 없이 조용히 통과되는 회귀(방어적 계약 붕괴)
        """
        monitor = IsofixForcedLockMonitor()

        with self.assertRaises(ValueError):
            monitor.evaluate(None, validField(False))


if __name__ == "__main__":
    unittest.main()
