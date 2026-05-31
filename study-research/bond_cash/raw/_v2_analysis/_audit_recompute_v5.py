"""독립 audit 재계산 — v5 claim 검증 (audit subagent, 2026-06-01).
재현: KW vs ACM corr / HYG regime IS-OOS / sign_prior eligible / 합성 지문 / ADF.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from statsmodels.tsa.stattools import adfuller

DATA = Path(__file__).resolve().parent / "data"

print("="*70)
print("[1] KW vs ACM cross-check 독립 재계산 (B/D축)")
acm = pd.read_parquet(DATA / "ACM.parquet")
kw10 = pd.read_parquet(DATA / "THREEFYTP10.parquet")
common = acm.index.intersection(kw10.index)
a = acm.loc[common, "ACMTP10"].dropna()
k = kw10.loc[common, "THREEFYTP10"].dropna()
j = pd.concat([a, k], axis=1).dropna()
j.columns = ["ACM", "KW"]
print(f"  n={len(j)}  period {j.index.min().date()}~{j.index.max().date()}")
print(f"  level corr = {j.corr().iloc[0,1]:.4f}  (claim 0.8597)")
jd = j.diff(20).dropna()
print(f"  d20 corr   = {jd.corr().iloc[0,1]:.4f}  (claim 0.7241)")
print(f"  mean(ACM-KW)={(j['ACM']-j['KW']).mean():.4f} (claim 0.2553) std={(j['ACM']-j['KW']).std():.4f}")

print("="*70)
print("[2] 합성 지문 검사 (§0) — 역사적 이벤트 + 결측/갭/주말")
hyg = pd.read_parquet(DATA / "YF_HYG.parquet")
col = [c for c in hyg.columns if "adj_close" in c][0]
px = hyg[col].dropna()
ret = px.pct_change()
print(f"  HYG n={len(px)} {px.index.min().date()}~{px.index.max().date()}")
# 2020-03 코로나 급락 실재?
covid = ret.loc["2020-03-01":"2020-03-31"]
print(f"  2020-03 HYG min daily ret = {covid.min():.4f} (코로나 급락 실재 확인)")
# 2022 금리쇼크 (TLT)
tlt = pd.read_parquet(DATA/"YF_TLT.parquet")
tcol=[c for c in tlt.columns if "adj_close" in c][0]
tret = tlt[tcol].pct_change()
y2022 = (tlt[tcol].loc["2022-12-30"]/tlt[tcol].loc["2022-01-03"]-1)
print(f"  2022 TLT full-year return = {y2022:.4f} (금리쇼크 -30%대 실재 확인)")
print(f"  ret kurtosis = {ret.dropna().kurt():.2f} (정규=0; fat tail 실데이터 지문)")
# 주말 공백 / 결측
idx = px.index
wd = pd.Series(idx.weekday)
print(f"  weekday 분포 (0-4 평일만이어야): {sorted(wd.unique())}")
gaps = idx.to_series().diff().dt.days
print(f"  max gap days = {gaps.max()} (휴일/연휴 갭 실재)")

print("="*70)
print("[3] HYG regime walk-forward 독립 재계산 (B/C축 핵심)")
def fetch_re(s):
    df=pd.read_parquet(DATA/f"{s}.parquet"); return df
fred={s:pd.read_parquet(DATA/f"{s}.parquet") for s in ["DGS10","DGS2","BAA10Y"]}
move=pd.read_parquet(DATA/"YF_MOVE.parquet")
p=pd.DataFrame(index=pd.date_range("2007-01-01","2026-05-29",freq="B"))
mc=move["^MOVE_close"].reindex(p.index,method="ffill")
p["MOVE_Z"]=(mc-mc.rolling(252).mean())/mc.rolling(252).std()
kwt=kw10["THREEFYTP10"].reindex(p.index,method="ffill")
p["KW_TP10_d20"]=kwt.diff(20)
acmt=acm["ACMTP10"].reindex(p.index,method="ffill")
p["ACM_TP10_d20"]=acmt.diff(20)
dgs10=fred["DGS10"]["DGS10"].reindex(p.index,method="ffill")
p["DGS10_chg20"]=dgs10.diff(20)
dgs2=fred["DGS2"]["DGS2"].reindex(p.index,method="ffill")
p["T10Y2Y_d20"]=(dgs10-dgs2).diff(20)
baa=fred["BAA10Y"]["BAA10Y"].reindex(p.index,method="ffill")
p["BAA10Y_chg20"]=baa.diff(20)
rate_up=dgs10.diff(126)>0
move_high=mc>mc.rolling(252).median()
p["regime"]=np.where(rate_up&move_high,"rate_up_vol_high",
            np.where(rate_up&~move_high,"rate_up_vol_low",
            np.where(~rate_up&move_high,"rate_down_vol_high","rate_down_vol_low")))
DRV=["MOVE_Z","ACM_TP10_d20","KW_TP10_d20","DGS10_chg20","T10Y2Y_d20","BAA10Y_chg20"]
panel=p.dropna(subset=DRV,how="any")
print(f"  panel n={len(panel)} (claim 4814)")

def wf(x,y,n_splits=5):
    n=len(x);chunk=n//n_splits;res=[]
    for kk in range(1,n_splits):
        te=kk*chunk;ts=te;tend=min(te+chunk,n)
        if tend-ts<30:continue
        ii,_=stats.spearmanr(x[:te],y[:te])
        io,_=stats.spearmanr(x[ts:tend],y[ts:tend])
        if np.isnan(ii) or np.isnan(io):continue
        res.append((ii,io,int(np.sign(ii)==np.sign(io))))
    if not res:return None
    sm=sum(r[2] for r in res)/len(res)
    return len(res),round(sm,3),round(np.mean([r[0] for r in res]),4),round(np.mean([r[1] for r in res]),4)

hyg_px=px
yf60=hyg_px.pct_change(60).shift(-60)
hp=panel[["MOVE_Z","regime"]].join(yf60.rename("y"),how="inner").dropna()
for cell in ["rate_up_vol_high","rate_up_vol_low","rate_down_vol_high","rate_down_vol_low"]:
    cd=hp[hp["regime"]==cell]
    if len(cd)<100:continue
    r=wf(cd["MOVE_Z"].values,cd["y"].values)
    print(f"  {cell:22s} n={len(cd):>5d} splits={r[0]} sign_match={r[1]} IS={r[2]:+.4f} OOS={r[3]:+.4f}")

print("="*70)
print("[4] sign_prior eligible 재계산 (C축 — 전 sub-cluster)")
SUB={"tsy_long":"TLT","tsy_mid":"IEF","tsy_short":"SHY","ig_credit":"LQD","hy_credit":"HYG","cash_tbill":"BIL","tips":"TIP"}
FWDS=[5,20,60]
for sub,etf in SUB.items():
    e=pd.read_parquet(DATA/f"YF_{etf}.parquet")
    ec=[c for c in e.columns if "adj_close" in c][0]
    epx=e[ec]
    elig=0;tot=0
    for d in DRV:
        for f in FWDS:
            yv=epx.pct_change(f).shift(-f)
            tmp=panel[[d]].join(yv.rename("y"),how="inner").dropna()
            if len(tmp)<200:continue
            r=wf(tmp[d].values,tmp["y"].values)
            if r is None:continue
            tot+=1
            if r[0]>=3 and r[1]>=0.5:elig+=1
    print(f"  {sub:12s} eligible={elig}/{tot}")

print("="*70)
print("[5] ADF 단위근 — driver stationary 확인 (B/§1.7)")
for d in DRV:
    s=panel[d].dropna()
    pv=adfuller(s,regression="c",autolag="AIC")[1]
    print(f"  {d:16s} ADF p={pv:.2e}  {'I(0) stationary' if pv<0.05 else 'I(1) 의심!'}")
# KW level ADF (D축: KW 도 nonstationary level 인지)
print(f"  KW_TP10 level    ADF p={adfuller(k.values,regression='c',autolag='AIC')[1]:.2e}")
print(f"  ACM_TP10 level   ADF p={adfuller(a.values,regression='c',autolag='AIC')[1]:.2e}")
print("[DONE]")
