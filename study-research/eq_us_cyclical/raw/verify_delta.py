"""Verify-stage statistics for eq_us_cyclical industry x regime delta matrix.
4 obligations: G2 stationary bootstrap CI / G4 leave-one-epoch-out OOS / K multiple comparison / per-industry vol.
Data: raw/yfinance/sector_etf_close.csv (4 industries) over M3 frame 2021-12-01 ~ 2024-12-31.
Replicates m3_analysis.py epoch boundaries exactly. No synthetic data.
"""
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
from pathlib import Path

rng = np.random.default_rng(20260531)
ROOT = Path('D:/projects/Inv/study-research/eq_us_cyclical/raw')

close = pd.read_csv(ROOT / 'yfinance/sector_etf_close.csv', parse_dates=['Date'], index_col='Date')
START, END = pd.Timestamp('2021-12-01'), pd.Timestamp('2024-12-31')
close = close.loc[START:END]
IND = ['SOXX', 'XLB', 'XLI', 'XLE']
ret = close[IND].pct_change().dropna(how='all')

epochs = [
    ('E1_tightening_shock', '2022-01-01', '2022-09-30'),
    ('E2_transition_rally', '2022-10-01', '2023-06-30'),
    ('E3_rate_re_rise',     '2023-07-01', '2023-10-31'),
    ('E4_pivot_cuts',       '2023-11-01', '2024-12-31'),
]
TRADING = 252


def ann_from_daily(r):
    r = r.dropna()
    n = len(r)
    if n == 0:
        return np.nan, 0
    return (1 + r).prod() ** (TRADING / n) - 1, n


print("=" * 80)
print("VERIFY STAGE -- eq_us_cyclical industry x regime delta (M3 frame 2021-12~2024-12)")
print("ETF window: %s ~ %s  daily n=%d" % (ret.index.min().date(), ret.index.max().date(), len(ret)))
print("=" * 80)

# ---- replicate point estimates ----
print("\n[REPLICATION] per-industry per-epoch annualized return (vs findings table)")
print("%-24s %s   n" % ("epoch", " ".join("%9s" % s for s in IND)))
point = {}
ndays = {}
for name, s0, s1 in epochs:
    mask = (ret.index >= s0) & (ret.index <= s1)
    row = "%-24s " % name
    point[name] = {}
    for s in IND:
        a, n = ann_from_daily(ret.loc[mask, s])
        point[name][s] = float(a)
        row += "%+9.1f " % (a * 100)
    ndays[name] = int(mask.sum())
    row += "  %d" % ndays[name]
    print(row)

# ---- obligation 4: per-industry per-epoch realized vol ----
print("\n[OBLIGATION 4] per-industry per-epoch realized annualized vol (vs sleeve vol proxy)")
print("%-24s %s  sleeve_vol(m3)" % ("epoch", " ".join("%9s" % s for s in IND)))
SLEEVE_VOL = {'E1_tightening_shock': 0.2555, 'E2_transition_rally': 0.2125,
              'E3_rate_re_rise': 0.1296, 'E4_pivot_cuts': 0.1413}
vol = {}
for name, s0, s1 in epochs:
    mask = (ret.index >= s0) & (ret.index <= s1)
    row = "%-24s " % name
    vol[name] = {}
    for s in IND:
        v = ret.loc[mask, s].std() * np.sqrt(TRADING)
        vol[name][s] = float(v)
        row += "%+9.1f " % (v * 100)
    row += "  %7.1f" % (SLEEVE_VOL[name] * 100)
    print(row)


# ---- obligation 1 / G2: stationary bootstrap CI ----
def stationary_bootstrap_ann(r, B=5000, mean_block=20):
    r = r.dropna().values
    n = len(r)
    if n < 5:
        return np.nan, np.nan, np.nan
    p = 1.0 / mean_block
    out = np.empty(B)
    for b in range(B):
        idx = np.empty(n, dtype=int)
        i = rng.integers(0, n)
        idx[0] = i
        for t in range(1, n):
            if rng.random() < p:
                i = rng.integers(0, n)
            else:
                i = (i + 1) % n
            idx[t] = i
        rs = r[idx]
        out[b] = (1 + rs).prod() ** (TRADING / n) - 1
    return np.percentile(out, 2.5), np.percentile(out, 97.5), out.std()


print("\n[OBLIGATION 1 / G2] stationary bootstrap 95%% CI for ann return (B=5000, mean_block=20d)")
print("  delta(B-direction-aware) = ann_ret(frac); clip[-0.15,+0.15]; CI on UNCLIPPED delta")
print("%-28s %10s %9s %8s %9s %9s %9s" % ("cell", "point_ann%", "d_unclip", "d_clip", "CI_lo(d)", "CI_hi(d)", "CIcross0"))
bootci = {}
for name, s0, s1 in epochs:
    mask = (ret.index >= s0) & (ret.index <= s1)
    for s in IND:
        lo, hi, sd = stationary_bootstrap_ann(ret.loc[mask, s])
        d_unclip = point[name][s]
        d_clip = float(np.clip(d_unclip, -0.15, 0.15))
        cross = (lo < 0 < hi)
        bootci["%s|%s" % (name, s)] = {'point_ann': float(point[name][s]), 'd_unclip': float(d_unclip),
                                       'd_clip': d_clip, 'ci_lo': float(lo), 'ci_hi': float(hi),
                                       'boot_sd': float(sd), 'ci_cross_zero': bool(cross)}
        print("%-28s %+10.1f %+9.3f %+8.3f %+9.3f %+9.3f %9s" % (
            name[:12] + "|" + s, point[name][s] * 100, d_unclip, d_clip, lo, hi, "YES" if cross else "no"))

# ---- obligation 3 / K: multiple comparison ----
print("\n[OBLIGATION 3 / K] multiple comparison -- H0: epoch mean DAILY return = 0 (Newey-West t)")
print("  16 cells. raw p, Bonferroni alpha/16=0.003125, Benjamini-Hochberg FDR q=0.05")
pvals = []
cells = []
tinfo = {}
for name, s0, s1 in epochs:
    mask = (ret.index >= s0) & (ret.index <= s1)
    for s in IND:
        y = ret.loc[mask, s].dropna().values
        n = len(y)
        X = np.ones((n, 1))
        lag = max(int(np.floor(4 * (n / 100) ** (2 / 9))), 1)
        res = sm.OLS(y, X).fit(cov_type='HAC', cov_kwds={'maxlags': lag})
        p = float(res.pvalues[0])
        t = float(res.tvalues[0])
        pvals.append(p)
        cells.append("%s|%s" % (name, s))
        tinfo["%s|%s" % (name, s)] = {'mean_daily': float(y.mean()), 't': t, 'p_raw': p, 'nw_lag': lag, 'n': n}
pvals = np.array(pvals)
bonf = 0.05 / 16
order = np.argsort(pvals)
sorted_p = pvals[order]
m = 16
q = 0.05
bh_crit = 0.0
for k in range(m, 0, -1):
    if sorted_p[k - 1] <= k / m * q:
        bh_crit = sorted_p[k - 1]
        break
print("%-28s %9s %7s %10s %13s %7s" % ("cell", "mean_d%", "t_NW", "p_raw", "Bonf(<.0031)", "BH-FDR"))
for i, c in enumerate(cells):
    bp = 'PASS' if pvals[i] < bonf else 'fail'
    fp = 'PASS' if pvals[i] <= bh_crit else 'fail'
    md = tinfo[c]['mean_daily']
    t = tinfo[c]['t']
    short = c.split("|")[0][:12] + "|" + c.split("|")[1]
    print("%-28s %+9.3f %+7.2f %10.4f %13s %7s" % (short, md * 100, t, pvals[i], bp, fp))
print("  Bonferroni survivors: %d/16   BH-FDR survivors: %d/16 (crit p=%.4f)" % (
    int((pvals < bonf).sum()), int((pvals <= bh_crit).sum()), bh_crit))

# ---- obligation 2 / G4: leave-one-epoch-out OOS ----
print("\n[OBLIGATION 2 / G4] leave-one-epoch-out -- does epoch-mean regime signal generalize?")
print("  Test: sign of held-out epoch return vs predicted by mean of 3 training epochs (same industry)")
print("%-24s %8s %9s %16s %10s" % ("held_out", "industry", "true_ann%", "pred(train)%", "sign_match"))
oos_correct = 0
oos_total = 0
for name, s0, s1 in epochs:
    for s in IND:
        train_means = []
        for n2, a, b in epochs:
            if n2 == name:
                continue
            mask = (ret.index >= a) & (ret.index <= b)
            train_means.append(ret.loc[mask, s].mean())
        pred_daily = np.mean(train_means)
        true_ann = point[name][s]
        match = np.sign(pred_daily) == np.sign(true_ann)
        oos_total += 1
        oos_correct += int(match)
        print("%-24s %8s %+9.1f %+16.1f %10s" % (
            name, s, true_ann * 100, pred_daily * TRADING * 100, "MATCH" if match else "MISS"))
print("  OOS sign-match: %d/%d = %.0f%% (chance=50%%)" % (oos_correct, oos_total, oos_correct / oos_total * 100))

print("\n  Daily-level R2: IS (epoch-mean fit) vs OOS (leave-one-epoch, predict by mean of other 3)")
print("%8s %8s %8s %8s" % ("industry", "R2_IS", "R2_OOS", "delta"))
r2tab = {}
for s in IND:
    epoch_daily = {}
    for name, s0, s1 in epochs:
        mask = (ret.index >= s0) & (ret.index <= s1)
        epoch_daily[name] = ret.loc[mask, s].dropna()
    grand = pd.concat(epoch_daily.values())
    gmean = grand.mean()
    ss_tot = ((grand - gmean) ** 2).sum()
    ss_res_is = 0.0
    ss_res_oos = 0.0
    for name in epoch_daily:
        d = epoch_daily[name]
        ss_res_is += ((d - d.mean()) ** 2).sum()
        others = pd.concat([epoch_daily[n2] for n2 in epoch_daily if n2 != name])
        ss_res_oos += ((d - others.mean()) ** 2).sum()
    r2_is = 1 - ss_res_is / ss_tot
    r2_oos = 1 - ss_res_oos / ss_tot
    r2tab[s] = {'r2_is': float(r2_is), 'r2_oos': float(r2_oos)}
    print("%8s %8.4f %8.4f %+8.4f" % (s, r2_is, r2_oos, r2_oos - r2_is))

out = {'point': point, 'ndays': ndays, 'vol': vol, 'sleeve_vol': SLEEVE_VOL, 'bootci': bootci,
       'mult_comp': {'bonferroni_alpha': bonf, 'bh_crit_p': float(bh_crit),
                     'bonf_survivors': int((pvals < bonf).sum()),
                     'bh_survivors': int((pvals <= bh_crit).sum()), 'cells': tinfo},
       'oos_sign_match': "%d/%d" % (oos_correct, oos_total), 'r2_is_oos': r2tab}
with open(ROOT / 'verify-delta-metrics.json', 'w') as f:
    json.dump(out, f, indent=2)
print("\n[Saved] %s" % (ROOT / 'verify-delta-metrics.json'))
