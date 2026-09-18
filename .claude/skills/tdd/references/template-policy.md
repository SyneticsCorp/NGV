# 구현 단계 산출물 정책

`WP_Templates/` 전체를 확인한 결과, 구현(코딩) 단계 전용 문서 템플릿(DOCX/XLSX)은 **존재하지 않습니다**. 구현 단계의 산출물은 다음 두 가지입니다.

1. **소스코드와 단위테스트 코드** — 별도 문서 템플릿 없이, `quality-gates.md`/`doxygen-comments.md`의 기준을 만족하는 코드 자체가 산출물입니다.
2. **단계 완료 시점의 리뷰/인스펙션 결과** — CLAUDE.md의 "각 단계가 완료되었을 때, 지정된 템플릿을 이용한 산출물이 생성되어야 한다" 정책을 채우는 실제 템플릿은 `WP_Templates/Engineering/QualityReview/TPL-REV-001_단계별 인스펙션 결과 템플릿.xlsx`(적용 프로세스 `Common/SUP.1`)입니다. 이 템플릿은 구현 단계뿐 아니라 다른 단계에도 공통으로 쓰이는 범용 리뷰 기록 양식입니다.

## TPL-REV-001 구조 (그대로 유지, 열 순서/이름을 바꾸지 않음)

산출물 ID: `ENG-REV-001_단계별 인스펙션 결과`. 각 시트 9행이 헤더, **실제 데이터는 10행부터** 입력합니다(다른 xlsx 템플릿과 동일 관례). anthropic-skills:xlsx 스킬로 편집합니다.

### 시트 `Inspection Sessions`

| Session ID | Process | Date | Baseline | Artifact | Reviewers | Entry | Exit | Evidence Locator |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

검토 대상과 베이스라인, 참여 역할, 진입/종료 판정과 객관적 증거 위치를 세션별로 기록합니다. `Artifact` 열에는 이번에 구현한 `IU-NNNN`(구현 단위)이나 해당 소스 파일 경로를 적습니다.

### 시트 `Findings`

| Finding ID | Session ID | Severity | Description | Owner | Due | Status | Closure Evidence | Defect Link |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

품질 게이트(`quality-gates.md`) 실측에서 기준을 벗어난 항목이 있었다면, 수정 후 완료됐더라도 이 시트에 지적사항으로 남기고 `Closure Evidence`에 재측정 결과를 기록하는 것을 권장합니다(A-SPICE PA 2.2 근거).

### 시트 `Change History`

| Revision | 변경일 | 작성 역할 | 변경 내용 | 검토 상태 | 승인 상태 |
| --- | --- | --- | --- | --- | --- |

## 언제 인스펙션 세션을 기록하는가

- 구현 단위(`IU-NNNN`) 하나 또는 논리적으로 묶인 여러 단위의 구현이 완료되어 품질 게이트를 통과했을 때.
- 반드시 매 함수마다 별도 세션을 만들 필요는 없습니다 — 프로젝트의 리뷰 단위(예: PR 단위, 모듈 단위)에 맞춰 합리적으로 묶으세요. 묶는 기준이 불명확하면 사용자에게 확인하세요.

## 파일명/저장 위치

- `ENG-REV-001_단계별 인스펙션 결과.xlsx` (`TPL-*` → `ENG-*` 규칙, 다른 스킬과 동일).
- 저장 위치 기본 제안: `Deliverables/Engineering/QualityReview/` (확정된 프로젝트 관례가 아니라 제안값).
- 템플릿을 복사한 뒤 이름을 바꿔 작성하고, 원본 템플릿 파일은 수정하지 않습니다.
