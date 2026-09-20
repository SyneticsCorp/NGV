"""!
@file ignition_off_release_monitor.py
@brief IU-0016(ARC-0016 ignition-off 해제 후보 생성) — ignition_on=FALSE 판정 및 해제 후보
       생성(신규, Phase3). OFF 상태 값 자체는 소유하지 않는다(IU-0003 소유, 2장 참조).

@par 관련 항목
- 요구사항: SWR-020
- 상세설계: ENG-SWE3-001 5.14절/6.16절/7장 결정표 N
"""

from ngv.domain.constants import PRIORITY_IGNITION_OFF_RELEASE, REASON_CODE_IGNITION_OFF
from ngv.domain.types import ArbitrationCommand, CandidateCommand, Door, IgnitionOffReleaseResult


class IgnitionOffReleaseMonitor:
    """!
    @brief ignition_on을 결정표 N에 따라 판정하고 유효한 FALSE일 때만 해제 후보를 만든다.

    내부 상태 없음(순수 판정, ARC-0016 설계와 일치). IU-0003의 OFF 판정 보류 결정(8.8절)과
    정확히 대칭인 기준(valid=False이면 후보 미생성)을 적용한다.
    """

    def evaluate(self, ignitionOnField, nowS):
        """!
        @brief ignition_on 필드를 판정해 IgnitionOffReleaseResult를 만든다.

        @param ignitionOnField FieldValidationResult[bool] — IU-0001 정규화 결과
        @param nowS float — 현재 이 알고리즘에서는 미사용(향후 확장 예약)
        @return IgnitionOffReleaseResult{off, releaseCandidate}
        @exception ValueError ignitionOnField가 None이면 발생
        """
        del nowS  # 6.16절 알고리즘은 nowS를 판정에 사용하지 않는다(향후 확장 예약 인자).
        if ignitionOnField is None:
            raise ValueError("IU-0016: ignitionOnField must not be None")

        if ignitionOnField.valid and ignitionOnField.value is False:
            return IgnitionOffReleaseResult(off=True, releaseCandidate=self.buildReleaseCandidate())

        return IgnitionOffReleaseResult(off=False, releaseCandidate=None)

    @staticmethod
    def buildReleaseCandidate():
        """!
        @brief off=True일 때의 ignition-off 해제 후보를 만든다(중복 생성 코드 제거용 헬퍼).
        @return CandidateCommand(door=BOTH, command=RELEASE, priority=PRIORITY_IGNITION_OFF_RELEASE,
                reasonCode=IGNITION_OFF)
        """
        return CandidateCommand(
            door=Door.BOTH,
            command=ArbitrationCommand.RELEASE,
            priority=PRIORITY_IGNITION_OFF_RELEASE,
            reasonCode=REASON_CODE_IGNITION_OFF,
        )
