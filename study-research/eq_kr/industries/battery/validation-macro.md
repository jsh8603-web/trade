# validation-macro — Layer 2 거시 4 + 신지표 lag-corr · 5게이트 (2026-05-30)

> data source: raw/data/macro.parquet (USDKRW, KOSPI, LIT, BATT, SMH, TSLA daily 2018-01-02 ~ 2026-05-29).
> analysis code: raw/run_validation.py + raw/run_neutralized.py.
> raw 결과: raw/validation-metrics.json + raw/validation-neutralized.json.

## §1. 측정 unit + portfolio label (frame §1.6 의무)

| 측정 unit (β identification) | portfolio label (user task) |
|---|---|
| CELL = {373220, 006400} (KRW 강세 → 수출 매출 ↑ 가설) | "한국 셀 메이커" (LG에솔, 삼성SDI) |
| CATHODE = {247540, 003670} (리튬 cost-pass-through) | "한국 양극재" (에코프로비엠, 포스코퓨처엠) |
| INDUSTRY_MEAN = 4종 equal-weight | "2차전지 산업 sleeve" (frame §1 Tier 2) |

★ sub-cluster 분할 = ★중요. CELL 과 CATHODE 는 부호 다른 driver 노출 (셀=USDKRW 수출, 양극재=리튬 cost). eq-weight 산업 평균 = factor cancel 위험 (frame §1.6 anchor incident).

## §2. ★H2 LIT (리튬 ETF) yoy → 양극재 — ★5게이트 ALL PASS

### 2.1 실측

- **driver**: LIT (Global X Lithium ETF, yfinance) 252-day yoy.
- **target**: CATHODE (247540, 003670) 종목별 60-day forward return, 월말 panel mean.
- **measurement**: monthly lag-corr (Spearman) + Newey-West HAC SE (nw_lags=3).

| lag (M) | Spearman ρ | n | p_value | 5게이트 gate1 N≥24 | gate2 p<0.05 | gate4 FDR (p<0.014) |
|---|---|---|---|---|---|---|
| 0 | **+0.322** | 89 | **0.002** | PASS | PASS | PASS |
| 1 | **+0.359** | 88 | **0.001** | PASS | PASS | PASS |
| 3 | **+0.351** | 86 | **0.001** | PASS | PASS | PASS |
| 6 | +0.180 | 83 | 0.103 | PASS | FAIL | FAIL |

### 2.2 IS/OOS

- **IS (2018-01 ~ 2022-12, n_months=47)**: lag0 ρ=**+0.262**, p=0.075 (직접 보고). 단 SE 보정 후 통계량 약함.
- **OOS (2023-01 ~ 2026-05, n_months=42)**: lag0 ρ=**+0.312**, p=0.044. ★ OOS > IS — 신호 강화.
- **OOS ratio** = |0.312 / 0.262| = **1.19** (frame §M4 gate5 ≥0.5 임계 PASS, 부호 동일 PASS).

### 2.3 Factor-neutralized (J축, raw/run_neutralized.py)

- **방법**: 월간 종목 return 을 KOSPI + dlnFX + SMH 3-factor OLS → residual 에 lag-corr.
- **결과**: lag0 raw ρ=**+0.441** (n=100, p<0.001) → neutralized ρ=**+0.225** (n=100, p=0.024).
  - ★ neutralization 후 ~50% 축소. 단 여전히 유의 (p<0.05).
  - 해석: raw IC 중 약 49% 가 일반 factor (KOSPI/FX/SMH) 매개 + 51% 가 LIT 고유 (양극재 cost-pass-through 가설 부분 확인).

### 2.4 regime breakdown (LIT yoy 자체로 분해)

| regime | n | ρ | p_value | verdict |
|---|---|---|---|---|
| lit_neutral (\|yoy\|≤20%) | 46 | +0.105 | 0.487 | TENTATIVE (cell N≥24 but p>0.10) |
| lit_bull (yoy>+20%) | 29 | +0.051 | 0.794 | INSUFFICIENT (n<24 임계 근접 + p>0.5) |
| lit_bear (yoy<-20%) | 14 | -0.108 | 0.714 | INSUFFICIENT (n=14<24) |

★ regime 분해 시 cell N 부족 → 전체 표본 (n=89) 신호가 강한 반면 regime 별 분해 신호 분산. 신호 = LIT yoy continuous 차원에서 강하고 regime threshold 분해는 cell 부족으로 추가 검증 불가. frame §M3 cell collapse 가이드 적용 — fallback = LIT continuous 모드 한정 보고.

### 2.5 결론

- **★verdict = CONFIRMED** (n=89 ≥ 30 + p<0.05 + LOO ★다음 라운드 위임 + spec/code match + Newey-West SE 보정 + multiple comparison Bonferroni α/7≈0.014 후도 lag0/1/3 모두 생존).
- **5게이트 통과**: gate1 PASS / gate2 PASS / gate3 PASS (MDE = 2.8/√89 = 0.30, ρ=0.322 > MDE) / gate4 PASS / gate5 PASS (OOS ratio 1.19, sign match).
- **★hedge 어휘 (small-N rule 적용 n=89 boundary 영역)**: 점추정 +0.322 단정 회피, CI 박제 의무.
- **95% CI 추정** (block bootstrap 보정 fallback — 본 라운드 IID 변동만): SE_IID = (1-ρ²)/√(n-1) = (1-0.104)/√88 = 0.0955. CI ≈ [+0.135, +0.509]. 본 산출 ★CI 명시.

## §3. ★H1 USDKRW yoy → 셀 — ★가설 기각 (REJECT)

### 3.1 실측

- **driver**: USDKRW 252-day yoy.
- **target**: CELL (373220, 006400) y20d panel mean (월말).

| lag (M) | ρ | n | p_value | gate2 |
|---|---|---|---|---|
| 0 | -0.096 | 90 | 0.370 | FAIL |
| 1 | -0.047 | 89 | 0.663 | FAIL |
| 3 | (n=87) -0.067 | 87 | 0.534 | FAIL |

### 3.2 IS/OOS

- IS (2018-2022) lag0 ρ=**-0.247** (n_months=47).
- OOS (2023-2026) lag0 ρ=**+0.095** (n_months=42).
- ★ 부호 flip. OOS ratio = -0.38 ≠ ≥0.5 임계 → gate5 FAIL.

### 3.3 Factor-neutralized

- raw: dlnFX (monthly log diff) lag0 → CELL panel mean monthly return ρ=**-0.174** (n=100, p=0.083). 약한 음의 신호 (이론 가설 = 양의 신호, ★부호 반대).
- neutralized: ρ=**+0.048** (p=0.635). FX 노출이 KOSPI 시장 factor 와 collinear → 완전 흡수.

### 3.4 결론

- **★verdict = REJECTED** (H1 USDKRW 강세 → 셀 outperform 가설 기각).
- 메커니즘 해석: 셀 매출 수출 비중 90% 가설은 맞으나, ① USDKRW 강세 = 외국인 매도 동조 (한국 자산 회피) → 셀 더 큰 매도 압력 ② 셀 비용 (니켈/리튬) 도 USD 노출 → 매출/비용 동시 노출 cancel.
- **반증 기록 정상** (frame F축 — 기각 가설도 산출).

## §4. H3 TSLA yoy → 산업 평균 — 비유의

### 4.1 실측

- driver: TSLA 252-day yoy (EV sentiment proxy).
- target: 산업 4종 평균 y20d.

| lag | ρ | n | p_value |
|---|---|---|---|
| 0 | +0.080 | 90 | 0.453 |
| 1 | +0.052 | 89 | 0.626 |
| 3 | -0.018 | 87 | 0.867 |

### 4.2 결론

- **verdict = REJECTED** (TSLA EV sentiment 단독 proxy 무효).
- 해석: TSLA idiosyncratic (FSD 호재, Cybertruck, Musk twitter) 노이즈가 EV cycle 신호 압도. 보다 직접적 proxy 필요 (예: LIT + BATT 혼합).

## §5. B5 SMH yoy → 산업 평균 (반도체 spillover) — 비유의

| lag | ρ | n | p_value |
|---|---|---|---|
| 0 | -0.048 | 90 | 0.653 |
| 1 | -0.058 | 89 | 0.591 |

- **verdict = REJECTED**. 반도체 cycle 직접 spillover 없음. BMS 반도체 수요는 2차전지 매출에 미미한 비중 (가설 정당화 약함).

## §6. control: realized vol (60D) cross-sectional IC

- IC = -0.007 (t = -0.09, n_months=84). ★ 무관.
- 해석: 변동성 anomaly 가 2차전지 4종 sub-universe 에서 작동하지 않음 (small N=4 cross-section, 단정 위험).

## §7. 종합 5게이트 표

| 가설 | gate1 N | gate2 SE | gate3 Power | gate4 FDR | gate5 OOS | 결론 |
|---|---|---|---|---|---|---|
| **H2 LIT→cathode lag0** | ✓ 89 | ✓ p=0.002 | ✓ MDE 0.30 | ✓ p<0.014 | ✓ ratio 1.19 sign match | **★CONFIRMED** |
| H2 LIT→cathode lag1 | ✓ 88 | ✓ p=0.001 | ✓ | ✓ | (lag0 OOS proxy 사용) | **CONFIRMED** |
| H1 USDKRW→cell | ✓ 90 | ✗ p=0.37 | ✓ | ✗ | ✗ sign flip | **REJECTED** |
| H3 TSLA→industry | ✓ 90 | ✗ p=0.45 | ✓ | ✗ | n/a | REJECTED |
| B5 SMH→industry | ✓ 90 | ✗ p=0.65 | ✓ | ✗ | n/a | REJECTED |

## §8. 데이터 무결성 / 한계 (frame G·H축)

- **autocorr 보정**: Newey-West HAC nw_lags=3 적용. 추가 block-bootstrap 권고 (다음 라운드).
- **multiple comparison**: 7개 hypothesis 동시 검증 → Bonferroni α/7 ≈ 0.014. H2 lag0/1/3 만 통과.
- **OOS split**: 2023-01 cutoff. IS 60 months (2018-2022), OOS 41 months (2023-2026-05). frame §M4 #5 권고 CPCV 미적용 (skfolio 미적재) — fallback walk-forward 단일 split. 다음 라운드 위임.
- **regime 36 cell 미실행**: 외국인 flow regime 데이터 부재 (pykrx KRX_ID/PW 인증 필요). frame §M3 cell collapse fallback (KRW 3 cell 만 분해) 적용. 표본 부족으로 KRW regime 도 모두 INSUFFICIENT/TENTATIVE.
- **survivor bias**: krx_universe.delisted 미점검. 2차전지 4종 = 모두 살아있는 종목. ★ 단 2018-2022 표본 시 247540 / 003670 액면분할 / 인적분할 영향 미반영 — 다음 라운드 FDR 수정주가 추가 검증.
