---
tags: [type/raw, domain/inv, asset/bond, asset/cash, phase/study, round/5]
date: 2026-05-30
round: 5
topic: Cash sleeve optionality + 한국 KTB + Fed spillover
source: WebSearch (native fallback)
---

# Round 5 — Cash optionality / KTB / Fed spillover

## 검색어 (2건)
- `cash treasury bill optionality portfolio defensive stagflation rate cut Sharpe`
- `Korean treasury bond KTB Bank of Korea Fed rate spillover spread emerging market`

## 원천 (URL hyperlink)

### Cash / T-Bill optionality
- [VGSH: Cash-Plus Carry With Rate-Cut Optionality (Seeking Alpha)](https://seekingalpha.com/article/4861713-vgsh-cash-plus-carry-with-rate-cut-optionality)
- [Investing During Stagflation (Thrivent)](https://www.thrivent.com/insights/investing/investing-during-stagflation-strategies-for-portfolio-protection)
- [Sharpe ratios in term structure models — Duffee (JHU)](http://www.econ2.jhu.edu/people/Duffee/duffeeSharpe.pdf)
- [Rising T-Bill Supply and Yield Curve Inversion (Ainvest)](https://www.ainvest.com/news/rising-bill-supply-yield-curve-inversion-tactical-shift-fixed-income-portfolios-2507/)
- [Distorted probability operator for dynamic portfolio optimization (PMC9734642)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9734642/)
- [Economic events and the volatility of government bill rates (PMC9581437)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9581437/)
- [Systemic global inflation, equity markets, portfolio implications (arXiv 2111.11022)](https://arxiv.org/pdf/2111.11022)
- [Minimising a portfolio's shortfall probability (arXiv 1602.02192)](https://arxiv.org/pdf/1602.02192)

### KTB / Fed spillover
- [Outlook for KRW and KTB: Fed rate cut should boost the won (ING THINK)](https://think.ing.com/articles/outlook-for-krw-ktb-treasury-bonds-fed-cut-should-boost-won/)
- [Dollar and government bond liquidity: evidence from Korea (BIS Working Paper 1145)](https://www.bis.org/publ/work1145.pdf)
- [Republic of Korea Government Bonds Yield, KTB 1.375% 10dec2029 (Cbonds)](https://cbonds.com/bonds/618783/)
- [Spillover Effects of US Monetary Policy on Emerging Markets (arXiv 2402.07266)](https://arxiv.org/pdf/2402.07266)
- [South Korea holds rates, reveals hawkish split within board (CNBC)](https://www.cnbc.com/amp/2026/05/28/south-korea-holds-rates-reveals-hawkish-split-within-board.html)

## 핵심 정제

### 1) Cash / Short-T-Bill = "rate-cut optionality"
- 단기 T-Bill ETF (VGSH 등) = "Cash-Plus Carry With Rate-Cut Optionality" 라는 표현 자체가 통념화
- "could benefit from price appreciation if employment data deteriorates and the Fed eases policy" → rate cut 시 price appreciation 받는 *옵션 가치*
- 즉 cash 는 단순 "기회비용 최소화"가 아니라 **(carry + 옵션 가치) 결합 자산**

### 2) Short-Tsy Sharpe ≥ stock market Sharpe (놀라운 사실)
- Duffee paper: "bond portfolio containing Treasury bonds with **less than five years to maturity** has a **monthly Sharpe ratio that slightly exceeds** the monthly Sharpe ratio of the stock market"
- → cash + short-Tsy 결합이 risk-adjusted 로 주식 sleeve 와 *경쟁력 있음*
- **검증 대상 핵심**: 우리 backtest 에서 cash floor 5%가 정당화되는 정량 근거

### 3) Stagflation 방어 = TIPS 우위 재확인
- "Treasury Inflation-Protected Securities (TIPS) adjust with inflation, preserving purchasing power, and can work well as part of a **stagflation defense strategy**"
- → Round 2 의 결론 보강. bond sleeve 안에 TIPS 분리 archetype 필요성 강화.

### 4) T-Bill 공급 증가 → curve flattening risk
- "Surging short-term Treasury bill issuance is poised to **flatten the yield curve**, creating risks for traditional bond investors"
- → 정책 sleeve allocation 결정에 T-Bill 발행량 (supply factor) 도 모니터링 대상
- **collector_plan 후보**: FRED 의 T-Bill 발행량 시리즈

### 5) KTB 3-driver (한국 채권 특수성)
- KTB 시장은 "the pace of rate cuts from both the **Fed and the Bank of Korea**, as well as outcomes related to the **WGBI**" 3 driver 가 핵심
- WGBI = World Government Bond Index (FTSE Russell). KTB 편입 여부가 외국인 자금 흐름 좌우
- → **kr sleeve 의 bond 부분은 us bond 와 다른 driver 셋** 가 필요. 단순 us_bond 의 한국 mirror 가 아님.

### 6) Fed spillover 비대칭 (불확실성 동반 시 증폭)
- arXiv 2402.07266: "spillover effects are **significantly amplified** when US monetary policy tightening is accompanied by an **increase in monetary policy uncertainty**"
- → 단순 fed_funds 변동만으론 spillover 측정 부족. **monetary policy uncertainty index** (FRED 시리즈 또는 Baker-Bloom-Davis EPU) 동반 필요.

### 7) Dollar liquidity ↔ KTB
- BIS 1145: 달러 유동성 위축 시 KTB 시장 유동성에 직접 영향. dollar funding stress = KTB sell-off
- → DXY 또는 cross-currency basis swap 이 KTB 모델의 risk 채널.

## 우리 시스템 매핑

| 새로 식별된 driver | 우리 시스템 매핑 | 액션 |
|---|---|---|
| Cash optionality | regime_to_weights `BASE_WEIGHTS[cash]=0.09` floor | confidence_hook[cash_optionality_value] 정량화 (이전 yaml 의 가설 유지) |
| Short-Tsy Sharpe | `weight_falsification.rank_ic` baseline | SHY/BIL forward Sharpe 사전등록 |
| TIPS 분리 | 현재 미모델링 | 블록2 indicators 신규 (`tips_10y` = DFII10 derived) + 블록4 weight_rules `inflation_regime` 트리거 |
| T-Bill 공급 | 현재 부재 | collector_plan: FRED bill supply 시리즈 (`MTSTOTUS` 등) — 약 prior |
| WGBI (KR 한정) | 부재 | KR sleeve 별도 inflows 시리즈 (외국인 KTB 순매수) — 향후 eq_kr 방과 공유 |
| Fed MP uncertainty | 부재 | collector_plan: FRED `USEPUINDXD` (Baker-Bloom-Davis EPU) 또는 `EFFR` volatility |
| Dollar liquidity | macro 방 DXY | 본 방은 *수신*, 별도 추가 없음 |

## 가설 초안 (라운드 5)

**H5-A**: 단기 T-Bill ETF (SHV/BIL) 의 fed_funds 인하 발표 후 5/10/20일 forward return 분포가 양수 분리.
   - 반증: Fed cut events × forward return 평균이 0 가설 기각 못 함.
   - **rate-cut optionality 정량 검증**.

**H5-B**: Cash sleeve (SHY+BIL+SHV 평균) 의 1976-2024 월별 Sharpe > stock sleeve (SP500) 월별 Sharpe.
   - 반증: 검증 기간에서 cash Sharpe ≤ stock Sharpe → 가설 기각 → REGIME_DIRECTION[Overheat][cash]="down" 정당.
   - 확신: bond sleeve 와 별도, cash 의 단일 sleeve 가치 입증.

**H5-C**: Overheat·Stagflation 국면에서 TIP-TLT spread 의 forward 60일 cumulative return > 0 (TIPS outperform 명목채).
   - 반증: 60일 누적 spread ≤ 0 OR 통계적 미유의.

**H5-D**: Fed 인상 + EPU 동반 상승 (compound shock) 시 KTB sleeve return < Fed 인상 단독 시 KTB return.
   - 반증: compound shock 가 단순 인상보다 KTB 에 더 큰 충격이 아닌 경우.

**H5-E**: DXY Z↑ 시점 × KTB ETF (or 외국인 KTB 순매수) forward return 의 Rank-IC < 0.
   - 반증: Rank-IC ≥ 0.
   - (KR sleeve 와 공유. eq_kr 방의 외국인 순매수와 직접 연결.)

## 검증 방향 초안 (라운드 5)
- VGSH / SHV / BIL 일별가 + FOMC 인하 dates → event study
- SHY+BIL ETF 월 수익 + SP500 → rolling 36개월 Sharpe 비교 (Duffee 사실 재현)
- TIP vs TLT spread → Overheat/Stagflation 라벨 conditional return
- KTB ETF (KOSEF 국고채 ETF) + DXY + FEDFUNDS + EPU → multi-factor regression
- 모든 가설은 `score_ic_breakdown_eprocess` 로 anytime-valid 검정 (alpha=0.05)

## Gap / 마무리
1. 가설 H1-A ~ H5-E **총 16개** 가설 누적. R6 추가 불필요 — direction.md 종합 단계.
2. 환각 검증 필요 사항:
   - BAMLH0A0HYM2 1996-12 시작 → FRED 메타데이터 OK (사실)
   - Duffee paper 의 short-Tsy Sharpe 주장 → 원전 url 보유, 인용 가능
   - 평균 lead time 48주/11개월 → 1969~2024 기간 추정, 가용 NBER 사이클 데이터로 우리가 재현 가능
3. R6 자문 (gemini-web/claude-web) 는 채널 경합 우려로 skip → 사용자 메시지의 "1~2R씩" "WebSearch 폴백 허용" 지침 준수. 5R = 3~7R 수렴 범위 안.
