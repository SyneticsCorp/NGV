"""!
@file test_it_step17_vehicle_speed_auto_lock_monitor.py
@brief 통합 17단계 — ARC-0014(차속 자동주행잠금 감시), IF-0021 인터페이스 계약 검증
       (신규, Phase3).

테스트 베이시스: ENG-SWE2-001 6.1절(IF-0021), 11장 순서표 17행("단위시험 하네스, 차속 경계값
2.9/3.0/3.1 km/h 시험벡터"). ENG-SWE3-001 7장 결정표 L(IU-0014 차속 판정)을 그대로 시험벡터
도출에 사용한다.
"""

import unittest

from tests_integration.it_helpers import invalidField, validField
from ngv.core.vehicle_speed_auto_lock_monitor import VehicleSpeedAutoLockMonitor
from ngv.domain.types import ArbitrationCommand, Door


class TestIT0104BelowThresholdYieldsNoCandidate(unittest.TestCase):
    """IT-0104 — Trace: IF-0021 / SWR-003(a), 결정표 L, 경계값분석"""

    def testSpeed29YieldsNotLocked(self):
        """!
        @brief vehicle_speed_kph=2.9(임계 3.0 미만)이면 locked=False이고 후보를 생성하지
               않아야 한다(경계값 하한-1).
        @technique 경계값분석(Boundary Value Analysis) — 3.0km/h 임계 바로 아래
        @case Negative
        @breaks 임계 미만에서도 잠금 후보가 생성되는 회귀
        """
        monitor = VehicleSpeedAutoLockMonitor()

        result = monitor.evaluate(validField(2.9), 1.000)

        self.assertFalse(result.locked)
        self.assertIsNone(result.lockCandidate)


class TestIT0105AtThresholdYieldsLockCandidatePrioritySix(unittest.TestCase):
    """IT-0105 — Trace: IF-0021 / SWR-003(a), 결정표 L, 경계값분석"""

    def testSpeedExactly30YieldsLockedWithCandidate(self):
        """!
        @brief vehicle_speed_kph=3.0(임계값 자체, 이상 조건)이면 locked=True와 door=BOTH/
               command=LOCK/priority=6/reasonCode=AUTO_DRIVE_LOCK인 lockCandidate를 생성해야
               한다(SWR-003a, 경계값 정확히 일치).
        @technique 경계값분석(Boundary Value Analysis) — 3.0km/h 임계값 자체
        @case Positive
        @breaks 임계값 자체에서 미포함(잠금 미발생)으로 오판정되는 경계 오류(off-by-one) 회귀
        """
        monitor = VehicleSpeedAutoLockMonitor()

        result = monitor.evaluate(validField(3.0), 1.000)

        self.assertTrue(result.locked)
        self.assertIsNotNone(result.lockCandidate)
        self.assertEqual(result.lockCandidate.door, Door.BOTH)
        self.assertEqual(result.lockCandidate.command, ArbitrationCommand.LOCK)
        self.assertEqual(result.lockCandidate.priority, 6)
        self.assertEqual(result.lockCandidate.reasonCode, "AUTO_DRIVE_LOCK")


class TestIT0106AboveThresholdYieldsLockCandidate(unittest.TestCase):
    """IT-0106 — Trace: IF-0021 / SWR-003(a), 결정표 L, 경계값분석"""

    def testSpeed31YieldsLocked(self):
        """!
        @brief vehicle_speed_kph=3.1(임계 초과)이면 locked=True여야 한다(경계값 상한+1).
        @technique 경계값분석(Boundary Value Analysis) — 3.0km/h 임계 바로 위
        @case Positive
        @breaks 임계 초과에서도 잠금이 미발생하는 회귀
        """
        monitor = VehicleSpeedAutoLockMonitor()

        result = monitor.evaluate(validField(3.1), 1.000)

        self.assertTrue(result.locked)
        self.assertIsNotNone(result.lockCandidate)


class TestIT0107InvalidFieldYieldsNoCandidateWithoutException(unittest.TestCase):
    """IT-0107 — Trace: IF-0021 / 9장 확인 필요 항목(10.4절 원칙 적용), 오류주입"""

    def testInvalidFieldIsTreatedAsNotLockedWithoutRaising(self):
        """!
        @brief vehicleSpeedField.valid=False(범위 0.0~300.0 밖 등)는 예외 없이 locked=False
               (후보 미생성)로 방어적으로 처리되어야 한다(9장 — 10.4절 원칙과 동일).
        @technique 오류주입(Fault Injection Test) — ENG-SWE2-001 9장 "확인 필요" 항목 실제 동작 검증
        @case Negative
        @breaks 무효 필드에서 예외가 발생하거나 잘못된 후보가 생성되는 회귀
        """
        monitor = VehicleSpeedAutoLockMonitor()

        result = monitor.evaluate(invalidField(350.0, errorReason="OUT_OF_RANGE"), 1.000)

        self.assertFalse(result.locked)
        self.assertIsNone(result.lockCandidate)


class TestIT0108VehicleSpeedFieldNoneContractViolationRaises(unittest.TestCase):
    """IT-0108 — Trace: IF-0021 / 방어적 계약, 오류주입"""

    def testVehicleSpeedFieldNoneRaisesValueError(self):
        """!
        @brief vehicleSpeedField 자체가 None(상위 계약 위반, 오케스트레이터 배선 결함
               시뮬레이션)이면 ValueError를 발생시켜야 한다(방어적 계약).
        @technique 오류주입(Fault Injection Test) — 상위 계약 위반(None) 주입
        @case Negative
        @breaks None 입력에서 예외 없이 조용히 통과되는 회귀(방어적 계약 붕괴)
        """
        monitor = VehicleSpeedAutoLockMonitor()

        with self.assertRaises(ValueError):
            monitor.evaluate(None, 1.000)


if __name__ == "__main__":
    unittest.main()
