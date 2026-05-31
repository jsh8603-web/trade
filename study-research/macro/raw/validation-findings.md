---
tags: [type/validation, domain/inv, study/macro, phase/2-3]
date: 2026-05-30
study_id: macro
phase: "2-3 실데이터 검증 (가설0 GATE PASS)"
data: "data/historical_{2022,2023,2024} 일별 6자산, n=756, 2021-12~2024-12"
script: raw/validate_macro_hypotheses.py
output: raw/validation-output.txt
note: macro 가설 0/2/4/5 실데이터 정식검정 결과·해석. v1(자문 코드화) 대비 진짜 진전 = 가설2 FAIL이 설계를 재조정.
---

# macro 2-3 검증 결과 (가설 0/2/4/5)

## 검정 요약표

| 가설 | 검정 | 결과 | 판정 |
|---|---|---|---|
| **0 (GATE)** | LR(Σ_regime vs Σ_static vs μ_regime) + OOS logLik | cov LR=95.2 p=4.9e-11 / mean LR=18.9 p=4.5e-3 / **공분산 정보이득 5.0배** / OOS A−B=+9.9 | **PASS ✅** |
| **2** | between-regime Ω(partial-corr) 거리 permutation 1000회 | 관측 0.326 vs null 평균0.302 95%분위0.430 / **p=0.348** | **FAIL ⚠️** |
| **4** | force-include 없이 직접엣지 부트스트랩 CI | dxy~us10y rate-up[+0.18,+0.38]·down[+0.16,+0.40] / gold~us10y up[−0.30,−0.11]·down[−0.39,−0.19] / dxy~gold 양 regime CI<0 | **PASS ✅** |
| **5** | sp500~us10y 직접 pcorr CI | rate-up[−0.02,+0.08] median+0.00 / down[+0.00,+0.08] median+0.03 — **양 regime CI∋0** | **PASS ✅** |

## ★핵심 발견 (v1 대비 진짜 진전 — 설계 재조정)

### 1. 가설0 PASS + 가설2 FAIL 의 종합 = 신호의 *소재* 재정의
- **가설0**: 국면조건부 *공분산*이 정적 대비 압도(정보이득 5배, OOS 견고). "신호가 평균 아닌 공분산"
  정식 입증(v1 dispersion≈0의 정량 확정).
- **가설2**: 그러나 *partial-corr 네트워크(Ω 구조)*는 rate-regime 간 유의하게 다르지 않다(p=0.35).
- **재조정(애널리스트)**: 둘을 합치면 — regime 신호는 **(a) 분산/변동성 크기 + (b) 공통원인(real-rate/
  dollar/risk) 매개 강도**에 있지, **sparse 직접엣지 네트워크의 *구조 변화*에 있지 않다.** 즉 국면이 바뀌면
  자산들의 *변동성과 공통인자 노출*이 변하지(공분산 magnitude), 직접 인과 배선(Ω 엣지)이 재배선되진 않는다.

### 2. 직접 거시구조는 regime 불변 = 구조적 안정 관계 (force-include 정당)
- dxy~us10y(+0.28)·gold~us10y(−0.21)·dxy~gold(−0.37) 직접 partial-corr 이 rate-up/down CI 거의 동일.
  = 이 거시 직접관계는 *국면 무관 구조 상수*. → 블록3 force-include prior 채택 정당(데이터가 안정 입증).
- sp500~us10y 는 양 regime 모두 직접 pcorr CI∋0 = **매개**(v1 raw-corr 반전 Δ-0.26은 공통원인/변동성
  loading 변화이지 직접 배선 아님). 가설5 입증 + v1 "stock~dollar 매개 0.36" 정합.

### 3. 설계 함의 — hard 국면별 Ω 스위칭 ❌ → [안정구조 + 분산스케일 + soft belief] ✅
- 가설2 FAIL = 2-1에서 예고한 **연속 belief 폴백 발동**. 국면별로 별개 Ω 네트워크를 hard-fit 하면 차이가
  noise 수준(permutation 비유의) → 과적합. 대신:
  1. **직접구조 Ω 는 (거의) 공통**으로 두고 force-include 안정엣지 유지,
  2. **regime별 변동성/분산 스케일**(D@corr@D 의 D)을 조건부로,
  3. **soft belief-mix Σ_eff**(between-dispersion)로 국면 전이 de-risk.
  → 이건 우리가 *이미 보유한* belief-mix Σ_eff 메커니즘이 정확히 하는 일. RegimeGlasso 가 regime별 Ω 를
  hard 분리하기보다, EB shrinkage 가 공통 prior 로 수축시키는 현 설계가 데이터와 정합(가설2 FAIL이 이를 지지).

### 4. 단서·한계 (정직)
- 가설2 비유의는 **crude 2-regime(rate-up/down) proxy** 때문일 수도 — 정식 Investment Clock 4국면
  (FRED 펀더멘털 기반)이면 네트워크 차이가 더 클 가능성 배제 못함. 단 *가용 데이터(rate proxy)에선*
  네트워크 regime-불변이 결론. FRED 펀더멘털 확보(collector_plan) 후 4국면으로 재검정이 후속 과제.
- glasso+EBIC+EB shrinkage 가 양 regime Ω 를 공통 prior 로 강하게 수축 → 네트워크 차이 축소에 기여
  (소표본 정당, 단 regime 차이 탐지력 저하 trade-off). λ sweep 민감도는 후속.

## study_session.yaml 갱신 방향 (이 검증 반영)
- 블록1 lens.regime_reading: "직접 거시구조는 국면 불변, 변하는 건 변동성·공통인자 노출" 추가.
- 블록3 relationships: 직접엣지(dxy~us10y/gold~us10y/dxy~gold) edge_type=direct + prior_strength=측정 median,
  force-include 화이트리스트 명시. sp500~us10y = common_cause(CI∋0 입증).
- 블록4 weight_rules: regime modulation = 분산스케일+belief-mix(hard Ω 스위치 아님) 명시.
- 블록5 confidence_hooks: omega_structure_drift = "네트워크는 안정적이라 drift 임계 보수적, 주 신호는 변동성".
- 블록7: inject belief-mix(검증된 경로) 우선, learn 의 hard regime Ω 분리는 EB shrinkage 공통수축 유지.
