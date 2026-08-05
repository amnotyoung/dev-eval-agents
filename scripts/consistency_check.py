#!/usr/bin/env python3
"""consistency_check.py — 평가보고서 수치 일관성 검사 (형식 무관·독립 실행).

느슨한 형식의 종료평가 보고서에서도 사람이 국문/영문/표에 같은 숫자를 옮기다
어긋내는 사고(예: 종합점수 11.7 vs 12.7)와 등급↔점수 괴리를 잡는다. 채점 스키마·
점수 JSON·집계기에 의존하지 않으며, 자유 서술 형식을 강제하지 않는다 —
**수치·등급의 자기모순만** 본다.

지원 형식(하네스 자체 초안 + 실제 KOICA 보고서 양쪽):
  [사업평가]
   ① 종합점수 전건 일치 — `NN/16`·`/20`·`/24`, 표 안 맨숫자 `종합 점수 … 12.34`,
      국문 역순 `24점 만점 중 11.7`, 영문 `12.7 (points) out of 24`
      (국문↔영문 요약 불일치 — 캄보디아 종료평가의 11.7 vs 12.7 — 를 잡는 핵심 형식)
   ② a+b+c+d 산술 — `평균 점수(a)~(d)`의 합이 종합점수와 같은가 (실제 보고서 최빈 사고)
   ③ 등급 전건 일치 — A~F 문자 또는 라벨(매우 성공적/성공적/부분 성공적/미흡)
   ④ 등급 ↔ 점수 정합 — /20은 A~F 등급표, 4기준(/16)은 평균(종합÷기준수) 4단계 밴드
  [품질검토]
   ⑤ 총점(`NN/100`) 전건 일치·세부항목 합산==총점·등급(A~D)↔총점↔Pass/Non-Pass

실제 KOICA 종료평가 PDF 334건 전수 스윕(2026-08)으로 보정한 오탐 억제:
  - 범례·임계값 문장("…이상이면 매우 성공적, …" / 라벨 3종 이상 열거)은 평정이 아니라
    척도 정의이므로 제외한다.
  - 품질검토 도장("평가품질 등급: B")은 A~D 품질 체계라 사업 A~F 등급과 다른 체계다 —
    사업평가 모드의 등급 수집에서 '품질' 줄을 제외한다.
  - 만족도·설문 종합점수(5점 척도 등)는 DAC 종합점수가 아니다 — 해당 줄을 제외하고,
    사업 종합점수는 24 이하만 인정한다(체계 최대 = 24점).
  - `8/20개소`(개수)·`7/20(월)`(일정) 같은 N/M 표기는 점수가 아니다 — 단위·요일이
    붙으면 제외한다.
'잠정·범위·보류' 표기가 있는 줄은 정당한 복수 값이므로 일치 검사에서 제외한다.
다건 묶음(평가용역) 보고서는 사업별로 다른 종합점수·등급이 정상이다 — 이 검사는
단일 사업 문서 기준이므로, 묶음이면 사업 단위로 잘라서 검사하라.
**확인 불가와 통과를 구분**한다 — 검사할 수치를 하나도 못 찾으면 '통과'가 아니라
'확인 불가'로 알린다(거짓 초록불 방지). fail-open: 크래시 시 종료 0.

사용법:
    python3 scripts/consistency_check.py <report.md> [--mode auto|project|quality]
종료 코드: 0 = 통과 / 2 = 위반(한국어 번호 목록, stderr) / 3 = 확인 불가(검사할 수치
없음 — 통과 아님). 읽기 실패·내부 오류는 fail-open으로 0.
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
# 사업 종합점수 검사 상한 — /24로 작성된 기존·외부 보고서도 불일치 검사용으로 읽는다
COMPOSITE_MAX = Decimal(24)
# 만족도·설문 종합점수(5점 척도 등)는 DAC 종합점수가 아니다
SURVEY_WORDS = ("만족도", "설문", "응답률", "응답자", "리커트")


def norm_label(s):
    return re.sub(r"\s+", " ", s).strip()


def distinct_labels(line):
    """줄 안의 서로 다른 등급 라벨 수. 3종 이상 열거는 평정이 아니라 척도 범례다."""
    return len({norm_label(m.group(0)) for m in re.finditer(LABEL_ALT, line)})


def is_threshold_def(line):
    """'…점 이상이면 매우 성공적, … 미만이면 …' 같은 등급 산정 기준 서술."""
    return ("이상이면" in line or "미만이면" in line
            or ("이상" in line and "미만" in line))


def is_mismatch_quote(line):
    """불일치를 '보고하는' 메타 서술 줄 — 값 주장이 아니라 인용이다.

    검증 초안이 원보고서의 총점 불일치를 "국문 11.7/24 vs 영문 12.7/24 — 상호
    불일치"처럼 한 줄로 인용하면, 그 줄의 두 값은 초안 자신의 자기모순이 아니다.
    정상적인 값 주장 줄은 '불일치'라는 단어를 쓰지 않는다.
    """
    return "불일치" in line


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

def find_totals(text, denoms, require_words=None):
    """분모부 표기: NN/16·20·24·100. 잠정 줄 제외. {denom: [(Decimal, lineno)]}

    점수가 아닌 N/M 표기를 배제한다 — 개수(`8/20개소`), 일정·날짜(`7/20(월)`,
    `3/20-24`, `2020/7/20`), 비율 분모 연속(`20/100,000명`), 남/여 인원(`(35/24)`,
    분자>분모라 점수일 수 없음). require_words를 주면 그 단어가 있는 줄만 본다
    (품질검토 총점 줄을 PDM 달성률 `NN/100점`과 구분할 때).
    """
    out = {}
    pat = re.compile(
        r"(?<![\d./])(\d{1,3}(?:\.\d{1,2})?)\s*(?:점)?\s*/\s*(" + "|".join(denoms) + r")"
        r"(?!\d)(?![,.]\d)(?!\s*[-–~])"
        r"(?!\s*(?:[개명건회차호인주]|문항|개소|가구|과목|\(?[월화수목금토일]\)))")
    for lineno, line in numbered(text):
        if is_provisional(line) or is_mismatch_quote(line):
            continue
        if require_words and not any(w in line for w in require_words):
            continue
        for m in pat.finditer(line):
            try:
                val = Decimal(m.group(1))
            except InvalidOperation:
                continue
            if val > Decimal(m.group(2)):
                continue
            out.setdefault(m.group(2), []).append((val, lineno))
    return out


def find_totals_alt(text, denoms):
    """분모가 뒤에 오는 표기. {denom: [(Decimal, lineno)]}

    국문 역순 `총 24점 만점 중 11.7(점)` + 영문 `12.7 (points) out of 24`.
    국문↔영문 요약이 다른 값을 적는 사고(캄보디아 11.7 vs 12.7)는 이 형식에서만 잡힌다.
    """
    out = {}
    pat_ko = re.compile(r"(?<![\d.])(\d{1,3})\s*점\s*만점\s*중\s*(\d{1,3}(?:\.\d{1,2})?)")
    pat_en = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d{1,2})?)\s*(?:점|points?)?\s*out\s+of\s+(\d{1,3})(?!\d)",
                        re.IGNORECASE)
    for lineno, line in numbered(text):
        if is_provisional(line) or is_mismatch_quote(line):
            continue
        for m in pat_ko.finditer(line):
            if m.group(1) in denoms:
                try:
                    out.setdefault(m.group(1), []).append((Decimal(m.group(2)), lineno))
                except InvalidOperation:
                    continue
        for m in pat_en.finditer(line):
            if m.group(2) in denoms:
                try:
                    out.setdefault(m.group(2), []).append((Decimal(m.group(1)), lineno))
                except InvalidOperation:
                    continue
    return out


def find_composite_labeled(text):
    """분모 없는 종합점수: '종합 점수 … 12.34' (실제 보고서 표 안 맨숫자). [(Decimal, lineno)]

    제외: 만족도·설문 줄(다른 척도), 등급 산정 기준 서술(범례)·불일치 인용 줄,
    값 뒤에 이상/미만(임계값)·만점(분모)이 붙는 경우, 체계 상한(24) 초과 값,
    그리고 '종합점수'와 숫자 사이에 산정·확정·기준·등급·보류가 끼는 경우 —
    "종합점수·등급(D 또는 E)의 확정 및 외부 6기준"의 6, 출처 표기 "[05, 06]"의
    05처럼 점수가 아닌 숫자를 넘겨 잡는 것을 막는다(값 서술은 그 사이에 그런
    절차어가 없다).
    """
    out = []
    pat = re.compile(r"종합\s*(?:평가\s*)?점수([^\d\n]{0,40})(\d{1,3}(?:\.\d{1,2})?)"
                     r"(?!\s*점?\s*(?:이상|미만|만점))")
    gap_stopwords = ("산정", "확정", "기준", "등급", "보류", "제외", "미포함")
    for lineno, line in numbered(text):
        if is_provisional(line) or is_threshold_def(line) or is_mismatch_quote(line):
            continue
        if any(w in line for w in SURVEY_WORDS):
            continue
        for m in pat.finditer(line):
            if any(w in m.group(1) for w in gap_stopwords):
                continue
            try:
                val = Decimal(m.group(2))
            except InvalidOperation:
                continue
            if val <= COMPOSITE_MAX:
                out.append((val, lineno))
    return out


def find_criterion_means(text):
    """평균 점수(a)~(f)의 값. [Decimal] — 문서에 표기된 4~6개 기준 점수 셀."""
    means = []
    pat = re.compile(r"평균\s*점수\s*\(([a-fA-F])\)[^\d\n]{0,20}(\d(?:\.\d{1,2})?)")
    for m in pat.finditer(text):
        try:
            means.append(Decimal(m.group(2)))
        except InvalidOperation:
            continue
    return means


def find_grades_af(text):
    """사업평가 A~F 등급.

    다른 체계의 등급 줄은 제외한다 — '평가품질 등급: B'(A~D 품질검토 체계),
    '용역종합 등급: B'(평가용역 묶음 단위 등급). 개별 사업 등급과 섞으면
    체계가 다른 값끼리 거짓 불일치가 난다.
    """
    out = []
    pat_ko = re.compile(r"등급(?:\(안\))?\s*[::]?\s*\**\s*([A-F])(?![A-Za-z+인~∼])")
    pat_en = re.compile(r"[Gg]rade\s*[::]?\s*\**\s*([A-F])(?![A-Za-z+인~∼])")
    for lineno, line in numbered(text):
        if is_provisional(line) or is_mismatch_quote(line) or "품질" in line or "용역" in line:
            continue
        for pat in (pat_ko, pat_en):
            for m in pat.finditer(line):
                out.append((m.group(1), lineno))
    return out


def find_grades_label(text):
    """등급이 언급된 줄에서만 라벨 수집(서술문의 '성공적으로' 등 오탐 방지).

    라벨 3종 이상 열거('매우 성공적, 성공적, 부분 성공적, 미흡')와 임계값 서술은
    척도 범례이지 평정이 아니므로 줄째로 제외한다.
    """
    out = []
    pat = re.compile(r"(" + LABEL_ALT + r")")
    for lineno, line in numbered(text):
        if is_provisional(line) or is_mismatch_quote(line) or "등급" not in line:
            continue
        if distinct_labels(line) >= 3 or is_threshold_def(line):
            continue
        for m in pat.finditer(line):
            # PDF 줄바꿈으로 '부분 성공적'이 '부/분 성공적'으로 쪼개지면 '성공적'만
            # 잡혀 거짓 불일치가 된다 — 직전 텍스트가 '분'으로 끝나면 건너뛴다.
            if norm_label(m.group(1)) == "성공적" and re.search(r"분\s*$", line[:m.start()]):
                continue
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
    # ① 종합점수 전건 일치 (분모부 + 역순·영문 + 라벨 맨숫자)
    comp_vals = {}  # Decimal -> [lineno]
    for finder in (find_totals, find_totals_alt):
        for _denom, entries in finder(text, ["16", "20", "24"]).items():
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

    # ② a+b+c+d = 종합점수 — 기준 수는 4~6개(구형·현행 또는 외부 보고서 자체 체계).
    # 그 밖의 개수는 표 추출이 불완전하거나 다른 표를 잡은 것이므로 합산하지 않는다.
    means = find_criterion_means(text)
    if 4 <= len(means) <= 6 and composite is not None:
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
        if len(label_set) == 1 and 4 <= len(means) <= 6:
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
    # PDM 달성률·만족도도 `NN/100점`으로 적힌다 — 품질검토 총점 줄만 본다.
    for val, lineno in find_totals(text, ["100"], require_words=("총점", "품질", "합계")).get("100", []):
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
    # 'A~C'(범위)·'D인 경우'(범례 서술)는 판정이 아니다 — 뒤에 ~·인이 붙으면 제외.
    gset = set(re.findall(r"품질\s*등급[^A-D\n]{0,20}([A-D])(?![A-Za-z+~∼인])", text))
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


SUPPORTED = ("지원 형식: 종합점수 NN/16·20·24, 'NN점 만점 중 X', 'X (points) out of NN', "
             "'종합 점수 … 12.34', 평균 점수(a~d), 등급 A~F 또는 "
             "매우 성공적/성공적/부분 성공적/미흡, 품질 총점 NN/100")


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
        print("[consistency_check] 수치·등급 패턴 없음 — 확인 불가(통과 아님, exit 3). " + SUPPORTED,
              file=sys.stderr)
        return 3
    violations = []
    checks = check_project(text, violations) if mode == "project" else check_quality(text, violations)
    name = os.path.basename(path)
    if violations:
        print(f"[consistency_check] {name} — 수치 불일치 {len(violations)}건 ({mode} 모드):", file=sys.stderr)
        for i, v in enumerate(violations, 1):
            print(f"  {i}) {v}", file=sys.stderr)
        return 2
    if checks == 0:
        print(f"[consistency_check] {name} — 확인할 수치를 못 찾음: '통과' 아님(확인 불가, exit 3). "
              + SUPPORTED, file=sys.stderr)
        return 3
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
