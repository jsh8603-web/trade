# -*- coding: utf-8 -*-
"""measure_critique.py — ★aitech S5 역공격 + 비판검토 실측 (S6 audit 방어).

비판 가설을 데이터로 직접 검정 (자문 무비판 채택 0):
  Q1: pbr value premium = size factor 위장? (26종 small-universe → 저PBR=소형주 confound)
      → Fama-MacBeth: ret ~ PBR_rank + Size_rank 매월 회귀 → 계수 시계열 t.
  Q2: pbr 신호 = HBM/AI 버블기(2021)·붕괴기(2022) episode 종속? (sub-period 부호 일관)
  Q3: momentum reversal = 게임주 단일 episode(P2E 붕괴 2022) 종속? (leave-2022-out)
  Q4: per_z = 적자종목 제외 편의? (E/P earnings yield 음수익 처리 대체)
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
from measure_conditional import load, build_price_signals, build_valuation_signals, forward_returns_daily, ic_series, csz

if not isinstance(sys.stdout, io.TextIOWrapper) or (sys.stdout.encoding or "").lower() != "utf-8":
    try: sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception: pass


def fama_macbeth_pbr_size(px, fin, uni, val_sigs, horizon_d=60):
    """Q1: ret_rank ~ PBR_rank + Size_rank 매월 cross-section 회귀 → 계수 시계열 t-test.
    PBR|Size 통제 후 유의 유지 = size 위장 아님."""
    pxm = px.resample("ME").last()
    anchor = val_sigs["pbr_z"].dropna(how="all").index
    fwd = forward_returns_daily(px, anchor, horizon_d)
    # size = log marcap proxy = log(price × shares근사). uni Marcap 현재값 → 시점별은 가격비례 근사.
    uni_mc = uni["Marcap"]
    pbr = val_sigs["pbr_z"]
    coefs_pbr, coefs_size = [], []
    for dt in pbr.index.intersection(fwd.index):
        pv = pbr.loc[dt].dropna()
        rv = fwd.loc[dt].dropna()
        common = pv.index.intersection(rv.index)
        common = [c for c in common if c in uni_mc.index and pd.notna(uni_mc.get(c)) and pd.notna(pxm.loc[dt, c])]
        if len(common) < 8:
            continue
        # size = log(현재시총 × 가격/현재가격) ≈ log(시점 시총)
        size = pd.Series({c: np.log(uni_mc[c] * pxm.loc[dt, c] / px[c].dropna().iloc[-1]) for c in common})
        sr_pbr = stats.rankdata(pv.loc[common]) / len(common) - 0.5
        sr_size = stats.rankdata(size.loc[common]) / len(common) - 0.5
        rr = stats.rankdata(rv.loc[common]) / len(common) - 0.5
        X = np.column_stack([np.ones(len(common)), sr_pbr, sr_size])
        beta = np.linalg.lstsq(X, rr, rcond=None)[0]
        coefs_pbr.append(beta[1]); coefs_size.append(beta[2])
    def tstat(a):
        a = np.array(a); return float(a.mean() / (a.std(ddof=1) / np.sqrt(len(a)))) if len(a) > 2 else np.nan
    # univariate PBR
    uni_pbr = []
    for dt in pbr.index.intersection(fwd.index):
        pv = pbr.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
        common = pv.index.intersection(rv.index)
        if len(common) < 8: continue
        rho, _ = stats.spearmanr(pv.loc[common], rv.loc[common])
        if not np.isnan(rho): uni_pbr.append(rho)
    return {
        "univariate_pbr_ic_mean": round(float(np.mean(uni_pbr)), 4), "univariate_n": len(uni_pbr),
        "pbr_controlled_b": round(float(np.mean(coefs_pbr)), 4), "pbr_controlled_t": round(tstat(coefs_pbr), 2),
        "size_controlled_b": round(float(np.mean(coefs_size)), 4), "size_controlled_t": round(tstat(coefs_size), 2),
        "n_months": len(coefs_pbr),
        "verdict": ("★PBR 독립 alpha (size 위장 아님)" if abs(tstat(coefs_pbr)) > 2
                    else "PBR|Size 통제 후 비유의 = size 위장 가능"),
    }


def subperiod_consistency(px, val_sigs, price_sigs, horizon_d=60):
    """Q2/Q3: sub-period 부호 일관 (버블 2019-21 vs 붕괴/회복 2022-26)."""
    anchor = val_sigs["pbr_z"].dropna(how="all").index
    fwd = forward_returns_daily(px, anchor, horizon_d)
    periods = {"2019-2021": ("2019-01-01", "2021-12-31"), "2022-2026": ("2022-01-01", "2026-12-31")}
    out = {}
    for sname, sig in {"pbr_z": val_sigs["pbr_z"], "per_z": val_sigs["per_z"],
                       "mom_12_1": price_sigs["mom_12_1"]}.items():
        ic = ic_series(sig, fwd)
        row = {}
        for pn, (lo, hi) in periods.items():
            sub = ic[(ic.index >= lo) & (ic.index <= hi)]
            row[pn] = {"ic": round(float(sub.mean()), 4), "n": len(sub)} if len(sub) >= 3 else None
        signs = [np.sign(v["ic"]) for v in row.values() if v]
        row["consistent"] = bool(len(set(signs)) == 1) if signs else None
        out[sname] = row
    return out


def leave_2022_out(px, val_sigs, price_sigs, horizon_d=60):
    """Q3: momentum reversal = 2022 P2E붕괴 단일 episode 종속? (2022 제외 후 생존)."""
    anchor = val_sigs["pbr_z"].dropna(how="all").index
    fwd = forward_returns_daily(px, anchor, horizon_d)
    out = {}
    for sname, sig in {"mom_12_1": price_sigs["mom_12_1"], "pbr_z": val_sigs["pbr_z"]}.items():
        ic = ic_series(sig, fwd)
        full = float(ic.mean())
        ex22 = ic[~((ic.index >= "2022-01-01") & (ic.index <= "2022-12-31"))]
        out[sname] = {"full_ic": round(full, 4), "ex2022_ic": round(float(ex22.mean()), 4),
                      "n_full": len(ic), "n_ex2022": len(ex22),
                      "verdict": "부호 생존(episode 종속 아님)" if np.sign(full) == np.sign(ex22.mean()) else "부호 반전(episode 종속)"}
    return out


def main():
    px, lab, fin, uni = load()
    uni_idx = uni.copy()
    price_sigs = build_price_signals(px)
    val_sigs = build_valuation_signals(px, fin, uni_idx)

    results = {
        "Q1_fama_macbeth_pbr_size": fama_macbeth_pbr_size(px, fin, uni_idx, val_sigs, horizon_d=60),
        "Q2Q3_subperiod_consistency": subperiod_consistency(px, val_sigs, price_sigs, horizon_d=60),
        "Q3_leave_2022_out": leave_2022_out(px, val_sigs, price_sigs, horizon_d=60),
    }
    out = ROOT / "validation-critique-v3.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Saved {out}\n")

    q1 = results["Q1_fama_macbeth_pbr_size"]
    print(f"=== Q1 Fama-MacBeth PBR vs Size (y_60d) ===")
    print(f"  univariate PBR IC={q1['univariate_pbr_ic_mean']} (n={q1['univariate_n']})")
    print(f"  PBR|Size b={q1['pbr_controlled_b']} t={q1['pbr_controlled_t']} / Size|PBR b={q1['size_controlled_b']} t={q1['size_controlled_t']} (n_mo={q1['n_months']})")
    print(f"  → {q1['verdict']}")
    print(f"\n=== Q2/Q3 sub-period 부호 일관 ===")
    for s, d in results["Q2Q3_subperiod_consistency"].items():
        p1 = d.get("2019-2021"); p2 = d.get("2022-2026")
        print(f"  {s:10s} 2019-21={p1['ic'] if p1 else 'NA':+.4f} 2022-26={p2['ic'] if p2 else 'NA':+.4f} consistent={d['consistent']}")
    print(f"\n=== Q3 leave-2022-out ===")
    for s, d in results["Q3_leave_2022_out"].items():
        print(f"  {s:10s} full={d['full_ic']:+.4f} ex2022={d['ex2022_ic']:+.4f} {d['verdict']}")


if __name__ == "__main__":
    main()
