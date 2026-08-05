"""평가 근거·상충·검증 정정이 최종 산출물에서 사라지지 않는지 회귀 검사."""

import os
import subprocess
import sys
import tempfile
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKER = os.path.join(ROOT, "scripts", "auditable_output_check.py")
FIXTURES = os.path.join(ROOT, "tests", "fixtures")


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as stream:
        return stream.read()


def run_fixture(name, *extra_args):
    return subprocess.run(
        [sys.executable, CHECKER, *extra_args, os.path.join(FIXTURES, name)],
        check=False,
        text=True,
        capture_output=True,
    )


def run_text(text, *extra_args):
    """Write then close a temporary file before the checker reopens it (Windows-safe)."""
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "brief.md")
        with open(path, "w", encoding="utf-8") as stream:
            stream.write(text)
        return subprocess.run(
            [sys.executable, CHECKER, *extra_args, path],
            check=False,
            text=True,
            capture_output=True,
        )


class CheckerBehavior(unittest.TestCase):
    def test_complete_brief_passes(self):
        result = run_fixture("auditable-brief-clean.md")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_ledger_only_stage_passes_before_scoring(self):
        result = run_fixture("source-fact-ledger-stage.md", "--ledger-only")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("원문 사실대장 계약 통과", result.stdout)

    def test_unit_count_period_and_status_differences_need_classification(self):
        result = run_fixture("source-fact-ledger-unclassified.md", "--ledger-only")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        for fact_id in ("F1", "F2", "F3", "F4"):
            self.assertIn(fact_id, result.stderr)
        self.assertIn("설명됨", result.stderr)
        self.assertIn("상충", result.stderr)

    def test_disagreement_text_does_not_count_as_agreement(self):
        text = read("tests", "fixtures", "source-fact-ledger-stage.md").replace(
            "| 보고서 v1 | p.20 본문 | 일치 |",
            "| 보고서 v1 | p.20 본문 | 불일치 |",
            1,
        )
        result = run_text(text, "--ledger-only")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("F2", result.stderr)
        self.assertIn("'일치'", result.stderr)

    def test_same_fact_key_cannot_be_split_across_fact_ids(self):
        text = read("tests", "fixtures", "source-fact-ledger-stage.md")
        text = text.replace(
            "| F2 | 초청연수 수료인원 실적 | 55 | 명 | 수료자 | 사업누적 | 고유인원 | 2021-12-31 | 보고서 v1 | p.20 본문 | 일치 |",
            "| F20 | 초청연수 수료인원 실적 | 55 | 명 | 수료자 | 사업누적 | 고유인원 | 2021-12-31 | 보고서 v1 | p.20 본문 | 단일 출처 — 전체검색 완료 |",
            1,
        ).replace(
            "| F2 | 초청연수 수료인원 실적 | 55 | 명 | 수료자 | 사업누적 | 고유인원 | 2021-12-31 | 보고서 v1 | p.21 표 | 일치 |",
            "| F2 | 초청연수 수료인원 실적 | 55 | 명 | 수료자 | 사업누적 | 고유인원 | 2021-12-31 | 보고서 v1 | p.21 표 | 단일 출처 — 전체검색 완료 |",
            1,
        )
        result = run_text(text, "--ledger-only")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("여러 F-ID로 분할", result.stderr)
        self.assertIn("F20", result.stderr)

    def test_second_fact_ledger_table_cannot_hide_occurrences(self):
        text = read("tests", "fixtures", "source-fact-ledger-stage.md").replace(
            "\n## 3. 종합 평정",
            "\n| 사실 ID | 사실 키·정의 | 값·상태 | 단위 | 분모·대상 | 기준기간 | 집계규칙 | 상태기준일 | 문서·버전 | 원문 위치 | 대조 판정·상충 ID |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|\n"
            "| F9 | 숨긴 완료상태 | 진행 중 | 해당 없음 | 전체 시설 | 종료점검 | 하자 전건 | 2022-11-30 | 보고서 v1 | p.99 | 단일 출처 — 전체검색 완료 |\n"
            "\n## 3. 종합 평정",
            1,
        )
        result = run_text(text, "--ledger-only")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("표는 하나만 허용", result.stderr)

    def test_ledger_rows_must_be_contiguous_with_the_header(self):
        text = read("tests", "fixtures", "source-fact-ledger-stage.md").replace(
            "|---|---|---|---|---|---|---|---|---|---|---|\n| F1 |",
            "|---|---|---|---|---|---|---|---|---|---|---|\n\n대장 표 종료\n| F1 |",
            1,
        )
        result = run_text(text, "--ledger-only")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("원문 사실대장에 F-ID", result.stderr)

    def test_dash_is_not_a_completed_ledger_field(self):
        text = read("tests", "fixtures", "source-fact-ledger-stage.md").replace(
            "| F1 | 사업 승인예산 | 1000000 |",
            "| F1 | 사업 승인예산 | - |",
            1,
        )
        result = run_text(text, "--ledger-only")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("F1", result.stderr)
        self.assertIn("값·상태", result.stderr)

    def test_decorated_unknown_cannot_be_confirmed_as_agreement(self):
        text = read("tests", "fixtures", "source-fact-ledger-stage.md").replace(
            "| 55 | 명 |",
            "| 미상(원문 미기재) | 명 |",
        )
        result = run_text(text, "--ledger-only")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("F2", result.stderr)
        self.assertIn("설명됨", result.stderr)

    def test_explanation_placeholder_is_not_concrete_evidence(self):
        text = read("tests", "fixtures", "source-fact-ledger-stage.md").replace(
            "설명됨: 서로 다른 연도별 실적",
            "설명됨: [근거]",
        )
        result = run_text(text, "--ledger-only")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("F3", result.stderr)
        self.assertIn("구체 근거", result.stderr)

    def test_fact_marker_cannot_fill_an_unrelated_ledger_field(self):
        text = read("tests", "fixtures", "source-fact-ledger-stage.md").replace(
            "| F1 | 사업 승인예산 |",
            "| F1 | [사실: F1] |",
            1,
        )
        result = run_text(text, "--ledger-only")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("사실 키·정의", result.stderr)

    def test_document_version_difference_needs_classification(self):
        text = read("tests", "fixtures", "source-fact-ledger-stage.md").replace(
            "| 보고서 v1 | p.21 표 | 일치 |",
            "| 보고서 v2 | p.21 표 | 일치 |",
            1,
        )
        result = run_text(text, "--ledger-only")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("F2", result.stderr)
        self.assertIn("문서·버전", result.stderr)

    def test_same_source_occurrence_cannot_be_counted_twice(self):
        text = read("tests", "fixtures", "source-fact-ledger-stage.md").replace(
            "| 보고서 v1 | p.21 표 | 일치 |",
            "| 보고서 v1 | p.20 본문 | 일치 |",
            1,
        )
        result = run_text(text, "--ledger-only")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("F2", result.stderr)
        self.assertIn("원문 위치가 중복", result.stderr)

    def test_detail_conflict_fact_pair_must_match_ledger(self):
        text = read("tests", "fixtures", "auditable-brief-clean.md").replace(
            "[사실: F3] | [근거: 보고서 p.20]",
            "[사실: F4] | [근거: 보고서 p.20]",
            1,
        )
        result = run_text(text)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("상세 평정 X1", result.stderr)
        self.assertIn("F3", result.stderr)
        self.assertIn("F4", result.stderr)

    def test_every_ledger_fact_must_reach_a_detailed_rating(self):
        text = read("tests", "fixtures", "auditable-brief-clean.md").replace(
            "[사실: F5] | [근거: 보고서 p.40]",
            "[사실: F4] | [근거: 보고서 p.40]",
            1,
        )
        result = run_text(text)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("F5", result.stderr)
        self.assertIn("어느 상세 평정에도", result.stderr)

    def test_conflict_register_requires_the_full_row_schema(self):
        text = read("tests", "fixtures", "auditable-brief-clean.md")
        old = (
            "| ID | 사실 ID | 쟁점 | 값·진술 A(원문 위치) | 값·진술 B(원문 위치) | 대조 결과·가능한 설명 | 해결 상태 | 점수·결론 영향 | 후속 확인 |\n"
            "|---|---|---|---|---|---|---|---|---|\n"
            "| X1 | [사실: F3] | 연수 횟수 | 5회(p.20) | 6회(p.21) | 집계규칙 설명 없음 | 미해결 | 효과성 4→3 | 원자료 확인 |"
        )
        collapsed = (
            "| ID | 사실 ID |\n"
            "|---|---|\n"
            "| X1 | [사실: F3] 해결 상태 점수·결론 영향 후속 확인 |"
        )
        result = run_text(text.replace(old, collapsed, 1))
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("상충 등록부 필드 누락", result.stderr)
        self.assertIn("값·진술 A", result.stderr)

    def test_combined_criterion_heading_cannot_satisfy_five_sections(self):
        text = read("tests", "fixtures", "auditable-brief-clean.md").replace(
            "### 적절성",
            "### 적절성·일관성·효과성·효율성·지속가능성",
            1,
        )
        for criterion in ("일관성", "효과성", "효율성", "지속가능성"):
            text = text.replace(f"### {criterion}\n", "", 1)
        result = run_text(text)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        for criterion in ("적절성", "일관성", "효과성", "효율성", "지속가능성"):
            self.assertIn(f"기준별 상세 평정 누락: {criterion}", result.stderr)

    def test_negated_unavailable_sentence_does_not_replace_fact_evidence(self):
        text = read("tests", "fixtures", "auditable-brief-clean.md").replace(
            "| 수요 | 부합 | [사실: F1] | [근거: 보고서 p.10] | 주민자료 없음 | 없음 | 확인됨 |",
            "기준 전체 평가 불가 아님. 수요는 부합한다고 평가함.",
            1,
        ).replace(
            "| 조율 | 일부 | [사실: F2] |",
            "| 조율 | 일부 | [사실: F2] [사실: F1] |",
            1,
        )
        result = run_text(text)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("적절성 상세 평정", result.stderr)

    def test_conflict_marker_missing_from_register_fails(self):
        result = run_fixture("auditable-brief-missing-register.md")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("X1", result.stderr)
        self.assertIn("상충 등록부", result.stderr)

    def test_negated_no_conflict_sentence_does_not_pass(self):
        text = read("tests", "fixtures", "auditable-brief-clean.md")
        text = text.replace(
            "| F3 | 현지연수 실시 횟수 실적 | 5 | 회 | 현지연수 | 사업누적 | 행사 횟수 | 2023-12-01 | 종료보고서 v1 | p.20 본문 | [상충: X1] |",
            "| F3 | 현지연수 실시 횟수 실적 | 5 | 회 | 현지연수 | 사업누적 | 행사 횟수 | 2023-12-01 | 종료보고서 v1 | p.20 본문 | 일치 |",
            1,
        ).replace(
            "| F3 | 현지연수 실시 횟수 실적 | 6 | 회 | 현지연수 | 사업누적 | 행사 횟수 | 2023-12-01 | 종료보고서 v1 | p.21 표 | [상충: X1] |",
            "| F3 | 현지연수 실시 횟수 실적 | 5 | 회 | 현지연수 | 사업누적 | 행사 횟수 | 2023-12-01 | 종료보고서 v1 | p.21 표 | 일치 |",
            1,
        ).replace(" [상충: X1]", "", 1)
        old_register = (
            "| ID | 사실 ID | 쟁점 | 값·진술 A(원문 위치) | 값·진술 B(원문 위치) | 대조 결과·가능한 설명 | 해결 상태 | 점수·결론 영향 | 후속 확인 |\n"
            "|---|---|---|---|---|---|---|---|---|\n"
            "| X1 | [사실: F3] | 연수 횟수 | 5회(p.20) | 6회(p.21) | 집계규칙 설명 없음 | 미해결 | 효과성 4→3 | 원자료 확인 |"
        )
        text = text.replace(
            old_register,
            "중대 상충 없음이라고 확인할 수 없으며 반복 표기 점검도 수행하지 못했다.",
            1,
        )
        result = run_text(text)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("중대 상충 없음", result.stderr)

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

    def test_unfilled_ledger_fails_early_gate(self):
        result = subprocess.run(
            [
                sys.executable,
                CHECKER,
                "--ledger-only",
                os.path.join(ROOT, "templates", "auditable-evaluation-brief-template.md"),
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("원문 사실대장", result.stderr)
        self.assertIn("자리표시자", result.stderr)

    def test_detail_fact_reference_missing_from_ledger_fails(self):
        text = read("tests", "fixtures", "auditable-brief-clean.md").replace(
            "[사실: F5] | [근거: 보고서 p.40]",
            "[사실: F99] | [근거: 보고서 p.40]",
            1,
        )
        result = run_text(text)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("F99", result.stderr)
        self.assertIn("원문 사실대장", result.stderr)


class RuntimeContract(unittest.TestCase):
    def test_evaluate_skill_routes_template_and_checker(self):
        skill = read("skills", "evaluate", "SKILL.md")
        self.assertIn("auditable-evaluation-brief-template.md", skill)
        self.assertIn("auditable_output_check.py", skill)
        self.assertIn("원문 사실대장", skill)
        self.assertIn("--ledger-only", skill)
        self.assertIn("[사실: Fn]", skill)
        self.assertIn("상충·불일치 등록부", skill)
        self.assertIn("검증 후", skill)
        self.assertLess(skill.index("--ledger-only"), skill.index("기준 평가관 병렬 위임"))

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
        for token in (
            "원문 사실대장",
            "한 원문 표기당 한 행",
            "[사실: Fn]",
            "중대 상충",
            "상충·불일치 등록부",
            "검증 후 점수",
            "조건부 통과",
        ):
            self.assertIn(token, ko)
        for token in (
            "source-fact ledger",
            "one row per source occurrence",
            "[Fact: Fn]",
            "material conflict",
            "Conflict and inconsistency register",
            "post-verification score",
        ):
            self.assertIn(token, en)

    def test_fallback_and_plan_require_early_fact_ledger(self):
        ko = read("AGENTS.md")
        en = read("docs", "en", "AGENTS.md")
        plan = read("templates", "eval-plan-template.md")
        for token in ("원문 사실대장", "--ledger-only", "[사실: Fn]"):
            self.assertIn(token, ko)
        for token in ("source-fact ledger", "--ledger-only", "[Fact: Fn]"):
            self.assertIn(token, en)
        self.assertIn("원문 사실대장 작성", plan)
        self.assertIn("--ledger-only", plan)

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

    def test_report_path_preserves_source_fact_ledger(self):
        active_paths = (
            ("skills", "write-report", "SKILL.md"),
            ("agents", "report-composer.md"),
            ("agents", "narrative-verifier.md"),
            ("templates", "evaluation-report-template.md"),
        )
        for path in active_paths:
            body = read(*path)
            self.assertIn("원문 사실대장", body, "/".join(path))
            self.assertIn("[사실: Fn]", body, "/".join(path))
        for path in (
            ("docs", "en", "agents", "report-composer.md"),
            ("docs", "en", "agents", "narrative-verifier.md"),
        ):
            body = read(*path)
            self.assertIn("source-fact ledger", body.lower(), "/".join(path))
            self.assertIn("[Fact: Fn]", body, "/".join(path))

    def test_open_runner_requests_fact_ledger_traceability(self):
        runner = read("scripts", "open_runner.py")
        self.assertIn("F-ID 사실대장", runner)
        self.assertIn("[사실: Fn]", runner)

    def test_nonstandard_cts_criterion_is_not_routed(self):
        self.assertFalse(os.path.exists(os.path.join(ROOT, "agents", "cts-validity-evaluator.md")))
        active_paths = (
            ("AGENTS.md",),
            ("CLAUDE.md",),
            ("README.md",),
            ("README.ko.md",),
            ("docs", "en", "AGENTS.md"),
            ("docs", "en", "CLAUDE.md"),
            ("skills", "evaluate", "SKILL.md"),
            ("skills", "write-report", "SKILL.md"),
            ("templates", "eval-plan-template.md"),
            ("templates", "evaluation-report-template.md"),
            ("templates", "auditable-evaluation-brief-template.md"),
            ("agents", "report-composer.md"),
            ("docs", "en", "agents", "report-composer.md"),
        )
        forbidden = (
            "cts-validity",
            "CTS면 타당성",
            "CTS 6기준",
            "CTS Validity",
            "5~6기준",
            "5–6 criteria",
        )
        for path in active_paths:
            body = read(*path)
            for token in forbidden:
                self.assertNotIn(token, body, "/".join(path))

if __name__ == "__main__":
    unittest.main()
