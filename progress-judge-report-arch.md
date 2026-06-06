---
tags: [progress, inv, judge, report, architecture]
date: 2026-06-03
session: btn-Inv
plan: plan-judge-report-arch.md
---

# Progress — judge 재설계 + 리서치 통합 아키텍처

> 설계 SSOT = [.consult-judge-report-RESULTS.md](./.consult-judge-report-RESULTS.md) (5R 수렴).
> plan = [plan-judge-report-arch.md](./plan-judge-report-arch.md). 각 step = `model:` 또는 `wf:` 정확히 하나.
> ⛔ go-live=사람 게이트. push 금지. 결정론·risk_gate 무수정(오버레이만). 주식 S6=button 세션.

## Phase 0 — 설계 (완료)
- [x] **자문 5R(gemini+claude 병렬)** — `model: opus` ✅ 완료(2026-06-03). FHC primitive·2-leg·(B)강화·5중봉인·confidence 방화벽·종목 바스켓·메타카드·2-stage 리서치·능동루프 7-step·INV-1..16 수렴. raw=.consult-judge-report-RESULTS.md / .gemini-web-last.md / .claude-web-basic-last.md
- [x] **정합성 subagent 검증** — `model: opus` ✅ 완료(2026-06-03, general-purpose a4900197). 58항목→54 반영/4 부분(사유박제)/누락0/skip0, 역방향 위반0(기각 7항목 plan 미침투 확인). 무손실 반영.

## Phase 1 — 구현 (설계 검증 후 착수)
- [~] **S0 결정론 baseline 테스트(judge off)** — `model: opus` (=plan-test-readiness P2 Test2a, INV-11 기준선) ★착수(2026-06-03). 독립=stock 비겹침.
  - 조율: btn-button에 `.coord-macro-stock-fhc-20260603.md` 발송(샌드키+파일). 겹침 5구역(메타카드↔Σ_signal·FHC↔exposure card·bonus채널↔construction seam·outcome reject↔wire_falsification·mediator↔RegimeGlasso). 공유 인프라 S1~S5=button 회신 후 단일구현 합의 → 연결.
- [x] **S1 FHC 안전 인프라**(5-state machine+2-leg+INV) — `model: opus`(harness2→direct, 야간 ctx보존+신규additive) ✅ 완료(2026-06-03). `core/assume/fhc.py`: FHCard/FHCState·eval_mediator(deterministic/state_space/fail-closed)·update_outcome(previsible no-bet)·bonus_from_evalue(monotone log e clip)·transition(5-state). _DirectionalE 단측 betting e-process(MixtureSPRTEProcess 양측은 2-leg 부적합). self-test 10/10. 소유=btn-Inv 확정. 계약=.coord-fhc-contract-20260603.md
- [ ] **S2 mediator wiring**(state-space filtered-only 구독) — `wf: harness2` ⏸ **블록**(study room state-space=button RegimeGlasso 공유, button 진행 후)
- [x] **S3a breaker+fail-closed**(regime-primary breaker flag, INV-3/9) — `model: opus` ✅ 완료. bonus_channel.py `breaker_tripped` + 천장 누락 fail-closed. (IOC ladder 실행=INV-8=go-live downstream)
- [x] **S3b bonus emission**(w=clip(L1+Σbonus, 천장C), INV-1/4) — `model: opus` ✅ 완료. `core/assume/bonus_channel.py` size_with_bonus + AssetSizing. (B)강화 구현(L1 초과·천장C cap). self-test 7/7.
- [ ] **S4 능동 애널리스트 루프**(7-step+Opus pre-mint audit) — `wf: harness2`
- [ ] **S5 리서치 통합**(2-stage 카드발권+RAG 하이브리드, VaultVoice 재사용) — `wf: harness2`
- [ ] **S6 종목 바스켓**(룰코어 스크린+딥모델 비교선택+메타카드, KIS) — `→ button 세션`

## S0 baseline 결과 (2026-06-03, .p2-test2a.py 실행, coin 단일자산)
- BuyHold: OFF −1.65% / ON −0.17% (gap +1.5pp). SMAcross: OFF −64.4% / ON −7.5% (gap +56.9pp).
- attribution: gross median 0.558(vol-target OK)·lo-clip 0%·reject 0~1·judge final 1.0(coin bypass)·**position median 0.1=MAX_WEIGHT_SINGLE 10% cap binding**.
- ★진단: "on≪off=코드결함" 가설 **역전**(on≫off) → 코드 사이징=방어 오버레이(손실원 아님). 진짜 손실=**방법론(SMA whipsaw=신호설계)**. INV-11 off=byte-identical 보존.
- 잔여: substrate on(멀티에셋 macro view+regime) 주입 variant = RegimeGlasso 공유라 button 연결 후. coin baseline은 확보.

## Working Notes
> [ckpt-202606041XXX:btn-Inv S4/S5 정보파이프라인 자문 수렴 → plan 반영]
> ★**gemini-web+claude-web 병렬 자문 1R 강수렴**(.gemini-web-last.md / .claude-web-basic-last.md): **"텍스트는 가설 생성만 하고, 잔차 수익률 공간이 가설을 판정한다"** 한 원칙으로 두 모델 수렴. 새 의문 비생성 → 1R 종료. **3 핵심 반영(plan §3 S4/S5)**:
> (1) **Q2 호출빈도**: daily batch **폐기** → 정보델타(retrieval 임베딩 novelty 임계초과) 트리거 + 생성/승격 분리(up 지연 e-value / down 즉시 = down-only 정합). 효과 3=유령회전(phantom turnover) 제거 + FDR 예산(LORD++ α-spending 매일소진) 절약 + 비용절감. ★현 설계 **최대 약한고리** 정정.
> (2) **Q1 리포트 편향**: 별도모듈 X, 기존 불변식 흡수 — surprise/revision 공간만(level 금지)·한국 매도의견 희소→down-only 매핑·톤 2회 디민(애널리스트 FE + 동시점 횡단면)·선반영=발간 CAR통제+bitemporal PIT가 RAG stale 누수 차단. (Loughran-McDonald 2011, Michaely-Womack 1999)
> (3) **Q3 직교성**: FWL 스패닝 회귀 발권게이트("잔차 수익률공간 α≠0 못 보이면 가설 아님", MOVE⊥VIX 흡수판정 공식화) + 국면 interaction(무조건부0/조건부 알파=최고가치) + 팩터타이밍 vs 종목선택 분해. (GRS 1989, Kelly-Pruitt-Su 2019)
> ★**사용자 논의(대부분 기존 설계와 일치)**: 정보소스=정량(EDGAR/pykrx/공시) + 정성(리포트 RAG) / 카드 3겹 기준=사전 study 검증룰 + 정성 촉매(RAG) + 사후 e-value 채점 / 7팩터=바닥 좌표계(systematic) vs HBM류=잔차 테마(idiosyncratic, 직교 검증 통과분만). 사용자 RAG 구상(리포트 요약→BGE→LLM 발권)=S5 설계와 수렴 확인. ⛔ S2/S4/S5 = button 합류 + go-live 선결 불변.
>
> [ckpt-202606040XXX:btn-Inv core 정교화 2건 완료(67 passed) — chatter backoff 통합 + episode-LOO]
> ★**완료(검증됨)**: 핸드오프 §5 미서명 "core 정교화 잔여"(btn-Inv 단독 가능) **2건 집행** → `tests/assume/ 67 passed`(기존 63 + 신규 4). **(1) ChatterBackoff 통합**: `transition`에 `chatter_backoff`(reject_recovery.ChatterBackoff 재사용)+`now_tick` opt-in 주입. revived→vacated 시 `record_kill`(지수 cooldown) → vacated→revived 직전 `can_retry` 게이트 → flapping noise 추격 차단(§14.8a). revival_cap(hard limit)과 보완(cap 전 시간 간격↑). **(2) episode-LOO**: `_DirectionalE`에 `_log_factors`+`e_value_loo`(양 기여 최대 단일 tick 제거) → `FHCState.e_value_loo` 노출 + `transition(require_loo_robust=True)` 게이트(단일 outlier episode 제거 후 e≥thr 요구, empirical-claim §1.2 n<30). 검증 e=24.3≥20>LOO=18.7.
> ★**INV-11 byte-identical 입증**: 신규 3 param 전부 None/False fallback → 기존 63 passed 불변 + `test_chatter_backoff_none_byte_identical` 명시 케이스. additive·호출처 0·결정론/risk_gate 무수정 유지. fhc.py self-test 12/12 PASS.
> ★**다음**: ② 코인 Markov ex-ante(별 트랙, macro_vol_transfer 승격 관문) / ③ 커밋 정리. S2/S4/S5 = button 합류+go-live 선결(불변).
>
> [ckpt-202606032210:btn-Inv INV-12 회귀 편입 완결(63 passed) + 트랙 상태 확정]
> ★**완료(검증됨)**: 직전 ckpt "남은 단 1 step = pytest 63 passed" **실행 완료** → `tests/assume/ 63 passed in 3.00s`(58 + fhc_fdr 5). INV-12 회귀 편입 **완결**. 자산무관 core 3모듈(`fhc.py` S1 / `bonus_channel.py` S3 / `fhc_fdr.py` INV-12) = 빌드+회귀 전부 닫힘, additive·호출처 0(go-live 시 소비)·결정론/risk_gate 무수정.
> ★**다음 재개점 = button(주식 S6) 회신 대기**: S2 mediator(state-space=button RegimeGlasso 공유)·S4 능동루프·S5 리서치 = button 합류 + go-live 게이트 선결로 단독 진행 불가. btn-Inv 단독 가능 잔여 = 코인 Markov ex-ante(별 트랙) 또는 core 정교화(reject_recovery 트리거 통합·_DirectionalE 정밀화).
> ★**자문 누락 점검(이 ckpt)**: plan §1(D1~D11=C1~C12 매핑)·§2(INV-1..16=C13)·§3(S0~S6=C14) 전부 `.consult-judge-report-RESULTS.md` 포인터 보유. ★빠졌던 것=**C9 "결정론이 못 푸는 6유형"**(①regime-break 구조모델 무효 ②value-trap 판별 ③cross-source 합성 ④신규 가설 생성 ⑤이산 이벤트 ⑥instrument 선택)=S4 능동루프 7-step 존재이유 → plan §3 S4에 포인터 박음. C16 최종변환 한문장 = 핸드오프 자문종합 반영.
> ★**별 트랙(같은 세션)**: 코인 `coin_ssr_oscillator` ledger status drift 정정(candidate→rejected_provisional, 본문·progress 결론과 정합). 코인 신규지표 라운드(M4 5종+babyplace 4종) ledger 박제 완결 재확인. **압축내성 핸드오프 = `handoff-judge-fhc-arch-20260603.md`**(자기완결 6섹션).

> [ckpt-202606032130:btn-Inv INV-12 FDR firewall wire 완료·검증]
> ★**완료(자율, 검증됨)**: INV-12 alpha-wealth FDR firewall = `core/assume/fhc_fdr.py`(FDRFirewall·_layer_of·per-layer ELOND·test_confirm[카드당1회+pre-filter+layer고정분할]) + `fhc.py` transition(`fdr_firewall=None` param + minted 분기 `confirm_e_ok` 교체, None=고정임계 byte-identical fallback). **self-test 6/6 PASS**(firewall None fallback·pre-filter budget절약·강e confirm·INV-12 layer격리 macro/basket·double-spend 캐시·multiplicity 통제 FDR0≤고정20).
> ★**자산무관 core 3모듈 완결**: fhc.py(S1)+bonus_channel.py(S3)+fhc_fdr.py(INV-12). 전부 additive·호출처 0(go-live 시 소비)·결정론/risk_gate 무수정.
> (1) 마지막 결정: INV-12 옵션 주입 방식(기존 고정임계 fallback 보존). _DirectionalE 단측 e-process 유지. ELOND 재사용(eprocess_backbone).
> (2) 다음 의도(재개점): **(a) 회귀 confirm ✅완료**(pytest tests/assume **58 passed**, INV-11 보존). **(b) polish 진행중** = `test_fhc_core.py`에 `from core.assume.fhc_fdr import FDRFirewall` import **추가됨**(미사용=valid, 58 passed 유지). **append ✅완료**(fhc_fdr pytest 5개: test_fdr_none_fallback/prefilter_no_budget/layer_isolation/double_spend_cache/multiplicity_control + `_state_e` helper. 깨진 lambda 1블록 수정 완료). ★**남은 단 1 step(다음 세션 첫 행동)** = `python -m pytest tests/assume/ -q` 실행해 **63 passed** 확인(현 58 + fhc_fdr 5). 통과 시 INV-12 회귀편입 완결. **STATUS**: resolved (2026-06-03, 63 passed in 3.00s 확인 — 후속 ckpt-202606032210 흡수). 그 다음 S2/S4/S5 = button RegimeGlasso 합류+go-live 게이트 선결(SACRED, 야간 진행 불가).
> (3) 동기화 필요: button=core API(fhc/bonus_channel/fhc_fdr) 어댑트 통지함. go-live·push 미접촉. plan-test-readiness P3/P5 흡수. commit 미실행(push 금지).

> [ckpt-202606032055:btn-Inv INV-12 FDR firewall wire 진행중(재개점)]
> ★완료 유지: S1 `core/assume/fhc.py`+S3 `core/assume/bonus_channel.py`+`tests/assume/test_fhc_core.py`(17). tests/assume **58 passed**. button API 통지 완료.
> ★**진행중 = INV-12 alpha-wealth FDR firewall**(confirm 게이트 multiplicity 통제, 고정20.0 임계 → ELOND 동적). **현 상태**: `fhc.py` transition() 시그니처에 `fdr_firewall=None` param 추가 완료(미사용=valid, 기존 58 passed 무영향).
> ★**재개 3-step(정밀)**:
>   (1) `fhc.py` minted 분기 confirm 조건 교체: `confirm_e_ok = fdr_firewall.test_confirm(card, e_conf) if fdr_firewall is not None else e_conf >= card.confirm_e_threshold` → `elif (holds and confirm_e_ok and (graduation...)):`. transition docstring에 fdr_firewall 1줄.
>   (2) 신규 `core/assume/fhc_fdr.py` = `FDRFirewall(alpha=0.05)`: per-layer ELOND(`from core.structure.eprocess_backbone import ELOND`), `_layer_of(scope)`(sector→basket / macro·global→macro / else asset), `test_confirm(card, e_value)`= ①card.card_id 캐시(`self._decided`)면 반환(카드당1회 double-spend 방지) ②e_value<card.confirm_e_threshold면 False(pre-filter, budget 미소비) ③`self._ledger(layer).test(e_value).reject` 캐시·반환. INV-12 고정분할(layer별 별 ledger, cross-boundary 0). `stats()`.
>   (3) `test_fhc_core.py`에 4 추가: firewall None=기존동작 / 다수카드 multiplicity 통제(약 e는 reject) / macro vs sector 별 ledger 격리 / pre-filter+double-spend 캐시. → pytest 실행(목표 21+ passed 회귀0).
> ★ELOND.test(e_value)→ELONDDecision(reject=e·α_t≥1, alpha_t=α·γ_t·(n_disc+1), 호출당 t++·reject시 n_disc++). γ_t=(6/π²)/t².
> (1) 마지막 결정: INV-12를 confirm 게이트에 옵션 주입(기존 fixed 임계 fallback 보존=byte-identical). _DirectionalE 단측 e-process 유지.
> (2) 다음 의도: 위 재개 3-step 완료 → S1/S3/INV-12 = 자산무관 core 완결. 이후 S2/S4/S5는 button RegimeGlasso 합류+go-live 게이트 선결(SACRED, 야간 진행 불가).
> (3) 동기화 필요: button=core API(fhc/bonus_channel) 어댑트 통지함. go-live·push 미접촉. plan-test-readiness P3/P5 흡수.

> [ckpt-202606032010:btn-Inv S1+S3 core 완성·검증 / S2·S4·S5 블록]
> ★**완료(자율, 야간)**: S1 `core/assume/fhc.py`(FHCard·FHCState·2-leg·5-state·INV) + S3 `core/assume/bonus_channel.py`(size_with_bonus·(B)강화·INV-1/3/9) + `tests/assume/test_fhc_core.py`(17 pytest). **tests/assume 58 passed 회귀 0**(INV-11 신규파일·importer 0·__init__ 무수정 by construction).
> ★**core API 시그니처**(button plug-in용, .coord-fhc-contract §4 약속): `eval_mediator(spec, observable_value=None, *, posterior_holds=None)→MediatorState` / `update_outcome(state, signal_z, mediator_holds)` / `transition(card, state, *, mediator_state=None, graduation_decision=None)→FHCState` / `bonus_from_evalue(card, state)→float` / `size_with_bonus(l1_weights, card_states, ceilings, *, breaker_tripped=False)→{asset:AssetSizing}`. equity exposure card = `FHCard(scope="sector", outcome=OutcomeSpec("cs_rank_IC"), targets=(...))`.
> (1) 마지막 결정: S1/S3 direct opus 빌드 완료(harness2 야간 미감독 위험 회피). _DirectionalE 단측 e-process(양측 MixtureSPRTEProcess는 2-leg 부적합)=설계 정정. (B)강화=L1 초과·천장C hard cap 동작 검증.
> (2) 다음 의도: **S2/S4/S5 블록 상태** — S2 mediator=study state-space(=button RegimeGlasso 공유, button 진행 후 연결). S4 능동루프=LLM 소환(go-live 경계). S5 리서치=RAG(VaultVoice). → button 회신(단일구현·ETA) + go-live 게이트 전까지 진행 불가. 독립 가능 잔여=코인 트랙 Markov ex-ante(별건) 또는 S1/S3 정교화(reject_recovery 트리거 통합·online_fdr alpha-wealth INV-12 wire).
> (3) 동기화 필요: button=core API로 exposure card 어댑트(psmux 통지함). go-live·push 미접촉 유지. plan-test-readiness P3/P5 흡수.

> [ckpt-202606031840:btn-Inv S1 착수+button core소유 통보 완료]
> ★**button 통보 2건 발송 완료(psmux btn-button + 파일)**:
>   1. `.coord-macro-stock-fhc-20260603.md` = 겹침 5구역 매핑(메타카드↔Σ_signal·FHC↔exposure card·bonus채널↔construction seam·outcome reject↔wire_falsification·mediator↔RegimeGlasso) + 정렬요청.
>   2. `.coord-fhc-contract-20260603.md` = 단일 FHC 계약(§2 schema·§3 5-state lifecycle·§4 bonus API·§5 INV). ★**소유 확정 통보**: btn-Inv가 core/assume/ FHC core 단일 소유·구현(사용자 결정 "주식 리서치 한세월이니 너가 먼저"), button=core 짓지 말 것+산업 리서치 계속+나중 bonus API plug-in. button 회신="정렬 동의·2벌 회피 합의"(받음).
> ★**S1 설계 발견(기존 인프라 조합=2벌 회피)**: FHC core는 신규 통째 구현 아님. 기존 재사용 = `card_contract.AssumptionCardLike`(Protocol, falsification_metric 필수 게이트=FHC 만족/확장) / `reject_recovery.py`(IC9 부활: RejectClass·evaluate_recovery·should_trigger_revival·ChatterBackoff·content_address) / `weight_falsification.py`(e-CUSUM PRIMARY kill=outcome reject leg) / `graduation.py`(evaluate_graduation 5-AND=confirm 전이) / `structure/online_fdr.py`(LORD++ alpha-wealth=FDR firewall INV-12) / `structure/eprocess_backbone.py`(e-value/log-wealth) / `structure/hierarchical_fdr.py`(sector sub-family). **FHC가 새로 더할 것 4개만**: (a)2-leg mediator gating(전제 관찰량 holds/fails, alpha-wealth 미소비) (b)vacate state(confirmed→mediator fails=보너스 suspend, 기존 reject와 별개) (c)bonus 채널(L1+bonus≤천장C, realized_bonus=monotone(log e-value) clip) (d)통합 FHC schema(.coord-fhc-contract §2)+5-state machine 조립.
> (1) 마지막 결정: S1=harness2 아님 **direct opus 빌드**(야간 ctx보존+신규 additive+계약확정+INV-11 자명). S0 baseline 완료(코드 사이징=방어, 손실=방법론). 
> (2) 다음 의도: **core/assume/fhc.py 작성**(위 기존 7모듈 조합 + 신규 4). 인터페이스 = card_contract Protocol 확장. → `bonus_channel.py`(emit_bonus·size_with_bonus clip C) → `tests/assume/test_fhc.py`+`test_bonus_channel.py`(verifier 대체 엄격검증). additive·off byte-identical(INV-11)·risk_gate 무수정·go-live 미접촉·push 금지. 미읽음=reject_recovery/graduation/weight_falsification/eprocess_backbone 본문 시그니처(작성 전 Read 필수).
> (3) 동기화 필요: button=exposure card를 FHC scope=sector 어댑트(별 schema 금지). core bonus API 시그니처 확정시 btn-button 통지. S2 mediator=study state-space 구독(filtered-only). S6 종목=button. plan-test-readiness P3(judge)/P5(리포트)는 본 plan으로 흡수.

> [ckpt-202606031730:btn-Inv judge/리서치 아키텍처 5R 자문 수렴+설계확정]
> (1) 마지막 결정: FHC primitive로 전부 수렴. 강화=(B)안(L1 초과·천장 C가 진짜 불변식·신규 파라미터 0)+5중봉인(확정카드/천장cap/시간감쇠/게이트하위/regime-primary breaker). confidence 방화벽(self-conf→attention/e-value→capital). 종목=룰코어 분산바스켓→딥모델 ordinal 비교선택(바스켓 틸트 카드). 리서치=2-stage 카드발권+VaultVoice 재사용. 능동루프 7-step. INV-1..16(core=1·3·11·16). 구현 7단계(S0 baseline→S1 안전인프라→S2 mediator→S3a off-switch선/S3b bonus→S4 능동루프→S5 리서치→S6 종목=button).
> (2) 다음 의도: 정합성 subagent(raw C1~C16 ↔ plan/progress 매핑 누락0) → 사용자에 전/후 흐름 기능별 쉬운 설명. 이후 S0=plan-test-readiness P2 Test2a 착수.
> (3) 동기화 필요: 주식 S6=button 세션에 동일 FHC 설계 공유. plan-test-readiness P3(judge 재설계)/P5(리포트)가 본 plan으로 흡수·구체화됨(과소명세 정정).
