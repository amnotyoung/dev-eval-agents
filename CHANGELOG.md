# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
follows [Semantic Versioning](https://semver.org/) (0.x = pre-1.0, interfaces
may still change).

The project was developed iteratively as a series of "slices" in June 2026;
each slice below is recorded as a 0.x milestone.

## [Unreleased]

### Added
- **e2e-8 validation entry** (`docs/validation-log.md`) — the full evaluate-track
  pipeline (6 parallel evaluators + quality-verifier + report-composer + numeric
  checker + narrative-verifier, with optional gateway evidence) ran live on the
  complete text of the real Cambodia CTS end-of-project report: ~60 sampled
  evidence citations, zero hallucinations, 4 real evaluator errors caught and
  corrected by the verification layer, band agreement with the human team
  reproduced, and 3 defects of the published report itself re-confirmed.
- **Regression test suite + CI** (`tests/`, `.github/workflows/checks.yml`) —
  the deterministic components finally have automated tests: 18 unittest cases
  for `scripts/consistency_check.py` (fixtures reproduce failure/false-positive
  patterns observed in real KOICA reports), 15 behavior tests for
  `hooks/boulder.sh`, and `scripts/check-manifest-sync.sh` guarding name/version
  parity across the 4 plugin manifests (Claude + Codex + both marketplaces).
- **Ko↔En composite-score extraction** in the numeric checker — Korean reversed
  form (`총 24점 만점 중 11.7`) and English form (`12.7 points out of 24`).
  Validated against a full sweep of **334 real KOICA end-of-project evaluation
  PDFs**: the checker now catches **two genuine published Ko↔En summary
  mismatches** (11.7 vs 12.7 — the very Cambodia CTS case this project's
  design story is built on — and a sibling report's 9.3 vs 10.3).

### Changed
- **Numeric checker false-positive suppression**, calibrated on the same
  334-report sweep (violation flags 71 → 22, all remaining flags are
  multi-project bundles or true candidates): scale legends/threshold sentences,
  quality-panel stamps (`평가품질 등급`, A–D scheme) and service-bundle grades
  (`용역종합 등급`) vs project A–F, satisfaction-survey composites, count/date
  ratios (`8/20개소`, `3/20-24`, `20/100,000명`, `(35/24)`), PDM achievement
  rates masquerading as `NN/100` quality totals, and line-wrapped severed
  labels (`부/분 성공적`). Criterion-mean sum check now requires a plausible
  4–6 criteria and supports `(a)`–`(f)`.
- **Checker exit codes**: "nothing to check" is now exit **3** (distinct from
  pass 0 / violation 2) so scripted callers cannot mistake it for a pass;
  crash/read failure stays fail-open 0. Skills updated accordingly.
- **Completion engine pause semantics** (`hooks/boulder.sh`) — when a guard
  trips (3 stalls or 20 attempts) the hook now records the plan's fingerprint
  and stops nagging while the plan is untouched; editing the plan (renewed
  intent) re-arms the engine. Previously the counters reset after firing, so an
  abandoned plan re-blocked every subsequent turn.

## [0.10.0] — 2026-08-02 — Digital Public Goods readiness

### Added
- **Packaged as installable Claude Code and Codex plugins** — the repository
  *is* the plugin, so an
  evaluator installs it once and works **in their own folder** instead of inside
  this repo (evaluation reports are the evaluator's local work product; the repo
  is the tool).
  - `.claude-plugin/plugin.json` (name `deveval`) + `.claude-plugin/marketplace.json`
    for self-distribution: `/plugin marketplace add amnotyoung/dev-eval-agents`
    → `/plugin install deveval@deveval-agents`.
  - `.codex-plugin/plugin.json` + `.agents/plugins/marketplace.json` for native
    Codex discovery: `codex plugin marketplace add amnotyoung/dev-eval-agents
    --ref main` → `codex plugin add deveval@deveval-agents`. Both plugin
    manifests use version `0.10.0` and the same stable plugin identity.
  - **Workflows became skills** (`skills/`): `deveval:evaluate`,
    `deveval:quality-review`, `deveval:impact-review`, and
    `deveval:write-report` (Codex invokes them with `$`; Claude Code with `/`).
    A plugin does not load `CLAUDE.md` as context (`claude plugin validate` warns
    about exactly this), so the evaluation procedure now lives in skills — loaded
    on demand rather than always-on.
  - `.claude/agents/` → `agents/` (12 agents, unchanged content),
    `.claude/settings.json` hooks → `hooks/hooks.json` using `${CLAUDE_PLUGIN_ROOT}`.
  - `bin/` (on Claude Code's `PATH` while enabled): `deveval-root` resolves the plugin's absolute
    path so skills can pass **absolute** reference paths to sub-agents — agents only
    have `Read/Grep/Glob` and cannot resolve `reference/…` from the user's folder;
    `deveval-consistency-check` wraps the numeric consistency checker.
  - The same four skills now resolve their installed root without assuming
    plugin `bin/` is on `PATH`, load Claude-format role files into generic Codex
    subagents, and retain a sequential independence fallback when subagents are
    unavailable.
  - `CLAUDE.md` rewritten as **repository/development** context only, with the
    evaluation workflow removed to prevent duplication drift with `skills/`.
- **Open-source licensing**: MIT for software (`LICENSE`) and CC BY 4.0 for
  documentation/content (`LICENSE-CONTENT`).
- **Governance & policy docs**: `MAINTAINERS.md`, `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, `SECURITY.md`, `PRIVACY.md`.
- **Do-no-harm, standards, and platform-independence documentation** under
  `docs/`.
- **Open-model path** (platform-independence evidence): `scripts/open_runner.py`
  runs the same agents on a local open-weight model via Ollama;
  `notebooks/open-model-demo.ipynb` reproduces it on Google Colab.
- **English documentation**: English reference translations under `docs/en/` and
  an English-first `README.md` (Korean preserved as `README.ko.md`).
- **SDG relevance statement** (SDG 16 & 17).
- **DPG application answer packet**: `docs/dpg-application.md`.
- **Impact evaluator** (`dac-impact-evaluator`): the DAC Impact criterion now has
  a dedicated **ex-post** evaluator (KO executable + EN mirror), assessed
  separately and **excluded** from the 5-criterion, 20-point Final-Evaluation
  composite — so all six DAC criteria have an evaluator agent (12 agents total).
  It is distinct from `impact-evaluation-reviewer`, which reviews formal Impact
  Evaluation reports' causal methodology.
- **Optional evidence-gateway integration** (`oda-intelligence`): the evaluate /
  write-report / quality-review skills and the Codex `AGENTS.md` can now augment
  the evidence gate with the same maintainer's public, read-only
  [ODA Intelligence MCP gateway](https://github.com/amnotyoung/oda-intelligence-plugin)
  — country indicators & other donors (relevance/coherence), the Korean ODA map
  (duplication checks), KOICA regulation full text, and `verify_citation` for
  report citations. Strictly optional (no hard dependency; workflows run
  unchanged without the connector, preserving platform independence). Evidence
  discipline: status tools first, missing ≠ zero, gateway evidence augments —
  never replaces — the project documents. Agent files are untouched: evidence
  travels as a self-describing block in delegation prompts. Guide:
  `docs/oda-intelligence-integration.md`.

### Changed
- `reference/` digests rewritten in the project's own expression with explicit
  citations to the underlying KOICA/KIEP sources (copyright-safe).
- `README` restructured (English-first, with License and SDG sections).

## [0.8.0] — 2026-06-14 — Slice 8: multi-harness (Codex support)
### Added
- `AGENTS.md` — a Codex-harness variant of the workflow, so the same agents run
  as a single-agent sequential evaluation. Shared knowledge in `reference/` is
  used by both harnesses. Validated end-to-end with `codex exec` (gpt-5.5).

## [0.7.0] — 2026-06 — Slice 7: quality inspector v2
### Changed
- Report-quality inspector updated to the official *Evaluation Quality Review
  Guideline v2* (2025-06): Pass boundary corrected 70 → 60, v2 sub-item names
  and mapping, 200-character summary, and the evaluation-service aggregate-grade
  table.

## [0.6.0] — 2026-06 — Slice 6: impact evaluation + regulation basis
### Added
- `impact-evaluation-reviewer` module (5 axes / 10 questions → Adequate /
  Conditional / Inadequate).
- Regulatory grounding injected from KOICA Project Evaluation Regulation No. 536.

## [0.5.0] — 2026-06 — Slice 5: report composition support
### Added
- `report-composer` (write access) and `narrative-verifier`, enforcing "no
  evidence, no text".

## [0.4.0] — 2026-06 — Slice 4: report quality inspection (meta-evaluation)
### Added
- `report-quality-inspector` — grades a report on a 24-item / A–D checklist.

## [0.3.0] — 2026-06 — Slice 3: completion engine
### Added
- `.claude/hooks/boulder.sh` Stop hook — drives long/multi-project evaluations to
  completion with stagnation and attempt-cap guards.

## [0.2.0] — 2026-06 — Slice 2 / 2.5: parallel criteria team
### Added
- Parallel 6-criteria evaluation team with aggregate-score → A–F grading
  (parallel multi-angle evaluation).
- `cts-validity-evaluator` — Validity as a 6th auxiliary criterion for CTS /
  technology-innovation projects.

## [0.1.0] — 2026-06 — Slice 1–1.6: first evaluator on KOICA 2024
### Added
- First DAC-criteria evaluator aligned to the *KOICA Evaluation Guidelines 2024*
  (DAC 6 criteria, official A–F grade scale, 4-point rubric).
