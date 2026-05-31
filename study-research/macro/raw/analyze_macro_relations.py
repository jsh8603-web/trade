"""analyze_macro_relations.py — macro 스터디 §2-2단계: lens 가설을 실데이터로 대조.

데이터: data/historical_{2022,2023,2024}/macro_yahoo_raw.json (일별 sp500/nasdaq/dxy/gold/oil/us10y).
목적: 거시 관계 가설(블록3 prior)을 실제 과거에서 검증 —
  (1) 전체 상관 vs partial-corr(glasso) 차이 = 공통원인 매개 분해 입증
  (2) regime별 조건부 상관이 실제로 달라지는가(R15 핵심 thesis) = RegimeGlasso 적용
  (3) 거시 driver(real rate proxy=us10y, dollar=dxy)와 자산 관계 부호 검증

regime 정의(데이터 자생 — 라벨 없음): us10y 추세(rate-up/rate-down) 60일 기울기로 2분할.
  → Investment Clock 의 'rate regime' 축 근사. risk-on/off 도 보조로 SP500 60일 모멘텀.

⛔ 추상 금지: 모든 관계는 이 출력의 수치로 뒷받침. confidence flag(블록5) 입력.
"""
from __future__ import annotations
import json, sys
import numpy as np
import pandas as pd

sys.path.insert(0, "D:/projects/Inv")
from core.structure.conditional_correlation import RegimeGlasso, effective_precision

COLS = ["sp500", "nasdaq", "dxy", "gold", "oil", "us10y"]


def load_prices() -> pd.DataFrame:
    frames = []
    for yr in ("2022", "2023", "2024"):
        d = json.load(open(f"data/historical_{yr}/macro_yahoo_raw.json", encoding="utf-8"))
        # 각 시리즈: [{date, close...}] — close 추출
        cols = {}
        for k in COLS:
            rows = d.get(k, [])
            s = pd.Series({r["date"]: r.get("close", r.get("open")) for r in rows})
            cols[k] = s
        df = pd.DataFrame(cols)
        frames.append(df)
    px = pd.concat(frames).sort_index()
    px = px[~px.index.duplicated(keep="last")]
    px.index = pd.to_datetime(px.index)
    return px.dropna()


def to_features(px: pd.DataFrame) -> pd.DataFrame:
    """가격 5종 = 로그수익률, us10y = 일별 레벨 변화(bp). 거시 driver 부호 직관 유지."""
    feat = pd.DataFrame(index=px.index)
    for c in ["sp500", "nasdaq", "dxy", "gold", "oil"]:
        feat[c] = np.log(px[c]).diff()
    feat["us10y"] = px["us10y"].diff()        # 금리 일변화(레벨, %p).
    return feat.dropna()


def define_regimes(px: pd.DataFrame, feat: pd.DataFrame):
    """rate-regime: us10y 60일 변화 부호 (rate-up=1 / rate-down=0). Investment Clock rate 축 근사."""
    slope = px["us10y"].reindex(feat.index).diff(60)
    rate_up = (slope > 0).astype(int)          # 1=금리상승국면, 0=금리하락국면
    return rate_up.fillna(0).astype(int).values


def corr_table(feat: pd.DataFrame, label: str):
    c = feat.corr()
    print(f"\n=== [{label}] 전체 Pearson 상관 (n={len(feat)}) ===")
    print(c.round(3).to_string())
    return c


def partial_corr_from_precision(prec: np.ndarray, cols):
    """precision → partial correlation: -P_ij/sqrt(P_ii P_jj)."""
    d = np.sqrt(np.diag(prec))
    pc = -prec / np.outer(d, d)
    np.fill_diagonal(pc, 1.0)
    return pd.DataFrame(pc, index=cols, columns=cols)


def main():
    px = load_prices()
    feat = to_features(px)
    print(f"기간: {feat.index[0].date()} ~ {feat.index[-1].date()}, n={len(feat)}일, 자산={COLS}")

    # (1) 전체 상관
    corr_full = corr_table(feat, "전체기간")

    # (2) regime 분할 상관
    regime = define_regimes(px, feat)
    feat2 = feat.copy()
    up = feat2[regime == 1]
    dn = feat2[regime == 0]
    print(f"\nregime 분포: rate-up={int((regime==1).sum())}일 / rate-down={int((regime==0).sum())}일")
    c_up = corr_table(up, "rate-UP 국면")
    c_dn = corr_table(dn, "rate-DOWN 국면")

    print("\n=== regime별 상관 차이 (UP - DOWN), |Δ|>0.15 = 조건부성 강함 ===")
    diff = (c_up - c_dn)
    pairs = []
    for i, a in enumerate(COLS):
        for j, b in enumerate(COLS):
            if i < j:
                pairs.append((f"{a}~{b}", round(corr_full.loc[a,b],3),
                              round(c_up.loc[a,b],3), round(c_dn.loc[a,b],3),
                              round(diff.loc[a,b],3)))
    print(f"{'pair':<16}{'full':>8}{'up':>8}{'down':>8}{'Δ(up-dn)':>10}")
    for p in sorted(pairs, key=lambda x: -abs(x[4])):
        flag = "  <-- 조건부 강함" if abs(p[4]) > 0.15 else ""
        print(f"{p[0]:<16}{p[1]:>8}{p[2]:>8}{p[3]:>8}{p[4]:>10}{flag}")

    # (3) RegimeGlasso — partial-corr (공통원인 매개 분해)
    print("\n=== RegimeGlasso partial-corr (직접효과; 전체상관과 차이=공통원인 분해) ===")
    X = feat.values
    rids = regime
    try:
        rg = RegimeGlasso(min_obs=30).fit(X, rids)
        for rid, m in sorted(rg.models_.items()):
            name = "rate-UP" if rid == 1 else "rate-DOWN"
            pc = partial_corr_from_precision(m.precision, COLS)
            print(f"\n--- regime {name} (n={m.n}, λ={m.lam:.3f}, glasso_α={m.glasso_alpha:.4f}, cond={m.cond_number:.1f}) ---")
            print("partial-corr:")
            print(pc.round(3).to_string())
            # 전체상관 대비 partial 이 죽은 엣지 = 공통원인 매개
            print("Pearson vs partial 차이 (|Pearson|-|partial| 큰 것 = 매개효과):")
            cc = (up if rid==1 else dn).corr()
            mediated = []
            for i,a in enumerate(COLS):
                for j,b in enumerate(COLS):
                    if i<j:
                        gap = abs(cc.loc[a,b]) - abs(pc.loc[a,b])
                        if gap > 0.1:
                            mediated.append((f"{a}~{b}", round(cc.loc[a,b],3), round(pc.loc[a,b],3), round(gap,3)))
            for med in sorted(mediated,key=lambda x:-x[3]):
                print(f"   {med[0]:<14} Pearson={med[1]:>7} partial={med[2]:>7} 매개={med[3]}")
    except Exception as e:
        import traceback; traceback.print_exc()
        print("RegimeGlasso 실패:", e)

    # (4) belief-mix Σ_eff 데모 (내 effective_precision 실데이터 적용)
    print("\n=== effective_precision belief-mix Σ_eff (rate-UP 0.7 / DOWN 0.3) ===")
    try:
        belief = {rid: (0.7 if rid==1 else 0.3) for rid in rg.models_}
        res = effective_precision(rg.models_, belief)
        print(f"Σ_eff cond={res.cond_number:.2f}, within_trace={res.within_trace:.4f}, "
              f"between_trace={res.between_trace:.4f}, dispersion={res.dispersion:.4f}, chol_ok={res.cholesky_ok}")
        print("dispersion = regime간 평균 이격 = belief 불확실 시 공분산 inflate(transition de-risk) 신호")
    except Exception as e:
        print("effective_precision 데모 실패:", e)


if __name__ == "__main__":
    main()
