# -*- coding: utf-8 -*-
"""exposure_card.py — §M.7 cross-sectional peer-relative z-score exposure card. battery 미러.
universe 각 종목의 현 시점 momentum 지표 횡단면 z-score (sector-neutral 표준화 = subagent 담당).
※ valuation(PBR/PER) z-score = measure_valuation.py(DART 재구성)에서 별도 산출. 본 파일 = 가격신호 z."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
import numpy as np, pandas as pd
DATA = Path("data")
px = pd.read_parquet(DATA/"prices.parquet"); px.index = pd.to_datetime(px.index)
uni = pd.read_parquet(DATA/"universe.parquet"); uni = uni[uni["pass_floor"]].set_index("Code")
pxm = px.resample("ME").last()
# 최신 시점 횡단면 신호
mom_6 = (pxm/pxm.shift(6)-1).iloc[-1]
mom_12_1 = (pxm.shift(1)/pxm.shift(12)-1).iloc[-1]
ret_d = px.pct_change(); vol_60 = (ret_d.rolling(60).std()*np.sqrt(252)).resample("ME").last().iloc[-1]
def z(s): return (s - s.mean())/s.std(ddof=1)
card = pd.DataFrame({
    "name": uni["Name"], "marcap": uni["Marcap"],
    "mom_6_z": z(mom_6), "mom_12_1_z": z(mom_12_1), "vol_60_z": z(vol_60),
}).dropna(subset=["mom_6_z"]).sort_values("mom_6_z", ascending=False)
card_out = []
for code, r in card.iterrows():
    card_out.append(dict(ticker=code, name=r["name"], marcap_won=int(r["marcap"]),
                         mom_6_z=round(float(r["mom_6_z"]),3),
                         mom_12_1_z=round(float(r["mom_12_1_z"]),3) if not np.isnan(r["mom_12_1_z"]) else None,
                         vol_60_z=round(float(r["vol_60_z"]),3) if not np.isnan(r["vol_60_z"]) else None))
Path("exposure-card-v3.json").write_text(json.dumps(
    {"as_of": str(pxm.index[-1].date()), "n_universe": len(card_out),
     "standardization": "sector-neutral cross-sectional z = (x - semi_universe_mean)/std (local, R2-1 gap 메움)",
     "signal_sign_note": "★반도체 momentum forward IC = 음(contrarian/cyclical reversal). 따라서 mom_6_z 상위 = forward 약(reversal) → selection 은 supervisor 가 IC 부호 반영(저 mom_z overweight).",
     "note": "valuation(PBR/PER) z-score = measure_valuation.py(DART). supervisor 조립(score→target weight)은 dispatch 밖.",
     "cards": card_out}, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"as_of {pxm.index[-1].date()}, n={len(card_out)}")
print(f"{'ticker':<8}{'name':<14}{'mom_6_z':>9}{'mom12_1_z':>11}{'vol_z':>8}")
for c in card_out[:12]:
    print(f"{c['ticker']:<8}{c['name']:<14}{c['mom_6_z']:>9.2f}{(c['mom_12_1_z'] or 0):>11.2f}{(c['vol_60_z'] or 0):>8.2f}")
