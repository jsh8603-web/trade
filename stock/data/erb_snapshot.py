"""stock/data/erb_snapshot.py — ERB(earnings revision breadth) self-snapshot forward collector.

배경: ERB(상향-하향 revision breadth) = 외부 자문 양채널 1순위 alpha 후보. 단 BW8 11가설
실측엔 없는 미검증 prior(약한 축) — DEF-2/value 가 이미 입증돼 ERB 는 필수 아닌 보강.

무료 historical consensus 시계열(수년치)은 불가(자문 3소스 만장일치). 그러나 yfinance 가
무료로 다음을 제공 → self-snapshot 으로 매일 동결하면 forward 시계열 구축:
  - eps_revisions: upLast7days/upLast30days/downLast30days/downLast7Days (revision breadth 직접)
  - eps_trend    : current/7daysAgo/30daysAgo/60daysAgo/90daysAgo consensus (90d 윈도우 내장)
  - earnings_estimate: avg/low/high/numberOfAnalysts/growth

reserve_snapshot.py(crypto) 패턴 복제(bitemporal append-only):
  - fetch_erb_live(tickers, as_of) → yfinance per-ticker fetch
  - build_snapshot_rows(raw, as_of) → (ticker,period) × sys_time=as_of 동결행
  - append_snapshot(rows) → (ticker,period,sys_time) 멱등 parquet 누적
  - capture(as_of, tickers) → 일일 1회 호출(schtasks 대상)

⛔ forward-only(backfill 불가) — 당장 backtest 불가, 적립 시작 = 옵션가치. 신호계산은 measure 단계.
   ERB = (upLast30days - downLast30days) / numberOfAnalysts (period="0y" 주신호, cross-sectional z).
⛔ revision count 레벨 사이징 금지(수집·검정 전용). push 금지.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SNAP_PARQUET = os.path.join(ROOT, "stock", "data", "erb-pit-snapshots.parquet")

# yfinance eps_revisions 는 공표 즉시 반영(분석가 추정 갱신 = 시장 즉시 가시) → publish lag 0.
VALUE_COLS = (
    "up7", "up30", "down7", "down30", "n_analysts",
    "eps_avg", "eps_low", "eps_high", "growth",
    "eps_current", "eps_7d", "eps_30d", "eps_60d", "eps_90d",
)
PANEL_COLS = ["ticker", "period", "knowable_from", "sys_time", *VALUE_COLS]


def _f(x) -> Optional[float]:
    try:
        v = float(x)
        return v if v == v else None  # NaN guard
    except (TypeError, ValueError):
        return None


def _i(x) -> Optional[float]:
    v = _f(x)
    return None if v is None else float(int(v))


def load_us_universe() -> list[str]:
    """3 sleeve(cyclical/defensive/mega) universe ticker 합집합. parquet/json 혼재 흡수."""
    import json
    base = os.path.join(ROOT, "study-research", "eq_us", "industries")
    tickers: list[str] = []
    for sleeve in ("us_cyclical", "us_defensive", "us_mega_tech"):
        d = os.path.join(base, sleeve, "raw-v3", "data")
        pq = os.path.join(d, "universe.parquet")
        js = os.path.join(d, "universe.json")
        if os.path.exists(pq):
            tickers += pd.read_parquet(pq)["ticker"].tolist()
        elif os.path.exists(js):
            tickers += list(json.loads(open(js, encoding="utf-8").read())["tickers"].keys())
    # 중복 제거(AVGO/AMD/NVDA 가 cyclical·mega 양쪽), 순서 보존
    return list(dict.fromkeys(tickers))


def fetch_erb_live(tickers: list[str], as_of: datetime) -> pd.DataFrame:
    """yfinance eps_revisions/eps_trend/earnings_estimate per ticker → long(ticker×period) raw.

    실패 종목은 skip(부분 커버리지 허용). 0행이면 ValueError(전수 실패 = 네트워크/차단).
    """
    import yfinance as yf
    rows: list[dict] = []
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            rev = tk.eps_revisions
        except Exception:
            continue
        if rev is None or len(rev) == 0:
            continue
        try:
            tr = tk.eps_trend
        except Exception:
            tr = None
        try:
            est = tk.earnings_estimate
        except Exception:
            est = None
        for period in rev.index:
            r = rev.loc[period]
            d: dict = {"ticker": t, "period": str(period)}
            d["up7"] = _i(r.get("upLast7days"))
            d["up30"] = _i(r.get("upLast30days"))
            d["down7"] = _i(r.get("downLast7Days"))
            d["down30"] = _i(r.get("downLast30days"))
            if est is not None and period in est.index:
                e = est.loc[period]
                d["eps_avg"] = _f(e.get("avg"))
                d["eps_low"] = _f(e.get("low"))
                d["eps_high"] = _f(e.get("high"))
                d["n_analysts"] = _i(e.get("numberOfAnalysts"))
                d["growth"] = _f(e.get("growth"))
            if tr is not None and period in tr.index:
                tt = tr.loc[period]
                d["eps_current"] = _f(tt.get("current"))
                d["eps_7d"] = _f(tt.get("7daysAgo"))
                d["eps_30d"] = _f(tt.get("30daysAgo"))
                d["eps_60d"] = _f(tt.get("60daysAgo"))
                d["eps_90d"] = _f(tt.get("90daysAgo"))
            rows.append(d)
    if not rows:
        raise ValueError("ERB live 0 rows (전수 실패 — 네트워크/yfinance 차단 의심)")
    df = pd.DataFrame(rows)
    for c in VALUE_COLS:
        if c not in df.columns:
            df[c] = None
    return df


def build_snapshot_rows(raw: pd.DataFrame, as_of: datetime) -> pd.DataFrame:
    """raw(ticker×period) → bitemporal 행(sys_time=as_of 동결). knowable_from=as_of(revision 즉시 가시)."""
    as_of_ts = pd.Timestamp(as_of)
    if as_of_ts.tz is not None:
        as_of_ts = as_of_ts.tz_convert("UTC").tz_localize(None)
    as_of_ts = as_of_ts.normalize()
    out = raw.copy()
    out["knowable_from"] = as_of_ts
    out["sys_time"] = as_of_ts
    return out[PANEL_COLS].reset_index(drop=True)


def append_snapshot(rows: pd.DataFrame, parquet_path: str = SNAP_PARQUET) -> pd.DataFrame:
    """bitemporal parquet 누적. (ticker,period,sys_time) 멱등 — 같은 vintage 재실행 무중복."""
    if os.path.exists(parquet_path):
        prior = pd.read_parquet(parquet_path)
        merged = pd.concat([prior, rows], ignore_index=True)
    else:
        merged = rows.copy()
    merged = merged.drop_duplicates(subset=["ticker", "period", "sys_time"], keep="last").reset_index(drop=True)
    merged = merged.sort_values(["ticker", "period", "sys_time"]).reset_index(drop=True)
    os.makedirs(os.path.dirname(parquet_path), exist_ok=True)
    merged.to_parquet(parquet_path, index=False)
    return merged


def erb_breadth(up30, down30, n_analysts) -> Optional[float]:
    """ERB 주신호 = (up30 - down30) / n_analysts. n 없으면 (up-down) 합으로 정규화."""
    up = _f(up30) or 0.0
    dn = _f(down30) or 0.0
    n = _f(n_analysts)
    if n and n > 0:
        return (up - dn) / n
    denom = up + dn
    return None if denom == 0 else (up - dn) / denom


def capture(as_of: Optional[datetime] = None, tickers: Optional[list[str]] = None,
            parquet_path: str = SNAP_PARQUET) -> dict:
    """일일 1회 호출: yfinance fresh fetch → as_of vintage 동결 → 누적. (schtasks 대상)

    forward-only: 매 호출이 그날의 revision breadth 를 새 sys_time layer 로 적립.
    과거 layer 불변(append-only) → 미래 라벨 repaint 누수 차단.
    """
    if as_of is None:
        as_of = pd.Timestamp.utcnow().normalize().to_pydatetime()
    if tickers is None:
        tickers = load_us_universe()
    raw = fetch_erb_live(tickers, as_of)
    rows = build_snapshot_rows(raw, as_of)
    merged = append_snapshot(rows, parquet_path)
    n_tk = rows["ticker"].nunique()
    return {
        "as_of": pd.Timestamp(as_of).normalize().date().isoformat(),
        "captured_tickers": int(n_tk),
        "requested_tickers": len(tickers),
        "snapshot_rows": int(len(rows)),
        "total_rows": int(len(merged)),
        "parquet": parquet_path,
    }


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(capture(), ensure_ascii=False, indent=2))
