"""!
@file it_helpers.py
@brief 통합시험(SWE.5) 공용 헬퍼. ENG-SWE2-001 6장 인터페이스 데이터 계약(IF-NNNN)에 맞춰
       시험벡터를 만드는 함수만 모아둔다. unittest discover 패턴("test_*.py")에 걸리지 않도록
       파일명을 "it_"로 시작한다.

@par 관련 항목
- 테스트 베이시스: ENG-SWE2-001 6장(인터페이스 명세), 11장(통합 전략)
- mock 라이브러리를 쓰지 않는다 — tests/test_safety_kernel_orchestrator.py와 동일한 관례
  (실제 협력 객체 + 얇은 계측 래퍼만 사용, "Exercise the Real Thing" 원칙).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.adapters.decision_logger_stub import DecisionLoggerStub
from ngv.adapters.input_validation_adapter import InputValidationAdapter
from ngv.adapters.notification_adapter import NotificationAdapter
from ngv.adapters.output_actuator_adapter import OutputActuatorAdapter
from ngv.core.command_arbiter import CommandArbiter
from ngv.core.freshness_monitor import FreshnessMonitor
from ngv.core.output_hold_actuator import OutputHoldActuator
from ngv.core.state_manager import StateManager
from ngv.domain.types import (
    ArbitrationCommand,
    ArbitrationResult,
    CandidateCommand,
    CrashStatus,
    Door,
    FieldValidationResult,
    FreshnessResult,
    NormalizedSafetyInput,
    RawCycleInput,
    StateResult,
    SystemState,
)

from testsupport.orchestrator_factory import buildOrchestrator

## Phase2 전체 체인(IT-0087) 기대 호출 순서 — recordCalls 계측 대상 공통 상수(중복 코드 방지).
PHASE2_ORCHESTRATOR_CALL_ORDER = [
    "IF-0006",
    "IF-0007",
    "IF-0016",
    "IF-0017",
    "IF-0018",
    "IF-0019",
    "IF-0008",
    "IF-0009",
    "IF-0010",
    "IF-0011",
    "IF-0012",
]

## Phase3 전체 체인(IT-0136) 기대 호출 순서 — PHASE2_ORCHESTRATOR_CALL_ORDER에 IU-0016/0015/0014
## (IF-0023/0022/0021)가 fire monitor 이후·arbitrate 이전에 삽입된 형태(11장 통합 순서 근거).
PHASE3_ORCHESTRATOR_CALL_ORDER = (
    PHASE2_ORCHESTRATOR_CALL_ORDER[:6]
    + ["IF-0023", "IF-0022", "IF-0021"]
    + PHASE2_ORCHESTRATOR_CALL_ORDER[6:]
)


def validField(value):
    """!
    @brief 유효한 FieldValidationResult(IF-0005/IF-0006/IF-0007 등 데이터 계약)를 만든다.
    """
    return FieldValidationResult(value=value, valid=True, rawValue=value)


def invalidField(rawValue, errorReason="TYPE_ERROR", substituteValue=None):
    """!
    @brief 무효한 FieldValidationResult를 만든다. substituteValue를 주면 fail-safe 대체가
           적용된 상태(예: sensorFaultField)를 재현한다.
    """
    return FieldValidationResult(
        value=substituteValue, valid=False, rawValue=rawValue, errorReason=errorReason
    )


def buildNormalizedInput(timestampField, ignitionField, sensorFaultField):
    """!
    @brief IF-0005 데이터 계약(NormalizedSafetyInput)을 만든다.
    """
    return NormalizedSafetyInput(
        sourceTimestampField=timestampField,
        ignitionOnField=ignitionField,
        sensorFaultField=sensorFaultField,
    )


def buildFreshnessResult(stale, elapsedS, detectedAtS):
    """!
    @brief IF-0006 데이터 계약(FreshnessResult)을 합성한다(2단계에서 ARC-0002 실물 없이 주입).
    """
    return FreshnessResult(stale=stale, elapsedS=elapsedS, detectedAtS=detectedAtS)


def buildStateResult(state, changedToFault=False, warningReasonCode=None):
    """!
    @brief IF-0007 데이터 계약(StateResult)을 합성한다(3단계에서 ARC-0003 실물 없이 주입).
    """
    return StateResult(state=state, changedToFault=changedToFault, warningReasonCode=warningReasonCode)


def buildArbitrationResult(leftCommand, rightCommand, blocked=False, blockReason=None):
    """!
    @brief IF-0008 데이터 계약(ArbitrationResult)을 합성한다(3단계에서 ARC-0005 실물 없이 주입).
    """
    return ArbitrationResult(
        leftCommand=leftCommand, rightCommand=rightCommand, blocked=blocked, blockReason=blockReason
    )


def buildRawCycleInput(rawSourceTimestamp, rawIgnitionOn, rawSensorFault):
    """!
    @brief IF-0001/IF-0002 원시 외부 입력(RawCycleInput)을 만든다(Vehicle 실물 대신 시험벡터 주입).
    """
    return RawCycleInput(
        rawSourceTimestamp=rawSourceTimestamp, rawIgnitionOn=rawIgnitionOn, rawSensorFault=rawSensorFault
    )


def buildPhase2RawCycleInput(rawSourceTimestamp, rawIgnitionOn, rawSensorFault, **phase2RawFields):
    """!
    @brief IF-0001/IF-0002/IF-0013/IF-0014/IF-0015 원시 외부 입력(RawCycleInput, Phase2 6필드
           포함)을 만든다(11장 13단계). 지정하지 않은 Phase2 필드는 RawCycleInput 기본값(None,
           MISSING으로 판정됨)을 그대로 사용한다.

    @param phase2RawFields rawCrashStatus/rawLeftApproachRisk/rawRightApproachRisk/
           rawFireDetected/rawOvertemperatureDetected/rawAdultPresent 중 필요한 것만 kwargs로 전달
    """
    return RawCycleInput(
        rawSourceTimestamp=rawSourceTimestamp,
        rawIgnitionOn=rawIgnitionOn,
        rawSensorFault=rawSensorFault,
        **phase2RawFields,
    )


def buildPhase2NormalizedInput(timestampField, ignitionField, sensorFaultField, **phase2Fields):
    """!
    @brief IF-0005 데이터 계약(NormalizedSafetyInput, Phase2 6필드 포함)을 만든다(11장 8~12단계).
           지정하지 않은 Phase2 필드는 default_factory(MISSING, valid=False)를 그대로 사용한다.

    @param phase2Fields crashStatusField/leftApproachRiskField/rightApproachRiskField/fireField/
           overtempField/adultField 중 필요한 것만 kwargs로 전달
    """
    return NormalizedSafetyInput(
        sourceTimestampField=timestampField,
        ignitionOnField=ignitionField,
        sensorFaultField=sensorFaultField,
        **phase2Fields,
    )


def buildPhase3RawCycleInput(rawSourceTimestamp, rawIgnitionOn, rawSensorFault, **phase3RawFields):
    """!
    @brief IF-0001(vehicle_speed_kph 잔여필드)/IF-0002/IF-0020(isofix_left/right) 원시 외부
           입력(RawCycleInput)을 만든다(11장 15~21단계). buildPhase2RawCycleInput()과 구현이
           동일하다 — RawCycleInput이 이미 Phase3 필드를 갖고 있어 위임만 하면 되지만(dataclass
           1개 정의, 재번호 금지 원칙과 동일하게 재정의하지 않음), Phase3 시험 파일의 가독성을
           위해 이름을 별도로 둔다(중복 코드 아님 — 위임 1줄).

    @param phase3RawFields rawVehicleSpeedKph/rawIsofixLeft/rawIsofixRight 등 필요한 것만
           kwargs로 전달(Phase1/2 필드도 함께 전달 가능)
    """
    return buildPhase2RawCycleInput(rawSourceTimestamp, rawIgnitionOn, rawSensorFault, **phase3RawFields)


def buildPhase2RegressionFieldsKwargs():
    """!
    @brief IT-0081(step13)/IT-0130(step20)이 공유하는 Phase2 6필드 회귀 시험벡터를 만든다
           (동일한 값을 두 시험 파일에 직접 나열하면 중복 코드가 되므로 이 헬퍼로 대체한다).
    """
    return dict(
        rawCrashStatus="PENDING",
        rawLeftApproachRisk=True,
        rawRightApproachRisk=False,
        rawFireDetected=False,
        rawOvertemperatureDetected=True,
        rawAdultPresent=False,
    )


def buildPhase3NormalizedInput(timestampField, ignitionField, sensorFaultField, **phase3Fields):
    """!
    @brief IF-0005 데이터 계약(NormalizedSafetyInput, Phase3 필드 포함)을 만든다(11장 15~19단계).
           buildPhase2NormalizedInput()에 위임한다(위 함수와 동일한 재사용 근거).

    @param phase3Fields vehicleSpeedField/isofixLeftField/isofixRightField 등 필요한 것만
           kwargs로 전달(Phase1/2 필드도 함께 전달 가능)
    """
    return buildPhase2NormalizedInput(timestampField, ignitionField, sensorFaultField, **phase3Fields)


def buildCandidateCommand(door, command, priority, reasonCode="TEST_REASON"):
    """!
    @brief IF-0016~IF-0019가 공통으로 산출하는 CandidateCommand(IF-0008 입력)를 합성한다
           (12단계에서 8~11단계 실물 없이 결과를 모사할 때 사용).
    """
    return CandidateCommand(door=door, command=command, priority=priority, reasonCode=reasonCode)


def buildRealOrchestrator():
    """!
    @brief 6단계 통합 대상 — ARC-0002~0008 실물로 구성한 오케스트레이터(mock 미사용).
    """
    return buildOrchestrator()


def buildRecordedBaseCollaboratorsKwargs(callLog):
    """!
    @brief IF-0006~IF-0012 기본 7개 협력 객체를 recordCalls로 감싸 kwargs로 반환한다
           (여러 통합시험 파일이 공통으로 쓰는 고정 태그 — 중복 코드 제거).
    """
    return {
        "freshnessMonitor": recordCalls(FreshnessMonitor(), "evaluate", "IF-0006", callLog),
        "stateManager": recordCalls(StateManager(), "evaluate", "IF-0007", callLog),
        "outputHoldActuator": recordCalls(OutputHoldActuator(), "confirm", "IF-0009", callLog),
        "commandArbiter": recordCalls(CommandArbiter(), "arbitrate", "IF-0008", callLog),
        "outputAdapter": recordCalls(OutputActuatorAdapter(), "publish", "IF-0010", callLog),
        "notificationAdapter": recordCalls(NotificationAdapter(), "publishWarning", "IF-0011", callLog),
        "decisionLogger": recordCalls(DecisionLoggerStub(), "log", "IF-0012", callLog),
    }


def buildRealAdapterWithOrchestrator():
    """!
    @brief 7단계 통합 대상 — ARC-0001 실물 + 6단계 실물 오케스트레이터 전체 체인.
    """
    orchestrator = buildRealOrchestrator()
    adapter = InputValidationAdapter(orchestrator)
    return adapter, orchestrator


def recordCalls(instance, methodName, tag, callLog):
    """!
    @brief 실제 인스턴스의 메서드를 감싸 호출 순서/인자만 관찰하고 원본 로직에 그대로 위임한다.
           mock을 쓰지 않고 실제 프로덕션 객체를 그대로 실행시키는 최소 계측(instrumentation)이다.
    """
    original = getattr(instance, methodName)

    def wrapped(*args, **kwargs):
        callLog.append(tag)
        return original(*args, **kwargs)

    setattr(instance, methodName, wrapped)
    return instance


def captureReturn(instance, methodName, sink):
    """!
    @brief 실제 인스턴스 메서드의 반환값을 sink 리스트에 적재하는 캡처 싱크로 감싼다.
           (11장 5단계 "외부측은 캡처용 인메모리 싱크로 대체"에 대응 — publish 반환값 관찰용).
    """
    original = getattr(instance, methodName)

    def wrapped(*args, **kwargs):
        result = original(*args, **kwargs)
        sink.append(result)
        return result

    setattr(instance, methodName, wrapped)
    return instance


class RaisingFreshnessMonitor(FreshnessMonitor):
    """!
    @brief 오류 주입 전용 — IF-0006.evaluate() 호출 시 항상 예외(ASIL B 핵심 경로 결함 시뮬레이션).
    """

    def evaluate(self, sourceTimestampField, nowS):
        raise RuntimeError("IF-0006 fault injection: freshness monitor failure")


class RaisingOutputActuatorAdapter(OutputActuatorAdapter):
    """!
    @brief 오류 주입 전용 — IF-0010.publish() 호출 시 항상 예외(QM 어댑터 격리 시나리오).
    """

    def publish(self, confirmedOutput):
        raise RuntimeError("IF-0010 fault injection: publish failure")


class RaisingNotificationAdapter(NotificationAdapter):
    """!
    @brief 오류 주입 전용 — IF-0011.publishWarning() 호출 시 항상 예외(QM 어댑터 격리 시나리오).
    """

    def publishWarning(self, stateResult):
        raise RuntimeError("IF-0011 fault injection: publishWarning failure")


class RaisingDecisionLogger(DecisionLoggerStub):
    """!
    @brief 오류 주입 전용 — IF-0012.log() 호출 시 항상 예외(QM 어댑터 격리 시나리오).
    """

    def log(self, entry):
        raise RuntimeError("IF-0012 fault injection: log failure")


__all__ = [
    "ArbitrationCommand",
    "SystemState",
    "CrashStatus",
    "Door",
    "CandidateCommand",
    "validField",
    "invalidField",
    "buildNormalizedInput",
    "buildFreshnessResult",
    "buildStateResult",
    "buildArbitrationResult",
    "buildRawCycleInput",
    "buildPhase2RawCycleInput",
    "buildPhase2NormalizedInput",
    "buildPhase3RawCycleInput",
    "buildPhase3NormalizedInput",
    "buildCandidateCommand",
    "buildRealOrchestrator",
    "buildRealAdapterWithOrchestrator",
    "recordCalls",
    "captureReturn",
    "RaisingFreshnessMonitor",
    "RaisingOutputActuatorAdapter",
    "RaisingNotificationAdapter",
    "RaisingDecisionLogger",
]
