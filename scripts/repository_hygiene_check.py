#!/usr/bin/env python3
"""추적 예정 파일의 중복 사본과 플러그인 정본 ID 충돌을 검사한다.

파일시스템 전체를 훑지 않는다. Git이 추적하거나 추적할 예정이면서 ignore되지
않은 파일만 검사해 ``.local/`` 자료, 로컬 worktree, ``.DS_Store`` 같은 개발자별
파일이 CI 결과에 섞이지 않게 한다.

종료 코드:
  0 = 통과
  1 = Git/파일 읽기 오류
  2 = 저장소 위생 계약 위반
"""

from __future__ import annotations

import argparse
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import unicodedata
from collections import defaultdict
from collections.abc import Iterable, Sequence


ROOT = Path(__file__).resolve().parent.parent
COPY_ALLOWLIST = ".repository-hygiene-allow"

# 운영체제·동기화 도구가 만드는 전형적인 사본 접미사. 숫자 제목의 오탐을
# 피하려고 이 패턴만으로 실패시키지 않고, 접미사를 뺀 sibling이 실제로 있을
# 때만 사본 충돌로 판정한다.
COPY_COMPONENT_RE = re.compile(
    r"^(?P<base>.+?)(?: - | )"
    r"(?P<marker>(?:[2-9]|[1-9][0-9]+)|copy(?: [0-9]+)?|복사본(?: [0-9]+)?|\([1-9][0-9]*\))"
    r"(?P<extensions>(?:\.[^./]+)*)$",
    re.IGNORECASE,
)
CANONICAL_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NAME_LINE_RE = re.compile(r"^name:\s*(.*?)\s*$")


class InventoryError(RuntimeError):
    """Git 인벤토리를 만들지 못했을 때 발생한다."""


@dataclass(frozen=True, order=True)
class Issue:
    """결정적으로 정렬·출력할 수 있는 단일 위반."""

    code: str
    path: str
    message: str


@dataclass(frozen=True)
class CanonicalEntry:
    path: str
    declared_name: str
    expected_name: str
    body: str


def _sort_key(path: str) -> tuple[str, str]:
    normalized = unicodedata.normalize("NFC", path).casefold()
    return normalized, path


def git_inventory(root: Path) -> list[str]:
    """Git 추적 파일과 ignore되지 않은 미추적 파일을 NUL 안전하게 반환한다."""

    try:
        result = subprocess.run(
            [
                "git",
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
                "--",
            ],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", b"")
        if isinstance(detail, bytes):
            detail = detail.decode("utf-8", errors="replace")
        message = str(detail).strip() or str(exc)
        raise InventoryError(f"Git 파일 인벤토리를 만들 수 없다: {message}") from exc

    paths: set[str] = set()
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        path = raw_path.decode("utf-8", errors="surrogateescape")
        absolute = root / PurePosixPath(path)
        # 삭제 중인 tracked 파일은 현재 작업트리 계약의 대상이 아니다. 심볼릭
        # 링크는 깨져 있어도 Git 엔트리로 남아 있으면 경로 충돌 검사에 포함한다.
        if absolute.exists() or absolute.is_symlink():
            paths.add(PurePosixPath(path).as_posix())
    return sorted(paths, key=_sort_key)


def _all_nodes(paths: Iterable[str]) -> set[str]:
    """파일과 그 상위 디렉터리의 POSIX 경로 집합을 만든다."""

    nodes: set[str] = set()
    for path in paths:
        parts = PurePosixPath(path).parts
        for end in range(1, len(parts) + 1):
            nodes.add(PurePosixPath(*parts[:end]).as_posix())
    return nodes


def _portable_key(path: str) -> str:
    return "/".join(
        unicodedata.normalize("NFC", part).casefold()
        for part in PurePosixPath(path).parts
    )


def _copy_collisions(
    paths: Sequence[str], allowed_copy_paths: Iterable[str] = ()
) -> list[Issue]:
    nodes = _all_nodes(paths)
    nodes_by_portable_key: dict[str, set[str]] = defaultdict(set)
    for node in nodes:
        nodes_by_portable_key[_portable_key(node)].add(node)
    allowed_keys = {_portable_key(path) for path in allowed_copy_paths}
    # 복제 디렉터리 안 파일이 여러 개여도 같은 디렉터리 사고는 한 번만 보고한다.
    collisions: dict[tuple[str, str], str] = {}

    for path in paths:
        parts = PurePosixPath(path).parts
        for index, component in enumerate(parts):
            match = COPY_COMPONENT_RE.fullmatch(component)
            if not match:
                continue
            canonical_component = match.group("base") + match.group("extensions")
            copied_prefix = PurePosixPath(*parts[: index + 1]).as_posix()
            canonical_prefix = PurePosixPath(
                *parts[:index], canonical_component
            ).as_posix()
            if _portable_key(copied_prefix) in allowed_keys:
                continue
            canonical_matches = nodes_by_portable_key.get(
                _portable_key(canonical_prefix), set()
            )
            if canonical_matches:
                canonical = sorted(canonical_matches, key=_sort_key)[0]
                collisions.setdefault((copied_prefix, canonical), path)

    return [
        Issue(
            "copy-suffix-collision",
            witness,
            f"사본형 경로 '{copied}'가 정본형 sibling '{canonical}'와 충돌한다.",
        )
        for (copied, canonical), witness in sorted(collisions.items())
    ]


def _portable_collisions(paths: Sequence[str]) -> list[Issue]:
    groups: dict[str, set[str]] = defaultdict(set)
    for node in _all_nodes(paths):
        groups[_portable_key(node)].add(node)

    issues: list[Issue] = []
    for members in groups.values():
        if len(members) < 2:
            continue
        ordered = sorted(members, key=_sort_key)
        issues.append(
            Issue(
                "portable-path-collision",
                ordered[0],
                "NFC·대소문자 정규화 후 같은 경로가 된다: " + ", ".join(ordered),
            )
        )
    return issues


def _frontmatter(
    text: str, *, allow_reference_preamble: bool = False
) -> tuple[str | None, str | None]:
    """(name, body)를 반환한다. 형식이 잘못됐으면 (None, None)이다."""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    if not lines:
        return None, None

    # 실행 정본은 첫 줄부터 frontmatter여야 한다. docs/en/agents 번역 미러만
    # 정본을 가리키는 blockquote/빈줄 preamble을 첫 8줄 안에서 허용한다.
    if allow_reference_preamble:
        start = None
        for index, line in enumerate(lines[:8]):
            if line.lstrip("\ufeff") == "---":
                start = index
                break
            if line and not line.lstrip("\ufeff").startswith(">"):
                return None, None
        if start is None:
            return None, None
    else:
        if lines[0].lstrip("\ufeff") != "---":
            return None, None
        start = 0

    try:
        end = lines.index("---", start + 1)
    except ValueError:
        return None, None

    names: list[str] = []
    for line in lines[start + 1 : end]:
        match = NAME_LINE_RE.fullmatch(line)
        if match:
            value = match.group(1).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            names.append(value)
    if len(names) != 1:
        return None, None

    body = "\n".join(lines[end + 1 :]).rstrip("\n")
    return names[0], body


def _canonical_specs(path: str) -> tuple[str, str] | None:
    """(registry, expected_name)을 반환한다."""

    parts = PurePosixPath(path).parts
    if len(parts) == 2 and parts[0] == "agents" and parts[1].endswith(".md"):
        return "agents", PurePosixPath(parts[1]).stem
    if (
        len(parts) == 4
        and parts[:3] == ("docs", "en", "agents")
        and parts[3].endswith(".md")
    ):
        # 영문 미러는 정본과 같은 ID를 갖지만 별도 registry로 검사한다.
        return "docs/en/agents", PurePosixPath(parts[3]).stem
    if len(parts) == 3 and parts[0] == "skills" and parts[2] == "SKILL.md":
        return "skills", parts[1]
    return None


def _semantic_id(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = re.sub(r"[\s_]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-")


def _canonical_entries(root: Path, paths: Sequence[str]) -> tuple[list[CanonicalEntry], list[Issue]]:
    entries: list[CanonicalEntry] = []
    issues: list[Issue] = []

    skill_dirs = {
        PurePosixPath(path).parts[1]
        for path in paths
        if len(PurePosixPath(path).parts) >= 3
        and PurePosixPath(path).parts[0] == "skills"
    }
    path_set = set(paths)
    for skill_dir in sorted(skill_dirs, key=_sort_key):
        entrypoint = f"skills/{skill_dir}/SKILL.md"
        if entrypoint not in path_set:
            issues.append(
                Issue(
                    "missing-skill-entrypoint",
                    f"skills/{skill_dir}",
                    f"스킬 디렉터리에 정본 진입점이 없다: {entrypoint}",
                )
            )

    for path in paths:
        spec = _canonical_specs(path)
        if spec is None:
            continue
        registry, expected_name = spec
        try:
            text = (root / PurePosixPath(path)).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            issues.append(
                Issue(
                    "unreadable-canonical-file",
                    path,
                    f"정본 UTF-8 파일을 읽을 수 없다: {exc}",
                )
            )
            continue

        declared_name, body = _frontmatter(
            text, allow_reference_preamble=registry == "docs/en/agents"
        )
        if declared_name is None or body is None:
            issues.append(
                Issue(
                    "invalid-frontmatter-name",
                    path,
                    "YAML frontmatter에 단 하나의 평문 name 필드가 있어야 한다.",
                )
            )
            continue

        if not CANONICAL_ID_RE.fullmatch(declared_name):
            issues.append(
                Issue(
                    "invalid-canonical-id",
                    path,
                    f"정본 ID '{declared_name}'는 소문자 kebab-case여야 한다.",
                )
            )
        if declared_name != expected_name:
            issues.append(
                Issue(
                    "canonical-id-path-mismatch",
                    path,
                    f"frontmatter name '{declared_name}'가 경로 ID '{expected_name}'와 다르다.",
                )
            )
        entries.append(CanonicalEntry(path, declared_name, expected_name, body))

    return entries, issues


def _canonical_collisions(entries: Sequence[CanonicalEntry]) -> list[Issue]:
    by_registry: dict[str, list[CanonicalEntry]] = defaultdict(list)
    for entry in entries:
        spec = _canonical_specs(entry.path)
        if spec is not None:
            by_registry[spec[0]].append(entry)

    issues: list[Issue] = []
    for registry, registry_entries in sorted(by_registry.items()):
        id_groups: dict[str, list[CanonicalEntry]] = defaultdict(list)
        body_groups: dict[str, list[CanonicalEntry]] = defaultdict(list)
        for entry in registry_entries:
            id_groups[_semantic_id(entry.declared_name)].append(entry)
            digest = hashlib.sha256(entry.body.encode("utf-8")).hexdigest()
            body_groups[digest].append(entry)

        for entries_with_id in id_groups.values():
            if len(entries_with_id) < 2:
                continue
            ordered = sorted(entries_with_id, key=lambda entry: _sort_key(entry.path))
            paths = [entry.path for entry in ordered]
            issues.append(
                Issue(
                    "duplicate-canonical-id",
                    paths[0],
                    f"{registry} registry에서 정규화 ID가 중복된다: " + ", ".join(paths),
                )
            )

        for entries_with_body in body_groups.values():
            if len(entries_with_body) < 2:
                continue
            ordered = sorted(entries_with_body, key=lambda entry: _sort_key(entry.path))
            paths = [entry.path for entry in ordered]
            issues.append(
                Issue(
                    "duplicate-canonical-body",
                    paths[0],
                    f"{registry} registry에서 frontmatter를 제외한 본문이 같다: "
                    + ", ".join(paths),
                )
            )
    return issues


def inspect(
    root: Path,
    paths: Sequence[str],
    allowed_copy_paths: Iterable[str] = (),
) -> list[Issue]:
    """주어진 저장소 상대경로들을 검사한다. 테스트에서 순수하게 재사용한다."""

    normalized_paths = sorted(
        {PurePosixPath(path).as_posix() for path in paths}, key=_sort_key
    )
    entries, entry_issues = _canonical_entries(root, normalized_paths)
    issues = [
        *_copy_collisions(normalized_paths, allowed_copy_paths),
        *_portable_collisions(normalized_paths),
        *entry_issues,
        *_canonical_collisions(entries),
    ]
    return sorted(set(issues))


def load_copy_allowlist(root: Path) -> set[str]:
    """검토 가능한 exact-path 사본 예외 목록을 읽는다."""

    path = root / COPY_ALLOWLIST
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return set()
    except (OSError, UnicodeError) as exc:
        raise InventoryError(f"{COPY_ALLOWLIST}를 읽을 수 없다: {exc}") from exc

    allowed: set[str] = set()
    for line_number, raw_line in enumerate(lines, 1):
        value = raw_line.strip()
        if not value or value.startswith("#"):
            continue
        candidate = PurePosixPath(value)
        if candidate.is_absolute() or ".." in candidate.parts or candidate.as_posix() in ("", "."):
            raise InventoryError(
                f"{COPY_ALLOWLIST}:{line_number}은 저장소 상대경로여야 한다: {value}"
            )
        allowed.add(candidate.as_posix())
    return allowed


def _gha_property(value: str) -> str:
    return (
        value.replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
        .replace(":", "%3A")
        .replace(",", "%2C")
    )


def _gha_message(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def report(issues: Sequence[Issue]) -> None:
    github_actions = bool(os.environ.get("GITHUB_ACTIONS"))
    for issue in issues:
        message = f"[{issue.code}] {issue.message}"
        if github_actions:
            print(
                f"::error file={_gha_property(issue.path)}::{_gha_message(message)}",
                file=sys.stderr,
            )
        else:
            print(f"ERROR [{issue.code}] {issue.path}: {issue.message}", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="검사할 Git 저장소 루트(기본: 이 스크립트의 상위 저장소)",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()

    try:
        paths = git_inventory(root)
        allowed_copy_paths = load_copy_allowlist(root)
    except InventoryError as exc:
        print(f"repository hygiene check 오류: {exc}", file=sys.stderr)
        return 1

    issues = inspect(root, paths, allowed_copy_paths)
    if issues:
        report(issues)
        print(f"저장소 위생 계약 위반 {len(issues)}건.", file=sys.stderr)
        return 2

    print(f"저장소 위생 검사 통과 — Git 대상 파일 {len(paths)}개, 충돌 0건.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
