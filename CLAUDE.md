# DevEval Agents — 저장소 개발 컨텍스트

이 파일은 **이 저장소에서 작업할 때**(플러그인을 개발·유지보수할 때) Claude Code가 읽는 지침이다.

> ⚠️ **평가 워크플로는 여기에 없다.** 이 저장소는 그 자체가 **Claude Code·Codex 공용 플러그인**이고, 평가 절차는 `skills/`에 있다. 설치형 플러그인 사용자에게 CLAUDE.md는 로드되지 않는다 — 그래서 워크플로를 스킬로 옮겼다. **평가 절차를 고치려면 `skills/`를 고쳐라. 이 파일에 워크플로를 다시 쓰지 마라**(중복은 곧 드리프트다).

## 이 저장소 = 플러그인

```
.claude-plugin/plugin.json       매니페스트 (name: deveval)
.claude-plugin/marketplace.json  자체 배포용 마켓플레이스
.codex-plugin/plugin.json        Codex 매니페스트 (같은 name/version)
.agents/plugins/marketplace.json Codex 저장소 마켓플레이스
skills/                          평가 워크플로 4종 ← 사용자의 실제 진입점
agents/                          전담 평가관·검증자 12명
hooks/hooks.json + boulder.sh    완료 엔진 (Stop hook)
bin/                             Claude가 PATH에 올리는 실행파일(Codex는 절대경로 폴백)
reference/                       KOICA 기준 다이제스트 5종 (공용 지식)
templates/ · samples/ · scripts/ 템플릿·샘플·러너
```

| 스킬 | 하는 일 |
|------|---------|
| `deveval:evaluate` | 사업평가 — 5~6기준 병렬 평정 → 종합점수·등급(안) |
| `deveval:quality-review` | 평가보고서 품질심사 — 24문항/100점/A~D |
| `deveval:impact-review` | 영향평가 방법론 검토 — 5축/10질문 |
| `deveval:write-report` | 보고서 작성 — 작성→수치검사→서술검증→사람 |

Claude Code는 `/deveval:<skill>`, Codex는 `$deveval:<skill>` 문법으로 호출한다.

## 개발 방법

Claude 쪽 개발 동작은 **플러그인으로 로드**해 확인한다:

```bash
claude --plugin-dir .        # 이 저장소를 플러그인으로 올려서 테스트
claude plugin validate .     # 매니페스트·구조 검증
/reload-plugins              # 세션 중 변경사항 반영
```

결정적 컴포넌트(수치 검사기·완료 엔진·매니페스트 정합)는 CI(`checks`)가 지키는 테스트가 있다 — 로컬에서도 돌려라:

```bash
python3 -m unittest discover -s tests   # 수치 검사기 회귀 (픽스처 = 실제 사고 유형)
bash tests/test_boulder.sh              # 완료 엔진(Stop hook) 동작
bash scripts/check-manifest-sync.sh     # 4개 매니페스트 이름·버전 일치
```

`.claude/agents/`나 `.claude/settings.json`으로 되돌리지 마라 — 공용 플러그인 레이아웃(`skills/`, `agents/`, `hooks/hooks.json`)이 정본이다. Codex 매니페스트는 plugin-creator 검증기로 별도 검사한다.

**한국어 정본을 고치면 `docs/en/` 미러도 같은 PR에서 고쳐라.** `CLAUDE.md`·`AGENTS.md`·`agents/`·`reference/`가 대상이고, CI(`mirror-sync`)가 한쪽만 바뀐 PR을 막는다. 한쪽만 바꾸는 것이 의도된 PR에는 `mirror-sync-exempt` 라벨을 붙인다.

```bash
bash scripts/check-mirror-sync.sh            # PR 모드 — origin/main과의 변경분 검사
bash scripts/check-mirror-sync.sh --audit    # 감사 모드 — 저장소 전체의 미러 최신성
```

## 경로 규칙 (중요)

플러그인 사용자는 **자기 작업 폴더**에서 이걸 쓴다. 저장소 안이 아니다. 따라서:

- **에이전트·스킬은 `reference/…` 상대경로로 파일을 못 찾는다.** 스킬은 `deveval-root`가 있으면 사용하고, 없으면 로드된 `SKILL.md` 위치에서 루트를 계산한 뒤 **위임 프롬프트에 절대경로를 실어** 보낸다. Codex에서는 역할별 `agents/*.md`도 절대경로로 읽혀야 한다.
- **수치 검사기**는 bare command가 없으면 `<root>/scripts/consistency_check.py`를 절대경로로 실행한다.
- **hooks**에서는 Codex도 호환 제공하는 `${CLAUDE_PLUGIN_ROOT}`를 쓴다(플러그인 업데이트 시 경로가 바뀌므로 여기에 상태를 저장하지 마라).
- **평가자의 산출물**(`.omo/eval-plan.md`, `.omo/draft-report*.md`)은 **사용자 작업 폴더**에 만든다. 플러그인 디렉토리에 쓰지 마라.

## 원칙 (스킬·에이전트 전체에 공통)

1. **근거 없으면 등급 없음** — 데이터 없으면 "근거 불충분 → 평가 불가"(지어내기 금지)
2. 미검증은 `[INFO: 확인 필요]`
3. AI는 **잠정 점수·등급(안)**만 — **최종 확정은 사람(평가담당관)**
4. 강점·단점 균형 + 한계 명시
5. 평가윤리 — 조사대상자 익명, 평가 독립성

이 원칙을 바꾸면 `skills/` 4개 전부와 관련 에이전트를 함께 고쳐야 한다.

## 규정적 근거

- `reference/KOICA-평가지침-2024-다이제스트.md` — 기준·4점척도·A~F (주 자산). `KOICA-평가지침-다이제스트.md`는 2017 구버전(비교용)
- `reference/KOICA-사업평가규정-다이제스트.md` — 규정 제536호(2025.2): 제6조 기준·제7조 유형·제27~28조 품질검토·제5조 원칙·제19조 독립성·제6장 윤리
- `reference/KOICA-품질검토-체크리스트.md` — 품질심사 v2 룰브릭
- `reference/KOICA-영향평가-가이드라인-다이제스트.md` — 영향평가(KIEP 2025)

사실·결론과 가치판단·제언을 명확히 구분하고(제5조 투명성), 평가 독립성(제19조: 일방적 수정·삭제 요구 금지)을 침해하지 않는다.

## 선택적 게이트웨이 연동 (oda-intelligence)

스킬 3종(evaluate·write-report·quality-review)과 Codex `AGENTS.md`에는 **선택적** 외부 증거 보강이 있다 — 같은 관리자의 `oda-intelligence` 플러그인(공개 read-only MCP 게이트웨이)이 설치된 세션에서만 동작하고, 없으면 건너뛴다(하드 의존 아님 — CONTRIBUTING의 model-agnostic 원칙과 DPG 지표 4를 지키는 조건). 연동 규칙·도구 매핑의 정본은 `docs/oda-intelligence-integration.md`. 연동 부분을 고치면 스킬·`AGENTS.md`·통합 문서를 함께 동기화한다. 에이전트 파일은 건드리지 않는 설계다 — 증거는 위임 프롬프트에 실리는 자기서술형 블록으로 전달된다.

> 학습·실험용 프로젝트다. Codex 설치형 플러그인, Codex `AGENTS.md` 직접 실행 폴백, 오픈웨이트 `scripts/open_runner.py`가 같은 `reference/` 지식을 공유한다 — 워크플로를 고칠 땐 모두의 동기화를 검토한다.
