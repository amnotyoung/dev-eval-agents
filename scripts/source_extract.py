#!/usr/bin/env python3
"""source_extract.py — 평가 원문(PDF·HWP·HWPX·DOCX·XLSX)을 쪽 표지가 있는 텍스트로 바꾼다.

평가관·검증자 에이전트는 Read·Grep·Glob만 쓰므로 PDF·HWP를 직접 검색하지 못한다.
평가총괄(스킬)이 위임 전에 이 스크립트로 원문을 사용자 작업 폴더의 `.omo/sources/`에
변환하고, 에이전트에게는 변환본의 절대경로를 넘긴다.

변환기 순서 (`--engine auto`):
  1. kordoc — 한국 공문서(HWP·HWPX)와 PDF 표를 복원한다. PATH의 `kordoc`이 있으면 그것을,
     없으면 `npx --yes kordoc@<고정 버전>`을 쓴다(Node 20 이상). 버전을 고정하는 이유:
     kordoc은 하루에도 여러 번 릴리스되므로 `@latest`면 같은 원문이 세션마다 다른 변환기로
     읽힌다. 감사추적에는 변환기 버전이 남아야 한다. `DEVEVAL_KORDOC_VERSION`으로 바꿀 수 있다.
  2. pdftotext -layout — PDF 전용 폴백(표 복원은 약하다).
  3. 둘 다 안 되면 그 파일은 변환 불가(exit 3) — 스킬이 다른 경로(kordoc MCP, 사람에게
     텍스트 요청)를 안내한다.
  `.md`·`.txt`는 변환 없이 UTF-8로 옮기고 같은 머리글만 붙인다.

산출물:
  <out-dir>/<원본 이름>.md  — 머리 주석에 원본 절대경로·SHA-256·변환기·버전·쪽 표지 방식·경고,
                              본문에 실제 쪽마다 `<!-- p.N -->` 표지(원문 위치 인용용)
  <out-dir>/index.md        — 변환본 목록(원본 ↔ 변환본 ↔ 변환기 ↔ 경고)
같은 원본(SHA-256)·같은 변환기 설정의 변환본이 이미 있으면 다시 변환하지 않는다(`--force`로 강제).

변환은 이 컴퓨터 안에서만 한다. kordoc의 웹훅 같은 전송 기능은 쓰지 않는다. 단, npx 경로는
처음 한 번 npm 레지스트리에서 kordoc 패키지를 내려받는다.

사용법:
    python3 scripts/source_extract.py <원문…> [--out-dir .omo/sources] [--engine auto|kordoc|pdftotext]
                                      [--ocr] [--force]
종료 코드: 0 = 모두 변환 / 3 = 하나 이상 변환 불가(통과 아님 — 메시지의 대안 경로를 따른다).
표준 라이브러리만 사용.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KORDOC_VERSION = os.environ.get("DEVEVAL_KORDOC_VERSION", "4.24.1")
KORDOC_TIMEOUT = int(os.environ.get("DEVEVAL_KORDOC_TIMEOUT", "1800"))
KORDOC_EXT = {".pdf", ".hwp", ".hwpx", ".hml", ".docx", ".xlsx"}
TEXT_EXT = {".md", ".markdown", ".txt"}
HEADER_START = "<!-- deveval-source"
IMAGE_LINE = re.compile(r"^\s*!\[[^\]]*\]\([^)]*\)\s*$")


class Unavailable(Exception):
    """이 변환기를 쓸 수 없거나 변환에 실패했다."""


# ---------- 공통 ----------

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "cp949"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise Unavailable("텍스트 원문을 UTF-8·CP949로 읽을 수 없음")


def pages_to_markdown(pages: list[tuple[int, str]]) -> str:
    return "\n\n".join(f"<!-- p.{number} -->\n{body.strip()}" for number, body in pages) + "\n"


def summarize_pages(numbers: list[int], limit: int = 12) -> str:
    """'p.41, 47, 84' 또는 'p.41, … 129 외 3개 쪽'."""
    shown = "p." + ", ".join(str(n) for n in numbers[:limit])
    return shown + (f" 외 {len(numbers) - limit}개 쪽" if len(numbers) > limit else "")


def read_header(path: Path) -> dict[str, str]:
    """변환본 머리 주석의 `키: 값` 줄을 읽는다."""
    try:
        head = path.read_text(encoding="utf-8")[:4000]
    except (OSError, UnicodeDecodeError):
        return {}
    if not head.startswith(HEADER_START):
        return {}
    block = head.split("-->", 1)[0]
    fields = {}
    for line in block.splitlines()[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


# ---------- 변환기 ----------

def node_major() -> int | None:
    node = shutil.which("node")
    if not node:
        return None
    try:
        out = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.match(r"v?(\d+)", out.strip())
    return int(match.group(1)) if match else None


def kordoc_command() -> tuple[list[str], str]:
    """(실행 명령, 버전 표기). PATH의 kordoc을 먼저, 없으면 고정 버전 npx."""
    local = shutil.which("kordoc")
    if local:
        try:
            out = subprocess.run([local, "--version"], capture_output=True, text=True, timeout=120)
            version = out.stdout.strip().splitlines()[-1] if out.stdout.strip() else "버전 미상"
        except (OSError, subprocess.SubprocessError):
            version = "버전 미상"
        return [local], f"{version} (PATH)"
    npx = shutil.which("npx")
    if not npx:
        raise Unavailable("kordoc 없음 — PATH에 kordoc도 npx도 없음(Node 20 이상 필요)")
    major = node_major()
    if major is None or major < 20:
        raise Unavailable(f"kordoc {KORDOC_VERSION}은 Node 20 이상 필요 — 현재 Node {major or '없음'}")
    return [npx, "--yes", f"kordoc@{KORDOC_VERSION}"], f"{KORDOC_VERSION} (npx 고정)"


def run_kordoc(src: Path, ocr: bool) -> dict:
    command, version = kordoc_command()
    with tempfile.TemporaryDirectory(prefix="deveval-kordoc-") as tmp:
        out = Path(tmp) / "out.json"
        args = command + [str(src), "--format", "json", "--table-format", "gfm", "--no-images",
                          "-o", str(out), "--silent"]
        if ocr:
            args.append("--ocr")
        try:
            proc = subprocess.run(args, capture_output=True, text=True, timeout=KORDOC_TIMEOUT, cwd=tmp)
        except subprocess.TimeoutExpired:
            raise Unavailable(f"kordoc 시간 초과({KORDOC_TIMEOUT}초)") from None
        except OSError as exc:
            raise Unavailable(f"kordoc 실행 실패: {exc}") from None
        if proc.returncode != 0 or not out.exists():
            detail = (proc.stderr or proc.stdout).strip().splitlines()[-1:] or ["출력 없음"]
            raise Unavailable(f"kordoc 실패(exit {proc.returncode}): {detail[0][:300]}")
        try:
            data = json.loads(out.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise Unavailable(f"kordoc 결과를 읽을 수 없음: {exc}") from None
    if not isinstance(data, dict):
        raise Unavailable("kordoc 결과가 JSON 객체가 아님")
    if not data.get("success", True):
        raise Unavailable(f"kordoc 파싱 실패: {data.get('error') or data.get('code') or '사유 미상'}")
    try:
        doc = kordoc_document(data, version)
    except (TypeError, ValueError, KeyError, AttributeError) as exc:
        raise Unavailable(f"kordoc 쪽 구조를 읽을 수 없음: {exc}") from None
    doc["signature"] = kordoc_signature(version, ocr)
    return doc


def kordoc_document(data: dict, version: str) -> dict:
    """kordoc JSON(pages·warnings·qualitySummary)을 쪽 표지 마크다운과 경고 목록으로 바꾼다."""
    pages = [(int(p["pageNumber"]), p.get("markdown") or "") for p in data.get("pages") or []]
    page_mode = (data.get("metadata") or {}).get("pageMode") or "미상"
    if pages:
        body = pages_to_markdown(pages)
        marker = "실제 쪽" if page_mode == "layout" else f"섹션 근사({page_mode})"
    else:
        body = (data.get("markdown") or "").strip() + "\n"
        marker = "없음 — 쪽 정보를 주지 않는 형식"
    warnings = []
    by_code: dict[str, list[int]] = {}
    for item in data.get("warnings") or []:
        by_code.setdefault(item.get("code") or "WARN", []).append(item.get("page") or 0)
    for code, numbers in sorted(by_code.items()):
        numbers = sorted({n for n in numbers if n})
        where = f" — {summarize_pages(numbers)}" if numbers else ""
        warnings.append(f"{code} {len(numbers) or 1}건{where}")
    quality = data.get("qualitySummary") or {}
    if quality.get("needsOcr"):
        warnings.append("NEEDS_OCR — 텍스트층이 없거나 깨진 쪽이 있음: --ocr로 다시 변환하라")
    images = sum(1 for line in body.splitlines() if IMAGE_LINE.match(line))
    if images:
        warnings.append(f"그림 영역 {images}곳 — 표·도표가 그림이면 수치를 읽지 못했을 수 있음")
    return {"engine": f"kordoc {version} (json·gfm 표·이미지 제외)", "marker": marker,
            "body": body, "warnings": warnings, "pages": len(pages)}


def kordoc_signature(version: str, ocr: bool) -> str:
    return f"kordoc {version}|ocr={int(ocr)}"


def run_pdftotext(src: Path) -> dict:
    tool = shutil.which("pdftotext")
    if not tool:
        raise Unavailable("pdftotext 없음")
    try:
        version = subprocess.run([tool, "-v"], capture_output=True, text=True, timeout=30)
        version_text = (version.stderr or version.stdout).strip().splitlines()[0]
    except (OSError, subprocess.SubprocessError, IndexError):
        version_text = "pdftotext"
    try:
        proc = subprocess.run([tool, "-layout", "-enc", "UTF-8", "-q", str(src), "-"],
                              capture_output=True, timeout=600)
    except (OSError, subprocess.SubprocessError) as exc:
        raise Unavailable(f"pdftotext 실행 실패: {exc}") from None
    if proc.returncode != 0:
        raise Unavailable(f"pdftotext 실패(exit {proc.returncode})")
    text = proc.stdout.decode("utf-8", errors="replace")
    chunks = text.split("\f")
    if chunks and not chunks[-1].strip():
        chunks = chunks[:-1]
    pages = [(i, chunk) for i, chunk in enumerate(chunks, 1)]
    empty = [n for n, chunk in pages if not chunk.strip()]
    warnings = ["표 복원 없음 — pdftotext 배치 텍스트라 다단 표의 열이 섞일 수 있음"]
    if empty:
        warnings.append(f"텍스트 없는 쪽 {len(empty)}개 — {summarize_pages(empty)}(스캔·그림일 수 있음)")
    return {"engine": f"{version_text} (-layout)", "marker": "실제 쪽", "body": pages_to_markdown(pages),
            "warnings": warnings, "pages": len(pages), "signature": "pdftotext"}


def run_text(src: Path) -> dict:
    return {"engine": "텍스트 원문(변환 없음)", "marker": "없음 — 원문 줄 번호로 인용",
            "body": decode(src.read_bytes()), "warnings": [], "pages": 0, "signature": "text"}


# ---------- 실행 ----------

def wanted_signatures(ext: str, engine: str, ocr: bool) -> set[str]:
    """재사용해도 되는 기존 변환본의 '설정' 값. kordoc을 쓸 수 있으면 kordoc 결과만 인정한다 —
    kordoc 실패로 pdftotext에 폴백한 변환본은 kordoc이 다시 가능해지면 새로 만든다."""
    if ext in TEXT_EXT:
        return {"text"}
    if engine in ("auto", "kordoc"):
        try:
            _command, version = kordoc_command()
            return {kordoc_signature(version, ocr)}
        except Unavailable:
            pass
    return {"pdftotext"} if engine in ("auto", "pdftotext") and ext == ".pdf" else set()


def target_path(out_dir: Path, src: Path, digest: str) -> Path:
    # index.md is reserved for the generated inventory. Never overwrite an
    # unrelated user file, even when it has no provenance header.
    stem = f"{src.stem}-source" if src.stem.casefold() == "index" else src.stem
    path = out_dir / f"{stem}.md"
    counter = 0
    while path.exists() and read_header(path).get("원본") != str(src):
        suffix = f"-{counter}" if counter else ""
        path = out_dir / f"{stem}-{digest[:8]}{suffix}.md"
        counter += 1
    return path


def convert(src: Path, out_dir: Path, engine: str, ocr: bool, force: bool) -> tuple[Path, dict, bool]:
    ext = src.suffix.lower()
    digest = sha256(src)
    path = target_path(out_dir, src, digest)
    existing = read_header(path)
    if (not force and existing.get("SHA-256") == digest
            and existing.get("설정") in wanted_signatures(ext, engine, ocr)):
        return path, existing, True

    errors = []
    result = None
    if ext in TEXT_EXT:
        result = run_text(src)
    elif ext in KORDOC_EXT:
        attempts = []
        if engine in ("auto", "kordoc"):
            attempts.append(lambda: run_kordoc(src, ocr))
        if engine in ("auto", "pdftotext") and ext == ".pdf":
            attempts.append(lambda: run_pdftotext(src))
        for attempt in attempts:
            try:
                result = attempt()
                break
            except Unavailable as exc:
                errors.append(str(exc))
    else:
        errors.append(f"지원하지 않는 형식 {ext or '(확장자 없음)'}")
    if result is None:
        raise Unavailable("; ".join(errors) or "쓸 수 있는 변환기 없음")
    readable = re.sub(r"<!--.*?-->", "", result["body"], flags=re.DOTALL)
    readable = "\n".join(line for line in readable.splitlines() if not IMAGE_LINE.match(line))
    if not readable.strip():
        raise Unavailable("읽을 수 있는 본문 없음 — OCR 또는 텍스트 원문 필요")

    if errors:
        result["warnings"].insert(0, "앞선 변환기 실패 — " + "; ".join(errors))
    header = [
        HEADER_START,
        f"원본: {src}",
        f"SHA-256: {digest}",
        f"변환기: {result['engine']}",
        f"설정: {result['signature']}",
        f"쪽 표지: {result['marker']}",
        f"변환일: {_dt.date.today().isoformat()}",
        "경고: " + (" / ".join(result["warnings"]) if result["warnings"] else "없음"),
        "-->",
        "",
    ]
    path.write_text("\n".join(header) + result["body"], encoding="utf-8")
    return path, read_header(path), False


def write_index(out_dir: Path) -> Path:
    rows = []
    for path in sorted(out_dir.glob("*.md")):
        if path.name == "index.md":
            continue
        fields = read_header(path)
        if not fields:
            continue
        rows.append(f"| {fields.get('원본', '')} | {path} | {fields.get('변환기', '')} | "
                    f"{fields.get('쪽 표지', '')} | {fields.get('경고', '')} |")
    index = out_dir / "index.md"
    index.write_text(
        "# 원문 변환본 색인\n\n"
        "평가관에게는 원본이 아니라 이 변환본의 절대경로를 넘긴다. 원문 위치는 `<!-- p.N -->` 표지로 인용하고,"
        " 경고가 있는 쪽의 수치는 원본과 대조하기 전까지 `[INFO: 확인 필요]`로 둔다.\n\n"
        "| 원본 | 변환본 | 변환기 | 쪽 표지 | 경고 |\n|---|---|---|---|---|\n" + "\n".join(rows) + "\n",
        encoding="utf-8",
    )
    return index


class _ArgParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"[source_extract] 사용법 오류 — 변환하지 않음(exit 3): {message}", file=sys.stderr)
        sys.exit(3)


def main(argv=None) -> int:
    ap = _ArgParser(description="평가 원문을 쪽 표지가 있는 텍스트로 변환(kordoc → pdftotext)")
    ap.add_argument("sources", nargs="+", help="PDF·HWP·HWPX·DOCX·XLSX·MD·TXT 원문 경로")
    ap.add_argument("--out-dir", default=".omo/sources", help="변환본 폴더(기본: 작업 폴더의 .omo/sources)")
    ap.add_argument("--engine", choices=("auto", "kordoc", "pdftotext"), default="auto")
    ap.add_argument("--ocr", action="store_true", help="kordoc OCR로 스캔·그림 쪽까지 인식(첫 사용 시 모델 다운로드)")
    ap.add_argument("--force", action="store_true", help="같은 원본의 변환본이 있어도 다시 변환")
    args = ap.parse_args(argv)

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    failures = []
    for raw in args.sources:
        src = Path(raw).expanduser().resolve()
        if not src.is_file():
            failures.append((src, "파일 없음"))
            continue
        try:
            path, fields, cached = convert(src, out_dir, args.engine, args.ocr, args.force)
        except (Unavailable, OSError, UnicodeError) as exc:
            failures.append((src, str(exc)))
            continue
        state = "기존 변환본 사용" if cached else "변환"
        print(f"[source_extract] {state}: {src.name} → {path}")
        print(f"    변환기: {fields.get('변환기', '')} · 쪽 표지: {fields.get('쪽 표지', '')}")
        if fields.get("경고", "없음") != "없음":
            print(f"    경고: {fields['경고']}")
    index = write_index(out_dir)
    print(f"[source_extract] 색인: {index}")
    if failures:
        print("[source_extract] 변환 불가 — 통과 아님(exit 3):", file=sys.stderr)
        for src, reason in failures:
            print(f"  - {src}: {reason}", file=sys.stderr)
        print("  대안: kordoc MCP 도구(parse_document·parse_pages)가 보이면 그 결과를 쪽 범위별로 "
              f"{out_dir}에 저장하고 한계에 'MCP 경유 변환'을 적는다. 그것도 없으면 사람에게 텍스트 원문을 요청한다.",
              file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
