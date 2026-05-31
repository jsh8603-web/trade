"""validate_macro_hypotheses.py — macro 2-3 실데이터 가설 검정.

검정(theory-notes 설계):
 - 가설0 (★선결 GATE): regime 신호가 평균(μ) 아닌 공분산(Σ)구조에 있다.
     Model A=Σ_regime(국면조건부 cov, μ=0) / B=Σ_static(정적) / C=μ_regime(국면평균, 정적 cov).
     LR test 2(LL_A−LL_B) chi2 + OOS logLik. A≫C 면 신호=공분산. ⛔ 실패 시 나머지 중단.
 - 가설2: between-regime Ω거리 > within. regime 라벨 셔플 permutation 1000회 p-value.
 - 가설4: force-include 없이 dxy~us10y(+)/gold~us10y(−) 직접 partial-corr 내생발견(부트스트랩 CI).
 - 가설5: Reflation/rate-down 에서 sp500~us10y 직접 pcorr≈0(매개)·CI 0 포함(decoupling).

데이터: data/historical_{2022,2023,2024}/macro_yahoo_raw.json (일별 6자산, n≈756).
결정론: seed 고정 bootstrap/permutation. 7축 확장(DFII10/VIX)=collector 이연, 가용 6자산 진행.
"""
from __future__ import annotations
import json, sys
import numpy as np
import pandas as pd

sys.path.insert(0, "D:/projects/Inv")
from core.structure.conditional_correlation import RegimeGlasso, fit_glasso_ebic, nonparanormal_transform

COLS = ["sp500", "nasdaq", "dxy", "gold", "oil", "us10y"]
SEED = 20260530


def load_features():
    frames = []
    for yr in ("2022", "2023", "2024"):
        d = json.load(open(f"data/historical_{yr}/macro_yahoo_raw.json", encoding="utf-8"))
        cols = {k: pd.Series({r["date"]: r.get("close", r.get("open")) for r in d.get(k, [])}) for k in COLS}
        frames.append(pd.DataFrame(cols))
    px = pd.concat(frames).sort_index()
    px = px[~px.index.duplicated(keep="last")]
    px.index = pd.to_datetime(px.index); px = px.dropna()
    feat = pd.DataFrame(index=px.index)
    for c in ["sp500", "nasdaq", "dxy", "gold", "oil"]:
        feat[c] = np.log(px[c]).diff()
    feat["us10y"] = px["us10y"].diff()
    feat = feat.dropna()
    slope = px["us10y"].reindex(feat.index).diff(60)
    regime = (slope > 0).astype(int).fillna(0).astype(int).values  # 1=rate-up 0=down
    return feat, regime, px


def _cov_mle(X):
    """MLE 공분산(μ=0 가정, 수익률). ridge 1e-6 안정."""
    S = (X.T @ X) / len(X)
    return S + 1e-6 * np.eye(S.shape[0])


def _mvn_loglik(X, mu, S):
    """다변량정규 총 loglik (μ, S)."""
    p = S.shape[0]
    sign, logdet = np.linalg.slogdet(S)
    if sign <= 0:
        S = S + 1e-4 * np.eye(p); sign, logdet = np.linalg.slogdet(S)
    Si = np.linalg.inv(S)
    d = X - mu
    quad = np.einsum("ij,jk,ik->i", d, Si, d)
    return float(np.sum(-0.5 * (p * np.log(2 * np.pi) + logdet + quad)))


def hypothesis_0_gate(feat, regime):
    print("=" * 70)
    print("가설0 (★선결 GATE): regime 신호가 평균 아닌 공분산구조에 있나")
    print("=" * 70)
    X = feat.values
    p = X.shape[1]
    rids = np.unique(regime)
    K = len(rids)

    # Model B: static cov, μ=0
    S_static = _cov_mle(X)
    LL_B = _mvn_loglik(X, np.zeros(p), S_static)

    # Model A: regime-conditional cov, μ=0
    LL_A = 0.0
    for r in rids:
        Xr = X[regime == r]
        LL_A += _mvn_loglik(Xr, np.zeros(p), _cov_mle(Xr))

    # Model C: regime mean, static cov
    LL_C = 0.0
    for r in rids:
        Xr = X[regime == r]
        LL_C += _mvn_loglik(Xr, Xr.mean(axis=0), S_static)

    # LR tests
    from core.structure.conditional_correlation import _norm_cdf
    def chi2_sf(stat, df):
        # Wilson-Hilferty 근사 chi2 생존함수
        if stat <= 0: return 1.0
        z = ((stat / df) ** (1/3) - (1 - 2/(9*df))) / np.sqrt(2/(9*df))
        return float(1.0 - _norm_cdf(z))
    df_cov = (K - 1) * p * (p + 1) / 2
    df_mean = (K - 1) * p
    LR_A_B = 2 * (LL_A - LL_B)
    LR_C_B = 2 * (LL_C - LL_B)
    p_A = chi2_sf(LR_A_B, df_cov)
    p_C = chi2_sf(LR_C_B, df_mean)
    print(f"in-sample logLik: A(Σ_regime)={LL_A:.1f} / B(Σ_static)={LL_B:.1f} / C(μ_regime)={LL_C:.1f}")
    print(f"LR A vs B (cov): {LR_A_B:.1f} (df={df_cov:.0f}) p={p_A:.2e}")
    print(f"LR C vs B (mean): {LR_C_B:.1f} (df={df_mean:.0f}) p={p_C:.2e}")
    print(f"공분산 정보이득 / 평균 정보이득 = {LR_A_B/max(LR_C_B,1e-9):.1f}배")

    # OOS: train 60% / test 40% (시간순)
    n = len(X); cut = int(n * 0.6)
    Xtr, rtr = X[:cut], regime[:cut]
    Xte, rte = X[cut:], regime[cut:]
    S_static_tr = _cov_mle(Xtr)
    Sr_tr = {r: _cov_mle(Xtr[rtr == r]) for r in rids if (rtr == r).sum() > p}
    LL_A_oos = sum(_mvn_loglik(Xte[rte == r], np.zeros(p), Sr_tr[r])
                   for r in rids if r in Sr_tr and (rte == r).sum() > 0)
    LL_B_oos = _mvn_loglik(Xte, np.zeros(p), S_static_tr)
    mur_tr = {r: Xtr[rtr == r].mean(axis=0) for r in rids if (rtr == r).sum() > p}
    LL_C_oos = sum(_mvn_loglik(Xte[rte == r], mur_tr[r], S_static_tr)
                   for r in rids if r in mur_tr and (rte == r).sum() > 0)
    print(f"\nOOS(train60/test40) logLik: A={LL_A_oos:.1f} / B={LL_B_oos:.1f} / C={LL_C_oos:.1f}")
    print(f"OOS A−B={LL_A_oos-LL_B_oos:+.1f} (양수=공분산조건부 OOS 우위) / C−B={LL_C_oos-LL_B_oos:+.1f}")

    gate_pass = (p_A < 0.01) and (LR_A_B > LR_C_B) and (LL_A_oos > LL_B_oos)
    print(f"\n>>> 가설0 GATE: {'PASS ✅' if gate_pass else 'FAIL ❌ (2-3 나머지 중단·즉시 보고)'}")
    print(f"    조건: LR_A_B p<0.01 [{p_A<0.01}] AND 공분산>평균 [{LR_A_B>LR_C_B}] AND OOS A>B [{LL_A_oos>LL_B_oos}]")
    return gate_pass


def _partial_corr(X):
    """nonparanormal→EBIC glasso→partial-corr 행렬."""
    Z = nonparanormal_transform(X)
    S = np.corrcoef(Z, rowvar=False)
    fit = fit_glasso_ebic(S, n=len(X))
    prec = fit.precision
    d = np.sqrt(np.diag(prec))
    pc = -prec / np.outer(d, d); np.fill_diagonal(pc, 1.0)
    return pc


def hypothesis_2_permutation(feat, regime, n_perm=1000):
    print("\n" + "=" * 70)
    print("가설2: between-regime Ω거리 > within (permutation 검정)")
    print("=" * 70)
    X = feat.values
    rids = np.unique(regime)
    pc = {r: _partial_corr(X[regime == r]) for r in rids}
    obs_dist = float(np.linalg.norm(pc[rids[0]] - pc[rids[1]]))
    rng = np.random.default_rng(SEED)
    null = []
    for _ in range(n_perm):
        perm = rng.permutation(regime)
        try:
            a = _partial_corr(X[perm == rids[0]]); b = _partial_corr(X[perm == rids[1]])
            null.append(np.linalg.norm(a - b))
        except Exception:
            continue
    null = np.array(null)
    pval = float((null >= obs_dist).mean())
    print(f"관측 between-regime ‖ΔΩ_pcorr‖_F = {obs_dist:.3f}")
    print(f"null(셔플 {len(null)}회) 평균={null.mean():.3f} 95%분위={np.quantile(null,0.95):.3f}")
    print(f"permutation p-value = {pval:.3f}  → {'유의(regime 조건부성 실재) ✅' if pval<0.05 else '비유의(국면내≈국면간, 취약가설 확인) ⚠️'}")
    return pval


def _block_bootstrap_pcorr(X, edges, n_boot=500, block=20):
    """블록 부트스트랩 partial-corr CI (자기상관 보존)."""
    rng = np.random.default_rng(SEED)
    n = len(X); nb = int(np.ceil(n / block))
    out = {e: [] for e in edges}
    for _ in range(n_boot):
        starts = rng.integers(0, max(n - block, 1), size=nb)
        idx = np.concatenate([np.arange(s, min(s + block, n)) for s in starts])[:n]
        try:
            pc = _partial_corr(X[idx])
            for (i, j) in edges:
                out[(i, j)].append(pc[i, j])
        except Exception:
            continue
    return {e: (np.quantile(v, 0.025), np.median(v), np.quantile(v, 0.975)) for e, v in out.items() if v}


def hypothesis_4_5_bootstrap(feat, regime):
    print("\n" + "=" * 70)
    print("가설4(내생발견)·5(단절): 핵심 엣지 부트스트랩 95% CI")
    print("=" * 70)
    X = feat.values
    ix = {c: i for i, c in enumerate(COLS)}
    up = X[regime == 1]; dn = X[regime == 0]
    edges = [(ix["dxy"], ix["us10y"]), (ix["gold"], ix["us10y"]),
             (ix["sp500"], ix["us10y"]), (ix["dxy"], ix["gold"])]
    name = {(ix["dxy"],ix["us10y"]):"dxy~us10y", (ix["gold"],ix["us10y"]):"gold~us10y",
            (ix["sp500"],ix["us10y"]):"sp500~us10y", (ix["dxy"],ix["gold"]):"dxy~gold"}
    for label, data in [("rate-UP", up), ("rate-DOWN", dn)]:
        ci = _block_bootstrap_pcorr(data, edges)
        print(f"\n--- {label} (n={len(data)}) partial-corr 95% CI ---")
        for e, (lo, md, hi) in ci.items():
            excl0 = "≠0(직접엣지)" if (lo > 0 or hi < 0) else "∋0(단절/매개)"
            print(f"  {name[e]:<14} [{lo:+.3f}, {hi:+.3f}] median={md:+.3f}  {excl0}")
    print("\n해석: 가설4 = dxy~us10y(rate-up CI>0)·gold~us10y(CI<0) 직접엣지 / 가설5 = sp500~us10y CI∋0(매개·단절)")


if __name__ == "__main__":
    feat, regime, px = load_features()
    print(f"데이터: {feat.index[0].date()}~{feat.index[-1].date()}, n={len(feat)}, "
          f"regime up={int((regime==1).sum())}/down={int((regime==0).sum())}\n")
    gate = hypothesis_0_gate(feat, regime)
    if not gate:
        print("\n⛔ 가설0 GATE FAIL — theory-notes 보강(b)대로 2-3 나머지 중단. main 즉시 보고.")
        sys.exit(0)
    hypothesis_2_permutation(feat, regime)
    hypothesis_4_5_bootstrap(feat, regime)
    print("\n" + "=" * 70 + "\n2-3 validation 완료 (가설0 GATE PASS → 2/4/5 진행)")
