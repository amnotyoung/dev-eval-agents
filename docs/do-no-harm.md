# Do No Harm by Design / 무해성 설계

> Evidence for the Digital Public Goods Standard, **Indicator 9 (Do No Harm By
> Design)** and its sub-indicators 9A / 9B / 9C, plus the AI-specific
> do-no-harm expectations for an LLM-assisted tool.
> 디지털 공공재 표준 **지표 9(무해성 설계)** 및 9A/9B/9C, 그리고 LLM 보조 도구에
> 대한 AI 특유 무해성 기대 근거 문서.

## What "harm" would look like here / 이 도구에서의 위해 시나리오

The realistic risk of an AI evaluation aid is **not** user-generated-content
abuse; it is a *wrong or fabricated judgment* being treated as authoritative, or
personal data in a report being mishandled. The system is designed against
exactly these. AI 평가 보조도구의 실질 위험은 사용자 콘텐츠 남용이 아니라 **틀리거나
지어낸 판단이 권위 있는 것으로 오용되는 것**과 개인정보 오처리다 — 시스템은 바로
이 둘을 막도록 설계됐다.

## 9A — Data privacy & security / 데이터 프라이버시·보안

Covered in full by [`../PRIVACY.md`](../PRIVACY.md). Summary: the project stores
**no** personal data, runs locally, minimizes exposure, instructs agents to
**anonymize** individuals, and offers a **local open-weight** path so sensitive
documents need never leave the user's machine. Applicable law: Korea PIPA / GDPR
(user is the data controller).

전문은 [`../PRIVACY.md`](../PRIVACY.md). 요약: 개인정보 무저장·로컬 실행·노출
최소화, 개인 **익명 처리** 지시, 민감 문서를 위한 **로컬 오픈모델** 경로 제공.

## 9B — Inappropriate & illegal content / 부적절·불법 콘텐츠

**Not applicable by design.** The tool does **not** collect, host, publish, or
distribute user-generated or third-party content. It reads a document the user
already possesses and writes an evaluation to the user's own disk. There is no
content platform, feed, upload, or sharing surface to moderate.

**설계상 해당 없음.** 이 툴은 사용자 생성·제3자 콘텐츠를 수집·호스팅·게시·배포하지
않는다. 사용자가 이미 보유한 문서를 읽어 로컬에 평가를 쓸 뿐, 검열 대상이 되는
콘텐츠 플랫폼·피드·업로드·공유 기능이 없다.

## 9C — Protection from harassment / 괴롭힘 방지

**Not applicable by design.** There is no user-to-user interaction, no accounts,
no comments, no social features. The project's community spaces (issues, PRs) are
governed by the [Code of Conduct](../CODE_OF_CONDUCT.md).

**설계상 해당 없음.** 사용자 간 상호작용·계정·댓글·소셜 기능이 없다. 프로젝트
커뮤니티 공간(이슈·PR)은 [행동강령](../CODE_OF_CONDUCT.md)이 규율한다.

## AI-specific safeguards / AI 특유 안전장치

These are the heart of the do-no-harm design and are enforced in the agents'
instructions (`CLAUDE.md`, `AGENTS.md`, `.claude/agents/*`), grounded in KOICA
evaluation ethics (Regulation No. 536) and the OECD-DAC framework:

| Safeguard / 안전장치 | How it works / 작동 방식 |
|---|---|
| **Human gate / 사람 게이트** | AI never finalizes a grade. Every output is a **draft** and ends by deferring the final grade/decision to a human evaluation officer. (원칙 5) |
| **Evidence gate / 근거 게이트** | *No evidence → no grade / no text.* When a criterion lacks supporting evidence, the system marks it **"cannot evaluate (평가 불가)"** instead of guessing. Fabrication is prohibited. (원칙 1) |
| **Anti-hallucination verification / 반환각 검증** | `quality-verifier` and `narrative-verifier` cross-check every score/claim against cited evidence and internal consistency; unverified items are flagged `[INFO]`. |
| **Limitation labeling / 한계 라벨링** | Qualitative impact, recipient-country context, and political judgments are explicitly labeled **"requires human judgment"**. (원칙 6) |
| **Balance / 완결성** | Strengths *and* weaknesses must both be reported, with limitations stated. (원칙 4) |
| **Evaluation independence / 평가 독립성** | The system will not bend a score under undue pressure to alter results (Reg. 536 Art. 19); it self-corrects toward the evidence rather than complying with biased framing (see validation-log §3). |
| **Equity / LNOB** | The effectiveness criterion explicitly checks inclusion of vulnerable groups and differential results (Leave No One Behind). |

## Intended use & misuse / 의도된 용도와 오용 방지

- **Intended:** *decision support* for trained human evaluators — drafting,
  cross-checking evidence, and surfacing gaps, so a person evaluates faster and
  more consistently.
- **Not intended / misuse:** automated **final** grading without human
  confirmation; public ranking or "scoring" of named projects, institutions, or
  countries; or replacing professional evaluators. Outputs are drafts for expert
  review, **not** authoritative verdicts.

**의도된 용도**는 훈련된 평가자를 위한 *의사결정 지원*(초안·근거 교차확인·공백
발견)이다. **오용 금지**: 사람 확인 없는 자동 최종등급, 실명 사업·기관·국가의
공개 순위매김, 전문 평가자 대체. 산출물은 전문가 검토용 초안이지 확정 판정이 아니다.

## Known limitations (honest) / 알려진 한계 (정직)

Documented in [`validation-log.md`](validation-log.md) §4: small validation
sample; results depend on the quality of the human/assistant fact-extraction
step; open-weight models demonstrate portability but not quality parity;
calibration (conservatism) is still being tuned. These are disclosed so users do
not over-trust outputs.

한계는 [`validation-log.md`](validation-log.md) §4에 공개: 소표본, 사실추출 품질
의존, 오픈모델의 품질 비동치, 캘리브레이션 진행 중 — 과신을 막기 위해 명시한다.
