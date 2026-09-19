"""!
@file test_it_step13_input_validation_adapter_extended.py
@brief 통합 13단계 — ARC-0001(입력 검증 어댑터, 신규 필드 검증 확장), IF-0013/IF-0014/IF-0015,
       IF-0005 확장 데이터 인터페이스 계약 검증(Phase2 갱신).

테스트 베이시스: ENG-SWE2-001 6.2절(IF-0013/IF-0014/IF-0015), 11장 순서표 13행("단위시험
하네스, Vehicle 원시 입력은 시험벡터로 대체"). 회귀 범위: 기존 7단계(SWR-013 관련 필드)
— 신규 필드 검증 추가가 기존 검증 로직에 영향 없는지 확인.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.adapters.input_validation_adapter import InputValidationAdapter
from ngv.domain.types import CrashStatus, RawCycleInput


class TestIT0075ValidCrashStatusEnumStringIsAccepted(unittest.TestCase):
    """IT-0075 — Trace: IF-0013 / SWR-007, 결정표 E 입력 경로"""

    def testConfirmedStringIsParsedToCrashStatusEnum(self):
        """!
        @brief rawCrashStatus="CONFIRMED"(정의된 열거값 문자열)는 valid=True,
               value=CrashStatus.CONFIRMED로 정규화되어야 한다.
        @technique 요구사항 기반 시험(Requirements-based Test) — OEM-IF-002 정상 경로
        @case Positive
        @breaks 정의된 열거값 문자열이 거절되는 회귀
        """
        result = InputValidationAdapter.validateCrashStatusField("CONFIRMED")

        self.assertTrue(result.valid)
        self.assertEqual(result.value, CrashStatus.CONFIRMED)


class TestIT0093CrashStatusEnumInstanceIsAcceptedDirectly(unittest.TestCase):
    """IT-0093 — Trace: IF-0013 / 5.1절 비고(이미 파싱된 열거형 인스턴스 경로), 동등분할"""

    def testAlreadyCrashStatusInstanceIsAcceptedWithoutReparsing(self):
        """!
        @brief rawCrashStatus가 이미 CrashStatus enum 인스턴스(예: 상위 계층이 이미 파싱해
               전달한 경우)이면 재파싱 없이 valid=True로 그대로 수용되어야 한다.
        @technique 동등분할(Equivalence Partitioning) — 이미 파싱된 인스턴스 클래스(문자열이
                   아닌 입력 경로)
        @case Positive
        @breaks 이미 유효한 CrashStatus 인스턴스가 문자열이 아니라는 이유로 거절되는 회귀
        """
        result = InputValidationAdapter.validateCrashStatusField(CrashStatus.PENDING)

        self.assertTrue(result.valid)
        self.assertEqual(result.value, CrashStatus.PENDING)


class TestIT0076InvalidCrashStatusEnumValueIsRejected(unittest.TestCase):
    """IT-0076 — Trace: IF-0013 / OEM-IF-002 공통 규칙, 동등분할"""

    def testUnknownEnumStringIsRejectedWithInvalidEnumReason(self):
        """!
        @brief 정의된 3개 값(NONE/PENDING/CONFIRMED) 외의 문자열은 valid=False,
               errorReason=INVALID_ENUM_VALUE로 거절되어야 한다.
        @technique 동등분할(Equivalence Partitioning) — 정의되지 않은 열거값 클래스
        @case Negative
        @breaks 정의되지 않은 값이 통과되는 회귀
        """
        result = InputValidationAdapter.validateCrashStatusField("BOGUS_STATUS")

        self.assertFalse(result.valid)
        self.assertEqual(result.errorReason, "INVALID_ENUM_VALUE")


class TestIT0077MissingCrashStatusIsRejected(unittest.TestCase):
    """IT-0077 — Trace: IF-0013 / OEM-IF-002 공통 규칙, 동등분할"""

    def testNoneRawValueIsRejectedAsMissing(self):
        """!
        @brief rawCrashStatus=None(누락)은 valid=False, errorReason=MISSING으로 거절되어야 한다.
        @technique 동등분할(Equivalence Partitioning) — 누락 클래스
        @case Negative
        @breaks 누락 값이 통과되거나 잘못된 errorReason이 부여되는 회귀
        """
        result = InputValidationAdapter.validateCrashStatusField(None)

        self.assertFalse(result.valid)
        self.assertEqual(result.errorReason, "MISSING")


class TestIT0078NonStringCrashStatusIsRejectedAsTypeError(unittest.TestCase):
    """IT-0078 — Trace: IF-0013 / OEM-IF-002 공통 규칙, 동등분할"""

    def testIntegerRawValueIsRejectedAsTypeError(self):
        """!
        @brief rawCrashStatus가 문자열도 CrashStatus 인스턴스도 아니면(예: 정수) valid=False,
               errorReason=TYPE_ERROR로 거절되어야 한다.
        @technique 동등분할(Equivalence Partitioning) — 형식 오류 클래스
        @case Negative
        @breaks 잘못된 타입이 통과되는 회귀
        """
        result = InputValidationAdapter.validateCrashStatusField(1)

        self.assertFalse(result.valid)
        self.assertEqual(result.errorReason, "TYPE_ERROR")


class TestIT0079ApproachRiskBooleanFieldsValidatedIndependently(unittest.TestCase):
    """IT-0079 — Trace: IF-0014 / SWR-005, SWR-009, 요구사항 기반 시험"""

    def testLeftTrueRightFalseAreValidatedIndependently(self):
        """!
        @brief rear_left_approach_risk=True, rear_right_approach_risk=False는 각각 독립적으로
               validateBooleanField()를 거쳐 valid=True, value가 그대로 보존되어야 한다.
        @technique 요구사항 기반 시험(Requirements-based Test) — OEM-IF-003 정상 경로, 좌우 독립
        @case Positive
        @breaks 좌/우 필드 값이 뒤섞이거나 잘못 검증되는 회귀
        """
        leftResult = InputValidationAdapter.validateBooleanField(True, "left_approach_risk")
        rightResult = InputValidationAdapter.validateBooleanField(False, "right_approach_risk")

        self.assertTrue(leftResult.valid)
        self.assertTrue(leftResult.value)
        self.assertTrue(rightResult.valid)
        self.assertFalse(rightResult.value)


class TestIT0080FireSeriesNonBooleanIsRejectedAsTypeError(unittest.TestCase):
    """IT-0080 — Trace: IF-0015 / SWR-017, OEM-IF-007 공통 규칙, 동등분할"""

    def testNonBooleanFireDetectedIsRejected(self):
        """!
        @brief fire_detected가 bool이 아닌 값(예: 문자열 "yes")이면 valid=False,
               errorReason=TYPE_ERROR로 거절되어야 한다(overtemperature_detected/adult_present와
               동일한 검증 로직 재사용 확인).
        @technique 동등분할(Equivalence Partitioning) — 형식 오류 클래스
        @case Negative
        @breaks 잘못된 타입의 화재계열 필드가 통과되는 회귀
        """
        result = InputValidationAdapter.validateBooleanField("yes", "fire_detected")

        self.assertFalse(result.valid)
        self.assertEqual(result.errorReason, "TYPE_ERROR")


class TestIT0081NormalizeCycleAssemblesAllNineFieldsWithoutRegression(unittest.TestCase):
    """IT-0081 — Trace: IF-0005(확장) / SWR-013 회귀 확인, 요구사항 기반 시험"""

    def testNormalizeCycleAssemblesPhase2FieldsWithoutBreakingPhase1Fields(self):
        """!
        @brief normalizeCycle()은 Phase1 3필드(timestamp/ignition/sensorFault)와 Phase2 6필드를
               모두 정규화해 NormalizedSafetyInput 9필드로 조립해야 하며, Phase2 필드 추가가
               Phase1 필드의 검증 결과에 영향을 주지 않아야 한다(11장 13단계 회귀 범위 — 기존
               7단계 SWR-013 관련 필드 회귀 확인).
        @technique 요구사항 기반 시험(Requirements-based Test) — 정규화 조립 전체 계약
        @case Positive
        @breaks Phase2 필드 추가로 Phase1 필드 정규화 결과가 훼손되는 회귀
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
        )

        normalized = InputValidationAdapter.normalizeCycle(rawInput, 1.000)

        self.assertTrue(normalized.sourceTimestampField.valid)
        self.assertEqual(normalized.sourceTimestampField.value, 1.000)
        self.assertTrue(normalized.ignitionOnField.valid)
        self.assertTrue(normalized.sensorFaultField.valid)
        self.assertFalse(normalized.sensorFaultField.value)
        self.assertTrue(normalized.crashStatusField.valid)
        self.assertEqual(normalized.crashStatusField.value, CrashStatus.PENDING)
        self.assertTrue(normalized.leftApproachRiskField.value)
        self.assertFalse(normalized.rightApproachRiskField.value)
        self.assertFalse(normalized.fireField.value)
        self.assertTrue(normalized.overtempField.value)
        self.assertFalse(normalized.adultField.value)


if __name__ == "__main__":
    unittest.main()
