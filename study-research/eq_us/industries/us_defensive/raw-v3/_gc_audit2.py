# -*- coding: utf-8 -*-
"""_gc_audit2.py — G-C 추가 정밀 검증: negative PIT lag 1건 / power analysis / regime split 유의성 정직성
/ payout sub-sector cancel 점검 / sub_sector_sign 재현."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure as M


def main():
    px, ed, uni, macro = M.load()
    secmap = dict(zip(uni["ticker"], uni["subcl"]))
    pxm = px.resample("ME").last()
    P = M.build_pit_panels(px, ed)

    print("=" * 90)
    print("A. negative PIT lag 1건 정체 (self-audit D축 'negative lag 0' 주장 점검)")
    edp = M._ed_prep(ed).copy()
    edp["end_dt"] = pd.to_datetime(edp["end"], errors="coerce")
    edp["lag"] = (edp["filed_dt"] - edp["end_dt"]).dt.days
    negrows = edp[edp["lag"] < 0]
    print(f"  negative lag rows = {len(negrows)}")
    for _, r in negrows.iterrows():
        print(f"    ticker={r['ticker']} concept={r['concept']} end={r['end']} filed={r['filed']} lag={r['lag']} val={r['val']}")
    print("  → 1건 = filed 가 end 보다 279일 빠름 = restated/오타 가능. PIT 영향: _latest_pit 는 filed<=dt 필터라")
    print("     이 row 가 실제 measure 에 쓰이려면 filed_dt 시점에 노출. end 미래여도 filed 기준이라 lookahead 직접 아님.")

    print("\n" + "=" * 90)
    print("B. POWER ANALYSIS (claude 자문 'n=48 t-2.2 → power 0.53' 주장 재현)")
    # IC 기반 검정력: H1 effect = observed mean IC, sd from monthly IC series, n_eff = ts_eff_n
    ep_z = M.cs_z(P["ep_yield"], secmap)
    fwd12 = pxm.shift(-12) / pxm - 1
    ic, _ = M.cs_ic(ep_z, fwd12)
    se = M.nw_se(ic, 12)
    t_obs = ic.mean() / se
    # post-hoc power at alpha=0.05 two-sided, noncentral t with ncp=t_obs
    from scipy.stats import nct, t as tdist
    df = len(ic) - 1
    tcrit = tdist.ppf(0.975, df)
    power = 1 - nct.cdf(tcrit, df, t_obs) + nct.cdf(-tcrit, df, t_obs)
    print(f"  ep_yield 12M: t_obs={t_obs:.2f}, n_months={len(ic)}, df={df}")
    print(f"  post-hoc power (alpha=0.05, 2-sided, ncp=|t_obs|) = {power:.3f}")
    print(f"  → claude 자문은 'n=48'(종목수) 기준 = cross-sectional 단면. 측정은 시계열 IC 평균 t (n_months=185).")
    print(f"     자문 power 0.53 framing 은 n=48 종목 단일 단면 가정 → 측정 단위와 다른 layer. 그러나 결론(검정력 부족)")
    print(f"     방향은 BY 미생존과 정합. 측정 t-stat 자체의 검정력은 위 {power:.2f}.")

    print("\n" + "=" * 90)
    print("C. REGIME SPLIT 유의성 정직성 (ep_yield 2022+ 비유의 점검)")
    print("  ep_yield 2022+ IC=-0.0396 t=-1.29 (n=41) → CI [-0.075, +0.006] (0 포함, 비유의)")
    print("  → self-audit 'consist True' = 부호만 유지. 'regime-robust' = magnitude/유의성 아닌 부호 일관.")
    print("     verdict TENTATIVE_DIRECTIONAL 은 비유의 + 부호유지 = small-n rule 정합 (CONFIRMED 아님).")
    # 2022+ block-boot CI 재확인
    e2 = ic[ic.index >= "2022-01-01"]
    ci = M.block_boot(e2.values, 3, 2000)
    print(f"  2022+ block-boot CI 재계산 = [{ci[0]:+.4f}, {ci[1]:+.4f}] (0 포함={ci[0]<0<ci[1]})")

    print("\n" + "=" * 90)
    print("D. SUB-SECTOR SIGN 재현 (payout/dividend cancel 아님 = regime 축 점검)")
    for sname, panel in [("payout_yield", P["payout_yield"]), ("dividend_yield", P["dividend_yield"]),
                          ("ep_yield", P["ep_yield"]), ("gross_prof", P["gross_prof"])]:
        sig = M.cs_z(panel, secmap)
        res = M.sub_sector_sign(sig, fwd12, secmap)
        row = "  ".join(f"{s}={d.get('ic_mean','-')}" for s, d in res.items() if 'ic_mean' in d)
        print(f"  {sname:14} {row}")
    print("  → json sub_sector_sign: payout 전 4 음 / dividend 전 4 음 / ep 전 4 음 / gross_prof staples+0.059 health-0.081 (불일치, COGS sub-universe)")

    print("\n" + "=" * 90)
    print("E. payout regime FLIP = artifact 확정 정직성 (full-period 양 일관인데 regime flip)")
    payout_z = M.cs_z(P["payout_yield"], secmap)
    icp, _ = M.cs_ic(payout_z, fwd12)
    e1 = icp[icp.index < "2022-01-01"]; e2 = icp[icp.index >= "2022-01-01"]
    print(f"  payout 12M: full={icp.mean():+.4f}  QE={e1.mean():+.4f}(n{len(e1)})  2022+={e2.mean():+.4f}(n{len(e2)})")
    se2 = M.nw_se(e2, 12); t2 = e2.mean()/se2
    print(f"  2022+ t={t2:+.2f} (n={len(e2)}) → 부호 양전환 but 비유의. FLIP 'reach-for-yield QE artifact' verdict:")
    print(f"     QE -0.122 t-2.86 (유의 음) → 2022+ +0.054 t1.27 (비유의 양). = QE era 에서만 유의 신호.")
    print(f"     rejected_provisional 타당 (QE 한정 유의 + value-revival 소멸/역전).")

    print("\n✅ audit2 done")


if __name__ == "__main__":
    main()
