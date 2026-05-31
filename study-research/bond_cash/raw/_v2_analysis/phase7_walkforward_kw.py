"""phase7_walkforward_kw.py — bond_cash P0 2건 해소 (2026-05-31, main option A 확정).

P0-1: walk-forward regime classifier (expanding window, audit C축 격하 해소)
P0-2: Kim-Wright FRED THREEFYTP10/5 fetch + ACM_TP10 cross-check (audit D축 격하 해소)

산출:
  - data/THREEFYTP10.parquet, THREEFYTP5.parquet, THREEFFTP10.parquet (R3 발견 KW endpoint)
  - sub-clusters/_walkforward_v5.json (walk-forward IS/OOS sign match per cell)
  - sub-clusters/_kw_vs_acm.json (KW vs ACM corr + magnitude diff)
  - sub-clusters/summary_v5.yaml (Phase 7 진입 ready)
"""
from __future__ import annotations
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import statsmodels.api as sm
from dotenv import load_dotenv
from scipy import stats

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT.parents[0] / "sub-clusters"

load_dotenv(ROOT.parents[3] / ".env")
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
assert FRED_API_KEY, "FRED_API_KEY missing"

# --- P0-2: KW fetch (R3 발견) ----------------------------------------------
KW_SERIES = {
    "THREEFYTP10": {"start": "1990-01-02", "cat": "kw_term_premium_10y"},
    "THREEFYTP5":  {"start": "1990-01-02", "cat": "kw_term_premium_5y"},
    "THREEFFTP10": {"start": "1990-01-02", "cat": "kw_forward_tp_10y_hence"},
}

def fetch_fred(sid: str, start: str) -> pd.DataFrame:
    url = "https://api.stlouisfed.org/fred/series/observations"
    r = requests.get(url, params={"series_id": sid, "api_key": FRED_API_KEY,
                                  "file_type": "json", "observation_start": start}, timeout=30)
    r.raise_for_status()
    df = pd.DataFrame(r.json().get("observations", []))
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")[["value"]].rename(columns={"value": sid})
    df[sid] = pd.to_numeric(df[sid], errors="coerce")
    return df.dropna(how="all")

print("[KW fetch — R3 발견 FRED endpoint]")
kw = {}
for sid, meta in KW_SERIES.items():
    df = fetch_fred(sid, meta["start"])
    df.to_parquet(DATA / f"{sid}.parquet")
    kw[sid] = df
    print(f"  [OK] {sid} rows={len(df):,} {df.index.min().date()}~{df.index.max().date()}")

# --- KW vs ACM cross-check (10Y) -------------------------------------------
acm = pd.read_parquet(DATA / "ACM.parquet")
common_idx = acm.index.intersection(kw["THREEFYTP10"].index)
acm10 = acm.loc[common_idx, "ACMTP10"].dropna()
kw10 = kw["THREEFYTP10"].loc[common_idx, "THREEFYTP10"].dropna()
joint = pd.concat([acm10, kw10], axis=1).dropna()
joint.columns = ["ACM_TP10", "KW_TP10"]
corr = joint.corr().iloc[0, 1]
mean_diff = (joint["ACM_TP10"] - joint["KW_TP10"]).mean()
std_diff = (joint["ACM_TP10"] - joint["KW_TP10"]).std()
joint_d20 = joint.diff(20).dropna()
corr_d20 = joint_d20.corr().iloc[0, 1]
kw_acm = {
    "common_period": [str(joint.index.min().date()), str(joint.index.max().date())],
    "n": int(len(joint)),
    "level_corr_acm_kw": round(float(corr), 4),
    "mean_diff_acm_minus_kw": round(float(mean_diff), 4),
    "std_diff": round(float(std_diff), 4),
    "d20_corr_acm_kw": round(float(corr_d20), 4),
    "interpretation": "level corr 가 매우 높으면(>0.95) 둘이 본질 동일, 낮으면 모델 차이 material — Fed FEDS Notes 2017 의 long-maturity material difference 검증."
}
(OUT / "_kw_vs_acm.json").write_text(json.dumps(kw_acm, indent=2))
print(f"\n[KW vs ACM cross-check 10Y]")
print(f"  common period: {kw_acm['common_period'][0]} ~ {kw_acm['common_period'][1]}, n={kw_acm['n']:,}")
print(f"  level corr  = {kw_acm['level_corr_acm_kw']:+.4f}")
print(f"  d20 corr    = {kw_acm['d20_corr_acm_kw']:+.4f}")
print(f"  mean(ACM-KW)= {kw_acm['mean_diff_acm_minus_kw']:+.4f}  std= {kw_acm['std_diff']:+.4f}")

# --- P0-1: walk-forward regime classifier ---------------------------------
# load v2 panel
fred = {s: pd.read_parquet(DATA / f"{s}.parquet")
        for s in ["DGS10", "DGS2", "DFII10", "BAA10Y"]}
move = pd.read_parquet(DATA / "YF_MOVE.parquet")

p = pd.DataFrame(index=pd.date_range("2007-01-01", "2026-05-29", freq="B"))
move_close = move["^MOVE_close"].reindex(p.index, method="ffill")
p["MOVE_Z"] = (move_close - move_close.rolling(252).mean()) / move_close.rolling(252).std()
acm_tp10 = acm["ACMTP10"].reindex(p.index, method="ffill")
p["ACM_TP10_d20"] = acm_tp10.diff(20)
# ★ KW TP10 = 새 stationary driver (D축 cross-check)
kw_tp10 = kw["THREEFYTP10"]["THREEFYTP10"].reindex(p.index, method="ffill")
p["KW_TP10_d20"] = kw_tp10.diff(20)
dgs10 = fred["DGS10"]["DGS10"].reindex(p.index, method="ffill")
p["DGS10_chg20"] = dgs10.diff(20)
dgs2 = fred["DGS2"]["DGS2"].reindex(p.index, method="ffill")
p["T10Y2Y_d20"] = (dgs10 - dgs2).diff(20)
baa = fred["BAA10Y"]["BAA10Y"].reindex(p.index, method="ffill")
p["BAA10Y_chg20"] = baa.diff(20)
rate_up = dgs10.diff(126) > 0
move_high = move_close > move_close.rolling(252).median()
p["regime"] = np.where(rate_up & move_high, "rate_up_vol_high",
              np.where(rate_up & ~move_high, "rate_up_vol_low",
              np.where(~rate_up & move_high, "rate_down_vol_high", "rate_down_vol_low")))
DRIVERS_V5 = ["MOVE_Z", "ACM_TP10_d20", "KW_TP10_d20", "DGS10_chg20", "T10Y2Y_d20", "BAA10Y_chg20"]
panel = p.dropna(subset=DRIVERS_V5, how="any")
print(f"\n[v5 panel] {panel.index.min().date()} ~ {panel.index.max().date()}  n={len(panel):,}")

SUB_CLUSTERS = {
    "tsy_long": "TLT", "tsy_mid": "IEF", "tsy_short": "SHY",
    "ig_credit": "LQD", "hy_credit": "HYG", "cash_tbill": "BIL", "tips": "TIP",
}
etfs = {s: pd.read_parquet(DATA / f"YF_{t}.parquet") for s, t in SUB_CLUSTERS.items()}

FWDS = [5, 20, 60]
N_SPLITS = 5      # walk-forward expanding window

def walk_forward_ic(x: np.ndarray, y: np.ndarray, n_splits: int = 5):
    """expanding-window IS/OOS sign match: 첫 1/n train 부터 시작, 1/n 씩 expanding.
       각 split 의 OOS IC sign 이 IS IC sign 과 일치하는지 측정."""
    n = len(x)
    chunk = n // n_splits
    results = []
    for k in range(1, n_splits):
        train_end = k * chunk
        test_start = train_end
        test_end = min(train_end + chunk, n)
        if test_end - test_start < 30:
            continue
        ic_is, _ = stats.spearmanr(x[:train_end], y[:train_end])
        ic_oos, _ = stats.spearmanr(x[test_start:test_end], y[test_start:test_end])
        if np.isnan(ic_is) or np.isnan(ic_oos):
            continue
        results.append({"split": k, "n_is": train_end, "n_oos": test_end - test_start,
                        "ic_is": float(ic_is), "ic_oos": float(ic_oos),
                        "sign_match": int(np.sign(ic_is) == np.sign(ic_oos))})
    if not results:
        return {"valid_splits": 0, "sign_match_rate": np.nan, "mean_ic_is": np.nan, "mean_ic_oos": np.nan}
    sm = sum(r["sign_match"] for r in results) / len(results)
    return {
        "valid_splits": len(results),
        "sign_match_rate": round(sm, 3),
        "mean_ic_is": round(np.mean([r["ic_is"] for r in results]), 4),
        "mean_ic_oos": round(np.mean([r["ic_oos"] for r in results]), 4),
        "splits": results,
    }

walk_results = {}
for sub, etf in SUB_CLUSTERS.items():
    etf_df = etfs[sub]
    px = etf_df[f"{etf}_adj_close"]
    sub_results = {}
    for d in DRIVERS_V5:
        for f in FWDS:
            yf = px.pct_change(f).shift(-f)
            tmp = panel[[d]].join(yf.rename("y"), how="inner").dropna()
            if len(tmp) < 200:
                continue
            res = walk_forward_ic(tmp[d].values, tmp["y"].values, n_splits=N_SPLITS)
            sub_results[f"{d}_fwd{f}"] = res
    walk_results[sub] = sub_results

# also regime-conditional walk-forward for HYG MOVE_Z fwd60 (audit C축 핵심 자가검증)
print("\n[★ HYG regime walk-forward 자가검증 (audit C축 핵심)]")
hyg_px = etfs["hy_credit"]["HYG_adj_close"]
yf60 = hyg_px.pct_change(60).shift(-60)
hyg_panel = panel[["MOVE_Z", "regime"]].join(yf60.rename("y"), how="inner").dropna()
regime_cells = ["rate_up_vol_high", "rate_up_vol_low", "rate_down_vol_high", "rate_down_vol_low"]
hyg_regime_wf = {}
for cell in regime_cells:
    cell_data = hyg_panel[hyg_panel["regime"] == cell]
    if len(cell_data) < 100:
        continue
    res = walk_forward_ic(cell_data["MOVE_Z"].values, cell_data["y"].values, n_splits=N_SPLITS)
    hyg_regime_wf[cell] = {**res, "n_total": int(len(cell_data))}
    print(f"  {cell:24s} n={len(cell_data):>5d} sign_match={res['sign_match_rate']} "
          f"mean_IS={res['mean_ic_is']:+.4f} mean_OOS={res['mean_ic_oos']:+.4f}")

(OUT / "_walkforward_v5.json").write_text(json.dumps({
    "n_splits": N_SPLITS,
    "drivers_v5": DRIVERS_V5,
    "per_sub_cluster": walk_results,
    "hyg_regime_walk_forward": hyg_regime_wf,
}, indent=2, default=str))

# --- summary v5 -----------------------------------------------------------
# walk-forward sign_match_rate 가 ≥0.5 (majority) 인 cell 만 sign-prior 진입 가능
sign_prior_eligible = {}
for sub, cells in walk_results.items():
    eligible = []
    for cell_key, res in cells.items():
        if res.get("valid_splits", 0) >= 3 and res.get("sign_match_rate", 0) >= 0.5:
            eligible.append({
                "spec": cell_key, "sign_match_rate": res["sign_match_rate"],
                "valid_splits": res["valid_splits"],
                "mean_ic_oos_sign": "+" if res["mean_ic_oos"] > 0 else "-",
            })
    sign_prior_eligible[sub] = eligible
    print(f"\n  [{sub}] walk-forward sign-prior eligible = {len(eligible)} / {len(cells)} specs")

(OUT / "_sign_prior_eligible_v5.json").write_text(json.dumps(sign_prior_eligible, indent=2))
print(f"\n[DONE] walk-forward + KW-vs-ACM v5 → {OUT}")
