"""!
@file types.py
@brief 안전 커널 공통 자료형(ENG-SWE3-001 4장 "공통 자료형" 표를 그대로 구현).

모든 시간 값의 단위는 초(s)이다. 이 모듈은 값 객체/열거형만 정의하며 별도 함수 계약(IU-NNNN)을
가지지 않는다(ENG-SWE3-001 2장 — 공통 자료형은 IU를 부여하지 않는다).

@par 관련 항목
- 요구사항: SWR-013, SWR-021
- 상세설계: ENG-SWE3-001 4장
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


@dataclass(frozen=True)
class RawCycleInput:
    """!
    @brief 형식 미검증 원시 Vehicle 입력(OEM-IF-001/009 원문 그대로).
    """

    rawSourceTimestamp: Any
    rawIgnitionOn: Any
    rawSensorFault: Any


@dataclass(frozen=True)
class FieldValidationResult:
    """!
    @brief 필드 단위 검증 결과 래퍼(설계상 FieldValidationResult[T] — 값 타입은 필드별로 다름:
           source_timestamp_s는 float, ignition_on/sensor_fault는 bool).
    @invariant valid=True이면 value is not None. valid=False이면 errorReason은 비공백 문자열이어야 한다.
    """

    value: Optional[Any]
    valid: bool
    rawValue: Any
    errorReason: Optional[str] = None


@dataclass(frozen=True)
class NormalizedSafetyInput:
    """!
    @brief IU-0001.normalizeCycle()의 산출물 — 검증 완료 입력.
    @invariant sensorFaultField.value는 항상 not None(10장 fail-safe 대체 규칙에 의해 보장).
    """

    sourceTimestampField: FieldValidationResult
    ignitionOnField: FieldValidationResult
    sensorFaultField: FieldValidationResult


@dataclass(frozen=True)
class FreshnessResult:
    """!
    @brief IU-0002.evaluate()의 산출물 — freshness(최신성) 판정 결과.
    @invariant elapsedS >= 0.0 또는 math.inf(최초 유효 표본 수신 전 부팅 상태 한정 sentinel).
    """

    stale: bool
    elapsedS: float
    detectedAtS: float


class SystemState(Enum):
    """!
    @brief 안전 커널 시스템 상태(상호 배타).
    """

    NORMAL = "NORMAL"
    DEGRADED = "DEGRADED"
    FAULT = "FAULT"


@dataclass(frozen=True)
class StateResult:
    """!
    @brief IU-0003.evaluate()의 산출물 — 상태 판정 결과.
    @invariant state==FAULT ⟺ warningReasonCode is not None.
    """

    state: SystemState
    changedToFault: bool
    warningReasonCode: Optional[str] = None


class LockCommand(Enum):
    """!
    @brief 확정된 차일드락 출력 커맨드(OEM-IF-005 대응).
    """

    LOCK = "LOCK"
    RELEASE = "RELEASE"


class ArbitrationCommand(Enum):
    """!
    @brief Command Arbiter 후보 커맨드(IU-0005 입출력).
    """

    LOCK = "LOCK"
    RELEASE = "RELEASE"
    NO_CHANGE = "NO_CHANGE"


@dataclass(frozen=True)
class ArbitrationResult:
    """!
    @brief IU-0005.arbitrate()의 산출물.
    @invariant blocked=True ⇒ leftCommand==NO_CHANGE and rightCommand==NO_CHANGE.
    """

    leftCommand: ArbitrationCommand
    rightCommand: ArbitrationCommand
    blocked: bool
    blockReason: Optional[str] = None


@dataclass(frozen=True)
class ConfirmedOutput:
    """!
    @brief IU-0004.confirm()의 산출물 — 확정된 좌/우 차일드락 출력. 불변 값 객체.
    """

    left: LockCommand
    right: LockCommand


@dataclass(frozen=True)
class PublishResult:
    """!
    @brief IU-0006/IU-0007 발행 결과. Phase1은 실제 I/O 없음(스텁) — success는 항상 True.
    """

    success: bool
    payload: dict = field(default_factory=dict)
    errorReason: Optional[str] = None


@dataclass(frozen=True)
class DecisionLogEntry:
    """!
    @brief IU-0008.log()의 입력. Phase1 미사용(no-op) — Phase5에서 실제 사용.
    """

    cycleId: int
    nowS: float
    state: SystemState
    confirmedOutput: ConfirmedOutput
    blocked: bool
    blockReason: Optional[str] = None


@dataclass(frozen=True)
class CycleResult:
    """!
    @brief IU-0009.evaluateCycle()의 반환값 — 시험 하네스/합성근 관찰용.
    """

    confirmedOutput: ConfirmedOutput
    stateResult: StateResult
    errorOccurred: bool
