# 통합 투자 시스템 구현 프롬프트 (for Claude Code, 로컬)

> 이 문서를 `jsh8603-web/coin` 리포 루트에서 Claude Code에 전달하여 단계적으로 구현한다.
> 기존 코인 시스템을 **재작성하지 말고**, asset-agnostic 코어로 **일반화**한 뒤 주식 트랙을 추가하는 것이 목표다.

---

# ■ 교차모델 평가 의뢰 (Gemini Web & Claude Local 공통)

**평가 대상**: `https://github.com/jsh8603-web/coin` (현 코인 자동매매 시스템, v1.29.0)
**의뢰 내용**: 아래 "평가 핵심 기준"으로 이 프로젝트를 평가하고, 본 로드맵(아래 전체 문서)이 갭을 적절히 메우는지 교차 검증하라. 두 모델은 **동일 출력 포맷**으로 답하여 결과를 비교(수렴 분석)할 수 있게 한다.

**각 축마다 다음 포맷으로 답하라:**
```
[축 ID] 상태: 미구현 / 부분구현 / 구현됨   |   근거: (파일·함수 등 구체적)
리스크: (실제 운영에서 무엇이 깨지나)
개선안: (무엇을, 어떻게)
교차참조: (아래 GitHub 목록 중 차용할 repo)
```
마지막에 **우선순위 Top 5**(치명도×구현난이도)와 **본 로드맵이 놓친 축이 있으면 추가**하라.

## 평가 핵심 기준 (8 레이어 × 25 축)

**Data** — D1 무결성/no-lookahead(백테스트가 point-in-time 데이터인가, 미래정보 누수 없나) · D2 staleness/소스 quorum(데이터 신선도 검증 + 소스 장애 시 매매 거부 규칙)
**Brain** — B1 구조화출력 검증(LLM 출력이 스키마로 강제 검증/환각 가드) · B2 차원 일관성(임베딩 교체가 RL/하위모듈을 깨지 않나) · B3 버전·결정성(temperature/seed/model_id 고정 + 프롬프트 버전 기록으로 재현 가능한가) · B4 감사/설명가능성(결정 근거 추적 — score breakdown)
**Risk** — R1 사전게이트/kill switch(위험주문 차단 + 우회 불가가 코드로 강제) · R2 reconciliation(거래소 실잔고 대조 루프) · R3 포지션사이징(Kelly fraction 검증·캘리브레이션)
**Exec** — E1 레이트리밋(중앙 limiter + 백오프, 특히 KIS) · E2 멱등성/exactly-once(client_order_id dedup으로 이중주문 방지) · E3 부분체결(미체결 잔량 처리 규칙)
**Learning** — L1 과적합/walk-forward(OOS + no-lookahead) · L2 온라인학습 안정성(성과 하락 시 롤백) · L3 레짐 라벨 정확도/hysteresis(flapping 방지) · L4 reward hacking(보상 clip/제약)
**Ops** — O1 관측가능성(통합 성과 대시보드) · O2 self-healing/uptime(무중단 + 자동복구) · O3 DR/상태영속성(DB 장애 시 fallback)
**Security** — S1 키 스코핑(최소권한 + 출금권한 미부여 강제) · S2 감사추적(모든 결정/거절/실패 기록)
**Portfolio** — P1 배분/상관/분산(멀티에셋 비중 + 상관 캡) · P2 세금/수수료(회전율·세금 최적화)
**Cross-cutting** — C1 동시성/분산락 정합성(file lock + ZMQ 멀티프로세스 + 멀티머신 환경에서 공유 상태 경합 방지) · C2 LLM 서킷브레이커+지연예산(트리거 연발 시 Claude 호출 폭주/지연 blowup 방지 — 일일 호출 캡 + 최대 결정지연 초과 시 휴리스틱 fallback)
> D2에는 **소스 신뢰도 1차 스코어링**(뉴스 오분류로 인한 거짓 트리거 방지)을 포함해 평가할 것.

> 참고(채점 가이드 — Round 1·2 교차검증으로 **확정/정정된** 기준선):
> - **강점(코드 확인)**: L2(Sharpe-drop 자동롤백), B4·S2(감사 테이블), R1(EMERGENCY_STOP env 우회불가, orchestrator.py:179), O2(file lock+self-healing), L4(reward clip+tail_risk).
> - **확정 미구현(치명)**: E2(멱등성 — uuid는 Upbit JWT nonce, 주문 body에 `identifier` 미전송), R2(reconciliation 0건), B1(스키마 존재하나 jsonschema 강제 0건). **이 3종은 모두 현재 라이브 코인 경로의 구멍 → Phase -1로 선반영.**
> - **확정 약함**: B3(temperature=0.3·seed/model_id/prompt_hash 없음 — 거의 0비용 quick win), D2·L3·E1·E3·L1(부분).
> - **정정됨**: B2는 라이브 42d 임베딩-프리라 PPO 파괴 위험 **낮음**(임베딩 테이블은 1536→3072 이력, BGE 1024는 3번째 변경 → 재임베딩 가드 필요). S1은 owner/worker 역할분리 키모델(잔여 갭=출금스코프 코드강제). H1 슬리피지는 reward 경로 flat 3bps, **백테스트 엔진엔 0**.
> - **Round 2 신규(구조)**: M1 전략 택소노미(kimchirang/scalp_ml/altrang은 AssetTrack 단일 ABC에 안 맞음→계열 분기), M2 양다리 leg-reconciliation, M3 시퀀싱(안전 하드닝을 Phase -1로 선행), M4 임베딩 마이그레이션 역호환, +H15 스마트 주문집행.
> - **Round 3 신규/정정**: 펀더멘털 PIT+생존편향(H5, 가치전략 토대), C2×Phase3 강등 충돌(매수 abstain, H14), 양다리 원자성 불가→leg unwind+source-of-truth(H2), Phase 0 parity 재정의(RAG격리/freeze/결정성+의미동치), kill switch halt-then-confirm(자동 전량청산 footgun 제거), **세율 0.18%→0.20% 정정(웹검증)**, +H16 기업행위·H17 가격제한폭·H18 US FX·H19 코인 shadow-live(Upbit 테스트넷 없음)·H20 수동이관/글로벌limiter·H21 constrained decoding.
> - **메타(Round 3)**: 두 LLM이 부분만 보이는 코드를 평가하면 blind spot을 공유(README 과신·런타임 버그 미포착)한다. cross-model 수렴은 *검증이 아니라 가설 생성*으로 취급하고, **진짜 게이트는 §2.9 fault-injection**이다 — 이 문서의 가장 단단한 자산.
> - **Round 4 신규**: H22 LLM 백테스트 오염(training-data lookahead로 패리티 원리적 불성립 → 기계적/LLM 2층 분리, 최우선), H23 다중검정/PBO, H24 kimchirang 규제 viability(Binance 한국 차단 웹검증 → research/shadow 강등 검토), H25 상관 위기수렴, H26 numeraire/FX 타이밍, H27 halt-then-confirm 무인 보완(시간분산 축소), H28 전략 capacity. + 세금 nuance(손익통산·국내상장 해외ETF 배당과세).
> - **수렴 판정(4라운드 종합)**: 코드근거 축(E2/R2/B1/B3 등 라이브 코인)은 **완전 수렴**(Round 4 Gemini 순수 추인) → Phase -1은 즉시 착수 가능. 신규 발견은 전부 *아직 코드 없는* 주식·멀티에셋 설계 영역(H16~H28)에서 나옴 → 추가 라운드는 수확체감. **리뷰 종료, Phase -1 구현 착수 + 주식트랙은 PIT/H22 데이터원칙부터 확정** 권고.

## 참고 GitHub 목록 (두 모델 즉시 참조용)

평가 대상:
- 본 프로젝트: https://github.com/jsh8603-web/coin

두뇌·멀티에이전트:
- TradingAgents (오케스트레이션·모델카탈로그·구조화출력): https://github.com/TauricResearch/TradingAgents
- ai-hedge-fund (투자거장 페르소나·밸류에이션): https://github.com/virattt/ai-hedge-fund
- dexter (심층 금융리서치 에이전트): https://github.com/virattt/dexter
- AlpacaTradingAgent (Macro Analyst·Ollama·로컬): https://github.com/huygiatrng/AlpacaTradingAgent
- TradingGoose (Portfolio Manager 결정위계): https://github.com/TradingGoose/TradingGoose.github.io

정량·배분·리스크:
- FinRL (DRL 배분): https://github.com/AI4Finance-Foundation/FinRL
- FinRL-Trading / FinRL-X (no-lookahead·Alpaca): https://github.com/AI4Finance-Foundation/FinRL-Trading
- Riskfolio-Lib (HRP·CVaR·Kelly): https://github.com/dcajasn/Riskfolio-Lib
- skfolio (walk-forward CV·데이터누수 방지): https://github.com/skfolio/skfolio
- PyPortfolioOpt (Black-Litterman·HRP): https://github.com/robertmartin8/PyPortfolioOpt
- yakub268/algo-trading-platform (리스크엔진·HMM레짐·대시보드): https://github.com/yakub268/algo-trading-platform
- polymarket-bot (레이어드 익싯·ghost check·Kelly): https://github.com/guberm/polymarket-bot

실행·이벤트·데이터:
- nautilus_trader (멱등 주문 상태머신·backtest-live 패리티·슬리피지): https://github.com/nautechsystems/nautilus_trader
- OpenBB (글로벌·매크로 멀티소스): https://github.com/OpenBB-finance/OpenBB
- AgenticTrading (HMM 레짐·MCP): https://github.com/Open-Finance-Lab/AgenticTrading
- trader-magic (로컬 Ollama+실행 레퍼런스): https://github.com/rawveg/trader-magic
- llm-trading-strategy-assistant (완전 로컬·멀티모달): https://github.com/maghdam/llm-trading-strategy-assistant

한국·실행(KIS):
- koreainvestment/open-trading-api (공식, LLM 샘플): https://github.com/koreainvestment/open-trading-api
- Soju06/python-kis (웹소켓 자동재연결): https://github.com/Soju06/python-kis
- pjueon/pykis: https://github.com/pjueon/pykis
- sharebook-kr/pykrx (KRX 데이터): https://github.com/sharebook-kr/pykrx
- sharebook-kr/pykrx-mcp (MCP): https://github.com/sharebook-kr/pykrx-mcp
- FinanceData/FinanceDataReader (다국가·ETF·환율): https://github.com/FinanceData/FinanceDataReader

큐레이션:
- awesome-systematic-trading: https://github.com/wangzhe3224/awesome-systematic-trading
- awesome-quant: https://github.com/wilsonfreitas/awesome-quant

---

## 0. 컨텍스트 (현재 자산 = 절대 무시 금지)

기존 `coin` 리포(v1.29.0, Python 93%)는 단일자산(BTC) 자동매매의 **검증된 레퍼런스**다. 아래 자산을 **재사용·일반화**한다. 새로 만들지 말 것:

- `agents/base_agent.py` — `calculate_buy_score()`(점수제), `kelly_position_size()`, `detect_regime()`, 레짐별 적응형 청산(`trailing_stop_bull -15` ~ `trailing_stop_bear -1.5`), 이중 스톱(`stop_loss_pct -5` / `forced_stop_loss_pct -10`)
- `agents/orchestrator.py` — `_calculate_danger_score`/`_calculate_opportunity_score`(0~100), 3계급 에이전트 자율전환, `warmup_threshold` 블렌딩, file locking
- `agents/external_data.py` (NewsRang) — 11소스 병렬 수집 + Data Fusion 5단계 신호
- `rl_hybrid/` — ZMQ 메시지 버스(main_brain ↔ llm_worker ↔ trading_worker ↔ rl_worker), PPO, `decision_blender`(RL+LLM 블렌딩), RAG 자기기억
- `prompts/schemas/decision_result.json` — 결정 JSON 스키마 (`next_check_recommendation`, `feedback_applied`, `confidence` 포함)
- `strategy.md` — 자연어 전략(LLM이 해석, 코드 하드코딩 안 함)
- `supabase/migrations/` — 50개 마이그레이션 (decisions, embeddings, near_miss_veto, execution_failures, decision_aftermath 등 감사 테이블)
- 안전장치: `DRY_RUN`, `EMERGENCY_STOP`(에이전트가 해제 불가), Lifeline 자동긴급정지, 텔레그램

**핵심 보존 원칙**: 점수 투명성(score breakdown), 자연어 전략, JSON 결정 스키마, 감사 테이블, DRY_RUN 게이팅, 수동 EMERGENCY_STOP 우회 불가 — 이 6가지는 전 트랙에 유지·확장한다.

---

## 0.5 Phase 0 사전검증 (코드로 먼저 확인 — 이 스펙의 추론성 가정)

본 스펙은 grep 조각 기반이라 아래 가정을 **실제 코드로 먼저 검증**하고 차이를 보고한 뒤 착수한다:

1. **임베딩-RL 차원 결합** *(교차검증으로 정정됨 — 위험 하향)*: 라이브 경로는 `main_brain.py:350-351`·`live_trader.py:61`이 **임베딩-프리 `StateEncoder`(obs_dim=42)**를 쓰므로 Gemini→BGE 교체로 **라이브 PPO가 깨지지 않는다**(기존 "PPO 파괴" 가정은 과장이었음). Gemini 결합은 **휴면 경로** `llm_state_encoder.py`(`LLM_EMBEDDING_DIM=3072`→64d projection→`ENHANCED_OBS_DIM=106`)에만 존재. 따라서 진짜 작업은 ① `decision_embeddings`(3072d)→BGE(1024d) **재임베딩 후 RAG top-k recall delta 측정**, ② 106d enhanced 인코더를 쓰는 경우에만 reproject. embedder 차원은 config화하고 42d 라이브 경로는 임베딩-무관 유지. (Gemini 평가의 "1024→42 PCA 어댑터" 권고는 이 정정 전 가정에 기반한 것이라 **채택 안 함**.) **(Round 2 M4 — 마이그레이션 역호환)**: 임베딩 차원은 이미 1536d(OpenAI)→3072d(mig 045, Gemini)로 한 번 바뀐 이력이 있어 BGE 1024d(mig 051)는 **세 번째 변경**이다. 재임베딩 중 구·신 벡터(3072/1024) 혼재 시 RAG가 차원 불일치로 깨질 수 있으므로, 051에 **"재임베딩 완료 전까지 신규 인덱스 미사용" 가드 + 진행률 체크포인트**를 둘 것.
2. **decision_blender 포맷 의존**: `rl_hybrid/rl/decision_blender.py`가 Gemini 출력 구조에 의존하는지.
3. **기존 임베딩 테이블 실제 차원**: `decision_embeddings`/`rag_analysis_vectors`의 현재 벡터 차원 확인 후 BGE-m3(예상 1024) 마이그레이션 설계.
4. **ZMQ 메시지 계약**: `llm_worker` 교체가 main_brain/trading_worker 메시지 스키마를 깨지 않는지.

---

## 1. 목표 아키텍처

```
                  [Portfolio Orchestrator]   ← 자산배분 (코인/주식/현금 비중)
                  레짐 + 상관도 기반, 트랙 간 자본 한도 배분
                          │
        ┌─────────────────┴─────────────────┐
   [Coin Track: 기존 흡수]            [Stock Track: 신규]
   AssetTrack 구현체                  AssetTrack 구현체
   - 모멘텀/심리/레짐 트리거(기존)      - 가치기반 2단 트리거(신규)
   - BTC 단일                          - KR/US 개별주 + ETF
        │                                      │
        └─────────────────┬─────────────────┘
              [Shared Risk Gate]   ← 우회 불가, hard rule
              포트폴리오 손실한도 / 상관도 캡 / 회전율 / kill switch
                          │
        ┌─────────────────┴─────────────────┐
   [Coin Exec: 기존]                 [Stock Exec: 신규]
   업비트 / 바이낸스                  한국투자증권(KIS)
```

신설 디렉토리(제안):
```
core/                       ← asset-agnostic 추상 (신규)
  asset_track.py            ← AssetTrack ABC
  risk_gate.py              ← 공통 리스크 게이트 (Lifeline/한도/kill switch 일반화)
  portfolio_orchestrator.py ← 트랙 간 자본배분
  brain/                    ← 두뇌 추상 (Gemini → Qwen/Claude 교체 지점)
    llm_provider.py         ← LLM 추상 인터페이스 (quick/deep 분리)
    embedder.py             ← 임베딩 추상 (Gemini → BGE-m3)
stock/                      ← 주식 트랙 (신규)
  value_trigger.py          ← 가치기반 2단 트리거
  valuation.py              ← 내재가치 산출 (DCF/멀티플)
  kis_client.py             ← 한국투자증권 실행 어댑터
  data/                     ← pykrx, FinanceDataReader, OpenBB, FRED/ECOS
coin/  (= 기존 agents/, rl_hybrid/, kimchirang/ 를 AssetTrack 구현체로 래핑)
backtest/                   ← 2018+ 통합 백테스트 (nautilus_trader 선택 채택)
```

---

## 2. 단계별 구현 계획 (Phase)

각 Phase는 독립 PR + 테스트 통과 + DRY_RUN 검증 후 다음으로 진행.

> **⚠️ 시퀀싱 원칙 (Round 2 핵심 교정)**: 가장 치명적인 갭(E2 멱등성·R2 reconciliation·B1 스키마강제·B3 결정성·C2 서킷브레이커)은 **미래의 주식 트랙이 아니라 지금 당장 실금전 매매가 가능한 라이브 코인 경로**에 있다. 따라서 이들을 Phase 2/4로 미루지 말고 **Phase -1로 끌어와 현재 코인 경로에 먼저 적용**한다. 특히 Phase 1(Gemini→Qwen, 환각률↑ 모델)을 스키마강제(B1) 없이 먼저 하면 위험구간이 생기므로 — **안전 하드닝 → 그 다음 두뇌교체·주식확장** 순서를 지킨다.

### Phase -1 — 라이브 코인 안전 하드닝 (최우선, 두뇌교체·주식확장보다 먼저)
현재 코인 경로에 직접 적용. 주식/Qwen과 무관하게 즉시 가치.
- **E2 멱등성(H9)**: Upbit `identifier`(client_order_id) 부여 + 제출 전 미체결/체결 조회 → 멱등 재시도.
- **R2 reconciliation(H2)**: 사이클마다 실잔고↔내부상태 대조 + `execution_failures` 기록. **kimchirang 양다리는 leg-level 별도**(아래 H2 참조).
- **B1 스키마 하드게이트(H3)**: 현재 Gemini 출력부터 jsonschema 강제(Qwen 전환 전 필수 선행).
- **B3 결정성(H10)**: temperature=0 + model_id/prompt_hash를 결정 레코드에 기록 — **거의 0비용 quick win, 즉시 착수**.
- **C2 서킷브레이커(H14)**: 일일 LLM 호출 캡 + 폭주 시 degrade-to-Qwen.
- **수용 기준**: §2.9의 E2·R2·B1 결함주입 판정을 **현 코인 라이브(DRY_RUN)에서** 통과.

### Phase 0 — 코어 추상화 (기존 코인 동작 100% 보존)
- `core/asset_track.py`: `AssetTrack` ABC 정의
  - `collect_market_state() -> dict`
  - `generate_candidate(state) -> Decision`  (점수제, 기존 calculate_buy_score 패턴 따름)
  - `recommended_next_check(state) -> datetime`  (기존 `next_check_recommendation` 일반화 = 적응형 폴링)
- **⚠️ 전략 택소노미 분기 (Round 2 M1 — 단일 ABC로 뭉개지 말 것)**: 리포에는 단일자산 방향성 외에 **kimchirang(델타뉴트럴·양다리·2거래소), scalp_ml(LightGBM+DQN 초단타·sub-minute 폴링), altrang(mig 040)**이 별개 아키타입으로 존재. 이들은 `generate_candidate→buy_score`(방향성) 시그니처와 `recommended_next_check`(적응형 폴링) 가정에 안 맞는다.
  - → AssetTrack을 **Directional / MarketNeutral / HFT** 3계열로 분기하거나, kimchirang·scalp_ml은 AssetTrack 밖 별도 `Strategy` 인터페이스로 두고 risk_gate·포트폴리오 레벨에서만 통합.
- 기존 코인 로직을 적절한 계열 구현체로 **래핑만** 한다. 시그니처 보존, 동작 불변.
- **수용 기준**: 기존 코인 + **kimchirang·scalp_ml DRY_RUN 결과가 래핑 전후 동일**(회귀 0건).

### Phase 1 — 두뇌 마이그레이션 (Gemini → Qwen 로컬 + Claude / 임베딩 → BGE-m3)
마이그레이션 대상 파일(grep 확인됨):
`rl_hybrid/rag/gemini_client.py`, `rl_hybrid/rag/embedding_store.py`, `rl_hybrid/nodes/llm_worker.py`, `rl_hybrid/rl/decision_blender.py`, `rl_hybrid/rl/llm_state_encoder.py`, `scripts/run_agents.py`, `scripts/embed_historical_data.py`

- `core/brain/llm_provider.py`: 추상 인터페이스. 구현체 `OllamaQwenProvider`(quick), `ClaudeProvider`(deep), (기존 `GeminiProvider` 호환 유지).
  - 라우팅 규칙: 평상시 = Qwen 로컬 quick. 트리거 발동 시에만 = Claude deep.
- `core/brain/embedder.py`: 추상화. 구현체 `BGEm3Embedder`(로컬, 기존 DA 검색 자산 재사용), `GeminiEmbedder`(호환).
  - **주의**: 기존 `decision_embeddings`/`rag_analysis_vectors` 테이블의 벡터 차원이 Gemini 기준이므로, BGE-m3 차원(1024)에 맞춰 신규 마이그레이션 SQL(`051_bge_embeddings.sql`)을 추가하고 기존 벡터는 재임베딩 스크립트로 마이그레이션.
- ZMQ 워커 구조 덕에 `llm_worker`만 교체하면 main_brain/trading_worker 무변경.
- **수용 기준**: Qwen 로컬로 평상시 사이클 동작, Claude 호출은 트리거 시에만 발생(로그로 호출 카운트 검증).

### Phase 2 — 공통 리스크 게이트 (asset-agnostic, 우회 불가)
- `core/risk_gate.py`: 기존 Lifeline·이중스톱·일일한도를 **트랙 무관**으로 승격.
  - 입력: 모든 트랙의 매수/매도 후보(Decision) + 현재 통합 포트폴리오
  - hard rule (절대 우회 불가):
    - per-position stop: soft −5% / forced −10% (기존값 트랙별 오버라이드 가능)
    - 일일 포트폴리오 손실 한도 도달 시 전 트랙 신규매매 halt
    - 상관도 캡: 트랙 간/종목 간 corr > 0.7 중복 진입 차단
    - 종목 max weight(단일 10% / 섹터 30% / 트랙 max 비중)
    - `max_annual_turnover`, `min_holding_period` (수수료·세금 제어 — 아래 §5)
    - portfolio kill switch: 통합 MDD > X% → **신규진입 halt + 알림 + 사람 컨펌 후에만 청산**(자동 전량청산 금지 — 플래시크래시 바닥 매도 후 반등 footgun). **단 무인 보완(H27)**: 컨펌이 N시간 내 없고 손실이 2차 임계 초과 시(US장=KST 야간 대비) 자동 *시간분산 축소*(전량 아님). 그 외엔 수동 컨펌 전까지 포지션 보존.
    - 수동 `EMERGENCY_STOP`은 어떤 에이전트도 해제 불가 (기존 원칙 유지)
- **격리**: risk_gate는 별도 모듈 + 매매 실행 권한 보유 프로세스와 LLM 프로세스를 분리. LLM은 후보 제안까지만. (기존 `--dangerously-skip-permissions` 제거 검토)
- **수용 기준**: 게이트가 거절/축소한 사례가 `near_miss_veto` 테이블에 기록됨(기존 감사 패턴 재사용).

### Phase 3 — 주식 트랙 + 가치기반 2단 트리거 (신규)
- `stock/valuation.py`: 내재가치 산출 (DCF 간이 + PER/PBR/EV-EBITDA 멀티플 밴드). ai-hedge-fund Valuation/Damodaran 로직 참고.
- `stock/value_trigger.py`: **2단 게이트**
  ```
  1차 (싸고 빠른 Qwen 필터): 가격 변동 > X% (예: 가치주 -7%)
     └→ AND 내재가치 갭(margin of safety) > 임계치 (예: 가격이 내재가치의 70% 이하)
          └→ 2차 (heavy agent = Claude/Damodaran 페르소나):
               내재가치를 재산출하여 "싸진 것(기회)"인지 "thesis 붕괴(value trap)"인지 판정
               └→ 갭 유효 시에만 → risk_gate로 매수 후보 전달
  ```
  - **함정 방지**: 단순 buy-the-dip 금지. 가격↓ + 내재가치↓(동반 하락)이면 매수 아님.
- `stock/StockTrack(AssetTrack)`: 점수제는 기존 패턴 유지하되 입력 피처를 가치·펀더멘털로 교체. 매크로 트리거(top-down)는 자산배분 레벨(Portfolio Orchestrator)에서 처리.
- 자연어 전략: `strategy_stock.md` 신설 (기존 strategy.md 포맷 그대로, 점수표 형식 유지).
- **수용 기준**: 가격만 빠진 종목 vs 가치 갭이 벌어진 종목을 트리거가 구분(테스트 케이스).

### Phase 4 — 데이터 레이어 + KIS 실행
- `.mcp.json`(현재 `{}`)에 `pykrx-mcp` 추가 → Qwen 에이전트가 한국 데이터 자연어 조회.
- `stock/data/`: pykrx(국내), FinanceDataReader(국내·미국·ETF·환율), OpenBB(글로벌·매크로), FRED + 한국은행 ECOS(거시지표).
- NewsRang(기존 11소스)을 **공통 매크로 소스로 승격** → 주식 트랙도 DXY/10Y/유가/FGI 공유.
- `stock/kis_client.py`: 한국투자증권 어댑터. `koreainvestment/open-trading-api`(공식) + `Soju06/python-kis`(웹소켓 자동재연결) 참고. **모의투자 환경 우선**.
- **수용 기준**: KIS 모의투자로 주문 제출/조회/취소 왕복 성공.

### Phase 5 — 통합 백테스트 (2018+)
- `backtest/`: 2018-01-01 이후. 코로나·금리인상·BTC 사이클 포함.
- 옵션 A(가벼움): skfolio walk-forward CV + 기존 코인 백테스트 스크립트 확장.
- 옵션 B(엄격함): `nautechsystems/nautilus_trader` 채택 → backtest-live 코드 패리티. 주식 트랙부터 적용, 코인은 후순위.
- 슬리피지·수수료·세금(§5)을 반드시 반영(README의 "백테스트 환상 vs 실데이터" 교훈 준수).
- **수용 기준**: 동일 전략 코드가 백테스트와 DRY_RUN 라이브에서 동작(패리티).

### Phase 6 — Portfolio Orchestrator (최상위)
- `core/portfolio_orchestrator.py`: 레짐 + 트랙 간 상관도 기반으로 코인/주식/현금 자본 비중 결정.
- 디폴트 배분: Riskfolio-Lib HRP(신호 약할 때 fallback).
- 트랙별 자본 한도를 risk_gate에 전달.

---

## 2.9 단계별 운영 합격 판정 (Operational Acceptance)

각 Phase는 "테스트 green"이 아니라 **아래 운영 목표를 실측으로 통과**해야 다음으로 넘어간다. 모든 판정은 실제/재생 시장 데이터 또는 결함 주입(fault injection)으로 검증하며, 결과 수치를 보고한다.

> **기존 테스트 자산 활용(Round 1 발견)**: 리포에 이미 ~80개 테스트(`test_e2e_*`, `test_lifeline`, `test_build_safety`, `test_orchestrator_switch_dedup` 등)가 있다. Phase별 운영 acceptance는 이 하니스를 **확장**하라(신규 작성 최소화).

### Phase 0 — "보이지 않는 리팩터링" 증명
- **운영 목표**: 래핑 후에도 기존 코인 봇의 매매 판단이 의미적으로 바뀌지 않는다.
- **판정**: 최근 7일치 실제 시장 상태(틱/캔들/외부신호)를 래핑 전·후 경로에 동일 입력 → 모든 사이클의 `decision`·`buy_score breakdown`이 **의미적 동치**(수치는 tolerance 내). **단, parity 하니스 전제(Round 3)**: ① RAG 자기기억(decision_aftermath·embeddings) 상태 격리/리셋(run이 남긴 기억이 다음 run 입력을 바꾸면 같은 7일도 달라짐) ② 외부데이터·시계 freeze ③ PPO 추론 결정성(argmax거나 고정 seed) — B3(H10) 결정성을 Phase -1에서 선행. "1건이라도 diff" 같은 byte 동일 기준은 부동소수점 재정렬에 깨지므로 금지. **④ LLM 출력은 record-and-replay fixture로**(첫 run의 LLM 응답을 저장해 재생 — H22의 그 인프라와 동일, 한 번에 구축). 그래야 LLM-프리 경로가 아닌 실제 라이브 동작과 의미 동치가 성립.

### Phase 1 — "비용 0의 상시감시 + 트리거시 각성" 증명
- **운영 목표**: 평상시 Qwen 로컬만 돌고 Claude는 사건 때만 호출되며, 두뇌 교체로 판단 품질·기억(RAG)·PPO가 깨지지 않는다.
- **판정**: 72시간 연속 DRY_RUN에서 ① 평상시 Claude 호출 = 0, Claude 호출 횟수 = 트리거 발동 횟수와 정확히 일치 ② 실제 변동성 이벤트(예: BTC −5% 급락) 재생 시 트리거 발동→Claude 호출 발생 ③ BGE-m3 재임베딩 후 과거 유사패턴 RAG top-k recall이 Gemini 대비 유지(저하 < 10%p) ④ PPO 추론 정상(차원오류·NaN 0건) ⑤ Qwen vs 기존 Gemini 의사결정 방향성 일치율 보고(참고지표).

### Phase 2 — "위험주문은 반드시 막힌다 + 우회 불가" 증명 (결함 주입)
- **운영 목표**: 게이트가 실제로 위험을 차단하고, LLM이 절대 우회하지 못한다.
- **판정**: 5종 시나리오 주입 전부 통과 — ① 일일 손실한도 초과 주입 → 신규매매 halt ② 상관도 0.7+ 중복진입 시도 → 차단 ③ 종목 max weight 초과 주문 → 자동 축소 ④ MDD 임계 주입 → **신규진입 halt + 알림 + 사람 컨펌 전까지 청산 보류**(자동 전량청산 아님) ⑤ LLM이 게이트 룰 수정/우회 시도 → 실패. 5건 모두 `near_miss_veto`에 사유와 함께 기록.

### Phase 3 — "기회와 함정을 구분한다" 증명 (역사적 케이스)
- **운영 목표**: 가격이 빠진 종목 중 진짜 싸진 것만 사고, value trap은 거른다.
- **판정**: 한국·미국의 **실제 역사적 사건** N개(≥10, **반드시 상장폐지/0으로 간 종목 포함** — 생존편향 제거)로 — ① 일시적 패닉셀(내재가치 유지)에서 매수 후보 생성 ② 실적쇼크/구조적 악재(내재가치 동반 하락)에서 매수 안 함. value-trap 회피율과 기회 포착율을 혼동행렬로 보고. value-trap을 매수한 케이스가 있으면 트리거 재설계.

### Phase 4 — "실거래 라이프사이클 + 한도 견딤" 증명 (KIS 모의)
- **운영 목표**: KIS 모의계좌에서 주문이 끝까지 돌고, 분당 한도와 토큰만료를 견딘다.
- **판정**: ① 매수→체결확인→매도→정산 왕복 성공 ② 부분체결 상황에서 미체결 잔량 처리 정상 ③ 분당 한도 80%까지 호출 부하를 줘도 실패율 < 5%(RoboTrader 75% 실패 대비) ④ 6시간 경과시 토큰 자동 갱신 + 웹소켓 자동 재연결 ⑤ 잔고에 인위적 drift 주입 → reconciliation이 다음 사이클에 감지·기록.

### Phase 5 — "백테스트가 거짓말하지 않는다" 증명
- **운영 목표**: 슬리피지 포함 현실 백테스트 + 백테스트↔라이브 코드 패리티 + 과적합 미발생.
- **판정**: ① 슬리피지 0 vs 현실 슬리피지 백테스트 수익률 차이를 정량화·보고(차이 과대 시 전략 경고) ② **기계적 score 레이어**(LLM 제외)의 동일 전략 코드가 2018-01~현재 백테스트와 DRY_RUN 라이브에서 동일 신호 생성(패리티 ≥ 95%). **LLM 판단 레이어는 training-data lookahead·재현불가로 패리티 측정 대상에서 명시적 제외**(H22). LLM은 백테스트에서 abstain stub으로 대체 ③ walk-forward OOS Sharpe / in-sample Sharpe 비율 + **Deflated Sharpe/PBO**(H23, trial-count 보정) 보고 ④ 전 구간(코로나·금리인상·약세장) MDD가 kill switch 임계 내. 유니버스에 상장폐지 종목 포함(H5).

### Phase 6 — "스스로 살아 돌아간다 + 분산효과" 증명
- **운영 목표**: 레짐에 따라 자본이 실제 이동하고, 통합 포트폴리오가 개별 트랙 합보다 안전하며, 90일 무중단 운영된다.
- **판정**: ① 레짐 전환(불→베어) 재생 시 코인/주식/현금 비중 실제 이동 ② 통합 MDD < 개별 트랙 MDD 단순합(분산효과 수치 증명) ③ 통합 대시보드에 P&L·MDD·Sharpe·회전율·LLM비용 실시간 표시 ④ **90일 연속 DRY_RUN 무중단 완주**(self-healing 작동, 다운타임 0, 일일요약 정상 발송).

### 🚦 실전 자금 전환 게이트 (전 Phase 누적 — 통과 전 실자금 금지)
1. Phase 0~6 운영 판정 전부 통과.
2. KIS 모의 + 코인 DRY_RUN을 **합산 90일 이상** 무중단 운영, 그 사이 최소 1회의 실제 급락/급등 이벤트를 사고 없이 통과.
3. 라이브(DRY_RUN) 신호가 백테스트 분포 안에 있음(드리프트 경보 0).
4. kill switch·EMERGENCY_STOP·reconciliation을 실제 발동시켜 본 기록 존재.
5. 통과 후에도 초기 실자금은 잃어도 되는 극소액부터.

---

## 3. 트리거 로직 사양 (요약)

| 트랙 | 트리거 성격 | 구현 |
|---|---|---|
| 코인 | 모멘텀·심리·레짐 | 기존 `calculate_buy_score` + danger/opportunity + `detect_regime` (재사용) |
| 주식(bottom-up) | 가치 갭 (가격 vs 내재가치) | `value_trigger.py` 2단 게이트 (신규) |
| 자산배분(top-down) | 매크로 지표 유의변동 | Portfolio Orchestrator (신규) |

폴링 cadence는 기존 `next_check_recommendation`을 일반화한 `recommended_next_check()`로 트랙별 적응형 결정. 평상시 Qwen 로컬, 트리거 시 Claude.

---

## 4. 두뇌 라우팅 규칙 (비용 통제)

```
평상시 (N분 주기, Qwen 로컬):
  - 매크로/포지션/지표 스냅샷 체크
  - 점수제 1차 필터
  - 임계치 미달 → 아무 것도 안 함 (Claude 호출 0)

트리거 발동 시에만 (Claude deep):
  - 코인: danger/opportunity 극단 or 레짐 전환
  - 주식: 가격변동 AND 내재가치갭 동시 충족
  - 자산배분: 매크로 surprise
  - → Claude로 내재가치 재산출 / 최종 판단 → risk_gate
```

임베딩은 전량 BGE-m3 로컬. Claude/Qwen API 호출 카운트를 텔레그램 일일 요약에 포함.

---

## 5. 수수료·세금 정책 (게이트 hard parameter)

> **세율 갱신(Round 3, 웹검증 완료)**: 2026-01-01부터 금투세 폐지로 증권거래세 환원 — **코스피·코스닥 매도 실효세율 = 0.20%**(코스피 0.05%+농특세 0.15% / 코스닥 0.20%). 문서의 0.18%는 2024년 stale 값. 또한 **국내 개인 주식 양도차익세는 사실상 0**(대주주만 과세) → ETF vs 개별주 복제 시 *거래세 차이(0.20%)는 실재하나 양도세 차이는 국내 개인에겐 없음*. 해외주식 양도세 22%(+지방세)/250만원 공제는 유효.

- 국내주식 ETF를 개별주로 복제 금지(매도 시 거래세 **0.20%** 발생 → 운용보수 절감분 초과).
- 국내상장 해외 ETF는 KIS 해외주식 직접매매로 대체 검토(운용보수 0.3~0.5% 회피).
- 고비용 테마 ETF(보수 0.5%+)만 선택적 부분복제.
- `max_annual_turnover`, `min_holding_period`로 회전율 자체를 억제(수수료/세금 직접 통제).
- 백테스트·risk_gate turnover 비용에 거래세(국내 **0.20%** 매도), 해외 환전수수료(~0.2%), 해외 양도세(22%/250만 공제), 슬리피지 모두 반영.
- **세금 nuance(Round 4)**: ① 해외주식 양도세는 *연간 종목 간 손익통산* 후 과세 → risk_gate의 회전율 억제(`min_holding_period`)가 연말 tax-loss harvesting(손실실현 통산) 경로를 막지 않도록 예외 허용. ② 국내상장 해외ETF의 분배·매매차익은 **배당소득 15.4% + 금융소득종합과세(2천만원 초과) 합산** → ETF→직접보유 대체의 이득은 보수 절감뿐 아니라 *과세 성격 차이*가 더 큼(0.20% 거래세 비교만으론 의사결정 왜곡).

---

## 5.7 Stock 트랙 데이터 토대 스펙 (이 세션 확정 — 주식 트랙의 첫 단추)

가치전략의 백테스트·내재가치 산출이 거짓이 되지 않게, 코드 착수 전 데이터 원칙을 고정한다. **H5(펀더멘털 PIT)·H16(기업행위)·H22(LLM 2층) 종합.**

**A. 펀더멘털 PIT (pykrx/FDR 불가 → DART/EDGAR 필수)**
pykrx·FinanceDataReader는 *현재 시점의 재작성된* 재무를 줘서 가치전략 백테스트에 쓰면 "발표 전 실적을 아는" 누수가 생긴다. 모든 펀더멘털에 **(회계기간, 공시 접수일자/filing timestamp, as-reported 값)** 3-튜플 태깅. 백테스트는 `announcement_date ≤ as_of_date`인 데이터만 사용.
- 한국: **DART OpenAPI**(opendart.fss.or.kr) — 접수일자 + as-reported 원본. 정정공시는 원본 접수일 기준으로만(나중 정정값 금지). pykrx/FDR은 가격·시세 전용.
- 미국: **SEC EDGAR**(filing timestamp + XBRL as-reported).
- 공시 dissemination lag(접수→시장반영)를 announcement-date 정렬 레이어에 반영.

**B. 생존편향 (PIT 유니버스에 상폐 포함)**
백테스트 유니버스 = 그 시점의 구성종목(상장폐지 종목 포함). 한국 FDR `KRX-DELISTING`, 미국 상폐 포함 historical constituents. Phase 3 value-trap 검증 유니버스도 동일.

**C. 기업행위 (H16)**
수정주가 + 이벤트 캘린더(분할·배당락·합병·유상증자·상폐)로 분할이 "-50% 급락"으로 안 보이게. reconciliation 오류 방지.

**D. H22 2층 백테스트 (가장 중요)**
- **Layer 1 (기계적)**: `calculate_buy_score`·멀티플 밴드·레짐 → PIT-clean 정상 백테스트. **패리티(≥95%)는 이 레이어에서만 측정**.
- **Layer 2 (LLM 판단)**: 백테스트 패리티에서 **명시적 제외**(training-data lookahead·재현불가). 백테스트에선 "기계적 레이어만으로 자격 안 되면 abstain" 보수적 stub. forward-test에서만 record-and-replay fixture.
- `stock/value_trigger.py`의 내재가치 산출은 반드시 **announcement-date 정렬 PIT 펀더멘털**로(현재 재작성값 금지). 2단 게이트의 heavy-agent(thesis붕괴 판정)도 H22 stub 정책을 따른다.

> 이 스펙이 주식 트랙 Phase 3·4·5의 전제. 데이터 토대가 거짓이면 그 위 전부가 거짓이므로, 코인 Phase -1과 병행해 **데이터원 결정(DART/EDGAR 연동)부터** 착수.

---

## 5.5 내구성(Hardening) 요구사항 — 검토 축 기반, 전 Phase 횡단

실제 코드 검토에서 드러난 갭. 각 항목은 해당 Phase에 **필수 작업**으로 포함한다.

### H1. 백테스트 현실성 — 슬리피지/호가 모델 (Phase 5, 최우선)
*(교차검증 정밀화)* 슬리피지가 완전 부재는 아니다 — `reward.py`/`reward_v7/v8`에 `SLIPPAGE_RATE=0.0003`(flat 3bps)이 있다. 그러나 ① **백테스트 엔진 `sim_engine.py`엔 `FEE_RATE`만, 슬리피지 0**(README가 자인한 교훈이 정작 백테스트에 미반영) ② 존재하는 곳도 호가깊이·체결규모 비례가 아닌 **고정상수**.
- `sim_engine.py`에 슬리피지 반영 + **거래대금/호가잔량 비례 임팩트** 모델로 격상(고정상수→동적). 코인은 Upbit 호가, 주식은 KIS 호가/스프레드.
- 산재한 13개 backtest_*.py를 **단일 엔진**으로 통합(또는 nautilus 채택 시 그 위에서). FinRL식 거래비용 env 참고.
- **타임존 패리티**(minor): 코드 전반 `datetime.now(KST)`. Upbit(KST)/Binance(UTC)/KIS 시각 정렬을 통일하지 않으면 backtest-live 패리티 버그원이 된다 — 단일 UTC 기준 + 표시만 KST 권장.

### H2. 상태 정합성 — reconciliation 루프 (Phase -1/2/4)
거래소 잔고를 내부 상태와 대조하는 루프가 없다(부분체결·drift 위험).
- 사이클마다 거래소 실잔고 ↔ 내부 포지션 대조 → 불일치 시 보정 + `execution_failures` 기록. polymarket-bot의 "ghost check" 패턴 차용.
- 부분체결(partial fill) 명시 처리: 미체결 잔량 취소/재주문 규칙.
- **양다리/교차거래소(Round 2 M2 + Round 3 정정, kimchirang 치명)**: kimchirang은 Upbit 롱 + Binance 숏 → leg risk(한 다리만 체결 시 방향성 노출). **단, 두 독립 거래소의 "진짜 원자성"은 물리적으로 불가능** — "둘 다 체결 or 둘 다 취소"는 구현 불가 스펙이다. 현실 스펙은 **leg-by-leg 체결 + hedge-completion 데드라인 + 2번째 다리 실패 시 1번째 다리 unwind 프로토콜**. 그리고 reconciliation엔 **source-of-truth 정책**이 필요: "거래소=truth, 단 H11 staleness/quorum 통과 시에만, 임계 초과 drift는 auto-correct가 아니라 halt"(거래소가 일시적으로 틀린 잔고를 줄 때 맹목 추종 방지). 교차거래소 시계 정렬(H1 타임존)은 arb에선 실손익원.

### H3. 구조화 출력 강제 검증 (Phase 1)
`decision_result.json` 스키마는 있으나 결정 경로에서 **jsonschema 검증이 강제되지 않는다** → LLM 환각/깨진 JSON 통과 위험.
- `llm_worker` 출력 → risk_gate 진입 사이에 jsonschema 검증을 **하드 게이트**로. 실패 시 관망 처리 + `near_miss_veto` 기록.
- TradingAgents v0.2.4 structured-output 패턴 참고. Qwen 로컬은 환각 가능성이 더 크므로 이 검증이 더 중요.

### H4. 중앙 레이트리밋 (Phase 4, KIS 치명적)
코인은 버텼지만 KIS는 분당 한도 초과 시 실패율 75%(RoboTrader 사례). retry/sleep이 산발적이다.
- 거래소별 **중앙 토큰버킷 limiter**(코인/KIS 분리). 백오프 + 우선순위 큐(주문 > 조회).
- KIS 토큰 6시간 만료 자동 갱신 + 웹소켓 재연결(`Soju06/python-kis` 패턴).

### H5. 체계적 walk-forward / no-lookahead (Phase 5) + **펀더멘털 PIT·생존편향 (Round 3 #1 — 가치전략 토대)**
보상함수 clip·multi-objective(tail_risk 포함)는 우수하나, 수동 기간분리(2018-21/2022-24)뿐 체계적 OOS 하니스가 없어 온라인 학습이 최근 레짐에 과적합할 위험.
- walk-forward 분할 + strict no-lookahead(point-in-time 데이터) 강제. FinRL-X "no-lookahead semantics", skfolio CV 참고.
- 라이브 성과를 백테스트 분포와 비교하는 drift 모니터(라이브≪백테스트면 경보).
- **D1을 가격-PIT / 펀더멘털-PIT로 분리(가치전략 존재론적 구멍)**: 가격 누수보다 펀더멘털 누수가 가치전략엔 더 치명적이다. pykrx·FinanceDataReader는 **현재 시점의 재작성된(restated) 재무**를 주므로 point-in-time이 아니다. Phase 3 내재가치 백테스트가 "발표 전 실적을 이미 알고" 매수하는 누수가 생긴다. 재무는 **filing timestamp(발표시점)**로 정렬해야지 회계기간 종료일이 아니다. → as-reported 스냅샷 소스 또는 announcement-date 정렬 레이어를 **Phase 4 데이터 작업에 명시**(FDR/pykrx가 PIT 미제공임을 전제).
- **생존편향 + 상장폐지(#1과 짝)**: 백테스트 유니버스에 상장폐지 종목이 없으면 0으로 간 진짜 value-trap이 빠져 가치전략이 인위적으로 좋아 보인다. Phase 3 검증 유니버스는 **반드시 delisted 종목 포함**.

### H6. 비밀키/권한 (Phase 0/4)
*(교차검증 정정)* "평문 service_role"이 아니라 **역할분리 키모델**이 이미 있다 — `.env.owner`=service_role / `.env.collaborator`·`.env.coworker`=anon+WORKER_TOKEN, 커밋된 `.env.*`는 플레이스홀더 템플릿(실제 `.env`는 gitignore). 잔여 갭은 두 가지로 좁혀진다:
- service_role 키의 광범위 권한 → 읽기/쓰기 분리, 가능하면 OS keyring/vault.
- **출금권한 미부여가 문서화만 되어 코드 강제가 아님** → 시작 시 거래소 키의 withdraw 스코프를 조회해 부여돼 있으면 경고/중단(`sys.exit`).

### H7. 통합 관측가능성 (Phase 6)
sharpe/mdd/win_rate가 RL 맥락에만 산재. 라이브 포트폴리오 차원 통합 대시보드가 없다.
- 트랙 통합 P&L·MDD·Sharpe·회전율·LLM 호출수/비용을 한 대시보드 + 텔레그램 일일요약에. yakub268 Flask 대시보드 참고.
- **에스컬레이션 매트릭스(Round 2 Gemini)**: 정보성 알림과 치명적 알림(kill switch 발동·연속 실패·reconciliation 불일치)을 분리. 치명 알림은 단순 텔레그램을 넘어 재알림/2차 채널(SMS 등) 에스컬레이션 — 관리자가 놓쳐 복구 지연되는 것 방지.

### H9. 주문 멱등성 / exactly-once (Phase 4, 치명적) — 교차참조: nautilus_trader
`execute_trade.py`의 uuid는 Upbit 인증 nonce용일 뿐, **클라이언트 주문 ID 기반 dedup이 없다**. 타임아웃 후 재시도 시 이중주문 위험(코인·KIS 공통).
- nautilus_trader의 결정적 주문 상태머신 차용: client_order_id 부여 → 제출 전 미체결/체결 조회 → 멱등 재시도. 동일 client_order_id 재제출 금지.
- 판정: 주문 직후 응답 유실을 인위 주입 → 재시도해도 **주문이 1건만** 남는지.

### H10. 모델/프롬프트 버전·결정성 (Phase 1) — 교차참조: TradingAgents model catalog
`llm_worker`/`config`에 temperature·seed·model_id·prompt_version 고정이 없다 → 모델/버전 변경 시 같은 입력에 다른 결정 → 감사·재현 불가.
- temperature=0(또는 고정 seed), model snapshot ID, strategy.md/프롬프트 해시를 **모든 결정 레코드에 기록**. Qwen·Claude 버전을 명시 카탈로그로 관리.
- 판정: 동일 입력 N회 반복 시 결정 동일(결정성), 모델 교체 시 레코드에 버전 차이가 남는지.

### H11. 데이터 staleness / 소스 quorum (Phase 4) — 교차참조: OpenBB 멀티소스
타임아웃 처리는 있으나 "신선하지 않거나 N개 소스가 죽었을 때 매매 거부/감점" 규칙이 없다.
- 각 데이터에 timestamp + 신선도 임계. 핵심 소스 quorum(예: ≥70% 신선) 미달 시 강제 관망. NewsRang Data Fusion에 소스 가용성 가중 반영.
- 판정: 소스 절반을 인위 차단 → 매매가 관망으로 전환되는지.

### H12. 레짐 라벨 정확도 / hysteresis (Phase 0/6) — 교차참조: yakub268·AgenticTrading HMM
bull/early_bull/sideways/bear/crisis가 매수차단·임계를 좌우하나, 룰 경계에서 레짐 flapping → 에이전트 진동 위험.
- 확률 기반 레짐(HMM) 또는 최소 전환 쿨다운·확률 임계·hysteresis 도입. (기존 D의 Sharpe-drop 자동 롤백은 **보존**.)
- 판정: 경계 구간 데이터 재생 시 레짐 전환 횟수가 임계 이하(진동 억제)인지.

### H13. 동시성 / 분산락 정합성 (Phase 0/2) — Round 1 신규 발견
동시성 원시기능이 `data/trading.lock` 파일락뿐. ZMQ 멀티프로세스 + `utils/machine.py` 멀티머신 + 공유 Supabase 상태 환경에서 락파일·상태 경합 위험. 멱등성(H9)과 짝을 이룬다.
- 분산락(예: Supabase advisory lock/행 잠금) 또는 낙관적 동시성(version 컬럼) 도입. 멀티머신에서 동일 주문이 두 머신에서 나가지 않도록 H9와 통합.
- 판정: 두 워커/머신에서 동시 주문 트리거를 인위 주입 → 주문이 1건만 나가는지.

### H14. LLM 서킷브레이커 + 지연예산 (Phase 1) — Round 1 신규 발견
"트리거 시에만 Claude" 라우팅에 호출량 상한·지연 상한이 없으면, 급변 이벤트(flash crash)에서 트리거 연발 → Claude 호출 폭주(비용·지연 blowup) → 정작 의사결정이 늦어 손실.
- 일일 Claude 호출 캡 + 초과 시 **degrade-to-Qwen** 폴백. 결정당 **최대 허용 지연(예: 3초)** 예산 초과 시 즉시 휴리스틱(기본 룰) 매도/관망으로 fallback.
- 추가(D2 연계): NewsRang 소스 신뢰도 1차 스코어링으로 뉴스 오분류발 거짓 트리거 차단.
- **C2 × Phase 3 충돌 해소(Round 3 #3 — 미해결 상호작용)**: 종목 급락(=트리거 시점)은 대개 시장 전체 이벤트라 트리거가 동시다발 → degrade-to-Qwen 발동 → 그런데 2단 게이트의 핵심은 *heavy agent(Claude)*가 thesis붕괴 vs 일시패닉을 가르는 것. 판단이 가장 중요한 순간에 약한 모델로 강등되는 모순. → **정책 분리: 모니터링은 Qwen 강등 OK, 그러나 매수 결정은 강등 시 abstain(매수 금지)**. 즉 heavy agent 불가용 시 신규 매수 후보 생성 안 함.
- 판정: 트리거 폭주를 인위 주입 → 호출 캡 발동 + Qwen 폴백, 지연 초과 시 휴리스틱 경로로 빠지는지.

### H15. 스마트 주문 집행 / Order Type 최적화 (Phase 4) — Round 2 신규 발견
H1은 슬리피지를 "비용"으로만 다루나, 실제로 호가창이 얇은(thin orderbook) 자산에 시장가로 진입하면 막대한 체결 손실이 난다(특히 주식 소형주·일부 코인).
- 지정가(limit) 기반 **Post-Only / FOK / IOC**를 기본 집행 방식으로, n분 내 미체결 시 호가 정정(order modification)하는 스마트 집행 로직을 Exec 레이어에 명시. E3(부분체결)와 통합.
- 판정: 얇은 호가 시나리오 재생 시 시장가 대비 체결 손실이 한도 내인지.

### H16. 기업행위(Corporate Actions) 처리 (Phase 3/4) — Round 3 신규 (주식 필수)
액면분할·배당락·합병·유상증자·상장폐지 미처리 시 분할이 -50% "급락"으로 보여 **거짓 트리거 + reconciliation 오류**. 주식 트랙 필수인데 어디에도 없었다.
- 수정주가(adjusted price) + 기업행위 이벤트 캘린더로 가격·수량 보정. 상장폐지는 H5 생존편향과 연결.

### H17. 가격제한폭 / 거래정지 (Phase 4/5) — Round 3 신규
한국 ±30% 상·하한가, 거래정지는 슬리피지·집행과 직결. **하한가 잠김(limit-down lock)이면 매도 체결 자체가 불가**. H1/H15는 호가깊이만 다룬다.
- 백테스트 슬리피지 모델 + 라이브 집행 모두 **"팔 수 없는 상태"**를 표현. 거래정지·상하한가 플래그를 데이터·게이트에 반영.

### H18. US 주식 FX를 1급 리스크로 (Phase 4/6) — Round 3 신규
KIS 해외주식은 USD 결제 → **KRW/USD 변동이 US 주식 P&L을 압도**할 수 있다(§5는 환전수수료=비용만 언급). Portfolio Orchestrator에서 **FX를 상관·리스크 입력**으로(원화 강세장에선 명목수익이 환손실로 상쇄). + US 장시간(KST 야간)×상시 모니터링 상호작용(pre/post market, KIS 해외주문 처리) 설계.

### H19. 코인 집행 현실성 — shadow-live (Phase -1/5) — Round 3 신규
**Upbit는 테스트넷이 없다.** 코인 DRY_RUN이 순수 내부 시뮬이면 90일 무중단은 uptime만 증명하지 *집행 현실성(슬리피지·부분체결·레이턴시)*은 증명 못 한다(§2.9 패리티가 코인에선 미성립). → Binance testnet 또는 **shadow-live**(주문을 계산만 하고 실시장 호가에 대조) 모드를 별도로. + kimchirang **funding cost**(Binance 무기한 숏 펀딩비)를 델타뉴트럴 P&L에 반영.

### H20. 운영 연속성 — 수동이관·글로벌 limiter (Phase 4/6) — Round 3 신규 (Gemini)
- **수동 reconciliation 플로우**: API 전면 장애(KIS/업비트 수시간 정지) 시 시스템은 관망·종료 상태 유지, 사용자가 HTS로 수동 청산한 내역을 재기동 시 내부 DB에 동기화하는 워크플로우(O3 확장).
- **글로벌 rate-limit 큐 동기화**: H4 limiter를 ZMQ 멀티프로세스(main_brain·workers)가 공유하려면 Redis 백엔드 또는 중앙 큐로 구체화(C1 분산락과 연계).

### H21. 생성단계 스키마 강제 — constrained decoding (Phase 1) — Round 3 개선
B1을 "validate-then-reject"로만 두지 말 것. 로컬 Qwen은 **constrained decoding(Outlines / llama.cpp GBNF / Ollama `format=json`+schema)으로 생성 단계에서 스키마 준수를 강제**하는 게 strictly 낫다(깨진 JSON이 애초에 안 나옴). post-hoc jsonschema(H3)는 2차 방어로만.

### H22. LLM 백테스트 오염 — training-data lookahead + 재현불가 (Phase 5, 치명·최우선) — Round 4 신규
**4라운드 통틀어 백테스트 유효성에 대한 가장 깊은 발견.** 결정의 일부가 LLM(Claude/Qwen)인 한 Phase 5 패리티("백테스트=라이브 동일신호 ≥95%")는 LLM 레이어에서 **원리적으로 성립하지 않는다**:
- *Training-data lookahead*: LLM은 2022 Terra/LUNA·FTX 붕괴 결과를 **이미 안다**. 과거 시점에 "매수냐" 물으면 파라메트릭 메모리의 미래정보는 prompt를 PIT로 마스킹해도 안 지워진다. Phase 3의 thesis붕괴 판정이 정확히 이 오염에 가장 취약.
- *Non-replayability*: 2018~현재 LLM 호출을 결정적·저비용으로 재생 불가(H10 결정성은 동일입력 반복 보장일 뿐, 과거 모델 스냅샷 재생이 아님).
- → **백테스트 2층 분리**: (a) 기계적 score 레이어(`calculate_buy_score`·멀티플 밴드·레짐)는 정상 백테스트, (b) LLM 판단 레이어는 백테스트에서 **제외하거나 보수적 stub**(heavy agent 불가 시 abstain과 동일 처리). **Phase 5 패리티 기준을 "기계적 레이어 ≥95% + LLM 레이어는 패리티 측정 대상에서 명시적 제외"로 재정의**. 안 하면 백테스트 Sharpe가 LLM 후견지명으로 부풀어 실전 게이트를 조용히 통과시킨다.

### H23. 다중검정 / 백테스트 과적합 확률 (Phase 5) — Round 4 신규
H5는 walk-forward·생존편향까지 갔으나 **몇 개 전략·파라미터를 시도했는가** 보정이 없다. 4계열(kimchirang/scalp_ml/altrang/value)×튜닝 = effective trials 수십~수백 → 그중 하나가 "OOS Sharpe 좋음"으로 통과하는 건 우연일 확률이 높다.
- **Deflated Sharpe Ratio** 또는 **PBO(Probability of Backtest Overfitting, Bailey/López de Prado)**를 Phase 5 수용기준에 추가. 시도한 조합 수를 결정 레코드(H10)에 trial-count로 로깅해 Sharpe를 deflate. skfolio combinatorial purged CV로 PBO 산출.

### H24. kimchirang 교차거래소 viability — 규제·이관·청산 (Phase -1/4, 웹검증) — Round 4 신규
**코드 이전의 결정.** Binance 앱은 2026년부터 한국 차단(앱스토어 제거)·FSC 미등록·KRW 온램프 없음, 트래블룰 전면 적용(명의일치 필수). H2의 leg-reconciliation은 *체결 후*만 본다. 빠진 것:
- *인벤토리/이관 마찰*: Upbit(KRW)↔Binance(USDT) 즉시 리밸런싱 불가 → 델타뉴트럴 드리프트를 빠르게 못 맞춤.
- *숏 레그 청산 cascade*: BTC 급등 시 Binance 무기한 숏 청산 가능한데 Upbit 담보를 제때 못 넘김 → **포지션 소멸 리스크**(H19 funding은 P&L 항목일 뿐).
- → **결정(이 세션에서 확정): kimchirang을 research/shadow-only로 강등.** 근거: 규제 궤적 적대적·악화(Binance 한국 차단·FSC 역외거래소 차단 추진), 실행 viability 구조적 취약(이관 마찰·청산 cascade), BTC 단일 수렴 시스템에서 델타뉴트럴은 사이드 전략인데 MarketNeutral 아키타입+교차거래소 정합성 전체를 떠안는 비용 과다. 강등 시 Directional/HFT 2계열만 남아 Phase 범위 경감. **재진입 조건(둘 다 충족)**: (i) 합법·실무 자금이동 경로 확보 (ii) leg-unwind·숏레그 마진버퍼·이관 리드타임 구현 + shadow-live 검증. → §6 hard rule로 고정.

### H25. 상관 추정 불안정성 / tail co-movement (Phase 2/6) — Round 4 신규
`corr>0.7 중복진입 차단`·상관기반 배분은 *상관 안정* 가정인데 **상관은 위기에 1로 수렴** → 캡이 가장 필요한 순간(플래시크래시)에 무력. trailing window 0.7은 평시 분산 과대·위기 과소평가.
- Ledoit-Wolf shrinkage + **tail(하방) 상관을 별도 입력**(평시 상관과 분리). 최소한 "상관 캡은 평시 가정, crisis 레짐(H12)에선 무력"임을 게이트에 명시.

### H26. 포트폴리오 numeraire / FX 재평가 타이밍 (Phase 6) — Round 4 신규
멀티에셋(Upbit KRW코인/Binance USDT코인/KR주식 KRW/US주식 USD)에서 통합 MDD·Sharpe·kill switch를 **어떤 기준통화·어느 시점 FX로** 계산하는지 미정의 → FX 노이즈로 kill switch 오발 가능.
- 단일 numeraire(KRW 권장) + FX 스냅샷 타이밍 고정(H1 단일 UTC와 정합) + kill switch 입력에서 FX 변동분 분리 옵션.

### H27. halt-then-confirm의 무인 footgun (Phase 2 × H18) — Round 4 신규 (R3 수정 보완)
R3의 "MDD 임계 → halt + 사람 컨펌 전 청산 보류"는 옳으나, **US장=KST 야간**에 사람이 자는 동안 손실 누적되는 *역footgun*. → **bounded auto-fallback**: 컨펌이 N시간 내 없고 손실이 2차 임계 초과 시 자동 *시간분산 축소*(전량 아님). "불가피 시 단계적"을 무인 시나리오에 명시적으로 트리거.

### H28. 전략 capacity / 시장충격 (Phase 5/6) — Round 4 신규 (간단)
H15는 *주문당* 슬리피지를 다루나 *전략당 capacity*(자기 충격으로 엣지를 죽이기 전 흡수 가능 자본)는 없다. 한국 소형주·얇은 알트에 실재. → Portfolio Orchestrator 트랙별 한도에 capacity 상한 입력.

---

## 6. 비협상 안전 규칙 (전 Phase 공통)

1. 실자금 전환 전 전 트랙 DRY_RUN 최소 2주 + 모의투자(KIS) 통과 의무.
2. LLM은 "후보 제안"만. 매매 실행 권한은 risk_gate 통과분만, 별도 격리 프로세스.
3. 수동 EMERGENCY_STOP은 코드/에이전트가 절대 해제 불가.
4. risk_gate 규칙은 LLM이 호출하는 함수가 아니라 그 위의 inviolable wrapper.
5. 모든 거절/near-miss/실패는 감사 테이블에 기록(기존 패턴 유지).
6. 초기 실자금은 잃어도 되는 극소액부터.
7. **kimchirang(Binance 숏 레그)은 research/shadow-only.** 위 H24 재진입 조건 둘 다 충족 전까지 실자금 양다리 집행 금지.

---

## 7. 기존 규약 준수 (스타일)

- 자연어 전략 파일(strategy*.md)의 점수표 포맷 유지.
- 결정은 `prompts/schemas/decision_result.json` 스키마 확장(주식용 `valuation_gap`, `intrinsic_value` 필드 추가).
- Supabase 마이그레이션은 번호 순차(`051_`부터), 트랙 컬럼(`asset_track`) 추가.
- 텔레그램 알림 포맷·자가치유·file locking 패턴 유지.
- 점수 breakdown 투명성(감사 가능) 전 트랙 유지.

---

## 8. 첫 작업 지시 (Claude Code에게)

> "Phase 0부터 시작하라. 먼저 `core/asset_track.py`의 `AssetTrack` ABC를 설계하고, 기존 `agents/`·`rl_hybrid/`의 코인 로직을 시그니처·동작 변경 없이 `CoinTrack`으로 래핑하라. 기존 코인 DRY_RUN 동작이 래핑 전후 동일함을 보이는 회귀 테스트를 `tests/`에 추가하라. 완료 후 diff와 테스트 결과를 보고하고 Phase 1 진행 승인을 받아라. 각 Phase는 §6 안전 규칙을 위반하지 않는다."