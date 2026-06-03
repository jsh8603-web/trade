# -*- coding: utf-8 -*-
"""exposure_card.py — §M.7 cross-sectional peer-relative z-score (us_mega_tech). basket 11종."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
import numpy as np, pandas as pd
DATA = Path("data")
px = pd.read_parquet(DATA/"prices.parquet"); px.index = pd.to_datetime(px.index)
uni = json.loads((DATA/"universe.json").read_text(encoding="utf-8")); tags = uni["tickers"]
pxm = px.resample("ME").last()
vol_60 = (px.pct_change().rolling(60).std()*np.sqrt(252)).resample("ME").last().iloc[-1]
mom_6 = (pxm/pxm.shift(6)-1).iloc[-1]
mom_12_1 = (pxm.shift(1)/pxm.shift(12)-1).iloc[-1]
def z(s): return (s - s.mean())/s.std(ddof=1)
card = pd.DataFrame({"sub": pd.Series(tags),
    "vol_60_z": z(vol_60), "mom_6_z": z(mom_6), "mom_12_1_z": z(mom_12_1)}).dropna(subset=["vol_60_z"])
card = card.sort_values("vol_60_z")  # ★저변동성 = compounder quality (vol_60 IC +0.241 강)
out = []
for t, r in card.iterrows():
    out.append(dict(ticker=t, sub=r["sub"], vol_60_z=round(float(r["vol_60_z"]),3),
                    mom_6_z=round(float(r["mom_6_z"]),3) if not np.isnan(r["mom_6_z"]) else None,
                    mom_12_1_z=round(float(r["mom_12_1_z"]),3) if not np.isnan(r["mom_12_1_z"]) else None))
Path("exposure-card-v3.json").write_text(json.dumps(
    {"as_of": str(pxm.index[-1].date()), "n_universe": len(out),
     "standardization": "peer-relative cross-sectional z (Mag7 basket 11종, local). ★n=11 small-basket = z 안정성 낮음 hedge.",
     "signal_sign_note": "★compounder: vol_60 IC +0.241 강(저변동성 mega-cap quality = AAPL/MSFT 안정성장). 저vol_z 상위 = forward 강. momentum 약 양(growth persistence). valuation=PBR 약 value(§10).",
     "note": "valuation(PER/PBR/capex) = measure_valuation §10(EDGAR). supervisor 조립은 dispatch 밖.",
     "cards": out}, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"as_of {pxm.index[-1].date()}, n={len(out)} (저변동성 상위 = compounder quality)")
print(f"{'ticker':<7}{'sub':<14}{'vol_z':>8}{'mom6_z':>8}{'mom12_z':>9}")
for c in out:
    print(f"{c['ticker']:<7}{c['sub']:<14}{c['vol_60_z']:>8.2f}{(c['mom_6_z'] or 0):>8.2f}{(c['mom_12_1_z'] or 0):>9.2f}")
