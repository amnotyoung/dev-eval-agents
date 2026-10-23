# 0.13 release verification / 릴리스 검증

Date: 2026-10-23. This is a maintainer-side integration test, not an independent
expert validation of evaluation scores. Original reports, converted full text,
and agent transcripts remain local and are not distributed with the plugin.

## Published artifacts

| Version | Commit | Purpose |
|---|---|---|
| 0.13.0 | `984fd7a55af5c6bf4611e583e8d9d237c5eed3d3` | PRs #18–#23: source ledger, checker repairs, conversion, role contracts, release hardening |
| 0.13.1 | `06ff2d6191a739b1b402aba25d68e855bf4f1acd` | PR #24: bare-grade parser fix discovered from actual output |

The 0.13.0 tag was not moved. Use 0.13.1 for grade validation.

## Deterministic checks and installation

- 0.13.0: 169 Python tests and 15 completion-hook cases passed.
- 0.13.1: 173 Python tests and the same 15 hook cases passed; main CI passed.
- Manifest identity, repository hygiene, Korean/English mirror checks, and
  Claude plugin validation passed for the integration release.
- Both tags were installed in separate empty Codex and Claude plugin/config
  directories. Codex installed from the public Git tag; Claude installed from
  a fresh checkout of that tag. No prior user settings or companion MCP
  configuration were copied. Existing authentication was reused for model
  execution. This is a fresh application configuration, not a fresh OS image.
- Codex CLI: 0.146.0. Claude Code: 2.1.294. Claude installation and manifest
  validation were checked; the full report-generation runs used Codex.
- The 117 tracked files in the installed Codex 0.13.0 package matched the
  public tag byte for byte.
- The 117 tracked files in both installed 0.13.1 packages (Codex and Claude)
  also matched that public tag byte for byte before evaluation.
- A separate plugin-creator validator was not available in this environment;
  Codex's native marketplace installation/loading was the host-specific check.

## Real-report input

- Report: *요르단 시리아 난민 밀집 지역 취약계층 아동을 위한 3개 학교 건립사업
  (2017–2022/1,110만불) 신속평가 결과보고서*, 2023.10.
- Source ID: `000000018487_01.pdf`; 64 PDF pages.
- SHA-256: `c8f2da2e8f260aa74b1cd3e60c562cffdaaa7984b08be2ab662383af4db0745b`.
- Input was the original PDF in a new working folder, not a prepared text
  extract. `$deveval:evaluate` performed conversion and the evaluation workflow.
- kordoc 4.24.1 (pinned npx) retained page markers and warnings: 12 low-confidence
  OCR pages, 11 pages with skipped images, and 42 image regions. These counts
  overlap and are not a count of distinct unusable pages.

## 0.13.0 run and the defect it exposed

The full run exited 0 after 20.04 minutes. It produced the plan, source index,
fact ledger, five criterion drafts, independent verification, and final brief.
The final brief had 58 ledger rows, 46 fact IDs, 12 conflict records, and no
unchecked plan items. The audit and numeric checks were independently rerun.

The audit gate caught an actual assembly problem: JONEPS procurement and Queen
Rania Academy cooperation shared F9 but linked to different conflicts. The
workflow retained F9 for procurement and added F46 for cooperation, preserving
both X4 and X5 before passing. The final score was a provisional 11.67/20 (E),
with E–D sensitivity and a conditional verification judgment. The report's
existing human grade remained visible in the input, so this was not a blind
accuracy benchmark.

**Passing the generated document was not sufficient.** Replacing its final
`11.67/20, E` with `11.67/20, A` still passed both checkers in 0.13.0. The numeric
parser recognized `E(안)` but missed the bare letter specified by the composer.
PR #24 fixes that exact shape, including Markdown emphasis. The genuine output
passes under 0.13.1; the wrong-grade copy returns exit 2. Grade extraction over
the existing 334-report text corpus was unchanged by the narrow fix.

The first run used ephemeral sessions and logged parent-transcript lookup
warnings for subagent hooks; it still completed. The patch run retains local
transcripts to make role invocation inspectable. The reviewed completion hook
was trusted for the invocation; the workspace-write sandbox remained enabled.

## 0.13.1 fresh full run

The second run used a separate empty plugin/config cache and working directory,
installed the published 0.13.1 tag, and started again from the original PDF.
It exited 0 after **17.01 minutes**. The observed default model was
`gpt-5.6-sol`; it was not overridden by the test command.

The retained trace confirms eight worker roles: source analyst, relevance,
coherence, effectiveness, efficiency, sustainability, quality verifier, and
report composer. The final package contains the plan, source index, criterion
drafts, verification result, and completed auditable brief:

| Check | Observed result |
|---|---|
| Fact ledger | 58 rows, 48 F-IDs |
| Conflict register | 10 X-IDs, including unresolved/partly resolved evidence |
| Unchecked plan items | 0 |
| Independent audit-check rerun | exit 0 |
| Independent numeric-check rerun | exit 0; both total and grade extracted |
| Actual output changed from D to A | exit 2, grade/score mismatch |
| Actual output changed from 12.42 to 19.42 | exit 2, criterion-sum mismatch |
| Installed package after model execution | 117 tracked files still identical to the tag |

The provisional result was **12.42/20, D**, with a **conditional** verification
judgment. Source warnings, missing records, conflict IDs, and the human final
decision were retained. Spot checks against a separate pdftotext extraction
confirmed the reported project period, total budget, regional refugee counts,
curriculum development count, the main school-enrolment figures, and the
4,000-JD annual school budget. This was a limited factual spot check, not a
full validation of all 48 facts, qualitative judgments, or OCR/image content.

The first run's assembly issue and grade-mutation false pass were preserved in
the record instead of treating its exit 0 as sufficient evidence of reliability.

## Interpretation and limits / 판정 범위

Installation, workflow completion, output-contract checks, arithmetic, and
source-fact spot checks are distinct evidence. None establishes general scoring
accuracy or replaces the evaluation officer. One real report does not establish
cross-country, sector, model, or repeated-run reliability. The optional evidence
gateway was not connected. Low-confidence image/OCR evidence and missing
accounting, approval, registration, and defect-inspection records remain limits.

The patch changes grade parsing, not the scoring rubric or LLM prompts. The
two runs nevertheless produced different provisional grades (0.13.0: E;
0.13.1: D). This is observed rating variation, not evidence that the
patch improved project performance or scoring accuracy.

The retained Codex trace uses `fork_turns: all` for criterion workers. Their
delegation prompts omit other criteria's scores, but inherited parent history
can expose earlier results to later batches. Separate role invocation therefore
does **not** prove structurally isolated or blind ratings. This remains a
limitation of this tested configuration, in addition to the human grade being
visible in the source report.

새 설치와 실제 보고서 전체 실행을 확인하되 **전문가 채점 정확도를 입증한 것은
아니다.** 기존 334건은 수치 검사기 시험이고, 이번 실제 보고서는 1건이다.
최종 점수·등급은 평가담당관이 확정한다. 원문·변환본·전체 실행 로그는 로컬의
`.local/release-validation/`에 보존하며 공개 저장소에 커밋하지 않는다.
Codex 실행은 `fork_turns: all`로 상위 이력을 상속했다. 위임문에서 다른 기준의
점수를 제외해도 뒤 묶음에 앞선 결과가 노출될 수 있으므로 완전한 블라인드·컨텍스트
독립성까지 입증한 것으로 해석하지 않는다.
