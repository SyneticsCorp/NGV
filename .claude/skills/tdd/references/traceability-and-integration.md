# 양방향 추적성 (TPL-TRC-001 "Code"/"SWE.4" 열 대응)

구현은 추적 사슬의 마지막 두 칸을 채웁니다: 구현 단위(`IU-NNNN`, `detailed-design`) → **Code**(실제 구현) → **SWE.4**(단위테스트). `requirements-analysis`의 `traceability.md`(`TPL-TRC-001`)와 짝을 이룹니다 — 별도 매트릭스를 새로 만들지 않고 같은 산출물(`ENG-TRC-001`)을 갱신합니다.

## `ENG-TRC-001`에 기록할 값

| 열 | 기록할 값 |
| --- | --- |
| Code | 구현 위치 — 파일 경로와 함수명(예: `src/offset_calculator.py::calculateOffset`) |
| SWE.4 | 이 구현을 검증하는 unittest 테스트 식별자(예: `test_offset_calculator.TestCalculateOffset.testReturnsZeroWhenInputIsZero`, 여러 개면 대표 테스트 파일/클래스명) |
| Coverage | 이 구현까지 추적 사슬이 완성됐다면 "SWE.4까지 완료"로 갱신 |

## 유지 규칙

1. 함수/모듈을 구현하거나 변경할 때마다 같은 작업 내에서 `ENG-TRC-001`의 `Code`/`SWE.4` 열을 함께 갱신합니다 — 나중으로 미루지 않습니다.
2. 구현했지만 대응하는 `IU-NNNN`(상세설계 구현 단위)이나 `SWR-NNNN`(요구사항)이 없는 코드가 발견되면 고아(orphan) 구현으로 간주하고 갭으로 보고합니다 — 왜 필요한지 근거를 확인하세요.
3. 상세설계의 함수 계약이 변경되면, 그와 연결된 구현/테스트에 "재확인 필요" 표시를 남깁니다.
4. `quality-gates.md`의 게이트를 통과하지 못한 구현은 `Coverage` 열에 "품질 게이트 미통과"로 표시하고, 통과 전에는 "완료"로 기록하지 않습니다.
5. `tdd/references/template-policy.md`의 `ENG-REV-001`(인스펙션 결과)에 리뷰를 남길 때는 `Artifact` 열이 여기서 쓰는 것과 동일한 `IU-NNNN`/파일 경로를 가리키도록 일치시킵니다.
