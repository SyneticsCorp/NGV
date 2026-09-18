# 테스트 함수 작성 규칙 (이 프로젝트 고유 요구사항)

모든 테스트 함수(메서드)는 아래 세 가지를 docstring에 **반드시** 포함해야 합니다. 이는 `writing-good-tests.md`의 "깨짐의 이름을 대라" 원칙을 실제 산출물에 강제하기 위한 것입니다.

1. **사용한 기법** — 이 테스트가 어떤 테스트 설계 기법으로 도출됐는지.
2. **긍정/부정 케이스 여부** — 정상 입력에 대한 기대 동작을 검증하는지(Positive), 비정상/오류 입력에 대한 처리를 검증하는지(Negative).
3. **Doxygen 형식의 테스트 목적** — `@brief`로 이 테스트가 무엇을 검증하는지 사람이 읽을 수 있는 한 문장.

## Doxygen 태그 형식

```python
def test<시나리오>(self):
    """!
    @brief <이 테스트가 검증하는 것을 한 문장으로>
    @technique <사용한 테스트 설계 기법>
    @case <Positive|Negative> — <그렇게 분류한 이유를 짧게>
    @breaks <이 테스트가 잡아내는 구체적인 회귀/버그 — writing-good-tests.md의 "깨짐의 이름 대기">
    """
```

- `@brief`, `@technique`, `@case`는 **필수**입니다.
- `@breaks`는 권장이며, 있으면 "이 테스트가 왜 존재하는가"에 대한 근거가 더 명확해집니다(비워두면 안 되고, 채울 수 없다면 테스트 자체가 불필요할 수 있다는 신호 — `writing-good-tests.md`의 게이트 함수를 다시 확인하세요).

## 예시

```python
def testRejectsEmptyEmail(self):
    """!
    @brief 빈 이메일 문자열이 입력되면 "Email required" 오류를 반환한다.
    @technique 동등분할(Equivalence Partitioning) — 빈 문자열은 무효 입력 클래스의 대표값
    @case Negative — 잘못된 입력에 대한 오류 처리 경로를 검증
    @breaks submitForm이 빈 이메일을 유효한 값으로 통과시키는 회귀
    """
    result = submitForm({"email": ""})
    self.assertEqual(result["error"], "Email required")

def testAcceptsMinimumBoundaryAge(self):
    """!
    @brief 나이가 허용 최소값(18)일 때 등록이 성공한다.
    @technique 경계값분석(Boundary Value Analysis) — 유효 범위의 하한 경계값
    @case Positive — 경계값 자체는 유효 입력이어야 한다
    @breaks 하한 경계 비교에 <= 대신 <를 써서 18세를 거부하는 회귀
    """
    result = registerUser({"age": 18})
    self.assertTrue(result["accepted"])
```

## 기법(`@technique`) 선택 기준

상황에 맞는 기법을 고르고, 근거 없이 아무 기법이나 적지 마세요. 자주 쓰는 기법:

| 기법 | 언제 쓰는가 |
| --- | --- |
| 동등분할(Equivalence Partitioning) | 입력을 유효/무효 클래스로 나누고 각 클래스의 대표값을 검증 |
| 경계값분석(Boundary Value Analysis) | 범위의 경계(최소/최대, 경계-1/경계/경계+1)를 검증 |
| 결정테이블 테스트(Decision Table Testing) | 여러 조건 조합에 따라 다른 동작이 나올 때(`detailed-design`의 7장 정책 의사결정표와 직결) |
| 상태전이 테스트(State Transition Testing) | 상태 기계의 전이/가드 조건을 검증(`detailed-design`의 8장 상태전이 상세와 직결) |
| 오류추측(Error Guessing) | 경험상 흔한 실수(널, 빈 값, 타입 불일치 등)를 겨냥 |
| 유스케이스 테스트(Use Case Testing) | `requirements-analysis`의 Use Case 명세서 기본/대안/예외 흐름을 그대로 검증 |
| 뮤테이션 기반(Mutation-driven) | `writing-good-tests.md`의 뮤테이션 체크에서 잡히지 않는 변형을 발견해 추가한 테스트 |

## Positive / Negative 분류 기준

- **Positive(긍정 케이스)**: 유효한 입력/정상 흐름에서 기대되는 성공 동작을 검증. "이 기능이 의도대로 동작하는가."
- **Negative(부정 케이스)**: 무효한 입력, 예외 상황, 권한 없음, 자원 실패 등에서 기대되는 오류 처리/방어 동작을 검증. `detailed-design`의 10장(오류와 방어 동작)과 직접 연결됩니다.
- 하나의 계약(사전조건/사후조건)에 Positive와 Negative 케이스가 모두 있어야 완전합니다 — Positive만 있고 Negative가 없다면 `tdd-workflow.md`의 완료 체크리스트("경계 조건과 오류 케이스를 다뤘다")를 통과하지 못한 것입니다.

## 강제 방법 (coding 서브에이전트)

품질 게이트(`quality-gates.md`)를 실행하기 전에, 새로 작성한 모든 테스트 함수의 docstring에 `@brief`, `@technique`, `@case`가 실제로 있는지 확인하세요. Bash로 간단히 점검할 수 있습니다.

```bash
python - <<'PY'
import ast, sys

def checkFile(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    missing = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
            doc = ast.get_docstring(node) or ""
            for tag in ("@brief", "@technique", "@case"):
                if tag not in doc:
                    missing.append((node.name, tag))
    return missing

for path in sys.argv[1:]:
    for name, tag in checkFile(path):
        print(f"{path}: {name} missing {tag}")
PY
```

이 스크립트가 무언가를 출력하면(누락된 태그가 있으면) 해당 테스트를 보완할 때까지 구현을 "완료"로 보고하지 마세요.
