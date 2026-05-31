---
tags: [type/raw, domain/inv, asset/bond, asset/cash, phase/study, round/4]
date: 2026-05-30
round: 4
topic: Yield curve 역전·bond ETF 백테스트·Rank IC 검증법
source: WebSearch (native fallback)
---

# Round 4 — Yield curve 역전 lead time 검증법

## 검색어
`yield curve inversion recession lead time bond ETF backtest Rank IC performance`

## 원천 (URL hyperlink)
- [Inverted Yield Curve Trading Strategy (Backtest) — QuantifiedStrategies](https://www.quantifiedstrategies.com/yield-inversion-trading-strategy/)
- [Yield Curve Inversion 2025: Recession Risk Analysis (YCharts)](https://get.ycharts.com/resources/blog/yield-curve-inversion-2025/)
- [Inverted Yield Curve: Is it Still a Recession Indicator? (U.S. News)](https://money.usnews.com/investing/articles/inverted-yield-curve-is-it-still-a-recession-indicator)
- [Treasury Yields Snapshot 2026-02-20 (Advisor Perspectives)](https://www.advisorperspectives.com/dshort/updates/2026/02/20/treasury-yields-snapshot-february-20-2026)
- [Treasury Yields Snapshot 2025-11-21 (Advisor Perspectives)](https://www.advisorperspectives.com/dshort/updates/2025/11/21/treasury-yields-snapshot-november-21-2025)
- [Yield Curve Inversion (Fisher Investments)](https://www.fisherinvestments.com/en-us/insights/personal-wealth-management/yield-curve-inversion)
- [Inverted Yield Curve Explained (YCharts)](https://get.ycharts.com/resources/blog/inverted-yield-curve-what-it-means-and-how-to-navigate-it/)
- [Yield Curve Valuation Model (Current Market Valuation)](https://www.currentmarketvaluation.com/models/yield-curve.php)
- [Current US Yield Curve Today (GuruFocus)](https://www.gurufocus.com/yield_curve.php)

## 핵심 정제

### 1) 역전 → 침체 lead time 분포
- "average lead time from the first negative spread date to a recession is approximately **48 weeks**, or about **eleven months**"
- "Since World War II, every yield curve inversion has been followed by a recession in the following **6-18 months**"
- 즉 분포 평균 ≈11개월, IQR 6-18개월. **48주 = baseline lag** 로 활용.

### 2) 신뢰성 limit
- "the relationship is not mechanical, as inversions are not precise timing tools and do not always precede recessions in a consistent way"
- → false signal 도 발생 가능. e-process 의 anytime-valid 검정으로 적합.

### 3) Bond ETF 거동 (역전 해소 = bull steepening 사례)
- 2007-2009 recession: "rate cuts or expected rate cuts triggered a surge in longer-term bond prices in the **iShares 10-20 Year Treasury Bond ETF (TLH)**, leading to a decline in yields and a normalization of the yield curve during a '**bull steepening**' event"
- → 침체 진입 후 → CB 가 인하 → long-duration 강세 → curve normalize. **TLT/TLH 매수 timing = 역전 해소 시작 시점**.

### 4) 누락 (Rank IC 직접 자료 없음)
- 채권 strategy Rank IC 직접 비교 자료는 검색 결과에 없음.
- → 우리 시스템의 `weight_falsification.rank_ic` + `score_ic_breakdown_eprocess` 를 채권에 적용 시, **baseline_ic 사전등록** 이 핵심 (논문 사례 부재 → 자체 historical 로 calibration).

## 우리 시스템 매핑

| 검증 항목 | 우리 코드 | 사용 방법 |
|---|---|---|
| 역전→침체 lead time 분포 | `weight_falsification.score_ic_breakdown_eprocess` | curve flip event 후 12-18M forward sleeve return 의 Rank-IC e-process |
| Bull steepening event | `update_controller.step` (TRANSITION 분기) | curve flip 검출 → bond 카드 TRANSITION |
| False signal (lag instability) | `rank_ic` (PIT 윈도별) | regime label 오분류 시 rank_ic 음반전 |

## 가설 초안 (라운드 4)

**H4-A**: 10Y-2Y curve flip event (역전 진입 vs 역전 해소) 의 forward 12M bond sleeve return 의 Rank-IC > 0.
   - 반증: e-CUSUM 단측 붕괴 (baseline_ic 미달) OR sign reversal.
   - **baseline_ic**: 1976-2024 NBER 침체 8회 + 역전 사건 ~9건 → 80%ile lead time = 11~12개월 검증.

**H4-B**: Bull steepening 진입 시점 (curve flip back to positive) 의 forward 6M long Treasury (TLT) return 의 Rank-IC > IEF (mid-duration) Rank-IC.
   - 즉 long 이 mid 보다 *더 큰* 신호. 듀레이션 beta 의 nonlinearity.
   - 반증: TLT Rank-IC ≤ IEF Rank-IC OR 둘 다 0.

**H4-C**: Curve flip 신호의 *false-positive* 율은 5% 미만 (anytime-valid Ville bound).
   - 반증: 1996-2024 backtest 에서 false-flip 사건 (역전 후 침체 없음) > 5%.
   - 1995, 1998 사례 = 역전 후 침체 *지연*된 case study 가능.

**H4-D**: Rate-cut 시작 시점 (Fed funds 인하 발표) 이 curve flip 보다 *나중* 발생 — long-duration ETF rally 의 트리거.
   - 반증: Fed funds 인하 < curve flip 시점이면 가설 반전.

## 검증 방향 초안 (라운드 4)
- T10Y2Y 일별 시계열 → 부호 flip event 추출 → forward 6/12/18 month panel
- TLT/IEF/SHY 일별가 → Rank-IC sliding window
- FOMC dates 와 curve flip 의 시간차 측정

## Gap / 라운드 5 로 넘길 질문
1. **cash sleeve optionality** 정량화 (R5)
2. **한국 KTB** 와 미국 채권의 spillover (R5)
3. **엔캐리 채널**: BOJ vs Fed 금리차 (이전 라운드 미커버)
