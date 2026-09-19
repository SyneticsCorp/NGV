"""!
@file approach_risk_override_manager.py
@brief IU-0012(ARC-0012 접근위험 override 판정기) — 문별 10초 재입력 override 판정(신규, Phase2).

유일하게 내부 상태(firstSuppressedAtLeftS/firstSuppressedAtRightS)를 보유하는 Phase2 신규
구현 단위다(ENG-SWE3-001 5.6절/8.6절).

@par 관련 항목
- 요구사항: SWR-006
- 상세설계: ENG-SWE3-001 5.6절/6.11절/7장 결정표 G/8.6절
"""

from ngv.domain.constants import (
    OVERRIDE_WINDOW_S,
    REASON_CODE_APPROACH_RISK_OVERRIDE_LEFT,
    REASON_CODE_APPROACH_RISK_OVERRIDE_RIGHT,
)
from ngv.domain.types import OverrideDecision


class ApproachRiskOverrideManager:
    """!
    @brief 문별 최초 억제 시각을 단독 소유하고, 재입력 시각 대비 10초 이내 여부로 override를 판정한다.
    """

    def __init__(self):
        """!
        @brief 억제 이력 없음(None, None)으로 초기화한다.
        """
        self.firstSuppressedAtLeftS = None
        self.firstSuppressedAtRightS = None

    def decide(self, leftRiskActive, rightRiskActive, leftReleaseReRequested, rightReleaseReRequested, nowS):
        """!
        @brief 좌/우 문을 완전 독립적으로 판정한다(6.11절 알고리즘).

        @param leftRiskActive bool — IU-0011 산출값
        @param rightRiskActive bool — IU-0011 산출값
        @param leftReleaseReRequested bool — IU-0009.composeReleaseReRequested()의 placeholder
        @param rightReleaseReRequested bool — 상동
        @param nowS float — 단조 증가 현재 평가주기 시각(초)
        @return OverrideDecision{leftOverrideActive, rightOverrideActive,
                leftOverrideReasonCode, rightOverrideReasonCode}
        @exception 없음(방어적 — 6장 타이머 갱신 규칙이 riskActive=False를 항상 안전하게 처리)
        """
        leftActive, leftReason, self.firstSuppressedAtLeftS = self.decideSide(
            leftRiskActive,
            leftReleaseReRequested,
            self.firstSuppressedAtLeftS,
            nowS,
            REASON_CODE_APPROACH_RISK_OVERRIDE_LEFT,
        )
        rightActive, rightReason, self.firstSuppressedAtRightS = self.decideSide(
            rightRiskActive,
            rightReleaseReRequested,
            self.firstSuppressedAtRightS,
            nowS,
            REASON_CODE_APPROACH_RISK_OVERRIDE_RIGHT,
        )
        return OverrideDecision(
            leftOverrideActive=leftActive,
            rightOverrideActive=rightActive,
            leftOverrideReasonCode=leftReason,
            rightOverrideReasonCode=rightReason,
        )

    @staticmethod
    def decideSide(riskActive, releaseReRequested, firstSuppressedAtS, nowS, reasonCode):
        """!
        @brief 한쪽 문의 타이머 갱신과 override 판정을 함께 수행한다.

        @param riskActive bool
        @param releaseReRequested bool
        @param firstSuppressedAtS Optional[float] — 이 문의 현재 저장된 최초 억제 시각
        @param nowS float
        @param reasonCode str — 이 문에 고정 배정된 override 이유코드
        @return tuple(bool overrideActive, Optional[str] overrideReasonCode,
                Optional[float] 갱신된 firstSuppressedAtS)
        """
        if riskActive:
            if firstSuppressedAtS is None:
                firstSuppressedAtS = nowS
        else:
            firstSuppressedAtS = None

        if riskActive and releaseReRequested and firstSuppressedAtS is not None:
            elapsedS = nowS - firstSuppressedAtS
            if elapsedS <= OVERRIDE_WINDOW_S:
                return True, reasonCode, firstSuppressedAtS

        return False, None, firstSuppressedAtS

    def reset(self):
        """!
        @brief 억제 이력을 초기화한다(부팅/재시작 시 fail-safe 방향과 일치, 8.6절).
        @return None
        """
        self.firstSuppressedAtLeftS = None
        self.firstSuppressedAtRightS = None
