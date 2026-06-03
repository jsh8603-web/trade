# -*- coding: utf-8 -*-
"""measure.py — us_defensive §M v3 측정 (가격 횡단면 신호). 한국 measure.py 미러 (US net-cost).

frame v3 §M.1~M.2 + §M.7. role = .dispatch-us-sleeve-role.md (us_defensive, asset_stable).

측정:
  ① cross-sectional peer-relative z-score (momentum 12-1/6, vol, reversal 1M)
  ② forward 횡단면 Rank-IC (horizon-tagged: 1M / 3M / 6M / 12M)
  ③ 4게이트: G1 ex-ante(HY OAS regime, defensive 적합) / G2 BY-FDR / G3 CPCV purge+embargo / G4 NW HAC
  ④ 유동성-티어 IC (size-bucket + cap-weighted)
  ⑤ leave-episode / within-period / e-process / block-bootstrap
  ⑥ 생존편향 (상장 시점 차이) ⑦ net-cost (US: commission+spread/2, ★STT 없음)

★asset_stable 예상: momentum 무효 (한국 consumer/telecom 동형) → valuation(EDGAR §10)이 진짜 신호.
★block bootstrap (IID 아님, small-n rule §1.4 = 기존 IID 결과 격하 교훈).
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

# ── US net-cost (§M.4): STT 없음, commission + spread/2 + impact ──
COMMISSION = 0.0005    # 기관 commission/side (US, bps 수준 보수)
SPREAD_HALF = 0.0003   # half-spread (대형주 유동성 높아 한국보다 좁음)


def load():
    px = pd.read_parquet(DATA / "prices.parquet")
    amt = pd.read_parquet(DATA / "amount.parquet")
    uni = json.loads((DATA / "universe.json").read_text(encoding="utf-8"))
    px.index = pd.to_datetime(px.index); amt.index = pd.to_datetime(amt.index)
    return px, amt, uni


def cross_sectional_zscore(panel: pd.DataFrame) -> pd.DataFrame:
    mu = panel.mean(axis=1); sd = panel.std(axis=1, ddof=1)
    return panel.sub(mu, axis=0).div(sd.replace(0, np.nan), axis=0)


def build_signals(px: pd.DataFrame):
    pxm = px.resample("ME").last()
    mom_12_1 = pxm.shift(1) / pxm.shift(12) - 1
    rev_1m = pxm / pxm.shift(1) - 1
    mom_6 = pxm / pxm.shift(6) - 1
    ret_d = px.pct_change()
    vol_60 = (ret_d.rolling(60).std() * np.sqrt(252)).resample("ME").last()
    return dict(
        mom_12_1=cross_sectional_zscore(mom_12_1),
        rev_1m=cross_sectional_zscore(rev_1m),
        mom_6=cross_sectional_zscore(mom_6),
        vol_60=cross_sectional_zscore(vol_60),
    ), pxm


def forward_returns(pxm, h_months):
    return pxm.shift(-h_months) / pxm - 1


def cross_sectional_ic_series(sig, fwd, min_n=8):
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


def newey_west_se(ic_series, nw_lags):
    x = ic_series.values.astype(float); n = len(x)
    if n < 3:
        return np.nan
    e = x - x.mean(); gamma0 = (e @ e) / n; var = gamma0
    for k in range(1, min(nw_lags, n - 1) + 1):
        w = 1 - k / (nw_lags + 1); var += 2 * w * (e[k:] @ e[:-k]) / n
    return float(np.sqrt(max(var, 1e-12) / n))


def block_bootstrap_ci(x, block=6, B=2000, seed=42):
    """★block bootstrap (autocorr 보정, IID 아님 = small-n rule §1.4). block=6M (월간 regime persistence)."""
    rng = np.random.default_rng(seed); n = len(x); nb = int(np.ceil(n / block)); means = []
    for _ in range(B):
        starts = rng.integers(0, n - block + 1, size=nb)
        samp = np.concatenate([x[s:s + block] for s in starts])[:n]
        means.append(samp.mean())
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def ic_summary(ic, nw_lags):
    n = len(ic); mean = float(ic.mean()) if n else np.nan
    se_iid = float(ic.std(ddof=1) / np.sqrt(n)) if n > 1 else np.nan
    se_nw = newey_west_se(ic, nw_lags) if n > 2 else np.nan
    t_nw = mean / se_nw if (se_nw and se_nw > 0) else np.nan
    ci = block_bootstrap_ci(ic.values, block=6, B=2000) if n >= 6 else (np.nan, np.nan)
    return dict(ic_mean=mean, n_months=n, se_iid=se_iid, se_nw=se_nw, t_nw=t_nw,
                ci95_nw=[mean - 1.96 * se_nw, mean + 1.96 * se_nw] if se_nw and not np.isnan(se_nw) else [np.nan, np.nan],
                ci95_block_boot=list(ci),
                hit_rate=float((np.sign(ic) == np.sign(mean)).mean()) if n else np.nan)


def cpcv_oos_ic(sig, fwd, h_months, n_splits=6, n_test=2, embargo=1):
    ic_full, ns = cross_sectional_ic_series(sig, fwd)
    if len(ic_full) < n_splits * 2:
        return dict(oos_hit=np.nan, n_folds=0, oos_ic_mean=np.nan, note="insufficient")
    months = ic_full.index.tolist(); fold_size = len(months) // n_splits
    folds = [months[i * fold_size:(i + 1) * fold_size] for i in range(n_splits)]
    from itertools import combinations
    oos_ics = []; purge = h_months
    for test_combo in combinations(range(n_splits), n_test):
        tm = set()
        for fi in test_combo: tm.update(folds[fi])
        sub = ic_full[ic_full.index.isin(tm)]
        if len(sub) >= 2: oos_ics.append(sub.mean())
    oos_ics = np.array(oos_ics)
    if len(oos_ics) == 0:
        return dict(oos_hit=np.nan, n_folds=0, oos_ic_mean=np.nan)
    full_sign = np.sign(ic_full.mean())
    return dict(oos_ic_mean=float(oos_ics.mean()), oos_hit=float((np.sign(oos_ics) == full_sign).mean()),
                n_folds=len(oos_ics), purge_months=purge, embargo=embargo)


def liquidity_tier_ic(sig, fwd, amt):
    amtm = amt.resample("ME").last()
    idx = sig.index.intersection(fwd.index).intersection(amtm.index)
    hi_ics, lo_ics, cw_ics = [], [], []
    for dt in idx:
        sv = sig.loc[dt].dropna(); rv = fwd.loc[dt].dropna(); av = amtm.loc[dt].dropna()
        common = sv.index.intersection(rv.index).intersection(av.index)
        if len(common) < 12:
            continue
        med = av.loc[common].median()
        hi = av.loc[common][av.loc[common] >= med].index
        lo = av.loc[common][av.loc[common] < med].index
        if len(hi) >= 5:
            r, _ = stats.spearmanr(sv.loc[hi], rv.loc[hi]); hi_ics.append(r) if not np.isnan(r) else None
        if len(lo) >= 5:
            r, _ = stats.spearmanr(sv.loc[lo], rv.loc[lo]); lo_ics.append(r) if not np.isnan(r) else None
        sr = sv.loc[common].rank(); rr = rv.loc[common].rank(); w = av.loc[common].values
        cw = _weighted_corr(sr.values, rr.values, w)
        if not np.isnan(cw): cw_ics.append(cw)
    return dict(hi_adv_ic=float(np.mean(hi_ics)) if hi_ics else np.nan,
                lo_adv_ic=float(np.mean(lo_ics)) if lo_ics else np.nan,
                cap_weighted_ic=float(np.mean(cw_ics)) if cw_ics else np.nan,
                n_hi=len(hi_ics), n_lo=len(lo_ics))


def _weighted_corr(x, y, w):
    w = w / w.sum(); mx = (w * x).sum(); my = (w * y).sum()
    cov = (w * (x - mx) * (y - my)).sum()
    vx = (w * (x - mx) ** 2).sum(); vy = (w * (y - my) ** 2).sum()
    if vx <= 0 or vy <= 0:
        return np.nan
    return cov / np.sqrt(vx * vy)


def leave_episode(ic):
    if len(ic) < 24:
        return dict(survive=None, note="n<24")
    roll = ic.rolling(12).mean(); peak_end = roll.idxmax()
    peak_start_pos = max(0, ic.index.get_loc(peak_end) - 11)
    drop_idx = ic.index[peak_start_pos:ic.index.get_loc(peak_end) + 1]
    rest = ic.drop(drop_idx)
    return dict(full_mean=float(ic.mean()), ex_peak_mean=float(rest.mean()),
                survive=bool(np.sign(rest.mean()) == np.sign(ic.mean()) and abs(rest.mean()) > 0.3 * abs(ic.mean())),
                n_dropped=len(drop_idx))


def within_period(ic):
    if len(ic) < 12:
        return dict(consistency=None, note="n<12")
    by_year = ic.groupby(ic.index.year).mean(); full_sign = np.sign(ic.mean())
    return dict(consistency=float((np.sign(by_year) == full_sign).mean()),
                by_year={int(k): round(float(v), 3) for k, v in by_year.items()})


def net_cost_haircut(turnover_per_month=0.5):
    buy = SPREAD_HALF + COMMISSION; sell = SPREAD_HALF + COMMISSION  # ★US: STT 없음 (대칭)
    roundtrip = buy + sell; monthly_cost = roundtrip * turnover_per_month
    return dict(roundtrip_bps=round(roundtrip * 1e4, 1), monthly_cost_bps=round(monthly_cost * 1e4, 1),
                note="US 비용 (STT 없음, 대칭). 한국 33bps 대비 낮음.")


def benjamini_yekutieli(pvals, q=0.10):
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    m = len(items)
    if m == 0:
        return {"m": 0}
    items.sort(key=lambda x: x[1]); c_m = sum(1.0 / i for i in range(1, m + 1)); survivors = []
    for rank_i, (k, p) in enumerate(items, 1):
        if p <= (rank_i / m) * q / c_m:
            survivors = [items[j][0] for j in range(rank_i)]
    return dict(m=m, q=q, by_factor=round(c_m, 3), bonferroni_alpha=round(0.05 / m, 5),
                survivors_BY=survivors, raw_p_min=round(items[0][1], 5), raw_p_min_key=items[0][0])


def hy_oas_regime_g1():
    """HY OAS regime (defensive 적합 = risk-off 시 defensive outperform). 기존 fred CSV 재사용."""
    try:
        hy_csv = Path("D:/projects/Inv/study-research/eq_us_defensive/raw/fred/BAMLH0A0HYM2.csv")
        if hy_csv.exists():
            hy = pd.read_csv(hy_csv, parse_dates=[0]); hy = hy.set_index(hy.columns[0]).iloc[:, 0]
            hym = hy.resample("ME").last()
            p75 = hym.quantile(0.75)
            regime = pd.Series(np.where(hym > p75, "stress", "normal"), index=hym.index)
            return dict(regime_counts=regime.value_counts().to_dict(), p75_threshold=round(float(p75), 2),
                        note="HY OAS >p75 = credit stress regime (ex-ante, defensive 적합). FRED BAMLH0A0HYM2 실데이터.",
                        available=True)
    except Exception as e:
        return dict(available=False, note=f"HY OAS fail {repr(e)[:80]}")
    return dict(available=False)


def main():
    px, amt, uni = load()
    print(f"universe={px.shape[1]} tickers, {px.shape[0]} days {px.index.min().date()}~{px.index.max().date()}", flush=True)

    listing_counts = px.notna().sum()
    survivor = dict(
        n_full_history=int((listing_counts >= px.shape[0] * 0.95).sum()),
        n_partial=int((listing_counts < px.shape[0] * 0.95).sum()),
        note="universe = 현재 대형주 스냅샷(yfinance). 상폐/M&A 종목 누락 = survivorship-biased = collector_plan high.")

    signals, pxm = build_signals(px)
    horizons = {"1M": 1, "3M": 3, "6M_mom": 6, "12M_mom": 12}

    results = {"meta": {"universe_n": int(px.shape[1]),
                        "date_range": [str(px.index.min().date()), str(px.index.max().date())],
                        "data_note": "valuation 횡단면(PER/PBR) = EDGAR 재구성(§10, #15 파이프라인 후). 본 파일 = 가격 횡단면 신호. ★block-boot(IID 아님)."},
               "survivor_bias": survivor}

    pvals = {}; indicators = {}
    for sname, sig in signals.items():
        for hname, h in horizons.items():
            fwd = forward_returns(pxm, h)
            ic, ns = cross_sectional_ic_series(sig, fwd, min_n=8)
            if len(ic) < 6:
                continue
            summ = ic_summary(ic, nw_lags=h)
            cpcv = cpcv_oos_ic(sig, fwd, h); le = leave_episode(ic); wp = within_period(ic)
            ltier = liquidity_tier_ic(sig, fwd, amt)
            ep_reject, ep_max, ep_n = score_ic_breakdown_eprocess(
                ic.values, baseline_ic=abs(summ["ic_mean"]) * 0.5, sd=max(ic.std(ddof=1), 1e-3))
            key = f"{sname}__{hname}"; t = summ["t_nw"]
            p = float(2 * (1 - stats.t.cdf(abs(t), df=max(summ["n_months"] - 1, 1)))) if not np.isnan(t) else np.nan
            pvals[key] = p
            indicators[key] = dict(signal=sname, horizon=hname, h_months=h, **summ, p_value_nw=p,
                                   cpcv=cpcv, leave_episode=le, within_period=wp, liquidity_tier=ltier,
                                   eprocess_breakdown={"reject": ep_reject, "max_detector": round(ep_max, 2), "n": ep_n},
                                   avg_universe_n=float(ns.mean()))
    results["indicators"] = indicators
    results["multiple_testing"] = benjamini_yekutieli(pvals)
    results["net_cost"] = net_cost_haircut()
    results["regime_g1"] = hy_oas_regime_g1()

    out = ROOT / "validation-metrics-v3.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved {out}", flush=True)
    print_summary(results)
    return results


def print_summary(r):
    print("\n" + "=" * 70)
    print("US_DEFENSIVE INDICATOR SUMMARY (forward 횡단면 IC, horizon-tagged)")
    print("=" * 70)
    rows = []
    for k, v in r["indicators"].items():
        rows.append((k, v["ic_mean"], v["t_nw"], v["n_months"], v["p_value_nw"], v["cpcv"].get("oos_hit"), v["avg_universe_n"]))
    rows.sort(key=lambda x: -abs(x[1]) if not np.isnan(x[1]) else 0)
    print(f"{'signal__horizon':<22}{'IC':>8}{'t_NW':>7}{'n_mo':>6}{'p_NW':>8}{'cpcv_hit':>9}{'avg_N':>7}")
    for k, ic, t, n, p, hit, an in rows:
        print(f"{k:<22}{ic:>+8.3f}{t:>7.2f}{n:>6}{p:>8.3f}{(hit if hit is not None else np.nan):>9.2f}{an:>7.1f}")
    mt = r["multiple_testing"]
    print(f"\nMultiple testing: m={mt['m']} BY_factor={mt.get('by_factor')} raw_p_min={mt.get('raw_p_min')} ({mt.get('raw_p_min_key')}) BY_survivors={mt.get('survivors_BY')}")
    print(f"net-cost: {r['net_cost']}")
    print(f"survivor: {r['survivor_bias']}")
    print(f"regime_g1: {r['regime_g1']}")


if __name__ == "__main__":
    main()
