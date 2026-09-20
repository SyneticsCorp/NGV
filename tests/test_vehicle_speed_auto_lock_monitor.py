"""!
@file test_vehicle_speed_auto_lock_monitor.py
@brief IU-0014(ARC-0014 차속 자동주행잠금 감시) 함수 계약 검증(ENG-SWE3-001 5.12절/6.14절/
       7장 결정표 L, SWR-003).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.domain.constants import PRIORITY_AUTO_DRIVE_LOCK, REASON_CODE_AUTO_DRIVE_LOCK
from ngv.domain.types import ArbitrationCommand, Door, FieldValidationResult
from ngv.core.vehicle_speed_auto_lock_monitor import VehicleSpeedAutoLockMonitor


def validField(value):
    """테스트 헬퍼 — 유효한 FieldValidationResult[float]를 만든다."""
    return FieldValidationResult(value=value, valid=True, rawValue=value)


def invalidField(rawValue, errorReason="TYPE_ERROR"):
    """테스트 헬퍼 — 무효한 FieldValidationResult를 만든다."""
    return FieldValidationResult(value=None, valid=False, rawValue=rawValue, errorReason=errorReason)


class TestVehicleSpeedAutoLockMonitorEvaluate(unittest.TestCase):
    """IU-0014.evaluate() 결정표 L 계약 검증."""

    def testSpeedAtOrAboveThresholdProducesBothDoorsLockCandidate(self):
        """!
        @brief value>=3.0이면 door=BOTH, command=LOCK, priority=6인 자동주행잠금 후보를 만든다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 L, valid=True/>=3.0 행
        @case Positive — SWR-003(a) 자동주행잠금 후보 생성 경로를 검증
        @breaks 3km/h 이상인데도 lockCandidate가 None으로 남는 회귀
        """
        result = VehicleSpeedAutoLockMonitor().evaluate(validField(10.0), 1.0)

        self.assertTrue(result.locked)
        self.assertIsNotNone(result.lockCandidate)
        self.assertEqual(result.lockCandidate.door, Door.BOTH)
        self.assertEqual(result.lockCandidate.command, ArbitrationCommand.LOCK)
        self.assertEqual(result.lockCandidate.priority, PRIORITY_AUTO_DRIVE_LOCK)
        self.assertEqual(result.lockCandidate.reasonCode, REASON_CODE_AUTO_DRIVE_LOCK)

    def testSpeedExactlyAtThresholdBoundaryIsLocked(self):
        """!
        @brief value==3.0(경계값)은 임계값 성립 쪽(>=)에 포함되어 locked=True다.
        @technique 경계값분석(Boundary Value Analysis) — SWR-003(a) 3.0km/h 경계값 자체
        @case Positive — 경계값 자체가 LOCK 성립 쪽에 포함되는지 검증(2.9/3.0/3.1 시험벡터의 중심)
        @breaks 경계 비교 연산자가 > 대신 >=가 아니어서 3.0km/h를 거절하는 회귀
        """
        result = VehicleSpeedAutoLockMonitor().evaluate(validField(3.0), 1.0)

        self.assertTrue(result.locked)

    def testSpeedJustBelowThresholdIsNotLocked(self):
        """!
        @brief value==2.9(경계값 바로 아래)는 locked=False, lockCandidate=None이다.
        @technique 경계값분석(Boundary Value Analysis) — 경계값 바로 아래(2.9km/h)
        @case Negative — 임계값 미달 시 후보를 생성하지 않는지 검증
        @breaks 2.9km/h에서도 잘못 LOCK 후보를 생성하는 회귀
        """
        result = VehicleSpeedAutoLockMonitor().evaluate(validField(2.9), 1.0)

        self.assertFalse(result.locked)
        self.assertIsNone(result.lockCandidate)

    def testSpeedJustAboveThresholdIsLocked(self):
        """!
        @brief value==3.1(경계값 바로 위)은 locked=True다.
        @technique 경계값분석(Boundary Value Analysis) — 경계값 바로 위(3.1km/h)
        @case Positive — 2.9/3.0/3.1 3점 경계값 시험벡터의 나머지 한 점을 검증
        @breaks 3.1km/h에서도 LOCK 후보를 생성하지 않는 회귀
        """
        result = VehicleSpeedAutoLockMonitor().evaluate(validField(3.1), 1.0)

        self.assertTrue(result.locked)

    def testInvalidFieldRejectsWithoutGeneratingNewCandidate(self):
        """!
        @brief valid=False이면 locked=False, lockCandidate=None이다(10.4절/10.7절 원칙).
        @technique 동등분할(Equivalence Partitioning) — 무효 입력 클래스의 대표값
        @case Negative — 신뢰할 수 없는 데이터로 새 LOCK 후보를 생성하지 않는 방어 원칙을 검증
        @breaks 손상된 입력에서도 LOCK 후보를 생성해 불필요한 잠금을 유발하는 회귀
        """
        result = VehicleSpeedAutoLockMonitor().evaluate(invalidField("fast"), 1.0)

        self.assertFalse(result.locked)
        self.assertIsNone(result.lockCandidate)

    def testRaisesValueErrorWhenFieldIsNone(self):
        """!
        @brief vehicleSpeedField가 None이면 ValueError를 던진다(상위 계약 위반 방어).
        @technique 오류추측(Error Guessing) — IU-0010 선례와 동일한 방어적 예외 패턴
        @case Negative — 사전조건(not None) 위반 시 방어적 예외를 검증
        @breaks None 입력이 예외 없이 통과되어 하류에서 AttributeError로 이어지는 회귀
        """
        with self.assertRaises(ValueError):
            VehicleSpeedAutoLockMonitor().evaluate(None, 1.0)


if __name__ == "__main__":
    unittest.main()
