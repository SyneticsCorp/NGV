# 아키텍처 설계서 양식 적용 정책

사용자가 제시하기로 한 아키텍처 설계서 양식이 확인되었습니다: `WP_Templates/Engineering/SoftwareArchitecturalDesign/` 아래의 공식 템플릿입니다. 더 이상 양식 미반영 상태가 아닙니다 — 아래 지정 양식을 반드시 사용하세요.

## 지정 템플릿

| Template ID | 파일 | 용도 |
| --- | --- | --- |
| TPL-SWE2-001 | `WP_Templates/Engineering/SoftwareArchitecturalDesign/TPL-SWE2-001_SW 아키텍처 설계서 템플릿.docx` | 아키텍처 설계서 본문 |
| TPL-SWE2-002 | `WP_Templates/Engineering/SoftwareArchitecturalDesign/TPL-SWE2-002_SW 아키텍처 UML 템플릿.drawio` | 아키텍처 구조 다이어그램 |

전체 등록 정보는 `WP_Templates/PRC-TPL-001_표준 산출물 양식 등록부.xlsx`(시트 `Template Register`, `Engineering Template Files`)에 있습니다.

## 파일명/산출물 ID 규칙

- 산출물 ID/파일명: `ENG-SWE2-001_SW 아키텍처 설계서.docx`, `ENG-SWE2-002_SW 아키텍처 UML.drawio` (`requirements-analysis` 스킬과 동일한 `TPL-*` → `ENG-*` 규칙).
- 템플릿을 복사한 뒤 이름을 바꿔 작성하고, 원본 템플릿 파일은 수정하지 않습니다.
- 저장 위치 기본 제안: `Deliverables/Engineering/SoftwareArchitecturalDesign/` (확정된 프로젝트 관례가 아니라 제안값 — 사용자가 다른 위치를 지정하면 그것을 따릅니다).

## 작성 방법 (`WP_Templates/Engineering/README.md` 규칙)

- **DOCX(TPL-SWE2-001)**: anthropic-skills:docx 스킬로 작성합니다. 장/절 제목은 그대로 유지하고, "작성 안내:" 서술형 가이드를 실제 내용으로 교체합니다.
- **DRAWIO(TPL-SWE2-002)**: XML이므로 Read/Edit로 직접 열람·수정 가능합니다. 자리표시자 도형만 있고 특정 UML 셰이프 라이브러리는 쓰지 않습니다. 안내 박스가 요구하는 4가지(①소프트웨어 요소와 계층 ②제공 및 요구 인터페이스 ③허용된 의존 방향 ④요구사항 할당 ID)를 실제 요소로 채우고 안내 박스는 삭제합니다. 먼저 `architecture-diagrams.md`의 Mermaid로 초안을 만들어 확인한 뒤 drawio로 옮기는 것을 권장합니다. 검토본/베이스라인 생성 시 PNG를 함께 내보냅니다.

## TPL-SWE2-001 목차 (변경 없이 그대로 사용)

1. 목적 및 적용범위
2. 아키텍처 설계 원칙
3. 논리 아키텍처 (3.1 아키텍처 요소: ID, 명칭, 목적, 제공 기능, 소유 책임 / 3.2 관계와 제약)
4. 컴포넌트 책임
5. 정적 의존성
6. 인터페이스 명세 (6.1 내부 인터페이스 / 6.2 외부 인터페이스 — 인터페이스 ID, 제공자, 사용자, 데이터, 호출 조건, 시간 제약, 오류 계약)
7. 동적 동작
8. 상태 전이
9. 오류 격리와 안전 동작
10. 품질 속성 분석
11. 통합 전략 (통합 단위, 순서, 인터페이스 검증, 스텁 또는 드라이버, 회귀 범위)
12. 요구사항 할당
13. 자원 및 배포 경계
14. 추적성
15. 참고자료

템플릿 자체에는 컴포넌트/인터페이스를 담는 고정 표가 없고 각 절에 서술형 가이드만 있습니다. 각 절에서 어떤 필드로 기술할지는 `design-principles.md`·`interface-and-integration.md`의 작업용 표를 그대로 사용하세요. 위 목차의 각 항목(예: 6장 인터페이스 필드 목록)은 이미 그 스킬 문서에 반영되어 있습니다.

**중요:** 이 템플릿에는 ASIL을 담는 전용 필드/컬럼이 없습니다. ASIL·안전 관련 사항은 9장(오류 격리와 안전 동작)에 서술형으로 기술합니다(`iso26262-aspice-alignment.md` 참고). 임의로 전용 표를 새로 만들지 말고 9장 서술 안에서 구조적으로(요소별로 나누어) 다루세요.

## 양식이 이미 반영된 뒤 다시 구조를 바꿔야 할 때

- 컴포넌트 ID, 인터페이스 ID, 추적 링크는 그대로 유지하세요 — 바뀌면 기존 추적성이 끊어집니다.
- 정보가 없는 항목은 지어내지 말고 "확인 필요"로 표시하세요.
