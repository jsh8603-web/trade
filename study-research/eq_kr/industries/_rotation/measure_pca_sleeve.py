# -*- coding: utf-8 -*-
"""measure_pca_sleeve.py — S6 residual-PCA sleeve 실측 (plan §8 D1~D7).

★자문 B: raw-return PCA 는 PC1(=Korea risk-on/off)이 60-70% 흡수 → sleeve 무의미.
  → ① 공통인자 residualize → ② residual cross-section 에서 sleeve clustering (PCA).
D1 eigenvalue spectrum + MP edge/parallel-analysis / D2 PC1 loading / D3 PC2+ varimax 블록 /
D7 subsample 안정성 + 외부앵커 회귀(PC ~ USDKRW/flow/수출 부호).
★go-live·WIRE5 미접촉. 점추정 박제 금지(분포+CI, parallel analysis null).
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
IND_ROOT = ROOT.parent
INDUSTRIES = ["semiconductor", "auto", "financial", "battery", "chemical", "refining",
              "shipbuilding", "steel", "bio", "consumer", "telecom", "aitech"]
SEMI_PPI_LAG = 1
STRICT_OVERRIDE = {"refining": ["096770", "010950"]}

import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("mi", ROOT / "measure_integration.py")
mi = _ilu.module_from_spec(_spec); _spec.loader.exec_module(mi)
try:
    sys.stdout = io.TextIOWrapper(__import__("os").fdopen(__import__("os").dup(1), "wb"), encoding="utf-8")
except Exception:
    pass


def parallel_analysis(R, n_iter=500, seed=3):
    """Horn parallel analysis: 무작위 데이터 eigenvalue 95퍼센타일 = noise edge."""
    n, p = R.shape
    rng = np.random.default_rng(seed)
    rand_ev = np.zeros((n_iter, p))
    for i in range(n_iter):
        X = rng.standard_normal((n, p))
        rand_ev[i] = np.linalg.eigvalsh(np.corrcoef(X, rowvar=False))[::-1]
    return np.percentile(rand_ev, 95, axis=0)


def varimax(Phi, gamma=1.0, q=50, tol=1e-6):
    p, k = Phi.shape
    R = np.eye(k)
    d = 0
    for _ in range(q):
        d_old = d
        Lambda = Phi @ R
        u, s, vh = np.linalg.svd(
            Phi.T @ (Lambda ** 3 - (gamma / p) * Lambda @ np.diag(np.diag(Lambda.T @ Lambda))))
        R = u @ vh
        d = np.sum(s)
        if d_old != 0 and d / d_old < 1 + tol:
            break
    return Phi @ R


def main():
    # residual 패널 (measure_integration 재사용: 좀비 마스킹 + refining strict2)
    panels = {s: mi.panel_monthly(s) for s in INDUSTRIES}
    P = pd.DataFrame(panels).loc["2019-01-01":]
    F = mi.common_factors()
    Rresid = {s: mi.residualize(P[s], F) for s in INDUSTRIES}
    Rdf = pd.DataFrame(Rresid).dropna()

    out = {"meta": {
        "method": "S6 residual-PCA sleeve (plan §8 D1~D7). residual=공통인자{d_usdkrw,foreign,semi_ppi_yoy} 제거 후.",
        "자문_B": "raw-PCA PC1 60-70% 흡수 → residual cross-section PCA 로 sleeve. ★좀비 마스킹 + refining strict2 반영.",
        "n_months": len(Rdf), "go_live": "미접촉(사람게이트)"}}

    # ── correlation-PCA (구조 우선, 자문) ──
    C = Rdf.corr().values
    ev, evec = np.linalg.eigh(C)
    ev = ev[::-1]; evec = evec[:, ::-1]

    # D1: eigenvalue spectrum + parallel analysis + MP edge
    pa_95 = parallel_analysis(Rdf.values)
    n, p = Rdf.shape
    mp_edge = (1 + np.sqrt(p / n)) ** 2   # Marchenko-Pastur upper edge (λ＞edge = 신호)
    k_pa = int(np.sum(ev > pa_95))
    k_mp = int(np.sum(ev > mp_edge))
    out["D1_eigenvalue_spectrum"] = {
        "eigenvalues": [round(float(e), 3) for e in ev],
        "var_ratio": [round(float(e / p), 3) for e in ev],
        "parallel_analysis_95": [round(float(e), 3) for e in pa_95],
        "mp_upper_edge": round(float(mp_edge), 3),
        "k_star_parallel": k_pa, "k_star_mp": k_mp,
        "pc1_var": round(float(ev[0] / p), 3),
        "verdict": f"residual PC1 분산 {round(float(ev[0]/p)*100)}% (raw 55% 대비↓). noise선 넘는 PC = parallel {k_pa}개 / MP {k_mp}개 = sleeve 수 상한."}

    # D2: PC1 loading (공통 잔여 flow)
    out["D2_pc1_loading"] = {s: round(float(evec[i, 0]), 3) for i, s in enumerate(INDUSTRIES)}

    # D3: PC2+ varimax 블록 (k* 만큼)
    k = max(2, min(k_pa, 5))
    L = evec[:, :k] * np.sqrt(np.maximum(ev[:k], 0))
    Lv = varimax(L)
    blocks = {}
    for i, s in enumerate(INDUSTRIES):
        pc_assign = int(np.argmax(np.abs(Lv[i])))
        blocks.setdefault(f"PC{pc_assign+1}", []).append(s)
    out["D3_varimax_blocks"] = {
        "k_used": k,
        "loadings": {s: [round(float(Lv[i, j]), 2) for j in range(k)] for i, s in enumerate(INDUSTRIES)},
        "blocks": blocks}

    # D7: 외부앵커 회귀 (PC score ~ USDKRW/flow/semi_ppi, 부호 경제직관)
    scores = pd.DataFrame(Rdf.values @ evec[:, :k], index=Rdf.index, columns=[f"PC{i+1}" for i in range(k)])
    Fa = F.reindex(scores.index)
    anchor = {}
    for pc in scores.columns:
        y = scores[pc]
        row = {}
        for fac in F.columns:
            common = y.dropna().index.intersection(Fa[fac].dropna().index)
            if len(common) > 20:
                from scipy import stats as st
                rho = st.spearmanr(y.loc[common].values, Fa.loc[common, fac].values)[0]
                row[fac] = round(float(rho), 3)
        anchor[pc] = row
    out["D7_anchor_regression"] = {
        "method": "PC score ~ 공통인자 Spearman (residual 라 잔여 노출 = sleeve 경제 라벨)",
        "anchors": anchor,
        "note": "residual PC 라 공통인자 노출 약해야 정상(residualize 성공). 큰 잔여=residualize 불완전 flag."}

    # D7-b: subsample 안정성 (前半 2019-22 / 後半 2023-26 PC1 loading corr)
    half = len(Rdf) // 2
    C1 = Rdf.iloc[:half].corr().values; C2 = Rdf.iloc[half:].corr().values
    e1 = np.linalg.eigh(C1)[1][:, ::-1][:, 0]
    e2 = np.linalg.eigh(C2)[1][:, ::-1][:, 0]
    from scipy import stats as st
    pc1_stab = abs(st.spearmanr(np.abs(e1), np.abs(e2))[0])
    out["D7b_subsample_stability"] = {
        "pc1_loading_rank_corr_half": round(float(pc1_stab), 3),
        "verdict": "PC1 loading 前後半 rank corr (高=안정 sleeve, 低=spurious). 안정 블록만 채택."}

    fp = ROOT / "validation-pca-sleeve-v1.json"
    fp.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Saved {fp}\n")
    print("=== D1 eigenvalue spectrum (residual-PCA) ===")
    d1 = out["D1_eigenvalue_spectrum"]
    print(f"  eigenvalues: {d1['eigenvalues'][:6]}")
    print(f"  var_ratio:   {d1['var_ratio'][:6]}")
    print(f"  parallel95:  {d1['parallel_analysis_95'][:6]}")
    print(f"  MP edge={d1['mp_upper_edge']} | k*(parallel)={d1['k_star_parallel']} k*(MP)={d1['k_star_mp']} | PC1 var={d1['pc1_var']}")
    print(f"\n=== D3 varimax blocks (k={out['D3_varimax_blocks']['k_used']}) ===")
    for pc, members in out["D3_varimax_blocks"]["blocks"].items():
        print(f"  {pc}: {members}")
    print(f"\n=== D7 anchor regression (PC ~ 공통인자) ===")
    for pc, row in out["D7_anchor_regression"]["anchors"].items():
        print(f"  {pc}: {row}")
    print(f"\n=== D7b subsample stability ===\n  PC1 loading 前後半 rank corr = {out['D7b_subsample_stability']['pc1_loading_rank_corr_half']}")


if __name__ == "__main__":
    main()
