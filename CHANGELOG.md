# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
follows [Semantic Versioning](https://semver.org/) (0.x = pre-1.0, interfaces
may still change).

The project was developed iteratively as a series of "slices" in June 2026;
each slice below is recorded as a 0.x milestone.

## [Unreleased] — Digital Public Goods readiness (2026-07)

### Added
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
