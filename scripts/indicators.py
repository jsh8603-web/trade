"""
인크리멘탈 기술지표 계산기 — O(n²) → O(n)

매 캔들마다 전체를 재계산하지 않고, 이전 상태를 유지하며 O(1)로 갱신한다.
- RSI: Wilder's smoothed moving average (지수 평활)
- SMA: 슬라이딩 윈도우 합산
- MACD: EMA-12, EMA-26, Signal EMA-9 carry-forward
- ATR: 슬라이딩 윈도우 평균
- 연속 음봉: 카운터 유지
"""

from __future__ import annotations

from collections import deque


class IncrementalIndicators:
    """캔들을 하나씩 feed하면 O(1)로 지표를 갱신하는 클래스."""

    def __init__(self, rsi_period: int = 14, sma_period: int = 20, atr_window: int = 24):
        self.rsi_period = rsi_period
        self.sma_period = sma_period
        self.atr_window = atr_window

        # RSI state
        self._prev_close: float | None = None
        self._avg_gain: float = 0.0
        self._avg_loss: float = 0.001
        self._rsi_count: int = 0  # 받은 close 개수
        self._initial_gains: list[float] = []
        self._initial_losses: list[float] = []

        # SMA state — 슬라이딩 윈도우
        self._sma_buf: deque[float] = deque(maxlen=sma_period)
        self._sma_sum: float = 0.0

        # MACD state — EMA carry-forward
        self._ema12: float | None = None
        self._ema26: float | None = None
        self._ema_signal: float | None = None
        self._ema12_count: int = 0
        self._ema26_count: int = 0
        self._signal_count: int = 0
        self._ema12_init: list[float] = []
        self._ema26_init: list[float] = []
        self._macd_history: deque[float] = deque(maxlen=9)

        # ATR state — 슬라이딩 윈도우
        self._atr_buf: deque[float] = deque(maxlen=atr_window)
        self._atr_sum: float = 0.0

        # 연속 음봉 카운터
        self._consecutive_red: int = 0

        # 24h 변화 (6캔들 전)
        self._price_buf: deque[float] = deque(maxlen=7)

        # 총 캔들 수
        self._count: int = 0

    def update(self, candle: dict) -> dict:
        """캔들 1개를 받아 지표를 갱신하고 결과 dict를 반환한다."""
        price = candle["trade_price"]
        high = candle["high_price"]
        low = candle["low_price"]
        opening = candle["opening_price"]

        self._count += 1

        # ── RSI 갱신 ──
        rsi = self._update_rsi(price)

        # ── SMA 갱신 ──
        sma20 = self._update_sma(price)

        # ── MACD 갱신 ──
        macd = self._update_macd(price)

        # ── SMA 이탈도 ──
        sma_deviation = ((price - sma20) / sma20 * 100) if sma20 else 0

        # ── 24h 가격 변화 (6캔들 전) ──
        self._price_buf.append(price)
        if len(self._price_buf) >= 7:
            price_24h_ago = self._price_buf[0]
            change_24h = (price - price_24h_ago) / price_24h_ago * 100
        else:
            change_24h = 0

        # ── ATR 갱신 ──
        tr = (high - low) / low * 100 if low > 0 else 0
        if len(self._atr_buf) == self._atr_buf.maxlen:
            self._atr_sum -= self._atr_buf[0]
        self._atr_buf.append(tr)
        self._atr_sum += tr
        atr_4h = self._atr_sum / len(self._atr_buf) if self._atr_buf else 1.0

        # ── 연속 음봉 ──
        if price < opening:
            self._consecutive_red += 1
        else:
            self._consecutive_red = 0

        return {
            "current_price": price,
            "rsi_14": rsi,
            "sma_20": round(sma20),
            "sma_deviation_pct": round(sma_deviation, 2),
            "macd": macd,
            "price_change_24h": round(change_24h, 2),
            "volume": candle.get("candle_acc_trade_volume", 0),
            "atr_4h": round(atr_4h, 3),
            "consecutive_red": self._consecutive_red,
        }

    # ── RSI: Wilder's smoothed ──

    def _update_rsi(self, price: float) -> float:
        self._rsi_count += 1

        if self._prev_close is None:
            self._prev_close = price
            return 50.0

        delta = price - self._prev_close
        self._prev_close = price
        gain = max(delta, 0)
        loss = max(-delta, 0)

        period = self.rsi_period

        if self._rsi_count <= period + 1:
            # 초기 구간: 값을 모아서 단순 평균
            self._initial_gains.append(gain)
            self._initial_losses.append(loss)
            if self._rsi_count == period + 1:
                self._avg_gain = sum(self._initial_gains) / period
                self._avg_loss = sum(self._initial_losses) / period or 0.001
                self._initial_gains.clear()
                self._initial_losses.clear()
            else:
                return 50.0

        else:
            # Wilder's smoothing: avg = (prev_avg * (period-1) + current) / period
            self._avg_gain = (self._avg_gain * (period - 1) + gain) / period
            self._avg_loss = (self._avg_loss * (period - 1) + loss) / period
            if self._avg_loss == 0:
                self._avg_loss = 0.001

        rs = self._avg_gain / self._avg_loss
        return round(100 - (100 / (1 + rs)), 2)

    # ── SMA: 슬라이딩 윈도우 ──

    def _update_sma(self, price: float) -> float:
        if len(self._sma_buf) == self._sma_buf.maxlen:
            self._sma_sum -= self._sma_buf[0]
        self._sma_buf.append(price)
        self._sma_sum += price

        if len(self._sma_buf) < self.sma_period:
            return price
        return self._sma_sum / self.sma_period

    # ── MACD: EMA carry-forward ──

    def _update_macd(self, price: float) -> dict:
        # EMA-12
        ema12 = self._update_ema(price, 12)
        # EMA-26
        ema26 = self._update_ema(price, 26)

        if ema12 is None or ema26 is None:
            return {"macd": 0, "signal": 0, "golden_cross": False}

        macd_line = ema12 - ema26
        self._macd_history.append(macd_line)

        # Signal EMA-9 (MACD 값의 EMA)
        signal = self._update_signal_ema(macd_line)

        return {
            "macd": round(macd_line, 2),
            "signal": round(signal, 2),
            "golden_cross": macd_line > signal,
        }

    def _update_ema(self, price: float, period: int) -> float | None:
        if period == 12:
            self._ema12_count += 1
            if self._ema12_count <= period:
                self._ema12_init.append(price)
                if self._ema12_count < period:
                    return None
                # 초기화 완료
                self._ema12 = sum(self._ema12_init) / period
                self._ema12_init.clear()
                return self._ema12
            k = 2 / (period + 1)
            self._ema12 = price * k + self._ema12 * (1 - k)
            return self._ema12
        else:  # period == 26
            self._ema26_count += 1
            if self._ema26_count <= period:
                self._ema26_init.append(price)
                if self._ema26_count < period:
                    return None
                self._ema26 = sum(self._ema26_init) / period
                self._ema26_init.clear()
                return self._ema26
            k = 2 / (period + 1)
            self._ema26 = price * k + self._ema26 * (1 - k)
            return self._ema26

    def _update_signal_ema(self, macd_val: float) -> float:
        self._signal_count += 1
        if self._signal_count < 9:
            return macd_val
        if self._signal_count == 9:
            self._ema_signal = sum(self._macd_history) / 9
            return self._ema_signal
        k = 2 / (9 + 1)
        self._ema_signal = macd_val * k + self._ema_signal * (1 - k)
        return self._ema_signal
