# -*- coding: utf-8 -*-
"""measure_attack.py — 정유 S5 역공격 (최강 반증 직접 투척, frame K축 무비판채택 차단).

★반증 3종:
  ATK-1: 유가 forward 음(-)이 단지 '정유주 자체 mean-reversion'(가격 reversal) 아닌가?
         = 유가 빼고 정유 자체 과거수익 → forward 음이면 유가 신호 = 가격 reversal 위장.
  ATK-2: 유가 forward 음(-)이 'KOSPI 시장 베타' 효과 아닌가? (시장 동반 하락)
         = 시장수익 통제 후 유가 forward 음 잔존?
  ATK-3: capex spurious REJECTION이 과한가? = detrend(차분) capex 가 진짜 신호 남나?
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


def srho(x, y, lo="2019-01-01"):
    c = x.dropna().index.intersection(y.dropna().index)
    c = [i for i in c if i >= pd.Timestamp(lo)]
    if len(c) < 8:
        return None, None, len(c)
    rho, p = stats.spearmanr(x.loc[c], y.loc[c])
    return float(rho), float(p), len(c)


def partial_rho(x, y, z, lo="2019-01-01"):
    """z 통제 후 x-y partial Spearman (rank 잔차 corr)."""
    c = x.dropna().index.intersection(y.dropna().index).intersection(z.dropna().index)
    c = [i for i in c if i >= pd.Timestamp(lo)]
    if len(c) < 10:
        return None, len(c)
    xr = stats.rankdata(x.loc[c]); yr = stats.rankdata(y.loc[c]); zr = stats.rankdata(z.loc[c])
    # residualize x,y on z
    def resid(a, b):
        b1 = np.column_stack([np.ones(len(b)), b])
        coef = np.linalg.lstsq(b1, a, rcond=None)[0]
        return a - b1 @ coef
    xres = resid(xr, zr); yres = resid(yr, zr)
    rho, _ = stats.spearmanr(xres, yres)
    return float(rho), len(c)


def main():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    cyc = pd.read_parquet(DATA / "refining_cycle.parquet"); cyc.index = pd.to_datetime(cyc.index)
    uni = pd.read_parquet(DATA / "universe.parquet")
    strict2 = [c for c in uni[uni["is_refining_core"] & uni["pass_floor_strict"]]["Code"] if c in px.columns]
    pxm = px.resample("ME").last()
    ret = pxm[strict2].pct_change().mean(axis=1)
    fwd3 = pxm[strict2].pct_change(3).mean(axis=1).shift(-3)
    cycm = cyc.resample("ME").last()
    brent = cycm["brent"]

    # 시장수익 = KOSPI proxy (정유 패널 own 제외 어려움 → 전체 11종 평균을 시장 proxy)
    allpx = pxm.pct_change().mean(axis=1)   # 11종 평균(정유+가스) = 에너지섹터 proxy
    mom_self = pxm[strict2].pct_change(3).mean(axis=1)  # 정유 자체 과거 3M 수익(reversal 점검)

    out = {"meta": {"panel": strict2, "purpose": "S5 역공격 — 유가 forward 음 반증 3종"},
           "attacks": {}}

    # ATK-1: 유가 빼고 정유 자체 과거수익 → forward (가격 reversal 위장?)
    r_self, p_self, n1 = srho(mom_self, fwd3)
    out["attacks"]["ATK1_price_reversal"] = {
        "self_mom3_fwd3_rho": round(r_self, 4) if r_self else None, "p": round(p_self, 4) if p_self else None, "n": n1,
        "verdict": ("★정유 자체 reversal 존재 — 유가 신호와 분리 필요" if (r_self and r_self < -0.15 and p_self < 0.1)
                    else "정유 자체 reversal 약/무 → 유가 forward 음은 가격 reversal 위장 아님")}

    # ATK-2: 시장(에너지섹터) 통제 후 유가 forward 음 잔존? (partial)
    pr, n2 = partial_rho(brent, fwd3, allpx)
    r_raw, _, _ = srho(brent, fwd3)
    out["attacks"]["ATK2_market_beta"] = {
        "brent_fwd3_raw_rho": round(r_raw, 4) if r_raw else None,
        "brent_fwd3_partial_on_market_rho": round(pr, 4) if pr else None, "n": n2,
        "verdict": ("시장 통제 후 유가 forward 음 소멸 → 시장베타 효과" if (pr is not None and abs(pr) < 0.1)
                    else "★시장 통제 후에도 유가 forward 음 잔존 → 유가 고유 신호(mean-reversion robust)")}

    # ATK-3: capex detrend(차분) 진짜 신호 남나? (spurious REJECTION 재검)
    ext = pd.read_parquet(DATA / "dart_extended.parquet").copy()
    ext["rcept_dt"] = pd.to_datetime(ext["rcept_dt"], format="%Y%m%d", errors="coerce")
    ext = ext.dropna(subset=["rcept_dt"])
    core = [c for c in uni[uni["is_refining_core"]]["Code"] if c in px.columns]
    cap = {}
    for code in core:
        cf = ext[ext["code"] == code].sort_values("rcept_dt").drop_duplicates("rcept_dt", keep="last")
        s = pd.Series(index=pxm.index, dtype=float)
        for dt in pxm.index:
            av = cf[cf["rcept_dt"] <= dt]
            if len(av):
                l = av.iloc[-1]; a, p = l.get("assets"), l.get("ppe")
                if a and a > 0 and pd.notna(p):
                    s[dt] = p / a
        cap[code] = s
    ind_cap = pd.DataFrame(cap).mean(axis=1)
    # detrend = 차분 + brent 통제
    r_d, p_d, n3 = srho(ind_cap.diff(), fwd3)
    pr_cap, n3b = partial_rho(ind_cap, fwd3, brent)  # brent 통제 후 capex
    out["attacks"]["ATK3_capex_detrend"] = {
        "d_capex_fwd3_rho": round(r_d, 4) if r_d else None, "p": round(p_d, 4) if p_d else None,
        "capex_fwd3_partial_on_brent_rho": round(pr_cap, 4) if pr_cap else None, "n": n3,
        "verdict": ("★capex detrend/통제 후 신호 소멸 → spurious REJECTION 정당(유가 proxy 확인)"
                    if (pr_cap is not None and abs(pr_cap) < 0.15) else "capex 통제 후 잔존 → REJECTION 재검 필요")}

    (ROOT / "validation-attack-v3.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("=== S5 역공격 (최강 반증 투척) ===")
    for k, v in out["attacks"].items():
        print(f"\n[{k}]")
        for kk, vv in v.items():
            print(f"  {kk}: {vv}")
    print("\nSaved validation-attack-v3.json")


if __name__ == "__main__":
    main()
