---
tags: [type/study-validation, domain/inv, study/eq_intl, phase/merit-indicators]
date: 2026-06-01
study_id: eq_intl
sleeve: equity.intl
session: btn-eq_intl-merit
raw_source: raw/validation-merit-indicators.py + raw/validation-merit-output.txt + raw/merit_cache/
principles: [PIT 종가, OOS half-split, 합성 금지(fetch 실패 raise), 월간 log-return, Newey-West HAC SE, Bonferroni/BH-FDR, ADF 사전검정]
scope: "block6 collector_plan 4 merit 지표 실데이터 탐구 (검토만 되고 미탐구 상태 → fetch·측정·verdict)"
indicators: [jgb_ust_spread, real_exchange_rate_valuation(REER/terms_of_trade), china_credit_impulse, fx_carry_momentum]
---

# eq_intl merit-indicator 실데이터 탐구 (block6 4 지표)

> 기존 macro-linkage.md(β_dollar/rate/oil) 스타일 미러. block6 collector_plan 에 "검토만 되고 미탐구" 로
> 박힌 4 merit 지표를 실데이터로 fetch → 변환(spec↔code 1:1) → contemporaneous + lead-lag 상관/Rank-IC
> → Newey-West HAC t/p + 95% CI + Bonferroni/BH-FDR → ADF 사전검정 + half-split OOS 부호 일치.
> ★점추정 magnitude 박제 금지 — sign/direction prior + CI. n<30 단정 금지. 비유의면 비유의로.

## §0. 데이터 provenance (감사 §0 — claim 이 아니라 재계산 가능)

| 시리즈 | 소스 | 코드/단위 | 가용 범위 | 빈도 |
|---|---|---|---|---|
| JP 10Y | FRED `IRLTLT01JPM156N` | percent (level) | 1989-01 ~ 2026-04 | M |
| US 10Y | FRED `DGS10` | percent (level), daily→month-last | 1962-01 ~ 2026-05 | D→M |
| REER brazil/mexico/india/china/korea | FRED BIS `RB{BR,MX,IN,CN,KR}BIS` | Real Broad EER (index) | 1994-01 ~ 2026-04 | M |
| China total credit | FRED `QCNPAMUSDA` | Total Credit to Private Non-Fin Sector, USD bn | 1985-10 ~ 2025-07 | Q |
| FX (JPY/BRL/INR/KRW/MXN per USD) | FRED `DEX{JP,BZ,IN,KO,MX}US` | local per USD, daily→month-last | 1971~/1995~/1973~/1981~/1993~ | D→M |
| 국가 ETF (EWJ/EWZ/EWW/FXI/INDA/EWY/EWT) | yfinance `period=max, interval=1mo, auto_adjust=True` (TR) | adj-close (배당·분할 반영) | EWJ/EWW 1996-04~ / EWZ/EWY/EWT 2000~ / FXI 2004-11~ / INDA 2012-03~ | M |

- **합성 지문 검사**: 전 시리즈 FRED/yfinance 실 fetch (raw/merit_cache/ JSON 캐시 박제). ETF 월간 TR n=171~362 (실 거래월), FRED REER n=388, JP 10Y n=448, 결측·갭 실재(주말·휴일 month-last 처리). 합성 시드 아님.
- **★PIT caveat (D축)**: FRED REER·credit·금리 시리즈 = **revised(최종개정치)** — first-release vintage 아님. China credit(QCNPAMUSDA)·BIS REER 는 분기/월 후행 발표 + 사후 개정. **lookahead 위험 존재** → 본 validation 은 "방향성/co-movement 탐구" 한정, 라이브 사이징 직박제 금지(아래 verdict 의 collector_plan 후속 = ALFRED vintage 재검 의무). ETF TR = PIT-safe(가격은 개정 없음).
- 재현: `PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python raw/validation-merit-indicators.py`

## §1. JGB-UST spread vs EWJ(japan) — **verdict: INSUFFICIENT (방향성 부재)**

**spec↔code 1:1**:
- spec: JP 10Y − US 10Y 금리차(엔 carry/디커플 채널). 부호 prior = **양면적(약)** — spread↑(JP 상대고금리)는 엔 강세 압력(unhedged USD 투자자 환이익)이나 일본 수출주 EPS 부담 = 순효과 불명.
- code: driver = **Δspread (1차 차분)** — ADF(spread level) t_rho=**−2.53** > −2.86(5%) → **I(1) 의심 → 차분 강제(§1.7-B)**. target = EWJ monthly log-return. contemporaneous + lead k=1/3/6m.
- Verify: Δspread(return 단위) ↔ EWJ log-return(return 단위) 정합. PASS.

| 측정 | Rank-IC | HAC-t | p | n |
|---|---:|---:|---:|---:|
| contemporaneous (OLS β=+0.0134, HAC-SE 0.0165, 95%CI [−0.019,+0.046], R²=0.004) | +0.047 | +0.68 | 0.495 | 361 |
| lead k=1m | −0.054 | −1.07 | 0.287 | 362 |
| lead k=3m | −0.003 | −0.06 | 0.951 | 362 |
| lead k=6m | +0.037 | +0.80 | 0.425 | 362 |

- half-split OOS: rho1=+0.052 / rho2=+0.051, 부호일치 True — but **둘 다 ≈0**(부호 일치가 신호 아님, 노이즈 부호).
- 다중비교: m=4, Bonferroni α/m=0.0125, raw p<0.05 **0/4**, Bonferroni 생존 **0/4**, BH-FDR **0/4**.
- **verdict = ★INSUFFICIENT/REJECTED (예측·동시 모두 비유의)**: |Rank-IC|<0.06 전 측정, p>0.28. yaml line 274 "dm_japan β_dollar (JGB-UST spread 미반영 caveat)" 의 **JGB-UST spread 자체는 EWJ 월간 수익과 유의한 선형/순위 관계 없음**. caveat 해소 = "JGB-UST spread 가 빠진 게 문제 아님 — 이 spread 는 EWJ 월간 return 에 대해 비유의" 로 해소(누락이 결함이 아님). 엔 환 채널은 §4 fx momentum(japan)에서 별도 측정(역시 약).

## §2. REER (terms_of_trade/valuation) vs 해당국 ETF — **verdict: TENTATIVE DIRECTIONAL (china만 약 방향성, 나머지 비유의)**

**spec↔code 1:1**:
- spec: REER 고평가 → 미래 통화·지수 약세(장기 평균회귀 valuation) = **예측 음 direction prior**. block2 `real_exchange_rate_valuation` transform=own_history_z, lag=1.
- code: driver = **REER own-history rolling z(36m)**(level 비정상 risk 회피 — ADF(REER lvl) t=−2.1~−2.6 전부 I(1) 의심, z 변환으로 비정상 완화). target = 해당국 ETF **forward** monthly log-return(lead k=1/3/6m, valuation = 예측 축). contemporaneous(z↔동월ret)도 병기.
- Verify: own_history_z(36m), lead = forward return. spec 의 "장기 평균회귀(예측)" = lead 측정 매칭. PASS. ★단 contemporaneous 는 valuation 예측이 아니라 동시 co-move(해석 분리).

| 국가 (ETF) | contemp Rank-IC (p) | lead k=1m (p) | lead k=3m (p) | lead k=6m (p) | half-split 부호일치 | n |
|---|---:|---:|---:|---:|:---:|---:|
| brazil (EWZ) | **+0.135** (0.005) | +0.011 (0.84) | −0.001 (0.98) | −0.020 (0.73) | True (둘 다 +) | 309 |
| mexico (EWW) | +0.005 (0.91) | −0.116 (0.026) | −0.090 (0.078) | −0.090 (0.082) | **False** (sign flip) | 361 |
| india (INDA) | +0.039 (0.59) | −0.067 (0.35) | −0.072 (0.30) | −0.023 (0.74) | True (둘 다 +, ≈0) | 170 |
| china (FXI) | −0.106 (0.088) | −0.061 (0.32) | −0.045 (0.48) | −0.044 (0.52) | True (둘 다 −) | 258 |
| korea (EWY) | +0.042 (0.51) | −0.071 (0.29) | −0.032 (0.62) | −0.029 (0.66) | True (둘 다 +, ≈0) | 311 |

- 다중비교: m=20, Bonferroni α/m=0.0025, raw p<0.05 **2/20**(brazil contemp +0.135, mexico lead1 −0.116), Bonferroni 생존 **0/20**, BH-FDR **0/20**.
- **해석**:
  - **brazil contemp +0.135 = 부호 반대(양)** → valuation 평균회귀(음 예측)와 무관, REER↑(통화강세 국면)에 ETF 도 동시 강세 = terms-of-trade 동시 co-move(commodity 통화). 예측 신호 아님.
  - **mexico lead −0.116(부호 prior 일치)**이나 half-split sign flip(rho1 −0.019 / rho2 +0.039) = 표본 의존, 불안정.
  - **china lead 전 음(부호 prior 일치) + half-split 둘 다 음(rho1 −0.110 / rho2 −0.205)** — 유일하게 valuation 평균회귀 방향성 일관, but p>0.08 비유의.
- **verdict = TENTATIVE DIRECTIONAL (china 약 방향성, 나머지 비유의/혼선)**: Bonferroni 0/20 생존. REER valuation 의 forward 예측력 = 전반적으로 약/비유의. **china 만** 부호 prior(고평가→약세) 일관(half-split 음 양쪽). brazil 의 +상관은 valuation 이 아닌 commodity-통화 동시성(별 채널). → block2 `real_exchange_rate_valuation` = **structural_low_confidence prior(validated_alpha:false)** 유지, china sub-archetype 한정 약 prior.

## §3. China credit impulse vs FXI/EWZ/EWY — **verdict: 동시 CONFIRMED(robust) / 예측-lead REJECTED (spec drift)**

**spec↔code 1:1 + ★spec drift 발견**:
- spec(yaml line 159·25): "China credit impulse↑ → **6~12개월 lag** 로 원자재·원자재수출국 지수 **선행**(예측)". block2 transform=yoy, lag=2.
- code: driver = **credit impulse = Δ(YoY% of total credit)** = 2차 차분(표준 credit-impulse 정의). ADF(credit level) t=**+2.48** > −2.86 → I(1) → YoY/Δ 사용(§1.7-B 정합). impulse coverage 1986-Q4~2025-Q3 (n_q≈156). target = FXI/EWZ/EWY **quarterly** log-return. contemporaneous(동분기) + lead k=1/2/3/4Q.
- Verify: spec 의 핵심 동사 = "**lead 6-12m 선행(예측)**". code 의 **lead k=2~4Q(=6~12m)** 가 spec 매칭 축. contemporaneous 는 spec 아님(별 해석). ★결과 = lead 축이 spec, 아래 표.

| 대상 (ETF) | contemp 동분기 Rank-IC (p) | lead 1Q (p) | lead 2Q (p) | lead 3Q (p) | lead 4Q (p) | n |
|---|---:|---:|---:|---:|---:|---:|
| china (FXI) | **+0.413** (0.0000) | +0.054 (0.60) | −0.047 (0.65) | −0.198 (0.036) | −0.095 (0.37) | 83~86 |
| brazil (EWZ) | **+0.303** (0.0005) | +0.010 (0.92) | +0.005 (0.96) | −0.046 (0.66) | +0.021 (0.83) | 100~103 |
| korea (EWY) | **+0.427** (0.0000) | −0.046 (0.67) | −0.058 (0.54) | −0.092 (0.35) | −0.121 (0.27) | 101~104 |

- 다중비교: m=15, Bonferroni α/m=0.0033. raw p<0.05 **4/15**. Bonferroni 생존 **3/15 = 전부 contemporaneous**(china/brazil/korea 동분기, p≤0.0005). **lead(예측) 측정은 전부 비유의**(china lead3Q −0.198 p=0.036 raw 1건이나 부호 **음** = prior(양) 반대 + Bonferroni 탈락).
- **★spec↔code drift 발견 (감사 §1.3·E97)**: yaml spec = "credit impulse **6-12m 선행(예측)**". 실측 = **동분기 co-movement 만 robust(Rank-IC +0.30~+0.43, Bonferroni 생존), forward lead 1-4Q 는 전부 비유의/부호반전**. 즉 credit impulse 는 china/brazil/korea 지수와 **동시(contemporaneous) 강 동조**하나 **선행 예측력 없음**.
- **verdict**:
  - **contemporaneous co-movement = ★CONFIRMED(robust)**: china/brazil/korea Rank-IC +0.30~+0.43, HAC-t +3.5~+5.3, Bonferroni 3/3 생존, n=83~101. credit cycle 과 EM 지수의 동시 동조 = 강 신호.
  - **lead/예측(spec 의 "선행") = ★REJECTED**: lead 1-4Q 전부 비유의(부분 음 부호). yaml 의 "6-12m 선행" 박제는 **본 표본(quarterly, revised credit)에서 미지지** → 격하.
- ★해석 caveat: credit 은 revised+분기 후행발표라 동시상관에 **lookahead/동시성 오염** 가능(D축). 동시 robust 도 라이브 사이징엔 vintage(ALFRED first-release) 재검 의무. block2 `china_credit_impulse` = **동시 regime-coincident 지표(coincident, NOT leading)** 로 라벨 정정, lag=2(선행) 박제 격하.

## §4. fx_carry_momentum vs 해당국 ETF — **verdict: 동시 CONFIRMED(robust, EM) / 예측-lead REJECTED**

**spec↔code 1:1**:
- spec(yaml line 143·28): unhedged 환은 1차 driver. carry=금리차, momentum=환율 3-12m 추세. 부호 prior = USD/local 상승추세(local 약세) → unhedged ETF return **음**.
- code: driver = **FX momentum = log(local_per_USD_t / local_per_USD_{t−h})**, h=3/12m (상승 = local 약세). target = 해당국 ETF monthly log-return. contemporaneous + lead k=1/3m. ADF(log FX) t=−0.97~−3.80(대부분 I(1), mexico −3.80 만 경계) → momentum=h-기간 차분이라 정상 근사.
- Verify: USD/local momentum↑(local 약세) ↔ unhedged ETF return. 부호 prior 음. PASS.

| 국가 (ETF) | h | contemp Rank-IC (p) | lead 1m (p) | lead 3m (p) | half-split 부호일치 | n |
|---|---|---:|---:|---:|:---:|---:|
| japan (EWJ) | 3m | −0.111 (0.047) | −0.023 (0.69) | +0.043 (0.42) | True | 362 |
| japan (EWJ) | 12m | −0.074 (0.22) | −0.038 (0.50) | −0.048 (0.41) | **False** | 362 |
| brazil (EWZ) | 3m | **−0.432** (0.0000) | −0.012 (0.82) | −0.024 (0.69) | True | 310 |
| brazil (EWZ) | 12m | **−0.192** (0.0002) | +0.012 (0.83) | +0.034 (0.58) | True | 310 |
| india (INDA) | 3m | **−0.340** (0.0000) | +0.017 (0.80) | −0.061 (0.39) | True | 171 |
| india (INDA) | 12m | −0.167 (0.008) | +0.056 (0.44) | +0.060 (0.34) | True | 171 |
| korea (EWY) | 3m | **−0.281** (0.0000) | +0.044 (0.46) | +0.007 (0.89) | True | 312 |
| korea (EWY) | 12m | −0.118 (0.036) | +0.055 (0.37) | +0.011 (0.85) | True | 312 |
| mexico (EWW) | 3m | **−0.349** (0.0000) | +0.004 (0.93) | +0.053 (0.26) | True | 362 |
| mexico (EWW) | 12m | −0.119 (0.017) | +0.064 (0.21) | +0.117 (0.020) | True | 362 |

- 다중비교: m=30, Bonferroni α/m=0.0017. raw p<0.05 **10/30**. Bonferroni 생존 **5/30 = 전부 contemporaneous 3m**(brazil/india/korea/mexico mom3 + brazil mom12). BH-FDR 생존 **6/30**(동일 + india mom12). **lead(예측) 측정 전부 비유의**.
- **해석**:
  - **EM(brazil/mexico/india/korea) contemporaneous mom_3m = ★CONFIRMED(robust)**: Rank-IC −0.28~−0.43, HAC-t −5.5~−12.7, Bonferroni 생존, half-split 부호 일치. **부호 prior(local 약세→ETF 음) 강 일치**. unhedged EM ETF 의 환 채널이 1차 driver = lens "환을 빼면 절반 놓친다"(pricing_principle) **강 지지**.
  - **japan = 약(mom3 −0.111 raw p=0.047, Bonferroni 탈락, mom12 half-split flip)** — 일본은 환↔지수 동조 약(수출주 엔약세 수혜로 상쇄, lens "헤지/언헤지 분기 핵심" 정합).
  - **lead/예측 전부 REJECTED**: 환 모멘텀의 **forward 예측력 없음**(전 lead p>0.2, Bonferroni 0). 즉 동시 환 효과는 mechanical(unhedged 가격 = 현지지수×환율 동시 반영), 미래 예측 신호 아님.
- **verdict**:
  - **EM 환 동시 채널 = ★CONFIRMED(robust, 부호 일치)** — block2 `fx_carry_momentum` 의 **contemporaneous 환 노출**은 EM 에서 강·robust.
  - **환 momentum 예측(lead) = ★REJECTED** — block5 `fx_sleeve_promotion` 의 "native 신호" 가 예측 alpha 라면 미지지. 단 **현재 환노출 사이징(동시 베타)** 용도면 robust.
  - ★sleeve 승격 함의: fx 의 가치 = 예측 alpha 가 아니라 **현재 환 익스포저를 명시 사이징**(unhedged risk decomposition)에 있음. cap(0.04) 부당 여부는 "예측 IC" 가 아닌 "환 베타 robust" 근거로 재평가 필요.

## §5. 12축 audit-ready 표

| 축 | 본 산출 충족 | 근거 |
|---|---|---|
| **A 이론 학습** | 부분 | lens report_relations(엔/REER/credit/carry) 기반, 본 md 는 실측 전담(이론은 direction.md/lens) |
| **B 실데이터 시계열** ★ | **충족** | FRED+yfinance 실 fetch(raw/merit_cache JSON), n=83~448, HAC-t/p/95%CI/Rank-IC 박제. 합성 아님 |
| **C yaml 도출 추적성** ★ | 충족(본 md 까지) | 모든 수치 raw/validation-merit-output.txt 재현. ★yaml 직접수정 금지 — main verdict+audit 후 |
| **D PIT/lookahead** ★ | **부분(caveat 박제)** | ETF TR=PIT-safe / FRED REER·credit·금리=revised(개정치) → lookahead 위험 명시, 라이브 직박제 금지·ALFRED vintage 후속 의무 |
| **E 자문비판+환각** | 충족 | 외부 prior 인용 없음(primary FRED/yfinance 직측). 환각 ref 0 |
| **F 반증+기각** | **충족** | JGB-UST INSUFFICIENT/REJECTED, REER lead 비유의, credit lead REJECTED(spec drift), fx lead REJECTED = 기각 다수 |
| **G effective-N/검정력** | 충족(tier 라벨) | quarterly credit n_q≈156(effective↓, 자기상관), monthly n=171~362. Rank-IC HAC-t 로 검정력 표기 |
| **H 미해결 의문** | 충족 | §6 |
| **I 무결성·생존편향** ★ | 충족 | ETF=현존 단일국 대형 ETF(상폐 없음), auto_adjust split/배당 반영. FRED 무결 |
| **J 경제유의성·거래비용** | N/A(탐구 단계) | 본 단계는 신호 탐구 — turnover/비용 차감은 sleeve 승격 백테스트 시 |
| **K 다중검정 보정** ★ | **충족** | 지표별 Bonferroni α/m + BH-FDR + raw p<0.05 카운트 박제(§1~4). 시도횟수 = 지표별 m=4/20/15/30 공시 |
| **L 통합 상관행렬** ★ | 충족(caveat) | credit/fx 동시 co-move 는 dollar 채널(macro-linkage β_dollar)과 **중복 risk** — 통합 시 공통인자 1회 계상(L축). fx 환 = β_dollar 와 같은 베팅 |

## §6. 미해결 의문 (H축)

1. **동시 vs 예측의 본질적 분리**: credit·fx 모두 동시(contemporaneous) robust + 예측(lead) 비유의. 이는 (a) 환·credit 이 ETF 가격에 동시 반영(mechanical) (b) 시장이 이미 가격에 선반영 — 둘 구분 미해결. 라이브 가치 = "현재 노출 사이징" 한정(예측 alpha 아님).
2. **credit revised 오염**: QCNPAMUSDA 분기 발표 + 사후 개정 → 동시상관에 lookahead 혼입 가능. ALFRED first-release vintage 로 재측정 시 동시 Rank-IC 감쇠 가능성.
3. **brazil REER +상관 부호반전**: valuation(평균회귀 음 예측)과 반대 = commodity-통화 동시성. terms_of_trade 를 REER 대신 직접 수출가격/수입가격 지수로 재정식화 시 부호 분리 가능(미탐구).
4. **fx-dollar 중복(L축)**: EM fx momentum(−0.43)과 macro-linkage β_dollar(−1.1~−1.4)는 같은 환 채널 — 통합 시 이중계상 위험. partial-corr(dollar 고정 후 local-fx 잔차) 미측정.
5. **JGB-UST 양면성**: spread 자체 비유의이나, regime-conditional(엔 carry-trade unwind 국면) 한정 효과 가능성 미탐구.

## §7. 종합 verdict (4 지표)

| 지표 | verdict | 핵심 근거 |
|---|---|---|
| **JGB-UST spread** | **★INSUFFICIENT/REJECTED** | 동시·예측 전부 \|Rank-IC\|<0.06 p>0.28, Bonferroni 0/4. yaml line 274 caveat = "누락이 결함 아님"(이 spread 는 EWJ 월간 return 비유의)로 해소 |
| **REER (terms_of_trade/valuation)** | **TENTATIVE DIRECTIONAL** | Bonferroni 0/20. china 만 부호 prior(고평가→약세) 일관(half-split 음 양쪽, p=0.088). structural_low_confidence prior 유지(validated_alpha:false) |
| **China credit impulse** | **동시 ★CONFIRMED(robust) / 예측-lead ★REJECTED** | 동분기 Rank-IC +0.30~+0.43 Bonferroni 3/3 생존. lead 1-4Q 전부 비유의 → "6-12m 선행" spec drift, **coincident** 로 라벨 정정 |
| **fx_carry_momentum** | **동시 ★CONFIRMED(robust, EM) / 예측-lead ★REJECTED** | EM mom_3m Rank-IC −0.28~−0.43 Bonferroni 생존 부호 일치. lead 전부 비유의 → 예측 alpha 아님, **현재 환 노출 사이징**용. japan 약 |

★ **공통 발견**: 4 지표 중 credit·fx 는 **동시 co-movement 가 강·robust**(mechanical 채널)하나 **forward 예측력은 전무**. JGB-UST·REER 는 동시·예측 모두 약. yaml 의 "lead/선행" 박제(credit lag=2, REER lag=1 valuation, fx native 예측)는 **본 표본에서 미지지** → coincident/exposure 라벨로 정정 의무(예측 alpha 박제 금지).
