"""core/data/factor_returns.py — IC2: factor 레벨 시계열 → static Λ (corr_prior 입력용).

WHY: `_ic_corr_prior`(regime_to_weights)가 현재 Λ=단위(부호 구조만). R9 IC2 결선 = static-Λ →
배분 corr_prior / gate-Λ → risk_gate clamp(two-layer). 본 모듈이 factor 레벨(FRED) → 혁신 →
**static 장기 Λ**(long half-life, 안정성>반응성)를 산출해 corr_prior magnitude 를 채운다.

설계:
- 추정 로직(to_factor_returns·estimate_factor_cov)은 factor_cov_estimate 재사용(신규 0).
- static Λ = long half-life EWMA(default 250d ≈ 표본공분산, gate 의 75d reactive 와 분리=two-layer).
- source_fn 주입 가능(테스트 mock / 실 fetch=FRED). 실패/부족 시 None → 호출자 Λ=단위 fallback(무회귀).
- opt-in 게이트는 호출자(_ic_corr_prior)가 관리. 본 모듈은 순수 데이터→Λ.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Callable, Optional, Sequence

import numpy as np

# factor → FRED series (rate/credit=Δ, dollar/oil/vol/fx=Δlog; 변환은 factor_cov_estimate.FACTOR_TRANSFORM)
FACTOR_SERIES = {
    "rate": "DGS10",            # 10Y Treasury yield
    "dollar": "DTWEXBGS",       # Broad USD TWI
    "oil": "DCOILWTICO",        # WTI spot
    "credit": "BAMLH0A0HYM2",   # HY OAS
    "vol": "VIXCLS",            # VIX
    "fx": "DEXKOUS",            # KRW per USD (IC8 denomination factor — KRW 투자자 USD자산 환노출).
                                #   dollar(broad TWI 글로벌 강세)와 별 채널: fx=USDKRW 환산. 이중계상 0.
}


def fetch_factor_cov(
    as_of: Optional[object] = None,
    lookback_days: int = 750,
    factors: Optional[Sequence[str]] = None,
    *,
    source_fn: Optional[Callable] = None,
    halflife: float = 250.0,
    min_rows: int = 60,
) -> Optional[np.ndarray]:
    """factor 레벨 → 혁신 → static 장기 Λ(F,F). 부족/실패 시 None.

    source_fn(series_ids, start, end) -> {factor: 1d level array}. None=FRED(fred_adapter).
    halflife: static long(default 250d). gate 용(75d)과 분리.
    """
    from core.study.factor_cov_estimate import to_factor_returns, estimate_factor_cov

    facs = list(factors) if factors else list(FACTOR_SERIES.keys())
    facs = [f for f in facs if f in FACTOR_SERIES]
    if len(facs) < 2:
        return None
    a = _as_date(as_of)
    end = a - timedelta(days=1)                          # 전일까지(lookahead 차단)
    start = end - timedelta(days=int(lookback_days * 1.5) + 30)
    src = source_fn or _default_fred_source
    try:
        levels = src([FACTOR_SERIES[f] for f in facs], start, end)
    except Exception:
        return None
    if not levels:
        return None
    # series_id 키 → factor 키 정렬
    sid_to_fac = {FACTOR_SERIES[f]: f for f in facs}
    lv = {}
    for sid, arr in levels.items():
        f = sid_to_fac.get(sid, sid)
        a_arr = np.asarray(arr, float)
        a_arr = a_arr[~np.isnan(a_arr)]
        if len(a_arr) >= min_rows:
            lv[f] = a_arr[-lookback_days:]
    keep = [f for f in facs if f in lv]
    if len(keep) < 2:
        return None
    # 길이 정렬(공통 최소 — 단순 tail align; PIT 정밀 정렬은 호출자 vintage 책임)
    m = min(len(lv[f]) for f in keep)
    if m < min_rows:
        return None
    levels_aligned = {f: lv[f][-m:] for f in keep}
    R = to_factor_returns(levels_aligned, keep)           # (m-1, F)
    res = estimate_factor_cov(R, keep, halflife=halflife)
    return np.asarray(res.cov, float)


def _default_fred_source(series_ids: Sequence[str], start: date, end: date) -> dict:
    """FRED 레벨 시계열 (RealFredAdapter.get_series 경유). 실패/unavailable 시 예외 → 호출자 None.

    fred_adapter 에 `fetch_series_levels` 는 없음 — 계약은 `get_series(series_id, as_of)`.
    get_series = first-release PIT(발표시점값, lookahead 없음) + as_of=end 상한 causal mask.
    start 로 lookback 하한 슬라이스. 반환 {series_id: 1d level array}.
    키/네트워크/fredapi 부재 → is_available()=False → RuntimeError → fetch_factor_cov 가 None 처리.
    """
    import pandas as pd
    from core.brain.fred_adapter import RealFredAdapter  # 지연 import

    adapter = RealFredAdapter()
    if not adapter.is_available():
        raise RuntimeError("FRED adapter unavailable (no api_key / fredapi)")
    start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)
    out = {}
    for sid in series_ids:
        s = adapter.get_series(sid, as_of=end_ts)   # PIT 상한(전일)
        if s is None or len(s) == 0:
            continue
        s = s[s.index >= start_ts]                  # lookback 하한
        if len(s) > 0:
            out[sid] = s.to_numpy(dtype=float)
    return out


def _as_date(x: Optional[object]) -> date:
    if x is None:
        import pandas as pd
        return pd.Timestamp.today().date()
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    import pandas as pd
    return pd.Timestamp(str(x)).date()


if __name__ == "__main__":
    # self-test: mock factor 레벨(합성) → static Λ PSD + 형태
    def _mock(series_ids, start, end):
        rng = np.random.default_rng(0)
        out = {}
        for sid in series_ids:
            # 레벨 시계열(누적) — rate/credit 은 차분, dollar/oil 은 로그수익 변환됨
            out[sid] = 100 + np.cumsum(rng.standard_normal(400) * 0.5)
        return out

    Lam = fetch_factor_cov(as_of="2026-06-01", lookback_days=300, source_fn=_mock)
    assert Lam is not None, "Lam None"
    nf = len(FACTOR_SERIES)
    assert Lam.shape == (nf, nf), Lam.shape
    eig = np.linalg.eigvalsh(Lam)
    assert eig.min() > -1e-8, f"not PSD: {eig.min()}"
    print(f"factor_returns self-test PASS: Lam shape={Lam.shape}, min eig={eig.min():.2e}")
