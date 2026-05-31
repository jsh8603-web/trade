"""bgroup_regime_harness.py — B(a) dollar/oil OOS regime-eval harness.

가설(보류 2종 활성조건): dollar_broad(DTWEXBGS)/oil_wti 를 regime classifier JM feature 로 추가하면
  "분류 hit 실제 개선"되는가. ★tautology 우려(시장가격→regime 분류 순환참조, R1 FCI 경고 동형)는
  자동기각이 아니라 testable — OOS 로 검정.

조작적 정의: regime = 위험 상태. risk-off proxy = forward 21거래일 SPY 수익률(음=risk-off).
  "분류 hit 개선" = dollar/oil 신호가 forward risk 를 OOS 로 예측(Rank-IC)하는가. 게이트(axis B):
  OOS Rank-IC>0.03 AND |t|>2.0 (중첩윈도우 → Newey-West/block-bootstrap SE 강제, axis L).
  ⚠️contemporaneous(동시) 상관은 tautology(시장가격=risk 동시반영) → PREDICTIVE(forward) OOS 만 인정.

데이터:
  - DTWEXBGS (dollar broad, 2006~2026, 2008 GFC/2020 COVID 포함) — dollar 신호 장윈도우.
  - WTI (eq_intl/yahoo_cache/wti_oil, 2021-06~2026-05) — oil 신호 단윈도우(위기 부재 caveat).
  - SPY (sector_etf_close, 2000~2026) — risk-off target.
  - baseline macro feature(증분 검정용): real_rate Δ(DFII10), term_spread(T10Y2Y), VIX level.

방법:
  - 신호 = (a) level z-score (강달러/고유가 regime) (b) 20d momentum Δ.
  - walk-forward OOS: expanding window, 매 분기 재적합 후 다음 분기 OOS 예측 → 전 OOS 구간 Rank-IC.
  - 중첩 21d forward → block bootstrap(block=21) Rank-IC CI + NW-HAC t (autocorr 보정).
  - 증분: baseline-only vs baseline+dollar/oil OOS Spearman IC 비교(순수 증분가치).
  - 시도횟수 공시(K): 신호 2종(level/mom) × 자산 2종(dollar/oil) × target 1 = 4 검정.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

RNG = np.random.default_rng(20260531)
SR = Path("study-research")
DF_FRED = SR / "eq_us_defensive/raw/fred"
CY_FRED = SR / "eq_us_cyclical/raw/fred"
ETF = SR / "eq_us_cyclical/raw/yfinance/sector_etf_close.csv"
INTL = SR / "eq_intl/raw/yahoo_cache"

FWD = 21  # forward window (거래일)


def load_fred(path: Path) -> pd.Series:
    df = pd.read_csv(path); df.columns = ["date", "v"]
    df["date"] = pd.to_datetime(df["date"])
    s = pd.to_numeric(df["v"], errors="coerce"); s.index = df["date"]
    return s.dropna()


def load_intl(name) -> pd.Series:
    df = pd.read_csv(INTL / f"{name}.csv"); df.columns = ["date", "v"]
    df["date"] = pd.to_datetime(df["date"])
    s = pd.to_numeric(df["v"], errors="coerce"); s.index = df["date"]
    return s.dropna()


def spy() -> pd.Series:
    df = pd.read_csv(ETF); df["Date"] = pd.to_datetime(df["Date"])
    s = pd.to_numeric(df.set_index("Date")["SPY"], errors="coerce").dropna()
    return s


def block_boot_ic_ci(sig, fwd, block=21, B=3000):
    """block bootstrap Spearman IC 95% CI (중첩윈도우 autocorr 보정)."""
    n = len(sig); nb = int(np.ceil(n / block)); pool = np.arange(0, n - block + 1)
    ics = []
    for _ in range(B):
        starts = RNG.choice(pool, size=nb, replace=True)
        idx = np.concatenate([np.arange(s, s + block) for s in starts])[:n]
        ic = stats.spearmanr(sig[idx], fwd[idx]).statistic
        if not np.isnan(ic):
            ics.append(ic)
    return float(np.percentile(ics, 2.5)), float(np.percentile(ics, 97.5))


def nw_tstat_ic(sig, fwd, L=FWD):
    """Spearman IC 의 NW-HAC t: rank 변환 후 단순회귀 t (중첩 → maxlags=FWD)."""
    import statsmodels.api as sm
    rs = stats.rankdata(sig); rf = stats.rankdata(fwd)
    rs = (rs - rs.mean()) / rs.std(); rf = (rf - rf.mean()) / rf.std()
    res = sm.OLS(rf, sm.add_constant(rs)).fit(cov_type="HAC", cov_kwds={"maxlags": L})
    return float(res.params[1]), float(res.tvalues[1])


def walkforward_ic(sig: pd.Series, fwd: pd.Series, init_frac=0.4):
    """expanding-window OOS: 신호는 무적합(monotonic) 이므로 OOS = init 이후 전 구간 IC.
    (단순 신호라 fit 파라미터 없음 → walk-forward = OOS holdout IC + 부호 사전고정 검증)."""
    j = pd.concat({"s": sig, "f": fwd}, axis=1).dropna()
    n = len(j); cut = int(n * init_frac)
    # 부호 사전 고정: IS(첫 init) 부호 → OOS 동일부호 유지 검증
    is_ic = stats.spearmanr(j["s"].values[:cut], j["f"].values[:cut]).statistic
    oos_s, oos_f = j["s"].values[cut:], j["f"].values[cut:]
    oos_ic = stats.spearmanr(oos_s, oos_f).statistic
    b, t = nw_tstat_ic(oos_s, oos_f)
    lo, hi = block_boot_ic_ci(oos_s, oos_f)
    return dict(is_ic=is_ic, oos_ic=oos_ic, t=t, ci=(lo, hi), n_oos=len(oos_s),
                cov=(j.index[cut].date().isoformat(), j.index[-1].date().isoformat()))


def evaluate(label, raw: pd.Series, spy_px: pd.Series):
    lev = (raw - raw.rolling(252).mean()) / raw.rolling(252).std()  # level z (regime)
    mom = raw.pct_change(20)                                         # 20d momentum
    fwd = np.log(spy_px).diff().rolling(FWD).sum().shift(-FWD)       # forward 21d SPY ret
    # 부호 가설: 강달러/고유가 = risk-off 예고 → forward SPY 음 → IC<0 기대
    for signame, sg in [("level_z", lev), ("mom20", mom)]:
        r = walkforward_ic(sg, fwd)
        gate = "✓PASS" if (abs(r["oos_ic"]) > 0.03 and abs(r["t"]) > 2.0) else "✗FAIL"
        signflip = "" if np.sign(r["is_ic"]) == np.sign(r["oos_ic"]) else " ⚠️부호반전(IS↔OOS)"
        print(f"  {label}.{signame:8s} IS-IC={r['is_ic']:+.3f} → OOS-IC={r['oos_ic']:+.3f} "
              f"NW-t={r['t']:+.2f} CI[{r['ci'][0]:+.3f},{r['ci'][1]:+.3f}] "
              f"n_oos={r['n_oos']} {gate}{signflip}")


def incremental(spy_px: pd.Series, dollar: pd.Series, oil: pd.Series):
    """baseline(real_rate,term,VIX) vs +dollar/oil OOS Spearman IC 증분(다변량 신호 합성)."""
    import statsmodels.api as sm
    dfii = load_fred(DF_FRED / "DFII10.csv").diff()
    term = load_fred(CY_FRED / "T10Y2Y.csv")
    vix = load_intl("vix")
    fwd = np.log(spy_px).diff().rolling(FWD).sum().shift(-FWD)
    base = pd.concat({"d_real": dfii, "term": term, "vix": vix}, axis=1)
    full = pd.concat([base, pd.DataFrame({"dxy_mom": dollar.pct_change(20),
                                          "oil_mom": oil.pct_change(20)})], axis=1)
    def oos_ic(Xdf):
        j = pd.concat([Xdf, fwd.rename("f")], axis=1).dropna()
        n = len(j); cut = int(n * 0.5)
        Xtr = sm.add_constant(j.iloc[:cut, :-1]); ytr = j.iloc[:cut, -1]
        m = sm.OLS(ytr, Xtr).fit()
        Xte = sm.add_constant(j.iloc[cut:, :-1]); pred = m.predict(Xte)
        ic = stats.spearmanr(pred, j.iloc[cut:, -1]).statistic
        return ic, len(j) - cut, j.index[cut].date().isoformat(), j.index[-1].date().isoformat()
    ib, nb, c0, c1 = oos_ic(base)
    iff, nf, *_ = oos_ic(full)
    print(f"  [증분] baseline(real,term,vix) OOS-IC={ib:+.3f} (n={nb}, {c0}~{c1})")
    print(f"  [증분] +dxy/oil mom         OOS-IC={iff:+.3f} (n={nf})  Δ증분={iff-ib:+.3f}")


def main():
    spy_px = spy()
    dtwex = load_fred(DF_FRED / "DTWEXBGS.csv")
    wti = load_intl("wti_oil")
    print("=" * 78)
    print("B(a) dollar/oil OOS regime-eval — forward 21d SPY ret 예측 Rank-IC (walk-forward OOS)")
    print(f"게이트(axis B): |OOS Rank-IC|>0.03 AND |NW-t|>2.0. 시도횟수(K)=신호2×자산2=4 검정")
    print("부호가설: 강달러/고유가 regime → forward risk-off(SPY↓) → IC<0 기대")
    print("=" * 78)
    print(f"DOLLAR (DTWEXBGS, {dtwex.index.min().date()}~{dtwex.index.max().date()}, 2008/2020 위기포함):")
    evaluate("dxy", dtwex, spy_px)
    print(f"OIL (WTI, {wti.index.min().date()}~{wti.index.max().date()}, ⚠️위기부재 단윈도우):")
    evaluate("oil", wti, spy_px)
    print()
    print("증분 검정 (baseline macro 대비 dollar/oil 추가 OOS 가치):")
    incremental(spy_px, dtwex, wti)
    print()
    print("⛔ contemporaneous(동시) 상관은 tautology(시장가격=risk 동시) → 본 harness 는 PREDICTIVE 만 평가")


if __name__ == "__main__":
    main()
