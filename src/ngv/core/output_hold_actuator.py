"""!
@file output_hold_actuator.py
@brief IU-0004(ARC-0004 출력 유지 액추에이터) — 출력 고정(fail-freeze).

@par 관련 항목
- 요구사항: SWR-021(a)
- 상세설계: ENG-SWE3-001 5장/6.5절/7장 결정표 B
"""

from ngv.domain.constants import BOOT_DEFAULT_LOCK_COMMAND
from ngv.domain.types import ArbitrationCommand, ConfirmedOutput, LockCommand, SystemState


class OutputHoldActuator:
    """!
    @brief FAULT 시 직전 확정값을 유지(fail-freeze)하고, 그 외에는 후보 커맨드를 해석해 확정한다.

    내부 상태(lastConfirmedOutput)는 이 클래스가 단독으로 소유한다(ENG-SWE3-001 8장).
    """

    def __init__(self):
        """!
        @brief 부팅 기본값(LOCK, LOCK)으로 초기화한다.
        """
        self.lastConfirmedOutput = self.bootDefaultOutput()

    def confirm(self, arbitrationResult, stateResult):
        """!
        @brief 결정표 B에 따라 출력을 확정한다.

        @param arbitrationResult ArbitrationResult — IU-0005.arbitrate()의 반환값
        @param stateResult StateResult — IU-0003.evaluate()의 반환값
        @return ConfirmedOutput{left, right}
        @exception 없음
        """
        if stateResult.state == SystemState.FAULT:
            return self.lastConfirmedOutput

        newLeft = self.resolveAxis(arbitrationResult.leftCommand, self.lastConfirmedOutput.left)
        newRight = self.resolveAxis(arbitrationResult.rightCommand, self.lastConfirmedOutput.right)
        self.lastConfirmedOutput = ConfirmedOutput(left=newLeft, right=newRight)
        return self.lastConfirmedOutput

    def reset(self):
        """!
        @brief 내부 상태를 부팅 기본값(LOCK, LOCK)으로 초기화한다.
        @return None
        """
        self.lastConfirmedOutput = self.bootDefaultOutput()

    def getLastConfirmedOutput(self):
        """!
        @brief 현재 보관된 확정값을 반환한다(읽기 전용 접근자 — 시험/로깅 목적).
        @return ConfirmedOutput — 마지막 confirm()/reset() 호출 결과와 동일
        """
        return self.lastConfirmedOutput

    @staticmethod
    def bootDefaultOutput():
        """!
        @brief 부팅 기본값(LOCK, LOCK)을 생성한다.
        @return ConfirmedOutput(left=BOOT_DEFAULT_LOCK_COMMAND, right=BOOT_DEFAULT_LOCK_COMMAND)
        """
        return ConfirmedOutput(left=BOOT_DEFAULT_LOCK_COMMAND, right=BOOT_DEFAULT_LOCK_COMMAND)

    @staticmethod
    def resolveAxis(command, previousValue):
        """!
        @brief 후보 커맨드 한 축을 해석한다.

        @param command ArbitrationCommand — LOCK/RELEASE/NO_CHANGE
        @param previousValue LockCommand — 해당 축의 직전 확정값(NO_CHANGE일 때 사용)
        @return LockCommand — LOCK->LOCK, RELEASE->RELEASE, NO_CHANGE->previousValue
        """
        if command == ArbitrationCommand.NO_CHANGE:
            return previousValue
        return arbitrationToLockCommand(command)


def arbitrationToLockCommand(command):
    """!
    @brief ArbitrationCommand(LOCK/RELEASE)를 LockCommand로 변환한다.

    @param command ArbitrationCommand — LOCK 또는 RELEASE(NO_CHANGE는 호출하지 않음)
    @return LockCommand — 이름이 동일한 LockCommand 값
    """
    return LockCommand[command.name]
