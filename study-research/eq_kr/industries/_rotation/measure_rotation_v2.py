# -*- coding: utf-8 -*-
"""measure_rotation_v2.py — rotation 보강 측정 (자문 2R 확정 spec, 신호 위계 반영).

★자문 결론 A = 고유 cycle 직접신호 = primary alpha / momentum·rel_mom = secondary(강등, 공통인자 재포장 위험)
  / valuation band = tertiary(structural-break guard, chemical만 일관).
★자문 Q-a = intermediate(6-12m) momentum = flow persistence 오염 → ★공통인자 residualize 후 부호 재측정 의무.
★자문 §4 본인검증 = (1) 36셀 N<24 collapse 비율 실측 (2) residual N_eff(participation ratio) vs raw N_eff.

================================================================================
★G-F FRAME CONTRACT 7항 (measure_rotation.py 준용)
1. regime: Macro(CLI4)×KRW(3)×flow(3). eff-n=block. CLI/semi_ppi PIT lag(2/1).
2. interaction/split: forward h = shift(-h). ★공통인자 residualize order 명시(아래 §residualize).
3. 단일 FDR family: {고유cycle + momentum(residualized) + valband} × 12산업 × horizon. BY(hierarchical=S6/S7).
4. null+MDE/power: t_obs=|IC|·√n_eff ⋚ 2.802. underpowered=gated default.
5. PIT: cycle spot=실시간(lag X). 가격=forward shift. valuation=DART rcept_dt.
6. turnover/T-cost: KR STT 0.2% 비대칭. cost-aware no-trade(통합).
7. per-test: wild-cluster(Rademacher B=2000) + block-boot CI + eff-N autocorr.
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
IND_ROOT = ROOT.parent
DATA = ROOT / "data"
INDUSTRIES = ["semiconductor", "auto", "financial", "battery", "chemical", "refining",
              "shipbuilding", "steel", "bio", "consumer", "telecom", "aitech"]
HORIZONS_M = {"y_20d": 1, "y_60d": 3}
OOS_SPLIT = "2023-01-01"
T_BREAKEVEN = 2.802
CLI_PUB_LAG = 2
SEMI_PPI_LAG = 1

# 산업 고유 cycle parquet (collect_industry_cycle.py 산출) + 기존 capsule cycle
CYCLE_FILES = {
    "steel": DATA / "cycle_steel.parquet",
    "battery": DATA / "cycle_battery.parquet",
    "chemical": DATA / "cycle_chemical.parquet",
    "auto": DATA / "cycle_auto.parquet",
    "shipbuilding": DATA / "cycle_shipbuilding.parquet",
    "semiconductor": DATA / "cycle_semiconductor.parquet",
    "refining": IND_ROOT / "refining" / "raw-v3" / "data" / "refining_cycle.parquet",
}
# 고유 cycle 직접 부재 = momentum proxy 유지 (한계 박제)
NO_DIRECT = {"telecom", "financial", "bio", "consumer"}


# ──────── 통계 인프라 (measure_rotation.py 동일) ────────
def nw_se(x, lag):
    n = len(x)
    if n < 3: return np.nan
    e = x - x.mean(); var = (e @ e) / n
    for k in range(1, min(lag, n - 1) + 1):
        var += 2 * (1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n
    return float(np.sqrt(max(var, 1e-12) / n))


def n_eff_autocorr(x, max_lag=12):
    n = len(x)
    if n < 4: return float(n)
    e = x - x.mean(); v = (e @ e) / n
    if v <= 0: return float(n)
    s = 0.0
    for k in range(1, min(max_lag, n - 1) + 1):
        rk = (e[k:] @ e[:-k]) / n / v
        if rk <= 0: break
        s += (1 - k / (max_lag + 1)) * rk
    return float(n / (1 + 2 * s))


def wild_cluster_p(x, B=2000, seed=42):
    n = len(x)
    if n < 4: return np.nan
    rng = np.random.default_rng(seed); sd = x.std(ddof=1)
    t_obs = abs(x.mean() / (sd / np.sqrt(n))) if sd > 0 else 0.0
    e = x - x.mean(); cnt = 0
    for _ in range(B):
        w = rng.choice([-1.0, 1.0], size=n); xn = w * e; sb = xn.std(ddof=1)
        tb = abs(xn.mean() / (sb / np.sqrt(n))) if sb > 0 else 0.0
        if tb >= t_obs: cnt += 1
    return (cnt + 1) / (B + 1)


def block_boot_ci(x, block, B=2000, seed=42):
    rng = np.random.default_rng(seed); n = len(x)
    if n < block + 1: return [np.nan, np.nan]
    nb = int(np.ceil(n / block)); means = []
    for _ in range(B):
        st = rng.integers(0, n - block + 1, size=nb)
        means.append(np.concatenate([x[s:s + block] for s in st])[:n].mean())
    return [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


def benjamini_yekutieli(pvals, q=0.10):
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    m = len(items)
    if m == 0: return {"m": 0, "note": "powered cell 0"}
    items.sort(key=lambda x: x[1])
    c_m = sum(1.0 / i for i in range(1, m + 1)); surv = []
    for ri, (k, p) in enumerate(items, 1):
        if p <= (ri / m) * q / c_m: surv = [items[j][0] for j in range(ri)]
    return {"m": m, "by_factor": round(c_m, 3), "survivors_BY": surv,
            "raw_p_min": round(items[0][1], 5), "raw_p_min_key": items[0][0], "bonferroni_alpha": round(0.05 / m, 5)}


def signal_forward_stat(sig, fwd, h_months, label, oos_split=OOS_SPLIT):
    common = sig.dropna().index.intersection(fwd.dropna().index)
    if len(common) < 12:
        return {"label": label, "n": len(common), "status": "INSUFFICIENT(n<12)"}
    sv, fv = sig.loc[common].values, fwd.loc[common].values
    rho, p_param = stats.spearmanr(sv, fv)
    sr = stats.rankdata(sv) / len(sv) - 0.5; fr = stats.rankdata(fv) / len(fv) - 0.5
    prod = sr * fr; n = len(prod)
    neff = n_eff_autocorr(prod); se = nw_se(prod, h_months)
    t_nw = prod.mean() / se if se and se > 0 else np.nan
    wc_p = wild_cluster_p(prod); ci = block_boot_ci(prod, max(2, h_months))
    t_power = abs(rho) * np.sqrt(max(neff, 1.0))
    powered = (n >= 24) and (neff >= 6) and (t_power >= T_BREAKEVEN)
    is_idx = [d for d in common if str(d) < oos_split]; oos_idx = [d for d in common if str(d) >= oos_split]
    oos = {"is_n": len(is_idx), "oos_n": len(oos_idx)}
    if len(is_idx) >= 8 and len(oos_idx) >= 8:
        rho_is = stats.spearmanr(sig.loc[is_idx].values, fwd.loc[is_idx].values)[0]
        rho_oos = stats.spearmanr(sig.loc[oos_idx].values, fwd.loc[oos_idx].values)[0]
        oos.update({"rho_is": round(float(rho_is), 4), "rho_oos": round(float(rho_oos), 4)})
        sign_hold = (np.sign(rho_is) == np.sign(rho_oos)) and abs(rho_oos) >= 0.5 * abs(rho_is)
        oos["eligible"] = bool(sign_hold and abs(rho_oos) > 0.02)
        oos["verdict"] = ("OOS 부호+mag 유지" if sign_hold else
                          ("OOS 부호유지 mag약" if np.sign(rho_is) == np.sign(rho_oos) else "OOS flip"))
    else:
        oos["eligible"] = None; oos["verdict"] = "OOS n<8"
    return {"label": label, "n": n, "n_eff": round(neff, 1), "spearman_rho": round(float(rho), 4),
            "t_power_mde": round(float(t_power), 2),
            "wild_cluster_p": round(wc_p, 4) if not np.isnan(wc_p) else None,
            "ci95_block_boot_prod": [round(c, 5) for c in ci] if not np.isnan(ci[0]) else None,
            "walk_forward_oos": oos, "status": "powered" if powered else ("underpowered" if n >= 12 else "INSUFFICIENT")}


# ──────── 패널 + 신호 ────────
def load_industry(sector):
    d = IND_ROOT / sector / "raw-v3" / "data"
    px = pd.read_parquet(d / "prices.parquet"); px.index = pd.to_datetime(px.index)
    rs = pd.read_parquet(d / "regime_series.parquet"); rs.index = pd.to_datetime(rs.index)
    return px, rs


def panel_monthly_return(px):
    return px.resample("ME").last().pct_change().mean(axis=1, skipna=True)


def common_factors_monthly(rs):
    """공통 driver (residualize 용): usdkrw Δ + foreign flow + semi_ppi yoy (글로벌 cyclical)."""
    rsm = rs.resample("ME").last()
    F = pd.DataFrame(index=rsm.index)
    F["d_usdkrw"] = rsm["usdkrw"].pct_change()
    F["foreign"] = rsm["foreign_net_kospi"]
    if "semi_ppi" in rsm.columns:
        F["semi_ppi_yoy"] = rsm["semi_ppi"].shift(SEMI_PPI_LAG).pct_change(12)
    return F


def residualize(y: pd.Series, F: pd.DataFrame):
    """y(산업 패널 월수익)에서 공통인자 F 회귀 잔차 = idiosyncratic 성분 (자문 Q-a)."""
    common = y.dropna().index.intersection(F.dropna().index)
    if len(common) < 20:
        return y
    yy = y.loc[common].values
    X = np.column_stack([np.ones(len(common))] + [F.loc[common, c].values for c in F.columns])
    beta, *_ = np.linalg.lstsq(X, yy, rcond=None)
    resid = yy - X @ beta
    return pd.Series(resid, index=common)


def main():
    # 12산업 패널 + 공통인자
    all_panels, cache, Fmap = {}, {}, {}
    for s in INDUSTRIES:
        px, rs = load_industry(s); cache[s] = (px, rs)
        all_panels[s] = panel_monthly_return(px); Fmap[s] = common_factors_monthly(rs)
    all_panels = pd.DataFrame(all_panels)

    results = {"meta": {
        "method": "rotation 보강 v2 — 고유cycle(primary) + momentum residualized(secondary) + valband(tertiary)",
        "자문": "결론 A = 고유 cycle 직접신호=primary alpha, momentum 강등(공통인자 재포장 위험). RESULTS §2 Q-a",
        "signal_hierarchy": {"primary": "산업 고유 cycle 직접(yfinance proxy)", "secondary": "momentum/rel_mom (★공통인자 residualize 후 재측정)", "tertiary": "valuation band(별 스크립트)"},
        "residualize": "산업 패널 월수익 ~ {d_usdkrw, foreign_flow, semi_ppi_yoy} OLS 잔차 = idiosyncratic. order: 공통인자 먼저 제거 → 잔차 momentum",
        "horizons_months": HORIZONS_M, "oos_split": OOS_SPLIT, "t_breakeven": T_BREAKEVEN,
        "no_direct_cycle": list(NO_DIRECT),
    }, "industries": {}}
    fdr_primary, fdr_all = {}, {}

    for s in INDUSTRIES:
        px, rs = cache[s]
        pret = panel_monthly_return(px).loc["2019-01-01":]
        cum = (1 + pret.fillna(0)).cumprod()
        F = Fmap[s]
        # ── 공통인자 residualized 패널수익 (자문 Q-a) ──
        resid_ret = residualize(pret, F)
        resid_cum = (1 + resid_ret.fillna(0)).cumprod()

        sec = {"panel": {"n_months": int(pret.dropna().shape[0])}, "primary_cycle": {}, "secondary_momentum": {}}

        # ───── PRIMARY: 산업 고유 cycle 직접신호 ─────
        if s in CYCLE_FILES and CYCLE_FILES[s].exists():
            cyc = pd.read_parquet(CYCLE_FILES[s]); cyc.index = pd.to_datetime(cyc.index)
            cycm = cyc.resample("ME").last()
            for col in cyc.columns:
                base = cycm[col]
                # cycle 신호 변형: level yoy + Δ(모멘텀)
                sigs = {f"{col}_yoy": base.pct_change(12), f"{col}_d3": base.pct_change(3)}
                for signame, sigser in sigs.items():
                    sigser = sigser.loc["2019-01-01":]
                    for hl, hm in HORIZONS_M.items():
                        fwd = cum.pct_change(hm).shift(-hm)
                        st = signal_forward_stat(sigser, fwd, hm, f"{s}__cycle_{signame}__{hl}")
                        sec["primary_cycle"][f"{signame}__{hl}"] = st
                        if st.get("status") in ("powered", "underpowered") and st.get("wild_cluster_p") is not None:
                            fdr_all[f"{s}__cyc_{signame}__{hl}"] = st["wild_cluster_p"]
                            if st["walk_forward_oos"].get("eligible"):
                                fdr_primary[f"{s}__cyc_{signame}__{hl}"] = st["wild_cluster_p"]
        else:
            sec["primary_cycle"] = {"status": f"NO_DIRECT_CYCLE — {s} 고유 cycle 무료 부재(momentum proxy 유지, 이연 아님)"}

        # ───── SECONDARY: momentum (raw + ★residualized 비교, 자문 Q-a) ─────
        for tag, c in [("raw", cum), ("resid", resid_cum)]:
            for mname, lookback in [("mom_3", 3), ("mom_6", 6)]:
                sig = c.pct_change(lookback).loc["2019-01-01":]
                for hl, hm in HORIZONS_M.items():
                    fwd = cum.pct_change(hm).shift(-hm)
                    st = signal_forward_stat(sig, fwd, hm, f"{s}__mom_{tag}_{mname}__{hl}")
                    sec["secondary_momentum"][f"{tag}_{mname}__{hl}"] = st
                    if st.get("status") in ("powered", "underpowered") and st.get("wild_cluster_p") is not None:
                        fdr_all[f"{s}__mom_{tag}_{mname}__{hl}"] = st["wild_cluster_p"]
        results["industries"][s] = sec

    results["fdr_primary_cycle"] = benjamini_yekutieli(fdr_primary)
    results["fdr_all_single"] = benjamini_yekutieli(fdr_all)
    out = ROOT / "validation-rotation-v2.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Saved {out}\n")
    print_summary(results)
    return results


def print_summary(r):
    print("=" * 80)
    print("★PRIMARY: 산업 고유 cycle 직접신호 (OOS eligible + wc_p<0.10)")
    print("=" * 80)
    for s, sd in r["industries"].items():
        pc = sd.get("primary_cycle", {})
        if isinstance(pc, dict) and "status" in pc:
            print(f"  [{s}] {pc['status'][:60]}")
            continue
        rows = []
        for k, st in pc.items():
            if not isinstance(st, dict): continue
            oos = st.get("walk_forward_oos", {}); wcp = st.get("wild_cluster_p")
            if oos.get("eligible") and wcp is not None and wcp < 0.10:
                rows.append(f"    [Y]{k:22s} rho={st['spearman_rho']:+.3f} wc_p={wcp} OOS{oos.get('rho_is')}->{oos.get('rho_oos')} {st['status'][:4]}")
        if rows:
            print(f"  [{s}]"); print("\n".join(rows))
    print("\n" + "=" * 80)
    print("★SECONDARY: momentum raw vs residualized (자문 Q-a: residual 후 신호 잔존?)")
    print("=" * 80)
    for s, sd in r["industries"].items():
        for k, st in sd.get("secondary_momentum", {}).items():
            oos = st.get("walk_forward_oos", {}); wcp = st.get("wild_cluster_p")
            if oos.get("eligible") and wcp is not None and wcp < 0.10:
                tag = "resid" if "resid" in k else "raw  "
                print(f"  [{s:13s}] {k:22s} rho={st['spearman_rho']:+.3f} wc_p={wcp} OOS{oos.get('rho_is')}->{oos.get('rho_oos')}")
    print(f"\nFDR primary cycle: {json.dumps(r['fdr_primary_cycle'], ensure_ascii=False)}")
    print(f"FDR all single: {json.dumps(r['fdr_all_single'], ensure_ascii=False)}")


if __name__ == "__main__":
    main()
