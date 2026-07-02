# Platform Independence / 플랫폼 독립성

> Evidence for the Digital Public Goods Standard, **Indicator 4 (Platform
> Independence)**. / 디지털 공공재 표준 **지표 4(플랫폼 독립성)** 근거 문서.

## Summary / 요약

**DevEval Agents does not depend on any single proprietary platform or model.**
Its substance is *portable Markdown*: agent instructions (`CLAUDE.md`,
`AGENTS.md`, `.claude/agents/*.md`) plus a shared knowledge base (`reference/`)
and one small shell hook. The only mandatory dependency is **"a capable LLM
agent-harness"** — a *category* of tool, not a specific commercial product. The
same agents already run on three independent stacks, including a **fully
open-weight** one.

**본 프로젝트는 특정 상용 플랫폼·모델에 종속되지 않는다.** 실체는 이식 가능한
Markdown(에이전트 지침 + 공용 지식 `reference/` + 소형 shell 훅)이다. 유일한 필수
의존성은 "임의의 LLM 에이전트 하네스"라는 **범주**이지 특정 상용 제품이 아니며,
동일 에이전트가 **완전한 오픈웨이트 스택을 포함해** 세 개의 독립 스택에서 작동한다.

## The same agents on three stacks / 세 스택에서 동일 에이전트

| Stack / 스택 | Harness | Model / 모델 | Openness / 개방성 | Status |
|---|---|---|---|---|
| 1 | Claude Code (`.claude/agents/`, parallel sub-agents) | Anthropic Claude | proprietary | validated (README §Validation) |
| 2 | Codex (`AGENTS.md`, single-agent sequential) | GPT-5.5 | proprietary | validated (`codex exec`, Slice 8) |
| 3 | **Ollama + `scripts/open_runner.py`** | **Qwen2.5-14B (open weights, Apache-2.0)** | **fully open** | **validated locally — see below** |

The reference knowledge in `reference/` is shared unchanged across all three.
Swapping the harness or the model requires **no change to the core product** —
you point a different runner at the same Markdown agents. That is exactly the
substitutability that Indicator 4 asks for.

## Open-weight demonstration / 오픈웨이트 실증

Reproducible, no proprietary API involved:

```bash
# 1. Install & start Ollama (https://ollama.com), then pull an open model
ollama pull qwen2.5:14b          # Apache-2.0 open weights

# 2. Run the same agents on the open model against the bundled sample
python3 scripts/open_runner.py --out docs/open-model-demo-output.md
```

`scripts/open_runner.py` reproduces, on a single open model, what the Codex
harness does with `AGENTS.md`: it injects the rules + the KOICA reference
knowledge, then evaluates the target report against the OECD-DAC criteria. It
uses **only the Python standard library** and talks to a **local** Ollama
endpoint (`http://localhost:11434`).

**Result (Qwen2.5-14B, local, 2026-07):** the system produced a complete
KOICA-style evaluation — the five criteria each scored on the 1–4 scale with
cited evidence, an aggregate score of 13 → draft grade **D**, an explicit
deferral of the final grade to the human evaluator, and a limitations note for
the indicators with missing data. Prompt = 7,631 tokens, completion = 991
tokens. Full output: [`open-model-demo-output.md`](open-model-demo-output.md).

Notably, the open-model run preserved the project's core safeguards — evidence
citations, the "no evidence, cannot evaluate" rule, and the **human gate** — so
platform independence does not come at the cost of the do-no-harm design (see
[`do-no-harm.md`](do-no-harm.md)).

### On Google Colab / 구글 코랩에서

For reviewers without a local GPU, [`notebooks/open-model-demo.ipynb`](../notebooks/open-model-demo.ipynb)
reproduces the same run on Colab's free tier with one "Run all". Mac 없이도 무료로
재현할 수 있다.

### Honest limitation / 정직한 한계

This demonstrates **portability and independence**, not quality parity with the
best commercial models. A larger or better-tuned open model narrows the gap; the
point for Indicator 4 is that the product *functions* on open components and the
proprietary model is a **replaceable runtime choice**, not a hard requirement.

이 실증은 *이식성·독립성*을 보이는 것이지 상용 최상위 모델과의 품질 동치를
주장하지 않는다. 지표 4의 핵심은 제품이 개방 구성요소만으로 **작동**하며 상용
모델은 **교체 가능한 런타임 선택지**라는 점이다.

## Why this is not an "AI system" asset / "AI 시스템" 트랙에 해당하지 않는 이유

Under the DPGA's AI-system guidance, the additional Data/Code/Model-weights
requirements apply to projects that *contribute a model* as the good. This
project **ships no model and no weights** — it is open *software* (MIT) and open
*content* (CC BY 4.0) that orchestrates whichever LLM the user supplies. The
model is infrastructure the user brings, like a database or an OS, not an asset
this project distributes. It is therefore submitted under the **Open Software +
Open Content** categories.

본 프로젝트는 **모델·가중치를 배포하지 않는다.** 사용자가 가져오는 LLM을
조율하는 개방 소프트웨어(MIT)·개방 콘텐츠(CC BY 4.0)이며, 모델은 데이터베이스나
OS처럼 사용자가 제공하는 인프라다. 따라서 **Open Software + Open Content**
카테고리로 제출한다.
