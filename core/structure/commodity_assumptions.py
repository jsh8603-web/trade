"""core/structure/commodity_assumptions.py — BB-5: 상품/크립토 archetype 검증 통계 경로.

DESIGN-button-v2.md §7 / 자문 R1·R2·R4. archetype.py 카드(무엇을 보고 싼지)에 대응하는
**검증 통계**(그 가정이 깨졌는지 어떻게 아는가)를 제공하고, BaseAssumptionFields 카드를 발행해
AssumptionValidationEngine(BB-4) 이 holds_now → 가정별 FDR 로 소비하게 한다.

archetype ↔ 검증 통계 (자문 수렴):
- commodity_carry : convenience-yield rolling-z(현 carry 스트레치) + carry→fwd-return slope(prequential,
                    부호전환=백워데이션 프리미엄 falsified).
- seasonal        : 월더미 F-test(계절성 존재) + STL-식 seasonal-strength + OOS hit.
- inventory       : variance-ratio(Lo-MacKinlay, VR<1=평균회귀) + threshold-regression(Hansen, threshold=
                    days-of-supply) + oversupply decoupling(고재고인데 회귀 안 함=구조적 공급과잉).
                    COT 예측력 약(Sanders-Irwin) → companion 강등(검정 primary 아님).
- monetary_store  : MVRV regime-median mean-revert(AR(1) ρ<1) — realized-price cost-basis.
- speculative_flow: netflow guard = 비활성 stub(거래소 netflow=유료데이터, 프로비저닝 전 보수 band).

관측·산출만 — 결정 X. 데이터는 호출자가 주입(ledger/feature store). scipy.stats 사용(설치 확인됨),
부재 시 norm 은 numpy fallback.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from core.assume.card_contract import BaseAssumptionFields

try:
    from scipy import stats as _sps
    _HAS_SCIPY = True
except Exception:                       # pragma: no cover - scipy 부재 graceful
    _sps = None
    _HAS_SCIPY = False


# ---------------------------------------------------------------------------
# 분포 p-value seam (scipy 우선, norm 은 numpy fallback)
# ---------------------------------------------------------------------------

def _norm_sf(z: float) -> float:
    if _HAS_SCIPY:
        return float(_sps.norm.sf(z))
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def _f_sf(f: float, d1: int, d2: int) -> float:
    if _HAS_SCIPY:
        return float(_sps.f.sf(f, d1, d2))
    # numpy fallback: F → 정규근사(거칠지만 graceful). scipy 부재 시만.
    x = ((f ** (1.0 / 3.0)) * (1.0 - 2.0 / (9.0 * d2)) - (1.0 - 2.0 / (9.0 * d1)))
    denom = math.sqrt(2.0 / (9.0 * d1) + (f ** (2.0 / 3.0)) * 2.0 / (9.0 * d2))
    return _norm_sf(x / denom) if denom > 0 else 1.0


def _ols(x: np.ndarray, y: np.ndarray):
    """단순 OLS y = a + b x → (a, b, resid, ssr)."""
    X = np.column_stack([np.ones_like(x), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    return float(beta[0]), float(beta[1]), resid, float(resid @ resid)


# ---------------------------------------------------------------------------
# commodity_carry — convenience-yield z + carry→fwd-return slope
# ---------------------------------------------------------------------------

@dataclass
class CarrySlopeResult:
    slope: float                 # carry → fwd-return 회귀 기울기 (양수=백워데이션 프리미엄 성립)
    intercept: float
    t_stat: float
    p_value: float               # slope=0 검정 (작을수록 신호 유의)
    sign_flip: bool              # prequential: 최근 윈도우 기울기 부호가 전체와 반대 (가정 깸 경고)
    convenience_z: float         # 현 convenience yield rolling-z


def carry_convenience_zscore(cy: np.ndarray, window: int = 60) -> float:
    """현 convenience yield 의 rolling z (양수 클수록 carry 스트레치=현물 타이트)."""
    cy = np.asarray(cy, float)
    w = cy[-window:] if cy.size > window else cy
    sd = w.std(ddof=1) if w.size > 1 else 0.0
    return float((cy[-1] - w.mean()) / sd) if sd > 1e-12 else 0.0


def carry_forward_slope(carry: np.ndarray, fwd_ret: np.ndarray,
                        prequential_window: int = 40) -> CarrySlopeResult:
    """carry → 차기 수익률 회귀. slope>0 = 백워데이션 carry 가 수익률 예측(가정 성립).
    prequential: 최근 윈도우 기울기 부호가 전체와 반대면 sign_flip=True(프리미엄 붕괴 falsification)."""
    carry = np.asarray(carry, float); fwd_ret = np.asarray(fwd_ret, float)
    a, b, resid, ssr = _ols(carry, fwd_ret)
    n = carry.size
    dof = max(n - 2, 1)
    s2 = ssr / dof
    sxx = float(((carry - carry.mean()) ** 2).sum())
    se = math.sqrt(s2 / sxx) if sxx > 1e-12 else float("inf")
    t = b / se if se not in (0.0, float("inf")) else 0.0
    p = 2.0 * _norm_sf(abs(t))
    flip = False
    if n > prequential_window + 5:
        _, b_recent, _, _ = _ols(carry[-prequential_window:], fwd_ret[-prequential_window:])
        flip = (np.sign(b_recent) != np.sign(b)) and abs(b) > 1e-9
    return CarrySlopeResult(slope=b, intercept=a, t_stat=float(t), p_value=float(min(max(p, 1e-9), 1.0)),
                            sign_flip=bool(flip), convenience_z=carry_convenience_zscore(carry))


# ---------------------------------------------------------------------------
# seasonal — 월더미 F-test + STL-식 strength
# ---------------------------------------------------------------------------

@dataclass
class SeasonalFResult:
    f_stat: float
    p_value: float               # 계절성 부재(null) 기각용 (작을수록 계절성 유의)
    strength: float              # STL-식 [0,1] (1=강한 계절성)
    significant: bool            # p<0.05 AND strength>0.3


def seasonal_f_test(values: np.ndarray, months: np.ndarray, period: int = 12,
                    alpha: float = 0.05) -> SeasonalFResult:
    """월(phase) 더미 결합유의 F-test + 계절강도. 계절성 존재 가정의 검증."""
    values = np.asarray(values, float); months = np.asarray(months, int)
    n = values.size
    grand = values.mean()
    ssr0 = float(((values - grand) ** 2).sum())          # intercept-only
    phases = np.unique(months)
    pred = np.empty_like(values)
    for ph in phases:
        m = months == ph
        pred[m] = values[m].mean()
    ssr1 = float(((values - pred) ** 2).sum())            # phase-mean model
    k = phases.size                                       # 추정 평균 수
    d1 = max(k - 1, 1)                                    # 더미 자유도
    d2 = max(n - k, 1)
    f = ((ssr0 - ssr1) / d1) / (ssr1 / d2) if ssr1 > 1e-12 else float("inf")
    p = _f_sf(f, d1, d2)
    strength = seasonal_strength(values, months, period)
    return SeasonalFResult(f_stat=float(f), p_value=float(p), strength=float(strength),
                           significant=bool(p < alpha and strength > 0.3))


def seasonal_strength(values: np.ndarray, months: np.ndarray, period: int = 12) -> float:
    """STL-식 seasonal strength = max(0, 1 - Var(resid)/Var(detrended)). 고전 분해(numpy)."""
    values = np.asarray(values, float); months = np.asarray(months, int)
    n = values.size
    if n < period * 2:
        trend = np.full(n, values.mean())
    else:
        k = period | 1                                    # 홀수 윈도우
        pad = k // 2
        ext = np.pad(values, pad, mode="edge")
        trend = np.convolve(ext, np.ones(k) / k, mode="valid")[:n]
    detr = values - trend
    seas = np.empty_like(values)
    for ph in np.unique(months):
        m = months == ph
        seas[m] = detr[m].mean()
    resid = detr - seas
    var_detr = detr.var()
    return float(max(0.0, 1.0 - resid.var() / var_detr)) if var_detr > 1e-12 else 0.0


# ---------------------------------------------------------------------------
# inventory — variance-ratio (Lo-MacKinlay) + threshold-regression (Hansen)
# ---------------------------------------------------------------------------

@dataclass
class VarianceRatioResult:
    vr: float                    # VR(q): <1 평균회귀, =1 RW, >1 추세
    z_stat: float                # 동분산 z (VR=1 검정)
    p_value: float
    mean_reverting: bool         # VR<1 AND z<-1.96


def variance_ratio(series: np.ndarray, q: int = 5) -> VarianceRatioResult:
    """Lo-MacKinlay (1988) VR(q). series=레벨(log price/정규화 재고). VR<1 유의 = 평균회귀."""
    p = np.asarray(series, float)
    nq = p.size - 1
    if q < 2 or nq < q + 1:
        return VarianceRatioResult(1.0, 0.0, 1.0, False)
    mu = (p[-1] - p[0]) / nq
    diff1 = np.diff(p)
    sig_a = float(((diff1 - mu) ** 2).sum()) / (nq - 1)
    diffq = p[q:] - p[:-q]
    m = q * (nq - q + 1) * (1.0 - q / nq)
    sig_c = float(((diffq - q * mu) ** 2).sum()) / m if m > 0 else float("nan")
    vr = sig_c / sig_a if sig_a > 1e-15 else 1.0
    var_vr = 2.0 * (2 * q - 1) * (q - 1) / (3.0 * q * nq)
    z = (vr - 1.0) / math.sqrt(var_vr) if var_vr > 0 else 0.0
    p_val = 2.0 * _norm_sf(abs(z))
    return VarianceRatioResult(vr=float(vr), z_stat=float(z), p_value=float(min(max(p_val, 1e-9), 1.0)),
                               mean_reverting=bool(vr < 1.0 and z < -1.96))


@dataclass
class ThresholdResult:
    threshold: float             # days-of-supply 분할점 (Hansen)
    f_stat: float                # 선형 vs 임계 모형 (분할효과)
    ssr_linear: float
    ssr_threshold: float
    slope_low: float             # thr<=c 구간 기울기
    slope_high: float            # thr>c 구간 기울기
    has_threshold_effect: bool


def threshold_regression(y: np.ndarray, x: np.ndarray, thr_var: np.ndarray,
                         trim: float = 0.15) -> ThresholdResult:
    """Hansen threshold regression: y=a+b·x, 단 thr_var 의 임계 c 에서 (a,b) 가 바뀐다.
    c 그리드(분위 trim) SSR 최소화 탐색. 재고-수익률 관계의 구조 분할(oversupply 경계) 탐지."""
    y = np.asarray(y, float); x = np.asarray(x, float); thr = np.asarray(thr_var, float)
    n = y.size
    _, _, _, ssr_lin = _ols(x, y)
    qs = np.quantile(thr, [trim, 1 - trim])
    cand = np.unique(thr[(thr >= qs[0]) & (thr <= qs[1])])
    best = None
    for c in cand:
        lo = thr <= c; hi = ~lo
        if lo.sum() < 3 or hi.sum() < 3:
            continue
        _, b_lo, _, ssr_lo = _ols(x[lo], y[lo])
        _, b_hi, _, ssr_hi = _ols(x[hi], y[hi])
        ssr_t = ssr_lo + ssr_hi
        if best is None or ssr_t < best[1]:
            best = (float(c), ssr_t, b_lo, b_hi)
    if best is None:
        return ThresholdResult(float("nan"), 0.0, ssr_lin, ssr_lin, 0.0, 0.0, False)
    c, ssr_t, b_lo, b_hi = best
    d2 = max(n - 4, 1)
    f = ((ssr_lin - ssr_t) / 2.0) / (ssr_t / d2) if ssr_t > 1e-12 else 0.0
    p = _f_sf(f, 2, d2)
    return ThresholdResult(threshold=c, f_stat=float(f), ssr_linear=ssr_lin, ssr_threshold=ssr_t,
                           slope_low=b_lo, slope_high=b_hi, has_threshold_effect=bool(p < 0.05))


@dataclass
class OversupplyResult:
    normal_slope: float          # 정상 regime: 고재고→수익률 회귀 기울기 (음수=평균회귀 정상)
    oversupply_slope: float      # 공급과잉 regime 기울기 (0 근처/부호전환=decoupling)
    decoupled: bool              # 평균회귀 메커니즘 무력화


def oversupply_decoupling(inv_z: np.ndarray, fwd_ret: np.ndarray, regime_ids: np.ndarray,
                          oversupply_regime: int = 1) -> OversupplyResult:
    """고재고(inv_z↑)가 정상 regime 에선 가격 회귀(slope<0)인데 oversupply regime 에선
    decouple(slope≈0/부호전환) 되는가. inventory 카드의 oversupply value-trap 검증."""
    inv_z = np.asarray(inv_z, float); fwd_ret = np.asarray(fwd_ret, float)
    reg = np.asarray(regime_ids, int)
    norm_m = reg != oversupply_regime; over_m = reg == oversupply_regime
    _, b_norm, _, _ = _ols(inv_z[norm_m], fwd_ret[norm_m]) if norm_m.sum() >= 3 else (0, 0.0, 0, 0)
    _, b_over, _, _ = _ols(inv_z[over_m], fwd_ret[over_m]) if over_m.sum() >= 3 else (0, 0.0, 0, 0)
    decoupled = (b_norm < -1e-6) and (b_over >= 0.5 * b_norm)   # 회귀강도 절반 이하로 소멸/역전
    return OversupplyResult(normal_slope=float(b_norm), oversupply_slope=float(b_over),
                            decoupled=bool(decoupled))


# ---------------------------------------------------------------------------
# crypto — MVRV regime-median mean-revert + netflow guard stub
# ---------------------------------------------------------------------------

@dataclass
class MvrvMeanRevertResult:
    rho: float                   # AR(1) 계수 (regime-median 편차의 지속성). <1 = 평균회귀
    t_stat: float                # H0: rho=1 (단위근=회귀없음)
    p_value: float
    mean_reverting: bool         # rho<1 AND t<-1.96


def mvrv_mean_revert(mvrv: np.ndarray, regime_ids: np.ndarray) -> MvrvMeanRevertResult:
    """MVRV 가 regime-median 으로 평균회귀하는가 (BTC monetary_store cheapness 의 핵심 가정).
    편차 d_t = mvrv_t - median(regime). AR(1): d_t = rho·d_{t-1}. rho<1 유의 = 회귀(가정 성립)."""
    mvrv = np.asarray(mvrv, float); reg = np.asarray(regime_ids, int)
    med = np.empty_like(mvrv)
    for r in np.unique(reg):
        m = reg == r
        med[m] = np.median(mvrv[m])
    d = mvrv - med
    d0, d1 = d[:-1], d[1:]
    a, rho, resid, ssr = _ols(d0, d1)
    n = d0.size
    sxx = float(((d0 - d0.mean()) ** 2).sum())
    s2 = ssr / max(n - 2, 1)
    se = math.sqrt(s2 / sxx) if sxx > 1e-12 else float("inf")
    t = (rho - 1.0) / se if se not in (0.0, float("inf")) else 0.0
    p = _norm_sf(-t)             # 단측: rho<1
    return MvrvMeanRevertResult(rho=float(rho), t_stat=float(t), p_value=float(min(max(p, 1e-9), 1.0)),
                                mean_reverting=bool(rho < 1.0 and t < -1.96))


def netflow_guard(active: bool = False) -> dict:
    """거래소 netflow value-trap guard. 데이터=유료(CoinMetrics Pro 등) → 프로비저닝 전 비활성 stub.
    비활성 시 band 보수(halfwidth↑)로 안전실패(과신 금지). proxy 금지(transition 체계오류)."""
    if active:
        raise NotImplementedError("netflow guard 활성 = 유료 netflow 데이터 프로비저닝 후 구현")
    return {"active": False, "band_halfwidth_mult": 1.5,
            "reason": "exchange netflow=paid data; pre-provisioning conservative band (fail-to-attenuation)",
            "proxy_forbidden": True}


# ---------------------------------------------------------------------------
# 카드 발행 — BB-4 AssumptionValidationEngine 소비용
# ---------------------------------------------------------------------------

def build_commodity_cards() -> list[BaseAssumptionFields]:
    """상품 archetype → 검증 가능 가정 카드(falsification_metric 정합). engine.validate 가 소비."""
    return [
        BaseAssumptionFields(
            id="commodity.carry_premium_holds", kind="structural", scope="asset", domain="commodity",
            statement="백워데이션 carry 가 차기 수익률을 예측한다(carry→fwd-return slope>0)",
            falsification_metric="carry→fwd-return slope 부호전환 prequential + 2sigma 이탈"),
        BaseAssumptionFields(
            id="commodity.seasonality_present", kind="structural", scope="asset", domain="commodity",
            statement="가격에 통계적으로 유의한 계절성이 존재한다",
            falsification_metric="월더미 F-test p<0.05 + STL seasonal-strength>0.3 + 차기 OOS hit"),
        BaseAssumptionFields(
            id="commodity.inventory_mean_reverts", kind="parametric", scope="asset", domain="commodity",
            statement="정규화 재고(days-of-supply)는 평균회귀한다",
            falsification_metric="variance-ratio VR(q)<1 z<-1.96 + threshold-regression days-of-supply 분할"),
    ]


def build_crypto_cards() -> list[BaseAssumptionFields]:
    """크립토 archetype → 검증 가능 가정 카드. netflow guard 는 비활성 stub(band 보수)."""
    return [
        BaseAssumptionFields(
            id="crypto.mvrv_mean_reverts", kind="parametric", scope="asset", domain="crypto",
            statement="MVRV 는 regime-median 으로 평균회귀한다(realized-price cost-basis 지지)",
            falsification_metric="AR(1) rho<1 단위근검정 t<-1.96 + realized-price 하회 영구성"),
        BaseAssumptionFields(
            id="crypto.speculative_flow_overheat", kind="parametric", scope="asset", domain="crypto",
            statement="SOPR/funding 과열은 평균회귀하나 영구손상 guard 필요(netflow=stub)",
            falsification_metric="SOPR CUSUM 이탈 + netflow guard(비활성→band 보수)"),
    ]


if __name__ == "__main__":
    rng = np.random.default_rng(11)

    # 1) carry: 백워데이션 carry 가 fwd-return 예측(slope>0) → 가정 성립
    carry = rng.normal(0.0, 1.0, 200)
    fwd = 0.6 * carry + rng.normal(0, 0.5, 200)          # 양의 관계 주입
    cr = carry_forward_slope(carry, fwd)
    print(f"1) carry slope={cr.slope:.3f} t={cr.t_stat:.2f} p={cr.p_value:.4f} flip={cr.sign_flip}")
    assert cr.slope > 0 and cr.p_value < 0.05 and not cr.sign_flip

    # 1b) contango flip: 최근 윈도우만 부호 반대 → sign_flip True
    carry2 = rng.normal(0, 1, 200)
    fwd2 = 0.6 * carry2 + rng.normal(0, 0.4, 200)
    fwd2[-40:] = -0.7 * carry2[-40:] + rng.normal(0, 0.4, 40)   # 최근 부호전환
    cr2 = carry_forward_slope(carry2, fwd2)
    print(f"1b) contango flip: overall slope={cr2.slope:.3f} flip={cr2.sign_flip}")
    assert cr2.sign_flip

    # 2) seasonal: 월패턴 주입 → F 유의 + strength↑ / 평탄 → 미유의
    months = np.tile(np.arange(12), 12)
    seas_amp = np.sin(2 * np.pi * months / 12) * 3.0
    vals = seas_amp + rng.normal(0, 0.5, months.size)
    sf = seasonal_f_test(vals, months)
    print(f"2) seasonal F={sf.f_stat:.2f} p={sf.p_value:.4g} strength={sf.strength:.3f} sig={sf.significant}")
    assert sf.significant
    flat = rng.normal(0, 1, months.size)
    sf0 = seasonal_f_test(flat, months)
    print(f"2b) flat: F={sf0.f_stat:.2f} p={sf0.p_value:.3f} sig={sf0.significant}")
    assert not sf0.significant

    # 3) inventory variance-ratio: 평균회귀(OU) → VR<1 / 랜덤워크 → VR≈1
    n = 600
    ou = np.zeros(n)
    for t in range(1, n):
        ou[t] = 0.7 * ou[t - 1] + rng.normal(0, 1)       # AR(1) ρ=0.7 (mean-reverting)
    vr = variance_ratio(ou, q=5)
    print(f"3) VR(5)={vr.vr:.3f} z={vr.z_stat:.2f} mean_reverting={vr.mean_reverting}")
    assert vr.mean_reverting
    rw = np.cumsum(rng.normal(0, 1, n))
    vr_rw = variance_ratio(rw, q=5)
    print(f"3b) RW VR(5)={vr_rw.vr:.3f} z={vr_rw.z_stat:.2f} mean_reverting={vr_rw.mean_reverting}")
    assert not vr_rw.mean_reverting

    # 4) threshold regression: days-of-supply<c 구간과 >c 구간 기울기 상이 → 분할 탐지
    dos = rng.uniform(0, 100, 300)
    c_true = 60.0
    x = rng.normal(0, 1, 300)
    y = np.where(dos <= c_true, -0.8 * x, 0.1 * x) + rng.normal(0, 0.3, 300)
    th = threshold_regression(y, x, dos)
    print(f"4) threshold c={th.threshold:.1f} F={th.f_stat:.2f} slope_lo={th.slope_low:.2f} "
          f"slope_hi={th.slope_high:.2f} effect={th.has_threshold_effect}")
    assert th.has_threshold_effect and 40 < th.threshold < 80

    # 5) oversupply decoupling: 정상 regime 회귀(slope<0) / oversupply regime decouple(slope≈0)
    m = 400
    reg = rng.integers(0, 2, m)
    invz = rng.normal(0, 1, m)
    fr = np.where(reg == 0, -0.7 * invz, 0.02 * invz) + rng.normal(0, 0.3, m)
    od = oversupply_decoupling(invz, fr, reg, oversupply_regime=1)
    print(f"5) oversupply: normal_slope={od.normal_slope:.3f} over_slope={od.oversupply_slope:.3f} "
          f"decoupled={od.decoupled}")
    assert od.decoupled

    # 6) MVRV mean-revert: regime-median 편차 AR(1) ρ<1 → 회귀
    k = 500
    rids = (np.arange(k) // 250).astype(int)             # 2 regime
    mv = np.zeros(k)
    base = np.where(rids == 0, 1.5, 2.5)                 # regime별 median 다름
    mv[0] = base[0]
    for t in range(1, k):
        mv[t] = base[t] + 0.6 * (mv[t - 1] - base[t - 1]) + rng.normal(0, 0.1)
    mr = mvrv_mean_revert(mv, rids)
    print(f"6) MVRV rho={mr.rho:.3f} t={mr.t_stat:.2f} p={mr.p_value:.4g} mean_reverting={mr.mean_reverting}")
    assert mr.mean_reverting

    # 7) netflow guard 비활성 stub
    ng = netflow_guard(active=False)
    print(f"7) netflow guard: active={ng['active']} band_mult={ng['band_halfwidth_mult']} "
          f"proxy_forbidden={ng['proxy_forbidden']}")
    assert ng["active"] is False and ng["band_halfwidth_mult"] > 1.0 and ng["proxy_forbidden"]

    # 8) 카드 발행 → BB-4 엔진 소비 (integration smoke)
    from core.structure.assumption_validation_engine import AssumptionValidationEngine
    eng = AssumptionValidationEngine()
    cmds = build_commodity_cards(); cryp = build_crypto_cards()
    print(f"8) 발행 카드: commodity {len(cmds)} + crypto {len(cryp)} = {len(cmds)+len(cryp)}")
    # parametric 카드 1개를 엔진에 먹여 verdict 생성 확인 (재고 평균회귀)
    inv_card = [c for c in cmds if c.kind == "parametric"][0]
    reg2 = np.zeros(120, int)
    realized = rng.normal(40, 3, 120)                    # days-of-supply 안정 → holds
    verdict = eng.validate(inv_card, regime_ids=reg2, current_regime=0,
                           realized=realized, assumed_value=40.0, sd=3.0)
    print(f"   engine verdict: id={verdict.assumption_id} holds={verdict.holds_now} "
          f"fdr_sig={verdict.fdr_significant} falsifiable={verdict.falsifiable}")
    assert verdict.falsifiable and verdict.assumption_id == inv_card.id

    print("commodity_assumptions self-test PASS "
          "(carry slope/flip · seasonal F · variance-ratio · threshold · oversupply · MVRV · netflow stub · 카드발행)")
