# 구현 핵심 (implementation-keys) — 7-에이전트 종합

> 생성 2026-05-28 · `IMPLEMENTATION_PROMPT.md`(Round 10) 보완 companion. plan/progress/harness2 가 이 파일을 참조한다.
> 입력: 분석 5(A1-A5) + 코드작성 2(B1 macro·B2 quant) opus 에이전트. coin clone=`coin/`, 레퍼런스=`_refs/`.
> **B1 macro 는 완료 시 §6 에 append** (현재 진행 중).

---

## 0. 최상위 작업 규칙 (사용자 확정 — 전 Phase·전 step 강제)

1. **Sonnet-executable 강제**: plan/progress/harness 의 모든 step 은 Sonnet 이 그대로 코딩 가능하도록 5항목 — (1) 대상 파일 절대경로 (2) 함수/심볼/라인 (3) before/after 또는 신규 코드 블록 (4) 건들지 말 경계 (5) 완료 판정 기준 — 을 갖춘다. 추상 표현("적절히") 금지.
2. **reuse-github-as-is 기본 규칙**: 레퍼런스 repo 에 있는 코드는 **재작성하지 말고 최대한 그대로 가져다 쓴다**. 차용 시 (repo 파일:심볼 → 우리 target 경로) 매핑을 step 에 명시. 새로 짜기 전 repo 열어 입출력 계약 확인(§0.3 규칙). 아래 §1-§6 의 "코드 위치"가 그 차용 출처.
3. **stub 주의**: 일부 레퍼런스는 공개판이 stub 다 — MlFinLab labeling 본문 `pass`, AgenticTrading `_attribute_performance_to_factors`=`np.random`, AT registry 대부분 disabled. 이건 **계약(docstring/시그니처)만 차용하고 본체는 자체 구현**.

---

## 1. A1 — 실행·정합성 (S7/S8, Phase -1/4) · 차용=nautilus·pykis·polymarket

### 설계 미반영 → 추가 필요
- **(a) 매도 시 거래소 실잔량 클램프**: 부분체결 후 내부기록>실잔량이면 과매도. polymarket `trader.py:283-289` `sell_shares=min(req, actual_balance)` 패턴. coin `execute_trade.py:457` `body["volume"]=amount` 그대로 보냄 → 클램프 없음.
  - wire: KIS/Upbit 어댑터 `execute()` 내 `_clamp_to_balance(side, amount)` 신설, R2 의 free 잔량(locked 제외) 재사용. (Phase -1/4)
- **(b) poll-then-amend 미체결 정정 루프**: H15 는 "n분 정정"만, 실패 처리 미정. polymarket `trader.py:314-337` 3×2s poll→cancel. coin `execute()` POST 1회뿐.
  - wire: KIS 어댑터 `_poll_and_amend(order,timeout,ticks)` → pykis `modify_order`(`_refs/python-kis api/account/order_modify.py:521`, `ORGN_ODNO`) / 실패 시 `cancel_order(:607)`. (Phase4·H15)
- **(c) 멱등성 fallback = 체결완료 주문 조회**: coin `check_open_orders_and_cancel`(`:123`)은 `state=wait`(대기)만 조회 → **체결완료 후 응답유실 못 잡음**. pending_order + daily_order(체결포함) 양쪽 조회 필요. KIS/Upbit 둘 다 client_order_id 미지원 확정(KIS=`KisOrderNumber(account,branch,number)` 서버발급 3튜플 `order.py:346-358`).
  - wire: `execute_trade.py:176` E2 확장 — POST 타임아웃 catch → 재시도 전 `daily_order`+`pending_order` 조회+identifier 매칭. `check_open_orders_and_cancel`→`_reconcile_recent_order(identifier)` 일반화. (Phase -1)
- **(d) 명시적 OrderState enum/전이표 부재**: nautilus FSM(INITIALIZED→SUBMITTED→ACCEPTED→PARTIALLY_FILLED→FILLED/CANCELED). 슬리피지 `FillModel`(확률체결) 미반영.
  - wire: S7 에 `OrderState` enum+전이검증(nautilus 축약), `FillModel`은 H1 `sim_engine` 확률체결 옵션. (Phase5)

### 설계 반영분 구현 핵심 + 코드 위치
- **E2 identifier**: Upbit 는 body 에 identifier 넣되 **응답유실 시 동일 identifier 재조회가 핵심**. KIS 는 identifier 없음 → pykis `from_number(account,branch,number)`(`order.py:392-417`)로 서버주문번호 즉시 DB 저장. coin 현재 identifier 미사용(`:451-457`).
- **H15 modify/cancel**: pykis `domestic_modify_order`(`order_modify.py:103`), `RVSE_CNCL_DVSN_CD`(정정01/취소02)·`ORGN_ODNO`. 정정은 신규주문번호 발급 → **원번호 추적 체인 유지**(이중정정 방지).
- **R2 reconciliation 양방향**: polymarket `trader.py:260-274 verify_positions`=ghost(거래소엔 없는데 DB有) write-off. 우리 R9=locked(거래소에 묶인 잔고를 DB에 더함)는 반대 방향 → **양방향 둘 다 필요**. 임계 drift=halt(자동 write-off 아님).
- **websocket 재연결**: pykis `client/websocket.py:358 _run_forever`(reconnect=True, interval=5s), `:411 _restore_subscriptions`, `:456` PINGPONG echo — 재연결 후 체결통보 구독 복원 코드 보장. **그대로 채택**. 토큰 24h(H4 "6h"는 보수적 갱신주기).

---

## 2. A2 — 리스크·포트폴리오 최적화·사이징 (S6/§6, Phase 2) · 차용=Riskfolio·PyPortfolioOpt·skfolio·ai-hedge-fund

### 설계 미반영 → 추가 필요
- **포트폴리오 레벨 사이징 부재**: coin `base_agent.py:55 kelly_position_size`=confidence 테이블+승률 스칼라뿐, **공분산·상관 미반영**. §0.7-G1 은 corr dedup 만, 실제 공분산 기반 비중 산출기 없음.
- **Ledoit-Wolf 라이브러리 이원화 위험**: PyPortfolioOpt `risk_models.py:509 CovarianceShrinkage.ledoit_wolf()`(PSD 보정 `:57` 내장) vs Riskfolio `ParamsEstimation.py:230`(PSD 보정 없음). **한쪽 택1 필수** → PyPortfolioOpt 로 SSOT 단일화(BL 과 동일 라이브러리=계약 일관).
- **HRP fallback trigger 미명세**: Riskfolio `HCPortfolio.optimization(model="HRP", codependence="tail", w_max=0.10)`(`HCPortfolio.py:716`). H25 crisis corr 1수렴 해결책=tail-codependence(`:318`)인데 설계 미연결. trigger=cov condition number↑ 또는 corr 평균>임계.
- **turnover-aware QP 누락**: §0.7-G1 cvxpy 가 캡만 제약. skfolio `_mean_risk.py:256 transaction_costs`·`:320 previous_weights` 항 추가 필요(밴드 룰과 충돌 방지).
- **CVaR 사이징 미연결**: coin 은 `multi_objective_reward.py:274`에서 RL 보상으로만. Riskfolio CVaR 최적화를 게이트/사이징에 미반영.

### 설계 반영분 구현 핵심 + 코드 위치
- **BL custom prior 완전 지원**(중요·B1 연결): PyPortfolioOpt `black_litterman.py:141 __init__(cov_matrix, pi=…, absolute_views=…)`, `:274 _set_pi`. **macro brain 의 regime→% 를 `pi` 로 주입**. 출력 `bl_returns()`(`:417` solve, singular시 lstsq)·`bl_weights()`. omega=idzorek(`:380`) 또는 default(`:366`).
- **상관 multiplier**: ai-hedge-fund `risk_manager.py:301 calculate_correlation_multiplier`(corr≥0.8→0.7x) → §6 상관캡 항에 이식. 평시용 명시, crisis 는 HRP 분기(H25).
- **precedence 격자 백스톱**: §6 격자 통과 후 마지막 hard cap = nautilus `risk/engine.pyx:359 max_notional_per_order`·`:492 _deny_order_list` 패턴(LLM 우회불가 wrapper 최종 관문).
- **skfolio walk-forward**: `_walk_forward.py:118 purged_size`≥1(집행지연 자산). turnover 이중 페널티 주의(`_mean_risk.py:448`).

---

## 3. A3 — ops·통합대시보드·GO/NO-GO·과적합 (S11/S12, Phase 5/6) · 차용=yakub268·skfolio

### 설계 미반영 → 추가 필요
- **(a) PBO 산출법 미명세(가장 중요)**: yakub268 `validation_framework.py:179`=`norm.cdf(0, mean(sharpe), std(sharpe))` **근사치(주석 "Simplified")**, López de Prado CSCV 아님. skfolio `_combinatorial.py:50 CombinatorialPurgedCV`=정통 purged CV 이나 **PBO 스칼라 함수 없음** → CV 경로 위에 **자체 CSCV logit-rank 집계기** 작성 필요. 설계에 "PBO=CSCV 정통식" 명시 안 하면 근사치 함정.
- **(b) G8 "백테스트=라이브 지표함수 공유" 강제장치 부재**: coin 이 정반대 — `sim_engine.py:83 calc_danger`/`:116 calc_opportunity`(백테스트) vs `agents/base_agent.py`(라이브)에 **동일 점수로직 중복**. `backtest_v6_simulation.py:187 calc_rsi` 등도 자체 구현. → **단일 `common/metrics.py` 모듈 강제**(sim_engine·라이브·backtest 동일 import). Phase R 회귀0 게이트.

### 설계 반영분 구현 핵심 + 코드 위치
- **공통지표 SSOT**: yakub268 `walk_forward.py:96/110/120 calculate_sharpe_ratio/max_drawdown/profit_factor`(순수함수) → `common/metrics.py` 로. coin 3중 중복 제거가 강제 게이트.
- **GO/NO-GO 카드**: yakub268 `walk_forward.py:134 assess_go_nogo`+`GoNoGoStatus`(GO/MARGINAL/NO_GO)+`GoNoGoCriteria`(MIN_SHARPE=1.0, MAX_DD=-15%, MIN_WIN=45%) → 카드 렌더 스키마 직차용. `WalkForwardResult` dataclass JSON 1:1.
- **PBO/DSR**: skfolio `CombinatorialPurgedCV(n_folds,n_test_folds,purged_size,embargo_size)` 경로 생성 + 자체 logit-rank CSCV 집계기. DSR=yakub268 `validation_framework.py:218 calculate_deflated_sharpe_ratio`(`:271 norm.cdf`, trial-count 입력 필수). PBO 근사식(:179)은 **버리고** skfolio 경로로.
- **대시보드 멀티에셋 확장**: coin `dashboard.py` `run_script(name)`→`run_script(name,asset_id)`, `_CACHE` 키 `f"{asset}:{key}"`. SQL `v_daily_summary`(`009:135`)에 `asset` 컬럼+`GROUP BY asset`. yakub268 `dashboard/app.py`+`routes/v5.py` 레이아웃 참조.

---

## 4. A4 — consensus·학습루프·사후귀속·PIT 메모리 (S5/S9/S10, §4.2, Phase 1/6) · 차용=TradingAgents·AgenticTrading·논문

### 설계 미반영 → 추가 필요
- **(a) FinMem 계층메모리 decay 식 부재**: coin `embedding_store.search_similar`=코사인 단독. FinMem `score=w_r·recency+w_v·relevance+w_i·importance`, decay `α^(경과)`. recency/importance/decay 3축 전무.
- **(b) PIT causal-mask 미구현(가장 시급)**: coin rag 에 `as_of`/`causal`/`mask` 0 → 백테스트 누수. `match_similar_analyses` RPC 에 `as_of` 파라미터+`WHERE created_at<as_of`.
- **(c) reflection→RAG 적재 루프 미구현**: TradingAgents `memory.py` 완성형 — `store_decision`(pending)→`update_with_outcome`(resolved+REFLECTION, atomic)→`get_past_context`. 우리 `trade_reviews` 미배선과 정확히 대응.
- **(d) Judge 가 실제론 2단**: TradingAgents = Research Manager(Bull/Bear→ResearchPlan structured) → Portfolio Manager(Risk 3-debator→PortfolioDecision, **past_context lesson 주입**). 설계 §4.2 는 단일 Judge 로 압축.
- **(e) Registration Bus = event-stream**: AT `memory_bridge.py` 이벤트 emit/query. H29 liveness=이벤트 staleness 기반 degrade(별도 heartbeat 불필요). **단 AT registry.py 대부분 stub**.
- **(f) dexter 자가검증 부적합**: TUI 범용 에이전트, 트레이딩 validate 노드 없음. 자가검증=TradingAgents 토론구조로 충족, dexter 는 컨텍스트 압축 참고만.

### 설계 반영분 구현 핵심 + 코드 위치
- **TradingAgents Judge**: `portfolio_manager.py:35-58` structured output(`bind_structured`)+freetext fallback, lesson 주입 핵심. 종료조건 `count>=2*rounds`(연구)/`3*rounds`(리스크) — 코인 24/7 토큰폭발 방어 **rounds=1**.
- **History Rhymes causal-mask**: 쿼리 timestamp 이전만 검색+구조지표·narrative 공동임베딩. repo 없음 → 단일 BGE-m3 텍스트화 후 임베딩(추정, 논문 cutoff 이후).
- **factor 귀속 ⓐ vs AT 차이(중요·확정)**: AT 는 alpha/risk/cost(`portfolio_construction/core.py:5,476`), `_attribute_performance_to_factors(:1911)`=`np.random` **stub**. → factor 회귀(market-β+섹터+잔차)는 **우리가 직접 작성**(B2 `factor_attribution.py` 가 이미 구현), AT 는 alpha/risk/cost event-stream **배선 패턴만** 차용. enum 매핑(β지배=MACRO_REGIME_WRONG/idio=VALUE_TRAP) 유효.
- **AT reflection alpha**: `reflection.py:51` raw_return+벤치(SPY) 초과지 factor alpha 아님 — 혼동 금지(메모리 태그용).

---

## 5. A5 — 유니버스·데이터·PIT (S1/§5.7/§5.10, Phase 3/4) · 차용=Lean·pykrx·FDR·OpenBB

### 설계 정정(중요) → 반드시 반영
- **① "관리종목=pykrx 헬퍼"는 헛다리**: pykrx ~80함수에 `get_administrative` 없음. 실제=**FDR** `KrxAdministrative`(`_refs/FinanceDataReader/krx/listing.py:321`, `data.py:181 'KRX-ADMINISTRATIVE'`). → 관리종목 소스 FDR 로 고정.
- **② ALFRED vintage 거시 PIT 완전 미설계**: OpenBB FRED 는 vintage 버림(`fred_base.py:61-65`만, `models/series.py:163-164` realtime `d.pop()`). → FRED `realtime_*`(=ALFRED) 직접 호출 필요. 거시 백테스트 lookahead 차단 핵심.
- **③ KrxAdministrative 자체가 PIT 아님**: 현 시점 스냅샷만(해제일 없음) → 과거 시점 재구성 불가. **일별 스냅샷 적재** 필요(백테스트 admission 게이트 PIT).
- **④ Lean coarse obsolete**: `CoarseFundamental.cs:97` `InvalidOperationException`. 현행=`Fundamental`+`FineFundamental` 통합. 개념 유효, 명칭만 매핑.
- **⑤ EDGAR frames lookahead**(설계 인지): accession 단위 PIT 는 OpenBB 미제공 → 자체 파서.

### 설계 반영분 구현 핵심 + 코드 위치
- **admission 게이트(S4 앞단)**: Lean `CoarseFundamentalDataProvider.cs:50` **날짜별 CSV**(`{yyyyMMdd}.csv`) PIT 강제 패턴. coarse=FDR `StockListing("KRX-MARCAP")`(Marcap/Volume). fine=`KRX-ADMINISTRATIVE`+`KrxDelisting`(`listing.py:236`, `DelistingDate`/`Reason`). selector 시그니처=Lean `FineFundamentalUniverse.cs:36`.
- **PIT 3-튜플**: KR=`_refs/dart-fss`+`OpenDartReader` `fnlttXbrl.xml` rcept_no 단위 파싱. US=OpenBB SEC `models/company_filings.py` accession+filing_date 받아 accession 단위 선별(frames 우회). `as_of>=filing_date` 필터.
- **생존편향**: 상폐포함=**백테스트만**, 라이브 매수 제외. FDR `KrxDelisting`(DelistingDate PIT). **US 상폐 무료 소스 부재 주의**(FDR US listing=현재형뿐 → 별도 소스).
- **휴장일(H31)**: pykrx `get_previous_business_days`(`stock_api.py:117`), US=`pandas_market_calendars` 권장.

---

## 6. B2 — quant brain 코드 (작성 완료, `stock/` ~1,700줄) · 차용=ai-hedge-fund·MlFinLab

### 작성 파일 (실구현, 스모크 테스트 통과)
- `stock/contracts.py`(234) — 계약 SSOT. `Fundamentals`(PIT 3-튜플 fiscal_period+filing_timestamp+FilingSource, `is_pit_clean()`·`visible_at(as_of)`), `ValuationResult`·`ValueTriggerResult`·`AttributionResult`, enum(`FailureReason`/`ValueVerdict`/`ProductTier`/`RunMode`).
- `stock/data/fundamentals_adapter.py`(119) — `PITFundamentalsAdapter.get_pit_fundamentals(ticker,as_of)`(백테스트서 미래·RESTATED 차단), `FundamentalsProvider` 프로토콜(DART/EDGAR 경계).
- `stock/valuation.py`(383) — `value_stock(fundamentals,quote,sector_ev_ebitda)`. 보조 `calculate_wacc`·`dcf_scenarios`(bear/base/bull)·`multiple_band`(PER/PBR 분위)·`ev_ebitda_implied_equity`·`peg_ratio`·`_residual_income_value`.
- `stock/value_trigger.py`(346) — `run_value_trigger(valuation,fundamentals,price_change_pct,heavy_agent,metalabeler,mode)`, `passes_gate1`, `to_track_decision`(risk_gate 입력 변환), `HeavyAgent`/`MetaLabeler` 프로토콜.
- `stock/factor_attribution.py`(445) — `attribute_trade(...)`, `_ols_multifactor`(표준 OLS), `triple_barrier_label`, `daily_volatility`, `ValueTrapMetaLabeler`, `detect_value_factor_regime`(스타일 군집).

### 차용(파일:심볼)
- ai-hedge-fund `valuation.py`: `calculate_enhanced_dcf_value`/`calculate_dcf_scenarios`/`calculate_wacc`/`calculate_ev_ebitda_value`/`calculate_residual_income_value` 수식 어댑트, 입력만 PIT 3-튜플로.
- ai-hedge-fund `aswath_damodaran.py`/`stanley_druckenmiller.py`: 2차 게이트 `HeavyAgent` 프로토콜로 분리(intrinsic_value_dcf·margin_of_safety·asymmetric risk-reward).
- MlFinLab `labeling/labeling.py`: `get_events`/`get_bins` **계약만**(공개판 stub) → triple-barrier 자체 구현.

### 주의·미해결(튜닝)
- H22: BACKTEST 모드 2차 heavy-agent=`ABSTAIN` stub 강제(forward만 실판정) — 코드 반영됨.
- buy-the-dip 차단: 가격↓+내재가치↓ 동반=1차 통과시키되 2차 trap 우선(prev_intrinsic 주입 시 정밀).
- 섹터 팩터 없으면 market+idio 2팩터 degrade. 저신뢰=UNATTRIBUTED.
- 튜닝 미확정값: 1차 임계 X=10%/Y=gap0.25, 지배 임계 0.5, 군집 0.4. DART XBRL·EDGAR accession 실 I/O 는 프로토콜 경계만(외부 구현 대기).

---

## 7. B1 — macro brain 코드 (작성 완료, `core/brain/` ~2,324줄) · 차용=jumpmodels·PyPortfolioOpt·TradingAgents

### 작성 파일 (실구현, 8 smoke test + full pipeline 통과, jumpmodels·pypfopt import 검증 ok)
- `macro_schema.py`(155) — `MacroView`(per-bloc regimes+stance+status+age)·`RegimeEstimate`(regime_now/regime_forecast 분리)·enum(RegimeLabel 4분면·Bloc·ViewStatus). `is_well_formed()`·`degrade_to_stale()`(H29).
- `macro_indicators.py`(240) — `michez_rule(u,v)`(이중임계 0.29/0.81)·`sahm_rule`·`gdp_gdi_divergence`·`yield_curve_signal`·`truflation_lead_signal`·`investment_clock_quadrant(growth,infl)→(label,conf)`.
- `fred_adapter.py`(190) — `FredAdapter` Protocol / `RealFredAdapter`(fredapi, **first_release PIT**) / `NullFredAdapter`(폴백)·`FRED_SERIES` 큐레이션(16+NBER 라벨전용)·`fetch_macro_bundle()`.
- `regime_classifier.py`(477) — `RegimeClassifier.classify()→MacroView`. IC 4분면 + JM/SJM overlay(filter/smoother 발산) + 조건부 상관약화 + forecaster 분리 + per-bloc.
- `regime_to_weights.py`(318) — `regime_to_weights(macro_view,returns,method)→{weights,prior,method,status,caution}`·`ic_target_weights()`(§5.8-B 표 정량화)·BL weight_tilt(기본)·bl_returns(PyPortfolioOpt) 2경로.
- `macro_reasoning.py`(207) — `MacroReasoningNode.enrich(baseline,trigger)`. LLM stance+thesis+반대thesis·C2 abstain·contamination probe hook.
- `indicator_event_correlation.py`(542) — **§5.8-H 상관모델(사용자 추가요구)**: `EVENT_BASELINE`·6 `ANOMALY_CASES`·`conditional_attenuation()`·`IndicatorEventCorrelation(ingest_correction/recall_similar, PIT)`.
- `MACRO_CORRELATION_BACKGROUND.md`(147) — 코드 출처 배경문서(이벤트별 정상패턴·6 이상케이스·조건부약화·학습경로 + macro.md 라인 1:1 + 외부출처).

### 차용(파일:심볼)
- jumpmodels `jump.py:JumpModel`(`.fit(X,ret_ser,sort_by)`/`predict_online`/`labels_`/`transmat_`)·`preprocess.py:StandardScalerPD/DataClipperStd` → `_jump_model_overlay`(import 검증 ok).
- PyPortfolioOpt `black_litterman.py:BlackLittermanModel`(pi/absolute_views/omega=idzorek/tau→bl_weights)·`risk_models` Ledoit-Wolf → `_bl_returns_path`. **cvxpy 회피 위해 sklearn LedoitWolf**로 H25 충족.
- TradingAgents `fundamentals_analyst.py` analyst node 패턴 → MacroReasoningNode(report 대신 구조화 stance JSON).

### 코드화한 것 / 못한 것
코드화: Michez Rule(min(û,v̂))·Sahm·공급충격 발산·GDP-GDI 단절·금리커브 역전무력화·Truflation 선행·M2-인플레 디커플링(통화승수/유통속도)·모기지락인·R*·IC 4분면·선행/동행/후행 SHAP 가중(payrolls 1위). 못함(인터페이스만): Truflation 실시간 API(유료)·near-term forward spread·WALCL·R* 추정(FRED extra 주입경로만)·한국 ECOS(미연동 시 KRW=USD 폴백)·contamination probe 코사인(embedder 미연동).

### wire + 주의·미해결
- wire: portfolio_orchestrator 사이클 → `classify()` baseline(무료·결정론) → macro-trigger 시 `enrich()`(Claude deep) → `regime_to_weights()` 슬리브% → risk_gate 캡·밴드. §5.8-H 루프: `ingest_correction()`→`recall_similar()`→confidence 하향→BL τ·Ω 확대.
- 미해결: JM n_components=2(stress/calm) vs 4분면 직접학습(라벨매핑 모호→규칙우선); attenuation 곱(0.4~0.7) 휴리스틱→보정누적 후 실측 재튜닝; **bl_returns 정통경로는 cvxpy 필요**(미설치 시 weight_tilt 폴백=기본). 리서치 출처(배경문서): NY Fed·FRBSF·Dallas Fed·St.Louis Fed·CBO·Hamilton·López de Prado.
- ⚠️ risk: cvxpy 미설치 시 bl_returns 정통경로 미동작(weight_tilt 폴백 커버), Truflation/ECOS 미연동.

---

## 8. IMPLEMENTATION_PROMPT.md 적용할 정정 (요약)

1. §5.10-C·§6.10: 관리종목 소스 "pykrx"→**FDR `KrxAdministrative`** (A5-①).
2. §5.8: **ALFRED vintage 거시 PIT** 를 명시 작업으로 격상 — FRED realtime_* 직접 호출 (A5-②).
3. §5.10: KrxAdministrative **일별 스냅샷 적재**(PIT) 추가 (A5-③).
4. §5.10: Lean coarse/fine → **Fundamental/FineFundamental** 명칭 + 날짜별 CSV PIT (A5-④).
5. H23/G5: PBO = **CSCV logit-rank 정통식**(skfolio CV + 자체 집계기), yakub268 근사식 폐기 (A3-a).
6. G8: **단일 `common/metrics.py`** 강제(백테스트=라이브 지표함수 공유), coin 3중 중복 제거 (A3-b).
7. §4.2: Judge **2단**(Research Manager→Portfolio Manager+lesson 주입), rounds=1 (A4-d).
8. §5.8-E/§5.9: FinMem decay 3축(recency·importance·decay) + **PIT causal-mask**(as_of 필터) 구체식 (A4-a,b).
9. §5.9-B: AgenticTrading factor 분해 불가(stub) → **자체 factor 회귀**(B2 완료), AT 는 event-stream 배선만 (A4, B2).
10. §0.4: **dexter 자가검증 제외**(부적합), 자가검증=TradingAgents 토론구조 (A4-f).
11. Ledoit-Wolf **PyPortfolioOpt 로 SSOT 단일화**(BL 과 동일) (A2).
12. KIS: 토큰 **24h**(6h 아님), 레이트리밋 **초당**(분당 아님), client_order_id **미지원→앱단**(A1, 기검증).
13. 마이그레이션 **047_ 부터**(051 아님, 실제 48개·최고 046).
14. 멱등성 fallback: 대기주문뿐 아니라 **체결완료 주문 조회**(A1-c).

---

## 9. plan/progress/harness 구조 (예정 — B1 완료 후 확정)

- **plan.md**: Phase -1~6 + R, 각 Phase 의 Sonnet-executable step + reuse-github 매핑(위 §1-§7 코드위치) + §2.9 게이트.
- **progress.md**: step 단위 `model: sonnet`(대부분, Sonnet-executable) / `wf: harness2`(고위험·DB/상태·회귀민감) / `model: opus`(설계판단). XOR.
- **harness2.md**: §2.9 단계별 게이트 = **verifier 검증 핵심**. Pipeline Goal→Phase Final Obj→Sub-obj(관찰가능·원자·커버리지·독립) + Sufficiency Check + RC.
- **착수 권고**: Phase -1 부터(코드검증 완료·외부의존 0·즉시가치). B1/B2 코드는 Phase 1·3 의 시드.
