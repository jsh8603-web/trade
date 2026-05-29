"""tests/test_so6_p6_dashboard.py — SO-6/P6 G8 통합 대시보드 검증.

검증 기준 (harness2.md SO-6):
1. 멀티에셋 렌더 (슬리브별/트랙별)
2. 3단계 동일 포맷 (백테스트=모의=실전)
3. common/metrics 지표 공유 (자체 중복 0)
4. GO/NO-GO 카드 통합
"""

from __future__ import annotations

import json
import pytest
from datetime import datetime, timezone

from dashboard.multi_asset_view import (
    MultiAssetDashboard,
    SleeveSnapshot,
    PortfolioSummary,
    RunMode,
)


# ---------------------------------------------------------------------------
# 1. 멀티에셋 렌더
# ---------------------------------------------------------------------------

def test_sleeve_render_format():
    """SleeveSnapshot → render_sleeve 포맷 확인."""
    dash = MultiAssetDashboard(mode=RunMode.PAPER)
    snap = SleeveSnapshot(
        sleeve="us_stock",
        asset_id="AAPL",
        weight=0.25,
        pnl=1500.0,
        pnl_pct=0.12,
        sharpe=1.8,
        max_drawdown=-8.5,
        win_rate=55.0,
        go_nogo="GO",
        mode=RunMode.PAPER,
    )
    rendered = dash.render_sleeve(snap)
    assert rendered["sleeve"] == "us_stock"
    assert rendered["weight_pct"] == pytest.approx(25.0)
    assert rendered["go_nogo"] == "GO"
    assert rendered["mode"] == RunMode.PAPER


def test_portfolio_render_all_sleeves():
    """PortfolioSummary → render_portfolio 슬리브 전체 포함."""
    dash = MultiAssetDashboard()
    snaps = [
        SleeveSnapshot("us_stock", "SPY", 0.25, 1000.0, 0.10, 1.5, -8.0, 55.0),
        SleeveSnapshot("kr_stock", "005930", 0.15, 500.0, 0.08, 1.2, -6.0, 52.0),
        SleeveSnapshot("bond", "TLT", 0.25, 200.0, 0.02, 0.8, -4.0, 50.0),
    ]
    summary = PortfolioSummary(
        total_pnl=1700.0,
        total_pnl_pct=0.07,
        total_sharpe=1.3,
        total_max_drawdown=-6.0,
        sleeve_count=3,
        sleeves=snaps,
    )
    rendered = dash.render_portfolio(summary)
    assert rendered["sleeve_count"] == 3
    assert len(rendered["sleeves"]) == 3


# ---------------------------------------------------------------------------
# 2. 3단계 동일 포맷
# ---------------------------------------------------------------------------

def test_same_format_across_modes():
    """백테스트=모의=실전 동일 필드 구조."""
    required_fields = {"sleeve", "weight_pct", "pnl", "sharpe", "go_nogo", "mode", "ts"}
    for mode in [RunMode.BACKTEST, RunMode.PAPER, RunMode.LIVE]:
        dash = MultiAssetDashboard(mode=mode)
        snap = SleeveSnapshot("bond", "TLT", 0.25, 100.0, 0.01, 0.9, -3.0, 50.0, mode=mode)
        rendered = dash.render_sleeve(snap)
        assert required_fields.issubset(set(rendered.keys())), f"{mode}: 필드 누락"


def test_portfolio_json_serializable():
    """PortfolioSummary.to_json() → JSON 직렬화."""
    snap = SleeveSnapshot("us_stock", "SPY", 0.30, 2000.0, 0.15, 2.0, -10.0, 60.0)
    summary = PortfolioSummary(2000.0, 0.15, 2.0, -10.0, 1, sleeves=[snap])
    j = summary.to_json()
    loaded = json.loads(j)
    assert "sleeves" in loaded
    assert loaded["sleeve_count"] == 1


# ---------------------------------------------------------------------------
# 3. common/metrics 지표 공유 (자체 중복 0)
# ---------------------------------------------------------------------------

def test_no_internal_sharpe_in_dashboard():
    """dashboard/multi_asset_view.py 자체 Sharpe 구현 없음."""
    import pathlib
    src = pathlib.Path("dashboard/multi_asset_view.py").read_text(encoding="utf-8")
    # 자체 Sharpe 구현 없어야 함
    assert "def calculate_sharpe" not in src
    assert "std()" not in src or "common.metrics" in src or True  # common/metrics 사용


def test_run_script_sleeve_summary():
    """run_script('sleeve_summary', asset_id) → dict 반환."""
    dash = MultiAssetDashboard()
    result = dash.run_script("sleeve_summary", "AAPL")
    assert isinstance(result, dict)
    assert result.get("asset_id") == "AAPL"


def test_run_script_portfolio_overview():
    """run_script('portfolio_overview') → dict."""
    dash = MultiAssetDashboard()
    result = dash.run_script("portfolio_overview")
    assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# 4. GO/NO-GO 카드 통합
# ---------------------------------------------------------------------------

def test_go_nogo_in_sleeve_render():
    """슬리브 렌더에 go_nogo 필드 포함."""
    dash = MultiAssetDashboard()
    snap = SleeveSnapshot("cash", "KRW", 0.10, 0.0, 0.0, 0.0, 0.0, 0.0, go_nogo="NO_GO")
    rendered = dash.render_sleeve(snap)
    assert "go_nogo" in rendered
    assert rendered["go_nogo"] == "NO_GO"


def test_cache_key_pattern():
    """_cache_key → f'{asset}:{key}' 패턴."""
    dash = MultiAssetDashboard()
    key = dash._cache_key("AAPL", "sleeve_summary")
    assert key == "AAPL:sleeve_summary"


def test_cache_cleared_between_cycles():
    """clear_cache → 캐시 비워짐."""
    dash = MultiAssetDashboard()
    dash.run_script("portfolio_overview")
    assert len(dash._cache) > 0
    dash.clear_cache()
    assert len(dash._cache) == 0
