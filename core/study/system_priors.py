"""core/study/system_priors.py — 시스템 선결 2건 파라미터화 (골격 G5).

자문/엄격검토에서 남은 시스템 선결 2건을 정책 함수로 구현한다. **본체(conditional_correlation,
regime_to_weights)는 안 고친다** — study_register(G6)가 학습 산출(RegimeModel/Σ)에 이 정책을 적용.

(1) **cross-sleeve 공분산 (factor-implied 기본)**: sleeve 간 공분산을 별도 추정(데이터 부족·노이즈)
    대신 **팩터 노출로 암시**한다. Σ_st = b_s'·Λ·b_t (+ s==t 면 idio). B Λ Bᵀ + diag(idio) = PD.
    bounded macro hybrid(자문 §8)의 named driver(rate/dollar/oil/credit) 베타가 factor loading.

(2) **regime obs floor (<30 → global shrink-fallback)**: regime 표본이 floor 미만이면 그 regime 의
    Σ 를 global(regime 무시 전체) Σ 쪽으로 수축. n 이 hard_min 미만이면 global 통째 fallback.
    소표본 regime 의 과적합(자문: N≈45 도 빠듯, partial-corr SE 0.186) 방어.

둘 다 PD 보존 + 입력 검증 + graceful. 파라미터(floor/hard_min/idio_floor)는 호출자가 조정.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np


# ---------------------------------------------------------------------------
# (1) cross-sleeve 공분산 — factor-implied
# ---------------------------------------------------------------------------

@dataclass
class CrossSleeveCov:
    """sleeve 간 factor-implied 공분산 결과."""
    sleeves: list                # 순서 = 행/열 라벨
    cov: np.ndarray              # (S, S) PD covariance
    factors: list                # 팩터 라벨(B 의 열)


def factor_implied_cross_cov(
    betas: dict, factor_cov: np.ndarray, *,
    factors: Optional[Sequence[str]] = None,
    idio_var: Optional[dict] = None,
    idio_floor: float = 1e-4,
) -> CrossSleeveCov:
    """sleeve 팩터 베타 + 팩터 공분산 → cross-sleeve 공분산 Σ = B Λ Bᵀ + diag(idio).

    betas: {sleeve: [b_f1, b_f2, ...]} (팩터 순서 일치). factor_cov: (F,F) 팩터 공분산 Λ.
    idio_var: {sleeve: 고유분산}(없으면 idio_floor). 결과는 항상 PD(idio_floor>0 보장).
    """
    sleeves = list(betas.keys())
    if not sleeves:
        return CrossSleeveCov(sleeves=[], cov=np.empty((0, 0)), factors=list(factors or []))
    B = np.array([np.asarray(betas[s], dtype=float) for s in sleeves])   # (S, F)
    Lam = np.asarray(factor_cov, dtype=float)
    if B.shape[1] != Lam.shape[0] or Lam.shape[0] != Lam.shape[1]:
        raise ValueError(f"베타 팩터수 {B.shape[1]} ≠ factor_cov {Lam.shape}")
    Sigma = B @ Lam @ B.T                                                # (S, S) systematic
    idio = np.full(len(sleeves), float(idio_floor))
    if idio_var:
        for i, s in enumerate(sleeves):
            idio[i] = max(float(idio_var.get(s, idio_floor)), idio_floor)
    Sigma = Sigma + np.diag(idio)
    Sigma = 0.5 * (Sigma + Sigma.T)
    # PD 보정(수치 오차로 음의 고유값 시 floor)
    w, V = np.linalg.eigh(Sigma)
    if np.any(w <= 0):
        w = np.clip(w, idio_floor, None)
        Sigma = (V * w) @ V.T
        Sigma = 0.5 * (Sigma + Sigma.T)
    return CrossSleeveCov(sleeves=sleeves, cov=Sigma,
                          factors=list(factors or [f"f{i}" for i in range(B.shape[1])]))


# ---------------------------------------------------------------------------
# (2) regime obs floor — global shrink-fallback
# ---------------------------------------------------------------------------

@dataclass
class RegimeShrinkResult:
    """regime obs floor shrink 산출. regime_id → (Σ_shrunk, λ_to_local, mode)."""
    sigma: dict                  # regime_id → Σ (shrunk)
    precision: dict              # regime_id → Ω = inv(Σ)
    lam_local: dict              # regime_id → local 가중(1=원본, 0=global)
    mode: dict                   # regime_id → 'keep' | 'shrink' | 'fallback'


def regime_obs_floor_shrink(
    regime_sigma: dict, obs_counts: dict, global_sigma: np.ndarray,
    *, floor: int = 30, hard_min: int = 10,
) -> RegimeShrinkResult:
    """regime 표본 부족 시 global Σ 로 수축.

    n ≥ floor          → keep(원본 그대로, λ=1).
    hard_min ≤ n < floor → shrink: Σ' = λ·Σ_r + (1-λ)·Σ_global, λ=(n-hard_min)/(floor-hard_min).
    n < hard_min       → fallback: Σ' = Σ_global(λ=0).
    PD 보존(둘 다 PD 면 볼록결합도 PD). precision 동반 산출.
    """
    G = np.asarray(global_sigma, dtype=float)
    span = max(int(floor) - int(hard_min), 1)
    out_s, out_p, out_l, out_m = {}, {}, {}, {}
    for r, Sig in regime_sigma.items():
        S = np.asarray(Sig, dtype=float)
        n = int(obs_counts.get(r, 0))
        if n >= floor:
            lam, mode, Sp = 1.0, "keep", S
        elif n >= hard_min:
            lam = float(np.clip((n - hard_min) / span, 0.0, 1.0))
            mode = "shrink"
            Sp = lam * S + (1.0 - lam) * G
        else:
            lam, mode, Sp = 0.0, "fallback", G
        Sp = 0.5 * (Sp + Sp.T)
        out_s[r] = Sp
        out_l[r] = lam
        out_m[r] = mode
        try:
            out_p[r] = np.linalg.inv(Sp)
        except np.linalg.LinAlgError:
            out_p[r] = np.linalg.pinv(Sp)
    return RegimeShrinkResult(sigma=out_s, precision=out_p, lam_local=out_l, mode=out_m)


# ===========================================================================
# self-test
# ===========================================================================

if __name__ == "__main__":
    # 1) factor-implied cross-sleeve: 같은 팩터 노출 sleeve 는 양의 공분산
    betas = {
        "eq_us": [1.0, -0.3, 0.2, 0.5],     # rate, dollar, oil, credit beta
        "eq_intl": [0.8, 0.6, 0.1, 0.4],    # dollar beta 부호 반대(자문: intl)
        "gold": [-0.5, -0.8, 0.0, -0.2],
    }
    Lam = np.diag([0.04, 0.02, 0.03, 0.05])      # 팩터 분산(대각 가정)
    res = factor_implied_cross_cov(betas, Lam, factors=["rate", "dollar", "oil", "credit"],
                                   idio_var={"eq_us": 0.02, "eq_intl": 0.03, "gold": 0.05})
    assert res.cov.shape == (3, 3)
    w = np.linalg.eigvalsh(res.cov)
    assert np.all(w > 0), f"PD 위반: {w}"
    # eq_us vs eq_intl: rate 동방향(+,+) → 양의 systematic 공분산 기대
    i_us, i_intl, i_gold = 0, 1, 2
    assert res.cov[i_us, i_intl] > 0
    # gold 는 rate/dollar 반대 노출 → eq_us 와 음의 공분산
    assert res.cov[i_us, i_gold] < 0
    print(f"1) factor-implied cross-cov OK: PD✓ eqUS·intl={res.cov[i_us,i_intl]:+.4f}(+) "
          f"eqUS·gold={res.cov[i_us,i_gold]:+.4f}(-)")

    # 2) 빈 입력 graceful
    empty = factor_implied_cross_cov({}, Lam)
    assert empty.cov.shape == (0, 0)
    print(f"2) 빈 sleeve graceful OK")

    # 3) regime obs floor: keep / shrink / fallback 3-mode
    p = 3
    rng = np.random.default_rng(1)
    def _pd(scale):
        A = rng.normal(size=(p, p)) * scale
        return A @ A.T + np.eye(p)
    regime_sigma = {0: _pd(1.0), 1: _pd(1.5), 2: _pd(2.0)}
    G = _pd(1.2)
    obs = {0: 50, 1: 20, 2: 5}    # keep / shrink / fallback
    sr = regime_obs_floor_shrink(regime_sigma, obs, G, floor=30, hard_min=10)
    assert sr.mode == {0: "keep", 1: "shrink", 2: "fallback"}, sr.mode
    assert sr.lam_local[0] == 1.0 and sr.lam_local[2] == 0.0
    assert 0.0 < sr.lam_local[1] < 1.0
    # fallback regime 은 global 과 동일
    assert np.allclose(sr.sigma[2], 0.5 * (G + G.T))
    # keep regime 은 원본
    assert np.allclose(sr.sigma[0], 0.5 * (regime_sigma[0] + regime_sigma[0].T))
    # shrink 결과 PD
    for r in sr.sigma:
        assert np.all(np.linalg.eigvalsh(sr.sigma[r]) > 0), f"regime {r} PD 위반"
        assert np.allclose(sr.precision[r] @ sr.sigma[r], np.eye(p), atol=1e-6)
    print(f"2.5) regime obs floor OK: modes={sr.mode} λ1={sr.lam_local[1]:.3f} (PD+precision 일치)")

    # 4) floor 경계: n=floor → keep, n=floor-1 → shrink
    sr2 = regime_obs_floor_shrink({0: _pd(1.0), 1: _pd(1.0)}, {0: 30, 1: 29}, G,
                                  floor=30, hard_min=10)
    assert sr2.mode[0] == "keep" and sr2.mode[1] == "shrink"
    print(f"4) floor 경계(30=keep / 29=shrink) OK")

    print("\nsystem_priors self-test PASS "
          "(factor-implied cross-cov PD + 부호 + regime obs floor 3-mode shrink/fallback PD)")
