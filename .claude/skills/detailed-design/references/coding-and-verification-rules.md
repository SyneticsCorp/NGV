# 코딩 및 검증 규칙 (TPL-SWE3-001 §11 대응)

TPL-SWE3-001 11장은 "코딩 표준, 정적분석, 단위검증, 커버리지와 리뷰 기준"을 요구합니다. 이 프로젝트는 `CLAUDE.md`에서 이미 코딩 표준을 확정했으므로, 아래 내용을 그대로 11장에 기록하세요 — 더 이상 제안 단계가 아닙니다.

## 확정된 코딩 표준 (CLAUDE.md 구현 지침)

| 항목 | 값 |
| --- | --- |
| 언어 | Python 3.14 |
| 단위검증 기법 | `unittest` (TDD, Red-Green-Refactor) |
| 함수 순수코드라인 | 50 이하 |
| 함수 순환복잡도 | 10 이하 |
| 중복 코드 허용치 | 7라인까지(8라인 이상부터 위반) |
| 주석 방식/비율 | Doxygen 방식, 20% 이상 |
| 네이밍 | 함수/변수명 3자 이상, camelCase |
| 측정 도구 | radon(복잡도·라인수), pylint(중복코드·네이밍) |

실제 구현·측정 절차, radon/pylint 명령과 임계값 설정, Doxygen 주석 형식은 `tdd` 스킬(`references/quality-gates.md`, `references/doxygen-comments.md`)이 권위 있는 출처입니다 — 이 문서에서 중복 작성하지 않습니다. 구현 단계 자체는 `coding` 서브에이전트가 담당합니다(`CLAUDE.md` 구현 지침).

## 이 장(11장)에 실제로 기록할 내용

1. 위 표를 그대로 인용(코딩 표준과 근거는 `CLAUDE.md`).
2. 정적분석 도구(radon, pylint)와 통과 기준 — `tdd`의 `quality-gates.md` 참조.
3. 단위검증 기법(`unittest`, TDD)과, 안전 관련 단위(ASIL이 있는 경우)는 예외/방어 동작 테스트를 반드시 포함해야 한다는 점(`tdd`의 `iso26262-aspice-alignment.md`).
4. 리뷰 기준과 기록 방법 — `tdd`의 `template-policy.md`(`ENG-REV-001`, `TPL-REV-001`)를 참조. 리뷰 기록은 A-SPICE PA 2.2(작업 산출물 관리)의 근거가 됩니다(`aspice-auditor` 스킬과 연계).

## 프로젝트가 CLAUDE.md와 다른 규칙을 요구하는 경우

CLAUDE.md와 상충하는 별도 지시(예: 다른 언어, 다른 임계값)를 사용자가 주면, 임의로 어느 한쪽을 따르지 말고 어느 것이 우선인지 먼저 확인하세요.
