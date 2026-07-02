# DPG Application — prepared answer packet / DPG 신청 답변 패킷

> This packet contains ready-to-paste answers for the Digital Public Goods
> application at **https://app.digitalpublicgoods.net/**. The **maintainer**
> submits it (the portal requires the authorized representative's identity and
> email verification). Fill the `<…>` fields. Evidence links assume the
> `dpg-readiness` branch has been merged to the default branch.
>
> 이 패킷은 DPG 신청 포털에 그대로 붙여넣을 답변 모음이다. **실제 제출은
> 소유자(권한 있는 대표)가 수행**한다(본인 인증·이메일 검증 필요). `<…>`만 채우면
> 된다. 링크는 `dpg-readiness` 브랜치가 기본 브랜치에 병합된 뒤 유효하다.

Repo: https://github.com/amnotyoung/dev-eval-agents

---

## General information

- **Solution name:** DevEval Agents
- **Aliases / acronyms:** DevEval; formerly "oh-my-oda-agent" (OMOA)
- **Categories:** **Open Software** + **Open Content**
  *(Not "Open AI system": the project ships no model or weights — it orchestrates
  whichever LLM the user supplies. See Indicator 4.)*
- **Short description (tweet-length):** An open, model-agnostic multi-agent
  framework that supports OECD-DAC / KOICA-style evaluation of ODA (development
  aid) projects — with evidence gates, verification, and a mandatory human gate.
- **Website:** https://github.com/amnotyoung/dev-eval-agents
- **Source code:** https://github.com/amnotyoung/dev-eval-agents
- **Contact email:** `<your contact email>`

## Indicator 1 — Relevance to the SDGs

- **Relevant SDGs:** **SDG 16** (Peace, Justice and Strong Institutions) and
  **SDG 17** (Partnerships for the Goals).
- **How it is relevant:**
  - *SDG 16, target 16.6 (effective, accountable, transparent institutions):* the
    tool raises the quality, consistency, and transparency of ODA project
    evaluation — every score cites evidence, strengths and weaknesses are
    balanced, and a human makes the final decision — strengthening accountable
    institutional practice in development cooperation.
  - *SDG 17 (development effectiveness & capacity):* by lowering the effort and
    increasing the consistency of monitoring & evaluation (M&E), it supports the
    evaluation capacity that effective, learning-oriented development
    partnerships depend on.
  - It evaluates ODA projects across sectors (health, energy, water, education,
    public administration), so it indirectly supports the SDGs those projects
    target by improving the learning-and-accountability feedback loop.

## Indicator 2 — Use of approved open licenses

- **Licenses:** **MIT** (software) and **CC BY 4.0** (documentation/content) —
  both on the DPGA-approved lists (OSI / Creative Commons).
- **Evidence:**
  [`LICENSE`](https://github.com/amnotyoung/dev-eval-agents/blob/main/LICENSE),
  [`LICENSE-CONTENT`](https://github.com/amnotyoung/dev-eval-agents/blob/main/LICENSE-CONTENT),
  and the "License" section of the README. Each component's license is mapped
  explicitly; no proprietary/closed license is mixed in.

## Indicator 3 — Clear ownership

- **Owner:** amnotyoung (individual maintainer).
- **Ownership evidence:**
  [`MAINTAINERS.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/MAINTAINERS.md)
  + the copyright notices in `LICENSE` / `LICENSE-CONTENT`.
- **Owning organization type:** individual.
- **Owner country:** Republic of Korea.
- **Do you own all code/content/data?** Yes for the project's own code and
  content. Third-party material is limited to: (a) *design principles* inspired by
  OMO (ideas only, no code, not a derivative) and (b) the project's **own
  descriptions** of publicly documented KOICA/KIEP evaluation methodology (facts
  and criteria are not copyrightable; original documents are cited, not
  redistributed — see `.gitignore` and `LICENSE-CONTENT`). No third-party content
  is redistributed under our license.

## Indicator 4 — Platform independence

- **Does the solution have mandatory closed-component dependencies?** It requires
  *a capable LLM agent-harness* at runtime — a category of tool, not a specific
  proprietary product.
- **How closed components can be replaced:** the core product is portable
  Markdown; the **same agents run on Claude Code, on Codex, and on fully
  open-weight models** (Qwen2.5, Apache-2.0) via Ollama, with **no change to the
  core**. A user can swap the proprietary model for open weights by pointing
  `scripts/open_runner.py` at the same agents — **demonstrated and reproducible**
  in
  [`docs/platform-independence.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/docs/platform-independence.md)
  and the Colab notebook
  [`notebooks/open-model-demo.ipynb`](https://github.com/amnotyoung/dev-eval-agents/blob/main/notebooks/open-model-demo.ipynb).
  The project itself ships no proprietary component.

## Indicator 5 — Documentation

- **Location:** the README, the [`docs/`](https://github.com/amnotyoung/dev-eval-agents/tree/main/docs)
  directory (platform-independence, do-no-harm, standards, validation log), and
  English reference translations under
  [`docs/en/`](https://github.com/amnotyoung/dev-eval-agents/tree/main/docs/en).
  Documentation covers setup for three harnesses, system architecture, the agent
  catalog, use cases, and functional requirements.

## Indicator 6 — Non-PII data extraction / portability

- **Does the solution collect/use non-PII data?** The tool has **no data store**,
  database, or export step. All inputs and outputs are **open, non-proprietary
  formats** (Markdown / plain text), so any data a user produces with it is fully
  portable with any text tool — no lock-in. See
  [`PRIVACY.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/PRIVACY.md).

## Indicator 7 — Privacy & applicable laws

- **Applicable frameworks:** Republic of Korea **Personal Information Protection
  Act (PIPA)**; **GDPR** where EU personal data is processed; and KOICA's own
  evaluation-ethics/confidentiality rules for KOICA materials.
- **Evidence of compliance:**
  [`PRIVACY.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/PRIVACY.md).
  The tool runs locally and stores no personal data; the user/organization is the
  data controller.

## Indicator 8 — Standards & best practices

- **Standards adhered to:** OECD-DAC Evaluation Criteria; KOICA Evaluation
  Guidelines 2024, Regulation No. 536, Quality-Review Guideline v2; open formats
  (CommonMark/Markdown, JSON, Jupyter); SPDX-identified licenses; Semantic
  Versioning + Keep a Changelog; Contributor Covenant.
- **Evidence:**
  [`docs/standards.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/docs/standards.md).

## Indicator 9A — Data privacy & security

- **Does the solution collect/store PII?** **No.** The project stores no PII and
  has no accounts, telemetry, or database. User-supplied inputs may contain PII
  but are processed locally/ephemerally and not retained; the agents are
  instructed to anonymize individuals, and a **local open-weight path** lets
  sensitive documents stay on the user's machine.
- **Measures:**
  [`PRIVACY.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/PRIVACY.md)
  and
  [`docs/do-no-harm.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/docs/do-no-harm.md).

## Indicator 9B — Inappropriate & illegal content

- **Does the solution enable content collection/distribution?** **No.** It does
  not collect, host, publish, or distribute user-generated or third-party
  content; it reads a document the user already has and writes an evaluation
  locally. No moderation surface exists. See `docs/do-no-harm.md` §9B.

## Indicator 9C — Protection from harassment

- **Does the solution facilitate user-to-user interaction?** **No.** There are no
  accounts, messaging, comments, or social features. Community spaces (issues,
  PRs) are governed by the
  [`CODE_OF_CONDUCT.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/CODE_OF_CONDUCT.md).
  See `docs/do-no-harm.md` §9C.

## Scale & reach (optional fields)

- **Countries with active deployments:** Republic of Korea (developed for the
  Korean ODA/KOICA evaluation context); the framework is reusable for any
  OECD-DAC-based evaluation.
- **Multilingual support:** Yes — Korean and English (bilingual documentation).
- **Maturity:** early-stage / experimental (validated prototype; see the
  validation log). *Note: the DPGA supports early-stage projects; maturity is not
  an eligibility bar.*
- **Real-world evaluation targets:** see
  [`docs/real-world-examples.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/docs/real-world-examples.md)
  *(published KOICA evaluation reports this tool is designed to evaluate).*

---

## Residual risk to be aware of / 유의할 잔존 리스크

The main reviewer-judgment risk is **classification**: a reviewer could treat an
LLM-using tool as an "AI system" and ask for open training data/model weights.
Pre-empt this with the Indicator 4 answer and `docs/platform-independence.md`:
the project **ships no model or weights** — the model is user-supplied
infrastructure (like a database or OS), and the tool is demonstrably operable on
open weights. It is therefore an Open Software + Open Content good, not an AI-model
contribution.
