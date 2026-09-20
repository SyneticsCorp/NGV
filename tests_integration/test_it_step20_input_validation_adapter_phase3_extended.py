"""!
@file test_it_step20_input_validation_adapter_phase3_extended.py
@brief 통합 20단계 — ARC-0001(입력 검증 어댑터, IF-0001 잔여필드[vehicle_speed_kph]·IF-0020
       [isofix_left/right] 검증 확장), IF-0001/IF-0020/IF-0005 확장 인터페이스 계약 검증
       (Phase3 신규).

테스트 베이시스: ENG-SWE2-001 6.2절(IF-0001 확장, IF-0020), 11장 순서표 20행("단위시험 하네스,
Vehicle 원시 입력은 시험벡터로 대체"). 회귀 범위: 7, 13단계(기존 필드 검증) — 신규 필드 검증
추가가 기존 검증 로직에 영향 없는지 확인.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.adapters.input_validation_adapter import InputValidationAdapter
from ngv.domain.types import CrashStatus, RawCycleInput


class TestIT0124ValidVehicleSpeedWithinRangeIsAccepted(unittest.TestCase):
    """IT-0124 — Trace: IF-0001(vehicle_speed_kph) / SWR-003, 요구사항 기반 시험"""

    def testSpeedWithinRangeIsParsedAsFloat(self):
        """!
        @brief rawVehicleSpeedKph=50.0(0.0~300.0 범위 내)은 valid=True, value=50.0으로
               정규화되어야 한다.
        @technique 요구사항 기반 시험(Requirements-based Test) — OEM-IF-001 정상 경로
        @case Positive
        @breaks 범위 내 정상값이 거절되는 회귀
        """
        result = InputValidationAdapter.validateVehicleSpeedField(50.0)

        self.assertTrue(result.valid)
        self.assertEqual(result.value, 50.0)


class TestIT0125VehicleSpeedBelowMinimumIsRejected(unittest.TestCase):
    """IT-0125 — Trace: IF-0001(vehicle_speed_kph) / SWR-003, 경계값분석"""

    def testNegativeSpeedIsRejectedAsOutOfRange(self):
        """!
        @brief rawVehicleSpeedKph=-1.0(범위 0.0 미만)은 valid=False, errorReason=OUT_OF_RANGE로
               거절되어야 한다(경계값 하한-1).
        @technique 경계값분석(Boundary Value Analysis) — 0.0 하한 바로 아래
        @case Negative
        @breaks 범위 밖 값이 통과되는 회귀
        """
        result = InputValidationAdapter.validateVehicleSpeedField(-1.0)

        self.assertFalse(result.valid)
        self.assertEqual(result.errorReason, "OUT_OF_RANGE")


class TestIT0126VehicleSpeedAboveMaximumIsRejected(unittest.TestCase):
    """IT-0126 — Trace: IF-0001(vehicle_speed_kph) / SWR-003, 경계값분석"""

    def testSpeedAbove300IsRejectedAsOutOfRange(self):
        """!
        @brief rawVehicleSpeedKph=300.1(범위 300.0 초과)은 valid=False, errorReason=OUT_OF_RANGE로
               거절되어야 한다(경계값 상한+1).
        @technique 경계값분석(Boundary Value Analysis) — 300.0 상한 바로 위
        @case Negative
        @breaks 범위 밖 값이 통과되는 회귀
        """
        result = InputValidationAdapter.validateVehicleSpeedField(300.1)

        self.assertFalse(result.valid)
        self.assertEqual(result.errorReason, "OUT_OF_RANGE")


class TestIT0127VehicleSpeedNonNumericIsRejectedAsTypeError(unittest.TestCase):
    """IT-0127 — Trace: IF-0001(vehicle_speed_kph) / OEM-IF-001 공통 규칙, 동등분할"""

    def testNonNumericSpeedIsRejectedAsTypeError(self):
        """!
        @brief rawVehicleSpeedKph="fast"(숫자로 변환 불가)는 valid=False, errorReason=TYPE_ERROR로
               거절되어야 한다.
        @technique 동등분할(Equivalence Partitioning) — 형식 오류 클래스
        @case Negative
        @breaks 잘못된 타입이 통과되는 회귀
        """
        result = InputValidationAdapter.validateVehicleSpeedField("fast")

        self.assertFalse(result.valid)
        self.assertEqual(result.errorReason, "TYPE_ERROR")


class TestIT0128VehicleSpeedMissingIsRejectedAsMissing(unittest.TestCase):
    """IT-0128 — Trace: IF-0001(vehicle_speed_kph) / OEM-IF-001 공통 규칙, 동등분할"""

    def testNoneRawValueIsRejectedAsMissing(self):
        """!
        @brief rawVehicleSpeedKph=None(누락)은 valid=False, errorReason=MISSING으로 거절되어야
               한다.
        @technique 동등분할(Equivalence Partitioning) — 누락 클래스
        @case Negative
        @breaks 누락 값이 통과되거나 잘못된 errorReason이 부여되는 회귀
        """
        result = InputValidationAdapter.validateVehicleSpeedField(None)

        self.assertFalse(result.valid)
        self.assertEqual(result.errorReason, "MISSING")


class TestIT0129IsofixBooleanFieldsValidatedIndependently(unittest.TestCase):
    """IT-0129 — Trace: IF-0020(isofix_left/right) / SWR-018, 요구사항 기반 시험"""

    def testLeftTrueRightFalseAreValidatedIndependently(self):
        """!
        @brief isofix_left=True, isofix_right=False는 각각 독립적으로 validateBooleanField()를
               거쳐 valid=True, value가 그대로 보존되어야 한다(좌우 독립, SWR-018b).
        @technique 요구사항 기반 시험(Requirements-based Test) — OEM-IF-008 정상 경로, 좌우 독립
        @case Positive
        @breaks 좌/우 필드 값이 뒤섞이거나 잘못 검증되는 회귀
        """
        leftResult = InputValidationAdapter.validateBooleanField(True, "isofix_left")
        rightResult = InputValidationAdapter.validateBooleanField(False, "isofix_right")

        self.assertTrue(leftResult.valid)
        self.assertTrue(leftResult.value)
        self.assertTrue(rightResult.valid)
        self.assertFalse(rightResult.value)


class TestIT0130NormalizeCycleAssemblesAllTwelveFieldsWithoutRegression(unittest.TestCase):
    """IT-0130 — Trace: IF-0005(확장) / SWR-013/SWR-005~017 회귀 확인, 요구사항 기반 시험"""

    def testNormalizeCycleAssemblesPhase3FieldsWithoutBreakingPriorFields(self):
        """!
        @brief normalizeCycle()은 Phase1 3필드 + Phase2 6필드 + Phase3 3필드를 모두 정규화해
               NormalizedSafetyInput 12필드로 조립해야 하며, Phase3 필드 추가가 이전 9필드의
               검증 결과에 영향을 주지 않아야 한다(11장 20단계 회귀 범위 — 기존 7/13단계 필드
               회귀 확인).
        @technique 요구사항 기반 시험(Requirements-based Test) — 정규화 조립 전체 계약(12필드)
        @case Positive
        @breaks Phase3 필드 추가로 Phase1/2 필드 정규화 결과가 훼손되는 회귀
        """
        rawInput = RawCycleInput(
            rawSourceTimestamp=1.000,
            rawIgnitionOn=True,
            rawSensorFault=False,
            rawCrashStatus="PENDING",
            rawLeftApproachRisk=True,
            rawRightApproachRisk=False,
            rawFireDetected=False,
            rawOvertemperatureDetected=True,
            rawAdultPresent=False,
            rawVehicleSpeedKph=3.0,
            rawIsofixLeft=True,
            rawIsofixRight=False,
        )

        normalized = InputValidationAdapter.normalizeCycle(rawInput, 1.000)

        self.assertTrue(normalized.sourceTimestampField.valid)
        self.assertTrue(normalized.ignitionOnField.valid)
        self.assertFalse(normalized.sensorFaultField.value)
        self.assertEqual(normalized.crashStatusField.value, CrashStatus.PENDING)
        self.assertTrue(normalized.leftApproachRiskField.value)
        self.assertFalse(normalized.rightApproachRiskField.value)
        self.assertFalse(normalized.fireField.value)
        self.assertTrue(normalized.overtempField.value)
        self.assertFalse(normalized.adultField.value)
        self.assertTrue(normalized.vehicleSpeedField.valid)
        self.assertEqual(normalized.vehicleSpeedField.value, 3.0)
        self.assertTrue(normalized.isofixLeftField.value)
        self.assertFalse(normalized.isofixRightField.value)


if __name__ == "__main__":
    unittest.main()
