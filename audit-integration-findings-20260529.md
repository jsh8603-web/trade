# 전수조사 findings + 사용자 요구 프롬프트 박제 (2026-05-29)

> 목적: Phase I(빌드된 것 가동) + Phase II(주식/거시 적응학습) 후속 진행용 보존 문서.
> 진행상태 SSOT = `progress.md` (Phase I WP1~6 / Phase II II-A·II-B / `## 이연 항목` N-INT-1~7).
> ⚠️ Agent 원본 §3 보존 — 후속 세션에서 재스폰 없이 참조.

---

## 0. 핵심 요약

- **루트 발견**: `core/*` 신규 asset-agnostic 아키텍처(Phase 0~R)가 라이브 결정 루프에 **reachable = 0%**. 실행 중 시스템 = 레거시(`run_agents.py → agents/orchestrator.py → execute_trade.py`)이고 `core/*` 를 단 하나도 import/호출 안 함. 두 평행 시스템, 브리지 없음. 개별 갭(learning loop·valuation·risk gate)은 전부 이 root 의 하위 증상.
- **Phase I** = 빌드된 것 가동(통합). WP1 spine 직렬 선행 → WP2~5 / WP6 반독립. 권장 WP6→WP1+WP3→WP2→WP4/5.
- **Phase II** = 주식/거시 적응학습. 이번 세션 = **프롬프트 기록만**, 연구·구현 후속.

---

## 1. 사용자 요구 프롬프트 (verbatim 박제)

### 1-1. 거시 (macro)
1. "시장의 특성에 따라 거시 지표의 가중치를 조정하는 것 (예: 일반적으로 X 거시 상황에서는 Y지표가 올라야하는데, 안움직이는 이유는 무엇이고, 이는 Z 지표와 상관이 있다. Z 지표가 미래에도 움직이면 Y 지표가 안오르는 X-1 거시 상황일 수도 있다 와 같은 분석이 학습되어야한다. 그리고, Y 지표의 변동에 따라서 X-1 이 X 로 바뀌었다던지 와 같은 판정을 해야한다.)"
2. "이런게 학습된 데이터로 있어야한다. 위 상황에서 Y 지표와 Z 지표의 변동을 읽을때, 이런 관련 정보들이 들어와야한다."
3. "거시 지표도 거시상황을 5개? 정도 (inflation 등) 으로 구분하면 안되고, 상황에따라 현재 있는 거시 이론들에 추가해서 계속 가지를 쳐나가야한다. (전쟁중일수도 있고)"

### 1-2. 미시/주식·상품 (micro)
1. "퀀트로 후보를 뽑고, 실제 투자할때는 가치 분석도 바탕이 되었으면 한다. 각 PER PBR이든 뭐가 되었든, 투자 결정에 영향을 주는 지표들이 시기별/산업별로 달라지는 느낌이 있을건데, 그럼 그 상수값이 조정되어야한다."
2. "절대 주식이나 상품의 평가 지표들을 기간/산업군 별로 동일하게 보면 안된다. 추가로 더 논의할 부분이 있겠지만, 이게 최소한의 선이다."

### 1-3. 진행 방침
- "지금은 주식/거시에 대해 구현 단계만 확인하고, 내 프롬프트를 넣어두는 수준으로만 정리. 우선 발견된 결함 패치를 이번 세션에 집중." / "후속 단계에서 이어할께 (주식/거시)."
- GitHub 리서치(open-ended 레짐·산업조건부 valuation) = **deferred** (후속).
- **🔑 스코프 분담(2026-05-29 사용자 명시)**: **학습 루프 = 이 세션은 "돌아가는지" does-it-run 확인까지만** (WP6 백테스트 학습 sink·WP3 결정로깅 = 가동 검증 완료). **학습/판단 레이어(HeavyAgent 가치판정·Phase II 거시 open-ended 레짐·미시 적응 상수·메타라벨러 학습)는 별도 세션에서 대량 개발 중 → 사용자와 ~50% 분담 추가개발 → push 후 정식 학습**. 이 세션에서 판단 레이어 깊은 구현 금지(분담 충돌 회피). 결정론 HeavyAgent 빌드도 보류(판단 레이어).

---

## 2. 직접 코드/레퍼런스 확인 (Supervisor grep, 2026-05-29)

- **레짐 = 고정-K**: `core/brain/regime_classifier.py` — JumpModel `n_components=2`(bull/bear) ~ `4`(IC 4분면). open-ended/HDP/infinite/Dirichlet/novelty 흔적 = `core/`·`_refs/` 에 0. → 사용자 "고정 5개 금지, 가지 쳐나가야" 요구와 **위배**.
- **valuation = 산업 차등 미연결**: `stock/valuation.py:247` `sector_ev_ebitda` 파라미터 hook 존재하나 호출부에서 미주입(자기 역사 fallback). Gate1Thresholds·multiple_band·WACC 상수 전부 하드코딩. → 사용자 "기간/산업 동일 금지" 요구와 **위배**.
- **레퍼런스(`_refs/`)**: jumpmodels(고정-K), ai-hedge-fund(persona DCF 고정상수), MlFinLab(메타라벨링), Riskfolio/PyPortfolioOpt/skfolio. open-ended 레짐 분기·산업조건부 적응 valuation 은 **미보유** → 추가 GitHub 리서치 필요(deferred).
- 후속 리서치 후보 키워드: HDP-HMM / sticky infinite-state HMM / non-parametric regime discovery / novelty→new-regime branching / sector-relative & regime-conditional valuation multiples.

---

## 3. Agent 원본 보존 (5-subagent 전수조사, 2026-05-29)

> general-purpose subagent 5개 병렬, whole-file 읽기 + cross-file. 검토 축 = "GOLDEN(IMPLEMENTATION_PROMPT.md) 기준 구현됐으나 호출부 없어 루프 안 닫힌 wiring 갭".

### A1 — 거시 brain 학습 wiring (agentId ab548986a9578743a)

VERDICT: 거시 조건부상관 attenuation(read side)은 `regime_classifier.classify()` 에, `recall_similar`은 `macro_reasoning.enrich()` 에 wired 됐으나 전체 체인이 프로덕션에서 dead — 유일 live caller(`coin_track_macro.py:63`)가 `allocate()` 를 macro_view 없이 호출해 항상 HRP fallback, RegimeClassifier/MacroReasoningNode 가 tests 외 미인스턴스화. §5.8-H WRITE/학습 절반(`ingest_correction`·`CorrectionRecord` 생성·`baseline_violation`)은 0 callers(완전 dead) — wrap-up/hindsight job 부재로 루프가 어떤 학습데이터도 영속/recall 못함. 즉 레짐 재판정+recall-at-decision = implemented-but-unwired; 조건부상관은 아무것도 호출 안 하는 경로 안 정적 규칙으로만 존재.

- F1 macro brain chain(classify→enrich→weights) 프로덕션 미호출: RegimeClassifier.classify()(regime_classifier.py:95)·MacroReasoningNode.enrich()(macro_reasoning.py:88)·regime_to_weights(portfolio_orchestrator.py:152) 구현됨. wired=no — allocate()는 coin_track_macro.py:63 에서 macro_view 인자 없이만 호출→_fallback_hrp(:150). RegimeClassifier(/MacroReasoningNode( tests 외 0회 인스턴스화. [critical]
- F2 조건부상관 구현+classify 내 wired 됐으나 경로 dead: conditional_attenuation(:304)·AnomalyCase 6 cases(:159)·score_confidence(:410), regime_classifier._apply_correlation_attenuation(:160,364)에서 소비. classify() 자체가 프로덕션 미실행. [high, F1 고치면 자동 작동]
- F3 baseline_violation(detection channel ⓑ) 0 callers: indicator_event_correlation.py:350 구현, core/stock/agents/backtest/scripts/rl_hybrid + tests 전부 0 callers = 순수 dead code. [high]
- F4 ingest_correction+CorrectionRecord WRITE side 완전 unwired·영속 없음: ingest_correction(:471)·CorrectionRecord(:370) 구현. ingest_correction 0 callers, CorrectionRecord 생성 어디서도 0회. weekly_retrain.py=순수 RL/PPO(macro link 없음). add_correction/retrieve_corrections RAG store 구현체 없음(stub) → recall_similar 항상 빈 store recall. [critical]
- F5 shared-instance gap: classifier(자체 IndicatorEventCorrelation 생성, regime_classifier.py:88)와 reasoner(correction_memory=None default→[] 반환, macro_reasoning.py:136)가 서로 다른 correction memory 사용, 단일 인스턴스 공유·ingest 안 함. [high]
- F6 anchor 확인 memory_layer store_decision/update_with_outcome 0 live callers 확정: tests + CoinMemoryLayer(이것도 tests 만 인스턴스화) 외 0. [critical]
- 정정: 사용자 framing 일부 방향 어긋남 — READ side(recall_similar/score_confidence/conditional_attenuation)는 classify/enrich 에 code-wired. 진짜 zero-caller 갭 = WRITE side(ingest_correction+CorrectionRecord+baseline_violation), 게다가 read 경로 host 함수(classify)가 프로덕션 미호출(F1).
- remediation: §5.9-E wrap-up job 신설(과거 as_of HMM smoothed/NBER hindsight 재계산→regime_realtime≠hindsight 시 CorrectionRecord 생성→공유 ingest_correction) + 실 rag_store 어댑터. macro_view 주입 체인 가동. 단일 IndicatorEventCorrelation 양쪽 주입.

### A2 — 주식 valuation + 적응상수 (agentId a4bfe93722228ba28)

VERDICT: 가치분석 기반 주식투자(quant-screen → value-confirm)는 implemented-but-unwired — 2단 게이트·DCF/멀티플·PIT 어댑터·factor attribution·meta-labeler 전부 존재+테스트 통과하나, 프로덕션 entrypoint 가 StockTrack 미인스턴스화, 구체 HeavyAgent 가 repo 어디에도 없음, value_stock() 라이브 미호출(stock_track.py:157-166 이 _valuation_override 없으면 ABSTAIN, override 는 tests 만). 결정 영향 상수(Gate1 price-move/value-gap·멀티플 분위·margin_of_safety·attribution threshold) 전부 하드코딩 class-attr/default-arg literal, regime/sector/outcome 적응 0 — 유일 sector hook(sector_ev_ebitda)·regime hook(detect_value_factor_regime)은 dead(0 live callers).

- F1 2차 HeavyAgent stub, 프로덕션 GATE2 미도달 [critical]: HeavyAgent=Protocol only(value_trigger.py:76-91), 구체 구현 repo 없음(mocks=_smoke_test.py:44-51+tests). run_value_trigger(heavy_agent=)는 stock_track.py:169 가 self._heavy_agent(default _heavy_agent_override=None, :67,79) 전달→None 시 ABSTAIN 강제(:250-287). 실 agent 주입 tests 외 0.
- F2 value_stock() 라이브 미경로·fundamentals stub-only [critical]: value_stock()(valuation.py:244)·PITFundamentalsAdapter(fundamentals_adapter.py:57). value_stock 라이브엔 docstring(stock_track.py:8,137)만, generate_candidate 는 _valuation_override 없으면 abstain(:155-166). PITFundamentalsAdapter/FundamentalsProvider 프로덕션 0 callers(InMemory synthetic+tests 만). DART/EDGAR provider 없음.
- F3 결정상수 전부 하드코딩, regime/sector/outcome 적응 0 [high, 사용자 핵심]: Gate1Thresholds(value_trigger.py:55-60) price_drop_pct=0.10·valuation_gap_min=0.25·value_decline_tolerance=-0.05 — live caller 미override(stock_track.py:169 thresholds= 생략). multiple_band(valuation.py:202) low_pct=0.25/high_pct=0.75 고정. _residual_income_value(valuation.py:366) margin_of_safety=0.20·terminal_growth=0.03. WACC(valuation.py:60-90) rf=0.045·ERP=0.06·tax=0.25·floor0.06/cap0.20. AttributionConfig(factor_attribution.py:140-144) dominance=0.5·min_r2=0.3·residual=0.6. meta-labeler prior_trap_rate=0.3+literal cutoff(factor_attribution.py:402-409). **적응 메커니즘 없음** — regime/sector 읽어 변경하는 코드 0. sector_ev_ebitda(valuation.py:247) 모든 caller 미전달→자기역사 fallback. detect_value_factor_regime 는 recommended_confidence_haircut advisory dict(factor_attribution.py:419)만, 0 live callers.
- F4 meta-labeler·attribution 학습 closure 없음·라이브 미호출 [high]: ValueTrapMetaLabeler(factor_attribution.py:348) SecondaryModel=Protocol(:336) 구체 fit/predict 없음, trap_probability 항상 정적 heuristic(:394-412). attribute_trade(:147) tests 외 0 callers. realized-outcome→triple_barrier→fit 파이프 없음, G9 mark-to-market 미호출.
- 루트: 주식 brain 전체가 Phase3 코드인데 live consumer(StockTrack 인스턴스화·core/brain HeavyAgent+regime classifier·DART/EDGAR provider)가 Phase4/6 으로 이연·미빌드 → 구조완성 but dormant. value_trigger.py:31("HeavyAgent 구현체는 외부, 프로토콜 경계만")이 open-loop anchor.

### A3 — risk/order/consensus 강제 (agentId abf44dd4bd1cbc369)

VERDICT: risk/order/consensus 보장이 implemented-but-unenforced. 실 코인 사이클 run_agents.py→orchestrator.py→execute_trade.py + 주식 kis_client.order() — 어느 것도 risk_gate/GatedOrderRouter/ConsensusJudge/KillSwitch/resolve_precedence import·호출 안 함. Phase2/4/6/R 안전모듈 전부 tests 외 0 callers. 현 live 안전 = kis_client _check_safety(DRY_RUN/EMERGENCY_STOP) + execute_trade auto_emergency.json 만.

- (1) NO-BYPASS(N-P4-GATE): GatedOrderRouter.submit(risk_gate.py:473-526, via_gate guard :506) 구현. wired=0 callers 외 tests. 실 코인주문 run_agents.py:880,892 가 execute_trade.py 직접 shell-out, execute_trade.py risk_gate 참조 없음. 주식 kis_client.py:222-279 _check_safety+_clamp_to_balance 만(risk_gate/admission 미호출). bypass 자명히 가능. known_deferral=yes(progress.md:59 N-P4-GATE). [high]
- (2) risk_gate always-on: RiskGate.check(risk_gate.py:158-289). coin·stock 둘 다 tests 외 0 callers. orchestrator.py risk_gate import 안 함, stock_track.py:14,140 "risk_gate 경유=호출자 책임, 후보 반환만". partial deferral(N-P4-GATE/N-P6-FULL-INTEGRATION). 라이브 코인 경로(execute_trade.py)에 always-on 부재가 surprise. [high]
- (3) consensus §4.2: is_high_stakes(portfolio_orchestrator.py:63-77)·check_consensus_trigger(:254-267)·ConsensusJudge(consensus.py:88-259)·coin lens(coin_consensus_lens.py:91)·path-attribution DecisionRecord 구현. tests 외 0 callers. allocate()(coin_track_macro.py:63)가 consensus 미호출. regime 선제트리거·누적포지션 트리거 라이브 미계산. DecisionRecord 실 decisions DB 미기록. known_deferral=yes. [medium]
- (4) KillSwitch/precedence §6: KillSwitch(risk_gate.py:304-386)·resolve_precedence(:418-468). tests 외 0 callers. 라이브 MDD 계산·update_mdd 피드 없음. 단 라이브 코인은 별도 auto_emergency.json(orchestrator.py:1579 _evaluate_auto_emergency, execute_trade.py:318) — 작동하나 설계 KillSwitch 와 무관. known_deferral=yes. [medium]
- 결론: 4건 모두 pinned deferral(governance surprise 아님). 진짜 surprise=실 코인트랙(execute_trade.py, 실제 돈 움직이는 유일 경로)이 설계 risk/consensus/killswitch 전부 우회 — DRY_RUN+레거시 auto_emergency.json 만 막음. DRY_RUN=false flip(N-PR-GOLIVE-FLIP)이 N-P4-GATE 전에 일어나면 "우회불가 백스톱" = 환상.

### A4 — 라이브 통합 갭 (agentId af1b9ee2c22b2877c)

VERDICT: 실행 시스템 = 100% 레거시(run_agents.py→agents/orchestrator.Orchestrator→execute_trade.py), 신규 core/ 아키텍처 전체 dormant. 어떤 live entrypoint 도 CoinTrackWithMacro/StockTrack/PortfolioOrchestrator/RiskGate/ConsensusJudge/MemoryLayer import·인스턴스화 안 함 — core/* importer 는 전부 tests 또는 다른 core/ 모듈. 브리지 코드 0 — 재빌드가 live loop 에 연결된 적 없음.

- (1) THE BIG Q — 신규 아키텍처 live loop 에? NO. run_agents.py imports: agents.external_data(:25)·agents.orchestrator(:26). from core/ import 0. main() Orchestrator()(:684)→orchestrator.run()(:685). 실행 subprocess execute_trade.py(:880,892). orchestrator.py imports=agents.conservative/moderate/aggressive/base_agent(:24-27), core.|CoinTrack|RiskGate|ConsensusJudge|memory_layer|store_decision 매칭 0. live_trader.py core/ import 0. **정량: ~24 core/ 모듈 중 live reachable=0, tests reachable≈100%.**
- (2) 결정로깅 S9 레거시-only 이중경로: 레거시A(run_agents.py Phase5) Supabase decisions REST POST(:1012-1017)+market_context_log(:1080)+market_data(:1098)+execution_logs(:1114). 메모리 recall=subprocess recall_rag.py(:641-646)+past decisions(:665) — core.brain.memory_layer 아님. 레거시B(execute_trade.py) _record_trade_to_db(:623)→decisions POST(:739). 신규 S9 store(memory_layer store_decision:111/get_past_context:151) 0 live callers. IMPLEMENTATION_PROMPT §0.2:137("trade_reviews writer 0(죽음)") 일치.
- (3) dangling(정의+테스트, 0 live callers): coin_track/coin_track_macro/stock_track/asset_track/portfolio_orchestrator/risk_gate/consensus/risk_sizing/strategy/budget_ledger/fallback_policy/coin_sizing/coin_memory/coin_shadow/coin_consensus_lens + core/brain/* 전부. [critical — "우회불가" risk gate 프로덕션 미실행, 라이브 MAX_* 체크는 execute_trade.py:336-480 에만]
- (4) 브리지: 없음. agents.orchestrator + core.* 둘 다 import 하는 파일 0. N-P6-FULL-INTEGRATION 미구현 = 완전 평행.
- remediation: run_agents.py main()(684-690 Orchestrator 블록)에서 core.portfolio_orchestrator 인스턴스화+CoinTrackWithMacro per asset→ConsensusJudge→RiskGate→execute_trade subprocess. 레거시 flag 보존. RiskGate.check() 를 결정(:858)↔주문 subprocess(:880/892) 사이 삽입. MemoryLayer.store_decision()(:111) Phase5 decisions POST 옆에, get_past_context()(:151) ~:636 recall_rag 대체/보강.

### A5 — 백테스트 PIT/학습 closure (agentId adda9e69f867ebcda)

VERDICT: 충실 PIT replay-with-learning 불가(현재). BacktestEngine.run() 은 순수 price-driven sim — collect_market_state()(timestamp 없음)→price 만 override→generate_candidate→buy/sell→equity append. 학습 피드백 0(update_with_outcome/attribute_trade/ingest_correction 미호출), per-bar PIT macro/sentiment 재구성 0. PIT 프리미티브(filter_pit_fundamentals/MacroVintageProvider/krx_universe)는 실재하나 library-only(tests 만 wire), turnkey runner 부재.

- F1 백테스트 학습 closure 부재 [CRITICAL]: run() 루프(engine.py:227-302)=collect_market_state(231)→generate_candidate(237)→buy/sell(242/269)→equity append(302) 만. update_with_outcome(memory_layer.py:138)/attribute_trade(factor_attribution.py:147)/ingest_correction(indicator_event_correlation.py:471) 호출 0. 학습모듈 import=regime_classifier.py:55+tests 만. remediation: SELL fill 후(>:300) outcome_pct→update_with_outcome+attribute_trade, open=G9 mark-to-market, run()에 learning_sink 주입.
- F2 PIT 환경 재구성 = price-only [CRITICAL]: collect_market_state() as_of 인자 없음(asset_track.py:61·coin_track.py:61[live _run_script+ExternalDataAgent.collect_all()="now"]·stock_track.py:87). engine.py:231-234 price/asset/timestamp 키만 override, macro/external/FGI=라이브fetch or 빈mock. → price 만 historical, macro=now/stub=lookahead. remediation: collect_market_state(as_of) ABC+양 track 추가, engine.py:231 as_of=ts 전달, track 이 PIT provider(MacroVintageProvider.get_vintage)로 해소.
- F3 vintage 실재하나 credential-gated·unwired [HIGH]: macro_vintage.py:65-102 realtime_start=end=as_of 실 vintage+future as_of 거부(:83), FRED_API_KEY 없으면 None(:52,77), ECOS=NotImplementedError stub(:153). filter_pit_fundamentals(walk_forward.py:30-47)·UniverseManager(:234-254)·krx_universe jsonl PIT(:13,63) 존재. WalkForwardEngine.run()(:135)이 raw returns 로 Sharpe 만, filter_pit_fundamentals/is_delisted_universe_only/engine 미호출. as_of 는 미사용 helper(walk_forward.py:32/44/50)에만.
- F4 turnkey runner 없음 [CRITICAL]: backtest/=__init__.py+5 library, __main__/def main/argparse 0. WalkForwardEngine/CoinBacktestEngine/build_go_nogo_card/BacktestEngine caller=tests 만. build_go_nogo_card 도 tests 에서 hand-built oos_sharpe_paths 받음. remediation: backtest/run_replay.py(CLI --asset --start --end --speed: 히스토리 pull→AssetTrack(as_of-aware)→BacktestEngine 루프+learning sink→WalkForwardEngine→build_go_nogo_card→JSON). F1/F2/F4 동시 해소.
- go/no-go 결론: F1/F2/F4 blocker. 현 엔진=cost-aware 하나 lookahead-prone·non-learning equity curve. 90일 paper 전 runner+as_of+learning-sink 필수(전부 code-level, 프리미티브 존재).
