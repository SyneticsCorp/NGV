# 템플릿 적용 정책

## 지정 템플릿

| Template ID | 파일 | 용도 |
| --- | --- | --- |
| TPL-SWE6-001 | `WP_Templates/Engineering/SoftwareVerification/TPL-SWE6-001_SW 검증 명세서 템플릿.xlsx` | SW 검증(시스템 테스트) 명세서 |
| TPL-SWE6-002 | `WP_Templates/Engineering/SoftwareVerification/TPL-SWE6-002_SW 검증 결과서 템플릿.xlsx` | SW 검증(시스템 테스트) 결과서 |

전체 등록 정보는 `WP_Templates/PRC-TPL-001_표준 산출물 양식 등록부.xlsx`에 있습니다. `Template Register` 시트에는 TPL-SWE6-001 한 행만 있고(두 산출물이 " / "로 나열됨), `Engineering Template Files` 시트에는 두 Template ID가 각각 개별 행으로 등록되어 있습니다.

## 파일명/산출물 ID 규칙

- `ENG-SWE6-001_SW 검증 명세서.xlsx`, `ENG-SWE6-002_SW 검증 결과서.xlsx` (`TPL-*` → `ENG-*` 규칙, 다른 스킬과 동일).
- 시스템 테스트 케이스 ID: 기능 요구사항 대상이면 `ST-FUNC-<일련번호>`, 비기능 요구사항 대상이면 `ST-NFR-<특성약어>-<일련번호>`. 일련번호는 4자리, 0채움.
- **특성약어(이 스킬에서 새로 정의 — `requirements-analysis`에는 아직 약어 체계가 없어 여기서 도입):**

  | 특성 | 약어 |
  | --- | --- |
  | 기능 적합성 | FUNCSUIT |
  | 성능 효율성 | PERF |
  | 호환성 | COMPAT |
  | 사용성 | USE |
  | 신뢰성 | REL |
  | 보안성 | SEC |
  | 유지보수성 | MAINT |
  | 이식성 | PORT |

  특성 이름은 `requirements-analysis`의 `nfr-iso25010.md` 표와 동일합니다. 예: `ST-NFR-SEC-0003`, `ST-NFR-PERF-0007`.
- 이미 프로젝트에 다른 접두사가 쓰이고 있다면 그것을 따르세요.
- 템플릿을 복사한 뒤 이름을 바꿔 작성하고, 원본 템플릿 파일은 수정하지 않습니다.
- 저장 위치 기본 제안: `Deliverables/Engineering/SoftwareVerification/` (확정된 프로젝트 관례가 아니라 제안값).

## TPL-SWE6-001 (SW 검증 명세서) 시트 구조

**이 템플릿에는 기능/비기능을 구분하는 별도 시트나 컬럼이 없습니다.** 하나의 `Verification Specification` 시트에서 `Test ID` 접두사(`ST-FUNC-`/`ST-NFR-`)로 구분합니다. 임의로 새 시트나 컬럼을 추가하지 않습니다(원본 구조 유지 규칙).

### 시트 `Verification Specification`

| Test ID | SW Req | Level/Environment | Stimulus | Expected Result | Technique | Execution |
| --- | --- | --- | --- | --- | --- | --- |

헤더는 9행, **데이터는 10행부터**.

| 열 | 채우는 값 |
| --- | --- |
| Test ID | `ST-FUNC-NNNN` 또는 `ST-NFR-<특성약어>-NNNN` |
| SW Req | 대상 요구사항 `SWR-NNNN`(`requirements-analysis`) — `ENG-TRC-001`의 `SWE.6` 열과 일치해야 함 |
| Level/Environment | 시험 수준/환경(PC, SIL, Web 등 — `Environment` 시트의 `Environment ID`와 연결) |
| Stimulus | 입력/자극 |
| Expected Result | 기대 결과. 요구사항 원문에 없거나 더 엄격한 판정기준을 확정한 경우, 이 셀 끝에 `[확정: <일자>, 승인: <역할/성명>]` 형식으로 근거를 덧붙입니다(전용 열이 없으므로 이 관례를 따름 — 임의로 새 열을 만들지 않음). |
| Technique | 사용한 시험 설계 기법(`test-design-techniques.md`) |
| Execution | 실행 방법(수동/자동, 자동화 스크립트 참조 등) |

### 시트 `Environment`

| Environment ID | 구성 | 버전 및 식별 | 사용 범위 | 수집 증거 | 명시적 제외 |
| --- | --- | --- | --- | --- | --- |

### 시트 `Change History`

| Revision | 변경일 | 작성 역할 | 변경 내용 | 검토 상태 | 승인 상태 |
| --- | --- | --- | --- | --- | --- |

## TPL-SWE6-002 (SW 검증 결과서) 시트 구조

### 시트 `Verification Results`

| Test ID | SW Req | Result | Actual Result | Evidence Locator | Execution Time | Scope Note |
| --- | --- | --- | --- | --- | --- | --- |

`Evidence Locator`는 재현 가능한 근거(로그 경로, 실행 링크 등)여야 합니다 — "확인함" 같은 근거 없는 문구를 적지 않습니다.

### 시트 `Summary`

| 항목 | 계획 | 실행 | Pass | Fail | 미실행 | 판정 | 제한 |
| --- | --- | --- | --- | --- | --- | --- | --- |

### 시트 `Change History` (결과서)

TPL-SWE6-001과 동일 구조.

모두 헤더 9행, 데이터 10행부터. anthropic-skills:xlsx 스킬로 편집합니다.
