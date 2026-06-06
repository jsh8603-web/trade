# -*- coding: utf-8 -*-
"""measure_rotation_ship.py — 조선 ★업종 rotation 신호 (team-lead 지시 2026-06-05, 신조선가 proxy 재탐색).

★rotation = 종목선택 아니라 "어느 국면 → 조선 업종 OW/UW" (frame M2 시계열, _rotation 미러).
측정 = cycle 신호 → 조선 업종 eq-weight forward return(20d/60d) timing IC.

★배경 (rotation-analyst v2 = 조선 REJECTED):
  v2 = baltic_dry_yoy(BDI 운임) IC -0.091 (사전확약 양인데 실측 음 = 미성립). 결론 = 신조선가가 진짜 driver인데 무료 부재.

★team-lead 지시 = ① 신조선가 무료 proxy 재탐색 + ② BDI 왜 안 맞나 이론 정리.
  ★Gemini 리서치(하나증권 최광식/메리츠 배기종/NH 2023) 결론:
  (1) 신조선가 = 주가가 6-12M 선행 → 신조선가 자체 = 후행 = rotation 선행신호 부적합.
  (2) BDI 부적합 = ★선종 불일치(결정적): BDI=벌크선, 한국 조선=LNG/컨테이너/탱커/VLCC. + 운임=해운사 수익(조선 수주 아님) + 18M lag.
  (3) ★무료 proxy 최우선 = ★해운사 주가(탱커/컨테이너 = 조선 고객 발주여력·의지 선행 반영). 후판가=이중성(원가-/수요+), BOAT=좋은 macro.

★신호 (cycle_shipbuilding_v2.parquet, yfinance proxy):
  - tanker_basket (TNK/STNG/FRO momentum)    = ★VLCC/탱커 발주 수요 선행. 부호확약 ★양 (고객 발주여력↑→조선↑).
  - container_basket (GSL/DAC/ZIM momentum)  = ★ULCS 컨테이너선 발주 수요 선행. 부호확약 ★양.
  - lng_demand (LNG=Cheniere momentum)       = LNG선 수요 proxy. 부호확약 ★양 (LNG 수출↑→LNG선 발주).
  - steel_plate (HRC yoy)                     = 후판 원가. ★two-sided (원가 역 / 수요견인 동행, Gemini 이중성).
  - boat_etf (BOAT momentum)                  = 글로벌 조선해운 macro. 부호확약 ★양 (2021~ 짧음).
  ★신조선가 직접 = 무료 부재 + 후행이라 부적합 → 고객 해운사 주가가 선행 proxy (이론 우월).

================================================================================
★G-F FRAME CONTRACT 7항 (measure_rotation_v2.py 준용)
1. regime: 조선 업종 forward = 시계열 timing. eff-n = n/(1+2Σρ) (proxy momentum persistence).
2. forward h = shift(-h). 신호 t → 조선 업종 forward t+h (predictive).
3. 단일 FDR family: {5 proxy × 2 horizon × (yoy/d3 변환)} BY-FDR. v2 baltic 과 동일 family 합산은 통합단계.
4. null+MDE/power: t_obs=|IC|·√n_eff ⋚ 2.802. underpowered=gated.
5. PIT: proxy spot=실시간(lag X). forward=shift. ★proxy=US-listed = 글로벌 cycle proxy(KR 직접 아님 한계 박제).
6. turnover/T-cost: 통합단계.
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
DATA = ROOT / "data"
OOS_SPLIT = "2023-01-01"
T_BREAKEVEN = 2.802

# 부호 사전확약 (one-sided pre-commit, 데이터 접촉 前 동결)
# ★team-lead ≥8 후보: v2(5) + add(6) = 11 후보. 신조선가 직접 = 무료부재(후행 부적합).
PRIOR_SIGN = {
    # cycle_shipbuilding_v2.parquet (해운사/후판/LNG)
    "tanker_basket": "+", "container_basket": "+", "lng_demand": "+",
    "boat_etf": "+", "steel_plate": "two-sided",
    # cycle_shipbuilding_add.parquet (환율/유가/철강/BDI/중국)
    "usdkrw": "+",        # ★원화약세(USDKRW↑) → 조선 수출주 수익성↑ (H1)
    "oil_wti": "+",       # ★유가 → 해양플랜트/LNG선 수요 (H8)
    "steel_etf": "two-sided",   # ★철강 ETF = 후판 원가 cycle (이중성, HRC 보완)
    "iron_ore": "two-sided",    # ★철광석 = 후판 원료 (이중성)
    "baltic_bdry": "+",  # ★BDI 운임 (v2 REJECTED 재현, 선종불일치)
    "china_proxy": "-",  # ★중국(FXI) = 중국조선 수주점유 proxy (중국↑→한국 점유↓ 가능)
}
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
    rng = np.random.default_rng(seed); sd = x.std(ddof=1)
    t_obs = abs(x.mean() / (sd / np.sqrt(n))) if sd > 0 else 0.0
    e = x - x.mean(); cnt = 0
    for _ in range(B):
        w = rng.choice([-1.0, 1.0], size=n); xn = w * e; sb = xn.std(ddof=1)
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


def ship_industry_return(px):
    """조선 업종 eq-weight 월간 수익 (rotation 종속변수)."""
    pxm = px.resample("ME").last()
    return pxm.pct_change().mean(axis=1)


def timing_corr(sig, fwd, h):
    """신호(t) → 조선 업종 forward(t→t+h) Spearman + wild-cluster (시계열 timing IC)."""
    df = pd.concat([sig.rename("s"), fwd.rename("r")], axis=1).dropna()
    if len(df) < 18:
        return None
    rho, p_param = stats.spearmanr(df["s"], df["r"])
    sc = (df["s"] - df["s"].mean()).values
    rc = (df["r"] - df["r"].mean()).values
    prod = sc * rc / (df["s"].std() * df["r"].std() + 1e-12)
    neff = n_eff_autocorr(df["s"].values)
    wc_p = wild_cluster_p(prod)
    ci = block_boot_ci(prod, block=max(3, h))
    t_obs = abs(rho) * np.sqrt(max(neff, 1))
    return {"spearman_rho": round(float(rho), 4), "p_param": round(float(p_param), 4),
            "n": len(df), "n_eff": round(neff, 1),
            "t_power_mde": round(float(t_obs), 2),
            "wild_cluster_p": round(wc_p, 4) if not np.isnan(wc_p) else None,
            "ci95_block_boot_prod": [round(v, 5) for v in ci],
            "status": "powered" if (neff >= 12 and t_obs >= T_BREAKEVEN) else
                      ("underpowered" if neff >= 8 else "INSUFFICIENT")}


def walk_forward(sig, fwd, h):
    df = pd.concat([sig.rename("s"), fwd.rename("r")], axis=1).dropna()
    is_df = df[df.index < OOS_SPLIT]; oos_df = df[df.index >= OOS_SPLIT]
    if len(is_df) < 12 or len(oos_df) < 8:
        return {"eligible": False, "verdict": "n 부족"}
    r_is = stats.spearmanr(is_df["s"], is_df["r"])[0]
    r_oos = stats.spearmanr(oos_df["s"], oos_df["r"])[0]
    hold = np.sign(r_is) == np.sign(r_oos)
    return {"is_n": len(is_df), "oos_n": len(oos_df),
            "rho_is": round(float(r_is), 4), "rho_oos": round(float(r_oos), 4),
            "eligible": bool(hold), "verdict": "OOS 부호유지" if hold else "★OOS flip"}


def main():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    cyc = pd.read_parquet(DATA / "cycle_shipbuilding_v2.parquet"); cyc.index = pd.to_datetime(cyc.index)
    # ★team-lead ≥8 후보: add parquet(환율/유가/철강/BDI/중국) 병합
    add_path = DATA / "cycle_shipbuilding_add.parquet"
    if add_path.exists():
        add = pd.read_parquet(add_path); add.index = pd.to_datetime(add.index)
        cyc = cyc.join(add, how="outer")
    ship_ret = ship_industry_return(px)
    cyc_m = cyc.resample("ME").last()
    pxm = px.resample("ME").last()

    results = {"meta": {
        "method": "★조선 업종 rotation: cycle proxy(t) → 조선 eq-weight forward return(t+h) timing IC. cross-sectional 아님.",
        "rotation_v2_baltic": "v2 baltic_dry_yoy IC -0.091 REJECTED(사전확약 양인데 실측 음). 본 측정 = 신조선가 proxy 재탐색.",
        "proxy_theory": "★Gemini(하나/메리츠/NH 2023): 신조선가=주가 6-12M 후행=부적합. BDI=선종불일치(벌크 vs LNG/컨테이너/탱커). ★해운사 주가=고객 발주여력 선행=최우선 proxy.",
        "prior_sign": PRIOR_SIGN,
        "proxy_limit": "★proxy = US-listed(글로벌, KR 직접 아님). 신조선가 직접 = 무료 부재(Clarksons 유료) + 후행이라 부적합.",
    }, "signals": {}}

    pvals = {}
    for pname in cyc_m.columns:
        # 신호 변환: yoy (12M) + d3 (3M momentum) 둘 다 (v2 양식 미러)
        raw = cyc_m[pname]
        sig_yoy = raw / raw.shift(12) - 1
        sig_d3 = raw / raw.shift(3) - 1
        for vname, sig in [("yoy", sig_yoy), ("d3", sig_d3)]:
            for hname, h in HORIZONS_M.items():
                fwd = (pxm.shift(-h) / pxm - 1).mean(axis=1)  # 조선 업종 forward h개월
                r = timing_corr(sig, fwd, h)
                if r is None:
                    continue
                r["walk_forward_oos"] = walk_forward(sig, fwd, h)
                r["prior_sign"] = PRIOR_SIGN.get(pname, "?")
                # 부호 일치 점검 (사전확약 vs 실측)
                exp = PRIOR_SIGN.get(pname, "?")
                act = "+" if r["spearman_rho"] > 0 else "-"
                r["sign_match"] = (exp == act) if exp in ("+", "-") else "two-sided"
                key = f"{pname}_{vname}__{hname}"
                results["signals"][key] = r
                if r["status"] == "powered" and r.get("wild_cluster_p") is not None:
                    pvals[key] = r["wild_cluster_p"]

    results["fdr_family"] = by_fdr(pvals)
    out = ROOT / "validation-rotation-ship-v2.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Saved {out}\n")
    print("=== 조선 업종 rotation 신호 (신조선가 proxy 재탐색, 부호확약 vs 실측) ===")
    print(f"{'signal':32s}{'IC':>9}{'wc_p':>8}{'n':>5}{'n_eff':>7}{'t_mde':>7}  {'prior':>9} {'match':>6} {'OOS':>10}")
    for k, v in sorted(results["signals"].items(), key=lambda x: -abs(x[1]["spearman_rho"])):
        oos = v["walk_forward_oos"].get("verdict", "")
        print(f"{k:32s}{v['spearman_rho']:>+9.4f}{str(v['wild_cluster_p']):>8}{v['n']:>5}{v['n_eff']:>7.1f}{v['t_power_mde']:>7.2f}  {v['prior_sign']:>9} {str(v['sign_match']):>6} {oos:>10}  [{v['status']}]")
    print(f"\nFDR family: {results['fdr_family']}")


def by_fdr(pvals, q=0.10):
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    m = len(items)
    if m == 0:
        return {"m": 0, "note": "powered cell 0 (전부 underpowered/INSUFFICIENT)"}
    items.sort(key=lambda x: x[1])
    c_m = sum(1.0 / i for i in range(1, m + 1)); surv = []
    for ri, (k, p) in enumerate(items, 1):
        if p <= (ri / m) * q / c_m:
            surv = [items[j][0] for j in range(ri)]
    return {"m": m, "by_factor": round(c_m, 3), "survivors_BY": surv,
            "raw_p_min": round(items[0][1], 5), "raw_p_min_key": items[0][0]}


if __name__ == "__main__":
    main()
