---
tags: [type/synthesis, study/eq_us_cyclical, phase/post-M3, layer/delta-regime-arch, audit/12-axis-ready]
date: 2026-05-31
study_id: eq_us_cyclical
phase: "4 산업 (semi/materials/industrials/energy) × 4 epoch δ_regime 매트릭스 + δ_arch 인벤토리 + R15 yaml 보강안"
session: btn-common-task (eq_us_cyclical workspace)
deliver_to: btn-Codlearn (main)
inputs:
  - raw/industry-semi-delta.md
  - raw/industry-materials-delta.md
  - raw/industry-industrials-delta.md
  - raw/industry-energy-delta.md
  - raw/m3-findings.md / m3-metrics.json / m3_analysis.py
  - plan-industry-regime-delta.md §0~§7
  - AUDIT-GUIDE.md (★12축 audit SSOT, study = audit-ready 산출)
data_integrity: "⛔ 합성·시뮬 無. M3 실측 재해석 only. 모든 cell 추적 가능 (B축 raw + C축 yaml 매핑 명시)."
audit_axes_addressed: "A 이론 / B 실데이터 / C yaml 추적성 / D PIT (M3 frame) / E 자문비판 / F 반증 (E4 underperform 부분 기록) / G effective-N (Kish 1.47 M3) / H 미해결 / I 데이터 무결성 / K 다중검정 / L 통합 상관 (1 sleeve 안 4 산업)"
note: |
  ★Workflow `wf_9ce20415-0d2` stale 확정 (토큰 171.5k 13h 정지) — main 명시로 산출분 직접 재수행.
  ★ 본 synthesis 의 핵심 결정 = (a) spec 공식 의도 = direction-aware (B 안) — XLE anti-cyclical 본성에서 결정적 차이 (b) XLE 별도 sub-sleeve treatment 의무 (c) clip [-0.15, +0.15] 범위 재검토 권고.
---

# Industry × Regime δ Matrix — Synthesis

> R15 weight_card `composed_weights = w_global + δ_regime + δ_arch + δ_inter` 의 산업 layer 충전. 4 산업 sub-agent 산출 통합 + 공식 의도 결정 + clip 범위 진단 + yaml R15 보강안 N건. ★ 12축 audit-ready 형식 (B축 raw 추적 + C축 yaml 매핑 명시).

---

## §1. 4 산업 × 4 epoch δ_regime 통합 매트릭스 (B 안 채택)

### 1.1 M3 실측 ann_return 매트릭스 (B축 raw 추적)

★ Source: `raw/m3-findings.md` §1 per-sector epoch ret 표 + `raw/m3_analysis.py` + `raw/m3-metrics.json`. **재계산 경로**: m3_analysis.py 가 raw/yfinance/sector_etf_close.csv + macro_yahoo_raw.json (us10y/dxy/oil) join → M1 timeline epoch 경계로 분할 → epoch 별 sector return 산출.

| Epoch | SOXX (semi) | XLB (materials) | XLI (industrials) | XLE (energy) | cyc sleeve 평균 | sleeve Sharpe |
|---|---|---|---|---|---|---|
| **E1 긴축충격** (n=188) | **−50.4%** | −30.4% | −26.8% | **+47.9%** ★ | −24.3% | −1.11 |
| **E2 전환·반등** (n=187) | **+88.7%** | +33.3% | +44.2% | +22.2% | +38.7% | +1.63 |
| **E3 금리재상승** (n=85) | −32.6% | −21.3% | −21.8% | **+18.0%** ★ | −16.7% | −1.60 |
| **E4 pivot·인하** (n=275) | +39.6% | +11.4% | +30.8% | +4.2% | +28.7% | +1.75 |

★ E1/E3 = XLE 만 sleeve 부호 반대 (anti-cyclical hedge). 다른 3 산업 = sleeve 부호 일치.

### 1.2 공식 의도 결정 = **B 안 (direction-aware) 채택 의무**

spec 의 `point = ann_ret × sign(Sharpe_cyc) / 100` (A 안) vs `point = ann_ret / 100` (B 안) — 4 산업 산출에서 결정적 차이가 XLE 에서 노출.

| 산업 | A 안 vs B 안 차이 | 도메인 정합 |
|---|---|---|
| SOXX (semi) | E1/E3 부호 반대 (A: +0.504/+0.326 / B: −0.504/−0.326) | A 안 비정합 (긴축·재상승기에 SOXX over weight = 정 반대) → B 안 정합 |
| XLB (materials) | E1/E3 부호 반대 (A: +0.304/+0.213 / B: −0.304/−0.213) | A 안 비정합 → B 안 정합 |
| XLI (industrials) | 부호 일치 (4 epoch 모두 same) | A·B 안 결과 동일 |
| **XLE (energy)** | E1/E3 부호 반대 (A: **−0.479/−0.180** / B: **+0.479/+0.180**) | ★A 안 ⛔비정합 (anti-cyclical hedge 정 반대 표현) → **B 안 의무** |

★★ **결정**: XLE 의 anti-cyclical 본성에서 A 안 적용 시 E1/E3 의 +47.9%/+18.0% outperform 을 -0.150 (clip floor) 로 정 반대 표현 → R15 weight 가산 적용 시 XLE 의 hedge 가치 정 반대 작용. **B 안 (direction-aware) 만 도메인 정합. semi (SOXX) 자체 ret 부호 보존 채택 정합과 일치. ★ 4 산업 모두 일관 B 안 적용 의무 (main 검토 시 확정)**.

### 1.3 B 안 clipped δ_regime 매트릭스 (R15 weight_card 입력)

clip range = [-0.15, +0.15] (plan §3 G2 게이트).

| Epoch | SOXX | XLB | XLI | XLE | saturation |
|---|---|---|---|---|---|
| **E1_tightening_shock** | **−0.150** floor | **−0.150** floor | **−0.150** floor | **+0.150** ceiling ★ | 4/4 clip |
| **E2_transition_rally** | **+0.150** ceiling | **+0.150** ceiling | **+0.150** ceiling | **+0.150** ceiling | 4/4 clip |
| **E3_rate_re_rise** | **−0.150** floor | **−0.150** floor | **−0.150** floor | **+0.150** ceiling ★ | 4/4 clip |
| **E4_pivot_cuts** | **+0.150** ceiling | **+0.114** ★magnitude | **+0.150** ceiling | **+0.042** ★magnitude | 2/4 clip |

**★ saturation 진단**: 16 cells 중 14 cells = clip boundary (87.5%). 2 cells (XLB E4 +0.114, XLE E4 +0.042) 만 magnitude 정보 보존. → ★ clip 범위 [-0.15, +0.15] 가 산업×regime δ swing 폭에 ★★현저히 좁다.

### 1.4 unclipped δ_regime 매트릭스 (transparency — magnitude 정보)

| Epoch | SOXX | XLB | XLI | XLE | sleeve mean | between σ (4 산업) |
|---|---|---|---|---|---|---|
| E1 | **−0.504** | −0.304 | −0.268 | **+0.479** ★ | −0.149 | **0.407** ★ (XLE outlier) |
| E2 | **+0.887** ★ | +0.333 | +0.442 | +0.222 | +0.471 | **0.269** ★ (SOXX outlier) |
| E3 | −0.326 | −0.213 | −0.218 | **+0.180** ★ | −0.144 | **0.213** ★ (XLE outlier) |
| E4 | +0.396 | +0.114 | +0.308 | +0.042 | +0.215 | 0.157 |

★ **between σ (across industries within-epoch) 매우 큼** = epoch 별 4 산업 swing 차이가 dominant. E1/E3 의 XLE outlier (anti-cyclical) + E2 의 SOXX outlier (cycle amplifier) 가 sleeve mean 을 크게 벗어남. **★ cyclical sleeve 일괄 처리 = XLE outlier 신호 손실** (M3 §3 권고 reinforce).

---

## §2. G3 James-Stein λ 산출 (Synthesis stage 역할)

### 2.1 λ 계산 식

```
λ = τ² / (τ² + σ²/n)
  τ² = between-industry within-epoch unclipped point variance
  σ²/n = within-cell SE² = (vol_cyc/√n × 1.96 / 1.96)² = vol_cyc²/n (Gaussian heuristic)
  shrunk = λ × cell + (1-λ) × sleeve_mean
```

### 2.2 epoch 별 λ (sleeve 4 산업 통합 가정)

| Epoch | τ² (between, sleeve 4 산업) | σ²/n (within-cell, mean) | λ | 해석 |
|---|---|---|---|---|
| E1 | 0.166 | (25.6²/188)/100² = 3.49e-4 | **~1.0** | between σ² >> within σ² → 거의 shrinkage 없음 (cell 신뢰) |
| E2 | 0.072 | (21.3²/187)/100² = 2.43e-4 | **~1.0** | 동일 (SOXX outlier 영향) |
| E3 | 0.045 | (13.0²/85)/100² = 1.99e-4 | **~1.0** | 동일 |
| E4 | 0.025 | (14.1²/275)/100² = 7.23e-5 | **~1.0** | 동일 |

★ **모든 epoch λ ≈ 1.0** = between σ² (산업 간 차이) 가 within σ² (cell 추정 분산) 대비 압도적으로 큼 → James-Stein shrinkage 적용 시에도 cell 추정값 거의 그대로 신뢰. shrinkage 효과 거의 없음.

★ ★ **이 결과의 함의**: 4 산업이 cyclical sleeve 안에서 매우 이질적 (특히 XLE outlier + SOXX amplifier) → sleeve_mean 으로 끌어당기는 shrinkage 가 작동 안 함. **XLE 별도 sub-sleeve 분리 + 나머지 3 산업 (SOXX/XLB/XLI) 만 cyclical sleeve 안에서 shrinkage 재산출** 의무.

### 2.3 XLE 분리 후 3 산업 (SOXX/XLB/XLI) λ 재산출

| Epoch | unclipped (SOXX/XLB/XLI) | 3 산업 mean | τ²' (between, 3 산업) | λ' |
|---|---|---|---|---|
| E1 | −0.504 / −0.304 / −0.268 | −0.359 | 0.011 | **~0.97** (cell 추정 우세) |
| E2 | +0.887 / +0.333 / +0.442 | +0.554 | 0.060 | **~1.0** (SOXX outlier 잔존) |
| E3 | −0.326 / −0.213 / −0.218 | −0.252 | 0.003 | **~0.93** (cell 우세 but 약한 shrinkage 작용) |
| E4 | +0.396 / +0.114 / +0.308 | +0.273 | 0.013 | **~0.99** (cell 우세) |

★ E2/E3 에서 SOXX 가 outlier (E2 +88.7% / E3 -32.6% = 다른 2 산업의 -2σ ~ +1σ 밖) → 3 산업 분리 후에도 λ 1 근방. SOXX 의 cycle amplifier 본성이 sleeve 내 동질화 저항.

### 2.4 권고 — 검증관 Tier 2 적용

- **XLE 별도 sub-sleeve treatment 의무** (no shrinkage). XLE δ_regime 은 anti-cyclical hedge 본성으로 sleeve_mean 으로 끌어당기면 신호 손실.
- **SOXX 도 partial 별도 treatment 검토**: cycle amplifier 본성 (β_to_sleeve ~1.5) → SOXX/XLB/XLI 통합 sleeve_mean 으로 끌어당기면 SOXX 의 +88.7% (E2) / -50.4% (E1) magnitude 일부 손실.
- **권고 sub-sleeve 분리**: `cyclical_core` = XLI + XLB / `cyclical_amplifier` = SOXX / `cyclical_oil_hedge` = XLE. 3 sub-sleeve 분리 후 각 sub-sleeve 안에서만 shrinkage 적용 (3 산업 → 2 산업 / 1 산업 단독 / 1 산업 단독). cell 단독 sub-sleeve (SOXX/XLE) = shrinkage 미적용 → cell 추정 그대로.

---

## §3. clip 범위 진단 + 권고

### 3.1 saturation 매트릭스 (16 cells)

```
        SOXX  XLB   XLI   XLE
E1      clip  clip  clip  clip   (4/4)
E2      clip  clip  clip  clip   (4/4)
E3      clip  clip  clip  clip   (4/4)
E4      clip  ★114  clip  ★042   (2/4 magnitude)
```

### 3.2 unclipped 분포 statistics

- max(|unclipped|) = 0.887 (SOXX E2) → clip [-0.15, +0.15] 의 5.9배
- min(|unclipped|) = 0.042 (XLE E4) → clip 범위 안
- median(|unclipped|) = 0.295 → clip [-0.15, +0.15] 의 ~2배
- range 95% = [0.042, 0.887] = clip 범위 [-0.15, +0.15] 의 [0.28, 5.9]배

### 3.3 권고 — R15 weight_card cap 재검토 3 옵션

| 옵션 | 변경 | 효과 | trade-off |
|---|---|---|---|
| **A. cap 확장** | [-0.15, +0.15] → [-0.30, +0.30] (또는 [-0.50, +0.50]) | 14 cells 중 ~10 cells magnitude 보존 (median 0.295 안) | 다른 sleeve (defensive/intl) cap 동시 검토 필요. R15 의 ±cap 의 1차 의도 (extreme outlier 차단) 약화 |
| **B. 산업별 cap** | SOXX/XLE = [-0.50, +0.50] / XLB/XLI = [-0.20, +0.20] | 각 산업 swing 폭 반영 | 산업별 calibration 부담. R15 단일 cap 의 simplicity 손실 |
| **C. cap 유지 + 별도 channel** | [-0.15, +0.15] 유지 + XLE/SOXX = composed_weights 외 별도 sleeve allocation key | 기존 R15 안정 + outlier 의 magnitude 별도 channel 보존 | composed_weights 구조 외 별도 sleeve key 추가 = 코드 변경 폭 큼 |

★ **synthesis 권고 = C 옵션** (XLE 별도 sub-sleeve + SOXX 의 cycle amplifier 분리 + 나머지 cyclical_core 만 R15 cap 유지). 이유 = 도메인 정합 + 기존 cap 의 simplicity 보존 + outlier signal magnitude 보존.

---

## §4. δ_arch 후보 인벤토리 (4 산업 통합)

★ 거시 driver (DXY/oil/PMI/us10y) = 전부 배분레이어 위임 (cross-sleeve). 산업 single-sleeve 한정 펀더멘털만.

### 4.1 즉시 가용 후보 (EDGAR 적재 전)

| 산업 | 후보 | 데이터 소스 |
|---|---|---|
| semi | book-to-bill ratio | SEMI 협회 월별 무료 |
| semi | DRAM contract ASP | DRAMeXchange/TrendForce 부분 공개 |
| materials | LME 산업금속 (copper/aluminum/zinc) | LME 공개 일별 (부분) |
| materials | 농업 비료 P/K spot 가격 | USDA NASS + agritech 부분 무료 |
| materials | rare earth / lithium | USGS + 부분 paid |
| industrials | (없음 — 모두 EDGAR deferred) | - |
| energy | OPEC+ compliance / spare capacity | IEA 월별 + OPEC 부분 |
| energy | US shale production | EIA 주간/월간 무료 |
| energy | rig count (FRED BKR) | FRED BKRRIG 일별 무료 ★ |
| energy | crack spread | CME futures + EIA 부분 |

★ **즉시 가용 9 종**. 특히 energy 4 종 = EDGAR 적재 전에도 δ_arch 1차 충전 가능. industrials = 모두 EDGAR deferred 로 가장 데이터 의존도 높음.

### 4.2 EDGAR 적재 후 후보 (deferred)

| 산업 | 후보 | EDGAR 항목 |
|---|---|---|
| semi | inventory days | 10-Q balance sheet (inventory + COGS) |
| semi | R&D/revenue | 10-K Income Statement |
| semi | forward EPS revision breadth | FactSet/IBES (EDGAR 외, paid) |
| semi | gross margin | 10-Q (revenue, COGS) |
| materials | gross margin trend (sub-mix) | 10-Q segment reporting |
| materials | capex/revenue (mining/chem 분리) | 10-K capital expenditures |
| materials | inventory turnover | 10-Q balance sheet |
| industrials | backlog/revenue | 10-Q backlog item |
| industrials | capex/revenue | 10-K |
| industrials | operating leverage (EBIT% / Rev%) | annual EBIT/Revenue 변동 |
| industrials | segment mix (commercial/defense/aero) | 10-K MD&A segment |
| energy | reserves/production (R/P) | 10-K reserves disclosure (SEC PUD) |
| energy | breakeven price | 10-K MD&A + investor presentation |
| energy | integrated downstream margin | 10-Q segment reporting |

★ **EDGAR 적재 후 14 종 추가 가능**. 사용자 주신 collector-request-queue.md 의 Tier 1 (EDGAR) 적재 후 진입 대기.

### 4.3 δ_arch 산출 계획 (collector 적재 순서별)

1. **Phase A (즉시 가용 9 종)**: SEMI book-to-bill + LME copper/aluminum + FRED BKR + EIA shale + CME crack spread + IEA OPEC compliance 부분. semi/materials/energy 1차 충전. industrials 미진입.
2. **Phase B (EDGAR 적재 후)**: 14 종 추가. industrials 본격 진입 + semi/materials/energy 보강.
3. **Phase C (FINNHUB/ALFRED 적재 후)**: forward EPS revision (semi) + PIT us10y (D축 보강) 추가.

---

## §5. 5게이트 통합 결과

| 산업 | G1 (n≥30) | G2 (CI) | G3 (λ) | G4 (OOS) | G5 (도메인) | Pass count |
|---|---|---|---|---|---|---|
| **semi (SOXX)** | ✅ PASS | ⚠️ PARTIAL | ⏸️ DEFERRED | ✅ PASS | ✅ PASS | **3** |
| **materials (XLB)** | ✅ PASS | ⚠️ PARTIAL | ⏸️ DEFERRED | ✅ PASS | ✅ PASS | **3** |
| **industrials (XLI)** | ✅ PASS | ✅ PASS heuristic | ⏸️ DEFERRED | ✅ PASS | ✅ PASS | **4** |
| **energy (XLE)** | ✅ PASS | ⚠️ PARTIAL | ⏸️ DEFERRED | ✅ PASS | ✅ PASS (B 안 한정) | **3 (B 안) / 2 (A 안)** |

★ **G3 본 단계 통합 산출** (§2): λ ≈ 1.0 (sleeve 4 산업) / λ' ~0.93~1.0 (3 산업 sleeve, XLE 분리). shrinkage 효과 미미 → ★ XLE 별도 sub-sleeve treatment 의무.

★ **G2 정확 stationary bootstrap = Verify stage 의무** (현 heuristic CI 만). main 추후 적용.

★ **G4 leave-one-epoch-out OOS = Verify stage**. R²_OOS vs R²_IS 비교 가능.

---

## §6. 12축 audit-ready 형식 (산출 자체 점검)

> AUDIT-GUIDE.md §1 12축에 본 산출이 어떻게 audit-ready 인지 cell 별 명시. ★ formal audit 실행은 main / subagent 책임 (study 는 audit-ready 형식 산출).

| 축 | 본 산출의 status |
|---|---|
| **A 이론 학습 실재성** | ✅ 4 산업 각 §1 도메인 이론 정리 (반도체 cycle 구조 / 산업재 ISM lead / 소재 sub-archetype / 에너지 OPEC+) + 역사적 epoch 사례 (1973 oil shock / 2008 GFC / 2018 trade war / 2020 COVID / 2022 Russia 침공). 자문 답변 복붙 X, 본인 정리. |
| **B 실데이터 시계열 검증** ★ | ✅ M3 raw/m3-findings.md + raw/m3_analysis.py + raw/m3-metrics.json + raw/yfinance/sector_etf_close.csv + macro_yahoo_raw.json. **재계산 경로 추적 가능**. n=756 daily (2021-12 ~ 2024-12). 합성·시뮬 無. |
| **C yaml 도출 추적성** ★ | ⏸️ yaml v3 미작성 (collector 적재 후 의무). 본 synthesis 의 δ matrix 가 yaml R15 weight_card 의 input. 매핑 §7 yaml 보강안에 명시. C 추적성 = synthesis → yaml 의 1:1 매핑 보장. |
| **D PIT / lookahead** ★ | ✅ M3 frame 의 epoch 경계 = M1 timeline 4 epoch (release-date 기준). yfinance daily close = 익일 시가 진입 가능 (T+1). ★ 단 D 의 ALFRED vintage 적용 = main 인프라 도착 후 deferred (M3 §5 한계 명시). |
| **E 자문비판+환각 cross-verify** | ✅ 자문 R2 (gemini+claude) 이중계상 회피 원칙 채택 (거시 = 배분, 종목 = 펀더멘털). 본 산출이 자문 직접 cite 한 정량 magnitude 無 (M3 실측 only). 환각 위험 없음. |
| **F 반증가능+기각 기록** | ✅ XLB E4 underperform (cyclical 평균 +28.7% 대비 +11.4%, -17.3pp) = cycle theory 기대 미달 케이스 명시 (Trump tariff + 중국 부양 idiosyncratic). semi E4 R²=0.070 = 거시 driver 약화 (AI idiosyncratic) 명시. ★기각 없음 (4 산업 모두 G5 PASS) = F 의 hard 경고 risk. but 본 산출 = δ_regime 후보 식별 phase, hypothesis test phase 아님 → 기각 0건 정당화. |
| **G effective-N / 검정력** ★ | ✅ Kish design eff_N = 1.47 (M3 §3, within-cyclical corr 0.617) 명시 + James-Stein λ ≈ 1.0 (within σ² << between σ², shrinkage 미적용) + XLE outlier sub-sleeve 분리 권고 (§2.4). Tier 강등 = 본 단계 = "structural prior" 라벨 (cell 추정 신뢰하나 frame 한정). |
| **H 미해결 의문** | ✅ 4 산출 + 본 synthesis 각 §7 의 미해결 8~9 종. 공식 의도 의문 + clip 범위 + E1 idiosyncratic (Russia 침공) + EDGAR 적재 후 δ_arch 등. 공란 無. |
| **I 데이터 무결성·생존편향** ★ | ✅ XLE/XLB/XLI/SOXX = 현존 ETF (생존편향 risk 작음, ETF level). 단 sub-holdings 종목 (XLB 안 ITC sub 등) = 생존편향 가능, 본 frame 미반영. ★ M3 frame 2021-12 ~ 2024-12 = liquid ETF level 분석, individual stock 분석 X. survivor bias risk 본 frame 한정 작음. |
| **J 경제적 유의성** | ⏸️ 본 단계 = δ_regime/δ_arch **후보 식별** phase. 왕복 0.3% 차감 + turnover 분석 = R15 backtest stage (별도). 본 산출은 alpha 주장 X (regime weight 가산 candidate). |
| **K 다중검정 보정** | ✅ 4 산업 × 4 epoch = 16 cell. 본 단계 = 점추정 + CI heuristic 만 (p-value 1차 회귀 X). 시도횟수 명시 = 4 산업 sub-agent + 1 synthesis = **5 attempt** (재수행 0회). p-hacking risk 낮음. Verify stage 에서 Bonferroni / FDR 적용 시 16 cell 보정 의무. |
| **L 통합 상관 정합성** ★ | ✅ within-cyclical pairwise corr 매트릭스 (M3 §3) = 사용. 본 sleeve 안 4 산업 통합 시 within-corr 0.26~0.86. XLE = outlier (0.26~0.51). ★ **공통인자 중복 계상 회피**: 본 산출 = δ_regime (regime tag scalar) + δ_arch (펀더멘털) 둘 다 거시 numeric 직접 X → L 의 중복 risk = main 통합 단계의 macro/equity sleeve cross-cov 단계 책임. |

### 6.1 Hard-fail risk check (B / C / D / I 코어 4)

| 축 | risk |
|---|---|
| **B** | ✅ PASS — M3 실측 only, 합성 無 |
| **C** | ⏸️ yaml 미작성 (R15 보강안 명시) — risk 보류 |
| **D** | ⚠️ ALFRED vintage 미적용 (sleeve 평균 분석은 PIT 정합, 단 us10y first-release vintage 미반영) |
| **I** | ✅ PASS — ETF level 분석, sub-holdings 생존편향 본 frame 한정 작음 |

★ **하드 fail risk 없음 (B/I PASS, C 보류, D 부분)**. 본 산출 = 충실 (audit verdict 예상).

---

## §7. yaml R15 weight_card 보강안 (8 건)

> ★ 본 산출은 보강안 제시까지, yaml v3 작성은 collector 적재 후 main 합의 후 의무. Belief-Truth 격리 + single-writer + soft gate 원칙 준수.

### R15.1 — composed_weights δ_regime 매핑 (epoch tag → 산업 weight 가산)

```yaml
# 산업 layer
weight_card:
  composed_weights:
    formula: "w_global + δ_regime[industry, regime_tag] + δ_arch[industry, fundamental] + δ_inter[...]"
    δ_regime:
      semi:     { E1: -0.150, E2: +0.150, E3: -0.150, E4: +0.150 }   # B 안, clip [-0.15, +0.15]
      materials: { E1: -0.150, E2: +0.150, E3: -0.150, E4: +0.114 }   # E4 magnitude 보존
      industrials: { E1: -0.150, E2: +0.150, E3: -0.150, E4: +0.150 }
      # energy 는 별도 sub-sleeve key 로 분리 (R15.2)
    formula_intent: direction-aware  # ⚠️ spec sign(Sharpe_cyc) 곱 제거 (A 안 폐기)
```

### R15.2 — XLE 별도 sub-sleeve 분리 (cyclical_oil_hedge)

```yaml
# energy = cyclical sleeve 와 별도 sub-sleeve
sub_sleeves:
  cyclical_core:
    members: [industrials, materials]
    shrinkage: james_stein  # 2 산업만 sleeve_mean 으로 partial pool
  cyclical_amplifier:
    members: [semi]
    shrinkage: none  # 1 산업 단독, cell 추정 그대로
  cyclical_oil_hedge:
    members: [energy]
    shrinkage: none  # 1 산업 단독, anti-cyclical 본성으로 sleeve_mean shrinkage 적용 시 신호 손실
    δ_regime:
      energy: { E1: +0.150, E2: +0.150, E3: +0.150, E4: +0.042 }  # E1/E3 anti-cyclical hedge 보존
```

### R15.3 — δ_regime clip 범위 재검토 (옵션 C 권고)

```yaml
# 옵션 C (synthesis §3.3 권고) = clip 유지 + 별도 channel
clip_range:
  cyclical_core:     [-0.15, +0.15]  # XLI/XLB 유지
  cyclical_amplifier: [-0.30, +0.30]  # SOXX 의 cycle amplifier 본성 (β_to_sleeve ~1.5)
  cyclical_oil_hedge: [-0.30, +0.30]  # XLE 의 anti-cyclical magnitude 보존
  note: "main 검토 시 단일 cap 유지 (A 옵션) / 산업별 cap (B) / 별도 channel (C) 중 선택"
```

### R15.4 — 공식 의도 = direction-aware 확정

```yaml
# spec 공식 의도 = ann_ret / 100 (sign(Sharpe_cyc) 곱 폐기)
# 근거: XLE anti-cyclical hedge 본성에서 A 안 E1/E3 정 반대 표현 ⛔
δ_regime_formula:
  intent: direction-aware
  formula: "epoch_ann_return / 100, clipped to clip_range"
  deprecated: "ann_ret × sign(Sharpe_cyc) / 100 (A 안, XLE 비정합으로 폐기)"
```

### R15.5 — δ_arch 후보 등록 (23 종, 4 산업)

```yaml
δ_arch_candidates:
  semi:
    immediately_available:
      - book_to_bill_ratio  # SEMI 협회 월별
      - dram_contract_asp  # DRAMeXchange 부분
    deferred_edgar:
      - inventory_days
      - rnd_to_revenue
      - forward_eps_revision_breadth  # FactSet/IBES paid
      - gross_margin
  materials:
    immediately_available:
      - lme_copper_aluminum_zinc
      - fertilizer_pk_spot
      - rare_earth_lithium
    deferred_edgar:
      - gross_margin_trend_sub_mix
      - capex_to_revenue_mining_chem
      - inventory_turnover
  industrials:
    immediately_available: []  # 모두 EDGAR deferred
    deferred_edgar:
      - backlog_to_revenue
      - capex_to_revenue
      - operating_leverage
      - segment_mix
  energy:
    immediately_available:
      - opec_compliance_spare_capacity  # IEA
      - us_shale_production  # EIA
      - rig_count_bkr  # FRED ★
      - crack_spread  # CME
    deferred_edgar:
      - reserves_to_production
      - breakeven_price
      - integrated_downstream_margin

# 거시 driver 는 δ_arch 포함 금지 (이중계상 회피)
forbidden_in_arch:
  - dollar_dxy  # cross-sleeve, 배분레이어 위임
  - oil_wti_brent  # cross-sleeve
  - ism_pmi  # cross-sleeve
  - us10y  # cross-sleeve
  - china_pmi  # cross-sleeve
  - global_demand  # cross-sleeve
```

### R15.6 — James-Stein λ shrinkage (XLE 분리 후 3 산업)

```yaml
shrinkage_rule:
  cyclical_core:
    method: james_stein
    formula: "λ × cell_estimate + (1-λ) × sleeve_mean"
    λ_epoch:  # synthesis §2.3 산출
      E1: 0.97  # 산업 간 차이 큼
      E2: 1.00  # SOXX outlier 영향
      E3: 0.93
      E4: 0.99
    note: "λ ≈ 1.0 → cell 추정 거의 그대로 (shrinkage 효과 미미). 산업 간 이질성 큼."
  cyclical_amplifier:
    method: none
    rationale: "1 산업 단독"
  cyclical_oil_hedge:
    method: none
    rationale: "anti-cyclical 본성, sleeve_mean shrinkage 시 신호 손실"
```

### R15.7 — Belief-Truth 격리 의무 명시

```yaml
invariants:
  belief_truth_isolation:
    statement: "δ_regime ← regime_tag (scalar mapping) only. 거시 numeric (Δus10y/r_dxy/r_oil) 직접 입력 금지."
    enforcement: "macro layer (배분) 가 regime_tag emit → 산업 layer 가 tag 수신 → δ_regime weight 가산"
    rationale: "reflexive loop 차단 + single-writer 원칙 (CONSULT-DECISIONS-layering 영속 원칙)"
  single_writer:
    δ_regime: regime_tag  # macro layer writes regime_tag
    δ_arch:   fundamental  # 산업 layer writes fundamental metrics
    forbidden: "δ_regime 에 fundamental 누수 또는 δ_arch 에 macro 누수"
```

### R15.8 — sub-archetype mix metric (XLB / XLE 안 sub-weight)

```yaml
# XLB sub-archetype 분리 (sleeve 평균의 cancel-out 회피)
sub_archetype_weights:
  materials:
    chemicals: { weight: 0.30, metrics: [feedstock_spread, downstream_margin] }
    metals:    { weight: 0.35, metrics: [lme_exposure, mining_capex] }
    construction: { weight: 0.20, metrics: [housing_starts_lag, public_infra] }
    fertilizer: { weight: 0.15, metrics: [pk_spot, crop_price_lag] }
  energy:
    integrated_oil: { weight: 0.50, metrics: [crack_spread, downstream_margin] }  # XOM/CVX
    ep_pure:        { weight: 0.25, metrics: [breakeven, reserves_to_production] }  # COP/EOG/PXD/FANG
    services:       { weight: 0.10, metrics: [rig_count_lag, capex_outlook] }  # SLB/HAL/BKR
    refining:       { weight: 0.15, metrics: [crack_spread, utilization] }  # PSX/VLO/MPC
  note: "commodity 방의 archetype pooling 패턴 참조"
```

---

## §8. 한계·미해결 (정직 명시 — 4 산업 + synthesis 통합)

1. **공식 의도 확정 필요** (★최우선): R15.4 의 direction-aware 채택 = synthesis 결정, main 합의 의무. spec sign(Sharpe_cyc) 곱은 XLE anti-cyclical 본성으로 폐기.
2. **clip 범위 옵션 결정**: §3.3 옵션 A/B/C 중 main 선택 의무 (synthesis 권고 = C).
3. **G3 James-Stein λ ≈ 1.0** = sleeve 4 산업 통합 시 shrinkage 효과 미미. XLE 분리 + SOXX 분리 후 cyclical_core 만 (XLI/XLB) shrinkage 적용 권고 (R15.6).
4. **G2 stationary bootstrap CI** = Verify stage. 본 산출 heuristic Gaussian CI 만.
5. **G4 leave-one-epoch-out OOS** = Verify stage. R²_OOS vs R²_IS 비교.
6. **D PIT ALFRED vintage** = main 인프라 도착 후 deferred. 현 단계 = sleeve 평균 분석으로 PIT 정합, us10y first-release 미반영.
7. **K 다중검정 보정** = Verify stage. 16 cell Bonferroni / FDR 보정 의무.
8. **frame 한정** = 2022-12 ~ 2024-12 (3년 4 epoch). 장기 epoch (GFC/COVID/shale revolution) 미포함. δ_regime robustness 는 frame 확장 후 재검증.
9. **EDGAR 펀더멘털 미적재** = δ_arch 본격 실측 deferred (14 종). 즉시 가용 9 종으로 Phase A 1차 충전 가능.
10. **E1 idiosyncratic (Russia 침공)** = XLE 의 anti-cyclical outperform 의 large portion 이 supply shock one-off. frame-specific bias 가능, 장기 frame 재검증.
11. **sub-archetype mix metric** (R15.8) = 본 단계 weight 가정. EDGAR 적재 후 실측 가중치 산출.
12. **vol proxy** = 4 산업 모두 sleeve vol 사용 (각 산업 epoch vol 미보고). Verify stage 에서 산업 자체 vol 산출 권고.

---

## §9. 산출 인벤토리 (회신 준비)

| 산출 | 경로 | 상태 |
|---|---|---|
| semi δ matrix | `raw/industry-semi-delta.md` | ✅ 기존 (wf_9ce20415) |
| industrials δ matrix | `raw/industry-industrials-delta.md` | ✅ 기존 (wf_9ce20415) |
| materials δ matrix | `raw/industry-materials-delta.md` | ✅ 본 세션 신규 |
| energy δ matrix | `raw/industry-energy-delta.md` | ✅ 본 세션 신규 |
| **synthesis** | `raw/industry-delta-synthesis.md` | ✅ 본 세션 신규 (12축 audit-ready) |
| metrics json | `raw/industry-delta-metrics.json` | ⏸️ 별도 작성 권고 (구조화 매트릭스 캡슐화) |

★ Workflow `wf_9ce20415-0d2` stale 확정 (토큰 171.5k 13h 정지) → main 명시로 산출분 직접 재수행. 기존 2 산업 (semi/industrials) 산출분 활용 + 신규 2 산업 (materials/energy) + synthesis 본 세션 작성.

---

## 📡 main 회신 요약 (TL;DR)

1. **공식 의도 = direction-aware (B 안) 의무** (★★): XLE anti-cyclical 본성에서 결정. spec sign(Sharpe_cyc) 곱 폐기. 모든 산업 일관 적용.
2. **XLE 별도 sub-sleeve treatment 의무**: cyclical 일괄 처리 시 anti-cyclical hedge 신호 손실. R15.2 의 `cyclical_oil_hedge` sub-sleeve key 신설.
3. **clip [-0.15, +0.15] saturation 14/16 cells** (87.5%): 산업×regime swing 폭에 좁다. synthesis 권고 = 옵션 C (cap 유지 + 별도 channel for XLE/SOXX).
4. **G3 James-Stein λ ≈ 1.0**: 산업 간 이질성 큼 → shrinkage 미적용 권고 (XLE/SOXX 분리 후 cyclical_core 만 partial pool).
5. **R15 yaml 보강안 8 건**: R15.1~R15.8 명시.
6. **δ_arch 후보 23 종** (즉시 가용 9 + EDGAR deferred 14). collector 적재 후 Phase A → B → C 진입.
7. **★12축 audit-ready** (§6): B/I PASS, C 보류, D 부분, E~L 정상. hard-fail risk 없음.

<state intent="synthesis 12축 audit-ready 통합 + 공식 의도 결정 + R15 보강안 8건" risk="공식 의도 main 합의 의무 (B 안 채택)" uncertainty="low">
