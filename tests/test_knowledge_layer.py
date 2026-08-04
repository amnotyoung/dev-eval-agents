"""공용 지식층의 존재·우선순위·스킬 라우팅 회귀 테스트.

방법론 파일이 추가돼도 KOICA 공식 규범층을 덮어쓰거나 KIEP 전문 제안층을
공식 지침으로 승격시키지 않고, 한국어 정본·영문 미러·설치형 스킬·오픈웨이트
러너의 지식이 갈라지지 않도록 결정적인 계약만 검사한다.
"""

import ast
import os
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

METHOD_REFS = (
    "개발평가-설계방법론-다이제스트.md",
    "개발평가-자료분석방법론-다이제스트.md",
    "개발평가-관리보고윤리-다이제스트.md",
)


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as stream:
        return stream.read()


class ReferenceLayer(unittest.TestCase):
    def test_all_method_references_have_english_mirrors(self):
        for name in METHOD_REFS:
            canonical = os.path.join(ROOT, "reference", name)
            mirror = os.path.join(ROOT, "docs", "en", "reference", name)
            self.assertTrue(os.path.isfile(canonical), canonical)
            self.assertTrue(os.path.isfile(mirror), mirror)
            self.assertGreater(os.path.getsize(canonical), 3000, canonical)
            self.assertGreater(os.path.getsize(mirror), 3000, mirror)

    def test_each_digest_declares_supporting_status_and_precedence(self):
        for name in METHOD_REFS:
            ko = read("reference", name)
            en = read("docs", "en", "reference", name)
            self.assertIn("보조 방법론", ko, name)
            self.assertIn("우선", ko, name)
            self.assertIn("supporting methodology", en, name)
            self.assertIn("Precedence", en, name)

    def test_source_pdf_remains_excluded(self):
        self.assertIn("*.pdf", read(".gitignore"))


class SkillRouting(unittest.TestCase):
    def assert_skill_routes(self, skill, expected):
        body = read("skills", skill, "SKILL.md")
        for name in expected:
            self.assertIn(name, body, f"{skill} does not route {name}")
        self.assertIn("규범", body, skill)

    def test_evaluate_routes_design_and_data(self):
        self.assert_skill_routes("evaluate", METHOD_REFS[:2])

    def test_impact_review_routes_design_and_data(self):
        self.assert_skill_routes("impact-review", METHOD_REFS[:2])

    def test_quality_review_routes_all_methods(self):
        self.assert_skill_routes("quality-review", METHOD_REFS)

    def test_write_report_routes_reporting_and_conditional_methods(self):
        self.assert_skill_routes("write-report", METHOD_REFS)

    def test_design_matrix_template_is_routed_to_evaluate_and_write(self):
        name = "evaluation-design-matrix-template.md"
        template = read("templates", name)
        self.assertIn("질문·판단 매트릭스", template)
        self.assertIn("자료·분석 매트릭스", template)
        self.assertIn("핵심 주장-근거 등록부", template)
        self.assertIn(name, read("skills", "evaluate", "SKILL.md"))
        self.assertIn(name, read("skills", "write-report", "SKILL.md"))


class HarnessParity(unittest.TestCase):
    def test_cross_cutting_agents_receive_method_boundaries(self):
        mapping = {
            "quality-verifier.md": METHOD_REFS[:2],
            "impact-evaluation-reviewer.md": METHOD_REFS[:2],
            "report-quality-inspector.md": METHOD_REFS,
            "report-composer.md": METHOD_REFS,
            "narrative-verifier.md": (),
        }
        for agent, expected in mapping.items():
            canonical = read("agents", agent)
            mirror = read("docs", "en", "agents", agent)
            for name in expected:
                self.assertIn(name, canonical, agent)
            self.assertIn("방법론", canonical, agent)
            self.assertIn("method", mirror.lower(), agent)

    def test_codex_fallback_and_mirror_list_all_modules(self):
        for path in (("AGENTS.md",), ("docs", "en", "AGENTS.md")):
            body = read(*path)
            for name in METHOD_REFS:
                self.assertIn(name, body, "/".join(path))

    def test_open_runner_injects_design_and_data_not_reporting(self):
        source = read("scripts", "open_runner.py")
        tree = ast.parse(source)
        refs = None
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "DEFAULT_REFERENCES":
                        refs = ast.literal_eval(node.value)
        self.assertIsNotNone(refs)
        self.assertIn(f"reference/{METHOD_REFS[0]}", refs)
        self.assertIn(f"reference/{METHOD_REFS[1]}", refs)
        self.assertNotIn(f"reference/{METHOD_REFS[2]}", refs)
        self.assertLess(
            refs.index(f"reference/KOICA-사업평가규정-다이제스트.md"),
            refs.index(f"reference/{METHOD_REFS[0]}"),
        )
        self.assertIn("충돌 시 규범층이 우선", source)


class ImpactSourceIntegrity(unittest.TestCase):
    def test_policy_study_is_not_misrepresented_as_enacted_guidance(self):
        ko = read("reference", "KOICA-영향평가-가이드라인-다이제스트.md")
        en = read("docs", "en", "reference", "KOICA-영향평가-가이드라인-다이제스트.md")
        self.assertIn("가이드라인(안)", ko)
        self.assertIn("공식 시행지침", ko)
        self.assertIn("proposed guidelines", en.lower())
        self.assertIn("not a verified enacted", en.lower())

    def test_six_principles_and_three_by_seven_evaluability_are_preserved(self):
        paths = (
            ("reference", "KOICA-영향평가-가이드라인-다이제스트.md"),
            ("skills", "impact-review", "SKILL.md"),
            ("agents", "impact-evaluation-reviewer.md"),
        )
        for path in paths:
            body = read(*path)
            self.assertIn("6개", body, "/".join(path))
            self.assertIn("지속가능성", body, "/".join(path))
            self.assertIn("3요소·7항목", body, "/".join(path))

    def test_completed_projects_are_not_blanket_rejected(self):
        paths = (
            ("reference", "KOICA-영향평가-가이드라인-다이제스트.md"),
            ("skills", "impact-review", "SKILL.md"),
            ("agents", "impact-evaluation-reviewer.md"),
            ("docs", "en", "agents", "impact-evaluation-reviewer.md"),
        )
        for path in paths:
            body = read(*path)
            self.assertNotIn("이미 종료된 사업은 부적합", body, "/".join(path))
            self.assertNotIn("completed projects are unsuitable", body.lower(), "/".join(path))

    def test_three_way_label_is_explicitly_project_operational(self):
        skill = read("skills", "impact-review", "SKILL.md")
        agent = read("agents", "impact-evaluation-reviewer.md")
        self.assertIn("DevEval의 운용 프레임", skill)
        self.assertIn("공식 판정", agent)


if __name__ == "__main__":
    unittest.main()
