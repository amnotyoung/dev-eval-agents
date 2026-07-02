# Real-world evaluation targets / 실제 평가 대상 예시

> This tool is designed to evaluate **real, publicly published** KOICA evaluation
> reports. This page **links** to KOICA's own public pages — no report files are
> redistributed here (they are runtime inputs the user supplies; see
> [`../PRIVACY.md`](../PRIVACY.md)). Linking to a public page raises no copyright
> or privacy issue regardless of the report's 공공누리 (KOGL) license type.
>
> 이 툴은 **실제 공개된** KOICA 평가보고서를 평가 대상으로 한다. 이 문서는 KOICA의
> 공개 페이지로 **링크**만 하며 보고서 파일을 재배포하지 않는다(원문은 사용자가 실행
> 시 제공하는 런타임 입력). 공개 페이지 링크는 원문의 공공누리 유형과 무관하게
> 저작권·개인정보 문제가 없다.

## Authoritative public indexes / 권위 있는 공개 인덱스

- **KOICA Business Evaluation Information Disclosure Platform / KOICA 사업평가
  정보공개 플랫폼** — final-evaluation reports, evaluation yearbooks, M&E resources:
  https://www.koica.go.kr/koica_kr/976/subview.do
- **Public Data Portal dataset / 공공데이터포털** — "한국국제협력단_개발협력사업
  종료평가보고서" (carries an explicit 공공누리/KOGL license tag):
  https://www.data.go.kr/data/15120039/fileData.do
- **KOICA ODA Library / KOICA ODA 도서관**: https://lib.koica.go.kr/

## Representative targets / 대표 평가 대상

Reports the framework has been checked against (see
[`validation-log.md`](validation-log.md) §2) plus a governance example, spanning
several sectors — which is also why the tool's SDG relevance is broad. Exact
library titles and URLs are being finalized by the maintainer.

| Report (descriptive) | Type | Sector / SDG | URL |
|---|---|---|---|
| Cambodia — cervical cancer screening software project, final evaluation | Final (CTS, 6 criteria) | Health / SDG 3 | *maintainer to confirm* |
| Myanmar — solar power (electrification) project, final evaluation | Final (infrastructure) | Energy / SDG 7 | *maintainer to confirm* |
| Pakistan — wastewater treatment project, final evaluation | Final (infrastructure) | Water & sanitation / SDG 6 | *maintainer to confirm* |
| Vietnam — vocational-training capacity building, impact evaluation | Impact evaluation | Education / jobs, SDG 4 & 8 | *maintainer to confirm* |
| Uzbekistan — public-administration academy capacity building (2017–2021), final evaluation | Final (governance) | Institutions / SDG 16 | *maintainer to confirm* |

> These reports are **not** bundled in this repository. The tool reads a report
> the user provides at runtime and produces a draft evaluation for human review.
