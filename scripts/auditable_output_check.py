#!/usr/bin/env python3
"""DevEval 기본 평가 브리프의 최소 감사추적 계약을 검사한다.

이 검사는 평가가 옳은지 대신, 평정 전에 만든 원문 사실대장이 비교축 차이를
분류했는지와 근거·반대근거·상충·검증 정정이 최종 산출물에서 사라지지 않았는지
형식적으로 확인한다. 원문에서 같은 사실을 찾아 같은 F-ID로 묶는 의미 판단과
상충의 내용 판정은 평가관과 quality-verifier의 몫이다.

사용법: python3 scripts/auditable_output_check.py <evaluation-brief.md>
        python3 scripts/auditable_output_check.py --ledger-only <working-brief.md>
종료 코드: 0 = 계약 충족 / 2 = 필수 산출물 누락 / 1 = 파일 읽기 실패.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from consistency_check import band20


REQUIRED_SECTIONS = (
    "평가 범위·자료·방법",
    "원문 사실대장",
    "종합 평정",
    "기준별 상세 평정",
    "상충·불일치 등록부",
    "평가 불가·미확인 등록부",
    "검증 정정·점수 재산정",
    "결론 연계 제언",
    "한계·사람 판단",
)
CRITERIA = ("적절성", "일관성", "효과성", "효율성", "지속가능성")
CONFLICT_MARKER = re.compile(r"\[상충:\s*(X\d+)\]", re.IGNORECASE)
CONFLICT_ID = re.compile(r"\bX\d+\b", re.IGNORECASE)
FACT_MARKER = re.compile(r"\[사실:\s*(F\d+)\]", re.IGNORECASE)
FACT_ID = re.compile(r"F\d+", re.IGNORECASE)
CORRECTION_ID = re.compile(r"\bV\d+\b", re.IGNORECASE)
PLACEHOLDER_VALUES = {"-", "—", "–", "...", "…", "n/a", "na", "tbd"}
LEDGER_HEADERS = (
    "사실 ID",
    "사실 키·정의",
    "값·상태",
    "단위",
    "분모·대상",
    "기준기간",
    "집계규칙",
    "상태기준일",
    "문서·버전",
    "원문 위치",
    "대조 판정·상충 ID",
)
SIGNATURE_HEADERS = (
    "값·상태",
    "단위",
    "분모·대상",
    "기준기간",
    "집계규칙",
    "상태기준일",
    "문서·버전",
)
UNKNOWN_VALUES = {"미상", "불명", "확인 필요", "확인필요", "unknown"}
GENERIC_EXPLANATIONS = {
    "근거",
    "구체 근거",
    "설명",
    "구체 설명",
    "사유",
    "미작성",
    "확인 필요",
    "확인필요",
    "tbd",
}
NO_MATERIAL_CONFLICT = re.compile(
    r"(?m)^\s*(?:[-*]\s*)?(?:\*\*)?중대 상충 없음\s*[—-]\s*"
    r".+(?:점검함|점검 완료|점검을 완료함)\.?\s*(?:\*\*)?\s*$"
)
CRITERION_UNAVAILABLE = re.compile(
    r"(?m)^\s*(?:[-*]\s*)?(?:\*\*)?기준 전체 평가 불가(?:\*\*)?"
    r"(?:\s*[—:-]\s*(?!아님|아니|불가하지)[^\n]+)?\s*$"
)
# 대괄호로 감싸도 정상인 플러그인 표지 — 그 밖의 대괄호-only 값은 템플릿 자리표시자다.
LEGIT_BRACKET = re.compile(
    r"^\[\s*(?:(?:사실|상충|근거|출처)\s*:|INFO\s*:|확인\s*필요|사람\s*판단\s*필요)",
    re.IGNORECASE,
)
LABELED_BRACKET_VALUE = re.compile(r"^\s*[-*]\s+[^:\n]{1,60}:\s*(\[[^\]\n]*\])\s*$")
STANDALONE_BRACKET = re.compile(r"^\s*(\[[^\]\n]+\])\s*$")
SCORE_VALUE = re.compile(r"\d(?:\.\d{1,2})?")
SCORE_RANGE = re.compile(r"\d(?:\.\d{1,2})?[~∼–-]\d(?:\.\d{1,2})?")
UNSCORED = re.compile(r"평가\s*불가|보류|근거\s*불충분|산정\s*불가")
COMPOSITE_20 = re.compile(r"(?<![\d.])(\d{1,2}(?:\.\d{1,2})?)\s*/\s*20(?!\d)")
COMPOSITE_QUALIFIED = re.compile(r"보류|잠정|범위|단서|[~∼]|\d\s*[–-]\s*\d")
STRICT_COMPOSITE = re.compile(
    r"(?:(?:단서부|잠정|범위)\s*)*"
    r"(?P<lo>\d{1,2}(?:\.\d{1,2})?)(?:\s*[~∼–-]\s*(?P<hi>\d{1,2}(?:\.\d{1,2})?))?"
    r"\s*/\s*20\s*,\s*(?P<grade>[A-F])(?:\(안\))?"
    r"(?:\s*[~∼–-]\s*(?P<grade_hi>[A-F])(?:\(안\))?)?"
    r"(?:\s*[—–-]\s*(?:매우 성공적|부분 성공적|성공적|미흡))?\s*"
)
CONFLICT_HEADERS = (
    "ID",
    "사실 ID",
    "쟁점",
    "값·진술 A(원문 위치)",
    "값·진술 B(원문 위치)",
    "대조 결과·가능한 설명",
    "해결 상태",
    "점수·결론 영향",
    "후속 확인",
)


def criterion_heading_pattern(title: str) -> str:
    return (
        rf"(?m)^###\s+(?:\d+[.)]\s*)?{re.escape(title)}"
        rf"(?:\s*\([^\n)]*\))?(?:\s+(?:평정|평가))?\s*$"
    )


def section(text: str, title: str) -> str | None:
    """Return a level-2 Markdown section whose heading contains title."""
    match = re.search(rf"(?m)^##\s+[^\n]*{re.escape(title)}[^\n]*$", text)
    if not match:
        return None
    next_heading = re.search(r"(?m)^##\s+", text[match.end():])
    end = match.end() + next_heading.start() if next_heading else len(text)
    return text[match.end():end]


def subsection(text: str, title: str) -> str | None:
    """Return a level-3 Markdown subsection whose heading contains title."""
    match = re.search(criterion_heading_pattern(title), text)
    if not match:
        return None
    next_heading = re.search(r"(?m)^###\s+", text[match.end():])
    end = match.end() + next_heading.start() if next_heading else len(text)
    return text[match.end():end]


def markdown_cells(line: str) -> list[str] | None:
    """Split one pipe table row, preserving escaped pipes inside cells."""
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return None
    cells = re.split(r"(?<!\\)\|", stripped[1:-1])
    return [cell.replace(r"\|", "|").strip() for cell in cells]


def normalized(value: str) -> str:
    """Conservative comparison normalization; semantic equivalence stays explicit."""
    value = unicodedata.normalize("NFKC", value)
    return re.sub(r"\s+", " ", value).strip().casefold()


def is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def is_placeholder(cell: str) -> bool:
    """Reject empty sentinels and fully bracketed template cells."""
    return normalized(cell) in PLACEHOLDER_VALUES or bool(
        re.fullmatch(r"\[[^\]]*\]", cell)
    )


def is_single_source_verdict(value: str) -> bool:
    return bool(re.fullmatch(r"단일 출처\s*[—-]\s*전체검색 완료", value.strip()))


def is_agreement_verdict(value: str) -> bool:
    return normalized(value) == "일치"


def is_unknown_value(value: str) -> bool:
    """Treat decorated unknown labels as unknown, not as confirmed agreement."""
    value = normalized(value)
    if value in UNKNOWN_VALUES:
        return True
    return bool(
        re.match(
            r"^(?:미상|불명|확인\s*필요|unknown)(?:\s|\(|\[|/|:|-|—)",
            value,
        )
    )


def has_concrete_explanation(value: str) -> bool:
    """Require prose after ``설명됨:`` instead of a template placeholder."""
    match = re.search(r"설명됨\s*:\s*(.+)$", value.strip())
    if not match:
        return False
    explanation = match.group(1).strip()
    if is_placeholder(explanation) or is_unknown_value(explanation):
        return False
    return normalized(explanation) not in GENERIC_EXPLANATIONS


def ledger_table(body: str) -> tuple[list[str] | None, list[list[str]]]:
    """Find the source-fact-ledger table and return its header and data rows."""
    lines = body.splitlines()
    for index, line in enumerate(lines):
        header = markdown_cells(line)
        if not header or header[0] != "사실 ID":
            continue
        if index + 1 >= len(lines):
            return header, []
        separator = markdown_cells(lines[index + 1])
        if (
            separator is None
            or len(separator) != len(header)
            or not is_separator(separator)
        ):
            return header, []
        rows: list[list[str]] = []
        for candidate in lines[index + 2:]:
            cells = markdown_cells(candidate)
            if cells is None:
                break
            rows.append(cells)
        return header, rows
    return None, []


def conflict_table(body: str) -> tuple[list[str] | None, list[list[str]], int]:
    """Return the single conflict-register table and its header count."""

    lines = body.splitlines()
    header_indexes: list[int] = []
    for index, line in enumerate(lines):
        cells = markdown_cells(line)
        if cells and cells[0] == "ID":
            header_indexes.append(index)
    if not header_indexes:
        return None, [], 0

    index = header_indexes[0]
    header = markdown_cells(lines[index])
    if index + 1 >= len(lines):
        return header, [], len(header_indexes)
    separator = markdown_cells(lines[index + 1])
    if (
        separator is None
        or header is None
        or len(separator) != len(header)
        or not is_separator(separator)
    ):
        return header, [], len(header_indexes)
    rows: list[list[str]] = []
    for candidate in lines[index + 2:]:
        cells = markdown_cells(candidate)
        if cells is None:
            break
        rows.append(cells)
    return header, rows, len(header_indexes)


def inspect_ledger(text: str) -> tuple[list[str], set[str], dict[str, set[str]]]:
    """Validate the early source-fact ledger and return F-IDs and X→F links."""
    violations: list[str] = []
    body = section(text, "원문 사실대장")
    if body is None:
        return ["필수 섹션 누락: 원문 사실대장"], set(), {}

    ledger_header_count = 0
    for line in body.splitlines():
        cells = markdown_cells(line)
        if cells and cells[0] == "사실 ID":
            ledger_header_count += 1
    if ledger_header_count > 1:
        violations.append(
            "원문 사실대장 표는 하나만 허용됨 — 모든 원문 표기를 같은 표에 합쳐야 함"
        )

    header, raw_rows = ledger_table(body)
    if header is None:
        return ["원문 사실대장 표 누락"], set(), {}
    missing_headers = [field for field in LEDGER_HEADERS if field not in header]
    for field in missing_headers:
        violations.append(f"원문 사실대장 필드 누락: {field}")
    if missing_headers:
        return violations, set(), {}

    positions = {field: header.index(field) for field in LEDGER_HEADERS}
    rows_by_fact: dict[str, list[dict[str, str]]] = defaultdict(list)
    fact_ids_by_key: dict[str, set[str]] = defaultdict(set)
    fact_key_labels: dict[str, str] = {}
    ledger_conflicts: dict[str, set[str]] = defaultdict(set)
    for row_number, cells in enumerate(raw_rows, 1):
        if len(cells) != len(header):
            violations.append(
                f"원문 사실대장 행 {row_number} 열 수 불일치 — {len(header)}개 필드가 필요함"
            )
            continue
        fact_id = cells[positions["사실 ID"]].upper()
        if not FACT_ID.fullmatch(fact_id):
            violations.append(f"원문 사실대장 행 {row_number}의 사실 ID 형식 오류: {fact_id or '(빈칸)'}")
            continue
        record = {field: cells[index] for field, index in positions.items()}
        for field, value in record.items():
            marker_value = field == "대조 판정·상충 ID" and bool(
                CONFLICT_MARKER.fullmatch(value)
            )
            if not value or (is_placeholder(value) and not marker_value):
                violations.append(f"{fact_id}의 필수 필드가 비었거나 자리표시자임: {field}")
        rows_by_fact[fact_id].append(record)
        normalized_key = normalized(record["사실 키·정의"])
        fact_ids_by_key[normalized_key].add(fact_id)
        fact_key_labels.setdefault(normalized_key, record["사실 키·정의"])
        for conflict_id in CONFLICT_MARKER.findall(record["대조 판정·상충 ID"]):
            ledger_conflicts[conflict_id.upper()].add(fact_id)

    if not rows_by_fact:
        violations.append("원문 사실대장에 F-ID 원문 표기 행이 하나 이상 필요함")
        return violations, set(), dict(ledger_conflicts)

    for normalized_key, linked_ids in sorted(fact_ids_by_key.items()):
        if len(linked_ids) > 1:
            label = fact_key_labels[normalized_key]
            violations.append(
                f"동일 사실 키·정의 '{label}'가 여러 F-ID로 분할됨: "
                + ", ".join(sorted(linked_ids))
            )

    for fact_id, records in sorted(rows_by_fact.items()):
        keys = {normalized(record["사실 키·정의"]) for record in records}
        if len(keys) > 1:
            violations.append(f"{fact_id}가 서로 다른 사실 키·정의에 재사용됨")

        occurrence_keys = [
            (
                normalized(record["문서·버전"]),
                normalized(record["원문 위치"]),
            )
            for record in records
        ]
        if len(set(occurrence_keys)) != len(occurrence_keys):
            violations.append(
                f"{fact_id}에 동일한 문서·버전과 원문 위치가 중복 등록됨"
            )

        comparisons = [record["대조 판정·상충 ID"] for record in records]
        conflict_sets = [
            {item.upper() for item in CONFLICT_MARKER.findall(comparison)}
            for comparison in comparisons
        ]
        signatures = {
            tuple(normalized(record[field]) for field in SIGNATURE_HEADERS)
            for record in records
        }
        has_unknown = any(
            is_unknown_value(record[field])
            for record in records
            for field in SIGNATURE_HEADERS
        )

        if len(records) == 1:
            if conflict_sets[0]:
                violations.append(f"{fact_id}는 상충 표기가 있으나 원문 표기 행이 한 개뿐임")
            if not is_single_source_verdict(comparisons[0]):
                violations.append(f"{fact_id}의 단일 행은 '단일 출처 — 전체검색 완료'로 대조 판정을 남겨야 함")
            continue

        needs_explanation = len(signatures) > 1 or has_unknown
        if needs_explanation:
            all_conflicts = set().union(*conflict_sets)
            explained = [
                has_concrete_explanation(comparison)
                for comparison in comparisons
            ]
            if all_conflicts:
                if len(all_conflicts) > 1 or any(ids != all_conflicts for ids in conflict_sets):
                    violations.append(f"{fact_id}의 모든 상충 행은 하나의 동일한 X-ID로 연결해야 함")
            elif not all(explained):
                axes = "/".join(SIGNATURE_HEADERS)
                violations.append(
                    f"{fact_id}의 비교축({axes})이 다르거나 미상인데 "
                    "'설명됨: 구체 근거' 또는 '[상충: Xn]'이 없음"
                )
        elif not all(is_agreement_verdict(comparison) for comparison in comparisons):
            violations.append(f"{fact_id}의 동일한 반복 표기는 모든 행을 '일치'로 대조 판정해야 함")

    return violations, set(rows_by_fact), dict(ledger_conflicts)


def template_placeholders(text: str) -> list[tuple[int, str]]:
    """Find template prompts left in any table cell, labeled bullet value, or bare line.

    `[질문]`, `[통과 / 조건부 통과 / 반려]`, `[없음/Xn]` 같은 템플릿 안내문이 남아 있어도
    섹션 제목과 필드명만 보면 통과하던 빈틈을 막는다. `[사실: F1]`·`[근거: …]`·
    `[INFO: 확인 필요]`·`[사람 판단 필요]` 같은 플러그인 표지는 정상 값이다.
    """
    found: list[tuple[int, str]] = []
    in_fence = False
    for line_number, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        cells = markdown_cells(line)
        if cells is not None:
            if is_separator(cells):
                continue
            for cell in cells:
                if re.fullmatch(r"\[[^\]]*\]", cell) and not LEGIT_BRACKET.match(cell):
                    found.append((line_number, cell))
            continue
        for pattern in (LABELED_BRACKET_VALUE, STANDALONE_BRACKET):
            match = pattern.match(line)
            if match and not LEGIT_BRACKET.match(match.group(1)):
                found.append((line_number, match.group(1)))
                break
    return found


def summary_score_cells(overall: str) -> dict[str, str] | None:
    """Return criterion → post-verification score cell from the 종합 평정 table."""
    lines = overall.splitlines()
    for index, line in enumerate(lines):
        header = markdown_cells(line)
        if not header or header[0].strip("* ") != "기준":
            continue
        column = next((i for i, cell in enumerate(header) if "검증 후" in cell), None)
        if column is None:
            continue
        cells_by_criterion: dict[str, str] = {}
        for candidate in lines[index + 1:]:
            cells = markdown_cells(candidate)
            if cells is None:
                break
            if is_separator(cells) or len(cells) <= column:
                continue
            name = cells[0].strip("* ")
            if name in CRITERIA:
                cells_by_criterion[name] = cells[column]
        return cells_by_criterion
    return None


def score_kind(cell: str) -> str:
    """Classify a criterion score cell: score / range / unscored / placeholder / invalid."""
    if is_placeholder(cell):
        return "placeholder"
    compact = re.sub(r"\s*\([^()]*\)\s*$", "", cell)   # `2.75 (2.5+3.0)` 같은 산식 주석
    compact = re.sub(r"[*\s]", "", compact)
    compact = re.sub(r"점$", "", compact)
    if SCORE_VALUE.fullmatch(compact):
        return "score" if 1 <= float(compact) <= 4 else "invalid"
    if SCORE_RANGE.fullmatch(compact):
        lo, hi = re.split(r"[~∼–-]", compact)
        return "range" if 1 <= Decimal(lo) <= Decimal(hi) <= 4 else "invalid"
    if UNSCORED.search(cell):
        return "unscored"
    return "invalid"


def inspect_scores(overall: str, detail: str) -> list[str]:
    """근거 없으면 등급 없음 — 평가 불가 기준에 점수를 붙이거나 종합점수를 단정하지 않는다."""
    violations: list[str] = []
    cells = summary_score_cells(overall)
    if cells is None:
        return ["종합 평정 표 누락 — '기준' 열과 '검증 후' 점수 열이 있는 기준별 표가 필요함"]
    kinds: dict[str, str] = {}
    for criterion in CRITERIA:
        count = sum(bool(row and row[0].strip("* ") == criterion)
                    for row in (markdown_cells(line) for line in overall.splitlines()))
        if count > 1:
            violations.append(f"종합 평정 표의 {criterion} 행이 중복됨")
    for criterion in CRITERIA:
        if criterion not in cells:
            violations.append(f"종합 평정 표에 {criterion} 행이 없음")
            continue
        kind = score_kind(cells[criterion])
        kinds[criterion] = kind
        if kind in ("invalid", "placeholder"):
            violations.append(
                f"종합 평정 {criterion}의 검증 후 점수 형식 오류: '{cells[criterion]}' — "
                "1~4점, 범위(예: 2~3) 또는 '평가 불가'로 적어야 함"
            )
        unavailable = bool(CRITERION_UNAVAILABLE.search(subsection(detail, criterion) or ""))
        if unavailable and kind in ("score", "range"):
            violations.append(
                f"{criterion}은(는) 상세 평정에서 '기준 전체 평가 불가'인데 종합 평정에 점수 "
                f"'{cells[criterion]}'이(가) 있음 — 근거 없으면 등급 없음"
            )
        if unavailable:
            kinds[criterion] = "unscored"

    composite_lines = [line for line in overall.splitlines() if re.search(r"검증 후 종합\s*점수", line)]
    if not composite_lines:
        violations.append("종합 평정에 '검증 후 종합점수·등급(안)' 줄이 없음")
        return violations
    if len(composite_lines) != 1:
        violations.append("검증 후 종합점수·등급 줄은 정확히 하나여야 함")
    composite_line = composite_lines[0]
    value = composite_line.split(":", 1)[1] if ":" in composite_line else composite_line
    value = value.replace("**", "").strip()
    unscored = [criterion for criterion, kind in kinds.items() if kind in ("unscored", "range")]
    if re.fullmatch(r"산정 보류(?:\s*[—–-]\s*[^\n]+)?", value) and not re.search(r"/\s*20|(?<![A-Za-z0-9])[A-F](?![A-Za-z0-9])", value):
        return violations
    parsed = STRICT_COMPOSITE.fullmatch(value)
    if parsed is None:
        violations.append("종합점수와 등급을 모두 해석할 수 없음 — '13/20, D' 또는 명시적 '산정 보류'가 필요함")
        return violations
    lo = Decimal(parsed['lo'])
    hi = Decimal(parsed['hi']) if parsed['hi'] else lo
    if not 5 <= lo <= hi <= 20:
        violations.append("종합점수 범위 오류 — 5~20점 안의 오름차순 값이어야 함")
    expected = (band20(lo), band20(hi))
    stated_grades = (parsed['grade'], parsed['grade_hi'] or parsed['grade'])
    if stated_grades != expected:
        violations.append(f"종합 등급-점수 괴리 — {lo}~{hi}/20은 {expected[0]}~{expected[1]}인데 {stated_grades[0]}~{stated_grades[1]}로 표기됨")
    if unscored and not parsed['hi']:
        violations.append(
            f"평가 불가·범위 기준({', '.join(unscored)})이 있는데 종합점수를 {lo}/20으로 "
            "단정함 — 단서부 범위 또는 산정 보류로 적어야 함"
        )
    if all(kinds.get(c) == "score" for c in CRITERIA):
        total = sum(Decimal(re.sub(r"[*\s점]", "", re.sub(r"\s*\([^()]*\)\s*$", "", cells[c]))) for c in CRITERIA)
        stated = lo
        if parsed['hi']:
            violations.append("5개 기준이 모두 점수인데 종합점수가 범위임 — 점추정과 민감도를 별도 줄에 적어야 함")
        if total != stated:
            violations.append(
                f"종합 평정의 기준별 검증 후 점수 합 {total}이(가) 검증 후 종합점수 {stated}/20과 다름"
            )
    return violations


def inspect(text: str) -> list[str]:
    violations: list[str] = []
    if re.search(r"\[\s*\]", text) or "[사업명]" in text:
        violations.append("템플릿 미작성 자리표시자([ ] 또는 [사업명])가 남아 있음")
    leftovers = template_placeholders(text)
    if leftovers:
        examples = ", ".join(f"줄 {n} {cell}" for n, cell in leftovers[:5])
        more = f" 외 {len(leftovers) - 5}곳" if len(leftovers) > 5 else ""
        violations.append(f"템플릿 자리표시자가 남아 있음 ({len(leftovers)}곳): {examples}{more}")
    sections: dict[str, str] = {}
    for title in REQUIRED_SECTIONS:
        body = section(text, title)
        if body is None:
            violations.append(f"필수 섹션 누락: {title}")
        else:
            sections[title] = body

    ledger_violations, fact_ids, ledger_conflicts = inspect_ledger(text)
    # REQUIRED_SECTIONS already reports the same missing-section error.
    if "원문 사실대장" not in sections:
        ledger_violations = [item for item in ledger_violations if "필수 섹션 누락" not in item]
    violations.extend(ledger_violations)

    detail = sections.get("기준별 상세 평정", "")
    for criterion in CRITERIA:
        if not re.search(criterion_heading_pattern(criterion), detail):
            violations.append(f"기준별 상세 평정 누락: {criterion}")
    for field in ("지지근거", "반대·제약근거", "근거 상태", "인접 점수"):
        if field not in detail:
            violations.append(f"상세 평정 필드 누락: {field}")
    support_column = None
    for line_number, line in enumerate(detail.splitlines(), 1):
        cells = markdown_cells(line)
        if cells is None or is_separator(cells):
            continue
        if any("핵심질문" in cell for cell in cells):
            support_column = next((i for i, cell in enumerate(cells) if "지지근거" in cell), None)
            continue
        if support_column is not None and FACT_MARKER.search(line):
            support = cells[support_column] if len(cells) > support_column else ""
            if (not support or normalized(support) in PLACEHOLDER_VALUES
                    or re.fullmatch(r"\[\s*(?:근거|출처)\s*:\s*\]", support)):
                violations.append(f"상세 평정 행 {line_number}의 지지근거가 비어 있음")
    detail_facts = {item.upper() for item in FACT_MARKER.findall(detail)}
    detail_conflict_links: dict[str, set[str]] = defaultdict(set)
    for line_number, line in enumerate(detail.splitlines(), 1):
        line_conflicts = {item.upper() for item in CONFLICT_MARKER.findall(line)}
        if not line_conflicts:
            continue
        line_facts = {item.upper() for item in FACT_MARKER.findall(line)}
        for conflict_id in line_conflicts:
            if not line_facts:
                violations.append(
                    f"상세 평정 행 {line_number}의 {conflict_id}에 [사실: Fn] 연결이 없음"
                )
            detail_conflict_links[conflict_id].update(line_facts)
    for fact_id in sorted(detail_facts - fact_ids):
        violations.append(f"상세 평정의 {fact_id}가 원문 사실대장에 없음")
    for fact_id in sorted(fact_ids - detail_facts):
        violations.append(f"원문 사실대장의 {fact_id}가 어느 상세 평정에도 [사실: {fact_id}]로 연결되지 않음")
    for criterion in CRITERIA:
        criterion_body = subsection(detail, criterion) or ""
        if not FACT_MARKER.search(criterion_body) and not CRITERION_UNAVAILABLE.search(
            criterion_body
        ):
            violations.append(
                f"{criterion} 상세 평정에 [사실: Fn] 근거 연결 또는 '기준 전체 평가 불가' 명시가 필요함"
            )

    overall = sections.get("종합 평정", "")
    for field in ("검증 후", "근거 상태", "검증 판정"):
        if field not in overall:
            violations.append(f"종합 평정 필드 누락: {field}")
    if "종합 평정" in sections:
        violations.extend(inspect_scores(overall, detail))

    register = sections.get("상충·불일치 등록부", "")
    detail_markers = {item.upper() for item in CONFLICT_MARKER.findall(detail)}
    register_header, raw_register_rows, register_table_count = conflict_table(register)
    if register_table_count > 1:
        violations.append("상충 등록부 표는 하나만 허용됨")
    register_records: dict[str, dict[str, str]] = {}
    row_ids: set[str] = set()
    if register_header is not None:
        missing_headers = [field for field in CONFLICT_HEADERS if field not in register_header]
        for field in missing_headers:
            violations.append(f"상충 등록부 필드 누락: {field}")
        positions = {
            field: register_header.index(field)
            for field in CONFLICT_HEADERS
            if field in register_header
        }
        for row_number, cells in enumerate(raw_register_rows, 1):
            if len(cells) != len(register_header):
                violations.append(
                    f"상충 등록부 행 {row_number} 열 수 불일치 — {len(register_header)}개 필드가 필요함"
                )
                continue
            conflict_id = cells[0].upper()
            if not CONFLICT_ID.fullmatch(conflict_id):
                violations.append(
                    f"상충 등록부 행 {row_number}의 ID 형식 오류: {conflict_id or '(빈칸)'}"
                )
                continue
            if conflict_id in row_ids:
                violations.append(f"상충 등록부 ID 중복: {conflict_id}")
                continue
            row_ids.add(conflict_id)
            if missing_headers:
                continue
            record = {field: cells[index] for field, index in positions.items()}
            for field, value in record.items():
                fact_marker_value = field == "사실 ID" and bool(
                    FACT_MARKER.fullmatch(value)
                )
                if not value or (is_placeholder(value) and not fact_marker_value):
                    violations.append(
                        f"상충 등록부 {conflict_id}의 필수 필드가 비었거나 자리표시자임: {field}"
                    )
            register_records[conflict_id] = record
    elif detail_markers or ledger_conflicts:
        violations.append("상충·불일치 등록부 표 누락")

    register_ids = row_ids
    if row_ids:
        for conflict_id in sorted(detail_markers - register_ids):
            violations.append(f"상세 평정의 {conflict_id}가 상충 등록부에 없음")
        for conflict_id in sorted(register_ids - detail_markers):
            violations.append(f"상충 등록부의 {conflict_id}가 상세 평정에 [상충: {conflict_id}]로 연결되지 않음")
        for conflict_id in sorted(set(ledger_conflicts) - register_ids):
            violations.append(f"원문 사실대장의 {conflict_id}가 상충 등록부에 없음")
        for conflict_id in sorted(register_ids - set(ledger_conflicts)):
            violations.append(f"상충 등록부의 {conflict_id}가 원문 사실대장에 [상충: {conflict_id}]로 연결되지 않음")
        register_fact_links: dict[str, set[str]] = {}
        for conflict_id, record in sorted(register_records.items()):
            linked = {item.upper() for item in FACT_MARKER.findall(record["사실 ID"])}
            register_fact_links[conflict_id] = linked
            if not linked:
                violations.append(f"상충 등록부의 {conflict_id}에 [사실: Fn] 연결이 없음")
            for fact_id in sorted(linked - fact_ids):
                violations.append(f"상충 등록부 {conflict_id}의 {fact_id}가 원문 사실대장에 없음")
        for conflict_id, linked_facts in sorted(ledger_conflicts.items()):
            register_linked = register_fact_links.get(conflict_id, set())
            missing = linked_facts - register_linked
            for fact_id in sorted(missing):
                violations.append(f"상충 등록부 {conflict_id}에 원문 사실대장 {fact_id} 연결이 없음")
            for fact_id in sorted(register_linked - linked_facts):
                violations.append(
                    f"상충 등록부 {conflict_id}의 {fact_id}가 원문 사실대장에서는 해당 상충과 연결되지 않음"
                )
            detail_linked = detail_conflict_links.get(conflict_id, set())
            for fact_id in sorted(linked_facts - detail_linked):
                violations.append(
                    f"상세 평정 {conflict_id}에 원문 사실대장 {fact_id} 연결이 없음"
                )
            for fact_id in sorted(detail_linked - linked_facts):
                violations.append(
                    f"상세 평정 {conflict_id}의 {fact_id}가 원문 사실대장에서는 해당 상충과 연결되지 않음"
                )
    elif detail_markers or ledger_conflicts:
        for conflict_id in sorted(detail_markers | set(ledger_conflicts)):
            violations.append(f"상세 평정 또는 원문 사실대장의 {conflict_id}가 상충 등록부에 없음")
    elif not NO_MATERIAL_CONFLICT.search(register):
        violations.append("상충 등록부에 상충 행 또는 '중대 상충 없음 — … 점검함' 확인문이 필요함")

    corrections = sections.get("검증 정정·점수 재산정", "")
    if not CORRECTION_ID.search(corrections) and "검증 정정 없음" not in corrections:
        violations.append("검증 정정 섹션에 V-ID 정정행 또는 '검증 정정 없음' 확인문이 필요함")
    for field in ("검증 전", "원문 대조", "종합점수·등급 영향"):
        if field not in corrections:
            violations.append(f"검증 정정 필드 누락: {field}")

    if "최종 등급은 평가담당관이 확정" not in text:
        violations.append("사람 확정 게이트 문구 누락")
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="감사 가능한 평가 브리프 산출물 계약 검사")
    parser.add_argument("brief", help="검사할 Markdown 평가 브리프")
    parser.add_argument(
        "--ledger-only",
        action="store_true",
        help="평정 전 작업본에서 원문 사실대장 계약만 조기 검사",
    )
    parser.add_argument("--isolation", help="원시 로그와 재대조할 독립성 확인서 JSON")
    parser.add_argument("--require-isolation", action="store_true", help="확인서 없이 병렬 평가를 통과시키지 않음")
    parser.add_argument("--scores", help="질문별 점수 JSON 정본")
    parser.add_argument("--before", help="검증 전 질문별 점수 JSON 정본")
    parser.add_argument("--require-scores", action="store_true", help="계산 정본·코드 투영 없이 통과시키지 않음")
    args = parser.parse_args()
    try:
        raw = Path(args.brief).read_bytes()
    except OSError as exc:
        print(f"읽기 실패: {exc}", file=sys.stderr)
        return 1
    for encoding in ("utf-8-sig", "cp949"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        print("읽기 실패: UTF-8·CP949로 읽을 수 없음", file=sys.stderr)
        return 1

    if args.ledger_only:
        violations, _fact_ids, _conflicts = inspect_ledger(text)
    else:
        violations = inspect(text)
        scores = Path(args.scores) if args.scores else Path(args.brief).parent / "verified-scores.json"
        if args.require_scores or args.scores or scores.exists() or "<!-- deveval:score-input" in text:
            try:
                import score_calculate
                result = score_calculate.verify_projection(args.brief, args.scores, args.before)
                _ledger_errors, fact_ids, _conflicts = inspect_ledger(text)
                used_facts = {f for c in result["criteria"] for q in c["questions"] for f in q["fact_ids"]}
                used_facts.update(f for s in result.get("scenarios", []) for change in s["changes"] for f in change["fact_ids"])
                violations.extend(f"점수 정본의 {f}가 원문 사실대장에 없음" for f in sorted(used_facts - fact_ids))
                registered = {cells[0].upper() for cells in conflict_table(section(text, "상충·불일치 등록부") or "")[1] if cells and CONFLICT_ID.fullmatch(cells[0])}
                used_conflicts = {x for c in result['criteria'] for x in c['conflict_ids']}
                violations.extend(f"점수 정본의 {x}가 상충 등록부에 없음" for x in sorted(used_conflicts - registered))
                manifest_path = Path(args.brief).parent / "delegation-manifest.json"
                if manifest_path.exists():
                    import json
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    if result["source_sha256"] != manifest.get("source_sha256"):
                        violations.append("점수 정본의 원문 해시가 위임 입력팩과 다름")
            except OSError as exc:
                print(f"점수 정본 확인 불가(exit 3): {exc}", file=sys.stderr)
                return 3
            except (ValueError, KeyError, TypeError) as exc:
                violations.append(f"점수 정본·코드 투영: {exc}")
        receipt = Path(args.isolation) if args.isolation else Path(args.brief).parent / "isolation.json"
        if args.require_isolation or args.isolation or receipt.exists():
            try:
                import delegation_check
                result = delegation_check.verify_receipt(receipt)
                violations.extend("독립성: " + item for item in result["violations"])
                if not result.get("prompt_bodies_verified") and "[INFO: 위임문 본문 미검증 — 암호화된 로그]" not in (section(text, "한계·사람 판단") or ""):
                    violations.append("독립성 한계 누락 — 9절에 [INFO: 위임문 본문 미검증 — 암호화된 로그]를 남겨야 함")
            except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
                print(f"독립성 확인 불가(exit 3): {exc}", file=sys.stderr)
                return 3
    if violations:
        label = "원문 사실대장" if args.ledger_only else "감사 가능한 평가 브리프"
        print(f"{label} 계약 위반:", file=sys.stderr)
        for index, item in enumerate(violations, 1):
            print(f"  {index}. {item}", file=sys.stderr)
        return 2
    if args.ledger_only:
        print("원문 사실대장 계약 통과.")
    else:
        print("감사 가능한 평가 브리프 계약 통과.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
