---
tags: [type/design, domain/inv, phase/II, track/T1, topic/assumption-lifecycle-v2, session/btn-Inv]
date: 2026-05-29
session: btn-Inv
deliver_to: btn-Codlearn (T3, 최종 통합 + 3자 schema 합의)
plan: ./plan-inv-v2.md
progress: ./progress-inv-v2.md
raw_consult: [./.consult-inv-R1.txt, ./.consult-inv-R2.txt, ./.consult-inv-R3.txt]
briefings: [./.consult-inv-briefing-R1.txt, ./.consult-inv-briefing-R2.txt, ./.consult-inv-briefing-R3.txt, ./.consult-inv-briefing-R4.txt]
contract: [./DESIGN-button-v2.md (§10.6 event ledger), ./CONSULT-DECISIONS-button-v2-20260529.md (§5/§6), ./CONSULT-DECISIONS-whole-20260529.md (§btn-Inv — 12event/3ts/CQRS/checksum/replay/fill 보강 확정)]
note: btn-Inv(T1) 데이터·PIT·실거래 안전 계층 v2 설계. 자문 R1~R3 수렴(gemini+claude 병렬) + btn-button event-ledger 계약 재정렬. 구현 내용·자문요약·raw 포인터 = main 전달용.
---

# DESIGN-inv-v2 — 데이터·PIT·실거래 안전 계층 (event-ledger 재정렬)

## 0. 범위 + 바인딩 축 (btn-Codlearn 정의)
btn-Inv(T1) 소유: 학습 데이터 기반 + 실거래 안전. 충족 게이트:
- **IA-1**[축A·F] 모든 결정→trigger 가정 id+version PIT log + 실현 outcome join (3+도메인, 결과라벨 100%, 역추적).
- **IA-2**[축D] data_contract 게이트=validator 앞단 (측정깨짐=incident ≠ 가정틀림).
- **IA-3**[축F] 임의 as_of 가정체인 재현(lineage replay) + online_fdr alpha-wealth 영속(bitemporal).
- **IA-4**[금융상품] 무료 PIT 데이터소스 + panel 자산 컬럼 + 생존편향.
- **IA-5**[축F·Q1] 모의계정 outcome 수집 + shadow→live 사람게이트.
- **IA-6**[신규 제안, 자문 채택] 시계·정정 무결성(단일 UTC + 거래소 calendar bitemporal).
요청 GATE: R4데이터(상품/자산 archetype 데이터) · R5데이터(결정log→학습 closed-loop) · R8(d4_book 실데이터) · R11(data_contract/lineage/online_fdr 영속) · R12(실거래까지).

## 1. ★ 교차세션 재정렬 (확정 — 재논의 X)
closed-loop substrate = **단일 bitemporal append-only event ledger** (btn-button 5R 확정, btn-Codlearn 조율). **본인(T1)이 ledger 본체 소유**. btn-button(T2)=read-only 소비, btn-Codlearn(T3)=lifecycle event emit + state 소비.
- 계약 SSOT: `DESIGN-button-v2.md §10.6` + `CONSULT-DECISIONS-button-v2-20260529.md §5/§6`. **★3자 ack 도착(2026-05-29 btn-Codlearn)**: event-ledger 채택 OK + 전체구조 3R 자문 보강 5건 **빌드 전 반영 필수** = (1)12 event(+REVISION_OBSERVED) (2)3 typed timestamp(tt/dt/vt) (3)CQRS(snapshot+watermark) (4)ingestion checksum→DATA_CONTRACT_VIOLATION (5)적대적 PIT replay 1급 게이트 + shadow→live fill 내생성 + crypto-only 의존 금지. 본 설계 §2·§5 반영 완료.
- 도메인 확장: 거시 / 개별주식 / ETF / commodity / **crypto(BTC/ETH, CoinMetrics Community 무료, proxy 금지)** / FX(risk-regime gate). asset_class 공통필드 분기. crypto on-chain 소싱 = 내 데이터 도메인.

## 2. 설계 — 2 레이어
### 레이어1: THE EVENT LEDGER = outcome_ledger 본체 (별도 스키마 폐기)
`core/data/event_ledger.py` (신규). ★전체구조 3R 자문 보강 반영(CONSULT-DECISIONS-whole §btn-Inv):
- **12 event**(11→12, ★REVISION_OBSERVED 추가): ASSUMPTION_CREATED / PREDICTION_MADE{assumption_id,version,regime_ctx_snapshot,trigger_snapshot,horizon_h,deadline} / OUTCOME_OBSERVED / **REVISION_OBSERVED{supersedes_event_id, 동 vt·새 tt}** / HOLD_REMEASURED / CANDIDATE_PROPOSED / RATIFIED / FDR_DECISION / TRANSITIONED / RETIRED / DATA_CONTRACT_VIOLATION / CALIBRATION_CHANGED.
  - ★REVISION = 사후 거시지표 정정 = **새 bitemporal fact**(동일 vt, 새 tt, supersedes=원본 OUTCOME event_id). ⛔ OUTCOME 에 vintage 필드로 mutate 금지(append-only 위반 + tt 순서 소실 = revised lookahead alpha 누수, 에러 없이 라이브 하회로만 드러남). as-of 해석 = 각 vt 에서 tt ≤ as-of 인 최신 fact.
- **★3 typed timestamp 강제**(single 금지): `tt`(transaction_time=append 불변·**seq total order=저장순**) / `dt`(decision_time=엔진 인지) / `vt`(valid_time=데이터 날짜). reduce=**tt 순**, FDR replay=**dt 순**, Brier/DM=**vt 재계산**. tt 만 저장순이고 dt/vt 는 read-model 인덱스.
- 공통필드: event_id(ULID), seq(monotonic tie-break), schema_version, asset_class, parent_event_id, config_hash, data_vintage, crc, **(tt,dt,vt)**.
- **★CQRS**: log=진실원(append-only), snapshot=**tt-cut reduce projection + watermark(seq)**, 순서=**append→ack→project**. 라이브 소비=snapshot. byte-identical=reducer 결정론(Walking Skeleton 으로 증명).
- ★FDR_DECISION = immutable, dt 순만 재생. late outcome=OUTCOME_OBSERVED append(wealth 되감기 X). FDR event 에 account_type{discovery,retest} + write-time 동결 family key(domain×campaign) (claude R3).
- 영속: jsonl flock + .tmp→os.replace 원자성. 기존 `core/structure/online_fdr.py`(LORD++/AlphaInvesting) 알고리즘을 reducer 내부에서 사용.
- 본인 emit: PREDICTION_MADE / OUTCOME_OBSERVED / REVISION_OBSERVED / HOLD_REMEASURED / FDR_DECISION / DATA_CONTRACT_VIOLATION.
- ★Walking Skeleton: dummy-event 랜덤순서 주입→특정 tt-cut state 100% 복원 TDD 증명 전 분석로직 금지. **+ 적대적 PIT replay 1급 게이트**(아래 §5).

### 레이어2: PIT DATA SUBSTRATE (ledger 이벤트가 참조/계산하는 시장데이터)
- `core/data/identity.py` (신규): PSID(영구 surrogate) + identifier_history(bitemporal: psid,id_type{ticker/isin/krx_short/cusip},id_value,valid_from/to,knowable_from,sys_time) + corporate_action_graph(predecessor/successor_psid,action,effective_date,knowable_from). resolve_psid(ticker,as_of)=PIT 함수. 합병=splice 금지. **ticker 키 금지(재사용 splice)**.
- `core/data/corporate_action.py` (기존 corp_action.py 확장/신규): 분배/분할 별도 bitemporal CA ledger(각 이벤트 own knowable_from+vintage, 연말 재분류=sys_time append). OUTCOME 의 TR 계산 입력.
- `core/data/instrument_source.py` (신규): ETF TR forward-only(raw close + CA ledger, back-adjust 금지, Net/Gross convention) / 선물 `roll_adjusted_return(legs:Mapping[ContractId,RawSeries], roll_calendar(bitemporal), *, as_of, roll_policy(frozen), ...) -> {returns(knowable_from 인덱스), active_leg, roll_events, coverage_start}` (★price 출력 부재, 연속물 저장 금지) / crypto CoinMetrics(MVRV/realized-cap/LTH, netflow guard 비활성+band 보수) / NAV괴리 regime-tag(replication_type{physical,synthetic}+underlying_session, 구조괴리 baseline 차감 residual).
- `core/data/fx.py` (신규): 통화 PIT 정규화. OUTCOME_OBSERVED.outcome_value 에 currency+fx_convention+fx_vintage. cross-asset 비교 = 공통 as-of instant T_compare=max(outcome_knowable_from) 의 FX vintage(claude R3). hedged/unhedged.
- `core/data/calendar.py` (신규): 거래소 세션·휴장 bitemporal 참조 → decision_time/knowable_from 산정. IA-6 단일 UTC/DST 결합.
- `core/data/data_contract.py` (신규, Pandera): ingestion↔검증 게이트, 이상→DATA_CONTRACT_VIOLATION emit + HOLD_SUSPENDED(FDR 제외+사람확인). max_staleness per-series cadence-aware + consumer calendar 기준. contract_schema_version 각인. ContractResult{passed,incidents[],as_of}. 측정깨짐≠가정틀림, PENDING(미실현)과 분리.
  - ★**ingestion checksum/hash 대조**(전체구조 자문 #2·#R3): 벤더가 REVISION 통지 없이 과거를 silent 덮어쓰면 PIT 형식은 멀쩡해 data_contract 가 못 잡는다. → 이전 vintage 의 (key, knowable_from≤이전 as_of) content fingerprint 를 보관하고 재적재 시 대조. **이미 알 수 있던 과거 값이 통지 없이 바뀜 = silent_rewrite incident → DATA_CONTRACT_VIOLATION**(정상 REVISION 은 REVISION_OBSERVED event 동반이라 구분). PENDING/정상 revision 과 분리.
- `core/data/universe_membership.py` (신규, claude R3 #1 — crypto/ETF first-class라 필수): bitemporal(member_psid,universe_id,weight,valid_from/to,knowable_from,sys_time). ETF holdings/지수구성/crypto 바스켓. 관측시점 append-only 축적(vendor 현재구성만).
- `core/data/pit_query.py` (확장): synth_knowable_from(≥max(입력)+compute_delay) + assert_referential_pit(seed.derived_from→as_of 활성 가정, T3 is_active 계약). knowable_from write-time 동결 materialize, replay 재계산 금지(claude R3 invariant lock).
- `core/data/lineage.py` (신규): ProvenanceRef + LineageEvent + emit(jsonl) + replay_provenance(as_of). config_hash 공통필드 연계.
- `core/structure/panel_schema.py` (확장): instrument_kind{equity,etf,commodity,crypto,macro_series,fx} + lifecycle_status{active,delisted,expired,discontinued,liquidated} + tradability(직교: AUM/volume floor → zombie/halt) + coverage_start + inception_date + live_tracked vs index_backfilled + tick_size/multiplier(gemini R3). delist_* 하위호환.
- vintage(open-sequence, claude R3 #2 + btn-button revision-drift): macro/지표 vintage 를 (vintage_knowable_from,sys_time) open append. realtime/final=view. revision-drift monitor(결정 vs 수정된 진실).
- `core/data/online_fdr_state.py` 또는 event_ledger 내장: alpha-wealth = FDR_DECISION 이벤트 reduce 로 도출(별도 영속 불필요 — ledger 가 SSOT). p_value_vintage 기록.
- 연결: data_vintage=vintage / asset_class=도메인 / config_hash=compute_delay+derivation_fn_version stamp(replay config 재읽기 금지) / terminal outcome(delist/merger_cash/liquidation/expiry)=OUTCOME_OBSERVED.terminal_reason+terminal_value.
- IA-5/R12: `core/data/promotion_gate_live.py` — shadow→live 사람게이트. promotion_record(append-only){assumption_id,version,shadow_window,attribution_summary,alpha_consumed,regime_coverage,incident_count,family,approver,approval_ts}. kill_switch latch 재사용(해제=사람만). 로직 분기 금지·sink만 분기(shadow vs live = execution_mode).
  - ★**fill 내생성 + shadow→live ramp**(자문 #4 + R4/R5 Q1): own-impact·adverse-selection·reflexivity = interventional gap → observational 보정 불가, **소액 live ramp 만 추정**. ramp = 사전등록 **geometric ladder**(c₀,2c₀,4c₀…), **rung 크기 FIX·'전진 여부'만 data-dependent**(size-as-peeking 차단). 각 rung = R2 graph node(부모 e-돌파 시 자본 해금 = e-allocation 흡수). ramp 전용 **e-process**(null="net-of-impact edge≤0") → size↑ 서 net edge 부호반전 = capacity ceiling 표면화. realized impact > band = **OOB breaker**. impact estimator = 실행강도 랜덤화(자기 flow 내 식별) + multi-horizon post-trade reversion(temp/perm, Almgren √-law). 방어 = 실행 랜덤화·PoV cap·venue/timing 분산.
  - ★**전이 불변식 — crypto-only 속성 의존 금지**(자문 #5): self-flatten 등 안전장치가 crypto 의 ①연속거래 ②데이터 final ③substrate 독립 에 은밀 의존하면 equity overnight gap·halt 시 무의미. 안전 invariant 는 machinery correctness(PIT byte-identity·ledger 결정론·abstain-on-missing·breaker-binds-before-ruin)만 전이, parameter·시장구조 가정 비전이.
- R8: `core/book/d4_book.py` 실데이터 populate + to_context 소비 wire.

## 3. 자문 수렴 요약 (raw = .consult-inv-R{1,2,3}.txt)
- 채널: gemini Pro + claude Opus 4.8 병렬(Playwright). R1 설계 → R2 ETF 전용/retrofit 탐침 → R3 통합 검증. R4 briefing 작성됨(event-ledger 재정렬, 미발사 — 계약 확정으로 확인용).
- 수렴 핵심: 측정깨짐≠가정틀림 / outcome_knowable_from=max(입력)+compute_delay·미실현 3-state / back-adjust(선물·ETF Adj Close)=lookahead→forward-only 합성·저장금지 / 거시 realtime vs final 라벨 / FDR decision_time 불변·bitemporal·discovery vs retest 분리 / sink만 분기 promotion_record / 단일 UTC+거래소 calendar PIT.
- claude retrofit급(R2 A~G, R3 #1#2): FX 통화 first-class·CA 별도 ledger·PSID 식별자·tradability·calendar·compute_delay stamp·FDR 결정성 / R3 미해결 2(universe membership·vintage open-sequence) = **event-ledger 계약이 해소**.
- gemini: R3 수렴 선언. minor 2(tick_size/multiplier·ETF Net/Gross TR) 반영함.
- 판정: **수렴**(유의미 개선점 소진, 잔여=계약 텍스트 lock + minor 속성).

## 4. ★ 3자 schema 합의 표면 (btn-Codlearn 회신 대상)
내 outcome_ledger = btn-button 11-event ledger **그대로 채택, 충돌 없음**. 확인 필요 interface:
(a) FX currency/fx_convention/fx_vintage = OUTCOME_OBSERVED payload 권장(공통필드 승격 아님). (b) terminal_reason/terminal_value = OUTCOME_OBSERVED payload. (c) universe_id = 별도 substrate 참조(ledger 비포함). (d) data_vintage 공통필드 = 내 vintage open-sequence 의 vintage_knowable_from. (e) config_hash = compute_delay+derivation_fn_version stamp. (f) CA/vintage 정정 = substrate bitemporal 테이블(이벤트 아님), ledger 는 data_vintage 로 참조.

## 5. 구현 순서 (Walking Skeleton — btn-button R5 + 전체구조 3R 보강)
① event_ledger reducer + **12 event** dataclass(+REVISION_OBSERVED) + **3 typed timestamp(tt/dt/vt)** + **CQRS(snapshot+watermark)** + dummy-event 랜덤순서 TDD(tt-cut state 100% 복원) — 인프라만. ② data_contract(+**ingestion checksum silent-rewrite**) + identity + calendar substrate. ③ instrument_source(crypto MVRV 최소) + fx + outcome resolver + **REVISION_OBSERVED resolver** → 최소 backtest closed-loop(crypto MVRV 7d). ④ universe_membership·CA·vintage·panel 확장·lineage. ⑤ promotion_gate_live(**fill 내생성**) + d4. 로직+인프라 동시 테스트 금지. self-test: `PYTHONIOENCODING=utf-8 PY -m core.data.X`.
- ★**적대적 PIT replay = 1급 CI 게이트**(자문 #3·#R3): OUTCOME+REVISION 에 taint-tag → as-of-A(t0≤A<t1) 산출에 tainted 0건 assert + revision 물리부재 oracle 과 byte-identical. 전 seam 관통(storage→reducer→read-model→signal→FDR→sizing). 시나리오: 지연개정·동일vt 다중개정·결정창 중간도착·이미소비 fact 개정. reducer 결정론보다 강한 **시간적 결정론**. → P3 closed-loop 직후 P6 에서 게이트화.
- ★**property-based test = R5 practical-saturation 유일 material 잔여**(V&V/코드 정합성): 수식이 맞아도 reducer/e-allocation **코드 버그**면 全보증 silent 붕괴(엔지니어링≠통계, 질적 직교). adversarial PIT replay 는 부분커버 → **랜덤 valid 이벤트열 생성 → state/wealth 불변식 검증**(①tt-cut 결정성 ②입력순서 무관 ③watermark 단조 ④FDR dt-순 동결 ⑤append-only 보존). P1-보강(reducer)에서 선반영, P6 에서 e-allocation 확장. + 인프라 DR(거래소 API 장애 이중화)=모델 밖, go-live 운영. **자문 5R = practical saturation(잔여=V&V·DR), 이후 추가 자문 ROI 음 → 구현/운영 규율 이행**.

## 6. 환경
python `/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe`, **pandera 0.31.1 설치됨**(`import pandera.pandas`). 기존 코드: core/data/{pit_query,pit_panel,corp_action}, core/structure/{panel_schema,online_fdr(LORD++ 메모리),detectors,assumption_stats}, core/pit/as_of, core/rules/{ledger,seed_builder,signal,bitemporal_store}, core/book/d4_book, core/observability/kill_switch. 계약: T3 assumption_store.is_active(id,ver,as_of).

## 7. 부수 산출 (이 세션) — 외부 자문 runner 수리 (전역 스킬 코드)
`~/.claude/skills/gemini-web-consult/runner.js` + `claude-web-consult/runner-basic.js`: (1) 매 send 새 창+새 대화(Target.createTarget newWindow + waitForEvent('page'), 끝에 page.close) — 동시 세션 격리. (2) anti-throttle Chrome 플래그 + bringToFront. (3) claude waitForResponse 재작성 = 무성장 STABLE_MS=6s + tolerance 4(완료후 micro-oscillation 무시→timeout 대기 버그 해소), getLatestResponseText 가 .standard-markdown 없으면 '' 반환(Opus4.8 thinking 텍스트 오인 차단). 문법검증 + claude R2/R3 7534/4682자 완전회수 실증.
