---
tags: [type/study-validation, domain/inv, study/eq_intl, phase/2-3, hypothesis/h7]
date: 2026-05-30
session: btn-excel
study_id: eq_intl
hypothesis: H7 — TSM self-momentum (Moskowitz-Ooi-Pedersen 2012 country adapt): 각 국가 ETF 12m self-return 부호 → 다음 1m return 부호 동일
raw_source: raw/walkforward.py + raw/walkforward-output.txt
factor_set_frozen: [self-only — univariate self-return]
walkforward_setup: "monthly resample (5y → 60m), each month t: past 12m cum log-return → next-1m sign hit rate"
---

# H7 walk-forward 검증 — TSM self-momentum

## §1. 가설 + 반증조건

- **가설**: 각 국가 ETF 의 [t-12, t-1] cumulative log-return 부호 = t+1 의 log-return 부호.
- **반증조건**: hit rate < 52% (random 노이즈 영역).

## §2. Walk-forward setup

- Monthly resample 5y → 60 month-end. Past 12m exclude current → 46 effective t.
- factor 고정 = self-return only (univariate Moskowitz-style).
- 국가별 + cross-asset summary.

## §3. 결과 — archetype 별 mixed

| 분류 | 국가 | hit rate | n | mom mean | next mean |
|---|---|---:|---:|---:|---:|
| ★ DM 강 | uk | **69.57%** | 46 | +0.105 | +0.012 |
| DM 강 | dm_exus | 65.22% | 46 | +0.084 | +0.012 |
| DM 강 | em_broad | 65.22% | 46 | +0.045 | +0.014 |
| DM 강 | us_spy | 63.04% | 46 | +0.114 | +0.014 |
| DM 강 | europe | 63.04% | 46 | +0.089 | +0.013 |
| DM 강 | japan | 60.87% | 46 | +0.077 | +0.013 |
| DM 중 | germany | 58.70% | 46 | +0.100 | +0.015 |
| 중 | taiwan | 58.70% | 46 | +0.086 | +0.023 |
| 중 | em_ex_china | 54.35% | 46 | +0.064 | +0.017 |
| 약 | india / mexico | 50.00% | 46 | +0.05/+0.11 | +0.003/+0.014 |
| ★ 약/반전 | brazil | **39.13%** | 46 | +0.068 | +0.010 |
| ★ 약/반전 | korea | **39.13%** | 46 | +0.053 | +0.028 |
| ★ 약/반전 | china | 47.83% | 46 | +0.028 | +0.005 |
| ★ 약/반전 | msci_china | 47.83% | 46 | +0.006 | +0.004 |

## §4. 판정

**△ archetype 별 mixed**:
- **dm_europe + DM broad + uk = 강 성립** (hit rate 60~70%). Moskowitz-style TSM 의 country 적용 strong evidence.
- **EM single = 부분 기각** (brazil/korea **<40%**, china 48%) — TSM 신호가 EM 에서 작동 안 함 또는 반전.
- DM/EM 의 archetype 차이 명확 — H7 base 가중 적용 시 archetype 별 modulate 필수.

★ archetype 적용 결과:
- archetype dm_europe / dm_broad / uk = TSM 가중 ↑
- archetype em_commodity (brazil) + tech_exporter (korea) = **TSM 가중 ↓ 또는 반전 부호** — momentum 자체가 부정적 signal.
- archetype em_china = mixed (48%) — H5 의 idio dominance 와 일관.

## §5. yaml 갱신 표지

- block2 mom_12_1_country: archetype 별 modulate 명시 (DM=양, EM=mixed).
- block3 새 edge: `tsm_self_archetype_modulation` (archetype 별 부호 가변).
- block4 mom_12_1_country base_weight 0.12 → archetype 별 split:
  - delta_arch_by_type[dm_europe] : +0.04
  - delta_arch_by_type[commodity_exporter] : -0.04
  - delta_arch_by_type[em_china] : 0
- block5 confidence_hook tsm_archetype_modulation: NEEDS_DEPLOY.

## §6. 향후 개선

- 9~12m, 6m, 3m 다양한 lookback 별 hit rate (Moskowitz 2012 의 표 재현).
- regime-conditional TSM (risk-on/off split) — H9 momentum_crash_regime 연계.
- AQR TSM dataset 의 country index 결과와 cross-validation.
