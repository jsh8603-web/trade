"""tests/structure/test_eprocess_backbone_properties.py — R4/R5 e-value backbone V&V.

R5 유일 material·직교 잔여 = 검증기 자체의 V&V/구현 정합성(수식 맞아도 코드버그면 全보증 silent
붕괴). e-allocation 의 핵심 불변식을 property-based 로 보호:
  P1. replay reorder-invariance (dt내 순서 무관 = bitemporal 재현 결정론)
  P2. Ville 보존 (H0 e-process false-alarm ≤ α, Monte Carlo 보수 상한)
  P3. e-LOND 임의의존 robust (자기상관 null 에서도 FDR 폭주 X)
  P4. graph e-allocation 안전축 (부모 잠김 → new_entry 절대 reject X)
"""

from __future__ import annotations

import numpy as np
import pytest

from core.structure.eprocess_backbone import (
    MixtureSPRTEProcess, ELOND, GraphEAllocation,
)


# --- P1: replay reorder-invariance ------------------------------------------

@pytest.mark.parametrize("seed", [1, 7, 42, 100, 2026])
def test_replay_reorder_invariance(seed):
    """같은 dt 의 관측은 순서를 어떻게 섞어도 as-of E 가 동일해야 (폐형 E=f(S,n), S·n 순서불변)."""
    rng = np.random.default_rng(seed)
    xs = [(1, float(v)) for v in rng.normal(0, 1, 25)] + [(2, float(v)) for v in rng.normal(0.5, 1, 10)]
    base = MixtureSPRTEProcess.replay_value(xs, cut_dt=1, tau2=1.0)
    for _ in range(20):
        perm = list(rng.permutation(np.array(xs, dtype=object)))
        perm = [(int(d), float(x)) for d, x in perm]
        assert abs(MixtureSPRTEProcess.replay_value(perm, cut_dt=1, tau2=1.0) - base) < 1e-9


def test_replay_cut_monotone_in_n():
    """dt-cut 을 늘리면 누적 관측만 증가 (cut=1 ⊂ cut=2 의 S·n)."""
    xs = [(1, 0.5), (1, -0.3), (2, 1.2), (3, 0.1)]
    e1 = MixtureSPRTEProcess.replay_value(xs, cut_dt=1)
    e2 = MixtureSPRTEProcess.replay_value(xs, cut_dt=2)
    # 동일 데이터로 online update 한 값과 일치해야 (telescoping)
    ep = MixtureSPRTEProcess()
    for _, x in [p for p in xs if p[0] <= 2]:
        ep.update(x)
    assert abs(ep.e_value - e2) < 1e-9 and e1 > 0


# --- P2: Ville 보존 (H0 false-alarm ≤ α) ------------------------------------

def test_ville_false_alarm_bound():
    """H0(N(0,1)) 하에서 e-process 가 1/α 를 넘는 경로 비율 ≤ α (Ville). 보수 상한 2α 로 검증."""
    rng = np.random.default_rng(11)
    alpha = 0.05
    trials, crossed = 400, 0
    for _ in range(trials):
        ep = MixtureSPRTEProcess(alpha=alpha, tau2=1.0)
        hit = False
        for x in rng.normal(0, 1, 150):
            if ep.update(float(x)).reject:
                hit = True
                break
        crossed += int(hit)
    rate = crossed / trials
    assert rate <= 2 * alpha, f"false-alarm {rate} > 2α (Ville 위반 의심)"


def test_eprocess_power_on_shift():
    """실제 mean-shift 면 거의 항상 탐지 (power)."""
    rng = np.random.default_rng(13)
    hits = 0
    for _ in range(50):
        ep = MixtureSPRTEProcess(alpha=0.05, tau2=1.0)
        if any(ep.update(float(x)).reject for x in rng.normal(0.7, 1, 80)):
            hits += 1
    assert hits >= 45


# --- P3: e-LOND 임의의존 robust ----------------------------------------------

def test_elond_fdr_control_under_autocorrelation():
    """자기상관(AR(1)) null e-value 스트림에서도 e-LOND 발견율이 폭주하지 않아야
    (p값 LOND 의 독립가정 취약성 회피 = e값 backbone 채택 근거)."""
    rng = np.random.default_rng(17)
    n = 600
    # AR(1) 잠재 → uniform PIT → VS e-value (평균 1). 자기상관 주입.
    z = np.zeros(n)
    for t in range(1, n):
        z[t] = 0.8 * z[t - 1] + rng.normal(0, 1)
    from scipy import stats
    u = stats.norm.cdf(z)                 # 자기상관 있으나 주변분포 ~ Uniform (H0)
    e_vals = 0.5 / np.sqrt(np.clip(u, 1e-12, 1.0))
    el = ELOND(alpha=0.05)
    disc = sum(el.test(float(e)).reject for e in e_vals)
    assert disc <= 15, f"자기상관 null 에서 발견 {disc} 폭주 (e-LOND robust 실패)"


def test_elond_discovers_strong_signal():
    """강신호는 발견. 단, e-LOND budget α_t=α·γ_t·(D+1), γ_t=1/t² 는 front-load — online FDR 특성상
    후반 가설은 더 큰 e 필요. 강신호가 예산 충분한 구간이면 발견(여기선 초반 배치)."""
    rng = np.random.default_rng(19)
    el = ELOND(alpha=0.05)
    seq = [1000.0] * 5 + list(0.5 / np.sqrt(rng.uniform(0, 1, 100)))  # 강신호 초반
    disc = sum(el.test(float(e)).reject for e in seq)
    assert disc >= 3


# --- P4: graph e-allocation 안전축 -------------------------------------------

@pytest.mark.parametrize("e_value", [1.0, 50.0, 1e6])
def test_graph_locked_parent_never_rejects_new_entry(e_value):
    """부모 e-process 미돌파 시 자식 new_entry 는 e값이 아무리 커도 reject 금지 (post-selection 차단)."""
    g = GraphEAllocation(alpha=0.05)
    d = g.test_child("macro.p", "child.c", e_value, action="new_entry")
    assert d.reject is False and d.reason == "parent_locked"


def test_graph_decay_freezes_new_entry_but_allows_derisk():
    g = GraphEAllocation(alpha=0.05)
    # 부모 해금
    rng = np.random.default_rng(3)
    for x in rng.normal(1.2, 1, 80):
        g.update_parent("macro.p", float(x))
    assert g.parent_unlocked("macro.p")
    g.set_parent_decay("macro.p", True)
    d_new = g.test_child("macro.p", "c", 1e6, action="new_entry")
    d_risk = g.test_child("macro.p", "c", 1e6, action="de_risking")
    # 안전축: decay 시 new_entry 동결, de-risk 는 동결 X (평가 허용 = node de-risk 가능)
    assert d_new.reject is False and d_new.reason == "parent_decayed_freeze"
    assert d_risk.reason != "parent_decayed_freeze"
