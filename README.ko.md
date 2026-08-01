# DevEval Agents

*다른 언어로 읽기: [English](README.md) · **한국어**(이 파일).*

> **ODA(공적개발원조) 사업평가를 보조하는, 모델에 종속되지 않는 멀티 에이전트 프레임워크.**
> KOICA 평가 업무를 보조하는 agent 팀을 [Claude Code](https://claude.com/claude-code)·**Codex**·**오픈웨이트 모델** 세 하네스 위에서 슬라이스 단위로 직접 구현했다 (공용 지식 `reference/`는 공유).

코딩 전용 부품을 걷어내고 **도메인 무관 설계 원리**만 이 도메인에 적용한다 — 역할=권한, 근거 게이트, Rules 주입, 병렬 다각도, 검증, 완료 강제, 사람 게이트. 평가 기준·척도·규정은 **실제 KOICA 평가지침(2024)·사업평가 규정(제536호)** 기반(`reference/`).

---

## 🌍 지속가능발전목표(SDG)와의 관련성

개발원조를 근거에 기반해 더 잘 평가하는 일은 원조를 **책무성 있고 효과적으로** 만드는 장치의 일부다. 이 도구는 그 장치를 강화한다.

- **SDG 16 — 평화·정의·강력한 제도**, 특히 세부목표 **16.6**("효과적이고 책무성 있으며 투명한 제도의 발전"). 이 시스템은 출처를 단 근거, 균형 잡힌 강점·단점, 의무적인 사람 게이트로 ODA 사업평가의 품질·일관성·투명성을 높여, 개발협력의 책무성 있는 제도적 관행을 뒷받침한다.
- **SDG 17 — 목표 달성을 위한 파트너십**, 특히 **개발 효과성과 역량**에 관한 세부목표들. 모니터링·평가(M&E)의 수고를 낮추고 일관성을 높여, 효과적이고 학습 지향적인 파트너십이 기대는 평가 역량을 뒷받침한다.

**분야를 가리지 않고**(보건·에너지·물·교육·공공행정 등) ODA 사업을 평가하므로, 학습과 책무성의 환류를 개선함으로써 그 사업들이 겨냥하는 SDG를 간접적으로 뒷받침한다. 직접적인 서비스 전달 도구가 아니라 **M&E 기능을 돕는 조력자**다.

## ✅ 디지털 공공재(DPG) 준비 상태

이 저장소는 [DPG 표준](https://www.digitalpublicgoods.net/standard)의 9개 지표에 맞춰 준비되어 있다.

| # | 지표 | 근거 위치 |
|---|------|-----------|
| 1 | SDG 관련성 | 위 SDG 섹션, 그리고 `docs/dpg-application.md` |
| 2 | 승인된 오픈 라이선스 | [`LICENSE`](LICENSE)(MIT) + [`LICENSE-CONTENT`](LICENSE-CONTENT)(CC BY 4.0) |
| 3 | 명확한 소유권 | [`MAINTAINERS.md`](MAINTAINERS.md) |
| 4 | 플랫폼 독립성 | [`docs/platform-independence.md`](docs/platform-independence.md) |
| 5 | 문서화 | 이 README + [`docs/`](docs/) + 영문 번역 [`docs/en/`](docs/en/) |
| 6 | 데이터 추출·이식성 | 개방형 Markdown·평문만 사용 — [`PRIVACY.md`](PRIVACY.md) |
| 7 | 개인정보보호·준거법 | [`PRIVACY.md`](PRIVACY.md)(개인정보보호법 / GDPR) |
| 8 | 표준·모범사례 준수 | [`docs/standards.md`](docs/standards.md) |
| 9 | 설계 단계의 무해성 | [`docs/do-no-harm.md`](docs/do-no-harm.md) |

거버넌스: [`CONTRIBUTING.md`](CONTRIBUTING.md) · [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) · [`SECURITY.md`](SECURITY.md) · [`CHANGELOG.md`](CHANGELOG.md).

## 🎛️ 시스템 구성 — 12 에이전트, 두 평가 유형, 세 하네스

KOICA 평가는 **유형이 다르다.** 이 시스템은 두 유형을 구분해 다룬다.

### ① 종료평가 (Final Evaluation) — 사업을 6기준으로 평정 → **A~F 등급**

```
평가 요청 → [평가총괄: evaluate 스킬이 KOICA 기준·규정 주입]
  ▼ 6기준 평가관 병렬 (읽기전용, 각자 1~4점 + 근거; 근거 없으면 "평가 불가")
     적절성·일관성·효과성·효율성·지속가능성  [+CTS 사업은 타당성]
  ▼ quality-verifier        근거 원문 대조 + 점수–근거 정합성
  ▼ 종합점수 → A~F 등급(안)  (평가 불가 기준 있으면 단정 보류)
  ▼ report-composer(작성) → narrative-verifier(서술 검증) → report-quality-inspector(24문항 품질심사)
  ▼ 사람(평가담당관) 확정
```

#### 종료평가 6기준 — OECD DAC 평가기준 (KOICA 2024)

| DAC 기준 | 무엇을 보는가 (핵심 질문) | 종합점수 |
|---------|------------------------|:---:|
| **적절성** Relevance | 수원국·수혜자의 실제 수요·우선순위에 부합하게 설계·관리됐는가 | ✅ |
| **일관성** Coherence | 한국정부·KOICA 타 사업(내적)·타 공여기관·수원국(외적)과 상호보완·조화·중복방지 | ✅ |
| **효과성** Effectiveness | 목표·산출물을 실제로 달성했거나 달성 전망인가 (취약계층 포용 포함) | ✅ |
| **효율성** Efficiency | 투입 대비 경제적·시의적절하게 성과를 냈는가 | ✅ |
| **영향력** Impact | 장기·광범위한 전환적 효과(transformative effect)를 냈거나 낼 가능성 | ➖ 사후평가용 |
| **지속가능성** Sustainability | 종료 후에도 성과가 유지될 재정·제도·사회적 역량이 갖춰졌는가 | ✅ |
| **타당성** Validity | *(CTS·기술혁신 사업 한정)* 기술적 타당성 — 비표준 보조 기준 | ⭐ CTS만 |

- **종합점수** = 영향력을 뺀 **5개 기준**(적절성·일관성·효과성·효율성·지속가능성)을 각 **1~4점** → 합산 **20점 만점** → A~F. **영향력은 사후평가 기준**이라 종료평가 종합점수에서 제외한다. CTS 사업만 **타당성**을 더해 6기준 평균으로 4단계 평정.
- **4점 척도** — ① 명백한 부정적 영향 · ② 일부 영향 · ③ 전반적으로 양호하게 달성 · ④ 모두 달성 + 기대 이상.
- **A~F 등급** — 18↑ **A**(매우 성공적) · 16~18 **B** · 14~16 **C**(성공적) · 12~14 **D** · 10~12 **E**(부분 성공적) · 10 미만 **F**(미흡).

> 근거: `reference/KOICA-평가지침-2024-다이제스트.md` (§1·§2). 기준 체계는 DAC **6대**지만 종료평가 **채점은 5개**(영향력 제외)라는 점이 핵심.

### ② 영향평가 (Impact Evaluation) — 인과효과 측정 → **적합/조건부/부적합 (등급 없음)**

```
영향평가 보고서 → impact-evaluation-reviewer
  ▼ 5축(과학성·실용성·투명성·윤리성·포용성) / 10질문(인과식별·반사실·선택편의·강건성…)
  ▼ 적합 / 조건부 보완 / 부적합  + 🚩 기술검토(계량) 권고
  ▼ 사람(평가실·품질검토위) 확정
```

> ⚠️ 종료평가의 6기준 틀을 영향평가에 들이대지 않는다 — **평가 유형을 구분**하는 것이 핵심.

### 에이전트 카탈로그 (12)

| 역할 | 에이전트 | 권한 |
|------|---------|:---:|
| 종료평가 DAC 6기준 | `dac-{relevance,coherence,effectiveness,efficiency,sustainability,impact}-evaluator` — 영향력은 사후평가라 20점 종합 제외 | 읽기 |
| CTS 타당성 보조 (CTS만) | `cts-validity-evaluator` | 읽기 |
| 근거 검증 | `quality-verifier` | 읽기 |
| 보고서 작성 | `report-composer` | **쓰기** |
| 서술 검증 (환각·일관성) | `narrative-verifier` | 읽기 |
| 보고서 품질심사 (24문항/A~D) | `report-quality-inspector` | 읽기 |
| 영향평가 검토 (5축/10질문) | `impact-evaluation-reviewer` | 읽기 |

\+ **완료 엔진** (`hooks/boulder.sh`, Stop hook): 작업판에 미완료가 남으면 끝까지 굴린다.

## 🧬 설계 원리 → 이 시스템

| 설계 원리 | 구현 |
|---------|------|
| **병렬 다각도** | 6기준 평가관이 서로 다른 관점으로 병렬 평가 |
| **역할 = 권한** | 평가관·검증자는 읽기전용 / `report-composer`만 쓰기 |
| **근거 게이트** | "근거 없으면 등급 없음 / 서술 없음" (지어내기 금지) |
| **완료 주장 불신** | `quality-verifier`·`narrative-verifier`가 근거·일관성 검증 |
| **완료 강제** | 완료 엔진(Stop hook) — 정체·상한 가드 포함 |
| **Rules 주입** | 스킬이 KOICA 2024 지침 + 규정 제536호(`reference/` 다이제스트)를 위임 프롬프트에 주입 |
| **사람 게이트** *(공공기관 특수)* | 최종 등급·판정은 AI가 못 함, 사람 몫 |

> 코딩 전용 메커니즘은 이 도메인에 불필요해 생략하고, "근거 없으면 등급 없음"·"사람 게이트"라는 **공공기관 평가 특유의 안전장치**를 더했다.

## ▶️ 써보기

**쓰는 법 3단계** — ① 평가할 자료(사업계획서·PDM·종료보고서 등)를 Markdown·텍스트로 준비 → ② 하네스를 켜고 자료 경로와 함께 평가를 요청 → ③ 시스템이 **기준별 점수·근거 → 검증 → 종합 등급(안)**을 초안으로 제시. **최종 등급 확정은 사람(평가담당관)의 몫** — AI는 근거 있는 초안까지만 만든다(사람 게이트).

**세 가지 사용 모드 — 무엇을 요청하면 무엇이 나오나:**

| 이렇게 요청하면 | 이런 결과가 나온다 | 담당 |
|----------------|------------------|------|
| `이 사업을 DAC 기준으로 평가해줘` | 6기준 점수 + 종합 **A~F 등급(안)** | 종료평가팀 (6기준 평가관) |
| `이 영향평가 보고서를 검토해줘` | 인과추론·방법론 심사 → **적합/조건부/부적합** | `impact-evaluation-reviewer` |
| `이 평가보고서 품질을 검토해줘` | 24문항 메타심사 → 품질등급 **A~D** | `report-quality-inspector` |

> 처음이라면 동봉된 가상 샘플 [`samples/sample-evaluation-report.md`](samples/sample-evaluation-report.md)로 종료평가를 돌려 보라 — 일부 성과지표를 **일부러 비워 둬**서, "근거 없으면 평가 불가" 게이트가 실제로 작동하는 걸 볼 수 있다.

**Claude Code — 플러그인으로 설치** (권장: 이 저장소 안이 아니라 *자기 작업 폴더*에서 쓴다):
```bash
/plugin marketplace add amnotyoung/dev-eval-agents
/plugin install deveval@deveval-agents
/reload-plugins
```
그다음, 평가 자료가 있는 폴더 어디서든:

| 스킬 | 하는 일 |
|------|---------|
| `/deveval:evaluate` | 사업평가 — 5~6기준 병렬 평정 → 종합점수·등급(안) |
| `/deveval:quality-review` | 평가보고서 품질심사 — 24문항/100점/A~D |
| `/deveval:impact-review` | 영향평가 방법론 검토 — 5축/10질문 |
| `/deveval:write-report` | 보고서 작성 — 작성→수치검사→서술검증→사람 |

작업 산출물(`.omo/eval-plan.md`, `.omo/draft-report*.md`)은 **사용자 폴더**에 남는다 — 플러그인 디렉토리는 읽기전용 지식이다. 플러그인이 켜져 있는 동안 동봉된 `deveval-consistency-check` 명령이 `PATH`에 오른다.

설치 없이 써 보려면(또는 개발하려면):
```bash
git clone https://github.com/amnotyoung/dev-eval-agents
claude --plugin-dir ./dev-eval-agents
```

**Codex** (`AGENTS.md` 단일 에이전트 순차 독립 평정):
```bash
codex exec "samples/sample-evaluation-report.md 이 사업을 DAC 기준으로 평가해줘"
```
**오픈웨이트 모델** (독점 API 없이 — [Ollama](https://ollama.com) + 오픈 가중치):
```bash
ollama pull qwen2.5:14b
python3 scripts/open_runner.py --out docs/open-model-demo-output.md
```
무료 Google Colab로도 재현 가능: [`notebooks/open-model-demo.ipynb`](notebooks/open-model-demo.ipynb).

## 🔌 권장 동반 설치 — ODA Intelligence 플러그인 (선택)

DevEval의 증거 게이트는 "근거 없으면 등급 없음"이다. 같은 관리자의
[ODA Intelligence 플러그인](https://github.com/amnotyoung/oda-intelligence-plugin)을
함께 설치하면 **대조 가능한 근거의 범위**가 넓어진다 — 공개 read-only MCP
게이트웨이 도구 29종: 국가 지표·타 공여기관 활동(IATI·세계은행 등, 적절성·일관성),
같은 나라 한국 ODA 사업 지도(중복·연계 확인), KOICA 규정 조문 전문, 그리고
보고서가 인용한 조문의 실재를 검증하는 `verify_citation`.

```bash
/plugin marketplace add amnotyoung/oda-intelligence-plugin
/plugin install oda-intelligence@oda-intelligence-plugin
```

**엄격히 선택 사항** — 커넥터가 없어도 모든 워크플로는 그대로 돌고, 산출물에
"외부 맥락 증거 미보강"이 한계로 남을 뿐이다(플랫폼 독립성 무영향). 연동 시에도
증거 규율은 그대로다: 상태 도구 먼저, 소스 부재는 0이 아니며, 게이트웨이 증거는
사업 문서를 **보강**할 뿐 대체하지 않는다. 상세:
[`docs/oda-intelligence-integration.md`](docs/oda-intelligence-integration.md).

## ✅ 검증 (Validation)

실제로 작동하고 실제 KOICA 평가와 부합하는지의 기록 → **[`docs/validation-log.md`](docs/validation-log.md)**

- **실물 e2e 4회** — Claude Code(`claude -p`, `.claude/agents/*`) 3회 + **Codex(`codex exec`, `AGENTS.md`) 1회** (시뮬레이션 아님)
- **실제 보고서 4건 대조** — 캄보디아(등급 일치)·미얀마(기준별 방향 일치)·파키스탄(약점 방향 일치)·베트남(평가 유형 구분)
- **게이트 실증** — 근거 없으면 평가 불가·종합 보류·사람 게이트가 실제로 작동
- ⚠️ 학습·실험 자체검증(표본 소수). 전문가 교차검증·표본 확대는 진행 과제.

## 🔌 플랫폼 독립성

필수 의존 대상은 *유능한 LLM 에이전트 하네스*라는 **범주**이지 특정 상용 제품이 아니다. 같은 에이전트가 Claude Code·Codex·오픈웨이트 모델(Qwen2.5, Apache-2.0)에서 **핵심 산출물의 변경 없이** 동작한다. 전체 근거: [`docs/platform-independence.md`](docs/platform-independence.md).

## 🗺️ 로드맵

슬라이스 1~8 완료 — 변경 이력은 [`CHANGELOG.md`](CHANGELOG.md) 참조.

- ✅ **슬라이스 1~1.6**: 효과성 평가관 → KOICA 길라잡이 2024 반영 (DAC 6대 기준, A~F 공식 등급척도, 4점 루브릭)
- ✅ **슬라이스 2 / 2.5**: 6기준 병렬 평가팀 + 종합점수→A~F (병렬 다각도) / CTS 타당성 평가관 추가
- ✅ **슬라이스 3**: 완료 엔진 — Stop hook으로 긴/다건 평가를 끝까지
- ✅ **슬라이스 4**: 평가보고서 품질심사관 — 보고서를 24문항/A~D로 심사 (메타 평가)
- ✅ **슬라이스 5**: 보고서 작성 지원 — `report-composer`(쓰기) + `narrative-verifier`. "근거 없으면 서술 없음"
- ✅ **슬라이스 6**: 영향평가 검토 모듈 + 사업평가 규정(제536호) 규정 근거 주입
- ✅ **슬라이스 7**: 품질심사관 공식 v2 반영 — 「평가품질검토 가이드라인 v2」(2025.6)로 갱신. **Pass 경계 70→60 교정**, 세부항목 v2 명칭·매핑, 총평 200자, 평가용역 종합등급 산정표 신설
- ✅ **슬라이스 8**: **멀티 하네스** — `AGENTS.md`(Codex판 지침) 추가로 Claude Code(`.claude/`)·Codex(`AGENTS.md`)에서 작동, 공용 지식(`reference/`) 공유. `codex exec` e2e 검증. 여기에 **오픈웨이트 모델**(Qwen2.5 등, `scripts/open_runner.py` — 독점 API 없음)까지 더해 **세 번째 스택**을 실증 → 총 **세 하네스**(플랫폼 독립성)

## 📜 라이선스

DPGA가 승인한 오픈 라이선스로 이중 배포한다.

- **소프트웨어**(shell hook, 설정, 러너 스크립트, 노트북) — **MIT**, [`LICENSE`](LICENSE) 참조.
- **문서·콘텐츠**(Markdown 에이전트, `reference/` 다이제스트, 템플릿, 샘플, docs) — **CC BY 4.0**, [`LICENSE-CONTENT`](LICENSE-CONTENT) 참조.

`reference/` 다이제스트는 공개적으로 문서화된 KOICA·KIEP 평가 실무를 이 프로젝트가 **직접** 서술하고 출처를 표기한 것이며, 원본 PDF·HWP는 재배포하지 않는다. [`MAINTAINERS.md`](MAINTAINERS.md) 참조.

## 📚 reference (KOICA 공식 자료 다이제스트)

원본 PDF·HWP는 저작권 고려해 미포함(`.gitignore`), 추출 다이제스트만 보관:
- `KOICA-평가지침-2024-다이제스트.md` (종료평가 기준·등급척도) / `KOICA-평가지침-다이제스트.md` (2017 구버전)
- `KOICA-품질검토-체크리스트.md` (24문항/A~D)
- `KOICA-영향평가-가이드라인-다이제스트.md` (KIEP 2025)
- `KOICA-사업평가규정-다이제스트.md` (규정 제536호, 2025.2 — 우리 시스템의 규정적 근거)

## 📌 출처와 상태

평가 기준·규정은 KOICA 공식 자료에서 추출(원본 미포함, 다이제스트만). **독립적·비공식** 학습·실험용 개인 프로젝트로, KOICA와 제휴·후원 관계가 없다. 설계 계보 표기·소유권은 [`MAINTAINERS.md`](MAINTAINERS.md) 참조. 이전 이름: `oh-my-oda-agent`(리포 리네임, 옛 링크 리다이렉트).
