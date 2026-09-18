"""!
@file test_output_actuator_adapter.py
@brief IU-0006(ARC-0006 출력 액추에이터 어댑터) Phase1 최소 계약(패스스루) 검증(ENG-SWE3-001 5장).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.domain.types import ConfirmedOutput, LockCommand
from ngv.adapters.output_actuator_adapter import OutputActuatorAdapter


class TestOutputActuatorAdapterPublish(unittest.TestCase):
    """IU-0006.publish() 계약 검증(값 변형 없는 패스스루)."""

    def testPublishesLockLockWithoutValueTransformation(self):
        """!
        @brief LOCK/LOCK 확정 출력을 OEM-IF-005 문자열 payload로 값 변형 없이 변환한다.
        @technique 동등분할(Equivalence Partitioning) — LockCommand.LOCK 대표값
        @case Positive — 패스스루(값 변형 없음) 계약을 검증
        @breaks LOCK을 다른 문자열로 잘못 변환하거나 필드명을 바꾸는 회귀
        """
        adapter = OutputActuatorAdapter()
        result = adapter.publish(ConfirmedOutput(left=LockCommand.LOCK, right=LockCommand.LOCK))

        self.assertTrue(result.success)
        self.assertEqual(result.payload, {"lock_left": "LOCK", "lock_right": "LOCK"})
        self.assertIsNone(result.errorReason)

    def testPublishesDifferentLeftRightValuesIndependently(self):
        """!
        @brief 좌/우 값이 서로 다를 때도 각 축을 독립적으로 정확히 변환한다.
        @technique 동등분할(Equivalence Partitioning) — RELEASE/LOCK 혼합 대표값
        @case Negative — 좌/우 축이 뒤바뀌거나 뭉개지는 결함을 검출
        @breaks left/right 필드를 서로 뒤바꾸거나 한쪽 축을 무시하는 회귀
        """
        adapter = OutputActuatorAdapter()
        result = adapter.publish(ConfirmedOutput(left=LockCommand.RELEASE, right=LockCommand.LOCK))

        self.assertEqual(result.payload, {"lock_left": "RELEASE", "lock_right": "LOCK"})


if __name__ == "__main__":
    unittest.main()
