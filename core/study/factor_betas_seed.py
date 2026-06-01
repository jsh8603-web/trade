"""core/study/factor_betas_seed.py — M4 거시-종목 factor 통합: cross-sleeve betas seed (골격 M4-a).

검증된 dollar/rate driver(M3 5/6 verdict)를 cross-sleeve factor 공분산(B·Λ·Bᵀ, system_priors.
factor_implied_cross_cov)의 betas 로 변환한다. ★핵심: 점추정 회귀계수를 covariance prior 로 박제하지
않는다 — 각 셀을 (β̂, SE, t, n, tier) 분포로 저장하고 James-Stein 수축으로 신뢰도에 비례해 pool 쪽으로
당긴다(자문 3R 수렴, CONSULT-DECISIONS-M4-factor-integration-20260530.md).

설계 7원칙(요약):
- 2. verdict 3-tier → confidence: validated=w 그대로 / structural=w≤w_max 캡(pool 강수축) /
     reject=pool 계산서 제외하되 노출 b=β_pool·w=0(게이트 사각지대 회피) / hold(미검증)=β_pool·w=0.
- 3. dollar β 크기 보존(sign-only 기각) — 게이트 MRC 가 크기를 먹음. 크기는 두되 confidence shrink.
- 4. idio conservation: d_i = max(σ²_total − b_iᵀΛb_i, κ·σ²_total). 수축으로 b 작아지면 residual=idio 자동 증가.
- 7. τ pooling: a priori 경제 자산군(dollar-sensitivity 행태로 묶으면 순환참조). 그룹 n<2 → grand fallback.

★seed v1 = verdict-derived(gold 만 실측 std β, 나머지는 tier+검증관 강도 표현 등급). 정밀 std β 재추출
(각 sleeve raw 재실행으로 통일 표준화)은 shadow validation 단계 TODO. James-Stein 이 어차피 noisy 셀을
pool 로 수축하므로 seed 정밀도는 shadow OOS 검증에서 보정(점진 rollout). 이 모듈은 betas/idio 만 만들고,
B·Λ·Bᵀ 합성은 system_priors.factor_implied_cross_cov 재사용. risk gate wiring 은 M5(opt-in, 범위 밖).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


# 팩터 순서 — system_priors.factor_implied_cross_cov betas 행과 일치 필수.
# ★append-only(M5 Phase A): vol(VIX) 추가. macro VIF 실측 1.00 무공선(rate/dollar/oil/credit 직교).
#   전 sleeve vol β=None=HOLD → pool 부재 → 노출 0(B·Λ·Bᵀ 0 기여=무회귀 placeholder). 어느 sleeve가
#   vol β 측정 시 pool 형성·활성(VIX↑=cyclical−defensive excess 등 contemp risk-gate 채널 예상).
# ★append-only(IC8): fx(USDKRW denomination) 추가. fx_β=measured 아니라 ★구조 denomination prior
#   (KRW 투자자가 USD-표시 자산 보유 시 환산 노출). dollar(broad TWI 가격채널)와 별 layer = 이중계상 0.
#   measured 가 아니므로 James-Stein 수축 우회(TIER_DENOMINATION) — build_seed_betas 가 β 원값 보존.
#   ★fx_β 스케일(외부자문 2모델+코드검증 수렴 B, IC8): fx_β=**절대 denomination 1.0**(USD자산 환율
#   100% 노출, 추정 β 아닌 결정론 값 — GLD 포함 full). corr_prior=magnitude FREEZE 라 fx 기여=fx_β²·Λfx
#   곱만 의미 → 절대 1.0 유지하되 _static_factor_lambda 가 fx 대각만 축소(eye fallback Λfx=0.15, 실 FRED
#   Λ면 환율 실변동성 자동)해 fx 가 corr 지배하는 것 방지. ★Λfx=0.15 근거(2026-06-02 자문+falsification
#   실측): naive (σ_fx/σ_asset)²=0.33 은 무조건부 realized KRW gold×equity corr(+0.17~0.20) 초과=over-load
#   → 직교 할인(R²=0.268→0.242 상한) + F4 target 재현(0.15→implied +0.20) 으로 0.15 확정(자문 band 하단).
#   gold full 은 KRW 환산 현실. fx_hedge="full"=전 fx_β:=0(IC10 정확 복원 토글, off byte-identical).
FACTORS = ("rate", "dollar", "oil", "credit", "vol", "fx")

# verdict tier — opus 독립 검증관(raw 재실행 provenance) 판정.
TIER_VALIDATED = "validated"      # 통계 생존(t 강건·Bonferroni). w 그대로.
TIER_STRUCTURAL = "structural"    # 비유의·방향성만(넓은 CI / n 작음). w 캡 → pool 강수축.
TIER_REJECT = "reject"            # 기각(오해석·노이즈). pool 계산서 제외, 노출=β_pool·w=0.
TIER_HOLD = "hold"                # 미검증 sleeve. pooled-prior·w=0·live hold(β=0 금지=게이트 사각지대).
TIER_DENOMINATION = "denomination"  # ★IC8 fx 전용: measured 아닌 구조 denomination prior. James-Stein
#   수축 우회(pool 무의미 — 자산 표시통화는 회귀추정 대상 아님). fx_hedge=full 이면 build 가 β:=0(환헤지).

_W_MAX_STRUCTURAL = 0.25          # structural 수축 상한(자문 0.2~0.3).
_KAPPA_IDIO = 0.15                # idio floor 비율 κ(자문 0.1~0.2): 순수 systematic 자산 없음 강제.
_BETA_ABS_CLAMP = 2.0             # |β| max clamp(단일 노이즈 loading 의 structured 분산 폭발 방지).


@dataclass(frozen=True)
class FactorCell:
    """sleeve×factor 한 셀. β̂ 점추정이 아니라 (추정치+불확실성) 분포로 저장."""
    sleeve: str
    factor: str                   # FACTORS 중 하나
    beta: Optional[float]         # standardized β̂. None = 미측정(pool/hold).
    se: Optional[float] = None    # 표준오차. None 이고 t 있으면 |β/t| 로 역산.
    t: Optional[float] = None
    n: int = 0
    tier: str = TIER_HOLD
    note: str = ""

    def std_err(self) -> Optional[float]:
        """SE 반환. 직접 SE 없으면 t-stat 에서 |β/t| 역산(자문: t→confidence)."""
        if self.se is not None:
            return float(self.se)
        if self.beta is not None and self.t not in (None, 0.0):
            return abs(float(self.beta) / float(self.t))
        return None


# a priori 경제 자산군(pooling group) — ★dollar-sensitivity 행태로 묶지 않음(순환참조).
# gold/precious = commodity 아니라 real-rate/currency 군(자문 7). 그룹 n<2 → grand fallback.
POOL_GROUP = {
    "eq_us_cyclical": "equity_risk",
    "eq_intl": "equity_risk",
    "reit": "equity_risk",
    "eq_us_defensive": "equity_risk",   # 방어주도 equity-군 노출(hold, 매매 안 함)
    "gold": "real_rate_currency",
    "commodity": "commodity_real",
}


# ===========================================================================
# SEED — M3 5/6 verdict(study-research/macro/m4-collection.md) 추출
# ===========================================================================
# ★gold = 유일 실측 std β(검증관 provenance 일치). 나머지 = tier + 검증관 강도 표현 등급(강 0.5/중 0.3/
#   약 0.1). reject(rate-up 증폭·EM idio 오해석)는 β 미신뢰 → pool 노출만. credit = M3 미측정(전부 None).
SEED_CELLS = (
    # ★IC10(a) batch multivariate measured std β 전면 교체(2026-06-01, 사용자 "측정으로 magnitude 판단").
    #   source=study-research/_factor_shadow/batch-std-beta-5sleeve.json (5f multivariate, HAC NW=5,
    #   n≈5052, 2006-01~2026-05, VIF 1.0~1.14 직교). 이전 M3 등급값(강0.5/중0.3/약0.1)·verdict-derived 폐기.
    #   ★shadow population 폐기(사용자): large-n 측정값 직접 박제(magnitude FREEZE=small-n 한정으로 좁힘).
    #   tier=batch tier_suggest. reject 셀=build_seed_betas 가 β:=0 lock. defensive=batch 미포함→HOLD(pool).
    #   ★독립 P2 audit(2026-06-01) 확정: cross-corr sign 정합(cyclical/intl/reit vol 강음=risk-off 동조).
    # --- gold (batch mv, n=5052) ---
    FactorCell("gold", "rate",   -0.2155, se=0.0179, t=-12.028, n=5052, tier=TIER_VALIDATED, note="batch mv std β"),
    FactorCell("gold", "dollar", -0.3166, se=0.0190, t=-16.675, n=5052, tier=TIER_VALIDATED, note="batch mv, dollar>rate"),
    FactorCell("gold", "oil",    +0.1209, se=0.0274, t=+4.415,  n=5052, tier=TIER_VALIDATED, note="batch mv, inflation hedge"),
    FactorCell("gold", "credit", -0.0144, se=0.0184, t=-0.780,  n=5052, tier=TIER_REJECT,    note="batch mv 비유의 p=0.44"),
    FactorCell("gold", "vol",    -0.0106, se=0.0239, t=-0.442,  n=5052, tier=TIER_REJECT,    note="batch mv 비유의 p=0.66 + 독립 audit p_NW=0.077 → β:=0 lock(decoupling/equity-vol 오염 방어)"),
    FactorCell("gold", "fx",     +1.0,  tier=TIER_DENOMINATION, note="IC8 denomination full(+1.0, GLD=USD자산 KRW 환노출 — 외부자문 2모델+코드검증 수렴). IC10 risk-off decoupling은 dollar/vol 열 보존, fx는 별 KRW 환산 레이어(동조 추가=환노출 현실). dollar β(-0.32)=가격채널 별 layer"),

    # --- eq_us_cyclical (XLB/XLI/SOXX, batch mv) ---
    FactorCell("eq_us_cyclical", "rate",   +0.1052, se=0.0162, t=+6.488,  n=5052, tier=TIER_VALIDATED,  note="batch mv, rate 통제후 양(growth, 이전 −0.07 등급 정정)"),
    FactorCell("eq_us_cyclical", "dollar", -0.1710, se=0.0172, t=-9.959,  n=5052, tier=TIER_VALIDATED,  note="batch mv(이전 −0.55 등급 정정)"),
    FactorCell("eq_us_cyclical", "oil",    +0.0363, se=0.0225, t=+1.613,  n=5052, tier=TIER_STRUCTURAL, note="batch mv 약 p=0.11"),
    FactorCell("eq_us_cyclical", "credit", -0.0037, se=0.0140, t=-0.268,  n=5052, tier=TIER_REJECT,     note="batch mv 비유의"),
    FactorCell("eq_us_cyclical", "vol",    -0.6871, se=0.0247, t=-27.859, n=5052, tier=TIER_VALIDATED,  note="batch mv, risk-off 최강"),
    FactorCell("eq_us_cyclical", "fx",     +1.0 , tier=TIER_DENOMINATION, note="IC8 denomination full(USD-표시 자산, KRW 투자자 USDKRW 환노출); 절대 denomination 1.0=KRW 환노출 full, _static_factor_lambda Λfx 축소가 corr 지배 방지(B 수렴)"),

    # --- eq_intl (EFA/EEM, batch mv) ---
    FactorCell("eq_intl", "rate",   +0.0942, se=0.0152, t=+6.206,  n=5052, tier=TIER_VALIDATED,  note="batch mv, rate 통제후 양(이전 reject 정정)"),
    FactorCell("eq_intl", "dollar", -0.2951, se=0.0178, t=-16.558, n=5052, tier=TIER_VALIDATED,  note="batch mv, Bonferroni 생존"),
    FactorCell("eq_intl", "oil",    +0.0434, se=0.0176, t=+2.463,  n=5052, tier=TIER_STRUCTURAL, note="batch mv 약 p=0.014"),
    FactorCell("eq_intl", "credit", -0.0420, se=0.0165, t=-2.542,  n=5052, tier=TIER_STRUCTURAL, note="batch mv p=0.011"),
    FactorCell("eq_intl", "vol",    -0.6414, se=0.0299, t=-21.441, n=5052, tier=TIER_VALIDATED,  note="batch mv"),
    FactorCell("eq_intl", "fx",     +1.0 , tier=TIER_DENOMINATION, note="IC8 denomination full(EFA/EEM USD-표시 ETF, KRW 환산); 절대 denomination 1.0=KRW 환노출 full, _static_factor_lambda Λfx 축소가 corr 지배 방지(B 수렴)"),

    # --- reit (VNQ, batch mv) — ★rate multivariate 비유의(univariate −0.45는 vol/dollar 공선 흡수) ---
    FactorCell("reit", "rate",   -0.0035, se=0.0213, t=-0.166,  n=5052, tier=TIER_REJECT,    note="batch mv 비유의(univariate +0.13 → vol(VIX) 단독 흡수, omitted-var 구조 corr(rate,vol)=−0.24·dollar 무관). yaml rate-duration=univariate 단일사이클 자산특성(별 unit, Phase W4 caveat)"),
    FactorCell("reit", "dollar", -0.0896, se=0.0258, t=-3.477,  n=5052, tier=TIER_VALIDATED, note="batch mv p=0.0005"),
    FactorCell("reit", "oil",    -0.0044, se=0.0242, t=-0.183,  n=5052, tier=TIER_REJECT,    note="batch mv 비유의"),
    FactorCell("reit", "credit", -0.0247, se=0.0206, t=-1.199,  n=5052, tier=TIER_REJECT,    note="batch mv 비유의"),
    FactorCell("reit", "vol",    -0.5647, se=0.0352, t=-16.025, n=5052, tier=TIER_VALIDATED, note="batch mv, risk-off 주채널"),
    FactorCell("reit", "fx",     +1.0 , tier=TIER_DENOMINATION, note="IC8 denomination full(US REIT VNQ USD-표시); 절대 denomination 1.0=KRW 환노출 full, _static_factor_lambda Λfx 축소가 corr 지배 방지(B 수렴)"),

    # --- commodity (DBC, batch mv, n=5028) ---
    FactorCell("commodity", "rate",   +0.0665, se=0.0190, t=+3.490, n=5028, tier=TIER_VALIDATED,  note="batch mv p=0.0005"),
    FactorCell("commodity", "dollar", -0.2054, se=0.0228, t=-9.027, n=5028, tier=TIER_VALIDATED,  note="batch mv"),
    FactorCell("commodity", "oil",    +0.6128, se=0.0988, t=+6.201, n=5028, tier=TIER_VALIDATED,  note="batch mv, oil 본체"),
    FactorCell("commodity", "credit", -0.0335, se=0.0168, t=-1.991, n=5028, tier=TIER_STRUCTURAL, note="batch mv p=0.046"),
    FactorCell("commodity", "vol",    -0.1408, se=0.0160, t=-8.823, n=5028, tier=TIER_VALIDATED,  note="batch mv"),
    FactorCell("commodity", "fx",     +1.0 , tier=TIER_DENOMINATION, note="IC8 denomination full(DBC USD-표시); 절대 denomination 1.0=KRW 환노출 full, _static_factor_lambda Λfx 축소가 corr 지배 방지(B 수렴)"),

    # --- eq_us_defensive (batch 미포함) — HOLD: equity_risk pool 노출(vol≈−0.63 = 독립 audit corr −0.66 정합) ---
    FactorCell("eq_us_defensive", "rate",   None, tier=TIER_HOLD, note="batch 미측정 → equity_risk pool"),
    FactorCell("eq_us_defensive", "dollar", None, tier=TIER_HOLD, note="batch 미측정 → equity_risk pool"),
    FactorCell("eq_us_defensive", "oil",    None, tier=TIER_HOLD, note="batch 미측정"),
    FactorCell("eq_us_defensive", "credit", None, tier=TIER_HOLD, note="batch 미측정"),
    FactorCell("eq_us_defensive", "vol",    None, tier=TIER_HOLD, note="batch 미측정 → equity_risk vol pool(≈−0.63, 독립 audit corr −0.66 정합)"),
    FactorCell("eq_us_defensive", "fx",     +1.0 , tier=TIER_DENOMINATION, note="IC8 denomination full(USD-표시 방어주); 구조값=측정대상 아님 → HOLD 무관 직접 부여(measured β 대역 +0.30)"),
)


@dataclass
class SeedBetas:
    """seed → James-Stein 수축 후 betas(B) + idio. system_priors.factor_implied_cross_cov 입력."""
    sleeves: list
    factors: list
    betas: dict                   # sleeve → [b_rate, b_dollar, b_oil, b_credit] (수축 후)
    idio_var: dict                # sleeve → 고유분산(conservation form)
    weights: dict                 # (sleeve,factor) → James-Stein w(진단)
    pool: dict                    # (group,factor) → β_pool(진단)


def _factor_pool(cells: list, factor: str) -> tuple:
    """factor 의 그룹별 β_pool + τ²(MoM). reject/hold 셀은 pool 계산서 제외(β_pool 오염 방지).

    ★IC3 codify(R9 오염차단 정수, group-specific fallback): **grand(cross-group) fallback 폐기**.
    이전엔 group n<2 → 전 자산 평균(grand) 상속 → gold(real_rate_currency 단독)가 equity군 dollar
    평균으로 당겨지는 −0.508/-0.408 오염 root cause. 이제 group 내 estimated 만으로 pool 산출,
    그 factor 에 estimated 셀 없는 group 은 pool 키 부재 → 호출부 fallback=β:=0(독립 보수 prior).
    n==1(group 유일 estimated)=그 자신(자기 수축=원값 보존, magnitude FREEZE 정합).
    """
    by_group: dict = {}
    for c in cells:
        if c.factor != factor or c.beta is None:
            continue
        if c.tier in (TIER_REJECT, TIER_HOLD, TIER_DENOMINATION):  # ★pool 미참여(reject/hold/denom 구조값)
            continue
        by_group.setdefault(POOL_GROUP.get(c.sleeve, "_ungrouped"), []).append(c)
    pool_beta: dict = {}
    tau2: dict = {}
    for g, gc in by_group.items():
        betas = np.array([c.beta for c in gc], dtype=float)
        ses = np.array([c.std_err() or 0.0 for c in gc], dtype=float)
        if len(betas) == 1:                         # group 유일 estimated → 자기(원값 보존)
            pool_beta[g] = float(betas[0])
            tau2[g] = max(float(ses[0] ** 2), 1e-6)
        else:                                       # group-specific 평균(grand cross-group 아님)
            pool_beta[g] = float(np.mean(betas))
            s2_between = float(np.var(betas, ddof=1))
            tau2[g] = max(s2_between - float(np.mean(ses ** 2)), 1e-6)   # MoM: max(0, S²−mean SE²)
    return pool_beta, tau2


def build_seed_betas(cells=SEED_CELLS, *, factors=FACTORS,
                     total_var: Optional[dict] = None, factor_cov=None,
                     fx_hedge: str = "none") -> SeedBetas:
    """seed 셀 → James-Stein 수축 betas + idio conservation. (CONSULT-DECISIONS-M4 원칙 2·4·7)

    total_var: sleeve → σ²_total(실현 EWMA). 없으면 idio_floor 단위(1.0)로 placeholder(self-test).
    factor_cov: Λ(F,F). idio conservation 의 b_iᵀΛb_i 계산용. 없으면 단위 대각(self-test).
    fx_hedge: ★IC8 denomination 토글. "none"(기본)=fx_β 원값(KRW 투자자 USD 환노출 그대로) /
        "full"=전 sleeve fx_β:=0(완전 환헤지 → fx factor 무기여, IC10 gold decoupling 영향 0).
    """
    cells = list(cells)
    sleeves = sorted({c.sleeve for c in cells})
    fidx = {f: i for i, f in enumerate(factors)}
    # 1) factor 별 pool/τ² (★IC3 codify: grand fallback 폐기 → group-specific 만)
    pools: dict = {}
    for f in factors:
        pb, t2 = _factor_pool(cells, f)
        pools[f] = (pb, t2)
    # 2) 셀별 James-Stein 수축
    betas = {s: [0.0] * len(factors) for s in sleeves}
    wmap: dict = {}
    pdiag: dict = {}
    cell_by = {(c.sleeve, c.factor): c for c in cells}
    for s in sleeves:
        g = POOL_GROUP.get(s, "_ungrouped")
        for f in factors:
            pb, t2 = pools[f]
            beta_pool = pb.get(g, 0.0)                       # group 없음 → β:=0 (독립 보수, grand 오염 차단)
            tau2 = t2.get(g, max(t2.values()) if t2 else 1e-6)
            pdiag[(g, f)] = beta_pool
            c = cell_by.get((s, f))
            if c is not None and c.beta is not None and c.tier == TIER_REJECT:
                # ★IC3 codify(R9 #1): reject=가설상 무관 확정 → β:=0 lock. group pool 노출도 차단
                # (eq_intl rate-up 증폭 기각 셀이 equity_risk rate 평균을 거짓 상속하던 오염 제거).
                b = 0.0
                w = 0.0
            elif c is not None and c.tier == TIER_DENOMINATION:
                # ★IC8: 구조 denomination prior — James-Stein/pool 우회(β 원값 보존, 회귀추정 대상 아님).
                # fx_hedge="full" → β:=0(완전 환헤지=fx factor 무기여). measured 셀과 다른 layer.
                b = 0.0 if fx_hedge == "full" else float(c.beta)
                w = 1.0   # 진단: 수축 안 함 표식
            elif c is None or c.beta is None or c.tier == TIER_HOLD:
                # missing/hold → group-specific fallback(없으면 0). 미측정의 동일 경제군 추정
                # (게이트 가시성 보존 — M4 의도 유지하되 grand cross-group 오염은 차단).
                b = beta_pool
                w = 0.0
            else:
                se = c.std_err() or 0.0
                w = tau2 / (tau2 + se ** 2) if (tau2 + se ** 2) > 0 else 0.0
                if c.tier == TIER_STRUCTURAL:
                    w = min(w, _W_MAX_STRUCTURAL)            # pool 강수축
                b = w * c.beta + (1.0 - w) * beta_pool
            b = float(np.clip(b, -_BETA_ABS_CLAMP, _BETA_ABS_CLAMP))   # |β| clamp
            betas[s][fidx[f]] = b
            wmap[(s, f)] = float(w)
    # 3) idio conservation: d_i = max(σ²_total − b_iᵀΛb_i, κ·σ²_total)
    F = len(factors)
    Lam = np.eye(F) * 0.02 if factor_cov is None else np.asarray(factor_cov, dtype=float)
    idio: dict = {}
    for s in sleeves:
        sig2 = float(total_var.get(s, 1.0)) if total_var else 1.0
        b = np.asarray(betas[s], dtype=float)
        explained = float(b @ Lam @ b)
        idio[s] = max(sig2 - explained, _KAPPA_IDIO * sig2)
    return SeedBetas(sleeves=sleeves, factors=list(factors),
                     betas=betas, idio_var=idio, weights=wmap, pool=pdiag)


# ===========================================================================
# self-test
# ===========================================================================
if __name__ == "__main__":
    from core.study.system_priors import factor_implied_cross_cov

    sb = build_seed_betas()
    fi = {f: i for i, f in enumerate(sb.factors)}
    di = fi["dollar"]

    # 1) 수축된 dollar 노출: 위험자산(eq/gold/reit/commodity) 전부 음(-) — dollar 강세=동반하락 구조
    for s in ("gold", "eq_us_cyclical", "eq_intl", "reit", "commodity"):
        assert sb.betas[s][di] < 0, f"{s} dollar 노출이 음이 아님: {sb.betas[s][di]}"
    print(f"1) dollar 음노출 전 sleeve OK: " +
          " ".join(f"{s}={sb.betas[s][di]:+.3f}" for s in
                   ("gold", "eq_us_cyclical", "eq_intl", "reit", "commodity")))

    # 2) validated(gold dollar) 는 수축 약함, structural(commodity dollar)·hold 는 강수축/노출만
    # measured: gold/commodity 둘 다 group 단독 validated(w=0.5 자기수축). validated vs structural 비교는
    # equity_risk 군 내에서(dollar=validated pool 복수 → 덜 수축 / oil=structural 캡). hold=defensive w=0.
    w_cyc_dollar = sb.weights[("eq_us_cyclical", "dollar")]   # validated, equity_risk pool
    w_cyc_oil = sb.weights[("eq_us_cyclical", "oil")]          # structural, 캡
    w_def = sb.weights[("eq_us_defensive", "dollar")]          # hold
    assert w_cyc_dollar > w_cyc_oil, f"validated({w_cyc_dollar}) 가 structural({w_cyc_oil}) 보다 덜 수축해야"
    assert w_cyc_oil <= _W_MAX_STRUCTURAL + 1e-9, f"structural w 캡 위반: {w_cyc_oil}"
    assert w_def == 0.0, f"hold sleeve w=0 이어야: {w_def}"
    print(f"2) tier 수축 OK: eq_us_cyclical dollar(validated) w={w_cyc_dollar:.3f} > oil(structural) w={w_cyc_oil:.3f} "
          f"/ eq_us_defensive(hold) w={w_def:.3f}")

    # 3) ★IC3 오염차단 + IC10 measured: reject=β:=0 lock. batch mv 에서 reit rate 가 reject —
    #    univariate −0.45 는 vol/dollar 공선 흡수, multivariate(직교 통제) 후 t=−0.166 비유의 → 정정.
    #    가설상 무관 확정이므로 group pool 노출도 차단(reject≠missing). hold(미측정 pool)와 구분.
    ri = fi["rate"]
    b_reit_rate = sb.betas["reit"][ri]
    w_reit_rate = sb.weights[("reit", "rate")]
    assert w_reit_rate == 0.0, f"reject w=0 이어야: {w_reit_rate}"
    assert b_reit_rate == 0.0, f"reject β:=0 lock 이어야(오염차단): {b_reit_rate}"
    print(f"3) reject β:=0 lock OK: reit rate w=0, b={b_reit_rate:+.3f}(batch mv 비유의 → 노출 0, univariate 공선 정정)")

    # 4) hold(eq_us_defensive) 가 equity_risk pool dollar 노출 받음(미검증이나 동조 가시성 유지)
    b_def_dollar = sb.betas["eq_us_defensive"][di]
    assert b_def_dollar < 0, f"방어주 pool dollar 노출 음이어야(equity_risk): {b_def_dollar}"
    print(f"4) hold pooled-prior OK: eq_us_defensive dollar={b_def_dollar:+.3f}(equity_risk pool, live hold)")

    # 5) idio conservation: 모든 sleeve idio ≥ κ·σ²(floor), 순수 systematic 없음
    for s in sb.sleeves:
        assert sb.idio_var[s] >= _KAPPA_IDIO * 1.0 - 1e-9, f"{s} idio floor 위반: {sb.idio_var[s]}"
    print(f"5) idio conservation OK: floor κ={_KAPPA_IDIO} 전 sleeve 충족")

    # 6) ★end-to-end: seed betas → factor_implied_cross_cov → PD + dollar 동조 양공분산
    Lam = np.diag([0.04, 0.05, 0.03, 0.05, 0.06, 0.02])   # rate/dollar/oil/credit/vol/fx 분산(self-test 가정)
    sb2 = build_seed_betas(factor_cov=Lam)
    res = factor_implied_cross_cov(sb2.betas, Lam, factors=list(sb2.factors), idio_var=sb2.idio_var)
    eig = np.linalg.eigvalsh(res.cov)
    assert np.all(eig > 0), f"cross-sleeve cov PD 위반: {eig}"
    i_gold = res.sleeves.index("gold")
    i_cyc = res.sleeves.index("eq_us_cyclical")
    assert res.cov[i_gold, i_cyc] > 0, "둘 다 dollar 음노출 → 양 공분산 기대"
    print(f"6) end-to-end OK: B·Λ·Bᵀ PD✓(min eig={eig.min():.5f}) "
          f"gold·eq_us_cyclical cov={res.cov[i_gold,i_cyc]:+.5f}(+, dollar 동조)")

    # 7) ★IC10(a) vol(VIX) measured: equity/commodity sleeve vol 강음(risk-off 공통인자). gold vol=
    #    reject(β:=0 lock, batch+audit 비유의). defensive(hold)=equity_risk vol pool 노출(audit corr −0.66 정합).
    #    ★L축: vol 공통인자는 SEED vol factor 1회만 계상(VIX-regime 별도 wire 금지, 독립 audit 가드).
    assert "vol" in sb.factors and len(sb.factors) == 6, f"vol append 실패: {sb.factors}"
    vi = fi["vol"]
    for s in ("eq_us_cyclical", "eq_intl", "reit", "commodity"):
        assert sb.betas[s][vi] < 0, f"{s} vol 음노출(risk-off) 이어야: {sb.betas[s][vi]}"
    assert sb.betas["gold"][vi] == 0.0, f"gold vol=reject β:=0 lock 이어야: {sb.betas['gold'][vi]}"
    b_def_vol = sb.betas["eq_us_defensive"][vi]
    assert b_def_vol < 0, f"defensive(hold) equity_risk vol pool 노출 음 이어야: {b_def_vol}"
    print(f"7) vol measured OK: equity vol 음노출(cyclical={sb.betas['eq_us_cyclical'][vi]:+.3f}) / "
          f"gold vol β:=0(reject) / defensive pool={b_def_vol:+.3f}(equity_risk, audit corr −0.66 정합)")

    # 8) ★IC8 fx denomination: USD-표시 자산 fx_β=원값 보존(James-Stein 우회) / gold=부분(+0.3) /
    #    fx_hedge="full" → 전 sleeve fx_β:=0(완전 환헤지). measured 셀과 다른 layer(회귀추정 대상 아님).
    assert "fx" in sb.factors and len(sb.factors) == 6, f"fx append 실패: {sb.factors}"
    xi = fi["fx"]
    assert abs(sb.betas["eq_us_cyclical"][xi] - 1.0) < 1e-9, f"USD자산 fx_β=+1.0 절대 denomination 실패: {sb.betas['eq_us_cyclical'][xi]}"
    assert abs(sb.betas["gold"][xi] - 1.0) < 1e-9, f"gold fx_β=+1.0(GLD=USD자산 full denomination) 실패: {sb.betas['gold'][xi]}"
    assert sb.weights[("eq_us_cyclical", "fx")] == 1.0, "denomination w=1(수축 우회) 이어야"
    sb_hedge = build_seed_betas(fx_hedge="full")
    assert all(sb_hedge.betas[s][xi] == 0.0 for s in sb_hedge.sleeves), "fx_hedge=full 시 전 fx_β=0 이어야"
    print(f"8) fx denomination OK: 전 USD자산 fx_β=+1.0(절대 denomination, GLD 포함 KRW 환노출 full) / "
          f"hedge=full→전 sleeve 0(환헤지). Λfx 축소(_static_factor_lambda eye fallback 0.15)가 corr 지배 방지")

    # 9) ★gold decoupling 측정(fx 영향): fx_hedge none vs full 비교. gold full(+1.0, GLD=USD자산)이나
    #    Λfx 작아(self-test 0.02 / 런타임 eye fallback 0.15) fx_β²·Λfx 곱 작음 → Δcorr<0.25 게이트.
    #    IC10 risk-off decoupling 은 dollar/vol 열에 보존, fx 는 별 KRW 환산 레이어(동조 추가는 환노출 현실).
    Lam6 = np.diag([0.04, 0.05, 0.03, 0.05, 0.06, 0.02])
    sb_n = build_seed_betas(factor_cov=Lam6, fx_hedge="none")
    sb_f = build_seed_betas(factor_cov=Lam6, fx_hedge="full")
    res_n = factor_implied_cross_cov(sb_n.betas, Lam6, factors=list(sb_n.factors), idio_var=sb_n.idio_var)
    res_f = factor_implied_cross_cov(sb_f.betas, Lam6, factors=list(sb_f.factors), idio_var=sb_f.idio_var)
    ig2, ic2 = res_n.sleeves.index("gold"), res_n.sleeves.index("eq_us_cyclical")

    def _corr(res, i, j):
        d = np.sqrt(np.diag(res.cov))
        return float(res.cov[i, j] / (d[i] * d[j]))
    corr_n = _corr(res_n, ig2, ic2)
    corr_f = _corr(res_f, ig2, ic2)
    assert corr_n - corr_f < 0.25, f"fx 가 gold decoupling 과훼손(Δcorr={corr_n-corr_f:.3f} ≥ 0.25) → gold fx_β 축소 필요"
    print(f"9) gold decoupling 보호 OK: gold×eq_us_cyclical corr none={corr_n:+.4f} / hedge-full={corr_f:+.4f} "
          f"(Δ={corr_n-corr_f:+.4f} < 0.25 게이트)")

    print("\nfactor_betas_seed self-test PASS "
          "(James-Stein 수축 + verdict tier(validated/structural/reject/hold) + idio conservation "
          "+ a priori pool + end-to-end cross-sleeve cov PD)")
