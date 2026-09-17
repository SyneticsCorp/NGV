---
name: requirements-analysis
description: 요구사항 분석 및 요구사항 명세서 작성 시 사용합니다. ISO 26262/A-SPICE 정렬, 기능 요구사항의 UML/SysML 다이어그램화, ISO 25010 기반 비기능 요구사항과 실행 가능한 검증방안, 양방향 추적성, 명확성(EARS 패턴)·일관성 확보 방법을 제공합니다. requirements-analyst 서브에이전트가 사용합니다. "요구사항 분석", "요구사항 명세서", "기능/비기능 요구사항", "추적성 매트릭스" 등의 요청에 반응합니다.
---

# 요구사항 분석 스킬

이 스킬은 요구사항 산출물을 작성/점검할 때 필요한 참고 지식을 제공합니다. 프로젝트 파일을 직접 읽거나 쓰지는 않습니다 — 그 역할은 호출한 에이전트(보통 `requirements-analyst`)가 담당하고, 이 스킬은 무엇을, 어떤 형식으로, 어떤 기준으로 작성할지를 제공합니다.

## 참고자료 구성

1. `references/template-policy.md` — 사용자 지정 템플릿 적용 정책(현재 템플릿 미제공 상태에서의 처리 방법 포함).
2. `references/requirement-schema.md` — 템플릿이 없을 때 사용하는 기본 요구사항 필드 스키마와 ID 체계.
3. `references/clarity-and-consistency.md` — EARS 패턴 기반 명확성 확보 방법과 일관성 자체 점검 체크리스트.
4. `references/uml-sysml-diagrams.md` — 기능 요구사항을 UML/SysML 다이어그램(Mermaid 우선)으로 표현하는 방법.
5. `references/nfr-iso25010.md` — ISO 25010 품질 특성 기반 비기능 요구사항 작성법과 실행 가능한 검증방안 작성 기준.
6. `references/traceability.md` — 양방향 추적성 확보 방안(추적성 매트릭스 구조, 유지 규칙).
7. `references/iso26262-aspice-alignment.md` — ISO 26262 및 A-SPICE 요구사항 관리 기대사항과의 정렬 지침. (CL2 관점 산출물 점검이 필요하면 `aspice-auditor` 스킬과 연계하세요.)

## 사용 순서

1. `template-policy.md`로 템플릿 적용 여부를 확인합니다.
2. 템플릿이 없다면 `requirement-schema.md`의 기본 스키마로 요구사항 항목을 구성합니다.
3. `clarity-and-consistency.md`의 EARS 패턴으로 모든 요구사항 문장을 작성합니다.
4. 기능 요구사항은 `uml-sysml-diagrams.md`에 따라 다이어그램을 함께 만듭니다.
5. 비기능 요구사항은 `nfr-iso25010.md`에 따라 ISO 25010 특성과 실행 가능한 검증방안을 함께 작성합니다.
6. `traceability.md`에 따라 추적성 매트릭스를 만들고 유지합니다.
7. `iso26262-aspice-alignment.md`로 표준 정렬 여부를 확인합니다.
8. 마무리 전 `clarity-and-consistency.md`의 일관성 체크리스트로 전체 산출물을 재점검합니다.

## 중요한 한계

- 여기 담긴 ISO 26262 / A-SPICE / ISO 25010 관련 내용은 실무 적용을 돕기 위한 요약이며, 공식 표준 문서 원문을 그대로 옮긴 것이 아닙니다. 인증/계약상 엄밀함이 필요한 경우 공식 표준 문서를 확인해야 합니다.
- 사용자가 제시하기로 한 템플릿이 아직 없다면, 산출물에 그 사실을 반드시 명시하세요. 템플릿 없이 작성한 산출물을 최종본처럼 다루지 마세요.
