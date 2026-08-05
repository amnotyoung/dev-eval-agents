> English reference translation of `CLAUDE.md`. The Korean file is the executable version loaded by the harness.

# DevEval Agents — Repository Development Context

This file is the instruction Claude Code reads **when working in this repository** (developing and maintaining the plugin).

> ⚠️ **The evaluation workflows are not here.** This repository is itself a **shared Claude Code and Codex plugin**, and the evaluation procedures live in `skills/`. CLAUDE.md is not loaded for installed-plugin users, which is why the workflows were moved into skills. **To change an evaluation procedure, edit `skills/`. Do not write workflows back into this file** (duplication is drift).

## This repository = a plugin

```
.claude-plugin/plugin.json       manifest (name: deveval)
.claude-plugin/marketplace.json  marketplace for self-distribution
.codex-plugin/plugin.json        Codex manifest (same name/version)
.agents/plugins/marketplace.json Codex repository marketplace
skills/                          the 4 evaluation workflows ← the user's actual entry point
agents/                          12 dedicated evaluators & verifiers
hooks/hooks.json + boulder.sh    completion engine (Stop hook)
bin/                             executables Claude puts on PATH (Codex uses absolute fallback paths)
reference/                       official KOICA norms + Impact Evaluation proposal + 3 methods modules (shared knowledge)
templates/ · samples/ · scripts/ templates · samples · runners
```

| Skill | What it does |
|-------|--------------|
| `deveval:evaluate` | project evaluation — 5 criteria rated in parallel → composite score + draft grade |
| `deveval:quality-review` | evaluation-report quality inspection — 24 items / 100 pts / A–D |
| `deveval:impact-review` | impact-evaluation methodology review — 6 proposed principles + 10 DevEval questions |
| `deveval:write-report` | report drafting — write → numeric check → narrative verification → human |

Invoke a skill as `/deveval:<skill>` in Claude Code or `$deveval:<skill>` in Codex.

## How to develop

To inspect Claude behavior during development, **load it as a plugin**:

```bash
claude --plugin-dir .        # load this repo as a plugin for testing
claude plugin validate .     # validate the manifest & structure
/reload-plugins              # pick up changes mid-session
```

The deterministic components (numeric checker, completion engine, manifest identity) have tests guarded by CI (`checks`) — run them locally too:

```bash
python3 -m unittest discover -s tests   # numeric-checker regressions (fixtures = real failure patterns)
bash tests/test_boulder.sh              # completion engine (Stop hook) behavior
bash scripts/check-manifest-sync.sh     # name/version parity across the 4 manifests
```

Do not fall back to `.claude/agents/` or `.claude/settings.json` — the shared plugin layout (`skills/`, `agents/`, `hooks/hooks.json`) is canonical. Validate the Codex manifest separately with plugin-creator's validator.

**When you change a Korean canonical file, update its `docs/en/` mirror in the same PR.** This covers `CLAUDE.md`, `AGENTS.md`, `agents/`, and `reference/`; CI (`mirror-sync`) blocks a PR that changes only one side. Label a deliberately one-sided PR `mirror-sync-exempt`.

```bash
bash scripts/check-mirror-sync.sh            # PR mode — check the diff against origin/main
bash scripts/check-mirror-sync.sh --audit    # audit mode — mirror freshness across the repo
```

## Path rules (important)

Plugin users run this from **their own working folder** — not from inside the repo. Therefore:

- **Agents and skills cannot find files via relative `reference/…` paths.** A skill uses `deveval-root` when available or derives the root from the loaded `SKILL.md` location, then **embeds absolute paths in the delegation prompt**. On Codex, role-specific `agents/*.md` files must also be loaded by absolute path.
- **The numeric checker** is invoked as `<root>/scripts/consistency_check.py` when no bare command is available.
- **Hooks** use `${CLAUDE_PLUGIN_ROOT}`, which Codex also provides as a compatibility variable (the path changes on plugin updates, so do not store state there).
- **Evaluator outputs** (`.omo/eval-plan.md`, `.omo/draft-report*.md`) are created in the **user's working folder**. Do not write into the plugin directory.

## Principles (shared across all skills & agents)

1. **No evidence, no grade** — with no data, state "insufficient evidence → cannot evaluate" (no fabrication)
2. Unverified information gets `[INFO: needs verification]`
3. The AI produces **provisional scores / draft grades** only — **final confirmation is the human's (the evaluation officer's)**
4. Balance of strengths & weaknesses + statement of limitations
5. Evaluation ethics — anonymity of those surveyed, evaluation independence

Changing these principles means updating all 4 `skills/` and the related agents together.

## Shared-knowledge precedence

`reference/` has three roles. The **official normative layer always prevails**; the specialist proposal and methods layers stay within their stated boundaries.

### Official normative layer

- `reference/KOICA-평가지침-2024-다이제스트.md` — criteria, 4-point scale, A–F (primary asset). `KOICA-평가지침-다이제스트.md` is the older 2017 version (for comparison)
- `reference/KOICA-사업평가규정-다이제스트.md` — Regulation No. 536 (2025.2): Art. 6 criteria · Art. 7 types · Arts. 27–28 quality review · Art. 5 principles · Art. 19 independence · Ch. 6 ethics
- `reference/KOICA-품질검토-체크리스트.md` — quality-inspection v2 rubric

### Specialist proposal layer

- `reference/KOICA-영향평가-가이드라인-다이제스트.md` — the KIEP 2025 policy study's **proposed Impact Evaluation guidelines**. It is primary specialist evidence, not an enacted guideline or binding verdict table.

### Methods layer

- `reference/개발평가-설계방법론-다이제스트.md` — theory of change, evaluation questions, design matrix, and validity
- `reference/개발평가-자료분석방법론-다이제스트.md` — measurement, tools, sampling, bias, analysis, and triangulation
- `reference/개발평가-관리보고윤리-다이제스트.md` — TOR, quality management, reporting, recommendations, independence, and ethics

The methods source dates from 2009 and does not define current Coherence, scoring, or grades. Precedence is **official norms > specialist proposal > methods**, and skills delegate only the files needed for the task by absolute path.

Clearly distinguish facts and conclusions from value judgments and recommendations (Art. 5, transparency), and do not infringe evaluation independence (Art. 19: no unilateral demands to amend or delete).

## Optional gateway integration (oda-intelligence)

Three skills (evaluate · write-report · quality-review) and the Codex `AGENTS.md` carry an **optional** external-evidence augmentation — it operates only in sessions where the same maintainer's `oda-intelligence` plugin (a public read-only MCP gateway) is installed, and is skipped otherwise (no hard dependency — the condition that keeps CONTRIBUTING's model-agnostic principle and DPG indicator 4 intact). The canonical source for the integration rules and tool mapping is `docs/oda-intelligence-integration.md`. When you change the integration, sync the skills, `AGENTS.md`, and the integration doc together. By design the agent files are untouched — evidence travels as a self-describing block embedded in the delegation prompt.

> A learning/experimentation project. The installed Codex plugin, the Codex `AGENTS.md` direct-run fallback, and the open-weight `scripts/open_runner.py` share the same `reference/` knowledge — review synchronization across all of them when changing a workflow.
