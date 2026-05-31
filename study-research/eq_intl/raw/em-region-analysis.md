---
tags: [type/study-subagent, domain/inv, study/eq_intl, region/em]
date: 2026-05-31
session: btn-excel (EM subagent recovery)
region: EM
universe: [em_broad, brazil, india, china, korea, taiwan, mexico, em_ex_china, msci_china]
factor_set: [Δrate(^TNX pp), Δlog DXY, Δlog WTI]
principles: [PIT, OOS regime, 점추정 박제 금지 (95% CI 동반), Bonferroni, ★R² 금지 (idio σ 근거만)]
raw_data: raw/yahoo_cache/
ref_script: raw/em_analysis.py
ref_output: raw/em-analysis-output.txt
recovery_note: "subagent script 작성까지 완료 후 md Write 단계 stuck — main 세션이 직접 실행 + 박제"
n_days: 1254
---

# EM region 거시민감도 + R² 잔차분산 분해

## §1. 전체 5y baseline (EM-sleeve-avg + 9 ETF)

raw/em-analysis-output.txt §A 의 epoch 별 표 참조. 핵심: EM-sleeve-avg β_dollar = **-1.205** [-1.346, -1.064], |t|=16.76.

### Bonferroni 9 ETF × 3 coef × 6 epoch ≈ 105 tests, α=0.05/105 → |t|>3.55 생존
| ETF | β_rate | β_dollar | β_oil |
|---|---:|---:|---:|
| em_broad | 0/6 | 4/6 | 2/6 |
| brazil | 0/6 | 3/6 | 0/6 |
| india | 0/6 | 3/6 | 2/6 |
| china | 0/6 | 4/6 | 0/6 |
| korea | 0/6 | 4/6 | 2/6 |
| taiwan | 0/6 | 4/6 | 0/6 |
| mexico | 0/6 | 4/6 | 1/6 |
| em_ex_china | 0/6 | 5/6 | 2/6 |
| msci_china | 0/6 | 4/6 | 0/6 |

★ **β_dollar 35/54 생존** (65% epoch 별). β_rate 0/54 = rate 직접 채널 EM 도 무력. β_oil 9/54 = commodity bull regime 일부 유의.

## §2. EM archetype 분해 (전체 5y, 점추정 박제 금지 — 95% CI 동반)

| archetype | ETFs | β_rate (95% CI) | β_dollar (95% CI) | β_oil (95% CI) |
|---|---|---|---|---|
| **commodity_exporter** | brazil, mexico | +0.000 [-0.010, +0.011] | -1.121 [-1.262, -0.979] | **+0.060** [+0.036, +0.083] |
| **tech_exporter** | korea, taiwan | +0.014 [+0.004, +0.025] | **-1.380** [-1.522, -1.239] | -0.016 [-0.040, +0.007] |
| **domestic_demand** | india | +0.014 [+0.005, +0.023] | -0.720 [-0.843, -0.598] | -0.030 [-0.050, -0.010] |
| **em_china** | china, msci_china | +0.021 [+0.008, +0.034] | **-1.392** [-1.567, -1.218] | +0.044 [+0.014, +0.073] |
| em_broad_basket | em_broad, em_ex_china | +0.014 [+0.007, +0.022] | -1.170 [-1.267, -1.073] | -0.003 [-0.020, +0.013] |

★ **commodity_exporter β_oil = +0.060** (CI 0 미포함) — commodity exporter archetype 정량 확인.
★ **tech_exporter / em_china dollar 베타 가장 강** (-1.38 / -1.39) — dm_europe (-1.44) 와 비슷 수준.
★ **domestic_demand (india) dollar 베타 가장 약** (-0.72) — 내수 중심 archetype.

## §3. ★ R² 잔차분산 분해 (★main 격하 의무 준수 — R² 금지, σ_idio 만)

| ETF | systematic share (R²) | idio share | σ_idio annualized | σ_total annualized |
|---|---:|---:|---:|---:|
| em_broad | 0.187 | 0.813 | 17.02% | 18.86% |
| brazil | 0.097 | **0.903** | **26.37%** | 27.72% |
| india | 0.101 | 0.899 | 14.58% | 15.36% |
| china | 0.095 | **0.905** | **29.88%** | 31.38% |
| korea | 0.156 | 0.844 | 26.36% | 28.66% |
| taiwan | 0.115 | 0.885 | 21.04% | 22.34% |
| mexico | 0.130 | 0.870 | 21.09% | 22.58% |
| em_ex_china | 0.195 | 0.805 | 15.63% | 17.40% |
| msci_china | 0.097 | 0.903 | 28.94% | 30.43% |
| dm_exus | 0.297 | 0.703 | 13.82% | 16.46% |
| japan | 0.146 | 0.854 | 16.87% | 18.23% |
| germany | 0.311 | 0.689 | 16.98% | 20.43% |
| uk | 0.294 | 0.706 | 13.84% | 16.45% |
| europe | 0.330 | 0.670 | 14.65% | 17.88% |

| sleeve | mean σ_idio ann | SD | n |
|---|---:|---:|---:|
| **EM** | **22.32%** | 5.81% | 9 |
| **DM** | **15.23%** | 1.58% | 5 |

⛔ **R² 차이 (DM 0.29 / EM 0.10) 자체는 EM 약가중 근거로 사용 금지**. **σ_idio gap 만** 사용.

## §4. DM vs EM 상대가중 input

### 4.1 β_dollar 비교 (직접)
| sleeve | β_dollar | 95% CI | \|t\| |
|---|---:|---|---:|
| EM | -1.205 | [-1.346, -1.064] | 16.76 |
| DM | -1.348 | [-1.466, -1.231] | 22.54 |
| **diff (EM−DM)** | **+0.143** | (계산: SE=0.094) | **+1.53** |
| p_diff | **0.126** (n.s.) | | |

★ **β_dollar 자체는 DM/EM 통계적 동급**. dollar 채널 강도는 사실상 같다.

### 4.2 σ_idio 비교 (★ EM 약가중 정당화 ground)
| sleeve | σ_idio ann mean | SD | n |
|---|---:|---:|---:|
| EM | 22.32% | 5.81% | 9 |
| DM | 15.23% | 1.58% | 5 |
| **Welch t-test (EM−DM)** | **+7.09%p** | SE=2.06 | **t=+3.44, p=5.76e-04** |

★ **EM idio σ 가 DM 대비 1.47배 (Welch p=5.76e-04 강유의)** = ★ EM 약가중 정당화 **유일한 valid 근거**.

⛔ **'R² 차이' 금지** — systematic/idio share 는 mechanism 박제용. EM 의사결정 시 σ_idio 만.

## §5. 누락 critical 지표 caveat — EM region 우선순위

| 지표 | EM 영향 채널 | 우리 수집기 | 우선순위 |
|---|---|---|---|
| **terms-of-trade (commodity export/수입 비율, country별)** | brazil/mexico/indonesia commodity exporter archetype 의 본질 driver. β_oil 만으로 ToT 변동 미반영 | 부재 (IMF terms-of-trade index 필요) | **★★★** |
| 美대비 상대 이익모멘텀 (MSCI EM forward EPS revision vs SPX) | EM 펀더멘털 모멘텀 — dollar 노이즈 제거 후 분리 | 부재 (Refinitiv/IBES) | ★★ |
| forward PE 갭 (MSCI EM vs SPX) | 저평가 매력도 | 부재 | ★★ |
| 금리차/carry (EM 정책금리 - US FFR, country별) | EM carry trade, capital flow 핵심 | 부재 (IMF IFS API) | ★★ |

## §6. main 통합 인계 (EM 핵심 통계)

- **EM-sleeve β_dollar = -1.205** [-1.346, -1.064] vs DM-sleeve -1.348 → diff p=0.126 (n.s.).
- **β_dollar archetype**: commodity_exporter -1.121, tech_exporter -1.380, em_china -1.392, domestic_demand -0.720.
- **commodity_exporter β_oil = +0.060** [+0.036, +0.083] — archetype 정량 확인.
- **σ_idio gap**: EM 22.32% vs DM 15.23%, Welch p=5.76e-04 ★ **EM 약가중 정당화 ground**.
- **점추정 박제 금지 준수**: 모든 β/δ 95% CI 동반.
- ⛔ R² 차이 = mechanism 박제용, EM 약가중 근거 X.
- 누락 critical: **terms-of-trade for brazil/mexico** (commodity exporter archetype 본질) — 블록6 ★★★.
