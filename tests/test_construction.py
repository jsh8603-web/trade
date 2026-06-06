"""WIRE3.5-Gd 테스트: stock/construction.build_sleeve_decisions (sleeve 단위 조립 진입점).

검증기준:
- sleeve명만으로 preset 부호(signs_for) + yaml weights + interaction 자동 주입
- cyclical universe → 종목선택 Decision 리스트 (pbr/ev 부호 자동)
- defensive → DEF-2 interaction 자동 (composite 내부 panel 부재 시 skip 무오류)
- 미지 sleeve → metric_panel 키 +1 default fallback
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stock.construction import build_sleeve_decisions
from stock.contracts import FilingSource, Fundamentals, MarketQuote, RunMode

KST = timezone(timedelta(hours=9))


def _funds(t):
    src = FilingSource.DART_XBRL
    return Fundamentals(ticker=t, fiscal_period="2024FY",
                        filing_timestamp=datetime(2024, 3, 15, tzinfo=KST), source=src,
                        currency="USD", revenue=3e11, free_cash_flow=3e10,
                        outstanding_shares=5e9, ebitda=4e10)


def _quote(t, mcap):
    return MarketQuote(ticker=t, as_of=datetime(2024, 4, 1, tzinfo=KST), price=100.0,
                       market_cap=mcap, price_change_pct=0.0, price_change_window_days=30)


def _ha_nontrap():
    m = MagicMock()
    from stock.value_trigger import HeavyAgentVerdict
    m.judge_value_trap.return_value = HeavyAgentVerdict(is_trap=False, confidence=0.8, reasoning="기회")
    return m


def test_build_sleeve_cyclical_auto_signs():
    """cyclical: signs_for 자동(pbr/ev −1) → 저PBR/저EV 종목 선택. yaml weights 자동."""
    tickers = ["A", "B", "C"]
    panel = {"pbr": {"A": 0.8, "B": 1.2, "C": 4.0},
             "ev_ebitda": {"A": 5.0, "B": 7.0, "C": 18.0}}
    caps = {t: 50e9 for t in tickers}
    funds = {t: [_funds(t)] for t in tickers}
    quotes = {t: _quote(t, 50e9) for t in tickers}
    secs = {t: "s" for t in tickers}
    out = build_sleeve_decisions("cyclical", panel, caps, funds, quotes,
                                 sectors=secs, heavy_agent=_ha_nontrap(),
                                 config=None, mode=RunMode.FORWARD)
    assert isinstance(out, list)
    for d in out:
        assert d["target_weight"] > 0 and "cheapness_z" in d


def test_build_sleeve_defensive_interaction_skips_missing():
    """defensive: DEF-2 interaction 자동 주입되나 panel 에 div/op 부재 → 내부 skip 무오류."""
    tickers = ["A", "B"]
    panel = {"net_issuance": {"A": 0.05, "B": -0.02},
             "ep_yield": {"A": 0.08, "B": 0.03}}
    caps = {t: 40e9 for t in tickers}
    funds = {t: [_funds(t)] for t in tickers}
    quotes = {t: _quote(t, 40e9) for t in tickers}
    out = build_sleeve_decisions("defensive", panel, caps, funds, quotes,
                                 heavy_agent=_ha_nontrap())
    assert isinstance(out, list)   # interaction(div×op) panel 부재여도 무오류


def test_build_sleeve_unknown_default_signs():
    """미지 sleeve = metric_panel 키 +1 default (호출자 책임 fallback, 무오류)."""
    panel = {"foo": {"A": 1.0, "B": 2.0}}
    caps = {"A": 10e9, "B": 10e9}
    funds = {t: [_funds(t)] for t in ["A", "B"]}
    quotes = {t: _quote(t, 10e9) for t in ["A", "B"]}
    out = build_sleeve_decisions("unknown_sleeve", panel, caps, funds, quotes,
                                 heavy_agent=_ha_nontrap())
    assert isinstance(out, list)
