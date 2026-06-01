"""P2a independent audit recompute — NOT trusting P1 JSON. Re-fetch, recompute, fingerprint."""
from __future__ import annotations
import json, warnings
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
warnings.filterwarnings("ignore")
rng = np.random.default_rng(777)  # different seed than P1 to confirm robustness

ROOT = Path(r"D:\projects\Inv\study-research")
FRED = ROOT / "eq_us_defensive" / "raw" / "fred"

SLEEVE_TICKERS = {
    "eq_cyclical": ["XLB", "XLI", "SOXX"],
    "xle_energy": ["XLE"],
    "eq_intl": ["EFA", "EEM"],
    "reit": ["VNQ"],
    "commodity": ["DBC"],
    "gold": ["GLD"],
    "defensive": ["XLP", "XLU", "XLV"],  # P1 GAP — defensive own sleeve
}

def fetch_prices(tickers):
    import yfinance as yf
    cols = {}
    for t in tickers:
        h = yf.Ticker(t).history(period="max", auto_adjust=True)
        if len(h) == 0:
            raise RuntimeError(f"EMPTY {t}")
        px = h["Close"].copy()
        px.index = pd.to_datetime(px.index).tz_localize(None)
        cols[t] = px
    return pd.DataFrame(cols)

def sleeve_logret(px, sleeve):
    avail = [t for t in SLEEVE_TICKERS[sleeve] if t in px.columns]
    r = np.log(px[avail]).diff()
    return r.mean(axis=1).dropna()

def load_fred(name):
    df = pd.read_csv(FRED / f"{name}.csv")
    df.columns = ["date", "val"]
    df["date"] = pd.to_datetime(df["date"])
    s = pd.to_numeric(df["val"], errors="coerce"); s.index = df["date"]
    return s.dropna()

def fisher_ci(r, n, alpha=0.05):
    z = np.arctanh(r); se = 1/np.sqrt(n-3); zc = stats.norm.ppf(1-alpha/2)
    return (np.tanh(z-zc*se), np.tanh(z+zc*se))

all_t = sorted({t for v in SLEEVE_TICKERS.values() for t in v})
px = fetch_prices(all_t)
sret = {s: sleeve_logret(px, s) for s in SLEEVE_TICKERS}

print("=== FINGERPRINT (synthetic detection) ===")
# per-ticker coverage + gap + 2020-03 & 2022 event presence
for t in all_t:
    s = px[t].dropna()
    daily_ret = np.log(s).diff().dropna()
    # 2020-03 crash: should have big negative days
    m2003 = daily_ret["2020-03-01":"2020-03-31"]
    min2003 = m2003.min() if len(m2003) else np.nan
    # 2022 drawdown presence
    y2022 = daily_ret["2022-01-01":"2022-12-31"]
    std2022 = y2022.std() if len(y2022) else np.nan
    # gap check: max calendar gap between consecutive obs
    gaps = s.index.to_series().diff().dt.days.dropna()
    maxgap = int(gaps.max()) if len(gaps) else -1
    n_dupe = int(s.index.duplicated().sum())
    print(f"{t:5s} n={len(s):5d} {s.index.min().date()}~{s.index.max().date()} "
          f"maxgap={maxgap}d dupes={n_dupe} 2020-03_min={min2003:.4f} 2022_std={std2022:.5f}")

print("\n=== VIX series fingerprint ===")
vix = load_fred("VIXCLS")
print(f"VIX n={len(vix)} {vix.index.min().date()}~{vix.index.max().date()} "
      f"min={vix.min():.2f} max={vix.max():.2f} (2020-03 peak should be ~80+)")
print(f"  2020-03 VIX max = {vix['2020-03-01':'2020-03-31'].max():.2f}")
print(f"  2008-10/11 VIX max = {vix['2008-10-01':'2008-11-30'].max():.2f}")

# VIX regime PIT-safe expanding median (replicate P1)
vix_d = vix.reindex(px.index).ffill()
exp_med = vix_d.expanding(min_periods=250).median()
riskoff = (vix_d >= exp_med)

print("\n=== INDEPENDENT PEARSON RECOMPUTE (seed=777 boot) ===")
PAIRS = [
    ("eq_cyclical","eq_intl"), ("eq_cyclical","reit"), ("commodity","xle_energy"),
    ("gold","commodity"), ("gold","eq_intl"), ("xle_energy","eq_cyclical"),
    ("gold","eq_cyclical"),
    # P1 GAP fills:
    ("defensive","eq_cyclical"), ("defensive","gold"), ("defensive","reit"),
]
bonf = 0.05/len(PAIRS)
for a,b in PAIRS:
    df = pd.concat([sret[a].rename("x"), sret[b].rename("y")], axis=1).dropna()
    n=len(df); r,p = stats.pearsonr(df.x, df.y); lo,hi = fisher_ci(r,n)
    print(f"{a:11s}<->{b:11s} r={r:+.4f} CI[{lo:+.4f},{hi:+.4f}] n={n} p={p:.2e} bonf_surv={p<bonf}")

print("\n=== C7 gold-hedge TAIL check (N-axis tail sign reversal) ===")
# Does gold<->equity flip negative in VIX tail (top 5% / top 1%)?
for tail_q in [0.90, 0.95, 0.99]:
    thr = vix_d.expanding(min_periods=250).quantile(tail_q)  # PIT-safe expanding quantile
    tail_mask = (vix_d >= thr)
    for pair in [("gold","eq_cyclical"), ("gold","eq_intl")]:
        a,b = pair
        df = pd.concat([sret[a].rename("x"), sret[b].rename("y"), tail_mask.rename("t")], axis=1).dropna()
        d = df[df.t]
        if len(d) < 10:
            print(f"  VIX>q{tail_q} {a}<->{b}: n={len(d)} INSUFFICIENT"); continue
        r,p = stats.pearsonr(d.x,d.y); lo,hi=fisher_ci(r,len(d))
        print(f"  VIX>q{tail_q} {a}<->{b}: r={r:+.4f} CI[{lo:+.4f},{hi:+.4f}] n={len(d)} p={p:.2e}")

print("\n=== defensive (C9) own vol exposure — direct measurability check ===")
# regress defensive sleeve return on VIX daily change (vol factor proxy)
dvix = vix_d.diff()
for a in ["defensive","eq_cyclical","gold"]:
    df = pd.concat([sret[a].rename("y"), dvix.rename("dvix")], axis=1).dropna()
    r,p = stats.pearsonr(df.y, df.dvix); n=len(df); lo,hi=fisher_ci(r,n)
    print(f"  {a:11s} corr(ret, dVIX) = {r:+.4f} CI[{lo:+.4f},{hi:+.4f}] n={n} p={p:.2e}")

print("\n=== L-axis: VIX common-factor single-count probe ===")
# partial corr: does eq_cyclical<->eq_intl survive after removing VIX(dvix)?
def partial_corr(a,b,ctrl):
    df = pd.concat([sret[a].rename("a"), sret[b].rename("b"), ctrl.rename("c")], axis=1).dropna()
    ra = stats.linregress(df.c, df.a).slope; resa = df.a - ra*df.c
    rb = stats.linregress(df.c, df.b).slope; resb = df.b - rb*df.c
    r,p = stats.pearsonr(resa, resb)
    return r, len(df), p
for a,b in [("eq_cyclical","eq_intl"),("eq_cyclical","reit"),("gold","eq_cyclical")]:
    r0 = stats.pearsonr(*pd.concat([sret[a],sret[b]],axis=1).dropna().T.values)[0]
    rp,n,p = partial_corr(a,b,dvix)
    print(f"  {a}<->{b}: raw={r0:+.4f} | partial(removeVIX)={rp:+.4f} n={n} p={p:.2e} (drop={r0-rp:+.4f})")
