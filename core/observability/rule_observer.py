"""core/observability/rule_observer.py — RuleObserver 5지표 + divergence (S6, F축).

claude R6: **divergence(shadow↔live)가 안전 1차 방어선**. drift(모델)보다 divergence
(실행 괴리)가 라이브 사고에 선행한다. R1~5 에서 가장 약했던 축.

5 지표 (claude R6 RuleObserver):
  ①decision agreement rate (shadow vs live)
  ②signal staleness (as_of − knowledge_date) — 누적 = PIT 누수 신호
  ③residual drift pctile (PSI + 0근방 질량)
  ④veto/force-include 빈도
  ⑤archetype별 활성도

조기 감지: Page-Hinkley/CUSUM(잔차) + agreement-rate 급락 + abstention spike
  = 큐와 분리된 fast-path alert.
Rule-level Stop (R6 gemini): 룰 누적 OOS MDD −5% 터치 → 그 rule 신호 Mute.

⛔ **모듈 4분리 (claude R6): 관측은 read-only. 제어를 직접 못 건드린다.**
   이 클래스는 alert/mute "신호"를 반환만 한다. 실제 Mute 집행은 RolloutController(외부) 몫.
   여기서 rule 을 끄거나 주문을 막지 않는다 (관측≠제어).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


# --- 통계 primitive ---------------------------------------------------------

def psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """Population Stability Index. >0.25 = 심한 분포 이동."""
    expected = np.asarray(expected, float); actual = np.asarray(actual, float)
    expected = expected[np.isfinite(expected)]; actual = actual[np.isfinite(actual)]
    if len(expected) < bins or len(actual) < 1:
        return float("nan")
    edges = np.quantile(expected, np.linspace(0, 1, bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    e_pct = np.histogram(expected, edges)[0] / len(expected)
    a_pct = np.histogram(actual, edges)[0] / len(actual)
    e_pct = np.clip(e_pct, 1e-6, None); a_pct = np.clip(a_pct, 1e-6, None)
    return float(np.sum((a_pct - e_pct) * np.log(a_pct / e_pct)))


def near_zero_mass(resid: np.ndarray, band: float = 0.25) -> float:
    """잔차 0근방 질량 비율. ↑ = 밸류트랩 밀집(싸 보이나 진짜 저평가 아님) 신호."""
    r = np.asarray(resid, float); r = r[np.isfinite(r)]
    return float(np.mean(np.abs(r) < band)) if len(r) else float("nan")


class PageHinkley:
    """Page-Hinkley change detector (잔차 평균 이동 조기 감지)."""
    def __init__(self, delta: float = 0.005, threshold: float = 0.5):
        self.delta, self.threshold = delta, threshold
        self.n = 0; self.mean = 0.0; self.mT = 0.0; self.min_mT = 0.0

    def update(self, x: float) -> bool:
        self.n += 1
        self.mean += (x - self.mean) / self.n
        self.mT += x - self.mean - self.delta
        self.min_mT = min(self.min_mT, self.mT)
        return (self.mT - self.min_mT) > self.threshold


# --- RuleObserver (read-only) -----------------------------------------------

@dataclass
class ObserverReport:
    agreement_rate: float
    mean_staleness_days: float
    residual_psi: float
    near_zero_mass: float
    veto_rate: float
    force_include_rate: float
    archetype_activity: dict
    divergence_alert: bool
    drift_alert: bool
    muted_rules: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class RuleObserver:
    """관측 전용. alert/mute 신호만 산출(집행 X). 모듈 4분리 준수."""

    def __init__(self, agreement_floor: float = 0.85, rule_mdd_stop: float = -0.05,
                 psi_alert: float = 0.25):
        self.agreement_floor = agreement_floor
        self.rule_mdd_stop = rule_mdd_stop
        self.psi_alert = psi_alert
        self._ph = PageHinkley()

    def observe(
        self,
        shadow_verdicts: list[str],
        live_verdicts: list[str],
        staleness_days: list[float],
        resid_baseline: np.ndarray,
        resid_live: np.ndarray,
        archetypes: list[str],
        rule_cum_returns: Optional[dict] = None,   # {rule_id: [cum_ret...]}
    ) -> ObserverReport:
        # ① agreement rate (shadow vs live)
        pairs = list(zip(shadow_verdicts, live_verdicts))
        agree = np.mean([s == l for s, l in pairs]) if pairs else float("nan")

        # ② staleness
        mean_stale = float(np.mean(staleness_days)) if staleness_days else float("nan")

        # ③ residual drift (PSI + 0근방 질량)
        p = psi(resid_baseline, resid_live)
        nz = near_zero_mass(resid_live)
        drift_change = False
        for r in np.asarray(resid_live, float):
            if np.isfinite(r):
                drift_change = self._ph.update(float(r)) or drift_change

        # ④ veto / force-include 빈도
        allv = live_verdicts or []
        veto_rate = np.mean([v == "veto" for v in allv]) if allv else 0.0
        force_rate = np.mean([v == "force_include" for v in allv]) if allv else 0.0

        # ⑤ archetype별 활성도
        act = defaultdict(int)
        for a in archetypes:
            act[a] += 1

        # divergence = 1차 방어선
        div_alert = (np.isfinite(agree) and agree < self.agreement_floor)
        drift_alert = (np.isfinite(p) and p > self.psi_alert) or drift_change

        # Rule-level Stop: 누적수익 MDD ≤ -5% → mute 신호
        muted = []
        if rule_cum_returns:
            for rid, cum in rule_cum_returns.items():
                c = np.asarray(cum, float)
                if len(c) < 2:
                    continue
                peak = np.maximum.accumulate(c)
                mdd = float(np.min(c - peak))
                if mdd <= self.rule_mdd_stop:
                    muted.append(rid)

        notes = []
        if div_alert:
            notes.append(f"★ divergence alert: agreement {agree:.2f} < {self.agreement_floor} (1차 방어선)")
        if drift_alert:
            notes.append(f"drift alert: PSI={p:.3f} near0={nz:.2f} PH={drift_change}")
        if muted:
            notes.append(f"Rule-Stop mute 신호(집행은 RolloutController): {muted}")

        return ObserverReport(
            agreement_rate=float(agree), mean_staleness_days=mean_stale,
            residual_psi=float(p), near_zero_mass=float(nz),
            veto_rate=float(veto_rate), force_include_rate=float(force_rate),
            archetype_activity=dict(act), divergence_alert=bool(div_alert),
            drift_alert=bool(drift_alert), muted_rules=muted, notes=notes,
        )


if __name__ == "__main__":
    rng = np.random.default_rng(1)

    # 1) 정상: shadow≈live, drift 없음
    sv = ["cheap"] * 90 + ["neutral"] * 10
    lv = ["cheap"] * 88 + ["neutral"] * 12
    base = rng.normal(0, 1, 500)
    live_ok = rng.normal(0, 1, 200)
    obs = RuleObserver()
    rep = obs.observe(sv, lv, [3.0] * 100, base, live_ok, ["cyclical"] * 100)
    print(f"1) 정상: agree={rep.agreement_rate:.2f} div={rep.divergence_alert} drift={rep.drift_alert}")
    assert not rep.divergence_alert

    # 2) divergence: shadow vs live 크게 갈림 → 1차 방어선 alert
    lv_bad = ["veto"] * 50 + ["cheap"] * 50
    rep = obs.observe(sv, lv_bad, [3.0] * 100, base, live_ok, ["cyclical"] * 100)
    print(f"2) divergence: agree={rep.agreement_rate:.2f} alert={rep.divergence_alert} ({rep.notes[0][:40]})")
    assert rep.divergence_alert

    # 3) drift: live 잔차 분포 이동 → PSI alert
    obs2 = RuleObserver()
    live_drift = rng.normal(2.0, 1, 200)
    rep = obs2.observe(sv, lv, [3.0] * 100, base, live_drift, ["cyclical"] * 100)
    print(f"3) drift: PSI={rep.residual_psi:.3f} alert={rep.drift_alert}")
    assert rep.drift_alert

    # 4) Rule-level Stop: MDD -8% rule → mute 신호
    rep = obs2.observe(sv, lv, [3.0] * 100, base, live_ok, ["cyclical"] * 100,
                       rule_cum_returns={"r_good": [0, 0.01, 0.03, 0.05], "r_bad": [0, -0.03, -0.06, -0.08]})
    assert rep.muted_rules == ["r_bad"], rep.muted_rules
    print(f"4) Rule-Stop: muted={rep.muted_rules} (MDD≤-5%, 집행은 외부)")

    print("S6 rule_observer self-test PASS")
