import sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
import numpy as np,pandas as pd
from scipy import stats
from pathlib import Path
ROOT=Path(__file__).resolve().parent;CHEM=ROOT.parent.parent;DATA=ROOT/"data"
px=pd.read_parquet(CHEM/"raw-v3"/"data"/"prices.parquet");px.index=pd.to_datetime(px.index)
pxm=px.resample("ME").last();ind=pxm.pct_change().mean(axis=1).dropna()
em=pd.read_parquet(DATA/"chem_rotation_ext.parquet");em.index=pd.to_datetime(em.index);em=em.resample("ME").last()
z=lambda s:(s-s.mean())/s.std()
mom3=z(pxm.pct_change(3).mean(axis=1))
common=pd.concat([z(em["usdkrw"].pct_change(3)).rename("u"),z(em["brent"].pct_change(3)).rename("b")],axis=1)
df0=pd.concat([mom3.rename("y"),common],axis=1).dropna()
X=np.column_stack([np.ones(len(df0))]+[df0[c].values for c in ["u","b"]]);b=np.linalg.lstsq(X,df0["y"].values,rcond=None)[0]
mom3r=pd.Series(df0["y"].values-X@b,index=df0.index)
fwd=ind.shift(-1).rolling(3).sum().shift(-2)
df=pd.concat([mom3r.rename("s"),fwd.rename("f")],axis=1).dropna()
rho=stats.spearmanr(df["s"],df["f"])[0]
sub=df.iloc[::3];rho_no=stats.spearmanr(sub["s"],sub["f"])[0]
rng=np.random.default_rng(7);c=0
for _ in range(500):
    if abs(stats.spearmanr(rng.permutation(df["s"].values),df["f"])[0])>=abs(rho):c+=1
placebo=(c+1)/501
loy={int(y):round(float(stats.spearmanr(df[df.index.year!=y]["s"],df[df.index.year!=y]["f"])[0]),3) for y in sorted(set(df.index.year))}
loyc=all(np.sign(v)==np.sign(rho) for v in loy.values())
print(f"mom_3_residualized y60: rho={rho:+.3f} non-ovlp(s3)={rho_no:+.3f} placebo_p={placebo:.4f} LOY_consistent={loyc}")
print(f"  LOY={loy}")
