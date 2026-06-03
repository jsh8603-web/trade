# -*- coding: utf-8 -*-
"""measure.py — us_mega_tech §M v3 측정 (가격 횡단면 + reflexivity monitor). us_defensive 미러.

frame v3 §M.1~M.2 + §M.7. role = .dispatch-us-sleeve-role (us_mega_tech, compounder).

측정:
  ① cross-sectional peer-relative z-score (momentum 12-1/6, vol, reversal 1M)
     ★compounder = momentum 살아있을 가능성(growth persistence) 검증 = battery 양 momentum 과 비교.
  ② forward 횡단면 Rank-IC (1M/3M/6M/12M, ★n=11 basket = min_n 낮춤)
  ③ 4게이트: G1 ex-ante(NDX yoy regime) / G2 BY-FDR / G3 CPCV / G4 NW HAC + block-boot(block=6M)
  ④ ★H9 reflexivity monitor: intra-Mag7 60d rolling corr + breadth(EW-CW 3M spread) 동시 → cap-down 신호
  ⑤ ★momentum crash tail (Daniel-Moskowitz 2016): 모멘텀 신호의 좌측 꼬리(bear→rebound 급반전)
  ⑥ leave-episode / within-period / e-process / net-cost(US STT 없음)

★universe 11종 = 횡단면 IC small (avg_N~11) → small-n hedge 강. reflexivity·capex(§10)가 본질.
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, "D:/projects/Inv")
from core.assume.weight_falsification import rank_ic, score_ic_breakdown_eprocess

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

COMMISSION = 0.0005; SPREAD_HALF = 0.0002  # ★US mega-cap = 최고 유동성, spread 극소


def load():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    amt = pd.read_parquet(DATA / "amount.parquet"); amt.index = pd.to_datetime(amt.index)
    uni = json.loads((DATA / "universe.json").read_text(encoding="utf-8"))
    return px, amt, uni


def cs_z(panel):
    mu = panel.mean(axis=1); sd = panel.std(axis=1, ddof=1)
    return panel.sub(mu, axis=0).div(sd.replace(0, np.nan), axis=0)


def build_signals(px):
    pxm = px.resample("ME").last()
    return dict(
        mom_12_1=cs_z(pxm.shift(1) / pxm.shift(12) - 1),
        rev_1m=cs_z(pxm / pxm.shift(1) - 1),
        mom_6=cs_z(pxm / pxm.shift(6) - 1),
        vol_60=cs_z((px.pct_change().rolling(60).std() * np.sqrt(252)).resample("ME").last()),
    ), pxm


def cs_ic(sig, fwd, min_n=6):   # ★n=11 basket → min_n=6
    idx = sig.index.intersection(fwd.index); ics, ns, dates = [], [], []
    for dt in idx:
        sv = sig.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
        c = sv.index.intersection(rv.index)
        if len(c) < min_n:
            continue
        rho, _ = stats.spearmanr(sv.loc[c], rv.loc[c])
        if not np.isnan(rho):
            ics.append(rho); ns.append(len(c)); dates.append(dt)
    return pd.Series(ics, index=dates), pd.Series(ns, index=dates)


def nw_se(ic, lags):
    x = ic.values.astype(float); n = len(x)
    if n < 3:
        return np.nan
    e = x - x.mean(); g0 = (e @ e) / n; var = g0
    for k in range(1, min(lags, n - 1) + 1):
        w = 1 - k / (lags + 1); var += 2 * w * (e[k:] @ e[:-k]) / n
    return float(np.sqrt(max(var, 1e-12) / n))


def block_boot(x, block=6, B=2000, seed=42):
    rng = np.random.default_rng(seed); n = len(x); nb = int(np.ceil(n / block)); m = []
    for _ in range(B):
        st = rng.integers(0, n - block + 1, size=nb)
        m.append(np.concatenate([x[s:s+block] for s in st])[:n].mean())
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def cpcv(sig, fwd, h, n_splits=6, n_test=2):
    ic, _ = cs_ic(sig, fwd)
    if len(ic) < n_splits * 2:
        return dict(oos_hit=np.nan, n_folds=0)
    months = ic.index.tolist(); fs = len(months) // n_splits
    folds = [months[i*fs:(i+1)*fs] for i in range(n_splits)]
    from itertools import combinations
    oos = []
    for combo in combinations(range(n_splits), n_test):
        tm = set()
        for fi in combo: tm.update(folds[fi])
        sub = ic[ic.index.isin(tm)]
        if len(sub) >= 2: oos.append(sub.mean())
    oos = np.array(oos); fsign = np.sign(ic.mean())
    return dict(oos_ic_mean=float(oos.mean()), oos_hit=float((np.sign(oos) == fsign).mean()), n_folds=len(oos))


def within_period(ic):
    if len(ic) < 12:
        return None
    by = ic.groupby(ic.index.year).mean(); fs = np.sign(ic.mean())
    return float((np.sign(by) == fs).mean())


def leave_episode(ic):
    if len(ic) < 24:
        return None
    roll = ic.rolling(12).mean(); pe = roll.idxmax()
    ps = max(0, ic.index.get_loc(pe) - 11)
    drop = ic.index[ps:ic.index.get_loc(pe) + 1]; rest = ic.drop(drop)
    return dict(full=round(float(ic.mean()), 4), ex_peak=round(float(rest.mean()), 4),
                survive=bool(np.sign(rest.mean()) == np.sign(ic.mean()) and abs(rest.mean()) > 0.3 * abs(ic.mean())))


def measure_sig(sig, fwd, h, name):
    ic, ns = cs_ic(sig, fwd)
    if len(ic) < 6:
        return None
    n = len(ic); mean = float(ic.mean())
    se = nw_se(ic, h); t = mean / se if se and se > 0 else np.nan
    p = float(2 * (1 - stats.t.cdf(abs(t), df=max(n-1, 1)))) if not np.isnan(t) else np.nan
    ci = block_boot(ic.values, 6, 2000) if n >= 6 else (np.nan, np.nan)
    return dict(signal=name, h_months=h, ic_mean=round(mean, 4), n_months=n,
                se_nw=round(se, 4) if not np.isnan(se) else None,
                t_nw=round(t, 2) if not np.isnan(t) else None,
                p_value_nw=round(p, 4) if not np.isnan(p) else None,
                ci95_nw=[round(mean-1.96*se, 4), round(mean+1.96*se, 4)] if se and not np.isnan(se) else None,
                ci95_block_boot=[round(ci[0], 4), round(ci[1], 4)],
                cpcv=cpcv(sig, fwd, h), within_period=within_period(ic),
                leave_episode=leave_episode(ic), avg_universe_n=round(float(ns.mean()), 1))


def benjamini_yekutieli(pvals, q=0.10):
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    m = len(items)
    if m == 0:
        return {"m": 0}
    items.sort(key=lambda x: x[1]); cm = sum(1.0 / i for i in range(1, m + 1)); surv = []
    for r, (k, p) in enumerate(items, 1):
        if p <= (r / m) * q / cm: surv = [items[j][0] for j in range(r)]
    return dict(m=m, by_factor=round(cm, 3), survivors_BY=surv,
                raw_p_min=round(items[0][1], 5), raw_p_min_key=items[0][0])


def reflexivity_monitor(px):
    """★H9: intra-Mag7 60d rolling corr + breadth(EW-CW 3M spread). 동시 극단 = cap-down 신호.
    intra-corr 높음(동조 과열) AND breadth 음(소수 종목 주도) = reflexivity 정점 = 위험."""
    ret = px.pct_change()
    # intra-basket 평균 pairwise 60d rolling corr
    corrs = []
    idx = ret.index[60:]
    for i in range(60, len(ret), 5):  # 5일 간격 샘플
        window = ret.iloc[i-60:i]
        cm = window.corr().values
        n = cm.shape[0]
        avg_corr = (cm.sum() - n) / (n * (n - 1)) if n > 1 else np.nan
        corrs.append((ret.index[i], avg_corr))
    corr_s = pd.Series(dict(corrs))
    # breadth: EW vs CW 3M spread (CW 근사 = 동일가중 불가 → 첫종목 비중 대용 없음 → EW return vs basket median)
    pxm = px.resample("ME").last(); retm = pxm.pct_change()
    ew_3m = retm.mean(axis=1).rolling(3).sum()
    # CW 근사: 가장 큰 종목(시총 대용 = 가격×보편) 없으니 NVDA/AAPL/MSFT top3 평균 (mega 주도)
    top3 = [c for c in ["NVDA", "AAPL", "MSFT"] if c in retm.columns]
    cw_3m = retm[top3].mean(axis=1).rolling(3).sum() if top3 else ew_3m
    breadth_spread = (ew_3m - cw_3m)  # 음 = top3 주도(breadth 좁음)
    return dict(
        avg_intra_corr_recent=round(float(corr_s.dropna().iloc[-12:].mean()), 3) if len(corr_s.dropna()) else None,
        avg_intra_corr_full=round(float(corr_s.dropna().mean()), 3) if len(corr_s.dropna()) else None,
        intra_corr_p75=round(float(corr_s.dropna().quantile(0.75)), 3) if len(corr_s.dropna()) else None,
        breadth_spread_recent=round(float(breadth_spread.dropna().iloc[-3:].mean()), 4) if len(breadth_spread.dropna()) else None,
        n_high_corr_months=int((corr_s.dropna() > 0.70).sum()),
        note="★H9 reflexivity: intra-corr>0.70-0.75 AND breadth EW-CW 3M spread<-3~-5%p 동시 = cap-down 신호(supervisor throttle). corr=60d rolling pairwise avg, breadth=EW vs top3(NVDA/AAPL/MSFT) 3M spread.")


def net_cost():
    rt = 2 * (SPREAD_HALF + COMMISSION)  # US STT 없음 대칭, mega-cap 초저 spread
    return dict(roundtrip_bps=round(rt * 1e4, 1), monthly_cost_bps=round(rt * 0.5 * 1e4, 1),
                note="US mega-cap 최고유동성 = spread 극소(STT 없음).")


def ndx_regime_g1():
    """NDX(나스닥100) yoy regime (tech cycle ex-ante). bull/bear."""
    try:
        import yfinance as yf
        ndx = yf.download("^NDX", start="2015-01-01", end="2026-05-29", progress=False, auto_adjust=True)["Close"].squeeze()
        ndx.index = pd.to_datetime(ndx.index); m = ndx.resample("ME").last(); yoy = m / m.shift(12) - 1
        regime = pd.Series(np.where(yoy > 0.15, "bull", np.where(yoy < -0.15, "bear", "neutral")), index=yoy.index)
        return dict(regime_counts=regime.value_counts().to_dict(), available=True,
                    note="NDX yoy regime ex-ante (tech cycle). compounder = bull 편중 예상.")
    except Exception as e:
        return dict(available=False, note=f"NDX fail {repr(e)[:60]}")


def main():
    px, amt, uni = load()
    print(f"universe={px.shape[1]} basket, {px.shape[0]} days {px.index.min().date()}~{px.index.max().date()}", flush=True)

    listing = px.notna().sum()
    survivor = dict(n_full_history=int((listing >= px.shape[0] * 0.95).sum()),
                    n_partial=int((listing < px.shape[0] * 0.95).sum()),
                    note="Mag7 basket = 현 대형주(생존). PIT 멤버십(편입 시점=NVDA pre/post-AI) = collector_plan.")

    signals, pxm = build_signals(px)
    horizons = {"1M": 1, "3M": 3, "6M_mom": 6, "12M_mom": 12}
    results = {"meta": {"universe_n": int(px.shape[1]),
                        "date_range": [str(px.index.min().date()), str(px.index.max().date())],
                        "data_note": "★compounder basket n=11 = 횡단면 small-n hedge. valuation(PER/capex)=measure_valuation §10. block-boot(IID 아님)."},
               "survivor_bias": survivor}
    pvals, indicators = {}, {}
    for sname, sig in signals.items():
        for hname, h in horizons.items():
            fwd = pxm.shift(-h) / pxm - 1
            r = measure_sig(sig, fwd, h, f"{sname}__{hname}")
            if r:
                key = f"{sname}__{hname}"; results.setdefault("indicators", {})[key] = r; pvals[key] = r["p_value_nw"]
    indicators = results.get("indicators", {})
    results["multiple_testing"] = benjamini_yekutieli(pvals)
    results["net_cost"] = net_cost()
    results["regime_g1"] = ndx_regime_g1()
    results["reflexivity_monitor"] = reflexivity_monitor(px)

    out = ROOT / "validation-metrics-v3.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved {out}", flush=True)
    rows = sorted([(k, v["ic_mean"], v["t_nw"], v["n_months"], v["p_value_nw"], v["cpcv"].get("oos_hit"), v["avg_universe_n"])
                   for k, v in indicators.items()], key=lambda x: -abs(x[1]) if not np.isnan(x[1]) else 0)
    print(f"\n{'signal__horizon':<22}{'IC':>8}{'t_NW':>7}{'n_mo':>6}{'p_NW':>8}{'cpcv':>7}{'avgN':>6}")
    for k, ic, t, n, p, hit, an in rows:
        print(f"{k:<22}{ic:>+8.3f}{(t or 0):>7.2f}{n:>6}{(p or 0):>8.3f}{(hit if hit is not None else 0):>7.2f}{an:>6.1f}")
    mt = results["multiple_testing"]
    print(f"\nBY: m={mt['m']} raw_p_min={mt.get('raw_p_min')} ({mt.get('raw_p_min_key')}) survivors={mt.get('survivors_BY')}")
    print(f"reflexivity: {results['reflexivity_monitor']}")
    print(f"regime: {results['regime_g1'].get('regime_counts')}")


if __name__ == "__main__":
    main()
