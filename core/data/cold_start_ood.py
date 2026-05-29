"""core/data/cold_start_ood.py — cold-start OOD 감지 (R15 §4-5·§1.9).

CONSULT-DECISIONS-weight-20260529.md §1.9 (btn-Inv 분담).

신규 지표/국면 = regime 불확실성 극단. 두 축으로 out-of-distribution(OOD)을 감지한다:
  ① **calibrated max-belief < θ**: regime classifier(calibration 후, btn-button)가 어느
     regime 에도 충분히 확신 못함 = 전이/미지 국면. raw softmax 아닌 **calibrated** posterior
     입력(§1.6: raw 는 boundary 과신).
  ② **Mahalanobis 밖**: 현재 feature 가 모든 regime centroid 에서 통계적으로 멀다(학습 분포
     밖). d²=(x−μ)ᵀΩ(x−μ), Ω=precision(btn-button EB-shrunk). 최소 거리 > χ²(p, 1−α) → OOD.

★live override 아님(§1.9): 본 모듈은 **감지 신호(데이터)만** 산출 — live score 미접촉.
  OOD default 동작 = belief 기계가 알아서 de-risk(high-entropy belief→between-cov 폭발→
  w 분산·floor·1/N 강등, 사람 결정 0). 신규지표 양의 weight 부여는 offline·pre-registered·
  prior-space override(§1.9 (b))뿐 — 그건 btn-Codlearn 게이트. 여기는 OOD 여부 boolean.

순수 numpy/scipy — 추정/calibration 자체는 범위 밖(btn-button).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence, Union

import numpy as np
from scipy.stats import chi2


@dataclass
class OODResult:
    """cold-start OOD 판정. is_ood=True 면 belief 기계 de-risk 경로(데이터 신호)."""
    is_ood: bool
    reason: str               # "" | "low_belief" | "mahalanobis" | "low_belief+mahalanobis"
    max_belief: float
    min_mahalanobis_sq: float  # 가장 가까운 regime centroid 까지 d²
    chi2_threshold: float      # χ²(p, 1−α)
    nearest_regime: object = None


def mahalanobis_sq(x: np.ndarray, mu: np.ndarray, precision: np.ndarray) -> float:
    """d² = (x−μ)ᵀ Ω (x−μ). Ω=precision(공분산 역행렬, EB-shrunk 입력 가정)."""
    d = np.asarray(x, dtype=float) - np.asarray(mu, dtype=float)
    return float(d @ np.asarray(precision, dtype=float) @ d)


def max_belief_ood(belief: Sequence[float], theta: float = 0.5) -> bool:
    """calibrated max-belief < θ 면 True(어느 regime 에도 확신 없음 = 전이/미지)."""
    b = np.asarray(belief, dtype=float)
    if b.size == 0:
        return True
    return float(b.max()) < theta


def detect_cold_start_ood(
    belief: Sequence[float],
    feature: Sequence[float],
    centroids: Mapping,                 # {regime_label: mean_vector}
    precisions: Union[Mapping, np.ndarray],  # {label: precision} 또는 공통 precision 1개
    *,
    theta: float = 0.5,
    chi2_alpha: float = 0.01,
) -> OODResult:
    """① max-belief<θ OR ② min Mahalanobis > χ²(p,1−α) → OOD. reason 에 발동 축 기록.

    precisions 가 단일 행렬이면 모든 regime 공유. centroids 비면 Mahalanobis 축 skip(belief만).
    """
    x = np.asarray(feature, dtype=float)
    p = x.shape[0]
    thr = float(chi2.ppf(1.0 - chi2_alpha, df=p))

    mb = float(np.asarray(belief, dtype=float).max()) if len(belief) else 0.0
    low_belief = mb < theta

    min_d = float("inf")
    nearest = None
    for lab, mu in centroids.items():
        prec = precisions[lab] if isinstance(precisions, Mapping) else precisions
        d2 = mahalanobis_sq(x, mu, prec)
        if d2 < min_d:
            min_d, nearest = d2, lab
    maha_ood = (min_d > thr) if centroids else False

    reasons = []
    if low_belief:
        reasons.append("low_belief")
    if maha_ood:
        reasons.append("mahalanobis")
    return OODResult(
        is_ood=bool(low_belief or maha_ood),
        reason="+".join(reasons),
        max_belief=mb, min_mahalanobis_sq=min_d, chi2_threshold=thr,
        nearest_regime=nearest,
    )


if __name__ == "__main__":
    rng = np.random.default_rng(42)

    # 2 regime, 3-dim feature. centroid 와 단위 precision(공분산=I 가정)
    centroids = {"risk_on": np.array([0.0, 0.0, 0.0]),
                 "risk_off": np.array([5.0, 5.0, 5.0])}
    prec = np.eye(3)   # 공통 precision (Σ=I)

    # 1) max-belief OOD: 평평한 belief(0.34/0.33/0.33) → max<θ=0.5 → OOD
    assert max_belief_ood([0.34, 0.33, 0.33], theta=0.5) is True
    assert max_belief_ood([0.8, 0.15, 0.05], theta=0.5) is False
    print("1) max-belief OOD: uniform(max 0.34)<0.5=OOD / peaked(0.8)=in-dist OK")

    # 2) Mahalanobis OOD: risk_on centroid 근처(확신) = in-dist / 둘 다서 먼 점 = OOD
    near = detect_cold_start_ood([0.9, 0.1], [0.3, -0.2, 0.1], centroids, prec,
                                 theta=0.5, chi2_alpha=0.01)
    assert not near.is_ood and near.nearest_regime == "risk_on", near
    far = detect_cold_start_ood([0.9, 0.1], [50.0, -40.0, 30.0], centroids, prec,
                                theta=0.5, chi2_alpha=0.01)
    assert far.is_ood and "mahalanobis" in far.reason, far
    print(f"2) Mahalanobis: centroid 근처={near.min_mahalanobis_sq:.1f}<thr / "
          f"먼 점={far.min_mahalanobis_sq:.0f}>thr({far.chi2_threshold:.1f})=OOD OK")

    # 3) 통합: confident + in-dist = not OOD / low belief 만 = OOD(low_belief)
    ok = detect_cold_start_ood([0.85, 0.15], [0.1, 0.1, 0.1], centroids, prec)
    assert not ok.is_ood and ok.reason == "", ok
    lb = detect_cold_start_ood([0.4, 0.35, 0.25], [0.1, 0.1, 0.1], centroids, prec)
    assert lb.is_ood and lb.reason == "low_belief", lb
    print("3) 통합: confident+in-dist=not OOD / low-belief(max 0.4)=OOD(low_belief) OK")

    # 4) 두 축 동시: 평평 belief + 먼 feature → reason=low_belief+mahalanobis
    both = detect_cold_start_ood([0.34, 0.33, 0.33], [40.0, 40.0, 40.0], centroids, prec)
    assert both.is_ood and both.reason == "low_belief+mahalanobis", both
    print(f"4) 두 축 동시: reason='{both.reason}' OK")

    # 5) χ² threshold dim 정합: df=3, α=0.01 → chi2.ppf(0.99,3)
    expected = float(chi2.ppf(0.99, df=3))
    assert abs(both.chi2_threshold - expected) < 1e-9, both.chi2_threshold
    print(f"5) χ² threshold(df=3, α=0.01)={both.chi2_threshold:.3f} 정합 OK")

    # 6) per-regime precision(dict) + nearest 식별: risk_off 쪽이 더 가까운 점
    precs = {"risk_on": np.eye(3), "risk_off": np.eye(3) * 0.5}
    r = detect_cold_start_ood([0.6, 0.4], [4.8, 5.1, 4.9], centroids, precs)
    assert r.nearest_regime == "risk_off", r.nearest_regime
    print(f"6) per-regime precision dict + nearest={r.nearest_regime} OK")

    print("cold_start_ood (calibrated max-belief + Mahalanobis OOD) self-test PASS")
