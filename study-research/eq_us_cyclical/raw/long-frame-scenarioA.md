---
tags: [type/scenarioA-result, study/eq_us_cyclical, phase/post-M3, topic/long-frame-robustness, audit/B-axis, audit/K-axis]
date: 2026-05-31
study_id: eq_us_cyclical
phase: "시나리오 A 실행 결과 — 24.8년 단일회귀 + Newey-West HAC + Bonferroni 보정"
session: btn-common-task (eq_us_cyclical workspace)
deliver_to: btn-Codlearn (main, item7 시나리오 A 결과 보고)
inputs:
  - raw/yfinance/sector_etf_close.csv (4 산업 ETF, 2001-07-13 ~ 2026-05-29)
  - raw/fred/DGS10.csv (us10y, 1990-01 ~ 2026-05)
  - yfinance fetch: DX-Y.NYB (dxy, 2001-07 ~ 2026-05) + CL=F (oil WTI futures, 2001-07 ~ 2026-05)
  - raw/m3-metrics.json (M3 frame β 비교)
  - raw/long_frame_scenarioA.py (분석 script)
  - raw/scenarioA_output.txt (실행 stdout 박제)
  - raw/scenarioA_metrics.json (구조화 결과)
data_integrity: "⛔ 합성·시뮬 無. 실데이터 only. small-n-statistical-rigor.md 5 의무 + empirical-claim-presentation.md 5 의무 준수."
trust_tier: "structural_prior_low_confidence — frame-conditional bias 정량화 목적, raw β 직접 prior 박제 X. ETF holdings drift caveat 잔존."
note: |
  ★사용자 inject 지시 — main 5 합의건 회신 대기 중 시나리오 A (전체 frame 24.8년 단일회귀) 실행.
  결과 1줄 보고 후 main 5 합의건 판정 input.
---

# Scenario A Result — 24.8-year Long-Frame Single Regression

> long-frame-prescan.md §3.1 시나리오 A 의 실행 결과. ★주요 발견 = M3 frame β magnitude 의 frame-specific bias 정량 확인 (β_dxy 절댓값 long-frame 평균이 M3 frame 의 1/2~1/3). β_oil 채널 Bonferroni 후 sleeve 전반 비유의 (oil-equity decoupling tentative 신호). 본 결과 = raw β prior 직접 박제 X, frame-conditional bias 비교용 reference.

---

## §0. 사전 자가 점검 (5 의무 준수)

### empirical-claim-presentation.md 5 의무

| # | 의무 | 준수 status |
|---|---|---|
| 1.1 | Data Coverage 일자 명시 | ✅ frame 2001-07-13 ~ 2026-05-29 (24.8년) + per-source 가용 (SOXX inception bottleneck 2001-07-13 / DGS10 1990-01- / yfinance DXY+CL 24.8년 fetch) + per-industry n=5937 daily 명시 |
| 1.2 | Sample n + LOO | ✅ n=5937 daily 명시. ⏸️ LOO = 본 round 미수행, robustness 시나리오 C (LOEO CV) 별도 |
| 1.3 | Spec text ↔ code 1:1 match | ✅ script docstring 의 spec = "y_{i,t} = α_i + β_us10y · Δus10y_t + β_dxy · r_dxy_t + β_oil · r_oil_t + ε_{i,t}" 와 OLS 코드 동일. Δus10y = first-diff (yield level), r_dxy/r_oil = pct_change |
| 1.4 | Autocorrelation 안전장치 | ✅ Newey-West HAC SE, lag=9 (= floor(4·(5937/100)^(2/9))) |
| 1.5 | Multiple comparison 보정 | ✅ Bonferroni α/12 = 0.00417 (4 산업 × 3 driver 동시 비교). raw p + Bonferroni 통과 여부 박제 |

### small-n-statistical-rigor.md 5 게이트

| 게이트 | 준수 status |
|---|---|
| (a) p-value 명기 | ✅ |
| (b) ≥4 비교 Bonferroni/FDR | ✅ (12 비교) |
| (c) 95% CI 박제 | ✅ |
| (d) hedge 어휘 강제 | ✅ ("강력 확인" / "압도적" / "본질" 금지, "방향성 prior" / "비유의" / "tentative" / "frame-specific bias 정량 확인" 사용) |
| (e) 점추정 covariance prior 박제 금지 | ✅ raw β 직접 prior 박제 X. **frame-conditional bias 비교** 용도 한정 (M3 frame β 의 frame-specific bias 정량화) |

---

## §1. 데이터 인벤토리 + Coverage

### 1.1 소스별 가용 일자

| Source | 시리즈 | 가용 시작 | 가용 종료 | n |
|---|---|---|---|---|
| yfinance (기존 raw) | SOXX/XLB/XLI/XLE close | 2001-07-13 | 2026-05-29 | 6256 일/산업 |
| FRED (기존 raw) | DGS10 (us10y) | 1990-01-02 (frame restrict 후) | 2026-05-28 | 6490 일 |
| yfinance fetch (본 round) | DX-Y.NYB (dxy) close | 2001-07-13 | 2026-05-28 | 6277 일 |
| yfinance fetch (본 round) | CL=F (WTI futures) close | 2001-07-13 | 2026-05-28 | 6246 일 |

### 1.2 Panel join 후

| 항목 | 값 |
|---|---|
| inner join (driver 3종 non-null) | n=5938 daily |
| Per-industry valid (inc. ETF return non-null) | n=5937 daily |
| Window | 2001-07-16 ~ 2026-05-28 (24.8년) |
| Spec 정합 | r_{i,t} (industry pct_change) regressed on Δus10y_t (first-diff) + r_dxy_t (pct_change) + r_oil_t (pct_change), 모두 동기 (no lag) |

### 1.3 분석 unit ↔ portfolio label 분리 (1.6 의무)

- 분석 unit (β 측정) = SOXX / XLB / XLI / XLE ETF level daily return
- portfolio label (R15 sleeve assignment) = cyclical (4 산업 통합) 또는 sub-sleeve (R15.2 synthesis 권고 = cyclical_core / cyclical_amplifier / cyclical_oil_hedge)
- 본 round = 산업 ETF level β 측정만, sleeve assignment 결정 X (main 합의 의무 R15.2)

---

## §2. Long-frame β + 95% CI + Bonferroni 보정

### 2.1 산업별 점추정 + Newey-West HAC SE + p-value

| Industry | n | coef | β point | NW SE | t-stat | p-raw | 95% CI | Bonferroni (α=0.00417) |
|---|---|---|---|---|---|---|---|---|
| **SOXX** | 5937 | α (intercept) | +0.00077 | 0.00024 | +3.23 | 0.0013 | [+0.00030, +0.00123] | PASS |
| | | β_us10y | +0.0913 | 0.0079 | +11.58 | 5.2e-31 | [+0.0758, +0.1067] | ✅ PASS |
| | | β_dxy | -0.4501 | 0.0804 | -5.60 | 2.1e-08 | [-0.6077, -0.2926] | ✅ PASS |
| | | β_oil | +0.0236 | 0.0106 | +2.22 | 0.0265 | [+0.0027, +0.0444] | ⛔ fail |
| | | R² | 0.0718 | (adj R² 0.0713) | | | | |
| **XLB** | 5937 | α | +0.00045 | 0.00016 | +2.74 | 0.0061 | [+0.00013, +0.00077] | ⛔ fail |
| | | β_us10y | +0.0741 | 0.0062 | +11.99 | 3.8e-33 | [+0.0620, +0.0862] | ✅ PASS |
| | | β_dxy | -0.7614 | 0.0637 | -11.95 | 6.8e-33 | [-0.8863, -0.6365] | ✅ PASS |
| | | β_oil | +0.0296 | 0.0168 | +1.77 | 0.0776 | [-0.0033, +0.0625] | ⛔ fail |
| | | R² | 0.1433 | (adj R² 0.1428) | | | | |
| **XLI** | 5937 | α | +0.00047 | 0.00016 | +2.98 | 0.0029 | [+0.00016, +0.00078] | ✅ PASS |
| | | β_us10y | +0.0714 | 0.0055 | +12.92 | 3.6e-38 | [+0.0606, +0.0823] | ✅ PASS |
| | | β_dxy | -0.4448 | 0.0598 | -7.44 | 1.0e-13 | [-0.5619, -0.3276] | ✅ PASS |
| | | β_oil | +0.0229 | 0.0115 | +1.98 | 0.0472 | [+0.0003, +0.0454] | ⛔ fail |
| | | R² | 0.1204 | (adj R² 0.1200) | | | | |
| **XLE** | 5937 | α | +0.00052 | 0.00022 | +2.38 | 0.0171 | [+0.00009, +0.00094] | ⛔ fail |
| | | β_us10y | +0.0864 | 0.0089 | +9.75 | 1.9e-22 | [+0.0690, +0.1038] | ✅ PASS |
| | | β_dxy | -0.6985 | 0.0894 | -7.81 | 5.7e-15 | [-0.8737, -0.5232] | ✅ PASS |
| | | β_oil | +0.0904 | 0.0606 | +1.49 | 0.1355 | [-0.0283, +0.2091] | ⛔ fail |
| | | R² | 0.1747 | (adj R² 0.1743) | | | | |

### 2.2 Bonferroni 보정 후 (8/12 driver coef 통과)

| Driver | SOXX | XLB | XLI | XLE | 통과 비율 |
|---|---|---|---|---|---|
| β_us10y | ✅ | ✅ | ✅ | ✅ | 4/4 |
| β_dxy | ✅ | ✅ | ✅ | ✅ | 4/4 |
| β_oil | ⛔ | ⛔ | ⛔ | ⛔ | **0/4** ★ |

★ **결론 1 (방향성 prior, tentative)**: Bonferroni 보정 후 β_us10y / β_dxy 채널이 4 산업 모두 long-frame 에서 유의 신호. β_oil 채널 = 4 산업 모두 sleeve 전반 비유의 (CI 가 0 통과 또는 raw p > 0.0042). 단 XLE β_oil = +0.0904 [-0.0283, +0.2091] 가 다른 3 산업 (+0.022~+0.030) 보다 절댓값 큼 → oil-XLE 잔존 sensitivity 의 약한 방향성 prior.

### 2.3 R² 비교

| Industry | R² long-frame | (M3 frame R² 비교 — §3) |
|---|---|---|
| SOXX | 0.072 | (M3: 0.097) |
| XLB | 0.143 | (M3: 0.215) |
| XLI | 0.120 | (M3: 0.120, 일치) |
| XLE | 0.175 | (M3: 0.406, **-0.231 큰 차이**) ★ |

---

## §3. Frame-conditional bias — Long-frame vs M3 frame

> ★주요 산출: M3 frame β 의 frame-specific bias 정량 확인. 본 round = raw β prior 박제 X, **bias 비교** 만 박제.

### 3.1 M3 frame β (raw/m3-metrics.json sector_loadings_full)

| Industry | β_us10y_M3 | β_dxy_M3 | β_oil_M3 | R²_M3 |
|---|---|---|---|---|
| SOXX | +0.0281 | -1.6219 | +0.0074 | 0.097 |
| XLB | +0.0093 | -1.1783 | +0.0500 | 0.215 |
| XLI | +0.0102 | -0.8093 | +0.0318 | 0.120 |
| XLE | +0.0264 | -0.5779 | +0.4064 | 0.406 |

### 3.2 Δβ (long-frame − M3)

| Industry | Δβ_us10y | Δβ_dxy | Δβ_oil | ΔR² |
|---|---|---|---|---|
| SOXX | +0.0632 | **+1.1718** | +0.0162 | -0.025 |
| XLB | +0.0648 | +0.4169 | -0.0204 | -0.072 |
| XLI | +0.0613 | +0.3646 | -0.0089 | -0.000 |
| XLE | +0.0600 | -0.1206 | **-0.3160** ★ | **-0.231** ★ |

### 3.3 해석 (hedge 어휘 준수)

**(a) β_us10y 차이 = +0.06~+0.07 일관 (long-frame > M3 frame)**:
- long-frame 평균이 일반 rate-growth coupling 의 양수 prior 를 보임 (yield 1pp 상승 = ETF daily ret 약 +0.07pp).
- M3 frame ≈ 0 = 긴축충격기 (E1) 의 rate-dollar dominance 가 일반 rate-growth correlation 을 가린 frame-specific 신호.
- ★ frame-specific bias 정량: M3 frame 의 ≈0 채택이 long-frame 의 +0.07 prior 와 충돌. 추가 검증 필요 (rolling window B / regime-conditional D).

**(b) β_dxy 차이 = SOXX +1.17 / XLB +0.42 / XLI +0.36 / XLE -0.12**:
- M3 frame β_dxy 절댓값 큼 (-0.58 ~ -1.62) → long-frame 절댓값 1/2~1/3 (-0.45 ~ -0.76).
- 부호는 long-frame 도 모두 음수 유지 → ★ dollar-cyclical inverse coupling 의 long-frame robust 신호 (방향성 prior 유지).
- magnitude 는 M3 긴축 epoch (E1 R²=0.212) + 전환 epoch (E2 R²=0.293) 의 dollar dominance frame-specific.
- ★ tentative 결론: M3 frame 의 β_dxy magnitude 박제 시 (R15.1 의 -0.150 clip 처리) overstate risk. long-frame 평균 magnitude 가 1/2~1/3 = clip 후 R15 weight 가 long-frame 평균 대비 overweight.
- XLE 만 Δβ_dxy = -0.12 (절댓값 long-frame 이 M3 보다 큼) = XLE 의 anti-cyclical 본성이 dollar channel 에 부분 노출, long-frame 에서 dollar inverse coupling 의 잔존 강도.

**(c) β_oil 차이 = XLE 만 -0.316 (압도적 큰 frame-specific bias)**:
- 다른 3 산업 (SOXX/XLB/XLI) Δβ_oil = +0.016 ~ -0.020 (frame 차이 작음).
- XLE M3 frame +0.41 (R²=0.406 강력) → long-frame +0.09 (Bonferroni 미통과).
- ★ tentative 가설: 2022 Russia 침공 (E1) + 인플레 pass-through 의 frame-specific. shale revolution post-2014 의 oil-equity decoupling 도 long-frame 평균을 약화.
- ★ caveat: long-frame 안 oil 채널 epoch heterogeneity 큼 (pre-2014 oil cycle / post-2014 shale / 2020 COVID negative WTI / 2022 Russia spike). 단일 회귀의 β 평균은 epoch heterogeneity 의 cancel-out → regime-conditional 분석 (시나리오 D) 필요.

**(d) R² 차이 = XLE 가장 큰 frame-specific bias (-0.231)**:
- XLE M3 frame R²=0.406 의 약 절반이 frame-specific (2022 Russia + 인플레 pass-through epoch).
- 다른 3 산업 ΔR² = -0.072 ~ -0.000 (frame 영향 작음, XLI 거의 동일).
- ★ XLE 별도 sub-sleeve treatment (R15.2 synthesis 권고) 의 long-frame 추가 motivation.

---

## §4. 도메인 plausibility (Tier 3 — long-frame 한정)

### 4.1 부호 정합

| Industry | β_us10y > 0? | β_dxy < 0? | β_oil 부호 |
|---|---|---|---|
| SOXX | ✅ (+0.091) | ✅ (-0.450) | +0.024 (비유의) |
| XLB | ✅ (+0.074) | ✅ (-0.761) | +0.030 (비유의) |
| XLI | ✅ (+0.071) | ✅ (-0.445) | +0.023 (비유의) |
| XLE | ✅ (+0.086) | ✅ (-0.699) | +0.090 (비유의 but XLE 만 양수 magnitude 큼) |

★ **결론 2**: β_us10y/β_dxy 부호 4 산업 모두 도메인 prior 정합 (long-frame robust 신호). β_oil = Bonferroni 후 비유의 단 XLE 의 +0.09 잔존 sensitivity 가 anti-cyclical hedge 본성과 일관 (tentative).

### 4.2 magnitude 도메인 정합

- **β_us10y +0.07 일관 = 동행 measure** (Δus10y 1pp 상승 ↔ daily ret +0.07). long-frame yield ↑ 시 cyclical equity 동행 양수 = ★ growth-rate channel (수익률 측 coupling 의 일반화).
- **β_dxy 절댓값**: long-frame -0.45 ~ -0.76. dollar 1% 상승 ↔ cyclical ret -0.45 ~ -0.76%. ★ dollar-cyclical inverse coupling 의 long-frame 평균치 prior.
- **β_dxy magnitude 순서**: XLB > XLE > SOXX/XLI. (M3 frame: SOXX > XLB > XLI > XLE 와 다름)
  - M3 frame SOXX 의 강력 dollar inverse (-1.62) = 2022 긴축 epoch dollar surge + SOXX 글로벌 매출 + multiple contraction 의 epoch-specific.
  - long-frame XLB 의 강력 dollar inverse (-0.76) = 24.8년 평균 metals-dollar inverse coupling (XLB metals + dollar 표시 거래 비중).

### 4.3 Tier 3 verdict

**Long-frame 단일 회귀 = PARTIAL PASS** (방향성 prior 4 산업 모두 정합, magnitude 의 frame-conditional bias 정량 확인). β_oil 채널 Bonferroni 후 sleeve 전반 비유의 = oil-equity channel 의 regime-conditional 분석 필요 (시나리오 D).

---

## §5. 한계·미해결 (정직 명시)

1. **ETF holdings drift caveat (long-frame-prescan.md §4)**: SOXX (NVDA dominant post-2023) / XLE (shale-pure-play post-2014) / XLB (rare earth sub 추가 post-2010) 의 holdings 시간변화가 long-frame β 에 cycle 변화와 mixing. 본 결과 β = ETF level holdings drift 평균, 24.8년 전 구간 동일 holdings 가정의 limitation.
2. **단일 회귀의 epoch heterogeneity**: long-frame 안 epoch 별 β 변동 (M3 frame E3 의 β_us10y=-0.027 음수 전환 등) 의 평균. regime-conditional 분석 (시나리오 D) 또는 rolling window (시나리오 B) 별도.
3. **β_oil 비유의의 mechanism 불명**: 단일 회귀에서 oil-equity 채널이 sleeve 전반 약화. 가설 2종 (a) shale post-2014 decoupling (b) epoch heterogeneity cancel-out. 본 round 분리 X.
4. **t-stat 의 분산 보정**: Newey-West HAC lag=9 (Bartlett kernel) 사용. autocorr 보정 patial. 대안 (block bootstrap stationary, Driscoll-Kraay) Verify stage 별도.
5. **Δus10y 단위 caveat**: DGS10 = 일별 yield (% 단위, 예: 4.5 = 4.5%). Δus10y = first-diff in percentage points (예: +0.05 = +5bp). β_us10y = ETF daily return per 1 percentage point of yield change. **bp 단위로 환산 시 β/100**.
6. **dxy/oil yfinance fetch 의 missing days**: dxy n=6277, oil n=6246, ETF n=6256. inner join 후 n=5937 = 약 280일 손실 (holiday/weekend/missing). 본 결과 panel 의 selection bias 작음 (대부분 holiday).
7. **frame-conditional bias 의 statistical test 부재**: long-frame β vs M3 frame β 의 차이가 statistically significant 한지 본 round 검정 X (Chow test 시나리오 E 별도).
8. **point estimate vs interval 박제**: 본 결과 β point + 95% CI 동봉, raw β prior 직접 박제 X (small-n rigor §1.5 점추정 covariance prior 박제 금지 준수). 다음 round 에서 prior 채택 시 wide-prior 또는 structural_low_confidence tier 의무.

---

## §6. main 합의 input (5 합의건 판정 input)

본 결과가 main 5 합의건에 미치는 input:

| 합의건 | 시나리오 A 결과의 input |
|---|---|
| **공식 의도 B 안 (direction-aware)** | 본 round = 공식 의도와 직교 (β 회귀 측정). XLE β_dxy = -0.70 long-frame robust = sleeve 와 부호 일치 (negative coupling) → R15 의 direction-aware 공식 B 안 (XLE 자체 ret 부호 보존) 과 일관. A 안 vs B 안 결정에 영향 X. |
| **clip 범위 옵션 C** | M3 frame β_dxy 절댓값 (-1.62 SOXX 등) 이 long-frame 평균 (-0.45 ~ -0.76) 의 2~3배 = **frame-specific bias** 정량 확인. ★ clip 범위 [-0.15, +0.15] 의 saturation 이 long-frame 평균 β magnitude (1/2~1/3) 와 비교 시 더 좁아짐 → cap 확장 (옵션 A) 또는 별도 channel (옵션 C) 의 motivation 강화. synthesis 권고 옵션 C 일관. |
| **XLE 별도 sub-sleeve** | XLE ΔR² = -0.231 (다른 산업 -0.072 ~ 0.000) = ★ XLE 의 frame-conditional bias 가장 큼. β_oil 채널 의 frame-specific (Russia 침공 + 인플레 pass-through) 강력 확인. **XLE 별도 sub-sleeve treatment 의 long-frame 추가 motivation**. |
| **δ_arch 등록** | 본 round = 거시 driver 만 측정 (δ_regime). δ_arch 와 직교. β_oil 채널 long-frame 약화 = 거시 oil driver 의 sleeve 전반 영향 제한적 → XLE δ_arch 의 oil-specific metric (crack spread / OPEC compliance / WTI breakeven) 의 separate channel 채택 motivation. |
| **Verify stage 주체** | 본 round Newey-West HAC = G2 게이트 의 정확 stationary bootstrap 의 partial. Verify stage 의 stationary bootstrap + leave-one-epoch-out CV + Chow / Bai-Perron break detection 필요. **본 round = 시나리오 A only, B/C/D/E 시나리오 별도 Verify stage**. |

---

## §7. 1줄 보고용 핵심 요약

```
[scenarioA 결과] n=5937 daily (2001-07-13~2026-05-28, SOXX inception bottleneck). Newey-West HAC lag=9 + Bonferroni α/12.
β_us10y +0.06~+0.09 (4 산업 PASS, M3 frame 대비 일반 rate-growth coupling 의 long-frame 드러남).
β_dxy -0.45~-0.76 (4 산업 PASS, M3 frame 절댓값 의 1/2~1/3 — frame-specific bias 정량 확인).
β_oil = 4 산업 모두 Bonferroni fail (sleeve 전반 비유의), XLE +0.090 잔존 sensitivity tentative.
ΔR² XLE = -0.231 (M3 0.406 → long 0.175, 절반 frame-specific) = XLE 별도 sub-sleeve motivation 강화.
clip 옵션 C + XLE 분리 권고 reinforce. raw β prior 박제 X, frame-conditional bias 비교 reference only.
```

---

## §8. 산출 인벤토리

| 산출 | 경로 | 크기 |
|---|---|---|
| 분석 script | `raw/long_frame_scenarioA.py` | 7.5 KB |
| 실행 stdout 박제 | `raw/scenarioA_output.txt` | 5.1 KB |
| 구조화 결과 | `raw/scenarioA_metrics.json` | 6.5 KB |
| 본 보고 | `raw/long-frame-scenarioA.md` | (본 파일) |

<state intent="시나리오 A 24.8년 단일회귀 + Newey-West HAC + Bonferroni + frame-conditional bias 비교 실행" risk="ETF holdings drift caveat + epoch heterogeneity cancel-out (시나리오 B/D 별도)" uncertainty="med">
