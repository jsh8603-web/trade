# direction — eq_us Phase 3.5 (frame v3 §M 양식 반영, 2026-06-04)

> **진입**: [handoff-eq_us-phase3-complete-20260531.md](../../handoff-eq_us-phase3-complete-20260531.md) §6 초안(R1+R2 자문 gemini-web+claude-web 수렴) + **frame v3 §M 양식 적용**(한국 7산업 batch 학습 반영).
> **frame v2(2026-05-31) → v3 차이**: 측정 **15종**(주식 적용 14, intraday만 제외) + **15축 audit**(A~P) + **cross 3종 라우팅**(RegimeGlasso 동시 / Diebold-Yilmaz 방향 / supply-chain 구조) + **exposure card 분담**(sleeve subagent=측정 전용, supervisor=조립·Σ·throttle·execution) + **archetype 척추**(us 3 sleeve = `core/structure/archetype.py`) + **6단계 SOP**.

---

## §0. frame v3 §M 양식 적용 (★한국 7산업 batch 입증 반영)

### 0.1 측정 단위 = sleeve (exposure card)

한국 = 산업(industry), 미국 = **sleeve**(Tier 차등). frame v3 §M.7 exposure card 계약 동일:
- **sleeve subagent = 측정 전용** — universe 내 cross-sectional peer-relative z-score → forward Rank-IC + regime 4게이트 + PIT + 생존편향 + 유동성-티어. ⛔ 조립·Σ_signal·RegimeGlasso Ω·DY throttle·construction = supervisor 몫(안 함).
- **supervisor = single-writer** — sleeve exposure card 합산 → 직교화 → L축 공통인자 1회 계상 + PSD → §K construction.

### 0.2 측정 15종 (미국 적용 14, intraday 제외)

forward 횡단면 IC(horizon-tagged) + regime 4게이트(G1 ex-ante / G2 Bonferroni·BY-FDR / G3 walk-forward CPCV purge+embargo / G4 Newey-West HAC) + leave-episode + within-period + partial-corr + placebo + effective-N tier + net-cost + e-process(e-CUSUM) + block-bootstrap + within-family neutralize + cross-asset family. **★미국 특화**: factor neutralize = **FF5+Mom+QMJ+BAB**(Ken French + AQR public) — 모든 alpha → time-series 회귀 intercept NW t 보고(concentration beta 분리, H12).

### 0.3 cross 3종 라우팅 (§M.3, sleeve=보고만 / supervisor=통합)

- **RegimeGlasso(동시 의존)** → Σ_return: sleeve는 공통인자 β(dollar/rate/HY OAS/oil/VIX) **보고만**.
- **Diebold-Yilmaz spillover(방향)** → de-risk throttle(attenuation-only) + regime feature. ⛔ Σ covariance 주입 금지(PSD 파괴).
- **supply-chain momentum(구조)** → alpha 후보(15종 검증, null이면 skip). 미국 = AI capex → Mag7 fwd EPS(H6), 글로벌 semi cycle.

### 0.4 archetype 척추 (us 3 sleeve, `archetype.py` 정의)

| sleeve | archetype | 구성 | valuation 1차 가설 |
|---|---|---|---|
| **us_mega_tech** (T0) | compounder | Mag7 + AVGO/ORCL/AMD (±ASML US ADR) | expensive_trap(고PER 정상, growth-duration) |
| **us_cyclical** (T1) | cyclical | SOXX/XLB/XLI/XLE/XLF | ★PBR○ PER✗(peak-EPS, ★한국 auto·반도체 입증 = 미국 cyclical 재현 검증) |
| **us_defensive** (T1) | asset_stable | XLP/XLU/XLV/XLC-mature | PER value premium(한국 consumer·telecom 동형 검증) + bond-proxy duration |

★valid_from PIT 사전선언(§M.5, ex-post 금지). sub-archetype 부호 반대(bank rate+ vs utility/REIT rate−) = T2 분기.

### 0.5 6단계 SOP (S1 논문→S2 실측 4게이트→S3 외부검토→S4 재검증→S5 역공격 수렴→S6 15축 audit)

Phase 3 자문(S3/S4) 수렴 완료 = 본 direction. Phase 5 sleeve = S1·S2·S6, Phase 6 = 독립 15축 audit(hard-fail 0 전 adopted 금지).

### 0.6 ★미국 특수 제약 (한국과 다른 점)

- **universe = ETF holdings / custom basket** (한국 종목 universe ≠). T0 = Mag7 basket(GICS 3 파편화 = "T1=XLK+XLC 50%" 가설 폐기), T1/T2 = sector ETF.
- **데이터**: yfinance(가격, ★survivorship-biased 명시) + **EDGAR**(10-K/Q, Form 4, XBRL = 한국 DART 대응) + FRED/ALFRED(거시 PIT vintage) + Ken French. ⛔ 합성·시뮬 금지(★eq_us_defensive synthetic 240m seed 사건 재발 방지 — Phase 6 합성 지문검사 의무).
- **PIT = EDGAR filing acceptance timestamp**(filer 등급별: Large accel 10-K 60d/10-Q 40d). DART rcept_dt 대응.
- **생존편향**: yfinance + S&P500 historical changes + 상폐 ticker 보존 partial, 불충분 시 Sharadar Core US($50/월) 도입 권고.
- **기존 자료 통합(재작업 금지)**: `eq_us_cyclical/`(SOXX/XLB/XLI/XLE M3 실측) + `eq_us_defensive/`(★합성 P0 재검증 대상)는 input prior로 통합만.

---

## ① 이론 수집 방향

### 1.1 미국 시장 본질 (한국과 다른 점, R1+R2 핵심)

- **Mag7 GICS 3 sector 파편화** (★R2 사실 확인, 2018-09-28 S&P / 2018-11-30 MSCI 재편): AAPL/MSFT/NVDA=XLK / GOOGL/META=XLC / AMZN/TSLA=XLY. 사용자 "T1=XLK+XLC 50%+" 가설 깨짐 → **T0 = custom basket(Mag7+AVGO/ORCL/AMD ±ASML US ADR)**. Mag7 합산 S&P weight 31-34%.
- **alpha driver 1-3 순위** (R1+R2 합의):
  1. **Earnings Revision Breadth (ERB)** — IBES revision momentum + PEAD, US 가장 안정 cross-sectional alpha
  2. **Total Shareholder Yield (TSY)** — buyback + dividend, fundamental tilt(crowding 저항)
  3. **HY OAS regime** — risk-on/off cyclical↔defensive rotation 최강 분류기. Fed funds path / AI capex = base driver 아닌 **regime conditioner**
- **dollar 채널 = 3 메커니즘 혼재** (★R2 절충, Claude frame): (1) foreign-revenue translation(구조) (2) commodity 가격(구조) (3) financial conditions(rate cycle 흡수, 표본 한정 artifact). Bruno-Shin(2015) = EM/sovereign 메커니즘 = US sector cross-sectional 도달 약(★오적용 주의).
- **defensive sub-archetype 부호 반대**(cash-flow-mechanical): bank rate-beta(+, NIM) vs utility/REIT rate-beta(−, bond-proxy DCF duration).
- **XLRE 분리**(eq_us=GICS 10): REIT FFO 별도 valuation, reit study(H1 REJECT 이력)는 exogenous prior만 import.
- **factor decay**(McLean-Pontiff 2016 JF 58% post-pub, 26% post-sample): shareholder yield=fundamental 완만 / revision breadth=PIT confound 위험.

### 1.2 이론 정독 list (★환각 정정 4건 적용 reference 22)

**핵심 학술**: Damodaran NYU(2024 Sector Valuation) / Fama-French(1997 JFE 43) / ★**Asness-Moskowitz-Pedersen (2013) JF 68** Value&Momentum Everywhere(R1 환각 정정) / Asness-Frazzini-Pedersen(2019) **RAS 24** QMJ(저널 정정) / Frazzini-Pedersen(2014 JFE 111 BAB) / ★**Ben-David-Franzoni-Moussawi (2018) JF 73** ETF Volatility(환각 정정) / Daniel-Moskowitz(2016 JFE Momentum Crashes, ★Mag7 cap 근거) / McLean-Pontiff(2016 JF 71 decay) / Boudoukh-Michaely-Richardson-Roberts(2007 JF 62 Payout Yield) / Chan-Jegadeesh-Lakonishok(1996 JF 51 earnings momentum) / Novy-Marx(2013 JFE 108 Gross Profitability) / Bruno-Shin(2015 ReStud 82, ★메커니즘 오적용 caveat) / Weber(2018 JFE [vol verify]) / ★**Gormsen-Lazarus (2023) JF** Duration-Driven Returns(표현 정정) / Stickel(1991 Accounting Review 66 [부제 verify]) / Elton-Gruber-Blake(1996 RFS 9 Survivorship) / López de Prado(2018 CPCV) / Newey-West(1987) / Bailey-López de Prado(2014 Deflated Sharpe) / VanderWeele-Ding(2017 E-Value).

**실무·정책**: GS(2024 Earnings&Yield) / BofA(2023 HY OAS rotation) / JPM(2023 FX-Rates) / S&P DJI(2023 Concentration+Capping) / NAREIT / CBOE(0DTE) / SEC EDGAR Rule / IRA(2022 ITC/PTC·약가).

**OSS/1차**: FRED(DGS10/DFII10/BAMLH0A0HYM2/DTWEXBGS/WTISPLC/T10YIE/VIXCLS) + ALFRED vintage / SEC EDGAR(10-K/Q, Form 4, 13F, XBRL) / Ken French(FF5+Mom) / skfolio·toraniko·alphalens / Sharadar Core US($50, survivorship-free, OSS 불충분 시) / yfinance(★bias 명시).

## ② 이론 검증 방향

### 2.1 평가 SSOT
- **15축 audit**(frame v3 A~P, ★frame v2 12축 확장) — Hard-fail 코어 4 = B(실데이터)·C(추적성)·D(PIT)·I(생존편향).
- **측정 4게이트**(§M): N≥24 / SE CI 0배제 / Power MDE>0.05 / BY-FDR q<0.10 / OOS skfolio CPCV.
- **factor model baseline** = Ken French FF5+Mom + QMJ + BAB neutralize 의무.

### 2.2 OSS validate 인프라
skfolio CPCV(purge+embargo 1-5%) / toraniko(미국=FF5+Mom+QMJ+BAB) / alphalens(IC tearsheet) / Newey-West HAC(lag ~T^¼) / block bootstrap(block ~T^⅓, 점추정 X) / Benjamini-Hochberg·BY + deflated Sharpe / Ken French datareader.

### 2.3 Tier 차등 → frame v3 sleeve 매핑 (★R2 macro-sleeve 재설계)

| Tier | frame v3 sleeve | 구성 | 책임 |
|---|---|---|---|
| **T0** | us_mega_tech (compounder) | Mag7 + AVGO/ORCL/AMD (±ASML US ADR) | reflexivity monitor(intra-corr+breadth 동시) / AI capex×fwd EPS / momentum crash tail(Daniel-Moskowitz 2016) |
| **T1** | us_cyclical + us_defensive (macro-sleeve 2-4축) | cyclical(XLI/XLB/XLE/XLF/SOXX) / defensive(XLP/XLU/XLV/XLC) / rate-sensitive(XLU bond-proxy) / dollar-sensitive(XLB/SOXX) | Macro driver 4(dollar 3채널+rate / HY OAS / Fed path conditioner) × regime 4(Reflation/Recovery/Overheat/Slowdown) |
| **T2** | sub-archetype 분기 | bank/insurance(XLF) / pharma/biotech(XLV) / utility(XLU) / staples(XLP) / payments(XLF) | sub-archetype 부호 반대(rate +/−, NIM thesis) |
| (관측만) | — | GICS 10 sector ETF(XLRE 제외) | data layer |

**★T0 reflexivity monitor trigger**(R2): intra-Mag7 60d corr > 0.70-0.75 AND breadth(S&P EW-CW 3m spread <−3~−5%p 또는 %>200dma <40%) **동시** → concentration **축소**(cap-up 정반대).

### 2.4 PIT / lookahead
EDGAR filing acceptance timestamp(filer 등급 차등) / ALFRED first-release vintage / survivorship-free(Sharadar 권고) / PIT revision IC(unrestated vs retroactive, look-ahead artifact).

### 2.5 regime cell (32 = Macro 4 × HY OAS 4 × dollar 2)
Macro 4(Reflation/Recovery/Overheat/Slowdown) × HY OAS 4(<300/300-500/500-800/>800) × dollar 2(ρ(Δrate,Δdollar) low/high rolling 252d). N gate(cell N≥24) + cell collapse 가이드.

### 2.6 ★사용자측 실측 3건 (Phase 5 sleeve 핵심)
1. **2015-2019 β_dxy 회귀**(DTWEXBGS + sector ETF) → dollar 구조성(|β|≥0.3 유의=구조 / <0.2=artifact, H4).
2. **11-ETF PCA**(2015-2024 raw+residual) → 80% PC 개수(≤5=macro-sleeve / ≥7=11 tier, H8).
3. **PIT revision IC 재추정**(unrestated vs retroactive) → >30% drop=look-ahead artifact(H1·H11).

## ③ 핵심 가설 12 (반증조건 포함)

| # | 가설 | signal source | 반증조건 | confidence |
|---|---|---|---|---|
| H1 | Revision Breadth(ERB) → fwd 1-3M cross-sec return(+) (★1순위) | IBES, EDGAR | rolling 3y IC CI 하한 ≤0 OR FF5+Mom intercept NW t<2 OR PIT re-run <30% drop | high |
| H2 | Total Shareholder Yield(TSY) → value/quality, real-rate 조건부(★2순위) | EDGAR Form 4+10-Q, DFII10 | L/S spread CI high·low rate 양쪽 0 OR 부호 flip OR ~58% decay | med-high |
| H3 | HY OAS regime → cyclical↔defensive rotation(★3순위 conditioner) | BAMLH0A0HYM2 | regime 수익차 CI 0 OR Granger fail. Transition: OAS +100bps/Q | high |
| H4 | dollar 채널 = translation+commodity(구조) + financial conditions(artifact). 2015-2019 β_dxy 판정 | DTWEXBGS, DGS10, ETF | 2015-2019 \|β_dxy\|≥0.3 유의 → 구조설 / <0.2 불안정 → artifact설 | med |
| H5 | bank rate-beta(+) vs utility/REIT(−) regime-안정 | DGS10, sub-sleeve | N≥24 epoch 부호 flip OR CI 양방향 0 | med |
| H6 | AI capex → Mag7 fwd EPS lag 1-2Q. ★IC regime-unstable(reflexivity 의무) | Mag7 10-Q capex | capex-peak 후 CI 하한 >0=durable(H6 기각 위험) / monitor flag 무효 | med-high |
| H7 | Fed funds path surprise → duration-sorted CAR | OIS vs FOMC dot | CAR duration sort monotonic 아님 OR e-value <1.5 | med |
| H8 | sector eff_N ≤5(★PCA 실측): raw 80% ≤5 PC AND residual ≤6 PC → macro-sleeve | 11 ETF 2015-2024 | residual 80% ≥7 PC → 11 tier 독립 | high |
| H9 | Mag7 reflexivity monitor → cascade risk 차단(corr>0.70-0.75 AND breadth 협소 동시) | 60d corr + EW-CW | flag 후 3-6m drawdown 비-flag 대비 유의차 없음 → monitor 무효 | med |
| H10 | XLRE 분리(GICS 10) — REIT FFO 별도. reit study(H1 REJECT) → prior import만 | reit output | REIT signal incremental R² utility 대비 ΔR² CI 하한 >0 | high |
| H11 | shareholder yield post-2010 decay 완만 vs revision breadth post-2015 decay | TSY spread + revision IC | yield ~58% decay → 가설 기각 / PIT revision <retroactive 30% drop → artifact | med |
| H12 | factor neutralize(FF5+Mom+QMJ+BAB) 후 잔존 alpha = 진짜(concentration beta 분리) | toraniko + Ken French + AQR | neutralize 후 sector L/S NW t<2 또는 0 → concentration beta 재포장 | high |

각 가설 = Phase 5 sleeve subagent 가 측정 14종 + 4게이트 통과 시 exposure card weight_rule_candidates 등록 → supervisor 조립.

---

## ④ 5 금지 (모든 Phase invariant)
1. 점추정 prior 박제 금지 — 분포 + CI + 게이트.
2. 합성·시뮬 금지 — 실 수집기 PIT만(★eq_us_defensive synthetic 240m 재발 방지).
3. 자문 그대로 코드화 금지 — supervisor 비판 + 환각 cross-verify 후 채택.
4. Single-source 단정 금지 — 학술+실무+1차 3중.
5. Small-N 단정 금지 — cell N<24 "유의" X. + ★supervisor 직접 평가 금지(Phase 6 독립 15축 audit) + opt-in off byte-identical + reflexive loop 차단(belief→_macro, L축 1회 계상 PSD) + tier 정직성(검증 통과 ≠ validated alpha).

## ⑤ Phase 4-7 (다음 단계)
- **Phase 4**: frame.md(eq_us, frame v3 §M 미러) + plan.md(Phase 5-7 dispatch table + 5분 self-wake monitoring) + evaluation-axes.md(15축 application).
- **Phase 5**: sleeve dispatch — T0(us_mega_tech 1) + T1(us_cyclical/us_defensive 2~4) + T2(sub-archetype). 각 `industries/{sleeve}/` self-contained capsule(summary.yaml v3 + validation-v3 + 15axis-audit). ★resource-consume-consent(대규모) — 사용자 확인 후 착수.
- **Phase 6**: 독립 15축 audit subagent(hard-fail 0, 합성 지문검사). PARTIAL/FAIL → 재dispatch(최대 2회).
- **Phase 7**: 통합 study_session.yaml 7블록 + 직교화 + L축 1회 계상 PSD + main 승인 게이트.
