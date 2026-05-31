"""m4_factor_vif.py — M4 factor 축 확장 직교성(VIF) 실측.

cross-sleeve factor 4→N 확장 시 다중공선성(collinearity) 점검. 현 FACTORS=(rate,dollar,oil,credit).
가용 실데이터로 구성가능 factor: rate(Δus10y), dollar(Δlog dxy), oil(Δlog oil), vol(sp500 20d 실현변동성).
real_rate(DFII10)/term_spread(T10Y2Y)/credit(HY OAS)/VIX/funding= collector 이연(daily 부재).

VIF_i = 1/(1−R²_i), R²_i = factor_i ~ 나머지 factors 회귀. VIF<5 직교충분 / 5~10 주의 / >10 심각.
★L축 1회계상 = factor 간 직교(공통분산 1회만). ⛔합성無 data/historical 실 일별.
"""
from __future__ import annotations
import json, sys
import numpy as np
import pandas as pd

RAW = ["sp500", "dxy", "oil", "us10y"]


def load():
    frames = []
    for yr in ("2022", "2023", "2024"):
        d = json.load(open(f"data/historical_{yr}/macro_yahoo_raw.json", encoding="utf-8"))
        cols = {k: pd.Series({r["date"]: r.get("close", r.get("open")) for r in d.get(k, [])}) for k in RAW}
        frames.append(pd.DataFrame(cols))
    px = pd.concat(frames).sort_index()
    px = px[~px.index.duplicated(keep="last")]; px.index = pd.to_datetime(px.index)
    return px.dropna()


def vif(X, names):
    out = {}
    for i, nm in enumerate(names):
        y = X[:, i]
        Z = np.column_stack([np.ones(len(X))] + [X[:, j] for j in range(X.shape[1]) if j != i])
        coef, *_ = np.linalg.lstsq(Z, y, rcond=None)
        resid = y - Z @ coef
        r2 = 1 - np.var(resid) / np.var(y)
        out[nm] = 1.0 / max(1e-9, 1 - r2)
    return out


def main():
    px = load()
    f = pd.DataFrame(index=px.index)
    f["rate"] = px["us10y"].diff()
    f["dollar"] = np.log(px["dxy"]).diff()
    f["oil"] = np.log(px["oil"]).diff()
    sp_ret = np.log(px["sp500"]).diff()
    f["vol"] = sp_ret.rolling(20).std()          # VIX surrogate (실현변동성)
    f = f.dropna()
    print(f"M4 factor 직교성 VIF | n={len(f)}, {f.index[0].date()}~{f.index[-1].date()} | ⛔합성無")
    print("가용 factor: rate(Δus10y)/dollar(Δlog dxy)/oil(Δlog oil)/vol(sp500 20d 실현변동성=VIX 대용)\n")

    print("=== 상관행렬 (Pearson) ===")
    print(f.corr().round(3).to_string())

    print("\n=== VIF (1/(1−R²), <5 직교충분 / >10 심각) ===")
    # 현 4 factor 중 가용 3(rate/dollar/oil) + 신규후보 vol
    for subset, label in [(["rate","dollar","oil"], "현 FACTORS 가용 3종"),
                          (["rate","dollar","oil","vol"], "+vol(VIX 대용) 확장")]:
        X = f[subset].values
        v = vif(X, subset)
        print(f"  [{label}]")
        for nm in subset:
            flag = "✅" if v[nm]<5 else ("주의" if v[nm]<10 else "⛔심각")
            print(f"    VIF[{nm:<7}]={v[nm]:.2f} {flag}")

    # vol 의 rate/dollar/oil 과 상관 (직교성 직접)
    print("\n=== vol(변동성) vs 기존 factor 상관 (직교성 직접 점검) ===")
    for c in ["rate","dollar","oil"]:
        print(f"  corr(vol, {c}) = {f['vol'].corr(f[c]):+.3f}")
    print("\n해석: vol VIF·상관 낮으면 신규 factor 로 직교 추가 가능. 높으면 dollar/rate 와 공통분산 중복(L축 위반).")


if __name__ == "__main__":
    main()
