"""!
@file test_it_step2_state_manager.py
@brief 통합 2단계 — ARC-0003(상태 관리자), IF-0007 인터페이스 계약 검증.

테스트 베이시스: ENG-SWE2-001 6.1절(IF-0007), 8장(상태 전이, FAULT>DEGRADED 우선),
11장 순서표 2행("단위시험 하네스로 직접 호출, 합성 FreshnessResult 주입 — ARC-0002 실물 불필요").
"""

import unittest

from tests_integration.it_helpers import (
    SystemState,
    buildFreshnessResult,
    invalidField,
    validField,
)
from ngv.core.state_manager import StateManager


def ignitionOnField():
    """테스트 헬퍼 — 정상 ON/유효 ignitionOnField를 만든다(Phase1/2 회귀 케이스의 기본값)."""
    return validField(True)


class TestIT0005NormalDecision(unittest.TestCase):
    """IT-0005 — Trace: IF-0007 / SWR-013(a)"""

    def testStaleFalseFaultFalseYieldsNormal(self):
        """!
        @brief stale=False, fault=False 조합은 NORMAL을 반환해야 한다(결정표 A).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 A 행 1
        @case Positive
        @breaks 정상 조합에서 DEGRADED/FAULT가 반환되는 회귀
        """
        manager = StateManager()
        freshness = buildFreshnessResult(stale=False, elapsedS=0.050, detectedAtS=1.000)

        result = manager.evaluate(freshness, validField(False), ignitionOnField(), 1.000)

        self.assertEqual(result.state, SystemState.NORMAL)
        self.assertIsNone(result.warningReasonCode)


class TestIT0006DegradedDecision(unittest.TestCase):
    """IT-0006 — Trace: IF-0007 / SWR-013(a)"""

    def testStaleTrueFaultFalseYieldsDegraded(self):
        """!
        @brief stale=True, fault=False 조합은 DEGRADED를 반환해야 한다(결정표 A).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 A 행 2
        @case Positive
        @breaks stale만 발생했는데도 FAULT나 NORMAL로 오판정되는 회귀
        """
        manager = StateManager()
        freshness = buildFreshnessResult(stale=True, elapsedS=0.250, detectedAtS=1.000)

        result = manager.evaluate(freshness, validField(False), ignitionOnField(), 1.000)

        self.assertEqual(result.state, SystemState.DEGRADED)
        self.assertIsNone(result.warningReasonCode)


class TestIT0007FaultPriorityOverDegraded(unittest.TestCase):
    """IT-0007 — Trace: IF-0007 / SWR-021(b), 8장 FAULT 우선 규칙"""

    def testStaleTrueFaultTrueYieldsFaultNotDegraded(self):
        """!
        @brief stale=True와 fault=True가 동시 성립하면 FAULT가 DEGRADED보다 우선한다(8장).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 A 행 3(동시 성립)
        @case Positive — 8장에서 명시한 "FAULT 우선" 설계 결정이 코드에 그대로 구현됐는지 검증
        @breaks 두 조건 동시 성립 시 DEGRADED가 반환되는 회귀(안전 우선순위 위반)
        """
        manager = StateManager()
        freshness = buildFreshnessResult(stale=True, elapsedS=0.300, detectedAtS=1.000)

        result = manager.evaluate(freshness, validField(True), ignitionOnField(), 1.000)

        self.assertEqual(result.state, SystemState.FAULT)
        self.assertEqual(result.warningReasonCode, "SENSOR_FAULT_DETECTED")


class TestIT0008FaultDetectedWarningCode(unittest.TestCase):
    """IT-0008 — Trace: IF-0007 / SWR-021(b)"""

    def testValidSensorFaultTrueYieldsDetectedWarningCode(self):
        """!
        @brief 정상 관측된 sensor_fault=True는 SENSOR_FAULT_DETECTED 경고코드를 산출해야 한다.
        @technique 동등분할(Equivalence Partitioning) — sensorFaultField.valid=True 클래스
        @case Positive
        @breaks 정상 관측 fault에서도 INPUT_INVALID 계열 경고코드가 나오는 회귀
        """
        manager = StateManager()
        freshness = buildFreshnessResult(stale=False, elapsedS=0.010, detectedAtS=1.000)

        result = manager.evaluate(freshness, validField(True), ignitionOnField(), 1.000)

        self.assertEqual(result.state, SystemState.FAULT)
        self.assertEqual(result.warningReasonCode, "SENSOR_FAULT_DETECTED")
        self.assertTrue(result.changedToFault)


class TestIT0009FailSafeSubstitutedSensorFaultWarningCode(unittest.TestCase):
    """IT-0009 — Trace: IF-0007 / SWR-013(b), IF-0002 오류 계약과의 연계(확인 필요 항목 해소)"""

    def testFailSafeSubstitutedInvalidSensorFaultYieldsInputInvalidWarningCode(self):
        """!
        @brief IF-0001/IF-0002에서 sensor_fault 자체가 INVALID여서 fail-safe 대체(True)가 적용된
               경우(valid=False, value=True), StateManager는 FAULT로 판정하되 경고코드를
               SENSOR_FAULT_INPUT_INVALID로 구분해야 한다. ENG-SWE2-001 4장/6.1절이
               "sensorFaultValid=False 처리 규칙 확인 필요"로 남긴 항목이 상세설계/구현
               단계에서 이렇게 해소되었음을 통합시험으로 확인한다.
        @technique 오류주입(Error Guessing) + 결정테이블 테스트 — 무효 입력 fail-safe 대체 클래스
        @case Negative — 입력 자체 오류와 정상 관측 fault를 경고코드로 구분하는지 검증
        @breaks fail-safe 대체 케이스가 SENSOR_FAULT_DETECTED로 혼동되는 회귀(원인 구분 불가)
        """
        manager = StateManager()
        freshness = buildFreshnessResult(stale=False, elapsedS=0.010, detectedAtS=1.000)
        failSafeField = invalidField(rawValue=None, errorReason="MISSING", substituteValue=True)

        result = manager.evaluate(freshness, failSafeField, ignitionOnField(), 1.000)

        self.assertEqual(result.state, SystemState.FAULT)
        self.assertEqual(result.warningReasonCode, "SENSOR_FAULT_INPUT_INVALID")


class TestIT0010SensorFaultValueNoneFaultInjection(unittest.TestCase):
    """IT-0010 — Trace: IF-0007, ASIL B 오류 주입"""

    def testSensorFaultFieldValueNoneRaisesValueError(self):
        """!
        @brief IF-0007 사전조건(sensorFaultField.value is not None)을 위반한 호출은 ValueError로
               방어되어야 한다(ASIL B 경로 오류 주입 — 상위 계약 위반 감지).
        @technique 오류주입(Fault Injection Test) — 계약 위반 입력(None) 직접 주입
        @case Negative
        @breaks 사전조건 위반 시 예외 없이 조용히 오판정(state=NORMAL 등)이 나오는 회귀
        """
        manager = StateManager()
        freshness = buildFreshnessResult(stale=False, elapsedS=0.010, detectedAtS=1.000)
        noneValueField = invalidField(rawValue=None, errorReason="MISSING", substituteValue=None)

        with self.assertRaises(ValueError):
            manager.evaluate(freshness, noneValueField, ignitionOnField(), 1.000)


class TestIT0011FaultThenReturnsToNormalAcrossCycles(unittest.TestCase):
    """IT-0011 — Trace: IF-0007, 8장 상태 전이"""

    def testChangedToFaultOnlyTrueOnFirstFaultCycle(self):
        """!
        @brief 두 평가주기 연속 fault=True이면 첫 주기만 changedToFault=True, 두 번째는 False여야
               한다(SWR-021b "TRUE로 전이된 첫 평가주기" 요건).
        @technique 상태전이 테스트(State Transition Testing) — NORMAL -> FAULT -> FAULT(유지)
        @case Positive — 상태 전이 자체가 아니라 "전이된 순간"만 changedToFault로 표시되는지 검증
        @breaks 매 주기마다 changedToFault=True가 반복 발생하는 회귀(경고 중복 발행 유발)
        """
        manager = StateManager()
        freshness = buildFreshnessResult(stale=False, elapsedS=0.010, detectedAtS=1.000)

        first = manager.evaluate(freshness, validField(True), ignitionOnField(), 1.000)
        second = manager.evaluate(freshness, validField(True), ignitionOnField(), 1.050)

        self.assertTrue(first.changedToFault)
        self.assertFalse(second.changedToFault)
        self.assertEqual(second.state, SystemState.FAULT)


if __name__ == "__main__":
    unittest.main()
