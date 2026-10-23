# Security Policy / 보안 정책

## Threat model / 위협 모델

DevEval Agents is a **local, offline-first** toolkit. It is a collection of
Markdown agent instructions, reference digests, templates, and one shell hook.
It runs inside an LLM agent harness (Claude Code, Codex, or an open-model runner)
on the user's own machine.

- It exposes **no network service**, opens **no ports**, and ships **no server**.
- It stores **no credentials** and manages **no user accounts**.
- Executable components include:
  - [`hooks/boulder.sh`](hooks/boulder.sh) — a Stop hook that
    reads a local plan file (`.omo/eval-plan.md`) and counts unchecked items. It
    performs no network I/O and writes only a local state file.
  - [`scripts/open_runner.py`](scripts/open_runner.py) — an optional runner that
    defaults to a local Ollama endpoint (`http://localhost:11434`). Setting
    `OLLAMA_HOST` selects a different endpoint, which receives the input report.
  - The audit/numeric checkers and repository validation scripts under
    `scripts/`, plus their `bin/` wrappers.
  - [`scripts/source_extract.py`](scripts/source_extract.py) — local document
    conversion through kordoc or pdftotext. The npx fallback downloads the
    pinned kordoc package from npm; OCR may download model assets. A PATH
    installation uses its installed version and records that version.

The optional ODA Intelligence integration queries a remote read-only gateway.

`delegation_check.py` checks native Codex/Claude call evidence for the current
workspace. Its receipt is not a filesystem sandbox, and cannot establish the
truth of a model's judgments. `score_calculate.py` accepts question judgments
and computes report values; `auditable_output_check.py --require-scores
--require-isolation` fails when mandatory artifacts cannot be verified.
Local conversion does not make a hosted LLM workflow offline. Conversion
copies in `.omo/sources/` retain the source contents and must be protected like
the originals. Model instructions and checker passes do not establish factual
correctness or eliminate prompt injection; source verification and the human
decision gate remain required.

The main residual risks are therefore (a) prompt-injection via untrusted
evaluation documents fed to the agents, and (b) the usual risks of whichever LLM
harness/model the user chooses to run. Users should treat evaluation inputs as
untrusted and follow the data-handling guidance in [`PRIVACY.md`](PRIVACY.md).

## Supported versions / 지원 버전

The latest `main` branch is supported. Fixes are applied to `main`.

## Reporting a vulnerability / 취약점 신고

Please report suspected vulnerabilities **privately**:

1. Preferred: open a **GitHub Security Advisory** (repository → *Security* →
   *Report a vulnerability*), or
2. Contact the maintainer via GitHub [@amnotyoung](https://github.com/amnotyoung).

Please do **not** open a public issue for a security problem until it has been
addressed. We aim to acknowledge reports within 7 days and to agree on a
disclosure timeline with the reporter.

취약점은 공개 이슈 대신 위 비공개 채널로 신고해 주세요. 7일 이내 접수 확인을
목표로 하며, 신고자와 공개 시점을 협의합니다.
