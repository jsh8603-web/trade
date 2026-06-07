"""core/data/sleeve_returns.py — 배분 sleeve 수익률 패널 (IC0: returns_history 공급).

WHY: allocate(returns_history=None) → _belief_conditional_cov 미진입 → corr_prior/glasso/Λ
dormant. 본 모듈이 SLEEVES 대표 ETF 가격 → PIT 일별 로그수익률 패널을 만들어 공급해야
IC1 배선(corr_prior)·IC2(Λ)가 실효한다.

설계:
- opt-in(INV_R15_WEIGHTS) 게이트 뒤에서만 호출(호출부 coin_track_macro). off=공급 0=무회귀.
- source_fn 주입 가능(테스트 mock / 실 fetch 분리). default=yfinance 전일 종가(lookahead 차단).
- 실패/데이터 부재 시 None 반환 → allocate fallback(_fallback_hrp) 무회귀.
- ★1차: 각 sleeve USD 표시 대표 ETF close → log-return. FX local-return 분리(IC8)는 후속.
- sleeve→ticker 매핑은 합리적 default(사용자 조정 가능, progress-wire-impl IC0).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Callable, Optional, Sequence

import numpy as np
import pandas as pd

# 배분 SLEEVES 대표 자산 (regime_to_weights.SLEEVES 와 키 일치). USD 표시 ETF 1차.
SLEEVE_TICKERS = {
    "us_stock": "SPY",      # S&P500
    "kr_stock": "EWY",      # iShares MSCI South Korea (USD) — KRW local-return 은 IC8 후속
    "commodity": "DBC",     # Invesco DB Commodity
    "gold": "GLD",          # SPDR Gold
    "bond": "BND",          # Vanguard Total Bond
    "cash": "BIL",          # SPDR 1-3M T-Bill
    "coin": "BTC-USD",      # Bitcoin
}


def _default_yf_source(tickers: Sequence[str], start: date, end: date) -> "pd.DataFrame":
    """yfinance 종가 패널 (index=date, columns=ticker). 실패 시 예외 → 호출자 None 처리."""
    import yfinance as yf  # 지연 import(opt-in on 경로에서만 의존)

    raw = yf.download(list(tickers), start=start.isoformat(), end=end.isoformat(),
                      progress=False, auto_adjust=True)
    # multi-ticker → ('Close', ticker), single → 'Close'
    close = raw["Close"] if "Close" in raw else raw
    if isinstance(close, pd.Series):
        close = close.to_frame(tickers[0])
    return close


def fetch_sleeve_returns(
    as_of: Optional[object] = None,
    lookback_days: int = 252,
    sleeves: Optional[Sequence[str]] = None,
    *,
    source_fn: Optional[Callable] = None,
    min_rows: int = 30,
) -> Optional["pd.DataFrame"]:
    """배분 sleeve 일별 로그수익률 패널. allocate(returns_history=) 입력.

    as_of: PIT 기준일(None=오늘). end = as_of 전일(당일 종가 미확정 → lookahead 차단).
    반환: DataFrame(index=date, columns=sleeve, values=log-return). 부족/실패 시 None.
    source_fn(tickers, start, end)->close DataFrame 주입(테스트 mock). None=yfinance.
    """
    cols = list(sleeves) if sleeves else list(SLEEVE_TICKERS.keys())
    tickers = [SLEEVE_TICKERS[s] for s in cols if s in SLEEVE_TICKERS]
    if not tickers:
        return None
    a = _as_date(as_of)
    end = a - timedelta(days=1)                      # 전일까지(당일 미확정 차단)
    start = end - timedelta(days=int(lookback_days * 1.6) + 10)  # 거래일 공백 여유
    src = source_fn or _default_yf_source
    try:
        close = src(tickers, start, end)
    except Exception as _exc:  # C2: data_empty 라벨 — 동작 동일(None 반환), silent 제거
        import logging as _log
        _log.getLogger(__name__).warning(
            "fetch_sleeve_returns data_empty: price fetch failed [label=data_empty] exc=%r",
            _exc,
        )
        return None
    if close is None or len(close) < min_rows:
        return None
    # ticker→sleeve 역매핑(컬럼명 sleeve 로) — 정렬 일관성
    tick_to_sleeve = {SLEEVE_TICKERS[s]: s for s in cols if s in SLEEVE_TICKERS}
    close = close.rename(columns=tick_to_sleeve)
    keep = [s for s in cols if s in close.columns]
    if len(keep) < 2:
        return None
    px = close[keep].astype(float).sort_index()
    rets = np.log(px).diff().dropna(how="all")
    rets = rets.tail(lookback_days)
    if len(rets) < min_rows:
        return None
    return rets


def _as_date(x: Optional[object]) -> date:
    if x is None:
        # Date.now 류 금지 환경 대비: pandas Timestamp.today 사용
        return pd.Timestamp.today().date()
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    return pd.Timestamp(str(x)).date()


if __name__ == "__main__":
    # self-test: mock source(합성 가격) → 패널 형태 + 무에러
    def _mock(tickers, start, end):
        idx = pd.bdate_range(start, end)
        rng = np.random.default_rng(0)
        data = {t: 100 * np.exp(np.cumsum(rng.standard_normal(len(idx)) * 0.01))
                for t in tickers}
        return pd.DataFrame(data, index=idx)

    panel = fetch_sleeve_returns(as_of="2026-06-01", lookback_days=120, source_fn=_mock)
    assert panel is not None, "panel None"
    assert list(panel.columns) == list(SLEEVE_TICKERS.keys()), panel.columns.tolist()
    assert len(panel) <= 120 and len(panel) >= 30, len(panel)
    assert not panel.isna().all().any(), "all-NaN column"
    print("sleeve_returns self-test PASS: shape", panel.shape, "cols", list(panel.columns))
