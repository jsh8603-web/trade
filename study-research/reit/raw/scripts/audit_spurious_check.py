"""
audit_spurious_check.py — INDEPENDENT audit re-verification (opus audit subagent)
B축 spurious 검정 + §5 level vs return corr + §3 reproduce + walk-forward OOS.
Fresh fetch yfinance VNQ/SPY/^GSPC + FRED CPI. self-audit 신뢰 X.
"""
import numpy as np, pandas as pd, yfinance as yf, urllib.request
from io import StringIO
from scipy import stats
from statsmodels.tsa.stattools import adfuller, kpss

def fred(sid):
    url=f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
    req=urllib.request.Request(url,headers={"User-Agent":"audit jsh8603@gmail.com"})
    t=urllib.request.urlopen(req,timeout=30).read().decode()
    df=pd.read_csv(StringIO(t)); c=df.columns
    df[c[0]]=pd.to_datetime(df[c[0]]); df=df.set_index(c[0])
    return pd.to_numeric(df[c[1]],errors="coerce").rename(sid).dropna()

def nw_corr(x,y,lag=None):
    n=len(x)
    if lag is None: lag=max(int(np.floor(4*(n/100)**(2/9))),1)
    xm=x-x.mean(); ym=y-y.mean()
    cov=(xm*ym).mean(); vx=(xm**2).mean(); vy=(ym**2).mean()
    r=cov/np.sqrt(vx*vy)
    u=xm*ym-cov; vh=(u**2).mean()
    for l in range(1,lag+1):
        w=1-l/(lag+1); vh+=2*w*(u[l:]*u[:-l]).mean()
    se=np.sqrt(max(vh/n,1e-12))/np.sqrt(vx*vy)
    t=r/se if se>0 else np.nan
    p=2*(1-stats.norm.cdf(abs(t))) if np.isfinite(t) else np.nan
    return r,se,t,p

print("=== INDEPENDENT AUDIT: fresh fetch ===",flush=True)
# Use SPY (not ^GSPC) as independent cross-check ticker for stock proxy
px=yf.download(["VNQ","SPY","^GSPC"],start="2004-09-01",end="2026-05-31",interval="1mo",auto_adjust=True,progress=False)["Close"]
px=px.dropna(how="any")
print(f"levels: n={len(px)}, range={px.index.min().date()}~{px.index.max().date()}",flush=True)
ret=np.log(px).diff().dropna()
print(f"log returns: n={len(ret)}",flush=True)

print("\n=== B축 STATIONARITY (ADF / KPSS) ===",flush=True)
for col in ["VNQ","^GSPC","SPY"]:
    lv=px[col].values; rt=ret[col].values
    adf_lv=adfuller(lv,autolag="AIC")[1]; adf_rt=adfuller(rt,autolag="AIC")[1]
    kp_lv=kpss(lv,regression="c",nlags="auto")[1]; kp_rt=kpss(rt,regression="c",nlags="auto")[1]
    print(f"{col}: LEVEL adf_p={adf_lv:.3f} kpss_p={kp_lv:.3f} | RETURN adf_p={adf_rt:.4f} kpss_p={kp_rt:.3f}",flush=True)
print("(adf_p>0.05 = unit root/nonstationary; kpss_p<0.05 = nonstationary)",flush=True)

print("\n=== §5 LEVEL corr vs RETURN corr (spurious test) ===",flush=True)
# LEVEL-on-LEVEL (spurious candidate)
rl,_,tl,pl=nw_corr(px["VNQ"].values,px["^GSPC"].values)
print(f"LEVEL VNQ~^GSPC price: r={rl:.3f} NW t={tl:.2f} p={pl:.2e}",flush=True)
# RETURN corr (what the session script actually used)
rr,_,tr,pr=nw_corr(ret["VNQ"].values,ret["^GSPC"].values)
print(f"RETURN VNQ~^GSPC logret: r={rr:.3f} NW t={tr:.2f} p={pr:.2e} (session reported 0.746)",flush=True)
# SPY cross-check
rr2,_,tr2,pr2=nw_corr(ret["VNQ"].values,ret["SPY"].values)
print(f"RETURN VNQ~SPY logret: r={rr2:.3f} NW t={tr2:.2f} p={pr2:.2e} (independent ticker)",flush=True)

print("\n=== §5 regime split reproduce (high/low vol) ===",flush=True)
d5=ret[["VNQ","^GSPC"]].copy()
vol12=d5["VNQ"].rolling(12).std(); med=vol12.dropna().median()
hi=d5[(vol12>med).fillna(False)]; lo=d5[(~(vol12>med)&vol12.notna())]
for lab,sub in [("full",d5),("high_vol",hi),("low_vol",lo)]:
    r,_,t,p=nw_corr(sub["VNQ"].values,sub["^GSPC"].values)
    print(f"{lab}: r={r:.3f} t={t:.2f} p={p:.2e} n={len(sub)}",flush=True)

print("\n=== §5 walk-forward / half-split OOS (return corr) ===",flush=True)
half=len(d5)//2
for lab,sub in [("1st_half",d5.iloc[:half]),("2nd_half",d5.iloc[half:])]:
    r,_,t,p=nw_corr(sub["VNQ"].values,sub["^GSPC"].values)
    print(f"{lab}: r={r:.3f} t={t:.2f} p={p:.2e} n={len(sub)} range={sub.index.min().date()}~{sub.index.max().date()}",flush=True)
# rolling 36m corr stability
roll=d5["VNQ"].rolling(36).corr(d5["^GSPC"]).dropna()
print(f"rolling 36m return-corr: min={roll.min():.3f} max={roll.max():.3f} mean={roll.mean():.3f} (all positive? {(roll>0).all()})",flush=True)

print("\n=== §3 VNQ-CPI reproduce ===",flush=True)
cpi=fred("CPIAUCSL"); cpiyoy=(cpi/cpi.shift(12)-1).resample("MS").last()
vq=ret["VNQ"].copy(); vq.index=vq.index.to_period("M").to_timestamp()
d3=pd.concat([vq.rename("vnq"),cpiyoy.rename("cpi")],axis=1).dropna()
r,se,t,p=nw_corr(d3["vnq"].values,d3["cpi"].values)
print(f"VNQ-CPIyoy: r={r:.3f} NW t={t:.2f} p={p:.3f} n={len(d3)} (session reported r=-0.112 p=0.090 n=258)",flush=True)
