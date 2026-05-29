---
tags: [type/design, domain/inv, phase/II, track/T2, topic/assumption-lifecycle-v2, session/btn-button]
date: 2026-05-29
session: btn-button
plan: ./plan-assumption-v2-axes.md
progress: ./progress-T2-assumption-20260529.md
prior: ./DESIGN-T2-assumption-stats.md
binding_axes: [BB-1, BB-2, BB-3, BB-4, BB-5]
consult: [./.consult-button-R1.txt]
note: T2(btn-button) v2 설계 — 거시 학습·검증·판정 통계. 직전 T2 는 범용 통계엔진(25/25 PASS) 완성, v2 는 BB 축의 실제 연결분(거시 카드화·live 루프·regime 발견·commodity)을 구현. 코드레벨 file:function:contract.
---

# DESIGN-button-v2 — 거시 학습 + 검증·판정 통계 (BB-1~5 코드레벨)

> **담당**: btn-button (T2). **산출**: 본 설계 + 구현 + self-test. **최종통합**: btn-Codlearn (T3).
> **전제**: 직전 T2 가 범용 통계엔진 완성 (`detectors.py` / `online_fdr.py` / `assumption_stats.py` / `archetype.py`(equity 5) / `pit_regime.py`, 25/25 PASS). v2 = **BB 축이 요구하는 도메인 연결분** 구현.

## 0. 현 상태 vs BB 갭 (코드 매핑 증거)

| BB 축 | 요구 | 현 코드 | 갭 (v2 구현 대상) |
|---|---|---|---|
| **BB-1** [B] | 6 decoupling → falsification 있는 **버전드 카드** + 신규 case | `indicator_event_correlation.ANOMALY_CASES` = static dataclass (version·falsification 無) | AnomalyCase → 버전드 `MacroAssumptionCard` 승격 + falsification_metric + 신규 case API |
| **BB-2** [A] | `ingest_correction`/`recall_similar` **live 연결** | 메서드 존재하나 dead. `regime_classifier` 는 `score_confidence`(읽기)만 호출 | filter/smoother divergence → CorrectionRecord harvest → ingest + recall surface (PIT mask) |
| **BB-3** [A·Q3] | open-ended regime 발견 + **사람비준 gate** | `pit_regime` = 고정-K3 only. `Bocpd` 존재하나 discovery 모듈 無 | `core/regime/regime_discovery.py` (BOCPD novelty, bnpy 미설치 graceful) + CandidateRegime + HumanApprovalGate |
| **BB-4** [D] | regime-conditional holds + online-FDR (가정별 alpha-wealth) | `assumption_stats`(holds) + `online_fdr`(LORD++) = 부품만, 가정별 스트림 cohesion 無 | 가정 검증 엔진 (card → validate → p-value → 가정별 FDR stream → AND-gate fdr_significant) |
| **BB-5** [상품] | commodity archetype(carry/seasonal/inventory) + 검증 통계 | `archetype.py` = equity 5종만 | commodity 3 카드 discriminated union + config yaml + 검증 경로(parametric carry / structural seasonal) |

**bnpy/ruptures 미설치 확정** (Python 3.12.10, numpy 2.4.2 / pandas 2.2.3 / pydantic 2.12.5). → BB-3 = numpy-only (BOCPD + 잔차 novelty) + **bnpy 어댑터 seam** (설치 시 sticky-HDP-HMM birth/merge 사용, jumpmodels 부재 시 규칙 폴백과 동형).

## 1. 경계 (T2 vs T3) — 충돌 방지

- **T3 (Codlearn) 소유**: `core/assume/` 오케스트레이션 코어 = Card **Registry** / **Validator** / **UpdateController** / DAG.
- **T2 (button) 산출 = 본 설계**: (a) **공유 계약** `AssumptionCardLike` Protocol + 최소 base 필드 (T3 가 소비·확장) (b) **거시 도메인 카드** (MacroAssumptionCard, brain) (c) **commodity 도메인 카드** (archetype 확장) (d) **검증 엔진** (가정 → holds → FDR) (e) **regime 발견·학습 루프**.
- 원칙: T2 는 **standalone 동작 + self-test** 하는 도메인 자산 + 계약 제공. Registry/Validator/UpdateController 는 T3 가 본 계약 위에 wire. → 보고서에 **계약 표면** 명시 (plan §5.4).

## 2. BB-1 — 거시 decoupling → 버전드 MacroAssumptionCard

**파일**:
- `core/assume/__init__.py` (신규 패키지)
- `core/assume/card_contract.py` — 공유 계약 (T2 제공, T3 소비)
- `core/brain/macro_assumption_card.py` — 거시 도메인 카드 + 어댑터 + 6 승격 카드

**`card_contract.py`** (공유 계약):
```python
class AssumptionCardLike(Protocol):              # 구조적 타이핑 (T3 base 와 무충돌)
    id: str; version: str
    kind: Literal["structural","parametric"]
    scope: Literal["global","sector","asset","macro"]
    domain: Literal["macro","equity","commodity"]
    statement: str; rationale: str
    falsification_metric: str                    # ★ 반증불가 = 진입금지
    is_base_layer: bool
    valid_from: Optional[date]; regime_model_version: Optional[str]
    posterior_confidence: float; band_halfwidth: float
    depends_on: list[str]
    half_life: Optional[float]

class BaseAssumptionFields(BaseModel):           # frozen pydantic, 위 필드 구현 (선택적 base)
    model_config = {"frozen": True}
    ...
    @field_validator("falsification_metric")     # 빈 falsification = ValueError (gemini C-1)
    ...
def assert_falsifiable(card) -> None: ...        # 진입 게이트 헬퍼
```

**`macro_assumption_card.py`** (거시 카드):
```python
class MacroAssumptionCard(BaseAssumptionFields):
    domain = "macro"; kind = "structural"; scope = "macro"
    event: str                                   # MacroEvent.value
    distorted_indicator: str
    expected: str; actual: str                   # Dir.value
    supplementary: list[dict]                    # SupplementarySignal 직렬화
    attenuation: float
    historical_episodes: list[str]
    falsification_metric: str                    # ★ 케이스별 반증 조건 (아래)

def anomaly_to_card(case: AnomalyCase, version="v1", valid_from=None) -> MacroAssumptionCard
def card_to_anomaly(card: MacroAssumptionCard) -> AnomalyCase    # 역방향 (live 주입)
def promote_all(version="v1") -> list[MacroAssumptionCard]       # 6 case 일괄 승격
def add_candidate_card(event, distorted_indicator, expected, actual, reason,
                       supplementary, attenuation, falsification_metric,
                       version="v1.cand", episodes=()) -> MacroAssumptionCard   # 신규 case
MACRO_DECOUPLING_CARDS: list[MacroAssumptionCard]   # promote_all() 결과 (모듈 상수)
```

**falsification_metric 설계** (케이스별, 반증가능):
- `yc_inversion_term_premium`: "역전(yc<0) ∧ WALCL>7.5e6 인 기간의 forward 12M 침체확률 ≤ baseline 침체율 + 효과크기 d≥0.5 (즉 attenuation 이 실제로 침체신호를 약화시켰나)". 반증 = 역전+QE 인데도 12M 내 침체 발생 빈도가 baseline 과 동일.
- `sahm_supply_shock`: "Sahm 트리거 ∧ V/U>1.0 인 기간의 12M 침체율 < Sahm 단독 트리거의 침체율". 반증 = V/U 높아도 침체율 동일.
- `m2_inflation_decoupling`: "M2 급증 ∧ M2V<1.3 ∧ 초과준비금 급등 시 24M 후 코어CPI YoY < M2 급증 단독의 인플레". 반증 = velocity 낮아도 인플레 동일.
- (나머지 3 동형 — 각 보조지표 trigger 조건부로 distorted_indicator 의 baseline 거동이 실제로 깨지는지 정량 비교).
- **컴파일**: falsification_metric 문자열 → `assumption_validation_engine.compile_falsification()` 가 (regime-conditional) validator 파라미터로 변환 (BB-4 와 연결).

**버전·bitemporal**: `version` (정의 변경 시 bump) + `valid_from` (시변 — 케이스가 유효해진 시점). 정의 전환 (S→S') = 새 version 카드 발행 + 이전 version `valid_to` 마킹 (T3 ledger 가 영속).

## 3. BB-2 — indicator_event_correlation live 학습 루프

**파일**: `core/brain/correction_loop.py`

**핵심 통찰**: `regime_classifier._jump_model_overlay` 가 이미 **filter(online) vs smoother(insample) divergence** 를 계산하나 confidence 보정에만 쓰고 버린다. 이 divergence 가 곧 "실시간 판정 ≠ 사후정답" = CorrectionRecord 의 원천. → 버려지는 신호를 harvest.

```python
@dataclass
class CorrectionHarvestConfig:
    hindsight_source: Literal["jm_smoother","nber","realized"] = "jm_smoother"
    min_lag_days: int = 0

class LiveCorrelationLoop:
    """IndicatorEventCorrelation 을 live 학습 루프에 연결 (BB-2). PIT causal mask 준수."""
    def __init__(self, model: IndicatorEventCorrelation | None = None): ...

    def harvest_from_jm(self, online_labels, smoother_labels, as_of_index,
                        signature_fn, confidence_series=None) -> list[CorrectionRecord]:
        # filter≠smoother 인 시점마다 CorrectionRecord 생성 (regime_realtime=online,
        # regime_hindsight=smoother, anomaly_signature=signature_fn(t), lag=Δdays)
        # → 각각 model.ingest_correction (is_misjudgment 만 적재)

    def recall_for_classify(self, regime, signature, as_of_ts, k=3) -> list[dict]:
        # model.recall_similar wrapper (PIT mask) — classify 경로에 surface

    def attach_to_classifier(self, classifier) -> None:
        # classifier.correlation_model 을 이 loop 의 model 로 교체 (read+write 동일 인스턴스)
```

**wire 지점** (계약, regime_classifier 비침습):
- read 경로 = 기존 `_apply_correlation_attenuation` → `score_confidence` (불변).
- write 경로 = 사이클 종료/배치 시 `harvest_from_jm(online, smoother, ...)` 호출 → 동일 model 인스턴스에 ingest. 다음 사이클부터 `score_confidence` 의 `recurrent_misjudgment` 가중이 자동 반영 (코드상 이미 `_case_stats` 소비).
- recall = classify 시 `recall_for_classify` 결과를 evidence 에 surface (macro_reasoning 입력).
- **PIT 철칙**: ingest 는 as_of_ts 박제, recall 은 as_of 이전만 (둘 다 기존 코드가 보장 — loop 은 호출 규약만 강제).

**self-test**: 합성 online/smoother 라벨 divergence → harvest → ingest → 같은 signature 로 recall 시 hint surface 확인 + PIT mask (미래 보정 미surface).

## 4. BB-3 — open-ended regime 발견 + 사람비준 gate

**파일**: `core/regime/regime_discovery.py`

```python
@dataclass(frozen=True)
class CandidateRegime:
    candidate_id: str
    discovered_at: pd.Timestamp
    segment_start: pd.Timestamp; segment_end: pd.Timestamp
    feature_centroid: dict[str, float]
    novelty_score: float                  # 기존 regime 중심과의 거리 (Mahalanobis-ish)
    nearest_known_regime: int; distance_to_nearest: float
    n_obs: int
    status: str = "candidate"             # ★ 자동승격 금지

class OnlineRegimeDiscovery:
    """numpy-only open-ended regime 발견. bnpy 설치 시 sticky-HDP-HMM 위임 (어댑터 seam)."""
    def __init__(self, known_centroids: dict[int, np.ndarray], known_covs=None,
                 novelty_threshold: float = 3.0, min_segment: int = 6,
                 hazard_lambda: float = 60.0, use_bnpy: bool = True): ...

    def _try_bnpy(self, X):               # import 성공 시 sticky-HDP-HMM birth/merge → 신규 state
        try: import bnpy ... except: return None    # graceful degrade

    def scan(self, X: pd.DataFrame) -> list[CandidateRegime]:
        # 1) bnpy 가능하면 위임 (birth move 가 신규 국면 = candidate)
        # 2) fallback: 다변량 → BOCPD(요약통계)로 segment 분절 → 각 segment centroid 의
        #    기존 regime 중심 대비 최소거리 > novelty_threshold (σ 단위) → CandidateRegime
        # 발견 = 자동, 적용 = 안 함 (status=candidate)

class HumanApprovalGate:
    """발견자동·승격사람 (BB-3 / claude C-meta base-layer). regime = base-layer 가정."""
    def __init__(self, base_version="pit_fixedk3_v1"): ...
    def pending(self) -> list[CandidateRegime]
    def approve(self, candidate_id, new_label: str, approver: str,
                rationale: str) -> RegimePromotion:    # ★ 사람만 — version bump
        # → 새 regime_model_version (예: pit_fixedk4_v1) + 신규 regime def 발행
        # + 의존 가정 전체 재검증 epoch 트리거 신호 (T3 UpdateController)
    def reject(self, candidate_id, reason, approver) -> None
```

**설계 결정**:
- regime 발견 = base-layer 가정 변경 → `assumption_stats.hysteresis_and_gate(is_base_layer=True)` 가 항상 자동차단하는 것과 동형. discovery 는 candidate 발행까지만, 승격은 `approve()` 사람 호출 필수.
- novelty = 기존 regime 중심들과의 최소 Mahalanobis 거리 (cov 없으면 표준화 유클리드). threshold σ 단위 (기본 3.0).
- BOCPD 는 다변량 요약(예: 첫 PC 또는 feature 평균 z)에 적용 — `detectors.Bocpd.map_run_length` 급락으로 segment 경계.
- bnpy seam: 설치 시 sticky-HDP-HMM 의 birth move 가 발견하는 신규 state 를 candidate 로 매핑 (Hughes&Sudderth 2015). 미설치 = numpy fallback.
- 승격 시 `regime_model_version` bump → cheapness_z σ 재현성 직결 (pit_regime docstring) → 의존 가정 재검증 epoch (T3 계약).

**self-test**: (a) 기존 3 regime 합성데이터 → candidate 0 (b) 신규 분포(다른 mean/cov) 주입 → candidate ≥1, novelty>threshold (c) approve() 만 version bump, 미승인 시 base_version 불변 (d) reject 후 pending 제거.

## 5. BB-5 — 금융상품(financial-product) archetype 프레임워크 + 검증 경로

> **스코프 정정 (사용자 2026-05-29)**: "상품" = **금융상품(financial product) 우선** + **commodity 도 포함**. 거래가능한 일반 종목 중 **학습대상 instrument 는 R2 자문에서 식별 → 해당 자산 포함 구현** (§9 R2). equity 5 archetype 은 기존 보유. v2 BB-5 = (a) commodity 3 카드 (확정, 아래) + (b) R2 식별 instrument (crypto/FX/ETF/bond 등 후보) archetype 확장.

**파일**: `core/structure/archetype.py` (확장) + `config/archetypes/commodity_*.yaml` (신규) + `core/structure/commodity_assumptions.py` (검증 경로). R2 후 instrument 카드 추가.

**archetype 확장** (discriminated union):
```python
class CommodityCarryCard(_ArchetypeBase):
    archetype = "commodity_carry"
    cheapness_sign = "low_multiple"        # 백워데이션(carry+) = 매력 (저평가 동형)
    carry_inputs = ["roll_yield","term_structure_slope","cot_net_long","storage_cost"]
    # trap: contango_flip(carry 음전환), 재고급증
class SeasonalCard(_ArchetypeBase):
    archetype = "seasonal"
    season_inputs = ["seasonal_zscore","heating_degree_days","harvest_calendar"]
    # trap: regime_break(계절성 무력화 — 이상기온/공급충격)
class InventoryCard(_ArchetypeBase):
    archetype = "inventory"
    inventory_inputs = ["days_of_supply","inventory_zscore","production_qoq","cot_net_long"]
    # trap: oversupply_regime(재고 극단인데 평균회귀 안 함 = 구조적 공급과잉)
```
- `ArchetypeCard` union + `ARCHETYPE_NAMES` + `_CARD_CLASSES` + `DEFAULT_SECTOR_ARCHETYPE` (crude_oil/natgas→seasonal·inventory, grains→seasonal, metals→inventory·carry) 확장.
- config yaml 3종 추가, `load_cards_from_config` 8종 검증.

**검증 경로** `commodity_assumptions.py` (통합 method §3.5 동형 — 거시 decoupling 패턴을 상품에):
```python
def carry_normal_range_assumption(card, roll_yields, regime_ids, current_regime, normal_carry):
    # parametric: "백워데이션 carry 정상범위=θ" → validate_parametric (regime별 CUSUM+PSI)
def seasonal_pattern_assumption(card, seasonal_pred, realized, regime_ids, current_regime):
    # structural: "계절 패턴이 작동한다" → validate_structural (prequential kink + BOCPD)
def oversupply_decoupling_check(cot_net_long, fwd_return, supplementary_triggered):
    # 거시 decoupling 동형: COT 극단(평균회귀 baseline) UNLESS 재고>임계 → decoupling
    #   = AnomalyCase 와 같은 구조 (C=원자재×재고regime, M=COT, S=재고)
```
- 통합 method: commodity 의 "COT 극단 → 평균회귀, UNLESS 공급과잉 regime" = 거시 "역전 → 침체, UNLESS QE왜곡" 과 동형. → 동일 `conditional_attenuation` 패턴 재사용 가능 (상품 AnomalyCase set).

**self-test**: 3 카드 round-trip + config 8종 로드 + carry parametric (regime별 holds) + seasonal structural + oversupply decoupling 발동.

## 6. BB-4 — 거시·상품 regime-conditional 검증 cohesion

**파일**: `core/structure/assumption_validation_engine.py`

기존 부품(`assumption_stats` holds + `online_fdr` LORD++)을 **가정 단위로 묶는** cohesion 레이어. T3 Validator/UpdateController 가 호출할 엔진.

```python
class AssumptionValidationEngine:
    """가정 카드 → validate(holds) → p-value → 가정별 FDR stream → AND-gate fdr_significant.
    T2 통계 cohesion. 결정 X (관측·산출만). T3 가 카드/데이터 주입해 호출."""
    def __init__(self, alpha=0.05): self._fdr: dict[str, LordPlusPlus] = {}

    def _stream(self, assumption_id) -> LordPlusPlus     # 가정별 alpha-wealth (부활 차단)

    def validate(self, card, *, realized=None, predictions=None, outcomes=None,
                 assumed_value=None, regime_ids, current_regime) -> ValidationVerdict:
        # 1) card.kind dispatch → validate_parametric / validate_structural
        # 2) RegimeConditionalReport.holds_now / confidence_now
        # 3) holds 증거 → p-value (effect→z→p, 보수적) → self._stream(card.id).test(p)
        # 4) ValidationVerdict(holds_now, confidence_now, fdr_significant, by_regime, evidence)
        #    fdr_significant = AND-gate 첫 조건 (T3 UpdateController 가 hysteresis_and_gate 에 주입)

    def compile_falsification(self, falsification_metric: str) -> dict:
        # BB-1 falsification 문자열 → validator 파라미터 (kind/threshold/window) 휴리스틱 파서

@dataclass
class ValidationVerdict:
    assumption_id: str; holds_now: Optional[bool]; confidence_now: float
    fdr_significant: bool; by_regime: dict; falsifiable: bool; evidence: dict
```

- **거시 decoupling 검증** (축D 목적): MacroAssumptionCard 의 falsification = "decoupling 이 실제 성립" → structural validation (실시간 판정 vs 사후 정답의 예측력) = BB-2 CorrectionRecord 빈도로 채점.
- **상품 검증**: commodity 카드 → carry parametric / seasonal structural (BB-5).
- **부활 차단**: 기각된 가정을 regime 복귀 때 재검정 → alpha-wealth 고갈 (online_fdr self-test 3 동형).
- **base-layer**: regime 정의 카드 = `is_base_layer=True` → engine 은 검증만, 변경은 BB-3 HumanApprovalGate.

**self-test**: 거시 카드 + commodity 카드를 엔진에 통과 (holds_now + fdr_significant) + 부활 남용 차단 + falsification 컴파일.

## 7. 산출 파일 요약 (v2 신규/확장)

| 파일 | BB | 상태 |
|---|---|---|
| `core/assume/__init__.py` | 1 | 신규 |
| `core/assume/card_contract.py` | 1 | 신규 (공유 계약, T3 소비) |
| `core/brain/macro_assumption_card.py` | 1 | 신규 |
| `core/brain/correction_loop.py` | 2 | 신규 |
| `core/regime/regime_discovery.py` | 3 | 신규 |
| `core/structure/archetype.py` | 5 | 확장 (commodity 3 카드) |
| `config/archetypes/commodity_carry.yaml` 외 2 | 5 | 신규 |
| `core/structure/commodity_assumptions.py` | 5 | 신규 |
| `core/structure/assumption_validation_engine.py` | 4 | 신규 |

## 8. T3 계약 표면 (btn-Codlearn wire)

1. **카드 계약** `AssumptionCardLike` Protocol — Registry 가 macro/commodity/equity 카드 통합 보관.
2. **검증 엔진** `AssumptionValidationEngine.validate(card,...)` → Validator dispatch. `fdr_significant` → `hysteresis_and_gate`.
3. **regime 승격** `HumanApprovalGate.approve()` → regime_model_version bump → UpdateController epoch 재검증.
4. **live 루프** `LiveCorrelationLoop.attach_to_classifier()` — 사이클 종료 시 harvest 호출처는 orchestrator.
5. **falsification 게이트** `assert_falsifiable(card)` — Registry 등록 전 진입 게이트.

## 9. 자문 (gemini-web + claude-web 병렬)

### R1 — 핵심 설계 검증 (commodity 확정분 + 방법론)
1. **BB-3**: bnpy 미설치 환경에서 numpy-only open-ended regime 발견의 **신뢰 가능한 최소 설계** — BOCPD segment + centroid novelty 면 충분한가, 아니면 online Dirichlet-process mixture (variational, numpy 구현) 가 ROI 있나? 사람비준 gate 의 false-discovery 통제는?
2. **BB-5**: commodity carry/seasonal/inventory 의 **falsification_metric 표준** — roll yield / COT / days-of-supply 의 정상범위·계절성 검정 정설 방법론 (academic/실무)?
3. **BB-1/통합**: 거시 decoupling 의 falsification 을 "attenuation 이 실제로 오판을 줄였나" 로 채점하는 게 통계적으로 타당한가 (meta-labeling 적중 평가 동형)? 더 나은 반증 설계?

### R2 — 학습대상 금융상품 instrument universe (사용자 정정 2026-05-29)
4. **거래가능한 일반 종목 중 "가정 라이프사이클 학습대상"으로 가치 있는 instrument 는?** — 기준(valuation/criteria)이 regime/기간/유형별로 실제 변하고 학습 가능한 자산군 식별. 후보: KR/US equity (기존 archetype), commodity (R1), **crypto (BTC 등, Upbit 연동)**, FX, ETF/섹터, 국채/크레딧. 각 instrument 의 **archetype + 가정 + falsification 방법론** + 우선순위. → 식별 후 사용자 승인 → 해당 자산 archetype/검증 경로 구현.

## 10. 자문 R1+R2 수렴 반영 (gemini Pro + claude Opus 4.8, 2026-05-29)

> raw: `.consult-button-R1.txt` / `.consult-button-R2.txt`. 두 모델 독립·수렴. 아래 = 구현에 반영할 확정 설계.

### 10.1 BB-3 regime 발견 (R1 수렴 — 설계 정밀화)
- **DP-mixture(variational numpy) 폐기** (양모델): 공분산 붕괴·label-switching·비결정 → numpy 비권장. base-layer 가정이라 cardinality 는 사람이 결정 (모델에 재귀 불필요).
- **BOCPD = timing trigger only (1-D 요약)** + **novelty 판정은 full 다변량** (claude 핵심): 신규 regime 은 종종 first-PC 와 직교 → 1-D 요약에서 안 보임. novelty = **Hotelling T²** (segment 평균 vs 기존 regime center, 분산 1/m 보정) / 점 단위는 **χ²_d 분위수** (σ 아님).
- **후보발행 = online-FDR(LordPlusPlus) 로 wrap** (claude 강력추천, 인프라 재사용): 신규 regime 선언율에 FDR 보장. Q1(후보발행)·Q3(attenuation) 둘 다 "희소 이벤트 스트림 FDR" = online-FDR 공통 백본.
- false-discovery 통제: **min-dwell τ_min + segment 내 χ² 초과비율 ≥ p + time-separation(과거 1년 무재현) + economic-overlay(기존 룰 falsification rate 동반 급증 시만 진짜 regime)**. **재현 K회 = booster only, kill 조건 아님** (COVID-2020식 일회성 진짜 regime 보호).
- 사람비준 gate 유지 (발견자동·승격사람).

### 10.2 BB-5 commodity 검증 (R1 수렴 — 방법론 확정)
- **carry**: `carry = annualized (F_near−F_far)/F_far` rolling z (또는 convenience yield δ). falsification = **carry→forward-return 예측회귀 slope 부호전환/유의성 상실** (prequential 추적) + 2σ band 이탈 + 가격역행. 근거: Gorton-Rouwenhorst(2006), Koijen-Moskowitz-Pedersen-Vrugt "Carry"(2018 JFE), Erb-Harvey(2006). 곡선 PCA(Litterman-Scheinkman) 병행.
- **seasonal**: 월 dummy 회귀 + **결합 F-test** + **STL seasonal-strength** `F_S=max(0,1−Var(remainder)/Var(seasonal+remainder))` + 다음 cycle **OOS hit-rate**. 단위근 HEGY(1990), 비모수 Kruskal-Wallis. falsification = F-test p↑ + strength↓ + OOS 붕괴.
- **inventory**: 정규화 재고/COT-OI z + **variance-ratio test(Lo-MacKinlay 1988)** (평균회귀 검정) + **threshold regression(Hansen 2000, threshold=days-of-supply)** (공급과잉 decoupling = regime-conditional 회귀 동형). **★경고: COT 예측력 약함(Sanders-Irwin-Merrin) → COT 는 companion 강등, primary 부적합.**

### 10.3 BB-1/BB-4 decoupling falsification (R1 수렴 — precision/recall 폐기)
- **episode-level precision/recall 폐기** (양모델, n≈5~8 → CI≈[0,1], 1건 오분류 20pp 흔듦). 평가 단위 episode→**observation-level** 로 하향.
- **① prequential ΔBrier/Δlog-loss** (attenuated vs non-attenuated 확률예측, horizon h 내 실현결과) — 기존 prequential 엔진 재사용, 최강수.
- **② paired forecast test**: Diebold-Mariano(1995) 등예측력 / regime-conditional 이면 Giacomini-White(2006) conditional predictive ability.
- **③ 잔차 CUSUM**: `Residual_t = 실제 − baseline×attenuation` 의 CUSUM 이탈 = attenuation 값 falsified (기존 `detectors.Cusum` 재사용).
- **④ mechanism-validation(결과독립)**: WALCL trigger 전제(QE→term-premium 왜곡)를 ACM(Adrian-Crump-Moench) term premium 으로 독립 검증 — 희소 침체 에피소드 비의존. **crypto 는 spurious 범람 → 필수**.
- **⑤ Beta posterior CI 명시** (point estimate 과신 금지). severity-weighted Brier 보조.

### 10.4 instrument universe (R2 수렴 — BB-5 확장)
- **4단 archetype 추상(primary_metric + companion_signals + value_trap_guards + cheapness_sign) = 전 자산군 보편** (양모델). **통합 통찰**: `value_trap_guard = cheapness 위에 얹는 regime/구조건전성 게이트 = R1 decoupling 머신 일반화`. cheapness_sign=baseline / guard=decoupling detector / companion=entry timing.
- **우선순위 top2 = crypto + 주식 sector-ETF** (양모델 동의, 순서만 이견). Rates/Credit = **signal layer** (FRED, 별 tradable universe 만들지 말 것). FX = risk-regime gate 먼저. REITs defer.
- **crypto archetype** (R2 확정): `monetary_store`(BTC, primary=MVRV/realized-price, mechanical robust) / `network_utility`(ETH, fee-burn·staking 준현금흐름) / `speculative_flow`(alts, trap_guard 최강). falsifiable 강→약: realized-price/MVRV > SOPR > stablecoin supply > funding(regime-dep) > NVT(degraded, worked-then-broke) > **halving(통계검정 금지, Schelling prior only)**. regime = R1 BOCPD+Hotelling T² 전이, feature=[realized-price slope, MVRV-Z, LTH supply Δ, SOPR, funding], Wyckoff 2D(trend × cost-basis-stress). **decoupling 실증 케이스 = on-chain exchange netflow (ETF 후 AP→custody 파이프로 깨짐)** = BB-2/BB-4 첫 실증.
- value_trap 자산별: crypto=impairment+forced-deleverage(LUNA/FTX) / FX=peso problem(터키리라, guard=CDS·tail-skew) / bond=credit default-cycle + duration inflation-persistence(guard=inflation·default gate, stock-bond corr sign flip=regime var).
- **★ 미결정 (사용자 선택 대기)**: 구현 순서 — (gemini) ETF→Crypto→Macro/FX/Bond vs (claude) Crypto→Rates·Credit signal→sector ETF→FX. commodity 는 R1 이미 설계분.

### 10.5 R3 통합 아키텍처 (crypto 데이터·closed-loop·다중시간척도)
- **crypto 데이터**: degrade proxy(가격/거래량만으로 MVRV 추정)는 **transition 에서 체계적 오류**(realized-price=stock 개념 vs 200wMA=flow → decoupling 순간 최대 괴리 = 최악 trap). → **CoinMetrics Community 무료 정식**(daily MVRV/realized-cap/LTH). netflow = 유료 도입 전까지 **guard 비활성 + band 보수화**. proxy 쓰려면 falsification gate 통과 1급 가설로만(naive 못 이기면 폐기). 위험순: MVRV-proxy < LTH-proxy < netflow(가짜 절대 금지).
- **closed-loop #1 레버리지 = append-only event ledger** (assumption-outcome 단일 계약, 하위 단계 = ledger 의 순수함수). join key = `(assumption_id, version)`. 실패모드 4 + 방어: silent 단절(deadline open-expectation + reconciliation orphan 경보) / 계약 drift(경계 schema validator fail-closed) / estimand 혼동(regime_ctx point-in-time 동결, 채점 시 재유도 금지) / 재주입 오염(개입 이벤트화 + post-intervention 새 stream).
- **최소 closed-loop**: crypto · MVRV 1개 · 7d forward · CoinMetrics · **역사 backtest 한방**(짧은 horizon × 긴 역사 → outcome 이미 존재 → 수백 closed loop 결정론 축적). 가정 = "regime R 내 MVRV 는 regime-median mean-revert". ★최소루프 = **backtestable 필수**(outcome 즉시).
- **다중 시간척도**: 모든 파라미터 = **event-time(resolved outcome 수)**, 단위 = horizon h. **자산클래스별 독립 FDR 스트림**(풀링 금지 — crypto 가 macro alpha 예산 독식 + exchangeability 붕괴). crypto 폭주 = debounce(material change 만 test) + dependence-robust FDR. macro 희소 = half-life 확대 + archetype partial-pooling(strength borrow) + mechanism-validation/사람 gate. macro stream dormant 정상.

### 10.6 R4 구현 specifics (bitemporal ledger · calibration · data-contract)
- **bitemporal ledger**: `valid_time`(데이터 날짜) vs `decision_time`(엔진 인지). 이벤트 11종: ASSUMPTION_CREATED(genesis) / PREDICTION_MADE{regime_ctx_snapshot, trigger_snapshot, horizon_h, deadline} / OUTCOME_OBSERVED / HOLD_REMEASURED / CANDIDATE_PROPOSED / RATIFIED(detector≠FDR≠사람 분리) / FDR_DECISION / TRANSITIONED(v_n→v_{n+1} 인과 edge) / RETIRED / DATA_CONTRACT_VIOLATION / CALIBRATION_CHANGED. 공통필드: event_id(ULID), seq(monotonic tie-break), schema_version, asset_class, parent_event_id, config_hash, data_vintage, crc. `state = reduce(pure_apply, sorted(events), init)`.
- **★ FDR 시간축 분리 (crux)**: online-FDR error control = **결정 순서**의 성질 → `FDR_DECISION` immutable, **decision_time 순으로만 재생**(valid_time 재정렬 = alpha-wealth 경로 변경 + 미래지식 사용 = 보장 파괴). late outcome = 해소 이벤트 append(wealth 되감기 X). Brier/DM retrospective 통계**만** valid_time 으로 재계산. 정렬 tie = (transaction_time, seq), late = full replay. jsonl = flock + .tmp→os.replace 원자성(또는 SQLite WAL).
- **calibration 기본값** (static YAML, 자산별): LORD++ crypto α=0.10·w0=0.05 / macro α=0.05·w0=0.025. BOCPD hazard λ=1/60(daily)·1/48(monthly). novelty χ² = 99th(crypto)·95th(macro) 분위. DM HAC lag = h−1. prequential N=90·hl45(crypto)·N=60·hl30(macro). Hotelling T² 소표본 = `F=(n−p)/(p(n−1))·T² ~ F_{p,n−p}`, **min n≥3p else suspend**.
- **data-contract gate (축D)**: ingestion ↔ 검증엔진 사이 Data Contract Validator, 이상 → **HOLD_SUSPENDED**(FDR 스트림 제외, alpha 소진 중단, 사람 확인 후 재개). crypto: netflow diff>5σ(재라벨링)·NVT 분모 0/결측. commodity: contract-roll OI 교차확인·만기±3d masking. macro: vintage diff(lag-1 join, |now−past|/past>thr = silent revision). Hard Suspend 권장.

### 10.7 R5 완결성 비평 — SATURATION + 구현 전 반영 2종
- **gemini 명시 saturation**: "구현 가능한 포화도 도달, 설계·통계 검증 레이어 매우 견고." (claude R5 = 채널 contention 으로 미수집, R1-R3 full + R4 crux 로 충분 반영)
- **신규 맹점 1 — cross-asset 종속성**: FDR 스트림 완전 분리(10.5)가 거시 regime 의 **cross-asset 동시영향**을 무시. 상위(거시) regime 변화 시 하위(crypto/equity) 자산 파라미터 **cascade reset** 필요 — 안 하면 구조변화를 "이상치 연속"으로 오인해 FDR 통제 상실. → 거시 base-layer regime 을 하위 자산 가정의 conditioning 으로 + T3 ATMS 의존전파로 해소.
- **신규 맹점 2 — Revision Drift**: 거시 지표 사후 수정 시 "당시 결정 vs 수정된 진실" 괴리 측정 루프 부재 → Brier calibration 신뢰도 저하. → revision-drift monitor(vintage diff 연계).
- **★ 재실패 지점 = 통계 아닌 인프라(ledger reducer)**: 11 event type 의 중앙 reducer 가 순서역전·비동기지연 처리 실패 시 파이프라인 붕괴. 예방 = **dummy-event TDD 먼저**(랜덤순서 주입 → 특정 decision_time state 100% 복원 증명 전까지 분석로직 작성 금지) + event schema gateway.
- **★ 우선 1수 = Walking Skeleton (구현 순서 확정)**: ① dummy 데이터(결측 포함)+정적룰로 ledger lifecycle(CREATED→RETIRED)+time-travel+Data Contract Validator **배선만 먼저 증명** → ② dummy 룰 제거 + 실제 통계 모듈 플러그인 → ③ 최소 backtest 루프(로직 증명). **로직+인프라 동시 테스트 금지**.

> **자문 종결 (5R saturation)**: R1(거시·통계 설계) → R2(instrument universe) → R3(통합 아키텍처) → R4(구현 specifics) → R5(완결성 비평 = saturation 선언). raw 5 file: `.consult-button-R{1..5}.txt`.

---

## 11. 구현 종결 (V0~V7, 2026-05-29) — 전 11 모듈 self-test PASS + 25 structure regression PASS

> SSOT 설계 = §10. 본 절 = 실제 코드 산물·계약 표면. progress = `progress-T2-assumption-20260529.md` ckpt-202605292355.

### 11.1 구현 파일 (BB-1~5 + V7 보강)
| 모듈 | BB | 핵심 |
|---|---|---|
| `core/assume/card_contract.py` | 공유계약 | AssumptionCardLike(Protocol)+BaseAssumptionFields(frozen)+assert_falsifiable. ★btn-Codlearn 합의=card_contract.py 만 btn-button 소유 |
| `core/brain/macro_assumption_card.py` | BB-1 | 6+1 AnomalyCase→버전드 MacroAssumptionCard, FALSIFICATION_BY_CASE, anomaly↔card 어댑터, add_candidate_card |
| `core/brain/correction_loop.py` | BB-2 | LiveCorrelationLoop: JM divergence harvest→ingest_correction(live)+recall PIT mask+attach_to_classifier |
| `core/structure/assumption_validation_engine.py` | BB-4 | card.kind dispatch→holds_now + 자산클래스 격리 LORD++ FDR + 부활차단 + compile_falsification. **V7 배선**: ②e-process AND-gate·③power 게이트·①cascade parent_id/action·④DOMAIN_ESTIMATION_POLICY |
| `core/regime/regime_discovery.py` | BB-3 | BOCPD timing + Hotelling/χ² novelty + online-FDR wrap + HumanApprovalGate(승격=사람) + bnpy seam. **V7 ⑤**: sequestered_confirm(anytime-valid)+false_positive_rate(정지 합성)+require_sequestered |
| `core/structure/archetype.py` | BB-5 | equity 5 + commodity 3(carry/seasonal/inventory) + crypto 3(monetary_store/network_utility/speculative_flow) = 11종 discriminated union + DEFAULT_SECTOR_ARCHETYPE 8섹터 추가 |
| `config/archetypes/*.yaml` | BB-5 | commodity_carry/seasonal/inventory/monetary_store/network_utility/speculative_flow 6종 신규 (총 11) |
| `core/structure/commodity_assumptions.py` | BB-5 | carry_forward_slope(prequential sign-flip)·seasonal_f_test(월더미 F+STL strength)·variance_ratio(Lo-MacKinlay)·threshold_regression(Hansen)·oversupply_decoupling·mvrv_mean_revert·netflow_guard(비활성 stub) + build_commodity/crypto_cards |
| `core/structure/hierarchical_fdr.py` | V7 신규 | pvalue_to_evalue(VS calibrator e=0.5/√p)·EProcessSpender(anytime-valid, Ville)·falsification_power/protectable·HierarchicalFDRCascade(BB 독립substrate+de-risking bypass) |

### 11.2 V7 보강 (CONSULT-DECISIONS-whole §btn-button, btn-Codlearn 전체구조 3R 확정)
- **① hierarchical FDR cascade (Benjamini-Bogomolov)**: 거시 regime=부모, **독립 substrate** 엄격 통과해야 자식 family FDR 예산 해금(post-selection 차단). de-risking 보호액션만 per-stream 우회, **신규진입 부모게이트 우회 금지**. 검증: 부모 미통과→new_entry locked / de_risking bypass / 비독립 substrate→부모 통과불가.
- **② e-process alpha-spending (anytime-valid)**: LORD++ 위 test-martingale, Ville 부등식 E≥1/α 기각, 기각 시 리셋(spend). 최종 FDR_significant = LORD++ ∧ e-process. 검증: 200 null-스트림 1/α 돌파 7회(≤α·200=10) = optional-stopping robust.
- **③ falsification POWER 게이트**: 형식 존재 + 검정력 하한(power_ref_effect=0.5, floor=0.5, min_baseline_n per-domain). power<floor/baseline 부재(crypto post-ETF)→protectable=False→fdr_significant 무효. 검증: n=8→power 0.345→차단.
- **④ per-domain 추정 다형성**: DOMAIN_ESTIMATION_POLICY(eprocess_decay·update_period_days·min_baseline_n) — crypto 빠른 망각(0.90)/macro 느린(0.99)·희소 baseline(24).
- **⑤ 거짓 regime 방어선**: optimizer 미접촉 sequestered stream anytime-valid 확인(사전 threshold, 사후 튜닝 불가) + 정지 합성데이터 주입 FP rate 정량화(=0.000). 승격 = 사람비준 AND sequestered confirmed 둘 다.

### 11.3 T3(btn-Codlearn) 소비 계약 표면 (하위호환)
- `ValidationVerdict` 4 신규 필드: `eprocess_significant`/`power`/`protectable`/`cascade_reason` (기본값 보존, 기존 필드 불변).
- `AssumptionValidationEngine.__init__`: `use_eprocess`/`power_floor`/`power_ref_effect`/`cascade` 옵션. `validate(..., parent_id, action)` 2 신규 kwarg(기본 new_entry).
- 신규 export: `HierarchicalFDRCascade`·`EProcessSpender`·`falsification_protectable`·`estimation_policy`·`build_commodity_cards`/`build_crypto_cards`·`OnlineRegimeDiscovery.sequestered_confirm`/`false_positive_rate`.
- **미해결(R4 후보, 사용자 결정)**: online FDR/optional-stopping/anytime-valid 단독 심화 자문. cross-asset cascade 의존전파·revision-drift = T3 ATMS / btn-Inv vintage 조율.

### 11.4 환경
scipy 1.17.1 사용(F/norm 분포; 부재 시 numpy fallback 내장). bnpy/ruptures 미설치=graceful seam. py=`/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe`, 콘솔 한글=`PYTHONIOENCODING=utf-8`.

---

## 12. R4/R5 robustness 업그레이드 (e-value backbone, 2026-05-29) — btn-Codlearn 전체구조 자문

> SSOT = §R4·§R5 (CONSULT-DECISIONS-whole-20260529.md). 신규 = `core/structure/eprocess_backbone.py` + 엔진 backbone 옵션 + V&V property test. 동기 = 금융 regime **자기상관**에서 p값 LORD++/SAFFRON 독립가정 취약 → e값(임의의존·optional-stopping robust)으로.

### 12.1 e-process backbone (R4 최우선)
- **MixtureSPRTEProcess**: Robbins-Siegmund 폐형 mixture test martingale `E_t=(1+τ²n)^{-1/2}·exp(τ²S²/(2(1+τ²n)))`, S=Σx. E_0=1 nonneg martingale → Ville `P(sup E_t≥1/α)≤α`. optional-stopping·임의의존 robust.
- **ELOND**: e값 구동 online FDR `reject_i ⟺ e_i≥1/α_i, α_i=α·γ_i·(D_{i-1}+1)`, γ_t=(6/π²)/t². e값 평균≤1+Markov → **임의의존 FDR≤α** (p값 LOND 의존가정 불요 = 자기상관 robust). 단일 e-substrate, readout 2개(e-process=baseline 변경 1급 증거 / e-LOND=발견율).
- **replay reorder-invariance**: 폐형 E=f(S,n), S·n 순서불변 → 증분 ℓ_t=E_t/E_{t-1} (dt,vt) 로그, as-of=dt≤cut 곱(dt내 순서무관). `replay_value` property-test 로 보호.
- **엔진 배선**: `AssumptionValidationEngine(fdr_backbone='lord'|'elond')` — 'lord' 기본(하위호환), 'elond' 면 e-LOND 가 fdr_significant 주체. verdict `fdr_backbone`/`elond_significant` 노출.

### 12.2 graph-structured online e-allocation (R4-B)
- **GraphEAllocation**: W(node,t), 거시 DAG wealth 분할 × node-local ELOND. 부모 regime e-process 1/α 돌파→자식 family wealth 해금 / 부모 decay→자식 freeze(de-risk only) / 부모 잠김+de-risk→bypass(보수 budget) / 신규진입 우회 금지. reorder-invariant. HierarchicalFDRCascade(§11.2①) 의 e-wealth 일반화.

### 12.3 spec sentinel 층 (R5-C, wrong-H0 방어)
- e-process 는 **고른 null 상대**만 anytime-valid(틀린 null 무방비). **SpecSentinel**: (a) PIT uniformity model-free test martingale(Vovk betting `∏(1+λ(2u-1))` λ-mix) (b) exchangeability test martingale(conformal rank 추세 betting, 교환성 붕괴=regime 공유). 점화→primary e validity 강등→`action='abstain'`(judge expected-errored→abstain 동형).

### 12.4 decay vs regime (R5-D)
- **ReverseEProcess**: null='최근 edge=과거 baseline', alt='최근<과거' — `(baseline-edge)/sd` 를 mixture SPRT → wealth 상승 중 slope↓ 면 점화(decay). **e_cusum**: SR/CUSUM reset e-detector changepoint. **classify_decay_vs_regime**: regime=다수 sibling 동기화+exchangeability 동반점화→`parent_freeze` / decay=node 특이·monotone·exchangeability 침묵→`node_de_risk`.

### 12.5 V&V (R5 유일 material 잔여) + 계약 표면
- `tests/structure/test_eprocess_backbone_properties.py` (14 property test): P1 replay reorder-invariance(20 perm) / P2 Ville false-alarm ≤2α(400 trial) / P3 e-LOND AR(1) 자기상관 robust / P4 graph 안전축(잠김 부모 new_entry 절대 reject X). 전 39 structure regression PASS(기존 25 + 14).
- **T3 소비 export**: `MixtureSPRTEProcess`·`ELOND`·`GraphEAllocation`·`SpecSentinel`·`ReverseEProcess`·`e_cusum`·`classify_decay_vs_regime`. 엔진 `fdr_backbone` 옵션 + verdict 2 신규 필드(하위호환).
- **잔여(practical saturation, R5)**: 추가 자문 ROI 음 → 엔지니어링·운영 규율 영역. graph×online×임의의존 joint 이론 빈약(유효하나 power 보수적). fill 내생성=소액 live ramp 추정(btn-Inv). meta-reflexivity=hash-commit 사전등록(설계 前). 인프라 DR=모델 밖.
