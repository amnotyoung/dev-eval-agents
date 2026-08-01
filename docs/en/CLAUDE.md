> English reference translation of `CLAUDE.md`. The Korean file is the executable version loaded by the harness.

# DevEval Agents — Repository Development Context

This file is the instruction Claude Code reads **when working in this repository** (developing and maintaining the plugin).

> ⚠️ **The evaluation workflows are not here.** This repository is itself a **Claude Code plugin**, and the evaluation procedures live in `skills/`. CLAUDE.md is not loaded for plugin users (`claude plugin validate` warns about this) — which is why the workflows were moved into skills. **To change an evaluation procedure, edit `skills/`. Do not write workflows back into this file** (duplication is drift).

## This repository = a plugin

```
.claude-plugin/plugin.json       manifest (name: deveval)
.claude-plugin/marketplace.json  marketplace for self-distribution
skills/                          the 4 evaluation workflows ← the user's actual entry point
agents/                          12 dedicated evaluators & verifiers
hooks/hooks.json + boulder.sh    completion engine (Stop hook)
bin/                             executables placed on PATH while the plugin is enabled
reference/                       5 KOICA criteria digests (shared knowledge)
templates/ · samples/ · scripts/ templates · samples · runners
```

| Skill | What it does |
|-------|--------------|
| `/deveval:evaluate` | project evaluation — 5–6 criteria rated in parallel → composite score + draft grade |
| `/deveval:quality-review` | evaluation-report quality inspection — 24 items / 100 pts / A–D |
| `/deveval:impact-review` | impact-evaluation methodology review — 5 axes / 10 questions |
| `/deveval:write-report` | report drafting — write → numeric check → narrative verification → human |

## How to develop

Since this repository is a plugin, to see its behavior during development you must **load it as a plugin**:

```bash
claude --plugin-dir .        # load this repo as a plugin for testing
claude plugin validate .     # validate the manifest & structure
/reload-plugins              # pick up changes mid-session
```

Do not fall back to `.claude/agents/` or `.claude/settings.json` — the plugin layout (`agents/`, `hooks/hooks.json`) is canonical.

**When you change a Korean canonical file, update its `docs/en/` mirror in the same PR.** This covers `CLAUDE.md`, `AGENTS.md`, `agents/`, and `reference/`; CI (`mirror-sync`) blocks a PR that changes only one side. Label a deliberately one-sided PR `mirror-sync-exempt`.

```bash
bash scripts/check-mirror-sync.sh            # PR mode — check the diff against origin/main
bash scripts/check-mirror-sync.sh --audit    # audit mode — mirror freshness across the repo
```

## Path rules (important)

Plugin users run this from **their own working folder** — not from inside the repo. Therefore:

- **Agents and skills cannot find files via relative `reference/…` paths.** A skill obtains the plugin's absolute path via `deveval-root` (bin) and **embeds absolute paths in the delegation prompt**. Agents only have `Read/Grep/Glob` and cannot discover the path on their own.
- **Hooks** use `${CLAUDE_PLUGIN_ROOT}` (the path changes on plugin updates, so do not store state there).
- **Evaluator outputs** (`.omo/eval-plan.md`, `.omo/draft-report*.md`) are created in the **user's working folder**. Do not write into the plugin directory.

## Principles (shared across all skills & agents)

1. **No evidence, no grade** — with no data, state "insufficient evidence → cannot evaluate" (no fabrication)
2. Unverified information gets `[INFO: needs verification]`
3. The AI produces **provisional scores / draft grades** only — **final confirmation is the human's (the evaluation officer's)**
4. Balance of strengths & weaknesses + statement of limitations
5. Evaluation ethics — anonymity of those surveyed, evaluation independence

Changing these principles means updating all 4 `skills/` and the related agents together.

## Regulatory basis

- `reference/KOICA-평가지침-2024-다이제스트.md` — criteria, 4-point scale, A–F (primary asset). `KOICA-평가지침-다이제스트.md` is the older 2017 version (for comparison)
- `reference/KOICA-사업평가규정-다이제스트.md` — Regulation No. 536 (2025.2): Art. 6 criteria · Art. 7 types · Arts. 27–28 quality review · Art. 5 principles · Art. 19 independence · Ch. 6 ethics
- `reference/KOICA-품질검토-체크리스트.md` — quality-inspection v2 rubric
- `reference/KOICA-영향평가-가이드라인-다이제스트.md` — impact evaluation (KIEP 2025)

Clearly distinguish facts and conclusions from value judgments and recommendations (Art. 5, transparency), and do not infringe evaluation independence (Art. 19: no unilateral demands to amend or delete).

## Optional gateway integration (oda-intelligence)

Three skills (evaluate · write-report · quality-review) and the Codex `AGENTS.md` carry an **optional** external-evidence augmentation — it operates only in sessions where the same maintainer's `oda-intelligence` plugin (a public read-only MCP gateway) is installed, and is skipped otherwise (no hard dependency — the condition that keeps CONTRIBUTING's model-agnostic principle and DPG indicator 4 intact). The canonical source for the integration rules and tool mapping is `docs/oda-intelligence-integration.md`. When you change the integration, sync the skills, `AGENTS.md`, and the integration doc together. By design the agent files are untouched — evidence travels as a self-describing block embedded in the delegation prompt.

> A learning/experimentation project. The other harnesses (Codex `AGENTS.md`, open-weight `scripts/open_runner.py`) share the same `reference/` knowledge — when you change a workflow, review synchronization on that side as well.
