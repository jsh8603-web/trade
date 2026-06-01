"""core/study/factor_shadow.py — M4 거시-종목 factor 통합: shadow validation (골격 M4-c).

cross-sleeve factor 모델 Σ_model = B·Λ·Bᵀ + diag(idio) 가 실현 cross-sleeve 공분산을 OOS 로 추종하는지
**로깅만** 검증한다(자문 3R §6, CONSULT-DECISIONS-M4-factor-integration-20260530.md).

⛔★격리 불변식(자문 §1 — Claude 교정): 본 모듈은 **순수 함수**다. 어떤 production 상태(RNG·cov 캐시·
파일 IO·registry)도 write 하지 않는다. 따라서 risk gate/배분 경로가 본 모듈을 호출하든 안 하든 production
출력은 byte-identical(off-path). risk gate wiring(M5)에서 shadow 를 호출할 때도 "결과 로깅만, 결정 미반영"
을 유지하고 on/off diff=0 을 회귀로 박제해야 한다(공유 상태 경유 간접 drift 차단).

합격 metric(사전 고정, 자문 §6):
- 1차(합격판정) = bias statistic on decision portfolios: √(wᵀΣ_model w) / realized vol, 밴드 [0.9,1.1].
  게이트가 실제 소비하는 양(포트 위험)을 검증(Barra B-stat). Frobenius/corr-of-corr 보다 decision-relevant.
- 2차(구조) = 지배 eigenvector cosine alignment |v₁·v₁^realized| > 0.9. dollar dominance 직접 검정 —
  안 맞으면 dominance 스토리가 틀린 것.
- Frobenius / corr-of-corr = monitor 만(scale-dominated / decision-weight 없음, 합격선 부적합).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


_BIAS_BAND = (0.9, 1.1)          # bias statistic 합격 밴드(자문 §6).
_EIGVEC_COS_MIN = 0.9            # 지배 eigenvector cosine 합격선.


@dataclass
class ShadowReport:
    """shadow validation 산출(로깅 전용 — 어떤 결정에도 미반영)."""
    bias_by_portfolio: dict          # 포트명 → bias statistic(√(wᵀΣ_model w)/realized vol)
    bias_pass: bool                  # 모든 테스트 포트가 밴드 내
    eigvec_cosine: float             # 지배 eigenvector |cos|
    eigvec_pass: bool
    frobenius_corr: float            # monitor(상대 Frobenius, 상관행렬)
    overall_pass: bool
    note: str = ""


def _test_portfolios(sleeves: list, betas: dict, factor: str = "dollar") -> dict:
    """decision portfolios(자문 §6): dollar-mimicking / equal-weight / 집중. 합=0 또는 1 정규화."""
    n = len(sleeves)
    ports: dict = {}
    # equal-weight cross-sleeve(분산 포트)
    ports["equal_weight"] = np.full(n, 1.0 / n)
    # dollar-mimicking: dollar 노출 부호로 long-short(동조 위험 최대 노출)
    fidx = ("rate", "dollar", "oil", "credit").index(factor)
    expo = np.array([betas[s][fidx] for s in sleeves], dtype=float)
    if np.any(expo != 0):
        w = -np.sign(expo)               # dollar 강세 시 동반 하락하는 방향으로 집중
        ports["dollar_mimicking"] = w / np.sum(np.abs(w))
    # 집중(첫 sleeve 단독) — under-detection 점검
    conc = np.zeros(n); conc[0] = 1.0
    ports["concentrated"] = conc
    return ports


def bias_statistic(w: np.ndarray, sigma_model: np.ndarray, sigma_realized: np.ndarray) -> float:
    """√(wᵀΣ_model w) / √(wᵀΣ_realized w). 1=완벽, >1=모델 과대예측, <1=과소(위험)."""
    pm = float(w @ sigma_model @ w)
    pr = float(w @ sigma_realized @ w)
    if pr <= 0:
        return float("nan")
    return float(np.sqrt(max(pm, 0.0) / pr))


def dominant_eigvec_cosine(sigma_model: np.ndarray, sigma_realized: np.ndarray) -> float:
    """두 공분산의 지배(top) eigenvector cosine 절댓값. dollar dominance 구조 일치 검정."""
    wm, Vm = np.linalg.eigh(sigma_model)
    wr, Vr = np.linalg.eigh(sigma_realized)
    v1m = Vm[:, int(np.argmax(wm))]
    v1r = Vr[:, int(np.argmax(wr))]
    return float(abs(v1m @ v1r) / (np.linalg.norm(v1m) * np.linalg.norm(v1r)))


def _rel_frobenius_corr(sigma_model: np.ndarray, sigma_realized: np.ndarray) -> float:
    """monitor 용 — 상관행렬 상대 Frobenius 거리(scale-free)."""
    def _corr(S):
        d = np.sqrt(np.clip(np.diag(S), 1e-12, None))
        return S / np.outer(d, d)
    cm, cr = _corr(sigma_model), _corr(sigma_realized)
    return float(np.linalg.norm(cm - cr, ord="fro") / max(np.linalg.norm(cr, ord="fro"), 1e-12))


def run_shadow(sleeves: list, betas: dict, sigma_model: np.ndarray,
               sigma_realized: np.ndarray, *, factor: str = "dollar") -> ShadowReport:
    """shadow validation 실행 — 로깅 전용 ShadowReport 반환(★production 상태 write 없음).

    sigma_model: B·Λ·Bᵀ+diag(idio)(factor_implied_cross_cov 산출). sigma_realized: 실현 sleeve 표본공분산.
    """
    Sm = np.asarray(sigma_model, dtype=float)
    Sr = np.asarray(sigma_realized, dtype=float)
    ports = _test_portfolios(sleeves, betas, factor=factor)
    bias = {name: bias_statistic(w, Sm, Sr) for name, w in ports.items()}
    bias_pass = all(_BIAS_BAND[0] <= b <= _BIAS_BAND[1]
                    for b in bias.values() if np.isfinite(b))
    cos = dominant_eigvec_cosine(Sm, Sr)
    eig_pass = cos > _EIGVEC_COS_MIN
    frob = _rel_frobenius_corr(Sm, Sr)
    overall = bias_pass and eig_pass
    note = "PASS" if overall else (
        f"FAIL({'bias ' if not bias_pass else ''}{'eigvec' if not eig_pass else ''})")
    return ShadowReport(bias_by_portfolio=bias, bias_pass=bias_pass, eigvec_cosine=cos,
                        eigvec_pass=eig_pass, frobenius_corr=frob, overall_pass=overall, note=note)


# ===========================================================================
# self-test
# ===========================================================================
if __name__ == "__main__":
    from core.study.factor_betas_seed import build_seed_betas
    from core.study.system_priors import factor_implied_cross_cov

    Lam = np.diag([0.04, 0.05, 0.03, 0.05])
    sb = build_seed_betas(factor_cov=Lam)
    res = factor_implied_cross_cov(sb.betas, Lam, factors=list(sb.factors), idio_var=sb.idio_var)
    Sm = res.cov
    sleeves = res.sleeves

    # 1) realized = model 과 정합(같은 factor 구조에서 생성) → bias≈1, cosine>0.9 → PASS
    rng = np.random.default_rng(11)
    L = np.linalg.cholesky(Sm + 1e-9 * np.eye(len(sleeves)))
    sims = (rng.normal(size=(4000, len(sleeves))) @ L.T)
    Sr_good = np.cov(sims, rowvar=False)
    rep_good = run_shadow(sleeves, sb.betas, Sm, Sr_good)
    assert rep_good.overall_pass, f"정합 케이스 FAIL: {rep_good}"
    print(f"1) 정합 shadow PASS: bias={ {k: round(v,3) for k,v in rep_good.bias_by_portfolio.items()} } "
          f"eigvec cos={rep_good.eigvec_cosine:.3f} frob={rep_good.frobenius_corr:.3f}")

    # 2) realized 가 model 과 크게 다름(무상관 + 큰 분산) → bias·eigvec 불합격 감지
    Sr_bad = np.diag(np.diag(Sm) * 4.0)        # 분산 4배 + 공분산 0(동조 구조 파괴)
    rep_bad = run_shadow(sleeves, sb.betas, Sm, Sr_bad)
    assert not rep_bad.overall_pass, "불일치인데 PASS(검출 실패)"
    print(f"2) 불일치 shadow FAIL 검출 OK: {rep_bad.note} "
          f"bias_pass={rep_bad.bias_pass} eigvec_pass={rep_bad.eigvec_pass}(cos={rep_bad.eigvec_cosine:.3f})")

    # 3) ★격리: run_shadow 는 입력을 변형하지 않음(순수 함수 — off-path byte-identical 근거)
    Sm_before = Sm.copy()
    betas_before = {k: list(v) for k, v in sb.betas.items()}
    _ = run_shadow(sleeves, sb.betas, Sm, Sr_good)
    assert np.array_equal(Sm, Sm_before), "Σ_model 변형됨(격리 위반)"
    assert all(sb.betas[k] == betas_before[k] for k in betas_before), "betas 변형됨(격리 위반)"
    print(f"3) ★격리 OK: run_shadow 입력 불변(Σ_model·betas 미변형) = production 상태 write 없음(off-path 근거)")

    # 4) bias statistic 단위 검증: 동일 행렬이면 정확히 1.0
    w = np.full(len(sleeves), 1.0 / len(sleeves))
    assert abs(bias_statistic(w, Sm, Sm) - 1.0) < 1e-9
    print(f"4) bias statistic 단위 OK: 동일행렬 bias=1.0")

    print("\nfactor_shadow self-test PASS "
          "(bias statistic[0.9,1.1] + 지배 eigenvector cosine>0.9 + 불일치 FAIL 검출 + ★순수함수 격리)")
