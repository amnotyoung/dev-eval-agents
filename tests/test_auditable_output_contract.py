"""평가 근거·상충·검증 정정이 최종 산출물에서 사라지지 않는지 회귀 검사."""

import os
import subprocess
import sys
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKER = os.path.join(ROOT, "scripts", "auditable_output_check.py")
FIXTURES = os.path.join(ROOT, "tests", "fixtures")


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as stream:
        return stream.read()


def run_fixture(name):
    return subprocess.run(
        [sys.executable, CHECKER, os.path.join(FIXTURES, name)],
        check=False,
        text=True,
        capture_output=True,
    )


class CheckerBehavior(unittest.TestCase):
    def test_complete_brief_passes(self):
        result = run_fixture("auditable-brief-clean.md")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_conflict_marker_missing_from_register_fails(self):
        result = run_fixture("auditable-brief-missing-register.md")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("X1", result.stderr)
        self.assertIn("상충 등록부", result.stderr)

    def test_terse_score_only_answer_fails(self):
        result = run_fixture("auditable-brief-terse.md")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("필수 섹션 누락", result.stderr)

    def test_unfilled_template_fails(self):
        result = subprocess.run(
            [sys.executable, CHECKER, os.path.join(ROOT, "templates", "auditable-evaluation-brief-template.md")],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("자리표시자", result.stderr)


class RuntimeContract(unittest.TestCase):
    def test_evaluate_skill_routes_template_and_checker(self):
        skill = read("skills", "evaluate", "SKILL.md")
        self.assertIn("auditable-evaluation-brief-template.md", skill)
        self.assertIn("auditable_output_check.py", skill)
        self.assertIn("상충·불일치 등록부", skill)
        self.assertIn("검증 후", skill)

    def test_all_criterion_agents_capture_counterevidence_and_conflicts(self):
        agents = (
            "dac-relevance-evaluator.md",
            "dac-coherence-evaluator.md",
            "dac-effectiveness-evaluator.md",
            "dac-efficiency-evaluator.md",
            "dac-sustainability-evaluator.md",
            "dac-impact-evaluator.md",
        )
        for name in agents:
            ko = read("agents", name)
            en = read("docs", "en", "agents", name)
            self.assertIn("반대·제약근거", ko, name)
            self.assertIn("원자료 상충 후보", ko, name)
            self.assertIn("Source-conflict candidates", en, name)

    def test_verifier_aggregates_conflicts_and_corrected_scores(self):
        ko = read("agents", "quality-verifier.md")
        en = read("docs", "en", "agents", "quality-verifier.md")
        for token in ("중대 상충", "상충·불일치 등록부", "검증 후 점수", "조건부 통과"):
            self.assertIn(token, ko)
        for token in ("material conflict", "Conflict and inconsistency register", "post-verification score"):
            self.assertIn(token, en)

    def test_known_conflict_classes_are_routed_to_the_right_roles(self):
        skill = read("skills", "evaluate", "SKILL.md")
        for token in ("단위", "분모", "집계규칙", "상태기준일"):
            self.assertIn(token, skill)
        self.assertIn("수행횟수", read("agents", "dac-effectiveness-evaluator.md"))
        self.assertIn("연장 횟수", read("agents", "dac-efficiency-evaluator.md"))
        self.assertIn("하자", read("agents", "dac-sustainability-evaluator.md"))

    def test_fallback_and_report_path_preserve_audit_trail(self):
        for path in (("AGENTS.md",), ("docs", "en", "AGENTS.md")):
            body = read(*path)
            self.assertIn("audit", body.lower(), "/".join(path))
        self.assertIn("상충·불일치 등록부", read("templates", "evaluation-report-template.md"))
        self.assertIn("상충·불일치 등록부", read("skills", "write-report", "SKILL.md"))

    def test_nonstandard_cts_criterion_is_not_routed(self):
        self.assertFalse(os.path.exists(os.path.join(ROOT, "agents", "cts-validity-evaluator.md")))
        active_paths = (
            ("AGENTS.md",),
            ("docs", "en", "AGENTS.md"),
            ("skills", "evaluate", "SKILL.md"),
            ("skills", "write-report", "SKILL.md"),
            ("templates", "eval-plan-template.md"),
            ("templates", "evaluation-report-template.md"),
            ("templates", "auditable-evaluation-brief-template.md"),
            ("agents", "report-composer.md"),
            ("docs", "en", "agents", "report-composer.md"),
        )
        forbidden = ("cts-validity", "CTS면 타당성", "CTS 6기준", "CTS Validity")
        for path in active_paths:
            body = read(*path)
            for token in forbidden:
                self.assertNotIn(token, body, "/".join(path))

if __name__ == "__main__":
    unittest.main()
