"""!
@file state_manager.py
@brief IU-0003(ARC-0003 상태 관리자) — NORMAL/DEGRADED/FAULT 상태 판정(FAULT 우선).

@par 관련 항목
- 요구사항: SWR-013(a), SWR-021(b)
- 상세설계: ENG-SWE3-001 5장/6.4절/7장 결정표 A
"""

from ngv.domain.constants import (
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

    def evaluate(self, freshnessResult, sensorFaultField, nowS):
        """!
        @brief 결정표 A(FAULT 우선)에 따라 상태를 재판정한다.

        @param freshnessResult FreshnessResult — IU-0002.evaluate()의 반환값
        @param sensorFaultField FieldValidationResult[bool] — IU-0001에서 fail-safe 대체가 적용된 값
        @param nowS float — 현재 평가주기 시각(초, 이번 계약에서는 참고용)
        @return StateResult{state, changedToFault, warningReasonCode}
        @exception ValueError sensorFaultField.value가 None이면(상위 계약 위반) 발생
        """
        del nowS  # 이번 판정 알고리즘 자체는 nowS를 사용하지 않는다(6.4절 알고리즘).
        if sensorFaultField.value is None:
            raise ValueError("IU-0003: sensorFaultField.value must not be None")

        faultFlag = sensorFaultField.value is True
        staleFlag = freshnessResult.stale is True

        if faultFlag:
            newState = SystemState.FAULT
        elif staleFlag:
            newState = SystemState.DEGRADED
        else:
            newState = SystemState.NORMAL

        changedToFault = newState == SystemState.FAULT and self.currentState != SystemState.FAULT

        if newState == SystemState.FAULT:
            warningReasonCode = (
                WARNING_CODE_SENSOR_FAULT_DETECTED
                if sensorFaultField.valid
                else WARNING_CODE_SENSOR_FAULT_INPUT_INVALID
            )
        else:
            warningReasonCode = None

        self.currentState = newState
        return StateResult(
            state=newState, changedToFault=changedToFault, warningReasonCode=warningReasonCode
        )

    def reset(self):
        """!
        @brief 내부 상태를 중립 초기값(NORMAL)으로 초기화한다.
        @return None
        """
        self.currentState = SystemState.NORMAL
