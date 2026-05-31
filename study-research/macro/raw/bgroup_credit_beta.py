"""bgroup_credit_beta.py — B(c) credit factor β per sleeve (OOS, audit-ready).

목적: factor_betas_seed.FACTORS 의 'credit' 칸(현재 전 sleeve None=HOLD)을 채울 표준화
      contemporaneous β 를 sleeve 별 실측. credit factor shock = Δ(HY OAS).

★데이터 coverage(정직 명시 — small-N rigor §1.1):
  - HY OAS (BAMLH0A0HYM2): 2023-05-30~2026-05-28 (~750 거래일, ~36개월). ⚠️위기표본 부재
    (2008 GFC / 2020 COVID / 2022 금리쇼크 credit 확대 모두 윈도우 밖) → tail credit β 미관측.
  - BAA10Y (Moody's BAA - 10y, IG credit spread): 1986~2026 (n~10500). ★robustness: 위기 포함.
    HY 대용은 아니나 credit 채널 동형 + regime 변동(GFC/COVID) 관측 가능 → regime-conditional β.

sleeve 수익률(실측):
  - sector ETF (eq_us_cyclical/defensive sector_etf_close.csv): XLB XLE XLF XLI XLP XLU XLV XLY SPY
    2000-01~2026-05. 합성 sleeve: cyclical={XLB,XLI,XLY,XLF,XLE} / defensive_pure={XLP,XLU,XLV}.
  - eq_intl (world/em_broad/dm_exus, 2021-06~): credit β 보조.
  - reit(VNQ)·commodity(DBC): ⛔데이터 공백 → INSUFFICIENT(collector 필요), 측정 skip.

방법(audit 12축 정합):
  - 표준화 β: z(ret) ~ z(ΔHYOAS). Newey-West HAC SE(L=10) → t-stat (axis B/L 중첩윈도우 보정).
  - block bootstrap CI(block=5, B=5000): IID 가정 회피(axis L).
  - Bonferroni: N sleeve 동시검정 보정(axis K 다중검정).
  - walk-forward OOS: train 60% → test 40% β 부호/크기 안정성(axis D).
  - regime-conditional(BAA10Y): crisis(상위10% ΔBAA 변동월) vs normal β (tail-correlation, axis L).
  - 시도횟수 공시(axis K): sleeve 수 × spread 2종 = 검정 횟수 명기.
  - ⛔James-Stein 점추정 박제 금지(factor_betas_seed 가 수축) — 본 산출 = (β,SE,t,n,tier) 분포.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import statsmodels.api as sm
from pathlib import Path

RNG = np.random.default_rng(20260531)
SR = Path("study-research")
CY_FRED = SR / "eq_us_cyclical/raw/fred"
ETF = SR / "eq_us_cyclical/raw/yfinance/sector_etf_close.csv"


def load_fred(path: Path) -> pd.Series:
    df = pd.read_csv(path); df.columns = ["date", "v"]
    df["date"] = pd.to_datetime(df["date"])
    s = pd.to_numeric(df["v"], errors="coerce"); s.index = df["date"]
    return s.dropna()


def load_etf() -> pd.DataFrame:
    df = pd.read_csv(ETF)
    df["Date"] = pd.to_datetime(df["Date"]); df = df.set_index("Date")
    return df.apply(pd.to_numeric, errors="coerce")


def hac_beta(y: np.ndarray, x: np.ndarray, L: int = 10):
    """z(y) ~ z(x) 표준화 β + Newey-West HAC t. 반환 (beta, se, t, n)."""
    yz = (y - y.mean()) / y.std(ddof=1)
    xz = (x - x.mean()) / x.std(ddof=1)
    X = sm.add_constant(xz)
    res = sm.OLS(yz, X).fit(cov_type="HAC", cov_kwds={"maxlags": L})
    return float(res.params[1]), float(res.bse[1]), float(res.tvalues[1]), len(y)


def block_bootstrap_ci(y, x, block=5, B=5000):
    """block bootstrap 표준화 β 95% CI (자기상관 보정)."""
    n = len(y); nb = int(np.ceil(n / block))
    yz = (y - y.mean()) / y.std(ddof=1); xz = (x - x.mean()) / x.std(ddof=1)
    betas = np.empty(B)
    starts_pool = np.arange(0, n - block + 1)
    for b in range(B):
        starts = RNG.choice(starts_pool, size=nb, replace=True)
        idx = np.concatenate([np.arange(s, s + block) for s in starts])[:n]
        yy, xx = yz[idx], xz[idx]
        xx_c = xx - xx.mean()
        denom = float(xx_c @ xx_c)
        betas[b] = float(xx_c @ (yy - yy.mean())) / denom if denom > 0 else np.nan
    betas = betas[~np.isnan(betas)]
    return float(np.percentile(betas, 2.5)), float(np.percentile(betas, 97.5))


def measure(name, ret: pd.Series, dspread: pd.Series, L=10, walk=True):
    j = pd.concat({"r": ret, "d": dspread}, axis=1).dropna()
    if len(j) < 40:
        return None
    y, x = j["r"].values, j["d"].values
    beta, se, t, n = hac_beta(y, x, L)
    lo, hi = block_bootstrap_ci(y, x)
    out = dict(name=name, beta=beta, se=se, t=t, n=n, ci=(lo, hi),
               cov=(j.index.min().date().isoformat(), j.index.max().date().isoformat()))
    if walk and len(j) >= 100:
        cut = int(len(j) * 0.6)
        b_tr, _, t_tr, _ = hac_beta(y[:cut], x[:cut], L)
        b_te, _, t_te, _ = hac_beta(y[cut:], x[cut:], L)
        out["walk"] = (b_tr, t_tr, b_te, t_te)
    return out


def main():
    hyoas = load_fred(CY_FRED / "BAMLH0A0HYM2.csv")
    baa = load_fred(CY_FRED / "BAA10Y.csv")
    d_hy = hyoas.diff().dropna()          # Δ HY OAS (credit shock)
    d_baa = baa.diff().dropna()           # Δ BAA10Y (IG, crisis-inclusive)

    etf = load_etf()
    rets = np.log(etf).diff()             # daily log return
    sleeves = {
        "XLB": rets["XLB"], "XLE": rets["XLE"], "XLF": rets["XLF"], "XLI": rets["XLI"],
        "XLP": rets["XLP"], "XLU": rets["XLU"], "XLV": rets["XLV"], "XLY": rets["XLY"],
        "SPY(mkt)": rets["SPY"],
        "cyclical(XLB,I,Y,F,E)": rets[["XLB", "XLI", "XLY", "XLF", "XLE"]].mean(axis=1),
        "defensive_pure(XLP,U,V)": rets[["XLP", "XLU", "XLV"]].mean(axis=1),
    }
    N = len(sleeves)
    # Bonferroni: 검정 = N sleeve × 1 spread(primary HY). |z|=2 → α=0.05; α/N 임계 t.
    from scipy import stats
    t_bonf = stats.norm.ppf(1 - 0.05 / (2 * N))

    print("=" * 78)
    print("B(c) CREDIT β per sleeve — PRIMARY: Δ HY OAS (표준화 contemp β, NW-HAC L=10)")
    print(f"HY OAS raw coverage: {d_hy.index.min().date()} ~ {d_hy.index.max().date()}  "
          f"({len(d_hy)}d 원시, ~36개월) ⚠️위기표본 부재")
    print(f"※ 회귀 n = ETF수익률 ∩ ΔHYOAS inner-join 후 거래일수 (각 row 'n=NNN(joined)' 표기)")
    print(f"시도횟수 공시(K): {N} sleeve × 1 spread = {N} 검정. Bonferroni α/{N}: |t|>{t_bonf:.2f} 생존임계")
    print("=" * 78)
    rows = []
    for nm, r in sleeves.items():
        m = measure(nm, r, d_hy)
        if not m:
            print(f"{nm:26s} INSUFFICIENT"); continue
        surv = "✓BONF" if abs(m["t"]) > t_bonf else ("·raw5%" if abs(m["t"]) > 1.96 else "")
        w = m.get("walk")
        wtxt = f" | walk tr β={w[0]:+.2f}(t{w[1]:+.1f}) te β={w[2]:+.2f}(t{w[3]:+.1f})" if w else ""
        print(f"{nm:26s} β={m['beta']:+.3f} SE={m['se']:.3f} t={m['t']:+.2f} {surv:7s} "
              f"n={m['n']}(joined) CI[{m['ci'][0]:+.2f},{m['ci'][1]:+.2f}]{wtxt}")
        rows.append(m)

    print()
    print("=" * 78)
    print("ROBUSTNESS: Δ BAA10Y (IG credit, 위기포함 1986~) + regime-conditional β")
    print("=" * 78)
    # crisis = ΔBAA 절대변동 상위 10% 일 (credit stress 급변동 = 위기 proxy)
    thr = d_baa.abs().quantile(0.90)
    for nm in ["XLF", "cyclical(XLB,I,Y,F,E)", "defensive_pure(XLP,U,V)", "SPY(mkt)"]:
        r = sleeves[nm]
        m = measure(nm, r, d_baa, walk=False)
        if not m:
            continue
        # regime split
        j = pd.concat({"r": r, "d": d_baa}, axis=1).dropna()
        crisis = j[j["d"].abs() >= thr]; normal = j[j["d"].abs() < thr]
        bc, _, tc, nc = hac_beta(crisis["r"].values, crisis["d"].values, 10)
        bn, _, tn, nn = hac_beta(normal["r"].values, normal["d"].values, 10)
        print(f"{nm:26s} full β={m['beta']:+.3f} t={m['t']:+.2f} n={m['n']} "
              f"cov={m['cov'][0]}~{m['cov'][1]} | crisis β={bc:+.2f}(t{tc:+.1f},n{nc}) "
              f"normal β={bn:+.2f}(t{tn:+.1f},n{nn})")

    print()
    print("⛔ reit(VNQ)·commodity(DBC): 데이터 공백 → INSUFFICIENT (collector 필요, 측정 skip)")
    print("⛔ gold: macro_yahoo 2021-2024 vs HY OAS 2023-05+ overlap ~1.5yr → 별도 robustness 미흡, skip")


if __name__ == "__main__":
    main()
