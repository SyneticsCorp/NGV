"""!
@file vehicle_speed_auto_lock_monitor.py
@brief IU-0014(ARC-0014 차속 자동주행잠금 감시) — 차속 3km/h 임계 판정 및 자동주행잠금 후보
       생성(신규, Phase3).

@par 관련 항목
- 요구사항: SWR-003
- 상세설계: ENG-SWE3-001 5.12절/6.14절/7장 결정표 L
"""

from ngv.domain.constants import (
    AUTO_DRIVE_LOCK_SPEED_THRESHOLD_KPH,
    PRIORITY_AUTO_DRIVE_LOCK,
    REASON_CODE_AUTO_DRIVE_LOCK,
)
from ngv.domain.types import ArbitrationCommand, CandidateCommand, Door, VehicleSpeedLockResult


class VehicleSpeedAutoLockMonitor:
    """!
    @brief vehicle_speed_kph를 결정표 L에 따라 판정하고 임계값 이상일 때만 잠금 후보를 만든다.

    내부 상태 없음(순수 판정, ARC-0014 설계와 일치).
    """

    def evaluate(self, vehicleSpeedField, nowS):
        """!
        @brief vehicle_speed_kph 필드를 판정해 VehicleSpeedLockResult를 만든다.

        @param vehicleSpeedField FieldValidationResult[float] — IU-0001 정규화 결과
        @param nowS float — 현재 이 알고리즘에서는 미사용(향후 확장 예약)
        @return VehicleSpeedLockResult{locked, lockCandidate}
        @exception ValueError vehicleSpeedField가 None이면 발생
        """
        del nowS  # 6.14절 알고리즘은 nowS를 판정에 사용하지 않는다(향후 확장 예약 인자).
        if vehicleSpeedField is None:
            raise ValueError("IU-0014: vehicleSpeedField must not be None")

        if vehicleSpeedField.valid and vehicleSpeedField.value >= AUTO_DRIVE_LOCK_SPEED_THRESHOLD_KPH:
            return VehicleSpeedLockResult(locked=True, lockCandidate=self.buildLockCandidate())

        return VehicleSpeedLockResult(locked=False, lockCandidate=None)

    @staticmethod
    def buildLockCandidate():
        """!
        @brief 임계값 이상일 때의 자동주행잠금 후보를 만든다(중복 생성 코드 제거용 헬퍼).
        @return CandidateCommand(door=BOTH, command=LOCK, priority=PRIORITY_AUTO_DRIVE_LOCK,
                reasonCode=AUTO_DRIVE_LOCK)
        """
        return CandidateCommand(
            door=Door.BOTH,
            command=ArbitrationCommand.LOCK,
            priority=PRIORITY_AUTO_DRIVE_LOCK,
            reasonCode=REASON_CODE_AUTO_DRIVE_LOCK,
        )
