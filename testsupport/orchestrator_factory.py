"""!
@file orchestrator_factory.py
@brief SafetyKernelOrchestrator(ARC-0009) 실물 조립 공용 팩토리.

tests/, tests_integration/, tests_system/ 세 테스트 루트가 각자 동일한 14개 협력 객체
(IU-0002~0004, IU-0006~0008, IU-0010~0016, IU-0005) 기본 생성 코드를 반복해서 pylint
duplicate-code(R0801, min-similarity-lines=8)를 위반했다 — 이 모듈이 그 유일한 출처다.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.adapters.decision_logger_stub import DecisionLoggerStub
from ngv.adapters.notification_adapter import NotificationAdapter
from ngv.adapters.output_actuator_adapter import OutputActuatorAdapter
from ngv.app.safety_kernel_orchestrator import SafetyKernelOrchestrator
from ngv.core.approach_risk_evaluator import ApproachRiskEvaluator
from ngv.core.approach_risk_override_manager import ApproachRiskOverrideManager
from ngv.core.command_arbiter import CommandArbiter
from ngv.core.crash_monitor import CrashMonitor
from ngv.core.fire_overtemp_occupant_monitor import FireOvertempOccupantMonitor
from ngv.core.freshness_monitor import FreshnessMonitor
from ngv.core.ignition_off_release_monitor import IgnitionOffReleaseMonitor
from ngv.core.isofix_forced_lock_monitor import IsofixForcedLockMonitor
from ngv.core.output_hold_actuator import OutputHoldActuator
from ngv.core.state_manager import StateManager
from ngv.core.vehicle_speed_auto_lock_monitor import VehicleSpeedAutoLockMonitor


def buildOrchestratorKwargs(**overrides):
    """!
    @brief SafetyKernelOrchestrator의 14개 협력 객체 기본값(전부 실물)을 kwargs 딕셔너리로
           반환한다. 특정 협력 객체만 테스트 더블/계측 래퍼로 바꾸고 싶으면 overrides로
           지정한다(나머지는 실물 그대로 유지).

    @param overrides 교체할 kwarg 이름=값 (예: freshnessMonitor=RaisingFreshnessMonitor())
    @return dict — SafetyKernelOrchestrator(**dict) 형태로 그대로 전달 가능
    """
    defaults = {
        "freshnessMonitor": FreshnessMonitor(),
        "stateManager": StateManager(),
        "outputHoldActuator": OutputHoldActuator(),
        "commandArbiter": CommandArbiter(),
        "outputAdapter": OutputActuatorAdapter(),
        "notificationAdapter": NotificationAdapter(),
        "decisionLogger": DecisionLoggerStub(),
        "crashMonitor": CrashMonitor(),
        "approachRiskEvaluator": ApproachRiskEvaluator(),
        "overrideManager": ApproachRiskOverrideManager(),
        "fireMonitor": FireOvertempOccupantMonitor(),
        "vehicleSpeedMonitor": VehicleSpeedAutoLockMonitor(),
        "isofixMonitor": IsofixForcedLockMonitor(),
        "ignitionOffReleaseMonitor": IgnitionOffReleaseMonitor(),
    }
    defaults.update(overrides)
    return defaults


def buildOrchestrator(**overrides):
    """!
    @brief 실물(real) 협력 객체로 구성된 SafetyKernelOrchestrator를 만든다(mock 미사용,
           "Exercise the Real Thing" 원칙).

    @param overrides buildOrchestratorKwargs()와 동일 — 특정 협력 객체만 교체 가능
    @return SafetyKernelOrchestrator 인스턴스
    """
    return SafetyKernelOrchestrator(**buildOrchestratorKwargs(**overrides))
