"""!
@file freshness_monitor.py
@brief IU-0002(ARC-0002 Freshness 모니터) — freshness(최신성) 판정.

@par 관련 항목
- 요구사항: SWR-013(a)
- 상세설계: ENG-SWE3-001 5장/6.3절/8.4절
"""

import math

from ngv.domain.constants import FRESHNESS_STALE_THRESHOLD_S
from ngv.domain.types import FreshnessResult


class FreshnessMonitor:
    """!
    @brief 최근 유효 source_timestamp_s 이후 경과시간을 추적해 stale 여부를 판정한다.

    내부 상태(lastValidTimestampS)는 이 클래스가 단독으로 소유한다(ENG-SWE3-001 4장/8.4절).
    """

    def __init__(self):
        """!
        @brief 부팅 기본값(유효 표본 없음)으로 초기화한다.
        """
        self.lastValidTimestampS = None

    def evaluate(self, sourceTimestampField, nowS):
        """!
        @brief freshness를 판정한다.

        @param sourceTimestampField FieldValidationResult[float] — IU-0001이 검증한 source_timestamp_s
        @param nowS float — 단조 증가 현재 평가주기 시각(초)
        @return FreshnessResult{stale, elapsedS, detectedAtS}
        @exception 없음 — 사전조건 위반 시에도 방어적으로 동작(5장 계약)
        """
        if sourceTimestampField.valid:
            self.lastValidTimestampS = sourceTimestampField.value

        if self.lastValidTimestampS is None:
            elapsedS = math.inf
        else:
            elapsedS = nowS - self.lastValidTimestampS

        stale = elapsedS > FRESHNESS_STALE_THRESHOLD_S
        return FreshnessResult(stale=stale, elapsedS=elapsedS, detectedAtS=nowS)

    def reset(self):
        """!
        @brief 내부 상태를 부팅 기본값(유효 표본 없음)으로 초기화한다.
        @return None
        """
        self.lastValidTimestampS = None
