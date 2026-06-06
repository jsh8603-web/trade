# -*- coding: utf-8 -*-
"""_b2_cyclical_interactions.py — ★CYC-1~6 2-way interaction 드라이버 (team-lead 지시 2026-06-04).

입력 계약 = REWORK-prereg-11hypotheses-20260604.md CYC-1~6 (spec/predicted_sign/incremental_req invariant).
공통 계약: full-panel cross-sectional IC(월별 rank-IC), within-sub-sector demean(sector-neutral z),
  fixed-b t(KV) + wild-cluster bootstrap(B>=9999), n_eff=n/(1+2Sum rho_k) floor 30 미달=UNDERPOWERED,
  FWL incremental(interaction ⊥ {main1, main2, (net_issuance)} 직교 후 잔차 IC 양).

★raw stat 만 산출. ⛔FDR threshold 적용 X (team-lead 가 11개 통합).
★import: 로컬 measure 우선(sys.path.insert(0, 로컬)) → defensive 는 sys.path.append(끝) 로 _b2_stats 만(measure shadow 방지).

CYC-1: ev_ebitda(저cheap) × gross_prof(고) [+] ⊥{ev_ebitda, gross_prof, net_issuance}
CYC-2: PER-cheap − (PBR·sales)-cheap divergence single [−] ⊥{ep_yield, pbr, sales_yield}
CYC-3: op_prof(고) × asset_growth(저) [+] ★revival ⊥{op_prof, asset_growth, net_issuance}
CYC-4: ep_yield(고) × residual_mom(+) [+] ⊥{ep_yield, residual_mom}
CYC-5: ep_yield(고) × idio_vol(저) [+] ⊥{ep_yield, idio_vol}
CYC-6: [capex×ep_yield] IC_t ~ d_baa_aaa slope [+] Tier2 gatekept (capex 필요)
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))   # ★로컬 measure 우선
import measure as M
sys.path.append("D:/projects/Inv/study-research/eq_us/industries/us_defensive/raw-v3")  # _b2_stats 만
from _b2_stats import effective_n, fixed_b_cv, wild_cluster_boot, persistence_block

ROOT = Path(__file__).resolve().parent
NEFF_FLOOR = 30
WILD_B = 9999


def cs_z(panel, secmap):
    return M.cs_z(panel, secmap)


def interaction_z(z1, z2, secmap):
    return M.cs_z(z1 * z2, secmap)


def fwl_incremental_ic(inter_sig, main_sigs, fwd, secmap, min_n=10):
    idx = inter_sig.index.intersection(fwd.index); ics, dates = [], []
    for dt in idx:
        iv = inter_sig.loc[dt].dropna(); mains = [m.loc[dt] for m in main_sigs]; rv = fwd.loc[dt].dropna()
        common = iv.index
        for m in mains:
            common = common.intersection(m.dropna().index)
        common = common.intersection(rv.index)
        if len(common) < min_n:
            continue
        y = iv.loc[common].values
        X = np.column_stack([m.loc[common].values for m in mains] + [np.ones(len(common))])
        try:
            beta, *_ = np.linalg.lstsq(X, y, rcond=None); resid = y - X @ beta
        except Exception:
            continue
        rho, _ = stats.spearmanr(resid, rv.loc[common].values)
        if not np.isnan(rho):
            ics.append(rho); dates.append(dt)
    return pd.Series(ics, index=dates)


def size_valid_block(ic, label):
    ic = pd.Series(ic).dropna(); n = len(ic)
    if n < 12:
        return dict(label=label, n=n, note="insufficient")
    blk = persistence_block(ic.values); eff = effective_n(ic.values); mean = float(ic.mean())
    x = ic.values; e = x - x.mean(); g0 = (e @ e) / n; var = g0
    for k in range(1, min(blk, n - 1) + 1):
        var += 2 * (1 - k / (blk + 1)) * (e[k:] @ e[:-k]) / n
    se = float(np.sqrt(max(var, 1e-12) / n)); t = mean / se if se > 0 else np.nan
    fb = fixed_b_cv(n, blk)
    Xc = pd.DataFrame({"const": np.ones(n)}, index=ic.index)
    wc = wild_cluster_boot(pd.Series(ic.values, index=ic.index), Xc, "const", block=blk, B=WILD_B)
    return dict(label=label, ic_mean=round(mean, 4), n=n, hac_lag=blk,
                t_nw=round(float(t), 2) if not np.isnan(t) else None,
                n_eff=eff["n_eff"], underpowered=bool(eff["n_eff"] < NEFF_FLOOR),
                fixed_b_cv=fb["cv_5pct"], fixed_b_b=fb["b"],
                fixed_b_sig=bool(not np.isnan(t) and abs(t) > fb["cv_5pct"]),
                asymptotic_sig=bool(not np.isnan(t) and abs(t) > 1.96),
                p_wild_cluster=wc.get("p_wild_cluster"))


def fetch_capex(px, ed_existing):
    if "capex" in ed_existing["concept"].unique():
        return ed_existing
    import requests, time
    cmap = json.loads((ROOT / "data" / "cik_map.json").read_text(encoding="utf-8"))
    HDR = {"User-Agent": "inv-research research@example.com"}
    cands = ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"]
    rows = []
    for t in px.columns:
        cik = cmap.get(t)
        if not cik:
            continue
        for c in cands:
            try:
                r = requests.get(f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{c}.json",
                                 headers=HDR, timeout=20); time.sleep(0.12)
                if r.status_code == 200:
                    u = r.json().get("units", {}).get("USD", [])
                    if u:
                        for x in u:
                            rows.append(dict(ticker=t, concept="capex", end=x.get("end"), val=x.get("val"),
                                             filed=x.get("filed"), form=x.get("form"), fp=x.get("fp"), src_concept=c))
                        break
            except Exception:
                continue
    if rows:
        new = pd.concat([ed_existing, pd.DataFrame(rows)], ignore_index=True)
        new.to_parquet(ROOT / "data" / "edgar_fundamentals.parquet"); return new
    return ed_existing


def build_signals(px, ed, P, secmap):
    pxm = px.resample("ME").last(); ed = M._ed_prep(ed)
    by_t = {t: ed[ed["ticker"] == t] for t in px.columns}; midx = pxm.index
    ep, opp, ni_iss = {}, {}, {}
    for t in px.columns:
        sub = by_t[t]; g = lambda c: sub[sub["concept"] == c].sort_values("filed_dt")
        ni, sh, opi, assets = g("net_income"), g("shares"), g("op_income"), g("assets")
        e_s = pd.Series(index=midx, dtype=float); o_s = pd.Series(index=midx, dtype=float); n_s = pd.Series(index=midx, dtype=float)
        for dt in midx:
            price = pxm.loc[dt, t]
            if np.isnan(price):
                continue
            shv = M._latest_pit(sh, dt)
            if not np.isnan(shv) and shv > 0:
                mc = price * shv; niv = M._ttm(ni, dt)
                if not np.isnan(niv):
                    e_s[dt] = niv / mc
            a = M._latest_pit(assets, dt); opv = M._ttm(opi, dt)
            if not np.isnan(opv) and a and a > 0:
                o_s[dt] = opv / a
            shy = sh[sh["filed_dt"] <= dt].copy()
            if len(shy) >= 2:
                shy["end_dt"] = pd.to_datetime(shy["end"], errors="coerce")
                shy = shy.dropna(subset=["end_dt"]).sort_values("end_dt")
                if len(shy) >= 2:
                    cur = shy.iloc[-1]
                    prev = shy[(shy["end_dt"] <= cur["end_dt"] - pd.Timedelta(days=265)) &
                               (shy["end_dt"] >= cur["end_dt"] - pd.Timedelta(days=465))]
                    if len(prev) and prev.iloc[-1]["val"] > 0:
                        n_s[dt] = cur["val"] / prev.iloc[-1]["val"] - 1
        ep[t] = e_s; opp[t] = o_s; ni_iss[t] = n_s

    rets = px.pct_change(); mkt = rets.mean(axis=1)
    idio = pd.DataFrame(index=px.index, columns=px.columns, dtype=float)
    for t in px.columns:
        cov = rets[t].rolling(120).cov(mkt); var = mkt.rolling(120).var(); beta = cov / var
        idio[t] = (rets[t] - beta * mkt).rolling(60).std() * np.sqrt(252)
    idio_m = idio.resample("ME").last()

    raw_mom = pxm.shift(1) / pxm.shift(12) - 1
    mkt_m = mkt.resample("ME").last(); rets_m = pxm.pct_change()
    betas = pd.DataFrame(index=pxm.index, columns=pxm.columns, dtype=float)
    for t in pxm.columns:
        cov = rets_m[t].rolling(36).cov(mkt_m); var = mkt_m.rolling(36).var(); betas[t] = cov / var
    secs = sorted(set(secmap.get(t, "_") for t in pxm.columns))
    rmom = pd.DataFrame(index=raw_mom.index, columns=raw_mom.columns, dtype=float)
    for dt in raw_mom.index:
        y = raw_mom.loc[dt].dropna()
        if len(y) < 12:
            continue
        b = betas.loc[dt].reindex(y.index)
        rows = [{**{"beta": b.get(t, np.nan)}, **{f"sec_{s}": (1.0 if secmap.get(t) == s else 0.0) for s in secs[1:]}} for t in y.index]
        Xdf = pd.DataFrame(rows, index=y.index).dropna(); yy = y.reindex(Xdf.index)
        if len(yy) < 10:
            continue
        try:
            rmom.loc[dt, Xdf.index] = sm.OLS(yy.values, sm.add_constant(Xdf).values).fit().resid
        except Exception:
            continue

    return dict(
        ev_ebitda=cs_z(P["ev_ebitda"], secmap), gross_prof=cs_z(P["gross_prof"], secmap),
        ep_yield=cs_z(pd.DataFrame(ep), secmap), pbr=cs_z(P["pbr"], secmap),
        sales_yield=cs_z(P["sales_yield"], secmap), op_prof=cs_z(pd.DataFrame(opp), secmap),
        asset_growth=cs_z(P["asset_growth"], secmap), net_issuance=cs_z(pd.DataFrame(ni_iss), secmap),
        idio_vol=cs_z(idio_m, secmap), residual_mom=cs_z(rmom, secmap),
    )


def main():
    px, ed, uni, macro = M.load()
    secmap = dict(zip(uni["ticker"], uni["subcl"]))
    pxm = px.resample("ME").last(); P = M.build_pit_panels(px, ed)
    Z = build_signals(px, ed, P, secmap)
    H = 12; fwd = pxm.shift(-H) / pxm - 1
    results = {"meta": {"H_months": H, "neff_floor": NEFF_FLOOR, "wild_B": WILD_B, "z_method": "sector-neutral",
                        "note": "raw stat only, FDR X(team-lead 통합). cheap-dir: ev_ebitda 저=cheap(-z), ep_yield 고=cheap(+z)."}}
    cheap_ev = -Z["ev_ebitda"]; low_ag = -Z["asset_growth"]; low_vol = -Z["idio_vol"]

    inter = interaction_z(cheap_ev, Z["gross_prof"], secmap)
    results["CYC-1"] = dict(spec="ev_ebitda(저cheap) x gross_prof(고)", predicted_sign=1,
        raw_interaction_ic=size_valid_block(M.cs_ic(inter, fwd)[0], "CYC-1_raw"),
        incremental_ic=size_valid_block(fwl_incremental_ic(inter, [cheap_ev, Z["gross_prof"], Z["net_issuance"]], fwd, secmap), "CYC-1_incr"))

    book_sales_cheap = M.cs_z((-Z["pbr"] + Z["sales_yield"]) / 2, secmap)
    divergence = M.cs_z(Z["ep_yield"] - book_sales_cheap, secmap)
    results["CYC-2"] = dict(spec="PER-cheap - (PBR.sales)-cheap divergence single", predicted_sign=-1,
        raw_interaction_ic=size_valid_block(M.cs_ic(divergence, fwd)[0], "CYC-2_raw"),
        incremental_ic=size_valid_block(fwl_incremental_ic(divergence, [Z["ep_yield"], Z["pbr"], Z["sales_yield"]], fwd, secmap), "CYC-2_incr"))

    inter3 = interaction_z(Z["op_prof"], low_ag, secmap)
    results["CYC-3"] = dict(spec="op_prof(고) x asset_growth(저)", predicted_sign=1, revival_test=True,
        raw_interaction_ic=size_valid_block(M.cs_ic(inter3, fwd)[0], "CYC-3_raw"),
        incremental_ic=size_valid_block(fwl_incremental_ic(inter3, [Z["op_prof"], low_ag, Z["net_issuance"]], fwd, secmap), "CYC-3_incr"))

    inter4 = interaction_z(Z["ep_yield"], Z["residual_mom"], secmap)
    results["CYC-4"] = dict(spec="ep_yield(고) x residual_mom(+)", predicted_sign=1,
        raw_interaction_ic=size_valid_block(M.cs_ic(inter4, fwd)[0], "CYC-4_raw"),
        incremental_ic=size_valid_block(fwl_incremental_ic(inter4, [Z["ep_yield"], Z["residual_mom"]], fwd, secmap), "CYC-4_incr"))

    inter5 = interaction_z(Z["ep_yield"], low_vol, secmap)
    results["CYC-5"] = dict(spec="ep_yield(고) x idio_vol(저)", predicted_sign=1,
        raw_interaction_ic=size_valid_block(M.cs_ic(inter5, fwd)[0], "CYC-5_raw"),
        incremental_ic=size_valid_block(fwl_incremental_ic(inter5, [Z["ep_yield"], low_vol], fwd, secmap), "CYC-5_incr"))

    ed2 = fetch_capex(px, ed)
    if "capex" in ed2["concept"].unique():
        edp = M._ed_prep(ed2); midx = pxm.index; capex_pan = {}
        for t in px.columns:
            sub = edp[edp["ticker"] == t]; cx = sub[sub["concept"] == "capex"].sort_values("filed_dt")
            ax = sub[sub["concept"] == "assets"].sort_values("filed_dt")
            s = pd.Series(index=midx, dtype=float)
            for dt in midx:
                cv = M._ttm(cx, dt); a = M._latest_pit(ax, dt)
                if not np.isnan(cv) and a and a > 0:
                    s[dt] = cv / a
            capex_pan[t] = s
        capex_z = cs_z(pd.DataFrame(capex_pan), secmap)
        capex_ep = interaction_z(capex_z, Z["ep_yield"], secmap)
        ic_ce, _ = M.cs_ic(capex_ep, fwd)
        mm = macro.resample("ME").last(); d_baa = mm["baa_aaa"].diff()
        df = pd.concat([ic_ce.rename("ic"), d_baa.rename("reg")], axis=1).dropna()
        if len(df) >= 24:
            X = sm.add_constant(df[["reg"]]); blk = persistence_block(df["ic"].values)
            m = sm.OLS(df["ic"], X).fit(cov_type="HAC", cov_kwds={"maxlags": blk})
            t_hac = float(m.tvalues["reg"]); fb = fixed_b_cv(len(df), blk)
            wc = wild_cluster_boot(df["ic"], X, "reg", block=blk, B=WILD_B)
            results["CYC-6"] = dict(spec="[capex x ep_yield] IC_t ~ d_baa_aaa slope", predicted_sign=1, tier=2,
                twoway_ic=size_valid_block(ic_ce, "CYC-6_2way"), slope_beta=round(float(m.params["reg"]), 4),
                slope_t_hac=round(t_hac, 2), n=len(df), fixed_b_cv=fb["cv_5pct"],
                slope_fixed_b_sig=bool(abs(t_hac) > fb["cv_5pct"]), slope_p_wild=wc.get("p_wild_cluster"))
        else:
            results["CYC-6"] = dict(note="insufficient baa_aaa overlap", n=len(df))
    else:
        results["CYC-6"] = dict(note="capex fetch 실패 = SKIP (collector_plan)")

    (ROOT / "_b2_cyclical_interactions_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("=" * 84)
    for cyc in ["CYC-1", "CYC-2", "CYC-3", "CYC-4", "CYC-5", "CYC-6"]:
        r = results.get(cyc, {})
        if "raw_interaction_ic" in r:
            raw = r["raw_interaction_ic"]; inc = r["incremental_ic"]
            sign_ok = (np.sign(raw.get("ic_mean", 0)) == r["predicted_sign"])
            print(f"{cyc} [{r['spec'][:42]}] pred={r['predicted_sign']:+d}")
            print(f"   raw  IC={raw.get('ic_mean')} t={raw.get('t_nw')} n_eff={raw.get('n_eff')} CV={raw.get('fixed_b_cv')} fb_sig={raw.get('fixed_b_sig')} wildP={raw.get('p_wild_cluster')} UP={raw.get('underpowered')} sign_ok={sign_ok}")
            print(f"   incr IC={inc.get('ic_mean')} t={inc.get('t_nw')} fb_sig={inc.get('fixed_b_sig')} wildP={inc.get('p_wild_cluster')}")
        elif "twoway_ic" in r:
            tw = r["twoway_ic"]
            print(f"{cyc} [Tier2 {r['spec'][:34]}] 2way IC={tw.get('ic_mean')} fb_sig={tw.get('fixed_b_sig')} | slope b={r.get('slope_beta')} t={r.get('slope_t_hac')} fb_sig={r.get('slope_fixed_b_sig')} wildP={r.get('slope_p_wild')}")
        else:
            print(f"{cyc}: {r.get('note')}")


if __name__ == "__main__":
    main()
