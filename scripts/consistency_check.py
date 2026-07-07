#!/usr/bin/env python3
"""consistency_check.py — 평가보고서 수치 일관성 검사 (형식 무관·독립 실행).

느슨한 형식의 종료평가 보고서에서도 사람이 국문/영문/표에 같은 숫자를 옮기다
어긋내는 사고(예: 종합점수 11.7 vs 12.7)를 잡는다. 채점 스키마·점수 JSON·집계기에
의존하지 않으며, 자유 서술 형식을 강제하지 않는다 — **수치·등급의 자기모순만** 본다.

검사 항목(모두 형식 무관, 보수적 추출: 확실히 파싱된 값만 위반 처리):
  [사업평가]
   ① 종합점수 표기 전건 일치 — 문서 전체의 `NN/20`(·/16·/24)가 같은가 (11.7 vs 12.7 포착)
   ② 등급 문자(A~F) 전건 일치 — 국문·영문·표의 등급이 같은가
   ③ 등급 ↔ 점수 정합 — 단일 종합점수·단일 등급일 때, 점수의 KOICA 등급표 판정과 본문 등급이 같은가
  [품질검토]
   ④ 총점 표기(`NN/100`) 전건 일치, 세부항목 합산 == 총점(추출 가능 시)
   ⑤ 품질등급(A~D) ↔ 총점 ↔ Pass/Non-Pass 정합

'잠정·범위·보류' 표기가 있는 줄은 정당한 복수 값이므로 일치 검사에서 제외한다.
fail-open: 크래시·읽기 실패 시 종료 0(도구 오류로 워크플로를 막지 않음).

사용법:
    python3 scripts/consistency_check.py <report.md> [--mode auto|project|quality]
종료 코드: 0 = 통과 / 2 = 위반(한국어 번호 목록, stderr).
표준 라이브러리만 사용. (arch-hardening 브랜치 report_lint.py의 수치 대조 부분만 추출·독립화.)
"""

import argparse
import os
import re
import sys
from decimal import Decimal, InvalidOperation

PROVISIONAL = ("잠정", "범위", "보류", "가정", "~")

# KOICA 2024 종합 등급표(/20) — 반개구간 [하한, 상한). 등급↔점수 재계산용.
GRADE_20 = [(Decimal(18), "A"), (Decimal(16), "B"), (Decimal(14), "C"),
            (Decimal(12), "D"), (Decimal(10), "E"), (None, "F")]
# 품질검토 v2(/100)
GRADE_Q = [(Decimal(90), "A"), (Decimal(80), "B"), (Decimal(60), "C"), (None, "D")]


def grade20(total):
    for lo, letter in GRADE_20:
        if lo is None or total >= lo:
            return letter
    return "F"


def gradeq(total):
    for lo, letter in GRADE_Q:
        if lo is None or Decimal(total) >= lo:
            return letter
    return "D"


def is_provisional(line):
    return any(k in line for k in PROVISIONAL)


def numbered(text):
    return list(enumerate(text.splitlines(), 1))


def detect_mode(text):
    q = sum(bool(re.search(p, text)) for p in (
        r"품질\s*검토|품질\s*등급", r"세부항목", r"총점\s*[::]?\s*\**\s*\d{1,3}\s*/\s*100", r"Non-?Pass"))
    if q >= 2:
        return "quality"
    if re.search(r"\d\s*/\s*(16|20|24)(?!\d)|종합\s*점수|등급(\(안\))?\s*[::]?\s*\**\s*[A-F](?![A-Za-z])", text):
        return "project"
    return "none"


def find_totals(text, denoms):
    """분모별로 (Decimal, lineno, raw) 수집. 잠정 줄 제외."""
    out = {}
    pat = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d{1,2})?)\s*(?:점)?\s*/\s*(" + "|".join(denoms) + r")(?!\d)")
    for lineno, line in numbered(text):
        if is_provisional(line):
            continue
        for m in pat.finditer(line):
            try:
                out.setdefault(m.group(2), []).append((Decimal(m.group(1)), lineno, m.group(0).strip()))
            except InvalidOperation:
                continue
    return out


def find_grades(text, letters_class):
    """등급 문자 수집. 잠정 줄 제외. letters_class 예: 'A-F' / 'A-D'."""
    out = []
    pat_ko = re.compile(r"등급(?:\(안\))?\s*[::]?\s*\**\s*([" + letters_class + r"])(?![A-Za-z+])")
    pat_en = re.compile(r"[Gg]rade\s*[::]?\s*\**\s*([" + letters_class + r"])(?![A-Za-z+])")
    for lineno, line in numbered(text):
        if is_provisional(line):
            continue
        for pat in (pat_ko, pat_en):
            for m in pat.finditer(line):
                out.append((m.group(1), lineno))
    return out


def check_project(text, violations):
    # ① 종합점수 표기 전건 일치
    totals = find_totals(text, ["16", "20", "24"])
    for denom, entries in totals.items():
        distinct = {}
        for val, lineno, raw in entries:
            distinct.setdefault(val, []).append((lineno, raw))
        if len(distinct) > 1:
            desc = " vs ".join(f"{v} (line {locs[0][0]})" for v, locs in sorted(distinct.items()))
            violations.append(f"종합점수(/{denom}) 표기 불일치 — {desc}. 같은 수치는 문서 전체에서 일치해야 합니다")
    # ② 등급 문자 전건 일치
    grades = find_grades(text, "A-F")
    letters = {}
    for letter, lineno in grades:
        letters.setdefault(letter, []).append(lineno)
    if len(letters) > 1:
        desc = " vs ".join(f"{ltr} (line {ls[0]})" for ltr, ls in sorted(letters.items()))
        violations.append(f"등급 표기 불일치 — {desc}. 국문·영문·표의 등급은 일치해야 합니다")
    # ③ 등급 ↔ 점수 재계산 (단일 /20 총점 + 단일 등급 + 잠정 없음일 때만)
    t20 = {v for v, _, _ in totals.get("20", [])}
    if len(t20) == 1 and len(letters) == 1 and not any(k in text for k in ("잠정", "보류")):
        total = next(iter(t20))
        stated = next(iter(letters))
        expected = grade20(total)
        if stated != expected:
            violations.append(
                f"등급-점수 괴리 — 종합점수 {total}/20의 등급표 판정은 {expected}인데 본문 등급은 {stated}"
                " (2024 지침 p.7 서술-등급 괴리 점검)")


def extract_quality_items(text):
    items = []
    circled = "①②③④⑤⑥⑦⑧⑨⑩"
    pat = re.compile(r"^\|\s*([①②③④⑤⑥⑦⑧⑨⑩]|10|[1-9])\s*\|[^|\n]*\|\s*(\d{1,2})\s*\|", re.MULTILINE)
    for m in pat.finditer(text):
        rid = m.group(1)
        iid = circled.index(rid) + 1 if rid in circled else int(rid)
        items.append((iid, int(m.group(2))))
    return items


def check_quality(text, violations):
    # ④ 총점 표기 전건 일치
    totals = find_totals(text, ["100"])
    t100 = totals.get("100", [])
    distinct = {}
    for val, lineno, raw in t100:
        distinct.setdefault(val, []).append(lineno)
    if len(distinct) > 1:
        desc = " vs ".join(f"{v} (line {ls[0]})" for v, ls in sorted(distinct.items()))
        violations.append(f"총점(/100) 표기 불일치 — {desc}. 같은 총점은 문서 전체에서 일치해야 합니다")
    # 세부항목 합산 == 총점 (10개 정확 추출 시)
    items = extract_quality_items(text)
    total_val = int(distinct and next(iter(sorted(distinct)))) if len(distinct) == 1 else None
    if total_val is not None and len({i for i, _ in items}) == 10 and len(items) == 10:
        s = sum(sc for _, sc in items)
        if s != total_val:
            violations.append(f"총점 {total_val} ≠ 세부항목 합산 {s}")
    # ⑤ 품질등급 ↔ 총점 ↔ Pass/Non-Pass
    grades = find_grades(text, "A-D")
    gletters = {g for g, _ in grades}
    if len(gletters) > 1:
        violations.append(f"품질등급 표기 불일치 — {' vs '.join(sorted(gletters))}")
    if total_val is not None and len(gletters) == 1 and "잠정" not in text:
        stated = next(iter(gletters))
        expected = gradeq(total_val)
        if stated != expected:
            violations.append(f"품질등급 {stated} ≠ 총점 {total_val}/100의 등급표 판정 {expected}")
    has_np = re.search(r"Non-?Pass", text)
    has_pass = re.search(r"(?<![Nn]on-)\bPass\b", text)
    if gletters == {"D"} and has_pass and not has_np:
        violations.append("품질등급 D인데 Non-Pass 표기가 없습니다 (D = Non-Pass)")
    if gletters and gletters <= {"A", "B", "C"} and has_np:
        violations.append(f"품질등급 {'/'.join(sorted(gletters))}인데 Non-Pass 표기가 있습니다 (A·B·C = Pass)")


def run(path, mode):
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        print(f"[consistency_check] 읽기 실패 — 검사 생략(fail-open): {exc}", file=sys.stderr)
        return 0
    if mode == "auto":
        mode = detect_mode(text)
    if mode == "none":
        print("[consistency_check] 수치·등급 패턴 없음 — 스킵", file=sys.stderr)
        return 0
    violations = []
    if mode == "project":
        check_project(text, violations)
    else:
        check_quality(text, violations)
    if violations:
        print(f"[consistency_check] {os.path.basename(path)} — 수치 불일치 {len(violations)}건 ({mode} 모드):",
              file=sys.stderr)
        for i, v in enumerate(violations, 1):
            print(f"  {i}) {v}", file=sys.stderr)
        return 2
    print(f"[consistency_check] {os.path.basename(path)} — 수치 일관성 통과 ({mode} 모드)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="평가보고서 수치 일관성 검사 (형식 무관·독립)")
    ap.add_argument("report", help="검사할 보고서 마크다운 경로")
    ap.add_argument("--mode", choices=("auto", "project", "quality"), default="auto")
    args = ap.parse_args(argv)
    try:
        return run(args.report, args.mode)
    except Exception as exc:  # noqa: BLE001 — fail-open
        print(f"[consistency_check] 내부 오류 — 검사 생략(fail-open): {exc}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
