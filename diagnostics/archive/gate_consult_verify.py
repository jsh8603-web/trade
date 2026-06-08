"""P3 게이트 자문 — 데이터 검증 (무비판 수용 금지, decision-quality-protocol advisory).

자문 3대 방향 claim 을 우리 실데이터(yfinance)로 정량 검증:
  C1. "단일종목 -10% 급락 = 사실상 시장 dip 매수"(시장베타 교락)
      → 개별종목 21d 수익 ~ SPY 21d 수익 회귀 R²(시장 설명분).
  C2. "저평가 진입 이벤트 유효N 한 자릿수"(valuation gap 자기상관)
      → 가격 < 0.75×200dMA(저평가 proxy) 독립 에피소드(gap>60d) 카운트.
  C3. "단일종목 -10% dip 이 시장 dip 과 동시 발생"
      → 종목 21d<-10% 사건 중 SPY 21d<-5% 동반 비율.

hedge: n<30 독립 에피소드는 방향성 prior 한정(단정 금지).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

TICKERS = ["AAPL", "MSFT", "JPM", "KO", "XOM", "JNJ", "PG", "WMT", "CVX", "INTC"]
START, END = "2010-01-01", "2026-06-01"


def main():
    import yfinance as yf
    print(f"[fetch] {len(TICKERS)}종목 + SPY {START}~{END} ...")
    raw = yf.download(TICKERS + ["SPY"], start=START, end=END, auto_adjust=True, progress=False)
    px = raw["Close"].dropna(how="all")
    spy = px["SPY"]
    print(f"[fetch] 일봉 {len(px)}행, 컬럼 {list(px.columns)}\n")

    spy_21 = spy.pct_change(21)
    rows = []
    for t in TICKERS:
        if t not in px.columns:
            print(f"  {t}: 데이터 없음 skip")
            continue
        s = px[t].dropna()
        if len(s) < 300:
            print(f"  {t}: n={len(s)} 부족 skip")
            continue
        r21 = s.pct_change(21)

        # C1: 21d 수익 시장 설명분 R²
        df = pd.concat([r21, spy_21], axis=1, keys=["stk", "spy"]).dropna()
        if len(df) > 50:
            beta, alpha = np.polyfit(df["spy"], df["stk"], 1)
            pred = beta * df["spy"] + alpha
            ss_res = ((df["stk"] - pred) ** 2).sum()
            ss_tot = ((df["stk"] - df["stk"].mean()) ** 2).sum()
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
        else:
            beta, r2 = np.nan, np.nan

        # C2: 저평가 proxy(가격<0.75×200dMA) 독립 에피소드
        ma200 = s.rolling(200).mean()
        cheap = (s < 0.75 * ma200)
        cheap_days = int(cheap.sum())
        # 독립 에피소드: cheap True 진입 시작점이 직전 종료서 >60일 떨어진 것
        idx = np.where(cheap.values)[0]
        episodes = 0
        if len(idx) > 0:
            episodes = 1
            for k in range(1, len(idx)):
                if idx[k] - idx[k - 1] > 60:
                    episodes += 1

        # C3: 종목 21d<-10% 중 SPY 21d<-5% 동반
        dip = df[df["stk"] <= -0.10]
        n_dip = len(dip)
        co = int((dip["spy"] <= -0.05).sum()) if n_dip else 0
        co_frac = co / n_dip if n_dip else np.nan

        rows.append(dict(ticker=t, n=len(s), beta=beta, r2_market=r2,
                         cheap_days=cheap_days, cheap_episodes=episodes,
                         n_dip10=n_dip, dip_co_market=co, dip_co_frac=co_frac))

    res = pd.DataFrame(rows)
    pd.set_option("display.width", 160, "display.max_columns", 20)
    print("=" * 100)
    print("[C1 시장 설명분] 개별종목 21d 수익 ~ SPY 21d 회귀 R² (높을수록 '시장 dip' 교락)")
    print(res[["ticker", "beta", "r2_market"]].to_string(index=False))
    print(f"\n  R² 중앙값 = {res['r2_market'].median():.3f}, 평균 = {res['r2_market'].mean():.3f}")
    print(f"  → 자문 claim '단일종목 급락=시장 dip 매수' 검증: R²↑면 지지")

    print("\n" + "=" * 100)
    print("[C2 유효N] 저평가(가격<0.75×200dMA) 독립 에피소드(gap>60d) — 단일종목 표본수")
    print(res[["ticker", "cheap_days", "cheap_episodes"]].to_string(index=False))
    print(f"\n  독립 에피소드 중앙값 = {res['cheap_episodes'].median():.1f} (16년 일봉 기준)")
    print(f"  → 자문 claim '유효N 한 자릿수' 검증: 에피소드<10이면 지지")

    print("\n" + "=" * 100)
    print("[C3 동반] 종목 21d<-10% 급락 중 SPY 21d<-5% 동반 비율")
    print(res[["ticker", "n_dip10", "dip_co_market", "dip_co_frac"]].to_string(index=False))
    print(f"\n  동반비율 중앙값 = {res['dip_co_frac'].median():.3f}")
    print(f"  → 높을수록 '급락 진입=시장 타이밍' 교락 지지")
    print("=" * 100)

    res.to_csv(".p3-gate-verify-result.csv", index=False)
    print("\n[저장] .p3-gate-verify-result.csv")


if __name__ == "__main__":
    main()
