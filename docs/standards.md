# Standards & Best Practices / 표준·모범사례 준수

> Evidence for the Digital Public Goods Standard, **Indicator 8 (Adherence to
> standards & best practices)**.
> 디지털 공공재 표준 **지표 8(표준·모범사례 준수)** 근거 문서.

## Domain standards / 도메인 표준

The system is built on recognized international and national evaluation
standards — it does not invent its own criteria:

- **OECD-DAC Evaluation Criteria** — Relevance, Coherence, Effectiveness,
  Efficiency, Impact, Sustainability. These are the internationally agreed
  criteria for evaluating development assistance, and they are the backbone of
  the six evaluator agents.
- **KOICA Evaluation Guidelines 2024** (『KOICA 평가 업무수행 길라잡이』) — the
  4-point scale, the A–F aggregate grade scale, and the standard evaluation
  questions the agents apply. See `reference/KOICA-평가지침-2024-다이제스트.md`.
- **KOICA Project Evaluation Regulation No. 536 (2025)** — the regulatory basis
  for evaluation principles, types, quality review, independence, and ethics.
  See `reference/KOICA-사업평가규정-다이제스트.md`.
- **KOICA Evaluation Quality Review Guideline v2 (2025)** — the 24-item / A–D
  meta-evaluation rubric used by `report-quality-inspector`.
- **Impact-evaluation methodology** (KIEP 2025) — causal-identification and
  counterfactual standards used by `impact-evaluation-reviewer`.

시스템은 임의 기준이 아니라 **OECD-DAC 평가기준**과 **KOICA 평가지침 2024·규정
제536호·품질검토 가이드라인 v2·영향평가(KIEP)** 등 국제·국가 표준에 근거한다.

## Open technical standards / 개방 기술 표준

- **Open, non-proprietary formats** — all instructions, knowledge, and outputs
  are **Markdown/CommonMark** and plain text; configuration is **JSON**; the demo
  is a standard **Jupyter/`.ipynb`** notebook. No proprietary formats.
- **SPDX-identifiable licenses** — **MIT** (`LICENSE`) and **CC BY 4.0**
  (`LICENSE-CONTENT`), both on the DPGA-approved lists (OSI / Creative Commons),
  with a clear per-component mapping.
- **Model/harness-agnostic interfaces** — the same Markdown agents run on Claude
  Code (`.claude/agents/`), Codex (`AGENTS.md`), and open-weight models via the
  Ollama HTTP API (`scripts/open_runner.py`). See
  [`platform-independence.md`](platform-independence.md).

## Software & repository best practices / 소프트웨어·리포 모범사례

- **Semantic Versioning** (SemVer) and a **Keep a Changelog**-formatted
  [`CHANGELOG.md`](../CHANGELOG.md).
- Standard community health files: [`README`](../README.md),
  [`LICENSE`](../LICENSE), [`CONTRIBUTING`](../CONTRIBUTING.md),
  [`CODE_OF_CONDUCT`](../CODE_OF_CONDUCT.md) (**Contributor Covenant 2.1**),
  [`SECURITY`](../SECURITY.md), [`MAINTAINERS`](../MAINTAINERS.md).
- **Reproducibility** — a [`validation-log.md`](validation-log.md) records
  end-to-end runs, and the open-model demo is reproducible by anyone on free
  Google Colab (`notebooks/open-model-demo.ipynb`).
- **Internationalization** — bilingual Korean/English documentation (English
  reference translations under [`en/`](en/)).

## AI evaluation best practices / AI 평가 모범사례

The design follows widely recommended practices for responsible AI in
consequential decision support: **human-in-the-loop** (human gate),
**evidence-grounding** (no evidence → no grade), **transparency** (every score
cites its source), and **explicit limitation disclosure**. See
[`do-no-harm.md`](do-no-harm.md).

책임 있는 AI 의사결정 지원의 권고 관행 — **사람 개입**·**근거 기반**·**투명성**·
**한계 명시** — 을 따른다([`do-no-harm.md`](do-no-harm.md)).
