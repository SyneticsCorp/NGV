"""!
@file test_state_manager.py
@brief IU-0003(ARC-0003 상태 관리자) 함수 계약 검증(ENG-SWE3-001 5.11절/6.13절/7장 결정표K,
       SWR-013(a)/SWR-021(b)/SWR-020(a)/(b)).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.domain.constants import (
    WARNING_CODE_IGNITION_OFF,
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


def ignitionOn(value=True, valid=True):
    """테스트 헬퍼 — ignitionOnField(FieldValidationResult[bool])를 만든다(기본값: 점화 ON/유효)."""
    return FieldValidationResult(value=value, valid=valid, rawValue=value)


class TestStateManagerEvaluate(unittest.TestCase):
    """IU-0003.evaluate() 계약 검증(결정표 A, Phase1/2 회귀 — ignitionOnField는 기본 ON/유효로 고정)."""

    def testNormalWhenNoFaultAndNotStale(self):
        """!
        @brief faultFlag=False, staleFlag=False, ignitionOn=True이면 NORMAL을 반환한다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 K 행(False, ON, False)
        @case Positive — 정상 입력에서의 기대 상태
        @breaks NORMAL 조건을 잘못 판정해 DEGRADED/FAULT/OFF를 반환하는 회귀
        """
        manager = StateManager()
        result = manager.evaluate(freshness(False), sensorFault(False), ignitionOn(), 1.0)

        self.assertEqual(result.state, SystemState.NORMAL)
        self.assertIsNone(result.warningReasonCode)

    def testDegradedWhenStaleOnly(self):
        """!
        @brief faultFlag=False, staleFlag=True, ignitionOn=True이면 DEGRADED를 반환한다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 K 행(False, ON, True)
        @case Positive — SWR-013(a) freshness 초과 시 DEGRADED 전이 요구를 검증
        @breaks staleFlag=True인데도 NORMAL로 남는 회귀
        """
        manager = StateManager()
        result = manager.evaluate(freshness(True), sensorFault(False), ignitionOn(), 1.0)

        self.assertEqual(result.state, SystemState.DEGRADED)
        self.assertIsNone(result.warningReasonCode)

    def testFaultTakesPriorityOverStale(self):
        """!
        @brief faultFlag=True, staleFlag=True이면 staleFlag와 무관하게 FAULT가 우선한다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 K 행(True, ON, True), 충돌 해결 규칙
        @case Negative — 두 이상 신호 동시 이상에서 방어적(가장 보수적) 상태 우선순위를 검증
        @breaks FAULT 우선 규칙이 깨져 DEGRADED가 반환되는 회귀(SWR-021(b) 위반)
        """
        manager = StateManager()
        result = manager.evaluate(freshness(True), sensorFault(True), ignitionOn(), 1.0)

        self.assertEqual(result.state, SystemState.FAULT)
        self.assertEqual(result.warningReasonCode, WARNING_CODE_SENSOR_FAULT_DETECTED)

    def testFaultWhenSensorFaultOnly(self):
        """!
        @brief faultFlag=True, staleFlag=False이면 FAULT를 반환한다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 K 행(True, ON, False)
        @case Positive — SWR-021(b) sensor_fault 단독 신호로도 FAULT 전이가 발생하는지 검증
        @breaks sensor_fault만 True인데 FAULT로 전이하지 않는 회귀
        """
        manager = StateManager()
        result = manager.evaluate(freshness(False), sensorFault(True), ignitionOn(), 1.0)

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
        result = manager.evaluate(freshness(False), sensorFault(True, valid=False), ignitionOn(), 1.0)

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
        first = manager.evaluate(freshness(False), sensorFault(True), ignitionOn(), 1.0)
        second = manager.evaluate(freshness(False), sensorFault(True), ignitionOn(), 1.05)

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
            manager.evaluate(freshness(False), invalidSensorFault, ignitionOn(), 1.0)


class TestStateManagerOffState(unittest.TestCase):
    """IU-0003.evaluate() OFF 판정 계약 검증(Phase3 신규, 5.11절/6.13절/7장 결정표K, SWR-020)."""

    def testOffWhenIgnitionValidFalseAndNoFaultRegardlessOfStale(self):
        """!
        @brief faultFlag=False, ignitionOn.valid=True/value=False이면 staleFlag와 무관하게 OFF를 반환한다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 K 행(False, OFF, 무관)
        @case Positive — SWR-020(a) ignition_on=FALSE 전이 시 OFF 판정 요구를 검증
        @breaks ignition_on=FALSE인데도 DEGRADED/NORMAL로 오판정하는 회귀
        """
        manager = StateManager()
        result = manager.evaluate(freshness(False), sensorFault(False), ignitionOn(value=False), 1.0)

        self.assertEqual(result.state, SystemState.OFF)
        self.assertEqual(result.warningReasonCode, WARNING_CODE_IGNITION_OFF)

    def testFaultTakesPriorityOverOff(self):
        """!
        @brief faultFlag=True, ignitionOn=False가 동시 성립하면 FAULT가 OFF보다 우선한다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 K, FAULT>OFF 우선순위, 충돌 해결 규칙
        @case Negative — 4상태 우선순위(FAULT>OFF>DEGRADED>NORMAL)의 최상위 규칙을 검증
        @breaks FAULT 우선 규칙이 깨져 OFF가 반환되는 회귀
        """
        manager = StateManager()
        result = manager.evaluate(freshness(False), sensorFault(True), ignitionOn(value=False), 1.0)

        self.assertEqual(result.state, SystemState.FAULT)
        self.assertEqual(result.warningReasonCode, WARNING_CODE_SENSOR_FAULT_DETECTED)

    def testOffTakesPriorityOverDegraded(self):
        """!
        @brief ignitionOn=False, staleFlag=True가 동시 성립하면 OFF가 DEGRADED보다 우선한다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 K, OFF>DEGRADED 우선순위
        @case Negative — 4상태 우선순위 중 두 번째 규칙(OFF가 DEGRADED보다 우선)을 검증
        @breaks OFF 우선 규칙이 깨져 DEGRADED가 반환되는 회귀
        """
        manager = StateManager()
        result = manager.evaluate(freshness(True), sensorFault(False), ignitionOn(value=False), 1.0)

        self.assertEqual(result.state, SystemState.OFF)
        self.assertEqual(result.warningReasonCode, WARNING_CODE_IGNITION_OFF)

    def testIgnitionInvalidFieldFallsBackToNormalNotOff(self):
        """!
        @brief ignitionOnField.valid=False(형식 오류)이면 OFF를 판정하지 않고 freshness/NORMAL
               경로로 대체한다(8.8절 SW 설계 재량 확정 사항, 회귀 방지 핵심 테스트).
        @technique 오류추측(Error Guessing) — 8.8절이 확정한 미판정 규칙의 회귀 검출
        @case Negative — ignitionOnField.valid=False가 OFF를 잘못 트리거하지 않는지 검증
        @breaks 형식 오류 필드(valid=False)를 "OFF"로 잘못 해석하는 회귀(8.8절 위반)
        """
        manager = StateManager()
        result = manager.evaluate(freshness(False), sensorFault(False), ignitionOn(value=False, valid=False), 1.0)

        self.assertEqual(result.state, SystemState.NORMAL)
        self.assertIsNone(result.warningReasonCode)

    def testIgnitionInvalidFieldFallsBackToDegradedNotOffWhenStale(self):
        """!
        @brief ignitionOnField.valid=False이고 staleFlag=True이면 OFF가 아닌 DEGRADED로 대체된다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 K 3행(valid=False, stale=True)
        @case Negative — 8.8절 대체 경로가 freshness 판정과 정확히 이어지는지 검증
        @breaks valid=False 필드가 OFF로 오판정되거나 DEGRADED 대신 NORMAL로 잘못 대체되는 회귀
        """
        manager = StateManager()
        result = manager.evaluate(freshness(True), sensorFault(False), ignitionOn(value=False, valid=False), 1.0)

        self.assertEqual(result.state, SystemState.DEGRADED)

    def testRaisesValueErrorWhenIgnitionOnFieldIsNone(self):
        """!
        @brief ignitionOnField가 None이면 상위 계약 위반으로 ValueError를 던진다.
        @technique 오류추측(Error Guessing) — IU-0010/0011/0013과 동일한 방어적 예외 패턴
        @case Negative — 신규 파라미터의 사전조건(not None) 위반 방어를 검증
        @breaks None 값을 그대로 통과시켜 AttributeError 등으로 이어지는 회귀
        """
        manager = StateManager()

        with self.assertRaises(ValueError):
            manager.evaluate(freshness(False), sensorFault(False), None, 1.0)


class TestStateManagerFourStateCombinations(unittest.TestCase):
    """IU-0003.evaluate() FAULT/OFF/DEGRADED/NORMAL 4상태 전 조합 계약 검증(11.4절 필수 커버리지)."""

    def testAllEightSensorFaultIgnitionStaleCombinationsMatchDecisionTableK(self):
        """!
        @brief (faultFlag, ignitionOn valid/value, staleFlag) 2x2x2=8개 조합이 모두 결정표 K와
               정확히 일치하는 상태를 반환한다(FAULT>OFF>DEGRADED>NORMAL 우선순위 전수 검증).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 K 전 조합(오류 값 포함) 전수 검증
        @case Positive — 4상태 판정 우선순위가 모든 입력 조합에서 일관되는지 검증
        @breaks 특정 조합 하나에서만 우선순위가 어긋나는 회귀(부분 리팩터링 실수 등)
        """
        cases = [
            (False, True, True, False, SystemState.NORMAL),
            (False, True, True, True, SystemState.DEGRADED),
            (False, False, True, False, SystemState.NORMAL),
            (False, False, True, True, SystemState.DEGRADED),
            (False, True, False, False, SystemState.OFF),
            (False, True, False, True, SystemState.OFF),
            (True, True, True, False, SystemState.FAULT),
            (True, True, False, True, SystemState.FAULT),
        ]
        for faultFlag, ignitionValid, ignitionValue, staleFlag, expectedState in cases:
            with self.subTest(
                faultFlag=faultFlag, ignitionValid=ignitionValid, ignitionValue=ignitionValue, staleFlag=staleFlag
            ):
                manager = StateManager()
                result = manager.evaluate(
                    freshness(staleFlag),
                    sensorFault(faultFlag),
                    ignitionOn(value=ignitionValue, valid=ignitionValid),
                    1.0,
                )
                self.assertEqual(result.state, expectedState)


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
        manager.evaluate(freshness(False), sensorFault(True), ignitionOn(), 1.0)

        manager.reset()
        result = manager.evaluate(freshness(False), sensorFault(True), ignitionOn(), 1.0)

        self.assertTrue(result.changedToFault)


if __name__ == "__main__":
    unittest.main()
