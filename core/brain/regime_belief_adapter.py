"""core/brain/regime_belief_adapter.py — 거시상황(MacroView) → R15 belief b(t) 어댑터 (CL-W 배선 b).

CONSULT-DECISIONS-weight-20260529.md §1.6 (belief b(t)) 라이브 공급 seam.

3-subagent connectivity 검증(2026-05-30)이 지적한 "belief 공급원 부재" 해소: regime 분류기
(RegimeClassifier.classify→MacroView)의 거시상황 판정을 R15 가중학습의 belief 분포 b(t) 로 변환한다.
이 belief 가 effective_precision(models, belief)·weight_cycle 의 동적 가중 입력이 된다.

★사용자 핵심: "어떤 거시상황인지에 따라" — regime_now(argmax 거시국면) + confidence_now 를
soft belief 로 푼다. confidence 높으면 해당 국면에 집중, 낮으면 평탄(=transition de-risk 로 이어짐,
effective_precision 의 between-dispersion 이 자동 inflate).

★b(t) frozen(§1.6): 결정시점 belief 를 동결(predictable convex combo = mixture e-process
supermartingale 보존). 반환 dict 를 WeightAssumptionCard.belief_vector 로 박제 → replay 재현.

⛔ 추정(glasso·calibration)은 본 모듈 범위 밖. 여기는 거시상황 → belief 변환만(라이브 공급).
classifier confidence 의 정식 calibration(TemperatureCalibrator, OOS label fit)은 substrate 도착
후 connect(현재는 raw confidence soft-spread, calibrator 옵션 주입 가능).
"""

from __future__ import annotations

from typing import Optional

# RegimeLabel 4-state (macro_schema). regime_to_weights 와 동일 라벨 공간.
REGIME_LABELS = ("Reflation", "Recovery", "Overheat", "Stagflation")


def belief_from_macro_view(
    macro_view,
    *,
    bloc=None,
    labels: tuple = REGIME_LABELS,
    floor: float = 0.02,
) -> dict:
    """MacroView(거시상황 판정) → R15 belief 분포 {regime_label: prob}, 합=1.

    regime_now(argmax 국면)에 confidence_now 질량, 나머지 국면에 (1−conf) 균등 분배 + floor.
    - confidence 高 → regime_now 집중(거시상황 확신) → 해당 국면 Ω 지배.
    - confidence 低 → 평탄 → effective_precision between-dispersion inflate(transition de-risk).
    unavailable/regimes 부재 → uniform(최대 불확실 = 자동 de-risk). floor = 0 belief 방지(역행렬 안정).
    """
    try:
        from core.brain.macro_schema import Bloc, ViewStatus
    except Exception:
        Bloc = ViewStatus = None

    n = len(labels)
    uniform = {lab: 1.0 / n for lab in labels}

    if macro_view is None or not getattr(macro_view, "regimes", None):
        return uniform
    if ViewStatus is not None and getattr(macro_view, "status", None) == ViewStatus.UNAVAILABLE:
        return uniform

    regimes = macro_view.regimes
    if bloc is None:
        # 메인 bloc(USD) 우선, 없으면 첫 항목.
        if Bloc is not None and Bloc.USD in regimes:
            bloc = Bloc.USD
        else:
            bloc = next(iter(regimes))
    est = regimes.get(bloc)
    if est is None:
        return uniform

    now = getattr(est, "regime_now", None)
    label_now = getattr(now, "value", now)
    conf = float(getattr(est, "confidence_now", 0.0) or 0.0)
    conf = max(0.0, min(1.0, conf))
    if label_now not in labels:
        return uniform

    # soft belief: regime_now 에 conf, 나머지 (1−conf) 균등. floor 보장 후 재정규화.
    rest = [lab for lab in labels if lab != label_now]
    b = {lab: max(floor, (1.0 - conf) / max(len(rest), 1)) for lab in rest}
    b[label_now] = max(floor, conf)
    s = sum(b.values())
    return {lab: b[lab] / s for lab in labels}


def belief_vector(belief: dict, labels: tuple = REGIME_LABELS) -> tuple:
    """belief dict → 고정 순서 tuple (WeightAssumptionCard.belief_vector 박제용, replay 순서불변)."""
    return tuple(float(belief.get(lab, 0.0)) for lab in labels)


def calibrated_belief(
    macro_view,
    calibrator=None,
    *,
    bloc=None,
    labels: tuple = REGIME_LABELS,
) -> dict:
    """calibrator(TemperatureCalibrator, frozen) 가 있으면 보정 belief, 없으면 raw soft belief.

    classifier 가 logit/probability 시계열을 노출하고 OOS label 로 fit 된 calibrator 가 주입되면
    그 보정 확률을 belief 로 쓴다(과신 boundary 완화). 현재 MacroView 는 점추정+confidence 라
    calibrator 없으면 belief_from_macro_view(raw soft-spread) 로 graceful. substrate 도착 후 connect.
    """
    if calibrator is None or not hasattr(macro_view, "regime_logits"):
        return belief_from_macro_view(macro_view, bloc=bloc, labels=labels)
    logits = macro_view.regime_logits          # (1, n) 또는 (n,)
    try:
        probs = calibrator.transform(logits)
        p = probs[0] if getattr(probs, "ndim", 1) > 1 else probs
        b = {lab: float(p[i]) for i, lab in enumerate(labels)}
        s = sum(b.values()) or 1.0
        return {lab: b[lab] / s for lab in labels}
    except Exception:
        return belief_from_macro_view(macro_view, bloc=bloc, labels=labels)


if __name__ == "__main__":
    from core.brain.macro_schema import Bloc, MacroView, RegimeEstimate, RegimeLabel, ViewStatus

    def _view(label, conf, status=ViewStatus.FRESH):
        est = RegimeEstimate(bloc=Bloc.USD, regime_now=label, confidence_now=conf)
        return MacroView(regimes={Bloc.USD: est}, status=status, as_of_ts=0.0)

    # 1) confidence 高 → regime_now 집중
    b_hi = belief_from_macro_view(_view(RegimeLabel.OVERHEAT, 0.9))
    assert abs(sum(b_hi.values()) - 1.0) < 1e-9
    assert b_hi["Overheat"] > 0.85 and max(b_hi, key=b_hi.get) == "Overheat"
    print(f"1) confidence 高(0.9) → 집중: {{k: round(v,3) for...}} Overheat={b_hi['Overheat']:.3f}")

    # 2) confidence 低 → 평탄(uniform 근접) = transition de-risk 유발
    b_lo = belief_from_macro_view(_view(RegimeLabel.OVERHEAT, 0.1))
    spread_hi = max(b_hi.values()) - min(b_hi.values())
    spread_lo = max(b_lo.values()) - min(b_lo.values())
    assert spread_lo < spread_hi, (spread_lo, spread_hi)
    print(f"2) confidence 低(0.1) → 평탄: spread {spread_lo:.3f} < 高 {spread_hi:.3f} (de-risk)")

    # 3) 합=1 + floor 보장(0 belief 없음 = 역행렬 안정)
    assert all(v >= 0.02 - 1e-9 for v in b_hi.values()) and abs(sum(b_lo.values()) - 1.0) < 1e-9
    print(f"3) 합=1 + floor≥0.02 보장 OK")

    # 4) unavailable → uniform(최대 불확실 = 자동 de-risk)
    b_un = belief_from_macro_view(MacroView.unavailable())
    assert all(abs(v - 0.25) < 1e-9 for v in b_un.values())
    print(f"4) unavailable → uniform {b_un['Reflation']:.2f} (자동 de-risk)")

    # 5) belief_vector 순서 고정(replay 박제)
    v = belief_vector(b_hi)
    assert len(v) == 4 and abs(v[2] - b_hi["Overheat"]) < 1e-9   # labels[2]=Overheat
    print(f"5) belief_vector 순서고정 OK: {tuple(round(x,3) for x in v)}")

    # 6) calibrator 없음 → raw soft belief graceful (substrate 게이트)
    b_cal = calibrated_belief(_view(RegimeLabel.RECOVERY, 0.7), calibrator=None)
    assert max(b_cal, key=b_cal.get) == "Recovery"
    print(f"6) calibrator 없음 → raw soft graceful: Recovery={b_cal['Recovery']:.3f}")

    print("CL-W regime_belief_adapter self-test PASS "
          "(거시상황→belief b(t), confidence soft-spread, floor, uniform fallback, 순서박제, calibrator graceful)")
