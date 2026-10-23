"""스킬 실행 규칙 회귀 테스트 — 실제 헤드리스 e2e(2026-10-22)에서 평가가 멈춘 원인들.

- 평가총괄이 사실대장 담당을 백그라운드로 띄운 뒤 차례를 끝냈고, 헤드리스 실행이 10분 뒤
  그 작업들을 종료해 기준 평가관·검증자가 한 번도 호출되지 않았다.
- 여러 사업 합본인데 작업판을 만들지 않아 완료 엔진(Stop hook)이 무장되지 않았다.
- 플러그인 폴더에 `ls`·`cp`를 써서 권한 확인에 걸렸다(작업 폴더 밖).
- 산출물 경로가 `.omo/` 한 곳으로 고정돼 합본의 사업들이 섞일 수 있었다.
"""

import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = ("evaluate", "quality-review", "impact-review", "write-report")


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


class DelegationRuns(unittest.TestCase):
    def test_host_adapters_do_not_require_an_unsupported_background_parameter(self):
        for name in SKILLS:
            body = read("skills", name, "SKILL.md")
            self.assertIn("해당 매개변수를 지원하는 위임 도구에서만", body)
            self.assertIn("모든 결과를 기다린 뒤", body)

    def test_codex_writer_roles_keep_scoped_write_permissions(self):
        body = read("skills", "evaluate", "SKILL.md")
        self.assertIn("읽기 전용 제약은 기준 평가관·검증자에만 적용", body)
        self.assertIn("산출물의 쓰기·수정과 검사 실행을 허용", body)

    def test_every_skill_delegates_in_the_foreground(self):
        for name in SKILLS:
            body = read("skills", name, "SKILL.md")
            self.assertIn("포그라운드", body, name)
            self.assertIn("차례를 끝내지 않는다", body, name)
            # v5 e2e: 값을 비운 위임이 비동기로 돌아 평가총괄이 sleep 대기를 7번 되풀이했다
            self.assertIn("`run_in_background: false`를 **명시한다**", body, name)

    def test_long_conversion_is_awaited_not_backgrounded(self):
        body = read("skills", "evaluate", "SKILL.md")
        self.assertNotIn("백그라운드로 돌린다", body)
        self.assertIn("끝날 때까지 기다린다", body)


class PlanBoardAlwaysArmsTheStopHook(unittest.TestCase):
    def test_evaluate_creates_a_plan_for_every_evaluation(self):
        body = read("skills", "evaluate", "SKILL.md")
        self.assertIn("평가마다(사업이 하나여도) 작업판을 만든다", body)
        self.assertIn(".omo/eval-plan.md", body)
        self.assertNotIn("긴 평가나 여러 사업을 함께 평가할 때는", body)

    def test_plan_template_matches(self):
        plan = read("templates", "eval-plan-template.md")
        self.assertIn("평가마다", plan)
        self.assertIn("사업 경계 판별", plan)
        self.assertIn(".omo/<사업 약칭>/", plan)


class PluginFolderIsReadNotShelled(unittest.TestCase):
    def test_no_shell_copy_of_templates(self):
        for name in SKILLS:
            body = read("skills", name, "SKILL.md")
            self.assertIsNone(re.search(r"\.md`?를 [^\n]{0,60}\.omo/[^\n]{0,80}로 복사", body), name)
        self.assertIn("Read·Write로 옮긴다", read("skills", "evaluate", "SKILL.md"))
        self.assertNotIn("로 복사해", read("templates", "eval-plan-template.md"))

    def test_plugin_root_is_checked_with_read_tools(self):
        for name in SKILLS:
            self.assertIn("Glob 같은 읽기 도구로", read("skills", name, "SKILL.md"), name)


class PerProjectFolders(unittest.TestCase):
    def test_brief_matrix_and_draft_live_in_the_project_folder(self):
        evaluate = read("skills", "evaluate", "SKILL.md")
        self.assertIn(".omo/<사업 약칭>/auditable-evaluation-brief.md", evaluate)
        self.assertIn(".omo/<사업 약칭>/evaluation-design-matrix.md", evaluate)
        self.assertIn("합본", evaluate)
        self.assertNotIn("`.omo/auditable-evaluation-brief.md`", evaluate)
        self.assertIn(".omo/<사업 약칭>/draft-report", read("skills", "write-report", "SKILL.md"))
        self.assertIn(".omo/<사업 약칭>/draft-report", read("agents", "report-composer.md"))
        self.assertIn(".omo/<project-slug>/draft-report", read("docs", "en", "agents", "report-composer.md"))
        self.assertIn(".omo/<사업 약칭>/auditable-evaluation-brief.md", read("AGENTS.md"))
        self.assertIn(".omo/<project-slug>/auditable-evaluation-brief.md", read("docs", "en", "AGENTS.md"))

    def test_redelegation_does_not_leak_other_criteria_scores(self):
        body = read("skills", "evaluate", "SKILL.md")
        self.assertIn("1·2절만", body)
        self.assertIn("3·4절은 넘기지 않는다", body)


if __name__ == "__main__":
    unittest.main()
