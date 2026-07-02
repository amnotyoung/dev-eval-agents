# oh-my-oda-agent

*Read this in other languages: **English** (this file) · [한국어](README.ko.md).*

> **A model-agnostic, multi-agent framework that supports OECD-DAC / KOICA-style
> evaluation of ODA (Official Development Assistance) projects.**
> It ports the *design principles* of [OMO (oh-my-openagent)](https://github.com/code-yeongyu/oh-my-openagent)
> — role = authority, evidence gates, rules injection, parallel multi-angle
> review, verification, completion enforcement, and a human gate — into the ODA
> evaluation domain. Criteria, scales, and rules are grounded in the **KOICA
> Evaluation Guidelines (2024)** and **Project Evaluation Regulation No. 536**
> (digests in `reference/`).

The system is **portable Markdown**: agent instructions plus a shared knowledge
base and one shell hook. The same agents already run on **three independent
stacks** — Claude Code, Codex, and a **fully open-weight** model — so the tool is
not locked to any single vendor.

---

## 🌍 Relevance to the Sustainable Development Goals

Better, evidence-grounded evaluation of development aid is part of the machinery
that makes aid *accountable* and *effective*. This tool strengthens that
machinery:

- **SDG 16 — Peace, Justice and Strong Institutions**, esp. target **16.6**
  ("develop effective, accountable and transparent institutions"). The system
  improves the quality, consistency, and transparency of ODA project evaluation —
  with cited evidence, balanced strengths/weaknesses, and a mandatory human gate —
  reinforcing accountable institutional practice in development cooperation.
- **SDG 17 — Partnerships for the Goals**, esp. the targets on **development
  effectiveness and capacity**. By lowering the effort and raising the
  consistency of monitoring & evaluation (M&E), it supports the evaluation
  capacity on which effective, learning-oriented partnerships depend.

Because it evaluates ODA projects **across sectors** (health, energy, water,
education, public administration, …), it indirectly supports the SDGs those
projects target by improving the learning-and-accountability feedback loop.
It is an **enabler for the M&E function**, not a direct service-delivery tool.

## ✅ Digital Public Good readiness

This repository is prepared against the [DPG Standard](https://www.digitalpublicgoods.net/standard)'s
nine indicators:

| # | Indicator | Where |
|---|-----------|-------|
| 1 | SDG relevance | this section, and `docs/dpg-application.md` |
| 2 | Approved open license | [`LICENSE`](LICENSE) (MIT) + [`LICENSE-CONTENT`](LICENSE-CONTENT) (CC BY 4.0) |
| 3 | Clear ownership | [`MAINTAINERS.md`](MAINTAINERS.md) |
| 4 | Platform independence | [`docs/platform-independence.md`](docs/platform-independence.md) |
| 5 | Documentation | this README + [`docs/`](docs/) + English translations in [`docs/en/`](docs/en/) |
| 6 | Data extraction / portability | open Markdown/plain-text only — [`PRIVACY.md`](PRIVACY.md) |
| 7 | Privacy & applicable laws | [`PRIVACY.md`](PRIVACY.md) (PIPA / GDPR) |
| 8 | Standards & best practices | [`docs/standards.md`](docs/standards.md) |
| 9 | Do no harm by design | [`docs/do-no-harm.md`](docs/do-no-harm.md) |

Governance: [`CONTRIBUTING.md`](CONTRIBUTING.md) · [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) · [`SECURITY.md`](SECURITY.md) · [`CHANGELOG.md`](CHANGELOG.md).

## 🎛️ System — 11 agents, two evaluation types, three harnesses

KOICA evaluation comes in **different types**; the system handles two of them
distinctly.

### ① Final Evaluation — rate a project on 6 criteria → **A–F grade**

An orchestrator injects the KOICA criteria/rules, delegates the criteria to
read-only evaluators **in parallel**, has a verifier check the evidence, sums the
scores, and hands a **draft** grade to a human. Standard 5 criteria (Relevance,
Coherence, Effectiveness, Efficiency, Sustainability) sum to 20 points → A–F;
CTS/technology-innovation projects add **Validity** as a 6th criterion.

### ② Impact Evaluation — measure causal effect → **Adequate / Conditional / Inadequate** (no grade)

A different type entirely (causal effect via PSM/DiD/RCT, no A–F grade). Reviewed
on **5 axes / 10 questions** (causal identification, counterfactual design,
selection bias, robustness, …). The 6-criteria frame is deliberately **not**
applied here.

### Agent catalog (11)

| Role | Agent | Access |
|------|-------|:---:|
| Final-eval, 6 criteria | `dac-{relevance,coherence,effectiveness,efficiency,sustainability}-evaluator` + `cts-validity-evaluator` | read |
| Evidence verification | `quality-verifier` | read |
| Report composition | `report-composer` | **write** |
| Narrative verification (hallucination/consistency) | `narrative-verifier` | read |
| Report quality inspection (24-item / A–D) | `report-quality-inspector` | read |
| Impact-evaluation review (5 axes / 10 questions) | `impact-evaluation-reviewer` | read |

Plus a **completion engine** (`.claude/hooks/boulder.sh`, a Stop hook) that drives
long/multi-project evaluations to completion, with stagnation and attempt-cap
guards (OMO "Boulder").

### OMO principle → this system

| OMO principle | Implementation |
|---------------|----------------|
| Parallel multi-angle (hyperplan) | six criteria evaluated in parallel, each from its own angle |
| Role = authority | evaluators/verifiers are read-only; only `report-composer` writes |
| Evidence gate | *no evidence → no grade / no text* (fabrication prohibited) |
| Distrust completion claims | `quality-verifier` / `narrative-verifier` check evidence & consistency |
| Completion enforcement (Boulder) | Stop hook with stagnation / cap guards |
| Rules injection | `CLAUDE.md` injects KOICA 2024 guidelines + Regulation No. 536 |
| **Human gate** *(public-sector, new)* | AI cannot finalize a grade — that is a human's job |

## ▶️ Quick start

**Claude Code** (parallel sub-agents in `.claude/agents/`):
```bash
cd oh-my-oda-agent
claude        # approve the Stop hook in settings.json on first run
```

**Codex** (single-agent sequential, `AGENTS.md`):
```bash
codex exec "samples/sample-evaluation-report.md 이 사업을 DAC 기준으로 평가해줘"
```

**Open-weight model** (no proprietary API — [Ollama](https://ollama.com) + open weights):
```bash
ollama pull qwen2.5:14b
python3 scripts/open_runner.py --out docs/open-model-demo-output.md
```
Or reproduce it on free Google Colab: [`notebooks/open-model-demo.ipynb`](notebooks/open-model-demo.ipynb).

## ✅ Validation

Records of the system actually running and agreeing with real KOICA evaluations:
**[`docs/validation-log.md`](docs/validation-log.md)** — 5 end-to-end runs
(Claude Code ×3, Codex ×1, open-weight ×1) and 4 real-report comparisons
(Cambodia: grade match). ⚠️ Self-validation of a learning/research project (small
sample); expert cross-validation is ongoing.

## 🔌 Platform independence

The mandatory dependency is *a capable LLM agent-harness* — a category, not a
product. The same agents run on Claude Code, Codex, and an open-weight model
(Qwen2.5, Apache-2.0) with **no change to the core product**. Full evidence:
[`docs/platform-independence.md`](docs/platform-independence.md).

## 📜 License

Dual-licensed with DPGA-approved open licenses:

- **Software** (shell hook, config, runner scripts, notebooks) — **MIT**, see
  [`LICENSE`](LICENSE).
- **Documentation & content** (Markdown agents, `reference/` digests, templates,
  samples, docs) — **CC BY 4.0**, see [`LICENSE-CONTENT`](LICENSE-CONTENT).

The `reference/` digests are the project's **own** descriptions of publicly
documented KOICA/KIEP evaluation practice, cited to their sources; original
PDF/HWP documents are not redistributed. See [`MAINTAINERS.md`](MAINTAINERS.md).

## 📚 reference/ (KOICA source digests)

Original PDFs/HWP are excluded for copyright (`.gitignore`); only the project's
own digests are kept: 2024 guidelines (criteria, scales, A–F), Regulation No. 536
(regulatory basis), the quality-review checklist (v2), and the impact-evaluation
guideline (KIEP 2025).

## 🗺️ Roadmap

Slices 1–8 are complete (see [`CHANGELOG.md`](CHANGELOG.md)): first evaluator on
KOICA 2024 → parallel 6-criteria team + CTS validity → completion engine → report
quality inspector → report composition + narrative verifier → impact-evaluation
review + Regulation No. 536 → quality inspector v2 → **multi-harness (Codex)**.

## 📌 Attribution & status

Inspired by the *design principles* of [oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent)
(ideas/patterns only; no OMO source code included — not a derivative). Evaluation
criteria and rules are grounded in official KOICA materials (digests only,
originals excluded). An **independent, unofficial** learning/research project —
not affiliated with or endorsed by KOICA. Maintainer & ownership:
[`MAINTAINERS.md`](MAINTAINERS.md).
