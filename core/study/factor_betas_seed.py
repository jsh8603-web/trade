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
# ★append-only(M5 Phase A): vol(VIX) 추가. macro VIF 실측 1.00 무공선.
#   gold vol β=reject(§3, p=0.077 비유의 → β:=0 lock, decoupling 방어). equity/commod vol 강음(risk-off).
# ★Y5 factor codify(2026-06-02): rate(명목 DGS10)→**real(DFII10) 교체** + **breakeven(T5YIE) 추가**.
#   근거: P2 독립 audit 가 real/breakeven/MOVE/slope 4축 adopted 판정 → 통일 8-factor joint multivariate
#   재측정(batch-std-beta-9factor, n≈5000, MAX VIF 1.26 무공선) + 외부자문 2모델(gemini/claude) 만장일치.
#   ★핵심 발견: audit 헤드라인 β 는 **univariate** 였고, VIX 동시통제(joint) 시 MOVE/slope β→0 으로 붕괴
#     (VIX 가 risk-off 분산 완전 흡수). factor 공분산 prior(B·Λ·Bᵀ)는 joint β 가 정합 — univariate 박으면
#     VIX 와 risk-off 채널 ★이중계상(L축 불변식 위반). univariate inflation (1+3ρ²)는 sleeve 별로 달라
#     magnitude FREEZE/cov2corr 로도 못 씻음(상대 corr 까지 왜곡, Claude 미니증명). → ★MOVE/slope DROP.
#   ★re-scope(번복 아님): audit verdict=marginal association(유효, ledger §6 보존) / covariance-incremental
#     =rejected(VIX 조건부 redundant, FWL=joint β 가 이미 잔차계수, VIF 1.26 → MOVE⊥ 분산 79% 보존=진짜
#     partialling). 채택 게이트 업그레이드: covariance-prior factor 는 univariate screen 만으로 부족, joint
#     incremental 통과 필수. → cross-regime-ledger.md §6 Y5-reconcile.
#   real: gold/bond 만 adopt(equity 양상관 OOS sign-flip 재현 → reject). gold real −0.233(명목 rate −0.2155
#     재현대). breakeven: commod 만 adopt(joint +0.117 t=3.1 유의, univariate +0.33 → 약화하나 생존).
# ★append-only(IC8): fx(USDKRW denomination). fx_β=measured 아니라 ★구조 denomination prior(KRW 투자자가
#   USD-표시 자산 보유 시 환산 노출). dollar(broad TWI 가격채널)와 별 layer = 이중계상 0. James-Stein 우회
#   (TIER_DENOMINATION). fx_β=절대 1.0(추정 아닌 결정론, GLD 포함 full). corr_prior=magnitude FREEZE 라
#   fx 기여=fx_β²·Λfx 곱만 의미 → _static_factor_lambda eye fallback Λfx=0.15(자문 2모델 band 하단 +
#   falsification 실측: naive 0.33=realized KRW gold×eq +0.17~0.20 초과 over-load → 직교할인 0.242 상한,
#   F4 target 재현 0.15→implied +0.20). fx_hedge="full"=전 fx_β:=0(IC10 정확 복원 토글, off byte-identical).
FACTORS = ("real", "dollar", "oil", "credit", "vol", "breakeven", "fx")

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
    # ★Y5 codify(2026-06-02) 통일 8-factor joint multivariate 재측정 전면 교체.
    #   source=study-research/_factor_shadow/batch-std-beta-9factor.json (real/dollar/oil/credit/vol/move/
    #   breakeven/slope 8f multivariate, HAC NW=5, n≈5000, 2006-01~2026-05, MAX VIF 1.26 무공선).
    #   ★rate→real(DFII10) 교체 + breakeven 추가. MOVE/slope=joint β→0 붕괴(VIX 흡수)로 ★DROP(자문 2모델
    #   만장일치, factor set 미포함). gold dollar/oil 기존 batch(−0.3166/+0.1209) ±0.02 재현=방법 신뢰 게이트.
    #   tier=joint tier_suggest. reject 셀=build_seed_betas β:=0 lock. defensive=batch 미포함→HOLD(pool).
    # --- gold (joint mv, n=4999) ---
    FactorCell("gold", "real",      -0.2329, se=0.0212, t=-10.986, n=4999, tier=TIER_VALIDATED, note="Y5 joint mv, real(DFII10)=gold 실질금리 기회비용(명목 rate −0.2155 재현대)"),
    FactorCell("gold", "dollar",    -0.3004, se=0.0192, t=-15.641, n=4999, tier=TIER_VALIDATED, note="Y5 joint mv (기존 batch −0.3166 재현)"),
    FactorCell("gold", "oil",       +0.1079, se=0.0255, t=+4.224,  n=4999, tier=TIER_VALIDATED, note="Y5 joint mv, inflation hedge"),
    FactorCell("gold", "credit",    -0.0098, se=0.0190, t=-0.514,  n=4999, tier=TIER_REJECT,    note="Y5 joint mv 비유의"),
    FactorCell("gold", "vol",       -0.0008, se=0.0239, t=-0.033,  n=4999, tier=TIER_REJECT,    note="§3 gold vol p=0.077 비유의 → β:=0 lock(decoupling/equity-vol 오염 방어)"),
    FactorCell("gold", "breakeven", -0.0827, se=0.0246, t=-3.367,  n=4999, tier=TIER_REJECT,    note="§6 breakeven=commod only (gold joint −0.083=real 공선 ghost, 채택 set 외)"),
    FactorCell("gold", "fx",        +1.0,  tier=TIER_DENOMINATION, note="IC8 denomination full(+1.0, GLD=USD자산 KRW 환노출 — 외부자문 2모델+코드검증 수렴). decoupling은 dollar/vol 열 보존, fx는 별 KRW 환산 레이어. dollar β(-0.30)=가격채널 별 layer"),

    # --- eq_us_cyclical (XLB/XLI/SOXX, joint mv) ---
    FactorCell("eq_us_cyclical", "real",      +0.0592, se=0.0180, t=+3.294,  n=4999, tier=TIER_REJECT,     note="§6 real=bond/gold only — equity 양상관 OOS sign-flip 재현 → reject(in-sample 유의해도 채택 set 외)"),
    FactorCell("eq_us_cyclical", "dollar",    -0.1663, se=0.0164, t=-10.155, n=4999, tier=TIER_VALIDATED,  note="Y5 joint mv"),
    FactorCell("eq_us_cyclical", "oil",       +0.0366, se=0.0243, t=+1.505,  n=4999, tier=TIER_REJECT,     note="Y5 joint mv 비유의(t=1.5, real/MOVE 추가 통제후 약화)"),
    FactorCell("eq_us_cyclical", "credit",    -0.0056, se=0.0138, t=-0.402,  n=4999, tier=TIER_REJECT,     note="Y5 joint mv 비유의"),
    FactorCell("eq_us_cyclical", "vol",       -0.6978, se=0.0276, t=-25.316, n=4999, tier=TIER_VALIDATED,  note="Y5 joint mv, risk-off 최강"),
    FactorCell("eq_us_cyclical", "breakeven", +0.0552, se=0.0275, t=+2.009,  n=4999, tier=TIER_REJECT,     note="§6 breakeven=commod only"),
    FactorCell("eq_us_cyclical", "fx",        +1.0 , tier=TIER_DENOMINATION, note="IC8 denomination full(USD-표시 자산, KRW 투자자 USDKRW 환노출); Λfx 축소가 corr 지배 방지"),

    # --- eq_intl (EFA/EEM, joint mv) ---
    FactorCell("eq_intl", "real",      +0.0777, se=0.0162, t=+4.786,  n=4999, tier=TIER_REJECT,     note="§6 real=bond/gold only — equity OOS sign-flip → reject"),
    FactorCell("eq_intl", "dollar",    -0.2965, se=0.0167, t=-17.707, n=4999, tier=TIER_VALIDATED,  note="Y5 joint mv, Bonferroni 생존"),
    FactorCell("eq_intl", "oil",       +0.0473, se=0.0195, t=+2.421,  n=4999, tier=TIER_STRUCTURAL, note="Y5 joint mv 약 p=0.016"),
    FactorCell("eq_intl", "credit",    -0.0443, se=0.0165, t=-2.689,  n=4999, tier=TIER_STRUCTURAL, note="Y5 joint mv p=0.007"),
    FactorCell("eq_intl", "vol",       -0.6476, se=0.0326, t=-19.844, n=4999, tier=TIER_VALIDATED,  note="Y5 joint mv"),
    FactorCell("eq_intl", "breakeven", +0.0423, se=0.0274, t=+1.547,  n=4999, tier=TIER_REJECT,     note="§6 breakeven=commod only"),
    FactorCell("eq_intl", "fx",        +1.0 , tier=TIER_DENOMINATION, note="IC8 denomination full(EFA/EEM USD-표시 ETF, KRW 환산); Λfx 축소가 corr 지배 방지"),

    # --- reit (VNQ, joint mv) ---
    FactorCell("reit", "real",      -0.0161, se=0.0254, t=-0.636,  n=4999, tier=TIER_REJECT,    note="§6 real=bond/gold only; joint 비유의"),
    FactorCell("reit", "dollar",    -0.0998, se=0.0255, t=-3.922,  n=4999, tier=TIER_VALIDATED, note="Y5 joint mv p=0.0001"),
    FactorCell("reit", "oil",       +0.0081, se=0.0271, t=+0.298,  n=4999, tier=TIER_REJECT,    note="Y5 joint mv 비유의"),
    FactorCell("reit", "credit",    -0.0281, se=0.0211, t=-1.330,  n=4999, tier=TIER_REJECT,    note="Y5 joint mv 비유의"),
    FactorCell("reit", "vol",       -0.5827, se=0.0388, t=-15.033, n=4999, tier=TIER_VALIDATED, note="Y5 joint mv, risk-off 주채널"),
    FactorCell("reit", "breakeven", -0.0559, se=0.0519, t=-1.078,  n=4999, tier=TIER_REJECT,    note="§6 breakeven=commod only; joint 비유의"),
    FactorCell("reit", "fx",        +1.0 , tier=TIER_DENOMINATION, note="IC8 denomination full(US REIT VNQ USD-표시); Λfx 축소가 corr 지배 방지"),

    # --- commodity (DBC, joint mv, n=4975) ---
    FactorCell("commodity", "real",      -0.0034, se=0.0143, t=-0.240, n=4975, tier=TIER_REJECT,     note="§6 real=bond/gold only; commod joint 비유의"),
    FactorCell("commodity", "dollar",    -0.1885, se=0.0206, t=-9.160, n=4975, tier=TIER_VALIDATED,  note="Y5 joint mv"),
    FactorCell("commodity", "oil",       +0.5968, se=0.0983, t=+6.069, n=4975, tier=TIER_VALIDATED,  note="Y5 joint mv, oil 본체"),
    FactorCell("commodity", "credit",    -0.0333, se=0.0176, t=-1.893, n=4975, tier=TIER_STRUCTURAL, note="Y5 joint mv p=0.058"),
    FactorCell("commodity", "vol",       -0.1530, se=0.0181, t=-8.462, n=4975, tier=TIER_VALIDATED,  note="Y5 joint mv"),
    FactorCell("commodity", "breakeven", +0.1165, se=0.0372, t=+3.129, n=4975, tier=TIER_STRUCTURAL, note="§6 commod adopt. Y5 joint +0.117 t=3.1 유의(univariate +0.33 → joint 약화하나 생존). p=0.0018>Bonferroni α/40 → structural(James-Stein 강수축)"),
    FactorCell("commodity", "fx",        +1.0 , tier=TIER_DENOMINATION, note="IC8 denomination full(DBC USD-표시); Λfx 축소가 corr 지배 방지"),

    # --- eq_us_defensive (batch 미포함) — HOLD: equity_risk pool 노출(vol≈−0.63 = 독립 audit corr −0.66 정합) ---
    FactorCell("eq_us_defensive", "real",      None, tier=TIER_HOLD, note="batch 미측정 → equity_risk pool(real=gold/bond only 라 equity pool 노출도 작음)"),
    FactorCell("eq_us_defensive", "dollar",    None, tier=TIER_HOLD, note="batch 미측정 → equity_risk pool"),
    FactorCell("eq_us_defensive", "oil",       None, tier=TIER_HOLD, note="batch 미측정"),
    FactorCell("eq_us_defensive", "credit",    None, tier=TIER_HOLD, note="batch 미측정"),
    FactorCell("eq_us_defensive", "vol",       None, tier=TIER_HOLD, note="batch 미측정 → equity_risk vol pool(≈−0.63, 독립 audit corr −0.66 정합)"),
    FactorCell("eq_us_defensive", "breakeven", None, tier=TIER_HOLD, note="batch 미측정"),
    FactorCell("eq_us_defensive", "fx",        +1.0 , tier=TIER_DENOMINATION, note="IC8 denomination full(USD-표시 방어주); 구조값=측정대상 아님 → HOLD 무관 직접 부여"),
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

    # 2) validated 는 수축 약함, structural 은 강수축(캡), hold 는 노출만. eq_intl 군 내에서 비교
    #    (dollar=validated 복수 pool → 덜 수축 / oil=structural 캡). hold=defensive w=0.
    w_intl_dollar = sb.weights[("eq_intl", "dollar")]   # validated, equity_risk pool
    w_intl_oil = sb.weights[("eq_intl", "oil")]          # structural, 캡
    w_def = sb.weights[("eq_us_defensive", "dollar")]    # hold
    assert w_intl_dollar > w_intl_oil, f"validated({w_intl_dollar}) 가 structural({w_intl_oil}) 보다 덜 수축해야"
    assert w_intl_oil <= _W_MAX_STRUCTURAL + 1e-9, f"structural w 캡 위반: {w_intl_oil}"
    assert w_def == 0.0, f"hold sleeve w=0 이어야: {w_def}"
    print(f"2) tier 수축 OK: eq_intl dollar(validated) w={w_intl_dollar:.3f} > oil(structural) w={w_intl_oil:.3f} "
          f"/ eq_us_defensive(hold) w={w_def:.3f}")

    # 3) ★IC3 오염차단: reject=β:=0 lock(group pool 노출도 차단, reject≠missing). reit oil 가 reject(Y5
    #    joint 비유의 t=0.30) — equity_risk oil pool(eq_intl oil structural +0.047)이 존재하나 reject 라
    #    그 pool 을 ★안 빌리고 β:=0. hold(미측정 → pool 빌림)와 구분되는 핵심 케이스.
    oi = fi["oil"]
    b_reit_oil = sb.betas["reit"][oi]
    w_reit_oil = sb.weights[("reit", "oil")]
    assert w_reit_oil == 0.0, f"reject w=0 이어야: {w_reit_oil}"
    assert b_reit_oil == 0.0, f"reject β:=0 lock 이어야(equity_risk oil pool 안 빌림): {b_reit_oil}"
    print(f"3) reject β:=0 lock OK: reit oil w=0, b={b_reit_oil:+.3f}(joint 비유의 → 노출 0, oil pool 미상속)")

    # 4) hold(eq_us_defensive) 가 equity_risk pool dollar 노출 받음(미검증이나 동조 가시성 유지)
    b_def_dollar = sb.betas["eq_us_defensive"][di]
    assert b_def_dollar < 0, f"방어주 pool dollar 노출 음이어야(equity_risk): {b_def_dollar}"
    print(f"4) hold pooled-prior OK: eq_us_defensive dollar={b_def_dollar:+.3f}(equity_risk pool, live hold)")

    # 5) idio conservation: 모든 sleeve idio ≥ κ·σ²(floor), 순수 systematic 없음
    for s in sb.sleeves:
        assert sb.idio_var[s] >= _KAPPA_IDIO * 1.0 - 1e-9, f"{s} idio floor 위반: {sb.idio_var[s]}"
    print(f"5) idio conservation OK: floor κ={_KAPPA_IDIO} 전 sleeve 충족")

    # 6) ★end-to-end: seed betas → factor_implied_cross_cov → PD + dollar 동조 양공분산
    Lam = np.diag([0.04, 0.05, 0.03, 0.05, 0.06, 0.04, 0.02])  # real/dollar/oil/credit/vol/breakeven/fx(self-test 가정)
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
    assert "vol" in sb.factors and len(sb.factors) == 7, f"vol append 실패: {sb.factors}"
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
    assert "fx" in sb.factors and len(sb.factors) == 7, f"fx append 실패: {sb.factors}"
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
    Lam6 = np.diag([0.04, 0.05, 0.03, 0.05, 0.06, 0.04, 0.02])  # 7f: real/dollar/oil/credit/vol/breakeven/fx
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
