"""!
@file test_freshness_monitor.py
@brief IU-0002(ARC-0002 Freshness 모니터) 함수 계약 검증(ENG-SWE3-001 5장/6.3절, SWR-013(a)).
"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.domain.constants import FRESHNESS_STALE_THRESHOLD_S
from ngv.domain.types import FieldValidationResult
from ngv.core.freshness_monitor import FreshnessMonitor


def validField(value):
    """테스트 헬퍼 — 유효한 FieldValidationResult[float]를 만든다."""
    return FieldValidationResult(value=value, valid=True, rawValue=value)


def invalidField(rawValue):
    """테스트 헬퍼 — 무효한 FieldValidationResult[float]를 만든다."""
    return FieldValidationResult(value=None, valid=False, rawValue=rawValue, errorReason="TYPE_ERROR")


class TestFreshnessMonitorEvaluate(unittest.TestCase):
    """IU-0002.evaluate() 계약 검증."""

    def testFreshInputIsNotStale(self):
        """!
        @brief 최근 유효 표본 이후 경과시간이 200ms 미만이면 stale=False를 반환한다.
        @technique 동등분할(Equivalence Partitioning) — 유효 구간(임계값 미만)의 대표값
        @case Positive — 정상 freshness 경로
        @breaks stale 판정 로직이 항상 True를 반환하거나 임계값 비교가 반대로 뒤집히는 회귀
        """
        monitor = FreshnessMonitor()
        result = monitor.evaluate(validField(10.000), 10.050)

        self.assertFalse(result.stale)
        self.assertAlmostEqual(result.elapsedS, 0.050)

    def testExceedsThresholdIsStale(self):
        """!
        @brief 경과시간이 200ms를 초과하면 stale=True를 반환한다.
        @technique 동등분할(Equivalence Partitioning) — 무효 구간(임계값 초과)의 대표값
        @case Negative — SWR-013(a) 초과 경과 시 STALE 전이 요구를 검증
        @breaks 200ms 초과에도 stale=False로 남는 회귀(요구사항 SWR-013(a) 위반)
        """
        monitor = FreshnessMonitor()
        monitor.evaluate(validField(10.000), 10.000)
        result = monitor.evaluate(invalidField(None), 10.201)

        self.assertTrue(result.stale)
        self.assertAlmostEqual(result.elapsedS, 0.201)

    def testExactlyAtThresholdIsNotStale(self):
        """!
        @brief 경과시간이 정확히 200ms이면 "초과"가 아니므로 stale=False를 반환한다.
        @technique 경계값분석(Boundary Value Analysis) — 임계값 자체(200ms)
        @case Positive — SWR-013(a) 원문 "초과하여 경과하면"의 문언(>, >=가 아님)을 검증
        @breaks 비교 연산자를 >에서 >=로 잘못 바꾸는 회귀
        """
        monitor = FreshnessMonitor()
        monitor.evaluate(validField(10.000), 10.000)
        result = monitor.evaluate(invalidField(None), 10.200)

        self.assertFalse(result.stale)
        self.assertAlmostEqual(result.elapsedS, FRESHNESS_STALE_THRESHOLD_S)

    def testNoValidSampleYetIsStaleByDefault(self):
        """!
        @brief 부팅 이후 유효 표본을 한 번도 받지 못했으면 stale=True, elapsedS=inf를 반환한다.
        @technique 오류추측(Error Guessing) — 부팅 직후 "데이터 없음" 경계 상태
        @case Negative — 데이터 부재 시 보수적(fail-safe) 기본값을 검증
        @breaks 유효 표본이 없는데도 stale=False로 낙관 판정하는 회귀
        """
        monitor = FreshnessMonitor()
        result = monitor.evaluate(invalidField(None), 5.000)

        self.assertTrue(result.stale)
        self.assertEqual(result.elapsedS, math.inf)

    def testInvalidFieldDoesNotUpdateLastValidTimestamp(self):
        """!
        @brief sourceTimestampField.valid=False이면 직전 유효 표본 기준 경과시간이 계속 누적된다.
        @technique 상태전이 테스트(State Transition Testing) — 내부 lastValidTimestampS 상태 보존
        @case Negative — 무효 입력이 내부 상태를 오염시키지 않는지 검증
        @breaks 무효 입력을 그대로 lastValidTimestampS에 대입해 경과시간 계산이 깨지는 회귀
        """
        monitor = FreshnessMonitor()
        monitor.evaluate(validField(1.000), 1.000)
        result = monitor.evaluate(invalidField("bad"), 1.100)

        self.assertAlmostEqual(result.elapsedS, 0.100)
        self.assertFalse(result.stale)


class TestFreshnessMonitorReset(unittest.TestCase):
    """IU-0002.reset() 계약 검증."""

    def testResetReturnsToNoValidSampleState(self):
        """!
        @brief reset() 이후 다음 evaluate()는 "유효 표본 없음" 상태(stale=True, elapsedS=inf)로 복귀한다.
        @technique 상태전이 테스트(State Transition Testing) — 부팅/재시작 초기화 전이
        @case Positive — reset()이 8장 근거대로 fail-safe 부팅 기본값을 복원하는지 검증
        @breaks reset()이 lastValidTimestampS를 초기화하지 않아 이전 표본이 남는 회귀
        """
        monitor = FreshnessMonitor()
        monitor.evaluate(validField(1.000), 1.000)

        monitor.reset()
        result = monitor.evaluate(invalidField(None), 1.001)

        self.assertTrue(result.stale)
        self.assertEqual(result.elapsedS, math.inf)


if __name__ == "__main__":
    unittest.main()
