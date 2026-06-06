"""stock/cross_sectional_selection.py — universe 횡단면 cheapness → 종목 픽 변환부.

임무 (실행 wire 갭 #1): 연구가 입증한 "peer 평균 대비 싼 종목이 forward 수익 예측"
(cyclical PBR/EV CONFIRM, defensive net_issuance PARTIAL)을 *실제 종목 선택*으로 변환한다.
= "시총 top-N universe 안에서 지표가 평균 대비 얼마나 싼지로 골고루 산다"(사용자 핵심 요구).

⛔ 이 모듈은 "무엇을 고를지(selection)"만 한다. "이게 함정인가(trap veto)"는
   stock/value_trigger.py 의 stage-2 를 재사용한다(재구현 0). risk_gate/order/go-live 무접촉.

설계 근거 (외부 자문 2R 수렴, 2026-06-04 — .consult-us-selection-layer-brief.md):
- Q1 −10% 게이트 완전 제거: value_trigger 1차게이트(가격 −10% AND)는 coin 단일종목
  dip-buy 혈통 → cross-sectional value-rank 픽을 전멸(횡보·상승 중 싼 종목 REJECT).
  selection 경로는 run_value_trigger(bypass_gate1=True) 로 stage-2 trap veto 만 적용.
- Q2 net-alpha t-cost: 미국 sleeve(STT 0) v1 = turnover band 로 충분(net-alpha deferred).
  한국 sleeve(STT 매도 0.18~0.23% 지배) wire 시 = hard net-alpha reject 신규(미구현).
- Q3 demean = sleeve 레벨(cyclical 60종 / defensive 48종). GICS L3 분할 금지
  (bucket n=3~5 → median/MAD 통계 붕괴). measured IC = traded IC 정합.
- Q4 순서: trap veto 를 selection 이전 eligibility 필터로(post-veto 면 capped-EW 비중이
  veto 시점에 깨짐). robust z = 전체 sleeve universe 로 계산(n 최대=안정) 후 veto.

코드 정합 (재사용):
- composite z 합성 = core.assume.weight_card.synthesize_l1(z, derive_weights 가중). 미주입 시 등가중.
- capped-EW cap = risk_gate(종목 10% / 섹터 30%) 안쪽. selection 은 권고 cap, 최종 강제는 risk_gate.
- trap veto = stock.value_trigger.run_value_trigger(bypass_gate1=True). FORWARD 만 실판정(H22).

미해결 가정:
- universe {ticker → metrics + market_cap} 조립은 호출자(supervisor/construction) 책임
  (fhc_adapter "targets=universe / supervisor 가 universe 로 확장" 계약과 정합).
- ADV(거래대금) 유동성 floor 는 market_cap floor 로 근사(ADV 데이터 wire 후 정밀화).
- net-alpha t-cost reject(한국 hard)는 본 v1 범위 밖(자문 미국 soft = deferred).
"""

from __future__ import annotations

import statistics
from datetime import datetime
from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

# numpy 는 robust z 벡터 연산에만. 미설치 환경 대비 statistics fallback.
try:
    import numpy as _np
except Exception:  # pragma: no cover
    _np = None


# ---------------------------------------------------------------------------
# 계약
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SelectionCandidate:
    """selection 결과 1종목. risk_gate/sizer 가 소비하는 후보."""
    ticker: str
    cheapness_z: float           # within-sleeve robust composite z (높을수록 쌈, 부호=archetype)
    market_cap: float
    rank: int                    # cheapness 순위 (1=가장 쌈)
    target_weight: float         # capped-EW 권고 비중 (risk_gate cap 안쪽)
    eligible: bool               # microcap floor + trap veto 통과
    reason: str = ""
    per_metric_z: dict = field(default_factory=dict)   # {metric: robust_z} 추적용
    # ★ETF fallback 메타 (Phase A, 자문 3R 2026-06-06, default=byte-identical):
    #   약변별 sleeve dispatch 시 RepresentativeETFSelector 가 채운다. EQUITY 경로는 default 유지
    #   → 기존 생성부(:431 keyword) 무변경 = byte-identity 보존.
    instrument_type: str = "EQUITY"               # EQUITY | ETF
    holdings_source: Optional[str] = None         # ETF look-through 출처 (risk_gate 섹터 cap 분해용)
    holdings_asof: Optional[datetime] = None       # ETF holdings PIT 시점 (max-lag 검증용)
    pre_resolved: bool = False                    # True=ranker bypass (sleeve-target 직접배정, cheapness 미산출)


@dataclass(frozen=True)
class SelectionConfig:
    """selection 파라미터 (자문 2R 확정값 default)."""
    top_k: int = 10                       # 매수 후보 수
    max_weight_single: float = 0.05       # 종목 cap 5% (risk_gate 10% 안쪽)
    max_weight_sector: float = 0.20       # 섹터 cap 20% (risk_gate 30% 안쪽)
    market_cap_floor: float = 500e6       # microcap 배제 $500M (자문 Gemini)
    winsorize_pct: float = 0.01           # group 내 1/99 winsorize (robust z 전)
    min_universe_n: int = 10              # n<10 = robust z 통계 무의미 → 경고
    # no-trade band (히스테리시스): 매수=top_k 진입 / 매도=top_k_exit 이탈까지 보유
    top_k_exit: int = 30                  # 보유 종목이 rank>top_k_exit 이탈 시에만 매도
    # ★sector-neutral demean (WIRE3 실측 추가, default off=byte-identical):
    #   multi-sector sleeve(cyclical 5 sector×12종)는 sleeve-level z 가 sector 간 valuation
    #   레벨차(financials 항상 저PBR 등)를 cheapness 로 오인 → within-sector value 신호 희석.
    #   실측(_wire3_selection_sim): sector-neutral spread 0.139(t3.22) vs sleeve 0.049(t0.87).
    #   sectors 주입 + 이 플래그 on 시 sector 내 robust demean. bucket n<min_sector_n → sleeve pool fallback.
    demean_by_sector: bool = False
    min_sector_n: int = 8                 # sector bucket n<이면 sleeve pool fallback(mega 11종 등 보호)
    # ★net-alpha t-cost 게이트 (WIRE4, default off=byte-identical, 자문 selection 2R Q2):
    #   미국(STT 0)=turnover band(top_k_exit)로 충분=soft → default off 무영향.
    #   한국(STT 매도 0.18~0.23% 지배)=net-alpha hard reject 신규 → wire 시 net_alpha_hard_reject=on + stt_sell 주입.
    #   E[alpha] = expected_alpha_scale × cheapness_z (측정 IC×수익 변환, 호출자 주입). round-trip cost =
    #   2×cost_per_side + stt_sell(매도세). net_alpha = E[alpha] − cost < 0 → 매수 부적격(hard reject).
    cost_per_side: float = 0.0008         # commission+spread half (미국 round-trip ~0.16%)
    stt_sell: float = 0.0                 # 매도 거래세 (미국 0 / 한국 0.0018~0.0023)
    expected_alpha_scale: float = 0.0     # cheapness_z(1σ) → 보유기간 E[alpha]. 0 = 게이트 비활성(추정 미주입)
    net_alpha_hard_reject: bool = False   # True + scale>0 시 net_alpha<0 종목 매수 제외 (한국 hard)
    # ★결측 펀더멘털 fill (Gi-A, 자문 R1 만장일치 2026-06-05, default off=byte-identical):
    #   "neutral"=결측 z=0(중앙) — 결측 비랜덤(부실·소형이 보고 부실)이면 매수 편향.
    #   "sector_min"=결측 z=sector present 하위 분위(missing_quantile) 강제. 점추정(-2) 회피 + 분포 보존.
    #   저결측 metric(net_iss 6%)서 과처리 bound. 고결측 metric은 호출자가 더미인자 등 별도 고려.
    missing_fill: str = "neutral"         # sector_min 시 robust_z default 분위(0.10) 적용 (12종/섹터서 ~최악 1종)


# ---------------------------------------------------------------------------
# robust z (median / MAD) — 자문 Q2 (fat-tail·부호반전 멀티플에 강건)
# ---------------------------------------------------------------------------

def robust_z(values: Sequence[float], winsorize_pct: float = 0.01,
             missing_fill: str = "neutral", missing_quantile: float = 0.10,
             sign: int = 1) -> list[float]:
    """median/MAD 기반 robust z-score. 결측(None) 처리는 missing_fill 로 제어.

    z_i = (x_i − median) / (1.4826·MAD). 1.4826 = 정규분포 MAD→σ 일치 상수.
    MAD=0(동일값 다수)이면 0 벡터. winsorize 로 극단 outlier 영향 제한.

    missing_fill (Gi-A, 자문 R1 만장일치 2026-06-05, default=byte-identical):
      "neutral"   = 결측 z=0(중앙) — 기존 동작. ★단 결측 비랜덤(부실·소형이 보고 부실)이면 매수 편향.
      "sector_min"= 결측 z = present(non-None) z 의 ★불리(안 쌈) 쪽 missing_quantile 분위 강제.
                    sign 으로 cheapness 방향 정합: sign≥0(값 高=쌈, 예 net_iss/ep)이면 raw 하위 분위,
                    sign<0(값 低=쌈, 예 PBR/EV)이면 raw 상위 분위 = sign 곱 후 항상 "안 쌈". 점추정(-2)
                    회피 + 분포 보존. _robust_z_grouped 가 sector bucket 단위 호출 → "sector 하위" 자동.
      sign: 호출자가 metric_signs[metric] 주입(default +1). missing_fill="neutral" 시 무시.
    """
    xs = [float(v) for v in values if v is not None]
    if len(xs) < 2:
        return [0.0 for _ in values]

    # winsorize (group 내 1/99 클리핑)
    if winsorize_pct > 0 and len(xs) >= 5:
        s = sorted(xs)
        lo = s[int(winsorize_pct * (len(s) - 1))]
        hi = s[int((1 - winsorize_pct) * (len(s) - 1))]
        xs_clip = [min(max(x, lo), hi) for x in xs]
    else:
        xs_clip = xs

    med = statistics.median(xs_clip)
    mad = statistics.median([abs(x - med) for x in xs_clip])
    scale = 1.4826 * mad
    if scale <= 1e-12:
        # ★자문 결함4 guard (MAD=0 silent): >50% 가 median 공유(net_issuance 0-mass 류)면 MAD=0
        #   → metric 조용히 0벡터화. IQR(→σ 1.349) fallback, 그것도 0이면 std fallback.
        s = sorted(xs_clip)
        q1 = s[int(0.25 * (len(s) - 1))]
        q3 = s[int(0.75 * (len(s) - 1))]
        iqr = q3 - q1
        scale = iqr / 1.349 if iqr > 1e-12 else 0.0
        if scale <= 1e-12:
            mean = sum(xs_clip) / len(xs_clip)
            scale = (sum((x - mean) ** 2 for x in xs_clip) / len(xs_clip)) ** 0.5
        if scale <= 1e-12:
            return [0.0 for _ in values]   # 진짜 상수 (IQR·std 모두 0)

    def _zval(v: float) -> float:
        x = min(max(float(v), lo), hi) if (winsorize_pct > 0 and len(xs) >= 5) else float(v)
        return (x - med) / scale

    # 결측 fill z 결정 (Gi-A): neutral=0(byte-identical) / sector_min=present 불리쪽 분위
    if missing_fill == "sector_min":
        present_z = sorted(_zval(v) for v in values if v is not None)
        if present_z:
            # 불리(안 쌈) 분위: sign≥0(고=쌈)→raw 하위 / sign<0(저=쌈)→raw 상위. sign 곱 후 항상 최악쪽.
            q = missing_quantile if sign >= 0 else (1.0 - missing_quantile)
            fill_z = present_z[int(q * (len(present_z) - 1))]
        else:
            fill_z = 0.0
    else:
        fill_z = 0.0

    out: list[float] = []
    for v in values:
        out.append(fill_z if v is None else _zval(v))
    return out


# ---------------------------------------------------------------------------
# sector-aware robust z (그룹 demean) — WIRE3 실측 정합용
# ---------------------------------------------------------------------------

def _robust_z_grouped(
    col: dict[str, Optional[float]],
    tickers: Sequence[str],
    sectors: Optional[dict[str, str]],
    min_sector_n: int,
    winsorize_pct: float,
    missing_fill: str = "neutral",
    sign: int = 1,
) -> dict[str, float]:
    """단일 metric 의 robust z. sectors 주입 시 sector 내에서 demean (sector-neutral).

    sector bucket 의 present(non-None) n < min_sector_n 이면 그 종목들을 sleeve pool 로 합쳐
    pool 단위 robust z (작은 bucket median/MAD 붕괴 방지, mega 11종 등 보호).
    sectors=None → 전체 universe robust z (기존 sleeve-level, byte-identical).

    missing_fill (Gi-A): sector_min 이면 각 bucket 의 present 불리쪽 분위로 결측 채움 →
    "sector 하위 분위" 자동 충족(이 함수가 bucket 단위 호출이므로). sign 으로 불리 방향 정합.
    default neutral=byte-identical.
    """
    if sectors is None:
        zs = robust_z([col.get(t) for t in tickers], winsorize_pct=winsorize_pct,
                      missing_fill=missing_fill, sign=sign)
        return {t: z for t, z in zip(tickers, zs)}

    groups: dict[str, list[str]] = {}
    for t in tickers:
        groups.setdefault(sectors.get(t, t), []).append(t)

    out: dict[str, float] = {}
    pool: list[str] = []
    for _s, cols in groups.items():
        present = sum(1 for c in cols if col.get(c) is not None)
        if present >= min_sector_n:
            zs = robust_z([col.get(c) for c in cols], winsorize_pct=winsorize_pct,
                          missing_fill=missing_fill, sign=sign)
            out.update({c: z for c, z in zip(cols, zs)})
        else:
            pool.extend(cols)
    if pool:
        zs = robust_z([col.get(c) for c in pool], winsorize_pct=winsorize_pct,
                      missing_fill=missing_fill, sign=sign)
        out.update({c: z for c, z in zip(pool, zs)})
    return out


# ---------------------------------------------------------------------------
# FWL 잔차화 — interaction 곱항을 main effect 에 직교화 (자문 수렴 2026-06-05)
# ---------------------------------------------------------------------------

def _fwl_residualize(
    prod: dict[str, float],
    z1: dict[str, float],
    z2: dict[str, float],
    tickers: Sequence[str],
) -> dict[str, float]:
    """곱항을 {1, z1, z2} 에 cross-sectional OLS 회귀 후 잔차 (FWL = main effect 직교화).

    자문 수렴(2026-06-05) + 재검증(생짜 곱항 vs op_prof corr +0.363 = double-count 실재):
    측정 DEF-2 CONFIRM 은 FWL incremental(main 통제 후 잔차)이므로 traded 곱항도 main 직교화해야
    측정-거래 1:1. numpy 부재·특이행렬·표본부족(<4) 시 원 곱항 graceful fallback.
    """
    if _np is None:
        return prod
    ts = [t for t in tickers if t in prod]
    if len(ts) < 4:
        return prod
    X = _np.array([[1.0, z1.get(t, 0.0), z2.get(t, 0.0)] for t in ts])
    y = _np.array([prod[t] for t in ts])
    try:
        beta, *_ = _np.linalg.lstsq(X, y, rcond=None)
        resid = y - X @ beta
    except Exception:  # pragma: no cover — 특이행렬 등
        return prod
    out = dict(prod)
    for t, r in zip(ts, resid):
        out[t] = float(r)
    return out


# ---------------------------------------------------------------------------
# composite z — 여러 valuation 지표를 부호 정렬 후 합성
# ---------------------------------------------------------------------------

def composite_cheapness_z(
    metric_panel: dict[str, dict[str, Optional[float]]],
    metric_signs: dict[str, int],
    *,
    weights: Optional[dict[str, float]] = None,
    winsorize_pct: float = 0.01,
    sectors: Optional[dict[str, str]] = None,
    min_sector_n: int = 8,
    interactions: Optional[Sequence[tuple[str, str, int]]] = None,
    interactions_residualize: bool = True,
    missing_fill: str = "neutral",
) -> dict[str, float]:
    """종목별 within-sleeve(또는 within-sector) robust composite cheapness z.

    metric_panel = {metric: {ticker: value}}. metric_signs = {metric: +1/−1}
      (+1 = 값 높을수록 쌈, 예 net_issuance/ep_yield / −1 = 값 낮을수록 쌈, 예 PBR/EV-EBITDA).
    부호 정렬 후(sign·z) 합성 → 높을수록 쌈(매수 우선). weights 미주입 = 등가중(자문: null 축 불추가).

    sectors 주입 시 sector 내 robust demean (sector-neutral, WIRE3 실측 = cyclical multi-sector
      신호 보존). 미주입 = 기존 sleeve-level (byte-identical). 반환 {ticker: composite_z}.

    ★interactions (WIRE3.5-Gb, default None=byte-identical): factor×factor 교호항 리스트
      [(m1, m2, sign), ...]. 선형합 composite 가 표현 못 하는 BW8 interaction 가설(DEF-2
      div_yield×op_prof CONFIRM 등)을 추가. 측정코드(_b2_*_interactions.py interaction_z) 와
      ★1:1 구조 일치 = robust_z(m1)·robust_z(m2) 곱 후 재-robust_z(sector-neutral), sign 곱.
      (측정은 cs_z[std], selection 은 robust_z[현 모듈 일관] — z 종류만 차이, 곱→재z 구조·부호 동일).
      weight key = f"{m1}*{m2}". m1/m2 가 metric_panel 에 없으면 그 항 skip(0 기여).
    """
    # 전 종목 합집합
    tickers: list[str] = sorted({t for m in metric_panel.values() for t in m})
    if not tickers:
        return {}

    raw_z: dict[str, dict[str, float]] = {}   # sign 적용 전 raw robust z (interaction 곱용)
    metric_z: dict[str, dict[str, float]] = {}
    for metric, col in metric_panel.items():
        sign = metric_signs.get(metric, 1)
        # main metric 결측에만 Gi-A fill 적용(sign=불리방향). interaction 곱항(아래)은 결측 None 부재→neutral.
        zmap = _robust_z_grouped(col, tickers, sectors, min_sector_n, winsorize_pct,
                                 missing_fill=missing_fill, sign=sign)
        raw_z[metric] = zmap
        metric_z[metric] = {t: sign * zmap.get(t, 0.0) for t in tickers}

    # ★interaction terms: z(m1)·z(m2) 곱 후 재-robust_z(sector-neutral), sign 곱 (측정코드 동형)
    inter_z: dict[str, dict[str, float]] = {}
    for (m1, m2, isign) in (interactions or []):
        if m1 not in raw_z or m2 not in raw_z:
            continue
        prod: dict[str, float] = {t: raw_z[m1].get(t, 0.0) * raw_z[m2].get(t, 0.0) for t in tickers}
        # ★FWL 잔차화 (자문 수렴 + collinearity 0.363 재검증): main 직교화 → 측정 incremental 1:1.
        if interactions_residualize:
            prod = _fwl_residualize(prod, raw_z[m1], raw_z[m2], tickers)
        izmap = _robust_z_grouped(prod, tickers, sectors, min_sector_n, winsorize_pct)
        inter_z[f"{m1}*{m2}"] = {t: isign * izmap.get(t, 0.0) for t in tickers}

    terms = list(metric_panel) + list(inter_z)
    w = weights or {m: 1.0 for m in terms}
    wsum = sum(abs(w.get(m, 0.0)) for m in terms) or 1.0

    out: dict[str, float] = {}
    for t in tickers:
        s = sum(w.get(m, 0.0) * metric_z[m].get(t, 0.0) for m in metric_panel)
        s += sum(w.get(k, 0.0) * inter_z[k].get(t, 0.0) for k in inter_z)
        out[t] = s / wsum
    return out


# ---------------------------------------------------------------------------
# selection 본체
# ---------------------------------------------------------------------------

def select_cross_sectional(
    metric_panel: dict[str, dict[str, Optional[float]]],
    market_caps: dict[str, float],
    metric_signs: dict[str, int],
    *,
    sectors: Optional[dict[str, str]] = None,
    config: SelectionConfig = SelectionConfig(),
    weights: Optional[dict[str, float]] = None,
    trap_veto: Optional[Callable[[str], bool]] = None,
    held_ranks: Optional[dict[str, int]] = None,
    interactions: Optional[Sequence[tuple[str, str, int]]] = None,
) -> list[SelectionCandidate]:
    """universe 횡단면 → top-K capped-EW 종목 픽.

    파이프라인 (자문 Q4 확정 순서):
      1. microcap floor (market_cap < floor 제외)
      2. within-sleeve robust composite z (전체 universe, n 최대=통계 안정)
      3. trap veto eligibility (trap_veto(ticker)=True → 제외, pre-selection)
      4. top-K by cheapness z ⊕ no-trade band (held_ranks 주입 시 히스테리시스)
      5. capped-EW (종목·섹터 cap, risk_gate 안쪽)

    trap_veto: ticker → is_trap(bool). value_trigger.run_value_trigger(bypass_gate1=True)
      verdict==VALUE_TRAP 을 래핑해 주입(재사용). 미주입 = veto 없음(z·cap 만).
    held_ranks: 현 보유 {ticker: 직전 rank}. no-trade band 매도 억제용. 미주입 = band 없음.

    반환 = SelectionCandidate 리스트 (eligible=True 만 target_weight>0, rank 순 정렬).
    """
    # 1. microcap floor
    universe = [t for t in market_caps if market_caps.get(t, 0.0) >= config.market_cap_floor]
    if not universe:
        return []

    # 2. composite z (floor 통과 universe 로 한정 — peer = sleeve 잔존 종목)
    #    sec_arg: demean_by_sector on + sectors 주입 시 sector-neutral demean (WIRE3 실측).
    sec_arg = sectors if (config.demean_by_sector and sectors) else None
    panel = {m: {t: col.get(t) for t in universe} for m, col in metric_panel.items()}
    z_by_ticker = composite_cheapness_z(
        panel, metric_signs, weights=weights, winsorize_pct=config.winsorize_pct,
        sectors=sec_arg, min_sector_n=config.min_sector_n, interactions=interactions,
        missing_fill=config.missing_fill,
    )
    underpowered = len(universe) < config.min_universe_n

    # per-metric z (추적) — composite 와 동일 demean 경로
    per_metric: dict[str, dict[str, float]] = {}
    for metric, col in panel.items():
        sign = metric_signs.get(metric, 1)
        zmap = _robust_z_grouped(col, universe, sec_arg, config.min_sector_n, config.winsorize_pct,
                                 missing_fill=config.missing_fill, sign=sign)
        per_metric[metric] = {t: sign * zmap.get(t, 0.0) for t in universe}

    # 싼 순 정렬 (z 높을수록 쌈)
    ranked = sorted(universe, key=lambda t: z_by_ticker.get(t, 0.0), reverse=True)
    rank_of = {t: i + 1 for i, t in enumerate(ranked)}

    # 3. trap veto + net-alpha eligibility (pre-selection)
    def _eligible(t: str) -> tuple[bool, str]:
        if trap_veto is not None:
            try:
                if trap_veto(t):
                    return False, "stage-2 VALUE_TRAP veto (bypass_gate1 경로)"
            except Exception as e:  # veto 실패 = 보수적 제외
                return False, f"trap_veto 호출 실패 → 보수적 제외: {e}"
        # ★net-alpha hard reject (WIRE4): E[alpha]=scale·z − round-trip cost < 0 → 매수 부적격.
        #   default off(미국 turnover band soft). 한국 wire 시 net_alpha_hard_reject=on + stt_sell 주입.
        if config.net_alpha_hard_reject and config.expected_alpha_scale > 0:
            e_alpha = config.expected_alpha_scale * z_by_ticker.get(t, 0.0)
            rt_cost = 2 * config.cost_per_side + config.stt_sell
            if e_alpha - rt_cost < 0:
                return False, f"net-alpha<0 (E[a]={e_alpha:+.4f} < cost={rt_cost:.4f}, STT hard reject)"
        return True, ""

    # 4. top-K ⊕ no-trade band
    selected: list[str] = []
    for t in ranked:
        ok, _ = _eligible(t)
        if not ok:
            continue
        in_buy = rank_of[t] <= config.top_k
        # 히스테리시스: 보유 중이면 top_k_exit 이탈 전까지 유지
        held = held_ranks is not None and t in held_ranks
        in_hold_band = held and rank_of[t] <= config.top_k_exit
        if in_buy or in_hold_band:
            selected.append(t)

    # 5. capped-EW (종목 cap + 섹터 cap)
    weights_out = _capped_equal_weight(
        selected, sectors or {}, config.max_weight_single, config.max_weight_sector
    )

    # 결과 조립 (전 universe, eligible/target_weight 표기)
    out: list[SelectionCandidate] = []
    for t in ranked:
        ok, why = _eligible(t)
        tw = weights_out.get(t, 0.0)
        reason_parts = []
        if underpowered:
            reason_parts.append(f"UNDERPOWERED(n={len(universe)}<{config.min_universe_n})")
        if not ok:
            reason_parts.append(why)
        elif tw > 0:
            reason_parts.append(f"selected rank={rank_of[t]} z={z_by_ticker[t]:+.2f}")
        else:
            reason_parts.append(f"비선정 rank={rank_of[t]}")
        out.append(SelectionCandidate(
            ticker=t,
            cheapness_z=z_by_ticker.get(t, 0.0),
            market_cap=market_caps.get(t, 0.0),
            rank=rank_of[t],
            target_weight=tw,
            eligible=ok and tw > 0,
            reason="; ".join(reason_parts),
            per_metric_z={m: per_metric[m].get(t, 0.0) for m in panel},
        ))
    return out


def _capped_equal_weight(
    selected: Sequence[str],
    sectors: dict[str, str],
    max_single: float,
    max_sector: float,
) -> dict[str, float]:
    """capped equal-weight: 종목 cap + 섹터 cap, water-filling 재분배.

    EW = 1/N 시작 → 종목 cap 클립 → 섹터 cap 클립 → 잔여를 미포화 종목에 재분배.
    risk_gate(10%/30%) 안쪽 권고. 자문: optimizer(MVO) 금지, capped-EW 가 OOS 우위.
    """
    n = len(selected)
    if n == 0:
        return {}
    # ★자문 재검증 (capped-EW feasibility, 2026-06-05): 고정 max_single < 1/n 이면 Σw<1
    #   (자본 미투자 = 실측 Σ0.5 결함). cap_i = max(max_single, 1/n) 로 small-N feasibility 보장
    #   (Claude R3: cap_i=max(single,1/N) + N·cap≥1). 섹터 cap 도 단일섹터 sleeve 보호 위해 동일.
    eff_single = max(max_single, 1.0 / n)
    n_sec = len({sectors.get(t, t) for t in selected})
    eff_sector = max(max_sector, 1.0 / n_sec) if n_sec > 0 else 1.0
    w = {t: eff_single for t in selected}

    # 섹터 cap: 초과 섹터 비례 축소 (water-filling)
    for _ in range(8):  # 유한 반복 수렴
        sec_tot: dict[str, float] = {}
        for t in selected:
            sec_tot[sectors.get(t, t)] = sec_tot.get(sectors.get(t, t), 0.0) + w[t]
        over = {s: tot for s, tot in sec_tot.items() if tot > eff_sector + 1e-9}
        if not over:
            break
        for t in selected:
            s = sectors.get(t, t)
            if s in over:
                w[t] *= eff_sector / sec_tot[s]

    # L1 정규화 Σ=1 (eff cap 이 feasible 보장 → 미투자/over-allocation 없음)
    tot = sum(w.values())
    if tot > 1e-12:
        w = {t: v / tot for t, v in w.items()}
    return w


# ---------------------------------------------------------------------------
# value_trigger stage-2 trap veto 어댑터 (재사용 래퍼)
# ---------------------------------------------------------------------------

def make_trap_veto(
    valuation_of: Callable[[str], object],
    *,
    heavy_agent=None,
    fundamentals_of: Optional[Callable[[str], Sequence]] = None,
) -> Callable[[str], bool]:
    """ticker → is_trap 콜백 생성. value_trigger.run_value_trigger(bypass_gate1=True) 재사용.

    valuation_of(ticker) → ValuationResult. heavy_agent 미주입 = ABSTAIN(보수적 비-trap=False,
      매수 후보 유지하되 호출자가 abstain 로그 확인). FORWARD 만 실판정(H22 백테스트 abstain).
    """
    from stock.value_trigger import run_value_trigger  # noqa: PLC0415
    from stock.contracts import ValueVerdict, RunMode

    def _veto(ticker: str) -> bool:
        val = valuation_of(ticker)
        if val is None:
            return False  # valuation 부재 = 판정 불가, 보수적 비-trap (selection z 가 이미 픽)
        funds = fundamentals_of(ticker) if fundamentals_of else []
        res = run_value_trigger(
            valuation=val,
            fundamentals=funds,
            price_change_pct=None,
            heavy_agent=heavy_agent,
            mode=RunMode.FORWARD,
            bypass_gate1=True,
            heavy_agent_fail_reason="quality" if heavy_agent is None else None,
        )
        return res.verdict == ValueVerdict.VALUE_TRAP

    return _veto
