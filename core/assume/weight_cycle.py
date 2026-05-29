"""core/assume/weight_cycle.py — R15 가중학습 4단계 production 오케스트레이터 (CL-W 배선).

CONSULT-DECISIONS-weight-20260529.md §1.1~1.8 의 4단계(학습→기준화→주입→falsification/해제)를
**하나의 production-callable 함수**로 묶어, 지금까지 테스트-only 로만 돌던 seam 들을 실코드로 잇는다.

3-subagent connectivity 검증(2026-05-30)이 지적한 미배선 4 seam 해소:
 ① 학습   : weight_panel(IndicatorPanel) → RegimeGlasso.fit → effective_precision(belief)→Ω_eff
            ↳ GlassoWeightLearner 가 WeightLearner Protocol 구현체로 ①을 캡슐화(누락 글루).
 ② 기준화 : Ω_eff·IC → derive_weights → WeightAssumptionCard → registry.register (build_weight_card)
 ③ 주입   : card.composed_weights → synthesize_l1 (judge 가 소비; 여기선 score 시계열 생성)
 ③→④ join: 합성 score 시계열 → rank_ic → ic_series (run_weight_cycle 이 손수 잇던 걸 코드화)
 ④ 해제   : evaluate_weight_card → route_lifecycle (PRIMARY→RETIRE / ★SECONDARY→re-fit→TRANSITION)
            ↳ secondary_refit 플래그가 update_controller 로 안 흐르던 갭 해소(derive_weights 재실행).

⛔ 라이브 미접촉: 본 모듈은 offline/replay 결정론 경로(pre-LLM·pre-agent)만 조립한다. 라이브
   결정루프(run_agents/stock_track) 실주입·실주문 경로는 go-live 경계(N-INT, 자율 범위 밖)로 분리.
   본 오케스트레이터의 산출(WeightAssumptionCard·S_L1)을 라이브가 소비하도록 붙이는 건 별도 게이트.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np

from core.assume.registry import AssumptionRegistry
from core.assume.update_controller import (
    UpdateController, UpdateAction, UpdateDecision, transition_card,
)
from core.assume.weight_card import (
    WeightAssumptionCard, derive_weights, synthesize_l1,
    DEFAULT_BLEND_1N, DEFAULT_WEIGHT_CAP, DEFAULT_L1_FLOOR,
)
from core.assume.weight_falsification import (
    rank_ic, evaluate_weight_card, WeightFalsificationResult,
)
from core.structure.conditional_correlation import RegimeGlasso, effective_precision


# ---------------------------------------------------------------------------
# ① 학습 캡슐 — WeightLearner Protocol 구현체 (btn-button glasso 래핑)
# ---------------------------------------------------------------------------

class GlassoWeightLearner:
    """regime-conditional glasso 학습 + belief-mix Ω_eff + 지표별 IC 산출 (WeightLearner 구현).

    weight_card.WeightLearner Protocol 의 누락 구현체 — RegimeGlasso(btn-button) 를 감싸
    omega_eff(belief)/ic(returns) 두 표면으로 노출. 학습 패널 X(시점×지표, btn-Inv weight_panel
    의 IndicatorPanel.matrix 와 호환 형상)와 regime_ids 로 fit.
    """

    def __init__(self, *, lam_floor: float = 0.05):
        self.lam_floor = lam_floor
        self._rg: Optional[RegimeGlasso] = None
        self._X: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, regime_ids: Sequence[int]) -> "GlassoWeightLearner":
        """지표 패널 X(완전관측 행) + regime_ids → regime 별 sparse precision 학습."""
        self._X = np.asarray(X, dtype=float)
        self._rg = RegimeGlasso(lam_floor=self.lam_floor).fit(self._X, np.asarray(regime_ids))
        return self

    def omega_eff(self, belief: dict, as_of=None) -> np.ndarray:
        """belief b(t)(거시상황 확신도) → cov-space mix → 1회 역행렬 → Ω_eff (동적)."""
        if self._rg is None:
            raise RuntimeError("fit 선행 필요")
        return effective_precision(self._rg.models_, belief).Omega_eff

    def ic(self, returns: Sequence[float], as_of=None) -> np.ndarray:
        """지표별 Rank-IC = corr(지표 시계열, forward return). Grinold w∝Ω·IC 입력.

        학습 패널 각 열(지표)과 forward return 의 rank 상관 — 지표의 예측력 부호·크기.
        """
        if self._X is None:
            raise RuntimeError("fit 선행 필요")
        r = np.asarray(returns, dtype=float)
        n, p = self._X.shape
        if r.shape[0] != n:
            raise ValueError(f"returns 길이 {r.shape[0]} ≠ 패널 행 {n}")
        return np.array([rank_ic(self._X[:, j], r)[0] for j in range(p)], dtype=float)


def _omega_hash(omega: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(omega, dtype=float).tobytes()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# ② 기준화 — Ω_eff·IC → 비중 → 카드 → registry (build_weight_card)
# ---------------------------------------------------------------------------

def build_weight_card(
    learner: GlassoWeightLearner,
    belief: dict,
    returns: Sequence[float],
    *,
    domain: str,
    scope: str,
    series_ids: Sequence[str],
    regime_id: str,
    version: str = "v1",
    archetype: Optional[str] = None,
    calibration_hash: Optional[str] = None,
    blend_1n: float = DEFAULT_BLEND_1N,
    cap: float = DEFAULT_WEIGHT_CAP,
    floor: float = DEFAULT_L1_FLOOR,
    n_eff: int = 0,
    mde: float = 0.0,
    valid_from=None,
) -> WeightAssumptionCard:
    """학습 산출(Ω_eff·IC) → derive_weights → WeightAssumptionCard. b(t)·Ω hash 박제.

    belief = {regime: 확신도}(거시상황 인식 결과). 카드에 belief_vector·omega_hash 동결 → replay.
    """
    omega = learner.omega_eff(belief)
    ic = learner.ic(returns)
    w = derive_weights(omega, ic, blend_1n=blend_1n, cap=cap)
    belief_regimes = tuple(str(k) for k in belief)
    belief_vector = tuple(float(belief[k]) for k in belief)
    return WeightAssumptionCard(
        id=f"weight.{domain}.{regime_id}", version=version, kind="parametric",
        scope=scope, domain=domain,
        statement=f"{domain} {regime_id} 학습 합성비중(조건부상관 glasso)",
        falsification_metric="합성 score OOS Rank-IC anytime-valid e-process 붕괴 → kill",
        secondary_falsification="‖ΔΩ‖·logdet divergence > τ → re-fit",
        series_ids=tuple(series_ids),
        w_global=tuple(float(x) for x in w),
        ic=tuple(float(x) for x in ic),
        belief_regimes=belief_regimes, belief_vector=belief_vector,
        omega_hash=_omega_hash(omega), calibration_hash=calibration_hash,
        regime_id=regime_id, archetype=archetype,
        cap=cap, blend_1n=blend_1n, floor=floor,
        n_eff=n_eff, mde=mde, valid_from=valid_from)


# ---------------------------------------------------------------------------
# ③ 주입 — card → S_L1 (judge 가 실제 소비; 여기선 결정론 합성 확인 + score 시계열)
# ---------------------------------------------------------------------------

def inject_l1(card: WeightAssumptionCard, z: Sequence[float],
              *, regime_pi: Optional[dict] = None) -> float:
    """card 비중 + 지표신호 z → S_L1 = clamp_floor(Σ w·z). judge l1_size 입력(pre-agent)."""
    w = card.composed_weights(regime_pi)
    return synthesize_l1(z, w, floor=card.floor)


def score_series_from_panel(card: WeightAssumptionCard, panel: np.ndarray,
                            *, regime_pi: Optional[dict] = None) -> np.ndarray:
    """패널 각 행(시점)에 비중 합성 → S_L1 시계열. ③→④ join(IC 산출용 합성 score)."""
    w = card.composed_weights(regime_pi)
    P = np.asarray(panel, dtype=float)
    return np.array([synthesize_l1(P[i], w, floor=card.floor) for i in range(P.shape[0])])


# ---------------------------------------------------------------------------
# ④ 해제 — falsification → lifecycle. ★SECONDARY→re-fit 라우팅(미배선 갭 해소)
# ---------------------------------------------------------------------------

def route_lifecycle(
    registry: AssumptionRegistry,
    uc: UpdateController,
    card: WeightAssumptionCard,
    fres: WeightFalsificationResult,
    *,
    learner: Optional[GlassoWeightLearner] = None,
    belief: Optional[dict] = None,
    returns: Optional[Sequence[float]] = None,
    as_of=None,
    epoch: int = 0,
    effect_size: float = 0.0,
    dwell_ok: bool = False,
    k_window_persist: int = 0,
    same_regime: bool = True,
) -> UpdateDecision:
    """DUAL falsification 결과 → lifecycle.

    PRIMARY kill   → update_controller(hard_falsifier) = RETIRE (live 즉시 차단).
    ★SECONDARY     → Ω drift 만(score 견딤)이면 derive_weights 재실행 → transition_card →
                     registry.transition (재적합). secondary_refit 플래그가 lifecycle 로 흐르지
                     않던 갭을 여기서 잇는다. learner+belief+returns 제공 시 자동 재적합.
    그 외           → 일반 adopt gate(update_controller.step).
    """
    if fres.primary_kill:
        return uc.step(card, fres.verdict, hard_falsifier=True, as_of=as_of, epoch=epoch)

    if fres.secondary_refit and learner is not None and belief is not None and returns is not None:
        # 재적합: 최신 Ω_eff·IC 로 비중 재도출 → 새 버전 전환(기존 불변, append-only)
        new_w = derive_weights(learner.omega_eff(belief), learner.ic(returns),
                               blend_1n=card.blend_1n, cap=card.cap)
        new_omega_hash = _omega_hash(learner.omega_eff(belief))
        new_card = transition_card(card, as_of=as_of,
                                   w_global=tuple(float(x) for x in new_w),
                                   omega_hash=new_omega_hash)
        registry.transition(new_card)
        return UpdateDecision(
            UpdateAction.TRANSITION,
            "SECONDARY Ω drift → derive_weights 재적합(score IC 견딤, kill 아님)",
            new_card=new_card)

    return uc.step(card, fres.verdict, hard_falsifier=False, effect_size=effect_size,
                   dwell_ok=dwell_ok, k_window_persist=k_window_persist,
                   same_regime=same_regime, as_of=as_of, epoch=epoch)


# ---------------------------------------------------------------------------
# 4단계 1회전 오케스트레이터 (offline/replay, 라이브 미접촉)
# ---------------------------------------------------------------------------

@dataclass
class WeightCycleResult:
    card: WeightAssumptionCard
    s_l1: float                       # 현 시점 주입 S_L1 (대표 z)
    ic_series: list                   # ③→④ join 합성 score Rank-IC 시계열
    falsification: WeightFalsificationResult
    decision: UpdateDecision


def run_weight_cycle(
    learner: GlassoWeightLearner,
    *,
    belief: dict,
    returns: Sequence[float],
    z_now: Sequence[float],
    forward_returns: Sequence[float],
    registry: AssumptionRegistry,
    uc: UpdateController,
    domain: str,
    scope: str,
    series_ids: Sequence[str],
    regime_id: str,
    regime_pi: Optional[dict] = None,
    baseline_ic: float = 0.05,
    ic_sd: float = 0.02,
    omega_prev: Optional[np.ndarray] = None,
    as_of=None,
    epoch: int = 0,
) -> WeightCycleResult:
    """학습된 learner 로 4단계 1회전: 기준화→주입→score IC→DUAL→lifecycle.

    forward_returns = 합성 score 의 미래수익(③→④ IC 산출용, score_series 와 같은 길이의 패널
    행별 forward return). 라이브 미접촉 — registry/uc 상태만 갱신.
    """
    # ② 기준화
    card = build_weight_card(learner, belief, returns, domain=domain, scope=scope,
                             series_ids=series_ids, regime_id=regime_id, valid_from=as_of)
    registry.register(card)

    # ③ 주입 (현 시점 S_L1)
    s_l1 = inject_l1(card, z_now, regime_pi=regime_pi)

    # ③→④ join: 학습 패널로 합성 score 시계열 → 각 시점 Rank-IC(rolling 대신 누적 단일 IC 시퀀스)
    scores = score_series_from_panel(card, learner._X, regime_pi=regime_pi)
    fr = np.asarray(forward_returns, dtype=float)
    # 합성 score 의 예측력 시계열: 확장 윈도 Rank-IC (anytime-valid e-process 입력)
    ic_series = []
    min_w = 5
    for t in range(min_w, len(scores) + 1):
        ic_t, _ = rank_ic(scores[:t], fr[:t])
        ic_series.append(ic_t)

    # ④ DUAL falsification + lifecycle
    omega_now = learner.omega_eff(belief)
    fres = evaluate_weight_card(card, ic_series, baseline_ic=baseline_ic, sd=ic_sd,
                               omega_old=omega_prev, omega_new=omega_now)
    decision = route_lifecycle(registry, uc, card, fres, learner=learner, belief=belief,
                               returns=returns, as_of=as_of, epoch=epoch)
    return WeightCycleResult(card=card, s_l1=s_l1, ic_series=ic_series,
                             falsification=fres, decision=decision)


if __name__ == "__main__":
    from core.assume.dag import AssumptionDAG

    rng = np.random.default_rng(20260530)
    P = 6
    n_per = 90

    def _panel(seed):
        r = np.random.default_rng(seed)
        reg = np.array([0] * n_per + [1] * n_per)
        c0 = np.eye(P); c0[0, 1] = c0[1, 0] = 0.75
        c1 = np.eye(P); c1[2, 3] = c1[3, 2] = 0.75
        X0 = r.normal(size=(n_per, P)) @ np.linalg.cholesky(c0 + 0.05 * np.eye(P)).T
        X1 = r.normal(size=(n_per, P)) @ np.linalg.cholesky(c1 + 0.05 * np.eye(P)).T + 1.5
        return np.vstack([X0, X1]), reg

    sids = tuple(f"macro_ind{i}" for i in range(P))

    # 1) ① 학습 캡슐 — GlassoWeightLearner.fit → omega_eff(belief)/ic(returns)
    X, reg = _panel(1)
    ret = X[:, 0] * 0.5 + X[:, 2] * 0.3 + rng.normal(0, 0.5, len(X))   # 지표0,2 가 수익 예측
    learner = GlassoWeightLearner(lam_floor=0.05).fit(X, reg)
    om = learner.omega_eff({0: 0.7, 1: 0.3})
    ic = learner.ic(ret)
    assert om.shape == (P, P) and ic.shape == (P,)
    assert ic[0] > 0 and ic[2] > 0      # 예측 지표 양의 IC
    print(f"1) ① GlassoWeightLearner OK: Ω_eff{om.shape} ic[0]={ic[0]:+.3f} ic[2]={ic[2]:+.3f}")

    # 2) ② build_weight_card — Ω_eff·IC → 비중 → 카드 → registry
    reg_r = AssumptionRegistry(); dag = AssumptionDAG(reg_r)
    uc = UpdateController(reg_r, validator=None, dag=dag)
    card = build_weight_card(learner, {0: 0.7, 1: 0.3}, ret, domain="macro", scope="macro",
                             series_ids=sids, regime_id="recession", valid_from="2026-05-01")
    reg_r.register(card)
    assert abs(np.abs(card.composed_weights()).sum() - 1.0) < 1e-6
    assert card.omega_hash and card.belief_vector == (0.7, 0.3)
    print(f"2) ② build_weight_card OK: {card.id} w_sum=1 belief={card.belief_vector} Ωhash={card.omega_hash}")

    # 3) ③ 주입 — S_L1 = clamp_floor(Σ w·z)
    z = X[100]   # 어느 시점 지표 신호
    s_l1 = inject_l1(card, z)
    print(f"3) ③ inject_l1 OK: S_L1={s_l1:+.3f}")

    # 4) ★4단계 1회전 — 안정 score IC → KEEP (학습→...→해제 닫힌 production 함수)
    reg_r2 = AssumptionRegistry(); dag2 = AssumptionDAG(reg_r2)
    uc2 = UpdateController(reg_r2, validator=None, dag=dag2)
    res = run_weight_cycle(learner, belief={0: 0.7, 1: 0.3}, returns=ret, z_now=z,
                           forward_returns=ret, registry=reg_r2, uc=uc2,
                           domain="macro", scope="macro", series_ids=sids,
                           regime_id="recession", as_of="2026-05-01")
    print(f"4) ★4단계 1회전: action={res.decision.action.value} S_L1={res.s_l1:+.3f} "
          f"ic_n={len(res.ic_series)} primary_kill={res.falsification.primary_kill}")
    assert res.decision.action in (UpdateAction.KEEP, UpdateAction.TRANSITION)

    # 5) ★SECONDARY→re-fit 라우팅 (미배선 갭 해소) — Ω drift 큼 + score 견딤 → TRANSITION(v2)
    reg_r3 = AssumptionRegistry(); dag3 = AssumptionDAG(reg_r3)
    uc3 = UpdateController(reg_r3, validator=None, dag=dag3)
    card3 = build_weight_card(learner, {0: 0.5, 1: 0.5}, ret, domain="macro", scope="macro",
                              series_ids=sids, regime_id="neutral", valid_from="2026-05-01")
    reg_r3.register(card3)
    from core.assume.weight_falsification import WeightFalsificationResult, weight_card_verdict
    stable_ic = list(0.05 + rng.normal(0, 0.01, 30))
    O_big = np.diag([5.0] * P)    # 큰 drift
    fres = evaluate_weight_card(card3, stable_ic, baseline_ic=0.05, sd=0.02,
                               omega_old=np.eye(P), omega_new=O_big)
    assert fres.secondary_refit and not fres.primary_kill
    dec = route_lifecycle(reg_r3, uc3, card3, fres, learner=learner, belief={0: 0.5, 1: 0.5},
                          returns=ret, as_of="2026-06-01", epoch=1)
    assert dec.action == UpdateAction.TRANSITION and dec.new_card.version == "v2"
    assert reg_r3.get_version("weight.macro.neutral", "v2") is not None
    print(f"5) ★SECONDARY→re-fit 라우팅: action={dec.action.value} new_ver={dec.new_card.version} (갭 해소)")

    # 6) ★PRIMARY kill 라우팅 → RETIRE
    reg_r4 = AssumptionRegistry(); dag4 = AssumptionDAG(reg_r4)
    uc4 = UpdateController(reg_r4, validator=None, dag=dag4)
    card4 = build_weight_card(learner, {0: 0.5, 1: 0.5}, ret, domain="equity", scope="sector",
                              series_ids=sids, regime_id="recession", valid_from="2026-05-01")
    reg_r4.register(card4)
    break_ic = list(0.05 + rng.normal(0, 0.01, 8)) + list(-0.04 + rng.normal(0, 0.01, 32))
    fres4 = evaluate_weight_card(card4, break_ic, baseline_ic=0.05, sd=0.02)
    dec4 = route_lifecycle(reg_r4, uc4, card4, fres4, as_of="2026-06-01", epoch=1)
    assert dec4.action == UpdateAction.RETIRE
    print(f"6) ★PRIMARY kill 라우팅: action={dec4.action.value} (live 즉시 차단)")

    print("CL-W weight_cycle self-test PASS "
          "(① GlassoWeightLearner + ② build_card + ③ inject_l1 + 4단계 1회전 + "
          "★SECONDARY→re-fit + ★PRIMARY→RETIRE 라우팅 — 미배선 4 seam 해소)")
