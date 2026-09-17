---
name: aspice-auditor
description: 프로젝트 산출물을 Automotive SPICE(A-SPICE) 4.1 CL2(Capability Level 2) 기준 — PA 2.1 수행 관리와 PA 2.2 작업 산출물 관리 — 으로 감사/점검할 때 사용합니다. 대상 프로세스 영역 예: SYS.1-SYS.5, SWE.1-SWE.6, SUP.1/SUP.8/SUP.9/SUP.10, MAN.3, ACQ.4. 프로세스 영역별 산출물 참고자료, NPLF 등급 기준을 포함한 CL2 제네릭 프랙티스 근거 체크리스트, 그리고 aspice-cl2-auditor 서브에이전트가 사용하는 감사 보고서 템플릿을 제공합니다. "A-SPICE 감사", "CL2 점검", "산출물 점검" 등의 요청에 반응합니다.
---

# A-SPICE 4.1 CL2 감사원 스킬

이 스킬은 Automotive SPICE 4.1 기준으로 프로젝트 산출물이 CL2(Capability Level 2) 근거를 충분히 갖추었는지 평가하는 데 필요한 참고 지식을 담고 있습니다. 이 스킬 자체는 프로젝트 파일을 직접 읽지 않습니다 — 호출한 에이전트(보통 `aspice-cl2-auditor`)가 그 역할을 하고, 이 스킬은 무엇을 찾아야 하는지와 찾은 것을 어떻게 등급 매길지를 제공합니다.

CL2는 CL1 위에 존재합니다: 해당 프로세스 영역의 기본 관행이 이미 기대되는 산출물을 만들어내고 있어야 합니다(`references/process-work-products.md` 참고). CL2는 모든 프로세스 영역에 동일한 방식으로 평가되는 두 개의 프로세스 속성을 추가합니다.

- **PA 2.1 수행 관리(Performance Management)** — 프로세스 수행이 계획되고 통제되고 있는가?
- **PA 2.2 작업 산출물 관리(Work Product Management)** — 산출물 자체가 관리(정의, 식별, 리뷰, 통제)되고 있는가?

## 이 스킬 사용 방법

1. `references/process-work-products.md`를 읽어 대상 프로세스 영역이 어떤 산출물을 기대하는지, 그리고 이미 존재해야 할 CL1 근거가 무엇인지 파악합니다.
2. `references/cl2-checklist.md`를 읽어 각 산출물/프로세스에 물어야 할 제네릭 프랙티스 질문과 NPLF 등급 규칙을 확인합니다.
3. 프로젝트 안에서 실제 근거를 찾고(Read/Grep/Glob을 사용하는 호출 에이전트의 역할), 각 제네릭 프랙티스를 정직하게 채점합니다. 근거가 없거나 확인할 수 없으면 갭(gap)으로 처리하고, 절대 있다고 가정하지 않습니다.
4. `references/report-template.md`의 구조를 사용해 결과를 작성합니다.

## 중요한 한계

- 이 스킬의 프로세스 영역-산출물 목록(`references/process-work-products.md`)은 방향을 잡기 위한 실무자 수준 요약이며, 공식 Automotive SPICE 프로세스 평가 모델(PAM)을 그대로 옮긴 것이 아닙니다. 계약/인증용 평가가 필요하다면 공식 PAM과 BPG(Base Practices Guide) 문서가 권위 있는 출처이며, 사용자가 인증 등급의 엄밀함을 필요로 한다면 이를 알려주세요.
- "아마 괜찮을 것"이라는 이유로 등급을 올리지 마세요 — 대부분 달성/완전 달성 등급은 반드시 구체적인 산출물과 위치를 근거로 제시해야 합니다.
- 요청된 프로세스 영역이 `references/process-work-products.md`에 없다면, 예상 산출물을 지어내지 말고 그 사실을 명시적으로 알리세요.
