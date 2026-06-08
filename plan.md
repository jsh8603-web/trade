# 통합 투자 시스템 — 구현 plan

> ⚠️ **PRODUCTION MANDATE (2026-05-29 사용자 확정 · 전 Phase 강제)**: mock-only 개념 폐기. **프로덕션 품질로 한 번에 빌드(두 번 일 금지)** — 실 라이브러리·실 DB·실 서비스 경로. ① **DB=로컬 PostgreSQL(psycopg2)**, Supabase 클라우드 폐기(로컬 GPU 환경 필수라 클라우드 무용). ② **.env=신규 생성**(⛔ 기존 coin repo .env 사용 금지), 현재 실 자격증명=사용자 Claude OAuth 뿐. ③ **실 라이브러리 설치**(cvxpy·PyPortfolioOpt·riskfolio-lib 완료; sklearn/scipy 대체 금지). ④ **GO-LIVE 3단계 순서**(IMPLEMENTATION_PROMPT L307·L313 명문화): **(1)** 과거 데이터 백테스트 모의(Phase 5 엔진) → **(2)** 전체 파이프라인 실가동 + DRY_RUN 모의투자(실데이터·실서비스·실DB, 자금 미투입, KIS 모의+코인 DRY_RUN 합산 90일+ 무중단·실 급락/급등 1회 무사고) → **(3)** 극소액 실거래 시작(DRY_RUN=false, **사용자 명시 go-live 시에만**). DRY_RUN·EMERGENCY_STOP·kill switch 안전장치는 (1)(2) 내내 유지, (3)에서만 단계 해제. 코드는 전 단계 실가동 wiring(빌드 시점부터 (2) 수준). ⑤ 기존 mock/.env-후속 표현은 무효(인계: [handoff-inv-production-pivot-20260529.md](./handoff-inv-production-pivot-20260529.md)).

> 설계 SSOT: [`IMPLEMENTATION_PROMPT.md`](./IMPLEMENTATION_PROMPT.md) (Round 10) + [`implementation-keys.md`](./implementation-keys.md) (7-에이전트 종합, **충돌 시 우선**).
> 검토 근거: [`review-findings.md`](./review-findings.md). coin clone=`coin/`, 레퍼런스=`_refs/`, 작성된 brain 코드=`stock/`·`core/brain/`.
> 작업 규칙(전 step 강제): **① Sonnet-executable**(파일경로·심볼/라인·before/after·경계·완료판정) **② reuse-github-as-is**(레퍼런스 코드 그대로 차용, 출처=implementation-keys.md §1-§7) **③ stub 주의**(MlFinLab labeling·AT attribution·AT registry = 계약만, 본체 자체구현).

---

## 실행 엔진 확정 (DA phase4-engine-routing)

| Phase | 엔진 | 근거 |
|---|---|---|
| **-1 코인 안전 하드닝** | `wf: harness2` | 라이브 실금전 경로·DB/상태 변경·회귀 민감·멱등성/정합성 핵심로직 → 검증 필수 |
| **0 코어 추상화** | `wf: harness2` | 코인 동작 100% 보존(회귀 0) 검증 필수 |
| **1 두뇌 마이그레이션+brain wire** | `wf: harness2` | 신규 연동(Qwen/BGE)·작성 brain 코드 통합·회귀 위험 |
| **2 리스크 게이트** | `wf: harness2` | 우회불가 안전 핵심·precedence 격자·결함주입 검증 |
| **2.5 라이브 LLM 경로 C2/B3 복원** | `wf: harness2` | Phase1 LLMRouter 교체가 우회한 C2(캡·예산·degrade)+B3(결정성) 라이브 경로 복원·회귀 민감 |
| **3 주식 트랙(가치 2단)** | `wf: harness2` | 신규 핵심로직·PIT 데이터 연동·value-trap 검증 |
| **4 데이터+KIS 실행** | `wf: harness2` | 신규 외부연동·멱등성·레이트리밋·결함주입 |
| **5 통합 백테스트 엔진** | `wf: harness2` | coin 백테스트 교체·패리티·PBO 검증 |
| **6 Orchestrator+consensus** | `wf: harness2` | 최상위 통합·90일 무중단·분산효과 검증 |
| **R 코인 이식** | `wf: harness2` | 검증된 일반 파이프라인 → coin 특성변형+패리티 |

> 전 Phase `wf: harness2` (사용자 확정 — 전부 harness2 wf). progress.md 각 Phase = 1 step `wf: harness2`. Phase 내부 sub-objective·verifier 게이트는 `harness2.md` 가 관리(§2.9 = verifier 검증 핵심).
> **착수 순서**: Phase -1 → 0 → [1~6 일반 빌드] → R. 각 Phase 독립, §2.9 동작 게이트 통과 후 다음.

---

## Pipeline Goal

검증된 단일 BTC 봇(`coin/`)을 asset-agnostic 코어로 일반화 + 주식 트랙(KR/US 가치투자) + 거시 자산배분 brain 을 추가한 통합 투자 시스템을, **라이브 코인 구멍부터 막고(Phase -1) → 깨끗한 일반 버전 빌드(1-6) → coin 이식·패리티(R)** 순으로 구현한다. 모든 게이트는 *코드 완성*이 아니라 *돌려서 의도대로 행동*(does-it-run/behave) 기준.

---

## 🔒 GOLDEN RULE & Phase 누락 감사 게이트 (2026-05-29 사용자 확정)

- **IMPLEMENTATION_PROMPT.md = GOLDEN RULE**: 설계 SSOT 로 거의 불가침(10라운드+ 자문 수렴 결과물). 구현 중 "이건 아니다" 판단되는 항목만 **외부 자문(gemini-web + claude-web 병렬) 수렴**으로 변경하고, 소규모 변형(임계값·구현 방식·필드 표현)은 자문 없이 허용. 대규모/계약 변경은 자문 필수. 무단·무비판 일탈 금지. (implementation-keys.md 충돌 시 implementation-keys 우선 = 기존 규칙 유지.)
- **각 Phase 마지막 = GOLDEN RULE 누락 감사 게이트** (harness2.md 최종 Sub-obj 의무): 모든 Phase 의 마지막 Sub-obj 는 해당 Phase 산출물을 IMPLEMENTATION_PROMPT.md(+implementation-keys.md) 대응 섹션과 대조해 *빠진 항목*을 체계 점검한다. 산출 = 커버 / 누락 / 의도적 일탈(자문 ref) 체크리스트. **근거 사례**: Phase 1 SO-6 이 gemini_client 의 C2/B3 를 LLMRouter 교체로 라이브 경로 밖 우회 → 사후 감사로 발견 → Phase 2.5 신설. 진짜 누락 발견 시: 소규모면 그 Phase 안에서 흡수, 크면 후속 Phase/스텝 신설. Verifier 독립 검증 대상.
- **게이트 검토 이연 항목 = progress.md 박제 의무** (2026-05-29 사용자 확정): Verifier 검증·GOLDEN RULE 누락 감사·Sufficiency Check 등 게이트 검토에서 "보완 필요하나 당 Phase 에서 미룸(이연)" 으로 판정된 항목은 반드시 progress.md `## 이연 항목` 에 박제한다(항목·사유·목표 Phase·출처). `.harness2/` 내부 문서(audit-*.md)에만 남기지 말 것 — 압축·Phase 전환 시 유실 방지. 목표 Phase 도달 시 소진(체크).

---

## Phase -1 — 라이브 코인 안전 하드닝 (최우선·착수) `wf: harness2`

> **Final Objective**: 현 코인 라이브(DRY_RUN) 경로에 E2 멱등성·R2 reconciliation·B1 스키마 하드게이트·B3 결정성·C2 서킷브레이커를 적용해 §2.9 Phase -1 결함주입을 통과. 배선 SSOT = `IMPLEMENTATION_PROMPT.md §0.6-B` + `implementation-keys.md §1`.

### Step -1.1 · E2 멱등성 (`execute_trade.py`) — `wf: harness2`
- **대상 파일**: `coin/scripts/execute_trade.py`
- **현 구현**: 주문 body(`~:451-457`)에 market/side/ord_type 만, `identifier` 없음. nonce(`:153`)=JWT 인증용. `check_open_orders_and_cancel`(`:123`)=`state=wait`(대기)만 조회.
- **변경**: ① 주문 body 에 Upbit `identifier`(client_order_id) 부여 ② POST(`~:462`) 전 동일 identifier 로 미체결+**체결완료(daily_order)** 양쪽 조회(멱등) ③ POST 타임아웃 catch → 재시도 전 `_reconcile_recent_order(identifier)`(=`check_open_orders_and_cancel` 일반화)로 중복 차단.
- **reuse-github**: 응답유실 재시도 패턴=polymarket `_refs/polymarket-bot trader.py:314-337`. KIS 측은 pykis `from_number(account,branch,number)`(`order.py:392-417`) 서버주문번호 즉시저장(Phase 4 에서).
- **경계**: nonce(`:153`) 로직 건들지 말 것(JWT 인증 별개). DRY_RUN 게이팅·EMERGENCY_STOP 선검사(`:250`) 보존.
- **완료 판정**: §2.9 — 주문 직후 응답유실 인위 주입 → 재시도해도 주문 1건만. `near_miss_veto`/`execution_logs` 기록.

### Step -1.2 · R2 reconciliation 루프 — `wf: harness2`
- **대상 파일**: `coin/rl_hybrid/rl/live_trader.py`(`run_cycle`), `coin/scripts/get_portfolio.py` 직후 삽입
- **변경**: 사이클마다 거래소 실잔고 ↔ DB 포지션 대조 → drift 시 **halt + `execution_logs` 기록(자동보정 금지)**. drift 계산 day-1 fee-net. **거래소 open-orders 조회 → 미체결 locked 잔량을 DB 합산에 포함**(미체결 묶인 잔고를 drift 에서 제외=가짜 halt 방지, R9). 매도 시 `_clamp_to_balance(side,amount)`=`min(req, free잔량)`.
- **reuse-github**: ghost check(거래소엔 없는데 DB有 write-off)=polymarket `trader.py:260-274`. 우리 locked(반대방향)+ghost **양방향 둘 다**. clamp=polymarket `trader.py:283-289`.
- **경계**: 임계 drift=halt(자동 write-off 금지). 양다리(kimchirang)=leg-level 별도(H2, 강등상태라 후순위).
- **완료 판정**: §2.9 Phase4⑤ — 잔고 인위 drift 주입 → 다음 사이클 감지·기록. 미체결 보유 중 주입 → locked 오판 halt 안 함.

### Step -1.3 · B1 스키마 하드게이트 — `wf: harness2`
- **대상 파일**: `coin/rl_hybrid/nodes/llm_worker.py` 출력 → risk 경계
- **현 구현**: `prompts/schemas/decision_result.json` 존재하나 jsonschema 검증 0건(llm_worker 가 로드 안 함).
- **변경**: llm_worker 출력→risk 진입 사이에 jsonschema **하드게이트**(실패→관망+`near_miss_veto`). 1차 생성강제(Outlines/GBNF/Ollama format=json, Phase1 Qwen 시), 2차 post-hoc 검증.
- **reuse-github**: TradingAgents structured-output `bind_structured` 패턴(`_refs` 확인).
- **경계**: 스키마 자체(`decision_result.json`) 변경은 §7 확장(valuation_gap·macro_view 등)과 별도 — 본 step 은 검증 강제만.
- **완료 판정**: 깨진 JSON 주입 → 관망+기록, 통과 JSON → 정상.

### Step -1.4 · B3 결정성 — `wf: harness2`
- **대상 파일**: `coin/rl_hybrid/rag/gemini_client.py:78`, 결정 레코드(`base_agent.py:723`·`run_agents.py:665`·`execute_trade.py::_record_trade_to_db:685`)
- **변경**: `temperature=0.3`→**0**(config 화). 결정 레코드에 `model_id`·`prompt_hash`·`temperature` ALTER+기록. 마이그레이션 **047_**(051 아님).
- **경계**: PPO 추론 결정성은 별개(argmax/고정seed) — Phase 0 패리티 전제.
- **완료 판정**: 동일 입력 N회 동일 결정. 모델 교체 시 레코드에 버전 차이.

### Step -1.5 · C2 서킷브레이커 — `wf: harness2`
- **대상 파일**: `coin/rl_hybrid/rag/gemini_client.py`(현 `_rate_limit` 만), 신규 호출 카운터
- **변경**: 일일 LLM 호출 캡 + 초과 시 **degrade-to-Qwen** 폴백. 결정당 최대 지연예산 초과 시 휴리스틱 fallback. 텔레그램 일일요약에 호출 카운트.
- **경계**: 매수 결정은 degrade 시 **abstain**(H14, 가치전략 무력화 트레이드오프=review-findings §4 모순1 — Phase3 에서 우선순위 큐 재검토).
- **완료 판정**: §2.9 — 트리거 폭주 주입 → 캡 발동+Qwen 폴백, 지연 초과 시 휴리스틱.

> **Phase -1 §2.9 게이트(harness2 verifier 검증 핵심)**: E2·R2·B1 결함주입 전부 통과 + 5건 `near_miss_veto`/`execution_logs` 기록.

---

## Phase 0 — 코어 추상화 (코인 100% 보존) `wf: harness2`
- **Final Obj**: `core/asset_track.py` ABC(`collect_market_state()`/`generate_candidate(state)→Decision`/`recommended_next_check()→datetime`). 전략 택소노미 M1 = **Directional/MarketNeutral/HFT 3계열**(kimchirang=MarketNeutral 강등·scalp_ml=HFT). 기존 코인 로직 **래핑만**.
- **결정 필요(review-findings §4 갭4)**: 실무 권고 = AssetTrack=Directional 만(코인 BTC+주식 가치), scalp_ml/kimchirang 은 별도 Strategy 로 risk_gate/포트폴리오 레벨 통합.
- **§2.9 게이트**: 7일 실데이터 래핑 전·후 `decision`·breakdown 의미적 동치(RAG 격리·시계 freeze·PPO 결정성·LLM record-replay fixture 전제). byte-동일 금지.
- 상세 wire: `implementation-keys.md` (해당 phase 도달 시 detail).

## Phase 1 — 두뇌 마이그레이션 + brain 코드 wire `wf: harness2`
- **Final Obj**: `core/brain/llm_provider.py`(OllamaQwen quick·Claude deep·Gemini 호환)·`embedder.py`(BGEm3·Gemini), mig 051+재임베딩(M4 가드). ZMQ `llm_worker` 교체. **작성된 `core/brain/` 코드(B1) 통합** + 계층메모리(FinMem decay 3축)·RAG recall(PIT causal-mask)·reflection→RAG(trade_reviews 배선).
- **작성코드 wire**: `core/brain/regime_classifier.classify()`→`macro_reasoning.enrich()`→`regime_to_weights()`. `indicator_event_correlation`(§5.8-H) ingest/recall. (implementation-keys.md §7)
- **정정 반영**(implementation-keys §8): PIT causal-mask(as_of)·FinMem decay·Judge 2단·ALFRED vintage.
- **§2.9 게이트**: 72h DRY_RUN — Claude=0 평상시, 호출=트리거 일치, BGE recall 저하<10%p, PPO 정상, Qwen vs Gemini 방향 일치율.

## Phase 2 — 공통 리스크 게이트 (우회불가) `wf: harness2`
- **Final Obj**: `core/risk_gate.py` — per-position stop(-5/-10)·일일한도·상관캡·max weight·turnover·min_holding·kill switch(halt+컨펌, H27). **§6 precedence 격자** + 멀티에셋 사이징=Riskfolio Ledoit-Wolf(**PyPortfolioOpt SSOT 단일화**, HRP tail-codependence fallback H25). LLM/실행 프로세스 격리.
- **reuse-github**(implementation-keys §2): ai-hedge-fund `risk_manager.py:301` 상관 multiplier, nautilus `risk/engine.pyx:359` max_notional 백스톱, Riskfolio HRP `HCPortfolio.py:716`.
- **§2.9 게이트**: 5종 결함주입(손실한도/상관/max weight/MDD/LLM 우회) 전부 + precedence 격자 충돌 주입 → `near_miss_veto` 기록.

## Phase 2.5 — 라이브 LLM 경로 C2/B3 복원 `wf: harness2`
> 배경(2026-05-29 IMPLEMENTATION_PROMPT 감사 발견): Phase 1 SO-6 이 llm_worker→LLMRouter 경유로 교체(llm_worker.py:225)하며 gemini_client 의 **C2 서킷브레이커**(H14)·**B3 결정성 메타**(H10)가 라이브 결정 경로 밖으로 우회됨. LLMRouter 가 Phase 6 에서 정식 결정엔진으로 wire 되기 전 복원(코드 grep 검증: llm_provider.py 에 cap/budget/degrade 0건, model_id/prompt_hash 0건).
- **Final Obj**: gemini_client(`rl_hybrid/rag/gemini_client.py:40-172`)의 C2(일일 호출 캡·지연 예산·degrade-to-휴리스틱)+B3(model_id·prompt_hash·temperature)를 LLMRouter/Provider(`core/brain/llm_provider.py`) 레벨로 이식. llm_worker(`rl_hybrid/nodes/llm_worker.py:286 _parse_llm_response`) 결정 레코드에 B3 전파.
- **C2 정책**: 일일 캡/지연 예산 초과 → degrade(fallback 또는 휴리스틱 abstain, H14 "매수 degrade=abstain" 보수). 품질붕괴(degrade) vs 자원소진(429·예산) 구분 — Phase 3 모순1 최소훅·Phase 6 풀 메커니즘과 정합.
- **§2.9 게이트**: 일일 캡 초과→degrade 발동 / 지연 예산 초과→degrade / 같은 입력→같은 prompt_hash 재현(B3 결정성) / Phase -1(91)·0(43)·1·2(105) 회귀 0.

## Phase 3 — 주식 트랙 + 가치 2단 트리거 `wf: harness2`
- **Final Obj**: 작성된 `stock/` 코드(B2) 통합 — `valuation.py`·`value_trigger.py`(2단)·`factor_attribution.py`. announcement-date PIT. §5.10 admission 게이트(S4 앞단).
- **작성코드 wire**: `StockTrack.generate_candidate()`→`value_stock()`→`run_value_trigger()`→`to_track_decision()`→risk_gate. `ValueTrapMetaLabeler` 주입.
- **모순1 최소훅**(풀 메커니즘=Phase6): `run_value_trigger` heavy_agent 주입실패를 `degrade`(품질붕괴=abstain 정답) vs `resource`(429·예산=후속 재시도/예약 대상) 사유로 구분해 ValueTriggerResult.reasoning 에 명시. silent abstain 금지.
- **정정 반영**(§8): 관리종목=**FDR** `KrxAdministrative`(일별 스냅샷 PIT), Lean=`Fundamental`/`FineFundamental` 날짜별 CSV.
- **§2.9 게이트**: 실역사 N≥10(상폐 포함) value-trap 혼동행렬 + 유니버스 게이트(레버리지/인버스·선물·옵션 거절). **주의(review-findings §4 모순2)**: heavy-agent lookahead 오염 → training cutoff 이후 사건 또는 마스킹.

## Phase 4 — 데이터 레이어 + KIS 실행 `wf: harness2`
- **Final Obj**: `stock/data/`(pykrx·FDR·OpenBB·FRED+ECOS·**DART/EDGAR PIT 파서**)·`stock/kis_client.py`=pykis 어댑트(modify/cancel/pending·websocket·모의우선). **ALFRED vintage**(FRED realtime_*).
- **reuse-github**(§1,§5): pykis 그대로(`order_modify.py`·`client/websocket.py:358`), DART=`_refs/OpenDartReader`+`dart-fss` rcept_no XBRL 파싱, EDGAR accession 단위 PIT.
- **정정 반영**: KIS 토큰24h·초당 레이트리밋(분당80%→초당 기준)·client_order_id 앱단·토큰 1분당1회 공유캐시.
- **H30 데이터소스 rate-tier**(IMPLEMENTATION_PROMPT L533·S1 L39·L131 M5): DART(일 호출상한)·FRED(~120req/min)·OpenBB·ECOS tier·IP 정책 상이 → 소스별 jitter·백오프·rotation·tier 한도(KIS limiter 와 별개, §5.8-C 라이선스 연계). ⚠️2026-05-29 감사: plan 누락분 복원.
- **§2.9 게이트**: 왕복·부분체결·**초당** 레이트리밋·6h 토큰갱신+websocket 재연결·drift 감지·locked 오판 방지 + 데이터소스 tier 한도 초과→백오프/rotation 발동.

## Phase 5 — 통합 백테스트 엔진 (2018+) `wf: harness2`
- **Final Obj**: `backtest/` 단일 엔진(coin 13개 분산 backtest_*.py + 슬리피지0 **교체**). 슬리피지(거래대금/호가 비례)·수수료·세금. **단일 `common/metrics.py`**(백테스트=라이브 지표함수 공유).
- **reuse-github**(§3): skfolio `CombinatorialPurgedCV` + **자체 CSCV logit-rank PBO 집계기**(yakub268 근사 폐기), DSR=yakub268 `validation_framework.py:218`, GO/NO-GO 카드=`walk_forward.py:134`.
- **H28 전략 capacity 상한**(L531): 전략당 capacity(자기충격) — KR 소형주·얇은 알트 자기주문 가격충격. 트랙 한도에 capacity 상한 반영(슬리피지 모델≠capacity, 비현실적 규모 Sharpe 부풀림→GO/NO-GO 거짓 차단). ⚠️2026-05-29 감사 복원.
- **H1 라이브 캘리브레이션(E4)**(L505·S11 L59): R2 reconciliation 데이터로 예상 vs 실제 체결가 주간 측정→슬리피지 파라미터 자동 보정(백테스트=라이브 패리티 시간 유지). ⚠️2026-05-29 감사 복원.
- **§2.9 게이트**: 기계적 패리티≥95%(LLM abstain stub, H22)·walk-forward OOS/IS+DSR/PBO·전구간 MDD<kill switch + capacity 상한 초과 주문 거절·E4 보정 루프 동작.

## Phase 6 — Portfolio Orchestrator + Consensus `wf: harness2`
- **Final Obj**: `core/portfolio_orchestrator.py` — per-bloc 레짐+상관→슬리브% via **BL(`regime_to_weights` 작성됨, pi 주입)**. Drift Monitor(매 사이클 최우선). §4.2 고-스테이크스 consensus(TradingAgents **2단 Judge** rounds=1). 통합 대시보드(G8, coin `dashboard.py` 멀티에셋 확장).
- **모순1 풀 메커니즘**(LLM deep 예산, 2026-05-29 자문 판정): crash reserve 레짐조건부 예약 트랜치 + 3버킷(429·예산소진=재시도/예약 / degrade=abstain / 정상=큐) + 예산 ledger(C-lite — 정책은 트랙 도메인·회계만 LLMRouter reserve/consume/remaining) + 점수 `sat(gap)×pos×regime_mult`(급락폭은 quick proxy로만, 지배 금지). 검증가능 영역(예산역학·quick점수)만 시뮬, deep 판단품질은 forward only.
- **reuse-github**(§3,§4): yakub268 대시보드·Thompson, TradingAgents `portfolio_manager.py`.
- **H27 bounded auto-fallback**(L530, Phase2×H18 야간): US장=KST 야간 손실 누적 시 halt-then-confirm 무인 footgun → 컨펌 N시간 미수신 + 2차 임계 초과 시 자동 *시간분산 축소*(전량청산 아님). Phase 2 KillSwitch(confirm_pending)에 타임아웃 정책 연계. ⚠️2026-05-29 감사 복원.
- **§2.9 게이트**: 레짐전환 슬리브 이동·통합 MDD<트랙 합·90일 무중단·macro 노드 종료시 abstain+청산정상(H29)·consensus 적시 발동/미발동 + H27 야간 컨펌 미수신→bounded auto-fallback 발동.

## Phase R — Coin 이식 (retrofit) `wf: harness2`
- **Final Obj**: 검증된 일반 파이프라인 → coin 특성 변형표(24/7·Upbit fee·shadow-live H19·멀티코인 사이징·crypto decay·코인 consensus 렌즈) 이식 + **DRY_RUN 패리티(회귀0 or 개선)**.
- **§2.9 게이트**: 이식 전후 coin decision 동치 or 개선·안전게이트/reconciliation 정상·교체 백테스트 엔진이 더 현실적.

---

## 🚦 실전 자금 전환 게이트 (전 Phase 누적)
Phase 0~6+R+consensus 전부 통과 → KIS 모의+코인 DRY_RUN 합산 90일+ 무중단(급락/급등 1회 무사고) → 라이브 신호가 백테스트 분포 안 → kill switch·EMERGENCY_STOP·reconciliation 실발동 기록 → 극소액부터.

---

## 미해결 결정 (착수 중 판정 — review-findings §4)
1. **모순1** ✅판정(2026-05-29 gemini+claude 자문 수렴): 풀 메커니즘=**Phase6**(crash reserve 레짐조건부 예약 트랜치 + 3버킷[정상 / 429·예산소진=재시도·예약 / degrade=abstain] + 예산 ledger C-lite[정책 분산·회계만 LLMRouter 중앙] + 점수 `sat(gap)×pos×regime_mult` 곱셈). **Phase3**=최소훅(heavy_agent 주입실패를 degrade·resource 사유구분 + silent abstain 금지→hold+알림). ⛔기각: gemini 급락폭 지수증폭 `e^|Drop|`(가치갭과 이중계상+trap을 최상단에)·soft limit 초과호출(429 위험). 근거: 백테스트 deep=stub이라 점수정책 판단품질 검증불가→Phase3에 넣어도 두번일.
2. **모순2** H22 lookahead 가 Phase3 수용판정에도 적용 → training cutoff 이후 사건/마스킹/기계적-only 게이트.
3. **갭4** M1 택소노미 = Directional only(권고) vs 3계열 → Phase0 전 확정.
4. **디렉토리**: 현재 `coin/`(clone)·`core/`·`stock/`(작성) 분리. "Inv 구현→coin 덮기" 최종 구조 = coin 코드 Inv 루트 승격 시점 결정 필요.
