---
tags: [type/progress, domain/inv, phase/II, track/T1, topic/assumption-lifecycle-v2, session/btn-Inv]
date: 2026-05-29
session: btn-Inv
plan: ./plan-inv-v2.md
design: ./DESIGN-inv-v2.md
autopilot: OFF
note: btn-Inv(T1) 데이터·PIT·실거래 안전 v2 구현 진행. event-ledger 본체 + PIT substrate. ⛔ 루트 progress.md·progress-assumption-v2.md(btn-Codlearn) 건드리지 말 것 — 본 파일=btn-Inv 구현 SSOT.
---

# progress-inv-v2 — btn-Inv 데이터·PIT·실거래 안전 v2

> 설계=`DESIGN-inv-v2.md`, plan=`plan-inv-v2.md`. event ledger 계약=`DESIGN-button-v2.md §10.6`(확정). self-test=`PYTHONIOENCODING=utf-8 PY -m core.data.X`.

## 자문 수렴 GATE (통과 — 구현 진입 근거)
- gemini R3 = 수렴 선언. claude R3 = 미해결 gate 2(universe membership·vintage open-sequence) → **event-ledger 계약이 해소**. 유의미 추가 개선점 소진 → 수렴 확정.
- raw: `.consult-inv-R{1,2,3}.txt`. 요약: DESIGN-inv-v2 §3.

## 단계
- [ ] **P0** 3자 schema 합의 회신 + 포인터 전달 (btn-Codlearn) — `model: opus`. DESIGN-inv-v2 §4 interface(FX payload/terminal/universe_id/data_vintage/config_hash/CA·vintage substrate) 회신 + DESIGN/plan/progress·raw 포인터.
- [x] **P1** `core/data/event_ledger.py` — `model: opus`. ★3자 ack+전체구조 3R 보강 반영(CONSULT-DECISIONS-whole §btn-Inv): **12 event**(+REVISION_OBSERVED) + **3 typed timestamp(tt/dt/vt)** 강제 + 공통필드(event_id 결정적 ULID/seq/schema_version/asset_class/parent_event_id/config_hash/data_vintage/crc) + `reduce_events(sorted by (tt,seq), tt_cut)` + **CQRS(tt-cut projection+watermark, append→ack→project)**. **Walking Skeleton self-test 8/8 PASS**: ①random-order(20회) tt-cut state 100% 복원 ②CQRS tt-cut+watermark ③FDR dt-순 immutable replay(동결 결정) ④late OUTCOME(vt과거·tt최신) FDR 시퀀스 불변=wealth 되감기X ⑤REVISION as-of(02-20→2.0/03-20→2.5, OUTCOME mutate X·fact 2건) ⑥jsonl append+fsync→load→reduce 동일+snapshot os.replace ⑦crc 변조탐지 load 거부 ⑧seq 비단조 append 거부. 회귀: 신규 독립 모듈(기존 import 0). flock=Windows 단일프로세스라 append+fsync(멀티writer OS락 후속).
- [x] **P2** `core/data/{data_contract,calendar,identity,fx}.py` — `model: sonnet`. data_contract(Pandera, DATA_CONTRACT_VIOLATION emit + HOLD_SUSPENDED, max_staleness) / calendar(거래소 세션·휴장 bitemporal) / identity(PSID + identifier_history + corporate_action_graph, resolve_psid PIT) / fx(P3 선행 빌드). 4모듈 self-test 전 PASS, 신규 의존 0(pandera 기존 설치 + stdlib). 회귀: 전부 신규 독립 모듈(기존 import 0).
  - [x] `core/data/identity.py` — PSID 발급 + IdentifierRecord(bitemporal) + CorporateActionEdge + resolve_psid(PIT)/identifiers_for/successors. self-test 6/6 PASS(ticker recycling/change PIT·knowable_from·합병 splice 금지·sys_time 정정). 회귀: 신규 독립 모듈(기존 import 0).
  - [x] `core/data/data_contract.py` — Pandera 게이트(범위/PIT 단조성/per-domain staleness). self-test 5/5 PASS(clean equity·per=999 범위위반·sys_time<knowable PIT위반·382일 staleness·clean crypto). 회귀: 신규 독립 모듈.
  - [x] `core/data/calendar.py` — ExchangeCalendar(KRX/XNYS/XNAS/CRYPTO) 거래소 세션·휴장 bitemporal. 단일 UTC 환원(NYSE DST EDT13:30Z/EST14:30Z, KRX 09:00KST→00:00Z) + 휴장 PIT(긴급휴장 공표 전 as_of 미가시) + crypto 24x7 + next_trading_day PIT + sys_time 정정. self-test 6/6 PASS. 신규 의존 0(stdlib zoneinfo).
  - [x] `core/data/fx.py` — FxStore PIT 환율(직접/역/USD삼각). value_date fill-forward + knowable/sys_time 2중 게이트 + bitemporal 정정. self-test 8/8 PASS. 신규 의존 0. (plan 상 P3 항목이나 substrate 독립이라 선빌드.)
- [x] **P2-보강** `core/data/data_contract.py` — ★ingestion checksum: FingerprintStore(series×vt 값 지문) + check/record + scan_for_silent_rewrite. 통지없는 과거값 변경=silent_rewrite incident, 정상 REVISION_OBSERVED 동반=합법(구분). vt lenient 키(분기/월 라벨 허용). self-test 8/8 PASS(최초/동일/silent/revision/scan 혼합). (전체구조 자문 #2)
- [x] **P3** `core/data/instrument_source.py` + outcome/REVISION resolver — `model: opus`. CoinMetricsMvrvProvider(Community v4 무료, fetch_live=go-live N-P3-CM 박제) PIT(get_point/latest_knowable, vintage+정정 2중게이트) + `run_mvrv_closed_loop`(PREDICTION_MADE→OUTCOME_OBSERVED→FDR_DECISION ledger emit, MVRV>hi→mean-revert down 7d). **self-test 6/6 PASS**: ①MVRV PIT 공표전 미가시 ②latest_knowable 미래vt 차단 ③MVRV vintage 정정 as-of ④closed-loop 7예측/7적중/p=0.004/reject(emit) ⑤random-order 동일 state+FDR dt-순 동결 ⑥무lookahead(전 예측 신호 MVRV vt<결정일). REVISION resolver=ledger resolve_fact(#5)+provider get_point(#3) 양측 증명. event_ledger 첫 크로스모듈 통합 OK. 회귀: P1 reducer 불변(reduce_events 재사용, 변경 0).
- [x] **P4** `core/data/{universe_membership,lineage,vintage}.py`(신규) + `corp_action.py`·`pit_query.py`·`panel_schema.py` 확장(추가만) — `model: opus`(연속성). 6모듈 self-test 전 PASS:
  - [x] `universe_membership.py` — bitemporal 멤버십(생존편향 차단: 편출 종목도 그때 멤버면 포함, knowable PIT, crypto 바스켓 first-class). self-test 6/6.
  - [x] `lineage.py` — ProvenanceRef+LineageEvent+replay(as_of 재귀 체인, write-time 동결 config_hash, 순환탐지, 영속). IA-3. self-test 5/5.
  - [x] `vintage.py` — open-sequence realtime/final + revision_drift(자문 R1 #1: backtest-on-final lookahead 노출 정량). self-test 6/6.
  - [x] `pit_query.py` 확장 — synth_knowable_from(max입력+compute_delay) + assert_referential_pit(T3 is_active 계약 dangling 차단). IA-3. self-test 4/4.
  - [x] `panel_schema.py` 확장(추가만) — instrument_kind{equity,etf,commodity,crypto,macro_series,fx}+lifecycle_status+tradability(⊥lifecycle)+coverage/inception+tick/multiplier + validate_instrument_columns. 기존 equity 계약 byte-불변. IA-4.
  - [x] `corp_action.py` 확장 — DistributionLedger(배당 bitemporal, forward-only TR back-adjust 금지, Net/Gross 원천징수, 연말 재분류=sys_time append). self-test 4/4.
  - 회귀: 전 모듈 self-test 12 PASS/0 FAIL(기존 panel_schema equity·corp_action split-adjust 불변).
- [x] **P5** `core/data/promotion_gate_live.py`(IA-5·R12) + `core/book/d4_wire.py`(R8) — `model: opus`. self-test 8/8+6/6 PASS:
  - [x] `promotion_gate_live.py` — PromotionGate(사람게이트: approver 서명+incident 0+regime coverage, kill_switch latch 재사용 사람만 해제, 로직 무분기·execution_mode sink만 분기) + ★ramp(RampLadder geometric c₀·2c₀·4c₀ rung FIX, observe()=ramp e-process null=net-edge≤0 Ville→e≥1/α 전진, capacity ceiling 부호반전, OOB breaker realized impact>band 즉시 halt) + ★safe_flatten_action(crypto=flatten_now/equity 휴장=freeze_and_alert, crypto-only 연속거래 의존 차단). 8/8.
  - [x] `d4_wire.py`(R8) — VintageStore→MacroPeriod·패널→IndustryCharCard PIT 전파(knowable_from=vintage 공표시점) + to_context PIT 소비. 6/6. ⛔라이브 LLM 주입(run_agents)=N-INT go-live, 실 macro=FRED/ECOS go-live 게이트.
- [~] **P6** self-test 전수 + ★적대적 PIT replay 1급 CI 게이트 + ★property-based + IA-1~6 GATE 증거 + btn-Codlearn 최종 보고 — `model: opus`.
  - [x] `core/data/adversarial_replay.py` — 1급 CI 게이트(시간적 결정론): taint isolation(미래 REVISION sentinel 값 as-of-A 0건) + 물리부재 byte-identical(reduce(전체,cut)==reduce(미래제거,cut)) + closed-loop 전 seam 격리. 4 시나리오(지연개정·동일vt 다중개정·결정창 중간도착·이미소비 fact개정) PASS.
  - [x] property-based test = event_ledger #9(P1-보강) 완료.
  - [x] self-test 전수 회귀: **16 모듈 PASS / 0 FAIL**(core.data 13 + core.structure.panel_schema + core.book.d4_book/d4_wire).
  - [x] IA-1~6 + V&V GATE 증거표 채움(위 IA GATE 표).
  - [x] btn-Codlearn 최종 보고 전송(2026-05-29): 16모듈 PASS·IA-1~6+V&V GATE·보강 5+2 반영·go-live 게이트 목록.
  - [x] **P1-보강** event_ledger reducer **property-based test** — 랜덤 valid 이벤트열(60 trial × 5~30 event) 생성기 + 5 불변식(①tt-cut 결정성 ②입력순서 무관 ③watermark 단조 ④FDR dt-순 동결 ⑤append-only 보존=facts==OUTCOME+REVISION 수) 전부 PASS. R5 유일 material 잔여축(V&V/코드정합) 선반영. e-allocation property test=T3 e-substrate 영역.

## IA GATE (self-test 증거 후 [x]) — 전 모듈 16 PASS / 0 FAIL
| 축 | 내용 | 상태 | 증거(모듈·self-test) |
|---|---|---|---|
| IA-1 | 결정→가정 trigger PIT log + outcome join (3+도메인) | [x]* | event_ledger PREDICTION_MADE{assumption_id,version}→OUTCOME_OBSERVED parent_event_id join + instrument_source closed-loop(crypto 7예측 100% outcome join, lineage 역추적). *crypto 라이브 closed-loop PASS, equity/etf/macro=schema-ready(panel instrument_kind + data_contract 5도메인), 다도메인 라이브 closed-loop=go-live(실데이터 게이트) |
| IA-2 | data_contract 게이트=validator 앞단, 측정≠가정 | [x] | data_contract 8/8(범위·PIT 단조·per-domain staleness·★ingestion checksum silent-rewrite) → DATA_CONTRACT_VIOLATION emit, PENDING≠incident 분리 |
| IA-3 | lineage replay + FDR alpha-wealth bitemporal 영속 | [x] | lineage 5/5(as-of 재귀 replay·write-time 동결·순환탐지) + event_ledger FDR_DECISION dt-순 immutable reduce(#3) + pit_query 4/4(synth_knowable_from·assert_referential_pit) + vintage 6/6 |
| IA-4 | 무료 PIT 소스 + 자산 컬럼 + 생존편향(PSID/universe/backfill) | [x] | identity 6/6(PSID·ticker recycling) + universe_membership 6/6(생존편향 차단) + panel_schema instrument_kind 확장 + instrument_source(CoinMetrics Community 무료) + corp_action TR(back-adjust 금지) + fx |
| IA-5 | 모의 outcome 수집 + shadow→live 사람게이트 | [x] | promotion_gate_live 8/8(approver 사람게이트·kill_switch latch 사람만 해제·★ramp e-process·OOB breaker·crypto-only 비의존) |
| IA-6 | 단일 UTC + 거래소 calendar bitemporal | [x] | calendar 6/6(단일 UTC·NYSE DST·휴장 bitemporal PIT·crypto 24x7) + event_ledger 3 typed timestamp(tt/dt/vt) + fx PIT |
| +V&V | property-based + 적대적 PIT replay (R5 유일 material 잔여) | [x] | event_ledger property-based 60trial×5불변식 + adversarial_replay 1급 CI 게이트(taint isolation + 물리부재 byte-identical, 4 시나리오 + closed-loop seam 격리) |

## Working Notes
> 인계(종합 맥락): [DESIGN-inv-v2.md](./DESIGN-inv-v2.md) (설계+자문요약+runner수리), [plan-inv-v2.md](./plan-inv-v2.md). 자문 raw=.consult-inv-R1,R2,R3.txt.
> [ckpt-202605292350:btn-Inv] **★v2 구현 전 완료 — P0~P6 + 보강 5+2 반영, 16모듈 self-test PASS/0 FAIL, IA-1~6+V&V GATE 충족, btn-Codlearn 최종보고 전송.**
> (1) 마지막 결정: 3자 ack 도착(event-ledger 채택+보강 5+2 빌드전 필수) → DESIGN/plan/progress 반영 후 전 phase 빌드. ledger 본체=12 event(+REVISION_OBSERVED)·3 typed timestamp(tt/dt/vt)·CQRS. 신규 16모듈(core/data 13 + panel_schema 확장 + d4_wire + adversarial_replay). R5 practical-saturation 유일 material 잔여=V&V → property-based(60trial×5불변식) + 적대적 PIT replay 1급 게이트(시간적 결정론, 4 시나리오) 구현. long-mode ON(이번 세션 재ON, compact 시 원복).
> (2) 다음 의도: **구현 완결 — 추가 phase 없음**. 잔여=전부 go-live 게이트(자율 범위 밖): 실데이터 라이브 왕복(CoinMetrics fetch_live=N-P3-CM, FRED/ECOS), 다도메인 라이브 closed-loop, d4_book 라이브 LLM 주입(N-INT 브리지), 실거래 flip. btn-Codlearn 통합 회신 시 대응. 미커밋(전 신규 파일 untracked) — 사용자 커밋 지시 대기.
> (3) 동기화 필요: btn-Codlearn=lifecycle emit(ASSUMPTION_CREATED/CANDIDATE_PROPOSED/RATIFIED/TRANSITIONED/RETIRED/CALIBRATION_CHANGED)+state 소비, e-allocation property test·online e-process backbone=T3 e-substrate 영역 / btn-button=read-only 소비. 나 emit=PREDICTION_MADE/OUTCOME_OBSERVED/REVISION_OBSERVED/HOLD_REMEASURED/FDR_DECISION/DATA_CONTRACT_VIOLATION. make_event(event_type,tt=,dt=,vt=,seq=,asset_class=,assumption_id=,payload=) 팩토리. PY=`/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe`. self-test=`PYTHONIOENCODING=utf-8 PY -m core.data.X`. ⛔ 루트 progress.md·progress-assumption-v2.md 건드리지 말 것.

> [ckpt-202605292120:btn-Inv] (이전) 자문 수렴 + 설계/plan/progress + P0 전달 + substrate 2모듈 착수. (압축 전 — 상위 ckpt 가 갱신.)
