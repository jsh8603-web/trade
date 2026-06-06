#!/usr/bin/env python3
"""scripts/run_replay.py — WP6③ turnkey PIT 백테스트 리플레이 runner (Phase I).

용도: 과거 캔들을 N배속(실시간 sleep 없음)으로 리플레이 → AssetTrack 결정 →
  BacktestEngine(Upbit 비용 + 학습 sink) → 메트릭 → go/no-go 카드(JSON).

현 단계(WP6③):
- 데이터: Upbit 일봉 캔들(무료, 무인증) 실 pull.
- 결정 track: 단순 RSI 룰(데모용·결정론) — 라이브 결정엔진(CoinTrackWithMacro→Orchestrator)
  연결은 WP1 spine 이후(full PIT 환경=WP6② provider + WP4 macro).
- 학습: memory=MemoryLayer 주입 → BUY store_decision / SELL update_with_outcome 폐쇄(WP6②).

실행: python scripts/run_replay.py --market KRW-BTC --count 200
SACRED: 실주문 0건(백테스트 시뮬만), 라이브 경로 미접촉.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402
import requests  # noqa: E402

from backtest.engine import BacktestEngine  # noqa: E402
from backtest.coin_engine import UPBIT_COST_CONFIG  # noqa: E402
from backtest.pbo import assess_go_nogo, GoNoGoStatus  # noqa: E402
from core.asset_track import AssetTrack, MarketState  # noqa: E402
from common.metrics import calculate_rsi  # noqa: E402
from core.brain.memory_layer import MemoryLayer  # noqa: E402


def fetch_upbit_daily(market: str, count: int) -> pd.DataFrame:
    """Upbit 일봉 캔들 pull(무료·무인증). 시간순 정렬 DataFrame(close, volume)."""
    rows: list[dict] = []
    to = None
    remaining = count
    while remaining > 0:
        n = min(200, remaining)
        params = {"market": market, "count": n}
        if to:
            params["to"] = to
        r = requests.get(
            "https://api.upbit.com/v1/candles/days", params=params, timeout=10
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        rows.extend(batch)
        to = batch[-1]["candle_date_time_utc"]  # 다음 페이지(과거 방향)
        remaining -= len(batch)
    if not rows:
        raise RuntimeError(f"Upbit 캔들 0건: {market}")
    df = pd.DataFrame(rows)
    df["dt"] = pd.to_datetime(df["candle_date_time_utc"], utc=True)
    df = df.drop_duplicates("dt").sort_values("dt").set_index("dt")
    return pd.DataFrame(
        {"close": df["trade_price"], "volume": df["candle_acc_trade_price"]}
    )


class RsiReplayTrack(AssetTrack):
    """데모 결정 track — 누적 close 로 RSI 계산, 과매도 매수/과매수 매도(결정론)."""

    def __init__(self, low: float = 35.0, high: float = 65.0, period: int = 14):
        self._closes: list[float] = []
        self._low, self._high, self._period = low, high, period

    def collect_market_state(self, as_of=None) -> MarketState:
        return MarketState(raw_market_data={"as_of": as_of.isoformat() if as_of else None})

    def generate_candidate(self, state):
        price = state.raw_market_data.get("price")
        if price is not None:
            self._closes.append(float(price))
        action, rsi = "hold", None
        if len(self._closes) > self._period:
            rsi = calculate_rsi(self._closes, self._period)
            if rsi <= self._low:
                action = "buy"
            elif rsi >= self._high:
                action = "sell"

        class _D:
            pass
        d = _D()
        d.action = action
        d.reason = f"RSI={rsi:.1f}" if rsi is not None else "warmup"
        d.confidence = 0.6
        return d

    def recommended_next_check(self, state):
        return datetime.now(timezone.utc)


def _max_drawdown_pct(equity: pd.Series) -> float:
    if len(equity) < 2:
        return 0.0
    dd = (equity / equity.cummax() - 1.0).min()
    return float(dd) * 100.0


def main() -> int:
    ap = argparse.ArgumentParser(description="PIT 백테스트 리플레이 runner")
    ap.add_argument("--market", default="KRW-BTC")
    ap.add_argument("--count", type=int, default=200, help="일봉 개수")
    ap.add_argument("--capital", type=float, default=1_000_000.0)
    # A1: risk pipeline opt-in (기본 off = _run_legacy byte-identical)
    ap.add_argument("--risk-pipeline", action="store_true", default=False,
                    help="use_risk_pipeline=True 경로 활성화 (P2A A1)")
    args = ap.parse_args()

    df = fetch_upbit_daily(args.market, args.count)
    prices = df["close"].rename(args.market)
    volumes = df["volume"]

    mem = MemoryLayer()
    engine = BacktestEngine(
        cost_config=UPBIT_COST_CONFIG,
        initial_capital=args.capital,
        use_risk_pipeline=args.risk_pipeline,  # A1: opt-in flag
    )
    result = engine.run(RsiReplayTrack(), prices, volumes, region="KR", memory=mem)

    sells = [t for t in result.trades if getattr(t, "side", "") == "SELL"]
    wins = [t for t in sells if (getattr(t, "pnl", 0.0) or 0.0) > 0]
    win_rate = 100.0 * len(wins) / len(sells) if sells else 0.0
    max_dd = _max_drawdown_pct(result.equity_curve)
    status, reason = assess_go_nogo(result.sharpe, len(sells), max_dd, win_rate)
    learned = sum(
        1 for e in mem._store if getattr(e, "outcome_pct", None) is not None
    )

    # A1: per-bar checksum 메타 (risk_pipeline on 시만 존재)
    bar_checksums = getattr(result, "_bar_checksums", None)
    checksum_sample = bar_checksums[:3] if bar_checksums else None

    card = {
        "market": args.market,
        "bars": int(len(prices)),
        "period": [str(prices.index[0]), str(prices.index[-1])],
        "trades": len(result.trades),
        "sells": len(sells),
        "sharpe": round(result.sharpe, 3),
        "max_drawdown_pct": round(max_dd, 2),
        "total_return_pct": round(result.total_return_pct, 2),
        "win_rate_pct": round(win_rate, 1),
        "go_no_go": status.value if isinstance(status, GoNoGoStatus) else str(status),
        "reason": reason,
        "memory_entries": len(mem),
        "learned_outcomes": learned,
        # A1: risk pipeline 메타
        "risk_pipeline": args.risk_pipeline,
        "bar_checksum_sample": checksum_sample,
    }
    print(json.dumps(card, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
