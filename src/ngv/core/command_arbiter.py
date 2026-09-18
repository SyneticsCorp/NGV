"""!
@file command_arbiter.py
@brief IU-0005(ARC-0005 Command Arbiter) — Phase1 최소 계약(상태/입력유효성 게이트만).

Phase1 범위 밖: 우선순위 규칙 체인(Strategy/Chain of Responsibility)의 개별 규칙 구현체는
candidateCommands를 채우는 이후 Phase에서 확장한다(ENG-SWE3-001 5장) — 여기서는 만들지 않는다.

@par 관련 항목
- 요구사항: SWR-021(a) 경로에 간접 관여(확장 골격)
- 상세설계: ENG-SWE3-001 5장, 7장 결정표 D
"""

from ngv.domain.constants import BLOCK_REASON_INPUT_INVALID, BLOCK_REASON_STATE_FAULT
from ngv.domain.types import ArbitrationCommand, ArbitrationResult, SystemState


class CommandArbiter:
    """!
    @brief Phase1: state==FAULT 또는 inputValid==False일 때만 후보 커맨드를 차단하는 게이트.
    """

    def arbitrate(self, stateResult, inputValid, candidateCommands=None):
        """!
        @brief 상태/입력유효성 게이트를 적용한다(Phase1 최소 동작).

        @param stateResult StateResult — IU-0003.evaluate()의 반환값
        @param inputValid bool — 7장 결정표 D의 합성 결과
        @param candidateCommands list — Phase1은 항상 빈 리스트로 호출됨
        @return ArbitrationResult{leftCommand, rightCommand, blocked, blockReason}
        @exception NotImplementedError candidateCommands가 비어있지 않으면 발생
        """
        if candidateCommands:
            raise NotImplementedError("Command Arbiter 우선순위 규칙 체인은 Phase 2 이후 구현 예정")

        if stateResult.state == SystemState.FAULT:
            return self.buildBlockedResult(BLOCK_REASON_STATE_FAULT)
        if not inputValid:
            return self.buildBlockedResult(BLOCK_REASON_INPUT_INVALID)

        return ArbitrationResult(
            leftCommand=ArbitrationCommand.NO_CHANGE,
            rightCommand=ArbitrationCommand.NO_CHANGE,
            blocked=False,
            blockReason=None,
        )

    @staticmethod
    def buildBlockedResult(blockReason):
        """!
        @brief 차단된(blocked=True) ArbitrationResult를 만든다.

        @param blockReason str — "STATE_FAULT" 또는 "INPUT_INVALID"
        @return ArbitrationResult — 두 축 모두 NO_CHANGE, blocked=True
        """
        return ArbitrationResult(
            leftCommand=ArbitrationCommand.NO_CHANGE,
            rightCommand=ArbitrationCommand.NO_CHANGE,
            blocked=True,
            blockReason=blockReason,
        )
