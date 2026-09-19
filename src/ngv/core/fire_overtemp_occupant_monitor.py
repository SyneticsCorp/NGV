"""!
@file fire_overtemp_occupant_monitor.py
@brief IU-0013(ARC-0013 화재/과온/탑승 감시) — OR 판정 및 강제해제 후보 생성(신규, Phase2).

@par 관련 항목
- 요구사항: SWR-017
- 상세설계: ENG-SWE3-001 5.7절/6.12절/7장 결정표 H
"""

from ngv.domain.constants import (
    PRIORITY_FIRE_OVERTEMP_OCCUPANT,
    REASON_CODE_ADULT_PRESENT_DETECTED,
    REASON_CODE_FIRE_DETECTED,
    REASON_CODE_FORCED_RELEASE,
    REASON_CODE_OVERTEMPERATURE_DETECTED,
)
from ngv.domain.types import ArbitrationCommand, CandidateCommand, Door, ForcedReleaseResult


class FireOvertempOccupantMonitor:
    """!
    @brief 화재/과온/탑승 3개 필드를 OR로 결합해 강제해제 후보를 만든다.

    내부 상태 없음(순수 판정, ARC-0013 설계와 일치). 3개 필드는 상호 우선순위 없이 대칭 판정된다.
    """

    def evaluate(self, fireField, overtempField, adultField):
        """!
        @brief 3개 필드를 각각 독립 판정해 triggeredReasonCodes를 모두 모은다.

        @param fireField FieldValidationResult[bool] — IU-0001 정규화 결과
        @param overtempField FieldValidationResult[bool] — IU-0001 정규화 결과
        @param adultField FieldValidationResult[bool] — IU-0001 정규화 결과
        @return ForcedReleaseResult{triggered, releaseCandidate, triggeredReasonCodes}
        @exception ValueError 어느 하나라도 None이면 발생
        """
        if fireField is None or overtempField is None or adultField is None:
            raise ValueError("IU-0013: field must not be None")

        codes = []
        for fieldResult, reasonCode in (
            (fireField, REASON_CODE_FIRE_DETECTED),
            (overtempField, REASON_CODE_OVERTEMPERATURE_DETECTED),
            (adultField, REASON_CODE_ADULT_PRESENT_DETECTED),
        ):
            if fieldResult.valid and fieldResult.value is True:
                codes.append(reasonCode)

        triggered = len(codes) > 0
        releaseCandidate = self.buildReleaseCandidate() if triggered else None
        return ForcedReleaseResult(triggered=triggered, releaseCandidate=releaseCandidate, triggeredReasonCodes=codes)

    @staticmethod
    def buildReleaseCandidate():
        """!
        @brief triggered=True일 때의 강제해제 후보를 만든다(중복 생성 코드 제거용 헬퍼).
        @return CandidateCommand(door=BOTH, command=RELEASE, priority=PRIORITY_FIRE_OVERTEMP_OCCUPANT,
                reasonCode=FORCED_RELEASE)
        """
        return CandidateCommand(
            door=Door.BOTH,
            command=ArbitrationCommand.RELEASE,
            priority=PRIORITY_FIRE_OVERTEMP_OCCUPANT,
            reasonCode=REASON_CODE_FORCED_RELEASE,
        )
