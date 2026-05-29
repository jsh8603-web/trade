"""core/assume/weight_card.py — 가중학습(R15) 카드 + 비중 도출 + L1 합성 (CL-W, 축 A·B·C).

CONSULT-DECISIONS-weight-20260529.md §1.3·§1.4·§1.5·§1.6 (btn-Codlearn 통합 분담).

사용자 2회 명시한 누락축: "관계있는 지표를 함께 학습(조건부 상관) → 평가기준 지표 비중을
거시 국면·산업 사이클 조건부로 조절". 현 정적 구현(Investment Clock 표·정적 attenuation·
additive regime 더미)을 학습 기반 조건부 비중으로 대체하는 메타레이어의 **주입·카드화** 절반.

분담 경계:
- btn-button(core/structure): regime-conditional glasso → belief-mixed precision Ω_eff(§1.6
  cov-space mix) + IC + classifier calibration. 본 모듈은 그 산출을 **ndarray Protocol** 로
  추상화 소비(WeightLearner) — btn-button 산출 도착 전에도 완결·검증.
- btn-Inv(core/data/weight_panel): PIT 지표 패널 + 반사성 게이트(학습 입력 공급).
- 본 모듈(btn-Codlearn): WeightAssumptionCard(registry 서브타입) + derive_weights(Ω·IC+1/N+cap)
  + synthesize_l1(clamp_floor) + soft archetype membership + b(t) frozen 박제.

★3대 불변식 (자문 §1.4):
 1. 적용지점 = L1 결정론(pre-LLM·pre-agent). S_L1 = clamp_floor(Σ_i w_i(regime)·z_i).
 2. floor = 학습객체와 **분리된 primitive**(deadzone). 비중 갱신이 floor 를 못 흔든다
    → 지표별 falsifiability 보존((c)안 채택, gemini (b)안=cheapness_z 계수 직접 기각).
 3. 순서 불변식 = S_out = S_L1·∏ a_k (a_k∈[0,1]). LLM/agent 는 비중·지표벡터 비가시,
    S_L1 의 down-only attenuator 만. 천장 S_out ≤ S_L1 (judge 가 강제).

★replay (자문 §1.6·§1.7): 카드 = hash-pinned frozen. b(t)(regime soft belief)도 **결정시점
동결**(predictable convex combo = mixture e-process supermartingale 보존, lookahead 면 type-I
깨짐). Ω_eff·calibration model 은 hash 로 pin(재계산 fixture).
"""

from __future__ import annotations

import hashlib
from typing import Optional, Protocol, Sequence

import numpy as np
from pydantic import Field, field_validator

from core.assume.card_contract import BaseAssumptionFields

# 기본 상수 (자문 §1.3)
DEFAULT_WEIGHT_CAP: float = 0.40        # 단일 지표 비중 상한 (다중공선 폭주 차단)
DEFAULT_BLEND_1N: float = 0.30          # 1/N 블렌딩 비율(DeMiguel: 최적화가 1/N 에 짐 방어)
DEFAULT_L1_FLOOR: float = 0.25          # clamp_floor deadzone(학습 분리 primitive)


# ---------------------------------------------------------------------------
# btn-button 산출 추상화 (duck-typed) — conditional_correlation 도착 전 seam
# ---------------------------------------------------------------------------

class WeightLearner(Protocol):
    """regime-conditional glasso + belief-mix 산출 공급자 (btn-button conditional_correlation).

    omega_eff(regime_belief) = §1.6 cov-space mix 후 1회 역행렬 → belief-mixed precision Ω_eff.
    ic(as_of) = Grinold 정보계수 벡터(지표별 예측력). 둘 다 series 순서 = card.series_ids.
    """

    def omega_eff(self, regime_belief: Sequence[float], as_of) -> np.ndarray: ...
    def ic(self, as_of) -> np.ndarray: ...


# ---------------------------------------------------------------------------
# WeightAssumptionCard — registry 서브타입 (§1.5)
# ---------------------------------------------------------------------------

class WeightAssumptionCard(BaseAssumptionFields):
    """다중지표 비중 벡터 가정 카드. registry/validator/update_controller 동일 lifecycle.

    단일-지표 정의 카드(BaseAssumptionFields)와 **같은 표면**(AssumptionCardLike)으로 통합 —
    falsification·버전전환 S→S'·FDR 검증을 공유. kind="parametric"(비중=파라미터).

    hierarchical partial pooling(§1.5): composed_weights = w_global + δ_regime + δ_arch + δ_inter.
    각 항이 비면 0 벡터 → 소표본 자동 가법 강등(교호항 데이터 얇으면 δ_inter 부재 = 부모 수축).
    soft archetype: δ_arch 가 단일이 아니라 archetype 별 dict 면 π(membership)로 혼합.

    b(t) frozen(§1.6): belief_vector·belief_regimes 를 결정시점 동결 = replay 재현.
    """

    # --- 비중 벡터 골격 (series 순서 = replay 불변) ---
    series_ids: tuple[str, ...] = Field(default_factory=tuple)   # 지표 라벨(열, 순서 고정)
    w_global: tuple[float, ...] = Field(default_factory=tuple)   # 전역 비중(부모)
    delta_regime: tuple[float, ...] = Field(default_factory=tuple)   # regime 델타(부모로 수축)
    delta_arch: tuple[float, ...] = Field(default_factory=tuple)     # archetype 델타(hard, soft 없을 때)
    delta_arch_by_type: dict = Field(default_factory=dict)          # {archetype: δ벡터} (soft membership 용)
    delta_inter: tuple[float, ...] = Field(default_factory=tuple)   # 교호항(얇으면 빈 tuple=0 강등)

    # --- 조건부 컨텍스트 ---
    regime_id: Optional[str] = None         # 이 카드가 적용되는 regime
    archetype: Optional[str] = None         # 지배 archetype(hard 라벨, soft 면 by_type 사용)
    period: Optional[str] = None            # PIT period(recency)

    # --- 학습 메커니즘 파라미터 (§1.3) ---
    ic: tuple[float, ...] = Field(default_factory=tuple)    # Grinold 정보계수(frozen)
    cap: float = DEFAULT_WEIGHT_CAP
    blend_1n: float = DEFAULT_BLEND_1N
    floor: float = DEFAULT_L1_FLOOR         # clamp_floor primitive(학습 분리)

    # --- b(t) frozen 박제 (§1.6) ---
    belief_regimes: tuple[str, ...] = Field(default_factory=tuple)   # b(t) regime 라벨
    belief_vector: tuple[float, ...] = Field(default_factory=tuple)  # b(t) 결정시점 동결
    omega_hash: Optional[str] = None        # belief-mixed Ω_eff hash-pin(재계산 fixture)
    calibration_hash: Optional[str] = None  # classifier calibration model hash

    # --- 검정력·이차 반증 (§1.5·§1.8) ---
    n_eff: int = 0                          # effective-n(완전관측 행 수, MDE 게이트 입력)
    mde: float = 0.0                        # 사전등록 최소검출효과(검정력)
    secondary_falsification: str = ""       # ΔΩ·logdet drift > τ → re-fit(kill 아님)

    @field_validator("kind")
    @classmethod
    def _must_be_parametric(cls, v):
        if v != "parametric":
            raise ValueError("WeightAssumptionCard.kind 는 'parametric'(비중=파라미터) 고정")
        return v

    # --- 합성 ---
    def composed_weights(self, pi: Optional[dict] = None) -> np.ndarray:
        """hierarchical partial pooling 합성 비중 = w_global + δ_regime + δ_arch + δ_inter.

        soft archetype(§1.5): pi(membership {archetype: π}) 가 주어지고 delta_arch_by_type 이
        있으면 δ_arch = Σ_a π_a·δ_a. 없으면 hard delta_arch. 부재 component = 0 벡터(자동 가법 강등).
        """
        n = len(self.series_ids)
        w = np.zeros(n, dtype=float)

        def _add(vec):
            if vec is not None and len(vec):
                arr = np.asarray(vec, dtype=float)
                if arr.shape[0] != n:
                    raise ValueError(f"비중 component 길이 {arr.shape[0]} ≠ series {n}")
                return arr
            return np.zeros(n)

        w += _add(self.w_global)
        w += _add(self.delta_regime)
        # soft archetype membership 혼합 (순환·누수 차단: π 는 구조 feature 로 학습, 외부 주입)
        if pi and self.delta_arch_by_type:
            mix = np.zeros(n)
            tot = 0.0
            for a, p in pi.items():
                d = self.delta_arch_by_type.get(a)
                if d is not None and len(d):
                    mix += float(p) * np.asarray(d, dtype=float)
                    tot += float(p)
            # membership 합 정규화(∑π≠1 robust)
            w += mix / tot if tot > 1e-12 else mix
        else:
            w += _add(self.delta_arch)
        w += _add(self.delta_inter)
        return w

    def pin_hash(self) -> str:
        """frozen replay hash — 같은 카드 정의 → 같은 hash(결정 재현 단위).

        b(t)·Ω·calibration 까지 포함(자문 §1.6: replay 엔 b벡터+model/calibration hash 둘 다 pin).
        """
        h = hashlib.sha256()
        for part in (
            self.id, self.version, str(self.regime_id), str(self.archetype), str(self.period),
            ",".join(self.series_ids),
            np.asarray(self.w_global, float).tobytes() if self.w_global else b"",
            np.asarray(self.delta_regime, float).tobytes() if self.delta_regime else b"",
            np.asarray(self.delta_arch, float).tobytes() if self.delta_arch else b"",
            np.asarray(self.delta_inter, float).tobytes() if self.delta_inter else b"",
            np.asarray(self.ic, float).tobytes() if self.ic else b"",
            np.asarray(self.belief_vector, float).tobytes() if self.belief_vector else b"",
            ",".join(self.belief_regimes),
            str(self.omega_hash), str(self.calibration_hash),
            f"{self.cap}|{self.blend_1n}|{self.floor}",
        ):
            h.update(part.encode() if isinstance(part, str) else part)
        return h.hexdigest()[:16]


# ---------------------------------------------------------------------------
# 비중 도출 (§1.3) — Ω·IC(Grinold) + 1/N 블렌딩 + cap. 카드 생성/re-fit 시 호출.
# ---------------------------------------------------------------------------

def _capped_l1_normalize(w: np.ndarray, cap: float) -> np.ndarray:
    """L1=1 정규화 + |w_i|≤cap hard 동시 만족 (capped-simplex water-filling, 부호 보존).

    단순 clip→renorm 은 정규화가 cap 을 다시 깬다(고전 함정). cap 도달 항은 고정하고 남은
    질량을 자유 항에 비례 재분배 — 수렴까지 반복. cap·n < 1(불가능) 이면 best-effort
    (전 항 cap, L1<1). 강지표가 cap 에 막히면 나머지가 떠받쳐 L1=1 유지.
    """
    sign = np.sign(w)
    mag = np.abs(np.asarray(w, dtype=float)).copy()
    n = len(mag)
    if mag.sum() < 1e-12:
        return np.zeros(n)
    free = np.ones(n, dtype=bool)
    capped_total = 0.0
    for _ in range(n + 1):
        free_sum = mag[free].sum()
        remaining = 1.0 - capped_total
        if not free.any() or free_sum < 1e-12 or remaining <= 1e-12:
            break
        scaled = mag.copy()
        scaled[free] = mag[free] * (remaining / free_sum)
        newly = free & (scaled > cap)
        if not newly.any():
            mag = scaled
            break
        mag[newly] = cap
        capped_total += cap * int(newly.sum())
        free = free & ~newly
    return sign * mag


def derive_weights(
    omega_eff: np.ndarray,
    ic: np.ndarray,
    *,
    blend_1n: float = DEFAULT_BLEND_1N,
    cap: float = DEFAULT_WEIGHT_CAP,
) -> np.ndarray:
    """belief-mixed precision Ω_eff + 정보계수 IC → 비중 벡터(L1-normalized).

    자문 §1.3:
     - w ∝ Ω·IC (Grinold 최적결합): precision(역공분산) 직접 사용 — 표본 공분산 역행렬 금지.
       상관 높은 지표는 Ω 가 자동 감액(다중공선 해소).
     - 1/N 블렌딩(DeMiguel): w = blend·(1/N) + (1−blend)·w_opt — 최적화 과적합이 1/N 에 짐.
     - cap: |w_i| ≤ cap (capped-simplex projection, 재정규화가 cap 을 깨지 않음).
    부호 = IC 부호 보존(음의 예측력 지표는 음의 비중). L1 norm=1(합성 score 스케일 고정).
    """
    omega_eff = np.asarray(omega_eff, dtype=float)
    ic = np.asarray(ic, dtype=float)
    n = ic.shape[0]
    if omega_eff.shape != (n, n):
        raise ValueError(f"Ω_eff shape {omega_eff.shape} ≠ ({n},{n}) — series 정렬 불일치")

    w_opt = omega_eff @ ic                              # Grinold
    s = np.abs(w_opt).sum()
    w_opt = w_opt / s if s > 1e-12 else np.zeros(n)

    w_eq = np.sign(ic) / n                              # 1/N (부호=IC, 무정보 IC=0 → 0)
    if np.abs(w_eq).sum() < 1e-12:
        w_eq = np.ones(n) / n
    w = blend_1n * w_eq + (1.0 - blend_1n) * w_opt

    return _capped_l1_normalize(w, cap)                 # L1=1 + cap 동시 (water-filling)


# ---------------------------------------------------------------------------
# L1 합성 주입 (§1.4) — S_L1 = clamp_floor(Σ w·z). pre-LLM·pre-agent 결정론.
# ---------------------------------------------------------------------------

def clamp_floor(s: float, floor: float) -> float:
    """deadzone floor — |s| ≤ floor → 0(neutral), else floor 만큼 soft-threshold(부호 보존).

    ★floor = 학습 비중과 **분리된 비학습 primitive**. 비중 갱신이 floor 를 못 흔든다
    (자문 §1.4 (c)안: 지표별 falsifiability 보존). |s|=엣지 크기, floor 이하=진입 안 함.
    soft-threshold(LASSO 동형)로 floor 경계 불연속 점프 제거.
    """
    if abs(s) <= floor:
        return 0.0
    return float(np.sign(s) * (abs(s) - floor))


def synthesize_l1(
    z: Sequence[float],
    w: Sequence[float],
    *,
    floor: float = DEFAULT_L1_FLOOR,
) -> float:
    """S_L1 = clamp_floor(Σ_i w_i·z_i) — 학습 비중으로 합성한 L1 결정론 cheapness score.

    z = 지표별 표준화 신호(cheapness z-score 등, series 순서 = w 와 동일). w = composed_weights.
    이 S_L1 이 judge l1_size 의 입력(기존 단일 cheapness_z 대체). 결정론 = LLM/agent 이전.
    """
    z = np.asarray(z, dtype=float)
    w = np.asarray(w, dtype=float)
    if z.shape != w.shape:
        raise ValueError(f"z {z.shape} ≠ w {w.shape} — series 정렬 불일치")
    s_raw = float(np.dot(w, z))
    return clamp_floor(s_raw, floor)


def assert_ceiling_invariant(s_out: float, s_l1: float, *, tol: float = 1e-9) -> None:
    """순서 불변식(§1.4): S_out ≤ S_L1 (부호·크기). LLM/agent down-only attenuation 만 허용.

    s_out, s_l1 은 사이징 크기(≥0) 또는 동일부호 score. |s_out| ≤ |s_l1|+tol 위반 = 증폭 누수.
    """
    if abs(s_out) > abs(s_l1) + tol:
        raise AssertionError(
            f"천장 불변식 위반: |S_out|={abs(s_out):.6f} > |S_L1|={abs(s_l1):.6f} "
            "(LLM/agent 가 L1 사이징을 증폭 — down-only attenuation 만 허용)"
        )


if __name__ == "__main__":
    from datetime import date

    def _wcard(**kw):
        base = dict(
            id="weight.macro.recession", version="v1", kind="parametric",
            scope="macro", domain="macro",
            statement="침체국면 거시지표 합성비중",
            falsification_metric="합성 score OOS Rank-IC 의 anytime-valid(e-process) 붕괴 → kill",
            secondary_falsification="‖ΔΩ‖·logdet divergence > τ → re-fit(kill 아님)",
            series_ids=("yield_curve", "credit_spread", "pmi"),
        )
        base.update(kw)
        return WeightAssumptionCard(**base)

    # 1) 카드 생성 + AssumptionCardLike 통합 + frozen
    from core.assume.card_contract import assert_falsifiable, is_card_like
    c = _wcard(w_global=(0.4, 0.3, 0.3), ic=(0.05, -0.03, 0.04),
               valid_from=date(2024, 1, 1), regime_id="recession", archetype="cyclical")
    assert is_card_like(c), "WeightCard 가 AssumptionCardLike 미충족"
    assert_falsifiable(c)                              # falsification_metric 필수 통과
    try:
        c.cap = 0.9  # type: ignore
        raise AssertionError("frozen 위반")
    except (TypeError, ValueError):
        pass
    print(f"1) 카드 생성+통합 표면+frozen OK: {c.id} pin={c.pin_hash()}")

    # 2) hierarchical partial pooling — δ_inter 부재 = 자동 가법 강등(부모 수축)
    c2 = _wcard(w_global=(0.4, 0.3, 0.3), delta_regime=(0.1, -0.1, 0.0))  # δ_arch/inter 없음
    w2 = c2.composed_weights()
    assert np.allclose(w2, [0.5, 0.2, 0.3]), w2
    c2f = _wcard(w_global=(0.4, 0.3, 0.3), delta_regime=(0.1, -0.1, 0.0),
                 delta_inter=(0.05, 0.0, -0.05))
    w2f = c2f.composed_weights()
    assert np.allclose(w2f, [0.55, 0.2, 0.25]), w2f
    print(f"2) hierarchical pooling OK: 부모만={w2} / +교호항={w2f} (δ_inter 부재=가법강등)")

    # 3) ★soft archetype membership — π 혼합
    c3 = _wcard(w_global=(0.3, 0.3, 0.4),
                delta_arch_by_type={"cyclical": (0.2, 0.0, -0.2),
                                    "compounder": (-0.2, 0.2, 0.0)})
    w_cyc = c3.composed_weights(pi={"cyclical": 1.0})
    w_mix = c3.composed_weights(pi={"cyclical": 0.5, "compounder": 0.5})
    assert np.allclose(w_cyc, [0.5, 0.3, 0.2]), w_cyc
    assert np.allclose(w_mix, [0.3, 0.4, 0.3]), w_mix   # δ_arch=(0,0.1,-0.1) 혼합
    print(f"3) soft archetype OK: hard cyclical={w_cyc} / 50:50 혼합={w_mix}")

    # 4) ★derive_weights: Ω·IC Grinold — 상관 높은 지표 자동 감액 + 1/N + cap
    # 지표0,1 강상관(precision 비대각 음수 큼), 지표2 독립. IC 동일 → 상관쌍 비중↓
    omega = np.array([[2.0, -1.5, 0.0],
                      [-1.5, 2.0, 0.0],
                      [0.0, 0.0, 1.0]])
    ic = np.array([0.05, 0.05, 0.05])
    w = derive_weights(omega, ic, blend_1n=0.0, cap=1.0)   # blend 0 = 순수 Grinold
    assert abs(np.abs(w).sum() - 1.0) < 1e-9, np.abs(w).sum()
    assert w[2] > w[0] and w[2] > w[1], (w, "독립지표가 상관쌍보다 높은 비중")
    print(f"4) Grinold Ω·IC OK: 상관쌍 w={w[0]:.3f},{w[1]:.3f} < 독립 w={w[2]:.3f} (다중공선 감액)")

    # 4b) 1/N 블렌딩 — 최적화 비중을 1/N 쪽으로 당김
    w_blend = derive_weights(omega, ic, blend_1n=0.5, cap=1.0)
    spread_pure = w[2] - w[0]
    spread_blend = w_blend[2] - w_blend[0]
    assert spread_blend < spread_pure, (spread_pure, spread_blend)
    print(f"4b) 1/N 블렌딩 OK: 비중격차 순수 {spread_pure:.3f} → blend {spread_blend:.3f} (1/N 수축)")

    # 4c) cap — 단일지표 폭주 차단
    omega_skew = np.array([[5.0, 0.0, 0.0], [0.0, 0.5, 0.0], [0.0, 0.0, 0.5]])
    w_cap = derive_weights(omega_skew, np.array([0.1, 0.01, 0.01]), blend_1n=0.0, cap=0.4)
    assert np.all(np.abs(w_cap) <= 0.4 + 1e-9), w_cap
    print(f"4c) cap OK: max|w|={np.abs(w_cap).max():.3f} ≤ 0.4")

    # 5) ★synthesize_l1 + clamp_floor deadzone (학습 분리 primitive)
    w5 = np.array([0.5, 0.3, 0.2])
    z_strong = np.array([2.0, 1.5, 1.0])     # Σw·z = 1.0+0.45+0.2 = 1.65 > floor
    z_weak = np.array([0.1, 0.1, 0.1])       # Σw·z = 0.1 < floor 0.25 → neutral 0
    s_strong = synthesize_l1(z_strong, w5, floor=0.25)
    s_weak = synthesize_l1(z_weak, w5, floor=0.25)
    assert abs(s_strong - (1.65 - 0.25)) < 1e-9, s_strong   # soft-threshold
    assert s_weak == 0.0, s_weak
    print(f"5) synthesize_l1 OK: 강신호 S_L1={s_strong:.3f}(floor 차감) / 약신호={s_weak}(deadzone)")

    # 6) ★천장 불변식 — down-only attenuation 만 통과, 증폭 차단
    assert_ceiling_invariant(s_strong * 0.5, s_strong)       # a=0.5 attenuation OK
    try:
        assert_ceiling_invariant(s_strong * 1.2, s_strong)   # 증폭 = 위반
        raise AssertionError("천장 불변식이 증폭을 허용함")
    except AssertionError as e:
        assert "천장 불변식 위반" in str(e), e
    print("6) 천장 불변식 OK: attenuation(a=0.5) 통과 / 증폭(a=1.2) 차단")

    # 7) ★b(t) frozen replay — 같은 카드(belief 동결) → 같은 pin_hash(결정 재현)
    c7a = _wcard(belief_regimes=("expansion", "recession"), belief_vector=(0.3, 0.7),
                 omega_hash="ab12", calibration_hash="cd34", w_global=(0.4, 0.3, 0.3))
    c7b = _wcard(belief_regimes=("expansion", "recession"), belief_vector=(0.3, 0.7),
                 omega_hash="ab12", calibration_hash="cd34", w_global=(0.4, 0.3, 0.3))
    c7c = _wcard(belief_regimes=("expansion", "recession"), belief_vector=(0.5, 0.5),  # 다른 belief
                 omega_hash="ab12", calibration_hash="cd34", w_global=(0.4, 0.3, 0.3))
    assert c7a.pin_hash() == c7b.pin_hash(), "동일 belief = 동일 hash 여야(replay)"
    assert c7a.pin_hash() != c7c.pin_hash(), "다른 belief = 다른 hash 여야(frozen 식별)"
    print(f"7) b(t) frozen replay OK: 동결 belief 동일 hash={c7a.pin_hash()}, belief 변경 시 분기")

    # 8) kind 게이트 — parametric 강제
    try:
        _wcard(kind="structural")
        raise AssertionError("kind 게이트 미작동")
    except ValueError as e:
        assert "parametric" in str(e), e
    print("8) kind=parametric 게이트 OK")

    print("CL-W weight_card self-test PASS "
          "(카드+pooling+soft archetype+Grinold+1/N+cap+synthesize_l1+천장불변식+b(t) frozen)")
