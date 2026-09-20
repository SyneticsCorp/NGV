"""!
@file constants.py
@brief 안전 커널 전역 상수(ENG-SWE3-001 4장 "상수(Constants)" 표를 그대로 구현).

@par 관련 항목
- 요구사항: SWR-013, SWR-021
- 상세설계: ENG-SWE3-001 4장, 6.1절(EVALUATION_TICK_S 근거)
"""

from ngv.domain.types import LockCommand

## SWR-013(a) 원문 수치(200ms). freshness stale 판정 임계값(초). 변경 불가(요구사항 직접 인용).
FRESHNESS_STALE_THRESHOLD_S = 0.200

## SWR-013(a) 원문 수치(100ms 이내 전이). 코드 판단에는 쓰이지 않으며 EVALUATION_TICK_S 선정 근거로만 사용.
FRESHNESS_DETECTION_BUDGET_S = 0.100

## 평가주기(tick) 길이(초). 신규 확정(ENG-SWE3-001 6.1절) — 100ms 마감시한 대비 2배 여유.
EVALUATION_TICK_S = 0.050

## 부팅 시 초기 확정 출력 기본값(안전측 기본값, ENG-SWE3-001 8장 근거).
BOOT_DEFAULT_LOCK_COMMAND = LockCommand.LOCK

## sensor_fault 필드 자체가 INVALID일 때의 fail-safe 대체값(ENG-SWE3-001 10장 근거).
SENSOR_FAULT_FAILSAFE_SUBSTITUTE_VALUE = True

## 정상 수신된 sensor_fault=TRUE에 대한 경고코드(ENG-SWE3-001 4장 경고코드 카탈로그, 확인 필요 — OEM 카탈로그 확정 전 SW 자체 정의).
WARNING_CODE_SENSOR_FAULT_DETECTED = "SENSOR_FAULT_DETECTED"

## sensor_fault 필드 자체가 INVALID여서 fail-safe 대체가 적용된 경우의 경고코드(위와 동일 근거).
WARNING_CODE_SENSOR_FAULT_INPUT_INVALID = "SENSOR_FAULT_INPUT_INVALID"

## IU-0009가 2-1~2-4단계 예외를 포착해 FAULT를 강제할 때 사용하는 경고코드(ENG-SWE3-001 6.6절/10.2절).
WARNING_CODE_ORCHESTRATION_ERROR = "ORCHESTRATION_ERROR"

## IU-0005 게이트가 state==FAULT로 차단할 때의 blockReason(ENG-SWE3-001 5장 IU-0005 계약).
BLOCK_REASON_STATE_FAULT = "STATE_FAULT"

## IU-0005 게이트가 inputValid==False로 차단할 때의 blockReason(ENG-SWE3-001 5장 IU-0005 계약).
BLOCK_REASON_INPUT_INVALID = "INPUT_INVALID"

## SWR-006(a)/(b) 원문 수치(10초). override 재입력 판정 윈도우(초). 변경 불가(요구사항 직접 인용).
OVERRIDE_WINDOW_S = 10.0

## 충돌(crash) 후보 우선순위(최고). ENG-SWE2-001 4장/9장 우선순위 태그. 변경 불가(질적 순서).
PRIORITY_CRASH = 1

## 접근위험(approach risk) 후보 우선순위(중간). 상동.
PRIORITY_APPROACH_RISK = 2

## 화재/과온/탑승(fire/overtemp/occupant) 후보 우선순위(최저, 그러나 필수). 상동.
PRIORITY_FIRE_OVERTEMP_OCCUPANT = 3

## IU-0010이 crash_status=CONFIRMED일 때 생성하는 긴급해제 후보의 이유코드(ENG-SWE3-001 4장 카탈로그).
REASON_CODE_CRASH_CONFIRMED = "CRASH_CONFIRMED"

## IU-0011이 좌측 접근위험 억제 후보에 부여하는 이유코드.
REASON_CODE_APPROACH_RISK_LEFT = "APPROACH_RISK_LEFT"

## IU-0011이 우측 접근위험 억제 후보에 부여하는 이유코드.
REASON_CODE_APPROACH_RISK_RIGHT = "APPROACH_RISK_RIGHT"

## IU-0012가 좌측 override 성립 시 부여하는 이유코드(SWR-006a).
REASON_CODE_APPROACH_RISK_OVERRIDE_LEFT = "APPROACH_RISK_OVERRIDE_LEFT"

## IU-0012가 우측 override 성립 시 부여하는 이유코드(SWR-006a).
REASON_CODE_APPROACH_RISK_OVERRIDE_RIGHT = "APPROACH_RISK_OVERRIDE_RIGHT"

## IU-0013이 fire_detected=True일 때 triggeredReasonCodes에 추가하는 이유코드.
REASON_CODE_FIRE_DETECTED = "FIRE_DETECTED"

## IU-0013이 overtemperature_detected=True일 때 triggeredReasonCodes에 추가하는 이유코드.
REASON_CODE_OVERTEMPERATURE_DETECTED = "OVERTEMPERATURE_DETECTED"

## IU-0013이 adult_present=True일 때 triggeredReasonCodes에 추가하는 이유코드.
REASON_CODE_ADULT_PRESENT_DETECTED = "ADULT_PRESENT_DETECTED"

## IU-0013이 triggered=True일 때 releaseCandidate.reasonCode에 부여하는 대표 마커.
REASON_CODE_FORCED_RELEASE = "FORCED_RELEASE"

## IU-0001.validateCrashStatusField()가 str이지만 정의된 3개 값(NONE/PENDING/CONFIRMED) 외일 때의 오류 사유.
ERROR_REASON_INVALID_ENUM_VALUE = "INVALID_ENUM_VALUE"

## ignition-off 해제(RELEASE 계열) 후보 우선순위(Phase3 신규). ENG-SWE2-001 9장 우선순위 체인 확정.
## SWR-007(a) 원문 직접 근거로 crash(1)보다는 낮고 fire(3)보다도 낮으나, ISOFIX/자동주행잠금(5,6)
## 보다는 높다 — entrapment 방지 취지상 ignition-off가 LOCK 계열보다 우선(SW 설계 재량).
PRIORITY_IGNITION_OFF_RELEASE = 4

## ISOFIX 강제잠금(LOCK 계열) 후보 우선순위(Phase3 신규). 자동주행잠금보다 근소하게 높은
## 우선순위(더 구체적인 위험신호) — 영향은 미미(둘 다 LOCK이므로 최종 출력에는 무관, 이유코드
## 보고 순서에만 영향). ENG-SWE2-001 9장 근거.
PRIORITY_ISOFIX_FORCED_LOCK = 5

## 자동주행잠금(LOCK 계열) 후보 우선순위(Phase3 신규). 우선순위 체인 전체에서 최저. 상동.
PRIORITY_AUTO_DRIVE_LOCK = 6

## SWR-003(a)/(b) 원문 수치(3 km/h). 자동주행잠금 차속 임계값. 변경 불가(요구사항 직접 인용).
AUTO_DRIVE_LOCK_SPEED_THRESHOLD_KPH = 3.0

## ENG-SWE2-001 6.2절 IF-0001 범위(0.0~300.0). vehicle_speed_kph 유효 범위 하한. 변경 불가(아키텍처 직접 인용).
VEHICLE_SPEED_MIN_KPH = 0.0

## 상동. vehicle_speed_kph 유효 범위 상한.
VEHICLE_SPEED_MAX_KPH = 300.0

## IU-0014 lockCandidate.reasonCode(ENG-SWE2-001 IF-0021 예시 문구 그대로 채택).
REASON_CODE_AUTO_DRIVE_LOCK = "AUTO_DRIVE_LOCK"

## IU-0015 leftReasonCode(경고코드 카탈로그 미확정, 갭 3 승계 — SW 자체 정의 문자열).
REASON_CODE_ISOFIX_LEFT = "ISOFIX_FORCED_LOCK_LEFT"

## IU-0015 rightReasonCode. 상동.
REASON_CODE_ISOFIX_RIGHT = "ISOFIX_FORCED_LOCK_RIGHT"

## IU-0016 releaseCandidate.reasonCode(ENG-SWE2-001 IF-0023 예시 문구 그대로 채택).
REASON_CODE_IGNITION_OFF = "IGNITION_OFF"

## IU-0003이 state==OFF일 때 생성하는 StateResult.warningReasonCode(ENG-SWE2-001 7장 시나리오10
## 근거 — REASON_CODE_IGNITION_OFF와 값은 같으나 별도 네임스페이스, WARNING_CODE_SENSOR_FAULT_*
## 선례와 동일 관례).
WARNING_CODE_IGNITION_OFF = "IGNITION_OFF"
