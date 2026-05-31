---
tags: [type/collector-request, study/eq_us, phase/3.5, purpose/main-handoff]
date: 2026-05-31
study_id: eq_us
phase_snapshot: Phase 3 R1+R2 자문 수렴 완료 → 사용자 ★순서정정 (candidate-ledger 후순위, merit 후보 + collector 요청 1순위)
purpose: |
  Phase 3 자문 (Claude R1/R2 + Gemini R1/R2) + eq_us_cyclical/defensive input + eq_kr baseline + M3 findings 에서
  도출된 ★merit 있는 지표 후보 전수 + merit 근거 (자문/이론/실측 anchor) + 필요 collector + 무료 데이터소스 후보.
  사용자 박제 흐름 = main collector 구현 → eq_us study (이론→실데이터→상관·Rank-IC) → 12축 audit (별도 subagent) → yaml 반영.
basis: study-research/eq_us/candidate-ledger.md (Phase 3 후보 집약, 이미 작성) → 본 문서 = ★merit 작업큐 전환 (collector 부재 = 탈락 사유 부적격)
---

# eq_us → main 인수인계: collector 구현 요청 (merit 후보 전수)

> ★사용자 순서정정 박제 (2026-05-31):
> "candidate-ledger 먼저 쓰지 마라. (1순위) merit 있는 후보 지표를 실제 추가하는 study 다시 — collector 없으면 main 이 구현하니 'merit 근거 + 필요 collector + 무료 데이터소스 후보' 를 main 에 먼저 보고. 흐름 = main collector 구현 → study (이론→실데이터→상관·Rank-IC) → 12축 audit (별도 subagent) → yaml 반영. collector 없음/후순위/이연 = 탈락 사유 부적격."
>
> ★기존 ledger 의 [채택/이연/미채택] 카테고리 = 사용자 framing 위배 → 본 문서가 작업큐 SSOT.

---

## ◆ Tier A — 양 채널 자문 1-3순위 합의 (최우선 merit)

### A-1. earnings_revision_breadth (ERB)

- **Merit 근거**:
  - Claude R1 Q2 1순위 + Gemini R1 Q2 1순위 = ★양 채널 1순위 합의
  - "US 에서 가장 문서화·안정적인 cross-sectional alpha" (Claude). monthly IC 0.03-0.06 (Claude tentative), SE ±0.015 (Gemini)
  - 학술 anchor: Chan-Jegadeesh-Lakonishok (1996) JF "Momentum Strategies" + Stickel (1991) The Accounting Review
  - eq_kr 의 "외국인 net buy" 대응물 (미국 = 자국시장 → ERB 가 가장 가까운 지속적 flow-유사 driver)
- **필요 collector**:
  - 종목별 ERB 시계열 (월간 또는 주간): `(상향 추정 수 − 하향 추정 수) / 전체 추정 수`
  - 컨센서스 추정치 PIT (★ retroactive 수정 차단 필수)
- **무료 데이터소스 후보 (우선순위 순)**:
  - **FINNHUB API 무료티어** (`/stock/recommendation` + `/stock/upgrade-downgrade`) — 권장 1순위 (예산 0)
  - SEC EDGAR 8-K (Item 7.01 가이던스) 파싱 — text-mining, 컨센서스 미포함 → ERB 대신 분자 (가이던스 상하향) 만
  - Alpha Vantage (`EARNINGS_ESTIMATES`) — 무료 키 500 calls/day
- **검증 계획**: 이론 (Chan-Jegadeesh-Lakonishok 1996) → 12M revision IC 측정 → FF5+Mom residual intercept NW t-stat → PIT 재추정 (look-ahead artifact ★사용자 실측 #3)

### A-2. total_shareholder_yield (buyback + dividend)

- **Merit 근거**:
  - Claude R1 Q2 2순위 + Gemini R1 Q2 2순위 = ★양 채널 합의
  - 미국 특유 feature (buyback 비중 한국 대비 압도). L/S spread 역사 2-4%/yr, post-2010 t-stat 약화 (decay)
  - 학술 anchor: Boudoukh-Michaely-Richardson-Roberts (2007) JF vol 62 "On the Importance of Measuring Payout Yield" (정정 verify 완료)
  - Claude R2 QR2-4: fundamental cash-return 기반 → 순수 statistical anomaly 대비 decay 완만 예상
- **필요 collector**:
  - 종목별 분기 자사주 매입 (10-Q cash flow statement: "repurchase of common stock")
  - 종목별 분기 배당 (10-Q cash flow statement: "dividends paid")
  - 시가총액 시계열
  - shareholder_yield = (buyback + dividend) / market_cap (TTM)
- **무료 데이터소스 후보**:
  - **SEC EDGAR XBRL** (Financial Statement Datasets, 무료) — 권장 1순위
  - SEC EDGAR submissions API + 10-Q full-text 파싱 — 권장 2순위 (XBRL 누락 case fallback)
  - yfinance `quarterly_cashflow` — 권장 3순위 (PIT 보장 X → cross-check 용도만)
- **검증 계획**: 이론 (Boudoukh 2007) → L/S decile spread → FF5+QMJ residual → real-rate regime conditional (Claude H2)

### A-3. HY_OAS regime (BAMLH0A0HYM2)

- **Merit 근거**:
  - Claude R1 Q2 3순위 (regime conditioner) + Gemini R1 Q9 H3 = ★양 채널 합의
  - "신용 spread 가 주식 선행 — risk-on/off·cyclical-defensive rotation 최강 분류기" (Claude)
  - ★defensive H3 실측 REVERSED (Credit Stress -1.5%/월 sleeve excess, n=9 small-N) → 자문 prior 와 반대 → ★재검증 필수
  - cyclical credit_beta H4 PARTIAL (VIX 흡수 partial=-0.025)
- **필요 collector**:
  - HY OAS 일별 (BAMLH0A0HYM2, FRED) — 무료 가용, 단 2023-05-30 시작 (★cyclical 박제: cosd 적용해도 짧음)
  - IG OAS 일별 (BAMLC0A0CM, FRED) — 무료 가용
  - 빈자판 BAA10Y-AAA10Y 일별 (FRED) — 1986+ 풀시계열, OAS 대체 prior
- **무료 데이터소스 후보**:
  - **FRED API** (BAMLH0A0HYM2, BAMLC0A0CM, BAA10Y, AAA10Y) — 권장 1순위
  - ALFRED vintage (FRED) — look-ahead 회피 PIT
- **검증 계획**: regime 분류 (OAS > 75th percentile = Credit Stress) → sleeve excess return + LOO + Block Bootstrap autocorr 보정 (n=9 small-N latch) → e-CUSUM monitor

### A-4. real_rate (DFII10) — sub-sleeve sign-split

- **Merit 근거**:
  - Claude R1 Q3 + Q9 H5 (sub-sleeve mechanical) + Gemini R1 Q3 (구조적) = ★양 채널 합의
  - ★defensive H1 실측 anchor: 일별 ΔDFII10 partial IC|SPY: XLU=-0.167 / XLF=+0.129 / XLP=-0.040 (n=5844 일, p<0.0001) — ★단 합성 의심 P0 재검증 의무
  - 학술: Ilmanen (2011) Expected Returns Ch14 "Defensive Equity" bond proxy + Boyd-Gertler-Bernanke (1994) NIM
- **필요 collector**:
  - DFII10 일별 (FRED, 무료 가용) — 권장 1순위
  - DGS10 일별 (FRED) — nominal rate
  - T10YIE (FRED) — breakeven inflation
- **무료 데이터소스 후보**: **FRED API** (DFII10, DGS10, T10YIE) — 100% 가용
- **검증 계획**: P0 재검증 (eq_us_defensive H1 실측 재실행, MAIN-DISPATCH §1 의무) → industry granularity sign-split + name_specific shrinkage → rolling 60D sign-flip rate (≤25% → 안정)

### A-5. dollar (DTWEXBGS) — ρ-conditional regime switch

- **Merit 근거**:
  - Claude R2 QR2-1 절충 (3 메커니즘: 다국적 translation 구조 + commodity 구조 + global risk artifact) + Gemini R2 QR2-1 입장 수정 (구조 + 표본 혼재) = ★양 채널 절충 합의
  - cyclical M3 실측: β_dxy −0.58~−1.62 dominant (epoch R²=0.21 E1), defensive M3 실측: rate-up E3 +0.21~+0.66 / rate-down E4 −0.01~−0.18 부호 반전
  - 학술: Bruno-Shin (2015) ReStud (★Claude R2 메커니즘 약화 — US sector cross-section 1:1 전이 학술 실증 약)
- **필요 collector**:
  - DTWEXBGS 일별 (FRED, 무료 가용)
  - rolling 252d ρ(Δrate, Δdollar) 계산
  - 2-cell regime (low-ρ < 0.3 / high-ρ ≥ 0.3) 분기
- **무료 데이터소스 후보**: **FRED API** (DTWEXBGS, DGS10) — 100% 가용
- **검증 계획**: ★사용자 실측 #1 (2015-2019 sub-sample β_dxy 회귀) → ρ<0.3 구간 |β|≥0.3 + 유의 → 구조설 채택 / |β|<0.2 → artifact 설 채택 → high-ρ cell 직교화 (residual after rate regression) 구현

---

## ◆ Tier B — 구조 결정 (PCA macro-sleeve + Mag7 + Reflexivity Monitor)

### B-1. 11-ETF PCA eigenvalue (raw + market-residual)

- **Merit 근거**:
  - Claude R1 Q9 H8 + Claude R2 QR2-3 + Gemini R2 QR2-3 = ★양 채널 합의 (80% 분산 4-6 PC)
  - ★사용자 실측 #2 (양 채널 권고): Tier 11 GICS 독립 vs macro-sleeve 결정자
  - 학술: Fama-French (1997) JFE industry-level 추정 부정확 시사
- **필요 collector**:
  - 11 SPDR ETF 일별 가격 (XLK/XLC/XLY/XLI/XLB/XLE/XLF/XLV/XLP/XLU/XLRE)
  - SPY 일별 가격 (market residualize 용)
  - PCA eigenvalue table (raw + market-residual 양쪽)
- **무료 데이터소스 후보**:
  - **yfinance** (11 SPDR + SPY) — 권장 1순위 (단 PIT/survivorship 보장 X → 분석 한정, backtest 시 Sharadar 필요)
  - Yahoo Finance 직접 CSV (yfinance 우회) — 백업
- **검증 계획**: 이론 (Fama-French 1997) → sklearn PCA (raw + residual 양쪽) → 80% 분산 PC 수 측정 → ≥7 PC 시 Tier 11 채택 / ≤5 PC 시 macro-sleeve 채택 (★예상)

### B-2. Mag7-EW − S&P493-EW spread (concentration factor)

- **Merit 근거**:
  - Claude R2 QR2-2 (regime indicator 활용 권고, priced factor 약 collinear) + Gemini R2 (priced factor 대안 2 + toraniko characteristic 추가)
  - ★role disagree: Claude=regime indicator / Gemini=priced factor → ★사용자 framing 사항
  - Claude R1 Q5: "Mag7 dominance 시 회귀의 'tech beta' 는 사실 Mag7 idiosyncratic 가장무도회"
- **필요 collector**:
  - Mag7 7 종목 일별 가격 (AAPL/MSFT/NVDA/GOOGL/META/AMZN/TSLA)
  - S&P 500 구성종목 일별 가격 + EW/CW 시가총액 매트릭스
  - Mag7-EW basket return + S&P493-EW basket return (월간/분기)
- **무료 데이터소스 후보**:
  - **yfinance** (Mag7 + S&P 500 holdings) — 권장 1순위
  - SPDR ETF holdings (RSP 동등가중 / SPY 시가가중) 월간 CSV — 보조
  - Wikipedia S&P 500 구성종목 + GICS 분류 — 권장 보조
- **검증 계획**: spread 시계열 + 20d Z-score → regime indicator vs priced factor 검정 (FF5 residual IC) → Mag7 custom basket sleeve 정의 input

### B-3. Reflexivity Monitor (intra-Mag7 corr + breadth)

- **Merit 근거**:
  - Claude R2 QR2-2 spec (corr > 0.70-0.75 AND EW-CW spread < −3~−5%p **동시**) + Gemini R2 (corr > 0.65 AND breadth 하위 10% 동시) = ★양 채널 spec 합의
  - 학술: Daniel-Moskowitz (2016) JFE "Momentum Crashes" — crowded momentum 좌비대칭 tail
  - 2024-08-05 VIX 장중 ~65 (엔 캐리 mini-crash) anchor
- **필요 collector**:
  - intra-Mag7 60d rolling mean pairwise corr (B-2 데이터 재활용)
  - S&P500 EW (RSP) vs CW (SPY) 3m return spread
  - %>200dma breadth (S&P 500 구성종목 200d MA 위 비율)
  - VIX 일별 (FRED VIXCLS, 무료 가용)
- **무료 데이터소스 후보**:
  - **yfinance** (Mag7 7개 + RSP + SPY + S&P 500 구성종목 200d) — 권장 1순위
  - **FRED API** (VIXCLS) — 보조
- **검증 계획**: monitor flag 발효 시 후속 3-6m Mag7 drawdown 측정 → 비-flag 구간 대비 유의 차 (Welch t-test + Block Bootstrap) → monitor 무효 시 cap-up 재검토

### B-4. yield_curve_slope_beta (XLF NIM)

- **Merit 근거**:
  - Gemini R1 Q9 H3 인접 + Claude R1 Q9 H5 인접
  - ★defensive H2 실측 anchor: 월별 Δ(DGS10-DGS2) → XLF excess contemporaneous IC=+0.171, p=0.002, n=317 월 (★단 Stigum 3-6M lag 미관측 — 시장 효율성)
  - 학술: Boyd-Gertler-Bernanke (1994), Stigum's Money Market (2007), Estrella-Mishkin (1998) 침체 선행
- **필요 collector**:
  - DGS10 일별 (FRED, 무료) — 가용
  - DGS2 일별 (FRED, 무료) — 가용
  - slope = DGS10 - DGS2 일별
  - cyclical block6 의 yield_curve_10y_2y 와 동일 — 재사용 가능
- **무료 데이터소스 후보**: **FRED API** (DGS10, DGS2) — 100% 가용
- **검증 계획**: contemporaneous IC + lagged 3-6M IC (Stigum 가설 재검증) → industry granularity (banks 한정 마스크)

### B-5. VIX_beta

- **Merit 근거**:
  - Claude R1 Q10 risk-off 채널 + cyclical H4 실측 (동시 IC=−0.378 가장 강한 risk 공통원인)
  - cyclical block5 박제: VIX 가 credit_beta 흡수 (partial=-0.025) — risk-off 동시 채널
- **필요 collector**:
  - VIXCLS 일별 (FRED, 무료 가용)
  - 종목별 VIX-beta 252d rolling
- **무료 데이터소스 후보**: **FRED API** (VIXCLS) — 100% 가용
- **검증 계획**: cyclical 재사용 (base 0.18) + defensive 추가 검증 (regime contemp IC e-CUSUM)

---

## ◆ Tier C — 가설 검증 인프라 (무료 가용)

### C-1. EDGAR filing acceptance timestamp PIT

- **Merit 근거**:
  - Claude R1 Q7 정확 사실: Large accelerated filer 10-K 60d/10-Q 40d / Non-accelerated 90d/45d (★사용자 45/90 = Non-acc case 만 정확)
  - ★실무 robust PIT rule = 실 EDGAR filing acceptance timestamp 사용 (가정 불필요)
- **필요 collector**:
  - SEC EDGAR submissions API (CIK 별 filing date + form type)
  - filer accelerated grade (Large/Accelerated/Non-accelerated)
- **무료 데이터소스 후보**:
  - **SEC EDGAR submissions API** (`/submissions/CIK{cik}.json`, 무료) — 권장 1순위
  - SEC EDGAR full-text search API — 보조
- **검증 계획**: 모든 펀더멘털 지표 (fwd_ep, shareholder_yield, ROE) lag = filing timestamp 기준 → PIT 무결성 확보

### C-2. Ken French FF5+Mom+QMJ+BAB residual intercept

- **Merit 근거**:
  - Claude R1 Q8 + Gemini R1 Q8 = ★양 채널 합의: 모든 sleeve alpha = factor regression intercept (NW-HAC SE, CPCV)
  - 학술: Fama-French (2015) JFE FF5, Asness-Frazzini-Pedersen (2019) RAS QMJ (정정 verify), Frazzini-Pedersen (2014) JFE BAB
- **필요 collector**:
  - Ken French Daily FF5 (Mkt-RF, SMB, HML, RMW, CMA, Mom)
  - QMJ daily/monthly (AQR Capital Management public datasets)
  - BAB daily/monthly (AQR public datasets)
- **무료 데이터소스 후보**:
  - **Ken French Data Library** (Dartmouth Tuck, 무료 CSV) — 권장 1순위
  - **AQR Datasets** (qmj-monthly, bab-monthly, 무료 CSV) — 권장 2순위
  - pandas-datareader `FamaFrench` reader — 보조
- **검증 계획**: 모든 sleeve alpha = time-series 회귀 intercept + NW-HAC SE → 진짜 alpha 분리

### C-3. FOMC dot plot vs OIS surprise (H7)

- **Merit 근거**:
  - Claude R1 Q9 H7: duration-sorted event-study CAR
  - 학술: Bernanke-Kuttner (2005) JF (FOMC surprise effect on stock returns)
- **필요 collector**:
  - FOMC 회의 일정 + dot plot 발표일 (분기)
  - OIS forward curve (1M, 3M, 6M, 12M) FOMC 직전 종가
  - surprise = OIS 직전 implied path − FOMC dot median
- **무료 데이터소스 후보**:
  - **CME FedWatch Tool** (FOMC implied path, 무료 public API 또는 scraping)
  - **FRED** (FEDFUNDS, DFEDTAR, DFEDTARU, DFEDTARL) — 보조
  - Fed 공식 사이트 (FOMC 일정 + Summary of Economic Projections)
- **검증 계획**: 이벤트 윈도우 CAR (FOMC ±5 day) + duration sort + e-value (목표 >1.5) → monotonic 검증

### C-4. CPCV + NW-HAC + Block Bootstrap + Deflated Sharpe + BH FDR + E-value

- **Merit 근거**:
  - Claude R1 Q8 + Gemini R1 Q8 = ★양 채널 합의 모듈군 (cyclical block7 박제 미작성)
  - 학술: López de Prado (2018) AFML CPCV, Newey-West (1987), Politis-Romano stationary bootstrap, Bailey-López de Prado (2014) deflated Sharpe, Benjamini-Hochberg (1995) FDR, VanderWeele-Ding (2017) E-value
- **필요 collector**:
  - 검증 모듈 (코드, 데이터 X) — main 구현 사항
- **무료 데이터소스 후보**: N/A (코드 모듈)
  - **skfolio** (CombinatorialPurgedKFold, 무료 OSS)
  - **statsmodels** (NW HAC)
  - **arch** 또는 자체 구현 (Politis-Romano)
  - **scipy.stats** (BH FDR)
  - 자체 구현 (Deflated Sharpe + E-value)
- **검증 계획**: cyclical block7 미작성 모듈 통합 구현 → eq_us validation pipeline 동시 사용

### C-5. 11-K Geographic Segment (foreign revenue ratio)

- **Merit 근거**:
  - Claude R2 QR2-1 절충: 다국적 대형주 foreign-revenue translation = dollar 채널 구조 메커니즘
  - eq_us_defensive direction §1.1 (Bernstein/Barclays CPG, 10-K Geographic Segment): KO/PG/PEP/PM 신흥시장 매출 高 → DXY 환차손 직접 노출
- **필요 collector**:
  - 종목별 10-K Geographic Segment (foreign revenue / total revenue)
  - 연도별 vintage (annual report)
- **무료 데이터소스 후보**:
  - **SEC EDGAR 10-K XBRL** (us-gaap:Revenues + dei:LegalEntityCountry) — 권장 1순위
  - SEC EDGAR 10-K full-text 파싱 (Geographic Segment 표) — 보조
- **검증 계획**: foreign_rev_ratio × DXY 회귀 → 다국적 multinational 종목 부호 (Claude 채널 mechanism #1 확인)

### C-6. Damodaran implied ERP (월별 vintage)

- **Merit 근거**:
  - cyclical block6 P1 박제 (NYU Stern 데이터 페이지). Damodaran > historical 5%
  - Damodaran NYU Stern Sector-Specific Valuation 학술 standard
- **필요 collector**:
  - implied ERP 월별 (NYU Stern 데이터 페이지 CSV)
  - vintage 컬럼 (look-ahead 회피)
- **무료 데이터소스 후보**:
  - **NYU Stern Damodaran 데이터 페이지** (`https://pages.stern.nyu.edu/~adamodar/New_Home_Page/dataarchived.html`, 무료 월간 CSV) — 권장 1순위
- **검증 계획**: fair_mult Band Monte Carlo 분모 floor + sector-specific COE 계산 input

### C-7. Damodaran bottom-up beta (산업 무차입 → D/E relever)

- **Merit 근거**:
  - cyclical block7 박제 미작성: Damodaran > 회귀 베타 (top-down regression noisy)
- **필요 collector**:
  - 산업별 unlevered beta (Damodaran 분기 업데이트)
  - 종목별 D/E ratio (10-K) → relever
- **무료 데이터소스 후보**:
  - **NYU Stern Damodaran 데이터 페이지** (`Levered and Unlevered Betas by Industry`, 무료) — 권장 1순위
  - SEC EDGAR 10-K XBRL D/E ratio — 보조
- **검증 계획**: bottom-up beta vs 회귀 beta IC 비교 → fair_mult 분모 정확화

---

## ◆ Tier D — eq_us 특화 + cyclical/defensive 재사용 (무료 가용)

### D-1. WTI oil beta (XLE 분리 트랙)

- **Merit 근거**:
  - cyclical 실측: XLE rank-IC +0.602 압도 (별도 채널)
  - Claude R1 Q4: Energy sub-sleeve 별도 (commodity exposure)
- **필요 collector**:
  - WTI 일별 (FRED WTISPLC, 무료 가용)
  - 종목별 WTI-beta 252d rolling
- **무료 데이터소스 후보**: **FRED API** (WTISPLC) — 100% 가용
- **검증 계획**: cyclical 재사용

### D-2. T10YIE breakeven inflation

- **Merit 근거**:
  - eq_us_defensive Q3 mechanism: real rate = nominal − breakeven → breakeven 변동이 real rate sign-split 의 confound
  - cyclical block6 P1 (FRED 가용)
- **필요 collector**: T10YIE 일별 (FRED, 무료 가용)
- **무료 데이터소스 후보**: **FRED API** (T10YIE) — 100% 가용
- **검증 계획**: real rate 부호 안정성 conditioning 변수

### D-3. UNRATE (실업률)

- **Merit 근거**: 경기 사이클 macro driver, Investment Clock anchor
- **필요 collector**: UNRATE 월별 (FRED, 무료 가용) + ALFRED vintage (release-date PIT)
- **무료 데이터소스 후보**: **FRED API** (UNRATE) + **ALFRED** vintage — 100% 가용
- **검증 계획**: regime 분류 input + macro driver 채택

### D-4. EDGAR Y-9C 은행 특화 (NIM/NPL/CET1)

- **Merit 근거**:
  - eq_us_defensive Q1: 은행 = 잔여이익 모델 RIM 핵심 input
  - block6 #5~#8 (EDGAR 은행 파싱 — sub-sleeve 신호 활성화 prerequisite)
- **필요 collector**:
  - 은행지주회사 FR Y-9C 파일 (분기, 무료)
  - NIM = Net Interest Income / Interest Earning Assets
  - NPL = Non-Performing Loans / Total Loans
  - CET1 = Common Equity Tier 1 capital ratio
- **무료 데이터소스 후보**:
  - **Federal Reserve National Information Center (NIC)** (FR Y-9C XBRL, 무료) — 권장 1순위
  - **FDIC Call Reports** (분기, 무료) — 권장 2순위
- **검증 계획**: bank archetype lens 정성필드 + sub-sleeve NIM 신호

### D-5. CMS Medicare 약가 정책 이벤트 캘린더

- **Merit 근거**:
  - eq_us_defensive §1.1: Kaiser Family Foundation IRA Prescription Drug Provisions → pharma multiple 디레이팅
  - Claude R1 Q4: XLV sub (pharma 정책 idiosyncratic)
- **필요 collector**:
  - CMS Medicare 협상 약물 리스트 (분기, 무료)
  - IRA 이정표 (2024 negotiation, 2026 effective)
- **무료 데이터소스 후보**:
  - **CMS.gov** (Medicare Drug Price Negotiation Program 페이지) — 권장 1순위
  - **Kaiser Family Foundation** (KFF Health Policy 페이지) — 보조
- **검증 계획**: 이벤트 dummy + 펑요일 ±5 day CAR (pharma sub-sleeve)

### D-6. cyclical 17 indicators 재사용 (eq_us 통합)

| cyclical 지표 id | family | 무료 데이터소스 | 비고 |
|---|---|---|---|
| **fwd_ep_normalized** (Damodaran) | valuation | SEC EDGAR XBRL (EPS) + 가격 | C-1 + C-6 합치 |
| **roe_margin_trend** | quality | SEC EDGAR XBRL (ROE, gross_margin) | C-1 합치 |
| **fwd_eps_momentum** | revision | SEC EDGAR XBRL (EPS 변화율) | C-1 합치 |
| **dollar_beta** | macro_sens | FRED DTWEXBGS | A-5 합치 |
| **oil_beta** | macro_sens | FRED WTISPLC | D-1 합치 |
| **credit_beta** | macro_sens | FRED BAMLH0A0HYM2 | A-3 합치 |
| **ism_pmi_proxy** | macro_driver | FRED NAPMPI 또는 NAPM | cyclical H3 REJECT 종속 재정의 대기 |
| **realized_vol_60d** | risk | yfinance | 100% 가용 |
| **price_mom_12_1** | momentum | yfinance | 100% 가용 |
| **rate_beta** | macro_sens | FRED DFII10 | A-4 합치 |
| **vix_beta** | macro_sens | FRED VIXCLS | B-5 합치 |
| **yield_curve_10y_2y** | macro_driver | FRED DGS10, DGS2 | B-4 합치 |
| **asset_growth_yoy** (CMA) | quality | SEC EDGAR XBRL (total_assets) | C-1 합치 |
| **capex_to_rev** | quality | SEC EDGAR XBRL (capex, revenue) | C-1 합치 |
| **operating_leverage_nm** (Novy-Marx 2011) | quality | SEC EDGAR XBRL (fixed_costs proxy / book_assets) | C-1 합치 |
| **ebp_residual** (GZ TRACE+Merton DD) | macro_driver | ★TRACE 유료 → 대안 Favara FEDS Notes 부록 무료 | Tier E 의사결정 |
| **earnings_revision_breadth** | revision | A-1 합치 | FINNHUB 무료 |

### D-7. defensive 핵심 indicators 재사용 (★P0 재검증 후)

| defensive 지표 id | family | 무료 데이터소스 | P0 재검증 의무 |
|---|---|---|---|
| **dividend_yield** | valuation | SEC EDGAR XBRL (배당) / 가격 | ✅ |
| **dividend_safety** | quality | SEC EDGAR XBRL (FCF/배당 + 부채 + 5Y CV) | ✅ |
| **fcf_yield** | valuation | SEC EDGAR XBRL (FCF / 시가총액) | ✅ |
| **earnings_stability** | quality | SEC EDGAR XBRL (5Y EPS std/mean) | ✅ |
| **nim_trend** | quality | D-4 합치 (Y-9C/Call Reports) | ✅ |
| **pb_ratio** | valuation | SEC EDGAR XBRL (BV) / 가격 | ✅ |

---

## ◆ Tier E — 유료 / 의사결정 필요 (사용자 framing 사항)

### E-1. Sharadar Core US (survivorship-free 가격)

- **Merit 근거**: Claude R1 Q7 + Gemini R1 Q7 = ★양 채널 권장. yfinance 단독 = backtest 1.5-3.0%/yr 과대
- **비용**: $50/월 (개인 라이선스)
- **무료 대안**:
  - 대형주 (S&P 500) 한정 yfinance + bias 명시 (Gemini R1 후속 질의 우회) — ★사용자 직접 답 필요
  - CRSP via WRDS (학술 라이선스, 직장/학교 필요)
- **의사결정**: 예산 대 alpha 정확도 trade-off (사용자 framing)

### E-2. Norgate Data (편출입 PIT)

- **Merit 근거**: Claude R1 Q7 보조 권장 (완벽 편출입 PIT)
- **비용**: $1000+/yr
- **무료 대안**: Sharadar 우선 (저렴)

### E-3. I/B/E/S consensus (Refinitiv)

- **Merit 근거**: Claude R1 Q2 (revision breadth 표준 source)
- **비용**: 매우 비쌈 (기관 라이선스)
- **무료 대안**:
  - **FINNHUB API 무료티어** — A-1 권장 1순위
  - Alpha Vantage — 보조
- **의사결정**: FINNHUB 무료티어로 시도 → 부족 시 재논의

### E-4. CBOE 0DTE volume

- **Merit 근거**: Gemini R1 Q10 H11 신규 confound
- **비용**: 구독
- **무료 대안**: CBOE Market Insights 월간 리포트 (집계치만, raw X) — 후순위

### E-5. GZ EBP TRACE (cyclical block6 P2)

- **Merit 근거**: cyclical 빈자판 BAA10Y-AAA10Y 대체
- **비용**: TRACE 유료
- **무료 대안**: Favara FEDS Notes 부록 (월별 EBP 시계열, 무료 CSV) — ★cyclical 박제

---

## ◆ 사용자 실측 권고 3건 (Phase 5 산업 subagent 작업 의무)

| # | 실측 | 필요 데이터 | 판정 기준 | Tier |
|---|---|---|---|---|
| **#1** | 2015-2019 β_dxy sub-sample 회귀 | FRED DXY + yfinance 11-ETF | ρ<0.3 구간 \|β\| ≥0.3 + 유의 → 구조설 / \|β\|<0.2 → artifact | A-5 |
| **#2** | 11-ETF PCA (raw + market-residual) | yfinance 11 SPDR + SPY | 80% 분산 ≥7 PC → Tier 11 / ≤5 PC → macro-sleeve | B-1 |
| **#3** | PIT revision IC vs backfilled IC | EDGAR + FINNHUB | PIT IC < backfilled × 0.7 → look-ahead artifact 확정 | A-1 |

---

## ◆ defensive v2 yaml P0 재검증 (MAIN-DISPATCH §1 박제 의무)

| 가설 | 현 상태 | 재검증 의무 |
|---|---|---|
| **H1 Real Rate Dichotomy** (XLU −0.167 / XLF +0.129, n=5844) | ★합성 의심 | 실데이터 재실행 (FRED DFII10 + yfinance) |
| **H2 Yield Curve 3-6M NIM lag** REJECTED → contemp IC +0.171 | ★합성 의심 | 실데이터 재실행 (FRED DGS10-DGS2 + 월별 XLF excess) |
| **H3 HY OAS REVERSED** (-1.5%/월, n=9 small-N) | ★small-N 단정 위반 | LOO + Block Bootstrap (Politis-Romano) + autocorr 보정 |
| **H4a Credit beta sub-sleeve** (defensive +0.09 / XLF -0.166, n=752) | ★합성 의심 | 실데이터 재실행 (FRED BAMLH0A0HYM2 + yfinance) |
| **M3 Dollar 부호 반전** (E3 +0.21~+0.66 / E4 -0.01~-0.18) | ★합성 의심 | 실데이터 재실행 (FRED DTWEXBGS + cyclical M3 코드 재사용) |

---

## ◆ Phase 흐름 (사용자 박제)

```
1. main collector 구현 (본 문서 Tier A → E 순서)
   ↓
2. eq_us study 재실행:
   (a) 이론 정독 (학술 paper + Damodaran + 자문 R1+R2)
   (b) 실데이터 검증 (collector 적재 후)
   (c) 상관 + Rank-IC (FF5+Mom+QMJ+BAB residual + NW HAC + Block Boot + CPCV)
   ↓
3. 12축 audit (별도 subagent — supervisor 직접 평가 금지, MAIN-DISPATCH §5)
   ↓
4. study_session.yaml 반영 (7블록)
```

---

## ◆ main 보고 우선순위 (collector 구현 순서)

1. **즉시 (FRED 100% 가용)**: A-3 (HY OAS) / A-4 (DFII10) / A-5 (DTWEXBGS) / B-4 (DGS10-DGS2) / B-5 (VIXCLS) / D-1 (WTI) / D-2 (T10YIE) / D-3 (UNRATE)
2. **단기 (yfinance + Wikipedia)**: B-1 (11-ETF PCA) / B-2 (Mag7-EW spread) / B-3 (Reflexivity Monitor breadth)
3. **중기 (FINNHUB 무료티어 + SEC EDGAR XBRL)**: A-1 (ERB) / A-2 (TSY) / C-1 (filing timestamp PIT) / D-6 cyclical 17 재사용 / D-7 defensive 6 재사용
4. **중기 보조 (Ken French + AQR + NYU Stern)**: C-2 (FF5+QMJ+BAB) / C-6 (Damodaran ERP) / C-7 (bottom-up beta)
5. **중기 신규 (NIC + FDIC + CMS)**: D-4 (Y-9C 은행) / D-5 (CMS 약가)
6. **장기 (CME FedWatch + SEC 10-K geo)**: C-3 (FOMC OIS) / C-5 (foreign revenue)
7. **코드 모듈 (data X)**: C-4 (CPCV + NW + Block Boot + Deflated Sharpe + BH + E-value)
8. **사용자 framing**: E-1 (Sharadar 예산) / E-3 (FINNHUB 부족 시 Refinitiv)

---

## ◆ TL;DR — main 인계 한 줄

- **Tier A 5건 (양 채널 1-3순위 합의)** = ERB / TSY / HY OAS / DFII10 sub-sleeve / DXY ρ-conditional → 모두 FRED 또는 FINNHUB 무료 가용
- **Tier B 5건 (구조 결정)** = 11-ETF PCA / Mag7 spread / Reflexivity Monitor / slope_beta / VIX_beta → 모두 FRED+yfinance 무료
- **Tier C 7건 (인프라)** = EDGAR PIT / FF5+QMJ+BAB / FOMC OIS / 검증 모듈군 / Geographic Segment / Damodaran ERP / bottom-up beta → 모두 무료 OSS+공개 데이터
- **Tier D 7+13 (eq_us 특화 + cyclical/defensive 재사용)** = WTI/T10YIE/UNRATE/Y-9C/CMS + cyclical 17 + defensive 6 → 거의 모두 무료
- **Tier E 5 (유료/의사결정)** = Sharadar/Norgate/IBES/CBOE/TRACE → 사용자 framing 사항 (무료 대안 제시)
- **사용자 실측 3** = 2015-2019 β_dxy / 11-ETF PCA / PIT revision IC → Phase 5 subagent 의무
- **defensive v2 P0 재검증** = H1/H2/H3/H4a/M3 합성 의심 → 실데이터 재실행 (n=9 small-N H3 = Block Bootstrap + LOO)

★ main 진행 권고: Tier A + Tier B + Tier D (FRED/yfinance 100% 가용) 우선 구현 → eq_us study 재실행 진입 가능. 그 사이 Tier C (EDGAR XBRL + Ken French) 병렬 구현.

<state intent="merit 후보 전수 식별 + 무료 collector 매핑 + main 인계 문서 작성 (사용자 ★순서정정 반영)" risk="defensive v2 합성 의심 미재검증 시 yaml 박제 부적격" uncertainty="low">
