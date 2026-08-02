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
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import consistency_check as cc  # noqa: E402

FIXTURES = os.path.join(ROOT, "tests", "fixtures")


def run_fixture(name, mode="auto"):
    """(exit_code, 출력 텍스트) — stdout·stderr를 합쳐 돌려준다."""
    buf_out, buf_err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        code = cc.run(os.path.join(FIXTURES, name), mode)
    return code, buf_out.getvalue() + buf_err.getvalue()


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

    def test_missing_file_fails_open(self):
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            code = cc.run(os.path.join(FIXTURES, "없는-파일.md"), "auto")
        self.assertEqual(code, 0)
        self.assertIn("fail-open", buf.getvalue())


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
        text = ("표준 5기준 종합점수·등급(D 또는 E)의 확정 및 CTS 6기준 매트릭스 총점 확정\n"
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


class BundledSample(unittest.TestCase):
    def test_bundled_sample_is_honest_uncheckable(self):
        """samples/의 서술형 샘플은 '통과'가 아니라 '확인 불가(3)'여야 한다."""
        buf_out, buf_err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            code = cc.run(os.path.join(ROOT, "samples", "sample-evaluation-report.md"), "auto")
        self.assertEqual(code, 3, buf_out.getvalue() + buf_err.getvalue())


if __name__ == "__main__":
    unittest.main()
