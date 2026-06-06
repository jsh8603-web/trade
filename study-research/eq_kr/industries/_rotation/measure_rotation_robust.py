# -*- coding: utf-8 -*-
"""measure_rotation_robust.py — rotation 후보 신호 robustness (S4 재검증 + S5 역공격).

measure_rotation.py 의 OOS-eligible 후보에 대해:
  (1) leave-one-year-out: 특정 연도 episode 종속성 (S5 역공격)
  (2) placebo: 무작위 shuffle 신호 → forward corr 분포 (우연 발생 확률)
  (3) 60d overlap 정직 보정: 비중첩(non-overlapping) sub-sample IC 비교 (eff_N 과대 점검)
  (4) cross-industry N_eff: 공통 macro 지배도 (가짜 breadth 차단, G-G v2)

★rotation 본체 = 산업 고유 신호(rel_mom/산업 momentum) — macro 공통(cli_chg)은 12산업 1베팅이라
  rotation 이 아니라 시장 timing. 본 robustness 는 산업 고유 신호 우선.
"""
from __future__ import annotations
import sys, io, json, os
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
IND_ROOT = ROOT.parent
INDUSTRIES = ["semiconductor", "auto", "financial", "battery", "chemical", "refining",
              "shipbuilding", "steel", "bio", "consumer", "telecom", "aitech"]

# measure_rotation.py 와 동일 신호 구성 재사용.
# ★mr 가 module-level 에서 sys.stdout 을 새 TextIOWrapper 로 교체(원 stdout buffer 소유) → import 후
#   우리도 fresh wrapper 를 os.dup(1) 새 fd 로 열어 print 가능하게 복구.
import importlib.util
spec = importlib.util.spec_from_file_location("mr", ROOT / "measure_rotation.py")
mr = importlib.util.module_from_spec(spec); spec.loader.exec_module(mr)
try:
    sys.stdout = io.TextIOWrapper(os.fdopen(os.dup(1), "wb"), encoding="utf-8")
except Exception:
    pass


def spearman_rho(sig, fwd):
    common = sig.dropna().index.intersection(fwd.dropna().index)
    if len(common) < 8:
        return np.nan, len(common)
    return float(stats.spearmanr(sig.loc[common].values, fwd.loc[common].values)[0]), len(common)


def leave_one_year(sig, fwd, years):
    """연도별 1개씩 제외 → rho 안정성 (episode 종속)."""
    out = {}
    common = sig.dropna().index.intersection(fwd.dropna().index)
    for y in years:
        keep = [d for d in common if d.year != y]
        if len(keep) >= 12:
            rho = float(stats.spearmanr(sig.loc[keep].values, fwd.loc[keep].values)[0])
            out[str(y)] = round(rho, 3)
    return out


def placebo(sig, fwd, B=2000, seed=7):
    """신호 시계열 무작위 shuffle → forward corr 분포. 실측 |rho| 우연 초과 비율."""
    common = sig.dropna().index.intersection(fwd.dropna().index)
    if len(common) < 12:
        return None
    sv, fv = sig.loc[common].values, fwd.loc[common].values
    rho_obs = abs(stats.spearmanr(sv, fv)[0])
    rng = np.random.default_rng(seed); cnt = 0
    for _ in range(B):
        rho_p = abs(stats.spearmanr(rng.permutation(sv), fv)[0])
        if rho_p >= rho_obs:
            cnt += 1
    return round((cnt + 1) / (B + 1), 4)


def nonoverlap_ic(sig, fwd_index_px_cum, hm, sig_full):
    """60d forward overlap 정직 보정 — h개월 간격 non-overlapping sub-sample IC.
    overlapping 은 인접 obs 강상관 → t 과대. h개월 stride 로 독립 sub-sample 만 사용."""
    common = sig.dropna().index.intersection(fwd_index_px_cum.dropna().index)
    common = sorted(common)
    if len(common) < hm * 3:
        return None
    sub = common[::hm]  # h개월 stride (non-overlapping)
    if len(sub) < 8:
        return None
    rho = float(stats.spearmanr(sig.loc[sub].values, fwd_index_px_cum.loc[sub].values)[0])
    return {"rho_nonoverlap": round(rho, 3), "n_nonoverlap": len(sub)}


# ── 후보 신호 (measure_rotation OOS-eligible 강 후보, 산업 고유 우선) ──
CANDIDATES = [
    ("refining", "rel_mom_6", 3),     # 상대모멘텀 reversal (약신호 산업 활로)
    ("refining", "rel_mom_3", 3),
    ("consumer", "rel_mom_6", 3),     # 내수 상대모멘텀 reversal
    ("chemical", "mom_3", 3),         # 산업 자체 momentum
    ("chemical", "mom_6", 3),
    ("battery", "mom_3", 3),
    ("auto", "mom_3", 3),
    ("telecom", "mom_12_1", 3),
    ("steel", "mom_3", 3),
    ("financial", "cli_chg", 3),      # macro 공통 (대조: 시장 timing)
    ("semiconductor", "mom_3", 3),
    ("consumer", "mom_6", 3),
    ("telecom", "foreign_flow", 3),   # 외국인 flow rotation
    ("steel", "foreign_flow", 3),
    ("telecom", "semi_ppi_yoy", 3),   # 반도체 cycle 약 → IT/통신 방어 rotation
    ("aitech", "semi_ppi_yoy", 3),
]


def main():
    # 12산업 패널 (cross-industry relative 위해)
    all_panels = {}
    cache = {}
    for s in INDUSTRIES:
        px, lab, rs, dart = mr.load_industry(s)
        cache[s] = (px, lab, rs)
        all_panels[s] = mr.panel_monthly_return(px)
    all_panels = pd.DataFrame(all_panels)

    out = {"meta": {"purpose": "rotation 후보 robustness (LOY + placebo + non-overlap + N_eff)",
                    "rotation_본체": "산업 고유 신호(rel_mom/산업 momentum). macro 공통(cli_chg/foreign_flow)=시장 timing 대조"},
           "cross_industry": {}, "candidates": {}}

    # cross-industry N_eff (가짜 breadth)
    P = all_panels.loc["2019-01-01":]
    c = P.corr(); ev = np.linalg.eigvalsh(c.values); ev = ev[ev > 0]; p = ev / ev.sum()
    out["cross_industry"] = {
        "mean_pairwise_corr": round(float(c.values[np.triu_indices(12, 1)].mean()), 3),
        "N_eff_eigen_entropy": round(float(np.exp(-(p * np.log(p)).sum())), 2),
        "pc1_var_ratio": round(float(p.max()), 3),
        "note": "PC1 지배 = 외국인flow/USDKRW 공통인자. macro 신호는 12산업 거의 동일 = rotation 아닌 시장 timing."}

    years = list(range(2019, 2027))
    for s, signame, hm in CANDIDATES:
        px, lab, rs = cache[s]
        pret, sigs = mr.build_signals(px, rs, all_panels, s)
        if signame not in sigs:
            continue
        sig = sigs[signame]
        cum = (1 + pret.fillna(0)).cumprod()
        fwd = cum.pct_change(hm).shift(-hm)
        rho, n = spearman_rho(sig, fwd)
        loy = leave_one_year(sig, fwd, years)
        loy_vals = list(loy.values())
        plac = placebo(sig, fwd)
        nov = nonoverlap_ic(sig, fwd, hm, sig)
        macro = signame in ("cli_chg", "usdkrw_yoy", "d_usdkrw", "foreign_flow", "semi_ppi_yoy")
        # LOY 안정성: 부호 일관 + min/max 범위
        sign_consistent = all(np.sign(v) == np.sign(rho) for v in loy_vals) if loy_vals else None
        out["candidates"][f"{s}__{signame}"] = {
            "type": "MACRO공통(시장timing)" if macro else "산업고유(rotation)",
            "horizon_m": hm, "rho_full": round(rho, 3), "n": n,
            "leave_one_year": loy,
            "loy_sign_consistent": sign_consistent,
            "loy_range": [round(min(loy_vals), 3), round(max(loy_vals), 3)] if loy_vals else None,
            "placebo_p": plac,
            "nonoverlap": nov,
        }

    fp = ROOT / "validation-rotation-robust-v1.json"
    fp.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Saved {fp}\n")
    print(f"=== cross-industry: {json.dumps(out['cross_industry'], ensure_ascii=False)}\n")
    print(f"{'산업/신호':28s} {'type':18s} rho_full  placebo  LOY일관 LOY범위        non-overlap")
    print("-" * 110)
    for k, v in out["candidates"].items():
        nov = v["nonoverlap"]
        novs = f"{nov['rho_nonoverlap']:+.3f}(n={nov['n_nonoverlap']})" if nov else "NA"
        lr = v["loy_range"]
        print(f"{k:28s} {v['type']:18s} {v['rho_full']:+.3f}    {v['placebo_p']}   "
              f"{str(v['loy_sign_consistent']):5s}  {str(lr):16s} {novs}")


if __name__ == "__main__":
    main()
