# -*- coding: utf-8 -*-
"""measure_rotation_composite.py — bio rotation composite overlay + 강건성 (tradeable 판정).

measure_rotation.py 1차 = 후보 10개 단변량(전부 underpowered, BY 미생존). 본 스크립트:
  (1) ★composite overlay = 이론 부호 정렬 신호 z-score 평균 → bio 업종 forward IC (power 보강)
      - rate_overlay = -(us_10y_d z) (금리 음 → 부호 뒤집어 양으로 정렬)
      - bio_global_overlay = +(xbi_rel_mom z + ibb_rel_mom z)/2 (글로벌바이오 양)
      - full_overlay = rate_overlay + bio_global_overlay (이론 정렬 합성)
  (2) ★leave-episode: us_10y_d y_60d 의 2022(금리쇼크) 제외 후 생존
  (3) ★tradeable 판정 (G-G v2 2축: eligibility OOS 부호유지 / conviction)

★좀비 마스킹 적용 (mask_trading_halt). ★이론 부호 사전확약(measure_rotation.py 헤더 동결).
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
HORIZONS_D = {"y_20d": 20, "y_60d": 60}
OOS_SPLIT = "2023-01-01"
T_BREAKEVEN = 2.802

# measure_rotation.py 재사용 (import 시 measure_rotation 가 stdout 래핑 → 중복 래핑 금지)
sys.path.insert(0, str(ROOT))
from measure_rotation import (mask_trading_halt, nw_se, n_eff_autocorr, wild_cluster_p,
                              block_boot_ci, build_bio_index, load_data, build_macro_signals)


def zscore(s):
    return (s - s.rolling(36, min_periods=12).mean()) / s.rolling(36, min_periods=12).std()


def ic_stat(sig, fwd, h_months, label, drop_years=None):
    s = sig.dropna()
    if drop_years:
        s = s[~s.index.year.isin(drop_years)]
    common = s.index.intersection(fwd.dropna().index)
    if len(common) < 12:
        return {"label": label, "n": len(common), "status": "INSUFFICIENT"}
    sv, fv = s.loc[common].values, fwd.loc[common].values
    rho, _ = stats.spearmanr(sv, fv)
    sr = stats.rankdata(sv) / len(sv) - 0.5; fr = stats.rankdata(fv) / len(fv) - 0.5
    prod = sr * fr
    neff = n_eff_autocorr(prod); se = nw_se(prod, h_months)
    t_nw = prod.mean() / se if se and se > 0 else np.nan
    wc_p = wild_cluster_p(prod); ci = block_boot_ci(prod, max(2, h_months))
    t_power = abs(rho) * np.sqrt(max(neff, 1.0))
    is_idx = [d for d in common if str(d) < OOS_SPLIT]; oos_idx = [d for d in common if str(d) >= OOS_SPLIT]
    oos = {"is_n": len(is_idx), "oos_n": len(oos_idx)}
    if len(is_idx) >= 8 and len(oos_idx) >= 8:
        rho_is = stats.spearmanr(s.loc[is_idx].values, fwd.loc[is_idx].values)[0]
        rho_oos = stats.spearmanr(s.loc[oos_idx].values, fwd.loc[oos_idx].values)[0]
        sign_hold = (np.sign(rho_is) == np.sign(rho_oos)) and abs(rho_oos) >= 0.5 * abs(rho_is)
        oos.update({"rho_is": round(float(rho_is), 4), "rho_oos": round(float(rho_oos), 4),
                    "eligible": bool(sign_hold and abs(rho_oos) > 0.02),
                    "verdict": ("OOS 부호+mag 유지" if sign_hold else
                                ("OOS 부호유지 mag약" if np.sign(rho_is) == np.sign(rho_oos) else "OOS flip"))})
    else:
        oos.update({"eligible": None, "verdict": "OOS n<8"})
    return {"label": label, "n": len(common), "n_eff": round(neff, 1), "spearman_rho": round(float(rho), 4),
            "t_nw": round(float(t_nw), 2) if not np.isnan(t_nw) else None, "t_power_mde": round(float(t_power), 2),
            "wild_cluster_p": round(wc_p, 4) if not np.isnan(wc_p) else None,
            "ci95_block_boot": [round(c, 5) for c in ci] if not np.isnan(ci[0]) else None,
            "walk_forward_oos": oos,
            "status": "powered" if (len(common) >= 24 and neff >= 6 and t_power >= T_BREAKEVEN)
                      else ("underpowered" if len(common) >= 12 else "INSUFFICIENT")}


def main():
    px, cf, rs, gb, kr, macro, fda = load_data()
    cum, _ = build_bio_index(px); cum = cum.loc["2019-01-01":]
    sigs = build_macro_signals(cf, rs, gb, kr, macro, fda, cum.index)
    raw = {k[0]: v for k, v in sigs.items()}   # name -> series

    # ── composite overlay (이론 부호 정렬 z-score) ──
    rate_overlay = -zscore(raw["us_10y_d"])                      # 금리 음 → +로 정렬
    xbi_z = zscore(raw["xbi_rel_mom"]); ibb_z = zscore(raw["ibb_rel_mom"])
    bio_global = (xbi_z + ibb_z) / 2                              # 글로벌바이오 양
    full_overlay = (rate_overlay + bio_global) / 2               # 이론 정렬 합성 (방향 = bio OW 클수록 양)
    rate_global = full_overlay  # alias

    composites = {
        "rate_overlay": rate_overlay,            # -(US 10Y Δ) = 금리 하락 → bio OW
        "bio_global_overlay": bio_global,        # XBI/IBB 상대모멘텀 평균
        "full_overlay": full_overlay,            # 금리 + 글로벌바이오 합성
    }
    # composite 부호 사전확약 = 전부 양(+): overlay 값 클수록 bio forward 높음
    results = {"meta": {
        "method": "bio rotation composite overlay (이론 부호 정렬 z-score 합성) + leave-episode 강건성",
        "composite_def": {
            "rate_overlay": "-(US 10Y Δ3M z) = 금리 하락 시 bio OW (growth duration)",
            "bio_global_overlay": "(XBI/SPY + IBB/NDX 상대모멘텀 z)/2 = 글로벌바이오 강세 → 한국bio OW",
            "full_overlay": "(rate_overlay + bio_global_overlay)/2 = 금리+글로벌바이오 합성",
        },
        "prior_sign_all": "+1 (overlay 값 클수록 bio forward 높음)",
        "horizons_days": HORIZONS_D, "oos_split": OOS_SPLIT,
    }, "composites": {}, "robustness": {}}

    for cname, cser in composites.items():
        results["composites"][cname] = {}
        for hl, hd in HORIZONS_D.items():
            hm = max(1, round(hd / 21))
            fwd = cum.pct_change(hm).shift(-hm)
            results["composites"][cname][hl] = ic_stat(cser, fwd, hm, f"bio_rot_comp__{cname}__{hl}")

    # ── 강건성: us_10y_d y_60d leave-2022(금리쇼크) ──
    fwd60 = cum.pct_change(3).shift(-3)
    results["robustness"]["us_10y_d_y60_full"] = ic_stat(raw["us_10y_d"], fwd60, 3, "us_10y_d_y60_full")
    results["robustness"]["us_10y_d_y60_drop2022"] = ic_stat(raw["us_10y_d"], fwd60, 3, "us_10y_d_y60_drop2022", drop_years={2022})
    # full_overlay y_60d leave-2022
    results["robustness"]["full_overlay_y60_drop2022"] = ic_stat(full_overlay, fwd60, 3, "full_overlay_y60_drop2022", drop_years={2022})

    out = ROOT / "validation-rotation-composite-v3.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Saved {out}\n")

    print("=" * 88)
    print("COMPOSITE OVERLAY (이론 부호 정렬, prior=+ 전부)")
    print("=" * 88)
    for cname, hd in results["composites"].items():
        for hl, st in hd.items():
            if "spearman_rho" not in st:
                print(f"  {cname:20s} {hl}: {st.get('status')}"); continue
            oos = st["walk_forward_oos"]
            oos_s = f"{oos.get('rho_is')}->{oos.get('rho_oos')}" if "rho_is" in oos else oos.get("verdict")
            el = "Y" if oos.get("eligible") else ("n" if oos.get("eligible") is False else "-")
            print(f"  {cname:20s} {hl}: rho={st['spearman_rho']:+.3f} wc_p={st['wild_cluster_p']} "
                  f"t_pow={st['t_power_mde']} OOS[{oos_s}] elig={el} {st['status']}")
    print("\n" + "=" * 88); print("강건성 (leave-2022 금리쇼크)"); print("=" * 88)
    for k, st in results["robustness"].items():
        if "spearman_rho" in st:
            oos = st["walk_forward_oos"]
            print(f"  {k:30s} rho={st['spearman_rho']:+.3f} wc_p={st['wild_cluster_p']} n={st['n']} "
                  f"OOS[{oos.get('rho_is')}->{oos.get('rho_oos')}] {st['status']}")
    return results


if __name__ == "__main__":
    main()
