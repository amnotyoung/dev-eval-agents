"""중복 사본·플러그인 정본 ID 충돌 검사기의 회귀 테스트."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import repository_hygiene_check as hygiene  # noqa: E402


def frontmatter(name, body):
    return f"---\nname: {name}\ndescription: test\n---\n\n{body}\n"


class Files:
    """임시 파일 집합을 만들고 검사하는 작은 테스트 헬퍼."""

    def __init__(self, files):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.paths = sorted(files)
        for relative, content in files.items():
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

    def inspect(self, allowed_copy_paths=()):
        return hygiene.inspect(self.root, self.paths, allowed_copy_paths)

    def close(self):
        self.temp.cleanup()


class RepositoryContract(unittest.TestCase):
    def test_current_repository_passes(self):
        paths = hygiene.git_inventory(ROOT)
        allowed_copy_paths = hygiene.load_copy_allowlist(ROOT)
        issues = hygiene.inspect(ROOT, paths, allowed_copy_paths)
        self.assertEqual(issues, [], "\n".join(map(str, issues)))

    def test_git_inventory_excludes_ignored_copy_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / ".gitignore").write_text(".local/\n", encoding="utf-8")
            (root / "base.md").write_text("canonical\n", encoding="utf-8")
            ignored = root / ".local" / "base 2.md"
            ignored.parent.mkdir()
            ignored.write_text("copy\n", encoding="utf-8")

            paths = hygiene.git_inventory(root)
            self.assertIn("base.md", paths)
            self.assertNotIn(".local/base 2.md", paths)


class CopySuffixContract(unittest.TestCase):
    def assert_issue(self, issues, code):
        self.assertIn(code, {issue.code for issue in issues}, issues)

    def test_numbered_file_with_canonical_sibling_fails(self):
        files = Files(
            {
                "scripts/check-mirror-sync.sh": "canonical\n",
                "scripts/check-mirror-sync 2.sh": "copy\n",
            }
        )
        try:
            self.assert_issue(files.inspect(), "copy-suffix-collision")
        finally:
            files.close()

    def test_copied_skill_directory_fails(self):
        files = Files(
            {
                "skills/evaluate/SKILL.md": frontmatter("evaluate", "# Evaluate"),
                "skills/evaluate 2/SKILL.md": frontmatter("evaluate-2", "# Copy"),
            }
        )
        try:
            self.assert_issue(files.inspect(), "copy-suffix-collision")
        finally:
            files.close()

    def test_two_digit_copy_suffix_fails(self):
        files = Files(
            {
                "docs/guide.md": "canonical\n",
                "docs/guide 10.md": "copy\n",
            }
        )
        try:
            self.assert_issue(files.inspect(), "copy-suffix-collision")
        finally:
            files.close()

    def test_copy_suffix_finds_case_variant_canonical_sibling(self):
        files = Files(
            {
                "docs/Guide.md": "canonical\n",
                "docs/guide copy.md": "copy\n",
            }
        )
        try:
            self.assert_issue(files.inspect(), "copy-suffix-collision")
        finally:
            files.close()

    def test_windows_style_copy_suffix_fails(self):
        files = Files(
            {
                "docs/guide.md": "canonical\n",
                "docs/guide - Copy.md": "copy\n",
            }
        )
        try:
            self.assert_issue(files.inspect(), "copy-suffix-collision")
        finally:
            files.close()

    def test_explicit_exact_path_allowlist_permits_intentional_numeric_pair(self):
        files = Files(
            {
                "docs/phase.md": "overview\n",
                "docs/phase 2.md": "second phase\n",
            }
        )
        try:
            issues = files.inspect({"docs/phase 2.md"})
            self.assertEqual(issues, [])
        finally:
            files.close()

    def test_standalone_numeric_title_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            issues = hygiene.inspect(Path(directory), ["docs/phase 2.md"])
        self.assertEqual(issues, [])

    def test_intentional_pairs_and_mirrors_pass(self):
        files = Files(
            {
                "assets/logo.svg": "svg\n",
                "assets/logo.png": "png\n",
                "README.md": "English\n",
                "README.ko.md": "Korean\n",
                "agents/example-agent.md": frontmatter("example-agent", "# 한국어"),
                "docs/en/agents/example-agent.md": (
                    "> English reference translation of the canonical agent.\n\n"
                    + frontmatter("example-agent", "# English")
                ),
            }
        )
        try:
            self.assertEqual(files.inspect(), [])
        finally:
            files.close()


class CanonicalIdentityContract(unittest.TestCase):
    def assert_issue(self, issues, code):
        self.assertIn(code, {issue.code for issue in issues}, issues)

    def test_duplicate_agent_id_fails(self):
        files = Files(
            {
                "agents/alpha.md": frontmatter("alpha", "# Alpha"),
                "agents/beta.md": frontmatter("alpha", "# Beta"),
            }
        )
        try:
            issues = files.inspect()
            self.assert_issue(issues, "duplicate-canonical-id")
            self.assert_issue(issues, "canonical-id-path-mismatch")
        finally:
            files.close()

    def test_semantically_equivalent_agent_ids_fail(self):
        files = Files(
            {
                "agents/example-agent.md": frontmatter("example-agent", "# Hyphen"),
                "agents/example_agent.md": frontmatter("example_agent", "# Underscore"),
            }
        )
        try:
            issues = files.inspect()
            self.assert_issue(issues, "invalid-canonical-id")
            self.assert_issue(issues, "duplicate-canonical-id")
        finally:
            files.close()

    def test_skill_name_must_match_directory(self):
        files = Files(
            {
                "skills/evaluate/SKILL.md": frontmatter("quality-review", "# Evaluate")
            }
        )
        try:
            self.assert_issue(files.inspect(), "canonical-id-path-mismatch")
        finally:
            files.close()

    def test_executable_agent_rejects_reference_preamble(self):
        files = Files(
            {
                "agents/example.md": (
                    "> reference-only preamble\n\n"
                    + frontmatter("example", "# Agent")
                )
            }
        )
        try:
            self.assert_issue(files.inspect(), "invalid-frontmatter-name")
        finally:
            files.close()

    def test_skill_frontmatter_must_start_on_first_line(self):
        files = Files(
            {"skills/example/SKILL.md": "\n" + frontmatter("example", "# Skill")}
        )
        try:
            self.assert_issue(files.inspect(), "invalid-frontmatter-name")
        finally:
            files.close()

    def test_same_skill_body_after_frontmatter_fails(self):
        files = Files(
            {
                "skills/alpha/SKILL.md": frontmatter("alpha", "# Same body"),
                "skills/beta/SKILL.md": frontmatter("beta", "# Same body"),
            }
        )
        try:
            self.assert_issue(files.inspect(), "duplicate-canonical-body")
        finally:
            files.close()

    def test_missing_skill_entrypoint_fails(self):
        files = Files({"skills/example/references/guide.md": "support\n"})
        try:
            self.assert_issue(files.inspect(), "missing-skill-entrypoint")
        finally:
            files.close()

    def test_direct_skills_document_is_not_a_skill_directory(self):
        files = Files({"skills/README.md": "overview\n"})
        try:
            self.assertEqual(files.inspect(), [])
        finally:
            files.close()

    def test_portable_case_collision_fails(self):
        # 합성 경로를 직접 넘겨 대소문자 비구분 파일시스템에서도 재현 가능하게 한다.
        with tempfile.TemporaryDirectory() as directory:
            issues = hygiene.inspect(Path(directory), ["Docs/A.md", "docs/a.md"])
        self.assert_issue(issues, "portable-path-collision")

    def test_portable_unicode_normalization_collision_fails(self):
        # 합성 경로를 사용해 호스트 파일시스템의 NFC/NFD 저장 방식과 무관하게 검사한다.
        with tempfile.TemporaryDirectory() as directory:
            issues = hygiene.inspect(
                Path(directory), ["docs/caf\u00e9.md", "docs/cafe\u0301.md"]
            )
        self.assert_issue(issues, "portable-path-collision")


if __name__ == "__main__":
    unittest.main()
