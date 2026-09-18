---
name: architecture-design
description: 아키텍처 설계 시 사용합니다. ISO 26262 Part 6과 A-SPICE(SYS.3/SWE.2)의 아키텍처 설계 원칙, 후보 아키텍처 패턴 카탈로그(레이어드/AUTOSAR형/헥사고날/이벤트 기반/안전 아키텍처 패턴 등), 응집도·결합도·SOLID·변경 유연성 체크리스트, 인터페이스 정의 규칙과 통합 순서 결정 방법을 제공합니다. architecture-designer 서브에이전트가 사용합니다. "아키텍처 설계", "아키텍처 구조 제안", "컴포넌트 설계" 등의 요청에 반응합니다.
---

# 아키텍처 설계 스킬

이 스킬은 아키텍처 산출물을 작성/점검할 때 필요한 참고 지식을 제공합니다. 프로젝트 파일을 직접 읽거나 쓰지 않습니다 — 그 역할은 호출한 에이전트(보통 `architecture-designer`)가 담당하고, 이 스킬은 후보 아키텍처를 어떻게 고르고, 무엇을 기준으로 설계·평가하며, 어떤 형식으로 작성할지를 제공합니다.

## 참고자료 구성

1. `references/template-policy.md` — 지정 양식(`WP_Templates/Engineering/SoftwareArchitecturalDesign/TPL-SWE2-001·002`) 위치, 산출물 ID/파일명 규칙, 목차, 작성 방법.
2. `references/architecture-patterns.md` — 후보 아키텍처 패턴 카탈로그(1단계 제안에 사용).
3. `references/design-principles.md` — 응집도/결합도, SOLID, 변경 유연성 체크리스트.
4. `references/interface-and-integration.md` — 컴포넌트 인터페이스 정의 규칙과 통합 순서 결정 방법.
5. `references/iso26262-aspice-alignment.md` — ISO 26262 Part 6 안전 아키텍처 원칙과 A-SPICE SYS.3/SWE.2 기대사항 정렬 지침. (CL2 관점 산출물 점검은 `aspice-auditor` 스킬과 연계하세요.)
6. `references/architecture-diagrams.md` — 컴포넌트/의존성/배치 다이어그램 표현 방법(Mermaid). 표기법 기본기는 `requirements-analysis` 스킬의 `uml-sysml-diagrams.md`와 공유합니다.

## 사용 순서

1. `template-policy.md`로 지정 설계서 양식 적용 여부를 확인합니다.
2. `architecture-patterns.md`에서 프로젝트 특성에 맞는 후보 2~4개를 골라 제안합니다(사용자 선택 대기 — `architecture-designer`의 1단계).
3. 사용자가 선택하면 `design-principles.md`로 컴포넌트 분해와 원칙 준수를 점검합니다.
4. `interface-and-integration.md`로 모든 컴포넌트 인터페이스를 정의하고 통합 순서를 근거와 함께 정합니다.
5. `iso26262-aspice-alignment.md`로 표준 정렬을 확인합니다.
6. `architecture-diagrams.md`로 구조/의존성을 다이어그램으로 표현합니다.

## 중요한 한계

- 여기 담긴 ISO 26262 / A-SPICE 관련 내용은 실무 적용을 돕기 위한 요약이며, 공식 표준 문서 원문을 그대로 옮긴 것이 아닙니다. 인증/계약상 엄밀함이 필요한 경우 공식 표준 문서를 확인해야 합니다.
- 지정 양식(TPL-SWE2-*)이 실제로 프로젝트에 있는지 매 작업 시작 시 다시 확인하세요(`WP_Templates/PRC-TPL-001_표준 산출물 양식 등록부.xlsx`).
- 후보 아키텍처를 사용자 확인 없이 임의로 확정하지 마세요.
- `WP_Templates/Engineering/README.md`의 저작권 고지(교육/실습용, 과정 밖 배포·상업적 이용 시 사전 서면승인 필요)를 유의하세요.
