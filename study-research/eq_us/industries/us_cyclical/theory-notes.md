---
tags: [type/theory-notes, domain/equity, sector/us_cyclical, status/active]
date: 2026-06-03
purpose: S1 학술 ground — us_cyclical(반도체/소재/산업재/에너지/금융) cross-sectional alpha·regime 지표의 1차 문헌 근거. 자문 복붙 아님, Gemini 2-Phase 리서치 + citation 환각검증 + EDGAR concept 가용성 실측.
sources: Gemini Pro 2-Phase (archive: ~/.claude/docs/archive/research-raw/us-cyclical-*-20260603.txt) + citation 교차검증 + EDGAR XBRL 실측
---

# us_cyclical 이론 노트 (S1 학술 ground)

> ★핵심 framing: cyclical sector 의 본질 문제 = **earnings cycle 진폭** (peak-EPS trap). 사이클 정점에서 EPS 高 → P/E 낮아 보임 → 함정. 트로프에선 EPS≈0/음수 → P/E 무용. → ★peak-EPS-robust 신호 (balance-sheet 기반 / sales 기반 / forward expectation) 가 핵심. 기존 per_z/pbr_z/vol/mom 은 일부일 뿐.

## 1. peak-EPS-robust valuation·quality 신호 (S1 핵심 발굴)

### 1.1 Asset Growth / Investment factor ★최우선 신규
- **정의**: AG_t = Assets_t / Assets_{t-1} − 1 (총자산 YoY 성장). cross-sectional rank, **음 sign** (저성장 → forward 수익↑).
- **메커니즘 (cyclical 특화)**: cyclical 산업 = boom-bust capex cycle. 정점에서 현금·낙관 과잉 → 과잉투자 → 신규 capacity 가 수요 둔화기에 가동 → 공급과잉·가격전쟁·수익성 붕괴. 高 asset growth = 강한 음의 forward 예측. ★peak-EPS 를 *유발하는* capital cycle 을 직접 포착 → balance-sheet 기반이라 peak-EPS 면역.
- **citation**: Cooper, Gulen, Schill (2008) *Journal of Finance* 63(4) "Asset Growth and the Cross-Section of Stock Returns" (★환각검증 CONFIRMED). long-short top/bottom decile 월 1~1.5% (논문 표본). capital-intensive·investment-flexibility 高 산업에서 최강.
- **decay 경고**: McLean-Pontiff (2016) ~26% post-pub decay. 2015~ factor crowding 으로 alpha 압축 가능 — 단 capital-discipline risk 신호로는 robust. ★우리 표본(2015~)에서 재측정 의무 (decay 반영 약 prior 가능).
- **★데이터 실측**: EDGAR `Assets` concept = **전 60종 universe 가용** (NVDA 136/LIN 64/CAT 154/XOM 152/JPM 203/GS 205 obs) = ★가장 깨끗하게 측정 가능한 신규 신호. revenue/COGS 처럼 sector별 태그 파편화 없음.

### 1.2 Gross Profitability (GP/A) ★quality 신규
- **정의**: Gross Profit / Total Assets. **양 sign**.
- **메커니즘 (cyclical 특화)**: cyclical = COGS(원자재 input) 변동성 高 → net income 은 일회성 impairment·tax shield 로 왜곡. Gross Profit 은 훨씬 안정 → 고품질 운영자(저비용·moat) vs 저품질(다운턴 마진 붕괴) 변별. value 와 음상관 = 분산 효과.
- **citation**: Novy-Marx (2013) *JFE* 108(1) "The Other Side of Value: The Gross Profitability Premium" (★CONFIRMED). book-to-market 만큼 강력 + HML 과 음상관.
- **★데이터 실측 제약**: EDGAR `GrossProfit`+`CostOfRevenue` = **semi(NVDA)·industrials(CAT)만 가용**, materials(LIN)·energy(XOM)·financials(JPM/BAC/GS) = 0. → ★sector별 커버리지 파편화 = 측정 시 가용 sub-universe 한정 또는 fallback 태그(Revenues − CostOfGoodsAndServicesSold) 필요. 부분 측정 → small-N hedge 의무.

### 1.3 Sales Yield (Sales/Price) ★peak-EPS-robust value 대표
- **정의**: Sales/Price (= 1/PSR). 매출은 earnings 보다 사이클 안정 → "earnings trap" 면역. cross-sectional, **양 sign** (저PSR = 싼 = forward↑).
- **메커니즘**: cyclical 트로프에서 적자라도 매출 capacity 유지 → 저PSR 가 진짜 value 포착. P/E 가 정점 EPS 로 "싸 보이는" 함정 회피.
- **citation**: Barbee, Mukherji, Raines (1996) *Financial Analysts Journal* "Do Sales-Price and Debt-Equity Explain Stock Returns Better than Book-Market and Firm Size?" (★환각검증 CORRECTED: Phase1 의 "Barbee-Jeong-Mukherji 2008" 오류 → 정확 = Barbee-Mukherji-Raines 1996 FAJ). O'Shaughnessy *What Works on Wall Street* (sell-side, sales-to-price 최강 standalone value 중 하나).
- **★자문 권고**: EV/Sales 보다 **Sales/Price 가 equity factor selection 에 우월** (cash/debt 변동 noise 회피, M&A valuation 용은 EV/Sales). → Sales/Price 우선, EV/Sales 는 보조.
- **★데이터 실측 제약**: `Revenues` = JPM/BAC/CAT/NVDA 가용, **GS·LIN = 0** (다른 revenue 태그). fallback 태그 필요.

### 1.4 Accruals (Sloan) ⏳ 이연
- **정의**: ΔNet Operating Assets / avg Total Assets. **음 sign** (高 accrual = 저품질 earnings = forward↓).
- **메커니즘**: 사이클 정점에서 aggressive accrual 로 earnings inflate → peak 저품질 earnings 탐지. ★peak 탐지에 직결.
- **citation**: Sloan (1996) *The Accounting Review* (★CONFIRMED).
- **데이터 제약**: NOA = (Assets−Cash)−(Liab−Debt) 분해 필요 → 다수 BS concept (current/noncurrent liab, debt 세분) 수집 필요. 현 EDGAR 3-concept 부족 → collector_plan 이연.

## 2. macro / regime / cross-asset 지표 (cross-sectional vs 시계열 라우팅)

★중요: macro 변수(HY OAS/dollar/oil)는 단일 시계열 → cross-sectional signal 직접 불가. 두 경로: (i) **regime conditioner**(시간 분할) 또는 (ii) **cross-sectional β sort**(각 종목 민감도 = 신호).

### 2.1 Credit cycle (HY OAS) — regime conditioner ★3순위
- **변수**: ICE BofA HY OAS `BAMLH0A0HYM2`. risk-on/off → cyclical↔defensive rotation 최강 분류기.
- **메커니즘**: 스프레드 확대(risk-off) = cyclical 약세(고레버리지·earnings 변동·다운턴 민감). 축소(risk-on) = cyclical 강세. coincident~slightly leading.
- **citation**: Fama-French (1989) *JFE* "Business Conditions and Expected Returns" (★CONFIRMED, default spread 가 주식수익 예측). sell-side: BofA(Hartnett) HY spread = risk-on/off 1차 지표. transition signal = 정적 level 아닌 **3~6M 변화 / 1Y MA 돌파**.
- **★데이터 제약 (핵심)**: FRED BAMLH0A0HYM2 = **2023-05~ 37개월만** (실측 확인). regime split 불가(eq_us_defensive H3 ERROR 패턴). → ★장기 proxy 의무:
  - **Baa-Aaa** (BAA−AAA, FRED 월별 1919~) = ★자문 권장 winner. HY OAS 와 ρ>0.85, IG quality spread 가 HY 를 3~6M 선행. risk-free level 면역(treasury 제거).
  - BAA10Y (1986~) / NFCI·NFCICREDIT (주별 1971~, 단 volatility·leverage 혼입 = pure credit 신호 흐림).
  - → ★Baa-Aaa 장기 regime 채택 권고. (collector_plan: FRED BAA/AAA fetch)

### 2.2 Credit-spread β — cross-sectional sort ⏳ 보조
- **정의**: R_i = α + β_mkt·R_mkt + β_credit·ΔSpread + ε 의 β_credit 으로 rank. **음 sign** (高 credit-β = 취약·고레버리지 → forward↓ / risk-off 시 underperform).
- **citation**: Friewald-Wagner-Zechner (2014) *JFE* (equity ↔ credit spread 민감). Garlappi-Yan (2011) distress puzzle.
- **★pitfall (자문)**: ΔSpread ↔ R_mkt 강상관(flight-to-quality) → 다중공선성. **orthogonalize**: ΔSpread 를 R_mkt 에 회귀 후 잔차 사용. rolling window 추정 noise.
- → 측정 복잡 + β 추정 noise + 36mo HY 제약 → 보조/이연. Baa-Aaa 장기로 추정 가능(별도).

### 2.3 dollar β — cross-sectional, 약 prior
- **변수**: DTWEXBGS(broad, DXY 보다 우월) 또는 DXY. 3채널: translation(foreign rev) / commodity(energy·materials) / financial conditions(Bruno-Shin).
- **citation**: Bruno-Shin (2015) *JME* (★단 EM/sovereign 메커니즘 → US large-cap cross-section 도달 약 = ★오적용 주의, direction R2 정합). Liljeblom-Lounasvuori (2011) industry FX exposure. JPM "Dollar Smile".
- **★기존 측정 결과**: dollar β = −0.228 t=−1.02 **비유의** (R2 Bruno-Shin US 도달 약 정합). 약 prior 유지 가능.

### 2.4 ISM/PMI manufacturing — 시계열 timing (cross-sectional 아님)
- **변수**: ISM Mfg PMI `NAPM`. >50 상승=cyclical 강. 변화율(momentum)이 level 보다 중요.
- **citation**: Koenig (2002) Dallas Fed (PMI 가 GDP·IP 선행). Chen-Roll-Ross (1986) IP growth = priced factor.
- **★역할**: leading time-series timing. ★cross-sectional signal 아님 → sleeve 측정(cross-sectional)엔 직접 부적합. supervisor regime feature 후보 (보고만). → 이연.

### 2.5 industrial production / inventory-to-sales / capacity util — 시계열 conditioner
- INDPRO/ISRATIO/TCUTIL. coincident. Chen-Roll-Ross (1986) IP = APT priced factor. → 시계열, sleeve cross-sectional 직접 부적합. 이연(supervisor regime).

### 2.6 oil / commodity — energy·materials β
- WTI `DCOILWTICO`. energy/materials = 직접 pass-through β. broader cyclical = global 수요 강도 timing.
- → energy·materials sub-sleeve cross-sectional β 가능하나 sector-concentrated. cross β 보고 후보.

### 2.7 yield curve / real rate — financials 특화 conditioner
- T10Y2Y(Estrella-Mishkin 1998 recession 예측) / DFII10. steepening = financials NIM↑. → H5 bank rate+ vs utility rate− 는 us_defensive 영역. cyclical 내 financials = rate β 보고.

## 3. 측정 방법론 정정 (자문 R2 + Phase 2 수렴)

- **family 3분리**: family_1 unconditional 예측 IC(1차 discovery, BY 검정) / family_2 regime-conditional gated(2차, 별도 m) / family_3 driver β attribution(BY 제외). ★Harvey-Liu-Zhu (2016) *RFS* — regime-conditional 을 unconditional 과 같은 family 에 넣으면 "regime 탐색" 페널티. 단 cherry-pick 방지 위해 ★regime 사전지정(high spread = 상위 quintile)이면 별 family 정당.
- **M_eff (Li-Ji 2005 *Heredity* eigenvalue)**: near-duplicate test(per_z 3M/6M/12M/24M 강상관) → raw count 과대. M_eff = Σ[I(λ_i≥1)+(λ_i−⌊λ_i⌋)]. ★test-statistic 상관행렬에 적용(원변수 행렬보다 robust). caveat: M_eff≪M 일 때 critical value 조정.
- **eff_N 이중보정**: 시계열 eff_N≈T/h × 횡단면 eff_N=N/(1+(N−1)ρ̄). 둘 다 곱해 IC 검정·breadth-IR 양축. 24M overlap = eff_indep_N≈n/24≈4.7 degenerate.
- **24M_value degenerate**: 23/24 overlap → eff_N≈2.5~4.7 = primary 근거 강등, 3M/6M/12M primary 재배치. magnitude+significance 둘 다 overlap inflation.
- **Romano-Wolf bootstrap** (자문 보조 권고): overlapping horizon 의존구조에 eigenvalue 보다 modern — 단 구현 복잡, M_eff 1차 채택 + Romano-Wolf 후속 의제.

## 4. S1 결론 — 측정 대상 지표 확정 (§2 측정 진입용)

★기존 4 (per_z/pbr_z/vol/mom) + ★신규 측정 (데이터 가용):
1. **asset_growth** (Assets YoY, 음) — ★전 universe 가용, 최우선 신규
2. **gross_profitability** (GP/Assets, 양) — semi·industrials 가용, sector 부분
3. **sales_yield** (Revenues/Price, 양) — 부분 가용(revenue 태그 fallback 필요)
4. **ev_ebitda** (보조) — OperatingIncomeLoss+D&A+debt+cash 가용 일부

★regime/cross (cross-sectional 직접 부적합 → conditioner·β 보고 or 이연):
- credit regime = **Baa-Aaa 장기 proxy** (HY OAS 37mo 대체) ★collector_plan
- dollar/rate/vix/oil β = 보고 (기존 hy_oas β 강하나 36mo hedge)

★이연 (데이터·범위): accruals(NOA 분해) / ERB(IBES 유료, free 부재) / credit-spread β cross-sec(추정 noise) / PMI·INDPRO·ISRATIO(시계열 = supervisor regime) / BAB(beta sort, 보조).
