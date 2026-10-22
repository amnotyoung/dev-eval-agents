"""AGENTS.md 단일 문서 구조 검사 — 옛 CLAUDE.md(저장소 개발 지침)와 Codex 평가 폴백을 합쳤다.

- 1부(저장소 개발)와 2부(Codex 직접 실행 평가 폴백)가 한 문서에 있고, 2부는 표지로 감싼다.
- 오픈웨이트 러너는 2부만 시스템 프롬프트로 쓴다 — 개발 지침이 평가 모델에 섞이지 않는다.
- CLAUDE.md가 다시 생겨 지침이 두 곳으로 갈라지지 않는다.
"""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import open_runner  # noqa: E402

START = "<!-- deveval:codex-fallback:start -->"
END = "<!-- deveval:codex-fallback:end -->"


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


class SingleAgentsDocument(unittest.TestCase):
    def test_no_separate_claude_md(self):
        self.assertFalse(os.path.exists(os.path.join(ROOT, "CLAUDE.md")))
        self.assertFalse(os.path.exists(os.path.join(ROOT, "docs", "en", "CLAUDE.md")))

    def test_both_parts_in_order_with_markers(self):
        for path, part1, part2, dev_section, workflow in (
            (("AGENTS.md",), "# 1부 · 저장소 개발 지침", "# 2부 · Codex 직접 실행 평가 폴백",
             "## 경로 규칙", "## 평가 워크플로 (Codex 단일 에이전트)"),
            (("docs", "en", "AGENTS.md"), "# Part 1 · Repository development",
             "# Part 2 · Codex direct-run evaluation fallback",
             "## Path rules", "## Evaluation Workflow (Codex single agent)"),
        ):
            body = read(*path)
            name = "/".join(path)
            self.assertEqual(body.count(START), 1, name)
            self.assertEqual(body.count(END), 1, name)
            before, inside = body.split(START)[0], body.split(START)[1].split(END)[0]
            self.assertIn(part1, before, name)
            self.assertIn(dev_section, before, name)
            self.assertIn(part2, inside, name)
            self.assertIn(workflow, inside, name)
            self.assertNotIn(part1, inside, name)

    def test_open_runner_uses_only_the_evaluation_part(self):
        system = open_runner.evaluation_instructions(read("AGENTS.md"))
        self.assertIn("평가 워크플로 (Codex 단일 에이전트)", system)
        self.assertNotIn("1부 · 저장소 개발 지침", system)
        self.assertNotIn("## 이 저장소 = 플러그인", system)
        legacy = "# 예전 판\n평가 워크플로 전체"
        self.assertEqual(open_runner.evaluation_instructions(legacy), legacy)

    def test_mirror_check_tracks_the_single_document(self):
        script = read("scripts", "check-mirror-sync.sh")
        self.assertIn('MIRRORED_FILES=("AGENTS.md")', script)
        self.assertNotIn('"CLAUDE.md"', read(".github", "workflows", "mirror-sync.yml"))


if __name__ == "__main__":
    unittest.main()
