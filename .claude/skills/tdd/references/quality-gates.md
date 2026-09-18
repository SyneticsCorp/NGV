# 품질 게이트 (CLAUDE.md 구현 지침의 4대 필수 지표)

CLAUDE.md는 아래 4개 지표를 **반드시** 준수하라고 명시합니다. 각 지표를 "느낌"으로 판단하지 말고 실제로 radon/pylint를 실행해 수치로 확인하세요. 기준을 넘는 코드는 리팩터링해서 통과시키는 것이 원칙이며, 예외로 그냥 넘기지 않습니다(예외가 불가피하다고 판단되면 사용자에게 먼저 확인).

두 도구 모두 PyPI에서 바로 설치 가능한 표준 오픈소스 도구입니다(`pip install radon pylint`, 이미 설치되어 있지 않다면 설치).

## 1. 함수 순수코드라인 ≤ 50 (radon)

radon `raw` 명령은 파일 단위로만 LOC/SLOC을 세므로, 함수 단위로 보려면 radon `cc`(JSON)로 각 함수의 시작/끝 줄 번호를 얻은 뒤 그 범위의 빈 줄/주석 전용 줄을 제외하고 셉니다.

```bash
radon cc <파일> -j
```

JSON 결과의 각 함수 항목에서 `lineno`, `endline`을 확인하고, 아래처럼 그 범위의 순수 코드 라인 수를 계산합니다(빈 줄과 `#`으로 시작하는 줄, docstring 전용 줄 제외).

```python
def countPureCodeLines(filePath, startLine, endLine):
    with open(filePath, encoding="utf-8") as f:
        lines = f.readlines()[startLine - 1:endLine]
    return sum(
        1 for line in lines
        if line.strip() and not line.strip().startswith("#")
    )
```

(docstring 블록 전체를 제외하려면 `ast` 모듈로 함수의 docstring 노드 범위를 추가로 걸러내세요.) 결과가 50을 넘으면 함수를 분리하세요.

## 2. 함수 순환복잡도 ≤ 10 (radon)

```bash
radon cc <경로> -n C -s
```

`-n C`는 복잡도 등급 C(11~20) 이상만 출력합니다 — 즉 이 명령의 출력에 나오는 함수는 전부 기준(10) 위반입니다. 출력이 없으면 통과입니다.

## 3. 중복 코드는 7라인까지 허용 (pylint)

"7라인까지 허용"은 8라인 이상 중복부터 위반이라는 뜻입니다. 저장소 루트의 `.pylintrc`에 이미 반영되어 있습니다(새로 만들지 마세요).

```ini
[SIMILARITIES]
min-similarity-lines=8
ignore-comments=yes
ignore-docstrings=yes
```

```bash
pylint --disable=all --enable=duplicate-code <경로>
```

`R0801 duplicate-code`가 보고되면 위반입니다. 공통 로직을 함수/모듈로 추출해 제거하세요.

## 4. Doxygen 방식 주석 20% 이상

측정 방법(파일 단위 비율로 해석 — 다른 기준을 원하면 사용자와 재확인):

```bash
radon raw <파일> -s
```

출력의 `comments`(순수 주석 줄) 또는 `comments + multi`(docstring 포함)를 `loc`(전체 줄)로 나눈 비율이 20% 이상이어야 합니다. 형식 자체는 `doxygen-comments.md`를 따르세요 — 비율만 채우고 형식이 Doxygen 태그(`@brief`/`@param`/`@return`)를 안 갖추면 지표를 만족한 것이 아닙니다.

## 네이밍 규칙 — 3자 이상, camelCase

CLAUDE.md 지침이며 PEP 8 기본값(snake_case)과 다릅니다. 저장소 루트의 `.pylintrc`에 이미 이 설정이 반영되어 있습니다(그렇지 않으면 pylint가 기본 snake_case 규칙으로 camelCase 이름을 오히려 위반으로 표시합니다) — 새로 만들지 말고 그 파일을 그대로 사용하세요. `{2,}` 뒤 정규식은 "첫 글자 + 최소 2글자" = 최소 3글자를 강제합니다. 클래스명 등 CLAUDE.md가 규칙을 명시하지 않은 대상은 Python 관례(PascalCase)를 유지하되, 프로젝트에 다른 지시가 있으면 그것을 따르세요. `.pylintrc`를 수정할 일이 생기면 이 문서도 함께 갱신하세요.

```bash
pylint --disable=all --enable=invalid-name <경로>
```

## 게이트 실행 순서 (Refactor 단계 직후)

1. `radon cc -n C -s` (복잡도)
2. 함수별 순수코드라인 계산 (위 스크립트)
3. `pylint --enable=duplicate-code`
4. `pylint --enable=invalid-name`
5. `radon raw -s` (주석 비율)

다섯 가지 모두 통과해야 구현이 "완료"입니다. 하나라도 실패하면 4단계(구현 완료 보고)로 넘어가지 마세요.
