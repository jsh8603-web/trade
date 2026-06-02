"""core/study/factor_cov_estimate.py — M4 거시-종목 factor 통합: 팩터 공분산 Λ 추정 (골격 M4-b).

cross-sleeve factor 공분산 B·Λ·Bᵀ 의 Λ(rate/dollar/oil/credit 팩터 공분산)를 실 팩터 시계열로 추정한다.
자문 3R 수렴(CONSULT-DECISIONS-M4-factor-integration-20260530.md §5·§7):

- **정상성**: factor return 혁신으로 변환 후 추정 — rate(DGS10)·credit(HY OAS) = Δbp(레벨 차분, near-unit-root
  상태변수), dollar(DTWEXBGS)·oil(WTI) = Δlog(가격/지수). ADF+KPSS 양쪽(차분 정상 & 레벨 비정상 확인).
- **gate 용 Λ**: EWMA(half-life 60~90d) + stress correlation floor `ρ←max(ρ_EWMA, ρ_stress)`(상향 클램프만,
  비대칭=down-only 일관) → Higham nearest-correlation PSD 재투영.
- **static 장기 Λ**: BL/Π(belief, 1차모멘트) 입력용 별도(안정성>반응성). gate 용과 분리(two-layer 분업).

이 모듈은 Λ 만 만든다. B·Λ·Bᵀ 합성=system_priors.factor_implied_cross_cov, betas=factor_betas_seed.
실데이터 fetch 는 호출자(shadow validation / M1 raw factor 시계열)가 주입 — 본 모듈은 순수 추정 로직.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np


# 팩터별 변환 규칙(자문 §5): 레벨차분 vs 로그수익.
FACTOR_TRANSFORM = {
    "real": "diff",      # DFII10 실질금리 Δ (★Y5 rate=DGS10 교체)
    "credit": "diff",    # HY OAS Δbp
    "breakeven": "diff", # T5YIE 기대인플레 Δ (★Y5 추가)
    "dollar": "dlog",    # DTWEXBGS broad TWI Δlog
    "oil": "dlog",       # WTI Δlog
    "vol": "dlog",       # VIX Δlog (M5 Phase A — 변동성지수 양수·mean-reverting, 로그수익 클러스터)
    "fx": "dlog",        # DEXKOUS KRW/USD 환율 Δlog (IC8 — denomination factor, 환율=로그수익)
}


@dataclass
class FactorCovResult:
    factors: list
    cov: np.ndarray          # Λ (F,F) PSD
    corr: np.ndarray         # 상관행렬(stress floor 적용 후)
    vols: np.ndarray         # 팩터별 std
    stress_applied: bool


def to_factor_returns(levels: dict, factors: Sequence[str]) -> np.ndarray:
    """팩터 레벨 시계열 dict → return 혁신 행렬 (T-1, F). 변환은 FACTOR_TRANSFORM.

    levels: {factor: 1d array(레벨)}. rate/credit=차분, dollar/oil=로그수익. 길이 일치 가정.
    """
    cols = []
    for f in factors:
        x = np.asarray(levels[f], dtype=float)
        kind = FACTOR_TRANSFORM.get(f, "diff")
        if kind == "dlog":
            r = np.diff(np.log(x))
        else:
            r = np.diff(x)
        cols.append(r)
    n = min(len(c) for c in cols)
    return np.column_stack([c[-n:] for c in cols])


def stationarity_flags(series: np.ndarray) -> dict:
    """ADF(귀무=단위근)+KPSS(귀무=정상) 근사 — statsmodels 없으면 휴리스틱 fallback.

    실데이터 검증용. 반환 {adf_reject_unitroot, kpss_reject_stationary, note}.
    차분계열은 adf_reject=True(정상) & kpss_reject=False(정상) 기대.
    """
    x = np.asarray(series, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 20:
        return {"adf_reject_unitroot": None, "kpss_reject_stationary": None, "note": "n<20"}
    try:
        from statsmodels.tsa.stattools import adfuller, kpss
        adf_p = adfuller(x, autolag="AIC")[1]
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            kpss_p = kpss(x, regression="c", nlags="auto")[1]
        return {"adf_reject_unitroot": adf_p < 0.05, "kpss_reject_stationary": kpss_p < 0.05,
                "adf_p": float(adf_p), "kpss_p": float(kpss_p), "note": "statsmodels"}
    except Exception:
        # fallback: lag-1 자기상관(ρ→1 이면 단위근 의심). 차분계열은 ρ 낮음.
        x0 = x - x.mean()
        rho = float(np.sum(x0[:-1] * x0[1:]) / np.sum(x0[:-1] ** 2)) if np.sum(x0[:-1] ** 2) > 0 else 0.0
        return {"adf_reject_unitroot": rho < 0.9, "kpss_reject_stationary": abs(rho) > 0.95,
                "rho1": rho, "note": "heuristic(lag1 ac)"}


def _ewma_cov(returns: np.ndarray, halflife: float) -> np.ndarray:
    """지수가중 공분산(half-life). 최근 관측 가중 ↑. 평균≈0 가정(factor 혁신)."""
    T = returns.shape[0]
    lam = 0.5 ** (1.0 / float(halflife))
    w = lam ** np.arange(T - 1, -1, -1)          # 과거→현재 가중 증가
    w = w / w.sum()
    mu = np.average(returns, axis=0, weights=w)
    X = returns - mu
    return (X * w[:, None]).T @ X                # 가중 공분산


def higham_nearest_corr(A: np.ndarray, *, max_iter: int = 100, tol: float = 1e-8) -> np.ndarray:
    """Higham(2002) alternating projection — 대칭 행렬을 가장 가까운 상관행렬(PSD·단위대각)로 투영.

    stress floor 상향 클램프 후 PSD 깨짐 복구용(자문 §5 필수).
    """
    n = A.shape[0]
    A = 0.5 * (A + A.T)
    Y = A.copy()
    dS = np.zeros_like(A)
    for _ in range(max_iter):
        R = Y - dS
        # PSD 투영(음 고유값 floor)
        w, V = np.linalg.eigh(0.5 * (R + R.T))
        w = np.clip(w, 0.0, None)
        X = (V * w) @ V.T
        dS = X - R
        # 단위 대각 투영
        Y = X.copy()
        np.fill_diagonal(Y, 1.0)
        if np.linalg.norm(Y - X, ord="fro") / max(np.linalg.norm(Y, ord="fro"), 1e-12) < tol:
            break
    # 수치적 PSD 보장
    w, V = np.linalg.eigh(0.5 * (Y + Y.T))
    w = np.clip(w, 1e-10, None)
    Y = (V * w) @ V.T
    d = np.sqrt(np.diag(Y))
    Y = Y / np.outer(d, d)
    return 0.5 * (Y + Y.T)


def estimate_factor_cov(
    factor_returns: np.ndarray, factors: Sequence[str], *,
    halflife: float = 75.0,
    stress_corr: Optional[np.ndarray] = None,
) -> FactorCovResult:
    """factor return 혁신 → gate 용 Λ. EWMA + stress corr floor(상향클램프) + Higham PSD.

    factor_returns: (T,F) 혁신(to_factor_returns 산출). halflife: EWMA 반감기(자문 60~90d).
    stress_corr: (F,F) ρ_stress(장기 팩터유도/보수사전값). 주면 ρ←max(ρ_EWMA, ρ_stress) 상향 클램프.
    """
    R = np.asarray(factor_returns, dtype=float)
    cov = _ewma_cov(R, halflife)
    cov = 0.5 * (cov + cov.T)
    vols = np.sqrt(np.clip(np.diag(cov), 1e-12, None))
    corr = cov / np.outer(vols, vols)
    corr = np.clip(corr, -1.0, 1.0)
    np.fill_diagonal(corr, 1.0)
    stress_applied = False
    if stress_corr is not None:
        S = np.asarray(stress_corr, dtype=float)
        # ★상향 클램프만(비대칭): 부호 보존하며 |ρ| 를 stress 쪽으로 상향. down-only 일관.
        clamped = corr.copy()
        for i in range(corr.shape[0]):
            for j in range(corr.shape[1]):
                if i == j:
                    continue
                if abs(S[i, j]) > abs(corr[i, j]):
                    clamped[i, j] = S[i, j]
        clamped = 0.5 * (clamped + clamped.T)
        corr = higham_nearest_corr(clamped)        # PSD 재투영
        stress_applied = True
    Lam = corr * np.outer(vols, vols)              # 상관→공분산 복원
    Lam = 0.5 * (Lam + Lam.T)
    # 최종 PSD 보장
    w, V = np.linalg.eigh(Lam)
    if np.any(w <= 0):
        w = np.clip(w, 1e-12, None)
        Lam = (V * w) @ V.T
        Lam = 0.5 * (Lam + Lam.T)
    return FactorCovResult(factors=list(factors), cov=Lam, corr=corr, vols=vols,
                           stress_applied=stress_applied)


# ===========================================================================
# self-test
# ===========================================================================
if __name__ == "__main__":
    rng = np.random.default_rng(7)
    factors = ["rate", "dollar", "oil", "credit"]
    T = 600

    # 1) 변환: rate/credit=차분, dollar/oil=로그수익
    levels = {
        "rate": np.cumsum(rng.normal(0, 3, T)) + 350,       # DGS10 bp 레벨(단위근성)
        "credit": np.cumsum(rng.normal(0, 5, T)) + 400,     # HY OAS bp
        "dollar": 100 * np.exp(np.cumsum(rng.normal(0, 0.003, T))),
        "oil": 80 * np.exp(np.cumsum(rng.normal(0, 0.02, T))),
    }
    R = to_factor_returns(levels, factors)
    assert R.shape == (T - 1, 4)
    print(f"1) to_factor_returns OK: shape={R.shape} (rate/credit=Δbp, dollar/oil=Δlog)")

    # 2) 정상성: 레벨=단위근 의심, 차분=정상
    lvl_flag = stationarity_flags(levels["rate"])
    dif_flag = stationarity_flags(R[:, 0])
    assert dif_flag["adf_reject_unitroot"] in (True, None)
    print(f"2) stationarity OK: 레벨 rho/adf={lvl_flag.get('rho1', lvl_flag.get('adf_p'))} "
          f"차분 정상판정={dif_flag['adf_reject_unitroot']} ({dif_flag['note']})")

    # 3) EWMA Λ: PSD + 대각=분산
    res = estimate_factor_cov(R, factors, halflife=75)
    eig = np.linalg.eigvalsh(res.cov)
    assert np.all(eig > 0), f"Λ PSD 위반: {eig}"
    print(f"3) EWMA Λ OK: PSD✓(min eig={eig.min():.3e}) vols={np.round(res.vols,4)}")

    # 4) ★stress corr floor: 상향 클램프 + Higham PSD. floor 후 |ρ| ≥ EWMA |ρ|
    base = estimate_factor_cov(R, factors, halflife=75)
    stress = np.eye(4)
    stress[0, 1] = stress[1, 0] = 0.7     # rate-dollar 위기 동조 0.7 강제
    stress[1, 3] = stress[3, 1] = 0.6     # dollar-credit
    fl = estimate_factor_cov(R, factors, halflife=75, stress_corr=stress)
    eig2 = np.linalg.eigvalsh(fl.cov)
    assert np.all(eig2 > 0), f"stress floor 후 PSD 위반(Higham 실패): {eig2}"
    assert abs(fl.corr[0, 1]) >= abs(base.corr[0, 1]) - 1e-9, "상향 클램프 위반(ρ 하향됨)"
    assert fl.corr[0, 1] >= 0.69 - 1e-6, f"stress 0.7 floor 미반영: {fl.corr[0,1]}"
    print(f"4) stress floor OK: rate-dollar ρ {base.corr[0,1]:+.3f}→{fl.corr[0,1]:+.3f}(≥0.7 클램프) "
          f"PSD✓(min eig={eig2.min():.3e}, Higham 재투영)")

    # 5) Higham: 비PSD 유사상관 → 가장 가까운 상관(PSD·단위대각)
    bad = np.array([[1.0, 0.9, -0.9], [0.9, 1.0, 0.9], [-0.9, 0.9, 1.0]])  # indefinite
    nc = higham_nearest_corr(bad)
    assert np.all(np.linalg.eigvalsh(nc) > -1e-10), "Higham 결과 비PSD"
    assert np.allclose(np.diag(nc), 1.0), "Higham 단위대각 위반"
    print(f"5) Higham OK: indefinite→PSD(min eig={np.linalg.eigvalsh(nc).min():.3e}) 단위대각✓")

    print("\nfactor_cov_estimate self-test PASS "
          "(Δbp/Δlog 변환 + ADF/KPSS 정상성 + EWMA Λ + stress 상향클램프 floor + Higham PSD 재투영)")
