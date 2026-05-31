---
tags: [type/raw, domain/inv, asset/bond, asset/cash, phase/study, round/3]
date: 2026-05-30
round: 3
topic: HY OAS credit cycle 와 채권/현금 거동
source: WebSearch (native fallback)
---

# Round 3 — HY OAS Credit Cycle × 채권 거동

## 검색어
`high yield credit spread OAS recession indicator bond returns regime cycle backtest`

## 원천 (URL hyperlink)
- [High-Yield Spreads: The 319 bps Signal That Precedes Every Crash (Money365)](https://www.money365.market/articles/credit-cycle-analysis)
- [BAMLH0A0HYM2: US High Yield OAS Daily Data Since 1996 (eco3min)](https://eco3min.fr/en/credit-spreads-recession-risk-dataset/)
- [High yield bonds: Can tight credit spreads persist? (Janus Henderson — US Investor)](https://www.janushenderson.com/en-us/investor/article/high-yield-bonds-can-tight-credit-spreads-persist/)
- [High yield bonds: Can tight credit spreads persist? (Janus Henderson — US Advisor)](https://www.janushenderson.com/en-us/advisor/article/high-yield-bonds-can-tight-credit-spreads-persist/)
- [ICE BofA US HY Index OAS — TradingView (FRED:BAMLH0A0HYM2)](https://www.tradingview.com/symbols/FRED-BAMLH0A0HYM2/ideas/)
- [Bond Yield Credit Spreads — Updated Chart (LongtermTrends)](https://www.longtermtrends.com/bond-yield-credit-spreads/)
- [Forecasting the Leading Indicator of a Recession: 10Y-3M Treasury Yield Spread (arXiv 2009.05507)](https://arxiv.org/pdf/2009.05507)

## 핵심 정제

### 1) HY OAS = 가장 신뢰 가능한 침체 선행 지표 중 하나
- "single most reliable early warning indicator for recessions and market crashes"
- "tending to widen months before equities peak" (주식 peak 보다 *수개월* 선행)
- 1996-2024 분석: **HY OAS 가 600 bps 돌파 시 12-18개월 내 침체 발생 ~85%**

### 2) 데이터 사양 (BAMLH0A0HYM2)
- ICE BofA US High Yield Index Option-Adjusted Spread
- Below-investment-grade US corporate bonds 가 같은 만기 Treasury 대비 지불하는 daily 시장 프리미엄
- FRED 배포 시작 = **1996-12** → 30년 가까운 historical 가용
- 현재 in_our_system ✅ (`fred_adapter.FRED_SERIES[BAMLH0A0HYM2]`)

### 3) Credit Cycle 단계 vs 매수 시점
- **peak 시 HY 매수**: "highest-quality junk bonds purchased at peak spreads have historically delivered **15-25% annual returns over the subsequent 2-3 years**"
- 즉 spread 정점 부근에서 contrarian HY 매수 → recovery 단계 수익 큼
- **확대 진행 중**: default 위험 + 유동성 위축 동반, 매수 부적절
- **압축 진행 중**: carry 우위 (현재 spread 가 좁아도 default-adjusted yield 양수면 매수)

### 4) Multi-Signal 침체 경보 시스템
- "3-signal warning system combining HY spreads, yield curve, and VIX can provide 4-8 months of lead time"
- 3 시그널 조합:
  1. HY OAS (credit risk premium)
  2. yield curve (10Y-2Y or 10Y-3M)
  3. VIX (주식 implied vol)
- → 단일 시그널 보다 noise reduction. 조합 weight 가 가능한 합성 signal.

## 우리 시스템 매핑

| 시그널 | 우리 indicator | 현재 코드 위치 |
|---|---|---|
| HY OAS | `credit_spread_hy_oas` (BAMLH0A0HYM2) | ✅ in_our_system, blocks 2/3/4 활용 |
| Yield curve | `yield_10y_2y` (T10Y2Y) | ✅ in_our_system |
| VIX | (부재) | ❌ blockt 6 collector_plan 신규: FRED `VIXCLS` |

→ **VIX 도입 권고**. 현재 7 indicators 만으로 3-signal warning 미구성.

## 가설 초안 (라운드 3)

**H3-A**: HY OAS 의 600 bps 돌파 후 12-18개월 forward bond sleeve return 이 cash sleeve 보다 평균 negative spread (cash 우위 입증).
   - 반증: 1996-2024 sample 에서 600bps event 후 12-18개월 평균 return spread (bond − cash) ≥ 0.

**H3-B**: HY OAS Z-score 의 6주 변화율 이 HY ETF (HYG/JNK) 의 다음 4주 forward return 과 partial Rank-IC < 0 (음의 신호 = widening 후 HY underperform).
   - 반증: Rank-IC ≥ 0 or e-CUSUM 단측 붕괴.

**H3-C**: HY OAS spike 와 long Treasury (TLT) 의 *카운터-사이클* 관계 — HY OAS Z↑ 시점에서 TLT 1주 forward return 의 Rank-IC > 0 (flight-to-quality).
   - 반증: Rank-IC ≤ 0 in shock window subset.

**H3-D**: 3-signal combined warning (HY OAS Z + 10Y2Y level + VIX Z) 가 단일 HY OAS 보다 침체 lead-time 분포의 IQR 좁다.
   - 반증: combined warning 의 lead time IQR ≥ HY OAS 단독 IQR (= 조합이 noise 만 늘림).

## 검증 방향 초안 (라운드 3)
- BAMLH0A0HYM2 1996~2024 + NBER recession dates → 600bps event study (12-18M forward return panel)
- HY OAS Z-score (own_history_z) × HYG/JNK 일별가 → 1~4주 forward Rank-IC time-series
- TLT vs HYG cointegration / regime-conditional correlation (R3 partial-corr 후속)

## Gap / 라운드 5 로 넘길 질문
1. **검증 방법론** — 자세한 Rank-IC + e-process 가 채권에 어떻게 적용되나 (R4 결과 보강 필요)
2. **VIX collector_plan 추가** 의사결정 — 단일 HY OAS vs 3-signal 합성
3. cash sleeve optionality 정량화 + 한국 KTB 특수성 (R5)
