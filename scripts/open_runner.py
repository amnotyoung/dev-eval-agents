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
Part 2 of `AGENTS.md` (the Codex direct-run fallback): inject the rules + the layered normative/methods knowledge, then
evaluate a project report against the OECD-DAC criteria.

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
import hashlib
import os
import re
import sys
from pathlib import Path
import urllib.error
import urllib.request

import auditable_output_check
import consistency_check
import score_calculate

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Knowledge injected into the system prompt (what an agentic harness would read
# from disk). The normative sources govern scoring; two compact methods modules
# help the open model diagnose design and evidence without importing old rules.
DEFAULT_REFERENCES = [
    "AGENTS.md",  # Part 2 (Codex direct-run fallback) = system role; Part 1 is repo-dev context
    "reference/KOICA-평가지침-2024-다이제스트.md",
    "reference/KOICA-사업평가규정-다이제스트.md",
    "reference/개발평가-설계방법론-다이제스트.md",
    "reference/개발평가-자료분석방법론-다이제스트.md",
    "templates/auditable-evaluation-brief-template.md",
    "docs/score-contract.md",
    "templates/score-input-template.json",
]

OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")


def read(path):
    full = path if os.path.isabs(path) else os.path.join(REPO_ROOT, path)
    with open(full, "r", encoding="utf-8") as fh:
        return fh.read()


FALLBACK_START = "<!-- deveval:codex-fallback:start -->"
FALLBACK_END = "<!-- deveval:codex-fallback:end -->"


def evaluation_instructions(text):
    """AGENTS.md의 2부(평가 워크플로)만 돌려준다 — 1부(저장소 개발 지침)는 평가 모델에 필요 없다.

    표지가 없는 예전 판이면 문서 전체를 쓴다.
    """
    if FALLBACK_START in text and FALLBACK_END in text:
        return text.split(FALLBACK_START, 1)[1].split(FALLBACK_END, 1)[0].strip()
    return text


def build_messages(target_path, reference_paths, target_bytes=None):
    """Assemble the same context the Codex harness gets: rules + reference,
    then the evaluation target as the user turn."""
    agents_md = evaluation_instructions(read(reference_paths[0]))
    knowledge = "\n\n".join(
        f"===== {p} =====\n{read(p)}" for p in reference_paths[1:]
    )
    system = (
        agents_md
        + "\n\n---\n\n# 주입된 공용 지식 (reference/)\n"
        + "아래 공용 지식은 규범층과 방법론층으로 나뉜다. KOICA 지침·규정만 "
        + "기준·척도·등급을 정하며, 개발평가 방법론 문서는 질문-근거 연결과 "
        + "근거의 강도·한계 점검에만 사용한다. 충돌 시 규범층이 우선하고, "
        + "방법론 지식으로 사업문서의 증거 공백을 메우지 마라.\n\n"
        + knowledge
    )
    target_bytes = Path(target_path).read_bytes() if target_bytes is None else target_bytes
    target = target_bytes.decode("utf-8-sig")
    source_hash = hashlib.sha256(target_bytes).hexdigest()
    user = (
        "다음 사업 종료보고서를 KOICA 2024 평가지침의 DAC 기준으로 평가해줘.\n"
        "평정 전에 점수를 좌우하는 원문 표기를 한 행씩 F-ID 사실대장으로 만들고, "
        "상세 평정은 [사실: Fn]으로 대장에 연결하라. 기준별로 1~4점(근거 없으면 "
        "'평가 불가')과 지지·반대근거를 제시하고, "
        "같은 사실의 값·단위·횟수·기간·완료 상태가 다르면 상충 ID와 양쪽 위치를 "
        "상충·불일치 등록부에 남겨라. 검증 전후 점수와 정정 내역을 보인 뒤 종합점수와 "
        "A~F 등급(안)을 산정하고, 주입된 감사 가능한 평가 브리프 템플릿의 구조를 따르며, "
        "최종 등급 확정은 사람 몫임을 명시해라.\n\n"
        "평균·합계·등급은 계산하지 마라. 브리프 3절은 제목만 두고 4절은 기준별 제목과 근거를 써라. "
        "답변 끝에 score-contract v1 전체 입력 객체를 정확히 하나의 json 코드 블록으로 반환하라. "
        "질문 점수·상태·F-ID·이유를 모두 채워라. 단일 모델 자기검증이므로 verification은 conditional로 둔다. "
        f"source_sha256은 {source_hash}를 그대로 사용하라.\n\n"
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


def validate_output(content):
    """Validate the generated brief without pretending to verify its source facts."""
    if not isinstance(content, str) or not content.strip():
        return 3, ["Empty or non-text model response; nothing was validated."]
    violations = auditable_output_check.inspect(content)
    checks = consistency_check.check_project(
        consistency_check.flatten_html_tables(content), violations
    )
    if violations:
        return 2, violations
    if checks == 0:
        return 3, ["No checkable numeric result; this is not a numeric-validation pass."]
    return 0, ["Audit structure and numeric checks passed; source evidence still needs human review."]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run DevEval Agents on an open model via Ollama.")
    ap.add_argument("--model", default=os.environ.get("DEVEVAL_MODEL", "qwen2.5:14b"))
    ap.add_argument("--target", default=os.path.join(REPO_ROOT, "samples/sample-evaluation-report.md"))
    ap.add_argument("--out", default=None, help="Write the evaluation to this file (Markdown).")
    ap.add_argument("--num-ctx", type=int, default=32768)
    ap.add_argument("--temperature", type=float, default=0.2)
    args = ap.parse_args(argv)

    if args.out and Path(args.out).expanduser().resolve() == Path(args.target).resolve():
        print("[open_runner] Output must not overwrite the source report.", file=sys.stderr)
        return 3

    print(f"[open_runner] Ollama: {OLLAMA_URL}", file=sys.stderr)
    print(f"[open_runner] model : {args.model}", file=sys.stderr)
    print(f"[open_runner] target: {args.target}", file=sys.stderr)

    try:
        target_bytes = Path(args.target).read_bytes()
        messages = build_messages(args.target, DEFAULT_REFERENCES, target_bytes)
    except (OSError, UnicodeError) as exc:
        print(f"[open_runner] Cannot read input; not validated: {exc}", file=sys.stderr)
        return 3
    sys_chars = len(messages[0]["content"])
    usr_chars = len(messages[1]["content"])
    print(f"[open_runner] prompt chars: system={sys_chars} user={usr_chars}", file=sys.stderr)

    try:
        data = chat(args.model, messages, args.num_ctx, args.temperature)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        print(f"[open_runner] ERROR: could not reach Ollama at {OLLAMA_URL} ({exc}).", file=sys.stderr)
        print("[open_runner] Start it with `ollama serve` and pull the model, e.g. `ollama pull qwen2.5:14b`.", file=sys.stderr)
        return 3

    if not isinstance(data, dict) or not isinstance(data.get("message"), dict):
        print("[open_runner] Invalid model response; not validated.", file=sys.stderr)
        return 3
    content = data["message"].get("content", "")
    authority = None
    if not isinstance(content, str) or not content.strip():
        status, findings = 3, ["Empty/non-text model output; not validated."]
    else:
        blocks = list(re.finditer(r"```json\s*\n(.*?)\n```", content, re.DOTALL))
        try:
            candidates = [(b, score_calculate.loads(b.group(1))) for b in blocks]
            candidates = [(b,v) for b,v in candidates if isinstance(v,dict) and "criteria" in v]
            if len(candidates) != 1:
                raise FileNotFoundError("Exactly one structured question-score JSON block is required.")
            block, authority = candidates[0]
            if authority.get("source_sha256") != hashlib.sha256(target_bytes).hexdigest():
                raise score_calculate.Invalid("Question-score source hash differs from the actual input.")
            if authority.get("verification") == "passed":
                authority["verification"] = "conditional"  # one model is not independent verification
            body = content[:block.start()] + content[block.end():]
            name = Path(args.out).stem + ".scores.json" if args.out else "verified-scores.json"
            content, _ = score_calculate.render_text(body, authority, after_name=name)
            status, findings = validate_output(content)
        except FileNotFoundError as exc:
            authority = None; status, findings = 3, [str(exc)]
        except (ValueError, KeyError, TypeError) as exc:
            authority = None; status, findings = 2, [str(exc)]
    for finding in findings:
        print(f"[open_runner] validation (exit {status}): {finding}", file=sys.stderr)
    if not isinstance(content, str) or not content.strip():
        return status
    ev_count = data.get("eval_count")
    prompt_count = data.get("prompt_eval_count")
    print(f"[open_runner] tokens: prompt={prompt_count} completion={ev_count}", file=sys.stderr)

    print(content)
    if not args.out and authority is not None:
        print("\n```json\n" + score_calculate.dumps(authority) + "```")

    if args.out:
        out_path = Path(args.out).expanduser().resolve()
        header = (
            f"# Open-model evaluation output\n\n"
            f"> Generated by `scripts/open_runner.py` on the **open-weight** model "
            f"`{args.model}` via local Ollama — no proprietary API involved.\n"
            f"> Target: `{args.target}`. Prompt tokens: {prompt_count}, "
            f"completion tokens: {ev_count}.\n"
            f"> This artifact is evidence for DPG Indicator 4 (Platform Independence). "
            f"It demonstrates portability, not quality parity with commercial models.\n\n---\n\n"
        )
        validation = f"> Validation exit code: **{status}** (0 = structural/numeric pass; 2 = violations; 3 = cannot determine).\n"
        try:
            if authority is not None:
                score_path = out_path.with_name(out_path.stem + ".scores.json")
                if score_path == Path(args.target).resolve():
                    raise OSError("Score sidecar would overwrite the input report.")
                score_path.write_text(score_calculate.dumps(authority),encoding="utf-8")
            with open(out_path, "w", encoding="utf-8") as fh:
                single = "> Execution: single model; context isolation and independent source verification were not performed.\n"
                fh.write(header.replace("\n\n---", "\n" + validation + single + "\n---") + content + "\n")
        except OSError as exc:
            print(f"[open_runner] Cannot write output: {exc}", file=sys.stderr)
            return 3
        print(f"[open_runner] wrote {out_path}", file=sys.stderr)
    return status


if __name__ == "__main__":
    sys.exit(main())
