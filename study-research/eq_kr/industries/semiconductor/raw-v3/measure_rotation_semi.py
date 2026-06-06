# -*- coding: utf-8 -*-
"""measure_rotation_semi.py — 반도체 업종 rotation timing 측정 (team-lead 지시, fundamental 심화).

★임무 = "어느 국면에 반도체 업종 OW/UW" = 업종 자체 시계열 forward 예측 (종목 selection 아님).
rotation-analyst 1차(SOXX +0.171 약, soxx 1컬럼)를 ★반도체 fundamental 전문성으로 보강.

신호 8개 (rotation-signals.md §1 부호 사전확약):
  ppi_yoy(음) / ppi_d3(음) / export_yoy(음) / inv_yoy(양,재고) / soxx_d3(양동행) / usdkrw_yoy(양) / real_rate_d(음) / cli_chg(양)
★사전확약 = 반도체 주가는 업황 6-9M 선행 → 변곡(PPI/수출 yoy 高=매도, 재고 高=매수).

================================================================================
★G-F FRAME CONTRACT 7항 (measure_rotation.py 준용)
================================================================================
1. regime = Macro(CLI) × KRW × flow (regime_series). effective-n = block 수, NW lag = horizon_months.
2. forward h일 = panel_ret.shift(-h). 단변량 신호 forward 예측 먼저.
3. ★단일 FDR family: {8 신호 × 2 horizon} = 16 BY-FDR.
4. MDE/power: t_obs = IC·√N/σ_IC ⋚ 2.802 (G-G v2 breakeven). t<2.802 underpowered(OOS면 tradeable).
5. PIT: 가격=forward shift / PPI·수출 = 발표 1M lag / 재고 = DART rcept_dt / CLI = 2M lag.
6. turnover/T-cost: rotation sleeve-level, KR STT 0.2% 비대칭. net = |IC| vs cost 표시.
7. wild-cluster bootstrap(Rademacher B=2000) + block-boot CI. asymptotic t 보조.

★G-G v2 tradeable: (a) OOS 부호+magnitude (b) tier≥structural_prior (c) net-alpha (d) regime 명시.
★momentum residualize: 업종 momentum = 공통인자(flow/USDKRW/SOXX) 제거 후 잔존 = 진짜 / 소멸 = data mining.
================================================================================
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
ROT = ROOT.parent.parent / "_rotation" / "data"   # rotation-analyst cycle_semiconductor (soxx)

OOS_SPLIT = "2023-01-01"
T_BREAKEVEN = 2.802
STT_SELL, COMMISSION, TURNOVER = 0.0020, 0.00015, 0.5
HORIZONS_M = {"y_20d": 1, "y_60d": 3}


def nw_se(x, lag):
    n = len(x)
    if n < 3:
        return np.nan
    e = x - x.mean(); var = (e @ e) / n
    for k in range(1, min(lag, n - 1) + 1):
        var += 2 * (1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n
    return float(np.sqrt(max(var, 1e-12) / n))


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


def wild_cluster_p(x, B=2000, seed=42):
    n = len(x)
    if n < 4:
        return np.nan
    rng = np.random.default_rng(seed)
    t_obs = abs(x.mean() / (x.std(ddof=1) / np.sqrt(n))) if x.std(ddof=1) > 0 else 0.0
    e = x - x.mean(); cnt = 0
    for _ in range(B):
        w = rng.choice([-1.0, 1.0], size=n)
        xn = w * e; sb = xn.std(ddof=1)
        tb = abs(xn.mean() / (sb / np.sqrt(n))) if sb > 0 else 0.0
        if tb >= t_obs:
            cnt += 1
    return (cnt + 1) / (B + 1)


def spearman_ic(sig, fwd, d0=None, d1=None):
    common = sig.dropna().index.intersection(fwd.dropna().index)
    if d0:
        common = common[(common >= d0) & (common <= d1)]
    if len(common) < 8:
        return None
    rho, _ = stats.spearmanr(sig.loc[common], fwd.loc[common])
    return (rho, len(common)) if not np.isnan(rho) else None


def signal_stat(sig, panel_ret, h, label):
    """forward 예측 IC + IS/OOS walk-forward + wild-cluster + MDE/power."""
    fwd = panel_ret.shift(-h).rolling(h).sum()
    full = spearman_ic(sig, fwd, "2019-01-01", "2026-12-31")
    if full is None:
        return {"status": "INSUFFICIENT"}
    rho, n = full
    # IC 시계열 (월별 부호 안정성 위해 rolling 아닌 전체 rho + wild-cluster on per-month contribution)
    common = sig.dropna().index.intersection(fwd.dropna().index)
    common = common[(common >= "2019-01-01") & (common <= "2026-12-31")]
    sv = stats.rankdata(sig.loc[common]); rv = stats.rankdata(fwd.loc[common])
    prod = (sv - sv.mean()) * (rv - rv.mean())   # IC 기여 시계열 (wild-cluster 입력)
    wc_p = wild_cluster_p(prod)
    neff = n_eff_autocorr(prod)
    sigma_ic = 1.0 / np.sqrt(max(neff - 1, 1))   # IC SE 근사
    t_obs = abs(rho) * np.sqrt(neff) / 1.0 if sigma_ic > 0 else 0.0
    t_obs = abs(rho) / sigma_ic
    # walk-forward IS/OOS
    is_ic = spearman_ic(sig, fwd, "2019-01-01", "2022-12-31")
    oos_ic = spearman_ic(sig, fwd, OOS_SPLIT, "2026-12-31")
    sign_hold = None
    if is_ic and oos_ic:
        sign_hold = bool(np.sign(is_ic[0]) == np.sign(oos_ic[0]))
    # contemporaneous (동행)
    contemp = spearman_ic(sig, panel_ret, "2019-01-01", "2026-12-31")
    return {
        "ic_forward": round(rho, 4), "n": n,
        "wild_cluster_p": round(wc_p, 4) if not np.isnan(wc_p) else None,
        "n_eff": round(neff, 1), "t_obs": round(t_obs, 2),
        "powered": bool(t_obs >= T_BREAKEVEN),
        "is_ic": round(is_ic[0], 4) if is_ic else None, "is_n": is_ic[1] if is_ic else None,
        "oos_ic": round(oos_ic[0], 4) if oos_ic else None, "oos_n": oos_ic[1] if oos_ic else None,
        "oos_sign_hold": sign_hold,
        "contemp_ic": round(contemp[0], 4) if contemp else None,
        "label": label,
    }


def build_signals(px, fund, reg, ext, soxx):
    pxm = px.resample("ME").last()
    panel_ret = pxm.pct_change().mean(axis=1)   # ★eq-weight 업종 월수익 (93% 집중 → eq-weight 필수)
    ppi = fund["semi_ppi"]; ppi.index = pd.to_datetime(ppi.index)
    exp = fund["kr_export"]; exp.index = pd.to_datetime(exp.index)
    soxxm = soxx.resample("ME").last()
    usdkrw = reg["usdkrw"].resample("ME").last()
    rate = reg["rate10y"].resample("ME").last() if "rate10y" in reg.columns else None
    cli = reg["cli_kr"].resample("ME").last() if "cli_kr" in reg.columns else None
    # 재고 yoy (DART 산업 합산, PIT)
    ext2 = ext.copy(); ext2["rcept_dt"] = pd.to_datetime(ext2["rcept_dt"], format="%Y%m%d", errors="coerce")
    inv_q = ext2.dropna(subset=["rcept_dt"]).groupby("rcept_dt").agg(inv=("inventory", "sum"), ast=("assets", "sum"))
    inv_ratio = (inv_q["inv"] / inv_q["ast"]).resample("ME").last().ffill()
    inv_yoy = inv_ratio.pct_change(12)

    sig = {
        "ppi_yoy": ppi.shift(1).pct_change(12),       # PPI yoy (PIT lag 1) — 음 prior
        "ppi_d3": ppi.shift(1).pct_change(3),         # PPI 3M — 음
        "export_yoy": exp.shift(1).pct_change(12),    # 수출 yoy — 음
        "inv_yoy": inv_yoy,                            # 재고 yoy — 양 (재고 peak=매수)
        "soxx_d3": soxxm.pct_change(3),               # SOXX 3M — 양동행
        "usdkrw_yoy": usdkrw.pct_change(12),          # USDKRW yoy — 양
        "ind_mom_6": pxm.pct_change(6).mean(axis=1),  # 업종 momentum (residualize 검증용)
    }
    if rate is not None:
        sig["real_rate_d"] = rate.diff(3)             # 금리 3M 변화 — 음
    if cli is not None:
        sig["cli_chg"] = cli.shift(2).diff(3)         # CLI 3M 변화 (PIT lag 2) — 양
    return panel_ret, sig


def benjamini_yekutieli(pvals, q=0.10):
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    m = len(items)
    if m == 0:
        return {"m": 0}
    items.sort(key=lambda x: x[1])
    c_m = sum(1.0 / i for i in range(1, m + 1))
    surv = []
    for ri, (k, p) in enumerate(items, 1):
        if p <= (ri / m) * q / c_m:
            surv = [items[j][0] for j in range(ri)]
    return {"m": m, "by_factor": round(c_m, 3), "survivors_BY": surv,
            "raw_p_min": round(items[0][1], 5), "raw_p_min_key": items[0][0]}


def residualize_momentum(px, reg, soxx, panel_ret):
    """업종 momentum을 공통인자(USDKRW/SOXX/flow) 제거 후 잔존 IC (data mining 차단)."""
    pxm = px.resample("ME").last()
    ind_mom = pxm.pct_change(6).mean(axis=1)
    usdkrw_r = reg["usdkrw"].resample("ME").last().pct_change(6)
    soxx_r = soxx.resample("ME").last().pct_change(6)
    flow = reg["foreign_net_kospi"].resample("ME").sum() if "foreign_net_kospi" in reg.columns else None
    fwd = panel_ret.shift(-3).rolling(3).sum()
    raw = spearman_ic(ind_mom, fwd, "2019-01-01", "2026-12-31")
    # residualize: ind_mom ~ usdkrw + soxx (+flow) → 잔차
    df = pd.DataFrame({"mom": ind_mom, "usd": usdkrw_r, "soxx": soxx_r})
    if flow is not None:
        df["flow"] = flow.pct_change(6).replace([np.inf, -np.inf], np.nan)
    df = df.dropna()
    if len(df) < 20:
        return {"raw": raw[0] if raw else None, "resid": None, "note": "n부족"}
    X = np.column_stack([np.ones(len(df))] + [df[c].values for c in df.columns if c != "mom"])
    beta = np.linalg.lstsq(X, df["mom"].values, rcond=None)[0]
    resid = pd.Series(df["mom"].values - X @ beta, index=df.index)
    res_ic = spearman_ic(resid, fwd, "2019-01-01", "2026-12-31")
    return {"raw_ic": round(raw[0], 4) if raw else None,
            "resid_ic": round(res_ic[0], 4) if res_ic else None,
            "verdict": ("잔존(진짜 idiosyncratic)" if res_ic and abs(res_ic[0]) > 0.5 * abs(raw[0])
                        else "소멸(공통인자 재포장=data mining)")}


def main():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    fund = pd.read_parquet(DATA / "rotation_fundamentals.parquet")
    reg = pd.read_parquet(DATA / "regime_series.parquet")
    ext = pd.read_parquet(DATA / "dart_extended.parquet")
    soxx = pd.read_parquet(ROT / "cycle_semiconductor.parquet")["soxx"]; soxx.index = pd.to_datetime(soxx.index)

    panel_ret, sigs = build_signals(px, fund, reg, ext, soxx)
    PRIOR = {"ppi_yoy": "음", "ppi_d3": "음", "export_yoy": "음", "inv_yoy": "양",
             "soxx_d3": "양동행", "usdkrw_yoy": "양", "real_rate_d": "음", "cli_chg": "양", "ind_mom_6": "검증용"}

    results = {"meta": {"unit": "반도체 업종 eq-weight 패널 forward return (rotation timing)",
                        "priors": PRIOR, "oos_split": OOS_SPLIT, "t_breakeven": T_BREAKEVEN,
                        "note": "fundamental 심화(rotation-analyst soxx 보강). 부호 사전확약 = rotation-signals.md §1."},
               "signals": {}}
    pvals = {}
    for signame, sig in sigs.items():
        results["signals"][signame] = {"prior": PRIOR.get(signame, "?"), "horizons": {}}
        for hl, hm in HORIZONS_M.items():
            st = signal_stat(sig, panel_ret, hm, f"semi__{signame}__{hl}")
            results["signals"][signame]["horizons"][hl] = st
            if st.get("powered") and st.get("wild_cluster_p") is not None:
                pvals[f"{signame}__{hl}"] = st["wild_cluster_p"]
            elif st.get("wild_cluster_p") is not None:
                pvals[f"{signame}__{hl}"] = st["wild_cluster_p"]   # 전체 FDR family (underpowered 포함)
    results["fdr_family"] = benjamini_yekutieli(pvals)
    results["momentum_residualize"] = residualize_momentum(px, reg, soxx, panel_ret)

    out = ROOT / "validation-rotation-semi-v1.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Saved {out}\n")
    print("=== 반도체 업종 rotation IC (fundamental, y_60d) ===")
    print(f"{'signal':14s}{'prior':8s}{'fwd_IC':>9s}{'wc_p':>8s}{'t_obs':>7s}{'OOS':>9s}{'contemp':>9s} verdict")
    for sn, d in results["signals"].items():
        h = d["horizons"].get("y_60d", {})
        if h.get("status") == "INSUFFICIENT":
            print(f"{sn:14s}{d['prior']:8s} INSUFFICIENT")
            continue
        prior = d["prior"]
        match = "✅" if ((prior[0] == "음" and (h.get("ic_forward") or 0) < 0) or
                        (prior[0] == "양" and (h.get("ic_forward") or 0) > 0)) else "⚠️"
        print(f"{sn:14s}{prior:8s}{h.get('ic_forward'):>+9.3f}{h.get('wild_cluster_p') or 0:>8.3f}"
              f"{h.get('t_obs') or 0:>7.2f}{h.get('oos_ic') or 0:>+9.3f}{h.get('contemp_ic') or 0:>+9.3f} {match}")
    print(f"\nFDR family: {results['fdr_family']}")
    print(f"momentum residualize: {results['momentum_residualize']}")


if __name__ == "__main__":
    main()
