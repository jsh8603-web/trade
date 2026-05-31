"""run_validations.py — bond_cash 2-3 단계 실데이터 시계열 검증.

데이터 소스 (✅ FRED API + yfinance, 합성 금지):
  - FRED (fredapi, key from D:/projects/Inv/.env):
      BAMLH0A0HYM2 (HY OAS, 1996-12~), T10Y2Y (10Y-2Y, 1976~), DFII10 (10Y TIPS, 2003~),
      DGS10 (10Y nominal, 1962~), DGS2 (2Y, 1976~), BAA10Y (IG spread, 1986~), FEDFUNDS, T5YIE
  - yfinance: TLT/IEF/SHY/BIL/SHV/HYG/LQD/TIP/SPY 일별 Close (Yahoo, ETF inception 부터)

검증 4건 (direction.md ②검증방향 + 가설 12개 중 핵심):
  V1. HY OAS 600bps event study  → forward 12-18M panel
  V2. Yield curve flip lead-time → forward 6/12/18M panel (1976~)
  V3. Cash Sharpe competitiveness → SHY/BIL vs SPY rolling 36M Sharpe
  V4. Bond return decomposition  → TLT return = -D·Δy + 0.5·C·(Δy)² + carry/252 regression

출력: stdout = 사람 읽는 요약. 4 분리 markdown 은 별도 스크립트가 파싱.
"""
from __future__ import annotations
import os, sys, json
from datetime import datetime
import numpy as np
import pandas as pd

sys.path.insert(0, "D:/projects/Inv")


# === 환경 로드 ===
def _load_env(path: str = "D:/projects/Inv/.env"):
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8").read().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


_load_env()
FRED_API_KEY = os.environ.get("FRED_API_KEY")
if not FRED_API_KEY:
    print("⚠️  FRED_API_KEY 없음 — FRED CSV endpoint(최근 3년)로 폴백 시도")


# === 데이터 fetcher ===
def fred_series(series_id: str, start: str = "1990-01-01") -> pd.Series:
    """fredapi 사용 시 full historical, 폴백은 CSV endpoint(최근만)."""
    if FRED_API_KEY:
        from fredapi import Fred
        f = Fred(api_key=FRED_API_KEY)
        s = f.get_series(series_id, observation_start=start)
        s.name = series_id
        return s.dropna()
    # 폴백
    import urllib.request
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    df = pd.read_csv(url)
    df["observation_date"] = pd.to_datetime(df["observation_date"])
    return df.set_index("observation_date")[series_id].astype(float).dropna()


def yf_close(ticker: str, start: str = "1990-01-01") -> pd.Series:
    import yfinance as yf
    t = yf.Ticker(ticker)
    h = t.history(start=start, auto_adjust=True, actions=False)
    if h.empty:
        return pd.Series(dtype=float, name=ticker)
    s = h["Close"]
    s.index = pd.to_datetime(s.index).tz_localize(None)
    s.name = ticker
    return s.astype(float)


# === V1. HY OAS 600bps event study ===
def v1_hy_oas_event_study():
    print("\n" + "=" * 78)
    print("V1. HY OAS 600bps Event Study (BAMLH0A0HYM2, 1996-12~)")
    print("=" * 78)

    hy = fred_series("BAMLH0A0HYM2", start="1996-12-01")
    hy = hy.resample("D").ffill().dropna()
    print(f"  HY OAS 데이터: n={len(hy)}, period={hy.index[0].date()} ~ {hy.index[-1].date()}")
    print(f"  분포: mean={hy.mean():.2f}, std={hy.std():.2f}, p50={hy.median():.2f}, p95={hy.quantile(0.95):.2f}, max={hy.max():.2f}")

    # 600bps 이상 진입 event 검출 (이전 < 600, 현재 >= 600)
    above = (hy >= 6.0)
    entries = above & ~above.shift(1, fill_value=False)
    entry_dates = hy.index[entries]
    print(f"\n  600bps 진입 event: {len(entry_dates)}건")
    for d in entry_dates:
        print(f"    {d.date()}  level={hy.loc[d]:.2f}%")

    # ETF forward return (HYG/TLT/IEF/SHY/BIL 가용)
    hyg = yf_close("HYG", start="2007-04-01")
    tlt = yf_close("TLT", start="2002-07-01")
    shy = yf_close("SHY", start="2002-07-01")
    bil = yf_close("BIL", start="2007-05-01")

    print(f"\n  ETF 가용: HYG n={len(hyg)} ({hyg.index[0].date() if len(hyg) else 'N/A'}~), TLT n={len(tlt)}, SHY n={len(shy)}, BIL n={len(bil)}")

    if len(entry_dates) == 0:
        print("  ⚠️ 진입 event 없음 — 600bps 미돌파")
        return {"event_dates": [], "panel": None}

    results = []
    for d in entry_dates:
        row = {"event_date": str(d.date()), "hy_oas_level": float(hy.loc[d])}
        for name, etf in [("hyg", hyg), ("tlt", tlt), ("shy", shy), ("bil", bil)]:
            if etf.empty or d > etf.index[-1]:
                row[f"{name}_12m_ret"] = None
                row[f"{name}_18m_ret"] = None
                continue
            try:
                p0 = etf.asof(d)
                p12 = etf.asof(d + pd.Timedelta(days=365))
                p18 = etf.asof(d + pd.Timedelta(days=548))
                row[f"{name}_12m_ret"] = float(p12 / p0 - 1) if pd.notna(p12) and pd.notna(p0) else None
                row[f"{name}_18m_ret"] = float(p18 / p0 - 1) if pd.notna(p18) and pd.notna(p0) else None
            except Exception:
                row[f"{name}_12m_ret"] = None
                row[f"{name}_18m_ret"] = None
        results.append(row)

    panel = pd.DataFrame(results)
    print("\n  Forward return panel (% 단위):")
    show = panel.copy()
    for c in show.columns:
        if c.endswith("_ret"):
            show[c] = show[c].apply(lambda x: f"{x*100:+.2f}%" if x is not None else "  N/A")
    print(show.to_string(index=False))

    print("\n  요약 통계 (event 평균):")
    for col in ["hyg_12m_ret", "tlt_12m_ret", "shy_12m_ret", "bil_12m_ret",
                "hyg_18m_ret", "tlt_18m_ret", "shy_18m_ret", "bil_18m_ret"]:
        vals = panel[col].dropna()
        if len(vals) == 0:
            continue
        print(f"    {col:<16} n={len(vals)}, mean={vals.mean()*100:+.2f}%, p50={vals.median()*100:+.2f}%, hit_pos={(vals>0).mean()*100:.0f}%")

    # bond - cash 스프레드 분석 (H6: HY OAS 600bps → bond-cash < 0 가설)
    print("\n  bond − cash spread (TLT − SHY) 가설 H6:")
    for hor in ["12m", "18m"]:
        b = panel[f"tlt_{hor}_ret"].dropna()
        c = panel[f"shy_{hor}_ret"].dropna()
        if len(b) > 0 and len(c) > 0:
            spread = (panel[f"tlt_{hor}_ret"] - panel[f"shy_{hor}_ret"]).dropna()
            print(f"    {hor}: n={len(spread)}, mean={spread.mean()*100:+.2f}%, p50={spread.median()*100:+.2f}%, negative_frac={(spread<0).mean()*100:.0f}%")

    return {"event_dates": [str(d.date()) for d in entry_dates], "panel": panel.to_dict("records")}


# === V2. Yield Curve flip lead-time ===
def v2_curve_flip_lead():
    print("\n" + "=" * 78)
    print("V2. Yield Curve Flip Lead-Time (T10Y2Y, 1976~)")
    print("=" * 78)

    yc = fred_series("T10Y2Y", start="1976-06-01")
    yc = yc.resample("D").ffill().dropna()
    print(f"  T10Y2Y: n={len(yc)}, period={yc.index[0].date()} ~ {yc.index[-1].date()}")

    # flip event: 부호 전환 — Inversion (>=0 → <0) 와 Steepening (<0 → >=0)
    sign = (yc < 0).astype(int)
    inversion_flip = (sign == 1) & (sign.shift(1, fill_value=0) == 0)
    steepening_flip = (sign == 0) & (sign.shift(1, fill_value=0) == 1)

    inv_dates = yc.index[inversion_flip]
    steep_dates = yc.index[steepening_flip]
    print(f"  Inversion entries (>=0 → <0): {len(inv_dates)}건")
    print(f"  Steepening exits (<0 → >=0): {len(steep_dates)}건")

    # NBER 침체 시작일 (가용 사이클): USREC (1=recession)
    rec = fred_series("USREC", start="1976-06-01").resample("D").ffill()
    rec_starts = rec.index[(rec == 1) & (rec.shift(1, fill_value=0) == 0)]
    print(f"  NBER recession starts: {len(rec_starts)}건  → {[d.strftime('%Y-%m') for d in rec_starts]}")

    # 각 inversion event 의 lead time = 다음 recession 까지 일수
    print("\n  Inversion → recession lead time (days):")
    leads = []
    for inv in inv_dates:
        following = [r for r in rec_starts if r > inv]
        if not following:
            print(f"    {inv.date()}  → 후속 recession 없음")
            continue
        lead = (following[0] - inv).days
        leads.append(lead)
        print(f"    {inv.date()}  → {following[0].date()}  = {lead}일 ({lead/7:.1f}주, {lead/30.4:.1f}월)")

    if leads:
        a = np.array(leads)
        print(f"\n  분포 통계 (n={len(a)}): mean={a.mean():.0f}일 ({a.mean()/7:.1f}주), median={np.median(a):.0f}일, IQR=[{np.percentile(a,25):.0f}, {np.percentile(a,75):.0f}]")
        print(f"  웹리서치 baseline: avg 48주, IQR 6-18개월 = [180, 540]일")
        within_iqr = ((a >= 180) & (a <= 540)).mean()
        print(f"  baseline IQR [180,540]일 내 비율: {within_iqr*100:.0f}% (n={len(a)})")

    # bull steepening event 후 TLT forward return
    tlt = yf_close("TLT", start="2002-07-01")
    if not tlt.empty:
        print("\n  Bull-steepening event 후 TLT forward return (TLT 가용 = 2002-07~):")
        for d in steep_dates:
            if d < tlt.index[0] or d > tlt.index[-1]:
                continue
            try:
                p0 = tlt.asof(d)
                p3 = tlt.asof(d + pd.Timedelta(days=90))
                p6 = tlt.asof(d + pd.Timedelta(days=180))
                p12 = tlt.asof(d + pd.Timedelta(days=365))
                r3 = (p3 / p0 - 1) * 100 if pd.notna(p3) else None
                r6 = (p6 / p0 - 1) * 100 if pd.notna(p6) else None
                r12 = (p12 / p0 - 1) * 100 if pd.notna(p12) else None
                rs = [f"{x:+.2f}%" if x is not None else "  N/A" for x in (r3, r6, r12)]
                print(f"    {d.date()}  3m={rs[0]}, 6m={rs[1]}, 12m={rs[2]}")
            except Exception:
                pass

    return {"inversion_dates": [str(d.date()) for d in inv_dates],
            "steepening_dates": [str(d.date()) for d in steep_dates],
            "lead_times_days": leads}


# === V3. Cash Sharpe vs SPY (Duffee 재현) ===
def v3_cash_sharpe():
    print("\n" + "=" * 78)
    print("V3. Cash Sharpe vs SPY (Duffee fact 재현)")
    print("=" * 78)

    spy = yf_close("SPY", start="2002-07-01")
    shy = yf_close("SHY", start="2002-07-01")
    bil = yf_close("BIL", start="2007-05-01")
    shv = yf_close("SHV", start="2007-01-01")

    if spy.empty or shy.empty:
        print("  ⚠️ SPY/SHY 부재 — skip")
        return {}

    # 일별 log return → 월별 합산
    def monthly_log_ret(s: pd.Series) -> pd.Series:
        lr = np.log(s).diff().dropna()
        return lr.resample("ME").sum().dropna()

    spy_m = monthly_log_ret(spy)
    shy_m = monthly_log_ret(shy)
    bil_m = monthly_log_ret(bil) if not bil.empty else pd.Series(dtype=float)
    shv_m = monthly_log_ret(shv) if not shv.empty else pd.Series(dtype=float)

    # cash basket = (SHY + BIL + SHV) / 3 (구간별 가용 평균)
    cash_m = pd.concat([shy_m, bil_m, shv_m], axis=1).mean(axis=1).dropna()
    print(f"  월별 return 기간: SPY n={len(spy_m)} ({spy_m.index[0].date()}~{spy_m.index[-1].date()})")
    print(f"                     cash n={len(cash_m)} (avg of SHY/BIL/SHV when available)")

    # full-sample Sharpe (월별, 연환산 X — Duffee monthly Sharpe)
    def sharpe_m(s: pd.Series) -> float:
        s = s.dropna()
        return float(s.mean() / s.std()) if s.std() > 0 else 0.0

    spy_s = sharpe_m(spy_m)
    cash_s = sharpe_m(cash_m)
    print(f"\n  Full-sample monthly Sharpe:")
    print(f"    SPY  : {spy_s:.4f}  (n={len(spy_m)})")
    print(f"    Cash : {cash_s:.4f}  (n={len(cash_m)})")
    print(f"    Cash − SPY = {cash_s - spy_s:+.4f}  → {'Cash Sharpe ≥ SPY (Duffee fact 지지)' if cash_s >= spy_s else 'Cash Sharpe < SPY (Duffee fact 미관측)'}")
    print(f"    ⚠️ Duffee 는 1976~2000 또는 더 긴 sample 기준. 우리 sample 은 2002+ (post-GFC + ZIRP 시기).")

    # rolling 36M Sharpe
    print("\n  Rolling 36M monthly Sharpe:")
    aligned = pd.concat([spy_m, cash_m], axis=1, keys=["spy", "cash"]).dropna()
    if len(aligned) > 36:
        roll_spy = aligned["spy"].rolling(36).apply(lambda x: x.mean() / x.std() if x.std() > 0 else 0)
        roll_cash = aligned["cash"].rolling(36).apply(lambda x: x.mean() / x.std() if x.std() > 0 else 0)
        win_cash = ((roll_cash > roll_spy) & roll_spy.notna()).sum()
        total = roll_spy.notna().sum()
        print(f"    Cash > SPY 비율: {win_cash}/{total} = {win_cash/total*100:.1f}%")
        # 마지막 36개월 window 결과
        last = aligned.iloc[-36:]
        last_spy_s = last["spy"].mean() / last["spy"].std() if last["spy"].std() > 0 else 0
        last_cash_s = last["cash"].mean() / last["cash"].std() if last["cash"].std() > 0 else 0
        print(f"    최근 36M window ({last.index[0].date()}~{last.index[-1].date()}):")
        print(f"      SPY  Sharpe = {last_spy_s:.4f}")
        print(f"      Cash Sharpe = {last_cash_s:.4f}")

    return {"spy_sharpe_monthly": spy_s, "cash_sharpe_monthly": cash_s,
            "diff": cash_s - spy_s, "sample_period": [str(spy_m.index[0].date()), str(spy_m.index[-1].date())]}


# === V4. Bond return decomposition ===
def v4_bond_decomposition():
    print("\n" + "=" * 78)
    print("V4. Bond Return Decomposition (TLT regression on Δy, Δy²)")
    print("=" * 78)

    tlt = yf_close("TLT", start="2003-01-01")
    ief = yf_close("IEF", start="2003-01-01")
    shy = yf_close("SHY", start="2003-01-01")
    dgs10 = fred_series("DGS10", start="2003-01-01")
    dgs2 = fred_series("DGS2", start="2003-01-01")

    if tlt.empty or dgs10.empty:
        print("  ⚠️ TLT 또는 DGS10 부재 — skip")
        return {}

    # 일별 log return + yield 일변화
    def daily_lr(s):
        return np.log(s).diff().dropna()

    df = pd.DataFrame({
        "tlt_lr": daily_lr(tlt),
        "ief_lr": daily_lr(ief),
        "shy_lr": daily_lr(shy),
        "dgs10": dgs10,
        "dgs2": dgs2,
    }).dropna()
    df["d_dgs10"] = df["dgs10"].diff()
    df["d_dgs10_sq"] = df["d_dgs10"] ** 2
    df["d_dgs2"] = df["dgs2"].diff()
    df = df.dropna()
    print(f"  기간: {df.index[0].date()} ~ {df.index[-1].date()}, n={len(df)}일")

    # OLS regression (manual): r_etf = α + β1·Δy + β2·Δy²
    def ols_3param(y, x1, x2):
        X = np.column_stack([np.ones(len(y)), x1, x2])
        beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        y_hat = X @ beta
        ss_res = ((y - y_hat) ** 2).sum()
        ss_tot = ((y - y.mean()) ** 2).sum()
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        # standard errors
        n, k = len(y), X.shape[1]
        sigma2 = ss_res / (n - k)
        cov = sigma2 * np.linalg.inv(X.T @ X)
        se = np.sqrt(np.diag(cov))
        t_stats = beta / se
        return {"alpha": beta[0], "beta1_d_y": beta[1], "beta2_d_y2": beta[2],
                "se_alpha": se[0], "se_beta1": se[1], "se_beta2": se[2],
                "t_alpha": t_stats[0], "t_beta1": t_stats[1], "t_beta2": t_stats[2],
                "r2": r2, "n": n}

    print("\n  TLT (long, D≈17): r = α + β1·Δy + β2·Δy²")
    res_tlt = ols_3param(df["tlt_lr"].values, df["d_dgs10"].values, df["d_dgs10_sq"].values)
    for k, v in res_tlt.items():
        print(f"    {k:<15} = {v:.6f}" if isinstance(v, float) else f"    {k:<15} = {v}")
    print(f"    → β1 implied duration = {-res_tlt['beta1_d_y']*100:.2f}년 (이론 ≈17)")

    print("\n  IEF (mid, D≈8):")
    res_ief = ols_3param(df["ief_lr"].values, df["d_dgs10"].values, df["d_dgs10_sq"].values)
    for k, v in res_ief.items():
        print(f"    {k:<15} = {v:.6f}" if isinstance(v, float) else f"    {k:<15} = {v}")
    print(f"    → β1 implied duration = {-res_ief['beta1_d_y']*100:.2f}년 (이론 ≈8)")

    print("\n  SHY (short, D≈2): SHY 는 DGS2 변동에 더 민감")
    res_shy = ols_3param(df["shy_lr"].values, df["d_dgs2"].values, (df["d_dgs2"]**2).values)
    for k, v in res_shy.items():
        print(f"    {k:<15} = {v:.6f}" if isinstance(v, float) else f"    {k:<15} = {v}")
    print(f"    → β1 implied duration (vs Δ DGS2) = {-res_shy['beta1_d_y']*100:.2f}년 (이론 ≈2)")

    # H1-B: convexity premium = E[0.5·C·(Δy)²] > 0
    # implied: β2 > 0 (양수 = positive convexity 회귀상 확인)
    print("\n  H1-B convexity premium (β2 sign):")
    for name, res in [("TLT", res_tlt), ("IEF", res_ief), ("SHY", res_shy)]:
        sig = "양수 (positive convexity ✅)" if res["beta2_d_y2"] > 0 else "음수 (이상)"
        t_sig = "유의" if abs(res["t_beta2"]) > 1.96 else "미유의"
        print(f"    {name}: β2 = {res['beta2_d_y2']:+.5f}  ({sig}, t={res['t_beta2']:.2f} {t_sig})")

    return {
        "tlt": res_tlt, "ief": res_ief, "shy": res_shy,
        "period": [str(df.index[0].date()), str(df.index[-1].date())],
    }


# === main ===
def main():
    print(f"\n실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"FRED_API_KEY: {'OK (full historical)' if FRED_API_KEY else 'MISSING (CSV polback ~3년)'}")
    print(f"데이터 정책: ⛔ 합성 금지, 실수집기 데이터만 (FRED + yfinance)")

    out = {}
    try:
        out["v1"] = v1_hy_oas_event_study()
    except Exception as e:
        print(f"\n[V1 ERROR] {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()
        out["v1"] = {"error": str(e)}

    try:
        out["v2"] = v2_curve_flip_lead()
    except Exception as e:
        print(f"\n[V2 ERROR] {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()
        out["v2"] = {"error": str(e)}

    try:
        out["v3"] = v3_cash_sharpe()
    except Exception as e:
        print(f"\n[V3 ERROR] {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()
        out["v3"] = {"error": str(e)}

    try:
        out["v4"] = v4_bond_decomposition()
    except Exception as e:
        print(f"\n[V4 ERROR] {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()
        out["v4"] = {"error": str(e)}

    # JSON snapshot
    snap_path = "D:/projects/Inv/study-research/bond_cash/raw/_v2_analysis/results.json"
    try:
        with open(snap_path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, default=str)
        print(f"\n✅ snapshot saved: {snap_path}")
    except Exception as e:
        print(f"snapshot save fail: {e}")


if __name__ == "__main__":
    main()
