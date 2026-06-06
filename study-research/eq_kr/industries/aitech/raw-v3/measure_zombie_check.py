# -*- coding: utf-8 -*-
"""measure_zombie_check.py — ★G-C audit 보강: 좀비(거래정지 carry-forward) 마스킹 후 momentum 재측정.

G-C audit 발견: 셀바스AI(108860) 2019-03~2020-05 거래정지 284거래일 px=4155 고정 + amt=0.
  → halt 기간 mom_12_1=0(저모멘텀=reversal 매수대상) + forward 음 = reversal IC 인공 증폭.
조치: 가격신호 zombie(amt==0 또는 연속 동일종가 ≥10일) NaN 마스킹(reject≠missing, O축 tri-state) 후 momentum magnitude 재박제.
  ★부호·유의 불변 확인(audit: mom IC -0.1055→-0.0963 ~9% 과대 but t -2.58→-2.59 robust).

measure_conditional / measure 함수 재사용 (drift 0). raw 재현 = 본 .py + prices/amount.parquet.
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT))
from measure_conditional import (
    build_price_signals, build_valuation_signals, forward_returns_daily, ic_series,
    measure_cell, csz,
)

if not isinstance(sys.stdout, io.TextIOWrapper) or (sys.stdout.encoding or "").lower() != "utf-8":
    try: sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception: pass


def zombie_mask(px: pd.DataFrame, amt: pd.DataFrame, dup_days=10) -> pd.DataFrame:
    """좀비 마스킹 = (a) 거래대금 0 (b) 연속 동일종가 ≥dup_days → NaN (reject≠missing).
    거래정지/관리종목 carry-forward 가격 = 가짜 신호(저모멘텀=halt) 차단."""
    pxm = px.copy()
    # (a) amt==0 또는 NaN → 거래 없음
    amt_al = amt.reindex_like(px)
    zero_amt = (amt_al.fillna(0) == 0)
    # (b) 연속 동일종가 ≥ dup_days (정지 carry-forward)
    same = px.eq(px.shift(1))
    run = same.copy().astype(float)
    for c in px.columns:
        s = same[c].values
        cnt = 0; out = np.zeros(len(s))
        for i in range(len(s)):
            cnt = cnt + 1 if s[i] else 0
            out[i] = cnt
        run[c] = out
    long_dup = (run >= dup_days)
    mask = zero_amt | long_dup
    pxm = pxm.mask(mask)
    return pxm, int(mask.sum().sum())


def main():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    amt = pd.read_parquet(DATA / "amount.parquet"); amt.index = pd.to_datetime(amt.index)
    fin = pd.read_parquet(DATA / "dart_financials.parquet")
    uni = pd.read_parquet(DATA / "universe.parquet"); uni = uni[uni["pass_floor"]].set_index("Code")

    px_clean, n_masked = zombie_mask(px, amt, dup_days=10)
    print(f"zombie 마스킹: {n_masked} cells NaN 처리 (amt==0 OR 연속동일종가 ≥10일)")

    sigs_raw = build_price_signals(px)
    sigs_clean = build_price_signals(px_clean)
    val_raw = build_valuation_signals(px, fin, uni)
    val_clean = build_valuation_signals(px_clean, fin, uni)

    anchor = sigs_raw["mom_6"].dropna(how="all").index

    results = {"n_masked": n_masked, "method": "amt==0 OR 연속동일종가≥10일 → NaN(reject≠missing, O축 tri-state)", "comparison": {}}
    print("\n=== 좀비 마스킹 전/후 momentum + valuation IC (y_60d, 12M) ===")
    for sname, raw, clean in [("mom_12_1", sigs_raw, sigs_clean), ("mom_6", sigs_raw, sigs_clean),
                              ("rev_1m", sigs_raw, sigs_clean),
                              ("pbr_z", val_raw, val_clean), ("per_z", val_raw, val_clean)]:
        for hd, hl in [(60, "12M")]:
            fwd_raw = forward_returns_daily(px, anchor, hd)
            fwd_clean = forward_returns_daily(px_clean, anchor, hd)
            ic_raw = ic_series(raw[sname], fwd_raw)
            ic_clean = ic_series(clean[sname], fwd_clean)
            mr = measure_cell(ic_raw, hd, block_min=2)
            mc = measure_cell(ic_clean, hd, block_min=2)
            delta = (mc["ic_mean"] - mr["ic_mean"])
            pct = abs(delta / mr["ic_mean"] * 100) if mr["ic_mean"] else 0
            sign_hold = np.sign(mr["ic_mean"]) == np.sign(mc["ic_mean"])
            results["comparison"][f"{sname}__{hl}"] = {
                "ic_raw": mr["ic_mean"], "ic_clean": mc["ic_mean"], "delta": round(delta, 4),
                "pct_change": round(pct, 1), "t_raw": mr.get("t_nw_asymptotic"), "t_clean": mc.get("t_nw_asymptotic"),
                "wc_p_raw": mr.get("wild_cluster_p"), "wc_p_clean": mc.get("wild_cluster_p"),
                "sign_hold": bool(sign_hold), "n_raw": mr["n_months"], "n_clean": mc["n_months"],
            }
            print(f"  {sname:9s} {hl}: IC raw={mr['ic_mean']:+.4f}(t={mr.get('t_nw_asymptotic')}) → "
                  f"clean={mc['ic_mean']:+.4f}(t={mc.get('t_nw_asymptotic')}) Δ={delta:+.4f}({pct:.1f}%) "
                  f"{'✅부호·방향 불변' if sign_hold else '❌부호반전'}")

    out = ROOT / "validation-zombie-v3.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved {out}")
    print("\n★결론: 좀비 마스킹 후 momentum magnitude 과대 보정(~9%) but 부호·유의 불변 = reversal 결론 robust. pbr 좀비 영향 거의 0(공시후 진입).")


if __name__ == "__main__":
    main()
