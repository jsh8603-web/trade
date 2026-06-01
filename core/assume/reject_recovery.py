"""core/assume/reject_recovery.py — reject 가설 재진입 로직 본체 (IC9, decisions §14 R11 수렴).

reject ≠ missing. "일시적 regime-conditional 연관 파탄"(증시서 흔함)으로 기각된 가설이 연관 회복 시
**자동 재진입**(production 무인 — 운영자 건건 승인 X, §14.1 human surface 신설 금지). 운영자 역할 =
정책 상수(false-revival budget·λ·threshold) 1회 확정뿐, 그 다음 무인 집행. 재진입 적절성 검증 =
실제 구현 기반 지표 시계열 주입 트레이딩 시뮬에서 재진입 발생 관찰(테스트, Phase V 성격).

§14 핵심 (gemini+claude 병렬 수렴):
- 14.1 상태기계: REJECT →(trigger)→ SHADOW(관찰, auto, risk 불변) →(5-AND adopt gate)→ live.
  재진입=새 human surface 신설 X. shadow→live = 기존 hysteresis_and_gate routing(자동, 무인).
- 14.2 matched convex-leak: E_against(immortality 방어=죽지 않는 가설)와 대칭 E_for(재진입 증거=
  phoenix 방어). 모든 reject state에 E_for 경로(reachable exit, black-hole 차단). leak Ẽ_t=γ·Ẽ_{t-1}·m_t+(1−γ).
- 14.3 burden = reject_class 분기:
  · regime_conditional/missing(국면 미발생/n부족 power 부재) → burden = 원 adopt gate 그대로(disconfirm 無).
  · structural/evidence(adequate power로 전국면 무관/역부호) → adopt gate + overcoming term
    (= reject 시 누적 E_against, 신규 positive 가 prior disconfirmation 흡수+초과).
- 14.4 alpha-pricing: 재진입 e-process = 최초 discovery와 동일 alpha-wealth 인출(online_fdr).
  structural reject 재제안=비싸고 regime-draw 재진입=쌈. 재탐구차단=block 아닌 회계.
- 14.5 trigger multiplex: regime_draw / data_event(class C=PIT-corrupt 는 E_for 누적 격리) / n_regime_gated.
- 14.6 ledger = event_ledger 확장(신규 ledger 금지). reject event type + materialized projection.
- 14.9 선결: live-격리 관찰 상태(shadow tier) — 재진입 관찰이 live signal 로 안 새는 격리.

본 S1 = 골격(enum + RejectRecord §14.6 필드 + content-addressed id + burden 헬퍼). 본체(gate/trigger/
E_for/projection)는 S2~ 단계. opt-in off byte-identical: 본 모듈은 import 자체가 opt-in on 경로에서만.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Sequence


# ---------------------------------------------------------------------------
# reject_class / revival_trigger (§14.3 / §14.5)
# ---------------------------------------------------------------------------

class RejectClass(str, Enum):
    """기각 분류 — 재진입 burden 을 가른다(§14.3). reject≠missing 오라벨 지점 구분."""
    REGIME_CONDITIONAL = "regime_conditional"  # 국면 미발생/n부족 power 부재 → burden=원 adopt gate 그대로
    STRUCTURAL = "structural"                   # adequate power 로 전국면 무관/역부호 → burden=gate+overcoming
    DATA_CORRUPT = "data_corrupt"               # class C(PIT-corrupt) → E_for 누적 격리(데이터 수정 전)


class RevivalTrigger(str, Enum):
    """재진입 트리거 타입(§14.5). reject_class 별 리스너 분리 바인딩."""
    REGIME_DRAW = "regime_draw"        # 국면 episode 누적(conditional 재평가)
    DATA_EVENT = "data_event"          # 데이터 수정/신규(class C 는 수정 전까지 누적 격리)
    N_REGIME_GATED = "n_regime_gated"  # 단일 draw 론 structural/conditional 구분 불가 → threshold 미달 UNKNOWN 잔류


# ---------------------------------------------------------------------------
# content-addressed hypothesis id (§14.6 — cosmetic 리네임도 충돌)
# ---------------------------------------------------------------------------

def content_address(
    *,
    statement: str,
    falsification_metric: str,
    domain: str,
    scope: str,
    kind: str,
    series_ids: Sequence[str] = (),
) -> str:
    """가설 본질 내용 → content-addressed id. 표면 id(카드 id)가 아니라 **내용**(statement+반증조건+
    series+분류)을 hash → cosmetic 리네임(표면 id만 변경)도 동일 내용=동일 주소 → reject pool 재제안
    충돌 감지(§14.6). 정의 변경(statement/metric 변경)=새 주소(별 가설로 취급, alpha 새로 인출)."""
    parts = [
        str(domain), str(scope), str(kind),
        str(statement).strip(),
        str(falsification_metric).strip(),
        "|".join(sorted(str(s) for s in series_ids)),
    ]
    canon = "␟".join(parts).encode("utf-8")     # U+241F = 단위 구분자(필드 경계 충돌 방지)
    return "rj_" + hashlib.sha256(canon).hexdigest()[:16]


# ---------------------------------------------------------------------------
# RejectRecord — reject 사건 1건 (§14.6 필드)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RejectRecord:
    """reject 사건 1건(§14.6 필드 전수). event_ledger reject event payload + materialized projection 단위.

    frozen = append-only(재진입은 새 event 로 기록, 본 record mutate 금지 — bitemporal 일관성).
    E_against_at_reject = structural 재진입의 overcoming term(신규 positive 가 이걸 흡수+초과해야).
    power_at_decision = "봤는데 없음(high power)" vs "못 봤음(low power)" 구분 → reject_class 판정 근거.
    """
    hypothesis_id: str                           # content_address() — 본질 내용 주소
    reject_class: RejectClass
    reason_code: str                             # 기각 사유 코드(audit verdict / falsifier breach 등)
    n_at_decision: int                           # reject 시점 표본 n
    regime_composition: dict = field(default_factory=dict)   # regime_id → count(국면 구성, n 분해)
    power_at_decision: Optional[float] = None    # 검정력(low=못 봤음=regime_conditional 쪽)
    e_against_at_reject: float = 1.0             # reject 시 누적 E_against(structural overcoming 기준)
    revival_trigger: Optional[RevivalTrigger] = None
    e_for_state: float = 1.0                     # 현재 E_for 누적(재진입 증거, convex-leak 적용)
    leak_lambda: float = 1.0                     # convex-leak γ. half-life = −ln2/lnγ (γ<1)
    alpha_charge: float = 0.0                    # alpha-wealth 인출액(재탐구 회계, §14.4)
    tt: str = ""                                 # transaction time(append)
    dt: str = ""                                 # decision time(엔진 인지)
    vt: str = ""                                 # valid time(데이터 날짜)
    card_id: str = ""                            # WeightAssumptionCard 포인터(표면 id)
    card_version: str = ""
    human_gate_required: bool = False            # shadow→live = 무인 자동(§14.1)이라 기본 False

    def to_payload(self) -> dict:
        """event_ledger reject event payload(직렬화). enum → value(jsonl 호환)."""
        return {
            "hypothesis_id": self.hypothesis_id,
            "reject_class": self.reject_class.value,
            "reason_code": self.reason_code,
            "n_at_decision": int(self.n_at_decision),
            "regime_composition": dict(self.regime_composition),
            "power_at_decision": self.power_at_decision,
            "e_against_at_reject": float(self.e_against_at_reject),
            "revival_trigger": self.revival_trigger.value if self.revival_trigger else None,
            "e_for_state": float(self.e_for_state),
            "leak_lambda": float(self.leak_lambda),
            "alpha_charge": float(self.alpha_charge),
            "card_id": self.card_id,
            "card_version": self.card_version,
            "human_gate_required": bool(self.human_gate_required),
        }


# ---------------------------------------------------------------------------
# burden 헬퍼 (§14.3 / §14.5)
# ---------------------------------------------------------------------------

def requires_overcoming(reject_class) -> bool:
    """재진입 burden 에 overcoming term(누적 E_against 흡수+초과) 필요? structural=True / 나머지=False.

    §14.3: regime_conditional/missing = disconfirm 없으니(못 봤을 뿐) 원 adopt gate 그대로
    (first-time adoption 과 대칭). structural = adequate power 로 disconfirm 됐으니 그 누적 E_against 를
    신규 positive 가 흡수+초과해야 재진입(높은 burden, alpha 도 비쌈).
    """
    return RejectClass(reject_class) == RejectClass.STRUCTURAL


def e_for_accrual_isolated(reject_class) -> bool:
    """E_for 누적을 격리? class C(data_corrupt)=데이터 수정 전까지 누적 격리(§14.5).

    PIT-corrupt 데이터 위에서 E_for 를 누적하면 = corrupt 위 lookahead = 최악의 false revival.
    데이터 정정(DATA_EVENT) 전까지 E_for 동결. 나머지 class = 정상 누적.
    """
    return RejectClass(reject_class) == RejectClass.DATA_CORRUPT


def classify_reject(power_at_decision: Optional[float], *, power_floor: float = 0.5,
                    data_corrupt: bool = False) -> RejectClass:
    """reject_class 판정(§14.3). data_corrupt 우선 → DATA_CORRUPT. 검정력 floor 미달(못 봤음)=
    REGIME_CONDITIONAL / 충분(봤는데 없음)=STRUCTURAL. power=None(미측정)=보수적 REGIME_CONDITIONAL
    (재진입 가능 = black-hole 차단, structural 의 높은 burden 을 함부로 안 씌움)."""
    if data_corrupt:
        return RejectClass.DATA_CORRUPT
    if power_at_decision is None:
        return RejectClass.REGIME_CONDITIONAL
    return RejectClass.STRUCTURAL if float(power_at_decision) >= power_floor else RejectClass.REGIME_CONDITIONAL


# ---------------------------------------------------------------------------
# RejectRecoveryGate (§14.1 상태기계 + §14.3 burden 분기) — S4
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RecoveryDecision:
    """재진입 판정 결과. revive=True ⟺ shadow→live 무인 자동 승급(§14.1 human surface 신설 X)."""
    revive: bool
    reason: str                  # 감사용 사유서
    burden_met: bool             # reject_class burden 충족(structural=overcoming)
    e_for: float
    overcoming_required: float   # structural 흡수 기준(E_against_at_reject), 그 외 0.0
    gate_promote: bool           # 5-AND adopt gate 통과 여부
    alpha_ok: bool = True        # ★§14.4 alpha-wealth 검정 통과(account 미지정 시 True=skip)
    alpha_charge: float = 0.0    # 이번 재진입 시도가 인출한 alpha(재탐구 회계)


def evaluate_recovery(
    record: "RejectRecord",
    *,
    e_for: float,
    fdr_significant: bool,
    effect_size: float = 0.0,
    dwell_ok: bool = False,
    k_window_persist: int = 0,
    same_regime: bool = True,
    adopt_gate=None,
    alpha_account=None,
    p_value: Optional[float] = None,
) -> RecoveryDecision:
    """reject 가설 재진입 판정(§14.1 + §14.3 + §14.4). 무인 자동 — 운영자 건건 승인 X.

    1) class C(data_corrupt) 격리: 데이터 정정(DATA_EVENT) 전 revive 차단 — corrupt 위 E_for 누적=
       lookahead=최악 false revival(§14.5).
    2) 5-AND adopt gate = 기존 `hysteresis_and_gate` 재사용(새 human surface 신설 X, §14.1).
    3) burden = reject_class(§14.3):
       · regime_conditional/missing: gate promote 면 revive(원 gate 그대로, disconfirm 無).
       · structural: gate promote AND E_for ≥ E_against_at_reject(overcoming — 신규 positive 가
         reject 시 누적 반증을 흡수+초과해야).
    4) ★alpha-pricing(§14.4): alpha_account(online_fdr LordPlusPlus/AlphaInvesting) 주면 wealth 검정.
       p = p_value 또는 E_for→p 근사(1/E_for). 동일 reject pool 재제안 반복 = wealth 고갈 → 자동 차단
       (재탐구=block 아닌 회계). structural 재제안=비쌈/regime-draw=쌈 = account omega 차등(호출자 구성).
    """
    if adopt_gate is None:
        from core.structure.assumption_stats import hysteresis_and_gate
        adopt_gate = hysteresis_and_gate
    rc = RejectClass(record.reject_class)
    # 1) class C 격리(데이터 수정 전 차단)
    if e_for_accrual_isolated(rc) and record.revival_trigger != RevivalTrigger.DATA_EVENT:
        return RecoveryDecision(
            revive=False, reason="class C(data_corrupt) E_for 격리 — 데이터 정정(DATA_EVENT) 전 재진입 차단",
            burden_met=False, e_for=float(e_for), overcoming_required=0.0, gate_promote=False)
    # 2) 5-AND adopt gate(기존 재사용)
    gate = adopt_gate(fdr_significant=fdr_significant, effect_size=effect_size,
                      dwell_ok=dwell_ok, k_window_persist=k_window_persist, same_regime=same_regime)
    # 3) burden 분기
    overcoming_req = float(record.e_against_at_reject) if requires_overcoming(rc) else 0.0
    burden_met = (float(e_for) >= overcoming_req) if requires_overcoming(rc) else True
    # 4) ★alpha-pricing(§14.4): account 주면 wealth 검정(재탐구 회계 차단). 미지정=skip(하위호환).
    alpha_ok, alpha_charge = True, 0.0
    if alpha_account is not None:
        pv = float(p_value) if p_value is not None else 1.0 / max(float(e_for), 1e-12)
        dec = alpha_account.test(pv)
        alpha_ok = bool(dec.reject)              # wealth 충분 + 유의 → 인출 허용 / 고갈 → 차단
        alpha_charge = float(getattr(dec, "alpha_t", 0.0))
    revive = bool(gate.promote and burden_met and alpha_ok)
    if revive:
        reason = f"revive(무인 자동): 5-AND gate + burden({rc.value}) + alpha 충족"
    elif not gate.promote:
        reason = f"보류: 5-AND gate 미통과({gate.reason})"
    elif not burden_met:
        reason = f"보류: structural overcoming 미충족(E_for {float(e_for):.2f} < E_against {overcoming_req:.2f})"
    else:
        reason = "보류: alpha-wealth 고갈(재탐구 회계 차단, §14.4)"
    return RecoveryDecision(revive=revive, reason=reason, burden_met=burden_met, e_for=float(e_for),
                            overcoming_required=overcoming_req, gate_promote=bool(gate.promote),
                            alpha_ok=alpha_ok, alpha_charge=alpha_charge)


# ---------------------------------------------------------------------------
# trigger multiplex (§14.5) + chatter backoff (§14.8) — S6
# ---------------------------------------------------------------------------

def should_trigger_revival(
    reject_class,
    *,
    regime_episodes: int = 0,
    distinct_regimes: int = 0,
    data_corrected: bool = False,
    n_regime_threshold: int = 3,
    episode_threshold: int = 1,
) -> tuple:
    """trigger multiplex(§14.5): reject_class 별 리스너 분리 → (fired, trigger).

    - class C(data_corrupt): 데이터 정정(data_corrected)만 격리 해제 발화(DATA_EVENT). 그 외 미발화.
    - data_event: 데이터 신규/정정 → 발화(DATA_EVENT).
    - n_regime_gated: distinct_regimes < threshold → **UNKNOWN 잔류**(미발화) — 단일 draw 론
      structural/conditional 구분 불가(reit WALT n=1 케이스). 충분 정보 모일 때까지 대기.
    - regime_draw: regime episode 누적 ≥ episode_threshold → 발화(conditional 재평가).
    """
    rc = RejectClass(reject_class)
    if rc == RejectClass.DATA_CORRUPT:
        return (True, RevivalTrigger.DATA_EVENT) if data_corrected else (False, None)
    if data_corrected:
        return (True, RevivalTrigger.DATA_EVENT)
    if distinct_regimes < n_regime_threshold:
        return (False, RevivalTrigger.N_REGIME_GATED)        # UNKNOWN 잔류(구분 불가)
    if regime_episodes >= episode_threshold:
        return (True, RevivalTrigger.REGIME_DRAW)
    return (False, None)


class ChatterBackoff:
    """hypothesis 별 chatter/oscillation(revive→kill→revive) 차단 = exponential backoff(§14.8a).

    revive 후 kill 되면 사이클++ → cooldown 2배 증가 → 재진입 시도 간격 지수 증가(noise 추격 차단).
    안정 복귀(kill 없이 유지)면 reset. 기존 state machine 재사용 원칙(별 영속 X, 호출자 tick 관리)."""
    def __init__(self, base_cooldown: int = 4, max_cooldown: int = 256):
        self.base = int(base_cooldown)
        self.max = int(max_cooldown)
        self._cycles: dict = {}            # hid → revive→kill 사이클 수
        self._cooldown_until: dict = {}    # hid → 재시도 허용 tick

    def record_kill(self, hid: str, now_tick: int) -> int:
        """revive 후 kill 1회 = 사이클++ → cooldown 지수 증가. 반환 = 다음 재시도 허용 tick."""
        c = self._cycles.get(hid, 0) + 1
        self._cycles[hid] = c
        cooldown = min(self.base * (2 ** (c - 1)), self.max)
        self._cooldown_until[hid] = int(now_tick) + cooldown
        return self._cooldown_until[hid]

    def can_retry(self, hid: str, now_tick: int) -> bool:
        """현재 tick 에 재진입 시도 허용? (cooldown 경과 여부)."""
        return int(now_tick) >= self._cooldown_until.get(hid, 0)

    def reset(self, hid: str) -> None:
        """안정 복귀(kill 없이 유지) 시 사이클·cooldown 리셋."""
        self._cycles.pop(hid, None)
        self._cooldown_until.pop(hid, None)


def revival_cohort_falsified(cohort_ic_series, *, baseline_ic: float, sd: float,
                             alpha: float = 0.05) -> bool:
    """복귀 cohort falsification(§14.8b): 재진입한 가설들의 OOS Rank-IC 가 baseline(never-rejected /
    random re-entry) 아래로 붕괴 → 복귀=noise → kill. 기존 E_against(score_ic_breakdown) 재사용 —
    복귀 cohort group 에 동일 e-CUSUM kill 적용(random re-entry 와 구분 불가면 kill)."""
    from core.assume.weight_falsification import score_ic_breakdown_eprocess
    reject, _, _ = score_ic_breakdown_eprocess(cohort_ic_series, baseline_ic=baseline_ic, sd=sd, alpha=alpha)
    return bool(reject)


# ===========================================================================
# self-test (S1 enum/record/burden + S4 gate + S5 alpha + S6 trigger/chatter)
# ===========================================================================
if __name__ == "__main__":
    # 1) content_address 결정성 + cosmetic 리네임 충돌 + 정의변경 분리
    base = dict(statement="HY OAS 확대 → 방어주 초과수익", falsification_metric="credit regime IC<0 e-process",
                domain="equity", scope="sector", kind="parametric", series_ids=("BAMLH0A0HYM2", "XLP"))
    a1 = content_address(**base)
    a2 = content_address(**base)                                  # 동일 내용 → 동일 주소
    assert a1 == a2, (a1, a2)
    # series 순서 무관(정렬)
    base_reorder = {**base, "series_ids": ("XLP", "BAMLH0A0HYM2")}
    assert content_address(**base_reorder) == a1, "series 순서로 주소 갈림(정렬 실패)"
    # 정의 변경(statement) → 새 주소
    base_def = {**base, "statement": "HY OAS 확대 → 방어주 *하락*"}
    assert content_address(**base_def) != a1, "정의 변경이 동일 주소(별 가설 미구분)"
    print(f"1) content_address OK: 동일내용=동일주소({a1}), series순서무관, 정의변경=새주소")

    # 2) RejectClass / RevivalTrigger enum
    assert RejectClass("structural") == RejectClass.STRUCTURAL
    assert RevivalTrigger("regime_draw") == RevivalTrigger.REGIME_DRAW
    assert len(RejectClass) == 3 and len(RevivalTrigger) == 3
    print(f"2) enum OK: RejectClass={[c.value for c in RejectClass]} / RevivalTrigger={[t.value for t in RevivalTrigger]}")

    # 3) RejectRecord 생성 + frozen + payload 직렬화
    rec = RejectRecord(
        hypothesis_id=a1, reject_class=RejectClass.REGIME_CONDITIONAL,
        reason_code="credit_stress_n4_directional", n_at_decision=4,
        regime_composition={"credit_stress": 4}, power_at_decision=0.3,
        e_against_at_reject=2.1, revival_trigger=RevivalTrigger.REGIME_DRAW,
        leak_lambda=0.98, alpha_charge=0.005, card_id="weight.eq_defensive.credit", card_version="v1")
    try:
        rec.n_at_decision = 9    # type: ignore
        raise AssertionError("frozen RejectRecord 수정됨")
    except (AttributeError, TypeError, ValueError):
        pass
    p = rec.to_payload()
    assert p["reject_class"] == "regime_conditional" and p["revival_trigger"] == "regime_draw"
    assert p["human_gate_required"] is False, "재진입 live flip = 무인 자동(§14.1)이라 기본 False"
    print(f"3) RejectRecord OK: frozen + payload enum→value(reject_class={p['reject_class']}, human_gate={p['human_gate_required']})")

    # 4) burden 분기(§14.3): structural=overcoming 필요 / regime_conditional=원 gate
    assert requires_overcoming(RejectClass.STRUCTURAL) is True
    assert requires_overcoming(RejectClass.REGIME_CONDITIONAL) is False
    assert requires_overcoming("structural") is True              # str 입력도
    print(f"4) burden OK: structural=overcoming필요 / regime_conditional=원gate(disconfirm無)")

    # 5) E_for 격리(§14.5): class C(data_corrupt) 만 격리(corrupt 위 누적=lookahead 방지)
    assert e_for_accrual_isolated(RejectClass.DATA_CORRUPT) is True
    assert e_for_accrual_isolated(RejectClass.REGIME_CONDITIONAL) is False
    assert e_for_accrual_isolated(RejectClass.STRUCTURAL) is False
    print(f"5) E_for 격리 OK: data_corrupt만 격리(데이터 수정 전 누적 동결)")

    # 6) classify_reject: power floor 분기 + None 보수 + data_corrupt 우선
    assert classify_reject(0.8) == RejectClass.STRUCTURAL                  # 봤는데 없음
    assert classify_reject(0.3) == RejectClass.REGIME_CONDITIONAL          # 못 봤음(저power)
    assert classify_reject(None) == RejectClass.REGIME_CONDITIONAL         # 미측정=보수(재진입 가능)
    assert classify_reject(0.9, data_corrupt=True) == RejectClass.DATA_CORRUPT  # corrupt 우선
    print(f"6) classify_reject OK: high-power=structural / low·None=regime_conditional / corrupt=data_corrupt")

    # 7) ★S4 regime_conditional 재진입: 5-AND gate 통과 → revive(원 gate 그대로, overcoming 無)
    rec_rc = RejectRecord(hypothesis_id="rj_x", reject_class=RejectClass.REGIME_CONDITIONAL,
                          reason_code="rc", n_at_decision=4, e_against_at_reject=2.1)
    d_rc = evaluate_recovery(rec_rc, e_for=1.0, fdr_significant=True, effect_size=0.6,
                             dwell_ok=True, k_window_persist=2, same_regime=True)
    assert d_rc.revive is True and d_rc.overcoming_required == 0.0, d_rc
    print(f"7) regime_conditional revive OK: revive={d_rc.revive}(overcoming 無, E_for {d_rc.e_for} 무관)")

    # 8) ★S4 structural overcoming 미충족: gate 통과해도 E_for < E_against_at_reject → 보류
    rec_st = RejectRecord(hypothesis_id="rj_y", reject_class=RejectClass.STRUCTURAL, reason_code="st",
                          n_at_decision=200, e_against_at_reject=10.0, power_at_decision=0.9)
    d_st_lo = evaluate_recovery(rec_st, e_for=5.0, fdr_significant=True, effect_size=0.6,
                                dwell_ok=True, k_window_persist=2, same_regime=True)
    assert d_st_lo.revive is False and d_st_lo.gate_promote is True and d_st_lo.burden_met is False
    print(f"8) structural overcoming 미충족 OK: gate통과({d_st_lo.gate_promote}) but E_for 5<E_against 10 → revive={d_st_lo.revive}")

    # 9) ★S4 structural overcoming 충족: E_for ≥ E_against → revive
    d_st_hi = evaluate_recovery(rec_st, e_for=12.0, fdr_significant=True, effect_size=0.6,
                                dwell_ok=True, k_window_persist=2, same_regime=True)
    assert d_st_hi.revive is True and d_st_hi.burden_met is True
    print(f"9) structural overcoming 충족 OK: E_for 12≥E_against 10 → revive={d_st_hi.revive}")

    # 10) ★S4 class C(data_corrupt) 격리: trigger≠DATA_EVENT → 차단(E_for·gate 무관)
    rec_dc = RejectRecord(hypothesis_id="rj_z", reject_class=RejectClass.DATA_CORRUPT, reason_code="pit_corrupt",
                          n_at_decision=100, revival_trigger=RevivalTrigger.REGIME_DRAW)
    d_dc = evaluate_recovery(rec_dc, e_for=99.0, fdr_significant=True, effect_size=0.6,
                             dwell_ok=True, k_window_persist=2, same_regime=True)
    assert d_dc.revive is False, d_dc
    print(f"10) class C 격리 OK: regime_draw(≠DATA_EVENT) → revive={d_dc.revive}(데이터 정정 전 차단, E_for 99 무관)")

    # 11) ★S4 class C + DATA_EVENT(데이터 정정) → 격리 해제, gate 통과 시 revive
    rec_dc2 = RejectRecord(hypothesis_id="rj_z2", reject_class=RejectClass.DATA_CORRUPT, reason_code="pit_fixed",
                           n_at_decision=100, revival_trigger=RevivalTrigger.DATA_EVENT)
    d_dc2 = evaluate_recovery(rec_dc2, e_for=99.0, fdr_significant=True, effect_size=0.6,
                              dwell_ok=True, k_window_persist=2, same_regime=True)
    assert d_dc2.revive is True, d_dc2
    print(f"11) class C + DATA_EVENT OK: 데이터 정정 → 격리 해제 → revive={d_dc2.revive}")

    # 12) ★S4 5-AND gate 미통과(effect 약함) → 보류(burden 무관)
    d_gate_fail = evaluate_recovery(rec_rc, e_for=99.0, fdr_significant=True, effect_size=0.2,
                                    dwell_ok=True, k_window_persist=2, same_regime=True)
    assert d_gate_fail.revive is False and d_gate_fail.gate_promote is False
    print(f"12) 5-AND gate 미통과 OK: effect 0.2 약 → gate_promote={d_gate_fail.gate_promote} → revive={d_gate_fail.revive}")

    # 13) ★S5 alpha-pricing(§14.4): wealth 고갈 시 재진입 차단(죽은 가설 반복 재제안=회계 차단)
    from core.structure.online_fdr import AlphaInvesting
    acct = AlphaInvesting(alpha=0.05)
    revived_cnt = 0
    for _ in range(60):              # 약신호(p=0.5) 반복 재시도 → wealth 소진 → alpha 차단
        d = evaluate_recovery(rec_rc, e_for=2.0, fdr_significant=True, effect_size=0.6,
                              dwell_ok=True, k_window_persist=2, same_regime=True,
                              alpha_account=acct, p_value=0.5)
        if d.revive:
            revived_cnt += 1
    assert revived_cnt == 0, f"약신호 60회 재시도가 alpha 통과(회계 차단 실패): {revived_cnt}"
    acct2 = AlphaInvesting(alpha=0.05)
    d_strong = evaluate_recovery(rec_rc, e_for=1e6, fdr_significant=True, effect_size=0.6,
                                 dwell_ok=True, k_window_persist=2, same_regime=True,
                                 alpha_account=acct2, p_value=1e-6)
    assert d_strong.revive is True and d_strong.alpha_ok is True, d_strong
    print(f"13) ★alpha-pricing OK: 약신호(p=0.5)×60 revive={revived_cnt}(wealth 고갈 차단) / "
          f"강신호(p=1e-6) revive={d_strong.revive}(charge={d_strong.alpha_charge:.4f})")

    # 14) ★S6 trigger multiplex(§14.5): regime_draw 발화 / n_regime_gated 잔류 / data_event / class C
    f_rd, t_rd = should_trigger_revival(RejectClass.REGIME_CONDITIONAL, regime_episodes=2, distinct_regimes=4)
    assert f_rd is True and t_rd == RevivalTrigger.REGIME_DRAW
    f_ng, t_ng = should_trigger_revival(RejectClass.REGIME_CONDITIONAL, regime_episodes=5, distinct_regimes=1)
    assert f_ng is False and t_ng == RevivalTrigger.N_REGIME_GATED      # distinct<3 → UNKNOWN 잔류
    f_de, t_de = should_trigger_revival(RejectClass.STRUCTURAL, data_corrected=True, distinct_regimes=0)
    assert f_de is True and t_de == RevivalTrigger.DATA_EVENT
    f_c, t_c = should_trigger_revival(RejectClass.DATA_CORRUPT, regime_episodes=9, distinct_regimes=9)
    assert f_c is False and t_c is None                                 # class C: 정정 전 미발화
    f_c2, t_c2 = should_trigger_revival(RejectClass.DATA_CORRUPT, data_corrected=True)
    assert f_c2 is True and t_c2 == RevivalTrigger.DATA_EVENT
    print(f"14) ★trigger multiplex OK: regime_draw={t_rd.value}(발화) / n<3={t_ng.value}(UNKNOWN 잔류) / "
          f"data_event={t_de.value} / classC(정정전)={t_c}(미발화)→정정후={t_c2.value}")

    # 15) ★S6 chatter backoff(§14.8a): revive→kill 반복 → cooldown 지수 증가
    cb = ChatterBackoff(base_cooldown=4, max_cooldown=256)
    u1 = cb.record_kill("rj_chat", now_tick=0)      # 1사이클: cooldown 4
    assert u1 == 4 and cb.can_retry("rj_chat", 3) is False and cb.can_retry("rj_chat", 4) is True
    u2 = cb.record_kill("rj_chat", now_tick=10)     # 2사이클: cooldown 8
    u3 = cb.record_kill("rj_chat", now_tick=20)     # 3사이클: cooldown 16
    assert (u2 - 10) == 8 and (u3 - 20) == 16, (u2, u3)
    cb.reset("rj_chat")
    assert cb.can_retry("rj_chat", 0) is True       # 안정 복귀 → 리셋
    print(f"15) ★chatter backoff OK: cooldown 1→4 2→8 3→16(지수 증가) + reset 후 즉시 재시도 가능")

    # 16) ★S6 복귀 cohort falsification(§14.8b): cohort IC 붕괴 → 복귀=noise kill
    import numpy as _np
    _rng = _np.random.default_rng(11)
    cohort_break = list(0.05 + _rng.normal(0, 0.01, 10)) + list(-0.05 + _rng.normal(0, 0.01, 30))
    cohort_hold = list(0.05 + _rng.normal(0, 0.01, 40))
    assert revival_cohort_falsified(cohort_break, baseline_ic=0.04, sd=0.02) is True
    assert revival_cohort_falsified(cohort_hold, baseline_ic=0.04, sd=0.02) is False
    print(f"16) ★복귀 cohort falsification OK: cohort IC 붕괴→kill=True / 유지→kill=False(noise 구분)")

    print("\nreject_recovery S1+S4+S5+S6 self-test PASS "
          "(enum + content-addressed id + RejectRecord §14.6 + burden 분기 + classify_reject "
          "+ RejectRecoveryGate(gate/overcoming/classC/5-AND) + alpha-pricing 회계 차단 "
          "+ trigger multiplex(regime_draw/n_gated/data_event/classC) + chatter backoff + cohort falsification)")
