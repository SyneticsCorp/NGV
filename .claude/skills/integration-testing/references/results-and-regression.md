# 결과 기록과 회귀 전략 (TPL-SWE5-001 §8/§9/§10, TPL-SWE5-003 대응)

## 실행 및 결과 기록 (8장, `ENG-SWE5-003`)

`Integration Results` 시트(`Test ID | Trace | Result | Actual Result | Evidence Locator | Defect ID | Disposition`)에 실제로 실행한 케이스만 기록합니다.

- `Result`: Pass/Fail/Blocked 등 — 실행하지 않았다면 이 열을 채우지 않습니다(추정으로 "Pass"를 적지 않음).
- `Evidence Locator`: 재현 가능한 근거(로그 파일 경로, `coverage.json` 위치, CI 실행 링크 등). "확인함" 같은 근거 없는 문구를 적지 않습니다.
- `Defect ID`: 실패 시 문제 기록(`SUP.9` 문제 해결 관리와 연결되는 ID 체계가 있다면 그것을 사용, 없으면 이번 프로젝트의 결함 추적 방식을 사용자에게 확인).
- `Disposition`: 실패의 처리 방향(수정 예정/재시험/계획된 예외 등).

`Run Summary` 시트(`Run ID | Date | Baseline | Environment | Planned | Pass | Fail | Overall | Limitation`)에는 실행 단위(예: 한 번의 통합 단계 전체 실행)별 집계를 기록합니다. `Limitation`에는 `coverage-criteria.md`에서 확인한 커버리지 실측치와, 이번 실행이 확인하지 못한 범위를 남깁니다.

## 회귀 전략 (9장)

- 아키텍처 인터페이스나 구현이 변경되면, 그 변경이 영향을 주는 통합시험 케이스를 `ENG-TRC-001`(`traceability-and-integration.md`)로 식별합니다.
- 회귀 범위는 "변경된 인터페이스와 직접 연결된 케이스" + "그 인터페이스에 의존하는 하류 통합 단계의 케이스"를 포함합니다 — 변경된 케이스만 재실행하고 끝내지 않습니다.
- 가능하면 회귀 실행을 자동화하고(`ENG-SWE5-002`의 `Automation` 열), 자동화되지 않은 케이스는 수동 재실행 계획을 명시합니다.
- 회귀 실행 후에도 `coverage-criteria.md`의 함수/Call 커버리지가 유지되는지 재확인합니다 — 변경으로 새로 생긴 호출 경로가 커버리지에서 빠지지 않도록 합니다.

## 실패 및 편차 처리 (10장)

실패를 발견하면 원인에 따라 분류합니다.

| 분류 | 처리 |
| --- | --- |
| 구현 결함 | `coding`/`detailed-designer`로 피드백, `Defect ID` 연결 |
| 테스트 설계 결함(잘못된 기대값 등) | `ENG-SWE5-002` 케이스 수정, 수정 사유를 `Change History`에 기록 |
| 환경/도구 문제 | 환경을 고치고 재실행 — 이 실패를 "결함 없음"으로 조용히 덮지 않음 |
| 계획된 편차(의도적으로 이번엔 다루지 않는 범위) | `ENG-SWE5-001` 12장(적용 한계)에 근거와 함께 명시, 사용자 확인 필요 |

임의로 실패를 재시험 없이 "통과"로 바꾸거나, 원인 분류 없이 넘어가지 않습니다.
