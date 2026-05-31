"""m3-commodity-linkage.py — M3 commodity sleeve 거시연관 분석.

지시 (timeline.md §4): regime별 sleeve 수익률 분해 + rate/dollar/oil driver loading
  + cross-asset-class vs within-sleeve 구분 (L축 caveat).
  ★rate 직접보다 dollar 채널·국면조건부 주목 (M1 발견).

⛔ 합성無, PIT (분기말 close 사용), OOS regime 라벨은 timeline.md proxy 그대로 (재라벨링 X).
data: yfinance 실 일별 (2021-12 ~ 2024-12, 3년 13분기).
"""
from __future__ import annotations
import json, sys
import numpy as np
import pandas as pd
import yfinance as yf

sys.stdout.reconfigure(encoding="utf-8")

# Sleeve ticker (commodity 4 sub-sleeve)
SLEEVES = {
    "energy": ["CL=F", "BZ=F", "NG=F"],            # WTI, Brent, NatGas
    "industrial": ["HG=F"],                          # Copper (Al·Zn 선물 yahoo 부재 → ETF 보조 안 함, raw 우선)
    "precious_non_gold": ["SI=F", "PL=F", "PA=F"],  # Silver, Platinum, Palladium
    "agri": ["ZC=F", "ZW=F", "ZS=F"],               # Corn, Wheat, Soybeans
}
# Macro driver
DRIVER = {
    "us10y": "^TNX",   # 10Y yield (=us10y * 10, 변환 후)
    "dxy": "DX-Y.NYB", # DXY index
    "oil": "CL=F",     # WTI (자기 sleeve 와 collinear — energy 제외 회귀 추가 비교)
}

# Timeline epoch (M1)
EPOCH = {
    "E1_긴축충격":   ("2022-01-01", "2022-09-30"),
    "E2_전환반등":   ("2022-10-01", "2023-06-30"),
    "E3_금리재상승": ("2023-07-01", "2023-09-30"),
    "E4_pivot인하":  ("2023-10-01", "2024-12-31"),
}
# Regime (timeline.md proxy: rate방향 × equity방향)
REGIME_Q = {
    "2021Q4": "Recovery",
    "2022Q1": "긴축",     "2022Q2": "긴축",     "2022Q3": "긴축",     "2022Q4": "Recovery",
    "2023Q1": "Reflation","2023Q2": "Recovery", "2023Q3": "긴축",     "2023Q4": "Reflation",
    "2024Q1": "Recovery", "2024Q2": "Reflation","2024Q3": "Reflation","2024Q4": "Recovery",
}


def fetch():
    """yfinance fetch — 2021-12-01 ~ 2024-12-31. close 일별."""
    all_tickers = sorted({t for v in SLEEVES.values() for t in v} | set(DRIVER.values()))
    df = yf.download(all_tickers, start="2021-12-01", end="2024-12-31",
                     auto_adjust=False, progress=False, group_by="ticker")
    # ticker 별 close 추출
    out = pd.DataFrame()
    for t in all_tickers:
        try:
            out[t] = df[t]["Close"]
        except Exception:
            print(f"  ⚠️ ticker {t} 데이터 부재", file=sys.stderr)
    out = out.dropna(how="all")
    # ^TNX = yield × 10 (e.g. 35.0 = 3.50%) → 보정
    if "^TNX" in out.columns:
        out["^TNX"] = out["^TNX"] / 10.0
    return out


def quarterly_return(px: pd.Series) -> pd.Series:
    """분기말 close 기준 분기 수익률 (log return)."""
    q = px.resample("QE").last().dropna()
    return np.log(q).diff().dropna()


def quarterly_d10y(yld: pd.Series) -> pd.Series:
    """분기말 10Y yield 변화 (bp)."""
    q = yld.resample("QE").last().dropna()
    return (q.diff() * 100).dropna()  # %p → bp


def main():
    print("=" * 88)
    print("M3 commodity sleeve 거시연관 분석 (M1 timeline.md §4 가이드)")
    print("=" * 88)
    px = fetch()
    print(f"raw px 기간 {px.index.min().date()}~{px.index.max().date()} | n={len(px)} 거래일")
    print(f"sleeve = {list(SLEEVES.keys())}, driver = {list(DRIVER.keys())}")
    print("⛔ 합성無, yfinance 실 일별. PIT (분기말 close). regime = M1 timeline proxy 그대로.\n")

    # 분기 수익률 / driver 변화
    q = pd.DataFrame()
    # sleeve 수익률 = ticker 평균 (equal-weight, sleeve 대표)
    for sl, tks in SLEEVES.items():
        valid = [t for t in tks if t in px.columns]
        if not valid:
            continue
        # ticker 별 분기 수익 → sleeve mean
        rets = pd.concat([quarterly_return(px[t]) for t in valid], axis=1)
        rets.columns = valid
        q[f"sleeve_{sl}"] = rets.mean(axis=1)
        # within-sleeve pairwise corr (L축 — equity factor like 식별)
        if len(valid) >= 2:
            print(f"--- within-sleeve [{sl}] daily logret corr (n={len(valid)} ticker) ---")
            daily = np.log(px[valid]).diff().dropna()
            cm = daily.corr()
            for i in range(len(valid)):
                for j in range(i+1, len(valid)):
                    print(f"  {valid[i]} ↔ {valid[j]}: {cm.iloc[i,j]:+.3f}")
    # driver
    if "^TNX" in px.columns:
        q["d_us10y"] = quarterly_d10y(px["^TNX"])
    if "DX-Y.NYB" in px.columns:
        q["dxy_r"] = quarterly_return(px["DX-Y.NYB"])
    if "CL=F" in px.columns:
        q["oil_r"] = quarterly_return(px["CL=F"])
    q = q.dropna()
    # regime / epoch 라벨
    q["regime"] = q.index.to_period("Q").astype(str).map(REGIME_Q).fillna("Unknown")
    def epoch_of(d):
        for nm, (s, e) in EPOCH.items():
            if pd.Timestamp(s) <= d <= pd.Timestamp(e):
                return nm
        return "Pre_E1"
    q["epoch"] = q.index.map(epoch_of)
    print(f"\n분기 panel n={len(q)} | columns={list(q.columns)}")

    # ===== 1. Regime 별 sleeve 분기 수익률 분해 =====
    print("\n" + "=" * 88)
    print("1. Regime 별 sleeve 평균 분기수익률 (mean ± std, n)")
    print("=" * 88)
    sleeve_cols = [c for c in q.columns if c.startswith("sleeve_")]
    for sl in sleeve_cols:
        print(f"\n  [{sl}]")
        for rg, sub in q.groupby("regime"):
            r = sub[sl].dropna()
            print(f"    {rg:<10} n={len(r):2d}  mean={r.mean()*100:+6.2f}%  std={r.std()*100:5.2f}%  min={r.min()*100:+.1f}% max={r.max()*100:+.1f}%")

    # ===== 2. Epoch 별 sleeve 누적수익 =====
    print("\n" + "=" * 88)
    print("2. Epoch 별 sleeve 누적수익 (log → 단순)")
    print("=" * 88)
    for ep, sub in q.groupby("epoch"):
        if ep == "Pre_E1":
            continue
        print(f"\n  [{ep}] 분기 {len(sub)} 개")
        for sl in sleeve_cols:
            cum = np.exp(sub[sl].sum()) - 1
            print(f"    {sl:<28} 누적 {cum*100:+7.2f}%")

    # ===== 3. Driver loading 회귀 (sleeve ~ rate, dollar, oil) =====
    print("\n" + "=" * 88)
    print("3. Driver loading 회귀 — sleeve ~ [Δus10y(bp), dxy_r, oil_r]")
    print("=" * 88)
    print("  ⚠️ energy sleeve 는 oil 과 collinear (CL=F 자기) — energy 만 oil 제외 회귀 추가 비교")
    drv_cols = ["d_us10y", "dxy_r", "oil_r"]
    for sl in sleeve_cols:
        y = q[sl].values
        # 전체 (3 driver)
        X = np.column_stack([np.ones(len(q)), q[drv_cols].values])
        coef, res, rnk, sv = np.linalg.lstsq(X, y, rcond=None)
        yhat = X @ coef
        ss_res = ((y - yhat) ** 2).sum()
        ss_tot = ((y - y.mean()) ** 2).sum()
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
        print(f"\n  [{sl}]  n={len(q)}")
        print(f"    β_rate(per bp) = {coef[1]*100:+.4f}%/bp  β_dxy = {coef[2]:+.3f}  β_oil = {coef[3]:+.3f}   R²={r2:.3f}")
        # rate 직접 vs dollar 비교
        # rate-up regime conditional
        for sub_rg, lab in [(q["d_us10y"] > 0, "rate-UP"), (q["d_us10y"] <= 0, "rate-DOWN")]:
            if sub_rg.sum() >= 3:
                ys = q[sl][sub_rg].values
                Xs = np.column_stack([np.ones(sub_rg.sum()), q[drv_cols][sub_rg].values])
                cs, *_ = np.linalg.lstsq(Xs, ys, rcond=None)
                print(f"    {lab:<8} n={sub_rg.sum():2d}: β_rate={cs[1]*100:+.4f}%/bp  β_dxy={cs[2]:+.3f}  β_oil={cs[3]:+.3f}")
        if "energy" in sl:
            # oil 제외 (collinear 회피)
            X2 = np.column_stack([np.ones(len(q)), q[["d_us10y", "dxy_r"]].values])
            c2, *_ = np.linalg.lstsq(X2, y, rcond=None)
            yhat2 = X2 @ c2
            r2_2 = 1 - ((y - yhat2) ** 2).sum() / ss_tot if ss_tot > 0 else np.nan
            print(f"    [oil 제외] β_rate={c2[1]*100:+.4f}%/bp β_dxy={c2[2]:+.3f}  R²={r2_2:.3f}")

    # ===== 4. Cross-sleeve vs cross-asset 상관 (L축 caveat 점검) =====
    print("\n" + "=" * 88)
    print("4. Cross-sleeve 분기수익 pairwise corr (자산군*간*, 거시 named factor 정합)")
    print("=" * 88)
    cm = q[sleeve_cols].corr()
    print(cm.round(3).to_string())

    # ===== 5. 요약 핵심상관 (회신용) =====
    print("\n" + "=" * 88)
    print("5. 핵심상관 (main 회신용 1-pager)")
    print("=" * 88)
    # rate-up 시 sleeve 평균 vs rate-down
    for sl in sleeve_cols:
        rup = q[q["d_us10y"] > 0][sl].mean() * 100
        rdn = q[q["d_us10y"] <= 0][sl].mean() * 100
        print(f"  {sl:<28}  rate-UP {rup:+6.2f}%  vs  rate-DOWN {rdn:+6.2f}%   Δ={rup-rdn:+.2f}%p")
    # dxy 상관 (sleeve ~ DXY return spearman/pearson)
    from scipy.stats import spearmanr
    print("\n  sleeve ↔ DXY 분기수익 corr (pearson, spearman):")
    for sl in sleeve_cols:
        p = q[sl].corr(q["dxy_r"])
        sp, _ = spearmanr(q[sl], q["dxy_r"])
        print(f"    {sl:<28}  pearson={p:+.3f}  spearman={sp:+.3f}")
    print("\n  sleeve ↔ oil 분기수익 corr:")
    for sl in sleeve_cols:
        if "energy" in sl:
            continue  # 자기 sleeve
        p = q[sl].corr(q["oil_r"])
        sp, _ = spearmanr(q[sl], q["oil_r"])
        print(f"    {sl:<28}  pearson={p:+.3f}  spearman={sp:+.3f}")

    # 결과 저장
    out_path = "D:/projects/Inv/study-research/commodity/raw/m3-commodity-linkage-results.json"
    res = {
        "panel_n": len(q),
        "period": f"{q.index.min().date()}~{q.index.max().date()}",
        "sleeves": list(SLEEVES.keys()),
        "regime_means": {sl: q.groupby("regime")[sl].mean().to_dict() for sl in sleeve_cols},
        "epoch_cumret": {ep: {sl: float(np.exp(sub[sl].sum())-1) for sl in sleeve_cols} for ep, sub in q.groupby("epoch") if ep != "Pre_E1"},
        "cross_sleeve_corr": cm.round(4).to_dict(),
        "rate_up_down": {sl: {"up": float(q[q["d_us10y"]>0][sl].mean()), "down": float(q[q["d_us10y"]<=0][sl].mean())} for sl in sleeve_cols},
        "dxy_corr": {sl: {"pearson": float(q[sl].corr(q["dxy_r"])), "spearman": float(spearmanr(q[sl], q["dxy_r"])[0])} for sl in sleeve_cols},
        "oil_corr": {sl: {"pearson": float(q[sl].corr(q["oil_r"])), "spearman": float(spearmanr(q[sl], q["oil_r"])[0])} for sl in sleeve_cols if "energy" not in sl},
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n결과 저장: {out_path}")


if __name__ == "__main__":
    main()
