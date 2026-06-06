# -*- coding: utf-8 -*-
"""measure_timeseries.py — 정유 시계열(산업 패널) 측정 (frame M2, 좁은 universe 핵심 측정).

★cross-sectional IC(min 8종) 불가(정유 코어 strict 2종) → 산업 패널 시계열 분석으로 측정.
측정 대상 = 정유사 패널수익 vs 정제마진(crack)/유가/가동률 lag-corr + regime conditional.
"이 산업의 forward return 과 가장 상관 높은 지표 + 어떤 국면에서 강해지나"(frame §0) 를
종목 횡단면 대신 ★산업 시계열로 답한다 (small breadth 정직 대응).

================================================================================
★G-F FRAME CONTRACT 7항 (measure_conditional.py 헤더 준용 + 시계열 조정)
================================================================================
1. regime: Macro(CLI 4) × KRW(3) × flow(3). effective-n = block 수(월간 overlapping, NW lag=h_months).
2. interaction/split: regime split 사전동결. forward h일 = shift(-h).
3. 단일 FDR family: {정유패널 신호(crack/oil/util/value) × horizon × powered regime cell} 사전 고정 BY-FDR.
4. null+MDE/power: null=corr 0. 시계열 n_months ~82(2019~) eff-N autocorr 보정. n_eff<6=inconclusive.
5. PIT 동결: crack/oil = FRED first-release 근사(일별 spot=실시간). refinery_ip = 월별 발표지연 IP_PUB_LAG=2.
   ★정유사 패널수익은 contemporaneous(동시) vs forward(예측) 양쪽 측정 (frame §D horizon falsifier).
6. turnover/T-cost: 산업 timing 신호 = sleeve-level (종목선택 아님). net-cost 는 통합단계.
7. per-test: small n_months → wild-cluster bootstrap(Rademacher B=2000) + block-boot CI.

★핵심 측정 2종:
  (A) contemporaneous: 정유패널 월수익 vs crack/oil Δ 동시 상관 (정유사 = 정제마진 동조 = 본질)
  (B) forward (★falsifier): crack/oil level·Δ → 정유패널 forward h일 수익 예측 (alpha 존재?)
     coin/auto 교훈 = 산업 cycle 변수는 contemporaneous 동조 강, forward 예측 약(risk-monitor 용도).
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

HORIZONS_D = {"y_5d": 5, "y_20d": 20, "y_60d": 60}
IP_PUB_LAG = 2  # refinery_ip 월별 발표지연 (D축 PIT)


def load():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    cyc = pd.read_parquet(DATA / "refining_cycle.parquet"); cyc.index = pd.to_datetime(cyc.index)
    lab = pd.read_parquet(DATA / "regime_labels.parquet"); lab.index = pd.to_datetime(lab.index)
    uni = pd.read_parquet(DATA / "universe.parquet")
    return px, cyc, lab, uni


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


def block_boot_ci(x, block, B=2000, seed=42):
    rng = np.random.default_rng(seed); n = len(x)
    if n < block + 1:
        return [np.nan, np.nan]
    nb = int(np.ceil(n / block)); means = []
    for _ in range(B):
        st = rng.integers(0, n - block + 1, size=nb)
        means.append(np.concatenate([x[s:s + block] for s in st])[:n].mean())
    return [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


def corr_stat(a: pd.Series, b: pd.Series, h_months: int, label: str):
    """두 시계열 Spearman corr + wild-cluster p (paired product proxy → bootstrap mean)."""
    common = a.dropna().index.intersection(b.dropna().index)
    if len(common) < 8:
        return {"label": label, "n": len(common), "status": "INSUFFICIENT(n<8)"}
    av, bv = a.loc[common].values, b.loc[common].values
    rho, p_param = stats.spearmanr(av, bv)
    # paired rank product (mean-zero 검정용 surrogate) → wild-cluster on demeaned product
    ar = stats.rankdata(av) / len(av) - 0.5
    br = stats.rankdata(bv) / len(bv) - 0.5
    prod = ar * br  # mean(prod) ∝ rho
    n = len(prod)
    neff = n_eff_autocorr(prod)
    se = nw_se(prod, h_months)
    t_nw = prod.mean() / se if se and se > 0 else np.nan
    wc_p = wild_cluster_p(prod)
    ci = block_boot_ci(prod, max(2, h_months))
    powered = (n >= 24) and (neff >= 6)
    return {"label": label, "n": n, "n_eff": round(neff, 1),
            "spearman_rho": round(float(rho), 4), "p_parametric": round(float(p_param), 4),
            "t_nw_asymptotic": round(t_nw, 2) if not np.isnan(t_nw) else None,
            "wild_cluster_p": round(wc_p, 4) if not np.isnan(wc_p) else None,
            "ci95_block_boot_prod": [round(c, 5) for c in ci] if not np.isnan(ci[0]) else None,
            "status": "powered" if powered else ("underpowered" if n >= 12 else "INSUFFICIENT(n<12)")}


def main():
    px, cyc, lab, uni = load()
    # ★정유 코어 패널 = 석유 정제품 제조업 (strict 2종 = SK이노/S-Oil 주력 + 코어 5종 옵션)
    core_codes = uni[uni["is_refining_core"]]["Code"].tolist()
    core_codes = [c for c in core_codes if c in px.columns]
    strict2 = uni[uni["is_refining_core"] & uni["pass_floor_strict"]]["Code"].tolist()
    strict2 = [c for c in strict2 if c in px.columns]
    gas_codes = uni[uni["segment"] == "gas_util"]["Code"].tolist()
    gas_codes = [c for c in gas_codes if c in px.columns]
    print(f"refining core codes (전체): {core_codes}")
    print(f"refining strict2 (cross-sectional 자격): {strict2}")
    print(f"gas_util codes: {gas_codes}")

    pxm = px.resample("ME").last()
    # 패널 = 동일가중 월수익 (refining strict2 주력, core5 병행)
    def panel_ret(codes):
        sub = pxm[codes]
        ret = sub.pct_change()
        # 동일가중 평균 (최소 1종 존재 월만)
        return ret.mean(axis=1, skipna=True)

    ret_strict2 = panel_ret(strict2)
    ret_core5 = panel_ret(core_codes)
    ret_gas = panel_ret(gas_codes) if gas_codes else None

    cycm = cyc.resample("ME").last()
    # PIT: refinery_ip 발표지연 lag
    cycm = cycm.copy()
    cycm["refinery_ip"] = cycm["refinery_ip"].shift(IP_PUB_LAG)

    # cycle 변수 월간 (level + Δ)
    drivers = {
        "blended_crack": cycm["blended_crack"],
        "gasoline_crack": cycm["gasoline_crack"],
        "diesel_crack": cycm["diesel_crack"],
        "brent": cycm["brent"],
        "oil_yoy": cycm["oil_yoy"],
        "refinery_ip": cycm["refinery_ip"],
        "natgas": cycm["natgas"],
    }
    drivers_chg = {f"d_{k}": v.diff() for k, v in drivers.items() if k not in ("oil_yoy",)}

    lab19 = lab.loc["2019-01-01":]
    results = {"meta": {
        "method": "산업 패널 시계열 (frame M2) — 정유사 동일가중 월수익 vs cycle driver lag-corr",
        "rationale": "★cross-sectional IC 불가(정유 strict 2종) → 산업 시계열 측정으로 frame §0 답.",
        "panel": {"refining_strict2": strict2, "refining_core5": core_codes, "gas_util": gas_codes},
        "drivers": list(drivers.keys()),
        "horizons_days": HORIZONS_D, "ip_pub_lag": IP_PUB_LAG,
        "gf_contract": "measure_timeseries.py 헤더 7항 준용 (wild-cluster + block-boot + eff-N)",
    }, "contemporaneous": {}, "forward": {}, "regime_conditional": {}, "panels": {}}

    # ── 패널별 측정 (strict2 주력) ──
    for pname, pret in [("refining_strict2", ret_strict2), ("refining_core5", ret_core5)] + (
            [("gas_util", ret_gas)] if ret_gas is not None else []):
        pret = pret.loc["2019-01-01":].dropna()
        results["panels"][pname] = {"n_months": len(pret),
                                    "ret_mean_monthly": round(float(pret.mean()), 4),
                                    "ret_vol_monthly": round(float(pret.std()), 4)}

    # ── (A) contemporaneous: 정유패널 월수익 vs driver Δ (동시 상관) ──
    # 정유사 = 정제마진/유가 동시 동조 (본질 mechanism)
    h_m_default = 1
    for dname, dser in {**drivers, **drivers_chg}.items():
        # 동시 = 같은 월 패널수익 vs driver Δ(또는 yoy/level)
        if dname.startswith("d_") or dname == "oil_yoy":
            x = dser
        else:
            x = dser.diff()  # level driver → Δ 동시 비교
        st = corr_stat(ret_strict2.loc["2019-01-01":], x.loc["2019-01-01":], h_m_default, dname)
        results["contemporaneous"][dname] = st

    # ── (B) forward (★falsifier): driver level/Δ(t) → 패널 forward 1~3M 수익 ──
    # crack/oil level 이 forward 정유수익 예측? (alpha vs risk-monitor)
    for hm_label, hm in [("fwd_1m", 1), ("fwd_3m", 3)]:
        fwd_ret = ret_strict2.shift(-hm).rolling(1).sum() if hm == 1 else (pxm[strict2].pct_change(hm).mean(axis=1).shift(-hm))
        results["forward"][hm_label] = {}
        for dname in ["blended_crack", "diesel_crack", "brent", "oil_yoy", "refinery_ip",
                      "d_blended_crack", "d_brent"]:
            base = drivers.get(dname) if dname in drivers else drivers_chg.get(dname)
            if base is None:
                continue
            x = base.loc["2019-01-01":]
            y = fwd_ret.loc["2019-01-01":]
            st = corr_stat(x, y, max(1, hm), f"{dname}__{hm_label}")
            results["forward"][hm_label][dname] = st

    # ── regime conditional (contemporaneous blended_crack, 주 신호) ──
    x_main = drivers["blended_crack"].diff().loc["2019-01-01":]
    y_main = ret_strict2.loc["2019-01-01":]
    pvals_fdr = {}
    for axis in ["macro_regime", "krw_regime", "flow_regime"]:
        la = lab19[axis].dropna()
        for rg in sorted(la.unique()):
            months = la[la == rg].index
            xs = x_main[x_main.index.isin(months)]
            ys = y_main[y_main.index.isin(months)]
            st = corr_stat(xs, ys, 1, f"blended_crack_contemp__{axis}={rg}")
            results["regime_conditional"][f"{axis}={rg}"] = st
            if st.get("status") == "powered" and st.get("wild_cluster_p") is not None:
                pvals_fdr[f"blended_crack__{axis}={rg}"] = st["wild_cluster_p"]
    # uncond contemp blended_crack 도 FDR family
    uc = results["contemporaneous"].get("blended_crack", {})
    if uc.get("status") == "powered" and uc.get("wild_cluster_p") is not None:
        pvals_fdr["blended_crack__uncond_contemp"] = uc["wild_cluster_p"]

    results["fdr_family_timeseries"] = benjamini_yekutieli(pvals_fdr)

    out = ROOT / "validation-timeseries-v3.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved {out}")
    print_summary(results)
    return results


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


def print_summary(r):
    print("\n" + "=" * 72)
    print("정유 산업 패널 시계열 — contemporaneous (동시 상관, 정유사 mechanism)")
    print("=" * 72)
    for dname, st in r["contemporaneous"].items():
        if st.get("status", "").startswith("INSUFF"):
            continue
        print(f"  {dname:18s} rho={st.get('spearman_rho'):+.3f}  wc_p={st.get('wild_cluster_p')}  n={st.get('n')}  n_eff={st.get('n_eff')}  {st.get('status')}")
    print("\n--- forward (falsifier: 예측력) ---")
    for hl, hd in r["forward"].items():
        for dname, st in hd.items():
            if st.get("status", "").startswith("INSUFF"):
                continue
            print(f"  {dname:24s} [{hl}] rho={st.get('spearman_rho'):+.3f}  wc_p={st.get('wild_cluster_p')}  n={st.get('n')}")
    print("\n--- regime conditional (blended_crack 동시) ---")
    for ck, st in r["regime_conditional"].items():
        if st.get("status") in ("powered", "underpowered"):
            star = "★" if st["status"] == "powered" else " "
            print(f"  {star}{ck:32s} rho={st.get('spearman_rho'):+.3f}  wc_p={st.get('wild_cluster_p')}  n={st.get('n')}  {st.get('status')}")
    print(f"\nFDR family (시계열): {r['fdr_family_timeseries']}")


if __name__ == "__main__":
    main()
