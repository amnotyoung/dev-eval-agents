"""기준 평가관 6명과 공통 계약(reference/평가관-공통계약.md)의 드리프트 검사.

공통 규칙은 계약 파일 한 곳에만 두고, 평가관 파일에는 기준별 정의·질문·루브릭·고유 규칙만
남긴다. 스킬은 모든 주장에 `[사실: Fn]`을 요구하는데 평가관 출력 형식에 사실 ID 열이 빠져
있던 사고(0.12.0)가 다시 생기지 않도록, 출력 표의 열을 계약에 적힌 열과 그대로 대조한다.
"""

import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTRACT = "평가관-공통계약.md"
CRITERIA = {
    "relevance": "REL-X1",
    "coherence": "COH-X1",
    "effectiveness": "EFF-X1",
    "efficiency": "EFI-X1",
    "sustainability": "SUS-X1",
    "impact": "IMP-X1",
}


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def contract_columns(text, title):
    """계약 §6에서 '**title** 표 — 열: a · b · …' 목록을 읽는다(굵게 표시 제거)."""
    match = re.search(rf"\*\*{re.escape(title)}\*\* (?:표|table) — (?:열|columns): ([^\n]+)", text)
    assert match, title
    listed = match.group(1).split(". ")[0]
    return [re.sub(r"\*\*", "", c).strip().rstrip(".") for c in listed.split(" · ")]


def table_header_after(text, heading):
    """heading 다음에 처음 나오는 표 머리글 행의 셀."""
    start = text.index(heading)
    for line in text[start:].splitlines()[1:]:
        if line.startswith("|"):
            return cells(line)
    raise AssertionError(f"{heading} 아래 표가 없음")


class ContractFile(unittest.TestCase):
    def test_contract_exists_in_both_languages_and_is_subordinate_to_norms(self):
        ko = read("reference", CONTRACT)
        en = read("docs", "en", "reference", CONTRACT)
        self.assertIn("공식 규범", ko)
        self.assertIn("우선", ko)
        self.assertIn("official norms", en)
        for text in (ko, en):
            self.assertIn("p.N", text)
            self.assertIn("300", text)  # 부분 Read 상한


class CriterionAgentsFollowContract(unittest.TestCase):
    ko_contract = read("reference", CONTRACT)
    en_contract = read("docs", "en", "reference", CONTRACT)

    def test_rating_table_columns_match_contract(self):
        expected = contract_columns(self.ko_contract, "핵심질문별 평정")
        expected_en = contract_columns(self.en_contract, "Rating by key question")
        for key in CRITERIA:
            name = f"dac-{key}-evaluator.md"
            got = table_header_after(read("agents", name), "### 핵심질문별 평정")
            self.assertTrue(got[0].startswith("핵심질문"), (name, got))
            self.assertTrue(got[2].startswith("점수("), (name, got))
            self.assertEqual(got[1:2] + got[3:], expected[1:2] + expected[3:], name)
            got_en = table_header_after(read("docs", "en", "agents", name), "### Rating by key question")
            self.assertTrue(got_en[0].startswith("Key question"), (name, got_en))
            self.assertTrue(got_en[2].startswith("Score ("), (name, got_en))
            self.assertEqual(got_en[1:2] + got_en[3:], expected_en[1:2] + expected_en[3:], name)

    def test_fact_ledger_additions_table_matches_contract(self):
        expected = contract_columns(self.ko_contract, "사실대장 추가 제안")
        expected_en = contract_columns(self.en_contract, "Fact-ledger additions")
        for key in CRITERIA:
            name = f"dac-{key}-evaluator.md"
            self.assertEqual(table_header_after(read("agents", name), "### 사실대장 추가 제안"), expected, name)
            self.assertEqual(
                table_header_after(read("docs", "en", "agents", name), "### Fact-ledger additions"),
                expected_en, name)

    def test_conflict_candidates_table_matches_contract(self):
        expected = contract_columns(self.ko_contract, "원자료 상충 후보")
        for key in CRITERIA:
            name = f"dac-{key}-evaluator.md"
            self.assertEqual(table_header_after(read("agents", name), "### 원자료 상충 후보"), expected, name)

    def test_agents_reference_contract_and_keep_only_criterion_rules(self):
        for key, prefix in CRITERIA.items():
            name = f"dac-{key}-evaluator.md"
            ko = read("agents", name)
            en = read("docs", "en", "agents", name)
            for text in (ko, en):
                self.assertIn(CONTRACT, text, name)
                self.assertIn(prefix, text, name)
            self.assertIn("고유 규칙", ko, name)
            self.assertNotIn("## 절대 규칙", ko, name)  # 공통 규칙을 다시 복제하지 않는다
            self.assertIn("-specific rules", en, name)

    def test_missing_evidence_is_never_a_score_of_one(self):
        for key in CRITERIA:
            name = f"dac-{key}-evaluator.md"
            self.assertIsNone(re.search(r"1 = [^·\n]*근거[^·\n]*(미비|부족|없음)", read("agents", name)), name)
            self.assertIsNone(re.search(r"1 = [^·\n]*evidence[^·\n]*lacking",
                                        read("docs", "en", "agents", name), re.IGNORECASE), name)
        self.assertIn("근거 부재를 1점으로 바꾸지 않는다", self.ko_contract)


class RatingTableAlignment(unittest.TestCase):
    """채점은 KOICA 평가 등급 결과표 양식을 따른다 — 질문별 1~4점, 기준 평점 = 질문 점수 평균.

    최종보고서 21건 대조에서 인간 평가팀은 질문 점수의 평균(또는 양식 가중평균)으로 기준 평점을
    냈고, 효과성은 산출물·중장기 성과/목표·형평성 3문항을 채점했다. 예전 지시("기계적 평균이
    아니라 총체적 판단")와 '가시성' 채점 문항은 이 양식과 어긋났다.
    """

    ACTIVE_KO = (("reference", CONTRACT), ("skills", "evaluate", "SKILL.md"), ("AGENTS.md",),
                 ("agents", "quality-verifier.md"), ("templates", "auditable-evaluation-brief-template.md"))

    def test_no_instruction_against_the_rating_table_formula(self):
        for path in self.ACTIVE_KO + tuple(("agents", f"dac-{k}-evaluator.md") for k in CRITERIA):
            self.assertNotIn("기계적 평균이 아니라", read(*path), "/".join(path))
            self.assertNotIn("기계적으로 평균하지 말고", read(*path), "/".join(path))
        for path in (("docs", "en", "reference", CONTRACT), ("docs", "en", "agents", "quality-verifier.md"),
                     ("docs", "en", "agents", "dac-effectiveness-evaluator.md")):
            self.assertNotIn("not a mechanical average", read(*path), "/".join(path))

    def test_contract_and_skill_state_the_formula(self):
        self.assertIn("채점 질문 점수의 평균", read("reference", CONTRACT))
        self.assertIn("0.5점 단위", read("reference", CONTRACT))
        self.assertIn("기준 평점 산식", read("skills", "evaluate", "SKILL.md"))
        digest = read("reference", "KOICA-평가지침-2024-다이제스트.md")
        self.assertIn("## 2-1. ★ 평가 등급 결과표", digest)
        self.assertIn("기준 평점 = 채점 질문 점수의 평균", digest)
        self.assertIn("## 2-1. ★ Rating table", read("docs", "en", "reference", "KOICA-평가지침-2024-다이제스트.md"))

    def test_effectiveness_scores_outcome_not_visibility(self):
        ko = read("agents", "dac-effectiveness-evaluator.md")
        self.assertIn("2. **중장기 성과(outcome)·목표(goal) 달성**", ko)
        self.assertIn("추가 확인(채점하지 않음)", ko)
        self.assertNotIn("| ③ 가시성 |", ko)
        en = read("docs", "en", "agents", "dac-effectiveness-evaluator.md")
        self.assertIn("**Medium/long-term outcome and goal achievement**", en)

    def test_grade_table_boundaries_are_half_open(self):
        for path in (("skills", "evaluate", "SKILL.md"), ("AGENTS.md",)):
            body = read(*path)
            self.assertIn("16 이상 18 미만", body, "/".join(path))
            self.assertNotIn("| 16~18 |", body, "/".join(path))


class SourceAnalystRole(unittest.TestCase):
    """원문을 끝까지 읽는 역할은 자료 정리관 하나다(e2e에서 평가총괄이 직접 원문을 읽어
    위임 전에 컨텍스트 20만 토큰을 썼다). 검증자는 기준 간 교차 정합을 본다."""

    def test_source_analyst_writes_only_ledger_and_index(self):
        ko = read("agents", "source-analyst.md")
        self.assertIn("tools: Read, Grep, Glob, Write", ko)
        self.assertNotIn("Edit", ko.split("---")[1])
        for token in ("auditable-evaluation-brief.md", "source-index.md", "30~80행", "점수·등급"):
            self.assertIn(token, ko)
        self.assertIn("source-index.md", read("docs", "en", "agents", "source-analyst.md"))

    def test_evaluate_delegates_reading_before_the_ledger_gate(self):
        skill = read("skills", "evaluate", "SKILL.md")
        self.assertIn("원문 전체를 직접 읽지 않는다", skill)
        self.assertIn("`source-analyst`", skill)
        self.assertLess(skill.index("`source-analyst`에게 포그라운드로 위임"), skill.index("--ledger-only"))
        self.assertIn("쪽 색인 `source-index.md`", skill)

    def test_verifier_checks_cross_criterion_consistency_and_reads_partially(self):
        ko = read("agents", "quality-verifier.md")
        self.assertIn("## (C2) 기준 간 교차 정합", ko)
        self.assertIn("이중 감점", ko)
        self.assertIn("원문을 처음부터 정독하지 않는다", ko)
        self.assertIn("## (C2) Cross-criterion consistency", read("docs", "en", "agents", "quality-verifier.md"))


class DelegationCarriesContract(unittest.TestCase):
    def test_evaluate_skill_and_codex_fallback_pass_the_contract(self):
        skill = read("skills", "evaluate", "SKILL.md")
        self.assertTrue(f"<root>/reference/{CONTRACT}" in skill, "evaluate 스킬이 계약 절대경로를 넘기지 않음")
        self.assertTrue(CONTRACT in read("AGENTS.md"), "AGENTS.md가 계약을 참조하지 않음")
        self.assertTrue(CONTRACT in read("docs", "en", "AGENTS.md"), "docs/en/AGENTS.md가 계약을 참조하지 않음")


if __name__ == "__main__":
    unittest.main()
