"""core/structure/hierarchical_fdr.py — V7 BB-4 보강: cascade + e-process + power 게이트.

CONSULT-DECISIONS-whole-20260529.md §btn-button (전체구조 3R 자문, btn-Codlearn 확정):
- ① **hierarchical FDR cascade (Benjamini-Bogomolov)**: 거시 regime=부모가설을 **독립 substrate**
     에서 평가, 엄격 통과해야 자식 family 예산 해금(post-selection inference 차단). false-positive
     1개가 3도메인 동시 false discovery 되는 것을 막는다.
- ① **de-risking bypass**: 보호액션(노출 축소)만 per-stream 예산 우회 허용. **신규진입(노출 증가)
     부모게이트 우회 금지** (안전축).
- ② **e-process alpha-spending (anytime-valid)**: LORD++(FDR) 위에 test-martingale 을 얹어
     optional-stopping robust 화. "regime 보일 때까지 본다" = false-discovery 엔진 → Ville 부등식
     으로 임의정지에도 type-I ≤ alpha. p→e VS calibrator e=0.5/√p (E_H0[e]≤1).
- ③ **falsification POWER 게이트**: falsification_metric 형식 존재만으론 불충분 — 통계 power 하한
     필요. crypto post-ETF 처럼 baseline 부재/n 빈약이면 power≈0 → 보호 0 → block.

관측·산출만 — 결정 X. scipy.stats 우선, 부재 시 numpy fallback.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from core.structure.online_fdr import FdrDecision, LordPlusPlus

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


def _norm_ppf(q: float) -> float:
    if _HAS_SCIPY:
        return float(_sps.norm.ppf(q))
    # Acklam 근사 (scipy 부재 fallback)
    if q <= 0:
        return -math.inf
    if q >= 1:
        return math.inf
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if q < plow:
        x = math.sqrt(-2 * math.log(q))
        return (((((c[0]*x+c[1])*x+c[2])*x+c[3])*x+c[4])*x+c[5]) / ((((d[0]*x+d[1])*x+d[2])*x+d[3])*x+1)
    if q > phigh:
        x = math.sqrt(-2 * math.log(1 - q))
        return -(((((c[0]*x+c[1])*x+c[2])*x+c[3])*x+c[4])*x+c[5]) / ((((d[0]*x+d[1])*x+d[2])*x+d[3])*x+1)
    x = q - 0.5
    r = x * x
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*x / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


# ---------------------------------------------------------------------------
# ② e-process alpha-spending (anytime-valid)
# ---------------------------------------------------------------------------

def pvalue_to_evalue(p: float, kappa: float = 0.5) -> float:
    """VS(Vovk-Shafer) calibrator: e = κ·p^(κ-1), κ∈(0,1). E_H0[e]=∫κp^(κ-1)dp=1 (valid e-value).
    κ=0.5 → e = 0.5/√p. p 작을수록 e 커짐(증거 강함)."""
    p = float(min(max(p, 1e-12), 1.0))
    return float(kappa * p ** (kappa - 1.0))


@dataclass
class EDecision:
    reject: bool
    e_value: float           # 현 누적 E_t (test martingale)
    threshold: float         # 1/alpha (Ville)
    p_value: float
    t: int


class EProcessSpender:
    """anytime-valid e-process. 누적 E_t = Π e(p_s). Ville: P(sup_t E_t ≥ 1/α) ≤ α (H0).
    임의 정지·반복 peeking 에도 type-I ≤ α. 기각 시 E 리셋(다음 epoch 새 예산 = alpha-spending schedule).

    decay∈(0,1] = stale 증거 망각(E 를 1 쪽으로 수축; supermartingale 유지 → Ville 보장 불변).
    """
    def __init__(self, alpha: float = 0.05, kappa: float = 0.5, decay: float = 1.0):
        self.alpha = alpha
        self.kappa = kappa
        self.decay = decay
        self.threshold = 1.0 / alpha
        self._log_e = 0.0            # log E_t
        self.t = 0
        self.reject_times: list[int] = []
        self.max_e = 1.0

    def test(self, p_value: float) -> EDecision:
        self.t += 1
        if self.decay < 1.0:
            self._log_e *= self.decay     # 1(log0) 쪽으로 수축 = 망각
        self._log_e += math.log(pvalue_to_evalue(p_value, self.kappa))
        self._log_e = max(self._log_e, math.log(1e-12))   # 수치 하한
        e = math.exp(self._log_e)
        self.max_e = max(self.max_e, e)
        rej = e >= self.threshold
        if rej:
            self.reject_times.append(self.t)
            self._log_e = 0.0             # 한 단위 spend → 다음 epoch 리셋
        return EDecision(reject=rej, e_value=float(e), threshold=float(self.threshold),
                         p_value=float(p_value), t=self.t)

    @property
    def e_value(self) -> float:
        return math.exp(self._log_e)

    @property
    def n_rejections(self) -> int:
        return len(self.reject_times)


# ---------------------------------------------------------------------------
# ③ falsification POWER 게이트
# ---------------------------------------------------------------------------

@dataclass
class PowerVerdict:
    power: float                 # 추정 검정력 [0,1]
    protectable: bool            # power ≥ floor → 보호 의미 있음
    n_eff: int
    effect_size: float
    reason: str


def falsification_power(effect_size: float, n: int, alpha: float = 0.05,
                        sides: int = 2) -> float:
    """평균이동 effect_size(Cohen's d)를 n 표본·유의수준 α 에서 탐지할 검정력(z 근사).
    ncp = d·√n, power = 1 - Φ(z_{1-α/sides} - ncp). n=0/effect=0 → power→α(=무의미)."""
    if n <= 1 or effect_size <= 0:
        return float(alpha)       # 검정 불가 = 무작위 수준(보호 없음)
    z_a = _norm_ppf(1.0 - alpha / sides)
    ncp = abs(effect_size) * math.sqrt(n)
    power = 1.0 - _norm_cdf(z_a - ncp)
    return float(min(max(power, 0.0), 1.0))


def falsification_protectable(effect_size: float, n: int, *, alpha: float = 0.05,
                              power_floor: float = 0.5, has_baseline: bool = True) -> PowerVerdict:
    """형식+POWER 게이트. baseline 부재(crypto post-ETF) 또는 power<floor → protectable=False(block).
    '형식만 존재하고 power=0 이면 보호 0' (자문 결함#5)."""
    if not has_baseline:
        return PowerVerdict(power=0.0, protectable=False, n_eff=int(n), effect_size=float(effect_size),
                            reason="baseline 부재(예: crypto post-ETF 1회성) → power=0, 보호 무효")
    power = falsification_power(effect_size, n, alpha)
    ok = power >= power_floor
    return PowerVerdict(power=power, protectable=ok, n_eff=int(n), effect_size=float(effect_size),
                        reason=("ok" if ok else f"power {power:.2f} < floor {power_floor} → 보호 부족(block)"))


# ---------------------------------------------------------------------------
# ① hierarchical FDR cascade (Benjamini-Bogomolov) + de-risking bypass
# ---------------------------------------------------------------------------

@dataclass
class ParentState:
    parent_id: str
    passed: bool
    substrate_independent: bool
    p_value: float


@dataclass
class CascadeDecision:
    reject: bool
    reason: str                  # 'parent_passed' / 'parent_gate_locked' / 'de_risking_bypass'
    parent_id: str
    assumption_id: str
    action: str
    alpha_t: float = 0.0
    e_value: float = 0.0
    bypass: bool = False


class HierarchicalFDRCascade:
    """거시 regime=부모, 자식 가정=하위 family. 부모가 **독립 substrate** 에서 엄격 통과해야
    자식 family FDR 예산 해금(Benjamini-Bogomolov post-selection 차단). LORD++(자식 FDR) +
    선택적 e-process(anytime-valid) 동시 게이트. de-risking 보호액션만 부모게이트 우회 허용.
    """
    DE_RISKING_ACTIONS = {"de_risking", "reduce", "attenuate", "flatten", "halt_entry"}

    def __init__(self, alpha: float = 0.05, alpha_parent: float = 0.05, use_eprocess: bool = True):
        self.alpha = alpha
        self.alpha_parent = alpha_parent
        self.use_eprocess = use_eprocess
        self._parents: dict[str, ParentState] = {}
        self._child_lord: dict[tuple, LordPlusPlus] = {}
        self._child_eproc: dict[tuple, EProcessSpender] = {}
        self._bypass_lord: dict[tuple, LordPlusPlus] = {}   # de-risking 별 보수 스트림

    def evaluate_parent(self, parent_id: str, p_independent: float,
                        substrate_independent: bool = True) -> ParentState:
        """부모(거시 regime) 가설을 **독립 substrate** p-value 로 평가. 독립성 미보장이면 통과 불가
        (자식 re-derivation 와 같은 오염가능 substrate 면 post-selection 차단 의미가 사라짐)."""
        passed = bool(substrate_independent and p_independent <= self.alpha_parent)
        st = ParentState(parent_id=parent_id, passed=passed,
                         substrate_independent=bool(substrate_independent), p_value=float(p_independent))
        self._parents[parent_id] = st
        return st

    def _child_alpha(self, parent: ParentState) -> float:
        """BB: 부모 통과 시 자식 family 에 해금되는 예산. 통과 부모 1개 기준 selective α."""
        return self.alpha if parent.passed else 0.0

    def test_child(self, parent_id: str, assumption_id: str, p_value: float,
                   action: str = "new_entry") -> CascadeDecision:
        """자식 가정 검정. 부모 통과 → 정상 FDR(LORD++ [+e-process]). 부모 미통과 →
        de-risking 액션만 별 보수 스트림으로 우회 허용(신규진입은 block)."""
        parent = self._parents.get(parent_id)
        key = (parent_id, assumption_id)
        if parent is None or not parent.passed:
            if action in self.DE_RISKING_ACTIONS:
                # de-risking 보호: per-stream 보수 예산 우회 (부모게이트 무관, 안전축)
                s = self._bypass_lord.setdefault(key, LordPlusPlus(alpha=self.alpha / 2.0))
                d = s.test(p_value)
                return CascadeDecision(reject=d.reject, reason="de_risking_bypass", parent_id=parent_id,
                                       assumption_id=assumption_id, action=action, alpha_t=d.alpha_t,
                                       bypass=True)
            return CascadeDecision(reject=False, reason="parent_gate_locked", parent_id=parent_id,
                                   assumption_id=assumption_id, action=action, alpha_t=0.0)
        # 부모 통과 → 자식 FDR 예산 해금
        child_alpha = self._child_alpha(parent)
        lord = self._child_lord.setdefault(key, LordPlusPlus(alpha=child_alpha))
        d = lord.test(p_value)
        reject = d.reject
        e_val = 0.0
        if self.use_eprocess:
            ep = self._child_eproc.setdefault(key, EProcessSpender(alpha=child_alpha))
            ed = ep.test(p_value)
            e_val = ed.e_value
            reject = reject and ed.reject     # AND: FDR ∧ anytime-valid (optional-stopping robust)
        return CascadeDecision(reject=bool(reject), reason="parent_passed", parent_id=parent_id,
                               assumption_id=assumption_id, action=action, alpha_t=d.alpha_t,
                               e_value=float(e_val))


if __name__ == "__main__":
    import numpy as np
    rng = np.random.default_rng(17)

    # ② e-process: null → E 낮음(기각 희소) / 강신호 → E≥1/α 기각
    ep_null = EProcessSpender(alpha=0.05)
    n_null = sum(ep_null.test(float(p)).reject for p in rng.uniform(0, 1, 500))
    print(f"② e-process null 500 → 기각 {n_null} (max_e={ep_null.max_e:.2f})"); assert n_null <= 5
    ep_sig = EProcessSpender(alpha=0.05)
    rejected = False
    for _ in range(10):
        if ep_sig.test(1e-3).reject:
            rejected = True; break
    print(f"② e-process 강신호 → 기각={rejected} e_path max={ep_sig.max_e:.1f}"); assert rejected

    # ② optional-stopping robust: null 을 계속 peeking 해도 sup_t E 가 1/α 거의 안 넘음
    crossings = 0
    for _ in range(200):
        ep = EProcessSpender(alpha=0.05)
        crossed = any(ep.test(float(p)).reject for p in rng.uniform(0, 1, 100))
        crossings += int(crossed)
    print(f"② optional-stopping: 200 null-스트림 중 1/α 돌파 {crossings} (≤ ~α·200=10)")
    assert crossings <= 20, crossings

    # ③ power 게이트: 큰 n+effect → protectable / baseline 부재 → block / tiny n → block
    pv_ok = falsification_protectable(0.6, 120)
    pv_crypto = falsification_protectable(0.6, 4, has_baseline=False)
    pv_tiny = falsification_protectable(0.2, 5)
    print(f"③ power: ok(power={pv_ok.power:.2f},prot={pv_ok.protectable}) / "
          f"crypto({pv_crypto.protectable}:{pv_crypto.reason[:18]}) / tiny(power={pv_tiny.power:.2f},{pv_tiny.protectable})")
    assert pv_ok.protectable and not pv_crypto.protectable and not pv_tiny.protectable

    # ① cascade: 부모 미통과 → 신규진입 block / de-risking 우회 허용
    casc = HierarchicalFDRCascade(alpha=0.05)
    casc.evaluate_parent("macro.regime_shift", p_independent=0.40)   # 부모 미통과(p 큼)
    d_new = casc.test_child("macro.regime_shift", "equity.cyclical_cheap", 1e-4, action="new_entry")
    d_risk = casc.test_child("macro.regime_shift", "equity.cyclical_cheap", 1e-4, action="de_risking")
    print(f"① 부모미통과: new_entry reject={d_new.reject}({d_new.reason}) / "
          f"de_risking reject={d_risk.reject}({d_risk.reason})")
    assert d_new.reject is False and d_new.reason == "parent_gate_locked"
    assert d_risk.bypass and d_risk.reason == "de_risking_bypass"

    # ① BB 독립 substrate: p 작아도 substrate 비독립이면 부모 통과 불가
    p_dep = casc.evaluate_parent("macro.regime2", p_independent=1e-5, substrate_independent=False)
    print(f"① 비독립 substrate: parent passed={p_dep.passed} (p작아도 통과불가)")
    assert p_dep.passed is False

    # ① 부모 통과 → 자식 family 예산 해금 (FDR∧e-process 강신호 기각)
    casc.evaluate_parent("macro.regime3", p_independent=1e-4, substrate_independent=True)
    rj = any(casc.test_child("macro.regime3", "commodity.carry_premium", 1e-5,
                             action="new_entry").reject for _ in range(8))
    print(f"① 부모통과 후 자식 강신호 → 기각={rj}"); assert rj

    print("hierarchical_fdr self-test PASS "
          "(① cascade+BB독립substrate+de-risking bypass · ② e-process anytime-valid · ③ power 게이트)")
