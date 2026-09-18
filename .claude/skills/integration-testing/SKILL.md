---
name: integration-testing
description: 소프트웨어 통합 테스트(SWE.5) 작성/실행 시 사용합니다. ISO 26262 Part 6 기반 시험 설계기법(요구사항기반/동등분할/경계값분석/결정테이블/상태전이/오류주입), 함수 커버리지·Call 커버리지 100% 측정 방법, 아키텍처 설계서(인터페이스·통합 순서)를 테스트 베이시스로 삼는 방법, 추적성, A-SPICE SWE.5 정렬을 제공합니다. integration-tester 서브에이전트가 사용합니다. "통합 테스트", "통합시험", "SWE.5" 등의 요청에 반응합니다.
---

# 통합 테스트 스킬

이 스킬은 소프트웨어 통합 테스트 산출물을 작성/점검할 때 필요한 참고 지식을 제공합니다. 프로젝트 파일을 직접 읽거나 쓰지 않습니다 — 그 역할은 호출한 에이전트(보통 `integration-tester`)가 담당하고, 이 스킬은 무엇을 테스트 베이시스로 삼고, 어떤 기법으로, 어떤 커버리지 기준으로 진행할지를 제공합니다.

## 참고자료 구성

1. `references/template-policy.md` — 지정 템플릿(`WP_Templates/Engineering/SoftwareComponentVerificationAndIntegrationVerification/TPL-SWE5-001·002·003`) 위치, 산출물 ID/파일명 규칙, 목차, 시트 구조.
2. `references/test-basis-and-order.md` — 아키텍처 설계서(인터페이스 명세, 통합 순서)를 테스트 베이시스로 삼는 방법.
3. `references/test-design-techniques.md` — ISO 26262 Part 6 기반 시험 설계기법과 적용 기준.
4. `references/coverage-criteria.md` — 함수 커버리지·Call 커버리지 100% 정의와 `coverage.py` 기반 실측 방법.
5. `references/traceability-and-integration.md` — 통합시험 케이스/결과를 인터페이스(`IF-NNNN`)·요구사항(`SWR-NNNN`)·`ENG-TRC-001`(`SWE.5` 열)에 연결하는 방법.
6. `references/results-and-regression.md` — 통합시험 결과 기록(`ENG-SWE5-003`)과 회귀 전략, 실패/편차 처리 방법.
7. `references/iso26262-aspice-alignment.md` — ISO 26262 Part 6 통합시험 관점과 A-SPICE SWE.5/SYS.4 기대사항 정렬 지침. (CL2 관점 산출물 점검은 `aspice-auditor` 스킬과 연계하세요.)

## 사용 순서

1. `template-policy.md`로 지정 템플릿과 산출물 ID 규칙을 확인합니다.
2. `test-basis-and-order.md`로 아키텍처 설계서의 인터페이스/통합 순서를 테스트 베이시스로 확보합니다.
3. `test-design-techniques.md`로 각 통합 항목에 맞는 기법을 선정합니다.
4. 통합 순서대로 `ENG-SWE5-002`에 케이스를 작성하고 실행합니다.
5. `coverage-criteria.md`로 함수/Call 커버리지를 100%까지 실측·보완합니다.
6. `results-and-regression.md`로 `ENG-SWE5-003`에 결과를 기록하고 회귀 전략을 정합니다.
7. `traceability-and-integration.md`로 `ENG-TRC-001`을 갱신합니다.
8. `iso26262-aspice-alignment.md`로 표준 정렬을 확인합니다.

## 중요한 한계

- 여기 담긴 ISO 26262 / A-SPICE 관련 내용은 실무 적용을 돕기 위한 요약이며, 공식 표준 문서 원문을 그대로 옮긴 것이 아닙니다. 인증/계약상 엄밀함이 필요한 경우 공식 표준 문서를 확인해야 합니다.
- `TPL-SWE5-001`에는 "커버리지 기준"이라는 전용 절이 없습니다 — 함수/Call 커버리지 100% 요구는 5장(진입 및 종료 기준)의 종료 기준으로, 기법 선정 근거는 7장(시험 설계기법)에 기록하세요(`template-policy.md`).
- 지정 템플릿(TPL-SWE5-*)이 실제로 프로젝트에 있는지 매 작업 시작 시 다시 확인하세요(`WP_Templates/PRC-TPL-001_표준 산출물 양식 등록부.xlsx`).
- 아키텍처 설계서가 없거나 인터페이스/통합 순서가 불완전하면 테스트 베이시스가 없는 것이므로, 지어내지 말고 `architecture-designer`로 먼저 보완해야 한다고 알리세요.
- `WP_Templates/Engineering/README.md`의 저작권 고지(교육/실습용, 과정 밖 배포·상업적 이용 시 사전 서면승인 필요)를 유의하세요.
- 이 스킬은 SWE.5(소프트웨어 통합시험, 테스트 베이시스=아키텍처)만 다룹니다. SWE.6(소프트웨어 시스템 시험, 테스트 베이시스=요구사항 명세서)은 별도의 `sw-system-test` 스킬이 담당합니다(이 스킬과 별개로 프로젝트에 추가되어 있음 — 전용 서브에이전트는 아직 없음).
