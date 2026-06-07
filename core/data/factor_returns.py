"""core/data/factor_returns.py — IC2: factor 레벨 시계열 → static Λ (corr_prior 입력용).

WHY: `_ic_corr_prior`(regime_to_weights)가 현재 Λ=단위(부호 구조만). R9 IC2 결선 = static-Λ →
배분 corr_prior / gate-Λ → risk_gate clamp(two-layer). 본 모듈이 factor 레벨(FRED) → 혁신 →
**static 장기 Λ**(long half-life, 안정성>반응성)를 산출해 corr_prior magnitude 를 채운다.

설계:
- 추정 로직(to_factor_returns·estimate_factor_cov)은 factor_cov_estimate 재사용(신규 0).
- static Λ = long half-life EWMA(default 250d ≈ 표본공분산, gate 의 75d reactive 와 분리=two-layer).
- source_fn 주입 가능(테스트 mock / 실 fetch=FRED). 실패/부족 시 None → 호출자 Λ=단위 fallback(무회귀).
- opt-in 게이트는 호출자(_ic_corr_prior)가 관리. 본 모듈은 순수 데이터→Λ.

★C1 credit splice (P3-prep, 2026-06-07):
- BAMLH0A0HYM2(HY OAS) = FRED BofA 라이센스 2023-05~ 이후만 가용.
- 이전 구간(~2023-04): BAA10Y(IG proxy, 1986~) 로 splice.
- 단위 통일: 둘 다 basis-points 레벨 → Δlevel(first-difference) = 동일 단위 (FACTOR_TRANSFORM credit="diff").
- 2023-05 cutover 점프 없음(Δ 변환 후 레벨 불연속은 사라짐).
- credit_grade_mismatch confidence 라벨: BAA10Y 구간=IG grade, HY OAS 구간=HY grade. 믹스 lookback 시 라벨 박제.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Callable, Optional, Sequence

import numpy as np

# factor → FRED series (real/credit/breakeven=Δ, dollar/oil/vol/fx=Δlog; 변환=factor_cov_estimate.FACTOR_TRANSFORM)
# ★Y5(2026-06-02): rate(DGS10 명목)→real(DFII10) 교체(명목·실질 corr 0.914 공선, real=gold driver 경제적
#   정합) + breakeven(T5YIE) 추가. MOVE/slope=joint multivariate β→0(VIX 흡수, 이중계상)로 DROP(factor 미포함).
# ★C1(2026-06-07): credit 기본 = HY OAS(BAMLH0A0HYM2). as_of<2023-05 구간 = BAA10Y splice.
#   fetch_factor_cov 내부에서 credit_series_for(as_of) 경유 — 정적 FACTOR_SERIES[credit]는 기본값 유지.
FACTOR_SERIES = {
    "real": "DFII10",           # 10Y TIPS real yield (★rate=DGS10 교체)
    "dollar": "DTWEXBGS",       # Broad USD TWI
    "oil": "DCOILWTICO",        # WTI spot
    "credit": "BAMLH0A0HYM2",   # HY OAS (as_of>=2023-05). 이전=BAA10Y splice(credit_series_for 경유).
    "vol": "VIXCLS",            # VIX
    "breakeven": "T5YIE",       # 5Y breakeven inflation (★Y5 추가 — commod adopt)
    "fx": "DEXKOUS",            # KRW per USD (IC8 denomination factor — KRW 투자자 USD자산 환노출).
                                #   dollar(broad TWI 글로벌 강세)와 별 채널: fx=USDKRW 환산. 이중계상 0.
}

# ★C1: credit splice 경계. BAMLH0A0HYM2 FRED BofA 라이센스 가용 시작(2023-05-01).
_CREDIT_SPLICE_CUTOVER = date(2023, 5, 1)
_CREDIT_HY_SERIES = "BAMLH0A0HYM2"   # HY OAS (2023-05~)
_CREDIT_IG_SERIES = "BAA10Y"          # IG Moody BAA-Treasury (1986~, splice proxy)


def credit_series_for(as_of: object) -> str:
    """as_of 시점 기준 credit factor FRED 시리즈 ID 반환.

    as_of >= 2023-05-01 → BAMLH0A0HYM2(HY OAS, BofA FRED 가용).
    as_of <  2023-05-01 → BAA10Y(Moody's IG proxy, 1986~, splice).

    C1 설계: 단위=Δlevel(basis-points first-difference). 두 시리즈 모두 bp 레벨 →
    diff 변환 후 Δbp로 통일. 2023-05 cutover 레벨 점프는 Δ 후 사라짐.
    """
    d = _as_date(as_of)
    return _CREDIT_HY_SERIES if d >= _CREDIT_SPLICE_CUTOVER else _CREDIT_IG_SERIES


def credit_confidence_label(start: date, end: date) -> str:
    """lookback 기간에 두 grade 가 혼재하면 credit_grade_mismatch 라벨 반환.

    start~end 가 2023-05 경계를 걸치면 'credit_grade_mismatch(BAA10Y+HY_OAS_splice)'
    한 grade 만이면 해당 grade 라벨.
    """
    if start < _CREDIT_SPLICE_CUTOVER <= end:
        return "credit_grade_mismatch(BAA10Y+HY_OAS_splice)"
    elif end < _CREDIT_SPLICE_CUTOVER:
        return "credit_grade=IG(BAA10Y)"
    else:
        return "credit_grade=HY_OAS"


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

    ★C1: credit factor = as_of 기준 조건부 splice (credit_series_for 경유).
    lookback 기간에 경계 걸치면 credit_confidence_label 로 grade mismatch 기록.
    """
    from core.study.factor_cov_estimate import to_factor_returns, estimate_factor_cov

    facs = list(factors) if factors else list(FACTOR_SERIES.keys())
    facs = [f for f in facs if f in FACTOR_SERIES]
    if len(facs) < 2:
        return None
    a = _as_date(as_of)
    end = a - timedelta(days=1)                          # 전일까지(lookahead 차단)
    start = end - timedelta(days=int(lookback_days * 1.5) + 30)

    # ★C1: credit factor → splice 시리즈 결정 (as_of 기준)
    def _resolve_series_id(f: str) -> str:
        if f == "credit":
            return credit_series_for(a)  # as_of 기준 BAA10Y or BAMLH0A0HYM2
        return FACTOR_SERIES[f]

    series_ids = [_resolve_series_id(f) for f in facs]
    # sid → factor 역매핑 (credit splice 시 resolved id 사용)
    sid_to_fac = {_resolve_series_id(f): f for f in facs}

    src = source_fn or _default_fred_source
    try:
        levels = src(series_ids, start, end)
    except Exception as _exc:  # C2: source_missing 라벨 — 동작 동일(None 반환), silent 제거
        import logging as _log
        _log.getLogger(__name__).warning(
            "fetch_factor_cov source_missing: factor fetch failed [label=source_missing] exc=%r",
            _exc,
        )
        return None
    if not levels:
        return None

    # ★C1: credit_grade_mismatch 신뢰도 라벨 기록 (lookback 경계 걸치면)
    if "credit" in facs:
        import logging
        clabel = credit_confidence_label(start, end)
        if "mismatch" in clabel:
            logging.getLogger(__name__).info(
                "fetch_factor_cov credit_confidence: %s (start=%s end=%s as_of=%s)",
                clabel, start, end, a,
            )

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
