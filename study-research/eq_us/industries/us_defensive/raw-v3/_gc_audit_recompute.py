# -*- coding: utf-8 -*-
"""_gc_audit_recompute.py — ★G-C 독립 audit raw 재계산 (author != auditor).
self-audit 초안 / G-B 자문 verdict 를 복붙하지 않고 validation-metrics-v3.json + _gb_verify.json 의
핵심 수치를 raw(prices/edgar/macro/universe.parquet)로 재계산해 대조한다. measure.py 함수 재사용.
⛔ 산출 수정 0 (별 산출 stdout 만)."""
from __future__ import annotations
import sys, io, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure as M  # measure 가 sys.stdout utf-8 설정

ROOT = Path(__file__).resolve().parent


def line(s=""):
    print(s)


def main():
    px, ed, uni, macro = M.load()
    secmap = dict(zip(uni["ticker"], uni["subcl"]))
    pxm = px.resample("ME").last()
    P = M.build_pit_panels(px, ed)

    line("=" * 96)
    line("0. 기초 재현 — universe / EDGAR rows / PIT lag")
    line(f"  universe n = {px.shape[1]} (author json: 48)")
    line(f"  sub-sectors = {uni['subcl'].value_counts().to_dict()}")
    line(f"  date_range = {px.index.min().date()} ~ {px.index.max().date()}")
    edp = M._ed_prep(ed)
    line(f"  EDGAR rows (filed/val non-null) = {len(edp)} (author: 111140)")
    line(f"  EDGAR concepts = {sorted(edp['concept'].unique())}")
    # PIT lag: filed - end
    edp2 = edp.copy()
    edp2["end_dt"] = pd.to_datetime(edp2["end"], errors="coerce")
    lag = (edp2["filed_dt"] - edp2["end_dt"]).dt.days.dropna()
    neg = int((lag < 0).sum())
    line(f"  PIT lag (filed-end): min={lag.min()} median={lag.median()} max={lag.max()} | negative={neg}/{len(lag)} ({100*neg/len(lag):.3f}%)")
    line(f"  panel cov: " + ", ".join(f"{k}={int(v.notna().sum().sum())}" for k, v in P.items()))

    # ── sector-neutral z ──
    ep_z = M.cs_z(P["ep_yield"], secmap)
    per_z = M.cs_z(P["per"], secmap)
    pbr_z = M.cs_z(P["pbr"], secmap)
    payout_z = M.cs_z(P["payout_yield"], secmap)
    div_z = M.cs_z(P["dividend_yield"], secmap)
    gp_z = M.cs_z(P["gross_prof"], secmap)

    line("\n" + "=" * 96)
    line("1순위-A. core IC 재현 (sector-neutral z, NW t)")
    fwd12 = pxm.shift(-12) / pxm - 1
    fwd6 = pxm.shift(-6) / pxm - 1
    fwd3 = pxm.shift(-3) / pxm - 1
    for name, sig, fwd, h, ref in [
        ("ep_yield 3M", ep_z, fwd3, 3, "json IC -0.0385 t-2.40 p0.0174"),
        ("ep_yield 6M", ep_z, fwd6, 6, "json IC -0.0484 t-2.10"),
        ("ep_yield 12M", ep_z, fwd12, 12, "json IC -0.0560 t-2.20"),
        ("payout 12M", payout_z, fwd12, 12, "json IC -0.0828 t-2.10"),
        ("per_z 3M", per_z, fwd3, 3, "json IC +0.0381 t+2.28"),
        ("pbr_z 12M", pbr_z, fwd12, 12, "json IC +0.0159 t+0.51"),
        ("gross_prof 12M", gp_z, fwd12, 12, "json IC +0.0022 t+0.06"),
    ]:
        ic, ns = M.cs_ic(sig, fwd)
        se = M.nw_se(ic, h); t = ic.mean() / se
        line(f"  {name:16} IC={ic.mean():+.4f} t={t:+.2f} n={len(ic)}   [{ref}]")

    # ── BY / M_eff 재계산 ──
    line("\n" + "=" * 96)
    line("2순위. BY / M_eff 재계산 (Li-Ji eigenvalue)")
    signals = {
        "rev_1m": M.cs_z(pxm / pxm.shift(1) - 1, secmap),
        "mom_6": M.cs_z(pxm / pxm.shift(6) - 1, secmap),
        "vol_60": M.cs_z((px.pct_change().rolling(60).std() * np.sqrt(252)).resample("ME").last(), secmap),
        "per_z": per_z, "pbr_z": pbr_z, "ep_yield": ep_z,
        "ev_ebitda": M.cs_z(P["ev_ebitda"], secmap),
        "gross_prof": gp_z, "payout_yield": payout_z, "dividend_yield": div_z,
        "fcf_yield": M.cs_z(P["fcf_yield"], secmap), "earnings_cv": M.cs_z(P["earnings_cv"], secmap),
    }
    horizons = {"3M": 3, "6M": 6, "12M": 12, "24M_value": 24}
    pvals, ic_series = {}, {}
    for sname, sig in signals.items():
        for hname, h in horizons.items():
            fwd = pxm.shift(-h) / pxm - 1
            ic, ns = M.cs_ic(sig, fwd)
            if len(ic) < 6:
                continue
            se = M.nw_se(ic, h); t = ic.mean() / se if se and se > 0 else np.nan
            n = len(ic)
            p = float(2 * (1 - stats.t.cdf(abs(t), df=max(n-1, 1)))) if not np.isnan(t) else np.nan
            key = f"{sname}__{hname}"
            pvals[key] = round(p, 4) if not np.isnan(p) else None
            ic_series[key] = ic
    keys = list(ic_series.keys())
    ic_df = pd.DataFrame({k: ic_series[k] for k in keys})
    tcorr = ic_df.corr().fillna(0).values; np.fill_diagonal(tcorr, 1.0)
    m_eff = M.m_eff_liji(tcorr)
    by_meff = M.benjamini_yekutieli(pvals, m_override=m_eff)
    by_raw = M.benjamini_yekutieli(pvals, m_override=None)
    line(f"  raw_m = {by_raw['m_raw']} (author: 48)")
    line(f"  M_eff = {m_eff:.2f} (author: 26.0)")
    line(f"  BY rank1_thr (raw) = {by_raw['rank1_threshold']} (author: 0.000467)")
    line(f"  BY rank1_thr (M_eff) = {by_meff['rank1_threshold']} (author: 0.000998)")
    line(f"  raw_p_min = {by_meff['raw_p_min']} [{by_meff['raw_p_min_key']}] (author: 0.0174 ep_yield__3M)")
    line(f"  survivors_BY (M_eff) = {by_meff['survivors_BY']} (author: [])")
    line(f"  raw_p_min > thr*2 ? {by_meff['raw_p_min']} > {by_meff['rank1_threshold']*2:.6f} = {by_meff['raw_p_min'] > by_meff['rank1_threshold']*2} (G-B trigger)")

    # ── regime split (1순위) ──
    line("\n" + "=" * 96)
    line("1순위-B. REGIME SPLIT 재계산 (QE 2010-2021 vs value-revival 2022+), split 2022-01-01")
    def regime_ic(sig, fwd, h):
        ic, _ = M.cs_ic(sig, fwd)
        e1 = ic[ic.index < "2022-01-01"]; e2 = ic[ic.index >= "2022-01-01"]
        def st(x):
            if len(x) < 6: return (None, None, 0)
            se = M.nw_se(x, 12); t = x.mean()/se if se>0 else None
            return (round(float(x.mean()),4), round(float(t),2) if t else None, len(x))
        full = st(ic); q = st(e1); hk = st(e2)
        consist = (np.sign(e1.mean()) == np.sign(e2.mean())) if len(e1)>=6 and len(e2)>=6 else None
        return full, q, hk, consist
    for name, sig, ref in [
        ("ep_yield 12M", ep_z, "json QE -0.0607 t-1.95 / 2022+ -0.0396 t-1.29 consist=True"),
        ("payout 12M", payout_z, "json QE -0.1217 t-2.86 / 2022+ +0.0538 t1.27 consist=False"),
        ("dividend 12M", div_z, "json QE -0.1202 t-2.67 / 2022+ +0.0961 t1.15 consist=False"),
        ("per_z 12M", per_z, "json QE +0.0507 / 2022+ -0.0134 consist=False"),
    ]:
        full, q, hk, c = regime_ic(sig, fwd12, 12)
        line(f"  {name:14} full={full[0]:+.4f}  QE={q[0]:+.4f}(t{q[1]},n{q[2]})  2022+={hk[0]:+.4f}(t{hk[1]},n{hk[2]})  consist={c}")
        line(f"                 [{ref}]")

    # ── leave-sub-sector (1순위, healthcare 지배 점검) ──
    line("\n" + "=" * 96)
    line("1순위-C. LEAVE-SUB-SECTOR (ep_yield, healthcare 지배 위험 점검)")
    subs = sorted(set(secmap.values()))
    line(f"  sub-sectors = {subs}")
    for h, fwd in [(6, fwd6), (12, fwd12)]:
        line(f"  -- horizon {h}M (full + each leave-one-sub-sector) --")
        ic_full, _ = M.cs_ic(ep_z, fwd)
        line(f"     full IC = {ic_full.mean():+.4f}")
        for s in subs:
            keep = [t for t in P["ep_yield"].columns if secmap.get(t) != s]
            sub_panel = P["ep_yield"][keep]
            sub_z = M.cs_z(sub_panel, {t: secmap[t] for t in keep})
            ic, _ = M.cs_ic(sub_z, fwd)
            line(f"     ex_{s:12} IC={ic.mean():+.4f} (n={len(ic)})  [json ep 12M ex_healthcare -0.062]")

    # ── quality partial-corr (1순위) ──
    line("\n" + "=" * 96)
    line("1순위-D. QUALITY PARTIAL-CORR (ep_yield | gross_prof 잔차 IC)")
    def partial(sig_panel, ctrl_panel, fwd):
        sig_z = M.cs_z(sig_panel, secmap); ctrl_z = M.cs_z(ctrl_panel, secmap)
        idx = sig_z.index.intersection(fwd.index)
        raw_ics, part_ics = [], []
        for dt in idx:
            sv = sig_z.loc[dt].dropna(); cv = ctrl_z.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
            c = sv.index.intersection(rv.index)
            if len(c) < 8: continue
            rho, _ = stats.spearmanr(sv.loc[c], rv.loc[c])
            if not np.isnan(rho): raw_ics.append(rho)
            cc = c.intersection(cv.index)
            if len(cc) < 8: continue
            s = sv.loc[cc].values; ct = cv.loc[cc].values; r = rv.loc[cc].values
            A = np.vstack([np.ones_like(ct), ct]).T
            beta, *_ = np.linalg.lstsq(A, s, rcond=None)
            rho_p, _ = stats.spearmanr(s - A @ beta, r)
            if not np.isnan(rho_p): part_ics.append(rho_p)
        def summ(arr):
            x = pd.Series(arr); se = M.nw_se(x, 12); t = x.mean()/se if se>0 else None
            return round(float(np.mean(arr)),4), round(float(t),2) if t else None, len(arr)
        return summ(raw_ics), summ(part_ics)
    for name, sp, fwd, ref in [
        ("ep 6M", P["ep_yield"], fwd6, "json raw -0.0484 t-2.03 / partial -0.0645 t-2.46"),
        ("ep 12M", P["ep_yield"], fwd12, "json raw -0.056 t-2.2 / partial -0.0508 t-1.55"),
    ]:
        rw, pt = partial(sp, P["gross_prof"], fwd)
        line(f"  {name:8} raw IC={rw[0]:+.4f}(t{rw[1]},n{rw[2]})  partial|quality={pt[0]:+.4f}(t{pt[1]},n{pt[2]})")
        line(f"           [{ref}]")
    # payout partial
    rw, pt = partial(P["payout_yield"], P["gross_prof"], fwd12)
    line(f"  payout12 raw IC={rw[0]:+.4f}(t{rw[1]})  partial|quality={pt[0]:+.4f}(t{pt[1]})  [json raw -0.0828 / partial -0.0588 t-0.99]")

    # ── sector-z decomposition (1순위, 무회복) ──
    line("\n" + "=" * 96)
    line("1순위-E. SECTOR-Z DECOMPOSITION (us_cyclical 무회복 대조)")
    line(f"  {'signal':16}{'uni':>9}{'secN':>9}{'sectorLvl':>11}{'cross_std':>11}")
    for name in ["pbr", "per", "ep_yield", "payout_yield"]:
        for h, fwd in [(12, fwd12), (24, pxm.shift(-24)/pxm - 1)]:
            d = M.sector_z_decomposition(P[name], fwd, secmap)
            line(f"  {name+'__'+str(h)+'M':16}{d['ic_universe_z']:>+9.4f}{d['ic_sector_neutral_z']:>+9.4f}{d['ic_sector_level_component']:>+11.4f}{d['cross_std_sector_neutral']:>11.3f}")

    # ── byte-identical (단일산업 무회귀, M wire) ──
    line("\n" + "=" * 96)
    line("3순위-M. byte-identical (단일 sub-sector = universe-demean == sector-neutral)")
    one = [t for t in P["pbr"].columns if secmap.get(t) == "healthcare"]
    z_uni = M.cs_z(P["pbr"][one], None)
    z_sn = M.cs_z(P["pbr"][one], {t: secmap[t] for t in one})
    diff = float(np.nanmax(np.abs((z_uni - z_sn).values)))
    line(f"  healthcare single-sector ({len(one)}종) max|uni-secN| = {diff:.2e} (expect 0.00e+00)")

    line("\n✅ G-C recompute done")


if __name__ == "__main__":
    main()
