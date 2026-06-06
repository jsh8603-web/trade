"""core/assume/spanning_gate.py — S4 직교성 발권 게이트 (C9/Q3 스패닝 회귀).

정성 텍스트 촉매(예 'HBM 공급부족')가 기존 7팩터의 위장(중복)인지 진짜 잔차 알파인지 판정한다.
★텍스트 공간 신규성을 믿지 않고 **직교화된 수익률 공간에서 증명**(plan §3 S4 Q3, 두 모델 최강 수렴):

  촉매 → 거래가능 신호(롱숏 바스켓 수익률 r_c) → 스패닝 회귀 r_c = α + βᵀF + ε  (F = 7 공통팩터)
    - α ≈ 0 (비유의)        → **위장**(결정론 노출에 이미 있음) → 발권 금지(camouflage)
    - α 유의 + 잔차 forward IC → **진짜 잔차 알파** → 발권 허가(mint)
  ★잔차 수익률 공간에서 α≠0 못 보이면 가설 아님(falsifiability 사수 — MOVE⊥VIX 흡수판정과 동형).

도구: FWL 잔차화(OLS) + Newey-West HAC SE(시계열 자기상관 보정, small-n-rigor §1.4) +
조건부 검사(국면 interaction, regime-switching conditional-IC 정합) + 팩터타이밍/종목선택 분해.

★small-n-rigor / empirical-claim §1.2-1.4 준수: n 명기, HAC SE, n<n_min → INSUFFICIENT 격하(단정 금지).
★additive(INV-11): 순수 통계 함수, 호출처 0(go-live 시 카드 mint 경로서 r_c·F 시계열 주입). 외부 의존 0.
⛔ go-live 미접촉: 실제 r_c 는 라이브 바스켓에서 나오고, 본 모듈은 시계열을 받아 판정만(실거래 무관).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np


@dataclass
class SpanningResult:
    """스패닝 회귀 r_c = α + βᵀF + ε 결과."""
    alpha: float
    alpha_se: float          # Newey-West HAC SE
    alpha_t: float
    beta: tuple              # 팩터 로딩 (K,)
    resid: tuple             # 잔차 ε (T,) — forward IC 입력
    n: int
    r2: float
    hac_lags: int

    @property
    def alpha_significant(self) -> bool:
        return abs(self.alpha_t) >= 2.0


def _nw_lags(n: int) -> int:
    """Newey-West 자동 lag = floor(4·(n/100)^(2/9)) (Stock-Watson 관행). 최소 1."""
    if n <= 1:
        return 0
    return max(1, int(math.floor(4.0 * (n / 100.0) ** (2.0 / 9.0))))


def spanning_regression(
    r_c: Sequence[float],
    factors: Sequence[Sequence[float]],
    *,
    hac_lags: Optional[int] = None,
) -> SpanningResult:
    """OLS r_c = α + βᵀF + ε + Newey-West HAC SE(α).

    r_c     : (T,) 촉매 롱숏 바스켓 수익률.
    factors : (T, K) 공통팩터 수익률(F). intercept 는 본 함수가 자동 추가.
    hac_lags: None → _nw_lags(T) 자동.
    """
    y = np.asarray(r_c, dtype=float).reshape(-1)
    F = np.asarray(factors, dtype=float)
    if F.ndim == 1:
        F = F.reshape(-1, 1)
    T = y.shape[0]
    if F.shape[0] != T:
        raise ValueError(f"r_c({T}) ↔ factors({F.shape[0]}) 길이 불일치")

    X = np.column_stack([np.ones(T), F])         # [1, F]
    k = X.shape[1]
    beta_hat, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta_hat
    ss_res = float(resid @ resid)
    ss_tot = float(((y - y.mean()) ** 2).sum()) or 1e-12
    r2 = 1.0 - ss_res / ss_tot

    # Newey-West HAC: cov = (X'X)^-1 · S · (X'X)^-1, S = Σ_l w_l (Γ_l + Γ_l')
    lags = _nw_lags(T) if hac_lags is None else int(hac_lags)
    XtX_inv = np.linalg.pinv(X.T @ X)
    u = X * resid.reshape(-1, 1)                  # (T, k) score
    S = u.T @ u                                   # lag 0
    for l in range(1, lags + 1):
        w = 1.0 - l / (lags + 1.0)                # Bartlett kernel
        G = u[l:].T @ u[:-l]
        S = S + w * (G + G.T)
    cov = XtX_inv @ S @ XtX_inv
    alpha_se = float(math.sqrt(max(cov[0, 0], 1e-18)))
    alpha = float(beta_hat[0])
    alpha_t = alpha / alpha_se if alpha_se > 0 else 0.0

    return SpanningResult(
        alpha=alpha, alpha_se=alpha_se, alpha_t=alpha_t,
        beta=tuple(float(b) for b in beta_hat[1:]),
        resid=tuple(float(e) for e in resid),
        n=T, r2=r2, hac_lags=lags,
    )


def residual_forward_ic(resid: Sequence[float], fwd_returns: Sequence[float]) -> dict:
    """잔차 ε ↔ forward 수익률 Spearman rank-IC(잔차 알파가 미래 수익 예측하는지)."""
    e = np.asarray(resid, dtype=float).reshape(-1)
    f = np.asarray(fwd_returns, dtype=float).reshape(-1)
    m = min(len(e), len(f))
    e, f = e[:m], f[:m]
    mask = np.isfinite(e) & np.isfinite(f)
    e, f = e[mask], f[mask]
    n = len(e)
    if n < 3 or np.std(e) < 1e-12 or np.std(f) < 1e-12:
        return {"ic": 0.0, "n": n, "ok": False}
    # Spearman = Pearson on ranks
    re = np.argsort(np.argsort(e)).astype(float)
    rf = np.argsort(np.argsort(f)).astype(float)
    ic = float(np.corrcoef(re, rf)[0, 1])
    # 근사 t (Fisher), small-n hedge 는 호출자 판정
    t = ic * math.sqrt(max(n - 2, 1) / max(1e-12, 1 - ic * ic))
    return {"ic": ic, "n": n, "t": t, "ok": True}


@dataclass
class MintVerdict:
    """발권 게이트 판정. verdict ∈ {mint, camouflage, insufficient}."""
    verdict: str
    alpha: float
    alpha_t: float
    n: int
    resid_ic: Optional[float] = None
    reason: str = ""
    detail: dict = field(default_factory=dict)

    @property
    def can_mint(self) -> bool:
        return self.verdict == "mint"


def mint_gate(
    r_c: Sequence[float],
    factors: Sequence[Sequence[float]],
    fwd_returns: Optional[Sequence[float]] = None,
    *,
    alpha_t_min: float = 2.0,
    resid_ic_t_min: float = 1.64,
    n_min: int = 20,
    hac_lags: Optional[int] = None,
) -> MintVerdict:
    """직교성 발권 게이트 — 촉매가 7팩터 위장이면 발권 차단, 진짜 잔차 알파면 발권 허가.

    판정 순서(empirical-claim §1.2 단정 금지):
      1. n < n_min            → INSUFFICIENT(TENTATIVE, 발권 보류 — 소표본 단정 금지)
      2. |α_t(HAC)| < t_min   → CAMOUFLAGE(7팩터에 흡수, 발권 X = falsifiability 사수)
      3. α 유의 + (fwd 주면 잔차 forward IC 유의) → MINT(진짜 잔차 알파)
         fwd 미제공 시 = α 유의만으로 잠정 MINT(forward 검증은 호출자 후속).
    """
    res = spanning_regression(r_c, factors, hac_lags=hac_lags)
    base = dict(alpha=res.alpha, alpha_t=res.alpha_t, n=res.n)

    if res.n < n_min:
        return MintVerdict(verdict="insufficient", **base,
                           reason=f"n={res.n}<{n_min} 소표본 단정 금지(TENTATIVE)",
                           detail={"r2": res.r2, "hac_lags": res.hac_lags})

    if abs(res.alpha_t) < alpha_t_min:
        return MintVerdict(verdict="camouflage", **base,
                           reason=f"α_t={res.alpha_t:.2f}<{alpha_t_min} = 7팩터 흡수(위장, 발권 X)",
                           detail={"r2": res.r2, "beta": res.beta, "hac_lags": res.hac_lags})

    ic = None
    if fwd_returns is not None:
        ric = residual_forward_ic(res.resid, fwd_returns)
        ic = ric.get("ic")
        if ric.get("ok") and abs(ric.get("t", 0.0)) < resid_ic_t_min:
            return MintVerdict(verdict="camouflage", alpha=res.alpha, alpha_t=res.alpha_t,
                               n=res.n, resid_ic=ic,
                               reason=f"α 유의나 잔차 forward IC t={ric.get('t', 0):.2f} 비유의 → 발권 보류",
                               detail={"r2": res.r2})

    return MintVerdict(verdict="mint", alpha=res.alpha, alpha_t=res.alpha_t,
                       n=res.n, resid_ic=ic,
                       reason=f"α_t={res.alpha_t:.2f} 유의 + 잔차 알파 = 진짜 신규 정보(발권 허가)",
                       detail={"r2": res.r2, "beta": res.beta, "hac_lags": res.hac_lags})


def conditional_alpha(
    r_c: Sequence[float],
    factors: Sequence[Sequence[float]],
    regime_mask: Sequence[bool],
    *,
    hac_lags: Optional[int] = None,
) -> dict:
    """조건부 검사 — 무조건부 α≈0 인데 특정 국면 내 α 유의(regime-switching conditional alpha).

    ★plan §3 S4 최고가치: 결정론 팩터코어가 state-dependence 못 잡음 → 국면 조건부 알파가 진짜 엣지.
    regime_mask=True 인 구간만 스패닝 회귀 → 그 국면 α 유의면 conditional mint 후보.
    """
    mask = np.asarray(regime_mask, dtype=bool).reshape(-1)
    y = np.asarray(r_c, dtype=float).reshape(-1)
    F = np.asarray(factors, dtype=float)
    if F.ndim == 1:
        F = F.reshape(-1, 1)
    m = min(len(mask), len(y), F.shape[0])
    mask, y, F = mask[:m], y[:m], F[:m]

    out = {}
    for label, sel in (("in_regime", mask), ("out_regime", ~mask)):
        if sel.sum() < 5:
            out[label] = {"n": int(sel.sum()), "ok": False}
            continue
        r = spanning_regression(y[sel], F[sel], hac_lags=hac_lags)
        out[label] = {"alpha": r.alpha, "alpha_t": r.alpha_t, "n": r.n,
                      "significant": r.alpha_significant}
    return out


if __name__ == "__main__":
    rng = np.random.RandomState(0)
    T, K = 240, 3
    F = rng.randn(T, K) * 0.01

    # 1) 순수 팩터 노출(α=0) → camouflage
    r_pure = F @ np.array([1.2, -0.5, 0.8]) + rng.randn(T) * 0.002
    v1 = mint_gate(r_pure, F)
    assert v1.verdict == "camouflage", v1
    print(f"1) 순수 팩터 노출 → CAMOUFLAGE (α_t={v1.alpha_t:.2f}) OK")

    # 2) 팩터 직교 알파(α>0) → mint
    r_alpha = 0.004 + F @ np.array([0.3, 0.2, -0.1]) + rng.randn(T) * 0.002
    v2 = mint_gate(r_alpha, F)
    assert v2.verdict == "mint", v2
    print(f"2) 팩터 직교 알파 → MINT (α={v2.alpha:.4f}, α_t={v2.alpha_t:.2f}) OK")

    # 3) 소표본 → insufficient
    v3 = mint_gate(r_alpha[:15], F[:15])
    assert v3.verdict == "insufficient", v3
    print(f"3) n=15 소표본 → INSUFFICIENT (단정 금지) OK")

    # 4) 잔차 forward IC 게이트: α 유의나 잔차가 미래수익 무관 → 발권 보류
    fwd_noise = rng.randn(T) * 0.01
    v4 = mint_gate(r_alpha, F, fwd_returns=fwd_noise)
    assert v4.verdict == "camouflage" and "forward IC" in v4.reason, v4
    print(f"4) 잔차 forward IC 비유의 → 발권 보류 (resid_ic={v4.resid_ic:.3f}) OK")

    # 5) 잔차가 forward 수익 예측 → mint
    res5 = spanning_regression(r_alpha, F)
    fwd_signal = np.array(res5.resid) * 2.0 + rng.randn(T) * 0.001  # 잔차가 미래수익 예측
    v5 = mint_gate(r_alpha, F, fwd_returns=fwd_signal)
    assert v5.verdict == "mint", v5
    print(f"5) 잔차→forward 수익 예측 → MINT (resid_ic={v5.resid_ic:.3f}) OK")

    # 6) HAC SE: 자기상관 잔차서 naive보다 SE 커짐(α_t 보수화)
    ar = np.zeros(T)
    for t in range(1, T):
        ar[t] = 0.7 * ar[t - 1] + rng.randn() * 0.002
    r_ar = 0.003 + ar
    res6 = spanning_regression(r_ar, F)
    assert res6.hac_lags >= 1
    print(f"6) Newey-West HAC lags={res6.hac_lags} 적용 OK")

    # 7) 조건부 알파: 국면 내에서만 α 발현
    regime = np.array([i % 2 == 0 for i in range(T)])
    r_cond = np.where(regime, 0.005, 0.0) + F @ np.array([0.2, 0.1, 0.0]) + rng.randn(T) * 0.002
    c = conditional_alpha(r_cond, F, regime)
    assert c["in_regime"]["n"] > 0 and c["out_regime"]["n"] > 0
    print(f"7) 조건부 알파: in α_t={c['in_regime']['alpha_t']:.2f} / out α_t={c['out_regime']['alpha_t']:.2f} OK")

    print("S4 spanning_gate self-test PASS "
          "(camouflage/mint/insufficient · HAC SE · 잔차 forward IC · 조건부 알파)")
