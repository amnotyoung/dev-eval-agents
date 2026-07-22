# DevEval Agents — 저장소 개발 컨텍스트

이 파일은 **이 저장소에서 작업할 때**(플러그인을 개발·유지보수할 때) Claude Code가 읽는 지침이다.

> ⚠️ **평가 워크플로는 여기에 없다.** 이 저장소는 그 자체가 **Claude Code 플러그인**이고, 평가 절차는 `skills/`에 있다. 플러그인 사용자에게 CLAUDE.md는 로드되지 않는다(`claude plugin validate`가 이를 경고한다) — 그래서 워크플로를 스킬로 옮겼다. **평가 절차를 고치려면 `skills/`를 고쳐라. 이 파일에 워크플로를 다시 쓰지 마라**(중복은 곧 드리프트다).

## 이 저장소 = 플러그인

```
.claude-plugin/plugin.json       매니페스트 (name: deveval)
.claude-plugin/marketplace.json  자체 배포용 마켓플레이스
skills/                          평가 워크플로 4종 ← 사용자의 실제 진입점
agents/                          전담 평가관·검증자 12명
hooks/hooks.json + boulder.sh    완료 엔진 (Stop hook)
bin/                             플러그인 활성화 시 PATH에 오르는 실행파일
reference/                       KOICA 기준 다이제스트 5종 (공용 지식)
templates/ · samples/ · scripts/ 템플릿·샘플·러너
```

| 스킬 | 하는 일 |
|------|---------|
| `/deveval:evaluate` | 사업평가 — 5~6기준 병렬 평정 → 종합점수·등급(안) |
| `/deveval:quality-review` | 평가보고서 품질심사 — 24문항/100점/A~D |
| `/deveval:impact-review` | 영향평가 방법론 검토 — 5축/10질문 |
| `/deveval:write-report` | 보고서 작성 — 작성→수치검사→서술검증→사람 |

## 개발 방법

이 저장소는 플러그인이므로, 개발 중 동작을 보려면 **플러그인으로 로드**해야 한다:

```bash
claude --plugin-dir .        # 이 저장소를 플러그인으로 올려서 테스트
claude plugin validate .     # 매니페스트·구조 검증
/reload-plugins              # 세션 중 변경사항 반영
```

`.claude/agents/`나 `.claude/settings.json`으로 되돌리지 마라 — 플러그인 레이아웃(`agents/`, `hooks/hooks.json`)이 정본이다.

## 경로 규칙 (중요)

플러그인 사용자는 **자기 작업 폴더**에서 이걸 쓴다. 저장소 안이 아니다. 따라서:

- **에이전트·스킬은 `reference/…` 상대경로로 파일을 못 찾는다.** 스킬이 `deveval-root`(bin)로 플러그인 절대경로를 얻어 **위임 프롬프트에 절대경로를 실어** 보낸다. 에이전트는 `Read/Grep/Glob`만 가져 스스로 경로를 알아낼 수 없다.
- **hooks**에서는 `${CLAUDE_PLUGIN_ROOT}`를 쓴다(플러그인 업데이트 시 경로가 바뀌므로 여기에 상태를 저장하지 마라).
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

> 학습·실험용 프로젝트다. 다른 하네스(Codex `AGENTS.md`, 오픈웨이트 `scripts/open_runner.py`)도 같은 `reference/` 지식을 공유한다 — 워크플로를 고칠 땐 그쪽 동기화도 함께 검토한다.
