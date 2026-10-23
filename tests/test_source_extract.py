"""source_extract.py 회귀 테스트 — 원문(PDF·HWP) 텍스트화 경로.

실제 kordoc·pdftotext 대신 같은 인터페이스의 가짜 실행파일을 PATH에 둬서 네트워크 없이
변환기 선택·폴백·쪽 표지·경고·캐시·실패 코드를 고정한다.
"""

import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "source_extract.py")

KORDOC_RESULT = {
    "success": True,
    "metadata": {"pageMode": "layout"},
    "pages": [
        {"pageNumber": 1, "markdown": "| 종합 점수 (a+b+c+d+e) |  | 14.1 /16점 |"},
        {"pageNumber": 2, "markdown": "![image_001.png](image_001.png)"},
    ],
    "warnings": [{"page": 2, "code": "OCR_LOW_CONF", "message": "저신뢰 OCR 라인 폐기"}],
    "qualitySummary": {"needsOcr": False},
}


def write_exe(directory, name, body):
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"#!{sys.executable}\n" + textwrap.dedent(body))
    os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
    return path


def fake_kordoc(directory, fail=False):
    payload = json.dumps(KORDOC_RESULT, ensure_ascii=False)
    return write_exe(directory, "kordoc", f"""
        import sys
        args = sys.argv[1:]
        if "--version" in args:
            print("9.9.9"); sys.exit(0)
        if {fail!r}:
            print("파싱 실패", file=sys.stderr); sys.exit(1)
        out = args[args.index("-o") + 1]
        assert "--table-format" in args and "gfm" in args and "--no-images" in args
        with open(out, "w", encoding="utf-8") as fh:
            fh.write({payload!r})
    """)


def fake_pdftotext(directory):
    return write_exe(directory, "pdftotext", """
        import sys
        if "-v" in sys.argv:
            print("pdftotext version 0.0-test", file=sys.stderr); sys.exit(0)
        sys.stdout.write("첫 쪽 본문\\f둘째 쪽 종합점수 13/20\\f")
    """)


@unittest.skipIf(os.name == "nt", "가짜 실행파일은 POSIX 셸뱅을 쓴다")
class SourceExtract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.bin = os.path.join(self.tmp.name, "bin")
        self.work = os.path.join(self.tmp.name, "work")
        os.makedirs(self.bin)
        os.makedirs(self.work)

    def source(self, name, data=b"%PDF-1.4 dummy"):
        path = os.path.join(self.work, name)
        with open(path, "wb") as fh:
            fh.write(data)
        return path

    def run_extract(self, *args):
        env = {"PATH": self.bin, "HOME": self.tmp.name}
        return subprocess.run([sys.executable, SCRIPT, *args], cwd=self.work, env=env,
                              text=True, capture_output=True, check=False)

    def converted(self, stem):
        with open(os.path.join(self.work, ".omo", "sources", f"{stem}.md"), encoding="utf-8") as fh:
            return fh.read()

    def test_kordoc_output_gets_page_markers_provenance_and_warnings(self):
        fake_kordoc(self.bin)
        src = self.source("보고서.hwp")
        result = self.run_extract(src)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        text = self.converted("보고서")
        self.assertTrue(text.startswith("<!-- deveval-source"))
        self.assertIn(f"원본: {os.path.realpath(src)}", text)
        self.assertIn("SHA-256: ", text)
        self.assertIn("kordoc 9.9.9 (PATH)", text)
        self.assertIn("<!-- p.1 -->", text)
        self.assertIn("<!-- p.2 -->", text)
        self.assertIn("OCR_LOW_CONF 1건 — p.2", text)
        self.assertIn("그림 영역 1곳", text)
        with open(os.path.join(self.work, ".omo", "sources", "index.md"), encoding="utf-8") as fh:
            self.assertIn("보고서.hwp", fh.read())

    def test_same_source_is_not_converted_twice(self):
        fake_kordoc(self.bin)
        src = self.source("보고서.pdf")
        self.run_extract(src)
        again = self.run_extract(src)
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn("기존 변환본 사용", again.stdout)
        with open(src, "ab") as fh:  # 원본이 바뀌면 다시 변환한다
            fh.write(b" changed")
        changed = self.run_extract(src)
        self.assertIn("변환:", changed.stdout)

    def test_pdf_falls_back_to_pdftotext_and_retries_kordoc_later(self):
        fake_kordoc(self.bin, fail=True)
        fake_pdftotext(self.bin)
        src = self.source("보고서.pdf")
        result = self.run_extract(src)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        text = self.converted("보고서")
        self.assertIn("pdftotext version 0.0-test", text)
        self.assertIn("앞선 변환기 실패 — kordoc 실패", text)
        self.assertIn("<!-- p.2 -->\n둘째 쪽 종합점수 13/20", text)
        fake_kordoc(self.bin)  # kordoc이 다시 되면 폴백 변환본을 재사용하지 않는다
        retry = self.run_extract(src)
        self.assertIn("변환:", retry.stdout)
        self.assertIn("kordoc 9.9.9", self.converted("보고서"))

    def test_no_converter_is_exit_3_with_alternatives(self):
        src = self.source("보고서.hwp")
        result = self.run_extract(src)
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertIn("변환 불가", result.stderr)
        self.assertIn("kordoc MCP", result.stderr)
        self.assertIn("텍스트 원문을 요청", result.stderr)

    def test_text_source_is_copied_with_header_without_converter(self):
        src = self.source("요약.md", "종합점수: 13/20, 등급: D".encode("cp949"))
        result = self.run_extract(src)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        text = self.converted("요약")
        self.assertIn("텍스트 원문(변환 없음)", text)
        self.assertIn("종합점수: 13/20, 등급: D", text)

    def test_unsupported_and_missing_inputs_fail(self):
        result = self.run_extract(self.source("사진.bmp", b"BM"), os.path.join(self.work, "없음.pdf"))
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertIn("지원하지 않는 형식", result.stderr)
        self.assertIn("파일 없음", result.stderr)

    def test_usage_error_is_exit_3(self):
        result = self.run_extract("--engine", "ocrmagic", "x.pdf")
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)

    def test_index_named_source_is_not_replaced_by_inventory(self):
        src = self.source("index.md", "평가 원문 본문".encode())
        result = self.run_extract(src)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("평가 원문 본문", self.converted("index-source"))
        self.assertIn("원문 변환본 색인", self.converted("index"))

    def test_unrelated_output_file_is_preserved(self):
        src = self.source("report.txt", b"source report")
        out = os.path.join(self.work, ".omo", "sources")
        os.makedirs(out)
        with open(os.path.join(out, "report.md"), "w") as fh:
            fh.write("user notes")
        result = self.run_extract(src)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.converted("report"), "user notes")
        self.assertEqual(len([n for n in os.listdir(out) if n.startswith("report-")]), 1)

    def test_empty_source_is_not_successful_conversion(self):
        result = self.run_extract(self.source("empty.txt", b"  \n"))
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertIn("읽을 수 있는 본문 없음", result.stderr)


class KordocOutputReadsCleanlyInChecker(unittest.TestCase):
    """kordoc MCP 기본 출력(HTML 표)의 colspan 숫자를 점수로 읽지 않는다."""

    def test_html_table_colspan_not_read_as_score(self):
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        import consistency_check as cc

        html = ('<tr><td colspan="2">종합 점수 (a+b+c+d+e)</td><td colspan="4">14.1 /16점</td></tr>\n'
                '<tr><td colspan="2">종합 평가 등급</td><td colspan="4">매우 성공적</td></tr>\n')
        flat = cc.flatten_html_tables(html)
        self.assertEqual([v for v, _ in cc.find_composite_labeled(flat)], [cc.Decimal("14.1")])
        self.assertEqual(cc.flatten_html_tables("기준 <10점 미만"), "기준 <10점 미만")


if __name__ == "__main__":
    unittest.main()
