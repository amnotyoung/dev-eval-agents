#!/usr/bin/env bash
# hooks/boulder.sh (완료 엔진 Stop hook) 동작 테스트.
#
# 실행:  bash tests/test_boulder.sh
# 종료 코드 계약: 0 = 종료 허용 / 2 = 차단(계속 작업).
# 일시정지 의미론: 정체 3회·시도 20회 초과 시 작업판 지문을 남기고 종료 허용,
# 작업판이 편집되기 전까지 다시 차단하지 않는다.

set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK="$ROOT/hooks/boulder.sh"
TMP="$(mktemp -d)"
trap 'chmod -R u+w "$TMP" 2>/dev/null; rm -rf "$TMP"' EXIT

PASS=0; FAIL=0
check() { # check <설명> <기대코드> <실제코드>
  if [ "$2" = "$3" ]; then
    PASS=$((PASS + 1)); echo "ok  - $1"
  else
    FAIL=$((FAIL + 1)); echo "FAIL - $1 (기대 $2, 실제 $3)"
  fi
}
skip() { echo "skip - $1"; }
# BSD sed는 -i에 접미사 인자를 요구하고 GNU sed는 받지 않는다 (CI는 Linux, 개발은 macOS)
sed_i() {
  if sed --version >/dev/null 2>&1; then sed -i "$@"; else sed -i '' "$@"; fi
}
run_hook() { # run_hook <프로젝트폴더> → 종료코드를 표준출력
  CLAUDE_PROJECT_DIR="$1" bash "$HOOK" >/dev/null 2>&1
  echo $?
}

# 1) 작업판 없음 → 평가 모드 아님, 종료 허용
D="$TMP/no-plan"; mkdir -p "$D"
check "작업판 없으면 종료 허용" 0 "$(run_hook "$D")"

# 2) 전부 [x]/[~] → 완료, 종료 허용 + 상태 리셋
D="$TMP/done"; mkdir -p "$D/.omo"
printf -- '- [x] 적절성\n- [~] 타당성 (CTS 아님)\n' > "$D/.omo/eval-plan.md"
touch "$D/.omo/.boulder-state"
check "전부 완료/막힘이면 종료 허용" 0 "$(run_hook "$D")"
[ ! -f "$D/.omo/.boulder-state" ]; check "완료 시 상태 파일 제거" 0 $?

# 3) 미완료 → 차단(exit 2) + 안내 메시지
D="$TMP/incomplete"; mkdir -p "$D/.omo"
printf -- '- [ ] 적절성\n- [ ] 효과성\n' > "$D/.omo/eval-plan.md"
check "미완료면 차단" 2 "$(run_hook "$D")"
MSG=$(CLAUDE_PROJECT_DIR="$D" bash "$HOOK" 2>&1 >/dev/null; true)
case "$MSG" in *"미완료 항목"*) check "차단 메시지에 미완료 안내 포함" 0 0 ;; *) check "차단 메시지에 미완료 안내 포함" 0 1 ;; esac

# 4) 정체 3회 → 일시정지(종료 허용), 방치 시 재차단 없음, 편집 시 재무장
D="$TMP/stall"; mkdir -p "$D/.omo"
printf -- '- [ ] 적절성\n- [ ] 효과성\n' > "$D/.omo/eval-plan.md"
c1=$(run_hook "$D"); c2=$(run_hook "$D"); c3=$(run_hook "$D"); c4=$(run_hook "$D")
check "정체 1~3회차는 차단" 2 "$c1"
check "정체 누적 중에도 차단" 2 "$c3"
check "정체 3회면 일시정지(종료 허용)" 0 "$c4"
check "방치된 작업판은 다시 조르지 않음" 0 "$(run_hook "$D")"
grep -q '^paused ' "$D/.omo/.boulder-state"; check "상태 파일에 paused 기록" 0 $?
printf -- '- [x] 적절성\n- [ ] 효과성\n' > "$D/.omo/eval-plan.md"   # 편집 = 재개 의사
check "작업판 편집 시 재무장·차단 재개" 2 "$(run_hook "$D")"

# 5) 진전이 있으면 정체 리셋 — 4회 연속 호출해도 매번 진전이면 계속 차단
D="$TMP/progress"; mkdir -p "$D/.omo"
printf -- '- [ ] a\n- [ ] b\n- [ ] c\n- [ ] d\n- [ ] e\n' > "$D/.omo/eval-plan.md"
codes=""
for i in 1 2 3 4; do
  codes="$codes $(run_hook "$D")"
  sed_i "${i}s/\[ \]/[x]/" "$D/.omo/eval-plan.md"   # 진전 시뮬레이션: 항목 하나 완료
done
check "진전이 계속되면 정체 없이 차단 유지" " 2 2 2 2" "$codes"

# 6) 시도 상한: 진전이 있어도 총 20회 초과면 일시정지
D="$TMP/cap"; mkdir -p "$D/.omo"
: > "$D/.omo/eval-plan.md"
for i in $(seq 1 30); do printf -- '- [ ] 항목%s\n' "$i" >> "$D/.omo/eval-plan.md"; done
last=""; capped_at=""
for i in $(seq 1 21); do
  last=$(run_hook "$D")
  [ "$last" = "0" ] && { capped_at=$i; break; }
  sed_i "${i}s/\[ \]/[x]/" "$D/.omo/eval-plan.md"
done
check "21회차에 시도 상한 일시정지" "21" "${capped_at:-none}"
check "상한 도달 시 종료 허용" 0 "$last"

# 7) 읽기전용 상태 디렉토리 → fail-open 종료 허용
# root는 퍼미션을 무시하므로(-w가 참) 이 케이스를 재현할 수 없다 — 건너뛴다.
if [ "$(id -u)" = "0" ]; then
  skip "상태 저장 불가면 종료 허용(fail-open) — root라 읽기전용 재현 불가"
else
  D="$TMP/readonly"; mkdir -p "$D/.omo"
  printf -- '- [ ] 적절성\n' > "$D/.omo/eval-plan.md"
  chmod 555 "$D/.omo"
  check "상태 저장 불가면 종료 허용(fail-open)" 0 "$(run_hook "$D")"
  chmod 755 "$D/.omo"
fi

echo
echo "통과 $PASS / 실패 $FAIL"
[ "$FAIL" -eq 0 ]
