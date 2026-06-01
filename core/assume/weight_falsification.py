"""core/assume/weight_falsification.py — 가중카드 DUAL falsification (CL-W, 축 D·E).

CONSULT-DECISIONS-weight-20260529.md §1.5 (btn-Codlearn 분담).

WeightAssumptionCard 는 단일-지표 카드와 **같은 lifecycle**(validator/update_controller)을 타되,
반증 성격이 둘이다(자문 §1.5 DUAL):

 PRIMARY (kill) = 합성 score 의 OOS Rank-IC anytime-valid(e-process) 붕괴.
   → 비중으로 만든 score 가 더 이상 수익을 예측 못 함 = 비중 가정 자체가 틀림 → retract.
   기존 e-process(MixtureSPRTEProcess) 재사용 — score IC 를 FDR 부모노드 서브패밀리로.

 SECONDARY (re-fit, kill 아님) = 상관구조 drift ‖ΔΩ‖·logdet divergence > τ.
   → Ω 가 흔들렸어도 score IC 가 견디면 비중은 robust(분리 이유). 구조 drift 만으로 kill 하면
   과민 → transition(재적합) 트리거. 새 비중은 derive_weights 재실행(오케스트레이터).

★PIT: ic_series = OOS 윈도별 Rank-IC(knowledge_time 순). e-process 는 reorder-invariant 폐형
(eprocess_backbone) 이라 replay 재현. verdict = ValidationVerdict 로 패키징 → update_controller
.step(hard_falsifier=primary_kill) 가 PRIMARY→RETIRE / SECONDARY→TRANSITION 으로 분기.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np

from core.assume.card_contract import AssumptionCardLike
from core.structure.assumption_validation_engine import ValidationVerdict
from core.structure.eprocess_backbone import e_cusum, shift_lr, ConvexLeakEProcess

# SECONDARY drift 기본 임계 (자문 §1.5 ‖ΔΩ‖·logdet)
DEFAULT_TAU_FRO: float = 0.50       # 상대 Frobenius drift (Ω 50% 변형)
DEFAULT_TAU_LOGDET: float = 1.00    # |Δ logdet(Ω)| (정보량 급변)


def _rankdata(a: np.ndarray) -> np.ndarray:
    """평균순위(ties 평균) — Spearman rank-IC 용. 동점은 평균순위로 안정."""
    a = np.asarray(a, dtype=float)
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty(len(a), dtype=float)
    ranks[order] = np.arange(len(a), dtype=float)
    # ties 평균
    _, inv, counts = np.unique(a, return_inverse=True, return_counts=True)
    sums = np.zeros(len(counts))
    np.add.at(sums, inv, ranks)
    avg = sums / counts
    return avg[inv]


def rank_ic(scores: Sequence[float], returns: Sequence[float]) -> tuple[float, int]:
    """Spearman Rank-IC = corr(rank(score), rank(forward_return)). (ic, n).

    합성 score 의 예측력 척도. 분산 0/길이부족 → (0.0, n). 부호 = 예측 방향.
    """
    s = np.asarray(scores, dtype=float)
    r = np.asarray(returns, dtype=float)
    if s.size < 2 or s.size != r.size:
        return (0.0, int(s.size))
    rs, rr = _rankdata(s), _rankdata(r)
    if rs.std() == 0.0 or rr.std() == 0.0:
        return (0.0, int(s.size))
    return (float(np.corrcoef(rs, rr)[0, 1]), int(s.size))


def score_ic_breakdown_eprocess(
    ic_series: Sequence[float],
    *,
    baseline_ic: float,
    sd: float,
    alpha: float = 0.05,
    tau2: float = 1.0,
) -> tuple[bool, float, int]:
    """합성 score Rank-IC 시계열의 **붕괴**(baseline 아래 단측 하락)를 anytime-valid E-CUSUM 으로.

    z_t = (baseline − ic_t)/sd: IC 가 baseline 아래로 내려갈수록 z↑ → detector↑ → reject.
    ★단측 E-CUSUM(log_R = max(0, ·) reset): IC **개선**(ic>baseline)은 0 으로 floor = kill 안 함
    (붕괴만 kill). mixture 양측이 IC 개선도 reject·overflow 하던 문제 해소. changepoint=max_r≥1/alpha.
    Ville: P(거짓 kill)≤alpha, optional-stopping robust. (reject, max_detector, n).
    """
    sd = float(sd) if sd and sd > 1e-9 else 1.0
    s = np.asarray(list(ic_series), dtype=float)
    if s.size == 0:
        return (False, 1.0, 0)
    max_r = e_cusum(s, float(baseline_ic), sd, tau2=tau2, alpha=alpha)
    return (bool(max_r >= 1.0 / alpha), float(max_r), int(s.size))


def score_ic_recovery_eprocess(
    ic_series: Sequence[float],
    *,
    baseline_ic: float,
    sd: float,
    alpha: float = 0.05,
    gamma: float = 0.98,
    tau2: float = 1.0,
) -> tuple[bool, float, int]:
    """★§14.2 E_for(재진입 증거 e-process) — score_ic_breakdown_eprocess 의 **대칭**.

    reject 된 가중카드의 합성 score Rank-IC 가 baseline 위로 **회복**(개선)하는지 convex-leak
    e-process 로 누적. z_t = (ic_t − baseline)/sd: IC↑(회복)이면 z↑ → m_t=shift_lr(z)>1 → Ẽ_for↑.
    ★convex-leak(Ẽ_t=γ·Ẽ_{t-1}·m_t+(1−γ)): 회복 증거 소멸 시 1 로 누수 = phoenix(drift 부활) 방어.
    E_against(baseline 아래 하락=score_ic_breakdown)와 matched(동일 leak primitive, 부호만 반전).
    재진입 ⟺ sup Ẽ_for ≥ 1/α. (revive, max_E_for, n). ★ic_series 는 dt 순 주입(leak 순서 의존)."""
    sd = float(sd) if sd and sd > 1e-9 else 1.0
    s = list(ic_series)
    if not s:
        return (False, 1.0, 0)
    ep = ConvexLeakEProcess(alpha=alpha, gamma=gamma)
    for ic in s:
        z = (float(ic) - float(baseline_ic)) / sd          # 회복 방향(baseline 위 = 양의 shift)
        ep.update(shift_lr(z, tau2=tau2))
    return (bool(ep.reject), float(ep.max_e), int(len(s)))


def omega_drift(omega_old: np.ndarray, omega_new: np.ndarray) -> tuple[float, float]:
    """상관구조 drift = (상대 Frobenius ‖ΔΩ‖/‖Ω‖, |Δlogdet(Ω)|). SECONDARY 입력.

    비양정치(slogdet sign≤0) 면 logdet divergence=inf(강제 re-fit). Ω 정렬은 호출자(같은 series).
    """
    A = np.asarray(omega_old, dtype=float)
    B = np.asarray(omega_new, dtype=float)
    fro_rel = float(np.linalg.norm(B - A) / (np.linalg.norm(A) + 1e-12))
    sa, la = np.linalg.slogdet(A)
    sb, lb = np.linalg.slogdet(B)
    logdet_div = abs(float(lb) - float(la)) if (sa > 0 and sb > 0) else float("inf")
    return (fro_rel, logdet_div)


def needs_refit(fro_rel: float, logdet_div: float, *,
                tau_fro: float = DEFAULT_TAU_FRO, tau_logdet: float = DEFAULT_TAU_LOGDET) -> bool:
    """SECONDARY re-fit 트리거: 상대 Frobenius 또는 logdet divergence 임계 초과(kill 아님)."""
    return fro_rel > tau_fro or logdet_div > tau_logdet


def weight_card_verdict(
    card: AssumptionCardLike,
    ic_series: Sequence[float],
    *,
    baseline_ic: float,
    sd: float,
    alpha: float = 0.05,
    tau2: float = 1.0,
) -> ValidationVerdict:
    """PRIMARY(score IC 붕괴) → ValidationVerdict (update_controller 입력 형식 재사용).

    holds_now = NOT 붕괴. fdr_significant·eprocess_significant = 붕괴 reject. evidence 에
    score IC·e-value 기록. p_value = 1/e (e-process 역수, 보고용 근사).
    """
    reject, e_value, n = score_ic_breakdown_eprocess(
        ic_series, baseline_ic=baseline_ic, sd=sd, alpha=alpha, tau2=tau2)
    ic_last = float(ic_series[-1]) if len(ic_series) else 0.0
    fmeta = (getattr(card, "falsification_metric", "") or "").strip()
    return ValidationVerdict(
        assumption_id=card.id, domain=card.domain, kind=card.kind,
        holds_now=(not reject),
        confidence_now=float(np.clip(abs(ic_last) * 10.0, 0.05, 0.95)),
        p_value=float(1.0 / e_value) if e_value > 1e-12 else 1.0,
        alpha_t=float(alpha),
        fdr_significant=reject,
        eprocess_significant=reject,
        falsifiable=bool(fmeta),
        evidence={"score_rank_ic": ic_last, "e_value": e_value, "n": n,
                  "primary_breakdown": reject,
                  "metric": "OOS Rank-IC anytime-valid e-process"},
        fdr_backbone="eprocess")


@dataclass
class WeightFalsificationResult:
    """DUAL falsification 산출. primary_kill→RETIRE / secondary_refit→TRANSITION 라우팅."""
    verdict: ValidationVerdict
    primary_kill: bool                       # score IC 붕괴 = kill (hard_falsifier)
    secondary_refit: bool                    # Ω drift = 재적합(kill 아님)
    drift: Optional[tuple[float, float]] = None   # (fro_rel, logdet_div) 또는 None


def evaluate_weight_card(
    card: AssumptionCardLike,
    ic_series: Sequence[float],
    *,
    baseline_ic: float,
    sd: float,
    omega_old: Optional[np.ndarray] = None,
    omega_new: Optional[np.ndarray] = None,
    tau_fro: float = DEFAULT_TAU_FRO,
    tau_logdet: float = DEFAULT_TAU_LOGDET,
    alpha: float = 0.05,
    tau2: float = 1.0,
) -> WeightFalsificationResult:
    """DUAL falsification 통합 — PRIMARY(score IC e-process) + SECONDARY(Ω drift).

    update_controller 연계: primary_kill → step(hard_falsifier=True)=RETIRE(즉시 live 차단).
    secondary_refit(only) → 정상 adopt gate 통해 TRANSITION(재적합). Ω 미제공 시 PRIMARY 만.
    """
    verdict = weight_card_verdict(card, ic_series, baseline_ic=baseline_ic, sd=sd,
                                  alpha=alpha, tau2=tau2)
    primary_kill = bool(verdict.fdr_significant)
    secondary_refit = False
    drift: Optional[tuple[float, float]] = None
    if omega_old is not None and omega_new is not None:
        fro, ld = omega_drift(omega_old, omega_new)
        drift = (fro, ld)
        secondary_refit = needs_refit(fro, ld, tau_fro=tau_fro, tau_logdet=tau_logdet)
    return WeightFalsificationResult(verdict=verdict, primary_kill=primary_kill,
                                     secondary_refit=secondary_refit, drift=drift)


if __name__ == "__main__":
    import numpy as np
    from core.assume.weight_card import WeightAssumptionCard
    from core.assume.registry import AssumptionRegistry
    from core.assume.dag import AssumptionDAG
    from core.assume.update_controller import UpdateController, UpdateAction

    rng = np.random.default_rng(7)

    def _wcard(id="weight.macro.recession"):
        return WeightAssumptionCard(
            id=id, version="v1", kind="parametric", scope="macro", domain="macro",
            statement="침체 거시 합성비중",
            falsification_metric="합성 score OOS Rank-IC anytime-valid e-process 붕괴 → kill",
            secondary_falsification="‖ΔΩ‖·logdet divergence > τ → re-fit",
            series_ids=("yc", "credit", "pmi"), w_global=(0.4, 0.3, 0.3))

    # 1) rank_ic — 단조/역단조/무상관
    s = [1, 2, 3, 4, 5]
    assert abs(rank_ic(s, [10, 20, 30, 40, 50])[0] - 1.0) < 1e-9
    assert abs(rank_ic(s, [50, 40, 30, 20, 10])[0] - (-1.0)) < 1e-9
    print(f"1) rank_ic OK: 단조={rank_ic(s, [10,20,30,40,50])[0]:.2f} 역={rank_ic(s, [50,40,30,20,10])[0]:.2f}")

    # 2) score IC 안정(baseline 유지) → e-process no reject (holds)
    ic_stable = list(0.05 + rng.normal(0, 0.01, 40))     # baseline 0.05 근처 유지
    rej_s, e_s, n_s = score_ic_breakdown_eprocess(ic_stable, baseline_ic=0.05, sd=0.02)
    assert rej_s is False, (rej_s, e_s)
    print(f"2) score IC 안정 → no kill: reject={rej_s} e={e_s:.3f} n={n_s}")

    # 3) ★score IC 붕괴(0.05 → -0.04 음전환) → e-process reject (PRIMARY kill)
    ic_break = list(0.05 + rng.normal(0, 0.01, 10)) + list(-0.04 + rng.normal(0, 0.01, 30))
    rej_b, e_b, n_b = score_ic_breakdown_eprocess(ic_break, baseline_ic=0.05, sd=0.02)
    assert rej_b is True, (rej_b, e_b)
    print(f"3) ★score IC 붕괴 → PRIMARY kill: reject={rej_b} e={e_b:.1f} (Ville: 거짓kill≤5%)")

    # 3b) ★§14.2 E_for(재진입 증거 대칭): reject 가설 IC 가 baseline 위로 회복 → revive /
    #     baseline 아래 정체 → convex-leak 누수 → revive X(phoenix 방어). E_against 와 부호 반전 대칭.
    ic_recover = list(-0.02 + rng.normal(0, 0.01, 10)) + list(0.10 + rng.normal(0, 0.01, 40))
    rev_r, ef_r, n_r = score_ic_recovery_eprocess(ic_recover, baseline_ic=0.02, sd=0.02)
    assert rev_r is True, (rev_r, ef_r)
    ic_flat = list(-0.02 + rng.normal(0, 0.01, 50))      # 회복 없음(baseline 아래 정체)
    rev_f, ef_f, _ = score_ic_recovery_eprocess(ic_flat, baseline_ic=0.02, sd=0.02)
    assert rev_f is False, (rev_f, ef_f)
    print(f"3b) ★E_for 재진입: 회복→revive={rev_r}(E_for={ef_r:.1f}) / 정체→revive={rev_f}(phoenix 방어, leak 누수)")

    # 4) Ω drift — 작음(no refit) / 큼(refit)
    O = np.array([[2.0, -0.5, 0.0], [-0.5, 2.0, 0.0], [0.0, 0.0, 1.0]])
    O_small = O + 0.02 * np.eye(3)
    O_big = O * 0.3 + np.array([[0, 0, 1.5], [0, 0, 0], [1.5, 0, 0]])  # 구조 급변
    f_s, l_s = omega_drift(O, O_small)
    f_b, l_b = omega_drift(O, O_big)
    assert not needs_refit(f_s, l_s) and needs_refit(f_b, l_b), ((f_s, l_s), (f_b, l_b))
    print(f"4) Ω drift OK: 작음 fro={f_s:.3f}(no refit) / 큼 fro={f_b:.3f} logdet={l_b:.2f}(refit)")

    # 5) ★DUAL → update_controller: PRIMARY 붕괴 = RETIRE (hard_falsifier 경유)
    reg = AssumptionRegistry(); dag = AssumptionDAG(reg)
    uc = UpdateController(reg, validator=None, dag=dag)
    c = _wcard(); reg.register(c)
    res_kill = evaluate_weight_card(c, ic_break, baseline_ic=0.05, sd=0.02,
                                    omega_old=O, omega_new=O_small)
    assert res_kill.primary_kill is True and res_kill.secondary_refit is False
    dec = uc.step(c, res_kill.verdict, hard_falsifier=res_kill.primary_kill,
                  as_of="2026-05-01", epoch=1)
    assert dec.action == UpdateAction.RETIRE, dec
    print(f"5) DUAL→uc: PRIMARY 붕괴 → {dec.action.value} (kill, live 즉시 차단)")

    # 6) ★SECONDARY only(score IC 견디는데 Ω drift) → kill 아님 → adopt gate(TRANSITION 후보)
    reg2 = AssumptionRegistry(); dag2 = AssumptionDAG(reg2)
    uc2 = UpdateController(reg2, validator=None, dag=dag2)
    c2 = _wcard("weight.macro.expansion"); reg2.register(c2)
    res_refit = evaluate_weight_card(c2, ic_stable, baseline_ic=0.05, sd=0.02,
                                     omega_old=O, omega_new=O_big)
    assert res_refit.primary_kill is False and res_refit.secondary_refit is True
    # SECONDARY = 재적합 트리거. holds_now=True(score 견딤) → retract 아님. 재적합은 adopt gate 경유.
    dec2 = uc2.step(c2, res_refit.verdict, hard_falsifier=False,
                    effect_size=0.6, dwell_ok=True, k_window_persist=2, same_regime=True,
                    as_of="2026-05-01", epoch=1)
    # holds_now=True → retract X. adopt gate 는 fdr_significant=False(붕괴 아님)라 KEEP — 재적합은
    # 별도 트리거(secondary_refit 플래그)로 오케스트레이터가 derive_weights 재실행 후 transition.
    assert dec2.action == UpdateAction.KEEP, dec2
    print(f"6) SECONDARY only: score 견딤 → uc={dec2.action.value}(kill X), refit 플래그={res_refit.secondary_refit}")

    # 7) verdict 패키징 형식 — update_controller 가 읽는 필드 충족
    v = res_kill.verdict
    assert v.assumption_id == c.id and v.fdr_significant is True
    assert v.evidence["primary_breakdown"] is True and v.fdr_backbone == "eprocess"
    print(f"7) verdict 패키징 OK: id={v.assumption_id} holds={v.holds_now} e={v.evidence['e_value']:.1f}")

    print("CL-W weight_falsification self-test PASS "
          "(rank_ic + score IC e-process 붕괴(PRIMARY kill) + Ω drift(SECONDARY refit) + DUAL→uc 라우팅)")
