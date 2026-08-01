# ODA Intelligence 게이트웨이 연동 (선택) / Optional Evidence Gateway

> **English summary.** The [ODA Intelligence plugin](https://github.com/amnotyoung/oda-intelligence-plugin)
> (same maintainer) is an **optional companion**: one public, read-only MCP
> gateway exposing 29 evidence tools — country indicators and other donors'
> activities, the Korean ODA project map, development-trend documents,
> partner-country procurement models, and KOICA regulation full text with
> citation verification (`verify_citation`). DevEval has **no hard dependency**
> on it: every workflow runs unchanged without the connector and simply records
> that external context was not augmented (see `CONTRIBUTING.md`, "keep it
> model-agnostic", and DPG Indicator 4 in `docs/platform-independence.md`).
> With the connector, the same evidence discipline applies — status tools
> first, a missing source is **not** a zero, and gateway evidence **augments,
> never replaces**, the project documents.

## 왜 연동하나

DevEval의 증거 게이트는 "근거 없으면 등급 없음"이다. 그런데 평가관이 대조할 수
있는 근거는 기본적으로 **사용자가 준 사업 문서**뿐이다. 게이트웨이는 대조 가능한
근거의 범위를 넓힌다:

- **적절성** — 수원국 지표·인도적 맥락·현지 동향과 사업 설계를 대조한다.
- **일관성** — 같은 나라의 다른 한국 ODA 사업(중복·연계), 타 공여기관
  활동(IATI)과 대조한다.
- **규정 근거** — KOICA 규정 조문을 **전문**으로 인용하고, 보고서가 인용한
  조문이 **실재하는지** 검증한다.

이 프레임워크의 규정적 근거인 **사업평가 규정(제536호)** 도 게이트웨이의 규정
인덱스에 색인되어 있어, 다이제스트(`reference/KOICA-사업평가규정-다이제스트.md`)를
넘어 조문 원문 확인이 가능하다.

## 무엇이 어느 국면에 쓰이나

| 평가 국면 | 게이트웨이 증거 | 대표 도구 |
|---|---|---|
| 적절성 (Relevance) | 국가 지표·인도적 맥락, 현지 정책·동향 | `country_report_context` · `country_humanitarian_context` · `search_development_trends` |
| 일관성 (Coherence) — 내적 | 같은 나라의 한국 ODA 사업 (중복·연계 확인) | `oda_map_projects` · `oda_map_project_detail` |
| 일관성 (Coherence) — 외적 | 타 공여기관 활동(IATI), 협력관계 신호 | `iati_query_country` · `search_entity_relationships` |
| 효율성·지속가능성 | 수원국 조달·거버넌스·사업형성 맥락 | `procurement_country_context` · `procurement_model_detail` |
| 영향력 (사후) | 국가 수준 지표 (세계은행·WHO 등) | `country_report_context` |
| 보고서 작성·품질심사 | 규정 조문 전문 · 인용 실재 검증 · 조문 관계 | `search_regulation` · `get_article` · `verify_citation` · `find_references` |

**효과성(Effectiveness)의 1차 근거는 여전히 사업 문서다**(종료보고서·PDM·
성과지표). 게이트웨이는 사업 내부 성과 데이터를 갖고 있지 않다 — 어떤 기준에서든
게이트웨이 증거로 사업 문서의 공백을 "달성"으로 메우지 마라.

## 설치

**Claude Code** — 플러그인으로 설치(권장):

```bash
/plugin marketplace add amnotyoung/oda-intelligence-plugin
/plugin install oda-intelligence@oda-intelligence-plugin
```

설치되면 `oda-intelligence` 커넥터의 read-only 도구 29종이 세션에 나타난다.
인증·토큰은 필요 없다.

**Codex** — Codex의 MCP 서버 설정에 공개 게이트웨이 URL을 추가한다(무인증,
streamable HTTP):

```text
https://oda-mcp.fly.dev/oda-intelligence/v2/mcp
```

**오픈웨이트 러너**(`scripts/open_runner.py`) — MCP 미연동. 연동 없이 동작하는
것이 정상이다.

## 증거 규율 (연동 시에도 그대로)

게이트웨이를 쓴다고 증거 게이트가 느슨해지는 게 아니다. 오히려 다음 규율이
**추가**된다:

1. **상태 도구 먼저.** `oda_map_data_status` · `country_data_status` ·
   `procurement_model_status` · `list_available_corpora`가 각 소스의 현재 상태를
   보고한다. 상태 확인 없이 부른 증거 도구는 얇은 답을 완전한 답처럼 보이게
   한다.
2. **missing ≠ 0.** `stale` · `no_data` · `disabled` · `error`는 "증거가 관측되지
   않았다"는 뜻이지, 수량이 0이거나 위험이 없다는 뜻이 아니다. 그 상태 그대로
   인용한다.
3. **출처·상태 라벨.** 게이트웨이에서 온 항목은
   `[근거: 게이트웨이/<소스>, <상태>, <조회일>]`처럼 출처와 조회 상태를 함께
   단다.
4. **보조 맥락 원칙.** 평가 대상 사업 문서가 1차 근거다. 게이트웨이 증거는 맥락
   대조용이다.
5. **관계 추출은 신호.** `search_entity_relationships`가 돌려주는 관계는 근거
   문서를 확인한 뒤에만 인용한다.
6. **내부규정 인덱스 한정.** `verify_citation`은 KOICA 내부규정 인덱스만
   대조한다. 외부 법령(국가법령) 인용은 이 검사로 확정하지 마라.

## 워크플로별 진입점

- `/deveval:evaluate` — **게이트웨이 증거 보강 (선택)** 단계: 위임 전에 맥락
  증거를 수집해 증거 블록으로 평가관에게 전달한다.
- `/deveval:write-report` — **(선택) 규정 인용 검증** 단계: 초안의
  `{규정명} 제N조` 인용을 `verify_citation`으로 대조한다.
- `/deveval:quality-review` — **규정 인용 검증 (선택)** 절: 심사 대상 보고서의
  조문 인용 실재를 확인한다.
- Codex `AGENTS.md` — **외부 증거 보강 (선택 — MCP)** 절.

## 의존성 경계

- **하드 의존성 없음.** 커넥터가 없으면 각 단계는 건너뛰고, 산출물 한계에 "외부
  맥락 증거 미보강"으로 기록된다. 코어 산출물(점수·등급안·보고서)은 커넥터
  유무와 무관하게 생성된다.
- 게이트웨이는 공개·무인증·read-only이며, 이 저장소는 게이트웨이 코드를 포함하지
  않는다. 반대 방향도 마찬가지다 — 게이트웨이는 이 저장소에 의존하지 않는다.
- 데이터 출처·재사용 조건·공개 범위는 게이트웨이 저장소
  ([oda-intelligence-plugin](https://github.com/amnotyoung/oda-intelligence-plugin))의
  문서를 따른다.
