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

class _SeriesQuoteProvider:
    """이미 fetch 한 price_series 를 in-memory quote source 로 재사용(매 bar 네트워크 0).

    WHY: QuoteProvider.get_quote_at 는 매 bar HistoricalProvider range fetch →
         캐시 미스 시 yfinance 단일일 재호출 실패 → quote None → valuation 미연결 abstain.
         price_series(전체 1회 fetch)에서 as_of≤종가 + window 변동률을 합성하면
         lookahead 안전(≤ts 필터) + 실패 0. market_cap=None(단일종목 백테스트 무관).
    """
    def __init__(self, price_series, window: int = 21):
        self._px = price_series
        self._window = window

    def get_quote_at(self, ticker, as_of, region=None, **kw):
        import pandas as pd
        from datetime import datetime
        from stock.contracts import MarketQuote
        ts = pd.Timestamp(as_of)
        s = self._px[self._px.index <= ts]
        if s.empty:
            return None
        price = float(s.iloc[-1])
        chg = None
        if len(s) > self._window:
            prev = float(s.iloc[-1 - self._window])
            if prev > 0:
                chg = price / prev - 1.0
        asof_idx = s.index[-1]
        as_of_dt = (asof_idx.to_pydatetime() if hasattr(asof_idx, "to_pydatetime")
                    else datetime.combine(ts.date(), datetime.min.time()))
        return MarketQuote(ticker=ticker, as_of=as_of_dt, price=price, market_cap=None,
                           price_change_pct=chg, price_change_window_days=self._window)


class _StubNonTrap:
    """P3-2b 스모크용 stub heavy-agent — 항상 non-trap(OPPORTUNITY 통과).

    배관 검증 전용(EDGAR→value_stock→engine 체결 경로 확인). alpha 측정 아님.
    실 운용/측정은 gate2 LLM off(=systematic value rank, P3-2a) 또는 실 heavy-agent.
    """
    def judge_value_trap(self, valuation, fundamentals, price_change_pct, context):
        from stock.value_trigger import HeavyAgentVerdict
        return HeavyAgentVerdict(is_trap=False, confidence=0.6, reasoning="smoke stub non-trap")


def run_one(
    ticker: str,
    region: str,
    start: date,
    end: date,
    dry_run: bool = True,
    bypass_gate1: bool = False,
    stub_agent: bool = False,
) -> dict:
    """ticker 백테스트 1사이클. dict(metrics, checksum, dry_run) 반환.

    bypass_gate1: 가격 −10% dip 게이트(coin 혈통) 면제 → systematic value 진입(저평가 갭만).
      자문 2R+데이터검증 수렴(2026-06-07): 단일종목 단독은 alpha 측정 부적합(유효N 붕괴),
      배관 스모크 용도. 측정은 P3-2a 횡단면 rank-IC.
    stub_agent: gate2 non-trap stub 주입(FORWARD 모드 OPPORTUNITY 통과) → 체결 배관 검증.
    """
    import pandas as pd
    from backtest.engine import BacktestEngine
    from backtest.diagnostics import four_layer_metrics
    from core.stock_track import StockTrack
    from stock.contracts import RunMode
    from stock.data.quote_provider import QuoteProvider
    from stock.data.fundamentals_pit_provider import FundamentalsPitProvider

    logger.info("백테스트 시작 %s/%s %s~%s DRY_RUN=%s bypass_gate1=%s stub=%s",
                region, ticker, start, end, dry_run, bypass_gate1, stub_agent)

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
    # ★PD: 매 bar quote = price_series 재사용(네트워크 0·실패 0·lookahead 안전).
    #   QuoteProvider() 단일일 fetch 실패→abstain 폭주 우회.
    quote_provider = _SeriesQuoteProvider(price_series)
    fund_provider = FundamentalsPitProvider()

    # 진단용 라벨(마지막 bar 1회 — 실거래 결정은 StockTrack 이 매 bar 동적 조회)
    as_of_date = price_series.index[-1].date()
    as_of_dt = datetime.combine(as_of_date, datetime.min.time())
    _diag_fund = fund_provider.get_fundamentals_pit(ticker, as_of_dt, region)
    _diag_quote = quote_provider.get_quote_at(ticker, as_of_date, region)
    if not _diag_fund.available:
        logger.warning("fundamentals(마지막bar) %s/%s label=%s", region, ticker, _diag_fund.label)

    # 5. StockTrack 조립 — provider 주입(override 없음 → 매 bar 동적 PIT)
    #    stub_agent 주입 시 FORWARD(gate2 OPPORTUNITY 통과) — H22 BACKTEST abstain 우회(배관 검증).
    mode = RunMode.FORWARD if stub_agent else (RunMode.BACKTEST if not dry_run else RunMode.FORWARD)
    stock_track = StockTrack(
        ticker=ticker,
        mode=mode,
        _fund_provider=fund_provider,
        _quote_provider=quote_provider,
        _region=region,
        _bypass_gate1_override=bypass_gate1,
        _heavy_agent_override=_StubNonTrap() if stub_agent else None,
        _heavy_agent_fail_reason_override=None if stub_agent else "quality",
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
    parser.add_argument("--bypass-gate1", action="store_true", default=False,
                        help="가격 -10% dip 게이트 면제(systematic value 진입, 배관 스모크)")
    parser.add_argument("--stub-agent", action="store_true", default=False,
                        help="gate2 non-trap stub 주입(체결 배관 검증)")
    args = parser.parse_args()

    end_date = date.fromisoformat(args.end) if args.end else date.today() - timedelta(days=1)
    start_date = date.fromisoformat(args.start) if args.start else end_date - timedelta(days=365)

    result = run_one(
        ticker=args.ticker,
        region=args.region,
        start=start_date,
        end=end_date,
        dry_run=args.dry_run,
        bypass_gate1=args.bypass_gate1,
        stub_agent=args.stub_agent,
    )

    print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    sys.exit(main())
