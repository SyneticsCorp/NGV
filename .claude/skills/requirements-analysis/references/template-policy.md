# 템플릿 적용 정책

사용자가 제시하기로 한 요구사항 명세서 템플릿이 확인되었습니다: `WP_Templates/Engineering/SoftwareRequirementsAnalysis/` 아래의 공식 템플릿입니다. 더 이상 템플릿 미반영 상태가 아닙니다 — 아래 지정 템플릿을 반드시 사용하세요.

## 지정 템플릿

| Template ID | 파일 | 용도 |
| --- | --- | --- |
| TPL-SWE1-001 | `WP_Templates/Engineering/SoftwareRequirementsAnalysis/TPL-SWE1-001_SW 요구사항 명세서 템플릿.docx` | SW 요구사항 명세서 본문 |
| TPL-SWE1-002 | `WP_Templates/Engineering/SoftwareRequirementsAnalysis/TPL-SWE1-002_Use Case 명세서 템플릿.docx` | Use Case 명세서 |
| TPL-SWE1-003 | `WP_Templates/Engineering/SoftwareRequirementsAnalysis/TPL-SWE1-003_Use Case 다이어그램 템플릿.drawio` | Use Case 다이어그램 |

전체 등록 정보는 `WP_Templates/PRC-TPL-001_표준 산출물 양식 등록부.xlsx`(시트 `Template Register`, `Engineering Template Files`)에 있습니다.

참고: `OEM_Sample/OEM-SWR-001_OEM SW 요구사항 사양서.docx`는 우리가 채우는 템플릿이 아니라, OEM이 공급자에게 전달하는 **입력 요구사항 예시**입니다. 상위 요구사항(추적성 매트릭스의 "Upper Req")의 형태를 참고하는 용도로만 사용하세요.

## 파일명/산출물 ID 규칙

- 템플릿 ID: `TPL-<프로세스>-NNN` (예: `TPL-SWE1-001`).
- 실제 산출물(작성 완료본) ID/파일명: `ENG-<프로세스>-NNN_<명칭>.<확장자>` (예: `ENG-SWE1-001_SW 요구사항 명세서.docx`, `ENG-SWE1-002_Use Case 명세서.docx`, `ENG-SWE1-003_Use Case 다이어그램.drawio`).
- 산출물은 템플릿 파일을 **복사한 뒤** 위 규칙으로 이름을 바꿔 작성합니다. 원본 템플릿 파일은 수정하지 않습니다.
- 저장 위치: 프로젝트에 기존 산출물 폴더 구조가 없다면 `Deliverables/Engineering/SoftwareRequirementsAnalysis/`에 두는 것을 기본으로 제안하고, 사용자가 다른 위치를 지정하면 그것을 따릅니다(이 경로는 확정된 프로젝트 관례가 아니라 제안값입니다).

## 작성 방법 (`WP_Templates/Engineering/README.md` 규칙)

- **DOCX(TPL-SWE1-001, TPL-SWE1-002)**: docx는 anthropic-skills:docx 스킬로 열어 작성합니다. 각 장/절 제목은 그대로 유지하고, 제목 아래의 "작성 안내:" 서술형 가이드 문구를 실제 내용으로 교체합니다. 장/절 구조 자체를 임의로 바꾸지 않습니다(아래 목차 참고).
- **XLSX(추적 매트릭스 등)**: 기존 시트/열 구조를 그대로 유지하고, 실제 데이터는 **10행부터** 입력합니다(`traceability.md` 참고).
- **DRAWIO(TPL-SWE1-003)**: 파일은 일반 XML이며 Read/Edit로 직접 열람·수정 가능합니다. 템플릿에는 실제 UML 표기법 없이 자리표시자 도형(경계 상자, 액터 사각형, 대상요소 사각형, 화살표 1개, 노란 안내 박스)만 있습니다. 안내 박스가 요구하는 4가지(①시스템경계와대상기능 ②주액터와보조액터 ③Use Case와관계 ④관련요구사항ID)를 실제 요소로 채우고 안내 박스는 삭제합니다. 정확한 배치가 어려우면 먼저 `uml-sysml-diagrams.md`의 Mermaid로 초안을 만들어 사용자와 확인한 뒤 drawio로 옮기세요. 검토본/베이스라인 생성 시 PNG로 함께 내보냅니다.

## TPL-SWE1-001 목차 (변경 없이 그대로 사용)

1. 목적 및 적용범위 (1.1 목적 / 1.2 적용범위 / 1.3 적용경계)
2. 요구사항 작성 및 판정 규칙 (2.1 식별 및 상태 규칙 / 2.2 품질 판정 기준)
3. 상태와 우선순위
4. 기능 및 안전 관련 SW 요구사항 (4.1 기능요구사항 / 4.2 안전관련SW요구사항)
5. 입력 데이터 사전
6. 외부 인터페이스 요구
7. 비기능 및 환경 제약
8. 분석 결과와 가정
9. 하향 할당 및 검증 계획
10. 범위 밖 주장
11. 추적성
12. 참고자료

템플릿 자체에는 요구사항 항목을 담는 고정 표(컬럼)가 없고 서술형 가이드만 있습니다. 각 장에서 실제로 어떤 필드로 요구사항을 기술할지는 `requirement-schema.md`의 작업용 스키마를 따르세요 — 그 스키마가 위 장/절에 어떻게 대응되는지도 함께 정리되어 있습니다.

## TPL-SWE1-002 목차 (Use Case 명세서, 변경 없이 그대로 사용)

1. 목적 및 적용범위
2. 액터와 시스템 경계
3. Use Case 목록 (Use Case ID, 명칭, 목적, 주 액터, 관련 요구사항, 우선순위)
4. Use Case 상세 (4.1 기본정보 / 4.2 사전조건과 트리거 / 4.3 기본흐름 / 4.4 대안흐름 / 4.5 예외흐름 / 4.6 사후조건 — Use Case마다 이 하위 절을 복제)
5. 비대상 시나리오
6. 추적성
7. 참고자료
