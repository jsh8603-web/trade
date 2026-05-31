---
tags: [type/evaluation, study/gold, phase/audit, domain/inv]
date: 2026-05-31
study_id: gold
version: v2
auditor: opus 12-axis independent audit subagent
note: |
  AUDIT-GUIDE.md §1 12축 독립 감사. self-audit(audit-2.5-checklist.md) 신뢰 X — raw .py 재실행 + 실데이터 재계산이 판정 근거.
  재현 환경: Python 3.12 + statsmodels + numpy/scipy/pandas, cwd D:/projects/Inv.
---

# [감사] gold v2 — overall verdict: **부분 (PARTIAL) — H8 "SUPPORTED" 격하 의무, H5 유지, CFTC 통과**

> 한 줄: 수치 재현성은 100% 일치하나, **H8 dual e-process 의 "LEVEL mechanism 우선 SUPPORTED" 결론은 spurious level regression 위에 세워진 통계 인공물** (B축 spurious + D축 martingale 가정 위반). H5 TENTATIVE / CFTC n=157 은 정당.

---

## 0. Provenance + Recomputation (§0) — 재계산 일치 여부

| 검증 | 재실행 결과 | json/md 일치 |
|---|---|---|
| H8 analyze-h8.py 재실행 | τ_level=2022-02-21, τ_dbeta=2025-12-30, e_level=inf, e_dbeta=1.41e23 | ✓ **정확 일치** |
| H5 analyze-h5.py 재실행 | γ_BAA_q90=-0.0252 (p=0.273), Markov AIC=-27836.5, crisis state mean=-3.4bp | ✓ **정확 일치** |
| CFTC extract 재실행 | n=157 weekly, 2022-01-04~2024-12-31, net_long [-43094, 219029] | ✓ **정확 일치** |
| H2 결과 json 교차확인 | `H2_supported: false`, `coint_support: false`, Johansen rank=0 | ★yaml 과 **불일치** (아래 C축) |
| 합성 지문 검사 | FRED 결측/주말 공백 실재, r_gold fat-tail, 2020-03·2022 이벤트 실재 | ✓ **합성 0건** |

**합성 데이터 hard-fail: NONE.** 모든 입력은 실측 FRED/Yahoo/CFTC raw. 재현성 자체는 흠 없음.

---

## H8 — dual e-process ordering: **SUPPORTED → ★TENTATIVE/격하 (방법론 결함)**

### Provenance
analyze-h8.py 재실행 = json 완전 일치. τ_level 2022-02-21 ≪ τ_dbeta 2025-12-30 gap 3.8년 재현됨. **수치는 맞다.**

### ★B축 spurious (★가장 중요한 결함) — FAIL

H8 의 `e_level` 은 **level-on-level 회귀** `ln_gold ~ const + real_rate + ln_dollar` 의 정규화 잔차로 정의됨. 독립 ADF/KPSS 재계산:

| series | ADF p | KPSS p | 판정 |
|---|---|---|---|
| ln_gold | **0.994** | 0.010 | ★I(1) 비정상 |
| real_rate | 0.594 | 0.010 | ★I(1) 비정상 |
| ln_dollar | 0.644 | 0.010 | ★I(1) 비정상 |
| r_gold (diff) | 0.000 | 0.053 | 정상 |
| d_real (diff) | 0.000 | 0.100 | 정상 |

세 변수 모두 비정상 I(1). level 회귀 진단:
- **DW = 0.002** (≈0 = 교과서 spurious regression 지문)
- full-sample 잔차 **ADF p=0.845 = 비정상** → **cointegration 없음** (Engle-Granger 기각)
- **방의 자체 H2 json 도 `coint_support: false`, Johansen rank=0, Gregory-Hansen reject=false 로 동일 결론을 이미 박제**

→ e_level 은 cointegrating 균형이 *존재하지 않는* 회귀의 잔차. "균형식 안정 귀무 위반" 이라는 H8 framing 자체가 성립 불가 (안정 균형식이 애초에 없음).

### ★e_level 발화의 기계적 정체 (mechanism 재구성)
- pre-2022 calibration: b_real=**-0.206** (NEG)
- post-2022 real_rate 평균 **+1.33%p 상승**, 동시에 gold 상승
- NEG 계수 × 상승한 real_rate ⇒ 균형식이 gold **하락을 예측** → 실제 gold 상승 ⇒ 잔차 +10σ 로 **기계적 폭증**
- e_level=inf 는 "anytime-valid 강한 증거" 가 아니라 **비정상 회귀를 OOS 외삽한 결정론적 산물**

### ★D축 martingale 가정 위반 — e-process Ville 보증 무효
GROW e-process 의 type-I 보증은 `z_t ~ IID N(0,1) under H0` 전제. 실제 잔차는 (a) 비정상 (b) DW 0.002 의 극단 자기상관 → `E[m_t|F_{t-1}]=1` 깨짐. **스크립트 §7 한계 자체가 이를 자인** ("실제 잔차는 자기상관 + heteroscedasticity → actual type-1 error 가 명목 α 보다 클 수 있음"). 잔차 자기상관 0.002 수준에서는 "클 수 있음" 이 아니라 **보증 전면 붕괴**. e_level 발화 일자 = look-ahead 는 없으나(sequential) 정당한 anytime-valid 사건이 아님.

### gap 3.8년 해석 타당성 — ★기각
"τ_level(2022) ≪ τ_dbeta(2025) gap 3.8년 = LEVEL mechanism 우선" 은:
- e_level 측: 위 spurious 인공물 → 발화 자체가 무효
- e_dbeta 측: rolling β z_real mean +1.26σ (즉 β 거의 안정) 인데도 누적 e_dbeta=1.4e23 발화 = λ·(z²-1) 의 점진 누적 (1041 obs 곱셈). 이 역시 "변화율 mechanism 식별" 이 아니라 작은 deviation 의 산술 누적.
- 두 e-process 의 발화 시점 차이를 mechanism 위계로 해석하려면 **두 H0 가 모두 valid e-process** 여야 함. e_level 이 무효이므로 **ordering 비교 자체가 ill-posed**.

→ **H8 verdict: SUPPORTED → 격하.** 정당한 잔여 신호 = "post-2022 ln_gold 가 pre-2022 단순 OLS 선형결합에서 대규모 이탈" (이건 사실) but 이를 "LEVEL mechanism > Δ-beta mechanism" 위계 + anytime-valid SUPPORTED 로 박제 불가. **sign prior 로 격하: "2022 이후 gold 가 전통 real-rate/dollar 선형식에서 이탈 (방향 = 상방)" tentative, mechanism 인과·위계 단정 금지.**

### H8 12축
B FAIL(spurious) · C PARTIAL(yaml H2 격상 불일치) · D FAIL(martingale 가정) · A PASS · F PASS · G structural_low · H PASS · I N/A
- **hard-fail: B + D (2건)**

---

## H5 — safe-haven regime: **TENTATIVE DIRECTIONAL — 유지 (정당)**

### Provenance
analyze-h5.py 재실행 = json 완전 일치.

### 12축
- **B**: γ_BAA_q90=-0.0252, NW HAC SE 0.023, t=-1.10, **p=0.273** → Bonferroni α/8=0.00625 한참 미달. ΔVIX γ 부호조차 +(無). block bootstrap CI 0 포함. → 부호만 음(3/4), magnitude 비유의 = TENTATIVE 라벨 정확. **PASS** (실측, 합성 0).
- **B축 spurious 점검**: H5 는 **diff/return 단위** (r_gold ~ Δstress) 사용 → 정상 series 회귀. spurious 함정 회피됨 (H8 과 대조적으로 올바름). ✓
- **D**: BAA/VIX daily same-day publish, PIT 적합. HY OAS 3년치 한정 명시. PASS.
- **F**: Markov crisis state gold mean=-3.4bp (panic sell 동조) = Baur-Lucey 직관 반대 신호 정직 박제 = 기각 기록 ✓.
- **G tier**: n_daily=4279 but regime persistence p≈0.9 → effective-N≈200 명시. **structural_prior** 정당.
- **hard-fail: 0건.** TENTATIVE DIRECTIONAL 격하 라벨이 통계 현실과 정합. small-N rigor (n·p·HAC·block boot·Bonferroni·hedge 어휘) 전부 준수.

### H5 tier 재판정
★**structural_low_confidence / TENTATIVE DIRECTIONAL 유지.** validated_alpha=false 정당. BAA10Y daily 단독으로는 가설 무효, HY OAS full(1996~) monthly 적재 후 재검증 조건부 = collector_plan priority 1 정합. **격상 불가, 현 라벨 적정.**

---

## CFTC mm_gold — **n=157 추출: PASS**

### Provenance
extract 재실행 = n=157, 2022-01-04~2024-12-31, "GOLD - COMMODITY EXCHANGE INC." 단일, net_long [-43094, 219029]. **정확 일치.**

### 12축
- **B/D/I**: 088691 managed-money long−short, weekly Tue report / Fri release lag='3d' 명시 (PIT 적합). CFTC 보고 연속성 = COT zip 2022/2023/2024 연속, 결측 없음 (n=157 ≈ 52주×3 정합). 생존편향 무관(단일 contract). PASS.
- **C**: yaml 에서 `prior_strength: untested_in_v2`, `force_include: false`, `deferred_for_round: next` 로 **명시적 미검증 박제** = 점추정 박제 0 = 정직. PASS.
- ★주의: date_max **2024-12-31** (yaml 주석 "2022-01~2024-12" 정합) — 2025~2026 누락이나 v2 미검증 indicator 라 영향 없음. full history extension 대기 = collector 정합.

---

## C축 — yaml v2 수치 추적성: **PARTIAL (★1건 격상 불일치)**

- ★**핵심 불일치**: 방 자체 `h2_result.json` 의 `H2_supported: false` + `coint_support: false` + Johansen rank=0 인데, yaml 과 validation summary 는 H2 를 **"★STRONGLY SUPPORTED"** 로 격상 박제. 근거 = "unexplained ln_gold +391% 단조 + e_level 발화" 인데 이 둘 다 위 spurious 메커니즘의 동일 산물. **cointegration 부재 = 균형식 자체 부재**인데 "균형식 재구성(equilibrium re-formation)" 으로 서사화 = ★over-claim. STRONGLY SUPPORTED → **PARTIAL/sign-prior 격하 의무.**
- 나머지: base_weight 전부 `magnitude=FREEZE` + sign-only prior = 점추정 박제 0건 = small-N FREEZE 정책 정당 (C 추적성 회피 합법). prior_strength 라벨 전부 정성(wide_ci_neg/tentative/freeze) = 매직넘버 0.
- → C: magnitude 측면 PASS_via_freeze, **verdict 격상(H2/H8) 측면 FAIL**.

---

## 종합 12축 PASS/PARTIAL/FAIL

| 축 | 결과 | 근거 |
|---|---|---|
| A 이론 | PASS | 8 학술 정독, 저자·연도 명시 |
| **B 실데이터** | **PARTIAL→FAIL(H8)** | H5/CFTC 실측 OK · ★H8 e_level = spurious level 회귀 (ADF resid p=0.845, DW 0.002, coint 부재) |
| **C 추적성** | **PARTIAL** | FREEZE 정책 OK · ★H2 STRONGLY SUPPORTED / H8 SUPPORTED 격상이 자체 json(H2_supported=false)과 불일치 |
| **D PIT/martingale** | **PARTIAL→FAIL(H8)** | daily PIT OK · ★H8 e-process martingale 가정(IID N(0,1)) 비정상·자기상관으로 붕괴 → Ville 보증 무효 |
| E 자문환각 | PASS_residual | Arslanalp 권호·WGC 2024 final 미확정(handoff 명시) |
| F 반증기록 | PASS | H4 기각 + H5 panic-sell 반대신호 정직 박제 |
| G effective-N | TIER structural_low | n≥4279이나 regime persistence·spurious로 validated 불가 |
| H 미해결 | PASS | 각 validation §미해결 박제 |
| **I 무결성** | PASS | 단일자산, CFTC 연속, 합성 0 |
| J 경제유의 | DEFERRED | factor id 단계 (lens 정성 허용) |
| K 다중검정 | PASS_disclosed | 8가설 + sub-test 공시, Bonferroni α/8 |
| L 통합PSD | NOTED_main | gold rate/dollar β 타 sleeve 중복계상 주의 |

**hard_fail_count = 2 (B, D — 둘 다 H8 한정).** H5·CFTC 단독으로는 hard-fail 0.

---

## tier 재판정 (G축)

- **H5**: structural_prior (TENTATIVE), validated_alpha=false ✓ 적정
- **CFTC**: untested_in_v2 ✓ 적정
- **H8**: 자체판정 SUPPORTED → ★**structural_low_confidence, sign-prior only** 로 강등. mechanism 위계·anytime-valid SUPPORTED 박제 금지.
- **H2** (간접 검증): STRONGLY SUPPORTED → ★**PARTIAL** 강등 (cointegration 부재 = 균형식 재구성 서사 unsupported, 잔차 drift 는 spurious 산물).
- 전체 trust_tier=`structural_prior_with_validated_sign` 라벨 자체는 유지 가능하나, **H2/H8 의 "validated_sign" 중 level-mechanism 부분은 spurious 라 sign 도 신뢰 격하.**

---

## ★gold 관계 spurious 여부 — 결론

**부분 spurious.**
- ★**H8/H2 의 level-on-level (ln_gold ~ real_rate level + ln_dollar level) = spurious regression** (3변수 모두 I(1), cointegration 부재, DW≈0). 여기서 도출한 e_level 발화·"+391% unexplained"·"LEVEL mechanism 우선"·"equilibrium re-formation" 은 모두 동일 인공물의 재서술. **hard-fail (B+D).**
- ★H5/H4/H1 등 **return/diff 단위** 분석은 정상 series → spurious 회피, 부호(real_rate NEG, dollar NEG) 도 이론 정합 (return betas: b_real -0.06, c_dollar -0.94). 이 부분은 건전.
- **직전 reit/bond_cash level 함정의 재발 패턴** — 동일 root cause (비정상 level 회귀). e-process 라는 정교한 포장이 spurious 를 가린 케이스.

---

## 판정 + 보강 요청 (방으로)

**verdict: 부분 (PARTIAL register).** H5 + CFTC + return-unit 분석(H1/H4/H6/H7)은 register 가능. ★단 **H8/H2 의 level-mechanism 결론은 다음 보강 전 register 차단**:

1. ★**H8 e_level 재정식화**: level 잔차가 아니라 **VECM error-correction term (cointegration 입증 후)** 또는 **차분 단위** 위에서 e-process 구성. cointegration 이 Johansen/EG 로 기각된 이상 "균형식 안정 귀무" framing 폐기.
2. ★**H2 "STRONGLY SUPPORTED" → "PARTIAL/TENTATIVE"** 강등 (자체 json `H2_supported=false` 와 정합화). "unexplained +391%" 는 spurious 회귀 잔차임을 명시.
3. ★**yaml**: H8 confidence_hook verdict_v2 SUPPORTED → TENTATIVE, H2 STRONGLY_SUPPORTED → PARTIAL. lens.report_relations / estimation_note 의 "dual e-process ordering level >> Δ-beta", "equilibrium re-formation" 박제 격하 (sign-only: "post-2022 traditional linear model 이탈, 방향 상방, mechanism 인과 미입증").
4. ★**D축 e-process 한계 격상**: martingale 가정 위반(비정상·자기상관)을 SUPPORTED 가 아닌 caveat-dominant 로.
5. H5/CFTC = 추가 보강 불요 (현 TENTATIVE/untested 라벨 정확).

**시스템 정합(§4)**: VECM/State-Space monitor 모듈 신설 계획(block 7 upgrade_new_module)은 **오히려 본 결함의 정답** — RegimeGlasso 정적 partial-corr 도, 현 spurious level 회귀도 아닌 *제대로 된 cointegration/ECM* 으로 구현해야 H2/H8 의도가 산다. 단 cointegration 이 데이터상 기각된 만큼 "γ error-correction 분해" 가 실제로 유의한지부터 모듈 내 재검증 필요 (다운그레이드 아니라 정합화).
