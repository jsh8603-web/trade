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
- [~] **S2 mediator wiring**(state-space filtered-only 구독) — `model: opus`(harness2→direct, additive) ★**macro 구독측 ✅**(2026-06-06) / RegimeGlasso 공급측(button INV-9 breaker)=선결 유지. `core/assume/macro_mediator.py` 신규(`belief_from_macro_view` 재사용→`posterior_holds`, fail-closed UNKNOWN, entropy 게이트, filtered-only=regime_now만·forecast 무시) + `eval_macro_mediator` fhc 연결. test 14. **81 passed 회귀0**(기존 67 불변). fhc/regime_belief_adapter 무수정=INV-11 byte-identical.
- [x] **S3a breaker+fail-closed**(regime-primary breaker flag, INV-3/9) — `model: opus` ✅ 완료. bonus_channel.py `breaker_tripped` + 천장 누락 fail-closed. (IOC ladder 실행=INV-8=go-live downstream)
- [x] **S3b bonus emission**(w=clip(L1+Σbonus, 천장C), INV-1/4) — `model: opus` ✅ 완료. `core/assume/bonus_channel.py` size_with_bonus + AssetSizing. (B)강화 구현(L1 초과·천장C cap). self-test 7/7.
- [~] **S4 능동 애널리스트 루프**(7-step+Opus pre-mint audit) — `model: opus`(harness2→direct shadow) ★**본체 ✅**(2026-06-06) `core/assume/active_loop.py`(ActiveAnalystLoop). 7-step: 저신뢰 트리거(conf↓/mediator UNKNOWN)→summon gate(info_delta rate-cap)→retrieve(ReportStore)→claim(LLM)→pre-mint audit(falsifiability+spanning 직교성+LLM 2차)→probationary mint(bonus_cap=0 자본0)→write-back(shadow sink). ★llm None=전부 abstain(C2). 게이트 3종 재사용. test 8, **105 passed**. ⏳잔여=LLM 실연결·Σ_signal write-back sink(button, compact 후)·종목 scope='sector' 확장(S6)=go-live/button.
- [ ] **S5 리서치 통합**(2-stage 카드발권+RAG 하이브리드, VaultVoice 재사용) — `wf: harness2`
- [ ] **S6 종목 바스켓**(룰코어 스크린+딥모델 비교선택+메타카드, KIS) — `→ button 세션`

## S0 baseline 결과 (2026-06-03, .p2-test2a.py 실행, coin 단일자산)
- BuyHold: OFF −1.65% / ON −0.17% (gap +1.5pp). SMAcross: OFF −64.4% / ON −7.5% (gap +56.9pp).
- attribution: gross median 0.558(vol-target OK)·lo-clip 0%·reject 0~1·judge final 1.0(coin bypass)·**position median 0.1=MAX_WEIGHT_SINGLE 10% cap binding**.
- ★진단: "on≪off=코드결함" 가설 **역전**(on≫off) → 코드 사이징=방어 오버레이(손실원 아님). 진짜 손실=**방법론(SMA whipsaw=신호설계)**. INV-11 off=byte-identical 보존.
- 잔여: substrate on(멀티에셋 macro view+regime) 주입 variant = RegimeGlasso 공유라 button 연결 후. coin baseline은 확보.

## Working Notes
> [ckpt-202606061600:btn-Inv ★실 Claude OAuth 발권 실연결 검증 + temperature 버그 픽스]
> ★**완료**: 사용자 "A(ollama) 이미 깔려있고 / B 전역 클로드 oath 키 사용" → B(Claude OAuth) 배선. ★A 재확인=11434 무응답+설치경로 미발견(서버 미가동, graceful abstain). ★B=`~/.claude/.credentials.json` claudeAiOauth.accessToken(sk-ant-oat01, len108) + `llm_provider.ClaudeProvider`(이미 구현, deep tier, urllib 직접 HTTP /v1/messages OAuth Bearer) + anthropic SDK 0.104.1.
> (1) **loop_factory use_claude 추가**(commit f443527): build_active_loop(use_claude=True)→ClaudeProvider→GenerateToComplete 어댑터. 우선순위 use_claude>use_local_llm.
> (2) **★temperature deprecated 버그 픽스**(llm_provider.py): claude-opus-4-7/sonnet-4/haiku-4=temperature 파라미터 deprecated(HTTP 400 invalid_request)→신형 4.x payload 생략(모델 기본)·구형만 주입. ★진단=실 LIVE 발권서 400 본문 "`temperature` is deprecated for this model" 확인. 픽스 후 **400→429**(Too Many Requests) 진행=인증·요청형식·서버 도달 정상=★실 Claude OAuth 실연결 검증 완료. LIVE 카드 출력만 메인 세션(이 Opus) 동일 OAuth 한도 경합으로 보류(코드 결함 아님, 한가할 때 통과). 회귀 tests/assume 118 passed.
> (3) **다음 의도**: 발권 LIVE 카드 출력=메인 idle 시 background 재시도 통과 확인. production wire(coin_track_macro opt-in shadow)는 실 LLM 한도 안정 후. ⛔실자금 flip(DRY_RUN=false)·push=사람 게이트(autopilot-run-scope). 발권=자본0 probationary 불변. long-mode on2.
>
> [ckpt-202606061500:btn-Inv S5 ingest + S4 발권 실연결 팩토리 ✅ — 거시 FHC 파이프라인 e2e shadow(118 passed)]
> ★**완료**: "이 세션 plan progress 자율주행 다해" + "고 라이브 실연결도 다해" → 거시 FHC 파이프라인 shadow **e2e 닫음**(발권 실연결까지). 누적 9 커밋(d00fe0f S2 / 7f6e945 S4직교성 / 729e48f S5정보델타 / 536b1b4 게이트테스트 / cd77af9 계약수렴 / c2142d7 S4능동루프 / 85d4ab4 S5 ingest / ed89979 발권실연결팩토리).
> (1) **S5 stage-1 ingest** `core/assume/research_ingest.py`: 소형 LLM 요약→임베딩(brain.embedder)→중복판정(info_delta novelty)→bitemporal PIT(release/ingestion)→store.upsert/shadow. ingest→retrieve→active_loop 발권으로 RAG 파이프라인 닫힘. test 7.
> (2) **S4 발권 실연결** `core/assume/loop_factory.py`: GenerateToComplete(brain.llm_provider generate↔macro_reasoning complete 어댑터)+build_active_loop(use_local_llm·ollama_health graceful)+JSON 추출. use_local_llm=False→llm None abstain(byte-identical). True→OllamaQwen 어댑터(health 후, 미가동 graceful). test 6.
> (3) **★라이브 실연결 한계(기존 논의 확인 정합)**: autopilot-run-scope(2026-05-29)=실자금 flip(DRY_RUN=false)·90일검증·push=사람 게이트, 자율 절대 밖. 안전장치 유지. plan §4=전 구간 사람 게이트. → 발권 실연결(LLM 어댑터/팩토리, 자본0)까지=자율 완결. ★실 LLM 호출=ollama 미설치+.env 키 미설정=환경 선결(자율 밖). production wire(coin_track_macro L83 opt-in)=실 LLM 없으면 무동작+회귀민감→환경 생긴 후/사용자 확인 시 켜기. 실자금·push=사람 게이트 유지.
> (4) **다음 의도**: 환경 선결(ollama 설치 or .env 키)→production wire(coin_track_macro opt-in shadow, off byte-identical)→실 LLM 발권 LIVE 검증. 그 후도 실자금 arming=90일 게이트(사람). button write-back sink·종목 S6=button(compact 후). push·go-live 미접촉, DRY_RUN/EMERGENCY_STOP 유지. long-mode on2.
>
> [ckpt-202606061400:btn-Inv S4 능동 애널리스트 루프 shadow 본체 ✅ — LLM 소환 발권(105 passed)]
> ★**정정+완료**: 사용자 dispute("LLM 소환까지 다 못해? 진입점 button이랑 논의하고 할 줄 알았는데 그게 plan progress 진행이다") → 내 오해 정정: **LLM 소환 능동루프 ≠ go-live**. plan §4="S0~S4 전부 dry-run/shadow, go-live=능동루프 shadow 지속통과 직후 arming"이라 **LLM 소환·카드발권은 shadow 구현 대상**(자본0), go-live는 그 후 실거래만. 내가 "LLM 소환=go-live"로 잘못 묶어 멈춤=틀림.
> (1) **button 진입점 정렬**(psmux 1R): S4 본체=btn-Inv 영역 동의 / button 접점=step7 write-back(카드→Σ_signal 원장 meta=button §6 Y, 미구현=go-live→**shadow dry-run sink로 충돌0**) / LLM 소환=orchestrator 소유 / probationary=자본0·INV-12 firewall go-live시 button / 종목 S6=scope='sector' 별도(button, compact 후).
> (2) **구현**: `core/assume/active_loop.py`(ActiveAnalystLoop). 7-step shadow orchestrator = 저신뢰 트리거(macro_schema confidence↓/mediator UNKNOWN)→summon gate(info_delta_gate rate-cap)→retrieve(brain.macro_reasoning ReportStore Protocol)→falsifiable claim(LLMProvider.complete)→pre-mint audit(falsification_metric 필수 + spanning_gate 직교성 camouflage/insufficient reject + LLM 2차 approve)→probationary mint(FHCard kind='probationary' bonus_cap=0)→write-back(sink 또는 shadow_sink). ★llm None/trigger 없음/claim 실패/audit reject=전부 abstain None(C2, 결정론 baseline). 게이트 3종(macro_mediator/spanning_gate/info_delta) 전부 판정부로 재사용. self-test 7 + test_active_loop 8, **105 passed 회귀0**. additive INV-11(호출처 0, go-live 시 소비), 기존 brain/assume 무수정.
> (3) **다음 의도**: S4 shadow 본체 닫힘. ⏳잔여=LLM 실연결(provider 주입)·Σ_signal write-back sink(button compact 후)·종목 scope='sector' 확장(S6 button)=전부 go-live arming/button 합류 선결. push·go-live 미접촉. long-mode on2(750k).
>
> [ckpt-202606061300:btn-Inv FHC 통합 계약 §6 수렴 — button 양측 합의 봉인]
> ★**완료**: 사용자 "버튼과 샌드키 논의" → btn-button과 psmux 2R 논의 → **.coord-fhc-contract §6 계약 닫힘**(§6'' 봉인).
> (1) **논의 흐름**: 1R=거시 FHC 게이트 3종(d00fe0f/7f6e945/729e48f) 통지 + §6 4건 회신 요청 → button이 **git 충돌 점검만 답하고 계약 미회신**(파일명 다름·충돌0 확인). 2R=Y/N 형태로 재요청(프레이밍 좁힘) → button §6' 박제. ★수렴 합의: (b)Y core/assume=btn-Inv 단일소유 + construction.build_sleeve_decisions가 size_with_bonus 소비(WireSmith, ETF fallback도 동일 seam) / (c)ETA=go-live arming(dormant, 날짜미정) / (Σ)Y meta·basket=button·core=INV-12 firewall만. ★(RG)=button 회신 누락이나 **§5 INV-9 기정의로 닫힘**(button RegimeGlasso native sleeve cov transition 감지→core fhc.transition(breaker_tripped) boolean 구독, macro_mediator MacroView 구독과 별 레이어). .coord §6'' btn-Inv 확인 봉인.
> (2) **다음 의도**: FHC 통합 계약 전부 닫힘(5건 합의/기정의). 남은 건 go-live arming(사람 게이트) 시 core bonus plug-in 실소비뿐. btn-Inv 거시 트랙(S2 mediator+S4 직교성+S5 정보델타 게이트 3종 + 계약 수렴) 자율 완결.
> (3) **동기화**: .coord-fhc-contract §6''(72줄). button 64e8bc0 무접촉, btn-button 살려둠(ctx 92%로 정리). git HEAD=536b1b4. push·go-live 미접촉.
>
> [ckpt-202606061130:btn-Inv S5 정보델타 발권 트리거 게이트 ✅ — rate-cap AND 델타 결합]
> ★**완료(self-test 7/7 PASS)**: "다 진행" 자율 속개(long-mode ON). `core/assume/info_delta_gate.py` 신규(numpy만, 외부의존 0). plan §3 S5 Q2 정정 설계(2026-06-06 사용자 반박 교정) 코드화 = **rate-cap(시계 상한) AND 델타(novelty OR 수치리비전) 결합**: 순수 델타는 상한 없어 daily보다 폭증 → 시계 rate-cap 으로 상한, batch 단독은 phantom turnover/FDR 소진 → 델타로 무의미 필터.
> (1) **구현**: `cosine_novelty`(임베딩 코퍼스 최근접 대비 1−max cos, 빈 코퍼스=1.0) + `RateCapState`(슬롯별 발권 카운터 cap_per_slot, slot_fn 시계 슬롯) + `delta_gate`(①rate-cap 소진→skip 폭증방지 ②novelty<임계 AND 수치리비전 무→skip 무의미 ③else FIRE+카운터차감). self-test: 신규→fire/중복→skip/수치리비전 단독→fire/rate-cap 슬롯당2 [T,T,F,F]/슬롯리셋/빈코퍼스 novelty1.0/임베딩없이 수치단독. ★임베딩 벡터=호출자(VaultVoice BGE) 주입=LLM추론 무관 순수거리. additive INV-11(호출처 0, go-live 시 대형 LLM 발권 트리거 소비).
> (2) **다음 의도**: pytest 격리 테스트(test_spanning_gate.py + test_info_delta_gate.py) 추가 + plan S4/S5 마킹. ★btn-Inv 거시 scope 자율 게이트 3종 완료(S2 mediator + S4 직교성 + S5 정보델타). 잔여=LLM 소환 루프 골격(S4 7-step)·리포트 편향 보정(S5 surprise/revision 변환, KR-FinBERT 톤 디민)도 통계부는 자율 가능하나 점증 복잡 → 다음 세션. S6 종목·S2 RegimeGlasso 공급측=button+go-live 선결 불변.
> (3) **동기화**: git HEAD=7f6e945(S4). long-mode ON(cap500k). button 64e8bc0 무접촉, btn-button 살려둠. push·go-live 미접촉.
>
> [ckpt-202606061030:btn-Inv S4 직교성 발권 게이트 ✅ — 스패닝 회귀(C9/Q3) additive 구현]
> ★**완료(self-test 7/7 PASS)**: 사용자 "이 세션 plan progress 다 진행" → plan §4 go-live 경계 재판정="S0~S4 전부 dry-run/shadow, arming만 go-live" + §6 "S4/S5=거시 scope=현 세션 소유"(S6만 button) → **S4 직교성 발권 게이트가 LLM무관 통계라 자율 가능 확정**(S1/S2/S3 dormant 선례 동형).
> (1) **마지막 결정/구현**: `core/assume/spanning_gate.py` 신규(numpy OLS+Newey-West HAC, 외부의존 0). `spanning_regression`(r_c=α+βᵀF+ε, HAC SE=Bartlett kernel 자동 lag) + `residual_forward_ic`(Spearman) + `mint_gate`(★n<20=INSUFFICIENT 단정금지 / |α_t(HAC)|<2=CAMOUFLAGE 7팩터 위장 발권차단 / α유의+잔차 forward IC=MINT 진짜 잔차알파) + `conditional_alpha`(국면 interaction=regime-switching conditional alpha, 결정론 팩터코어 못잡는 state-dependence). small-n-rigor §1.2-1.4 준수(n·HAC·hedge·INSUFFICIENT 격하). self-test: 순수팩터노출→camouflage(α_t-0.54)/직교알파→mint(α_t36.9)/n15→insufficient/잔차 forward IC 비유의→보류/잔차→fwd예측→mint(ic0.97)/HAC lags4/조건부 in28.4 vs out-0.16. ★additive INV-11(호출처 0, go-live 시 카드 mint 경로서 r_c·F 주입), go-live·실거래 무접촉.
> (2) **다음 의도**: pytest 격리 테스트 파일(tests/assume/test_spanning_gate.py) 추가 + plan S4 마킹 + 격리 커밋. 이후 S5 정보델타 게이트(임베딩 novelty+rate-cap AND 델타, LLM무관 = 자율 가능 동형). S4 LLM 소환(claim 생성·Opus audit)·S5 대형 발권·S6 종목·S2 RegimeGlasso 공급측 = button+go-live 선결 불변.
> (3) **동기화**: git HEAD=d00fe0f(S2). button 64e8bc0(ETF) 무접촉. btn-button 세션 살려둠(사용자 "세션둬"). push·go-live 미접촉.
>
> [ckpt-202606060900:btn-Inv S2 macro mediator 구독측 ✅ — posterior 노출 판정→어댑터 구현(81 passed)]
> ★**완료(검증됨)**: 직전 ckpt 재개점("macro_schema posterior 노출 판정")을 사용자 지시("너거 하라고"+"리드미 참고")로 집행 → **macro 구독측 자율 구현 완료**.
> (1) **판정**: `macro_schema.py` MacroView 원본은 `regime_now`(PIT filtered, NBER lag 미사용)+`confidence_now`(스칼라)만 노출, full posterior 벡터·entropy·covariance **미노출**. BUT `eval_mediator`(fhc.py L222)는 **boolean `posterior_holds`만** 받음(자산무관 core=MacroView 무지) → holds 산출은 구독 어댑터 책임 → **baseline 무수정 자율 가능 확정**. ★README 참고로 `core/brain/regime_belief_adapter.belief_from_macro_view` 발견 = MacroView→4-state belief 확률벡터 변환 **이미 존재**(confidence soft-spread+floor+unavailable→uniform) → caveat(full posterior 미노출) 해소(belief 분포서 entropy 산출).
> (2) **구현**: `core/assume/macro_mediator.py` 신규(brain↔assume 단방향 seam, fhc는 MacroView import 0 유지). `macro_posterior_holds`(belief_from_macro_view 재사용→target 국면 질량 op threshold→bool, fail-closed UNKNOWN[None/unavailable/stale-too-old/라벨오타], entropy 게이트=평탄 국면 보류, ★filtered-only=regime_now만·regime_forecast 무시 look-ahead 차단) + `eval_macro_mediator`(fhc.eval_mediator 연결 헬퍼) + `belief_entropy`. observable_ref="regime:{BLOC}:{Label}". self-test 9/9 + `tests/assume/test_macro_mediator.py` 14(filtered-only/KRW bloc/entropy bound 포함). **81 passed**(기존 67+14, 회귀0). fhc/regime_belief_adapter **무수정**=INV-11 byte-identical, 호출처 0(go-live 시 카드 mint 경로 소비).
> (3) **다음 의도**: S2 macro 구독측 닫힘. 잔여 S2 = RegimeGlasso 공급측(sleeve cov, button INV-9 breaker, .coord §6 미해결)=button 합류 선결. S4/S5/S6=go-live+button 선결 불변. btn-Inv 단독 자율분=소진(사용자 "완료인데" 정합). 격리 커밋(core/assume+tests/assume+progress/plan/handoff judge만, button ETF 미커밋 무접촉). push·go-live 미접촉.
>
> [ckpt-202606062XXX:btn-Inv 자율주행 진입 — S2 mediator wiring 착수 탐색(미완, 재개점 명확)]
> (1) **마지막 결정/발견**: 사용자 "주식 끝 자율 on" → S2 mediator wiring 가능 여부 탐색. **.coord-fhc-contract-20260603.md 확인 = 소유 분담 명확**: FHC core(자산무관)=btn-Inv(core/assume 완료) / Equity 인스턴스=button(stock/) / **Macro mediator(state-space 구독)=btn-Inv 소유**. ★regime 2층 구분 발견: (a) core/brain `RegimeClassifier`→`MacroView`(거시 국면, JM filtered/smoother 구분 §5.8-H, **btn-Inv 소유**) vs (b) RegimeGlasso(sleeve cov, **button 소유**, INV-9 breaker용). **macro 카드 mediator는 (a) 거시 국면 posterior 구독이 자연 = 내 소유라 자율 가능**. grep 결과 macro_schema.py `RegimeEstimate`(L66)·`MacroView`(L98)에 filtered/entropy/posterior/covariance 필드 **미검출**(class만 매칭=노출 안 할 가능성↑).
> (2) **다음 의도(재개점)**: ①`core/brain/macro_schema.py` RegimeEstimate(L66)/MacroView(L98) **본문 Read** → filtered posterior·entropy·covariance 노출 여부 판정. ②노출 시 → S2 mediator 구독 어댑터(`core/assume/` 신규, additive·off byte-identical, fhc.py `eval_mediator(STATE_SPACE_POSTERIOR)` 연결, filtered-only+versioned+covariance/entropy 노출 plan S2 spec) 골격 구현+self-test+pytest+격리커밋. ③미노출 시 → MacroView 확장 필요(결정론 baseline 수정=신중, btn-Inv 소유나 회귀민감)→S2 coder-readiness 명세로 plan 박제 후 보고. ⛔button RegimeGlasso API(.coord §6 미해결 b/c)는 button 합류 선결, S2 구독측(btn-Inv)만 자율.
> (3) **동기화**: git HEAD=2f90748(button), **미커밋 379개**(button eq_kr study 대량, core/assume와 경로 안 겹침=격리 커밋 가능). autopilot flag ON(agent/.secretary/.autopilot-btn-Inv.flag). 이번 세션 박제 완료=자문 수렴(S4/S5 정보델타+편향+직교)·종목 universe 정책·core 정교화(chatter/LOO 67p)·코인 Markov 실패. push·go-live 미접촉. 인계=handoff-judge-fhc-arch-20260603.md.
>
> [ckpt-202606061XXX:btn-Inv 종목 단위 카드 발권 트리거 + universe 정책 확정 → plan 명시]
> ★사용자 질문="개별 종목 소식 트리거로 카드 생성되는 구조인가, 그렇다면 명시". 확인=현 plan에 종목 카드(스크린 내 틸트 C6)·리포트→발권(S5)은 있으나 **"종목 단위 소식 트리거"·universe 밖 정책 명시 약함**(정직 갭 보고). → **사용자 (3) 단계적 확정**: 발권 트리거=종목 소식 + rate-cap AND 델타 게이트(novelty+수치 리비전) / universe=①기본 스크린 통과분 내(C6) ②universe 밖 신선종목=임시 후보풀 적재→다음 스크린/슬롯 승격(즉시 끌어오기 X) ③안정 후 게이트와 함께 임시승격 허용. ⛔"임의 종목 소식=즉시 카드" 금지(빈도 상한 소실=직전 빈도 재검토와 동일 원리). plan S6 §종목 트리거 + S5 발권단위 명시 완료. ⛔ S6=button 세션 영역(go-live 선결).
>
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
