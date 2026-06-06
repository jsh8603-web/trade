# -*- coding: utf-8 -*-
"""_gb_self_verify.py — ★G-B 1차 자체 검증 (team-lead 지시, 자문 전).
empirical-claim §1.7-D walk-forward + regime-conditional. anti-value/anti-yield 본질 vs QE regime artifact 판별.

3 검증:
1. regime split 부호 일관성: QE era(2010-2021) vs rate-hike/value-revival era(2022-2026).
   ★value-revival era 에서도 anti-value 유지 = 본질 / 역전·소멸 = QE/성장우위 regime artifact.
2. anti-value vs quality 재해석: ep_yield anti-value 가 gross_prof/earnings-quality 통제(partial-corr) 후 잔존?
3. LOO-year: anti-value 가 특정 연도(2020 COVID 성장폭등) 의존?

measure.py 함수 재사용. ⛔ validation-metrics-v3.json 수정 안 함 (별 산출 _gb_verify.json).
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure as M   # ★measure 가 sys.stdout=TextIOWrapper(utf-8) 설정 (재설정 금지, 충돌)

ROOT = Path(__file__).resolve().parent


def regime_split_ic(sig, fwd, split_date="2022-01-01"):
    """2 epoch IC + NW t + block-boot CI. anti-value 부호 일관성."""
    ic, ns = M.cs_ic(sig, fwd)
    if len(ic) < 24:
        return None
    e1 = ic[ic.index < split_date]   # QE era
    e2 = ic[ic.index >= split_date]  # rate-hike/value-revival era
    def stat(x, lags=12):
        if len(x) < 6:
            return dict(ic=None, n=len(x))
        se = M.nw_se(x, lags); t = float(x.mean()/se) if se and se > 0 else None
        ci = M.block_boot(x.values, 3, 1000) if len(x) >= 6 else (None, None)
        return dict(ic=round(float(x.mean()), 4), n=len(x),
                    t_nw=round(t, 2) if t else None,
                    ci=[round(ci[0], 4), round(ci[1], 4)] if ci[0] is not None else None)
    return dict(full=stat(ic), qe_2010_2021=stat(e1), hike_2022_2026=stat(e2),
                sign_consistent=bool(len(e1) >= 6 and len(e2) >= 6 and
                                     np.sign(e1.mean()) == np.sign(e2.mean())))


def partial_corr_quality(sig_panel, ctrl_panel, fwd, secmap):
    """★anti-value(ep) 가 quality(gross_prof) 통제 후 잔존?
    각 월: forward ~ sig + ctrl 회귀 후 sig 잔차 IC (partial). secmap = sector-neutral z 사용."""
    sig_z = M.cs_z(sig_panel, secmap)
    ctrl_z = M.cs_z(ctrl_panel, secmap)
    idx = sig_z.index.intersection(fwd.index)
    raw_ics, partial_ics, ns = [], [], []
    for dt in idx:
        sv = sig_z.loc[dt].dropna(); cv = ctrl_z.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
        c = sv.index.intersection(rv.index)
        if len(c) < 8:
            continue
        # raw IC
        rho, _ = stats.spearmanr(sv.loc[c], rv.loc[c])
        if not np.isnan(rho):
            raw_ics.append(rho)
        # partial: sig | ctrl (둘 다 있는 종목만)
        cc = c.intersection(cv.index)
        if len(cc) < 8:
            continue
        s = sv.loc[cc].values; ct = cv.loc[cc].values; r = rv.loc[cc].values
        # sig 의 ctrl-잔차
        A = np.vstack([np.ones_like(ct), ct]).T
        try:
            beta, *_ = np.linalg.lstsq(A, s, rcond=None)
            s_resid = s - A @ beta
            rho_p, _ = stats.spearmanr(s_resid, r)
            if not np.isnan(rho_p):
                partial_ics.append(rho_p); ns.append(len(cc))
        except Exception:
            pass
    def summ(arr, lags=12):
        if len(arr) < 6:
            return dict(ic=None, n=len(arr))
        x = pd.Series(arr)
        se = M.nw_se(x, lags); t = float(x.mean()/se) if se and se > 0 else None
        return dict(ic=round(float(np.mean(arr)), 4), n=len(arr), t_nw=round(t, 2) if t else None)
    return dict(raw_ic=summ(raw_ics), partial_ic_given_quality=summ(partial_ics),
                note="partial = ep_yield 의 gross_prof 잔차 IC. raw 와 비슷=quality 독립 / 0 수렴=quality proxy.")


def loo_year(sig, fwd):
    ic, _ = M.cs_ic(sig, fwd)
    if len(ic) < 24:
        return None
    out = {}
    for y in sorted(set(ic.index.year)):
        sub = ic[ic.index.year != y]
        out[str(y)] = round(float(sub.mean()), 4)
    full = float(ic.mean()); vals = list(out.values())
    return dict(full_ic=round(full, 4), per_year_ex=out, min_ex=min(vals), max_ex=max(vals),
                sign_stable=bool(all(np.sign(v) == np.sign(full) for v in vals)))


def main():
    px, ed, uni, macro = M.load()
    secmap = dict(zip(uni["ticker"], uni["subcl"]))
    pxm = px.resample("ME").last()
    P = M.build_pit_panels(px, ed)

    # sector-neutral z signals
    ep_z = M.cs_z(P["ep_yield"], secmap)
    per_z = M.cs_z(P["per"], secmap)
    payout_z = M.cs_z(P["payout_yield"], secmap)
    div_z = M.cs_z(P["dividend_yield"], secmap)
    earn_cv_z = M.cs_z(P["earnings_cv"], secmap)

    sigs = {"ep_yield": ep_z, "per_z": per_z, "payout_yield": payout_z,
            "dividend_yield": div_z, "earnings_cv": earn_cv_z}

    out = {"note": "★G-B 자체검증 (자문 전, team-lead 지시). regime split=value-revival era 부호일관성 핵심 falsifier."}

    # ── 1. regime split (12M horizon primary) ──
    print("=" * 90)
    print("★1. REGIME SPLIT (QE 2010-2021 vs value-revival 2022-2026), 12M horizon")
    print(f"{'signal':<16}{'full IC':>10}{'QE IC(t,n)':>20}{'2022+ IC(t,n)':>22}{'sign_consist':>14}")
    reg = {}
    for h in [6, 12]:
        fwd = pxm.shift(-h) / pxm - 1
        for name, sig in sigs.items():
            r = regime_split_ic(sig, fwd, "2022-01-01")
            if r:
                reg[f"{name}__{h}M"] = r
                if h == 12:
                    q = r["qe_2010_2021"]; hk = r["hike_2022_2026"]
                    qs = "{:+.3f}(t{},{})".format(q['ic'], q.get('t_nw'), q['n']) if q.get('ic') is not None else "n/a"
                    hs = "{:+.3f}(t{},{})".format(hk['ic'], hk.get('t_nw'), hk['n']) if hk.get('ic') is not None else "n/a"
                    print("{:<16}{:>+10.4f}{:>20}{:>22}{:>14}".format(
                        name, r['full']['ic'], qs, hs, str(r['sign_consistent'])))
    out["regime_split"] = reg

    # ── 2. partial-corr quality ──
    print("\n" + "=" * 90)
    print("★2. ANTI-VALUE vs QUALITY (ep_yield partial-corr given gross_prof), 12M")
    pc = {}
    for h in [6, 12]:
        fwd = pxm.shift(-h) / pxm - 1
        r = partial_corr_quality(P["ep_yield"], P["gross_prof"], fwd, secmap)
        pc[f"ep_yield__{h}M"] = r
        if h == 12:
            print(f"  ep_yield raw IC = {r['raw_ic']}")
            print(f"  ep_yield | gross_prof partial = {r['partial_ic_given_quality']}")
    # payout | quality 도
    for h in [12]:
        fwd = pxm.shift(-h) / pxm - 1
        r2 = partial_corr_quality(P["payout_yield"], P["gross_prof"], fwd, secmap)
        pc[f"payout_yield__{h}M"] = r2
        print(f"  payout raw IC = {r2['raw_ic']}")
        print(f"  payout | gross_prof partial = {r2['partial_ic_given_quality']}")
    out["partial_corr_quality"] = pc

    # ── 3. LOO-year ──
    print("\n" + "=" * 90)
    print("★3. LOO-YEAR (anti-value 특정 연도 의존?), 12M")
    loo = {}
    fwd12 = pxm.shift(-12) / pxm - 1
    for name in ["ep_yield", "payout_yield"]:
        r = loo_year(sigs[name], fwd12)
        loo[f"{name}__12M"] = r
        if r:
            print(f"  {name}: full={r['full_ic']:+.4f} ex-range[{r['min_ex']:+.4f},{r['max_ex']:+.4f}] sign_stable={r['sign_stable']}")
            # 가장 영향 큰 연도 (제외 시 full 에서 가장 멀어지는)
            devs = {y: abs(v - r['full_ic']) for y, v in r['per_year_ex'].items()}
            top = sorted(devs.items(), key=lambda x: -x[1])[:3]
            print(f"    most-influential years (ex-dev): {[(y, r['per_year_ex'][y]) for y,_ in top]}")
    out["loo_year"] = loo

    (ROOT / "_gb_verify.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("\nsaved _gb_verify.json")


if __name__ == "__main__":
    main()
