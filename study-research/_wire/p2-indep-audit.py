"""P2 INDEPENDENT audit — auditor's OWN recompute. Does NOT import P1/P2a code.
Different choices to catch measurer coder bugs:
  - Newey-West HAC SE for the correlation (Fisher-z regression) -> robust p (IID pearsonr ignores autocorr)
  - independent partial-corr via OLS residualization (cross-check P2a L-axis)
  - defensive sleeve ticker independence: confirm XLP/XLU/XLV equal-weight log-return
  - C7 tail with BOTH expanding-quantile (PIT) AND simple full-sample quantile (robustness)
"""
from __future__ import annotations
import numpy as np, pandas as pd, warnings
from pathlib import Path
from scipy import stats
import statsmodels.api as sm
warnings.filterwarnings("ignore")

FRED = Path(r"D:\projects\Inv\study-research\eq_us_defensive\raw\fred")
SLEEVE = {
    "eq_cyclical": ["XLB","XLI","SOXX"], "xle": ["XLE"], "eq_intl": ["EFA","EEM"],
    "reit": ["VNQ"], "commodity": ["DBC"], "gold": ["GLD"], "defensive": ["XLP","XLU","XLV"],
}

def fetch(tickers):
    import yfinance as yf
    cols={}
    for t in tickers:
        h=yf.Ticker(t).history(period="max", auto_adjust=True)
        px=h["Close"].copy(); px.index=pd.to_datetime(px.index).tz_localize(None)
        cols[t]=px
    return pd.DataFrame(cols)

def sret(px, s):
    av=[t for t in SLEEVE[s] if t in px.columns]
    return np.log(px[av]).diff().mean(axis=1).dropna()

def nw_corr_p(x, y, lags=10):
    """correlation significance via Newey-West HAC on standardized regression."""
    x=(x-x.mean())/x.std(); y=(y-y.mean())/y.std()
    X=sm.add_constant(x.values)
    m=sm.OLS(y.values, X).fit(cov_type="HAC", cov_kwds={"maxlags":lags})
    beta=m.params[1]; pval=m.pvalues[1]
    return beta, pval

def fisher_ci(r,n,a=0.05):
    z=np.arctanh(r); se=1/np.sqrt(n-3); zc=stats.norm.ppf(1-a/2)
    return np.tanh(z-zc*se), np.tanh(z+zc*se)

allt=sorted({t for v in SLEEVE.values() for t in v})
px=fetch(allt)
S={s:sret(px,s) for s in SLEEVE}

# independent VIX load (do not reuse P2a func)
vdf=pd.read_csv(FRED/"VIXCLS.csv"); vdf.columns=["d","v"]
vdf["d"]=pd.to_datetime(vdf["d"]); vix=pd.to_numeric(vdf["v"],errors="coerce"); vix.index=vdf["d"]; vix=vix.dropna()
vix_d=vix.reindex(px.index).ffill()

print("=== DEFENSIVE sleeve independence (XLP/XLU/XLV eq-wt) ===")
for t in ["XLP","XLU","XLV"]:
    s=px[t].dropna(); print(f"  {t}: n={len(s)} {s.index.min().date()}~{s.index.max().date()}")
print(f"  defensive sleeve ret n={len(S['defensive'])} (eq-weight log-ret of 3)")

PAIRS=[("eq_cyclical","eq_intl"),("eq_cyclical","reit"),("commodity","xle"),
       ("gold","commodity"),("gold","eq_intl"),("xle","eq_cyclical"),
       ("gold","eq_cyclical"),("defensive","eq_cyclical"),("defensive","reit")]
print("\n=== INDEP Pearson r + Newey-West HAC p (lags=10) ===")
for a,b in PAIRS:
    df=pd.concat([S[a].rename("x"),S[b].rename("y")],axis=1).dropna()
    n=len(df); r,p_iid=stats.pearsonr(df.x,df.y); lo,hi=fisher_ci(r,n)
    beta,p_nw=nw_corr_p(df.x,df.y)
    print(f"{a:11s}<->{b:11s} r={r:+.4f} CI[{lo:+.4f},{hi:+.4f}] n={n} p_iid={p_iid:.1e} p_NW={p_nw:.1e}")

print("\n=== defensive vol beta: corr(ret,dVIX) indep ===")
dvix=vix_d.diff()
for a in ["defensive","eq_cyclical","gold"]:
    df=pd.concat([S[a].rename("y"),dvix.rename("d")],axis=1).dropna()
    r,_=stats.pearsonr(df.y,df.d); n=len(df); lo,hi=fisher_ci(r,n)
    _,p_nw=nw_corr_p(df.y,df.d)
    print(f"  {a:11s} corr(ret,dVIX)={r:+.4f} CI[{lo:+.4f},{hi:+.4f}] n={n} p_NW={p_nw:.1e}")

print("\n=== C7 gold-hedge tail: PIT expanding-q AND full-sample q ===")
for label,thr_series in [("PITexp",vix_d.expanding(min_periods=250).quantile(0.99)),
                         ("fullsample",pd.Series(vix_d.quantile(0.99),index=vix_d.index))]:
    mask=vix_d>=thr_series
    for a,b in [("gold","eq_cyclical"),("gold","eq_intl")]:
        df=pd.concat([S[a].rename("x"),S[b].rename("y"),mask.rename("m")],axis=1).dropna()
        d=df[df.m]
        if len(d)<10: print(f"  {label} VIX>q99 {a}<->{b}: n={len(d)} INSUFF"); continue
        r,p=stats.pearsonr(d.x,d.y); lo,hi=fisher_ci(r,len(d))
        print(f"  {label} VIX>q99 {a}<->{b}: r={r:+.4f} CI[{lo:+.4f},{hi:+.4f}] n={len(d)} p={p:.1e}")

print("\n=== L-axis partial-corr (indep OLS residualize on dVIX) ===")
def pcorr(a,b,ctrl):
    df=pd.concat([S[a].rename("a"),S[b].rename("b"),ctrl.rename("c")],axis=1).dropna()
    ra=sm.OLS(df.a,sm.add_constant(df.c)).fit().resid
    rb=sm.OLS(df.b,sm.add_constant(df.c)).fit().resid
    r,p=stats.pearsonr(ra,rb); return r,len(df),p
for a,b in [("eq_cyclical","eq_intl"),("eq_cyclical","reit"),("gold","eq_cyclical")]:
    raw=stats.pearsonr(*pd.concat([S[a],S[b]],axis=1).dropna().T.values)[0]
    rp,n,p=pcorr(a,b,dvix)
    print(f"  {a}<->{b}: raw={raw:+.4f} partial(removeVIX)={rp:+.4f} drop={raw-rp:+.4f} n={n} p={p:.1e}")
