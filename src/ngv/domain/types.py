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
    @brief 형식 미검증 원시 Vehicle 입력(OEM-IF-001/002/003/007/008/009 원문 그대로).

    Phase2 신규 6필드(rawCrashStatus 등)와 Phase3 신규 3필드(rawVehicleSpeedKph 등)는
    default=None — 호출부가 아직 값을 채우지 않은 경우 IU-0001 검증 함수가 그대로
    "MISSING"으로 판정하도록 하기 위함이며(4장 invariant), 이전 Phase 호출부(테스트 등)와의
    하위 호환을 목적으로 임의 값을 대체하지 않는다.
    """

    rawSourceTimestamp: Any
    rawIgnitionOn: Any
    rawSensorFault: Any
    rawCrashStatus: Any = None
    rawLeftApproachRisk: Any = None
    rawRightApproachRisk: Any = None
    rawFireDetected: Any = None
    rawOvertemperatureDetected: Any = None
    rawAdultPresent: Any = None
    rawVehicleSpeedKph: Any = None
    rawIsofixLeft: Any = None
    rawIsofixRight: Any = None


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


def buildMissingFieldDefault():
    """!
    @brief NormalizedSafetyInput의 Phase2 신규 필드 default_factory — "MISSING"으로 검증된
           FieldValidationResult를 만든다(값 자체는 None이 아닌 객체이므로 하위 IU의
           "not None" 사전조건은 항상 만족되고, valid=False이므로 10.4절 원칙에 따라
           새 능동 후보를 생성하지 않는다).
    @return FieldValidationResult(value=None, valid=False, rawValue=None, errorReason="MISSING")
    """
    return FieldValidationResult(value=None, valid=False, rawValue=None, errorReason="MISSING")


@dataclass(frozen=True)
class NormalizedSafetyInput:
    """!
    @brief IU-0001.normalizeCycle()의 산출물 — 검증 완료 입력.
    @invariant sensorFaultField.value는 항상 not None(10장 fail-safe 대체 규칙에 의해 보장).
    @invariant Phase2/Phase3 신규 필드는 대체 보장이 없다 — valid=False이면 value는 None일 수
               있다(10.4절/10.7절 원칙). default_factory는 하위 호환을 위해 "MISSING"을 채운다.
    """

    sourceTimestampField: FieldValidationResult
    ignitionOnField: FieldValidationResult
    sensorFaultField: FieldValidationResult
    crashStatusField: FieldValidationResult = field(default_factory=buildMissingFieldDefault)
    leftApproachRiskField: FieldValidationResult = field(default_factory=buildMissingFieldDefault)
    rightApproachRiskField: FieldValidationResult = field(default_factory=buildMissingFieldDefault)
    fireField: FieldValidationResult = field(default_factory=buildMissingFieldDefault)
    overtempField: FieldValidationResult = field(default_factory=buildMissingFieldDefault)
    adultField: FieldValidationResult = field(default_factory=buildMissingFieldDefault)
    vehicleSpeedField: FieldValidationResult = field(default_factory=buildMissingFieldDefault)
    isofixLeftField: FieldValidationResult = field(default_factory=buildMissingFieldDefault)
    isofixRightField: FieldValidationResult = field(default_factory=buildMissingFieldDefault)


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
    @brief 안전 커널 시스템 상태(상호 배타). Phase3: OFF 추가(FAULT>OFF>DEGRADED>NORMAL).
    """

    NORMAL = "NORMAL"
    DEGRADED = "DEGRADED"
    FAULT = "FAULT"
    OFF = "OFF"


@dataclass(frozen=True)
class StateResult:
    """!
    @brief IU-0003.evaluate()의 산출물 — 상태 판정 결과.
    @invariant state ∈ {FAULT, OFF} ⟺ warningReasonCode is not None(Phase3 확장 — 기존
               "state==FAULT ⟺..."에서 OFF 포함으로 확장). changedToFault는 Phase1 의미
               ("이번 주기에 새로 FAULT로 전이했는가")를 그대로 유지하며, OFF 전이 전용
               플래그는 추가하지 않는다(어떤 SWR도 요구하지 않음, 13장 구현 경계).
    """

    state: SystemState
    changedToFault: bool
    warningReasonCode: Optional[str] = None


class CrashStatus(Enum):
    """!
    @brief 충돌 상태(OEM-IF-002 대응, IU-0010 입력).
    """

    NONE = "NONE"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"


class Door(Enum):
    """!
    @brief CandidateCommand의 적용 대상 문(door).
    """

    LEFT = "LEFT"
    RIGHT = "RIGHT"
    BOTH = "BOTH"


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
class CandidateCommand:
    """!
    @brief IU-0010~0016이 생성하는 후보 커맨드(Phase2/Phase3 신규, IU-0005 입력).
    @invariant command ∈ {LOCK, RELEASE}(NO_CHANGE 금지 — 후보는 항상 명시적 동작).
    @invariant priority ∈ {1..6}(Phase3 확장 — PRIORITY_CRASH=1/APPROACH_RISK=2/
               FIRE_OVERTEMP_OCCUPANT=3/IGNITION_OFF_RELEASE=4/ISOFIX_FORCED_LOCK=5/
               AUTO_DRIVE_LOCK=6). IU-0005.selectForDoor()의 최소-priority 선택 알고리즘은
               이 값 범위 확장과 무관하게 코드 변경 없이 그대로 동작한다(OCP, 5.2b절).
    @invariant reasonCode는 비공백 문자열.
    """

    door: Door
    command: ArbitrationCommand
    priority: int
    reasonCode: str


@dataclass(frozen=True)
class CrashEvaluationResult:
    """!
    @brief IU-0010.evaluate()의 산출물(Phase2 신규, IF-0016).
    @invariant status==CONFIRMED ⟺ releaseCandidate is not None.
    @invariant status==PENDING ⟹ pendingHoldApplied=True(그 외 False).
    """

    status: CrashStatus
    releaseCandidate: Optional[CandidateCommand]
    pendingHoldApplied: bool


@dataclass(frozen=True)
class ApproachRiskResult:
    """!
    @brief IU-0011.evaluate()의 산출물(Phase2 신규, IF-0017).
    @invariant leftRiskActive ⟺ leftSuppressCandidate is not None ⟺ leftReasonCode is not None
               (우측 대칭, 좌우 완전 독립 — SWR-009).
    """

    leftRiskActive: bool
    rightRiskActive: bool
    leftSuppressCandidate: Optional[CandidateCommand]
    rightSuppressCandidate: Optional[CandidateCommand]
    leftReasonCode: Optional[str]
    rightReasonCode: Optional[str]


@dataclass(frozen=True)
class OverrideDecision:
    """!
    @brief IU-0012.decide()의 산출물(Phase2 신규, IF-0018).
    @invariant leftOverrideActive ⟹ leftOverrideReasonCode is not None(우측 대칭).
    """

    leftOverrideActive: bool
    rightOverrideActive: bool
    leftOverrideReasonCode: Optional[str]
    rightOverrideReasonCode: Optional[str]


@dataclass(frozen=True)
class ForcedReleaseResult:
    """!
    @brief IU-0013.evaluate()의 산출물(Phase2 신규, IF-0019).
    @invariant triggered ⟺ len(triggeredReasonCodes)>0 ⟺ releaseCandidate is not None.
    """

    triggered: bool
    releaseCandidate: Optional[CandidateCommand]
    triggeredReasonCodes: list


@dataclass(frozen=True)
class VehicleSpeedLockResult:
    """!
    @brief IU-0014.evaluate()의 산출물(Phase3 신규, IF-0021).
    @invariant locked=True ⟺ lockCandidate is not None. lockCandidate가 있으면 door=BOTH,
               command=LOCK, priority=PRIORITY_AUTO_DRIVE_LOCK(6), reasonCode=AUTO_DRIVE_LOCK.
    """

    locked: bool
    lockCandidate: Optional[CandidateCommand]


@dataclass(frozen=True)
class ISOFIXLockResult:
    """!
    @brief IU-0015.evaluate()의 산출물(Phase3 신규, IF-0022).
    @invariant leftLockActive ⟺ leftLockCandidate is not None ⟺ leftReasonCode is not None
               (우측 대칭, 좌우 완전 독립 — SWR-018b, ApproachRiskResult와 동일한 불변조건 패턴).
    """

    leftLockActive: bool
    rightLockActive: bool
    leftLockCandidate: Optional[CandidateCommand]
    rightLockCandidate: Optional[CandidateCommand]
    leftReasonCode: Optional[str]
    rightReasonCode: Optional[str]


@dataclass(frozen=True)
class IgnitionOffReleaseResult:
    """!
    @brief IU-0016.evaluate()의 산출물(Phase3 신규, IF-0023).
    @invariant off=True ⟺ releaseCandidate is not None. releaseCandidate가 있으면 door=BOTH,
               command=RELEASE, priority=PRIORITY_IGNITION_OFF_RELEASE(4), reasonCode=
               IGNITION_OFF. off는 SystemState.OFF와 동일한 이름이나 별개 자료형이다(IU-0003이
               상태 값 자체를 소유, 2장 참조 — 응집도 분리 원칙).
    """

    off: bool
    releaseCandidate: Optional[CandidateCommand]


@dataclass(frozen=True)
class ArbitrationResult:
    """!
    @brief IU-0005.arbitrate()의 산출물.
    @invariant blocked=True ⇒ leftCommand==NO_CHANGE and rightCommand==NO_CHANGE
               (Phase2: leftReasonCode/rightReasonCode도 None).
    @invariant leftCommand==NO_CHANGE ⟺ leftReasonCode is None(우측 대칭, Phase2 신규).
    """

    leftCommand: ArbitrationCommand
    rightCommand: ArbitrationCommand
    blocked: bool
    blockReason: Optional[str] = None
    leftReasonCode: Optional[str] = None
    rightReasonCode: Optional[str] = None


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
