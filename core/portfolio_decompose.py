"""core/portfolio_decompose.py — 배분 sleeve → 업종 sub-sleeve weight 분해 (끊긴 wire W2).

WHY (끊긴 wire 진단, 2026-06-07): orchestrator.allocate 는 sleeve 레벨 weight
({us_stock, kr_stock, gold, ...})만 산출하고, 종목선택(stock/construction.build_sleeve_decisions)은
업종(us_cyclical/us_defensive/us_mega_tech) 레벨로 동작한다. 둘 사이 "sleeve weight → 업종 weight
분해" 경로가 production 에 부재했다(grep 0). 거시배분과 종목선택을 잇는 누락 배선.

SLEEVE_AGG(core/brain/regime_to_weights.py:172) 와의 구분:
  - SLEEVE_AGG = 세분 sleeve → 배분 sleeve **cov-공간 roll-up**(W·Σ·Wᵀ, IC1 corr_prior 전용,
    방향 fine→coarse). weight 분해와 방향·목적이 반대 → 재사용 부적합(+ mega_tech 미수록).
  - 본 모듈 = 배분 sleeve weight → 업종 weight **분해**(방향 coarse→fine). SLEEVE_AGG 무수정.

설계 (자문 P3-G nested 정신 + 패시브 표준):
  - 시총비례(market-cap weighting)가 기본 = 패시브 표준(대형 업종에 비례 배분).
  - method="equal" = 업종 균등(1/N) fallback. 백테스트 A/B 비교용.
  - 분해는 순수 산술(weight × frac). 업종 총시총 조립은 호출자(provider/드라이버) 책임
    = construction 의 universe 조립 경계와 동일.

factor-z 보간 (2026-06-08, W3 — 18축 ④산업간배분 저조 fix, eq_us weight_rules 배선 ⑱):
  - study-research/eq_us/study_session.yaml 블록4 weight_rules(base_weight_range + regime_modulate
    + factor sensitivity)를 런타임에 소비 못 해 us 업종 비중이 시총비례에만 고정됐던 누락 배선.
    `factor_z` 인자(real_rate z 등) 주어질 때만 study 보간을 적용한다.
  - ★데이터 실측 calibrate(.p4-w3-sensitivity.py, factor z → 산업 forward 수익 rank-IC + walk-forward):
    • defensive ← real_rate z: fwd12M IC −0.334(p<0.001,n=184) walk-forward IS−0.329→OOS−0.235 일관
      = study β(−0.066 robust) 정합. ★study weight_rules 보존(2026-06-08 복원): base_weight_range
      [0.10,0.28]가 이미 소표본 hedge(점추정 회피 범위)이므로 그대로 작동밴드로 사용 = yaml 분석을 살린다.
      추가 축소(좁은 하위밴드)는 분석 자체를 죽이므로 금지. 선형 단조 보간
      `w=clip(mid − k·z·half_range, lo, hi)`, mid=0.19, half_range=0.09, k=0.5,
      z=±2σ → 0.10/0.28(study range 전체) 도달, 극단 z 는 range clip. z↑→비중↓. ⛔임계 스위치 금지(단조).
    • mega_tech: study regime_modulate=FALSE(노출≠alpha, real_rate forward OOS flip 확증) → mid 고정.
    • ★cyclical: study β(동시 −0.120) vs forward(+0.460 contrarian) 부호 충돌 + forward 신호 생존 15~20%
      (OOS>IS = V자반등 과적합 적색신호) → cap(시총비례) 유지 확정(자문 수렴). ⛔즉흥 부호 선택 금지.
  - ★factor_z=None 이면 기존 cap/equal 출력과 **byte-identical**(off 불변식 핵심).
  - 정규화: cyclical(cap) + defensive(보간) + mega_tech(고정) 산출 후 Σ 정규화 → parent_weight 곱
    = Σ sub_weight = parent_weight 보존.

불변식: parent_weight 보존(Σ sub_weight = parent_weight). 미주입 업종은 분배 제외(0).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

_INV_ROOT = Path(__file__).resolve().parents[1]   # D:/projects/Inv
_EQ_US_STUDY = _INV_ROOT / "study-research" / "eq_us" / "study_session.yaml"

# ★W3 calibrate 상수 (.p4-w3-sensitivity.py 실측, 2026-06-08; full range 복원).
#   defensive: fwd12M IC −0.334 정합. study base_weight_range[0.10,0.28] = 이미 소표본 hedge 범위
#   (점추정 회피)이므로 그대로 작동밴드로 사용 → yaml 분석 보존. 추가 축소 = 분석 죽임이라 금지.
#   설계: w = clip(mid − k·z·half_range, lo, hi). study mid=0.19, half_range=0.09.
#   k=0.5 → z 1σ 당 0.045 이동, z=±2σ 서 study range 끝(0.10/0.28) 도달, 극단은 clip(단조·임계 X).
_DEFENSIVE_TILT_K = 0.5
_DEFENSIVE_BAND = (0.10, 0.28)   # ★study base_weight_range 전체 = yaml 분석 보존(점추정 회피 hedge).
# 보간 적용 업종 = defensive(real_rate)만. mega_tech=고정 mid, cyclical=cap(보류 확정).
_MODULATED_FACTOR = {"defensive": "real_rate"}

# 배분 sleeve → 업종 sub-sleeve 목록 (study-research/eq_us 업종 = us_*, eq_kr 업종 = 한국 테마).
#   값 = construction.build_sleeve_decisions 의 sleeve 인자로 그대로 쓰는 식별자.
#   us_mega_tech = SLEEVE_AGG 누락분(custom basket) 포함 → 업종 전수.
#   ★식별자 = construction.build_sleeve_decisions 의 sleeve 인자(prefix 無) = sleeve_signals
#   .signs_for/load_sleeve_weights("cyclical"→us_cyclical/summary.yaml) 와 1:1. study 디렉토리명
#   (us_cyclical)은 호출자(드라이버)가 "us_"+name 으로 매핑.
SUB_SLEEVES: Dict[str, List[str]] = {
    "us_stock": ["cyclical", "defensive", "mega_tech"],
    # kr_stock 업종(eq_kr study) = 12산업 전수 배선(2026-06-08). 직전 7업종 = 미완 배선(데이터
    #   12/12 완비인데 SUB_SLEEVES 미등록으로 decompose_weight 가 5섹터 비중=0 처리 = ⑱축 누락).
    #   _ETF_FALLBACK_ROUTING: financial/battery/shipbuilding/auto→ETF(KODEX), 나머지→EW(구성종목,
    #   semiconductor/steel/aitech 는 .get fallback=EW). selection 부호(within-residual-v2)는 robust
    #   3곳(semi/steel/aitech, BY생존+ρ≥0.25)만 후속 배선 — 현 단계 = 12산업 ETF/EW 배분.
    "kr_stock": ["financial", "battery", "bio", "shipbuilding", "consumer", "chemical", "auto",
                 "semiconductor", "steel", "aitech", "refining", "telecom"],
}


def subsleeves_for(parent_sleeve: str) -> List[str]:
    """배분 sleeve → 업종 sub-sleeve 목록(복사본). 미정의 = []."""
    return list(SUB_SLEEVES.get(parent_sleeve, []))


_US_WEIGHT_RANGE_CACHE: Optional[Dict[str, tuple]] = None


def _load_us_weight_ranges() -> Dict[str, tuple]:
    """study_session.yaml 블록4 weight_rules → {업종: (lo, hi)} base_weight_range (캐시).

    study_loader.WeightRule dataclass 는 base_weight_range/sensitivity 필드 미정의 → 직접 파싱.
    yaml/PyYAML 부재·미매칭 = 빈 dict(graceful → 보간 미적용 = cap byte-identical).
    업종 식별자 = study "us_cyclical" → SUB_SLEEVES 의 "cyclical"(prefix 제거).
    """
    global _US_WEIGHT_RANGE_CACHE
    if _US_WEIGHT_RANGE_CACHE is not None:
        return _US_WEIGHT_RANGE_CACHE
    out: Dict[str, tuple] = {}
    try:
        import yaml  # 지연 import (부재 환경 graceful)
        data = yaml.safe_load(_EQ_US_STUDY.read_text(encoding="utf-8")) or {}
        for r in data.get("weight_rules") or []:
            ind = str(r.get("industry", ""))
            name = ind[3:] if ind.startswith("us_") else ind   # us_cyclical → cyclical
            rng = r.get("base_weight_range")
            if name and rng and len(rng) >= 2:
                out[name] = (float(rng[0]), float(rng[-1]))
    except Exception:
        out = {}
    _US_WEIGHT_RANGE_CACHE = out
    return out


def _modulated_us_weights(
    cap_frac: Dict[str, float],
    factor_z: Dict[str, float],
) -> Optional[Dict[str, float]]:
    """us_stock factor-z 보간 비중(Σ=1, parent_weight 곱 전). 실패 시 None(→ cap fallback).

    - defensive: real_rate z 선형 보간 `w=clip(mid − k·z·half, lo, hi)` (z↑→비중↓, β음
      정합). ★study base_weight_range[0.10,0.28] 전체를 작동밴드로 사용 = yaml 분석 보존(k=0.5).
    - mega_tech: 고정 mid (regime_modulate=false).
    - cyclical: cap 시총비례 점유율 유지(보류 확정 — study β vs forward 부호 충돌, forward 생존 15~20%).
    cap_frac = {업종: 시총 점유율(Σ=1)}. factor_z = {factor: z}.
    """
    ranges = _load_us_weight_ranges()
    if not ranges:
        return None
    raw: Dict[str, float] = {}
    for s in ("cyclical", "defensive", "mega_tech"):
        rng = ranges.get(s)
        if s == "cyclical":
            # 보류 = cap 시총 점유율 그대로(보간 미적용). cap 부재 시 mid fallback.
            raw[s] = cap_frac.get(s) if cap_frac.get(s, 0.0) > 0 else (
                (rng[0] + rng[1]) / 2.0 if rng else 0.0)
            continue
        if not rng:
            raw[s] = cap_frac.get(s, 0.0)
            continue
        lo, hi = rng
        mid = (lo + hi) / 2.0
        if s == "mega_tech":
            raw[s] = mid   # regime_modulate=false 고정
            continue
        fac = _MODULATED_FACTOR.get(s)
        z = factor_z.get(fac) if fac else None
        if z is None:
            raw[s] = mid   # factor 미주입 → mid(graceful)
            continue
        # ★study weight_rules 보존(k=0.5): study half_range(0.09)에 k=0.5 → z↑→비중↓ 단조, range clip.
        #   w = mid − k·z·half_range, clip[lo,hi]. k=0.5·half(0.09)=0.045/z →
        #   z=±2σ 서 study range 끝(0.10/0.28) 도달, 극단 z 는 range clip(임계 스위치 없는 단조).
        half = (hi - lo) / 2.0                       # study half_range = 0.09
        band_lo, band_hi = _DEFENSIVE_BAND           # study range 전체 (0.10, 0.28) = yaml 보존
        w = mid - _DEFENSIVE_TILT_K * float(z) * half   # k=0.5, z↑→비중↓
        raw[s] = min(band_hi, max(band_lo, w))       # study range clip(yaml 분석 보존)
    tot = sum(raw.values())
    if tot <= 0:
        return None
    return {s: w / tot for s, w in raw.items()}


def decompose_weight(
    parent_sleeve: str,
    parent_weight: float,
    subsleeve_mktcaps: Optional[Dict[str, float]] = None,
    *,
    method: str = "cap",
    factor_z: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """배분 sleeve weight → 업종 sub-sleeve weight 분해.

    Args:
        parent_sleeve: 배분 sleeve("us_stock" 등).
        parent_weight: 거시배분이 준 sleeve 총비중(0~1).
        subsleeve_mktcaps: {업종: as_of 총시총}. method="cap" 시 필수.
            None/빈 dict 면 method 무관 equal fallback(시총 부재 graceful).
        method: "cap"(시총비례, 기본) | "equal"(업종 균등 1/N).
        factor_z: {factor: z-score}(예: {"real_rate": 0.7}). ★None(기본) 이면 study 보간 미적용
            = 기존 cap/equal 출력과 byte-identical(off 불변식). 주어질 때만 us_stock 의
            defensive(real_rate z 보간)/mega_tech(고정)/cyclical(cap 보류) study 배선 적용.

    Returns:
        {업종: weight} (Σ = parent_weight, 부동소수 오차 한정). 업종 목록 부재 시 {}.
        시총 0/음수 업종은 cap 에서 제외(equal 은 전 업종 포함).
    """
    subs = subsleeves_for(parent_sleeve)
    if not subs or parent_weight <= 0:
        return {}

    # cap 시총 점유율(Σ=1, parent_weight 곱 전) — 보간/cap 공통 base.
    cap_frac: Optional[Dict[str, float]] = None
    if method == "cap" and subsleeve_mktcaps:
        valid = {s: mc for s in subs
                 if (mc := subsleeve_mktcaps.get(s, 0.0)) and mc > 0}
        total = sum(valid.values())
        if total > 0:
            cap_frac = {s: mc / total for s, mc in valid.items()}

    # ★study 보간 (us_stock + factor_z 주어질 때만). 실패 시 cap/equal fallback.
    if factor_z and parent_sleeve == "us_stock":
        mod = _modulated_us_weights(cap_frac or {}, factor_z)
        if mod is not None:
            return {s: parent_weight * f for s, f in mod.items()}

    # cap 시총비례
    if cap_frac is not None:
        return {s: parent_weight * f for s, f in cap_frac.items()}

    # equal (또는 cap 시총 부재 fallback)
    n = len(subs)
    return {s: parent_weight / n for s in subs}
