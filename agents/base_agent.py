"""
전략 에이전트 추상 기본 클래스

모든 전략 에이전트(보수적/보통/공격적)는 이 클래스를 상속하고,
자기만의 임계값과 규칙으로 매매 판단을 내린다.
"""

from __future__ import annotations

import json
import os
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# DB 어댑터 (Supabase REST → sqlite/supabase 백엔드 추상화)
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from core.db import db


def _acquire_lock(lock_path: str, retries: int = 10, wait: float = 0.02):
    """파일 락 획득. 지수 백오프로 경합 시 대기 시간 최소화."""
    current_wait = wait
    for _ in range(retries):
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return True
        except FileExistsError:
            try:
                lock_age = time.time() - os.path.getmtime(lock_path)
                if lock_age > 120:
                    os.remove(lock_path)
                    continue
            except OSError:
                pass
            time.sleep(current_wait)
            current_wait = min(current_wait * 2, 0.5)  # 지수 백오프, 최대 0.5s
    return False


def _release_lock(lock_path: str):
    try:
        os.remove(lock_path)
    except OSError:
        pass


# ── Kelly Criterion 포지션 사이징 ──────────────────────────

def kelly_position_size(
    confidence: float,
    base_amount: int,
    win_rate: float = 0.5,
    half_kelly: bool = True,
) -> tuple[int, float]:
    """Kelly Criterion 기반 포지션 사이징.

    strategy.md 테이블 준수:
      ≥0.85 → 100%, 0.70~0.84 → 70%, 0.55~0.69 → 50%, <0.55 → 30%
    Half-Kelly 적용으로 과다 투자를 방지한다.

    Args:
        confidence: 매매 확신도 (0.0 ~ 1.0)
        base_amount: 에이전트가 계산한 기본 매매 금액 (KRW)
        win_rate: 과거 승률 (기본 0.5)
        half_kelly: True이면 Kelly fraction을 절반으로 축소

    Returns:
        (최종 금액, kelly_fraction) 튜플
    """
    # 1) strategy.md 테이블 기반 confidence 배수
    if confidence >= 0.85:
        conf_multiplier = 1.0
    elif confidence >= 0.70:
        conf_multiplier = 0.7
    elif confidence >= 0.55:
        conf_multiplier = 0.5
    else:
        conf_multiplier = 0.3

    # 2) Kelly 보정: 승률이 높으면 conf_multiplier를 부스트, 낮으면 감소
    #    Kelly fraction = W - (1-W)/R, R=avg_win/avg_loss (1.0 가정)
    #    win_rate=0.5 → kelly_f=0 → 보정 없음 (conf_multiplier 그대로)
    #    win_rate=0.6 → kelly_f=0.2 → 약간 부스트
    #    win_rate=0.7 → kelly_f=0.4 → 큰 부스트
    avg_win_loss_ratio = 1.0
    kelly_f = win_rate - (1 - win_rate) / avg_win_loss_ratio
    kelly_f = max(0.0, min(1.0, kelly_f))

    if half_kelly:
        kelly_f *= 0.5

    # 3) 최종 fraction: conf_multiplier를 기본으로, Kelly로 ±30% 보정
    #    kelly_f > 0 → 부스트 (최대 +30%), kelly_f = 0 → 그대로
    kelly_boost = kelly_f * 0.6  # 0~0.3 범위
    final_fraction = conf_multiplier * (1.0 + kelly_boost)
    final_fraction = max(0.3, min(1.0, final_fraction))  # 최소 30%, 최대 100%

    amount = int(base_amount * final_fraction)
    amount = max(5000, amount)  # Upbit 최소 주문 5000원

    # final_fraction is for logging/diagnostics only; `amount` (int) is the authoritative trade value
    return amount, round(final_fraction, 4)


@dataclass
class Decision:
    """매매 결정 결과."""
    decision: str           # "buy" | "sell" | "hold"
    confidence: float       # 0.0 ~ 1.0
    reason: str
    buy_score: dict         # 점수 내역
    trade_params: dict      # {"side": "bid"|"ask", "market": "KRW-BTC", "amount": int}
    external_signal: dict   # Data Fusion 결과
    agent_name: str         # 결정을 내린 에이전트
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S+09:00"))
    # 감독 오버라이드 / AI 거부권 메타데이터 (런타임에서 동적 할당)
    _orchestrator_override: Optional[bool] = field(default=None, repr=False)
    _override_reason: Optional[str] = field(default=None, repr=False)
    _original_action: Optional[str] = field(default=None, repr=False)
    _was_ai_vetoed: Optional[bool] = field(default=None, repr=False)
    _ai_veto_reason: Optional[str] = field(default=None, repr=False)

    def to_dict(self) -> dict:
        d = {
            "decision": self.decision,
            "confidence": self.confidence,
            "reason": self.reason,
            "buy_score": self.buy_score,
            "trade_params": self.trade_params,
            "external_signal_summary": {
                "total_score": self.external_signal.get("total_score", 0),
                "strategy_bonus": self.external_signal.get("strategy_bonus", 0),
                "fusion_signal": self.external_signal.get("fusion", {}).get("signal", "unknown"),
            },
            "agent_name": self.agent_name,
            "timestamp": self.timestamp,
        }
        # 감독 오버라이드/AI 거부권 메타데이터 보존
        for attr in ("_orchestrator_override", "_override_reason", "_original_action",
                      "_was_ai_vetoed", "_ai_veto_reason"):
            val = getattr(self, attr, None)
            if val is not None:
                d[attr] = val
        return d


class BaseStrategyAgent(ABC):
    """전략 에이전트 공통 인터페이스."""

    # 서브클래스에서 반드시 정의
    name: str = ""
    emoji: str = ""
    description: str = ""

    # ── 매수 조건 임계값 (서브클래스에서 오버라이드) ──
    fgi_threshold: int = 30
    rsi_threshold: int = 30
    sma_deviation_pct: float = -5.0
    buy_score_threshold: int = 70
    macd_bonus: bool = False

    # ── 매도 조건 ──
    target_profit_pct: float = 15.0
    stop_loss_pct: float = -5.0
    forced_stop_loss_pct: float = -10.0
    sell_fgi_threshold: int = 75
    sell_rsi_threshold: int = 70

    # ── 매매 규모 ──
    max_trade_ratio: float = 0.10      # 총 자산 대비 1회 매매
    max_daily_trades: int = 3
    weekend_reduction: float = 0.50    # 주말 축소 비율
    dca_max_ratio: float = 0.50        # DCA 최대 비율

    # ── v7.2 매도 점수제 + 레짐별 포지션 사이징 ──
    sell_score_threshold_bull: int = 85       # v7: 상승장 매도 억제
    sell_score_threshold_early_bull: int = 70  # v8.1: 상승 초입 — bull보다 낮게 (빠른 탈출)
    sell_score_threshold_sideways: int = 45   # v9: 50→45 (소액 매수 현실에 맞게 완화)
    sell_score_threshold_bear: int = 40       # v7.2: 45→40 (하락 즉시 매도)

    trailing_stop_bull: float = -15.0         # v7: 상승장 흔들림 허용
    trailing_stop_early_bull: float = -12.0   # v7.2: early_bull 별도
    trailing_stop_sideways: float = -4.0
    trailing_stop_bear: float = -1.5          # v7.2: -2→-1.5 (하락 타이트)

    buy_blocked_regimes: tuple = ("bear", "crisis")

    # v7.2: 레짐별 포지션 비율 (상승장 더 공격, 하락장 방어 유지)
    regime_trade_ratios: Optional[dict] = None  # __init_subclass__에서 초기화

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.regime_trade_ratios is None:
            cls.regime_trade_ratios = {
                "bull": 0.50,           # v7.2: 40→50% (상승장 풀베팅)
                "early_bull": 0.35,     # v7.2: 30→35%
                "sideways": 0.10,       # v7.1 유지
                "bear": 0.03,           # v7.1 유지
                "crisis": 0.00,
            }

    # ── 점수 배점 ──
    fgi_points: int = 30
    rsi_points: int = 25
    sma_points: int = 25
    news_points: int = 20

    def calculate_buy_score(
        self,
        fgi: int,
        rsi: float,
        sma_deviation: float,
        news_negative: bool,
        external_bonus: int,
        macd_golden_cross: bool = False,
        fast: bool = False,
        price_change_24h: float = 0.0,
    ) -> dict:
        """매수 점수를 계산한다. fast=True: 백테스트용 (breakdown 생략)."""
        score = 0

        # 1) FGI
        if fgi <= self.fgi_threshold:
            pts = self.fgi_points
            if fgi <= self.fgi_threshold * 0.5:
                pts += 5
            if fgi <= 20:
                pts += 5
            score += pts
        elif fgi <= self.fgi_threshold + 10:
            score += int(self.fgi_points * 0.5)

        # 2) RSI
        if rsi <= self.rsi_threshold:
            score += self.rsi_points
        elif rsi <= self.rsi_threshold + 5:
            score += 15

        # 3) SMA 이탈
        if sma_deviation <= self.sma_deviation_pct:
            score += self.sma_points
        elif sma_deviation <= self.sma_deviation_pct / 2:
            score += 15

        # 4) 뉴스 감성
        if not news_negative:
            score += self.news_points

        # 5) MACD 보너스 (보통 전략만)
        if self.macd_bonus and macd_golden_cross:
            score += 10

        # 6) 외부 지표 Data Fusion 보너스
        score += external_bonus

        # 7) 하락 추세 감점 (v8.2: 2026-04-20)
        # 24h 하락 중이면 감점하여 하락장 무분별 매수 방지
        # -1% ~ -3%: -10점, -3% ~ -5%: -20점, -5% 이상: -30점
        trend_penalty = 0
        if price_change_24h < -1:
            if price_change_24h < -5:
                trend_penalty = -30
            elif price_change_24h < -3:
                trend_penalty = -20
            else:
                trend_penalty = -10
            score += trend_penalty

        result = "buy" if score >= self.buy_score_threshold else "hold"

        if fast:
            return {"total": score, "threshold": self.buy_score_threshold, "result": result,
                    "trend_penalty": trend_penalty}

        # 상세 breakdown (프로덕션/디버그용) — 다시 계산
        breakdown: dict = {}
        # FGI breakdown
        if fgi <= self.fgi_threshold:
            pts = self.fgi_points
            if fgi <= self.fgi_threshold * 0.5: pts += 5
            if fgi <= 20: pts += 5
            breakdown["fgi"] = {"score": pts, "value": fgi, "threshold": self.fgi_threshold}
        elif fgi <= self.fgi_threshold + 10:
            breakdown["fgi"] = {"score": int(self.fgi_points * 0.5), "value": fgi, "partial": True}
        else:
            breakdown["fgi"] = {"score": 0, "value": fgi}
        # RSI breakdown
        if rsi <= self.rsi_threshold:
            breakdown["rsi"] = {"score": self.rsi_points, "value": round(rsi, 2), "threshold": self.rsi_threshold}
        elif rsi <= self.rsi_threshold + 5:
            breakdown["rsi"] = {"score": 15, "value": round(rsi, 2), "partial": True}
        else:
            breakdown["rsi"] = {"score": 0, "value": round(rsi, 2)}
        # SMA breakdown
        if sma_deviation <= self.sma_deviation_pct:
            breakdown["sma"] = {"score": self.sma_points, "value": round(sma_deviation, 2), "threshold": self.sma_deviation_pct}
        elif sma_deviation <= self.sma_deviation_pct / 2:
            breakdown["sma"] = {"score": 15, "value": round(sma_deviation, 2), "partial": True}
        else:
            breakdown["sma"] = {"score": 0, "value": round(sma_deviation, 2)}
        # 나머지
        breakdown["news"] = {"score": self.news_points if not news_negative else 0, "negative": news_negative}
        if self.macd_bonus and macd_golden_cross:
            breakdown["macd"] = {"score": 10, "golden_cross": True}
        breakdown["external"] = {"score": external_bonus}
        if trend_penalty < 0:
            breakdown["trend_penalty"] = {"score": trend_penalty, "price_change_24h": round(price_change_24h, 2)}
        breakdown["total"] = score
        breakdown["threshold"] = self.buy_score_threshold
        breakdown["result"] = result

        return breakdown

    # ── 포지션 과다 분할 매도 ──
    overweight_profit_threshold: float = 5.0   # 포지션 과다 시 분할 매도 트리거 수익률(%)
    overweight_sell_ratio: float = 1 / 3       # 분할 매도 비율 (보유량의 1/3)

    def evaluate_sell(
        self,
        profit_pct: float,
        current_fgi: int,
        current_rsi: float,
        buy_score: dict,
        ai_signal_score: int,
        drop_context: dict | None = None,
        btc_position_ratio: float = 0.0,
    ) -> dict | None:
        """
        v6 매도 평가: 점수제 + 트레일링 스탑 + 안전망.

        drop_context v6 키 (orchestrator가 주입):
          - v6_regime: 시장 레짐 (bull/early_bull/sideways/bear/crisis)
          - v6_danger_score: 위험도 점수 (0~100)
          - v6_sma_deviation: SMA20 이탈률 (%)
          - v6_change_24h: 24h 가격 변동률 (%)
          - v6_macro_score: 매크로 점수
          - v6_kimchi_pct: 김치 프리미엄 (%)
          - v6_news_negative: 뉴스 약세 여부
          - v6_current_price: 현재가
          - v6_position_peak: 포지션 최고가 (트레일링용)
        기존 drop_context 키도 하이브리드 DCA 안전망에서 계속 사용.
        """
        dc = drop_context or {}

        # ── 1. 포지션 과다 분할 매도 (최우선) ──
        max_position = float(os.getenv("MAX_POSITION_RATIO", "0.5"))
        if btc_position_ratio > max_position and profit_pct >= self.overweight_profit_threshold:
            return {
                "action": "sell_partial",
                "reason": (
                    f"포지션 과다 분할 매도: BTC 비중 {btc_position_ratio:.0%} > "
                    f"{max_position:.0%} 한도, 수익률 +{profit_pct:.1f}% >= "
                    f"+{self.overweight_profit_threshold}% -> 보유량 1/3 매도"
                ),
                "type": "overweight_rebalance",
                "sell_ratio": self.overweight_sell_ratio,
            }

        # ── v6 컨텍스트 추출 ──
        regime = dc.get("v6_regime", "sideways")
        danger = dc.get("v6_danger_score", dc.get("cascade_risk", 0))
        sma_dev = dc.get("v6_sma_deviation", 0.0)
        change_24h = dc.get("v6_change_24h", dc.get("price_change_24h", 0))
        macro_score = dc.get("v6_macro_score", 0.0)
        kimchi_pct = dc.get("v6_kimchi_pct", 0.0)
        news_negative = dc.get("v6_news_negative", False)
        current_price = dc.get("v6_current_price", 0.0)
        position_peak = dc.get("v6_position_peak", 0.0)

        # ── 2. v6 매도 점수제 ──
        sell_score = self.calculate_sell_score(
            pnl_pct=profit_pct, rsi=current_rsi, fgi_val=current_fgi,
            sma_dev=sma_dev, change_24h=change_24h, danger=danger,
            news_negative=news_negative, macro_score=macro_score,
            kimchi_pct=kimchi_pct,
        )
        threshold = self._get_sell_threshold(regime)

        if sell_score["total"] >= threshold:
            # AI 강세 시 1회 유예 (수익 중일 때만)
            if ai_signal_score > 20 and profit_pct > 0:
                state_file = Path(__file__).resolve().parent.parent / "data" / "agent_state.json"
                lock_path = str(state_file) + ".lock"
                already_deferred = False
                _locked = _acquire_lock(lock_path)
                try:
                    _st = {}
                    try:
                        with open(state_file, encoding="utf-8") as _sf:
                            _st = json.load(_sf)
                    except (FileNotFoundError, json.JSONDecodeError):
                        pass
                    already_deferred = _st.get("deferred_target_profit", False)
                    # 한 번의 lock 안에서 플래그를 토글하고 저장
                    _st["deferred_target_profit"] = not already_deferred
                    try:
                        with open(state_file, "w", encoding="utf-8") as _sf:
                            json.dump(_st, _sf, ensure_ascii=False, indent=2)
                    except OSError:
                        pass
                finally:
                    if _locked:
                        _release_lock(lock_path)
                if not already_deferred:
                    # 첫 유예 (플래그 True로 설정됨)
                    return {
                        "action": "hold_defer",
                        "reason": (
                            f"v6 매도점수 {sell_score['total']}>={threshold}이나 "
                            f"AI 강세({ai_signal_score}) -> 1회 유예"
                        ),
                    }
                # 이미 유예 완료 → 플래그 초기화 후 매도 진행
            # v7.2: 상승장에서는 1/4만 부분매도 (나머지 유지)
            if regime in ("bull", "early_bull"):
                return {
                    "action": "sell_partial",
                    "sell_ratio": 1 / 4,
                    "reason": (
                        f"v7.2 상승장 부분매도 1/4: 점수 {sell_score['total']}>={threshold} "
                        f"(regime={regime}, pnl={profit_pct:+.1f}%)"
                    ),
                    "type": "v6_sell_score",
                    "sell_score": sell_score,
                }
            return {
                "action": "sell",
                "reason": (
                    f"v6 매도점수 {sell_score['total']}>={threshold} "
                    f"(regime={regime}, pnl={profit_pct:+.1f}%)"
                ),
                "type": "v6_sell_score",
                "sell_score": sell_score,
            }

        # ── 3. v6 트레일링 스탑 ──
        if profit_pct > 0 and position_peak > 0 and current_price > 0:
            trail_from_peak = ((current_price / position_peak) - 1) * 100
            trail_threshold = self._get_trailing_threshold(regime)
            if trail_from_peak <= trail_threshold:
                return {
                    "action": "sell",
                    "reason": (
                        f"v6 트레일링 스탑: 피크 대비 {trail_from_peak:.1f}% <= "
                        f"{trail_threshold}% (peak={position_peak:,.0f}, regime={regime})"
                    ),
                    "type": "v6_trailing_stop",
                }

        # ── 4. 강제 손절 (어떤 상황에서도) ──
        if profit_pct <= self.forced_stop_loss_pct:
            return {
                "action": "sell",
                "reason": f"강제 손절: {profit_pct:.1f}% <= {self.forced_stop_loss_pct}%",
                "type": "forced_stop",
            }

        # ── 5. 하이브리드 DCA 안전망 (손절선 도달 시) ──
        # v7.2: Bull/Early bull에서는 DCA 대신 손절 (상승장에서 물타기 금지)
        if profit_pct <= self.stop_loss_pct and regime in ("bull", "early_bull"):
            return {
                "action": "sell",
                "reason": (
                    f"v7.2 상승장 손절: {profit_pct:.1f}% <= {self.stop_loss_pct}% "
                    f"(regime={regime}, DCA 금지)"
                ),
                "type": "bull_stop_loss",
            }
        if profit_pct <= self.stop_loss_pct:
            conditions_met = sum(1 for k in ["fgi", "rsi", "sma", "news"]
                                 if buy_score.get(k, {}).get("score", 0) > 0)

            cascade_risk = dc.get("cascade_risk", 0)
            dca_already_done = dc.get("dca_already_done", False)
            volume_ratio = dc.get("volume_ratio", 1.0)
            external_bearish = dc.get("external_bearish_count", 0)
            price_change_4h = dc.get("price_change_4h", 0)
            trend_falling = dc.get("trend_falling", False)

            if dca_already_done:
                return {
                    "action": "sell",
                    "reason": f"손절선 도달({profit_pct:.1f}%), DCA 1회 완료 -> 손절",
                    "type": "dca_exhausted",
                }

            if cascade_risk >= 70:
                return {
                    "action": "sell",
                    "reason": (
                        f"손절선 도달({profit_pct:.1f}%), "
                        f"캐스케이딩 {cascade_risk}점 "
                        f"(4h {price_change_4h:+.1f}%, vol {volume_ratio:.1f}x, "
                        f"약세 {external_bearish}개) -> 손절"
                    ),
                    "type": "cascade_stop",
                }

            if cascade_risk >= 40:
                if conditions_met >= 4 and ai_signal_score >= 0:
                    return {
                        "action": "dca",
                        "reason": (
                            f"손절선({profit_pct:.1f}%), 캐스케이딩 중간({cascade_risk}) "
                            f"+ 바닥 {conditions_met}개 -> DCA"
                        ),
                        "type": "hybrid_dca_cautious",
                    }
                return {
                    "action": "sell",
                    "reason": (
                        f"손절선({profit_pct:.1f}%), 캐스케이딩 {cascade_risk}점 "
                        f"+ 바닥 부족({conditions_met}개) -> 손절"
                    ),
                    "type": "cascade_moderate_stop",
                }

            if external_bearish >= 3 and conditions_met >= 3:
                return {
                    "action": "sell",
                    "reason": (
                        f"손절선({profit_pct:.1f}%), 외부 약세 {external_bearish}개 겹침 -> 손절"
                    ),
                    "type": "external_bearish_override",
                }

            if trend_falling and conditions_met >= 3 and ai_signal_score >= 0:
                if conditions_met >= 4 or ai_signal_score >= 15:
                    return {
                        "action": "dca",
                        "reason": f"손절선({profit_pct:.1f}%), 하락추세 + 강한 바닥 -> DCA",
                        "type": "hybrid_dca_trend",
                    }
                return {
                    "action": "sell",
                    "reason": f"손절선({profit_pct:.1f}%), 하락추세 + 바닥 부족 -> 손절",
                    "type": "trend_stop",
                }

            if conditions_met >= 3 and ai_signal_score >= 0:
                return {
                    "action": "dca",
                    "reason": f"손절선({profit_pct:.1f}%) + 바닥 {conditions_met}개 -> DCA",
                    "type": "hybrid_dca",
                }
            elif conditions_met >= 3 and ai_signal_score < -20:
                return {
                    "action": "sell",
                    "reason": f"손절선({profit_pct:.1f}%), AI 극매도({ai_signal_score}) -> 손절",
                    "type": "hybrid_forced",
                }
            else:
                return {
                    "action": "sell",
                    "reason": f"손절선({profit_pct:.1f}%), 바닥 부족({conditions_met}개) -> 손절",
                    "type": "stop_loss",
                }

        return None

    def save_buy_score_detail(
        self,
        decision: Decision,
        market_data: dict,
    ) -> str | None:
        """매수 점수 상세 내역을 buy_score_detail 테이블에 저장한다.

        DB 저장 실패가 매매 로직에 영향을 주지 않도록 전체를 try/except로 감싼다.
        """
        try:
            from utils.machine import skip_trade_db
            if skip_trade_db("buy_score_detail"):
                return None

            bs = decision.buy_score or {}
            fgi_obj = bs.get("fgi", {}) if isinstance(bs.get("fgi"), dict) else {}
            rsi_obj = bs.get("rsi", {}) if isinstance(bs.get("rsi"), dict) else {}
            sma_obj = bs.get("sma", {}) if isinstance(bs.get("sma"), dict) else {}
            news_obj = bs.get("news", {}) if isinstance(bs.get("news"), dict) else {}
            ext_obj = bs.get("external", {}) if isinstance(bs.get("external"), dict) else {}

            indicators = market_data.get("indicators", {})
            ticker = market_data.get("ticker", {}) or {}

            # SMA position description
            sma_val = sma_obj.get("value", 0)
            sma_position = "above" if sma_val >= 0 else f"below_{abs(sma_val):.1f}%"

            # News sentiment from market_data
            news_data = market_data.get("news", {})
            news_sentiment_str = news_data.get("overall_sentiment", "neutral")
            news_sentiment_val = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}.get(
                news_sentiment_str, 0.0
            )

            # External signal summary
            ext_signal = decision.external_signal or {}
            fusion = ext_signal.get("fusion", {})
            ext_signal_text = fusion.get("signal", "unknown") if fusion else "unknown"

            # Trade params
            tp = decision.trade_params or {}
            buy_amount = tp.get("amount") if decision.decision == "buy" else None
            sell_pct = None
            if decision.decision == "sell" and tp.get("volume"):
                sell_pct = 100.0  # full sell

            # ADX regime
            adx_regime = indicators.get("adx_regime", None)

            # Price change as market trend
            price_change = ticker.get("signed_change_rate", 0) * 100
            if price_change > 2:
                market_trend = "bullish"
            elif price_change < -2:
                market_trend = "bearish"
            else:
                market_trend = "sideways"

            # cycle_id 생성
            try:
                sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
                from scripts.cycle_id import get_or_create_cycle_id
                _cycle_id = get_or_create_cycle_id("agent")
            except Exception:
                from datetime import datetime as _dt, timezone as _tz, timedelta as _td
                _cycle_id = _dt.now(_tz(_td(hours=9))).strftime("%Y%m%d-%H%M") + "-agent"

            total_score = bs.get("total", 0)

            row = {
                "cycle_id": _cycle_id,
                "agent_type": self.name,
                "threshold": self.buy_score_threshold,
                "fgi_score": fgi_obj.get("score", 0),
                "fgi_value": fgi_obj.get("value"),
                "rsi_score": rsi_obj.get("score", 0),
                "rsi_value": rsi_obj.get("value"),
                "sma_score": sma_obj.get("score", 0),
                "sma_position": sma_position,
                "news_score": news_obj.get("score", 0),
                "news_sentiment": news_sentiment_val,
                "external_bonus": ext_obj.get("score", 0),
                "external_signal": ext_signal_text,
                "total_score": total_score,
                "action": decision.decision,
                "buy_amount": buy_amount,
                "sell_pct": sell_pct,
                "confidence": round(decision.confidence, 2),
                "reason": decision.reason,
                "btc_price": ticker.get("trade_price"),
                "market_trend": market_trend,
                "adx_regime": adx_regime,
                # 니어미스 + AI 거부권 + 감독 오버라이드 추적
                "points_from_threshold": round(total_score - self.buy_score_threshold, 2),
                "is_near_miss": abs(total_score - self.buy_score_threshold) <= 5,
                "price_at_decision": int(market_data.get("current_price", 0) or ticker.get("trade_price", 0) or 0) or None,
                "was_ai_vetoed": getattr(decision, '_was_ai_vetoed', False),
                "ai_veto_reason": getattr(decision, '_ai_veto_reason', None),
                "orchestrator_override": getattr(decision, '_orchestrator_override', False),
                "override_reason": getattr(decision, '_override_reason', None),
                "original_action": getattr(decision, '_original_action', None),
            }

            saved = db.insert("buy_score_detail", row, returning=True)
            # 저장된 레코드의 ID를 반환하여 decisions와 연결
            if isinstance(saved, dict):
                return saved.get("id")
        except Exception as e:
            print(f"[base_agent] buy_score_detail 저장 예외: {e}", file=sys.stderr)
        return None

    def _get_historical_win_rate(self, days: int = 30) -> float:
        """Supabase decisions 테이블에서 최근 N일 에이전트별 승률을 조회한다.

        데이터 부족 시 보수적 기본값 0.5를 반환한다.
        """
        try:
            from datetime import datetime, timezone, timedelta
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

            rows = db.select(
                "decisions",
                filters={
                    "created_at": f"gte.{cutoff}",
                    "decision": "in.(매수,매도)",
                    "profit_loss": "not.is.null",
                },
                order="created_at.desc",
                limit=100,
                select="profit_loss",
            )
            # Minor: weekend timing edge case (fewer trades on weekends) — not worth caching
            if not rows or len(rows) < 3:
                return 0.5  # 데이터 부족

            wins = sum(1 for r in rows if (r.get("profit_loss") or 0) > 0)
            return round(wins / len(rows), 4)
        except Exception:
            return 0.5

    @abstractmethod
    def decide(
        self,
        market_data: dict,
        external_signal: dict,
        portfolio: dict,
        drop_context: dict | None = None,
    ) -> Decision:
        """시장 데이터와 외부 시그널을 받아 매매 결정을 내린다."""
        ...

    def _extract_indicators(self, market_data: dict) -> dict:
        """market_data JSON에서 주요 지표를 추출한다."""
        indicators = market_data.get("indicators") or {}
        ticker = market_data.get("ticker") or {}

        change_rate = ticker.get("signed_change_rate")
        if change_rate is None:
            change_rate = market_data.get("change_rate_24h") or 0

        # RSI 14: None이면 50으로 폴백 (0은 유효한 값이라 `or 50` 사용 불가)
        rsi = indicators.get("rsi_14")
        if rsi is None:
            rsi = 50

        return {
            "current_price": ticker.get("trade_price") or market_data.get("current_price") or 0,
            "rsi": rsi,
            "sma20": indicators.get("sma_20") or 0,
            "sma_deviation": indicators.get("sma_20_deviation_pct") or 0,
            "macd": indicators.get("macd") or {},
            "bollinger": indicators.get("bollinger") or {},
            "price_change_24h": change_rate * 100,
        }

    def _is_weekend(self) -> bool:
        import datetime
        KST = datetime.timezone(datetime.timedelta(hours=9))
        return datetime.datetime.now(KST).weekday() >= 5

    # ── v6 레짐 감지 ──────────────────────────────────

    @staticmethod
    def detect_regime(sma_deviation: float, fgi_value: int,
                      change_24h: float, atr_4h: float = 1.0,
                      consecutive_up_days: int = 0) -> str:
        """v8 시장 레짐을 5단계로 분류한다.

        v7.2 문제: 완만한 상승장에서 SMA편차가 작아 sideways로 오판.
        v8 개선: FGI 기반 심리 감지 추가 — 시장 심리가 탐욕이면 상승장.

        Args:
            consecutive_up_days: 연속 상승일 수 (0이면 미사용)
        """
        # ── Bull: 확실한 상승장 ──
        if sma_deviation > 2.0 and fgi_value >= 45:
            return "bull"
        if sma_deviation > 1.5 and change_24h >= 3.0:
            return "bull"
        # 3일+ 연속 상승 시 bull 승격
        if consecutive_up_days >= 3 and sma_deviation > 0.3 and fgi_value >= 30:
            return "bull"
        # v8: FGI 강한 탐욕 + SMA 양수 → bull
        if fgi_value >= 65 and sma_deviation > 0.5:
            return "bull"

        # ── Early bull: 상승 초입 ──
        if sma_deviation > 0.3 and fgi_value >= 30 and change_24h >= 0.5:
            return "early_bull"
        # v8: 심리 기반 — FGI 탐욕 + SMA 확실히 양수 = 완만한 상승장
        # v8.1: FGI 50→55, SMA 0→0.3으로 상향 (sideways 오분류 방지)
        if fgi_value >= 55 and sma_deviation > 0.3:
            return "early_bull"

        # ── Bear/Crisis ──
        if sma_deviation < -2.0 and fgi_value <= 20 and atr_4h > 2.0:
            return "crisis"
        if sma_deviation < -0.5 and fgi_value <= 40:
            return "bear"

        return "sideways"

    # ── v6 매도 점수 계산 ──────────────────────────────

    @staticmethod
    def calculate_sell_score(
        pnl_pct: float, rsi: float, fgi_val: int, sma_dev: float,
        change_24h: float, danger: int, news_negative: bool,
        macro_score: float, kimchi_pct: float,
        fast: bool = False,
    ) -> dict:
        """8개 시그널 합산 매도 점수 (최대 ~120점). fast=True: breakdown 생략."""
        score = 0

        # 1) 수익률 (max 25) — v9: 소액 매수 현실에 맞게 구간 세분화
        if pnl_pct >= 7: score += 25
        elif pnl_pct >= 4: score += 20
        elif pnl_pct >= 2: score += 15
        elif pnl_pct >= 1: score += 10
        elif pnl_pct >= 0.5: score += 5
        elif pnl_pct <= -7: score += 25
        elif pnl_pct <= -5: score += 20
        elif pnl_pct <= -3: score += 12

        # 2) RSI 과매수 (max 20)
        if rsi >= 75: score += 20
        elif rsi >= 70: score += 15
        elif rsi >= 65: score += 8

        # 3) FGI 탐욕 (max 20)
        if fgi_val >= 80: score += 20
        elif fgi_val >= 70: score += 15
        elif fgi_val >= 60: score += 8

        # 4) SMA 하회 추세 이탈 (max 15)
        if sma_dev < -2.0: score += 15
        elif sma_dev < -1.0: score += 10
        elif sma_dev < 0: score += 5

        # 5) 24h 모멘텀 하락 (max 15)
        if change_24h <= -5: score += 15
        elif change_24h <= -3: score += 10
        elif change_24h <= -1: score += 5

        # 6) 위험도 가산 (max 10)
        if danger >= 60: score += 10
        elif danger >= 40: score += 5

        # 7) 뉴스/매크로 약세 (max 10)
        ext_pts = 0
        if news_negative: ext_pts += 5
        if macro_score <= -10: ext_pts += 5
        score += min(ext_pts, 10)

        # 8) 김치 프리미엄 과열 (max 5)
        if kimchi_pct >= 5: score += 5
        elif kimchi_pct >= 3: score += 3

        total = min(score, 120)
        if fast:
            return {"total": total}

        return {"total": total}

    def _get_sell_threshold(self, regime: str) -> int:
        if regime == "bull":
            return self.sell_score_threshold_bull
        elif regime == "early_bull":
            return self.sell_score_threshold_early_bull
        elif regime == "sideways":
            return self.sell_score_threshold_sideways
        return self.sell_score_threshold_bear

    def _get_trailing_threshold(self, regime: str) -> float:
        if regime == "bull":
            return self.trailing_stop_bull
        elif regime == "early_bull":
            return self.trailing_stop_early_bull
        elif regime == "sideways":
            return self.trailing_stop_sideways
        return self.trailing_stop_bear

    # v7.2: 레짐별 1회 매매 상한 (상승장 확대, 하락장 축소)
    REGIME_MAX_TRADE = {
        "bull": 3_000_000,
        "early_bull": 2_000_000,
        "sideways": 300_000,
        "bear": 100_000,
        "crisis": 0,
    }

    # v8.3: RL 6단계 레짐 → 에이전트 5단계 레짐 매핑
    # RL 모델 학습 결과를 보존하면서 에이전트 포지션 사이징에 올바르게 연동
    RL_TO_AGENT_REGIME = {
        "bull_strong": "bull",
        "bull_weak":   "early_bull",
        "sideways":    "sideways",
        "bear_weak":   "bear",
        "bear_strong": "bear",
        "volatile":    "sideways",
    }

    def _calculate_trade_amount(self, total_krw: float, external_bonus: int = 0, regime: str = "sideways") -> int:
        """1회 매매 금액을 계산한다. v7.2: 레짐별 포지션 비율 + 레짐별 MAX_TRADE."""
        # v8.3: RL 레짐을 에이전트 레짐으로 변환
        agent_regime = self.RL_TO_AGENT_REGIME.get(regime, regime)
        ratios = self.regime_trade_ratios or {}
        trade_ratio = ratios.get(agent_regime, self.max_trade_ratio)
        amount = int(total_krw * trade_ratio)
        if self._is_weekend():
            if external_bonus >= 10:
                pass  # 주말이더라도 외부 점수가 높으면 축소 룰 무효화 (불장/호재)
            else:
                amount = int(amount * (1 - self.weekend_reduction))
        # v8: 레짐별 MAX_TRADE (상승장 3M, 하락장 100K)
        regime_max = self.REGIME_MAX_TRADE.get(agent_regime, 300_000)
        # .env MAX_TRADE_AMOUNT는 항상 안전 상한으로 작동 (절대 우회 불가)
        env_max = int(os.getenv("MAX_TRADE_AMOUNT", "100000"))
        max_amount = min(regime_max, env_max)
        return min(amount, max_amount)
