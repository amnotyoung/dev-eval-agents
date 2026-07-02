# Privacy & Data Handling / 개인정보 처리방침

> Evidence for the Digital Public Goods Standard, **Indicator 7 (Privacy &
> applicable laws)** and **Indicator 9A (data privacy & security)**, and
> **Indicator 6 (data extraction / portability)**.
> 디지털 공공재 표준 **지표 7(프라이버시·적용법)·9A(데이터 프라이버시·보안)·6(데이터 추출)** 근거 문서.

## What this project collects / 본 프로젝트가 수집하는 것

**Nothing.** DevEval Agents is a set of Markdown agent instructions, reference
digests, templates, and one shell hook that run inside an LLM agent harness on
the user's own machine.

- **No accounts, no telemetry, no analytics, no database, no server.**
- It stores no personal data and transmits nothing on its own. The optional
  `scripts/open_runner.py` talks only to a **local** endpoint
  (`http://localhost:11434`).
- Its outputs are plain-text/Markdown files written to the user's local disk.

**아무것도 수집하지 않는다.** 계정·텔레메트리·분석·DB·서버가 없고, 개인정보를
저장하지 않으며, 자체적으로 어떤 데이터도 외부로 전송하지 않는다. 산출물은
로컬 디스크의 평문/Markdown 파일이다.

## Data flows the user should understand / 사용자가 알아야 할 데이터 흐름

The tool processes **evaluation documents that the user supplies at runtime**
(e.g. a project completion report). Two things follow:

1. **If you run the agents on a hosted LLM** (e.g. Claude Code, Codex), the input
   documents are sent to that provider and are governed by **that provider's**
   terms and privacy policy — not by this project. For sensitive inputs, either
   anonymize/redact first, or use the **local open-weight path**
   (`scripts/open_runner.py` + Ollama), which keeps everything on your machine.
   See [`docs/platform-independence.md`](docs/platform-independence.md).
2. **User inputs are not part of this repository.** The `.gitignore` excludes
   source reports and originals; do not commit real evaluation documents.

사용자가 실행 시 제공하는 평가 문서를 처리한다. ① 호스티드 LLM에서 실행하면 그
문서는 해당 제공자로 전송되어 **제공자의 약관·정책**을 따른다(본 프로젝트 관할
아님) — 민감 입력은 사전 비식별하거나 **로컬 오픈모델 경로**를 사용하라. ②
사용자 입력은 리포지토리에 포함하지 않는다(`.gitignore`).

## Personal data in evaluation reports / 평가보고서 내 개인정보

Evaluation reports can contain personal data about survey respondents or
beneficiaries. This project's design **actively minimizes** exposure:

- The agents are instructed to **anonymize** individuals (use initials) and to
  respect evaluation ethics and independence — see
  [`docs/do-no-harm.md`](docs/do-no-harm.md), grounded in KOICA's evaluation
  ethics (Regulation No. 536, Ch. 6: anonymity Art. 42, personal-data protection
  Art. 46).
- Officially **published** KOICA evaluation reports are generally already
  anonymized by KOICA prior to publication. For non-public inputs, users are
  responsible for anonymizing personal data before processing.

평가보고서엔 조사대상자·수혜자 개인정보가 있을 수 있다. 에이전트는 개인을 **익명
처리**(이니셜)하고 평가윤리·독립성을 준수하도록 지시된다(규정 제536호 제6장:
익명성 제42조·개인정보보호 제46조). KOICA가 **공식 게시**한 보고서는 통상 사전
익명화돼 있으며, 비공개 입력은 사용자가 처리 전 비식별할 책임이 있다.

## Applicable laws / 적용 법령

Because the tool runs locally and stores no personal data, the **data controller
is the user or their organization**, under whichever law applies to them:

- **Republic of Korea — Personal Information Protection Act (PIPA / 개인정보
  보호법).** Users processing Korean personal data must comply with PIPA,
  including lawful basis, minimization, and purpose limitation.
- **EU/EEA — GDPR**, where the user processes personal data of EU data subjects.
- Users remain bound by **KOICA's own evaluation ethics and confidentiality**
  rules when handling KOICA materials.

본 툴은 로컬 실행·무저장이므로 **데이터 컨트롤러는 사용자·소속기관**이다. 한국
개인정보보호법(PIPA), (해당 시) GDPR, 그리고 KOICA 평가윤리·비밀엄수 규정을
사용자가 준수한다.

## Data retention / 데이터 보존

The project retains **no** user data (nothing to retain — it has no store).
Outputs live only where the user saves them and can be deleted at any time.

## Data extraction & portability (Indicator 6) / 데이터 추출·이식성

There is **no lock-in**. All inputs and outputs are **open, non-proprietary
formats** — Markdown / plain text. Results can be read, edited, diffed, and moved
with any text tool; no export step or proprietary reader is required.

락인이 없다. 모든 입출력은 **개방·비독점 포맷(Markdown/평문)**이며, 별도 내보내기나
독점 뷰어 없이 어떤 텍스트 도구로도 이동·재사용할 수 있다.
