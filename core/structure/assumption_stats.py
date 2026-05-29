"""core/structure/assumption_stats.py — 가정 검증통계 엔진 (T2 도메인 핵심).

분담: T2 = 검증통계·regime·구조모델. T3(btn-Codlearn) = AssumptionCard/Registry/Validator/
UpdateController orchestration. 본 모듈 = T3 Validator 가 dispatch 해 호출하는 **통계 엔진**
(Card/Registry/Controller 자체는 T3). 결정 X, 통계 산출만 (관측≠제어, claude D 원칙 동형).

핵심 설계 (자문 수렴):
- **kind dispatch** (claude A-0): structural(메커니즘 작동?) → regime/추세 detection /
  parametric(추정 안정?) → drift/change-point. 같은 통계로 판정하면 조건부참 구조가정 기각 +
  깨진 모수 통과. archetype dispatch 패턴 재사용.
- **regime-conditional 검증** (claude A-1 핵심 누락): pooled 금지. holds 는 **레짐별**.
  레짐 A서 참·B서 거짓 조건부 가정 오판 방지. 현재 regime 판정만 거래에 쓴다.
- **hysteresis AND-gate** (claude A-2): ChangeRequest 승격 = (online-FDR 유의 ∧ 효과 material
  ∧ dwell-time ∧ K-윈도우 지속 ∧ 동일 regime) 전부. consensus.py 보다 빡세게.
- **base-layer 가정** (claude C-meta): regime 모델 = 토대 가정. 자동변경 금지(사람 소유).
- **신뢰도→band→사이징** (claude C / gemini C-2): 신뢰도 낮으면 넓은 band → 작은 포지션/abstain.
- **생존편향** (양 자문): 검증 패널은 as-of 당시 살아있던 전체 모집단(상폐 포함). panel_schema
  의 delist_flag 가 그 계약 — 이 모듈은 패널을 그대로 신뢰(필터 안 함).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

import numpy as np

from core.structure.detectors import Cusum, Bocpd, psi, prequential_loss
# R15 §1.8 — IC falsification 검정력 게이트 (조건부상관 모듈에서 산출, 여기서 AND-gate 에 wire)
from core.structure.conditional_correlation import ic_power_gate, ICPowerVerdict  # noqa: F401

AssumptionKind = Literal["structural", "parametric"]


# ---------------------------------------------------------------------------
# regime-conditional ValidationReport (pooled 금지)
# ---------------------------------------------------------------------------

@dataclass
class RegimeHolds:
    regime_id: int
    holds: bool
    n_obs: int
    confidence: float                 # 0..1 (gemini C-2: n_obs·효과 기반)
    evidence: dict = field(default_factory=dict)


@dataclass
class RegimeConditionalReport:
    assumption_id: str
    kind: AssumptionKind
    by_regime: dict[int, RegimeHolds]            # ★ 레짐별 (pooled 아님)
    current_regime: int
    notes: list[str] = field(default_factory=list)

    @property
    def holds_now(self) -> Optional[bool]:
        """현재 regime 의 holds 만 거래 판정에 사용."""
        rh = self.by_regime.get(self.current_regime)
        return rh.holds if rh else None

    @property
    def confidence_now(self) -> float:
        rh = self.by_regime.get(self.current_regime)
        return rh.confidence if rh else 0.0


def assumption_confidence(n_obs: int, effect_size: float, min_n: int = 20) -> float:
    """가정 신뢰도 0..1 (gemini C-2). n_obs 충분 + 효과 작을수록(=가정 안정) 높음.

    effect_size = |위반 정도| (Cohen's d 류). 작을수록 가정 잘 성립 → 신뢰도↑.
    """
    if n_obs < 3:
        return 0.0
    n_factor = min(1.0, n_obs / max(min_n, 1))          # 표본 충분도
    stability = 1.0 / (1.0 + max(effect_size, 0.0))     # 위반 클수록 신뢰도↓
    return float(np.clip(n_factor * stability, 0.0, 1.0))


# ---------------------------------------------------------------------------
# kind dispatch — parametric / structural validator
# ---------------------------------------------------------------------------

def validate_parametric(
    assumption_id: str,
    assumed_value: float,
    realized: np.ndarray,
    regime_ids: np.ndarray,
    current_regime: int,
    sd: Optional[float] = None,
    psi_threshold: float = 0.25,
) -> RegimeConditionalReport:
    """모수가정("정상 멀티플=θ", "임계값=θ") → 추정 안정성 = drift/change-point.

    레짐별로 realized 가 assumed_value 근처 안정인지 CUSUM(평균이동) + PSI(분포이동).
    """
    realized = np.asarray(realized, float)
    regime_ids = np.asarray(regime_ids, int)
    sd = sd if sd is not None else (float(np.nanstd(realized)) or 1.0)
    by_regime: dict[int, RegimeHolds] = {}

    for r in np.unique(regime_ids):
        rv = realized[regime_ids == r]
        rv = rv[np.isfinite(rv)]
        if len(rv) < 3:
            continue
        # CUSUM: assumed_value 기준 평균이동
        cu = Cusum(target=assumed_value, sd=sd, k_sigma=1.0, h_sigma=5.0)
        cusum_fired = any(cu.update(float(x)) for x in rv)
        # PSI: 가정 분포(assumed±sd 합성 baseline) vs realized
        baseline = assumed_value + sd * np.random.default_rng(0).normal(0, 1, max(len(rv), 30))
        p = psi(baseline, rv)
        # 효과크기 (Cohen's d): 실현평균이 가정에서 얼마나 벗어났나
        d = abs(float(np.mean(rv)) - assumed_value) / sd
        holds = (not cusum_fired) and (not (np.isfinite(p) and p > psi_threshold))
        conf = assumption_confidence(len(rv), d)
        by_regime[int(r)] = RegimeHolds(
            int(r), holds, len(rv), conf,
            evidence={"cusum_fired": cusum_fired, "psi": round(float(p), 3),
                      "cohens_d": round(d, 3), "mean_realized": round(float(np.mean(rv)), 3)},
        )
    return RegimeConditionalReport(assumption_id, "parametric", by_regime, current_regime,
                                   notes=[f"sd={sd:.3f}, regimes={sorted(by_regime)}"])


def validate_structural(
    assumption_id: str,
    predictions: np.ndarray,
    outcomes: np.ndarray,
    regime_ids: np.ndarray,
    current_regime: int,
) -> RegimeConditionalReport:
    """구조가정("반도체 PER 은 공정주기를 탄다") → 메커니즘 작동성 = 예측력 추세.

    레짐별로 가정 예측 vs 실현의 prequential loss kink + BOCPD run-length 붕괴 →
    "이 레짐에서 메커니즘이 여전히 작동하는가". (forward-return 예측 아님 — 멀티플 수준 설명력.)
    """
    predictions = np.asarray(predictions, float)
    outcomes = np.asarray(outcomes, float)
    regime_ids = np.asarray(regime_ids, int)
    by_regime: dict[int, RegimeHolds] = {}

    for r in np.unique(regime_ids):
        m = regime_ids == r
        pred, out = predictions[m], outcomes[m]
        fin = np.isfinite(pred) & np.isfinite(out)
        pred, out = pred[fin], out[fin]
        if len(pred) < 5:
            continue
        pr = prequential_loss(pred, out, recent_window=max(3, len(pred) // 4))
        # BOCPD run-length 붕괴 = 메커니즘 단절
        b = Bocpd(hazard_lambda=max(20.0, len(pred)))
        rls = []
        for e in (pred - out):
            b.update(float(e)); rls.append(b.map_run_length)
        rl_collapse = bool(len(rls) >= 6 and max(rls[:len(rls)//2]) - min(rls[len(rls)//2:]) >= max(5, len(rls)//4))
        holds = (not pr.kink_alert) and (not rl_collapse)
        # 효과: 최근 손실 기울기 정규화
        eff = abs(pr.recent_slope) / (pr.mean_loss + 1e-9) if np.isfinite(pr.recent_slope) else 0.0
        conf = assumption_confidence(len(pred), eff)
        by_regime[int(r)] = RegimeHolds(
            int(r), holds, len(pred), conf,
            evidence={"prequential_kink": pr.kink_alert, "rl_collapse": rl_collapse,
                      "mean_loss": round(pr.mean_loss, 3), "recent_slope": round(float(pr.recent_slope), 3)
                      if np.isfinite(pr.recent_slope) else None},
        )
    return RegimeConditionalReport(assumption_id, "structural", by_regime, current_regime,
                                   notes=[f"regimes={sorted(by_regime)}"])


# ---------------------------------------------------------------------------
# hysteresis AND-gate — ChangeRequest 승격 조건 (claude A-2)
# ---------------------------------------------------------------------------

@dataclass
class AndGateResult:
    promote: bool
    conditions: dict[str, bool]        # 각 조건 pass/fail = 감사가능 "변경 사유서"
    reason: str


def hysteresis_and_gate(
    *,
    fdr_significant: bool,             # online-FDR 유의 (T3 가 LordPlusPlus 스트림으로 산출해 주입)
    effect_size: float,                # 효과크기 (Cohen's d 류)
    effect_threshold: float = 0.5,     # gemini: Cohen's d > 0.5 (중간 이상)
    dwell_ok: bool,                    # 최소 유지기간 경과 (consensus.hysteresis)
    k_window_persist: int,             # 비중첩 K 윈도우 연속 기각 신호
    k_window_required: int = 2,
    same_regime: bool,                 # 신호가 동일 regime 내 (claude A-2 / consensus R7)
    is_base_layer: bool = False,       # ★ base-layer 가정(regime 모델 등) = 자동변경 금지
    falsifiable: bool = True,          # R15 §1.8 검정력 게이트 (False=unfalsified 보호관찰, 승격 차단)
) -> AndGateResult:
    """ChangeRequest 승격 = AND 게이트. base-layer 가정은 자동승격 불가(사람 비준, C-meta).
    R15 §1.8: falsifiable=False(검정력 미달)면 형식상 유의해도 승격 차단 — power 없는 기각은
    노이즈 추격. ic_power_gate(...).falsifiable 을 주입한다."""
    cond = {
        "fdr_significant": bool(fdr_significant),
        "effect_material": bool(effect_size >= effect_threshold),
        "dwell_ok": bool(dwell_ok),
        "k_window_persist": bool(k_window_persist >= k_window_required),
        "same_regime": bool(same_regime),
        "falsifiable": bool(falsifiable),
    }
    all_pass = all(cond.values())
    if is_base_layer:
        return AndGateResult(False, cond,
                             "base-layer 가정(regime 등) = 자동변경 금지 → 사람 비준 필수 (C-meta)")
    if all_pass:
        return AndGateResult(True, cond, "5조건 AND 통과 → ChangeRequest 승격 (감사 사유서 보유)")
    failed = [k for k, v in cond.items() if not v]
    return AndGateResult(False, cond, f"미통과 조건: {failed} → 승격 차단(노이즈 추격 방지)")


# ---------------------------------------------------------------------------
# 신뢰도 → band → 사이징 (claude C / gemini C-2)
# ---------------------------------------------------------------------------

def confidence_to_band(point: float, confidence: float, base_halfwidth: float) -> tuple[float, float]:
    """threshold 를 점추정 아닌 band 로. 신뢰도 낮을수록 넓은 band (정보 보존)."""
    conf = float(np.clip(confidence, 0.01, 1.0))
    halfwidth = base_halfwidth / conf           # 신뢰도 0.5 → 2배 넓이
    return (point - halfwidth, point + halfwidth)


def band_to_size_multiplier(band_halfwidth: float, ref_halfwidth: float,
                            abstain_ratio: float = 3.0) -> float:
    """band 넓이 → 베팅규모 배수 0..1 (fractional Kelly 페널티). 너무 넓으면 abstain(0)."""
    if ref_halfwidth <= 0:
        return 1.0
    ratio = band_halfwidth / ref_halfwidth
    if ratio >= abstain_ratio:
        return 0.0                              # 신뢰도 너무 낮음 → abstain
    return float(np.clip(1.0 / ratio, 0.0, 1.0))


if __name__ == "__main__":
    rng = np.random.default_rng(11)

    # 1) parametric: regime 0 안정(가정 성립) / regime 1 평균이동(가정 깸) — 레짐별 분리
    n = 80
    reg = np.array([0] * n + [1] * n)
    r0 = rng.normal(15.0, 1.0, n)               # 가정값 15 근처
    r1 = rng.normal(19.0, 1.0, n)               # 19 로 이동 = 가정 깸
    rep = validate_parametric("semi_normal_mult", assumed_value=15.0,
                              realized=np.concatenate([r0, r1]), regime_ids=reg,
                              current_regime=0, sd=1.0)
    print(f"1) parametric: regime0 holds={rep.by_regime[0].holds} / regime1 holds={rep.by_regime[1].holds}")
    assert rep.by_regime[0].holds and not rep.by_regime[1].holds
    print(f"   holds_now(regime0)={rep.holds_now} conf={rep.confidence_now:.2f}")

    # 2) structural: 메커니즘 작동(예측 OK) → holds
    pred = rng.normal(0, 0.3, 60); out = pred + rng.normal(0, 0.2, 60)
    reps = validate_structural("semi_per_cycle", pred, out, np.zeros(60, int), 0)
    print(f"2) structural(작동): regime0 holds={reps.by_regime[0].holds}")
    assert reps.by_regime[0].holds

    # 3) AND-gate: 일부 조건 미충족 → 차단
    g1 = hysteresis_and_gate(fdr_significant=True, effect_size=0.7, dwell_ok=True,
                             k_window_persist=2, same_regime=True)
    g2 = hysteresis_and_gate(fdr_significant=True, effect_size=0.3, dwell_ok=True,
                             k_window_persist=2, same_regime=True)   # 효과 미달
    g3 = hysteresis_and_gate(fdr_significant=True, effect_size=0.7, dwell_ok=True,
                             k_window_persist=2, same_regime=True, is_base_layer=True)
    g4 = hysteresis_and_gate(fdr_significant=True, effect_size=0.7, dwell_ok=True,
                             k_window_persist=2, same_regime=True, falsifiable=False)  # R15 검정력 미달
    print(f"3) AND-gate: 전부통과={g1.promote} / 효과미달={g2.promote}({[k for k,v in g2.conditions.items() if not v]}) / base-layer={g3.promote} / 검정력미달={g4.promote}")
    assert g1.promote and not g2.promote and not g3.promote and not g4.promote

    # 3-bis) IC 검정력 게이트 (R15 §1.8): 짧은 자기상관 IC → 비falsifiable → 승격 차단
    rng2 = np.random.default_rng(7)
    pv_short = ic_power_gate(rng2.normal(0.1, 1, 12), ref_effect=0.3)
    pv_long = ic_power_gate(rng2.normal(0.5, 1, 200), ref_effect=0.5)
    print(f"3-bis) IC power gate: short falsifiable={pv_short.falsifiable} / long falsifiable={pv_long.falsifiable}")
    assert not pv_short.falsifiable and pv_long.falsifiable

    # 4) 신뢰도→band→사이징
    lo, hi = confidence_to_band(15.0, confidence=0.5, base_halfwidth=1.0)
    mult_hi = band_to_size_multiplier(1.0, 1.0)        # 신뢰도 높음 → full
    mult_lo = band_to_size_multiplier(3.5, 1.0)        # 너무 넓음 → abstain
    print(f"4) band(conf0.5)=[{lo:.1f},{hi:.1f}] size: 정상={mult_hi:.2f} abstain={mult_lo:.2f}")
    assert hi - lo > 2.0 and mult_hi == 1.0 and mult_lo == 0.0

    print("assumption_stats self-test PASS (kind dispatch + regime-conditional + AND-gate + band)")
