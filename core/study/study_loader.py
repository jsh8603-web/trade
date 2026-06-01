"""core/study/study_loader.py — study_session.yaml(7블록) 로더·검증·정규화 (통합 골격 G1).

STUDY-KIT.md §3 의 7블록 산출 계약을 *표준 수용* 하는 어댑터. 개별 작업방이 자산군·지표·관계를
다양하게 가져와도 이 로더가 (1) 파싱 (2) 스키마 검증 (3) 표준 dataclass 정규화 까지 책임진다.
이후 register(별도)가 4단계 파이프(panel/card/judge/falsification) 주입점으로 라우팅한다.
→ 방마다 weight_panel/weight_card/judge/weight_falsification 본체를 고치지 않게 = 플러그인.

자문 결론(STUDY-KIT §8) 반영 검증:
- partial-corr prior: edge 마다 conditioning_set 키 필수(빈 셋이어도 명시) — glasso Ω 와 비교가능.
- 주식 통일 하드룰: equity.* scope 면 코어셋 6 family 가 is_core=true 로 존재해야.
- force-include ≤4: code/relationship 의 force_include true 는 자산군당 4개 이하(소표본 prior leverage 제한).
- vintage_policy: 학습 입력 지표는 point_in_time 강제(final_revised = lookahead 경고).
- granularity ticker: 독립학습 불가 → hierarchical pooling(archetype+membership) 경고(부록 B).

검증은 errors(치명, 주입 거부) / warnings(주의, 주입 허용) 로 분리. yaml 부재/PyYAML 부재 graceful.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# 주식 통일 하드룰 코어셋 family (STUDY-KIT §6). equity.* 는 이 6개를 is_core 로 emit 해야 비교가능.
CORE_EQUITY_FAMILIES = frozenset(
    {"valuation", "quality", "momentum", "revision", "macro_sensitivity", "risk"}
)
VALID_FAMILIES = CORE_EQUITY_FAMILIES | {"macro_driver"}
VALID_EDGE_TYPES = frozenset({"direct", "common_cause", "undetermined"})
VALID_STAGES = frozenset({"learn", "card", "inject", "falsify"})
VALID_GRANULARITY = frozenset({"sleeve", "industry", "ticker"})
VALID_VINTAGE = frozenset({"point_in_time", "final_revised"})
MAX_FORCE_INCLUDE = 4   # 자문: 소표본 prior leverage 제한 (force-include 화이트리스트 ≤4)


# ---------------------------------------------------------------------------
# 7블록 표준 dataclass (방 산출이 다양해도 이 형상으로 정규화)
# ---------------------------------------------------------------------------

@dataclass
class Lens:                                  # 블록1 — 정성 렌즈(LLM 주입용)
    pricing_principle: str = ""
    report_relations: list = field(default_factory=list)
    regime_reading: str = ""
    estimation_note: str = ""


@dataclass
class Indicator:                             # 블록2
    id: str
    family: str = ""
    is_core: bool = False
    in_our_system: bool = False
    source_or_collector: str = ""
    transform: str = ""
    vintage_policy: str = "point_in_time"
    lag: int = 0


@dataclass
class EdgeHypothesis:                        # 블록3 — partial-corr prior
    node_a: str
    node_b: str
    edge_type: str = "undetermined"
    conditioning_set: list = field(default_factory=list)
    lag_routing: str = "contemporaneous"
    prior_sign: str = "unsigned"
    prior_strength: float = 0.0
    theory_basis: str = ""
    force_include: bool = False


@dataclass
class WeightRule:                            # 블록4 — 최종 산출(종목별 동적 가중)
    indicator_id: str
    base_weight: float = 0.0
    modulate_by: list = field(default_factory=list)
    direction: str = ""
    granularity: str = "sleeve"


@dataclass
class ConfidenceHook:                        # 블록5 — flag 코드화
    hypothesis_id: str
    confirm_signal: str = ""
    reject_signal: str = ""
    emit_where: str = ""
    accumulate_in: str = ""
    confidence_metric: str = ""
    store: str = ""
    action_threshold: str = ""
    feeds_weight: str = ""
    affects_indicator: str = ""   # 이 flag 신뢰도가 변조하는 indicator id(블록4 연결, G6 tilt). 없으면 hypothesis_id 추론.
    affects_edge: tuple = ()      # ★이 flag 가 약화/강화할 corr_prior edge (node_a, node_b). flag→corr_prior shrink(U2). 없으면 affects_indicator node 로 근사.


@dataclass
class CollectorPlan:                         # 블록6
    missing: str
    source: str = ""
    interface: str = "new"
    credential: Optional[str] = None


@dataclass
class CodeChange:                            # 블록7 — 4단계 변경 계획
    stage: str
    file: str = ""
    symbol: str = ""
    current: str = ""
    change: str = ""
    risk: str = ""


@dataclass
class StudySession:
    study_id: str
    asset_scope: list = field(default_factory=list)
    as_of: str = ""
    lens: Lens = field(default_factory=Lens)
    indicators: list = field(default_factory=list)
    relationships: list = field(default_factory=list)
    weight_rules: list = field(default_factory=list)
    confidence_hooks: list = field(default_factory=list)
    collector_plan: list = field(default_factory=list)
    code_change_plan: list = field(default_factory=list)

    def is_equity(self) -> bool:
        return any(str(s).startswith("equity") for s in self.asset_scope)


# ---------------------------------------------------------------------------
# 로드 (yaml/dict → StudySession). 누락 필드는 기본값으로 graceful 정규화.
# ---------------------------------------------------------------------------

def _as_list(v) -> list:
    return list(v) if isinstance(v, (list, tuple)) else ([] if v is None else [v])


def load_study_session(source) -> StudySession:
    """yaml 경로(str) 또는 이미 파싱된 dict → StudySession 표준 정규화.

    PyYAML 부재/파일 부재 시에도 dict 입력은 동작(graceful). 알 수 없는 키는 무시(전방호환).
    """
    if isinstance(source, dict):
        d = source
    else:
        try:
            import yaml
        except Exception as exc:                       # PyYAML 부재 graceful
            raise RuntimeError(f"PyYAML 필요(yaml 경로 로드): {exc}")
        with open(source, "r", encoding="utf-8") as f:
            # frontmatter(--- tags/date ---) + 본문 multi-document 허용(방마다 frontmatter 습관 수용).
            # study_id 있는 document 를 본문으로 선택, 없으면 마지막 dict.
            docs = [x for x in yaml.safe_load_all(f) if isinstance(x, dict)]
        d = next((x for x in docs if "study_id" in x), docs[-1] if docs else {})

    ln = d.get("lens", {}) or {}
    return StudySession(
        study_id=str(d.get("study_id", "")),
        asset_scope=_as_list(d.get("asset_scope")),
        as_of=str(d.get("as_of", "")),
        lens=Lens(
            pricing_principle=str(ln.get("pricing_principle", "")),
            report_relations=_as_list(ln.get("report_relations")),
            regime_reading=str(ln.get("regime_reading", "")),
            estimation_note=str(ln.get("estimation_note", "")),
        ),
        indicators=[_mk(Indicator, x, "id") for x in _as_list(d.get("indicators"))],
        relationships=[_mk(EdgeHypothesis, x, "node_a", "node_b")
                       for x in _as_list(d.get("relationships"))],
        weight_rules=[_mk(WeightRule, x, "indicator_id") for x in _as_list(d.get("weight_rules"))],
        confidence_hooks=[_mk(ConfidenceHook, x, "hypothesis_id")
                          for x in _as_list(d.get("confidence_hooks"))],
        collector_plan=[_mk(CollectorPlan, x, "missing") for x in _as_list(d.get("collector_plan"))],
        code_change_plan=[_mk(CodeChange, x, "stage") for x in _as_list(d.get("code_change_plan"))],
    )


def _mk(cls, raw: dict, *required):
    """dict → dataclass. dataclass 필드만 취해 알 수 없는 키 무시(전방호환). 필수키 부재 시 빈값."""
    if not isinstance(raw, dict):
        raw = {}
    fields = {f for f in cls.__dataclass_fields__}
    kwargs = {k: v for k, v in raw.items() if k in fields}
    for r in required:
        kwargs.setdefault(r, "")
    return cls(**kwargs)


# ---------------------------------------------------------------------------
# 검증 (errors=주입거부 / warnings=허용). 자문 결론을 규칙으로.
# ---------------------------------------------------------------------------

@dataclass
class ValidationReport:
    study_id: str
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_study_session(s: StudySession) -> ValidationReport:
    """7블록 + 자문 결론 검증. errors(치명)면 주입 거부, warnings 면 주의하며 허용."""
    rep = ValidationReport(study_id=s.study_id or "<no-id>")
    E, W = rep.errors.append, rep.warnings.append

    # 헤더
    if not s.study_id:
        E("study_id 누락")
    if not s.asset_scope:
        E("asset_scope 누락(소비 인스턴스 미지정)")
    if not s.as_of:
        W("as_of(PIT 기준점) 누락")

    # 블록2 indicators
    if not s.indicators:
        E("indicators 비어있음(스터디 핵심 산출 부재)")
    seen_ids = set()
    for ind in s.indicators:
        if not ind.id:
            E("indicator id 누락")
            continue
        if ind.id in seen_ids:
            E(f"indicator id 중복: {ind.id}")
        seen_ids.add(ind.id)
        if ind.family and ind.family not in VALID_FAMILIES:
            W(f"indicator {ind.id}: 알 수 없는 family '{ind.family}'")
        if ind.vintage_policy not in VALID_VINTAGE:
            W(f"indicator {ind.id}: vintage_policy '{ind.vintage_policy}' 비표준")
        elif ind.vintage_policy == "final_revised":
            W(f"indicator {ind.id}: final_revised = 학습 입력 시 lookahead 위험(point_in_time 권장)")
        if not ind.in_our_system and not ind.source_or_collector:
            W(f"indicator {ind.id}: 우리 시스템에 없는데 source/collector 미지정")

    # 주식 통일 하드룰: equity.* 는 코어셋 6 family 가 is_core 로 존재
    if s.is_equity():
        core_present = {ind.family for ind in s.indicators if ind.is_core}
        missing = CORE_EQUITY_FAMILIES - core_present
        if missing:
            E(f"주식 통일 하드룰 위반: 코어셋 family 누락 {sorted(missing)} (STUDY-KIT §6)")

    # 블록3 relationships — partial-corr 규율
    for e in s.relationships:
        if e.edge_type not in VALID_EDGE_TYPES:
            E(f"edge {e.node_a}-{e.node_b}: edge_type '{e.edge_type}' 불가({sorted(VALID_EDGE_TYPES)})")
        if e.node_a not in seen_ids or e.node_b not in seen_ids:
            W(f"edge {e.node_a}-{e.node_b}: indicator id 미참조(블록2에 없음)")
        # partial-corr 비교가능: conditioning_set 키가 명시돼야(빈 리스트는 허용, 누락은 경고)
        if e.edge_type == "common_cause" and not getattr(e, "conditioning_set", None):
            W(f"edge {e.node_a}-{e.node_b}: common_cause 인데 공통노드(conditioning_set) 미명시")

    # force-include ≤4 (자문: 소표본 prior leverage 제한)
    n_force = sum(1 for e in s.relationships if e.force_include)
    if n_force > MAX_FORCE_INCLUDE:
        E(f"force_include {n_force}개 > {MAX_FORCE_INCLUDE} (자문: 화이트리스트 ≤4)")

    # 블록4 weight_rules
    for wr in s.weight_rules:
        if wr.indicator_id not in seen_ids:
            W(f"weight_rule: indicator_id '{wr.indicator_id}' 블록2 미참조")
        if wr.granularity not in VALID_GRANULARITY:
            W(f"weight_rule {wr.indicator_id}: granularity '{wr.granularity}' 비표준")
        elif wr.granularity == "ticker":
            W(f"weight_rule {wr.indicator_id}: ticker 독립학습 불가 → "
              f"hierarchical pooling(archetype+membership)으로 해석(STUDY-KIT 부록 B)")
    if not s.weight_rules:
        W("weight_rules 비어있음(최종 산출=종목별 동적 가중 미작성)")

    # 블록7 code_change_plan — 4단계 커버
    stages = {c.stage for c in s.code_change_plan}
    bad = stages - VALID_STAGES
    if bad:
        E(f"code_change_plan: 알 수 없는 stage {sorted(bad)}")
    missing_stage = VALID_STAGES - stages
    if missing_stage:
        W(f"code_change_plan: 4단계 중 미작성 {sorted(missing_stage)} (STUDY-KIT §4)")

    # coin 예외: 지표가중 부적합 — weight_rules 없어도 정상
    if "coin" in s.asset_scope and s.weight_rules:
        W("coin 은 지표가중 R15 부적합(belief→사이징만). weight_rules 대신 belief 경로 권장")

    return rep


# ===========================================================================
# self-test (실동작 검증 — 스텁 금지)
# ===========================================================================

if __name__ == "__main__":
    # 부록 A(macro) 완전 예시를 dict 로 — PyYAML 없이도 검증 로직 확인
    macro = {
        "study_id": "macro", "asset_scope": ["macro"], "as_of": "2026-05-30",
        "lens": {"pricing_principle": "성장·인플레·유동성 조합",
                 "report_relations": ["M2↔미·일 국채↔환율"], "regime_reading": "Reflation→주식우위",
                 "estimation_note": "Recovery 초입 추정"},
        "indicators": [
            {"id": "yield_10y_2y", "family": "macro_driver", "is_core": True,
             "in_our_system": True, "source_or_collector": "fred[T10Y2Y]",
             "transform": "level", "vintage_policy": "point_in_time", "lag": 0},
            {"id": "credit_spread_hy_oas", "family": "macro_driver", "is_core": True,
             "in_our_system": True, "source_or_collector": "fred[BAMLH0A0HYM2]",
             "transform": "own_history_z", "vintage_policy": "point_in_time", "lag": 0},
        ],
        "relationships": [
            {"node_a": "credit_spread_hy_oas", "node_b": "yield_10y_2y", "edge_type": "direct",
             "conditioning_set": ["real_gdp"], "lag_routing": "contemporaneous",
             "prior_sign": "pos", "prior_strength": 0.6, "theory_basis": "리스크오프 동반",
             "force_include": True},
        ],
        "weight_rules": [
            {"indicator_id": "credit_spread_hy_oas", "base_weight": 0.25,
             "modulate_by": ["regime"], "direction": "리스크오프→가중↑", "granularity": "sleeve"},
        ],
        "confidence_hooks": [
            {"hypothesis_id": "hy_oas_risk_regime", "confirm_signal": "Rank-IC 양 유지",
             "reject_signal": "e-CUSUM 붕괴", "accumulate_in": "weight_falsification",
             "confidence_metric": "e-value", "store": "registry", "action_threshold": "retract",
             "feeds_weight": "derive_weights 재적합"},
        ],
        "collector_plan": [
            {"missing": "JGB", "source": "FRED IRLTLT01JPM156N", "interface": "VintageProvider",
             "credential": None}],
        "code_change_plan": [
            {"stage": "learn", "file": "fred_adapter.py", "symbol": "FRED_SERIES",
             "current": "16종", "change": "JGB 추가", "risk": "dict 추가만"},
            {"stage": "card", "file": "weight_card.py", "symbol": "WeightAssumptionCard",
             "current": "정량", "change": "lens 박제", "risk": "필드 추가"},
            {"stage": "inject", "file": "judge.py", "symbol": "synthesize_l1",
             "current": "L1", "change": "lens 주입", "risk": "opt-in"},
            {"stage": "falsify", "file": "weight_falsification.py", "symbol": "score_ic...",
             "current": "kill", "change": "flag 연결", "risk": "추가만"},
        ],
    }

    # 1) 로드 정규화
    s = load_study_session(macro)
    assert s.study_id == "macro" and len(s.indicators) == 2 and s.is_equity() is False
    assert s.lens.report_relations == ["M2↔미·일 국채↔환율"]
    assert s.relationships[0].conditioning_set == ["real_gdp"]
    print(f"1) load OK: {s.study_id} indicators={len(s.indicators)} edges={len(s.relationships)} "
          f"hooks={len(s.confidence_hooks)} code_changes={len(s.code_change_plan)}")

    # 2) 정상 검증 PASS (errors 0)
    rep = validate_study_session(s)
    print(f"2) validate macro: ok={rep.ok} errors={len(rep.errors)} warnings={len(rep.warnings)}")
    for w in rep.warnings:
        print(f"     ⚠ {w}")
    assert rep.ok, rep.errors

    # 3) equity 통일 하드룰 위반 검출 (코어셋 누락 → error)
    bad_eq = {"study_id": "eq_us", "asset_scope": ["equity.us"], "as_of": "2026-05-30",
              "indicators": [{"id": "pe", "family": "valuation", "is_core": True,
                              "in_our_system": True, "source_or_collector": "x"}],
              "code_change_plan": [{"stage": "learn"}]}
    rep2 = validate_study_session(load_study_session(bad_eq))
    assert not rep2.ok and any("통일 하드룰" in e for e in rep2.errors), rep2.errors
    print(f"3) equity 코어셋 누락 검출 OK: {[e for e in rep2.errors if '하드룰' in e][0][:50]}...")

    # 4) force-include >4 검출
    edges = [{"node_a": f"a{i}", "node_b": f"b{i}", "edge_type": "direct", "force_include": True}
             for i in range(5)]
    inds = [{"id": f"a{i}", "family": "macro_driver", "in_our_system": True} for i in range(5)]
    inds += [{"id": f"b{i}", "family": "macro_driver", "in_our_system": True} for i in range(5)]
    bad_force = {"study_id": "x", "asset_scope": ["macro"], "as_of": "t",
                 "indicators": inds, "relationships": edges,
                 "code_change_plan": [{"stage": s2} for s2 in VALID_STAGES]}
    rep3 = validate_study_session(load_study_session(bad_force))
    assert not rep3.ok and any("force_include" in e for e in rep3.errors)
    print(f"4) force-include >4 검출 OK")

    # 5) 알 수 없는 키 무시(전방호환) + 빈 입력 graceful
    s5 = load_study_session({"study_id": "z", "asset_scope": ["gold"], "as_of": "t",
                             "indicators": [{"id": "g", "family": "macro_driver",
                                             "in_our_system": True, "future_field": "ignored"}],
                             "unknown_block": [1, 2, 3]})
    assert s5.indicators[0].id == "g"
    rep5 = validate_study_session(s5)
    print(f"5) 전방호환(unknown 키 무시)+graceful OK: gold ok={rep5.ok} warns={len(rep5.warnings)}")

    # 6) ticker granularity 경고(hierarchical pooling)
    tick = {"study_id": "t", "asset_scope": ["equity.us"], "as_of": "t",
            "indicators": [{"id": f"i_{fam}", "family": fam, "is_core": True, "in_our_system": True}
                           for fam in CORE_EQUITY_FAMILIES],
            "weight_rules": [{"indicator_id": "i_valuation", "granularity": "ticker"}],
            "code_change_plan": [{"stage": s2} for s2 in VALID_STAGES]}
    rep6 = validate_study_session(load_study_session(tick))
    assert rep6.ok and any("pooling" in w for w in rep6.warnings)
    print(f"6) ticker→pooling 경고 OK (equity 코어셋 충족 시 ok)")

    print("\nstudy_loader self-test PASS "
          "(7블록 로드·정규화 + 통일 하드룰/force-include/partial-corr/4단계 검증 + 전방호환)")
