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
  - *SDG 17, targets 17.9 (effective, targeted capacity-building) and 17.16 /
    17.19 (multi-stakeholder partnerships and better data/methodologies to
    measure progress on the 2030 agenda):* by lowering the effort and increasing
    the consistency of monitoring & evaluation (M&E), it supports the evaluation
    capacity that effective, learning-oriented development partnerships depend on.
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
  content. Third-party material is limited to: (a) general multi-agent **design
  patterns** — the project shares **no source code** with, and is **not a
  derivative of**, the upstream *oh-my-openagent* project (whose license is
  non-standard); only uncopyrightable ideas/patterns were re-implemented in the
  project's own words — and (b) the project's **own
  descriptions** of publicly documented KOICA/KIEP evaluation methodology (facts
  and criteria are not copyrightable; original documents are cited, not
  redistributed — see `.gitignore` and `LICENSE-CONTENT`). No third-party content
  is redistributed under our license.
- **Do you have the right to reproduce / redistribute all included content, data,
  and code? — Yes.** Every file is either the maintainer's **own work** or an
  **uncopyrightable restatement of public facts**; the repository redistributes
  **no third-party code or dataset** under our licenses, and copyrighted originals
  are excluded by design. Evidence, component by component:
  - *Own software* (the `boulder.sh` Stop hook, `scripts/open_runner.py`, the
    notebook, config) → **MIT**, © 2026 amnotyoung
    ([`LICENSE`](https://github.com/amnotyoung/dev-eval-agents/blob/main/LICENSE)).
  - *Own documentation & content* (agent instructions in `.claude/agents/`,
    `CLAUDE.md`, `AGENTS.md`, `templates/`, `docs/`) → **CC BY 4.0**
    ([`LICENSE-CONTENT`](https://github.com/amnotyoung/dev-eval-agents/blob/main/LICENSE-CONTENT)).
  - *`reference/` digests* → the project's **own original wording** summarizing
    *publicly documented* KOICA/KIEP criteria, scales, and regulation (each cited
    by document name + article/page). Facts, criteria, and regulatory provisions
    are **not copyrightable**; only the project's expression is distributed. The
    **original copyrighted PDF/HWP files are never redistributed** — they are
    git-ignored (`*.pdf`, `*.hwp`; see
    [`.gitignore`](https://github.com/amnotyoung/dev-eval-agents/blob/main/.gitignore)).
    Basis stated in each digest's header note and in
    [`MAINTAINERS.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/MAINTAINERS.md)
    §"Third-party material."
  - *No third-party source code* → the repository is **original code**, includes
    **no source code from any other project**, and is **not a derivative work**;
    its multi-agent design was informed only by general, uncopyrightable patterns.
    The single design-lineage note is recorded in
    [`MAINTAINERS.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/MAINTAINERS.md)
    §"Third-party material."
  - *Samples & real reports* → `samples/sample-evaluation-report.md` is a
    **fictional, author-created** example (no real project or personal data); real
    KOICA reports are **linked by URL only, never bundled**
    (`docs/real-world-examples.md`).
  - *Future code contributions* → an **inbound = outbound** term: by contributing,
    a contributor agrees the material is licensed under the same MIT / CC BY 4.0
    scheme and **confirms they have the right to contribute it** — see
    [`CONTRIBUTING.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/CONTRIBUTING.md)
    §"Licensing of contributions." The project is single-maintainer, so no
    separate signed CLA is currently in force.

## Indicator 4 — Platform independence

- **Core technologies the solution depends on (list):** the substance is
  *portable Markdown* (agent instructions + a shared `reference/` knowledge base
  + one shell hook). It ships no model, server, or database of its own and
  orchestrates whichever LLM the user supplies. Core dependencies — every
  mandatory one has a fully open alternative:
  - *An LLM agent-harness* — **mandatory, but a category, not a specific
    product.** The same agents run unchanged on Claude Code (proprietary), Codex
    (proprietary), and Ollama + `scripts/open_runner.py` (fully open).
  - *An LLM model* — **user-supplied.** Proprietary (Anthropic Claude, GPT-5.5)
    *or* a fully open-weight model (**Qwen2.5-14B, Apache-2.0**); the proprietary
    model is a replaceable runtime choice, not a hard requirement.
  - *Python 3* — **standard library only, no third-party packages** — for the
    open-weight runner
    [`scripts/open_runner.py`](https://github.com/amnotyoung/dev-eval-agents/blob/main/scripts/open_runner.py).
  - *Ollama* — open-source local model server for the fully-open path (runs
    locally at `http://localhost:11434`, no proprietary API).
  - *Bash* — for the single optional completion hook `.claude/hooks/boulder.sh`
    (Claude Code path only).
  - *Markdown / plain text* — the format of all agent instructions, reference
    knowledge, and evaluation inputs/outputs. **No framework and no database.**
  - A complete path — **Ollama + Qwen2.5 (Apache-2.0) + the Python standard
    library** — runs the entire solution with no proprietary dependency.
- **Does the solution use any closed components that create a proprietary
  dependency?** **No.** The project ships **no closed component of its own** and
  has **no mandatory proprietary dependency (no lock-in).** It needs a capable LLM
  agent-harness at runtime — a *category* of tool, not a specific product — and a
  complete path built only from open components (**Ollama + Qwen2.5-14B,
  Apache-2.0 + the Python standard library**) runs the entire solution.
  Proprietary options (Claude Code, Codex, Anthropic Claude / GPT-5.5) are
  **optional, replaceable runtime choices** — like a database or OS the user
  supplies — not dependencies the project mandates or bundles.
- **How closed components can be replaced:** the core product is portable
  Markdown; the **same agents run on Claude Code, on Codex, and on fully
  open-weight models** (Qwen2.5, Apache-2.0) via Ollama, with **no change to the
  core**. Replacing a closed component is a **minimal configuration change, not a
  major overhaul** — you point a different runner at the same Markdown agents. A
  user swaps the proprietary model for open weights by pointing
  `scripts/open_runner.py` at the same agents — **demonstrated and reproducible**
  in
  [`docs/platform-independence.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/docs/platform-independence.md)
  and the Colab notebook
  [`notebooks/open-model-demo.ipynb`](https://github.com/amnotyoung/dev-eval-agents/blob/main/notebooks/open-model-demo.ipynb).
  The project itself ships no proprietary component.

## Indicator 5 — Documentation

- **Location:** the
  [README](https://github.com/amnotyoung/dev-eval-agents/blob/main/README.md),
  the [`docs/`](https://github.com/amnotyoung/dev-eval-agents/tree/main/docs)
  directory, and English reference translations under
  [`docs/en/`](https://github.com/amnotyoung/dev-eval-agents/tree/main/docs/en).
  Mapped to the software-documentation types the DPG Standard asks for — **all
  available in English**:
  - *User guide* → README "Quick start" (setup for all three harnesses) plus the
    bundled [`samples/`](https://github.com/amnotyoung/dev-eval-agents/tree/main/samples)
    walk-through.
  - *Technical architecture* → README "System" (11 agents, two evaluation types,
    three harnesses) and
    [`docs/platform-independence.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/docs/platform-independence.md).
  - *Developer docs* →
    [`CLAUDE.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/CLAUDE.md)
    /
    [`AGENTS.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/AGENTS.md)
    (agent contracts & workflow),
    [`CONTRIBUTING.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/CONTRIBUTING.md),
    and the per-agent instruction files, with English mirrors under
    [`docs/en/`](https://github.com/amnotyoung/dev-eval-agents/tree/main/docs/en).
  - *Content access (Open Content)* → the "content" — the Markdown agent
    instructions and the
    [`reference/`](https://github.com/amnotyoung/dev-eval-agents/tree/main/reference)
    digests — is plain Markdown / UTF-8 text: **reading** it needs only a text
    editor or web browser, and **running** it needs any LLM agent-harness (Claude
    Code, Codex, or Ollama + `scripts/open_runner.py`). No proprietary app, reader,
    or special hardware is required.
  - *Additional references* → design/standards, safety, and evidence docs:
    [`docs/standards.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/docs/standards.md),
    [`docs/do-no-harm.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/docs/do-no-harm.md),
    [`docs/validation-log.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/docs/validation-log.md)
    (English summary + Korean detail),
    [`PRIVACY.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/PRIVACY.md),
    and [`CHANGELOG.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/CHANGELOG.md).
  - *AI-system docs (model card, datasheet, training data)* → **not applicable**:
    the project ships **no trained model or weights** (the model is user-supplied —
    see Indicator 4), so there is no model to document. It is submitted as **Open
    Software + Open Content**, not an AI model.

## Indicator 6 — Non-PII data extraction / portability

- **Does the solution collect/use non-PII data?** The tool has **no data store**,
  database, or export step. All inputs and outputs are **open, non-proprietary
  formats** (Markdown / plain text), so any data a user produces with it is fully
  portable with any text tool — no lock-in. See
  [`PRIVACY.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/PRIVACY.md).
- **Which extraction options to select on the form:** the structured presets
  (CSV / XML / JSON, or exposing non-PII data through an API) **do not apply** —
  by design there is no database, no data layer, and no API. Select **"Other"**
  and state: *all content is authored and emitted as **Markdown / plain text**, a
  non-proprietary, human- and machine-readable format that any tool can import or
  export with no conversion step and no lock-in.*

## Indicator 7 — Privacy & applicable laws

- **Applicable frameworks:** Republic of Korea **Personal Information Protection
  Act (PIPA)**; **GDPR** where EU personal data is processed; and KOICA's own
  evaluation-ethics/confidentiality rules for KOICA materials.
- **Evidence (privacy documentation):**
  [`PRIVACY.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/PRIVACY.md)
  — the project's privacy & data-handling policy — and
  [`docs/do-no-harm.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/docs/do-no-harm.md)
  §9A. There is **no separate Terms of Service**: the tool runs locally with no
  accounts or hosted service, so use is governed by the open license
  ([`LICENSE`](https://github.com/amnotyoung/dev-eval-agents/blob/main/LICENSE) /
  [`LICENSE-CONTENT`](https://github.com/amnotyoung/dev-eval-agents/blob/main/LICENSE-CONTENT))
  plus `PRIVACY.md`.
- **Consent, purpose of processing & subject requests:** because the solution
  **collects and stores no PII** (no accounts, database, telemetry, or server),
  there is **no consent to manage, no PII processed for any purpose of the tool's
  own, and no subject-request queue** on the solution's side. Where a user feeds a
  document that incidentally contains personal data, it is processed **locally and
  transiently** and not retained; the **user/organization is the data controller**
  and remains responsible for lawful basis, consent, and data-subject requests
  under PIPA / GDPR. The design supports them: agents are instructed to
  **anonymize** individuals, and a **fully local open-weight path** lets sensitive
  documents never leave the user's machine.

## Indicator 8 — Standards & best practices

- **Standards adhered to:** OECD-DAC Evaluation Criteria; KOICA Evaluation
  Guidelines 2024, Regulation No. 536, Quality-Review Guideline v2; open formats
  (CommonMark/Markdown, JSON, Jupyter); SPDX-identified licenses; Semantic
  Versioning + Keep a Changelog; Contributor Covenant.
- **Evidence:**
  [`docs/standards.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/docs/standards.md).

## Indicator 9A — Data privacy & security

> Baseline: the solution **collects and stores no PII** — no accounts, telemetry,
> analytics, database, or server; it runs on the user's machine and retains
> nothing. It processes only the evaluation document the user supplies at runtime,
> which *may* incidentally contain personal data; that is handled transiently and
> the agents are instructed to anonymize individuals. The five portal questions
> answered against that baseline:

- **Is this the minimum amount of PII required to function? (data minimization)**
  **Yes — the minimum is none.** The solution requires **no PII to operate** and
  collects/stores none. It reads only the document the user provides, only for the
  duration of one run; any PII in that file is incidental to the user's own
  material, not something the tool requests or needs. The agents are further
  instructed to **anonymize** individuals (initials), reducing exposure beyond the
  minimum.
- **How does the solution communicate that it collects PII? (transparency /
  consent)** There is **no PII collection to consent to**, and no signup/account
  surface. Transparency is provided in documentation: [`PRIVACY.md`](https://github.com/amnotyoung/dev-eval-agents/blob/main/PRIVACY.md)
  states plainly that the tool "collects nothing," and discloses the data flows a
  user must understand — in particular that running on a **hosted** LLM sends the
  input to that provider under the provider's own policy, whereas the **local
  open-weight path** keeps everything on-device. The user runs the tool locally and
  controls which file is supplied and where it executes.
- **Which mechanisms delete PII? (retention & deletion)** The solution **retains
  nothing** (it has no datastore), so no server-side deletion mechanism is
  required. Outputs are plain-text/Markdown files the user saves to their **own
  disk** and can delete at any time with ordinary file tools; inputs are never
  copied into the repository or any store (`.gitignore` excludes real reports). If
  a hosted LLM is used, provider-side transient data follows **that provider's**
  retention/deletion policy; the local open-weight path avoids third-party
  retention entirely.
- **Where is PII processed/used, and which components access it? (purpose
  limitation)** PII exists only **transiently**, inside the single document
  supplied for one run, held in memory during processing and not persisted. Access
  is limited to: the **agent instructions** (`.claude/agents/*`, `CLAUDE.md`,
  `AGENTS.md`) that read the document **read-only** to draft an evaluation; and the
  **LLM harness/model** the user chose (hosted → the text is sent to that provider;
  local `scripts/open_runner.py` → it stays on `localhost:11434`). Nothing else has
  access — the completion hook `.claude/hooks/boulder.sh` reads only a local task
  checklist, and there is **no database, content logging, network export, or
  analytics** component. The single purpose is drafting an evaluation.
- **How does the solution ensure data privacy, security & integrity?**
  **Minimize** (no PII stored, nothing retained); **local-by-default** with a fully
  on-device open-weight path, giving data sovereignty over sensitive evaluation
  material; **anonymization** grounded in KOICA evaluation ethics (Regulation
  No. 536 Ch. 6 — Art. 42 anonymity, Art. 46 personal-data protection);
  **third-party clarity** (hosted-LLM inputs are governed by that provider's
  policy, and the user/organization is the **data controller** under PIPA / GDPR);
  **integrity** via open, inspectable, Git-versioned Markdown (no opaque binaries)
  plus evidence/verification gates and a mandatory human gate; and **no
  distribution surface** (it does not host, publish, or share content), so there is
  no collection-storage-distribution channel through which adverse impact could
  arise.
- **Evidence:**
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
