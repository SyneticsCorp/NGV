"""!
@file state_manager.py
@brief IU-0003(ARC-0003 상태 관리자) — NORMAL/DEGRADED/FAULT/OFF 상태 판정
       (FAULT>OFF>DEGRADED>NORMAL 우선순위, Phase3 OFF 판정 추가).

@par 관련 항목
- 요구사항: SWR-013(a), SWR-021(b), SWR-020(a)/(b)
- 상세설계: ENG-SWE3-001 5.11절/6.13절/7장 결정표 K/8.7절~8.8절
"""

from ngv.domain.constants import (
    WARNING_CODE_IGNITION_OFF,
    WARNING_CODE_SENSOR_FAULT_DETECTED,
    WARNING_CODE_SENSOR_FAULT_INPUT_INVALID,
)
from ngv.domain.types import StateResult, SystemState


class StateManager:
    """!
    @brief faultFlag(sensor_fault)와 staleFlag(freshness)로부터 시스템 상태를 재판정한다.

    내부 상태(currentState)는 이 클래스가 단독으로 소유하는 단일 진실 공급원이다
    (ENG-SWE3-001 8장).
    """

    def __init__(self):
        """!
        @brief 중립 초기값(NORMAL)으로 초기화한다.
        """
        self.currentState = SystemState.NORMAL

    def evaluate(self, freshnessResult, sensorFaultField, ignitionOnField, nowS):
        """!
        @brief 결정표 K(FAULT>OFF>DEGRADED>NORMAL)에 따라 상태를 재판정한다.

        @param freshnessResult FreshnessResult — IU-0002.evaluate()의 반환값
        @param sensorFaultField FieldValidationResult[bool] — IU-0001에서 fail-safe 대체가 적용된 값
        @param ignitionOnField FieldValidationResult[bool] — IU-0001 검증 결과(Phase3 신규 파라미터)
        @param nowS float — 현재 평가주기 시각(초, 이번 계약에서는 참고용)
        @return StateResult{state, changedToFault, warningReasonCode}
        @exception ValueError sensorFaultField.value가 None이거나 ignitionOnField가 None이면
                (상위 계약 위반) 발생
        """
        del nowS  # 이번 판정 알고리즘 자체는 nowS를 사용하지 않는다(6.13절 알고리즘).
        if sensorFaultField.value is None:
            raise ValueError("IU-0003: sensorFaultField.value must not be None")
        if ignitionOnField is None:
            raise ValueError("IU-0003: ignitionOnField must not be None")

        newState = self.decideState(freshnessResult, sensorFaultField, ignitionOnField)
        changedToFault = newState == SystemState.FAULT and self.currentState != SystemState.FAULT
        warningReasonCode = self.decideWarningReasonCode(newState, sensorFaultField)

        self.currentState = newState
        return StateResult(
            state=newState, changedToFault=changedToFault, warningReasonCode=warningReasonCode
        )

    @staticmethod
    def decideState(freshnessResult, sensorFaultField, ignitionOnField):
        """!
        @brief 결정표 K의 4개 행을 순서대로 평가해 상태 하나를 고른다(6.13절 알고리즘).

        @param freshnessResult FreshnessResult
        @param sensorFaultField FieldValidationResult[bool]
        @param ignitionOnField FieldValidationResult[bool]
        @return SystemState — FAULT/OFF/DEGRADED/NORMAL 중 하나
        """
        faultFlag = sensorFaultField.value is True
        ignitionOffFlag = ignitionOnField.valid is True and ignitionOnField.value is False
        staleFlag = freshnessResult.stale is True

        if faultFlag:
            return SystemState.FAULT
        if ignitionOffFlag:
            return SystemState.OFF
        if staleFlag:
            return SystemState.DEGRADED
        return SystemState.NORMAL

    @staticmethod
    def decideWarningReasonCode(newState, sensorFaultField):
        """!
        @brief 판정된 상태에 대응하는 경고코드를 고른다(FAULT/OFF만 경고코드를 가진다).

        @param newState SystemState — decideState()의 반환값
        @param sensorFaultField FieldValidationResult[bool]
        @return Optional[str] — FAULT/OFF가 아니면 None
        """
        if newState == SystemState.FAULT:
            return (
                WARNING_CODE_SENSOR_FAULT_DETECTED
                if sensorFaultField.valid
                else WARNING_CODE_SENSOR_FAULT_INPUT_INVALID
            )
        if newState == SystemState.OFF:
            return WARNING_CODE_IGNITION_OFF
        return None

    def reset(self):
        """!
        @brief 내부 상태를 중립 초기값(NORMAL)으로 초기화한다.
        @return None
        """
        self.currentState = SystemState.NORMAL
