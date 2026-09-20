"""!
@file test_it_step19_state_manager_off_state.py
@brief 통합 19단계 — ARC-0003(상태 관리자, OFF 상태 추가 — FAULT>OFF>DEGRADED>NORMAL),
       IF-0007 인터페이스 계약 검증(Phase3 갱신).

테스트 베이시스: ENG-SWE2-001 6.1절(IF-0007 확장), 8장("Phase 3 확장 — OFF 상태 추가 및 결정
규칙"), 11장 순서표 19행("단위시험 하네스, ignitionOnField 추가 파라미터 포함 합성 입력").
회귀 범위: 2단계(Phase1 상태판정) — OFF 추가가 기존 FAULT/DEGRADED 판정에 영향 없는지 확인.
ENG-SWE3-001 7장 결정표 K(IU-0003 확장 상태판정)를 그대로 시험벡터 도출에 사용한다.
"""

import unittest

from tests_integration.it_helpers import (
    SystemState,
    buildFreshnessResult,
    invalidField,
    validField,
)
from ngv.core.state_manager import StateManager


class TestIT0117IgnitionOnDoesNotForceOffRegression(unittest.TestCase):
    """IT-0117 — Trace: IF-0007 / SWR-013(a), 회귀(2단계), 결정표 K"""

    def testIgnitionOnValidTrueWithNoOtherConditionYieldsNormal(self):
        """!
        @brief ignitionOnField.valid=True, value=True(정상 ON)이고 stale=False/fault=False이면
               기존과 동일하게 NORMAL을 반환해야 한다(Phase1 회귀 기준선 — OFF 추가가 기존
               NORMAL 판정을 깨지 않는지 확인).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 K 행 4(NORMAL), 회귀
        @case Positive
        @breaks ignition-on 정상 상태에서 OFF/DEGRADED로 오판정되는 회귀
        """
        manager = StateManager()
        freshness = buildFreshnessResult(stale=False, elapsedS=0.010, detectedAtS=1.000)

        result = manager.evaluate(freshness, validField(False), validField(True), 1.000)

        self.assertEqual(result.state, SystemState.NORMAL)
        self.assertIsNone(result.warningReasonCode)


class TestIT0118IgnitionOffYieldsOffStateWithWarningCode(unittest.TestCase):
    """IT-0118 — Trace: IF-0007 / SWR-020(a)/(b), 결정표 K(OFF 행), 7장 시나리오 10"""

    def testIgnitionOnValidFalseYieldsOffState(self):
        """!
        @brief ignitionOnField.valid=True, value=False(유효한 ignition-off)이고 fault=False이면
               state=OFF와 warningReasonCode="IGNITION_OFF"를 반환해야 한다(SWR-020b, 7장
               시나리오 10 재현).
        @technique 요구사항 기반 시험(Requirements-based Test) — 결정표 K OFF 행
        @case Positive
        @breaks ignition-off인데도 OFF로 판정되지 않거나 경고코드가 없는 회귀
        """
        manager = StateManager()
        freshness = buildFreshnessResult(stale=False, elapsedS=0.010, detectedAtS=1.000)

        result = manager.evaluate(freshness, validField(False), validField(False), 1.000)

        self.assertEqual(result.state, SystemState.OFF)
        self.assertEqual(result.warningReasonCode, "IGNITION_OFF")


class TestIT0119FaultPriorityOverOff(unittest.TestCase):
    """IT-0119 — Trace: IF-0007 / 8장 "FAULT > OFF > DEGRADED > NORMAL", 결정표 K"""

    def testSensorFaultTrueAndIgnitionOffSimultaneouslyYieldsFaultNotOff(self):
        """!
        @brief sensor_fault=True와 ignition-off가 동시 성립하면 FAULT가 OFF보다 우선해야 한다
               (8장 판정 순서 — sensor_fault는 입력 신뢰성 자체를 의심해야 하는 명시적 고장 신호).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 K 동시 성립(FAULT vs OFF)
        @case Positive — 8장에서 명시한 "FAULT 최우선" 설계 결정이 OFF 추가 후에도 유지되는지 검증
        @breaks 두 조건 동시 성립 시 OFF가 반환되는 회귀(안전 우선순위 위반)
        """
        manager = StateManager()
        freshness = buildFreshnessResult(stale=False, elapsedS=0.010, detectedAtS=1.000)

        result = manager.evaluate(freshness, validField(True), validField(False), 1.000)

        self.assertEqual(result.state, SystemState.FAULT)
        self.assertEqual(result.warningReasonCode, "SENSOR_FAULT_DETECTED")


class TestIT0120OffPriorityOverDegraded(unittest.TestCase):
    """IT-0120 — Trace: IF-0007 / 8장 "FAULT > OFF > DEGRADED > NORMAL", 결정표 K"""

    def testIgnitionOffAndStaleSimultaneouslyYieldsOffNotDegraded(self):
        """!
        @brief ignition-off와 freshness stale이 동시 성립하면 OFF가 DEGRADED보다 우선해야 한다
               (8장 근거 — ignition_on=FALSE는 확정적 신호, DEGRADED는 정황적 증상).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 K 동시 성립(OFF vs DEGRADED)
        @case Positive — 누적 갭 15 해소 사항(OFF>DEGRADED)이 코드에 그대로 구현됐는지 검증
        @breaks 두 조건 동시 성립 시 DEGRADED가 반환되는 회귀
        """
        manager = StateManager()
        freshness = buildFreshnessResult(stale=True, elapsedS=0.250, detectedAtS=1.000)

        result = manager.evaluate(freshness, validField(False), validField(False), 1.000)

        self.assertEqual(result.state, SystemState.OFF)
        self.assertEqual(result.warningReasonCode, "IGNITION_OFF")


class TestIT0121InvalidIgnitionFieldDoesNotForceOffAndFallsBackToNormalPath(unittest.TestCase):
    """IT-0121 — Trace: IF-0007 / ENG-SWE3-001 8.8절(SW 설계 재량 확정), 오류주입"""

    def testIgnitionOnFieldInvalidIsNotJudgedAsOff(self):
        """!
        @brief ignitionOnField.valid=False(형식 오류)는 OFF로 판정되지 않고 freshness/NORMAL
               경로로 대체되어야 한다(ENG-SWE3-001 8.8절 SW 설계 재량 확정 — ARC-0016의 IF-0023
               오류계약과 대칭인 기준). 이 시험은 오케스트레이터 지침에서 명시한 "ignitionOnField
               invalid → OFF 미판정 회귀" 확인 케이스다.
        @technique 오류주입(Fault Injection Test) — ENG-SWE2-001 9장/ENG-SWE3-001 8.8절 실제 동작 검증
        @case Negative
        @breaks 형식 오류 ignitionOnField에서도 OFF로 잘못 판정되는 회귀(8.8절 결정 붕괴)
        """
        manager = StateManager()
        freshness = buildFreshnessResult(stale=False, elapsedS=0.010, detectedAtS=1.000)
        invalidIgnitionField = invalidField("not-a-bool", errorReason="TYPE_ERROR")

        result = manager.evaluate(freshness, validField(False), invalidIgnitionField, 1.000)

        self.assertEqual(result.state, SystemState.NORMAL)
        self.assertIsNone(result.warningReasonCode)


class TestIT0122IgnitionOnFieldNoneContractViolationRaises(unittest.TestCase):
    """IT-0122 — Trace: IF-0007 / 방어적 계약, ASIL B 오류 주입"""

    def testIgnitionOnFieldNoneRaisesValueError(self):
        """!
        @brief ignitionOnField 자체가 None(상위 계약 위반, 오케스트레이터 배선 결함
               시뮬레이션)이면 ValueError로 방어되어야 한다(IU-0003 사전조건).
        @technique 오류주입(Fault Injection Test) — 계약 위반 입력(None) 직접 주입
        @case Negative
        @breaks 사전조건 위반 시 예외 없이 조용히 오판정이 나오는 회귀
        """
        manager = StateManager()
        freshness = buildFreshnessResult(stale=False, elapsedS=0.010, detectedAtS=1.000)

        with self.assertRaises(ValueError):
            manager.evaluate(freshness, validField(False), None, 1.000)


class TestIT0123FourStateExhaustiveCombinationTable(unittest.TestCase):
    """IT-0123 — Trace: IF-0007 / 결정표 K 전체, 결정테이블 전 조합 검증"""

    def testAllEightFaultIgnitionStaleCombinationsMatchDecisionTableK(self):
        """!
        @brief fault/ignitionOff/stale 3개 이진 조건의 8개 조합 전부가 결정표 K(FAULT>OFF>
               DEGRADED>NORMAL)와 정확히 일치해야 한다(전 조건 조합 시험).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 K 전 조합(2^3=8)
        @case Positive — 회귀 안전망(개별 케이스가 놓친 조합 누락 방지)
        @breaks 8개 조합 중 하나라도 결정표 K의 우선순위 규칙과 어긋나는 회귀
        """
        manager = StateManager()
        staleFreshness = buildFreshnessResult(stale=True, elapsedS=0.300, detectedAtS=1.000)
        freshFreshness = buildFreshnessResult(stale=False, elapsedS=0.010, detectedAtS=1.000)

        table = [
            (True, False, False, SystemState.FAULT),
            (True, False, True, SystemState.FAULT),
            (True, True, False, SystemState.FAULT),
            (True, True, True, SystemState.FAULT),
            (False, True, False, SystemState.OFF),
            (False, True, True, SystemState.OFF),
            (False, False, True, SystemState.DEGRADED),
            (False, False, False, SystemState.NORMAL),
        ]

        for faultValue, ignitionOffValue, staleValue, expectedState in table:
            with self.subTest(fault=faultValue, ignitionOff=ignitionOffValue, stale=staleValue):
                freshness = staleFreshness if staleValue else freshFreshness
                result = manager.evaluate(
                    freshness, validField(faultValue), validField(not ignitionOffValue), 1.000
                )
                self.assertEqual(result.state, expectedState)


if __name__ == "__main__":
    unittest.main()
