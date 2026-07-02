# Contributing to DevEval Agents / 기여 안내

Thank you for your interest in improving DevEval Agents! This project is an
open, model-agnostic agent framework that supports KOICA-style ODA project
evaluation. Contributions of all sizes are welcome.

기여에 관심 가져 주셔서 감사합니다. 이 프로젝트는 KOICA식 ODA 사업평가를 보조하는
개방형·모델 무관 에이전트 프레임워크입니다. 크고 작은 기여를 환영합니다.

## What we welcome / 환영하는 기여

- **Agent improvements** — sharper rubrics, clearer instructions, better output
  formats for the agents in `.claude/agents/`.
- **Reference corrections** — fixes/updates to the `reference/` digests **with a
  citation** to the published KOICA/KIEP source (name + article/page).
- **Harness adapters** — new ways to run the same agents (e.g. additional
  open-model runners beyond `scripts/open_runner.py`).
- **Translations** — improving or extending the bilingual (Korean/English)
  documentation under `docs/en/`.
- **Validation cases** — new worked examples in `samples/` and results in
  `docs/validation-log.md`.

## Ground rules / 기본 원칙

1. **Evidence-grounded.** Mirror the project's own ethic — *no evidence, no
   claim*. Any statement about KOICA methodology must cite its source. Do not
   invent criteria, scales, or regulation.
2. **No copyrighted originals.** Never commit original KOICA/KIEP PDF or HWP
   files (they are git-ignored). Contribute your **own** wording plus a citation,
   not copied text.
3. **Respect evaluation independence & ethics.** Keep the human-gate and
   anonymization principles intact (see [`docs/do-no-harm.md`](docs/do-no-harm.md)).
4. **Keep it model-agnostic.** Avoid hard dependencies on any single proprietary
   LLM or harness. If a change assumes one, note how it degrades/adapts on others.

## Process / 절차

1. Open an issue describing the change (or comment on an existing one).
2. Fork, create a topic branch, make your change.
3. Keep Korean and English docs in sync where practical (the Korean files under
   `.claude/`, `CLAUDE.md`, `AGENTS.md`, `reference/` are the executable source;
   English lives under `docs/en/`).
4. Open a pull request with a clear description and, for methodology changes, the
   supporting citation.

## Licensing of contributions / 기여물 라이선스

By submitting a contribution you agree that it is licensed under the project's
dual-license scheme:

- **Code** contributions under the **MIT License** (`LICENSE`).
- **Documentation/content** contributions under **CC BY 4.0** (`LICENSE-CONTENT`).

You confirm that you have the right to contribute the material under these terms.

## Code of Conduct / 행동강령

All participation is governed by our [Code of Conduct](CODE_OF_CONDUCT.md).
