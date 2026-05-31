---
tags: [type/validation, hypothesis/H1, study/eq_us_defensive, phase/2-3, version/v3]
date: 2026-05-31
hypothesis: H1 — Real Rate Sensitivity Dichotomy
verdict: ★PARTIAL — contemporaneous co-movement CONFIRMED / predictive 3M FAILS (spec/impl drift 정정)
---

# validation-H1.md — Real Rate Sensitivity Dichotomy 실측 (v3)

**분석 unit (β 측정)**: DEFENSIVE_PURE = {XLU, XLP, XLV, XLC mature} (rate-NEG bond proxy) / FINANCIALS = {XLF} (rate-POS, NIM)
**Portfolio label**: "미국 방어주 + 금융주" sleeve (user task label)
**Spec ↔ Code 1:1 verify** (rule §1.3):
- v2 spec 원문: "DFII10 1σ 상승 → XLU 향후 3M 선도수익률 음의 영향" (★predictive forward 3M)
- v2 코드: `corr(d_DFII10, daily_ret)` = same-day contemporaneous (★drift)
- ★v3 정정: contemporaneous 와 predictive 분리 측정, verdict 도 분리

## 가설 (direction.md §H1)

원안 spec text: **다른 매크로 통제 시 DFII10 1σ 상승 → XLU/XLP 향후 3M 선도수익률 음의 영향 + XLF 양의 영향**

- Anchor: Ilmanen (2011) bond proxy / Boyd-Gertler-Bernanke (1994) 은행 대차대조표 채널
- Prior: XLU/XLP NEG (-0.5 ~ -0.7 합성 시뮬), XLF POS (+0.4 ~ +0.6 합성 시뮬) — ★n<30 합성 시뮬 폐기 (rule §1)

## 데이터

- **FRED DFII10** (10Y TIPS yield, real rate, spot only) — 2003-01-02 ~ 2026-05-28 (n=5844 일)
- **ETF**: XLP, XLU, XLV, XLF, XLC, SPY (Yahoo Finance, 2003-01 이후 join — XLC 는 2018-06 이후)
- **Coverage**: 두 시리즈 inner join (실 표본 = 2003-01-03 ~ 2026-05-28, 누락 0)
- **ALFRED PIT**: 미보유 — DFII10 vintage 없음 (실측 정확성 한계, handoff-bugfix §데이터 결함 #7)
- **분석 .py**: `raw/run_validation.py` (v3 USE_FORWARD_3M=True)

## 방법 — Contemporaneous (v2 측정)

1. 일별 ΔDFII10 (real rate change)
2. 일별 sector return
3. Pearson β (rate sensitivity): `β = cov(r_sector, ΔDFII10) / var(ΔDFII10)`
4. Spearman rank-IC (전체 + SPY-controlled partial)
5. Rolling 60D β + sign-flip rate (시간 가변성)

## 방법 — Forward 3M Predictive (★v3 신규)

1. 월별 DFII10 last value → ΔDFII10_m
2. 월별 sector return → forward 3M sum return (t+1 ~ t+3 누적)
3. Spearman rank-IC + SPY-controlled partial
4. n=월 표본 (~280 months)

## 결과 (1) Contemporaneous — 전체 표본 (n=5844)

| sector | β | rankIC | p | partial IC \| SPY | partial p | n |
|---|---:|---:|---:|---:|---:|---:|
| **XLU** | -0.0106 | -0.070 | <0.0001 | **-0.167** | **<0.0001** | 5844 |
| **XLP** | +0.0114 | +0.053 | 0.0001 | **-0.040** | 0.0025 | 5844 |
| XLV | +0.0150 | +0.081 | <0.0001 | -0.011 | 0.3848 | 5844 |
| **XLF** | +0.0462 | +0.170 | <0.0001 | **+0.129** | **<0.0001** | 5844 |
| XLC | -0.0191 | -0.084 | 0.0002 | -0.046 | 0.0416 | 1980 |
| SPY | +0.0218 | +0.115 | <0.0001 | N/A | N/A | 5844 |

### 결과 (1.5) Rolling 60D rate beta 시간 가변성

| sector | mean β | std | sign-flip rate |
|---|---:|---:|---:|
| XLU | -0.0218 | 0.0586 | 33.4% |
| XLP | +0.0105 | 0.0421 | 42.6% |
| XLV | +0.0196 | 0.0519 | 38.2% |
| **XLF** | +0.0640 | 0.0827 | **25.0%** (가장 안정) |
| XLC | -0.0100 | 0.0719 | 38.7% |

## 결과 (2) Forward 3M Predictive — ★v3 신규 실측 (spec text 매칭, n=277 월)

| sector | rankIC_fwd3M | p | partial IC \| SPY | partial p | n |
|---|---:|---:|---:|---:|---:|
| XLU | +0.017 | 0.7764 | **-0.006** | **0.9157** | 277 |
| XLP | -0.052 | 0.3879 | **-0.065** | 0.2827 | 277 |
| XLV | +0.039 | 0.5213 | +0.028 | 0.6454 | 277 |
| XLF | -0.032 | 0.5971 | **-0.035** | 0.5592 | 277 |
| XLC | -0.049 | 0.4180 | +0.079 | 0.1874 | 277 |
| SPY | -0.069 | 0.2534 | N/A | N/A | 277 |

★v3 fwd3M sign split: **FAIL** (XLU/XLP NEG 동일이지만 XLF 도 NEG = spec text 와 불일치).
모든 sector partial p > 0.18 → predictive 채널 무효 (rule §2 REJECTED).
handoff main 독립검증 anchor 와 정합 (XLU ~-0.004 vs 본 측정 -0.006).

## 평가

### ★v3 verdict: PARTIAL (spec/impl 분리)

**Contemporaneous (same-day)**:
- XLU partial IC = -0.167 (p<0.0001) — sign split 확인. CONFIRMED (n=5844, 단 hedge 어휘: same-day co-movement 한정)
- XLF partial IC = +0.129 (p<0.0001) — sign split 확인. CONFIRMED (동일 hedge)
- **Spec text 와 lag 일치 X** — 본 결과는 same-day 공동 변동성, predictive 채널 X

**Forward 3M Predictive (spec text 직접 매칭)**:
- 세 sector 모두 partial IC ~0, p>0.3 — ★FAILS (predictive 채널 무효)
- 자문 prior 의 predictive 가정이 실데이터에서 미관측 (시장 효율성 가설과 정합)

**v3 격하 결론** (rule §2 verdict 5단계):
- contemporaneous channel: CONFIRMED (n=5844 충분, 단 spec text 와 lag 불일치)
- predictive 3M channel (★spec text 원안): FAILS (rule §2: REJECTED)
- ★단정 "강력" 어휘 철회 (rule §2): hedge 어휘 적용 — "방향성 약 prior" 격하

### 합성 prior vs 실측 (★격하)

| sector | 합성 prior | 실측 contemp | 실측 fwd3M (partial) | 평가 |
|---|---:|---:|---:|---|
| XLU | -0.5 ~ -0.7 (n=240 합성, ★폐기) | -0.167 | -0.006 (p=0.92) | contemp 1/3 강도 / fwd 무효 |
| XLP | -0.3 ~ -0.5 | -0.040 | -0.065 (p=0.28) | contemp 1/8 / fwd 무효 |
| XLV | -0.1 (mild NEG) | -0.011 (무유의) | +0.028 (p=0.65) | 사실상 무효 |
| XLF | +0.4 ~ +0.6 | +0.129 | -0.035 (p=0.56) | contemp 1/3 / fwd 부호 reversed (무효) |
| XLC | -0.1~-0.2 | -0.046 | +0.079 (p=0.19) | contemp 1/3 / fwd 부호 reversed (무효) |

→ contemp 채널만 부호 정합, 강도 약함. **predictive 채널 (spec text 원안) 전 sector 무효**.

### 시간 가변성 (참조)

- XLU sign-flip 33%, XLP 43% — bond proxy 효과 시간 가변성 1/3~1/2 시기는 부호 반대
- XLF sign-flip 25% — 가장 안정 (NIM 이론 지속력 높음)
- → R3 H1 의 "120M rolling p.corr" 검증 design 정당화 — 시간 가변성 명확

## 코드화 권고 (yaml 반영, v3)

### relationships (블록3) — lag_routing 명시

```yaml
- {node_a: real_rate_dfii10, node_b: XLU_return, edge_type: direct,
   conditioning_set: [SPY_return], lag_routing: contemporaneous,
   prior_sign: neg, prior_strength: 0.17,
   theory_basis: "★v3 실측: contemporaneous partial IC=-0.167 p<0.0001 (n=5844). predictive fwd3M FAILS (~0, p>0.3). 본 prior 는 same-day co-movement 한정"}

- {node_a: real_rate_dfii10, node_b: XLF_return, edge_type: direct,
   conditioning_set: [SPY_return], lag_routing: contemporaneous,
   prior_sign: pos, prior_strength: 0.13,
   theory_basis: "★v3 실측: contemporaneous partial IC=+0.129 p<0.0001 (n=5844). predictive fwd3M FAILS. NIM lag 채널 직접 검증 X"}
```

### weight_rules (블록4) — base_weight hedge 적용

```yaml
- {indicator_id: rate_beta, base_weight: 0.08,  # v2 0.10 → v3 0.08 (predictive FAILS 격하)
   modulate_by: [regime, industry, name_specific],
   direction: "★v3 hedge: contemporaneous sign split CONFIRMED (utility/staples NEG, banks POS), predictive 3M FAILS. lag_routing=contemporaneous 한정. 시간 가변성 25~43%. ALFRED PIT 미보유 → vintage 정확성 한계",
   granularity: ticker}
```

### confidence_hooks 갱신 경로

- **confirm condition (contemp)**: 120M rolling partial IC 가 prior 부호 유지 + |IC| > 0.05 가 60% 이상 기간
- **reject condition (contemp)**: partial IC 부호 반전 12M 지속 또는 rolling sign-flip > 50%
- **predictive fwd3M monitor**: rolling 60M predictive partial IC 가 |IC| > 0.05 + p<0.10 등장 시 spec text 재정의 검토 (현재 무효)
- **action**: confirm → base_weight 0.08 유지 / reject → rate_beta 가중 0.04 강등

## 한계 (★v3 명시)

- **Spec/impl drift**: v2 verdict "★CONFIRMED 강력" = predictive 라 주장 + 코드 contemporaneous → main 독립검증으로 fix
- DFII10 ALFRED PIT 미보유 → vintage X spot only, predictive 재검증 정확성 한계 (handoff §데이터 결함 #7)
- 일별 ΔDFII10 vs 일별 return = high-frequency noise. 월별 aggregate 시 partial IC 약 + fwd3M 무효
- partial-corr conditioning = SPY only. R2 권고 `{SPY, ΔVIX, ΔOAS}` 확장 필요 (다음 cycle)
- XLV (healthcare) 무유의 → real rate 채널이 healthcare 에 약함. sub-archetype 분해 (pharma vs HMO) 필요
- 2003-01 시작 = QE 이전 vintage 없음. Pre-QE rate beta 비교 불가
- n<30 합성 prior 박제 금지 (rule §1.5) — v1 합성 시뮬값 전량 폐기

## 참조

- `run_validation.py` H1 contemp block (line 60-128) + H1 forward 3M block (★v3 신규 line 130+)
- `validation-metrics.json` h1_real_rate_dichotomy_contemporaneous + h1_real_rate_dichotomy_forward_3m
- direction.md §H1 (가설 원문)
- raw/round-1.md (Ilmanen·Boyd-Gertler anchor)
- handoff-bugfix-v3-20260530.md §3 (spec/impl drift 발견)
- ~/.claude/rules/empirical-claim-presentation.md §1.1 (coverage) + §1.3 (spec/code 1:1) + §1.6 (분석 unit ↔ portfolio label)
- ~/.claude/memory/promotion-log.md ERROR-202605302130 (v3 보수 trigger)
