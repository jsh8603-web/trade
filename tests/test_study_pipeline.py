"""tests/test_study_pipeline.py — 종목 스터디 시스템 통합 골격(G1~G6) pytest 가드.

각 모듈의 __main__ self-test 와 별개로, CI 회귀 가드를 제공한다. 핵심:
- opt-in OFF(기본) = production 경로 미개통 = 무회귀(byte-identical) 보장.
- opt-in ON = yaml → 카드/렌즈/flag → 동적 가중치 production wiring 동작.
- 방 산출(study_session.yaml)이 도착하면 study_register.register(path) 로 통합되는 계약.

opt-in 환경변수는 테스트 내에서만 set/restore(전역 오염 방지).
"""

import os

import numpy as np
import pytest

from core.study.study_loader import load_study_session, validate_study_session
from core.study import panel_manifest as pm
from core.study import lens_store as ls
from core.study.flag_router import FlagRouter, FlagAccumulator
from core.study import system_priors as sp
from core.study.study_register import StudyRegister, is_r15_enabled


# 부록 A(macro) 본떠 — 7블록 완비 표준 산출
MACRO_YAML = {
    "study_id": "macro", "asset_scope": ["macro"], "as_of": "2026-05-30",
    "lens": {"pricing_principle": "거시 자산가격 = 성장·인플레·유동성 조합",
             "report_relations": ["HY OAS 확대→리스크오프"],
             "regime_reading": "Reflation→주식우위", "estimation_note": "Recovery 초입"},
    "indicators": [
        {"id": "hy_oas", "family": "macro_driver", "is_core": True, "in_our_system": True,
         "source_or_collector": "fred[BAMLH0A0HYM2]", "vintage_policy": "point_in_time"},
        {"id": "y10_2", "family": "macro_driver", "is_core": True, "in_our_system": True,
         "source_or_collector": "fred[T10Y2Y]", "vintage_policy": "point_in_time"},
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
        {"hypothesis_id": "hy_risk", "affects_indicator": "hy_oas",
         "confirm_signal": "IC양", "reject_signal": "붕괴",
         "accumulate_in": "weight_falsification", "confidence_metric": "e-value",
         "store": "registry", "action_threshold": "retract", "feeds_weight": "derive_weights 재적합"},
    ],
    "collector_plan": [{"missing": "JGB", "source": "FRED", "interface": "VintageProvider"}],
    "code_change_plan": [{"stage": st} for st in ("learn", "card", "inject", "falsify")],
}


@pytest.fixture
def optin_off():
    """opt-in 환경변수 제거 + 종료 후 복원."""
    saved = {k: os.environ.get(k) for k in ("INV_R15_WEIGHTS", "INV_STUDY_LENS")}
    for k in saved:
        os.environ.pop(k, None)
    yield
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


@pytest.fixture
def optin_on(optin_off):
    os.environ["INV_R15_WEIGHTS"] = "1"
    os.environ["INV_STUDY_LENS"] = "1"
    yield


# --- G1 loader/validator ---
def test_g1_load_validate_macro():
    s = load_study_session(MACRO_YAML)
    rep = validate_study_session(s)
    assert rep.ok, rep.errors
    assert s.study_id == "macro" and len(s.indicators) == 2


def test_g1_equity_core_hardrule_enforced():
    bad = {"study_id": "eq", "asset_scope": ["equity.us"], "as_of": "2026-05-30",
           "indicators": [{"id": "pe", "family": "valuation", "is_core": True,
                           "in_our_system": True}],
           "code_change_plan": [{"stage": "learn"}]}
    rep = validate_study_session(load_study_session(bad))
    assert not rep.ok and any("하드룰" in e for e in rep.errors)


# --- G2 panel_manifest (본체 build_indicator_matrix wrap) ---
def test_g2_panel_build_wraps_core():
    class FakeProvider:
        def realtime(self, sid, period, as_of):
            return float(sum(ord(c) for c in sid) % 5 + 1)
    s = load_study_session(MACRO_YAML)
    m = pm.from_study_session(s)
    assert m.series_ids == ["hy_oas", "y10_2"]
    panel = pm.build_panel(m, FakeProvider(), ["2026-01", "2026-02", "2026-03"])
    assert panel.shape == (3, 2) and not np.isnan(panel.matrix).any()


def test_g2_reflexive_series_rejected_by_core():
    bad = {"study_id": "b", "asset_scope": ["macro"], "as_of": "2026-05-30",
           "indicators": [{"id": "my_position_pnl", "family": "risk", "in_our_system": True}]}
    m = pm.from_study_session(load_study_session(bad))
    with pytest.raises(ValueError, match="반사성"):
        pm.build_panel(m, None, ["2026-01"])


# --- G3 lens_store (opt-in 게이트) ---
def test_g3_lens_optin_gate(optin_off):
    store = ls.from_study_session(load_study_session(MACRO_YAML))
    assert store.render("macro") is None          # off → 무회귀
    os.environ["INV_STUDY_LENS"] = "1"
    r = store.render("macro")
    assert r and "판단 렌즈" in r                   # on → 주입


# --- G4 flag_router (동적 가중치 재적합 신규 코드) ---
def test_g4_flag_tilts_weights():
    fr = FlagRouter()
    from core.study.study_loader import ConfidenceHook
    fr.register(ConfidenceHook(hypothesis_id="h"), indicator_id="a")
    for _ in range(12):
        fr.on_trade("h", "confirm")
    base = np.array([0.5, 0.5])
    tilted = fr.tilt_weights(base, ["a", "b"], cap=0.9)
    assert tilted[0] > base[0]                      # 확신 누적 → 가중 ↑
    assert abs(np.sum(np.abs(tilted)) - 1.0) < 1e-6  # L1 보존


def test_g4_beta_posterior_direction():
    acc = FlagAccumulator()
    assert abs(acc.confidence() - 0.5) < 1e-9
    for _ in range(10):
        acc.reject()
    assert acc.confidence() < 0.5


# --- G5 system_priors ---
def test_g5_factor_implied_cross_cov_pd():
    betas = {"a": [1.0, 0.2], "b": [0.5, -0.3]}
    res = sp.factor_implied_cross_cov(betas, np.diag([0.04, 0.03]), idio_var={"a": 0.02, "b": 0.03})
    assert np.all(np.linalg.eigvalsh(res.cov) > 0)   # PD


def test_g5_regime_obs_floor_modes():
    rng = np.random.default_rng(0)
    def _pd():
        A = rng.normal(size=(2, 2)); return A @ A.T + np.eye(2)
    sr = sp.regime_obs_floor_shrink({0: _pd(), 1: _pd(), 2: _pd()},
                                    {0: 50, 1: 20, 2: 5}, _pd(), floor=30, hard_min=10)
    assert sr.mode == {0: "keep", 1: "shrink", 2: "fallback"}


# --- G6 study_register (production wiring end-to-end) ---
def test_g6_optin_off_no_production(optin_off):
    sr = StudyRegister()
    rep = sr.register(MACRO_YAML)
    assert rep.ok and sr.cards == {}                # off → 카드 미등록(무회귀)
    jc = sr.prepare_judge_call("macro")
    assert jc["weight_card"] is None and jc["lens_prompt"] is None


def test_g6_optin_on_production_wiring(optin_on):
    from core.assume.registry import AssumptionRegistry
    reg = AssumptionRegistry()
    sr = StudyRegister(assumption_registry=reg)
    sr.register(MACRO_YAML)
    assert "macro" in sr.cards
    assert reg.get("weight.macro.base") is not None
    jc = sr.prepare_judge_call("macro")
    assert jc["weight_card"] is not None and jc["lens_prompt"]


def test_g6_outcome_changes_card_weight(optin_on):
    """★flag→동적 가중치: 거래 outcome 이 실제 카드 가중을 바꾼다(사용자 핵심 요구)."""
    sr = StudyRegister()
    sr.register(MACRO_YAML)
    base = np.array(sr.prepare_judge_call("macro")["weight_card"].w_global)
    for _ in range(15):
        sr.on_trade_outcome("hy_risk", "confirm")
    after = np.array(sr.prepare_judge_call("macro")["weight_card"].w_global)
    i = sr.cards["macro"].series_ids.index("hy_oas")
    assert after[i] > base[i]


def test_g6_register_rejects_invalid(optin_on):
    sr = StudyRegister()
    bad = {"study_id": "bad_eq", "asset_scope": ["equity.us"], "as_of": "2026-05-30",
           "indicators": [{"id": "pe", "family": "valuation", "is_core": True, "in_our_system": True}],
           "code_change_plan": [{"stage": "learn"}]}
    rep = sr.register(bad)
    assert not rep.ok and "bad_eq" not in sr.sessions
