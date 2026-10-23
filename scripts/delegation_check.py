#!/usr/bin/env python3
"""Freeze pre-rating input and verify isolated criterion calls in native host logs.

Exit 0: verified; 2: contract violation; 3: unavailable/unreadable evidence.
This checks parent-history isolation and supplied packets, not a filesystem
security boundary or factual/scoring accuracy. No third-party dependencies.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import uuid

CRITERIA = ("relevance", "coherence", "effectiveness", "efficiency", "sustainability")
FORBIDDEN_FILES = ("criterion-drafts.md", "verification.md", "verified-scores.json", "ratings.json")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def input_digest(manifest):
    bound = {k:manifest[k] for k in ("run_id", "project_root", "packet", "packet_sha256", "source", "source_sha256", "index", "index_sha256")}
    return hashlib.sha256(json.dumps(bound, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def task_names(manifest):
    return {name:f"{name}_r{input_digest(manifest)[:16]}" for name in CRITERIA}


def prepare(brief, source, index, project_root):
    packet_display = str(Path(brief).absolute().parent / "source-pack.md")
    brief, source, index = (Path(p).resolve() for p in (brief, source, index))
    text = brief.read_text(encoding="utf-8-sig")
    cut = re.search(r"(?m)^##\s+3[.．]?\s", text)
    if not cut or "원문 사실대장" not in text[:cut.start()]:
        raise ValueError("1·2절의 원문 사실대장만 포함하는 입력이 필요함")
    body = text[:cut.start()].strip() + "\n"
    if re.search(r"검증 후 종합점수|검증 전 점수|기준별 상세 평정", body):
        raise ValueError("평정 전 입력팩에 평가 결과가 섞여 있음")
    packet = brief.parent / "source-pack.md"
    path = brief.parent / "delegation-manifest.json"
    if path.exists():
        raise ValueError("입력팩이 이미 생성됨 — 현재 실행은 기존 매니페스트를 읽고, 새 실행은 새 폴더를 사용해야 함")
    if packet.exists() and packet.read_text(encoding="utf-8") != body:
        raise ValueError("기존 source-pack.md와 다름 — 새 실행 폴더에서 시작해야 함")
    packet.write_text(body, encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "run_id": uuid.uuid4().hex,
        "project_root": str(Path(project_root).resolve()),
        "packet": str(packet), "packet_sha256": digest(packet),
        "packet_display": packet_display,
        "source": str(source), "source_sha256": digest(source),
        "index": str(index), "index_sha256": digest(index),
    }
    manifest["input_sha256"] = input_digest(manifest)
    manifest["task_names"] = task_names(manifest)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path, manifest


def criterion_name(name):
    leaf = str(name or "").split("/")[-1].split(":")[-1]
    for criterion in CRITERIA:
        if re.fullmatch(rf"(?:dac-)?{criterion}(?:-evaluator)?(?:_r[0-9a-f]{{16}})?(?:[_-]retry\d*)?", leaf):
            return criterion
    return None


def read_trace(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    if not rows:
        raise ValueError("빈 실행 기록")
    return rows


def codex_calls(rows):
    meta = next((r["payload"] for r in rows if r.get("type") == "session_meta"), None)
    if not meta:
        return None
    outputs = {r["payload"].get("call_id"): r["payload"].get("output") for r in rows
               if r.get("payload", {}).get("type") == "function_call_output"}
    calls = []
    for row in rows:
        p = row.get("payload", {})
        if p.get("type") != "function_call" or p.get("name", "").split(".")[-1] != "spawn_agent":
            continue
        a = json.loads(p.get("arguments", "{}"))
        criterion = criterion_name(a.get("task_name"))
        if not criterion:
            continue
        result = outputs.get(p.get("call_id"))
        try:
            result = json.loads(result) if isinstance(result, str) else result
        except ValueError:
            result = None
        named_ok = isinstance(result, dict) and str(result.get("task_name", "")).split("/")[-1] == a.get("task_name")
        prompt = a.get("message") or a.get("prompt") or ""
        calls.append({"criterion": criterion, "call_id": p.get("call_id"), "task_name": a.get("task_name"),
                      "isolated": a.get("fork_turns") == "none",
                      "successful_spawn": isinstance(result, dict) and bool(named_ok or result.get("agent_id")) and not result.get("error"),
                      "prompt_visibility": "redacted" if re.fullmatch(r"gAAAAA[A-Za-z0-9_-]{60,}=*", prompt) else "plain",
                      "prompt": prompt})
    return {"host": "codex", "thread_id": meta.get("id"), "cwd": meta.get("cwd"), "calls": calls}


def claude_calls(rows):
    meta = next((r for r in rows if r.get("sessionId") and r.get("cwd") and not r.get("isSidechain")), None)
    if not meta:
        return None
    outputs = {}
    for row in rows:
        for item in row.get("message", {}).get("content", []) if isinstance(row.get("message", {}).get("content"), list) else []:
            if item.get("type") == "tool_result":
                outputs[item.get("tool_use_id")] = item
    calls = []
    for row in rows:
        content = row.get("message", {}).get("content", [])
        for item in content if isinstance(content, list) else []:
            if item.get("type") != "tool_use" or item.get("name") not in ("Agent", "Task"):
                continue
            a = item.get("input", {})
            criterion = criterion_name(a.get("subagent_type"))
            if not criterion:
                continue
            result = outputs.get(item.get("id"))
            calls.append({"criterion": criterion, "call_id": item.get("id"),
                          "task_name": a.get("subagent_type"), "prompt_visibility": "plain",
                          "isolated": not a.get("resume") and a.get("run_in_background") is False,
                          "successful_spawn": result is not None and not result.get("is_error"),
                          "prompt": a.get("prompt") or ""})
    return {"host": "claude", "thread_id": meta["sessionId"], "cwd": meta["cwd"], "calls": calls}


def verify(manifest_path, transcript):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("지원하지 않는 입력팩 계약 버전")
    violations = []
    if manifest.get("input_sha256") != input_digest(manifest):
        violations.append("입력팩 매니페스트의 결속 해시가 다름")
    for field in ("packet", "source", "index"):
        if digest(manifest[field]) != manifest[field + "_sha256"]:
            violations.append(f"위임 후 {field} 내용이 바뀜")
    rows = read_trace(transcript)
    trace = codex_calls(rows) or claude_calls(rows)
    if trace is None:
        raise ValueError("지원하는 Codex/Claude 원시 실행 기록이 아님")
    if not trace.get("cwd") or Path(trace["cwd"]).resolve() != Path(manifest["project_root"]).resolve():
        violations.append("실행 기록의 작업 폴더가 입력팩과 다름")
    seen = set()
    token = f"[DEVEVAL_PACKET_SHA256: {manifest['packet_sha256']}]"
    input_token = f"[DEVEVAL_INPUT_SHA256: {input_digest(manifest)}]"
    names = task_names(manifest)
    packet_paths = {manifest["packet"]}
    alias = manifest.get("packet_display")
    if alias and Path(alias).resolve() == Path(manifest["packet"]).resolve():
        packet_paths.add(alias)
    relevant = []
    for call in trace["calls"]:
        prompt = call["prompt"]
        scoped = re.fullmatch(re.escape(names[call['criterion']])+r"(?:_retry\d+)?", call.get('task_name') or '')
        if scoped or any(path in prompt for path in packet_paths) or token in prompt or input_token in prompt:
            relevant.append(call)
        elif call.get('prompt_visibility') == 'redacted' and re.search(r"_r[0-9a-f]{16}(?:_retry\d+)?$",call.get('task_name') or ''):
            continue  # clear task scope identifies another run despite redacted body
        elif re.search(r"\[DEVEVAL_INPUT_SHA256: [0-9a-f]{64}\]", prompt):
            continue  # another project's frozen packet in the same parent session
        else:
            violations.append(f"{call['criterion']}: 어느 입력팩인지 식별할 수 없는 위임")
    for call in relevant:
        name = call["criterion"]
        seen.add(name)
        if not call["isolated"]:
            violations.append(f"{name}: 부모 이력 상속 또는 기존/백그라운드 세션 사용")
        if not call["successful_spawn"]:
            violations.append(f"{name}: 성공한 위임 결과가 확인되지 않음")
        prompt = call["prompt"]
        if trace['host']=='codex' and not re.fullmatch(re.escape(names[name])+r"(?:_retry\d+)?",call.get('task_name') or ''):
            violations.append(f"{name}: 입력팩 해시에 결속된 task_name이 아님")
        if call['prompt_visibility']=='plain':
            if token not in prompt or input_token not in prompt or not any(path in prompt for path in packet_paths):
                violations.append(f"{name}: 고정 입력팩 경로·해시가 위임문에 없음")
            if any(path in prompt for path in FORBIDDEN_FILES):
                violations.append(f"{name}: 다른 평정·검증 결과 경로가 위임문에 포함됨")
    for name in sorted(set(CRITERIA) - seen):
        violations.append(f"{name}: 실제 위임 기록 없음")
    call_evidence = [{k: v for k, v in c.items() if k != "prompt"} | {"logged_prompt_sha256": hashlib.sha256(c["prompt"].encode()).hexdigest()} for c in relevant]
    return {"schema_version": 1, "status": "failed" if violations else "passed",
            "host": trace["host"], "thread_id": trace["thread_id"],
            "manifest_path": str(Path(manifest_path).resolve()),
            "manifest_sha256": digest(manifest_path),
            "transcript_path": str(Path(transcript).resolve()),
            "criterion_calls": call_evidence, "violations": violations,
            "prompt_bodies_verified": bool(relevant) and all(c['prompt_visibility']=='plain' for c in relevant),
            "limitations": ["위임문 본문은 호스트 로그에서 가려짐. 이력 분리·실행 범위·입력 무결성은 확인했으나 명시적 위임문 내용은 검사하지 못함"] if any(c['prompt_visibility']=='redacted' for c in relevant) else []}


def find_transcript(project_root, thread_id=None):
    """Find a native host transcript; no guessed pass if evidence is unavailable."""
    root = Path(project_root).resolve()
    home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    db_path = home / "state_5.sqlite"
    if db_path.exists():
        with sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True) as db:
            wanted = thread_id or os.environ.get("CODEX_THREAD_ID")
            if wanted:
                candidates = db.execute("SELECT rollout_path,cwd FROM threads WHERE id=?", (wanted,)).fetchall()
            else:
                candidates = db.execute("SELECT rollout_path,cwd FROM threads WHERE agent_path IS NULL ORDER BY created_at_ms DESC").fetchall()
            for path, cwd in candidates:
                if Path(cwd).resolve() == root and Path(path).is_file():
                    return Path(path)
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))
    # Native Claude escapes dots/spaces as well as slashes in project folders.
    folders = {str(root).replace("/", "-"), re.sub(r"[^A-Za-z0-9]", "-", str(root))}
    candidates = {p for name in folders for p in (config / "projects" / name).glob("*.jsonl")}
    for path in sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True):
        trace = claude_calls(read_trace(path))
        if trace and Path(trace["cwd"]).resolve() == root and (not thread_id or trace["thread_id"] == thread_id):
            return path
    raise FileNotFoundError("현재 원시 실행 기록 없음 — 기록을 보존하는 실행 또는 명시적 --transcript가 필요함")


def verify_receipt(path):
    saved = json.loads(Path(path).read_text(encoding="utf-8"))
    current = verify(saved["manifest_path"], saved["transcript_path"])
    if saved.get("status") != "passed" or saved.get("manifest_sha256") != current["manifest_sha256"] or saved.get("criterion_calls") != current["criterion_calls"]:
        current["violations"].append("독립성 확인서가 현재 원시 기록과 다르거나 통과 상태가 아님")
        current["status"] = "failed"
    return current


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    for name in ("brief", "source", "index"):
        p.add_argument("--" + name, required=True)
    p.add_argument("--project-root", default=".")
    p = sub.add_parser("check")
    p.add_argument("--manifest", required=True)
    p.add_argument("--transcript")
    p.add_argument("--thread-id")
    p.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        if a.command == "prepare":
            path, manifest = prepare(a.brief, a.source, a.index, a.project_root)
            print(f"manifest: {path}")
            print(f"source-pack: {manifest['packet']}")
            print(f"[DEVEVAL_PACKET_SHA256: {manifest['packet_sha256']}]")
            print(f"[DEVEVAL_INPUT_SHA256: {manifest['input_sha256']}]")
            print("Codex task_names: " + json.dumps(manifest['task_names'],ensure_ascii=False))
            return 0
        manifest = json.loads(Path(a.manifest).read_text(encoding="utf-8"))
        transcript = a.transcript or find_transcript(manifest["project_root"], a.thread_id)
        receipt = verify(a.manifest, transcript)
        Path(a.out).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False))
        return 0 if receipt["status"] == "passed" else 2
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        print(f"위임 독립성 확인 불가(exit 3): {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
