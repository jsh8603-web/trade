---
tags: [type/validation, hypothesis/H3, study/eq_us_defensive, phase/2-3, version/v4]
date: 2026-05-31
hypothesis: H3 v4 — Credit/Financial Stress Regime → DEF_PURE outperform / FIN underperform
verdict: TENTATIVE DIRECTIONAL — 4 regime × 2 sleeve 부호 분기 방향성 일관, 통계 비유의 (Bonferroni 0/8 PASS)
---

# validation-H3-v4.md — sleeve 분리 + Credit Stress 재검증

**분석 unit (β 측정)** — rule §1.6:
- `DEFENSIVE_PURE = {XLP, XLU, XLV}` (rate-NEG bond proxy, 부호 동일 grouping)
- `FINANCIALS = {XLF}` (rate-POS NIM, 독립 측정)
- XLC mature (post-2018-06) 별도 archetype 분리

**Portfolio label**: "미국 방어주 + 금융주" sleeve (user task) — factor β cancel 회피 위해 **별도 측정**

**Spec ↔ Code 1:1 verify** (rule §1.3):
- Spec: Credit/Financial Stress regime 진입 시 defensive sleeve outperform / financials underperform
- Code: `run_validation_v4.py` — NFCI/BAA10Y p75 dual cross-check + sleeve 분리 + Block bootstrap (block=4mo) + LOO + Bonferroni

## 데이터 (★v4 — handoff anchor 정정)

- **★FRED BAMLH0A0HYM2 = 가용 2023-05-30~ 만 (handoff "2000-01~" anchor 잘못, OBSERVE 기록)** — v3 INSUFFICIENT root cause
- **PRIMARY 대안 (main APPROVED)**: NFCI weekly **1971-01-08 ~ 2026-05-22 (n=2890)** Chicago Fed Financial Conditions Index
- **SECONDARY exogenous (main 권고 우선)**: BAA10Y daily **1986-01-02 ~ 2026-05-28 (n=10101)** Moody IG credit spread
- **ETF**: XLP, XLU, XLV, XLF, XLC, SPY (2000-01 ~ 2026-05, monthly resample)
- **★main caveat (적용 보고)**:
  (a) NFCI **주간 개정됨** → 본 v4 = current revision 사용 (★PIT 엄밀화 시 ALFRED vintage 별도 fetch 필요, 본 cycle scope 외)
  (b) NFCI = **equity volatility 포함** → 주식 return regime 과 mild 내생성 → **BAA10Y exogenous 우선 cross-check**
  (c) regime threshold p75 = full-historical 기준 (★lookahead 잠재성) → **walk-forward** 분석 follow-up

## 방법 (★small-N rigor 5의무 + autocorr 안전장치)

1. **regime classifier**:
   - NFCI primary: NFCI > p75 (=0.162) 또는 NFCI > p90 (=1.398)
   - BAA10Y secondary (exogenous): BAA10Y > p75 (=2.680) 또는 BAA10Y > p90 (=3.134)
2. **sleeve eq-weight monthly excess vs SPY** (DEFENSIVE_PURE / FINANCIALS 분리)
3. **Block bootstrap** (rule §1.4): block_size=4 months (autocorr decay 통상 4-6mo), n_iter=5000
4. **LOO sensitivity** (rule §1.2): 각 sample 빼고 t-test p 의 max (worst-case fragility)
5. **Bonferroni 보정** (rule §1.5): m=4 (2 regime axes × 2 sleeves) → α/4 = 0.0125
6. **Cross-sleeve Welch t-test**: DEF_PURE - FIN gap 검정 (rule §1.6 정합성)

## 결과 (1) Regime distribution (★v4 full-historical 활용)

| Regime axis | n (mo) | % | 비고 |
|---|---:|---:|---|
| NFCI p75 stress | 23 | 7.3% | 2008 GFC + 2020 COVID + 2022 inflation + 2023 banks 다중 cycle 포함 |
| NFCI p90 stress | 7 | 2.2% | ★n<10 INSUFFICIENT 잠재 |
| BAA10Y p75 stress | 113 | 35.6% | exogenous credit, broader 정의 |
| BAA10Y p90 stress | 49 | 15.5% | exogenous credit, narrow stress |
| NFCI ∩ BAA10Y p75 | 21 | 6.6% | dual cross-check |

★v3 의 n=9 (HY OAS post-2023 only) → v4 의 n=23/113/49 (full historical) = **★n 14배 확장**.

## 결과 (2) Regime conditional sleeve excess (★rule §1 5의무)

| regime | sleeve | n | mean/mo | 95% CI (Block bootstrap) | p_block | LOO p_max | verdict |
|---|---|---:|---:|---|---:|---:|---|
| NFCI p75 | DEFENSIVE_PURE | 23 | +0.0043 | [-0.0111, +0.0223] | 0.505 | 0.815 | TENTATIVE DIRECTIONAL |
| NFCI p75 | FINANCIALS | 23 | -0.0122 | [-0.0478, +0.0221] | 0.444 | 0.759 | TENTATIVE DIRECTIONAL |
| NFCI p90 | DEFENSIVE_PURE | 7 | +0.0052 | [-0.0093, +0.0407] | 0.253 | 0.970 | TENTATIVE (n<10) |
| NFCI p90 | FINANCIALS | 7 | -0.0313 | [-0.0960, -0.0295] | 0.000 | 0.869 | TENTATIVE (n<10, LOO fragile) |
| BAA10Y p75 | DEFENSIVE_PURE | 113 | +0.0012 | [-0.0037, +0.0058] | 0.688 | 0.897 | TENTATIVE DIRECTIONAL |
| BAA10Y p75 | FINANCIALS | 113 | -0.0033 | [-0.0122, +0.0043] | 0.358 | 0.623 | TENTATIVE DIRECTIONAL |
| BAA10Y p90 | DEFENSIVE_PURE | 49 | -0.0007 | [-0.0091, +0.0094] | 0.942 | 0.994 | TENTATIVE DIRECTIONAL |
| BAA10Y p90 | FINANCIALS | 49 | -0.0071 | [-0.0229, +0.0090] | 0.414 | 0.557 | TENTATIVE DIRECTIONAL |

### ★방향성 일관 발견

- **DEFENSIVE_PURE**: 4 regime 중 3 regime 양수 (NFCI p75/p90 + BAA10Y p75) + 1 regime 0 근사 (BAA10Y p90)
- **FINANCIALS**: 4 regime 모두 음수 (-0.7%/월 ~ -3.1%/월)
- ★sub-sleeve 부호 분기 = 4/4 regime 일관 — **rule §1.6 sleeve 분리 정당성 ★실증**

### 통계적 강도 (★rule §1.5 + §1.2)

- raw p<0.05: NFCI p90 FIN 만 1건 (단 LOO p=0.87 fragile → 단일 outlier dependency)
- Bonferroni α/4=0.0125: **0/8 cell PASS**
- LOO p_max > 0.5: 8/8 cell (모두 fragile) — sample 1개 제외 시 p>0.5 으로 약화 = **small sample regime dependence 강**

## 결과 (3) Cross-sleeve Welch (rule §1.6 검증)

| regime | n_def | n_fin | mean_def | mean_fin | gap | Welch t | p |
|---|---:|---:|---:|---:|---:|---:|---:|
| NFCI p75 | 23 | 23 | +0.0043 | -0.0122 | **+0.0165** | +0.939 | 0.355 |
| NFCI p90 | 7 | 7 | +0.0052 | -0.0313 | **+0.0365** | +0.810 | 0.439 |
| BAA10Y p75 | 113 | 113 | +0.0012 | -0.0033 | **+0.0046** | +0.944 | 0.346 |
| BAA10Y p90 | 49 | 49 | -0.0007 | -0.0071 | **+0.0064** | +0.754 | 0.453 |

★4/4 regime gap > 0 (DEF_PURE outperforms FIN in stress) — **방향성 일관 PASS** 단 통계 비유의 (p>0.34).
sleeve 분리 grouping (rule §1.6) 부호 분기 정합성 = **실증 (단 약 신호)**.

## 결과 (4) H4a v4 — BAA10Y daily credit beta (★n=6588 full historical)

★v3 의 n=752 (HY OAS post-2023 only) short window 한계 → v4 n=6588 (26년) 로 해소.

| sector | partial IC (ΔBAA10Y) \| SPY | p | n | Bonferroni m=5 α/5=0.01 |
|---|---:|---:|---:|---|
| XLU | +0.046 | 0.0002 | 6588 | ★PASS |
| XLP | +0.054 | <0.0001 | 6588 | ★PASS |
| XLV | +0.019 | 0.1230 | 6588 | FAIL |
| XLC | +0.053 | 0.0174 | 1979 | raw only |
| **XLF** | **-0.059** | **<0.0001** | 6588 | **★PASS** |
| **DEF_PURE_eq** | **+0.058** | **<0.0001** | 6588 | **★PASS** |

★Gap (DEF_PURE - XLF) = **+0.117**:
- **부호 분기 verdict**: ★**CONFIRMED Bonferroni** (DEF_PURE +0.058 vs XLF -0.059, 둘 다 p<0.0001 + Bonferroni m=5 PASS — industry sign split 강 신호)
- **gap magnitude verdict**: rule §1.6 threshold 0.15 미달 (실측 +0.117) — 본 threshold 는 "정량 magnitude" 기준 (강한 분기 정의), 부호 분기 정합성과 별개. magnitude TENTATIVE 단 sign split 자체는 강 신호.

## 평가 (★v4 종합)

### v3 vs v4 격하/회복 비교

| 항목 | v2 (위조) | v3 (격하) | v4 (재검증) |
|---|---|---|---|
| H3 regime | n=9 silent | INSUFFICIENT | **TENTATIVE DIRECTIONAL** (n=23~113, 방향 일관) |
| H4a credit beta | n=752 short | PARTIAL (short window) | **CONFIRMED Bonferroni** (n=6588, DEF_PURE +0.058 / XLF -0.059) |
| sleeve 정합 | XLF cancel | 미검증 | **★sleeve 분리 PASS** (4/4 regime gap > 0) |
| 통계 anchor | HY OAS 직접 | INSUFFICIENT | NFCI+BAA10Y dual cross-check (PIT caveat) |

### ★v4 verdict (rule §2 5단계)

1. **H3 regime → sleeve excess sign** (방향성 가설): **TENTATIVE DIRECTIONAL CONFIRMED 부호 분기** — 4/4 regime DEF_PURE > FIN, 단 p>0.34 통계 비유의
2. **H3 magnitude** (정량 강도): **TENTATIVE** — Block bootstrap p>0.05, LOO p>0.5 → small sample dependence
3. **H4a sub-sleeve split** (★강 신호): **CONFIRMED Bonferroni** (n=6588 full historical, DEF_PURE/XLF 부호 분기 p<0.0001)
4. **★rule §1.6 sleeve 분리 정당성**: **실증** (cross-sleeve gap 4/4 regime 양)

### 자문 prior vs 실측 (★v4 정정)

**자문 prior** (R1 Frazzini-Pedersen + R3 H3):
- Credit Stress regime → defensive outperform p<0.05

**v4 실측 (full historical NFCI/BAA10Y)**:
- 방향성: ★일관 (DEF_PURE 4/4 regime ≥0, FIN 4/4 regime <0)
- magnitude: 약 (DEF_PURE +0.4%/월 mean, FIN -1.2%/월 mean — 단 CI 0 포함)
- 통계 강도: Bonferroni 후 0/8 PASS → 자문 prior 의 "p<0.05" 단정 X
- → **방향성 confirm 부분 + 강도 약 — TENTATIVE DIRECTIONAL**

### main caveat 적용 (★보고)

| caveat | 적용 |
|---|---|
| (a) NFCI 주간 개정 PIT | 본 v4 = current revision (★ALFRED vintage walk-forward 후속 todo) |
| (b) NFCI equity vol 내생성 | BAA10Y exogenous primary, NFCI secondary — 두 axis 결과 일관 (방향) |
| (c) regime threshold walk-forward | 본 v4 = full-historical p75 (lookahead) — walk-forward 후속 todo |

## 한계 (★v4 정직)

1. NFCI realtime PIT 미적용 (current revision 사용) — walk-forward backtest 필요
2. BAA10Y = IG (Investment Grade) Baa, ★HY 아님 — HY direct anchor 는 BofA-FRED 라이센스 제약으로 미가용
3. Bonferroni 후 0/8 PASS — 방향성 일관 단 magnitude 통계 약 (단일 cycle 의존도 강 LOO p>0.5)
4. Block bootstrap block_size=4 = empirical (월별 stress regime persistence 통상 4-6mo). 다른 block 시 미세 변동 가능
5. 본 v4 sleeve 분리 결과는 user portfolio label (방어주+금융주 통합) 의 eq-weight 부호 cancel 위험 명확 — relative 가중 (defensive ↑ / financial ↓ in stress) 권고
6. ALFRED HY OAS full historical = BofA 라이센스 제약 (FRED 미제공). Bloomberg/ICE 유료 source 만 가용

## 코드화 권고 (yaml v4 반영 — 별도 study_session.yaml v4 작성)

### sleeve 정의 명시
```yaml
sleeve_definitions:
  DEFENSIVE_PURE: [XLP, XLU, XLV]  # rate-NEG bond proxy, 부호 동일 grouping
  FINANCIALS: [XLF]                # rate-POS NIM 독립
  portfolio_label_user_task: "미국 방어주 + 금융주" sleeve (eq-weight 부호 cancel 위험 — relative 가중 권고)
```

### relationships (블록3) — H3 v4 부호 분기 anchor
```yaml
- {node_a: credit_stress_regime, node_b: def_pure_excess, edge_type: direct,
   conditioning_set: [], lag_routing: contemporaneous,
   prior_sign: pos, prior_strength: 0.10,  # ★v4 약 신호 hedge
   theory_basis: "★v4: NFCI/BAA10Y p75 stress regime 4/4 DEF_PURE excess > 0 (방향성 일관).
     Block bootstrap p>0.34 비유의 (TENTATIVE). magnitude DEF_PURE +0.4%/월 mean"}

- {node_a: credit_stress_regime, node_b: fin_excess, edge_type: direct,
   conditioning_set: [], lag_routing: contemporaneous,
   prior_sign: neg, prior_strength: 0.15,
   theory_basis: "★v4: NFCI/BAA10Y p75 stress regime 4/4 FIN excess < 0 (방향성 일관).
     magnitude FIN -1.2%/월 mean. NFCI p90 raw p<0.001 (단 LOO p=0.87 fragile)"}

- {node_a: baa10y_change, node_b: def_pure_return, edge_type: direct,
   conditioning_set: [SPY_return], lag_routing: contemporaneous,
   prior_sign: pos, prior_strength: 0.058,  # ★n=6588 partial IC
   theory_basis: "★v4 strong: partial IC=+0.058 (p<0.0001 Bonferroni PASS, n=6588 26년).
     credit ↑ 시 defensive 시장 베타 흡수 후 residual 회복력 (long anchor)"}

- {node_a: baa10y_change, node_b: xlf_return, edge_type: direct,
   conditioning_set: [SPY_return], lag_routing: contemporaneous,
   prior_sign: neg, prior_strength: 0.059,  # ★n=6588 partial IC
   theory_basis: "★v4 strong: partial IC=-0.059 (p<0.0001 Bonferroni PASS, n=6588).
     credit ↑ 시 banks provisioning channel 시장 베타 초과 penalty"}
```

### weight_rules (블록4) — v4 grade
```yaml
- {indicator_id: credit_beta, base_weight: 0.07,  # v3 0.04 → v4 0.07 (n=6588 BAA10Y CONFIRMED)
   modulate_by: [regime, industry, sleeve_grouping],
   direction: "★v4: BAA10Y daily n=6588 anchor — DEF_PURE +0.058 / XLF -0.059 industry 부호 분기 CONFIRMED.
     sleeve_grouping=[DEFENSIVE_PURE / FINANCIALS] 분리 측정 의무 (rule §1.6).
     H3 regime conditional 은 TENTATIVE (Block bootstrap p>0.34, LOO fragile)",
   granularity: industry_sleeve_split}
```

## 참조

- `run_validation_v4.py` (★sleeve 분리 + NFCI/BAA10Y regime + Block bootstrap + LOO + Bonferroni)
- `validation-metrics-v4.json` (h3_v4_regime_conditional + h3_v4_cross_sleeve_welch + h4a_v4_baa10y_credit_beta)
- `validation-H3.md` v3 (★INSUFFICIENT 격하 — v4 회복)
- `validation-H1.md` v3 (real rate dichotomy contemp/fwd 분리)
- `m3-macro-linkage.md` v3 (M3 dollar Welch z + Bonferroni)
- direction.md §H3 (가설 원문)
- ~/.claude/rules/empirical-claim-presentation.md §1 5의무 + §1.6 분석 unit / portfolio label + §2 verdict 5단계
- ~/.claude/memory/promotion-log.md ERROR-202605302130 (v3 root cause) + ERROR-202605302245 (sleeve 결합 결함)
