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


def _apply_judge_hook(
    judge_hook,
    *,
    sleeve: str,
    proposed_size: float,
    l1_size: float = 1.0,
) -> float:
    """★A4 judge(down-only) hook 적용.

    engine W3 패턴 재현: JudgeVerdict 또는 dict 허용.
    final = size_mult ∈ [0, l1_size] (down-only 불변식 보장).
    hook=None → fail-open a=1.0 (결정론 baseline).

    Returns: a_judge (0~l1_size)
    """
    if judge_hook is None:
        return l1_size  # fail-open

    try:
        jv = judge_hook(sleeve=sleeve, proposed_size=proposed_size, l1_size=l1_size)
        if hasattr(jv, "size_mult") and hasattr(jv, "l1_size"):
            l1_ref = float(jv.l1_size) if jv.l1_size else l1_size
            a = float(jv.size_mult)
        elif isinstance(jv, dict):
            l1_ref = float(jv.get("l1_size", l1_size))
            a = float(jv.get("size_mult", l1_size))
        else:
            return l1_size  # 알 수 없는 형식 → fail-open
        # ★천장 불변식: final ≤ l1_size (down-only, 증폭 금지)
        return float(min(max(a, 0.0), l1_ref))
    except Exception as exc:
        logger.warning("judge_hook 예외 → fail-open: %s", exc)
        return l1_size  # 장애 = fail-open


def run_one_cycle(
    *,
    dry_run: bool = True,
    coin_track=None,
    stock_track=None,
    orchestrator=None,
    nav: float = 1_000_000.0,
    corr_matrix: Optional[Dict[str, Dict[str, float]]] = None,
    judge_hook=None,    # A4: judge hook (None=fail-open a=1.0)
) -> Dict[str, Any]:
    """coin + stock 1사이클 weights 산출 + A3 GatedOrderRouter.submit + ★A4 judge hook.

    ★A3 SR directive: engine avg_correlation=0.0/sector_weight=current_weight 하드코딩 해소.
    ★A4: judge hook — high-stakes 시 사이징 감쇠. final ≤ l1_size (down-only 불변식).

    Returns:
        {"weights": {sleeve: pct}, "coin_action": str, "stock_action": str,
         "gate_verdicts": {asset: verdict_str}, "judge_a": {asset: float},
         "triggered_rules": [str], "bypassed_attempts": int,
         "orders_attempted": int, "dry_run": bool}
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
    judge_a: Dict[str, float] = {}    # A4: sleeve별 judge a 값
    triggered_rules: list = []
    orders_attempted = 0

    asset_actions = [("coin", coin_action), ("kr_stock", stock_action)]
    for sleeve, action in asset_actions:
        if action not in ("buy", "sell"):
            gate_verdicts[sleeve] = "hold_skip"
            judge_a[sleeve] = 1.0
            continue

        proposed_size = nav * weights.get(sleeve, 0.0)

        # ★A4 judge hook — gate submit 전 사이징 감쇠 (down-only)
        l1_size = 1.0  # 기본 L1 = 단위 사이즈
        a_judge = _apply_judge_hook(judge_hook, sleeve=sleeve,
                                    proposed_size=proposed_size, l1_size=l1_size)
        judge_a[sleeve] = a_judge
        proposed_size_judged = proposed_size * a_judge  # judge 적용 후 사이즈

        # ★합산층 실산출 (engine 0.0 하드코딩 대신)
        avg_corr, sector_w = _compute_multiasset_corr_sector(
            weights, sleeve, corr_matrix=corr_matrix
        )
        current_w = weights.get(sleeve, 0.0)

        verdict = router.submit(
            {"action": action, "asset": sleeve, "trade_value": proposed_size_judged},
            cycle_id=f"multiasset-{sleeve}",
            via_gate=True,
            action=action,
            proposed_size=proposed_size_judged,  # judge 감쇠 후 사이즈
            current_weight=current_w,
            sector_weight=sector_w,              # ★합산층 산출값
            avg_correlation=avg_corr,            # ★합산층 산출값
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
                logger.info("[DRY_RUN] %s %s → stub_order [%s] judge_a=%.3f",
                            sleeve, action, verdict.verdict.value, a_judge)
            else:
                logger.info("[LIVE] %s %s → 주문 경로(A5 wire 후) [%s] judge_a=%.3f",
                            sleeve, action, verdict.verdict.value, a_judge)
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
        "judge_a": judge_a,                  # A4: down-only 사이징 감쇠 결과
        "triggered_rules": triggered_rules,
        "bypassed_attempts": router.bypassed_attempts,
        "orders_attempted": orders_attempted,
        "dry_run": dry_run,
    }


def _coin_stub_order(market: str, action: str, *, dry_run: bool = True) -> dict:
    """★A5 Upbit 코인 주문 코드경로.

    DRY_RUN=true → stub (네트워크0). False + 실 credential → Upbit API 경로(사람게이트).
    이 함수는 코드경로 도달 검증용 — 실 Upbit API 호출은 go-live 사람게이트 후에만.
    """
    if dry_run:
        return {"status": "stub", "market": market, "action": action, "network": 0}
    # 실 주문 경로 (go-live 사람게이트 — DRY_RUN=false 시만 도달)
    logger.info("[LIVE] Upbit coin order: %s %s (A5 wire 연결완료)", action, market)
    return {"status": "live_path", "market": market, "action": action}


def _stock_order_via_kis(
    ticker: str,
    action: str,
    qty: float = 1.0,
    *,
    dry_run: bool = True,
) -> dict:
    """★A5 KIS paper 주문 코드경로.

    DRY_RUN=true → KisClient(paper=True) 생성 + stub 반환(네트워크0).
    credential 없음 → _stub_order 경로(KisClient 내부 deferral). 실주문=사람게이트.
    """
    try:
        from stock.kis_client import KisClient
        # credential 없으면 _stub_order 내부 경로(deferral-pinning)
        kis = KisClient(paper=True, dry_run=dry_run)
        if dry_run:
            return {"status": "stub", "ticker": ticker, "action": action, "paper": True}
        # 실 주문 경로 (paper=True = 모의투자, go-live 사람게이트)
        ref = kis.order(ticker, action.upper(), qty)
        return {
            "status": "paper_sent" if ref else "blocked",
            "ticker": ticker,
            "action": action,
            "order_ref": str(ref) if ref else None,
        }
    except Exception as exc:
        logger.warning("KIS 주문 경로 예외(코드경로 도달, 실 발송 아님): %s", exc)
        return {"status": "error", "ticker": ticker, "action": action, "error": str(exc)}


# ---------------------------------------------------------------------------
# 백테스트 모드 (P4 — 프로덕션 경로 시계열 검증)
#   ⛔ 별도 회계 우회 금지(progress 상단 명시금지): 종목마다 GatedOrderRouter.submit(via_gate)
#      + judge_hook 경유, 통과분만 NAV 반영. 업종분해(portfolio_decompose)+종목선택(construction)
#      = 프로덕션 모듈 호출. run_one_cycle 의 gate/judge 경유를 시계열·종목 레벨로 확장.
# ---------------------------------------------------------------------------
from pathlib import Path as _Path

_IND_US = _Path("study-research/eq_us/industries")
_US_SUB = {"cyclical": "us_cyclical", "defensive": "us_defensive", "mega_tech": "us_mega_tech"}
_IND_KR = _Path("study-research/eq_kr/industries")
# ★12산업 전체 배선(2026-06-08): 데이터 12/12 완비(_bt_load_kr 검증). 직전 7섹터만 등록 = 단순
#   누락 버그(근거 주석 부재)였음을 측정으로 정정. 추가 5: semiconductor/steel/aitech/refining/telecom.
#   selection 등급(within-residual-v2): robust(BY생존+ρ≥0.25)=semiconductor/steel/aitech 3곳,
#   나머지 9곳 ρ<0.25 약 → ETF/EW fallback 라우팅(_ETF_FALLBACK_ROUTING, semi/steel/aitech 미수록=.get EW).
_KR_SUB = ["financial", "battery", "bio", "shipbuilding", "consumer", "chemical", "auto",
           "semiconductor", "steel", "aitech", "refining", "telecom"]
_KR_ETF_PICKS = {
    "financial": {"ticker": "091170", "aum": 6.143e11, "holdings_source": "FDR"},
    "battery": {"ticker": "305720", "aum": 2.045e12, "holdings_source": "FDR"},
    "shipbuilding": {"ticker": "441540", "aum": 8.75e10, "holdings_source": "FDR"},
    "auto": {"ticker": "091180", "aum": 5.65e11, "holdings_source": "FDR"},
}


def _bt_load_us(name):
    import pandas as pd
    d = _IND_US / _US_SUB[name] / "raw-v3" / "data"
    px = pd.read_parquet(d / "prices.parquet"); px.index = pd.to_datetime(px.index)
    ed = pd.read_parquet(d / "edgar_fundamentals.parquet")
    ed["filed"] = pd.to_datetime(ed["filed"]); ed["end"] = pd.to_datetime(ed["end"])
    uf = d / "universe.parquet"
    tks = pd.read_parquet(uf)["ticker"].tolist() if uf.exists() else []
    # ★mega_tech = custom basket(11종 Mag7+AVGO/AMD/ORCL/ASML)이라 universe.parquet 부재 →
    #   prices.parquet 컬럼(=basket 종목)을 fallback universe 로 사용(④산업간배분 mega_tech 집계 복원).
    #   cyclical/defensive 는 universe.parquet 존재 → 무영향(byte-identical).
    if not tks:
        tks = [str(c) for c in px.columns]
    return px, ed, tks


_US_SECTORS_CACHE: dict = {}
_DEF_QUALITY_PANEL = None   # (dividend_yield_df, op_profitability_df) study PIT 패널 캐시


def _bt_def_quality_panels():
    """defensive DEF-2 입력 패널(dividend_yield/op_profitability) = study 빌더 그대로(정의 1:1).

    measure.build_pit_panels(dividend_yield=ttm_div/mktcap) + _breadth_sweep.build_breadth_panels
    (op_profitability=ttm_op/equity, FF2015 RMW). ttm 재구현 대신 study 산출 직접 lookup → spec↔code
    drift 0. 월별 PIT 시계열 → _bt_us_picks 가 as_of≤ 최신행을 panel 에 주입.
    """
    global _DEF_QUALITY_PANEL
    if _DEF_QUALITY_PANEL is not None:
        return _DEF_QUALITY_PANEL
    import sys
    import pandas as pd
    raw = _IND_US / _US_SUB["defensive"] / "raw-v3"
    sys.path.insert(0, str(raw))
    import measure as _M
    from _breadth_sweep import build_breadth_panels as _bbp
    px, ed, _uni, _macro = _M.load()
    P = _M.build_pit_panels(px, ed)
    amt = pd.read_parquet(raw / "data" / "amount.parquet"); amt.index = pd.to_datetime(amt.index)
    Bp = _bbp(px, ed, amt)
    _DEF_QUALITY_PANEL = (P["dividend_yield"], Bp["op_profitability"])
    return _DEF_QUALITY_PANEL


def _bt_add_def_quality(panel, mcap_by, as_of):
    """defensive panel 에 dividend_yield/op_profitability raw 값 주입(DEF-2 interaction 활성용).

    build_sleeve_decisions(use_interactions=True) → interactions_for('defensive')=[DEF-2(div×op,+1)] →
    composite_cheapness_z 가 panel[div]·panel[op] 참조해 교호항 z 생성. panel 부재 시 내부 skip(현 결함).
    """
    import pandas as pd
    try:
        dyP, opP = _bt_def_quality_panels()
    except Exception as exc:
        logger.warning("def quality panels: %r", exc); return
    asof_ts = pd.Timestamp(as_of)
    for src, key in ((dyP, "dividend_yield"), (opP, "op_profitability")):
        rows = src[src.index <= asof_ts]   # PIT: as_of 이하 최신 월행
        if rows.empty:
            continue
        last = rows.iloc[-1]
        panel[key] = {tk: float(last[tk]) for tk in mcap_by
                      if tk in last.index and pd.notna(last[tk])}


def _bt_us_sectors(name):
    """universe.parquet subcl → {ticker: sub_sector} (study sector-neutral demean용).

    ★study 명시(measure.py:26 'universe-demean=결함', dividend_yield sub-sector sign flip): defensive/
    cyclical 은 multi-sector → sector-neutral 필수. 미주입 시 cross-sector cancel 로 value/quality 신호
    소멸(.p4-defensive-quality 실측: value t+3.33→+0.91 붕괴). build_sleeve_decisions(sectors=) 주입 →
    demean_by_sector=on. subcl 부재(mega_tech basket)=None=universe-demean(byte-identical).
    """
    if name in _US_SECTORS_CACHE:
        return _US_SECTORS_CACHE[name]
    import pandas as pd
    uf = _IND_US / _US_SUB[name] / "raw-v3" / "data" / "universe.parquet"
    m = None
    if uf.exists():
        u = pd.read_parquet(uf)
        if "subcl" in u.columns:
            m = dict(zip(u["ticker"].astype(str), u["subcl"].astype(str)))
    _US_SECTORS_CACHE[name] = m
    return m


def _bt_real_rate_z(end, window=36):
    """real_rate(DFII10) 월말 rolling z-score 시계열 (PIT, as_of-causal).

    W3 산업간 배분 배선: defensive 업종 weight 를 study weight_rules base_weight_range 내에서
    real_rate z 로 보간(decompose_weight factor_z 인자). z↑→defensive 비중↓(study β−0.066 정합).
    factor_returns.RealFredAdapter.get_series = first-release PIT(발표시점값, lookahead 없음).
    실패(FRED unavailable) 시 None → decompose_weight factor_z=None → cap byte-identical.
    """
    import pandas as pd
    import numpy as np
    try:
        from core.data.factor_returns import FACTOR_SERIES
        from core.brain.fred_adapter import RealFredAdapter
        adapter = RealFredAdapter()
        if not adapter.is_available():
            return None
        s = adapter.get_series(FACTOR_SERIES["real"], as_of=pd.Timestamp(end))
        if s is None or len(s) == 0:
            return None
        s = s.resample("ME").last().dropna()
        mu = s.rolling(window, min_periods=max(12, window // 2)).mean()
        sd = s.rolling(window, min_periods=max(12, window // 2)).std()
        z = ((s - mu) / sd).replace([np.inf, -np.inf], np.nan).dropna()
        return z
    except Exception as exc:
        logger.warning("real_rate z 시계열 실패: %r → cap fallback", exc)
        return None


def _bt_load_kr(name):
    import pandas as pd
    d = _IND_KR / name / "raw-v3" / "data"
    px = pd.read_parquet(d / "prices.parquet"); px.index = pd.to_datetime(px.index)
    px.columns = [str(c) for c in px.columns]
    uni = pd.read_parquet(d / "universe.parquet"); uni["Code"] = uni["Code"].astype(str)
    # ★study cheapness(pbr) selection 용 DART 재무(PIT key=rcept_dt). 부재 시 None=ETF/EW 경로.
    dp = d / "dart_financials.parquet"
    dart = None
    if dp.exists():
        dart = pd.read_parquet(dp); dart["code"] = dart["code"].astype(str)
    return px, uni, dart


def _kr_pit_equity(dart, code, as_of_ts):
    """한국 종목 PIT 자본(book_value) — rcept_dt(공시일)≤as_of 중 최신 분기. lookahead 차단(L2b).

    equity = 자본총계(시점 stock 변수, 분기 누적 무관). pbr = mktcap/equity 용. 결측 None.
    """
    import pandas as pd
    if dart is None:
        return None
    m = dart[dart["code"] == code]
    if m.empty:
        return None
    filed = pd.to_datetime(m["rcept_dt"].astype(str), format="%Y%m%d", errors="coerce")
    vis = m[filed <= as_of_ts]
    if vis.empty:
        return None
    fvis = pd.to_datetime(vis["rcept_dt"].astype(str), format="%Y%m%d", errors="coerce")
    eq = vis.loc[fvis.idxmax(), "equity"]
    return float(eq) if pd.notna(eq) and float(eq) > 0 else None


def _kr_pit_roe(dart, code, as_of_ts):
    """PIT ROE(quality) = 최신 공시 net_income/equity. ★plan W4: cheapness×quality 게이트 —
    한국 저PBR 코리아 디스카운트(거버넌스 영구할인) 트랩 방어. 저PBR+저ROE=영구할인 자동 하위 랭크.
    """
    import pandas as pd
    if dart is None:
        return None
    m = dart[dart["code"] == code]
    if m.empty:
        return None
    filed = pd.to_datetime(m["rcept_dt"].astype(str), format="%Y%m%d", errors="coerce")
    vis = m[filed <= as_of_ts]
    if vis.empty:
        return None
    fvis = pd.to_datetime(vis["rcept_dt"].astype(str), format="%Y%m%d", errors="coerce")
    row = vis.loc[fvis.idxmax()]
    ni = row.get("net_income"); eq = row.get("equity")
    if pd.notna(ni) and pd.notna(eq) and float(eq) > 0:
        return float(ni) / float(eq)
    return None


def _kr_mom_12_1(px, code, as_of_ts):
    """12-1개월 momentum(최근 1개월 skip) — steel cs_mom_12_1_reversal selection 용. 가격 PIT.

    p[t-21d]/p[t-252d]-1. reversal 신호이므로 sleeve_signals 부호 −1(낮을수록 쌈). 결측 None.
    """
    if code not in px.columns:
        return None
    s = px[code][px.index <= as_of_ts].dropna()
    if len(s) < 252:
        return None
    p_recent = float(s.iloc[-21]); p_base = float(s.iloc[-252])
    return (p_recent / p_base - 1.0) if p_base > 0 else None


_KR_ROT_CACHE = None


def _kr_rotation_apply(subw, as_of_ts):
    """산업간 비중 tilt — ★자문 3R 수렴: 분기 동시 신호 tilt → **정적 틸트**(회전 0).

    자문(claude 3R): 거시 타이밍 로테이션은 표본외 소멸 → 시클리컬 구조 프리미엄을 정적 OW 로
    재표현. 신호 z 제거(분기 변동 X). kappa(수축 IC robust, _sleeve_rotation_kr) 비례 고정 OW.
    위험기여 근사: 시클리컬 묶음(steel/chemical/refining=경기민감 1베팅, 상관 高 합산 한도 +2.5%p)
    + telecom(방어 1베팅 +1.5%p). ⚠️자문 경고 박제: 타이밍-순진(불경기 드로다운 집중), 전표본 vol
    이 수축 조건부위험 과소(경기민감 상관은 아플 때 치솟음). 폐기조건=확장패널 재추정 무너지면.
    """
    global _KR_ROT_CACHE
    import pandas as pd
    try:
        if _KR_ROT_CACHE is None:
            import sys
            import json
            rd = str((_IND_KR / "_rotation").resolve())
            if rd not in sys.path:
                sys.path.insert(0, rd)
            import _sleeve_rotation_kr as ROT
            res = json.load(open(_IND_KR / "_rotation" / "_sleeve_rotation_kr_results.json",
                                 encoding="utf-8"))
            _KR_ROT_CACHE = (ROT, res["kappa"], float(res["meta"]["s_rot_calib"]))
        _ROT, kappa, _s = _KR_ROT_CACHE
        base_w = pd.Series(subw)
        if base_w.sum() <= 0:
            return subw
        base_w = base_w / base_w.sum()
        w = base_w.copy()
        for grp, ow in ((["steel", "chemical", "refining"], 0.025), (["telecom"], 0.015)):
            kpos = {i: kappa.get(i, 0.0) for i in grp if kappa.get(i, 0.0) > 0 and i in base_w.index}
            ks = sum(kpos.values())
            if ks <= 0:
                continue
            for i, k in kpos.items():
                w[i] = base_w[i] + ow * (k / ks)   # 정적 OW(신호 z 무관), kappa 비례 배분
        w = w.clip(lower=0.0); w = w / w.sum()
        return {i: float(w[i]) for i in w.index if w[i] > 1e-9}
    except Exception as exc:
        logger.warning("kr static tilt: %r", exc)
        return subw


# ★study horizon holding(개월): selection 신호의 forward horizon(within-residual capsule 측정).
#   semi pbr_z__24M_value(BY 생존 유일, 3M/6M/12M 미생존) → 24M / aitech·steel cs_*_y12m → 12M.
#   종목 집합을 그 기간 유지(분기 리밸런싱해도 동일) = study 장기 신호를 단기로 평가하던 mismatch 해소
#   (rotation 1M/3M 버그 §4-3 와 동형). _KR_SEL_CACHE = run_backtest 시작 시 clear(시계열 상태).
_KR_SEL_HORIZON = {"semiconductor": 24, "aitech": 12, "steel": 12}
_KR_SEL_CACHE: dict = {}


def _bt_fundamentals(ed_t, tk, as_of):
    """edgar long → PIT Fundamentals(filed≤as_of, 최신순). (검증된 로직, gate 전 universe 공급)."""
    from stock.contracts import Fundamentals, FilingSource
    m = ed_t[ed_t["filed"] <= as_of]
    if m.empty:
        return []
    funds = []
    for end_d, grp in m.groupby("end"):
        cvals = {}
        for concept, cg in grp.groupby("concept"):
            cvals[concept] = float(cg.sort_values("filed")["val"].iloc[-1])
        cfiled = grp["filed"].max().to_pydatetime()
        fp = grp["fp"].dropna().iloc[-1] if grp["fp"].notna().any() else "FY"
        op = cvals.get("op_income"); da = cvals.get("dep_amort")
        ebitda = (op + da) if (op is not None and da is not None) else None
        cfo = cvals.get("cfo"); capex = cvals.get("capex")
        fcf = (cfo - abs(capex)) if (cfo is not None and capex is not None) else cfo
        td = (cvals.get("lt_debt") or 0.0) + (cvals.get("st_debt") or 0.0) or None
        equity = cvals.get("equity")
        funds.append(Fundamentals(
            ticker=tk, fiscal_period=f"{end_d.year}{fp}", filing_timestamp=cfiled,
            source=FilingSource.EDGAR_XBRL, currency="USD", revenue=cvals.get("revenues"),
            operating_income=op, ebit=op, net_income=cvals.get("net_income"), ebitda=ebitda,
            free_cash_flow=fcf, depreciation_amortization=da, capital_expenditure=capex,
            total_debt=td, cash_and_equivalents=cvals.get("cash"),
            shareholders_equity=equity, book_value=equity, outstanding_shares=cvals.get("shares")))
    funds.sort(key=lambda f: f.filing_timestamp, reverse=True)
    return funds


def _bt_metric_panel(funds_by, mcap_by, signs, ttm=False):
    """signs 기반 metric panel. ttm=True → ep_yield/ev_ebitda 를 최근 4분기 합(저빈도 신호 안정,
    forecasting 정의 정합). net_issuance 는 주식수 변화율이라 ttm 불가(5분기 추적 유지)."""
    panel = {m: {} for m in signs}
    for t, funds in funds_by.items():
        if not funds:
            continue
        cur = funds[0]; mc = mcap_by.get(t)
        if not mc:
            continue
        if "pbr" in panel and cur.book_value:
            panel["pbr"][t] = mc / cur.book_value
        if "ev_ebitda" in panel and cur.ebitda:
            nd = (cur.total_debt or 0) - (cur.cash_and_equivalents or 0)
            eb = sum(f.ebitda or 0 for f in funds[0:4]) if (ttm and len(funds) >= 4) else cur.ebitda
            if eb:
                panel["ev_ebitda"][t] = (mc + nd) / eb
        if "ep_yield" in panel and cur.net_income:
            ni = sum(f.net_income or 0 for f in funds[0:4]) if (ttm and len(funds) >= 4) else cur.net_income
            panel["ep_yield"][t] = ni / mc
        if "net_issuance" in panel and len(funds) > 4 and cur.outstanding_shares:
            old = funds[4].outstanding_shares
            if old:
                panel["net_issuance"][t] = cur.outstanding_shares / old - 1.0
    return panel


def _bt_us_picks(as_of, ind_data, etf_on, real_rate_z=None):
    """us_stock 내부 종목 비중(Σ=1, gate 전) — 업종분해(portfolio_decompose)+종목선택(construction).

    real_rate_z: as_of 시점 real_rate z-score → decompose_weight factor_z 로 전달(study weight_rules
        배선: defensive 비중 보간). None=study 보간 미적용=cap byte-identical(off 불변식).
    """
    import pandas as pd
    from datetime import datetime
    from stock.contracts import MarketQuote
    from stock.construction import build_sleeve_decisions
    from stock.sleeve_signals import signs_for
    from core.portfolio_decompose import decompose_weight
    as_of_dt = datetime.combine(pd.Timestamp(as_of).date(), datetime.min.time())
    mktcaps, sleeve_picks, ind_universe = {}, {}, {}
    for name in ("cyclical", "defensive", "mega_tech"):
        px, ed, tickers = ind_data[name]
        funds_by, quote_by, mcap_by = {}, {}, {}
        for tk in tickers:
            if tk not in px.columns:
                continue
            funds = _bt_fundamentals(ed[ed.ticker == tk], tk, as_of)
            if not funds or not funds[0].outstanding_shares:
                continue
            s = px[tk][px.index <= as_of].dropna()
            if s.empty:
                continue
            price = float(s.iloc[-1]); mc = funds[0].outstanding_shares * price
            if mc <= 0:
                continue
            funds_by[tk] = funds
            quote_by[tk] = MarketQuote(ticker=tk, as_of=as_of_dt, price=price, market_cap=mc)
            mcap_by[tk] = mc
        mktcaps[name] = sum(mcap_by.values())
        ind_universe[name] = list(mcap_by.keys())   # ★W6: 업종 전체 유효 universe(선택 전) = 선택alpha 분모
        signs = signs_for(name)
        _def_meas = (name == "defensive" and not etf_on)   # ★Phase A: defensive 픽 측정(ttm+tercile)
        panel = _bt_metric_panel(funds_by, mcap_by, signs, ttm=_def_meas) if signs else {}
        if _def_meas:
            # ★DEF-2 quality(div×op) = 종목선택 측정(etf_on=False) 전용. 실 백테스트(etf_on=True=ETF
            #   라우팅)는 종목선택 미수행 → 주입 불요(measure.load 오버헤드 회피, byte-identical).
            _bt_add_def_quality(panel, mcap_by, as_of)
        override = etf_pk = None
        if name == "mega_tech":
            override = {"mega_tech": "EW"}
        elif name == "defensive" and etf_on:
            override = {"defensive": "ETF"}
            etf_pk = {"defensive": {"ticker": "XLP", "aum": 1.5e10, "holdings_source": "yfinance"}}
        # ★sector-neutral demean = defensive 한정. study 근거: defensive 는 sub-sector sign flip
        #   (dividend_yield staples↔utilities 부호반전) → sector-neutral 필수. cyclical 은 cross-sector
        #   value(에너지/금융/소재 업종째 cheapness)가 alpha원 → sector demean 이 제거(파이프 실측
        #   .p4-sector-pipe: cyclical OFF t2.22 > ON t1.01). mega_tech=basket(무관).
        sectors = _bt_us_sectors(name) if name == "defensive" else None
        sel_cfg = None
        if _def_meas:   # ★tercile EW (defensive 측정 전용): top_k 집중 대신 상위 1/3 균등 + sector-neutral
            from stock.cross_sectional_selection import SelectionConfig
            sel_cfg = SelectionConfig(tercile_enabled=True, demean_by_sector=True)
        try:
            decs = build_sleeve_decisions(name, panel, mcap_by, funds_by, quote_by,
                                          deterministic_no_llm=True, etf_fallback_routing=override,
                                          etf_picks=etf_pk, sectors=sectors, config=sel_cfg)
        except Exception as exc:
            logger.warning("bt us/%s build_sleeve_decisions: %r", name, exc); decs = []
        picks = {}
        for dd in decs:
            tk = dd.get("ticker") or (dd.get("trade_params") or {}).get("ticker")
            tw = float(dd.get("target_weight") or 0)
            if tk and tw > 0:
                picks[tk] = tw
        sleeve_picks[name] = picks
    # ★W3: real_rate z 주어지면 study weight_rules 보간(defensive 비중), 아니면 cap byte-identical.
    fz = {"real_rate": float(real_rate_z)} if real_rate_z is not None else None
    subw = decompose_weight("us_stock", 1.0, mktcaps, method="cap", factor_z=fz)
    holdings, ind_holdings = {}, {}
    for name, picks in sleeve_picks.items():
        sw = subw.get(name, 0.0); tot = sum(picks.values())
        if sw <= 0 or tot <= 0:
            ind_holdings[name] = {}; continue
        ih = {tk: sw * (w / tot) for tk, w in picks.items()}
        ind_holdings[name] = ih
        for tk, w in ih.items():
            holdings[tk] = holdings.get(tk, 0.0) + w
    tot = sum(holdings.values())
    if tot > 0:
        holdings = {tk: w / tot for tk, w in holdings.items()}
        ind_holdings = {n: {tk: w / tot for tk, w in ih.items()} for n, ih in ind_holdings.items()}
    return holdings, ind_holdings, ind_universe


def _bt_kr_picks(as_of, kr_data):
    """kr_stock 내부 종목/ETF 비중(Σ=1, gate 전).

    ★robust 섹터(sleeve_signals 한국 부호 등록=semi/aitech, within-residual-v2 BY생존+ρ≥0.25)
      = study cheapness(pbr z rank) selection 경로. 약섹터 9곳 = ETF/EW fallback(미국 defensive
      교훈: 약팩터는 capped-EW 에서 죽음). PIT pbr=mktcap/_kr_pit_equity(rcept_dt≤as_of).
    """
    import pandas as pd
    from stock.construction import build_sleeve_decisions, _ETF_FALLBACK_ROUTING
    from stock.sleeve_signals import signs_for
    from core.portfolio_decompose import decompose_weight
    as_of_ts = pd.Timestamp(as_of)
    mktcaps, sleeve_picks, ind_universe = {}, {}, {}
    for name in _KR_SUB:
        if name not in kr_data:
            continue
        px, uni, dart = kr_data[name]
        mcap_by = {}
        for _, row in uni.iterrows():
            code = str(row["Code"])
            if not bool(row.get("pass_floor", True)):
                continue
            mc_latest = float(row.get("Marcap") or 0)
            if mc_latest <= 0 or code not in px.columns:
                continue
            s_all = px[code].dropna(); s_asof = s_all[s_all.index <= as_of_ts]
            if s_asof.empty or s_all.empty:
                continue
            pl = float(s_all.iloc[-1]); pa = float(s_asof.iloc[-1])
            mcap_by[code] = mc_latest * (pa / pl) if pl > 0 else mc_latest
        if not mcap_by:
            sleeve_picks[name] = {}; mktcaps[name] = 0.0; ind_universe[name] = []; continue
        mktcaps[name] = sum(mcap_by.values())
        ind_universe[name] = list(mcap_by.keys())   # ★W6: 업종 전체 유효 universe(선택 전) = 선택alpha 분모
        signs = signs_for(name)   # ★study 부호 등록된 robust 섹터 = cheapness 경로
        if signs and dart is not None:
            _h = _KR_SEL_HORIZON.get(name, 3)
            _prev = _KR_SEL_CACHE.get(name)
            if _prev is not None and (as_of_ts - _prev[0]).days < _h * 30 - 10:
                decs = _prev[1]   # ★study horizon holding(24M/12M): 종목 유지(장기 신호 단기평가 회피)
            else:
                panel = {m: {} for m in signs}
                for code in mcap_by:
                    if "pbr" in panel:
                        eq = _kr_pit_equity(dart, code, as_of_ts)
                        if eq:
                            panel["pbr"][code] = mcap_by[code] / eq
                    if "mom_12_1" in panel:
                        mom = _kr_mom_12_1(px, code, as_of_ts)
                        if mom is not None:
                            panel["mom_12_1"][code] = mom
                    if "roe" in panel:
                        roe = _kr_pit_roe(dart, code, as_of_ts)
                        if roe is not None:
                            panel["roe"][code] = roe
                try:
                    # etf_fallback_routing 미주입 → env ETF_FALLBACK off → cheapness(횡단면 pbr z rank)
                    decs = build_sleeve_decisions(name, panel, mcap_by, {}, {}, deterministic_no_llm=True)
                    _KR_SEL_CACHE[name] = (as_of_ts, decs)
                except Exception as exc:
                    logger.warning("bt kr/%s cheapness: %r", name, exc); decs = []
        else:
            routing = _ETF_FALLBACK_ROUTING.get(name, "EW")
            etf_pk = {name: _KR_ETF_PICKS[name]} if (routing == "ETF" and name in _KR_ETF_PICKS) else None
            try:
                decs = build_sleeve_decisions(name, {}, mcap_by, {}, {}, deterministic_no_llm=True,
                                              etf_fallback_routing={name: routing}, etf_picks=etf_pk)
            except Exception as exc:
                logger.warning("bt kr/%s build_sleeve_decisions: %r", name, exc); decs = []
        picks = {}
        for dd in decs:
            tk = dd.get("ticker") or (dd.get("trade_params") or {}).get("ticker")
            tw = float(dd.get("target_weight") or 0)
            if tk and tw > 0:
                picks[tk] = tw
        sleeve_picks[name] = picks
    subw = decompose_weight("kr_stock", 1.0, mktcaps, method="cap")
    subw = _kr_rotation_apply(subw, as_of_ts)   # ★rotation 신호 산업간 tilt(분기 3M, PIT)
    holdings, ind_holdings = {}, {}
    for name, picks in sleeve_picks.items():
        sw = subw.get(name, 0.0); tot = sum(picks.values())
        if sw <= 0 or tot <= 0:
            ind_holdings[name] = {}; continue
        ih = {tk: sw * (w / tot) for tk, w in picks.items()}
        ind_holdings[name] = ih
        for tk, w in ih.items():
            holdings[tk] = holdings.get(tk, 0.0) + w
    tot = sum(holdings.values())
    if tot > 0:
        holdings = {tk: w / tot for tk, w in holdings.items()}
        ind_holdings = {n: {tk: w / tot for tk, w in ih.items()} for n, ih in ind_holdings.items()}
    return holdings, ind_holdings, ind_universe


def _bt_qret(tk, d, nxt, sources):
    """tk 의 (d,nxt] 단순수익 — 가격 소스 리스트 탐색."""
    for px in sources:
        if tk in px.columns:
            seg = px[tk][(px.index > d) & (px.index <= nxt)].dropna()
            base = px[tk][px.index <= d].dropna()
            if not seg.empty and not base.empty:
                return float(seg.iloc[-1] / base.iloc[-1] - 1.0)
    return None


def _gate_judge_filter(picks, sleeve, sleeve_w, nav, all_weights, *,
                       judge_hook, router, corr_matrix, sector_weight):
    """★orphan 해소 핵심: construction 종목 비중 → 종목마다 judge_hook + GatedOrderRouter.submit
    (via_gate, risk_gate cap/corr 경유) → 통과분만 (judge 감쇠 반영) 비중 반환.

    run_one_cycle 의 sleeve-레벨 gate/judge 경유를 종목 레벨로 확장(동일 프로덕션 모듈).
    ★sector_weight = 호출자가 산출한 '그 종목 업종의 포트 비중'(order_assembly 정신, CODEMAP:174 order
      path). 자산군 전체(주식 합산)가 아니라 업종 단위 = max_weight_sector(30%) 정확 적용.
    avg_correlation = sleeve-pair 상관(_compute_multiasset_corr_sector, corr_matrix 없으면 0)."""
    from core.risk_gate import VerdictType
    avg_corr, _ = _compute_multiasset_corr_sector(all_weights, sleeve, corr_matrix=corr_matrix)
    out = {}; n_rej = 0; rej_rules = []; judge_atten = []   # ⑥게이트사유 ⑨judge감쇠
    for tk, w in picks.items():
        cur_w = sleeve_w * w          # 종목 전체 포트 비중
        proposed = nav * cur_w
        a = _apply_judge_hook(judge_hook, sleeve=sleeve, proposed_size=proposed, l1_size=1.0)
        judge_atten.append(a)
        proposed_j = proposed * a
        try:
            v = router.submit(
                {"action": "buy", "asset": tk, "trade_value": proposed_j},
                cycle_id=f"bt-{sleeve}-{tk}", via_gate=True, action="buy",
                proposed_size=proposed_j, current_weight=cur_w, sector_weight=sector_weight,
                avg_correlation=avg_corr, nav=nav, position_pnl_pct=0.0, holding_days=0,
                ytd_realized_pnl_pct=0.0, daily_loss_pct=0.0)
        except Exception as exc:
            logger.warning("gate submit %s/%s: %r", sleeve, tk, exc); continue
        if v.verdict != VerdictType.REJECTED:
            out[tk] = w * a   # judge 감쇠 반영(down-only)
        else:
            n_rej += 1
            rr = getattr(v, "triggered_rules", None) or getattr(v, "reason", None) or "unknown"
            if isinstance(rr, (list, tuple)):
                rej_rules.extend(rr)
            else:
                rej_rules.append(str(rr))
    return out, n_rej, rej_rules, judge_atten


def run_backtest(start="2017-01-01", end="2026-03-31", *, etf_on=True, kr_on=True):
    """프로덕션 경로 시계열 백테스트. allocate(as_of)→업종분해→construction→종목 gate/judge 경유→회계.

    ⛔ 종목 결정마다 GatedOrderRouter.submit(via_gate)+judge_hook 경유(orphan 0). 회계=통과분 비중.
    """
    # ★거시배분 substrate on: regime→weights 동적 배분 경로 개통.
    #   미설정 시 collect_market_state 내부 macro_view=None(is_r15_enabled 게이트)
    #   → allocate(macro_view=None) → 정적 BL prior(36분기 배분 동일=regime 미반영).
    #   "true"=is_r15_enabled()("1/true/on/yes")+orchestrator:158(=="true") 둘 다 통과
    #   (두 게이트 값비교 불일치 회피). 구 별도드라이버(.p3:312)는 "on"만 켜 orchestrator 게이트 누락.
    os.environ["INV_R15_WEIGHTS"] = "true"
    import numpy as np
    import pandas as pd
    from datetime import date
    from core.portfolio_orchestrator import PortfolioOrchestrator
    from core.coin_track_macro import CoinTrackWithMacro
    from core.data.sleeve_returns import _default_yf_source, SLEEVE_TICKERS
    from core.risk_gate import GatedOrderRouter
    from core.brain.regime_classifier import RegimeClassifier
    from core.brain.fred_adapter import RealFredAdapter
    from core.brain.macro_schema import Bloc
    from backtest.diagnostics import nw_hac_tstat, block_bootstrap_ci, four_layer_metrics

    print(f"[프로덕션 백테스트] {start}~{end} run_multiasset.py 보수 경로 "
          f"(allocate→업종분해→construction→종목 gate/judge 경유→회계)")
    ind_data = {n: _bt_load_us(n) for n in ("cyclical", "defensive", "mega_tech")}
    kr_data = {}
    _KR_SEL_CACHE.clear()   # ★horizon holding 캐시 초기화(이전 run 상태 격리)
    if kr_on:
        for n in _KR_SUB:
            try:
                kr_data[n] = _bt_load_kr(n)
            except Exception as exc:
                logger.warning("KR load %s: %r", n, exc)

    orch = PortfolioOrchestrator()
    ct = CoinTrackWithMacro(macro_orchestrator=orch, macro_enabled=True)
    rc = RegimeClassifier(usd_adapter=RealFredAdapter())
    router = GatedOrderRouter()   # ★프로덕션 risk_gate (매 종목 submit 경유)
    # ★W3 산업간 배분: real_rate z 시계열(PIT) 1회 구성 → as_of 별 조회로 _bt_us_picks 주입.
    #   None(FRED unavailable) 이면 decompose factor_z=None = cap byte-identical(graceful).
    rr_z_series = _bt_real_rate_z(end)
    if rr_z_series is not None:
        print(f"[W3 배선] real_rate z 시계열 n={len(rr_z_series)} "
              f"{rr_z_series.index.min().date()}~{rr_z_series.index.max().date()} "
              f"→ defensive 업종 weight 보간(cap fallback graceful)")

    cols = list(SLEEVE_TICKERS.keys())
    px = _default_yf_source([SLEEVE_TICKERS[s] for s in cols], date(2007, 1, 1), date.fromisoformat(end))
    px = px.rename(columns={v: k for k, v in SLEEVE_TICKERS.items()})
    rets = np.log(px.astype(float)).diff()
    us_src = [ind_data[n][0] for n in ("cyclical", "defensive", "mega_tech")]
    if etf_on:
        ep = _default_yf_source(["XLP"], date(2007, 1, 1), date.fromisoformat(end))
        us_src.append(ep)
    kr_src = [kr_data[n][0] for n in _KR_SUB if n in kr_data]
    if kr_on and kr_data:
        import FinanceDataReader as fdr
        ks = {}
        for code in sorted({v["ticker"] for v in _KR_ETF_PICKS.values()}):
            try:
                ks[code] = fdr.DataReader(code, "2018-01-01", end)["Close"]
            except Exception as exc:
                logger.warning("KODEX %s FDR: %r", code, exc)
        if ks:
            kep = pd.DataFrame(ks); kep.index = pd.to_datetime(kep.index)
            kep.columns = [str(c) for c in kep.columns]; kr_src.append(kep)

    rebal = [d for d in pd.date_range(start, end, freq="QE") if d >= rets.index[0]]
    nav = 1.0
    us_alpha_seq, kr_alpha_seq = [], []
    n_gate_submit = n_gate_rej = n_judge = 0
    OOS_FROM = pd.Timestamp("2022-01-01")
    wf = {"IS": {"port": 0.0, "n": 0}, "OOS": {"port": 0.0, "n": 0}}
    navs = [1.0]; rows = []
    from collections import defaultdict
    sleeve_contrib = defaultdict(float)   # 자산군별 누적 기여(Σ ws·use)
    sleeve_ret_hist = defaultdict(list)   # 자산군별 분기수익(Sharpe)
    ind_ret_hist = defaultdict(list)      # 산업별 통과분 분기수익
    ind_sel_alpha = defaultdict(list)     # 산업별 종목선택 alpha(선택가중 vs 업종 EW)
    port_seq = []                         # 전체 분기수익(Sharpe)
    reg_sleeve_ret = defaultdict(lambda: defaultdict(list))  # ①regime→자산→실측수익(신호 예측력)
    reg_sleeve_w = defaultdict(lambda: defaultdict(list))    # ②regime→자산→우리비중(배분 기준)
    ind_w_hist = defaultdict(list)        # ④산업→배분비중(gate 전, 산업간 배분 진단)
    gate_rej_reasons = []                  # ⑥게이트 거부 사유(triggered_rules)
    judge_atten_all = []                  # ⑨judge 감쇠계수(현 baseline=1.0)
    conc_hist = defaultdict(list)          # ⑦종목 집중도(통과수, 최대비중)

    # judge hook: down-only 감쇠(현 결정론 baseline=fail-open a=1.0, 경유는 live=orphan 0)
    def judge_hook(*, sleeve, proposed_size, l1_size=1.0):
        nonlocal n_judge
        n_judge += 1
        return {"size_mult": 1.0, "l1_size": l1_size}   # 결정론 baseline(향후 regime down-only)

    prev_w: dict = {}   # ⑮거래비용 turnover 기준(직전 분기 종목/sleeve 비중)
    for i in range(len(rebal) - 1):
        d, nxt = rebal[i], rebal[i + 1]
        # ★거시배분 = 프로덕션 경로 coin_track_macro.collect_market_state(내부 allocate 호출,
        #   CODEMAP:168). FRED 캐시 적재 → 이후 classify 작동. allocate 직접호출=우회(드리프트) 제거.
        regime_lbl = "?"; krw_lbl = "?"; w = {}; gated = {}; kgated = {}
        mv_conf = None; macro_status = "?"; mv_gz = None; mv_iz = None
        try:
            state = ct.collect_market_state(as_of=pd.Timestamp(d))
            w = state.raw_external_data.get("macro_weights", {}) or {}
            macro_status = getattr(state, "macro_status", None) or \
                (state.raw_external_data.get("macro_status") if hasattr(state, "raw_external_data") else "?")
            mv = rc.classify(pd.Timestamp(d))   # collect 후 FRED 캐시 hit
            if mv is not None and getattr(mv, "regimes", None):
                est = mv.regime(Bloc.USD) or next(iter(mv.regimes.values()), None)
                if est is not None:
                    regime_lbl = getattr(est.regime_now, "value", str(est.regime_now))
                    mv_conf = getattr(est, "confidence_now", None)  # ⑯ RegimeEstimate 필드명=confidence_now
                    _ev = getattr(est, "evidence", None) or {}       # ⑪ Investment Clock 축(분류기 경계 검증)
                    mv_gz = _ev.get("growth_z"); mv_iz = _ev.get("inflation_z")  # classifier 키=inflation_z
                kest = mv.regime(Bloc.KRW)
                if kest is not None:
                    krw_lbl = getattr(kest.regime_now, "value", str(kest.regime_now))
            else:
                logger.warning("[BT %s] mv=None/regimes 비어있음 → 거시배분 중립 prior", d.date())
        except Exception as exc:
            logger.warning("%s collect_market_state: %r", d.date(), exc)
        tot = sum(w.values())
        if tot > 0 and abs(tot - 1.0) > 1e-6:
            w = {k: v / tot for k, v in w.items()}

        period = rets[(rets.index > d) & (rets.index <= nxt)]
        sret = {s: float(np.expm1(period[s].dropna().sum()))
                for s in period.columns if period[s].notna().any()}

        # us_stock: 업종분해+종목선택 → ★종목 gate/judge 경유 → 통과분
        us_ret = spy_ret = None
        w_us = float(w.get("us_stock", 0))
        if w_us > 0:
            # ★W3: as_of 시점 real_rate z(PIT, 당일 이하 최근) → defensive 업종 weight 보간.
            rr_z = None
            if rr_z_series is not None:
                _prior = rr_z_series[rr_z_series.index <= d]
                rr_z = float(_prior.iloc[-1]) if len(_prior) else None
            _picks, ind_h, ind_uni = _bt_us_picks(d, ind_data, etf_on, real_rate_z=rr_z)
            gated = {}; us_ind_g = {}
            for ind_name, ih in ind_h.items():        # cyclical/defensive/mega_tech 업종 단위
                if not ih:
                    continue
                sec_w = w_us * sum(ih.values())        # ★업종 포트 비중 = sector_weight
                ind_w_hist[f"us:{ind_name}"].append(sec_w)   # ④산업간 배분비중
                g, nrej, rr, ja = _gate_judge_filter(ih, "us_stock", w_us, nav, w, judge_hook=judge_hook,
                                                     router=router, corr_matrix=None, sector_weight=sec_w)
                n_gate_submit += len(ih); n_gate_rej += nrej
                gate_rej_reasons.extend(rr); judge_atten_all.extend(ja)
                gated.update(g)
                if g:
                    us_ind_g[ind_name] = dict(g)
            tg = sum(gated.values())
            if tg > 0:
                gated = {tk: x / tg for tk, x in gated.items()}
                us_ret = sum((_bt_qret(tk, d, nxt, us_src) or 0.0) * x for tk, x in gated.items())
                conc_hist["us"].append((len(gated), max(gated.values()) if gated else 0.0))  # ⑦집중도
                # ★산업별 통과분 실측수익 + 종목선택 alpha(선택가중 − 업종 EW)
                for ind_name, g in us_ind_g.items():
                    gt2 = sum(g.values())
                    if gt2 <= 0:
                        continue
                    sel = sum((_bt_qret(tk, d, nxt, us_src) or 0.0) * (gv / gt2) for tk, gv in g.items())
                    # ★W6: 선택alpha 분모 = 업종 전체 universe EW(선택 전 종목 포함), 비면 통과 g fallback
                    _uni = ind_uni.get(ind_name) or list(g)
                    ew = float(np.mean([(_bt_qret(tk, d, nxt, us_src) or 0.0) for tk in _uni]))
                    ind_ret_hist[f"us:{ind_name}"].append(sel)
                    ind_sel_alpha[f"us:{ind_name}"].append(sel - ew)
        spy_ret = sret.get("us_stock")

        # kr_stock: 동일 경유
        kr_ret = ewy_ret = None
        w_kr = float(w.get("kr_stock", 0))
        if kr_on and kr_data and w_kr > 0:
            _kpicks, kind_h, kind_uni = _bt_kr_picks(d, kr_data)
            kgated = {}; kr_ind_g = {}
            for ind_name, ih in kind_h.items():       # KR 업종 단위
                if not ih:
                    continue
                sec_w = w_kr * sum(ih.values())        # ★업종 포트 비중
                ind_w_hist[f"kr:{ind_name}"].append(sec_w)   # ④산업간 배분비중
                g, knrej, krr, kja = _gate_judge_filter(ih, "kr_stock", w_kr, nav, w, judge_hook=judge_hook,
                                                        router=router, corr_matrix=None, sector_weight=sec_w)
                n_gate_submit += len(ih); n_gate_rej += knrej
                gate_rej_reasons.extend(krr); judge_atten_all.extend(kja)
                kgated.update(g)
                if g:
                    kr_ind_g[ind_name] = dict(g)
            tg = sum(kgated.values())
            if tg > 0:
                kgated = {tk: x / tg for tk, x in kgated.items()}
                kr_ret = sum((_bt_qret(tk, d, nxt, kr_src) or 0.0) * x for tk, x in kgated.items())
                conc_hist["kr"].append((len(kgated), max(kgated.values()) if kgated else 0.0))  # ⑦집중도
                # ★산업별 통과분 실측수익 + 종목선택 alpha
                for ind_name, g in kr_ind_g.items():
                    gt2 = sum(g.values())
                    if gt2 <= 0:
                        continue
                    sel = sum((_bt_qret(tk, d, nxt, kr_src) or 0.0) * (gv / gt2) for tk, gv in g.items())
                    # ★W6: 선택alpha 분모 = 업종 전체 universe EW(선택 전), 비면 통과 g fallback
                    _uni = kind_uni.get(ind_name) or list(g)
                    ew = float(np.mean([(_bt_qret(tk, d, nxt, kr_src) or 0.0) for tk in _uni]))
                    ind_ret_hist[f"kr:{ind_name}"].append(sel)
                    ind_sel_alpha[f"kr:{ind_name}"].append(sel - ew)
        ewy_ret = sret.get("kr_stock")

        # 포트폴리오 수익(통과분 반영) — 비주식 sleeve = 대표자산
        port = 0.0
        for s in sret:
            ws = float(w.get(s, 0))
            if s == "us_stock":
                use = us_ret if us_ret is not None else sret["us_stock"]
            elif s == "kr_stock":
                use = kr_ret if kr_ret is not None else sret["kr_stock"]
            else:
                use = sret[s]
            port += ws * use
            if ws > 0:
                sleeve_contrib[s] += ws * use      # 자산군별 누적 기여(Σ ws·분기수익)
                sleeve_ret_hist[s].append(use)     # 자산군별 분기수익(Sharpe)
        if not w:
            port = float(np.mean(list(sret.values()))) if sret else 0.0
        # ★⑮거래비용: 분기 turnover × 자산군 cost(한국 STT+수수료 ≈0.25% / 미국·ETF·coin ≈0.07%,
        #   편도 근사). rotation 산업 tilt + selection 종목교체 회전 잠식 반영 → 진짜 순 alpha(§4-3).
        cur_w = {}
        for tk, x in gated.items():
            cur_w[("us", tk)] = w_us * x
        for tk, x in kgated.items():
            cur_w[("kr", tk)] = w_kr * x
        for s in sret:
            if s not in ("us_stock", "kr_stock"):
                cur_w[("sl", s)] = float(w.get(s, 0))
        tcost = sum(abs(cur_w.get(k, 0.0) - prev_w.get(k, 0.0)) * (0.0025 if k[0] == "kr" else 0.0007)
                    for k in set(cur_w) | set(prev_w))
        port -= tcost
        prev_w = cur_w
        nav *= (1 + port)
        navs.append(nav)
        port_seq.append(port)
        # ①②regime별 자산 실측수익 + 우리 비중 (신호 예측력 / 배분 기준 진단)
        for s in sret:
            reg_sleeve_ret[regime_lbl][s].append(sret[s])
            reg_sleeve_w[regime_lbl][s].append(float(w.get(s, 0)))

        if us_ret is not None and spy_ret is not None:
            us_alpha_seq.append(us_ret - spy_ret)
        if kr_ret is not None and ewy_ret is not None:
            kr_alpha_seq.append(kr_ret - ewy_ret)
        seg = "OOS" if d >= OOS_FROM else "IS"
        wf[seg]["port"] += port; wf[seg]["n"] += 1
        rows.append((nxt.date().isoformat(), regime_lbl, round(port, 4), round(nav, 3)))
        # ★분기별 상세 로깅 (regime/거시배분/통과종목 — 원인 파악용)
        wstr = " ".join(f"{k}={v:.2f}" for k, v in sorted(w.items(), key=lambda x: -x[1]) if v > 0.005)
        conf_s = f"{mv_conf:.2f}" if mv_conf is not None else "?"
        gz_s = f"{mv_gz:+.2f}" if mv_gz is not None else "?"
        iz_s = f"{mv_iz:+.2f}" if mv_iz is not None else "?"
        logger.info(
            "[BT %s] regime USD=%s/KRW=%s conf=%s gz=%s iz=%s macro=%s | w{%s} | "
            "us통과=%d kr통과=%d rej누적=%d | port=%+.4f nav=%.3f",
            nxt.date(), regime_lbl, krw_lbl, conf_s, gz_s, iz_s, macro_status, wstr,
            len(gated), len(kgated), n_gate_rej, port, nav)

    yrs = max((rebal[-1] - rebal[0]).days / 365.25, 0.1)
    cagr = lambda v: v ** (1 / yrs) - 1
    print(f"\n리밸런스 {len(rows)}회 | NAV {nav:.3f} (CAGR {cagr(nav):+.2%})")
    print(f"[★orphan 0 검증] GatedOrderRouter.submit 종목 경유 {n_gate_submit}회 "
          f"(REJECTED {n_gate_rej}) | judge_hook 경유 {n_judge}회 | router.bypassed={router.bypassed_attempts}")
    for lbl, seq in [("us9-SPY", us_alpha_seq), ("kr9-EWY", kr_alpha_seq)]:
        if len(seq) >= 4:
            t, n, lags = nw_hac_tstat(seq)
            lo, mu, hi = block_bootstrap_ci(seq)
            sig = "유의" if (abs(t) > 1.96 and lo * hi > 0) else "비유의"
            print(f"  {lbl}: 분기평균 {mu:+.4f} NW-HAC t={t:+.2f}(n={n}) CI[{lo:+.4f},{hi:+.4f}] {sig}")
    print(f"[walk-forward] IS n={wf['IS']['n']} Σ{wf['IS']['port']:+.3f} | "
          f"OOS n={wf['OOS']['n']} Σ{wf['OOS']['port']:+.3f}")
    m = four_layer_metrics(navs, n_errors=0, n_stages_disconnected=0)
    print(f"[지표] MDD={m['max_drawdown']:.3f}")

    def _sharpe(seq):
        a = np.array(seq, dtype=float)
        return float(a.mean() / a.std() * np.sqrt(4)) if len(a) > 1 and a.std() > 1e-9 else 0.0
    print(f"[전체] 분기 Sharpe(연율)={_sharpe(port_seq):.2f} (n={len(port_seq)})")
    print("[자산군별 기여/Sharpe] (누적기여=Σ ws·분기수익, 저조순 ↑)")
    for s, c in sorted(sleeve_contrib.items(), key=lambda x: x[1]):
        h = sleeve_ret_hist[s]
        print(f"  {s:<10} 누적기여 {c:+.3f} | 분기평균 {np.mean(h):+.4f} Sharpe {_sharpe(h):+.2f} (n={len(h)})")
    print("[산업별 통과분 수익/종목선택alpha] (★W6: alpha=선택가중 − 업종 전체universe EW=선택가치, 저조순 ↑)")
    for ind in sorted(ind_ret_hist, key=lambda k: float(np.mean(ind_ret_hist[k]))):
        h = ind_ret_hist[ind]; sa = ind_sel_alpha.get(ind, [])
        sa_s = f"{np.mean(sa):+.4f}" if sa else "n/a"
        # ★자문검증(claude): selection alpha t-stat — |t|<2면 신호부재(노이즈), 트랩 인과 불요
        sa_t = (f"t={np.mean(sa)/(np.std(sa)/np.sqrt(len(sa))):+.2f}"
                if sa and len(sa) > 1 and np.std(sa) > 1e-9 else "t=n/a")
        print(f"  {ind:<16} 분기평균 {np.mean(h):+.4f} | 선택alpha {sa_s} ({sa_t}) Sharpe {_sharpe(h):+.2f} (n={len(h)})")
    print("[④산업간 배분] 산업: 평균배분비중 → 평균수익 (비중↑ vs 수익↑ 정합?)")
    for ind in sorted(ind_w_hist, key=lambda k: -float(np.mean(ind_w_hist[k]))):
        wv = float(np.mean(ind_w_hist[ind]))
        r = float(np.mean(ind_ret_hist[ind])) if ind_ret_hist.get(ind) else 0.0
        print(f"  {ind:<16} 평균비중 {wv:.3f} | 평균수익 {r:+.4f} (n={len(ind_w_hist[ind])})")
    print("[①②거시신호+배분 진단] regime별 (비중-수익 정렬corr>0=좋은자산에 무게 / 그 국면 최고수익 자산)")

    def _pearson(xs, ys):
        if len(xs) <= 2 or np.std(xs) < 1e-9 or np.std(ys) < 1e-9:
            return float("nan")
        return float(np.corrcoef(xs, ys)[0, 1])

    def _spearman(xs, ys):
        # numpy rank 기반 (scipy 미의존). 동률은 평균랭크.
        def _rank(a):
            a = np.asarray(a, dtype=float)
            order = a.argsort()
            r = np.empty(len(a), dtype=float)
            r[order] = np.arange(len(a), dtype=float)
            # 동률 평균랭크 보정
            _, inv, cnt = np.unique(a, return_inverse=True, return_counts=True)
            sums = np.zeros(len(cnt)); np.add.at(sums, inv, r)
            means = sums / cnt
            return means[inv]
        return _pearson(_rank(xs), _rank(ys))

    for reg in reg_sleeve_ret:
        srv = reg_sleeve_ret[reg]
        if not srv:
            continue
        items = [(s, float(np.mean(reg_sleeve_w[reg][s])), float(np.mean(srv[s]))) for s in srv]
        ws_ = [x[1] for x in items]; rs_ = [x[2] for x in items]
        corr = _pearson(ws_, rs_)
        n = len(next(iter(srv.values())))
        top = sorted(items, key=lambda x: -x[2])[:3]
        tops = ", ".join(f"{s}({r:+.3f}/w{wv:.2f})" for s, wv, r in top)
        print(f"  {reg:<12}(n={n}) 비중-수익corr={corr:+.2f} | 최고수익: {tops}")

    # ★W2 진단: coin 제외 ② corr 재측정 + 전체 sleeve 표 + Spearman (자문 R2 분기점)
    #   가설: coin(수익 최고/비중 최저) outlier 가 횡단면 corr 을 음으로 끄는가?
    #   주의(small-n): 횡단면 단위 = sleeve 수(7→coin제외 6), n_q=해당 regime 분기수.
    #   점추정 단정 금지 — 방향성 prior 로만 해석(SE 미부착, sleeve cross-section 매우 작음).
    print("[★W2 ②corr coin제외 재측정] (횡단면=sleeve 평균, coin in/out Pearson+Spearman)")
    for reg in reg_sleeve_ret:
        srv = reg_sleeve_ret[reg]
        if not srv:
            continue
        items = [(s, float(np.mean(reg_sleeve_w[reg][s])), float(np.mean(srv[s]))) for s in srv]
        n_q = len(next(iter(srv.values())))
        full_w = [x[1] for x in items]; full_r = [x[2] for x in items]
        noc = [x for x in items if x[0] != "coin"]
        noc_w = [x[1] for x in noc]; noc_r = [x[2] for x in noc]
        print(f"  {reg:<12}(n_q={n_q}, k_sleeve={len(items)}→{len(noc)}) "
              f"Pearson full={_pearson(full_w, full_r):+.2f} no_coin={_pearson(noc_w, noc_r):+.2f} | "
              f"Spearman full={_spearman(full_w, full_r):+.2f} no_coin={_spearman(noc_w, noc_r):+.2f}")
        for s, wv, rv in sorted(items, key=lambda x: -x[2]):
            mark = " ←coin(outlier 후보)" if s == "coin" else ""
            print(f"      {s:<10} w={wv:.3f} ret={rv:+.4f}{mark}")

    # ★W2 진단: regime 에피소드 타임라인 (Stagflation 이 2022 단일점인지 / 분산돼 있는지)
    print("[★W2 regime 에피소드 타임라인] (분기 date→regime, 연속구간 식별)")
    reg_dates = defaultdict(list)
    for (_dt, _lbl, _p, _nv) in rows:
        reg_dates[_lbl].append(_dt)
    for _lbl, _ds in sorted(reg_dates.items(), key=lambda x: -len(x[1])):
        yrs = sorted(set(d[:4] for d in _ds))
        print(f"  {_lbl:<12} n={len(_ds)} 연도={','.join(yrs)}")
        print(f"      분기: {', '.join(_ds)}")
    # ★regime별 손익 attribution (USD regime 기준) — 거시배분이 regime 반영되는지 진단
    from collections import defaultdict
    reg_agg = defaultdict(lambda: [0.0, 0])
    for (_dt, _lbl, _p, _nv) in rows:
        reg_agg[_lbl][0] += _p
        reg_agg[_lbl][1] += 1
    print("[regime별 손익 attribution] (USD regime, n=분기수)")
    for _lbl, (_ps, _n) in sorted(reg_agg.items(), key=lambda x: -x[1][0]):
        print(f"  {_lbl}: n={_n} Σport={_ps:+.3f} 평균{_ps/_n:+.4f}")
    from collections import Counter
    print("[⑥게이트 거부사유] (REJECT 분해 — gate가 무엇을 막았나)")
    if gate_rej_reasons:
        for rule, c in Counter(gate_rej_reasons).most_common():
            print(f"  {rule}: {c}회")
    else:
        print("  (거부 0)")
    for mkt in ("us", "kr"):
        h = conc_hist.get(mkt, [])
        if h:
            print(f"[⑦종목집중도:{mkt}] 평균통과 {np.mean([x[0] for x in h]):.1f}종목 | "
                  f"평균 최대단일비중 {np.mean([x[1] for x in h]):.3f} (n={len(h)})")
    if judge_atten_all:
        print(f"[⑨judge 감쇠] 평균 a={np.mean(judge_atten_all):.3f} 최소 {min(judge_atten_all):.3f} "
              f"(1.0=무감쇠 baseline, <1=down-only 작동)")
    print("[★survivorship] us universe=survivor-only, alpha는 phantom haircut(~1.2%p/yr 가정) 동반 해석 필수.")
    return {"nav": nav, "n_gate_submit": n_gate_submit, "n_judge": n_judge, "rows": rows}


def main() -> int:
    # ★진입점 credential 로드 (레거시 run_agents.py:512 동일 패턴).
    #   미호출 시 fred_adapter(api_key=None)가 .env FRED_API_KEY 못 읽음
    #   → RegimeClassifier unavailable → macro_view=None → 거시배분 중립 prior.
    #   import는 함수 내부 lazy = 모듈 import 부작용 0(off=byte-identical).
    from dotenv import load_dotenv
    load_dotenv(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

    ap = argparse.ArgumentParser(description="멀티에셋 라이브 entry 1사이클 (P2A A2~A5)")
    ap.add_argument("--backtest", action="store_true", default=False,
                    help="백테스트 모드(프로덕션 경로 시계열 — allocate→construction→종목 gate/judge 경유)")
    ap.add_argument("--start", default="2017-01-01")
    ap.add_argument("--end", default="2026-03-31")
    ap.add_argument("--no-dry-run", action="store_true", default=False,
                    help="DRY_RUN 해제 (★사람게이트 — 이 flag 단독으로는 실주문 미발생, A5 wire 후)")
    ap.add_argument("--with-stock", action="store_true", default=False,
                    help="stock_track stub 주입 (어댑터 검증용)")
    args = ap.parse_args()

    if args.backtest:
        run_backtest(start=args.start, end=args.end)
        return 0

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

    # ★A5 주문 코드경로 추가 (DRY_RUN=true → stub, 실 주문 0건)
    coin_order_ref = None
    stock_order_ref = None
    if result["coin_action"] in ("buy", "sell"):
        coin_order_ref = _coin_stub_order("KRW-BTC", result["coin_action"], dry_run=dry_run)
    if result["stock_action"] in ("buy", "sell"):
        stock_order_ref = _stock_order_via_kis("005930", result["stock_action"], dry_run=dry_run)

    result["coin_order_ref"] = coin_order_ref
    result["stock_order_ref"] = stock_order_ref

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
