"""!
@file test_it_step15_ignition_off_release_monitor.py
@brief 통합 15단계 — ARC-0016(ignition-off 해제 후보 생성), IF-0023 인터페이스 계약 검증
       (신규, Phase3).

테스트 베이시스: ENG-SWE2-001 6.1절(IF-0023), 11장 순서표 15행("단위시험 하네스,
ignitionOnField valid/TRUE/FALSE 시험벡터"). ENG-SWE3-001 7장 결정표 N(IU-0016 ignition-off
판정)을 그대로 시험벡터 도출에 사용한다.
"""

import unittest

from tests_integration.it_helpers import invalidField, validField
from ngv.core.ignition_off_release_monitor import IgnitionOffReleaseMonitor
from ngv.domain.types import ArbitrationCommand, Door


class TestIT0094ValidFalseYieldsReleaseCandidatePriorityFour(unittest.TestCase):
    """IT-0094 — Trace: IF-0023 / SWR-020(a), 결정표 N"""

    def testValidIgnitionOffYieldsBothDoorReleaseCandidate(self):
        """!
        @brief ignitionOnField.valid=True, value=False(ignition-off)이면 off=True와
               door=BOTH/command=RELEASE/priority=4/reasonCode=IGNITION_OFF인 releaseCandidate를
               생성해야 한다(SWR-020a).
        @technique 요구사항 기반 시험(Requirements-based Test) — 결정표 N FALSE 행
        @case Positive
        @breaks ignition-off인데도 후보가 생성되지 않거나 priority/door가 잘못되는 회귀
        """
        monitor = IgnitionOffReleaseMonitor()

        result = monitor.evaluate(validField(False), 1.000)

        self.assertTrue(result.off)
        self.assertIsNotNone(result.releaseCandidate)
        self.assertEqual(result.releaseCandidate.door, Door.BOTH)
        self.assertEqual(result.releaseCandidate.command, ArbitrationCommand.RELEASE)
        self.assertEqual(result.releaseCandidate.priority, 4)
        self.assertEqual(result.releaseCandidate.reasonCode, "IGNITION_OFF")


class TestIT0095ValidTrueYieldsNoCandidate(unittest.TestCase):
    """IT-0095 — Trace: IF-0023 / SWR-020, 결정표 N"""

    def testValidIgnitionOnYieldsNoCandidate(self):
        """!
        @brief ignitionOnField.valid=True, value=True(ignition-on, 유효값)이면 off=False이고
               후보를 생성하지 않아야 한다.
        @technique 동등분할(Equivalence Partitioning) — 결정표 N TRUE(유효) 행
        @case Positive
        @breaks ignition-on인데도 해제 후보가 잘못 생성되는 회귀
        """
        monitor = IgnitionOffReleaseMonitor()

        result = monitor.evaluate(validField(True), 1.000)

        self.assertFalse(result.off)
        self.assertIsNone(result.releaseCandidate)


class TestIT0096InvalidFieldYieldsNoCandidateWithoutException(unittest.TestCase):
    """IT-0096 — Trace: IF-0023 / ENG-SWE3-001 8.8절(SW 설계 재량 확정), 오류주입"""

    def testInvalidFieldIsTreatedAsNotOffWithoutRaising(self):
        """!
        @brief ignitionOnField.valid=False(형식 오류)는 예외 없이 off=False(후보 미생성)로
               방어적으로 처리되어야 한다(ENG-SWE3-001 8.8절 — IU-0003의 OFF 미판정 결정과
               대칭인 기준, 10.4절 원칙과 동일).
        @technique 오류주입(Fault Injection Test) — 형식 오류 필드 실제 동작 검증
        @case Negative
        @breaks 무효 필드에서 예외가 발생하거나 잘못된 후보가 생성되는 회귀
        """
        monitor = IgnitionOffReleaseMonitor()

        result = monitor.evaluate(invalidField("not-a-bool", errorReason="TYPE_ERROR"), 1.000)

        self.assertFalse(result.off)
        self.assertIsNone(result.releaseCandidate)


class TestIT0097IgnitionOnFieldNoneContractViolationRaises(unittest.TestCase):
    """IT-0097 — Trace: IF-0023 / 방어적 계약, 오류주입"""

    def testIgnitionOnFieldNoneRaisesValueError(self):
        """!
        @brief ignitionOnField 자체가 None(상위 계약 위반, 오케스트레이터 배선 결함 시뮬레이션)이면
               ValueError를 발생시켜야 한다(방어적 계약).
        @technique 오류주입(Fault Injection Test) — 상위 계약 위반(None) 주입
        @case Negative
        @breaks None 입력에서 예외 없이 조용히 통과되는 회귀(방어적 계약 붕괴)
        """
        monitor = IgnitionOffReleaseMonitor()

        with self.assertRaises(ValueError):
            monitor.evaluate(None, 1.000)


if __name__ == "__main__":
    unittest.main()
