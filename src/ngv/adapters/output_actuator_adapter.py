"""!
@file output_actuator_adapter.py
@brief IU-0006(ARC-0006 출력 액추에이터 어댑터) — Phase1 최소 계약(패스스루).

Phase1 범위 밖: 실제 통신 프로토콜(CAN/LIN, HTTP 등)과 발행 실패 시 재시도/오류 반환 정책은
이후 Phase에서 정의한다(ENG-SWE3-001 13장) — 여기서는 만들지 않는다.

@par 관련 항목
- 요구사항: SWR-021(a) 전달 경로
- 상세설계: ENG-SWE3-001 5장
"""

from ngv.domain.types import PublishResult


class OutputActuatorAdapter:
    """!
    @brief 확정 출력(ConfirmedOutput)을 OEM-IF-005 문자열 payload로 값 변형 없이 변환·발행한다.
    """

    def publish(self, confirmedOutput):
        """!
        @brief 확정 출력을 발행한다(Phase1: 실제 I/O 없는 패스스루 스텁).

        @param confirmedOutput ConfirmedOutput — IU-0004.confirm()의 반환값
        @return PublishResult{success=True, payload={"lock_left":.., "lock_right":..}, errorReason=None}
        @exception 없음(Phase1)
        """
        payload = {
            "lock_left": confirmedOutput.left.value,
            "lock_right": confirmedOutput.right.value,
        }
        return PublishResult(success=True, payload=payload, errorReason=None)
