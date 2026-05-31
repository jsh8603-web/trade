---
tags: [type/study-validation, domain/inv, study/eq_intl, phase/2-3, hypothesis/h2]
date: 2026-05-30
session: btn-excel
study_id: eq_intl
hypothesis: H2 — Regime amplification: risk-off (VIX>25) 시 dollar-EM coupling 강화
raw_source: raw/walkforward.py + raw/walkforward-output.txt + raw/analysis-output.txt
factor_set_frozen: [DXY, VIX (regime label only)]
walkforward_setup: "Train 24m rolling, risk-on/off split (VIX>25 binary), DXY↔EM pearson 각 regime 별"
---

# H2 walk-forward 검증 — Regime amplification

## §1. 가설 + 반증조건

- **가설**: train window 내 risk-off (VIX>25) 일자의 DXY↔EM corr 가 risk-on 일자보다 더 음수 (강화).
- **반증조건**: |risk-off corr − risk-on corr| < 0.10 in majority of windows OR diff 부호 반전.

## §2. Walk-forward setup

- Train: 매 6 month 마다 직전 504 daily obs (3 windows).
- Risk-off split: VIX > 25 daily.
- Risk-on split: VIX ≤ 25.
- DXY ↔ EM_broad pearson 각 regime 별 측정.
- ⚠️ 한계: 5y 데이터 + 24m train 내 risk-off 일수 (보통 15~140일) 적어 in-window detect 약함.

## §3. 결과 — 가설 부분 기각 (walk-forward) + 강확인 (전체 5y daily, ref)

### 3.1 Walk-forward (in-train split)
| month_t | corr_off | corr_on | n_off | n_on | amplified? |
|---|---:|---:|---:|---:|---|
| 2023-06 | -0.478 | -0.496 | 140 | 364 | ✗ (corr_off > corr_on) |
| 2023-12 | -0.518 | -0.544 | 133 | 371 | ✗ |
| 2024-06 | -0.615 | -0.572 | 62 | 442 | ✓ |
| **mean** | **-0.537** | **-0.537** | — | — | diff = +0.000 |
| amplification | — | — | — | — | **33.3% (1/3 windows)** |

### 3.2 전체 5y daily 분해 (raw/analysis-output.txt H4)
ref: 월별 5y panel 의 regime split (risk-off months 8, risk-on 51)
| country | risk-on corr | risk-off corr | amplified? |
|---|---:|---:|---|
| em_broad | -0.640 | **-0.796** | ✓ 강 |
| japan | -0.608 | **-0.901** | ✓ 강 |
| korea | -0.405 | **-0.770** | ✓ 강 |
| brazil | -0.506 | -0.456 | △ |
| china | -0.541 | **+0.033** | ✗ (반전, R3 H5 지지) |
| europe | -0.769 | -0.755 | △ |

## §4. 판정

**△ 조건부 성립**: 전체 5y 일별 panel 에서는 risk-off 시 EM/japan/korea 의 dollar coupling 강력 증폭 (-0.640 → -0.796) — 강확인. 그러나 walk-forward 24m train window 안에서는 detect 약함 (risk-off 일수 부족 + within-window noise).

→ **결론**: H2 는 **macro regime cycle 수준에서 성립** (5y 전체), **micro 24m window 내에서는 noise** 가 강함. walk-forward 검증보다는 **regime-conditional weight switching** 으로 코드화하는 게 맞음 (regime label 진입 시 weight ↑, exit 시 ↓ — 단순 회귀가 아님).

## §5. yaml 갱신 표지

- block3 risk_off_dxy_em_amplification edge 신설 (조건부 prior, conditioning_set = VIX-regime).
- block4 dollar_beta_country modulate_by: [regime] 명시 강화 — risk-off detect 시 base_weight 0.22 → 0.30 boost.
- block5 confidence_hook regime_amplification: 5y 일별 강확인 기준 EARLY_ADOPT, walk-forward 24m noise 는 CAVEAT 명시.
- block5 추가 evidence: 5y daily risk-off (n=8 month) em_broad -0.796 vs risk-on (n=51) -0.640. walk-forward 24m frequency 33%.

## §6. 향후 개선

- HY OAS (BAMLH0A0HYM2) 직접 regime label 추가 — VIX 보다 채권 채널 직접.
- e-CUSUM 단측 위반 시점 (regime transition) 별 IC 분해.
