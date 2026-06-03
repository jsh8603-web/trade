---
tags: [type/design, domain/inv, phase/II, track/T3, topic/assumption-lifecycle-v2, session/btn-Codlearn]
date: 2026-05-29
session: btn-Codlearn
plan: ./plan-assumption-v2-axes.md
progress: ./progress-assumption-v2.md
prior: ./handoff-T3-assumption-integration-20260529.md
binding_axes: [CL-1, CL-2, CL-3, CL-4, CL-5]
consult: [./.consult-codlearn-R1-prompt.txt, ./.consult-R1-gemini.txt, ./.consult-R1-claude.txt]
note: T3(btn-Codlearn) v2 설계 — 가정 라이프사이클 오케스트레이션(core/assume) + 판정(L1+L2+L3+DCF) + ATMS/orphaned/decay + closed-loop 통합. 코드레벨 file:function:contract. btn-button card_contract 표면 위에 wire.
---

# DESIGN-codlearn-v2 — 오케스트레이션 + 판정 레이어 (CL-1~5 코드레벨)

> **담당**: btn-Codlearn (T3). **산출**: 본 설계 + 구현 + self-test + **전 세션 최종 통합**.
> **경계**: T2(btn-button)=카드/검증엔진/regime발견/commodity, T1(btn-Inv)=데이터/lineage/실거래. T3=그 위 오케스트레이션·판정·안전·통합.
> **자문**: gemini-web R1 완료(결론 §아래 반영), claude-web R1 프롬프트 작성완료(채널 점유로 발사 보류 — `.consult-codlearn-R1-prompt.txt`).

## 0. 전제 — 확정된 wire 표면 (코드 매핑 증거, 실재 시그니처)

| 레이어 | 파일:함수 | 시그니처 | 소유 |
|---|---|---|---|
| as_of SSOT | `core/pit/as_of.py:resolve_as_of/knowable_filter/cheapness_z_safe` | `resolve_as_of(x, *, now)->Timestamp` (미래·None reject, tz정규화) | **T3(나)·실재** |
| L1 floor | `core/rules/l1_gate.py:l1_verdict` | `(firm,sector,date_,as_of,model,features,signals,cards,cfg)->Verdict(final∈{allow_cheap,veto,abstain,neutral})` | 실재 |
| cheapness_z | `core/structure/structure_model.py:StructureModel.cheapness_z` | `(firm,sector,date,as_of)->float` (regime-conditional σ), `driver_2x2(narr,stat)` | 실재 |
| cheapness_band | `structure_model.cheapness_band` | `(firm,sector,date,as_of)->(z,lo,hi)` | **T2 B2 대기** |
| DCF | `stock/valuation.py:value_stock` | `(fundamentals,quote,sector_ev_ebitda)->ValuationResult(valuation_gap,intrinsic_value,bear/base/bull,wacc)` | 실재 |
| L3 BGE PIT | `core/brain/rag_pit.py:RagPitPipeline.query_similar` | `(query_text,top_k,as_of)->list[dict]` (PIT mask) + `embedder.py` | 실재 |
| 검증엔진 | `core/structure/assumption_validation_engine.py:AssumptionValidationEngine.validate` | `(card,*,realized,predictions,outcomes,assumed_value,regime_ids,current_regime)->ValidationVerdict(holds_now,fdr_significant,by_regime)` | **T2 BB-4 대기** |
| AND-gate | `core/structure/assumption_stats.py:hysteresis_and_gate` | 5조건 AND(FDR∧effect∧dwell∧K∧regime), `is_base_layer=True`→자동차단, `confidence_to_band(conf)->band` | 실재 |
| 카드 계약 | `core/assume/card_contract.py:AssumptionCardLike/BaseAssumptionFields/assert_falsifiable` | Protocol{id,version,kind,scope,domain,falsification_metric,is_base_layer,valid_from,posterior_confidence,band_halfwidth,depends_on,half_life} | **T2 BB-1 대기** |
| regime 승격 | `core/regime/regime_discovery.py:HumanApprovalGate.approve` | `(candidate_id,new_label,approver,rationale)->RegimePromotion` (version bump) | **T2 BB-3 대기** |
| live 학습 | `core/brain/correction_loop.py:LiveCorrelationLoop.attach_to_classifier/harvest_from_jm` | filter≠smoother harvest→ingest | **T2 BB-2 대기** |
| 2-ledger | `core/rules/ledger.py` | DecisionLedger(frozen immutable) / AnalysisLedger(version_basis∈frozen,counterfactual) / RulePerformance(regime_model_version 필수) | 실재 |

**원칙**: `core/assume/__init__.py` + `card_contract.py` = **btn-button 소유** (내가 생성 X, import만). 내 모듈은 그 계약 위에 wire. 검증엔진/regime발견/live루프/commodity = btn-button 랜딩 대기 (§9 의존표).

## 1. CL 갭 (축 → 코드 매핑)

| CL 축 | 목적(plan §2.1) | 현 코드 | 갭(v2 구현) |
|---|---|---|---|
| **CL-1** [B] | 3도메인 공통 Card/Registry/Validator/UpdateController | `assumption_stats`(검증부품)·`ledger`(버전부품) 실재, orchestration 0 | `core/assume/{registry,validator,update_controller,derivation}.py` |
| **CL-2** [C·Q4] | 활성정의→판정 L1+L2+L3+DCF + 신뢰도→band→사이징 | L1·cheapness_z·valuation·rag_pit 부품 실재, 결합 0 | `core/assume/judge.py` (4요소 안전결합) |
| **CL-3** [E] | AND-gate + base사람비준 + ATMS전파 + orphaned + decay | `hysteresis_and_gate` 실재, 전파/orphaned 0 | `core/assume/{dag,orphan_guard}.py` (grace+lazy) |
| **CL-4** [통합] | closed-loop 거시∧주식∧상품 | 부품 산재, end-to-end 0 | `tests/assume/test_closed_loop_3domain.py` |
| **CL-5** [주식/상품] | cheapness_z/archetype 기간·산업 적응 (method §3.5 동형) | structure_model regime-σ·archetype 실재 | derivation 이 scope(sector×period×regime) 조건부 파라미터 산출 |

## 2. CL-1 — core/assume 오케스트레이션

**파일**: `core/assume/{registry,validator,update_controller,derivation}.py` (T3 신규, btn-button card_contract import).

### 2.1 `registry.py` — 카드 보관 + 버전 + 진입게이트
```python
class AssumptionRegistry:
    """3도메인(macro/equity/commodity) 카드 통합 보관. 버전드. PIT 조회."""
    def register(self, card: AssumptionCardLike) -> None:
        assert_falsifiable(card)              # btn-button 진입게이트 (반증불가=거부)
        # (id, version) 키. 같은 id 새 version = 이전 valid_to 마킹 (S→S' 전환)
    def get(self, id: str, as_of) -> AssumptionCardLike | None:   # valid_from≤as_of 최신 version
    def get_version(self, id: str, version: str) -> AssumptionCardLike  # PIT replay 용 정확 버전
    def active(self, domain=None, scope=None, as_of=...) -> list   # 활성 카드 surface (judge 입력)
    def dependents(self, id: str) -> list[str]                     # depends_on 역색인 (ATMS)
```
- 버전 전환 = append-only (ledger 철학 동형). 카드 id 불변, version bump = S→S' 정의전환.
- `dependents` = `depends_on` 역인덱스 캐시 (DAG 전파 O(1) 조회).

### 2.2 `validator.py` — 검증엔진 dispatch + 결과 영속
```python
class AssumptionValidator:
    def __init__(self, engine: AssumptionValidationEngine, perf: RulePerformance): ...
    def validate(self, card, evidence, *, regime_ids, current_regime) -> ValidationVerdict:
        # 0) ★per-domain alpha-wealth: engine 의 LORD++ 스트림을 card.domain 별 격리 키로 (claude R1)
        #    pooling 시 noisy commodity 가 macro 발견 starve → domain(또는 family) 별 wealth pool
        # 1) engine.validate(card,...) → holds_now/fdr_significant/by_regime (T2 BB-4)
        # 2) perf.log(card.id_as_rule, regime, sector, regime_model_version, ic, n)  ← 축A 영속
        # 3) return verdict (UpdateController 가 소비)
```
- 측정깨짐≠정의틀림: evidence 가 data_contract(T1 IA-2) 위반이면 `incident` 마킹 → validate skip (가정 틀림으로 오판 금지).
- **★per-domain alpha-wealth 격리**(claude R1): FDR alpha-wealth 를 3도메인 pooling 금지 — `domain`(macro/equity/commodity) 또는 family 단위 stream 키. 통계예산은 도메인 격리, ATMS 위상은 단일.

### 2.3 `update_controller.py` — ★adopt/retract 비대칭 gate + base사람비준
> **claude R1 핵심 정정**: 채택/변경(adopt)과 기각(retract)에 **같은 AND-gate 쓰면 치명적**. falsification breach 된(증명상 틀린) 가정이 dwell/K 채울 때까지 live 노출. → **adopt = conjunctive(slow) / retract = hard-falsifier disjunctive(fast) 분리**.
```python
class UpdateController:
    def __init__(self, registry, validator, dag, adopt_gate=hysteresis_and_gate): ...
    def step(self, card, verdict) -> UpdateAction:    # ACTION∈{keep,retire,transition,human_review}
        # === RETRACT gate (fast, disjunctive) — 먼저. hard falsifier breach = 즉시 ===
        if retract_now(verdict):                       # falsification_metric breach OR FDR 강기각
            self.dag.invalidate(card.id, mode="hard")  # §4 hard-retract → orphan fast-exit 대상
            return UpdateAction.retire
        # === base-layer = 사람비준 (자동변경 금지) ===
        if card.is_base_layer:                          # regime/지표의미
            return UpdateAction.human_review            # BB-3 HumanApprovalGate (재유도+shadow, §4)
        # === ADOPT gate (slow, conjunctive 5조건 AND) — 정의 S→S' 전환 ===
        gres = self.adopt_gate(fdr_significant=verdict.fdr_significant, effect_size=...,
                               dwell_ok=..., k_window_persist=..., same_regime=...)
        # gate 결과 = (pass, evidence, cost_to_flip) — binding constraint 노출 (claude R1)
        if gres.passed:
            new = transition_card(card)                 # version bump, valid_to 마킹
            self.registry.register(new)
            self.dag.invalidate(card.id, mode="soft")   # §4 soft = grace+lazy 재유도
            return UpdateAction.transition
        return UpdateAction.keep                         # cost_to_flip 로 "왜 미승격" 설명
```
- **retract ≠ transition**: retract = 즉시(falsifier), transition = 느린 정의전환(adopt gate). 둘 분리가 live 노출 차단의 핵심.
- gate 반환 = bool 아니라 `(passed, evidence, cost_to_flip)` → HumanApprovalGate·로그가 binding constraint 설명.

### 2.4 `derivation.py` — 가정→파라미터 순수함수 (PIT replay seam, R10)
```python
@dataclass(frozen=True)
class DerivedParameterSet:
    value: float; band: tuple[float,float]
    provenance: list[tuple[str,str,pd.Timestamp]]    # (assumption_id, version, knowable_from)

def derive(card_refs: list[tuple[str,str]], registry, as_of, *, regime, sector) -> DerivedParameterSet:
    """버전드 순수함수. 같은 (card_refs, as_of) → 항상 같은 결과 (PIT replay 보장)."""
    cards = [registry.get_version(i, v) for i, v in card_refs]   # 정확 버전 (frozen 재현)
    # 신뢰도 → band: confidence_to_band(card.posterior_confidence)  ← 축C band
    # scope 조건부: regime/sector/period 계층 (CL-5, gemini: cross 금지·계층적)
```
- **PIT replay (R10)**: 과거 결정의 `DecisionRecord.rule_version` + card_refs 로 `get_version` → `derive` 재호출 = frozen 값 재현. AnalysisLedger.recompute(version_basis=counterfactual)로 "지금 정의로 그때 보면" 분리.
- **★replay 재현 보장**(claude R1 Q3): 결정 시 `(base, cheapness_z, DCF입력, model_version_SHA, code_SHA)` 불변해시 + bitemporal(valid_time, decision_time) 박제. replay = as-of 스냅샷에 **L1/DCF(결정론)만 정확 재계산** + **L2/L3(확률 attenuator)는 가중치 비재현 → 로깅된 출력을 frozen-fixture 로 고정**. (결정론 floor=정확재현 / 확률 attenuator=fixture.)

## 3. CL-2 — judge (L1 floor + L2 Qwen + L3 BGE + DCF dual-gate) ✅구현완료

**파일**: `core/assume/judge.py` (self-test 7/7 PASS). **자문 수렴 경계**(gemini R1 + claude R1 정정):
- **L1 = 상대축**(cheapness_z 구조모델 대비 저평가) = **sizing 축**. **DCF = 절대축**(내재가치) = **pure kill 축**. 둘은 **결합 안 함**(평균/가중합 금지 — 저평가+무가치가 중간점수로 생존하는 누수 차단). `live = L1_pass ∧ DCF_pass` (veto disjunctive).
- **L2/L3 = strictly attenuating-only** (claude R1 핵심 정정 — gemini "confirm" 은 위험): `final = L1_size * a2 * a3`, a2/a3 ∈ [0,1]. → final ∈ [0, L1_size]. L2/L3 가 L1 sizing 을 **증폭하는 경로 구조적 부재**(monotone-down) = LLM safe-by-construction. self-test case7 이 모든 L2/L3 조합에서 size ≤ l1_size 검증.
- **fail-open = L1-fallback**: L2/L3 결측·저신뢰·장애 → a=1.0 (안전은 L1∧DCF 가 이미 확보). **abstain(포지션0) ≠ fallback**: |cheapness_z|<deadzone(L1 neutral band) OR DCF veto 일 때만.

```python
@dataclass
class JudgeVerdict:
    final: str                  # allow | veto | abstain | neutral
    l1: Verdict; dcf_gap: float | None
    l2_context: dict; l3_analogs: list
    confidence: float; band: tuple[float,float]; size_mult: float
    vetoed_by: list[str]        # ["l1"] / ["dcf"] / ["l1","dcf"]

def judge(firm, sector, date_, as_of, *, model, features, signals, cards,
          fundamentals=None, quote=None, rag: RagPitPipeline=None,
          qwen_hook=None, derived: DerivedParameterSet=None) -> JudgeVerdict:
    a = resolve_as_of(as_of)                                    # PIT 강제 (내 SSOT)
    # --- GATE 1: L1 결정론 veto floor (수치 싼지/비싼지 = 결정론만, anti-pattern 차단) ---
    l1 = l1_verdict(firm, sector, date_, a, model, features, signals, cards)
    # --- GATE 2: DCF 독립 veto (병렬 dual-gate, gemini) ---
    dcf_gap = None
    if fundamentals and quote:
        vr = value_stock(fundamentals, quote)
        dcf_gap = vr.valuation_gap if vr else None              # 내재가치-가격 갭
    vetoed = []
    if l1.final == "veto": vetoed.append("l1")
    if dcf_gap is not None and dcf_gap < DCF_VETO_GAP: vetoed.append("dcf")  # 내재가치 훼손 veto
    if vetoed:
        return JudgeVerdict(final="veto", l1=l1, dcf_gap=dcf_gap, vetoed_by=vetoed, ...)
    if l1.final == "abstain":
        return JudgeVerdict(final="abstain", ...)               # 정보부족 → confirm 안 함
    # --- L1 통과분만 confirm (L2/L3 = 맥락·사례, 수치판정 X) ---
    l2 = qwen_hook(firm, sector, a, derived) if qwen_hook else {}   # 현 상황정의 S/S' 맥락 태그
    l3 = rag.query_similar(f"{sector} {firm} {features}", top_k=5, as_of=a) if rag else []
    # confirm = confidence 변조만 (정의전환·유사사례 일치도). band/사이징에 반영.
    conf = _combine_confidence(l1, derived, l2, l3)            # base=derived.posterior, ±l2/l3
    band = confidence_to_band(conf); size_mult = _size(conf, band)
    final = "allow" if l1.final == "allow_cheap" else "neutral"
    return JudgeVerdict(final=final, l1=l1, dcf_gap=dcf_gap, l2_context=l2,
                        l3_analogs=l3, confidence=conf, band=band, size_mult=size_mult, vetoed_by=[])
```
- **안티패턴 차단**(plan §0): 싼지/비싼지 수치 = L1(cheapness_z)·DCF 결정론. L2 Qwen=상황정의(S vs S') 맥락 태그, L3 BGE=유사 과거사례. **LLM 은 수치판정 X**.
- **veto 우선순위**: rule trap(l1 내부) > L1 floor > DCF — 단 L1·DCF 는 병렬 veto (어느 하나 veto=차단). confirm 층은 veto 불가(신뢰도만).
- **fallback 안전**: qwen_hook/rag/fundamentals 부재 → confirm 생략, L1+DCF floor 만으로 결정(결정론 floor 가 항상 바닥). LLM 장애가 매매 차단 X (degrade to deterministic).

## 4. CL-3 — ATMS 전파 + orphaned + decay (gridlock 방어)

**파일**: `core/assume/dag.py` + `core/assume/orphan_guard.py`. **gemini ★실패모드 방어**: 거시 가정 변경 시 cascade rollback 폭주→매매 마비 → **grace period + lazy evaluation**.

### 4.1 `dag.py` — hard/soft mode + epoch single-pass + grace/lazy + base shadow/canary
```python
class AssumptionDAG:
    def invalidate(self, id, *, epoch, mode="soft", grace_days=GRACE) -> InvalidationResult:
        # mode="hard" (retract gate 발화) → dependents fast-path (orphan 즉시 후보, §4.2 token-bucket)
        # mode="soft" (adopt transition) → 아래 grace+lazy
        # 1) 즉시 전부 under_review 금지 (gemini) → dependents 에 stale_mark(grace_until=as_of+grace)
        # 2) lazy: stale 카드는 다음 derive() 접근 시에만 재검증 (eager cascade X)
        # 3) epoch topological single-pass (재진입 0, nogood 기록 = 같은 epoch 재무효화 차단)
        # 4) graph churn > CHURN_CAP → escalate human (rate-limit, 폭주 차단)
    def resolve_stale(self, id, as_of) -> bool:   # derive 가 호출: grace 만료+재검증 후 확정

class BaseLayerCutover:
    """★base-layer(regime/지표의미) 변경 = retraction 아니라 re-derivation (claude R1).
    '가정 바뀜'≠'결론 틀림' — 새 base 아래서도 결론 근사 유효 가능. shadow/canary."""
    def begin(self, base_id, new_version) -> None:
        # old derived param 으로 카드 계속 운영 + new base 로 그림자 유도 병행
    def is_stable(self, base_id) -> bool:          # 그림자 유도 안정 확인
    def commit(self, base_id) -> None:             # 안정 후에만 전환 (grace period 의 상위버전)
```
- **hard vs soft**: retract(falsifier)=hard fast-path / transition(adopt)=soft grace+lazy. §2.3 비대칭의 전파 레벨 구현.
- **grace/lazy**: 의존 가정 stale 마킹만(즉시 retire X), 재검증은 derive 접근 시. epoch single-pass+nogood=무한루프 차단, churn cap=사람.
- **base shadow/canary**: regime/지표의미 변경은 old 계속+new 그림자 병행→안정후 commit. cascade 폭주를 "병행 후 검증된 전환"으로 대체.

### 4.2 `orphan_guard.py` — managed-exit + token-bucket + 도메인 netting + decay
```python
def on_assumption_retired(card_id, registry, ledger: DecisionLedger, positions, *, mode) -> list[ExitOrder]:
    # 1) DecisionLedger 에서 이 가정 trigger 한 결정 → 보유 포지션 역추적
    # 2) ★mode 분기 (claude R1 Q4): hard-retract(falsifier 발화)분만 fast 청산,
    #    나머지(soft)는 re-derivation→shadow (즉시청산 X)
    # 3) ★book 레벨 rate-limiter(token bucket): 동시다발 retire 시 청산 토큰버킷 제한 (폭주 차단)
    # 4) ★도메인간 netting: macro·equity orphan 상쇄 후 net 만 집행 (= §2.3 adopt/retract 비대칭의
    #    포트폴리오 레벨 승격)
    # 5) decay: card.half_life 로 신뢰도 시간감쇠 (재검증 전 점진 사이징 축소)
def decayed_confidence(card, age_days) -> float:   # posterior * 0.5**(age/half_life)
```
- **청산폭주 방지**(claude R1 Q4): hard-retract 만 fast, soft 는 shadow. **token-bucket rate-limit** + **도메인 netting**(상쇄 후 net 집행) 으로 동시다발 일괄청산(gridlock) 차단.

## 5. CL-5 — cheapness_z/archetype 기간·산업 적응 (method §3.5 동형)

- **derivation 이 scope 조건부**: `derive(...,regime,sector)` 가 카드 scope(sector×period×regime) 계층(gemini: cross 금지·계층적 regime>archetype>period)로 파라미터 산출. cheapness_z 는 이미 regime-conditional σ — 여기에 **카드 기반 z_floor/band 가 sector×period 로 시변**.
- **통합 method 동형**: 거시 decoupling(역전→침체 UNLESS QE) = 주식(저PER=싸다 UNLESS 공정전환기) = 상품(COT극단→평균회귀 UNLESS 공급과잉). 셋 다 `AssumptionCard{baseline, decoupling 조건(보조지표), falsification}` → `derive` → judge. **단일 경로**.
- 주식 archetype(`l1_gate` cards dispatch) + 기간(공정전환기=valid_from 시변 카드) + commodity archetype(T2 BB-5) 모두 같은 Registry·derive·judge 통과.

## 6. CL-4 — closed-loop GATE (3도메인 동형, ★부분구현 차단)

**파일**: `tests/assume/test_closed_loop_3domain.py`. plan §3 루프를 거시∧주식∧상품 **각각** end-to-end:
```
[결정] judge → DecisionLedger.record(frozen, rule_version, regime_model_version)   축C·A
   → [학습] outcome join → validator.validate(regime-conditional)                  축A·D
   → [검증] ValidationVerdict(holds_now, fdr_significant)                          축D
   → [변경] UpdateController.step → AND-gate → transition(S→S')                    축E
   → [전파] dag.invalidate(grace+lazy) + orphan_guard                             축E·F
   → [재주입] registry.active → 다음 judge                                         축C
```
- **GATE**: 3도메인 각각 위 6스텝 self-test PASS + PIT replay(과거결정 frozen 재현) + gridlock 미발생(grace 내 매매유지) 확인 후에만 progress 18셀·14행 [x].
- **★진짜 가장 먼저 깨질 지점 = 재주입의 반사성(reflexivity)**(claude R1 Q5 — gridlock 은 가시적·하류일 뿐): 학습기 훈련데이터가 **자기 과거 결정으로 오염** → i.i.d. 붕괴 → "자기 결정이 수익낸 신호를 신뢰"하는 self-confirming attractor 로 수렴. noisy commodity 가 spurious 패턴 최다 생성 → pooling 시 macro 로 누출(= per-domain 격리 필요 재확인).
  - **방어 3종**(closed-loop 구현 시 필수): (1) **frozen control book** — 재주입 신호 안 받는 통제계좌 = drift 탐지 기준선 (2) **off-policy 로깅** — abstain·shadow arm 결정 기록 + IPS 가중 → 학습기가 자기-생성 아닌 데이터 확보 (3) **동형은 구조(loop shape)만, state·weight 는 도메인 격리** (인터페이스 재사용, 파라미터 분리).

## 7. 산출 파일 + self-test

| 파일 | CL | self-test |
|---|---|---|
| `core/assume/registry.py` | 1 | 등록·버전전환·PIT조회·dependents 역색인 |
| `core/assume/validator.py` | 1 | engine dispatch + perf 영속 + incident skip |
| `core/assume/update_controller.py` | 1·3 | AND-gate 통과/차단 + base사람비준 분기 + transition |
| `core/assume/derivation.py` | 1·5 | 순수성(동일입력→동일출력) + PIT replay frozen 재현 |
| `core/assume/judge.py` | 2 | L1 veto / DCF dual-gate veto / L1통과 confirm / LLM부재 degrade |
| `core/assume/dag.py` | 3 | grace stale·lazy 재검증·epoch single-pass·churn escalate |
| `core/assume/orphan_guard.py` | 3 | retire→역추적→grace review→managed-exit + decay |
| `tests/assume/test_closed_loop_3domain.py` | 4 | 거시∧주식∧상품 6스텝 end-to-end + gridlock 미발생 |

## 8. 자문 R1 ✅수렴 (gemini R1 + claude R1 Opus4.8, raw=`.consult-codlearn-R1.txt`)

gemini+claude **topology 수렴**(단일 ATMS·Card통합 A안·L1∥DCF dual-gate·계층조건화). claude 가 **안전 디테일 7건 정정/추가**(상호 비모순, 전부 본 설계 반영):
1. **adopt/retract gate 분리** — adopt=conjunctive slow / retract=hard-falsifier disjunctive fast (§2.3). [같은 gate 기각 시 반증가정 live 노출 = 치명].
2. **per-domain alpha-wealth 격리** — pooling 시 noisy commodity 가 macro starve (§2.2).
3. **L2/L3 monotone-down** — confirm 아니라 [0,L1_size] attenuator. L1=sizing/DCF=kill 비결합 (§3, judge.py 구현완료).
4. **base = re-derivation + shadow/canary cutover** — retraction 아님 (§4.1).
5. **orphan = token-bucket + 도메인 netting** — hard-retract 만 fast 청산 (§4.2).
6. **★진짜 first break = reflexivity** (gridlock 아님) — frozen control book + off-policy(IPS) 로깅 + 도메인 state 격리 (§6).
7. **PIT replay = SHA 해시 + L2/L3 frozen-fixture** (§2.4).

→ **R1 수렴 종결**(정정이 표준·내적정합, 추가 라운드 불요). judge.py 는 정정 반영해 재구현(self-test 7/7). 나머지 core/assume 는 본 §2~4 확정 설계로 card_contract 랜딩 후 구현.

## 9. 워커 계약 의존 (랜딩 대기 = 내 구현 선행조건)
| 의존 | 담당 | 내 모듈 영향 | 상태 |
|---|---|---|---|
| `core/assume/card_contract.py` (AssumptionCardLike/assert_falsifiable) | btn-button BB-1 | registry/derivation/judge import | 설계완료, 구현 대기 |
| `assumption_validation_engine.py:validate` | btn-button BB-4 | validator 호출 | 설계완료, 구현 대기 |
| `regime_discovery.py:HumanApprovalGate` | btn-button BB-3 | update_controller base분기 | 설계완료, 구현 대기 |
| `correction_loop.py:LiveCorrelationLoop` | btn-button BB-2 | closed-loop 거시 학습 | 설계완료, 구현 대기 |
| `structure_model.cheapness_band` | btn-button B2 | derivation band(주식) | 대기 |
| data_contract/lineage/online_fdr 영속 | btn-Inv IA-2/3 | validator incident·PIT replay | 대기 |
| 모의 API outcome 수집 | btn-Inv IA-5 | closed-loop outcome join | 대기 |

> **착수 순서**: card_contract 랜딩 → registry/derivation(계약만 의존) 선구현 → judge(부품 실재, 즉시 가능) → validation_engine 랜딩 → validator/update_controller → dag/orphan_guard → closed-loop 통합.
> judge 는 L1·DCF·cheapness_z·rag_pit 전부 실재 → **card_contract 무관하게 선구현 가능** (derived 파라미터를 optional 로).

## 10. btn-button R5 통합 아키텍처 반영 + 교차세션 조율 (2026-05-29)

> btn-button 5R saturation(`CONSULT-DECISIONS-button-v2-20260529.md` + `DESIGN-button-v2.md §10`) 수신. BB-1~5 확정, V0~V6 빌드 진입(Walking Skeleton). T3 정합 + 조율 3건.

### 10.1 ★closed-loop substrate = bitemporal append-only event ledger (내 모듈 재배선)
btn-button 통합결정 = closed-loop 의 단일 레버리지 = **11-event 이벤트소싱 ledger** (`state = reduce(pure_apply, sorted(events))`). 내 core/assume 모듈을 이 substrate 위로 재배선:
- **Registry** = 카드 lifecycle 이벤트 emit: `ASSUMPTION_CREATED`(register) / `TRANSITIONED`(version bump, v_n→v_{n+1} 인과 edge) / `RETIRED`(retract). 기존 단순 dict 보관 → 이벤트 emit + state 투영.
- **derivation/PIT replay** = `get_version` 이 ledger state 투영(`decision_time` 스냅샷)에서 카드 복원. §2.4 의 (base,z,DCF,SHA) 해시 = `PREDICTION_MADE{regime_ctx_snapshot, trigger_snapshot, horizon_h, deadline}` 이벤트로 박제.
- **★FDR_DECISION 시간축 불변식**(btn-button crux): online-FDR = 결정 순서의 성질 → `FDR_DECISION` immutable, **decision_time 순으로만 재생**. late outcome = 해소 이벤트 append(wealth 되감기 X). Brier/DM retrospective 만 valid_time 재계산. → 내 UpdateController 가 FDR 결과 소비 시 이 불변식 준수(재정렬 금지).
- **본체 소유 = btn-Inv(IA-1)**, btn-button BB-4 = read-only, 나(T3) = lifecycle emit + state 소비. → §10.4 조율#1.

### 10.2 ★cross-asset cascade (R5 맹점1) — 내 ATMS 도메인 (CL-3 보강)
btn-button 의 **자산클래스별 독립 FDR 스트림(풀링 금지)** 이 거시 regime 의 **cross-asset 동시영향**을 무시 → 상위 거시 regime 변화 시 하위(crypto/equity/commodity) 자산 파라미터 cascade reset 필요(안 하면 구조변화를 "이상치 연속"으로 오인 → FDR 통제 상실).
- **해소 = T3 ATMS 의존전파**: 거시 base-layer regime 카드 → 하위 자산 가정의 **conditioning edge**(depends_on). 거시 regime `TRANSITIONED`/`RATIFIED` 시 → 하위 자산 카드 `dag.invalidate(mode="soft")` → **re-derivation**(FDR 풀링 아님, claude R1 정합). 
- **통계예산 격리는 유지**(per-domain alpha-wealth, §2.2) + **위상 전파는 단일 ATMS**(cross-asset edge). 둘 양립 = claude R1("위상 단일·예산 격리")과 btn-button(풀링 금지) 동시 충족.
- `dag.py` 에 cross-asset edge type 추가: `macro_regime → {crypto,equity,commodity} card` (base-layer→하위 conditioning). 거시 cutover(§4.1 BaseLayerCutover) 시 하위 shadow 병행.

### 10.3 revision-drift monitor (R5 맹점2) — closed-loop 보강 (CL-4)
거시 지표 사후수정(vintage revision) 시 "당시 결정 vs 수정된 진실" 괴리 측정 루프 부재 → Brier calibration 신뢰도 저하. claude R1 의 **reflexivity 방어(off-policy 로깅)** 와 동족.
- **구현**: `OUTCOME_OBSERVED` 의 realtime vs final(vintage) 라벨 분리(btn-Inv vintage 연계) → drift = |realtime−final| 추세. drift 급증 = 해당 거시 카드 calibration 재검 트리거. closed-loop §6 의 reflexivity 방어(frozen control book + off-policy)에 편입.

### 10.4 교차세션 조율 (btn-Codlearn 주관)
1. **event ledger schema 3자 합의** ⚠️시급 — 본체=btn-Inv IA-1, read-only=btn-button BB-4, lifecycle emit+소비=나. btn-Inv 에 11-event 계약(§10.1) 정렬 메시지 전송완료(2026-05-29). btn-Inv 의 `outcome_ledger` 가 이 계약 본체가 되도록. 회신 대기.
2. **cross-asset cascade** = §10.2 내 ATMS 로 해소(설계 반영완료).
3. **crypto on-chain 데이터(CoinMetrics Community 무료)** = btn-Inv 데이터 도메인 의존 — btn-Inv IA-4(상품 데이터) 범위에 crypto 추가 필요. instrument 우선 = crypto+sector-ETF+commodity(btn-button 확정).

### 10.5 btn-button 확정 설계 중 내 wire 갱신점
- BB-5 **4단 archetype 추상**(primary/companion/value_trap_guard/cheapness) = 전자산 보편, **value_trap_guard = decoupling 머신 일반화** → 통합 method §3.5 와 정확히 일치(거시 decoupling=주식 trap=상품 oversupply). 내 derivation/judge 의 cards dispatch 가 이 4단 추상 소비.
- BB-3 regime 발견 = BOCPD(timing)+Hotelling T²/χ²(novelty)+LORD++ wrap+사람 gate → 내 UpdateController 의 `is_base_layer` 사람비준 분기(§2.3)가 `HumanApprovalGate.approve` wire.
- **미결정(사용자 대기)**: instrument 구현 순서 — btn-button 은 crypto-first(MVRV walking skeleton) 진행 중. 사용자 명시 정정 없으면 이대로 진행.

## 11. ★전체구조 3R 자문 반영 (whole-architecture, 2026-05-29) → `CONSULT-DECISIONS-whole-20260529.md`

> 사용자 "전체 구조 기준 3R 자문"(gemini+claude 병렬). 통합 레벨 결함→해소→완결성. **R3=NOT saturation**(시간축 1개 남음). 전문=결정 문서. 내 모듈 영향 요약:
- **judge.py fail 방향 정정**(R1/R2): fail-open(a=1.0) 역방향 → manifest 기반 fail-safe. errored-expected-L2/L3→abstain(방향노출 0), absent→L1 baseline. ✅반영완료(self-test 8/8).
- **dag cascade**(R2): hierarchical FDR(부모=macro regime, 독립 substrate) + de-risking bypass(신규진입 우회 금지). §10.2 cross-asset edge 를 이 형태로 구현.
- **derivation/event ledger**(R2): 3 typed timestamp(tt/dt/vt) + REVISION_OBSERVED(12 event) + CQRS(snapshot+watermark). PIT replay = 적대적 taint-replay(byte-identical) 1급 게이트.
- **dumb circuit breaker**(R1/R2): out-of-band 신규 컴포넌트(execution 층, substrate 비참조, 정적캡 3종). 소유 경계(btn-Inv 실행 vs 나) 조율 필요.
- **judge/derivation per-domain 다형성 + falsification power**(R3): estimation 비전이 — update 주기·decay 도메인별, falsification power 하한.
- **closed-loop**(R3): sequestered control stream(optimizer 미접촉) + online FDR/e-process + 정지 합성데이터 false-positive 정량화 편입.
- **미해결(R4 후보)**: 시간축 단독(online FDR/e-process·optional-stopping·anytime-valid) — 양모델 권고, 사용자 승인 대기.
