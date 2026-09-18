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
from ngv.app.safety_kernel_orchestrator import SafetyKernelOrchestrator
from ngv.core.command_arbiter import CommandArbiter
from ngv.core.freshness_monitor import FreshnessMonitor
from ngv.core.output_hold_actuator import OutputHoldActuator
from ngv.core.state_manager import StateManager
from ngv.domain.types import (
    ArbitrationCommand,
    ArbitrationResult,
    FieldValidationResult,
    FreshnessResult,
    NormalizedSafetyInput,
    RawCycleInput,
    StateResult,
    SystemState,
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


def buildRealOrchestrator():
    """!
    @brief 6단계 통합 대상 — ARC-0002~0008 실물로 구성한 오케스트레이터(mock 미사용).
    """
    return SafetyKernelOrchestrator(
        freshnessMonitor=FreshnessMonitor(),
        stateManager=StateManager(),
        outputHoldActuator=OutputHoldActuator(),
        commandArbiter=CommandArbiter(),
        outputAdapter=OutputActuatorAdapter(),
        notificationAdapter=NotificationAdapter(),
        decisionLogger=DecisionLoggerStub(),
    )


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
    "validField",
    "invalidField",
    "buildNormalizedInput",
    "buildFreshnessResult",
    "buildStateResult",
    "buildArbitrationResult",
    "buildRawCycleInput",
    "buildRealOrchestrator",
    "buildRealAdapterWithOrchestrator",
    "recordCalls",
    "captureReturn",
    "RaisingFreshnessMonitor",
    "RaisingOutputActuatorAdapter",
    "RaisingNotificationAdapter",
    "RaisingDecisionLogger",
]
