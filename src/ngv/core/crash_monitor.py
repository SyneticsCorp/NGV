"""!
@file crash_monitor.py
@brief IU-0010(ARC-0010 충돌 감시) — crash_status 판정 및 긴급해제 후보 생성(신규, Phase2).

@par 관련 항목
- 요구사항: SWR-007, SWR-008
- 상세설계: ENG-SWE3-001 5.4절/6.9절/7장 결정표 E
"""

from ngv.domain.constants import PRIORITY_CRASH, REASON_CODE_CRASH_CONFIRMED
from ngv.domain.types import ArbitrationCommand, CandidateCommand, CrashEvaluationResult, CrashStatus, Door


class CrashMonitor:
    """!
    @brief crash_status를 결정표 E에 따라 판정하고 CONFIRMED일 때만 긴급해제 후보를 만든다.

    내부 상태 없음(순수 판정, ARC-0010 설계와 일치).
    """

    def evaluate(self, crashStatusField, nowS):
        """!
        @brief crash_status 필드를 판정해 CrashEvaluationResult를 만든다.

        @param crashStatusField FieldValidationResult[CrashStatus] — IU-0001 정규화 결과
        @param nowS float — 현재 이 알고리즘에서는 미사용(향후 확장 예약)
        @return CrashEvaluationResult{status, releaseCandidate, pendingHoldApplied}
        @exception ValueError crashStatusField가 None이면 발생
        """
        del nowS  # 6.9절 알고리즘은 nowS를 판정에 사용하지 않는다(향후 확장 예약 인자).
        if crashStatusField is None:
            raise ValueError("IU-0010: crashStatusField must not be None")

        if not crashStatusField.valid:
            return self.buildResult(CrashStatus.NONE, None, False)

        if crashStatusField.value == CrashStatus.CONFIRMED:
            candidate = CandidateCommand(
                door=Door.BOTH,
                command=ArbitrationCommand.RELEASE,
                priority=PRIORITY_CRASH,
                reasonCode=REASON_CODE_CRASH_CONFIRMED,
            )
            return self.buildResult(CrashStatus.CONFIRMED, candidate, False)

        if crashStatusField.value == CrashStatus.PENDING:
            return self.buildResult(CrashStatus.PENDING, None, True)

        return self.buildResult(CrashStatus.NONE, None, False)

    @staticmethod
    def buildResult(status, releaseCandidate, pendingHoldApplied):
        """!
        @brief CrashEvaluationResult를 조립한다(중복 생성 코드 제거용 헬퍼).

        @param status CrashStatus
        @param releaseCandidate Optional[CandidateCommand]
        @param pendingHoldApplied bool
        @return CrashEvaluationResult
        """
        return CrashEvaluationResult(
            status=status, releaseCandidate=releaseCandidate, pendingHoldApplied=pendingHoldApplied
        )
