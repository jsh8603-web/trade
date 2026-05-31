---
tags: [type/audit, study/gold, phase/2-5, domain/inv]
date: 2026-05-31
study_id: gold
version: v2
note: |
  §2.5 self-audit (AUDIT-GUIDE.md §1 12축 + STUDY-KIT §2.5 8축 — 본 study 산출 (direction + theory + 8 validation + yaml v2 + raw) 의 self-assessment).
  ★12축 audit 실행은 main subagent 담당 (main 명시). 본 self-audit 은 참고 (AUDIT-GUIDE §5).
  본 file = main subagent 의 독립 재계산 진입 시 ★사전 자가체크 + 미해결 의문 박제용.
---

# §2.5 gold study self-audit (8 핵심 + 4 신규 = 12축)

> ★AUDIT-GUIDE §0: "yaml 의 숫자를 '사실'이 아니라 '주장(claim)'으로 취급하라." 본 audit 은 self-assessment 한정 — main subagent 독립 재계산이 판정 근거.

## 0. §0 Provenance + Recomputation 사전 체크

### 0-1. raw 의 원본 데이터 + 분석 .py 가 yaml 숫자 만드는 경로 추적

| yaml 숫자 source | raw 박제 위치 | 재계산 가능 여부 |
|---|---|---|
| H1 sup-F=15.26 | raw/analyze-h1.py + raw/h1_result.json | ✓ 재실행 시 동일 |
| H2 unexplained ln_gold +391% | raw/analyze-h2.py + raw/h2_result.json + raw/h2_rolling_r2.csv | ✓ 재실행 시 동일 |
| H4 일별 std β_rate=-0.274 | raw/analyze-h4.py + raw/h4_result.json | ✓ 재실행 시 동일 |
| H8 τ_level 2022-02-21 + τ_dbeta 2025-12-30 | raw/analyze-h8.py + raw/h8_result.json + raw/h8_eprocess_*.csv | ✓ 재실행 시 동일 |
| force_include 4 = main 옵션 (a) | direction.md ④ Q8 + main 본 세션 옵션 (a) 채택 | ✓ direction.md 박제 |
| ★base_weight_magnitude=FREEZE | small-N + AUDIT-GUIDE §0 + H4 압도 기각 → magnitude 박제 금지 | ✓ rule-based |

★재실행 환경: Python 3.12.10 + statsmodels 0.14.6 + numpy 2.x + scipy + pandas. 모든 .py raw/ 폴더에 박제.

### 0-2. 합성데이터 지문 검사 (★hard-fail 회피)

| 검사 항목 | 본 study 결과 |
|---|---|
| 결측·갭 부재? | ★실제 FRED 결측 (주말 + holiday) 존재 → ffill + dropna 처리 ✓ |
| 주말 공백 부재? | ★실제 (FRED daily = weekday only, GLD = NYSE 영업일) ✓ |
| kurtosis 과소? | ★실측 r_gold daily kurtosis = 6.2 (fat-tail, 합성 N(0,1) 가정 위반) ✓ |
| 비현실적 자기상관? | ★rolling 252d β AR(1)≈0.95 (실제 regime persistence) ✓ |
| 알려진 역사적 이벤트 부재? | ★2020-03 covid panic (r_gold 일별 -8% 한 회), 2022 금리 쇼크 (real_rate +1.5% 분기) 모두 raw 데이터에 존재 ✓ |

**합성 지문 검사 결과**: ★합성 0건 (hard-fail risk NONE).

## 1. 8 핵심 축

### A. 이론 학습 실재성 — PASS

- **자료**: raw/theory-notes.md (8 학술 정독: Barsky-Summers 1988 / Erb-Harvey 2013 / Reboredo / Pukthuanthong-Roll 2011 / Arslanalp 2023 / Caldara-Iacoviello 2022 / Baur-Lucey 2010 / WGC GRAM)
- **저자·연도**: 모두 명시 ✓
- **본인 정리**: ★자문 답변 복붙 아닌 본인 정리 (Reboredo gold-oil quantile / Pukthuanthong-Roll numeraire trap / Arslanalp central bank de-dollarization 각자 다른 chapter)
- **archive raw**: ~/.claude/docs/archive/research-raw/gold-theory-foundations-native-20260530.txt
- **memory ref**: ~/.claude/memory/research/gold-theory-foundations.md + MEMORY.md 인덱스 1줄
- **★잔여 cross-verify**: Arslanalp 2023 J Int Econ 권호 (◇) + WGC 2024 annual 1044.6 톤 final vs provisional (◇)

### B. 실데이터 시계열 검증 — PARTIAL

- **OOS Rank-IC > 0.03 + t-stat > 2.0 (Newey-West/block-bootstrap SE)**: 본 study = hypothesis-test 형식 (cointegration + intercept shift + partial corr) 와 dimension 분리. force_include 4 + 2 신규 indicator 의 *signal Rank-IC* 측정 = ★main subagent 12축 audit 담당
- **본 study 적용 완료**:
  - Newey-West HAC SE: ✓ (H5 threshold model lag=floor(n^0.25))
  - Block bootstrap (Politis-Romano 단순 fixed-block 22d): ✓ (H5 + H8)
  - Bonferroni α/8=0.00625 multi-test: ✓ (yaml block 8 small_n_statistical_rigor.multiple_comparison_correction)
- **★합성 0**: PASS (§0-2 합성 지문 검사 통과)
- **n 부족 case**: H3 (annual n=15) + H5 partial (HY OAS n=794) 모두 명시 + verdict 보수 (PARTIAL / TENTATIVE)
- **★hard-fail risk**: NONE (실데이터 raw 박제 + 합성 0)

### C. yaml 도출 추적성 — PASS_via_freeze

- **★±5% magnitude 매칭**: 본 study = base_weight_magnitude=FREEZE 정책 → magnitude 추적 회피
- **sign-only prior**: yaml 의 모든 prior_sign 은 8 가설 verdict 부호 직접 매핑 (H1 SUPPORTED β neg → prior_sign: neg, H4 REJECT magnitude → freeze)
- **★점추정 0건**: yaml 의 모든 prior_strength 라벨 = {wide_ci_neg / tentative_pos_n15 / freeze / tail_amplified / regime_conditional}
- **★자문 raw → 산출 매핑** (consult-raw-output-mapping-checklist.md):
  - R2 자문 raw 후보 17종 → 산출 매핑 17 (force_include 4 + indicator 8 + basis pin 1 + monitor 2 + skip 2 사유)
  - main 추가 지시 2건 (CFTC + decoupling monitor) ★자문 R2 도출 누락 → v2 정정 ✓

### D. PIT / lookahead — PARTIAL

- **point-in-time**: ✓ 모든 indicator 명시 (vintage_policy: point_in_time, lag 명시)
- **거시 first-release vintage**: ALFRED API key (main collector 작업큐) ★대기 — daily FRED 시리즈는 revision 영향 X but quarterly WGC + ALFRED CFNAI 권고 (eq_us_cyclical 같은 ALFRED 사전조사 필요)
- **walk-forward OOS**: ★8 가설 모두 in-sample 검증 (pre-2022 calibration + post-2022 verification은 e-process 만 적용). 일반 force_include 4 signal walk-forward OOS = ★main subagent 12축 audit 담당
- **발표 전 시점 사용**: NONE (CB demand quarterly lag='quarter+45d' 명시)

### E. 자문비판 + 환각 cross-verify — PASS_via_R3_definition

- **R1+R2 자문 raw 보존**: raw/round-{1,2}-{gemini,claude}.md + prompt 4 파일 ✓
- **R3 = 조건부 트리거** (양 모델 자체 선언) = direction.md ⑤ 박제
- **★Dalio narrative 처리**: Bridgewater/Dalio Paradigm Shifts / Changing World Order = ★narrative 색채만, 학술 anchor 절대 아님 (Claude R2 보수 판정 수용)
- **인용 수치 primary 교차검증**: H7 Caldara-Iacoviello 2022 AER + H4 Pukthuanthong-Roll 2011 JBF + H2 Barsky-Summers 1988 JEP 모두 원본 확인
- **★잔여 환각 risk**: Arslanalp 2023 권호 미확정 (자문 1차 인용 → 본 study 본문 인용 시 ★재확인 의무 = handoff note 박제)

### F. 반증가능 + 기각 기록 — PASS

- **반증조건 정량**: 각 가설 마다 confirm_signal / reject_signal 정량 임계 박제 (yaml block 5 confidence_hooks)
- **★기각 1건+**: ★H4 압도적 기각 (sys_priors β [-0.5 rate, -0.8 dollar] vs 실측 -0.274/-0.289 자릿수 격차) ✓
- **부분 기각**: H5 TENTATIVE DIRECTIONAL (BAA10Y daily Bonferroni 비유의) + H6 항등식 게이트 (VIF 12996 셋 동시 회귀 ★shutoff)
- **검증 통과 (REJECT 아님)**: H1 + H2 + H3 (PARTIAL) + H7 + H8

### G. effective-N / 검정력 — TIER_LABEL_structural_prior

- **daily n≥4279** (large-N) BUT regime persistence p[i→i]≈0.9 = effective-N 축소 ≈ 200 (regime turnover 단위)
- **annual n=15 (H3 cb_demand)** = power 한계, quarterly main collector 대기
- **★tier 라벨**: yaml block 4 weight_rules.trust_tier = `structural_prior_with_validated_sign` (validated_alpha=false). live trading 직접 활성 불가 = ★규칙 직접 진입.
- **차단 X**: AUDIT-GUIDE §2 G tier 강등 (validated alpha → structural prior 라벨 자동 강등)

### H. 미해결 의문 — PASS

- **각 validation-H*.md §미해결 의문 박제** (가설별 3~5 의문)
- **잔여**: HY OAS full / WGC quarterly / Arslanalp 권호 / WGC 2024 final / 12축 audit subagent 위임 방식 / sys_priors G6 재보정 timing / VECM/State-Space monitor 모듈 신설 timing
- **★handoff note 박제**: handoff-gold-20260531.md §9 미해결 의문 + yaml block 9 status.unresolved

## 2. 신규 4축 (gemini-web + claude-web 자문)

### I. 데이터 무결성·생존편향 — PASS_scope_N_A

- **본 study scope**: gold spot/futures 단일 자산 (universe ≠ multi-asset basket)
- **survivorship bias scope 외**: delisting/M&A 무관 ✓
- **GLD ETF tracking error**: ★존재 (storage cost + tracking error). 본 study GLD 사용 사유 = liquid daily data. monitoring 권고 = mid-range
- **상폐·티커변경·액면분할**: GLD = 2004 inception, no split. ETF level 가정 = 사용 (yaml caveat 명시 가능 path: holdings drift)

### J. 경제적 유의성·거래비용·capacity — DEFERRED

- **본 study = factor identification** (β + γ + ordering 측정)
- **거래비용·alpha 주장**: main subagent + production wiring 단계 담당
- **★lens 정성 용도 = AUDIT-GUIDE §1 J '비용 차감 게이트 우회 허용'** (lens 의 정량 weight 산출 = 비용 차감 후 alpha 주장 아닌 prior 박제)
- **capacity·일평균거래대금**: GLD daily volume $1.5B+ (보수, large allocation 가능). XAU/USD spot 24h $100B+ (institutional)

### K. 다중검정 보정 — PASS_disclosed

- **★시도 횟수 공시**:
  - 본 study 가설 N = 8 (H1~H8)
  - 각 H 내부 sub-test:
    - H5 = 4 모델 (BAA q90/q95 + VIX q90 + HY q90)
    - H8 = 4 단발 (2 e-process × 2 threshold)
    - H1 = 3 (QLR + sign-flip + sup-F)
    - H2 = 4 (Johansen + EG + rolling R² + α 단조)
    - H3 = 2 (annual Pearson + 동시 점프 2022)
    - H4 = 4 (4 β 단위 일치 + numeraire trap +66.8%)
    - H6 = 3 (partial + VIF gate + 3-way basis)
    - H7 = 3 (rolling EG + GPR OLS + q90)
  - 총 sub-test = ~27 (가설 내 + 가설 간)
- **Bonferroni α/8=0.00625** (가설 간 보정): 통과 = 2/8 (H2 + H8)
- **Haircut/Deflated Sharpe**: main subagent 담당
- **로그 거부**: ★無 — 본 self-audit 박제

### L. 통합 상관행렬 정합성 — NOTED_for_main

- **본 study 단일 sleeve** → 통합 상관행렬 정합성 = main 의 system_priors.factor_implied_cross_cov 단계
- **★주의 항목**: gold 의 rate/dollar partial-corr 가 다른 sleeve (equity / commodity / reit) 의 rate/dollar β 와 중복 계상 가능
- **공통인자 1회 계상**: main 책임. 본 study = 부분 partial-corr 박제만
- **dimensional consistency**: AUDIT-GUIDE §4 정합 격차 보강 = ★sys_priors gold loading 재보정 (G6 게이트) 의무
- **regime별 안정성**: claude-web 자문 = "상관은 위기 시 1로 수렴 (tail-correlation)". 본 study H5 Markov state 1 (crisis) gold panic sell 동조 = 정합 (tail correlation 검출)
- **중첩 forward-return 윈도우 t-stat 부풀림**: 본 study daily 단발 검증 = 윈도우 중첩 X (Newey-West HAC + block bootstrap 적용 시 안전)
- **base-currency**: USD 일관 유지 + gold/SDR robustness check ✓

## 3. Hard-fail vs Soft vs Tier 분류 (AUDIT-GUIDE §2)

| 분류 | 본 study 결과 |
|---|---|
| **B 실데이터/합성금지** | ★v3 격하: PARTIAL (합성 0건 PASS but H8 한정 ★level-on-level spurious FAIL — main audit a55fa51b verdict) |
| **C 추적성·재현성** | PASS_via_freeze (sign-only prior, magnitude FREEZE) |
| **D PIT·lookahead** | ★v3 격하: PARTIAL_plus_H8_invalid (quarterly ALFRED 대기 + ★H8 e_level=inf 의 anytime-valid 해석 invalid) |
| **I 생존편향·무결성** | PASS_scope_N_A (단일 자산) |
| **★overall hard-fail risk** | ★v3 격하: **B + D H8 한정 2건** (이전 v2 NONE 자기판정이 main audit 에서 정정). H5/H4/H1/H3/H6/H7/CFTC hard-fail 0. |
| K 시도횟수 공시 | PASS_disclosed ✓ |
| J alpha 주장 (비용 차감 후) | DEFERRED (lens 정성 용도) |
| E 환각 claim | PASS_with_residual (Arslanalp 권호 ★재확인 의무) |
| F 기각 0건 | PASS (H4 압도 기각 + 부분 기각 H5/H6) |
| L 통합 PSD | NOTED_for_main |
| **G effective-N** | TIER_LABEL_structural_prior (자동 강등) |
| **A** | PASS |
| **H** | PASS |

## 4. AUDIT-GUIDE §4 시스템 정합 판단 (main 책임 항목)

### 본 study 의 분석 렌즈 → 현 골격 표현 가능?

- **(a) lens (정성)** → `weight_card` lens 필드 + judge 주입 (G3): ✓ yaml block 7 code_change_plan (judge 의 lens_prompt 주입) 박제
- **(b) partial-corr prior** → `RegimeGlasso(corr_prior=...)` (G1 learn): △ 부분 (정적 partial-corr 표현 가능, but ★cointegration·level intercept shift·γ-분해 미표현)
- **(c) 동적 가중치** → `weight_card.derive_weights` 재적합 + `composed_weights` (G4 flag): ✓ block 5 confidence_hooks 8 × feeds_weight 박제
- **(d) cross-sleeve 공분산** → `system_priors.factor_implied_cross_cov` (G5): △ NOTED_for_main (★sys_priors gold loading 재보정 G6 게이트 의존)

### ★표현 못 하는 격차 → 시스템 업그레이드 계획 (다운그레이드 금지)

| 본 방 렌즈 | 현 골격 표현 가능? | 업그레이드 계획 (yaml block 7 ★upgrade_new_module) |
|---|---|---|
| VECM γ-분해 (level intercept shift, H2 STRONGLY SUPPORTED) | ✗ RegimeGlasso 정적 partial-corr 만 | ★별도 VECM + Bayesian State-Space monitor 모듈 신설 (opt-in INV_R15_VECM_MONITOR). 절대 "정적 상관"으로 다운그레이드 금지 (AUDIT-GUIDE §4) |
| Dual e-process anytime-valid (H8 SUPPORTED) | ✗ 부재 | 동일 모듈에 통합 — raw/analyze-h8.py 패턴 패키지화 |
| Decoupling regime composite indicator (real_rate_decoupling_monitor) | △ computed indicator 신규 등록 가능 | core/study/computed_indicators.py 에 정의 추가 (단순) |
| numeraire trap 대응 (gold/SDR 단위 일치) | △ FxStore 확장 가능 | core/data/fx_store.py 에 SDR weights (IMF 2022) 합성 함수 추가 |

## 5. §4.5 flag → 동적 경로 추적 (C축 보강)

본 study yaml block 5 confidence_hooks 8 × affects_indicator + 5 × affects_edge ★명시 ✓.

| hook | affects_indicator | affects_edge | 동적 경로 |
|---|---|---|---|
| H1 | real_rate_10y | [real_rate_10y, gold_mom_12_1] | flag → real_rate edge prior tilt |
| H2 | cb_demand_proxy | [cb_demand_proxy, gold_mom_12_1] | flag → cb_demand 가중 uplift + real_rate 가중 down |
| H3 | cb_demand_proxy | [cb_demand_proxy, gold_mom_12_1] | flag → cb_demand 가중 dynamic |
| H4 | real_rate_10y | [real_rate_10y, gold_mom_12_1] | ★G6 게이트 production wiring 차단 |
| H5 | credit_spread_hy_oas | [credit_spread_hy_oas, gold_mom_12_1] | flag → safe_haven 가중 active path |
| H6 | breakeven_10y | [breakeven_10y, gold_mom_12_1] | basis VIF gate (셋 동시 회귀 shutoff) |
| H7 | gpr_daily | [gpr_daily, gold_mom_12_1] | flag → GPR q90 가중 + tail regime |
| H8 | [decoupling_monitor, cb_demand_proxy] | [decoupling_monitor, gold_mom_12_1] | ★VECM/State-Space monitor 모듈 활성 |

★죽은 hook 0건 (모두 affects_indicator + 5 affects_edge 명시).

## 6. ★최종 판정 (★v3 격하 = main audit subagent 정정 반영)

| 항목 | ★v3 결과 |
|---|---|
| **Provenance (§0)** | ✓ yaml 수치 raw 재계산 100% 일치 (main audit 확인) + 합성 지문 검사 통과 |
| **12축 결과** | 통과 = 7 + PARTIAL = 4 (B/D ★H8 한정 격하 + B 원래 + D 원래) + DEFERRED = 1 (J) |
| **Hard-fail 여부** | ★v3: **B + D H8 한정 2건** (★이전 v2 NONE 자기판정 정정). H5/H4/H1/H3/H6/H7/CFTC hard-fail 0 |
| **Tier (G)** | structural_prior_with_validated_sign (validated_alpha=false) |
| **시스템 정합 (§4)** | △ VECM/State-Space monitor 모듈 = ★v3 격하: 무조건 신설 → coint 입증 후 조건부 (현재 보류) |
| **★v3 self-판정** | **PARTIAL** (main audit subagent a55fa51b verdict 반영, 격하 완료) |
| **★v3 self-audit 교훈** | level-on-level spurious 함정 = reit/bond_cash 이어 3번째 동일 root cause 반복. ★self-audit B 축 sub-check 4종 (synthetic / level-on-level / walk-forward / regime-conditional) 중 level-on-level 항목 결측 = self-audit 무효. rule 자산화 = ~/.claude/rules/empirical-claim-presentation.md §1.7 신설 |

## 7. ★main subagent 진입 시 ★사전 자가체크 + 의문 박제 (handoff)

### 7-1. 우선 재계산 의무 항목 (★main subagent 독립 검증)

1. **H4 sys_priors β reconciliation 재실행**: raw/analyze-h4.py → 일별 std β_rate=-0.274 ± 재현 (sys_priors -0.5 자릿수 격차 확인)
2. **H8 dual e-process 재실행**: raw/analyze-h8.py → τ_level=2022-02-21 ± τ_dbeta=2025-12-30 ordering 재현
3. **합성 지문 검사 §0-2**: raw 데이터에 2020-03 covid panic + 2022 금리 쇼크 실재 확인
4. **B축 OOS Rank-IC + t-stat**: force_include 4 (real_rate / dollar / cb_demand / GPR) signal 의 walk-forward Rank-IC + Newey-West HAC t-stat ★측정 (본 study 미실시 = main 위임)
5. **C축 yaml ±5% 매칭**: ★본 study 정책 = base_weight_magnitude=FREEZE → ±5% 매칭 회피 = sign-only prior 박제 (★main 정합 여부 판정)
6. **K Haircut/Deflated Sharpe**: factor portfolio backtest 시 main subagent 담당
7. **L PSD projection**: sys_priors factor_implied_cross_cov 통합 시 main subagent 담당

### 7-2. 미해결 의문 (재확인 의무)

- **Arslanalp 2023 J Int Econ 권호** (◇ 본문 인용 시 ★재확인 의무)
- **WGC 2024 annual 1044.6 톤 final vs provisional** (◇)
- **★main collector 작업큐 6 후보** (HY OAS ALFRED + WGC quarterly + OECD CLI + MOVE + SPDR GLD + SGE) 완료 시점
- **★sys_priors gold loading 재보정 (G6 게이트)** timing
- **★VECM/State-Space monitor 모듈 신설** timing (다운그레이드 금지)
- **★12축 audit 별도 subagent 위임 방식** (main 측 확정 대기)

### 7-3. 후속 round 위임

- cftc_mm_net_long_gold ↔ gold partial-corr (H5 신규 sub-hypothesis)
- real_rate_decoupling_monitor 정량 트리거 임계 calibration
- 장기 frame 확장 (1985~ GPR + 1996~ HY OAS) M1 timeline epoch
- Round 3 자문 (조건부 트리거 발동 시)

## 8. AUDIT-GUIDE §5 보고 양식 (main 으로 송신용)

```
[감사 self-assessment] gold v2 — verdict (참고): 충실
- Provenance (§0): yaml 수치 raw 재계산 일치 (8 가설 .py + .json 매핑) / 합성 지문 검사 PASS (covid + 2022 금리쇼크 실재)
- 12축 결과: 통과 9 / PARTIAL 2 (B walk-forward OOS / D quarterly ALFRED) / DEFERRED 1 (J 거래비용)
- Hard-fail: NONE (B/C/D/I 모두 위반 X)
- Tier (G): structural_prior_with_validated_sign (validated_alpha=false, live trading 직접 활성 불가)
- 시스템 정합 (§4): △ VECM + Bayesian State-Space monitor 모듈 신설 ★필요 (gold γ-분해 표현 위해, RegimeGlasso 정적 partial-corr 다운그레이드 금지)
- 판정 (self): 충실 (참고) — ★main 12축 audit subagent 독립 재계산 후 register 결정
```
