"""
시뮬레이터 공통 엔진 — backtest_v6_simulation.py / backtest_v6_2018_2021.py 공유.

두 백테스트 파일의 TradingSimulator/Simulator 클래스에서 공통 로직을 추출.
- 포트폴리오/평가액 계산
- 위험도(danger) / 기회도(opportunity) 점수
- 에이전트 전환 규칙
- 매수/매도 체결 + 통계 갱신
"""

from __future__ import annotations

from agents.conservative import ConservativeAgent
from agents.moderate import ModerateAgent
from agents.aggressive import AggressiveAgent


FEE_RATE = 0.0005  # Upbit 수수료 0.05%


class BaseSimulator:
    """두 백테스트 시뮬레이터의 공통 기반."""

    def __init__(self, initial_krw: float, version: str = "v5.1"):
        self.version = version
        self.initial_krw = float(initial_krw)
        self.krw = float(initial_krw)
        self.btc = 0.0
        self.avg_buy_price = 0.0
        self.active_agent_name = "conservative"
        self.consecutive_losses = 0
        self.total_buys = 0
        self.total_sells = 0
        self.win_trades = 0
        self.loss_trades = 0
        self.peak_eval = float(initial_krw)
        self.max_drawdown = 0.0
        self.total_fees = 0.0
        self._daily_buy_count = 0
        self._current_date = ""
        self._market_regime = "sideways"
        self._position_peak = 0.0
        self._consecutive_up_candles = 0
        # 매도 통계
        self._sell_by_score = 0
        self._sell_by_trailing = 0
        self._sell_by_forced = 0
        self._bear_blocks = 0
        self._blocked_count = 0  # 필터 차단 횟수

        self.agents = {
            "conservative": ConservativeAgent(),
            "moderate": ModerateAgent(),
            "aggressive": AggressiveAgent(),
        }
        self.yearly_stats: dict[str, dict] = {}
        self.trade_log: list[dict] = []

    @property
    def agent(self):
        return self.agents[self.active_agent_name]

    def total_eval(self, price: float) -> float:
        return self.krw + self.btc * price

    def get_portfolio(self, price: float) -> dict:
        btc_eval = self.btc * price
        total = self.krw + btc_eval
        btc_ratio = btc_eval / total if total > 0 else 0
        pnl = ((price / self.avg_buy_price) - 1) * 100 if self.avg_buy_price > 0 and self.btc > 0 else 0
        return {
            "total_krw": self.krw, "total_eval": total,
            "btc_ratio": round(btc_ratio, 4),
            "btc": {
                "balance": self.btc, "avg_buy_price": self.avg_buy_price,
                "profit_pct": round(pnl, 2), "eval_amount": btc_eval,
            },
            "krw_balance": self.krw,
        }

    # ── 위험도 / 기회도 점수 ──

    def calc_danger(self, indicators: dict, ext: dict) -> int:
        """위험도 점수 (0~100). portfolio 정보는 self에서 직접 계산."""
        score = 0
        change_24h = indicators.get("price_change_24h", 0)
        bs = ext["sources"]["binance_sentiment"]
        kimchi_pct = bs["kimchi_premium"]["premium_pct"]
        ls_ratio = bs["top_trader_long_short"]["current_ratio"]
        macro_score = ext["_macro_score"]

        # 연속 손절
        score += min(self.consecutive_losses * 10, 30)
        # BTC 과다 보유
        te = self.total_eval(indicators["current_price"])
        btc_ratio = (self.btc * indicators["current_price"]) / te if te > 0 else 0
        if btc_ratio > 0.3:
            score += min(round((btc_ratio - 0.3) * 100), 20)
        # 급락
        if change_24h < -3:
            score += min(int(abs(change_24h) * 5), 25)
        # 김치 프리미엄 과열
        if kimchi_pct > 3:
            score += min(int((kimchi_pct - 3) * 5), 15)
        # 롱 과밀
        if ls_ratio > 1.2:
            score += min(int((ls_ratio - 1.2) * 20), 10)
        # 매크로 약세
        if macro_score < -10:
            score += min(int(abs(macro_score) * 0.5), 15)
        # 뉴스 부정
        if ext["sources"]["news_sentiment"]["overall_sentiment"] == "negative":
            score += 10
        return min(score, 100)

    def calc_opportunity(self, indicators: dict, ext: dict) -> int:
        """기회도 점수 (0~100)."""
        score = 0
        fgi_val = ext["_fgi_value"]
        rsi = indicators.get("rsi_14", 50)
        change_24h = indicators.get("price_change_24h", 0)
        fusion = ext["external_signal"]["fusion"]
        bs = ext["sources"]["binance_sentiment"]
        funding_rate = bs["funding_rate"]["current_rate"]
        kimchi_pct = bs["kimchi_premium"]["premium_pct"]
        macro_score = ext["_macro_score"]

        if fgi_val <= 25:
            score += min(int((25 - fgi_val) * 1.5), 25)
        if rsi < 35:
            score += min(int((35 - rsi) * 1.0), 20)
        if change_24h > 1:
            score += min(int(change_24h * 5), 15)
        if fusion["signal"] == "strong_buy":
            score += 20
        elif fusion["signal"] == "buy":
            score += 10
        if funding_rate < 0:
            score += min(int(abs(funding_rate) * 500), 10)
        if kimchi_pct < -1:
            score += min(int(abs(kimchi_pct) * 5), 10)
        if macro_score > 10:
            score += min(int(macro_score * 0.5), 10)
        return min(score, 100)

    # ── 에이전트 전환 ──

    def evaluate_switch(self, danger: int, opportunity: int) -> str | None:
        """전환 대상 에이전트 이름 반환. 전환 불필요 시 None."""
        c = self.active_agent_name
        if danger >= 70:
            return "conservative" if c != "conservative" else None
        if danger >= 50 and c == "moderate":
            return "conservative"
        if danger >= 45 and c == "aggressive":
            return "moderate"
        if opportunity >= 60 and danger < 30:
            return "aggressive" if c != "aggressive" else None
        if opportunity >= 40 and danger < 35:
            if c == "conservative":
                return "moderate"
            elif c == "moderate":
                return "aggressive"
        if opportunity >= 25 and danger < 30 and c == "conservative":
            return "moderate"
        if danger < 25 and opportunity < 25 and c != "moderate":
            return "moderate"
        return None

    def apply_switch(self, danger: int, opportunity: int) -> None:
        """에이전트 전환을 평가하고 적용한다."""
        new = self.evaluate_switch(danger, opportunity)
        if new and new != self.active_agent_name:
            self.active_agent_name = new

    # ── 연속 상승 캔들 추적 ──

    def update_consecutive_up(self, change_24h: float) -> int:
        """연속 상승 캔들 갱신, consecutive_up_days 반환."""
        if change_24h > 0:
            self._consecutive_up_candles += 1
        else:
            self._consecutive_up_candles = 0
        return self._consecutive_up_candles // 6

    # ── 매수 체결 ──

    def execute_buy(self, price: float, trade_amount: int) -> None:
        """매수 체결: KRW 차감, BTC 추가, 통계 갱신."""
        fee = trade_amount * FEE_RATE
        self.total_fees += fee
        actual_btc = trade_amount * (1 - FEE_RATE) / price
        total_cost = self.avg_buy_price * self.btc + trade_amount
        self.btc += actual_btc
        self.avg_buy_price = total_cost / self.btc if self.btc > 0 else 0
        self.krw -= trade_amount
        self.total_buys += 1
        self._daily_buy_count += 1
        if self.version == "v6":
            self._position_peak = max(self._position_peak, price)

    # ── 매도 체결 ──

    def execute_sell(self, price: float, trade_volume: float, partial: bool = False) -> float:
        """매도 체결. 실현 손익(pnl_realized)을 반환한다."""
        gross_revenue = trade_volume * price
        fee = gross_revenue * FEE_RATE
        revenue = gross_revenue - fee
        self.total_fees += fee
        pnl_realized = revenue - (trade_volume * self.avg_buy_price)

        if pnl_realized < 0:
            self.consecutive_losses += 1
            self.loss_trades += 1
        else:
            self.consecutive_losses = 0
            self.win_trades += 1

        if partial:
            self.btc -= trade_volume
        else:
            self.btc = 0
            self.avg_buy_price = 0
            self._position_peak = 0.0

        self.krw += revenue
        self.total_sells += 1
        return pnl_realized

    # ── MDD 갱신 ──

    def update_drawdown(self, price: float) -> float:
        """현재 평가액으로 peak/MDD를 갱신하고 현재 평가액을 반환."""
        current_eval = self.total_eval(price)
        if current_eval > self.peak_eval:
            self.peak_eval = current_eval
        dd = (self.peak_eval - current_eval) / self.peak_eval * 100
        if dd > self.max_drawdown:
            self.max_drawdown = dd
        return current_eval

    # ── 날짜 키 갱신 ──

    def check_new_date(self, dt) -> str:
        """날짜 전환 시 daily_buy_count 리셋. date_key 반환."""
        date_key = dt.strftime("%Y-%m-%d")
        if date_key != self._current_date:
            self._current_date = date_key
            self._daily_buy_count = 0
        return date_key

    def ensure_yearly_stats(self, year_key: str, price: float) -> dict:
        """연도별 통계 초기화. yearly_stats[year_key] 반환."""
        if year_key not in self.yearly_stats:
            self.yearly_stats[year_key] = {
                "buys": 0, "sells": 0, "holds": 0,
                "pnl": 0.0, "start_eval": 0, "end_eval": 0,
            }
        ys = self.yearly_stats[year_key]
        if ys["start_eval"] == 0:
            ys["start_eval"] = self.total_eval(price)
        return ys
