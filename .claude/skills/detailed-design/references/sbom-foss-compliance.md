# SBOM / FOSS 라이선스 검토 (TPL-SBOM-001 대응)

`WP_Templates/Engineering/SoftwareDetailedDesignAndUnitConstruction/TPL-SBOM-001_Python 의존성 SBOM FOSS 라이선스 목록 템플릿.xlsx`를 복사해 `ENG-SBOM-001_Python 의존성 SBOM FOSS 라이선스 목록.xlsx`로 작성합니다. xlsx이므로 anthropic-skills:xlsx 스킬로 편집합니다.

## 시트 구조 (그대로 유지, 열 순서/이름을 바꾸지 않음)

헤더는 각 시트 9행이며, **실제 데이터는 10행부터** 입력합니다(다른 xlsx 템플릿과 동일한 관례).

### 시트 `SBOM`

| 열 | 의미 |
| --- | --- |
| Package | 패키지명 |
| Version | 버전 |
| Dependency Type | 직접/전이(transitive) 의존성 여부, 런타임/개발 의존성 여부 등 |
| SPDX | SPDX 라이선스 식별자 (예: `MIT`, `Apache-2.0`) |
| Evidence Type | 라이선스 정보를 확인한 방법(패키지 메타데이터, LICENSE 파일, 저장소 등) |
| Evidence Locator | 근거 위치(URL, 파일 경로, 커맨드 출력 등 — 재현 가능해야 함) |
| Distribution | 이 패키지가 배포물에 포함되는지, 어떻게 포함되는지(정적/동적 링크, 별도 프로세스 등) |
| Remark | 비고 |

### 시트 `FOSS Review`

| 열 | 의미 |
| --- | --- |
| Review ID | 검토 항목 고유 ID |
| Scope | 검토 대상(패키지 또는 패키지 그룹) |
| Criterion | 검토 기준(예: 카피레프트 여부, 상업적 배포 허용 여부, 의무 고지 요건) |
| Evidence | 검토 근거 |
| Result | 판정 결과(적합/조건부적합/부적합/검토중) |
| Owner | 검토 담당자 |
| Date | 검토일 |
| Limitation | 판정의 한계(예: "라이선스 텍스트만 확인, 법무 검토 미실시") |

### 시트 `Change History`

| Revision | 변경일 | 작성 역할 | 변경 내용 | 검토 상태 | 승인 상태 |
| --- | --- | --- | --- | --- | --- |

## 작성 규칙

1. **실제로 사용 중인 의존성만 기록합니다.** 프로젝트의 의존성 선언 파일(`pyproject.toml`, `requirements.txt`, `poetry.lock`, `Pipfile.lock` 등)을 Glob/Read/Bash로 실제 확인한 뒤 `SBOM` 시트를 채웁니다. 지어내거나 짐작으로 채우지 않습니다.
2. **Evidence Locator는 재현 가능해야 합니다.** "확인함"처럼 근거 없는 문구를 적지 않습니다 — 실제 파일 경로, URL, 또는 확인에 사용한 명령을 적습니다.
3. **`Result`를 "적합"으로 단정하기 전에 `Criterion`과 `Evidence`가 실제로 채워져 있는지 확인합니다.** 근거 없는 적합 판정은 A-SPICE PA 2.2(작업 산출물 관리)와 이 프로젝트의 "실행 불가능한 검증방안 금지" 원칙(`requirements-analysis`의 `nfr-iso25010.md`)에 모두 위배됩니다.
4. **법무적 최종 판단이 필요한 라이선스(예: 카피레프트 계열)는 "조건부적합" 또는 "검토중"으로 두고 `Limitation`에 한계를 명시**하세요 — 이 스킬은 법률 자문을 대체하지 않습니다.
5. 의존성이 변경될 때마다(`ENG-SBOM-001` 갱신) `Change History` 시트에 이력을 남기고, `template-policy.md`의 산출물 ID 규칙에 따라 관리합니다.
