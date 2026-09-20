"""!
@file isofix_forced_lock_monitor.py
@brief IU-0015(ARC-0015 ISOFIX 강제잠금 감시) — 좌/우 ISOFIX 완전 독립 판정 및 강제잠금 후보
       생성(신규, Phase3).

@par 관련 항목
- 요구사항: SWR-018
- 상세설계: ENG-SWE3-001 5.13절/6.15절/7장 결정표 M
"""

from ngv.domain.constants import (
    PRIORITY_ISOFIX_FORCED_LOCK,
    REASON_CODE_ISOFIX_LEFT,
    REASON_CODE_ISOFIX_RIGHT,
)
from ngv.domain.types import ArbitrationCommand, CandidateCommand, Door, ISOFIXLockResult


class IsofixForcedLockMonitor:
    """!
    @brief 좌/우 ISOFIX를 evaluateSide()로 완전 독립 판정한다(SWR-018(b) 구조적 보장).

    내부 상태 없음(순수 판정, ARC-0015 설계와 일치). 좌/우 호출 사이에 공유되는 변수가
    전혀 없어(6.15절, IU-0011.evaluateSide()와 동일한 패턴), 한쪽 도어의 판정이 반대쪽
    결정에 영향을 줄 수 없다.
    """

    def evaluate(self, isofixLeftField, isofixRightField):
        """!
        @brief 좌/우 ISOFIX 필드를 각각 독립적으로 판정한다.

        @param isofixLeftField FieldValidationResult[bool] — IU-0001 정규화 결과
        @param isofixRightField FieldValidationResult[bool] — IU-0001 정규화 결과
        @return ISOFIXLockResult{leftLockActive, rightLockActive, leftLockCandidate,
                rightLockCandidate, leftReasonCode, rightReasonCode}
        @exception ValueError 어느 한쪽이라도 None이면 발생
        """
        leftActive, leftCandidate, leftReason = self.evaluateSide(
            isofixLeftField, Door.LEFT, REASON_CODE_ISOFIX_LEFT
        )
        rightActive, rightCandidate, rightReason = self.evaluateSide(
            isofixRightField, Door.RIGHT, REASON_CODE_ISOFIX_RIGHT
        )
        return ISOFIXLockResult(
            leftLockActive=leftActive,
            rightLockActive=rightActive,
            leftLockCandidate=leftCandidate,
            rightLockCandidate=rightCandidate,
            leftReasonCode=leftReason,
            rightReasonCode=rightReason,
        )

    @staticmethod
    def evaluateSide(fieldResult, door, reasonCode):
        """!
        @brief 한쪽 문의 ISOFIX 필드만 보고 판정한다(다른 쪽 필드를 파라미터로 받지 않음).

        @param fieldResult FieldValidationResult[bool]
        @param door Door — LEFT 또는 RIGHT
        @param reasonCode str — 이 문에 고정 배정된 이유코드
        @return tuple(bool lockActive, Optional[CandidateCommand] lockCandidate,
                Optional[str] reasonCode)
        @exception ValueError fieldResult가 None이면 발생
        """
        if fieldResult is None:
            raise ValueError("IU-0015: isofixField must not be None")

        if fieldResult.valid and fieldResult.value is True:
            candidate = CandidateCommand(
                door=door, command=ArbitrationCommand.LOCK, priority=PRIORITY_ISOFIX_FORCED_LOCK, reasonCode=reasonCode
            )
            return True, candidate, reasonCode

        return False, None, None
