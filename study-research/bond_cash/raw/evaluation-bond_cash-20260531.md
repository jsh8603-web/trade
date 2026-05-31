# evaluation-bond_cash — 독립 12축 감사 (opus-1m, 2026-05-31)

> 평가자: independent audit subagent (opus-1m). self-audit 불신, raw parquet 재실행 + 실데이터 지문으로 직접 검증.
> SSOT: AUDIT-GUIDE.md §1·§2 / application: bond_cash/evaluation-axes.md §2·§3·§4.

---

## ★ OVERALL VERDICT (1줄)

**부분 (PARTIAL)** — 데이터·재현성·provenance 는 견고(합성 0, recompute 정확 일치)하나, ★CONFIRMED/Bonferroni-pass 의 다수가 **비정상(non-stationary) level-on-level 회귀의 spurious 산물**이며 regime-conditional 신호가 **in-sample 한정(walk-forward 미검증)** — 점추정 alpha 박제 불가, 전 sub-cluster **sign/direction prior 로 격하**.

- **hard-fail 코어 4 (B·C·D·I) 총건수**: **2** — (1) **D축 lookahead**: ACM_TP10 = NY Fed 재추정(revised) 시계열을 vintage 처리 없이 사용(전 7 sub-cluster 공통, 단 신호 자체가 spurious 라 영향 제한적). (2) **B축**: cash_tbill 의 6/15 Bonferroni-pass 가 비정상 회귀 t-stat 인플레 산물 → "validated" 주장 무효(숫자가 약한 게 아니라 *해석이 틀림*). 나머지 sub-cluster 는 B/C/I PASS, D는 ACM 공통이슈로 PARTIAL.
- **validated_alpha 판정 sub-cluster**: **0개** (전부 structural_prior_low_confidence). cash_tbill 도 spurious 로 격하.
- **합성 지문**: 전부 음성(real data). TLT 2020-03 COVID ±7.5% 일중 실재, MOVE/ACM 일별 실측, 결측·갭 정상.
- **recompute 일치**: tsy_long·cash_tbill 전 30 cell IC/t/p 표시정밀도까지 **정확 일치** → 위조·합성 0.

### 5개 위임 결정 판정 (각 1줄)

1. **sub-cluster tier 라벨**: 전 7 sub-cluster = **structural_prior_low_confidence**. validated_alpha 0개. (근거: ★CONFIRMED 신호가 비정상 level 회귀 artifact, differenced 시 소멸; cash_tbill 도 동일.)
2. **regime cell walk-forward OOS 정당성**: ⛔ **FAIL — 정당화 불가**. regime cell = 코드·md 모두 "in-sample classification" 자인. HYG MOVE_Z rate_up_vol_high (summary 헤드라인 IC=-0.151 Bonf-pass) 를 half-split 하면 IS=+0.077 / OOS=-0.331 — **부호가 반대로 뒤집힘**. regime-conditional 주장은 in-sample over-fit, walk-forward 재실행 의무.
3. **driver 공선 effective tests 정량**: 명목 105(또는 regime split 525, Bonf 분모 420). PCA 결과 **4 component = 96.4% 변동**(5번째 eigenvalue 0.18 = ACM↔T10Y2Y +0.813 붕괴). effective ≈ 4 driver-dim × ~1.5 nested-horizon × 7 asset ≈ **42~52** (명목의 절반). 방의 "effective << 105" 방향 맞음, 정량치는 ~50.
4. **BAA10Y proxy 의 BAMLH0A0HYM2 대체 정당성**: ✅ **정당**. BAMLH0A0HYM2 FRED 가용 2023-05-30~(rows=786, ICE 라이센스) 실측 확인. BAA10Y 1986~(rows=10101) 대체 = DA eq_us_defensive H3 검증 경로 재사용, provenance 박제. credit-spread Δ proxy 로 합당(단 BAA=IG 등급, HY OAS 와 등급 mismatch 는 H축에 명시 권장).
5. **Bonferroni α/420 vs FDR**: α/420 = **over-conservative**(effective ~50 인데 420 분모). 그럼에도 cash_tbill·일부 ACM 가 통과한 건 spurious 비정상 회귀 t-인플레 탓 — **Bonferroni 강화가 답이 아니라 stationary 변환(차분) + block-bootstrap + walk-forward 가 답**. 권고: **BH-FDR(q=0.10) on effective ~50 tests** + 비정상 regressor 차분 의무.

---

## 핵심 발견 — 비정상 회귀 spurious 진단 (감사관 독립 재실행)

> raw parquet 직접 로드, phase5_validation.py 파이프라인 복제. 모든 수치 재현 일치 후 추가 검정.

**(a) 강한 driver 2종이 비정상(unit-root)**:
- T10Y2Y: ADF p=0.553, AR(1)=0.9991
- ACM_TP10: ADF p=0.257, AR(1)=0.9985
→ level 회귀는 spurious regression 위험 직격.

**(b) 차분(stationary) 변환 시 신호 소멸**:
- cash_tbill T10Y2Y fwd60: level IC = **-0.735** → d20 차분 IC = **+0.033** (p=0.025, 부호 반대·magnitude 소멸)
- tsy_long ACM_TP10 fwd60: level IC = **+0.245** → d20 차분 IC = **+0.024** (p=0.105, 비유의)
→ ★CONFIRMED 강력 라벨의 실체 = level co-trend(커브·단기금리 사이클 동조), 예측 alpha 아님.

**(c) HAC lag 과소 → t-stat 인플레**:
- cash_tbill T10Y2Y fwd60: lag=60(방 설정) t=-10.4 / lag=9 t=-25.2 / lag=1000(18년 persistent+overlap 적정) t=-3.98.
→ verdict 의 t-stat 절대값은 lag 선택에 ~2.6배 민감. 60-day overlap nested window 에 lag=f(=60) 는 부족.

**(d) sub-period 불안정**:
- cash_tbill T10Y2Y fwd60: 1st-half IC=-0.219 / 2nd-half IC=-0.773 (불안정, level-dependent)
- HYG regime cell: IS=+0.077 / OOS=-0.331 (부호 반전)

→ small-N 아님(n=4580)이나 **유효 독립표본은 비정상·중첩으로 훨씬 작음**. 점추정 covariance/IC prior 박제 ⛔. sign/direction prior + CI 넓음 라벨만 허용.

---

## §4 양식 — sub-cluster 7개 평가 yaml

```yaml
evaluation_by: independent-audit-subagent-opus1m
date: 2026-05-31
evaluator_model: opus-1m
axes_source:
  primary: D:/projects/Inv/study-research/AUDIT-GUIDE.md
  application: D:/projects/Inv/study-research/bond_cash/evaluation-axes.md
recompute_method: "phase5_validation.py 파이프라인 parquet 직접 복제. tsy_long/cash_tbill 30 cell 정확 일치 (B-axis provenance PASS). 추가: ADF stationarity + 차분 robustness + half-split OOS + PCA Meff."

sub_clusters:
  - sub_cluster: tsy_long      # TLT, dur~17
    verdict: 부분
    provenance: {raw_scripts_rerun: true, synthetic_fingerprint_check: true, yaml_to_raw_traceable: true}
    axes_12:
      A: PASS        # Fabozzi return 분해 실재 정독, convexity/carry 원리 본인 정리
      B: PARTIAL     # 실데이터 정확 재현, but ★CONFIRMED(ACM/T10Y2Y) = 비정상 level artifact, 차분 시 소멸. Rank-IC>0.03 명목 충족하나 stationary 검증 미통과
      C: PARTIAL     # summary verdict count = 재현 일치. but yaml 에 base_weight/corr_prior 점추정 아직 미박제(phase5=pending), flag affects_indicator/edge 미작성
      D: FAIL        # ACM_TP10 = NY Fed 재추정(revised) 시계열, vintage 처리 없음 (lookahead). FRED first_release_default=true 는 OK
      E: PASS        # MOVE=ICE BofA / ACM=NY Fed Adrian-Crump-Moench / Kim-Wright cross-verify(R2). 환각 0. (★감사 spec 의 "MOVE=CBOE" 오류를 방은 ICE 로 올바로 식별)
      F: PASS        # ★REJECTED 3건 기록(MOVE_Z fwd20 등). 기각 0 아님
      G: PASS        # n=4580 명시, regime cell N(999~1405) 명시, tier 보수화 요청
      H: PASS        # driver 공선·BAA proxy·ACM ffill·regime in-sample·거래비용 미해결 솔직 기재
      I: PASS        # TLT inception 2002-07~, 중도삭제 0, ETF 생존편향 없음
      J: PARTIAL     # 거래비용(TLT 0.02%) 언급만, 차감 후 알파 미계산 (alpha 미주장이라 hard 아님)
      L: PARTIAL     # driver 공선 보고됨, but 통합 PSD/공통인자 1회계상 = Phase 7 미수행
    hard_fail_count: 1   # D (B는 PARTIAL)
    tier: structural_prior_low_confidence
    system_fit: {current_skeleton_fits: false, pipeline_upgrade_needed: true,
      upgrade_plan: "RegimeGlasso 정적 partial-corr 로는 비정상 level co-trend·차분 신호소멸을 표현 못함. ★다운그레이드 금지. (1) driver stationary 변환층(차분/z-score) 의무화 (2) walk-forward regime classifier 모듈 신설 (3) ACM vintage(또는 Kim-Wright real-time) 대체. sign-prior 만 corr_prior 에 주입, magnitude 박제 금지"}
    remediation:
      - "D: ACM term premium vintage/real-time(Kim-Wright) 처리 또는 'revised series, lookahead 잔존' 명시 후 신뢰도 격하"
      - "B: 비정상 driver(T10Y2Y/ACM) 차분 후 재검정 — 차분 IC 비유의면 verdict TENTATIVE 로 통일"
      - "C: yaml base_weight/corr_prior 박제 시 sign-only, flag affects_indicator/affects_edge 작성"

  - sub_cluster: tsy_mid       # IEF, dur~8
    verdict: 부분
    provenance: {raw_scripts_rerun: true, synthetic_fingerprint_check: true, yaml_to_raw_traceable: true}
    axes_12: {A: PASS, B: PARTIAL, C: PARTIAL, D: FAIL, E: PASS, F: PASS, G: PASS, H: PASS, I: PASS, J: PARTIAL, L: PARTIAL}
    hard_fail_count: 1
    tier: structural_prior_low_confidence
    system_fit: {current_skeleton_fits: false, pipeline_upgrade_needed: true, upgrade_plan: "tsy_long 동일 — stationary 변환층 + walk-forward"}
    remediation: ["D ACM vintage", "B 비정상 driver 차분 재검정"]

  - sub_cluster: tsy_short     # SHY, dur~2
    verdict: 부분
    provenance: {raw_scripts_rerun: true, synthetic_fingerprint_check: true, yaml_to_raw_traceable: true}
    axes_12: {A: PASS, B: PARTIAL, C: PARTIAL, D: FAIL, E: PASS, F: PASS, G: PASS, H: PASS, I: PASS, J: PARTIAL, L: PARTIAL}
    hard_fail_count: 1
    tier: structural_prior_low_confidence
    system_fit: {current_skeleton_fits: false, pipeline_upgrade_needed: true, upgrade_plan: "동일. SHY 는 verdict 약(★CONFIRMED 0) — sign-prior 도 약하게"}
    remediation: ["D ACM vintage", "B: 전 verdict 이미 약함, TENTATIVE 통일 권장"]

  - sub_cluster: ig_credit     # LQD, dur~8, A-/BBB+
    verdict: 부분
    provenance: {raw_scripts_rerun: true, synthetic_fingerprint_check: true, yaml_to_raw_traceable: true}
    axes_12: {A: PASS, B: PARTIAL, C: PARTIAL, D: FAIL, E: PASS, F: PASS, G: PASS, H: PASS, I: PASS, J: PARTIAL, L: PARTIAL}
    hard_fail_count: 1
    tier: structural_prior_low_confidence
    system_fit: {current_skeleton_fits: false, pipeline_upgrade_needed: true, upgrade_plan: "동일 + BAA10Y_chg20 credit Δ 와 IG ETF 등급 정합(LQD=A-/BBB+ vs BAA) 명시"}
    remediation: ["D ACM vintage", "B 비정상 차분 재검정", "L credit driver 와 macro/eq_defensive 중복계상 점검(통합)"]

  - sub_cluster: hy_credit     # HYG, dur~4, B+/BB
    verdict: 부분
    provenance: {raw_scripts_rerun: true, synthetic_fingerprint_check: true, yaml_to_raw_traceable: true}
    axes_12:
      A: PASS
      B: PARTIAL   # ★raw DGS10_chg20 fwd20 IC=-0.147 t=-2.18 = 유일 stationary(차분 driver) 신호 가능성, but Bonf 미통과
      C: FAIL      # summary.yaml regime_conditional_findings 가 in-sample IC(-0.151,+0.194)를 Bonferroni-pass=true 로 박제 → walk-forward 미검증을 validated 인 양 추적. half-split 시 부호반전(IS+0.077/OOS-0.331). yaml→raw 추적 시 OOS 정당성 결락 = 추적성 위반
      D: FAIL      # ACM vintage + BAMLH0A0HYM2 대신 BAA10Y(IG등급)로 HY credit 대리 = 등급 mismatch(H엔 명시되나 driver 정합 약)
      E: PASS
      F: PASS
      G: PARTIAL   # regime cell n=1036 명시하나 effective-N(자기상관·in-sample) 보수화 부족
      H: PASS
      I: PASS       # HYG inception 2007-04~, 생존편향 없음. BAMLH0A0HYM2 라이센스 제한 정직 기재
      J: PARTIAL    # HYG 왕복 0.08%+ 언급, 차감 미계산
      L: PARTIAL
    hard_fail_count: 2   # C + D
    tier: structural_prior_low_confidence
    system_fit: {current_skeleton_fits: false, pipeline_upgrade_needed: true,
      upgrade_plan: "regime-conditional MOVE 사이징 = walk-forward classifier + expanding-window OOS 모듈 신설 후에만 corr_prior 진입. ★in-sample regime IC 를 weight 로 박제 금지(다운그레이드 아니라 검증 강화)"}
    remediation:
      - "C: summary.yaml regime_conditional_findings 의 bonferroni_pass:true 를 'in-sample, walk-forward pending' 으로 정정. IC 점추정 박제 제거"
      - "regime cell walk-forward OOS 재실행 의무 — half-split 부호반전(IS+0.08/OOS-0.33) 데이터 첨부"
      - "D: HY credit driver = BAA10Y(IG) proxy 등급 mismatch. BAMLH0A0HYM2 2023-05~ short-sample 병기 또는 등급조정 명시"

  - sub_cluster: cash_tbill    # BIL, dur~0.1
    verdict: 부분
    provenance: {raw_scripts_rerun: true, synthetic_fingerprint_check: true, yaml_to_raw_traceable: true}
    axes_12:
      A: PASS
      B: FAIL      # ★6/15 Bonferroni-pass 의 핵심(T10Y2Y IC=-0.74 t=-25, ACM IC=-0.32)이 비정상 level-on-level spurious. 차분 시 IC -0.735→+0.033 소멸, lag=1000 시 t -25→-4, half 불안정(-0.22/-0.77). "validated" 해석 무효(숫자 자체는 재현되나 해석이 틀림)
      C: PARTIAL   # summary.yaml expected_tier 가 cash_tbill='validated_alpha' 기대 박제 → 본 감사로 기각. 추적 시 spurious 미인지
      D: FAIL      # ACM vintage
      E: PASS
      F: PASS
      G: PARTIAL
      H: PASS
      I: PASS       # BIL inception 2007-05~
      J: PASS       # cash sleeve 거래비용 거의 0 (정당)
      L: PARTIAL
    hard_fail_count: 2   # B + D
    tier: structural_prior_low_confidence   # ★ NOT validated_alpha (spurious 격하)
    system_fit: {current_skeleton_fits: false, pipeline_upgrade_needed: true,
      upgrade_plan: "cash carry/단기금리 신호는 stationary 변환(d-T10Y2Y, level 금리) 으로 재정의 후에만 weight. level co-trend 을 alpha 로 박제 금지"}
    remediation:
      - "B: T10Y2Y/ACM_TP10 level 회귀 = spurious. 차분 또는 cointegration(ECM) 으로 재검정. 차분 IC 비유의 → cash sleeve sign-prior(단기금리 carry) 만 유지"
      - "C: expected_tier 'validated_alpha' → structural_prior 정정. Bonferroni 6/15 = 비정상 artifact 라 박제"

  - sub_cluster: tips          # TIP, dur~7, AAA(TIPS)
    verdict: 부분
    provenance: {raw_scripts_rerun: true, synthetic_fingerprint_check: true, yaml_to_raw_traceable: true}
    axes_12: {A: PASS, B: PARTIAL, C: PARTIAL, D: FAIL, E: PASS, F: PASS, G: PASS, H: PARTIAL, I: PASS, J: PARTIAL, L: PARTIAL}
    hard_fail_count: 1   # D
    tier: structural_prior_low_confidence
    system_fit: {current_skeleton_fits: false, pipeline_upgrade_needed: true,
      upgrade_plan: "TIPS 는 real-rate(DFII10) driver 부재가 H 결함 — breakeven/실질금리 driver 추가. stationary 변환 동일"}
    remediation:
      - "D ACM vintage"
      - "H: TIPS sub-cluster 인데 DFII10(실질금리)·breakeven driver 미포함 = inflation-linked 핵심 driver 결락. driver set 보강 권고"
      - "B 비정상 driver 차분 재검정"

summary:
  total_sub_clusters: 7
  verdict_counts: {충실: 0, 부분: 7, 불충분: 0}
  hard_fail_sub_clusters: [hy_credit, cash_tbill]   # hard_fail_count>=2 (코어 2축 위반)
  hard_fail_axis_breakdown:
    D_acm_vintage_lookahead: [tsy_long, tsy_mid, tsy_short, ig_credit, hy_credit, cash_tbill, tips]  # 전체 공통 1축
    B_spurious_nonstationary: [cash_tbill]   # validated 주장 무효화
    C_oos_traceability: [hy_credit]          # in-sample 을 Bonf-pass 로 박제
  validated_alpha_sub_clusters: []           # ★ 0개 — 전부 structural_prior_low_confidence
  effective_tests_estimate: "~42-52 (PCA 4 driver-component × ~1.5 nested-horizon × 7 asset), 명목 105 / Bonf 분모 420 은 over-conservative. BH-FDR q=0.10 권고"
  overall_recommendation: "N sub-cluster 재dispatch(부분) + 파이프라인 업그레이드 필요. 전 7 sub-cluster 부분판정 — 통합(Phase 7) 진입 전 (1) 비정상 driver stationary 변환 의무 (2) regime cell walk-forward OOS 재실행 (3) ACM vintage 처리 (4) yaml=sign-prior only(magnitude 박제 금지). 합성 0·재현 정확이라 폐기 아닌 보강·재검정 경로."
```

---

## §4 시스템 정합 (다운그레이드 금지 원칙)

- 방의 분석 렌즈(regime-conditional driver IC, ACM term premium 분해, MOVE vol-regime 사이징)는 **현 RegimeGlasso 정적 partial-corr 골격으로 표현 불가** — 비정상 level co-trend·walk-forward regime·term-premium 분해 모두 정적 상관으로 다운그레이드 시 의미 손실.
- ⛔ **다운그레이드 금지**. 업그레이드 후보:
  1. **stationary 변환층**(차분/z-score)을 driver 전처리에 의무화 — spurious level 회귀 차단.
  2. **walk-forward regime classifier 모듈**(expanding window) — in-sample regime IC 의 over-fit 차단.
  3. **ACM vintage / Kim-Wright real-time term premium** 대체 — D축 lookahead 해소.
  4. **sign-prior corr_prior 주입**(magnitude 박제 금지) — small-N/비정상 rigor 준수.
- 이 업그레이드는 추가-only·opt-in·SACRED 불변. 통합(Phase 7) 전 progress 에 기록 권고.

---

## H/E축 보충 메모

- **E축 환각 0**: theory-notes 가 Fabozzi return 3-항 분해(duration/convexity/carry) 실재 정독, consult R1/R2 가 ICE BofA MOVE(FRED rid=209)·NY Fed ACM(Adrian-Crump-Moench)·Kim-Wright cross-verify 1차 source. ★감사 spec(evaluation-axes §2)의 "MOVE methodology CBOE" = **오류**(MOVE=ICE BofA, CBOE 는 VIX). 방은 ICE 로 올바로 식별 — 방이 spec 오류를 안 따라감(가점).
- **I축**: BAMLH0A0HYM2 FRED 가용 2023-05-30~(rows=786, ICE 라이센스) 실측 확인 — handoff anchor "1996~ 가용" 류 위조 없음. BAA10Y 1986~ proxy 정당(단 hy_credit 등급 mismatch H 명시 권고).
- **D축 핵심**: FRED 9 series 모두 first_release_default=true(vintage OK). ACM 만 NY Fed full-history 재추정 series — 모델 재적합되는 series 라 published=revised. 신호가 spurious 라 실무 영향은 제한적이나 원칙상 hard.
