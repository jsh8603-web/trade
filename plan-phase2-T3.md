---
tags: [type/plan, domain/inv, phase/II, track/T3]
date: 2026-05-29
session: btn-Codlearn
findings: ./FINDINGS-phase2-sector-rule-framework.md
spec: ./SPEC-T3-rule-governance.md
impl_outline: ./IMPL-OUTLINE-phase2.md
split_index: ./SPLIT-INDEX-phase2.md
progress: ./progress-phase2-T3.md
note: T3(rule·승격·거버넌스·관측) 구현 + 통합·wiring 계획. 자율주행. 압축 survive 목적 상세.
---

# PLAN — Phase2 T3 (rule·승격·거버넌스·관측) 구현 + 통합

> ⛔ 이 plan 은 btn-Codlearn(T3) 전용. progress SSOT = `progress-phase2-T3.md`.
> ⛔ 기존 `progress.md` 는 btn-Inv(Phase I/II) 소유 — **건드리지 말 것** (충돌 회피, 별도 파일 분리).
> 자율주행 ON: 압축돼도 progress 의 미체크 step 부터 재개. 멈추지 않고 끝까지.

## 0. 한 줄
T2 의 `cheapness_z`(싸다=구조모델 잔차)를 **rule 로 조립·승격·적용·관측·통제**한다. L1 결정론=불가침 veto floor, rule=soft 의견만, 변경은 OOS 게이트+사람 비준, 안전은 kill-switch+grandfather. 실자산 — shadow-only 부터.

## 1. ★ 확정 인터페이스 계약 (압축 survive — 재확인 불요)

T1·T2 산출물을 직접 읽어 확정 (2026-05-29 btn-Codlearn 검증):

### 계약 #1 — 패널 schema (T1→T2,T3) · `core/structure/panel_schema.py`
COL_* 상수로 컬럼 접근. structure_model 이 쓰는 것 확인됨:
- `COL_FIRM` `COL_SECTOR`(as-of) `COL_DATE` `COL_KNOWABLE_FROM` `COL_MULTIPLE` `COL_REGIME`(int) `COL_MULT_DEF_VER` `COL_DELIST_FLAG` `COL_DELIST_RET`(추정)
- `ps.driver_columns(panel) -> list[str]` (드라이버 컬럼 추출)
- `ps.make_semiconductor_fixture() -> pd.DataFrame` (T1 실패널 미도착 시 mock)
- ⚠️ T1 실패널 미도착 → fixture 로 개발, 도착 시 동일 schema 로 교체.

### 계약 #2 — cheapness_z (T2→T3) · `core/structure/structure_model.py`
- `StructureModel(StructureModelConfig).fit(panel, as_of) -> FittedStructure` (purged/expanding OOS, knowable_from ≤ as_of − purge_days)
- `.cheapness_z(firm, sector, date, as_of) -> float` (음수 클수록 저평가, 미관측=NaN)
- `.cheapness_z_rows(rows: pd.DataFrame) -> np.ndarray` (행 단위 배치)
- `.expected_multiple(rows) -> np.ndarray`
- ⚠️ **as_of 를 `pd.Timestamp()` 로만 정규화** — 미래거부·tz 정규화 없음 → T3 canonical resolver 가 그 갭을 메우고 cheapness_z 호출을 감싼다 (계약 #0).

### 계약 #3 — ArchetypeCard (T2→T3) · `core/structure/archetype.py`
- pydantic v2 discriminated union (판별자=`archetype`), frozen. 5종: cyclical/event_driven/spread_driven/asset_stable/compounder.
- 필드: `primary_metric` `companion_signals[]` `value_trap_guards[]` `valid_from`(시변) `percentile_overfit_risk`(bool) `cheapness_sign`("low_multiple"|"expensive_trap").
- `parse_card(dict) -> ArchetypeCard` / `archetype_for_sector(sector) -> str` / `load_cards_from_config() -> {archetype: card}` / `DEFAULT_SECTOR_ARCHETYPE` / `ARCHETYPE_NAMES`
- ★ compounder.cheapness_sign="expensive_trap" (함정이 비싼 쪽). cyclical.percentile_overfit_risk → L1 dispatch 분기.

### 계약 #0 — canonical as_of resolver (T3 신규, 공통 primitive)
- 두 세션(btn-Inv/btn-button)에 통지 완료: "T3 가 먼저 구현해 공유, 자체 as_of 해석 금지" (claude R7 reconcile 발산 방지).
- T3 가 `core/pit/as_of.py` 에 구현 → T2 cheapness_z 호출 직전 as_of 정규화. 기존 컨벤션=`macro_vintage.py`(as_of: datetime, `as_of.date() > date.today()` → reject, ALFRED realtime).

### 기존 시스템 seam (wire 판정, 검증됨)
- `stock/valuation.py`: `value_stock(:244)`, `multiple_band(:202)`=raw 분위(현 설계), `sector_ev_ebitda hook(:247)`=real 이나 미주입(죽은 hook).
- `stock/value_trigger.py`: `Gate1Thresholds(:55)`.
- `core/risk_gate.py`(RiskGate, 라이브), `core/consensus.py`(primitive), `core/regime/`(빈 패키지, regime_classifier 는 core/brain).
- `scripts/run_agents.py:873` `INV_CORE_GATE` opt-in 브리지 — `core.risk_gate.RiskGate`+`core.brain.memory_layer.MemoryLayer` 라이브 호출(코인). **T3 주입은 이 패턴 증분.** (E97 latch 검증 완료 2026-05-29)
- `scripts/run_agents.py` MAX_* / `execute_trade.py:346-480` — Token Bucket kill-switch seam.
- ⚠️ blocker: **StockTrack 가동 미인스턴스화**(주식 경로 죽음, run_agents=코인전용) = btn-Inv Phase I WP5 영역. T3 가 직접 건드리지 않고 shadow-only 로 가다 WP5 완료에 매단다.

## 2. ★ T3 모듈 구현 순서 (v1 DAG, 각 코드레벨 명세)

각 모듈 = `if __name__=="__main__"` self-test 필수 (fixture 기반, T2 패턴 동일). 불변식 4 준수.

### S0. `core/pit/as_of.py` — canonical as_of resolver (계약 #0)
- `resolve_as_of(x, *, now=None) -> pd.Timestamp`: str/date/datetime/Timestamp → tz-naive UTC Timestamp 정규화. 미래(`> now or today`) → ValueError(lookahead 거부). None → 정책상 reject (명시 as_of 강제).
- `knowable_filter(panel, as_of) -> pd.DataFrame`: `panel[COL_KNOWABLE_FROM] <= resolve_as_of(as_of)`.
- `cheapness_z_safe(model, firm, sector, date, as_of) -> float`: as_of·date 를 resolve 후 T2 `model.cheapness_z` 호출 (계약 #2 갭 보강 어댑터).
- self-test: 미래 as_of reject / str·date·datetime 동일 결과 / filter row 수.

### S1. `core/rules/signal.py` — versioned signal + EffectiveRule + resolver
- `Signal`(pydantic frozen): `id` `version` `archetype` `predicate`(DSL str) `direction`(±) `threshold`(τ) `effective_from` `knowable_from` `weight`.
- `WeakRuleEnsemble`: signal 리스트, ∑발동 ≥ `quorum`(기본 4) → trigger. 결측·노이즈 강건(monolithic 회피, B6).
- `EffectiveRule`(dataclass): resolve 결과 — 발동 signal 목록 + 합산 score + veto 여부 + deciding_rule_id.
- `rule_resolver(sector, decision_date, as_of, cards, signals) -> EffectiveRule`:
  archetype dispatch(archetype_for_sector) → 해당 archetype signal 만 → bitemporal(effective_from≠knowable_from, knowable_from≤as_of) → 앙상블 평가.
  ⚠️ 부호충돌(일부 +/일부 −) → abstain. value_trap_guard veto > 앙상블(veto 우선, R8).
- self-test: fixture signal 로 quorum trigger / veto 우선 / abstain.

### S2. `core/rules/bitemporal_store.py` — rule bitemporal store
- append-only(불변식②). `signals/{id}/{ver}.yaml` + in-memory index. effective_from(적용)·knowable_from(알게된시점)·invalidated_at(soft-delete, G5).
- `as_of_query(id, as_of) -> Signal|None`: knowable_from≤as_of & not invalidated. PIT 강제.
- rollback = 새 knowable_from row append(옛 row mutate 0, G5 claude). 
- self-test: append→as_of_query 과거시점 재현 / soft-delete 후 과거조회 불변.

### S3. `core/rules/promotion_gate.py` — G0~G6 승격
- `G0` 사전등록(pre-registration id 발급) → `G1` effect floor + BH FDR(statsmodels `multipletests(method='fdr_bh')`, ⚠️ 전역 multiplicity=LLM 제안 전체 후보 분모, Alpha Spending) → `G2` 국면안정(regime별 IC 부호 일관) → `G3` purged+embargo walk-forward(skfolio `_combinatorial` CPCV) → `G3.5` 비용/유동성/슬리피지 → `G4` PBO≤0.2(skfolio CPCV PBO + PSR/DSR) → `G5` shadow → `G6` 사람 비준.
- `EvidenceCard`(자동 생성) → `rule_evidence.jsonl`. anchoring=LLM 변수·방향만, τ=라벨 에피소드 적합 P/R(Pydantic strict schema, 환각 방어 R8).
- 차용: skfolio `_combinatorial.py`(BSD, mlfinlab stub 대체), statsmodels fdr_bh, rubenbriones PSR/DSR(~40줄).
- self-test: 가짜 signal 이 G1 FDR 통과/탈락 / PBO 계산 / EvidenceCard 직렬화.

### S4. `core/rules/ledger.py` — 2-ledger (E축)
- `decision_ledger`(immutable: "이 숫자가 실제 행동을 일으켰나"=freeze) / `analysis_ledger`(recompute, counterfactual, version 태그). `version_basis` ∈ {frozen, counterfactual}.
- `rule_performance`(version×regime×sector×regime_model_version) append-only. dormant rule 부활 매트릭스(regime_model_version 필수).
- self-test: decision freeze 불변 / analysis 소급 재계산 / dormant 부활.

### S5. `core/rules/l1_gate.py` — L1 결정론 veto floor (C축, 주입 핵심)
- archetype dispatch(계약 #3): cyclical→cheapness_z(잔차) 우선·percentile_overfit_risk 시 raw분위 경고 / event_driven→멀티플 percentile 무력화 / compounder→cheapness_sign="expensive_trap"(저멀티플≠기회).
- `l1_verdict(firm, sector, date, as_of, model, card, rule) -> Verdict`: hard veto floor(불가침) → rule 은 floor 허용공간 내 soft scoring 만. 우선순위 **하드리스크 > L1 veto > rule signal > default**.
- value_trap_guard veto > 앙상블. 부호충돌 → abstain.
- self-test: veto floor 가 rule 을 못 넘게 / archetype별 dispatch / 밸류트랩 veto.

### S6. `core/observability/rule_observer.py` — RuleObserver 5지표 (F축, RO)
- ①decision agreement rate(shadow vs live) ②signal staleness(as_of−knowledge_date) ③residual drift pctile(PSI+0근방질량) ④veto/force-include 빈도 ⑤archetype별 활성도.
- ★ **divergence(shadow↔live)=1차 방어선**(R6 claude). fast-path alert(Page-Hinkley/CUSUM + agreement 급락 + abstention spike, 큐와 분리).
- Rule-level Stop: 룰 누적 OOS MDD −5% → Mute.
- ⛔ **관측 read-only — 제어 직접 못 건드림**(모듈 4분리).
- self-test: 지표 계산 / divergence 임계 / Mute 발화.

### S7. `core/observability/rule_attributor.py` — 반사실 PnL (F축)
- Trade Tagging(주문에 trigger_rule_version 태깅) → PnL_rule = PnL_actual − PnL_baseline(floor/ceiling만), Shapley-lite.
- ⚠️ **veto 가 entry 막으면 기여=음수(0 아님), opportunity cost 별도 계상**(불변식④).
- self-test: tagging / opportunity cost 음수 계상.

### S8. `core/observability/kill_switch.py` — Token Bucket (G축, 불변식③)
- 섹터당 일일 최대주문·일 최대턴오버(3%) 물리한도. 초과 시 신호 100% veto. rule engine ⊂ emergency_stop(우회불가, producer 지 override 아님).
- rule 오작동(주문율 spike·agreement 붕괴) → auto_emergency 자동발화.
- seam: execute_trade.py:346-480 MAX_* + core/risk_gate. WIRE-READY.
- self-test: 토큰 소진 후 veto / emergency 자동발화.

### S9. `core/rules/consensus.py` (또는 core/consensus.py 증분) — 변경 트리거 (D축)
- 잔차 drift(PSI+0근방질량)→재검토큐(자동변경X). ⚠️ regime 먼저 판별→동일레짐 내 drift 만(무한루프 방지 R7).
- Proposer-Challenger-Arbiter: 텍스트 토론으로 상수 변경 금지 → 백테스트 OOS 개선 증명 시만. 변경폭 cap(±1std/±20%)+hysteresis+분기1회 batch.
- 토너먼트 가지치기(T1 BGE cosine>0.85 → T2 OLS t>2 → T3 full backtest top-5%).
- self-test: drift 트리거 / regime 선행 / cap 적용.

### S10. `stock/valuation.py` RuleProvider 래핑 — 통합 (additive, shadow-only)
- `RuleProvider`: value_stock(:244) 를 Provider 뒤로. sector_ev_ebitda hook(:247) 부활 OR 삭제 명시결정(부활 권장). cheapness_z + L1 veto 주입. **shadow-only**(verdict 기록만, 실주문 미변경).
- self-test: shadow verdict vs 기존 value_stock 비교 로그.

## 3. ★ 통합·wiring 계획 (thin live slice, INV_CORE_GATE 패턴)

순서(IMPL-OUTLINE §6, 불변식③ 먼저):
1. **kill_switch(S8)** → execute_trade Token Bucket(INV_CORE_GATE 확장, 불변식③ 먼저). WIRE-READY.
2. **structure_model 오프라인 + T2-7 검증**(button 소유, fixture=GO/STOP). ⚠️ 실데이터(T1) 도착 시 재실행 — STOP 이면 잔차 reframe 재검토(전제붕괴).
3. **RuleProvider(S10)** 가 value_stock 래핑(cheapness_z+sector_ev_ebitda 주입, shadow-only).
4. **PIT 패널+bitemporal store** → RuleProvider, RegimeClassifier.classify(라이브도달) regime 입력.
5. **StockTrack 가동화(flag, btn-Inv WP5)** → RuleProvider → L1 floor → RiskGate → execute_trade → RuleObserver divergence.
- 주입점 = `run_agents.py:873` INV_CORE_GATE 패턴 증분(try/except 라이브 미크래시, opt-in env). 기존 stock/valuation·execute_trade·risk_gate **폐기금지 증분**.
- ⛔ StockTrack 가동화(step5)는 btn-Inv 영역 — T3 는 shadow-only(step3~4)까지 자력, step5 는 그쪽 WP5 완료 대기.

## 4. 불변식 4 + 모듈 4분리 (전 모듈 준수)
- ①position=entry rule_version 고정 ②rollback=row append만(mutate 0) ③rule engine ⊂ emergency_stop(우회불가) ④opportunity cost(veto 차단분) attribution 명시.
- 모듈 4분리: RuleObserver(관측 RO) / RuleAttributor(반사실 PnL) / RolloutController(bitemporal write) / 기존 emergency(상위 차단). **관측≠제어**.

## 5. 검증·블로커
- 각 모듈 __main__ self-test(fixture). python 경로 = ⚠️ `python` PATH 부재 → 실행 시 venv/풀패스 탐색 필요(`where python`/`.venv`).
- 블로커: ①T1 실패널 미도착(fixture 로 진행, 도착 시 교체) ②StockTrack 미가동(shadow-only 한계, btn-Inv WP5 의존) ③T2-7 fixture=잠정 GO, 실데이터 STOP 시 전제 재검토.
- as_of 보완(계약#0) 두 세션 통지 완료. 나머지 경계 3(regime_id 순환·D4 Book 위치·T2-7 격상)=이 세션 통합 시 흡수.

## 6. 미수렴 경계 3 (통합 시 이 세션이 흡수, 통지 생략)
- regime_id: 패널 schema 가 regime_id 포함하나 regime 분류는 T2 소유 → 순환. 해소=regime 을 T1 매크로 파생 PIT 라벨로 산출 OR 패널서 빼고 T2 join. T3 는 소비자라 둘 중 확정 시 따름.
- D4 Book: 데이터절반(T1 ruptures 분절)+소비절반(T3 L2/L3) 분리. v1 미룸(v2).
- L2 Qwen/L3 BGE: v1 미룸(과설계 회피). v1=L1 결정론+rule+shadow 까지. L2/L3=v2.
