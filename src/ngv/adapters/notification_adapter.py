"""!
@file notification_adapter.py
@brief IU-0007(ARC-0007 표시/경고 어댑터) — Phase1 최소 계약(패스스루).

Phase1 범위 밖: priority_reason/input_validity 필드, 직렬화 실패 시 HTTP 500 처리는
실제 Web 어댑터 구현 시점(이후 Phase)으로 이월한다(ENG-SWE3-001 5장/9장) — 여기서는 만들지 않는다.

@par 관련 항목
- 요구사항: SWR-021(b)
- 상세설계: ENG-SWE3-001 5장
"""

from ngv.domain.types import PublishResult


class NotificationAdapter:
    """!
    @brief 상태 판정 결과(StateResult)를 OEM-IF-006 state/reason_code payload로 값 변형 없이 변환·발행한다.
    """

    def publishWarning(self, stateResult):
        """!
        @brief 상태/경고코드를 발행한다(Phase1: 실제 I/O 없는 패스스루 스텁).

        @param stateResult StateResult — IU-0003.evaluate()의 반환값
        @return PublishResult{success=True, payload={"state":.., "reason_code":..}, errorReason=None}
        @exception 없음(Phase1)
        """
        payload = {
            "state": stateResult.state.value,
            "reason_code": stateResult.warningReasonCode,
        }
        return PublishResult(success=True, payload=payload, errorReason=None)
