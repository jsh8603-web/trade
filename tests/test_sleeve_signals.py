"""WIRE3.5-Ga 테스트: stock/sleeve_signals.py sleeve별 cheapness 부호 preset.

검증기준:
- SLEEVE_SIGNS 부호가 연구 verdict + WIRE3 sim 하드코딩과 1:1 일치
- signs_for() helper 동작 (복사본 반환, 미지 sleeve = {})
- skip 사유 박제 존재
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stock.sleeve_signals import (
    SLEEVE_SIGNS,
    SLEEVE_SIGNS_SKIPPED,
    interaction_weights_for,
    interactions_for,
    load_sleeve_weights,
    signs_for,
)


def test_cyclical_signs_match_sim():
    """cyclical pbr/ev_ebitda = −1 (저평가=쌈). _wire3_selection_sim.py:144 와 1:1."""
    assert signs_for("cyclical") == {"pbr": -1, "ev_ebitda": -1}


def test_defensive_signs_match_sim():
    """defensive net_issuance +1 (buyback-aversion) / ep_yield −1 (anti-value). sim:112 와 1:1."""
    assert signs_for("defensive") == {"net_issuance": +1, "ep_yield": -1}


def test_mega_tech_empty():
    """mega_tech = basket 통째 보유, cross-sectional selection 대상 아님 → 빈 preset."""
    assert signs_for("mega_tech") == {}


def test_unknown_sleeve_empty():
    """미지 sleeve = {} (호출자 직접 주입 fallback, byte-identical)."""
    assert signs_for("nonexistent") == {}


def test_signs_for_returns_copy():
    """signs_for 는 복사본 반환 — 호출자 mutation 이 preset 오염 안 함."""
    s = signs_for("cyclical")
    s["pbr"] = 99
    assert SLEEVE_SIGNS["cyclical"]["pbr"] == -1


def test_skip_reasons_documented():
    """preset 제외 지표 = skip 사유 박제 (sales_yield, residual_mom)."""
    assert "cyclical.sales_yield" in SLEEVE_SIGNS_SKIPPED
    assert "defensive.residual_mom" in SLEEVE_SIGNS_SKIPPED
    assert all(len(v) > 5 for v in SLEEVE_SIGNS_SKIPPED.values())


# ── Gc: yaml base_weight → selection weights ────────────────────────

def test_load_weights_cyclical():
    """cyclical summary.yaml base_weight_range mid → {pbr, ev_ebitda} (cs_pbr_z [0.08,0.15]→0.115)."""
    w = load_sleeve_weights("cyclical")
    assert "pbr" in w and abs(w["pbr"] - 0.115) < 1e-6
    assert "ev_ebitda" in w and abs(w["ev_ebitda"] - 0.075) < 1e-6


def test_load_weights_unknown_empty():
    """미지 sleeve = 빈 dict (selection 등가중 fallback)."""
    assert load_sleeve_weights("nonexistent") == {}


# ── Gb/Gd: interaction preset ────────────────────────────────────────

def test_interactions_defensive():
    """defensive = DEF-2 (dividend_yield×op_profitability, sign +1)."""
    assert interactions_for("defensive") == [("dividend_yield", "op_profitability", 1)]


def test_interactions_unknown_empty():
    """미지/cyclical sleeve = interaction 없음."""
    assert interactions_for("nonexistent") == []
    assert interactions_for("cyclical") == []


# ── Gj: interaction weight discount (marginal hedge) ────────────────

def test_interaction_weight_discount():
    """interaction weight = main 평균 × 0.5 (DEF-2 marginal hedge). mean(0.10,0.06)=0.08 → 0.04."""
    iw = interaction_weights_for("defensive", {"net_issuance": 0.10, "ep_yield": 0.06})
    assert "dividend_yield*op_profitability" in iw
    assert abs(iw["dividend_yield*op_profitability"] - 0.04) < 1e-9


def test_interaction_weight_empty_main_fallback():
    """main weight 부재(yaml 미존재) = 빈 dict → 등가중 fallback(byte-identical)."""
    assert interaction_weights_for("defensive", {}) == {}


def test_interaction_weight_no_interaction_sleeve():
    """interaction 없는 sleeve(cyclical) = 빈 dict."""
    assert interaction_weights_for("cyclical", {"pbr": 0.1, "ev_ebitda": 0.07}) == {}
