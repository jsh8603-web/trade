"""P3 9단계 검증 — construction.build_sleeve_decisions 실호출 스모크.

목적(사용자 2번): 파이프라인 9단계(개별종목 selection→ETF fallback)를 실제 호출해
끊긴 wire 발견. 우회 아님 — production 모듈(construction)을 그대로 호출.
metric_panel(pbr/ev_ebitda)은 EDGAR fundamentals 에서 지표 정의대로 산출(회계, selection 로직 아님).
"""
from __future__ import annotations
import os
import sys
import pandas as pd
from datetime import date, datetime


def _metric_panel(funds_by, mcap_by, signs):
    """sleeve_signs 의 metric 만 fundamentals 에서 산출. {metric:{ticker:val}}."""
    panel = {m: {} for m in signs}
    shares_prev = {}
    for t, funds in funds_by.items():
        if not funds:
            continue
        srt = sorted(funds, key=lambda f: f.filing_timestamp, reverse=True)
        cur = srt[0]
        mc = mcap_by.get(t)
        if not mc:
            continue
        if "pbr" in panel and cur.book_value:
            panel["pbr"][t] = mc / cur.book_value
        if "ev_ebitda" in panel and cur.ebitda:
            nd = (cur.total_debt or 0) - (cur.cash_and_equivalents or 0)
            panel["ev_ebitda"][t] = (mc + nd) / cur.ebitda
        if "ep_yield" in panel and cur.net_income:
            panel["ep_yield"][t] = cur.net_income / mc
        if "net_issuance" in panel and len(srt) > 4 and cur.outstanding_shares:
            old = srt[4].outstanding_shares
            if old:
                panel["net_issuance"][t] = cur.outstanding_shares / old - 1.0
    return panel


def main():
    sleeve = sys.argv[1] if len(sys.argv) > 1 else "cyclical"
    as_of = pd.Timestamp(sys.argv[2] if len(sys.argv) > 2 else "2022-06-01")
    fallback = sys.argv[3] if len(sys.argv) > 3 else "off"
    os.environ["ETF_FALLBACK"] = fallback

    from stock.construction import build_sleeve_decisions
    from stock.sleeve_signals import signs_for
    from stock.data.fundamentals_pit_provider import FundamentalsPitProvider
    import yfinance as yf

    # sleeve별 대표 universe (EDGAR 무료)
    UNIV = {
        "cyclical": ["XOM", "CVX", "CAT", "DE", "FCX", "NUE", "DOW"],
        "defensive": ["KO", "PG", "WMT", "JNJ", "PEP", "CL", "MO"],
        "mega_tech": ["AAPL", "MSFT", "NVDA", "GOOGL", "META"],
    }
    tickers = UNIV.get(sleeve, UNIV["cyclical"])
    signs = signs_for(sleeve)
    print(f"[9단계 스모크] sleeve={sleeve} signs={signs} ETF_FALLBACK={fallback} as_of={as_of.date()}")
    print(f"  universe={tickers}")

    fp = FundamentalsPitProvider()
    px = yf.download(tickers, period="max", auto_adjust=True, progress=False)["Close"]
    funds_by, quote_by, mcap_by = {}, {}, {}
    from stock.contracts import MarketQuote
    for t in tickers:
        fr = fp.get_fundamentals_pit(t, as_of, "US")
        if not fr.available or not fr.filings:
            print(f"   {t}: fundamentals 없음 ({fr.label})")
            continue
        s = px[t][px[t].index <= as_of].dropna() if t in px.columns else pd.Series(dtype=float)
        if s.empty:
            continue
        price = float(s.iloc[-1])
        cur = sorted(fr.filings, key=lambda f: f.filing_timestamp, reverse=True)[0]
        mc = (cur.outstanding_shares or 0) * price
        funds_by[t] = fr.filings
        quote_by[t] = MarketQuote(ticker=t, as_of=datetime.combine(as_of.date(), datetime.min.time()),
                                  price=price, market_cap=mc, price_change_pct=None, price_change_window_days=None)
        mcap_by[t] = mc

    panel = _metric_panel(funds_by, mcap_by, signs) if signs else {}
    print(f"  metric_panel 산출: {{m: n_tickers}} = {{{', '.join(f'{m}:{len(v)}' for m,v in panel.items())}}}")

    decisions = build_sleeve_decisions(
        sleeve, panel, mcap_by, funds_by, quote_by,
        mode=__import__("stock.contracts", fromlist=["RunMode"]).RunMode.FORWARD,
        deterministic_no_llm=True,   # LLM off 결정론 경로(gate2 overlay skip)
    )
    print(f"\n  build_sleeve_decisions → {len(decisions)} decisions:")
    for d in decisions[:12]:
        tk = d.get("ticker") or d.get("trade_params", {}).get("ticker") or "?"
        tw = d.get("target_weight")
        tw_s = f"{tw:.3f}" if isinstance(tw, (int, float)) else str(tw)
        itype = d.get("instrument_type", "stock")
        print(f"    {tk:8s} dec={d.get('decision','?')} w={tw_s} "
              f"verdict={d.get('verdict') or d.get('_value_verdict','?')} type={itype} "
              f"rank={d.get('rank','?')} cheap_z={d.get('cheapness_z','?')} "
              f"reason={str(d.get('selection_reason') or d.get('reason',''))[:55]}")


if __name__ == "__main__":
    main()
