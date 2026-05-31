# validation-fundamental — Layer 1 펀더멘털 IC

> 2026-05-30, Tier 3 한국 바이오 sub-study, frame.md §M1 횡단면 Rank-IC 의도.
> ★ **본 라운드 = INSUFFICIENT** — DART_API_KEY 부재로 DART 펀더멘털 (PER/PBR/ROE/EPS revision) 적재 0건.

## §1 Layer 1 펀더멘털 지표 후보 (frame §3 Layer 1)

| family | 지표 id | source | status |
|---|---|---|---|
| valuation | per_fwd, pbr, ev_ebitda, div_yield | DART 또는 Naver Finance scrape | × DART_API_KEY 부재 |
| quality | roe, roa, op_margin, debt_ratio | DART | × |
| revision | eps_yoy, sales_yoy, op_margin_yoy | DART | × |
| growth (e-KJFS) | rd_to_asset, capex_to_asset, intangible_to_asset | DART | × |
| size | market_cap | FDR Marcap | ○ 적재 완료 |

## §2 본 라운드 산출

### 2.1 산출 0건
- DART_API_KEY 부재 → `stock/data/dart_provider.py DartXbrlProvider` graceful empty.
- DART 사용 시 약 50+ 종목 분기 펀더멘털 (PER/PBR/EPS/ROE) 적재 가능, 본 라운드 미진행.
- frame §5 8 파일 의무 충족 위해 본 파일 작성.

### 2.2 시총 (size) 만 가용
- universe Top 30 중 시총 분포 = 0.49조원 ~ 63.1조원 (×100배 dispersion)
- 시총 ↔ forward return 검증 = round-N future scope (시총 size factor 가 한국 시장에서 weak negative — frame §3 finding 권고 기반).

## §3 5게이트 status

- ★ **N gate**: 0/0 (적재 미달)
- ★ **SE gate**: 적용 불가
- ★ **Power gate**: 적용 불가
- ★ **FDR gate**: 적용 불가
- ★ **OOS gate**: 적용 불가
- **★verdict = INSUFFICIENT** (DART_API_KEY 의무 후 round-N 재검증)

## §4 collector_plan_industry (Layer 1)

| ID | item | source | priority | 비고 |
|---|---|---|---|---|
| BIO-D1 | DART_API_KEY 발급 + DART XBRL fetch | dart.go.kr | **P0** | 즉시 진행 |
| BIO-D2 | 한국 컨센서스 EPS (Naver Finance scrape) | Naver Finance | P1 | M1 revision indicator 핵심 |
| BIO-D3 | 한국 바이오 ROE 분기 시계열 (DART) | DART | P1 | quality factor |
| BIO-D4 | 한국 바이오 R&D/매출 분기 시계열 (DART) | DART | P1 | bio specific (R&D intensity) |

## §5 main 보고

본 validation-fundamental.md = ★INSUFFICIENT (Layer 1 IC 0건). frame §6 12축 평가 시 Hard-fail B (실데이터) FAIL → **Layer 1 만 INSUFFICIENT, Layer 2·Layer 3 는 PARTIAL** 로 분리 보고. round-N (DART_API_KEY 발급 후) 재검증.

⛔ **점추정 IC prior 박제 금지** (frame §0 ⛔). Layer 1 weight rule = `summary.yaml weight_rule_candidates` 에 포함 X (검증 0건).
