---
tags: [type/consult-decision, domain/inv, topic/study-wire, session/btn-Inv]
date: 2026-06-01
scope: study 산출 → 런타임 wire 방향 (4관문 중 1관문=자문 완료). 등록은 실측 15축+독립 audit 후.
consult: gemini-web(Pro) + claude-web(Opus 4.8 High) 병렬 6R, 독립+교차+Red Team+terminal
status: 설계 TERMINAL lock. 다음=실측 배터리 ①~⑧ + 독립 audit → per-relationship 등록
round_boundary: §0~7=설계자문 R1~R6 수렴 / §8~10=구현초안 / ★§11=R8 코드검증+R9-core(IC1~IC8) reconcile(이미있음·신규·deferral 3분류) / ★§12=독립 audit subagent용 15축 자기완결 검토기준. R9 양모델 수렴(2026-06-01, gemini bbhwz0ack+R9 / claude bj91n1qgu+04cac993). 추가 코드검증 2건 TODO(eb_shrink corr-only 시그니처 / factor_implied_cross_cov 호출부 0=단순 미배선 여부).
push: ⛔ 금지 (로컬 commit만)
---

# CONSULT-DECISIONS — study → 런타임 wire (2026-06-01, 6R 수렴)

> ⚠️ **범위 명시**: §0~7 = 설계자문 **R1~R6** 정리본 + §8~10 구현초안. 이후 R8 코드검증에서 "신규"라던 상당수가 이미 구현+M4자문됨이 밝혀져 §1~10 일부가 over-claim → **§11에서 reconcile 완료**(이미있음·신규·deferral 3분류). R9-core(IC1~IC8) 결선 = §11. 독립 audit subagent 자기완결 검토기준(15축) = §12. 상세 인계는 `handoff-wire-consult-20260601.md`.

## 0. 자문 메타 (raw → 산출 매핑)
- 6라운드 병렬 자문(gemini-web Pro + claude-web Opus 4.8). raw 보존: `.consult-wire-R{1..6}-*.md`(브리핑) + `~/.claude/.gemini-web-last.md`·`.claude-web-basic-last.md`(응답) + task output(`tasks/*.output`).
- 흐름: R1 독립 → R2 교차검증(수렴 제조 위험) → R3 Red Team(확증편향 적발·공격) → R4 파이프라인 실동작 주입+수정설계 → R5 lock 검증 → R6 terminal+"shadow=회피"(사용자) 반박.
- ★확증편향 교훈: R1~R2 빠른 수렴은 브리핑에 박은 prior + 교차투입 artifact. R3 Red Team이 실증바닥·경제성·복잡성 결함 다수 적발. R4에서 파이프라인 정확 주입하니 발산(firewall·down-only)이 *둘 다 파이프라인 오해*로 판명·해소. **외부 자문=reference, 등록은 실측+audit(4관문) 후** (decision-quality-protocol).

## 1. ★잠긴 설계 (TERMINAL — 양 모델 R6 합의)

### 1.1 아키텍처 (⑤)
- **judge에 lifecycle 통합 안 함.** judge = lifecycle read-only consumer(메타데이터 읽되 attenuation 방향만, transition-write 금지). down-only attenuator(`size_mult=l1·a2·a3, a2·a3∈[0,1]`, assert_ceiling).
- **단일 SSOT(StudyRegister 카드) → derive-on-read**로 (B)corr_prior view + (C)lens view 두 렌더링. facade `(card_version, as_of)` 순수함수. 사이클당 version pin 1회. retract=새 version append(bitemporal). ★State-Broker push 아님(분산일관성·PIT 위반).
- cross-view monotone-consistency(어떤 뷰도 다른 뷰 관계 부호 못 뒤집음) → audit M 1줄.

### 1.2 3채널 분리 (firewall scoping)
1. **static corr_prior**(블록3 relationships, sign-only·magnitude FREEZE·factor-space PSD `Σ=BΩBᵀ+D`): bond/macro 포함 **WIRE**(reflexivity 없음, 한 번도 firewall 대상 아니었음 — A우려 해소).
2. **belief→Σ_eff**: macro/bond scope=no-op **firewall 유지**(measured covariance pro-cyclicality 차단 — B정당). belief는 **congruence 갱신(D 또는 BΩ'Bᵀ)에만** 가둠=by-construction PSD. risk-asset off-diagonal 건드리면 채널1 침범.
3. **exogenous discrete flag**(yield-curve inversion·HY OAS spike, 포트폴리오 자산서 파생 안 됨): **de-risk-only MUST-APPLY**(regime→sleeve% 보수전환). imperfect exogeneity를 de-risk 비대칭으로 흡수.

### 1.3 cross factor
- risk-off=single latent → **VIX pool 단독, 채널 다중화 폐기**. C9(defensive↔cyclical excess)·C8(bond↔HY flight-to-quality) = corr_prior **NO-GO**(collinear double-count / 부호불안정 비선형). C9·C8은 validation·falsify 입력 + exogenous flag로만.
- **reject≠missing + 측정cell 불가침**(−0.508 오염 root cause). grand는 진짜 missing만·shrinkage-target만·측정cell 불가침.

### 1.4 regime (①)
- 추정 regime = **hardened-soft b(t)**(경계 hysteresis, band 밖 truncate→global contamination bound). 외생 시간(halving)=hard.
- 다중검정 **2단계**: full-sample-gate(독립 필터, threshold 사전고정, type-I valid)→FDR/BH. live rolling = online-FDR(LORD/SAFFRON)/e-process(BH는 fixed batch용).

### 1.5 shrinkage (②b)
- **target 1차**(dollar=one-factor-β, vol=reject-aware) **scalar λ 2차**. λ=empirical-Bayes partial-pooling(★whitened/MAD-winsorized space — crypto 분산 지배 방지, sleeve 비-exchangeable). **값 아닌 추정기 freeze**(target구조+LW공식버전+pooling상수 k). inner CV 폐기(n~15 leakage).

### 1.6 lifecycle falsify (③) 3-tier
- e-process(primary, anytime-valid) / confidence-decay(secondary) / regime-shift=**reset-trigger 아닌 reset/decay**.
- cooldown(re-risk)=evidentiary burden ≥m + shadow re-risk P&L 로그(reflexivity-caveat). de-risk=fast(invalidation debounce).
- ★immortality 방어: full-reset·단순 exp 둘 다 e-process invalid → **1로의 convex-leak `Ẽ_t=γ·Ẽ_{t-1}·m_t+(1−γ)`**(Ville 보존). half-life=−ln2/lnγ, dwell 분포 공동보정.

### 1.7 cost (②/경제성)
- **2-level**: inner no-trade band(Davis-Norman) / outer rolling-window turnover ceiling. + 경제적 유의성 게이트(Δw·edge>cost AND Δw가 covariance 추정오차와 구분 = marginal-precision test ⑤ 병합). market impact 제외(Upbit/소형). ★**KillSwitch/de-risk가 budget OVERRIDE**(flash crash 청산 막으면 안 됨, MUST-APPLY).
- ★aggregate structure-churn cap(사이클당, per-relationship 외 — regime shift가 다수 관계 동시 끊을 때 Σ 점프 방지).

### 1.8 down-only (②/철학)
- (B)cross-sleeve multiplier(≤1.0) + (C)judge attenuator에만. baseline(BL/regime/점수제/l1_size) 무관 — 평시 1.0=full투자. diversification=baseline optimizer에서 harvest, runtime multiplier 아님. under-investment 아님(파이프라인 오해 해소).

### 1.9 audit 15축
- M(wire충실: off byte-identical+facade call-path+orphan inject 0+cross-view monotone) / N(cross관계: sign-stable+**read-time 합성 PSD**+공통인자 1회+tail 부호반전) / O(leakage: PIT-safe+reject≠missing+full-sample-gate+availability-lag). 각 binary gate+증거.

## 2. ★rollout — shadow=회피 교훈 (사용자 R6 반박 채택)
- **통합 원리: 모든 lifecycle state(shadow·active)는 reachable exit 必. black-hole state 금지.** §1.5(validate/reject reachability)와 immortality(falsify reachability)는 같은 병의 양면.
- **경계 = "일별/월별"이 아니라 "unconditional/stationary 구조 vs regime-conditional 구조"**:
  - **unconditional static 채널**(20년 일별 large-n≈5052): OOS 검정 *지금* 결정적. np.eye 못 이기면 효과 없음(Null) → **즉각 activate OR reject(폐기). 영구 shadow 금지**(회피).
  - **regime-conditional·월별 small-n 채널**: n 부족 = **"UNKNOWN/INSUFFICIENT" 정직 라벨**(shadow=working facade 위장 금지) + event-driven 재평가(신규 독립 regime draw 누적 시, 달력 아님).
- np.eye-equiv 등록 = "작동" 아닌 **"무기여(no-contribution)"** 정직 라벨. 기존 np.eye=영구 null/fallback(폐기 아님). opt-in off=byte-identical.
- **go-live(inject 실제 배분변경·judge 라이브·실거래)=별도 gate, 자율 범위 밖.** "설계 수렴 ≠ go-live 준비."

## 3. ★기존 코드 폐기 vs 보완 = 순수 보완 (폐기율 0%)
- 양 모델 확정: 기존 10R 파이프라인 100% 보존. np.eye=beat-able powered null(폐기 아님, opt-in off/shadow서 살아있음). down-only·firewall·점수제 코인봇 미접촉. 신규 SSOT 렌더링(B/C)=거시·구조충격 방어 overlay brake. 라이브 매매=코인봇(study 무관).

## 4. ★실측 배터리 ①~⑧ (adopt 전 필수, audit subagent 독립 — 4관문 2~3단계)
1. VIX β crisis-incl/excl delta(tail-only면 NORMAL prior 아닌 exogenous flag — §1.2 분류 직접 결정).
2. regime-split VIF(Simpson's paradox = C9/VIX double-count 실측 = §1.3 NO-GO empirical check).
3. same-day vs lagged β(배분 prior로서 contemporaneous 타당성).
4. soft b(t)+λ turnover 시뮬 + ★de-risk stress-swap 검증("de-risk 폭이 corr-stale 손실 상한 지배").
5. marginal-precision(corr_prior가 비중 바꾸는 폭 vs naive — cost-gate 병합).
6. break-frequency calibration(m-obs cooldown 정합).
7. **wired-(B) vs np.eye OOS**(honest null=np.eye 이미 작동. **+사전등록 equivalence margin(TOST) 필수** — "못 이김"≠"0과 동등", margin 떨어지면 REJECT). fail-to-reject powered.
8. **★falsify reachability**: 경험 regime-dwell 분포 P(dwell≥m) 검사 → median dwell<m이면 convex-leak half-life decay(γ).

## 5. first-activation 전 lock할 activation-gate 잔여 5항 (calibration-class, 설계변경 아님)
① A: belief congruence-가둠 + read-time Cholesky-success assertion(★Higham silent-repair 금지, log-and-halt). audit N=read-time 합성객체.
② B: 사전등록 stress-corr swap + ④ stress sim 증명.
③ C: convex-leak e-process(γ-mixing) + ⑧ dwell gate.
④ equivalence margin(TOST) + **sunset clock**(영구 shadow 금지 메커니즘화 — 도달 시 강제 activate/reject).
⑤ (가) activation-side **e-BH(Vovk-Wang)/α-spending**(per-relationship activate=K-family selection, falsification만이 아니라 activation도) + (다) aggregate churn cap. (나) activation 증거가 full-sample(구조선택, static엔 허용) vs strictly-OOS(예측주장) 라벨 확인.

## 6. n<30 재귀적 한계 (메타데이터 박제 의무)
dwell-calibration(C/⑧)·equivalence margin·regime-conditional 판정 모두 distinct-regime 수(20년 ~10-25개) 위에서 추정. half-life γ는 보수적(긴 memory/kill 늦춤), 채널배정·margin은 regime 누적 시 재보정 대상. ★immortality 고치는 도구(dwell-보정 decay) 자체가 <30 draw로 보정되는 재귀 한계를 등록 메타데이터에 박을 것. small-n unknown 검증=non-parametric/bootstrap 보수 임계(Gemini note).

## 7. 다음 단계 (4관문)
자문(1관문) ✅ → **실측 배터리 ①~⑧(2관문)** → **독립 audit 15축 M/N/O(3관문)** → audit 충실분만 **per-relationship 등록(4관문, lifecycle wire)**. 등록도 shadow→unconditional만 activate/reject·regime-conditional은 UNKNOWN. go-live=사용자 게이트.
- 실측 subagent 스폰 시 자산별 기존 산출(direction/yaml/validation) 경로 제공+재작업 금지.

---

## 8. ★코드 구현 wiring 맵 (file:line · 현재 → 변경 · 경계 · 완료판정)

> ★대전제: 수렴 설계의 상당수가 **이미 구현됨**. wiring = 신규 글루보다 **기존 메커니즘 연결**이 핵심. 신규 항목만 타겟 확장. opt-in off=byte-identical 회귀 테스트(`tests/test_study_pipeline.py:58`, `tests/test_sleeve_belief_cov.py:150`) 매 변경 통과 의무. 전 wire = execute_trade 전 단계(SACRED 비접촉).

| # | decision | 대상 file:line | 현재 | 변경 | 경계(건들지 말 것) | 완료판정 |
|---|---|---|---|---|---|---|
| W1 | StudyRegister 부트스트랩 | `scripts/run_agents.py:870`(INV_CORE_GATE 블록 내) + `core/portfolio_orchestrator.py:120 allocate` | StudyRegister import 0 | INV_R15 게이트 뒤 모듈 1회 register(`study-research/*/study_session.yaml`) + status 로깅 | INV_CORE_GATE try/except·DRY_RUN·execute_trade | off=import 0 byte-identical / on=cards N개 등록 로그 |
| W2 | corr_prior 주입(static, 채널1) | `core/brain/regime_to_weights.py:197`(RegimeGlasso() 호출) ← `core/study/study_register.py:215 prepare_corr_prior` ← **신규 `relationships_to_corr_prior`** | `RegimeGlasso(min_obs=10)` corr_prior 생략→`np.eye`(`conditional_correlation.py:260`) | `RegimeGlasso(corr_prior=base_cp)`, base_cp=relationships→상관행렬(sign-only, default_rho). eb_shrink(`:207`)이 흡수 | `eb_shrink` λ 로직·`_pd_fix`(`:312` fail-loud)·series_ids 정렬 | off=np.eye 유지 / on=corr_prior≠eye + 배분 % 변화 로그 |
| W2b | belief firewall(채널2) | `core/study/flag_router.py:181 corr_prior_shrink(level=)` | **이미 구현** level='macro'→no-op | 변경 없음, **유지+검증만**. `_corr_level_of(scope)` 신규자산 매핑 확인 | macro/bond=macro level 불변 | self-test c6(`study_register.py:338`) cp_macro==base_cp |
| W3 | merit 지표 등록 | `core/brain/fred_adapter.py:64 FRED_SERIES` + yaml `indicators[].id` | DGORDER/Empire/vix_term 등록 0 | FRED 가용 series 1줄씩 추가(★`fred.get_series_info` 사전검증) + yaml indicator | `assert_no_reflexive_series`(`weight_panel.py:152`) | NaN 열 graceful + 반사성 게이트 통과 |
| W4 | judge facade 결선(채널 C) | `core/assume/judge.py:147 judge()` caller ← `study_register.py:196 prepare_judge_call` | judge() 런타임 호출 0(stock-track 전용) | caller가 prepare_judge_call dict 주입(lens_prompt/weight_card). **라이브 활성화=go-live 경계(범위 밖)** | `assert_ceiling_invariant`(`judge.py:251`) down-only | weight/lens None=무회귀(self-test c11) |
| A | 합성 PSD invariant | `core/structure/conditional_correlation.py:332~359`(belief congruence/`cholesky_ok`) | `_pd_fix` eps*eye fallback(`:353`)=silent-ish | belief를 **D 또는 BΩ'Bᵀ congruence에만** 가둠(by-construction). read-time 합성객체에 Cholesky assertion **log-and-halt(★Higham silent-repair 금지)** | 기존 cholesky_ok fallback 동작(회귀) — halt 전환 시 opt-in 경계 | audit N=합성객체 min-eig≥0 assert fire 시 belief 침범 버그 |
| B | de-risk stress-corr swap | `core/brain/regime_to_weights.py:145 cov_override` + `core/risk_gate.py` de-risk + `resolve_precedence:502` | belief cov_override만 | de-risk state 진입 시 pinned view→**사전등록 고정 stress 상관 floor** 교체(재추정 X, monotone) | KillSwitch override(budget MUST-APPLY) | ④ stress sim "de-risk 폭이 corr-stale 손실 상한 지배" |
| C/⑧ | immortality convex-leak | `core/assume/eprocess_backbone.py e_cusum` ← `weight_falsification.py:66 score_ic_breakdown_eprocess` | 단측 E-CUSUM(개선=0 floor, ★`update_controller:28` e_value saturate 경고) | **1로의 convex-leak `Ẽ_t=γ·Ẽ_{t-1}·m_t+(1−γ)`**(Ville 보존). dwell 분포 공동보정 γ | 기존 단측 reset 동작·`retract_now` effect_size 경로 | ⑧ dwell gate: P(dwell≥m) 충분 / median<m이면 decay |
| ④' | equivalence margin+sunset | `core/assume/update_controller.py:99 step`(adopt gate) + `study_register` status | adopt=`hysteresis_and_gate` 5-AND, **retract 비대칭 이미 있음** | adopt 전 TOST equivalence margin + shadow에 sunset clock(도달 시 강제 activate/reject) | `retract_now`(`:50` disjunctive fast)·RETRACT_EFFECT_HARD=3.0 | margin band 떨어지면 REJECT / sunset 무한대기 0 |
| ⑤가 | activation-side e-BH | `core/assume/update_controller.py`(activate 결정) — LORD/SAFFRON α-spending | falsification에 e-process | **activation도 e-BH(Vovk-Wang)/α-spending** 통과(per-relationship K-family selection) | 기존 falsification α-spending | activation gate에 multiplicity 보정 적용 확인 |
| ⑤다 | aggregate churn cap | `core/risk_gate.py`(MAX_TURNOVER_SINGLE 존재) | per-trade turnover cap | 사이클당 **aggregate 구조변동 cap**(regime shift가 다수 관계 동시 끊을 때 Σ 점프) | KillSwitch override 우선 | regime shift 시 turnover spike < cap |
| flag | exogenous discrete flag(채널3) | `core/brain/regime_classifier.py:150 _apply_indicator_overrides` + `fred_adapter`(T10Y2Y·BAMLH0A0HYM2) | regime override 일부 | yield-curve·HY OAS spike → regime→sleeve% 보수전환 **de-risk-only MUST-APPLY** | 포트폴리오 자산서 파생 안 됨(외생성) | flag fire 시 sleeve% 보수전환·corr 미변경 |

★게이트 환경변수(기존): `INV_R15_WEIGHTS`(corr_prior+belief), `INV_STUDY_LENS`(judge lens), `INV_CORE_GATE`(백스톱+거시 chain), `INV_UNATTENDED_FSM`(KillSwitch). 전부 default-off.

## 9. ★자산별 subagent 작업 — 핵심 + 입출력 템플릿

**핵심(무엇을 시키나)**: 각 자산의 *기존* study 산출(direction/yaml/validation) 위에서 **실측 배터리 ①~⑧을 그 자산의 relationships에 실행** → 각 relationship을 **채널 분류(unconditional static / regime-conditional / exogenous flag)** + **verdict(activate / reject / UNKNOWN)** 로 판정. ★밑바닥 재작업 금지, 신규 검증분만.

**입력 템플릿(subagent에 제공)**:
```
[자산]: {asset}
[기존 산출 — Read 후 그 위에서] :
  - study-research/{asset}/direction.md (방향·가설)
  - study-research/{asset}/study_session.yaml (블록3 relationships·블록4 weight_rules·블록5 confidence_hooks)
  - study-research/{asset}/raw/validation-*.md (기존 실측)
  - study-research/{asset}/theory-notes.md
[채널 규칙]: unconditional 20년 일별 large-n → activate/reject(영구 shadow 금지) / regime-conditional·월별 small-n → UNKNOWN+재평가
[배터리(자산 relationships에 실행)]: ① crisis-incl/excl β delta ② regime-split VIF(Simpson) ③ same-day vs lagged ④ turnover+stress-swap ⑤ marginal-precision ⑥ break-freq ⑦ wired vs np.eye OOS+equivalence margin(TOST) ⑧ dwell P(dwell≥m)
[불변식]: reject≠missing·factor-space PSD·down-only·belief→_macro firewall·sign-only+magnitude FREEZE
[금지]: 점추정 박제(magnitude FREEZE), 재작업, self-certify(독립 audit 별도)
[python]: C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe + PYTHONUTF8=1
```

**출력 템플릿(subagent가 반환)** — relationship별 1행:
```
| rel(node_a↔node_b) | 채널(uncond/regime/flag) | ①β_excl[CI] | ②VIF_split | ③lag delta | ⑤Δw vs naive | ⑦OOS vs np.eye(margin) | ⑧dwell | verdict(activate/reject/UNKNOWN) | 근거 |
```
+ 자산 요약: activate N / reject N / UNKNOWN N + 채널 배정 표 + n<30 hedge + 재귀한계(dwell-calib distinct-regime 수) 메타.

## 10. ★실제 구현 시 중요 항목 (12)

1. **중복 구현 금지** — retract 비대칭(`update_controller.retract_now`)·firewall(`flag_router.corr_prior_shrink` level)·e-process(`weight_falsification`)·eb_shrink·PD-fix는 **이미 있음**. 새로 짜지 말고 **재사용**. 신규는 convex-leak·stress-swap·equivalence margin·e-BH activation·factor-space·sunset clock·exogenous flag뿐.
2. **e_value saturation 함정** — `update_controller.py:28-29`: 엔진 e_value가 p-floor(1e-9)서 saturate(~1.6e4)→판별력 0이라 retract는 e_value 아닌 **effect_size(Cohen's d)** 씀. convex-leak ⑧ 추가 시 이 saturation과 상호작용 검증(γ-mixing이 saturate 전 작동해야).
3. **cholesky_ok fallback vs Higham-halt 충돌** — 현재 `_pd_fix` eps*eye(`:353`)=silent-ish repair. Claude "silent 금지, log-and-halt"와 충돌 → 기존 fallback을 halt로 바꾸면 **기존 동작 변경=회귀 위험**. opt-in 경계 안에서만, 기본 경로는 보존.
4. **series_ids 정렬 일관성** — `relationships_to_corr_prior`가 만드는 (p×p) 행렬 인덱스 순서 = `RegimeGlasso.fit`의 `ids_v` 순서와 **정확히 일치** 필수. off-by-index면 엉뚱한 자산쌍 상관 주입(silent 재앙).
5. **opt-in off byte-identical 회귀** — 매 wire 변경마다 `tests/test_study_pipeline.py:58`(R15/LENS toggle) + `test_sleeve_belief_cov.py:150`(R15 off=정적 무회귀) 통과 의무. off에서 import조차 안 일어나야.
6. **PIT vintage / availability-lag** — merit 지표 fetch(`weight_panel.realtime`)는 first-release + availability-month ffill(full-sample median lookahead 차단). ALFRED real-time vintage. ★FRED series_id 가용범위 박제 전 `get_series_info` 검증(empirical-claim §1.1-ext).
7. **study_id→scope→level 매핑** — `_corr_level_of(scope)`: macro/bond=macro(no-op), 그외=micro. **신규 자산 추가 시 이 매핑 정의 안 하면 default가 잘못된 channel**(firewall 누수 or 과차단).
8. **factor-space imputation 미구현** — 현 `eb_shrink`는 entry-space(corr 행렬 둘). factor-space `Σ=BΩBᵀ+D`(PSD 공짜+공통인자 1회)는 **신규 모듈**. `between_term`/Omega(`:341-359`)는 belief용이라 cross-sleeve B factor 분해는 별도 설계.
9. **KillSwitch override 경로** — turnover cap(`MAX_TURNOVER_SINGLE`) 있으나 KillSwitch가 budget override하는 경로 명시 안 됨. `resolve_precedence`(`risk_gate.py:502`)에 de-risk MUST-APPLY > turnover budget 우선순위 엮기.
10. **shadow 라벨=무기여 강제** — `StudyRegister.status()`에 **3-state(active/no-contribution(np.eye-equiv)/UNKNOWN)** 라벨 필드. "shadow=작동중" 위장 금지(§1.5 교훈). no-contribution은 라이브 결정에 0 기여 명시.
11. **version pin 미구현** — 현 facade는 study_id별 호출. **사이클당 card_version 1회 pin → 두 facade 동일 version**(coupling 없이 동기)은 신규. de-risk invalidation은 pin preempt(MUST-APPLY).
12. **reflexive 게이트 + magnitude FREEZE 이중** — `assert_no_reflexive_series`(포지션/PnL 유래 차단) + 블록4 weight_rules는 **sign-only, magnitude FREEZE**(점추정 박제 금지). corr_prior default_rho도 magnitude 아닌 sign 기반.

(부수 13: **macro/bond static corr_prior는 firewall 대상 아님**(§1.2-1) — `corr_prior_shrink` belief 차단과 별개 채널. relationships→corr_prior 주입은 belief 경로 안 거치고 직접 RegimeGlasso로. 코드상 두 경로 분리 확인.)

---

## 11. ★IC1~IC8 결선 reconcile (R9-core, 양 모델 수렴 — 이미있음·신규·deferral 3분류)

> R9-core(2026-06-01 gemini+claude 병렬) = "메커니즘은 기구현, **진짜 gap=runtime 연결**" 전제 위에서 *어떻게 결선하나*. 두 모델 8개 결정 전부 합의(모순 0). Claude가 correctness 정밀항 superset. 각 항: **결선(코드 위치)** / **3분류** / **함정** / **n<30 hedge**.

### IC1 — corr_prior 합성 (★최대 load-bearing)
- **결선**: `factor_implied_cross_cov(betas, Λ_static)`(`system_priors.py`) → **cov2corr** → `RegimeGlasso(corr_prior=structural_corr)`(`regime_to_weights.py:197`). `eb_shrink(corr_glasso, structural_corr, n_eff)`(`conditional_correlation.py:207`)이 `lam·prior+(1−lam)·glasso`로 흡수. structural=prior / glasso=likelihood (Bayesian shrinkage). 택일(if-else)은 regime 경계 불연속+분산감소 손실로 양 모델 기각 → **연속 blend**.
- **3분류**: `eb_shrink`·`RegimeGlasso`·`factor_implied_cross_cov`=**이미있음**(미wired). corr_prior 주입(`:197` 현 np.eye=★실버그)=**신규 글루**(=W2). `lam_eff` dual-uncertainty=**신규**.
- **★Claude 정밀(신규)**: `n_eff`를 glasso 표본수만 쓰지 말 것 — `lam_eff=f(n_eff_glasso, n_eff_prior)`, prior n은 SEED betas tier/SE에서 유도. low-tier(high-SE) betas면 `lam→1` 회피("노이즈를 노이즈로 수축"). + structural은 covariance라 **반드시 cov2corr 후** corr 공간 주입, vol은 분리(structural 대각을 vol로 쓰면 idio 가정이 vol-targeting에 누수).
- **함정**: `eb_shrink`가 corr만 받는지 시그니처 ★코드확인 TODO. Higham PSD는 cov 단에 걸렸으니 cov2corr 후 FP로 깨질 수 있음(개별 변환만 위험, convex blend 자체는 PSD 보존).
- **hedge**: n<30이면 data가 prior를 못 이기게 clamp(small-n서 추정량이 prior 이기는 게 흔한 silent 오염원).

### IC2 — gate-Λ vs static-Λ 라우팅 (★)
- **결선**: static-Λ(long half-life+BL/Π 수축) → `factor_implied_cross_cov`의 Λ 인자 → IC1 corr_prior(배분). gate-Λ(short EWMA+stress floor) → 배분 *이후* `risk_gate` down-only clamp. 둘은 같은 factor 혁신·같은 PIT 윈도우, half-life/shrinkage만 다름(이상적으로 `estimate_factor_cov`가 둘 다 반환).
- **3분류**: two-layer 분리=**이미있음**(`factor_cov_estimate` docstring). 어느 Λ가 어디로 가는 라우팅 결선=**신규 글루**. risk_gate clamp=**이미있음**.
- **함정**: gate-Λ를 prior로 먹이면 two-layer가 one-layer reactive로 붕괴. 파이프라인 단계 분리(static=pre-alloc corr_prior / gate=post-alloc clamp). down-only 강제: `w_final=w_alloc·min(1, gate_scale)`, scale-up 차단.

### IC3 — B(betas) 런타임 source
- **결선**: versioned **seed 테이블**(study yaml 아님 — betas는 provenance·버전 필요한 추정 산출물, IC7 연계). key=(asset, factor[, regime]) → (β̂,SE,t,n,tier). read-only handoff.
- **3분류**: `build_seed_betas` James-Stein 수축=**이미있음**. seed 테이블 provenance + tri-state + group fallback=**신규**(현 grand-fallback 오염=gold −0.508 root cause).
- **★오염차단 3종(신규)**: (1) **tri-state** `{estimated | reject(β:=0 locked) | missing(→fallback)}` — gold가 가설상 decoupled면 reject로 β:=0 lock, fallback 풀 제외. (2) **group-specific fallback**(grand mean 아닌 factor-group 평균 — gold가 equity-vol β 상속 경로 제거). (3) James-Stein target도 group mean. group n 부족 시 fallback=β:=0(독립 가정, 정직한 보수 prior).

### IC4 — shadow→active graduation owner (★)
- **결선**: `update_controller`(`:99 step`, 5-AND `hysteresis_and_gate`)가 **owner** — 한 AND = "e-process pass". e-process(`weight_falsification`+`eprocess_backbone`)=running test일 뿐 flip 권한 0. pass 시 update_controller가 StudyRegister에 state flip + bitemporal stamp. StudyRegister=dumb record.
- **3분류**: 5-AND gate=**이미있음**. e-process=**이미있음**. graduation 루프 결선(누가 읽어 flip, 주기)=**신규 글루**.
- **주기**: e-process는 연속 누적(shadow 로그마다 append), flip 판정은 **사이클 경계 1회**(IC7 pin 동기, mid-cycle 승격=pin 위반).
- **함정**: StudyRegister 자가승격 차단 — 카드 제안 study가 자기 채점=confirmation bias(독립 audit이 막으려는 바로 그것).

### IC5 — opt-in off byte-identical
- **결선**: shadow=공유상태 write 0인 read-only consumer, allocation 완료 후 snapshot에서만 동작.
- **3분류**: opt-in off 회귀테스트(`test_study_pipeline.py:58`, `test_sleeve_belief_cov.py:150`)=**이미있음**. RNG격리·FP order·golden byte-identical=**신규 강제**.
- **★구현 패턴(신규)**: (1) RNG: `np.random.default_rng(seed_shadow)` 전용 객체(global seed 차단 — 공유 stream 전진하면 off여도 downstream draw 변경). (2) cache: shadow는 frozen snapshot 히트, 공유 cov cache populate/evict 차단. (3) **FP 연산순서**: allocation 종료 → snapshot → shadow 순차(reduction에 interleave 차단). (4) **golden test**: 고정 seed+fixture로 off/on allocation 출력 `tobytes()` 해시 assert = CI 게이트(설계논증 아닌 증명). (5) IO: shadow 로깅 async/post-hoc. **계약**: allocation 출력=`(PIT inputs, pinned versions, seed)`의 pure function, shadow는 인자 아님.

### IC6 — judge 결선 (go-live 경계)
- **결선**: `prepare_judge_call`(`study_register.py:196`, side-effect 0, lens_prompt 조립+weight_card resolve+version pin) = **shadow-now** 결선 가능. `judge()`(`judge.py:147`)가 사이즈에 곱해져 소비되는 지점 = **go-live 경계**.
- **3분류**: prepare_judge_call·judge facade=**이미있음**. 소비 flip=**go-live deferral**.
- **soft 차이(main 결정)**: Claude=shadow서 실제 judge LLM 호출해 verdict 누적(calibration 확보·LLM 비용) / Gemini=shadow는 judge 미호출(엄격·저렴). go-live 경계엔 양 모델 합의. → **main 선택**(사이클 경계/subset 샘플로 비용 제한 시 Claude안 채택 권장). judge=down-only attenuator라 소비가 배분보다 안전.

### IC7 — version pin
- **결선**: derive-on-read + facade에 `as_of` 파라미터. StudyRegister 상태형 pin 메서드=**over-engineering(불요/drop)**. IC4가 graduation을 사이클 경계로 묶어 cycle-start snapshot ≈ implicit pin.
- **3분류**: facade study_id별 호출=**이미있음**. `as_of` 파라미터(값으로 내리는 최소 pin)=**신규 경량**. 상태형 pin API=**불요**.
- **★함정(신규)**: `as_of`를 ts로 resolve 시 valid-time **AS-OF decision-time**으로(="결정 시점에 valid라 믿은 것"). transaction-time으로 resolve하면 late-arriving 정정이 과거 결정에 누수=lookahead 오염. de-risk preempt는 pin 밖(gate 레이어, cut만 하므로 충돌 0).

### IC8 — FX factor 내재 (★ 코드검증=확정부재)
- **검증사실(main grep)**: `fx.py`=PIT 가치환산 전용(공분산 미접촉). `regime_to_weights` 공분산=외부주입 `returns_history`(통화-무관). ★프로덕션 유일 호출부 `coin_track_macro.py:64`가 `allocate()`를 returns_history 없이 호출 → glasso 공분산 경로 자체가 런타임 미실행(macro 산출=abstain bool+참조용 weights만 소비). 즉 KRW-홈인데 USD 슬리브 환노출이 공분산 어디에도 미반영.
- **결선**: 양 모델 **Option B 채택**(USDKRW를 6번째 explicit factor, 슬리브별 fx_β). (A)수익률 KRW 환산=기각(hedge 토글 불가+betas FX 오염+gold decoupling 재상관=one-way door). (A)+(B)혼용=이중계상 기각.
  - **glasso(likelihood)**: 모든 슬리브 **local(FX-stripped) return**(US=USD, KR=KRW, numeraire 일관 net-of-FX corr). **structural(prior)**: betas는 local return + USDKRW 6th factor(fx_β, Λ에 USDKRW vol). → **layer당 FX owner 1개**(empirical=FX제거 / structural=FX유일진입), 이중계상 0.
  - **hedge 토글**: G6 `fx_hedge:full`→fx_β:=0 / `none`→fx_β live. empirical은 토글 무관(항상 FX-stripped). gold=KRW 투자자에 부분 USD hedge라 hedge 여부가 gold diversification role 좌우(memory gold decoupling 직결).
- **3분류**: FX factor 전체=**신규**(현재 부재 확정). glasso local-return 전제=**신규 제약**. 단 returns_history 공급 자체가 선결(배분 경로 미wired).
- **hedge**: 슬리브 fx_β를 짧은 USDKRW×슬리브 overlap서 자유추정 차단(USDKRW regime shift 지배). denomination 구조로 prior 고정(full-USD≈1, gold=USD비율, hedged=0), 데이터는 n 충분할 때만 prior에서 이동.

### §11 종합 — 신규로 실제 짤 것 (나머지는 기존 재사용)
corr_prior 주입 글루(IC1 W2)·lam_eff dual-uncertainty(IC1)·Λ 라우팅 글루(IC2)·seed 테이블+tri-state+group fallback(IC3)·graduation 루프(IC4)·RNG격리+FP order+golden test(IC5)·as_of 파라미터(IC7)·FX 6th factor+local-return glasso(IC8). ★나머지(eb_shrink·RegimeGlasso·James-Stein·5-AND·e-process·two-layer·facade·회귀테스트)=전부 **이미있음, 재사용**.

---

## 12. ★독립 audit subagent 지시용 — 15축 자기완결 검토기준 (압축본)

> **용도**: 4관문 3단계(독립 audit). main은 통과편향이 있어 직접 감사하지 X(사용자 지적). subagent가 **이 §12 + 대상 자산 raw 아티팩트만으로** 독립 판정하도록, 9R 자문서 논의된 기준을 한 곳에 압축. 매 audit subagent 스폰 시 이 섹션을 그대로 전달(별도 재유도 불요).
> **제1원리(§0 AUDIT-GUIDE)**: yaml 숫자 = "사실" 아닌 **"주장(claim)"**. raw .py+데이터를 직접 재실행/정독해 재현. 합성데이터 지문(결측·갭 없음, 2020-03·2022 이벤트 부재) 검사. 재계산 불일치=hard-fail.

### 15축 = 12 study축(A~L) + 3 wire축(M~O)

**study 12축**(study-research 산출 검증, AUDIT-GUIDE 출처):
| 축 | 본다(1줄) | hard 여부 |
|---|---|---|
| A 이론실재성 | theory-notes가 실제 정독인가(저자·연도) | soft(날조인용만 hard) |
| **B 실데이터검증** | 실측 OOS Rank-IC>0.03 AND t>2.0(SE보정) | ★hard(합성·실측부재·n부족) |
| **C yaml추적성** | corr_prior/weight가 B 실측서 ±5% 매칭 | ★hard(매직넘버·재계산불가) |
| **D PIT/lookahead** | 거시=first-release vintage, 가격=익일시가 | ★hard(발표전·최종개정치) |
| E 자문환각 cross-verify | 인용 수치 원본 확인 | 조건부hard(환각 claim) |
| F 반증+기각기록 | 반증조건+기각 1건+ | 조건부hard(기각 0=p-hack) |
| G effective-N tier | N한계 숫자 명시+prior 보수화 | tier강등(차단X) |
| H 미해결의문 | confound·한계 솔직기재 | soft(공란=red flag) |
| **I 무결성·생존편향** | 상폐·split·universe PIT | ★hard(생존편향=무효화) |
| J 경제유의·비용 | 왕복 0.3% 차감 후 +알파, turnover | 조건부hard(비용後 음수면 alpha주장) |
| K 다중검정 | 시도횟수 공시+Deflated SR>1 | 조건부hard(미공시) |
| **L 통합상관 정합** | 공통인자(USD·rate·유동성) 1회 계상+PSD | ★hard(중복베팅·PSD깨짐=통합차단) |

**wire 3축 M~O**(런타임 결선 충실, §1.9 출처 — 본 wire 작업 고유):
| 축 | 본다(1줄) | Pass 증거 | hard 여부 |
|---|---|---|---|
| **M wire충실** | study 산출이 코드에 정직히 결선됐나 | (a)opt-in **off=byte-identical**(golden test `tobytes()` 해시, IC5) (b)facade call-path 추적 가능 (c)orphan inject 0 (d)cross-view monotone(어떤 뷰도 다른 뷰 부호 못 뒤집음) | ★hard(off 회귀=무효) |
| **N cross관계** | 합성 상관행렬이 수학·경제 정합인가 | (a)sign-stable (b)**read-time 합성 PSD**(Cholesky assert log-and-halt, Higham silent-repair 차단) (c)**공통인자 1회**(IC8: FX factor 이중계상 0=empirical local-return 확인) (d)tail 부호반전 점검 | ★hard(PSD깨짐·이중계상) |
| **O leakage** | 미래정보·오염 차단됐나 | (a)PIT-safe(IC7 as_of=valid-time decision-time, transaction-time 누수 차단) (b)**reject≠missing**(IC3 tri-state, gold β:=0 lock·grand-fallback 오염 0) (c)full-sample-gate→FDR 2단계 (d)availability-lag | ★hard(lookahead·reject오염) |

### IC1~IC8 결선을 audit checkpoint로 (wire축 판정 시 대조)
- **IC1**(N축): corr_prior가 `cov2corr` 거쳐 corr 공간 주입됐나? structural 대각이 vol로 누수 안 됐나? lam_eff가 prior n_eff(SEED tier/SE) 반영하나(low-tier서 lam→1 회피)?
- **IC2**(M축): static-Λ만 corr_prior로, gate-Λ는 risk_gate clamp로 분리됐나? gate-Λ가 prior에 누수 안 됐나?
- **IC3**(O축): seed 테이블 tri-state인가? reject 자산 β:=0 locked로 fallback 풀 제외됐나? group-specific fallback인가(grand mean 차단)?
- **IC4**: graduation owner=update_controller 5-AND인가? StudyRegister 자가승격 0(confirmation bias 차단)? flip=사이클 경계?
- **IC5**(M축): golden byte-identical test 존재+CI 게이트? RNG 전용 인스턴스? allocation→snapshot→shadow FP 순서?
- **IC6**: prepare_judge_call=side-effect 0? judge 소비=go-live 경계 분리?
- **IC7**(O축): as_of=valid-time AS-OF decision-time resolve? de-risk preempt가 pin 밖?
- **IC8**(N축): glasso가 local(FX-stripped) return인가? FX가 structural에만(6th factor)? A+B 이중계상 0? fx_hedge 토글이 fx_β 0/1로?

### Hard-fail 코어 (즉시 불충분/통합차단)
study: **B·C·D·I**(숫자 무효화/검증불가). wire: **M**(off 회귀)·**N**(PSD깨짐·FX 이중계상)·**O**(lookahead·reject오염). 1건이라도 위반=register 차단+보강요청.

### 채널 규칙 (relationship 분류 — verdict 전제)
- **unconditional static**(20년 일별 large-n≈5052): OOS 검정 *지금* 결정적. np.eye 못 이기면 **즉각 activate OR reject**(영구 shadow=회피, 차단). 단 ⑦ equivalence margin(TOST) — "못 이김"≠"0과 동등".
- **regime-conditional·월별 small-n**: "**UNKNOWN/INSUFFICIENT**" 정직 라벨(working facade 위장 차단)+event-driven 재평가(distinct-regime 누적 시, 달력 아님).
- np.eye-equiv 등록="무기여(no-contribution)" 정직 라벨(폐기 아님).

### 입력 템플릿(audit subagent에 제공)
```
[대상]: study-research/{asset}/ (direction.md / theory-notes.md / raw/validation-*.md / study_session.yaml / raw/*.py+데이터)
[너의 역할]: 독립 감사관. main의 self-audit·방의 self-cert 신뢰 X. raw 재계산이 판정 근거.
[제1원리]: yaml 숫자=주장. raw .py 재실행/정독 → yaml 수치 재현 확인. 합성 지문 검사(2020-03/2022 이벤트 실재?).
[검토축]: §12 15축(A~L study + M~O wire). hard 코어=B·C·D·I·M·N·O.
[IC checkpoint]: IC1~IC8 결선 대조(위 표).
[채널규칙]: uncond large-n→activate/reject / regime small-n→UNKNOWN.
[python]: C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe + PYTHONUTF8=1
[금지]: 통과편향, self-cert 수용, 점추정 박제 묵인, 합성 묵인.
```
### 출력 템플릿(audit subagent 반환)
```
[감사] {asset} — verdict: 충실 / 부분 / 불충분
- Provenance(§0): yaml 수치 raw 재계산 일치? / 합성 지문 결과
- 15축: 통과 N / 부분 M / 불충분 K (어느 축 왜)
- Hard-fail: B·C·D·I·M·N·O 중 위반?
- wire 3축 상세: M(off byte-identical?) / N(PSD+FX 이중계상?) / O(PIT+reject≠missing?)
- IC checkpoint: IC1~IC8 중 위반 결선
- Tier(G): validated alpha vs structural prior(저신뢰)
- 채널배정: relationship별 uncond/regime/flag + verdict(activate/reject/UNKNOWN)
- 판정: register 가능(충실) / 보강요청(부분·불충분, 항목 구체)
```

---

## 13. ★관문 구분 + Phase V 백테스트 검증 (사용자 framing 2026-06-01)

**두 관문 분리**:
- **(가) per-relationship 등록**: 15축 작성 → audit 15축(§12) → 통과분 등록(4관문 2~3단계). "어떤 관계를 카드로 박나".
- **(나) 구현 파이프라인**(§8~11 IC1~IC8): study 산출 런타임 배선. 검증 기준 = **자문 충실 이해 + 실제 매수/매도 신호 이상 초래 여부**(15축 audit 대상 아님, 신호 무이상이 게이트). off=byte-identical / on=신호 영향 측정.

**Phase V — 10년 백테스트 매매신호 일치성 (최종 관문, 자산별 subagent)**: ⛔**자율주행 제외 — 착수 전 사용자 방향 논의 게이트(2026-06-01 지시)**. IC0~IC9 배선 후, 각 자산별로 구현 코드가 뽑는 10년 매수/매도 타임 → 그대로 매매 시 이익 실현 가능한지 + 코드/yaml/리서치 3자 일치성 검증. 문제 시 4차원 진단((a)분석 오류 (b)코드 신호추출 오류=가중치 이상 (c)yaml 칼리브레이션 (d)배선 오류)→메인 제출→메인 통합 최종 수정. 상세 입출력 템플릿=`progress-wire-impl.md` Phase V. PIT walk-forward·왕복 0.3% 차감·실제 파이프라인 호출(재구현 금지).

---

## 14. ★reject 가설 복귀 로직 + 기각 ledger (R11 수렴, 2026-06-01 gemini+claude 병렬·조기수렴)

**문제**: "일시적 regime-conditional 연관 파탄"(증시서 흔함)으로 reject/INSUFFICIENT된 가설이 연관 회복 시 **자동 복귀하는 경로 부재**. 코드검증: 가중치 동적조정(`flag_router.tilt_weights`)은 activated 가설 신뢰도 변조만, reject 가설은 tilt 풀 밖. update_controller re-risk·study_register 상태전이 grep 0. 지표 기각 통합 ledger 부재(사유 yaml 3곳 산재). 실측 영구제외 의심 3건(eq_us_defensive H3 credit_stress n=4 방향일관 / eq_intl China credit_impulse PIT붕괴 / reit H1 long_WALT 단일 rate cycle).

**14.1 복귀 상태기계 (양 모델 합의)**: `REJECT → (trigger) → SHADOW(관찰, auto) → (adoption gate) → live`. de-risk fast(disjunctive `retract_now`) / re-risk gated(conjunctive). 복귀는 새 human surface 신설 X — shadow→live만 **기존 5-AND `hysteresis_and_gate`** 로 routing(자본 증가 transition만 gate, 10R 원칙).

**14.2 ★matched convex-leak (Claude 핵심)**: immortality 방어 `E_against`(기존 e-CUSUM convex-leak)와 **대칭 `E_for`**(복귀 증거 e-process, 동일 leak `Ẽ_t=γ·Ẽ_{t-1}·m_t+(1−γ)`). 죽지않는가설=E_against / 부활못함=모든 reject state에 E_for 경로(reachable exit, black-hole 차단) / phoenix(drift 부활)=E_for leak 차단. 신규 primitive 최소(E_for + reject_class projection만, 나머지 re-routing).

**14.3 ★burden = reject_class 분기 (Claude — "원 기준 높게"는 틀린 축)**:
- **regime-conditional·missing**(국면 미발생/n부족 power 부재 = reject≠missing 오라벨 지점): 복귀 burden = **원 adoption gate 그대로**(disconfirm 없으니 overcoming term 없음, first-time adoption과 대칭).
- **structural·evidence**(adequate power로 전국면 무관/역부호 확인): adoption gate + **overcoming term = reject 시 누적 E_against**(ledger 박제). 신규 positive가 prior disconfirmation 흡수+초과.

**14.4 ★alpha-pricing (Claude — 재탐구 차단=block 아닌 회계)**: 복귀 = reject pool sequential re-test = 다중검정. 신규 alpha budget 주면 alpha-laundering(reject→대기→재검→부활 반복). 복귀 e-process는 **최초 discovery와 동일 alpha-wealth(기존 LORD/SAFFRON)에서 인출**. class structural reject는 spent alpha 일부만 반환(leak의 FDR 버전) → structural 재제안은 비싸고 regime-draw 복귀는 쌈. leak·burden·재탐구차단 한 회계 통합.

**14.5 trigger = typed multiplex (양 모델, Claude 정밀)**: regime-draw(국면 episode 누적) / data-event(★class C=PIT-corrupt는 데이터 수정 전까지 **E_for 누적 격리** — corrupt 위 누적=lookahead=최악 false revival) / n_regime-gated(단일 draw론 structural/conditional 구분 불가 → threshold 미달 UNKNOWN 잔류, reit WALT n=1 케이스). reject_class별 리스너 분리 바인딩.

**14.6 ledger = event_ledger 확장 (★Claude 반박 채택, 신규 금지)**: 신규 ledger=두 번째 write-authority=산재 병 재발. `event_ledger`(bitemporal append-only) 신규 event type + **materialized projection**(reject 상태=decision-time as-of fold read-model). 재탐구 조회=as-of query. opt-in off byte-identical=기존 reader가 신규 type skip하는 forward-compat fold. reject event 필드: `hypothesis_id`(content-addressed=cosmetic 리네임도 충돌), `reject_class`, `reason_code`, `n_at_decision`+regime composition, `power_at_decision`(봤는데 없음 vs 못 봤음 구분), `E_against_at_reject`, `revival_trigger`(typed), `E_for_state`+leak λ, `alpha_charge`, 3 timestamp, WeightAssumptionCard 포인터, `human_gate_required`.

**14.7 운영 게이트 (양 모델)**: 탐지·E_for 누적·regime 감지·ledger projection·alert·shadow 재진입 = **auto**(risk 불변 bookkeeping/paper). shadow→live = **Human Gate**(capital 증가, 기존 adoption machinery).

**14.8 누락 위험 2 (Claude flag)**: (a) chatter/oscillation(revive→kill→revive) = two-e-process damping = hypothesis별 exponential backoff(기존 state machine 재사용). (b) 복귀 로직 falsification = 복귀 cohort OOS Rank-IC가 never-rejected baseline·random re-entry와 구분 불가 → 복귀=noise → e-CUSUM kill을 복귀 cohort group 적용.

**14.9 ★선결 코드검증(복귀 ship 전)**: registry에 live와 증명가능 격리된 **shadow tier** 존재? "shadow 재진입이 live signal로 새는 경로 있나"가 진짜 신호이상 게이트. 없으면 격리가 선행 빌드(복귀 로직 아님). λ·threshold·alpha 반환율 = n_regime 1~2서 underdetermined → conservative 초기값 + main이 false-revival-rate budget 보고 확정.

**14.10 즉시 보완**: study 3건 verdict 격상(영구reject → reject_class=regime-conditional + revival_trigger 명시). 단 텍스트 verdict 격상은 (가)등록 관문 작업(15축), 본 §14 코드(E_for·ledger·복귀기계)는 (나)구현 파이프라인. = progress-wire-impl.md IC9.
