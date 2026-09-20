"""!
@file test_ignition_off_release_monitor.py
@brief IU-0016(ARC-0016 ignition-off 해제 후보 생성) 함수 계약 검증(ENG-SWE3-001 5.14절/
       6.16절/7장 결정표 N, SWR-020).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.domain.constants import PRIORITY_IGNITION_OFF_RELEASE, REASON_CODE_IGNITION_OFF
from ngv.domain.types import ArbitrationCommand, Door, FieldValidationResult
from ngv.core.ignition_off_release_monitor import IgnitionOffReleaseMonitor


def validField(value):
    """테스트 헬퍼 — 유효한 FieldValidationResult[bool]를 만든다."""
    return FieldValidationResult(value=value, valid=True, rawValue=value)


def invalidField(rawValue, errorReason="TYPE_ERROR"):
    """테스트 헬퍼 — 무효한 FieldValidationResult를 만든다."""
    return FieldValidationResult(value=None, valid=False, rawValue=rawValue, errorReason=errorReason)


class TestIgnitionOffReleaseMonitorEvaluate(unittest.TestCase):
    """IU-0016.evaluate() 결정표 N 계약 검증."""

    def testValidValueFalseProducesBothDoorsReleaseCandidate(self):
        """!
        @brief valid=True, value==False이면 door=BOTH, command=RELEASE, priority=4인 해제 후보를 만든다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 N, valid=True/False 행
        @case Positive — SWR-020(a) ignition_on=FALSE 해제 후보 생성 경로를 검증
        @breaks ignition_on=FALSE인데도 releaseCandidate가 None으로 남는 회귀
        """
        result = IgnitionOffReleaseMonitor().evaluate(validField(False), 1.0)

        self.assertTrue(result.off)
        self.assertIsNotNone(result.releaseCandidate)
        self.assertEqual(result.releaseCandidate.door, Door.BOTH)
        self.assertEqual(result.releaseCandidate.command, ArbitrationCommand.RELEASE)
        self.assertEqual(result.releaseCandidate.priority, PRIORITY_IGNITION_OFF_RELEASE)
        self.assertEqual(result.releaseCandidate.reasonCode, REASON_CODE_IGNITION_OFF)

    def testValidValueTrueProducesNoCandidate(self):
        """!
        @brief valid=True, value==True(점화 ON)이면 off=False, releaseCandidate=None이다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 N, valid=True/True 행
        @case Positive — 점화 ON 상태에서는 해제 후보가 없는 기본 경로를 검증
        @breaks ignition_on=TRUE인데도 releaseCandidate가 생성되는 회귀
        """
        result = IgnitionOffReleaseMonitor().evaluate(validField(True), 1.0)

        self.assertFalse(result.off)
        self.assertIsNone(result.releaseCandidate)

    def testInvalidFieldRejectsWithoutGeneratingNewCandidate(self):
        """!
        @brief valid=False이면 off=False, releaseCandidate=None이다(10.4절/10.7절/8.8절 원칙).
        @technique 동등분할(Equivalence Partitioning) — 무효 입력 클래스의 대표값
        @case Negative — 신뢰할 수 없는 데이터로 새 RELEASE 후보를 생성하지 않는 방어 원칙을 검증
        @breaks 손상된 입력에서도 RELEASE 후보를 생성해 불필요한 해제를 유발하는 회귀
        """
        result = IgnitionOffReleaseMonitor().evaluate(invalidField("bogus"), 1.0)

        self.assertFalse(result.off)
        self.assertIsNone(result.releaseCandidate)

    def testInvalidFieldWithFalseValueStillProducesNoCandidate(self):
        """!
        @brief valid=False이고 대체값 자체가 value=False라도 후보를 생성하지 않는다
               (IU-0003의 OFF 미판정 결정과 대칭인 8.8절 확정 사항의 회귀 방지 테스트).
        @technique 오류추측(Error Guessing) — IU-0003 대칭 회귀 검출용 경계 케이스
        @case Negative — valid 플래그만으로 판정하고 value 자체는 근거로 삼지 않는지 검증
        @breaks value만 보고 valid를 무시해 무효 데이터로도 후보를 생성하는 회귀
        """
        result = IgnitionOffReleaseMonitor().evaluate(invalidField(False, errorReason="TYPE_ERROR"), 1.0)

        self.assertFalse(result.off)
        self.assertIsNone(result.releaseCandidate)

    def testRaisesValueErrorWhenFieldIsNone(self):
        """!
        @brief ignitionOnField가 None이면 ValueError를 던진다(상위 계약 위반 방어).
        @technique 오류추측(Error Guessing) — IU-0010/IU-0003 선례와 동일한 방어적 예외 패턴
        @case Negative — 사전조건(not None) 위반 시 방어적 예외를 검증
        @breaks None 입력이 예외 없이 통과되어 하류에서 AttributeError로 이어지는 회귀
        """
        with self.assertRaises(ValueError):
            IgnitionOffReleaseMonitor().evaluate(None, 1.0)


if __name__ == "__main__":
    unittest.main()
