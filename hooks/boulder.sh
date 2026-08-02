#!/usr/bin/env bash
# DevEval Agents — 완료 엔진 (Stop hook)
#
# Claude Code Stop hook. Claude가 응답을 끝내려 할 때 발화한다.
# 평가 작업판(.omo/eval-plan.md)에 미완료 체크박스가 남아 있으면
#   exit 2 + stderr 로 "계속하라"는 메시지를 Claude에 전달해 멈추지 못하게 한다.
#
# 무한루프 가드: (1) 정체 3회 (2) 시도 20회 를 넘으면 **일시정지**한다 —
# 작업판의 지문(cksum)을 상태 파일에 남기고 종료를 허용하며, 작업판이 그대로인
# 동안은 매 턴 다시 조르지 않는다. 작업판이 편집되면(체크·항목 추가 = 재개 의사)
# 카운터를 리셋하고 다시 무장한다.
#
# 완료 신호 = 모든 체크박스가 [x] 또는 [~](막힘). 미완료 = [ ].

PROJECT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
PLAN="$PROJECT/.omo/eval-plan.md"
STATE="$PROJECT/.omo/.boulder-state"

# 작업판이 없으면 평가 모드가 아님 → 정상 종료 허용
[ -f "$PLAN" ] || exit 0

# 읽기전용 작업공간에서는 정체 횟수를 저장할 수 없어 무한 재개될 수 있다.
# 상태 디렉토리에 쓸 수 없으면 안전하게 종료를 허용한다.
[ -w "$(dirname "$STATE")" ] || exit 0

# 미완료 체크박스 개수 ( - [ ] ). [x](완료)·[~](막힘)는 제외된다.
INCOMPLETE=$(grep -cE '^[[:space:]]*- \[ \]' "$PLAN" 2>/dev/null || true)
INCOMPLETE=${INCOMPLETE:-0}

# 모두 완료 → 종료 허용 + 상태 리셋
if [ "$INCOMPLETE" -eq 0 ]; then
  rm -f "$STATE"
  exit 0
fi

# 작업판 지문 — 일시정지 후 "편집됐는가(재개 의사)"를 판별한다
FP=$(cksum < "$PLAN" 2>/dev/null || echo "0 0")

# --- 상태 파일: "이전미완료 정체횟수 총시도" 또는 "paused <cksum> <bytes>" ---
PREV=-1; STALL=0; TOTAL=0
if [ -f "$STATE" ]; then
  read -r F1 F2 F3 < "$STATE"
  if [ "$F1" = "paused" ]; then
    if [ "$F2 $F3" = "$FP" ]; then
      exit 0   # 방치된 작업판 — 편집 전까지 다시 조르지 않는다
    fi
    # 작업판이 바뀜 = 재개 의사 → 카운터 리셋 후 재무장
  elif printf '%s' "$F1" | grep -qE '^-?[0-9]+$'; then
    PREV=$F1; STALL=${F2:-0}; TOTAL=${F3:-0}
  fi
fi
TOTAL=$((TOTAL + 1))

pause() { printf 'paused %s\n' "$FP" > "$STATE" 2>/dev/null; exit 0; }

# (가드 1) 시도 상한: 20회 초과 → 일시정지 (작업판 편집 시 재무장)
[ "$TOTAL" -gt 20 ] && pause

# 진전 체크: 미완료가 줄었으면 정체 리셋, 아니면 정체++
if [ "$PREV" -eq -1 ] || [ "$INCOMPLETE" -lt "$PREV" ]; then
  STALL=0
else
  STALL=$((STALL + 1))
fi

# (가드 2) 정체 3회(진전 없이 같은 자리) → 일시정지 (사람 개입 유도)
[ "$STALL" -ge 3 ] && pause

if ! printf '%s %s %s\n' "$INCOMPLETE" "$STALL" "$TOTAL" > "$STATE"; then
  exit 0
fi

# 미완료 항목 목록 (최대 10개)
PENDING=$(grep -E '^[[:space:]]*- \[ \]' "$PLAN" | sed -E 's/^[[:space:]]*- \[ \][[:space:]]*/  - /' | head -10)

# --- Block: exit 2 + stderr → Claude가 계속 작업 ---
{
  echo "[완료 엔진] 평가 작업판에 미완료 항목이 ${INCOMPLETE}개 남았습니다. 멈추지 말고 계속 진행하세요."
  echo ""
  echo "미완료 항목:"
  echo "${PENDING}"
  echo ""
  echo "각 항목을 끝내면 ${PLAN} 의 해당 체크박스를 [x]로 바꾸세요."
  echo "외부 자료 대기 등으로 정말 더 진행할 수 없으면, 막힌 항목을 [~]로 바꾸고 사유를 적으세요(미완료에서 제외됩니다)."
} >&2
exit 2
