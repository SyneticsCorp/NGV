---
name: detailed-design
description: 상세설계(SWE.3, Software Detailed Design and Unit Construction) 작성 시 사용합니다. ISO 26262 Part 6 단위 설계/구현 원칙과 A-SPICE SWE.3 기대사항, 모듈 분해·함수 계약·알고리즘·상태전이·오류처리 작성 방법, 코딩/검증 규칙, 양방향 추적성, Python 의존성 SBOM/FOSS 라이선스 검토를 제공합니다. detailed-designer 서브에이전트가 사용합니다. "상세설계", "모듈 분해", "함수 계약", "SBOM" 등의 요청에 반응합니다.
---

# 상세설계 스킬

이 스킬은 상세설계 산출물을 작성/점검할 때 필요한 참고 지식을 제공합니다. 프로젝트 파일을 직접 읽거나 쓰지 않습니다 — 그 역할은 호출한 에이전트(보통 `detailed-designer`)가 담당하고, 이 스킬은 무엇을, 어떤 형식으로, 어떤 기준으로 작성할지를 제공합니다.

## 참고자료 구성

1. `references/template-policy.md` — 지정 템플릿(`WP_Templates/Engineering/SoftwareDetailedDesignAndUnitConstruction/TPL-SWE3-001·002`, `TPL-SBOM-001`) 위치, 산출물 ID/파일명 규칙, 목차, 작성 방법.
2. `references/design-schema.md` — TPL-SWE3-001의 각 장에 대응하는 작업용 설계 필드 스키마와 ID 체계(`IU-NNNN`).
3. `references/coding-and-verification-rules.md` — `CLAUDE.md`에서 확정된 코딩 표준(Python 3.12, 품질 지표, `tdd` 스킬 연계)을 11장에 기록하는 방법.
4. `references/sbom-foss-compliance.md` — `TPL-SBOM-001`(SBOM/FOSS Review/Change History 시트) 작성 방법.
5. `references/detailed-design-diagrams.md` — 모듈 분해/호출관계 다이어그램 표현 방법(Mermaid 초안 → `TPL-SWE3-002` drawio 최종본).
6. `references/traceability-and-integration.md` — 구현 단위 ↔ 아키텍처 ↔ 요구사항 ↔ 단위시험 양방향 추적성(12장/14장 대응, `TPL-TRC-001` 연계).
7. `references/iso26262-aspice-alignment.md` — ISO 26262 Part 6 단위 설계/구현 원칙과 A-SPICE SWE.3 기대사항 정렬 지침. (CL2 관점 산출물 점검은 `aspice-auditor` 스킬과 연계하세요.)

## 사용 순서

1. `template-policy.md`로 지정 템플릿과 산출물 ID 규칙을 확인합니다.
2. `design-schema.md`의 작업용 스키마로 모듈 분해·함수 계약·알고리즘·상태전이·오류처리를 구성합니다.
3. `coding-and-verification-rules.md`로 확정된 코딩/검증 규칙을 11장에 기록합니다.
4. 외부 의존성이 있다면 `sbom-foss-compliance.md`로 SBOM/FOSS 검토를 작성합니다.
5. `detailed-design-diagrams.md`로 모듈 분해/호출관계를 다이어그램으로 표현합니다.
6. `traceability-and-integration.md`로 양방향 추적성을 갱신합니다.
7. `iso26262-aspice-alignment.md`로 표준 정렬을 확인합니다.

## 중요한 한계

- 여기 담긴 ISO 26262 / A-SPICE 관련 내용은 실무 적용을 돕기 위한 요약이며, 공식 표준 문서 원문을 그대로 옮긴 것이 아닙니다. 인증/계약상 엄밀함이 필요한 경우 공식 표준 문서를 확인해야 합니다.
- `TPL-SWE3-001` 자체는 코딩 표준을 지정하지 않지만, 이 프로젝트는 `CLAUDE.md`에서 코딩 표준(Python 3.12, 품질 지표, camelCase 네이밍)을 이미 확정했습니다 — `coding-and-verification-rules.md`/`tdd` 스킬을 그대로 따르고 다시 제안하지 않습니다.
- 지정 템플릿(TPL-SWE3-*, TPL-SBOM-001)이 실제로 프로젝트에 있는지 매 작업 시작 시 다시 확인하세요(`WP_Templates/PRC-TPL-001_표준 산출물 양식 등록부.xlsx`).
- `WP_Templates/Engineering/README.md`의 저작권 고지(교육/실습용, 과정 밖 배포·상업적 이용 시 사전 서면승인 필요)를 유의하세요.
