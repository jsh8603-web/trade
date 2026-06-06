# -*- coding: utf-8 -*-
"""stock/order_assembly.py — selection Decision → GatedOrderRouter → broker (WIRE6, flag-gated).

selection_pipeline/construction 의 Decision 후보를 실 주문 경로로 ★연결만 완성하고, 실 발송은
flag 로 차단한다(사용자 2026-06-05 "연결은 다 해두고 flag on/off"):
  - DRY_RUN=True(default) → broker 미발송(shadow 기록만). 실주문 0건.
  - EMERGENCY_STOP=True → 전면 차단(kill switch).
  - 모든 주문 = GatedOrderRouter.submit(via_gate=True) 경유 강제(risk_gate 우회 불가, nautilus 패턴).

flag on(dry_run=False) 실 발송은 broker 주입 + 사람 게이트(README-unattended-safety D1~D5) 후에만.
broker = OrderBroker Protocol(KisClient=한국 / 미국 adapter=추후). dry_run 시 broker 없어도 동작.

⛔ go-live 무접촉: 본 모듈 default(DRY_RUN=True)=실주문 0. coin_shadow/kis_client 와 동일 안전 패턴.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Optional, Protocol, Sequence

from core.risk_gate import (
    GatedOrderRouter,
    etf_lookthrough_exposures,
    holdings_pit_stale,
)

logger = logging.getLogger("stock.order_assembly")

# ETF holdings PIT max-lag (자문 D 라우팅 조건). 초과 = stale → look-through 불가 → wrapper 통째 보수.
_ETF_HOLDINGS_MAX_LAG_DAYS = int(os.environ.get("ETF_HOLDINGS_MAX_LAG_DAYS", "90"))


class OrderBroker(Protocol):
    """broker 어댑터 계약 (KisClient.order 시그니처 호환). dry_run=False + 주입 시만 실 발송."""

    def order(self, ticker: str, side: str, qty: float, **kwargs: Any) -> Any: ...


def _flag(name: str, default: bool) -> bool:
    """env flag 읽기 ("true"/"false"). 미설정 = default."""
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() == "true"


def _etf_fallback_on() -> bool:
    """ETF_FALLBACK 활성 여부 — construction._resolve_etf_routing 과 동일 규칙(off=비활성)."""
    return os.environ.get("ETF_FALLBACK", "off").strip().lower() != "off"


def _etf_lookthrough_gate_kwargs(
    d: dict, tw: float, gate_kwargs: dict, asof: Optional[datetime],
) -> tuple[dict, dict]:
    """ETF decision → risk_gate look-through gate_kwargs override + 로깅 dict.

    자문 D3 안전장치 (env gated 호출자만):
      - 단일발행체 = direct + via-ETF 최대 종목 실효비중 → current_weight 에 합산
        (check max_weight_single 이 underlying 집중을 포착 = '종목 cap=ETF 자체'를 넘어 underlying 분해).
      - 섹터 cap = look-through 최대 섹터 비중 → sector_weight 에 합산 (테마 ETF 통째보다 정밀).
      - holdings PIT stale / holdings 부재 → look-through 불가 → wrapper 통째 1섹터 보수(=tw).
    반환 (per_kwargs, lookthrough_log).
    """
    holdings = d.get("holdings") or []
    direct = d.get("direct_holdings") or None
    lt = etf_lookthrough_exposures(tw, holdings, direct_holdings=direct)

    asof = asof if isinstance(asof, datetime) else None
    stale = holdings_pit_stale(d.get("holdings_asof"), asof, _ETF_HOLDINGS_MAX_LAG_DAYS)

    by_sector = lt["by_sector"]
    # stale 또는 look-through 불가(섹터 분해 없음) → 보수: wrapper 통째 단일 섹터(=tw)
    max_sec = tw if (stale or not by_sector) else max(by_sector.values())
    base_sec = float(gate_kwargs.get("sector_weight", 0.0) or 0.0)
    # ETF 경로는 proposed_size=tw 명시 전달 → check max_weight 검사가 ETF 비중을 포착(EQUITY 무변경).
    per_kwargs = {**gate_kwargs, "sector_weight": base_sec + max_sec, "proposed_size": tw}

    top = lt["top_issuer"]
    log: dict[str, Any] = {
        "covered": lt["covered"], "n_sector": len(by_sector),
        "max_sector_eff": max_sec, "stale": stale,
    }
    if top and top[1] > 0 and not stale:
        base_cur = float(gate_kwargs.get("current_weight", 0.0) or 0.0)
        per_kwargs["current_weight"] = base_cur + top[1]   # 단일발행체 direct+via-ETF 합산
        log["top_issuer"] = top[0]
        log["top_issuer_eff"] = top[1]
    return per_kwargs, log


def assemble_stock_orders(
    decisions: Sequence[dict],
    *,
    router: GatedOrderRouter,
    broker: Optional[OrderBroker] = None,
    dry_run: Optional[bool] = None,
    emergency_stop: Optional[bool] = None,
    cycle_id: str = "",
    asof: Optional[datetime] = None,
    **gate_kwargs: Any,
) -> list[dict]:
    """Decision(target_weight>0) → order → GatedOrderRouter(risk_gate 경유) → broker(flag 차단).

    각 매수후보를 risk_gate 관문(via_gate=True 강제) 통과시킨 뒤, flag 에 따라:
      - emergency_stop / dry_run / broker 부재 → status="shadow" (미발송, 기록만).
      - approved + dry_run=False + broker 주입 → broker.order() 실 발송, status="sent".
      - risk_gate REJECTED → status="rejected".

    dry_run=None → env DRY_RUN(default True). emergency_stop=None → env EMERGENCY_STOP(default False).
    gate_kwargs = RiskGate.check 에 전달(nav/price 등). 반환 = 주문별 결과 dict 리스트.
    """
    dr = _flag("DRY_RUN", True) if dry_run is None else dry_run
    es = _flag("EMERGENCY_STOP", False) if emergency_stop is None else emergency_stop

    out: list[dict] = []
    for d in decisions:
        tw = float(d.get("target_weight", 0.0) or 0.0)
        if tw <= 0:
            continue
        ticker = d.get("ticker", "")
        order = {
            "ticker": ticker,
            "side": "buy",
            "target_weight": tw,
            "cheapness_z": d.get("cheapness_z"),
            "rank": d.get("rank"),
        }
        # ★ETF look-through (env ETF_FALLBACK on + instrument_type=ETF, 자문 D3 안전장치).
        #   off/EQUITY → per_kwargs=gate_kwargs = 기존 경로(byte-identical).
        per_kwargs = gate_kwargs
        rec_lt: Optional[dict] = None
        if _etf_fallback_on() and d.get("instrument_type") == "ETF":
            per_kwargs, rec_lt = _etf_lookthrough_gate_kwargs(d, tw, gate_kwargs, asof)
        verdict = router.submit(order, cycle_id=cycle_id, via_gate=True, **per_kwargs)
        rec: dict[str, Any] = {
            "ticker": ticker,
            "side": "buy",
            "target_weight": tw,
            "verdict": getattr(verdict, "verdict", None),
        }
        if rec_lt is not None:
            rec["lookthrough"] = rec_lt
        if not getattr(verdict, "approved", False):
            rec["status"] = "rejected"
            rec["reason"] = getattr(verdict, "reason", "")
            out.append(rec)
            continue
        if es or dr or broker is None:
            rec["status"] = "shadow"
            rec["reason"] = "emergency_stop" if es else ("dry_run" if dr else "no_broker")
            logger.info("[order_assembly] shadow(%s): buy %s tw=%.4f", rec["reason"], ticker, tw)
        else:
            broker.order(ticker=ticker, side="buy", qty=tw)   # ★실 발송 (flag on + 사람게이트 후)
            rec["status"] = "sent"
            logger.warning("[order_assembly] ★LIVE sent: buy %s tw=%.4f", ticker, tw)
        out.append(rec)
    return out
