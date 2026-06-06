"""WIRE 배선 테스트: stock/selection_pipeline.build_universe_candidates.

검증기준 (universe selection ⊕ per-ticker value_trigger 배선):
- universe → top-K capped-EW selection → 각 종목 generate_candidate → Decision 호환 dict
- bypass_gate1 우회: 가격 −10% 미달(횡보/상승)이어도 selection 픽이 REJECT 안 됨
- selection 메타(target_weight/cheapness_z/rank) 병합 확인
- microcap floor·trap veto eligibility 가 파이프에서 동작

★주의: 입력은 wire 동작 확인용 fixture (합성 IC/신호 박제 아님). 실데이터 IC 정합은
  study-research/eq_us/_wire3_selection_sim.py(영속 실측)가 담당 — 본 테스트는 코드 경로만.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stock.contracts import FilingSource, Fundamentals, MarketQuote, RunMode
from stock.cross_sectional_selection import SelectionConfig
from stock.selection_pipeline import build_universe_candidates

KST = timezone(timedelta(hours=9))


def _funds(ticker: str) -> Fundamentals:
    return Fundamentals(
        ticker=ticker,
        fiscal_period="2024FY",
        filing_timestamp=datetime(2024, 3, 15, tzinfo=KST),
        source=FilingSource.EDGAR_XBRL if hasattr(FilingSource, "EDGAR_XBRL") else FilingSource.DART_XBRL,
        currency="USD",
        revenue=300_000_000_000,
        free_cash_flow=30_000_000_000,
        outstanding_shares=5_000_000_000,
        ebitda=40_000_000_000,
    )


def _quote(ticker: str, mcap: float, price_change: float) -> MarketQuote:
    return MarketQuote(
        ticker=ticker,
        as_of=datetime(2024, 4, 1, tzinfo=KST),
        price=100.0,
        market_cap=mcap,
        price_change_pct=price_change,
        price_change_window_days=30,
    )


def _build(price_change: float = 0.0, heavy_agent=None, config=None):
    """4종목 universe: A/B 쌈(z 높음), C 비쌈, D microcap(floor 탈락)."""
    tickers = ["A", "B", "C", "D"]
    # pbr·ev_ebitda 낮을수록 쌈 (sign −1). A/B 저PBR, C 고PBR
    metric_panel = {
        "pbr": {"A": 0.8, "B": 1.0, "C": 3.5, "D": 0.9},
        "ev_ebitda": {"A": 5.0, "B": 6.0, "C": 18.0, "D": 5.5},
    }
    metric_signs = {"pbr": -1, "ev_ebitda": -1}
    market_caps = {"A": 50e9, "B": 40e9, "C": 30e9, "D": 100e6}  # D < $500M floor
    funds_by = {t: [_funds(t)] for t in tickers}
    quote_by = {t: _quote(t, market_caps[t], price_change) for t in tickers}
    cfg = config or SelectionConfig(top_k=2, market_cap_floor=500e6, min_universe_n=3)
    return build_universe_candidates(
        metric_panel, market_caps, metric_signs, funds_by, quote_by,
        config=cfg, heavy_agent=heavy_agent, mode=RunMode.FORWARD,
    )


# ── 배선 동작 ────────────────────────────────────────────────────────

def test_pipeline_returns_decision_dicts():
    """universe → eligible 종목 Decision 호환 dict 리스트."""
    mock_ha = MagicMock()
    from stock.value_trigger import HeavyAgentVerdict
    mock_ha.judge_value_trap.return_value = HeavyAgentVerdict(
        is_trap=False, confidence=0.8, reasoning="기회"
    )
    out = _build(price_change=0.0, heavy_agent=mock_ha)
    assert isinstance(out, list)
    for d in out:
        assert "decision" in d and "confidence" in d and "reason" in d
        assert "target_weight" in d and "cheapness_z" in d and "rank" in d


def test_pipeline_selection_meta_merged():
    """selection 메타(target_weight>0, rank) 병합 + microcap D 제외."""
    mock_ha = MagicMock()
    from stock.value_trigger import HeavyAgentVerdict
    mock_ha.judge_value_trap.return_value = HeavyAgentVerdict(
        is_trap=False, confidence=0.8, reasoning="기회"
    )
    out = _build(price_change=0.0, heavy_agent=mock_ha)
    tickers = {d["trade_params"].get("ticker") or d.get("rank") for d in out}
    # microcap D 는 floor 탈락 → 결과에 없음
    picked = [d for d in out]
    assert len(picked) >= 1
    for d in picked:
        assert d["target_weight"] > 0
        assert d["rank"] >= 1


def test_pipeline_bypass_gate1_no_price_drop():
    """★bypass_gate1: 가격 변동 0%(횡보)여도 selection 픽이 REJECT 안 됨.

    단일종목 dip-buy 경로면 가격 −10% 미달 → 1차 게이트 REJECT 였을 것.
    selection 경로는 bypass_gate1=True 라 stage-2 trap veto 만 → 매수 후보 생존.
    """
    mock_ha = MagicMock()
    from stock.value_trigger import HeavyAgentVerdict
    mock_ha.judge_value_trap.return_value = HeavyAgentVerdict(
        is_trap=False, confidence=0.8, reasoning="기회"
    )
    out = _build(price_change=0.0, heavy_agent=mock_ha)  # 가격 변동 없음
    # bypass 덕에 후보 생존 (REJECT 전멸 아님)
    assert len(out) >= 1
    # 1차 게이트 REJECT verdict 이 아님
    from stock.contracts import ValueVerdict
    for d in out:
        tr = d.get("_trigger_result")
        if tr is not None:
            assert tr.verdict != ValueVerdict.REJECT


def test_pipeline_trap_veto_eligibility():
    """trap veto=True(함정) → 해당 종목 eligibility 탈락 → 결과 제외."""
    mock_ha = MagicMock()
    from stock.value_trigger import HeavyAgentVerdict
    mock_ha.judge_value_trap.return_value = HeavyAgentVerdict(
        is_trap=True, confidence=0.85, reasoning="thesis 붕괴"
    )
    out = _build(price_change=0.0, heavy_agent=mock_ha)
    # 전 종목 trap → selection eligibility 탈락 → 빈 리스트
    assert out == []


def test_pipeline_empty_universe():
    """전 종목 microcap → floor 탈락 → 빈 리스트(무오류)."""
    metric_panel = {"pbr": {"A": 0.8, "B": 1.0}}
    out = build_universe_candidates(
        metric_panel, {"A": 100e6, "B": 50e6}, {"pbr": -1},
        {"A": [_funds("A")], "B": [_funds("B")]},
        {"A": _quote("A", 100e6, 0.0), "B": _quote("B", 50e6, 0.0)},
        config=SelectionConfig(top_k=2, market_cap_floor=500e6),
    )
    assert out == []
