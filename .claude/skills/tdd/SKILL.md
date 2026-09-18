---
name: tdd
description: 구현(코딩) 시 사용합니다. CLAUDE.md 구현 지침(Python 3.14, unittest 기반 TDD, 함수 순수코드라인 50 이하, 순환복잡도 10 이하, 중복코드 7라인까지 허용, Doxygen 방식 주석 20% 이상, 3자 이상 camelCase 네이밍)에 따라 Red-Green-Refactor 절차, radon/pylint 기반 품질 게이트 측정, Doxygen 주석 작성법, 추적성, ISO 26262/A-SPICE 정렬을 제공합니다. coding 서브에이전트가 사용합니다. "구현", "코딩", "TDD" 등의 요청에 반응합니다.
---

# TDD 스킬

이 스킬은 구현 산출물을 작성/점검할 때 필요한 참고 지식을 제공합니다. 프로젝트 파일을 직접 읽거나 쓰지 않습니다 — 그 역할은 호출한 에이전트(보통 `coding`)가 담당하고, 이 스킬은 어떤 절차로, 어떤 기준으로 구현·측정·기록할지를 제공합니다.

## 참고자료 구성

1. `references/template-policy.md` — 구현 단계 전용 문서 템플릿은 없음(코드+테스트가 산출물)과, 단계 완료 시점 리뷰 산출물(`TPL-REV-001`→`ENG-REV-001`) 작성 방법.
2. `references/tdd-workflow.md` — `unittest` 기반 Red-Green-Refactor 절차와 테스트 작성 규칙.
3. `references/quality-gates.md` — CLAUDE.md의 4대 **필수** 품질 지표별 정확한 기준치와 radon/pylint 실측 명령, 미달 시 조치.
4. `references/doxygen-comments.md` — Python에서 Doxygen 방식 주석을 작성하는 형식과 20% 기준 측정 방법.
5. `references/traceability-and-integration.md` — 코드/단위테스트를 구현 단위(`IU-NNNN`)·요구사항(`SWR-NNNN`)·`ENG-TRC-001`에 연결하는 방법.
6. `references/iso26262-aspice-alignment.md` — ISO 26262 Part 6 단위 구현/검증 관점과 A-SPICE SWE.3/SWE.4 기대사항 정렬 지침. (CL2 관점 산출물 점검은 `aspice-auditor` 스킬과 연계하세요.)

## 사용 순서

1. `template-policy.md`로 이번 단계에서 만들 산출물(코드/테스트/리뷰 기록)을 확인합니다.
2. `tdd-workflow.md`의 Red-Green-Refactor로 구현합니다.
3. `quality-gates.md`의 명령으로 라인수/복잡도/중복/네이밍을 실측하고 기준을 만족시킵니다.
4. `doxygen-comments.md`로 주석을 작성하고 비율을 측정합니다.
5. `traceability-and-integration.md`로 `ENG-TRC-001`을 갱신합니다.
6. `iso26262-aspice-alignment.md`로 표준 정렬을 확인합니다.

## 중요한 한계

- 여기 담긴 ISO 26262 / A-SPICE 관련 내용은 실무 적용을 돕기 위한 요약이며, 공식 표준 문서 원문을 그대로 옮긴 것이 아닙니다. 인증/계약상 엄밀함이 필요한 경우 공식 표준 문서를 확인해야 합니다.
- CLAUDE.md의 camelCase 네이밍 지침은 PEP 8(snake_case 권장) 및 pylint 기본 네이밍 규칙과 다릅니다 — `quality-gates.md`의 `.pylintrc` 설정 예시로 이 차이를 명시적으로 반영해야 하며, 임의로 snake_case로 되돌리지 않습니다.
- `WP_Templates/Engineering/README.md`의 저작권 고지(교육/실습용, 과정 밖 배포·상업적 이용 시 사전 서면승인 필요)를 유의하세요.
