# -*- coding: utf-8 -*-
"""measure_rotation_refining.py — 정유 rotation 신호 이론 검증 + 심화 (team-lead 지시).

★rotation-analyst v2 발견: gasoline_crack_d3 → 정유섹터 forward 양(+0.241 y_60d, OOS+0.39).
★team-lead 지시 = 정유 전문성으로 (1) crack_d3 이론 검증(PEAD/펀더멘털 모멘텀) (2) 제품별 크랙 심화
  (가솔린/디젤/항공유 — ★이론: 디젤이 한국 정유 핵심, 수출 ~40%) (3) 싱가포르 GRM proxy.

★이론 (theory-notes §M1 + Gemini 리서치 2026-06-05):
  crack LEVEL = 즉시 반영(효율적) / crack 변화율(d3 모멘텀) = 애널리스트 실적추정 상향 사이클로
  점진 반영(PEAD, Bernard-Thomas 1989/1990, Chan-Jegadeesh-Lakonishok 1996 earnings momentum).
  → crack_d3 (+) forward = fundamental momentum (data mining 아님, 이론 정당).
  crack_d3(+) vs rel_mom(-) = fundamental momentum vs price reversal 분리(Jegadeesh 1990).

★측정 = rotation-analyst measure_rotation_v2 미러 + 제품별 크랙 분해(디젤 우위 가설 검증).
  signal = product_crack.pct_change(3) [d3 모멘텀] → 정유섹터 cum return forward y_20d/y_60d.
  G-G v2: walk-forward OOS(2023 split) + wild-cluster + eff-N + 단일 FDR.
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
HORIZONS_M = {"y_20d": 1, "y_60d": 3}
OOS_SPLIT = "2023-01-01"
T_BREAKEVEN = 2.802


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


def signal_forward_stat(sig, fwd, h_months, label):
    common = sig.dropna().index.intersection(fwd.dropna().index)
    if len(common) < 12:
        return {"label": label, "n": len(common), "status": "INSUFFICIENT(n<12)"}
    sv, fv = sig.loc[common].values, fwd.loc[common].values
    rho, _ = stats.spearmanr(sv, fv)
    sr = stats.rankdata(sv) / len(sv) - 0.5; fr = stats.rankdata(fv) / len(fv) - 0.5
    prod = sr * fr; n = len(prod); neff = n_eff_autocorr(prod)
    wc_p = wild_cluster_p(prod); ci = block_boot_ci(prod, max(2, h_months))
    t_power = abs(rho) * np.sqrt(max(neff, 1.0))
    powered = (n >= 24) and (neff >= 6) and (t_power >= T_BREAKEVEN)
    is_idx = [d for d in common if str(d) < OOS_SPLIT]; oos_idx = [d for d in common if str(d) >= OOS_SPLIT]
    oos = {"is_n": len(is_idx), "oos_n": len(oos_idx)}
    if len(is_idx) >= 8 and len(oos_idx) >= 8:
        rho_is = stats.spearmanr(sig.loc[is_idx].values, fwd.loc[is_idx].values)[0]
        rho_oos = stats.spearmanr(sig.loc[oos_idx].values, fwd.loc[oos_idx].values)[0]
        sign_hold = (np.sign(rho_is) == np.sign(rho_oos)) and abs(rho_oos) >= 0.5 * abs(rho_is)
        oos.update({"rho_is": round(float(rho_is), 4), "rho_oos": round(float(rho_oos), 4),
                    "eligible": bool(sign_hold and abs(rho_oos) > 0.02),
                    "verdict": ("OOS 부호+mag 유지" if sign_hold else
                                ("OOS 부호유지 mag약" if np.sign(rho_is) == np.sign(rho_oos) else "OOS flip"))})
    else:
        oos["eligible"] = None; oos["verdict"] = "OOS n<8"
    return {"label": label, "n": n, "n_eff": round(neff, 1), "spearman_rho": round(float(rho), 4),
            "t_power_mde": round(float(t_power), 2),
            "wild_cluster_p": round(wc_p, 4) if not np.isnan(wc_p) else None,
            "ci95_block_boot_prod": [round(c, 5) for c in ci] if not np.isnan(ci[0]) else None,
            "walk_forward_oos": oos, "status": "powered" if powered else ("underpowered" if n >= 12 else "INSUFFICIENT")}


def main():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    cyc = pd.read_parquet(DATA / "refining_cycle.parquet"); cyc.index = pd.to_datetime(cyc.index)
    lab = pd.read_parquet(DATA / "regime_labels.parquet"); lab.index = pd.to_datetime(lab.index)
    uni = pd.read_parquet(DATA / "universe.parquet")
    strict2 = [c for c in uni[uni["is_refining_core"] & uni["pass_floor_strict"]]["Code"] if c in px.columns]

    # 정유섹터 cumulative return (rotation-analyst 동일: 패널 월수익 → cum)
    pret = px[strict2].resample("ME").last().pct_change().mean(axis=1).loc["2019-01-01":]
    cum = (1 + pret.fillna(0)).cumprod()
    cycm = cyc.resample("ME").last()

    # ★제품별 크랙 (이론: 디젤 우위 가설 검증) + 종합/유가/가동률
    cycle_signals = {
        "gasoline_crack": cycm["gasoline_crack"],   # 가솔린 크랙 (드라이빙시즌)
        "diesel_crack": cycm["diesel_crack"],       # ★디젤 크랙 (한국 정유 핵심, 수출 40%)
        "blended_crack": cycm["blended_crack"],     # 3-2-1 종합
        "brent": cycm["brent"],                     # 유가
        "refinery_ip": cycm["refinery_ip"],         # 가동률 proxy
    }

    out = {"meta": {
        "purpose": "정유 rotation 신호 이론 검증 + 제품별 크랙 심화 (team-lead 지시)",
        "panel": strict2, "horizons_months": HORIZONS_M, "oos_split": OOS_SPLIT, "t_breakeven": T_BREAKEVEN,
        "theory": "crack_d3(3M 모멘텀) = PEAD/펀더멘털 모멘텀(Bernard-Thomas 1989/1990, Chan-Jegadeesh-Lakonishok 1996). crack level=즉시반영(효율적), 변화율=애널리스트 실적추정 상향 점진반영.",
        "product_hypothesis": "★디젤 크랙 우위(한국 정유 수출 ~40% 경유) > 가솔린(드라이빙시즌) > 종합. Fesharaki-Wu 2018 싱가포르 GRM(US Gulf=proxy 한계).",
        "signal_transform": "crack.pct_change(3)=d3 모멘텀 + .pct_change(12)=yoy + level (비교). rotation-analyst measure_rotation_v2 미러.",
    }, "product_crack_comparison": {}, "all_signals": {}, "regime_conditional": {}}
    fdr = {}

    # ── 제품별 크랙 d3 비교 (디젤 우위 가설) ──
    for cname, base in cycle_signals.items():
        out["all_signals"][cname] = {}
        for tname, transform in [("d3", base.pct_change(3)), ("yoy", base.pct_change(12)), ("level", base)]:
            sig = transform.loc["2019-01-01":]
            for hl, hm in HORIZONS_M.items():
                fwd = cum.pct_change(hm).shift(-hm)
                st = signal_forward_stat(sig, fwd, hm, f"refining__{cname}_{tname}__{hl}")
                out["all_signals"][cname][f"{tname}__{hl}"] = st
                if st.get("status") in ("powered", "underpowered") and st.get("wild_cluster_p") is not None:
                    fdr[f"{cname}_{tname}__{hl}"] = st["wild_cluster_p"]

    # ── 제품별 크랙 d3 우위 비교표 (이론 검증: 디젤 > 가솔린?) ──
    for cname in ["gasoline_crack", "diesel_crack", "blended_crack"]:
        d3_60 = out["all_signals"][cname].get("d3__y_60d", {})
        d3_20 = out["all_signals"][cname].get("d3__y_20d", {})
        out["product_crack_comparison"][cname] = {
            "d3_y20d_rho": d3_20.get("spearman_rho"), "d3_y20d_wc_p": d3_20.get("wild_cluster_p"),
            "d3_y60d_rho": d3_60.get("spearman_rho"), "d3_y60d_wc_p": d3_60.get("wild_cluster_p"),
            "d3_y60d_oos": d3_60.get("walk_forward_oos", {}).get("verdict"),
            "d3_y60d_oos_rho": [d3_60.get("walk_forward_oos", {}).get("rho_is"), d3_60.get("walk_forward_oos", {}).get("rho_oos")]}

    # ── regime conditional (디젤 크랙 d3 × regime, OW/UW 국면) ──
    lab19 = lab.loc["2019-01-01":]
    diesel_d3 = cycle_signals["diesel_crack"].pct_change(3).loc["2019-01-01":]
    fwd60 = cum.pct_change(3).shift(-3)
    for axis in ["macro_regime", "krw_regime", "flow_regime"]:
        la = lab19[axis].dropna()
        for rg in sorted(la.unique()):
            months = la[la == rg].index
            xs = diesel_d3[diesel_d3.index.isin(months)]
            ys = fwd60[fwd60.index.isin(months)]
            st = signal_forward_stat(xs, ys, 3, f"diesel_crack_d3_y60__{axis}={rg}")
            out["regime_conditional"][f"{axis}={rg}"] = st
            if st.get("status") in ("powered", "underpowered") and st.get("wild_cluster_p") is not None:
                fdr[f"diesel_regime__{axis}={rg}"] = st["wild_cluster_p"]

    # ── 단일 FDR (BY) ──
    items = [(k, v) for k, v in fdr.items() if v is not None]
    m = len(items)
    if m:
        items.sort(key=lambda x: x[1]); c_m = sum(1.0 / i for i in range(1, m + 1)); surv = []
        for ri, (k, p) in enumerate(items, 1):
            if p <= (ri / m) * 0.10 / c_m: surv = [items[j][0] for j in range(ri)]
        out["fdr_family"] = {"m": m, "by_factor": round(c_m, 3), "survivors_BY": surv,
                             "raw_p_min": round(items[0][1], 5), "raw_p_min_key": items[0][0]}
    else:
        out["fdr_family"] = {"m": 0}

    (ROOT / "validation-rotation-refining-v3.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print("=== 제품별 크랙 d3 모멘텀 비교 (이론: 디젤 우위?) ===")
    for cname, d in out["product_crack_comparison"].items():
        print(f"  {cname:16s} d3_y20d={d['d3_y20d_rho']:+.3f}(wc{d['d3_y20d_wc_p']}) d3_y60d={d['d3_y60d_rho']:+.3f}(wc{d['d3_y60d_wc_p']}) OOS{d['d3_y60d_oos_rho']} {d['d3_y60d_oos']}")
    print("\n=== 전 신호 (d3 모멘텀 위주, wc_p<0.10) ===")
    for cname, sd in out["all_signals"].items():
        for k, st in sd.items():
            wcp = st.get("wild_cluster_p")
            if wcp is not None and wcp < 0.10:
                oos = st.get("walk_forward_oos", {})
                print(f"  ★{cname}_{k:14s} rho={st['spearman_rho']:+.3f} wc_p={wcp} t_pow={st['t_power_mde']} OOS{oos.get('rho_is')}->{oos.get('rho_oos')} elig={oos.get('eligible')} {st['status']}")
    print("\n=== regime conditional (디젤 크랙 d3 y_60d, OW/UW 국면) ===")
    for k, st in out["regime_conditional"].items():
        if st.get("status") in ("powered", "underpowered"):
            star = "★" if st["status"] == "powered" else " "
            print(f"  {star}{k:34s} rho={st['spearman_rho']:+.3f} wc_p={st.get('wild_cluster_p')} n={st['n']}")
    print(f"\nFDR family: {out['fdr_family']}")
    print("\nSaved validation-rotation-refining-v3.json")


if __name__ == "__main__":
    main()
