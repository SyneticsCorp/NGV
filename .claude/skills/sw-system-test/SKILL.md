---
name: sw-system-test
description: SW 요구사항 명세서 기반으로 SW 시스템 테스트(SWE.6, 검증) 케이스를 생성하기 위한 방법론 스킬입니다. ISO 26262 Part 6, A-SPICE SWE.6, ISO 29119/ISTQB, ISO 25000(SQuaRE)을 기반지식으로 하고, 기법 선택 기준·PICT 도구 사용법·작성 원칙을 정의합니다. sw-system-tester 서브에이전트가 사용합니다. 이 스킬은 방법론만 정의하며, 요구사항 분석·사용자 확인·실제 산출물(TPL-SWE6-001/002) 작성은 호출한 에이전트가 수행합니다.
---

# SW 시스템 테스트(SWE.6) 스킬

요구사항 명세서(`ENG-SWE1-001`)를 테스트 베이시스로 삼는 블랙박스 시스템 테스트 케이스를 "무엇을 근거로, 어떤 기법으로, 어떤 원칙으로" 설계할지를 정의합니다. 프로젝트 파일을 직접 읽거나 쓰지 않습니다 — 그 역할은 호출한 에이전트(보통 `sw-system-tester`)가 담당합니다.

## 참고자료 구성

1. `references/template-policy.md` — 지정 템플릿(`WP_Templates/Engineering/SoftwareVerification/TPL-SWE6-001·002`) 위치, 산출물 ID 규칙(`ST-FUNC-`/`ST-NFR-<특성>-`), 시트 구조.
2. `references/test-design-techniques.md` — 시스템 테스트 수준의 기법 적용 기준과, 이 수준 고유 기법(페어와이즈/전조건조합, PICT 도구).
3. `references/nfr-verification.md` — 비기능 요구사항(ISO 25010, `requirements-analysis`가 원본)을 실행 가능한 시스템 테스트 케이스로 구체화하는 방법.
4. `references/traceability-and-integration.md` — 시스템 테스트 케이스를 요구사항(`SWR-NNNN`)·`ENG-TRC-001`(`SWE.6` 열)에 연결하는 방법.
5. `references/writing-principles.md` — 케이스 작성 원칙(임의 가정 금지, 실행 가능성, "(제안)" 표기 등).
6. `references/iso26262-aspice-alignment.md` — ISO 26262 Part 6 검증 관점과 A-SPICE SWE.6 기대사항 정렬 지침. (CL2 관점 산출물 점검은 `aspice-auditor` 스킬과 연계하세요.)

## 사용 순서

1. `template-policy.md`로 지정 템플릿과 산출물 ID 규칙을 확인합니다.
2. 대상 요구사항(`ENG-SWE1-001`)의 기능/비기능 여부를 확인합니다 — 비기능이면 `nfr-verification.md`로 실행 가능한 케이스로 구체화합니다.
3. `test-design-techniques.md`로 기법을 선정하고(조합이 많으면 PICT 사용), `TPL-SWE6-001`의 `Verification Specification` 시트에 케이스를 작성합니다.
4. `writing-principles.md`의 원칙(임의 가정 금지, 재현 가능성 등)을 지킵니다.
5. `traceability-and-integration.md`로 `ENG-TRC-001`의 `SWE.6` 열을 갱신합니다.
6. `iso26262-aspice-alignment.md`로 표준 정렬을 확인합니다.

## 다른 테스트 스킬과의 경계

- **`tdd`(단위, SWE.4)**: 베이시스 = 상세설계 함수 계약. **`integration-testing`(통합, SWE.5)**: 베이시스 = 아키텍처 인터페이스/통합 순서. **`sw-system-test`(시스템, SWE.6, 이 스킬)**: 베이시스 = 요구사항 명세서. 세 스킬은 서로 다른 입력에서 케이스를 도출하므로 같은 케이스를 중복 생성하지 않습니다.
- 기본 테스트 기법(동등분할/경계값분석 등)의 정의는 `tdd`의 `test-annotation.md`에 있는 것과 동일합니다 — 이 스킬은 재정의하지 않고 적용 방법만 다룹니다.
- ISO 25010 품질 특성 전체 표는 `requirements-analysis`의 `nfr-iso25010.md`가 원본입니다 — 이 스킬은 나열하지 않고 시스템 테스트 케이스로 구체화하는 방법만 다룹니다.

## 중요한 한계

- 여기 담긴 ISO 26262 / ISO 29119 / ISO 25000 / A-SPICE 관련 내용은 실무 적용을 돕기 위한 요약이며, 공식 표준 문서 원문을 그대로 옮긴 것이 아닙니다. 인증/계약상 엄밀함이 필요한 경우 공식 표준 문서를 확인해야 합니다.
- `TPL-SWE6-001`에는 기능/비기능을 구분하는 전용 시트·컬럼이 없습니다 — `template-policy.md`의 `Test ID` 접두사 관례로 구분하고, 임의로 새 시트/컬럼을 추가하지 않습니다.
- 지정 템플릿(TPL-SWE6-*)이 실제로 프로젝트에 있는지 매 작업 시작 시 다시 확인하세요(`WP_Templates/PRC-TPL-001_표준 산출물 양식 등록부.xlsx`).
- `WP_Templates/Engineering/README.md`의 저작권 고지(교육/실습용, 과정 밖 배포·상업적 이용 시 사전 서면승인 필요)를 유의하세요.
