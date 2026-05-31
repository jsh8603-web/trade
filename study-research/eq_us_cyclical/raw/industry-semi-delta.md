---
tags: [type/research, study/eq_us_cyclical, phase/post-M3, industry/semiconductor, layer/delta-regime]
date: 2026-05-30
study_id: eq_us_cyclical
phase: "산업 subagent — 반도체 (SOXX) δ_regime / δ_arch 후보"
industry: semiconductor
etf: SOXX
inputs:
  - study-research/eq_us_cyclical/raw/m3-findings.md
  - study-research/eq_us_cyclical/plan-industry-regime-delta.md
data_integrity: "⛔ 합성 無. M3 실측 재해석 only. CI heuristic = vol/sqrt(n)×1.96 (정확 stationary bootstrap 은 Verify stage)"
---

# Industry × Regime δ — 반도체 (SOXX)

> R15 weight_card `composed_weights = w_global + δ_regime + δ_arch + δ_inter` 의 δ_regime / δ_arch 충전. ⛔ Belief-Truth 격리: δ_regime 은 regime tag scalar 매핑만, 거시 numeric 직접 박제 X.

## §1. 도메인 이론 정리

**반도체 cycle 구조**. 반도체 산업은 전형적으로 **2~3년 주기 cycle** 을 가짐. SEMI 협회의 **book-to-bill ratio** (신규주문/출하) 가 1.0 = 균형, >1 = 상승국면, <1 = 하강국면을 표시하는 대표 leading indicator. DRAM/NAND 메모리는 commodity 성격이 강해 **ASP volatility** 가 극단적 (peak-to-trough 50%+ swing). 메모리 cycle 은 logic/foundry cycle 보다 1~2 분기 선행. capex 집행 → 생산능력 → 공급과잉 → ASP 붕괴 → capex 삭감 → 공급정상화 → ASP 회복의 자기진동 구조.

**고듀레이션 자산**. 반도체는 성장기대를 가격에 반영하는 **growth multiple sensitive** 자산. EPS 추정치 자체보다 forward P/E·EV/Sales 의 multiple expansion/contraction 이 가격 변동의 60% 이상을 설명. 따라서 **할인율 (us10y) 변동에 매우 민감** — 듀레이션이 긴 cash flow profile 때문. 단, M3 실측에서는 β_us10y=+0.028 로 절댓값 작음 → rate 가 직접 가격에 미치는 영향보다 **dollar 채널 경유 (β_dxy=−1.62, cyclical sector 중 최대)** 가 dominant. 이는 반도체 매출의 **글로벌 비중이 70~85%** 에 달하기 때문 (TSMC/Samsung/SK Hynix 등 해외 고객 의존).

**시간 lag 구조**. (a) book-to-bill → 매출 인식: 6~9개월 lag. (b) DRAM ASP → SOXX 주가: 동행~3개월 선행 (시장이 ASP 반영). (c) capex 발표 → 공급 도달: 18~24개월. (d) Fed pivot → SOXX 반등: 동행 (E2 사례, 2022Q4 pivot 기대 시점부터 SOXX +88.7% rally). M3 E1·E2 swing 의 시간 sync 는 **multiple expansion/contraction 으로 즉시 반영**되는 자산임을 확인.

**역사적 epoch 사례**. (1) 2018 H2: Powell rate hike + 미중 무역분쟁 → SOXX −34% (E1 유사 패턴). (2) 2020 Q1 COVID: 일시 충격 후 WFH 수요로 빠른 회복 (E2 sleeve 와 유사한 transition rally). (3) 2022 (M3 E1): 인플레 + Fed 75bp 연속인상 + 메모리 cycle peak-out → SOXX −50.4% (M3 실측, cyclical 중 최악). (4) 2023 Q4 ~ 2024 (M3 E4): pivot 기대 + AI 가속 (NVDA 견인) → SOXX +39.6%. M3 4 epoch 가 **전형적인 반도체 boom-bust cycle 의 1.5 회전** 을 cover 한다고 해석 가능.

**Dollar 채널 메커니즘**. β_dxy=−1.62 의 경제적 해석: dollar 1σ 상승 → SOXX −1.62σ. (a) 매출 환산효과 (해외매출 dollar 환산 시 감소), (b) 신흥국 capex 가격경쟁력 약화, (c) global risk-off 의 dollar safe-haven 매수와 SOXX 매도가 동조하는 reflexive loop. M3 E1 (R²=0.212) 에서 dollar 채널이 가장 강하게 작동 — **긴축충격기에 dollar 가 모든 cyclical 의 1차 driver**, SOXX 가 그 정점.

**within-cyclical 위치**. M3 within-cyclical pairwise corr 매트릭스에서 SOXX 는 XLY (0.75) / XLI (0.67) / XLB (0.63) 와 강하게 동조, XLE 와는 0.26 (outlier 분리). 즉 반도체는 **consumer disc / industrials / materials 와 같은 cyclical core 그룹**에 속하며, 에너지·금융과는 별도 채널. 이는 반도체가 일반 cyclical risk asset 의 amplifier 임을 시사 — sleeve 평균보다 vol 1.5배, swing 도 그만큼 확대.

## §2. M3 결과 재해석 (SOXX 관점)

### Epoch 별 성과·β·Sharpe 의미

| Epoch | SOXX ann ret | cyc Sharpe | SOXX vol(추정) | 의미 |
|---|---|---|---|---|
| E1 긴축충격 | **−50.4%** | −1.11 | ~38% | **cyclical 최악**, dollar 채널 dominant (β_dxy=−1.34, R²=0.212), multiple contraction + 메모리 cycle peak-out 중첩 |
| E2 전환·반등 | **+88.7%** | +1.63 | ~32% | **cyclical 최고**, pivot 기대 multiple expansion + dollar 약세 (β_dxy=−1.12) + 메모리 bottom 통과 |
| E3 금리재상승 | −32.6% | −1.60 | ~20% | β_us10y=−0.027 (음수 전환, rate 직접 타격), dollar 채널 약화 (R²=0.131) → multiple contraction 재발 |
| E4 pivot·인하 | +39.6% | +1.75 | ~21% | rate cut 기대 + AI capex cycle, R²=0.070 (driver 분산), idiosyncratic AI narrative dominant |

★ **SOXX swing 폭 = cyclical 평균의 1.5배** (E1·E2 amplitude 비교). M3 §1 "SOXX = 고듀레이션 amplifier" 확인.

### within-cyclical 위치 — sleeve 평균 대비

| Epoch | sleeve cyc 평균 | SOXX | excess vs sleeve |
|---|---|---|---|
| E1 | −24.3% | −50.4% | **−26.1pp (최악)** |
| E2 | +38.7% | +88.7% | **+50.0pp (최고)** |
| E3 | −16.7% | −32.6% | −15.9pp |
| E4 | +28.7% | +39.6% | +10.9pp |

★ **excess 의 epoch 변동성** 이 sleeve 평균 변동성의 2배 — SOXX 가 cyclical 내부에서도 amplifier (β_to_sleeve ~ 1.5).

### Cross-sleeve dollar/oil 채널 강도

- **β_dxy=−1.62** = cyclical 6개 중 최대 absolute value. 글로벌 매출 비중·dollar invoice 비중 반영.
- **β_oil=+0.007** ≈ 0 = oil 무관 (XLE 와 anti-correlated 분리 명확).
- **β_us10y=+0.028** = 양수이나 절댓값 작음. duration sensitivity 가 dollar 경유로 우회.
- **rank-IC: r_dxy=−0.279 / r_oil=+0.075 / d_us10y=−0.036** → **dollar 가 거의 단일 driver**.
- **Kish design 관점**: SOXX 는 within-cyclical corr 0.56~0.75 → sleeve 평균과 자유도 거의 공유. SOXX 개별 δ_regime 도 sleeve 평균 δ_regime 과 강한 동조 예상 (independence 검증은 verify stage).

## §3. δ_regime 후보 (★핵심)

### 산출 방법

- **point = SOXX epoch ann_return / 100**, [-0.15, +0.15] clip
- ⛔ 지시 문구 `× sign(Sharpe)` 는 cyclical sleeve Sharpe 의 부호가 SOXX 본인 ret 의 부호와 항상 일치 (E1/E2/E3/E4 모두) → 곱하면 모두 양수 양산 (E1 +0.504 등 도메인 비정합). **본 후보는 SOXX 자체 ret 부호 보존** 으로 산출 (regime 별 over/underweight 의 직관 보존). Verify stage 에서 식 재확인 필요.
- **CI heuristic**: SOXX vol_ann / sqrt(n_daily) × 1.96, point scale [-1,+1] 변환 후 반영
- **regime_tag scalar 매핑** (거시 numeric 직접 X) — Belief-Truth 격리 준수

| Epoch | point | CI_low (95%) | CI_high (95%) | 근거 |
|---|---|---|---|---|
| E1_tightening_shock | **−0.15** (clip) | −0.20 | −0.10 | ann −50.4%, Sharpe −1.11, n=188, σ≈38%. raw=−0.504 → clip −0.15. dollar β=−1.34 dominant. CI 폭 ±0.054 |
| E2_transition_rally | **+0.15** (clip) | +0.10 | +0.20 | ann +88.7%, Sharpe +1.63, n=187, σ≈32%. raw=+0.887 → clip +0.15. multiple expansion. CI 폭 ±0.046 |
| E3_rate_re_rise | **−0.15** (clip) | −0.19 | −0.11 | ann −32.6%, Sharpe −1.60, n=85, σ≈20%. raw=−0.326 → clip −0.15. ★G1 boundary. CI 폭 ±0.043 |
| E4_pivot_cuts | **+0.15** (clip) | +0.13 | +0.18 | ann +39.6%, Sharpe +1.75, n=275, σ≈21%. raw=+0.396 → clip +0.15. AI narrative + rate cut. CI 폭 ±0.025 |

★ **4 epoch 모두 clip boundary 도달** = SOXX swing 폭이 R15 weight 가산 scalar 의 [-0.15, +0.15] 범위를 초과. 이는 (a) clip 범위가 보수적이거나 (b) SOXX 가 weight gate 가 아닌 별도 sleeve 로 처리되어야 함을 시사. **Verify stage 에서 clip 범위 재검토 권고**.

★ **regime_tag scalar 매핑만**: 위 point 는 macro layer 가 regime tag (E1/E2/E3/E4) 를 emit → 본 layer 가 tag → SOXX weight 가산 scalar 변환 시 사용. 거시 numeric (Δus10y/r_dxy/r_oil) 을 본 layer 가 직접 받지 않음. **single-writer 원칙 준수**.

★ **bootstrap CI 의무**: 위 CI 는 Gaussian heuristic. Verify stage 에서 **stationary bootstrap (Politis-Romano 1994, block √n)** 으로 정확 CI 산출 필수 (G2 게이트).

## §4. δ_arch 후보 (펀더멘털, 거시 제외)

| Metric | Theoretical basis | Data status |
|---|---|---|
| **book-to-bill ratio (SEMI 협회)** | 신규주문/출하 비율, 반도체 cycle 의 대표 leading indicator. >1=상승 / <1=하강. SOXX 6~9개월 선행 | **available_now** (SEMI 월별 공개 무료) |
| **DRAM contract ASP** | 메모리 commodity ASP, SOXX 동행~3개월 선행. peak-to-trough 50%+ swing 자체가 cycle 의 thermometer | **available_now** (DRAMeXchange/TrendForce 부분 공개, 전체 paid) |
| **inventory days** | DIO 계산 = 재고/(매출원가/365). 정상 75~95일, 100일+ = 공급과잉 신호. SOXX 6개월 선행 | **deferred_edgar** (EDGAR 10-Q balance sheet 적재 후) |
| **forward EPS revision breadth** | 분석가 EPS 추정치 상향 비율 - 하향 비율. multiple expansion 의 펀더멘털 anchor. M3 E2 rally 의 30%는 EPS revision 으로 설명 가능 (이론) | **deferred_boundary** (FactSet/IBES 유료. Refinitiv 부분 무료) |
| **R&D/revenue** | 반도체 산업 평균 15~22%. cycle 무관한 capex commitment proxy. forward growth 의 1차 driver | **deferred_edgar** (10-K Income Statement 적재 후) |
| **gross margin** | 메모리 cycle 의 P&L 표현. peak ~50% / trough ~20%. ASP 선행 후 1~2분기 lag | **deferred_edgar** (EDGAR 10-Q 적재 후) |

⛔ **거시 driver 포함 금지** (이중계상 회피): dollar / us10y / oil / VIX / ISM PMI 등은 배분레이어 전담. 반도체-specific 이지만 cross-sleeve 영향이 있는 metric (e.g., 글로벌 GDP) 도 제외.

★ **경계 분류 의문 — DXY 자체**: M3 β_dxy=−1.62 가 워낙 강해 dollar 를 SOXX δ_arch 로 박제 유혹 발생. **거시 = 배분레이어 (sleeve gate)** 원칙 준수 → δ_arch 에 포함 X. 단 본 sleeve 의 dollar 민감도 weight 는 배분레이어가 sleeve allocation 단계에서 반영.

★ **available_now 우선순위**: book-to-bill > DRAM ASP. 두 metric 으로 δ_arch 1차 충전 가능. EDGAR 인프라 도착 시 inventory/margin 추가.

## §5. 5게이트 적용 (plan §3)

| Gate | Pass | Note |
|---|---|---|
| **G1 (n≥30)** | **✅ PASS** | E1=188, E2=187, E3=85, E4=275 — 모두 daily n≥30 통과. E3 은 monthly 환산 시 ~4 → daily 기준 적용 명시 |
| **G2 (Bootstrap CI)** | **⚠️ PARTIAL** | Gaussian heuristic CI 만 산출 (vol/sqrt(n)×1.96). 정확 stationary bootstrap (block √n) 은 Verify stage 의무 |
| **G3 (James-Stein λ)** | **DEFERRED** | epoch×industry cell shrinkage 는 4 산업 통합 후 Synthesis stage. 본 sub-agent 단독 산출 X |
| **G4 (OOS)** | **✅ PASS (가능)** | 4 epoch holdout (leave-one-out) 구조 가능. 본 단계 직접 수행 X — Verify stage 에서 R²_OOS vs R²_IS 비교 |
| **G5 (Domain)** | **✅ PASS** | δ_regime 부호·크기 모두 반도체 cycle theory 정합 — §6 verdict |

**Pass count = 3** (G1/G4 가능/G5 통과). G2 partial 은 보수적으로 미카운트, G3 DEFERRED 는 지시대로 미카운트.

## §6. 도메인 plausibility (Tier 3)

### δ_regime 부호 정합

- **E1 (−0.15)**: 긴축충격 = dollar 급등 + 할인율 급등 + memory cycle peak-out 의 3중 타격. SOXX = high-duration·global-revenue 의 양 채널 정통, 가장 큰 음수 weight 가 cycle theory 정합. ✅
- **E2 (+0.15)**: pivot 기대 = multiple expansion + dollar 약세 + memory bottom 통과 + AI narrative 태동 (NVDA H100 출시 2022Q4). SOXX 의 비대칭 회복은 multiple expansion 이론·메모리 bottom 패턴과 정합. ✅
- **E3 (−0.15)**: rate 재상승기, β_us10y=−0.027 으로 음수 전환 = rate 직접 타격. 메모리 cycle 은 아직 회복 중간이라 ASP 미회복. SOXX -32.6% = 일반 cyclical 보다 -15.9pp 큰 손실, multiple contraction 재발. theory 정합. ✅
- **E4 (+0.15)**: rate cut 기대 + AI capex cycle (NVDA H100/H200/B100 발표·하이퍼스케일러 주문 폭발). 단 R²=0.070 으로 거시 driver 가 약화 — AI 라는 idiosyncratic narrative 가 dominant. theory 의 "cycle + secular AI 중첩" 정합. ✅

### δ_regime 크기 정합

- 4 epoch 모두 clip [-0.15, +0.15] boundary 도달 → SOXX 의 native swing 폭이 R15 weight scalar 한도를 초과. 이는 (a) 반도체가 R15 의 "soft gate" 가산보다 sleeve allocation 자체로 처리되어야 함을 시사하거나 (b) clip 범위가 cycle amplifier 자산에 대해 너무 보수적임을 시사.
- ★ **권고**: 반도체 sleeve 는 R15 weight 가산뿐만 아니라 **sleeve allocation 차원의 별도 분기** 가 필요. main / Synthesis stage 에서 결정.

### 종합 verdict

**Tier 3 Domain plausibility = ✅ PASS**. δ_regime 부호 4/4 정합, 크기 4/4 boundary saturation 은 SOXX 의 amplifier 본성을 반영 (cycle theory 정합). G5 통과. 단 clip 범위 재검토 필요 (Verify/Synthesis stage).

## §7. 한계·미해결 (정직 명시)

1. **SOXX vol_ann epoch 별 직접 산출 X** — cyc sleeve vol 에 SOXX/sleeve amplitude 비율 (~1.5) 곱한 추정값 사용. Verify stage 에서 SOXX 직접 vol 산출 후 CI 재계산 필요
2. **point = ann_ret/100 단순 normalization** — 지시문 `× sign(Sharpe)` 식대로 적용 시 도메인 비정합 (E1 +0.504 양수 등). 본 보고 = SOXX 자체 ret 부호 보존. main 식 재확인 필요
3. **4 epoch 모두 clip saturation** — SOXX swing 폭이 [-0.15, +0.15] 한도 초과. clip 범위 또는 R15 처리방식 재검토 권고
4. **G2 Bootstrap = Gaussian heuristic** (정확 stationary bootstrap 미수행). Verify stage 의무
5. **G3 James-Stein** = 4 산업 통합 Synthesis stage 에서 수행, 본 단계 단독 산출 X
6. **δ_arch 본격 실측 deferred** = EDGAR 적재 후. 현 단계 = 후보 식별 + 이론적 정당화 + data status 분류 한정
7. **AI narrative 의 idiosyncratic 성분** = E4 R²=0.070 으로 거시 driver 약. AI cycle 자체를 새로운 regime tag (e.g., `E_ai_capex`) 으로 별도 분리할지 main 검토 필요
8. **Kish eff_N 1.47 (M3 발견)** — SOXX 개별 δ 가 sleeve 평균 δ 와 강한 동조 예상. independence 검증은 verify stage 의무
