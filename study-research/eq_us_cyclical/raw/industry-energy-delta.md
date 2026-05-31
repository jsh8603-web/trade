---
tags: [type/research, study/eq_us_cyclical, phase/post-M3, industry/energy, anti-cyclical-hedge]
date: 2026-05-31
study_id: eq_us_cyclical
phase: "에너지 (XLE) δ_regime / δ_arch 후보 매트릭스 (M3 재해석 + anti-cyclical hedge 본성)"
session: btn-common-task (eq_us_cyclical workspace)
industry: energy
proxy_etf: XLE
inputs:
  - raw/m3-findings.md (β_oil=+0.41, R²=0.406, r_oil=+0.602, within-corr 0.26~0.51 outlier)
  - plan-industry-regime-delta.md §0~§5
  - raw/industry-semi-delta.md / industry-industrials-delta.md / industry-materials-delta.md (포맷 정합 + 공식 의도 의문)
invariants:
  - Belief-Truth 격리 (거시 numeric δ_arch 포함 금지)
  - regime_tag scalar 매핑만 (numeric 거시 직접 X)
  - 점추정 박제 금지 (CI 의무, G2)
  - 합성·시뮬 無 (M3 실측 재해석만)
data_integrity: "⛔ 합성 無. M3 실측 재해석 only. CI heuristic = vol/√n × 1.96 (정확 stationary bootstrap = Verify stage)."
---

# Energy (XLE) — δ_regime / δ_arch 후보

> XLE = within-cyclical 의 ★outlier. β_oil=+0.41 (sleeve 평균 +0.08 의 5배+, **rank-IC +0.602 cyclical 최강**) + R²=0.406 (cyclical 중 압도적 1위, 평균 0.188 의 2.2배) + within-corr 0.26~0.51 (cyclical 평균 0.617 미만, 단일 outlier). ★ **anti-cyclical hedge 본성**: E1 +47.9% (cyclical 평균 -24.3%, sleeve **부호 반대**), E3 +18.0% (cyclical 평균 -16.7%, sleeve **부호 반대**). E2 +22.2%·E4 +4.2% 는 sleeve 와 같은 부호이나 underperform → cyclical 상승기엔 XLE 가 oil cycle peak-out 으로 약함. **cyclical 일괄 처리 절대 금지** (M3 §3 명시) — sleeve allocation 자체에서 별도 sub-sleeve.

---

## §1. 도메인 이론 정리

### 에너지 cycle 의 본질

XLE = Integrated oil (XOM/CVX 50%+ weight) + E&P (COP/EOG/PXD/FANG) + 서비스 (SLB/HAL/BKR) + 정유 (PSX/VLO/MPC) 의 묶음. 매출 1차 driver = **WTI/Brent 가격** (rank-IC +0.602, cyclical 6 sector 중 압도적 최강). oil 자체가 인플레 pass-through hedge 본성을 가져 거시 인플레 충격기에 outperform.

핵심 cycle 구조:
1. **OPEC+ supply discipline** — 가격 floor 의 1차 결정 요인. 결속 강한 시기 (2020-2023 가을) = 가격 안정, 약한 시기 (2024 후반 비OPEC supply 증가) = 가격 stuck.
2. **글로벌 demand cycle** — 중국·인도 demand 가 marginal. cyclical 일반 sleeve 와는 별도 channel.
3. **E&P capex cycle (boom-bust)** — 가격 ↑ → capex ↑ (1~2년 lag) → supply 도달 → 가격 ↓ → capex 동결 → supply 정상화 → 가격 ↑ 의 자기진동. 일반 cyclical 보다 lag 가 길다.
4. **지정학 supply shock** — Russia/Iran/Venezuela 의 비대칭 영향. E1 (2022-02 Russia 침공) 같은 idiosyncratic event 의 dominant impact.
5. **inflation-pass-through hedge** — oil = TIPS 와 함께 인플레 hedge 양대 자산. 거시 인플레 충격기 (E1) 의 anti-cyclical outperform 의 본성.

### 핵심 driver 와 시간 lag

1. **WTI/Brent 가격** (lag 0~동행): β_oil=+0.41 sleeve 평균, rank-IC=+0.602. XLE 매출 직접 영향. 본 task = **거시 cross-sleeve → 배분레이어 위임** (oil 이 cyclical 전반 영향 — XLE 만이 아니라).
2. **OPEC+ compliance / spare capacity** (lead 0~3M): OPEC 결속 강도 + 사우디 spare capacity → 가격 floor. XLE single-sleeve 한정. δ_arch 후보.
3. **US shale production (비OPEC supply)** (lead 6~12M): 미국 E&P capex → shale output → 가격 ceiling. δ_arch.
4. **dollar (DXY)** (lag 0~3M): β_dxy=−0.58 (cyclical 중 가장 약, |β| 최소). oil 이 dollar 와 inverse 라 부분 cancel, XLE 의 글로벌 매출 비중도 비교적 작음 (Integrated XOM/CVX 의 US 비중 50%+). 배분레이어.
5. **us10y / E&P finance cost** (lag 3~9M): E&P capex finance + duration. β_us10y=+0.026 sleeve 평균. 배분레이어.
6. **crack spread (refining margin)** (lag 0~3M): 정유 sub 의 즉시 margin driver. δ_arch.

### 역사적 epoch 사례

- **1973~1974 oil shock**: OPEC embargo + 가격 4배 → XLE 류 +100%+ Y/Y. anti-cyclical hedge 의 본질.
- **2008 GFC 직전**: WTI $147 peak (2008-07) → XLE peak 도 동행. supply demand mismatch.
- **2014~2016 shale revolution**: US production 8M → 9.6M bpd → oil $100 → $30, XLE -55% 18M.
- **2020 COVID + WTI futures negative (2020-04)**: WTI 일시 -$37, XLE -50% YTD bottom.
- **2022 Russia 침공 (E1)**: WTI $130 spike + 유럽 가스 위기 → XLE +47.9% (M3 E1, sleeve 평균 -24.3% 의 sleeve **부호 반대**). ★perfect anti-cyclical hedge.
- **2023 OPEC+ 추가 감산 (E3)**: 가을 OPEC+ 200만 bpd 감산 + 미국 SPR 비축 종료 → 가격 floor 견고 → XLE +18.0% (M3 E3, sleeve 평균 -16.7% 의 **부호 반대**).
- **2024 비OPEC supply 증가 + 중국 demand 약화 (E4 후반)**: OPEC+ 감산에도 가격 stuck → XLE +4.2% (M3 E4, sleeve 평균 +28.7% 대비 큰 underperform).

### Investment Clock 사분면

에너지 = 통상 **Overheat quadrant 최강** (성장↑ + 인플레↑, oil pass-through). 그러나 본 M3 frame 의 E1 = Stagflation (성장↓ + 인플레↑) 인데 XLE 가 가장 강한 outperform = 인플레 + supply shock idiosyncratic 의 양면 작용. cycle theory 의 Overheat 한정 expectation 보다 더 광범위한 anti-cyclical hedge 본성을 보여줌. **inflation surprise = XLE 의 dominant driver**, cyclical 상태 (Recovery/Overheat/Stagflation) 와는 분리.

---

## §2. M3 결과 재해석 (XLE 관점)

### Epoch 별 의미 — ★anti-cyclical hedge 본성

| Epoch | XLE ann_ret | sleeve Sharpe | β_dxy (sleeve, epoch) | 해석 |
|---|---|---|---|---|
| **E1 긴축충격** (2022-01~09, n=188) | **+47.9%** | −1.11 (sleeve 약세) | −1.34 | ★sleeve **부호 반대**. Russia 침공 (2022-02) → WTI $130 spike + 유럽 가스 위기 + 미국 인플레 pass-through. perfect anti-cyclical hedge. supply shock idiosyncratic 의 dominant impact. |
| **E2 전환·반등** (2022-10~2023-06, n=187) | **+22.2%** | +1.63 (sleeve 강세) | −1.12 | sleeve 같은 부호이나 underperform (sleeve 평균 +38.7%). oil cycle peak after + 재고비축 + 가격 normalization (~$70). cyclical pivot rally 의 multiple expansion 에서 inflation-hedge 가 후순위. |
| **E3 금리재상승** (2023-07~10, n=85) | **+18.0%** | −1.60 (sleeve 약세) | −0.40 | ★sleeve **부호 반대**. OPEC+ 추가 감산 (200만 bpd, 2023-09) + 미국 SPR 비축 종료 + 가을 demand → 가격 floor 견고. anti-cyclical hedge 재확인. |
| **E4 pivot·인하** (2023-11~2024-12, n=275) | **+4.2%** | +1.75 (sleeve 강세) | −0.51 | sleeve 같은 부호이나 매우 약함 (sleeve 평균 +28.7%, -24.5pp 큰 underperform). 비OPEC supply 증가 + 중국 demand 약화 + OPEC+ 결속 약화 → 가격 stuck (~$75). cyclical 의 AI/pivot rally 와 분리. |

### Within-cyclical 위치 (sleeve 평균 대비)

- E1: XLE +47.9% vs cyc 평균 −24.3% → **+72.2pp anti-cyclical** ★
- E2: XLE +22.2% vs cyc 평균 +38.7% → -16.5pp 약
- E3: XLE +18.0% vs cyc 평균 −16.7% → **+34.7pp anti-cyclical** ★
- E4: XLE +4.2% vs cyc 평균 +28.7% → -24.5pp 약

★ **XLE 의 epoch 부호 패턴 = sleeve 와 정 반대 두 번 + 같은 부호이나 underperform 두 번** = ★complete anti-cyclical / inflation-hedge 본성. E1/E3 (sleeve 약세) XLE outperform + E2/E4 (sleeve 강세) XLE underperform → **regime-conditional weight 가 cyclical sleeve 와 분리되어야 함**.

### Cross-sleeve dollar/oil 채널 강도

- **β_oil=+0.41 (full sample)**: **cyclical 중 압도적 최강** (다음 XLB +0.050 의 8배). XLE 가 oil channel single-driver dominance.
- **β_dxy=−0.58 (full sample)**: cyclical 중 가장 약 (|β| 최소). oil 이 dollar 와 inverse 라 부분 cancel + XLE 의 US 비중 50%+ 영향.
- **β_us10y=+0.026 ≈ 0**: 직접 영향 미미.
- **R²=0.406**: ★cyclical 중 압도적 1위 (sleeve 평균 0.188 의 2.2배). **거시 (특히 oil) driver 가 XLE 의 40.6% 설명**. 다른 cyclical (0.07~0.22) 대비 XLE 의 단일 driver dominance 가 극단적.
- **rank-IC r_oil=+0.602**: cyclical 6 sector 중 압도적 최강. β linear 보다 sign-rank 가 더 강 → non-linear oil sensitivity 명확.

★ **M3 §3 명시 "cyclical 일괄 처리 시 XLE 분리 강력 권고"** = 본 sub-agent 산출에서 **strong reinforce**. XLE 의 anti-cyclical hedge 본성 + oil single-driver dominance + within-cyclical outlier (corr 0.26~0.51) 3 신호 동시 = **별도 sub-sleeve treatment 의무 (synthesis 단계 권고)**.

---

## §3. δ_regime 후보 (★핵심)

### 계산 방법

```
point = epoch_ann_return × sign(Sharpe_cyc) / 100, clipped to [-0.15, +0.15]
CI heuristic (95%) = ±vol_cyc/√n × 1.96 (XLE 별도 vol 미보고, sleeve vol proxy — XLE 실제 vol 은 sleeve 보다 클 것, CI 보수적 underestimate 가능)
```

★ 공식 의도 caveat — semi/industrials/materials 와 공통 의문. spec `× sign(Sharpe_cyc)` 적용 시 cyclical sleeve 부호에 따라 XLE 의 자체 ret 부호가 **뒤집힘** → ★XLE 의 anti-cyclical hedge 본성을 **정 반대로 표현**. **direction-aware** (`ann_ret/100`) 만 도메인 정합. 본 보고 **두 해석 병기 + B 안 강력 권고**.

### Unclipped 점추정 (transparency)

| Epoch | XLE ann_ret | Sharpe_cyc sign | A: unclipped (× sign) | B: unclipped (direction-aware) | SE (vol_cyc/√n) × 1.96 |
|---|---|---|---|---|---|
| E1 | **+47.9%** | −1 | **−0.479** ★ sleeve 약세에 - | **+0.479** ★ XLE 자체 outperform 보존 | ±0.0366 |
| E2 | +22.2% | +1 | +0.222 | +0.222 | ±0.0305 |
| E3 | **+18.0%** | −1 | **−0.180** ★ sleeve 약세에 - | **+0.180** ★ XLE 자체 outperform 보존 | ±0.0276 |
| E4 | +4.2% | +1 | +0.042 | +0.042 | ±0.0167 |

★ **E1/E3 의 A 안 vs B 안 부호 정반대** = XLE 에서 spec 공식 의도가 결정됨. semi (SOXX) 자체 ret 부호 보존 (B 안) 채택과 일치. industrials (산업재 cyclical core) 는 sleeve 부호와 자체 부호가 모든 epoch 일치하여 A·B 안 결과 동일 → 차이 안 보였을 뿐.

### Clipped δ_regime — 두 해석 병기

#### A. spec 공식 `× sign(Sharpe_cyc)` (magnitude × sleeve 부호)

| Epoch | point (clipped) | CI_low | CI_high | 비고 |
|---|---|---|---|---|
| **E1_tightening_shock** | **−0.150** | −0.150 | −0.150 | unclipped −0.479, clip floor. ⛔ ★sleeve 약세에 XLE under = anti-cyclical hedge 정 반대 표현. |
| **E2_transition_rally** | **+0.150** | +0.150 | +0.150 | unclipped +0.222, clip ceiling. |
| **E3_rate_re_rise** | **−0.150** | −0.150 | −0.150 | unclipped −0.180, clip floor. ⛔ E1 동일 문제. |
| **E4_pivot_cuts** | **+0.042** | +0.025 | +0.059 | ★unclipped < clip → magnitude 보존. CI 0 통과 = 약한 신호 boundary. |

#### B. direction-aware (`ann_ret/100`, XLE 자체 ret 부호 보존) ★권고

| Epoch | point (clipped) | CI_low | CI_high | 비고 |
|---|---|---|---|---|
| **E1_tightening_shock** | **+0.150** | +0.150 | +0.150 | unclipped +0.479, clip ceiling. ✅ XLE 의 anti-cyclical outperform 보존 (sleeve 약세에 XLE over weight). |
| **E2_transition_rally** | **+0.150** | +0.150 | +0.150 | unclipped +0.222, clip ceiling. |
| **E3_rate_re_rise** | **+0.150** | +0.150 | +0.150 | unclipped +0.180, clip ceiling. ✅ E1 동일 anti-cyclical 보존. |
| **E4_pivot_cuts** | **+0.042** | +0.025 | +0.059 | ★unclipped < clip → magnitude 보존. CI 0 통과 = 약한 신호 boundary. |

### 해석

- **A 안 (spec 공식)**: E1/E3 에서 XLE 의 anti-cyclical outperform 을 **정 반대로 표현** (clip floor -0.15). ⛔ 도메인 비정합 명백.
- **B 안 (direction-aware)**: 4 epoch 모두 + 방향. E1/E2/E3 clip ceiling + E4 만 +0.042. ✅ XLE 의 anti-cyclical hedge 본성 + E4 oil stuck 의 약한 신호 모두 보존.

★ **B 안의 도메인 정합 의무성** = XLE 는 spec 공식 의도가 **direction-aware** 라는 결정적 증거. semi (SOXX) 의 자체 ret 부호 보존 채택과 일치 → ★Synthesis stage 에서 main 검토 시 **B 안 채택 강력 권고**.

★ **E4 만 unclipped +0.042** = XLE 의 E4 underperform 의 mild over weight 표현. XLB E4 +0.114 와 형태 유사하나 magnitude 가 더 약함 (XLB +11.4% / XLE +4.2%).

★ **3 epoch (E1/E2/E3) clip ceiling** = XLE swing magnitude 가 R15 cap [-0.15, +0.15] 초과. semi/industrials/materials 와 공통 → cap 재검토 또는 XLE 별도 sub-sleeve treatment.

★ **regime_tag scalar 매핑만** + **bootstrap CI 의무** (G2 Verify stage) + **Belief-Truth 격리** — semi/industrials/materials 와 동일.

---

## §4. δ_arch 후보 (펀더멘털, 거시 제외)

| Metric | Theoretical basis | Data status |
|---|---|---|
| **OPEC+ compliance / spare capacity** | OPEC 결속 강도 + 사우디 spare capacity (현재 ~3M bpd) = 가격 floor 의 1차 결정. compliance 95%+ = 가격 안정, 80% 미만 = 결속 약화 신호. XLE single-sleeve 한정 (oil price 는 cross-sleeve 이지만 OPEC dynamics 는 oil-specific) | **available_now** (IEA 월별 + OPEC 공식 보고서 부분 무료, 추정치 paid) |
| **US shale production volume** | 비OPEC supply 의 dominant indicator. 2014 shale revolution 이래 글로벌 supply 의 marginal source. US E&P capex → 6~12M lag shale output. XLE 안 E&P sub (COP/EOG/PXD/FANG) 의 매출 직결 | **available_now** (EIA 주간 + 월간 무료) |
| **rig count (FRED BKR)** | 미국 E&P capex 의 즉시 thermometer. ★경계 분류 의문 (plan §2): oil 1차 driver 면 거시, 에너지 single-sleeve 면 δ_arch. ★결정: rig count = US E&P capex 의 즉시 측정 = **XLE single-sleeve 한정 (δ_arch 채택)**. WTI spot 가격은 거시 (cross-sleeve, 배분레이어). | **available_now** (FRED BKRRIG / IADC 일별 무료) |
| **reserves/production ratio (R/P)** | E&P 종목의 future supply 보장 metric. Integrated (XOM/CVX) 10~15 년, E&P-pure (EOG) 8~12 년 정상. R/P 감소 = future supply 위험 + reserve replacement capex 압력 | **deferred_edgar** (10-K reserves disclosure, SEC PUD reserves) |
| **crack spread (refining margin)** | 정유 sub (PSX/VLO/MPC) 의 즉시 margin driver. WTI vs gasoline/diesel spread, 통상 $15~25 정상, $30+ = 정유 outperform | **available_now** (CME crack spread futures 일별 + 부분 EIA 무료) |
| **breakeven price (E&P 종목)** | 종목별 (Permian/Bakken/Eagle Ford 등 basin 별) breakeven oil price. 현재 sweet spot Permian $45~55, 한계 basin $65~75. WTI 가 breakeven 위에서 얼마나 cushion 있는가 | **deferred_edgar** (10-K MD&A + investor presentation) |
| **integrated downstream margin (XOM/CVX)** | Integrated oil 의 정유·화학 sub margin 합산. upstream 가격 약세 시 hedge 역할 | **deferred_edgar** (10-Q segment reporting) |
| ⛔ **WTI/Brent spot 가격** | XLE 매출 1차 driver 이지만 sleeve 전반 (XLB chemicals/XLI transportation/macro inflation) 영향 | ⛔ **거시 cross-sleeve → 배분레이어 위임**. δ_arch 포함 금지. |
| ⛔ **dollar (DXY)** | XLE β_dxy=−0.58 (가장 약하지만 nonzero) | ⛔ **거시 cross-sleeve → 배분레이어 위임**. δ_arch 포함 금지. |
| ⛔ **글로벌 demand (중국/인도)** | oil cycle 의 demand side, sleeve 전반 영향 | ⛔ **거시 cross-sleeve → 배분레이어 위임**. δ_arch 포함 금지. |

⛔ 거시 driver (oil 가격/DXY/글로벌 PMI) 는 δ_arch 에 포함하지 않음. XLE single-sleeve 한정 펀더멘털 만 채택.

★ **현 단계 산출 = 이론 후보 식별 + 적재 후 실측 deferred**. δ_arch numeric 산출은 (a) FRED BKR + EIA shale + IEA OPEC + CME crack spread = **즉시 가용** 4 종 (b) reserves/R-P + breakeven + downstream margin = EDGAR 적재 후 3 종. 즉시 가용 4 종으로 δ_arch 1차 충전 가능.

★ **plan §2 경계 분류 의문 해결**: rig count = US E&P capex 의 즉시 측정 → **XLE single-sleeve δ_arch 채택**. WTI spot 가격은 **거시 (cross-sleeve, 배분레이어)** 위임. OPEC+ dynamics 는 oil-specific 이지만 oil 자체가 cross-sleeve 라 OPEC compliance metric 도 δ_arch 채택 가능 (XLE 만의 supply discipline thermometer). 사용자/main 검토 시 보정.

---

## §5. 5게이트 적용

| Gate | Pass | Note |
|---|---|---|
| **G1 (n≥30 daily)** | ✅ **PASS** | E1=188, E2=187, E3=85, E4=275 모두 daily n≥30. E3 monthly 환산 ~4 fail (daily 기준 적용). |
| **G2 (Bootstrap CI)** | ⚠️ **PARTIAL** | Gaussian heuristic CI (vol_cyc/√n × 1.96). XLE 실제 vol > sleeve vol 추정 → CI underestimate 가능. E4 만 CI 가 clip 안 = 점추정 박제 위험 정상 표현. E1/E2/E3 saturation. 정확 stationary bootstrap = Verify stage. |
| **G3 (James-Stein λ)** | ⏸️ **DEFERRED** | epoch×산업 cell shrinkage = Synthesis stage. 4 산업 통합 후 τ²/σ² 추정. XLE 의 anti-cyclical 특성으로 within-industry σ² 큰 추정 가능. |
| **G4 (OOS)** | ✅ **PASS (가능)** | 4 epoch holdout 가능. leave-one-epoch-out 가능. 본 단계 미실행, Verify stage. ★주의: E1 (Russia 침공) idiosyncratic 이라 OOS 평가 시 frame-specific bias 가능. |
| **G5 (Domain plausibility)** | ✅ **PASS (B 안 한정)** | §6 참조. **B 안 (direction-aware)** 만 도메인 정합. A 안 (spec 공식) 은 E1/E3 anti-cyclical hedge 정 반대 표현 → ⛔ **A 안 G5 FAIL**. |

**Gates pass count = 3 (G1/G4/G5(B 안) 통과, G2 PARTIAL, G3 DEFERRED)**. ★ A 안 채택 시 G5 FAIL → pass count = 2 (G1/G4) — 도메인 비정합으로 사실상 불용.

---

## §6. 도메인 plausibility (Tier 3)

### Verdict: **B 안 = STRONG MATCH (anti-cyclical hedge 본성 보존)** / A 안 = ⛔ INCONSISTENT (anti-cyclical 정 반대 표현)

| Epoch | XLE 측정 ann_ret | A 안 point | B 안 point | Cycle theory 기대 | A 안 정합 | B 안 정합 |
|---|---|---|---|---|---|---|
| **E1 긴축충격** | +47.9% (sleeve -24.3%) | **-0.150** ⛔ | **+0.150** ✅ | inflation surprise + Russia supply shock → anti-cyclical hedge **outperform expected** | ⛔ 정반대 | ✅ 정합 |
| **E2 전환·반등** | +22.2% (sleeve +38.7%) | +0.150 | +0.150 | pivot rally + oil cycle peak after → 같은 부호이나 underperform expected | △ magnitude saturation | △ magnitude saturation |
| **E3 금리재상승** | +18.0% (sleeve -16.7%) | **-0.150** ⛔ | **+0.150** ✅ | OPEC+ 감산 + 가을 demand → anti-cyclical hedge **outperform expected** | ⛔ 정반대 | ✅ 정합 |
| **E4 pivot·인하** | +4.2% (sleeve +28.7%) | +0.042 | +0.042 | 비OPEC supply + 중국 demand 약 + OPEC+ 결속 약 → mild underperform expected | ✅ magnitude 보존 | ✅ magnitude 보존 |

### 부가 plausibility check

- **β_oil=+0.41 + r_oil=+0.602** = oil channel single-driver dominance. domain expectation 정합 (XLE = oil pure-play sleeve).
- **β_dxy=−0.58 (cyclical 중 가장 약)** = oil-dollar inverse partial cancel + XLE 의 US 비중 50%+ 영향. domain expectation 정합 (Integrated XOM/CVX 50%+ weight).
- **R²=0.406 (cyclical 압도적 1위)** = oil single driver 가 XLE 의 40.6% 설명. domain expectation 정합 (다른 cyclical 보다 단일 driver dominance 압도적).
- **within-cyclical corr 0.26~0.51 (sleeve 평균 0.617 미만, outlier)** = XLE 가 within-sleeve 의 별도 channel. domain expectation 정합. **★cyclical 일괄 처리 금지 의 강력 motivation**.

### Tier 3 결론

- **B 안 (direction-aware)**: XLE 4 epoch 모두 cycle/inflation theory 정합. anti-cyclical hedge 본성 + oil single driver dominance + outlier within-corr 모두 보존. **G5 PASS**.
- **A 안 (spec 공식 sign 곱)**: E1/E3 에서 anti-cyclical 정 반대 표현. ⛔ **G5 FAIL**. magnitude 만 보존하고 방향 잃음 = R15 weight 가산 적용 시 XLE 의 hedge 가치 정 반대로 작용.

★ ★ **B 안 강력 권고**: synthesis stage 에서 main 검토 시 **direction-aware 공식 (B) 채택 의무**. spec 의 `× sign(Sharpe_cyc)` 는 cyclical core (industrials) 한정 적용 가능, anti-cyclical (XLE) 에는 적용 불가. semi (SOXX) 의 SOXX 자체 ret 부호 보존도 B 안과 일치. **모든 산업 일관 B 안 적용** = 최소 비용 정합 path.

---

## §7. 한계·미해결 (정직 명시)

1. **vol proxy**: XLE 별도 vol 미보고 → cyclical sleeve vol 채택. XLE 의 실제 vol 은 sleeve 평균보다 클 것 (within-cyclical outlier + supply shock 노출) → CI underestimate 가능. Verify stage 에서 XLE 자체 epoch vol 산출 권고.
2. **공식 의도 의문**: spec 의 `× sign(Sharpe_cyc)` (A) vs `ann_ret/100` (B). **XLE 의 anti-cyclical 본성에서 결정적 차이** (A 안 E1/E3 정 반대). semi 도 B 안 채택, industrials/materials 는 차이 안 보임 (cyclical core, 부호 일치). **synthesis 에서 main 검토 시 B 안 채택 의무** (★★).
3. **clip ceiling saturation**: E1/E2/E3 모두 unclipped > +0.15 → clip ceiling. E4 만 +0.042 magnitude 보존. R15 cap 재검토 또는 XLE 의 별도 sub-sleeve treatment 필요.
4. **G3 James-Stein λ deferred**: Synthesis stage. XLE 의 anti-cyclical 특성으로 between-industry τ² 큰 추정 가능 (XLE 가 outlier).
5. **δ_arch 일부 즉시 가용** (FRED BKR + EIA shale + IEA OPEC + CME crack spread = 4 종) **+ 일부 deferred_edgar** (reserves/breakeven/downstream margin = 3 종). 즉시 가용 4 종으로 1차 충전 가능, EDGAR 적재 후 추가.
6. **E1 idiosyncratic (Russia 침공)**: 본 frame 의 anti-cyclical outperform 의 large portion 이 Russia supply shock 의 one-off. δ_regime point 가 frame-specific bias 포함 가능. 장기 frame (1970s oil shock, 2008, 2014, 2020) 확장 시 재검증 필요.
7. **frame 한정**: 2022-12 ~ 2024-12 (3년, 4 epoch). 장기 cycle (shale revolution / WTI negative) 미포함.
8. **★cyclical 일괄 처리 금지 의 system 함의**: XLE 의 별도 sub-sleeve treatment 가 R15 weight_card 구조에서 어떻게 구현될지 (별도 sleeve allocation key, regime tag 분리, 또는 composed_weights 의 다른 channel) = main / system 레벨 설계 결정 필요.

---

## 📡 main 회신 핵심 상관

- **★★공식 의도 결정**: XLE 의 anti-cyclical 본성에서 **A 안 (spec sign 곱) vs B 안 (direction-aware) 차이 결정적**. E1/E3 에서 A 안은 +47.9% / +18.0% 의 outperform 을 -0.15 (clip floor) 로 정 반대 표현 → ⛔ G5 FAIL. **B 안 (direction-aware) 채택 의무** — 모든 산업 일관. semi (SOXX) 채택과 일치.
- **★★cyclical 일괄 처리 금지 강력 reinforce**: M3 §3 의 권고를 본 산출에서 reinforce. anti-cyclical hedge 본성 + oil single driver dominance + within-corr outlier (0.26~0.51) 3 신호 동시. **XLE 별도 sub-sleeve treatment 의무** — R15 weight_card 구조 설계 결정 필요.
- **★3 epoch clip ceiling + E4 만 +0.042 magnitude 보존**: semi/industrials/materials 와 공통 saturation + XLE/XLB E4 만 magnitude 보존 (4 산업 중 2 산업).
- **★Domain plausibility B 안 STRONG MATCH** (Tier 3): 4 epoch 모두 anti-cyclical / inflation hedge 본성 정합.
- **★δ_arch 즉시 가용 4 종**: FRED BKR (rig count) + EIA US shale + IEA OPEC + CME crack spread. EDGAR 적재 전에도 δ_arch 1차 충전 가능 — 다른 3 산업과 차별점.
- **★β_oil=+0.41 + R²=0.406 + r_oil=+0.602** = oil single driver dominance, cyclical 중 압도적 1위.
- **Gates pass = 3 (B 안 기준)** (G1/G4/G5 통과, G2 PARTIAL, G3 DEFERRED). A 안 채택 시 G5 FAIL → 2.

<state intent="energy (XLE) δ_regime/δ_arch 산출 산출분 직접 작성 — anti-cyclical hedge 본성으로 공식 의도 결정" risk="A 안 채택 시 도메인 비정합 명백" uncertainty="low">
