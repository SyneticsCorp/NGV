"""!
@file test_it_step18_command_arbiter_phase3_priority_chain.py
@brief 통합 18단계 — ARC-0005(Command Arbiter, 우선순위 체인 확장 — 4=ignition-off해제,
       5=ISOFIX강제잠금, 6=자동주행잠금), IF-0008 인터페이스 계약 검증(Phase3 갱신).

테스트 베이시스: ENG-SWE2-001 6.1절(IF-0008), 9장("Phase 3 우선순위 체인 확정"/"해소되지 않고
유지되는 갭"), 11장 순서표 18행("단위시험 하네스, 15~17단계 결과를 모사한 candidateCommands
합성 주입 — LOCK계열/RELEASE계열 상충 시나리오 포함"). 15~17단계 실물은 불필요(파라미터로 합성
입력). 회귀 범위: 1~4, 8~12단계(Phase1/2 게이트·우선순위 규칙) — 신규 우선순위 추가가 기존
규칙을 깨지 않는지 확인(코드 변경 없음, OCP 재확인).
"""

import unittest

from tests_integration.it_helpers import (
    ArbitrationCommand,
    Door,
    SystemState,
    buildCandidateCommand,
    buildStateResult,
)
from ngv.core.command_arbiter import CommandArbiter


class TestIT0109IgnitionOffPriorityWinsOverIsofixOnLeftDoor(unittest.TestCase):
    """IT-0109 — Trace: IF-0008/IF-0022/IF-0023 / SWR-018, SWR-020, 9장 "Phase 3 우선순위 체인 확정", 7장 시나리오 11"""

    def testIgnitionOffReleaseOverridesIsofixLockOnLeftDoor(self):
        """!
        @brief ignition-off 해제(priority=4, BOTH, RELEASE)와 ISOFIX 강제잠금(priority=5, LEFT,
               LOCK)이 동시에 존재하면 LEFT/RIGHT 모두 RELEASE가 선택되어야 한다(9장 근거 —
               entrapment 방지 취지상 ignition-off가 LOCK 계열보다 우선, 7장 시나리오 11 재현).
        @technique 결정테이블 테스트(Decision Table Testing) — 우선순위 충돌(4 vs 5)
        @case Positive
        @breaks LOCK 계열(ISOFIX)이 잘못 선택되거나 RIGHT가 영향받지 않는 회귀
        """
        arbiter = CommandArbiter()
        candidates = [
            buildCandidateCommand(Door.BOTH, ArbitrationCommand.RELEASE, 4, "IGNITION_OFF"),
            buildCandidateCommand(Door.LEFT, ArbitrationCommand.LOCK, 5, "ISOFIX_FORCED_LOCK_LEFT"),
        ]

        result = arbiter.arbitrate(buildStateResult(SystemState.OFF), True, candidates)

        self.assertFalse(result.blocked)
        self.assertEqual(result.leftCommand, ArbitrationCommand.RELEASE)
        self.assertEqual(result.rightCommand, ArbitrationCommand.RELEASE)
        self.assertEqual(result.leftReasonCode, "IGNITION_OFF")
        self.assertEqual(result.rightReasonCode, "IGNITION_OFF")


class TestIT0110IgnitionOffPriorityWinsOverAutoDriveLock(unittest.TestCase):
    """IT-0110 — Trace: IF-0008/IF-0021/IF-0023 / SWR-003, SWR-020, 9장 근거"""

    def testIgnitionOffReleaseOverridesAutoDriveLockOnBothDoors(self):
        """!
        @brief ignition-off 해제(priority=4, RELEASE)와 자동주행잠금(priority=6, LOCK)이 동시에
               존재하면 양쪽 모두 RELEASE가 선택되어야 한다(9장 근거, priority 격차 2단계).
        @technique 결정테이블 테스트(Decision Table Testing) — 우선순위 충돌(4 vs 6)
        @case Positive
        @breaks LOCK 계열(자동주행잠금)이 잘못 선택되는 회귀
        """
        arbiter = CommandArbiter()
        candidates = [
            buildCandidateCommand(Door.BOTH, ArbitrationCommand.RELEASE, 4, "IGNITION_OFF"),
            buildCandidateCommand(Door.BOTH, ArbitrationCommand.LOCK, 6, "AUTO_DRIVE_LOCK"),
        ]

        result = arbiter.arbitrate(buildStateResult(SystemState.OFF), True, candidates)

        self.assertEqual(result.leftCommand, ArbitrationCommand.RELEASE)
        self.assertEqual(result.rightCommand, ArbitrationCommand.RELEASE)
        self.assertEqual(result.leftReasonCode, "IGNITION_OFF")


class TestIT0111IsofixPriorityWinsOverAutoDriveLockOnSameDoor(unittest.TestCase):
    """IT-0111 — Trace: IF-0008/IF-0021/IF-0022 / SWR-003, SWR-018, 9장 "SWR-018과 SWR-003 사이의 상대 순서" """

    def testIsofixReasonCodeIsSelectedOverAutoDriveLockOnLeftDoor(self):
        """!
        @brief ISOFIX 강제잠금(priority=5, LEFT, LOCK)과 자동주행잠금(priority=6, BOTH, LOCK)이
               동시에 존재하면 두 후보 모두 LOCK을 요구하지만 우선순위가 더 높은(숫자가 작은)
               ISOFIX의 이유코드가 선택되어야 한다(9장 근거 — 실제 출력에는 무관하나 이유코드
               보고 순위에는 영향).
        @technique 결정테이블 테스트(Decision Table Testing) — 우선순위 충돌(5 vs 6, 동일 명령)
        @case Positive
        @breaks 더 낮은 우선순위(자동주행잠금)의 이유코드가 잘못 선택되는 회귀
        """
        arbiter = CommandArbiter()
        candidates = [
            buildCandidateCommand(Door.LEFT, ArbitrationCommand.LOCK, 5, "ISOFIX_FORCED_LOCK_LEFT"),
            buildCandidateCommand(Door.BOTH, ArbitrationCommand.LOCK, 6, "AUTO_DRIVE_LOCK"),
        ]

        result = arbiter.arbitrate(buildStateResult(SystemState.NORMAL), True, candidates)

        self.assertEqual(result.leftCommand, ArbitrationCommand.LOCK)
        self.assertEqual(result.leftReasonCode, "ISOFIX_FORCED_LOCK_LEFT")
        self.assertEqual(result.rightCommand, ArbitrationCommand.LOCK)
        self.assertEqual(result.rightReasonCode, "AUTO_DRIVE_LOCK")


class TestIT0112ApproachRiskPriorityWinsOverIgnitionOffCurrentBehavior(unittest.TestCase):
    """IT-0112 — Trace: IF-0008/IF-0017/IF-0023 / 누적 갭 16(해소되지 않음, 현재 동작 문서화)"""

    def testApproachRiskSuppressionCurrentlyOverridesIgnitionOffOnLeftDoor(self):
        """!
        @brief 접근위험 억제(priority=2, ASIL B, LEFT, LOCK)와 ignition-off 해제(priority=4,
               QM, BOTH, RELEASE)가 동일 도어에서 상충하면, 현재 구현은 접근위험이 승리한다
               (ASIL B 안전 메커니즘 우선 보존이라는 잠정 기본값, ENG-SWE2-001 9장). 이 관계는
               OEM-A 확인 없이 최종 확정된 것이 아니므로(누적 갭 16), 이 시험은 "현재 동작
               문서화" 성격이며 이 우선순위 관계 자체가 올바르다고 주장하지 않는다.
        @technique 결정테이블 테스트(Decision Table Testing) — 우선순위 충돌(2 vs 4), 갭 문서화
        @case Positive — 현재 코드 동작을 회귀 고정(갭 16은 임의로 해소된 것으로 단정하지 않음)
        @breaks 이 우선순위 관계가 의도치 않게 뒤바뀌는(코드 변경) 회귀 — 뒤바뀌면 갭 16 재검토 필요
        """
        arbiter = CommandArbiter()
        candidates = [
            buildCandidateCommand(Door.LEFT, ArbitrationCommand.LOCK, 2, "APPROACH_RISK_LEFT"),
            buildCandidateCommand(Door.BOTH, ArbitrationCommand.RELEASE, 4, "IGNITION_OFF"),
        ]

        result = arbiter.arbitrate(buildStateResult(SystemState.OFF), True, candidates)

        self.assertEqual(result.leftCommand, ArbitrationCommand.LOCK)
        self.assertEqual(result.leftReasonCode, "APPROACH_RISK_LEFT")
        self.assertEqual(result.rightCommand, ArbitrationCommand.RELEASE)
        self.assertEqual(result.rightReasonCode, "IGNITION_OFF")


class TestIT0113FirePriorityWinsOverIsofixForcedLock(unittest.TestCase):
    """IT-0113 — Trace: IF-0008/IF-0019/IF-0022 / SWR-017, SWR-018, 9장 "RELEASE 계열이 LOCK 계열보다 항상 우선" """

    def testFireForcedReleaseOverridesIsofixLockOnBothDoors(self):
        """!
        @brief 화재 등 강제해제(priority=3, BOTH, RELEASE)와 ISOFIX 강제잠금(priority=5, BOTH,
               LOCK)이 동시에 존재하면 RELEASE가 선택되어야 한다("RELEASE 계열이 LOCK 계열보다
               항상 우선한다"는 단일 원칙, 9장).
        @technique 결정테이블 테스트(Decision Table Testing) — 우선순위 충돌(3 vs 5)
        @case Positive
        @breaks LOCK 계열(ISOFIX)이 잘못 선택되는 회귀
        """
        arbiter = CommandArbiter()
        candidates = [
            buildCandidateCommand(Door.BOTH, ArbitrationCommand.RELEASE, 3, "FORCED_RELEASE"),
            buildCandidateCommand(Door.BOTH, ArbitrationCommand.LOCK, 5, "ISOFIX_FORCED_LOCK_LEFT"),
        ]

        result = arbiter.arbitrate(buildStateResult(SystemState.NORMAL), True, candidates)

        self.assertEqual(result.leftCommand, ArbitrationCommand.RELEASE)
        self.assertEqual(result.rightCommand, ArbitrationCommand.RELEASE)
        self.assertEqual(result.leftReasonCode, "FORCED_RELEASE")


class TestIT0114FaultGateBlocksAllPhase3Candidates(unittest.TestCase):
    """IT-0114 — Trace: IF-0008 / 8장 Phase3 확정 사항 재확인, 회귀(1~4, 8~12단계)"""

    def testFaultStateBlocksEvenWithNonEmptyPhase3Candidates(self):
        """!
        @brief state==FAULT이면 ignition-off/ISOFIX/자동주행잠금 후보가 모두 존재해도
               blocked=True/STATE_FAULT로 전부 차단되어야 한다(FAULT가 모든 Phase 후보보다
               항상 우선, Phase1/2 게이트 로직 회귀 확인을 겸함, 11장 18단계 회귀 범위).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 D 유지, 신규 우선순위 무관 확인
        @case Negative
        @breaks 신규 우선순위 규칙 추가가 FAULT 게이트를 깨서 후보가 통과되는 회귀
        """
        arbiter = CommandArbiter()
        candidates = [
            buildCandidateCommand(Door.BOTH, ArbitrationCommand.RELEASE, 4, "IGNITION_OFF"),
            buildCandidateCommand(Door.LEFT, ArbitrationCommand.LOCK, 5, "ISOFIX_FORCED_LOCK_LEFT"),
            buildCandidateCommand(Door.BOTH, ArbitrationCommand.LOCK, 6, "AUTO_DRIVE_LOCK"),
        ]

        result = arbiter.arbitrate(buildStateResult(SystemState.FAULT), True, candidates)

        self.assertTrue(result.blocked)
        self.assertEqual(result.blockReason, "STATE_FAULT")
        self.assertEqual(result.leftCommand, ArbitrationCommand.NO_CHANGE)
        self.assertEqual(result.rightCommand, ArbitrationCommand.NO_CHANGE)
        self.assertIsNone(result.leftReasonCode)
        self.assertIsNone(result.rightReasonCode)


class TestIT0115InputInvalidGateBlocksAllPhase3Candidates(unittest.TestCase):
    """IT-0115 — Trace: IF-0008 / 결정표 D 유지, 회귀(1~4, 8~12단계)"""

    def testInputInvalidBlocksEvenWithNonEmptyPhase3Candidates(self):
        """!
        @brief state!=FAULT이지만 inputValid==False이면 Phase3 후보가 존재해도 blocked=True/
               INPUT_INVALID로 차단되어야 한다(결정표 D 유지 재확인).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 D 행 2, 신규 우선순위 무관 확인
        @case Negative
        @breaks 입력 무효 상태에서도 Phase3 후보가 통과되는 회귀
        """
        arbiter = CommandArbiter()
        candidates = [buildCandidateCommand(Door.BOTH, ArbitrationCommand.LOCK, 6, "AUTO_DRIVE_LOCK")]

        result = arbiter.arbitrate(buildStateResult(SystemState.NORMAL), False, candidates)

        self.assertTrue(result.blocked)
        self.assertEqual(result.blockReason, "INPUT_INVALID")


class TestIT0116DuplicateMinimumPriorityAmongPhase3CandidatesRaises(unittest.TestCase):
    """IT-0116 — Trace: IF-0008 / 결정표 I 비고(설계상 불변조건), 오류주입"""

    def testTwoPhase3CandidatesWithSamePriorityOnSameDoorRaisesValueError(self):
        """!
        @brief 동일 문에 동일 최소 priority(신규 Phase3 값 포함) 후보가 2개 이상 존재하면
               설계상 발생 불가한 내부 불변조건 위반으로 간주해 ValueError를 발생시켜야 한다
               (Phase1/2와 동일한 불변조건이 신규 priority 5에도 그대로 적용됨을 확인).
        @technique 오류주입(Fault Injection Test) — 불변조건 위반(중복 priority=5) 주입
        @case Negative
        @breaks 충돌하는 두 후보 중 하나가 임의로 선택되고 예외가 발생하지 않는 회귀
        """
        arbiter = CommandArbiter()
        candidates = [
            buildCandidateCommand(Door.BOTH, ArbitrationCommand.LOCK, 5, "ISOFIX_FORCED_LOCK_LEFT"),
            buildCandidateCommand(Door.BOTH, ArbitrationCommand.LOCK, 5, "DUPLICATE_PRIORITY"),
        ]

        with self.assertRaises(ValueError):
            arbiter.arbitrate(buildStateResult(SystemState.NORMAL), True, candidates)


if __name__ == "__main__":
    unittest.main()
