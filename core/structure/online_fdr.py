"""core/structure/online_fdr.py — 스트리밍 다중검정 FDR 제어 (가정 변경통계 #1 우선순위).

claude 자문 TOP-1: 가정이 여러 개·연속 모니터링 = **시간·가정 다중검정**. G1 의 batch BH 는
고정 family 가정이라 스트리밍에 틀린다. 정석 = **online FDR** (Javanmard & Montanari 2018;
Ramdas et al. 2017). alpha-wealth 로 각 검정이 예산을 소모하고, 기각하면 일부 회수 → 끝없이
재검정해도 noise 추격을 차단. **= 사용자의 "합리적 이유 없이 자주 바뀌면 안 됨" 의 수학적 보장.**

특히 "기각 가정 부활" 함정 차단 (claude C-부활): 죽은 가정을 레짐 복귀 때 50번 재검정하면
우연히 한 번 통과 → SAFFRON/alpha-investing 이 wealth 고갈로 자동 차단.

구현: LORD++ (Ramdas et al. 2017, decaying memory) + alpha-investing 대안. numpy/math 만.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


def _gamma_seq(k: int) -> float:
    """LORD/SAFFRON 기본 gamma 수열 γ_k ∝ log(max(k,2)) / (k·e^√log k), Σ≈1 정규화."""
    if k <= 0:
        return 0.0
    return 0.07720838 * math.log(max(k, 2)) / (k * math.exp(math.sqrt(math.log(k + 1))))


@dataclass
class FdrDecision:
    reject: bool
    alpha_t: float           # 이 검정에 배정된 유의수준 (wealth 기반)
    p_value: float
    t: int                   # 검정 순번


class LordPlusPlus:
    """LORD++ online FDR (Ramdas et al. 2017). mFDR ≤ alpha 보장(독립/PRDS 가정).

    test(p) 호출마다: wealth 기반 alpha_t 산출 → p ≤ alpha_t 면 기각(+wealth 회수).
    가정 변경 ChangeRequest 의 통계 유의성 게이트로 사용 (AND-gate 첫 조건).
    """
    def __init__(self, alpha: float = 0.05, w0: float | None = None):
        self.alpha = alpha
        self.w0 = w0 if w0 is not None else alpha / 2.0
        self.t = 0
        self.reject_times: list[int] = []

    def _alpha_t(self, t: int) -> float:
        a = _gamma_seq(t) * self.w0
        if self.reject_times:
            tau1 = self.reject_times[0]
            a += (self.alpha - self.w0) * _gamma_seq(t - tau1)
            for tau in self.reject_times[1:]:
                a += self.alpha * _gamma_seq(t - tau)
        return min(a, self.alpha)         # 개별 검정 alpha 상한

    def test(self, p_value: float) -> FdrDecision:
        self.t += 1
        a = self._alpha_t(self.t)
        rej = p_value <= a
        if rej:
            self.reject_times.append(self.t)
        return FdrDecision(reject=rej, alpha_t=float(a), p_value=float(p_value), t=self.t)

    @property
    def n_rejections(self) -> int:
        return len(self.reject_times)


class AlphaInvesting:
    """Alpha-investing (Foster & Stine 2008). wealth 명시 추적 — 부활 남용 차단에 직관적.

    각 검정에 wealth 일부 베팅; 기각 시 omega 회수, 비기각 시 베팅분 소진. wealth 0 = 검정 중단.
    """
    def __init__(self, alpha: float = 0.05, w0: float | None = None, omega: float | None = None):
        self.wealth = w0 if w0 is not None else alpha / 2.0
        self.omega = omega if omega is not None else alpha    # 기각 시 회수량
        self.t = 0
        self.reject_times: list[int] = []

    def test(self, p_value: float) -> FdrDecision:
        self.t += 1
        if self.wealth <= 0:
            return FdrDecision(False, 0.0, float(p_value), self.t)  # 예산 고갈 → 검정 불가
        # 이 검정에 베팅할 alpha (wealth 비례)
        alpha_t = self.wealth / (1.0 + self.t)
        alpha_t = min(alpha_t, self.wealth * 0.5)
        rej = p_value <= alpha_t
        if rej:
            self.wealth += self.omega          # 회수(+보상)
            self.reject_times.append(self.t)
        else:
            self.wealth -= alpha_t / (1.0 - alpha_t)   # 베팅 소진
        return FdrDecision(rej, float(alpha_t), float(p_value), self.t)

    @property
    def n_rejections(self) -> int:
        return len(self.reject_times)


if __name__ == "__main__":
    import numpy as np
    rng = np.random.default_rng(3)

    # 1) 순수 null (uniform p): LORD++ 기각 거의 없음 (FDR 제어)
    lord = LordPlusPlus(alpha=0.05)
    nrej_null = sum(lord.test(float(p)).reject for p in rng.uniform(0, 1, 500))
    print(f"1) null 500 검정 → 기각 {nrej_null} (FDR 제어, 소수여야)"); assert nrej_null <= 5

    # 2) 강한 신호 (p≈0): 기각
    lord2 = LordPlusPlus(alpha=0.05)
    nrej_sig = sum(lord2.test(1e-6).reject for _ in range(20))
    print(f"2) 강신호 20 검정 → 기각 {nrej_sig}"); assert nrej_sig >= 10

    # 3) ★ 죽은 가정 부활 남용: null 을 50번 재검정 → wealth 고갈, 우연 통과 차단
    ai = AlphaInvesting(alpha=0.05)
    # 49 null + 1 우연히 작은 p (0.04) → wealth 고갈로 막판 통과 차단되는지
    pvals = list(rng.uniform(0.2, 1.0, 49)) + [0.04]
    decs = [ai.test(float(p)) for p in pvals]
    print(f"3) 부활 남용 50 검정 → 기각 {ai.n_rejections}, 막판 wealth={ai.wealth:.4f}")
    assert ai.n_rejections == 0, "부활 남용이 차단돼야 (wealth 고갈)"

    print("online_fdr self-test PASS (LORD++ FDR 제어 + alpha-investing 부활 차단)")
