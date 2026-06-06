# -*- coding: utf-8 -*-
"""measure_ts_robustness.py — 정유 시계열 신호 robustness (S4/S5, small-n §1.7 ADF + OOS + leave-episode).

★측정 핵심 = forward 음(-) 신호(brent/oil_yoy/refinery_ip → 정유 forward 3M 수익 음)가
  spurious(level-on-level 비정상) 아닌 진짜 mean-reversion 인지 검증.

검증 5종:
  1. ADF 단위근 (brent level / 정유 forward ret) — level-on-level spurious 점검 (§1.7-A)
  2. walk-forward OOS (IS 2019-22 / OOS 2023-26) — 부호+magnitude 유지
  3. leave-episode (2020 covid / 2022 우크라 crack spike 제외 후 생존)
  4. contemporaneous vs forward 부호 대조 (§1.8-4 rebound artifact 의심)
  5. eff-N 보정 t (60d/3M 중첩 autocorr)
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

try:
    from statsmodels.tsa.stattools import adfuller
    HAS_SM = True
except Exception:
    HAS_SM = False


def load():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    cyc = pd.read_parquet(DATA / "refining_cycle.parquet"); cyc.index = pd.to_datetime(cyc.index)
    uni = pd.read_parquet(DATA / "universe.parquet")
    return px, cyc, uni


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


def spearman_with_neff(x, y, label):
    common = x.dropna().index.intersection(y.dropna().index)
    if len(common) < 8:
        return {"label": label, "n": len(common), "status": "INSUFFICIENT"}
    av, bv = x.loc[common].values, y.loc[common].values
    rho, p = stats.spearmanr(av, bv)
    # eff-N: forward ret 시계열 autocorr (3M 중첩)
    neff = n_eff_autocorr(bv)
    # t with eff-N: rho*sqrt((neff-2)/(1-rho^2))
    if abs(rho) < 1 and neff > 2:
        t_eff = rho * np.sqrt((neff - 2) / (1 - rho ** 2))
    else:
        t_eff = np.nan
    t_naive = rho * np.sqrt((len(common) - 2) / (1 - rho ** 2)) if abs(rho) < 1 else np.nan
    return {"label": label, "n": len(common), "n_eff": round(neff, 1),
            "spearman_rho": round(float(rho), 4), "p_parametric": round(float(p), 4),
            "t_naive": round(float(t_naive), 2) if not np.isnan(t_naive) else None,
            "t_eff_corrected": round(float(t_eff), 2) if not np.isnan(t_eff) else None}


def main():
    px, cyc, uni = load()
    strict2 = uni[uni["is_refining_core"] & uni["pass_floor_strict"]]["Code"].tolist()
    strict2 = [c for c in strict2 if c in px.columns]
    pxm = px.resample("ME").last()
    ret = pxm[strict2].pct_change().mean(axis=1)

    cycm = cyc.resample("ME").last()
    brent = cycm["brent"]
    oil_yoy = cycm["oil_yoy"]
    refip = cycm["refinery_ip"].shift(2)
    crack = cycm["blended_crack"]
    diesel_crack = cycm["diesel_crack"]

    # forward 3M 정유 수익
    fwd3 = pxm[strict2].pct_change(3).mean(axis=1).shift(-3)

    out = {"meta": {"panel": strict2, "n_months": int(ret.loc["2019":].dropna().shape[0]),
                    "has_statsmodels": HAS_SM,
                    "purpose": "forward 음(-) 신호 spurious(level-on-level) vs 진짜 mean-reversion 검증"},
           "adf": {}, "forward_fullsample": {}, "walk_forward_oos": {},
           "leave_episode": {}, "contemp_vs_forward": {}}

    # ── 1. ADF 단위근 (§1.7-A level-on-level spurious) ──
    if HAS_SM:
        for nm, s in [("brent_level", brent), ("oil_yoy", oil_yoy), ("refinery_ip", refip),
                      ("blended_crack", crack), ("refining_fwd3_ret", fwd3),
                      ("refining_monthly_ret", ret), ("d_brent", brent.diff())]:
            sv = s.loc["2019":].dropna()
            if len(sv) >= 12:
                try:
                    r = adfuller(sv.values, regression="c", autolag="AIC")
                    out["adf"][nm] = {"adf_stat": round(r[0], 3), "p_value": round(r[1], 4),
                                      "I_class": "I(0) stationary" if r[1] < 0.05 else "I(1) 의심(비정상)"}
                except Exception as e:
                    out["adf"][nm] = {"error": str(e)[:50]}
    else:
        out["adf"]["note"] = "statsmodels 부재 — ADF skip (fallback: level vs Δ 부호 대조로 spurious 간접 점검)"

    # ── 2. forward full-sample (level + Δ 둘 다, spurious 점검) ──
    for nm, s in [("brent_level", brent), ("oil_yoy", oil_yoy), ("refinery_ip", refip),
                  ("blended_crack_level", crack), ("diesel_crack_level", diesel_crack),
                  ("d_brent", brent.diff()), ("d_blended_crack", crack.diff())]:
        out["forward_fullsample"][nm] = spearman_with_neff(s.loc["2019":], fwd3.loc["2019":], f"{nm}__fwd3")

    # ── 3. walk-forward OOS (IS 2019-22 / OOS 2023-26) ──
    for nm, s in [("brent_level", brent), ("oil_yoy", oil_yoy), ("refinery_ip", refip),
                  ("blended_crack_level", crack), ("diesel_crack_level", diesel_crack)]:
        x = s; y = fwd3
        is_idx = pd.date_range("2019-01-01", "2022-12-31", freq="ME")
        oos_idx = pd.date_range("2023-01-01", "2026-05-31", freq="ME")
        def sub_rho(idx):
            xi = x.reindex(idx).dropna(); yi = y.reindex(idx).dropna()
            c = xi.index.intersection(yi.index)
            if len(c) < 6:
                return None, len(c)
            return float(stats.spearmanr(xi.loc[c], yi.loc[c])[0]), len(c)
        ir, inn = sub_rho(is_idx); orr, onn = sub_rho(oos_idx)
        out["walk_forward_oos"][nm] = {
            "is_rho": round(ir, 4) if ir is not None else None, "is_n": inn,
            "oos_rho": round(orr, 4) if orr is not None else None, "oos_n": onn,
            "sign_hold": bool(ir is not None and orr is not None and np.sign(ir) == np.sign(orr)),
        }

    # ── 4. leave-episode (2020 covid + 2022 우크라 제외) ──
    for nm, s in [("brent_level", brent), ("oil_yoy", oil_yoy), ("refinery_ip", refip)]:
        full = spearman_with_neff(s.loc["2019":], fwd3.loc["2019":], nm)
        # 2020 covid 제외 (2020-01~2020-12)
        mask_cov = ~((s.index >= "2020-01-01") & (s.index <= "2020-12-31"))
        # 2022 우크라 제외 (2022-02~2022-12)
        mask_ukr = ~((s.index >= "2022-02-01") & (s.index <= "2022-12-31"))
        s_lo = s[mask_cov & mask_ukr]
        lo = spearman_with_neff(s_lo.loc["2019":], fwd3.loc["2019":], f"{nm}_leaveepi")
        out["leave_episode"][nm] = {
            "full_rho": full.get("spearman_rho"), "full_n": full.get("n"),
            "leave_covid_ukraine_rho": lo.get("spearman_rho"), "leave_n": lo.get("n"),
            "survive": bool(full.get("spearman_rho") and lo.get("spearman_rho") and
                            np.sign(full["spearman_rho"]) == np.sign(lo["spearman_rho"]))}

    # ── 5. contemporaneous vs forward 부호 대조 (§1.8-4 rebound artifact) ──
    ret_same = ret  # 동시
    for nm, s in [("brent", brent.diff()), ("oil_yoy", oil_yoy), ("refinery_ip", refip.diff())]:
        contemp = spearman_with_neff(s.loc["2019":], ret_same.loc["2019":], f"{nm}_contemp")
        forward = spearman_with_neff(s.loc["2019":], fwd3.loc["2019":], f"{nm}_fwd3")
        cr, fr = contemp.get("spearman_rho"), forward.get("spearman_rho")
        out["contemp_vs_forward"][nm] = {
            "contemp_rho": cr, "forward_rho": fr,
            "sign_flip": bool(cr and fr and np.sign(cr) != np.sign(fr)),
            "interpretation": "rebound/mean-reversion artifact 의심 (동시≠예측 부호)" if (cr and fr and np.sign(cr) != np.sign(fr)) else "부호 일관"}

    (ROOT / "validation-ts-robustness-v3.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    # ── 출력 ──
    print("=== 1. ADF 단위근 (level-on-level spurious 점검) ===")
    for k, v in out["adf"].items():
        print(f"  {k:24s} {v}")
    print("\n=== 2. forward 3M full-sample (level vs Δ, eff-N 보정) ===")
    for k, v in out["forward_fullsample"].items():
        if v.get("status") == "INSUFFICIENT": continue
        print(f"  {k:22s} rho={v['spearman_rho']:+.3f} n={v['n']} n_eff={v['n_eff']} t_naive={v['t_naive']} t_eff={v['t_eff_corrected']}")
    print("\n=== 3. walk-forward OOS (IS19-22 / OOS23-26) ===")
    for k, v in out["walk_forward_oos"].items():
        print(f"  {k:22s} IS={v['is_rho']}(n{v['is_n']}) OOS={v['oos_rho']}(n{v['oos_n']}) {'HOLD' if v['sign_hold'] else 'FLIP'}")
    print("\n=== 4. leave-episode (2020covid + 2022우크라 제외) ===")
    for k, v in out["leave_episode"].items():
        print(f"  {k:22s} full={v['full_rho']}(n{v['full_n']}) leave={v['leave_covid_ukraine_rho']}(n{v['leave_n']}) {'survive' if v['survive'] else 'DIE'}")
    print("\n=== 5. contemporaneous vs forward 부호 대조 ===")
    for k, v in out["contemp_vs_forward"].items():
        print(f"  {k:18s} contemp={v['contemp_rho']:+} forward={v['forward_rho']:+}  {v['interpretation']}")
    print("\nSaved validation-ts-robustness-v3.json")


if __name__ == "__main__":
    main()
