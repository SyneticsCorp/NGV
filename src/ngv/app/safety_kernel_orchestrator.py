"""!
@file safety_kernel_orchestrator.py
@brief IU-0009(ARC-0009 안전 커널 평가 오케스트레이터) — 평가주기 조율.

고정 순서(ENG-SWE3-001 3장)로 IU-0002~0008을 호출한다: 2-1 freshness -> 2-2 state
-> 2-3 arbitrate -> 2-4 confirm -> 2-5 publish -> 2-6 publishWarning -> 2-7 log.
2-1~2-4단계(판정 핵심 경로) 예외는 FAULT를 강제하고, 2-5~2-7단계(QM 어댑터) 예외는
개별 격리한다(10.2절). 예외를 외부로 전파하지 않는다.

@par 관련 항목
- 요구사항: SWR-013, SWR-021(조율)
- 상세설계: ENG-SWE3-001 5장/6.6절/10.2절
"""

from ngv.domain.constants import WARNING_CODE_ORCHESTRATION_ERROR
from ngv.domain.types import (
    ArbitrationCommand,
    ArbitrationResult,
    CycleResult,
    DecisionLogEntry,
    StateResult,
    SystemState,
)


class SafetyKernelOrchestrator:
    """!
    @brief IU-0002~0008을 고정 순서로 조율하고, 판정 핵심 경로 실패 시 fail-freeze를 강제한다.
    """

    def __init__(
        self,
        freshnessMonitor,
        stateManager,
        outputHoldActuator,
        commandArbiter,
        outputAdapter,
        notificationAdapter,
        decisionLogger,
    ):
        """!
        @brief 협력 객체(IU-0002~0008)를 주입받아 보관한다.

        @param freshnessMonitor IU-0002 인스턴스
        @param stateManager IU-0003 인스턴스
        @param outputHoldActuator IU-0004 인스턴스
        @param commandArbiter IU-0005 인스턴스
        @param outputAdapter IU-0006 인스턴스
        @param notificationAdapter IU-0007 인스턴스
        @param decisionLogger IU-0008 인스턴스
        """
        self.freshnessMonitor = freshnessMonitor
        self.stateManager = stateManager
        self.outputHoldActuator = outputHoldActuator
        self.commandArbiter = commandArbiter
        self.outputAdapter = outputAdapter
        self.notificationAdapter = notificationAdapter
        self.decisionLogger = decisionLogger
        self.cycleCount = 0

    def evaluateCycle(self, normalizedInput, nowS):
        """!
        @brief 한 평가주기를 조율한다.

        @param normalizedInput NormalizedSafetyInput — IU-0001.normalizeCycle()이 생성한 검증 완료 입력
        @param nowS float — 단조 증가 현재 평가주기 시각(초)
        @return CycleResult{confirmedOutput, stateResult, errorOccurred}
        @exception 없음 — 외부로 전파하지 않는다(방어적 최상위 경계)
        """
        self.cycleCount += 1
        stateResult, confirmedOutput, arbitrationResult, errorOccurred = self.runCoreStages(
            normalizedInput, nowS
        )
        self.runPublishStages(confirmedOutput, stateResult, arbitrationResult, nowS)
        return CycleResult(
            confirmedOutput=confirmedOutput, stateResult=stateResult, errorOccurred=errorOccurred
        )

    def runCoreStages(self, normalizedInput, nowS):
        """!
        @brief 2-1~2-4단계(freshness/state/arbitrate/confirm)를 실행하고, 예외 시 FAULT를 강제한다.

        @param normalizedInput NormalizedSafetyInput
        @param nowS float
        @return tuple(StateResult, ConfirmedOutput, ArbitrationResult, bool errorOccurred)
        """
        try:
            freshnessResult = self.freshnessMonitor.evaluate(normalizedInput.sourceTimestampField, nowS)
            stateResult = self.stateManager.evaluate(freshnessResult, normalizedInput.sensorFaultField, nowS)
            inputValid = self.composeInputValid(normalizedInput)
            arbitrationResult = self.commandArbiter.arbitrate(stateResult, inputValid, [])
            confirmedOutput = self.outputHoldActuator.confirm(arbitrationResult, stateResult)
            return stateResult, confirmedOutput, arbitrationResult, False
        except Exception:  # pylint: disable=broad-exception-caught
            return self.forceFault()

    def forceFault(self):
        """!
        @brief 판정 핵심 경로 예외 시 FAULT를 강제 구성하고 fail-freeze를 적용한다(10.2절).

        @return tuple(StateResult, ConfirmedOutput, ArbitrationResult, bool errorOccurred=True)
        """
        forcedState = StateResult(
            state=SystemState.FAULT, changedToFault=True, warningReasonCode=WARNING_CODE_ORCHESTRATION_ERROR
        )
        forcedArbitration = ArbitrationResult(
            leftCommand=ArbitrationCommand.NO_CHANGE,
            rightCommand=ArbitrationCommand.NO_CHANGE,
            blocked=True,
            blockReason=WARNING_CODE_ORCHESTRATION_ERROR,
        )
        confirmedOutput = self.outputHoldActuator.confirm(forcedArbitration, forcedState)
        return forcedState, confirmedOutput, forcedArbitration, True

    def runPublishStages(self, confirmedOutput, stateResult, arbitrationResult, nowS):
        """!
        @brief 2-5~2-7단계(publish/publishWarning/log)를 개별 격리해 실행한다(10.2절).

        @param confirmedOutput ConfirmedOutput
        @param stateResult StateResult
        @param arbitrationResult ArbitrationResult — DecisionLogEntry의 blocked/blockReason 출처
        @param nowS float
        @return None
        """
        logEntry = DecisionLogEntry(
            cycleId=self.cycleCount,
            nowS=nowS,
            state=stateResult.state,
            confirmedOutput=confirmedOutput,
            blocked=arbitrationResult.blocked,
            blockReason=arbitrationResult.blockReason,
        )
        for stage in (
            lambda: self.outputAdapter.publish(confirmedOutput),
            lambda: self.notificationAdapter.publishWarning(stateResult),
            lambda: self.decisionLogger.log(logEntry),
        ):
            try:
                stage()
            except Exception:  # pylint: disable=broad-exception-caught
                continue

    @staticmethod
    def composeInputValid(normalizedInput):
        """!
        @brief 7장 결정표 D에 따라 Command Arbiter 게이트용 inputValid를 합성한다.

        sensorFaultField.valid는 의도적으로 제외한다(ENG-SWE3-001 7장 결정표 D 근거 —
        sensor_fault 자체 INVALID는 이미 fail-safe 대체를 거쳐 state==FAULT로 차단되므로 중복 판정 방지).

        @param normalizedInput NormalizedSafetyInput
        @return bool — sourceTimestampField.valid and ignitionOnField.valid
        """
        return normalizedInput.sourceTimestampField.valid and normalizedInput.ignitionOnField.valid

    def reset(self):
        """!
        @brief IU-0002/0003/0004의 reset()을 각각 1회 호출해 시스템을 부팅 기본값으로 복귀시킨다.
        @return None
        """
        self.freshnessMonitor.reset()
        self.stateManager.reset()
        self.outputHoldActuator.reset()
