"""!
@file test_it_step3_output_hold_actuator.py
@brief 통합 3단계 — ARC-0004(출력 유지 액추에이터), IF-0009 인터페이스 계약 검증.

테스트 베이시스: ENG-SWE2-001 6.1절(IF-0009), 11장 순서표 3행("단위시험 하네스로 직접 호출,
합성 StateResult/ArbitrationResult 주입 — 불필요[실물]").
"""

import unittest

from tests_integration.it_helpers import ArbitrationCommand, SystemState, buildArbitrationResult, buildStateResult
from ngv.core.output_hold_actuator import OutputHoldActuator
from ngv.domain.types import LockCommand


class TestIT0012FaultFreezesOutput(unittest.TestCase):
    """IT-0012 — Trace: IF-0009 / SWR-021(a)"""

    def testFaultStateIgnoresArbitrationAndFreezesLastOutput(self):
        """!
        @brief state==FAULT면 ArbitrationResult 내용과 무관하게 직전 확정값을 그대로 유지해야
               한다(fail-freeze, SWR-021a, 결정표 B).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 B 행 1(FAULT)
        @case Positive
        @breaks FAULT 상태에서도 후보 명령이 출력에 반영되는 회귀(안전 요구사항 위반)
        """
        actuator = OutputHoldActuator()
        actuator.confirm(
            buildArbitrationResult(ArbitrationCommand.RELEASE, ArbitrationCommand.RELEASE),
            buildStateResult(SystemState.NORMAL),
        )

        maliciousCandidate = buildArbitrationResult(ArbitrationCommand.RELEASE, ArbitrationCommand.RELEASE)
        result = actuator.confirm(maliciousCandidate, buildStateResult(SystemState.FAULT))

        self.assertEqual(result.left, LockCommand.RELEASE)
        self.assertEqual(result.right, LockCommand.RELEASE)


class TestIT0013NormalStateAppliesCandidateCommands(unittest.TestCase):
    """IT-0013 — Trace: IF-0009"""

    def testNormalStateResolvesEachAxisIndependently(self):
        """!
        @brief FAULT가 아니면 좌/우 각 축이 후보 커맨드(LOCK/RELEASE)를 독립적으로 반영해야 한다.
        @technique 동등분할(Equivalence Partitioning) — LOCK/RELEASE 각 축 조합
        @case Positive
        @breaks 한쪽 축의 커맨드가 반대쪽 축에 영향을 주는 회귀(축 간 결합)
        """
        actuator = OutputHoldActuator()

        result = actuator.confirm(
            buildArbitrationResult(ArbitrationCommand.LOCK, ArbitrationCommand.RELEASE),
            buildStateResult(SystemState.NORMAL),
        )

        self.assertEqual(result.left, LockCommand.LOCK)
        self.assertEqual(result.right, LockCommand.RELEASE)


class TestIT0014NoChangeRetainsPreviousValue(unittest.TestCase):
    """IT-0014 — Trace: IF-0009"""

    def testNoChangeCommandKeepsPreviousAxisValue(self):
        """!
        @brief NO_CHANGE 커맨드는 해당 축의 직전 확정값을 그대로 유지해야 한다.
        @technique 동등분할(Equivalence Partitioning) — NO_CHANGE 클래스
        @case Positive
        @breaks NO_CHANGE가 예기치 않게 기본값(LOCK)으로 강제되는 회귀
        """
        actuator = OutputHoldActuator()
        actuator.confirm(
            buildArbitrationResult(ArbitrationCommand.RELEASE, ArbitrationCommand.RELEASE),
            buildStateResult(SystemState.NORMAL),
        )

        result = actuator.confirm(
            buildArbitrationResult(ArbitrationCommand.NO_CHANGE, ArbitrationCommand.NO_CHANGE),
            buildStateResult(SystemState.NORMAL),
        )

        self.assertEqual(result.left, LockCommand.RELEASE)
        self.assertEqual(result.right, LockCommand.RELEASE)


class TestIT0015BootDefaultOutputIsLockLock(unittest.TestCase):
    """IT-0015 — Trace: IF-0009, 8장 부팅 시 초기 확정값"""

    def testConstructionYieldsLockLockBootDefault(self):
        """!
        @brief 생성 직후(부팅 시) getLastConfirmedOutput()은 (LOCK, LOCK)이어야 한다
               (ENG-SWE3-001 8장, 안전측 기본값).
        @technique 요구사항 기반 시험(Requirements-based Test) — 부팅 기본값 확인 필요 항목 해소
        @case Positive
        @breaks 부팅 기본값이 RELEASE로 바뀌는 회귀(안전측 기본값 위반)
        """
        actuator = OutputHoldActuator()

        default = actuator.getLastConfirmedOutput()

        self.assertEqual(default.left, LockCommand.LOCK)
        self.assertEqual(default.right, LockCommand.LOCK)


class TestIT0016ResetRestoresBootDefault(unittest.TestCase):
    """IT-0016 — Trace: IF-0009"""

    def testResetAfterChangeRestoresBootDefault(self):
        """!
        @brief 값이 바뀐 뒤 reset()을 호출하면 다시 (LOCK, LOCK) 부팅 기본값으로 복귀해야 한다.
        @technique 상태전이 테스트(State Transition Testing) — 변경 이력 -> reset -> 부팅 상태
        @case Positive
        @breaks reset()이 직전 확정값을 초기화하지 않는 회귀
        """
        actuator = OutputHoldActuator()
        actuator.confirm(
            buildArbitrationResult(ArbitrationCommand.RELEASE, ArbitrationCommand.RELEASE),
            buildStateResult(SystemState.NORMAL),
        )

        actuator.reset()

        default = actuator.getLastConfirmedOutput()
        self.assertEqual(default.left, LockCommand.LOCK)
        self.assertEqual(default.right, LockCommand.LOCK)


if __name__ == "__main__":
    unittest.main()
