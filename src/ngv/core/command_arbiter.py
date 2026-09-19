"""!
@file command_arbiter.py
@brief IU-0005(ARC-0005 Command Arbiter) — 상태/입력유효성 게이트 + 문(door)별 우선순위 후보
       선택(Chain of Responsibility 실제 구현, Phase2 갱신).

Phase1의 "candidateCommands는 항상 빈 리스트/비어있지 않으면 NotImplementedError" 계약을
폐기하고, 문(door)별 최소-priority 후보 선택 알고리즘으로 완전히 대체한다(ENG-SWE3-001 5.2절).

@par 관련 항목
- 요구사항: SWR-021(a) 경로 + SWR-005, SWR-006, SWR-007, SWR-009, SWR-017(우선순위 중재)
- 상세설계: ENG-SWE3-001 5.2절/6.8절/7장 결정표 I
"""

from ngv.domain.constants import BLOCK_REASON_INPUT_INVALID, BLOCK_REASON_STATE_FAULT
from ngv.domain.types import ArbitrationCommand, ArbitrationResult, Door, SystemState


class CommandArbiter:
    """!
    @brief FAULT/inputValid 게이트를 최우선 적용한 뒤, 문별로 최소-priority 후보를 선택한다.

    내부 상태 없음(순수 함수, Phase1과 동일).
    """

    def arbitrate(self, stateResult, inputValid, candidateCommands=None):
        """!
        @brief 게이트를 적용하고, 통과하면 문별 우선순위 후보 선택을 수행한다.

        @param stateResult StateResult — IU-0003.evaluate()의 반환값
        @param inputValid bool — 7장 결정표 D의 합성 결과
        @param candidateCommands Optional[list[CandidateCommand]] — None이면 빈 리스트로 취급
        @return ArbitrationResult{leftCommand, rightCommand, blocked, blockReason,
                leftReasonCode, rightReasonCode}
        @exception ValueError 동일 문에 동일 최소 priority 후보가 2개 이상이면 발생(selectForDoor)
        """
        if stateResult.state == SystemState.FAULT:
            return self.buildBlockedResult(BLOCK_REASON_STATE_FAULT)
        if not inputValid:
            return self.buildBlockedResult(BLOCK_REASON_INPUT_INVALID)

        candidates = candidateCommands or []
        leftCommand, leftReasonCode = self.selectForDoor(candidates, Door.LEFT)
        rightCommand, rightReasonCode = self.selectForDoor(candidates, Door.RIGHT)
        return ArbitrationResult(
            leftCommand=leftCommand,
            rightCommand=rightCommand,
            blocked=False,
            blockReason=None,
            leftReasonCode=leftReasonCode,
            rightReasonCode=rightReasonCode,
        )

    @staticmethod
    def selectForDoor(candidateCommands, door):
        """!
        @brief 특정 문에 적용 가능한 후보 중 priority가 최소인 후보 1개를 선택한다(6.8절).

        @param candidateCommands list[CandidateCommand]
        @param door Door — LEFT 또는 RIGHT(조회 대상 문)
        @return tuple(ArbitrationCommand, Optional[str] reasonCode) — 후보 없으면 (NO_CHANGE, None)
        @exception ValueError 동일 최소 priority를 가진 후보가 2개 이상이면 발생(설계상 불변조건 위반)
        """
        applicable = [c for c in candidateCommands if c.door in (door, Door.BOTH)]
        if not applicable:
            return ArbitrationCommand.NO_CHANGE, None

        minPriority = min(c.priority for c in applicable)
        winners = [c for c in applicable if c.priority == minPriority]
        if len(winners) > 1:
            raise ValueError(
                f"IU-0005: {door.value} 문에 동일 priority({minPriority}) 후보가 {len(winners)}개 존재"
            )

        winner = winners[0]
        return winner.command, winner.reasonCode

    @staticmethod
    def buildBlockedResult(blockReason):
        """!
        @brief 차단된(blocked=True) ArbitrationResult를 만든다.

        @param blockReason str — "STATE_FAULT" 또는 "INPUT_INVALID"
        @return ArbitrationResult — 4필드 모두 NO_CHANGE/None, blocked=True
        """
        return ArbitrationResult(
            leftCommand=ArbitrationCommand.NO_CHANGE,
            rightCommand=ArbitrationCommand.NO_CHANGE,
            blocked=True,
            blockReason=blockReason,
            leftReasonCode=None,
            rightReasonCode=None,
        )
