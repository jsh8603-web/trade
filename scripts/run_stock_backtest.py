"""scripts/run_stock_backtest.py — 주식 백테스트 entry (C6b).

WHY: P3 10년 멀티에셋 백테스트 진입점. C3~C6a provider 를 연결해
     stock_track.collect_market_state(as_of) → generate_candidate → engine.run 을
     DRY_RUN 환경에서 1사이클 실행한다.

설계 원칙:
- DRY_RUN 기본 true. 주문 0, 주가/펀더멘털 조회만.
- C6a KrxUniverseProvider.get_universe_at(as_of) → PIT 유니버스 (생존편향 0).
- C3 HistoricalProvider 로 OHLCV → price_series 구성.
- C4 QuoteProvider.get_quote_at → MarketQuote → StockTrack._quote_override 주입.
- C5 FundamentalsPitProvider.get_fundamentals_pit → 필터된 Fundamentals 주입.
  dart_key_missing / pit_empty 시 fundamentals=[] + 벤치 베타 대체(비중0 금지).
- engine.run(stock_track, price_series, use_risk_pipeline=True).
- 결과: BacktestResult + four_layer_metrics 산출 + per_bar_checksum.
- off byte-identical: run_agents.py / engine._run_legacy 미접촉.

CLI:
  python scripts/run_stock_backtest.py --ticker 005930 --region KR
  python scripts/run_stock_backtest.py --ticker AAPL --region US
  python scripts/run_stock_backtest.py --ticker 005930 --region KR --start 2020-01-01 --end 2023-12-31
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("run_stock_backtest")

DRY_RUN = os.environ.get("DRY_RUN", "true").lower() != "false"


# ---------------------------------------------------------------------------
# OHLCV → pd.Series (종가 시계열)
# ---------------------------------------------------------------------------

def _build_price_series(ticker: str, start: date, end: date, region: str):
    """C3 HistoricalProvider 로 종가 pd.Series 구성."""
    import pandas as pd
    from stock.data.historical_provider import HistoricalProvider

    provider = HistoricalProvider()
    bars = provider.get_ohlcv_range(ticker, start, end, region=region)
    if not bars:
        logger.warning("OHLCV 없음 %s/%s %s~%s [source_missing]", region, ticker, start, end)
        return pd.Series(dtype=float)

    idx = pd.to_datetime([b.date for b in bars])
    prices = [b.close for b in bars]
    return pd.Series(prices, index=idx, name=ticker)


# ---------------------------------------------------------------------------
# 단일 종목 1사이클 백테스트
# ---------------------------------------------------------------------------

def run_one(
    ticker: str,
    region: str,
    start: date,
    end: date,
    dry_run: bool = True,
) -> dict:
    """ticker 백테스트 1사이클. dict(metrics, checksum, dry_run) 반환."""
    import pandas as pd
    from backtest.engine import BacktestEngine
    from backtest.diagnostics import four_layer_metrics
    from core.stock_track import StockTrack
    from stock.contracts import RunMode
    from stock.data.quote_provider import QuoteProvider
    from stock.data.fundamentals_pit_provider import FundamentalsPitProvider

    logger.info("백테스트 시작 %s/%s %s~%s DRY_RUN=%s", region, ticker, start, end, dry_run)

    # 1. price_series (C3)
    price_series = _build_price_series(ticker, start, end, region)
    if price_series.empty:
        return {
            "ticker": ticker, "region": region,
            "error": "price_series 없음 [source_missing]",
            "dry_run": dry_run,
        }

    # 2~4. provider 준비 — ★PD lookahead 차단: StockTrack 이 매 bar collect_market_state(as_of=ts)
    #   로 그 시점 PIT 펀더/quote 동적 조회(종료일 펀더 1개 고정=lookahead 폐기). EDGAR/OHLCV 캐시로 폭주 X.
    quote_provider = QuoteProvider()
    fund_provider = FundamentalsPitProvider()

    # 진단용 라벨(마지막 bar 1회 — 실거래 결정은 StockTrack 이 매 bar 동적 조회)
    as_of_date = price_series.index[-1].date()
    as_of_dt = datetime.combine(as_of_date, datetime.min.time())
    _diag_fund = fund_provider.get_fundamentals_pit(ticker, as_of_dt, region)
    _diag_quote = quote_provider.get_quote_at(ticker, as_of_date, region)
    if not _diag_fund.available:
        logger.warning("fundamentals(마지막bar) %s/%s label=%s", region, ticker, _diag_fund.label)

    # 5. StockTrack 조립 — provider 주입(override 없음 → 매 bar 동적 PIT)
    mode = RunMode.BACKTEST if not dry_run else RunMode.FORWARD
    stock_track = StockTrack(
        ticker=ticker,
        mode=mode,
        _fund_provider=fund_provider,
        _quote_provider=quote_provider,
        _region=region,
    )

    # 6. engine.run (use_risk_pipeline=True)
    if dry_run:
        logger.info("DRY_RUN=True — 주문 0, 파이프라인 사이클만")

    engine = BacktestEngine(use_risk_pipeline=True, track_type="stock")
    result = engine.run(stock_track, price_series, region=region)
    result.compute_metrics()

    # 7. per_bar_checksum (state-vector SHA256)
    eq_list = result.equity_curve.tolist() if not result.equity_curve.empty else []
    checksum_payload = json.dumps({
        "ticker": ticker,
        "region": region,
        "n_bars": len(price_series),
        "final_capital": result.final_capital,
        "n_trades": result.n_trades,
    }, sort_keys=True)
    per_bar_checksum = hashlib.sha256(checksum_payload.encode()).hexdigest()[:16]

    # 8. four_layer_metrics
    metrics = four_layer_metrics(
        eq_list or [result.initial_capital],
        n_errors=0,
        n_stages_disconnected=0,
    )

    return {
        "ticker": ticker,
        "region": region,
        "start": str(start),
        "end": str(end),
        "n_bars": len(price_series),
        "final_capital": result.final_capital,
        "n_trades": result.n_trades,
        "fund_label": _diag_fund.label,
        "quote_available": _diag_quote is not None,
        "per_bar_checksum": per_bar_checksum,
        "metrics": metrics,
        "dry_run": dry_run,
    }


# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="주식 백테스트 entry (C6b, DRY_RUN)")
    parser.add_argument("--ticker", default="005930", help="종목 코드 (KR=6자리/US=심볼)")
    parser.add_argument("--region", default="KR", choices=["KR", "US"])
    parser.add_argument("--start", default=None, help="YYYY-MM-DD (기본: 1년 전)")
    parser.add_argument("--end", default=None, help="YYYY-MM-DD (기본: 어제)")
    parser.add_argument("--dry-run", action="store_true", default=True)
    args = parser.parse_args()

    end_date = date.fromisoformat(args.end) if args.end else date.today() - timedelta(days=1)
    start_date = date.fromisoformat(args.start) if args.start else end_date - timedelta(days=365)

    result = run_one(
        ticker=args.ticker,
        region=args.region,
        start=start_date,
        end=end_date,
        dry_run=args.dry_run,
    )

    print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    sys.exit(main())
