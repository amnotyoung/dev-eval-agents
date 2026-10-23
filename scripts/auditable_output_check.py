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
from pathlib import Path


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


def inspect(text: str) -> list[str]:
    violations: list[str] = []
    if re.search(r"\[\s*\]", text) or "[사업명]" in text:
        violations.append("템플릿 미작성 자리표시자([ ] 또는 [사업명])가 남아 있음")
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
    args = parser.parse_args()
    try:
        text = Path(args.brief).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"읽기 실패: {exc}", file=sys.stderr)
        return 1

    if args.ledger_only:
        violations, _fact_ids, _conflicts = inspect_ledger(text)
    else:
        violations = inspect(text)
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
