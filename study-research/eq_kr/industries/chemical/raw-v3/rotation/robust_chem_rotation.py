# -*- coding: utf-8 -*-
"""robust_chem_rotation.py — 화학 rotation 신호 robustness (non-overlap + placebo + leave-one-year)."""
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np, pandas as pd
from scipy import stats
ROOT=Path(__file__).resolve().parent; CHEM=ROOT.parent.parent; DATA=ROOT/"data"

px=pd.read_parquet(CHEM/"raw-v3"/"data"/"prices.parquet"); px.index=pd.to_datetime(px.index)
ind_ret=px.resample("ME").last().pct_change().mean(axis=1).dropna()
cyc=pd.read_parquet(DATA/"chem_rotation_cycle.parquet"); cyc.index=pd.to_datetime(cyc.index)
cycm=cyc.resample("ME").last()
z=lambda s:(s-s.mean())/s.std()
naph_yoy=cycm["wti_naphtha"]/cycm["wti_naphtha"].shift(12)-1
fxi_yoy=cycm["china_fxi"]/cycm["china_fxi"].shift(12)-1
mchi_yoy=cycm["china_mchi"]/cycm["china_mchi"].shift(12)-1
spread=z(fxi_yoy)-z(naph_yoy)
sigs={"china_mchi_yoy":(mchi_yoy,"양"),"china_fxi_yoy":(fxi_yoy,"양"),
      "spread_demand_minus_cost":(spread,"양"),"naphtha_yoy":(naph_yoy,"음")}
h=3
def fwd_h(r,h): return r.shift(-1).rolling(h).sum().shift(-(h-1))
out={}
for sn,(sig,pr) in sigs.items():
    fwd=fwd_h(ind_ret,h)
    df=pd.concat([sig.rename("s"),fwd.rename("f")],axis=1).dropna()
    rho_full=stats.spearmanr(df["s"],df["f"])[0]
    # non-overlap stride=3
    sub=df.iloc[::3]
    rho_no=stats.spearmanr(sub["s"],sub["f"])[0] if len(sub)>=8 else np.nan
    # placebo: shuffle signal 500x → p
    rng=np.random.default_rng(7); cnt=0; B=500
    for _ in range(B):
        sh=rng.permutation(df["s"].values)
        if abs(stats.spearmanr(sh,df["f"])[0])>=abs(rho_full): cnt+=1
    placebo_p=(cnt+1)/(B+1)
    # leave-one-year
    loy={}
    for yr in sorted(set(df.index.year)):
        d2=df[df.index.year!=yr]
        loy[int(yr)]=round(float(stats.spearmanr(d2["s"],d2["f"])[0]),3)
    loy_sign_consistent=all(np.sign(v)==np.sign(rho_full) for v in loy.values())
    out[sn]={"rho_full":round(float(rho_full),4),"rho_nonoverlap_s3":round(float(rho_no),4) if not np.isnan(rho_no) else None,
             "nonoverlap_sign_hold":bool(not np.isnan(rho_no) and np.sign(rho_no)==np.sign(rho_full)),
             "placebo_p":round(placebo_p,4),"loy":loy,"loy_sign_consistent":bool(loy_sign_consistent),"prior":pr}
(ROOT/"validation-chem-rotation-robust-v1.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"{'signal':<30}{'rho':>8}{'nonovlp':>9}{'placebo_p':>10}{'LOY_consist':>12}")
for k,v in out.items():
    print(f"{k:<30}{v['rho_full']:>+8.3f}{(v['rho_nonoverlap_s3'] or 0):>+9.3f}{v['placebo_p']:>10.4f}{str(v['loy_sign_consistent']):>12}")
