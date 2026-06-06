# -*- coding: utf-8 -*-
"""measure_attack.py — auto S5 역공격 (최강 반증 직접 투척).

반증 3종 데이터 직접 검정:
  A1: capex_ratio = size factor 위장? → size-bucket 내 capex IC (대형/소형 분리)
  A2: PBR/capex OOS robust = 전동화 episode(2024-26) 종속? → sub-period(pre-2023 vs 2023+) IC 부호 일관성
  A3: 현대차/기아 대형주 의존? → 005380/000270 각 제외 LOO IC

산출: validation-attack-v3.json
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
import importlib.util

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("mc", str(ROOT / "measure_conditional.py"))
mc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mc)
import os
sys.stdout = io.TextIOWrapper(io.FileIO(os.dup(1), "w"), encoding="utf-8", write_through=True)
DATA = ROOT / "data"


def build_capex(px, monthly_idx):
    ext = pd.read_parquet(DATA / "dart_extended.parquet").copy()
    ext["rcept_dt"] = pd.to_datetime(ext["rcept_dt"], format="%Y%m%d", errors="coerce")
    ext = ext.dropna(subset=["rcept_dt"])
    panel = {}
    for code in px.columns:
        cf = ext[ext["code"] == code].sort_values("rcept_dt").drop_duplicates("rcept_dt", keep="last")
        if len(cf) < 4:
            continue
        s = pd.Series(index=monthly_idx, dtype=float)
        for dt in monthly_idx:
            av = cf[cf["rcept_dt"] <= dt]
            if len(av) == 0:
                continue
            last = av.iloc[-1]; a, p = last.get("assets"), last.get("ppe")
            if a and a > 0 and pd.notna(p):
                s[dt] = p / a
        panel[code] = s
    return mc.csz(pd.DataFrame(panel))


def ic_sub(sig, fwd, months_mask=None, exclude_codes=None, min_n=6):
    """IC series, 선택적으로 종목 제외 또는 월 마스크."""
    out = {}
    idx = sig.index.intersection(fwd.index)
    for dt in idx:
        if months_mask is not None and dt not in months_mask:
            continue
        sv = sig.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
        if exclude_codes:
            sv = sv.drop([c for c in exclude_codes if c in sv.index])
            rv = rv.drop([c for c in exclude_codes if c in rv.index])
        c = sv.index.intersection(rv.index)
        if len(c) < min_n:
            continue
        rho, _ = stats.spearmanr(sv.loc[c], rv.loc[c])
        if not np.isnan(rho):
            out[dt] = rho
    return pd.Series(out).sort_index()


def main():
    px, lab, fin, uni = mc.load()
    pxm = px.resample("ME").last()
    val_sigs = mc.build_valuation_signals(px, fin, uni)
    pbr = val_sigs["pbr_z"]
    capex = build_capex(px, pxm.index)
    anchor = pbr.dropna(how="all").index
    fwd60 = mc.forward_returns_daily(px, anchor, 60)

    results = {"meta": {"purpose": "S5 역공격 — capex size위장/episode종속/대형주의존 반증 검정"}}

    # ── A1: size-bucket 내 capex IC (대형 vs 소형) ──
    # marketcap proxy = px * shares근사
    shares = {}
    for code in px.columns:
        lp = px[code].dropna()
        if len(lp) and code in uni.index:
            mcv = uni.loc[code, "Marcap"]
            if pd.notna(mcv) and lp.iloc[-1] > 0:
                shares[code] = mcv / lp.iloc[-1]
    mktcap = pd.DataFrame({c: pxm[c] * shares[c] for c in shares})
    # 월별 median split: 대형(상위) / 소형(하위) bucket 내 capex IC
    big_ic, small_ic = {}, {}
    for dt in capex.index.intersection(fwd60.index):
        mc_dt = mktcap.loc[dt].dropna() if dt in mktcap.index else pd.Series(dtype=float)
        if len(mc_dt) < 8:
            continue
        med = mc_dt.median()
        big = mc_dt[mc_dt >= med].index; small = mc_dt[mc_dt < med].index
        for bucket, name, store in [(big, "big", big_ic), (small, "small", small_ic)]:
            sv = capex.loc[dt].reindex(bucket).dropna()
            rv = fwd60.loc[dt].reindex(bucket).dropna()
            c = sv.index.intersection(rv.index)
            if len(c) >= 4:
                rho, _ = stats.spearmanr(sv.loc[c], rv.loc[c])
                if not np.isnan(rho):
                    store[dt] = rho
    big_arr = np.array(list(big_ic.values())); small_arr = np.array(list(small_ic.values()))
    results["A1_size_bucket_capex"] = {
        "big_bucket": {"ic_mean": round(float(big_arr.mean()), 4) if len(big_arr) else None, "n": len(big_arr)},
        "small_bucket": {"ic_mean": round(float(small_arr.mean()), 4) if len(small_arr) else None, "n": len(small_arr)},
        "verdict": "size-bucket 내에서도 capex IC 음 유지 → size 위장 아님" if (len(big_arr) and len(small_arr) and big_arr.mean() < 0 and small_arr.mean() < 0) else "size 의존 의심",
    }
    print(f"A1 size-bucket capex IC(y_60d): big={results['A1_size_bucket_capex']['big_bucket']} small={results['A1_size_bucket_capex']['small_bucket']}")

    # ── A2: sub-period (pre-2023 전동화前 vs 2023+ 전동화) IC 부호 일관성 ──
    for sname, sig in [("pbr_z", pbr), ("capex_ratio", capex)]:
        ic_all = ic_sub(sig, fwd60)
        pre = ic_all[(ic_all.index >= "2019-01-01") & (ic_all.index <= "2022-12-31")]
        post = ic_all[(ic_all.index >= "2023-01-01")]
        results.setdefault("A2_subperiod", {})[sname] = {
            "pre_2023": {"ic": round(float(pre.mean()), 4), "n": len(pre)},
            "post_2023": {"ic": round(float(post.mean()), 4), "n": len(post)},
            "sign_consistent": bool(np.sign(pre.mean()) == np.sign(post.mean())),
        }
        print(f"A2 {sname}: pre-2023 IC={round(float(pre.mean()),4)}(n{len(pre)}) / 2023+ IC={round(float(post.mean()),4)}(n{len(post)}) "
              f"{'일관' if np.sign(pre.mean())==np.sign(post.mean()) else 'FLIP'}")

    # ── A3: 현대차(005380)/기아(000270) 각 제외 LOO ──
    for sname, sig in [("pbr_z", pbr), ("capex_ratio", capex)]:
        base = float(ic_sub(sig, fwd60).mean())
        ex_hmc = float(ic_sub(sig, fwd60, exclude_codes=["005380"]).mean())
        ex_kia = float(ic_sub(sig, fwd60, exclude_codes=["000270"]).mean())
        ex_both = float(ic_sub(sig, fwd60, exclude_codes=["005380", "000270"]).mean())
        results.setdefault("A3_loo", {})[sname] = {
            "base": round(base, 4), "ex_hyundai": round(ex_hmc, 4),
            "ex_kia": round(ex_kia, 4), "ex_both": round(ex_both, 4),
            "sign_robust": bool(all(np.sign(v) == np.sign(base) for v in [ex_hmc, ex_kia, ex_both])),
        }
        print(f"A3 {sname} LOO: base={round(base,4)} ex현대={round(ex_hmc,4)} ex기아={round(ex_kia,4)} ex둘다={round(ex_both,4)} "
              f"{'robust' if all(np.sign(v)==np.sign(base) for v in [ex_hmc,ex_kia,ex_both]) else 'flip'}")

    (ROOT / "validation-attack-v3.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("\nSaved validation-attack-v3.json")


if __name__ == "__main__":
    main()
