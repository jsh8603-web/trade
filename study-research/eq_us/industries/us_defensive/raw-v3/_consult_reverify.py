# -*- coding: utf-8 -*-
"""_consult_reverify.py — 3R 자문 수렴 의견의 적용 타당성 재검증 (advisory-protocol, 2026-06-05).

사용자 지시: 자문 수렴 = 의견(reference), 적용 타당성은 main 이 정량 재검증.
즉시 확인 가능한 critical 3개를 실데이터/코드로 검증 (무거운 trap-veto IC·horizon backtest 별도):
  검증1 [결함4] net_issuance MAD=0 silent — 실제 0 mass 몰림으로 metric 0벡터화되나?
  검증2 [critical] capped-EW infeasibility — small-N(comm 4)·top_k=10서 weight 합<1 + clip→renorm?
  검증3 [자문a] interaction 생짜곱항 vs main collinearity — double-count 위험 실재하나?

재현: python _consult_reverify.py (합성 0 = 실 EDGAR/가격, go-live 무접촉)
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

INV = "D:/projects/Inv"
HERE = str(Path(__file__).resolve().parent)
sys.path.insert(0, INV)
sys.path.insert(0, HERE)

import measure as M
import _breadth_sweep as BS
from stock.cross_sectional_selection import _capped_equal_weight


def _robust_z_col(s):
    med = s.median()
    mad = (s - med).abs().median()
    scale = 1.4826 * mad
    return (s - med) / scale if scale > 1e-12 else s * 0.0


def main():
    px, ed, uni, macro = M.load()
    amt = pd.read_parquet(Path(HERE) / "data" / "amount.parquet"); amt.index = pd.to_datetime(amt.index)
    P = M.build_pit_panels(px, ed)
    B = BS.build_breadth_panels(px, ed, amt)

    print("=" * 76)
    print("[검증1 — 결함4 MAD=0 silent] net_issuance 분포")
    ni = B["net_issuance"]
    tot, mad0 = 0, 0
    zero_share = []
    for dt in ni.index:
        row = ni.loc[dt].dropna()
        if len(row) < 5:
            continue
        tot += 1
        med = row.median()
        mad = (row - med).abs().median()
        if mad <= 1e-12:
            mad0 += 1
        zero_share.append(float((row.abs() < 1e-9).mean()))
    print(f"  net_issuance 유효월 {tot} / MAD=0(신호 silent 소멸) 월 {mad0} ({100*mad0/max(tot,1):.1f}%)")
    print(f"  월별 '정확히 0' 값 평균 비율 = {100*np.mean(zero_share):.1f}%  (>50% 면 MAD=0 위험 실재)")
    print(f"  → 자문 결함4 판정: {'★실재(guard 필요)' if (mad0>0 or np.mean(zero_share)>0.4) else '미발생(현 데이터)'}")

    print("=" * 76)
    print("[검증2 — critical capped-EW infeasibility] 현 _capped_equal_weight 거동")
    # 현 SelectionConfig default: max_weight_single=0.05, max_weight_sector=0.20
    for n, cap_s, cap_sec, label in [(10, 0.05, 0.20, "top_k=10 단일섹터"),
                                       (4, 0.05, 0.20, "comm_mature n=4"),
                                       (4, 0.10, 0.30, "comm n=4 @ risk_gate cap"),
                                       (15, 0.05, 0.20, "섹터 15종")]:
        sel = [f"T{i}" for i in range(n)]
        secs = {t: "s" for t in sel}            # 단일 섹터 (sector cap 효과 격리)
        w = _capped_equal_weight(sel, secs, cap_s, cap_sec)
        tot_w = sum(w.values())
        per = list(w.values())[0] if w else 0.0
        viol = "infeasible(합<1=미투자)" if tot_w < 0.999 else "feasible"
        print(f"  {label:24s} N={n} single_cap={cap_s}: Σw={tot_w:.3f} per={per:.3f} → {viol}")
    print("  → 자문 critical: Σw<1 이면 자본 미투자(under-allocation) = small-N서 발생 확인")

    print("=" * 76)
    print("[검증3 — 자문a interaction collinearity] 생짜곱항 z(z1·z2) vs main z1,z2")
    div = P.get("dividend_yield"); opp = B.get("op_profitability")
    if div is None or opp is None:
        print(f"  dividend_yield/op_profitability 패널 부재 (P keys={list(P)[:6]}.. / B keys={list(B)[:6]}..) → DEF-2 collinearity skip")
        return
    cds, cos = [], []
    for dt in div.index:
        d = div.loc[dt].dropna(); o = opp.loc[dt].dropna()
        c = d.index.intersection(o.index)
        if len(c) < 10:
            continue
        dz = _robust_z_col(d.loc[c]); oz = _robust_z_col(o.loc[c])
        prod = dz * oz
        df = pd.DataFrame({"p": prod, "dz": dz, "oz": oz}).dropna()
        if len(df) < 10 or df["p"].std() < 1e-9:
            continue
        cds.append(df["p"].corr(df["dz"])); cos.append(df["p"].corr(df["oz"]))
    if cds:
        md, mo = np.nanmean(cds), np.nanmean(cos)
        worst = max(abs(md), abs(mo))
        print(f"  생짜곱항 vs main: corr(prod,div)={md:+.3f} / corr(prod,op)={mo:+.3f} (n_month={len(cds)})")
        print(f"  |corr| max = {worst:.3f} → double-count 위험: "
              f"{'★실재(>0.2, FWL 잔차화 권장)' if worst > 0.2 else '경미(<0.2, 생짜 곱항도 근사 직교)'}")
    else:
        print("  유효 월 부족 → collinearity 측정 불가")


if __name__ == "__main__":
    main()
