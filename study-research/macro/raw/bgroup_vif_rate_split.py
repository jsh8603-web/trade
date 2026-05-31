"""bgroup_vif_rate_split.py — B(b) real_rate/term_spread rate축 분리 VIF 재측.

목적: 현 단일 'rate' factor 축을 real_rate(DFII10) + term_spread(T10Y2Y) 2축으로 분리 가능한지
      daily 공선성(VIF) 실측. ★Fisher 항등 회피: nominal ≈ real + breakeven 이므로 {nominal,real,
      breakeven} 동시 투입은 구조적 공선 → 금지. {real_rate, term_spread} 는 직교 추정 기대.

데이터(실측, FRED CSV):
  - DFII10  (10y TIPS real yield, %)        2003-01~2026-05
  - T10Y2Y  (10y-2y term spread, %)         1990-01~2026-05
  - T10YIE  (10y breakeven inflation, %)    2003-01~2026-05
  - DGS10   (10y nominal Treasury yield, %) 2003-01~ (from sector study, derived)

방법: 일별 Δ(레벨차분, 단위 동일 %), inner-join 공통일자, VIF + 상관 + condition number.
      VIF_i = 1/(1-R²_i) (i 번째 변수를 나머지로 회귀). VIF>5 주의, >10 심각 공선.

출력: stdout (validation md 에 박제). 점추정 단정 금지 — 공선 진단이므로 verdict = 분리가능/불가.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path

FRED = Path("study-research")
CY = FRED / "eq_us_cyclical/raw/fred"
DF = FRED / "eq_us_defensive/raw/fred"


def load_fred(path: Path, col: str) -> pd.Series:
    df = pd.read_csv(path)
    df.columns = ["date", "val"]
    df["date"] = pd.to_datetime(df["date"])
    s = pd.to_numeric(df["val"], errors="coerce")
    s.index = df["date"]
    return s.dropna()


def vif_table(X: pd.DataFrame) -> pd.DataFrame:
    """각 컬럼 VIF = 1/(1-R²) (나머지 컬럼으로 OLS 회귀)."""
    cols = list(X.columns)
    Xv = X.values
    out = {}
    for i, c in enumerate(cols):
        y = Xv[:, i]
        others = np.delete(Xv, i, axis=1)
        A = np.column_stack([np.ones(len(others)), others])
        beta, *_ = np.linalg.lstsq(A, y, rcond=None)
        resid = y - A @ beta
        ss_res = float(resid @ resid)
        ss_tot = float(((y - y.mean()) ** 2).sum())
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        out[c] = 1.0 / (1.0 - r2) if r2 < 1 else np.inf
    return pd.Series(out, name="VIF")


def cond_number(X: pd.DataFrame) -> float:
    Xs = (X - X.mean()) / X.std(ddof=0)
    s = np.linalg.svd(Xs.values, compute_uv=False)
    return float(s.max() / s.min())


def main():
    dfii10 = load_fred(DF / "DFII10.csv", "DFII10")        # real rate
    t10y2y = load_fred(CY / "T10Y2Y.csv", "T10Y2Y")        # term spread
    t10yie = load_fred(DF / "T10YIE.csv", "T10YIE")        # breakeven inflation
    dgs10 = load_fred(CY / "DGS10.csv", "DGS10")           # nominal 10y

    raw = pd.concat({"real_rate": dfii10, "term_spread": t10y2y,
                     "breakeven": t10yie, "nominal_10y": dgs10}, axis=1).dropna()
    # 일별 변화(레벨차분 — 단위 동일 %, 추세 제거로 정상화)
    d = raw.diff().dropna()
    print(f"=== B(b) rate축 분리 VIF (daily Δ, level diff) ===")
    print(f"공통 coverage: {d.index.min().date()} ~ {d.index.max().date()}  n={len(d)} 거래일")
    print()

    # Fisher 항등 확인: nominal ≈ real + breakeven
    fisher_resid = (raw["nominal_10y"] - raw["real_rate"] - raw["breakeven"])
    print(f"[Fisher 항등 검증] nominal - real - breakeven : "
          f"mean={fisher_resid.mean():+.4f} std={fisher_resid.std():.4f} "
          f"(≈0+소분산이면 구조적 공선 확인)")
    print()

    sets = {
        "TARGET {real_rate, term_spread}": ["real_rate", "term_spread"],
        "Fisher-violation {nominal, real, breakeven}": ["nominal_10y", "real_rate", "breakeven"],
        "{real_rate, term_spread, breakeven}": ["real_rate", "term_spread", "breakeven"],
        "{nominal, term_spread}": ["nominal_10y", "term_spread"],
    }
    for name, cols in sets.items():
        sub = d[cols]
        corr = sub.corr()
        vif = vif_table(sub)
        cn = cond_number(sub)
        print(f"--- {name} ---")
        print(f"  corr:\n{corr.round(3).to_string().replace(chr(10), chr(10)+'    ')}")
        print(f"  VIF: " + " | ".join(f"{c}={vif[c]:.2f}" for c in cols))
        print(f"  condition number={cn:.1f}  (>30 주의, >100 심각)")
        print()

    # 정상성 참고: Δ 자기상관 (block-bootstrap block size 판단용)
    for c in ["real_rate", "term_spread"]:
        ac1 = d[c].autocorr(1)
        print(f"  Δ{c} lag-1 autocorr={ac1:+.3f}")


if __name__ == "__main__":
    main()
