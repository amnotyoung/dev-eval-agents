#!/usr/bin/env python3
"""DevEval 기본 평가 브리프의 최소 감사추적 계약을 검사한다.

이 검사는 평가가 옳은지 대신, 근거·반대근거·상충·검증 정정이 최종 산출물에서
사라지지 않았는지 형식적으로 확인한다. 상충의 *발견*과 내용 판정은 평가관과
quality-verifier의 몫이다.

사용법: python3 scripts/auditable_output_check.py <evaluation-brief.md>
종료 코드: 0 = 계약 충족 / 2 = 필수 산출물 누락 / 1 = 파일 읽기 실패.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "평가 범위·자료·방법",
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
CORRECTION_ID = re.compile(r"\bV\d+\b", re.IGNORECASE)


def section(text: str, title: str) -> str | None:
    """Return a level-2 Markdown section whose heading contains title."""
    match = re.search(rf"(?m)^##\s+[^\n]*{re.escape(title)}[^\n]*$", text)
    if not match:
        return None
    next_heading = re.search(r"(?m)^##\s+", text[match.end():])
    end = match.end() + next_heading.start() if next_heading else len(text)
    return text[match.end():end]


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

    detail = sections.get("기준별 상세 평정", "")
    for criterion in CRITERIA:
        if not re.search(rf"(?m)^###\s+[^\n]*{criterion}", detail):
            violations.append(f"기준별 상세 평정 누락: {criterion}")
    for field in ("지지근거", "반대·제약근거", "근거 상태", "인접 점수"):
        if field not in detail:
            violations.append(f"상세 평정 필드 누락: {field}")

    overall = sections.get("종합 평정", "")
    for field in ("검증 후", "근거 상태", "검증 판정"):
        if field not in overall:
            violations.append(f"종합 평정 필드 누락: {field}")

    register = sections.get("상충·불일치 등록부", "")
    markers = {item.upper() for item in CONFLICT_MARKER.findall(text)}
    register_ids = {item.upper() for item in CONFLICT_ID.findall(register)}
    # Template instructions mention X1; only count IDs in actual table rows.
    row_ids = {
        match.group(1).upper()
        for match in re.finditer(r"(?m)^\|\s*(X\d+)\s*\|", register, re.IGNORECASE)
    }
    if row_ids:
        register_ids = row_ids
        for conflict_id in sorted(markers - register_ids):
            violations.append(f"상세 평정의 {conflict_id}가 상충 등록부에 없음")
        for conflict_id in sorted(register_ids - markers):
            violations.append(f"상충 등록부의 {conflict_id}가 상세 평정에 [상충: {conflict_id}]로 연결되지 않음")
        for field in ("해결 상태", "점수·결론 영향", "후속 확인"):
            if field not in register:
                violations.append(f"상충 등록부 필드 누락: {field}")
    elif markers:
        for conflict_id in sorted(markers):
            violations.append(f"상세 평정의 {conflict_id}가 상충 등록부에 없음")
    elif "중대 상충 없음" not in register or "점검" not in register:
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
    args = parser.parse_args()
    try:
        text = Path(args.brief).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"읽기 실패: {exc}", file=sys.stderr)
        return 1

    violations = inspect(text)
    if violations:
        print("감사 가능한 평가 브리프 계약 위반:", file=sys.stderr)
        for index, item in enumerate(violations, 1):
            print(f"  {index}. {item}", file=sys.stderr)
        return 2
    print("감사 가능한 평가 브리프 계약 통과.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
