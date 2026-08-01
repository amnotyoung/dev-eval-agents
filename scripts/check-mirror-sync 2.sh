#!/usr/bin/env bash
#
# 정본(한국어 실행본)과 docs/en 미러가 함께 갱신되는지 검사한다.
#
#   scripts/check-mirror-sync.sh [base-ref]   PR 모드 — base와의 변경분만 본다 (기본 origin/main)
#   scripts/check-mirror-sync.sh --audit      감사 모드 — 저장소 전체의 미러 최신성을 본다
#
# 왜 필요한가: CONTRIBUTING의 규칙대로 한국어 파일이 실행 정본이고 영문은
# docs/en/ 미러다. 정본만 고치고 미러를 두면 미러가 조용히 낡는다 —
# docs/en/CLAUDE.md가 실제로 한 달간 옛 판에 머물렀다.
#
# 번역의 정확성은 검사하지 않는다. "같이 갱신했는가"만 본다.

set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 1

MIRROR_PREFIX="docs/en/"
# 미러를 두는 정본 — 루트 파일과 디렉터리
MIRRORED_FILES=("CLAUDE.md" "AGENTS.md")
MIRRORED_DIRS=("agents" "reference")
# 한 쌍이지만 한쪽만 고치는 일이 정상인 문서 — 실패가 아니라 경고
SOFT_PAIR_A="README.md"
SOFT_PAIR_B="README.ko.md"

# 한글 파일명이 \354... 로 이스케이프되면 경로 비교가 깨진다
git() { command git -c core.quotepath=false "$@"; }

is_mirrored() { # 경로가 미러를 둬야 하는 정본인가
  local path=$1 f d
  for f in "${MIRRORED_FILES[@]}"; do
    [ "$path" = "$f" ] && return 0
  done
  for d in "${MIRRORED_DIRS[@]}"; do
    case "$path" in "$d"/*.md) return 0 ;; esac
  done
  return 1
}

annotate() { # GitHub Actions 주석 (로컬에서는 평문)
  local level=$1 message=$2
  if [ -n "${GITHUB_ACTIONS:-}" ]; then
    printf '::%s::%s\n' "$level" "$message"
  else
    printf '  [%s] %s\n' "$level" "$message"
  fi
}

audit_mode() {
  local failures=0 canonical mirror c_time m_time
  echo "미러 감사 — 정본이 미러보다 나중에 바뀐 쌍을 찾는다"
  echo

  while IFS= read -r canonical; do
    is_mirrored "$canonical" || continue
    mirror="${MIRROR_PREFIX}${canonical}"

    if [ ! -f "$mirror" ]; then
      annotate error "미러 없음: $canonical → $mirror"
      failures=$((failures + 1))
      continue
    fi

    c_time=$(git log -1 --format=%ct -- "$canonical")
    m_time=$(git log -1 --format=%ct -- "$mirror")
    if [ -n "$c_time" ] && [ -n "$m_time" ] && [ "$c_time" -gt "$m_time" ]; then
      annotate error "미러가 낡음: $mirror (정본 $canonical 이 더 최신)"
      failures=$((failures + 1))
    fi
  done < <(git ls-files)

  if [ "$failures" -eq 0 ]; then
    echo "모든 미러가 정본과 같거나 더 최신이다."
    return 0
  fi
  echo
  echo "낡은 미러 ${failures}건. 정본을 다시 읽고 docs/en 쪽을 갱신하라."
  return 1
}

pr_mode() {
  local base=$1 base_sha changed failures=0 canonical mirror
  base_sha=$(git merge-base "$base" HEAD 2>/dev/null)
  if [ -z "$base_sha" ]; then
    echo "base ref를 해석할 수 없다: $base" >&2
    return 2
  fi

  changed=$(git diff --name-only "$base_sha" HEAD)
  if [ -z "$changed" ]; then
    echo "변경된 파일이 없다."
    return 0
  fi

  echo "base $(git rev-parse --short "$base_sha") 와 비교 — 변경 $(printf '%s\n' "$changed" | wc -l | tr -d ' ')건"
  echo

  while IFS= read -r canonical; do
    [ -z "$canonical" ] && continue
    is_mirrored "$canonical" || continue
    mirror="${MIRROR_PREFIX}${canonical}"

    if printf '%s\n' "$changed" | grep -qxF "$mirror"; then
      echo "  OK    $canonical → $mirror 같이 갱신됨"
    else
      annotate error "$canonical 이 바뀌었는데 $mirror 는 그대로다. 같은 PR에서 미러도 갱신하라."
      failures=$((failures + 1))
    fi
  done < <(printf '%s\n' "$changed")

  # README 쌍은 한쪽만 고치는 일이 정상이라 경고만 한다
  local a_changed=no b_changed=no
  printf '%s\n' "$changed" | grep -qxF "$SOFT_PAIR_A" && a_changed=yes
  printf '%s\n' "$changed" | grep -qxF "$SOFT_PAIR_B" && b_changed=yes
  if [ "$a_changed" != "$b_changed" ]; then
    annotate warning "$SOFT_PAIR_A 와 $SOFT_PAIR_B 중 한쪽만 바뀌었다. 의도한 것이면 그대로 두라."
  fi

  echo
  if [ "$failures" -eq 0 ]; then
    echo "정본과 미러가 함께 갱신되었다."
    return 0
  fi
  echo "미러가 빠진 정본 ${failures}건."
  echo "의도적으로 한쪽만 바꾸는 PR이면 'mirror-sync-exempt' 라벨을 붙이면 이 검사를 건너뛴다."
  return 1
}

case "${1:---pr}" in
  --audit) audit_mode ;;
  --pr) pr_mode "origin/main" ;;
  -h | --help)
    sed -n '3,12p' "$0"
    ;;
  *) pr_mode "$1" ;;
esac
