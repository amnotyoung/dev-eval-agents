"""The open-model entry point must not label invalid model output a success."""

import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import open_runner


class OpenRunnerValidation(unittest.TestCase):
    def setUp(self):
        self.clean = (ROOT / "tests/fixtures/auditable-brief-clean.md").read_text()

    def test_valid_brief_passes_both_checks(self):
        self.assertEqual(open_runner.validate_output(self.clean)[0], 0)

    def test_wrong_grade_and_wrong_sum_fail(self):
        for replacement in ("13/20, A(안)", "19/20, A(안)"):
            with self.subTest(replacement=replacement):
                bad = self.clean.replace("13/20, D(안)", replacement)
                self.assertEqual(open_runner.validate_output(bad)[0], 2)

    def test_empty_or_nontext_response_is_uncheckable(self):
        for value in ("", "  ", None, []):
            self.assertEqual(open_runner.validate_output(value)[0], 3)

    def test_invalid_output_is_saved_with_failed_status_and_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "draft.md"
            with patch.object(open_runner, "chat", return_value={"message": {"content": "13/20, A"}}), \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                status = open_runner.main(["--out", str(output)])
            self.assertEqual(status, 2)
            self.assertIn("Validation exit code: **2**", output.read_text())

    def test_missing_target_never_calls_model(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(open_runner, "chat") as chat, \
                contextlib.redirect_stderr(io.StringIO()):
            status = open_runner.main(["--target", str(Path(tmp) / "missing.md")])
            self.assertEqual(status, 3)
            chat.assert_not_called()

    def test_bad_response_shape_is_uncheckable(self):
        with patch.object(open_runner, "chat", return_value={"message": None}), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(open_runner.main([]), 3)


if __name__ == "__main__":
    unittest.main()
