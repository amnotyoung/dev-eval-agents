# 검증 기록 (Validation Log)

> DevEval Agents가 ① **실제로 작동하는가**(실물 e2e) ② **실제 KOICA 평가 결과와 부합하는가**(대조)의 기록.
>
> ⚠️ **학습·실험 프로젝트의 자체 검증**이며 공식 검증이 아니다. 표본 소수(4건), 한계 존재(§4). 최종 갱신: 2026-07-03 (오픈모델 실증 e2e-5 추가).

---

## Summary (English)

> This log records two things: **(1) does the system actually run** (live
> end-to-end tests) and **(2) does it agree with real KOICA evaluations**
> (comparison). ⚠️ This is **self-validation of a learning/research project, not
> an official validation** — small sample (4 comparisons), with limitations in
> §4. Last updated 2026-07-03 (added the open-weight run e2e-5). The detailed
> tables below are kept in Korean (the working language of the KOICA source
> material); this section is a full English synopsis for reviewers.

**1. Live end-to-end runs (does it actually work).** Five headless runs — not
simulations: the harness loads the real `.claude/agents/*.md` (or `AGENTS.md`)
and the transcript is checked for the actual sub-agent calls.

- **e2e-1** — bundled `samples/` report on Claude Code: five `dac-*-evaluator`
  sub-agents fired; the deliberately blank indicator (O-2) was caught; coherence
  and sustainability were marked *"cannot evaluate"*; the aggregate was withheld
  and handed to the human.
- **e2e-2** — Myanmar solar project: five evaluators fired; coherence *"cannot
  evaluate"*; a conditional draft grade **D**.
- **e2e-3** — quality inspection of a defect-seeded report:
  `report-quality-inspector` fired with the v2 rubric (Pass = 60); caught the
  grade↔text mismatch, unmet SMART targets, and a missing attachment → 58 → **D
  (Non-Pass)**.
- **e2e-4** — **Codex harness** (`AGENTS.md`, GPT-5.5 via `codex exec`):
  `AGENTS.md` auto-loaded, `reference/` digests cited down to line numbers, the
  five criteria scored *sequentially* — same principles (evidence gate, three
  "cannot evaluate", withheld aggregate, human gate) as Claude Code.
- **e2e-5** — **open-weight harness** (`scripts/open_runner.py`, local Ollama +
  **Qwen2.5-14B**, Apache-2.0, **no proprietary API**): rules + `reference/`
  injected; five criteria scored 1–4 with evidence; aggregate 13 → draft **D**;
  the **human gate and the limitations note were preserved**. Its *"cannot
  evaluate"* calls were less conservative than the commercial harness (a
  calibration gap) — this demonstrates **portability, not quality parity**.

→ The Claude Code workflow was reproduced **3×** (2 project evaluations + 1
quality inspection); e2e-4 and e2e-5 show the **same shared knowledge runs on
Codex and on a fully open-weight stack** (multi-harness).

**2. Comparison against real KOICA reports (4 cases).**

| Project | Type | Human team | DevEval Agents | Agreement |
|---|---|---|---|---|
| Cambodia cervical-cancer screening SW | CTS (6-criteria) | 11.7/24 *partially successful* | 13/24 *partially successful* | ✅ **grade match** (1.3 pt apart, derived independently) |
| Myanmar solar | infra, completion (2018, 4-criteria) | 11.33/16 *successful* | ~12/20 **D** *partially successful* | ◐ **per-criterion direction match** (relevance 3 / effectiveness 3 / efficiency 2 exact); aggregate one band off |
| Pakistan wastewater | infra, completion (2017, qualitative) | no grade ("mostly met") | **D** (13.5/20) | ◐ weakness (sustainability) **direction match** |
| Vietnam vocational training | **impact evaluation** | (ungraded impact eval) | recognized "6-criteria inapplicable" → routed to the impact-evaluation reviewer | ✅ **evaluation-type distinction** verified |

Observation: in the two cases with a comparable/clear grade (Cambodia, Myanmar),
the **per-criterion direction agrees strongly**.

**3. Safeguard evidence.** No evidence → no grade (missing-evidence criteria are
marked *"cannot evaluate"*, never fabricated); the planted blank (O-2) was caught
independently; no aggregate is asserted when a *"cannot evaluate"* is present;
every output ends by deferring the final grade to the human; and a
**self-correction** case is on record — an evaluator once refused over a
"biased input" concern, then returned to an independent balanced score after
context was added (neither blindly complying nor ignoring the evidence).

**4. Honest tendencies & limitations.** Tendency: **more conservative** than the
human teams on sustainability and efficiency (possibly good rigor, possibly
over-conservatism — a calibration task). Limitations: **only 4 comparisons**
(not statistically reliable); fact-extraction (PART A) is done by a
human/assistant, so extraction bias would propagate (unresolved); the teams'
grade systems differ (2018 4-criteria/16 vs 2024 5-criteria/20), needing
normalization for a direct aggregate comparison; **no expert 1:1
cross-validation** yet; direct processing of very large PDFs is unverified (a
109-page report was run from an extract).

**Conclusion:** *"it runs"* is demonstrated (live e2e reproduced); *"it agrees in
direction with the evaluation teams"* is observed across 4 cases (per-criterion
match in the 2 clear-grade cases). Reliability still needs a larger sample and
expert cross-validation. Current stage = a **validated prototype, ahead of
production deployment**.

---

## 1. 실물 e2e — 실제 에이전트 작동 검증

시뮬레이션(메인이 역할을 흉내냄)이 아니라, headless `claude -p`로 `DevEval Agents`를 로드해 **실제 `.claude/agents/*.md`가 호출되는지** 검증했다.

```bash
# 검증 방식 (재현 가능)
cd dev-eval-agents
claude -p "<입력> 이 사업을 DAC 5대 기준으로 평가해줘" \
  --dangerously-skip-permissions --verbose --output-format stream-json --max-turns 50
# → 출력 stream에서 "subagent_type":"dac-*-evaluator" 호출을 확인
```

| 회차 | 입력 | 결과 |
|---|---|---|
| **e2e-1** | `samples/sample-evaluation-report.md` | 5개 `dac-*-evaluator` subagent_type 호출 ✅ / 의도된 빈칸(O-2 직무역량) 포착 / 일관성·지속가능성 "평가 불가" / 종합 보류·사람 인계 작동 |
| **e2e-2** | 미얀마 태양광 사업 사실근거 | 5개 `dac-*-evaluator` 호출 ✅ / 일관성 "평가 불가" 처리 / D(부분 성공적) 단서부 산정 |
| **e2e-3** | 품질심사: 결함 삽입 가상 평가보고서 | `report-quality-inspector` 호출 ✅ / **v2 룰브릭 적용**(Pass 60·세부항목 v2 공식명칭·총평 200자) / 등급-본문 불일치·SMART 미충족·첨부 누락 포착 / 58점 → D(Non-Pass). *(60 경계 적용은 확인; 단 58점이라 62~68점 경계케이스 'C vs D' 대조는 미실시)* |

| **e2e-4** | **Codex 하네스**: `AGENTS.md`로 사업평가(samples) | `codex exec`(gpt-5.5)로 실행, **AGENTS.md 자동 로드** ✅ / `reference/` 다이제스트를 라인번호까지 인용 / 5기준 *순차* 독립 평정 / O-2 포착·평가불가 3개·종합 보류·사람 게이트 — **Claude Code와 동일 원칙** |
| **e2e-5** | **오픈웨이트 하네스**: `scripts/open_runner.py`로 사업평가(samples) | 로컬 Ollama+**Qwen2.5-14B**(Apache-2.0 개방 가중치, **프로프라이어터리 API 전무**)로 실행 / `AGENTS.md`+`reference/` 주입 / 5기준 1~4점+근거, 종합 13→**D(안)**, **사람 게이트·한계 명시 준수** ✅ / 단 '평가 불가' 판정은 상용 하네스보다 덜 보수적(캘리브레이션 차) — **이식성 실증, 품질 동치 아님** (`docs/open-model-demo-output.md`, prompt 7,631tok) |

→ **실제 Claude Code가 CLAUDE.md 워크플로대로 작동**함을 **3회 재현**(사업평가 2회 + 품질심사 1회) 확인. "시뮬 ≠ 실물" 의심 해소. e2e-3은 슬라이스 7(가이드라인 v2) 룰브릭 적용도 입증. **e2e-4는 같은 공용 지식(`reference/`)이 Codex 하네스에서도 작동**함을 입증 — Claude Code(`.claude/`)와 Codex(`AGENTS.md`)가 *한 지식·같은 원칙*으로 평가(멀티 하네스).

---

## 2. 실제 KOICA 보고서 대조 (4건)

| 사업 | 유형 | 평가팀(인간) | DevEval Agents | 부합도 |
|---|---|---|---|---|
| 캄보디아 자궁경부암 검진 SW | CTS (6기준) | 11.7/24 **부분 성공적** | 13/24 **부분 성공적** | ✅ **등급 일치** (1.3pt 차, 독립 도출) |
| 미얀마 태양광 | 인프라 종료 (2018·4기준) | 11.33/16 성공적 | ~12/20 D(부분 성공적) | ◐ **기준별 방향 일치**(적절3·효과3·효율2 정확), 종합은 한 단계 차 |
| 파키스탄 하수처리 | 인프라 종료 (2017·정성) | 등급 없음 ("대부분 충족") | D (13.5/20) | ◐ 약점(지속가능성) **방향 일치** |
| 베트남 직업훈련 | **영향평가** | (등급 없는 영향평가) | "6기준 부적합" 인지 → 영향평가 검토관 적용 | ✅ **평가 유형 구분** 검증 |

**관찰**: 등급 체계가 같거나 명확한 2건(캄보디아·미얀마)에서 **기준별 평가 방향이 강하게 일치**. 특히 미얀마는 적절성·효과성·효율성 점수가 평가팀과 정확히 일치.

---

## 3. 게이트 작동 증거 (핵심 원칙의 실증)

- **근거 없으면 등급 없음** — 근거 전무한 일관성·지속가능성을 "평가 불가"로 (지어내지 않음)
- **의도된 함정 포착** — samples의 O-2 빈칸을 효과성·효율성 평가관이 독립적으로 잡아 감점
- **평가 불가 있으면 종합 단정 안 함** — 부분 점수만 산정, 전체 등급은 보류·단서부
- **사람 게이트** — 모든 산출물이 "최종 등급은 평가담당관이 확정"으로 종료
- **자정 사례** — 지속가능성 평가관이 한때 "편향 입력 세탁 우려"로 평가를 거부 → 맥락 보강 후 독립적 균형 평정으로 복귀 (압박에 맹종도, 근거 외면도 하지 않음)

---

## 4. 발견된 경향·한계 (정직)

**경향**
- 지속가능성·효율성에서 평가팀보다 **보수적**(재정·기술 취약을 무겁게, 근거 없으면 점수 안 줌). 좋은 엄격함일 수도, 과한 보수성일 수도 — **캘리브레이션 과제**.

**한계**
- **표본 4건** — 통계적 신뢰도엔 부족.
- **사실 추출(PART A)을 사람/보조가 수행** — 추출이 편향되면 전체가 흔들림 (미해결 과제).
- **평가팀 등급 체계 차이**(2018 4기준 16점 vs 2024 5기준 20점) — 종합 직접 비교엔 보정 필요.
- **전문가 1:1 교차검증**(동료 평가담당관이 직접 채점해 대조)은 미실시.
- **큰 PDF 직접 처리 미검증** — 109p 보고서는 추출본으로 e2e (토큰 부담).

---

> **결론**: *"작동한다"*는 입증됨(실물 e2e 2회 재현). *"평가팀과 방향 부합"*은 4건에서 관찰됨(명확 등급 2건은 기준별 일치). 단 **신뢰도는 표본 확대·전문가 교차검증으로 더 쌓아야** 한다. 현재 위치 = *실전 투입 제품 이전의, 검증된 프로토타입.*
