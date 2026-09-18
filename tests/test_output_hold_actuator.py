"""!
@file test_output_hold_actuator.py
@brief IU-0004(ARC-0004 출력 유지 액추에이터) 함수 계약 검증(ENG-SWE3-001 5장/6.5절/7장 결정표B, SWR-021(a)).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.domain.types import (
    ArbitrationCommand,
    ArbitrationResult,
    LockCommand,
    StateResult,
    SystemState,
)
from ngv.core.output_hold_actuator import OutputHoldActuator


def arbitration(leftCommand, rightCommand, blocked=False):
    """테스트 헬퍼 — ArbitrationResult를 만든다."""
    return ArbitrationResult(leftCommand=leftCommand, rightCommand=rightCommand, blocked=blocked)


def state(systemState):
    """테스트 헬퍼 — StateResult를 만든다(경고코드는 이 테스트 범위 밖)."""
    warningCode = "FAULT" if systemState == SystemState.FAULT else None
    return StateResult(state=systemState, changedToFault=False, warningReasonCode=warningCode)


class TestOutputHoldActuatorConfirm(unittest.TestCase):
    """IU-0004.confirm() 계약 검증(결정표 B)."""

    def testAppliesLockAndReleaseCommandsWhenNotFault(self):
        """!
        @brief state!=FAULT이면 LOCK/RELEASE 후보 커맨드를 그대로 확정 출력에 반영한다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 B 행(NORMAL, blocked=False)
        @case Positive — 정상 경로에서 후보 커맨드가 그대로 적용되는지 검증
        @breaks LOCK/RELEASE 해석이 뒤바뀌거나 확정값이 갱신되지 않는 회귀
        """
        actuator = OutputHoldActuator()
        result = actuator.confirm(
            arbitration(ArbitrationCommand.RELEASE, ArbitrationCommand.LOCK), state(SystemState.NORMAL)
        )

        self.assertEqual(result.left, LockCommand.RELEASE)
        self.assertEqual(result.right, LockCommand.LOCK)

    def testNoChangeKeepsPreviousConfirmedValuePerAxis(self):
        """!
        @brief NO_CHANGE 후보는 해당 축의 직전 확정값을 그대로 유지한다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 B, NO_CHANGE 개별 축 처리
        @case Positive — 좌/우 축이 독립적으로 유지/갱신되는지 검증
        @breaks NO_CHANGE를 LOCK/RELEASE 중 하나로 잘못 강제하는 회귀
        """
        actuator = OutputHoldActuator()
        actuator.confirm(
            arbitration(ArbitrationCommand.LOCK, ArbitrationCommand.RELEASE), state(SystemState.NORMAL)
        )

        result = actuator.confirm(
            arbitration(ArbitrationCommand.NO_CHANGE, ArbitrationCommand.NO_CHANGE), state(SystemState.NORMAL)
        )

        self.assertEqual(result.left, LockCommand.LOCK)
        self.assertEqual(result.right, LockCommand.RELEASE)

    def testFaultStateFreezesLastConfirmedOutputIgnoringCommands(self):
        """!
        @brief state==FAULT이면 후보 커맨드 내용과 무관하게 직전 확정값을 그대로 유지한다(fail-freeze).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 B 행(FAULT, 무관)
        @case Negative — SWR-021(a) fail-freeze 요구를 검증(FAULT가 커맨드 해석보다 항상 우선)
        @breaks FAULT임에도 후보 커맨드를 읽어 출력이 변경되는 회귀(SWR-021(a) 위반)
        """
        actuator = OutputHoldActuator()
        actuator.confirm(
            arbitration(ArbitrationCommand.LOCK, ArbitrationCommand.LOCK), state(SystemState.NORMAL)
        )

        result = actuator.confirm(
            arbitration(ArbitrationCommand.RELEASE, ArbitrationCommand.RELEASE), state(SystemState.FAULT)
        )

        self.assertEqual(result.left, LockCommand.LOCK)
        self.assertEqual(result.right, LockCommand.LOCK)

    def testFaultStateDoesNotMutateInternalStateBeyondFreeze(self):
        """!
        @brief FAULT 경로에서 내부 상태(lastConfirmedOutput)는 변경되지 않는다.
        @technique 상태전이 테스트(State Transition Testing) — FAULT 반복 호출 후 값 불변성
        @case Negative — 고정 자체가 핵심 계약(부작용 없음)임을 검증
        @breaks FAULT 경로에서 내부 상태가 몰래 갱신되는 회귀
        """
        actuator = OutputHoldActuator()
        actuator.confirm(
            arbitration(ArbitrationCommand.LOCK, ArbitrationCommand.RELEASE), state(SystemState.NORMAL)
        )

        actuator.confirm(arbitration(ArbitrationCommand.LOCK, ArbitrationCommand.LOCK), state(SystemState.FAULT))
        actuator.confirm(arbitration(ArbitrationCommand.LOCK, ArbitrationCommand.LOCK), state(SystemState.FAULT))

        self.assertEqual(actuator.getLastConfirmedOutput().left, LockCommand.LOCK)
        self.assertEqual(actuator.getLastConfirmedOutput().right, LockCommand.RELEASE)


class TestOutputHoldActuatorReset(unittest.TestCase):
    """IU-0004.reset()/getLastConfirmedOutput() 계약 검증."""

    def testResetRestoresBootDefaultLockLock(self):
        """!
        @brief reset() 이후 확정값은 부팅 기본값(LOCK, LOCK)이다.
        @technique 경계값분석(Boundary Value Analysis) — 부팅 직후(최초 확정 이전) 경계 상태
        @case Positive — 8장 근거(BOOT_DEFAULT_LOCK_COMMAND=LOCK/LOCK)를 검증
        @breaks reset() 후 기본값이 LOCK/LOCK이 아닌 회귀
        """
        actuator = OutputHoldActuator()
        actuator.confirm(
            arbitration(ArbitrationCommand.RELEASE, ArbitrationCommand.RELEASE), state(SystemState.NORMAL)
        )

        actuator.reset()

        result = actuator.getLastConfirmedOutput()
        self.assertEqual(result.left, LockCommand.LOCK)
        self.assertEqual(result.right, LockCommand.LOCK)

    def testGetLastConfirmedOutputIsValidBeforeAnyConfirmCall(self):
        """!
        @brief confirm()을 한 번도 호출하지 않아도 생성 직후 항상 유효한 확정값을 보유한다.
        @technique 경계값분석(Boundary Value Analysis) — 최초 생성 시점(confirm 미호출) 경계
        @case Positive — 사전조건 "reset() 또는 최초 생성 이후 항상 유효한 값 보유"를 검증
        @breaks 최초 생성 직후 getLastConfirmedOutput()이 None 또는 예외를 발생시키는 회귀
        """
        actuator = OutputHoldActuator()

        result = actuator.getLastConfirmedOutput()

        self.assertEqual(result.left, LockCommand.LOCK)
        self.assertEqual(result.right, LockCommand.LOCK)


if __name__ == "__main__":
    unittest.main()
