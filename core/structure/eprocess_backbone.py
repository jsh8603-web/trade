"""core/structure/eprocess_backbone.py — R4/R5 robustness 업그레이드 (btn-Codlearn 전체구조 자문).

CONSULT-DECISIONS-whole-20260529.md §R4·§R5. 금융 regime 자기상관에서 p값 LORD++/SAFFRON 은
독립가정 필요·취약 → **e-value backbone 으로 마이그레이션**. e값 = 임의의존 robust + optional-
stopping robust (Ville: P(sup_t E_t≥1/α)≤α). 단일 e-substrate, readout 2개:
  - e-process    = regime/baseline 변경 1급 증거 (sup E ≥ 1/α, anytime-valid)
  - e-LOND       = 발견율(online FDR) — e값 구동, 임의의존 FDR 제어

구성:
- MixtureSPRTEProcess : Robbins/GROW mixture test martingale E_t=∫∏(f_θ/f_0)dπ (mean-shift, 폐형).
- ELOND              : e값 online FDR (Wang-Ramdas, 임의의존 robust).
- GraphEAllocation   : W(node,t) DAG wealth 분할 × node e-LOND, 부모 e 1/α 돌파→자식 해금/decay→freeze.
- SpecSentinel       : wrong-H0 방어 — PIT uniformity(Vovk) + exchangeability test martingale → abstain.
- ReverseEProcess+ECUSUM : economic decay(최근<과거) detector, regime 과 판별.

증분 ℓ_t=E_t/E_{t-1} 은 (dt,vt) 키 로그 → as-of 누적 = dt≤cut 곱(dt내 순서무관, S·n 순서불변→폐형 E 불변).
관측·산출만, 결정 X. scipy 우선, numpy fallback.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np

try:
    from scipy import stats as _sps
    _HAS_SCIPY = True
except Exception:                       # pragma: no cover
    _sps = None
    _HAS_SCIPY = False


def _norm_cdf(z: float) -> float:
    if _HAS_SCIPY:
        return float(_sps.norm.cdf(z))
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


# ---------------------------------------------------------------------------
# e-process backbone — Robbins/GROW mixture SPRT test martingale
# ---------------------------------------------------------------------------

@dataclass
class EDecision:
    reject: bool
    e_value: float
    threshold: float
    increment: float          # ℓ_t = E_t/E_{t-1} (replay 로그용)
    t: int


class MixtureSPRTEProcess:
    """정규 mean-shift 의 mixture test martingale (Robbins-Siegmund 폐형).
    표준화 관측 x_t (H0: N(0,1)) · alt mean θ~N(0,τ²) 혼합:
        E_t = (1+τ²n)^(-1/2)·exp( τ²·S² / (2(1+τ²n)) ),  S=Σx_i.
    E_0=1, nonneg martingale → Ville: P(sup E_t≥1/α)≤α (optional-stopping·임의의존 robust).

    two_sided=False (decay 용): x_t 를 그대로 쓰되 S 단측 — 음/양 한쪽 shift 만 키움(부호 transform 으로 처리).
    """
    def __init__(self, alpha: float = 0.05, tau2: float = 1.0):
        self.alpha = alpha
        self.tau2 = tau2
        self.threshold = 1.0 / alpha
        self.S = 0.0
        self.n = 0
        self._log_e = 0.0
        self.max_e = 1.0
        self.reject_times: list[int] = []

    @staticmethod
    def _log_e_closed(S: float, n: int, tau2: float) -> float:
        denom = 1.0 + tau2 * n
        return -0.5 * math.log(denom) + (tau2 * S * S) / (2.0 * denom)

    def update(self, x: float) -> EDecision:
        prev = self._log_e
        self.S += float(x)
        self.n += 1
        self._log_e = self._log_e_closed(self.S, self.n, self.tau2)
        e = math.exp(self._log_e)
        self.max_e = max(self.max_e, e)
        rej = e >= self.threshold
        if rej:
            self.reject_times.append(self.n)
        return EDecision(reject=rej, e_value=float(e), threshold=float(self.threshold),
                         increment=float(math.exp(self._log_e - prev)), t=self.n)

    @property
    def e_value(self) -> float:
        return math.exp(self._log_e)

    @staticmethod
    def replay_value(xs_by_dt: list[tuple], cut_dt, tau2: float = 1.0) -> float:
        """as-of 재현: (dt, x) 목록에서 dt≤cut 누적 S·n 으로 폐형 E 계산. dt내 순서무관(S·n 순서불변).
        증분 곱 telescoping 과 동일 — reorder-invariant 재현 보장."""
        S, n = 0.0, 0
        for dt, x in xs_by_dt:
            if dt <= cut_dt:
                S += float(x); n += 1
        if n == 0:
            return 1.0
        return math.exp(MixtureSPRTEProcess._log_e_closed(S, n, tau2))


def _gamma_inv_sq(t: int) -> float:
    """γ_t = (6/π²)/t² , Σ_{t≥1} γ_t = 1 (e-LOND budget 분할)."""
    return (6.0 / (math.pi ** 2)) / (t * t)


@dataclass
class ELONDDecision:
    reject: bool
    e_value: float
    alpha_t: float            # 이 가설 budget
    n_discoveries: int
    t: int


class ELOND:
    """e값 구동 online FDR (Wang & Ramdas 2022). reject_i ⟺ e_i ≥ 1/α_i,
    α_i = α·γ_i·(D_{i-1}+1). e값 평균 ≤1 (H0) + Markov → **임의의존**에서 FDR ≤ α (p값 LOND 와 달리
    의존가정 불요 = 금융 regime 자기상관 robust). e-process 와 동일 e-substrate 소비(2번째 readout)."""
    def __init__(self, alpha: float = 0.05, gamma: Callable[[int], float] = _gamma_inv_sq):
        self.alpha = alpha
        self.gamma = gamma
        self.t = 0
        self.n_disc = 0

    def test(self, e_value: float) -> ELONDDecision:
        self.t += 1
        alpha_t = self.alpha * self.gamma(self.t) * (self.n_disc + 1)
        rej = float(e_value) * alpha_t >= 1.0     # e ≥ 1/α_t
        if rej:
            self.n_disc += 1
        return ELONDDecision(reject=rej, e_value=float(e_value), alpha_t=float(alpha_t),
                             n_discoveries=self.n_disc, t=self.t)


# ---------------------------------------------------------------------------
# R4-B graph-structured online e-allocation (DAG e-wealth)
# ---------------------------------------------------------------------------

@dataclass
class GraphDecision:
    reject: bool
    reason: str               # 'parent_unlocked' / 'parent_locked' / 'parent_decayed_freeze' / 'de_risking_bypass'
    node: str
    parent: Optional[str]
    e_value: float = 0.0
    bypass: bool = False


class GraphEAllocation:
    """거시 DAG(부모 regime → 자식 family) 의 online e-wealth 배분. 단순 합성이 아니라 graph-structured:
    부모 node e-process 가 1/α 돌파 → 자식 family wealth 해금(R2 게이트=e-wealth 표현). 부모 decay 점화
    → 자식 freeze(de-risk only). 자식 검정 = node-local ELOND. reorder-invariant(폐형 E, S·n 순서불변).

    de-risking 보호액션만 부모 잠김에도 우회(per-node 보수 budget). 신규진입 우회 금지(안전축).
    """
    DE_RISKING = {"de_risking", "reduce", "attenuate", "flatten", "halt_entry"}

    def __init__(self, alpha: float = 0.05, tau2: float = 1.0):
        self.alpha = alpha
        self.tau2 = tau2
        self._parent_ep: dict[str, MixtureSPRTEProcess] = {}
        self._parent_decay: dict[str, bool] = {}
        self._child_elond: dict[str, ELOND] = {}
        self._bypass_elond: dict[str, ELOND] = {}

    def update_parent(self, parent: str, x: float) -> bool:
        """부모 regime 증거 1틱. e-process 1/α 돌파 시 unlocked=True (자식 wealth 해금)."""
        ep = self._parent_ep.setdefault(parent, MixtureSPRTEProcess(alpha=self.alpha, tau2=self.tau2))
        ep.update(x)
        return ep.e_value >= ep.threshold

    def set_parent_decay(self, parent: str, decayed: bool) -> None:
        """ReverseEProcess/E-CUSUM 결과 주입 — decay 시 자식 freeze(de-risk only)."""
        self._parent_decay[parent] = bool(decayed)

    def parent_unlocked(self, parent: str) -> bool:
        ep = self._parent_ep.get(parent)
        return bool(ep and ep.e_value >= ep.threshold)

    def test_child(self, parent: str, child: str, e_value: float,
                   action: str = "new_entry") -> GraphDecision:
        key = f"{parent}/{child}"
        decayed = self._parent_decay.get(parent, False)
        unlocked = self.parent_unlocked(parent)
        # 부모 decay → 자식 freeze: de-risk 만 허용
        if decayed and action not in self.DE_RISKING:
            return GraphDecision(reject=False, reason="parent_decayed_freeze", node=child,
                                 parent=parent, e_value=float(e_value))
        if not unlocked:
            if action in self.DE_RISKING:
                s = self._bypass_elond.setdefault(key, ELOND(alpha=self.alpha / 2.0))
                d = s.test(e_value)
                return GraphDecision(reject=d.reject, reason="de_risking_bypass", node=child,
                                     parent=parent, e_value=float(e_value), bypass=True)
            return GraphDecision(reject=False, reason="parent_locked", node=child,
                                 parent=parent, e_value=float(e_value))
        s = self._child_elond.setdefault(key, ELOND(alpha=self.alpha))
        d = s.test(e_value)
        return GraphDecision(reject=d.reject, reason="parent_unlocked", node=child,
                             parent=parent, e_value=float(e_value))


# ---------------------------------------------------------------------------
# R5-C spec sentinel 층 (wrong-H0 방어)
# ---------------------------------------------------------------------------

@dataclass
class SentinelVerdict:
    fired: bool
    which: list                # ['pit_uniformity', 'exchangeability'] 중 점화된 것
    pit_e: float
    exch_e: float
    action: str                # 'ok' / 'abstain' (primary e validity 강등)


def pit_uniformity_martingale(u: np.ndarray, alpha: float = 0.05,
                              lambdas=(-0.9, -0.5, 0.5, 0.9)) -> float:
    """PIT 값 u_t (모델 정확 시 Uniform[0,1]) 의 model-free test martingale (Vovk betting).
    betting M = ∏(1 + λ(2u-1)) 를 λ grid 혼합. 비균일(모델 spec 오류)이면 max E↑. 반환=max E."""
    u = np.asarray(u, float)
    g = 2.0 * u - 1.0                     # [-1,1], H0 대칭평균 0
    log_es = np.zeros(len(lambdas))
    max_e = 1.0
    for gi in g:
        for j, lam in enumerate(lambdas):
            log_es[j] += math.log(max(1.0 + lam * gi, 1e-12))
        e = float(np.mean(np.exp(log_es)))   # 혼합 = 평균 (각 λ martingale, E[e]=1)
        max_e = max(max_e, e)
    return max_e


def exchangeability_martingale(scores: np.ndarray, alpha: float = 0.05) -> float:
    """교환성(exchangeability) 붕괴 test martingale. conformal 식: 각 시점 score 의 정규화 순위
    r_t∈(0,1) 를 PIT 로 보고 인접 추세(자기상관)에 betting. 교환성 성립 시 r_t≈Uniform·iid →
    추세 없음(E≈1). regime 전이로 score 가 추세화하면 E↑. 반환=max E."""
    s = np.asarray(scores, float)
    n = len(s)
    if n < 3:
        return 1.0
    # 온라인 conformal rank: r_t = (#{s_i ≤ s_t, i<t}+1)/(t+1)
    r = np.empty(n)
    for t in range(n):
        r[t] = (np.sum(s[:t] <= s[t]) + 1) / (t + 2)
    # 추세 betting: 연속 rank 의 부호상관(증가추세=비교환). g_t = sign-aligned (r_t-0.5)(r_{t-1}-0.5)
    dr = r - 0.5
    g = np.sign(dr[1:] * dr[:-1])         # +1 동방향(추세), -1 반전
    log_e = 0.0
    max_e = 1.0
    lam = 0.5
    for gi in g:
        log_e += math.log(max(1.0 + lam * gi, 1e-12))
        max_e = max(max_e, math.exp(log_e))
    return max_e


class SpecSentinel:
    """독립 spec sentinel 층. e-process 는 **고른 null 상대**만 anytime-valid(틀린 null 무방비).
    PIT uniformity(calibration null) + exchangeability(교환성=Q4 regime 공유) test martingale 점화 시
    → primary e validity 강등 → abstain (judge 'expected-errored→abstain' 동형)."""
    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha
        self.threshold = 1.0 / alpha

    def check(self, pit_values, conformal_scores=None) -> SentinelVerdict:
        pit_e = pit_uniformity_martingale(pit_values, self.alpha)
        exch_e = exchangeability_martingale(conformal_scores, self.alpha) if conformal_scores is not None else 1.0
        which = []
        if pit_e >= self.threshold:
            which.append("pit_uniformity")
        if exch_e >= self.threshold:
            which.append("exchangeability")
        fired = bool(which)
        return SentinelVerdict(fired=fired, which=which, pit_e=round(pit_e, 3),
                               exch_e=round(exch_e, 3), action=("abstain" if fired else "ok"))


# ---------------------------------------------------------------------------
# R5-D economic decay vs regime detector (reverse e-process + E-CUSUM)
# ---------------------------------------------------------------------------

@dataclass
class DecayVerdict:
    decayed: bool             # reverse e-process 또는 E-CUSUM 점화 (최근 edge < 과거)
    reverse_e: float
    ecusum_max: float
    classification: str       # 'decay'(node 특이·monotone) / 'regime'(sibling 동기화+exch) / 'none'
    recommend: str            # 'node_de_risk' / 'parent_freeze' / 'none'


class ReverseEProcess:
    """node-local reverse e-process. null='최근 edge=과거 baseline', alt='최근<과거'(edge 감소).
    edge 시계열 x_t 를 (baseline - x_t) 로 transform 후 mixture SPRT(양의 shift=decay) — wealth 상승
    중에도 slope↓ 면 점화. baseline=초기 window 평균."""
    def __init__(self, alpha: float = 0.05, tau2: float = 1.0, baseline_window: int = 20):
        self.ep = MixtureSPRTEProcess(alpha=alpha, tau2=tau2)
        self.baseline_window = baseline_window
        self._buf: list[float] = []
        self.baseline: Optional[float] = None
        self.sd: float = 1.0

    def update(self, edge: float) -> float:
        self._buf.append(float(edge))
        if self.baseline is None:
            if len(self._buf) >= self.baseline_window:
                arr = np.array(self._buf)
                self.baseline = float(arr.mean())
                self.sd = float(arr.std(ddof=1)) or 1.0
            return 1.0
        z = (self.baseline - edge) / self.sd     # decay(edge↓) → 양수 → E↑
        self.ep.update(z)
        return self.ep.e_value


def e_cusum(series: np.ndarray, baseline: float, sd: float, *, tau2: float = 1.0,
            alpha: float = 0.05) -> float:
    """E-CUSUM changepoint (e-detector): 누적 곱을 max(1,·) 로 reset 하며 운용 → 변화점에서 급등.
    reverse 방향(baseline 대비 하락) 누적. 반환=max detector 값(≥1/α=changepoint)."""
    s = np.asarray(series, float)
    R = 1.0
    max_r = 1.0
    log_R = 0.0
    for x in s:
        z = (baseline - x) / sd
        # 단일 관측 likelihood ratio (θ=tau under alt, 양의 shift)
        ll = math.exp(tau2 * z - 0.5 * tau2 * tau2)   # f_θ/f_0, θ=√tau2 근사
        log_R = max(0.0, log_R + math.log(max(ll, 1e-12)))   # SR/CUSUM reset at 1
        max_r = max(max_r, math.exp(log_R))
    return max_r


def classify_decay_vs_regime(node_decayed: bool, sibling_decay_count: int,
                             exchangeability_fired: bool, monotone: bool) -> DecayVerdict:
    """판별 (R5 Q4): regime=다수 sibling 동기화 + exchangeability 동반점화 → 부모 freeze /
    decay=node 특이·monotone·exchangeability 침묵 → node de-risk(monotone-down)."""
    if not node_decayed:
        return DecayVerdict(False, 0.0, 0.0, "none", "none")
    if sibling_decay_count >= 2 and exchangeability_fired:
        cls, rec = "regime", "parent_freeze"
    elif monotone and not exchangeability_fired:
        cls, rec = "decay", "node_de_risk"
    else:
        cls, rec = "decay", "node_de_risk"     # 기본: 보수적으로 node de-risk
    return DecayVerdict(True, 0.0, 0.0, cls, rec)


if __name__ == "__main__":
    rng = np.random.default_rng(23)

    # A) MixtureSPRTEProcess: null(N(0,1)) → E 낮음 / mean-shift → E≥1/α
    ep = MixtureSPRTEProcess(alpha=0.05, tau2=1.0)
    nrej = sum(ep.update(float(x)).reject for x in rng.normal(0, 1, 300))
    print(f"A) e-process null 300 → 기각 {nrej} max_e={ep.max_e:.2f}"); assert nrej <= 3
    ep2 = MixtureSPRTEProcess(alpha=0.05, tau2=1.0)
    crossed = False
    for x in rng.normal(0.8, 1, 50):
        if ep2.update(float(x)).reject: crossed = True; break
    print(f"A2) mean-shift(0.8) → 돌파={crossed} max_e={ep2.max_e:.1f}"); assert crossed

    # A3) replay reorder-invariance: dt내 순서 섞어도 as-of E 동일 (폐형 S·n 순서불변)
    xs = [(1, 0.5), (1, -0.2), (1, 1.1), (2, 0.3)]
    e_fwd = MixtureSPRTEProcess.replay_value(xs, cut_dt=1)
    e_rev = MixtureSPRTEProcess.replay_value(list(reversed(xs)), cut_dt=1)
    print(f"A3) replay dt=1 정/역순 E = {e_fwd:.6f} / {e_rev:.6f} (동일=reorder-invariant)")
    assert abs(e_fwd - e_rev) < 1e-12

    # B) ELOND: null e값(평균≤1) → 발견 희소 / 강한 e값 → 발견
    el = ELOND(alpha=0.05)
    # null e-value = 0.5/sqrt(U) (평균 1)
    null_e = 0.5 / np.sqrt(rng.uniform(0, 1, 500))
    nd = sum(el.test(float(e)).reject for e in null_e)
    print(f"B) e-LOND null 500 → 발견 {nd} (FDR 제어, 소수)"); assert nd <= 10
    el2 = ELOND(alpha=0.05)
    nd2 = sum(el2.test(500.0).reject for _ in range(10))
    print(f"B2) e-LOND 강신호(e=500)×10 → 발견 {nd2}"); assert nd2 >= 5

    # C) GraphEAllocation: 부모 잠김→신규진입 block / de-risk bypass / 부모 해금→자식 발견 / decay→freeze
    g = GraphEAllocation(alpha=0.05, tau2=1.0)
    # 부모 미돌파 상태
    d_lock = g.test_child("macro.regimeX", "crypto.mvrv", 500.0, action="new_entry")
    d_byp = g.test_child("macro.regimeX", "crypto.mvrv", 500.0, action="de_risking")
    print(f"C) 부모잠김: new_entry={d_lock.reject}({d_lock.reason}) / de_risk={d_byp.reject}({d_byp.reason})")
    assert d_lock.reject is False and d_lock.reason == "parent_locked"
    assert d_byp.bypass and d_byp.reason == "de_risking_bypass"
    # 부모 해금
    unlocked = False
    for x in rng.normal(1.0, 1, 60):
        if g.update_parent("macro.regimeX", float(x)): unlocked = True; break
    print(f"C2) 부모 e-process 해금={unlocked}"); assert unlocked
    rj = any(g.test_child("macro.regimeX", "crypto.mvrv", 500.0, action="new_entry").reject for _ in range(6))
    print(f"C3) 부모해금 후 자식 강신호 발견={rj}"); assert rj
    g.set_parent_decay("macro.regimeX", True)
    d_freeze = g.test_child("macro.regimeX", "crypto.mvrv", 500.0, action="new_entry")
    print(f"C4) 부모 decay → 자식 freeze: new_entry={d_freeze.reject}({d_freeze.reason})")
    assert d_freeze.reject is False and d_freeze.reason == "parent_decayed_freeze"

    # D) SpecSentinel: 균일 PIT → ok / 치우친 PIT(spec 오류) → abstain
    sent = SpecSentinel(alpha=0.05)
    v_ok = sent.check(rng.uniform(0, 1, 300))
    skewed = rng.beta(2.5, 1.0, 300)          # 비균일 = null spec 오류
    v_bad = sent.check(skewed)
    print(f"D) sentinel: 균일 fired={v_ok.fired}(pit_e={v_ok.pit_e}) / 치우침 fired={v_bad.fired}"
          f"(pit_e={v_bad.pit_e},act={v_bad.action})")
    assert v_ok.fired is False and v_bad.fired is True and v_bad.action == "abstain"
    # exchangeability: iid → 침묵 / 추세(regime) → 점화
    exch_iid = exchangeability_martingale(rng.normal(0, 1, 200))
    trend = np.cumsum(rng.normal(0.15, 1, 200))
    exch_tr = exchangeability_martingale(trend)
    print(f"D2) exchangeability: iid E={exch_iid:.2f} / 추세 E={exch_tr:.2f}")
    assert exch_tr > exch_iid

    # E) decay vs regime: reverse e-process(edge 감소) 점화 + 판별
    rev = ReverseEProcess(alpha=0.05, tau2=1.0, baseline_window=20)
    edges = np.concatenate([rng.normal(1.0, 0.3, 30), np.linspace(1.0, -0.5, 60)])  # 후반 단조 감소
    decay_fired = False
    for e in edges:
        if rev.update(float(e)) >= rev.ep.threshold: decay_fired = True
    print(f"E) reverse e-process decay 점화={decay_fired} max_e={rev.ep.max_e:.1f}"); assert decay_fired
    ec = e_cusum(np.linspace(1.0, -0.5, 60), baseline=1.0, sd=0.3)
    print(f"E2) E-CUSUM max={ec:.1f} (≥1/α=20 changepoint)"); assert ec >= 20
    dv_decay = classify_decay_vs_regime(True, sibling_decay_count=0, exchangeability_fired=False, monotone=True)
    dv_regime = classify_decay_vs_regime(True, sibling_decay_count=3, exchangeability_fired=True, monotone=False)
    print(f"E3) 판별: 단독monotone={dv_decay.classification}/{dv_decay.recommend} / "
          f"sibling+exch={dv_regime.classification}/{dv_regime.recommend}")
    assert dv_decay.recommend == "node_de_risk" and dv_regime.recommend == "parent_freeze"

    print("eprocess_backbone self-test PASS "
          "(e-process backbone + e-LOND · graph e-allocation · spec sentinel · decay-vs-regime)")
