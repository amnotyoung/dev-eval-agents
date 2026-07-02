# Security Policy / 보안 정책

## Threat model / 위협 모델

oh-my-oda-agent is a **local, offline-first** toolkit. It is a collection of
Markdown agent instructions, reference digests, templates, and one shell hook.
It runs inside an LLM agent harness (Claude Code, Codex, or an open-model runner)
on the user's own machine.

- It exposes **no network service**, opens **no ports**, and ships **no server**.
- It stores **no credentials** and manages **no user accounts**.
- The only executable code is:
  - [`.claude/hooks/boulder.sh`](.claude/hooks/boulder.sh) — a Stop hook that
    reads a local plan file (`.omo/eval-plan.md`) and counts unchecked items. It
    performs no network I/O and writes only a local state file.
  - [`scripts/open_runner.py`](scripts/open_runner.py) — an optional runner that
    talks to a **local** Ollama endpoint (`http://localhost:11434`).

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
