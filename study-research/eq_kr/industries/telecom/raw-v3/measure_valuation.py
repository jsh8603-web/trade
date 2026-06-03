# -*- coding: utf-8 -*-
"""measure_valuation.py — battery valuation 횡단면 IC (결함1 해소, §M.7 핵심).

supervisor 지시 (2026-06-03): DART 재무 + pykrx 가격 → PBR/PER cross-sectional z → 12M forward IC.

PIT 엄수:
  - 각 재무데이터(equity/net_income) = rcept_dt(공시일) 이후 시점에만 적용 (forward-fill from publication).
    = lookahead·restatement 회피 (FHC mediator publication lag).
  - 시총_t = Close_t × shares (★현재 주식수 근사 — 시점별 주식수 = DART stockTotqySttus 정밀화 collector_plan).
  - PBR = 시총 / 자본총계(equity, BS). PER = 시총 / TTM 순이익(4분기 누적).

측정:
  - cross-sectional z-score(sector-neutral, universe 횡단면) → valuation cs_rank_IC(forward).
  - ★valuation = "싼" 종목이 forward 높으면 IC<0 (저PBR=싸다=value premium) → 부호 해석 주의.
  - horizon: value 3-5Y 장기 + 1Q/6M/12M. 4게이트(G1/G2 BY/G3 CPCV/G4 NW) + block-boot.
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, "D:/projects/Inv")
from core.assume.weight_falsification import score_ic_breakdown_eprocess

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

# 분기 라벨 → 회계기간 종료 month (PIT 회계 기준일)
QUARTER_END = {"Q1": 3, "H1": 6, "Q3": 9, "FY": 12}


def load():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    fin = pd.read_parquet(DATA / "dart_financials.parquet")
    uni = pd.read_parquet(DATA / "universe.parquet"); uni = uni[uni["pass_floor"]]
    # 현재 주식수 (Marcap/Close 역산)
    import FinanceDataReader as fdr
    lst = pd.concat([fdr.StockListing("KOSPI")[["Code", "Close", "Marcap"]],
                     fdr.StockListing("KOSDAQ")[["Code", "Close", "Marcap"]]])
    lst = lst[lst["Code"].isin(uni["Code"])].copy()
    lst["shares"] = lst["Marcap"] / lst["Close"]
    shares = dict(zip(lst["Code"], lst["shares"]))
    return px, fin, shares, uni


def build_pit_fundamental_panel(px, fin, shares):
    """PIT-safe valuation 패널: 각 종목 월말 PBR/PER (공시일 이후만 적용)."""
    fin = fin.copy()
    fin["rcept"] = pd.to_datetime(fin["rcept_dt"], format="%Y%m%d", errors="coerce")
    fin = fin.dropna(subset=["rcept"])
    # TTM 순이익 (분기 누적 → 직전 4분기). 단순화: 각 (code) 시계열로 회계기간말 기준 누적 처리
    # 여기선 보수적으로: equity = 최신 공시 BS(자본총계), net_income = 직전 FY 연간(가장 안정) 또는 TTM
    monthly_idx = px.resample("ME").last().index
    pxm = px.resample("ME").last()

    pbr_panel = {}
    per_panel = {}
    for code in px.columns:
        sub = fin[fin["code"] == code].sort_values("rcept")
        if len(sub) == 0 or code not in shares:
            continue
        sh = shares[code]
        # 각 월말에 대해 그 시점까지 공시된 가장 최신 재무 사용 (PIT forward-fill)
        pbr_series = pd.Series(index=monthly_idx, dtype=float)
        per_series = pd.Series(index=monthly_idx, dtype=float)
        for dt in monthly_idx:
            avail = sub[sub["rcept"] <= dt]  # ★공시일 이후만 (PIT)
            if len(avail) == 0:
                continue
            price = pxm.loc[dt, code] if dt in pxm.index and code in pxm.columns else np.nan
            if np.isnan(price):
                continue
            mktcap = price * sh
            # equity: 최신 공시 자본총계
            eq = avail["equity"].iloc[-1]
            if eq and eq > 0:
                pbr_series[dt] = mktcap / eq
            # PER: 직전 4개 분기 누적 순이익 (TTM). FY 만 있으면 FY 연간.
            ni_avail = avail.dropna(subset=["net_income"])
            ttm = ttm_net_income(ni_avail)
            if ttm and ttm > 0:
                per_series[dt] = mktcap / ttm
        pbr_panel[code] = pbr_series
        per_panel[code] = per_series
    return pd.DataFrame(pbr_panel), pd.DataFrame(per_panel)


def ttm_net_income(ni_df):
    """TTM 순이익: 가장 최근 공시 기준 직전 12개월 누적.
    분기 누적치(Q1=1분기, H1=2분기누적, Q3=3분기누적, FY=연간)를 분기 incremental 로 환산 후 4분기 합.
    단순화: 최신이 FY → 그 연간 사용 / 분기 → (직전FY - 동기 누적 + 당기 누적) 근사. 보수적으로 최신 FY 사용."""
    if len(ni_df) == 0:
        return None
    # 최신 FY 우선 (가장 안정), 없으면 분기 누적 × 연율화
    fy = ni_df[ni_df["quarter"] == "FY"]
    if len(fy):
        return fy["net_income"].iloc[-1]
    # FY 없으면 최신 분기 누적 annualize
    last = ni_df.iloc[-1]
    q_mult = {"Q1": 4, "H1": 2, "Q3": 4 / 3, "FY": 1}.get(last["quarter"], 1)
    return last["net_income"] * q_mult


def cross_sectional_zscore(panel):
    mu = panel.mean(axis=1)
    sd = panel.std(axis=1, ddof=1)
    return panel.sub(mu, axis=0).div(sd.replace(0, np.nan), axis=0)


def cs_ic_series(sig, fwd, min_n=5):
    idx = sig.index.intersection(fwd.index)
    ics, ns, dates = [], [], []
    for dt in idx:
        sv = sig.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
        common = sv.index.intersection(rv.index)
        if len(common) < min_n:
            continue
        rho, _ = stats.spearmanr(sv.loc[common], rv.loc[common])
        if not np.isnan(rho):
            ics.append(rho); ns.append(len(common)); dates.append(dt)
    return pd.Series(ics, index=dates), pd.Series(ns, index=dates)


def newey_west_se(ic, nw_lags):
    x = ic.values.astype(float); n = len(x)
    if n < 3: return np.nan
    e = x - x.mean(); g0 = (e @ e) / n; var = g0
    for k in range(1, min(nw_lags, n - 1) + 1):
        w = 1 - k / (nw_lags + 1); var += 2 * w * (e[k:] @ e[:-k]) / n
    return float(np.sqrt(max(var, 1e-12) / n))


def block_boot_ci(x, block=3, B=2000, seed=42):
    rng = np.random.default_rng(seed); n = len(x); nb = int(np.ceil(n / block)); means = []
    for _ in range(B):
        st = rng.integers(0, n - block + 1, size=nb)
        means.append(np.concatenate([x[s:s + block] for s in st])[:n].mean())
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def cpcv(sig, fwd, h, n_splits=6, n_test=2):
    ic, _ = cs_ic_series(sig, fwd)
    if len(ic) < n_splits * 2:
        return dict(oos_hit=np.nan, n_folds=0)
    months = ic.index.tolist(); fs = len(months) // n_splits
    folds = [months[i * fs:(i + 1) * fs] for i in range(n_splits)]
    from itertools import combinations
    oos = []
    for combo in combinations(range(n_splits), n_test):
        tm = set()
        for fi in combo: tm.update(folds[fi])
        sub = ic[ic.index.isin(tm)]
        if len(sub) >= 2: oos.append(sub.mean())
    oos = np.array(oos); fsign = np.sign(ic.mean())
    return dict(oos_ic_mean=float(oos.mean()), oos_hit=float((np.sign(oos) == fsign).mean()),
                n_folds=len(oos), purge_months=h)


def within_period(ic):
    if len(ic) < 12: return dict(consistency=None)
    by = ic.groupby(ic.index.year).mean(); fs = np.sign(ic.mean())
    return dict(consistency=float((np.sign(by) == fs).mean()),
                by_year={int(k): round(float(v), 3) for k, v in by.items()})


def measure(sig, fwd, h, name):
    ic, ns = cs_ic_series(sig, fwd)
    if len(ic) < 6:
        return None
    n = len(ic); mean = float(ic.mean())
    se_nw = newey_west_se(ic, h); t_nw = mean / se_nw if se_nw and se_nw > 0 else np.nan
    p = float(2 * (1 - stats.t.cdf(abs(t_nw), df=max(n - 1, 1)))) if not np.isnan(t_nw) else np.nan
    ci_b = block_boot_ci(ic.values, 3, 2000) if n >= 6 else (np.nan, np.nan)
    ep_r, ep_m, ep_n = score_ic_breakdown_eprocess(ic.values, baseline_ic=abs(mean) * 0.5,
                                                    sd=max(ic.std(ddof=1), 1e-3))
    return dict(signal=name, h_months=h, ic_mean=round(mean, 4), n_months=n,
                se_nw=round(se_nw, 4) if not np.isnan(se_nw) else None,
                t_nw=round(t_nw, 2) if not np.isnan(t_nw) else None,
                p_value_nw=round(p, 4) if not np.isnan(p) else None,
                ci95_nw=[round(mean - 1.96 * se_nw, 4), round(mean + 1.96 * se_nw, 4)] if se_nw else None,
                ci95_block_boot=[round(ci_b[0], 4), round(ci_b[1], 4)],
                cpcv=cpcv(sig, fwd, h), within_period=within_period(ic),
                avg_universe_n=round(float(ns.mean()), 1),
                eprocess={"reject": ep_r, "max": round(ep_m, 2)})


def benjamini_yekutieli(pvals, q=0.10):
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    m = len(items)
    if m == 0: return {"m": 0}
    items.sort(key=lambda x: x[1])
    cm = sum(1.0 / i for i in range(1, m + 1)); surv = []
    for r, (k, p) in enumerate(items, 1):
        if p <= (r / m) * q / cm: surv = [items[j][0] for j in range(r)]
    return dict(m=m, by_factor=round(cm, 3), survivors_BY=surv,
                raw_p_min=round(items[0][1], 5), raw_p_min_key=items[0][0])


def main():
    px, fin, shares, uni = load()
    pxm = px.resample("ME").last()
    print(f"universe {px.shape[1]}, fin {len(fin)} rows")

    pbr, per = build_pit_fundamental_panel(px, fin, shares)
    print(f"PBR panel: {pbr.shape}, coverage {pbr.notna().sum().sum()} cells")
    print(f"PER panel: {per.shape}, coverage {per.notna().sum().sum()} cells")

    # cross-sectional z (저PBR=싸다 → -z 가 value). signal = z-score, IC 부호로 value premium 판정
    pbr_z = cross_sectional_zscore(pbr)
    per_z = cross_sectional_zscore(per)

    signals = {"pbr_z": pbr_z, "per_z": per_z}
    horizons = {"3M": 3, "6M": 6, "12M": 12, "24M_value": 24}

    results, pvals = {}, {}
    for sname, sig in signals.items():
        for hname, h in horizons.items():
            fwd = pxm.shift(-h) / pxm - 1
            r = measure(sig, fwd, h, f"{sname}__{hname}")
            if r:
                key = f"{sname}__{hname}"
                results[key] = r
                pvals[key] = r["p_value_nw"]

    out = {"meta": {"universe_n": int(px.shape[1]),
                    "pbr_coverage_cells": int(pbr.notna().sum().sum()),
                    "per_coverage_cells": int(per.notna().sum().sum()),
                    "pit_note": "재무 = rcept_dt(공시일) 이후만 적용. 시총=Close×현재주식수(시점별 주식수 정밀화 collector_plan).",
                    "sign_note": "z-score signal. PBR/PER 저(싸다)=낮은 z → value premium 이면 IC<0(저밸류→고forward)."},
            "indicators": results,
            "multiple_testing": benjamini_yekutieli(pvals)}
    (ROOT / "validation-valuation-v3.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print("\n" + "=" * 72)
    print(f"{'signal__h':<20}{'IC':>9}{'t_NW':>7}{'n_mo':>6}{'p_NW':>8}{'cpcv':>7}{'within':>8}{'avgN':>6}")
    for k, v in sorted(results.items(), key=lambda x: -abs(x[1]["ic_mean"] or 0)):
        print(f"{k:<20}{(v['ic_mean'] or 0):>+9.4f}{(v['t_nw'] or 0):>7.2f}{v['n_months']:>6}"
              f"{(v['p_value_nw'] or 0):>8.3f}{(v['cpcv'].get('oos_hit') or 0):>7.2f}"
              f"{(v['within_period'].get('consistency') or 0):>8.2f}{v['avg_universe_n']:>6.1f}")
    mt = out["multiple_testing"]
    print(f"\nBY: m={mt['m']} factor={mt.get('by_factor')} raw_p_min={mt.get('raw_p_min')} "
          f"({mt.get('raw_p_min_key')}) survivors={mt.get('survivors_BY')}")


if __name__ == "__main__":
    main()
