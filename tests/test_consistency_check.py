"""consistency_check.py 회귀 테스트.

픽스처는 실제 KOICA 종료평가 PDF 334건 전수 스윕(2026-08)에서 관측된 사고·오탐
유형을 합성으로 재현한 것이다 — 특히 국문↔영문 요약 종합점수 불일치(캄보디아
CTS 시리즈에서 실물 2건 확인: 11.7 vs 12.7, 9.3 vs 10.3)가 핵심 회귀 케이스다.

실행:  python3 -m unittest discover -s tests
표준 라이브러리만 사용(pytest 불필요).
"""

import contextlib
import io
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import consistency_check as cc  # noqa: E402

FIXTURES = os.path.join(ROOT, "tests", "fixtures")


def run_path(path, mode="auto"):
    """(exit_code, 출력 텍스트) — stdout·stderr를 합쳐 돌려준다."""
    buf_out, buf_err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        code = cc.run(path, mode)
    return code, buf_out.getvalue() + buf_err.getvalue()


def run_fixture(name, mode="auto"):
    return run_path(os.path.join(FIXTURES, name), mode)


def run_text(text, mode="auto"):
    """문자열(또는 바이트)을 임시 파일로 써서 검사한다."""
    data = text if isinstance(text, bytes) else text.encode("utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "report.md")
        with open(path, "wb") as fh:
            fh.write(data)
        return run_path(path, mode)


class ExitCodeContract(unittest.TestCase):
    """종료 코드 계약: 0=통과 / 2=위반 / 3=확인 불가. '확인 불가'는 통과가 아니다."""

    def test_clean_passes(self):
        code, out = run_fixture("project-clean.md")
        self.assertEqual(code, 0, out)
        self.assertIn("통과", out)

    def test_no_numbers_is_exit_3_not_0(self):
        code, out = run_fixture("no-numbers.md")
        self.assertEqual(code, 3, out)
        self.assertIn("확인 불가", out)

    def test_missing_file_is_uncheckable_not_pass(self):
        """읽지 못한 파일은 '통과(0)'가 아니라 '확인 불가(3)'다 — 스킬은 0을 통과로 읽는다."""
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            code = cc.run(os.path.join(FIXTURES, "없는-파일.md"), "auto")
        self.assertEqual(code, 3)
        self.assertIn("확인 불가", buf.getvalue())

    def test_usage_error_is_exit_3_not_violation_code(self):
        """argparse 기본 종료 코드 2는 '위반'과 겹친다 — 사용법 오류도 확인 불가(3)."""
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf), self.assertRaises(SystemExit) as ctx:
            cc.main(["보고서.md", "--mode", "projet"])
        self.assertEqual(ctx.exception.code, 3)
        self.assertIn("사용법 오류", buf.getvalue())

    def test_cp949_report_is_read(self):
        code, out = run_text("종합점수: 13/20, 등급: D".encode("cp949"))
        self.assertEqual(code, 0, out)


class KoEnMismatch(unittest.TestCase):
    """국문 '24점 만점 중 11.7' ↔ 영문 '12.7 points out of 24' 불일치 검출."""

    def test_cambodia_pattern_caught(self):
        code, out = run_fixture("project-ko-en-mismatch.md")
        self.assertEqual(code, 2, out)
        self.assertIn("종합점수 표기 불일치", out)
        self.assertIn("11.7", out)
        self.assertIn("12.7", out)

    def test_reversed_korean_form_extracted(self):
        got = cc.find_totals_alt("본 사업은 총 24점 만점 중 11.7점으로 평가", ["16", "20", "24"])
        self.assertEqual([v for v, _ in got["24"]], [cc.Decimal("11.7")])

    def test_english_form_extracted(self):
        got = cc.find_totals_alt("This project scored 12.7 points out of 24.", ["16", "20", "24"])
        self.assertEqual([v for v, _ in got["24"]], [cc.Decimal("12.7")])


class GradeScoreGap(unittest.TestCase):
    def test_actual_composer_bare_grade_gap_is_caught(self):
        code, out = run_text("- 검증 후 종합점수·등급(안): 11.67/20, A\n")
        self.assertEqual(code, 2, out)
        self.assertIn("등급-점수 괴리", out)

    def test_actual_composer_bare_grade_passes_when_correct(self):
        code, out = run_text("- 검증 후 종합점수·등급(안): 11.67/20, E\n")
        self.assertEqual(code, 0, out)
        self.assertEqual(cc.find_grades_af("- 검증 후 종합점수·등급(안): 11.67/20, E"), [("E", 1)])

    def test_bold_bare_grade_is_checked_without_scanning_unrelated_letters(self):
        text = "- 검증 후 종합점수·등급(안): **11.67/20, E**\n부록 A는 자료목록이다."
        self.assertEqual(cc.find_grades_af(text), [("E", 1)])
        code, out = run_text(text.replace(", E**", ", **A**"))
        self.assertEqual(code, 2, out)

    def test_grade_gap_caught(self):
        code, out = run_fixture("project-grade-gap.md")
        self.assertEqual(code, 2, out)
        self.assertIn("등급-점수 괴리", out)


class FalsePositiveRegression(unittest.TestCase):
    """스윕에서 확인된 오탐 유형 — 전부 무시되고 진짜 신호만 통과해야 한다."""

    def test_legend_noise_pack_passes(self):
        code, out = run_fixture("project-legend-noise.md")
        self.assertEqual(code, 0, out)
        self.assertIn("통과", out)

    def test_count_schedule_ratio_not_scores(self):
        text = ("입학생 수 (남/여) (35/24)\n"
                "3/20-24 비대면 현지조사 준비\n"
                "일정: 7/20(월) 도착\n"
                "달성 8/20개소\n"
                "영아사망률 20/100,000명")
        self.assertEqual(cc.find_totals(text, ["16", "20", "24"]), {})

    def test_scores_with_jeom_suffix_kept(self):
        got = cc.find_totals("종합점수는 14.5/20점이다", ["16", "20", "24"])
        self.assertEqual([v for v, _ in got["20"]], [cc.Decimal("14.5")])

    def test_quality_grade_line_excluded_from_project_grades(self):
        text = "평가품질 등급 : B\n용역종합 등급 : A\nKOICA 평가 등급: C"
        self.assertEqual({g for g, _ in cc.find_grades_af(text)}, {"C"})

    def test_quality_legend_range_and_definition_excluded(self):
        text = ("품질 등급이 A~C인 보고서는 기본 요건 충족\n"
                "품질 등급이 D인 경우 미부합\n"
                "평가품질 등급 : C")
        import re
        gset = set(re.findall(r"품질\s*등급[^A-D\n]{0,20}([A-D])(?![A-Za-z+~∼인])", text))
        self.assertEqual(gset, {"C"})

    def test_label_legend_line_skipped(self):
        text = "종합평가 등급   (매우 성공적, 성공적, 부분 성공적, 미흡)"
        self.assertEqual(cc.find_grades_label(text), [])

    def test_threshold_sentence_skipped(self):
        text = "종합점수가 14점 이상이면 매우 성공적, 11점 이상 14점 미만이면 성공적으로 평가함 (등급)"
        self.assertEqual(cc.find_grades_label(text), [])
        self.assertEqual(cc.find_composite_labeled(text), [])

    def test_survey_composite_skipped(self):
        text = "만족도 설문 종합점수 4.07점으로 긍정적"
        self.assertEqual(cc.find_composite_labeled(text), [])

    def test_mismatch_quote_line_not_reflagged(self):
        """원보고서의 불일치를 '인용·보고'하는 줄은 자기모순이 아니다.

        단, 인용 줄 밖에서 값을 주장하는 진짜 불일치는 계속 잡혀야 한다.
        """
        quote_only = "원보고서 총점: 국문요약 11.7/24 vs 영문요약 12.7/24 — 상호 불일치 [확인 필요]"
        self.assertEqual(cc.find_totals(quote_only, ["16", "20", "24"]), {})
        real = ("국문 요약: 총 24점 만점 중 11.7점\n"
                "Executive Summary: 12.7 points out of 24")
        got = cc.find_totals_alt(real, ["16", "20", "24"])
        self.assertEqual({v for v, _ in got["24"]}, {cc.Decimal("11.7"), cc.Decimal("12.7")})

    def test_composite_gap_stopwords_skipped(self):
        """'종합점수' 뒤 창이 절차어를 넘어 무관한 숫자를 잡지 않아야 한다."""
        text = ("표준 5기준 종합점수·등급(D 또는 E)의 확정 및 외부 6기준 매트릭스 총점 확정\n"
                "표준 5기준 종합점수 산정과 별도로 취급했다 [05, 06]")
        self.assertEqual(cc.find_composite_labeled(text), [])
        kept = cc.find_composite_labeled("종합 점수     12.34")
        self.assertEqual([v for v, _ in kept], [cc.Decimal("12.34")])


class QualityMode(unittest.TestCase):
    def test_quality_clean_passes(self):
        code, out = run_fixture("quality-clean.md")
        self.assertEqual(code, 0, out)
        self.assertIn("quality 모드", out)

    def test_quality_total_mismatch_caught_and_pdm_rate_ignored(self):
        code, out = run_fixture("quality-total-mismatch.md")
        self.assertEqual(code, 2, out)
        self.assertIn("총점(/100) 표기 불일치", out)
        self.assertNotIn("91.5", out)


class AuditableBriefGrades(unittest.TestCase):
    """플러그인 자체 산출물(감사 가능한 브리프)의 등급↔점수 검사가 실제로 켜져 있어야 한다.

    예전에는 문서 어딘가의 '잠정 점수' 문구 때문에 ④가 통째로 꺼졌고 `D(안)` 표기도
    등급으로 읽지 못해, 13/20에 A(안)을 적어도 통과했다.
    """

    def brief(self):
        with open(os.path.join(FIXTURES, "auditable-brief-clean.md"), encoding="utf-8") as fh:
            return fh.read()

    def test_clean_brief_passes(self):
        code, out = run_text(self.brief(), "project")
        self.assertEqual(code, 0, out)

    def test_wrong_draft_grade_in_brief_caught(self):
        text = self.brief().replace("13/20, D(안)", "13/20, A(안)")
        code, out = run_text(text, "project")
        self.assertEqual(code, 2, out)
        self.assertIn("등급-점수 괴리", out)

    def test_draft_grade_notation_extracted(self):
        got = cc.find_grades_af("- 검증 후 종합점수·등급(안): 13/20, D(안)")
        self.assertEqual([g for g, _ in got], ["D"])

    def test_pre_verification_and_history_lines_excluded(self):
        text = ("- 검증 전 종합점수·등급(안): 14/20, C(안)\n"
                "- 검증 후 종합점수·등급(안): 13/20, D(안)\n"
                "| V1 | 효과성 4 | 상충 | 효과성 3 | 14→13, C→D |\n")
        code, out = run_text(text)
        self.assertEqual(code, 0, out)


class GradeSchemes(unittest.TestCase):
    """등급↔점수 판정은 체계별 공식 구간으로만 한다."""

    def test_2024_letter_label_mismatch_caught(self):
        code, out = run_text("종합점수: 13/20, 등급: D(성공적)")
        self.assertEqual(code, 2, out)
        self.assertIn("문자-라벨 불일치", out)
        self.assertEqual(out.count("등급-점수 괴리"), 0, out)  # 같은 원인을 두 번 보고하지 않는다

    def test_2024_letter_label_match_passes(self):
        code, out = run_text("종합점수: 13/20, 등급: D(부분 성공적)")
        self.assertEqual(code, 0, out)

    def test_grade_gap_in_out_of_form_caught(self):
        code, out = run_text("본 사업은 총 20점 만점 중 12점, 등급: B")
        self.assertEqual(code, 2, out)
        self.assertIn("판정은 D", out)

    def test_2021_sixteen_point_scheme_not_held_to_2024_letters(self):
        """2021~23년 5기준 /16 보고서는 14.1점에 '매우 성공적'·B를 함께 쓴다 — 정상이다."""
        text = ("종합 점수 (a+b+c+d+e) 14.1 /16점\n"
                "종합 평가 등급 매우 성공적\n"
                "KOICA 평가 등급 B\n")
        code, out = run_text(text)
        self.assertEqual(code, 0, out)

    def test_2015_sixteen_point_labels_use_14_11_8(self):
        """국조실 2015 지침: 14·11·8점. 10.0/16은 '부분 성공적'이 맞다(평균 2.5 밴드가 아님)."""
        base = ("평균 점수(a) 2.7\n평균 점수(b) 3.3\n평균 점수(c) 2.0\n평균 점수(d) 2.0\n"
                "종합 점수(a+b+c+d) 10.0\n종합 평가 등급 {label}\n")
        code, out = run_text(base.format(label="부분성공적"))
        self.assertEqual(code, 0, out)
        code, out = run_text(base.format(label="성공적"))
        self.assertEqual(code, 2, out)
        self.assertIn("14점↑ 매우 성공적", out)

    def test_date_like_fraction_not_used_for_grade_judgment(self):
        """일정표 `10/16`(10월 16일)을 /16 종합점수로 보고 등급과 대조하지 않는다."""
        text = ("10/16 운영자 10명 서비스 개통 준비\n"
                "종합 평가 등급은 매우 성공적이며\n")
        code, out = run_text(text)
        self.assertNotIn("등급-점수 괴리", out)

    def test_twentyfour_point_labels_not_judged(self):
        """/24 체계는 공식 라벨 구간이 확인되지 않아 등급↔점수를 판정하지 않는다."""
        code, out = run_text("총 24점 만점 중 11.7점으로 '부분 성공적' 등급이다.")
        self.assertEqual(code, 0, out)


class ExtractionEdges(unittest.TestCase):
    def test_denominator_digit_not_read_as_score(self):
        """'종합 점수 24점 만점 중 11.7'에서 분모 24의 '2'를 점수로 잘라 읽지 않는다."""
        self.assertEqual(cc.find_composite_labeled("종합 점수 24점 만점 중 11.7점"), [])
        code, out = run_text("국문 요약: 종합 점수 24점 만점 중 11.7점.\n"
                             "Executive Summary: The project scored 11.7 points out of 24.\n")
        self.assertEqual(code, 0, out)

    def test_three_decimal_composite_kept_whole(self):
        got = cc.find_composite_labeled("종합 점수 (a+b+c+d+e) 13.125 /16점")
        self.assertEqual([v for v, _ in got], [cc.Decimal("13.125")])

    def test_manjeom_e_form_needs_composite_context(self):
        got = cc.find_totals_alt("종합점수는 20점 만점에 15점이다", ["16", "20", "24"])
        self.assertEqual([v for v, _ in got["20"]], [cc.Decimal("15")])
        self.assertEqual(cc.find_totals_alt("심리 검사 점수는 20점 만점에 17-18점으로", ["16", "20", "24"]), {})

    def test_ko_en_mismatch_with_manjeom_e_caught(self):
        code, out = run_text("종합점수는 20점 만점에 15점이다.\nThe project scored 16 points out of 20.\n")
        self.assertEqual(code, 2, out)

    def test_criterion_sum_compared_at_stated_precision(self):
        text = ("평균 점수(a) 2.33\n평균 점수(b) 3\n평균 점수(c) 3.34\n평균 점수(d) 3\n"
                "종합 점수 11.7\n")
        code, out = run_text(text)
        self.assertEqual(code, 0, out)
        code, out = run_text(text.replace("11.7", "12.7"))
        self.assertEqual(code, 2, out)
        self.assertIn("기준 평균 합 불일치", out)


class BundledSample(unittest.TestCase):
    def test_bundled_sample_is_honest_uncheckable(self):
        """samples/의 서술형 샘플은 '통과'가 아니라 '확인 불가(3)'여야 한다."""
        buf_out, buf_err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            code = cc.run(os.path.join(ROOT, "samples", "sample-evaluation-report.md"), "auto")
        self.assertEqual(code, 3, buf_out.getvalue() + buf_err.getvalue())


if __name__ == "__main__":
    unittest.main()
