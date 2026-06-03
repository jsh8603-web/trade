---
tags: [type/progress, domain/inv, phase/II, track/T3]
date: 2026-05-29
session: btn-Codlearn
plan: ./plan-phase2-T3.md
autopilot: ON
---

# PROGRESS — Phase2 T3 (rule·승격·거버넌스·관측)

> 인계: [plan-phase2-T3.md](./plan-phase2-T3.md) (확정 인터페이스 계약·코드레벨 명세·wiring)
> ⛔ 기존 `progress.md` = btn-Inv 소유, 건드리지 말 것.
> 🚗 **자율주행 ON** — 압축돼도 아래 첫 미체크 step 부터 재개. 멈추지 말 것. 각 step = self-test(fixture) 통과 후 [x].
> 모델: 이 세션(btn-Codlearn, opus 1M) 직접 구현. 설계 판단 포함 모듈 다수 → opus 유지.

## Step (v1 DAG)

- [x] **S0** `core/pit/as_of.py` — canonical as_of resolver (계약#0) · self-test PASS (4입력 수렴·tz정규화·미래/None거부·PIT단조·어댑터 선차단). ⚠️tz: +09:00→UTC drop 으로 날짜 하루 당겨질 수 있음(normalize 비교라 영향 적음, KST 정책시 재검토)
- [x] **S1** `core/rules/signal.py` — Signal(pydantic frozen)+weak-rule 앙상블(quorum4)+rule_resolver · self-test PASS (cheap quorum/trap veto 우선/neutral/bitemporal 제외/compounder expensive_trap veto). veto=trap≥1(R8 보수). abstain=v2(expensive kind 미도입)
- [x] **S2** `core/rules/bitemporal_store.py` — event-sourced append-only store(RuleEvent frozen)+AS-OF 복원 · self-test PASS (as_of별 version/rollback 복귀/append-only event만증가/PIT 당시사실 보존)
- [x] **S3** `core/rules/promotion_gate.py` — G0~G4 통계게이트(BH FDR 전역·PSR·PBO combinatorial)+EvidenceCard→jsonl, G5/G6=NEED_HUMAN · self-test PASS(초기 DSR게이트 과도→정정: DSR은 detail-only, hard gate=PSR≥0.95+PBO≤0.2. sr_variance 추정 v2). 돈flip=사람비준
- [x] **S4** `core/rules/ledger.py` — 2-ledger(DecisionLedger freeze immutable/AnalysisLedger counterfactual version_basis)+RulePerformance(dormant 부활 regime_model_version 필수) · self-test PASS(EXIT=0)
- [x] **S5** `core/rules/l1_gate.py` — L1 결정론 floor+archetype dispatch+rule soft 결합(우선순위 rule trap veto>L1 floor veto>event특례>cheap>neutral) · self-test PASS(EXIT=0, 6case). S0 as_of+S1 rule+T2 cheapz/archetype 통합 입증
- [x] **S6** `core/observability/rule_observer.py` — 5지표(agreement/staleness/PSI+0근방/veto빈도/archetype활성)+divergence 1차방어선+PageHinkley+Rule-Stop mute신호 · self-test PASS(EXIT=0). 관측 RO(집행은 RolloutController)
- [x] **S7** `core/observability/rule_attributor.py` — Trade Tagging+Shapley-lite 균등분배+opportunity cost(veto가 오른거래 막으면 음수기여, 불변식④) · self-test PASS(EXIT=0)
- [x] **S8** `core/observability/kill_switch.py` — Token Bucket(섹터일일주문/턴오버3% 하드리밋)+emergency latch(주문율spike 자동발화·rule 우회불가·해제 사람만, 불변식③) · self-test PASS(EXIT=0). wire seam=execute_trade.py:346-480
- [x] **S9** `core/rules/consensus.py` — 변경트리거(regime 선행→동일regime drift만 R7)+ChangeQueue(자동변경X)+cap(±1std/±20%)+hysteresis+Proposer-Challenger-Arbiter(OOS 입증시만)+토너먼트 가지치기 · self-test PASS(EXIT=0)
- [x] **S10** `core/rules/rule_provider.py` RuleProvider(value_stock 감쌈, additive)+evaluate_shadow(legacy↔rule divergence 기록, shadow-only)+regime변형 수용 · self-test PASS(EXIT=0). archetype 5종 config 로드 확인(=S13 정합 검증)
- [x] **S11** ★ seed 확보: `config/sector_rules/{cyclical,event_driven}.yaml`(signal seed) + `core/rules/seed_builder.py`(load_signal_seeds 실데이터/큐레이션 앵커 + extract_research_keywords LLM hook + SeedRegistry 무한확장 regime override) · self-test PASS(EXIT=0). 다산업=YAML sectors, 다기간=PeriodVariant. ⚠️실데이터 cache 도착시 _sector_multiple 자동override(go-live)
- [x] **S12** ★ D4 Book: `core/book/d4_book.py`(MacroPeriod+IndustryCharCard+D4Book PIT append-only+to_context LLM주입+ruptures segment) · self-test PASS(utf-8). 반도체 공정전환기 PER 일시상승 카드 예시 포함, PIT 누수차단 검증
- [x] **S13** archetype card 검증: config/archetypes/*.yaml 5종 load_cards_from_config 통과(S10에서 확인). cyclical.yaml 정상(value_trap_guards 채워짐). 추가 정합화 불요
- [ ] **INT** 통합 wiring (as_of→T1 set_as_of_resolver=core/data/pit_query.py:28 / kill_switch→execute_trade / RuleProvider shadow / run_agents.py:873 INV_CORE_GATE) · `model: opus` · ⚠️StockTrack 미가동=shadow까지만
- [ ] **VERIFY** 전 모듈 self-test 일괄(PYTHONIOENCODING=utf-8) + 회귀 확인 · `model: opus`
- [ ] **REVIEW** ★ opus 1M subagent 축별 스폰(코드레벨 wiring/미흡 검토) → 통합 보완계획 · `model: opus` · 평가기준=handoff §검토rubric

## ★ 가정(Assumption) 레이어 — 사용자 누락축 보완 (S14~S20, T3 통합)
> 인계: [handoff-T3-assumption-integration-20260529.md](./handoff-T3-assumption-integration-20260529.md) — T1·T2 완료 산출물·계약·7요소 설계·자문.
> T1(btn-Inv)✅ 데이터·PIT / T2(btn-button)✅ 검증·변경통계 / T3 통합 미착수. scope=거시/주식/상품 3도메인.
- [x] **A-T1** 데이터·PIT 리서치+설계 (btn-Inv): Pandera data_contract·OpenLineage·online_fdr 직접구현·3도메인 패널(생존편향)·knowable_from 합성. 계약=T3 `is_active(id,ver,as_of)`. ⚠️상품소스 N-T1-COMMODITY-SRC 미조사
- [x] **A-T2** 검증·변경통계 (btn-button): `core/structure/{detectors,online_fdr,assumption_stats}.py` 25/25 PASS. 계약=`validate_assumption`/`should_change_assumption`/`confidence_to_band`+AssumptionCardLike Protocol
- [ ] **S14** `core/assume/assumption.py` AssumptionCard(frozen, AssumptionCardLike 충족+falsification_metric/half_life/depends_on/status/scope/kind) · `model: opus`
- [ ] **S15** `core/assume/assumption_store.py` bitemporal 재사용+`is_active`(T1계약)+alpha_wealth 영속 · `model: opus`
- [ ] **S16** `core/assume/validator.py` T2 validate_assumption wrap+regime-conditional+T1 data_contract 앞단 · `model: opus`
- [ ] **S17** `core/assume/update_controller.py` T2 should_change+consensus 재사용+의존전파(무효화·epoch topological·DAG 비순환·nogood)+rate-limit→사람 · `model: opus`
- [ ] **S18** `core/assume/derivation.py` seam f({refs})→DerivedParameterSet+seed_builder.derived_from optional(additive)+knowable_from 합성 · `model: opus`
- [ ] **S19** orphaned position 정책(가정 기각→의존 포지션 review/managed-exit, emergency_stop 연결) · `model: opus`
- [ ] **S20** `config/assumptions/{macro,equity,commodity}.yaml` 3도메인 가정 표+통합 self-test(닫힌 루프) · `model: opus`

## ★ 매칭 점검 (사용자 지시 2026-05-29)
> [MATCHING-prompt-vs-impl-phase2.md](./MATCHING-prompt-vs-impl-phase2.md) — 프롬프트 요구 11 ↔ 구현 1:1. 핵심 누락 4 = signal seed YAML·seed 추출 파이프라인·D4 Book·archetype 정합화 → S11~S13 으로 구현.
> 사용자 메모(cyclical.yaml): seed 사전정의 + 파이프라인 무한 학습/확장(다산업·다기간 무한대).

## 의존·블로커 (재개 시 확인)
- T1 실패널 미도착 → `ps.make_semiconductor_fixture()` 로 개발. 도착 시 동일 schema 교체.
- StockTrack 미가동(btn-Inv WP5) → S10 은 shadow-only 까지만, 라이브 step5 는 WP5 완료 대기.
- ✅ python 경로 확보: `/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe` (pandas2.2.3·numpy·statsmodels·pydantic OK). self-test = `"$PY" -m core.pit.as_of` 식.
- T2-7 = fixture 잠정 GO. 실데이터(T1) STOP 시 전제 재검토(button 통지).

## Working Notes
> 인계: [handoff-T3-assumption-integration-20260529.md](./handoff-T3-assumption-integration-20260529.md) — ★가정 레이어 T1·T2 완료 산출물·계약·S14~S20 설계·자문 전문.
> 인계: [handoff-T3-impl-20260529.md](./handoff-T3-impl-20260529.md) — 검토 rubric·T1/T2/T3 분담·재개 포인트.
> [ckpt-202605291815:btn-Codlearn] **가정(Assumption) 라이프사이클 = 사용자 누락축 보완 진행 중.** 세션 느려 종료 준비.
> (1)마지막 결정: T1(btn-Inv)·T2(btn-button) 둘 다 리서치+설계+동작테스트 완료(스텁 아님). T1=Pandera data_contract·OpenLineage·online_fdr 직접구현·3도메인 PIT 패널·`is_active` 계약. T2=`core/structure/{detectors,online_fdr,assumption_stats}.py` 25/25 PASS·`validate_assumption`/`should_change_assumption`/`confidence_to_band` 계약. 자문 R1(gemini+claude) 완료=ATMS+SR11-7+online FDR, TOP3(online FDR/orphaned position/regime base-layer 승격). runner.js claude.ai/code networkidle→domcontentloaded 수정.
> (2)다음 의도: T3 통합 S14~S20 = `core/assume/{assumption,assumption_store,validator,update_controller,derivation}.py` + orphaned position 정책 + `config/assumptions/{macro,equity,commodity}.yaml`. AssumptionCard 는 T2 AssumptionCardLike Protocol(.assumption_id/.kind/.scope/.regime_id/.params) 충족 필수. assumption_store 는 bitemporal_store.py 재사용+is_active. UpdateController 는 consensus 재사용(객체타입 파라미터화). 상세=handoff-T3-assumption-integration-20260529.md §3.
> (3)동기화 필요: 미해결=상품 무료 데이터소스 N-T1-COMMODITY-SRC(확신<80%, 자문 1회 추가 권장). Pandera 신규 설치 필요. 기존 T3 잔여(INT as_of wire/VERIFY/REVIEW)는 가정 레이어와 별개. python=Python312 풀패스.
> [ckpt-202605292030:btn-Codlearn] **S0~S13 전부 구현+self-test PASS** (as_of/signal/bitemporal/promotion_gate/ledger/l1_gate/observer/attributor/kill_switch/consensus/rule_provider/seed_builder/d4_book + sector_rules YAML 2종). Python312 풀패스 검증. 남음=INT(as_of wire 1곳+shadow), VERIFY 일괄, REVIEW(축별 opus 스폰).
> 마지막 결정: ctx 432k·480k 강제 compact 임박 → 검토 agent 스폰은 compact 후(고아화 회피). long-mode ON.
> 다음 의도(compact 후 재개): (1) INT as_of wire = `core/data/pit_query.py:set_as_of_resolver(resolve_as_of)` (2) VERIFY 전모듈 `PYTHONIOENCODING=utf-8 PY -m core.X` 일괄 (3) ★REVIEW = handoff §검토rubric 대로 opus 1M subagent 축별(A~G 7축+seed/D4 집중 1기) 스폰 → wiring깨짐·미흡 조사 → 통합 보완계획 plan/progress 추가 + T1/T2/T3 분담.
> 동기화 필요: as_of resolver=내 core/pit/as_of.py, T1 pit_query.set_as_of_resolver 주입점 비어있음(INT 연결). T2 cheapness_z=core/structure 완료. seed 실데이터=N-T1-SECTORMULT(Damodaran cache, go-live).
