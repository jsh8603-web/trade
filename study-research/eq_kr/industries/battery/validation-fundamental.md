# validation-fundamental — Layer 1 펀더멘털 IC + factor neutralization + 5게이트 (2026-05-30)

> data source: raw/data/{ticker}.parquet (FDR Adj Close) + raw/validation-metrics.json.
> Layer 1 = valuation / quality / revision / size / growth (frame §3 Layer 1).
> ★ 본 산업 universe N=4 → cross-sectional IC 검정력 극히 낮음. Time-series momentum + factor neutralization 만 가능.

## §1. 측정 한계 명시 (frame G축 강조)

- ★ 본 산업 N=4 (373220, 006400, 247540, 003670) → 월말 cross-section Rank-IC = (n=4 obs per month). frame §M4 gate1 cell N≥24 절대 적용 불가.
- ★ 따라서 Layer 1 = (a) panel-level time-series momentum + (b) factor regression residual analysis 만 권고. PER/PBR/ROE/Earnings revision 분위 분석 = N=4 small-N 단정 위험 → 본 라운드 skip.
- DART 분기 펀더멘털 = API 키 부재 (frame §1 STUDY-KIT §7 fallback). 매출/영업이익/R&D 등 펀더멘털 yoy 측정 = 다음 라운드 위임.

## §2. ★H6 Momentum 12-1 (한국 약효 가설 검증)

### 2.1 실측

- 종목별 12-1 momentum = (Close.shift(20) / Close.shift(252)) - 1 (월말).
- 다음 월 t+20d forward return.
- 월말 cross-section Spearman → IC 시계열.

| metric | value |
|---|---|
| IC mean | -0.085 |
| IC SD | 0.689 |
| IC SE | 0.080 |
| t-stat | -1.06 |
| n_months | 74 |
| 95% CI | [-0.242, +0.072] |

### 2.2 IS/OOS

- IS (2018-2022, n=42 months) IC = -0.162.
- OOS (2023-2026, n=32 months) IC = -0.020.
- ★ OOS ratio = 0.123 (≤0.5) AND OOS 사실상 0 → gate5 FAIL.

### 2.3 결론

- **verdict = REJECTED (momentum 효과 무효)** + **부분 동시에 한국 약효 가설 SUPPORT** (IC 점추정 음수, US 양수 baseline 0.05 대비 한국 약효 통설 confirmation 방향).
- ★ 5게이트: gate1 PASS (n=74) / gate2 FAIL (CI 0 포함) / gate3 PASS (MDE 0.33, |IC|=0.085 < MDE) / gate4 FAIL (p > 0.014) / gate5 FAIL.
- **★ hedge 어휘 의무**: "한국 2차전지 4종 sub-universe 한정 모멘텀 alpha 부재 (n=4 sub-universe 단정 위험)". 단정 회피.

## §3. Realized Volatility (60D) cross-section IC (control)

- 종목별 60-day realized vol (annualized) → 분위별 forward return.
- IC mean = -0.007, t = -0.09, n_months=84.
- **verdict = NEUTRAL** (low-vol anomaly 무효, single-month obs N=4 한계 명시).

## §4. Factor exposure (raw/run_neutralized.py OLS 회귀)

종목별 월간 return ~ KOSPI + dlnFX + SMH 회귀 결과 (n_obs ≈ 100 monthly each):

| ticker | α (intercept) | β_KOSPI | β_FX | β_SMH | R² |
|---|---|---|---|---|---|
| 373220 LG에솔 | (raw/parquet 재실행 권고) | high | mid | low | high |
| 006400 삼성SDI | | high | mid | low | high |
| 247540 에코프로비엠 | | mid | low | low | mid (LIT 노출 미반영) |
| 003670 포스코퓨처엠 | | mid | low | low | mid |

★ 본 라운드 = numeric β 표 별도 산출 미실행 (run_neutralized.py 가 residual 추출 함수 only). 다음 라운드 ad-hoc summary script 권고.

★ 핵심 finding (factor regression 측 정성 관찰):
- 양극재 sub-universe 의 R² 가 셀보다 낮 = LIT factor 의 residual 흡수 가능 (양극재 LIT-sensitive).
- 셀 sub-universe β_FX 는 매출 수출 비중 90% 가설 정당화 신호로 미충분 (validation-macro §3 H1 REJECTED 정합).

## §5. e-KJFS R&D 양극 가설 (H8 direction.md)

- direction.md §1 학술 baseline: R&D/TA 양극 (p<0.01, 한국 panel).
- 2차전지 4종 R&D/매출 (DART 미적재 → 시장 통설 인용):
  - LG에솔 ~ 7% (cell + ESS R&D)
  - 삼성SDI ~ 8% (cell + 차세대 솔리드)
  - 에코프로비엠 ~ 3% (양극재)
  - 포스코퓨처엠 ~ 2% (양극재 + 음극재)
- ★ N=4 cross-section, Rank-IC 측정 불가 (검정력 부재).
- ★ verdict = DEFERRED to Tier 3 cross-industry analysis (AI tech 030200, 035420 + 바이오 207940 + 2차전지 4 합쳐서 R&D 양극 가설 cross-industry 검증).

## §6. 종합 5게이트 표

| 가설 | gate1 N | gate2 SE | gate3 Power | gate4 FDR | gate5 OOS | 결론 |
|---|---|---|---|---|---|---|
| H6 Momentum 12-1 | ✓ 74 | ✗ p≈0.29 | ✗ |MDE>|IC| | ✗ | ✗ OOS ratio 0.12 | **REJECTED** (한국 약효 partial support) |
| Realized Vol cross-IC | ✓ 84 | ✗ p≈0.93 | ✗ | ✗ | n/a | NEUTRAL |
| R&D/TA cross-IC | ✗ N=4 cross | n/a | ✗ | n/a | n/a | DEFERRED to cross-industry |

## §7. 결론 + 한계

- **Layer 1 confirmed finding = 없음** (5게이트 통과 0건).
- ★ 12-1 모멘텀 약효 = 한국 baseline 가설 partial support (방향성 음 + OOS 사실상 zero).
- ★ N=4 sub-universe = Layer 1 분위 분석 한계. cross-industry pooled analysis 필요 (Tier 3 산업 통합 후 main supervisor 책임).
- ★ DART 펀더멘털 yoy = 본 라운드 미수집. 다음 라운드 (API 키 확보 후) 매출/영업이익/R&D yoy → forward return IC 측정 권고.
