"""!
@file test_notification_adapter.py
@brief IU-0007(ARC-0007 표시/경고 어댑터) Phase1 최소 계약(패스스루) 검증(ENG-SWE3-001 5장).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.domain.types import StateResult, SystemState
from ngv.adapters.notification_adapter import NotificationAdapter


class TestNotificationAdapterPublishWarning(unittest.TestCase):
    """IU-0007.publishWarning() 계약 검증(값 변형 없는 패스스루)."""

    def testPublishesFaultStateAndReasonCodeWithoutTransformation(self):
        """!
        @brief FAULT 상태와 경고코드를 OEM-IF-006 state/reason_code 필드로 값 변형 없이 변환한다.
        @technique 동등분할(Equivalence Partitioning) — FAULT 대표값
        @case Positive — 패스스루(값 변형 없음) 계약을 검증
        @breaks state/reason_code 값을 임의로 변형하거나 필드명을 바꾸는 회귀
        """
        adapter = NotificationAdapter()
        stateResult = StateResult(state=SystemState.FAULT, changedToFault=True, warningReasonCode="SENSOR_FAULT_DETECTED")

        result = adapter.publishWarning(stateResult)

        self.assertTrue(result.success)
        self.assertEqual(result.payload, {"state": "FAULT", "reason_code": "SENSOR_FAULT_DETECTED"})

    def testPublishesNormalStateWithNoneReasonCode(self):
        """!
        @brief NORMAL 상태(경고코드 없음)에서도 reason_code=None을 그대로 payload에 전달한다.
        @technique 경계값분석(Boundary Value Analysis) — warningReasonCode가 None인 경계 케이스
        @case Negative — reason_code가 없는 상태를 임의의 기본 문자열로 대체하지 않는지 검증
        @breaks warningReasonCode=None을 빈 문자열 등으로 조용히 바꾸는 회귀
        """
        adapter = NotificationAdapter()
        stateResult = StateResult(state=SystemState.NORMAL, changedToFault=False, warningReasonCode=None)

        result = adapter.publishWarning(stateResult)

        self.assertEqual(result.payload, {"state": "NORMAL", "reason_code": None})


if __name__ == "__main__":
    unittest.main()
