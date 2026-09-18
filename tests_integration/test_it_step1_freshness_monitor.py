"""!
@file test_it_step1_freshness_monitor.py
@brief 통합 1단계 — ARC-0002(Freshness 모니터), IF-0006 인터페이스 계약 검증.

테스트 베이시스: ENG-SWE2-001 6.1절(IF-0006), 11장 순서표 1행("단위시험 하네스로 직접 호출,
의존 없음"). 단위시험(SWE.4)이 이미 IU-0002 자체 계약을 검증했으므로, 여기서는 IF-0006이
정의한 데이터 계약(FreshnessResult{stale, elapsedS, detectedAtS})과 시간 제약(200ms 임계,
SWR-013a)이 인터페이스 경계에서 실제로 성립하는지에 초점을 맞춘다.
"""

import unittest

from tests_integration.it_helpers import validField, invalidField
from ngv.core.freshness_monitor import FreshnessMonitor


class TestIT0001FreshnessBoundaryAtThreshold(unittest.TestCase):
    """IT-0001 — Trace: IF-0006 / SWR-013(a)"""

    def testExactly200msElapsedIsNotStale(self):
        """!
        @brief 정확히 200ms 경과(경계값)에서는 stale=False여야 한다(초과만 stale).
        @technique 경계값분석(Boundary Value Analysis) — FRESHNESS_STALE_THRESHOLD_S(0.200s) 경계
        @case Positive — 경계값 자체는 아직 초과가 아님을 확인
        @breaks 경계 비교연산자가 >=로 바뀌어 정상 경계에서 오탐 DEGRADED가 발생하는 회귀
        """
        monitor = FreshnessMonitor()
        monitor.evaluate(validField(0.000), 0.000)

        result = monitor.evaluate(invalidField(None, "MISSING"), 0.200)

        self.assertFalse(result.stale)
        self.assertAlmostEqual(result.elapsedS, 0.200)


class TestIT0002FreshnessBoundaryOverThreshold(unittest.TestCase):
    """IT-0002 — Trace: IF-0006 / SWR-013(a)"""

    def testOverThresholdByEpsilonIsStale(self):
        """!
        @brief 200ms를 아주 조금(경계+1) 초과하면 stale=True가 되어야 한다(SWR-013a).
        @technique 경계값분석(Boundary Value Analysis) — 경계+오차(0.201s)
        @case Positive — 임계 초과 직후 즉시 stale 판정
        @breaks 임계값이 하드코딩 오류로 다른 값(예: 0.3s)으로 바뀌는 회귀
        """
        monitor = FreshnessMonitor()
        monitor.evaluate(validField(0.000), 0.000)

        result = monitor.evaluate(invalidField(None, "MISSING"), 0.201)

        self.assertTrue(result.stale)
        self.assertAlmostEqual(result.elapsedS, 0.201)


class TestIT0003InvalidSampleDoesNotResetElapsed(unittest.TestCase):
    """IT-0003 — Trace: IF-0006 / SWR-013(b)"""

    def testInvalidTimestampFieldKeepsAccumulatingFromLastValid(self):
        """!
        @brief valid=False 표본은 freshness 갱신에 미반영되고, 마지막 valid 표본 기준
               경과시간이 계속 누적되어야 한다(IF-0006 오류 계약).
        @technique 동등분할(Equivalence Partitioning) — 유효/무효 입력 클래스
        @case Negative — 무효 표본이 워치독 상태를 오염시키지 않는지 검증
        @breaks 무효 표본이 lastValidTimestampS를 덮어써 워치독이 리셋되는 회귀
        """
        monitor = FreshnessMonitor()
        monitor.evaluate(validField(1.000), 1.000)

        firstInvalid = monitor.evaluate(invalidField("bad", "TYPE_ERROR"), 1.100)
        secondInvalid = monitor.evaluate(invalidField(None, "MISSING"), 1.250)

        self.assertFalse(firstInvalid.stale)
        self.assertAlmostEqual(firstInvalid.elapsedS, 0.100)
        self.assertTrue(secondInvalid.stale)
        self.assertAlmostEqual(secondInvalid.elapsedS, 0.250)


class TestIT0004ResetRestoresBootDefault(unittest.TestCase):
    """IT-0004 — Trace: IF-0006"""

    def testResetReturnsToNoValidSampleState(self):
        """!
        @brief reset() 이후에는 유효 표본이 없는 부팅 상태(elapsedS=inf)로 돌아가야 한다.
        @technique 상태전이 테스트(State Transition Testing) — 관측 이력 -> reset -> 부팅 상태
        @case Positive — reset()이 내부 워치독 상태를 완전히 비우는지 검증
        @breaks reset() 이후에도 이전 lastValidTimestampS가 남아있는 회귀
        """
        monitor = FreshnessMonitor()
        monitor.evaluate(validField(1.000), 1.000)

        monitor.reset()
        result = monitor.evaluate(invalidField(None, "MISSING"), 1.500)

        self.assertTrue(result.stale)
        self.assertEqual(result.elapsedS, float("inf"))


if __name__ == "__main__":
    unittest.main()
