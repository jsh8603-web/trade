"""backtest/engine.py — asset-agnostic 통합 백테스트 엔진 (SO-2/P5).

WHY: coin 13 분산 backtest_*.py + 슬리피지0 sim_engine.py 의 교체 대상(교체=Phase R).
     본 Phase = 일반 빌드만. 코인 기존 파일 미변경(SACRED).

설계:
- BacktestEngine: AssetTrack 계약(collect_market_state·generate_candidate) 경유
- 슬리피지 모델: 거래대금/호가잔량 비례 임팩트 (H1, sim_engine 슬리피지0 대비)
- 수수료: Upbit 0.05% / KIS (설정 가능)
- 세금: KR 거래세 0.20% 매도 / 환전 ~0.2% US / 해외양도세 22%
- nautilus OrderState enum: INITIALIZED→SUBMITTED→ACCEPTED→PARTIALLY_FILLED→FILLED/CANCELED
- FillModel: 확률체결 옵션 (랜덤 부분체결)
- UTC 단일 타임존
- common/metrics import (자체 지표 중복 0)
"""

from __future__ import annotations

import collections
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from common.metrics import (
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_profit_factor,
    calculate_win_rate,
    calculate_cagr,
    returns_from_equity,
)

logger = logging.getLogger("backtest.engine")

# ---------------------------------------------------------------------------
# PortfolioState — W2 회계 객체 (OPEN ZONE 신설)
# ---------------------------------------------------------------------------

@dataclass
class PortfolioState:
    """매 bar 엔진 상태 스냅샷 — GatedOrderRouter.submit gate_kwargs 공급원.

    ★SR NAV-basis 2분리:
      prev_close_nav  : 전 bar 종가 기준 NAV (일일 손실 한도 cap 계산용)
      intra_bar_nav   : 현 bar 체결 직후 NAV (체결 직후 위험 체크용)
    entry_bar = fill bar (t+1 의미) — off-by-one·lookahead 주석 고정.
    """

    # 자산
    cash: float = 0.0
    qty: float = 0.0           # 보유 수량
    avg_price: float = 0.0     # 평균 매수가

    # NAV 2분리 (SR 요구)
    prev_close_nav: float = 0.0    # 전 bar 종가 NAV — 일일 loss cap 기준
    intra_bar_nav: float = 0.0     # 체결 직후 NAV — risk check 기준

    # 포지션 메타
    entry_bar: int = -1            # fill bar index (t+1 의미, off-by-one 방지 주석)
    bar_idx: int = 0               # 현재 bar index

    # 리스크 게이트 입력
    daily_loss_pct: float = 0.0    # 당일 누적 손실 (NAV 대비, 음수 = 손실)
    ytd_realized_pnl_pct: float = 0.0
    _rejected_count: int = 0       # 거절 카운트 (로그용)

    def current_nav(self, price: float) -> float:
        """현재 NAV = cash + qty * price."""
        return self.cash + self.qty * price

    def current_weight(self, price: float) -> float:
        """현 포지션 포트폴리오 비중 (0~1)."""
        nav = self.current_nav(price)
        if nav <= 0:
            return 0.0
        return (self.qty * price) / nav

    def position_pnl_pct(self) -> float:
        """현 포지션 수익률 (손익 / 진입가 기준)."""
        if self.avg_price <= 0 or self.qty <= 0:
            return 0.0
        return 0.0  # 매도 시점 이전엔 MtM 대신 0 (daily_loss 경로 별도)

    def holding_days(self) -> int:
        """현재 보유일 수. entry_bar=-1이면 미보유."""
        if self.entry_bar < 0:
            return 0
        return max(0, self.bar_idx - self.entry_bar)

    def update_daily_loss(self, price: float) -> None:
        """당일 손실 갱신 (prev_close_nav 기준). 매 bar 종가에 호출."""
        if self.prev_close_nav > 0:
            self.daily_loss_pct = (self.current_nav(price) - self.prev_close_nav) / self.prev_close_nav
        else:
            self.daily_loss_pct = 0.0

    def open_bar(self, bar_idx: int, price: float) -> None:
        """바 시작 시 prev_close_nav 갱신 (전 bar 종가 = 현 bar 시가로 근사)."""
        self.bar_idx = bar_idx
        self.prev_close_nav = self.current_nav(price)

    def after_fill_buy(self, qty_filled: float, exec_price: float, commission: float) -> None:
        """매수 체결 후 intra_bar_nav 갱신."""
        self.cash -= qty_filled * exec_price + commission
        self.qty += qty_filled
        if self.entry_bar < 0:
            self.entry_bar = self.bar_idx  # fill bar (t+1 의미)
            self.avg_price = exec_price
        self.intra_bar_nav = self.cash + self.qty * exec_price

    def after_fill_sell(self, qty_filled: float, exec_price: float, commission: float, tax: float, pnl: float) -> None:
        """매도 체결 후 상태 정리 + intra_bar_nav 갱신."""
        realized_pct = (pnl / (self.avg_price * qty_filled)) if (self.avg_price > 0 and qty_filled > 0) else 0.0
        self.ytd_realized_pnl_pct += realized_pct
        self.cash += qty_filled * exec_price - commission - tax
        self.qty = 0.0
        self.avg_price = 0.0
        self.entry_bar = -1
        self.intra_bar_nav = self.cash


# ---------------------------------------------------------------------------
# OrderState — nautilus FSM 축약 (implementation-keys §1-(d))
# ---------------------------------------------------------------------------

class OrderState(Enum):
    """nautilus OrderState FSM 축약. 전이 검증 필수."""
    INITIALIZED = auto()
    SUBMITTED = auto()
    ACCEPTED = auto()
    PARTIALLY_FILLED = auto()
    FILLED = auto()
    CANCELED = auto()


_VALID_TRANSITIONS = {
    OrderState.INITIALIZED: {OrderState.SUBMITTED, OrderState.CANCELED},
    OrderState.SUBMITTED: {OrderState.ACCEPTED, OrderState.CANCELED},
    OrderState.ACCEPTED: {OrderState.PARTIALLY_FILLED, OrderState.FILLED, OrderState.CANCELED},
    OrderState.PARTIALLY_FILLED: {OrderState.PARTIALLY_FILLED, OrderState.FILLED, OrderState.CANCELED},
    OrderState.FILLED: set(),
    OrderState.CANCELED: set(),
}


def validate_transition(from_state: OrderState, to_state: OrderState) -> bool:
    return to_state in _VALID_TRANSITIONS.get(from_state, set())


# ---------------------------------------------------------------------------
# 비용 모델 설정
# ---------------------------------------------------------------------------

@dataclass
class CostConfig:
    """수수료/세금/슬리피지 설정 (OPEN ZONE — 구체 계수 튜닝 가능)."""
    # 수수료
    commission_rate: float = 0.0005      # Upbit 0.05%
    kis_commission_rate: float = 0.00015  # KIS ~0.015%

    # 세금 (§5)
    kr_transaction_tax: float = 0.002    # KR 거래세 0.20% 매도 시
    us_fx_cost: float = 0.002            # 환전 비용 ~0.2%
    us_capital_gains_tax: float = 0.22   # 해외 양도세 22% (연간 기준, 백테스트 근사)

    # 슬리피지 모델 파라미터 (H1)
    slippage_impact_factor: float = 0.001  # 거래대금/시총 비례 임팩트 기본 계수
    slippage_min: float = 0.0001           # 최소 슬리피지 (0.01%)
    slippage_max: float = 0.05             # 최대 슬리피지 (5%)

    # FillModel
    enable_partial_fill: bool = False      # 확률체결 옵션
    partial_fill_prob: float = 0.1         # 부분체결 확률


# ---------------------------------------------------------------------------
# 슬리피지 모델 (H1)
# ---------------------------------------------------------------------------

def calculate_slippage(
    trade_value: float,
    market_volume: float,
    config: CostConfig,
) -> float:
    """거래대금/시장거래량 비례 임팩트 슬리피지.

    market_volume = 해당 바의 거래대금(또는 시총). trade_value = 주문 금액.
    임팩트 = impact_factor * (trade_value / market_volume).
    """
    if market_volume <= 0 or market_volume != market_volume:  # NaN-safe (NaN != NaN)
        return config.slippage_max
    impact = config.slippage_impact_factor * (trade_value / market_volume)
    return float(max(config.slippage_min, min(config.slippage_max, impact)))


# ---------------------------------------------------------------------------
# 거래 레코드
# ---------------------------------------------------------------------------

@dataclass
class Trade:
    trade_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    asset: str = ""
    side: str = "BUY"               # "BUY" | "SELL"
    price: float = 0.0
    qty: float = 0.0
    commission: float = 0.0
    tax: float = 0.0
    slippage: float = 0.0
    pnl: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    order_state: OrderState = OrderState.FILLED
    region: str = "KR"              # "KR" | "US"


# ---------------------------------------------------------------------------
# BacktestResult
# ---------------------------------------------------------------------------

@dataclass
class BacktestResult:
    """백테스트 단일 구간 결과."""
    asset: str = ""
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    initial_capital: float = 10_000_000.0
    final_capital: float = 10_000_000.0
    trades: List[Trade] = field(default_factory=list)
    equity_curve: pd.Series = field(default_factory=pd.Series)

    # 지표 (common/metrics 로 채움)
    sharpe: float = 0.0
    max_drawdown: float = 0.0
    profit_factor: float = 0.0
    win_rate: float = 0.0
    cagr: float = 0.0
    total_return_pct: float = 0.0
    n_trades: int = 0

    def compute_metrics(self) -> None:
        """common/metrics 로 지표 산출 (자체 중복 0)."""
        if len(self.equity_curve) < 2:
            return
        returns = returns_from_equity(self.equity_curve)
        self.sharpe = calculate_sharpe_ratio(returns)
        self.max_drawdown = calculate_max_drawdown(self.equity_curve)
        self.cagr = calculate_cagr(self.equity_curve)
        if self.trades:
            df = pd.DataFrame([{"pnl": t.pnl} for t in self.trades])
            self.profit_factor = calculate_profit_factor(df)
            self.win_rate = calculate_win_rate(df)
        self.n_trades = len(self.trades)
        if self.initial_capital > 0:
            self.total_return_pct = (
                (self.final_capital - self.initial_capital) / self.initial_capital * 100
            )


# ---------------------------------------------------------------------------
# BacktestEngine — 메인 엔진
# ---------------------------------------------------------------------------

class BacktestEngine:
    """asset-agnostic 통합 백테스트 엔진.

    AssetTrack 계약(collect_market_state·generate_candidate) 경유.
    coin_track·stock_track 둘 다 구동.
    risk_gate(Phase2)·admission(Phase3) 재사용.
    common/metrics(SO-1) import.
    """

    def __init__(
        self,
        cost_config: Optional[CostConfig] = None,
        initial_capital: float = 10_000_000.0,
        fill_model_seed: Optional[int] = None,
        *,
        use_risk_pipeline: bool = False,
        vol_window: int = 20,       # rolling-returns deque 윈도우 (바 단위)
        target_vol: float = 0.15,   # 연환산 변동성 목표 (gross clip 기준)
        gross_lo: float = 0.10,     # gross 하한 (clip)
        gross_hi: float = 1.00,     # gross 상한 (clip, 레버리지 없음)
        gate=None,                  # W2: GatedOrderRouter 주입 (None=내부 기본 생성)
        judge_hook=None,            # W3: judge hook 주입 (None=coin bypass a=1.0)
        track_type: str = "coin",   # W3: "coin" | "stock" — 트랙별 판단 정책
    ):
        self._cost = cost_config or CostConfig()
        self._initial_capital = initial_capital
        self._rng = __import__("random").Random(fill_model_seed)
        # W1: risk pipeline opt-in flag
        self.use_risk_pipeline = use_risk_pipeline
        self._vol_window = vol_window
        self._target_vol = target_vol
        self._gross_lo = gross_lo
        self._gross_hi = gross_hi
        # W2: GatedOrderRouter (None이면 _run_risk_pipeline 내부에서 지연 생성)
        self._gate = gate
        # W3: judge hook + track_type
        self._judge_hook = judge_hook
        self._track_type = track_type

    def run(
        self,
        asset_track,
        price_series: pd.Series,
        volume_series: Optional[pd.Series] = None,
        region: str = "KR",
        memory=None,
    ) -> BacktestResult:
        """단일 자산 백테스트 1구간 완주.

        Args:
            asset_track: AssetTrack 구현체 (coin_track·stock_track)
            price_series: 가격 시계열 (UTC index)
            volume_series: 거래대금 시계열 (슬리피지 계산용, None이면 최대 슬리피지)
            region: "KR" | "US"
            memory: MemoryLayer 류(store_decision/update_with_outcome). 주입 시 학습 sink
              가동 — BUY=store_decision, SELL=update_with_outcome(realized pnl%). None=무학습
              (하위호환). WP6②: 리플레이가 결과로 prior 수정(전수조사 A5 F1 blocker 해소).

        W1: use_risk_pipeline=True 이면 on-경로(_run_risk_pipeline) 진입.
            False(기본) 이면 _run_legacy 경유 — 완전 byte-identical 동결.
        """
        # W1 hard-branch: off=_run_legacy(동결) / on=_run_risk_pipeline(배선)
        if not self.use_risk_pipeline:
            return self._run_legacy(
                asset_track, price_series, volume_series, region, memory
            )
        return self._run_risk_pipeline(
            asset_track, price_series, volume_series, region, memory
        )

    # ------------------------------------------------------------------
    # W1 on-경로: gross × weight 합성 사이징 (size_portfolio 무수정 호출)
    # ------------------------------------------------------------------

    def _run_risk_pipeline(
        self,
        asset_track,
        price_series: pd.Series,
        volume_series: Optional[pd.Series] = None,
        region: str = "KR",
        memory=None,
    ) -> BacktestResult:
        """use_risk_pipeline=True 경로.

        W1: rolling-returns deque → realized_vol → gross=clip(target_vol/realized_vol, lo, hi)
            trade_value = capital * gross * weights[asset]
        W2: PortfolioState 회계 객체 + GatedOrderRouter.submit(via_gate=True) 경유.
            ★SR NAV-basis 2분리: prev_close_nav(일일 loss cap) / intra_bar_nav(체결 직후 위험).
            모든 fill 시도 submit(via_gate=True) 경유 — 우회 차단.
            REJECTED→skip, 엔진 cap 추정 재시도 금지.
        """
        from core.risk_sizing import size_portfolio  # noqa: PLC0415
        from core.risk_gate import GatedOrderRouter  # noqa: PLC0415

        if volume_series is None:
            volume_series = pd.Series(
                [0.0] * len(price_series), index=price_series.index
            )

        # W2: GatedOrderRouter (주입 없으면 기본 생성)
        router: GatedOrderRouter = self._gate if self._gate is not None else GatedOrderRouter()

        # W2: PortfolioState 회계 초기화
        ps = PortfolioState(cash=self._initial_capital)

        equity_points: List[float] = [self._initial_capital]
        trades: List[Trade] = []

        asset_name = price_series.name or "UNKNOWN"
        entry_id = None

        # W1: rolling-returns deque
        _ret_deque: collections.deque = collections.deque(maxlen=self._vol_window)
        _prev_price: Optional[float] = None

        # G3 검증용
        position_fractions: List[float] = []

        # W3: judge hook 카운트 (매 의사결정 bar 호출, G5 검증용)
        judge_hook_calls: int = 0
        judge_finals: List[float] = []   # final size_mult 기록 (final<=L1 검증용)

        for bar_idx, (ts, price) in enumerate(price_series.items()):
            price = float(price)
            vol = float(volume_series.get(ts, 0.0))

            # W2: 바 시작 — prev_close_nav 갱신 (일일 loss 기준)
            ps.open_bar(bar_idx, price)

            # W1: gross 산출
            if _prev_price is not None and _prev_price > 0:
                _ret_deque.append(np.log(price / _prev_price))
            _prev_price = price

            if len(_ret_deque) >= 2:
                realized_vol = float(np.std(_ret_deque)) * np.sqrt(252)
            else:
                realized_vol = self._target_vol

            if realized_vol > 1e-9:
                gross = float(np.clip(
                    self._target_vol / realized_vol,
                    self._gross_lo, self._gross_hi,
                ))
            else:
                gross = self._gross_hi

            # W1: weights
            returns_df = pd.DataFrame(
                list(_ret_deque) or [0.0], columns=[asset_name]
            )
            weights, _method = size_portfolio(returns_df)
            w_asset = weights.get(asset_name, 1.0)

            # AssetTrack 계약 경유
            state = asset_track.collect_market_state(
                as_of=ts if isinstance(ts, datetime) else None
            )
            state.raw_market_data["price"] = price
            state.raw_market_data["asset"] = asset_name
            state.raw_market_data["timestamp"] = str(ts)

            try:
                decision = asset_track.generate_candidate(state)
                action = getattr(decision, "action", "hold")
            except Exception:
                action = "hold"

            # W2: 당일 손실 갱신 (현 bar 기준)
            ps.update_daily_loss(price)

            if action == "buy" and ps.cash > 0:
                # W3: 공통 judge hook — 매 의사결정 bar(buy 시도) 호출
                # 결정론 단계: valuation/rag/qwen=None → fail-open a=1.0 → final=L1×1.0=L1
                # coin bypass: firm/valuation 부재 → a=1.0 (hook 호출은 live)
                judge_hook_calls += 1
                a_judge = 1.0  # fail-open (결정론 baseline)
                l1_size_ref = 1.0  # 천장 불변식용 L1 참조
                if self._judge_hook is not None:
                    try:
                        jv = self._judge_hook(
                            bar_idx=bar_idx,
                            price=price,
                            gross=gross,
                            w_asset=w_asset,
                            track_type=self._track_type,
                        )
                        # JudgeVerdict 또는 dict 두 형식 허용
                        if hasattr(jv, "size_mult") and hasattr(jv, "l1_size"):
                            l1_size_ref = float(jv.l1_size) if jv.l1_size else 1.0
                            a_judge = float(jv.size_mult)
                        elif isinstance(jv, dict):
                            l1_size_ref = float(jv.get("l1_size", 1.0))
                            a_judge = float(jv.get("size_mult", 1.0))
                        # 천장 불변식: final ≤ L1 (down-only 보장)
                        a_judge = min(max(a_judge, 0.0), l1_size_ref)
                    except Exception:
                        a_judge = 1.0  # 장애 = fail-open

                judge_finals.append(a_judge)

                trade_value = ps.cash * gross * w_asset * a_judge
                proposed_size = trade_value

                # W2: GatedOrderRouter 경유 — via_gate=True 필수
                verdict = router.submit(
                    {"action": "buy", "asset": asset_name, "trade_value": trade_value},
                    cycle_id=f"bt-{bar_idx}",
                    via_gate=True,
                    action="buy",
                    proposed_size=proposed_size,
                    position_pnl_pct=ps.position_pnl_pct(),
                    holding_days=ps.holding_days(),
                    current_weight=ps.current_weight(price),
                    sector_weight=ps.current_weight(price),   # 단일자산 = current_weight
                    nav=ps.prev_close_nav if ps.prev_close_nav > 0 else self._initial_capital,
                    ytd_realized_pnl_pct=ps.ytd_realized_pnl_pct,
                    daily_loss_pct=ps.daily_loss_pct,
                    avg_correlation=0.0,  # 단일자산 상관 없음
                )

                from core.risk_gate import VerdictType as _VT  # noqa: PLC0415
                if verdict.verdict == _VT.REJECTED:
                    # REJECTED → skip, 엔진 cap 추정 재시도 금지
                    ps._rejected_count += 1
                    equity_points.append(ps.current_nav(price))
                    continue

                # APPROVED 또는 REDUCED: REDUCED면 adjusted_size 사용
                if verdict.verdict == _VT.REDUCED and verdict.adjusted_size is not None:
                    trade_value = float(verdict.adjusted_size)

                position_fractions.append(trade_value / (ps.cash if ps.cash > 0 else self._initial_capital))

                slip = calculate_slippage(trade_value, vol, self._cost)
                exec_price = price * (1 + slip)
                commission = trade_value * self._cost.commission_rate
                qty = (trade_value - commission) / exec_price

                state_order, qty = self._apply_fill_model(qty)

                if qty > 0:
                    # W2: 체결 후 PortfolioState 갱신
                    ps.after_fill_buy(qty, exec_price, commission)

                    if memory is not None:
                        try:
                            entry_id = memory.store_decision(
                                decision="buy",
                                reason=str(getattr(decision, "reason", "") or "backtest buy"),
                                confidence=float(getattr(decision, "confidence", 0.0) or 0.0),
                                created_at=ts.timestamp() if isinstance(ts, datetime) else None,
                                asset=asset_name,
                                entry_price=exec_price,
                            )
                        except Exception:
                            entry_id = None

                    trades.append(Trade(
                        asset=asset_name,
                        side="BUY",
                        price=exec_price,
                        qty=qty,
                        commission=commission,
                        slippage=slip * trade_value,
                        timestamp=ts if isinstance(ts, datetime) else datetime.now(timezone.utc),
                        order_state=state_order,
                        region=region,
                    ))

            elif action == "sell" and ps.qty > 0:
                trade_value = ps.qty * price
                proposed_size = trade_value

                # W2: 매도도 GatedOrderRouter 경유
                verdict = router.submit(
                    {"action": "sell", "asset": asset_name, "trade_value": trade_value},
                    cycle_id=f"bt-{bar_idx}-sell",
                    via_gate=True,
                    action="sell",
                    proposed_size=proposed_size,
                    position_pnl_pct=(price - ps.avg_price) / ps.avg_price if ps.avg_price > 0 else 0.0,
                    holding_days=ps.holding_days(),
                    current_weight=ps.current_weight(price),
                    sector_weight=ps.current_weight(price),
                    nav=ps.prev_close_nav if ps.prev_close_nav > 0 else self._initial_capital,
                    ytd_realized_pnl_pct=ps.ytd_realized_pnl_pct,
                    daily_loss_pct=ps.daily_loss_pct,
                    avg_correlation=0.0,
                )

                from core.risk_gate import VerdictType as _VT  # noqa: PLC0415
                if verdict.verdict == _VT.REJECTED:
                    ps._rejected_count += 1
                    equity_points.append(ps.current_nav(price))
                    continue

                slip = calculate_slippage(trade_value, vol, self._cost)
                exec_price = price * (1 - slip)
                exec_value = exec_price * ps.qty
                commission = exec_value * self._cost.commission_rate
                tax = self._calc_tax(exec_value, region)
                pnl = (exec_price - ps.avg_price) * ps.qty - commission - tax

                if self._is_lower_limit_locked(price, ps.avg_price):
                    logger.debug("H17 하한가잠김 — 매도 불가: %s", asset_name)
                    equity_points.append(ps.current_nav(price))
                    continue

                filled_qty = ps.qty

                if memory is not None and entry_id is not None:
                    try:
                        pnl_pct = ((exec_price - ps.avg_price) / ps.avg_price * 100.0) if ps.avg_price else 0.0
                        memory.update_with_outcome(entry_id, pnl_pct)
                    except Exception:
                        pass
                    entry_id = None

                # W2: 체결 후 PortfolioState 갱신
                ps.after_fill_sell(filled_qty, exec_price, commission, tax, pnl)

                trades.append(Trade(
                    asset=asset_name,
                    side="SELL",
                    price=exec_price,
                    qty=filled_qty,
                    commission=commission,
                    tax=tax,
                    slippage=slip * trade_value,
                    pnl=pnl,
                    timestamp=ts if isinstance(ts, datetime) else datetime.now(timezone.utc),
                    order_state=OrderState.FILLED,
                    region=region,
                ))

            # W2: 종가 equity 기록 (PortfolioState 기반)
            equity_points.append(ps.current_nav(price))

        final_capital = ps.current_nav(
            float(price_series.iloc[-1]) if len(price_series) > 0 else 0.0
        )

        result = BacktestResult(
            asset=asset_name,
            start=price_series.index[0] if len(price_series) > 0 else None,
            end=price_series.index[-1] if len(price_series) > 0 else None,
            initial_capital=self._initial_capital,
            final_capital=final_capital,
            trades=trades,
            equity_curve=pd.Series(equity_points),
        )
        result.compute_metrics()
        # W1 진단용 메타 (position_fraction 분산 검증용 — G3 oracle)
        result._position_fractions = position_fractions  # type: ignore[attr-defined]
        # W2 진단용 메타
        result._rejected_count = ps._rejected_count  # type: ignore[attr-defined]
        result._portfolio_state = ps  # type: ignore[attr-defined]
        # W3 진단용 메타
        result._judge_hook_calls = judge_hook_calls  # type: ignore[attr-defined]
        result._judge_finals = judge_finals  # type: ignore[attr-defined]
        return result

    # ------------------------------------------------------------------
    # _run_legacy: 현 run 본문 verbatim 동결 (off 경로 byte-identical 보장)
    # ------------------------------------------------------------------

    def _run_legacy(
        self,
        asset_track,
        price_series: pd.Series,
        volume_series: Optional[pd.Series] = None,
        region: str = "KR",
        memory=None,
    ) -> BacktestResult:
        """off 경로 — use_risk_pipeline=False 시 호출. 본문 동결(verbatim), 수정 금지."""
        if volume_series is None:
            volume_series = pd.Series(
                [0.0] * len(price_series), index=price_series.index
            )

        capital = self._initial_capital
        position = 0.0        # 보유 수량
        avg_price = 0.0
        equity_points: List[float] = [capital]
        trades: List[Trade] = []

        asset_name = price_series.name or "UNKNOWN"
        entry_id = None  # WP6② 학습 sink: BUY store_decision id → SELL update_with_outcome

        for ts, price in price_series.items():
            vol = float(volume_series.get(ts, 0.0))

            # AssetTrack 계약 경유 — as_of=ts 로 PIT 진입점 전달(백테스트 리플레이)
            state = asset_track.collect_market_state(
                as_of=ts if isinstance(ts, datetime) else None
            )
            state.raw_market_data["price"] = price
            state.raw_market_data["asset"] = asset_name
            state.raw_market_data["timestamp"] = str(ts)

            try:
                decision = asset_track.generate_candidate(state)
                action = getattr(decision, "action", "hold")
            except Exception:
                action = "hold"

            if action == "buy" and capital > 0:
                trade_value = capital * 0.95  # 자본의 95%
                slip = calculate_slippage(trade_value, vol, self._cost)
                exec_price = price * (1 + slip)
                commission = trade_value * self._cost.commission_rate
                qty = (trade_value - commission) / exec_price

                # FillModel 확률체결
                state_order, qty = self._apply_fill_model(qty)

                if qty > 0:
                    position += qty
                    avg_price = exec_price
                    capital -= (qty * exec_price + commission)

                    if memory is not None:
                        try:
                            entry_id = memory.store_decision(
                                decision="buy",
                                reason=str(getattr(decision, "reason", "") or "backtest buy"),
                                confidence=float(getattr(decision, "confidence", 0.0) or 0.0),
                                created_at=ts.timestamp() if isinstance(ts, datetime) else None,
                                asset=asset_name,
                                entry_price=exec_price,
                            )
                        except Exception:
                            entry_id = None

                    trades.append(Trade(
                        asset=asset_name,
                        side="BUY",
                        price=exec_price,
                        qty=qty,
                        commission=commission,
                        slippage=slip * trade_value,
                        timestamp=ts if isinstance(ts, datetime) else datetime.now(timezone.utc),
                        order_state=state_order,
                        region=region,
                    ))

            elif action == "sell" and position > 0:
                trade_value = position * price
                slip = calculate_slippage(trade_value, vol, self._cost)
                exec_price = price * (1 - slip)
                exec_value = exec_price * position
                commission = exec_value * self._cost.commission_rate
                tax = self._calc_tax(exec_value, region)
                pnl = (exec_price - avg_price) * position - commission - tax

                # H17: 하한가잠김 체크 (Phase4 kis_client 연계)
                if self._is_lower_limit_locked(price, avg_price):
                    logger.debug("H17 하한가잠김 — 매도 불가: %s", asset_name)
                    equity_points.append(capital + position * price)
                    continue

                filled_qty = position
                capital += position * exec_price - commission - tax
                position = 0.0

                if memory is not None and entry_id is not None:
                    try:
                        pnl_pct = ((exec_price - avg_price) / avg_price * 100.0) if avg_price else 0.0
                        memory.update_with_outcome(entry_id, pnl_pct)
                    except Exception:
                        pass
                    entry_id = None

                trades.append(Trade(
                    asset=asset_name,
                    side="SELL",
                    price=exec_price,
                    qty=filled_qty,
                    commission=commission,
                    tax=tax,
                    slippage=slip * trade_value,
                    pnl=pnl,
                    timestamp=ts if isinstance(ts, datetime) else datetime.now(timezone.utc),
                    order_state=OrderState.FILLED,
                    region=region,
                ))

            equity_points.append(capital + position * price)

        final_capital = capital + position * (
            float(price_series.iloc[-1]) if len(price_series) > 0 else 0.0
        )

        result = BacktestResult(
            asset=asset_name,
            start=price_series.index[0] if len(price_series) > 0 else None,
            end=price_series.index[-1] if len(price_series) > 0 else None,
            initial_capital=self._initial_capital,
            final_capital=final_capital,
            trades=trades,
            equity_curve=pd.Series(equity_points),
        )
        result.compute_metrics()
        return result

    def _apply_fill_model(self, qty: float):
        """FillModel 확률체결. 확률적으로 부분체결 시뮬레이션."""
        if not self._cost.enable_partial_fill:
            return OrderState.FILLED, qty
        if self._rng.random() < self._cost.partial_fill_prob:
            partial = qty * self._rng.uniform(0.3, 0.9)
            return OrderState.PARTIALLY_FILLED, partial
        return OrderState.FILLED, qty

    def _calc_tax(self, sell_value: float, region: str) -> float:
        """§5 세금 계산. KR 거래세 / US 환전 비용."""
        if region == "KR":
            return sell_value * self._cost.kr_transaction_tax
        elif region == "US":
            return sell_value * self._cost.us_fx_cost
        return 0.0

    @staticmethod
    def _is_lower_limit_locked(price: float, avg_price: float) -> bool:
        """H17 하한가잠김 — 기준가 대비 ±30% 하한 체크."""
        if avg_price <= 0:
            return False
        lower_limit = avg_price * 0.70
        return price <= lower_limit

    def compare_slippage(
        self,
        asset_track,
        price_series: pd.Series,
        volume_series: Optional[pd.Series] = None,
        region: str = "KR",
    ) -> Dict[str, Any]:
        """§2.9①: 슬리피지0 vs 현실 정량화."""
        zero_cost = CostConfig(
            slippage_impact_factor=0.0, slippage_min=0.0,
            commission_rate=0.0, kr_transaction_tax=0.0,
        )
        real_engine = BacktestEngine(self._cost, self._initial_capital)
        zero_engine = BacktestEngine(zero_cost, self._initial_capital)

        real_result = real_engine.run(asset_track, price_series, volume_series, region)
        zero_result = zero_engine.run(asset_track, price_series, volume_series, region)

        return {
            "real_sharpe": real_result.sharpe,
            "zero_sharpe": zero_result.sharpe,
            "real_return_pct": real_result.total_return_pct,
            "zero_return_pct": zero_result.total_return_pct,
            "slippage_drag_pct": zero_result.total_return_pct - real_result.total_return_pct,
        }
