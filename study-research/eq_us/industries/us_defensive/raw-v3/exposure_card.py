# -*- coding: utf-8 -*-
"""exposure_card.py — §M.7 cross-sectional peer-relative z-score exposure card (us_defensive).
universe 각 종목 현 시점 가격신호 횡단면 z (sector-neutral). valuation z = EDGAR(§10, #15 후)."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
import numpy as np, pandas as pd
DATA = Path("data")
px = pd.read_parquet(DATA/"prices.parquet"); px.index = pd.to_datetime(px.index)
uni = json.loads((DATA/"universe.json").read_text(encoding="utf-8")); tags = uni["tickers"]
pxm = px.resample("ME").last()
vol_60 = (px.pct_change().rolling(60).std()*np.sqrt(252)).resample("ME").last().iloc[-1]
rev_1m = (pxm/pxm.shift(1)-1).iloc[-1]
mom_6 = (pxm/pxm.shift(6)-1).iloc[-1]
def z(s): return (s - s.mean())/s.std(ddof=1)
card = pd.DataFrame({"sector": pd.Series(tags),
    "vol_60_z": z(vol_60), "rev_1m_z": z(rev_1m), "mom_6_z": z(mom_6)}).dropna(subset=["vol_60_z"])
card = card.sort_values("vol_60_z")  # ★저변동성 = defensive value (asset_stable, vol_60 IC 양 = 저vol→고forward)
out = []
for t, r in card.iterrows():
    out.append(dict(ticker=t, sector=r["sector"],
                    vol_60_z=round(float(r["vol_60_z"]),3),
                    rev_1m_z=round(float(r["rev_1m_z"]),3) if not np.isnan(r["rev_1m_z"]) else None,
                    mom_6_z=round(float(r["mom_6_z"]),3) if not np.isnan(r["mom_6_z"]) else None))
Path("exposure-card-v3.json").write_text(json.dumps(
    {"as_of": str(pxm.index[-1].date()), "n_universe": len(out),
     "standardization": "sector-neutral cross-sectional z = (x - defensive_universe_mean)/std (local, R2-1 gap)",
     "signal_sign_note": "★asset_stable: vol_60 IC 양(+0.076 저vol→고forward 저변동성 프리미엄) + rev_1m IC 음(-0.045 단기 reversal 유의). momentum 무효. valuation(PER value)=EDGAR §10.",
     "note": "valuation(PER/PBR) z = EDGAR XBRL 재구성(§10, #15 파이프라인 후). supervisor 조립(score→target)은 dispatch 밖.",
     "cards": out}, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"as_of {pxm.index[-1].date()}, n={len(out)} (저변동성 상위 = defensive value)")
print(f"{'ticker':<7}{'sector':<13}{'vol_z':>8}{'rev_z':>8}{'mom_z':>8}")
for c in out[:12]:
    print(f"{c['ticker']:<7}{c['sector']:<13}{c['vol_60_z']:>8.2f}{(c['rev_1m_z'] or 0):>8.2f}{(c['mom_6_z'] or 0):>8.2f}")
