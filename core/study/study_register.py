"""core/study/study_register.py — study_session.yaml → production end-to-end wiring (골격 G6).

★사용자 확정: main 은 방 산출(yaml)을 받아 **바로 production 되게 wiring 까지** 완료한다.
이 모듈이 그 통합 오케스트레이터다. G1~G5 골격을 묶어 7블록 yaml 한 개를:

  load+validate(G1) → panel manifest 등록(G2) → lens 등록(G3) → confidence_hooks 등록(G4)
  → weight_card 생성·AssumptionRegistry 등록 → judge 호출 인자(card+lens+regime) 제공

까지 연결한다. opt-in 게이트:
  - INV_R15_WEIGHTS: 가중치 카드 등록 + flag tilt 동적 재적합(off=등록 안 함, 무회귀).
  - INV_STUDY_LENS: lens 주입(lens_store 내부 게이트).
둘 다 off 면 register 는 검증만 하고 production 경로 미개통(byte-identical 무회귀).

stock_track/judge 본체는 안 고친다 — `prepare_judge_call` 이 judge() 에 그대로 넘길 dict 를
반환하는 facade. 호출부(stock_track)가 study_register 를 옵션으로 참조해 카드·렌즈를 받는다.
"""

from __future__ import annotations

import os
from typing import Optional

import numpy as np

from core.study.study_loader import (
    StudySession, ValidationReport, load_study_session, validate_study_session,
)
from core.study import panel_manifest as pm
from core.study import lens_store as ls
from core.study.flag_router import FlagRouter
from core.assume.weight_card import WeightAssumptionCard, DEFAULT_WEIGHT_CAP, DEFAULT_L1_FLOOR


_ENV_R15 = "INV_R15_WEIGHTS"


def is_r15_enabled() -> bool:
    """가중치 카드 등록 + flag tilt opt-in 게이트. off = production 경로 미개통(무회귀)."""
    return str(os.environ.get(_ENV_R15, "")).strip().lower() in ("1", "true", "on", "yes")


def _domain_of(scope: str) -> str:
    """asset_scope → WeightAssumptionCard.domain Literal(macro/equity/commodity/crypto) 매핑."""
    s = str(scope).lower()
    if s.startswith("equity") or s.startswith("reit"):
        return "equity"
    if s.startswith("coin") or s.startswith("crypto"):
        return "crypto"
    if s.startswith("commodity") or s.startswith("gold"):
        return "commodity"
    return "macro"          # macro / bond / bond_cash / 기타 = 거시 도메인


def _check_raw_completeness(yaml_path: str) -> list:
    """★v2 바탕 raw 완비 검사. study-research/{sid}/ 에 2-1/2-2/2-3 산출 raw 가 전부 있나.

    - direction.md       : 2-1 방향성(자문 다회 ①②③)
    - raw/round-*.md      : 2-1 자문 라운드 원문(다회)
    - raw/theory-notes.md : 2-2 이론 학습
    - raw/validation-*.md : 2-3 실데이터 시계열 검증
    하나라도 없으면 error 반환(주입 거부) — 바탕 없는 코드화 차단.
    """
    import os
    import glob as _glob
    d = os.path.dirname(os.path.abspath(yaml_path))
    raw = os.path.join(d, "raw")
    errs = []
    if not os.path.isfile(os.path.join(d, "direction.md")):
        errs.append("v2 raw 게이트: direction.md 없음(2-1 방향성·자문 다회 미산출)")
    if not _glob.glob(os.path.join(raw, "round-*.md")):
        errs.append("v2 raw 게이트: raw/round-*.md 없음(자문 다회 라운드 미수행)")
    if not os.path.isfile(os.path.join(raw, "theory-notes.md")):
        errs.append("v2 raw 게이트: raw/theory-notes.md 없음(2-2 이론학습 미수행)")
    if not _glob.glob(os.path.join(raw, "validation-*.md")):
        errs.append("v2 raw 게이트: raw/validation-*.md 없음(2-3 실데이터 시계열 검증 미수행)")
    return errs


def _scope_of(scope: str) -> str:
    """asset_scope → WeightAssumptionCard.scope Literal(global/sector/asset/macro) 매핑.

    카드 적용 범위: equity/reit=sector(섹터·산업 단위), macro/bond=macro(거시), 나머지(commodity/
    gold/coin)=asset(개별 자산). 원래 study scope 문자열은 카드 id(weight.{study_id}.*)에 보존됨.
    """
    s = str(scope).lower()
    if s.startswith("equity") or s.startswith("reit"):
        return "sector"
    if s.startswith("macro") or s.startswith("bond"):
        return "macro"
    return "asset"          # commodity / gold / coin / crypto = 개별 자산


def _corr_level_of(scope: str) -> str:
    """asset_scope → corr_prior shrink level(macro/micro) 매핑. ★reflexive loop 가드(U3).

    거시·채권 study 는 cross-sleeve driver 라 belief→corr_prior 누수 시 macro Σ 되먹임(종목 flag→
    "리스크 극저" 오판→drawdown 직전 최대 베팅). 따라서 macro/bond=level 'macro'(belief 차단 no-op),
    나머지(equity/reit/commodity/gold/crypto)=level 'micro'(within-sleeve 약화 허용). single-writer
    불변식(CONSULT-DECISIONS-layering-20260530.md): _macro 는 실현 cross-sleeve 수익률·regime 전용.
    """
    s = str(scope).lower()
    if s.startswith("macro") or s.startswith("bond"):
        return "macro"
    return "micro"          # equity / reit / commodity / gold / coin / crypto = within-sleeve


class StudyRegister:
    """여러 방의 study_session.yaml 을 받아 4단계 파이프에 production wiring 하는 통합 레지스트리."""

    def __init__(self, *, assumption_registry=None):
        self.sessions: dict = {}                 # study_id → StudySession
        self.reports: dict = {}                  # study_id → ValidationReport
        self.panels = pm.PanelManifestRegistry()  # G2
        self.lenses = ls.LensStore()              # G3
        self.flags = FlagRouter()                 # G4
        self.cards: dict = {}                    # study_id → WeightAssumptionCard
        self.reg = assumption_registry           # core.assume.registry.AssumptionRegistry (옵션)

    # --- 등록 (yaml 한 개를 전 골격에 wiring) ---
    def register(self, source, *, panel_instance_id: Optional[str] = None,
                 require_raw: bool = True) -> ValidationReport:
        s = load_study_session(source)                       # G1 로드
        rep = validate_study_session(s)                      # G1 검증
        # ★v2 바탕 raw 완비 게이트(사용자 정정): 자문 다회·이론·실데이터 검증 raw 없으면 산출 거부.
        # path 입력 시에만 검사(dict self-test 는 skip). 자문 그대로 코드화·종료 차단.
        if require_raw and isinstance(source, str):
            for e in _check_raw_completeness(source):
                rep.errors.append(e)
        self.reports[s.study_id] = rep
        if not rep.ok:                                       # errors → 주입 거부(production 미개통)
            return rep

        self.sessions[s.study_id] = s
        self.panels.register(pm.from_study_session(s, panel_instance_id=panel_instance_id))   # G2
        ls.from_study_session(s, self.lenses)                # G3
        for hook in s.confidence_hooks:                      # G4
            self.flags.register(hook, indicator_id=self._hook_indicator(hook, s))

        # 가중치 카드 생성·등록 (opt-in). off 면 production 경로 미개통.
        if is_r15_enabled():
            card = self._build_card(s)
            if card is not None:
                self.cards[s.study_id] = card
                if self.reg is not None:
                    self.reg.register(card)
        return rep

    # --- flag hook → indicator 연결(블록5 affects_indicator 우선 → hypothesis_id 추론) ---
    @staticmethod
    def _hook_indicator(hook, s: StudySession) -> Optional[str]:
        if getattr(hook, "affects_indicator", ""):
            return hook.affects_indicator
        ind_ids = {i.id for i in s.indicators}
        if hook.hypothesis_id in ind_ids:                    # hypothesis_id 가 곧 indicator
            return hook.hypothesis_id
        return None                                          # 미연결 = tilt 무영향(graceful)

    # --- weight_rules(블록4) → WeightAssumptionCard ---
    def _build_card(self, s: StudySession, *, regime_id: Optional[str] = None,
                    apply_tilt: bool = True) -> Optional[WeightAssumptionCard]:
        rules = [wr for wr in s.weight_rules if wr.indicator_id]
        if not rules:
            return None
        # ★같은 indicator_id 중복 rule → base_weight 합산 dedup. series_ids 중복은 corr_prior 인덱스
        # 충돌(idx dict 덮어쓰기)·derive_weights 공분산 특이를 부른다. 0.0 placeholder(peak_trap floor
        # 표식 등)는 합산해도 무영향이라 within-study 이중계상만 구조적으로 차단(L축 정합).
        agg: dict = {}
        order: list = []
        for wr in rules:
            if wr.indicator_id not in agg:
                agg[wr.indicator_id] = 0.0
                order.append(wr.indicator_id)
            agg[wr.indicator_id] += float(wr.base_weight)
        series = tuple(order)
        w = np.array([agg[i] for i in order], dtype=float)
        cap = DEFAULT_WEIGHT_CAP
        if apply_tilt:                                       # ★flag→동적 가중치 재적합(G4)
            w = self.flags.tilt_weights(w, list(series), cap=cap)
        scope = (s.asset_scope[0] if s.asset_scope else s.study_id) or s.study_id
        stmt = (s.lens.pricing_principle or f"{s.study_id} 지표 가중 카드").strip()[:200]
        return WeightAssumptionCard(
            id=f"weight.{s.study_id}.{regime_id or 'base'}",
            kind="parametric",
            scope=_scope_of(scope),
            domain=_domain_of(scope),
            statement=stmt,
            falsification_metric="OOS Rank-IC anytime-valid e-process",
            series_ids=series,
            w_global=tuple(float(x) for x in w),
            regime_id=regime_id,
            cap=cap,
            floor=DEFAULT_L1_FLOOR,
        )

    # --- production facade: judge() 인자 묶음 ---
    def prepare_judge_call(self, study_id: str, *, regime_id: Optional[str] = None,
                           refresh_tilt: bool = True) -> dict:
        """judge() 에 그대로 넘길 {weight_card, lens_prompt, regime_pi}.

        - weight_card: opt-in on 이면 flag tilt 재적용한 최신 카드, off 면 None(L1 단일 경로).
        - lens_prompt: lens_store(INV_STUDY_LENS 게이트) 렌더. off/없음 → None.
        둘 다 None 이면 judge 는 기존 동작(무회귀).
        """
        s = self.sessions.get(study_id)
        scope = (s.asset_scope[0] if (s and s.asset_scope) else study_id)
        card = None
        if s is not None and is_r15_enabled():
            card = self._build_card(s, regime_id=regime_id, apply_tilt=refresh_tilt)
        # ★U1 flag→lens: opt-in on 이면 라이브 누적 신뢰도를 lens 에 동적 주입(qwen 판단 보수화)
        note = self.flags.confidence_note() if is_r15_enabled() else None
        lens_prompt = self.lenses.render(str(scope), regime_id, confidence_note=note)
        return {"weight_card": card, "lens_prompt": lens_prompt, "regime_pi": None}

    # --- ★U3 flag→corr_prior facade: RegimeGlasso.fit(corr_prior=) 주입용 ---
    def prepare_corr_prior(self, study_id: str, base_corr_prior, series_ids,
                           *, conservative: bool = False):
        """flag 신뢰도로 약화된 corr_prior 를 반환(RegimeGlasso.fit(corr_prior=) prior 로 주입).

        study scope 로 level 을 결정해 corr_prior_shrink 호출 — 거시·채권 study(cross-sleeve driver)는
        level='macro' 라 belief 가 차단(no-op), 종목·상품 등은 level='micro' 라 within-sleeve 약화 허용.
        이 분리가 reflexive loop(종목 flag→macro Σ 되먹임)를 호출부에서 구조적으로 막는다(U3, 자문 3R).
        opt-in(INV_R15_WEIGHTS) off 면 base 그대로 반환(production 경로 미개통, 무회귀).
        """
        if not is_r15_enabled():
            return base_corr_prior
        s = self.sessions.get(study_id)
        scope = (s.asset_scope[0] if (s and s.asset_scope) else study_id)
        level = _corr_level_of(scope)
        return self.flags.corr_prior_shrink(
            base_corr_prior, series_ids, level=level, conservative=conservative)

    # --- 거래 outcome 라우팅(G4) ---
    def on_trade_outcome(self, hypothesis_id: str, signal: str, n: int = 1) -> None:
        self.flags.on_trade(hypothesis_id, signal, n)

    def emit_ic_outcome(self, hypothesis_id: str, scores, returns, **kw) -> str:
        return self.flags.emit_from_ic(hypothesis_id, scores, returns, **kw)

    # --- 진단 ---
    def status(self) -> dict:
        from core.study.indicator_ledger import build_indicator_ledger, ledger_summary
        return {
            "studies": sorted(self.sessions),
            "panels": self.panels.instances(),
            "lens_scopes": self.lenses.scopes(),
            "cards": sorted(self.cards),
            # P3 ledger: study_id → {adopted/candidate/rejected 카운트 + adopted_ids}.
            # 채택분 런타임 반영 대조 기준(yaml-runtime drift 감지). 산발 yaml 단일 집결 조회점.
            "ledger": {sid: ledger_summary(build_indicator_ledger(s))
                       for sid, s in self.sessions.items()},
            "r15_enabled": is_r15_enabled(),
            "lens_enabled": ls.is_enabled(),
        }


# ===========================================================================
# self-test (end-to-end production wiring 실동작)
# ===========================================================================

if __name__ == "__main__":
    from core.assume.registry import AssumptionRegistry

    # 부록 A(macro) 본떠 — weight_rules + confidence_hooks(affects_indicator 연결)
    macro = {
        "study_id": "macro", "asset_scope": ["macro"], "as_of": "2026-05-30",
        "lens": {"pricing_principle": "거시 자산가격 = 성장·인플레·유동성 조합",
                 "report_relations": ["HY OAS 확대→리스크오프"],
                 "regime_reading": "Reflation→주식우위", "estimation_note": "Recovery 초입"},
        "indicators": [
            {"id": "hy_oas", "family": "macro_driver", "is_core": True, "in_our_system": True,
             "source_or_collector": "fred[BAMLH0A0HYM2]"},
            {"id": "y10_2", "family": "macro_driver", "is_core": True, "in_our_system": True,
             "source_or_collector": "fred[T10Y2Y]"},
        ],
        "relationships": [{"node_a": "hy_oas", "node_b": "y10_2", "edge_type": "direct",
                           "conditioning_set": [], "theory_basis": "리스크오프 동반"}],
        "weight_rules": [
            {"indicator_id": "hy_oas", "base_weight": 0.5, "modulate_by": ["regime"],
             "direction": "리스크오프→↑", "granularity": "sleeve"},
            {"indicator_id": "y10_2", "base_weight": 0.5, "modulate_by": ["regime"],
             "direction": "역전→침체선행", "granularity": "sleeve"},
        ],
        "confidence_hooks": [
            {"hypothesis_id": "hy_risk", "confirm_signal": "IC양", "reject_signal": "붕괴",
             "affects_indicator": "hy_oas", "accumulate_in": "weight_falsification",
             "confidence_metric": "e-value", "store": "registry", "action_threshold": "retract",
             "feeds_weight": "derive_weights 재적합"},
        ],
        "collector_plan": [{"missing": "JGB", "source": "FRED", "interface": "VintageProvider"}],
        "code_change_plan": [{"stage": st} for st in ("learn", "card", "inject", "falsify")],
    }

    # 1) opt-in OFF → 검증만, production 미개통(무회귀)
    os.environ.pop(_ENV_R15, None)
    os.environ.pop("INV_STUDY_LENS", None)
    reg = AssumptionRegistry()
    sr = StudyRegister(assumption_registry=reg)
    rep = sr.register(macro)
    assert rep.ok, rep.errors
    assert sr.cards == {}, "opt-in off 인데 카드 등록됨(회귀)"
    jc_off = sr.prepare_judge_call("macro")
    assert jc_off["weight_card"] is None and jc_off["lens_prompt"] is None
    print(f"1) opt-in OFF: 검증 ok={rep.ok}, 카드 미등록, judge 인자 None (무회귀) OK")

    # 2) opt-in ON → 카드 등록 + judge 인자 채워짐 (production 개통)
    os.environ[_ENV_R15] = "1"
    os.environ["INV_STUDY_LENS"] = "1"
    reg2 = AssumptionRegistry()
    sr2 = StudyRegister(assumption_registry=reg2)
    rep2 = sr2.register(macro)
    assert "macro" in sr2.cards
    card = sr2.cards["macro"]
    assert card.series_ids == ("hy_oas", "y10_2") and card.kind == "parametric"
    assert reg2.get("weight.macro.base") is not None
    jc = sr2.prepare_judge_call("macro")
    assert jc["weight_card"] is not None
    assert jc["lens_prompt"] and "판단 렌즈" in jc["lens_prompt"]
    print(f"2) opt-in ON: 카드 등록(id={card.id}) + registry 조회 + judge 인자(card+lens) OK")

    # 3) ★flag→동적 가중치: hy_oas 확신 누적 → prepare_judge_call 카드 가중 변화
    base_w = np.array(sr2.prepare_judge_call("macro")["weight_card"].w_global)
    for _ in range(15):
        sr2.on_trade_outcome("hy_risk", "confirm")        # hy_oas 확신 누적
    tilt_w = np.array(sr2.prepare_judge_call("macro")["weight_card"].w_global)
    i_hy = card.series_ids.index("hy_oas")
    assert tilt_w[i_hy] > base_w[i_hy], f"확신 누적했는데 가중 안 변함: {tilt_w} vs {base_w}"
    print(f"3) ★flag→동적 가중치 production OK: hy_oas {base_w[i_hy]:.3f}→{tilt_w[i_hy]:.3f} "
          f"(거래 outcome 이 실제 카드 가중 변경)")

    # 4) 검증 실패 yaml → register 가 주입 거부
    bad = {"study_id": "bad_eq", "asset_scope": ["equity.us"], "as_of": "t",
           "indicators": [{"id": "pe", "family": "valuation", "is_core": True, "in_our_system": True}],
           "code_change_plan": [{"stage": "learn"}]}
    rep_bad = sr2.register(bad)
    assert not rep_bad.ok and "bad_eq" not in sr2.sessions
    print(f"4) 검증 실패(equity 코어셋 누락) → 주입 거부 OK: {len(rep_bad.errors)} errors")

    # 5) status 진단
    st = sr2.status()
    assert st["r15_enabled"] and st["lens_enabled"] and "macro" in st["cards"]
    print(f"5) status OK: {st}")

    # 6) ★U3 flag→corr_prior facade: study scope 로 level 분리(reflexive loop 가드)
    base_cp = np.array([[1.0, 0.5], [0.5, 1.0]])
    # (case 3 에서 hy_risk confirm 15 누적 = confidence>0.5). macro study = level 'macro' → belief 차단(no-op)
    cp_macro = sr2.prepare_corr_prior("macro", base_cp, ["hy_oas", "y10_2"])
    assert np.allclose(cp_macro, base_cp), f"macro level belief 차단 실패(reflexive loop 위험): {cp_macro}"
    # 대비군: 같은 flag 라도 level='micro' 직접 호출은 corr 반영(가드가 facade 의 macro 선택으로 막은 것)
    cp_micro_direct = sr2.flags.corr_prior_shrink(base_cp, ["hy_oas", "y10_2"], level="micro")
    assert not np.allclose(cp_micro_direct, base_cp), "micro 직접호출은 flag 반영돼야(대비군)"
    # scope→level 매핑
    assert _corr_level_of("macro") == "macro" and _corr_level_of("bond_cash") == "macro"
    assert _corr_level_of("equity.us") == "micro" and _corr_level_of("commodity") == "micro"
    assert _corr_level_of("gold") == "micro"
    # opt-in off → base 그대로(무회귀)
    os.environ.pop(_ENV_R15, None)
    assert sr2.prepare_corr_prior("macro", base_cp, ["hy_oas", "y10_2"]) is base_cp
    os.environ[_ENV_R15] = "1"
    print("6) ★U3 corr_prior facade OK: macro=belief차단 no-op / micro직접=flag반영(대비) / 매핑 / opt-in off 무회귀")

    os.environ.pop(_ENV_R15, None)
    os.environ.pop("INV_STUDY_LENS", None)
    print("\nstudy_register self-test PASS "
          "(opt-in OFF 무회귀 + ON 카드/registry/judge wiring + ★flag→동적가중치 production + 검증거부)")
