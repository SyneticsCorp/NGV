"""!
@file test_it_step11_fire_overtemp_occupant_monitor.py
@brief 통합 11단계 — ARC-0013(화재/과온/탑승 감시), IF-0019 인터페이스 계약 검증(신규, Phase2).

테스트 베이시스: ENG-SWE2-001 6.1절(IF-0019), 11장 순서표 11행("단위시험 하네스, 단독/복합
입력 조합 시험벡터"). ENG-SWE3-001 7장 결정표 H(OR 판정)를 그대로 사용한다.
"""

import unittest

from tests_integration.it_helpers import invalidField, validField
from ngv.core.fire_overtemp_occupant_monitor import FireOvertempOccupantMonitor
from ngv.domain.types import ArbitrationCommand, Door


class TestIT0062FireOnlyTriggersForcedRelease(unittest.TestCase):
    """IT-0062 — Trace: IF-0019 / SWR-017, 결정표 H(단독 입력)"""

    def testFireDetectedAloneTriggersRelease(self):
        """!
        @brief fire_detected=True만 단독으로 TRUE이면 triggered=True, reasonCodes=[FIRE_DETECTED],
               BOTH/RELEASE/priority=3 후보가 생성되어야 한다.
        @technique 동등분할(Equivalence Partitioning) — 결정표 H, fire 단독 대표값
        @case Positive
        @breaks fire 단독으로도 트리거가 성립하지 않는 회귀
        """
        monitor = FireOvertempOccupantMonitor()

        result = monitor.evaluate(validField(True), validField(False), validField(False))

        self.assertTrue(result.triggered)
        self.assertEqual(result.triggeredReasonCodes, ["FIRE_DETECTED"])
        self.assertIsNotNone(result.releaseCandidate)
        self.assertEqual(result.releaseCandidate.door, Door.BOTH)
        self.assertEqual(result.releaseCandidate.command, ArbitrationCommand.RELEASE)
        self.assertEqual(result.releaseCandidate.priority, 3)
        self.assertEqual(result.releaseCandidate.reasonCode, "FORCED_RELEASE")


class TestIT0063OvertemperatureOnlyTriggersForcedRelease(unittest.TestCase):
    """IT-0063 — Trace: IF-0019 / SWR-017, 결정표 H(단독 입력)"""

    def testOvertemperatureAloneTriggersRelease(self):
        """!
        @brief overtemperature_detected=True만 단독으로 TRUE이면 triggered=True,
               reasonCodes=[OVERTEMPERATURE_DETECTED]여야 한다.
        @technique 동등분할(Equivalence Partitioning) — 결정표 H, overtemp 단독 대표값
        @case Positive
        @breaks overtemp 단독으로도 트리거가 성립하지 않는 회귀
        """
        monitor = FireOvertempOccupantMonitor()

        result = monitor.evaluate(validField(False), validField(True), validField(False))

        self.assertTrue(result.triggered)
        self.assertEqual(result.triggeredReasonCodes, ["OVERTEMPERATURE_DETECTED"])


class TestIT0064AdultPresentOnlyTriggersForcedRelease(unittest.TestCase):
    """IT-0064 — Trace: IF-0019 / SWR-017, 결정표 H(단독 입력)"""

    def testAdultPresentAloneTriggersRelease(self):
        """!
        @brief adult_present=True만 단독으로 TRUE이면 triggered=True,
               reasonCodes=[ADULT_PRESENT_DETECTED]여야 한다.
        @technique 동등분할(Equivalence Partitioning) — 결정표 H, adult 단독 대표값
        @case Positive
        @breaks adult 단독으로도 트리거가 성립하지 않는 회귀
        """
        monitor = FireOvertempOccupantMonitor()

        result = monitor.evaluate(validField(False), validField(False), validField(True))

        self.assertTrue(result.triggered)
        self.assertEqual(result.triggeredReasonCodes, ["ADULT_PRESENT_DETECTED"])


class TestIT0065AllThreeSimultaneouslyRecordsAllReasonCodes(unittest.TestCase):
    """IT-0065 — Trace: IF-0019 / SWR-017, 결정표 H(복합 입력)"""

    def testAllThreeTrueRecordsAllThreeReasonCodesInOrder(self):
        """!
        @brief 세 입력이 모두 TRUE(복합)이면 triggeredReasonCodes에 [FIRE_DETECTED,
               OVERTEMPERATURE_DETECTED, ADULT_PRESENT_DETECTED] 순서로 모두 기록되어야 한다.
        @technique 동등분할(Equivalence Partitioning) — 결정표 H, 복합(전부 TRUE) 대표값
        @case Positive
        @breaks 복합 입력 중 일부 이유코드가 누락되는 회귀
        """
        monitor = FireOvertempOccupantMonitor()

        result = monitor.evaluate(validField(True), validField(True), validField(True))

        self.assertTrue(result.triggered)
        self.assertEqual(
            result.triggeredReasonCodes,
            ["FIRE_DETECTED", "OVERTEMPERATURE_DETECTED", "ADULT_PRESENT_DETECTED"],
        )


class TestIT0066AllFalseYieldsNoTrigger(unittest.TestCase):
    """IT-0066 — Trace: IF-0019, 결정표 H(전부 FALSE)"""

    def testAllFalseYieldsNoTriggerAndNoCandidate(self):
        """!
        @brief 세 입력이 모두 FALSE이면 triggered=False, releaseCandidate=None,
               triggeredReasonCodes=[]여야 한다.
        @technique 동등분할(Equivalence Partitioning) — 결정표 H, 전부 FALSE 대표값
        @case Negative
        @breaks 트리거 조건이 없는데도 후보가 생성되는 회귀
        """
        monitor = FireOvertempOccupantMonitor()

        result = monitor.evaluate(validField(False), validField(False), validField(False))

        self.assertFalse(result.triggered)
        self.assertIsNone(result.releaseCandidate)
        self.assertEqual(result.triggeredReasonCodes, [])


class TestIT0067InvalidFieldTreatedAsFalse(unittest.TestCase):
    """IT-0067 — Trace: IF-0019 / 9장 확인 필요 항목, 오류주입"""

    def testInvalidFireFieldIsTreatedAsFalseWithoutRaising(self):
        """!
        @brief fireField.valid=False는 예외 없이 FALSE(트리거 미기여)로 방어적으로 처리되어야
               한다(10.4절 신규 원칙).
        @technique 오류주입(Fault Injection Test) — ENG-SWE2-001 9장 "확인 필요" 항목 실제 동작 검증
        @case Negative
        @breaks 무효 필드가 트리거에 잘못 기여하는 회귀
        """
        monitor = FireOvertempOccupantMonitor()

        result = monitor.evaluate(
            invalidField(None, errorReason="MISSING"), validField(False), validField(False)
        )

        self.assertFalse(result.triggered)
        self.assertEqual(result.triggeredReasonCodes, [])


class TestIT0068AnyFieldNoneContractViolationRaises(unittest.TestCase):
    """IT-0068 — Trace: IF-0019 / 방어적 계약, 오류주입"""

    def testAnyFieldNoneRaisesValueError(self):
        """!
        @brief fireField/overtempField/adultField 중 하나라도 None(상위 계약 위반)이면
               ValueError를 발생시켜야 한다.
        @technique 오류주입(Fault Injection Test) — 상위 계약 위반(None) 주입
        @case Negative
        @breaks None 입력에서 예외 없이 조용히 통과되는 회귀(방어적 계약 붕괴)
        """
        monitor = FireOvertempOccupantMonitor()

        with self.assertRaises(ValueError):
            monitor.evaluate(validField(False), None, validField(False))


if __name__ == "__main__":
    unittest.main()
