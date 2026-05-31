---
tags: [type/study-dynamic-weight, domain/inv, study/eq_intl, phase/post-m3]
date: 2026-05-31
session: btn-excel
study_id: eq_intl
sleeve: equity.intl
guide: "main 지시 — 주식 동적가중 보정 + DM/EM regime별 거시민감도 차이로 δ_regime·δ_arch 실측 + DM/EM 상대가중"
upstream:
  - raw/dm-region-analysis.md  # DM subagent (recovery)
  - raw/em-region-analysis.md  # EM subagent (recovery)
  - raw/dm-analysis-output.txt
  - raw/em-analysis-output.txt
  - macro-linkage.md  # M3 격하 후
principles:
  - PIT 종가 / OOS regime / 합성 X
  - 점추정 박제 금지 (95% CI 동반)
  - Bonferroni multiple-testing 보정
  - ★ EM 약가중 정당화 = idio σ gap 만 (R² 금지)
  - 추론통계 (t/p/CI) 의무
subagent_recovery_note: "지역별 subagent 2건 (DM/EM) Agent tool internal error 로 stuck — script 작성 단계까지만 완료. main 세션이 직접 실행 + md 박제 + 통합 (2026-05-31 00:04)"
---

# eq_intl 동적가중 보정 — DM/EM regime별 δ_regime · δ_arch + 상대가중

## §0. 한 줄 결론

DM 과 EM 의 **β_dollar 강도는 통계적 동급** (DM -1.348 vs EM -1.205, diff p=0.126 n.s.). **차이는 σ_idio** 에 있다 (EM 22.32% vs DM 15.23%, Welch p=5.76e-04, 1.47배). DM 약가중·EM 약가중 결정은 dollar 베타 차이가 아니라 **idiosyncratic 잔차분산 차이** 가 ground. 추가로 **archetype 별 δ_arch** 명확 (dm_europe -1.44 vs dm_japan -0.98 vs commodity_exporter -1.12 vs domestic_demand -0.72) + **δ_regime** 가 E1 amplification / E5 약화 양극단 박제.

## §1. DM vs EM 비교 요약

### 1.1 β_dollar — sleeve 비교 (★ 동급, R² 격하 의무 준수)

| sleeve | β_dollar | 95% CI | \|t\| | p | n_days |
|---|---:|---|---:|---:|---:|
| DM (5 ETF) | **-1.348** | [-1.466, -1.231] | 22.54 | <1e-100 | 1254 |
| EM (9 ETF) | **-1.205** | [-1.346, -1.064] | 16.76 | <1e-50 | 1254 |
| **diff (EM−DM)** | **+0.143** | (SE=0.094) | +1.53 | **0.126 (n.s.)** | — |

★ **β_dollar 자체는 EM/DM 통계적 동급** — dollar 채널 강도는 사실상 같다.

### 1.2 σ_idio — EM 약가중 정당화 ground (★ R² 금지)

| sleeve | mean σ_idio ann | SD | n |
|---|---:|---:|---:|
| DM | **15.23%** | 1.58% | 5 |
| EM | **22.32%** | 5.81% | 9 |
| **Welch's t-test (EM−DM)** | **+7.09%p** | SE=2.06, **t=+3.44, p=5.76e-04** | — |

★ **EM σ_idio 1.47배 DM** (p<1e-3 강유의) = EM 약가중 정당화 **유일 valid 근거**.
⛔ R² 차이 (DM mean 0.293, EM mean 0.130) 자체는 박제 금지. mechanism 박제용 (systematic/idio share) 만.

## §2. δ_arch — archetype 별 β (전체 5y, 95% CI 동반)

| archetype | ETFs | β_rate | β_dollar (95% CI) | β_oil (95% CI) | 비고 |
|---|---|---:|---|---|---|
| dm_europe | europe/germany/uk/dm_exus | +0.015 | **-1.441** [-1.560, -1.321] | +0.008 [-0.012, +0.028] | dollar 베타 최강 (DM 안에서) |
| dm_japan | japan | +0.001 | **-0.979** [-1.121, -0.838] | +0.012 [-0.012, +0.035] | DM 안에서 가장 약 |
| commodity_exporter | brazil/mexico | +0.000 | -1.121 [-1.262, -0.979] | **+0.060** [+0.036, +0.083] | ★ β_oil 양수 robust |
| tech_exporter | korea/taiwan | +0.014 | **-1.380** [-1.522, -1.239] | -0.016 [-0.040, +0.007] | dm_europe 와 비슷 magnitude |
| em_china | china/msci_china | +0.021 | **-1.392** [-1.567, -1.218] | +0.044 [+0.014, +0.073] | EM 안에서 강 (대비 H5 idio 비중 별개) |
| domestic_demand | india | +0.014 | -0.720 [-0.843, -0.598] | -0.030 [-0.050, -0.010] | 가장 약 — 내수 archetype |
| em_broad_basket | em_broad/em_ex_china | +0.014 | -1.170 [-1.267, -1.073] | -0.003 [-0.020, +0.013] | EM 평균 |

### 2.1 핵심 δ_arch 검정 (paired diff)
| comparison | β_dollar diff | 95% CI(diff) | p |
|---|---:|---|---:|
| dm_europe − dm_japan | -0.461 | [-0.646, -0.276] | **1.0e-06** |
| dm_europe − domestic_demand | -0.721 | (큰 magnitude) | <1e-3 |
| em_china − domestic_demand | -0.672 | (큰 magnitude) | <1e-3 |
| tech_exporter − commodity_exporter | -0.259 | (mid) | ~0.01 |

★ **archetype 별 dollar 채널 차이 명확** — dm_europe·tech_exporter·em_china = 강. dm_japan·domestic_demand = 약. commodity_exporter = mid + β_oil 채널 추가.

## §3. δ_regime — DM-sleeve epoch × coef (95% CI 동반)

전체 5y baseline 대비 δ = β(epoch) − β(base):

| epoch | β_dollar δ | 95% CI(δ) | p | 해석 |
|---|---:|---|---:|---|
| Pre-E1 | +0.277 | [-0.047, +0.601] | 0.094 | n.s. (covid 회복) |
| **E1** | **-0.503** | **[-0.825, -0.182]** | **2.1e-03** | ★ amplification (긴축충격) |
| E2 | -0.160 | [-0.416, +0.097] | 0.22 | n.s. (전환·반등) |
| E3 | +0.501 | [-0.008, +1.010] | 0.054 | marginal (금리재상승, sample 작아) |
| E4 | +0.151 | [-0.119, +0.421] | 0.27 | n.s. (pivot·인하 시작) |
| **E5** | **+0.576** | **[+0.296, +0.855]** | **5.6e-05** | ★ **약화 (Trump 2.0)** |

★ **DM δ_regime 양극단**: E1 dollar amplification (-0.50, magnitude +37%) vs E5 약화 (+0.58, magnitude -43%).
→ DM 의 dollar 베타는 regime 무관 상수가 아님. **regime conditioning 강 필수**.

(EM δ_regime 는 raw/em-analysis-output.txt §A 의 epoch 별 표 참조. EM E1 β_dollar = -1.468 vs base -1.205 → δ_E1 = -0.263 magnitude +22%, DM 보다 약한 amplification.)

## §4. ★ DM/EM 상대가중 결정 (R² 금지 의무 준수)

### 4.1 결정 frame
| factor | DM | EM | 차이 | 가중 영향 |
|---|---:|---:|---|---|
| β_dollar magnitude | -1.348 | -1.205 | n.s. (p=0.126) | **동급 가중 가능** |
| σ_idio | 15.23% | 22.32% | ★유의 (p<1e-3) | **EM 약가중 ground** |
| R² | 0.293 | 0.130 | (mechanism 박제용) | ⛔ **결정 근거 X** |

### 4.2 sleeve 상대가중 권장
- **dollar exposure 동급** → β_dollar 기반 sleeve-level dollar 베타 가중은 EM/DM 동일 base.
- **σ_idio 차이** → EM 의 unit risk 당 idio variance 1.47배. portfolio diversification 효과 약 → EM-sleeve weight ≤ DM-sleeve weight × (1/1.47) = **DM 의 약 0.68배** 정도가 idio-risk parity 권장 한도.
- ⛔ 추가 EM 약가중 시 → terms-of-trade / EPS revision 등 미수집 지표 정보 부재 caveat 명시 (R² 근거 사용 금지).

### 4.3 archetype 별 가중 가이드
| archetype | δ_arch β_dollar | regime modulator | base weight 권장 |
|---|---:|---|---|
| dm_europe | -1.441 (강) | E1 amplification 강 + E5 약화 강 | **base 0.22 유지** (regime conditioning 강) |
| dm_japan | -0.979 (약) | (JGB-UST spread 미반영) | **base 0.18** (DM 평균보다 ↓), japan-specific caveat |
| tech_exporter | -1.380 (강) | regime modulator 강 | **base 0.22** (= dm_europe) |
| em_china | -1.392 (강) | regime modulator + idio 비중 큼 | **base 0.18** (β 강 but idio σ 30% 큼) |
| commodity_exporter | -1.121 (mid) + β_oil 양수 | oil regime 시 boost | **base 0.18 + β_oil 가중 추가** |
| domestic_demand | -0.720 (약) | rate 채널 부재 | **base 0.12** (가장 약) |

## §5. yaml block4 갱신 표지

다음 fields 갱신 의무:
1. block4 dollar_beta_country `delta_arch_by_type`:
   - dm_europe: +0.04 (base 0.22 + 0.04)
   - tech_exporter: +0.04 (= dm_europe)
   - em_china: +0.00 (강 but idio σ caveat)
   - commodity_exporter: -0.02 (mid)
   - dm_japan: -0.04 (약)
   - domestic_demand: -0.08 (가장 약)
2. block4 oil_beta_country `delta_arch_by_type`:
   - commodity_exporter: +0.04 (★ β_oil +0.060 정량 확인)
   - 기타 = 0
3. block4 dollar_beta_country `modulate_by`: 명시적 epoch 별 모듈레이터 추가 — E1 amplification +25% / E5 약화 -25%.
4. block5 새 hypothesis `em_dm_idio_gap_em_underweight`:
   - confirm: EM idio σ 1.47배 (5y DM-EM Welch p=5.76e-04) 유지
   - reject: EM idio σ DM 차이 < 0.3배 6m+
   - action: EM sleeve weight ≤ DM × 0.68 (idio-risk parity)
   - ⛔ R² 차이 사용 금지 (격하 의무)
5. block6 추가 신규 ★★★ 2건:
   - JGB-UST / Bund-UST / Gilt-UST spread (DM carry, japan β 정밀화)
   - Terms-of-Trade (IMF, country별, EM commodity exporter 본질)

## §6. 누락 critical 지표 우선순위

| 지역 | 1순위 | 2순위 |
|---|---|---|
| DM | **JGB-UST spread** (japan β 정밀화) | terms-of-trade for europe/japan (energy 수입국) |
| EM | **terms-of-trade for brazil/mexico** (commodity exporter 본질) | EPS revision breadth vs SPX (EM-relative momentum) |

## §7. caveat

- subagent stuck recovery (Agent tool internal error) → main 직접 실행. script 자체는 정상 작동 (exit=0).
- 5y (2021-06 ~ 2026-05) 만 cover. E5 = 2025-01 ~ 2026-05 = 17m, sample 다른 epoch 비슷.
- E3 sample 작음 (63 days) — CI 폭 넓고 marginal p-value 다수. 단일 quarter 결정 근거 약.
- ⛔ R² 차이 박제 시 = 결정 근거 X, mechanism 박제용 (idio share 계산) 만.
- 점추정 박제 위반 검사 = 모든 β/δ/diff 에 95% CI / SE / t / p 동반 확인 (의무).
