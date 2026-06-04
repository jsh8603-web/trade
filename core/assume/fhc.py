"""core/assume/fhc.py — FHC (Falsifiable Hypothesis Card) core lifecycle (S1).

설계 SSOT = .consult-judge-report-RESULTS.md (C1~C16, 5R gemini+claude 수렴) + .coord-fhc-contract-20260603.md.
자산무관 단일 primitive(macro/equity/commodity/crypto 공통). btn-button equity exposure card = 이 FHC 의
scope="sector" 인스턴스(별 schema 금지). 거시 카드 = scope="macro".

★2벌 회피 — 기존 인프라 정합/재사용 + 신규 최소:
  S1 재사용(직접): card_contract(falsification_metric 필수 게이트 정합, __post_init__) +
                anytime-valid e-process 원리(Ville, betting martingale).
  S1 hook(주입형): graduation.GraduationDecision 를 transition(graduation_decision=) 로 외부 5-AND
                confirm 게이트 주입(자가승격 차단 정합). 미주입 시 e게이트 단독.
  S3/S4 통합 예정(본 S1 미연동): reject_recovery.should_trigger_revival(부활 트리거 정교화) /
                online_fdr·ELOND(alpha-wealth firewall INV-12) / eprocess_backbone(regime-break 양측).
  ★단측 betting e-process 는 본 모듈 inline(_DirectionalE) — MixtureSPRTEProcess(S² 양측)는 confirm/
    reject 방향 분리 불가라 2-leg 부적합(양측은 regime-break 용으로 S4 별도).
  신규(본 모듈): (a) 2-leg mediator gating(전제 holds/fails/unknown, alpha-wealth 미소비)
               (b) vacate state(confirmed→mediator fails = 보너스 suspend, reject 와 별개)
               (c) realized_bonus(monotone(log e-value) clip at bonus_cap)
               (d) 5-state machine(minted→confirmed→vacated→rejected→revived) inline 조립.

★안전 불변식(INV, RESULTS C13) — 본 모듈이 enforce:
  INV-3 fail-closed: mediator UNKNOWN/오류 → 보너스 0(적립 안 함).
  INV-4 bounded: realized_bonus ∈ [0, bonus_cap], confirm 전 0, e-value monotone.
  INV-5 confirmed-card-only: confirmed/revived + mediator HOLDS 일 때만 보너스.
  INV-11 off byte-identical: 본 모듈 호출처 0 = 자동 격리(go-live 시 소비). import 만으로 회귀 0.
  lifecycle 불변식: minted→vacated 금지(minted-dormant), rejected absorbing(부활=새 card_id),
                    revival_count cap → retire.

⛔ 본 모듈은 사이징을 직접 안 함 — realized_bonus(자산별 기여)만 산출. w_final=clip(L1+Σbonus, 천장C)
   집계·천장 enforce 는 bonus_channel.py(S3). 결정론/risk_gate 무수정.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal, Optional


# ===========================================================================
# enums
# ===========================================================================
class FHCStateEnum(str, Enum):
    MINTED = "minted"
    CONFIRMED = "confirmed"
    VACATED = "vacated"
    REJECTED = "rejected"
    REVIVED = "revived"


class MediatorState(str, Enum):
    HOLDS = "holds"
    FAILS = "fails"
    UNKNOWN = "unknown"          # fail-closed 기본값(모르면 적립 안 함, INV-3)


class MediatorTest(str, Enum):
    DETERMINISTIC_THRESHOLD = "deterministic_threshold"   # PIT 값 op threshold (검정 아님=측정)
    CONF_SEQUENCE = "conf_sequence"                       # anytime-valid confidence sequence(반복평가)
    STATE_SPACE_POSTERIOR = "state_space_posterior"       # study room state-space filtered posterior 구독


Direction = Literal["long_tilt", "short_tilt", "de_risk"]
_OPS = {
    ">": lambda v, t: v > t, "<": lambda v, t: v < t,
    ">=": lambda v, t: v >= t, "<=": lambda v, t: v <= t,
}


# ===========================================================================
# specs (frozen 정적 — mint-time 고정)
# ===========================================================================
@dataclass(frozen=True)
class MediatorSpec:
    """전제 leg("if") — 예측 관찰량. deterministic=PIT 값 측정 / state_space=외부 posterior 구독."""
    observable_ref: str
    test: MediatorTest = MediatorTest.DETERMINISTIC_THRESHOLD
    op: str = ">"
    threshold: float = 0.0
    window: int = 1
    compute_delay: int = 0          # event→knowable lag(bar). sector 펀더멘털서 load-bearing(restatement PIT)


@dataclass(frozen=True)
class OutcomeSpec:
    """예측 leg("then") — 수익 tilt. macro=ts_rank_IC / sector=cs_rank_IC(RESULTS C7)."""
    metric: str = "ts_rank_IC"
    target_signal_ref: str = ""


@dataclass(frozen=True)
class FHCard:
    """Falsifiable Hypothesis Card — 정적 thesis + 2-leg spec(mint-time 고정).

    card_contract.AssumptionCardLike 정합(falsification_metric 필수 게이트). equity exposure card =
    scope="sector" + outcome.metric="cs_rank_IC" 인 이 카드 한 인스턴스.
    """
    card_id: str
    scope: str                       # macro/sector/single_asset/global/asset
    domain: str                      # macro/equity/commodity/crypto
    direction: Direction
    statement: str
    falsification_metric: str        # 반증조건(비면 진입 금지 — card_contract 정합)
    mediator: MediatorSpec
    outcome: OutcomeSpec
    bonus_cap: float = 0.0           # per-asset headroom = (천장C − L1 baseline). 구조값(confidence 무관)
    confirm_e_threshold: float = 20.0   # e-value(=1/α) confirm 게이트
    reject_e_threshold: float = 20.0    # adverse e-value reject 게이트
    revival_cap: int = 3             # zombie flapping 방지
    targets: tuple = ()
    valid_from: Optional[str] = None
    version: str = "v1"
    kind: str = "structural"

    def __post_init__(self):
        if not self.falsification_metric or not str(self.falsification_metric).strip():
            raise ValueError(
                f"FHC {self.card_id!r} falsification_metric 부재 = 반증불가 = 진입 금지 "
                "(card_contract.assert_falsifiable 정합)."
            )
        if self.bonus_cap < 0:
            raise ValueError(f"FHC {self.card_id!r} bonus_cap<0 금지 (INV-4 bounded augmentation).")
        if self.mediator.op not in _OPS:
            raise ValueError(f"mediator op 미지원: {self.mediator.op!r}")


# ===========================================================================
# 방향성 betting e-process (2-leg 전용 — 단측, anytime-valid)
# ===========================================================================
class _DirectionalE:
    """단측 betting test martingale. H0: E[x]≤0(예측력 없음) vs alt: sign 방향 평균>0.
        E_t = ∏(1 + λ·sign·clip(x_t)), E_0=1. E[1+λ·sign·x]=1(E[x]=0) → nonneg martingale,
        Ville: P(sup E≥1/α)≤α(optional-stopping robust).
    ★eprocess_backbone.MixtureSPRTEProcess 는 S² 양측(|mean|>0)=방향 분리 불가 → 2-leg(confirm +1 /
      adverse −1)엔 단측 betting. λ=shrinkage 고정(Kelly 금지, RESULTS C5). clip 로 factor>0 보장.
    """
    def __init__(self, sign: int = +1, lam: float = 0.1, clip: float = 3.0):
        self.sign = sign
        self.lam = lam
        self.clip = clip
        self._log_e = 0.0
        self._log_factors: list = []     # episode-LOO 용 per-tick log(factor)(empirical-claim §1.2 n<30)
        self.n = 0

    def update(self, x: float) -> float:
        xc = max(-self.clip, min(self.clip, float(x)))
        factor = max(1e-9, 1.0 + self.lam * self.sign * xc)
        lf = math.log(factor)
        self._log_e += lf
        self._log_factors.append(lf)
        self.n += 1
        return math.exp(self._log_e)

    @property
    def e_value(self) -> float:
        return math.exp(self._log_e)

    @property
    def e_value_loo(self) -> float:
        """episode-LOO e-value = 양의 기여 최대 단일 tick 1개 제거 후 e-value(최악 케이스).
        ★small-n(n<30) 카드 confirm 이 단일 outlier episode 에 의존하는지 노출(empirical-claim §1.2
        LOO robustness). 양 기여 없으면(전부 ≤0) 원 e-value 반환(제거해도 안 낮아짐)."""
        if not self._log_factors:
            return self.e_value
        max_pos = max(self._log_factors)
        if max_pos <= 0.0:
            return self.e_value
        return math.exp(self._log_e - max_pos)


# ===========================================================================
# 가변 lifecycle 상태
# ===========================================================================
@dataclass
class FHCState:
    """동적 평가 상태 — 2 e-process(confirm/adverse) + 상태기계 위치 + 부활 카운트.

    e-process = eprocess_backbone.MixtureSPRTEProcess(anytime-valid, optional-stopping robust).
    PIT 재현(dt-keyed replay)은 후속(S2 mediator wiring) — 본 S1 은 live 누적.
    """
    card_id: str
    state: FHCStateEnum = FHCStateEnum.MINTED
    mediator_state: MediatorState = MediatorState.UNKNOWN
    revival_count: int = 0
    realized_bonus: float = 0.0
    holds_ticks: int = 0             # effective N = mediator holds 틱 수(달력 아님)
    history: list = field(default_factory=list)   # [(from, to, reason)]
    _e_confirm: object = None
    _e_reject: object = None

    def __post_init__(self):
        if self._e_confirm is None:
            self._e_confirm = _DirectionalE(sign=+1)        # 예측 적중(IC>0) e-process
        if self._e_reject is None:
            self._e_reject = _DirectionalE(sign=-1)         # adverse(IC<0) e-process

    @property
    def e_value(self) -> float:
        return float(self._e_confirm.e_value)

    @property
    def e_value_loo(self) -> float:
        """confirm e-process 의 episode-LOO e-value(단일 outlier episode 제거 후). empirical-claim §1.2."""
        return float(self._e_confirm.e_value_loo)

    @property
    def e_reject(self) -> float:
        return float(self._e_reject.e_value)


# ===========================================================================
# mediator 평가 (신규 — 전제 gating, alpha-wealth 미소비)
# ===========================================================================
def eval_mediator(spec: MediatorSpec, observable_value: Optional[float] = None,
                  *, posterior_holds: Optional[bool] = None) -> MediatorState:
    """전제 leg 판정. ⛔ mediator 는 discovery 아닌 conditioning event = alpha-wealth 미차감.

    - deterministic_threshold: PIT observable op threshold. value None → UNKNOWN(fail-closed).
    - state_space_posterior / conf_sequence: 외부 posterior_holds(study room filtered) 주입. None → UNKNOWN.
    """
    if spec.test in (MediatorTest.STATE_SPACE_POSTERIOR, MediatorTest.CONF_SEQUENCE):
        if posterior_holds is None:
            return MediatorState.UNKNOWN
        return MediatorState.HOLDS if posterior_holds else MediatorState.FAILS
    if observable_value is None:
        return MediatorState.UNKNOWN
    holds = _OPS[spec.op](float(observable_value), spec.threshold)
    return MediatorState.HOLDS if holds else MediatorState.FAILS


# ===========================================================================
# outcome 갱신 (재사용 e-process + 신규 conditional previsible 규칙)
# ===========================================================================
def update_outcome(state: FHCState, signal_z: float, mediator_holds: bool) -> None:
    """outcome e-process 갱신. ★mediator.holds 틱에만 bet(λ_t=0 if fails).

    signal_z = 예측방향 정합 표준화 관측(rank-IC 부호 인코딩, +면 예측 적중). fails 틱 = no-bet(e 불변).
    mediator.state 는 forward return 실현 전 PIT 데이터로 계산 → λ_t=0 규칙 = previsible betting
    strategy → 귀무 하 valid e-process(별도 보정 불필요, RESULTS C5). adverse = -signal_z(reject leg).
    """
    if not mediator_holds:
        return                                  # λ_t=0, wealth 불변(no-bet)
    state.holds_ticks += 1
    state._e_confirm.update(float(signal_z))    # sign=+1 → IC>0 적중 시 e↑
    state._e_reject.update(float(signal_z))     # sign=−1 → IC<0 adverse 시 e↑(방향 내장)


# ===========================================================================
# realized_bonus (신규 — monotone(log e) clip, INV-4/5)
# ===========================================================================
def bonus_from_evalue(card: FHCard, state: FHCState) -> float:
    """realized_bonus = bonus_cap·(r/(r+1)), r=log(e/threshold). concave·monotone·[0,bonus_cap] 포화.

    INV-5: confirmed/revived + mediator HOLDS 일 때만 >0. INV-4: confirm_e_threshold 전 0, cap 포화.
    ★자본을 움직이는 건 earned e-value 뿐(self-confidence 아님, RESULTS C5 방화벽).
    """
    if state.state not in (FHCStateEnum.CONFIRMED, FHCStateEnum.REVIVED):
        return 0.0
    if state.mediator_state != MediatorState.HOLDS:
        return 0.0                              # vacate/dormant = no bonus(INV-5)
    e = state.e_value
    thr = card.confirm_e_threshold
    if e < thr:
        return 0.0
    r = math.log(e / thr)                       # concave in e, r≥0
    b = card.bonus_cap * (r / (r + 1.0))        # monotone↑, →bonus_cap 점근
    return max(0.0, min(card.bonus_cap, b))


# ===========================================================================
# 5-state machine (조립 — graduation/reject 재사용 + 신규 vacate)
# ===========================================================================
def transition(card: FHCard, state: FHCState, *,
               mediator_state: Optional[MediatorState] = None,
               graduation_decision=None, fdr_firewall=None,
               chatter_backoff=None, now_tick: Optional[int] = None,
               require_loo_robust: bool = False) -> FHCState:
    """5-state 전이 1회. mediator_state 주입(eval_mediator 산출). graduation_decision optional(5-AND).

    전이(RESULTS C13 lifecycle):
      minted→confirmed  : holds AND e_confirm≥thr AND (graduation 미주입 or graduate)
      minted→rejected   : holds AND e_reject≥thr (전제참·예측틀림)
      minted+fails      : minted-dormant(적립 0, ⛔vacate 금지)
      confirmed/revived→vacated : holds→fails(반증 아님, 보너스 suspend)
      confirmed/revived→rejected: holds AND e_reject≥thr(clawback)
      vacated→revived   : fails→holds AND 미기각 AND revival_count<cap
      vacated→rejected  : revival_count≥cap(retire) / holds AND e_reject≥thr
    ⛔ rejected = absorbing(un-reject 불가, 부활=새 card_id).

    ★opt-in 정교화(미주입 시 byte-identical, INV-11):
      - chatter_backoff(reject_recovery.ChatterBackoff) + now_tick: revived→vacated 시 record_kill →
        vacated→revived 직전 can_retry 게이트(지수 cooldown). flapping noise 추격 차단(§14.8a).
        revival_cap(hard limit)과 보완 — cap 전 시간 간격을 벌림. None = 즉시 부활(기존).
      - require_loo_robust: minted→confirmed e-게이트에 episode-LOO 부착(empirical-claim §1.2 n<30).
        단일 outlier episode 제거 후에도 e≥thr 이어야 confirm. False(기본) = byte-identical.
    """
    if mediator_state is not None:
        state.mediator_state = mediator_state
    s = state.state
    ms = state.mediator_state
    holds = ms == MediatorState.HOLDS
    fails = ms == MediatorState.FAILS
    e_conf = state.e_value
    e_rej = state.e_reject

    def _go(new: FHCStateEnum, reason: str):
        state.history.append((s.value, new.value, reason))
        state.state = new

    if s == FHCStateEnum.REJECTED:
        return state                            # absorbing

    if s == FHCStateEnum.MINTED:
        # confirm e-게이트: fdr_firewall 주입 시 alpha-wealth(ELOND) multiplicity 통제(INV-12),
        # 미주입 시 카드 고정 임계(byte-identical fallback).
        confirm_e_ok = (fdr_firewall.test_confirm(card, e_conf)
                        if fdr_firewall is not None
                        else e_conf >= card.confirm_e_threshold)
        # ★episode-LOO robustness(opt-in): 단일 outlier episode 제거 후에도 confirm 임계 생존 요구.
        #   small-n 카드가 한 episode 에 업혀 confirm 박제되는 것 차단(empirical-claim §1.2). 미주입 byte-identical.
        if confirm_e_ok and require_loo_robust:
            confirm_e_ok = state.e_value_loo >= card.confirm_e_threshold
        if holds and e_rej >= card.reject_e_threshold:
            _go(FHCStateEnum.REJECTED, f"minted→reject (adverse e={e_rej:.1f})")
        elif (holds and confirm_e_ok
              and (graduation_decision is None or getattr(graduation_decision, "graduate", True))):
            _go(FHCStateEnum.CONFIRMED, f"minted→confirm (e={e_conf:.1f})")
            state.realized_bonus = bonus_from_evalue(card, state)
        # holds 인데 미돌파, 또는 fails(=minted-dormant, ⛔vacate 금지) → 무전이
        return state

    if s in (FHCStateEnum.CONFIRMED, FHCStateEnum.REVIVED):
        if holds and e_rej >= card.reject_e_threshold:
            _go(FHCStateEnum.REJECTED, f"{s.value}→reject (adverse e={e_rej:.1f}, clawback)")
            state.realized_bonus = 0.0
        elif fails:
            # ★revived→vacated = 부활 후 재이탈 = chatter 사이클 → backoff record_kill(다음 부활 cooldown↑).
            #   confirmed→vacated(첫 suspend)는 chatter 아님 → 미기록.
            if s == FHCStateEnum.REVIVED and chatter_backoff is not None and now_tick is not None:
                chatter_backoff.record_kill(card.card_id, now_tick)
            _go(FHCStateEnum.VACATED, "holds→fails (보너스 suspend, 반증 아님)")
            state.realized_bonus = 0.0
        else:                                   # holds 유지 → 보너스 갱신
            state.realized_bonus = bonus_from_evalue(card, state)
        return state

    if s == FHCStateEnum.VACATED:
        if holds and e_rej >= card.reject_e_threshold:
            _go(FHCStateEnum.REJECTED, f"vacated→reject (adverse e={e_rej:.1f})")
        elif holds and e_rej < card.reject_e_threshold:
            if state.revival_count >= card.revival_cap:
                _go(FHCStateEnum.REJECTED, f"revival_cap({card.revival_cap}) 도달 → retire")
            elif (chatter_backoff is not None and now_tick is not None
                  and not chatter_backoff.can_retry(card.card_id, now_tick)):
                pass        # ★cooldown 중 → 부활 보류(vacated 잔류, flapping noise 추격 차단). 무전이.
            else:
                state.revival_count += 1
                _go(FHCStateEnum.REVIVED, f"vacated→revived #{state.revival_count}")
                state.realized_bonus = bonus_from_evalue(card, state)
        return state

    return state


# ===========================================================================
# self-test (verifier 대체 — 전 경로 + INV 집행 검증)
# ===========================================================================
if __name__ == "__main__":
    def _mk(**kw):
        base = dict(
            card_id="fhc.test", scope="macro", domain="macro", direction="long_tilt",
            statement="capex 가속 → 산업재 tilt", falsification_metric="capex 꺾이면 무효",
            mediator=MediatorSpec("capex_yoy", op=">", threshold=0.0),
            outcome=OutcomeSpec("ts_rank_IC", "indus_tilt"),
            bonus_cap=0.03, confirm_e_threshold=20.0, reject_e_threshold=20.0,
        )
        base.update(kw)
        return FHCard(**base)

    # 1) 반증불가 카드 차단(card_contract 정합)
    try:
        _mk(falsification_metric="  ")
        raise AssertionError("빈 falsification 통과")
    except ValueError:
        print("1) 반증불가 카드 차단 OK")

    # 2) mediator 평가: deterministic / state_space / fail-closed
    sp = MediatorSpec("x", op=">", threshold=0.0)
    assert eval_mediator(sp, 0.5) == MediatorState.HOLDS
    assert eval_mediator(sp, -0.5) == MediatorState.FAILS
    assert eval_mediator(sp, None) == MediatorState.UNKNOWN            # fail-closed
    ssp = MediatorSpec("r", test=MediatorTest.STATE_SPACE_POSTERIOR)
    assert eval_mediator(ssp, posterior_holds=True) == MediatorState.HOLDS
    assert eval_mediator(ssp, posterior_holds=None) == MediatorState.UNKNOWN
    print("2) mediator 평가(deterministic/state_space/fail-closed UNKNOWN) OK")

    # 3) minted→confirmed: 전제 holds + 강 신호 e돌파 → 보너스 적립
    c = _mk()
    st = FHCState(c.card_id)
    for _ in range(60):
        update_outcome(st, 1.2, mediator_holds=True)                  # 강 적중 신호
    transition(c, st, mediator_state=MediatorState.HOLDS)
    assert st.state == FHCStateEnum.CONFIRMED, st.state
    assert 0.0 < st.realized_bonus <= c.bonus_cap, st.realized_bonus
    print(f"3) minted→confirmed OK: e={st.e_value:.1f} bonus={st.realized_bonus:.4f}≤cap{c.bonus_cap}")

    # 4) confirmed→vacated: holds→fails → 보너스 suspend(반증 아님)
    transition(c, st, mediator_state=MediatorState.FAILS)
    assert st.state == FHCStateEnum.VACATED and st.realized_bonus == 0.0, (st.state, st.realized_bonus)
    print("4) confirmed→vacated OK: 보너스 suspend(0), 카드 생존")

    # 5) vacated→revived: fails→holds 재성립 + 미기각 → revival_count++
    transition(c, st, mediator_state=MediatorState.HOLDS)
    assert st.state == FHCStateEnum.REVIVED and st.revival_count == 1, (st.state, st.revival_count)
    assert st.realized_bonus > 0.0, st.realized_bonus
    print(f"5) vacated→revived OK: #{st.revival_count} bonus={st.realized_bonus:.4f}")

    # 6) ★INV: minted→vacated 금지(minted-dormant)
    c2 = _mk(card_id="fhc.dormant")
    st2 = FHCState(c2.card_id)
    transition(c2, st2, mediator_state=MediatorState.FAILS)
    assert st2.state == FHCStateEnum.MINTED, st2.state             # vacate 아님 = minted 유지
    assert st2.realized_bonus == 0.0
    print("6) INV minted→vacated 금지 OK: fails → minted-dormant(적립 0)")

    # 7) ★INV: rejected absorbing — adverse e돌파 → reject 후 holds 와도 불변
    c3 = _mk(card_id="fhc.rej", reject_e_threshold=5.0)
    st3 = FHCState(c3.card_id)
    for _ in range(80):
        update_outcome(st3, -1.5, mediator_holds=True)            # 강 역방향 = adverse e↑
    transition(c3, st3, mediator_state=MediatorState.HOLDS)
    assert st3.state == FHCStateEnum.REJECTED, st3.state
    transition(c3, st3, mediator_state=MediatorState.HOLDS)        # 재시도
    assert st3.state == FHCStateEnum.REJECTED, "rejected 가 absorbing 아님"
    print(f"7) INV rejected absorbing OK: e_reject={st3.e_reject:.1f} 재전이 불가")

    # 8) ★INV: revival_cap → retire(rejected)
    c4 = _mk(card_id="fhc.cap", revival_cap=1)
    st4 = FHCState(c4.card_id)
    for _ in range(60):
        update_outcome(st4, 1.2, mediator_holds=True)
    transition(c4, st4, mediator_state=MediatorState.HOLDS)        # confirmed
    transition(c4, st4, mediator_state=MediatorState.FAILS)        # vacated
    transition(c4, st4, mediator_state=MediatorState.HOLDS)        # revived #1
    transition(c4, st4, mediator_state=MediatorState.FAILS)        # vacated
    transition(c4, st4, mediator_state=MediatorState.HOLDS)        # cap=1 도달 → retire
    assert st4.state == FHCStateEnum.REJECTED, st4.state
    print("8) INV revival_cap → retire(rejected) OK")

    # 9) ★INV-5: confirmed 라도 mediator HOLDS 아니면 보너스 0(no leak)
    c5 = _mk(card_id="fhc.b")
    st5 = FHCState(c5.card_id)
    for _ in range(60):
        update_outcome(st5, 1.2, mediator_holds=True)
    transition(c5, st5, mediator_state=MediatorState.HOLDS)
    b_holds = bonus_from_evalue(c5, st5)
    st5.mediator_state = MediatorState.UNKNOWN
    assert bonus_from_evalue(c5, st5) == 0.0, "UNKNOWN 인데 보너스 누출"
    print(f"9) INV-5 fail-closed bonus OK: holds={b_holds:.4f} / unknown=0")

    # 10) ★previsible: fails 틱 no-bet(e 불변)
    c6 = _mk(card_id="fhc.prev")
    st6 = FHCState(c6.card_id)
    e0 = st6.e_value
    for _ in range(30):
        update_outcome(st6, 1.5, mediator_holds=False)            # fails → no-bet
    assert st6.e_value == e0 and st6.holds_ticks == 0, (st6.e_value, e0)
    print("10) previsible no-bet OK: fails 30틱 → e 불변(holds_ticks=0)")

    # 11) ★chatter backoff 통합(reject_recovery 재사용): revived→vacated record_kill → cooldown 중 부활 보류
    from core.assume.reject_recovery import ChatterBackoff
    cb = ChatterBackoff(base_cooldown=4, max_cooldown=256)
    c7 = _mk(card_id="fhc.chat", revival_cap=5)
    st7 = FHCState(c7.card_id)
    for _ in range(60):
        update_outcome(st7, 1.2, mediator_holds=True)
    transition(c7, st7, mediator_state=MediatorState.HOLDS, chatter_backoff=cb, now_tick=0)   # confirmed
    assert st7.state == FHCStateEnum.CONFIRMED
    transition(c7, st7, mediator_state=MediatorState.FAILS, chatter_backoff=cb, now_tick=1)   # confirmed→vacated(record_kill 안함)
    transition(c7, st7, mediator_state=MediatorState.HOLDS, chatter_backoff=cb, now_tick=2)   # revived #1(cooldown 없음)
    assert st7.state == FHCStateEnum.REVIVED and st7.revival_count == 1, (st7.state, st7.revival_count)
    transition(c7, st7, mediator_state=MediatorState.FAILS, chatter_backoff=cb, now_tick=3)   # revived→vacated: record_kill(until=3+4=7)
    transition(c7, st7, mediator_state=MediatorState.HOLDS, chatter_backoff=cb, now_tick=5)   # cooldown 중(5<7) → 부활 보류
    assert st7.state == FHCStateEnum.VACATED and st7.revival_count == 1, (st7.state, st7.revival_count)
    transition(c7, st7, mediator_state=MediatorState.HOLDS, chatter_backoff=cb, now_tick=7)   # 경과(7≥7) → 부활 #2
    assert st7.state == FHCStateEnum.REVIVED and st7.revival_count == 2, (st7.state, st7.revival_count)
    print("11) ★chatter backoff 통합 OK: revived→vacated record_kill → cooldown 중 부활 보류 → 경과 후 부활 #2")

    # 12) ★episode-LOO robustness(empirical-claim §1.2): 단일 outlier episode 에 업힌 confirm 차단
    c8 = _mk(card_id="fhc.loo", confirm_e_threshold=20.0)
    def _loo_state():
        st = FHCState("fhc.loo.x")
        for _ in range(60):
            update_outcome(st, 0.5, mediator_holds=True)   # 약신호 다수(e 를 threshold 직전까지)
        update_outcome(st, 3.0, mediator_holds=True)        # 강 outlier 1개(threshold 위로 밀어 올림)
        return st
    st8 = _loo_state()
    e_full, e_loo = st8.e_value, st8.e_value_loo
    assert e_full >= 20.0 > e_loo, (e_full, e_loo)          # full 통과, 단일 episode 제거 시 붕괴
    transition(c8, st8, mediator_state=MediatorState.HOLDS)                          # robust off(기본)
    assert st8.state == FHCStateEnum.CONFIRMED, st8.state
    st8b = _loo_state()
    transition(c8, st8b, mediator_state=MediatorState.HOLDS, require_loo_robust=True)  # robust on
    assert st8b.state == FHCStateEnum.MINTED, st8b.state    # LOO 후 미달 → confirm 보류(minted 잔류)
    print(f"12) ★episode-LOO OK: e={e_full:.1f}≥20>LOO={e_loo:.1f} / robust=off confirm, on 보류(단일 episode 의존 차단)")

    print("\nfhc self-test PASS (2-leg mediator/outcome · 5-state · INV minted-dormant/absorbing/"
          "revival-cap/fail-closed-bonus · previsible no-bet · chatter-backoff 통합 · episode-LOO robustness · "
          "기존 e-process 재사용)")
