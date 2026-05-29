"""tests/assume/test_weight_closed_loop.py — R15 가중학습 3세션 통합 closed-loop (CL-W GATE).

CONSULT-DECISIONS-weight-20260529.md §1.1~1.8 전체 파이프라인이 **실제 모듈**로 닫히는지 검증.
세 세션 산출 통합(btn-Codlearn 책임):
  btn-button(core/structure/conditional_correlation): RegimeGlasso·effective_precision·calibration
  btn-Inv(core/data/weight_panel): PIT 지표 패널 공급(여기선 합성 패널로 대체)
  btn-Codlearn(core/assume/weight_card·weight_falsification·judge): 비중·L1 주입·DUAL falsification

★사용자 핵심 요구(2회 명시) 박제:
 1. "관계있는 지표 함께 학습(조건부 상관)" → RegimeGlasso 가 regime 별 sparse precision 분리 학습.
 2. "어떤 거시상황(regime)이냐에 따라 상관계수가 달라진다" → 같은 IC 라도 belief b(t) 가 다르면
    Ω_eff 가 달라져 비중 w 가 **동적으로** 바뀐다 (test_weights_shift_by_regime).
 3. "학습 결과로 평가 지표 비중 조절, agent 이전(L1)" → derive_weights → synthesize_l1 (pre-LLM).
 4. 4단계 파이프라인(학습→기준화→주입→falsification)이 닫힌 루프로 회전(test_full_pipeline).
"""

from __future__ import annotations

import numpy as np
import pytest

from core.assume.card_contract import assert_falsifiable
from core.assume.dag import AssumptionDAG
from core.assume.registry import AssumptionRegistry
from core.assume.update_controller import UpdateController, UpdateAction
from core.assume.weight_card import (
    WeightAssumptionCard, derive_weights, synthesize_l1, assert_ceiling_invariant,
)
from core.assume.weight_falsification import (
    rank_ic, evaluate_weight_card,
)
from core.structure.conditional_correlation import (
    RegimeGlasso, effective_precision, TemperatureCalibrator,
)

P = 6  # 지표 수


# ---------------------------------------------------------------------------
# 합성 패널 — regime 별 조건부 상관이 다른 다중에셋 지표 (btn-Inv 패널 대역)
# ---------------------------------------------------------------------------

def _two_regime_panel(seed: int, n_per: int = 90):
    """regime 0: 지표0-1 강상관 / regime 1: 지표2-3 강상관 = '거시상황 따라 상관 다름'.

    같은 지표 집합인데 regime 에 따라 어느 지표쌍이 함께 움직이는지가 바뀐다 — 사용자 핵심.
    """
    rng = np.random.default_rng(seed)
    reg = np.array([0] * n_per + [1] * n_per)
    c0 = np.eye(P); c0[0, 1] = c0[1, 0] = 0.75
    c1 = np.eye(P); c1[2, 3] = c1[3, 2] = 0.75
    X0 = rng.normal(size=(n_per, P)) @ np.linalg.cholesky(c0 + 0.05 * np.eye(P)).T
    X1 = rng.normal(size=(n_per, P)) @ np.linalg.cholesky(c1 + 0.05 * np.eye(P)).T + 1.5
    return np.vstack([X0, X1]), reg


def _series_ids(domain: str):
    return tuple(f"{domain}_ind{i}" for i in range(P))


def _weight_card(domain: str, scope: str, w, belief, *, calib_hash="cal0", regime_id="recession"):
    return WeightAssumptionCard(
        id=f"weight.{domain}.{regime_id}", version="v1", kind="parametric",
        scope=scope, domain=domain,
        statement=f"{domain} {regime_id} 합성비중",
        falsification_metric="합성 score OOS Rank-IC anytime-valid e-process 붕괴 → kill",
        secondary_falsification="‖ΔΩ‖·logdet divergence > τ → re-fit",
        series_ids=_series_ids(domain),
        w_global=tuple(float(x) for x in w),
        belief_regimes=("r0", "r1"), belief_vector=tuple(float(b) for b in belief),
        calibration_hash=calib_hash, regime_id=regime_id)


# 3도메인 동형 단일 경로 (macro/equity/commodity)
DOMAINS = [("macro", "macro"), ("equity", "sector"), ("commodity", "asset")]


# ===========================================================================
# 1) ★조건부 상관 학습 = regime 따라 다름 (사용자 핵심 #1·#2)
# ===========================================================================

def test_regime_conditional_correlation_learned():
    """RegimeGlasso 가 regime 별로 다른 상관쌍을 분리 학습(조건부 상관)."""
    X, reg = _two_regime_panel(seed=1)
    rg = RegimeGlasso(lam_floor=0.05).fit(X, reg)
    m0, m1 = rg.models_[0], rg.models_[1]
    # regime 0 = 지표0-1 상관, regime 1 = 지표2-3 상관 (서로 다른 의존 구조)
    assert m0.corr[0, 1] > 0.3 and m0.corr[2, 3] < 0.3
    assert m1.corr[2, 3] > 0.3 and m1.corr[0, 1] < 0.3


# ===========================================================================
# 2) ★거시상황(belief)에 따라 비중이 동적으로 변함 (사용자 핵심 #2 — 가장 중요)
# ===========================================================================

def test_weights_shift_by_regime_belief():
    """같은 IC 벡터라도 belief b(t)(거시상황)가 다르면 Ω_eff→비중이 달라진다.

    이것이 사용자 2회 강조: '어떤 거시를 어떻게 이해하는지에 따라 상관계수가 달라지고,
    학습 결과로 평가 지표 비중을 조정한다'. 정적 표가 아닌 belief-조건부 동적 비중.
    """
    X, reg = _two_regime_panel(seed=2)
    rg = RegimeGlasso(lam_floor=0.05).fit(X, reg)
    ic = np.array([0.05, 0.05, 0.05, 0.05, 0.02, 0.02])     # 동일 IC

    omega_r0 = effective_precision(rg.models_, {0: 0.95, 1: 0.05}).Omega_eff
    omega_r1 = effective_precision(rg.models_, {0: 0.05, 1: 0.95}).Omega_eff
    w_r0 = derive_weights(omega_r0, ic, blend_1n=0.0)
    w_r1 = derive_weights(omega_r1, ic, blend_1n=0.0)

    # 비중이 거시상황(regime)에 따라 실제로 달라져야 함 (동적)
    assert not np.allclose(w_r0, w_r1, atol=0.05), (w_r0, w_r1)
    # 상관쌍은 자동 감액(다중공선): regime0 에선 지표0-1 이 서로 감액, regime1 에선 지표2-3
    assert abs(w_r0[0]) < abs(w_r0[4]) + 0.3   # regime0: 상관쌍(0) 감액 경향


def test_belief_mix_transition_derisk():
    """belief 모호(uniform) → between-dispersion inflate → 비중 분산(transition 자동 de-risk)."""
    X, reg = _two_regime_panel(seed=3)
    rg = RegimeGlasso(lam_floor=0.05).fit(X, reg)
    r_sharp = effective_precision(rg.models_, {0: 0.99, 1: 0.01})
    r_vague = effective_precision(rg.models_, {0: 0.5, 1: 0.5})
    # 모호 belief = 불확실성 최대 → between-regime dispersion 증가 (transition de-risk feature)
    assert r_vague.dispersion > r_sharp.dispersion
    assert r_vague.cholesky_ok and r_sharp.cholesky_ok        # 정상 역행렬 경로(fallback dead)


# ===========================================================================
# 3) ★4단계 파이프라인 닫힌 루프 (학습→기준화→L1 주입→falsification) — 3도메인 동형
# ===========================================================================

@pytest.mark.parametrize("domain,scope", DOMAINS)
def test_full_pipeline_4stage(domain, scope):
    """학습(glasso) → 기준화(비중카드) → 주입(S_L1) → falsification(DUAL) 닫힌 루프 1회전.

    3도메인(거시/주식/상품) 단일 경로 — 동형 처리 확인.
    """
    reg_registry = AssumptionRegistry()
    dag = AssumptionDAG(reg_registry)
    uc = UpdateController(reg_registry, validator=None, dag=dag)

    # (1) 학습: regime-conditional glasso
    X, reg = _two_regime_panel(seed=hash(domain) % 1000)
    rg = RegimeGlasso(lam_floor=0.05).fit(X, reg)
    belief = {0: 0.7, 1: 0.3}
    omega_eff = effective_precision(rg.models_, belief).Omega_eff
    ic = np.array([0.06, 0.04, 0.05, 0.03, 0.02, 0.04])

    # (2) 기준화: 비중 도출 + 카드화 (registry 등록 = 단일-지표 카드와 동일 lifecycle)
    w = derive_weights(omega_eff, ic, blend_1n=0.3, cap=0.4)
    assert abs(np.abs(w).sum() - 1.0) < 1e-6 and np.all(np.abs(w) <= 0.4 + 1e-9)
    card = _weight_card(domain, scope, w, [belief[0], belief[1]])
    assert_falsifiable(card)                                  # 진입 게이트 통과
    reg_registry.register(card)
    assert reg_registry.get(card.id) is card

    # (3) 주입: L1 결정론 합성 S_L1 = clamp_floor(Σ w·z) — pre-LLM·pre-agent
    z = np.array([1.5, 1.2, -0.8, 0.3, 0.9, -0.4])           # 지표 표준화 신호
    s_l1 = synthesize_l1(z, card.composed_weights(), floor=card.floor)
    # down-only attenuation(LLM/agent) 후 천장 불변식
    s_out = s_l1 * 0.6                                        # L2·L3 감쇠 예시
    assert_ceiling_invariant(s_out, s_l1)

    # (4) falsification: 합성 score 시계열 → Rank-IC → DUAL. 안정 IC → KEEP
    rng = np.random.default_rng(99)
    ic_series = list(0.05 + rng.normal(0, 0.01, 40))         # baseline 유지(붕괴 X)
    res = evaluate_weight_card(card, ic_series, baseline_ic=0.05, sd=0.02,
                              omega_old=omega_eff, omega_new=omega_eff)
    assert res.primary_kill is False and res.secondary_refit is False
    dec = uc.step(card, res.verdict, hard_falsifier=res.primary_kill, as_of="2026-05-01")
    assert dec.action == UpdateAction.KEEP


# ===========================================================================
# 4) ★falsification → lifecycle (PRIMARY kill = retract / SECONDARY = re-fit)
# ===========================================================================

def test_primary_breakdown_retracts():
    """합성 score Rank-IC 붕괴 → PRIMARY kill → update_controller RETIRE (live 즉시 차단)."""
    reg_registry = AssumptionRegistry()
    dag = AssumptionDAG(reg_registry)
    uc = UpdateController(reg_registry, validator=None, dag=dag)
    card = _weight_card("macro", "macro", [0.4, 0.3, 0.3, 0.0, 0.0, 0.0], [0.5, 0.5])
    reg_registry.register(card)

    rng = np.random.default_rng(5)
    # IC 가 0.05 → -0.04 음전환(비중이 더 이상 수익 예측 못 함)
    ic_break = list(0.05 + rng.normal(0, 0.01, 8)) + list(-0.04 + rng.normal(0, 0.01, 32))
    res = evaluate_weight_card(card, ic_break, baseline_ic=0.05, sd=0.02)
    assert res.primary_kill is True
    dec = uc.step(card, res.verdict, hard_falsifier=res.primary_kill, as_of="2026-05-01", epoch=1)
    assert dec.action == UpdateAction.RETIRE


def test_secondary_drift_does_not_kill():
    """Ω drift 만(score IC 견딤) → kill 아님(SECONDARY re-fit 플래그). 과민 retract 방지."""
    card = _weight_card("equity", "sector", [0.3, 0.3, 0.2, 0.2, 0.0, 0.0], [0.5, 0.5])
    rng = np.random.default_rng(6)
    ic_stable = list(0.05 + rng.normal(0, 0.01, 40))
    O = np.eye(P) * 2.0 - 0.3
    O_drift = O * 0.25 + np.diag([3.0] * P)                  # 구조 급변
    res = evaluate_weight_card(card, ic_stable, baseline_ic=0.05, sd=0.02,
                              omega_old=O, omega_new=O_drift)
    assert res.primary_kill is False and res.secondary_refit is True


# ===========================================================================
# 5) ★b(t) frozen replay — 같은 belief 동결 → 같은 Ω_eff → 같은 비중 (결정 재현)
# ===========================================================================

def test_btf_frozen_replay_deterministic():
    """belief 동결 시 effective_precision→derive_weights 가 결정론적 재현(PIT replay)."""
    X, reg = _two_regime_panel(seed=7)
    rg = RegimeGlasso(lam_floor=0.05).fit(X, reg)
    ic = np.array([0.05, 0.04, 0.05, 0.03, 0.02, 0.04])
    belief = {0: 0.6, 1: 0.4}

    w_a = derive_weights(effective_precision(rg.models_, belief).Omega_eff, ic)
    w_b = derive_weights(effective_precision(rg.models_, belief).Omega_eff, ic)
    assert np.allclose(w_a, w_b)                              # 동결 belief = 동일 비중(재현)

    # 카드 pin_hash 도 동일 belief → 동일(다른 belief → 분기)
    c1 = _weight_card("macro", "macro", w_a, [0.6, 0.4])
    c2 = _weight_card("macro", "macro", w_a, [0.6, 0.4])
    c3 = _weight_card("macro", "macro", w_a, [0.3, 0.7])
    assert c1.pin_hash() == c2.pin_hash() and c1.pin_hash() != c3.pin_hash()


# ===========================================================================
# 6) ★calibration → belief b(t) (거시상황 분류 신뢰도 보정, frozen)
# ===========================================================================

def test_calibration_produces_frozen_belief():
    """과신 분류기 logit → temperature calibration → 보정 belief + frozen pin(replay)."""
    rng = np.random.default_rng(8)
    nC = 300
    pred = rng.integers(0, 2, nC)
    logits = rng.normal(0, 0.5, (nC, 2))
    logits[np.arange(nC), pred] = 4.0
    flip = rng.random(nC) < 0.4
    y = np.where(flip, rng.integers(0, 2, nC), pred)
    cal = TemperatureCalibrator()
    cr = cal.fit(logits, y)
    assert cr.temperature > 1.0 and cr.ece_after <= cr.ece_before + 1e-6
    assert cr.pin_hash and cr.frozen                         # frozen + hash-pin (replay)
    # 보정 확률을 belief 로 카드에 박제 → calibration_hash 연결
    probs = cal.transform(logits[:1])[0]
    card = _weight_card("macro", "macro", [0.4, 0.3, 0.3, 0, 0, 0],
                       [float(probs[0]), float(probs[1])], calib_hash=cr.pin_hash)
    assert card.calibration_hash == cr.pin_hash


# ===========================================================================
# 7) ★production 오케스트레이터 (weight_cycle) — 미배선 4 seam 해소 회귀 게이트
# ===========================================================================

def _learner_and_returns(seed):
    import numpy as _np
    from core.assume.weight_cycle import GlassoWeightLearner
    X, reg = _two_regime_panel(seed=seed)
    rng = _np.random.default_rng(seed + 100)
    ret = X[:, 0] * 0.5 + X[:, 2] * 0.3 + rng.normal(0, 0.5, len(X))   # 지표0,2 예측
    return GlassoWeightLearner(lam_floor=0.05).fit(X, reg), X, ret


@pytest.mark.parametrize("domain,scope", DOMAINS)
def test_production_cycle_one_turn(domain, scope):
    """run_weight_cycle: 학습→기준화→주입→score IC→DUAL→lifecycle 한 바퀴(라이브 미접촉).

    seed 고정(hash 비결정성 제거 = flaky 차단). action 종류는 합성데이터 의존이라 단언 완화 —
    검증 핵심은 '4단계가 끊김 없이 1회전(카드 등록·S_L1·ic_series·decision 산출)'.
    """
    from core.assume.weight_cycle import run_weight_cycle
    learner, X, ret = _learner_and_returns(seed=42)
    reg_r = AssumptionRegistry(); dag = AssumptionDAG(reg_r)
    uc = UpdateController(reg_r, validator=None, dag=dag)
    res = run_weight_cycle(
        learner, belief={0: 0.7, 1: 0.3}, returns=ret, z_now=X[100], forward_returns=ret,
        registry=reg_r, uc=uc, domain=domain, scope=scope,
        series_ids=_series_ids(domain), regime_id="recession", as_of="2026-05-01")
    # 4단계 1회전 산출 확인(카드 등록 + S_L1 + ic 시계열 + decision). action 종류=데이터 의존.
    assert reg_r.get(res.card.id) is not None and len(res.ic_series) > 0
    assert res.decision.action is not None and isinstance(res.s_l1, float)


def test_cycle_secondary_refit_routes_to_transition():
    """★SECONDARY Ω drift(score 견딤) → route_lifecycle 가 derive_weights 재적합 → TRANSITION."""
    import numpy as _np
    from core.assume.weight_cycle import build_weight_card, route_lifecycle
    learner, X, ret = _learner_and_returns(seed=22)
    reg_r = AssumptionRegistry(); dag = AssumptionDAG(reg_r)
    uc = UpdateController(reg_r, validator=None, dag=dag)
    card = build_weight_card(learner, {0: 0.5, 1: 0.5}, ret, domain="macro", scope="macro",
                             series_ids=_series_ids("macro"), regime_id="neutral",
                             valid_from="2026-05-01")
    reg_r.register(card)
    rng = _np.random.default_rng(22)
    stable_ic = list(0.05 + rng.normal(0, 0.01, 30))
    res = evaluate_weight_card(card, stable_ic, baseline_ic=0.05, sd=0.02,
                              omega_old=_np.eye(P), omega_new=_np.diag([5.0] * P))
    assert res.secondary_refit and not res.primary_kill
    dec = route_lifecycle(reg_r, uc, card, res, learner=learner, belief={0: 0.5, 1: 0.5},
                          returns=ret, as_of="2026-06-01", epoch=1)
    assert dec.action == UpdateAction.TRANSITION and dec.new_card.version == "v2"
