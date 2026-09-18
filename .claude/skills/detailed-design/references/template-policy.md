# 템플릿 적용 정책

## 지정 템플릿

| Template ID | 파일 | 용도 |
| --- | --- | --- |
| TPL-SWE3-001 | `WP_Templates/Engineering/SoftwareDetailedDesignAndUnitConstruction/TPL-SWE3-001_SW 상세설계서 템플릿.docx` | 상세설계서 본문 |
| TPL-SWE3-002 | `WP_Templates/Engineering/SoftwareDetailedDesignAndUnitConstruction/TPL-SWE3-002_상세설계 UML 및 호출관계 템플릿.drawio` | 모듈 분해/호출관계 다이어그램 |
| TPL-SBOM-001 | `WP_Templates/Engineering/SoftwareDetailedDesignAndUnitConstruction/TPL-SBOM-001_Python 의존성 SBOM FOSS 라이선스 목록 템플릿.xlsx` | Python 의존성 SBOM 및 FOSS 라이선스 검토 |

전체 등록 정보는 `WP_Templates/PRC-TPL-001_표준 산출물 양식 등록부.xlsx`에 있습니다. `Template Register` 시트에는 TPL-SWE3-001 한 행만 있고(DOCX/DRAWIO 통합 표기), `Engineering Template Files` 시트에는 TPL-SWE3-001/002/TPL-SBOM-001 세 행이 개별적으로 등록되어 있습니다. TPL-SBOM-001은 `Template Register` 시트에는 등재되어 있지 않으므로, 등록부만 보고 존재를 누락하지 않도록 `Engineering Template Files` 시트도 함께 확인하세요.

## 파일명/산출물 ID 규칙

- `ENG-SWE3-001_SW 상세설계서.docx`, `ENG-SWE3-002_상세설계 UML 및 호출관계.drawio`, `ENG-SBOM-001_Python 의존성 SBOM FOSS 라이선스 목록.xlsx` (`TPL-*` → `ENG-*` 규칙, `requirements-analysis`/`architecture-design`과 동일).
- 템플릿을 복사한 뒤 이름을 바꿔 작성하고, 원본 템플릿 파일은 수정하지 않습니다.
- 저장 위치 기본 제안: `Deliverables/Engineering/SoftwareDetailedDesignAndUnitConstruction/` (확정된 프로젝트 관례가 아니라 제안값).

## 작성 방법 (`WP_Templates/Engineering/README.md` 규칙)

- **DOCX(TPL-SWE3-001)**: anthropic-skills:docx 스킬로 작성합니다. 장/절 제목은 그대로 유지하고, "작성 안내" 서술형 가이드를 실제 내용으로 교체합니다.
- **DRAWIO(TPL-SWE3-002)**: XML이므로 Read/Edit로 직접 열람·수정 가능합니다. 자리표시자 도형만 있고 특정 UML 셰이프 라이브러리는 쓰지 않습니다. 노란 안내 박스가 요구하는 4가지(①구현 단위와 책임 ②함수 또는 클래스 호출 ③입력 출력 자료형 ④설계 및 시험 추적 ID)를 실제 요소로 채우고 안내 박스는 삭제합니다. 먼저 `detailed-design-diagrams.md`의 Mermaid로 초안을 만들어 확인한 뒤 drawio로 옮기는 것을 권장합니다. 검토본/베이스라인 생성 시 PNG를 함께 내보냅니다.
- **XLSX(TPL-SBOM-001)**: anthropic-skills:xlsx 스킬로 작성합니다. 기존 시트/열 구조를 그대로 유지하고, 실제 데이터는 **10행부터** 입력합니다(`sbom-foss-compliance.md` 참고).

## TPL-SWE3-001 목차 (변경 없이 그대로 사용)

1. 목적 및 적용범위 (1.1 목적 / 1.2 적용범위 / 1.3 적용경계)
2. 모듈 분해
3. 상세 호출관계
4. 공통 자료형
5. 핵심 함수 계약
6. 핵심 알고리즘
7. 정책 의사결정표
8. 상태전이 상세
9. Web 및 API 상세
10. 오류와 방어 동작
11. 코딩 및 검증 규칙
12. 단위와 요구사항 할당
13. 구현 경계
14. 추적성
15. 참고자료

템플릿 자체에는 고정 표(컬럼)가 없고(문서 통제 표 3개 — 문서 메타/변경 이력/승인 상태 — 제외) 각 장에 서술형 작성 안내만 있습니다. 각 장에서 실제로 어떤 필드로 기술할지는 `design-schema.md`의 작업용 스키마를 따르세요.

**참고:** 9장(Web 및 API 상세)은 이 상세설계 대상에 Web/API 컴포넌트가 없다면 "해당 없음"으로 명시하고 건너뛰세요 — 비워두거나 지어내지 않습니다.

## 양식이 이미 반영된 뒤 다시 구조를 바꿔야 할 때

- 구현 단위 ID(`IU-NNNN`)와 추적 링크는 그대로 유지하세요 — 바뀌면 기존 추적성이 끊어집니다.
- 정보가 없는 항목은 지어내지 말고 "확인 필요"로 표시하세요.
