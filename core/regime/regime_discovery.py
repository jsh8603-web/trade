"""core/regime/regime_discovery.py — BB-3: open-ended regime 발견 + 사람비준 gate.

DESIGN-button-v2.md §4 / §10.1. pit_regime 은 고정-K3. 본 모듈 = 기존에 정의 안 된 새 거시 regime
을 online 발견. 자문 R1·R3·R4 수렴 반영 (numpy-only, bnpy/ruptures 미설치 graceful):
- DP-mixture 폐기 (numpy 불안정). 결정론 휴리스틱.
- BOCPD(detectors.Bocpd, 1-D 요약) = **timing trigger** / novelty 판정은 **full 다변량**.
- novelty = **Hotelling T² / Mahalanobis² vs χ²_d 분위** (σ 아님). nearest known center 대비.
- 후보발행 = **online-FDR(LordPlusPlus) wrap** (희소 이벤트 FDR 보장).
- false-discovery: min-dwell + time-separation(과거 무재현) + economic-overlay(선택 콜백).
- 발견 자동, **승격 사람 (HumanApprovalGate)** — regime = base-layer 가정 (claude C-meta).
- 재현 K회 = booster only (kill 조건 아님 — COVID식 일회성 진짜 regime 보호).
- bnpy seam: 설치 시 sticky-HDP-HMM birth move 위임 (미설치 = numpy fallback).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np

from core.structure.detectors import Bocpd
from core.structure.online_fdr import LordPlusPlus
from core.structure.hierarchical_fdr import EProcessSpender


def chi2_quantile(df: int, p: float) -> float:
    """χ²_df 의 p-분위 (Wilson-Hilferty 근사, scipy 불필요)."""
    # 표준정규 분위 (Acklam 근사 간략 — p=0.95/0.99 영역 정확)
    z = _normal_ppf(p)
    t = 1.0 - 2.0 / (9.0 * df) + z * math.sqrt(2.0 / (9.0 * df))
    return float(df * t ** 3)


def _normal_ppf(p: float) -> float:
    """표준정규 역CDF (Beasley-Springer-Moro 근사)."""
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    pl, ph = 0.02425, 1 - 0.02425
    if p < pl:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p <= ph:
        q = p - 0.5; r = q*q
        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)


@dataclass(frozen=True)
class CandidateRegime:
    candidate_id: str
    segment_start: int
    segment_end: int
    feature_centroid: tuple
    novelty_score: float                   # Mahalanobis² to nearest known center
    nearest_known_regime: int
    n_obs: int
    fdr_p: float
    fdr_passed: bool
    status: str = "candidate"              # ★ 자동승격 금지


@dataclass
class RegimePromotion:
    candidate_id: str
    new_label: str
    new_regime_id: int
    old_version: str
    new_version: str
    approver: str
    rationale: str
    sequestered_confirmed: bool = False    # ⑤ optimizer 미접촉 stream anytime-valid 통과 여부


@dataclass
class SequesteredVerdict:
    """⑤ optimizer 가 못 건드린 sequestered stream 의 anytime-valid 확인 결과."""
    confirmed: bool                  # e-process E_t 가 사전 threshold(1/α) 초과
    max_e_value: float
    threshold: float
    n_ticks: int


def _bump_version(base: str) -> str:
    """pit_fixedk{N}_v{M} → fixedk{N+1} (K 증가). 패턴 미매칭 시 suffix."""
    import re
    m = re.search(r"fixedk(\d+)", base)
    if m:
        return base.replace(f"fixedk{m.group(1)}", f"fixedk{int(m.group(1))+1}")
    return base + "+disc"


class OnlineRegimeDiscovery:
    """numpy-only open-ended regime 발견. bnpy 설치 시 sticky-HDP-HMM 위임 (어댑터 seam).

    known_centroids: {regime_id: np.ndarray(d)} — 기존 regime 중심 (표준화 feature 공간).
    known_covs: {regime_id: np.ndarray(d,d)} optional (없으면 단위행렬 = z-공간 Euclidean).
    """

    def __init__(
        self,
        known_centroids: dict[int, np.ndarray],
        known_covs: Optional[dict[int, np.ndarray]] = None,
        *,
        chi2_p: float = 0.99,              # novelty 임계 분위 (crypto 0.99 / macro 0.95)
        min_segment: int = 6,             # min-dwell
        hazard_lambda: float = 60.0,
        use_fdr: bool = True,
        fdr_alpha: float = 0.05,
        use_bnpy: bool = True,
    ):
        self.centroids = {int(k): np.asarray(v, float) for k, v in known_centroids.items()}
        self.covs = {int(k): np.asarray(v, float) for k, v in (known_covs or {}).items()}
        self.d = len(next(iter(self.centroids.values())))
        self.chi2_p = chi2_p
        self.threshold = chi2_quantile(self.d, chi2_p)
        self.min_segment = min_segment
        self.hazard_lambda = hazard_lambda
        self.use_fdr = use_fdr
        self._fdr = LordPlusPlus(alpha=fdr_alpha) if use_fdr else None
        self.use_bnpy = use_bnpy

    def _try_bnpy(self, X):
        """bnpy 설치 시 sticky-HDP-HMM birth move → 신규 state 후보. 미설치 None."""
        if not self.use_bnpy:
            return None
        try:
            import bnpy  # noqa: F401
        except Exception:
            return None
        return None  # bnpy 어댑터 자리 (설치 환경에서 구현; 현 환경 미설치 → numpy fallback)

    def _mahalanobis2(self, x: np.ndarray, rid: int) -> float:
        mu = self.centroids[rid]
        cov = self.covs.get(rid)
        diff = x - mu
        if cov is None:
            return float(diff @ diff)        # 단위공분산 = Euclidean²
        try:
            inv = np.linalg.pinv(cov)
        except Exception:
            return float(diff @ diff)
        return float(diff @ inv @ diff)

    def _segment_bounds(self, summary: np.ndarray) -> list[tuple]:
        """BOCPD map_run_length 급락으로 segment 경계 (1-D timing)."""
        b = Bocpd(hazard_lambda=self.hazard_lambda)
        rls = []
        for v in summary:
            b.update(float(v)); rls.append(b.map_run_length)
        # run-length reset(이전보다 급락) = 경계
        bounds, start = [], 0
        for i in range(1, len(rls)):
            if rls[i] < rls[i - 1] - 1 and rls[i] <= 2:
                bounds.append((start, i)); start = i
        bounds.append((start, len(summary)))
        return [(s, e) for s, e in bounds if e - s >= self.min_segment]

    def scan(self, X) -> list[CandidateRegime]:
        """다변량 거시 feature(행=시점, 열=feature, 표준화 가정) → CandidateRegime 목록.

        발견 자동, 적용 X (status=candidate). bnpy 가능 시 위임, 아니면 BOCPD+novelty fallback.
        """
        bn = self._try_bnpy(X)
        if bn is not None:
            return bn
        Xv = np.asarray(X, float)
        if Xv.ndim == 1:
            Xv = Xv.reshape(-1, 1)
        summary = Xv.mean(axis=1)            # 1-D 요약 (timing 용)
        cands = []
        for (s, e) in self._segment_bounds(summary):
            seg = Xv[s:e]
            centroid = seg.mean(axis=0)
            d2_by = {rid: self._mahalanobis2(centroid, rid) for rid in self.centroids}
            nearest = min(d2_by, key=d2_by.get)
            novelty = d2_by[nearest]
            if novelty <= self.threshold:
                continue                     # 기존 regime 에 충분히 가까움 → 후보 아님
            # 후보발행 = online-FDR wrap (novelty 클수록 p 작음)
            # p = P(χ²_d >= novelty) 근사 (Wilson-Hilferty 역)
            p = _chi2_sf(novelty, self.d)
            passed = True
            if self._fdr is not None:
                passed = self._fdr.test(p).reject
            if not passed:
                continue
            cands.append(CandidateRegime(
                candidate_id=f"cand_{s}_{e}",
                segment_start=s, segment_end=e,
                feature_centroid=tuple(round(float(c), 4) for c in centroid),
                novelty_score=round(novelty, 3),
                nearest_known_regime=nearest,
                n_obs=int(e - s), fdr_p=round(p, 6), fdr_passed=passed,
            ))
        return cands

    def sequestered_confirm(self, cand: CandidateRegime, X_sequestered,
                            *, alpha: float = 0.05, window: int = 6) -> SequesteredVerdict:
        """⑤ 거짓 regime 최종 방어선. 후보를 **optimizer 가 못 건드린 sequestered stream** 에서
        재평가. 각 window centroid 의 novelty(vs nearest known) → p → e-process(anytime-valid).
        E_t 가 사전 threshold 1/α 초과해야 confirmed (사후 threshold 튜닝 불가 = 과적합 차단).

        scan(발견)은 optimizable data, 승격증거는 본 stream — 분리가 핵심(자문 R3 최종 방어선).
        """
        Xs = np.asarray(X_sequestered, float)
        if Xs.ndim == 1:
            Xs = Xs.reshape(-1, 1)
        ep = EProcessSpender(alpha=alpha)
        confirmed = False
        for i in range(0, len(Xs) - window + 1, window):
            c = Xs[i:i + window].mean(axis=0)
            d2 = {rid: self._mahalanobis2(c, rid) for rid in self.centroids}
            novelty = d2[min(d2, key=d2.get)]
            p = _chi2_sf(novelty, self.d)
            if ep.test(p).reject:
                confirmed = True            # anytime-valid: 임의 정지점에서 초과 = 확정
        return SequesteredVerdict(confirmed=confirmed, max_e_value=round(ep.max_e, 3),
                                  threshold=round(1.0 / alpha, 3), n_ticks=ep.t)

    def false_positive_rate(self, rng, *, n_trials: int = 200, segment_len: int = 60,
                            base_regime: int = 0, jitter: float = 0.4) -> float:
        """⑤ 정지(stationary) 합성데이터 주입 → detector false-positive rate 정량화.
        regime 변화가 **없는** 데이터(단일 기존 중심 노이즈)에서 scan 이 후보를 '발견'하는 비율.
        stationary 에서 regime '발견' = 실거래 발견도 의심 (자문 R3). FDR 제어 시 ≲ α 기대."""
        mu = self.centroids[base_regime]
        hits = 0
        for _ in range(n_trials):
            X = rng.normal(mu, jitter, (segment_len, self.d))
            probe = OnlineRegimeDiscovery(self.centroids, self.covs or None,
                                          chi2_p=self.chi2_p, min_segment=self.min_segment,
                                          hazard_lambda=self.hazard_lambda,
                                          use_fdr=self.use_fdr,
                                          fdr_alpha=(self._fdr.alpha if self._fdr else 0.05),
                                          use_bnpy=False)
            if len(probe.scan(X)) > 0:
                hits += 1
        return float(hits / n_trials)


def _chi2_sf(x: float, df: int) -> float:
    """P(χ²_df >= x) (Wilson-Hilferty 정규근사). novelty → p-value."""
    if x <= 0:
        return 1.0
    t = (x / df) ** (1.0 / 3.0)
    mu = 1.0 - 2.0 / (9.0 * df)
    sd = math.sqrt(2.0 / (9.0 * df))
    z = (t - mu) / sd
    return float(max(1e-12, min(1.0, 1.0 - 0.5 * (1.0 + math.erf(z / math.sqrt(2.0))))))


class HumanApprovalGate:
    """발견자동·승격사람 (BB-3 / claude C-meta base-layer). regime 승격 = 사람만."""

    def __init__(self, base_version: str = "pit_fixedk3_v1", *, require_sequestered: bool = True):
        self.base_version = base_version
        self.require_sequestered = require_sequestered    # ⑤ 사전 anytime-valid 확인 의무
        self._pending: dict[str, CandidateRegime] = {}
        self.promotions: list[RegimePromotion] = []
        self.rejections: list[tuple] = []
        self._next_regime_id = 100          # 신규 regime id 시작 (기존 0~2 와 분리)

    def propose(self, cand: CandidateRegime) -> None:
        self._pending[cand.candidate_id] = cand

    def pending(self) -> list[CandidateRegime]:
        return list(self._pending.values())

    def approve(self, candidate_id: str, new_label: str, approver: str, rationale: str,
                *, sequestered: Optional[SequesteredVerdict] = None) -> RegimePromotion:
        """★ 사람만 — regime_model_version bump + 신규 regime id 발행. 의존 가정 재검증 epoch 트리거 신호.
        ⑤ require_sequestered 시 sequestered stream anytime-valid 확인(confirmed) 선행 의무 —
        사람비준만으론 부족(사후 narrative retrofit 부패 가능, 자문 R3)."""
        if not approver or not approver.strip():
            raise ValueError("승격은 사람 비준 필수 — approver 미지정 차단 (base-layer 자동변경 금지).")
        if self.require_sequestered and not (sequestered and sequestered.confirmed):
            raise ValueError("승격 차단 — sequestered stream anytime-valid 확인(e-process E≥1/α) 미통과. "
                             "사람비준+사전 threshold 둘 다 필요 (과적합/거짓 regime 방어선).")
        cand = self._pending.pop(candidate_id, None)
        if cand is None:
            raise KeyError(f"pending 후보 없음: {candidate_id}")
        new_v = _bump_version(self.base_version)
        promo = RegimePromotion(candidate_id, new_label, self._next_regime_id,
                                self.base_version, new_v, approver, rationale,
                                sequestered_confirmed=bool(sequestered and sequestered.confirmed))
        self.base_version = new_v
        self._next_regime_id += 1
        self.promotions.append(promo)
        return promo

    def reject(self, candidate_id: str, reason: str, approver: str) -> None:
        self._pending.pop(candidate_id, None)
        self.rejections.append((candidate_id, reason, approver))


if __name__ == "__main__":
    rng = np.random.default_rng(11)
    centroids = {0: np.array([0.0, 0.0]), 1: np.array([5.0, 0.0]), 2: np.array([0.0, 5.0])}

    # 1) 기존 regime 데이터만 → candidate 0 (모두 기존 중심 근처)
    disc = OnlineRegimeDiscovery(centroids, chi2_p=0.99, min_segment=6)
    Xk = np.vstack([rng.normal([0, 0], 0.4, (20, 2)),
                    rng.normal([5, 0], 0.4, (20, 2)),
                    rng.normal([0, 5], 0.4, (20, 2))])
    c_known = disc.scan(Xk)
    print(f"1) 기존 regime → candidate {len(c_known)} (0 기대)")
    assert len(c_known) == 0, [c.candidate_id for c in c_known]

    # 2) 신규 분포(먼 중심 [10,10]) 지속 segment → candidate ≥1, novelty>threshold
    disc2 = OnlineRegimeDiscovery(centroids, chi2_p=0.99, min_segment=6)
    Xn = np.vstack([rng.normal([0, 0], 0.4, (25, 2)),
                    rng.normal([10, 10], 0.4, (25, 2))])
    c_new = disc2.scan(Xn)
    print(f"2) 신규 regime → candidate {len(c_new)}, novelty={[c.novelty_score for c in c_new]} thr={disc2.threshold:.2f}")
    assert len(c_new) >= 1 and c_new[0].novelty_score > disc2.threshold
    assert c_new[0].status == "candidate"

    # ⑤a) sequestered 확인: 신규분포 sequestered stream → confirmed / 기존분포 → 미confirmed
    Xseq_new = rng.normal([10, 10], 0.4, (36, 2))      # optimizer 미접촉, 신규 regime 분포
    Xseq_known = rng.normal([0, 0], 0.4, (36, 2))      # 기존 regime 분포
    sv_new = disc2.sequestered_confirm(c_new[0], Xseq_new)
    sv_known = disc2.sequestered_confirm(c_new[0], Xseq_known)
    print(f"⑤a) sequestered: 신규 confirmed={sv_new.confirmed}(max_e={sv_new.max_e_value}) / "
          f"기존 confirmed={sv_known.confirmed}(max_e={sv_known.max_e_value}) thr={sv_new.threshold}")
    assert sv_new.confirmed is True and sv_known.confirmed is False

    # 3) 사람비준 gate — approver 없으면 차단 / sequestered 미통과 차단 / 둘 다 만족해야 승격
    gate = HumanApprovalGate(base_version="pit_fixedk3_v1")
    gate.propose(c_new[0])
    assert len(gate.pending()) == 1
    try:
        gate.approve(c_new[0].candidate_id, "ai_capex_regime", approver="", rationale="x", sequestered=sv_new)
        raise AssertionError("approver 없이 승격됨")
    except ValueError:
        print("3a) approver 없는 승격 차단 OK")
    try:
        gate.approve(c_new[0].candidate_id, "ai_capex_regime", approver="jsh", rationale="x", sequestered=sv_known)
        raise AssertionError("sequestered 미통과인데 승격됨")
    except ValueError:
        print("3b) sequestered 미통과 승격 차단 OK (사람비준만으론 부족)")
    promo = gate.approve(c_new[0].candidate_id, "ai_capex_regime", approver="jsh",
                         rationale="신규 거시 국면", sequestered=sv_new)
    print(f"3c) 승격 OK: {promo.old_version} → {promo.new_version} "
          f"(regime_id={promo.new_regime_id}, seq_confirmed={promo.sequestered_confirmed})")
    assert promo.new_version == "pit_fixedk4_v1" and gate.base_version == "pit_fixedk4_v1"
    assert promo.sequestered_confirmed and len(gate.pending()) == 0

    # 4) reject — pending 제거
    gate.propose(CandidateRegime("c2", 0, 10, (1, 1), 12.0, 0, 10, 0.001, True))
    gate.reject("c2", reason="노이즈 의심", approver="jsh")
    assert len(gate.pending()) == 0 and len(gate.rejections) == 1
    print("4) reject OK (pending 제거)")

    # 5) bnpy seam graceful (미설치 → None → numpy fallback 동작)
    assert disc2._try_bnpy(Xn) is None
    print("5) bnpy seam graceful (미설치 → numpy fallback)")

    # ⑤b) 정지 합성데이터 false-positive rate — regime 없는 데이터에서 '발견' 비율 ≲ α
    disc_fp = OnlineRegimeDiscovery(centroids, chi2_p=0.99, min_segment=6, fdr_alpha=0.05)
    fp_rate = disc_fp.false_positive_rate(rng, n_trials=200, segment_len=60)
    print(f"⑤b) stationary FP rate = {fp_rate:.3f} (<= 2*alpha=0.10 기대, FDR 제어)")
    assert fp_rate <= 0.10, fp_rate

    print("regime_discovery self-test PASS (BOCPD+Hotelling novelty + FDR wrap + 사람비준 gate + bnpy seam "
          "+ ⑤sequestered anytime-valid + 정지 FP rate)")
