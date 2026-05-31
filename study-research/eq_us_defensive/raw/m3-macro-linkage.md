---
tags: [type/macro-linkage, study/eq_us_defensive, phase/M3]
date: 2026-05-30
study_id: eq_us_defensive
target: main M4 factor seed
ref: study-research/macro/timeline.md §4
---

# M3 거시연관 — eq_us_defensive sleeve vs Macro Factor

> macro/timeline.md §4 가이드 준수: (1) epoch별 sleeve 분해 (2) macro driver loading 회귀 (3) cross-asset vs within-sleeve 구분 → main M4 factor seed 입력

## 데이터

- **FRED**: DGS10 (rate), DFII10 (real_rate), DTWEXBGS (DXY broad), BAMLH0A0HYM2 (HY OAS)
- **ETF**: XLP, XLU, XLV, XLF, XLC, SPY (Yahoo Finance)
- **분석 .py**: `raw/m3_macro_linkage.py` (OLS β + R² + Pearson corr)
- **표본 범위**: 일별 2023-05-31 ~ 2026-05-22 (n=742 일) — HY OAS 일별 시리즈 가용 한계
- **Epoch labels** (timeline §3): E0 pre-2022 / E1 긴축 2022Q1~Q3 / E2 전환 2022Q4~2023Q2 / E3 재상승 2023Q3 / E4 pivot 2023Q4~

## (1) Epoch별 sleeve excess return (sector - SPY 월별)

| Epoch | n월 | XLP-SPY | XLU-SPY | XLV-SPY | XLF-SPY | XLC-SPY | sleeve-SPY |
|---|---:|---:|---:|---:|---:|---:|---:|
| **E2 전환·반등** | 2 | -0.0516 | -0.0561 | -0.0347 | -0.0229 | +0.0085 | **-0.0413** |
| **E3 rate 재상승** | 3 | -0.0117 | -0.0206 | +0.0017 | +0.0071 | +0.0144 | -0.0059 |
| **E4 pivot·인하** | 32 | -0.0111 | -0.0035 | -0.0128 | -0.0037 | -0.0001 | -0.0078 |

★발견:
- 본 sleeve 가 모든 epoch 에서 *underperform* SPY (E2 가장 극단 -4.1%/월)
- 단 XLC (Comm) 만 E2/E3 에서 outperform → archetype 분리 정당화
- E1 긴축 (2022Q1~Q3) 시기 데이터 부족 (HY OAS 일별 가용 2023-05~)

## (2) Macro factor loading OLS (Full sample, n=742 일)

```
sector ~ α + β_rate·Δrate + β_real·Δreal_rate + β_dxy·r_dxy + β_hy·Δhy + ε
```

| sector | α | β_rate | β_real | β_dxy | β_hy | R² |
|---|---:|---:|---:|---:|---:|---:|
| XLP | +0.000315 | -0.0177 | -0.0158 | **-0.1522** | -0.0153 | 0.0754 |
| **XLU** | +0.000574 | -0.0239 | **-0.0436** | **-0.1805** | -0.0283 | 0.1431 |
| XLV | +0.000236 | -0.0173 | -0.0295 | +0.0259 | -0.0366 | 0.1359 |
| **XLF** | +0.000522 | +0.0244 | -0.0728 | **+0.1519** | **-0.0804** | **0.3668** |
| XLC | +0.000698 | +0.0014 | -0.0496 | -0.0726 | -0.0740 | 0.3030 |
| SPY | +0.000619 | +0.0079 | -0.0562 | -0.0103 | -0.0830 | 0.4403 |

★발견:
- **XLF (banks) β_dxy = +0.152 vs XLU (util) β_dxy = -0.181** — sub-sleeve **dollar 채널 부호 반대** (R² XLF 0.37 = 본 sleeve 의 가장 강한 신호)
- **XLV, XLF, XLC R² = 0.14~0.37** — macro factor 가 *상당히* 설명
- **XLP R² = 0.075** — staples 는 macro factor 약 (idio risk dominant)

## (3) Epoch-conditional β (★M1 dollar 채널 rate-regime 부호 반전 확인)

### E3 (rate 재상승, 2023Q3, n=63 일)

| sector | β_rate | β_real | β_dxy | β_hy | R² |
|---|---:|---:|---:|---:|---:|
| XLP | +0.0415 | -0.0851 | **+0.2150** | -0.0297 | 0.2360 |
| XLU | +0.0480 | -0.1238 | **+0.5743** | -0.0590 | 0.2317 |
| XLV | +0.0462 | -0.0921 | **+0.6633** | -0.0332 | 0.1886 |
| XLF | +0.0635 | -0.1170 | **+0.2014** | -0.0442 | 0.3145 |
| XLC | -0.0194 | -0.0347 | -0.1524 | -0.0531 | 0.2245 |

### E4 (pivot·인하, 2023Q4~, n=657 일)

| sector | β_rate | β_real | β_dxy | β_hy | R² |
|---|---:|---:|---:|---:|---:|
| XLP | -0.0276 | -0.0052 | -0.1363 | -0.0148 | 0.0692 |
| XLU | -0.0330 | -0.0375 | -0.1799 | -0.0280 | 0.1466 |
| XLV | -0.0249 | -0.0234 | -0.0146 | -0.0380 | 0.1415 |
| XLF | +0.0174 | -0.0644 | **+0.1545** | -0.0834 | 0.3715 |
| XLC | +0.0030 | -0.0462 | -0.0853 | -0.0772 | 0.3186 |

### ★M1 발견 강력 확인

**Dollar 채널 rate-regime 부호 반전**:

| sector | β_dxy E3 (rate↑) | β_dxy E4 (rate↓) | 차이 (E3-E4) |
|---|---:|---:|---:|
| XLU | **+0.574** | -0.180 | **+0.754** |
| XLV | **+0.663** | -0.015 | +0.678 |
| XLP | +0.215 | -0.136 | +0.351 |
| XLF | +0.201 | +0.154 | +0.047 (안정) |
| XLC | -0.152 | -0.085 | -0.067 |

★**rate-up regime 에서 방어 sleeve (XLU/XLV/XLP) dollar loading 2~5배 폭증** → M1 가설 "dollar 채널 rate-up 2배" 직접 확인 (XLU 의 경우 +0.57 = 2배 이상)

XLF (banks) 만 stable — rate-regime 무관 dollar 호재 일관

## (4) Within-sleeve corr (cross-asset vs within-sleeve 구분 — M1 caveat)

### Pearson corr (full sample, n=742 일)

|  | XLP | XLU | XLV | XLF | XLC | SPY |
|---|---:|---:|---:|---:|---:|---:|
| XLP | 1.000 | 0.605 | 0.614 | 0.574 | 0.534 | **0.675** |
| XLU | 0.605 | 1.000 | 0.530 | 0.492 | 0.425 | 0.610 |
| XLV | 0.614 | 0.530 | 1.000 | 0.622 | 0.629 | **0.779** |
| XLF | 0.574 | 0.492 | 0.622 | 1.000 | 0.669 | **0.828** |
| XLC | 0.534 | 0.425 | 0.629 | 0.669 | 1.000 | **0.865** |

★발견:
- **방어 4 (XLP/XLU/XLV/XLC) 평균 pair corr = 0.556**
- **방어 ~ SPY 평균 corr = 0.732**
- → 방어주가 *자기들끼리 (0.55)* 보다 *SPY 와 더 유사 (0.73)* — common equity factor (market beta) dominant
- **M1 caveat 적용**: defensive 내부 0.55 = 거시 factor 아니라 **equity common factor** (자기 sleeve 모델 소관)
- → M4 의 거시 named factor 후보 = **dollar (XLF/XLU 부호 반대 + epoch 부호 반전)** + credit (XLF 의 -0.08 잔여)

## (5) M4 factor seed 권고 (main 입력용)

본 실측 기반 M4 거시 factor seed:

### Factor 1: Real Rate Dichotomy (강 anchor)
- **sub-archetype 부호 분기**: XLU/XLP NEG / XLF POS (H1 검증 완료, partial IC -0.17 ~ +0.13, n=5844)
- **Cross-sleeve linkage**: util/staples 가 bond proxy 그룹 (gold/long bond 과 같은 duration 채널)

### Factor 2: Dollar Channel Rate-Regime Switch (★M1 발견)
- **rate-up regime**: 방어 sleeve dollar loading +0.2 ~ +0.66 (XLV/XLU 가장 민감)
- **rate-down regime**: 방어 sleeve dollar loading -0.1 ~ -0.18 (부호 반전)
- **XLF**: rate-regime 무관 dollar loading 일관 양 (+0.15~+0.20)
- → M4 의 dollar named factor 는 **rate-regime conditional** 필수

### Factor 3: Credit Cycle (banks 특화 잔여)
- 시장 베타 흡수 후 XLF partial IC = -0.166 (n=752 일) → banks provisioning channel 잔여
- 방어주는 시장 베타 흡수 후 +0.07 ~ +0.10 (residual 회복력)
- → M4 의 credit factor 는 **industry sub-archetype 분기 적용** 필수 (banks NEG / defensive POS)

### Factor 4: Equity Common (within-sleeve caveat)
- 방어 sleeve 내부 corr 0.55 vs SPY 0.73 → **거시 factor 아닌 equity common factor**
- M4 거시 layer 아닌 *equity factor model* 영역
- → M4 에서 본 sleeve 의 equity common 은 SPY beta 로 흡수, 별도 처리 X

## (6) 한계 (정직)

1. **표본**: 2023-05~2026-05 (3년) — E1 긴축 (2022Q1~Q3) 데이터 부족 (HY OAS 일별 시리즈 가용 한계)
2. **E2, E3 n월=2, 3** — Bootstrap CI 산출 불가, 평균만
3. **WTI (oil) 미포함** — 본 분석 4 factor 만 (rate, real_rate, dxy, hy_oas)
4. **regime 정의 = simple OLS β** — partial-corr conditioning 또는 RegimeGlasso 미적용 (full version 은 main M4 가 통합 검증)

## 참조

- `m3_macro_linkage.py` (분석 .py)
- `m3-metrics.json` (정량 결과)
- `validation-H1.md` (real rate dichotomy 풀 H1 anchor)
- `validation-H4.md` (credit beta sub-sleeve 분기)
- study-research/macro/timeline.md §4 (가이드 원문)
