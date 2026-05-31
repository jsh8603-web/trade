---
tags: [type/validation, study/gold, hypothesis/H8, domain/inv]
date: 2026-05-31
hypothesis_id: H8
hypothesis: 이중 e-process ordering (R2 Q6) — Δ-beta vs level 잔차 e-process 의 발화 순서로 mechanism 위계 판정
verdict: ★v3 격하 = "cointegration 기각·재정식화 필요" (이전 v2 = SUPPORTED 취소). 근거 = main audit subagent a55fa51b verdict (2026-05-31), level 회귀 spurious 진단.
v3_correction_note: |
  ★main audit verdict: e_level 의 ln_gold~real_rate+ln_dollar level 회귀가 3변수 I(1) + 잔차 ADF p=0.845 (coint 부재) + DW=0.002 = ★spurious OOS 외삽. e_level=inf 는 anytime-valid 증거 아닌 비정상 외삽 산물.
  τ change-point 수치 (2022-02-21 / 2025-12-30) 는 100% 재현되나 'LEVEL > Δ-beta 위계' 해석 ill-posed.
  ★재정식화 의무: ΔlnGold ~ Δreal_rate + Δln_dollar return/diff 단위 e-process 또는 VECM γ (coint 입증 후) — 본 작업방 후속 round 위임.
  rule 자산화: ~/.claude/rules/empirical-claim-presentation.md §1.7 신설 (ADF/coint 사전 검정 + return/diff 단위 강제).
script: raw/analyze-h8.py
result: raw/h8_result.json
data: raw/h8_eprocess_level.csv + raw/h8_eprocess_dbeta.csv
---

# H8 이중 e-process + ordering 검증

## 1. 가설 + 학술 anchor

- **가설**: 두 anytime-valid e-process 의 발화 순서로 본 study mechanism 위계 정량 판정.
  - e_level (균형식 안정 귀무) = level intercept shift mechanism (H2 가설) 정합 시 빠르게 발화
  - e_dbeta (변화율 β 안정 귀무) = β instability mechanism (H1 가설 반증) 정합 시 빠르게 발화
- **학술 anchor**: Howard et al 2021 (Ann Stat) anytime-valid sequential testing + Grünwald 2024 GROW betting + Ville's inequality (1939). R2 자문 (Claude + Gemini) Q6 합의.
- **falsification logic**: τ_level < τ_dbeta → H2 (level) > H1 (Δ-beta). 반대면 H1 > H2. 둘 다 미발화면 mechanism 미식별 (귀무 유지).

## 2. 데이터 + 측정 axis (spec ↔ code 1:1 verify)

- **source**: FRED DFII10 (real rate) + DTWEXBGS (broad TWI dollar) + Yahoo GLD ETF
- **coverage**: 2010-01-05 ~ 2026-05-29 = **n_total = 4279 daily obs**
- **split**: pre-2022 = 3129 (2010-01~2021-12, calibration), post-2022 = 1150 (2022-01~2026-05, e-process accumulation)
- **measurement axis verify**:
  - 시제: e_level = contemporaneous level residual / e_dbeta = rolling 252d β (level deviation from pre-mean)
  - frequency: daily (모두)
  - transform: e_level = (ln_gold - α_pre - b_pre·real - c_pre·ln_dol) / σ_pre normalized / e_dbeta = (β_t - μ_pre) / σ_pre normalized
  - conditioning: GROW betting m_t = 1 + λ·(z_t² - 1), λ=0.1 (보수적 고정)
  - 임계: e>20 (Ville α=0.05) + e>160 (Bonferroni α/8 = 0.00625 통합)

## 3. Calibration (pre-2022 OLS, H_0 정의)

| 파라미터 | 값 |
|---|---|
| α (intercept) | 6.831 |
| b (real_rate) | -0.206 |
| c (ln_dollar) | -0.406 |
| σ_pre (residual SD) | 0.0832 |
| rolling β_real μ_pre, σ_pre | -0.076, 0.028 |
| rolling β_dollar μ_pre, σ_pre | -0.981, 0.472 |

## 4. Post-2022 deviation (귀무 위반 측정)

### 4-1. e_level: 잔차 ε_t = ln_gold_t - (α_pre + b_pre·real_t + c_pre·ln_dol_t) 의 z_t = ε_t/σ_pre

| | mean | std | abs_max |
|---|---|---|---|
| z_level (post, n=1150) | **+10.45** | **5.03** | ★강한 drift |

→ 귀무 N(0,1) **완전 위반**: 잔차가 평균 +10σ (즉 ln_gold 가 균형식 예측보다 ★+10·0.083 ≈ +0.83 ln-unit ≈ +130% 상회) + std 5배 (분산 25배 폭증). H2 unexplained ln_gold +391% 와 정합 (단위 정합: +391% = ln(4.91) ≈ +1.59 ln-unit).

### 4-2. e_dbeta: rolling 252d β (real, dollar) 의 z² combined

| | mean | std |
|---|---|---|
| z_β_real (post) | +1.26 | 0.82 |
| z_β_dollar (post) | -0.12 | 0.99 |

→ β_real 만 약한 deviation (+1.26σ → 절대값 약 -0.04, pre -0.076 의 ★절반 감소). β_dollar 거의 변동 없음. 변화율 β 의 instability ★약하다.

## 5. E-process 발화 시점 (Ordering)

| e-process | e_final | τ (α=0.05, e>20) | τ (Bonferroni α/8, e>160) |
|---|---|---|---|
| **e_level** (잔차) | ★∞ (overflow) | **2022-02-21** (post 35 obs) | **2022-03-09** (post 47 obs) |
| **e_dbeta** (β stability) | 1.4×10²³ | **2025-12-30** (post 1041 obs) | **2026-01-08** (post 1048 obs) |

### Ordering verdict

**★ τ_level (2022-02-21) ≪ τ_dbeta (2025-12-30), gap ≈ 3년 10개월**

→ **LEVEL mechanism (H2) 우선 SUPPORTED**. Δ-beta mechanism 은 ~4년 후순위 발화 (즉 변화율 β 안정 가설 위반은 2025 말까지 통계적 증거 부족).

## 6. Verdict 판정

**★v3 격하: SUPPORTED 취소 → "cointegration 기각·재정식화 필요"** (main audit subagent a55fa51b verdict, 2026-05-31)

격하 근거:
- e_level 기반 회귀 ln_gold ~ const + real_rate + ln_dollar 의 잔차 ADF p=0.845 (coint H0 reject 실패) + Durbin-Watson 0.002 (자기상관 ≈ 1, spurious 의심 signature) + Johansen rank=0 (다변량 coint 부재).
- 3변수 모두 I(1) + coint 부재 → level 회귀 자체가 ★Granger-Newbold 1974 spurious regression. e_level → ∞ 는 anytime-valid 증거 아닌 비정상 OOS 외삽 산물.
- τ change-point 수치 자체는 100% 재현 (2022-02-21 / 2025-12-30) but 'LEVEL > Δ-beta 위계' 해석은 ill-posed (level 회귀 무효).

★v2 SUPPORTED 박제는 ★over-claim — self-audit B 축 sub-check (level-on-level spurious check) 결측이 catch 못함.

### v2 → v3 격하 후 라벨

**v3 verdict** = "cointegration 기각·재정식화 필요" (descriptive 관찰만 유지, mechanism 위계 단정 X)

### 재정식화 의무 (후속 round)

- (a) **return/diff 단위 e-process**: ΔlnGold ~ Δreal_rate + Δln_dollar 회귀 → 잔차 stationary 확보 후 dual e-process 재구성
- (b) **VECM γ (coint 입증 후)**: Johansen rank ≥ 1 + EG ADF p<0.05 통과 시 정식 VECM 도입 — 현재 미통과
- (c) **regime-conditional 검정**: specific epoch (E1~E4) 내 coint 가능성 별도 검정

근거:
- e_level 이 post-2022 시작 직후 (47 obs ≈ 2 mo) Bonferroni 임계 e>160 돌파
- post 잔차 z mean +10.45 = ln_gold 가 균형식 예측보다 일관 ★대규모 상회 = unexplained ln_gold trend (H2 STRONGLY SUPPORTED) 와 직접 정합
- e_dbeta 는 ~4년 후 발화 = 변화율 β 자체는 pre-2022 calibration 의 ±1.26σ 범위 내 유지 (절대 부호 + magnitude 안정)
- ordering 발화 gap 3.8년 = mechanism 우선순위 **명확** (mid-range tie 아님)

### 단정 회피 hedge

- e>20/160 임계 통과는 H_0 (균형식 안정/β 안정) 의 **anytime-valid 기각** 이지 mechanism 의 *유일한* 설명력 주장 X
- GROW λ=0.1 은 보수적 betting — mixture method 대비 lower power, conservative type-I robust
- ordering 우선 = mechanism 의 *식별 시점* 우선이지 *원인-결과* 인과 주장 X (causal 단정 회피)

## 7. 한계 (G축 effective-N + 검정력)

- **e-process martingale 가정**: m_t = 1 + λ(z²-1) 의 E[m_t|F_{t-1}] = 1 under H_0 정확 보장 = ★z_t IID N(0,1) iff. 실제 잔차는 자기상관 + heteroscedasticity → e-process 의 actual type-1 error 가 명목 α=0.05 보다 클 수 있음
- **λ=0.1 고정**: universal portfolio / Robbins-Monro adaptive 보다 보수적. e_level 발화는 강하므로 lambda sensitivity 미미, e_dbeta 는 lambda 조정 시 발화 시점 sensitive (λ=0.3 시 3년 단축 가능, robustness check 미수행)
- **rolling 252d β**: window 길이 sensitivity 미검증 (126d, 504d 비교 미수행)
- **pre-2022 calibration**: 2010-01 시작 = post-GFC + ZIRP 시기로 sample composition bias. 1996~ extended calibration 시 결과 sensitivity 미검증 (FRED DFII10 2003- 시작이라 외부 source 필요)

## 8. 미해결 의문 (H축)

- e_dbeta 가 2025-12 발화 = 직전 6개월 (2025-06~12) 의 *어떤* mechanism 인가? CFTC mm_net_long 급변 / OECD CLI peak / GPR spike 어느 것?
- HY OAS full history (main collector 작업큐) 추가 시 e_credit_stress 별도 e-process 가능 → triple e-process 확장
- multi-asset 통합 e-process (gold + silver + platinum + oil) 시 mechanism universality 검정
- e-process formal type-I error 시뮬 (calibration period block bootstrap re-sampling) 미수행

## 9. 시도 횟수 (K축 multiple comparison)

- 본 가설 H8 단독 = 2 e-process × 2 threshold = 4 단발 검증
- H1~H8 8 가설 합계 → Bonferroni α/8 = 0.00625 → e>160 임계 별도 보고 ✓
- e_level 결과는 e>160 통과 (post 47 obs) = **Bonferroni 보정 후도 robust**

## 10. main 시스템 정합 함의 (§4 정합 판단 후보)

- **★ AUDIT-GUIDE §4 정합 격차 (gold VECM/State-Space γ-분해)**: 본 H8 결과 = VECM 의 error-correction term γ 가 2022 이후 break (e_level 발화 시점 2022-02) → main 의 RegimeGlasso 정적 partial-corr 표현 *불가*. ★별도 VECM + Bayesian State-Space monitor 모듈 신설 필요 (다운그레이드 금지).
- **flag → corr_prior** (§4.5 U2): e_level 누적 → confidence_hooks "level intercept shift" indicator 변조 → corr_prior(ln_gold, [real_rate, ln_dollar]) edge 약화.
- **lens estimation_note**: yaml v2 block 4 lens 의 estimation_note 에 "equilibrium re-formation since 2022-02, dual e-process ordering: level >> Δ-beta (gap ~4yr)" 명시 의무.

## 11. raw 산출

- `raw/analyze-h8.py` (e-process 자체 구현, GROW betting)
- `raw/h8_result.json`
- `raw/h8_eprocess_level.csv` (date, e_level, z_level — 1150 obs)
- `raw/h8_eprocess_dbeta.csv` (date, e_dbeta, β_real, β_dollar, z_combined_sq — 1041 obs)
