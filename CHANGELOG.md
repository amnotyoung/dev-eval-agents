# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
follows [Semantic Versioning](https://semver.org/) (0.x = pre-1.0, interfaces
may still change).

The project was developed iteratively as a series of "slices" in June 2026;
each slice below is recorded as a 0.x milestone.

## [Unreleased]

### Added
- **Source-fact ledger before scoring** — `deveval:evaluate` now records one
  row per score-critical source occurrence under stable `F` IDs and runs an
  early `--ledger-only` gate. Differences in value/status, unit, denominator,
  period, aggregation rule, or as-of date require a supported explanation or a
  linked conflict ID; final briefs cross-check `F` IDs across the ledger,
  detailed ratings, and conflict register.
- **Repository hygiene CI** — checks now reject copy-suffixed files and
  directories when a canonical sibling exists, portable case/NFC path
  collisions, and duplicate or path-mismatched agent/skill identities. An
  exact-path allowlist documents the rare intentional suffix-shaped name.

- **PDF/HWP source conversion before delegation** — evaluator agents can only
  Read/Grep/Glob, so PDF, HWP, HWPX, DOCX, and XLSX sources were never actually
  searchable. `scripts/source_extract.py` (`bin/deveval-extract`) converts them into
  `.omo/sources/` with real-page markers (`<!-- p.N -->`), a provenance header
  (source path, SHA-256, converter and version, warnings for image regions,
  low-confidence OCR, and pages without text), and an `index.md`. kordoc is
  pinned (4.24.1; GFM tables, no images) and runs from `PATH` or through `npx`;
  `pdftotext -layout` is the PDF fallback; an unconvertible source exits 3. The
  same source is not converted twice. All four skills and the Codex `AGENTS.md`
  delegate converted copies; quality review now runs the numeric checker on the
  converted report instead of skipping PDFs.
- The numeric checker flattens HTML tables (kordoc MCP's default output), so
  `colspan="4"` is no longer read as a composite score.

- **Common evaluator contract** — `reference/평가관-공통계약.md` (with its
  English mirror) now holds the rules all six criterion evaluators share:
  source citation with `p.N`, no score without evidence (missing evidence is
  never a 1), `[사실: Fn]` on score-critical claims, source-conflict
  candidates, partial reading of large sources (Grep, then ≤300-line Reads),
  independence, and the shared output tables. The evaluate skill and the Codex
  `AGENTS.md` pass it to every evaluator.
- `tests/test_evaluator_contract.py` parses each evaluator's output tables and
  fails when their columns drift from the contract.

### Changed
- **Scoring follows the KOICA rating-table form** — human evaluation teams
  score each key question 1–4 (half points common) and compute the criterion
  rating as the mean of the scored questions (weighted mean when the form has a
  weight column). Checked against 21 published 2024-scheme final reports: 53
  of 54 two-question criteria and 13 of 18 three-question Effectiveness
  ratings match the mean. The plugin previously told evaluators the criterion
  score was *not* a mechanical average, so its integer holistic scores could
  not match human ratings. The 2024 digest gains §2-1 (scored questions and
  formula); the contract, skill, verifier, brief template, and Codex fallback
  follow it; grade-table boundaries read "16 to under 18".
- **Effectiveness scores outcome/goal, not visibility** — the current form
  scores outputs, medium/long-term outcome and goal, and equity; no report
  scored visibility. Partnership, follow-on, international-organization, and
  visibility questions become unscored checks that inform the scored ones.
- **Source analyst** — a new `source-analyst` agent is the only role that
  reads the whole source: it writes the brief's scope and source-fact ledger
  (at most 60 score-critical rows, identical repeats on one row) and a
  per-question page index. The lead
  evaluator no longer reads the source (in the e2e baseline it reached 207k
  tokens of context before delegating); evaluators and the verifier start from
  the ledger and index and Grep the rest.
- **Cross-criterion consistency** — the verifier checks for the same fact read
  two ways, double penalties, and contradictory narratives across criteria.
- **Scoring calibration** — each scored question gets a point estimate
  (sensitivity is reported separately, not as a range score); partial absence
  of evidence is not a penalty; a question uses only the facts it covers; a
  conflict matters only when it moves a question score by 0.5 or more; simple
  report typos are not penalties; official records outweigh after-the-fact
  statements.
- **Roles that produce an artifact check it themselves** — the source analyst
  runs `--ledger-only` until its ledger passes; the report composer assembles
  brief sections 3–9 from the saved criterion drafts and verification result
  and runs both checkers; the lead evaluator saves those two files, delegates
  assembly, and only confirms (it no longer edits the brief or reads checker
  code).
- **Leaner hand-offs** — the ledger is capped at 60 rows (2–4 key facts per
  scored question; identical repeats share one row with all locations). The
  composer reads its inputs once, writes the whole brief with one Write, does
  not re-read the source or the checker scripts, and fixes only the lines the
  checkers name. Measured on five real KOICA final reports with the human
  scores removed (seven runs per variant, `docs/validation-log.md` §1-2): cost
  per case −20% (lower in all five cases), wall time −6% (lower in four of
  five), approval prompts per run 6.6 → 0.7, and the grade matched two
  independent blind re-scorers in 7/7 runs (baseline 5/6; human teams 2/5).
- **One agent-instructions document** — the repository-development context
  (`CLAUDE.md`) and the Codex direct-run evaluation fallback (`AGENTS.md`)
  are merged into a single `AGENTS.md`: Part 1 for developing the plugin,
  Part 2 (between `deveval:codex-fallback` markers) for running an evaluation
  directly in Codex. `CLAUDE.md` and `docs/en/CLAUDE.md` are removed; the
  mirror check, CI paths, licensing and DPG docs, and reference mapping tables
  point at `AGENTS.md`. `scripts/open_runner.py` injects only Part 2 into the
  open-weight model. *Claude Code sessions in this repository need a setup
  that loads `AGENTS.md` (or should read it at session start).*
- **Criterion evaluators emit the fact-ID contract** — the evaluate skill
  required `[사실: Fn]` on every claim, but none of the six `dac-*` output
  formats had a fact-ID column. Each rating table now has one, each draft
  returns a **fact-ledger additions** table, and duplicated generic rules were
  replaced by a reference to the common contract plus criterion-specific
  rules. The effectiveness evaluator no longer starts by reading the whole
  source.
- **Impact evaluator's 1-point definition follows the official scale** — it
  read "most evidence of transformative effect lacking", which turned missing
  evidence into a score; missing evidence is now *cannot evaluate*.
- The Codex single-agent path reads the contract and the matching evaluator
  file per criterion, and states that it cannot structurally guarantee
  independence between criteria.
- **Checker exit codes no longer report an unread file as a pass** —
  `consistency_check.py` now returns 3 (cannot determine) instead of 0 for a
  missing or undecodable file, an internal error, or a usage error (argparse's
  default 2 collided with "violation"). Both checkers read UTF-8 (with BOM) and
  CP949. *Callers that treated a read failure as success must handle exit 3.*
- **Grade↔score judgment follows each scheme's official bands only** — /20
  uses the KOICA 2024 A–F table (letters and labels); /16 uses the Prime
  Minister's Office 2015 label bands (14·11·8 points) quoted in real reports.
  The previous mean-based bands (3.5/2.5/1.5) had no normative source and
  contradicted the /16 legend; /24 and other schemes are no longer judged.

### Fixed
- **The lead evaluator polled with `sleep`** — when a delegation left
  `run_in_background` unset, the host ran the five criterion evaluators
  asynchronously and the lead slept and re-read its whole context seven times.
  All four skills now pass `run_in_background: false` on every delegation.
- **Approval prompts from compound checker commands** — checker runs wrapped in
  `cd`, `&&`, shell variables or `echo $?`, and `sed -i` edits, were denied
  (each is an approval prompt for a real user). Checkers now run as one
  absolute-path command, and the source analyst fixes ledger rows with Edit.
- **The composite line skipped both checks** — the brief template put the
  sensitivity range on the composite line; a line with '잠정', '범위' or '~'
  is skipped by both checkers, so the score-sum and grade checks never ran and
  `consistency_check.py` returned exit 3. The composite line now carries only
  `score/20, grade`; the range has its own `민감도` line. Single-row ledger
  verdicts must stay exactly `단일 출처 — 전체검색 완료` (cross-references go
  to section 4 and the conflict register).
- **Evaluations stopped halfway in headless runs** — a real end-to-end run on a
  137-page, three-project HWP report delegated the fact-ledger work in the
  background and ended its turn; the headless runner killed the subagents
  after 10 minutes, so no criterion evaluator or verifier ever ran. All four
  skills now delegate in the foreground (parallel calls in one message) and
  never end a turn while background work is pending; long source conversion
  is awaited.
- **The completion engine was off for most evaluations** — the plan board,
  which arms the Stop hook, was only created for "long or multi-project"
  evaluations and was skipped even for that three-project bundle. A plan board
  is now created for every evaluation, with a shared block for conversion and
  project-boundary detection.
- **Permission friction from shelling into the plugin folder** — skills told
  the orchestrator to verify `reference/` etc. and copy templates, which it did
  with `ls`, `test`, and `cp` outside the working folder (blocked in the e2e
  run). Plugin files are now checked with Glob and templates moved with
  Read/Write.
- **Bundled reports could mix projects** — briefs, matrices, and drafts now
  live in `.omo/<project-slug>/`; a bundle gets one folder, brief, and F/X-ID
  series per project. Re-delegation passes only the brief's scope and ledger
  sections, never the sections holding other criteria's scores.
- `tests/test_skill_run_rules.py` pins these run rules.
- **Grade checks were silently off for the plugin's own briefs** — any "잠정"
  anywhere in a document disabled grade↔score checking, and the brief notation
  `13/20, D(안)` was not read as a grade, so `13/20, A(안)` passed. Exclusion is
  now per line; pre-verification lines (`검증 전 …`) and `14→13`, `C→D` history
  lines are excluded instead of the whole document. 2024 letter↔label
  mismatches (`D(성공적)`) are reported.
- **`종합 점수 24점 만점 중 11.7` was read as composite 2** (regex backtracking
  into the denominator). Values may no longer be cut mid-number; three-decimal
  composites (`13.125 /16점`) are kept whole; `20점 만점에 15점` is read on
  composite-context lines (not psychological-test ranges such as `17-18점`);
  criterion sums are compared at the composite's stated precision.
- **Auditable briefs passed with template prompts left in place** — any
  bracket-only table cell, labeled bullet value, or bare line such as `[질문]`,
  `[통과 / 조건부 통과 / 반려]`, or `[없음/Xn]` now fails; plugin markers
  (`[사실: F1]`, `[근거: …]`, `[INFO: 확인 필요]`, `[사람 판단 필요]`) remain
  valid.
- **Auditable briefs could carry scores without evidence** — each criterion's
  post-verification score must be 1–4, a range, or an explicit unavailable
  label; a criterion marked `기준 전체 평가 불가` may not keep a score; a brief
  with unavailable criteria may not state a single composite; five numeric
  criterion scores must sum to the stated composite.
- `bin/` wrappers resolve symlinks, so linking them into another `PATH`
  directory no longer exits 2 ("violation") with "can't open file".
- A 334-report sweep of real KOICA evaluation PDFs is unchanged by these fixes
  (92 pass / 20 violations / 222 cannot determine, identical messages).

## [0.12.0] — 2026-08-05 — Auditable briefs & normative criteria cleanup

### Changed
- **Auditable evaluation brief is now the default evaluation deliverable** — a
  score-only paragraph no longer satisfies the evaluate workflow. Criterion
  drafts must retain supporting and counterevidence, evidence status, adjacent-
  score rationale, and source-conflict candidates; the verifier assigns global
  conflict IDs and reports pre/post-verification scores before aggregation.
- **Material source conflicts survive every handoff** — conflicting indicator
  units, activity counts, project periods, budgets, and completion/defect status
  are recorded with both source locations, resolution status, score/conclusion
  effect, and follow-up. Report composition and narrative verification may not
  smooth these conflicts away.

### Added
- `templates/auditable-evaluation-brief-template.md` and the deterministic
  `scripts/auditable_output_check.py` guard, with regression fixtures proving
  that a terse score-only answer and an unregistered conflict marker fail.

### Removed
- The non-standard CTS-only `Validity` criterion, its evaluator, 24-point
  aggregation branch, and report/template routing. Project evaluation now uses
  only the documented KOICA/OECD-DAC criteria and scoring path.

## [0.11.0] — 2026-08-05 — Layered evaluation knowledge & source-status hardening

### Added
- **Layered development-evaluation methodology knowledge** — three own-word,
  bilingual digests derived from *The Road to Results* cover evaluation design
  (front-end analysis, ToC, questions, matrix, validity), data and analysis
  (measurement, sampling, bias, mixed methods, triangulation), and management /
  reporting / ethics (TOR, QA, recommendations, independence). The source PDF
  remains excluded from distribution.
- **Progressive methods routing across all four skills** — official KOICA sources
  remain the normative layer; the KIEP 2025 Impact Evaluation proposal is labeled
  separately as specialist evidence, and methods modules are passed only where
  they help diagnose evidence, design, reporting, or ethics. The Codex direct-run
  fallback and open-weight runner use the same precedence rule.
- **Evaluation design-matrix template** — links question type, judgment criteria,
  baseline/target, source, sample, collection, analysis, triangulation, limits,
  and a claim-evidence register. Complex evaluations can maintain it under the
  user's `.omo/` workspace and pass it through evaluation and report composition.

### Changed
- The open-weight runner now injects the design and data-analysis modules after
  the current KOICA guidance and regulation, with a hard prompt boundary that
  older methodology cannot create criteria, scores, grades, or missing case
  evidence.
- **Impact-review source integrity** — corrected the KIEP 2025 policy study's
  status from normative guidance to a proposed guideline; restored its six
  operating principles (including Sustainability), its three-element/seven-item
  evaluability screen, and source page references. The ten review questions and
  three-way result are now explicitly DevEval operational constructs. Sector or
  completion stage no longer causes automatic rejection when credible pre-data
  and comparison design remain possible.

## [0.10.0] — 2026-08-02 — Codex support, evidence gateway & verified hardening

### Added
- **Codex became a first-class host** — the same plugin now installs on both
  hosts under one identity: `.codex-plugin/plugin.json` +
  `.agents/plugins/marketplace.json` for native Codex discovery
  (`codex plugin marketplace add amnotyoung/dev-eval-agents --ref main` →
  `codex plugin add deveval@deveval-agents`), sharing the `name` and `version`
  of the Claude manifest added in 0.9.0. The four skills are invoked with `$` on
  Codex and `/` on Claude Code.
  - The skills now resolve their installed root without assuming plugin `bin/`
    is on `PATH`, load Claude-format role files into generic Codex subagents,
    and retain a sequential independence fallback when subagents are unavailable.
  - `AGENTS.md` reframed as the **direct-run fallback** for a cloned repository,
    rather than the Codex workflow of record.
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
- **Mirror-sync CI** (`.github/workflows/mirror-sync.yml`,
  `scripts/check-mirror-sync.sh`) — blocks a PR that changes a Korean canonical
  file (`CLAUDE.md`, `AGENTS.md`, `agents/`, `reference/`) without updating its
  `docs/en/` mirror, with an `--audit` mode for repository-wide staleness. The
  English `CLAUDE.md` mirror had silently sat a month behind before this.
- **Regression test suite + CI** (`tests/`, `.github/workflows/checks.yml`) —
  the deterministic components finally have automated tests: 20 unittest cases
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
- **e2e-8 validation entry** (`docs/validation-log.md`) — the full evaluate-track
  pipeline (6 parallel evaluators + quality-verifier + report-composer + numeric
  checker + narrative-verifier, with optional gateway evidence) ran live on the
  complete text of the real Cambodia CTS end-of-project report: ~60 sampled
  evidence citations, zero hallucinations, 4 real evaluator errors caught and
  corrected by the verification layer, band agreement with the human team
  reproduced, and 3 defects of the published report itself re-confirmed.

### Changed
- **License metadata corrected** in both plugin manifests to `MIT AND CC-BY-4.0`,
  matching the repository's actual split (MIT code + CC BY 4.0 content).
- **README (both languages)** gained install and invocation instructions for the
  two hosts, and the 12 English agent mirrors were resynced with their Korean
  canonical files (they had drifted a month behind).
- **Numeric checker false-positive suppression**, calibrated on the same
  334-report sweep (violation flags 71 → 20, all remaining flags are
  multi-project bundles or true candidates): scale legends/threshold sentences,
  quality-panel stamps (`평가품질 등급`, A–D scheme) and service-bundle grades
  (`용역종합 등급`) vs project A–F, satisfaction-survey composites, count/date
  ratios (`8/20개소`, `3/20-24`, `20/100,000명`, `(35/24)`), PDM achievement
  rates masquerading as `NN/100` quality totals, line-wrapped severed labels
  (`부/분 성공적`), and lines that merely *quote* a mismatch. Criterion-mean sum
  check now requires a plausible 4–6 criteria and supports `(a)`–`(f)`.
- **Checker exit codes**: "nothing to check" is now exit **3** (distinct from
  pass 0 / violation 2) so scripted callers cannot mistake it for a pass;
  crash/read failure stays fail-open 0. Skills updated accordingly. *Callers that
  treated any non-2 exit as success should be updated.*
- **Completion engine pause semantics** (`hooks/boulder.sh`) — when a guard
  trips (3 stalls or 20 attempts) the hook now records the plan's fingerprint
  and stops nagging while the plan is untouched; editing the plan (renewed
  intent) re-arms the engine. Previously the counters reset after firing, so an
  abandoned plan re-blocked every subsequent turn.

## [0.9.0] — 2026-07-22 — Plugin packaging & Digital Public Goods readiness

> Recorded retroactively. The version was bumped to 0.9.0 when the repository
> was packaged as a Claude Code plugin, but no entry was written at the time and
> 0.10.0 later absorbed the description. This entry restores it from the commit
> history; 0.9.0 was never tagged or published, so its work first reached users
> inside the `v0.10.0` tag.

### Added
- **Packaged as an installable Claude Code plugin** — the repository *is* the
  plugin, so an evaluator installs it once and works **in their own folder**
  instead of inside this repo (evaluation reports are the evaluator's local work
  product; the repo is the tool).
  - `.claude-plugin/plugin.json` (name `deveval`) + `.claude-plugin/marketplace.json`
    for self-distribution: `/plugin marketplace add amnotyoung/dev-eval-agents`
    → `/plugin install deveval@deveval-agents`.
  - **Workflows became skills** (`skills/`): `deveval:evaluate`,
    `deveval:quality-review`, `deveval:impact-review`, and
    `deveval:write-report`. A plugin does not load `CLAUDE.md` as context
    (`claude plugin validate` warns about exactly this), so the evaluation
    procedure now lives in skills — loaded on demand rather than always-on.
  - `.claude/agents/` → `agents/` (12 agents, unchanged content, moved as a git
    rename to preserve history), `.claude/settings.json` hooks →
    `hooks/hooks.json` using `${CLAUDE_PLUGIN_ROOT}`.
  - `bin/` (on Claude Code's `PATH` while enabled): `deveval-root` resolves the
    plugin's absolute path so skills can pass **absolute** reference paths to
    sub-agents — agents only have `Read/Grep/Glob` and cannot resolve
    `reference/…` from the user's folder; `deveval-consistency-check` wraps the
    numeric consistency checker.
- **Numeric consistency checker** (`scripts/consistency_check.py`) — a
  format-agnostic, standard-library-only checker for a report's *self*
  contradictions: composite score restated differently across the Korean
  summary, English summary and tables; grade↔score divergence; `a+b+c+d ≠
  composite`. Deliberately separates "nothing to check" from "passed" so a
  thin read cannot look like a green light.
- **Impact evaluator** (`dac-impact-evaluator`): the DAC Impact criterion now has
  a dedicated **ex-post** evaluator (KO executable + EN mirror), assessed
  separately and **excluded** from the 5-criterion, 20-point Final-Evaluation
  composite — so all six DAC criteria have an evaluator agent (12 agents total).
  It is distinct from `impact-evaluation-reviewer`, which reviews formal Impact
  Evaluation reports' causal methodology.
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
- **DPG application answer packet**: `docs/dpg-application.md`, plus
  `docs/real-world-examples.md` with links to the published KOICA reports.
- **Impact-track validation runs** e2e-6 / e2e-7 recorded in
  `docs/validation-log.md`, on a real KOICA impact-evaluation report.
- **Project identity**: renamed to **DevEval Agents**, with an SVG/PNG logo.

### Changed
- `reference/` digests rewritten in the project's own expression with explicit
  citations to the underlying KOICA/KIEP sources (copyright-safe).
- `README` restructured (English-first, with License and SDG sections).
- `CLAUDE.md` rewritten as **repository/development** context only, with the
  evaluation workflow removed to prevent duplication drift with `skills/`.

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
