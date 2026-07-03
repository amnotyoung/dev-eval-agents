# 검증 기록 (Validation Log)

> DevEval Agents가 ① **실제로 작동하는가**(실물 e2e) ② **실제 KOICA 평가 결과와 부합하는가**(대조)의 기록.
>
> ⚠️ **학습·실험 프로젝트의 자체 검증**이며 공식 검증이 아니다. 표본 소수(4건), 한계 존재(§4). 최종 갱신: 2026-07-03 (영향평가 트랙 실물 **e2e-6·e2e-7** 추가 — 실제 KOICA 영향평가 보고서 대상, 신규 `dac-impact-evaluator` 첫 실물 검증).

---

## Summary (English)

> This log records two things: **(1) does the system actually run** (live
> end-to-end tests) and **(2) does it agree with real KOICA evaluations**
> (comparison). ⚠️ This is **self-validation of a learning/research project, not
> an official validation** — small sample (4 comparisons), with limitations in
> §4. Last updated 2026-07-03 (added the impact-track live runs e2e-6/e2e-7 on a real
KOICA impact-evaluation report). The detailed
> tables below are kept in Korean (the working language of the KOICA source
> material); this section is a full English synopsis for reviewers.

**1. Live end-to-end runs (does it actually work).** Seven headless runs — not
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
- **e2e-6** — a **real KOICA impact-evaluation report** (Nghệ An Industrial-Technical
  School, 158 pp.) reviewed for methodology: `impact-evaluation-reviewer` fired (36
  stream events, **zero other sub-agents → correctly routed to the impact reviewer,
  not the 6-criteria team**); the 5-axis/10-question rubric returned **"not adequate
  as a rigorous impact evaluation (RIE)"**, transparency high, 🚩 technical review
  recommended. It caught the missing treatment dummy in the wage regression, the
  "starting = average wage" assumption, and a sampling self-contradiction, and
  flagged unreadable table images as `[INFO: needs confirmation]`. 5 turns, ~5.4 min.
- **e2e-7** — the same report, this time to **assess the project's Impact (영향력)
  criterion**: the **new `dac-impact-evaluator` fired for the first time on real
  material** (48 stream events, zero other sub-agents) → Impact **3/4** (generally
  good, at the *contribution* level), explicitly **excluded from the 20-point
  composite**, regional/equity/unintended effects marked *"cannot evaluate"*, causal
  language held to contribution, human gate. Confirms the new agent's **role
  separation** from `impact-evaluation-reviewer`. 4 turns, ~4 min.

→ The Claude Code workflow was reproduced **3×** (2 project evaluations + 1
quality inspection); e2e-4 and e2e-5 show the **same shared knowledge runs on
Codex and on a fully open-weight stack** (multi-harness). e2e-6/e2e-7 add the
**impact track**: on a real KOICA impact-evaluation report, the report-methodology
reviewer and the new Impact-criterion evaluator each fired and routed correctly,
handling the same project in two distinct roles.

**2. Comparison against real KOICA reports (4 cases).**

| Project | Type | Human team | DevEval Agents | Agreement |
|---|---|---|---|---|
| Cambodia cervical-cancer screening SW | CTS (6-criteria) | 11.7/24 *partially successful* | 13/24 *partially successful* | ✅ **grade match** (1.3 pt apart, derived independently) |
| Myanmar solar | infra, completion (2018, 4-criteria) | 11.33/16 *successful* | ~12/20 **D** *partially successful* | ◐ **per-criterion direction match** (relevance 3 / effectiveness 3 / efficiency 2 exact); aggregate one band off |
| Pakistan wastewater | infra, completion (2017, qualitative) | no grade ("mostly met") | **D** (13.5/20) | ◐ weakness (sustainability) **direction match** |
| Vietnam — Nghệ An Industrial-Technical School | **impact evaluation** (ex-post) | completion eval **93/100** (2009), "successful" (2011) → impact eval **favorable** (2017) | reviewer: report **not adequate as RIE** / Impact evaluator: **3/4** (good, *contribution* level) — *live e2e-6/e2e-7* | ◐ **direction matches** (positive individual outcomes); AI **more conservative** — human "favorable" vs AI contribution-only, regional/equity *"cannot evaluate"* |

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

**Conclusion:** *"it runs"* is demonstrated (**seven live e2e runs** — the correct
sub-agent fires and routes each time, including the new `dac-impact-evaluator`);
*"it agrees in direction with the evaluation teams"* is observed across 4 cases
(per-criterion match in the 2 clear-grade cases; the Vietnam impact case shows
direction agreement with the human team, with the AI more conservative on causal
attribution). Reliability still needs a larger sample and expert cross-validation. Current stage = a **validated prototype, ahead of
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
| **e2e-6** | **실제 KOICA 영향평가 보고서**(응에안성 산업기술학교, 158p) 방법론 검토 요청 | `impact-evaluation-reviewer` 호출 ✅ (스트림 36이벤트, **다른 서브에이전트 0 → 6기준팀 아닌 영향평가 검토관으로 정확 라우팅**) / 5축·10질문 → **부적합(RIE)**·투명성 상·🚩기술검토 권고 / 표43 처치더미 부재·각주9 가정·표집 내부모순까지 포착, 도표 이미지 판독불가는 `[INFO 확인 필요]`로 플래그 / 5턴·~5.4분·$1.49 (PDF→텍스트 추출본 입력) |
| **e2e-7** | 같은 보고서로 **사업 영향력(Impact) 기준 평정** 요청 | **신규 `dac-impact-evaluator` 호출 ✅** (스트림 48이벤트, 다른 서브에이전트 0) — 신규 에이전트 **첫 실물** / 영향력 **3/4**(양호·기여 수준), **종합 미포함** 명시, 지역·형평성·부작용 "평가 불가", 인과→기여로 절제, 사람 게이트 / 4턴·~4분·$1.32. **`impact-evaluation-reviewer`(보고서 심사)와 역할 분리 실증** |

→ **실제 Claude Code가 CLAUDE.md 워크플로대로 작동**함을 **3회 재현**(사업평가 2회 + 품질심사 1회) 확인. "시뮬 ≠ 실물" 의심 해소. e2e-3은 슬라이스 7(가이드라인 v2) 룰브릭 적용도 입증. **e2e-4는 같은 공용 지식(`reference/`)이 Codex 하네스에서도 작동**함을 입증 — Claude Code(`.claude/`)와 Codex(`AGENTS.md`)가 *한 지식·같은 원칙*으로 평가(멀티 하네스). **e2e-6·e2e-7**은 **영향평가 트랙**(보고서 방법론 심사 `impact-evaluation-reviewer` + 사업 영향력 평정 신규 `dac-impact-evaluator`)이 **실제 KOICA 영향평가 보고서**(응에안성 산업기술학교)에서 **실물 발화·정확 라우팅**(각 런 다른 서브에이전트 0)함을 입증 — 신규 `dac-impact-evaluator`의 첫 실물 검증 포함. 두 런은 같은 사업을 *다른 역할*(보고서 심사 vs 사업 영향력 평정)로 처리해 **역할 분리**도 실증.

---

## 2. 실제 KOICA 보고서 대조 (4건)

| 사업 | 유형 | 평가팀(인간) | DevEval Agents | 부합도 |
|---|---|---|---|---|
| 캄보디아 자궁경부암 검진 SW | CTS (6기준) | 11.7/24 **부분 성공적** | 13/24 **부분 성공적** | ✅ **등급 일치** (1.3pt 차, 독립 도출) |
| 미얀마 태양광 | 인프라 종료 (2018·4기준) | 11.33/16 성공적 | ~12/20 D(부분 성공적) | ◐ **기준별 방향 일치**(적절3·효과3·효율2 정확), 종합은 한 단계 차 |
| 파키스탄 하수처리 | 인프라 종료 (2017·정성) | 등급 없음 ("대부분 충족") | D (13.5/20) | ◐ 약점(지속가능성) **방향 일치** |
| 베트남 응에안성 산업기술학교 (직업훈련) | **영향평가**(사후) | 종료평가 **93점**(2009)·"성공적"(2011) → 영향평가 **긍정적 영향**(2017) | 검토관: 보고서 **부적합(RIE)**·투명성 상 / 영향력 평가관: **3/4**(양호·기여 수준, 종합 미포함) — *e2e-6·e2e-7 실물* | ◐ **방향 일치**(개인성과 긍정), 단 AI가 **더 보수적** — 인간 'favorable' vs AI 인과→기여·지역/형평성 "평가 불가" |

**관찰**: 등급 체계가 같거나 명확한 2건(캄보디아·미얀마)에서 **기준별 평가 방향이 강하게 일치**. 특히 미얀마는 적절성·효과성·효율성 점수가 평가팀과 정확히 일치. **베트남(영향평가)**은 인간의 favorable 결론과 AI의 '양호(기여 수준)'가 **방향 일치**하되, AI가 **인과 귀속에 더 보수적**(같은 데이터를 더 엄격한 근거기준으로 재평가한 것 — AI는 독립 데이터원이 아니라 보완적 규율 장치).

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

> **결론**: *"작동한다"*는 입증됨(**실물 e2e 7회** — 종료평가·품질심사·멀티하네스 + 영향평가 방법론 검토·사업 영향력 평정, 각 회차 서브에이전트 실제 호출·정확 라우팅 확인). *"평가팀과 방향 부합"*은 4건에서 관찰됨(명확 등급 2건 기준별 일치 + 베트남 영향평가는 방향 일치·AI 더 보수적). 단 **신뢰도는 표본 확대·전문가 교차검증으로 더 쌓아야** 한다. 현재 위치 = *실전 투입 제품 이전의, 검증된 프로토타입.*
