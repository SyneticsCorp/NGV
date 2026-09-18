# 양방향 추적성 확보 방안 (TPL-TRC-001 대응)

추적성 매트릭스는 markdown이 아니라 지정 xlsx 템플릿으로 관리합니다: `WP_Templates/Engineering/Traceability/TPL-TRC-001_양방향 요구사항 추적 매트릭스 템플릿.xlsx`. 이는 A-SPICE CL2 PA 2.2(작업 산출물 관리)의 핵심 근거이기도 합니다 — `aspice-auditor` 스킬의 체크리스트와 이 문서의 내용이 서로 대응해야 합니다.

## 산출물

- 템플릿을 복사해 `ENG-TRC-001_양방향 요구사항 추적 매트릭스.xlsx`로 저장합니다(`template-policy.md`의 산출물 ID 규칙).
- xlsx이므로 anthropic-skills:xlsx 스킬로 열람/편집합니다.

## 시트 구조 (그대로 유지, 열 순서/이름을 바꾸지 않음)

### 시트 `Bidirectional Trace`

9행이 헤더이며, **실제 데이터는 10행부터** 입력합니다.

| 열 | 의미 | 채우는 값 |
| --- | --- | --- |
| Upper Req | 상위(출처) 요구사항 | `OEM_Sample` 등 상위 입력의 요구사항 ID (예: `OEM-SR-003`, `OEM-FR-012`) |
| SW Req | 이 프로젝트의 소프트웨어 요구사항 | `SWR-NNNN` (`requirement-schema.md`) |
| Architecture | 이 요구사항을 만족(satisfies)하는 아키텍처 요소 | `architecture-design` 스킬에서 정의하는 아키텍처 요소 ID (예: `ARC-NNNN`) |
| Detailed Design | 상세설계 산출물 | SWE.3 산출물의 설계 항목 ID |
| Code | 구현 위치 | 파일 경로/함수/모듈 참조 |
| SWE.4 | 단위 시험 근거 | 단위 테스트 케이스 ID |
| SWE.5 | 통합 시험 근거 | 통합 테스트 케이스 ID |
| SWE.6 | 검증(자격) 시험 근거 | 검증 테스트 케이스 ID |
| Coverage | 이 요구사항의 추적 사슬이 어디까지 채워졌는지 요약 | 예: "SWE.4까지 완료", "아키텍처 단계까지만 존재" 등 |

### 시트 `Change History`

| Revision | 변경일 | 작성 역할 | 변경 내용 | 검토 상태 | 승인 상태 |
| --- | --- | --- | --- | --- | --- |

매트릭스 자체를 변경할 때마다 이 시트에 이력을 남깁니다.

## 유지 규칙

1. 요구사항을 추가/변경/폐기할 때마다 같은 작업 내에서 `Bidirectional Trace` 시트를 함께 갱신합니다 — 나중으로 미루지 않습니다.
2. 아직 해당 단계 산출물이 없는 열(예: 아직 설계를 시작하지 않았다면 Architecture 이후 열)은 비워두고, `Coverage` 열에 "아직 해당 단계 아님"을 명시합니다. 이를 "링크가 없다=문제"와 구분합니다.
3. 이미 존재하는 하위 산출물(설계, 코드, 테스트)이 있는데도 해당 열이 비어 있으면 고아(orphan) 요구사항으로 간주하고 갭으로 보고합니다.
4. ID는 각 산출물(SWR-, ARC-, IF- 등)의 실제 ID와 정확히 일치해야 합니다. 불일치는 추적성 단절이므로 발견 즉시 수정합니다.
5. `Upper Req` 열은 반드시 채워야 합니다 — 출처 없는 요구사항(고아 상위 링크)은 만들지 않습니다. 근거가 불명확하면 "확인 필요"로 표시하고 사용자에게 확인합니다.
6. `uml-sysml-diagrams.md`의 Mermaid `requirementDiagram`으로 초안 검토를 하더라도, 최종 근거는 이 xlsx 산출물입니다 — 두 표현이 있다면 반드시 서로 일치시킵니다.
