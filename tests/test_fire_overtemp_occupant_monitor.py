"""!
@file test_fire_overtemp_occupant_monitor.py
@brief IU-0013(ARC-0013 화재/과온/탑승 감시) 함수 계약 검증(ENG-SWE3-001 5.7절/6.12절/
       7장 결정표 H, SWR-017 OR 판정 및 복수 트리거).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.domain.constants import (
    PRIORITY_FIRE_OVERTEMP_OCCUPANT,
    REASON_CODE_ADULT_PRESENT_DETECTED,
    REASON_CODE_FIRE_DETECTED,
    REASON_CODE_FORCED_RELEASE,
    REASON_CODE_OVERTEMPERATURE_DETECTED,
)
from ngv.domain.types import ArbitrationCommand, Door, FieldValidationResult
from ngv.core.fire_overtemp_occupant_monitor import FireOvertempOccupantMonitor


def validField(value):
    """테스트 헬퍼 — 유효한 FieldValidationResult[bool]을 만든다."""
    return FieldValidationResult(value=value, valid=True, rawValue=value)


def invalidField(rawValue, errorReason="TYPE_ERROR"):
    """테스트 헬퍼 — 무효한 FieldValidationResult를 만든다."""
    return FieldValidationResult(value=None, valid=False, rawValue=rawValue, errorReason=errorReason)


class TestFireOvertempOccupantMonitorEvaluate(unittest.TestCase):
    """IU-0013.evaluate() 결정표 H(OR 판정) 계약 검증."""

    def testAllFalseProducesNoTriggerAndNoCandidate(self):
        """!
        @brief 세 필드 모두 False이면 triggered=False, releaseCandidate=None이다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 H, 전부 False/invalid 행
        @case Positive — 화재/과온/탑승 모두 없음 기본 상태를 검증
        @breaks 아무 조건도 없는데 강제해제가 트리거되는 회귀
        """
        result = FireOvertempOccupantMonitor().evaluate(validField(False), validField(False), validField(False))

        self.assertFalse(result.triggered)
        self.assertIsNone(result.releaseCandidate)
        self.assertEqual(result.triggeredReasonCodes, [])

    def testFireOnlyTriggersForcedReleaseWithFireReasonCode(self):
        """!
        @brief fire_detected만 True이면 triggered=True이고 FIRE_DETECTED만 기록된다(SWR-017a).
        @technique 동등분할(Equivalence Partitioning) — 단일 조건 트리거 대표값
        @case Positive — OR 판정(하나 이상)의 최소 성립 경로를 검증
        @breaks fire만 True인데도 triggered=False로 남는 회귀
        """
        result = FireOvertempOccupantMonitor().evaluate(validField(True), validField(False), validField(False))

        self.assertTrue(result.triggered)
        self.assertEqual(result.triggeredReasonCodes, [REASON_CODE_FIRE_DETECTED])
        self.assertIsNotNone(result.releaseCandidate)
        self.assertEqual(result.releaseCandidate.door, Door.BOTH)
        self.assertEqual(result.releaseCandidate.command, ArbitrationCommand.RELEASE)
        self.assertEqual(result.releaseCandidate.priority, PRIORITY_FIRE_OVERTEMP_OCCUPANT)
        self.assertEqual(result.releaseCandidate.reasonCode, REASON_CODE_FORCED_RELEASE)

    def testAllThreeTrueSimultaneouslyRecordsAllReasonCodes(self):
        """!
        @brief 세 필드 모두 동시에 True이면 triggeredReasonCodes에 셋 다 기록된다(SWR-017b).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 H, 복수 동시 TRUE 조합
        @case Positive — 복수 트리거가 모두 함께 기록되는지 검증
        @breaks 여러 조건이 동시에 성립해도 일부 이유코드가 누락되는 회귀
        """
        result = FireOvertempOccupantMonitor().evaluate(validField(True), validField(True), validField(True))

        self.assertTrue(result.triggered)
        self.assertEqual(
            result.triggeredReasonCodes,
            [REASON_CODE_FIRE_DETECTED, REASON_CODE_OVERTEMPERATURE_DETECTED, REASON_CODE_ADULT_PRESENT_DETECTED],
        )

    def testInvalidFieldDoesNotContributeToTrigger(self):
        """!
        @brief valid=False인 필드는 값이 True와 동등하더라도 트리거에 기여하지 않는다(10.4절).
        @technique 오류추측(Error Guessing) — 손상된 입력이 강제해제를 유발하지 않는지 확인
        @case Negative — 신뢰할 수 없는 데이터로 새 RELEASE 후보를 생성하지 않는 방어 원칙을 검증
        @breaks invalid 필드도 True처럼 취급해 불필요한 강제해제를 유발하는 회귀
        """
        result = FireOvertempOccupantMonitor().evaluate(invalidField("bad"), validField(False), validField(False))

        self.assertFalse(result.triggered)
        self.assertIsNone(result.releaseCandidate)
        self.assertEqual(result.triggeredReasonCodes, [])

    def testRaisesValueErrorWhenAnyFieldIsNone(self):
        """!
        @brief 세 인자 중 하나라도 None이면 ValueError를 던진다(사전조건 위반 방어).
        @technique 오류추측(Error Guessing) — 필수 인자 누락
        @case Negative — 사전조건(3개 인자 모두 not None) 위반 시 방어적 예외를 검증
        @breaks None 인자가 예외 없이 통과되어 AttributeError로 이어지는 회귀
        """
        with self.assertRaises(ValueError):
            FireOvertempOccupantMonitor().evaluate(None, validField(False), validField(False))


if __name__ == "__main__":
    unittest.main()
