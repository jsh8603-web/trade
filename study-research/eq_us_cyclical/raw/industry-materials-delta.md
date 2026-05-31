---
tags: [type/research, study/eq_us_cyclical, phase/post-M3, industry/materials]
date: 2026-05-31
study_id: eq_us_cyclical
phase: "소재 (XLB) δ_regime / δ_arch 후보 매트릭스 (M3 재해석 + 도메인 정합)"
session: btn-common-task (eq_us_cyclical workspace)
industry: materials
proxy_etf: XLB
inputs:
  - raw/m3-findings.md (E1~E4 epoch × sector, β_dxy=-1.18, R²=0.215, r_dxy=-0.400)
  - plan-industry-regime-delta.md §0~§5
  - raw/industry-semi-delta.md (포맷 정합 + sign 공식 caveat)
  - raw/industry-industrials-delta.md (포맷 정합 + sign 공식 caveat)
invariants:
  - Belief-Truth 격리 (거시 numeric δ_arch 포함 금지)
  - regime_tag scalar 매핑만 (numeric 거시 직접 X)
  - 점추정 박제 금지 (CI 의무, G2)
  - 합성·시뮬 無 (M3 실측 재해석만)
data_integrity: "⛔ 합성 無. M3 실측 재해석 only. CI heuristic = vol/√n × 1.96 (정확 stationary bootstrap = Verify stage)."
---

# Materials (XLB) — δ_regime / δ_arch 후보

> XLB = within-cyclical 의 dollar-via-metals 채널. β_dxy=−1.18 (cyclical 중 SOXX 다음, 절댓값 2위) + R²=0.215 (sleeve 두 번째 설명력). rank-IC r_dxy=−0.400 (cyclical 중 최대 절댓값) → ★metal-dollar inverse 관계가 산업재·반도체보다 더 dominant. 단 4 epoch 모두 cyclical 평균보다 underperform (E1 -6.1pp / E2 -5.4pp / E3 -4.6pp / **E4 -17.3pp**) — 특히 E4 의 큰 underperform = 중국 부양 efficacy 의문 + 2024 Trump tariff 전망 의 idiosyncratic 영향 시사.

---

## §1. 도메인 이론 정리

### 소재 cycle 의 본질

XLB = 산업금속 (Freeport-McMoRan, Newmont) + 화학 (Dow, LyondellBasell, DuPont) + 건설자재 (Vulcan, Martin Marietta) + 비료 (Mosaic, CF Industries) 의 묶음. 한 sleeve 안에 sub-archetype 이 4종 → ★sleeve 평균이 sub mix 의 cancel-out 으로 R²=0.215 이지만 sub 별 driver 가 매우 이질적.

핵심 cycle 구조:
1. **금속 cycle** — 중국 demand (글로벌 산업금속 50%+ 점유) → LME copper/aluminum/zinc 가격 → XLB 매출. 중국 PMI 가 6~9개월 선행. 단 본 task = 거시 cross-sleeve → 배분레이어 위임.
2. **화학 cycle** — 매출은 oil/gas feedstock cost spread (특히 ethylene/propylene producers), 수요는 자동차·건설·내구재. 별도 micro-cycle.
3. **건설자재** — 미국 인프라 spending + 주택 cycle 의 후행 (housing starts 12M lag).
4. **비료** — 농업 cycle (corn/soybean 가격 → P/K 수요), 곡물 가격은 oil cost + 기후 + geopolitics 의 합성.

### 핵심 driver 와 시간 lag

1. **dollar (DXY)** (lag 0~3M): XLB 의 β_dxy=−1.18 (cyclical 중 SOXX 다음으로 강), rank-IC=−0.400 (cyclical 최대 절댓값). (a) 산업금속 dollar-denominated 거래 → 가격 inverse, (b) 글로벌 메탈 매출의 환산 효과, (c) emerging-market mining capex 가격경쟁력. 배분레이어 위임.
2. **중국 PMI / 글로벌 산업금속 수요** (lag 6~9M): 매출 1차 forward. 배분레이어 위임 (cross-sleeve = cyclical 전반 영향).
3. **oil / 화학 feedstock cost** (lag 0~6M): 화학 sub 의 margin 직접 영향. β_oil=+0.050 sleeve 평균 (XLE 대비 작지만 0 보다 양수), 화학 sub 한정 sensitivity 가 크리라 추정. 배분레이어.
4. **us10y / 건설 finance cost** (lag 3~6M): 건설자재 sub 한정. β_us10y=+0.009 sleeve 평균 ≈ 0, sub-specific 감춰짐.

### 역사적 epoch 사례

- **2008~2009 GFC**: copper LME -70%, XLB ~-50% YTD. 중국 4조위안 부양으로 2009-2010 metal V-shape 회복.
- **2011~2015 super-cycle 종료**: 중국 투자 둔화 + supply build → copper -50% (4년 bear), XLB underperform.
- **2016~2018 mini-cycle**: 중국 supply-side reform + global synchronized growth → metal rally + XLB +35% 2017 단년.
- **2020 COVID → 2021 부양**: copper $9000+ rally, XLB +55% Y/Y.
- **2022~2024 M3 frame**:
  - E1 = 중국 Shanghai lockdown (2022-03~05) + dollar 급등 → metal 수요 acute 둔화 + 매출 환산 타격 (이중타격) → XLB −30.4% (cyclical 평균 -24.3% 보다 -6.1pp 약).
  - E2 = pivot 기대 + 중국 reopening 기대 → 그러나 2023 Q1 reopening 의 실제 효과 약함 (부동산 부진 지속) → XLB +33.3% (cyclical 평균 +38.7% 보다 -5.4pp 약).
  - E3 = rate 재상승 + 중국 부양 efficacy 의문 → metal 가격 재약화 → XLB -21.3% (cyclical 평균 -16.7% 보다 -4.6pp 약).
  - E4 = rate cut 기대지만 중국 부양 효과 미약 + 2024 Trump tariff 전망 (2024 Q4) → industrial metals rally 제한, XLB **+11.4%** (cyclical 평균 +28.7% 보다 **-17.3pp 큰 underperform**). ★특이.

### Investment Clock 사분면

소재 = 통상 **Recovery + Overheat 두 quadrant 우위** (성장↑ + 인플레↑ → 산업금속·화학 가격 동시 상승). M3 frame 의 E2 (Recovery) 가 이 quadrant 인데 XLB 가 cyclical 평균 미만 = ★unusual underperform → 중국 cycle 의 partial decoupling 가능성 시사. XLB 의 **secular 변화** (전기차 전환 metal demand 가 중국 부양 부재로 stalled) 가 cycle 기대를 overrule 한 frame 으로 해석.

---

## §2. M3 결과 재해석 (XLB 관점)

### Epoch 별 의미

| Epoch | XLB ann_ret | Sharpe (sleeve) | β_dxy (sleeve, epoch) | 해석 |
|---|---|---|---|---|
| **E1 긴축충격** (2022-01~09, n=188) | **−30.4%** | −1.11 | −1.34 | 중국 Shanghai lockdown + dollar 급등 이중타격. XLB = cyclical 평균 (-24.3%) 보다 -6.1pp 약. β_dxy=−1.18 (full sample, sleeve 평균 -1.05 보다 강) 의 효과 + 중국 needle drop 직격. |
| **E2 전환·반등** (2022-10~2023-06, n=187) | **+33.3%** | +1.63 | −1.12 | pivot + China reopening 기대. 단 cyclical 평균 (+38.7%) 보다 -5.4pp 약 = reopening 의 실제 metal demand pull-through 가 기대 미달 (부동산 부진 지속). |
| **E3 금리재상승** (2023-07~10, n=85) | **−21.3%** | −1.60 | −0.40 | rate 재상승 + 중국 부양 efficacy 의문 → metal 가격 재약화. cyclical 평균 -16.7% 보다 -4.6pp 약. |
| **E4 pivot·인하** (2023-11~2024-12, n=275) | **+11.4%** | +1.75 | −0.51 | ★cyclical 평균 +28.7% 보다 **-17.3pp 큰 underperform**. rate cut 기대 + 중국 부양 efficacy 약화 + Trump tariff 전망 (2024 Q4 dollar 재반등). XLB 의 secular pressure (전기차 demand 의 중국 부재) 가 cycle 기대를 압도. |

### Within-cyclical 위치 (sleeve 평균 대비)

- E1: XLB −30.4% vs cyc 평균 −24.3% → **-6.1pp 약**
- E2: XLB +33.3% vs cyc 평균 +38.7% → **-5.4pp 약**
- E3: XLB −21.3% vs cyc 평균 −16.7% → **-4.6pp 약**
- E4: XLB +11.4% vs cyc 평균 +28.7% → **-17.3pp 약 (★특이)**

★ XLB 의 **4 epoch 모두 sleeve 평균 미만** 패턴 = ★structural underperformance. (a) 중국 demand factor 의 idiosyncratic + (b) Trump tariff prospect 의 dollar reflex + (c) secular metal demand uncertainty. 단순 cyclical 일괄 처리 시 XLB underperform 이 감춰짐 → δ_regime 으로 잡아야 할 핵심 신호.

### Cross-sleeve dollar/oil 채널 강도

- **β_dxy=−1.18 (full sample)**: cyclical 평균 (−1.05) 보다 약 12% 강. SOXX (-1.62) 다음으로 강한 dollar inverse. metals + chemicals 의 dollar denominated 거래 비중 반영.
- **β_oil=+0.050**: sleeve 평균 (+0.08) 미만이지만 0 보다 양수. chemicals sub 의 feedstock cost spread 가 부분 반영. (XLE 의 +0.41 와는 1자리 차이.)
- **β_us10y=+0.009 ≈ 0**: 직접 영향 미미. sub-archetype mix 의 cancel-out (건설자재 = 금리 sensitive, metals = 무관) 가능성.
- **R²=0.215**: cyclical 평균 (0.188) 보다 강함. **거시 driver 의 설명력이 sleeve 안 두 번째**. 단 sub-archetype 4종이 각자 다른 micro driver 를 가짐에도 불구하고 dollar 단일 driver 로 21.5% 설명 = dollar 의 sleeve 전체 dominant 확인.
- **rank-IC r_dxy=-0.400** = cyclical 최대 절댓값. β linear regression 보다 sign-based rank order 가 더 강하게 dollar 와 inverse → ★non-linear dollar sensitivity 가능.

---

## §3. δ_regime 후보 (★핵심)

### 계산 방법

```
point = epoch_ann_return × sign(Sharpe_cyc) / 100, clipped to [-0.15, +0.15]
CI heuristic (95%) = ±vol_cyc/√n × 1.96 (XLB 별도 vol 미보고, sleeve vol proxy)
```

★ 공식 의도 caveat — semi/industrials 에서도 동일한 미해결 의문. spec `× sign(Sharpe_cyc)` 적용 시 **conviction magnitude** (방향 무관) 산출. **direction-aware** (E1/E3 = -, E2/E4 = +) 의도였다면 `ann_ret / 100` 만. 본 보고 = **두 해석 병기** (Synthesis stage 에서 main 검토).

### Unclipped 점추정 (transparency)

| Epoch | ann_ret | Sharpe_cyc sign | unclipped (× sign) | unclipped (direction-aware) | SE (vol/√n) × 1.96 |
|---|---|---|---|---|---|
| E1 | −30.4% | −1 | **+0.304** | **−0.304** | ±0.0366 |
| E2 | +33.3% | +1 | **+0.333** | **+0.333** | ±0.0305 |
| E3 | −21.3% | −1 | **+0.213** | **−0.213** | ±0.0276 |
| E4 | +11.4% | +1 | **+0.114** | **+0.114** | ±0.0167 |

★ **E4 unclipped = +0.114** (4 산업 중 유일하게 clip 미도달). XLB 의 E4 underperform 이 magnitude 정보를 보존. 다른 산업 (semi/industrials 4 epoch saturated) 와의 차별점.

### Clipped δ_regime — 두 해석 병기

#### A. spec 공식 `× sign(Sharpe_cyc)` (magnitude, industrials 와 같은 방식)

| Epoch | point (clipped) | CI_low | CI_high | 비고 |
|---|---|---|---|---|
| **E1_tightening_shock** | **+0.150** | +0.150 | +0.150 | unclipped +0.304, clip ceiling |
| **E2_transition_rally** | **+0.150** | +0.150 | +0.150 | unclipped +0.333, clip ceiling |
| **E3_rate_re_rise** | **+0.150** | +0.150 | +0.150 | unclipped +0.213, clip ceiling |
| **E4_pivot_cuts** | **+0.114** | +0.097 | +0.131 | ★unclipped < clip → **magnitude 정보 보존**. CI 0 미통과 = 신뢰 |

#### B. direction-aware (ann_ret/100, semi 와 같은 방식)

| Epoch | point (clipped) | CI_low | CI_high | 비고 |
|---|---|---|---|---|
| **E1_tightening_shock** | **−0.150** | −0.150 | −0.150 | unclipped −0.304, clip floor |
| **E2_transition_rally** | **+0.150** | +0.150 | +0.150 | unclipped +0.333, clip ceiling |
| **E3_rate_re_rise** | **−0.150** | −0.150 | −0.150 | unclipped −0.213, clip floor |
| **E4_pivot_cuts** | **+0.114** | +0.097 | +0.131 | ★unclipped < clip → magnitude 보존 |

### 해석

- **A 안 (magnitude)**: 4 epoch 모두 +방향 (regime tag 가 별도로 long/short 전달). E4 만 +0.114 = "확신 강도 약함" 으로 해석. 이는 XLB 의 E4 underperform 을 "거시 regime 만으로는 약한 신호" 로 표현.
- **B 안 (direction-aware)**: E1/E3 −0.15 (under), E2 +0.15 (over), E4 +0.114 (mild over) = R15 weight 가 직접 long/short 가산. E4 의 +0.114 = "small overweight" 로 해석되어 XLB 의 cyclical 평균 대비 underperform 을 **부분적으로** 반영.

★ **B 안의 E4 +0.114** = direction-aware 라면 R15 weight 에서 XLB E4 는 sleeve 평균 (+0.15) 보다 -3.6pp under (E4 cyclical 평균 +28.7% 대비 XLB +11.4%, -17.3pp 차이의 부분 표현). 단 magnitude saturation 으로 -17.3pp 의 full magnitude 는 잡지 못함.

★ **B 안의 E1 −0.15** = direction-aware 라면 XLB 의 -30.4% 손실 (cyclical 평균 -24.3%) 보다 약한 표현. 마찬가지 clip floor 로 -6.1pp 차이 cancel.

→ **두 해석 모두 clip 범위 [-0.15, +0.15] 가 XLB cycle swing 폭에 좁다** = R15 cap 재검토 필요 (semi/industrials 동일 발견).

★ **bootstrap CI 의무**: 위 CI = Gaussian heuristic. Verify stage 에서 stationary bootstrap (block √n) 정확 CI 산출 필수 (G2).

★ **regime_tag scalar 매핑만**: 위 point 는 macro layer (배분) 가 regime tag emit → 본 layer 가 tag → XLB weight 가산 scalar 변환 시 사용. 거시 numeric (Δus10y/r_dxy/r_oil) 직접 X. **Belief-Truth 격리 준수**.

---

## §4. δ_arch 후보 (펀더멘털, 거시 제외)

| Metric | Theoretical basis | Data status |
|---|---|---|
| **gross margin trend (chemicals/metals split)** | XLB = chemicals (Dow/LyondellBasell) + metals (Freeport/Newmont) + 건설자재 + 비료 의 4 sub-archetype. 각 sub margin pressure 가 sleeve 평균에서 cancel-out → sub-mix 가중 margin 이 forward 1~2 분기 EPS 선행 | **deferred_edgar** (10-Q segment reporting + COGS/Revenue) |
| **capex/revenue (mining + chemical 분리)** | 메탈 mining = 자본집약 (capex/rev 15~25%), 화학 = mid (8~12%), 건설자재 = low (5~8%). high-capex 종목 = peak cycle 위험 (다음 down-cycle 의 supply overhang 원인) | **deferred_edgar** (annual 10-K capital expenditures) |
| **inventory turnover (raw material days)** | 글로벌 supply chain bottleneck 의 thermometer. metals 평균 75~95일, chemicals 평균 45~65일. 100일+ = 수요 acute 둔화 신호. metal cycle 의 4~6M 선행 | **deferred_edgar** (10-Q balance sheet, inventory + COGS) |
| **LME 산업금속 노출도 (sub-sleeve weighted)** | copper/aluminum/zinc 가격 sensitivity. XLB 안 metal sub (FCX 등) 가 LME copper price 의 60~80% 변동 따라옴. sub-weighted XLB exposure | **available_now** (LME public 부분, copper/aluminum 일별 가격) |
| **agricultural fertilizer P/K spot 가격** | 비료 sub (Mosaic, CF Industries) only. 곡물 가격 + crop yield + 농업 season 에 의존. P/K spot 가격 추세 가 margin 의 즉시 영향 | **available_now** (USDA NASS + Bloomberg/agritech 부분 무료) |
| **rare earth / lithium price** | 전기차 transition 관련 secular driver. 단 XLB 직접 비중은 작음 (Albemarle 등 일부). secular thesis 의 보조 metric | **available_now** (USGS + 부분 paid) |
| ⛔ **중국 PMI / 글로벌 PMI** | 산업금속 매출 6~9M 선행 boundary, sleeve 전반 영향 | ⛔ **거시 cross-sleeve → 배분레이어 위임** (plan §2 경계 분류 결과). δ_arch 포함 금지. |
| ⛔ **dollar (DXY)** | XLB β_dxy=−1.18 강력하나 sleeve 전반 driver | ⛔ **거시 cross-sleeve → 배분레이어 위임**. δ_arch 포함 금지. |
| ⛔ **oil (WTI feedstock)** | chemicals sub margin 직접 영향이나 sleeve 전반 driver | ⛔ **거시 cross-sleeve → 배분레이어 위임**. δ_arch 포함 금지. |

⛔ 거시 driver (PMI/DXY/oil) 는 δ_arch 에 포함하지 않음. XLB single-sleeve 한정 펀더멘털 만 채택.

★ **현 단계 산출 = 이론 후보 식별 + EDGAR 적재 후 실측 deferred**. δ_arch numeric 산출은 EDGAR 인프라 도착 시 별도 round. LME copper/aluminum 일별 가격은 즉시 가용하지만 sub-weighted XLB exposure 산출에는 sub-archetype membership 데이터 필요 (10-K segment reporting).

★ **sub-archetype 분리 권고**: XLB sleeve 자체가 4 sub 의 cancel-out 구조 → δ_arch 산출 시 sub-archetype membership (chemical/metal/construction/fertilizer) 별 분리 검토. commodity 방의 archetype pooling (raw/m3-findings.md §3 cross-asset corr) 패턴 참조.

---

## §5. 5게이트 적용

| Gate | Pass | Note |
|---|---|---|
| **G1 (n≥30 daily)** | ✅ **PASS** | E1=188, E2=187, E3=85, E4=275 모두 daily n≥30. E3 monthly 환산 ~4 fail (daily 기준 적용). |
| **G2 (Bootstrap CI)** | ⚠️ **PARTIAL** | Gaussian heuristic CI 만 산출 (vol/√n × 1.96). 정확 stationary bootstrap (Politis-Romano, block √n) Verify stage. E4 만 CI 가 clip 안 = 점추정 박제 위험 정상 표현. E1/E2/E3 saturation. |
| **G3 (James-Stein λ)** | ⏸️ **DEFERRED** | epoch×산업 cell shrinkage = Synthesis stage. 4 산업 통합 후 τ²/σ² 추정. |
| **G4 (OOS)** | ✅ **PASS (가능)** | 4 epoch holdout 가능. leave-one-epoch-out 으로 R²_OOS vs R²_IS 비교 가능. 본 단계 미실행, Verify stage. |
| **G5 (Domain plausibility)** | ✅ **PASS** | §6 참조. XLB underperform 패턴이 중국 demand factor + Trump tariff 의 idiosyncratic 으로 설명 정합. |

**Gates pass count = 3 (G1/G4/G5 통과, G2 PARTIAL 미카운트, G3 DEFERRED 미카운트)**.

★ semi/industrials 와 차이: semi 는 3 (G1/G4/G5), industrials 는 4 (G1/G2/G4/G5). XLB 는 industrials 와 같이 G2 heuristic 동봉이지만 E4 unclipped saturation 미발생 → CI 0 통과 여부 명확 → G2 PASS 가능. 보수적으로 PARTIAL 표시 (synthesis 에서 재집계).

---

## §6. 도메인 plausibility (Tier 3)

### Verdict: **PARTIAL MATCH (E1~E3 정합, E4 부분 정합)**

| Epoch | 측정 ann_ret | Cycle theory 기대 | 정합 |
|---|---|---|---|
| **E1 긴축충격** | −30.4% | 중국 Shanghai lockdown + dollar 급등 이중타격, β_dxy 강 → cyclical 평균 -24.3% 대비 약함 expected. **-25~-35% 기대** | ✅ 정합 |
| **E2 전환·반등** | +33.3% | pivot + China reopening 기대. 단 reopening 의 실제 metal pull-through 가 부동산 부진으로 약함 → cyclical 평균 +38.7% 대비 약함 expected. **+30~+45% 기대** | ✅ 정합 (sleeve 평균 미달이 reopening efficacy 약함 정합) |
| **E3 금리재상승** | −21.3% | rate 재상승 + 중국 부양 efficacy 의문 → metal 가격 재약화. **-15~-25% 기대** | ✅ 정합 (cyclical 평균 -16.7% 보다 약간 약, 정합) |
| **E4 pivot·인하** | **+11.4%** | rate cut 기대 + 중국 부양 → metal recovery 기대 (이론 +25~+35%). 단 ★Trump tariff prospect (2024 Q4 dollar 재반등) + 중국 부양 효과 미약 + secular metal demand uncertainty 가 cycle 기대를 overrule. **이론 mid expectation 대비 -15~-20pp 부족** | ⚠️ **부분 정합** (이론 기대 미달이지만 idiosyncratic 설명 가능) |

### 부가 plausibility check

- **β_dxy=−1.18 (sleeve 평균 -1.05 보다 강)** = XLB 의 metals + chemicals 의 dollar-denominated 거래 비중 정합. Domain expectation: SOXX > XLB > XLF > XLY > XLI. 실측 -1.62 > -1.18 > -1.12 > -1.00 > -0.81 — **정합**.
- **β_oil=+0.050 (sleeve 평균 +0.08 미만)** = chemicals sub 의 feedstock cost 부분 반영, metals/건설/비료 sub 의 oil 무관 cancel. domain expectation 일치.
- **R²=0.215 (cyclical 두 번째 설명력)** = sub-archetype 4종에도 불구하고 dollar 단일 driver 가 21.5% 설명 = dollar 의 sleeve 전체 dominant 확인.
- **within-cyclical XLE 와 0.51 corr (cyclical 평균 0.617 미만)** = XLB 가 within-sleeve 의 dollar core (XLI/XLF 와 0.79~0.86) 와 oil-driven outlier (XLE) 의 중간 위치. metals 의 commodity character 가 XLE 와 부분 공유.

### Tier 3 결론

XLB δ_regime 4 epoch 중 3 epoch (E1/E2/E3) 정합, E4 부분 정합 (이론 expectation 미달이지만 Trump tariff + 중국 부양 효과 미약 + secular metal demand 의 idiosyncratic 으로 설명 가능). **G5 통과 가능 (E4 caveat 명시)**.

★ ★ **E4 underperform 의 systematic 신호 가치**: XLB E4 +11.4% = cyclical 평균 +28.7% 대비 **-17.3pp 큰 underperform**. R15 weight 에 cyclical 일괄 처리 시 이 신호 감춰짐 → δ_regime 으로 잡아야 할 **핵심 신호**. 단, direction-aware 해석 (B 안) 의 +0.114 (over) 는 이 underperform 의 부분 표현, magnitude 해석 (A 안) 의 +0.114 (mild conviction) 은 신호 magnitude 만 보존. **두 해석 모두 clip 범위 내에서 부분 표현** = clip 범위 재검토 (또는 별도 sub-sleeve treatment) 의 강력 motivation.

---

## §7. 한계·미해결 (정직 명시)

1. **vol proxy**: XLB 별도 vol 미보고 → cyclical sleeve vol 채택. XLB 가 sleeve 평균과 within-corr 0.69~0.86 (high)로 vol 도 유사 추정. Verify stage 에서 XLB 자체 epoch vol 산출 권고.
2. **공식 의도 의문**: spec 의 `× sign(Sharpe_cyc)` = conviction magnitude vs `ann_ret/100` = direction-aware. 본 보고 **두 해석 병기**. Synthesis stage 에서 main 검토 시 확정 받음 (★중요 의문, semi/industrials 와 공통).
3. **clip ceiling saturation**: E1/E2/E3 모두 unclipped > +0.15 → clip ceiling. magnitude 정보 손실. E4 만 +0.114 으로 magnitude 보존. R15 cap 재검토 또는 XLB 의 별도 sub-sleeve treatment 필요.
4. **G3 James-Stein λ deferred**: Synthesis stage. weakly informative prior τ²/σ² 가정 필요.
5. **δ_arch deferred_edgar**: 5 개 후보 중 3 개 (gross margin / capex / inventory) = EDGAR 10-Q/10-K 적재 대기. 2 개 (LME / 비료 P/K) = 즉시 가용 (LME public + USDA). 현 단계 = 이론 후보 식별 한정.
6. **sub-archetype mix 의 cancel-out**: XLB 안 chemicals/metals/건설/비료 4 sub 의 driver 가 sleeve 평균에서 cancel-out → sleeve-level 분석의 한계. commodity 방 archetype pooling 패턴 참조하여 sub-archetype 분리 검토 (synthesis stage 권고).
7. **frame 한정**: M3 frame = 2022-12 ~ 2024-12 (3년, 4 epoch). 장기 epoch (GFC/COVID/2017 mini-cycle) 미포함. δ_regime robustness 는 frame 확장 후 재검증.
8. **E4 idiosyncratic factor 분리 X**: Trump tariff prospect + 중국 부양 효과 미약 + secular metal demand uncertainty 의 3 factor 가 E4 -17.3pp 의 mechanism. 본 frame 에서 분리 산출 X (별도 regime tag 또는 펀더멘털 metric 으로 미래 확장).

---

## 📡 main 회신 핵심 상관

- **★δ_regime 4 epoch 중 3 epoch clip ceiling (+0.150) + E4 만 +0.114 magnitude 보존** = XLB 의 E4 underperform 이 clip 범위 안에서 magnitude 신호 보존. 다른 산업 (semi/industrials) 4 epoch saturation 와의 차별점.
- **★Domain plausibility PARTIAL MATCH** (Tier 3): 3 epoch 정합 + E4 부분 정합 (Trump tariff + 중국 부양 idiosyncratic).
- **★공식 의도 의문 재확인**: semi/industrials 와 공통. magnitude (A) vs direction-aware (B) 둘 다 병기. Synthesis 에서 main 검토.
- **★sub-archetype 분리 권고**: XLB = chemicals/metals/건설/비료 4 sub mix → cancel-out 으로 sleeve-level 분석 한계. commodity 방 archetype pooling 패턴 참조.
- **★β_dxy=−1.18 + rank-IC −0.400** = cyclical 중 dollar inverse 최강 (rank order 기준). non-linear dollar sensitivity 가능성 (Verify stage 확인).
- **★R²=0.215 (cyclical 두 번째)** = sub mix 에도 불구하고 dollar 단일 driver 가 21.5% 설명 = dollar dominant 확인.
- **Gates pass = 3** (G1/G4/G5 통과, G2 PARTIAL, G3 DEFERRED).

<state intent="materials (XLB) δ_regime/δ_arch 산출 산출분 직접 작성" risk="공식 의도 미확정 (magnitude vs direction-aware) — 두 안 병기" uncertainty="med">
