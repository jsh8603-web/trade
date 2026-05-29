"""dashboard/multi_asset_view.py — G8 통합 대시보드 멀티에셋 뷰 (SO-6/P6).

WHY: coin dashboard.py 는 BTC 단일 SACRED(미변경). 멀티에셋 슬리브 뷰는 신규 모듈로 분리.
     백테스트=모의=실전 3단계 동일 포맷. common/metrics SSOT 지표 공유.

reuse: yakub268 dashboard/app.py + routes/v5.py 레이아웃 참조.
      run_script(name, asset_id) 패턴 어댑트.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

logger = logging.getLogger("dashboard.multi_asset_view")

# ---------------------------------------------------------------------------
# 3단계 모드 — 백테스트/모의/실전 동일 포맷 (G8)
# ---------------------------------------------------------------------------

class RunMode:
    BACKTEST = "backtest"
    PAPER = "paper"
    LIVE = "live"


# ---------------------------------------------------------------------------
# 슬리브 P&L 레코드
# ---------------------------------------------------------------------------

@dataclass
class SleeveSnapshot:
    """슬리브별 P&L + 지표 스냅샷. 3단계 동일 포맷."""
    sleeve: str
    asset_id: str
    weight: float
    pnl: float
    pnl_pct: float
    sharpe: float
    max_drawdown: float
    win_rate: float
    mode: str = RunMode.PAPER
    go_nogo: str = "MARGINAL"   # GO/MARGINAL/NO_GO
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        d = asdict(self)
        d["ts"] = self.ts.isoformat()
        return d


@dataclass
class PortfolioSummary:
    """전체 포트폴리오 요약. G8 대시보드 렌더용."""
    total_pnl: float
    total_pnl_pct: float
    total_sharpe: float
    total_max_drawdown: float
    sleeve_count: int
    mode: str = RunMode.PAPER
    sleeves: List[SleeveSnapshot] = field(default_factory=list)
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_json(self) -> str:
        d = asdict(self)
        d["ts"] = self.ts.isoformat()
        for s in d.get("sleeves", []):
            if "ts" in s and hasattr(s["ts"], "isoformat"):
                s["ts"] = s["ts"].isoformat()
        return json.dumps(d, ensure_ascii=False, indent=2, default=str)


# ---------------------------------------------------------------------------
# MultiAssetDashboard — G8 통합 렌더
# ---------------------------------------------------------------------------

class MultiAssetDashboard:
    """G8 통합 대시보드 — 멀티에셋 슬리브/트랙별 렌더.

    SACRED: coin dashboard.py 미변경. 이 모듈=신규 뷰.
    common/metrics SSOT 지표 공유 (자체 중복 0).
    """

    def __init__(self, mode: str = RunMode.PAPER):
        self._mode = mode
        self._cache: Dict[str, Any] = {}  # f"{asset}:{key}" 캐시 패턴

    def _cache_key(self, asset: str, key: str) -> str:
        """yakub268 app.py _CACHE 패턴: f"{asset}:{key}"."""
        return f"{asset}:{key}"

    def run_script(self, name: str, asset_id: str = "") -> dict:
        """yakub268 run_script(name, asset_id) 패턴 어댑트.

        name: "sleeve_summary" | "portfolio_overview" | "go_nogo_card"
        asset_id: 슬리브 ID (빈 문자열=전체)
        """
        cache_key = self._cache_key(asset_id or "all", name)
        if cache_key in self._cache:
            return self._cache[cache_key]

        if name == "sleeve_summary":
            result = self._render_sleeve_summary(asset_id)
        elif name == "portfolio_overview":
            result = self._render_portfolio_overview()
        elif name == "go_nogo_card":
            result = self._render_go_nogo_card(asset_id)
        else:
            logger.warning("알 수 없는 스크립트: %s", name)
            result = {"error": f"unknown script: {name}"}

        self._cache[cache_key] = result
        return result

    def render_sleeve(self, snapshot: SleeveSnapshot) -> dict:
        """단일 슬리브 렌더 — 3단계 동일 포맷."""
        from common.metrics import calculate_sharpe_ratio, calculate_max_drawdown
        return {
            "sleeve": snapshot.sleeve,
            "asset_id": snapshot.asset_id,
            "weight_pct": round(snapshot.weight * 100, 2),
            "pnl": round(snapshot.pnl, 2),
            "pnl_pct": round(snapshot.pnl_pct * 100, 2),
            "sharpe": round(snapshot.sharpe, 4),
            "max_drawdown_pct": round(snapshot.max_drawdown, 2),
            "win_rate_pct": round(snapshot.win_rate, 2),
            "go_nogo": snapshot.go_nogo,
            "mode": snapshot.mode,
            "ts": snapshot.ts.isoformat(),
        }

    def render_portfolio(self, summary: PortfolioSummary) -> dict:
        """포트폴리오 전체 렌더 — 3단계 동일 포맷."""
        return {
            "total_pnl": round(summary.total_pnl, 2),
            "total_pnl_pct": round(summary.total_pnl_pct * 100, 2),
            "total_sharpe": round(summary.total_sharpe, 4),
            "total_max_drawdown_pct": round(summary.total_max_drawdown, 2),
            "sleeve_count": summary.sleeve_count,
            "mode": summary.mode,
            "sleeves": [self.render_sleeve(s) for s in summary.sleeves],
            "ts": summary.ts.isoformat(),
        }

    def _render_sleeve_summary(self, asset_id: str) -> dict:
        return {"script": "sleeve_summary", "asset_id": asset_id, "mode": self._mode}

    def _render_portfolio_overview(self) -> dict:
        return {"script": "portfolio_overview", "mode": self._mode}

    def _render_go_nogo_card(self, asset_id: str) -> dict:
        return {"script": "go_nogo_card", "asset_id": asset_id, "mode": self._mode}

    def clear_cache(self, asset_id: Optional[str] = None) -> None:
        """캐시 초기화 — 사이클마다 fresh 렌더."""
        if asset_id:
            keys_to_del = [k for k in self._cache if k.startswith(f"{asset_id}:")]
            for k in keys_to_del:
                del self._cache[k]
        else:
            self._cache.clear()
