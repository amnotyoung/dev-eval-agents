#!/usr/bin/env python3
"""Authoritative question scores -> deterministic KOICA scores and Markdown.

Only judgments/evidence enter the JSON. Means, totals, grades and projections
are generated here, never accepted as model-supplied aggregates. Stdlib only.
Exit 0: success; 2: invalid data/projection; 3: unreadable input/output.
"""
from __future__ import annotations

import argparse
import copy
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import html
import json
from pathlib import Path
import re
import sys

from consistency_check import band20

CRITERIA = {
    "relevance": ("적절성", 2), "coherence": ("일관성", 2),
    "effectiveness": ("효과성", 3), "efficiency": ("효율성", 2),
    "sustainability": ("지속가능성", 2),
}
STATUS = {"scored": "평가", "unavailable": "평가 불가", "not_applicable": "해당 없음"}
VERIFICATION = {"not_reviewed": "미검증", "passed": "통과", "conditional": "조건부 통과", "rejected": "반려"}
BINDING = re.compile(r"(?m)^<!-- deveval:score-input (\{.*\}) -->$")
SUMMARY_START = "<!-- deveval:computed-scores:start -->"
SUMMARY_END = "<!-- deveval:computed-scores:end -->"


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def keys(value, allowed, required, where):
    require(isinstance(value, dict), f"{where}: JSON 객체 필요")
    require(not set(value) - set(allowed), f"{where}: 알 수 없는 필드 {sorted(set(value) - set(allowed))}")
    require(not set(required) - set(value), f"{where}: 필수 필드 누락 {sorted(set(required) - set(value))}")


def number(value, where):
    require(isinstance(value, (int, float, Decimal)) and not isinstance(value, bool), f"{where}: 유한한 숫자 필요")
    result = Decimal(str(value))
    require(result.is_finite(), f"{where}: 유한한 숫자 필요")
    return result


def nonempty(value, where):
    require(isinstance(value, str) and bool(value.strip()), f"{where}: 빈 문자열 불가")
    return value.strip()


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"JSON 키 중복: {key}")
        result[key] = value
    return result


def loads(text):
    return json.loads(text, parse_float=Decimal, object_pairs_hook=no_duplicate_keys,
                      parse_constant=lambda value: (_ for _ in ()).throw(Invalid(f"비유한 JSON 숫자: {value}")))


def load(path):
    return loads(Path(path).read_text(encoding="utf-8-sig"))


def dumps(value):
    # Input Decimals are JSON numbers; stdlib's encoder has no Decimal support.
    def plain(v):
        if isinstance(v, Decimal):
            return int(v) if v == v.to_integral_value() else float(v)
        if isinstance(v, list):
            return [plain(x) for x in v]
        if isinstance(v, dict):
            return {k: plain(x) for k, x in v.items()}
        return v
    return json.dumps(plain(value), ensure_ascii=False, indent=2) + "\n"


def input_hash(data):
    return hashlib.sha256(dumps(data).encode()).hexdigest()


def display(value):
    if value is None:
        return "평가 불가"
    return format(Decimal(value).normalize(), "f")


def validate_criterion(c, profile, verification="conditional"):
    keys(c, {"criterion", "questions", "aggregation", "weight_basis", "summary", "conflict_ids"}, {"criterion", "questions"}, "기준")
    name = c["criterion"]
    require(name in CRITERIA, f"알 수 없는 기준: {name}")
    count = 3 if profile == "koica-legacy-weighted" and name == "relevance" else CRITERIA[name][1]
    questions = c["questions"]
    require(isinstance(questions, list) and len(questions) == count, f"{name}: 채점 질문 {count}개 모두 필요")
    require({q.get('id') for q in questions if isinstance(q, dict)} == {f"q{i}" for i in range(1, count+1)}, f"{name}: 질문 ID 누락·중복")
    mode = c.get("aggregation", "mean")
    require(mode in ("mean", "weighted_mean"), f"{name}: 지원하지 않는 산식")
    if profile == "koica-legacy-weighted":
        require(mode == "weighted_mean", f"{name}: 가중치 양식은 weighted_mean 필요")
    if mode == "weighted_mean":
        nonempty(c.get("weight_basis"), f"{name}.weight_basis(양식·쪽 근거)")
    weights = []
    for q in questions:
        keys(q, {"id", "status", "score", "weight", "fact_ids", "reason"}, {"id", "status", "score", "fact_ids", "reason"}, name)
        nonempty(q["reason"], f"{name}.{q['id']}.reason")
        require(q["status"] in STATUS, f"{name}.{q['id']}: 상태는 scored/unavailable/not_applicable")
        facts = q["fact_ids"]
        require(isinstance(facts, list) and all(isinstance(f, str) and re.fullmatch(r"F[1-9]\d*", f) for f in facts), f"{name}.{q['id']}: 사실 ID 목록 오류")
        require(len(facts) == len(set(facts)), f"{name}.{q['id']}: 사실 ID 중복")
        if q["status"] == "scored":
            score = number(q["score"], f"{name}.{q['id']}.score")
            require(1 <= score <= 4 and score % Decimal("0.5") == 0, f"{name}.{q['id']}: 질문 점수는 1~4, 0.5점 단위")
            require(bool(facts), f"{name}.{q['id']}: 점수를 뒷받침하는 F-ID 필요")
        else:
            require(q["score"] is None, f"{name}.{q['id']}: 평가 불가·해당 없음은 score=null")
        if mode == "weighted_mean":
            weight = number(q.get("weight"), f"{name}.{q['id']}.weight")
            require(0 < weight <= 1, f"{name}.{q['id']}: 가중치는 0 초과 1 이하")
            require(weight.as_tuple().exponent >= -6, f"{name}.{q['id']}: 가중치는 소수 6자리 이내")
            weights.append(weight)
        else:
            require("weight" not in q, f"{name}: mean 방식에는 별도 가중치를 넣지 않음")
    if weights:
        require(sum(weights) == 1, f"{name}: 가중치 합은 정확히 1이어야 함")
    if "summary" in c:
        nonempty(c["summary"], f"{name}.summary")
    conflicts = c.get("conflict_ids", [])
    local_prefix = {"relevance":"REL", "coherence":"COH", "effectiveness":"EFF", "efficiency":"EFI", "sustainability":"SUS"}[name]
    pattern = rf"(?:X[1-9]\d*|{local_prefix}-X[1-9]\d*)" if verification == "not_reviewed" else r"X[1-9]\d*"
    require(isinstance(conflicts, list) and all(isinstance(x, str) and re.fullmatch(pattern, x) for x in conflicts),
            f"{name}: 상충 ID 오류 — 검증 전에는 담당 기준 임시 ID, 검증 후에는 전역 X-ID만 허용")


def calculate(data):
    keys(data, {"schema_version", "project", "source_sha256", "profile", "verification", "criteria", "scenarios"},
         {"schema_version", "project", "source_sha256", "verification", "criteria"}, "점수 정본")
    require(type(data["schema_version"]) is int and data["schema_version"] == 1, "지원하는 schema_version은 1")
    nonempty(data["project"], "project")
    require(isinstance(data["source_sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", data["source_sha256"]), "source_sha256 오류")
    profile = data.get("profile", "koica-2024")
    require(profile in ("koica-2024", "koica-legacy-weighted"), "지원하는 질문 양식이 아님")
    require(data["verification"] in VERIFICATION, "verification 상태 오류")
    criteria = data["criteria"]
    require(isinstance(criteria, list) and len(criteria) == 5, "5개 기준이 모두 필요")
    require({c.get('criterion') for c in criteria if isinstance(c, dict)} == set(CRITERIA), "기준 ID 누락·중복")
    by_name = {}
    for c in criteria:
        validate_criterion(c, profile, data["verification"])
        by_name[c["criterion"]] = c
    results = []
    for name, (label, _) in CRITERIA.items():
        c = by_name[name]
        numerator, denominator = Decimal(0), Decimal(0)
        questions = sorted(c["questions"], key=lambda q:q["id"])
        scored = []
        for q in questions:
            if q["status"] == "scored":
                weight = number(q["weight"], "weight") if c.get("aggregation", "mean") == "weighted_mean" else Decimal(1)
                score = number(q["score"], "score")
                numerator += score * weight
                denominator += weight
                scored.append(q["id"])
        mean = (numerator / denominator).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if denominator else None
        results.append({"criterion": name, "label": label, "score": str(mean) if mean is not None else None,
                        "scored_questions": scored, "excluded_questions": [q['id'] for q in questions if q['status'] != 'scored'],
                        "numerator": str(numerator), "denominator": str(denominator), "questions": questions,
                        "summary": c.get("summary", ""), "conflict_ids": c.get("conflict_ids")})
    total = sum(Decimal(c["score"]) for c in results) if all(c["score"] is not None for c in results) else None
    incomplete = any(c["excluded_questions"] or c["conflict_ids"] is None for c in results)
    verification = "conditional" if data["verification"] == "passed" and incomplete else data["verification"]
    result = {"schema_version": 1, "project": data["project"], "profile": profile, "source_sha256": data["source_sha256"],
            "input_sha256": input_hash(data), "verification": verification, "criteria": results,
            "total": str(total) if total is not None else None, "grade": band20(total) if total is not None else None,
            "conditional": data["verification"] != "passed" or incomplete}
    scenarios = data.get("scenarios", [])
    require(isinstance(scenarios, list) and len(scenarios) <= 20, "민감도 시나리오는 최대 20개 목록")
    seen = set(); result["scenarios"] = []
    for scenario in scenarios:
        keys(scenario, {"id", "reason", "changes"}, {"id", "reason", "changes"}, "민감도 시나리오")
        sid = scenario["id"]
        require(isinstance(sid,str) and re.fullmatch(r"S[1-9]\d*",sid) and sid not in seen, "시나리오 ID 오류·중복")
        seen.add(sid); nonempty(scenario["reason"], sid)
        require(isinstance(scenario["changes"],list) and bool(scenario["changes"]), f"{sid}: 질문 변경 목록 필요")
        variant = copy.deepcopy({k:v for k,v in data.items() if k != "scenarios"})
        changed = set()
        for change in scenario["changes"]:
            keys(change, {"criterion", "question", "score", "fact_ids", "reason"}, {"criterion", "question", "score", "fact_ids", "reason"}, sid)
            key = (change["criterion"],change["question"])
            require(key not in changed, f"{sid}: 같은 질문 중복 변경")
            changed.add(key)
            target = next((q for c in variant['criteria'] if c['criterion']==key[0] for q in c['questions'] if q['id']==key[1]), None)
            require(target is not None, f"{sid}: 존재하지 않는 질문")
            target.update(status="scored",score=change['score'],fact_ids=change['fact_ids'],reason=change['reason'])
        computed = calculate(variant)
        result["scenarios"].append({"id":sid,"reason":scenario['reason'],"changes":scenario['changes'],"total":computed['total'],"grade":computed['grade']})
    if scenarios:
        result["conditional"] = True
        if result["verification"] == "passed": result["verification"] = "conditional"
    return result


def cell(value):
    return html.escape(str(value), quote=False).replace("|", r"\|").replace("\n", "<br>")


def summary_block(after, before=None):
    rows = [SUMMARY_START,
            "| 기준 | 검증 전 점수 | 검증 후 잠정 점수 | 근거 상태 | 중대 상충 ID | 핵심 판단 |",
            "|---|---:|---:|---|---|---|"]
    pre = {c['criterion']:c['score'] for c in before['criteria']} if before else {}
    for c in after["criteria"]:
        state = "근거 없음" if c["score"] is None else ("단서 필요" if after["conditional"] else "확인됨")
        coverage = f"{len(c['scored_questions'])}/{len(c['questions'])}개 질문 평가"
        conflicts = "[INFO: 상충 ID 미기재 — 등록부 확인]" if c['conflict_ids'] is None else (', '.join(c['conflict_ids']) or '없음')
        rows.append(f"| {c['label']} | {display(pre[c['criterion']]) if c['criterion'] in pre else '미제공'} | {display(c['score'])} | {state} | {conflicts} | {cell(c['summary'] or coverage)} |")
    composite = f"{display(after['total'])}/20, {after['grade']}" if after["total"] is not None else "산정 보류"
    rows += [f"- 검증 후 종합점수·등급(안): {composite}",
             f"- 검증 판정: {VERIFICATION[after['verification']]}",
             f"- 평가 가능성: {sum(c['score'] is not None for c in after['criteria'])}/5개 기준",
             "- 계산: 평가 불가·해당 없음 질문 제외 후 재정규화; 기준별 소수 둘째 자리 반올림 후 합산.",
             "- 민감도: 미해결 상충의 영향은 상세 평정·상충 등록부에서 별도로 검토한다."]
    if after.get('scenarios'):
        totals = [after['total']] + [s['total'] for s in after['scenarios']]
        if all(v is not None for v in totals):
            lo,hi = min(map(Decimal,totals)),max(map(Decimal,totals))
            rows[-1] = f"- 민감도 범위(코드): {display(lo)}~{display(hi)}/20, {band20(lo)}~{band20(hi)}"
        else:
            rows[-1] = "- 민감도 범위(코드): 산정 보류 — 평가 불가 기준이 포함됨"
        rows += ["| 시나리오 | 근거·가정 | 계산점수 | 등급 |", "|---|---|---:|---|"]
        rows += [f"| {s['id']} | {cell(s['reason'])} | {display(s['total'])} | {s['grade'] or '보류'} |" for s in after['scenarios']]
    rows.append(SUMMARY_END)
    return "\n".join(rows)


def question_block(c):
    start = f"<!-- deveval:questions:{c['criterion']}:start -->"
    end = f"<!-- deveval:questions:{c['criterion']}:end -->"
    rows = [start, f"**{c['label']} 질문별 점수(코드 생성)**", "| 채점 질문 | 상태 | 질문 점수 | 가중치 | 사실 ID | 판단 근거 |",
            "|---|---|---:|---:|---|---|"]
    for q in c["questions"]:
        facts = " ".join(f"[사실: {f}]" for f in q["fact_ids"]) or "해당 없음"
        score = display(q["score"]) if q["status"] == "scored" else STATUS[q["status"]]
        rows.append(f"| {q['id']} | {STATUS[q['status']]} | {score} | {display(q['weight']) if 'weight' in q else '균등'} | {facts} | {cell(q['reason'])} |")
    rows.append(f"- 기준 평점(코드): {display(c['score'])}")
    if c["score"] is None:
        rows.append("기준 전체 평가 불가 — 채점 가능한 질문 없음")
    else:
        rows.append(f"- 산식(코드): {display(c['numerator'])} / {display(c['denominator'])} = {display(c['score'])}")
    if c["excluded_questions"]:
        rows.append("- 평균에서 제외: " + ", ".join(c["excluded_questions"]))
    return "\n".join(rows + [end])


def section_span(text, title):
    matches = list(re.finditer(rf"(?m)^##\s+[^\n]*{re.escape(title)}[^\n]*$", text))
    require(len(matches) == 1, f"섹션은 하나여야 함: {title}")
    start = matches[0].end()
    nxt = re.search(r"(?m)^##\s+", text[start:])
    return start, start + nxt.start() if nxt else len(text)


def compatible(after, before):
    if before:
        for key in ("project", "profile", "source_sha256"):
            require(after[key] == before[key], f"검증 전후 {key}가 다름")


def render_text(text, data, before=None, after_name="verified-scores.json", before_name=None):
    after_result = calculate(data)
    before_result = calculate(before) if before else None
    compatible(after_result, before_result)
    require(data["verification"] in ("passed", "conditional"), "검증 전·반려 결과는 최종 브리프로 생성할 수 없음")
    text = BINDING.sub("", text).lstrip()
    # Migrate the former authored score line without losing its rationale.
    # The current rating now has exactly one authority: the generated block.
    text = re.sub(r"(?m)^-\s*잠정 점수 및 이유:\s*\**\d+(?:\.\d+)?\s*점\**[.。]?\s*(.*)$",
                  lambda m:"- 판단 근거: "+m.group(1), text)
    a, b = section_span(text, "종합 평정")
    text = text[:a] + "\n\n" + summary_block(after_result, before_result) + "\n\n" + text[b:]
    for c in after_result["criteria"]:
        pattern = rf"(?m)^###\s+(?:\d+[.)]\s*)?{c['label']}(?:\s*\([^\n)]*\))?(?:\s+(?:평정|평가))?\s*$"
        matches = list(re.finditer(pattern, text))
        require(len(matches) == 1, f"상세 기준 제목 누락·중복: {c['label']}")
        start = f"<!-- deveval:questions:{c['criterion']}:start -->"
        end = f"<!-- deveval:questions:{c['criterion']}:end -->"
        if start in text or end in text:
            require(text.count(start) == text.count(end) == 1, "질문 점수 블록 손상")
            text = re.sub(re.escape(start)+r".*?"+re.escape(end), lambda _:question_block(c), text, flags=re.DOTALL)
        else:
            offset = matches[0].end()
            text = text[:offset] + "\n\n" + question_block(c) + text[offset:]
    binding = json.dumps({"after": after_name, "before": before_name}, ensure_ascii=False)
    return f"<!-- deveval:score-input {binding} -->\n" + text, after_result


def verify_projection(brief, scores=None, before=None):
    brief = Path(brief).resolve()
    text = brief.read_text(encoding="utf-8-sig")
    require(not re.search(r"(?m)^-\s*잠정 점수(?: 및 이유)?:\s*\**\d", text),
            "현재 기준 평점은 수기 행 대신 코드 계산표로만 제시해야 함")
    bindings = BINDING.findall(text)
    require(len(bindings) == 1, "계산 정본 연결 표지가 없거나 중복됨")
    binding = loads(bindings[0])
    keys(binding, {"after", "before"}, {"after", "before"}, "정본 연결")
    def sibling(name):
        require(isinstance(name, str) and Path(name).name == name and name not in (".", ".."), "정본은 브리프와 같은 폴더의 파일이어야 함")
        path = (brief.parent/name).resolve()
        require(path.parent == brief.parent, "정본 경로가 사업 폴더 밖임")
        return path
    after_path = sibling(binding["after"])
    before_path = sibling(binding["before"]) if binding["before"] else None
    require(scores is None or Path(scores).resolve() == after_path, "지정 점수 정본과 브리프 연결이 다름")
    require(before is None or Path(before).resolve() == before_path, "지정 검증 전 정본과 브리프 연결이 다름")
    data = load(after_path); old = load(before_path) if before_path else None
    result = calculate(data); prior = calculate(old) if old else None
    compatible(result, prior)
    require(data["verification"] in ("passed", "conditional"), "미검증·반려 점수는 최종 보고서의 정본이 될 수 없음")
    blocks = [(SUMMARY_START, SUMMARY_END, summary_block(result, prior))]
    blocks += [(f"<!-- deveval:questions:{c['criterion']}:start -->", f"<!-- deveval:questions:{c['criterion']}:end -->", question_block(c)) for c in result['criteria']]
    for start, end, expected in blocks:
        require(text.count(start) == text.count(end) == 1, "계산 블록이 없거나 중복됨")
        found = re.search(re.escape(start)+r".*?"+re.escape(end), text, re.DOTALL)
        require(found and found.group(0) == expected, "정본과 보고서의 계산 블록이 다름 — 코드로 다시 생성해야 함")
    return result


def extract_criterion(text):
    candidates = []
    for body in re.findall(r"```json\s*\n(.*?)\n```", text, re.DOTALL):
        value = loads(body)
        if isinstance(value, dict) and "criterion" in value:
            candidates.append(value)
    require(len(candidates) == 1, "기준 결과에는 criterion JSON 블록이 정확히 하나 필요")
    return candidates[0]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("collect")
    p.add_argument("--directory", required=True); p.add_argument("--manifest", required=True)
    p.add_argument("--project", required=True); p.add_argument("--out", required=True)
    p.add_argument("--profile", default="koica-2024", choices=("koica-2024", "koica-legacy-weighted"))
    for command in ("calculate", "render", "check", "export"):
        p = sub.add_parser(command); p.add_argument("--input", required=True); p.add_argument("--before")
        if command in ("render", "check"): p.add_argument("--brief", required=True)
        p.add_argument("--out", required=command == "export")
    a = ap.parse_args(argv)
    try:
        if a.command == "collect":
            manifest = load(a.manifest)
            data = {"schema_version":1, "project":a.project, "source_sha256":manifest["source_sha256"],
                    "profile":a.profile, "verification":"not_reviewed", "criteria":[]}
            for name in CRITERIA:
                c = extract_criterion((Path(a.directory)/(name+".md")).read_text(encoding="utf-8"))
                require(c.get("criterion") == name, f"{name}.md의 기준 ID가 다름")
                data["criteria"].append(c)
            calculate(data)
            Path(a.out).write_text(dumps(data), encoding="utf-8")
            print(f"질문 점수 정본 수집: {a.out}")
            return 0
        data = load(a.input); before = load(a.before) if a.before else None
        if a.out:
            protected = {Path(a.input).resolve()}
            if a.before: protected.add(Path(a.before).resolve())
            if hasattr(a, "brief"): protected.add(Path(a.brief).resolve())
            require(Path(a.out).resolve() not in protected, "계산 결과 파일로 입력 정본·브리프를 덮어쓸 수 없음")
        result = calculate(data)
        if a.command == "render":
            brief = Path(a.brief).resolve()
            require(Path(a.input).resolve().parent == brief.parent, "점수 정본을 브리프와 같은 폴더에 두어야 함")
            require(not a.before or Path(a.before).resolve().parent == brief.parent, "검증 전 정본도 같은 사업 폴더에 두어야 함")
            text, result = render_text(brief.read_text(encoding="utf-8-sig"), data, before, Path(a.input).name, Path(a.before).name if a.before else None)
            brief.write_text(text, encoding="utf-8")
        elif a.command == "check":
            result = verify_projection(a.brief, a.input, a.before)
        elif a.command == "export":
            require(data["verification"] in ("passed", "conditional"), "미검증·반려 결과는 최종 보고서에 내보낼 수 없음")
            require(Path(a.out).resolve().parent == Path(a.input).resolve().parent, "계산표와 정본은 같은 사업 폴더에 두어야 함")
            prior = calculate(before) if before else None
            compatible(result, prior)
            binding = json.dumps({"after":Path(a.input).name,"before":Path(a.before).name if a.before else None},ensure_ascii=False)
            body = f"<!-- deveval:score-input {binding} -->\n" + summary_block(result,prior) + "\n\n" + "\n\n".join(question_block(c) for c in result['criteria']) + "\n"
            Path(a.out).write_text(body,encoding="utf-8")
            print(f"코드 계산표 내보내기: {a.out}")
            return 0
        if a.out:
            Path(a.out).write_text(dumps(result), encoding="utf-8")
        print(json.dumps({"total":result["total"],"grade":result["grade"],"verification":result["verification"],"input_sha256":result["input_sha256"]}, ensure_ascii=False))
        return 0
    except OSError as exc:
        print(f"점수 계산 확인 불가(exit 3): {exc}", file=sys.stderr); return 3
    except (ValueError, TypeError, KeyError) as exc:
        print(f"점수 정본·투영 위반(exit 2): {exc}", file=sys.stderr); return 2


if __name__ == "__main__":
    raise SystemExit(main())
