"""!
@file test_state_manager.py
@brief IU-0003(ARC-0003 상태 관리자) 함수 계약 검증(ENG-SWE3-001 5장/6.4절/7장 결정표A, SWR-013(a)/SWR-021(b)).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.domain.constants import (
    WARNING_CODE_SENSOR_FAULT_DETECTED,
    WARNING_CODE_SENSOR_FAULT_INPUT_INVALID,
)
from ngv.domain.types import FieldValidationResult, FreshnessResult, SystemState
from ngv.core.state_manager import StateManager


def freshness(stale):
    """테스트 헬퍼 — 주어진 stale 값을 가진 FreshnessResult를 만든다."""
    return FreshnessResult(stale=stale, elapsedS=0.0, detectedAtS=0.0)


def sensorFault(value, valid=True):
    """테스트 헬퍼 — sensorFaultField(FieldValidationResult[bool])를 만든다."""
    return FieldValidationResult(value=value, valid=valid, rawValue=value)


class TestStateManagerEvaluate(unittest.TestCase):
    """IU-0003.evaluate() 계약 검증(결정표 A)."""

    def testNormalWhenNoFaultAndNotStale(self):
        """!
        @brief faultFlag=False, staleFlag=False이면 NORMAL을 반환한다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 A 행(False, False)
        @case Positive — 정상 입력에서의 기대 상태
        @breaks NORMAL 조건을 잘못 판정해 DEGRADED/FAULT를 반환하는 회귀
        """
        manager = StateManager()
        result = manager.evaluate(freshness(False), sensorFault(False), 1.0)

        self.assertEqual(result.state, SystemState.NORMAL)
        self.assertIsNone(result.warningReasonCode)

    def testDegradedWhenStaleOnly(self):
        """!
        @brief faultFlag=False, staleFlag=True이면 DEGRADED를 반환한다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 A 행(False, True)
        @case Positive — SWR-013(a) freshness 초과 시 DEGRADED 전이 요구를 검증
        @breaks staleFlag=True인데도 NORMAL로 남는 회귀
        """
        manager = StateManager()
        result = manager.evaluate(freshness(True), sensorFault(False), 1.0)

        self.assertEqual(result.state, SystemState.DEGRADED)
        self.assertIsNone(result.warningReasonCode)

    def testFaultTakesPriorityOverStale(self):
        """!
        @brief faultFlag=True, staleFlag=True이면 staleFlag와 무관하게 FAULT가 우선한다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 A 행(True, True), 충돌 해결 규칙
        @case Negative — 두 이상 신호 동시 이상에서 방어적(가장 보수적) 상태 우선순위를 검증
        @breaks FAULT 우선 규칙이 깨져 DEGRADED가 반환되는 회귀(SWR-021(b) 위반)
        """
        manager = StateManager()
        result = manager.evaluate(freshness(True), sensorFault(True), 1.0)

        self.assertEqual(result.state, SystemState.FAULT)
        self.assertEqual(result.warningReasonCode, WARNING_CODE_SENSOR_FAULT_DETECTED)

    def testFaultWhenSensorFaultOnly(self):
        """!
        @brief faultFlag=True, staleFlag=False이면 FAULT를 반환한다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 A 행(True, False)
        @case Positive — SWR-021(b) sensor_fault 단독 신호로도 FAULT 전이가 발생하는지 검증
        @breaks sensor_fault만 True인데 FAULT로 전이하지 않는 회귀
        """
        manager = StateManager()
        result = manager.evaluate(freshness(False), sensorFault(True), 1.0)

        self.assertEqual(result.state, SystemState.FAULT)
        self.assertEqual(result.warningReasonCode, WARNING_CODE_SENSOR_FAULT_DETECTED)

    def testFaultWarningCodeDistinguishesInputInvalid(self):
        """!
        @brief sensor_fault 필드 자체가 INVALID(valid=False)였던 경우 별도 경고코드를 사용한다.
        @technique 동등분할(Equivalence Partitioning) — sensorFaultField.valid 값에 따른 코드 분기
        @case Negative — 입력 자체 무효 상태의 진단 구분 요구(10장)를 검증
        @breaks INPUT_INVALID 경로에서도 일반 SENSOR_FAULT_DETECTED 코드를 반환하는 회귀
        """
        manager = StateManager()
        result = manager.evaluate(freshness(False), sensorFault(True, valid=False), 1.0)

        self.assertEqual(result.state, SystemState.FAULT)
        self.assertEqual(result.warningReasonCode, WARNING_CODE_SENSOR_FAULT_INPUT_INVALID)

    def testChangedToFaultTrueOnlyOnTransition(self):
        """!
        @brief 직전 상태가 FAULT가 아니었을 때만 changedToFault=True가 된다.
        @technique 상태전이 테스트(State Transition Testing) — NORMAL -> FAULT -> FAULT 연속 호출
        @case Positive — changedToFault가 "전이 시점"만 표시하는지 검증
        @breaks 이미 FAULT인 상태에서도 매번 changedToFault=True를 반환하는 회귀
        """
        manager = StateManager()
        first = manager.evaluate(freshness(False), sensorFault(True), 1.0)
        second = manager.evaluate(freshness(False), sensorFault(True), 1.05)

        self.assertTrue(first.changedToFault)
        self.assertFalse(second.changedToFault)

    def testRaisesValueErrorWhenSensorFaultValueIsNone(self):
        """!
        @brief sensorFaultField.value가 None이면 상위 계약 위반으로 ValueError를 던진다.
        @technique 오류추측(Error Guessing) — IU-0001 사후조건 위반이라는 방어적 예외 경로
        @case Negative — 계약 위반 검출(방어적 구현) 요구를 검증
        @breaks None 값을 그대로 통과시켜 예외 없이 잘못된 상태를 산출하는 회귀
        """
        manager = StateManager()
        invalidSensorFault = FieldValidationResult(value=None, valid=False, rawValue=None)

        with self.assertRaises(ValueError):
            manager.evaluate(freshness(False), invalidSensorFault, 1.0)


class TestStateManagerReset(unittest.TestCase):
    """IU-0003.reset() 계약 검증."""

    def testResetReturnsToNormal(self):
        """!
        @brief reset() 이후 내부 상태는 NORMAL로 복귀한다.
        @technique 상태전이 테스트(State Transition Testing) — FAULT -> reset -> NORMAL
        @case Positive — 8장 근거대로 중립 초기값 복귀를 검증
        @breaks reset() 이후에도 이전 FAULT 상태가 유지되는 회귀
        """
        manager = StateManager()
        manager.evaluate(freshness(False), sensorFault(True), 1.0)

        manager.reset()
        result = manager.evaluate(freshness(False), sensorFault(True), 1.0)

        self.assertTrue(result.changedToFault)


if __name__ == "__main__":
    unittest.main()
