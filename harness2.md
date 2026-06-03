# harness2 — 통합 투자 시스템 구현

> harness2-wf 구동 문서. plan: [`plan.md`](./plan.md) · 구현핵심: [`implementation-keys.md`](./implementation-keys.md) · 설계: [`IMPLEMENTATION_PROMPT.md`](./IMPLEMENTATION_PROMPT.md) · progress: [`progress.md`](./progress.md)
> **verifier 검증 핵심 = §2.9 동작(does-it-run/behave) 게이트** (사용자 확정). 코드 완성 아닌 "돌려서 의도대로 행동" 기준. 임계값(95%·PBO<0.5·90일 등)=튜닝값.
> 작업 규칙: ① Sonnet-executable ② reuse-github-as-is(출처 implementation-keys.md §1-§7) ③ stub 주의(MlFinLab labeling·AT attribution·AT registry=계약만).

## Pipeline Goal
검증된 단일 BTC 봇(`coin/`)을 asset-agnostic 코어로 일반화 + 주식 트랙(KR/US 가치) + 거시 자산배분 brain 통합. **라이브 구멍 차단(Phase -1) → 일반 빌드(1-6) → coin 이식·패리티(R)**. 각 Phase 독립 PR + §2.9 동작 게이트 통과 후 다음.

---

## ▶ 현재 실행 Phase: Phase -1 — 라이브 코인 안전 하드닝

### Phase Final Objective
현 코인 라이브(DRY_RUN) 경로에 E2·R2·B1·B3·C2 적용 → §2.9 Phase -1 결함주입 전부 통과. 배선=`IMPLEMENTATION_PROMPT.md §0.6-B` + `implementation-keys.md §1`.

### Sub-objectives (관찰가능·원자·커버리지·독립)

- [ ] **SO-1 E2 멱등성** — `coin/scripts/execute_trade.py` 주문 body 에 Upbit `identifier` 부여 + POST(`~:462`) 전 미체결+체결완료(daily_order) 양쪽 조회 + 타임아웃 catch→`_reconcile_recent_order(identifier)` 중복차단.
  - reuse: polymarket `trader.py:314-337`(응답유실 재시도). 경계: nonce(`:153`)·DRY_RUN·EMERGENCY_STOP(`:250`) 보존.
  - **Verifier 검증(§2.9)**: 주문 직후 응답유실 인위 주입 → 재시도해도 주문 **1건만** + `execution_logs` 기록.
- [ ] **SO-2 R2 reconciliation** — `coin/rl_hybrid/rl/live_trader.py::run_cycle`(`get_portfolio` 직후) 거래소↔DB 대조→drift halt+`execution_logs`(자동보정 금지, fee-net day-1) + open-orders locked 잔량 DB 합산(가짜 halt 방지) + 매도 `_clamp_to_balance`.
  - reuse: polymarket `trader.py:260-274`(ghost) + `:283-289`(clamp), 양방향. 경계: 임계 drift=halt(자동 write-off 금지).
  - **Verifier 검증(§2.9)**: 잔고 drift 주입→다음 사이클 감지·기록. 미체결 보유 중 주입→locked 오판 halt 안 함.
- [ ] **SO-3 B1 스키마 하드게이트** — `coin/rl_hybrid/nodes/llm_worker.py` 출력→risk 경계 jsonschema(`prompts/schemas/decision_result.json`) 강제, 실패→관망+`near_miss_veto`.
  - reuse: TradingAgents structured-output 패턴. 경계: 스키마 본문 확장(§7)은 별도.
  - **Verifier 검증(§2.9)**: 깨진 JSON 주입→관망+기록, 통과 JSON→정상.
- [ ] **SO-4 B3 결정성** — `coin/rl_hybrid/rag/gemini_client.py:78` `temperature=0.3→0`(config) + 결정레코드(`base_agent.py:723`·`run_agents.py:665`·`execute_trade.py:685`)에 `model_id`·`prompt_hash`·`temperature` ALTER+기록. 마이그레이션 **047_**.
  - 경계: PPO 결정성 별개(Phase0). 
  - **Verifier 검증**: 동일입력 N회 동일결정 + 모델교체 시 레코드 버전차 기록.
- [ ] **SO-5 C2 서킷브레이커** — `coin/rl_hybrid/rag/gemini_client.py` 일일 LLM 호출캡+초과시 degrade-to-Qwen + 지연예산 초과→휴리스틱. 텔레그램 일일요약 호출카운트.
  - 경계: 매수 degrade 시 abstain(H14, 모순1=Phase3 재검토). 
  - **Verifier 검증(§2.9)**: 트리거 폭주 주입→캡 발동+Qwen 폴백, 지연초과→휴리스틱.

### Sufficiency Check (Supervisor 기입)
- [ ] 5 SO 전부 Sonnet-executable(파일:심볼·before/after·경계·완료판정 구비) 확인
- [ ] reuse-github 출처(polymarket/TradingAgents)가 `_refs/` 에 clone 됨 확인 (polymarket-bot 미clone 시 SO-1/2 전 clone)
- [ ] coin clone 라인번호 = v1.35.2 직접 재확인(§0.6 "편집 전 정독 확정")
- [ ] 결함주입 하니스 = 기존 ~80 테스트 확장(신규 최소화)

---

## 후속 Phase Final Objective + Verifier 게이트 (도달 시 sub-objective 상세화)

- **Phase 0** 코어 추상화: `core/asset_track.py` ABC·M1 택소노미·코인 래핑만. **게이트**: 7일 실데이터 래핑 전후 decision·breakdown 의미동치(RAG격리·시계freeze·PPO결정성·LLM record-replay, byte동일 금지).
- **Phase 1** 두뇌+brain wire: BGE·Qwen·작성 `core/brain/` 통합·PIT causal-mask·FinMem decay·reflection→RAG. **게이트**: 72h DRY_RUN Claude평상시0·트리거일치·recall<10%p·PPO정상.
- **Phase 2** 리스크게이트: precedence 격자·Riskfolio 사이징·프로세스격리. **게이트**: 5종+격자충돌 결함주입→`near_miss_veto`.
- **Phase 3** 주식 2단: 작성 `stock/` 통합·§5.10 admission(FDR PIT). **게이트**: 실역사 N≥10(상폐) value-trap 혼동행렬+유니버스 거절. (모순2 lookahead 대응 선행)
- **Phase 4** 데이터+KIS: DART/EDGAR PIT·ALFRED·pykis. **게이트**: 왕복·부분체결·초당 레이트리밋·토큰갱신+websocket·drift·locked 오판방지.
- **Phase 5** 백테스트 엔진: 단일엔진·`common/metrics.py`·자체 CSCV PBO. **게이트**: 기계적 패리티≥95%(LLM stub)·OOS/IS+DSR/PBO·MDD<kill switch.
- **Phase 6** Orchestrator+consensus: BL(작성 `regime_to_weights`)·Drift Monitor·2단 Judge·대시보드. **게이트**: 레짐전환 슬리브이동·통합MDD<트랙합·90일 무중단·macro종료 abstain+청산정상·consensus 적시.
- **Phase R** coin 이식: 특성변형+DRY_RUN 패리티. **게이트**: 이식 전후 동치/개선·안전게이트 정상·백테스트 더 현실적.

---

## 🔄 Reflection & Closing (Phase 완료 시)
- [ ] RC-1 각 에이전트(Worker/Verifier/Healer/SR) reflection 질문 + 요약 수집
- [ ] RC-2 수집 (3분 대기)
- [ ] RC-3 Supervisor 자체 reflection (4필드: 대상파일/현재L/변경제안/근거/영향범위)
- [ ] RC-4 promotion-log 기록 (없으면 "검토 완료 — 기록 대상 없음")
- [ ] RC-5 사용자 보고 + improvement-registry
- [ ] RC-5.5 progress.md 체크박스 반영 (완료 항목 `[x]`)
- [ ] RC-6 teammate 정리 + 플래그 정리

---

## 미해결 결정 (착수 중 판정 — review-findings §4)
1. 모순1: C2 degrade→Qwen abstain 이 급락장 가치전략 무력화 → Phase3 전 heavy-agent 우선순위 큐.
2. 모순2: H22 lookahead 가 Phase3 수용판정에도 적용 → training cutoff 이후/마스킹/기계적-only.
3. 갭4: M1 택소노미 = Directional only(권고) vs 3계열 → Phase0 전 확정.
4. 디렉토리: coin 코드 Inv 루트 승격 시점("Inv 구현→coin 덮기").
