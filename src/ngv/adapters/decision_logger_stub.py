"""!
@file decision_logger_stub.py
@brief IU-0008(ARC-0008 결정 로거 스텁) — Phase1 최소 계약(no-op).

Phase1 범위 밖: 실제 저장/재생 로직(최근 100건 인메모리 링버퍼, 결정론 재생)은
Phase5에서 구현한다(ENG-SWE3-001 5장/13장) — 여기서는 만들지 않는다.

@par 관련 항목
- 요구사항: OEM-NFR-001/002(향후 Phase 예약)
- 상세설계: ENG-SWE3-001 5장
"""


class DecisionLoggerStub:
    """!
    @brief 결정 로그 기록 포트(Phase1: no-op — 입력을 검증·저장하지 않는다).
    """

    def log(self, entry):
        """!
        @brief 결정 로그 항목을 기록한다(Phase1: no-op).

        @param entry DecisionLogEntry — 기록 대상 항목(Phase1은 사용하지 않음)
        @return None
        @exception 없음(Phase1 오류 계약 없음)
        """
        del entry  # Phase1은 no-op — 입력을 검증·저장하지 않는다(ENG-SWE3-001 5장).
        return None
