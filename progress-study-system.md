---
tags: [type/progress, domain/inv, phase/study-system]
date: 2026-05-30
note: 종목 스터디 시스템 진행. 계획=plan-study-system.md, 통일 지시서=STUDY-KIT.md. SSOT ckpt=progress-assumption-v2.md(R15 연장).
---

# progress-study-system

> 인계: [handoff-study-system-20260530.md](./handoff-study-system-20260530.md) (압축 전 상세 인계 — flag 3경로 U1/U2/U3·감사 3방·자문 3R·다음작업 우선순위)
> ★**재부팅 복구 인계 (2026-06-01, 단일세션 순차 완결판)**: [handoff-reboot-recovery-20260601.md](./handoff-reboot-recovery-20260601.md) — 각 자산군 12축 verdict+commit+잔여+사용자 게이트 3결정+12축 정의+yaml 7블록+flag 3경로+local-db 별도트랙 전부 박제. **재부팅 후 이 파일부터 Read**.
> 재현 SOP: [STUDY-ORCHESTRATION.md](./STUDY-ORCHESTRATION.md) (멀티세션 스폰→스터디→감사→통합 + 섹터 메타 + 통합 불변식. Inv/CLAUDE.md 트리거: `자산 스터디 wf`)

## §진입 스냅샷 (v2 — 사용자 framing 정정, 자율주행 재진입)
| 항목 | 내용 |
|---|---|
| ★사용자 정정 | v1 은 방들이 자문을 그대로 코드화하고 끝냈다(전문성 형성 과정 생략). **다시 한다(담당 종목 유지)** |
| v2 흐름 | 1) 자문 다회 라운드로 이론 수집·검증 방향 + 가설 초안(완전성↑) → **승인 게이트** 2) 이론 학습 3) 실데이터 시계열 검증→lens·상관계수 코드화. **raw 강제** |
| 승인 게이트 | 작업 전 1단계 방향성(direction.md) 마치고 main 에 보고·승인(사용자 "너에게 말해 승인"=main). 승인 전 2단계 금지 |
| 재사용 | v1 골격 G1~G6 + production wiring + 가드 13/13 = 그대로 재사용(인프라). 바뀌는 건 방 스터디 프로세스 |
| 세션 | 10 psmux 방(담당 study_id 유지). v1 산출은 raw 참고용 보존(폐기 X) |
| SACRED | DRY_RUN/execute_trade 불변, opt-in off 기본. 실거래 flip·README 교체 = 사용자 게이트 |

## ★자율주행 잔여 task 큐 (2026-05-31 핸드오프 통합 재개 — 자율주행 flag ON)
> 모델: main(btn-Codlearn opus) 오케스트레이터. 순서 무관, 각 = study→12축 audit(별도 opus subagent)→yaml/ledger 반영 완결.
- [x] **세션 핸드오프 통합**: stale 7방 인계→clear→재주입(+12축 원칙) = button(macro)/jsh86(gold)/profile(crypto)/GCP(reit)/powerbi(bond_cash)/DA/common-task. diary·excel·jpdf=종료대상(미오케). Inv=보호.
- [x] **macro B그룹**: study→12축 audit(Hard-fail 0)→verdict relay→macro yaml 반영+commit **b89f313** ✅ (B(b) rate분리 validated / B(c) credit β structural w≤0.25 / B(a) dollar·oil REJECTED 보류). 완료.
- [x] **commodity NOAA ONI(ENSO)**: study→독립 12축 audit(spurious 아님 확정·Hard-fail 0·predictive 라벨/PIT/effN 한계)→validation 격하+ledger 이연→채택(structural_low_confidence)+promo-log K+commit **da14...** ✅. 보강3(PIT lag·predictive분해·effN) 후 승격 후보. 완료.
- [~] **DA eq_us_defensive**: v3 격하 commit **eca172d** ✅. main 결정 전달완(P3 sleeve 분리 APPROVED=DEFENSIVE_PURE/FINANCIALS §1.6 / P1 collector=HY OAS full·VIX3M·DFII10·yield_curve 자체 fetch / EDGAR·FFIEC만 main 빌드→H4/H5/H10/H11 보류). ⏳ DA sleeve분리+HY OAS H3재검증 study 진행 → STUDY DONE 시 main audit.
- [~] **common-task eq_us_cyclical**: 산업 δ matrix + 시나리오A + 5 합의건 판정 + yaml R15 반영(8ddb50e) ✅. **main Verify stage 완료** → ★verdict PARTIAL = δ_regime magnitude 전멸(G2 14/16 CI cross-0, heuristic CI 10-30배 underest / K Bonferroni 0/16 / G4 LOEO OOS R² 음수 = descriptive not predictive). verdict 전달완 = δ_regime ±0.15 박제 금지→sign-only prior(magnitude freeze)·structural_prior_low_confidence / 산업 자체 vol / live regime 분류기 OOS 선행. promo-log K 기록. ⏳ common 격하 반영+'YAML v4 DONE' 대기.
- [x] **bond_cash**: collector P0 해소(self-fetch) → Phase5 7 sub-cluster×105 test STUDY DONE(ab0faac) → 12축 audit a75ab5a2 **verdict = PARTIAL**(데이터·재현성 견고·합성0, 단 Bonferroni-pass 다수가 비정상 level-on-level spurious + regime in-sample 한정 → validated_alpha 0, 전 7개 structural_prior_low_confidence). Hard-fail 3축(D=ACM revised vintage / B=cash_tbill spurious 차분 시 IC 소멸 / C=hy_credit OOS 부호반전). 해법=stationary 차분+block-bootstrap+walk-forward, BH-FDR q=0.10 on effective≈50. → **YAML v4 DONE(commit e17d51fd, 격하 5건 반영)** ✅ 사이클 완결. promo-log K(spurious 함정+ACM vintage) 자산화. ⏳ Phase7 통합 yaml=walk-forward classifier + Kim-Wright term premium 대체 후 후속.
- [x] **reit**: AMT fetch 4h20m hang → Escape 복구 → r4-carry-verify 5건 STUDY DONE → 12축 audit af63f996 **verdict = ★충실 PASS, hard-fail 0 (첫 PASS 사이클)**. §5 r=0.746=spurious 아님 검증완(log-return 차분, LEVEL 0.927 비정상이나 RETURN 0.746 NW t=4.14 정상·OOS 유지). 환각 2건 catch 정확. → **YAML v3 DONE** ✅(study_session.yaml v3, v2.bak): references_r4_verified 신설(Ling-Naranjo DOI 6/6+AMT/CCI primary 박제, ★Beracha 재환각 제거), block5 H6_reit_stock_integration_regime structural_strong 공분산 prior+L축 1회 계상 의무, block6 R5 후속 5건(BAA-AAA n확장·CPI PIT·AMT 8-K·일별 CAR), main_audit verdict 박제. 사이클 완전 완결.
- [~] **gold**: STUDY DONE(CFTC mm_gold n=157·H5 TENTATIVE·H8 dual e-process·yaml v2·small-N FREEZE) → 12축 audit a55fa51b **verdict = PARTIAL**(Hard-fail 2 B+D H8한정 / H5·CFTC 0). ★H8 SUPPORTED 기각: τ change-point 정확하나 e_level ln_gold~real_rate+ln_dollar = level-on-level spurious(3변수 I(1)·잔차 ADF p=0.845 coint부재·DW 0.002), e_level=inf=비정상 OOS 외삽. ★H2 yaml "STRONGLY SUPPORTED"=over-claim(방 자체 json coint_support=false 모순). **spurious 함정 3번째**(cash_tbill→gold). H5/H4/H1 return 단위 건전. verdict relay 완 → **YAML v3 DONE** ✅(H8 SUPPORTED 취소→coint 기각·재정식화 / H2 STRONGLY→PARTIAL / block7 VECM 무조건→coint 입증 후 조건부 보류 / validation·checklist 격하 박제 / ★rule 자산화=empirical-claim §1.7 신설[ADF/coint 사전검정 4단계+return/diff 강제+self-audit B축 sub-check 4종]+promo-log ERROR). H5/H4/H1/H3/H6/H7/CFTC return 단위 건전 유지. 사이클 완결. 차단=sys_priors G6+collector 큐 6(한도 후).
- [~] **crypto**: P0 unblock ack → direct fetch(CoinMetrics5+FRED3+yfinance3+PyTrends+DefiLlama) H7-H12 검증 진행중 → self-audit 후 STUDY DONE 예정.
- [ ] **common-task**: yaml v4 격하 반영 재개(hang 복구 후) → 'YAML v4 DONE' 대기.
- ⚠️ **주간 한도 97%**(Jun5 4am reset) — audit subagent 이 세션 3건(bond_cash 143k+reit 103k+gold) 소모. 절약 모드(추가 study/subagent 최소), 도달 시 자연 중단. 사용자 중단 지시 시 hold.
- [ ] **다음 commodity 이연 지표**: cushing_utilization(EIA)·stock_to_use(USDA)·roll_yield(CME term) 등 collector 빌드→study.

## 자율주행 실행 큐 v2 (사용자 정정 — 전문 애널리스트 프로세스)
- [x] **K. STUDY-KIT v2 개정**(§2 전면 교체: 2-1 자문다회→승인게이트 / 2-2 이론 / 2-3 실데이터 검증→코드화 + raw 강제. §5 폴더·§0 승인게이트 반영)
- [x] **L. study_register raw 완비 게이트**(`_check_raw_completeness`: direction.md+round-*+theory-notes+validation-* 검사, 없으면 거부. v1 yaml REJECT 확인. self-test/가드 무회귀)
- [x] **M. 10방 재지시 전송**(v2 2-1부터, 담당 유지, 자문 경합 시 폴백·동시 자제)
- [ ] **N. 1단계 방향성 수집 → main 승인 게이트**(방별 direction.md 검토: ①②③ 충족·가설 반증가능·다회 수렴)
- [ ] **O. 승인 방 → 2단계 이론학습**(theory-notes.md 강제)
- [ ] **P. 3단계 실데이터 시계열 검증→코드화**(validation-*.md 강제 + yaml)
- [ ] **Q. raw 완비 검증 → production wiring 재통합**(G6 register + 가드 재실행)
- [ ] **R. 최종 보고**(자산군별 검증 근거 + production 상태 + 커밋 대기)

## 파이프라인 업그레이드 큐 (flag→lens·corr 루프 완성 — 사용자 지시, seed→라이브 진화)
- [x] **U1. flag→lens 자동 갱신**(★main 직접 구현 — 순수 파이프라인 코드, 방 입력 불요) ✅ self-test PASS
  - 회귀 확인: confidence_note=None byte-identical + judge.py 본체 미변경(lens_prompt 경로 재사용) = 직교 무회귀
  - `lens_store.render(scope, regime_id, confidence=None)`: confidence 받으면 estimation_note 에 동적
    신뢰도 라벨 주입("가설 신뢰도 N(confirm M/reject K) → 저신뢰=보수 해석"). None 이면 기존과 byte-identical.
  - `study_register.prepare_judge_call`: flag.confidence_by_indicator 를 render 에 전달 → qwen(agent 판단)에
    갱신 lens 주입. judge.py:221 lens_prompt 경로 재사용(down-only 보존).
  - 무회귀 self-test: confidence=None 동일 출력 + confidence 주입 시 텍스트 변화 입증.
- [x] **U2. flag→corr_prior shrinkage**(★main 기본 구현 + 방 양식 입력) ✅ self-test PASS(누적0 무변동 / reject A-B 0.6→0.3 / affects_edge 직접·A-C 불변 / node fallback / confirm 강화 clip)
  - 회귀 확인: 누적 0 가설 byte-identical + base 미변경(copy) + RegimeGlasso 본체 미변경(prior 주입 인자만) = 직교 무회귀
  - `flag_router.corr_prior_shrink(edges, base_corr_prior, ...)`: 저신뢰 가설 edge 의 prior 를 1 쪽(독립)
    으로 약화. edge conf = 블록5 affects_edge 직접(방 입력) OR node conf 결합 근사(fallback).
  - `RegimeGlasso.fit(corr_prior=flag_adjusted)` 주입(conditional_correlation.eb_shrink 경로).
  - ★방 입력 필요(정밀): 블록5 confidence_hooks 에 `affects_edge:[node_a,node_b]` → 양식 배포 + 감사기준
    C축 추가(완료). 방 미입력 시 node conf 결합 근사로 graceful.
  - study_loader ConfidenceHook 에 `affects_edge` 필드 추가(default [], 무회귀).
- [x] **U3. corr_prior 레벨 분리**(★1순위 correctness — 자문 3R 수렴: reflexive loop 차단) ✅ self-test PASS(118 passed 회귀0). 보관=[CONSULT-DECISIONS-layering-20260530.md](./CONSULT-DECISIONS-layering-20260530.md)
  - ★문제: U2 `corr_prior_shrink` 가 단일 corr_prior 약화 = 종목 flag→macro Σ 누수(강세장 종목 과신→거시 "리스크 극저" 오판→하락 직전 최대 위험예산). reflexive pro-cyclical.
  - 처방: `_macro`(sleeve×sleeve dense)/`_micro`(sleeve block-diagonal) 별개 객체·인덱스. 종목 flag=_micro만. cross-sleeve hypothesis edge=런타임 가드 거부. single-writer(_macro writer=실현 cross-sleeve 수익률 EWMA + regime 전이만, belief 인자 X).
  - ✅구현(level 파라미터 가드 방식): `corr_prior_shrink(..., level='micro'|'macro')` — level≠micro 면 belief 차단 no-op(`flag_router.py:197`). `study_register.prepare_corr_prior(study_id, base, series)` facade 신규 — study scope→level 자동결정(`_corr_level_of`: macro/bond=macro 차단, equity/reit/commodity/gold/crypto=micro 허용). opt-in off=base 그대로(무회귀). self-test case6(macro=belief차단 no-op / micro직접=flag반영 대비군 / 매핑 / off무회귀).
  - ⏳잔여(U3b, register 통합 시점): _macro/_micro **별개 인덱스 객체** 완전분리 + cross-sleeve hypothesis edge **ValueError 런타임 가드**. 현 level 가드로 belief→macro **누수는 이미 차단**(핵심 correctness 충족), 별개 객체는 더 강한 isolation 형태로 register L축 점검과 동반.
  - ⛔구조만 분리, 파라미터 freeze. flag 3경로 = live baseline 전 shadow/log-only(실제 개입 off, INV_R15_WEIGHTS default-off 유지).
- [ ] **U4. Beta regime-tag + soft gate stub**(후순위 — 키잉 구조만, 파라미터 freeze)
  - FlagAccumulator → regime-keyed Beta(belief-weighted soft update + pooled shrinkage fallback, n→0=pooled). regime 식별=belief b(t).
  - regime_to_weights gate = floor/ceiling+deadband soft 확인(이미 BL confidence-weighted). 거시 consensus=직교 2nd regime view 1개(불일치 신호용) 후보.
  - ★자문 과설계 경고: robustness feature(deadband/clamp/shrinkage/fallback)만 지금, optimization/adaptation(튜닝 rate·학습 threshold·dynamic path)은 freeze.

## 거시-종목 cross-correlation 분석 (멀티세션 협업 — 사용자 지시 2026-05-30)
> 목적: 거시 이벤트/지표와 각 종목·종목 지표의 연관성(상관계수)을 실데이터로 측정 → 거시 판단에 가치있는 것을 거시 레이어(MacroView consensus regime)에 추가. cross-sleeve factor 베타(rate/dollar/oil/credit) 실증 근거 + 직교 2nd regime view 후보(U4 거시 consensus 연결). ★단 reflexive loop 가드(belief→_macro 차단, U3) + factor_implied 공통팩터 1회 계상(L축) 불변식 유지.
- [ ] **M1. 거시 이벤트·지표 요약 산출**: 거시 세션(btn-button)에 "기간별 주요 거시 이벤트 timeline + 거시 지표 요약"(regime/이벤트별 macro indicator 값·전환점) 요청. 산출 = 모든 세션 배포용 공통 입력(공통 기준선 통일 → 세션별 상관 비교 가능).
- [ ] **M2. 요약 전 세션 배포**: M1 산출을 종목 세션(eq_us_cyclical·eq_intl·commodity·gold·reit·bond_cash·crypto·eq_kr) 전체에 psmux 배포.
- [ ] **M3. 종목별 거시 연관성 분석**: 각 세션이 자기 종목 & 종목에서 보는 지표들이 거시 이벤트/지표와 갖는 연관성(상관계수·lead-lag·partial corr) 실데이터 분석. PIT·OOS·합성금지(AUDIT-GUIDE 12축 준용), 상관 임계(OOS|corr|·t-stat) 명시.
- [x] **M4. main 수집·거시 레이어 보강** (★자문 3R 수렴 2026-05-30 → 범위 M4/M5 분할, M4 구현 완료). 결정 SSOT=[CONSULT-DECISIONS-M4-factor-integration-20260530.md](./CONSULT-DECISIONS-M4-factor-integration-20260530.md). 검증 SSOT=[m4-collection.md](./study-research/macro/m4-collection.md)(5/6 verdict).
  - **M4 범위**(현 단계, opt-in/off-path byte-identical): (a) `core/study/factor_betas_seed.py` — 셀=(β̂,SE,t,n,Bonferroni,verdict-tier), James-Stein `w=τ²/(τ²+SE²)` + verdict 매핑(validated=w그대로/structural=w≤0.2-0.3캡/reject=pool제외·b=β_pool·w=0) + idio conservation `d=max(σ²−bᵀΛb, κσ²)`. (b) Λ 추정(Δbp/Δlog, ADF+KPSS, EWMA+stress floor, Higham PSD). (c) shadow validation(bias-stat[0.9,1.1]+eigenvector cosine>0.9, 로깅만 격리). ⛔shadow on/off diff=0 회귀박제.
  - **M5 범위**(후속, opt-in wiring): risk gate(deadband+clamp down-only)에 cross-sleeve cov 연결. ⛔BL prior cov 누수 금지(Π=δΣw view 환류=이중계상). static 장기 Λ는 BL용 별도.
  - **two-layer 분업**: dollar=모멘트당 1회(방향=Layer A belief 1차 / 동조위험=risk gate cov 2차 / cov→view 단방향 금지 / Layer B 종목매매 dollar 재진입 금지).
  - ★선행근거(btn-button M1 factor 분석, 2026-05-30): ①주식 dollar 채널 **국면조건부 전이 실증**(rate-up 국면 loading 약 2배). ②named factor caveat — rate/dollar/oil은 **cross-sleeve(asset-class 간)만 유효**, within-equity 는 못 잡음(equity market factor 소관). ③factor_implied_cross_cov 전 regime PD ✅. → **L축(공통팩터 cross-sleeve 1회계상) 실측 뒷받침**.
  - M3 검증 5/6: gold 충실 / eq_us_cyclical 충실 A− / reit 충실 중신뢰 / commodity 부분충실 / eq_intl 부분충실 B−(EM-idio·rate증폭 REJECT). eq_us_defensive=btn-DA 작업중(seed에 pooled-prior+hold).
  - ✅**M4 구현 완료**(2026-05-30): `core/study/factor_betas_seed.py`(James-Stein 수축+verdict tier 매핑+idio conservation, self-test 6/6 PASS) + `factor_cov_estimate.py`(Δbp/Δlog 변환+ADF/KPSS+EWMA+stress corr floor+Higham PSD, self-test 5/5) + `factor_shadow.py`(bias-stat[0.9,1.1]+eigenvector cosine>0.9+순수함수 격리, self-test 4/4). study 파이프 13/13 무회귀(신규 3모듈 production 미연결=off-path byte-identical). 결정 SSOT=CONSULT-DECISIONS-M4-factor-integration-20260530.md. README §종목 스터디 시스템 업데이트.
  - ⏳잔여: ①eq_us_defensive M3 검증=**불충실 Tier3**(H3 데이터 커버리지 위조급·dollar regime-switch 비유의)→seed HOLD 유지(교체 불가) ②M5=risk gate wiring ③Λ 실데이터 fetch로 shadow OOS 검증.
- [~] **M5. risk gate wiring + factor 확장 Phase A**: ①cross-sleeve cov(B·Λ·Bᵀ) risk gate opt-in 연결: ✅**wiring helper 완료**(2026-05-30, `risk_gate.py` `cross_sleeve_avg_correlation`(Σ→가중평균\|ρ\|+deadband 0.05)+`down_only_corr_multiplier`(확대 차단≤1.0)+`_cov_to_corr`, ⛔BL prior cov 누수 차단=gate 사이징 전용 view 환류 X, off=byte-identical 순수함수 누구도 미호출). 검증 PASS(가중평균상관·down-only·deadband). ⏳orchestrator 실배선=실거래 영향이라 **사용자 게이트 잔여**(점진 rollout). risk_gate 회귀: helper 격리 PASS, 전체묶음 3 fail=KIS 통합 test isolation 기존부채(내 변경 무관 박제). ②✅**factor 확장 Phase A=vol factor 추가 완료**(2026-05-30). 결정 SSOT=CONSULT-DECISIONS-M4. Phase B(rate분리 real_rate+term_spread / credit β 실측 / growth·copper-gold)=collector 의존 별도. ★Fisher 공선 금지(nominal+real+breakeven 동시 X).
  - ✅**Phase A 구현**(2026-05-30): `factor_betas_seed.FACTORS`=`(rate,dollar,oil,credit,vol)` append-only + 전 6 sleeve `vol` β=None=TIER_HOLD(pool 부재→노출 0=B·Λ·Bᵀ 0 기여 무회귀 placeholder, 게이트 vol 차원 중립). `factor_cov_estimate.FACTOR_TRANSFORM["vol"]="dlog"`(VIX 양수·mean-reverting 로그수익). self-test: factor_betas_seed 7/7(신규 #7 vol placeholder 정직성 박제, 기존 6 무회귀) + factor_cov 5/5 + system_priors 4/4 PASS(둘 다 4-factor self-test 무회귀, system_priors=factor-agnostic 변경0). study 회귀 **81 passed/0 failed**(신규 3모듈 여전히 production 미연결=off-path). ★VIX β 실측=어느 sleeve든 측정 시 pool 형성·활성(eq_us_cyclical VIX −0.378 실측 1순위 후보). ⛔β=0 게이트 사각지대 원칙과 구분: vol은 "미관측" 정직 0(신호부재)이지 reject/hold sleeve의 pool 노출 상실이 아님.
- [~] **M6. ★주식 sleeve 산업×regime 동적가중 보정** (사용자 우려 2026-05-30 — R15 핵심이 주식에서 미검증): weight_card `composed_weights = w_global+δ_regime+δ_arch+δ_inter` 구조는 有, 그러나 주식 sleeve에서 ①δ_regime/δ_arch 실측 충전 여부 ②sleeve 분류 정확성(★XLF 버그) ③산업별 critical 지표 완전성 미검증. → **opus 1m subagent 산업 리서치 스폰**(a6bedf6b, background): sleeve별 산업사이클 지표세트+regime×industry 가중매트릭스+재분류안+과적합방지+구현우선순위.
  - **자문 R2(gemini+claude) 수렴**: ①sleeve 정의=**팩터노출 기반**(GICS 멤버십 아님) — XLU(rate음·bond-proxy)+XLF(rate양·pro-cyclical) 부호상쇄 버그→XLF cyclical/financials 분리(financials 독립 sleeve는 breadth 충분 시) ②거시지표 **A배분 전담·B펀더멘털**(이중계상 회피), down-only 거시=risk-gate라 B잔류 무방, B에 cross-sectional 변환층 추가는 레이어분리 붕괴라 비추 ③**순수 down-only 유지**(SACRED, asymmetric 상방20% 비추=reflexivity·double-capture·risk-on false positive) ④충돌 시 거시(A) inviolable gate 우선.
  - **누락 critical 지표**(자문): cyclical=ISM신규주문/PMI 선행·forward EPS revision breadth, defensive=quality factor(earnings stability)·VIX term structure, financials=yield curve steepness·credit, intl=美대비 상대 이익모멘텀·forward PE갭·carry, eq_kr=**USD/KRW>외국인 순매수>중국 credit impulse>월간수출/반도체(DRAM·SOX)**. bond_cash=MOVE(risk_gate 사이징 직결, 최우선)·ACM term premium. gold=CFTC managed-money·실질금리 디커플링 모니터. commodity=CFTC COT·China credit impulse·days_of_supply z-score. crypto=perp funding+OI·spot ETF net flow.
  - **세션 보수 회신**(2026-05-30): commodity(btn-jpdf)=4단계 격하+★rule 생성(`small-n-statistical-rigor.md`=n<30 통계 5게이트+cross-session promo-log check) register 가능 / eq_intl(btn-excel)=추론통계 Bonferroni 12/12 박제(β_dollar |t|=9.87~23.96 전생존), rate-up 증폭 기각 박제, **B−→A− 회복 청구**(인정) / eq_us_defensive(btn-DA)=3결함 자가fix v3 부분완료(classify_regime KeyError 버그·H3 격하·dollar switch 격하).

## 자율주행 실행 큐 (model: opus 유지 — 골격 설계 + wiring)
- [x] **A. plan/progress 범위 확장**(Phase 3 main wiring 책임 명시)
- [ ] **B. STUDY-KIT 3흐름 보강**(①이론·리소스→lens 선작성 ②수집기 데이터 기초+부족시 main요청+과거실데이터 분석 ③lens 가변·flag 업데이트 루프)
- [x] **C. G2 panel_manifest**(build_indicator_matrix wrap, 본체 보존) + self-test 7/7
- [x] **D. G3 lens_store + judge wiring**(opt-in INV_STUDY_LENS, down-only 보존) lens_store 6/6 + judge 무회귀 11/11 + wiring 단위 PASS
- [x] **E. G4 flag_router + ★동적 가중치 재적합 신규 코드** self-test 6/6(tilt 실변화 입증). confidence_hooks→weight_falsification 연결.
  ⛔ 사용자 확정: **flag 달고 끝이 아니다.** flag(확신/거부) 누적 → 가정 신뢰도 누적 → (a) lens 는
  agent(LLM)가 읽어 반영하지만, (b) **flag 에 따라 지표별 동적 가중치가 실제로 변경되는 건 신규 구현
  코드**다. 구현: confidence_metric(e-value/Beta posterior) → `weight_card.derive_weights` 재적합
  trigger(base_weight 미세조정) → `composed_weights` 반영. 즉 신뢰도→가중치 경로를 코드로 박는다
  (단순 기록·정의 금지). self-test 로 "flag 누적 시 가중치 벡터가 실제로 변한다" 입증.
- [x] **F. G5 선결 2건**(cross-sleeve factor-implied 공분산 PD / regime obs floor 3-mode shrink) system_priors self-test PASS
- [x] **G. G6 study_register**(★production wiring: yaml→registry→judge facade→flag→동적가중치) self-test 5/5(outcome→카드 0.4→0.6 입증)
- [x] **H. 무회귀 회귀판정**(task-discipline-c): judge.py stash baseline=51 failed / 내변경=49 failed
  (judge 빼도 FAIL 안 줄음=회귀0). judge self-test 11/11 + lens_prompt=None byte-identical. study/* 신규
  6파일 = 기존 테스트 미import + self-test 전부 PASS(직교). 49 FAIL = btn-Inv 동시작업(derisk_executor/
  risk_gate→build/fsm) + 환경 외부의존(network/credential/ollama/api_key), 내 변경 무관.
- [x] **I. 10세션 작업지시 전송·가동 확인**(psmux_send 10건). btn-button(macro)=실데이터 regime 분석 코드
  작성 중, btn-profile(crypto)=coin 예외(§4③) 파악+코드 Read 시작. STUDY-KIT §2/§0 정확히 준수 가동.
- [x] **J. 방 산출 폴링·통합·production wiring 완료**: 10/10 yaml register OK(errors 0) → opt-in ON(INV_R15_WEIGHTS/
  INV_STUDY_LENS)에서 카드 10개 AssumptionRegistry 등록 + judge facade(card+lens) 전부 작동 miss=0 + 가드 13/13 +
  골격 6 self-test 무회귀. worker 6개 LLM hang 은 Escape 복구. scope/domain Literal 매핑 + frontmatter multi-doc 수용 개선.

## GitHub/OSS 자산 봉합 계획 (어느 단계·어떻게 쓰나)

OSS 는 성격별로 봉합 지점이 다르다. **코드로 끌어오는 것**과 **지식으로 흡수하는 것**을 분리한다.

| 유형 | 예 | 봉합 단계 | 어떻게 쓰나(wiring) |
|---|---|---|---|
| **① 라이브러리(pip)** | FinanceDataReader, pykrx, fredapi | Phase2 방 블록6 collector_plan 명시 → **Phase3 main G6 봉합** | `stock/data/` 또는 `core/data/` 에 수집기 추가, `VintageProvider.realtime`/`FundamentalsProvider.fetch_filings` 구현 → 자동 PIT. **이미 선구축**: pykrx=`krx_flows.py`, FRED=`fred_adapter.py`, FF5=`french_factors.py`, ETF=`us_etf.py`, FX=`macro_market.py` |
| **② 데이터셋/CSV** | Ken French 팩터, FinanceDatabase(티커 메타), Damodaran 멀티플 | Phase2 블록2 source_or_collector → **Phase3 G6** | 오프라인 캐시 + `VintageProvider`(offline graceful). french_factors.py 패턴 재사용. 갱신=`refresh_cache` 수동 |
| **③ 알고리즘/지식** | Investment Clock, MarketMoodRing(MIT regime), carry/backwardation 공식 | **Phase2 방이 흡수** → 블록1 lens / 블록3 relationships prior | 코드 fork 안 함. 자문(`/gemini-web`+`/claude-web`)으로 원리 학습 → lens.pricing_principle·report_relations + edge theory_basis 로 코드화. regime 분류는 기존 `core/brain/regime_classifier` 사용 |
| **④ 직접 fork 후보** | 특정 factor 계산 repo(있으면) | Phase2 방 식별 → main 승인 후 Phase3 | 라이선스(MIT/BSD) 확인 + 반사성 게이트 통과 series 만. force-include≤4 prior 제한 |

**봉합 규칙**: 방은 OSS 를 직접 코드에 박지 않는다(공유 파일 보존 원칙). 방은 블록2/블록6 에
"무엇을 어느 라이브러리/소스로"만 적고, **실제 코드 봉합(import·수집기·PIT wiring)은 Phase3 에서
main 이 G6 study_register + 수집기 추가로** 한다. 라이선스·반사성·PIT 게이트는 main 봉합 시 검증.
방이 "새 라이브러리 설치 필요" 판단 시 블록6 credential 옆에 `pip:<pkg>` 명시 → main 이 설치+봉합.

## 세션↔study_id 매핑 (작업지시 배정 — 산출 폴링 시 참조)
| psmux 세션 | study_id | 자산군 |
|---|---|---|
| btn-button | macro | 거시·FX |
| btn-common-task | eq_us_cyclical | 미국 경기민감주 |
| btn-DA | eq_us_defensive | 미국 방어/금융주 |
| btn-diary | eq_kr | 한국주식 |
| btn-excel | eq_intl | 국가지수 ETF |
| btn-GCP | reit | 리츠 |
| btn-jpdf | commodity | 원자재 |
| btn-jsh86 | gold | 금 |
| btn-powerbi | bond_cash | 채권/현금 |
| btn-profile | crypto | 암호화폐 |
> 산출 위치: `D:/projects/Inv/study-research/{study_id}/study_session.yaml`. 도착 시 study_register.register 로 production wiring.

### J 통합 현황 (방 산출 도착·검증 — 누적)
| study_id | 도착 | register 검증 | 비고 |
|---|---|---|---|
| gold | ✅종결 | OK (E0 W0) | ★②완수: FRED+GLD n=4279일 실측, decoupling 가설 데이터 기각(β 16년 안정), level intercept shift 로 estimation_note 재정의, reject/confirm signal 정량화. 자문 skip 승인 |
| eq_intl | ✅종결 | OK (E0 W5) | ★②완수: Yahoo 5y 18series(1255행) 실측 8가설 검증, dollar_dominance 강확인(H5 dxy_β R²~0.30). raw/yahoo_cache+analyze.py |
| eq_us_cyclical | ✅종결 | OK (E0 W1) | raw 반도체 패널 + summary §3.5 데이터 검증 + yaml R5 prior 하향 = ②완수 |
| macro | ✅종결 | OK (E0 W0) | ②완수: RegimeGlasso 756일, 공통원인 분해(nasdaq~dxy -0.40→partial 0.04). macro=regime엔진(belief→전 sleeve Σ_eff). inject 선결(max_sharpe rf 버그)=④에서 해소 확인. collector: DFII10/JGB/M2 fred_adapter 확장 |
| eq_kr | ✅ | OK (E0 W6) | Escape 재가동 후 완성. W=ticker→pooling/conditioning_set 권장(허용) |
| reit | ✅ | OK (E0 W6) | 〃. equity sub-panel |
| commodity | ✅ | OK (E0 W3) | ★yaml frontmatter multi-doc → study_loader safe_load_all 개선으로 수용. days_of_supply 명명(inventory 반사성 회피) |
| bond_cash | ✅ | OK (E0 W4) | 듀레이션·스프레드 |
| crypto | ✅ | OK (E0 W2) | coin §4③ 예외, inject3+falsify2+card-lens1 |
| eq_us_defensive | ✅ | OK | 방어/금융 특화 + 하드룰 코어셋. 완료 |
> ★10/10 통합·production wiring 완료(errors 0). 카드 10개 registry 등록 + judge facade(card+lens) miss=0 + 가드 13/13.
> ★골격 견고성 개선: yaml frontmatter(---) multi-document 를 study_loader.safe_load_all 로 수용(방마다 frontmatter 습관 graceful).
> ★공통 약점 = §2 작업순서 **②(과거 실데이터 분석)을 ctx 한계로 스킵**(gold·eq_intl 막힌점 일치). 1차 yaml=lens+가설
> 위주, 실데이터 대조 약함. 운영: 종결 방에 "실데이터 fetch→상관·Rank-IC 실측→prior_strength/flag 보정" 보완 scope 부여.
> 10개 완료 시 INV_R15_WEIGHTS on 으로 카드 등록 + 가드 재실행 + 최종 보고.
> ★production wiring TODO (gold dimensional consistency 지적): system_priors.factor_implied_cross_cov 의 factor
> loading 은 self-test 임의 예시([-0.5/-0.8/0/-0.2])가 아니라 **방 실측 베타**(gold: real -0.32/dollar -0.33)로
> 채워야 함. G6 study_register 가 cross-sleeve 공분산 조립 시 (a) 실측 베타 주입 (b) 일별 Pearson 스케일 vs
> loading 절댓값 dimensional consistency 게이트 추가. 10개 통합 후 production wiring 마무리 단계에서 구현.

## v2 승인 게이트 현황 (2-1 direction.md → main 승인 → 2-2/2-3)
| study_id | direction.md | 승인 | 비고 |
|---|---|---|---|
| macro | ✅ | ✅승인 | 7축 확장(Growth/Vol/Supply)+잠재인자 통제, Markov/DCC 외생위배 기각(벤치마크만), 가설0~6 정량 반증+GATE, 3R 수렴. 보강=effective-n 게이트+가설0 우선중단 |
| eq_intl | ✅ | ✅승인 | Intl CAPM/Adler-Dumas/segmentation, walk-forward OOS, 가설 9+2건. ★China 환각 cross-check 의무 자각. 승인 조건=환각 검증 이행 |
| 나머지 8 | ⏳ | — | 2-1 자문 다회 진행 중 |
> 승인 기준: ①이론수집 ②검증방향 ③가설(반증조건) 충실 + round-* 다회 수렴 + 자문 비판적 심사(맹목추종 회피).

## Working Notes
> [ckpt-202606012100:btn-Inv] 핸드오프 상세본+누락보완(889b179)+credential 정정 완료. ★cushing=EIA 무료키(유료 아님), roll/정밀fwdEPS만 유료, 3종 다 "하기로 결정X" probe 확인만. jsonl 대조 누락3건 보완. 결정=자문 3R 5대상(국면/cross/lifecycle/15축/judge아키텍처)=방향성설정 + 4관문(자문→15축 실측→독립audit→등록). 다음=jsonl 대조로 핸드오프 누락 보완 후 clear. long-mode ON, push 금지. 진입=handoff-study-wire-gap-20260601.md
> 인계: [handoff-study-wire-gap-20260601.md](./handoff-study-wire-gap-20260601.md) (★study→코드 wire 미연결 발견 + merit/audit/J축/regime/credential — 다음 세션 자율 진입점)
> [ckpt-202606011700:btn-Inv] ★wire gap 발견 + merit 후속 5건. study 산출 전부 런타임 미연결(설계상 opt-in facade, judge/corr_prior/merit지표 채택0). cyclical merit audit 충실+yaml v5 / crypto·eq_intl·defensive verdict→yaml / eq_intl L축 DTWEXBGS caveat 해소 / 지역연준 Empire→SOXX Bonferroni 첫 생존(audit 충실) / regime-conditional PoC(신호 정제 도구) / J축 sample+batch std β(shadow OOS PASS, SEED 미반영=grand fallback cross-group 오염) / credential probe(cushing·roll 불가, ISM/PMI 가능). ★다음=전자산 wire 전수조사+Phase I 통합개통(go-live경계)+J축 SEED build_seed_betas 보완(B factor별 정책+cross 자문). push 금지. 진입=handoff-study-wire-gap-20260601.md
> 인계: [handoff-study-merit-audit-20260601.md](./handoff-study-merit-audit-20260601.md) (이번 세션 완주 인계 — 커밋14·audit6·merit탐구·J축 검증·잔여)
> [ckpt-202606010900:bc9afbe0(신 main, 단일세션, ctx 86%)] J축 통합 기계검증 PASS + 세션 핸드오프 작성
> (1) 마지막 결정: J축 = `factor_betas_seed.build_seed_betas → system_priors.factor_implied_cross_cov` 기계 검증 완료(end-to-end PD min eig 0.986, study 13/13 무회귀). L축 1회 계상=FACTORS 구조적 보장. overlap 박제(fx↔dollar R²8.7% 75%독립·VIX↔credit R²2.2% 독립). ★정밀 β seed 셀 population(eq_us_defensive rate/credit/vol)은 의도적 미수행 — sleeve-내부 coincident 라 깨끗한 절대 std β 미산출, "점추정 magnitude 박제 금지" 원칙상 추측 loading 금지 → shadow validation 단계 raw 재실행 std β 추출 TODO.
> (2) 다음 의도: ①cyclical merit 12축 audit(DGORDER→XLE TENTATIVE, 저우선) ②J축 정밀 β shadow population(각 sleeve raw 재실행 std β→seed→factor_shadow OOS) ③eq_intl L축 DTWEXBGS full-sample 재검 ④audit verdict→yaml 반영(crypto H11/eq_intl merit/defensive vix_term/cyclical DGORDER) ⑤credential 게이트 지표(cyclical ISM·commodity cushing) 사용자 빌드 confirm. eq_kr/eq_us=stock.md 별도세션.
> (3) 동기화: study-research 미커밋 0(커밋14 push 보류). recent 0d98a57/e841b37/58f2184/51f3f26 audit. python=Python312 +PYTHONUTF8=1 필수. audit=별도 opus subagent 12축 self-certify 금지.
> [ckpt-202606010600:bc9afbe0(신 main, 단일세션)] 자산별 12축 audit 5건 완결 + merit 지표 실데이터 탐구 2건 (사용자 "추가검토 지표 실데이터 탐구 + 자산별 12축 audit + subagent 가속" 지시)
> (1) ★study→audit 사이클 완결 (전부 별도 opus subagent, self-certify 회피): bond_cash v5=충실(hard0, KW/ACM corr 0.86·walk-forward 부호반전 재현·register 가능, D축 표현 daily/revision-lag 정정) / crypto cycle2=부분(hard0, ★H11 over-claim 적발: IC 0.1117 raw p=0.28 비유의·CI 0포함·U-shape → validation TENTATIVE 격하 prior 0.20→0.05, H7/H8/H10/H12 ledger 탈락, H9 walk-forward 조건부) / eq_intl merit=부분(★credit impulse 동시 +0.41=revised-vintage lookahead 착시 적발: Q+1 라이브정렬 시 +0.05 붕괴 korea 부호반전 → structural_low 격하 / fx=PIT-safe exposure 수용 / JGB REJECT / REER TENTATIVE) / defensive VIX=충실(hard0, PIT-pure 정당, co-move/forward 코드분리 over-claim 없음, credit overlap R²2.2% 거의독립, register 가능).
> (2) ★merit 지표 실데이터 탐구 2건 (block6 collector_plan "검토만·미탐구" 해소, 무료 FRED+yfinance): eq_intl 4지표(JGB-UST/REER/China credit impulse/fx_carry) + defensive VIX term structure(VIX3M/VIX). 둘 다 12축 audit-ready 산출 → audit 통과.
> (3) ★★교차 발견 (4연속 재현): co-move(동시) 채널은 단단 / forward(예측) 채널은 전멸 — eq_intl credit·fx, bond_cash regime IC, defensive VIX 전부. 시스템 자화상 = "예측 알파 머신 아님, 레짐 동시진단 + risk-overlay + 방향 prior 머신". ★단 co-move 도 PIT 검증이 갈림: credit impulse=revised-vintage 착시(격하) vs VIX=무개정 PIT-pure(정당). lag_routing=contemporaneous 지표는 weight alpha tilt 금지·risk modulator 한정 배선.
> (4) ★커밋 12건 (push 금지=로컬, study-research 미커밋 0): eq_us_cyclical/reit/gold/bond_cash×3/crypto/eq_intl×2/defensive×2 + gitignore. recent: 0d98a57 VIX audit / e841b37 eq_intl audit / 58f2184 crypto audit / 51f3f26 bond_cash audit.
> (5) 다음 의도: ①L축 통합 선행측정 = eq_intl fx환↔macro β_dollar partial-corr + VIX_term↔credit_beta(R²2.2% 측정완) → ②최종 J축 system_priors 통합(공통 stress/dollar 인자 1회 계상 + PSD eigh-floor). ③잔여 미탐구 지표 = cyclical ISM/PMI·forward EPS(ISM 유료화+estimate=credential 게이트) / commodity 이연 cushing(EIA)·roll_yield(CME)=credential — 무료 가능분만 선별, 막힌 건 사용자 빌드 confirm 대기. ④eq_kr/eq_us=stock.md 별도세션(제외 확정).
> [ckpt-202606010300:bc9afbe0(신 main, 재부팅 복구 단일세션)] handoff-reboot-recovery 재개 — commit 5건 + bond_cash P0 구현 + audit 2 dispatch
> (1) ★ground truth 재확인: 핸드오프 스냅샷 "잔여 5건 미완"은 보수적. 실제 = eq_us_cyclical(yaml v4 격하 완료)·reit(§1.7 self-check 완료)·gold(§1.7 H2/H7/H8 완료) = **완료+미커밋**. crypto/macro 미커밋 0(stale). 유일 실잔여 = bond_cash P0(미실행). promo-log K 박제.
> (2) ★자산별 conventional commit 5건(push 금지): eq_us_cyclical d80d148(δ_regime sign-only+magnitude freeze) / reit 98237ec(R4 carry+§1.7) / gold e1c4b48(yaml v3+§1.7 H2/H7/H8) / bond_cash 88c5961+(v5 P0) / 백업 gitignore a7a6618. study-research 미커밋=0.
> (3) ★bond_cash Phase7 옵션A 구현(phase7_walkforward_kw.py 실행, PYTHONUTF8=1): P0-1 walk-forward(HYG 4 regime 중 3개 OOS 부호반전=in-sample artifact 입증, audit C축 해소) + P0-2 Kim-Wright(KW vs ACM corr 0.86<0.95 material 차이, ACM lookahead 의존 완화, audit D축 부분해소). summary_v5.yaml=sign-prior only·magnitude 박제⛔ 불변. data/ 28MB=.gitignore.
> (4) ★12축 audit 2 병렬 dispatch(opus subagent, 사용자 "자산별 audit + subagent 가속" 지시): bond_cash v5(af6c34ec) + crypto cycle2(a8a0931a). 둘 다 raw 재실행+ADF+half-split 독립검증. 나머지 7자산(commodity/macro/reit/gold/cyclical/defensive/eq_intl)=기 audit verdict 박제됨.
> (5) ★eq_intl 2단계 저장 self-check = PASS(정직): 검증지표(β_dollar 12/12 Bonferroni)는 full stats raw / merit 추가분(fx_carry·terms_of_trade·China TSF·JGB-UST)은 block6 collector_plan 정확배치+미검증 caveat 명시. ★잔여 = 이 4지표 FRED 무료 fetch→validation 미탐구(M3/M6 indicator exploration 핵심).
> (6) 다음 의도: audit 2건 verdict 수신 → yaml 반영. 사용자 "추가검토 지표 실데이터 탐구" 핵심 = eq_intl 4지표(JGB-UST/REER/TSF/fx_carry FRED 무료) + cyclical(ISM/PMI)·defensive(VIX term ^VIX3M 무료) 등 미탐구분 → study→audit. 최종 J축 system_priors 통합(L축 1회계상+PSD). eq_kr/eq_us=stock.md 별도세션(제외 확정).
> [ckpt-202605311730:bc9afbe0(신 main, btn-Codlearn 대체)] git 저장 점검 + 2단계 지표 저장 점검 + hang 2회 복구 + main 세션 정체 규명
> (1) ★main 세션 정체: btn-Codlearn psmux(4dd250f1) = 계정 주간한도 초과 → 다른 계정 OAuth 화면 멈춤(부활 불가). 현 main = bc9afbe0(psmux 밖 독립 인스턴스, pull 방식 = 각 세션 pane capture 로 회신 수집, relay 불요). 세션 지시 시 '결과 pane 출력만, btn-Codlearn relay 금지' 명시.
> (2) git 저장: study-research 130 미커밋 발견(register≠git commit 누적). main 직접 3 commit = commodity(61e6d4a, 37파일 merit study)/루트문서(8f14b41, AUDIT-GUIDE+DISPATCH-TRACKER)/eq_intl·kr·us(26cba0a 유실방지 스냅샷). 활성세션 7곳(gold/reit/crypto/eq_us_cyclical/bond_cash/eq_us_defensive/macro)엔 자기 자산군 로컬 commit 지시(push 금지=peer 충돌회피). 남은 61 미커밋=세션 작업완료 후 commit 예정.
> (3) 2단계 지표 저장 점검: 사용자 우려=2단계 merit 지표가 1단계만큼 원문/rationale 저장 안 됐을 가능성. ★commodity 직접검증=양호(validation-china: BIS stock proxy 한계+spec↔code drift+falsifier 명시=모범, round-* 에 china/cftc 자문 포함, m3-*.py provenance). Explore agent 전수판정=raw 못읽어 부정확(commodity 'rationale 0' 오판=신뢰불가). → 7세션 self-check 지시(commodity 모범 기준). eq_intl/eq_kr=세션부재 main 추후 직접.
> (4) §1.7 소급(사용자=의심건만): DA=ADF PASS clean(NFCI/BAA10Y mean-reverting level 정당, verdict 유지) / reit=level-on-level 4th instance 발견 보강중(mixed regression 실질영향 제한) / gold=H1/H4/H5/H6 clean·H3/H7 추가점검중.
> (5) ★hang 2회: PC 의도적 절전 1회(사용자, 재발없음)로 DA/GCP/jsh86 + profile/common-task LLM hang(토큰 정지+타이머만 wall-clock 증가). Escape 복구(C-c 금지)+nudge 재가동 전부 성공. 판별기준=spinner 토큰 고정 + esc-to-interrupt 부재.
> (6) 다음: 7세션 회신(git commit+self-check+§1.7+STUDY/YAML DONE) pull 수집 / eq_intl·eq_kr main 직접 점검 / 최종 J축 system_priors 통합(L축 공통 equity 1회 계상+PSD). 다른세션 느린것 추후 점검(사용자). autopilot flag ON.
> [ckpt-202605311700:btn-Codlearn] 8세션 소통 재확인 + 이해 검증 + 사용자 게이트 3결정 (autopilot ON 속개)
> (1) 마지막 결정: 사용자 "다른 세션 소통해 이해 검증 + 잔업 확인" 지시 → 8세션 전건 상태확인 송신·회신 수집. ★세션↔자산군 매핑 확정: gold=btn-jsh86 / bond_cash=btn-powerbi / reit=btn-GCP / crypto=btn-profile / δ=btn-common-task / eq_us_defensive=btn-DA / macro B그룹=btn-button / local-db=btn-Inv. 회신 6/8(활성 2=crypto·δ 큐잉). 검증 결과 = 큰 틀 일치, ★정정 2건: bond_cash·reit 는 12축 audit 이미 1회 완료(나는 미실행 오판). 잔업 거의 없음 = 6방 STUDY+audit 종료, 2방만 활성.
> (2) 사용자 게이트 3결정: ① macro B그룹 push=보류(로컬 유지, b89f313). ② bond_cash Phase7=옵션 A(walk-forward regime classifier + ACM Kim-Wright real-time 대체 P0 2건 구현 후 진입) — btn-powerbi 지시 송신. ③ §1.7 rule(gold H8 spurious 신설)=의심 건만 소급 — btn-DA(NFCI level regime classifier ADF 사전검정)·btn-GCP(reit level driver self-check)·btn-jsh86(gold H8 외 self-check) 지시 송신.
> (3) 다음 의도: ⏳ 회신 5건(bond_cash 'P0 DONE' / DA '§1.7 소급 DONE' / reit·gold '§1.7 clean or 소급' / crypto 'STUDY DONE' / δ 'YAML v4 DONE') → 도착 시 crypto만 12축 audit subagent dispatch(나머지 self-check·구현). 최종 J축 = system_priors 통합(L축 공통 equity 인자 1회 계상 + PSD 게이트). 작업·audit 전부 12축(AUDIT-GUIDE §1) 기준.
> (4) 동기화: autopilot flag=button/agent/.secretary/.autopilot-btn-Codlearn.flag ON(갱신 16:55). ★핵심 패턴: 점추정 magnitude는 정밀통계서 격하·sign/direction prior만 생존. audit=main subagent 전담(self-certify 회피). local-db(btn-Inv)=별도 트랙, 사용자가 'L3 새 세션' 직접 지시함(main 범위 밖).
> [ckpt-202605310355:btn-Codlearn] 압축 복구 후 자율 audit 루프 재개 + bond_cash unblock
> (1) 마지막 결정: 압축 직후 6 대기세션 pane 캡처 판정 — common-task(yaml v4 격하 반영 subagent 2/4)·gold(8축 self-audit)·crypto(P1-2)·reit(AMT 10-K Item7 fetch 14m)=전부 작업중. DA=eq_us_defensive 사이클 CLOSE(2be0fb8, validated 2건 확정) free. **bond_cash(powerbi)=main 의사결정 차단 상태** → 해소: P0 5건 전건 self-fetch 가능 판정·검증(ACM NY Fed XLS 200 OK·C1 fredapi·C2/C4 yfinance·C9=BAMLH0A0HYM2 2023-05~ FRED + BAA10Y/NFCI 무료 장기대체) → option A(즉시 study, main 빌드 불요) 송신 = unblock 완료(Simmering 확인). ICE 1996~ 유료분만 탈락(대체로 merit 보존).
> (2) 다음 의도: 전 세션 mid-study busy, audit 대상 리포트 미도착 = 알림 대기 루프. ⏳ common-task 'YAML v4 DONE'(δ_regime sign-only 격하) / gold·crypto·reit·bond_cash 'STUDY DONE' → 도착 시 각 12축 audit subagent dispatch(macro/commodity/DA 패턴 동일). DA=free(추가 scope 미부여, 종목 도메인 클로즈). commodity 잔여 이연(cushing EIA·stock_to_use USDA·lme/roll_yield 유료·CME)=credential 블록. EDGAR XBRL collector=사용자 빌드 confirm 대기.
> (3) 동기화: autopilot flag ON(15분 idle 비서 깨움). reports=psmux relay(SSOT psmux-send.sh), audit verdict=task-notification. ★핵심 패턴 유지: 점추정 magnitude는 정밀통계서 격하·sign/direction prior만 생존. audit=main subagent 전담. ⛔ a1a81513 재dispatch 금지.
> [ckpt-202605311645:btn-Codlearn] 핸드오프 통합 재개 + 자율 audit 사이클 (autopilot ON)
> (1) 마지막 결정: stale 7방 인계→clear→재주입 완료. study→main 12축 audit subagent→verdict relay→세션 yaml 반영 사이클 가동. ★audit 4건 완료 = macro B그룹(rate분리 validated/credit β structural w≤0.25/dollar REJECTED, commit b89f313) · commodity ENSO(이연→채택 structural_low_confidence, spurious 아님 확정, commit + promo-log K) · common-task Verify(δ_regime magnitude 전멸: G2 14/16 CI cross-0·K Bonferroni 0/16·G4 LOEO OOS R² 음수=descriptive not predictive → sign-only prior 격하 지시) · DA v4(충실 PASS hard-fail 0, ★H4a credit beta industry split=validated 핵심강신호 n=6588 p<0.0001 / H1 contemp validated / H2·fwd3M REJECTED / H3 structural TENTATIVE / v2 3결함 해소 확인). promo-log K 3건(고지속 predictive 분리·regime δ magnitude 박제금지·자문≠실측)+DA ERROR 1건(handoff source 미검증).
> (2) 다음 의도: ⏳ DA 'YAML v4 TIER DONE'(H4a validated 등 tier 반영+commit) + common-task 'YAML v4 DONE'(δ_regime sign-only 격하)+'YAML v4 TIER' 회신 → progress [x]. gold/crypto/reit/bond_cash STUDY DONE 도착 시 각 12축 audit subagent dispatch(macro/commodity/DA 패턴 동일). commodity 잔여 이연(cushing EIA·stock_to_use USDA·lme 유료·roll_yield CME)=credential 블록. EDGAR XBRL collector(H4/H5/H10/H11+산업 δ_arch 14종 unblock)=사용자 빌드 confirm 대기.
> (3) 동기화: autopilot flag=.autopilot-btn-Codlearn.flag ON(15분 idle 시 비서 깨움). audit subagent verdict=task-notification 수신, 세션 reports=psmux relay(SSOT psmux-send.sh). ★핵심 패턴: 점추정 magnitude는 정밀통계(bootstrap+LOEO OOS+Bonferroni)서 거의 격하, sign/direction prior만 생존(3 audit 공통). audit는 main subagent 전담(self-certify 회피). yaml Edit=각 방 opus 또는 main.
> (4) [ckpt-202605311652 갱신] DA YAML v4 TIER DONE(6c351a0, H4a validated 박제) → DA H3 walk-forward 보강 STUDY DONE(cb36b65, validation-H3-walkforward.md) → main 12축 audit a1a81513 **verdict 완료 = H3 structural TENTATIVE 유지 확정**(quantile lookahead 제거✔·OOS 부호분기 생존✔ sleeve §1.6 validated_structural·but Bonferroni 0/4 미달→magnitude 승격불가·effective-N≈6 crisis episodes). DA에 G축 effN≈6+D축 NFCI value-vintage 잔존 보강 지시 송신, 'H3 보강 DONE' 대기. ★**eq_us_defensive 사이클 클로즈 — validated 2건(H4a credit beta industry split·H1 contemp real-rate) 확보.** / ⛔ 미수신: common-task δ격하 'YAML v4 DONE' + gold/crypto/reit/bond_cash STUDY DONE → 도착 시 각 audit. ⛔ a1a81513 재dispatch 금지(완료).
> 인계: [handoff-collector-build-20260531.md](./handoff-collector-build-20260531.md) (collector-build program 자율 재개 진입점 — /clear 후 본 파일 Read)

> [ckpt-202605310200:btn-Codlearn] **collector-build program — merit 지표 실증 (자율주행 ON)**.
> (1) 마지막 결정: 사용자 program 확정 = merit 있으면 main이 collector 직접 구현 → M3 study → 12축 audit(별도 opus subagent) → yaml 반영. 미채택은 오직 '실측 무상관'. ledger=최종 잔여물(첫 작업 X). ★commodity 2건: **China credit impulse**(DBnomics BIS WS_TC Q.CN.P.A.M.770.A, 18 test 전부 Bonferroni/HAC/FDR 비유의→structural_low_confidence/validated_alpha=false, audit **충실**+보강2 적용) / ★**CFTC speculative**(CFTC Socrata 6dca-aqww 무료 copper noncomm net, 1m fwd ρ+0.223 HAC p=0.0025 Bonferroni·bootstrap[0.106,0.328] 생존 n=405, ★momentum 통제 후 z t=2.76 p=0.006+partial-spearman 0.21 p=3e-05=독립 alpha→**validated_alpha=true**, audit 진행중 a0fdca0e). 3 audit: commodity-China(충실)·eq_intl DM/EM(충실+JGB-UST carry-spread 보강)·macro HY OAS+real_rate(부분, 활성2종 regime-OOS 미검증=factor-beta prior, 비대칭 보강3 sent, dollar/oil 보류 정당). 파일=commodity/raw/m3-{china-credit-impulse-v2,cftc-speculative,cftc-momentum-control}.py.
> (2) 다음 의도: 세션 collector-request 트리아지(reit 19·gold collector-request-to-main.md·crypto merit-queue.md 14·eq_us_cyclical collector-request-queue.md EDGAR·eq_us) → free collector부터 main 구현: NOAA ONI(commodity agri, cpc oni.ascii.txt✓) / JGB-UST(eq_intl, FRED IRLTLT01JPM156N−DGS10) / EDGAR(eq_us_cyclical sec.gov UA-이메일) / CoinMetrics·yfinance corr(crypto) → 각 study→12축 audit→반영. CFTC audit(a0fdca0e)로 validated 확정/격하. 자율주행 ON until 전 누락지표 audit+반영.
> (3) 동기화: ⛔점추정 박제 금지(validated여도 covariance prior freeze X, prior_strength wide 0.30). 무료 collector: CFTC Socrata 6dca-aqww/NOAA cpc/BIS·IMF=DBnomics(FRED 직접 timeout)/EDGAR sec.gov. eq_us_cyclical Workflow wf_9ce20415-0d2 완주중(kill X). macro vol/VIX 후속(factor직교✓·분류기 미투입). ★psmux 다중라인 truncate→단일라인 송신 필수. DISPATCH-TRACKER §6=audit 현황판.

> [ckpt-202605302330:btn-Codlearn] **누락 지표 일괄 발송 정정 + crypto 감사 충실 + commodity main 직접**.
> 결정: ★누락 critical 지표(자문 R2)를 progress 정리만 하고 발송 누락=main 지시 누락(promo-log ERROR-202605302230 capture-idle 동반). 정정: 5 자산군 발송 완료(b2vn99aa9 exit0 — gold:CFTC managed-money·DFII10 디커플링 / eq_intl:상대이익모멘텀·forward PE갭·carry·China credit impulse / reit:sub-sector supply·cap-rate / bond_cash:MOVE최우선·ACM term premium / macro:term·credit spread RegimeClassifier 반영점검). crypto 12축 독립감사(a719c05)=★충실, register 가능(합성0 byte-identical 재현, MVRV2.83 ATH 지문, validated alpha 0=정직, 보수2: H1 20-cell Bonferroni 미적용→방향성격하 / prior_ladder sharpe 중첩윈도 SE 경고+"가장강"→"잠정우세"hedge). commodity=jpdf가 eq_us 전환(/clear)으로 세션 부재→main 직접. 누락지표 yaml 확인: CFTC/COT/days_of_supply/storage/backwardation/carry 다 반영, ★China credit impulse만 갭. self-audit 통과(8축5완전+3부분) register 가능.
> 다음 의도: ①✅**commodity register 완료**(2026-05-30, `register('study-research/commodity/study_session.yaml', require_raw=True)`=ok True/errors[]/warnings3 minor[edge conditioning_set 미명시×2 + days_of_supply hierarchical pooling]) ②★**China credit impulse = 실 study 필요**(★register는 기존 yaml 등록일 뿐 ≠ 누락지표 추가. 사용자 정정 2026-05-31: 누락지표 추가 = 최초 M3 흐름 동일 = ①지표 이론 스터디 ②PBOC TSF/BIS 실데이터 수집 ③commodity 수익률 상관계수·Rank-IC 측정 ④lens/yaml 반영. commodity 세션 부재(jpdf=eq_us)→main 직접 or 세션 재배정) ②b crypto register(보수2 후) — ★★동일 원칙: 발송한 5개 자산군(gold/eq_intl/reit/bond_cash/macro)도 누락지표 '지시'만으론 미완, 각 세션이 실 study(이론+실데이터+상관계수)해야 완성. main 모니터링 시 'register/발송 완료'를 'study 완료'로 오인 금지 ③crypto register(보수2 H1 Bonferroni+prior_ladder hedge 반영 후) ④eq_us(jpdf) Phase3 자문 모니터링→direction.md 승인게이트 ⑤bond_cash/reit direction.md 대기 ⑥DISPATCH-TRACKER에 '누락지표 반영' 칼럼 추가.
> 동기화: idle 판단=capture task패널+세션회신 교차(빈프롬프트 단독금지, promo-log ERROR). DISPATCH-TRACKER.md=dispatch 현황판 SSOT. 미커밋 누적. long-mode ON(cap500k, 480k compact).
>
> [ckpt-202605302130:btn-Codlearn] **eq_us(미국주식 전체) 작업방 dispatch 완료**.
> 결정: 사용자 지시(미국주식 전체 main 통합정리 → idle 세션 dispatch, 그 세션이 3R 자문부터 자율수행). eq_kr v2 baseline(`study-research/eq_kr/methodology-final-for-main-dispatch.md` 7-Phase + `raw/original-user-prompts-from-main.md` A1~B4) 미러링. dispatch 대상=**btn-profile**(crypto 슬롯, capture 결과 빈 `❯` 프롬프트=가장 깨끗 idle. jsh86 413k/DA 468k=ctx 한계, common-task=cyclical δ 작업 중이라 제외). 지시서=`study-research/eq_us/MAIN-DISPATCH.md`(6 SSOT 정독 + 미국 input(eq_us_cyclical 4산업 plan+M3 / eq_us_defensive 합성의심 P0 재검증) + GICS 11섹터 Tier 차등 + Investment Clock epoch×dollar×credit cell + 5 금지). btn-profile에 Read+Phase3 자율시작 주입 완료.
> 다음 의도: eq_us Phase 3 자문(/gemini-web+/claude-web 3~7R) 진행 모니터링 → `study-research/eq_us/direction.md` 산출 보고 도착 시 **승인 게이트**(eq_kr 미러: ①이론수집 ②검증방향 ③가설 반증조건 충실 + 자문 비판심사 확인 후 Phase 3.5 승인). eq_kr "v2 baseline 전 자산군 일괄 전달"=미국 dispatch 후속(사용자 추천 Q2-1). M5 risk gate 실배선=사용자 게이트 보류.
> 동기화: btn-common-task(eq_us_cyclical δ 매트릭스 2/4 agents 진행)=eq_us와 중복 회피(cyclical 4산업 input 수용, 재작업 금지). 미커밋 누적(M4 3모듈+M5 vol/risk_gate helper+progress+MAIN-DISPATCH+eq_kr 산출물). btn-Inv peer(6eb41d61) commit 전 `git pull --rebase`. **long-mode ON(cap 500k)** flag 자율.
>
> [ckpt-202605302030:btn-Codlearn] **M5 factor 확장 Phase A(vol) 완료**.
> 산출: `factor_betas_seed.FACTORS` append-only vol 추가(전 sleeve β=None=HOLD, pool 부재→노출 0 무회귀 placeholder) + `factor_cov_estimate.FACTOR_TRANSFORM["vol"]="dlog"`. self-test factor_betas_seed 7/7(신규 #7 vol placeholder) + factor_cov 5/5 + system_priors 4/4 PASS. study 회귀 81 passed/0 failed. system_priors=factor-agnostic 변경0.
> 회귀 확인: 신규 3모듈 여전히 production 미연결(off-path byte-identical). vol 0 기여라 B·Λ·Bᵀ PD 유지. 기존 4-factor self-test(factor_cov·system_priors) 무회귀.
> 다음 의도: **M5 잔여 = risk gate wiring**(cross-sleeve cov B·Λ·Bᵀ opt-in 연결, deadband+clamp down-only, ⛔BL prior cov 누수 차단=Π=δΣw view 환류 이중계상 금지). risk_gate 본체 read 후 opt-in 경로 설계(INV_R15_WEIGHTS off=byte-identical). financials sleeve 코드분리=세션 study 산출 후. 세션 주식 동적가중(M6) 회신 수집. commodity register 진입 가능. Λ 실데이터 fetch로 shadow OOS 검증.
> 동기화 필요: 미커밋 누적(README·progress·신규 3모듈+CONSULT-DECISIONS-M4·fred_adapter·m4-collection·equity-dynamic-weight-design-draft·promo-log + 본 vol 변경). btn-Inv peer(6eb41d61 등) 있어 commit 전 `git pull --rebase`. flag ON 자율.
>
> [ckpt-202605301233:btn-Codlearn] **FRED 1차 driver 등록 + M3 6/6 + 주식 동적가중 세션 위임**.
> 마지막 결정: ①M3 **6/6 독립검증** 완료(eq_us_defensive=불충실 Tier3 — H3 데이터 커버리지 위조급·dollar regime-switch 비유의 → seed HOLD 유지 / eq_intl B−→A− 추론통계 박제 / 나머지 충실). ②M4 factor 통합 3모듈 구현(factor_betas_seed·factor_cov_estimate·factor_shadow, self-test PASS, study 13/13 무회귀). ③자문 wiring R2 수렴(주식 sleeve=**팩터노출 정의**, XLU+XLF 부호상쇄 버그→XLF 분리 / 거시 A전담·B펀더멘털 / 순수 down-only 유지). ④주식 동적가중=4세션(btn-common-task/DA/excel/diary) **산업별 subagent 위임 전부 dispatch 안착**(main 직접 subagent 오해→정정, OBSERVE 기록). ⑤**FRED_SERIES에 DFII10/DTWEXBGS/DCOILWTICO/DGS10/DGS2 등록**(`core/brain/fred_adapter.py`, 1차 driver production 미등록이었음), 회귀 80 passed / 4 failed=ECOS credential 부재 직교(무회귀).
> 다음 의도: **M5 factor 확장 Phase A**(vol factor 추가, macro VIF 실측 1.00 무공선, `factor_betas_seed.FACTORS` append-only+신규β=None=HOLD 재사용). financials sleeve 코드분리(`regime_to_weights.SLEEVES`, BASE_WEIGHTS 재정규화=회귀민감 opt-in)=세션 study 산출 후. 세션 주식 동적가중 회신 수집. commodity register 진입 가능. risk gate wiring(M5).
> 동기화 필요: 미커밋 다수(README·progress·신규 3모듈+CONSULT-DECISIONS-M4·fred_adapter·m4-collection·equity-dynamic-weight-design-draft·promo-log). btn-Inv peer(6eb41d61 등) 있어 commit 전 `git pull --rebase`. flag ON 자율.
>
> [ckpt-202605301040:btn-Codlearn] **M4 거시-종목 factor 통합 구현 완료 (자문 3R 수렴)**.
> 마지막 결정: M3 5/6 verdict 확정(eq_intl 부분충실 B− 추가 — dollar dominance validated / EM-idio·rate증폭 **REJECT**). 자문 3R(gemini-web+claude-web 병렬) 완전 수렴 → [CONSULT-DECISIONS-M4-factor-integration-20260530.md](./CONSULT-DECISIONS-M4-factor-integration-20260530.md) 7원칙: ①M4(seed+Λ+shadow)/M5(gate wiring) 분리 ②verdict 3-tier→James-Stein(validated=w / structural=w≤0.25캡 / reject=pool노출 w=0 / hold=pooled-prior) ③dollar 크기 보존(MRC) ④idio conservation ⑤Λ EWMA+stress floor+Higham ⑥shadow bias-stat/eigenvector ⑦a priori pool. ✅3모듈 self-test 전부 PASS(factor_betas_seed 6/6·factor_cov_estimate 5/5·factor_shadow 4/4) + study 13/13 무회귀. README §종목 스터디 업데이트.
> 다음 의도: eq_us_defensive M3(btn-DA=H1~H4 validation 재칼리 중) 도착 시 seed hold→실측 교체. M5=risk gate wiring(opt-in). Λ 실데이터 fetch로 shadow OOS 검증. 커밋 대기(btn-Inv peer 있어 `git pull --rebase` 선행).
> 동기화 필요: 미커밋(README·progress·신규 3모듈+CONSULT-DECISIONS-M4). flag ON 자율.
>
> [ckpt-202605301645:btn-Codlearn] **멀티세션 M1~M3 완료 + M3 독립 검증 4/6 충실**.
> 마지막 결정: M3 수집 5/6(eq_us_defensive만 작업중). ★M3 독립 opus 검증(raw 재실행 provenance, self-report 신뢰 금지) verdict 4/6 = **gold 충실**(dollar β−0.328>rate validated, E4 decoupling=prior) / **eq_us_cyclical 충실 A−**(β_dxy t−11.04 dollar≫rate, Kish 1.47 정합) / **reit 충실 중신뢰**(3driver정상, VNQ rate직접 −3.82=주식과 다름) / **commodity 부분충실**(precious↔DXY −0.432 n=12 비유의→격하, +0.756 잔차공통→SLEEVE_BLOC B 권고). 전부 provenance 일치·합성無. ★dollar 채널 우위 검증 통과. 상세=study-research/macro/m4-collection.md(SSOT).
> 다음 의도: ★eq_intl 검증 stuck kill(a849ad00, 1000s+ 초과) → **압축 후 재스폰**(study-research/eq_intl/macro-linkage.md + raw/macro_linkage.py provenance 재실행) + eq_us_defensive M3 답신(btn-DA 작업중) → 6/6 후 M4 종합(dollar/broad TWI driver, ⛔점추정 covariance prior 박제금지·방향성만·D/K 미해결 상속). SLEEVE_BLOC A→B 재결정(commodity 검증 B 권고).
> 동기화 필요: m4-collection.md(verdict 보관소 SSOT), STUDY-ORCHESTRATION.md(통신3교훈+M3독립검증), 미커밋 다수. flag ON 자율. ★압축 와도 m4-collection+본 ckpt로 재개.
>
> [ckpt-202605301630:btn-Codlearn] **멀티세션 거시-종목 연관(M1~M4) + M3 독립 검증 진행**.
> 마지막 결정: M1~M3 멀티세션 완료(timeline 배포→6세션 거시연관 분석). M3 수집 5/6(gold·eq_us_cyclical·eq_intl·commodity·reit ✅ / eq_us_defensive 작업중). ★사용자 지적으로 M3도 opus 독립 검증 도입(self-report 신뢰 금지, raw 재실행 provenance, STUDY-ORCHESTRATION 박제). 검증 verdict 2/6: **commodity=부분충실**(provenance✅ but precious↔DXY −0.432 n=12 비유의→방향성격하, +0.756 잔차공통→SLEEVE_BLOC B 권고, ⛔점추정 covariance prior 박제금지) / **reit=충실**(provenance✅·합성無·3driver정상, VNQ rate직접loading −3.82 강함=주식 rate≈0과 다름, 중신뢰). 패턴: dollar 채널 우위 5세션 일관.
> 다음 의도: 나머지 3 verdict(gold a3c651f7/eq_us_cyclical a0b25d65/eq_intl a849ad00) + eq_us_defensive M3 답신 → 6/6 검증 후 M4 종합(거시 레이어 dollar/broad TWI driver, 단 검증통과·방향성만, ⛔점추정 prior 박제금지). SLEEVE_BLOC A→B 재결정.
> 동기화 필요: m4-collection.md(수집판), STUDY-ORCHESTRATION.md(통신 3교훈+M3독립검증), 미커밋 다수. flag ON 자율.
>
> [ckpt-202605301500:btn-Codlearn] **U3 level 분리 + 4방 register 게이트 PASS + 전체회귀 신규0 + M1~M4 등록**.
> 마지막 결정: ①U3 = `corr_prior_shrink(level)` 가드 + `study_register.prepare_corr_prior` facade(scope→level: macro/bond=macro 차단 no-op, 그외=micro). ②eq_us_cyclical 감사=충실(provenance 재계산 일치, tier=structural prior 저신뢰, hard-fail B·C·D·I 없음). ③4방(macro·eq_intl·eq_us_cyclical·commodity) register 통합 게이트 PASS — 검증·raw·카드·L축(id중복0 / cross-study 공통인자 중복계상0 / level분리). ④within-study 이중계상(fwd_ep_normalized×2) → `_build_card` base_weight 합산 dedup 해소.
> 회귀 확인: 전체 pytest **4377 passed / 48 failed 전부 KNOWN_FAILURES.md 4분류 매칭(신규 회귀 0)**. study/regime 2개(test_e2e_automation) 단독 PASS=격리부채. study 118 + register self-test 전부 PASS. study+brain 변경이 깬 프로덕션 코드 0.
> 다음 의도: 거시-종목 cross-correlation(M1~M4, TaskList #12~15) — M1 거시세션(btn-button) 이벤트·지표 요약 요청부터. U3b(별개 인덱스·cross-sleeve edge ValueError)·U4(Beta keying freeze) 후순위.
> 동기화 필요: 미커밋(README·judge·brain·portfolio_orchestrator·study 5파일+progress). btn-Inv peer 2f46607d 있어 commit 전 `git pull --rebase`. 사용자 commit 지시 대기.
>
> [ckpt-파이프라인업그레이드:btn-Codlearn] flag→lens·corr 루프 완성 결정(사용자: 혼자 구현 가능 코드면
> main 구현, 입력 필요하면 양식→방 채움→구현 + 감사기준 추가). **현 구현 상태**: flag→weight=✅
> (flag_router.tilt_weights + study_register:154) / flag→lens=△(lens_store 가변구조 有, flag confidence
> 연결 코드 無) / flag→corr_prior=✗(tilt 는 weight 만, RegimeGlasso.fit corr_prior 별도). **U1 flag→lens=
> main 직접구현**(순수 코드: lens_store.render 에 confidence 라벨 주입 + study_register.prepare_judge_call
> 전달). **U2 flag→corr_prior=main 기본구현(node conf 결합 근사)+방 양식(블록5 affects_edge 정밀)**. 양식
> 배포 → 감사기준 C축 + AUDIT-GUIDE 에 affects_edge 추적 추가함. 큐 U1/U2 추가. ✅**U1·U2 구현
> 완료 self-test PASS** — flag→{weight(tilt_weights), lens(confidence_note), corr_prior(corr_prior_shrink)}
> 3경로 전부 닫힘. 신규: lens_store.render(confidence_note) + flag_router.confidence_note()/corr_prior_shrink()
> + study_loader ConfidenceHook.affects_edge + study_register.prepare_judge_call 연결. 전부 opt-in 게이트 내
> 무회귀(None/누적0 byte-identical, 본체 judge/RegimeGlasso 미변경).
> [ckpt-감사결과-누적:btn-Codlearn] **opus 독립 감사관 verdict (AUDIT-GUIDE.md 12축, 라이브 재계산 기반)**:
> ▸**commodity = 충실(조건부)**. provenance 재계산 일치(H5 0.0452→0.2963 Welch t=-66.74 / H4 lag12 0.3998
> p=1e-12 소수점까지, 합성 지문 0=진짜 실측). hard-fail(B·C·D·I) 없음. D ALFRED미적용=soft(H5 가격무관,
> point_in_time 명시) / K lag·threshold ladder 투명공시=soft(deflation 미적용 0.70 과신) / **G=structural
> prior tier**(overlapping window+Newey-West SE 미보정→validated alpha 아님, self-audit보다 보수). 정합=
> archetype pooling은 weight_card.composed_weights 이미 sub_sleeve 지원→다운그레이드 불요(§4표 delta_arch
> 신규모듈=과대계획 정정, 필드 add만). **register 가능 3조건**: ①H4/H7 latest-vintage 라벨 ②H4 prior
> structural prior tier(validated 표기 금지) ③통합 시 gold real_rate 중복 PSD 점검(L축 main 책임). 방 통보함.
> ▸진행: macro·eq_intl·eq_us_cyclical 감사 대기. reit yaml v2 대기. gold 5/8.
> [ckpt-감사8축-독립감사:btn-Codlearn] ★사용자 지시(2건): (1)"감사 기준 박제+완전성 3개+ 추가+작업지시
> 전체 다시" → **STUDY-KIT §2.5 main 검수 감사 8축 신설**(A이론학습 실재성/B실데이터 시계열검증 실측·⛔합성금지/
> C yaml도출추적/D PIT·OOS/E자문비판+환각cross-verify/F반증+기각기록/G effective-N·검정력/H미해결의문. 판정
> 충실(8축)/부분/불충분(B부재·합성), 불충분·부분=보강요청, 충실만 register). 전 방 8축 통보 완료. (2)"너도
> 통과편향 있으니" → **main 직접 감사 금지, 다음 3산출 필수**: ⓐ8축을 증권 애널리스트/퀀트 시각으로 자문 보강
> (gemini-web+claude-web 1라운드: 빠진 축=data-mining bias·multiple testing·경제적 유의성·실행가능성 등 점검)
> → ⓑ8축 감사 상세 가이드 문서화(잘된 예시 포함, study-research/AUDIT-GUIDE.md) → ⓒ방 산출 도착마다
> **opus subagent 가 가이드 기반 독립 감사**(main 편향 배제). **현 스냅샷**: 2-3완료 충실후보 4방(macro·eq_intl·
> eq_us_cyclical·commodity)=opus 독립감사 통과해야 register / 2-2완료→2-3진입 3방(crypto·gold·reit) / 불충분
> 보강중 eq_us_defensive(합성 시뮬 적발) / 2-3진입지시 bond_cash / 2-1미완 eq_kr. 진행중: eq_intl·macro 감사
> Explore agent(a2cb7b2b) + 8축 자문 착수 예정. ⛔register 보류 — opus 독립감사 가이드 완성 후로.
> [ckpt-v2-진행-압축:btn-Codlearn] **v2 승인 게이트 진행 상황**(압축 전 저장).
> ▸승인 완료(2-2/2-3 진행 허가): **macro**(★2-3 완수+register OK E0W0, 가설0 GATE PASS 공분산 정보이득 5.0배 LR p=4.9e-11, 가설2 FAIL p=0.35=네트워크 rate-regime 불변→regime 신호는 분산+공통원인 매개에 있음, 설계 재조정 hard Ω스위칭❌→안정구조+분산스케일+soft belief-mix. 카드 weight.macro.base 등록=완전종결) / **eq_intl**(2-3 허가, ★China 환각 cross-check 이행: IMF MCHI β·AQR KWEB β 실측 강력기각=환각, 방향성만 ground truth MCHI R²0.23<<EMXC0.68 재정의, H5★★하향) / **eq_us_defensive**(426줄4R, Sahm's Rule/NIM lag/Bai-Perron, factor_beta_decomposition.py 신규=2-3 self-test) / **commodity**(434줄 2채널, Theory of Storage/Carry-Momentum, sub-sleeve archetype pooling) / **bond_cash**(168줄5R, HY OAS+600bps event study, 가설12) / **eq_us_cyclical**(170줄9R, Investment Clock=가설생성기만 ground truth금지, H1 Fama-MacBeth, H4 EBP 가지치기).
> ▸**승인 대기**: **crypto**(2-1 도착, direction 237줄6R, StockToFlow 반례교보재 비판적, coin §4③ belief 경로, halving=regime label/miner outflow=연속지표 분리, stablecoin supply DefiLlama). → **압축 후 첫 작업=crypto direction.md 검토·승인**.
> ▸**미보고/압축직전 신규**: **eq_intl 2-3 완전종결**(walk-forward OOS train24m/test1m/refit1m factor고정: H1 dollar △부분, H5 china idio MCHI R²0.205<<EMXC0.671 **100% OOS 강력확인**→em_china sub-archetype 분리, H7 TSM DM 60-70% vs EM 39-50% archetype mixed. yaml v3+raw(validation-h1/h2/h5/h7) 완비 → **압축 후 register(require_raw) 통합 대상**) / **gold 2-1 도착**(direction.md 작성, 승인 대기) / **eq_kr round-1**(거버넌스↛PBR 학술 반증 발견=v1 밸류업 채널 충돌, R2/3 진행 중, direction.md 미작성) / **reit** 미보고.
> ▸**다음 의도**: crypto 승인 → 나머지 direction.md 폴링·승인(같은 기준: ①②③+round 다회+자문 비판심사) → 2-3 완료 방은 `StudyRegister.register(경로, require_raw=True)` 통합(raw 게이트=round-*/theory-notes/validation-* 완비) → 10/10 카드 등록+가드 재실행+최종 보고.
> ▸**동기화 필요**: 여러 방이 HY OAS/yield curve/VIX driver 겹침=통합 시 중복정의 조율. gold·commodity(precious) 중복. macro 7축이 기준. worker LLM hang 빈번=capture 타이머 2회 고정시 Escape(C-c 금지).
> ▸v1 골격 G1~G6+가드 13/13+raw 게이트 = 재사용 인프라(무회귀). 세션↔study_id=위 매핑표. 자율주행 flag on(progress 완료까지).
>
> 진입: [plan-study-system.md](./plan-study-system.md) / 지시서: [STUDY-KIT.md](./STUDY-KIT.md) / SSOT ckpt: [progress-assumption-v2.md](./progress-assumption-v2.md)
> [ckpt-202605301140:btn-jpdf-audit] 8축 self-audit 완료 (self-audit-commodity.md). 5축 통과 (A이론/B실데이터/C도출/F기각/H의문) + 3축 부분 통과 (D PIT-OOS 실측 latest vintage, E sub-인용 환각 4건, G H7 marginal n=12 + SE 보정 미적용). register 진행 가능 보고 송신. 다음 의도: main register 응답 대기. 동기화 필요: ALFRED 도입 후 H4/H7 재검증.
> [ckpt-202605301115:btn-jpdf] yaml 존재 확인 (40286 bytes 7블록 v2 완성). main 점검 누락 오판 → 재보고 송신. handoff-commodity-v2-20260530.md 작성 (인계 md). 다음 의도: main 응답 (register 진행 or 추가 라운드) 대기. 동기화: study_session.yaml 7블록 + raw 전부 갖춤 → KIT v2 §2-3 raw 강제 통과 예상.
> [ckpt-202605301030:btn-jpdf→commodity방-v2-final] ★승인 후 2-2 theory-notes.md (591줄, 학파 정독 KWB/HK/Erb-Harvey/GHR/Deaton-Laroque/Tang-Xiong/BGR/AMP/Kilian/Szymanowska/Hamilton + sub-sleeve 4종 + 메타) + 2-3 실데이터 검증 (Python yfinance+FRED) 완료. ★검증 결과: H5 강력 확인 (pre/post 2004 0.045→0.296 Welch p≈0), H4 lag 정정 3m→12m (spearman 0.40 p=1e-12), H7 threshold 정정 30%→10% (12 events, CFNAI=-0.46), H1 weak partial -0.07 (gold방 정합), H3 proxy 부분, H10 EIA 404. study_session.yaml 7블록 (★archetype pooling 부록B + gold 분리 + inventory→days_of_supply 명명) + summary.md + validation-summary.md 산출. 다음 의도: main wiring 시 본 yaml 활용. Phase 2 collector (CME term structure 우선) 후 재검증 라운드. 동기화: ALFRED real-time vintage 의무, archetype pooling delta_arch_by_type, gold 방과 SLEEVE 분리 (precious_non_gold), claude R3 critique (H5≠H8 분리/PELT≠Bai-Perron/Kilian SVAR/GHR/Two-speed).
> [ckpt-202605301030:btn-jpdf→commodity방-v2] §2-1 direction.md (591줄) 완료. 자문 3R×2채널 수렴. v1 산출은 raw/v1/ 으로 보존. claude R3 critique 반영: H5≠H8 분리(CIT vs MM), PELT≠Bai-Perron 정정, Look-ahead bias 차단(ALFRED vintage), Kilian 2009 SVAR 보강, GHR inventory-state-variable 통합. 가설 11개(P1/1.5/2/3), collector ranking(DFII10>CFTC>CME>EIA>NOAA>USDA), SLEEVE 3-group(Cyclical/Defensive/Idiosyncratic). 다음 의도: main 승인 대기 → 승인 후 2-2 theory-notes.md 진입. 동기화 필요: G6 wiring 시 H5/H8 분리 측정, Bai-Perron two-speed 신규 모듈, ALFRED vintage 의무, Kilian SVAR.
> [ckpt-202605300645:btn-jpdf→commodity방] commodity 7블록 산출 완료(study-research/commodity/study_session.yaml 601줄+summary.md+raw). 핵심발견: weight_panel._REFLEXIVE_WORDS 에 "inventory" 포함 → commodity 재고 series 는 days_of_supply/stock_to_use_ratio 명명 회피(블록7 learn a안=코드 무변경). 블록6 collector 우선순위 DFII10·NAPM·EIA·USDA·CFTC·LME(stub). 다음 의도: btn-Codlearn 에 방향성 보고 송신 후 idle. 동기화 필요: main G1~G6 wiring 시 본 yaml 블록3 force-include 화이트리스트(days_of_supply↔convenience_yield_z, convenience_yield_z↔roll_yield) corr_prior 주입.
> [ckpt-202605300430:btn-Codlearn] 자문3R→KIT 7블록 확정. 수집기 4종 완료. G1 self-test 6/6.
> [ckpt-자율주행-진입:btn-Codlearn] 사용자 취침+자율주행 flag on. 범위=통합·코드화·렌즈화·production wiring 전부. 큐 A~J 순차. 방 산출 도착하면 J 통합.
> [ckpt-worker-hang-사건:btn-Codlearn] ★자율주행 중 미통합 worker 6개(macro·diary·GCP·powerbi·DA·profile)가 동시
> LLM 호출 hang(Calculating 타이머 수 분~2h 고정) 발견. macro=1h57m. 감지법: capture -S 0 타이머가 2회 측정·이전
> 폴링과 동일=hang. 복구: psmux key Escape(C-c 금지=claude kill) → 큐 nudge 처리로 재가동(전부 성공). 원인 추정=
> 9+ 세션 동시 LLM 호출 rate/응답 hang. 운영교훈: 자율주행 multi-session 은 타이머 고정 모니터링+Escape 복구 필수.
> [ckpt-자율주행-A~I완료:btn-Codlearn] G1~G6 골격 전부 self-test PASS + tests/test_study_pipeline.py 13/13 가드.
> 무회귀 0(judge.py stash 비교 baseline=51/내변경=49 FAIL, 내 변경 무관=btn-Inv 동시작업+환경의존). 10세션 작업지시
> 전송·가동 확인(btn-button macro 분석중, btn-profile crypto coin예외 파악). 남은 것=J: 방 yaml 폴링→study_register
> .register(path) production wiring→가드 재실행. ScheduleWakeup 30분 폴링 루프 진입. 신규파일: core/study/{panel_manifest,
> lens_store,flag_router,system_priors,study_register}.py + tests/test_study_pipeline.py. 수정: judge.py(lens_prompt), study_loader.py(affects_indicator).

> [ckpt-202605301200:btn-Codlearn] (1)마지막: flag→3경로(weight/lens/corr_prior) U1·U2 PASS. 자문 3R 수렴→CONSULT-DECISIONS-layering-20260530.md(belief-truth 격리·single-writer·corr_prior 레벨분리=1순위·shadow-only). flag_router.corr_prior_shrink에 level='micro' 가드 추가(belief→_macro 차단, reflexive loop 방지)=U3 착수. (2)다음: corr_prior_shrink self-test에 level='macro' no-op 케이스 추가 검증 + study_register 호출부가 study scope로 level 전달(macro/bond=macro, equity/commodity=micro). U4=Beta regime-tag·soft gate(키잉만 freeze). (3)동기화: 학습 6방 2-3완료(macro·eq_intl·eq_us_cyclical·commodity·gold·reit), 감사 충실 3방(commodity·eq_intl·macro), eq_us_cyclical 감사 대기(a427f8643). crypto·bond_cash yaml 작성중, eq_us_defensive 보강, eq_kr 2-1. 과거데이터 학습=flag 쌓기 항상(emit)·쓰기(INV_R15)는 baseline off 먼저→비교. raw 229파일+AUDIT-GUIDE 보존.
