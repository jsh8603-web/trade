# -*- coding: utf-8 -*-
"""measure_critique.py — auto 비판검토 데이터 직접 검정 (S4/S5, frame K축 무비판채택 차단).

★검정 2종 (반도체 §5.1 미러 + 자동차 핵심신호 capex/pbr 대상):
  Q6: PBR/capex value premium 이 Size factor 위장 아닌가? → Fama-MacBeth (Return ~ signal_rank + Size_rank)
  Q-capex: capex_ratio (asset growth) 가 size·value 와 독립 alpha 인가? → 다변량 통제

방법 = month-by-month cross-sectional 회귀(Fama-MacBeth 1973) → 시계열 평균 β + NW-HAC t.
산출: validation-critique-v3.json
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
import importlib.util

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("mc", str(ROOT / "measure_conditional.py"))
mc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mc)
import os
sys.stdout = io.TextIOWrapper(io.FileIO(os.dup(1), "w"), encoding="utf-8", write_through=True)
DATA = ROOT / "data"


def nw_se(x, lag):
    n = len(x)
    if n < 3:
        return np.nan
    e = x - x.mean(); var = (e @ e) / n
    for k in range(1, min(lag, n - 1) + 1):
        var += 2 * (1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n
    return float(np.sqrt(max(var, 1e-12) / n))


def build_capex_panel(px, monthly_idx):
    ext = pd.read_parquet(DATA / "dart_extended.parquet").copy()
    ext["rcept_dt"] = pd.to_datetime(ext["rcept_dt"], format="%Y%m%d", errors="coerce")
    ext = ext.dropna(subset=["rcept_dt"])
    panel = {}
    for code in px.columns:
        cf = ext[ext["code"] == code].sort_values("rcept_dt").drop_duplicates("rcept_dt", keep="last")
        if len(cf) < 4:
            continue
        s = pd.Series(index=monthly_idx, dtype=float)
        for dt in monthly_idx:
            av = cf[cf["rcept_dt"] <= dt]
            if len(av) == 0:
                continue
            last = av.iloc[-1]
            a, p = last.get("assets"), last.get("ppe")
            if a and a > 0 and pd.notna(p):
                s[dt] = p / a
        panel[code] = s
    return mc.csz(pd.DataFrame(panel))


def fama_macbeth(sig_panels: dict, fwd: pd.DataFrame, size_panel: pd.DataFrame, h_months: int):
    """month-by-month cross-sectional 회귀: ret_rank ~ Σ sig_rank. Fama-MacBeth 평균 β + NW t."""
    betas = {k: [] for k in list(sig_panels.keys()) + ["size"]}
    common_idx = fwd.index
    for sp in sig_panels.values():
        common_idx = common_idx.intersection(sp.index)
    common_idx = common_idx.intersection(size_panel.index)
    n_months = 0
    for dt in common_idx:
        rv = fwd.loc[dt].dropna()
        cols = set(rv.index)
        sig_vals = {}
        ok = True
        for k, sp in sig_panels.items():
            v = sp.loc[dt].dropna()
            cols &= set(v.index); sig_vals[k] = v
        sv_size = size_panel.loc[dt].dropna(); cols &= set(sv_size.index)
        cols = sorted(cols)
        if len(cols) < 8:
            continue
        # rank-normalize
        y = stats.rankdata(rv.loc[cols]) / len(cols) - 0.5
        X = [np.ones(len(cols))]
        names = []
        for k, v in sig_vals.items():
            X.append(stats.rankdata(v.loc[cols]) / len(cols) - 0.5); names.append(k)
        X.append(stats.rankdata(sv_size.loc[cols]) / len(cols) - 0.5); names.append("size")
        X = np.column_stack(X)
        try:
            b = np.linalg.lstsq(X, y, rcond=None)[0]
        except Exception:
            continue
        for i, nm in enumerate(names):
            betas[nm].append(b[i + 1])
        n_months += 1
    out = {}
    for k, bl in betas.items():
        if len(bl) < 4:
            continue
        arr = np.array(bl); m = arr.mean(); se = nw_se(arr, h_months)
        out[k] = {"beta_mean": round(m, 4), "t_nw": round(m / se, 2) if se else None, "n_months": len(bl)}
    out["_n_months"] = n_months
    return out


def main():
    px, lab, fin, uni = mc.load()
    pxm = px.resample("ME").last()
    val_sigs = mc.build_valuation_signals(px, fin, uni)
    pbr = val_sigs["pbr_z"]
    capex = build_capex_panel(px, pxm.index)
    # size = ln(marketcap) proxy = ln(price * shares근사). 단순화: ln(price)*  but cross-sectional size = ln Marcap.
    # Marcap 시점추정 = px * (uni Marcap / last px). size panel = ln(mktcap).
    shares = {}
    for code in px.columns:
        lp = px[code].dropna()
        if len(lp) and code in uni.index:
            mc_v = uni.loc[code, "Marcap"]
            if pd.notna(mc_v) and lp.iloc[-1] > 0:
                shares[code] = mc_v / lp.iloc[-1]
    size_panel = {}
    for code in px.columns:
        if code in shares:
            size_panel[code] = np.log(pxm[code] * shares[code])
    size_panel = mc.csz(pd.DataFrame(size_panel))

    anchor = pbr.dropna(how="all").index
    results = {"meta": {"method": "Fama-MacBeth 1973 month-by-month cross-sectional, rank-normalized, NW-HAC t",
                        "purpose": "Q6 PBR/capex value premium = size 위장 아닌지 + capex 독립 alpha 검정"},
               "tests": {}}
    for hname, h in [("y_20d", 20), ("y_60d", 60)]:
        fwd = mc.forward_returns_daily(px, anchor, h)
        h_m = max(1, round(h / 21))
        # (1) PBR univariate vs PBR|Size
        uni_pbr = fama_macbeth({"pbr": pbr}, fwd, size_panel, h_m)
        # (2) capex univariate vs capex|size|pbr 다변량
        uni_capex = fama_macbeth({"capex": capex}, fwd, size_panel, h_m)
        multi = fama_macbeth({"pbr": pbr, "capex": capex}, fwd, size_panel, h_m)
        results["tests"][hname] = {
            "pbr_plus_size": uni_pbr,
            "capex_plus_size": uni_capex,
            "pbr_capex_size_multivariate": multi,
        }
        print(f"=== {hname} ===")
        print(f"  PBR|Size:   pbr b={uni_pbr.get('pbr',{}).get('beta_mean')} t={uni_pbr.get('pbr',{}).get('t_nw')} / size b={uni_pbr.get('size',{}).get('beta_mean')} t={uni_pbr.get('size',{}).get('t_nw')}")
        print(f"  capex|Size: capex b={uni_capex.get('capex',{}).get('beta_mean')} t={uni_capex.get('capex',{}).get('t_nw')} / size b={uni_capex.get('size',{}).get('beta_mean')} t={uni_capex.get('size',{}).get('t_nw')}")
        m = multi
        print(f"  multi(pbr+capex+size): pbr b={m.get('pbr',{}).get('beta_mean')} t={m.get('pbr',{}).get('t_nw')} / capex b={m.get('capex',{}).get('beta_mean')} t={m.get('capex',{}).get('t_nw')} / size b={m.get('size',{}).get('beta_mean')} t={m.get('size',{}).get('t_nw')}")

    (ROOT / "validation-critique-v3.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("\nSaved validation-critique-v3.json")


if __name__ == "__main__":
    main()
