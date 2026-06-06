# -*- coding: utf-8 -*-
"""measure_telecom.py — 통신 conditional IC (frame v3 §M + dispatch).

★통신 = 2 archetype 분리 (frame §1.6 분석unit 오염 차단):
  (A) 통신서비스(service) = SKT/KT/LGU+ ★3사 strict-pass = cross-sectional INSUFFICIENT(정유 패턴).
      → ★frame M2 산업 시계열 (3사 동일가중 월수익 vs KR금리[배당주 duration]/커브 regime conditional).
      통신 = defensive 고배당 bond-proxy → 금리 상승 디레이팅(duration 음) 가설.
  (B) 통신장비(equipment) = strict-pass 10종(≥8) = cross-sectional 가능.
      ★단 cyclical 이질 archetype (5G capex cycle). service 와 ★pool 금지(측정축·driver 본질차, 부호 cancel 아님).
      → equipment cross-sectional value/momentum conditional IC 별도 측정.

================================================================================
★G-F FRAME CONTRACT 7항
================================================================================
1. regime: Macro(CLI 4) × KRW(3) × flow(3) + ★rate regime(KR10Y Δ up/flat/down). eff-n=block 수(NW lag=h).
2. interaction/split: service=금리 duration 사전동결(음 prior). forward h일=shift(-h). equipment=value 음 prior.
3. 단일 FDR family: {service 시계열(rate/curve × horizon × powered regime) + equipment cross-sectional(value/mom × horizon)} 단일 BY-FDR.
4. null+MDE/power: null=corr 0. service n_months~88. equipment n_months×avgN. n_eff<6=inconclusive. t_obs⋚2.802 MDE.
5. PIT 동결: KR rate=FRED 월별(발표지연 ffill). 가격 forward=shift(-h). equipment 재무=DART rcept_dt 이후만.
6. turnover/T-cost: service=sleeve timing(종목선택 아님). equipment=cross-sectional KR STT 0.2% 비대칭 net.
7. per-test: small n → wild-cluster bootstrap(Rademacher B=2000) + block-boot CI. fixed-b 정신.

★합성 ⛔. 실 pykrx 가격 + FRED KR rate + DART. raw 재현 가능.
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

SERVICE = ["017670", "030200", "032640"]  # SKT / KT / LGU+
HORIZONS_D = {"y_5d": 5, "y_20d": 20, "y_60d": 60}


# ───────────────────────── stat machinery (refining 미러) ─────────────────────────
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


def block_boot_ci(x, block, B=2000, seed=42):
    rng = np.random.default_rng(seed); n = len(x)
    if n < block + 1:
        return [np.nan, np.nan]
    nb = int(np.ceil(n / block)); means = []
    for _ in range(B):
        st = rng.integers(0, n - block + 1, size=nb)
        means.append(np.concatenate([x[s:s + block] for s in st])[:n].mean())
    return [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


def adf_pvalue(s: pd.Series):
    """ADF 단위근 (statsmodels 있으면 사용, 없으면 None)."""
    try:
        from statsmodels.tsa.stattools import adfuller
        s = s.dropna()
        if len(s) < 12:
            return None
        return float(adfuller(s.values, regression="c", autolag="AIC")[1])
    except Exception:
        return None


def corr_stat(a: pd.Series, b: pd.Series, h_months: int, label: str):
    """두 시계열 Spearman corr + wild-cluster p + eff-N + block-boot CI."""
    common = a.dropna().index.intersection(b.dropna().index)
    if len(common) < 8:
        return {"label": label, "n": len(common), "status": "INSUFFICIENT(n<8)"}
    av, bv = a.loc[common].values, b.loc[common].values
    rho, p_param = stats.spearmanr(av, bv)
    ar = stats.rankdata(av) / len(av) - 0.5
    br = stats.rankdata(bv) / len(bv) - 0.5
    prod = ar * br
    n = len(prod)
    neff = n_eff_autocorr(prod)
    se = nw_se(prod, h_months)
    t_nw = prod.mean() / se if se and se > 0 else np.nan
    # eff-N 보정 t (autocorr 반영)
    t_eff = float(rho * np.sqrt(max(neff - 1, 1))) if not np.isnan(rho) else np.nan
    wc_p = wild_cluster_p(prod)
    ci = block_boot_ci(prod, max(2, h_months))
    powered = (n >= 24) and (neff >= 6)
    return {"label": label, "n": n, "n_eff": round(neff, 1),
            "spearman_rho": round(float(rho), 4), "p_parametric": round(float(p_param), 4),
            "t_nw_asymptotic": round(t_nw, 2) if not np.isnan(t_nw) else None,
            "t_eff_corrected": round(t_eff, 2) if not np.isnan(t_eff) else None,
            "wild_cluster_p": round(wc_p, 4) if not np.isnan(wc_p) else None,
            "ci95_block_boot_prod": [round(c, 5) for c in ci] if not np.isnan(ci[0]) else None,
            "status": "powered" if powered else ("underpowered" if n >= 12 else "INSUFFICIENT(n<12)")}


def benjamini_yekutieli(pvals, q=0.10):
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    m = len(items)
    if m == 0:
        return {"m": 0, "note": "powered cell 0"}
    items.sort(key=lambda x: x[1])
    c_m = sum(1.0 / i for i in range(1, m + 1))
    surv = []
    for ri, (k, p) in enumerate(items, 1):
        if p <= (ri / m) * q / c_m:
            surv = [items[j][0] for j in range(ri)]
    return {"m": m, "by_factor": round(c_m, 3), "survivors_BY": surv,
            "raw_p_min": round(items[0][1], 5), "raw_p_min_key": items[0][0]}


def rank_ic_series(scores: pd.DataFrame, fwd: pd.DataFrame):
    """월별 cross-sectional Spearman IC 시계열 (equipment universe)."""
    ics, ns = [], []
    idx = scores.index.intersection(fwd.index)
    for dt in idx:
        s = scores.loc[dt].dropna()
        f = fwd.loc[dt].dropna()
        common = s.index.intersection(f.index)
        if len(common) < 5:
            continue
        rho, _ = stats.spearmanr(s.loc[common].values, f.loc[common].values)
        if not np.isnan(rho):
            ics.append(rho); ns.append(len(common))
    return np.array(ics), np.array(ns)


def ic_summary(ics, ns, h_months, label):
    if len(ics) < 8:
        return {"label": label, "n_months": len(ics), "status": "INSUFFICIENT(n<8)"}
    ic_mean = float(ics.mean())
    neff = n_eff_autocorr(ics)
    se = nw_se(ics, h_months)
    t_nw = ic_mean / se if se and se > 0 else np.nan
    t_eff = float(ic_mean * np.sqrt(max(neff, 1)) / (ics.std(ddof=1) + 1e-9)) if ics.std(ddof=1) > 0 else np.nan
    wc_p = wild_cluster_p(ics)
    ci = block_boot_ci(ics, max(2, h_months))
    avg_n = float(np.mean(ns))
    powered = (len(ics) >= 24) and (neff >= 6) and (avg_n >= 8)
    return {"label": label, "n_months": len(ics), "n_eff": round(neff, 1), "avg_universe_n": round(avg_n, 1),
            "ic_mean": round(ic_mean, 4), "t_nw": round(t_nw, 2) if not np.isnan(t_nw) else None,
            "t_eff": round(t_eff, 2) if not np.isnan(t_eff) else None,
            "wild_cluster_p": round(wc_p, 4) if not np.isnan(wc_p) else None,
            "ci95_block_boot": [round(c, 4) for c in ci] if not np.isnan(ci[0]) else None,
            "status": "powered" if powered else ("underpowered" if len(ics) >= 12 else "INSUFFICIENT")}


# ───────────────────────── load ─────────────────────────
def load():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    cyc = pd.read_parquet(DATA / "telecom_cycle.parquet"); cyc.index = pd.to_datetime(cyc.index)
    lab = pd.read_parquet(DATA / "regime_labels.parquet"); lab.index = pd.to_datetime(lab.index)
    cf = pd.read_parquet(DATA / "common_factors.parquet"); cf.index = pd.to_datetime(cf.index)
    uni = pd.read_parquet(DATA / "universe.parquet")
    dart = pd.read_parquet(DATA / "dart_financials.parquet")
    return px, cyc, lab, cf, uni, dart


def main():
    px, cyc, lab, cf, uni, dart = load()

    # strict floor (Marcap>=3000억 & ADV>=30억)
    uni["strict"] = (uni["Marcap"] >= 3e11) & (uni["Amount"] >= 3e9)
    svc_strict = [c for c in uni[(uni.subcl == "service") & uni.strict]["Code"] if c in px.columns]
    eqp_strict = [c for c in uni[(uni.subcl == "equipment") & uni.strict]["Code"] if c in px.columns]
    print(f"service strict (cross-sectional 자격): {svc_strict} (n={len(svc_strict)})")
    print(f"equipment strict (cross-sectional 자격): {eqp_strict} (n={len(eqp_strict)})")

    pxm = px.resample("ME").last()
    lab19 = lab.loc["2019-01-01":]
    cyc19 = cyc.loc["2019-01-01":]

    results = {"meta": {
        "method": "통신 2-archetype: (A) service 3사 시계열(frame M2, KR금리 duration) + (B) equipment cross-sectional conditional IC",
        "service_panel": svc_strict, "equipment_universe": eqp_strict,
        "rate_source": "★KR 10Y 국채 IRLTLT01KRM156N (배당주 duration). US rate10y(^TNX)=대조.",
        "horizons_days": HORIZONS_D,
        "gf_contract": "헤더 7항. wild-cluster B=2000 + block-boot CI + eff-N + ADF.",
    }}

    # ════════════════ (A) SERVICE 시계열 (3사, 배당주 duration) ════════════════
    svc_ret_m = pxm[svc_strict].pct_change().mean(axis=1, skipna=True).loc["2019-01-01":].dropna()
    results["service_panel_stats"] = {
        "n_months": len(svc_ret_m), "ret_mean_monthly": round(float(svc_ret_m.mean()), 4),
        "ret_vol_monthly": round(float(svc_ret_m.std()), 4)}

    drivers = {
        "kr_rate10y": cyc19["kr_rate10y"],
        "d_kr_rate10y": cyc19["d_kr_rate10y"],
        "kr_curve_10y3m": cyc19["kr_curve_10y3m"],
        "kr_rate10y_yoy": cyc19["kr_rate10y_yoy"],
        "us_rate10y": cf["rate10y"].resample("ME").last().loc["2019-01-01":],
    }
    # ── (A1) contemporaneous: 통신패널 월수익 vs 금리 Δ (배당주 duration 동시) ──
    results["service_contemporaneous"] = {}
    for dname, dser in drivers.items():
        x = dser.diff() if dname in ("kr_rate10y", "kr_curve_10y3m", "us_rate10y") else dser
        st = corr_stat(svc_ret_m, x.loc["2019-01-01":], 1, dname)
        results["service_contemporaneous"][dname] = st

    # ── (A2) forward (★falsifier): 금리 level/Δ(t) → 통신패널 forward 1~3M ──
    results["service_forward"] = {}
    for hm_label, hm in [("fwd_1m", 1), ("fwd_3m", 3)]:
        fwd_ret = pxm[svc_strict].pct_change(hm).mean(axis=1).shift(-hm).loc["2019-01-01":]
        results["service_forward"][hm_label] = {}
        for dname in ["kr_rate10y", "d_kr_rate10y", "kr_curve_10y3m", "kr_rate10y_yoy"]:
            st = corr_stat(drivers[dname].loc["2019-01-01":], fwd_ret, max(1, hm), f"{dname}__{hm_label}")
            results["service_forward"][hm_label][dname] = st

    # ── (A3) horizon sweep (5d/20d/60d): KR10Y level → service forward ──
    pxd = px[svc_strict]
    svc_ret_d_panel = pxd.pct_change().mean(axis=1)  # daily panel return
    kr10_d = cyc["kr_rate10y"].reindex(px.index, method="ffill")
    results["service_horizon_sweep"] = {}
    for hl, hd in HORIZONS_D.items():
        fwd = svc_ret_d_panel.shift(-hd).rolling(1).sum()
        # 월말 sample 만 (overlap 완화)
        me_idx = pxm.index.intersection(px.index) if False else px.index[px.index.isin(pxm.index)]
        xx = kr10_d.loc["2019-01-01":]
        yy = fwd.loc["2019-01-01":]
        # 월말 subsample
        mask = xx.index.isin(pxm.index)
        st = corr_stat(xx[mask], yy[mask], max(1, hd // 20), f"kr_rate10y__{hl}")
        results["service_horizon_sweep"][hl] = st

    # ── (A4) walk-forward OOS (IS 2019-22 / OOS 2023-26): KR10Y forward 3M ──
    kr10_lvl = drivers["kr_rate10y"].loc["2019-01-01":]
    fwd3 = pxm[svc_strict].pct_change(3).mean(axis=1).shift(-3).loc["2019-01-01":]
    def split_rho(x, y, lo, hi):
        idx = x.dropna().index.intersection(y.dropna().index)
        idx = idx[(idx >= lo) & (idx <= hi)]
        if len(idx) < 8:
            return None, len(idx)
        r, _ = stats.spearmanr(x.loc[idx].values, y.loc[idx].values)
        return round(float(r), 4), len(idx)
    is_rho, is_n = split_rho(kr10_lvl, fwd3, "2019-01-01", "2022-12-31")
    oos_rho, oos_n = split_rho(kr10_lvl, fwd3, "2023-01-01", "2026-12-31")
    full_rho, full_n = split_rho(kr10_lvl, fwd3, "2019-01-01", "2026-12-31")
    sign_hold = (is_rho is not None and oos_rho is not None and np.sign(is_rho) == np.sign(oos_rho))
    results["service_walk_forward_oos"] = {
        "driver": "kr_rate10y level → service fwd_3m",
        "full_rho": full_rho, "full_n": full_n, "is_rho": is_rho, "is_n": is_n,
        "oos_rho": oos_rho, "oos_n": oos_n, "sign_hold": bool(sign_hold)}

    # ── (A5) leave-episode (2020 covid 저금리 + 2022 인상 제외) ──
    ep_mask = ~(((kr10_lvl.index >= "2020-03-01") & (kr10_lvl.index <= "2020-09-30")) |
                ((kr10_lvl.index >= "2022-06-01") & (kr10_lvl.index <= "2023-01-31")))
    le_rho, le_n = split_rho(kr10_lvl[ep_mask], fwd3, "2019-01-01", "2026-12-31")
    results["service_leave_episode"] = {"leave_covid_hike_rho": le_rho, "n": le_n, "full_rho": full_rho,
                                        "survive": (le_rho is not None and full_rho is not None and np.sign(le_rho) == np.sign(full_rho))}

    # ── (A6) ADF (단위근 §1.7) ──
    results["service_adf"] = {
        "kr_rate10y_level": adf_pvalue(kr10_lvl),
        "d_kr_rate10y": adf_pvalue(drivers["d_kr_rate10y"]),
        "service_fwd3_ret": adf_pvalue(fwd3),
        "service_panel_ret": adf_pvalue(svc_ret_m)}

    # ── (A7) family_2 interaction (A-5): rate forward × macro regime ──
    # KR10Y forward 음(duration)이 국면 따라 강/약? Slowdown vs 기타
    results["service_family2_interaction"] = {}
    try:
        macro = lab19["macro_regime"].reindex(fwd3.index, method="ffill")
        df_i = pd.DataFrame({"y": fwd3, "x": kr10_lvl, "macro": macro}).dropna()
        df_i["slowdown"] = (df_i["macro"] == "Slowdown").astype(float)
        df_i["x_z"] = (df_i["x"] - df_i["x"].mean()) / df_i["x"].std()
        df_i["inter"] = df_i["x_z"] * df_i["slowdown"]
        import numpy.linalg as la
        X = np.column_stack([np.ones(len(df_i)), df_i["x_z"].values, df_i["slowdown"].values, df_i["inter"].values])
        yv = df_i["y"].values
        beta, *_ = la.lstsq(X, yv, rcond=None)
        resid = yv - X @ beta
        sigma2 = (resid @ resid) / max(len(yv) - 4, 1)
        cov = sigma2 * la.inv(X.T @ X)
        se = np.sqrt(np.diag(cov))
        results["service_family2_interaction"] = {
            "b_main_x": round(float(beta[1]), 4), "t_main_x": round(float(beta[1] / se[1]), 2),
            "b_inter_slowdown": round(float(beta[3]), 4), "t_inter": round(float(beta[3] / se[3]), 2),
            "n": len(df_i), "note": "KR10Y level forward × Slowdown interaction"}
    except Exception as e:
        results["service_family2_interaction"] = {"error": str(e)}

    # ── (A8) regime conditional: KR10Y Δ 동시 vs service ret, by regime ──
    x_main = drivers["d_kr_rate10y"].loc["2019-01-01":]
    results["service_regime_conditional"] = {}
    for axis in ["macro_regime", "krw_regime", "flow_regime"]:
        la_s = lab19[axis].dropna()
        for rg in sorted(la_s.unique()):
            months = la_s[la_s == rg].index
            xs = x_main[x_main.index.isin(months)]
            ys = svc_ret_m[svc_ret_m.index.isin(months)]
            st = corr_stat(xs, ys, 1, f"d_kr_rate10y_contemp__{axis}={rg}")
            results["service_regime_conditional"][f"{axis}={rg}"] = st

    # ── (A9) placebo (random series) ──
    rng = np.random.default_rng(7)
    placebo = pd.Series(rng.standard_normal(len(svc_ret_m)), index=svc_ret_m.index)
    results["service_placebo"] = corr_stat(svc_ret_m, placebo, 1, "placebo_random")

    # ════════════════ (B) EQUIPMENT cross-sectional (10종, cyclical) ════════════════
    # 가격기반 momentum + DART 기반 valuation(PBR via equity, PER via net_income)
    eqp_pxm = pxm[eqp_strict]
    # value: PBR = Marcap / equity (DART), PER = Marcap / net_income_ttm. z-score cross-sectional.
    # DART → 분기 equity/net_income, rcept_dt PIT
    dart_eq = dart[dart["code"].isin(eqp_strict)].copy()
    dart_eq["rcept_dt"] = pd.to_datetime(dart_eq["rcept_dt"], format="%Y%m%d")
    # 각 월말에 가용한 최신 공시(rcept_dt<=월말) 의 equity 사용 → PBR
    month_ends = eqp_pxm.index
    pbr_panel = pd.DataFrame(index=month_ends, columns=eqp_strict, dtype=float)
    per_panel = pd.DataFrame(index=month_ends, columns=eqp_strict, dtype=float)
    # 주식수 근사 = Marcap(현재) / 현재가 → 시점별 Marcap = 주식수 × 가격
    cur_marcap = uni.set_index("Code")["Marcap"]
    cur_px = px[eqp_strict].iloc[-1]
    shares = {c: (cur_marcap.get(c, np.nan) / cur_px.get(c, np.nan)) for c in eqp_strict}
    for c in eqp_strict:
        sub = dart_eq[dart_eq["code"] == c].sort_values("rcept_dt")
        if sub.empty:
            continue
        for me in month_ends:
            avail = sub[sub["rcept_dt"] <= me]
            if avail.empty:
                continue
            eq = avail.iloc[-1]["equity"]
            ni = avail.iloc[-1]["net_income"]
            price = eqp_pxm.loc[me, c]
            if pd.notna(price) and pd.notna(eq) and eq > 0 and pd.notna(shares[c]):
                mcap = shares[c] * price
                pbr_panel.loc[me, c] = mcap / eq
                if pd.notna(ni) and ni > 0:
                    per_panel.loc[me, c] = mcap / ni  # 흑자만

    def zscore_rows(df):
        return df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1) + 1e-9, axis=0)

    pbr_z = zscore_rows(pbr_panel.astype(float))
    per_z = zscore_rows(per_panel.astype(float))
    # momentum 12-1 (12개월 - 최근1개월)
    mom = eqp_pxm.pct_change(12) - eqp_pxm.pct_change(1)
    mom_z = zscore_rows(mom)

    results["equipment_cross_sectional"] = {}
    sig_panels = {"pbr_z": pbr_z, "per_z": per_z, "mom_12_1_z": mom_z}
    # prior: pbr_z 음(저PBR value), per_z 음, mom 양
    for hl, hd in [("y_5d", 5), ("y_20d", 20), ("y_60d", 60)]:
        hm = max(1, hd // 20)
        fwd = eqp_pxm.pct_change(hm).shift(-hm)
        results["equipment_cross_sectional"][hl] = {}
        for sname, spanel in sig_panels.items():
            ics, ns = rank_ic_series(spanel.loc["2019-01-01":], fwd.loc["2019-01-01":])
            results["equipment_cross_sectional"][hl][sname] = ic_summary(ics, ns, hm, f"{sname}__{hl}")

    # equipment value walk-forward OOS (pbr_z 20d)
    fwd20 = eqp_pxm.pct_change(1).shift(-1)
    def ic_split(spanel, fwd, lo, hi):
        ics, ns = rank_ic_series(spanel.loc[lo:hi], fwd.loc[lo:hi])
        return (round(float(ics.mean()), 4), len(ics)) if len(ics) >= 6 else (None, len(ics))
    eq_is, eq_isn = ic_split(pbr_z, fwd20, "2019-01-01", "2022-12-31")
    eq_oos, eq_oosn = ic_split(pbr_z, fwd20, "2023-01-01", "2026-12-31")
    results["equipment_value_oos"] = {"signal": "pbr_z 20d", "is_ic": eq_is, "is_n": eq_isn,
                                      "oos_ic": eq_oos, "oos_n": eq_oosn,
                                      "sign_hold": (eq_is is not None and eq_oos is not None and np.sign(eq_is) == np.sign(eq_oos))}

    # ════════════════ 단일 FDR family (service + equipment) ════════════════
    pvals_fdr = {}
    # service powered cells
    for dname, st in results["service_contemporaneous"].items():
        if st.get("status") == "powered" and st.get("wild_cluster_p") is not None:
            pvals_fdr[f"svc_contemp_{dname}"] = st["wild_cluster_p"]
    for hl, hd in results["service_forward"].items():
        for dname, st in hd.items():
            if st.get("status") == "powered" and st.get("wild_cluster_p") is not None:
                pvals_fdr[f"svc_{hl}_{dname}"] = st["wild_cluster_p"]
    for ck, st in results["service_regime_conditional"].items():
        if st.get("status") == "powered" and st.get("wild_cluster_p") is not None:
            pvals_fdr[f"svc_regime_{ck}"] = st["wild_cluster_p"]
    # equipment powered cells
    for hl, hd in results["equipment_cross_sectional"].items():
        for sname, st in hd.items():
            if st.get("status") == "powered" and st.get("wild_cluster_p") is not None:
                pvals_fdr[f"eqp_{hl}_{sname}"] = st["wild_cluster_p"]
    results["fdr_single_family"] = benjamini_yekutieli(pvals_fdr)

    out = ROOT / "validation-telecom-v3.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved {out}")
    print_summary(results)
    return results


def print_summary(r):
    print("\n" + "=" * 76)
    print("(A) 통신서비스 3사 시계열 — 배당주 duration (KR 금리)")
    print("=" * 76)
    print(f"  panel n_months={r['service_panel_stats']['n_months']} ret_mean={r['service_panel_stats']['ret_mean_monthly']}")
    print("\n  --- contemporaneous (금리 Δ 동시) ---")
    for d, st in r["service_contemporaneous"].items():
        if st.get("status", "").startswith("INSUFF"):
            continue
        print(f"    {d:18s} rho={st.get('spearman_rho'):+.3f} wc_p={st.get('wild_cluster_p')} t_eff={st.get('t_eff_corrected')} n={st.get('n')} {st.get('status')}")
    print("\n  --- forward (falsifier 예측력) ---")
    for hl, hd in r["service_forward"].items():
        for d, st in hd.items():
            if st.get("status", "").startswith("INSUFF"):
                continue
            print(f"    {d:16s}[{hl}] rho={st.get('spearman_rho'):+.3f} wc_p={st.get('wild_cluster_p')} t_eff={st.get('t_eff_corrected')} n={st.get('n')}")
    print("\n  --- horizon sweep (KR10Y level → fwd) ---")
    for hl, st in r["service_horizon_sweep"].items():
        if not st.get("status", "").startswith("INSUFF"):
            print(f"    {hl}: rho={st.get('spearman_rho'):+.3f} wc_p={st.get('wild_cluster_p')} t_eff={st.get('t_eff_corrected')} n={st.get('n')}")
    print(f"\n  walk-forward OOS: {r['service_walk_forward_oos']}")
    print(f"  leave-episode: {r['service_leave_episode']}")
    print(f"  ADF: {r['service_adf']}")
    print(f"  family_2 interaction: {r['service_family2_interaction']}")
    print(f"  placebo: rho={r['service_placebo'].get('spearman_rho')} wc_p={r['service_placebo'].get('wild_cluster_p')}")
    print("\n  --- regime conditional (powered만) ---")
    for ck, st in r["service_regime_conditional"].items():
        if st.get("status") in ("powered", "underpowered"):
            star = "★" if st["status"] == "powered" else " "
            print(f"   {star}{ck:30s} rho={st.get('spearman_rho'):+.3f} wc_p={st.get('wild_cluster_p')} n={st.get('n')} {st.get('status')}")
    print("\n" + "=" * 76)
    print("(B) 통신장비 cross-sectional — cyclical (value/momentum)")
    print("=" * 76)
    for hl, hd in r["equipment_cross_sectional"].items():
        for sname, st in hd.items():
            if st.get("status", "").startswith("INSUFF"):
                print(f"  {sname:12s}[{hl}] {st.get('status')}")
                continue
            print(f"  {sname:12s}[{hl}] IC={st.get('ic_mean'):+.3f} wc_p={st.get('wild_cluster_p')} t_eff={st.get('t_eff')} avgN={st.get('avg_universe_n')} n_m={st.get('n_months')} {st.get('status')}")
    print(f"\n  equipment value OOS: {r['equipment_value_oos']}")
    print(f"\n★단일 FDR family: {r['fdr_single_family']}")


if __name__ == "__main__":
    main()
