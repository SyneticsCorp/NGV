# TDD 절차 (Red-Green-Refactor, unittest)

CLAUDE.md는 "TDD 방식으로 진행"을 **반드시** 요구합니다. 테스트를 나중에 추가하는 것은 TDD가 아닙니다 — 항상 실패하는 테스트를 먼저 작성합니다.

## 1. Red — 실패하는 테스트 먼저 작성

1. 구현할 함수 계약(`detailed-design`의 `IU-NNNN.함수명`: 입력/출력/사전조건/사후조건/부작용/예외)을 확인합니다.
2. 계약의 각 항목(정상 케이스, 경계값, 사전조건 위반 시 예외 등)을 별도 테스트 메서드로 나눕니다 — 테스트 하나에 여러 계약을 몰아넣지 않습니다.
3. `unittest.TestCase`로 테스트를 작성합니다.
4. 아직 구현이 없거나 미완성이라 테스트가 **실패하는 것을 실제로 실행해 확인**합니다. 실행하지 않고 "실패할 것"이라고 가정하지 않습니다.

```python
import unittest

class TestCalculateOffset(unittest.TestCase):
    def testReturnsZeroWhenInputIsZero(self):  # 3자 이상 camelCase 메서드명
        self.assertEqual(calculateOffset(0), 0)

    def testRaisesWhenInputBelowLowerBound(self):
        with self.assertRaises(ValueError):
            calculateOffset(-1)
```

## 2. Green — 테스트를 통과시키는 최소 구현

- 테스트를 통과시키는 데 필요한 최소한의 코드만 작성합니다. 아직 테스트가 없는 동작을 미리 구현하지 않습니다(요구되지 않은 범위 확장 금지).
- 구현 후 반드시 테스트를 실행해 통과를 확인합니다: `python -m unittest <테스트파일 또는 모듈> -v`

## 3. Refactor — 리팩터링

- 테스트가 계속 통과하는 상태를 유지하면서(매 변경마다 재실행) 중복 제거, 이름 개선, 구조 정리를 수행합니다.
- 리팩터링이 끝나면 `quality-gates.md`의 품질 게이트를 실행합니다. 기준 미달이면 이 단계에서 해결합니다 — 다음 함수로 넘어가지 않습니다.

## 테스트 파일 위치/명명 규칙

- 테스트 파일: `test_<대상 모듈>.py` (프로젝트에 이미 다른 관례가 있으면 그것을 따릅니다 — Glob으로 기존 `test_*.py`/`tests/` 구조를 먼저 확인하세요).
- 테스트 메서드명: `test<시나리오>` 형태의 camelCase, 3자 이상(CLAUDE.md 네이밍 규칙 적용).
- 하나의 테스트 클래스는 하나의 구현 단위(`IU-NNNN`)에 대응시키는 것을 기본으로 합니다.

## 실행 방법

```bash
python -m unittest discover -s <테스트 디렉터리> -p "test_*.py" -v
```

프로젝트에 테스트 디렉터리 구조가 아직 없다면 임의로 만들지 말고, `detailed-design`의 13장(구현 경계)이나 사용자에게 위치를 확인하세요.
