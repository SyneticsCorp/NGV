"""!
@file test_it_step10_override_manager.py
@brief 통합 10단계 — ARC-0012(접근위험 override 판정기), IF-0018 인터페이스 계약 검증(신규,
       Phase2).

테스트 베이시스: ENG-SWE2-001 6.1절(IF-0018), 11장 순서표 10행("단위시험 하네스, 합성
leftRiskActive/rightRiskActive와 releaseReRequested placeholder 주입, 결정론적 고정 시계로
10초 경계 시험"). ENG-SWE3-001 7장 결정표 G(좌측 예시, 우측 대칭)와 8.6절 상태전이(타이머
리셋 규칙)를 그대로 사용한다. ARC-0011 실물은 불필요(파라미터로 합성 입력 — 리프-리프 코드
의존이 없음을 그대로 확인).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.core.approach_risk_override_manager import ApproachRiskOverrideManager


class TestIT0055RiskActiveWithoutReRequestYieldsNoOverride(unittest.TestCase):
    """IT-0055 — Trace: IF-0018 / SWR-006, 결정표 G"""

    def testRiskActiveButNoReleaseReRequestedYieldsSuppressionMaintained(self):
        """!
        @brief leftRiskActive=True이지만 leftReleaseReRequested=False이면 override가 성립하지
               않고 억제가 유지되어야 한다(결정표 G 기본 행).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 G, 재입력 없음 행
        @case Negative
        @breaks 재입력 신호 없이도 override가 성립하는 회귀
        """
        manager = ApproachRiskOverrideManager()

        result = manager.decide(True, False, False, False, 0.0)

        self.assertFalse(result.leftOverrideActive)
        self.assertIsNone(result.leftOverrideReasonCode)


class TestIT0056OverrideActiveAtExactlyTenSecondBoundary(unittest.TestCase):
    """IT-0056 — Trace: IF-0018 / SWR-006(a), 경계값분석"""

    def testExactlyTenSecondsElapsedYieldsOverrideActive(self):
        """!
        @brief 최초 억제 시각으로부터 정확히 10.0초 경과 시점의 재입력은 override를 성립시켜야
               한다("10초 이내" 문언의 <= 경계, SWR-006a).
        @technique 경계값분석(Boundary Value Analysis) — OVERRIDE_WINDOW_S(10.0) 상한 경계(포함)
        @case Positive
        @breaks 경계 비교를 <로 잘못 구현해 정확히 10.0초를 거절하는 회귀
        """
        manager = ApproachRiskOverrideManager()
        manager.decide(True, False, False, False, 100.0)

        result = manager.decide(True, False, True, False, 110.0)

        self.assertTrue(result.leftOverrideActive)
        self.assertEqual(result.leftOverrideReasonCode, "APPROACH_RISK_OVERRIDE_LEFT")


class TestIT0057OverrideNotActiveJustOverTenSecondBoundary(unittest.TestCase):
    """IT-0057 — Trace: IF-0018 / SWR-006(b), 경계값분석"""

    def testTenPointOneSecondsElapsedYieldsOverrideNotActive(self):
        """!
        @brief 최초 억제 시각으로부터 10.1초 경과 시점의 재입력은 override를 성립시키지 않아야
               한다(SWR-006b, 상한 경계 바로 위).
        @technique 경계값분석(Boundary Value Analysis) — OVERRIDE_WINDOW_S(10.0) 상한 경계 바로 위
        @case Negative
        @breaks 10.1초에도 override가 성립하는 회귀(억제 유지 실패)
        """
        manager = ApproachRiskOverrideManager()
        manager.decide(True, False, False, False, 100.0)

        result = manager.decide(True, False, True, False, 110.1)

        self.assertFalse(result.leftOverrideActive)
        self.assertIsNone(result.leftOverrideReasonCode)


class TestIT0058RiskInactiveResetsTimerRegardlessOfReRequest(unittest.TestCase):
    """IT-0058 — Trace: IF-0018 / 결정표 G, riskActive=False 행"""

    def testRiskInactiveYieldsNoOverrideAndClearsTimer(self):
        """!
        @brief leftRiskActive=False이면 releaseReRequested 값과 무관하게 override가 성립하지
               않고 타이머가 즉시 리셋되어야 한다(결정표 G riskActive=False 행).
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 G, riskActive=False 행
        @case Negative
        @breaks 위험이 없는데도 override가 성립하는 회귀
        """
        manager = ApproachRiskOverrideManager()
        manager.decide(True, False, False, False, 0.0)

        result = manager.decide(False, False, True, False, 1.0)

        self.assertFalse(result.leftOverrideActive)
        self.assertIsNone(result.leftOverrideReasonCode)


class TestIT0059LeftAndRightDoorsAreFullyIndependent(unittest.TestCase):
    """IT-0059 — Trace: IF-0018 / SWR-009 승계, 동등분할"""

    def testLeftOverrideDoesNotAffectRightDoor(self):
        """!
        @brief 좌측이 override 성립 조건이어도 우측 도어는 영향받지 않아야 한다(IU-0012 내부에서도
               좌/우 상태가 공유되지 않음).
        @technique 동등분할(Equivalence Partitioning) — 좌만 활성인 대표값
        @case Positive
        @breaks 좌측 override 판정이 우측 필드에 영향을 주는 회귀
        """
        manager = ApproachRiskOverrideManager()
        manager.decide(True, True, False, False, 0.0)

        result = manager.decide(True, True, True, False, 5.0)

        self.assertTrue(result.leftOverrideActive)
        self.assertFalse(result.rightOverrideActive)
        self.assertIsNone(result.rightOverrideReasonCode)


class TestIT0060SuppressionRestartsAfterRiskClearsAndReturns(unittest.TestCase):
    """IT-0060 — Trace: IF-0018 / 8.6절 상태전이(타이머 리셋 규칙)"""

    def testRiskClearsThenReactivatesStartsNewTenSecondWindow(self):
        """!
        @brief risk가 False로 전이되면 억제 타이머가 즉시 리셋되고, 재진입 시 새 10초 윈도우가
               시작되어야 한다(6.11절 확정 규칙, 8.6절 상태전이).
        @technique 상태전이 테스트(State Transition Testing) — Suppressed->Idle->Suppressed 재진입
        @case Negative
        @breaks 리셋 없이 이전 최초 억제 시각이 유지되어 새 윈도우 판정을 오염시키는 회귀
        """
        manager = ApproachRiskOverrideManager()
        manager.decide(True, False, False, False, 0.0)
        manager.decide(False, False, False, False, 3.0)
        manager.decide(True, False, False, False, 200.0)

        result = manager.decide(True, False, True, False, 209.0)

        self.assertTrue(result.leftOverrideActive)


class TestIT0061ResetClearsSuppressionTimer(unittest.TestCase):
    """IT-0061 — Trace: IF-0018 / 8.6절 상태전이(reset())"""

    def testResetClearsTimerEvenWhileRiskStaysActive(self):
        """!
        @brief reset()은 leftRiskActive가 계속 True인 도중에도 저장된 최초 억제 시각을 지워야
               한다(부팅/재시작 시 억제 이력 없음, 8.6절 fail-safe 방향).
        @technique 상태전이 테스트(State Transition Testing) — reset()에 의한 Idle 강제 복귀
        @case Positive
        @breaks reset()이 효과가 없어 오래된 최초 억제 시각이 남아 재입력이 잘못 거절되는 회귀
        """
        manager = ApproachRiskOverrideManager()
        manager.decide(True, False, False, False, 0.0)
        manager.decide(True, False, False, False, 50.0)

        manager.reset()
        result = manager.decide(True, False, True, False, 50.05)

        self.assertTrue(result.leftOverrideActive)


if __name__ == "__main__":
    unittest.main()
