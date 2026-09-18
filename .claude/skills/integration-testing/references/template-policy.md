# 템플릿 적용 정책

## 지정 템플릿

| Template ID | 파일 | 용도 |
| --- | --- | --- |
| TPL-SWE5-001 | `WP_Templates/Engineering/SoftwareComponentVerificationAndIntegrationVerification/TPL-SWE5-001_SW 통합전략 및 통합시험 명세서 템플릿.docx` | 통합전략 및 통합시험 명세서 본문 |
| TPL-SWE5-002 | `WP_Templates/Engineering/SoftwareComponentVerificationAndIntegrationVerification/TPL-SWE5-002_SW 통합시험 케이스 템플릿.xlsx` | 통합시험 케이스 |
| TPL-SWE5-003 | `WP_Templates/Engineering/SoftwareComponentVerificationAndIntegrationVerification/TPL-SWE5-003_SW 통합시험 결과서 템플릿.xlsx` | 통합시험 결과서 |

전체 등록 정보는 `WP_Templates/PRC-TPL-001_표준 산출물 양식 등록부.xlsx`에 있습니다. `Template Register` 시트에는 TPL-SWE5-001 한 행만 있고(세 산출물이 " / "로 나열됨), `Engineering Template Files` 시트에는 세 Template ID가 각각 개별 행으로 등록되어 있습니다 — 등록부만 보고 002/003의 존재를 누락하지 않도록 `Engineering Template Files` 시트도 함께 확인하세요.

## 파일명/산출물 ID 규칙

- `ENG-SWE5-001_SW 통합전략 및 통합시험 명세서.docx`, `ENG-SWE5-002_SW 통합시험 케이스.xlsx`, `ENG-SWE5-003_SW 통합시험 결과서.xlsx` (`TPL-*` → `ENG-*` 규칙, 다른 스킬과 동일).
- 통합시험 케이스 ID: `IT-<일련번호>`(예: `IT-0007`), 4자리 0채움. 이미 프로젝트에 다른 접두사가 쓰이고 있다면 그것을 따르세요.
- 템플릿을 복사한 뒤 이름을 바꿔 작성하고, 원본 템플릿 파일은 수정하지 않습니다.
- 저장 위치 기본 제안: `Deliverables/Engineering/SoftwareComponentVerificationAndIntegrationVerification/` (확정된 프로젝트 관례가 아니라 제안값).

## 작성 방법

- **DOCX(TPL-SWE5-001)**: anthropic-skills:docx 스킬로 작성합니다. 장/절 제목은 그대로 유지하고, "작성 안내" 서술형 가이드를 실제 내용으로 교체합니다.
- **XLSX(TPL-SWE5-002/003)**: anthropic-skills:xlsx 스킬로 작성합니다. 기존 시트/열 구조를 그대로 유지하고, 실제 데이터는 **10행부터** 입력합니다.

## TPL-SWE5-001 목차 (변경 없이 그대로 사용)

1. 목적 및 적용범위 (1.1 목적 / 1.2 적용범위 / 1.3 적용경계)
2. 통합 원칙
3. **통합 항목과 순서** — 통합 항목 ID, 선행조건, 의존성, 순서, 담당, 계획 베이스라인. `ENG-SWE2-001` 11장(통합 전략)의 순서를 그대로 옮겨옵니다(`test-basis-and-order.md`).
4. 환경 및 형상
5. **진입 및 종료 기준** — 각 통합 단계의 시작/중단/재개/완료 판정 기준. **함수 커버리지 100%, Call 커버리지 100%를 이 장의 종료 기준으로 명시**합니다(`coverage-criteria.md`).
6. **통합시험 케이스 요약** — 인터페이스와 통합 위험을 다루는 시험 ID, 추적 대상, 기대결과, 자동화 여부 요약.
7. **시험 설계기법** — 경계값, 동등분할, 결정표, 상태전이 등 기법의 선정 근거와 적용 대상. **여기에 함수/Call 커버리지 목표와 측정 방법의 근거도 함께 기록**합니다(템플릿에 별도 "커버리지 기준" 절이 없으므로).
8. 실행 및 결과 기록 규칙
9. 회귀 전략
10. 실패 및 편차 처리
11. **추적성과 보고** — 아키텍처 인터페이스, 시험 케이스, 실행 결과, 결함, 보고서의 연결.
12. 적용 한계 — 통합시험으로 확인하지 못하는 범위(시스템/HIL/차량/양산 환경 등)를 명시.
13. 추적성 — 입력 설계/형상, 시험 명세, 결과/결함 기록의 양방향 추적(11장과 별개 절 — 템플릿 원문 그대로).
14. 참고자료

## TPL-SWE5-002 (통합시험 케이스) 시트 구조

### 시트 `Integration Cases`

| Test ID | Trace | Integration Item | Stimulus | Expected Result | Technique | Automation |
| --- | --- | --- | --- | --- | --- | --- |

헤더는 9행, **데이터는 10행부터**. 각 열의 채우는 값은 `test-basis-and-order.md`/`test-design-techniques.md` 참고.

### 시트 `Change History`

| Revision | 변경일 | 작성 역할 | 변경 내용 | 검토 상태 | 승인 상태 |
| --- | --- | --- | --- | --- | --- |

## TPL-SWE5-003 (통합시험 결과서) 시트 구조

### 시트 `Integration Results`

| Test ID | Trace | Result | Actual Result | Evidence Locator | Defect ID | Disposition |
| --- | --- | --- | --- | --- | --- | --- |

### 시트 `Run Summary`

| Run ID | Date | Baseline | Environment | Planned | Pass | Fail | Overall | Limitation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

### 시트 `Change History` (결과서)

TPL-SWE5-002와 동일 구조.

모두 헤더 9행, 데이터 10행부터.
