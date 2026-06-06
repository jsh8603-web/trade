---
tags: [type/theory-notes, domain/equity, sector/us_defensive, status/active]
date: 2026-06-03
purpose: S1 학술 ground — us_defensive(필수소비 XLP / 유틸 XLU / 헬스케어 XLV / 성숙통신 XLC-mature) cross-sectional alpha·regime 지표의 1차 문헌 근거. 자문 복붙 아님, Gemini 2-Phase 리서치(Pro 광범위 + Flash 심층) + citation 환각검증 + EDGAR concept 가용성 실측 예정.
sources: Gemini Pro/Flash 2-Phase (archive: raw-v3/.s1tmp/result1.txt + result2.txt + citecheck-result.txt) + citation 교차검증
---

# us_defensive 이론 노트 (S1 학술 ground)

> ★핵심 framing: defensive(asset_stable) sector 의 본질 = **안정 현금흐름·배당·bond-proxy 듀레이션**. cyclical 의 peak-EPS trap(사이클 정점 EPS↑→P/E↓ 함정)과 **반대** — defensive 는 EPS 안정 → PER value 가 정상 작동 **가능**(가설). 단 ★문헌은 동시에 (a) PBR = buyback 가 book value 왜곡 noise-trap (b) FCF/EV·E/P 가 PER 보다 우월 (c) low-vol/quality/dividend 의 post-2010 crowding/decay 를 경고. 기존 rev_1m/vol_60/real_rate 는 일부 — 누락 = quality/payout-yield/earnings-stability.

## 1. defensive cross-sectional 신호 (S1 핵심 발굴)

### 1.1 Quality / Gross Profitability ★최우선 (BY 생존 1순위 예상)
- **정의**: Gross Profit / Total Assets (Novy-Marx). cross-sectional rank, **양 sign** (고품질 → forward↑). QMJ = profitability + growth + safety 복합(AFP).
- **메커니즘 (defensive 특화)**: defensive universe 는 *이미* 고품질 집합 → quality 신호가 "진짜 우수 운영자(brand moat·pricing power·운영효율) vs 단순 안정주" 변별. staples/utilities 에서 일관 고 GP = moat. safety 성분(low-beta/vol/leverage)은 universe 에 이미 내재 → ★profitability·payout 성분이 cross-sectional 주력.
- **citation**: Novy-Marx (2013) *JFE* 108(1) "The Other Side of Value: The Gross Profitability Premium" (★환각검증 CONFIRMED). Asness-Frazzini-Pedersen (2019) *Review of Accounting Studies* 24(1) 34-112 "Quality Minus Junk" (★CONFIRMED, 저널 RAS 정확 — 한국/cyclical 세션 ERROR 였던 "RFS/JoF" 아님).
- **★자문 BY 생존 우선순위 = 1위** (가장 persistent). decay 경고: McLean-Pontiff(2016) post-pub ~58% decay, smart-beta ETF 수조달러 유입 → quality 도 crowding. valuation overlay(quality-at-any-price 회피) 권고.
- **★데이터**: EDGAR `GrossProfit`/`CostOfRevenue`(fallback Revenues−COGS) + `Assets`. us_cyclical 실측 = semi/industrials 만 직접 가용·일부 fallback → defensive(staples/healthcare) 가용성 측정 의무.

### 1.2 Low-Volatility / Low-Beta (BAB) ★기존 보강
- **정의**: 60d realized vol (또는 market-beta) z. cross-sectional, **음 sign** (저변동성 → 고 risk-adjusted forward).
- **메커니즘**: leverage constraint(Frazzini-Pedersen: 레버리지 못 쓰는 투자자가 고베타 overweight → 고베타 overpriced, 저베타 underpriced) + lottery preference(Baker-Bradley-Wurgler: 투자자 고변동성 복권 선호 → 저변동성 구조적 저평가). defensive = 저베타 본산. ★within-defensive 에서도 0.4 베타 utility vs 0.7 베타 utility 상대가치.
- **citation**: Frazzini-Pedersen (2014) *JFE* 111(1) 1-25 "Betting Against Beta" (CONFIRMED). Baker-Bradley-Wurgler (2011) *FAJ* 67(1) 40-54 "Benchmarks as Limits to Arbitrage" (CONFIRMED). Ang-Hodrick-Xing-Zhang (2006) *JF* 61(1) 259-299 (CONFIRMED).
- **★기존 측정**: 현 us_defensive vol_60 12M IC +0.076(block-boot 0배제 but NW 0포함 TENTATIVE). ★자문 caveat: low-vol 을 beta 에 residualize 해야 pure rate-sensitivity(듀레이션) 혼입 회피. = sector-neutral 후 재측정 의무.

### 1.3 Payout / Shareholder Yield ★신규 (defensive 핵심, crowding 경고)
- **정의**: shareholder yield = (Dividends + net Repurchases − Issuance) / mktcap (BMRR). **양 sign** (고 payout → forward↑). dividend yield 단독 = 더 clean 하나 정보량 적음.
- **메커니즘 (defensive 특화)**: defensive = 배당주 본산. payout yield = 자본환원 commitment·경영 규율 신호. ★단 ★critical crowding: income-seeking 투자자가 고배당 몰림 → 고배당 = value trap(주가 하락→yield 인위 팽창=distress proxy) 위험. → quality(earnings sustainability) 필터 결합 필수.
- **citation**: Boudoukh-Michaely-Richardson-Roberts (2007) *JF* 62(2) 877-915 "On the Importance of Measuring Payout Yield" (★CONFIRMED, payout yield > dividend yield 단독). Fama-French (1988) *JFE* 22(1) 3-25 (dividend yield 예측, 주로 시계열).
- **★decay 경고**: dividend anomaly post-2010 ZIRP "reach for yield" 로 상당 붕괴(reach-for-yield 출처 = Greenwood-Vayanos 2014 RFS 는 ★bond supply/duration 다룸, reach-for-yield 1차 출처 아님 = 환각 정정, claim 약화 라벨). post-2015 고yield = distress proxy 多. → payout-quality 필터 시 IC 회복 가능.
- **★데이터**: EDGAR `PaymentsOfDividendsCommonStock` / `PaymentsForRepurchaseOfCommonStock` / `ProceedsFromIssuanceOfCommonStock`(cash flow stmt). 가용성 측정 의무.

### 1.4 Valuation (PER/E-P, FCF/EV, EV/EBITDA) ★핵심 가설 검증 (cyclical 반대)
- **정의**: 저PER/저EV-EBITDA(싼) = value, **음 sign**. E/P(earnings yield)·FCF-yield = **양 sign**.
- **★핵심 가설 (cyclical 반대)**: cyclical = peak-EPS trap → PER✗ PBR○. defensive = EPS 안정 → ★PER value 정상 작동 **예상**(denominator E 신뢰). 한국 consumer/telecom(asset_stable) value premium 방향 동형.
- **★단 문헌 caveat (가설 약화 요소 3)**:
  1. **PBR = noise-trap**: defensive buyback 多 → book value 왜곡(자사주 매입이 equity 감소). = 현 us_defensive PBR 24M IC +0.062 역방향(value trap)의 ★문헌적 설명. → PBR 보다 EV/EBITDA·FCF/EV 우월.
  2. **PER → E/P 변환**: negative earnings 시 PER undefined, E/P monotone(deeply negative = cheapest). asset_stable 도 일부 음수 EPS year(healthcare bad year) → E/P 권장.
  3. **FCF/EV > E/P**: defensive(utilities/staples) = CAPEX-heavy → E/P 가 D&A 왜곡. FCF/EV 가 실제 가용현금 측정 우월.
- **citation**: Basu (1977) *JF* 32(3) 663-682 (P/E value, CONFIRMED). Fama-French (1992) *JF* 47(2) 427-465 (B/M, CONFIRMED). Lakonishok-Shleifer-Vishny (1994) *JF* 49(5) 1541-1578 (value behavioral, CONFIRMED).
- **★검증 의무**: PER/E-P vs PBR vs EV/EBITDA sector-neutral IC 비교 → ★cyclical(PBR○ PER✗)과 반대로 defensive(PER/E-P○ PBR✗) 인지 직접 입증/반증. 현 PBR 역방향이 universe-demean artifact 인지 sector-neutral 후 재측정.

### 1.5 Earnings Stability / Accruals ★신규 (asset_stable 직결, 단 주의)
- **정의**: earnings stability = CV(20분기 net income) 또는 earnings persistence(ROE AR1 계수). 저변동성 = **양**(예상). accruals = NI − CFO, **음 sign**(고 accrual = 저품질 earnings → forward↓, Sloan).
- **메커니즘 (defensive 특화)**: asset_stable archetype 직접 play. ★단 ★중요 caveat: Ball-Gerakos-Linnainmaa-Nikolaev(2015) "Deflating Profitability" = "defensive"(low earnings-vol)은 operating quality proxy = **tail risk 감소이지 평균수익 상승 아님**(bull regime). → earnings stability 단독 alpha 약 prior. accruals red-flag(안정 earnings 가 managed 인지)은 보조.
- **citation**: Sloan (1996) *The Accounting Review* 71(3) 289-315 (accruals, CONFIRMED). Dechow-Dichev (2002) *The Accounting Review* 77(s-1) 35-59 (accrual quality, [tentative vol]). Ball-Gerakos-Linnainmaa-Nikolaev (2015) *JFE* 117(2) 225-248 "Deflating Profitability" (★환각검증 CORRECTED: Phase1 "Defensive Equity, JFE 119" 오류 → 정확 "Deflating Profitability" JFE 117(2)).
- **★데이터**: accruals = NI − CFO(EDGAR NetCashProvidedByUsedInOperatingActivities). earnings stability = 장기 NI 시계열 CV. → EDGAR concept 가용성 측정.

## 2. macro / regime / risk factor (cross-sectional 직접 부적합 → conditioner·β 보고 or 이연)

### 2.1 Rate-Duration (bond-proxy) ★risk factor — unconditional IC ≈0
- **변수**: 각 종목 rolling β to Δrate(DGS10) 또는 Δreal-rate(DFII10). defensive = long-duration(안정 장기 현금흐름) = bond-proxy.
- **★핵심 (자문)**: Gormsen-Lazarus(2023) duration = **risk factor, regime-dependent sign**. ★cross-sectional unconditional IC ≈0 (rate 방향 view 조건부). → ★cross-sectional alpha 아님 = family_3 driver β attribution + regime tilt. 현 us_defensive real_rate β −0.171 t−4.1(sleeve-level 듀레이션 민감 강) = ★sleeve common factor(보고만), cross-sectional 신호 X.
- **citation**: Gormsen-Lazarus (2023) *JF* 78(4) 2321-2365 "Duration-Driven Returns" (CONFIRMED — 한국 세션 "equity yield" 오표기 정정본). Dechow-Sloan-Soliman (2004) *Review of Accounting Studies* 9(1) 197-228 "Implied Equity Duration" (CONFIRMED). Weber (2018) JFE [tentative vol].

### 2.2 Credit regime (HY OAS / Baa-Aaa) — regime conditioner ★family_2
- **변수**: HY OAS `BAMLH0A0HYM2`(★2023-05~ 37mo만 = INSUFFICIENT, us_cyclical 동일 제약) → ★Baa-Aaa(BAA−AAA, 1919~) proxy. credit stress(spread 확대) = risk-off = defensive flight-to-quality 수혜.
- **메커니즘**: spread 확대 시 (a) defensive sleeve 절대·상대 강세 (b) within-defensive 에서 quality/low-vol 신호 증폭(투자자 hyper-discerning). → family_2 regime-conditional gated(별 m).
- **citation**: Fama-French (1989) *JFE* 25(1) 23-49 "Business Conditions and Expected Returns" (default spread 예측, CONFIRMED).

### 2.3 Short-term Reversal ★기존
- **정의**: 1M 단기수익 z, **음 sign** (반전). 현 us_defensive rev_1m 3M IC −0.045 t−2.70 유의(BY 미생존).
- **메커니즘**: 유동성 압력·overreaction. defensive = 대형주 유동성 高 → 효과 약할 수 있으나 noise 성격이라 reversal 신뢰 가능(자문). index rebalancing·fund flow 시 두드러짐.
- **citation**: Jegadeesh (1990) *JF* 45(3) 881-898 (CONFIRMED). ★자문 BY 생존 우선순위 = 2위(small panel·high-frequency·fundamental regime 독립).

### 2.4 Defensive-specific KPI ⏳ 이연 (데이터 부재)
- utilities(regulated ROE/rate base) / healthcare(R&D productivity/patent cliff) / staples(brand/gross-margin stability/pricing power) / telecom(ARPU/churn). ★문헌 = 실무 중심(MSCI/Wolfe), 단일 seminal academic anomaly 없음(Lev-Gu 2016 [tentative] 무형자산). ★데이터 = XBRL 표준화 안 됨(NLP/유료 필요) → 이연.

## 3. 측정 방법론 정정 (자문 R2 + us_cyclical pilot 흡수)

- **★sector-neutral z (최우선)**: ★자문 명시 — universe-demean 하면 "utilities vs healthcare(sub-sector level)"만 잡힘, within-sector value(같은 utility 중 싼 것) 못 잡음. defensive 4 sub-sector = ★dividend yield sign flip(staples/healthcare alpha vs utilities risk = cancel) → ★sector-neutral 필수 + sector interaction. = us_cyclical pilot 발견(universe-demean 결함, sector-neutral z BY 0→8) **동형 가능성 높음**.
- **family 3분리**: family_1 unconditional 예측 IC(BY 검정) / family_2 regime-conditional gated(Baa-Aaa 사전지정, 별 m) / family_3 driver β attribution(rate-duration 등, BY 제외).
- **M_eff (Li-Ji 2005 eigenvalue)**: near-dup horizon 강상관 → raw m 과대. M_eff = Σ[I(λ≥1)+(λ−⌊λ⌋)], test-stat 상관행렬.
- **eff_N 이중보정**: 시계열 T/h × 횡단면 N/(1+(N−1)ρ̄). 24M_value = eff_N≈n/24 degenerate(primary 강등, 3M/6M/12M primary).
- **defensive basket 불필요**: 49종 cross-sectional 유효(mega_tech 전용 basket).

## 4. S1 결론 — 측정 대상 지표 확정 (§2 측정 진입용)

★기존 (rev_1m/vol_60/mom) + ★신규 측정 (데이터 가용성 측정 후):
1. **gross_profitability** (GP/Assets, 양) — ★BY 생존 1순위 예상. EDGAR GrossProfit/COGS+Assets
2. **payout_yield / dividend_yield** (양) — defensive 핵심, ★crowding 경고. EDGAR dividends/repurchase/issuance
3. **valuation 비교**: per_z/ep_z(음/양) + ev_ebitda + fcf_yield — ★cyclical 반대 가설 검증(PER/E-P○ PBR✗). PBR noise-trap 가설
4. **earnings_stability** (CV NI, 양 약 prior) — asset_stable 직결, 단 tail-risk≠평균수익 주의
5. **rev_1m / vol_60** (음) — 기존, sector-neutral 재측정 (vol = beta residualize)

★regime/risk (cross-sectional 직접 부적합 → conditioner·β):
- credit regime = **Baa-Aaa 장기 proxy**(family_2, HY OAS 37mo 대체)
- rate-duration β = **family_3 attribution + regime tilt**(unconditional IC ≈0, cross-sectional alpha 아님)

★이연 (데이터·범위): defensive-specific KPI(XBRL 미표준화) / accruals(CFO concept 추가 fetch) / mom(asset_stable 무효 예상).
