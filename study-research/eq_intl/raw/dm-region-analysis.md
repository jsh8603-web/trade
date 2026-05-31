---
tags: [type/study-subagent, domain/inv, study/eq_intl, region/dm]
date: 2026-05-31
session: btn-excel (DM subagent recovery)
region: DM
universe: [europe, germany, uk, dm_exus, japan]
factor_set: [Δrate(^TNX pp), Δlog DXY, Δlog WTI]
principles: [PIT, OOS regime, 점추정 박제 금지 (95% CI 동반), Bonferroni]
raw_data: raw/yahoo_cache/
ref_script: raw/dm_analysis.py
ref_output: raw/dm-analysis-output.txt
recovery_note: "subagent script 작성까지 완료 후 md Write 단계 stuck — main 세션이 직접 실행 + 박제"
n_days: 1254
date_range: 2021-06-02 ~ 2026-05-29
---

# DM region 거시민감도 분석

## §1. 전체 5y baseline (DM-sleeve-avg + 5 ETF)

| ETF | β_rate (95% CI) | β_dollar (95% CI) | β_oil (95% CI) | R² |
|---|---|---|---|---:|
| europe | +0.015 [+0.006, +0.024] | **-1.504** [-1.627, -1.381] | +0.001 [-0.020, +0.021] | **0.330** |
| germany | +0.022 [+0.011, +0.032] | **-1.682** [-1.825, -1.540] | -0.024 [-0.048, +0.000] | 0.311 |
| uk | +0.013 [+0.004, +0.021] | -1.273 [-1.389, -1.157] | **+0.045** [+0.026, +0.065] | 0.294 |
| dm_exus | +0.011 [+0.002, +0.019] | -1.303 [-1.419, -1.187] | +0.010 [-0.010, +0.029] | 0.297 |
| japan | +0.001 [-0.009, +0.012] | -0.979 [-1.121, -0.838] | +0.012 [-0.012, +0.035] | 0.146 |
| **DM-sleeve-avg** | **+0.012** [+0.004, +0.021] | **-1.348** [-1.466, -1.231] | +0.009 [-0.011, +0.028] | 0.305 |

★ Bonferroni 5×5×3=75 tests, α=0.05/75 → |t|>3.51 생존:
- **β_dollar 27/30** (DM 강하게 robust, 5 ETF × 6 epoch 거의 모두 생존)
- β_rate 4/30 (mostly noise)
- β_oil 4/30 (Pre-E1·E3 commodity bull regime 만)

## §2. δ_regime — DM-sleeve-avg (epoch − base, 95% CI 동반)

| epoch | coef | β(ep) | β(base) | δ_regime | 95% CI(δ) | t | p | verdict |
|---|---|---:|---:|---:|---|---:|---:|---|
| Pre-E1 | β_rate | +0.045 | +0.012 | **+0.032** | [+0.007, +0.057] | +2.53 | 0.011 | ★유의 |
| Pre-E1 | β_oil | +0.142 | +0.009 | **+0.133** | [+0.083, +0.183] | +5.24 | 1.6e-07 | ★유의 |
| **E1** | β_dollar | **-1.852** | -1.348 | **-0.503** | [-0.825, -0.182] | -3.07 | **2.1e-03** | ★유의 (긴축충격 amplification) |
| E3 | β_rate | -0.039 | +0.012 | -0.052 | [-0.082, -0.021] | -3.32 | 8.9e-04 | ★유의 |
| E3 | β_oil | +0.118 | +0.009 | +0.109 | [+0.004, +0.214] | +2.03 | 0.042 | ★유의 |
| **E5** | β_dollar | **-0.773** | -1.348 | **+0.576** | [+0.296, +0.855] | +4.03 | **5.6e-05** | ★유의 (Trump 2.0 dollar 약화) |
| E5 | β_oil | -0.053 | +0.009 | -0.062 | [-0.106, -0.018] | -2.78 | 5.4e-03 | ★유의 |

★ 핵심 발견:
- **E1 긴축충격**: dollar 베타 -1.85 (vs base -1.35) → amplification (+37% magnitude).
- **E5 Trump 2.0**: dollar 베타 -0.77 (vs base -1.35) → **약화 (-43% magnitude)** ★ 가장 큰 regime shift.
- Pre-E1·E3: oil 채널 작동 (β_oil +0.13~+0.14) — 다른 epoch 에서는 oil noise.

## §3. δ_arch — dm_europe vs dm_japan (전체 5y)

| coef | dm_europe (95% CI) | dm_japan (95% CI) | diff (europe − japan) | 95% CI(diff) | p | verdict |
|---|---|---|---|---|---:|---|
| β_rate | +0.015 [+0.006, +0.024] | +0.001 [-0.009, +0.012] | +0.014 | [+0.000, +0.027] | 0.046 | ★유의 |
| **β_dollar** | **-1.441** [-1.560, -1.321] | **-0.979** [-1.121, -0.838] | **-0.461** | [-0.646, -0.276] | **1.0e-06** | ★유의 |
| β_oil | +0.008 [-0.012, +0.028] | +0.012 [-0.012, +0.035] | -0.004 | [-0.035, +0.027] | 0.80 | n.s. |

★ **dm_europe 의 dollar 베타가 dm_japan 보다 0.46 더 강** (p=1e-06). DM 안에서도 archetype 별 dollar 채널 강도 차이 명확.

## §4. 누락 critical 지표 caveat — DM region 우선순위

| 지표 | DM 영향 채널 | 우리 수집기 | 우선순위 |
|---|---|---|---|
| **금리차/carry (JGB-UST, Bund-UST, Gilt-UST)** | japan β_dollar 의미 가장 모호 (JGB-UST = USDJPY 본질). UST 만 회귀 시 spread 흡수 못함 | 부재 | **★★★** |
| terms-of-trade (DM energy 수입국) | europe/japan gas/oil 충격 → E1 regime amplification 의 미시 채널 | β_oil 만 측정, TWI-weighted import 비중 미반영 | ★★ |
| forward PE 갭 (Stoxx 600 vs SPX) | valuation 변동 미흡, regime shift 미반영 | 부재 | ★★ |
| 美대비 상대 이익모멘텀 | dollar/rate 노이즈 제거 후 펀더멘털 모멘텀 분리 가능 | 부재 | ★ |

## §5. main 통합 인계 (DM 핵심 통계)

- **DM-sleeve β_dollar = -1.348** [-1.466, -1.231], R² = 0.305, |t|=22.5.
- **archetype**: dm_europe -1.441 vs dm_japan -0.979 (diff p=1.0e-06).
- **δ_regime 핵심**: E1 dollar amplification -0.503 (p=2.1e-03), E5 dollar 약화 +0.576 (p=5.6e-05).
- **점추정 박제 금지 준수**: 모든 β/δ 에 95% CI 동반.
- 누락 critical: japan β_dollar 의미 정밀화 위해 **JGB-UST spread** 가 가장 critical → 블록6 ★★★ 추가.
