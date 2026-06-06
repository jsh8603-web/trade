"""core/assume/etf_beta_lock.py — ETF fallback alpha→beta 4중 잠금 (약변별 sleeve, 자문 D3 안전장치).

WHY: 약변별 sleeve → 단일 테마 ETF fallback 은 "종목 selection 알파를 포기하고 beta 노출만 산다"는
     선언이다. 이 선언이 슬그머니 깨지는(ETF 가 사실은 알파를 내거나, EW 대비 드래그가 쌓이거나,
     변별력이 회복됐는데 ETF 에 갇히는) 3가지 실패를 4중 잠금으로 감시한다.

4중 잠금 (자문 3R 수렴, etf-fallback-weak-sleeve-20260606):
  ① expected-alpha=0 선언   : ETF fallback = beta-only. 알파 0 을 명시 박제(falsification_metric 동반).
  ② shadow-EW e-CUSUM       : (ETF 수익 − 구성종목 EW 수익) 잔차를 양방향 betting e-process 로 감시.
                              지속 초과(알파 발생=선언 위반) 또는 지속 미달(TE 드래그) → e-value 발산 알림.
  ③ 대칭 promote-demote gate : within-IC 회복(≥ic_high) → selection 복귀(promote) / 약화(≤ic_low) →
                              ETF fallback(demote). hysteresis(ic_high>ic_low) 로 whipsaw 차단.
  ④ return-rank counterfactual: "리턴-랭크로 ETF 골랐다면?" 선택을 로깅만(채택 X) — momentum chasing
                              사후 비교용. 대표성-랭크 채택과의 갭을 노출.

재사용: core.assume.fhc._DirectionalE (단측 betting martingale, anytime-valid).
⛔off=byte-identical: 신규 모듈, 기존 assume 파일 무변경. 누구도 호출 안 하면 무동작(미배선).
   construction/orchestrator 가 ETF fallback sleeve 의 주기 수익을 observe 로 먹일 때만 활성.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from core.assume.fhc import _DirectionalE

# ① 선언 상수 — ETF fallback 의 기대 알파는 0 (beta-only). 반증 지표 동반(반증불가=가정 아님).
EXPECTED_ALPHA: float = 0.0
FALSIFICATION_METRIC: str = (
    "shadow-EW 대비 ETF 초과수익 잔차의 양방향 betting e-process 가 임계 발산 → "
    "expected-alpha=0 선언 위반(알파 발생 OR TE 드래그) → 재검토/교체"
)


@dataclass
class CounterfactualEntry:
    """리턴-랭크 vs 대표성-랭크 선택 1건 (채택 X, 로깅만)."""
    asof: datetime
    sleeve_id: str
    representativeness_pick: str       # 실제 채택(대표성+유동성+저비용)
    return_rank_pick: str              # 리턴-랭크였다면 골랐을 ETF
    diverged: bool                     # 두 선택이 다른가 = momentum chasing 했을 지점


class EtfBetaLock:
    """약변별 sleeve ETF fallback 의 alpha→beta 4중 잠금.

    한 sleeve 당 1 인스턴스. 주기 수익을 observe_decoupling 으로 먹이고, decoupled()/promote_demote()
    로 가정 위반·변별력 전환을 판정한다. 상태(e-process 누적 + counterfactual 로그)를 보유.
    """

    def __init__(
        self,
        sleeve_id: str,
        *,
        decoupling_lam: float = 0.1,
        decoupling_clip: float = 3.0,
        e_threshold: float = 20.0,         # Ville: P(sup E≥1/α)≤α → 20 ≈ α 0.05
    ) -> None:
        self.sleeve_id = sleeve_id
        self.e_threshold = e_threshold
        # ② 양방향: +1=ETF 가 EW 초과(알파 발생=선언 위반) / -1=ETF 가 EW 미달(TE 드래그)
        self._e_over = _DirectionalE(sign=+1, lam=decoupling_lam, clip=decoupling_clip)
        self._e_under = _DirectionalE(sign=-1, lam=decoupling_lam, clip=decoupling_clip)
        self._n = 0
        self._sumsq = 0.0          # 0중심 RMS 누적(잔차 변동성 스케일, 평균은 빼지 않음=알파 보존)
        self.counterfactuals: list[CounterfactualEntry] = []

    # ① 선언 ----------------------------------------------------------------
    @property
    def expected_alpha(self) -> float:
        """ETF fallback 기대 알파 = 0 (beta-only 선언)."""
        return EXPECTED_ALPHA

    @property
    def falsification_metric(self) -> str:
        return FALSIFICATION_METRIC

    # ② shadow-EW e-CUSUM ---------------------------------------------------
    def observe_decoupling(self, etf_return: float, shadow_ew_return: float) -> dict:
        """ETF 수익 vs 구성종목 EW(shadow) 수익 잔차 → 양방향 e-process 갱신.

        resid = etf − ew. >0 지속 = ETF 가 EW 초과(알파, 선언 위반) / <0 지속 = TE 드래그.
        반환 {resid, e_over, e_under, n}.
        """
        resid = float(etf_return) - float(shadow_ew_return)
        # 0중심 RMS 로 표준화(평균 미차감=알파 평균 보존). z 를 betting e-process(clip)에 투입.
        self._n += 1
        self._sumsq += resid * resid
        rms = (self._sumsq / self._n) ** 0.5
        z = resid / rms if rms > 1e-12 else 0.0
        e_over = self._e_over.update(z)
        e_under = self._e_under.update(z)
        return {"resid": resid, "z": z, "e_over": e_over, "e_under": e_under, "n": self._n}

    @property
    def e_over(self) -> float:
        return self._e_over.e_value

    @property
    def e_under(self) -> float:
        return self._e_under.e_value

    def decoupled(self, threshold: Optional[float] = None) -> bool:
        """디커플링 발산 여부 — max(e_over, e_under) ≥ 임계 → 선언 위반 알림(True)."""
        thr = self.e_threshold if threshold is None else threshold
        return max(self._e_over.e_value, self._e_under.e_value) >= thr

    def decoupling_reason(self) -> str:
        """발산 방향 설명 (over=알파 발생 / under=TE 드래그 / none)."""
        if self._e_over.e_value >= self.e_threshold:
            return "alpha_emergence(ETF가 EW 초과 지속 — expected-alpha=0 선언 위반)"
        if self._e_under.e_value >= self.e_threshold:
            return "te_drag(ETF가 EW 미달 지속 — 추종오차/비용 드래그)"
        return "none"

    # ③ 대칭 promote-demote gate -------------------------------------------
    @staticmethod
    def promote_demote(
        within_ic: float, *, ic_high: float = 0.45, ic_low: float = 0.25,
    ) -> str:
        """변별력(within-IC) 기반 대칭 게이트.

        ic ≥ ic_high → "promote"(selection 복귀, 변별력 회복) /
        ic ≤ ic_low  → "demote"(ETF fallback, 변별력 약) /
        그 사이       → "hold"(hysteresis deadband, whipsaw 차단).
        ⛔ ic_high > ic_low (대칭+hysteresis). 등급 임계(高≥0.45/低≥0.25, within_residual 정합).
        """
        if ic_high <= ic_low:
            raise ValueError(f"ic_high({ic_high}) > ic_low({ic_low}) 위반 — hysteresis 필요")
        if within_ic >= ic_high:
            return "promote"
        if within_ic <= ic_low:
            return "demote"
        return "hold"

    # ④ return-rank counterfactual -----------------------------------------
    def log_counterfactual(
        self, asof: datetime, representativeness_pick: str, return_rank_pick: str,
    ) -> CounterfactualEntry:
        """리턴-랭크 선택을 로깅만(채택 X). 대표성 선택과 갈리면 diverged=True(momentum chasing 지점)."""
        entry = CounterfactualEntry(
            asof=asof, sleeve_id=self.sleeve_id,
            representativeness_pick=representativeness_pick,
            return_rank_pick=return_rank_pick,
            diverged=(representativeness_pick != return_rank_pick),
        )
        self.counterfactuals.append(entry)
        return entry

    @property
    def counterfactual_divergence_rate(self) -> float:
        """대표성 vs 리턴-랭크 선택이 갈린 비율 = momentum chasing 회피 빈도."""
        if not self.counterfactuals:
            return 0.0
        return sum(1 for c in self.counterfactuals if c.diverged) / len(self.counterfactuals)


# ---------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print("=== ETF beta-lock 4중 잠금 self-test ===")

    lock = EtfBetaLock("financial")

    # ① 선언
    assert lock.expected_alpha == 0.0
    assert lock.falsification_metric
    print("1) 선언: expected_alpha=0 + falsification_metric 동반 OK")

    # ② shadow-EW 디커플링: ETF≈EW(잔차≈0) → 미발산
    import random
    rng = random.Random(42)
    for _ in range(60):
        ew = rng.gauss(0.0, 0.01)
        etf = ew + rng.gauss(0.0, 0.0005)   # TE 작음
        lock.observe_decoupling(etf, ew)
    assert not lock.decoupled(), (lock.e_over, lock.e_under)
    print(f"2a) ETF≈EW(TE 작음) → 미발산 (e_over={lock.e_over:.2f}, e_under={lock.e_under:.2f}) OK")

    # ② 알파 발생: ETF 가 EW 를 지속 초과 → e_over 발산(선언 위반)
    lock2 = EtfBetaLock("battery")
    for _ in range(60):
        ew = rng.gauss(0.0, 0.01)
        etf = ew + 0.004    # 지속 초과(알파)
        lock2.observe_decoupling(etf, ew)
    assert lock2.decoupled(), (lock2.e_over, lock2.e_under)
    assert "alpha_emergence" in lock2.decoupling_reason()
    print(f"2b) ETF 지속 초과(알파) → e_over 발산={lock2.e_over:.1f} → {lock2.decoupling_reason()[:20]}... OK")

    # ② TE 드래그: ETF 가 EW 미달 지속 → e_under 발산
    lock3 = EtfBetaLock("bio")
    for _ in range(60):
        ew = rng.gauss(0.0, 0.01)
        etf = ew - 0.004
        lock3.observe_decoupling(etf, ew)
    assert lock3.decoupled() and "te_drag" in lock3.decoupling_reason()
    print(f"2c) ETF 지속 미달(TE 드래그) → e_under 발산={lock3.e_under:.1f} OK")

    # ③ 대칭 게이트 + hysteresis
    assert EtfBetaLock.promote_demote(0.50) == "promote"   # 변별력 회복
    assert EtfBetaLock.promote_demote(0.20) == "demote"    # 변별력 약
    assert EtfBetaLock.promote_demote(0.35) == "hold"      # deadband
    try:
        EtfBetaLock.promote_demote(0.3, ic_high=0.2, ic_low=0.4)
        assert False
    except ValueError:
        pass
    print("3) 대칭 promote(≥0.45)/demote(≤0.25)/hold(deadband) + hysteresis 검증 OK")

    # ④ counterfactual
    t = datetime(2026, 6, 6)
    lock.log_counterfactual(t, "KODEX 은행", "KODEX 은행")          # 동일
    lock.log_counterfactual(t, "KODEX 은행", "KODEX 레버리지")      # 갈림(momentum)
    assert abs(lock.counterfactual_divergence_rate - 0.5) < 1e-9
    print(f"4) counterfactual: 대표성 vs 리턴-랭크 divergence={lock.counterfactual_divergence_rate:.0%} OK")

    print("\nETF beta-lock self-test PASS")
