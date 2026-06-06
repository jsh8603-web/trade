# -*- coding: utf-8 -*-
"""measure_oos.py — bio walk-forward OOS verdict + S5 역공격 (team-lead 지시 = 현 데이터 verdict 확정).

★team-lead 박제: 불확실성 deferral 금지. 미래 데이터 없이 현 데이터로 가능한 검증 전부 = IS/OOS split.
  IS(2019-2022) / OOS(2023-2026) 부호+magnitude 유지 = in-sample artifact 아님.

측정 대상 (measure_conditional.py 발견 기반):
  1. unconditional 핵심: vol_60(저변동성, bio primary) + rev_1m(단기 reversal) IS/OOS
  2. flow_sell conditional: 외국인 순매도 국면 = bio 증폭축(family_2 interaction mom_6/mom_12_1/per_z t<-2.3)
  3. family_2 interaction term IS/OOS (flow_sell × signal)
  4. ★S5 역공격: flow_sell 이 (a) 단일 episode 종속? (b) risk-off(VIX) 대리? (c) leave-worst-episode-out
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
HORIZON_D = 20  # y_20d 메인
IS_END = "2022-12-31"
OOS_START = "2023-01-01"


def csz(panel):
    return panel.sub(panel.mean(axis=1), axis=0).div(panel.std(axis=1, ddof=1).replace(0, np.nan), axis=0)


def mask_trading_halt(px, min_run=10):
    """★거래정지 좀비 carry-forward NaN 마스킹 (bio-audit remediation, measure_conditional 미러)."""
    out = px.copy()
    for code in px.columns:
        valid = px[code].dropna()
        if len(valid) < min_run + 1:
            continue
        same = valid.diff() == 0
        grp = (~same).cumsum()
        run_len = same.groupby(grp).transform("sum")
        halt_idx = run_len[run_len >= (min_run - 1)].index
        out.loc[halt_idx, code] = np.nan
    return out


def load():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    px = mask_trading_halt(px)   # ★거래정지 좀비 carry-forward NaN 마스킹 (bio-audit remediation)
    lab = pd.read_parquet(DATA / "regime_labels.parquet"); lab.index = pd.to_datetime(lab.index)
    fin = pd.read_parquet(DATA / "dart_financials.parquet")
    uni = pd.read_parquet(DATA / "universe.parquet"); uni = uni[uni["pass_floor"]].set_index("Code")
    return px, lab, fin, uni


def build_signals(px, fin, uni):
    pxm = px.resample("ME").last()
    ret_d = px.pct_change()
    sigs = {
        "mom_6": csz(pxm / pxm.shift(6) - 1),
        "mom_12_1": csz(pxm.shift(1) / pxm.shift(12) - 1),
        "rev_1m": csz(pxm / pxm.shift(1) - 1),
        "vol_60": csz((ret_d.rolling(60).std() * np.sqrt(252)).resample("ME").last()),
    }
    # valuation (PIT, 흑자한정 PER)
    shares = {}
    for code in px.columns:
        lp = px[code].dropna()
        if len(lp) and code in uni.index:
            mc = uni.loc[code, "Marcap"]
            if pd.notna(mc) and lp.iloc[-1] > 0:
                shares[code] = mc / lp.iloc[-1]
    fin = fin.copy()
    fin["rcept_dt"] = pd.to_datetime(fin["rcept_dt"], format="%Y%m%d", errors="coerce")
    pbr_p, per_p = {}, {}
    for code in px.columns:
        if code not in shares:
            continue
        cf = fin[fin["code"] == code].sort_values("rcept_dt")
        if len(cf) == 0:
            continue
        sh = shares[code]
        pbr_s = pd.Series(index=pxm.index, dtype=float); per_s = pd.Series(index=pxm.index, dtype=float)
        for dt in pxm.index:
            avail = cf[cf["rcept_dt"] <= dt]
            if len(avail) == 0 or pd.isna(pxm.loc[dt, code]):
                continue
            eq = avail["equity"].iloc[-1]; ni = avail["net_income"].iloc[-1]
            mktcap = pxm.loc[dt, code] * sh
            if eq and eq > 0:
                pbr_s[dt] = mktcap / eq
            if ni and ni > 0:
                per_s[dt] = mktcap / ni
        pbr_p[code] = pbr_s; per_p[code] = per_s
    sigs["pbr_z"] = csz(pd.DataFrame(pbr_p)); sigs["per_z"] = csz(pd.DataFrame(per_p))
    return sigs


def fwd_returns(px, anchor, h):
    out = {}
    for dt in anchor:
        pos = px.index.searchsorted(dt)
        if pos >= len(px.index):
            continue
        p0 = min(pos, len(px.index) - 1); p1 = p0 + h
        if p1 >= len(px.index):
            continue
        out[dt] = px.iloc[p1] / px.iloc[p0] - 1
    return pd.DataFrame(out).T


def ic_series(sig, fwd, min_n=8):
    out = {}
    for dt in sig.index.intersection(fwd.index):
        sv = sig.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
        c = sv.index.intersection(rv.index)
        if len(c) < min_n:
            continue
        rho, _ = stats.spearmanr(sv.loc[c], rv.loc[c])
        if not np.isnan(rho):
            out[dt] = rho
    return pd.Series(out).sort_index()


def split_verdict(ic, label):
    is_ic = ic[ic.index <= IS_END]; oos_ic = ic[ic.index >= OOS_START]
    if len(is_ic) < 3 or len(oos_ic) < 3:
        return {"label": label, "status": "INSUFFICIENT", "n_is": len(is_ic), "n_oos": len(oos_ic)}
    im, om = float(is_ic.mean()), float(oos_ic.mean())
    keep = np.sign(im) == np.sign(om)
    mag = "magnitude 유지/강화" if abs(om) >= abs(im) * 0.5 else "magnitude 약화"
    return {"label": label, "is_ic": round(im, 4), "oos_ic": round(om, 4),
            "n_is": len(is_ic), "n_oos": len(oos_ic),
            "sign_keep": bool(keep), "verdict": ("OOS 부호유지+" + mag) if keep else "OOS 부호반전(artifact)"}


def interaction_oos(sigs, px, anchor, lab19, dummy, period=None, drop_months=None):
    """flow_sell × signal interaction term, 특정 기간(IS/OOS) 또는 leave-episode."""
    axis, rg = dummy
    fwd = fwd_returns(px, anchor, HORIZON_D)
    res = {}
    for sname, sig in sigs.items():
        rows = []
        for dt in sig.index.intersection(fwd.index):
            if dt not in lab19.index or pd.isna(lab19.loc[dt, axis]):
                continue
            if period == "IS" and dt > pd.Timestamp(IS_END):
                continue
            if period == "OOS" and dt < pd.Timestamp(OOS_START):
                continue
            if drop_months is not None and dt.year in drop_months:
                continue
            dum = 1.0 if lab19.loc[dt, axis] == rg else 0.0
            sv = sig.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
            common = sv.index.intersection(rv.index)
            if len(common) < 10:
                continue
            sr = stats.rankdata(sv.loc[common]) / len(common) - 0.5
            rr = stats.rankdata(rv.loc[common]) / len(common) - 0.5
            for i, code in enumerate(common):
                rows.append((dt, sr[i], rr[i], dum))
        if len(rows) < 80:
            res[sname] = {"status": "INSUFFICIENT", "n_obs": len(rows)}
            continue
        df = pd.DataFrame(rows, columns=["dt", "sig", "ret", "dum"])
        df["inter"] = df["sig"] * df["dum"]
        X = np.column_stack([np.ones(len(df)), df["sig"], df["inter"]]); y = df["ret"].values
        beta = np.linalg.lstsq(X, y, rcond=None)[0]; resid = y - X @ beta
        XtX_inv = np.linalg.inv(X.T @ X); meat = np.zeros((3, 3))
        for _, g in df.groupby("dt"):
            idx = df.index.isin(g.index); Xg = X[idx]; ug = resid[idx]
            meat += Xg.T @ np.outer(ug, ug) @ Xg
        V = XtX_inv @ meat @ XtX_inv; se = np.sqrt(np.diag(V))
        res[sname] = {"b_inter": round(beta[2], 4), "t_inter": round(beta[2] / se[2], 2),
                      "n_obs": len(df), "n_months": int(df["dt"].nunique())}
    return res


def main():
    px, lab, fin, uni = load()
    sigs = build_signals(px, fin, uni)
    anchor = sigs["mom_6"].dropna(how="all").index
    lab19 = lab.loc["2019-01-01":]
    fwd = fwd_returns(px, anchor, HORIZON_D)
    out = {"meta": {"is_period": "2019~2022", "oos_period": "2023~2026", "horizon_d": HORIZON_D,
                    "method": "IS/OOS split + family_2 interaction OOS + S5 역공격(episode/VIX/leave-out)"}}

    # ── 1. unconditional 핵심 신호 IS/OOS ──
    uncond = {}
    for s in ["vol_60", "rev_1m", "mom_6", "pbr_z", "per_z"]:
        ic = ic_series(sigs[s], fwd)
        uncond[s] = split_verdict(ic, f"{s} unconditional y_20d")
    out["unconditional_oos"] = uncond

    # ── 2. flow_sell conditional 신호 IS/OOS (외국인 순매도 국면) ──
    cond = {}
    flow_sell_months = lab19[lab19["flow_regime"] == "flow_sell"].index
    for s in ["mom_6", "mom_12_1", "rev_1m", "vol_60", "per_z"]:
        ic = ic_series(sigs[s], fwd)
        ic_fs = ic[ic.index.isin(flow_sell_months)]
        cond[s] = split_verdict(ic_fs, f"{s} | flow_sell y_20d")
    out["flow_sell_conditional_oos"] = cond

    # ── 3. family_2 interaction term IS/OOS (flow_sell × signal) ──
    out["interaction_is"] = interaction_oos(sigs, px, anchor, lab19, ("flow_regime", "flow_sell"), period="IS")
    out["interaction_oos"] = interaction_oos(sigs, px, anchor, lab19, ("flow_regime", "flow_sell"), period="OOS")

    # ── 4. ★S5 역공격 ──
    attack = {}
    # (a) flow_sell episode 분산 (단일 episode 종속?)
    fs_years = pd.Series([d.year for d in flow_sell_months]).value_counts().sort_index().to_dict()
    attack["episode_distribution"] = {"flow_sell_months_by_year": {int(k): int(v) for k, v in fs_years.items()},
                                       "n_total": len(flow_sell_months),
                                       "note": "여러 해 분산 = 단일 episode 종속 아님"}
    # (b) risk-off(VIX) 대리 점검: flow_sell 시 VIX 수준 vs 전체
    cf = pd.read_parquet(DATA / "common_factors.parquet"); cf.index = pd.to_datetime(cf.index)
    vix_col = [c for c in cf.columns if "vix" in c.lower() or "VIX" in c]
    if vix_col:
        vix = cf[vix_col[0]].resample("ME").last()
        vix_fs = vix[vix.index.isin(flow_sell_months)].mean()
        vix_all = vix.loc["2019-01-01":].mean()
        attack["vix_proxy_check"] = {"vix_flow_sell": round(float(vix_fs), 2), "vix_all": round(float(vix_all), 2),
                                     "note": "비슷하면 risk-off 대리 아님(진짜 flow 효과), 크게 높으면 stress 대리"}
    else:
        attack["vix_proxy_check"] = {"note": "VIX 컬럼 미발견 in common_factors", "cols": list(cf.columns)}
    # (c) leave-worst-episode-out: flow_sell 가장 많은 해 제거 후 interaction 생존?
    worst_year = max(fs_years, key=fs_years.get) if fs_years else None
    attack["leave_worst_out"] = {"dropped_year": int(worst_year) if worst_year else None,
                                 "interaction_after_drop": interaction_oos(
                                     sigs, px, anchor, lab19, ("flow_regime", "flow_sell"),
                                     drop_months={int(worst_year)} if worst_year else None)}
    out["s5_attack"] = attack

    fp = ROOT / "validation-oos-v3.json"
    fp.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Saved {fp}\n")

    print("=" * 70); print("1. UNCONDITIONAL IS/OOS (y_20d)"); print("=" * 70)
    for s, v in uncond.items():
        if "verdict" in v:
            print(f"  {s:10s} IS={v['is_ic']:+.4f} → OOS={v['oos_ic']:+.4f} (n_is={v['n_is']},n_oos={v['n_oos']}) {v['verdict']}")
    print("\n" + "=" * 70); print("2. flow_sell CONDITIONAL IS/OOS"); print("=" * 70)
    for s, v in cond.items():
        if "verdict" in v:
            print(f"  {s:10s} IS={v['is_ic']:+.4f} → OOS={v['oos_ic']:+.4f} (n_is={v['n_is']},n_oos={v['n_oos']}) {v['verdict']}")
        else:
            print(f"  {s:10s} {v['status']} (n_is={v.get('n_is')},n_oos={v.get('n_oos')})")
    print("\n" + "=" * 70); print("3. family_2 interaction (flow_sell) IS vs OOS"); print("=" * 70)
    for s in out["interaction_is"]:
        iv = out["interaction_is"][s]; ov = out["interaction_oos"].get(s, {})
        if "t_inter" in iv and "t_inter" in ov:
            print(f"  {s:10s} IS t_inter={iv['t_inter']:+.2f} → OOS t_inter={ov['t_inter']:+.2f}")
        else:
            print(f"  {s:10s} IS={iv.get('status','?')} OOS={ov.get('status','?')}")
    print("\n" + "=" * 70); print("4. S5 역공격"); print("=" * 70)
    print(f"  (a) flow_sell 연도분산: {attack['episode_distribution']['flow_sell_months_by_year']} (총 {attack['episode_distribution']['n_total']}M)")
    print(f"  (b) VIX: flow_sell={attack['vix_proxy_check'].get('vix_flow_sell')} vs 전체={attack['vix_proxy_check'].get('vix_all')}")
    print(f"  (c) leave-{attack['leave_worst_out']['dropped_year']}-out interaction:")
    for s, v in attack["leave_worst_out"]["interaction_after_drop"].items():
        if "t_inter" in v:
            print(f"      {s:10s} t_inter={v['t_inter']:+.2f}")


if __name__ == "__main__":
    main()
