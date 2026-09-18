"""!
@file test_it_step5_secondary_adapters.py
@brief 통합 5단계(병렬) — ARC-0006/ARC-0007/ARC-0008, IF-0010/IF-0003, IF-0011/IF-0004, IF-0012
       인터페이스 계약 검증.

테스트 베이시스: ENG-SWE2-001 6.1/6.2절, 9장("이 어댑터들이 값을 변형 없이 그대로 전달함을
상세설계·단위시험 단계에서 검증해야 한다" — 왕복 비교 확인 필요 항목), 11장 순서표 5행
("각각 단위시험 하네스, 외부측은 캡처용 인메모리 싱크로 대체").
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.adapters.decision_logger_stub import DecisionLoggerStub
from ngv.adapters.notification_adapter import NotificationAdapter
from ngv.adapters.output_actuator_adapter import OutputActuatorAdapter
from ngv.domain.types import ConfirmedOutput, DecisionLogEntry, LockCommand, StateResult, SystemState


class TestIT0021OutputAdapterRoundTripLockRelease(unittest.TestCase):
    """IT-0021 — Trace: IF-0010, IF-0003 / SWR-021(a) 전달 경로"""

    def testPublishConvertsWithoutValueDistortion(self):
        """!
        @brief IF-0010으로 받은 ConfirmedOutput(LOCK, RELEASE)이 IF-0003 payload(lock_left/
               lock_right)로 값 변형 없이 왕복 변환되어야 한다(9장 확인 필요 항목 해소).
        @technique 요구사항 기반 시험(Requirements-based Test) — 왕복 비교(round-trip)
        @case Positive
        @breaks 좌/우 값이 뒤바뀌거나 enum 이름이 왜곡되는 회귀
        """
        adapter = OutputActuatorAdapter()
        confirmed = ConfirmedOutput(left=LockCommand.LOCK, right=LockCommand.RELEASE)

        result = adapter.publish(confirmed)

        self.assertTrue(result.success)
        self.assertEqual(result.payload["lock_left"], "LOCK")
        self.assertEqual(result.payload["lock_right"], "RELEASE")
        self.assertIsNone(result.errorReason)


class TestIT0022OutputAdapterRoundTripReleaseRelease(unittest.TestCase):
    """IT-0022 — Trace: IF-0010, IF-0003"""

    def testPublishHandlesSecondEquivalenceClass(self):
        """!
        @brief 두 축 모두 RELEASE인 등가클래스도 값 왜곡 없이 변환되어야 한다.
        @technique 동등분할(Equivalence Partitioning) — {LOCK,RELEASE} 조합의 두 번째 대표값
        @case Positive
        @breaks 특정 조합에서만 값이 고정(하드코딩)되는 회귀
        """
        adapter = OutputActuatorAdapter()
        confirmed = ConfirmedOutput(left=LockCommand.RELEASE, right=LockCommand.RELEASE)

        result = adapter.publish(confirmed)

        self.assertEqual(result.payload["lock_left"], "RELEASE")
        self.assertEqual(result.payload["lock_right"], "RELEASE")


class TestIT0023NotificationAdapterFaultWarning(unittest.TestCase):
    """IT-0023 — Trace: IF-0011, IF-0004 / SWR-021(b)"""

    def testPublishWarningCarriesFaultStateAndReasonCode(self):
        """!
        @brief IF-0011로 받은 StateResult(FAULT, reasonCode)가 IF-0004 payload(state/
               reason_code)로 값 변형 없이 전달되어야 한다(SWR-021b).
        @technique 요구사항 기반 시험(Requirements-based Test) — 왕복 비교
        @case Positive
        @breaks reason_code가 누락되거나 state 문자열이 왜곡되는 회귀
        """
        adapter = NotificationAdapter()
        stateResult = StateResult(
            state=SystemState.FAULT, changedToFault=True, warningReasonCode="SENSOR_FAULT_DETECTED"
        )

        result = adapter.publishWarning(stateResult)

        self.assertTrue(result.success)
        self.assertEqual(result.payload["state"], "FAULT")
        self.assertEqual(result.payload["reason_code"], "SENSOR_FAULT_DETECTED")


class TestIT0024NotificationAdapterNormalNoWarning(unittest.TestCase):
    """IT-0024 — Trace: IF-0011, IF-0004"""

    def testPublishWarningCarriesNoneReasonCodeForNormalState(self):
        """!
        @brief NORMAL 상태(reasonCode=None)에서는 payload의 reason_code도 None으로 전달되어야
               한다(경고 없음 등가클래스).
        @technique 동등분할(Equivalence Partitioning) — 경고 없음(None) 클래스
        @case Negative — None이 임의의 placeholder 문자열로 대체되지 않는지 검증
        @breaks None이 빈 문자열이나 임의 기본값으로 치환되는 회귀
        """
        adapter = NotificationAdapter()
        stateResult = StateResult(state=SystemState.NORMAL, changedToFault=False, warningReasonCode=None)

        result = adapter.publishWarning(stateResult)

        self.assertEqual(result.payload["state"], "NORMAL")
        self.assertIsNone(result.payload["reason_code"])


class TestIT0025DecisionLoggerStubNoOp(unittest.TestCase):
    """IT-0025 — Trace: IF-0012, OEM-NFR-001/002(Phase1 no-op)"""

    def testLogAcceptsEntryWithoutRaisingOrReturning(self):
        """!
        @brief Phase1 스텁은 어떤 DecisionLogEntry를 받아도 예외 없이 None을 반환해야 한다
               (11장 6단계에서 오케스트레이터가 항상 호출해도 사이클을 방해하지 않음을 보장).
        @technique 요구사항 기반 시험(Requirements-based Test) — no-op 계약
        @case Positive
        @breaks Phase1인데도 저장 로직이 동작하거나 예외가 발생하는 회귀(범위 초과 구현)
        """
        logger = DecisionLoggerStub()
        entry = DecisionLogEntry(
            cycleId=1,
            nowS=1.000,
            state=SystemState.NORMAL,
            confirmedOutput=ConfirmedOutput(left=LockCommand.LOCK, right=LockCommand.LOCK),
            blocked=False,
            blockReason=None,
        )

        result = logger.log(entry)

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
