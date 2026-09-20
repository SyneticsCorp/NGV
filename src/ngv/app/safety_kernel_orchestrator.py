"""!
@file safety_kernel_orchestrator.py
@brief IU-0009(ARC-0009 안전 커널 평가 오케스트레이터) — 평가주기 조율(Phase3 갱신).

고정 순서(ENG-SWE3-001 3.1절, Phase3 확장)로 IU-0002~0016을 호출한다: 2-1 freshness ->
2-2 state(ignitionOnField 전달) -> 2-3 crash(IU-0010) -> 2-4 approachRisk(IU-0011) ->
2-5 override(IU-0012) -> 2-6 fire(IU-0013) -> 2-7 ignitionOff(IU-0016) -> 2-8 isofix(IU-0015)
-> 2-9 vehicleSpeed(IU-0014) -> (candidateCommands 조립) -> 2-10 arbitrate -> 2-11 confirm ->
2-12 publish -> 2-13 publishWarning -> 2-14 log. 2-1~2-11단계(판정 핵심 경로, Phase3에서
IU-0014~0016 포함하도록 재확장) 예외는 FAULT를 강제하고, 2-12~2-14단계(QM 어댑터) 예외는
개별 격리한다(10.5절/10.10절). 예외를 외부로 전파하지 않는다.

@par 관련 항목
- 요구사항: SWR-013, SWR-021, SWR-005~009, SWR-017, SWR-003, SWR-018, SWR-020(조율)
- 상세설계: ENG-SWE3-001 5.3절/5.3b절/6.7절/6.17절/10.5절/10.10절
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
        crashMonitor,
        approachRiskEvaluator,
        overrideManager,
        fireMonitor,
        vehicleSpeedMonitor,
        isofixMonitor,
        ignitionOffReleaseMonitor,
    ):
        """!
        @brief 협력 객체(IU-0002~0016)를 주입받아 보관한다(Phase3: IU-0014~0016 신규).

        @param freshnessMonitor IU-0002 인스턴스
        @param stateManager IU-0003 인스턴스
        @param outputHoldActuator IU-0004 인스턴스
        @param commandArbiter IU-0005 인스턴스
        @param outputAdapter IU-0006 인스턴스
        @param notificationAdapter IU-0007 인스턴스
        @param decisionLogger IU-0008 인스턴스
        @param crashMonitor IU-0010 인스턴스
        @param approachRiskEvaluator IU-0011 인스턴스
        @param overrideManager IU-0012 인스턴스
        @param fireMonitor IU-0013 인스턴스
        @param vehicleSpeedMonitor IU-0014 인스턴스
        @param isofixMonitor IU-0015 인스턴스
        @param ignitionOffReleaseMonitor IU-0016 인스턴스
        """
        self.freshnessMonitor = freshnessMonitor
        self.stateManager = stateManager
        self.outputHoldActuator = outputHoldActuator
        self.commandArbiter = commandArbiter
        self.outputAdapter = outputAdapter
        self.notificationAdapter = notificationAdapter
        self.decisionLogger = decisionLogger
        self.crashMonitor = crashMonitor
        self.approachRiskEvaluator = approachRiskEvaluator
        self.overrideManager = overrideManager
        self.fireMonitor = fireMonitor
        self.vehicleSpeedMonitor = vehicleSpeedMonitor
        self.isofixMonitor = isofixMonitor
        self.ignitionOffReleaseMonitor = ignitionOffReleaseMonitor
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
        @brief 2-1~2-11단계(freshness~confirm, Phase3에서 IU-0014~0016 포함하도록 재확장)를
               실행하고, 예외 시 FAULT를 강제한다.

        @param normalizedInput NormalizedSafetyInput(12필드로 확장)
        @param nowS float
        @return tuple(StateResult, ConfirmedOutput, ArbitrationResult, bool errorOccurred)
        """
        try:
            freshnessResult = self.freshnessMonitor.evaluate(normalizedInput.sourceTimestampField, nowS)
            stateResult = self.stateManager.evaluate(
                freshnessResult, normalizedInput.sensorFaultField, normalizedInput.ignitionOnField, nowS
            )
            candidateCommands = self.evaluatePhase3Candidates(normalizedInput, nowS)
            inputValid = self.composeInputValid(normalizedInput)
            arbitrationResult = self.commandArbiter.arbitrate(stateResult, inputValid, candidateCommands)
            confirmedOutput = self.outputHoldActuator.confirm(arbitrationResult, stateResult)
            return stateResult, confirmedOutput, arbitrationResult, False
        except Exception:  # pylint: disable=broad-exception-caught
            return self.forceFault()

    def evaluatePhase3Candidates(self, normalizedInput, nowS):
        """!
        @brief 2-3~2-9단계(IU-0010~0013, IU-0016, IU-0015, IU-0014)를 호출하고
               candidateCommands를 조립한다(6.7절/6.17절, Phase2 evaluatePhase2Candidates()를
               개명·확장 — Phase2 로직은 그대로 보존).

        @param normalizedInput NormalizedSafetyInput
        @param nowS float
        @return list[CandidateCommand] — assembleCandidateCommands()의 반환값
        """
        crashResult = self.crashMonitor.evaluate(normalizedInput.crashStatusField, nowS)
        approachResult = self.approachRiskEvaluator.evaluate(
            normalizedInput.leftApproachRiskField, normalizedInput.rightApproachRiskField
        )
        leftReleaseReRequested, rightReleaseReRequested = self.composeReleaseReRequested()
        overrideDecision = self.overrideManager.decide(
            approachResult.leftRiskActive,
            approachResult.rightRiskActive,
            leftReleaseReRequested,
            rightReleaseReRequested,
            nowS,
        )
        forcedReleaseResult = self.fireMonitor.evaluate(
            normalizedInput.fireField, normalizedInput.overtempField, normalizedInput.adultField
        )
        ignitionOffResult = self.ignitionOffReleaseMonitor.evaluate(normalizedInput.ignitionOnField, nowS)
        isofixResult = self.isofixMonitor.evaluate(
            normalizedInput.isofixLeftField, normalizedInput.isofixRightField
        )
        vehicleSpeedResult = self.vehicleSpeedMonitor.evaluate(normalizedInput.vehicleSpeedField, nowS)
        return self.assembleCandidateCommands(
            crashResult,
            approachResult,
            overrideDecision,
            forcedReleaseResult,
            ignitionOffResult,
            isofixResult,
            vehicleSpeedResult,
        )

    @staticmethod
    def assembleCandidateCommands(
        crashResult,
        approachResult,
        overrideDecision,
        forcedReleaseResult,
        ignitionOffResult,
        isofixResult,
        vehicleSpeedResult,
    ):
        """!
        @brief 이미 계산된 7개 컴포넌트 결과를 리스트 멤버십으로만 결합한다(판정 로직 없음,
               결정표 J/6.17절 확장). Phase3 3건(ignitionOff/isofix 좌우/vehicleSpeed)은
               override 같은 철회 조건 없이 그대로 포함된다.

        @param crashResult CrashEvaluationResult
        @param approachResult ApproachRiskResult
        @param overrideDecision OverrideDecision
        @param forcedReleaseResult ForcedReleaseResult
        @param ignitionOffResult IgnitionOffReleaseResult(Phase3 신규)
        @param isofixResult ISOFIXLockResult(Phase3 신규)
        @param vehicleSpeedResult VehicleSpeedLockResult(Phase3 신규)
        @return list[CandidateCommand] — 우선순위 순서는 무의미(IU-0005가 priority로 선택)
        """
        candidates = SafetyKernelOrchestrator.assemblePhase2Candidates(
            crashResult, approachResult, overrideDecision, forcedReleaseResult
        )
        candidates.extend(
            SafetyKernelOrchestrator.assemblePhase3Candidates(ignitionOffResult, isofixResult, vehicleSpeedResult)
        )
        return candidates

    @staticmethod
    def assemblePhase2Candidates(crashResult, approachResult, overrideDecision, forcedReleaseResult):
        """!
        @brief Phase2 4개 소스(충돌/좌접근위험/우접근위험/화재 등)를 결정표 J대로 조립한다
               (assembleCandidateCommands()의 순환복잡도를 낮추기 위한 분리, 11.1절 근거).

        @param crashResult CrashEvaluationResult
        @param approachResult ApproachRiskResult
        @param overrideDecision OverrideDecision
        @param forcedReleaseResult ForcedReleaseResult
        @return list[CandidateCommand]
        """
        candidates = []
        if crashResult.releaseCandidate is not None:
            candidates.append(crashResult.releaseCandidate)
        if approachResult.leftSuppressCandidate is not None and not overrideDecision.leftOverrideActive:
            candidates.append(approachResult.leftSuppressCandidate)
        if approachResult.rightSuppressCandidate is not None and not overrideDecision.rightOverrideActive:
            candidates.append(approachResult.rightSuppressCandidate)
        if forcedReleaseResult.releaseCandidate is not None:
            candidates.append(forcedReleaseResult.releaseCandidate)
        return candidates

    @staticmethod
    def assemblePhase3Candidates(ignitionOffResult, isofixResult, vehicleSpeedResult):
        """!
        @brief Phase3 4개 소스(ignition-off/좌ISOFIX/우ISOFIX/자동주행잠금)를 결정표 J
               확장(6.17절)대로 조립한다(철회 조건 없음 — 있으면 항상 포함).

        @param ignitionOffResult IgnitionOffReleaseResult
        @param isofixResult ISOFIXLockResult
        @param vehicleSpeedResult VehicleSpeedLockResult
        @return list[CandidateCommand]
        """
        candidates = []
        if ignitionOffResult.releaseCandidate is not None:
            candidates.append(ignitionOffResult.releaseCandidate)
        if isofixResult.leftLockCandidate is not None:
            candidates.append(isofixResult.leftLockCandidate)
        if isofixResult.rightLockCandidate is not None:
            candidates.append(isofixResult.rightLockCandidate)
        if vehicleSpeedResult.lockCandidate is not None:
            candidates.append(vehicleSpeedResult.lockCandidate)
        return candidates

    @staticmethod
    def composeReleaseReRequested():
        """!
        @brief releaseReRequested 채널을 합성한다(OEM-FR-001 미분석 placeholder, ledger 갭 7).

        @return tuple(bool, bool) — 항상 (False, False)
        """
        return False, False

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
        @brief IU-0002/0003/0004/0012의 reset()을 각각 1회 호출해 시스템을 부팅 기본값으로
               복귀시킨다(Phase2: IU-0012 억제 타이머 초기화 추가). IU-0010/0011/0013은 내부
               상태가 없어 reset()을 정의하지 않는다(5.3절).
        @return None
        """
        self.freshnessMonitor.reset()
        self.stateManager.reset()
        self.outputHoldActuator.reset()
        self.overrideManager.reset()
