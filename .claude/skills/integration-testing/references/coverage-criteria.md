# 함수 커버리지·Call 커버리지 100% (필수)

사용자가 명시적으로 요구한 지표입니다. ISO 26262 Part 6은 소프트웨어 통합시험 수준의 구조적 커버리지로 **함수 커버리지(function coverage)**와 **호출 커버리지(call coverage)**를 제시합니다 — 단위 수준(SWE.4, `tdd`/`quality-gates.md`)의 구문/분기/MC-DC 커버리지와는 다른, 통합 수준 전용 지표입니다. 이 문서는 공식 표준 문서를 대체하지 않는 실무 요약입니다.

## 정의

- **함수 커버리지 100%**: 이번 통합 범위에 포함된 모든 인터페이스 오퍼레이션/함수(`ENG-SWE2-001` 6장 인터페이스 명세에 정의된 것)가 통합시험 실행 중 최소 한 번 이상 호출되어야 합니다.
- **Call 커버리지 100%**: 아키텍처의 컴포넌트 의존성 그래프(`architecture-diagrams.md`의 의존성 그래프)와 인터페이스 명세에 정의된 모든 "제공자→사용자" 호출 관계(호출 지점/엣지) 각각이 통합시험 실행 중 최소 한 번 이상 실제로 실행되어야 합니다. 함수가 호출됐다는 것만으로는 부족합니다 — *어떤 경로로* 호출되는지(어느 컴포넌트가 어느 인터페이스를 통해 호출하는지)까지 실행되어야 합니다.

## 측정 방법 (`coverage.py`)

Python 표준 커버리지 도구 `coverage.py`(`pip install coverage`)로 실측합니다. 느낌이나 케이스 개수로 "달성했다"고 판단하지 않습니다.

### 1. 실행하며 커버리지 수집

```bash
coverage run --branch -m unittest discover -s <통합테스트 디렉터리> -p "test_*.py" -v
coverage json -o coverage.json
```

### 2. 함수 커버리지 확인

각 인터페이스 함수의 정의부 시작 줄(첫 실행 가능한 줄)이 `coverage.json`의 `executed_lines`에 있는지 확인합니다. `radon cc -j`(`tdd`/`quality-gates.md`와 동일한 방식)로 함수의 `lineno`를 얻고 대조하는 스크립트 예시:

```python
import json, subprocess

def getFunctionCoverage(sourceFile, coverageJsonPath):
    radonResult = json.loads(subprocess.check_output(["radon", "cc", sourceFile, "-j"]))
    coverageData = json.load(open(coverageJsonPath))
    executed = set(coverageData["files"][sourceFile]["executed_lines"])
    missing = []
    for item in radonResult[sourceFile]:
        if item["lineno"] not in executed:
            missing.append(item["name"])
    return missing  # 비어 있으면 함수 커버리지 100%
```

### 3. Call 커버리지 확인

인터페이스 호출이 일어나는 **호출 지점(call site) 줄 번호**를 `ast` 모듈로 찾고(예: `ast.Call` 노드가 있는 줄), 그 줄이 `executed_lines`에 있는지 확인합니다. 이는 "이 컴포넌트가 저 컴포넌트의 이 오퍼레이션을 실제로 호출했다"를 직접 증명합니다.

```python
import ast

def findCallSites(sourceFile, targetFunctionNames):
    tree = ast.parse(open(sourceFile, encoding="utf-8").read())
    sites = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            calledName = getattr(node.func, "attr", getattr(node.func, "id", None))
            if calledName in targetFunctionNames:
                sites.append(node.lineno)
    return sites
```

`targetFunctionNames`는 아키텍처 인터페이스 명세(`IF-NNNN`)의 오퍼레이션 이름 목록에서 가져옵니다. 각 호출 지점 줄이 실행됐는지 `coverage.json`과 대조하면 Call 커버리지를 계산할 수 있습니다.

### 4. 100% 미달 시

- 어떤 함수/호출이 실행되지 않았는지 구체적으로 식별합니다.
- 그 함수/호출을 실행하는 통합시험 케이스(`ENG-SWE5-002`)를 추가하고 다시 실행/재측정합니다.
- 정말로 실행할 수 없는 코드(예: 도달 불가능한 방어적 코드, 이번 통합 범위 밖의 인터페이스)라면, 임의로 "달성"으로 보고하지 말고 `ENG-SWE5-001` 12장(적용 한계)에 그 코드와 사유를 명시하고 사용자에게 확인을 요청합니다. 근거 없이 커버리지 기준을 낮추지 않습니다.

## `ENG-SWE5-001`에 기록할 내용

- 5장(진입 및 종료 기준): "함수 커버리지 100%, Call 커버리지 100%"를 종료 기준으로 명시.
- 7장(시험 설계기법): 위 측정 방법(`coverage.py` + AST 대조)과 도구를 근거로 기록.

## `ENG-SWE5-003`에 기록할 내용

- `Run Summary` 시트에 이번 실행의 함수/Call 커버리지 실측치(%)를 `Limitation` 열 또는 비고로 남겨, 100% 미달 시 그 사실이 결과서에서 바로 보이게 합니다.
