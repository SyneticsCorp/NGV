# 기능 요구사항의 UML/SysML 다이어그램 표현

기능 요구사항은 텍스트 설명과 함께, 관련 동작/구조를 나타내는 다이어그램을 붙입니다. Markdown 산출물에서는 별도 도구 없이 렌더링되는 **Mermaid** 문법을 우선 사용하고, Mermaid로 표현하기 어려운 SysML 전용 다이어그램(블록 정의도, 내부 블록도 등)은 한계를 명시하고 대안을 제시합니다.

**Use Case 다이어그램의 최종 산출물은 Mermaid가 아니라 `TPL-SWE1-003_Use Case 다이어그램 템플릿.drawio`입니다.** 아래 Mermaid는 초안/검토용이며, 확정되면 `template-policy.md`의 절차에 따라 drawio 파일(`ENG-SWE1-003`)로 옮겨 최종본으로 삼으세요.

## 다이어그램 유형별 매핑

| 목적 | UML/SysML 다이어그램 | 권장 표현 방법 |
| --- | --- | --- |
| 요구사항 자체와 관계(포함/파생/만족/검증) 시각화 | SysML Requirement Diagram | Mermaid `requirementDiagram` (아래 예시) |
| 액터-시스템 상호작용 개요 | UML Use Case Diagram | Mermaid에 전용 문법 없음 → 텍스트 유스케이스 명세(액터/사전조건/기본흐름/대안흐름) + Mermaid `flowchart`로 액터-유스케이스 관계 근사 |
| 처리 흐름/알고리즘 | UML Activity Diagram | Mermaid `flowchart` |
| 상태 기반 동작 (상태 기반 EARS 요구사항과 특히 잘 맞음) | UML/SysML State Machine Diagram | Mermaid `stateDiagram-v2` |
| 컴포넌트 간 상호작용 순서 | UML Sequence Diagram | Mermaid `sequenceDiagram` |
| 구조/속성 (SysML Block Definition Diagram 근사) | UML Class Diagram | Mermaid `classDiagram` (블록≈클래스, 속성/오퍼레이션 표현) |
| 블록 간 포트/커넥터 상세 (SysML Internal Block Diagram) | — | Mermaid로 정확히 표현 불가. `flowchart`로 포트를 라벨링한 근사 표현을 쓰고, 정밀한 IBD가 필요하면 PlantUML(SysML 프로파일) 등 별도 도구 필요함을 명시 |

## Mermaid Requirement Diagram 예시 (요구사항-근거-검증 관계)

```mermaid
requirementDiagram

requirement REQ_SYS_FUNC_0012 {
  id: REQ-SYS-FUNC-0012
  text: 차량 속도가 0인 동안, 시스템은 주차 브레이크 해제를 허용하지 않는다.
  risk: high
  verifymethod: test
}

element TestCase_0012 {
  type: test case
}

TestCase_0012 - verifies -> REQ_SYS_FUNC_0012
```

- `risk`는 ISO 26262 ASIL 등 위험도와 연결지어 서술하는 용도로 사용합니다(속성 값 자체는 Mermaid 표기이며 공식 ASIL 값이 아님에 주의).
- `verifymethod`에는 `nfr-iso25010.md`/ISO 26262에서 쓰는 시험(test)/분석(analysis)/검사(inspection)/시연(demonstration) 중 실제로 적용할 기법을 적습니다.
- 관계는 `contains`, `copies`, `derives`, `satisfies`, `verifies`, `refines`, `traces` 등을 사용해 요구사항 간 계층과 추적 관계를 함께 표현할 수 있습니다 — `traceability.md`의 매트릭스와 내용이 일치해야 합니다(다이어그램과 매트릭스가 서로 다른 내용을 말하면 안 됨).

## 작성 규칙

- 하나의 다이어그램에 너무 많은 요구사항을 몰아넣지 않습니다. 응집도 높은 기능 단위로 다이어그램을 나눕니다.
- 다이어그램은 반드시 관련 요구사항 ID를 라벨/속성으로 포함해, 텍스트 요구사항과 다이어그램이 서로 참조 가능해야 합니다.
- 다이어그램만으로 요구사항을 대체하지 않습니다 — 다이어그램은 텍스트 요구사항(EARS 패턴)을 보완하는 것이지 대체하는 것이 아닙니다.
