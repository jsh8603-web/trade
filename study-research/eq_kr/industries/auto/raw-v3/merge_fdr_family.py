# -*- coding: utf-8 -*-
"""merge_fdr_family.py — ★단일 FDR family 통합 합산 (team-lead 순서3, garden-of-forking-paths).

가격/valuation conditional(validation-conditional-v3.json) + 신규지표(validation-fundamentals-cycle-v3.json)
powered cell p-value 를 ★하나의 BY-FDR family 로 합산 → 통합 m + survivors 재계산.
산업단계 = 각 family + 통합 m 박제. M_eff 통합보정은 supervisor.
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np

ROOT = Path(__file__).resolve().parent


def collect_pvals():
    pvals = {}
    # 1) conditional (가격+valuation) — powered cell wc_p
    cond = json.loads((ROOT / "validation-conditional-v3.json").read_text(encoding="utf-8"))
    for sname, hd in cond.get("conditional_ic_surface", {}).items():
        for hname, cells in hd.items():
            for ck, cv in cells.items():
                if cv.get("status") == "powered" and cv.get("wild_cluster_p") is not None:
                    pvals[f"COND::{sname}__{hname}__{ck}"] = cv["wild_cluster_p"]
    # 2) 신규 펀더멘털 cycle — fundamentals_pvals
    fpath = ROOT / "validation-fundamentals-cycle-v3.json"
    if fpath.exists():
        fund = json.loads(fpath.read_text(encoding="utf-8"))
        for k, v in fund.get("fundamentals_pvals", {}).items():
            pvals[f"FUND::{k}"] = v
    return pvals


def by_fdr(pvals, q=0.10):
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    m = len(items)
    if m == 0:
        return {"m": 0}
    items.sort(key=lambda x: x[1])
    c_m = sum(1.0 / i for i in range(1, m + 1))
    surv = []
    for ri, (k, p) in enumerate(items, 1):
        if p <= (ri / m) * q / c_m:
            surv = [items[j][0] for j in range(ri)]
    return {"m_total": m, "by_factor": round(c_m, 3), "q": q,
            "bonferroni_alpha": round(0.05 / m, 6),
            "survivors_BY": surv, "n_survivors": len(surv),
            "raw_p_min": round(items[0][1], 5), "raw_p_min_key": items[0][0],
            "top5": [(k, round(v, 5)) for k, v in items[:5]]}


def main():
    pvals = collect_pvals()
    n_cond = sum(1 for k in pvals if k.startswith("COND::"))
    n_fund = sum(1 for k in pvals if k.startswith("FUND::"))
    result = {
        "note": "★단일 FDR family 통합 합산 (가격/valuation conditional + 신규 펀더멘털 cycle). garden-of-forking-paths 차단.",
        "family_composition": {"conditional_powered": n_cond, "fundamentals_powered": n_fund, "total": len(pvals)},
        "merged_by_fdr": by_fdr(pvals),
        "m_eff_caveat": "naive m_total 박제. M_eff 통합보정(신호상관) = supervisor 통합단계(M.7).",
    }
    out = ROOT / "validation-merged-fdr-v3.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Saved {out}")
    print(f"\n통합 FDR family: m_total={result['merged_by_fdr'].get('m_total')} "
          f"(cond {n_cond} + fund {n_fund}) survivors={result['merged_by_fdr'].get('n_survivors')}")
    print(f"raw_p_min={result['merged_by_fdr'].get('raw_p_min')} ({result['merged_by_fdr'].get('raw_p_min_key')})")
    print("top5:", result['merged_by_fdr'].get('top5'))


if __name__ == "__main__":
    main()
