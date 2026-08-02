#!/usr/bin/env bash
#
# Claude·Codex 이중 매니페스트의 정체성(이름·버전)이 어긋나지 않았는지 검사한다.
#
#   scripts/check-manifest-sync.sh
#
# 왜 필요한가: 이 저장소는 같은 플러그인을 4개 매니페스트(.claude-plugin/plugin.json,
# .codex-plugin/plugin.json, 두 마켓플레이스)로 배포한다. 버전·이름 동기화가 규율에만
# 의존하면 언젠가 드리프트한다 — mirror-sync가 문서 미러를 지키듯 이 검사가
# 매니페스트 정체성을 지킨다. CHANGELOG에 현재 버전 항목이 있는지도 본다.

set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 1

FAILURES=0

annotate() {
  local level=$1 message=$2
  if [ -n "${GITHUB_ACTIONS:-}" ]; then
    printf '::%s::%s\n' "$level" "$message"
  else
    printf '  [%s] %s\n' "$level" "$message"
  fi
}

jget() { # jget <file> <python-expr on obj>
  python3 - "$1" "$2" <<'EOF'
import json, sys
obj = json.load(open(sys.argv[1], encoding="utf-8"))
print(eval(sys.argv[2], {"obj": obj}))
EOF
}

echo "매니페스트 정체성 검사 — 이름·버전이 4개 매니페스트에서 일치하는가"
echo

CL_NAME=$(jget .claude-plugin/plugin.json 'obj["name"]') || exit 1
CL_VER=$(jget .claude-plugin/plugin.json 'obj["version"]') || exit 1
CX_NAME=$(jget .codex-plugin/plugin.json 'obj["name"]') || exit 1
CX_VER=$(jget .codex-plugin/plugin.json 'obj["version"]') || exit 1

echo "  .claude-plugin/plugin.json : $CL_NAME $CL_VER"
echo "  .codex-plugin/plugin.json  : $CX_NAME $CX_VER"

if [ "$CL_NAME" != "$CX_NAME" ]; then
  annotate error "플러그인 이름 불일치: Claude '$CL_NAME' vs Codex '$CX_NAME'"
  FAILURES=$((FAILURES + 1))
fi
if [ "$CL_VER" != "$CX_VER" ]; then
  annotate error "플러그인 버전 불일치: Claude '$CL_VER' vs Codex '$CX_VER'"
  FAILURES=$((FAILURES + 1))
fi

MP_CL=$(jget .claude-plugin/marketplace.json 'obj["plugins"][0]["name"]') || exit 1
if [ "$MP_CL" != "$CL_NAME" ]; then
  annotate error "Claude 마켓플레이스 플러그인 이름 불일치: '$MP_CL' (매니페스트는 '$CL_NAME')"
  FAILURES=$((FAILURES + 1))
fi
if [ -f .agents/plugins/marketplace.json ]; then
  MP_CX=$(jget .agents/plugins/marketplace.json 'obj["plugins"][0]["name"]') || exit 1
  if [ "$MP_CX" != "$CX_NAME" ]; then
    annotate error "Codex 마켓플레이스 플러그인 이름 불일치: '$MP_CX' (매니페스트는 '$CX_NAME')"
    FAILURES=$((FAILURES + 1))
  fi
fi

if ! grep -q "^## \[$CL_VER\]" CHANGELOG.md; then
  annotate error "CHANGELOG.md에 현재 버전 [$CL_VER] 항목이 없다"
  FAILURES=$((FAILURES + 1))
fi

echo
if [ "$FAILURES" -eq 0 ]; then
  echo "매니페스트 정체성 일치."
  exit 0
fi
echo "불일치 ${FAILURES}건 — 4개 매니페스트와 CHANGELOG의 이름·버전을 함께 갱신하라."
exit 1
