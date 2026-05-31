"""
r4_carry_verify.py — R4 carry 학설 ↔ 실측 검증 (small-N rigor)
session: btn-GCP, ckpt: ckpt-202605310200, date: 2026-05-31

목적:
  R4 carry 5 ref 의 학설/event 실측 검증.
  AMT/CCI primary 는 r4-carry-verify.md §1/§2 박제 (10-K text grep).
  본 script = §3/§4/§5 학설 ↔ 실측 (yfinance + FRED public).

검증:
  - §3.2 (Beracha-Hardin 2019 재환각 → broader literature): REIT-CPI hedge corr
  - §4.2 (Ling-Naranjo 1997): VNQ vs economic factors (term spread, default spread, IP, CPI yoy)
  - §5.2 (Ling-Naranjo 1999): VNQ vs ^GSPC monthly corr regime-conditional

small-N rigor (~/.claude/rules/small-n-statistical-rigor.md + empirical-claim-presentation.md §1):
  - n / p 명기
  - Newey-West HAC SE
  - block bootstrap (block_size = 12 month, autocorr 보정)
  - Bonferroni 보정 (m=4 비교)
  - hedge 어휘 적용 (단정 금지)
  - spec ↔ code 1:1 verify

D PIT (lookahead 회피):
  - FRED CPIAUCSL = latest revised (true first-release vintage ALFRED TODO, PIT partial caveat)
  - 가격 = monthly close (익월 시작 진입 가능)

I 생존편향 caveat:
  - VNQ = REIT ETF basket (시가 가중, 상폐 종목 자동 제외 단 ETF index methodology) — partial 생존편향
  - ^GSPC = S&P500 index
  - AMT/CCI = 2026 현재 생존 종목 (event-study 단일 종목)

5 금지:
  1. 점추정 prior 박제 금지 — 분포 + CI + hedge
  2. 합성 데이터 금지 — fetch 실패 = raise
  3. 자문 그대로 코드화 금지 — primary verify 후 채택
  4. Single-source 단정 금지 — multi-ref cross-verify
  5. Small-N 단정 금지 — n<30 단정 verdict 금지
"""

import sys
import json
import numpy as np
import pandas as pd
from scipy import stats
import yfinance as yf
import urllib.request
import urllib.error
from io import StringIO


SEED_NOTE = "no synthetic seed — fetch 실패 시 raise (5 금지 #2)"


def fetch_fred_csv(series_id: str) -> pd.Series:
    """FRED public CSV fetch. paywall X, fetch 실패 = raise (합성 금지)."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "research jsh8603@gmail.com"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"FRED fetch failed ({series_id}): {e}")
    df = pd.read_csv(StringIO(text))
    # FRED CSV columns: observation_date, {series_id}
    date_col = df.columns[0]
    val_col = df.columns[1] if df.columns[1].lower() != "value" else df.columns[1]
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col)
    s = pd.to_numeric(df[val_col], errors="coerce").rename(series_id)
    return s.dropna()


def newey_west_se(x: np.ndarray, y: np.ndarray, lag: int | None = None):
    """Newey-West HAC SE for Pearson correlation. Returns (corr, se_corr, t, p_two_sided)."""
    n = len(x)
    if lag is None:
        lag = int(np.floor(4 * (n / 100) ** (2 / 9)))
    lag = max(lag, 1)
    xm = x - x.mean()
    ym = y - y.mean()
    cov = (xm * ym).mean()
    var_x = (xm ** 2).mean()
    var_y = (ym ** 2).mean()
    r = cov / np.sqrt(var_x * var_y)
    # Bartlett-kernel HAC for product series
    u = xm * ym - cov
    gamma0 = (u ** 2).mean()
    var_hac = gamma0
    for l in range(1, lag + 1):
        w = 1 - l / (lag + 1)
        gamma_l = (u[l:] * u[:-l]).mean()
        var_hac += 2 * w * gamma_l
    se_cov = np.sqrt(max(var_hac / n, 1e-12))
    # delta method: se(r) ≈ se(cov) / sqrt(var_x var_y)
    se_r = se_cov / np.sqrt(var_x * var_y)
    t = r / se_r if se_r > 0 else np.nan
    p = 2 * (1 - stats.norm.cdf(abs(t))) if np.isfinite(t) else np.nan
    return r, se_r, t, p, lag


def block_bootstrap_corr(x: np.ndarray, y: np.ndarray, block_size: int = 12, n_iter: int = 1000, seed: int = 42):
    """Block bootstrap CI for Pearson correlation."""
    rng = np.random.default_rng(seed)
    n = len(x)
    n_blocks = int(np.ceil(n / block_size))
    rs = []
    for _ in range(n_iter):
        starts = rng.integers(0, n - block_size + 1, size=n_blocks)
        idx = np.concatenate([np.arange(s, s + block_size) for s in starts])[:n]
        rs.append(np.corrcoef(x[idx], y[idx])[0, 1])
    rs = np.array(rs)
    ci_lo, ci_hi = np.quantile(rs, [0.025, 0.975])
    return float(np.mean(rs)), float(ci_lo), float(ci_hi)


def main():
    out = {"meta": {"session": "btn-GCP", "ckpt": "ckpt-202605310200", "date": "2026-05-31",
                    "rigor": "small-N: n+p+NW HAC+block bootstrap+Bonferroni",
                    "seed_note": SEED_NOTE}}

    # ===== Data fetch =====
    print("[fetch] yfinance VNQ + ^GSPC monthly...", flush=True)
    tickers = ["VNQ", "^GSPC", "AMT", "CCI"]
    px = yf.download(tickers, start="2004-09-01", end="2026-05-31", interval="1mo",
                     auto_adjust=True, progress=False)["Close"]
    if px.isna().all().any():
        raise RuntimeError(f"yfinance fetch failed for some ticker: {px.isna().all()}")
    px = px.dropna(how="any")
    ret = np.log(px).diff().dropna()
    print(f"[fetch] monthly returns: n={len(ret)}, range={ret.index.min().date()} ~ {ret.index.max().date()}", flush=True)

    print("[fetch] FRED public CSV (CPI, DGS10, DGS2, BAMLH0A0HYM2, INDPRO)...", flush=True)
    cpi = fetch_fred_csv("CPIAUCSL")
    dgs10 = fetch_fred_csv("DGS10")
    dgs2 = fetch_fred_csv("DGS2")
    hy_oas = fetch_fred_csv("BAMLH0A0HYM2")
    indpro = fetch_fred_csv("INDPRO")
    print(f"[fetch] FRED ok: CPI n={len(cpi)}, DGS10 n={len(dgs10)}, INDPRO n={len(indpro)}", flush=True)

    # CPI yoy (monthly)
    cpi_yoy = (cpi / cpi.shift(12) - 1).rename("cpi_yoy")
    # Term spread = DGS10 - DGS2 (monthly, last obs of month)
    dgs10_m = dgs10.resample("MS").last()
    dgs2_m = dgs2.resample("MS").last()
    term_spread = (dgs10_m - dgs2_m).rename("term_spread")
    # Default spread proxy = HY OAS (monthly avg)
    hy_oas_m = hy_oas.resample("MS").mean().rename("hy_oas")
    # IP yoy
    indpro_yoy = (indpro / indpro.shift(12) - 1).rename("indpro_yoy")
    # CPI yoy monthly
    cpi_yoy_m = cpi_yoy.resample("MS").last()

    # ===== §3.2 Beracha-Hardin 2019 재환각 → broader: REIT-CPI hedge corr =====
    # 학설 testable claim: VNQ monthly return vs CPI yoy (rolling 12m mean)
    # 학설 (Yobaccio 1995 / Glascock-Lu-So 2002): REIT-inflation NEGATIVE 또는 spurious
    vnq_ret = ret["VNQ"]
    vnq_ret.index = vnq_ret.index.to_period("M").to_timestamp()
    df3 = pd.concat([vnq_ret.rename("vnq"), cpi_yoy_m], axis=1).dropna()
    if len(df3) < 30:
        out["§3_reit_cpi_hedge"] = {"n": len(df3), "verdict": "INSUFFICIENT (n<30)"}
    else:
        r, se, t, p, lag = newey_west_se(df3["vnq"].values, df3["cpi_yoy"].values)
        b_mean, b_lo, b_hi = block_bootstrap_corr(df3["vnq"].values, df3["cpi_yoy"].values)
        out["§3_reit_cpi_hedge"] = {
            "claim": "REIT-CPI hedge (broader literature: Yobaccio 1995 / Glascock-Lu-So 2002 = NEGATIVE 또는 spurious)",
            "n": int(len(df3)),
            "pearson_r": float(r), "nw_se": float(se), "nw_t": float(t), "nw_p": float(p), "nw_lag": int(lag),
            "block_bootstrap_mean": b_mean, "ci_95_lo": b_lo, "ci_95_hi": b_hi,
            "verdict_raw": ("REJECT (REIT-inflation positive hedge 비유의)" if p > 0.05 or r < 0.1
                            else "PARTIAL (positive hedge weak)" if r < 0.3 else "CONFIRMED positive hedge"),
        }
        print(f"[§3.2] VNQ-CPI yoy: r={r:.3f}, NW p={p:.3f}, n={len(df3)}, block CI=[{b_lo:.3f}, {b_hi:.3f}]", flush=True)

    # ===== §4.2 Ling-Naranjo 1997: VNQ vs economic factors panel =====
    # claim: economic risk factors (term spread, default spread, IP growth, inflation) → CRE returns
    df4 = pd.concat([vnq_ret.rename("vnq"), term_spread, hy_oas_m, indpro_yoy, cpi_yoy_m], axis=1).dropna()
    if len(df4) < 30:
        out["§4_economic_risk_factors"] = {"n": len(df4), "verdict": "INSUFFICIENT (n<30)"}
    else:
        results = {}
        factors = ["term_spread", "hy_oas", "indpro_yoy", "cpi_yoy"]
        for f in factors:
            r, se, t, p, lag = newey_west_se(df4["vnq"].values, df4[f].values)
            b_mean, b_lo, b_hi = block_bootstrap_corr(df4["vnq"].values, df4[f].values)
            results[f] = {"r": float(r), "nw_p": float(p), "ci_95_lo": b_lo, "ci_95_hi": b_hi, "n": int(len(df4))}
        # Bonferroni 보정 (m=4)
        m = len(factors)
        alpha_bonf = 0.05 / m
        for f in factors:
            results[f]["bonferroni_alpha"] = alpha_bonf
            results[f]["bonferroni_survive"] = results[f]["nw_p"] < alpha_bonf
        out["§4_economic_risk_factors"] = {
            "claim": "Ling-Naranjo 1997 JREFE 14(3) — Economic Risk Factors → CRE Returns (term spread / default spread / IP / inflation)",
            "n": int(len(df4)),
            "factors": results,
            "bonferroni_m": m, "bonferroni_alpha": alpha_bonf,
        }
        for f in factors:
            r = results[f]
            print(f"[§4.2] VNQ-{f}: r={r['r']:.3f}, NW p={r['nw_p']:.3f}, Bonf-survive={r['bonferroni_survive']}", flush=True)

    # ===== §5.2 Ling-Naranjo 1999: REIT-stock integration regime-conditional =====
    # claim: VNQ-stock corr regime-conditional (high vol vs low vol regime)
    spx_ret = ret["^GSPC"]
    spx_ret.index = spx_ret.index.to_period("M").to_timestamp()
    df5 = pd.concat([vnq_ret.rename("vnq"), spx_ret.rename("spx")], axis=1).dropna()
    if len(df5) < 30:
        out["§5_reit_stock_integration"] = {"n": len(df5), "verdict": "INSUFFICIENT (n<30)"}
    else:
        # full sample
        r_full, se_full, t_full, p_full, lag_full = newey_west_se(df5["vnq"].values, df5["spx"].values)
        b_mean, b_lo, b_hi = block_bootstrap_corr(df5["vnq"].values, df5["spx"].values)
        # regime split by VNQ rolling 12m vol
        vol12 = df5["vnq"].rolling(12).std()
        med_vol = vol12.dropna().median()
        high_vol_mask = (vol12 > med_vol).fillna(False)
        df5_high = df5[high_vol_mask]
        df5_low = df5[~high_vol_mask & vol12.notna()]
        regime_results = {}
        for label, sub in [("full", df5), ("high_vol", df5_high), ("low_vol", df5_low)]:
            if len(sub) < 20:
                regime_results[label] = {"n": len(sub), "verdict": "INSUFFICIENT"}
                continue
            r, se, t, p, lag = newey_west_se(sub["vnq"].values, sub["spx"].values)
            bm, bl, bh = block_bootstrap_corr(sub["vnq"].values, sub["spx"].values)
            regime_results[label] = {"r": float(r), "nw_p": float(p), "ci_95_lo": bl, "ci_95_hi": bh, "n": int(len(sub))}
        out["§5_reit_stock_integration"] = {
            "claim": "Ling-Naranjo 1999 RealEstateEconomics 27(3) — REIT-stock market integration regime-conditional",
            "regime_results": regime_results,
            "regime_split": "VNQ rolling 12m vol > median (high) vs <= median (low)",
        }
        for label, r in regime_results.items():
            if "r" in r:
                print(f"[§5.2] {label}: r={r['r']:.3f}, NW p={r['nw_p']:.3f}, n={r['n']}", flush=True)

    # ===== AMT VIL Goodwill event-study (Q3 2023 = announcement period) =====
    # event date proxy: 2023-09-30 (Q3 end, charge taken). 다만 announcement = Q3 earnings ~Oct 2023.
    # AMT monthly return 2023-10 (Q3 earnings release month) vs prior 6m mean.
    amt_ret = ret["AMT"]
    amt_ret.index = amt_ret.index.to_period("M").to_timestamp()
    if "2023-10-01" in amt_ret.index.strftime("%Y-%m-%d").tolist():
        event_ret = amt_ret.loc["2023-10-01"]
        prior_window = amt_ret.loc["2023-04-01":"2023-09-01"]
        prior_mean = float(prior_window.mean())
        prior_std = float(prior_window.std())
        z = (event_ret - prior_mean) / prior_std if prior_std > 0 else np.nan
        out["§1_amt_event_study"] = {
            "claim": "AMT VIL Goodwill Impairment $322M (Q3 2023) announcement effect",
            "event_month": "2023-10",
            "event_return": float(event_ret),
            "prior_6m_mean": prior_mean,
            "prior_6m_std": prior_std,
            "z_score": float(z) if np.isfinite(z) else None,
            "n_event": 1,
            "verdict_raw": "TENTATIVE DIRECTIONAL (n=1 single event, prior 6m baseline) — single-event single-asset, hedge 어휘 강제",
        }
        print(f"[§1 AMT event] 2023-10 return={event_ret:.3f}, prior 6m mean={prior_mean:.3f}, z={z:.2f}", flush=True)

    # ===== CCI Sprint Cancellations event-study (2023 Q4 / FY 2024 earnings) =====
    cci_ret = ret["CCI"]
    cci_ret.index = cci_ret.index.to_period("M").to_timestamp()
    if "2024-01-01" in cci_ret.index.strftime("%Y-%m-%d").tolist():
        event_ret = cci_ret.loc["2024-01-01"]
        prior_window = cci_ret.loc["2023-07-01":"2023-12-01"]
        prior_mean = float(prior_window.mean())
        prior_std = float(prior_window.std())
        z = (event_ret - prior_mean) / prior_std if prior_std > 0 else np.nan
        out["§2_cci_event_study"] = {
            "claim": "CCI Sprint Cancellations $250M (2023 FY)+$235M (2025 guide) announcement",
            "event_month": "2024-01 (Q4 2023 earnings release)",
            "event_return": float(event_ret),
            "prior_6m_mean": prior_mean,
            "prior_6m_std": prior_std,
            "z_score": float(z) if np.isfinite(z) else None,
            "n_event": 1,
            "verdict_raw": "TENTATIVE DIRECTIONAL (n=1 single event, single-asset) — hedge 강제",
        }
        print(f"[§2 CCI event] 2024-01 return={event_ret:.3f}, prior 6m mean={prior_mean:.3f}, z={z:.2f}", flush=True)

    # ===== Summary =====
    print("[summary] R4 carry 실측 verify 완료. small-N rigor: hedge 어휘 강제 + Bonferroni + block bootstrap CI.", flush=True)
    print(json.dumps(out, indent=2, default=str), flush=True)
    return out


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}", flush=True)
        raise
