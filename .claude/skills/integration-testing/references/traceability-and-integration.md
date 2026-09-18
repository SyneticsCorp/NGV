# 양방향 추적성 (TPL-TRC-001 "SWE.5" 열 대응)

통합 테스트는 추적 사슬에서 단위테스트(SWE.4) 다음 칸을 채웁니다: 아키텍처 요소/인터페이스(`ARC-NNNN`/`IF-NNNN`) → 구현(Code) → 단위테스트(SWE.4) → **통합시험(SWE.5)**. `requirements-analysis`의 `traceability.md`, `tdd`의 `traceability-and-integration.md`와 짝을 이룹니다 — 별도 매트릭스를 새로 만들지 않고 같은 산출물(`ENG-TRC-001`)을 갱신합니다.

## `ENG-TRC-001`에 기록할 값

| 열 | 기록할 값 |
| --- | --- |
| SWE.5 | 이 인터페이스/통합 항목을 검증하는 통합시험 케이스 ID(`IT-NNNN`, 여러 개면 나열) |
| Coverage | 이 항목까지 추적 사슬이 완성됐다면 "SWE.5까지 완료(함수/Call 커버리지 100%)"로 갱신 |

## `ENG-SWE5-001` 11장/13장(추적성)에 기록할 내용

- 아키텍처 인터페이스(`IF-NNNN`) ↔ 통합시험 케이스(`IT-NNNN`) ↔ 실행 결과(`ENG-SWE5-003`의 Test ID) ↔ 결함(Defect ID)의 연결을 요약합니다.
- 상세 매트릭스는 `ENG-TRC-001`에서 관리하고, 여기서는 "전체 추적성은 `ENG-TRC-001` 참조"로 요약해도 됩니다(`requirements-analysis`의 11장 처리 방식과 동일).

## 유지 규칙

1. 통합시험 케이스를 추가/변경/폐기할 때마다 같은 작업 내에서 `ENG-TRC-001`의 `SWE.5` 열을 함께 갱신합니다.
2. 인터페이스(`IF-NNNN`)가 존재하는데 대응하는 `IT-NNNN`이 없으면 고아(orphan) 인터페이스로 간주하고 갭으로 보고합니다(`coverage-criteria.md`의 함수 커버리지 미달과 직결).
3. 아키텍처 인터페이스가 변경되면, 그와 연결된 모든 통합시험 케이스에 "재확인 필요" 표시를 남깁니다(영향 분석, `results-and-regression.md`의 회귀 범위 선정과 연결).
4. `ENG-SWE5-001`(명세), `ENG-SWE5-002`(케이스), `ENG-SWE5-003`(결과), `ENG-TRC-001`(매트릭스) 네 산출물의 ID와 관계는 항상 일치해야 합니다.
