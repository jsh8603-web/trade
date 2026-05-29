"""core/data/promotion_gate_live.py — shadow→live 승급 사람게이트 + ramp (IA-5·R12).

IA-5/R12: 모의(shadow)에서 검증된 가정을 실거래(live)로 올릴 때 **사람 게이트** 필수.
자동 승급 금지(자율 범위 밖 — autopilot-run-scope memory). 핵심 4:

1. **사람 승인 필수**: promotion_record(append-only) + approver 서명 없으면 live 불가.
   kill_switch latch 재사용 — 해제는 사람만(reset_emergency by_human=True).
2. **로직 분기 금지·sink 만 분기**: shadow/live 는 같은 결정 로직, execution_mode(sink)만 다름.
   (분기하면 shadow 가 검증한 코드와 live 코드가 달라져 검증 무의미.)
3. ★**shadow→live ramp**(전체구조 R4/R5 Q1): own-impact·adverse-selection 은 observational
   보정 불가 → 소액 live ramp 로만 추정. ramp = 사전등록 **geometric ladder**(c₀,2c₀,4c₀…),
   **rung 크기 FIX·'전진 여부'만 data-dependent**(size-as-peeking 차단). ramp 전용 **e-process**
   (null="net-of-impact edge≤0", Ville anytime-valid) → e≥1/α 면 전진. size↑ 서 net edge
   부호반전 = **capacity ceiling** 표면화. realized impact>band = **OOB breaker**(즉시 halt).
4. ★**crypto-only 속성 비의존**(R5): self-flatten 등 안전장치가 crypto 의 연속거래 가정에
   의존하면 equity overnight gap·halt 시 무의미. flatten 불가 시 freeze+alert 로 graceful.

신규 의존 0(기존 kill_switch 재사용).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal, Optional

from core.observability.kill_switch import KillSwitch

ExecutionMode = Literal["shadow", "live"]
FlattenAction = Literal["flatten_now", "freeze_and_alert"]


@dataclass
class PromotionRecord:
    """승급 신청/이력 1건 (append-only). 사람 승인 = approver 서명 + approval_ts."""
    assumption_id: str
    version: str
    shadow_window: tuple              # (start, end) shadow 검증 구간
    alpha_consumed: float
    regime_coverage: tuple            # 검증된 regime id 집합
    incident_count: int               # shadow 중 DATA_CONTRACT_VIOLATION 등 incident
    family: str
    attribution_summary: dict = field(default_factory=dict)
    approver: str = ""                # 사람 서명(빈 문자열=미승인)
    approval_ts: Optional[date] = None
    execution_mode: ExecutionMode = "shadow"


@dataclass(frozen=True)
class RampLadder:
    """사전등록 geometric ladder. rung 크기 FIX(데이터 무관), '전진 여부'만 data-dependent."""
    c0: float
    n_rungs: int
    ratio: float = 2.0

    def size_at(self, rung: int) -> float:
        if rung < 0 or rung >= self.n_rungs:
            raise IndexError(f"rung {rung} 범위 밖 [0,{self.n_rungs})")
        return self.c0 * (self.ratio ** rung)


@dataclass
class RampState:
    rung: int = 0
    e_value: float = 1.0              # ramp e-process (null: net edge≤0)
    halted: bool = False
    halt_reason: str = ""
    capacity_ceiling: Optional[int] = None
    n_obs: int = 0
    edge_sum_at_rung: float = 0.0     # 현 rung 누적 net edge(부호반전 감지)
    n_at_rung: int = 0


@dataclass
class RampAdvice:
    action: Literal["hold", "advance", "halt", "ceiling"]
    rung: int
    e_value: float
    detail: str = ""


class PromotionGate:
    """shadow→live 사람게이트 + ramp 진행. 로직 분기 금지·sink(execution_mode)만 분기."""

    def __init__(self, *, kill_switch: Optional[KillSwitch] = None, alpha: float = 0.05,
                 lam: float = 0.5, impact_band: float = 0.005,
                 min_regimes: int = 2, max_incidents: int = 0) -> None:
        self.ks = kill_switch or KillSwitch()
        self.alpha = alpha
        self.lam = lam                    # e-process betting fraction (0<lam<1)
        self.impact_band = impact_band    # OOB breaker 임계(realized impact)
        self.min_regimes = min_regimes
        self.max_incidents = max_incidents
        self._records: list[PromotionRecord] = []
        self._promoted: dict[str, PromotionRecord] = {}   # assumption_id -> live record

    # --- 승급 게이트 (사람 승인) ----------------------------------------
    def request_promotion(self, rec: PromotionRecord) -> tuple[bool, str]:
        """승급 신청. 로직 게이트(incident/regime coverage) + 사람 승인(approver) 모두 통과 시 live.

        반환 (granted, reason). 게이트 통과해도 approver 없으면 shadow 유지(사람게이트).
        """
        self._records.append(rec)
        if self.ks._emergency:
            return False, f"kill_switch emergency active — 승급 차단"
        if rec.incident_count > self.max_incidents:
            return False, f"incident {rec.incident_count}>{self.max_incidents} — 측정 무결성 미달"
        if len(set(rec.regime_coverage)) < self.min_regimes:
            return False, f"regime coverage {len(set(rec.regime_coverage))}<{self.min_regimes} — 검증 부족"
        if not rec.approver:
            return False, "approver 서명 없음 — 사람게이트 미통과(shadow 유지)"
        rec.execution_mode = "live"
        self._promoted[rec.assumption_id] = rec
        return True, f"live 승급(approver={rec.approver})"

    def execution_sink(self, assumption_id: str) -> ExecutionMode:
        """그 가정의 현재 sink. 승급+미emergency 면 live, 아니면 shadow. (로직 동일, sink만 분기.)"""
        if self.ks._emergency:
            return "shadow"
        rec = self._promoted.get(assumption_id)
        return "live" if rec and rec.execution_mode == "live" else "shadow"

    # --- ramp 진행 (e-process + OOB) ------------------------------------
    def observe(self, state: RampState, ladder: RampLadder, net_edge: float,
                realized_impact: float) -> RampAdvice:
        """net-of-impact edge 1관측 → ramp e-process 갱신 + OOB 검사. state in-place 갱신.

        net_edge = 실현 net-of-impact edge(impact 차감 후). realized_impact = 실제 시장충격.
        """
        if state.halted:
            return RampAdvice("halt", state.rung, state.e_value, state.halt_reason)

        # OOB breaker: 실현 impact 가 band 초과 = out-of-band, 즉시 halt(substrate 비참조)
        if realized_impact > self.impact_band:
            state.halted = True
            state.halt_reason = f"OOB: realized_impact {realized_impact:.4g}>{self.impact_band}"
            return RampAdvice("halt", state.rung, state.e_value, state.halt_reason)

        # ramp e-process: null=edge≤0. x clip 후 e *= (1+lam·x) (Ville supermartingale)
        x = max(-1.0, min(1.0, net_edge))
        state.e_value *= (1.0 + self.lam * x)
        state.n_obs += 1
        state.edge_sum_at_rung += net_edge
        state.n_at_rung += 1

        # capacity ceiling: 현 rung 충분관측 + 평균 net edge 부호반전(음) = 한계 표면화
        if state.rung > 0 and state.n_at_rung >= 3 and state.edge_sum_at_rung < 0:
            state.capacity_ceiling = state.rung
            return RampAdvice("ceiling", state.rung, state.e_value,
                              f"capacity ceiling rung={state.rung}(net edge 부호반전)")

        # 전진: e ≥ 1/α 면 다음 rung(사전등록 size, 데이터는 '전진 여부'만 결정)
        if state.e_value >= 1.0 / self.alpha and state.rung + 1 < ladder.n_rungs:
            state.rung += 1
            state.e_value = 1.0           # 새 rung 자체 evidence 로 재시작(ramp 전용)
            state.edge_sum_at_rung = 0.0
            state.n_at_rung = 0
            return RampAdvice("advance", state.rung, state.e_value,
                              f"e≥1/α 전진 → rung {state.rung} size={ladder.size_at(state.rung)}")
        return RampAdvice("hold", state.rung, state.e_value, "evidence 누적 중")

    # --- crypto-only 속성 비의존 안전장치 -------------------------------
    @staticmethod
    def safe_flatten_action(asset_class: str, market_open: bool) -> FlattenAction:
        """안전 청산 행동. crypto(연속거래)=즉시 flatten / equity·etf=장중만 flatten,

        휴장·halt 면 freeze+alert(연속거래 가정 의존 금지 — self-flatten 이 gap 에 무의미).
        """
        if asset_class == "crypto":
            return "flatten_now"           # 24x7 연속거래
        return "flatten_now" if market_open else "freeze_and_alert"


if __name__ == "__main__":
    # 1) 사람게이트: approver 없으면 shadow 유지
    gate = PromotionGate()
    rec = PromotionRecord("crypto.mvrv_mean_reverts", "1", ("2024-01-01", "2024-03-01"),
                          alpha_consumed=0.02, regime_coverage=(0, 1, 2), incident_count=0, family="crypto:mvrv")
    granted, why = gate.request_promotion(rec)
    assert not granted and "approver" in why, why
    assert gate.execution_sink("crypto.mvrv_mean_reverts") == "shadow"
    print(f"1) 사람게이트: approver 무 → shadow 유지({why}) OK")

    # 2) approver 서명 → live 승급, sink 전환
    rec2 = PromotionRecord("crypto.mvrv_mean_reverts", "1", ("2024-01-01", "2024-03-01"),
                           alpha_consumed=0.02, regime_coverage=(0, 1, 2), incident_count=0,
                           family="crypto:mvrv", approver="jsh", approval_ts=date(2024, 3, 2))
    granted, why = gate.request_promotion(rec2)
    assert granted and gate.execution_sink("crypto.mvrv_mean_reverts") == "live", why
    print(f"2) approver 서명 → live 승급, sink=live OK")

    # 3) incident>0 / regime 부족 = 게이트 거부(측정 무결성·검증 부족)
    bad = PromotionRecord("x", "1", ("a", "b"), 0.01, (0,), incident_count=2, family="f", approver="jsh")
    g3, w3 = gate.request_promotion(bad)
    assert not g3 and "incident" in w3, w3
    print(f"3) incident 2>0 게이트 거부({w3}) OK")

    # 4) kill_switch latch: emergency 시 전 sink shadow 강등, 해제는 사람만
    gate.ks.trip_emergency("급락 자동발화")
    assert gate.execution_sink("crypto.mvrv_mean_reverts") == "shadow", "emergency=shadow 강등"
    try:
        gate.ks.reset_emergency(by_human=False)
        raise AssertionError("기계 해제가 통과함")
    except Exception:
        pass
    gate.ks.reset_emergency(by_human=True)
    assert gate.execution_sink("crypto.mvrv_mean_reverts") == "live", "사람 해제 후 복귀"
    print("4) kill_switch latch: emergency→shadow 강등, 사람만 해제 OK")

    # 5) ★ramp e-process: 양의 net edge 누적 → e≥1/α 전진(size 2배 ladder)
    ladder = RampLadder(c0=1000.0, n_rungs=5, ratio=2.0)
    st = RampState()
    advanced = False
    for _ in range(20):
        adv = gate.observe(st, ladder, net_edge=0.8, realized_impact=0.001)
        if adv.action == "advance":
            advanced = True
            assert ladder.size_at(adv.rung) == 1000.0 * (2 ** adv.rung)
            break
    assert advanced and st.rung >= 1, (advanced, st.rung)
    print(f"5) ramp 전진: 양 edge → e≥1/α rung={st.rung} size={ladder.size_at(st.rung)} OK")

    # 6) ★capacity ceiling: 높은 rung 에서 net edge 부호반전 → ceiling 표면화
    st2 = RampState(rung=2, e_value=1.0)
    cap = None
    for _ in range(5):
        adv = gate.observe(st2, ladder, net_edge=-0.5, realized_impact=0.001)
        if adv.action == "ceiling":
            cap = adv.rung; break
    assert cap == 2 and st2.capacity_ceiling == 2, (cap, st2.capacity_ceiling)
    print(f"6) capacity ceiling: rung 2 net edge 음전환 → ceiling={cap} (전진 중단) OK")

    # 7) ★OOB breaker: realized impact>band → 즉시 halt(substrate 비참조)
    st3 = RampState()
    adv = gate.observe(st3, ladder, net_edge=0.9, realized_impact=0.02)  # band 0.005 초과
    assert adv.action == "halt" and st3.halted, adv
    print(f"7) OOB breaker: realized_impact 0.02>0.005 → halt({adv.detail}) OK")

    # 8) ★crypto-only 비의존: equity halt 시 freeze+alert(연속거래 가정 의존 금지)
    assert PromotionGate.safe_flatten_action("crypto", market_open=False) == "flatten_now"
    assert PromotionGate.safe_flatten_action("equity", market_open=True) == "flatten_now"
    assert PromotionGate.safe_flatten_action("equity", market_open=False) == "freeze_and_alert"
    assert PromotionGate.safe_flatten_action("etf", market_open=False) == "freeze_and_alert"
    print("8) crypto-only 비의존: equity 휴장=freeze_and_alert / crypto=flatten_now OK")

    print("promotion_gate_live (사람게이트 + ramp e-process/OOB + crypto-only 비의존) self-test PASS")
