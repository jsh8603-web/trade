"""m1_factor_linkage.py — M1 거시-종목 연관성: factor loading B + 팩터공분산 Λ 실측.

목적: system_priors.factor_implied_cross_cov(betas, factor_cov) 의 실증 입력 생성.
  - B = 종목 sleeve 의 거시 named factor(rate/dollar/oil) loading (OLS beta, regime별)
  - Λ = 팩터 공분산 (regime별)
  - factor_implied_cross_cov(B, Λ) → implied cross-sleeve cov, 경험 cov 와 대조 + PD 검증.

★U3 reflexive 차단: 실현수익률 전용(belief/flag 不유입). ⛔ 합성無, data/historical 실 일별.
factors = rate(Δus10y), dollar(dxy logret), oil(oil logret). sleeves = us_stock(sp500),
  tech(nasdaq), gold. credit(HY OAS)=daily 부재로 이연.
"""
from __future__ import annotations
import json, sys
import numpy as np
import pandas as pd

sys.path.insert(0, "D:/projects/Inv")
from core.study.system_priors import factor_implied_cross_cov

RAW = ["sp500", "nasdaq", "dxy", "gold", "oil", "us10y"]
FACTORS = ["rate", "dollar", "oil"]
SLEEVES = ["us_stock", "tech", "gold"]


def load():
    frames = []
    for yr in ("2022", "2023", "2024"):
        d = json.load(open(f"data/historical_{yr}/macro_yahoo_raw.json", encoding="utf-8"))
        cols = {k: pd.Series({r["date"]: r.get("close", r.get("open")) for r in d.get(k, [])}) for k in RAW}
        frames.append(pd.DataFrame(cols))
    px = pd.concat(frames).sort_index()
    px = px[~px.index.duplicated(keep="last")]; px.index = pd.to_datetime(px.index); px = px.dropna()
    f = pd.DataFrame(index=px.index)
    f["rate"] = px["us10y"].diff()
    f["dollar"] = np.log(px["dxy"]).diff()
    f["oil"] = np.log(px["oil"]).diff()
    f["us_stock"] = np.log(px["sp500"]).diff()
    f["tech"] = np.log(px["nasdaq"]).diff()
    f["gold"] = np.log(px["gold"]).diff()
    f = f.dropna()
    slope = px["us10y"].reindex(f.index).diff(60)
    regime = (slope > 0).astype(int).fillna(0).astype(int).values
    return f, regime


def fit_B_Lambda(f):
    """OLS: sleeve ~ factors → B(S,F) + Λ(F,F) + idio var."""
    Fm = f[FACTORS].values
    Fc = np.column_stack([np.ones(len(Fm)), Fm])   # +intercept
    betas, idio = {}, {}
    for s in SLEEVES:
        y = f[s].values
        coef, *_ = np.linalg.lstsq(Fc, y, rcond=None)
        betas[s] = coef[1:]                          # drop intercept
        resid = y - Fc @ coef
        idio[s] = float(np.var(resid))
    Lam = np.cov(Fm, rowvar=False)
    return betas, Lam, idio


def main():
    f, regime = load()
    print(f"M1 거시-종목 factor linkage | 기간 {f.index[0].date()}~{f.index[-1].date()}, n={len(f)}")
    print(f"factors={FACTORS} (rate=Δus10y, dollar=dxy r, oil=oil r) / sleeves={SLEEVES}")
    print("⛔ 실현수익률 전용(U3 reflexive 차단) · 합성無\n")

    for label, mask in [("전체", np.ones(len(f), bool)), ("rate-UP", regime == 1), ("rate-DOWN", regime == 0)]:
        fm = f[mask]
        betas, Lam, idio = fit_B_Lambda(fm)
        print(f"=== [{label}] n={len(fm)} ===")
        print("  factor loading B (sleeve × [rate, dollar, oil]):")
        for s in SLEEVES:
            print(f"    {s:<9} rate={betas[s][0]:+.4f} dollar={betas[s][1]:+.3f} oil={betas[s][2]:+.3f}  idio_var={idio[s]:.2e}")
        print(f"  팩터공분산 Λ diag(var): rate={Lam[0,0]:.3e} dollar={Lam[1,1]:.2e} oil={Lam[2,2]:.2e}")
        # factor-implied cross-sleeve cov
        ccov = factor_implied_cross_cov(betas, Lam, factors=FACTORS, idio_var=idio)
        S = ccov.cov
        # 경험 cross-sleeve cov 대조
        emp = np.cov(fm[SLEEVES].values, rowvar=False)
        w = np.linalg.eigvalsh(S)
        print(f"  factor-implied Σ_cross PD: eig_min={w.min():.2e} (PD={'✅' if w.min()>0 else '❌'})")
        # implied vs empirical 상관 (off-diag)
        def corr(M):
            d = np.sqrt(np.diag(M)); return M / np.outer(d, d)
        ci, ce = corr(S), corr(emp)
        offs = [(SLEEVES[i], SLEEVES[j], ci[i,j], ce[i,j]) for i in range(3) for j in range(i+1,3)]
        print("  implied vs 경험 sleeve 상관(off-diag):")
        for a,b,iv,ev in offs:
            print(f"    {a}~{b}: implied={iv:+.3f} 경험={ev:+.3f} Δ={iv-ev:+.3f}")
        print()

    # regime별 loading 차이 (M1 핵심: 거시-종목 연관이 국면조건부인가)
    bu,_,_ = fit_B_Lambda(f[regime==1]); bd,_,_ = fit_B_Lambda(f[regime==0])
    print("=== regime별 factor loading 차이 (rate-UP − rate-DOWN) — 거시-종목 연관 국면조건부성 ===")
    for s in SLEEVES:
        dr = bu[s]-bd[s]
        print(f"  {s:<9} Δrate={dr[0]:+.4f} Δdollar={dr[1]:+.3f} Δoil={dr[2]:+.3f}")
    print("\n해석: rate loading 부호·크기가 sleeve별로 다르고 regime 조건부면 = 거시→종목 차등전이(M1 입증).")


if __name__ == "__main__":
    main()
