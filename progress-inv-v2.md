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

## R15 가중학습 — 데이터/PIT 분담 (CONSULT-DECISIONS-weight-20260529.md §4 btn-Inv)
> 설계 SSOT=`CONSULT-DECISIONS-weight-20260529.md`(3R saturation 확정, §1 고정). 내 분담=데이터/PIT 영속만(통계 추정=btn-button, 오케스트레이션=btn-Codlearn). 자문 스킵 OK(확정 reference 구현, btn-Codlearn 확인). 막히면 단발 자문.
> 경계: 카드 weight_vector 의 *의미/도출*=btn-Codlearn / 카드 *저장·조회·PIT 무결성*=나. 학습 입력 *추정*=btn-button / 입력 *PIT 공급·분할·게이트*=나.
- [x] **W1** `core/data/weight_panel.py`(신규) — 지표 패널 PIT 공급(§4-1): VintageStore→as_of 시점 다series×시계열 매트릭스(glasso 학습 입력, realtime 값=개정 누수 차단) + ★반사성 게이트(§1.8·§4-4 과거 포지션/체결/PnL 유래 컬럼 배제, 외부 지표 시계열만). self-test 4/4 PASS(as_of 개정반영·PIT 누수차단 03-01 속보·반사성 4종 거부+over-reach 방지 word-boundary[book_value/trade_volume 통과]·미공표 NaN graceful). 회귀: 신규 독립 모듈(기존 import 0, VintageStore read-only 소비). `model: opus`.
- [x] **W2** `core/data/weight_card_store.py`(신규) — §1.7 WeightCard bitemporal 영속(§4-2): WeightCardRecord(knowledge_time=학습데이터 PIT경계 / decision_time=시스템 반영 / sys_time) append-only + `V(T)=knowledge_time≤T & decision_time≤T & embargo 충족 최신 카드` selector + hash-pin frozen(replay). event_ledger 패턴 차용(append-only+watermark+jsonl/fsync, ⛔본체 변경 0), 카드 weights=불가지(btn-Codlearn 소유). self-test 7/7 PASS(emit·V(T) 이중축 반영전 미가시·embargo 위반 emit 거부·re-fit 신규버전 과거불변·hash-pin frozen·jsonl round-trip·미존재 None). 회귀: 신규 독립 모듈(event_ledger import 0). `model: opus`.
- [x] **W3** `core/data/cv_split.py`(신규) — §1.8 purged+embargo CV split(§4-3): purged k-fold + Combinatorial Purged CV(CPCV, §3 차용) + embargo(전이구간 누수 차단), 순수 numpy(⛔mlfinlab 금지=라이선스, López 알고리즘 자체구현). label-horizon 겹침 purge + test 직후 embargo. self-test 6/6 PASS(분할 불변식·purge overlap 0·embargo 직후 0·point/horizon purge 차이·CPCV C(6,2)=15 다중 path·라벨구간 위반 거부). 회귀: 신규 독립 모듈. `model: opus`.
- [x] **W4** `core/data/cold_start_ood.py`(신규) — §1.9 cold-start OOD 감지 데이터(§4-5): calibrated max-belief<θ OR feature가 regime centroid Mahalanobis(d²>χ²(p,1−α)) 밖. 순수 numpy/scipy. live override 아님=감지 신호(데이터)만(§1.9 (a) 기계 de-risk default). self-test 6/6 PASS(max-belief·Mahalanobis 근/원·통합·두축 동시·χ² threshold 정합·per-regime precision nearest). 회귀: 신규 독립 모듈. `model: opus`.
- [x] **W5** `data_contract.py` 확장(추가만) + `lineage.py` 비중 provenance — `check_weight_card`(scope 키·weight finite/비영/cap·PIT 단조·embargo·옵션 hash 무결성, duck-typed=weight_card_store 역의존 회피) + `emit_weight_card_lineage`(기존 emit 재사용, output_id 규약+ProvenanceRef). 기존 계약 byte-불변. self-test: data_contract 11/11(기존 8 회귀 무손상+WeightCard 3) / lineage 6/6(기존 5+가중카드 provenance PIT). `model: opus`.
- 회귀: W1~5 전부 신규 독립 모듈/추가만(기존 16모듈 import 0 변경, data_contract/lineage 추가만=기존 self-test 무손상) — 직교 확인.
- **R15 데이터/PIT 분담 완료(2026-05-29)**: 신규 4모듈(weight_panel/weight_card_store/cv_split/cold_start_ood) + 2확장(data_contract/lineage). 전수 회귀 PASS/0 FAIL. 커밋 git 79217ee(7파일 pathspec 격리).
- **★R15 3세션 통합 완료(2026-05-30, btn-Codlearn 회신 수령)**: 내 weight_panel matrix(시점×지표, IndicatorPanel 형상) → GlassoWeightLearner wire 완료. 통합 closed-loop + production 오케스트레이터(미배선 4 seam) 완료 — self-test 12/12, pytest 61 passed 0회귀, btn-Codlearn 커밋 817791d. 내 데이터/PIT 계층 변경 0 보존. **R15 종결.**

## Working Notes
> 인계(종합 맥락): [DESIGN-inv-v2.md](./DESIGN-inv-v2.md) (설계+자문요약+runner수리), [plan-inv-v2.md](./plan-inv-v2.md). 자문 raw=.consult-inv-R1,R2,R3.txt. R15 설계=CONSULT-DECISIONS-weight-20260529.md.
> [ckpt-202605300130:btn-Inv] **★전체 readme.md 완성 — 다음=프로젝트 보완/우려 자문 3R.**
> (1) 마지막 결정: readme.md 전면 교체 완료(기존 셋업가이드 삭제 → architecture.md+ARCHITECTURE-brain.md 골격 + 6 기능영역 subagent 병렬 종합[두뇌/데이터PIT/가정통계/실행결정/레거시실행/주식백테스트] + brain 보완[regime_belief_adapter·correction_loop·indicator_event_correlation·rag_pit·llm_provider 등 ARCHITECTURE-brain.md 누락분 코드기준 채움] + Phase표/안전장치/디렉토리맵). 각 영역 설계결정 이유=자문 md(CONSULT-DECISIONS-*·architecture.md·MACRO_CORRELATION_BACKGROUND.md) 인용, 근거 미발견은 추측 대신 표기.
> (2) 다음 의도: **압축 후 자문 3R 실행** — 전체 readme.md 내용으로 프로젝트 보완점/우려사항 gemini-web+claude-web 병렬 3라운드 → 심각도별 패치 고려 → 패치 없으면 주요 기능 테스트(사용자 지시 2026-05-30). 자문 브리프 베이스=readme.md 6 기능영역 + 6대 불변식(down-only·falsification·PIT replay·floor 분리·학습/적용 분리·opt-in off).
> (3) 동기화 필요: README/자문 작업은 v2(6386ccf)·R15(79217ee, 통합 817791d) 완료·커밋과 별개 주제. 6 subagent 결과는 압축 전 readme.md 에 영속됨(컨텍스트 유실돼도 파일이 SSOT).
> [ckpt-202605300040:btn-Inv] **★R15 3세션 통합 종결 — 추가 빌드 없음.**
> (1) 마지막 결정: R15 데이터/PIT 분담 5단계(W1~5) 완료·커밋(git **79217ee**, 7파일 pathspec 격리=멀티세션 공유 index race 우회). btn-Codlearn 통합 완료 회신 수령 — weight_panel matrix(시점×지표, IndicatorPanel 형상)→GlassoWeightLearner wire, 통합 closed-loop+production 오케스트레이터(미배선 4 seam) self-test 12/12·pytest 61 passed 0회귀(btn-Codlearn 817791d). 내 데이터/PIT 계층 변경 0 보존.
> (2) 다음 의도: **R15 완전 종결**. v2(6386ccf)+R15(79217ee) 전 커밋. 신규 분담/통합 요청 시 재개. ⛔루트 progress.md 건드리지 말 것(btn-Inv SSOT=본 파일).
> (3) 동기화: 3세션 R15 통합 확인 — btn-button 통계 7543463(glasso/belief-mix) / btn-Codlearn 카드 87655fe+통합 9d70a84+오케 817791d / 내 데이터 79217ee. 공유 index race 패턴=add→연속 commit pathspec(-m 먼저, -- 뒤 경로) 으로 격리.
> [ckpt-202605300030:btn-Inv] **★R15 가중학습 데이터/PIT 분담 완료** (v2 P0~P6 는 git 6386ccf 커밋 완료).
> (1) 마지막 결정: R15 §4 btn-Inv 분담(자문 스킵=확정 reference 구현, btn-Codlearn 확인) 5단계 W1~5 완료. 신규 4모듈+2확장, 전수 회귀 **19 PASS/0 FAIL**. event_ledger 본체 변경 0(회귀 보존) — 카드 영속은 별도 store 가 그 패턴 차용.
> (2) 다음 의도: **R15 데이터/PIT 구현 완결**. btn-Codlearn 통합 대기. 배선 합의점 2: ⓐ WeightAssumptionCard(btn-Codlearn registry 서브타입) ↔ `WeightCardStore.emit(card_id,regime,archetype,period,weights,knowledge_time,decision_time,embargo_days,...)` (weights=opaque, V(T)=select(card_id,as_of)). ⓑ b(t)/calibration frozen(§1.6) ↔ `model_hash` pin(카드 hash 에 포함=replay 재현). ⓒ glasso 학습 입력 ↔ `weight_panel.build_indicator_matrix(vintage_store, series, periods, as_of)` (반사성 게이트 통과) + `cv_split.purged_kfold_splits/combinatorial_purged_splits(t_start,t_end,n_splits/n_groups,embargo_days)` + `cold_start_ood.detect_cold_start_ood(belief,feature,centroids,precisions)`. 신규 미커밋(사용자 지시 대기).
> (3) 동기화 필요: btn-button(통계 §1.1/1.2/1.6 추정·calibration·IC 검정력) = 내 weight_panel 매트릭스 + cv_split 인덱스 + cold_start_ood centroid/precision 소비. btn-Codlearn(§1.5 카드 정의·§1.3 derivation·§1.4 L1 주입·DUAL falsification) = 내 weight_card_store 영속 + check_weight_card 게이트 소비. PY/self-test 명령 동일(상단).
> [ckpt-202605292350:btn-Inv] **★v2 구현 전 완료 — P0~P6 + 보강 5+2 반영, 16모듈 self-test PASS/0 FAIL, IA-1~6+V&V GATE 충족, btn-Codlearn 최종보고 전송.**
> (1) 마지막 결정: 3자 ack 도착(event-ledger 채택+보강 5+2 빌드전 필수) → DESIGN/plan/progress 반영 후 전 phase 빌드. ledger 본체=12 event(+REVISION_OBSERVED)·3 typed timestamp(tt/dt/vt)·CQRS. 신규 16모듈(core/data 13 + panel_schema 확장 + d4_wire + adversarial_replay). R5 practical-saturation 유일 material 잔여=V&V → property-based(60trial×5불변식) + 적대적 PIT replay 1급 게이트(시간적 결정론, 4 시나리오) 구현. long-mode ON(이번 세션 재ON, compact 시 원복).
> (2) 다음 의도: **구현 완결 — 추가 phase 없음**. 잔여=전부 go-live 게이트(자율 범위 밖): 실데이터 라이브 왕복(CoinMetrics fetch_live=N-P3-CM, FRED/ECOS), 다도메인 라이브 closed-loop, d4_book 라이브 LLM 주입(N-INT 브리지), 실거래 flip. btn-Codlearn 통합 회신 시 대응. 미커밋(전 신규 파일 untracked) — 사용자 커밋 지시 대기.
> (3) 동기화 필요: btn-Codlearn=lifecycle emit(ASSUMPTION_CREATED/CANDIDATE_PROPOSED/RATIFIED/TRANSITIONED/RETIRED/CALIBRATION_CHANGED)+state 소비, e-allocation property test·online e-process backbone=T3 e-substrate 영역 / btn-button=read-only 소비. 나 emit=PREDICTION_MADE/OUTCOME_OBSERVED/REVISION_OBSERVED/HOLD_REMEASURED/FDR_DECISION/DATA_CONTRACT_VIOLATION. make_event(event_type,tt=,dt=,vt=,seq=,asset_class=,assumption_id=,payload=) 팩토리. PY=`/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe`. self-test=`PYTHONIOENCODING=utf-8 PY -m core.data.X`. ⛔ 루트 progress.md·progress-assumption-v2.md 건드리지 말 것.

> [ckpt-202605292120:btn-Inv] (이전) 자문 수렴 + 설계/plan/progress + P0 전달 + substrate 2모듈 착수. (압축 전 — 상위 ckpt 가 갱신.)
