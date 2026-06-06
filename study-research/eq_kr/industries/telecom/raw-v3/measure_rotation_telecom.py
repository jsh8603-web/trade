# -*- coding: utf-8 -*-
"""measure_rotation_telecom.py — 통신 업종 rotation 신호 (업종 자체 OW/UW, 종목선택 아님).

★rotation = "어느 국면에 통신 업종 비중↑/↓" (sector timing). 종목선택(cross-sectional)은 3사 과점 INSUFFICIENT.
★패널 = 통신서비스 strict 화이트리스트 SKT(017670)/KT(030200)/LGU+(032640) 동일가중 (team-lead 지시).

★핵심 검증 (team-lead 지시): 1차 rotation-analyst mom_12_1 +0.284(y_60d) + semi_ppi_yoy -0.334 가격통계 발견.
  → 이 통계가 통신 산업동향 이론으로 설명되나? 안 되면 data-mining 채택불가.
  통신 = defensive 고배당 bond-proxy → 이론 framework:
   (1) ★defensive counter-cyclical rotation: 경기/반도체 cycle 강세(semi_ppi↑) → 자금이 defensive 통신서 cyclical로 이탈 → 통신 UW. = semi_ppi 음의 이론 근거(risk-on/off defensive rotation).
   (2) ★dividend-carry persistence: 고배당 defensive = carry/flow 누적 → momentum. mom_12_1 양의 이론 근거(단 검증 필요).
   (3) ★배당 duration: 금리↓ → 통신 OW(bond-proxy 리레이팅). 금리 cycle rotation.
  ★mom_12_1 residualize on {semi_ppi, flow, rate} → 잔차 mom 신호 잔존? 잔존=독립 carry / 소멸=공통인자 재포장(data-mining).

================================================================================
★G-F FRAME CONTRACT 7항 (rotation 적용)
================================================================================
1. regime: sector-timing. effective-n = block 수(월간 overlapping, NW lag=h_months).
2. interaction/split: forward h일 = shift(-h). 부호 사전확약(theory-notes rotation §).
3. 단일 FDR family: {telecom rotation 후보 × horizon} 사전 고정 BY-FDR.
4. null+MDE/power: null=corr 0. n_months~85. t_obs ⋚ 2.802 (breakeven). underpowered 라벨.
5. PIT 동결: driver = 월말 가용분(semi_ppi 발표지연 / KR rate FRED 월별). 가격 forward shift(-h).
6. turnover/T-cost: sector-timing = sleeve-level (종목 turnover 없음). overlay weight.
7. per-test: small n → wild-cluster bootstrap(Rademacher B=2000) + block-boot CI + eff-N.

★합성 ⛔. 실 pykrx 가격 + FRED KR rate + regime_series(semi_ppi/flow/cli/usdkrw). raw 재현.
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
SERVICE = ["017670", "030200", "032640"]  # SKT / KT / LGU+ (strict 화이트리스트)
HORIZONS = {"y_20d": 1, "y_60d": 3}  # months
T_BREAKEVEN = 2.802


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


def corr_stat(a: pd.Series, b: pd.Series, h_months: int, label: str):
    common = a.dropna().index.intersection(b.dropna().index)
    if len(common) < 8:
        return {"label": label, "n": len(common), "status": "INSUFFICIENT(n<8)"}
    av, bv = a.loc[common].values, b.loc[common].values
    rho, p_param = stats.spearmanr(av, bv)
    ar = stats.rankdata(av) / len(av) - 0.5
    br = stats.rankdata(bv) / len(bv) - 0.5
    prod = ar * br
    n = len(prod); neff = n_eff_autocorr(prod)
    se = nw_se(prod, h_months)
    t_nw = prod.mean() / se if se and se > 0 else np.nan
    # power MDE: t_obs = |rho|·sqrt(neff)  (rank-corr 근사)
    t_power = float(abs(rho) * np.sqrt(max(neff, 1)))
    wc_p = wild_cluster_p(prod)
    ci = block_boot_ci(prod, max(2, h_months))
    powered = (n >= 24) and (neff >= 6)
    return {"label": label, "n": n, "n_eff": round(neff, 1),
            "spearman_rho": round(float(rho), 4), "p_parametric": round(float(p_param), 4),
            "t_nw": round(t_nw, 2) if not np.isnan(t_nw) else None,
            "t_power_mde": round(t_power, 2),
            "well_powered": bool(t_power >= T_BREAKEVEN),
            "wild_cluster_p": round(wc_p, 4) if not np.isnan(wc_p) else None,
            "ci95_block_boot_prod": [round(c, 5) for c in ci] if not np.isnan(ci[0]) else None,
            "status": "powered" if powered else ("underpowered" if n >= 12 else "INSUFFICIENT(n<12)")}


def walk_forward(a, b, split="2023-01-01"):
    common = a.dropna().index.intersection(b.dropna().index)
    isx = common[common < split]; oosx = common[common >= split]
    if len(isx) < 8 or len(oosx) < 8:
        return {"eligible": False, "verdict": "n 부족"}
    r_is, _ = stats.spearmanr(a.loc[isx].values, b.loc[isx].values)
    r_oos, _ = stats.spearmanr(a.loc[oosx].values, b.loc[oosx].values)
    hold = (not np.isnan(r_is) and not np.isnan(r_oos) and np.sign(r_is) == np.sign(r_oos))
    return {"is_n": len(isx), "oos_n": len(oosx), "rho_is": round(float(r_is), 4),
            "rho_oos": round(float(r_oos), 4), "eligible": bool(hold),
            "verdict": "OOS 부호유지" if hold else "OOS flip"}


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


def main():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    rs = pd.read_parquet(DATA / "regime_series.parquet"); rs.index = pd.to_datetime(rs.index)
    cyc = pd.read_parquet(DATA / "telecom_cycle.parquet"); cyc.index = pd.to_datetime(cyc.index)

    pxm = px.resample("ME").last()
    sec_ret = pxm[SERVICE].pct_change().mean(axis=1, skipna=True)  # 통신 업종 동일가중 월수익

    # ── 월말 driver 패널 ──
    rsm = rs.resample("ME").last()
    semi_ppi_yoy = (rsm["semi_ppi"] / rsm["semi_ppi"].shift(12) - 1)
    usdkrw_yoy = (rsm["usdkrw"] / rsm["usdkrw"].shift(12) - 1)
    d_usdkrw = rsm["usdkrw"].pct_change()
    flow = rsm["foreign_net_kospi"]  # 외국인 순매수 (월 누계 근사)
    cli_chg = rsm["cli_kr"].diff()

    # 가격 momentum
    mom_12_1 = pxm[SERVICE].mean(axis=1).pct_change(12) - pxm[SERVICE].mean(axis=1).pct_change(1)
    mom_6 = pxm[SERVICE].mean(axis=1).pct_change(6)

    # KR rate (배당 duration)
    kr10 = cyc["kr_rate10y"]
    d_kr10 = cyc["d_kr_rate10y"]
    curve = cyc["kr_curve_10y3m"]

    # ★8+ 후보 (theory-tagged 부호 사전확약)
    drivers = {
        # defensive counter-cyclical (경기↑→통신 UW)
        "semi_ppi_yoy":  (semi_ppi_yoy, "음(-)", "defensive counter-cyclical: 반도체/경기 cycle↑→자금 cyclical 이탈→통신 UW"),
        "cli_chg":       (cli_chg, "음(-)", "경기선행 개선→통신(defensive) UW (semi_ppi와 동형 risk-on)"),
        # 배당 duration (금리)
        "kr_rate10y":    (kr10.diff(), "음(-)", "배당 duration: 금리↑→bond-proxy 디레이팅→통신 UW"),
        "d_kr_rate10y":  (d_kr10, "음(-)", "금리 Δ↑→통신 UW (duration)"),
        "kr_curve":      (curve.diff(), "음(-)", "커브 스티프닝(경기회복)→통신 UW"),
        # flow / fx
        "foreign_flow":  (flow, "음(-)", "외국인 순매수↑(risk-on)→통신(low-beta defensive) UW"),
        "usdkrw_yoy":    (usdkrw_yoy, "양(+)", "원화약세(risk-off)→방어주 통신 OW (방향 약 prior)"),
        "d_usdkrw":      (d_usdkrw, "양(+)", "원화약세 동시→통신 상대강세 (약)"),
        # dividend-carry momentum
        "mom_12_1":      (mom_12_1, "양(+)", "dividend-carry persistence: 고배당 defensive carry 누적→momentum (★검증 필요)"),
        "mom_6":         (mom_6, "양(+)", "6M momentum (carry, 약)"),
    }

    results = {"meta": {
        "method": "통신 업종 rotation (sector OW/UW timing) — 종목선택 아님. service 3사 동일가중 패널.",
        "panel": SERVICE, "panel_note": "SKT/KT/LGU+ strict 화이트리스트",
        "theory_framework": "통신 = defensive 고배당 bond-proxy. (1) defensive counter-cyclical(semi_ppi/cli 음) (2) 배당 duration(금리 음) (3) dividend-carry momentum(양, 검증).",
        "horizons_months": HORIZONS, "t_breakeven": T_BREAKEVEN,
        "ref_1차": "_rotation/validation-rotation-v1.json telecom mom_12_1 y_60d +0.284 + semi_ppi_yoy -0.334",
    }, "panel_stats": {"n_months": int(sec_ret.loc['2019-01-01':].dropna().shape[0])}, "signals": {}}

    pvals_fdr = {}
    for hl, hm in HORIZONS.items():
        fwd = pxm[SERVICE].pct_change(hm).mean(axis=1).shift(-hm).loc["2019-01-01":]
        results["signals"][hl] = {}
        for dname, (dser, prior, theory) in drivers.items():
            x = dser.loc["2019-01-01":]
            st = corr_stat(x, fwd, hm, f"{dname}__{hl}")
            st["prior_sign"] = prior
            st["theory"] = theory
            if not st.get("status", "").startswith("INSUFF"):
                st["walk_forward_oos"] = walk_forward(x, fwd)
            results["signals"][hl][dname] = st
            if st.get("status") == "powered" and st.get("wild_cluster_p") is not None:
                pvals_fdr[f"{dname}__{hl}"] = st["wild_cluster_p"]

    results["fdr_single_family"] = benjamini_yekutieli(pvals_fdr)

    # ════════ ★mom_12_1 theory 검증 = residualize on {semi_ppi, flow, rate} ════════
    # mom이 공통인자(defensive counter-cyclical/flow/rate) 재포장인가 독립 carry인가
    fwd60 = pxm[SERVICE].pct_change(3).mean(axis=1).shift(-3).loc["2019-01-01":]
    theory_drivers = pd.DataFrame({
        "semi_ppi": semi_ppi_yoy, "flow": flow, "rate": d_kr10,
    }).loc["2019-01-01":]
    mom_df = pd.DataFrame({"mom": mom_12_1.loc["2019-01-01":]}).join(theory_drivers, how="inner").dropna()
    # residualize mom on theory drivers
    import numpy.linalg as la
    Xt = np.column_stack([np.ones(len(mom_df))] + [mom_df[c].values for c in ["semi_ppi", "flow", "rate"]])
    yv = mom_df["mom"].values
    beta, *_ = la.lstsq(Xt, yv, rcond=None)
    mom_resid = pd.Series(yv - Xt @ beta, index=mom_df.index)
    raw_mom_stat = corr_stat(mom_df["mom"], fwd60, 3, "mom_raw")
    resid_mom_stat = corr_stat(mom_resid, fwd60, 3, "mom_resid_on_theory")
    # variance explained by theory drivers
    r2 = 1 - np.var(yv - Xt @ beta) / np.var(yv) if np.var(yv) > 0 else 0
    raw_rho = raw_mom_stat.get("spearman_rho", 0)
    res_rho = resid_mom_stat.get("spearman_rho", 0)
    shrink = round((1 - abs(res_rho) / abs(raw_rho)) * 100, 1) if abs(raw_rho) > 1e-9 else None
    results["mom_theory_verification"] = {
        "question": "mom_12_1 +0.284 = dividend-carry 독립신호 vs 공통인자(semi_ppi/flow/rate) 재포장?",
        "mom_var_explained_by_theory_drivers_r2": round(float(r2), 3),
        "raw_mom_60d_rho": raw_rho, "resid_mom_60d_rho": res_rho, "shrink_pct": shrink,
        "raw_mom_oos": raw_mom_stat.get("walk_forward_oos") or walk_forward(mom_df["mom"], fwd60),
        "resid_mom_oos": walk_forward(mom_resid, fwd60),
        "verdict": None,  # 아래 print에서 판정
    }

    out = ROOT / "validation-rotation-telecom-v1.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Saved {out}\n")
    print_summary(results)
    return results


def print_summary(r):
    print("=" * 80)
    print("통신 업종 rotation (sector OW/UW) — theory-tagged 후보")
    print(f"panel = SKT/KT/LGU+ 동일가중, n_months={r['panel_stats']['n_months']}")
    print("=" * 80)
    for hl in ["y_20d", "y_60d"]:
        print(f"\n--- {hl} ---")
        for dname, st in r["signals"][hl].items():
            if st.get("status", "").startswith("INSUFF"):
                continue
            oos = st.get("walk_forward_oos", {})
            wp = st.get("well_powered")
            mark = "★" if (st.get("wild_cluster_p", 1) < 0.05 and oos.get("eligible")) else " "
            print(f" {mark}{dname:14s} rho={st.get('spearman_rho'):+.3f} wc_p={st.get('wild_cluster_p')} "
                  f"t_pow={st.get('t_power_mde')}{'(well)' if wp else ''} "
                  f"OOS({oos.get('rho_is')},{oos.get('rho_oos')},{oos.get('verdict','')}) [{st.get('prior_sign')}]")
    print(f"\n★FDR single family: {r['fdr_single_family']}")
    mv = r["mom_theory_verification"]
    print(f"\n★mom_12_1 theory 검증:")
    print(f"  공통인자(semi_ppi/flow/rate) 설명 R²={mv['mom_var_explained_by_theory_drivers_r2']}")
    print(f"  raw mom rho={mv['raw_mom_60d_rho']} → resid(theory 제거) rho={mv['resid_mom_60d_rho']} (shrink {mv['shrink_pct']}%)")
    print(f"  raw OOS={mv['raw_mom_oos'].get('verdict')} / resid OOS={mv['resid_mom_oos'].get('verdict')}")


if __name__ == "__main__":
    main()
