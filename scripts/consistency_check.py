#!/usr/bin/env python3
"""consistency_check.py — 평가보고서 수치 일관성 검사 (형식 무관·독립 실행).

느슨한 형식의 종료평가 보고서에서도 사람이 국문/영문/표에 같은 숫자를 옮기다
어긋내는 사고(예: 종합점수 11.7 vs 12.7)와 등급↔점수 괴리를 잡는다. 채점 스키마·
점수 JSON·집계기에 의존하지 않으며, 자유 서술 형식을 강제하지 않는다 —
**수치·등급의 자기모순만** 본다.

지원 형식(하네스 자체 초안 + 실제 KOICA 보고서 양쪽):
  [사업평가]
   ① 종합점수 전건 일치 — `NN/16`·`/20`·`/24` 또는 표 안 맨숫자 `종합 점수 … 12.34`
   ② a+b+c+d 산술 — `평균 점수(a)~(d)`의 합이 종합점수와 같은가 (실제 보고서 최빈 사고)
   ③ 등급 전건 일치 — A~F 문자 또는 라벨(매우 성공적/성공적/부분 성공적/미흡)
   ④ 등급 ↔ 점수 정합 — /20은 A~F 등급표, 4기준(/16)은 평균(종합÷기준수) 4단계 밴드
  [품질검토]
   ⑤ 총점(`NN/100`) 전건 일치·세부항목 합산==총점·등급(A~D)↔총점↔Pass/Non-Pass

'잠정·범위·보류' 표기가 있는 줄은 정당한 복수 값이므로 일치 검사에서 제외한다.
**확인 불가와 통과를 구분**한다 — 검사할 수치를 하나도 못 찾으면 '통과'가 아니라
'확인 불가'로 알린다(거짓 초록불 방지). fail-open: 크래시 시 종료 0.

사용법:
    python3 scripts/consistency_check.py <report.md> [--mode auto|project|quality]
종료 코드: 0 = 통과/확인 불가 / 2 = 위반(한국어 번호 목록, stderr).
표준 라이브러리만 사용.
"""

import argparse
import os
import re
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

PROVISIONAL = ("잠정", "범위", "보류", "가정", "~")

# KOICA 2024 종합 등급표(/20, 5기준) — 반개구간 [하한, 상한)
GRADE_20 = [(Decimal(18), "A"), (Decimal(16), "B"), (Decimal(14), "C"),
            (Decimal(12), "D"), (Decimal(10), "E"), (None, "F")]
# 품질검토 v2(/100)
GRADE_Q = [(Decimal(90), "A"), (Decimal(80), "B"), (Decimal(60), "C"), (None, "D")]
# 4점척도 라벨 밴드 — 평균(종합÷기준수) 기준 (KOICA/국조실 4단계)
LABEL_BANDS = [(Decimal("3.5"), "매우 성공적"), (Decimal("2.5"), "성공적"),
               (Decimal("1.5"), "부분 성공적"), (None, "미흡")]
# 라벨 매칭(긴 것 먼저 — '성공적'이 '매우 성공적'·'부분 성공적'의 부분문자열)
LABEL_ALT = r"매우\s*성공적|부분\s*성공적|성공적|미흡"


def norm_label(s):
    return re.sub(r"\s+", " ", s).strip()


def band20(total):
    for lo, letter in GRADE_20:
        if lo is None or total >= lo:
            return letter
    return "F"


def bandq(total):
    for lo, letter in GRADE_Q:
        if lo is None or Decimal(total) >= lo:
            return letter
    return "D"


def band_label(mean):
    for lo, label in LABEL_BANDS:
        if lo is None or mean >= lo:
            return label
    return "미흡"


def dec2(x):
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def is_provisional(line):
    return any(k in line for k in PROVISIONAL)


def numbered(text):
    return list(enumerate(text.splitlines(), 1))


def detect_mode(text):
    q = sum(bool(re.search(p, text)) for p in (
        r"품질\s*검토|품질\s*등급", r"세부항목", r"총점\s*[::]?\s*\**\s*\d{1,3}\s*/\s*100", r"Non-?Pass"))
    if q >= 2:
        return "quality"
    if re.search(r"\d\s*/\s*(16|20|24)(?!\d)|종합\s*점수|등급|" + LABEL_ALT, text):
        return "project"
    return "none"


# ---------- 추출기 ----------

def find_totals(text, denoms):
    """분모부 표기: NN/16·20·24·100. 잠정 줄 제외. {denom: [(Decimal, lineno)]}"""
    out = {}
    pat = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d{1,2})?)\s*(?:점)?\s*/\s*(" + "|".join(denoms) + r")(?!\d)")
    for lineno, line in numbered(text):
        if is_provisional(line):
            continue
        for m in pat.finditer(line):
            try:
                out.setdefault(m.group(2), []).append((Decimal(m.group(1)), lineno))
            except InvalidOperation:
                continue
    return out


def find_composite_labeled(text):
    """분모 없는 종합점수: '종합 점수 … 12.34' (실제 보고서 표 안 맨숫자). [(Decimal, lineno)]"""
    out = []
    pat = re.compile(r"종합\s*(?:평가\s*)?점수[^\d\n]{0,40}(\d{1,3}(?:\.\d{1,2})?)")
    for lineno, line in numbered(text):
        if is_provisional(line):
            continue
        for m in pat.finditer(line):
            try:
                out.append((Decimal(m.group(1)), lineno))
            except InvalidOperation:
                continue
    return out


def find_criterion_means(text):
    """평균 점수(a)~(d)의 값. [Decimal]"""
    means = []
    pat = re.compile(r"평균\s*점수\s*\(([a-dA-D])\)[^\d\n]{0,20}(\d(?:\.\d{1,2})?)")
    for m in pat.finditer(text):
        try:
            means.append(Decimal(m.group(2)))
        except InvalidOperation:
            continue
    return means


def find_grades_af(text):
    out = []
    pat_ko = re.compile(r"등급(?:\(안\))?\s*[::]?\s*\**\s*([A-F])(?![A-Za-z+])")
    pat_en = re.compile(r"[Gg]rade\s*[::]?\s*\**\s*([A-F])(?![A-Za-z+])")
    for lineno, line in numbered(text):
        if is_provisional(line):
            continue
        for pat in (pat_ko, pat_en):
            for m in pat.finditer(line):
                out.append((m.group(1), lineno))
    return out


def find_grades_label(text):
    """등급이 언급된 줄에서만 라벨 수집(서술문의 '성공적으로' 등 오탐 방지)."""
    out = []
    pat = re.compile(r"(" + LABEL_ALT + r")")
    for lineno, line in numbered(text):
        if is_provisional(line) or "등급" not in line:
            continue
        for m in pat.finditer(line):
            out.append((norm_label(m.group(1)), lineno))
    return out


def extract_quality_items(text):
    items = []
    circled = "①②③④⑤⑥⑦⑧⑨⑩"
    pat = re.compile(r"^\|\s*([①②③④⑤⑥⑦⑧⑨⑩]|10|[1-9])\s*\|[^|\n]*\|\s*(\d{1,2})\s*\|", re.MULTILINE)
    for m in pat.finditer(text):
        rid = m.group(1)
        iid = circled.index(rid) + 1 if rid in circled else int(rid)
        items.append((iid, int(m.group(2))))
    return items


# ---------- 검사 (반환값: 실제 수행한 실질 검증 수) ----------

def check_project(text, violations):
    checks = 0
    # ① 종합점수 전건 일치 (분모부 + 라벨 맨숫자)
    comp_vals = {}  # Decimal -> [lineno]
    for _denom, entries in find_totals(text, ["16", "20", "24"]).items():
        for val, lineno in entries:
            comp_vals.setdefault(val, []).append(lineno)
    for val, lineno in find_composite_labeled(text):
        comp_vals.setdefault(val, []).append(lineno)
    if comp_vals:
        checks += 1
        if len(comp_vals) > 1:
            desc = " vs ".join(f"{v} (line {ls[0]})" for v, ls in sorted(comp_vals.items()))
            violations.append(f"종합점수 표기 불일치 — {desc}. 같은 종합점수는 문서 전체에서 일치해야 합니다")
    composite = next(iter(comp_vals)) if len(comp_vals) == 1 else None

    # ② a+b+c+d = 종합점수
    means = find_criterion_means(text)
    if len(means) >= 2 and composite is not None:
        checks += 1
        s = dec2(sum(means))
        if s != composite:
            cells = " + ".join(str(m) for m in means)
            violations.append(f"기준 평균 합 불일치 — {cells} = {s} 인데 종합점수는 {composite} (a+b+c+d 산술 오류)")

    # ③ 등급 전건 일치 (A~F 또는 라벨, 스킴 내에서)
    af_set = {g for g, _ in find_grades_af(text)}
    label_set = {g for g, _ in find_grades_label(text)}
    if af_set:
        checks += 1
        if len(af_set) > 1:
            violations.append(f"등급 표기 불일치 — {' vs '.join(sorted(af_set))} (A~F)")
    if label_set:
        checks += 1
        if len(label_set) > 1:
            violations.append(f"등급 표기 불일치 — {' vs '.join(sorted(label_set))} (라벨)")

    # ④ 등급 ↔ 점수 재계산 (확정 단일값 + 잠정 없음일 때만)
    if composite is not None and not any(k in text for k in ("잠정", "보류")):
        if find_totals(text, ["20"]).get("20") and len(af_set) == 1:
            expected, stated = band20(composite), next(iter(af_set))
            if stated != expected:
                violations.append(
                    f"등급-점수 괴리 — 종합점수 {composite}/20의 등급표 판정은 {expected}인데 본문 등급은 {stated}")
        if len(label_set) == 1 and means:
            n_crit = len(means)
            mean = dec2(composite / Decimal(n_crit))
            expected, stated = band_label(mean), next(iter(label_set))
            if norm_label(stated) != expected:
                violations.append(
                    f"등급-점수 괴리 — 종합 {composite}(평균 {mean}, {n_crit}기준)의 밴드 판정은 "
                    f"'{expected}'인데 본문 등급은 '{stated}' "
                    f"[밴드: 평균 3.5↑ 매우 성공적 / 2.5↑ 성공적 / 1.5↑ 부분 성공적 / 그 미만 미흡]")
    return checks


def check_quality(text, violations):
    checks = 0
    distinct = {}
    for val, lineno in find_totals(text, ["100"]).get("100", []):
        distinct.setdefault(val, []).append(lineno)
    if distinct:
        checks += 1
        if len(distinct) > 1:
            desc = " vs ".join(f"{v} (line {ls[0]})" for v, ls in sorted(distinct.items()))
            violations.append(f"총점(/100) 표기 불일치 — {desc}. 같은 총점은 문서 전체에서 일치해야 합니다")
    items = extract_quality_items(text)
    total_val = int(next(iter(distinct))) if len(distinct) == 1 else None
    if total_val is not None and len({i for i, _ in items}) == 10 and len(items) == 10:
        checks += 1
        s = sum(sc for _, sc in items)
        if s != total_val:
            violations.append(f"총점 {total_val} ≠ 세부항목 합산 {s}")
    gset = set(re.findall(r"품질\s*등급[^A-D\n]{0,20}([A-D])", text))
    if gset:
        checks += 1
        if len(gset) > 1:
            violations.append(f"품질등급 표기 불일치 — {' vs '.join(sorted(gset))}")
    if total_val is not None and len(gset) == 1 and "잠정" not in text:
        stated, expected = next(iter(gset)), bandq(total_val)
        if stated != expected:
            violations.append(f"품질등급 {stated} ≠ 총점 {total_val}/100의 등급표 판정 {expected}")
    has_np = re.search(r"Non-?Pass", text)
    has_pass = re.search(r"(?<![Nn]on-)\bPass\b", text)
    if gset == {"D"} and has_pass and not has_np:
        violations.append("품질등급 D인데 Non-Pass 표기가 없습니다 (D = Non-Pass)")
    if gset and gset <= {"A", "B", "C"} and has_np:
        violations.append(f"품질등급 {'/'.join(sorted(gset))}인데 Non-Pass 표기가 있습니다 (A·B·C = Pass)")
    return checks


SUPPORTED = ("지원 형식: 종합점수 NN/16·20·24 또는 '종합 점수 … 12.34', "
             "평균 점수(a~d), 등급 A~F 또는 매우 성공적/성공적/부분 성공적/미흡, 품질 총점 NN/100")


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
        print("[consistency_check] 수치·등급 패턴 없음 — 확인 불가(통과 아님). " + SUPPORTED, file=sys.stderr)
        return 0
    violations = []
    checks = check_project(text, violations) if mode == "project" else check_quality(text, violations)
    name = os.path.basename(path)
    if violations:
        print(f"[consistency_check] {name} — 수치 불일치 {len(violations)}건 ({mode} 모드):", file=sys.stderr)
        for i, v in enumerate(violations, 1):
            print(f"  {i}) {v}", file=sys.stderr)
        return 2
    if checks == 0:
        print(f"[consistency_check] {name} — 확인할 수치를 못 찾음: '통과' 아님(확인 불가). " + SUPPORTED,
              file=sys.stderr)
        return 0
    print(f"[consistency_check] {name} — 수치 일관성 통과 ({mode} 모드, {checks}개 항목 확인)")
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
