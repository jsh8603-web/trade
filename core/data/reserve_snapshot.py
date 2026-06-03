"""core/data/reserve_snapshot.py — 길1 forward-OOS reserve vintage 동결 수집기 (additive).

배경(2026-06-03 btn-Inv, Phase 0a GREEN + DEFER 결정):
  거래소 reserve→fwd-vol 신호는 라이브 epoch(2022-11+)서 GREEN(코어 robust). 단 승격 binding
  조건 = PIT/vintage look-ahead 해소(provider 가 거래소 주소라벨을 소급 재배정 → 백테스트가
  '오늘 라벨'로 과거를 칠함 = look-ahead). 비싼 electrs 재구성(길2) 대신 audit 처방 길1 =
  '오늘부터 무료 CM Community 피드를 as-of 스냅샷으로 bitemporal 적재 → 미래분 forward-OOS 재확증'.

역할 분리(재발명 0):
  - 기존 collect_coinmetrics_v2.py  → coinmetrics-btc-community.csv 갱신(가변·최신-vintage raw)
  - 본 모듈                         → 그 tail 을 sys_time=as_of 로 동결, bitemporal parquet 누적
  - core/data/pit_query.py PitPanel → 적재분 as_of 조회(0수정 차용, 본 모듈이 schema 만 맞춤)

PIT schema(pit_query.py 계약):
  firm / date(=effective_from) / knowable_from / sys_time + value(reserve·flow)
  · knowable_from = date + PUBLISH_LAG (CM T+1 발행 보수적)
  · sys_time      = as_of (vintage 캡처 시각) — 매일 새 layer, 과거 layer 불변
  · forward-OOS 검정 = sys_time ≤ as_of 행만으로 신호 계산 → 미래 라벨 repaint 누수 차단

⛔ reserve 레벨 사이징 금지(수집·검정 전용). pit_query.py/as_of.py 0수정. push 금지.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CM_CSV = os.path.join(ROOT, "study-research", "crypto", "raw", "data", "coinmetrics-btc-community.csv")
SNAP_PARQUET = os.path.join(ROOT, "study-research", "crypto", "raw", "data", "reserve-pit-snapshots.parquet")

PUBLISH_LAG = pd.Timedelta(days=1)   # CM Community T+1 발행 보수적 가정
TAIL_DAYS = 400                   # 매 캡처 시 동결할 최근 관측 window
FIRM = "BTC"                      # venue-agnostic 글로벌 집계(scope guard: Upbit dated PoR pack 없음)
VALUE_COLS = ("reserve", "flow_in", "flow_out", "netflow")
PANEL_COLS = ["firm", "date", "effective_from", "knowable_from", "sys_time", *VALUE_COLS]


CM_API = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
CM_METRICS = ("SplyExNtv", "FlowInExNtv", "FlowOutExNtv")


def fetch_cm_live(tail_days: int = TAIL_DAYS, asset: str = "btc") -> pd.DataFrame:
    """CM Community API 익명티어로 reserve/flow 최근 tail 직접 fetch(daily 갱신용).

    CSV 의존 제거 — daily job 이 매번 fresh 관측을 가져온다. -status(flash/final) 정정은
    later sys_time vintage 로 자연 포착(append_snapshot 멱등키=firm/date/sys_time).
    실패 시 ValueError → capture() 가 CSV fallback.
    """
    import requests
    start = (pd.Timestamp.utcnow().normalize() - pd.Timedelta(days=tail_days + 5)).strftime("%Y-%m-%d")
    s = requests.Session()
    s.headers.update({"Accept": "application/json", "User-Agent": "Mozilla/5.0 (study-Inv-reserve-snap)"})
    merged: dict = {}
    for m in CM_METRICS:
        token = None
        for _ in range(60):
            params = {"assets": asset, "metrics": m, "frequency": "1d", "page_size": 1000, "start_time": start}
            if token:
                params["next_page_token"] = token
            r = s.get(CM_API, params=params, timeout=60)
            if r.status_code != 200:
                raise ValueError(f"CM live {m} HTTP {r.status_code}: {r.text[:80]}")
            j = r.json()
            for d in j.get("data", []):
                merged.setdefault(d["time"], {})[m] = d.get(m)
            token = j.get("next_page_token")
            if not token:
                break
    if not merged:
        raise ValueError("CM live 0 rows")
    df = pd.DataFrame([{"time": t, **v} for t, v in sorted(merged.items())])
    df["date"] = pd.to_datetime(df["time"], format="ISO8601", errors="coerce", utc=True).dt.tz_localize(None).dt.normalize()
    for c in CM_METRICS:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    df = df.dropna(subset=["date", "SplyExNtv"]).sort_values("date").drop_duplicates("date").tail(tail_days)
    out = pd.DataFrame({"date": df["date"].values, "reserve": df["SplyExNtv"].values,
                        "flow_in": df["FlowInExNtv"].values, "flow_out": df["FlowOutExNtv"].values})
    out["netflow"] = out["flow_in"] - out["flow_out"]
    return out.reset_index(drop=True)


def _load_cm_tail(csv_path: str = CM_CSV, tail_days: int = TAIL_DAYS) -> pd.DataFrame:
    """CM Community CSV 에서 reserve/flow 최근 tail 로드(최신-vintage raw)."""
    df = pd.read_csv(csv_path, low_memory=False, usecols=["time", "SplyExNtv", "FlowInExNtv", "FlowOutExNtv"])
    df["date"] = pd.to_datetime(df["time"], format="ISO8601", errors="coerce", utc=True).dt.tz_localize(None).dt.normalize()
    for c in ("SplyExNtv", "FlowInExNtv", "FlowOutExNtv"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["date", "SplyExNtv"]).sort_values("date").drop_duplicates("date")
    df = df.tail(tail_days).reset_index(drop=True)
    out = pd.DataFrame({
        "date": df["date"],
        "reserve": df["SplyExNtv"].values,
        "flow_in": df["FlowInExNtv"].values,
        "flow_out": df["FlowOutExNtv"].values,
    })
    out["netflow"] = out["flow_in"] - out["flow_out"]
    return out


def build_snapshot_rows(tail: pd.DataFrame, as_of: datetime, firm: str = FIRM) -> pd.DataFrame:
    """raw tail → bitemporal 행(sys_time=as_of 동결). pit_query schema 정합."""
    as_of_ts = pd.Timestamp(as_of)
    if as_of_ts.tz is not None:
        as_of_ts = as_of_ts.tz_convert("UTC").tz_localize(None)
    as_of_ts = as_of_ts.normalize()
    dates = pd.to_datetime(tail["date"])
    if dates.dt.tz is not None:
        dates = dates.dt.tz_convert("UTC").dt.tz_localize(None)
    dates = dates.reset_index(drop=True)
    rows = pd.DataFrame({
        "firm": firm,
        "date": dates,
        "effective_from": dates,
        "knowable_from": dates + PUBLISH_LAG,
        "sys_time": as_of_ts,
    })
    for c in VALUE_COLS:
        rows[c] = tail[c].values
    # knowable_from 이 as_of 를 넘는(미래 관측) 행 = 아직 알 수 없음 → 제외
    rows = rows[rows["knowable_from"] <= as_of_ts].reset_index(drop=True)
    return rows[PANEL_COLS]


def append_snapshot(rows: pd.DataFrame, parquet_path: str = SNAP_PARQUET) -> pd.DataFrame:
    """bitemporal parquet 누적. (firm,date,sys_time) 멱등 — 같은 vintage 재실행 무중복."""
    if os.path.exists(parquet_path):
        prior = pd.read_parquet(parquet_path)
        merged = pd.concat([prior, rows], ignore_index=True)
    else:
        merged = rows.copy()
    merged = merged.drop_duplicates(subset=["firm", "date", "sys_time"], keep="last").reset_index(drop=True)
    merged = merged.sort_values(["firm", "date", "sys_time"]).reset_index(drop=True)
    merged.to_parquet(parquet_path, index=False)
    return merged


def capture(as_of: Optional[datetime] = None, csv_path: str = CM_CSV,
            parquet_path: str = SNAP_PARQUET, tail_days: int = TAIL_DAYS,
            live: bool = True) -> dict:
    """일일 1회 호출: fresh fetch(live) tail → as_of vintage 동결 → 누적. (schtasks 대상)

    live=True: CM API 직접 fetch(daily 성장). 실패 시 CSV fallback. live=False: CSV only.
    """
    if as_of is None:
        as_of = pd.Timestamp.utcnow().normalize().to_pydatetime()
    src = "csv"
    if live:
        try:
            tail = fetch_cm_live(tail_days); src = "live"
        except Exception as e:
            print(f"[reserve_snapshot] live fetch 실패({e}) → CSV fallback")
            tail = _load_cm_tail(csv_path, tail_days)
    else:
        tail = _load_cm_tail(csv_path, tail_days)
    rows = build_snapshot_rows(tail, as_of)
    merged = append_snapshot(rows, parquet_path)
    n_vintages = merged["sys_time"].nunique()
    return {
        "as_of": pd.Timestamp(as_of).date().isoformat(),
        "source": src,
        "captured_rows": len(rows),
        "panel_total_rows": len(merged),
        "distinct_vintages": int(n_vintages),
        "date_span": f"{merged['date'].min().date()}~{merged['date'].max().date()}",
    }


# ---------------------------------------------------------------------------
# self-test — vintage 격리(forward-OOS 핵심): 늦은 sys_time revision 이 이른 as_of 조회에 누수 X
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import tempfile, sys
    sys.path.insert(0, os.path.join(ROOT))

    # CLI: `python -m core.data.reserve_snapshot capture` = daily 적재(schtasks 대상)
    if len(sys.argv) > 1 and sys.argv[1] == "capture":
        import json
        print(json.dumps(capture(live=True), ensure_ascii=False))
        sys.exit(0)

    from core.data.pit_query import PitPanel  # 0수정 차용

    tmp = os.path.join(tempfile.gettempdir(), "_reserve_snap_selftest.parquet")
    if os.path.exists(tmp):
        os.remove(tmp)

    # 합성 raw: date d0..d2, reserve 값
    base = pd.DataFrame({
        "date": pd.to_datetime(["2026-06-01", "2026-06-02", "2026-06-03"]),
        "reserve": [100.0, 101.0, 102.0], "flow_in": [5, 6, 7], "flow_out": [4, 4, 4],
    })
    base["netflow"] = base["flow_in"] - base["flow_out"]

    # vintage1: as_of=06-04 (d0..d2 knowable, T+1)
    r1 = build_snapshot_rows(base, datetime(2026, 6, 4))
    append_snapshot(r1, tmp)
    # vintage2: as_of=06-10, d1 reserve 가 소급 repaint(101→999, 라벨 재배정 모사)
    rev = base.copy(); rev.loc[1, "reserve"] = 999.0
    r2 = build_snapshot_rows(rev, datetime(2026, 6, 10))
    merged = append_snapshot(r2, tmp)

    panel = PitPanel(merged)
    # as_of=06-05 조회: vintage2(sys_time=06-10) 미래 → d1 = 원본 101 이어야(repaint 누수 X)
    v_early = panel.query("BTC", datetime(2026, 6, 2), datetime(2026, 6, 5))
    assert v_early is not None and abs(v_early["reserve"] - 101.0) < 1e-9, ("vintage 누수!", v_early)
    print(f"1) as_of=06-05 d=06-02 reserve={v_early['reserve']} (원본 101, repaint 차단) OK")
    # as_of=06-12 조회: vintage2 가시 → d1 = repaint 999(그때 알던 최신값)
    v_late = panel.query("BTC", datetime(2026, 6, 2), datetime(2026, 6, 12))
    assert v_late is not None and abs(v_late["reserve"] - 999.0) < 1e-9, ("최신 vintage 미반영", v_late)
    print(f"2) as_of=06-12 d=06-02 reserve={v_late['reserve']} (repaint 999, 최신 vintage) OK")
    # knowable_from 게이트: as_of=06-01 엔 d=06-03(knowable 06-04) 미가시
    v_future = panel.query("BTC", datetime(2026, 6, 3), datetime(2026, 6, 1))
    assert v_future is None, ("미래 관측 누수", v_future)
    print("3) as_of=06-01 d=06-03(knowable 06-04) 미가시(미래 관측 차단) OK")
    # 멱등: 같은 vintage 재append 무중복
    n_before = len(merged); merged2 = append_snapshot(r2, tmp)
    assert len(merged2) == n_before, ("멱등 위반", n_before, len(merged2))
    print(f"4) 같은 vintage 재append 멱등(rows={len(merged2)} 불변) OK")
    os.remove(tmp)
    print("reserve_snapshot (vintage 격리 + knowable 게이트 + 멱등) self-test PASS")
