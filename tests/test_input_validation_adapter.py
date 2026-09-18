"""!
@file test_input_validation_adapter.py
@brief IU-0001(ARC-0001 입력 검증 어댑터) 함수 계약 검증(ENG-SWE3-001 5장/6.2절/7장 결정표C, SWR-013(b)).
"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.domain.types import RawCycleInput, SystemState
from ngv.adapters.input_validation_adapter import InputValidationAdapter
from ngv.adapters.decision_logger_stub import DecisionLoggerStub
from ngv.adapters.notification_adapter import NotificationAdapter
from ngv.adapters.output_actuator_adapter import OutputActuatorAdapter
from ngv.core.command_arbiter import CommandArbiter
from ngv.core.freshness_monitor import FreshnessMonitor
from ngv.core.output_hold_actuator import OutputHoldActuator
from ngv.core.state_manager import StateManager
from ngv.app.safety_kernel_orchestrator import SafetyKernelOrchestrator


class TestValidateTimestampField(unittest.TestCase):
    """IU-0001.validateTimestampField() 계약 검증."""

    def testAcceptsNonNegativeFiniteValue(self):
        """!
        @brief 0.0 이상의 유한 수치는 valid=True, value=float(rawValue)로 반환된다.
        @technique 동등분할(Equivalence Partitioning) — 유효 구간의 대표값
        @case Positive — 정상 시각값 수용 경로를 검증
        @breaks 유효한 수치를 valid=False로 거절하는 회귀
        """
        result = InputValidationAdapter.validateTimestampField(12.345)

        self.assertTrue(result.valid)
        self.assertEqual(result.value, 12.345)

    def testAcceptsZeroAsBoundary(self):
        """!
        @brief 0.0(하한 경계값)은 유효하다("0.0 이상").
        @technique 경계값분석(Boundary Value Analysis) — 하한 경계(0.0)
        @case Positive — 경계값 자체가 유효 입력임을 검증
        @breaks 하한 비교를 >0으로 잘못 구현해 0.0을 거절하는 회귀
        """
        result = InputValidationAdapter.validateTimestampField(0.0)

        self.assertTrue(result.valid)
        self.assertEqual(result.value, 0.0)

    def testRejectsNoneAsMissing(self):
        """!
        @brief None은 valid=False, errorReason="MISSING"으로 거절된다.
        @technique 동등분할(Equivalence Partitioning) — 누락 입력 클래스의 대표값
        @case Negative — SWR-013(b) 형식 오류(누락) 거절 요구를 검증
        @breaks None을 valid=True로 잘못 통과시키는 회귀
        """
        result = InputValidationAdapter.validateTimestampField(None)

        self.assertFalse(result.valid)
        self.assertIsNone(result.value)
        self.assertEqual(result.errorReason, "MISSING")

    def testRejectsNonNumericStringAsTypeError(self):
        """!
        @brief 수치로 변환 불가능한 문자열은 valid=False, errorReason="TYPE_ERROR"로 거절된다.
        @technique 동등분할(Equivalence Partitioning) — 타입 오류 클래스의 대표값
        @case Negative — SWR-013(b) 형식 오류(타입 불일치) 거절 요구를 검증
        @breaks 문자열 입력에서 예외가 외부로 전파되거나 valid=True가 되는 회귀
        """
        result = InputValidationAdapter.validateTimestampField("not-a-number")

        self.assertFalse(result.valid)
        self.assertEqual(result.errorReason, "TYPE_ERROR")

    def testRejectsNegativeValueAsOutOfRange(self):
        """!
        @brief 음수는 valid=False, errorReason="OUT_OF_RANGE"로 거절된다.
        @technique 경계값분석(Boundary Value Analysis) — 하한 경계 바로 아래(-0.001)
        @case Negative — 시각값의 물리적 음수 불가 조건을 검증
        @breaks 음수를 valid=True로 통과시키는 회귀
        """
        result = InputValidationAdapter.validateTimestampField(-0.001)

        self.assertFalse(result.valid)
        self.assertEqual(result.errorReason, "OUT_OF_RANGE")

    def testRejectsNanAndInfinityAsOutOfRange(self):
        """!
        @brief NaN/Infinity는 valid=False, errorReason="OUT_OF_RANGE"로 거절된다.
        @technique 오류추측(Error Guessing) — 계측·직렬화 오류의 전형적 대표값(NaN, Infinity)
        @case Negative — 비유한 값 거절 요구를 검증
        @breaks NaN/Infinity를 유효한 시각값으로 통과시키는 회귀
        """
        nanResult = InputValidationAdapter.validateTimestampField(math.nan)
        infResult = InputValidationAdapter.validateTimestampField(math.inf)

        self.assertFalse(nanResult.valid)
        self.assertEqual(nanResult.errorReason, "OUT_OF_RANGE")
        self.assertFalse(infResult.valid)
        self.assertEqual(infResult.errorReason, "OUT_OF_RANGE")


class TestValidateBooleanField(unittest.TestCase):
    """IU-0001.validateBooleanField() 계약 검증."""

    def testAcceptsStrictBoolTrue(self):
        """!
        @brief 정확히 bool 타입(True)이면 valid=True, value=True를 반환한다.
        @technique 동등분할(Equivalence Partitioning) — 유효 bool 클래스의 대표값
        @case Positive — 정상 boolean 입력 수용 경로를 검증
        @breaks 유효한 bool을 valid=False로 거절하는 회귀
        """
        result = InputValidationAdapter.validateBooleanField(True, "ignition_on")

        self.assertTrue(result.valid)
        self.assertTrue(result.value)

    def testRejectsIntegerOneAsTypeErrorNotTruthy(self):
        """!
        @brief 1(int)은 bool이 아니므로 truthy 암묵적 변환 없이 valid=False, "TYPE_ERROR"로 거절된다.
        @technique 오류추측(Error Guessing) — 1/0, "True" 등 흔한 암묵적 타입 변환 함정
        @case Negative — 엄격한 타입 검사(SWR-013(b) 관대하지 않은 해석) 요구를 검증
        @breaks isinstance 대신 truthy 비교를 사용해 1을 True로 암묵 변환하는 회귀
        """
        result = InputValidationAdapter.validateBooleanField(1, "ignition_on")

        self.assertFalse(result.valid)
        self.assertEqual(result.errorReason, "TYPE_ERROR")

    def testRejectsNoneAsMissing(self):
        """!
        @brief None은 valid=False, errorReason="MISSING"으로 거절된다.
        @technique 동등분할(Equivalence Partitioning) — 누락 입력 클래스의 대표값
        @case Negative — 누락 필드 거절 요구를 검증
        @breaks None을 TYPE_ERROR로 잘못 분류하는 회귀
        """
        result = InputValidationAdapter.validateBooleanField(None, "sensor_fault")

        self.assertFalse(result.valid)
        self.assertEqual(result.errorReason, "MISSING")


class TestApplySensorFaultFailSafe(unittest.TestCase):
    """IU-0001.applySensorFaultFailSafe() 계약 검증."""

    def testPassesThroughValidResultUnchanged(self):
        """!
        @brief valid=True인 결과는 그대로 반환된다(대체 없음).
        @technique 동등분할(Equivalence Partitioning) — 유효 입력 클래스
        @case Positive — 정상 값에는 fail-safe 대체가 적용되지 않는지 검증
        @breaks 유효한 값도 True로 강제 대체해버리는 회귀
        """
        validResult = InputValidationAdapter.validateBooleanField(False, "sensor_fault")

        result = InputValidationAdapter.applySensorFaultFailSafe(validResult)

        self.assertTrue(result.valid)
        self.assertFalse(result.value)

    def testSubstitutesTrueWhenInvalidKeepingInvalidFlag(self):
        """!
        @brief valid=False인 결과는 value=True로 대체되며 valid=False/errorReason은 유지된다.
        @technique 오류추측(Error Guessing) — sensor_fault 자체 신뢰 불가 상황
        @case Negative — 10장 fail-safe 대체(비관적 해석) 요구를 검증
        @breaks 무효 결과의 value가 None으로 남아 하류 불변조건을 깨는 회귀
        """
        invalidResult = InputValidationAdapter.validateBooleanField(None, "sensor_fault")

        result = InputValidationAdapter.applySensorFaultFailSafe(invalidResult)

        self.assertIsNotNone(result.value)
        self.assertTrue(result.value)
        self.assertFalse(result.valid)
        self.assertEqual(result.errorReason, "MISSING")


class TestNormalizeCycle(unittest.TestCase):
    """IU-0001.normalizeCycle() 계약 검증."""

    def testProducesFullyValidNormalizedInputForValidRawInput(self):
        """!
        @brief 세 필드 모두 유효한 원시 입력은 세 필드 모두 valid=True인 NormalizedSafetyInput을 생성한다.
        @technique 유스케이스 테스트(Use Case Testing) — 기본 흐름(정상 원시 입력)
        @case Positive — 6.2절 알고리즘의 정상 경로를 검증
        @breaks 세 필드 검증 함수 중 하나라도 호출되지 않아 valid 여부가 누락되는 회귀
        """
        rawInput = RawCycleInput(rawSourceTimestamp=1.5, rawIgnitionOn=True, rawSensorFault=False)

        result = InputValidationAdapter.normalizeCycle(rawInput, 1.5)

        self.assertTrue(result.sourceTimestampField.valid)
        self.assertTrue(result.ignitionOnField.valid)
        self.assertTrue(result.sensorFaultField.valid)
        self.assertFalse(result.sensorFaultField.value)

    def testSensorFaultFieldValueNeverNoneEvenWhenAllFieldsInvalid(self):
        """!
        @brief 세 필드 모두 무효여도 sensorFaultField.value는 항상 not None이다(불변조건).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 C, 세 필드 동시 형식 오류
        @case Negative — NormalizedSafetyInput 불변조건(4장)을 검증
        @breaks sensorFaultField.value가 None으로 남아 IU-0003 사전조건을 깨는 회귀
        """
        rawInput = RawCycleInput(rawSourceTimestamp=None, rawIgnitionOn=None, rawSensorFault=None)

        result = InputValidationAdapter.normalizeCycle(rawInput, 1.0)

        self.assertFalse(result.sourceTimestampField.valid)
        self.assertFalse(result.ignitionOnField.valid)
        self.assertIsNotNone(result.sensorFaultField.value)
        self.assertTrue(result.sensorFaultField.value)


def buildRealOrchestrator():
    """테스트 헬퍼 — 실제(real) IU-0002~0008 협력 객체로 구성된 오케스트레이터를 만든다."""
    return SafetyKernelOrchestrator(
        freshnessMonitor=FreshnessMonitor(),
        stateManager=StateManager(),
        outputHoldActuator=OutputHoldActuator(),
        commandArbiter=CommandArbiter(),
        outputAdapter=OutputActuatorAdapter(),
        notificationAdapter=NotificationAdapter(),
        decisionLogger=DecisionLoggerStub(),
    )


class TestHandleCycle(unittest.TestCase):
    """IU-0001.handleCycle() 계약 검증(실제 IU-0009 오케스트레이터 연동)."""

    def testCallsOrchestratorExactlyOnceWithNormalizedInput(self):
        """!
        @brief normalizeCycle() 결과를 IU-0009.evaluateCycle()에 정확히 1회 전달하고 반환값을 그대로 돌려준다.
        @technique 유스케이스 테스트(Use Case Testing) — 3장 호출관계(IU-0001 -> IU-0009) 경계 계약
        @case Positive — 진입점 위임 계약(선형 위임)을 실제 오케스트레이터로 종단 검증
        @breaks evaluateCycle()을 0회/2회 호출하거나 원시 입력을 그대로(미정규화) 전달하는 회귀
        """
        orchestrator = buildRealOrchestrator()
        callLog = []
        originalEvaluateCycle = orchestrator.evaluateCycle

        def recordingEvaluateCycle(normalizedInput, nowS):
            callLog.append((normalizedInput, nowS))
            return originalEvaluateCycle(normalizedInput, nowS)

        orchestrator.evaluateCycle = recordingEvaluateCycle
        adapter = InputValidationAdapter(orchestrator)
        rawInput = RawCycleInput(rawSourceTimestamp=2.0, rawIgnitionOn=True, rawSensorFault=False)

        result = adapter.handleCycle(rawInput, 2.0)

        self.assertEqual(len(callLog), 1)
        normalizedInput, nowS = callLog[0]
        self.assertTrue(normalizedInput.sourceTimestampField.valid)
        self.assertEqual(nowS, 2.0)
        self.assertEqual(result.stateResult.state, SystemState.NORMAL)

    def testDoesNotRaiseWhenRawInputFieldsAreAllInvalid(self):
        """!
        @brief 원시 입력 필드가 모두 무효해도 handleCycle()은 예외를 던지지 않는다.
        @technique 오류추측(Error Guessing) — 모든 필드 동시 형식 오류라는 극단적 입력
        @case Negative — 5장 계약 "예외를 던지지 않는다(전면 어댑터의 방어적 계약)"를 실제 오케스트레이터로 검증
        @breaks 무효 입력 조합에서 예외가 외부로 전파되는 회귀
        """
        orchestrator = buildRealOrchestrator()
        adapter = InputValidationAdapter(orchestrator)
        rawInput = RawCycleInput(rawSourceTimestamp="bad", rawIgnitionOn=None, rawSensorFault=None)

        result = adapter.handleCycle(rawInput, 1.0)

        self.assertIsNotNone(result)
        self.assertEqual(result.stateResult.state, SystemState.FAULT)


if __name__ == "__main__":
    unittest.main()
