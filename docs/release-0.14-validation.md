# 0.14 release verification / 릴리스 검증

Date: 2026-10-23. This is maintainer-side verification of installation,
orchestration, evidence checks, and arithmetic. It is not an independent expert
validation of scoring accuracy. Original reports and native transcripts remain
in the ignored local validation archive, outside the distributed plugin.

## Three changes and their evidence

| Change | Verification |
|---|---|
| Required authored-output scores and grades | Missing grade, bracketed wrong grade, wrong total, and altered question table all fail on copies of the actual output |
| Criterion history isolation | Five `fork_turns: none` workers did not see a parent-only canary; a `fork_turns: all` positive control did see it |
| Code-computed score authority | Question JSON produces all means, exclusions, rounding, totals, grades, and report score blocks; changed/missing authority and unknown F/X references fail |

The native trace is re-read when checking the isolation receipt. Changing a
criterion to inherit history, removing a criterion's calls, or replacing the
receipt's call evidence with an empty list while keeping `passed` all fail.
There were **11 actual-artifact negative cases**, all rejected; the genuine
final artifact passed the strict score/isolation gate and numeric checker.

## Regression and host installation

- **218 Python tests**, **15 completion-hook cases**, manifest identity,
  repository hygiene, Korean/English mirror checks, and Claude plugin and
  marketplace validation passed. PR #26's CI passed before integration.
- Final runtime code was checked at `12acf64badc3f103ab371235d0a1e362458d222a`.
  Separate empty Codex and Claude plugin/config directories each installed all
  **124 tracked files** byte for byte. Both installed checkers passed the final
  real-report artifact with `--require-scores --require-isolation`.
- Codex CLI 0.146.0 and Claude Code 2.1.294 were used. The real full evaluation
  used Codex; Claude received installation/manifest checks and compatibility
  checks against an existing native trace, not a new full 0.14 report run.
- A separate plugin-creator validator was unavailable; Codex's native
  marketplace installation was the host-specific check.
- Empty application configuration/cache directories are not a fresh OS image.
  The full model run reused existing authentication by a temporary symlink,
  without copying user settings or companion MCP configuration. The reviewed
  completion hook was trusted for that invocation; the workspace sandbox
  remained enabled. Installation-only checks did not need that authentication.

## Actual report and full workflow

Input: *요르단 시리아 난민 밀집 지역 취약계층 아동을 위한 3개 학교 건립사업
(2017–2022/1,110만불) 신속평가 결과보고서*, 2023.10. Source ID
`000000018487_01.pdf`, 64 pages; SHA-256
`c8f2da2e8f260aa74b1cd3e60c562cffdaaa7984b08be2ab662383af4db0745b`.

The full run started with the original PDF in a new working directory and a
fresh installation of candidate `e1aa323371be6b86e615f8af4146aeb3952ed418`.
`$deveval:evaluate` performed conversion, source indexing, the fact ledger,
frozen packet preparation, five criterion ratings, verification, code
calculation, report assembly, and final checks. It exited 0 in **22.73 minutes**.
The default observed model was `gpt-5.6-sol`, without a model override.

| Observation | Result |
|---|---|
| Fact ledger | 45 rows, 35 F-IDs |
| Conflict register | 8 X-IDs; unresolved/partly resolved items retained |
| Criterion calls in native trace | Five initial calls and four retries; all nine use `fork_turns: none` and the same run scope |
| Question authority | `ratings.json` before verification; `verified-scores.json` after verification |
| Code-computed criterion scores after verification | 2.75, 2.75, 2.67, 2.25, 2.25 |
| Code-computed composite | **12.67/20, D**, conditional provisional result |
| Unchecked plan items | 0 |
| Final audit and numeric checks | Both exit 0 |

Pinned kordoc 4.24.1 retained page markers and warnings: 12 low-confidence OCR
pages, 11 pages with skipped images, and 42 image regions. These overlap; they
are not a count of distinct unusable pages. The final brief retains warnings,
missing source records, conflict links, corrections, and the human decision gate.

## What the real run exposed, and final-code replay

Native Codex logs encrypt delegation message bodies. The initial isolation
probe therefore failed instead of claiming a pass from unreadable prompts.
The revised contract uses visible run-scoped task names, successful native call
results, explicit `fork_turns`, and frozen input hashes. A second live canary
probe passed with its positive control. **The checker still cannot inspect the
encrypted message contents.** The receipt reports this limitation, and the
final brief must disclose it. No native messages were decrypted.

The real report exposed another contract mismatch: pre-verification evaluators
use local conflict IDs, while the initial JSON validator accepted only global
IDs. Four workers retried their JSON metadata. The final code accepts local IDs
only before verification and requires global X-IDs afterward. Replaying the
first five preserved responses now succeeds without those metadata retries;
that diagnostic replay does not replace the actual evaluation chain.

Final code also fixes native Claude directory escaping and treats omitted
conflict metadata as unknown, not as an assertion that no conflict exists.
The latter correctly invalidated the candidate's old rendered score block.
We preserved that candidate output and regenerated a separate final artifact
from the **unchanged** before/after question JSON. Both authority files are byte
identical to the original run. The numeric result remains 12.67/20, D; the
display now explicitly flags missing conflict metadata for review.

This is a full candidate model run followed by deterministic replay with the
final installed code, not a claim that the entire model run was repeated at
the final commit. Subsequent changes affect metadata acceptance, trace lookup,
and honest display; the question judgments and arithmetic did not change.

## Limits / 판정 범위

History isolation and frozen-file integrity do not prove that an encrypted
prompt contains only approved evidence, or provide a filesystem sandbox.
The original report's human grade was visible, so this is not a blind accuracy
benchmark. No independent experts cross-scored this run. One report does not
establish reliability across sectors, countries, models, or repeated runs.
The optional evidence gateway was not connected. OCR/image limitations and
missing accounting, approval, registration, and defect-inspection originals
remain unresolved evidence constraints.

세 개선과 회귀시험·새 설치·실제 보고서 전체 실행·최종 코드 재계산을 확인했다.
다만 암호화된 위임문 내용, 전문가 채점 정확도, 모든 원자료의 진실성까지 검증한
것은 아니다. **최종 점수·등급은 평가담당관이 확정한다.** 실행 기록·정본·변조
시험과 원래 산출물/재생성본은 `.local/release-validation/v0.14.0/`에 보존한다.
