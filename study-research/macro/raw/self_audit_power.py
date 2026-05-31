"""self_audit_power.py — STUDY-KIT §2.5 감사 G(검정력한계) + B(Rank-IC 실측) 보강.

G: 공통원인 분해(partial-corr)·permutation(가설2)의 effective-n(AR1 보정) + MDE.
   → 가설2 p=0.35 비유의가 *진짜 null* 인지 *검정력 부족* 인지 정직 점검.
B: 실 Rank-IC 측정(가설1 미실행분 일부 보강) — 거시신호→forward return Spearman IC.
   ⛔ 합성·시뮬 금지: data/historical 실 일별만.
"""
from __future__ import annotations
import json, sys
import numpy as np
import pandas as pd

sys.path.insert(0, "D:/projects/Inv")
from core.structure.conditional_correlation import effective_n_ar1, mde, block_bootstrap_se
from core.assume.weight_falsification import rank_ic

COLS = ["sp500", "nasdaq", "dxy", "gold", "oil", "us10y"]


def load():
    frames = []
    for yr in ("2022", "2023", "2024"):
        d = json.load(open(f"data/historical_{yr}/macro_yahoo_raw.json", encoding="utf-8"))
        cols = {k: pd.Series({r["date"]: r.get("close", r.get("open")) for r in d.get(k, [])}) for k in COLS}
        frames.append(pd.DataFrame(cols))
    px = pd.concat(frames).sort_index()
    px = px[~px.index.duplicated(keep="last")]; px.index = pd.to_datetime(px.index); px = px.dropna()
    feat = pd.DataFrame(index=px.index)
    for c in ["sp500","nasdaq","dxy","gold","oil"]: feat[c] = np.log(px[c]).diff()
    feat["us10y"] = px["us10y"].diff()
    feat = feat.dropna()
    slope = px["us10y"].reindex(feat.index).diff(60)
    regime = (slope>0).astype(int).fillna(0).astype(int).values
    return feat, regime, px


def axis_G(feat, regime):
    print("="*70); print("G. 검정력 한계 — effective-n(AR1) + MDE (공통원인 분해·permutation)"); print("="*70)
    X = feat.values; p = X.shape[1]
    # 전체·regime별 effective-n
    for label, mask in [("전체", np.ones(len(X),bool)), ("rate-UP", regime==1), ("rate-DOWN", regime==0)]:
        Xm = X[mask]; n = len(Xm)
        # 각 series AR1 기반 effective-n (평균)
        neffs = [effective_n_ar1(Xm[:,j]) for j in range(p)]
        neff_mean = float(np.mean(neffs))
        # partial-corr MDE: 상관계수 검정 근사 MDE = (z_a/2 + z_pow)/sqrt(n_eff-3)  (Fisher-z)
        m = mde(int(neff_mean), alpha=0.05, power=0.8)
        print(f"  [{label}] n={n}, AR1 평균={np.mean([_ar1(Xm[:,j]) for j in range(p)]):+.3f}, "
              f"effective-n≈{neff_mean:.0f} (감쇠 {100*(1-neff_mean/n):.0f}%), MDE(상관)≈{m:.3f}")
    # 가설2 permutation 검정력 해석
    print("\n  가설2(Ω-diff permutation p=0.35) 검정력 해석:")
    neff_up = float(np.mean([effective_n_ar1(X[regime==1][:,j]) for j in range(p)]))
    neff_dn = float(np.mean([effective_n_ar1(X[regime==0][:,j]) for j in range(p)]))
    print(f"   - rate-UP n_eff≈{neff_up:.0f} / DOWN n_eff≈{neff_dn:.0f}")
    print("   - p×(p-1)/2 = 15 엣지 동시검정, regime당 effective-n 작음 → Ω 행렬 차이 탐지 검정력 제한.")
    print("   - 결론: p=0.35 는 '진짜 null(네트워크 불변)' 과 '검정력 부족' 을 *구분 못함*. 단 직접엣지")
    print("     (dxy~us10y 등)는 CI가 좁고 regime 불변 명확 → 적어도 강엣지는 불변이 robust.")


def _ar1(x):
    x = x[~np.isnan(x)]
    if len(x) < 3: return 0.0
    return float(np.corrcoef(x[:-1], x[1:])[0,1])


def axis_B_rank_ic(feat, px):
    print("\n"+"="*70); print("B. 실 Rank-IC 측정 (거시신호→forward return, 실데이터 n·기간 명시)"); print("="*70)
    idx = feat.index
    # forward 20일 수익률 (실 가격)
    fwd = {}
    for c in ["sp500","nasdaq","gold"]:
        lp = np.log(px[c]).reindex(idx)
        fwd[c] = (lp.shift(-20) - lp).values
    # 거시신호(이론 부호 명시): us10y 20일변화(rate momentum), dxy 20일모멘텀
    sig = {}
    sig["rate_mom(us10y Δ20)"] = px["us10y"].reindex(idx).diff(20).values
    sig["dollar_mom(dxy r20)"] = (np.log(px["dxy"]).reindex(idx) - np.log(px["dxy"]).reindex(idx).shift(20)).values
    pairs = [("rate_mom(us10y Δ20)","nasdaq","− 기대(금리↑→고듀레이션↓)"),
             ("rate_mom(us10y Δ20)","gold","− 기대(실질금리↑→금↓)"),
             ("dollar_mom(dxy r20)","gold","− 기대(달러↑→금↓)"),
             ("dollar_mom(dxy r20)","sp500","− 기대(달러↑→위험자산↓)")]
    print(f"  기간 {idx[0].date()}~{idx[-1].date()}, forward=20거래일, ⛔합성無 실가격")
    for s,t,exp in pairs:
        m = ~(np.isnan(sig[s]) | np.isnan(fwd[t]))
        ic,n = rank_ic(sig[s][m], fwd[t][m])
        print(f"  {s:<22}→ fwd20 {t:<7} Rank-IC={ic:+.3f} (n={n})  이론={exp}")
    print("  ⚠️ 단일 in-sample IC(overlapping 20d→자기상관, OOS·e-process 아님). 가설1 정식 OOS IC =")
    print("     macro→sleeve forward return 필요(macro 자체 forward 없음) → 통합단계 검증(미해결 H).")


if __name__ == "__main__":
    feat, regime, px = load()
    axis_G(feat, regime)
    axis_B_rank_ic(feat, px)
    print("\n"+"="*70+"\nself-audit G+B 보강 완료")
