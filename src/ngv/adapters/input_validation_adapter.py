"""!
@file input_validation_adapter.py
@brief IU-0001(ARC-0001 입력 검증 어댑터) — 원시 Vehicle 입력의 형식·범위 검증 및 정규화.

@par 관련 항목
- 요구사항: SWR-013(b)
- 상세설계: ENG-SWE3-001 5장/6.2절/7장 결정표 C
"""

import math

from ngv.domain.constants import (
    ERROR_REASON_INVALID_ENUM_VALUE,
    SENSOR_FAULT_FAILSAFE_SUBSTITUTE_VALUE,
    VEHICLE_SPEED_MAX_KPH,
    VEHICLE_SPEED_MIN_KPH,
)
from ngv.domain.types import CrashStatus, FieldValidationResult, NormalizedSafetyInput


class InputValidationAdapter:
    """!
    @brief 원시 입력을 검증·정규화하고, 정규화 결과를 오케스트레이터(IU-0009)에 위임한다.

    검증 함수들(validateTimestampField/validateBooleanField/applySensorFaultFailSafe/
    normalizeCycle)은 내부 상태가 없는 순수 함수이며(5장 계약), handleCycle()만 협력 객체
    (오케스트레이터)에 의존한다.
    """

    def __init__(self, orchestrator):
        """!
        @brief 정규화된 입력을 전달할 오케스트레이터(IU-0009)를 주입받는다.
        @param orchestrator IU-0009 인스턴스 — evaluateCycle(normalizedInput, nowS)를 제공
        """
        self.orchestrator = orchestrator

    @staticmethod
    def validateTimestampField(rawValue):
        """!
        @brief source_timestamp_s 필드를 검증한다.

        @param rawValue Any — 원시 source_timestamp_s
        @return FieldValidationResult[float]
        @exception 없음 — 타입 변환 실패는 내부에서 포착해 valid=False로 변환
        """
        if rawValue is None:
            return FieldValidationResult(value=None, valid=False, rawValue=rawValue, errorReason="MISSING")
        try:
            numericValue = float(rawValue)
        except (TypeError, ValueError):
            return FieldValidationResult(value=None, valid=False, rawValue=rawValue, errorReason="TYPE_ERROR")
        if not math.isfinite(numericValue) or numericValue < 0.0:
            return FieldValidationResult(
                value=None, valid=False, rawValue=rawValue, errorReason="OUT_OF_RANGE"
            )
        return FieldValidationResult(value=numericValue, valid=True, rawValue=rawValue)

    @staticmethod
    def validateBooleanField(rawValue, fieldName):
        """!
        @brief ignition_on/sensor_fault 필드를 엄격한 bool 타입 검사로 검증한다.

        @param rawValue Any — 원시 boolean 필드값
        @param fieldName str — "ignition_on"|"sensor_fault"(오류 메시지 식별용)
        @return FieldValidationResult[bool]
        @exception 없음
        """
        del fieldName  # 현재 errorReason 형식에는 포함하지 않는다(5장 계약 — 식별용 참고 인자).
        if rawValue is None:
            return FieldValidationResult(value=None, valid=False, rawValue=rawValue, errorReason="MISSING")
        if isinstance(rawValue, bool):
            return FieldValidationResult(value=rawValue, valid=True, rawValue=rawValue)
        return FieldValidationResult(value=None, valid=False, rawValue=rawValue, errorReason="TYPE_ERROR")

    @staticmethod
    def validateCrashStatusField(rawValue):
        """!
        @brief crash_status 필드를 검증한다(Phase2 신규, OEM-IF-002).

        @param rawValue Any — 원시 crash_status(열거형 이름 문자열로 가정, 5.1절 비고)
        @return FieldValidationResult[CrashStatus]
        @exception 없음 — 모든 실패는 valid=False로 표현
        """
        if rawValue is None:
            return FieldValidationResult(value=None, valid=False, rawValue=rawValue, errorReason="MISSING")
        if isinstance(rawValue, CrashStatus):
            return FieldValidationResult(value=rawValue, valid=True, rawValue=rawValue)
        if isinstance(rawValue, str):
            try:
                return FieldValidationResult(value=CrashStatus(rawValue), valid=True, rawValue=rawValue)
            except ValueError:
                return FieldValidationResult(
                    value=None, valid=False, rawValue=rawValue, errorReason=ERROR_REASON_INVALID_ENUM_VALUE
                )
        return FieldValidationResult(value=None, valid=False, rawValue=rawValue, errorReason="TYPE_ERROR")

    @staticmethod
    def validateVehicleSpeedField(rawValue):
        """!
        @brief vehicle_speed_kph 필드를 검증한다(Phase3 신규, OEM-IF-001).

        @param rawValue Any — 원시 vehicle_speed_kph
        @return FieldValidationResult[float]
        @exception 없음 — 모든 실패는 valid=False로 표현
        """
        if rawValue is None:
            return FieldValidationResult(value=None, valid=False, rawValue=rawValue, errorReason="MISSING")
        try:
            numericValue = float(rawValue)
        except (TypeError, ValueError):
            return FieldValidationResult(value=None, valid=False, rawValue=rawValue, errorReason="TYPE_ERROR")
        if (
            not math.isfinite(numericValue)
            or numericValue < VEHICLE_SPEED_MIN_KPH
            or numericValue > VEHICLE_SPEED_MAX_KPH
        ):
            return FieldValidationResult(
                value=None, valid=False, rawValue=rawValue, errorReason="OUT_OF_RANGE"
            )
        return FieldValidationResult(value=numericValue, valid=True, rawValue=rawValue)

    @staticmethod
    def applySensorFaultFailSafe(fieldResult):
        """!
        @brief sensor_fault 필드 자체가 INVALID이면 값을 fail-safe 대체값(True)으로 치환한다.

        @param fieldResult FieldValidationResult[bool] — validateBooleanField(rawSensorFault, ...)의 반환값
        @return FieldValidationResult[bool] — valid=True면 그대로, valid=False면 value만 대체
        @exception 없음
        """
        if fieldResult.valid:
            return fieldResult
        return FieldValidationResult(
            value=SENSOR_FAULT_FAILSAFE_SUBSTITUTE_VALUE,
            valid=False,
            rawValue=fieldResult.rawValue,
            errorReason=fieldResult.errorReason,
        )

    @staticmethod
    def normalizeCycle(rawInput, nowS):
        """!
        @brief 원시 입력 3개 필드를 독립적으로 검증하고 sensor_fault에 fail-safe 대체를 적용한다.

        @param rawInput RawCycleInput — 형식 미검증 원시값(12필드로 확장, Phase3)
        @param nowS float — 초 단위 현재 평가주기 시각(이 알고리즘 자체는 사용하지 않음, 6.2절)
        @return NormalizedSafetyInput(12필드로 확장)
        @exception 없음(전면 어댑터의 방어적 계약)
        """
        del nowS  # 6.2절 알고리즘은 nowS를 정규화 판단에 사용하지 않는다(사전조건 검증용 인자).
        timestampField = InputValidationAdapter.validateTimestampField(rawInput.rawSourceTimestamp)
        ignitionField = InputValidationAdapter.validateBooleanField(rawInput.rawIgnitionOn, "ignition_on")
        rawSensorFaultField = InputValidationAdapter.validateBooleanField(
            rawInput.rawSensorFault, "sensor_fault"
        )
        sensorFaultField = InputValidationAdapter.applySensorFaultFailSafe(rawSensorFaultField)
        crashStatusField = InputValidationAdapter.validateCrashStatusField(rawInput.rawCrashStatus)
        leftApproachRiskField = InputValidationAdapter.validateBooleanField(
            rawInput.rawLeftApproachRisk, "left_approach_risk"
        )
        rightApproachRiskField = InputValidationAdapter.validateBooleanField(
            rawInput.rawRightApproachRisk, "right_approach_risk"
        )
        fireField = InputValidationAdapter.validateBooleanField(rawInput.rawFireDetected, "fire_detected")
        overtempField = InputValidationAdapter.validateBooleanField(
            rawInput.rawOvertemperatureDetected, "overtemperature_detected"
        )
        adultField = InputValidationAdapter.validateBooleanField(rawInput.rawAdultPresent, "adult_present")
        vehicleSpeedField = InputValidationAdapter.validateVehicleSpeedField(rawInput.rawVehicleSpeedKph)
        isofixLeftField = InputValidationAdapter.validateBooleanField(rawInput.rawIsofixLeft, "isofix_left")
        isofixRightField = InputValidationAdapter.validateBooleanField(rawInput.rawIsofixRight, "isofix_right")
        return NormalizedSafetyInput(
            sourceTimestampField=timestampField,
            ignitionOnField=ignitionField,
            sensorFaultField=sensorFaultField,
            crashStatusField=crashStatusField,
            leftApproachRiskField=leftApproachRiskField,
            rightApproachRiskField=rightApproachRiskField,
            fireField=fireField,
            overtempField=overtempField,
            adultField=adultField,
            vehicleSpeedField=vehicleSpeedField,
            isofixLeftField=isofixLeftField,
            isofixRightField=isofixRightField,
        )

    def handleCycle(self, rawCycleInput, nowS):
        """!
        @brief 원시 입력을 정규화한 뒤 오케스트레이터(IU-0009)에 정확히 1회 위임한다.

        @param rawCycleInput RawCycleInput — 형식 미검증 원시값
        @param nowS float — 초 단위 현재 평가주기 시각(제어 루프 드라이버가 전달하는 단조 시계)
        @return CycleResult — IU-0009.evaluateCycle()의 반환값을 그대로 전달
        @exception 없음 — normalizeCycle()과 evaluateCycle() 모두 예외를 던지지 않는 계약이므로 전이적으로 안전
        """
        normalizedInput = self.normalizeCycle(rawCycleInput, nowS)
        return self.orchestrator.evaluateCycle(normalizedInput, nowS)
