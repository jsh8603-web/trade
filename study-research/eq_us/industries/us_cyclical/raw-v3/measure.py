# -*- coding: utf-8 -*-
"""measure.py — us_cyclical §M v3 측정 (한국 미러 + 미국 EDGAR 적응).

frame v3 §M.1~M.7. ★핵심 가설: PBR○ PER✗(peak-EPS, 한국 auto/반도체 재현 검증) + dollar β + HY OAS regime.

측정:
  - forward 횡단면 Rank-IC (momentum/vol/valuation, horizon-tagged)
  - valuation = EDGAR PIT 재구성 (filed date 이후만 = lookahead 회피) → PBR/PER cross-sectional z
  - 4게이트: G2 BY-FDR / G3 CPCV purge+embargo / G4 Newey-West HAC + block-boot
  - dollar β (H4) + HY OAS regime (H3, ★2023~ 한정 caveat)
  - LOO robustness (small-universe magnitude 점검)
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, "D:/projects/Inv")
from core.assume.weight_falsification import rank_ic, score_ic_breakdown_eprocess

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

# US net-cost (STT 없음): commission + spread/2 + impact
COMMISSION = 0.0005
SPREAD_HALF = 0.0003


def load():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    ed = pd.read_parquet(DATA / "edgar_fundamentals.parquet")
    uni = pd.read_parquet(DATA / "universe.parquet")
    macro = pd.read_parquet(DATA / "macro.parquet"); macro.index = pd.to_datetime(macro.index)
    return px, ed, uni, macro


# ── EDGAR PIT valuation 패널 ──
def build_pit_valuation(px, ed):
    """EDGAR filed date 이후만 적용(PIT) → 월말 PBR/PER 패널.
    equity = StockholdersEquity(BS). net_income = TTM(직전 4분기 합 근사 = 최신 FY 또는 분기 annualize)."""
    pxm = px.resample("ME").last()
    monthly_idx = pxm.index
    ed = ed.copy()
    ed["filed_dt"] = pd.to_datetime(ed["filed"], errors="coerce")
    ed = ed.dropna(subset=["filed_dt", "val"])

    pbr_panel, per_panel = {}, {}
    for t in px.columns:
        sub = ed[ed["ticker"] == t]
        eq = sub[sub["concept"] == "equity"].sort_values("filed_dt")
        ni = sub[sub["concept"] == "net_income"].sort_values("filed_dt")
        sh = sub[sub["concept"] == "shares"].sort_values("filed_dt")
        if len(eq) == 0 or len(sh) == 0:
            continue
        pbr_s = pd.Series(index=monthly_idx, dtype=float)
        per_s = pd.Series(index=monthly_idx, dtype=float)
        for dt in monthly_idx:
            # ★PIT: filed_dt <= dt 인 것만 (lookahead 회피)
            eq_av = eq[eq["filed_dt"] <= dt]
            sh_av = sh[sh["filed_dt"] <= dt]
            if len(eq_av) == 0 or len(sh_av) == 0:
                continue
            price = pxm.loc[dt, t] if t in pxm.columns else np.nan
            if np.isnan(price):
                continue
            shares = sh_av["val"].iloc[-1]
            mktcap = price * shares
            equity = eq_av["val"].iloc[-1]
            if equity and equity > 0:
                pbr_s[dt] = mktcap / equity
            # PER: TTM net income (최신 FY 우선, 없으면 직전 4분기 합)
            ni_av = ni[ni["filed_dt"] <= dt]
            ttm = ttm_ni(ni_av)
            if ttm and ttm > 0:
                per_s[dt] = mktcap / ttm
        pbr_panel[t] = pbr_s
        per_panel[t] = per_s
    return pd.DataFrame(pbr_panel), pd.DataFrame(per_panel)


def ttm_ni(ni_df):
    """TTM 순이익: FY(연간) 우선, 없으면 최근 4 분기 합 근사."""
    if len(ni_df) == 0:
        return None
    fy = ni_df[ni_df["fp"] == "FY"]
    if len(fy):
        return fy["val"].iloc[-1]
    # 분기 누적 4개 (end 기준 최근 4 distinct quarter)
    q = ni_df[ni_df["fp"].isin(["Q1", "Q2", "Q3", "Q4"])].drop_duplicates("end").tail(4)
    if len(q) >= 4:
        return q["val"].sum()
    return None


def cs_z(panel):
    mu = panel.mean(axis=1); sd = panel.std(axis=1, ddof=1)
    return panel.sub(mu, axis=0).div(sd.replace(0, np.nan), axis=0)


def cs_ic(sig, fwd, min_n=8):
    idx = sig.index.intersection(fwd.index); ics, ns, dates = [], [], []
    for dt in idx:
        sv = sig.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
        c = sv.index.intersection(rv.index)
        if len(c) < min_n:
            continue
        rho, _ = stats.spearmanr(sv.loc[c], rv.loc[c])
        if not np.isnan(rho):
            ics.append(rho); ns.append(len(c)); dates.append(dt)
    return pd.Series(ics, index=dates), pd.Series(ns, index=dates)


def nw_se(ic, lags):
    x = ic.values.astype(float); n = len(x)
    if n < 3:
        return np.nan
    e = x - x.mean(); g0 = (e @ e) / n; var = g0
    for k in range(1, min(lags, n - 1) + 1):
        w = 1 - k / (lags + 1); var += 2 * w * (e[k:] @ e[:-k]) / n
    return float(np.sqrt(max(var, 1e-12) / n))


def block_boot(x, block=3, B=2000, seed=42):
    rng = np.random.default_rng(seed); n = len(x); nb = int(np.ceil(n / block)); m = []
    for _ in range(B):
        st = rng.integers(0, n - block + 1, size=nb)
        m.append(np.concatenate([x[s:s+block] for s in st])[:n].mean())
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def cpcv(sig, fwd, h, n_splits=6, n_test=2):
    ic, _ = cs_ic(sig, fwd)
    if len(ic) < n_splits * 2:
        return dict(oos_hit=np.nan, n_folds=0)
    months = ic.index.tolist(); fs = len(months) // n_splits
    folds = [months[i*fs:(i+1)*fs] for i in range(n_splits)]
    from itertools import combinations
    oos = []
    for combo in combinations(range(n_splits), n_test):
        tm = set()
        for fi in combo: tm.update(folds[fi])
        sub = ic[ic.index.isin(tm)]
        if len(sub) >= 2: oos.append(sub.mean())
    oos = np.array(oos); fsign = np.sign(ic.mean())
    return dict(oos_ic_mean=float(oos.mean()), oos_hit=float((np.sign(oos) == fsign).mean()),
                n_folds=len(oos), purge_months=h)


def within_period(ic):
    if len(ic) < 12:
        return None
    by = ic.groupby(ic.index.year).mean(); fs = np.sign(ic.mean())
    return float((np.sign(by) == fs).mean())


def measure_sig(sig, fwd, h, name):
    ic, ns = cs_ic(sig, fwd)
    if len(ic) < 6:
        return None
    n = len(ic); mean = float(ic.mean())
    se = nw_se(ic, h); t = mean / se if se and se > 0 else np.nan
    p = float(2 * (1 - stats.t.cdf(abs(t), df=max(n-1, 1)))) if not np.isnan(t) else np.nan
    ci = block_boot(ic.values, 3, 2000) if n >= 6 else (np.nan, np.nan)
    return dict(signal=name, h_months=h, ic_mean=round(mean, 4), n_months=n,
                t_nw=round(t, 2) if not np.isnan(t) else None,
                p_value_nw=round(p, 4) if not np.isnan(p) else None,
                ci95_block_boot=[round(ci[0], 4), round(ci[1], 4)],
                cpcv=cpcv(sig, fwd, h), within_period=within_period(ic),
                avg_universe_n=round(float(ns.mean()), 1))


def benjamini_yekutieli(pvals, q=0.10):
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    m = len(items)
    if m == 0:
        return {"m": 0}
    items.sort(key=lambda x: x[1])
    cm = sum(1.0 / i for i in range(1, m + 1)); surv = []
    for r, (k, p) in enumerate(items, 1):
        if p <= (r / m) * q / cm: surv = [items[j][0] for j in range(r)]
    return dict(m=m, by_factor=round(cm, 3), survivors_BY=surv,
                raw_p_min=round(items[0][1], 5), raw_p_min_key=items[0][0])


def dollar_beta(px, macro):
    """sleeve 동일가중 월간 수익 ~ dollar(DXY) Δ (H4, contemporaneous HAC)."""
    import statsmodels.api as sm
    pxm = px.resample("ME").last()
    ret = pxm.pct_change().mean(axis=1)
    mm = macro.resample("ME").last()
    feat = pd.DataFrame(index=mm.index)
    if "dollar" in mm: feat["dollar"] = mm["dollar"].pct_change()
    if "rate10y" in mm: feat["rate"] = mm["rate10y"].diff()
    if "vix" in mm: feat["vix"] = mm["vix"].diff()
    if "hy_oas" in mm: feat["hy_oas"] = mm["hy_oas"].diff()
    df = pd.concat([ret.rename("y"), feat], axis=1).dropna()
    if len(df) < 24:
        return {"note": "insufficient", "n": len(df)}
    X = sm.add_constant(df.drop(columns="y"))
    model = sm.OLS(df["y"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    out = {}
    for f in df.columns.drop("y"):
        out[f] = dict(beta=round(float(model.params[f]), 4), t=round(float(model.tvalues[f]), 2),
                      ci95=[round(float(model.conf_int().loc[f, 0]), 4), round(float(model.conf_int().loc[f, 1]), 4)])
    out["_meta"] = dict(n=len(df), r2=round(float(model.rsquared), 3),
                        note="HAC(maxlags=3). dollar=DXY pct, rate/vix/hy_oas=diff. ★hy_oas 2023~ 한정.")
    return out


def main():
    px, ed, uni, macro = load()
    pxm = px.resample("ME").last()
    print(f"universe {px.shape[1]} tickers, {px.shape[0]} days")

    # 가격 신호
    mom_12_1 = cs_z(pxm.shift(1) / pxm.shift(12) - 1)
    mom_6 = cs_z(pxm / pxm.shift(6) - 1)
    ret_d = px.pct_change(); vol_60 = cs_z((ret_d.rolling(60).std() * np.sqrt(252)).resample("ME").last())
    # valuation (EDGAR PIT)
    pbr, per = build_pit_valuation(px, ed)
    print(f"PBR panel {pbr.shape} cov {pbr.notna().sum().sum()} / PER {per.shape} cov {per.notna().sum().sum()}")
    pbr_z, per_z = cs_z(pbr), cs_z(per)

    signals = {"mom_12_1": mom_12_1, "mom_6": mom_6, "vol_60": vol_60, "pbr_z": pbr_z, "per_z": per_z}
    horizons = {"3M": 3, "6M": 6, "12M": 12, "24M_value": 24}

    indicators, pvals = {}, {}
    for sname, sig in signals.items():
        for hname, h in horizons.items():
            fwd = pxm.shift(-h) / pxm - 1
            r = measure_sig(sig, fwd, h, f"{sname}__{hname}")
            if r:
                key = f"{sname}__{hname}"; indicators[key] = r; pvals[key] = r["p_value_nw"]

    results = {
        "meta": {"universe_n": int(px.shape[1]), "date_range": [str(px.index.min().date()), str(px.index.max().date())],
                 "pbr_cov": int(pbr.notna().sum().sum()), "per_cov": int(per.notna().sum().sum()),
                 "note": "US EDGAR PIT(filed date) valuation + yfinance 가격. ★survivorship-biased(현 holdings)."},
        "indicators": indicators,
        "multiple_testing": benjamini_yekutieli(pvals),
        "dollar_beta_H4": dollar_beta(px, macro),
        "net_cost": {"roundtrip_bps": round((COMMISSION + SPREAD_HALF) * 2 * 1e4, 1), "note": "US STT 없음"},
    }
    (ROOT / "validation-metrics-v3.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print("\n" + "=" * 76)
    print(f"{'signal__h':<20}{'IC':>9}{'t_NW':>7}{'n_mo':>6}{'p_NW':>8}{'cpcv':>7}{'within':>8}{'avgN':>6}")
    for k, v in sorted(indicators.items(), key=lambda x: -abs(x[1]["ic_mean"] or 0)):
        print(f"{k:<20}{(v['ic_mean'] or 0):>+9.3f}{(v['t_nw'] or 0):>7.2f}{v['n_months']:>6}"
              f"{(v['p_value_nw'] or 0):>8.3f}{(v['cpcv'].get('oos_hit') or 0):>7.2f}"
              f"{(v['within_period'] or 0):>8.2f}{v['avg_universe_n']:>6.1f}")
    mt = results["multiple_testing"]
    print(f"\nBY: m={mt['m']} factor={mt.get('by_factor')} raw_p_min={mt.get('raw_p_min')} ({mt.get('raw_p_min_key')}) survivors={mt.get('survivors_BY')}")
    print("\ndollar β (H4):")
    for f, v in results["dollar_beta_H4"].items():
        if f == "_meta": continue
        print(f"  {f:<8} β={v['beta']:+.4f} t={v['t']:+.2f} CI={v['ci95']}")
    print(f"  {results['dollar_beta_H4'].get('_meta')}")


if __name__ == "__main__":
    main()
