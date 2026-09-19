"""!
@file test_approach_risk_override_manager.py
@brief IU-0012(ARC-0012 접근위험 override 판정기) 함수 계약 검증(ENG-SWE3-001 5.6절/6.11절/
       7장 결정표 G/8.6절 상태전이, SWR-006 10초 override 윈도우).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ngv.domain.constants import (
    REASON_CODE_APPROACH_RISK_OVERRIDE_LEFT,
    REASON_CODE_APPROACH_RISK_OVERRIDE_RIGHT,
)
from ngv.core.approach_risk_override_manager import ApproachRiskOverrideManager


class TestApproachRiskOverrideManagerDecide(unittest.TestCase):
    """IU-0012.decide() 결정표 G/타이머 갱신 규칙 계약 검증."""

    def testNoOverrideWhenRiskInactive(self):
        """!
        @brief leftRiskActive=False이면 재입력 여부와 무관하게 leftOverrideActive=False다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 G, riskActive=False 행
        @case Negative — 위험이 없는데도 override가 성립하지 않는지 검증
        @breaks riskActive=False인데도 override가 성립하는 회귀
        """
        manager = ApproachRiskOverrideManager()

        result = manager.decide(False, False, True, True, 1.0)

        self.assertFalse(result.leftOverrideActive)
        self.assertIsNone(result.leftOverrideReasonCode)
        self.assertFalse(result.rightOverrideActive)
        self.assertIsNone(result.rightOverrideReasonCode)

    def testNoOverrideWhenRiskActiveButNoReRequest(self):
        """!
        @brief riskActive=True이지만 releaseReRequested=False이면 override가 성립하지 않는다.
        @technique 결정테이블 테스트(Decision Table Testing) — 결정표 G, (True, False, 무관) 행
        @case Negative — 재입력 신호 없이는 override가 성립하지 않는지 검증
        @breaks 재입력 없이도 override가 성립하는 회귀
        """
        manager = ApproachRiskOverrideManager()

        result = manager.decide(True, False, False, False, 1.0)

        self.assertFalse(result.leftOverrideActive)

    def testOverrideActiveAtExactlyTenSecondsBoundary(self):
        """!
        @brief 억제 시작 후 정확히 10.0초(경계값) 경과 시점 재입력은 override를 성립시킨다(SWR-006a).
        @technique 경계값분석(Boundary Value Analysis) — OVERRIDE_WINDOW_S(10.0) 상한 경계, 이하 포함
        @case Positive — "10초 이하 경과"라는 원문 문언(<=) 경계값을 검증
        @breaks 경계 비교를 <로 잘못 구현해 정확히 10.0초를 거절하는 회귀
        """
        manager = ApproachRiskOverrideManager()
        manager.decide(True, False, False, False, 0.0)

        result = manager.decide(True, False, True, False, 10.0)

        self.assertTrue(result.leftOverrideActive)
        self.assertEqual(result.leftOverrideReasonCode, REASON_CODE_APPROACH_RISK_OVERRIDE_LEFT)

    def testOverrideNotActiveJustOverTenSecondsBoundary(self):
        """!
        @brief 억제 시작 후 10.1초 경과 시점 재입력은 override를 성립시키지 않는다(SWR-006b).
        @technique 경계값분석(Boundary Value Analysis) — OVERRIDE_WINDOW_S(10.0) 상한 경계 바로 위
        @case Negative — "10초를 초과"하면 불성립이라는 원문 문언 경계값을 검증
        @breaks 10.1초에도 override가 성립하는 회귀(억제 유지 실패)
        """
        manager = ApproachRiskOverrideManager()
        manager.decide(True, False, False, False, 0.0)

        result = manager.decide(True, False, True, False, 10.1)

        self.assertFalse(result.leftOverrideActive)
        self.assertIsNone(result.leftOverrideReasonCode)

    def testRiskInactiveThenReactiveStartsNewTenSecondWindow(self):
        """!
        @brief 위험 해제 후 재진입하면 타이머가 리셋되어 새 10초 윈도우가 시작된다(6.11절 확정 규칙).
        @technique 상태전이 테스트(State Transition Testing) — Suppressed->Idle->Suppressed 재진입
        @case Negative — 이전 억제 시각이 남아 새 윈도우 판정을 오염시키지 않는지 검증
        @breaks 리셋 없이 이전 firstSuppressedAtS가 유지되어 조기에 override 불성립 판정을 내리는 회귀
        """
        manager = ApproachRiskOverrideManager()
        manager.decide(True, False, False, False, 0.0)
        manager.decide(False, False, False, False, 5.0)
        manager.decide(True, False, False, False, 100.0)

        result = manager.decide(True, False, True, False, 108.0)

        self.assertTrue(result.leftOverrideActive)

    def testLeftAndRightAreFullyIndependent(self):
        """!
        @brief 좌측이 override 성립 조건이어도 우측(무관 상태)은 영향받지 않는다(SWR-009 승계).
        @technique 동등분할(Equivalence Partitioning) — 좌/우 조합 중 좌만 활성인 대표값
        @case Positive — IU-0012 내부에서도 좌우 상태가 공유되지 않는지 검증
        @breaks 좌측 override 판정이 우측 필드에 영향을 주는 회귀
        """
        manager = ApproachRiskOverrideManager()
        manager.decide(True, False, False, False, 0.0)

        result = manager.decide(True, False, True, False, 5.0)

        self.assertTrue(result.leftOverrideActive)
        self.assertFalse(result.rightOverrideActive)
        self.assertIsNone(result.rightOverrideReasonCode)

    def testRightOverrideUsesRightReasonCode(self):
        """!
        @brief 우측 override 성립 시 우측 전용 이유코드(APPROACH_RISK_OVERRIDE_RIGHT)를 사용한다.
        @technique 동등분할(Equivalence Partitioning) — 우측 활성 대표값
        @case Positive — 좌/우 이유코드가 뒤섞이지 않는지 검증
        @breaks 우측 override에 좌측 이유코드가 잘못 부여되는 회귀
        """
        manager = ApproachRiskOverrideManager()
        manager.decide(False, True, False, False, 0.0)

        result = manager.decide(False, True, False, True, 3.0)

        self.assertTrue(result.rightOverrideActive)
        self.assertEqual(result.rightOverrideReasonCode, REASON_CODE_APPROACH_RISK_OVERRIDE_RIGHT)


class TestApproachRiskOverrideManagerReset(unittest.TestCase):
    """IU-0012.reset() 계약 검증."""

    def testResetClearsSuppressionTimerEvenWhileRiskStaysActive(self):
        """!
        @brief reset()은 leftRiskActive가 계속 True인 도중에도 저장된 최초 억제 시각을 지운다.
        @technique 상태전이 테스트(State Transition Testing) — reset()에 의한 Idle 강제 복귀
        @case Positive — 부팅/재시작 시 억제 이력이 없다는 8.6절 계약을 검증
        @breaks reset()이 아무 효과가 없어 오래된 firstSuppressedAtLeftS(t=0)가 그대로 남아
                50초 뒤 재입력이 윈도우 만료(elapsed>10)로 잘못 거절되는 회귀
        """
        manager = ApproachRiskOverrideManager()
        manager.decide(True, False, False, False, 0.0)
        manager.decide(True, False, False, False, 50.0)

        manager.reset()
        result = manager.decide(True, False, True, False, 50.05)

        self.assertTrue(result.leftOverrideActive)


if __name__ == "__main__":
    unittest.main()
