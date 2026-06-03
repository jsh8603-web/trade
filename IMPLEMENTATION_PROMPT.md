# 통합 투자 시스템 구현 프롬프트 (for Claude Code, 로컬) — Round 10 최종본

> 이 문서를 `jsh8603-web/coin` 리포 루트에서 Claude Code에 전달하여 단계적으로 구현한다.
> 기존 코인 시스템을 맹목 보존하지 말고(**ref-우월 시 교체**, §0.3 B표·§2 coin 변형표), asset-agnostic 코어로 **일반화**한 뒤 coin은 Phase R에서 특성 변형 이식한다.
>
> 🔑 **구현 보완 companion = [`implementation-keys.md`](./implementation-keys.md)** (2026-05-28, 7-에이전트 종합). 본 설계 대비 **정정 14건**(§8)·도메인별 wire·코드위치·reuse-github 매핑·작성된 brain 코드(`stock/`·`core/brain/`) 보유. **본 문서와 충돌 시 implementation-keys.md 가 우선**(최신 검증). plan/progress/harness2 는 두 문서를 함께 참조.

---

## ★ Round 10 변경 요약 (최종 — 착수 전 필독)
R9(Gemini Top 5)에 더해 R10에서 반영: **① §4.2 고-스테이크스 consensus 게이트(안 "다")** — 평상시 blend, 고-스테이크스(레짐flip·배분변경·누적 x%)에만 다관점 토론(TradingAgents 어댑트, 코인 렌즈=on-chain/FGI/funding/technical), risk_gate 항상-on 백스톱, 게이팅 역효과 6 완화. **② Phase 재구조** — coin-외 일반 버전 먼저 빌드·검증 → **Phase R에서 coin 특성 변형 이식 + DRY_RUN 패리티**(coin 안전 하드닝 Phase -1만 선행). coin 변형표·교체 우선순위(백테스트 엔진>사이징>메모리>집행) 명시. **③ §2.9 게이트 재검증** — 전 게이트가 *코드 완성*이 아닌 *동작(does-it-run/behave)* 기준임을 재확인 + consensus·Phase R 동작 게이트 신설. 임계값은 튜닝값. **이번 라운드를 최종으로 본다 — 남은 미검증 항목은 문서 말미 "닫기 전 미검증 목록" 참조(구현 직전 확인).**

---

## ★ Round 9 변경 요약 (Gemini 교차검토 Top 5 통합 — 착수 전 필독)

Round 8(전면 재작성, ref 웹확인)에 더해, Round 9는 **Gemini의 S1~S12 워크스루 검토에서 나온 계약 끊김 Top 5**를 반영했다. 5건 모두 *운영에서 실제로 깨지는* 계약 갭이며 본문에 명문화했다.

1. **[S10] 미청산(open) 포지션 중간 귀속 부재** — G3이 closed 거래만 입력받아, 느리게 출혈하는 value trap·레짐 오판이 *청산 전까지 학습 루프에 안 들어감*. → **신규 G9**: 보유 N일 경과 또는 고점 대비 M% 하락한 미청산 포지션도 mark-to-market 귀속(§5.8-G③ 실현수익 에스컬레이션과 명시 연결).
2. **[S8] 미체결 주문발 가짜 drift** — 지정가 in-flight 시 다음 사이클 R2가 DB-거래소 불일치를 drift로 오인해 halt. → **R2 계약**: 거래소 open-orders의 잠긴(locked) 자산을 합산해 drift 계산, 미체결 묶임은 drift에서 제외(§0.6-B·H2).
3. **[S6] 세금통산 YTD 입력 누락** — 해외 22% tax-loss harvesting을 S6가 판별하려면 YTD 실현손익·tax lots가 입력이어야 하나 현재 입력은 현 포트폴리오+제안 결정뿐. → **S6 입력계약에 `ytd_realized_pnl`·`tax_lots_status` 주입**(§6·G7·§5).
4. **[S1~S7] 밴드 drift 감시 주체 불분명** — G7 밴드이탈 트리거를 누가 매 사이클 감시하는지 모호. → **Portfolio Orchestrator가 `recommended_next_check()`와 독립적으로 매 사이클 최우선 Drift Monitor 실행**(Phase 6·G7).
5. **[S2·S6] 야간 FX stale → 가짜 MDD/kill-switch** — KST 야간(US장중) 환율 미갱신·스프레드 확대로 H26 통합 MDD 왜곡→오발. → **H26**: 야간 US장은 직전 정규장 마감 고정환율(또는 NDF 역외환율) 사용.

> 메타(R7→R8→R9): "요약 신뢰 → phantom" 교훈이 누적 확인됨(R7 phantom 테이블, R8 history_rhymes=논문/forecasting=노트북/AgenticTrading 귀속종류). ref 차용은 **착수 직전 repo/논문을 직접 열어 입출력 계약 확인 후** 어댑트. **ROI 판단(본 문서 작성자)**: 코드근거 축(E2/R2/B1/B3)은 R4에 수렴, 끊김 계약은 R8·R9에 수렴 → **추가 광범위 리뷰 ROI 낮음.** 남은 진짜 불확실성(엣지 유무·학습루프 효과·계약의 부하내성)은 *더 읽어서가 아니라 Phase -1 구현 + §2.9 결함주입 + 모의로만* 검증됨. → **권고: 리뷰 종료, Phase -1 착수.** 단 G3 귀속종류(ⓐ factor vs ⓑ alpha/risk/cost) 결정과 BL regime→% 경로는 신규성이 높아, *구현 직전 1회 좁은 확인*은 가치 있음.

---

# ■ 교차모델 검토 의뢰 — 파이프라인 완전성 (Claude / Gemini 공통)

## 검토 프레이밍 (먼저 읽을 것 — 검토 범위 한정)
- **운영 경로는 검토 대상 아님(합의 완료)**: 과거데이터 수익률 백테스트 → 약 2주 모의(paper) → 소액 실전 점증. 이 단계화는 사용자와 이미 합의됐다. *"실전 가도 되나"류 전략 처방은 불필요.*
- **"coin repo에 있나 없나"는 검토 대상 아님**: 현 `coin` repo(v1.35.2)는 구현된 게 극소수다(단일 BTC). 본 로드맵은 **대부분 신규 구축**이다. 검토 대상은 *기존 구현 유무*가 아니라 **신규 구축 로드맵의 완전성·타당성**.
- **검토 단위 = end-to-end 파이프라인이 단계 간 끊김 없이 연결되는가.** 한 단계의 출력이 다음 단계의 입력으로 계약(contract)이 맞물리는지가 핵심.

## 검토 축 — 파이프라인 12단계 (각 단계: 입력계약 → 처리 → 출력계약)
> S(N) 출력 = S(N+1) 입력. 각 단계는 **[목표]**(실제 운영 결과 — 코드 유무 아님)와 처리·계약을 가진다. 차용 §0.3·§0.4, 배선 §0.6, 끊김 보완 §0.7, 세부 25축 하단.

- **S1 데이터 수집** — 거시(FRED-MD)·시장(KIS 주식/Upbit 코인)·뉴스/리포트. PIT·freshness·quorum(D1·D2·H11·H30·H31). → 출력: PIT-clean 피처+가격.
  **[목표]** 결정 시점에 *실제로 알 수 있었던* 데이터로만 판단, 소스 죽으면 stale 매매 안 하고 관망(미래누수 0).
- **S2 거시/레짐 추론** — HMM/WKM 분류 + 선행예측 → `macro_view`(status fresh/stale/unavailable, **per-bloc**). (§5.8-A) [classifier(현재)≠forecaster(선행) 필드 분리.]
  **[목표]** 현 거시국면을 *행동 가능할 만큼 일찍* 식별, 모르면 솔직히 unavailable.
- **S3 top-down 배분** — 레짐 → 슬리브 %. Investment Clock + **Black-Litterman(Prior=IC표)**. (§5.8-B·D) [regime→% BL 단일화. 밴드 drift 감시 = Portfolio Orchestrator 소유(R9·G7).]
  **[목표]** 자본이 국면에 맞는 자산군으로 *실제로* 이동하되 리스크 한도 내, 불필요한 회전 없이.
- **S4 종목 선정(bottom-up)** — 슬리브 내 ETF/종목/코인. value 2-gate(DCF+멀티플)+지표. (§5.7)
  **[목표]** 관점을 실제로 표현하면서 *거래 가능(유동성)* 종목 선정, value trap 회피.
- **S5 결정 융합** — agent+RL+LLM blend → 종목별 방향·크기. (allocation-aware, downgrade-ratchet 차단)
  **[목표]** 모순 없는 *하나의* 실행 가능 결정(배분 목표 vs 종목 신호 충돌 해소).
- **S6 리스크 게이트** — EMERGENCY_STOP·상관캡·사이징(Kelly+Ledoit-Wolf)·세금인지 + precedence 격자. 우회불가. (§6·R1·R3·P1) **[R9 입력계약: 현 포트폴리오+제안결정 + `ytd_realized_pnl`·`tax_lots_status`(세금통산용).]**
  **[목표]** 계좌 파산 주문은 *절대* 통과 못 함 — 캡이 실제 구속, LLM 우회 불가.
- **S7 집행** — 멱등 주문(E2)·스마트주문 modify/cancel/pending(H15·E3·pykis)·레이트리밋(E1)·멀티거래소. (§0.6-B)
  **[목표]** 의도한 거래가 *정확히 한 번* 수용가능 비용으로 체결되거나 안전 실패(이중체결·미인지 미체결 0).
- **S8 reconciliation** — 거래소↔DB 대조(R2, fee-net day-1, **R9: 미체결 locked 잔량 제외**)·양다리 leg(M2). drift→halt. (§0.6-B)
  **[목표]** 믿는 보유상태 = *항상* 거래소 실상태, drift 즉시 포착·정지. **단 미체결로 묶인 잔량은 가짜 drift로 오인 안 함.**
- **S9 기록** — `decisions`+`trade_reviews`(outcome)+attribution + ablation-config 플래그. (§0.6-A·C)
  **[목표]** 모든 결정·결과가 *학습 가능할 만큼 정직하게* 기록(재현·귀속 가능, 누락/중복 0).
- **S10 학습 루프** — 사후 귀속(factor 또는 alpha/risk/cost)→RAG 메모리(PIT)→결정 시 recall→RL 재훈련. (§5.9·§0.6-A) **[R9: closed뿐 아니라 open 포지션 mark-to-market 중간 귀속(G9).]**
  **[목표]** 시간이 지나며 *실제로 개선*되거나 귀속 가능한 실수를 반복 안 하고, *틀린 교훈* 학습 안 함. **진행 중 오판도 청산 전에 경고.**
- **S11 백테스트/검증** — 슬리피지+라이브 캘리브레이션(H1·E4)·walk-forward/PBO(H23)·GO/NO-GO·LLM 오염통제(H22). 2018~.
  **[목표]** 비용차감 후 엣지 유무를 *정직하게* 추정(과적합 통제), 모의→실전에 의미 있는 GO/NO-GO.
- **S12 운영/안전** — 대시보드(O1·G8)·서킷브레이커(C2)·kill switch·bus-factor(H32)·prompt-injection(H33)·키스코핑(S1).
  **[목표]** 무인 안전 가동, 고장 시 fail-safe + 알림, 운영자 부재에도 생존. *사용자는 백테스트·모의·실전을 동일 포맷 뷰(G8)로 본다.*

## 4대 검토 요청 (순서 = 우선순위) — 다음 라운드용
1. **시뮬레이션(최우선)**: S1~S12 실제 데이터 흐름 워크스루로 (a) 단계 간 끊김·미정의 계약, (b) 각 단계 [목표] 달성 여부. **R8/R9가 메운 항목(G1~G9·per-bloc·BL·precedence·recall A/B·open귀속·pending drift·YTD세금·drift monitor·FX night)의 잔여 결함**을 특히.
2. **핵심 코드의 ref repo 구현 여부**: §0.3·§0.4 차용 실재(파일/모듈). R8 정정(history_rhymes=논문, forecasting=노트북, MMR/AgenticTrading 계약불일치) 정확성 재확인.
3. **배선 정합성(§0.6)**: 명시 파일·함수·라인(coin v1.35.2)·핸드오프 계약 일관성.
4. **추가 구현 필요 여부**: 12단계 [목표] 완전성 누락. 있다면 정말 ref repo에 없는 신규인지.

**출력 포맷(단계별):**
```
[Sx] 목표달성: 충분/부분/불충분  ·  연결: 완결/끊김/미정의계약
끊긴 계약: (출력→입력 어디가 안 맞나)   |   목표 미달 사유: (운영에서 무엇이 안 되나)
보완: (무엇을, 어디에)
ref 차용: (해당 단계 repo/파일 — 실재 확인 결과)
```
마지막에 **끊김/목표미달 Top 5**(치명도×완전성영향)와 **누락 단계/계약 추가**.

---

## (참고) 세부 점검 체크리스트 — 8 레이어 × 25 축

**Data** — D1 무결성/no-lookahead · D2 staleness/소스 quorum(+신뢰도 스코어링)
**Brain** — B1 구조화출력 · B2 차원 일관성 · B3 버전·결정성 · B4 감사/설명가능성
**Risk** — R1 사전게이트/kill switch · R2 reconciliation · R3 포지션사이징
**Exec** — E1 레이트리밋 · E2 멱등성/exactly-once · E3 부분체결
**Learning** — L1 과적합/walk-forward · L2 온라인학습 안정성 · L3 레짐 hysteresis · L4 reward hacking
**Ops** — O1 관측가능성 · O2 self-healing/uptime · O3 DR/상태영속성
**Security** — S1 키 스코핑 · S2 감사추적
**Portfolio** — P1 배분/상관/분산 · P2 세금/수수료
**Cross-cutting** — C1 동시성/분산락 · C2 LLM 서킷브레이커+지연예산 · C3 필수입력 producer liveness 디커플(H29)

> 채점 가이드: **강점(코드 확인)** L2(Sharpe-drop 롤백)·B4·S2(감사)·R1(EMERGENCY_STOP orchestrator.py:179)·O2(file lock)·L4(reward clip). **확정 미구현(치명, Phase -1)** E2(`identifier` 미전송)·R2(0건)·B1(강제 0건). **확정 약함** B3(temp=0.3, 0비용 quick win)·D2·L3·E1·E3·L1. **R7 phantom 정정** `decision_aftermath`·`near_miss_veto` 미존재, outcome=`trade_reviews`(미배선), `continuous_learner`=RL. **R8 ref 정정** history_rhymes=논문, forecasting=노트북, MMR 입력=HMM states, AgenticTrading=alpha/risk/cost. **수렴 판정** 코드근거 축 완전수렴 → Phase -1 즉시. 진짜 게이트 = §2.9 fault-injection.

## 참고 GitHub/논문 목록 (확인 상태)

평가 대상: https://github.com/jsh8603-web/coin
- TradingAgents: https://github.com/TauricResearch/TradingAgents
- ai-hedge-fund (Damodaran·Druckenmiller·Valuation — ✅확인): https://github.com/virattt/ai-hedge-fund
- dexter (자가검증): https://github.com/virattt/dexter
- AlpacaTradingAgent (Macro Analyst·quick/deep·Qwen/Ollama/Claude — ✅확인): https://github.com/huygiatrng/AlpacaTradingAgent
- python-kis/pykis (modify/cancel/pending·websocket·모의투자 — ✅확인): https://github.com/Soju06/python-kis · 공식: https://github.com/koreainvestment/open-trading-api
- AgenticTrading (귀속=**alpha/risk/cost**, *beta/sector/idio 아님*): https://github.com/Open-Finance-Lab/AgenticTrading
- yakub268/algo-trading-platform (대시보드·Thompson·HMM·GO/NO-GO): https://github.com/yakub268/algo-trading-platform
- 메모리·reflection: FinMem(2311.13743)·FinAgent(2402.18485)·TradingGPT(2309.03736)·TradingGroup(2508.17565)
- **History Rhymes (PIT causal-mask — 논문, repo 아님)**: arXiv 2511.09754 (Sarthak Khanna et al.)
- LLM 백테스트 오염(H22): Glasserman&Lin 2023(2309.17322)·2602.14233·ScienceDirect 2025·MemGuard-Alpha(2603.26797, 수치 저신뢰)·unlearning(2512.06607)
- Riskfolio-Lib · skfolio(PBO·purged CV) · PyPortfolioOpt(BL) · nautilus_trader · OpenBB · polymarket-bot · **MlFinLab(Hudson&Thames — 메타라벨링·triple-barrier, §5.8-H 신호/레짐 오판 학습)** · **jumpmodels(Apache-2.0 — JM/SJM 레짐 식별, sparse·robust, §5.8-A)** · **FRED-MD/FRED-QD(McCracken-Ng, 1959+ 거시 빅데이터, 분류기 장기훈련)**
- MarketMoodRing (HMM/WKM + portfolio_optimization — ✅실재, 입력=HMM states+수익률): https://github.com/yvesdhondt/MarketMoodRing
- forecasting-economic-and-market-regimes (FRED-MD+NBER+ℓ1-trend — ✅실재, 노트북): https://github.com/ARahimiQuant/forecasting-economic-and-market-regimes
- KIS: koreainvestment/open-trading-api · Soju06/python-kis · sharebook-kr/pykrx · FinanceData/FinanceDataReader

---

## 0. 컨텍스트 (현재 자산 = 절대 무시 금지)

기존 `coin` 리포(v1.35.2, Python 93%)는 단일자산(BTC) 자동매매의 **검증된 레퍼런스**다. 아래를 **재사용·일반화**한다. 새로 만들지 말 것:
- `agents/base_agent.py` — `calculate_buy_score()`·`kelly_position_size()`·`detect_regime()`·레짐별 적응형 청산·이중 스톱(-5%/-10%)
- `agents/orchestrator.py` — danger/opportunity(0~100)·3계급 자율전환·`warmup_threshold`·file lock·`_get_performance_adjustment`
- `agents/external_data.py` (NewsRang) — 11소스 병렬 + Data Fusion
- `rl_hybrid/` — ZMQ 버스·PPO·`decision_blender`·RAG 자기기억
- `prompts/schemas/decision_result.json` · `strategy.md`
- `supabase/migrations/` **48개** — `decisions`·`buy_score_detail`·`signal_attempt_log`·`execution_logs` 실재·사용중. `trade_reviews`(mig 3, code 0) **완비·미배선**(+`v_trade_history`). `execution_failures`(mig 1, code 0) 미사용. **`decision_aftermath`·`near_miss_veto` 실존X(phantom).**
- 안전: `DRY_RUN`·`EMERGENCY_STOP`(해제 불가)·Lifeline·텔레그램. 뷰: `scripts/dashboard.py`(Flask)·`web/index.html`(단일 BTC).

**핵심 보존 원칙(6)**: 점수 투명성·자연어 전략·JSON 결정 스키마·감사 테이블·DRY_RUN 게이팅·수동 EMERGENCY_STOP 우회 불가.

---

## 0.1 Round 6 검토 결과 — 선별 반영
**받아들임**: KIS 약관·세무 웹검증(H32)·bus-factor(H32)·M5 rate-tier(H30)·M6 휴장일(H31).
**보류·완화**: 엣지 prior=하드블로커 아님(병행 추적) · 전체 구현 유효 · "LLM/매크로=beta" 미입증(§5.8/직교성 측정).

## 0.2 현재 코드 결정/학습 루프 배선 실태 (v1.35.2 — `live_trader.run_cycle` 7단계)
- **결정 입력**: ✅ `calculate_buy_score` + DXY·US10Y·funding 융합(단일자산).
- **학습→결정 2개(얕음)**: ⓐ `_get_performance_adjustment()`(연패3→danger+15/연승3+승률60→opp+10, 귀속 아님). ⓑ RAG `analyze_and_store`만, **`query_similar`(recall) 라이브 미호출** + LLM에 `external_data={}` 빈 거시.
- **outcome 기록/귀속**: ❌ `trade_reviews` writer 0(죽음). outcome=`decisions.profit_loss`만.
- **학습 루프**: 가격패턴 RL ✅ 닫힘. *귀속형 reflection* ❌ 미배선.
- **E2**: ⚠️ `check_open_orders_and_cancel`(대기주문 취소)는 있으나 `identifier` 없음 → 체결후 응답유실 이중체결.
- **기록 분산**: `_save_and_notify`=텔레그램만. **안전장치**: ✅ 강제. **거시→비중**: ❌ 미존재.
→ 보완: 1) trade_reviews 라이터 2) RAG recall+실거시 3) E2 identifier+R2(Phase -1) 4) 거시→배분.

## 0.3 재사용 소스 매핑 (재코딩 금지)
**A. 코인 repo 내부**: `calculate_buy_score`·`_get_performance_adjustment`·`external_data`(+`collect_macro.py`)·기록(`decisions`·`buy_score_detail`·`execution_logs`·`signal_attempt_log`, 함수 `execute_trade.py::_record_trade_to_db`)·outcome `trade_reviews`(배선만)·RAG `rag_pipeline.py`(`analyze_and_store`·`query_similar`)·`embedding_store.py`(`search_similar`, recall 배선만)·RL `{continuous_learner,offline_rl,weekly_retrain}.py`·안전 `orchestrator.py:179`. **실존X(생성)**: `near_miss_veto`(CREATE)·`decision_aftermath`(→trade_reviews).
**B. 외부 (어댑트, R8 확인)**:
- Macro Analyst: **AlpacaTradingAgent**(✅FRED·bull/bear·quick/deep).
- 밸류·페르소나: **ai-hedge-fund**(✅Damodaran·Druckenmiller·Valuation).
- 레짐+레짐→%: **MarketMoodRing**(✅HMM·JointStochasticProg). **[주의] 입력=HMM states+수익률(정성 IC라벨 아님) → §6 fallback만. 메인 regime→%=§5.8-D BL.**
- recession 선행: **forecasting repo**(✅FRED-MD+NBER+ℓ1, **노트북→방법론 재구현**).
- **PIT 메모리 = History Rhymes 논문(2511.09754)** [repo 아님] — causal mask(쿼리 날짜보다 엄격히 과거 이웃만) → `embedding_store` 옵션 재구현(§0.6 link3).
- 멱등주문·슬리피지: **nautilus_trader**(채택 시 E2·P2 무상, 미채택 시 `identifier` 직접).
- 최적화: **Riskfolio-Lib**(HRP·CVaR·Ledoit-Wolf)·**PyPortfolioOpt**(BL). 과적합: **skfolio**(PBO).
- KIS: **pykis**(✅modify/cancel/pending·websocket·모의투자) → H15·E3·H17 재코딩 금지.
> 규칙: 출처 항목 새로 짜기 전 **중단하고 repo/논문 열어 입출력 계약 확인 후 어댑트.**

## 0.4 추가 차용 후보
- **dexter** — 자가검증(plan→execute→**validate**→synthesize)+DCF → §5.7·§5.8 macro_view 검증.
- **AgenticTrading** — alpha/risk/cost 분해+학습피드백. **[정정] P&L 귀속이지 beta/sector/idio 아님** → §5.9-B 택1. + Registration Bus(H29).
- **yakub268** — ①대시보드(O1·G8) ②Thompson 자본배분 ③GO/NO-GO 백테스트(Phase5).
- **pykis/공식 open-trading-api** — modify/cancel/pending·websocket(✅) → H15·E3·H17. 공식 `examples_llm/`+strategy_builder→backtester→KIS(Phase4/5).
> 범위 주의: Thompson·다중검증·MCP는 여력 시. v0=끊긴 고리·Phase -1 우선. 즉시: AgenticTrading 귀속(§5.9)·yakub268 대시보드(O1)·pykis(Phase4).

## 0.5 Phase 0 사전검증
1. **임베딩-RL 차원**(위험 하향): 라이브=임베딩-프리 `StateEncoder`(obs_dim=42) → BGE 교체로 PPO 안 깨짐. 작업=① `decision_embeddings`(3072)→BGE(1024) 재임베딩 후 recall delta ② 106d enhanced만 reproject. M4: 1536→3072→1024(세 번째) → mig 051에 "재임베딩 완료 전 신규 인덱스 미사용" 가드+체크포인트.
2. `decision_blender` Gemini 포맷 의존 여부. 3. 기존 임베딩 차원 확인 후 BGE-m3. 4. ZMQ 메시지 계약.

---

## 0.6 배선 명세 (실제 파일·함수 — 재코딩 금지)
> 라인은 v1.35.2 직접 확인 권고. 착수 전 정독 확정. *인프라 있으면 어댑트, 없으면 신규.*

### A. 학습/결정 3대 고리 (§5.9 실체)
- **링크1 — `trade_reviews` 라이터**: `scripts/execute_trade.py::_record_trade_to_db`(**:685**). ① decisions POST 헤더 `return=minimal`→**`return=representation`**으로 `decision.id` 회신. ② `side=="ask"` 시 Upbit `avg_buy_price`로 실현 P&L(`backtest_jan2026.py:697` 이식) → `trade_reviews`(mig 002b) INSERT. ③ ALTER `failure_reason` enum + `attribution JSONB` — 귀속 종류는 §5.9-B 결정.
- **링크2 — RAG recall**: `rl_hybrid/live_trader.py::_get_llm_analysis`(Phase4). `analyze_and_store` 전 `rag_pipeline.py::query_similar`(**:88**)→`embedding_store.search_similar` 호출, top-k를 Phase5 `blender.blend()` 주입. + `external_data={}`→Phase2 실거시.
- **링크3 — PIT 가드**: `embedding_store.search_similar`에 `status='closed' AND exit_at≤as_of` 필터 옵션. History Rhymes 논문(2511.09754) causal mask 재구현(클론 대상 없음).

### B. Phase -1 안전 (실제 파일)
- **E2 멱등성**: `execute_trade.py` 주문 바디(**~:448**)에 Upbit `identifier` + POST(**:462**) 전 동일 identifier 체결조회. `check_open_orders_and_cancel`(**:449/123**)는 대기주문만 → 체결후 응답유실은 identifier로만.
- **R2 reconciliation**: `run_cycle` Phase1(`get_portfolio.py` 직후) 루프 — 거래소 잔고 vs DB, drift→**halt + `execution_logs` 기록(자동보정 금지)**. drift 계산 day-1부터 fee-net. **[R9] 거래소 open-orders 조회해 미체결 잠긴(locked) 잔량을 DB 합산에 포함 → 미체결로 묶인 잔고를 drift에서 제외(가짜 halt 방지).** 배당 15.4%·CA는 H16 온라인 시 예상변동 등록(M6).
- **B1 하드게이트**: `prompts/schemas/decision_result.json`을 `llm_worker` 출력→risk_gate 경계 jsonschema 강제. 1차 Outlines/GBNF 생성강제, 2차 검증.
- **B3 결정성**: `rl_hybrid/rag/gemini_client.py:78` `temperature=0.3`→**0**(config). 결정 레코드(`base_agent.py:723`·`run_agents.py:665`·`_record_trade_to_db`)에 `model_id`·`prompt_hash`·`temperature` ALTER+기록.

### C. 기록 일관성 + 게이트 감사
- 결정 기록 단일화(분산→단일 지점). `near_miss_veto` net-new CREATE(`signal_attempt_log`·`execution_logs` 패턴). ablation-config 플래그(`alloc_deviation_enabled`·`consistency_check_enabled`).

### D. 신규 빌드
- 거시→비중(§5.8-B·D): **메인=Black-Litterman(Prior=IC표)**, MMR fallback. macro_reasoning/regime_classifier 신규(`core/brain/`, AlpacaTradingAgent+forecasting 재구현).
> 신뢰도: A·B 파일/라인 grep 확인. 착수 전 `_record_trade_to_db`·`run_cycle`/`_get_llm_analysis`·`query_similar`·`gemini_client.py:78`·`get_portfolio.py` 정독.

---

## 0.7 끊김 후보 보완 — 단계 간 계약 (R8·R9)

**G1. S3→S4→S6 양의 배분 체인**:
1. S3 슬리브 목표 `w_sleeve`. 2. S4 후보 스코어링·랭킹 상위 K. 3. `w_name = w_sleeve × (score-비례/동일가중)`.
4. **캡·dedup·정규화**: (순서) 상관 dedup을 *사이징 전*(corr>0.7 중복은 score 낮은 쪽 제외). (정규화) 단일10%·섹터30%·슬리브합 동시 만족은 1패스 미수렴 → **cvxpy QP**(목적=score 추종, 제약=캡+슬리브합) **또는** IPF + fixed-point 수렴 체크. (잔여) 풀린 비중 **모두 현금**(타 슬리브 이동 금지=S3 권한).
5. 주수=`floor(목표금액/가격)`(호가단위·최소주문). 6. S6 정합(QP에 캡 흡수). 7. 밴드=`|목표−현재|>밴드(+세금·수수료)`일 때만.

**G2. S5 allocation-aware 융합**: blend=종목 신호(방향+conf), 사이징=G1. 종목 신호는 **하향만** 오버라이드, 상향은 S3/S4. **downgrade-ratchet 차단**: downgrade 종목은 suppress 플래그로 *그 사이클 G1 재매수 제외*(N사이클/신호 회복까지). **confidence→축소율 테이블**(예: <0.3 전량, 0.3~0.6 50%, >0.6 hold).

**G3. S10 귀속 에이전트** (**[R10 결정] ⓐ factor 귀속, tiered minimal-viable — §5.9-B**):
- **[정정] AgenticTrading=alpha/risk/cost지 beta/sector/idio 아님** → 분해 차용 불가. **결정=ⓐ factor**(주식: market-β+섹터+idio / 코인: market-β+idio, 2~3 팩터 상한). 입력=closed `trade_reviews`+진입 `buy_score_detail`+보유기간 수익. 출력=`failure_reason`(`MACRO_REGIME_WRONG`/`SECTOR_THEME_WRONG`/`VALUE_TRAP`/`EXECUTION_SLIPPAGE`)+`attribution JSONB`. 저신뢰=unattributed. LLM은 lesson 텍스트만. *세 학습 루프(§5.8-H 거시·스타일·value-trap)의 공유 의존성.*

**G4. S10 학습효과 측정·롤백**: 관측 비교 교란(recall은 친숙 레짐 발동) → **randomized recall hold-out(A/B)**: 적격 결정 일정%에서 recall 무작위 차단, 영향군 vs 차단군 win-rate·MDD 델타(causal). 악화 시 recall 자동 비활성(RL Sharpe-drop 롤백과 동형). 관측 비교는 보조.

**G5. S11 GO/NO-GO 임계**(기본값·튜닝): 백테스트→모의: 다수폴드 비용차감 양수·**PBO<0.5**·**DSR>0**·MDD 허용·단일레짐 비의존. 모의(2주)→소액: 추적오차 밴드내·미설명 drift=0·슬리피지 오차 한도·안전위반 0. 소액→증액: 실현 vs 모의 일관·Sharpe/MDD 한도. *ref skfolio·yakub268.*

**G6. S11 LLM 백테스트 한계**: 결정론 코어 2018~ 완전 백테스트. LLM층 신뢰평가 불가(파라메트릭) → record-replay 패리티+probe로 동작동치만, 알파는 forward만. GO/NO-GO 엣지=결정론 코어 기준.

**G7. 리밸런싱 트리거→집행→세금**: 트리거 ⓐ레짐flip(S2) ⓑ§5.8-G divergence ⓒ정기 드리프트 ⓓ밴드 이탈. 집행=G1 밴드 리밸런싱. 세금: 해외 22% 연간 netting→손실수확 우선·연말 이연·`min_holding` 존중, 국내 0.20%는 밴드 임계에 비용. 충돌은 §6 precedence 격자. **[R9] 밴드 이탈 감시 주체 확정 = Portfolio Orchestrator(Phase6)가 `recommended_next_check()`와 독립적으로 매 사이클 최우선 Drift Monitor 실행(슬리브 목표±밴드 이탈 검사).**

**G8. 사용자 뷰 계약 (S12/O1, 백테스트·모의·실전 동일 포맷)**:
> 현 `dashboard.py`+`web/index.html`은 단일 BTC만, 백테스트는 stdout+JSON뿐. 세 단계 동일 포맷 뷰 필요(G5 판정은 사람이 봄).
- **공통**: 누적수익곡선·CAGR·MDD·Sharpe·승률·회전율·vs벤치마크·**슬리브별 비중/기여도**·**트랙별 손익**·보유종목 테이블·세후손익.
- **백테스트**: + walk-forward 폴드별 + **PBO/DSR → GO/NO-GO 카드**(결과 JSON 렌더).
- **모의**: 실시간 포트폴리오(`dashboard.py` 멀티에셋 확장) + 백테스트 추적오차 + 슬리피지 실측vs모델(E4).
- **실전**: + reconciliation drift(R2) + 안전게이트 상태 + 세후 일별 P&L.
- **차용**: `dashboard.py`·SQL 뷰(`v_daily_summary`·`v_trade_history`·`v_regime_performance`) 확장 + yakub268 모니터링. *재작성 아님 — BTC단일→멀티에셋/3단계 일반화.* **백테스트와 라이브가 같은 지표 계산 함수 공유**(안 그러면 비교 거짓).

**G9. [R9 신규] S10 미청산(open) 포지션 중간 귀속 (mark-to-market)**:
- 문제: G3이 closed 거래만 입력 → 느린 출혈 value trap·레짐 오판이 *청산 전까지 학습/경고 루프에 안 들어감*.
- 계약: S10 귀속 입력에 `closed_trades` 외 **`unrealized_feedback`** 추가 — **보유 N일 경과 OR 고점 대비 M% 하락**한 미청산 포지션을 mark-to-market으로 G3 귀속 분석에 태움(중간 라벨=잠정, status=open). §5.8-G③ "실현수익 악화 에스컬레이션"과 **명시 연결**: 진행 중 레짐 오판도 heavy-agent 재검토 에스컬레이션 + confidence decay 트리거(자동청산 아님). 청산 시 잠정 라벨을 확정 라벨로 갱신.

---

## 1. 목표 아키텍처

```
                  [Portfolio Orchestrator]   ← 자산배분(슬리브) + Drift Monitor(매 사이클, R9)
                  거시레짐(per-bloc) + 상관도, §5.8-B baseline 대비 편차(BL)
                          │
        ┌─────────────────┴─────────────────┐
   [Coin Track: 기존 흡수]            [Stock Track: 신규]
   AssetTrack 구현체                  AssetTrack 구현체
        │                                      │
        └─────────────────┬─────────────────┘
              [Shared Risk Gate]   ← 우회불가 hard rule + precedence 격자(§6)
                          │
        ┌─────────────────┴─────────────────┐
   [Coin Exec: 기존 업비트/바이낸스]   [Stock Exec: 신규 KIS pykis]
```

신설:
```
core/ asset_track.py · risk_gate.py(+precedence 격자) · portfolio_orchestrator.py(BL+Drift Monitor)
core/brain/ llm_provider.py(quick/deep) · embedder.py(Gemini→BGE) · macro_reasoning.py(§5.8) · regime_classifier.py(per-bloc)
stock/ value_trigger.py · valuation.py · kis_client.py(pykis) · data/(pykrx·FDR·OpenBB·FRED/ECOS·DART)
coin/ (기존 agents/·rl_hybrid/·kimchirang/ 래핑)
backtest/ (2018+, nautilus 선택)
```

---

## 2. 단계별 구현 계획

> **시퀀싱 원칙(R10)**: ① 치명 갭(E2·R2·B1·B3·C2)은 라이브 코인 경로라 **Phase -1 선반영(실금전 긴급 — "교체"가 아니라 구멍 막기, 미룰 수 없음)**. ② 그 외 모든 신규/교체 파이프라인은 **coin 위에 바로 붙이지 않고, 깨끗한 일반(coin-외) 버전으로 먼저 만들어 검증**(주식 트랙·클린 모듈·백테스트로). ③ 검증된 일반 버전을 **Phase R에서 coin에 *특성 변형* 이식 + DRY_RUN 패리티 테스트**(잘 도는 게 확인된 뒤에만 coin 적용, 회귀 0). → "coin 무조건 보존"이 아니라 **ref-우월 시 교체(§0.3 B표·아래 coin 변형표), 단 라이브 검증 + 패리티 후**.

> **coin 특성 변형표 (Phase R 이식 시 적용)**:
> | 일반 파이프라인 | coin 변형 |
> |---|---|
> | 통합 백테스트 엔진 | 24/7(휴장·캘린더 없음)·Upbit maker/taker·호가깊이 슬리피지·얇은 알트 임팩트·funding·KRW 페어 |
> | 사이징(Riskfolio) | 단일 BTC=기존 Kelly 유지, 멀티코인만 Riskfolio. crisis alt→BTC 상관 1수렴(H25) 더 급격→tail 상관 입력 |
> | 계층 메모리(FinMem식) | decay 반감기 짧게(crypto cadence)·코인 이벤트 기억(반감기·거래소 사건) |
> | 집행 상태머신 | Upbit `identifier` 매핑·테스트넷 없음→shadow-live(H19)·Upbit nonce/레이트리밋 |
> | consensus(§4.2) | 분석 렌즈가 다름: on-chain·sentiment(FGI)·funding·technical(DCF 없음)·타임아웃 짧게 |
> | 결정엔진/레짐 | `calculate_buy_score`·price `detect_regime`는 crypto-튜닝됨 → **유지**, macro만 위에 추가 |

### Phase -1 — 라이브 코인 안전 하드닝 (최우선)
배선 §0.6-B. E2 멱등성·R2 reconciliation(fee-net, **미체결 locked 제외**)·B1 하드게이트·B3 결정성·C2 서킷브레이커(일일 LLM 캡+degrade-to-Qwen). **수용**: §2.9 E2·R2·B1 결함주입 통과.

### Phase 0 — 코어 추상화 (코인 100% 보존)
`core/asset_track.py` ABC: `collect_market_state()`/`generate_candidate(state)→Decision`/`recommended_next_check(state)→datetime`. **전략 택소노미(M1)**: kimchirang(MarketNeutral)·scalp_ml(HFT)·altrang → Directional/MarketNeutral/HFT 3계열. 기존 **래핑만**. **수용**: 래핑 전후 동일(회귀 0).

> Phase 1~6은 **coin-외 일반 버전을 빌드·검증**한다(주식 트랙·클린 모듈·백테스트 기준). coin 라이브 경로 이식은 **Phase R**에서 패리티 후.

### Phase 1 — 두뇌 마이그레이션 (Gemini→Qwen+Claude / 임베딩→BGE-m3) [일반 빌드]
`llm_provider.py`(OllamaQwen quick·Claude deep·Gemini 호환), `embedder.py`(BGEm3·Gemini), mig 051+재임베딩(M4 가드). ZMQ 덕에 `llm_worker`만 교체. **+계층 메모리(FinMem식)·RAG recall(§0.6-A 링크2)을 일반 버전으로**. **수용**: Qwen 평상시, Claude=트리거 일치, recall 동작.

### Phase 2 — 공통 리스크 게이트 (우회 불가) [일반 빌드]
`core/risk_gate.py`: Lifeline·이중스톱·일일한도 승격. hard rule: per-position stop(-5/-10)·일일 손실한도(전 트랙 halt)·상관캡(>0.7)·max weight(10/30/트랙)·turnover·min_holding·kill switch(MDD>X→신규 halt+컨펌후 청산, 자동 전량청산 금지; H27 보완). **§6 precedence 격자 강제** + **멀티에셋 사이징=Riskfolio(Ledoit-Wolf, H25)**. 격리(매매권한·LLM 프로세스 분리). **수용**: 거절/축소가 `near_miss_veto`(CREATE) 기록.

### Phase 3 — 주식 트랙 + 가치 2단 트리거 [일반 빌드]
`stock/valuation.py`(DCF+멀티플 밴드, ai-hedge-fund 참고). `stock/value_trigger.py` 2단: 1차 Qwen(가격변동 AND 내재가치 갭) → 2차 Claude/Damodaran(value trap 판정) → risk_gate. **단순 buy-the-dip 금지**. announcement-date PIT(§5.7). **수용**: 가격만 빠진 vs 가치 갭 구분.

### Phase 4 — 데이터 레이어 + KIS 실행 [일반 빌드]
`stock/data/`(pykrx·FDR·OpenBB·FRED+ECOS). `stock/kis_client.py`=**pykis 어댑트**(modify/cancel/pending·websocket·**모의투자 우선**). **수용**: KIS 모의 주문 왕복 성공.

### Phase 5 — 통합 백테스트 엔진 (2018+) [일반 빌드 — coin 백테스트 *교체* 대상]
`backtest/`: 코로나·금리인상·BTC 사이클. **nautilus 또는 skfolio로 단일 엔진 통합**(coin의 13개 분산 backtest_*.py·슬리피지 0을 *교체*). 슬리피지·수수료·세금(§5). **수용**: 동일 전략 코드 백테스트·DRY_RUN 패리티(기계적≥95%, LLM 제외 H22)·DSR/PBO.

### Phase 6 — Portfolio Orchestrator + Consensus 게이트 (최상위) [일반 빌드]
`core/portfolio_orchestrator.py`: per-bloc 레짐(§5.8-A)+상관도 → 슬리브 비중. §5.8-B baseline 앵커 + macro_view 편차를 **BL(§5.8-D)**로 %화, risk_gate 통과. fallback Riskfolio HRP/MMR. **Drift Monitor**: 매 사이클 최우선 밴드 이탈 검사(소유자=Orchestrator). **+ §4.2 고-스테이크스 consensus 게이트**(레짐 flip·배분 변경·누적 x% 초과 시 발동). **수용**: §2.9 Phase 6 + consensus 게이트 판정.

### Phase R — Coin 이식 (retrofit) [검증된 일반 파이프라인 → coin 특성 변형 + 패리티]
Phase 1~6의 일반 버전이 *검증된 뒤*, coin 라이브 경로를 그 위로 이식. 위 **coin 특성 변형표**대로 변형(백테스트 엔진 교체·멀티코인 사이징·crypto decay 메모리·Upbit 집행·코인 consensus 렌즈). **각 파이프라인 이식마다 DRY_RUN 패리티**(coin 동작 보존 or 개선, 회귀 0). **수용**: §2.9 Phase R.

---

## 2.9 단계별 운영 합격 판정

> **게이트 원칙(재검증 R10)**: 모든 합격 기준은 *코드 완성*이 아니라 **"실제로 돌려서 의도대로 *행동*하는가"**(does-it-run/behave). 아래 전부 이 기준임을 재확인 — 결함주입·실역사 재생·동작 동치·무중단 완주·관측된 거절/halt. 임계값(95%·PBO<0.5·90일·<10%p 등)은 **튜닝값**(borderline이면 강화). 기존 ~80개 테스트 **확장**(신규 최소화).
- **Phase 0**: 7일 실데이터 래핑 전·후 `decision`·breakdown 의미적 동치(tolerance). 전제: RAG 격리/리셋·외부데이터·시계 freeze·PPO 결정성(B3)·LLM record-replay fixture. byte-동일 금지. → *동작: 래핑이 행동을 바꾸지 않음.*
- **Phase 1**: 72h DRY_RUN — Claude=0 평상시, 호출=트리거 일치·BTC −5% 재생→트리거·BGE recall 저하<10%p·PPO 정상·Qwen vs Gemini 방향 일치율. → *동작: 72시간 실제 가동 중 라우팅·recall이 작동.*
- **Phase 2**: 5종 주입(①일일손실→halt ②corr0.7+→차단 ③max weight→축소 ④MDD→halt+알림+청산보류 ⑤LLM 우회→실패) 5건 `near_miss_veto`. **precedence 격자 충돌(레짐flip+min_holding+halt 동시) 주입** → 격자 순서 해소. → *동작: 게이트가 실제로 막음.*
- **Phase 3**: 실역사 N≥10(**상폐/0 포함**) — 패닉셀(가치유지)→후보, 실적쇼크(가치동반하락)→매수안함. value-trap 혼동행렬. **[R10] 유니버스 게이트(§5.10) 주입: 레버리지/인버스 ETF·선물·옵션·비US/KR 개별주·관리종목/거래정지 후보 투입 → admission에서 *전부 거절*(매수 유니버스 진입 0).** → *동작: 실제 사건에서 옳게 행동 + 부적격 상품 차단.*
- **Phase 4**: ①왕복 ②부분체결 ③분당한도 80% 실패<5% ④6h 토큰갱신+websocket 재연결 ⑤drift 주입→감지. **미체결 보유 중 reconciliation 주입 → locked 잔량 drift 오판 halt 안 함.** → *동작: 실거래소(모의) 왕복·복원.*
- **Phase 5**: ①슬리피지 0 vs 현실 정량화 ②기계적 패리티≥95%(LLM abstain stub) ③walk-forward OOS/IS Sharpe+**DSR/PBO** ④전구간 MDD<kill switch. 상폐 포함. → *동작: 동일 코드가 백테스트=라이브로 거동.*
- **Phase 6**: ①레짐 전환 시 슬리브 이동 §5.8-B 방향 정합(per-bloc) ②통합 MDD<트랙 합(분산) ③통합 대시보드(G8) ④**90일 무중단** ⑤macro 노드 강제종료→신규매수 보수(abstain)이나 청산·리밸런싱 정상(H29). **미청산 N일 경과 주입 → G9 발동·에스컬레이션. 야간 FX stale 주입 → H26 고정환율로 가짜 kill-switch 미발동.** **[R10] §5.8-H: 과거 레짐 오판 구간(filtered≠smoothed) 재생 → 보정 레코드 생성·PIT 준수(원결정 backfill 0)·유사구간 재현 시 confidence 하향/caution recall 발동.** → *동작: 무중단 가동·고장 시 fail-safe·레짐 오판 학습.*
- **[R10] Consensus 게이트(§4.2)**: ① 고-스테이크스 주입(레짐flip/배분변경/단일 x% 초과)→consensus *실제 발동*, 서브에이전트가 *상이한 view* 산출, Judge 종합 ② **누적 포지션 x% 교차 주입(단건은 작게)→발동**(누적 회피 차단 확인) ③ routine 결정 주입→consensus *미발동*(비용 게이팅 확인) ④ consensus 발동 중에도 risk_gate가 여전히 모든 거래 게이팅 ⑤ regime classifier 선제 트리거 동작 ⑥ path-attribution 태그가 결정 레코드에 기록. → *동작: 적시 발동·적시 미발동·백스톱 유지.*
- **[R10] Phase R (coin 이식 패리티)**: 각 일반 파이프라인 이식마다 — ① 이식 전·후 coin DRY_RUN `decision`·breakdown 동치 or *개선*(회귀 0, Phase0 판정 재사용) ② coin 특성 변형(24/7·Upbit fee·shadow-live 등) 적용 후에도 안전게이트·reconciliation 정상 ③ 교체된 백테스트 엔진이 coin 과거구간에서 기존 대비 슬리피지·수수료 더 현실적(정량 비교). → *동작: coin이 새 파이프라인 위에서 기존만큼/더 잘 거동.*

### 🚦 실전 자금 전환 게이트
1. Phase 0~6 + Phase R + consensus 게이트 전부 통과. 2. KIS 모의+코인 DRY_RUN **합산 90일+** 무중단(실 급락/급등 1회 무사고). 3. 라이브 신호가 백테스트 분포 안. 4. kill switch·EMERGENCY_STOP·reconciliation 실발동 기록. 5. 극소액부터.

---

## 3. 트리거 로직 (요약)
| 트랙 | 성격 | 구현 |
|---|---|---|
| 코인 | 모멘텀·심리·레짐 | 기존 `calculate_buy_score`+danger/opportunity+`detect_regime` |
| 주식 | 가치 갭 | `value_trigger.py` 2단(신규) |
| 자산배분 | 매크로 유의변동 | Portfolio Orchestrator + BL(신규) |
폴링=`recommended_next_check()` 적응형. 평상시 Qwen, 트리거 시 Claude.

## 4. 두뇌 라우팅 (비용 통제)
평상시 Qwen 로컬(스냅샷+1차 필터, 임계 미달=Claude 0). 트리거 시 Claude deep(코인 극단·레짐전환 / 주식 가격변동 AND 내재가치갭 / 배분 매크로 surprise)→risk_gate. 임베딩 전량 BGE-m3. 호출 카운트 텔레그램 일일요약.

### 4.1 LLM 호출 모델 = stateless 일회성 + 컨텍스트 팩 (영속 세션 금지)
**Claude·Qwen 호출은 매 이벤트 stateless 일회성**으로 한다 — 상시 떠 있는 세션(예: tmux에 Opus 1M 상주)에 누적 컨텍스트를 유지하지 **않는다**. 연속성(continuity)은 *세션*이 아니라 **매 호출마다 durable 저장소에서 조립하는 "컨텍스트 팩"**에 있다:
- 현재 시장 상태·지표(S1) + RAG recall 유사 과거사례(PIT, §0.6-A 링크2) + 현재 `macro_view`/thesis(DB, §5.8-D, status 포함) + 최근 성과 요약(§5.9-E 데일리 랩업).

**구현 목적(왜 일회성인가 — 영속 세션이 깨뜨리는 것)**:
- **B3 결정성/재현성**: §5.9 사후분석은 "같은 입력→같은 결정" 재현이 전제(temperature=0·model_id·prompt_hash). 영속 세션은 누적 컨텍스트가 달라 같은 시장에 다른 답 → "왜 실패했나" 루프가 거짓.
- **H22 record-replay 패리티**: 백테스트·§2.9 Phase0 패리티는 LLM 호출이 *입력의 순수 함수*여야 재생 가능. 영속 세션은 숨은 상태로 재생 불가 → 라이브·백테스트 경로 분기.
- **PIT·오염 차단(H33)**: 누적 컨텍스트는 초기 환각·프롬프트 인젝션을 이후 모든 결정에 앵커. 일회성은 매 결정이 깨끗.
- **자가치유(O2)·상태영속(O3)**: 세션 크래시=기억 소실. 기억이 DB/RAG에 있으면 재시작 손실 0.
- **비용·관련성**: 연대순 1M 상주보다 RAG top-k(가장 유사 사례, §5.8-E causal mask)가 싸고 결정 품질↑.

**기존 자산(신규 아님 — 재코딩 금지)**: 일회성 호출은 *이미 기본 모드*(`run_agents.py`·`execute_trade.py` 등 전부 `subprocess.run` 단발, 영속 세션 없음). 컨텍스트 팩 = 기존 `rag_pipeline.query_similar`·`embedding_store.search_similar`(§0.6-A 링크2 배선). → **추가 구현 없음, 기존 인프라 + 명세된 배선으로 충족.** (영속 세션 쪽이 오히려 net-new이며 위 속성을 깸 → 채택 금지.)

### 4.2 고-스테이크스 Consensus 게이트 (= 안 "다" 게이팅된 다관점 합의)
평상시는 §4.1 blend(agent+RL+LLM 융합) 단독. **고-스테이크스 결정에만** 서로 다른 렌즈의 다관점 토론을 로컬 Claude Code 서브에이전트로 발동한다. **결정론 risk_gate는 consensus와 무관하게 *항상-on*으로 모든 거래를 게이팅**(consensus는 그 위 *추가* 게이트지 대체 아님 — TradingAgents의 "Fund Manager 승인" 자리).

**구현 목적**: 과신·맹점 감소(단일 신호/단일 모델 편향 방어) + **비용 게이팅**(매거래 토론은 24/7 코인에 비현실 → C2 토큰 폭발). 우리 §4 라우터(평상시 Qwen, 무거운 건 트리거만)와 정합.

**발동 트리거 (고-스테이크스)**: ① 거시 레짐 flip(S2) ② 슬리브 배분 변경(S3) ③ **단일 결정 OR 누적 포지션이 자산의 x% 초과**(S6 사이징; x%=튜닝). *단건이 아니라 누적 교차*로 잡아 "임계 바로 밑 반복 매수로 리뷰 회피"(death by a thousand cuts) 차단.

**메커니즘 (TradingAgents 어댑트 — 발명 아님, §0.4)**: 다관점 서브에이전트(주식=fundamental/sentiment/news/technical + Bull/Bear 토론 + Risk + Judge; **코인=on-chain·sentiment(FGI)·funding·technical**, DCF 없음) → Judge 종합 → *합의 시만 실행, 미달이면 부분만/관망*. 각 서브에이전트 = §4.1 stateless 호출(자기 렌즈의 컨텍스트 팩).

**게이팅 역효과 6 + 완화(토큰 절약 외)**: ① 누적 회피 → **누적 포지션 트리거**(위). ② 빈번한 소액의 누적 미검토 리스크 → **결정론 risk_gate 항상-on 백스톱**. ③ 탐지 의존(flip 놓치면 consensus 영영 안 붐) → regime classifier가 **선제(async) 트리거**. ④ 2-브레인(Qwen vs multi-Claude) 캘리브레이션 불일치 → **path-attribution 태그**(ablation 플래그, §5.9 귀속에 어느 경로인지). ⑤ 최악 순간 지연(대형=급변장) → 긴급 청산은 consensus 아니라 **§6 precedence 격자(결정론 즉시)**, consensus는 숙고형(배분 등)만. ⑥ 거짓 안전감 → consensus는 routine 안전 대체 아님을 명시.

**기존 vs 신규**: 메커니즘=TradingAgents 어댑트(신규 아님). **선택적 게이팅(고-스테이크스에만 + 누적·선제 트리거)이 우리 신규 글루.** coin `multi_agent_consensus.py`(RL 앙상블)와 **별개**(혼동 금지). **수용**: §2.9 consensus 게이트.

## 5. 수수료·세금 (게이트 hard parameter)
> 2026-01-01~ 금투세 폐지·증권거래세 환원 → **코스피/코스닥 매도 실효 0.20%**. 국내 양도차익 사실상 0(대주주만). 해외주식 양도세 22%/250만 공제.
- 국내 ETF 개별주 복제 금지(거래세 0.20%>운용보수 절감). `max_annual_turnover`·`min_holding_period` 회전 억제. 백테스트·risk_gate 비용에 거래세·환전(~0.2%)·해외 양도세·슬리피지.
- nuance: ① 해외 양도세 연간 손익통산 → `min_holding`이 연말 tax-loss harvesting 막지 않게 예외. ② 국내상장 해외ETF=배당소득 15.4%+금융소득종합과세. ③ 2026 고배당 분리과세(최고 30% opt-in). ④ 배당 입금=잔고 변동 → R2가 원천징수(15.4%)를 drift 오인 안 하게 H16 연계. **[R9] S6가 ①을 판별하려면 입력에 `ytd_realized_pnl`·`tax_lots_status` 필요(§6).**

## 5.7 Stock 데이터 토대
**A. 펀더멘털 PIT(DART/EDGAR)**: pykrx·FDR은 재작성 → 누수. (회계기간, filing timestamp, as-reported) 3-튜플. 백테스트는 `announcement_date≤as_of`만. 한국=DART(정정공시는 원본 접수일), 미국=EDGAR XBRL. dissemination lag.
**B. 생존편향**: 유니버스 상폐 포함.
**C. 기업행위(H16)**: 수정주가+이벤트 캘린더.
**D. H22 2층**: Layer1(기계적) PIT-clean 패리티(≥95%), Layer2(LLM) 패리티 제외·abstain·forward만.

## 5.8 거시/미시 추론 레이어 (brain 핵심 입력)
> 진짜 빈 곳: ① 거시→top-down 배분 ② 거시 PIT(ALFRED) ③ 리포트 통합 ④ 기여분 수익성 분리.
> 필수 요건(freshness≠liveness, C3): `regime_classifier.py`(결정론·무료)가 **매 사이클** Investment Clock baseline으로 `macro_view` 채움. `macro_reasoning.py`(LLM)는 **macro-trigger 시에만** enrich. 스키마: `macro_view`=regime(per-bloc)+stance+근거+인용ID+`status(fresh/stale/unavailable)`+age. B1은 present·well-formed만 검증. outage 시 last-good stale로 degrade하되 청산·리밸런싱 가능(H29). macro 노드는 thesis+**최강 반대 thesis** 동반. **per-bloc 레짐**(KRW/USD 분리), FX(H26)=다리. 수익성 분리: factorial(off/alloc-only/consistency-only/both, ablation 플래그). 정량 축은 결정론 baseline 기여(PIT)에 정박, LLM 증분 보수 게이팅 + 직교성 측정.

**A. 레짐 분류기**: Investment Clock(성장×인플레 4분면, FRED 실질GDP·코어CPI). FRED-MD+NBER(권위 라벨). Sahm·금리역전·FRED Recession Prob. **NBER lag 분리**: 학습 라벨만, 실시간 추론엔 FRED-MD+Sahm+나우캐스팅. **classifier(현재)≠forecaster(선행)**: `macro_view`에 `regime_now`+`regime_forecast`(+horizon). 가격 `detect_regime`과 별개.
- **[R10] sparse 재구성(중요)**: "거시=참고용" caution은 *라이브 메타라벨링 루프(§5.8-H)*에만 적용 — **분류기 자체는 sparse 아님.** *분류기 훈련 창 ≠ 트레이딩 백테스트 창*: 백테스트는 2018+(코인 제약)이나 **분류기는 FRED-MD(1959:01~, 128 시리즈)·FRED-QD(1959Q1~, ~250 시리즈)·NBER 사이클로 수십 년 국면 훈련**(St.Louis Fed 무료·vintage 처리). 표본 多.
- **[R10] 방법 보강 — Statistical Jump Models(JM/SJM)**: HMM/GMM에 더해 **`jumpmodels`(PyPI, Apache-2.0)** 채택 — JM은 HMM 일반화로 *제한된 표본·고차원·오설정·상태지속성에 훨씬 강건*(우리 sparse 문제 직격). **Sparse JM=피처 선택**(많은 거시 지표 중 레짐 정의 인자 자동 선별). scikit-learn식 API·`predict_online/predict_proba_online`. 암호화폐(Cortese 2023)·주식(Shu/Mulvey arXiv 2402.05272) 양쪽 검증. → 규칙(4분면)+**JM/SJM**(+HMM 비교 폴백).
- **[R10] 추가 무료 레짐 피처**: ADS Business Conditions(Philly Fed 실시간)·CFNAI/NFCI(Chicago Fed)·STLFSI·NY Fed 금리커브 침체확률·GZ excess bond premium·Jurado-Ludvigson-Ng 거시 불확실성·Baker-Bloom-Davis EPU(상당수 FRED).
- **정직한 한계**: 비정상성(60년 ≠ i.i.d. 레짐, 구조변화) → 긴 역사는 도움이나 공짜 아님; JM도 *모델*이라 PBO/과적합(H23) 적용; NBER 라벨 후행(학습 전용).
- 참고: forecasting(노트북, FRED-MD+NBER)·MMR(HMM/WKM)·**jumpmodels(JM/SJM)**.
- **[R10] 실제 유사 프로젝트(검증 — 우리 접근 novel 아님, 조립만 net-new)**: **feedoracle/feedoracle-macro-mcp**(*가장 가까운 analog* — AI 에이전트용 결정론 레짐 분류, 86 FRED 시리즈·7 가중신호[VIX·금리커브·침체확률·신용스프레드·금융스트레스·Fed스탠스·소비심리], MCP 서버 → 신호셋·구조 차용)·**ErickDWalker/Predicting-Recessions**(침체 불균형분류→자산배분, 금리커브+실업률+NFCI, NBER 12개월 lead-shift 조기경보 → classifier≠forecaster·조기경보 참고)·zhangkelly014/Nowcasting(NY Fed DFM, optional — published nowcast 소비로 대체 가능)·arXiv 2205.12126(고차원 factor+regime switching on FRED-MD). **차용 전 라이선스·품질 검증 필수(§0.3) — 개인 repo는 "설계 우월≠프로덕션 준비".**

**B. 규칙 레이어 (per-bloc 분할 표)**: 슬리브=미국주식/한국주식/원자재/금/채권/현금/코인.

  | bloc 레짐 | 해당 주식(US행/KR행) | 원자재 | 금 | 채권 | 현금 | 코인 |
  |---|---|---|---|---|---|---|
  | Reflation | ↓ | ↓ | ↑ | **↑(최우위)** | 중립 | ↓ |
  | Recovery | **↑(최우위)** | 중립 | ↓ | ↓ | ↓ | ↑ |
  | Overheat | 중립 | **↑(최우위)** | ↑ | ↓ | ↓ | 중립 |
  | Stagflation | ↓ | 중립 | ↑ | ↓ | **↑(최우위)** | ↓ |

  US행=USD 레짐, KR행=KRW 레짐에 독립 키잉(US overheat+KR recovery 가능). 원자재/금/채권/현금/코인은 글로벌(USD). 실제 %는 리스크 한도·변동성 타깃과 튜닝(risk_gate 내). **% 산출=§5.8-D BL 메인**(MMR fallback — `calculate_weights()`가 HMM states+수익률 입력이라 baseline anchor와 충돌).

**C. 리포트·지표 (거시 재인식의 *기본 공동 리소스* — 지표와 동급)**: 지표=FRED(`fredapi`)+**ALFRED vintage(PIT)**·ECOS·OpenBB.
- **리포트 소스(tier)**: ① 한국 sell-side 컨센서스(한경 컨센서스·네이버 리서치 — 증권사 애널리스트) ② **글로벌/거시 무료·공신력 소스(신규, 아래 큐레이션)** ③ DART 공시(`OpenDartReader`, 의견 아닌 사실).
- **② 무료·공신력 해외 소스 큐레이션 (접근성·ToS 등급 표기)**:
  - **(i) 공식 나우캐스트·지수 — machine-readable, 公공역(US govt), ToS 부담 0, 최우선**: **Atlanta Fed GDPNow**(실시간 GDP 나우캐스트, 주관조정 없음)·**NY Fed Staff Nowcast**·**Chicago Fed CFNAI**(국가활동지수)·**NFCI**(금융상황지수)·**SF Fed**(뉴스심리지수 등)·BEA·BLS·Census·Treasury 금리커브·OECD **CLI**(선행지수). → 상당수 FRED로 수신 가능.
  - **(ii) 공식 정성 narrative — 레짐 서사·NLP 가능, US govt 공역/기관 인용허용**: **Fed Beige Book**(지역 정성 conditions, 연준 자체가 FinBERT로 침체 나우캐스팅하는 소스)·**FOMC statement/minutes/SEP(dot plot)**·**FEDS Notes**·NY Fed Liberty Street Economics·**IMF WEO/GFSR**·**OECD Economic Outlook**·**BIS Quarterly Review**(신용·금융상황 권위)·World Bank GEP·**NBER**(침체일자 — *라벨 전용*, §5.8-A).
  - **(iii) 무료 운용사·스타 투자자 거시 view — "어떤 투자자?"의 현실적 답(공신력 있는 무료 공개 견해)**: 
    - *대형 운용사 정기 outlook*: **JPMorgan AM "Guide to the Markets"+"Eye on the Market"(Cembalest)**·BlackRock Investment Institute·PIMCO Cyclical/Secular·Vanguard·Fidelity·State Street(SSGA)·Invesco·Franklin Templeton·Capital Group·T. Rowe Price·Goldman Sachs Insights/GSAM·Morgan Stanley **"Thoughts on the Market"**.
    - *스타 투자자 무료 정기 발행*: **Apollo "Daily Spark"(Torsten Slok, 일간)**·**Oaktree — Howard Marks 메모**(oaktreecapital.com/insights, 무료·전설적)·**KKR — Henry McVey "Insights"**·Carlyle(Jason Thomas)·**GMO — Jeremy Grantham 분기 레터**·**Hoisington(Lacy Hunt) 분기 리뷰**·Research Affiliates(Arnott)·**Charles Schwab — Liz Ann Sonders** 시황.
    - *접근(개인·로컬·비배포 기준)*: 전부 *무료 공개*. **본 프로젝트는 개인·로컬·비배포 → 시스템이 실제 읽는 리포트의 *전문 저장·분석 허용*(요약보다 레짐 서사 뉘앙스를 정확히 잡아 분석 품질↑).** 저작권 의무는 *배포/공개/서비스화* 시 발동(사적 사용 아님 — §6 라이선스 논리와 동일). **남는 실무 제약만**: ⓐ **비배포 유지**(공개·공유·서비스화 금지, 하면 재검토) ⓑ **공손 수집**(robots.txt+rate-limit, H30 — 위반 시 소송 아닌 *IP차단·계정정지*가 현실 위험) ⓒ **쓰는 만큼만 수집, 아카이브 통째 스크래핑 금지**(ToS·DB권·차단 위험은 개인사용이라도 대량수집에서 날카로움) ⓓ 뉴스레터 구독분(Daily Spark 등)은 개인사용 OK·*전달 금지*. 착수 시 각 채널 robots/ToS 확인(H30).
  - **(iv) 심리·포지셔닝(무료)**: AAII Sentiment·U.Michigan 소비심리(FRED)·Conference Board.
- **소스 신뢰도 tiering**: 트랙레코드·적중도로 가중(D2 소스 스코어링 연계). sell-side는 *군집·자기책 옹호* 보정.
- **수집 모드 = 백그라운드 Qwen 사전적재(pre-load), trigger 시 retrieve only**: 리포트 수집·파싱·요약·임베딩은 *지연 민감하지 않은* 작업 → **평상시 백그라운드 Qwen(§4)이 신규 발행분을 지속 수집·요약·임베딩해 RAG 스토어에 *미리 적재***. macro-trigger 시 heavy agent는 *적재된 스토어에서 retrieve만*(임계경로에서 라이브 fetch 없음). 이점: ①trigger 지연 0(이미 적재) ②신선도(발행 즉시 인덱싱) ③비용(싼 Qwen이 대량 수집, heavy agent 아님) ④**resilience(C3/H29)**: 소스 다운이어도 last-good 적재본으로 degrade ⑤PIT(적재 시 *발표일자 timestamp* 부착 → causal-mask 검색 깨끗). 스토어는 decay·refresh로 stale outlook 관리(§5.8-E·§5.9-E). **정직**: 특정 스타 투자자 *실시간 포지션* 피드는 불가(13F 분기·후행; ai-hedge-fund 페르소나는 스타일 시뮬) — 위 (iii)은 *발행된 정기 view*를 사전 수집하는 것.
- **저작권·ToS 가드(개인·비배포 기준)**: 내부 추론용·로컬 저장 → **전문 저장 허용**(개인 사용). *발동 트리거=배포/공개/서비스화*(그때 재검토 — §6). robots/rate-limit·아카이브 통째 금지(H30). 파싱=Marker/Nougat. 저장=(리포트ID·발행기관·**전문 또는 요약**·임베딩·**발표일자 timestamp**). *실무 메모*: 전문은 저장·임베딩 비용/검색 노이즈↑ → 고가치 소스만 전문, 나머지는 요약으로 두는 게 효율적(법적 제약 아닌 선택).
- **🚨 git push 위생 (저작권 트리거 차단 — 필수)**: **git push = 배포/공개 → 사적사용 면제가 깨짐.** 따라서 수집한 **리포트 전문·원문·그 임베딩·RAG 스토어·DB 덤프·캐시는 git에 절대 커밋/push 금지.**
  - `.gitignore`로 data/store 디렉토리(리포트 캐시·전문·임베딩·벡터DB·Supabase 덤프) 전부 제외 → **코드만 push, 데이터는 로컬 전용.** 비밀키/`.env`도 제외(H6 재확인).
  - **테스트 fixture·예시·샘플에 저작권 리포트 전문 박지 말 것**(gitignore된 본 스토어를 우회해 commit으로 새어나가는 흔한 경로) → fixture는 합성/공역(US govt) 데이터로.
  - 리포지토리 private 유지 권장. 단 *private이라도 협업자 공유=배포에 준함* → 가장 안전한 건 **애초에 저작권 데이터를 commit하지 않는 것**. (공역 (i)·(ii) 소스 데이터는 git 올라가도 무방.)

**D. Macro Reasoning 노드 + regime→% (BL)**:
- 입력: A+B baseline+**C 리포트(지표와 동급 기본 공동 리소스)**+vintage+E 과거국면. 출력: 매 사이클 `macro_view`(per-bloc) 필수. ①top-down BL %화 ②bottom-up 정합성. LLM은 baseline 조정만(C2 abstain). **거시 재인식 시 지표와 리포트를 함께 검토**(리포트는 §5.8-H ③채널로 오판 탐지에도 투입).
- **regime→% = Black-Litterman**: **Prior=§5.8-B IC 목표비중표**(시총 prior 아님 — 이종 슬리브에 CAPM 균형 prior 불가). **View=macro_view 편차**(정성 stance→view 벡터). **τ·Ω=confidence**(낮을수록 Prior 근접). 공분산=Ledoit-Wolf(H25). risk_gate(캡·밴드) 통과. *ref PyPortfolioOpt BL.* MMR fallback.

**E. 과거 유사국면**: **History Rhymes 논문(2511.09754) causal mask**(쿼리 날짜보다 엄격히 과거=PIT) 기존 RAG에 재구현(클론 없음). 구조화 지표+narrative 공동 임베딩.

**F. PIT 가드**: ①데이터 lookahead→ALFRED vintage+발표일 정렬(완전 제거). ②파라메트릭 lookahead(모델 기억)→규칙/분류기는 PIT면 깨끗, LLM 거시추론만 백테스트 제외·forward. **contamination probe**: 원본 vs 익명화(날짜 마스킹+Z-score+자산명 난수화) 스탠스 일치, 코사인<0.7→그 시기 abstain. **발표시차 freeze**: `release_date` 스냅샷 동결.

**G. 밴드 제약 + thesis 무효화**:
- ①밴드: baseline=목표, bottom-up은 슬리브 목표±밴드 내만, 이탈 시 drift 리밸런싱(risk_gate 하드 강제, 감시=Portfolio Orchestrator R9).
- ②가설 flip(지표): regime classifier 재산정, H12 hysteresis.
- ③가설 무효화(실현수익): 지표 그대로여도 슬리브 장기 실현수익 악화=정보. HMM 레짐스위칭+변동성관리 DAA 채택. 고유=조합·절제: ⓐ 실현-vs-기대 괴리를 *auto-flip 아니라 heavy agent 재검토 에스컬레이션+confidence decay*(임계/윈도우), ⓑ 기대분포는 PIT 결정론 분포(H22 회피). §5.9 aftermath 측정, 사유 `MACRO_REGIME_WRONG`. **[R9] G9와 연결: 미청산 포지션도 mark-to-market으로 이 에스컬레이션에 태움(청산 전 조기 경고).**
- 긴장 관리: ①규율 vs ③가설버리기, 둘 다 자동청산 아니라 에스컬레이션 디폴트.

**H. [R10 신규] 거시 레짐 오판 피드백 루프 (사후 보정 → 학습 → 이후 추정 개선)**
> 목표: "지표로 현재 레짐을 판정·배분했는데, 지나고 보니 특정 지표가 평소와 다르게 움직여 *실제로는 다른 레짐*이었다"를 **기록·보정하고 학습해, 유사한 거시상황 재현 시 더 잘 추정**한다. 현재 조각(G②③·§5.8-E·§5.9 `MACRO_REGIME_WRONG`)을 *닫힌 루프*로 연결하는 신규 와이어링.

- **① 탐지 (3채널)**: ⓐ(기존) 실현수익 괴리(§5.8-G③). ⓑ**지표 이상 탐지** — 선언된 레짐이 예측하는 지표 거동과 *불일치*(예: Reflation 선언인데 신용스프레드·금리커브·원자재가 Stagflation처럼 거동). 기계장치 = **HMM filter vs smoother 발산**(filtered=실시간 판정, smoothed=사후 정답; 둘이 갈리거나 관측 likelihood 낮으면 오판 후보, MMR HMM 무상). ⓒ**[R10 신규] 리포트 발산** — 동시대 리서치 컨센서스(§5.8-C)가 시스템 선언 레짐과 *어긋남*(애널리스트들이 "보통의 X 아니라 실은 Y"로 선회). 지연 하드지표보다 *빠른 정성 신호*이고, **PIT 타임스탬프된 동시대 리포트는 contamination 방어에 유리**(그때 알 수 있던 것 반영, §5.8-F와 정합). *단 caution: 리포트는 군집·후행·이해관계 → 지표와 *함께* 보는 한 신호일 뿐 단독 오버라이드 금지, 발표일자 PIT, 컨센서스 herding 중복제거.* "조금 늦지만 포지션 바꾸기엔 늦지 않은" 창 = §5.8-G③/H 에스컬레이션(auto-flip 아님).
- **② 사후 보정 레코드 (PIT-safe)**: `(as_of, regime_realtime, confidence_realtime, regime_hindsight, 이상지표_signature, lag)`를 기록. hindsight 라벨 = HMM smoothed state 또는 사후 NBER/실현. **PIT 철칙(§5.8-A NBER-lag 규칙과 동형)**: 보정 라벨은 **학습 신호로만**, *원래 실시간 결정에 절대 backfill 금지*(미래누수). 날짜 키 + causal mask.
- **③ 학습**: ⓐ 보정 레코드를 **§5.8-E RAG 거시 메모리에 'correction' 태깅** 적재 → 검색 시 "지표가 이렇게 보였을 때 교과서는 A라 했지만 실제 B였다"가 떠오름. ⓑ **분류기 보수적 재보정**(§5.9-E 데일리/주기 wrap-up 또는 weekly_retrain류 잡): 임계·전이확률·피처 가중을 *조심스럽게* 조정.
- **④ 이후 추정 개선**: 유사 거시 재현 시 §5.8-E causal-mask 검색이 과거 보정을 surface → **macro_reasoning(§5.8-D)이 confidence를 낮추고/보정 해석으로 tilt/caution flag**("이 지표 패턴이 과거 오판 선행") → BL τ·Ω 확대 → 배분이 Prior에 가깝게(과도 tilt 자제). 루프가 배분까지 닫힘.

- **⚠️ 정직한 한계(과대약속 금지)**:
  - **희소 데이터**: 구분되는 거시 레짐 에피소드는 *드뭄*(2018~2026에 수 건). 보정 샘플 수십 개로 분류기를 hard 재학습하면 **심한 과적합**(H23/PBO를 거시 레벨에 적용) → **보수적으로**: "hard 재가중"보다 *"불확실성 확대 + caution 메모리"*를 디폴트로. 이 루프는 *훈련된 예측기*라기보다 **"지표가 이상하면 덜 확신하라"는 caution 메모리**에 가깝다. **[R10 정밀화]**: 이 sparse caution은 *라이브 보정 루프*에만 — **분류기 자체는 FRED-MD/QD(1959+)·JM/SJM로 긴 역사 훈련 → sparse 아님**(§5.8-A). 즉 분류는 견고히, *라이브 오판 학습*만 caution.
  - **정답 자체가 추정**: "실제로는 다른 레짐이었다"도 lag·불확실성을 가진 추정(NBER 수개월 후 확정, 레짐은 잠재변수) → hard 재라벨이 아니라 *확률·confidence*로 다룬다.
- **기존 vs 신규**: 재사용=§5.8-A 분류기·§5.8-E RAG·§5.8-G②③·§5.9 `MACRO_REGIME_WRONG`·§5.9-E wrap-up·MMR HMM(filter/smoother)·forecasting repo `model_evaluation`(오프라인). 신규(소규모 어댑트)=지표 이상 탐지(HMM likelihood/filter-smoother 발산)+보정 레코드+보수적 재보정+보정 recall을 §5.8-D에 와이어. **표준 통계 기법(HMM smoothing) 위에 얹는 와이어링이지 신규 발명 아님.**
- **[R10 정정] 핵심 메커니즘 = 메타라벨링(명명된 기법, 발명 아님)**: "1차 모델(레짐/신호)이 맞았는지를 2차 모델이 학습해 억제·사이징"은 **López de Prado 메타라벨링**(*Advances in Financial ML*, 오픈소스 **MlFinLab** by Hudson&Thames). 불리한 레짐에서 동적 거래 억제·레짐 전환으로 모델 부진 해석이 정확히 이 기법의 명시 용도. → §5.8-H는 *메타라벨링 + HMM smoother + FinMem reflection을 레짐 레이어에 어댑트*. 차용 직전 MlFinLab 열어 확인(§0.3).
- **[R10 신규] 주식 레짐 오판 — 두 축 (메타라벨링의 진짜 sweet spot은 종목 신호)**:
  - **(a) 종목 신호 오판 = value trap(보안 레벨)**: §5.9-B `VALUE_TRAP`+G9가 다룸. 메타라벨링 교과서 적용처(2차 모델: "이 value 신호+피처면 함정 확률?" → 억제/사이징). **표본 多 → 거시보다 통계적으로 훨씬 건전.**
  - **(b) 스타일/팩터 레짐 = value-vs-growth 주도권(중간 레벨)**: value 스타일이 out-of-favor면 value_trigger가 체계적 함정 양산. 탐지=다수 종목에서 `VALUE_TRAP` *군집*(= value 팩터 실패, idiosyncratic 아님 → **G3 ⓐ factor 귀속에 의존**) → 그 스타일 레짐에서 value 트리거 confidence 하향. §5.8-H 루프를 *스타일 축*에 적용.
  - **건전성 비대칭(정직)**: 학습 건전성 = **종목신호(표본多) > 스타일레짐(수년 지속, 에피소드少) > 거시레짐(가장 sparse)**. 같은 메타라벨링 패턴을 쓰되 위로 갈수록 "예측기"가 아니라 "caution 메모리"로. 주식도 같은 오판이 있고 *오히려 종목 신호 레벨은 거시보다 학습이 더 잘 됨*.

## 5.9 결정 logging · 사후분석 · 지식 재활용 (귀속 종류 결정)
> 배선 §0.6-A. 성숙 패턴(FinMem·FinAgent·TradingGPT·TradingGroup) 채택·확장. repo 실태: outcome=`trade_reviews`(미배선, ~80% 완비), 귀속 substrate=`buy_score_detail`. → "기존 절반 + 신규(라이터·near_miss_veto·귀속·PIT) 절반". 고유 가치: ①PIT(History Rhymes mask) ②R2/B3 의존(없으면 틀린 교훈) ③credit assignment ④레짐 조건부 망각.

**A. logging**: 기존 breakdown+`buy_score_detail`+`decisions`+`execution_logs`/`signal_attempt_log`. outcome=`trade_reviews`(미배선). 확장 컬럼: `macro_view`(per-bloc·status)·`intrinsic_value`/`valuation_gap`·`trial-count`(H23)·`model_id`·`prompt_hash`(B3)·ablation-config.

**B. 사후분석 — [R10 결정 확정: ⓐ factor 귀속, tiered minimal-viable]**:
- **[정정] AgenticTrading=alpha/risk/cost(P&L 귀속)지 beta/sector/idio(factor) 아님** → AgenticTrading 분해는 그대로 못 씀. **결정: ⓐ factor 귀속 채택**(ⓑ alpha/risk/cost는 *거시오류 vs value trap* 구분을 뭉개 기각 — §5.8-H·스타일레짐·value-trap 세 루프가 전부 팩터 분해를 요구).
- **자산군별 tier(over-engineering 회피 — 최소 팩터)**: 
  - **주식(US/KR)**: market-β(KOSPI/KOSDAQ/S&P)+섹터+idiosyncratic 회귀(데이터 pykrx/FDR). → β지배=`MACRO_REGIME_WRONG`, 섹터지배=`SECTOR_THEME_WRONG`, idio지배(value 가설)=`VALUE_TRAP`, 잔차=`EXECUTION_SLIPPAGE`.
  - **코인**: market-β(BTC/총시총)+idiosyncratic만(섹터 축 없음 → ⓑ-lite로 degrade, *깨끗한 팩터 모델 없는 척 안 함*).
  - **상한**: Barra식 다팩터 리스크 모델 금지 — **market+섹터+잔차(2~3 팩터)**면 충분(과적합·over-engineering 회피선).
- **저신뢰 = unattributed**: 짧은 보유·소표본으로 β가 노이즈면 *억지 라벨 금지, 미귀속*(귀속은 사후 학습용이라 노이즈 β가 매매를 직접 망치진 않음).
- **enum과 분해 일치**(섞임 해소 완료). LLM은 라벨 위 lesson 텍스트만(라벨 생성 금지).
- **메타라벨링 연결(§5.8-H)**: 이 factor 귀속이 세 학습 루프의 공유 의존성 — `VALUE_TRAP` 군집→스타일레짐(value 팩터 실패), β지배 군집→거시레짐 오판. *ref: MlFinLab 메타라벨링 + factor 회귀(표준).*
- **[R9] 입력에 `unrealized_feedback`(G9)**: closed뿐 아니라 보유 N일/고점-M% 미청산 포지션 mark-to-market 귀속(잠정 라벨, 청산 시 확정 갱신).
- 귀속 강도(정직): 기계적 컴포넌트는 breakdown으로 강하게, LLM/거시는 H22로 약함 → probe+ablation 보완.

**C. 지식 재활용 (PIT)**: 유사 결정 시 RAG가 과거 결정+성공/실패+사유 검색(기존 RAG+§5.8-E mask). **PIT 강제**: `as_of` 이전 *결과 확정* 결정만.

**D. 신뢰성 의존성**: R2·B3(Phase -1)·H1/H19·H22. **R2·B3 없으면 사후분석 거짓** → 전제도 Phase -1.

**E. 데일리 랩업 (증류 = distillation job, 하루 1회)**
원시 로그(decisions·trade_reviews·attribution)는 granular하나 *합성 안 됨*. 하루 끝 **LLM 증류 잡**이 이를 상위 기억으로 distill한다(FinMem/TradingGroup의 reflection 패턴 채택).
- **구현 목적(왜 필요한가)**: ① 원시 로그를 *retrievable 내러티브 기억*으로 압축 → 다음 날 stateless 호출이 "어제의 합성"을 RAG로 retrieve(§4.1 연속성을 *세션 아닌 검색*으로 달성). ② **G9 미청산 포지션 mark-to-market 귀속**의 자연스러운 cadence(청산 전 조기 경고, §5.8-G③ 에스컬레이션). ③ **G4 학습효과 롤업** + thesis(`macro_view`) 갱신 + **레짐 조건부 망각**(낡은 기억 가중치 삭감). ④ G8 대시보드 일별 갱신.
- **실행 형태**: 하루 1회 *단일·바운드된* Claude deep 호출(열고→하루치 합성→닫음 — 상주 세션 아님). 결과 = **구조화 일일요약 레코드**(오늘 거래·레짐·thesis 유지/붕괴 사유·트랙별 P&L·관전포인트) → RAG에 임베딩(**날짜 키 + causal mask**로 PIT 안전 = 백테스트 day N 랩업은 day N까지만 가시). `model_id`·`prompt_hash` 로깅(다음 날 결정에의 영향 추적).
- **기존 vs 신규(재코딩 방지)**: **재사용** = 스케줄 하네스(`rl_hybrid/launchers/`·`weekly_retrain.py` 패턴·`run_monthly_training`), 일일 집계(`v_daily_summary`), 알림 집계(`scripts/alert_aggregator.py` = H7 에스컬레이션), RAG store/recall(`rag_pipeline`·`embedding_store`). **신규(어댑트)** = *LLM reflection 스텝 자체*(repo엔 RL 재훈련·SQL 집계·알림만 있고 LLM 회고→RAG 적재 잡은 없음) → FinMem/TradingGroup 패턴 어댑트, 발명 아님.
- **충분성 판단**: 결정 호출은 stateless+RAG recall로 *충분·우월*(§4.1). 데일리 랩업은 *학습 신호 품질*을 의미 있게 올리나 v0 필수는 아님 — 권장 구성요소(Phase 6 또는 Phase 1 후반에 추가 가능).

---

## 5.10 적격 유니버스 · 상품 정책 (S4 *앞단* admission 게이트 — 신규 레이어, R10)
> **문제(검토 결과)**: coin repo·본 설계 모두 *종목/상품 단위 적격성 필터가 부재*. coin은 `KRW-BTC` 단일 하드코딩(현물). 주식 트랙을 명시 정책 없이 풀면 KIS API가 **선물·옵션·레버리지/인버스 ETF(곱버스)까지 거래 가능**하므로 시스템이 의도치 않게 위험상품을 편입할 수 있다. → S4 종목 선정 *앞단*에 admission 필터를 둔다(파이프라인이 아니라 *상품 단위* 가드).

**A. 상품유형 정책 — 2계층(영구 floor / 완화가능 default-off)**
- **[Tier 1 — 영구 hard floor, 완화 불가]** 선물·옵션·마진·CFD·증거금 공매도 = *부채/청산 위험*. 강제청산·원금초과손실(마이너스 가능). 안전 아키텍처(스톱·kill-switch·캡)가 *청산 시점을 내가 통제하는 현물* 전제라 마진이 그 전제를 깸. 마진관리·롤·청산회피 서브시스템 없음. **편입 금지(consensus로도, 어떤 조건으로도 허용 안 함).**
- **[Tier 2 — 완화가능, default-off]** 레버리지/인버스 ETF·ETN(±1배 초과 곱버스/2x, 및 ±1배 인버스). 청산위험은 없으나 decay·경로의존·value 프레임 부적합. **디폴트 제외**, 단 §5.10-E 완화조건 충족 시 *격리 전술 슬리브*(하드캡 ≤X%·짧은 보유·value 프레임 제외·자체 빠른 스톱·consensus 게이팅 §4.2)로 개방. *주의*: ±2배는 decay가 커 완화 문턱 더 높게, ±1배 인버스는 청산위험 0이라 상대적으로 먼저 열 후보.
- **[허용 — 코어 유니버스]** 현물 개별주·ETF·금/원자재/채권 ETF·현물 코인(Upbit).

**B. 지역 정책 — 완화가능(default-off)**
- **[default]** 개별주 = 미국·한국만. 이유: bottom-up value(Phase 3)는 *PIT 펀더멘털*이 있어야 정직 → DART(KR)·EDGAR(US)만 신뢰 PIT 확보(§5.7). 다른 나라 개별주는 PIT 펀더멘털 파이프라인 부재 → 가치판단 근거 없음. 그 외 지역 노출 = ETF/ADR로(top-down 배분 결정).
- **[완화가능]** 특정 국가 개별주는 §5.10-E 조건(해당국 PIT 펀더멘털 소스 확보 + 백테스트 검증) 충족 시 화이트리스트에 추가 가능.

**C. 종목 단위 admission 필터 (coarse→fine, QuantConnect Lean Universe Selection 구조 차용)**
- **coarse**(유동성·가격): 최소 거래대금/ADV·최소 시총·**penny/저가주 제외**·상품유형 화이트리스트(A)·지역(B).
- **fine**(상태·펀더멘털): **KRX 관리종목·투자경고·투자위험·거래정지·상장폐지 우려 제외**(pykrx 헬퍼)·정정공시/감사의견 한정·H17(가격제한·하한가 잠김) 연계·H5(생존편향, 상폐 포함은 *백테스트 유니버스만*, 라이브 매수 유니버스에서는 제외).
- 통과분만 S4 종목 선정으로. 단일종목 집중캡(§6 max weight 10%)·섹터캡(30%)은 사이징 단계.

**D. 유니버스 = config, LLM 결정 아님**: 적격 유니버스는 *화이트리스트 config*이고 파이프라인은 그 *안에서* 고른다. **새 상품류/국가를 유니버스에 추가 = 사람 config 변경 + consensus(§4.2) 검토 + §5.10-E 완화조건 충족**(per-trade가 아니라 정책 변경). LLM/에이전트는 유니버스를 확장할 권한 없음(§6 hard rule).

**E. 완화 경로 (calibrated default → 증거 기반 개방)** — *보수성을 영구 금지가 아니라 "증거 충족 시 푸는 기본값"으로*:
- **Tier 1(마진/선물/옵션)**: **완화 없음(영구 floor).** 청산위험은 회복 불가·비대칭 → 어떤 단계·증거로도 자동 개방 금지(헷지 전용 도입은 별도 대규모 검증·사람 결정 주제로 분리, 본 시스템 범위 밖).
- **Tier 2(레버리지/인버스 ETF)·지역**: 아래 *전부* 충족 시에만 사람 승인 + consensus로 격리 슬리브 개방 —
  1. **모의/소액 단계 진입 후**(백테스트만으로 개방 금지).
  2. **decay·추적오차 실측**(레버리지/인버스): 보유기간 실측 decay가 기대범위 내, tracking error 한도 내.
  3. **데이터 PIT 확보**(지역): 해당국 펀더멘털 PIT 소스 + 백테스트 통과.
  4. **하드캡 + 빠른 스톱 + consensus 게이팅** 적용, value 프레임에서 제외.
  5. **롤백 조건 명시**: 개방 후 decay/추적오차/손익이 기준 이탈 시 자동 재폐쇄(슬리브 비중 0).
- 개방은 항상 *작게 시작*(캡 점증), 단계 게이트(§2.9·실전 전환 게이트)와 동일 철학.

> 차용: QuantConnect Lean `Universe Selection`(coarse/fine) 구조 — 착수 직전 열어 확인(§0.3). KR 제외목록=pykrx/FDR. **신규 레이어이나 구조는 표준 패턴 차용.**

> **[R10] 참조 repo 규칙 실태(검증)**: "트레이딩 규칙"을 둘로 나눠야 정확하다. **(1) 리스크/포지션 규칙 = ref에 풍부, 이미 차용**: ai-hedge-fund `risk_manager.py`(변동성조정 포지션 한도+상관행렬+스톱+하드 %캡)·nautilus RiskEngine(사전 주문 한도)·FinRL turbulence 청산·Riskfolio 제약 → 우리 §6·Riskfolio가 이미 사용. **(2) 유니버스/상품-적격성 규칙 = LLM-에이전트 repo엔 없음(설계상 위임)**: TradingAgents·ai-hedge-fund는 *티커를 사람이 입력*(`--ticker`), 상품유형·지역 스크린 없음 — 오히려 ai-hedge-fund는 short/margin까지 허용(우리보다 관대). → 이 레이어는 *프로덕션 프레임워크(Lean Universe Selection·nautilus instrument config)*에만 존재. 따라서 §5.10은 **Lean 구조를 차용 + 상품-유형/지역 제외는 우리가 의도적으로 더 보수적으로 거는 안전 정책**(프레임워크 결함 아님).

---

## 5.5 내구성(Hardening) — 전 Phase 횡단

**H1. 백테스트 슬리피지(Phase5 최우선)**: `reward.py` `SLIPPAGE_RATE=0.0003`(flat) 있으나 `sim_engine.py`엔 `FEE_RATE`만·슬리피지 0. → sim_engine에 슬리피지+거래대금/호가잔량 비례 임팩트. 13개 backtest 단일 엔진. 타임존 단일 UTC. **라이브 캘리브레이션(E4)**: R2 데이터로 예상 vs 실제 체결가 주간 측정→파라미터 자동 보정.
**H2. reconciliation(Phase -1/2/4)**: 사이클마다 거래소↔내부→보정+`execution_logs`. polymarket ghost check. **[R9] 미체결 open-orders locked 잔량 합산→drift 제외.** 양다리(kimchirang)=leg-by-leg+hedge-completion 데드라인+2번째 실패 시 1번째 unwind. truth=거래소(H11 quorum), 임계 drift=halt(auto-correct 아님).
**H3. 구조화 출력(Phase1)**: jsonschema 하드게이트, 실패→관망+`near_miss_veto`. Qwen 환각↑ 중요.
**H4. 중앙 레이트리밋(Phase4 KIS)**: 거래소별 토큰버킷+백오프+우선순위 큐(주문>조회). KIS 토큰 6h+websocket 재연결(pykis).
**H5. walk-forward+펀더멘털 PIT·생존편향(Phase5)**: D1을 가격-PIT/펀더멘털-PIT 분리(FDR/pykrx 재작성값). filing timestamp 정렬. 상폐 포함.
**H6. 키/권한(Phase0/4)**: 역할분리(`.env.owner`=service_role/collaborator=anon+token). service_role 읽/쓰 분리·vault, **출금스코프 시작 시 조회→부여 시 중단**(코드 강제).
**H7. 통합 관측(Phase6)**: 트랙 통합 P&L·MDD·Sharpe·회전율·LLM비용 대시보드(G8)+텔레그램. **에스컬레이션 매트릭스**: 정보성 vs 치명 분리, 치명은 2차 채널(SMS).
**H9. 멱등성(Phase -1/4 치명)**: client_order_id 부여→제출 전 조회→멱등 재시도. 판정: 응답유실 주입 후 재시도해도 1건.
**H10. 버전·결정성(Phase -1/1)**: temperature=0+model_id+prompt_hash 결정 레코드. 판정: 동일입력 N회 동일.
**H11. staleness/quorum(Phase4)**: timestamp+신선도, 핵심소스 quorum(≥70%) 미달→관망.
**H12. 레짐 hysteresis(Phase0/6)**: 확률 레짐+전환 쿨다운, Sharpe-drop 롤백.
**H13. 동시성/분산락(Phase0/2)**: file lock뿐→분산락(Supabase advisory)/낙관적 동시성. H9 통합. 판정: 두 워커 동시→1건.
**H14. LLM 서킷브레이커(Phase -1/1)**: 일일 Claude 캡+degrade-to-Qwen, 지연예산 초과→휴리스틱. **C2×Phase3 충돌**: 모니터링 Qwen 강등 OK, **매수 결정은 강등 시 abstain(매수 금지)**.
**H15. 스마트 주문(Phase4)**: 지정가 Post-Only/FOK/IOC+n분 미체결 정정(pykis `order.modify`). E3 통합.
**H16. 기업행위(Phase3/4)**: 수정주가+이벤트 캘린더(분할·배당락·합병·유증·상폐). 상폐→H5.
**H17. 가격제한폭/거래정지(Phase4/5)**: 한국±30%·거래정지·**하한가 잠김=매도 불가**를 슬리피지·게이트 반영(pykis 상하한가 조회).
**H18. US 주식 FX(Phase4/6)**: KIS 해외=USD → KRW/USD가 P&L 압도. FX를 상관·리스크 입력. US 장시간(KST 야간)×모니터링.
**H19. 코인 집행 현실성(Phase -1/5)**: Upbit 테스트넷 없음 → Binance testnet 또는 **shadow-live**(주문 계산만+실호가 대조). kimchirang funding cost.
**H20. 운영 연속성(Phase4/6)**: API 장애 시 관망+HTS 수동청산 재기동 동기화(O3). limiter ZMQ 공유.
**H21. 생성단계 스키마(Phase1)**: constrained decoding(Outlines/GBNF/Ollama format=json) + post-hoc 2차.
**H22. LLM 백테스트 오염(Phase5 치명)**: 결정 일부가 LLM인 한 패리티 원리적 불성립 → 2층 분리(기계적≥95%, LLM abstain stub). 정량화(ScienceDirect 2025)·필터(MemGuard-Alpha 저신뢰)·unlearning(2512.06607). 로컬 Qwen(소형) 오염 유리.
**H23. 다중검정/PBO(Phase5)**: 4계열×튜닝=trials 다수 → Deflated Sharpe/PBO(López de Prado) 수용기준. trial-count(H10) 로깅. skfolio purged CV.
**H24. kimchirang viability(Phase -1/4)**: Binance 한국 차단·FSC 미등록·트래블룰 → **research/shadow-only 강등**. 재진입(둘 다): 합법 자금이동+leg-unwind·숏레그 마진버퍼·이관 리드타임+shadow-live. §6 hard rule.
**H25. 상관 불안정/tail(Phase2/6)**: corr>0.7 캡은 위기에 1수렴→무력. Ledoit-Wolf+tail 상관 별도. "캡=평시 가정, crisis(H12)엔 무력" 명시.
**H26. numeraire/FX 타이밍(Phase6)**: 통합 MDD·Sharpe·kill switch를 **단일 numeraire(KRW)+FX 스냅샷 고정**(H1 UTC 정합). kill switch 입력에서 FX 변동 분리 옵션. **[R9] 야간 US장(KST 밤) 환율 API 미갱신·스프레드 확대 시 가짜 MDD→오발 → 직전 정규장 마감 고정환율(또는 NDF 실시간 역외환율)을 사용해 가짜 MDD 변동 차단**(§2.9 Phase6 주입 검증).
**H27. halt-then-confirm 무인 footgun(Phase2×H18)**: US장=KST 야간 손실 누적=역footgun → **bounded auto-fallback**(컨펌 N시간 없고 2차 임계 초과 시 자동 *시간분산 축소*, 전량 아님).
**H28. 전략 capacity(Phase5/6)**: 전략당 capacity(자기충격) — KR 소형주·얇은 알트. 트랙 한도에 capacity 상한.
**H29. 필수입력 producer liveness 디커플(C3)(Phase1/6)**: 필수입력 producer 장애 ≠ 결정 정지를 코드 강제. macro_view는 결정론 baseline 항상 present, LLM 실패는 status:stale/unavailable degrade하되 매매(청산) 지속. 판정: macro 노드 종료→신규 보수(abstain)이나 청산·리밸런싱 정상.
**H30. 데이터 프로바이더 rate-tier(Phase4)**: DART·FRED·OpenBB·ECOS tier·IP 정책 다름 → jitter·백오프·rotation·tier 한도. §5.8-C 라이선스 연계.
**H31. business-calendar/휴장일(Phase3/4/6)**: KRX·NYSE·코인24/7 → 자산별 calendar. 폐장·stale 시 관망 동결(거래 가능 시장만 리밸런싱).
**H32. KIS 적격성+bus-factor(Phase4)**: 개인 KIS 완전자동 약관·고회전 세무 웹검증. bus-factor: 운영자 부재 시 자동 보수화+비상연락.
**H33. prompt injection 위생(Phase1/3)**: NewsRang·리포트 원문 인젝션 → 위생 레이어(정규식+소형모델 instruction-parsing+데이터/지시 분리). §5.8-C 필수.

---

## 6. 비협상 안전 규칙 — [precedence 격자 + R9 세금입력]

1. 실자금 전 전 트랙 DRY_RUN 2주+KIS 모의 통과.
2. LLM은 후보 제안만. 실행권한=risk_gate 통과분, 격리 프로세스.
3. 수동 EMERGENCY_STOP 절대 해제 불가.
4. risk_gate는 LLM 호출 함수 아닌 그 위 inviolable wrapper.
5. 거절/near-miss/실패는 감사 테이블(`near_miss_veto`·`execution_logs`).
6. 초기 실자금 극소액.
7. **kimchirang research/shadow-only.** 재진입(둘 다): 합법 자금이동+leg-unwind·마진버퍼·리드타임+shadow-live. 강등 근거(정박): 자금이동 합법성·미등록 VASP·즉시 리밸런싱 불가. ("API 살아있는데?"로 뒤집지 말 것.)
8. **다중제약 precedence 격자(risk_gate 하드 강제, 위→아래 우선)**:
   ```
   EMERGENCY_STOP (수동, 최상위, 해제 불가)
   > kill-switch halt (MDD>X% → 신규 halt; 청산=사람 컨펌/H27)
   > forced_stop (-10% per-position, 즉시 청산)
   > regime-flip 청산 리밸런싱 (S2 flip → 비중↓; 청산 방향은 min_holding 면제)
   > min_holding_period (신규/증액만; 청산 항상 면제)
   > 밴드 리밸런싱 (|목표−현재|>밴드일 때만)
   ```
   청산은 `min_holding` 항상 면제. kill-switch halt 중 regime-flip 청산은 halt 규칙(컨펌/H27) 따름.
9. **[R9] 세금통산 입력 계약**: S6 risk_gate는 tax-loss harvesting 판별 위해 입력에 `ytd_realized_pnl`(연초 대비 실현손익 추정)·`tax_lots_status`(세금 롯)를 받는다. `get_portfolio()`/S9(DB)에서 주입. 없으면 해외 22% netting 최적화 불가.
10. **[R10] 적격 유니버스·상품 정책(§5.10, hard)**: ① **[영구 floor] 선물·옵션·마진·CFD·증거금 공매도 편입 금지**(부채/청산 위험 — consensus·어떤 조건으로도 불허). ② **[완화가능 default-off] 레버리지/인버스 ETF·ETN(곱버스·±1배 인버스 포함)** = 디폴트 제외, §5.10-E 완화조건(모의/소액+decay·추적오차 실측+하드캡+consensus+롤백) 충족 시에만 격리 전술 슬리브 개방. ③ **[완화가능 default-off] 개별주=미국·한국만**, 그 외 지역=ETF/ADR; 특정국 추가는 §5.10-E(PIT 소스+백테스트) 충족 시. ④ 유니버스는 *config 화이트리스트* — LLM/에이전트는 확장 권한 없음, 추가=사람 승인+consensus. ⑤ 매수 유니버스에서 관리종목·투자경고/위험·거래정지·penny 제외(S4 앞단 admission 게이트).

---

## 7. 기존 규약 (스타일)
- 자연어 전략(strategy*.md) 점수표 유지. 결정=`decision_result.json` 확장(`valuation_gap`·`intrinsic_value`·`macro_view`[per-bloc·status]·`trial-count`·`model_id`·`prompt_hash`·ablation-config). 마이그레이션 순차(`051_`~), `asset_track` 컬럼. 텔레그램·자가치유·file lock·점수 breakdown 유지.
- **git push 위생(§5.8-C·H6)**: 저작권 리포트 전문·임베딩·RAG/벡터DB 스토어·DB 덤프·`.env`/키는 `.gitignore`로 제외 — **코드만 push, 데이터·시크릿은 로컬 전용**(git push=배포→저작권 트리거). fixture에 저작권 전문 금지(합성/공역 데이터). 공역(US govt) 데이터만 commit 무방.

## 8. 첫 작업 지시 (Claude Code에게)
> "**Phase -1부터 시작하라.** §0.6-B 실제 파일·라인 정독·확정 후 ① E2 `identifier` 멱등성 ② R2 reconciliation(fee-net, **미체결 locked 제외**, halt-on-drift) ③ B1 jsonschema 하드게이트 ④ B3 temperature=0+model_id/prompt_hash ⑤ C2 일일 LLM 캡+degrade-to-Qwen 을 현 코인 라이브(DRY_RUN)에 적용. 각 항목 §2.9 Phase -1 결함주입 통과. 완료 후 diff·테스트·결함주입 결과 보고 후 Phase 0 승인. 어떤 ref 차용도 *새로 짜기 전에* repo/논문 열어 입출력 계약 확인(§0.3). 각 Phase는 §6 안전 규칙·precedence 격자·세금입력 계약 위반 금지."
> 이후: Phase -1 → 0(추상화·택소노미) → [1~6 일반 빌드] 1(두뇌+계층메모리) → 2(risk_gate+격자+Riskfolio) → 3(주식 2단, §5.7 병행) → 4(KIS pykis) → 5(통합 백테스트 엔진=coin 백테스트 교체) → 6(Orchestrator BL+Drift Monitor+consensus §4.2) → **Phase R(coin 이식+패리티)**. 각 Phase 독립 PR + §2.9 동작 게이트 통과 후 진행.

---

## 9. 핸드오프 전 검증 결과 (R10 웹 점검 완료 + 잔여 항목)
> 로컬 넘기기 전 *웹으로 점검 가능한 항목은 전부 점검*했다. ✅=검증 완료, ⚠️=부분(설계는 합당, 수치/실측은 구현 시), ⛔=웹으로 불가(로컬/설계 결정 — 해당 Phase 직전 처리). 신뢰도 위계: 라이브 grep > 명명 방법론 > 요약기반 주장 > 설계공간 "신규" 주장.

**A. go/no-go 블로커 — 둘 다 ✅ 해소**
1. ✅ **KIS 개인 자동매매 — 허용 확인.** KIS Developers Open API는 *개인 투자자의 자동매매 시스템 구축을 공식 지원*하며(REST+websocket+모의투자), 공식 포털이 "ChatGPT·Claude 등 AI 연동 자동매매"를 직접 안내한다. eFriend Expert Open API = "고객 본인 알고리즘으로 자동주문 프로그램 개발·매매" 명시. → **주식 트랙 집행 경로 유효, 블로커 아님.** *주의(블로커 아닌 형식)*: 관련 규정상 고빈도/알고리즘 계좌가 **KRX 알고리즘 계좌로 등록**될 수 있음(증권사가 처리). 고회전 시 양도세 신고는 §5 통산 규칙대로.
2. ✅ **라이선스 — 로컬/개인 사용엔 비차단.** **copyleft(GPL/LGPL/AGPL) 의무는 *배포/서비스 제공* 시에만 발동**하며, 본 시스템은 *로컬 단일 사용자 개인 운용*이라 **사적 사용으로는 어떤 OSS 라이선스도 의무 미발동**. 확인: nautilus_trader=**LGPL-3.0**(사적 사용 무방), Riskfolio-Lib/skfolio/PyPortfolioOpt=permissive(BSD/MIT), TradingAgents=Apache-2.0(연구용 고지)·FinRL=MIT. → **지금 차용 무방.** *유일 단서*: 향후 **코드를 배포하거나 타인에게 서비스로 제공**하면 nautilus(LGPL)·AGPL 의존성이 의무 발생 → 그때 재검토.

**B. 설계 결정/검증 — 일부 ⚠️, 일부 ⛔**
3. ✅ **G3 귀속 = ⓐ factor, tiered minimal-viable — 결정 완료(R10).** 주식=market-β+섹터+idio, 코인=market-β+idio(2~3 팩터 상한), 저신뢰=unattributed(§5.9-B). 잔여=구현 시 섹터지수/β proxy 매핑·회귀 안정성 튜닝(데이터는 pykrx/FDR 가용).
4. ⚠️ **BL 이종 슬리브 — 설계는 합당, 수치 sanity는 Phase 6.** BL Prior가 *시총 균형일 필요 없음* — 전략적 reference 비중(=IC표)을 Prior로 쓰는 건 **표준 실무 변형**(custom prior). 따라서 설계 자체는 정당. 단 금ETF+BTC+KR주식 혼합에서 수치 거동은 Phase 6 착수 시 소규모 시뮬로 확인.
5. ⛔ **ref repo 실제 입출력 시그니처 — 유보(규칙으로 커버).** 외부 repo는 존재/성격/라이선스 확인됨. 실제 함수 계약은 §0.3 규칙 "어댑트 직전 repo 열어 확인". coin만 v1.35.2 직접 grep.

**C. 환경·운영 — 데이터/세금/kimchi ✅, 컴퓨트·버전 ⛔(로컬)**
6. ⛔ **coin 라이브 버전 ≠ 클론(v1.35.2) 가능성 — 로컬 확인.** 배선 라인번호 "편집 전 정독 확정"(§0.6).
7. ✅ **데이터 소스 가용성 — 확인(개인 무료).** DART(OpenDART)=개인/기업/기관 누구나 무료, 과도호출 시 제한(일 호출상한 존재). FRED=무료 키(≈120 req/min). ECOS(한국은행)=무료 키. pykrx/FDR=공개. → **전부 개인 무료·가용.** 정확한 분당/일일 한도는 키 발급 후 확정 → H30 백오프·rotation으로 처리(이미 명세).
8. ⛔ **로컬 컴퓨트·지연 예산 — 로컬 측정.** Qwen 로컬 상시 + §4.2 consensus 서브에이전트 동시 소환의 하드웨어·지연 미측정(웹 불가). Phase 1·6에서 실측.
9. ✅ **2026 세금 — 확인(수치 확정).** 금투세 폐지·증권거래세 환원→코스피/코스닥 매도 실효 0.20%, 국내 양도차익 사실상 0(대주주만), 해외 22%/250만 공제·연간통산, 고배당 분리과세(opt-in 최고 30%). ⚠️ ETF-vs-직접보유 *손익분기 수치*만 hard parameter로 구현 시 산출(§5).
10. ✅ **kimchirang — 확인(파킹 유지).** Binance 한국 앱차단·미등록 VASP·트래블룰 → research/shadow-only 강등 근거 확정(§6-7·H24). 재진입 조건(합법 자금이동) 미충족 → 파킹.

> **종합**: 웹 점검 가능 항목(A1·A2·C7·C9·C10) **전부 ✅ 검증 완료** — go/no-go 블로커 없음, 착수 가능. 잔여 ⛔는 *로컬/설계 결정*(G3 택1·coin 버전·컴퓨트 실측)이고 ⚠️는 *해당 Phase 착수 시 sanity*(BL 수치). 이 목록을 Claude Code에 "각 ⛔/⚠️를 해당 Phase 진입 게이트에 포함"으로 전달할 것.
