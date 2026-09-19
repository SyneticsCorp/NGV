"""!
@file st_helpers.py
@brief 시스템 테스트(SWE.6) 공용 헬퍼. ENG-SWE1-001(SW 요구사항 명세서)을 테스트 베이시스로
       삼는 블랙박스 시스템 테스트 케이스가 공통으로 쓰는 "실물 시스템 조립"만 제공한다.
       unittest discover 패턴("test_*.py")에 걸리지 않도록 파일명을 "st_"로 시작한다.

@par 관련 항목
- 테스트 베이시스: Deliverables/Engineering/SoftwareRequirementsAnalysis/ENG-SWE1-001
  (아키텍처/상세설계 문서가 아니다 — tests_integration/it_helpers.py와는 목적이 다르다)
- 진입점: InputValidationAdapter.handleCycle(rawCycleInput, nowS) — OEM-IF-001/OEM-IF-009
  원시 Vehicle 입력을 받아 CycleResult를 반환하는 시스템 경계. SWR-013(b)의 자극(형식/범위
  오류가 포함된 원시값)은 이 경계에서만 진짜로 관찰 가능하므로(정규화는 IU-0001이 수행),
  IU-0009.evaluateCycle() 단독 호출이 아니라 이 전체 체인을 시스템 진입점으로 사용한다
  (ENG-SWE6-001 Change History / 최종 보고서에 이 결정 근거를 기록함).
- mock을 쓰지 않는다 — 실제 협력 객체(ARC-0001~0008 실물)만 조립한다("Exercise the Real
  Thing" 원칙, tests_integration/it_helpers.py와 동일 관례).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.adapters.decision_logger_stub import DecisionLoggerStub
from ngv.adapters.input_validation_adapter import InputValidationAdapter
from ngv.adapters.notification_adapter import NotificationAdapter
from ngv.adapters.output_actuator_adapter import OutputActuatorAdapter
from ngv.app.safety_kernel_orchestrator import SafetyKernelOrchestrator
from ngv.core.approach_risk_evaluator import ApproachRiskEvaluator
from ngv.core.approach_risk_override_manager import ApproachRiskOverrideManager
from ngv.core.command_arbiter import CommandArbiter
from ngv.core.crash_monitor import CrashMonitor
from ngv.core.fire_overtemp_occupant_monitor import FireOvertempOccupantMonitor
from ngv.core.freshness_monitor import FreshnessMonitor
from ngv.core.output_hold_actuator import OutputHoldActuator
from ngv.core.state_manager import StateManager
from ngv.domain.types import LockCommand, RawCycleInput, SystemState


def buildRawInput(rawSourceTimestamp, rawIgnitionOn, rawSensorFault):
    """!
    @brief OEM-IF-001(source_timestamp_s)/OEM-IF-009(ignition_on, sensor_fault) 원시 입력을
           그대로 표현하는 RawCycleInput을 만든다(형식 검증 전 값 — Vehicle 실물 대신 시험벡터).
    """
    return RawCycleInput(
        rawSourceTimestamp=rawSourceTimestamp,
        rawIgnitionOn=rawIgnitionOn,
        rawSensorFault=rawSensorFault,
    )


def buildPhase2RawInput(rawSourceTimestamp, rawIgnitionOn, rawSensorFault, **phase2RawFields):
    """!
    @brief OEM-IF-002(crash_status)/OEM-IF-003(접근위험)/OEM-IF-007(화재/과온/탑승) Phase2
           원시 입력 6필드를 포함하는 RawCycleInput을 만든다(형식 검증 전 값). 지정하지 않은
           Phase2 필드는 RawCycleInput 기본값(None, MISSING으로 판정됨)을 그대로 사용한다
           (tests_integration/it_helpers.py::buildPhase2RawCycleInput과 동일 관례).

    @param phase2RawFields rawCrashStatus/rawLeftApproachRisk/rawRightApproachRisk/
           rawFireDetected/rawOvertemperatureDetected/rawAdultPresent 중 필요한 것만 kwargs로 전달
    """
    return RawCycleInput(
        rawSourceTimestamp=rawSourceTimestamp,
        rawIgnitionOn=rawIgnitionOn,
        rawSensorFault=rawSensorFault,
        **phase2RawFields,
    )


def buildSystemUnderTest():
    """!
    @brief 시스템 테스트 대상 — ARC-0001(입력 검증) + ARC-0002~0008(오케스트레이터 실물 조립)
           전체 체인. mock을 쓰지 않고 프로덕션 컴포넌트를 그대로 사용한다.

    @return InputValidationAdapter — handleCycle(rawCycleInput, nowS)로 자극을 주입하는 진입점
    """
    orchestrator = SafetyKernelOrchestrator(
        freshnessMonitor=FreshnessMonitor(),
        stateManager=StateManager(),
        outputHoldActuator=OutputHoldActuator(),
        commandArbiter=CommandArbiter(),
        outputAdapter=OutputActuatorAdapter(),
        notificationAdapter=NotificationAdapter(),
        decisionLogger=DecisionLoggerStub(),
        crashMonitor=CrashMonitor(),
        approachRiskEvaluator=ApproachRiskEvaluator(),
        overrideManager=ApproachRiskOverrideManager(),
        fireMonitor=FireOvertempOccupantMonitor(),
    )
    return InputValidationAdapter(orchestrator)


__all__ = [
    "LockCommand",
    "SystemState",
    "buildRawInput",
    "buildPhase2RawInput",
    "buildSystemUnderTest",
]
