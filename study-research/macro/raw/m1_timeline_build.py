"""m1_timeline_build.py — M1 배포용 거시 timeline: 기간별 거시 지표 요약(실데이터).

main 조정: M1 = 배포용 공통 timeline(기간별 거시 이벤트·지표 요약). M2가 전 종목 세션에 배포 →
M3에서 각 종목이 거시 연관 분석. 본 스크립트 = 분기별 *실데이터* 지표 레벨/변화 + regime 라벨(proxy).
이벤트 주석은 timeline.md 에서 사람이 박제(팩트). ⛔합성無 data/historical 실 일별.

라벨(Investment Clock proxy, 가용 데이터): rate방향(us10y Δ분기) × equity방향(sp500 분기수익)
 → rate↑equity↓=긴축/리스크오프 / rate↑equity↑=Recovery / rate↓equity↑=Reflation/Recovery / rate↓equity↓=리스크오프.
 ⚠️ 진짜 Investment Clock 은 CPI·성장 펀더멘털 필요(collector 이연) — 본 라벨은 proxy.
"""
from __future__ import annotations
import json, sys
import numpy as np
import pandas as pd

RAW = ["sp500", "nasdaq", "dxy", "gold", "oil", "us10y"]


def load_px():
    frames = []
    for yr in ("2022", "2023", "2024"):
        d = json.load(open(f"data/historical_{yr}/macro_yahoo_raw.json", encoding="utf-8"))
        cols = {k: pd.Series({r["date"]: r.get("close", r.get("open")) for r in d.get(k, [])}) for k in RAW}
        frames.append(pd.DataFrame(cols))
    px = pd.concat(frames).sort_index()
    px = px[~px.index.duplicated(keep="last")]; px.index = pd.to_datetime(px.index)
    return px.dropna()


def regime_label(d_rate, eq_ret):
    up = d_rate > 0.05   # 분기 금리 +5bp 이상 = rate-up
    eqp = eq_ret > 0
    if up and not eqp: return "긴축/리스크오프(Overheat→Stagflation懸)"
    if up and eqp:     return "Recovery(성장>긴축)"
    if not up and eqp: return "Reflation/Recovery(완화+성장)"
    return "리스크오프/침체懸(완화+약세)"


def main():
    px = load_px()
    q = px.resample("QE")
    rows = []
    prev = None
    for ts, g in q:
        if len(g) < 5: continue
        first, last = g.iloc[0], g.iloc[-1]
        d_rate = float(last["us10y"] - first["us10y"])
        eq_ret = float(last["sp500"] / first["sp500"] - 1)
        nq_ret = float(last["nasdaq"] / first["nasdaq"] - 1)
        dxy_ret = float(last["dxy"] / first["dxy"] - 1)
        gold_ret = float(last["gold"] / first["gold"] - 1)
        oil_ret = float(last["oil"] / first["oil"] - 1)
        rows.append({
            "분기": f"{ts.year}Q{ts.quarter}",
            "us10y(말)": round(float(last["us10y"]), 2),
            "Δus10y(bp)": round(d_rate * 100, 0),
            "DXY(말)": round(float(last["dxy"]), 1),
            "sp500%": round(eq_ret * 100, 1),
            "nasdaq%": round(nq_ret * 100, 1),
            "dxy%": round(dxy_ret * 100, 1),
            "gold%": round(gold_ret * 100, 1),
            "oil%": round(oil_ret * 100, 1),
            "regime(proxy)": regime_label(d_rate, eq_ret),
        })
    df = pd.DataFrame(rows)
    print(f"M1 배포용 거시 timeline | {px.index[0].date()}~{px.index[-1].date()}, 분기 {len(df)}개 (실데이터)")
    print(df.to_string(index=False))
    df.to_csv("study-research/macro/raw/m1-timeline.csv", index=False, encoding="utf-8-sig")
    print("\nsaved raw/m1-timeline.csv")


if __name__ == "__main__":
    main()
