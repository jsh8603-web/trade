---
tags: [type/consult, domain/inv, asset/bond, asset/cash, phase/study-v2-phase3, round/2]
date: 2026-05-31
round: 2
topic: sub-cluster 학술 baseline (Q1) + MOVE risk parity (Q13) + ACM Kim-Wright cross-verify (Q14 + E축 single source 보완)
source: WebSearch native (R1 동일 폴백)
session: btn-powerbi (handoff §4 main 회신 option A 직후)
channels: 3 query 병렬 batch
---

# Consult Round 2 — sub-cluster + MOVE + ACM cross-verify

## R2 진입 배경
main 회신 (option A) 직후 진행. main 지시:
> "Phase 3 R2 자문은 sub-cluster 분할(Q1-Q6)+MOVE/ACM inject(Q13-Q14)로 진행"

methodology-brief §E R2 query 6건 중 우선순위 3 (학술 anchor + single source 보완 우선).

## Query 1 — sub-cluster 학술 baseline (Q1, methodology-brief §A)

Query: `bond ETF portfolio sub-cluster duration bucket vs credit quality matrix academic literature factor 2024 2025`

### Top 8 sources
- [Morningstar — 4 Top-Performing Corporate Bond Funds](https://www.morningstar.com/funds/4-top-performing-corporate-bond-funds-3)
- [State Street — Q2 bond market outlook for ETF investors](https://www.ssga.com/us/en/intermediary/insights/bond-market-outlook-etf)
- [Vanguard — 4 things to know about bond ETFs](https://advisors.vanguard.com/strategies/fixed-income/4-things-to-know-about-bond-etfs)
- [AInvest — Bond ETFs 2026 Strategic Allocation Framework Quality Yield](https://www.ainvest.com/news/bond-etfs-2026-strategic-allocation-framework-quality-yield-2601/)
- [VanEck — 2025 Corporate Bond Market Trends](https://www.vaneck.com/offshore/en/news-and-insights/blogs/income-investing/corporate-bond-market-trends-and-insights-a-2025-investors-guide/)
- [Morningstar — New Era for Bond ETFs](https://www.morningstar.com/funds/new-era-bond-etfs-what-investors-need-know)
- [Morningstar — Best Bond ETFs](https://www.morningstar.com/funds/best-bond-etfs)
- [ETFDB — IG Corporate ETF List](https://etfdb.com/etfs/bond/investment-grade-corporate/)

### 핵심 정제
- duration × credit quality matrix = Morningstar / Vanguard / State Street / VanEck **practitioner 합의** (industry-norm)
- 2024-2025 강조: **quality factor** (higher rating + shorter duration) — Fed cut 환경 anchor
- 학술 paper 부재 — practitioner-driven 영역

### ★ supervisor 비판 (E축)
- 7 sub-cluster 분할 (tsy_long/mid/short × IG/HY × cash + TIPS) = industry-norm aligned, academic novelty X (학술 정당화 X, practitioner 정당화 ✅)
- 2024-2025 quality factor 강조 → base_weight regime modulator 후보 (Phase 5 검증 시 quality regime 별 alpha test)

## Query 2 — MOVE 사이징 mechanism (Q13)

Query: `MOVE index risk parity vol targeting bond portfolio sizing mechanism academic paper 2024 2025`

### Top 7 sources
- [Eduvest — Bond Portfolio Risk Parity Optimization](https://eduvest.greenvest.co.id/index.php/edv/article/download/51299/4677/31665)
- [Man Group — The Impact of Volatility Targeting](https://www.man.com/insights/the-impact-of-volatility-targeting)
- [ArXiv 2603.01298 — Single-Asset Adaptive Leveraged Vol Control](https://arxiv.org/pdf/2603.01298)
- [SSRN 5165202 — Risk Parity and its Discontents (Sullivan, Wey)](https://papers.ssrn.com/sol3/Delivery.cfm/5165202.pdf?abstractid=5165202&mirid=1)
- [ArXiv 1411.7494 — Evolutionary Optimization Risk Parity](https://arxiv.org/pdf/1411.7494)
- [ArXiv 1311.4057 — Fast Algorithm High-dim Risk Parity](https://arxiv.org/pdf/1311.4057)
- [ArXiv 2203.00148 — Iterative methods Risk Parity](https://arxiv.org/pdf/2203.00148)

### 핵심 정제
- MOVE 와 risk parity 직접 결합 paper = **WebSearch 미노출**
- Ararat et al. 2024: ETF/bond/commodity risk parity 통합 (MOVE 직접 X)
- vol targeting 일반: drawdown 감소 ✅, Sharpe 영향 미미 (bonds/currencies/commodities)
- Sullivan-Wey 2025 SSRN: risk parity vs 60/40 backtest **underperform** (1951~)

### ★ supervisor 비판
- ⚠️ MOVE-direct 학술 single paper 부재 = single-query 한계, SSRN/ArXiv 직접 contact 필요 (R3 query 후보)
- ✅ 본 시스템 = **strict risk parity 아님** (cycle modulator 결합 형태) — Sullivan-Wey underperform 비판 비적용
- **결정**: MOVE 사이징 = (a) 사용자 명시 "사이징 직결" (practitioner heuristic 우선) + (b) Phase 5 실측 (forward Rank-IC × MOVE Z bucket) 결합. 학술 single source 의존 회피, K축 시도횟수 공시.

## Query 3 — Kim-Wright vs ACM cross-verify (Q14 + E축)

Query: `Kim Wright term premium model vs Adrian Crump Moench ACM cross validation difference robustness Treasury`

### Top 8 sources
- [Fed FEDS Notes 2017 — Robustness of long-maturity term premium estimates](https://www.federalreserve.gov/econres/notes/feds-notes/robustness-of-long-maturity-term-premium-estimates-20170403.html)
- [Liberty Street Economics — Treasury Term Premia 1961-Present](https://libertystreeteconomics.newyorkfed.org/2014/05/treasury-term-premia-1961-present/)
- [Fed FEDS Notes 2024-09 — Treasury Tantrum 2023](https://www.federalreserve.gov/econres/notes/feds-notes/the-treasury-tantrum-of-2023-20240903.html)
- [Neuberger Berman — The Term Premium Conundrum](https://www.nb.com/-/media/NB/Article-Assets/u0064_0319_wp_the_term_premium_conundrum.ashx)
- [AOFM — Estimation of term premium Australian Tsy Bonds](https://www.aofm.gov.au/publications/research/estimation-term-premium-within-australian-treasury-bonds)
- [AOFM — Term premium AU detailed](https://www.aofm.gov.au/media/269)
- [ResearchGate — Pricing the Term Structure with Linear Regressions (ACM 원전)](https://www.researchgate.net/publication/5051444_Pricing_the_Term_Structure_with_Linear_Regressions)
- [BIS QR 2018-09 — Term premia models and stylised facts](https://www.bis.org/publ/qtrpdf/r_qt1809h.pdf)

### 핵심 정제
- **Kim-Wright (KW, 2005)** = Don H. Kim + Jonathan H. Wright, 3-factor arbitrage-free term structure model
- **ACM (2013 FRBNY)** = multi-factor affine + linear regression coefficient estimation, fits data extremely well
- ★ "While the structures of these models are very similar, **their long-maturity term premium estimates can nevertheless differ materially at times**"
- Fed produces estimates using both for comparison purposes

### ★ supervisor 비판 (E축 single source 보완)
- ★ **long-maturity material difference** = R1 single source risk 확정 = E축 1-source 위반 risk
- Fed 자체가 둘 다 production = robustness 권장 강함
- **결정**:
  - (a) Phase 5 우선 ACM 단독 채택 (NY Fed xlsx 200 OK 본 세션 curl HEAD 검증)
  - (b) Kim-Wright = cross-check 보조 (FRB H.15 endpoint 또는 SSRN replication, ★R3 query 후보)
  - (c) weight_rules `prior_strength` = ACM·KW 두 추정 중 **보수적 magnitude** + CI 박제 (small-N rigor §1 의무 (c))

## R2 종합 채택/기각

### 채택 (3)
- ✅ 7 sub-cluster 분할 = practitioner industry-norm aligned (Phase 5 진행)
- ✅ 2024-2025 quality factor → base_weight regime modulator 후보 (Phase 5 검증)
- ✅ ACM 단독 + Kim-Wright cross-check 권고 (Phase 5 KW data 별도 확보 의무)

### 기각/보류 (2)
- ⚠️ MOVE-direct risk parity 학술 single paper 부재 — practitioner heuristic + Phase 5 실측 결합 (학술 단일 source 의존 회피)
- ⚠️ Strict risk parity underperform (Sullivan-Wey) — 본 시스템 cycle modulator 결합 형태 비적용 확정

### R3 추가 query 후보 (필요 시)
1. SSRN/ArXiv "MOVE OIS bond vol targeting" specific paper (학술 보강)
2. Kim-Wright data endpoint (FRB H.15 / SSRN replication) — Phase 5 cross-check input
3. ~~BAMLH0A0HYM2 1996-2023 historical 대체~~ → main 회신으로 확정 (BAA10Y 1986~ + NFCI 1971~) — R3 불요

## tries 누적 공시 (K축)
- consult round 누적 = v1 R1~R5 + v2 R1 + v2 R2 (3 query) = **9 round**
- WebSearch native 본 세션 = **5 query** (R1 후속 2 + R2 3)
- WebFetch = 2 (둘 다 403)

## 환각 검증 (E축)
- Kim-Wright 2005 / ACM 2013 FRBNY ✅ (Fed FEDS Notes + Liberty Street 직접 확인)
- Sullivan-Wey 2025 SSRN URL 노출 ✅ (R3 시 abstract direct 검증 가능)
- Ararat 2024 출처 URL = eduvest.greenvest.co.id ⚠️ medium risk, R3 시 정확 paper 추적 (현재 채택 X)

## 다음 액션
- consult-round-2.md (본 파일) commit
- Phase 4-1 fetch script (`raw/_v2_analysis/fetch_p0.py`) 작성 → 실행
- Phase 5 validation md 진입
- main "STUDY DONE" 보고 → main 12축 audit subagent dispatch 대기
