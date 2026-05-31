---
tags: [type/study-macro-linkage, domain/inv, study/eq_intl, phase/m3]
date: 2026-05-30
session: btn-excel
study_id: eq_intl
sleeve: equity.intl
guide: study-research/macro/timeline.md §4 M3
raw_source: raw/macro_linkage.py + raw/macro-linkage-output.txt + raw/yahoo_cache/
principles: [PIT 종가, OOS regime 라벨, 합성금지 (raw daily log-return only)]
universe: "12 country ETF (EFA-V2 제외, US-EX): dm_exus / japan / germany / uk / em_broad / brazil / india / china / korea / taiwan / mexico / europe"
drivers: "rate = ^TNX Δlevel (pp) / dollar = DXY Δlog / oil = WTI Δlog"
---

# eq_intl M3 거시연관 분석 (timeline.md §4 가이드 적용)

## §1. Regime 별 수익률·변동성 (sleeve-avg + 핵심 ETF)

| epoch | 시기 | sleeve ann_ret | sleeve ann_vol | sharpe | 핵심 anomaly |
|---|---|---:|---:|---:|---|
| **Pre-E1** | 2021-05 ~ 2021-12 (covid 잔류) | -8.77% | 17.06% | -0.51 | china -41.55% / brazil -46.41% / korea -27.31% (EM 부진) |
| **E1 긴축충격** | 2022Q1~Q3 | **-38.23%** | 25.70% | -1.49 | europe -49% / korea -67% 등 전 자산 폭락. **brazil +13.4%** (commodity 수혜 외톨이) |
| **E2 전환·반등** | 2022Q4~2023Q2 | **+32.49%** | 21.96% | 1.48 | europe +43% / korea +41% / japan +33% 강한 회복 |
| **E3 금리재상승** | 2023Q3 | -18.23% | 16.76% | -1.09 | 짧지만 broad 음수 (korea -29%) |
| **E4 pivot·인하** | 2023Q4~2024 | +7.38% | 18.45% | 0.40 | china +14.5% (의외, 일시 re-couple?). brazil -16% (commodity 부진) |
| **E5 (신규)** | 2025-01 ~ 2026-05 | **+33.56%** | 22.37% | 1.50 | **korea +101.63%** (단일국 폭발, AI/반도체 cycle), brazil +37%, em_broad +37% |

★ 핵심 관찰:
- E1 (긴축 + dollar 급등) = sleeve 전체가 균일하게 폭락. brazil 만 commodity exporter archetype 양 (+13.4%).
- E2 = pivot 기대만으로 강한 reversal. equity factor 가 dominant 한 시기.
- E5 (timeline 외 신규) = sleeve 강세지만 dispersion 큼 (korea 100%+ vs china 12%) → archetype 별 분화 강화.

## §2. 거시 driver loading (multi OLS: ETF ~ Δrate + Δlog_DXY + Δlog_WTI)

### 2.1 전체 5y (n=1254)

| ETF | β_rate | β_dollar | β_oil | R² |
|---|---:|---:|---:|---:|
| europe | +0.015 | **-1.504** | +0.001 | **0.330** |
| germany | +0.022 | **-1.682** | -0.024 | 0.311 |
| dm_exus | +0.011 | -1.303 | +0.010 | 0.297 |
| uk | +0.013 | -1.273 | +0.045 | 0.294 |
| em_broad | +0.016 | -1.206 | +0.002 | 0.187 |
| korea | +0.014 | **-1.640** | -0.038 | 0.156 |
| japan | +0.001 | -0.979 | +0.012 | 0.146 |
| mexico | +0.000 | -1.126 | +0.034 | 0.130 |
| taiwan | +0.014 | -1.121 | +0.005 | 0.115 |
| india | +0.014 | -0.720 | -0.030 | 0.101 |
| brazil | +0.000 | -1.115 | **+0.085** | 0.097 |
| china | +0.020 | -1.400 | +0.047 | 0.095 |

★ 관찰:
- **β_rate ≈ 0** 모든 ETF — rate 직접 채널 = 무력 (★M1 발견 강확인).
- **β_dollar 강 음수 일관** (-0.72 ~ -1.68) — dollar 가 1차 driver.
- **β_oil ≈ 0** 대부분, brazil 만 +0.085 (commodity exporter archetype 약확인).
- **R² DM Europe 최강** (europe 0.33 / germany 0.31 / dm_exus 0.30) vs EM 단일국 (brazil/india/china 0.10 이하). ★단 §1.5 추론통계 참조 — R² 차이 ≠ β 유의성 차이. EM 도 β_dollar Bonferroni 압도적 생존.

### §1.5 ★추론통계 박제 (raw/macro_linkage_v2.py + raw/macro-linkage-v2-output.txt)

★ **main 격하 의무 (a) (c) 이행**: R²↔유의성 혼동 정정 + t/p/CI 명시.

| ETF | β_dollar | SE | \|t\| | p (two-sided) | 95% CI | Bonferroni 생존? |
|---|---:|---:|---:|---:|---|:---:|
| dm_exus | -1.303 | 0.059 | 22.02 | 2.0e-107 | [-1.419, -1.187] | ✓ |
| japan | -0.979 | 0.072 | 13.55 | 7.5e-42 | [-1.121, -0.838] | ✓ |
| germany | -1.682 | 0.073 | 23.13 | 2.4e-118 | [-1.825, -1.540] | ✓ |
| uk | -1.273 | 0.059 | 21.48 | 2.4e-102 | [-1.389, -1.157] | ✓ |
| em_broad | -1.206 | 0.073 | 16.54 | 1.9e-61 | [-1.349, -1.063] | ✓ |
| **brazil** | **-1.115** | **0.113** | **9.87** | **5.7e-23** | **[-1.336, -0.894]** | **✓** |
| **india** | **-0.720** | 0.063 | 11.53 | 9.4e-31 | [-0.843, -0.598] | ✓ |
| **china** | **-1.400** | **0.128** | **10.94** | **7.8e-28** | **[-1.651, -1.149]** | **✓** |
| korea | -1.640 | 0.113 | 14.52 | 8.7e-48 | [-1.861, -1.419] | ✓ |
| taiwan | -1.121 | 0.090 | 12.43 | 1.8e-35 | [-1.297, -0.944] | ✓ |
| mexico | -1.126 | 0.090 | 12.47 | 1.1e-35 | [-1.304, -0.949] | ✓ |
| europe | -1.504 | 0.063 | 23.96 | 8.0e-127 | [-1.627, -1.381] | ✓ |

★ **β_dollar Bonferroni 12/12 생존** (α=0.05/36 ≈ 1.39e-3 → \|t\|>3.42). EM 단일국도 \|t\|=9.87~14.52, p<1e-22 = **압도적 robust**.
★ β_rate Bonferroni 생존 = **1/12** (germany 만 \|t\|=4.08). 모든 다른 ETF \|t\|<3.42 → rate 직접 채널 noise.
★ β_oil Bonferroni 생존 = **2/12** (uk +0.045 \|t\|=4.60 / brazil +0.085 \|t\|=4.53). brazil commodity exporter archetype 정량 확인.

★ R² 0.10 (EM) vs 0.33 (DM Europe) = **잔차분산 차이** (EM idiosyncratic 비중 큼). 단 거시 무관 ≠ R² 낮음. β_dollar 강도와 robust 검정은 EM/DM 공통으로 강확인.

### 2.2 Epoch 별 sleeve-avg β + |β_dollar / β_rate|

| epoch | β_rate(avg) | β_dollar(avg) | β_oil(avg) | \|β_dollar/β_rate\| | 의미 |
|---|---:|---:|---:|---:|---|
| Pre-E1 | +0.041 | -1.000 | +0.141 | 24.30 | covid recover, oil 채널 작동 (β_oil +0.141 — commodity export 강) |
| **E1 긴축충격** | +0.017 | **-1.627** | -0.007 | **94.95** | **dollar 압도 94배** (rate 채널 무력). 통제·재정·인플레 패닉 |
| E2 전환·반등 | +0.022 | -1.284 | +0.064 | 57.36 | 회복기 oil 양수 부분 작동 |
| E3 금리재상승 | -0.046 | -0.873 | +0.123 | **19.15** | 짧은 시기 rate β 음수 (소폭) + oil 양수 — energy/commodity 우위 |
| E4 pivot·인하 | -0.001 | -1.192 | +0.051 | **1118** | rate β ≈ 0 → 비율 폭발. dollar 채널 유지 |
| E5 (신규) | +0.008 | -0.790 | -0.067 | 106 | **dollar β 감소** (-1.0 → -0.79) — Trump 2.0 정책기 dollar 채널 약화 신호 |

★ ★M1 발견 (rate 직접 보다 dollar 채널·국면조건부 본질) **강확인**:
- 5y |β_dollar| / |β_rate| ratio = **107배** (1.26 vs 0.012).
- 모든 epoch 에서 ratio 19~1118 — rate 직접 채널 의미 X.
- **E1 ratio 95 vs E5 ratio 106** = dollar regime 변화에도 dollar 가 1차 driver 위치 유지.

## §3. ★rate-up 국면 조건부 dollar 강화 (M1 '2배 증폭' 가설) — **격하: 기각**

★ **main 격하 의무 (b) 이행**: 이전 박제 ("11/12 +5~32% 증폭 부호 일치") 는 SE/유의성 미검정 → **격하**.

5y daily rate-up (n=641) vs rate-down (n=595) split. 정식 β_dollar diff t-test (raw/macro_linkage_v2.py §2):

| ETF | β_d(up) | SE | β_d(dn) | SE | diff | SE_diff | t_diff | p (two-sided) | verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| mexico | -1.283 | 0.126 | -0.975 | 0.130 | -0.308 | 0.182 | -1.70 | 8.9e-02 | 부분 (p<0.10) |
| dm_exus | -1.360 | 0.087 | -1.267 | 0.082 | -0.093 | 0.120 | -0.78 | 4.4e-01 | n.s. |
| japan | -0.965 | 0.104 | -0.996 | 0.102 | +0.031 | 0.146 | +0.21 | 8.3e-01 | n.s. |
| germany | -1.770 | 0.107 | -1.620 | 0.101 | -0.150 | 0.147 | -1.02 | 3.1e-01 | n.s. |
| uk | -1.314 | 0.087 | -1.248 | 0.082 | -0.066 | 0.120 | -0.55 | 5.8e-01 | n.s. |
| em_broad | -1.255 | 0.110 | -1.161 | 0.097 | -0.095 | 0.147 | -0.65 | 5.2e-01 | n.s. |
| brazil | -1.194 | 0.167 | -1.068 | 0.153 | -0.126 | 0.227 | -0.56 | 5.8e-01 | n.s. |
| india | -0.758 | 0.093 | -0.667 | 0.086 | -0.090 | 0.126 | -0.72 | 4.7e-01 | n.s. |
| china | -1.464 | 0.205 | -1.332 | 0.158 | -0.132 | 0.259 | -0.51 | 6.1e-01 | n.s. |
| korea | -1.721 | 0.170 | -1.594 | 0.151 | -0.127 | 0.227 | -0.56 | 5.8e-01 | n.s. |
| taiwan | -1.222 | 0.131 | -1.044 | 0.125 | -0.178 | 0.181 | -0.98 | 3.3e-01 | n.s. |
| europe | -1.590 | 0.093 | -1.444 | 0.086 | -0.146 | 0.127 | -1.15 | 2.5e-01 | n.s. |

★ ★ ★ **결론 — 격하 (기각)**:
- 증폭 유의 (p<0.05): **0/12**.
- Bonferroni \|t\|>2.86 (α=0.05/12): **0/12**.
- 부분 (p<0.10): 1/12 (mexico 만 marginal, single-test p=0.089 → Bonferroni 조정 후 무의미).
- **★rate-up dollar 증폭 (M1 '2배 가설') = 순수 노이즈 → 기각**.
- 이전 박제 "1.05~1.32 ratio" 는 sample 변동으로 발생 noise. SE/유의성 미검정 박제 잘못.
- ★ block5 의 m1_dollar_channel_dominance hypothesis 박제 시 **국면조건부 부분 (rate-up 증폭) 명시적 배제**. dollar dominance 자체만 verified 등재.

## §4. cross-asset vs within-sleeve 구분 (★L축 caveat)

### 4.1 within-sleeve (12 country ETF pairwise daily corr)
| metric | value |
|---|---:|
| avg | **0.613** |
| range | [0.316, 0.977] |

top-5 pairs:
1. dm_exus ↔ europe **0.977**
2. germany ↔ europe **0.954**
3. dm_exus ↔ germany **0.928**
4. uk ↔ europe **0.917**
5. dm_exus ↔ uk **0.906**

→ DM Europe 클러스터 (europe / germany / uk / dm_exus) 끼리 **0.91~0.98** = 거의 동일 자산. 거시 driver 분리 후 잔차도 강 공통.

### 4.2 cross-asset (ETF ↔ driver)
| pair | avg | range |
|---|---:|---|
| ETF ↔ dollar | **-0.412** | [-0.569, -0.286] |
| ETF ↔ rate | -0.102 | [-0.144, -0.045] |
| ETF ↔ oil | +0.029 | [-0.064, +0.123] |

### 4.3 ★L축 판정
- within-sleeve avg **0.613** ∈ (0.5, 0.7) → **equity factor + 거시 driver 혼합**.
- 거시 loading 분리는 **부분 valid** — 거시 가 일부 설명 + 잔여는 equity factor (DM Europe 0.9+ cluster) + 국가 idio (EM 단일국 R² 0.10).
- **★ M1 caveat (within-sleeve 0.9+ 는 equity factor 소관)** 부분 발현: DM Europe 내부는 cross-asset 거시 driver 가 잡지 못하는 공통.
- → **eq_intl 의 거시 driver 가중 (dollar) 는 sleeve 외부 = cross-asset linkage 용**. within-sleeve dispersion (DM 끼리, 또는 brazil vs india) 의 거시 driver 분리는 부분 valid 만.

## §5. main 인계 핵심상관 (timeline.md M3 의무 답신)

### 5.1 거시 driver 핵심 상관 (5y, n=1254)

| driver | sleeve-avg β | sleeve-avg corr | 1순위 ETF | 1순위 magnitude |
|---|---:|---:|---|---:|
| **dollar (Δlog DXY)** | **-1.26** | **-0.412** | germany | β -1.68 / corr -0.55 |
| rate (Δ^TNX pp) | +0.012 | -0.102 | china | β +0.02 (약, 모두 ≈0) |
| oil (Δlog WTI) | +0.020 | +0.029 | brazil | β +0.085 (commodity exporter) |

### 5.2 epoch 별 dollar β (sleeve-avg)
- Pre-E1: -1.00 / **E1 -1.63** / E2 -1.28 / E3 -0.87 / E4 -1.19 / **E5 -0.79** (감소 신호)

### 5.3 M1 발견 검증 결과 (★ 격하 후 — verified / rejected 분리)
- ★ **dollar dominance (verified)**: rate 직접 vs dollar 채널 비교에서 dollar 가 1차 driver.
  - sleeve-avg |β_dollar|=1.26 (Bonferroni 12/12 생존, |t|=9.9~24.0, p<1e-22 ~ 1e-127)
  - sleeve-avg |β_rate|=0.012 (Bonferroni 1/12 생존, germany 만 |t|=4.08, 다른 모든 ETF noise)
  - 95% CI 12개 모두 음수 영역, 0 미포함
- ★ **rate-up 증폭 (★ 기각)**: 이전 박제 "1.05~1.32 ratio" 는 noise. 정식 diff t-test 0/12 유의 → M1 '2배 증폭 가설' 은 데이터로 지지되지 않음.
- ★ **R²↔유의성 분리 (정정)**: EM (brazil 0.097 / china 0.095 / india 0.101) 의 낮은 R² ≠ 거시 무관. 잔차분산 (idio) 큼이지 β_dollar 자체는 robust (|t|=9.9~11.5, Bonferroni 생존). dollar dominance 는 EM/DM 공통.

### 5.4 cross-asset vs within-sleeve
- within-sleeve avg corr **0.613** → equity factor + 거시 혼합. 거시 loading 분리 부분 valid.
- DM Europe (europe/germany/uk/dm_exus) 끼리 0.91~0.98 = within-sleeve 공통 dominant → 이 cluster 안에서는 거시 분리 의미 약.

## §6. 갱신 표지 (study_session.yaml 반영) — ★ 격하 반영

- block3 dollar-EM edge prior_strength 유지 + epoch 별 modulator 명시 (E1/E5 비교 boost).
- block4 dollar_beta_country base_weight 0.22 유지 (E1~E5 일관 dominant, Bonferroni 12/12 생존).
- block4 rate_beta_country base_weight 하향 검토 (5y \|β_rate\|≈0, Bonferroni 1/12 만 생존).
- block5 새 hypothesis `m1_dollar_channel_dominance_verified`:
  - **verified part**: rate 직접 vs dollar 채널 비교에서 dollar 가 1차 driver (5y |β_dollar|=1.26, Bonferroni 12/12 생존, p<1e-22~1e-127).
  - **★ 박제 금지**: 국면조건부 (rate-up 증폭) 부분 — 정식 diff t-test 0/12 유의 = 노이즈, 기각.
- block5 EM 약가중 시 R²-기반 근거 금지 (혼동 정정 의무) — '잔차분산 큼 = idio 큼' 별 근거 만 정당화.
- block6 ^TNX (10Y yield) 가용 추가 (Yahoo, 무료).
- ★ caveat (추론통계 누락 → R² 오해석 차단): 후속 분석에서 OLS β 보고 시 SE/t/p/95% CI/Bonferroni 임계 동반 의무.

## §7. caveat

- ^TNX = Yahoo 10Y yield index, FRED DGS10 와 일별 정합 가능하나 미검증.
- 5y 만 cover (2021-05 ~ 2026-05). 1980s/2008/2015 dollar cycle 미반영.
- regime 라벨 = timeline §3 의 ex-post epoch — OOS regime label 아니나, 분석 의도가 "각 epoch 에서 작동" 이라 ex-post 사용 정당.
- within-sleeve DM Europe cluster 의 거시 분리 잔차는 equity factor 소관 — M1 caveat 준수.
- E5 (2025-2026) = timeline 외 추가, Trump 2.0 dollar regime 가설 검증 자료.
- ★ main 독립검증 격하 (B−) 반영 (2026-05-30):
  - (a) R²↔유의성 혼동 정정: EM 낮은 R² ≠ 거시 무관, β_dollar Bonferroni 생존 EM/DM 공통 강확인.
  - (b) rate-up dollar 증폭 (M1 '2배 가설') 정식 diff t-test 0/12 유의 → 기각, 국면조건부 박제 금지.
  - (c) 추론통계 (t/p/95% CI) 명시 박제 의무 — §1.5 robust evidence 표 신설.
- ★ 'EM 약가중' 결정 시 R² 근거 사용 금지. 'idio 비중 큼 = 잔차분산' 별 근거만 정당화.
- 추가 가설 (mexico marginal p=0.089) 은 single-test, Bonferroni 조정 후 무의미.
