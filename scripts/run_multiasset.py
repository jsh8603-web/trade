#!/usr/bin/env python3
"""scripts/run_multiasset.py — P2A A2 라이브 멀티에셋 entry 골격.

WHY: coin_track_macro.collect_market_state + (opt) stock_track → portfolio_orchestrator.allocate
     → weights 산출. DRY_RUN=true 기본(실주문 0건).

★A2 SR directive: stock_track.generate_candidate=dict 반환 vs engine getattr(decision,action)=무음hold.
  → _stock_track_adapter(st, state) 어댑터로 dict→Decision-호환 객체 정규화.
    Decision.action 속성을 dict["decision"] 에서 매핑, action!=hold 시 주문시도 도달 가능.

SACRED: DRY_RUN/go-live=사람게이트. KIS=paper=True 한정(코드경로 도달, 실주문X).
        run_agents.py 무영향.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger("scripts.run_multiasset")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")


# ---------------------------------------------------------------------------
# ★A2 track 어댑터: stock dict → Decision-호환 객체
# ---------------------------------------------------------------------------

@dataclass
class _StockDecision:
    """stock_track.generate_candidate dict → engine getattr(decision, "action") 호환.

    SR 발견: engine은 getattr(decision, "action", "hold")를 쓰지만
    stock_track은 {"decision": "buy", ...} dict를 반환 → 항상 무음 hold.
    이 어댑터로 dict["decision"] → .action 속성 매핑.
    """
    action: str = "hold"
    confidence: float = 0.0
    reason: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)


def _stock_track_adapter(stock_track, state) -> _StockDecision:
    """stock_track.generate_candidate 호출 후 dict→_StockDecision 정규화.

    stock_track이 None(미주입)이면 hold 반환.
    dict 반환 시 "decision" 키를 .action 에 매핑.
    이미 action 속성 있는 객체면 그대로 반환.
    """
    if stock_track is None:
        return _StockDecision(action="hold", reason="stock_track 미주입")
    try:
        raw = stock_track.generate_candidate(state)
    except Exception as exc:
        logger.warning("stock_track.generate_candidate 예외 → hold: %s", exc)
        return _StockDecision(action="hold", reason=f"exception:{exc}")

    # 이미 action 속성 있으면 그대로 통과
    if hasattr(raw, "action"):
        return raw  # type: ignore[return-value]

    # dict 반환 → 정규화
    if isinstance(raw, dict):
        action = raw.get("decision", "hold")
        # "buy"/"sell"/"hold"/"abstain" 정규화 (abstain → hold)
        if action not in ("buy", "sell", "hold"):
            action = "hold"
        return _StockDecision(
            action=action,
            confidence=float(raw.get("confidence", 0.0)),
            reason=str(raw.get("reason", "")),
            raw=raw,
        )

    # 알 수 없는 형식 → hold
    logger.warning("stock_track 미지원 반환형식(%s) → hold", type(raw))
    return _StockDecision(action="hold", reason=f"unknown_type:{type(raw)}")


# ---------------------------------------------------------------------------
# 1사이클 멀티에셋 루프
# ---------------------------------------------------------------------------

def _compute_multiasset_corr_sector(
    weights: Dict[str, float],
    target_sleeve: str,
    *,
    corr_matrix: Optional[Dict[str, Dict[str, float]]] = None,
) -> tuple:
    """★A3 합산층: 자산집합에서 avg_correlation / sector_weight 실산출.

    SR 발견: engine 단일루프는 avg_correlation=0.0/sector_weight=current_weight 하드코딩
    → 멀티에셋 corr_cap/max_weight_sector 영구 미발동.
    이 함수를 호출자(합산층)에서 호출해 실 상관/섹터비중을 산출 주입.

    Args:
        weights: 슬리브 배분 비중 {sleeve: pct}
        target_sleeve: 신규 진입 sleeve 이름 (corr 기준점)
        corr_matrix: sleeve-pair 상관 행렬 dict. None이면 0.0 반환(보수적 fallback).

    Returns:
        (avg_correlation, sector_weight)
        - avg_correlation: target_sleeve ↔ 나머지 보유 슬리브 가중평균 |상관|
        - sector_weight: target_sleeve 가 속한 자산군 합산 비중
    """
    # avg_correlation 산출
    avg_corr = 0.0
    if corr_matrix and target_sleeve in corr_matrix:
        row = corr_matrix[target_sleeve]
        num = den = 0.0
        for sleeve, w in weights.items():
            if sleeve == target_sleeve or w <= 0:
                continue
            rho = abs(row.get(sleeve, 0.0))
            num += w * rho
            den += w
        avg_corr = (num / den) if den > 0 else 0.0

    # sector_weight: 같은 자산군 합산 (주식=us_stock+kr_stock, 기타=자기만)
    _STOCK_SLEEVES = {"us_stock", "kr_stock"}
    if target_sleeve in _STOCK_SLEEVES:
        sector_weight = sum(weights.get(s, 0.0) for s in _STOCK_SLEEVES)
    else:
        sector_weight = weights.get(target_sleeve, 0.0)

    return avg_corr, sector_weight


def run_one_cycle(
    *,
    dry_run: bool = True,
    coin_track=None,
    stock_track=None,
    orchestrator=None,
    nav: float = 1_000_000.0,
    corr_matrix: Optional[Dict[str, Dict[str, float]]] = None,
) -> Dict[str, Any]:
    """coin + stock 1사이클 weights 산출 + ★A3 GatedOrderRouter.submit 연결.

    ★A3 SR directive: engine avg_correlation=0.0/sector_weight=current_weight 하드코딩 해소.
    이 호출자(합산층)에서 corr/sector를 자산집합서 산출 → GatedOrderRouter.submit 주입.

    Returns:
        {"weights": {sleeve: pct}, "coin_action": str, "stock_action": str,
         "gate_verdicts": {asset: verdict_str}, "triggered_rules": [str],
         "bypassed_attempts": int, "orders_attempted": int, "dry_run": bool}
    """
    from core.asset_track import MarketState
    from core.risk_gate import GatedOrderRouter, VerdictType

    router = GatedOrderRouter()

    # --- coin ---
    coin_action = "hold"
    if coin_track is not None:
        try:
            coin_state = coin_track.collect_market_state()
            coin_decision = coin_track.generate_candidate(coin_state)
            coin_action = getattr(coin_decision, "action",
                                  getattr(coin_decision, "decision", "hold"))
            if coin_action not in ("buy", "sell", "hold"):
                coin_action = "hold"
        except Exception as exc:
            logger.warning("coin_track 예외 → hold: %s", exc)

    # --- stock (어댑터 경유) ---
    stock_decision = _StockDecision(action="hold", reason="stock_track 미주입")
    if stock_track is not None:
        stock_state = MarketState(raw_market_data={"ticker": "005930"})
        stock_decision = _stock_track_adapter(stock_track, stock_state)
    stock_action = stock_decision.action

    # --- orchestrator weights ---
    weights: Dict[str, float] = {}
    if orchestrator is not None:
        try:
            result = orchestrator.allocate()
            weights = result.get("weights", {})
        except Exception as exc:
            logger.warning("orchestrator.allocate 예외 → empty weights: %s", exc)
    else:
        # stub: 균등 배분
        weights = {"coin": 0.10, "us_stock": 0.30, "kr_stock": 0.20,
                   "gold": 0.10, "bond": 0.20, "cash": 0.10}

    # 합=1 검증 (정규화)
    total = sum(weights.values())
    if total > 0 and abs(total - 1.0) > 1e-6:
        weights = {k: v / total for k, v in weights.items()}

    # ★A3 합산층 GatedOrderRouter.submit — corr/sector 실산출 주입
    gate_verdicts: Dict[str, str] = {}
    triggered_rules: list = []
    orders_attempted = 0

    asset_actions = [("coin", coin_action), ("kr_stock", stock_action)]
    for sleeve, action in asset_actions:
        if action not in ("buy", "sell"):
            gate_verdicts[sleeve] = "hold_skip"
            continue

        proposed_size = nav * weights.get(sleeve, 0.0)
        # ★합산층 실산출 (engine 0.0 하드코딩 대신)
        avg_corr, sector_w = _compute_multiasset_corr_sector(
            weights, sleeve, corr_matrix=corr_matrix
        )
        current_w = weights.get(sleeve, 0.0)

        verdict = router.submit(
            {"action": action, "asset": sleeve, "trade_value": proposed_size},
            cycle_id=f"multiasset-{sleeve}",
            via_gate=True,
            action=action,
            proposed_size=proposed_size,
            current_weight=current_w,
            sector_weight=sector_w,          # ★합산층 산출값
            avg_correlation=avg_corr,        # ★합산층 산출값
            nav=nav,
            position_pnl_pct=0.0,
            holding_days=0,
            ytd_realized_pnl_pct=0.0,
            daily_loss_pct=0.0,
        )

        gate_verdicts[sleeve] = verdict.verdict.value
        if verdict.triggered_rules:
            triggered_rules.extend(verdict.triggered_rules)

        if verdict.verdict != VerdictType.REJECTED:
            orders_attempted += 1
            if dry_run:
                logger.info("[DRY_RUN] %s %s → stub_order(네트워크0) [%s]",
                            sleeve, action, verdict.verdict.value)
            else:
                logger.info("[LIVE] %s %s → 주문 경로(A5 wire 후) [%s]",
                            sleeve, action, verdict.verdict.value)
        else:
            logger.info("[GATE] %s %s REJECTED: %s", sleeve, action, verdict.reason)

    return {
        "weights": weights,
        "weights_sum": round(sum(weights.values()), 6),
        "coin_action": coin_action,
        "stock_action": stock_action,
        "stock_adapter_raw_decision": stock_decision.raw.get("decision", "")
            if isinstance(stock_decision, _StockDecision) else "",
        "gate_verdicts": gate_verdicts,
        "triggered_rules": triggered_rules,
        "bypassed_attempts": router.bypassed_attempts,
        "orders_attempted": orders_attempted,
        "dry_run": dry_run,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="멀티에셋 라이브 entry 1사이클 (P2A A2)")
    ap.add_argument("--no-dry-run", action="store_true", default=False,
                    help="DRY_RUN 해제 (★사람게이트 — 이 flag 단독으로는 실주문 미발생, A5 wire 후)")
    ap.add_argument("--with-stock", action="store_true", default=False,
                    help="stock_track stub 주입 (어댑터 검증용)")
    args = ap.parse_args()

    dry_run = not args.no_dry_run

    # stub track: stock 어댑터 검증용 (valuation 미주입 → abstain/hold)
    coin_track = None
    stock_track = None

    if args.with_stock:
        try:
            from core.stock_track import StockTrack
            stock_track = StockTrack()  # valuation 미주입 → hold/abstain 경로
            logger.info("StockTrack 주입(어댑터 검증용, valuation 미연결=hold 예상)")
        except Exception as exc:
            logger.warning("StockTrack 로드 실패: %s", exc)

    result = run_one_cycle(
        dry_run=dry_run,
        coin_track=coin_track,
        stock_track=stock_track,
        orchestrator=None,  # stub weights (Phase 4 wire 후 실연결)
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
