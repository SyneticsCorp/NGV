# 파이프라인 컨텍스트 원장

이 파일은 Main(오케스트레이팅 세션)과 서브에이전트(requirements-analyst, architecture-designer, detailed-designer, coding, integration-tester, sw-system-tester) 간 컨텍스트를 연결하기 위한 공유 로그입니다. **각 서브에이전트는 작업 시작 시 이 파일을 읽고, 작업을 마치면 이 파일 하단에 요약을 append합니다.** Main은 매번 전체 맥락을 프롬프트에 재작성하는 대신 이 파일을 참조하도록 지시해 프롬프트 길이(토큰)를 줄입니다.

## ID 레지스트리 (다음 사용 가능 번호 — 새 ID를 부여하기 전에 반드시 확인)

| 접두사 | 의미 | 다음 사용 가능 번호 | 비고 |
| --- | --- | --- | --- |
| `SWR-` | 소프트웨어 요구사항(SWE.1) | `0022` (Phase 2까지 005~009, 013, 017, 021 사용됨) | OEM 추적성 힌트가 있는 SWR 번호는 힌트를 우선 사용 — 빈 번호(019 등)는 향후 Phase에서 채워질 수 있음 |
| `IF-` | 인터페이스 카탈로그(SWE.2 전용 — SWE.1은 더 이상 이 번호를 부여하지 않음, `requirements-analysis/requirement-schema.md` 참고) | `0020` | Phase 1: 0001~0012, Phase 2: 0013~0019 |
| `ARC-` | 아키텍처 컴포넌트(SWE.2) | `0014` | Phase 1: 0001~0009, Phase 2: 0010~0013 |
| `IU-` | 구현 단위(SWE.3) | `0010` | Phase 1: 0001~0009 (Phase 2분 아직 미배정) |
| `IT-` | 통합시험 케이스(SWE.5) | `0044` | Phase 1: 0001~0043 |
| `ST-FUNC-`/`ST-NFR-` | 시스템시험 케이스(SWE.6) | `ST-FUNC-0014` | Phase 1: ST-FUNC-0001~0013 |
| `ENG-REV-001` 세션/지적사항 | 인스펙션(Common/SUP.1) | SES-0002 / F-0002 | Phase 1: SES-0001/F-0001 사용 |

## 누적 갭 (OEM-A 확인 필요 등 — 여러 Phase에 걸쳐 이월됨, 절대 조용히 해소하지 말 것)

1. **DEGRADED/FAULT 히스테리시스 없음(즉시 재판정)** — OEM 원문 미기재, Phase 1 아키텍처 단계에서 근거와 함께 결정(병렬-상호배타-FAULT우선). 상세설계에서 재확인 후 채택.
2. **source_timestamp_s 상한/단조성 판정식 미확정** — OEM 원문 미기재. 하한(0.0)만 검증됨.
3. **경고코드(reason_code) 실제 카탈로그 미확정** — OEM-IF-006에 정의 없음. 현재 "정의된 타입의 비공백 값" 기준으로만 판정.
4. **SWR-008(crash_status PENDING 처리)은 추론 요구사항** — OEM-SR-001 원문에 직접 기술 없음, OEM-A 확인 필요.
5. **SWR-006의 override 실제 출력 전환 여부 미기재** — OEM-FR-003 수용기준은 "override 상태/이유코드 생성"만 요구, 실제 RELEASE 전환은 원문 미기재.
6. **SWR-006의 ASIL B/QM 혼합 분류** — OEM 추적성 힌트가 OEM-SR-002(ASIL B)와 OEM-FR-003(QM)을 SWR-006 하나로 묶음. 아키텍처에서 ARC-0012로 격리했으나 근본적으로는 재검토 여지가 있음.
7. **releaseReRequested 채널(ARC-0012 입력)이 실제 신호에 미연결** — OEM-FR-001(운전자 명령, Phase 4 예정) 분석 전까지 placeholder(항상 False).
8. **ST-FUNC-0009(제안 케이스)의 정식 채택 여부** — 사용자 미확정, 현재 참고용/필수 합격기준 제외로 분리 표기됨.
9. **시스템 테스트 진입점**: `evaluateCycle()`이 아니라 `InputValidationAdapter.handleCycle()`(원시 입력 전체 체인) 사용 — Phase 1에서 근거와 함께 결정, 이후 Phase도 이 방식을 유지.

## 문제 해결 이력 (problem-solver가 개입한 경우)

(아직 없음 — `problem-solver` 서브에이전트가 개입할 때마다 이 절에 날짜/증상/재발 횟수/근본원인/조치/검증 결과를 append합니다.)

## 게이트별 진행 로그

### Phase 1 — 안전 커널 (SWR-013, SWR-021) — 완료, `main`에 병합(PR #4, 커밋 `6e97be6`)

- SWE.1(2026-09-18, requirements-analyst): SWR-013(입력유효성/freshness), SWR-021(sensor_fault fail-freeze) 작성. `ENG-SWE1-001` 최초 작성.
- SWE.2(2026-09-18, architecture-designer): 헥사고날+컴포넌트기반/모니터-액추에이터 선택. ARC-0001~0009, IF-0001~0012. Command Arbiter/로거 확장 골격만 정의.
- SWE.3(2026-09-18, detailed-designer): IU-0001~0009 함수 계약. 평가주기 50ms, 부팅 초기값 LOCK/LOCK 확정.
- 구현(2026-09-18, coding): `src/ngv/` 최초 작성. 52개 단위테스트, 품질 게이트 전부 통과.
- SWE.5(2026-09-18, integration-tester): 43개 케이스, 문장/분기/함수/Call 커버리지 100%.
- SWE.6(2026-09-18, sw-system-tester): 13개 케이스(ST-FUNC-0001~0013), 진입점을 `handleCycle()`로 결정.

### Phase 2 — 안전 긴급 대응 (SWR-005/006/007/008/009/017) — 진행 중, 브랜치 `phase-2-emergency-response`

- SWE.1(2026-09-19, requirements-analyst): SWR-005~009, 017 작성. `ENG-SWE1-001` v0.2. **IF- 번호 충돌 발견**(SWE.1이 IF-0003~0005를 독자 부여해 SWE.2의 기존 IF-0003/0004와 충돌) → Main이 직접 정정(SWE.1은 더 이상 IF- 번호를 부여하지 않도록 스킬 규칙 수정, `requirements-analysis/requirement-schema.md`).
- SWE.2(2026-09-19, architecture-designer): ARC-0010(충돌감시)/0011(접근위험평가)/0012(override판정기)/0013(화재등감시) 신규, IF-0013~0019 신규(위 정정된 번호 정책 적용), Command Arbiter 우선순위 규칙 3종 구현(충돌>접근위험>화재등). **서브에이전트가 `ENG-TRC-001` Architecture 열 갱신 전에 사용자에 의해 중단됨** → Main이 아키텍처 문서 12/14장 매핑을 직접 대조해 TRC-001 7개 행 완성(2026-09-19).
- SWE.3: 아직 시작 안 함(다음 게이트).
- 구현/SWE.5/SWE.6: 아직 시작 안 함.

### 이번 세션 인프라 변경 (2026-09-19)

- LibreOffice 설치(winget). 스킬 자체 recalc.py/render 래퍼는 Windows에서 작동 안 함(AF_UNIX 소켓 가정) — `soffice.exe --headless --convert-to pdf`를 직접 호출하는 방식으로 우회 가능함을 확인.
- 7개 파이프라인 서브에이전트를 `model: inherit`에서 `model: sonnet`으로 고정(Main이 다른 모델을 쓰더라도 이 7개는 품질 유지).
- `problem-solver` 서브에이전트 신설(`model: fable`) — 동일 문제가 2회 이상 반복될 때 Main이 호출.
- Phase 3~5는 사용자 승인 없이 자동으로 PR·머지 진행(사용자 명시적 허가, 2026-09-19).
