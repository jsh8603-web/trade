"""core/assume/macro_mediator.py — FHC macro mediator 구독 어댑터 (S2 state-space filtered posterior).

fhc.eval_mediator(STATE_SPACE_POSTERIOR) 는 posterior_holds(bool) 만 받는다(자산무관 core =
MacroView 무지, button plug-in 호환). 본 어댑터가 brain↔assume 단방향 seam: MacroView →
belief 분포(regime_belief_adapter.belief_from_macro_view 재사용) → 전제 국면 holds 판정(bool).
fhc.py 는 MacroView 를 import 하지 않는다(레이어 분리 유지 — 의존은 본 파일 한 곳).

설계 정합:
- ★filtered-only(§5.8-H look-ahead 방지): regime_now(PIT classifier, NBER lag 미사용)에서 파생된
  belief 만 구독. regime_forecast(선행)·smoother 는 구독 금지(backtest look-ahead = e-process 오염).
  belief_from_macro_view 가 regime_now+confidence_now 만 쓰므로 본 어댑터는 자동 filtered-only.
- ★fail-closed(INV-3): macro_view None / unavailable / stale-too-old / 라벨 불일치 → None(UNKNOWN)
  → eval_mediator 가 UNKNOWN 반환 → 보너스 미적립(모르면 안 건다).
- ★entropy 게이트(옵션): belief 분포가 평탄(국면 모호)하면 mass 가 우연히 임계를 넘어도 holds 보류.
  MacroView 원본은 점추정+스칼라 confidence 라 full posterior entropy 가 없지만, belief 변환 후
  분포에서 정규화 entropy 를 산출해 multi-modal/저확신 국면을 보수적으로 거른다.
- ★additive(INV-11): 호출처 0(go-live 시 카드 mint→mediator 평가 경로서 소비). 기존 모듈 무수정.
  regime_belief_adapter / fhc 둘 다 import 만 하고 수정하지 않는다.

observable_ref 형식: "regime:{BLOC}:{Label}" | "regime:{Label}" | "{Label}".
  BLOC ∈ {USD, KRW}(생략 시 USD 우선). Label ∈ RegimeLabel value(Reflation/Recovery/Overheat/Stagflation).
  threshold = 전제 국면 belief 질량 임계(예 0.5). op = 비교(기본 ">").
"""

from __future__ import annotations

import math
from typing import Optional

from core.assume.fhc import MediatorState, MediatorSpec, MediatorTest, eval_mediator, _OPS
from core.brain.regime_belief_adapter import REGIME_LABELS, belief_from_macro_view, calibrated_belief


def _parse_ref(observable_ref: str):
    """observable_ref → (bloc_name, label). 'regime' prefix 는 버린다. 미파싱 → (None, None)."""
    parts = [p.strip() for p in str(observable_ref or "").split(":") if p.strip()]
    if parts and parts[0].lower() == "regime":
        parts = parts[1:]
    if len(parts) == 2:
        return parts[0], parts[1]
    if len(parts) == 1:
        return None, parts[0]
    return None, None


def _resolve_bloc(bloc_name: Optional[str]):
    """'USD'/'KRW' → Bloc enum. 미매칭/None → None(belief_from_macro_view 가 USD 우선 처리)."""
    if not bloc_name:
        return None
    try:
        from core.brain.macro_schema import Bloc
    except Exception:
        return None
    key = bloc_name.strip().upper()
    return {"USD": Bloc.USD, "KRW": Bloc.KRW}.get(key)


def belief_entropy(belief: dict, labels: tuple = REGIME_LABELS) -> float:
    """belief 분포의 정규화 Shannon entropy [0,1]. 1=완전 평탄(uniform), 0=완전 집중(one-hot 근접)."""
    n = max(len(labels), 1)
    if n <= 1:
        return 0.0
    ps = [max(1e-12, float(belief.get(lab, 0.0))) for lab in labels]
    s = sum(ps) or 1.0
    ps = [p / s for p in ps]
    h = -sum(p * math.log(p) for p in ps)
    return h / math.log(n)


def _is_view_usable(macro_view, max_stale_seconds: Optional[float]) -> bool:
    """fail-closed 사전 게이트: None/unavailable/stale-too-old → False(=UNKNOWN 매핑)."""
    if macro_view is None or not getattr(macro_view, "regimes", None):
        return False
    try:
        from core.brain.macro_schema import ViewStatus
    except Exception:
        ViewStatus = None
    status = getattr(macro_view, "status", None)
    if ViewStatus is not None and status == ViewStatus.UNAVAILABLE:
        return False
    if max_stale_seconds is not None:
        age = getattr(macro_view, "age_seconds", None)
        if age is not None and float(age) > float(max_stale_seconds):
            return False
    return True


def macro_posterior_holds(
    macro_view,
    spec: MediatorSpec,
    *,
    calibrator=None,
    max_stale_seconds: Optional[float] = None,
    max_entropy: Optional[float] = None,
    labels: tuple = REGIME_LABELS,
) -> Optional[bool]:
    """MacroView → 전제 국면 belief 질량 (op) threshold → posterior_holds. fail-closed = None.

    macro_view        : core.brain.macro_schema.MacroView (regime_now+confidence_now filtered).
    spec              : FHC MediatorSpec. observable_ref 가 target 국면, threshold/op 가 belief 질량 게이트.
    calibrator        : TemperatureCalibrator(frozen) 옵션 — 있으면 calibrated_belief, 없으면 raw soft.
    max_stale_seconds : view age 초과 시 None(데이터 만료=모름). None=무제한.
    max_entropy       : 정규화 belief entropy 상한(평탄 국면 holds 보류). None=entropy 게이트 off.

    반환: True(holds) / False(fails) / None(UNKNOWN=fail-closed).
    """
    if not _is_view_usable(macro_view, max_stale_seconds):
        return None

    bloc_name, label = _parse_ref(spec.observable_ref)
    if not label or label not in labels:
        return None  # target 국면 미지정/오타 = 판정 불가 = fail-closed
    bloc = _resolve_bloc(bloc_name)

    belief = calibrated_belief(macro_view, calibrator=calibrator, bloc=bloc, labels=labels)
    mass = float(belief.get(label, 0.0))

    op_fn = _OPS.get(spec.op)
    if op_fn is None:
        return None
    holds = bool(op_fn(mass, float(spec.threshold)))

    # entropy 게이트: mass 통과여도 분포가 평탄(국면 모호)하면 보수적으로 보류(fails).
    if holds and max_entropy is not None:
        if belief_entropy(belief, labels) > float(max_entropy):
            holds = False
    return holds


def eval_macro_mediator(
    macro_view,
    spec: MediatorSpec,
    *,
    calibrator=None,
    max_stale_seconds: Optional[float] = None,
    max_entropy: Optional[float] = None,
) -> MediatorState:
    """구독 어댑터 → fhc.eval_mediator 연결 한 줄 헬퍼. STATE_SPACE_POSTERIOR 전용.

    deterministic spec 이 들어오면 posterior_holds=None 으로 위임(eval_mediator 가 observable 경로 처리).
    """
    if spec.test not in (MediatorTest.STATE_SPACE_POSTERIOR, MediatorTest.CONF_SEQUENCE):
        return eval_mediator(spec, None)
    holds = macro_posterior_holds(
        macro_view, spec,
        calibrator=calibrator,
        max_stale_seconds=max_stale_seconds,
        max_entropy=max_entropy,
    )
    return eval_mediator(spec, posterior_holds=holds)


if __name__ == "__main__":
    from core.brain.macro_schema import Bloc, MacroView, RegimeEstimate, RegimeLabel, ViewStatus

    def _view(label, conf, status=ViewStatus.FRESH, as_of=0.0):
        est = RegimeEstimate(bloc=Bloc.USD, regime_now=label, confidence_now=conf)
        return MacroView(regimes={Bloc.USD: est}, status=status, as_of_ts=as_of)

    sp = MediatorSpec("regime:USD:Overheat", test=MediatorTest.STATE_SPACE_POSTERIOR,
                      op=">=", threshold=0.5)

    # 1) target 국면 高 confidence → holds
    assert macro_posterior_holds(_view(RegimeLabel.OVERHEAT, 0.9), sp) is True
    print("1) target 국면 高 confidence → HOLDS OK")

    # 2) target 국면 低 confidence(평탄) → mass<0.5 → fails
    assert macro_posterior_holds(_view(RegimeLabel.OVERHEAT, 0.1), sp) is False
    print("2) target 국면 低 confidence(평탄) → FAILS OK")

    # 3) 다른 국면 → fails
    assert macro_posterior_holds(_view(RegimeLabel.RECOVERY, 0.9), sp) is False
    print("3) 다른 국면(Recovery) → FAILS OK")

    # 4) unavailable → None(fail-closed)
    assert macro_posterior_holds(MacroView.unavailable(), sp) is None
    # 5) None view → None
    assert macro_posterior_holds(None, sp) is None
    print("4-5) unavailable / None view → UNKNOWN(None) fail-closed OK")

    # 6) 오타/미지정 target → None
    bad = MediatorSpec("regime:USD:Nonexistent", test=MediatorTest.STATE_SPACE_POSTERIOR)
    assert macro_posterior_holds(_view(RegimeLabel.OVERHEAT, 0.9), bad) is None
    print("6) target 라벨 오타 → UNKNOWN(None) fail-closed OK")

    # 7) stale-too-old → None
    import time as _t
    old = _view(RegimeLabel.OVERHEAT, 0.9, status=ViewStatus.STALE, as_of=_t.time() - 10_000)
    assert macro_posterior_holds(old, sp, max_stale_seconds=3600) is None
    fresh = _view(RegimeLabel.OVERHEAT, 0.9, as_of=_t.time())
    assert macro_posterior_holds(fresh, sp, max_stale_seconds=3600) is True
    print("7) stale-too-old → None / fresh → HOLDS OK")

    # 8) entropy 게이트: mass 통과여도 평탄하면 보류. conf=0.5 → mass≈0.5 통과하나 분포 덜 평탄.
    sp_lo = MediatorSpec("regime:USD:Overheat", test=MediatorTest.STATE_SPACE_POSTERIOR,
                         op=">=", threshold=0.3)
    v_mod = _view(RegimeLabel.OVERHEAT, 0.35)
    holds_no_ent = macro_posterior_holds(v_mod, sp_lo)
    holds_ent = macro_posterior_holds(v_mod, sp_lo, max_entropy=0.85)
    assert holds_no_ent is True
    assert holds_ent is False  # 평탄(entropy>0.85) → 보류
    print(f"8) entropy 게이트: no-gate=HOLDS / gate(0.85)=FAILS (평탄 보류) OK")

    # 9) eval_macro_mediator → MediatorState 연결
    assert eval_macro_mediator(_view(RegimeLabel.OVERHEAT, 0.9), sp) == MediatorState.HOLDS
    assert eval_macro_mediator(_view(RegimeLabel.RECOVERY, 0.9), sp) == MediatorState.FAILS
    assert eval_macro_mediator(MacroView.unavailable(), sp) == MediatorState.UNKNOWN
    # deterministic spec → observable 경로 위임(value None → UNKNOWN)
    det = MediatorSpec("x", test=MediatorTest.DETERMINISTIC_THRESHOLD)
    assert eval_macro_mediator(None, det) == MediatorState.UNKNOWN
    print("9) eval_macro_mediator → HOLDS/FAILS/UNKNOWN + deterministic 위임 OK")

    print("S2 macro_mediator self-test PASS "
          "(filtered-only belief 구독 · fail-closed UNKNOWN · entropy 게이트 · eval_mediator 연결)")
