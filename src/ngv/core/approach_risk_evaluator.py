"""!
@file approach_risk_evaluator.py
@brief IU-0011(ARC-0011 접근위험 평가) — 좌/우 접근위험 완전 독립 판정 및 억제 후보 생성(신규, Phase2).

@par 관련 항목
- 요구사항: SWR-005, SWR-009
- 상세설계: ENG-SWE3-001 5.5절/6.10절/7장 결정표 F
"""

from ngv.domain.constants import (
    PRIORITY_APPROACH_RISK,
    REASON_CODE_APPROACH_RISK_LEFT,
    REASON_CODE_APPROACH_RISK_RIGHT,
)
from ngv.domain.types import ApproachRiskResult, ArbitrationCommand, CandidateCommand, Door


class ApproachRiskEvaluator:
    """!
    @brief 좌/우 접근위험을 evaluateSide()로 완전 독립 판정한다(SWR-009 구조적 보장).

    내부 상태 없음(순수 판정, ARC-0011 설계와 일치). 좌/우 호출 사이에 공유되는 변수가
    전혀 없어(6.10절), 한쪽 도어의 판정이 반대쪽 결정에 영향을 줄 수 없다.
    """

    def evaluate(self, leftApproachRiskField, rightApproachRiskField):
        """!
        @brief 좌/우 접근위험 필드를 각각 독립적으로 판정한다.

        @param leftApproachRiskField FieldValidationResult[bool] — IU-0001 정규화 결과
        @param rightApproachRiskField FieldValidationResult[bool] — IU-0001 정규화 결과
        @return ApproachRiskResult{leftRiskActive, rightRiskActive, leftSuppressCandidate,
                rightSuppressCandidate, leftReasonCode, rightReasonCode}
        @exception ValueError 어느 한쪽이라도 None이면 발생
        """
        leftActive, leftCandidate, leftReason = self.evaluateSide(
            leftApproachRiskField, Door.LEFT, REASON_CODE_APPROACH_RISK_LEFT
        )
        rightActive, rightCandidate, rightReason = self.evaluateSide(
            rightApproachRiskField, Door.RIGHT, REASON_CODE_APPROACH_RISK_RIGHT
        )
        return ApproachRiskResult(
            leftRiskActive=leftActive,
            rightRiskActive=rightActive,
            leftSuppressCandidate=leftCandidate,
            rightSuppressCandidate=rightCandidate,
            leftReasonCode=leftReason,
            rightReasonCode=rightReason,
        )

    @staticmethod
    def evaluateSide(fieldResult, door, reasonCode):
        """!
        @brief 한쪽 문의 접근위험 필드만 보고 판정한다(다른 쪽 필드를 파라미터로 받지 않음).

        @param fieldResult FieldValidationResult[bool]
        @param door Door — LEFT 또는 RIGHT
        @param reasonCode str — 이 문에 고정 배정된 이유코드
        @return tuple(bool riskActive, Optional[CandidateCommand] suppressCandidate,
                Optional[str] reasonCode)
        @exception ValueError fieldResult가 None이면 발생
        """
        if fieldResult is None:
            raise ValueError("IU-0011: approachRiskField must not be None")

        if fieldResult.valid and fieldResult.value is True:
            candidate = CandidateCommand(
                door=door, command=ArbitrationCommand.LOCK, priority=PRIORITY_APPROACH_RISK, reasonCode=reasonCode
            )
            return True, candidate, reasonCode

        return False, None, None
