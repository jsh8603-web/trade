# Inv CODEMAP

> 이 문서는 코드 디버깅 진입점 색인이다. 코드 수정 시 반드시 해당 모듈의 '설계 의도'를 먼저 확인하고, 수정 후 이 문서를 동기화한다. 지표 이론·yaml은 study-research/_wire/ ledger 참조.
>
> 작성 2026-06-07. 목적 = **최종 테스트(10년 백테스트 + 모의계좌) 중 "코드 문제 의심 시 어느 파일을 봐야 하는가"** 즉시 색인.
> 디버깅 진입점 문서 — 증상 → 레벨 귀속(**L0** 배선 / **L1** 이론·설계 / **L2** 코드·데이터·상수 / **L3** LLM) → 해당 단계 모듈.
> 근거 = `.p0-connectivity-map.md`(파이프라인 e2e 연결성) + `README.md`(레이어별 색인·설계이유). README의 "레이어 나열"을 **실행 파이프라인 순서**로 재배치했다.
>
> ★대전제(연결성맵 §1·§2): **현재 끝까지 도는 production 경로는 레거시 코인봇(`scripts/run_agents.py` → `agents/Orchestrator`)뿐**. 신규 `core/` asset-agnostic 트랙·stock 주문 경로는 **production 호출처 0(테스트만)**. risk_gate·judge·core 두뇌는 전부 env opt-in off 기본(byte-identical). 따라서 "어느 경로를 테스트 중인가"를 먼저 확정해야 디버깅 레벨이 갈린다.

## 배선 상태 범례
- **LIVE** — production entry 가 실제 호출(레거시 코인봇 경로)
- **opt-in off** — 코드 배선 완료, env flag off 기본 = 미진입(byte-identical). on 해야 작동
- **호출처0 dead** — 코드 완성, production caller 0 (테스트만 인스턴스화)
- **stub/미구현** — 의도적 stub 또는 실 배선 미작성

## 디버깅 레벨 정의
- **L0 배선** — 모듈이 호출되지 않음 / env off / entry 미작성. "코드는 맞는데 안 탄다". → 연결성맵 §2 미연결표 먼저 확인.
- **L1 이론·설계** — 신호·관계·불변식 설계 자체. README "설계 결정 이유" + study-research / decisions.
- **L2 코드·데이터·상수** — 함수 버그·threshold·데이터 빈도/커버리지·PIT 누수. 해당 `.py` + self-test.
- **L3 LLM** — LLM 비결정성·OAuth·환각·비용. 단 down-only 불변식이라 LLM 이 베팅을 키우는 경로는 코드상 없음(env off 면 무관).

---

# 파이프라인 실행 순서

진입점이 둘이다. (A) **레거시 코인봇** = 라이브 production. (B) **core asset-agnostic 트랙** = 호출처0(테스트만). 백테스트 엔진은 둘과 별개 entry. 아래는 논리적 파이프라인 순서(데이터→…→주문)로 두 경로를 합쳐 단계화했고, 각 모듈에 어느 경로 소속인지 표기한다.

---

## 0단계. 진입·안전 선검사 (게이트 0)

| 파일경로 | 핵심 함수 | 기능 | 설계 의도 | 배선 상태 |
|---|---|---|---|---|
| `scripts/run_agents.py` | `main()` (:520-536 EMERGENCY 체크) | 레거시 파이프라인 6 Phase 오케스트레이션 | 매매 로직을 LLM 에 안 떠넘기고 Python 에이전트가 직접 결정(빠름·저렴·코드 추적). cron 4h | **LIVE** |
| `scripts/execute_trade.py` | 안전장치 우회불가 순서 | Upbit 시장가 + EMERGENCY_STOP→auto_emergency→DRY_RUN→일횟수→간격→비율→보유량→MAX_TRADE_AMOUNT 순 | 실자산이라 버그=손실. EMERGENCY_STOP 을 DRY_RUN 보다 먼저, MAX_TRADE_AMOUNT 는 모든 경로 후 절대 클램프. SACRED diff=0 | **LIVE** |
| `data/auto_emergency.json` | (플래그 파일) | 감독 자동 긴급정지 상태 | 4h −10%·연속손절 5회+ 발동, 해제=12h+급락종료+공포완화. 수동 EMERGENCY_STOP 은 감독 해제 불가 | **LIVE** |

**디버깅 노트**: 주문이 안 나간다 → 먼저 **L0/L2**. `DRY_RUN` env, `auto_emergency.json` 존재 여부, `EMERGENCY_STOP` 순으로 확인(execute_trade.py 내부 선검사). 의도된 차단을 버그로 오인 금지. 실거래 전환(`DRY_RUN=false`)은 사람 게이트.

---

## 1단계. 데이터 수집

| 파일경로 | 핵심 함수 | 기능 | 설계 의도 | 배선 상태 |
|---|---|---|---|---|
| `scripts/collect_market_data.py` | (subprocess) | Upbit 시세+RSI/SMA/MACD/BB | run_agents.py:411-426 asyncio.gather 병렬 | **LIVE** |
| `scripts/get_portfolio.py` | (subprocess) | 계좌 잔고·평단·수익률 | 위 병렬 묶음 | **LIVE** |
| `scripts/collect_ai_signal.py` | (subprocess) | AI 복합 시그널 6종 | 위 병렬 묶음 | **LIVE** |
| `agents/external_data.py` | `ExternalDataAgent.collect_all()` | 뉴스랑 11소스 병렬 수집 + Data Fusion | run_agents.py:574 ThreadPoolExecutor, 하나 실패해도 나머지 정상(에러 격리) | **LIVE** |
| `scripts/collect_rss_news.py`·`collect_x_signals.py`·`collect_social_sentiment.py` | — | RSS 16피드 / X 7계정 / 소셜 감성 | 확장 3소스 | **LIVE** |
| `core/data/` (substrate) | `pit_query`·`pit_panel`·`vintage`·`fx`·`calendar`·`identity`·`corp_action`·`universe_membership`·`instrument_source` | bitemporal PIT 데이터 substrate — "그때 알 수 있던 것"만 | 미래 정보 1톨이라도 먹으면 silent alpha 누수. T2/T3 는 `pit_query` 로만 조회(raw parquet 직접=금지). 2중 게이트 `knowable_from≤as_of ∧ sys_time≤as_of` | **opt-in off** (core 트랙 경유 시. 레거시 미사용) |
| `core/data/event_ledger.py` | `make_event`·`reduce_events`·`LedgerState.resolve_fact` | 가정 라이프사이클 진실원(L1) — 12 event type·3 typed timestamp(tt/dt/vt) | append-only + CQRS(log=진실원 / snapshot=tt-cut reduce). REVISION_OBSERVED 는 OUTCOME mutate 안 함(새 fact) | **opt-in off** |
| `core/data/data_contract.py` | `check` (:171) | Pandera 계약 게이트 + ingestion checksum | 계약 위반=측정 incident(가정 틀림 아님). silent_rewrite(벤더 무통지 덮어쓰기) fingerprint 재대조 | **opt-in off** |
| `core/brain/fred_adapter.py` | `get_series(id, as_of)` | FRED/ALFRED vintage PIT 경계 | first_release(핫패스)/vintage(백테스트). USREC=학습 라벨 전용. NullFredAdapter graceful degrade. ★fetch 캐시(MEMORY: build 255s→29s) | **opt-in off** (core 트랙) |
| `core/data/reserve_snapshot.py` | (CM live fetch) | 거래소 reserve forward-OOS 수집기 | Phase0a 신호게이트 산물. Windows task 매일12:00. vintage 동결 | **수집 전용 dormant** — `core/data/reserve_snapshot.py` + cron `.bat` 만 존재. 어떤 매매 경로도 소비 안 함. Phase0a 신호게이트 GREEN 전까지 비활성 |

**디버깅 노트**:
- 수집 단계가 비면 → **L2**(subprocess 실패·API rate limit·키 부재). 레거시는 subprocess 격리라 한 소스 실패해도 진행.
- 백테스트에서 과거 값이 이상 → **L2 PIT 누수**. `vintage.realtime` vs `final()` 혼용, `pit_query` 우회(raw parquet 직접 필터) 의심. `core/data/adversarial_replay.py`(1급 CI 게이트)로 taint isolation 검증.
- core 트랙 데이터가 안 들어옴 → **L0**(INV_R15_WEIGHTS 등 off → fetch_sleeve_returns dormant).
- reserve_snapshot 은 수집 전용 dormant — 매매 경로 소비 없음이 정상. Phase0a IC 검증 후 배선 예정.

---

## 2단계. 지표 / feature → regime 판정

| 파일경로 | 핵심 함수 | 기능 | 설계 의도 | 배선 상태 |
|---|---|---|---|---|
| `agents/base_agent.py` | `detect_regime` (:757) | FGI/RSI/SMA 룰 기반 레짐(bull~crisis 5단계) | 레거시 결정론 레짐 | **LIVE** (레거시) |
| `scripts/regime_detector.py` | `detect_regime` | run_agents.py:689 호출 레짐 감지 | ★`core/brain/regime_classifier` **아님** — 레거시는 별 경로 | **LIVE** (레거시) |
| `core/brain/regime_classifier.py` | `classify(as_of)` (:95) → `MacroView` | 결정론 거시 레짐 4분면(Investment Clock) baseline | brain 매 사이클 무료 baseline. JM/SJM 2상태 overlay + Michez/Sahm/금리커브/GDP-GDI override. JM filter vs smoother 발산으로 confidence 감쇠(학습 harvest) | **opt-in off** (core 트랙. INV_CORE_GATE on 시 로깅용 1회만, 결정 미반영) |
| `core/brain/macro_indicators.py` | `michez_rule`·`investment_clock_quadrant`·`yield_curve_signal`·`gdp_gdi_divergence` | macro.md 정량 법칙을 순수함수로 코드화(PIT-safe) | HMM 대신 Investment Clock+JM(regime 외생화=소표본 회피). 경계 근처 신뢰도 낮게→reasoning 에스컬레이션 | **opt-in off** |
| `core/brain/macro_schema.py` | `MacroView`·`RegimeEstimate`·`degrade_to_stale`·`unavailable` | 거시 출력 공통 계약(SSOT). FRESH/STALE/UNAVAILABLE 3단 | regime_now(classifier) vs regime_forecast(forecaster) 분리=전환 임박 신호. outage→last-good 재사용 | **opt-in off** |
| `core/brain/indicator_event_correlation.py` | `conditional_attenuation`·`recall_similar` | 오판 피드백 — 정상상관/decoupling 6+1/보조지표 임계→상관 동적 약화 | López de Prado 메타라벨링 거시 어댑트. caution 메모리지 hard 재학습 아님(regime 에피소드 드뭄=PBO 회피) | **opt-in off** |
| `core/brain/correction_loop.py` | `harvest_from_jm`·`attach_to_classifier` | dead 학습 쓰기 경로를 live 루프로 배선 | classifier 가 버리던 JM 발산을 harvest. read/write 동일 model 인스턴스 공유=즉시 반영 | **opt-in off** |
| `core/regime/`·`core/pit/pit_regime.py` | K=3 결정론 분류 + `regime_discovery`(BOCPD+Hotelling T²) | 외생 regime 정의 + 신규 regime 발견(자동)·승격(사람) | endogenous partition=소표본 라벨 불안정·반사성. 발견 자동·승격 HumanApprovalGate | **opt-in off** |

**디버깅 노트**:
- ★**레거시 테스트 중 레짐이 이상** → `scripts/regime_detector.py` + `agents/base_agent.detect_regime`(**L2**). `core/brain/regime_classifier` 를 보는 건 헛다리(레거시 미사용).
- core 트랙 레짐이 이상 → **L1**(regime 정의·임계) 또는 **L2**(JM 미설치→규칙 단독 degrade, `_jump_model_overlay`). MacroView status=UNAVAILABLE 면 하류 중립 de-risk 의도된 동작.
- 거시 신호가 "정의대로 안 움직임" → **L1** decoupling 설계(indicator_event_correlation 의 ANOMALY_CASES) 의도 확인 후 L2.

---

## 3단계. 가정·통계 검증 (e-process / FDR / glasso)

| 파일경로 | 핵심 함수 | 기능 | 설계 의도 | 배선 상태 |
|---|---|---|---|---|
| `core/structure/` (e-process 백본) | `MixtureSPRTEProcess.update`·`ELOND`·`LordPlusPlus`·`HierarchicalFDRCascade`·`EProcessSpender` | anytime-valid 가정 검증 substrate | 연속 모니터링=optional-stopping false-discovery + regime 자기상관으로 p값 독립 깨짐. Ville 부등식이 임의정지·임의의존 robust | **opt-in off** (study/assume 경유) |
| `core/structure/` (glasso) | `RegimeGlasso.fit`·`effective_precision(models, belief)` | regime-conditional 조건부 상관 학습(R15 통계 본체) | nonparanormal→EBIC glasso(γ=0.5 고정=CV 회피 결정론)→EB shrinkage. cov-space belief-mix 1회 역행렬(이중 mix 금지). regime 모호 시 between-dispersion 항이 risk 자동 inflate | **opt-in off** |
| `core/assume/` (라이프사이클) | `registry`·`validator`·`update_controller`·`dag`·`judge` | 가정 카드 append-only 버전·PIT·lifecycle | 비대칭 게이트: RETRACT=disjunctive fast / ADOPT=conjunctive 5조건 AND slow / base-layer=human. 측정깨짐≠정의틀림(data_contract 위반=SKIP) | **opt-in off** |
| `core/assume/reject_recovery.py` | `evaluate_recovery`·`should_trigger_revival` | reject 가정 production 자동 재진입(IC9, §14 R11) | logging 아닌 무인집행. hysteresis 5-AND + class C 격리(DATA_EVENT 전차단). convex-leak e-process | **호출처0 dead** (자동격리, go-live 경계) |
| `core/assume/graduation.py` | `evaluate_graduation`·`graduation_sweep` | candidate→ratified 자가승격(IC4) | 5-AND hysteresis + StudyRegister 자가승격 가드 + 사이클경계 idempotent | **호출처0 dead** |
| `core/structure/structure_model.py`·`archetype.py` | `cheapness_z`·discriminated union 11종 | "싸다"=구조모델 잔차(밸류트랩 분리) + 자산 아키타입 | 잔차≈0=밸류트랩(drivers 가 낮은 멀티플 설명). cyclical=peak-EPS trap 등 | **opt-in off** |

**디버깅 노트**:
- 가정 카드가 안 뜨거나 안 사라짐 → **L1**(falsification power=0? `falsification_protectable`) 또는 **L2**(e-process update 키 `(dt,vt)` 누수). small-n 보고면 `~/.claude/rules/small-n-statistical-rigor` 게이트 적용 대상.
- 이 레이어는 "관측·산출만, 결정 안 함"(README). 따라서 매매가 틀어져도 여기는 1차 용의자 아님 — **배분/사이징/게이트(4~6단계)** 먼저 의심.

---

## 4단계. FHC 가설 발권 (LLM down-only, `core/assume/`)

| 파일경로 | 핵심 함수 | 기능 | 설계 의도 | 배선 상태 |
|---|---|---|---|---|
| `core/assume/fhc.py` | `FHCard` + 5-state machine | minted→confirmed→vacated→rejected→revived + 2-leg(mediator/outcome e-process) | minted→vacated 금지·rejected absorbing·fail-closed(UNKNOWN→보너스 미적립) | **opt-in off** |
| `core/assume/bonus_channel.py` | `size_with_bonus` (:44) | `clip(L1 + Σbonus, 천장 C)` | (B)강화는 L1 초과 가능하되 천장 C 가 진짜 불변식. breaker_tripped→bonus 0 즉시 | **opt-in off** (FHC_BONUS) |
| `core/assume/fhc_fdr.py`·`macro_mediator.py`·`spanning_gate.py`·`info_delta_gate.py` | INV-12 firewall / mediator posterior / 직교성 게이트 / rate-cap+델타 | 발권 판정 게이트 | spanning_gate: α≈0=위장(차단) / α유의+잔차 forward IC=진짜 알파(Newey-West, n<20 INSUFFICIENT). info_delta: 임베딩 novelty(LLM 추론 0) | **opt-in off** |
| `core/assume/active_loop.py`·`research_ingest.py`·`loop_factory.py`·`security_news_loop.py` | `build_active_loop(use_claude)`·`build_research_ingest`·`retrieve` | 능동 발권 7-step + 증권리포트 ingest(Haiku 요약→BGE 임베딩→PIT) | 결정론이 못 푸는 6유형에서만 LLM 우위. loop_factory=실 LLM/임베딩 배선(Claude OAuth+DaService BGE-m3 8787) | **opt-in off** (ACTIVE_LOOP_SHADOW) |

**디버깅 노트**:
- ★발권 카드는 전부 `probationary`(bonus_cap=0)=**자본0**. LLM 이 카드를 발권해도 go-live arming(사람 게이트) 전엔 배분 미투입 → 백테스트/모의 결과에 영향 없어야 정상. 영향 있으면 **L0 불변식 위반**(env off 인데 진입?) 의심.
- LLM 호출 비용·OAuth 429 → **L3**. OAuth 정책: `anthropic-beta: oauth-2025-04-20` 헤더 + system="You are Claude Code..." 필수(누락 시 429 위장거부). 백테스트엔 ACTIVE_LOOP_SHADOW/MACRO_ENRICH/MACRO_CONSENSUS **전부 off** 권장(비결정성=PIT replay hash-pin 위반).
- 거시 RAG 결과가 빔 → **L0-8**(거시 증권리포트 소스 미구축, graceful). 종목 on_news ingest 는 실동작.

---

## 5단계. 사이징 (멀티에셋, 결정론)

| 파일경로 | 핵심 함수 | 기능 | 설계 의도 | 배선 상태 |
|---|---|---|---|---|
| `agents/base_agent.py` | `kelly_position_size` (:60)·`calculate_buy_score`·`evaluate_sell` | 점수제 매수(FGI30+RSI25+SMA25+뉴스20) + 하이브리드 손절 + Half-Kelly | 단일 규칙은 노이즈 취약→약신호 가중합산. confidence 배수×Half-Kelly, MAX_TRADE_AMOUNT 절대 상한 | **LIVE** (레거시 실 사이징) |
| `core/risk_sizing.py` | (vol-target 역변동성) | Ledoit-Wolf 공분산→변동성 타깃 | ill-conditioned(cond>1e6) 또는 평균 corr>0.80→Riskfolio HRP tail fallback(w_max 0.10). 단일자산=1.0 | **호출처0 dead** (core 트랙) |
| `core/coin_sizing.py` | (위임) | 단일 BTC→risk_sizing 위임, 멀티코인만 tail HRP | Kelly/LW 재작성 금지. H25 crisis: 상관 과열(0.75)→BTC cap 0.40. risk_gate.check 경유 필수 | **호출처0 dead** |

**디버깅 노트**:
- ★레거시 NAV/사이징 이상 → `agents/base_agent.py`(**L2**). 점수 임계·Kelly 배수·MAX_TRADE_AMOUNT 클램프.
- ★**과거 진단 경고(MEMORY)**: `MAX_WEIGHT_SINGLE` = `core/risk_gate.py:47` = `float(os.environ.get("RISK_MAX_WEIGHT_SINGLE", "0.10"))` — env 기본 0.10. 단일자산 백테스트 NAV 를 압살하는 컨텍스트 미스매치(멀티에셋 분산용 10% 천장을 단일자산에 적용). scale-invariant 지표(Sharpe/IC)엔 무관, NAV 절대수익만. 우회=`RISK_MAX_WEIGHT_SINGLE=0.95` env(라이브 무손상). 단일자산 백테스트 NAV 가 낮으면 **L0/L2 컨텍스트 미스매치** 1순위.
- ★**과거 진단(MEMORY)**: coin 3에이전트 코어점수(공포+RSI과매도+SMA하향이탈)=mean-reversion 인데 BTC 단기=momentum→rank-IC −0.08~−0.11 음(역방향). 신호 방향이 의심되면 **L1**(trend-gate). trend-gate(B안) 는 `base_agent` 에 **production 미배선** — `.p2-trend-gate.py`(실험 스크립트)·`scalp_ml/feature_engineer.py`(별개 모듈)에만 존재. 현재 forecasting-object 검증 단계이며 production 진입 전.

---

## 6단계. risk_gate (우회 불가 백스톱)

| 파일경로 | 핵심 함수 | 기능 | 설계 의도 | 배선 상태 |
|---|---|---|---|---|
| `core/risk_gate.py` | `RiskGate.check` (:308)·`GatedOrderRouter.submit`·`KillSwitch` | 전 트랙 최종 안전 게이트, 항상-on 결정론(LLM import 0) | architecture §6 "위험주문 반드시 막힘+우회불가". `via_gate=False`→즉시 REJECTED+bypass 카운트. fail-closed(NaN/inf→REJECTED). KillSwitch MDD−15%→HALTED(자동 전량청산 금지, 사람 confirm) | **opt-in off** (레거시 INV_CORE_GATE on 시만 buy/sell 직전 1회. on 이어도 current_weight/sector/corr 미전달=부분 검사) |

**디버깅 노트**:
- ★레거시 라이브는 risk_gate 기본 **미연결**(INV_CORE_GATE off). 게이트 검증하려면 `INV_CORE_GATE=true`(연결성맵 §5-3). → 주문이 차단 안 되는 게 정상일 수 있음(**L0-3**).
- on 인데도 일부 룰 안 걸림 → **L0** 부분 검사(current_weight/sector_weight/avg_correlation 미전달, 연결성맵 §1 28번줄).
- 게이트가 과차단 → **L1**(precedence 격자: kill>안전스톱>캡>세금/보유>리밸런스) 또는 **L2**(threshold: per-position −5%/−10%, 단일10%·섹터30%, turnover20%, corr>0.7 차단). `risk_gate.py:47 MAX_WEIGHT_SINGLE` = 5단계 노트 참조.
- via_gate=False 가 REJECTED → 의도된 동작(우회 차단). 버그 아님.

---

## 7단계. judge (고-스테이크스 LLM, down-only attenuator)

| 파일경로 | 핵심 함수 | 기능 | 설계 의도 | 배선 상태 |
|---|---|---|---|---|
| `core/assume/judge.py` | (L1∥DCF + L2/L3 attenuating) | `final = L1·a2·a3 ∈ [0, L1]` | LLM/agent 는 감쇠만, 증폭 절대 불가(down-only). ★Claude "최종 결정" 경로는 코드에 **없음**(judge=attenuator a∈[0,1]) | **opt-in off** |
| `core/consensus.py` | `ConsensusJudge.run` (:221) | 고-스테이크스 2단 Judge(Layer1 LLM 구조화→Layer2 risk_gate 백스톱) | is_high_stakes False→즉시 stub(비용0). 거부 시 approve여도 hold 강제 | **호출처0 dead** (production 미호출, 테스트만) |
| `core/brain/consensus_node` | `build_consensus_node(use_claude)` | portfolio_orchestrator 의 consensus de-risk(별 경로) | MACRO_CONSENSUS on + is_high_stakes(regime flip/배분≥10%/누적≥25%)→down-only de_risk clip[0,1] | **opt-in off** (MACRO_CONSENSUS) |
| `backtest/engine.py` (judge_hook) | engine.py:447-474 | 백테스트 매 buy bar judge | 기본 None=호출0. 주입 시 fail-open a=1.0, final≤L1 | **opt-in off** (judge_hook 미주입 기본) |

**디버깅 노트**:
- judge 가 사이징을 키운다 → **L1 불변식 위반**(down-only 깨짐). final≤L1 천장(`assert_ceiling_invariant`) 확인. 사용자가 기대하는 "Claude 최종결정+강화" 는 코드에 없음(L0-6, judge 재설계 대상).
- 백테스트에서 judge 가 수천번 호출 → **L0** judge_hook 주입 여부. 10년×일봉 LLM hook=비용·비결정성 폭증. 반드시 결정론 hook 또는 미주입.
- consensus 미호출 → 정상(production caller 0). portfolio 경로의 consensus 는 별도(consensus_node).

---

## 8단계. 자산배분 오케스트레이션 (최상위, core 전용)

| 파일경로 | 핵심 함수 | 기능 | 설계 의도 | 배선 상태 |
|---|---|---|---|---|
| `core/portfolio_orchestrator.py` | `allocate` (:114) | regime→macro→weights 체인(BL 메인, HRP→IC prior 폴백). 슬리브 합=1. ★게이트 통일(:157) `is_r15_enabled()`(on/true/1/yes) — 기존 `=="true"` 단독은 "on"으로 켤 때 belief 동적공분산 silent-death 함정 | ★**allocate 는 risk_gate 호출 안 함**(:195-197) — "배분 산출 자체는 게이팅 안 함, risk_gate.check 는 개별 트레이드 진입 시 호출자가 적용". Drift Monitor SLEEVE_BANDS. H26 FX/H29 macro abstain | **LIVE(--backtest)** — `run_multiasset.py --backtest`(INV_R15_WEIGHTS=true) + `coin_track_macro._macro_orch` 경유. 레거시 라이브는 미호출 |
| `core/brain/regime_to_weights.py` | `weight_tilt`·`bl_returns` | 레짐→슬리브 % 배분(BL 메인, IC-prior 폴백) | ⚠️ R15 가중(종목 판정)과 다른 레이어(자산배분). confidence 낮을수록 Prior 근접, Ledoit-Wolf 고변동 억제, long-only+재정규화 | **opt-in off** |
| `core/portfolio_decompose.py` | `decompose_weight(parent_sleeve, parent_weight, mktcaps, *, method, factor_z=None)` · `_load_us_weight_ranges` · `_modulated_us_weights` | 배분 sleeve weight → 업종 sub-sleeve weight 분해(coarse→fine). SLEEVE_AGG(roll-up fine→coarse)와 방향·목적 반대=재사용 부적합 | 기본=시총비례(cap)/equal fallback. ★**W3 eq_us weight_rules 배선 완료(2026-06-08, 18축 ⑱ 해소)**: `study_session.yaml` 블록4 base_weight_range 를 `_load_us_weight_ranges` 로 파싱 → `factor_z`(real_rate z) 주어질 때만 study 보간. **데이터 실측 calibrate**(`.p4-w3-sensitivity.py`, factor z→산업 forward 수익 rank-IC+walk-forward): ① **defensive ← real_rate z** 선형보간 `w=clip(mid−k·z·half, BAND_LO, BAND_HI)`(z↑→비중↓ = study β−0.066 + forward IC−0.334 p<0.001 n=184 walk-forward 일관 정합). ★**study weight_rules 보존(2026-06-08 full range 복원)**: study `base_weight_range[0.10,0.28]` 전체를 작동밴드로(mid=0.19, **k=0.5**, z=±2σ서 study range 끝 0.10/0.28 도달, 극단 z clip, 단조·임계 스위치 X). ⛔base_weight_range 자체가 소표본 hedge(점추정 회피)라 추가 축소(하위밴드)=yaml 분석 죽임이라 금지. defensive raw 진폭 study range 전체 0.18(z±2σ) ② **mega_tech**=고정 mid(regime_modulate=false, real_rate forward OOS flip 확증) ③ **cyclical**=cap 보류 확정(study β동시−0.120 vs forward+0.460 contrarian **부호 충돌**+forward 생존15~20% OOS>IS V자반등 과적합 → regime 변조 미적용, ⛔즉흥 부호 선택 금지). ★W3 1차 regime 일반론 틸트(`_REGIME_SECTOR_GRADE` Investment Clock)=근거부재 롤백됨. ★**factor_z=None ⇒ cap/equal byte-identical**(off 불변식). 한국=`_rotation` 고유 cycle(나프타/철광석/리튬) 미배선(잔여) | **LIVE(--backtest)** — `run_multiasset._bt_us_picks(real_rate_z=as_of PIT z)` 경유. `_bt_real_rate_z`=DFII10 월말 rolling z(36M, FRED PIT). FRED unavailable→None→cap graceful. ★**mega_tech ④집계 복원(2026-06-08)**: `_bt_load_us` 가 universe.parquet 부재(mega_tech=11종 custom basket)면 prices.parquet 컬럼을 fallback universe 로 사용 → 이전 `tks=[]`→mega_tech holdings 전멸→④산업간배분 누락 해소(cyclical/defensive universe 존재=byte-identical). ★**defensive 수익 변동(W3 비중↓→ind_ret_hist)=정상 효과**: risk_gate 가 sec_w/cur_w(max_weight_single/sector) 에 반응(APPROVED→REDUCED)해 분기별 통과 g 변동=프로덕션 의도 동작(측정 버그 아님) |
| `core/brain/regime_belief_adapter.py` | `belief_from_macro_view` | MacroView→belief 분포 b(t) | confidence 高→집중, 低→평탄(between-dispersion inflate=transition de-risk). unavailable→uniform(최대 de-risk) | **opt-in off** |
| `core/fallback_policy.py`·`budget_ledger.py` | H27/H26/H29 + LLM 예산 회계 | confirm 타임아웃 시간분산 축소(전량청산 금지) / LLM soft limit | de-risk 는 청산·리밸런싱 계속(liveness 디커플링). 예산 e^|Drop| 지수증폭 금지 + RPM 10/min | **opt-in off** |

**디버깅 노트**:
- ★배분이 risk_gate 통과 안 함 → **의도된 설계**(L0-2). 게이트는 order path 호출자가 적용해야 하는데 그 호출자가 production 에 없음(L0-4).
- weights 가 "BL prior 근처에서 안 움직임" → ★**버그 아님**(MEMORY): stance 비면 π=δΣw 항등식으로 cov 상쇄=정상. stance 있을 때만 배분 작용(의도된 BL). macro_view(stance) 약하면 degenerate.
- 합≠1 → **L2**(재정규화 누락).

---

## 9단계. 주식 트랙 selection → 주문 실행 (core 전용, 전부 dead)

| 파일경로 | 핵심 함수 | 기능 | 설계 의도 | 배선 상태 |
|---|---|---|---|---|
| `core/stock_track.py` | `generate_candidate` (:165) | run_value_trigger 2단→Decision→`_apply_r15_sizing`(down-only 천장) | valuation=override 또는 fundamentals+quote 있으면 value_stock, 둘 다 없으면 abstain stub | **호출처0 dead** |
| `stock/value_trigger.py` | `run_value_trigger`(2단) | 1차(가격−10%∧갭≥0.25)→2차 trap 판정 | 단순 buy-the-dip 금지(가격↓+내재가치↓=매수 아님). H22: BACKTEST=heavy-agent ABSTAIN stub(LLM 미래오염), FORWARD만 실판정 | **호출처0 dead** (BACKTEST 모드 의도적 stub) |
| `stock/valuation.py` | `value_stock` | bear/base/bull DCF0.45+EV/EBITDA0.30+RIM0.25 확률가중→valuation_gap | ai-hedge-fund 수식을 PIT Fundamentals 입력으로 재설계 | **호출처0 dead** |
| `stock/selection_pipeline.py` | `build_universe_candidates` (:39, StockTrack at :110) | select_cross_sectional + make_trap_veto + StockTrack | 횡단면 선별 | **호출처0 dead** |
| `stock/construction.py` | `build_sleeve_decisions` (:98) | sleeve 단위 조립 + ETF fallback dispatch | env `ETF_FALLBACK` off 기본=byte-identical. N≥5∧passive-ETF→RepresentativeETFSelector / 약변별→EwBasketSelector | **opt-in off** (ETF_FALLBACK) |
| `stock/selector.py` | `Selector` ABC·`CheapnessSelector`·`EwBasketSelector`·`RepresentativeETFSelector` | 선정 추상 | 위험단어=ETF 아니라 "과거수익률 높은". 리턴-랭크→대표성-랭크 치환(momentum chasing 회피). ETF=value 2단 '안 부름'(우회 아님) | **opt-in off** |
| `stock/order_assembly.py` | `assemble_stock_orders` (:92, broker submit :135-156) | GatedOrderRouter.submit(via_gate=True)→approved+dry_run=False+broker→broker.order() | 주문 조립. broker 자리가 KisClient | **호출처0 dead** |
| `stock/admission.py` | `check_admission` | coarse(Tier)+fine(KRX 상태)+지역 3단 | 선물/옵션/마진 영구금지, 레버리지 ETF allowlist 없으면 거절, requested_by_llm=True 즉시 차단(LLM 유니버스 확장 불가) | **호출처0 dead** (loop_factory D 경유 import) |
| `stock/kis_client.py` | `KisClient.order`·`_ensure_pykis`·`_check_safety`·`_clamp_to_balance` | pykis 2.x 래퍼(모의 우선). order/modify/cancel/poll/ws/token | paper=True 시 모의키 양슬롯 주입(실전 도메인 미호출). credential 부재→`_stub_order`(uuid, 실 네트워크 0). H15 원번호/H17 ±30%/H18 USD→KRW | **stub** (어댑터·모의 배선 완료, production 주입 호출처 없음=실 왕복 미실행) |
| `stock/data/` | `PITFundamentalsAdapter`·DART/EDGAR provider·`krx_universe`·`etf_pit.py` | filing_timestamp≤as_of+non-RESTATED PIT | "현재 재작성값"=lookahead. announcement-date 정렬만, RESTATED 거부. etf_pit=AUM 우선순위+1일 lag | **호출처0 dead** |

**디버깅 노트**:
- ★주식 경로 전체가 **production 호출처 0**(L0-1·L0-4). "코드는 완성됐으나 어떤 entry 도 호출 안 함". 모의계좌 테스트하려면 멀티에셋 entry + KisClient(paper=True) 주입 + credential 필요(연결성맵 §5-6, 사람 게이트).
- KIS 주문이 stub uuid → **L0/L2**(credential 부재→`_stub_order`). 실 모의 왕복은 `appkey/secretkey/account_no/hts_id`(pykis 2.x 필수) + paper=True 필요(kis_client.py:124).
- value_trigger 가 BACKTEST 에서 ABSTAIN → **의도된 stub**(H22, LLM 미래오염 차단). 버그 아님.
- ★value alpha 측정 = **횡단면 cheapness rank-IC**(`value_stock.valuation_gap`/`cheapness_z` 의 forward-return Spearman). 진단 하네스 = `diagnostics/p3-stock-pipeline/xsection_value.py`. ★설계상 cross-sectional rank-IC 는 **시장 공통이동에 불변**(상대 랭킹)=이미 시장중립. 따라서 단일 SPY 선도수익 상수 차감(`f-spy_f`)은 rank-IC 에 no-op(순위 불변, raw IC 와 완전동일)·L/S 에도 상수 상쇄 → 무의미. **fix(2026-06-08)**: 종목별 β 차감(`f-β_t·spy_f`, β_t=추세 252d OLS)으로 교체=베타중립 IC(value 저베타 틸트를 alpha 와 분리). 베타중립 IC ≠ raw IC 이면 alpha 가 베타 너머 생존. 측정값 이상 시 **L2**(측정 방법론, 진단 스크립트).
- ETF fallback 이상 → **L1**(라우팅 등급 within_industry_residual) 또는 **L2**(etf_pit AUM/PIT lag). ETF_FALLBACK on 시 `stock/construction.py`·`stock/order_assembly.py` 에 코드는 존재하나 주문 경로(L0-4) 자체가 dead — **백테스트 미검증** 상태. 실 검증 전까지 ETF_FALLBACK on 효과 미확인.

---

## 10단계. 주문 실행 (LIVE = 레거시만)

| 파일경로 | 핵심 함수 | 기능 | 설계 의도 | 배선 상태 |
|---|---|---|---|---|
| `scripts/execute_trade.py` | (0단계 참조) | Upbit 시장가 bid/ask | run_agents.py:929-948 subprocess. DRY_RUN 게이트 내부. PID 파일락 이중주문 방지 | **LIVE** |
| `core/coin_shadow.py` | OrderState FSM | shadow-live(H19) DRY_RUN 경로 실주문 0건 | identifier=uuid4(H9 멱등성). SACRED: execute_trade.py diff=0 | **opt-in off** |
| `scripts/run_agents.py` (Unattended FSM) | `DeriskExecutor(FakeExchange())` (:891-918) | de-risk 자동 단계청산(IOC) | INV_UNATTENDED_FSM on. ★FakeExchange=stub(실거래소 어댑터 go-live 이연) | **opt-in off + stub** |
| `scripts/notify_telegram.py` | — | 매매결과/에러/요약 MarkdownV2 | run_agents.py:1002 | **LIVE** |
| DB 기록 | decisions/market_data/execution_logs | Supabase 감사 테이블 | run_agents.py:1006+ | **LIVE** |

**디버깅 노트**:
- 주문 미발송 → 0단계 안전장치(**L0/L2**) → DRY_RUN. 의도된 차단 vs 버그 구분.
- Unattended de-risk 가 실거래소 안 침 → **stub**(FakeExchange, L0-7). go-live 이연.

---

## 백테스트 엔진 (별도 entry, off 경로 LIVE)

| 파일경로 | 핵심 함수 | 기능 | 설계 의도 | 배선 상태 |
|---|---|---|---|---|
| `backtest/engine.py` | `BacktestEngine.run` (:308), W1 hard-branch (:330-332) | AssetTrack 계약 경유 코인·주식 동일 코드 | `use_risk_pipeline=False`(기본)→`_run_legacy`(verbatim 동결, byte-identical) / True→`_run_risk_pipeline`(PortfolioState+GatedOrderRouter via_gate+judge_hook). 슬리피지 거래대금 비례(고정상수 아님) | **LIVE(off 경로)** — run_replay 가 `_run_legacy` 로 돔 / risk_pipeline on=테스트만 |
| `scripts/run_replay.py` | `BacktestEngine(...)` (:121) | 코인 replay entry(use_risk_pipeline 미지정=off) | production replay 진입점 | **LIVE** |
| `scripts/run_multiasset.py` | `run_backtest` (:614), `main --backtest` | 멀티에셋 거시 자산비중 백테스트 entry(프로덕션 경로 하네스): collect_market_state(거시)→portfolio_decompose(업종분해)→build_sleeve_decisions(종목)→종목마다 judge_hook+GatedOrderRouter.submit(via_gate)→통과분 회계 | ★프로덕션 모듈 직접 호출(별도드라이버 우회 청산, R5 정정). `INV_R15_WEIGHTS="true"`(run_backtest 내부 set)로 거시 자산비중 regime 반영, `load_dotenv`(main)로 .env FRED키 로드. engine.py 와 별 entry(engine=단일 sleeve AssetTrack 시계열 / run_multiasset=거시+업종+종목 멀티에셋). ★17축 attribution 출력(축 정의=CLAUDE.md §📐17축). ⑯ conf 추출=`RegimeEstimate.confidence_now`(이전 `confidence` 오타→conf=? 버그 fix, 2026-06-08). W2 진단=②corr **coin in/out** 양측 + Spearman + regime 에피소드 타임라인(coin outlier 가설·Stagflation 단일점 여부 검정). ⚠️**W3 1차(2026-06-08) = 롤백 대상**: `_bt_us_picks`/`_bt_kr_picks`에 regime 전달로 일반론 틸트 도달시켰으나 **부호표 근거 부재**(산업간 regime 실측 없음 — ledger §2는 자산군 레벨). ★진짜 해법 = eq_us `weight_rules`(base_weight + `regime_modulate` factor sensitivity) 런타임 배선 = 18축 ⑱(yaml↔런타임) 누락 해소. 한국 = `_rotation` 고유 cycle 신호 배선(현 런타임 0) | **LIVE(--backtest)** |
| `backtest/coin_engine.py` | `run` (:68) | 24/7·얇은 알트 임팩트 2배 변형 | coin 전용 래퍼 | **LIVE** |
| `backtest/walk_forward.py` | `run` (:135) | skfolio CombinatorialPurgedCV IS/OOS + purge+embargo | 생존편향(H5): UniverseManager 백테스트엔 상폐 포함, 라이브만 제외 | **opt-in off/dead** — `scripts/run_replay.py` 에 walk_forward 호출 없음. engine 단독 실행(walk_forward/pbo/capacity 는 production 미소비) |
| `backtest/pbo.py` | `calculate_pbo_cscv`·`calculate_deflated_sharpe_ratio`·`build_go_nogo_card` | 다중검정 과적합(H23) 정량 | Bailey & López de Prado CSCV + DSR>0.95. trial-count deflate | **opt-in off/dead** |
| `backtest/capacity.py` | `check` (:40) | 주문≤일거래대금 1% 자기충격 차단 | Sharpe 부풀림 방지 | **opt-in off/dead** |

**디버깅 노트**:
- ★10년 백테스트 결과 이상 → 먼저 **어느 경로인가**: run_replay 는 기본 `_run_legacy`(게이트·judge 없음). risk_pipeline on 검증은 `BacktestEngine(use_risk_pipeline=True)` 명시 주입(연결성맵 §5-4, tests/test_engine_wire.py 의 per-bar checksum/golden master 기준).
- NAV 절대수익 낮음 → 5단계 노트(`MAX_WEIGHT_SINGLE` 컨텍스트 미스매치) 1순위(**L0/L2**).
- 백테스트 환상(과적합) → **L1** PBO/DSR(build_go_nogo_card GO/MARGINAL/NO_GO). 생존편향=walk_forward UniverseManager 상폐 포함 여부. 단, walk_forward 는 run_replay 에서 **미호출** — 별도 스크립트로 명시 주입 필요.
- 결과 재현 안 됨(replay 불변) → **L2/L3** LLM hook 주입으로 비결정성(judge_hook=None 또는 결정론 hook 강제, LLM env 전부 off).

---

## 두뇌/PIT 인프라 (관통 — 위 단계가 공유)

| 파일경로 | 핵심 함수 | 기능 | 설계 의도 | 배선 상태 |
|---|---|---|---|---|
| `core/brain/llm_provider.py` | `OllamaQwenProvider`·`ClaudeProvider`·`LLMRouter.route` | LLM 라우팅(평상시 Qwen quick, 트리거 Claude deep) | ClaudeProvider=Max OAuth만(api키 금지). C2 서킷브레이커(일일캡·degrade), B3 결정성(model_id·prompt_hash·temperature). 매수 degrade=abstain | **opt-in off** |
| `core/brain/embedder.py`·`memory_layer.py`·`rag_pit.py` | DaService BGE-m3 1024d / FinMem 계층메모리 / PIT causal-mask | 임베딩·메모리·RAG | 신규 ollama BGE 금지(공간 보존). RAG recall PIT(created_at<as_of+열린 포지션 제외) | **opt-in off** |
| `core/data/adversarial_replay.py` | (taint isolation) | 적대적 PIT replay 1급 CI 게이트 | reducer 결정론보다 강한 시간적 결정론. 미래 REVISION 이 as-of-A 산출에 0건 + 물리부재 byte-identical | **테스트 게이트** |
| `core/data/promotion_gate_live.py` | `reset_emergency(by_human=True)` | shadow→live 사람게이트 + ramp | 사람 승인 필수·자동 금지. shadow/live 같은 로직 sink만 분기. geometric ladder rung FIX(size-as-peeking 차단) | **사람 게이트** |
| `core/observability/` | `kill_switch`·`rule_observer`·`rule_attributor` | rule↔실행기 물리 방화벽 / 5지표 read-only / 반사실 PnL | rule 은 한도 producer지 override 아님. emergency 해제 사람만. divergence shadow↔live=안전 1차 방어선 | **opt-in off** |
| `core/book/` | `d4_book.to_context`·`d4_wire` | 거시·산업 append-only PIT Book | 그 시점 지식만 L2 judge 주입. PIT substrate→knowable_from 전파 | **opt-in off** |

**디버깅 노트**:
- LLM 호출이 안 됨/너무 잦음 → **L3**(LLMRouter.route 트리거 조건, budget_ledger C2 degrade). OAuth 429=oauth-beta 헤더+system 누락.
- PIT 누수 의심(silent alpha) → **L2** adversarial_replay 로 taint isolation 검증. lineage replay 로 도출 체인 재구성.
- 실거래 승급 막힘 → **사람 게이트**(promotion_gate_live, 자율 밖).

---

## 부록 A. 증상→파일 빠른 색인 (디버깅 진입표)

| 증상 | 1순위 의심 | 레벨 | 파일 |
|---|---|---|---|
| 레거시 코인 주문 안 나감 | 안전장치 선검사 | L0/L2 | execute_trade.py, auto_emergency.json, DRY_RUN env |
| 레거시 레짐 이상 | 레거시 레짐(core 아님) | L2 | scripts/regime_detector.py, agents/base_agent.detect_regime |
| 레거시 NAV/사이징 이상 | 점수제+Kelly | L2 | agents/base_agent.py (calculate_buy_score, kelly_position_size) |
| 단일자산 백테스트 NAV 압살 | MAX_WEIGHT_SINGLE 컨텍스트 미스매치 | L0/L2 | risk_gate.py:47 (RISK_MAX_WEIGHT_SINGLE=0.95 우회) |
| coin 신호 방향 역(rank-IC 음) | mean-rev vs momentum, trend-gate 미배선 | L1 | agents/base_agent.calculate_buy_score (.p2-trend-gate.py=실험, production 미배선) |
| core 트랙이 안 탐 | env opt-in off | L0 | INV_R15_WEIGHTS/MACRO_ENRICH 등, 연결성맵 §2 |
| risk_gate 차단 안 됨 | INV_CORE_GATE off / 부분검사 | L0 | run_agents.py:831, risk_gate.py:308 |
| 배분 weights 안 움직임 | stance 약함(버그 아님) | L1 | portfolio_orchestrator.allocate, regime_to_weights |
| 주식 주문 stub uuid | KIS credential 부재 | L0/L2 | kis_client._stub_order, _ensure_pykis |
| 주식 경로 전체 미작동 | production caller 0 | L0 | order_assembly/selection_pipeline/stock_track (entry 미작성) |
| judge 가 사이징 키움 | down-only 불변식 위반 | L1 | judge.py (final≤L1), bonus_channel.size_with_bonus |
| 백테스트 비결정성/재현 실패 | LLM hook 주입 | L3 | engine.judge_hook, MACRO_ENRICH/ACTIVE_LOOP/CONSENSUS off |
| 백테스트 과적합 | PBO/DSR | L1 | backtest/pbo.py (build_go_nogo_card) |
| 백테스트 walk_forward 안 탐 | run_replay 에 호출 없음 | L0 | backtest/walk_forward.py (별도 명시 주입 필요) |
| PIT 누수(과거 값 이상) | vintage realtime vs final, pit_query 우회 | L2 | core/data/vintage, pit_query, adversarial_replay |
| LLM OAuth 429 | oauth-beta 헤더+system 누락 | L3 | llm_provider.ClaudeProvider, loop_factory:102-106 |
| reserve_snapshot 매매 미반영 | 수집 전용 dormant (Phase0a 미통과) | L0 | core/data/reserve_snapshot.py (매매 경로 배선 미완) |

## 부록 B. env flag → 켜지는 경로 (연결성맵 §3 기준)

| env flag | default | 켜는 경로 | 백테스트 권장 |
|---|---|---|---|
| `INV_CORE_GATE` | off | 레거시 buy/sell 직전 risk_gate.check 1회 백스톱 | — |
| `INV_UNATTENDED_FSM` | off | DeriskExecutor(FakeExchange stub) | off |
| `INV_R15_WEIGHTS` | off | core 트랙 sleeve_returns+RegimeClassifier+belief | on/off byte-identical 검증 |
| `INV_STUDY_LENS` | off | study lens 주입 | — |
| `MACRO_ENRICH` | off | _run_macro_enrich(LLM stance, ★baseline 자체 수정) | **off**(비용·비결정성) |
| `ACTIVE_LOOP_SHADOW` | off | _run_fhc_shadow(LLM 발권, 자본0) | **off** |
| `FHC_BONUS` | off | confirmed+mediator HOLDS 카드 bonus tilt | — |
| `MACRO_CONSENSUS` | off | ConsensusNode down-only de-risk | **off** |
| `ETF_FALLBACK` | off | construction RepresentativeETF/EwBasket dispatch (백테스트 미검증) | — |
| `RISK_MAX_WEIGHT_SINGLE` | (미설정=0.10) | 단일자산 캡 우회(백테스트용 0.95) | 단일자산 백테스트 시 0.95 |
| `DRY_RUN` | true | false=실거래(★사람 게이트) | true |
