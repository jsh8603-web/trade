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

def run_one_cycle(
    *,
    dry_run: bool = True,
    coin_track=None,
    stock_track=None,
    orchestrator=None,
) -> Dict[str, Any]:
    """coin + stock 1사이클 weights 산출.

    Returns:
        {"weights": {sleeve: pct}, "coin_action": str, "stock_action": str,
         "stock_adapter_raw": str, "orders_attempted": int, "dry_run": bool}
    """
    from core.asset_track import MarketState

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

    # --- 주문 시도 카운트 (DRY_RUN 차단) ---
    orders_attempted = 0
    if coin_action == "buy":
        orders_attempted += 1
        if dry_run:
            logger.info("[DRY_RUN] coin buy 시도 → stub_order(네트워크0)")
        else:
            logger.info("[LIVE] coin buy → Upbit 주문 경로(A5 wire 후)")
    if stock_action == "buy":
        orders_attempted += 1
        if dry_run:
            logger.info("[DRY_RUN] stock buy 시도 → stub_order(네트워크0)")
        else:
            logger.info("[LIVE] stock buy → KIS paper 주문 경로(A5 wire 후)")

    return {
        "weights": weights,
        "weights_sum": round(sum(weights.values()), 6),
        "coin_action": coin_action,
        "stock_action": stock_action,
        "stock_adapter_raw_decision": stock_decision.raw.get("decision", ""),
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
