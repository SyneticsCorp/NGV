"""!
@file test_it_step8_crash_monitor.py
@brief 통합 8단계 — ARC-0010(충돌 감시), IF-0016 인터페이스 계약 검증(신규, Phase2).

테스트 베이시스: ENG-SWE2-001 6.1절(IF-0016), 11장 순서표 8행("단위시험 하네스로 직접 호출,
crash_status 3열거값 시험벡터"). ENG-SWE3-001 7장 결정표 E(IU-0010 crash_status 판정)를
그대로 시험벡터 도출에 사용한다.
"""

import unittest

from tests_integration.it_helpers import CrashStatus, invalidField, validField
from ngv.core.crash_monitor import CrashMonitor
from ngv.domain.types import ArbitrationCommand, Door


class TestIT0044CrashConfirmedProducesReleaseCandidate(unittest.TestCase):
    """IT-0044 — Trace: IF-0016 / SWR-007, 결정표 E"""

    def testConfirmedYieldsBothDoorReleaseCandidatePriorityOne(self):
        """!
        @brief crash_status=CONFIRMED이면 status=CONFIRMED와 door=BOTH/command=RELEASE/
               priority=1/reasonCode=CRASH_CONFIRMED인 releaseCandidate를 생성해야 한다(SWR-007).
        @technique 요구사항 기반 시험(Requirements-based Test) — 결정표 E CONFIRMED 행
        @case Positive
        @breaks CONFIRMED인데도 후보가 생성되지 않거나 priority/door가 잘못되는 회귀
        """
        monitor = CrashMonitor()

        result = monitor.evaluate(validField(CrashStatus.CONFIRMED), 1.0)

        self.assertEqual(result.status, CrashStatus.CONFIRMED)
        self.assertIsNotNone(result.releaseCandidate)
        self.assertEqual(result.releaseCandidate.door, Door.BOTH)
        self.assertEqual(result.releaseCandidate.command, ArbitrationCommand.RELEASE)
        self.assertEqual(result.releaseCandidate.priority, 1)
        self.assertEqual(result.releaseCandidate.reasonCode, "CRASH_CONFIRMED")
        self.assertFalse(result.pendingHoldApplied)


class TestIT0045CrashPendingAppliesHoldWithoutCandidate(unittest.TestCase):
    """IT-0045 — Trace: IF-0016 / SWR-008, 결정표 E"""

    def testPendingYieldsNoCandidateAndHoldApplied(self):
        """!
        @brief crash_status=PENDING이면 긴급해제 후보를 생성하지 않고 pendingHoldApplied=True여야
               한다(SWR-008, 오탐 방지 보류).
        @technique 동등분할(Equivalence Partitioning) — 결정표 E PENDING 행
        @case Positive
        @breaks PENDING인데도 후보가 생성되거나 pendingHoldApplied가 False인 회귀
        """
        monitor = CrashMonitor()

        result = monitor.evaluate(validField(CrashStatus.PENDING), 1.0)

        self.assertEqual(result.status, CrashStatus.PENDING)
        self.assertIsNone(result.releaseCandidate)
        self.assertTrue(result.pendingHoldApplied)


class TestIT0046CrashNoneYieldsNoCandidate(unittest.TestCase):
    """IT-0046 — Trace: IF-0016, 결정표 E"""

    def testValidNoneStatusYieldsNoCandidate(self):
        """!
        @brief crash_status=NONE(유효값)이면 후보 없이 status=NONE을 그대로 반환해야 한다.
        @technique 동등분할(Equivalence Partitioning) — 결정표 E NONE 행(buildResult 4번째 호출지점)
        @case Positive
        @breaks NONE인데도 후보가 잘못 생성되는 회귀
        """
        monitor = CrashMonitor()

        result = monitor.evaluate(validField(CrashStatus.NONE), 1.0)

        self.assertEqual(result.status, CrashStatus.NONE)
        self.assertIsNone(result.releaseCandidate)
        self.assertFalse(result.pendingHoldApplied)


class TestIT0047InvalidCrashStatusFieldYieldsNoneWithoutException(unittest.TestCase):
    """IT-0047 — Trace: IF-0016 / 9장 확인 필요 항목(결정표 E 재확인), 오류주입"""

    def testInvalidFieldIsTreatedAsNoneWithoutRaising(self):
        """!
        @brief crashStatusField.valid=False(정의된 3개 열거값 외)는 예외 없이 status=NONE으로
               방어적으로 처리되어야 한다(10.4절 신규 원칙 — 신뢰 불가 데이터로 새 능동 후보를
               생성하지 않음).
        @technique 오류주입(Fault Injection Test) — ENG-SWE2-001 9장 "확인 필요" 항목 실제 동작 검증
        @case Negative
        @breaks 무효 필드에서 예외가 발생하거나 잘못된 후보가 생성되는 회귀
        """
        monitor = CrashMonitor()

        result = monitor.evaluate(invalidField("BOGUS", errorReason="INVALID_ENUM_VALUE"), 1.0)

        self.assertEqual(result.status, CrashStatus.NONE)
        self.assertIsNone(result.releaseCandidate)
        self.assertFalse(result.pendingHoldApplied)


class TestIT0048CrashStatusFieldNoneContractViolationRaises(unittest.TestCase):
    """IT-0048 — Trace: IF-0016 / 방어적 계약, 오류주입"""

    def testCrashStatusFieldNoneRaisesValueError(self):
        """!
        @brief crashStatusField 자체가 None(상위 계약 위반, 오케스트레이터 배선 결함 시뮬레이션)이면
               ValueError를 발생시켜야 한다(방어적 계약).
        @technique 오류주입(Fault Injection Test) — 상위 계약 위반(None) 주입
        @case Negative
        @breaks None 입력에서 예외 없이 조용히 통과되는 회귀(방어적 계약 붕괴)
        """
        monitor = CrashMonitor()

        with self.assertRaises(ValueError):
            monitor.evaluate(None, 1.0)


if __name__ == "__main__":
    unittest.main()
