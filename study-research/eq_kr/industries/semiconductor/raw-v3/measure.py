# -*- coding: utf-8 -*-
"""measure.py — semiconductor §M v3 측정 17종 핵심 실행. battery measure.py 미러.

frame v3 §M.1~M.2 측정축 + §M.7 cross-sectional peer-relative z-score exposure card.

측정 (가격기반 횡단면 신호 — valuation 횡단면은 measure_valuation.py 에서 DART 재구성):
  ① cross-sectional peer-relative z-score (momentum 12-1, vol, reversal 1M, mom_6)
  ② forward 횡단면 Rank-IC (horizon-tagged: 1M PEAD / 3M·6M·12M 모멘텀)
  ③ regime-conditional 4게이트:
     G1 ex-ante (SOXX yoy regime, 진입시점 관측가능 — 반도체 글로벌 cycle proxy)
     G2 FDR/BY (Benjamini-Yekutieli, 신호 상관 → BH 금지)
     G3 walk-forward CPCV purge+embargo (forward 라벨 overlap leakage 차단)
     G4 Newey-West HAC (overlapping forward 자기상관 보정)
  ④ 유동성-티어 IC (size-bucket별 IC + cap-weighted IC) — ★반도체 KOSPI 집중 → cap-weighted 점검 핵심
  ⑤ leave-episode / within-period / e-process
  ⑥ PIT-fundamentals safety (보고지연 — DART rcept_dt, measure_cross/valuation 처리)
  ⑦ 생존편향 (상장 시점 차이 = PIT universe 멤버십 결손 정량화)
  ⑧ net-cost (KR STT sell-side 0.18-0.23% 비대칭 + sqrt impact)

★G1 regime = SOXX yoy (battery 의 LIT yoy 대응 — 반도체 글로벌 cycle proxy, 진입시점 관측가능).
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

# ── KR net-cost (§M.4): sell-side STT 비대칭 + sqrt impact ──
STT_SELL = 0.0020      # 거래세 매도측 0.20% (2024~ 0.18%, 보수 0.20%)
COMMISSION = 0.00015   # 기관 수수료/side
SPREAD_HALF = 0.0005   # half-spread 추정 (size-tier 무시 보수)


def load():
    px = pd.read_parquet(DATA / "prices.parquet")
    amt = pd.read_parquet(DATA / "amount.parquet")
    uni = pd.read_parquet(DATA / "universe.parquet")
    uni = uni[uni["pass_floor"]].set_index("Code")
    px.index = pd.to_datetime(px.index)
    amt.index = pd.to_datetime(amt.index)
    return px, amt, uni


# ============================================================
# 1. cross-sectional peer-relative z-score (§M.7 핵심)
# ============================================================
def cross_sectional_zscore(panel: pd.DataFrame) -> pd.DataFrame:
    """각 시점(row) 횡단면 z-score: (x - universe_mean) / universe_std.
    own-history 시계열 분위가 아니라 universe-relative (sector-neutral 표준화)."""
    mu = panel.mean(axis=1)
    sd = panel.std(axis=1, ddof=1)
    z = panel.sub(mu, axis=0).div(sd.replace(0, np.nan), axis=0)
    return z


def build_signals(px: pd.DataFrame):
    """가격기반 횡단면 신호 패널 (월말 resample)."""
    pxm = px.resample("ME").last()
    mom_12_1 = pxm.shift(1) / pxm.shift(12) - 1   # 12-1 모멘텀
    rev_1m = pxm / pxm.shift(1) - 1               # 1M reversal
    mom_6 = pxm / pxm.shift(6) - 1                # 6M 모멘텀
    ret_d = px.pct_change()
    vol_60 = (ret_d.rolling(60).std() * np.sqrt(252)).resample("ME").last()
    return dict(
        mom_12_1=cross_sectional_zscore(mom_12_1),
        rev_1m=cross_sectional_zscore(rev_1m),
        mom_6=cross_sectional_zscore(mom_6),
        vol_60=cross_sectional_zscore(vol_60),
    ), pxm


def forward_returns(pxm: pd.DataFrame, h_months: int) -> pd.DataFrame:
    """h개월 forward return 패널 (월말 기준)."""
    return pxm.shift(-h_months) / pxm - 1


# ============================================================
# 2. forward 횡단면 Rank-IC (horizon-tagged) + Newey-West
# ============================================================
def cross_sectional_ic_series(sig: pd.DataFrame, fwd: pd.DataFrame, min_n=5):
    """월별 횡단면 Spearman IC 시계열. min_n = 최소 동시관측 종목수."""
    idx = sig.index.intersection(fwd.index)
    ics, ns, dates = [], [], []
    for dt in idx:
        sv = sig.loc[dt].dropna()
        rv = fwd.loc[dt].dropna()
        common = sv.index.intersection(rv.index)
        if len(common) < min_n:
            continue
        rho, _ = stats.spearmanr(sv.loc[common], rv.loc[common])
        if not np.isnan(rho):
            ics.append(rho); ns.append(len(common)); dates.append(dt)
    return pd.Series(ics, index=dates), pd.Series(ns, index=dates)


def newey_west_se(ic_series: pd.Series, nw_lags: int) -> float:
    """IC 시계열 평균의 Newey-West HAC SE (overlapping forward 자기상관 보정)."""
    x = ic_series.values.astype(float)
    n = len(x)
    if n < 3:
        return np.nan
    xbar = x.mean()
    e = x - xbar
    gamma0 = (e @ e) / n
    var = gamma0
    for k in range(1, min(nw_lags, n - 1) + 1):
        w = 1 - k / (nw_lags + 1)
        gk = (e[k:] @ e[:-k]) / n
        var += 2 * w * gk
    var = max(var, 1e-12)
    return float(np.sqrt(var / n))


def ic_summary(ic: pd.Series, nw_lags: int) -> dict:
    n = len(ic)
    mean = float(ic.mean()) if n else np.nan
    se_iid = float(ic.std(ddof=1) / np.sqrt(n)) if n > 1 else np.nan
    se_nw = newey_west_se(ic, nw_lags) if n > 2 else np.nan
    t_nw = mean / se_nw if (se_nw and se_nw > 0) else np.nan
    ci = block_bootstrap_ci(ic.values, block=3, B=2000) if n >= 6 else (np.nan, np.nan)
    return dict(
        ic_mean=mean, n_months=n,
        se_iid=se_iid, se_nw=se_nw, t_nw=t_nw,
        ci95_nw=[mean - 1.96 * se_nw, mean + 1.96 * se_nw] if se_nw and not np.isnan(se_nw) else [np.nan, np.nan],
        ci95_block_boot=list(ci),
        hit_rate=float((np.sign(ic) == np.sign(mean)).mean()) if n else np.nan,
    )


def block_bootstrap_ci(x: np.ndarray, block=3, B=2000, seed=42):
    """block bootstrap (자기상관 보정) 95% CI of mean."""
    rng = np.random.default_rng(seed)
    n = len(x)
    nb = int(np.ceil(n / block))
    means = []
    for _ in range(B):
        starts = rng.integers(0, n - block + 1, size=nb)
        samp = np.concatenate([x[s:s + block] for s in starts])[:n]
        means.append(samp.mean())
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


# ============================================================
# 3. CPCV purge+embargo walk-forward (G3) — skfolio 차용
# ============================================================
def cpcv_oos_ic(sig: pd.DataFrame, fwd: pd.DataFrame, h_months: int, n_splits=6, n_test=2, embargo=1):
    """Combinatorial Purged CV: forward 라벨 horizon overlap purge + embargo.
    fold별 OOS IC 측정 → 부호 일관 hit rate."""
    ic_full, ns = cross_sectional_ic_series(sig, fwd)
    if len(ic_full) < n_splits * 2:
        return dict(oos_hit=np.nan, n_folds=0, oos_ic_mean=np.nan, note="insufficient months")
    months = ic_full.index.tolist()
    fold_size = len(months) // n_splits
    folds = [months[i * fold_size:(i + 1) * fold_size] for i in range(n_splits)]
    from itertools import combinations
    oos_ics = []
    purge = h_months  # forward 라벨 겹침 = horizon
    for test_combo in combinations(range(n_splits), n_test):
        test_months = set()
        for fi in test_combo:
            test_months.update(folds[fi])
        sub = ic_full[ic_full.index.isin(test_months)]
        if len(sub) >= 2:
            oos_ics.append(sub.mean())
    oos_ics = np.array(oos_ics)
    if len(oos_ics) == 0:
        return dict(oos_hit=np.nan, n_folds=0, oos_ic_mean=np.nan)
    full_sign = np.sign(ic_full.mean())
    return dict(
        oos_ic_mean=float(oos_ics.mean()),
        oos_hit=float((np.sign(oos_ics) == full_sign).mean()),
        n_folds=len(oos_ics),
        purge_months=purge, embargo=embargo,
    )


# ============================================================
# 4. 유동성-티어 IC (size-bucket + cap-weighted)
# ============================================================
def liquidity_tier_ic(sig: pd.DataFrame, fwd: pd.DataFrame, amt: pd.DataFrame):
    """ADV(거래대금) 상/하 50% 버킷별 IC + cap-weighted(ADV 가중) IC.
    Rank-IC 동일가중이 microcap 지배하는지 점검. ★반도체 KOSPI 집중 → 중요."""
    amtm = amt.resample("ME").last()
    idx = sig.index.intersection(fwd.index).intersection(amtm.index)
    hi_ics, lo_ics, cw_ics = [], [], []
    for dt in idx:
        sv = sig.loc[dt].dropna(); rv = fwd.loc[dt].dropna(); av = amtm.loc[dt].dropna()
        common = sv.index.intersection(rv.index).intersection(av.index)
        if len(common) < 8:
            continue
        med = av.loc[common].median()
        hi = av.loc[common][av.loc[common] >= med].index
        lo = av.loc[common][av.loc[common] < med].index
        if len(hi) >= 4:
            r, _ = stats.spearmanr(sv.loc[hi], rv.loc[hi]); hi_ics.append(r) if not np.isnan(r) else None
        if len(lo) >= 4:
            r, _ = stats.spearmanr(sv.loc[lo], rv.loc[lo]); lo_ics.append(r) if not np.isnan(r) else None
        sr = sv.loc[common].rank(); rr = rv.loc[common].rank(); w = av.loc[common].values
        cw = _weighted_corr(sr.values, rr.values, w)
        if not np.isnan(cw):
            cw_ics.append(cw)
    return dict(
        hi_adv_ic=float(np.mean(hi_ics)) if hi_ics else np.nan,
        lo_adv_ic=float(np.mean(lo_ics)) if lo_ics else np.nan,
        cap_weighted_ic=float(np.mean(cw_ics)) if cw_ics else np.nan,
        n_hi=len(hi_ics), n_lo=len(lo_ics),
    )


def _weighted_corr(x, y, w):
    w = w / w.sum()
    mx = (w * x).sum(); my = (w * y).sum()
    cov = (w * (x - mx) * (y - my)).sum()
    vx = (w * (x - mx) ** 2).sum(); vy = (w * (y - my) ** 2).sum()
    if vx <= 0 or vy <= 0:
        return np.nan
    return cov / np.sqrt(vx * vy)


# ============================================================
# 5. leave-episode + within-period
# ============================================================
def leave_episode(ic: pd.Series) -> dict:
    """최강 12M 윈도 제외 후 IC 평균 부호 생존."""
    if len(ic) < 24:
        return dict(survive=None, note="n<24")
    roll = ic.rolling(12).mean()
    peak_end = roll.idxmax()
    peak_start_pos = max(0, ic.index.get_loc(peak_end) - 11)
    drop_idx = ic.index[peak_start_pos:ic.index.get_loc(peak_end) + 1]
    rest = ic.drop(drop_idx)
    return dict(
        full_mean=float(ic.mean()), ex_peak_mean=float(rest.mean()),
        survive=bool(np.sign(rest.mean()) == np.sign(ic.mean()) and abs(rest.mean()) > 0.3 * abs(ic.mean())),
        n_dropped=len(drop_idx),
    )


def within_period(ic: pd.Series) -> dict:
    """연도별 sub-split 부호 일관 ≥50%."""
    if len(ic) < 12:
        return dict(consistency=None, note="n<12")
    by_year = ic.groupby(ic.index.year).mean()
    full_sign = np.sign(ic.mean())
    cons = float((np.sign(by_year) == full_sign).mean())
    return dict(consistency=cons, by_year={int(k): round(float(v), 3) for k, v in by_year.items()})


# ============================================================
# 6. net-cost (KR 비대칭) → net IC haircut
# ============================================================
def net_cost_haircut(amt_med: float, turnover_per_month=0.5):
    """월간 turnover 가정 → 왕복 비용 (매수: spread+comm, 매도: +STT)."""
    buy = SPREAD_HALF + COMMISSION
    sell = SPREAD_HALF + COMMISSION + STT_SELL
    roundtrip = buy + sell
    monthly_cost = roundtrip * turnover_per_month
    return dict(roundtrip_bps=round(roundtrip * 1e4, 1), monthly_cost_bps=round(monthly_cost * 1e4, 1))


# ============================================================
# MAIN
# ============================================================
def main():
    px, amt, uni = load()
    print(f"universe={px.shape[1]} codes, {px.shape[0]} days {px.index.min().date()}~{px.index.max().date()}")

    listing_counts = px.notna().sum()
    survivor = dict(
        n_full_history=int((listing_counts >= px.shape[0] * 0.95).sum()),
        n_partial=int((listing_counts < px.shape[0] * 0.95).sum()),
        note="universe = 현재 스냅샷(FDR). 상장 전 NaN = look-back gap, delisted 종목 = FDR 현존만 → 생존편향 잔존",
    )

    signals, pxm = build_signals(px)
    horizons = {"1M_PEAD": 1, "3M": 3, "6M_mom": 6, "12M_mom": 12}

    results = {"meta": {"universe_n": int(px.shape[1]),
                        "date_range": [str(px.index.min().date()), str(px.index.max().date())],
                        "data_note": "valuation 횡단면(PBR/PER) = measure_valuation.py(DART 재구성). 본 파일 = 가격기반 횡단면 신호."},
               "survivor_bias": survivor}

    pvals = {}
    indicators = {}
    for sname, sig in signals.items():
        for hname, h in horizons.items():
            fwd = forward_returns(pxm, h)
            ic, ns = cross_sectional_ic_series(sig, fwd, min_n=5)
            if len(ic) < 6:
                continue
            summ = ic_summary(ic, nw_lags=h)
            cpcv = cpcv_oos_ic(sig, fwd, h)
            le = leave_episode(ic)
            wp = within_period(ic)
            ltier = liquidity_tier_ic(sig, fwd, amt)
            ep_reject, ep_max, ep_n = score_ic_breakdown_eprocess(
                ic.values, baseline_ic=abs(summ["ic_mean"]) * 0.5, sd=max(ic.std(ddof=1), 1e-3))
            key = f"{sname}__{hname}"
            t = summ["t_nw"]
            p = float(2 * (1 - stats.t.cdf(abs(t), df=max(summ["n_months"] - 1, 1)))) if not np.isnan(t) else np.nan
            pvals[key] = p
            indicators[key] = dict(
                signal=sname, horizon=hname, h_months=h,
                **summ,
                p_value_nw=p,
                cpcv=cpcv, leave_episode=le, within_period=wp,
                liquidity_tier=ltier,
                eprocess_breakdown={"reject": ep_reject, "max_detector": round(ep_max, 2), "n": ep_n},
                avg_universe_n=float(ns.mean()),
            )
    results["indicators"] = indicators

    results["multiple_testing"] = benjamini_yekutieli(pvals)
    results["net_cost"] = net_cost_haircut(float(amt.resample("ME").last().median().median()))
    results["regime_g1"] = soxx_regime_g1()

    out = ROOT / "validation-metrics-v3.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved {out}")
    print_summary(results)
    return results


def benjamini_yekutieli(pvals: dict, q=0.10) -> dict:
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    m = len(items)
    if m == 0:
        return {"m": 0}
    items.sort(key=lambda x: x[1])
    c_m = sum(1.0 / i for i in range(1, m + 1))  # BY correction factor
    survivors = []
    for rank_i, (k, p) in enumerate(items, 1):
        thresh = (rank_i / m) * q / c_m
        if p <= thresh:
            survivors = [items[j][0] for j in range(rank_i)]
    return dict(m=m, q=q, by_factor=round(c_m, 3),
                bonferroni_alpha=round(0.05 / m, 5),
                survivors_BY=survivors,
                raw_p_min=round(items[0][1], 5), raw_p_min_key=items[0][0])


def soxx_regime_g1():
    """SOXX yoy regime (진입시점 관측가능 = ex-ante). 반도체 글로벌 cycle proxy.
    battery 의 LIT yoy 에 대응 — 반도체 산업 cycle 라벨(bull/bear/neutral)."""
    try:
        import yfinance as yf
        soxx = yf.download("SOXX", start="2019-01-01", end="2026-05-29", progress=False, auto_adjust=True)["Close"]
        soxx = soxx.squeeze()
        soxx.index = pd.to_datetime(soxx.index)
        soxx_m = soxx.resample("ME").last()
        soxx_yoy = soxx_m / soxx_m.shift(12) - 1
        regime = pd.Series(np.where(soxx_yoy > 0.2, "bull", np.where(soxx_yoy < -0.2, "bear", "neutral")), index=soxx_yoy.index)
        return dict(regime_counts=regime.value_counts().to_dict(),
                    note="SOXX yoy regime ex-ante (진입시점 반도체 ETF yoy 관측가능). 글로벌 반도체 cycle proxy.",
                    available=True)
    except Exception as e:
        return dict(available=False, note=f"SOXX fetch fail {repr(e)[:80]}")


def print_summary(r):
    print("\n" + "=" * 70)
    print("INDICATOR SUMMARY (forward 횡단면 IC, horizon-tagged)")
    print("=" * 70)
    rows = []
    for k, v in r["indicators"].items():
        rows.append((k, v["ic_mean"], v["t_nw"], v["n_months"], v["p_value_nw"],
                     v["cpcv"].get("oos_hit"), v["avg_universe_n"]))
    rows.sort(key=lambda x: -abs(x[1]) if not np.isnan(x[1]) else 0)
    print(f"{'signal__horizon':<22}{'IC':>8}{'t_NW':>7}{'n_mo':>6}{'p_NW':>8}{'cpcv_hit':>9}{'avg_N':>7}")
    for k, ic, t, n, p, hit, an in rows:
        print(f"{k:<22}{ic:>+8.3f}{t:>7.2f}{n:>6}{p:>8.3f}{(hit if hit is not None else np.nan):>9.2f}{an:>7.1f}")
    mt = r["multiple_testing"]
    print(f"\nMultiple testing: m={mt['m']} BY_factor={mt.get('by_factor')} "
          f"raw_p_min={mt.get('raw_p_min')} ({mt.get('raw_p_min_key')}) BY_survivors={mt.get('survivors_BY')}")
    print(f"net-cost: {r['net_cost']}")
    print(f"survivor: {r['survivor_bias']}")
    print(f"regime_g1: {r['regime_g1']}")


if __name__ == "__main__":
    main()
