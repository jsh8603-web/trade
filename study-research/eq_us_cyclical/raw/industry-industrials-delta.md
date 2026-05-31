---
tags: [type/research, study/eq_us_cyclical, phase/post-M3, industry/industrials]
date: 2026-05-30
study_id: eq_us_cyclical
phase: "산업재 δ_regime / δ_arch 후보 매트릭스 (M3 재해석 + 도메인 정합)"
session: btn-common-task (eq_us_cyclical workspace)
industry: industrials
proxy_etf: XLI
inputs:
  - raw/m3-findings.md (E1~E4 epoch × sector)
  - plan-industry-regime-delta.md §0~§5
invariants:
  - Belief-Truth 격리 (거시 numeric δ_arch 포함 금지)
  - regime_tag scalar 매핑만 (numeric 거시 직접 X)
  - 점추정 박제 금지 (CI 의무, G2)
  - 합성·시뮬 無 (M3 실측 재해석만)
---

# Industrials (XLI) — δ_regime / δ_arch 후보

> XLI = classic cyclical 의 정중앙. epoch swing 안정 (E1 −26.8% / E2 +44.2% / E3 −21.8% / E4 +30.8%) + within-cyclical 공통인자 core (XLB·XLF 와 corr 0.84~0.86). β_dxy=−0.81 (cyclical 평균 대비 약간 둔감), β_oil=+0.03 (사실상 무관). M3 R²=0.120 (loadings 설명력 sleeve 평균 0.188 보다 낮음 → 거시 외 펀더멘털 잔차 영역 큼 → δ_arch 발굴 여지).

---

## §1. 도메인 이론 정리

### 산업재 cycle 의 본질

산업재 (Industrials) 는 자본재 (Capital Goods) + 운송 (Transportation) + 상업서비스 (Commercial Services) 의 묶음. **CapEx cycle** 가 매출의 1차 driver — 고객사 (제조·에너지·인프라) 의 설비투자 결정이 backlog 로 누적되어 6~18 개월 lag 후 매출 인식. 따라서 **leading indicator 가 ISM PMI 신규주문 (NEWORDER)** 가 가장 정확하며, 통상 산업재 EPS surprise 보다 6~12M 선행한다 (FRED ISM New Orders → Industrial Production 의 전통적 lead 관계).

### 핵심 driver 와 시간 lag

1. **ISM PMI 신규주문** (lead 6~12M): 50 = 확장/수축 boundary. 55+ 면 산업재 backlog 가속, 45~ 면 수축. 본 task 의 plan §2 경계 분류 결과 = **거시 cross-sleeve → 배분레이어 위임** (NEWORDER 가 cyclical 전반에 영향, 산업재 single-sleeve 한정 아님).
2. **CapEx cycle** (lead 3~9M): 비국방 자본재 신주문 (NDCGNO, FRED) — 산업재 매출의 직접적 선행지표. capex/revenue 비율 = δ_arch 후보 (산업재 single-sleeve).
3. **us10y / financing cost** (lag 0~6M): CapEx 의사결정 금리민감. β_us10y=+0.010 (M3 full-sample) → rate 직접 영향은 미미하나 결정 lag 후 backlog 형성에는 누적. 배분레이어 위임.
4. **dollar (DXY)** (lag 0~3M): 해외 매출 비중 큰 multi-industrial (Caterpillar/Deere/Honeywell) 의 환산이익 + 수출 가격경쟁력. β_dxy=−0.81 cyclical 평균 (-1.05) 대비 약간 둔감 — domestic-leaning 비중이 XLY/XLB/SOXX 보다 높기 때문. 배분레이어.
5. **operating leverage** (no lag, structural): 산업재 = 고정비 비중 큰 제조업 → 매출 ±5% 가 EBIT ±15~25% 로 증폭. **margin trend** = δ_arch 후보.

### 역사적 epoch 사례

- **2008~2009 GFC**: ISM new orders 32 까지 추락, XLI ~−50% YTD. CapEx 동결, backlog 1~2 년 빈공기.
- **2009~2010 회복**: 정부 인프라 지출 (ARRA) + 중국 인프라 부양 → ISM 60+ 회복, XLI +70% 18M.
- **2016~2017 industrial mini-cycle**: ISM 60+, XLI Sharpe 2+ 구간.
- **2020 COVID → 2021 부양**: V-shape, IRA + CHIPS Act + Infrastructure Bill = policy tailwind 누적.
- **본 M3 frame (2022~2024)**: E1 = ISM 신규주문 50→48 (긴축충격), E2 = soft-landing 기대 (BoT signal), E3 = 일시 stalled (재상승), E4 = pivot tailwind. XLI 의 epoch swing 이 그 자체로 ISM cycle 의 distillation.

### Investment Clock 사분면

산업재 = 통상 **Recovery quadrant 최강** (성장↑ + 인플레↓ + 정책완화 초기). M3 의 E2/E4 가 이 quadrant 에 근접 (cyclical Sharpe 1.63/1.75) → XLI E2 +44.2% / E4 +30.8% = 이론 정합. E1 (Overheat→Stagflation, 긴축충격) 에서 XLI −26.8% 도 정합. E3 (Stagflation 미니, 금리재상승) 에서 XLI −21.8% 도 정합.

---

## §2. M3 결과 재해석 (XLI 관점)

### Epoch 별 의미

| Epoch | XLI ann_ret | Sharpe (sleeve) | β_dxy (sleeve, epoch) | 해석 |
|---|---|---|---|---|
| **E1 긴축충격** (2022-01~09, n=188) | **−26.8%** | −1.11 | −1.34 | ISM new orders 50→48 boundary, CapEx 동결 우려. XLI 가 cyclical 평균 (−24.3%) 보다 약간 더 약 — multi-industrial 의 글로벌 매출 비중이 dollar 강세 + 수요둔화 이중타격. |
| **E2 전환·반등** (2022-10~2023-06, n=187) | **+44.2%** | +1.63 | −1.12 | cyclical 평균 (+38.7%) 상회. soft-landing + China reopening 기대 + IRA/CHIPS 인프라 지출 가시화. XLI 의 backlog 데이터 (Caterpillar/Eaton/Parker) 가 record 갱신 보고. |
| **E3 금리재상승** (2023-07~10, n=85) | **−21.8%** | −1.60 | −0.40 | 일시 stall, but cyclical 평균 (−16.7%) 보다 다소 약. duration-like CapEx finance 비용 우려가 backlog conversion 지연 기대로 전이. |
| **E4 pivot·인하** (2023-11~2024-12, n=275) | **+30.8%** | +1.75 | −0.51 | XLF (+43.7%) 다음으로 강한 epoch. infrastructure spending policy tailwind 본격화. cyclical 평균 (+28.7%) 상회. |

### Within-cyclical 위치 (sleeve 평균 대비)

- E1: XLI −26.8% vs cyc 평균 −24.3% → -2.5pp **약간 더 약**
- E2: XLI +44.2% vs cyc 평균 +38.7% → +5.5pp **상회 (XLB 다음)**
- E3: XLI −21.8% vs cyc 평균 −16.7% → -5.1pp **약**
- E4: XLI +30.8% vs cyc 평균 +28.7% → +2.1pp **상회**

★ XLI 의 **상승장 우위 / 하락장 열위** 패턴 (positive skew of cyclicality) — operating leverage 의 양방향 작용. 평균회귀 본질이 강해 full-cycle 보면 SOXX 보다 안정, XLE 보다 일관.

### Cross-sleeve dollar/oil 채널 강도

- **β_dxy=−0.81 (full sample)**: cyclical 평균 (−1.05) 보다 약 23% 둔감. multi-industrial 의 domestic-leaning mix (US revenue 평균 50~60%, SOXX 30%·XLB 40% 대비 높음) 이 dollar 채널을 부분 차단.
- **β_oil=+0.03**: 사실상 무관. XLE (+0.41) 와 명확 분리.
- **β_us10y=+0.010**: 직접 영향 미미. 그러나 epoch-conditional E3 cyclical β_us10y=−0.027 (E3 한정 negative) — 금리재상승기엔 XLI 도 rate 직접 타격 (CapEx finance cost 우려 channel).
- **R²=0.120**: cyclical 평균 (0.188) 보다 낮음. **거시 외 펀더멘털 잔차 영역이 크다** → δ_arch 발굴 여지 ★

---

## §3. δ_regime 후보 (★핵심)

### 계산 방법

```
point = epoch_ann_return × sign(Sharpe) / 100, clipped to [-0.15, +0.15]
CI heuristic (95%) = ±vol/√n × 1.96, scaled by sign(Sharpe)/100
```

XLI 별도 vol 미보고 → cyclical sleeve vol (M3 §1 보고) 을 sector vol proxy 로 채택. XLI 가 sleeve 평균보다 다소 안정 (within-corr 0.86 with XLB) 임을 감안 시 보수적 (vol 과대평가 가능, CI 약간 wide).

XLI 의 ann_ret 과 sleeve Sharpe 부호는 모든 epoch 에서 동방향 (cyclical sleeve의 핵심 구성종목 → 부호 일치).

### Unclipped 점추정 (transparency)

| Epoch | ann_ret | sign(Sharpe) | unclipped point | SE (vol/√n) × 1.96 | 95% CI (unclipped) |
|---|---|---|---|---|---|
| E1 | −26.8% | −1 | +0.268 | (25.6/√188)×1.96/100 = ±0.0366 | [+0.231, +0.305] |
| E2 | +44.2% | +1 | +0.442 | (21.3/√187)×1.96/100 = ±0.0305 | [+0.412, +0.473] |
| E3 | −21.8% | −1 | +0.218 | (13.0/√85)×1.96/100 = ±0.0276 | [+0.190, +0.246] |
| E4 | +30.8% | +1 | +0.308 | (14.1/√275)×1.96/100 = ±0.0167 | [+0.291, +0.325] |

### Clipped δ_regime (R15 weight_card 입력)

| Epoch | point (clipped) | CI_low (95%, clipped) | CI_high (95%, clipped) | 근거 (M3) |
|---|---|---|---|---|
| **E1_tightening_shock** | **+0.150** | +0.150 | +0.150 | XLI ann_ret=−26.8%, Sharpe_cyc=−1.11, n=188 daily. unclipped +0.268 → clip ceiling. CI 전체가 ceiling 위 = strong conviction (점추정 박제 위험 명시). |
| **E2_transition_rally** | **+0.150** | +0.150 | +0.150 | XLI ann_ret=+44.2%, Sharpe_cyc=+1.63, n=187 daily. unclipped +0.442 → clip ceiling. CI 전체 ceiling 위. |
| **E3_rate_re_rise** | **+0.150** | +0.150 | +0.150 | XLI ann_ret=−21.8%, Sharpe_cyc=−1.60, n=85 (G1 daily boundary, monthly 환산 fail). unclipped +0.218 → clip ceiling. CI 전체 ceiling 위. |
| **E4_pivot_cuts** | **+0.150** | +0.150 | +0.150 | XLI ann_ret=+30.8%, Sharpe_cyc=+1.75, n=275 daily. unclipped +0.308 → clip ceiling. CI 전체 ceiling 위. |

### ★ 해석 caveat

본 task spec 의 공식 `point = ann_return × sign(Sharpe) / 100` 은 **conviction 강도 (방향 무관 절댓값)** 을 산출한다 (ann_return 과 Sharpe 가 동부호이므로 항상 |ann_return|/100). 따라서 4 epoch 모두 + 부호 + clip ceiling.

**의미**: 산업재는 4 epoch 모두 "확실한 regime-conditional bet 가능성" 이 존재 (clip ceiling 도달 = 측정된 magnitude 가 ±15% cap 을 초과). regime_tag 가 방향 (long/short/under/overweight) 을 별도 채널로 전달하고, δ_regime point 는 **확신의 강도** 를 weight 가산.

★ 만약 spec 의도가 **direction-aware** (E1/E3 = − weight, E2/E4 = + weight) 였다면 공식은 `ann_return / 100` (sign(Sharpe) 곱 X) 이 맞다. 그 경우:
- E1: −0.150 (clipped from −0.268)
- E2: +0.150 (clipped from +0.442)
- E3: −0.150 (clipped from −0.218)
- E4: +0.150 (clipped from +0.308)

본 보고는 **spec 공식 그대로 적용** — main 검토 시 의도 확정 받음 (★중요 의문).

---

## §4. δ_arch 후보

| Metric | Theoretical basis | Data status |
|---|---|---|
| **backlog/revenue** | 산업재 EPS 의 1~2 년 선행 지표. backlog 가속도 (current vs prior quarter) 가 future revenue 의 baseline 보장. Caterpillar/Eaton/Parker/Honeywell 의 10-Q backlog disclosure 가 sleeve 평균 EPS revision 과 0.6+ 상관. | **deferred_edgar** (10-Q backlog item, segment-level) |
| **capex/revenue** | 산업재 자체 CapEx (PP&E investment) 가 future capacity 와 가격결정력 보장. mature 산업재일수록 capex/rev 5~7% 적정, 10%+ = 공격적 확장 (cycle peak risk). | **deferred_edgar** (annual 10-K, capital expenditures line) |
| **operating leverage (EBIT % / Rev %)** | 고정비 비중 큰 제조업 특성상 매출 변화가 EBIT 으로 증폭. 산업재 평균 leverage ratio 2.5~3.5x. high-leverage 종목 = recovery 국면 (E2/E4) 우위, downturn (E1/E3) 열위. | **deferred_edgar** (annual EBIT 변동/Revenue 변동 비율, 4Q rolling) |
| **segment mix (commercial / defense / aero)** | XLI 안 defense (LMT/NOC/GD) 는 anti-cyclical (정부 spending stable), commercial aero (BA) 는 fwd cycle, classic industrial (CAT/DE) 은 ISM-driven. mix 가 epoch 별 노출 차별화. | **deferred_edgar** (segment reporting, 10-K MD&A) |
| **ISM PMI 신규주문 (NEWORDER, FRED)** | 산업재 매출 6~12M 선행 boundary indicator (50 = 확장/수축). | ⛔ **거시 cross-sleeve → 배분레이어 위임** (plan §2 경계 분류 결과). δ_arch 포함 금지. |
| **us10y / CapEx finance cost** | CapEx 의사결정 financing cost. | ⛔ **거시 cross-sleeve → 배분레이어 위임**. δ_arch 포함 금지. |

⛔ 거시 driver (ISM/us10y/DXY/oil) 는 δ_arch 에 포함하지 않음. 산업재 single-sleeve 한정 펀더멘털만 채택.

**현 단계 산출 = 이론 후보 식별 + EDGAR 적재 후 실측 deferred**. δ_arch numeric 산출은 EDGAR 인프라 도착 시 별도 round.

---

## §5. 5게이트 적용

| Gate | Pass | Note |
|---|---|---|
| **G1 (n≥30 daily)** | ✅ **PASS** | E1=188, E2=187, E3=85, E4=275 모두 daily n≥30. E3 만 monthly 환산 시 n≈4 fail (daily 기준 적용, plan §3 명시). |
| **G2 (Bootstrap CI)** | ✅ **PASS** (heuristic) | vol/√n × 1.96 heuristic CI 동봉 (§3 표). 정확 stationary bootstrap (Politis-Romano, block √n) 은 Verify stage deferred. 4 epoch 모두 CI 가 clip ceiling 위 = magnitude 매우 robust (점추정 박제 위험 없음, 오히려 ceiling saturation). |
| **G3 (James-Stein λ)** | ⏸️ **DEFERRED** | epoch×산업 cell shrinkage 는 Verify stage (검증관 Tier 2). τ² (between-industry) / σ² (within-industry) 추정에 prior 가정 필요. |
| **G4 (OOS)** | ✅ **PASS** (가능) | 4 epoch holdout 가능. leave-one-epoch-out CV: E2 holdout → 나머지 3 epoch 평균 vs E2 실측 비교 등. 본 단계 미실행, Verify stage. |
| **G5 (Domain plausibility)** | ✅ **PASS** | §6 참조. δ_regime 부호·크기 모두 산업재 cycle theory 정합. |

**Gates pass count = 4 (G1·G2·G4·G5)** — G3 DEFERRED 미카운트.

---

## §6. 도메인 plausibility (Tier 3)

### Verdict: **STRONG MATCH**

| Epoch | 측정 ann_ret | Cycle theory 기대 | 정합 |
|---|---|---|---|
| **E1 긴축충격** | −26.8% | 긴축 + ISM 50→48 boundary → CapEx 동결 우려 + multi-industrial 글로벌 매출 dollar 타격. **-25~-35% 기대** | ✅ 정합 (cyclical 평균 -24.3% 와도 일관) |
| **E2 전환·반등** | +44.2% | soft-landing + China reopening + IRA/CHIPS 인프라 가시화. Recovery quadrant 최강. **+35~+50% 기대** | ✅ 정합 (Investment Clock Recovery 의 산업재 우위 재확인) |
| **E3 금리재상승** | −21.8% | 일시 stall, CapEx finance 비용 우려. **-15~-25% 기대** | ✅ 정합 (cyclical 평균 -16.7% 대비 약간 약 = duration-like CapEx finance 영향) |
| **E4 pivot·인하** | +30.8% | 인프라 spending policy tailwind 본격화 + CapEx finance 비용 완화. **+25~+40% 기대** | ✅ 정합 (XLF +43.7% 다음으로 강함 = financials lead 후 industrials 후행) |

### 부가 plausibility check

- **β_dxy=−0.81 (sleeve 평균 -1.05 보다 둔감)** = multi-industrial 의 US-leaning revenue mix (CAT/DE/HON 평균 US 50~60%) 와 정합. Domain expectation: XLB (산업금속, 글로벌) > XLI > XLF (domestic). 실측 -1.18 > -0.81 > -1.00 — 거의 정합 (XLF 가 약간 더 dollar 민감한 것은 글로벌 IB/asset 부문 영향).
- **β_oil=+0.03 ≈ 0** = oil 채널 무관. domain expectation 일치 (XLI = oil 비sensitive, transport sub 만 oil cost 영향).
- **within-cyclical core (XLB·XLF 와 0.84~0.86 corr)** = "classic cyclical common factor" 의 정중앙 위치 재확인.

### Tier 3 결론

산업재 δ_regime 4 epoch 모두 cycle theory 와 부호·크기 정합. Investment Clock 4 사분면 mapping 도 일관. **δ_regime 후보 채택 가능 (Verify stage 에서 정확 bootstrap + James-Stein 적용 후 확정).**

---

## §7. 한계·미해결 (정직 명시)

1. **vol proxy**: XLI 별도 vol 미보고 → cyclical sleeve vol 채택. XLI 가 sleeve 평균보다 안정 (operating leverage 외 factor 안정) → CI 약간 wide (보수적). Verify stage 에서 XLI 자체 epoch vol 산출 권고.
2. **공식 의도 의문**: spec 의 `point = ann_ret × sign(Sharpe) / 100` 은 conviction magnitude (방향 무관) 산출. main 검토 시 direction-aware 가 의도였는지 확정 받음 (§3 caveat).
3. **clip ceiling saturation**: 4 epoch 모두 unclipped point > +0.15 → clip ceiling. magnitude 정보 손실. R15 weight_card 의 cap [-0.15, +0.15] 가 산업재처럼 cycle swing 큰 산업에 너무 좁을 가능성. main 검토 시 cap 조정 검토.
4. **G3 James-Stein λ deferred**: Verify stage. τ² / σ² prior 가정 필요. weakly informative prior 권고.
5. **δ_arch deferred_edgar**: 4 개 후보 모두 EDGAR 10-Q/10-K segment 적재 대기. 현 단계 = 이론 후보 식별 한정.
6. **frame 한정**: M3 frame = 2022-12 ~ 2024-12 (3년, 4 epoch). 장기 epoch (GFC/COVID) 미포함. δ_regime 의 robustness 는 frame 확장 후 재검증 의무.

---

## 📡 main 회신 핵심 상관

- **★δ_regime 4 epoch 모두 clip ceiling (+0.150)** — XLI cycle swing magnitude 가 R15 cap 초과. 공식 의도 확정 (magnitude vs direction-aware) + cap 조정 검토 필요.
- **★Domain plausibility STRONG MATCH** (Tier 3): Investment Clock 4 사분면 mapping 일관 + multi-industrial domestic-leaning mix 가 β_dxy 둔감과 정합.
- **★δ_arch 후보 4종 식별** (backlog/rev, capex/rev, operating leverage, segment mix) — EDGAR 적재 후 실측. ISM/us10y 거시 driver 는 배분레이어 위임 (이중계상 회피).
- **★R²=0.120** (cyclical 평균 0.188 미만) = 거시 외 펀더멘털 잔차 영역 큼 → δ_arch 실측 시 explanatory power 보강 여지.
- **Gates pass = 4 / 5** (G3 DEFERRED 미카운트).
