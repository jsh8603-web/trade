---
tags: [type/findings, study/eq_us_cyclical, phase/M3, layer/macro-linkage]
date: 2026-05-30
study_id: eq_us_cyclical
phase: "M3 거시연관 — sleeve × epoch driver loading + L축 caveat"
inputs:
  - study-research/macro/timeline.md (M1 timeline 4 epoch)
  - study-research/eq_us_cyclical/raw/yfinance/sector_etf_close.csv
  - data/historical_{2022,2023,2024}/macro_yahoo_raw.json (us10y, dxy, oil)
script: raw/m3_analysis.py
output_json: raw/m3-metrics.json
period: "2021-12-01 ~ 2024-12-31 daily n=756 (joined macro-equity)"
data_integrity: "⛔ 합성·시뮬 無. 실데이터 only. 미릴리즈 PIT 정합 (M1 timeline 분기 경계 사용)."
---

# M3 Findings — eq_us_cyclical 거시연관

> Sleeve = XLY/XLI/XLB/XLE/XLF + SOXX (cyclical), defensive 대조 = XLP/XLU/XLV. M1 timeline 4 epoch 정렬 driver loading + within-sleeve corr (L축 caveat).

## §1. Epoch 분해 — sleeve 평균수익·sharpe

| Epoch | 기간 | n | cyc_ann | def_ann | excess_ann | vol_cyc | Sharpe_cyc |
|---|---|---|---|---|---|---|---|
| **E1 긴축충격** | 2022-01 ~ 2022-09 | 188 | **−24.3%** | −13.5% | −12.4% | 25.6% | **−1.11** |
| **E2 전환·반등** | 2022-10 ~ 2023-06 | 187 | **+38.7%** | +12.2% | **+23.7%** | 21.3% | **+1.63** |
| **E3 금리재상승** | 2023-07 ~ 2023-10 | 85 | −16.7% | −19.7% | +3.1% | 13.0% | −1.60 |
| **E4 pivot·인하** | 2023-11 ~ 2024-12 | 293 | **+28.7%** | +18.4% | +8.3% | 14.1% | **+1.75** |

**Per-sector epoch ret (annualized)** — XLE/SOXX 의 epoch 별 swing 가장 큼:

| Epoch | XLY | XLI | XLB | XLE | XLF | **SOXX** | XLP | XLU | XLV |
|---|---|---|---|---|---|---|---|---|---|
| E1 | −37.9 | −26.8 | −30.4 | **+47.9** | −27.2 | **−50.4** | −15.6 | −8.6 | −17.1 |
| E2 | +28.1 | +44.2 | +33.3 | +22.2 | +17.6 | **+88.7** | +18.3 | +3.1 | +15.0 |
| E3 | −27.5 | −21.8 | −21.3 | **+18.0** | −10.2 | −32.6 | −21.6 | −22.0 | −16.2 |
| E4 | +40.9 | +30.8 | +11.4 | +4.2 | **+43.7** | +39.6 | +17.0 | +27.0 | +10.8 |

★해석:
- **XLE = anti-cyclical hedge** 성격 (E1 +47.9% / E3 +18.0%, 긴축·금리재상승서 cyclical 평균 역행)
- **SOXX = 고듀레이션 amplifier** (epoch swing −50% → +89%, |variance| 최대)
- **E2·E4 = cyclical Sharpe 1.6+** (전환·완화 두 epoch 가 sleeve 의 보상기)
- **E1 = 유일한 사망 구간** (excess −12pp), E3 단기 reset 후 E4 회복

## §2. Driver loading r_sleeve ~ Δus10y + r_dxy + r_oil

### Full sample (n=756)

| target | α(ann) | β_us10y | β_dxy | β_oil | R² |
|---|---|---|---|---|---|
| **cyclical sleeve** | +0.156 | **+1.76**/bp·100 ≈ 0.018/bp | **−1.05** | +0.08 | 0.188 |
| defensive sleeve | +0.122 | −1.47/bp·100 ≈ −0.015/bp | −0.49 | −0.00 | 0.118 |
| **excess (cyc−def)** | +0.034 | +3.23/bp·100 | −0.56 | +0.09 | 0.147 |

### Per-sector loading

| sector | β_us10y | **β_dxy** | β_oil | R² |
|---|---|---|---|---|
| XLY | +0.002 | **−1.12** | −0.006 | 0.105 |
| XLI | +0.010 | −0.81 | +0.032 | 0.120 |
| XLB | +0.009 | **−1.18** | +0.050 | 0.215 |
| **XLE** | **+0.026** | −0.58 | **+0.41** | **0.406** |
| XLF | +0.030 | −1.00 | +0.011 | 0.134 |
| **SOXX** | +0.028 | **−1.62** | +0.007 | 0.097 |
| XLP | −0.005 | −0.51 | −0.018 | 0.091 |
| **XLU** | **−0.035** | −0.40 | +0.023 | 0.105 |
| XLV | −0.004 | −0.55 | −0.013 | 0.091 |

### ★Epoch-conditional cyclical sleeve loading

| Epoch | n | β_us10y | **β_dxy** | β_oil | R² |
|---|---|---|---|---|---|
| **E1 긴축충격** | 188 | +0.014 | **−1.34** | +0.058 | **0.212** |
| **E2 전환·반등** | 187 | +0.031 | **−1.12** | +0.119 | **0.293** |
| **E3 금리재상승** | 85 | **−0.027** | −0.40 | +0.047 | 0.131 |
| **E4 pivot·인하** | 275 | +0.004 | −0.51 | +0.074 | 0.070 |

★핵심 발견 — **rate 직접 < dollar 채널** (M1 발견 재확인):

1. **모든 cyclical sector β_dxy < 0** (−0.58 ~ −1.62), |β_dxy| ≫ |β_us10y| (1자리 차이). rate 가 주식에 미치는 영향은 **거의 dollar 를 경유**. M1 timeline §4 가이드("rate 직접 loading 보다 dollar 채널·국면조건부가 본질") **실측 확인**.
2. **국면조건부 dollar 강도 가변**: E1·E2 (긴축·전환) R² 0.21~0.29 / E3·E4 (재상승·완화) R² 0.07~0.13. **긴축·전환기 dollar 채널 가장 강함**.
3. **E3 만 β_us10y 음수** (−0.027) — 금리재상승기엔 rate 가 risk-off 신호로 직결, 나머지는 dollar 경유.
4. **SOXX/XLB/XLY = dollar 최민감** (β_dxy −1.12 ~ −1.62). 글로벌 매출·import-input 비중 큰 sector 가 환율 1차.
5. **XLE = 별도 채널** (oil β +0.41 dominant, dollar 영향 약). 에너지는 inflation-pass-through hedge.
6. **defensive duration-like**: XLU β_us10y −0.035 = 금리↑ 직접 타격 (utility 채권 유사). 반면 cyclical 은 β_us10y +양수 (성장기대 channel).

## §3. cross-asset vs within-sleeve corr (★L축 caveat)

### Within-cyclical pairwise corr matrix

|  | XLY | XLI | XLB | XLE | XLF | SOXX |
|---|---|---|---|---|---|---|
| XLY | 1.00 | 0.75 | 0.69 | **0.28** | 0.70 | 0.75 |
| XLI | 0.75 | 1.00 | 0.86 | 0.49 | 0.84 | 0.67 |
| XLB | 0.69 | 0.86 | 1.00 | 0.51 | 0.79 | 0.63 |
| **XLE** | **0.28** | 0.49 | 0.51 | 1.00 | 0.48 | **0.26** |
| XLF | 0.70 | 0.84 | 0.79 | 0.48 | 1.00 | 0.56 |
| SOXX | 0.75 | 0.67 | 0.63 | **0.26** | 0.56 | 1.00 |

- **mean off-diagonal corr (within-cyclical) = 0.617**
- cyclical-defensive mean pairwise corr = **0.465** (defensive 도 market beta 크게 공유)
- **★Kish design eff_N = 6 / (1 + 5·0.617) = 1.47**

### Per-sector rank-IC vs macro driver

| sector | d_us10y | **r_dxy** | **r_oil** |
|---|---|---|---|
| XLY | −0.114 | **−0.298** | +0.045 |
| XLI | −0.064 | **−0.322** | +0.106 |
| XLB | −0.090 | **−0.400** | +0.176 |
| **XLE** | +0.124 | −0.156 | **+0.602** |
| XLF | +0.007 | **−0.304** | +0.111 |
| SOXX | −0.036 | **−0.279** | +0.075 |
| XLP | −0.174 | −0.272 | −0.045 |
| XLU | **−0.237** | −0.216 | +0.008 |
| XLV | −0.141 | −0.277 | −0.016 |

★L축 caveat 진단:

- **within-cyclical sleeve 종목간 평균 corr 0.617** = 거시 driver 가 sleeve 평균에 대부분 흡수. Kish eff_N 1.47 → 6 종목이 실효 자유도 1.5 개. **within-sleeve diversification 효과 미미**.
- **cross-asset 차원에서만 거시 named factor 의미 있음** (M1 timeline §4·3 가이드 confirm). cyclical sleeve 평균 vs defensive sleeve 평균 비교가 거시 1회 계상의 유효 단위.
- **within-cyclical 종목간 비교는 거시 잔차 = equity factor 영역** — yaml 블록4 base_weight 의 `fwd_ep_normalized`·`asset_growth_yoy`·`capex_to_rev` 같은 종목 차별화 변수가 잡아야 할 영역. 시스템이 거시 dollar β 를 종목별 weight 에 한 번 반영하고 나면, 종목간 분산은 equity factor 모델에 위임.
- **XLE 가 within-sleeve outlier** (others 와 corr 0.26~0.51, 평균 0.41) — oil rank-IC +0.602 압도. **cyclical 일괄 처리 시 XLE 분리** 또는 별도 oil-driven 분기 강력 권고.

## §4. System 코드화 시사 (yaml 블록 보강 후보)

(★main 검토 후 study_session.yaml v3 으로 반영 — main 권한)

1. **블록3 relationships 보강**:
   - `dollar→cyclical_eps` prior_strength 현재 0.3 → **0.4 권고** (E1·E2 R²↑ 근거)
   - **NEW `oil→XLE_eps` prior_strength 0.7** (rank-IC 0.602 검증)
   - **NEW `dollar→soxx/xlb/xly_eps` prior_strength 0.5** (β_dxy −1.12~−1.62 sector-specific)

2. **블록2 신규 indicator**:
   - `dxy_beta_sector_1y` (per-sector dollar loading, lookback 252d rolling)
   - `oil_beta_xle_1y` (별도 트랙)

3. **블록4 base_weight 조정** (cyclical sleeve 안):
   - dollar 민감 (SOXX/XLB/XLY): `dxy_beta` 변수 weight +0.04
   - XLE: oil_beta dominant, 일반 cyclical weight schema 면제 또는 별도 sleeve

4. **블록6 collector_plan 우선순위**:
   - DXY 일별 (yfinance, 이미 적재)
   - Brent/WTI 양쪽 비교 (oil channel 단일성 확인)
   - **★ALFRED us10y vintage** (D축 미해결 audit 항목 보강) — main 인프라 도착 시

5. **블록3 epoch tagging 매크로**:
   - dollar 채널 강도 분기 (R² 0.07~0.29 가변) → regime tag 으로 belief b(t) 입력 (CONSULT-DECISIONS-layering Belief-Truth 격리 1순위 불변식 준수)
   - ⛔ corr_prior 직접 belief 누수 금지 — regime tag → gate 입력만

## §5. 한계·미해결

- **D축 (PIT/OOS)**: ALFRED vintage 미적용 (FRED 단일 vintage). rolling OOS 12M holdout 미수행. main 인프라 의존.
- **G축 (검정력)**: Driscoll-Kraay panel HAC SE 미적용, stationary bootstrap p-value 미산출. β 부호 robust 하나 SE 절댓값은 보수적 해석.
- **기간 한정**: 2021-12 ~ 2024-12 (3년, n=756). 장기 epoch (GFC/COVID) 미포함. 4 epoch 중 E3 만 n=85 (≤90d), conditional β 추정 분산 큼.
- **driver 선택 한정**: VIX/EBP/credit spread 미포함 (v2 validation H4 에서 d_VIX rank-IC −0.378 검증 — common-cause). M3 후속 round 에서 VIX driver 추가 검증 필요.

---

## 📡 main 회신 핵심 상관

- **★rate < dollar (1자리 차이)** — cyclical β_dxy −0.58~−1.62 vs β_us10y ~0 (XLE 제외). M1 발견 재확인.
- **★국면조건부**: E1·E2 (긴축·전환) R²=0.21·0.29 dollar 채널 최강 / E3·E4 (재상승·완화) R²=0.13·0.07 약화.
- **★Kish eff_N 1.47** (within-cyclical 0.617 corr) — within-sleeve 거의 단일 자유도, cross-asset 차원에서만 거시 1회 계상.
- **★XLE 분리 권고** — oil rank-IC +0.602, others corr 0.26~0.51 outlier.
- **★Sharpe**: E1 −1.11 / E2 +1.63 / E3 −1.60 / E4 +1.75 → 전환·완화 2 epoch 가 cyclical 보상 구간.
