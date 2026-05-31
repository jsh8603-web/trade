---
tags: [type/collector-request, domain/inv, study/gold]
date: 2026-05-31
study_id: gold
note: main 의 ★순서정정 (candidate-ledger reverse) 후 merit 후보 → main collector 구현 요청. 무료 데이터 source 후보 명시. main collector 완료 후 → study (이론→실데이터→상관·Rank-IC) → 12축 audit (별도 subagent) → yaml 반영.
---

# Gold collector 구현 요청 (main 의 ★순서정정 후속)

> 흐름: main collector 구현 → gold study (이론·실측·상관·Rank-IC) → 12축 audit (별도 subagent) → yaml 반영.
> 우선순위 기준: (a) merit 근거 강도 (lens·H 가설 직결도) (b) 무료 data source 가용 (c) 데이터 power (n, 기간, 위기 포함).

---

## ★1. credit_HY_OAS — FRED ALFRED API key (free) 발급 필요

**merit 근거**: H5 safe-haven 국면의존 가설 (Baur-Lucey 2010) 의 1차 검증 변수. 본 study 의 fredgraph.csv endpoint 가 3년치(2023-05~)만 반환(cosd 무시 미해결) — 2008 GFC + 2020 covid + 2022 stress 모두 미포함. Markov regime-switching 위기 vs 평시 분리 power 부족. **FRED ALFRED API key (free, 무제한)** 로 1996~ full history 확보 가능.

**필요 collector**: FRED ALFRED API client (`api.stlouisfed.org/fred/series/observations?series_id=BAMLH0A0HYM2&api_key=...`). 본 시스템 `core/brain/fred_adapter.py` 에 API 경로 확장 + .env `FRED_API_KEY` 추가.

**무료 source 후보**: FRED ALFRED (https://fred.stlouisfed.org/docs/api/fred/ — register free key 1분).

**현재 임시**: D2 credit_BAA10Y (Moody's BAA−10Y, 4279 obs fredgraph.csv 통과) 1차 사용 — H5 검증은 BAA10Y 로 진행 가능하나 HY OAS 의 high-yield-credit 신호와 dimension 차이.

---

## ★2. economic_expansion — Manufacturing PMI / OECD CLI

**merit 근거**: WGC GRAM 4-driver 의 1개 (economic expansion category) 미실현. 본 study force_include 4 의 GRAM 1:1 span 에 economic expansion 자리가 비어 있음 (현재 cb_demand 로 대체). 실측 gold↔eco cyclical 정합 검증 시 lens regime_reading 의 Investment Clock 4국면 (Recovery·Overheat·Stagflation·Reflation) 매핑 정밀화.

**필요 collector**: (a) ISM Manufacturing PMI (월별, 미국) (b) OECD CLI Composite Leading Indicator (월별, OECD-wide) (c) Global Manufacturing PMI (S&P Global, 유료).

**무료 source 후보**:
- ISM Manufacturing PMI: FRED 시리즈 `MANEMP` 또는 `NAPM` (deprecated, ISM 직접) — ISM 유료 정책으로 lag 6mo 무료 / 실시간 유료.
- **OECD CLI**: stats.oecd.org / OECD SDMX-JSON API (★무료, 월별 1960~). 추천 1순위.
- ifo World Economic Climate (분기, free).

**study 활용**: M3 4 epoch 정합 + Investment Clock regime conditional 의 economic_expansion 차원 확장.

---

## ★3. cb_demand_quarterly — WGC GDT 분기 시계열

**merit 근거**: H3 cb_demand level 운반 검증 PARTIAL (annual n=15 power 한계). ★분기 데이터 (60 obs 2010-2024) + R2 Q5 Kalman smoother 합의로 SUPPORTED 전환 가능성 매우 높음. annual Pearson +0.784 → quarterly 시 Johansen + EG 정식 cointegration 통과 expected.

**필요 collector**: WGC GDT 분기 PDF/HTML parser (gold.org/goldhub/research/gold-demand-trends) → quarterly CB net purchase tonnes table 추출 + Kalman state-space smoother (statsmodels.tsa.statespace.sarimax 또는 직접 구현).

**무료 source 후보**:
- **WGC Gold Demand Trends** (gold.org public, 분기별 PDF + HTML 표) ★무료.
- IMF IFS reserves data (★무료, cross-validate).

**study 활용**: H3 PARTIAL → SUPPORTED 전환 + H2 unexplained ln_gold trend 와의 cointegration 정식 검증.

---

## ★4. move_index — ICE BofAML MOVE Index (채권 변동성)

**merit 근거**: R2 Claude 의 추가 변수 (별도 regime 변수). credit_HY_OAS 와 분리된 *interest rate vol* regime 신호. H5 safe-haven 의 ※채권 vol 채널 (equity vol VIX 와 dimension 분리). 본 시스템 risk regime 분리 정밀화.

**필요 collector**: Yahoo Finance `^MOVE` 또는 ICE 직접.

**무료 source 후보**:
- **Yahoo Finance ^MOVE** (yahoo v8 chart, ★무료, 일별 2002~).
- ICE 직접 (유료).

**study 활용**: H5 위기 regime 정의의 2 차원 분리 (equity vol VIX + bond vol MOVE).

---

## ★5. etf_holdings_flow — SPDR GLD daily 보유량 + IAU

**merit 근거**: WGC GDT 의 investment demand 의 일별 proxy. cftc_mm_net_long_gold (E1 채택, zip fetch 완료) 과 함께 *positioning* 차원의 양대 신호. R1 자문 Claude 의 변수정의표 부수 항목.

**필요 collector**: SPDR Gold Trust 일별 보유량 (gld.com 또는 spdrgoldshares.com daily holdings 페이지) + iShares Gold Trust IAU 일별 보유량.

**무료 source 후보**:
- **SPDR Gold Trust** (spdrgoldshares.com/total-tonnes-in-trust-history.html, ★무료, csv export 또는 HTML table).
- **WGC ETF Flow Data** (gold.org/goldhub/data/gold-backed-etf-flow, ★무료, 일별).

**study 활용**: positioning 가설 H7 (GPR force) 와 동등한 force_include 후보 검증. cftc_mm 과 partial corr 분해.

---

## ★6. shanghai_gold_premium — SGE physical premium

**merit 근거**: 중국 physical demand 신호. Arslanalp 2023 의 신흥국 de-dollarization 메커니즘의 *retail* 측 단서 (CB 가 official sector 라면 SGE 는 retail/jewelry). 2024-26 랠리의 China premium 패턴 검증.

**필요 collector**: SGE (Shanghai Gold Exchange) 일별/주별 spot 가격 − LBMA PM (premium = SGE − LBMA).

**무료 source 후보**:
- **SGE 공개 daily fixing** (en.sge.com.cn/data, ★무료).
- LBMA PM (B4 의 fix endpoint 실패 — 대안 = Yahoo XAU 또는 다른 source).

**study 활용**: 2022-26 China decoupling 의 retail 측 cross-validate (Arslanalp 의 CB official 측 ↔ SGE retail 측 양면).

---

## 부록 7. (낮은 merit, 보조) USD-exempt basket — 이미 4 FX fetch 완료, 합성만

본 study 가 이미 FRED DEXUSEU/DEXJPUS/DEXCHUS/DEXUSUK fetch 완료 → 합성 1줄로 가능 (gold_USD-excluded = gold_USD / (EUR/USD)^w1·(JPY/USD)^-w2·... constant weights). collector 신규 필요 X. study 직접 진행.

---

## ★8. sys_priors gold loading 재보정 (main G6 게이트 사안)

**merit 근거**: H4 압도 기각 (실측 일별 std β rate=-0.27/dollar=-0.29 vs sys [-0.5, -0.8]) + numeraire trap +66.8% 감쇠. production wiring 시 정정 필수. **main G6 게이트 사안** = collector 가 아니라 system_priors.py 의 직접 정정.

**필요 정정 (collector 아닌 code)**: `core/study/system_priors.py` 의 gold factor loading 을 실측 기반 재보정. derivation 출처 (theoretical / regime-conditional / multivariate) 확인 후.

---

## 종합 우선순위 (main 의 collector 작업큐)

| # | 후보 | merit | 무료 source | 본 study 영향 |
|---|---|:---:|---|---|
| ★1 | HY OAS full history | 최상 | FRED ALFRED key | H5 위기 검정력 회복 |
| ★2 | OECD CLI | 최상 | OECD SDMX-JSON | force_include 4 의 economic expansion 자리 채움 |
| ★3 | WGC quarterly CB | 최상 | WGC GDT public | H3 PARTIAL → SUPPORTED |
| ★4 | MOVE Index | 상 | Yahoo ^MOVE | H5 bond vol regime 분리 |
| ★5 | SPDR GLD daily | 상 | spdrgoldshares.com | positioning 2 차원 |
| ★6 | Shanghai premium | 중상 | en.sge.com.cn | China retail decoupling cross |
| (보조) | USD-exempt basket | 중 | 합성 (자체) | numeraire trap 직접 검증 |
| ★8 | sys_priors 재보정 | 최상 (code) | (main G6 게이트) | production wiring 정합성 |

★ main 의 collector 작업 완료 후 본 작업방이 study (이론→실측→상관/Rank-IC) → 12축 audit (별도 subagent) → yaml 반영 흐름 재개.

★ 한편 본 study 의 ★기존 fetch 완료 데이터 (CFTC zip 3건, FRED 9 시리즈, Yahoo DXY+GLD, GPR xls, WGC annual) 로 진행 가능한 작업 = H5 (BAA10Y/VIX 사용 Markov-switching) + H8 (이중 e-process) + yaml v2 + §2.5 8축 audit 는 main 의 collector 의존성 없음 → 본 작업방 자율 진행 가능.
