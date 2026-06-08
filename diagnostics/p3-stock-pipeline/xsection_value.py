"""P3-2a 다종목 횡단면 value alpha 측정 (순수 B, overlay OFF).

자문 결론(2026-06-07 2R+검증): value alpha 는 횡단면 rank-IC 로만 측정 가능.
  매 리밸런스 시점: 각 종목 valuation_gap(cheapness) = value_stock(PIT funds, quote).
  forward Q return 과 cross-sectional Spearman rank-IC → IC 시계열.
  + beta-neutral(종목별 β·SPY 차감) IC + tercile L/S + NW HAC t-stat.

★수정(2026-06-08): 기존 "market-excess = f - spy_f"(스칼라 상수 차감)는 Spearman rank-IC 에
  no-op(횡단면 상수 차감→순위 불변, raw IC 와 완전동일). L/S 도 long−short 에서 상수 상쇄.
  → 종목별 β 차감(f - β_t·spy_f)으로 교체. β_t 가 종목마다 달라 순위가 바뀌어 진짜 베타중립.
  value 의 저베타 틸트를 alpha 와 분리(베타중립 IC ≠ raw IC 이면 alpha 가 베타 너머 생존).

LLM/dip overlay OFF(순수 value rank). 단일종목 아님(횡단면).
통계 hedge: n_rebalance<30 → 방향성 prior, 단정 금지(NW t·CI 부착).
"""
from __future__ import annotations
import sys
import numpy as np
import pandas as pd

# 대형주 다양 섹터(EDGAR 무료 커버). 1차 스모크 — 검증 후 확대.
TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "JPM", "BAC",
           "KO", "PG", "WMT", "JNJ", "PFE", "XOM", "CVX", "HD", "INTC",
           "CSCO", "VZ", "MRK", "ABBV", "T", "ORCL", "QCOM"]
START, END = "2017-01-01", "2026-05-01"
FWD_DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 63  # forward 영업일(기본 1Q)


def main():
    import yfinance as yf
    from stock.data.fundamentals_pit_provider import FundamentalsPitProvider
    from stock.valuation import value_stock
    from stock.contracts import MarketQuote
    from datetime import datetime

    print(f"[fetch] 가격 {len(TICKERS)}종목+SPY ...")
    px = yf.download(TICKERS + ["SPY"], start=START, end=END, auto_adjust=True, progress=False)["Close"]
    spy = px["SPY"]
    daily = px.pct_change()   # 일수익(종목별 β 추정용)
    fp = FundamentalsPitProvider()

    def beta_at(t, d, window=252):
        """종목 t 의 as-of d 추세 β(종목 일수익 ~ SPY 일수익 OLS). 표본부족=1.0 폴백."""
        if t not in daily.columns:
            return 1.0
        sub = daily[[t, "SPY"]][daily.index <= d].dropna().iloc[-window:]
        if len(sub) < 60 or float(sub["SPY"].var()) <= 0:
            return 1.0
        return float(np.cov(sub[t], sub["SPY"])[0, 1] / sub["SPY"].var())

    # 분기말 리밸런스 날짜
    rebal = pd.date_range(START, END, freq="QE")
    rebal = [d for d in rebal if d >= px.index[0] and d <= px.index[-1]]

    def price_at(t, d):
        if t not in px.columns:
            return None
        s = px[t][px[t].index <= d].dropna()
        return float(s.iloc[-1]) if not s.empty else None

    def fwd_ret(s_series, d, fwd):
        s = s_series[s_series.index <= d].dropna()
        if s.empty:
            return None
        p0 = float(s.iloc[-1])
        sf = s_series[s_series.index > d].dropna()
        if sf.empty:
            return None
        # fwd 영업일 후(또는 가능한 마지막)
        sf2 = sf.iloc[:fwd]
        if sf2.empty:
            return None
        p1 = float(sf2.iloc[-1])
        return p1 / p0 - 1.0 if p0 > 0 else None

    ic_raw, ic_exc, ls_exc = [], [], []
    coverage = []
    for d in rebal:
        gaps, frets, frets_exc = {}, {}, {}
        spy_f = fwd_ret(spy, d, FWD_DAYS)
        for t in TICKERS:
            p = price_at(t, d)
            if p is None:
                continue
            try:
                fr = fp.get_fundamentals_pit(t, pd.Timestamp(d), "US")
            except Exception:
                continue
            if not fr.available or not fr.filings:
                continue
            q = MarketQuote(ticker=t, as_of=datetime.combine(d.date(), datetime.min.time()),
                            price=p, market_cap=None, price_change_pct=None, price_change_window_days=None)
            v = value_stock(fr.filings, q)
            if v is None:
                continue
            f = fwd_ret(px[t], d, FWD_DAYS)
            if f is None:
                continue
            gaps[t] = v.valuation_gap
            frets[t] = f
            # ★베타중립: 종목별 β·SPY 차감(상수 차감은 rank-IC no-op이라 폐기)
            frets_exc[t] = (f - beta_at(t, d) * spy_f) if spy_f is not None else f
        common = sorted(set(gaps) & set(frets))
        coverage.append((d.date().isoformat(), len(common)))
        if len(common) < 6:
            continue
        g = np.array([gaps[t] for t in common])
        fr_raw = np.array([frets[t] for t in common])
        fr_exc = np.array([frets_exc[t] for t in common])
        # Spearman rank-IC
        from scipy.stats import spearmanr
        ic1, _ = spearmanr(g, fr_raw)
        ic2, _ = spearmanr(g, fr_exc)
        ic_raw.append(ic1)
        ic_exc.append(ic2)
        # tercile L/S(상위 1/3 cheap − 하위 1/3), market-excess
        order = np.argsort(-g)  # cheap(gap 큰) 우선
        k = max(1, len(common) // 3)
        long_ret = fr_exc[order[:k]].mean()
        short_ret = fr_exc[order[-k:]].mean()
        ls_exc.append(long_ret - short_ret)

    def nw_tstat(x, lags=4):
        x = np.asarray([v for v in x if v == v])
        n = len(x)
        if n < 3:
            return np.nan, np.nan
        mu = x.mean()
        dev = x - mu
        gamma0 = (dev @ dev) / n
        var = gamma0
        for L in range(1, min(lags, n - 1) + 1):
            w = 1 - L / (lags + 1)
            cov = (dev[L:] @ dev[:-L]) / n
            var += 2 * w * cov
        se = np.sqrt(var / n) if var > 0 else np.nan
        return mu, (mu / se if se and se > 0 else np.nan)

    print("\n" + "=" * 90)
    print(f"[P3-2a 횡단면 value rank-IC] n_rebalance={len(ic_raw)}, FWD={FWD_DAYS}d, 유니버스 {len(TICKERS)}")
    print("=" * 90)
    cov_arr = [c for _, c in coverage]
    print(f"커버리지(종목수/리밸런스): 중앙값 {np.median(cov_arr):.0f}, min {min(cov_arr)}, max {max(cov_arr)}")

    for label, ic in [("raw IC", ic_raw), ("beta-neutral IC(종목별 β·SPY 차감)", ic_exc)]:
        mu, t = nw_tstat(ic)
        arr = np.array(ic)
        print(f"\n[{label}] n={len(ic)}")
        print(f"  평균 IC = {mu:+.4f}  (NW-HAC t = {t:+.2f})")
        print(f"  IC>0 비율 = {(arr > 0).mean():.2%}   IC 표준편차 = {arr.std():.4f}")
        # block bootstrap 95% CI
        if len(arr) >= 6:
            rng = np.random.RandomState(42)
            bl = max(2, len(arr) // 5)
            boots = []
            for _ in range(2000):
                idx = rng.randint(0, len(arr) - bl + 1, size=len(arr) // bl + 1)
                samp = np.concatenate([arr[i:i + bl] for i in idx])[:len(arr)]
                boots.append(samp.mean())
            lo, hi = np.percentile(boots, [2.5, 97.5])
            print(f"  block-bootstrap 95% CI = [{lo:+.4f}, {hi:+.4f}]")

    mu_ls, t_ls = nw_tstat(ls_exc)
    print(f"\n[tercile L/S (cheap−rich, market-excess)] n={len(ls_exc)}")
    print(f"  평균 분기수익차 = {mu_ls:+.4f} ({mu_ls*4:+.2%}/yr 근사, NW t={t_ls:+.2f})")
    print("=" * 90)
    print("hedge: n_rebalance<30 → 방향성 prior. value 정설=cheap이 forward 초과수익(IC>0).")


if __name__ == "__main__":
    main()
