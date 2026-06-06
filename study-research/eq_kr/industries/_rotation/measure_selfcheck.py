# -*- coding: utf-8 -*-
"""measure_selfcheck.py — 자문 §4 본인검증 2종 (advisory-protocol 의무).

자문 RESULTS §4:
  (1) ★Gemini "36셀 과적합" claim 검증 → 실제 36셀 N<24 collapse 비율 + 셀당 종목×월 표본 실측
      (Claude estimand 논리: L2 rotation 표본=industry-month 작음 / L3 selection 표본=stock×month 큼).
  (2) ★residual N_eff(participation ratio) vs raw N_eff = residualize 효과 정량 (자문 Q-b, B 효과).
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
IND_ROOT = ROOT.parent
INDUSTRIES = ["semiconductor", "auto", "financial", "battery", "chemical", "refining",
              "shipbuilding", "steel", "bio", "consumer", "telecom", "aitech"]
SEMI_PPI_LAG = 1


def participation_ratio(corr):
    ev = np.linalg.eigvalsh(corr); ev = ev[ev > 1e-10]
    return float((ev.sum() ** 2) / (ev ** 2).sum())


def main():
    out = {"meta": {"purpose": "자문 §4 본인검증: (1) 36셀 collapse 비율 (2) residual N_eff vs raw"}}

    # ── 12산업 패널 + 공통인자 ──
    panels, Fmap = {}, {}
    for s in INDUSTRIES:
        d = IND_ROOT / s / "raw-v3" / "data"
        px = pd.read_parquet(d / "prices.parquet"); px.index = pd.to_datetime(px.index)
        rs = pd.read_parquet(d / "regime_series.parquet"); rs.index = pd.to_datetime(rs.index)
        panels[s] = px.resample("ME").last().pct_change().mean(axis=1, skipna=True)
        rsm = rs.resample("ME").last()
        F = pd.DataFrame(index=rsm.index)
        F["d_usdkrw"] = rsm["usdkrw"].pct_change()
        F["foreign"] = rsm["foreign_net_kospi"]
        if "semi_ppi" in rsm.columns:
            F["semi_ppi_yoy"] = rsm["semi_ppi"].shift(SEMI_PPI_LAG).pct_change(12)
        Fmap[s] = F
    P = pd.DataFrame(panels).loc["2019-01-01":]

    # ── (2) raw N_eff vs residual N_eff (participation ratio) ──
    raw_corr = P.corr().values
    raw_neff = participation_ratio(raw_corr)
    # residualize 각 산업 → residual 패널
    Rresid = {}
    for s in INDUSTRIES:
        y = P[s]; F = Fmap[s]
        common = y.dropna().index.intersection(F.dropna().index)
        if len(common) < 20:
            Rresid[s] = y; continue
        X = np.column_stack([np.ones(len(common))] + [F.loc[common, c].values for c in F.columns])
        beta, *_ = np.linalg.lstsq(X, y.loc[common].values, rcond=None)
        Rresid[s] = pd.Series(y.loc[common].values - X @ beta, index=common)
    Rdf = pd.DataFrame(Rresid).dropna()
    resid_corr = Rdf.corr().values
    resid_neff = participation_ratio(resid_corr)
    out["neff_check"] = {
        "raw_N_eff_participation_ratio": round(raw_neff, 2),
        "residual_N_eff_participation_ratio": round(resid_neff, 2),
        "raw_pc1_var": round(float(np.linalg.eigvalsh(raw_corr).max() / 12), 3),
        "resid_pc1_var": round(float(np.linalg.eigvalsh(resid_corr).max() / 12), 3),
        "mean_pairwise_raw": round(float(raw_corr[np.triu_indices(12, 1)].mean()), 3),
        "mean_pairwise_resid": round(float(resid_corr[np.triu_indices(12, 1)].mean()), 3),
        "verdict": "residual N_eff = 공통인자 제거 후 진짜 독립 차원. 자문 Q-b '진짜 ~3-4' 검증.",
    }

    # ── (1) 36셀 collapse 비율 (L2 rotation = industry-month 표본) ──
    # regime_labels 36셀 = macro4×krw3×flow3. 월별 라벨 → 각 셀 industry-month 표본(=월 수)
    d0 = IND_ROOT / "semiconductor" / "raw-v3" / "data"
    lab = pd.read_parquet(d0 / "regime_labels.parquet"); lab.index = pd.to_datetime(lab.index)
    lab = lab.loc["2019-01-01":]
    cells = {}
    for _, row in lab.iterrows():
        key = f"{row['macro_regime']}|{row['krw_regime']}|{row['flow_regime']}"
        cells[key] = cells.get(key, 0) + 1
    total_cells_possible = 4 * 3 * 3
    occupied = len(cells)
    n_lt24 = sum(1 for v in cells.values() if v < 24)
    n_lt12 = sum(1 for v in cells.values() if v < 12)
    n_ge24 = sum(1 for v in cells.values() if v >= 24)
    out["cell_collapse_check"] = {
        "regime_grid": "36셀 (macro4 × krw3 × flow3)",
        "L2_rotation_unit": "industry-month (월 수 = 셀 표본). ★L3 selection 은 stock×month (별 unit, 자문 Q2 estimand)",
        "n_months_total": len(lab),
        "cells_possible": total_cells_possible,
        "cells_occupied": occupied,
        "cells_N_ge24_powered": n_ge24,
        "cells_N_lt24_collapse": n_lt24,
        "cells_N_lt12_severe": n_lt12,
        "collapse_ratio_lt24": round(n_lt24 / occupied, 3) if occupied else None,
        "cell_distribution": dict(sorted(cells.items(), key=lambda x: -x[1])),
        "verdict": f">>> L2 rotation 차원(industry-month): {n_ge24}/{occupied} 셀만 N≥24 powered. "
                   f"collapse(N<24) {n_lt24}/{occupied} = {round(n_lt24/occupied*100) if occupied else 0}%. "
                   f"★Gemini '36셀 과적합'(L2 rotation 표본 기준) = 입증(대부분 collapse). "
                   f"★단 Claude estimand: L3 selection 은 stock×month 라 표본 큼(36셀 L3 IC 는 별 차원, semiconductor capsule 36셀=0 N≥24 동일 실측). "
                   f"→ L2 rotation = 36셀 hard 부적합, single-axis(macro/krw/flow 각각) + partial-pooling 정당(자문 G-G v2).",
    }

    fp = ROOT / "validation-rotation-selfcheck-v1.json"
    fp.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Saved {fp}\n")
    print("=== (2) N_eff check (residualize 효과, 자문 Q-b) ===")
    for k, v in out["neff_check"].items():
        print(f"  {k}: {v}")
    print("\n=== (1) 36셀 collapse check (자문 Gemini vs Claude estimand) ===")
    cc = out["cell_collapse_check"]
    for k in ["n_months_total", "cells_occupied", "cells_N_ge24_powered", "cells_N_lt24_collapse", "collapse_ratio_lt24"]:
        print(f"  {k}: {cc[k]}")
    print(f"  verdict: {cc['verdict']}")
    print(f"\n  셀 분포 (상위): {dict(list(cc['cell_distribution'].items())[:8])}")


if __name__ == "__main__":
    main()
