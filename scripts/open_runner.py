#!/usr/bin/env python3
"""
open_runner.py — Run DevEval Agents on a fully OPEN-WEIGHT model.

Purpose (Digital Public Goods, Indicator 4 — Platform Independence)
-------------------------------------------------------------------
The DevEval Agents evaluation system is a set of *portable Markdown* agent
instructions plus a shared knowledge base under `reference/`. It is not tied to
any single proprietary LLM: it already runs on Claude Code and on Codex, and
this script demonstrates it running on an **open-weight** model served locally
by Ollama (https://ollama.com), with NO proprietary API involved.

It reproduces, on a single-agent open model, what the Codex harness does with
`AGENTS.md`: inject the rules + the KOICA reference knowledge, then evaluate a
project report against the OECD-DAC criteria.

Dependencies: Python 3 standard library only (urllib, json). No pip install.
Requires a local Ollama server (`ollama serve`) and a pulled open model.

Usage
-----
    # default: qwen2.5:14b on the bundled sample
    python3 scripts/open_runner.py

    # choose model / target / output
    python3 scripts/open_runner.py --model llama3.1:8b \
        --target samples/sample-evaluation-report.md \
        --out docs/open-model-demo-output.md

Any Ollama-served open-weight model works (qwen2.5, llama3.1/3.3, gemma2,
deepseek, mistral, ...). This is the point: the harness/model is replaceable.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Knowledge injected into the system prompt (what an agentic harness would read
# from disk). Kept minimal: the primary 2024 guideline digest + the regulation.
DEFAULT_REFERENCES = [
    "AGENTS.md",  # the Codex-harness instructions = system role
    "reference/KOICA-평가지침-2024-다이제스트.md",
    "reference/KOICA-사업평가규정-다이제스트.md",
]

OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")


def read(path):
    full = path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)
    with open(full, "r", encoding="utf-8") as fh:
        return fh.read()


def build_messages(target_path, reference_paths):
    """Assemble the same context the Codex harness gets: rules + reference,
    then the evaluation target as the user turn."""
    agents_md = read(reference_paths[0])
    knowledge = "\n\n".join(
        f"===== {p} =====\n{read(p)}" for p in reference_paths[1:]
    )
    system = (
        agents_md
        + "\n\n---\n\n# 주입된 공용 지식 (reference/)\n"
        + "아래는 평가에 사용할 KOICA 공식 자료 다이제스트다. 이 근거에만 기반해 평가하라.\n\n"
        + knowledge
    )
    target = read(target_path)
    user = (
        "다음 사업 종료보고서를 KOICA 2024 평가지침의 DAC 기준으로 평가해줘.\n"
        "기준별로 1~4점(근거 없으면 '평가 불가')과 근거를 제시하고, 종합점수와 "
        "A~F 등급(안)을 산정하되, 최종 등급 확정은 사람 몫임을 명시해라.\n\n"
        "===== 평가 대상 =====\n" + target
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def chat(model, messages, num_ctx, temperature):
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "num_ctx": num_ctx,
            "temperature": temperature,
        },
    }
    req = urllib.request.Request(
        OLLAMA_URL + "/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=1800) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data


def main():
    ap = argparse.ArgumentParser(description="Run DevEval Agents on an open model via Ollama.")
    ap.add_argument("--model", default=os.environ.get("DEVEVAL_MODEL", "qwen2.5:14b"))
    ap.add_argument("--target", default="samples/sample-evaluation-report.md")
    ap.add_argument("--out", default=None, help="Write the evaluation to this file (Markdown).")
    ap.add_argument("--num-ctx", type=int, default=32768)
    ap.add_argument("--temperature", type=float, default=0.2)
    args = ap.parse_args()

    print(f"[open_runner] Ollama: {OLLAMA_URL}", file=sys.stderr)
    print(f"[open_runner] model : {args.model}", file=sys.stderr)
    print(f"[open_runner] target: {args.target}", file=sys.stderr)

    messages = build_messages(args.target, DEFAULT_REFERENCES)
    sys_chars = len(messages[0]["content"])
    usr_chars = len(messages[1]["content"])
    print(f"[open_runner] prompt chars: system={sys_chars} user={usr_chars}", file=sys.stderr)

    try:
        data = chat(args.model, messages, args.num_ctx, args.temperature)
    except urllib.error.URLError as exc:
        print(f"[open_runner] ERROR: could not reach Ollama at {OLLAMA_URL} ({exc}).", file=sys.stderr)
        print("[open_runner] Start it with `ollama serve` and pull the model, e.g. `ollama pull qwen2.5:14b`.", file=sys.stderr)
        sys.exit(1)

    content = data.get("message", {}).get("content", "")
    ev_count = data.get("eval_count")
    prompt_count = data.get("prompt_eval_count")
    print(f"[open_runner] tokens: prompt={prompt_count} completion={ev_count}", file=sys.stderr)

    print(content)

    if args.out:
        out_path = args.out if os.path.isabs(args.out) else os.path.join(REPO_ROOT, args.out)
        header = (
            f"# Open-model evaluation output\n\n"
            f"> Generated by `scripts/open_runner.py` on the **open-weight** model "
            f"`{args.model}` via local Ollama — no proprietary API involved.\n"
            f"> Target: `{args.target}`. Prompt tokens: {prompt_count}, "
            f"completion tokens: {ev_count}.\n"
            f"> This artifact is evidence for DPG Indicator 4 (Platform Independence). "
            f"It demonstrates portability, not quality parity with commercial models.\n\n---\n\n"
        )
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(header + content + "\n")
        print(f"[open_runner] wrote {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
