---
tags: [type/macro-linkage, study/eq_us_defensive, phase/M3, version/v3]
date: 2026-05-31
study_id: eq_us_defensive
target: main M4 factor seed
ref: study-research/macro/timeline.md §4
verdict: ★v3 격하 — M1 dollar 채널 "강력 확인 / 2배" 단정 철회 (Welch z=1.34 p_diff=0.18 비유의)
---

# M3 거시연관 — eq_us_defensive sleeve vs Macro Factor (v3)

> macro/timeline.md §4 가이드 준수: (1) epoch별 sleeve 분해 (2) macro driver loading 회귀 (3) cross-asset vs within-sleeve 구분 → main M4 factor seed 입력

**분석 unit (β 측정)**: DEFENSIVE_PURE = {XLP, XLU, XLV} / FINANCIALS = {XLF} / XLC mature 별도
**Portfolio label**: "미국 방어주 + 금융주" sleeve
**v3 fix 핵심**: Welch z-test for β_dxy(E3) vs (E4) gap + Bonferroni 보정 (m=4 → α/4=0.0125) 부착

## 데이터

- **FRED**: DGS10 (rate), DFII10 (real_rate), DTWEXBGS (DXY broad), BAMLH0A0HYM2 (HY OAS)
- **ETF**: XLP, XLU, XLV, XLF, XLC, SPY (Yahoo Finance)
- **분석 .py**: `raw/m3_macro_linkage.py` (★v3 ols_loading SE 반환 + Welch z 추가)
- **표본 범위**: 일별 2023-05-31 ~ 2026-05-22 (n=742 일) — HY OAS 일별 시리즈 가용 한계
- **Epoch labels** (timeline §3): E0 pre-2022 / E1 긴축 2022Q1~Q3 / E2 전환 2022Q4~2023Q2 / E3 재상승 2023Q3 (n=63 일) / E4 pivot 2023Q4~ (n=657 일)

## (1) Epoch별 sleeve excess return (sector - SPY 월별) — ★n<5 INSUFFICIENT 명시

| Epoch | n월 | XLP-SPY | XLU-SPY | XLV-SPY | XLF-SPY | XLC-SPY | sleeve-SPY | verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| E2 전환·반등 | **2** | -0.0516 | -0.0561 | -0.0347 | -0.0229 | +0.0085 | -0.0413 | ★INSUFFICIENT (n<5) |
| E3 rate 재상승 | **3** | -0.0117 | -0.0206 | +0.0017 | +0.0071 | +0.0144 | -0.0059 | ★INSUFFICIENT (n<5) |
| E4 pivot·인하 | 32 | -0.0111 | -0.0035 | -0.0128 | -0.0037 | -0.0001 | -0.0078 | n≥30, raw mean 가능 |

★발견 (★hedge 적용):
- 본 sleeve 가 모든 epoch 에서 underperform SPY (E2 n=2 가장 극단 -4.1%/월 — 단 INSUFFICIENT)
- XLC (Comm) 만 E2/E3 에서 outperform → archetype 분리 정당화 (단 n=2,3 약 신호)
- E1 긴축 (2022Q1~Q3) 시기 데이터 부족 (HY OAS 일별 가용 2023-05~)

## (2) Macro factor loading OLS (Full sample, n=742 일)

```
sector ~ α + β_rate·Δrate + β_real·Δreal_rate + β_dxy·r_dxy + β_hy·Δhy + ε
```

| sector | α | β_rate | β_real | β_dxy | β_hy | R² |
|---|---:|---:|---:|---:|---:|---:|
| XLP | +0.000315 | -0.0177 | -0.0158 | -0.1522 | -0.0153 | 0.0754 |
| XLU | +0.000574 | -0.0239 | -0.0436 | -0.1805 | -0.0283 | 0.1431 |
| XLV | +0.000236 | -0.0173 | -0.0295 | +0.0259 | -0.0366 | 0.1359 |
| XLF | +0.000522 | +0.0244 | -0.0728 | +0.1519 | -0.0804 | 0.3668 |
| XLC | +0.000698 | +0.0014 | -0.0496 | -0.0726 | -0.0740 | 0.3030 |
| SPY | +0.000619 | +0.0079 | -0.0562 | -0.0103 | -0.0830 | 0.4403 |

★발견:
- **XLF (banks) β_dxy = +0.152 vs XLU (util) β_dxy = -0.181** — sub-sleeve dollar 채널 부호 반대
- **XLV, XLF, XLC R² = 0.14~0.37** — macro factor 상당히 설명
- **XLP R² = 0.075** — staples macro factor 약 (idio risk dominant)

## (3) Epoch-conditional β (★v3 — Welch z + Bonferroni 격하 적용)

### E3 (rate 재상승, 2023Q3, n=63 일) — ★v3 실측 SE_dxy 부착

| sector | β_rate | β_real | β_dxy | SE_dxy | β_hy | R² |
|---|---:|---:|---:|---:|---:|---:|
| XLP | +0.0415 | -0.0851 | +0.2150 | 0.3197 | -0.0297 | 0.2360 |
| XLU | +0.0480 | -0.1238 | +0.5743 | 0.5280 | -0.0590 | 0.2317 |
| XLV | +0.0462 | -0.0921 | +0.6633 | 0.3492 | -0.0332 | 0.1886 |
| XLF | +0.0635 | -0.1170 | +0.2014 | 0.3623 | -0.0442 | 0.3145 |
| XLC | -0.0194 | -0.0347 | -0.1524 | 0.5309 | -0.0531 | 0.2245 |

★SE_dxy 가 β_dxy 와 동급 또는 큰 magnitude → n=63 small sample 의 OLS 추정 정밀도 약 (CI 0 포함).

### E4 (pivot·인하, 2023Q4~, n=657 일) — ★v3 실측 SE_dxy 부착

| sector | β_rate | β_real | β_dxy | SE_dxy | β_hy | R² |
|---|---:|---:|---:|---:|---:|---:|
| XLP | -0.0276 | -0.0052 | -0.1363 | 0.1071 | -0.0148 | 0.0692 |
| XLU | -0.0330 | -0.0375 | -0.1799 | 0.1350 | -0.0280 | 0.1466 |
| XLV | -0.0249 | -0.0234 | -0.0146 | 0.1174 | -0.0380 | 0.1415 |
| XLF | +0.0174 | -0.0644 | +0.1545 | 0.1164 | -0.0834 | 0.3715 |
| XLC | +0.0030 | -0.0462 | -0.0853 | 0.1229 | -0.0772 | 0.3186 |

### ★v3 M1 dollar 채널 격하 — Welch z + Bonferroni (rule §1.5)

**v2 verdict (위반)**:
> "rate-up regime XLU β_dxy=+0.574 / rate-down E4 -0.180 → M1 '★dollar 채널 rate-up 2배' 직접 확인 (강력)"

**v3 정정** — Welch z-test for β_dxy(E3) vs β_dxy(E4) gap, m=4 비교 Bonferroni 보정:

| sector | β_dxy E3 | SE_E3 | β_dxy E4 | SE_E4 | gap (E3-E4) | Welch z | p_raw | Bonferroni α/4=0.0125 sig |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| XLU | +0.5743 | 0.5280 | -0.1799 | 0.1350 | +0.7542 | +1.384 | 0.1664 | **FAIL** |
| XLV | +0.6633 | 0.3492 | -0.0146 | 0.1174 | +0.6779 | +1.840 | 0.0658 | **FAIL** (raw p=0.066 도 미달) |
| XLP | +0.2150 | 0.3197 | -0.1363 | 0.1071 | +0.3513 | +1.042 | 0.2974 | **FAIL** |
| XLF | +0.2014 | 0.3623 | +0.1545 | 0.1164 | +0.0469 | +0.123 | 0.9019 | **FAIL** (안정 — rate-regime 무관) |

**main 독립검증 anchor 정합**: XLU z=1.34 (main) vs z=1.384 (본 v3 fix 실측) — 거의 일치.

**★v3 verdict** (rule §2 verdict 5단계):
- 4 sector 중 **0/4 raw p<0.05 PASS** (XLV 가장 강 raw p=0.066 도 미달)
- 4 sector 중 **0/4 Bonferroni p<0.0125 PASS**
- → **TENTATIVE DIRECTIONAL** (방향성 약 prior 한정, 비유의)
- ★단정 "M1 강력 확인 / 2배" 어휘 철회 (rule §1, hedge 어휘 적용)
- 단 raw gap 방향 (rate-up POS / rate-down NEG) 은 5/5 sector 중 4 sector 일관 → 표본 확장 시 confirm 가능성 잔존

### M3 한계 (★v3 명시)

1. **n=63 (E3) / 657 (E4) day epoch** — 일별 sample 수 충분하나 ★자기상관 미보정 (rule §1.4 HAC SE 또는 Block bootstrap 추후 필요)
2. **m=4 Bonferroni 적용 시 전 sector FAIL** — 단정 prior 박제 X (rule §1.5(e) 점추정 covariance prior 박제 금지)
3. **rate-regime 정의 = epoch 단순 분리** — partial-corr conditioning 또는 RegimeGlasso 미적용
4. **표본 = 2023-05~2026-05 (3년 + post-2023 만)** — E1 긴축 (2022Q1~Q3) 데이터 부재

## (4) Within-sleeve corr (cross-asset vs within-sleeve 구분 — M1 caveat)

### Pearson corr (full sample, n=742 일)

|  | XLP | XLU | XLV | XLF | XLC | SPY |
|---|---:|---:|---:|---:|---:|---:|
| XLP | 1.000 | 0.605 | 0.614 | 0.574 | 0.534 | 0.675 |
| XLU | 0.605 | 1.000 | 0.530 | 0.492 | 0.425 | 0.610 |
| XLV | 0.614 | 0.530 | 1.000 | 0.622 | 0.629 | 0.779 |
| XLF | 0.574 | 0.492 | 0.622 | 1.000 | 0.669 | 0.828 |
| XLC | 0.534 | 0.425 | 0.629 | 0.669 | 1.000 | 0.865 |

★발견:
- 방어 4 (XLP/XLU/XLV/XLC) 평균 pair corr = 0.556
- 방어 ~ SPY 평균 corr = 0.732
- → 방어주가 자기들끼리 (0.55) 보다 SPY 와 더 유사 (0.73) — common equity factor (market beta) dominant
- M1 caveat 적용: defensive 내부 0.55 = 거시 factor 아니라 equity common factor

## (5) M4 factor seed 권고 (★v3 격하 반영)

본 실측 기반 M4 거시 factor seed (★v3 hedge):

### Factor 1: Real Rate Dichotomy (★hedge)
- contemporaneous: sub-archetype 부호 분기 — XLU/XLP NEG / XLF POS (n=5844, contemp 한정)
- predictive fwd3M: FAILS (rule §2 REJECTED — H1 정정 참조)
- **M4 적용**: lag_routing=contemporaneous 한정 anchor

### Factor 2: Dollar Channel Rate-Regime Switch (★v3 격하 — TENTATIVE)
- ★Welch z + Bonferroni 후 전 sector 비유의 (XLU raw p=0.18, Bonferroni p>0.05 단정 X)
- raw gap 방향성 (rate-up POS / rate-down NEG) 은 일관 — 단 신호 크기 통계적 미보장
- **M4 적용**: rate-regime conditional 채택 **보류** — ALFRED HY OAS full fetch 후 표본 확장 + HAC SE 부착 후 재검증

### Factor 3: Credit Cycle (banks 특화 잔여)
- 시장 베타 흡수 후 XLF partial IC = -0.166 (n=752 일, short window) → banks provisioning channel 잔여
- 방어주 시장 베타 흡수 후 +0.07 ~ +0.10 (residual)
- **M4 적용**: industry sub-archetype 분기 (banks NEG / defensive POS) — short window 명시 hedge

### Factor 4: Equity Common (within-sleeve caveat)
- 방어 sleeve 내부 corr 0.55 vs SPY 0.73 → 거시 factor 아닌 equity common factor
- M4 거시 layer 아닌 *equity factor model* 영역
- **M4 적용**: 별도 처리 X (SPY beta 로 흡수)

## (6) 한계 (★v3 정직)

1. **표본**: 2023-05~2026-05 (3년) — E1 긴축 (2022Q1~Q3) 데이터 부족
2. **E2, E3 n월=2, 3** — ★INSUFFICIENT (n<5), Bootstrap CI 불가
3. **WTI (oil) 미포함** — 본 분석 4 factor 만 (rate, real_rate, dxy, hy_oas)
4. **regime 정의 = simple OLS β** — partial-corr conditioning 또는 RegimeGlasso 미적용
5. ★**자기상관 미보정** — HAC SE / Block bootstrap 미적용 (rule §1.4 추후 보강)
6. ★**Multiple comparison Bonferroni 적용 후 모든 sector 비유의** — M1 단정 철회 (rule §1.5)
7. ★**점추정 covariance prior 박제 금지** (rule §1.5(e)) — yaml 의 dollar_beta prior_strength = 0.30 → unsigned 또는 0.10 (tentative) 격하 필요

## 참조

- `m3_macro_linkage.py` (★v3 ols_loading SE + Welch z + Bonferroni 부착)
- `m3-metrics.json` (★v3 m3_dxy_gap_welch_bonferroni 포함)
- `validation-H1.md` v3 (real rate dichotomy contemp/fwd 분리)
- `validation-H4.md` (credit beta sub-sleeve 분기 — n=752 short window)
- study-research/macro/timeline.md §4 (가이드 원문)
- handoff-bugfix-v3-20260530.md §2 (M3 dollar 결함 main 독립검증)
- ~/.claude/rules/empirical-claim-presentation.md §1.4 (autocorr) + §1.5 (multiple comparison) + §2 verdict 5단계
- ~/.claude/memory/promotion-log.md ERROR-202605302130 (★v3 root cause)
