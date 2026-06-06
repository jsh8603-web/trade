"""stock/sleeve_signals.py — sleeve별 연구 입증 cheapness 부호 preset (WIRE3.5-Ga).

연구(각 sleeve summary.yaml verdict + WIRE3 _wire3_*_sim.py 실측 IC)가 확정한 sleeve별
metric cheapness 부호를 production 상수로 박제한다. selection(cross_sectional_selection /
selection_pipeline)의 metric_signs 인자에 sleeve명으로 주입(호출자 opt-in).
미지정 시 호출자 직접 주입 경로는 그대로 = byte-identical.

부호 규약 (composite_cheapness_z 와 동일): +1 = 값 높을수록 쌈(매수 우선) / −1 = 값 낮을수록 쌈.
출처 = summary.yaml verdict + sim 측정 IC 부호 (1:1 일치, test_sleeve_signals.py 검증).
"""

from __future__ import annotations

from pathlib import Path

try:
    import yaml as _yaml
except Exception:  # pragma: no cover
    _yaml = None

_INV_ROOT = Path(__file__).resolve().parents[1]   # D:/projects/Inv

# sleeve → {metric: cheapness sign}. 각 부호 출처 주석 명기 (summary.yaml verdict / WIRE3 sim IC).
SLEEVE_SIGNS: dict[str, dict[str, int]] = {
    # cyclical: pbr/ev_ebitda value ★CONFIRMED (summary.yaml IC −0.1172/−0.1095, 저평가=쌈 → −1).
    #   _wire3_selection_sim.py:144 {"pbr":-1,"ev_ebitda":-1} 와 1:1.
    "cyclical": {"pbr": -1, "ev_ebitda": -1},
    # defensive: net_issuance PARTIAL (IC +0.082, 발행多 forward↑=buyback-aversion anti-value → +1)
    #            ep_yield TENTATIVE (IC −0.056, ep高 forward↓=anti-value → −1).
    #   _wire3_defensive_sim.py:112 {"net_issuance":+1,"ep_yield":-1} (sign=IC 부호) 와 1:1.
    "defensive": {"net_issuance": +1, "ep_yield": -1},
    # mega_tech: 11종 basket 통째 보유 = cross-sectional selection 대상 아님 (빈 preset).
    #   summary.yaml base_weight [0,0] + role diagnostic_no_verdict.
    "mega_tech": {},
}

# ★preset 제외 사유 박제 (consult-raw-output-mapping §3 = skip 사유 기재 의무).
#   연구가 측정했으나 신호 불안정으로 selection 미투입. 활성화 = OOS persist/BY 생존 회복 후.
SLEEVE_SIGNS_SKIPPED: dict[str, str] = {
    "cyclical.sales_yield": "TENTATIVE — 24M IC +0.083 양이나 CI 0 포함 + OOS persist=False (시간 불안정)",
    "defensive.residual_mom": "TENTATIVE — BY multiple-test 미생존",
}


def signs_for(sleeve: str) -> dict[str, int]:
    """sleeve명 → metric cheapness 부호 dict (복사본). 미지 sleeve = {} (호출자 직접 주입 fallback)."""
    return dict(SLEEVE_SIGNS.get(sleeve, {}))


# ★sleeve별 interaction (BW8 11종 검증 생존분, WIRE3.5-Gb): (m1, m2, sign).
#   DEF-2 dividend_yield(고)×op_profitability(고) = 유일 robust CONFIRM (incremental +0.065, FWL).
#   DEF-1 net_iss×ep = TENTATIVE(PW flip) → flip-sign 신규 pre-reg+OOS 전까지 보류(미투입).
SLEEVE_INTERACTIONS: dict[str, list[tuple[str, str, int]]] = {
    "defensive": [("dividend_yield", "op_profitability", +1)],
}


def interactions_for(sleeve: str) -> list[tuple[str, str, int]]:
    """sleeve명 → interaction (m1,m2,sign) 리스트 (복사본). composite_cheapness_z interactions 인자."""
    return list(SLEEVE_INTERACTIONS.get(sleeve, []))


# ★interaction weight 디스카운트 (Gj, DEF-2 marginal hedge, 2026-06-05 레저↔배선 검증 발견).
#   DEF-2 incremental rank-IC +0.065 ≈ 단일 value(−0.117)의 절반 → 단일 metric 과 등가중(1.0)은 과대.
#   small-n marginal CONFIRM = OOS 검증 불가 → 약하게 베팅(단방향 안전, 자문 Gh-2 정신). 점추정 최적값
#   주장 아님(0.5 = "main 의 절반" 보수 prior, hedge). main weight(yaml) 부재 시 빈 dict → 등가중 유지.
INTERACTION_WEIGHT_MULT: float = 0.5


def interaction_weights_for(sleeve: str, main_weights: dict[str, float]) -> dict[str, float]:
    """interaction term weight dict ({f"{m1}*{m2}": w}). main weight 평균 × MULT (marginal hedge).

    composite_cheapness_z weights 인자에 main weight 와 함께 병합 주입. main_weights 비면 {} (등가중 fallback).
    """
    inters = SLEEVE_INTERACTIONS.get(sleeve, [])
    if not inters or not main_weights:
        return {}
    base = sum(main_weights.values()) / len(main_weights)
    return {f"{m1}*{m2}": base * INTERACTION_WEIGHT_MULT for (m1, m2, _s) in inters}


def load_sleeve_weights(sleeve: str) -> dict[str, float]:
    """summary.yaml weight_rule_candidates 의 base_weight_range mid → {metric: weight} (WIRE3.5-Gc).

    selection 의 composite weights 인자로 주입(연구 base_weight 를 종목선택 가중에 연결).
    SLEEVE_SIGNS 키(pbr/net_issuance 등)와 yaml indicator_id(cs_pbr_z/cs_net_issuance) substring 매칭.
    yaml/PyYAML 부재·미매칭 = 빈 dict → selection 등가중 fallback(byte-identical).
    """
    signs = SLEEVE_SIGNS.get(sleeve, {})
    if not signs or _yaml is None:
        return {}
    yp = _INV_ROOT / "study-research" / "eq_us" / "industries" / f"us_{sleeve}" / "summary.yaml"
    if not yp.exists():
        return {}
    try:
        data = _yaml.safe_load(yp.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    rules = data.get("weight_rule_candidates") or data.get("weight_rules") or []
    out: dict[str, float] = {}
    for metric in signs:
        for r in rules:
            if metric in str(r.get("indicator_id", "")):
                rng = r.get("base_weight_range")
                if rng and len(rng) >= 2:
                    out[metric] = (float(rng[0]) + float(rng[-1])) / 2.0
                elif r.get("base_weight") is not None:
                    out[metric] = float(r["base_weight"])
                break
    return out
