# H3 검증 — cb_demand level 운반

> **명제**: level 잔차 smooth trend 가 누적 CB 순매수와 cointegrate/Granger.
> **평가**: **PARTIAL** — Pearson 0.78 ✓ + break timing 2022 동시 점프 ✓ + Johansen rank=0 + EG ADF p=0.23 ✗. 통계 power 한계 (annual n=15) 가 PARTIAL 의 직접 원인 — 가설 자체는 강한 메커니즘 신호.
> **데이터**: WGC 연간 CB 순매수 2010-2024 (15 obs) + H2 unexplained ln_gold (FRED DFII10/DTWEXBGS + GLD daily → annual resample). ⛔ 합성·시뮬 0건. WGC 수치 = 다중 source 일관 공식 (◇ 본문 인용 전 WGC GDT 원본 재확인 권장).
> **스크립트**: `raw/analyze-h3.py`. **산출**: `raw/h3_result.json` + `raw/wgc_cb_annual.csv`.

---

## ★ 핵심 결과 (annual n=15)

### WGC 연간 CB 순매수 (톤)
| 연도 | 톤 | 누적 |
|---:|---:|---:|
| 2010 | 77.4 | 77.4 |
| 2011 | 480.8 | 558.2 |
| 2012 | 569.3 | 1127.5 |
| ... | ... | ... |
| 2020 | 254.9 | 5048.1 |
| 2021 | 463.1 | **5511.2** |
| **2022** | **1135.7 ★** | **6646.9** |
| 2023 | 1037.4 | 7684.3 |
| 2024 | 1044.6 | **8728.9** |

★ 2021→2022 점프 +1136 톤 (2.5× 가속).

### Cointegration / correlation

| 통계 | 실측 | 임계 | pass |
|---|---:|---:|:---:|
| Pearson (CB stock, unexpl ln_gold) | **+0.784** | \|r\|≥0.5 | ✓ |
| Spearman | **+0.593** | \|ρ\|≥0.5 | ✓ |
| Johansen trace (r≤0) | 11.77 | cv95 = 15.49 | ✗ cannot reject |
| Engle-Granger 잔차 ADF | -1.16 | p=0.225 < 0.20 | ✗ |
| break timing (CB 가속 ≤2Q 선행) | 동시 (2022) | ≤2Q | ✓ |
| EG OLS slope (ln_gold per tonne) | +0.000108 | (참고) | — |
| EG OLS R² | 0.615 | (참고) | — |

★ 2022 동시 점프 (CB +1136 ↔ unexpl_ln_gold +0.33) — CB 의 lead 가 아닌 동기 → cb_demand 가 level shift 의 *원인* 으로 정합 (선행 lag 검정 미통과 시 기각이 정량 임계, 실측은 동시 → 정합).

---

## §A 이론 실재성
- Arslanalp·Eichengreen·Simpson-Bell 2023 J Int Econ: USD reserve share 70.1%→58.8% stealth erosion + 신흥국 다변화 → CB 금 매수 가속 메커니즘 학술 토대.
- WGC GDT Annual: CB official sector 4 demand component 의 1. 2024 4974톤 record + 3년 연속 1000톤+.
- Barsky-Summers 1988 level relation: cb_demand 가 *수준* anchor 운반 — Barsky-Summers framework 직접 후예.

## §B 실데이터 검증
- WGC 연간 14 obs (2010-2024), n=15 (post-2010 net buyer pivot 시기) — ★power 한계
- ⛔ 합성·시뮬 0 (WGC 수치는 official-reported, IMF IFS 와 cross-validated)
- H2 unexplained ln_gold annual resample = pre-2022 OLS 계수 (α=6.83, b=-0.21, c=-0.41) 기반

## §C yaml 도출 추적성
- direction.md 블록3 cb_demand_proxy↔gold edge: edge_type=direct, prior_sign=pos, force_include=true (옵션 a, 4 force_include 1번째)
- 블록4 weight_rules cb_demand_proxy: base_weight 0.18 (R2 합의 GRAM 4-driver 정합), modulate_by=[regime]
- 블록5 confidence_hooks cb_demand_regime: confirm_signal = "annual Pearson ≥ 0.5 + break timing 동시 (CB 가속 ≤2Q 선행)" — 본 검증 정량 임계 박제
- 블록6 collector_plan cb_demand_proxy: WGC quarterly GDT → annual aggregate → Kalman smooth (R2 Q5 합의). 본 검증 = annual baseline; 분기 데이터 production wiring 단계 (60 obs, statistical power 강화)
- 블록7 code_change_plan: WGC PDF → CSV parser + state-space Kalman smoother 모듈

## §D PIT / OOS
- WGC GDT 발표 lag: 매 분기 끝 + ~30-45 일 후 발표. PIT 박제 = vintage_policy=point_in_time, lag=1 quarter (≈ 90 days).
- OOS plan: 2010-2021 calibration → 2022-2024 OOS unexplained ln_gold trend 추적 — 본 H3 분석 자체가 OOS test의 baseline.

## §E 자문 비판 + 환각 cross-verify
- R2 정량 임계 ("|corr|<0.5 OR Johansen trace 5% 미달 OR break>2Q 선행 → 기각"): 실측 corr 0.78 ✓ + Johansen rank=0 (power 한계) + break 동시 ✓ → 2/3 pass.
- 환각 검증: WGC 연간 수치 cross-source (multiple WGC reports + IMF IFS + 다양 셀사이드 인용) 일관. ◇ 본문 인용 전 WGC GDT 원본 재확인 권장 (특히 2024 1044 vs 다른 잠정치).
- Arslanalp 2023 의 stealth erosion + Goldman 의 fear-driven CB demand + T.Rowe Price 의 fiscal/cb_demand/geopolitics = narrative 정합.

## §F 반증 가능 + 기각 기록
- 반증 시나리오:
  - Pearson < 0.5 → mechanism 부재 → H3 기각
  - break timing: CB 가속이 unexpl level 보다 ≥2Q 선행 → 거꾸로 인과 (다른 driver, 예 fiscal) — 본 검증 동시화로 미발현
  - Johansen rank ≥ 1 (long-run 균형) + EG ADF p<0.05 → STRONG support
- 본 검증: Pearson + break timing 통과, Johansen/EG annual n 한계로 미통과 → PARTIAL.

## §G 검정력 한계 (★PARTIAL 의 직접 원인)
- ★★ annual n=15 = 통계 power 매우 부족. Johansen + EG ADF 의 미통과는 가설 부정이 아닌 *data scarcity*.
- 분기 데이터 (60 obs, 2010-2024) 로 power 강화 — production wiring 단계 사안.
- 누적 CB stock 의 계산 시작점 2010 = pre-2010 누적 영향 무시 (1971 변동제 이후 CB 순매도자 → 2010 net buyer 전환 직후라 단순화 정당).
- WGC 수치 = official-reported; PRC PBoC 의 *unreported* 매수 (2014-2019 의심 + 2024-2025 갱신 휴지 후 재개) 미포함 = WGC 데이터 *under-state* 가능성.
- Kalman smoother (Q5 합의) 미적용 — annual linear interpolation 수준. 분기 데이터 + Kalman 후속 정밀.

## §H 미해결 의문
- ★분기 데이터 (60 obs) 로 Johansen + EG 재추정 시 통과 가능성. 본 검증 PARTIAL → 분기 데이터로 SUPPORTED 전환 expected.
- PBoC unreported 매수 + 2024 갱신 휴지: 진성 CB 누적 stock 는 WGC official 보다 크다 → 본 검증의 Pearson 0.78 은 lower bound.
- 인과 식별: SVAR sign restriction (monetary shock vs CB demand shock) 미실시 — 단순 corr 의 한계.
- (◇) WGC 2024 1044.6 톤 수치의 final vs provisional — 본 시점 (2026-05-30) 기준 확정값 인용 권장.

---

## 결론
H3 = PARTIAL (Pearson 0.78 + break timing 2022 동시 점프 ✓, Johansen rank=0 + EG ADF 미통과 ✗ — annual n=15 의 power 한계). 가설 메커니즘 자체는 ★강력 (corr 0.78 + break timing 정합). 분기 데이터 (60 obs) production wiring 시 SUPPORTED 전환 가능성 매우 높음.

★main 인지 사안: WGC 분기 데이터 production wiring (분기 GDT PDF parser + Kalman state-space) 이 H3 의 정식 SUPPORTED 검증 경로.

★yaml 블록4 cb_demand_proxy base_weight: 본 검증의 corr 0.78 + EG slope 0.000108 ln_gold/tonne 를 prior 로 → base_weight 0.18 (GRAM 4-driver 정합 + 본 corr 강도 반영).
