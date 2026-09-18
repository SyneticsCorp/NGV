# Doxygen 방식 주석 (Python)

Doxygen은 원래 C/C++/Java용 도구지만 Python도 지원합니다(공식 Doxygen이 Python 파서를 내장하고 있음, 또는 `doxypypy` 필터 사용). 이 프로젝트는 아래 형식을 기본으로 사용합니다.

**이 문서는 구현(프로덕션) 코드의 주석 형식을 다룹니다.** 테스트 함수(`test*`)의 Doxygen 주석 형식(`@technique`, `@case` 등 테스트 전용 태그)은 `test-annotation.md`를 따르세요.

## 함수/메서드 주석 형식

```python
def calculateOffset(rawValue, calibration):
    """!
    @brief 원시 센서값을 보정값으로 변환한다.

    @param rawValue 원시 센서 입력값 (단위: raw count)
    @param calibration 보정 계수 객체 (IU-0007 공통 자료형 참고)
    @return 보정된 오프셋 값 (단위: mm)
    @exception ValueError rawValue가 유효 범위를 벗어나면 발생

    @par 관련 항목
    - 요구사항: SWR-0012
    - 함수 계약: IU-0007.calculateOffset (상세설계 5장)
    """
```

- `"""!`로 시작하는 docstring은 Doxygen이 특수 주석으로 인식합니다(Python용 Doxygen 설정에서 `JAVADOC_AUTOBRIEF`/기본 주석 스타일과 함께 사용).
- 최소 포함 항목: `@brief`, `@param`(각 파라미터마다), `@return`(반환값이 있으면), `@exception`(예외를 던지면). `design-schema.md`(detailed-design 스킬)의 함수 계약 필드와 1:1로 대응시킵니다.
- `@par 관련 항목`에 요구사항 ID(`SWR-NNNN`)와 구현 단위 ID(`IU-NNNN.함수명`)를 남겨 추적성을 코드 안에서도 확인할 수 있게 합니다(`traceability-and-integration.md`와 별개로, 코드를 직접 읽는 사람을 위한 보조 수단).

## 모듈/클래스 주석

```python
"""!
@file offset_calculator.py
@brief 센서 오프셋 계산 모듈 (IU-0007)
"""
```

## 인라인 주석

로직이 자명하지 않은 부분(왜 이렇게 처리했는지)에만 일반 `#` 주석을 사용합니다. 코드가 이미 말해주는 내용을 그대로 반복하는 주석은 작성하지 않습니다 — 분량을 채우기 위한 불필요한 주석은 `quality-gates.md`의 20% 기준을 형식적으로 맞추는 수단으로 쓰지 않습니다. 20% 기준은 어디까지나 결과 지표이며, 목표는 코드를 이해 가능하게 만드는 것입니다.

## Doxygen 실행 (선택)

프로젝트가 실제로 Doxygen HTML 문서를 생성해야 한다면:

```bash
doxygen -g Doxyfile   # 최초 1회, 설정 파일 생성
# Doxyfile에서 OPTIMIZE_OUTPUT_JAVA=NO, EXTENSION_MAPPING에 py=Python 등 확인
doxygen Doxyfile
```

Doxygen이 프로젝트 환경에 설치되어 있는지 먼저 확인하세요(`which doxygen` 또는 `doxygen --version`). 설치되어 있지 않다면 문서 생성 여부를 사용자에게 확인하고, 없어도 위 주석 형식 자체는 계속 유지합니다(형식 준수와 실제 HTML 생성은 별개입니다).
