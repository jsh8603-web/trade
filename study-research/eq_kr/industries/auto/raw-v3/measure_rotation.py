# -*- coding: utf-8 -*-
"""measure_rotation.py — auto 업종 rotation 신호 측정 (v2 baseline 심화).

★종목 selection(capex/PBR) 과 별개 = 업종 자체 OW/UW timing.
측정 = corr(거시 driver, 자동차 업종 eq-weight forward return). v2 방법론 미러.

신호 (theory: /tmp/auto-rotation-result.txt 부호 사전확약):
  - global_auto_d3   : CARZ 3M 변화율 (★v2 baseline STRONG, 양 prior) — 재검증
  - global_auto_yoy  : CARZ yoy (양 prior, v2 약)
  - usdkrw_d3        : USDKRW 3M 변화율 (수출채산, 양 prior)
  - cli_chg6         : 한국 CLI 6M 변화 (early-cycle, 양 prior)
  - dgs2_d3          : 미국 2년물 3M 변화 (할부수요, ★음 prior)
  - jpykrw_d3        : 엔/원 3M 변화 (한국 경쟁력, ★음 prior = 엔원 하락 시 OW)
  - iron_ore_d3      : 철광석 3M 변화 (원가, ★음 prior)

G-G v2: eq-weight forward(y_20d/y_60d) + wild-cluster p + walk-forward OOS(2023-01 split)
        + n_eff(autocorr) + block-boot CI + 단일 FDR family + placebo.
산출: validation-rotation-auto-v1.json + rotation-signals.md(별).
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
ROT = ROOT.parent.parent / "_rotation" / "data"   # _rotation cycle parquet
OOS_SPLIT = "2023-01-01"
HORIZONS_M = {"y_20d": 1, "y_60d": 3}


def wild_cluster_p(x, B=2000, seed=42):
    n = len(x)
    if n < 4:
        return np.nan
    rng = np.random.default_rng(seed)
    sd = x.std(ddof=1)
    t_obs = abs(x.mean() / (sd / np.sqrt(n))) if sd > 0 else 0.0
    e = x - x.mean(); cnt = 0
    for _ in range(B):
        w = rng.choice([-1.0, 1.0], size=n)
        xn = w * e; sb = xn.std(ddof=1)
        tb = abs(xn.mean() / (sb / np.sqrt(n))) if sb > 0 else 0.0
        if tb >= t_obs:
            cnt += 1
    return (cnt + 1) / (B + 1)


def n_eff_autocorr(x, max_lag=12):
    n = len(x)
    if n < 4:
        return float(n)
    e = x - x.mean(); v = (e @ e) / n
    if v <= 0:
        return float(n)
    s = 0.0
    for k in range(1, min(max_lag, n - 1) + 1):
        rk = (e[k:] @ e[:-k]) / n / v
        if rk <= 0:
            break
        s += (1 - k / (max_lag + 1)) * rk
    return float(n / (1 + 2 * s))


def block_boot_ci(x, block, B=2000, seed=42):
    rng = np.random.default_rng(seed); n = len(x)
    if n < block + 1:
        return [np.nan, np.nan]
    nb = int(np.ceil(n / block)); means = []
    for _ in range(B):
        st = rng.integers(0, n - block + 1, size=nb)
        means.append(np.concatenate([x[s:s + block] for s in st])[:n].mean())
    return [round(float(np.percentile(means, 2.5)), 5), round(float(np.percentile(means, 97.5)), 5)]


def rho_series(sig, fwd, min_overlap=20):
    """월별 정렬 후 시계열 Spearman (rolling 아님, 전체 표본 1 corr) — rotation = time-series predictive.
    단 rotation 은 cross-sectional 아닌 time-series: sig(t) vs fwd(t) 전체 corr."""
    common = sig.index.intersection(fwd.index)
    s = sig.reindex(common); f = fwd.reindex(common)
    df = pd.concat([s, f], axis=1).dropna()
    if len(df) < min_overlap:
        return None
    rho, _ = stats.spearmanr(df.iloc[:, 0], df.iloc[:, 1])
    return df, rho


def signal_stat(sig, fwd, hm, label):
    """rotation time-series stat: sig(t) → fwd return(t). v2 signal_forward_stat 미러."""
    res = rho_series(sig, fwd)
    if res is None:
        return {"label": label, "status": "INSUFFICIENT"}
    df, rho = res
    n = len(df)
    # forward overlap 자기상관 보정: monthly sample 의 IC 시계열 아닌 (sig,fwd) pair →
    # block bootstrap on the paired series rank-products
    sr = stats.rankdata(df.iloc[:, 0]) / n - 0.5
    fr = stats.rankdata(df.iloc[:, 1]) / n - 0.5
    prod = sr * fr   # rank-product = per-obs IC contribution
    neff = n_eff_autocorr(prod, max_lag=12)
    wc_p = wild_cluster_p(prod)
    ci = block_boot_ci(prod, block=max(2, hm))
    # MDE/power (effective-n 기반)
    mde = 2.802 / np.sqrt(max(neff, 1))   # t_breakeven=2.802 (v2) 기준 detectable rho 근사
    t_power = abs(rho) * np.sqrt(max(neff, 1))
    # walk-forward OOS
    is_df = df[df.index < OOS_SPLIT]; oos_df = df[df.index >= OOS_SPLIT]
    wf = {"eligible": False}
    if len(is_df) >= 12 and len(oos_df) >= 12:
        ris = stats.spearmanr(is_df.iloc[:, 0], is_df.iloc[:, 1])[0]
        ros = stats.spearmanr(oos_df.iloc[:, 0], oos_df.iloc[:, 1])[0]
        wf = {"is_n": len(is_df), "oos_n": len(oos_df), "rho_is": round(float(ris), 4),
              "rho_oos": round(float(ros), 4), "eligible": True,
              "verdict": "OOS 부호+mag 유지" if (np.sign(ris) == np.sign(ros) and abs(ros) >= abs(ris) * 0.5)
                         else ("OOS 부호유지(약화)" if np.sign(ris) == np.sign(ros) else "OOS flip")}
    powered = (n >= 24) and (neff >= 6)
    return {"label": label, "n": n, "n_eff": round(neff, 1), "spearman_rho": round(float(rho), 4),
            "t_power_mde": round(float(t_power), 2), "mde_rho": round(float(mde), 3),
            "wild_cluster_p": round(float(wc_p), 4) if not np.isnan(wc_p) else None,
            "ci95_block_boot": ci, "walk_forward_oos": wf,
            "status": "powered" if powered else ("underpowered" if n >= 12 else "INSUFFICIENT")}


def build_auto_panel_eqw():
    """자동차 17종 eq-weight 업종 cum return (v2 방식: 월간 수익 eq-weight)."""
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    pxm = px.resample("ME").last()
    ret = pxm.pct_change()
    eqw_ret = ret.mean(axis=1)   # eq-weight 업종 월수익
    cum = (1 + eqw_ret.fillna(0)).cumprod()
    return cum


def main():
    cum = build_auto_panel_eqw()
    # ── 거시 driver 월말 ──
    reg = pd.read_parquet(DATA / "regime_series.parquet"); reg.index = pd.to_datetime(reg.index)
    regm = reg.resample("ME").last()
    carz = pd.read_parquet(ROT / "cycle_auto.parquet"); carz.index = pd.to_datetime(carz.index)
    carzm = carz.resample("ME").last()["global_auto"]
    iron = pd.read_parquet(ROT / "cycle_steel.parquet"); iron.index = pd.to_datetime(iron.index)
    ironm = iron.resample("ME").last()["iron_ore"]
    rmac = pd.read_parquet(DATA / "rotation_macro.parquet"); rmac.index = pd.to_datetime(rmac.index)
    rmacm = rmac.resample("ME").last()

    signals = {
        "global_auto_d3": carzm.pct_change(3),                  # ★v2 baseline 양
        "global_auto_yoy": carzm.pct_change(12),                # 양 (v2 약)
        "usdkrw_d3": regm["usdkrw"].pct_change(3),              # 수출채산 양
        "cli_chg6": regm["cli_kr"] - regm["cli_kr"].shift(6),   # early-cycle 양
        "dgs2_d3": rmacm["dgs2"] - rmacm["dgs2"].shift(3),      # 할부수요 음
        "jpykrw_d3": rmacm["jpykrw"].pct_change(3),             # 한국 경쟁력 음(엔원 하락=OW)
        "iron_ore_d3": ironm.pct_change(3),                     # 원가 음
    }
    PRIOR = {"global_auto_d3": "양", "global_auto_yoy": "양", "usdkrw_d3": "양", "cli_chg6": "양",
             "dgs2_d3": "음", "jpykrw_d3": "음", "iron_ore_d3": "음"}

    results = {"meta": {
        "method": "auto 업종 eq-weight(17종) forward return vs 거시 driver time-series Spearman. v2 rotation 방법론 미러.",
        "unit": "★종목 selection 아닌 업종 OW/UW timing (rotation)",
        "theory_source": "/tmp/auto-rotation-result.txt (Gemini, P-Q-C 프레임워크 + Stovall early-cycle)",
        "priors": PRIOR, "horizons_months": HORIZONS_M, "oos_split": OOS_SPLIT,
        "v2_baseline": "global_auto_d3 = v2 STRONG (y_20d rho=0.222 wc_p=0.0335 / y_60d 0.261 wc_p=0.0245). 본 측정 = 재검증 + 고유 driver 심화.",
    }, "signals": {}}
    pvals = {}
    for sname, sig in signals.items():
        sig = sig.loc["2019-01-01":]
        results["signals"][sname] = {"prior_부호": PRIOR[sname], "horizons": {}}
        for hl, hm in HORIZONS_M.items():
            fwd = cum.pct_change(hm).shift(-hm)
            st = signal_stat(sig, fwd, hm, f"auto_rot_{sname}__{hl}")
            results["signals"][sname]["horizons"][hl] = st
            if st.get("status") == "powered" and st.get("wild_cluster_p") is not None:
                pvals[f"{sname}__{hl}"] = st["wild_cluster_p"]

    # ── 단일 FDR family (BY) ──
    items = sorted([(k, v) for k, v in pvals.items() if v is not None], key=lambda x: x[1])
    m = len(items)
    surv = []
    if m:
        c_m = sum(1.0 / i for i in range(1, m + 1))
        for ri, (k, p) in enumerate(items, 1):
            if p <= (ri / m) * 0.10 / c_m:
                surv = [items[j][0] for j in range(ri)]
    results["fdr_family"] = {"m": m, "by_factor": round(c_m, 3) if m else None,
                             "survivors_BY": surv, "raw_p_min": items[0][1] if m else None,
                             "raw_p_min_key": items[0][0] if m else None}

    # ── placebo: shuffle driver → IC 분포 (1 신호 데모) ──
    rng = np.random.default_rng(7)
    g = signals["global_auto_d3"].loc["2019-01-01":]
    fwd = cum.pct_change(1).shift(-1)
    res = rho_series(g, fwd)
    placebo_rhos = []
    if res is not None:
        df, real_rho = res
        for _ in range(500):
            perm = df.iloc[:, 0].sample(frac=1, random_state=rng.integers(1e6)).values
            placebo_rhos.append(stats.spearmanr(perm, df.iloc[:, 1])[0])
        pct = float((np.abs(placebo_rhos) >= abs(real_rho)).mean())
        results["placebo_global_auto_d3_y20d"] = {"real_rho": round(real_rho, 4),
            "placebo_exceed_frac": round(pct, 4), "n_perm": 500,
            "verdict": "placebo 통과 (real > 95% shuffle)" if pct < 0.05 else "placebo 미통과(우연 가능)"}

    out = ROOT / "validation-rotation-auto-v1.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Saved {out}\n")
    print("=== auto 업종 rotation 신호 (eq-weight forward) ===")
    print(f"{'signal':18s}{'prior':5s} {'h':6s} {'rho':>8s} {'wc_p':>7s} {'n_eff':>6s} {'OOS_is':>8s}{'OOS_oos':>8s} {'verdict'}")
    for sname, d in results["signals"].items():
        for hl, st in d["horizons"].items():
            if st.get("status") == "INSUFFICIENT":
                continue
            wf = st.get("walk_forward_oos", {})
            print(f"{sname:18s}{d['prior_부호']:5s} {hl:6s} {st['spearman_rho']:+8.4f} {str(st['wild_cluster_p']):>7s} "
                  f"{st['n_eff']:>6} {str(wf.get('rho_is','-')):>8}{str(wf.get('rho_oos','-')):>8} {wf.get('verdict','')}")
    print(f"\nFDR family: m={results['fdr_family']['m']} survivors={results['fdr_family']['survivors_BY']} "
          f"raw_p_min={results['fdr_family']['raw_p_min']}({results['fdr_family']['raw_p_min_key']})")
    if "placebo_global_auto_d3_y20d" in results:
        print(f"placebo: {results['placebo_global_auto_d3_y20d']}")


if __name__ == "__main__":
    main()
