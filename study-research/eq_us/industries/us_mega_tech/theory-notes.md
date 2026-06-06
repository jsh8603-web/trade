---
tags: [type/theory-notes, domain/equity, sector/us_mega_tech, status/active]
date: 2026-06-03
purpose: S1 학술 ground — us_mega_tech(compounder, Mag7+AVGO/AMD/ORCL/ASML 11종 custom basket) 신호의 1차 문헌 근거. ★N=11 small-basket → cross-sectional vs basket-level 어느 신호가 유의한가 발굴. 자문 R2 수정4(basket화) 학술 뒷받침. 자문 복붙 아님 — WebSearch citation + EDGAR concept 가용성 실측.
sources: WebSearch 7주제 (archive ~/.claude/docs/archive/research-raw/us-megatech-signals-native-20260603.txt, Gemini Pro 2-Phase rate-limited 폴백) + citation 교차검증 + EDGAR XBRL 실측 (§2 진입 시)
---

# us_mega_tech 이론 노트 (S1 학술 ground)

> ★핵심 framing: **compounder = long-duration growth + quality**. "싸다" ≠ 저PER(★expensive_trap: 고PER 정상 = growth-duration). value premium **부재**가 archetype 정의(cyclical/asset_stable 와 반대). ★측정 단위 문제 = N=11 custom basket → cross-sectional rank-IC 통계력 약(Grinold breadth) → **basket-level time-series factor timing 우선 + cross-sectional small-basket hedge** (자문 R2 수정4).
>
> ★us_cyclical pilot 의 sector-neutral z 발견은 **비적용** — us_mega_tech = 단일 archetype(compounder) basket, 11종 모두 같은 mega-tech 그룹 = sub-sector demean 할 peer 구조 없음. (이유 15axis G-A.5 명시.) 가져올 것 = family BY 3분리 / M_eff / eff_N 이중보정 / EDGAR PIT 파이프라인 / small-n hedge.

## 0. ★측정 단위 핵심 — N=11 small-basket 통계 (자문 수정4 학술 ground)

- **Grinold (1989) Fundamental Law of Active Management**: IR = IC·√breadth, breadth = N independent bets × frequency. ★N=11 cross-sectional = breadth 협소 → IR/통계력 급감. modest IC(0.03~0.05)는 수천 종목 누적이라야 유의. = ★cross-sectional rank-IC 단독 verdict 부적합 (자문 R2 #4 정합).
- **intra-basket 고상관 → 유효 breadth ≪ 11**: eff_N = N/(1+(N−1)ρ̄). mega-tech ρ̄ 높음(reflexivity, 현 recent 0.355) → 유효 breadth 추가 급감. breadth-IR 에서 count(11) 직접 사용 = IR 과대(자문 R2 [claude]).
- **★대안 = basket-level time-series factor timing**: basket EW(또는 cap-weight) return 의 factor exposure(real-rate β / VIX β / quality spread / momentum) 시계열 신호. cross-asset 비교는 basket-level. ★cross-sectional 은 small-basket hedge(breadth-IR + magnitude 50~70% haircut, §M.12) 강하게 병기, 단독 verdict 금지.
- ⛔ sector-neutral z 비적용(단일 archetype, peer 부재) — us_cyclical multi-sector 와 다름. 15axis G-A.5 사유 명시 의무.

## 1. compounder primary 신호 후보 (expensive_trap = value 반대)

### 1.1 ★Duration / real-rate sensitivity — ★최우선 basket-level (compounder 본질)
- **정의**: basket EW return ~ Δreal_rate(DFII10) β (시계열). long-duration growth = 미래 현금흐름 비중 높음 → 할인율(real rate) 민감 강.
- **메커니즘**: ★Gormsen-Lazarus (2023) JF 78(3) 1393-1447 *Duration-Driven Returns* (★환각검증 CONFIRMED, vol/page/year 일치). value/profitability/investment/low-risk/payout 프리미엄 = 전부 **short-duration** firm 투자(near-future cashflow). single-stock dividend futures 로 입증: firm 내 CAPM α 가 maturity 증가에 **감소**. → ★compounder(long-duration growth) = 그 프리미엄들의 **반대편** = ★expensive_trap(value premium 부재) **학술 직접 입증** + ★real-rate β 강 음.
- **★측정 라우팅**: real_rate 는 단일 시계열 → cross-sectional 직접 불가. (i) **basket-level β timing**(우선, mega-tech 본질 채널) 또는 (ii) cross-sectional 종목별 real-rate β sort(보조, N=11 약). ★basket-level 이 1차.
- **기존 측정**: cross-v3 real_rate β = −0.030 t=−0.2 비유의(basket 전체), ai_semi −0.245 약 음 / mag7 +0.007 무. ★단 이는 cross-v3 단순 단일회귀 — duration 채널은 ★multivariate(rate level vs Δ) + lead-lag 재측정 의무. us_defensive utilities(−0.213 강)보다 약하게 나온 것 = 측정 부족 가능성(Gormsen 이론상 강해야).

### 1.2 quality / low-volatility — cross-sectional(hedge) + basket-level
- **정의**: 저변동성(60d) z 하위(안정) overweight = quality 프리미엄. **양 sign**(저변동→고forward).
- **메커니즘**: ★BAB Frazzini-Pedersen (2014) JFE 111 (★CONFIRMED) — alpha/Sharpe 가 beta 증가에 단조 감소(funding constraint). QMJ Asness-Frazzini-Pedersen — quality 프리미엄, ★negative market beta·방어적(recession 강). compounder 해석: 저변동 = AAPL/MSFT 안정 mega-cap 복리 / 고변동 = AMD/TSLA 투기적.
- **★측정 제약**: ★BAB/QMJ 는 **broad cross-section 전제** → N=11 cross-sectional rank-IC 통계력 약(Grinold). 기존 vol_60 IC +0.241 t3.10 = ★n=11 basket BY 미생존(small-basket). → basket-level low-beta exposure timing 병행 + cross-sectional 은 breadth-IR/haircut hedge.
- **기존 측정**: cs_lowvol +0.241(12M, breadth-IR 2.56, BY 미생존) = dominant 하나 small-basket PARTIAL.

### 1.3 forward EPS growth / earnings revision breadth (ERB) — compounder primary(데이터 gap)
- **정의**: forward EPS 성장 / analyst revision breadth = (up−down)/total estimates. **양 sign**. compounder 의 진짜 primary(성장 지속).
- **메커니즘**: ★Chan-Jegadeesh-Lakonishok (1996) JF 51 / Stickel (1991) Accounting Review — revision breadth 1~6M forward 예측, underreaction drift(post-forecast-revision drift). 강한 revision = ★lower volatility(quality 와 연결). direction R1 alpha 1순위(ERB).
- **★데이터 gap (핵심)**: ★IBES/FactSet/Refinitiv 유료 = free API 부재. EDGAR = actuals only(expectation 없음). → fwd EPS proxy(net_income TTM YoY 외삽) 또는 collector_plan high. ★compounder primary 인데 직접 측정 불가 = 가장 큰 gap.

### 1.4 PER value = ★무신호 정상 (expensive_trap 직접 검증)
- **정의**: 저PER→고forward(value) cross-sectional. compounder 에선 ★작동 안 함 = 고PER 정상.
- **메커니즘**: §1.1 Gormsen-Lazarus duration = 고PER 가 long-duration 성장 반영 = 정상. value premium 부재가 archetype 정의. ★PER IC ≈ 0 을 직접 검증(reject 아닌 expected null = archetype 지지).
- **기존 측정**: per_z 3/6/12M ≈ 0(−0.001/+0.026/+0.013) = ★expensive_trap 정합. ★재측정도 무신호 확인 의무(archetype 입증).

## 2. momentum / risk factor

### 2.1 momentum & ★momentum crash tail
- **정의**: 6M momentum z → 1M forward. **양 약**(growth persistence). + ★crash 좌측꼬리 monitor.
- **메커니즘**: Jegadeesh-Titman baseline. ★Daniel-Moskowitz (2016) JFE 122 221-247 *Momentum Crashes* (★CONFIRMED, vol/page 일치) — momentum 음 skew, panic state(시장 하락 + 고변동성 후) crash. ★concentration 이 좌측꼬리 증폭(Mag7 동조). dynamic vol-scaling 으로 완화(α 2배).
- **기존 측정**: mom_6 1M IC +0.050 t1.56 비유의(약 양). ★crash tail = reflexivity monitor 와 연동(좌측꼬리 risk overlay).

### 2.2 VIX / market β — ★risk factor·timing (alpha 아님)
- **정의**: basket return ~ ΔVIX β. mega-tech 고베타 risk-on.
- **메커니즘**: ★고베타 risk-on 성장주. ★BAB 함의 = high-beta 는 risk-adjusted **underperform** → β 는 alpha 아닌 **risk overlay/timing**(de-risk 입력). 신호로 착각 금지.
- **기존 측정**: VIX β = −0.008 t−2.5(basket) / mag7 t−4.0 강 음 = 고베타 risk-on 확인. ★L축 공통인자(supervisor 1회 계상) + timing feature 보고.

### 2.3 AI capex supply-chain (H6) — 부호 불확실(over-investment vs productive)
- **정의**: capex/equity intensity z cross-sectional. hyperscaler capex(MSFT/AMZN/GOOGL/META)→반도체(NVDA/AVGO) fwd EPS lag 1-2Q.
- **메커니즘**: ★Cooper-Gulen-Schill (2008) JF 63(4) (★CONFIRMED) asset growth anomaly — 高 자산성장/capex = ★낮은 forward 수익(top decile 6% vs bottom 26% = 20%/yr). Titman-Wei-Xie (2004) over-investment underreaction. ★단 compounder AI capex = **productive growth** 가능성(over-investment penalty 반대) = ★부호 불확실 = 데이터 판정 대상. supply-chain lead-lag = supervisor DY 단계.
- **기존 측정**: capex_z IC 약 음(−0.028~−0.087 비유의) = over-investment 약 신호 or 무. fwd EPS proxy 필요.

## 3. risk overlay (신호 아님)

### 3.1 ★reflexivity / concentration monitor (H9) — de-risk throttle
- **정의**: intra-basket 60d rolling corr + breadth(EW vs cap-weight 3M spread). 동시 극단(corr↑ AND breadth 협소) = 정점 risk.
- **메커니즘**: ★Mag7 ~S&P 1/3 집중. EW-CW regime shift(2026 CW→EW 전환 조짐). ★intra-corr 불안정 = stress 시 cluster(diversification 실패) → drawdown 증폭(2022 Mag7 −40% vs S&P −18%). Soros reflexivity 정량화. ★return-predicting alpha 아님 = **risk overlay**(supervisor de-risk throttle).
- **기존 측정**: intra-corr recent 0.355 < 0.70 + breadth +0.08 양 = ★현재 정점 아님(cap-down 미발동). corr>0.70-0.75 AND breadth<−3~−5%p 동시 = 발동.

## 4. 측정 방법론 정정 (자문 R2 + frame §M.12 + ★수정4)

- **★수정4 basket화 (mega_tech 핵심)**: N=11 cross-sectional rank-IC = small-basket 통계력 약(Grinold). → ★basket-level time-series factor exposure timing(real-rate/VIX/quality/momentum) **우선** + cross-sectional 은 breadth-IR + magnitude 50~70% haircut hedge 강(§M.12), 단독 verdict 금지. ⛔ sector-neutral z 비적용(단일 archetype).
- **family 3분리**: family_1 unconditional 예측 IC(cross-sectional, BY 검정) + ★family_1b basket-level factor timing(별 측정) / family_2 regime-conditional(VIX/NDX regime 사전지정, 별 m) / family_3 driver β attribution(real-rate/VIX/dollar/rate, BY 제외). Harvey-Liu-Zhu (2016) RFS.
- **M_eff (Li-Ji 2005 Heredity eigenvalue)**: near-dup test(per/pbr/capex 강상관) → raw count 과대. M_eff = Σ[I(λ≥1)+(λ−⌊λ⌋)], test-stat(IC 시계열) 상관행렬. family_1 BY threshold.
- **eff_N 이중보정**: 시계열 eff_N≈T/h × 횡단면 eff_N=N/(1+(N−1)ρ̄). ★mega-tech ρ̄ 높아(0.355+) 횡단면 eff_N 급감 = small-basket degenerate 민감. 24M overlap = 시계열 eff_N≈4.7 degenerate.
- **block-boot**: block=horizon 비례(§M.12). NW-HAC lag=horizon.

## 5. S1 결론 — 측정 대상 확정 (§2 진입용)

★**basket-level (우선, 수정4)**:
1. **real_rate β timing** (음, Gormsen-Lazarus) — ★compounder 본질, multivariate + lead-lag 재측정
2. **VIX β timing** (음, risk-on) — risk overlay + timing feature
3. **quality(low-beta) basket exposure** (양) — BAB/QMJ basket-level
4. **momentum basket timing** (양 약) + crash tail monitor

★**cross-sectional (small-basket hedge, 단독 verdict 금지)**:
5. **vol_60** (양, quality) — 기존 dominant, breadth-IR + haircut
6. **mom_6/mom_12_1** (양 약) — growth persistence
7. **per_z** (≈0, expensive_trap 직접 검증 = expected null)
8. **pbr_z** (약 음, 비유의) / **capex_z** (H6, 부호 불확실)

★**risk overlay (신호 아님)**:
9. **reflexivity monitor** (H9) — intra-corr + breadth, de-risk throttle

★**이연 (데이터·범위)**: ERB/fwd EPS(IBES 유료, EDGAR actuals only = compounder primary gap) / FF5+QMJ+BAB neutralize(concentration β 분리, H12 = supervisor) / supply-chain lead-lag(DY supervisor) / gross_profitability(EDGAR concept 확장 가능 시).
