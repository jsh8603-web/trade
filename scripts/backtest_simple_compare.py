"""검증된 단순 전략 vs 사용자 v6 백테스트 비교.

기간: 2022-01 ~ 2024-11 (약 2년 11개월, historical 데이터)
초기자금: 1,000,000원
1회 매매 상한: 500,000원
수수료: 0.05% (Upbit)

비교 대상:
  1) Buy & Hold       — 첫 캔들 전액 매수, 마지막 캔들 매도
  2) Volatility Breakout (K=0.5) — Larry Williams, 일별 (전날 high-low) × K 돌파 시 매수
  3) RSI Mean Reversion — RSI<30 매수, RSI>70 매도 (분할)
  4) SMA Trend Follow  — 가격 > SMA20 + 골든크로스 매수, 데드크로스 매도

산출 지표:
  - 총 수익률, MDD, Sharpe (연 환산), 매수/매도 횟수, 매수:매도 비율, 승률, 수수료
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Callable

PROJECT_DIR = Path(__file__).resolve().parent.parent
KST = timezone(timedelta(hours=9))

sys.stdout.reconfigure(encoding="utf-8")

INITIAL_KRW = 1_000_000
MAX_TRADE = 500_000
FEE_RATE = 0.0005


# ─── 데이터 로드 ────────────────────────────────────────────

def load_year(year: int) -> tuple[list, list]:
    """(candles_4h, sim_points) 반환."""
    base = PROJECT_DIR / "data" / f"historical_{year}"
    with open(base / "candles_4h.json", "r", encoding="utf-8") as f:
        candles = json.load(f)
    with open(base / "sim_data_points.json", "r", encoding="utf-8") as f:
        sims = json.load(f)
    return candles, sims


def merge_by_time(candles: list, sims: list) -> list[dict]:
    """4h 캔들 + 지표를 시간으로 매칭하여 단일 row로 결합."""
    sim_by_dt = {s["datetime"][:13]: s for s in sims}  # "YYYY-MM-DDTHH"
    merged = []
    for c in candles:
        dt_kst = c["candle_date_time_kst"][:13]
        s = sim_by_dt.get(dt_kst)
        if not s:
            continue
        merged.append({
            "dt": c["candle_date_time_kst"],
            "date": dt_kst[:10],
            "open": c["opening_price"],
            "high": c["high_price"],
            "low": c["low_price"],
            "close": c["trade_price"],
            "rsi": s["indicators"].get("rsi_14", 50),
            "sma20": s["indicators"].get("sma_20", 0),
            "macd_golden": s["indicators"].get("macd", {}).get("golden_cross", False),
        })
    merged.sort(key=lambda r: r["dt"])
    return merged


def aggregate_daily(rows: list[dict]) -> dict[str, dict]:
    """4h 캔들을 일별 OHLC로 집계."""
    daily: dict[str, dict] = {}
    for r in rows:
        d = r["date"]
        if d not in daily:
            daily[d] = {"open": r["open"], "high": r["high"], "low": r["low"], "close": r["close"]}
        else:
            daily[d]["high"] = max(daily[d]["high"], r["high"])
            daily[d]["low"] = min(daily[d]["low"], r["low"])
            daily[d]["close"] = r["close"]  # 일자 마지막
    return daily


# ─── 시뮬레이터 ─────────────────────────────────────────────

class SimpleSimulator:
    """단순 전략용 백테스트 엔진. BaseSimulator의 fee/MDD 모델 호환."""

    def __init__(self, name: str, initial_krw: float = INITIAL_KRW,
                 max_trade: int = MAX_TRADE, fee_rate: float = FEE_RATE):
        self.name = name
        self.initial_krw = initial_krw
        self.krw = float(initial_krw)
        self.btc = 0.0
        self.avg_buy_price = 0.0
        self.max_trade = max_trade
        self.fee_rate = fee_rate
        # 통계
        self.peak_eval = float(initial_krw)
        self.max_drawdown = 0.0
        self.total_buys = 0
        self.total_sells = 0
        self.win_trades = 0
        self.loss_trades = 0
        self.total_fees = 0.0
        self.daily_eval: list[tuple[str, float]] = []
        self._last_eval_date = ""

    def total_eval(self, price: float) -> float:
        return self.krw + self.btc * price

    def buy(self, price: float, amount: float | None = None) -> bool:
        """매수. amount=None이면 max_trade. 잔고 부족 시 가능한 만큼."""
        if amount is None:
            amount = self.max_trade
        amount = min(amount, self.krw, self.max_trade if amount != self.krw else amount)
        if amount < 5000:
            return False
        fee = amount * self.fee_rate
        actual_btc = amount * (1 - self.fee_rate) / price
        total_cost = self.avg_buy_price * self.btc + amount
        self.btc += actual_btc
        self.avg_buy_price = total_cost / self.btc if self.btc > 0 else 0
        self.krw -= amount
        self.total_fees += fee
        self.total_buys += 1
        return True

    def buy_full(self, price: float) -> bool:
        """B&H용: max_trade 무시, 전액 매수."""
        amount = self.krw
        if amount < 5000:
            return False
        fee = amount * self.fee_rate
        actual_btc = amount * (1 - self.fee_rate) / price
        total_cost = self.avg_buy_price * self.btc + amount
        self.btc += actual_btc
        self.avg_buy_price = total_cost / self.btc if self.btc > 0 else 0
        self.krw -= amount
        self.total_fees += fee
        self.total_buys += 1
        return True

    def sell(self, price: float, ratio: float = 1.0) -> bool:
        if self.btc <= 0:
            return False
        volume = self.btc * ratio
        gross = volume * price
        fee = gross * self.fee_rate
        revenue = gross - fee
        pnl = revenue - (volume * self.avg_buy_price)
        if pnl > 0:
            self.win_trades += 1
        else:
            self.loss_trades += 1
        if ratio >= 0.999:
            self.btc = 0.0
            self.avg_buy_price = 0.0
        else:
            self.btc -= volume
        self.krw += revenue
        self.total_fees += fee
        self.total_sells += 1
        return True

    def tick(self, price: float, date_key: str) -> None:
        cur = self.total_eval(price)
        if cur > self.peak_eval:
            self.peak_eval = cur
        dd = (self.peak_eval - cur) / self.peak_eval * 100
        if dd > self.max_drawdown:
            self.max_drawdown = dd
        # 일별 평가액 (Sharpe 용)
        if date_key != self._last_eval_date:
            self.daily_eval.append((date_key, cur))
            self._last_eval_date = date_key

    def report(self, final_price: float) -> dict:
        final_eval = self.total_eval(final_price)
        roi = (final_eval / self.initial_krw - 1) * 100
        # 일별 평가액 → 일일 수익률 → 연 환산 Sharpe
        evals = [e for _, e in self.daily_eval]
        if len(evals) > 1:
            daily_rets = [(evals[i] / evals[i-1] - 1) for i in range(1, len(evals))]
            import statistics
            mean_r = statistics.mean(daily_rets)
            std_r = statistics.stdev(daily_rets) if len(daily_rets) > 1 else 0
            # 연 환산: 365일 중 거래일 가정 365 (BTC는 365일)
            sharpe = (mean_r * 365 - 0.03) / (std_r * (365 ** 0.5)) if std_r > 0 else 0
        else:
            sharpe = 0
        ratio = self.total_buys / self.total_sells if self.total_sells > 0 else float("inf")
        wr = self.win_trades / (self.win_trades + self.loss_trades) * 100 if (self.win_trades + self.loss_trades) > 0 else 0
        return {
            "name": self.name,
            "final_eval": final_eval,
            "roi": roi,
            "mdd": self.max_drawdown,
            "sharpe": sharpe,
            "buys": self.total_buys,
            "sells": self.total_sells,
            "buy_sell_ratio": ratio,
            "win_rate": wr,
            "total_fees": self.total_fees,
        }


# ─── 전략들 ─────────────────────────────────────────────────

def run_buy_and_hold(rows: list[dict]) -> dict:
    sim = SimpleSimulator("Buy & Hold")
    sim.buy_full(rows[0]["close"])
    for r in rows:
        sim.tick(r["close"], r["date"])
    sim.sell(rows[-1]["close"], 1.0)
    sim.tick(rows[-1]["close"], rows[-1]["date"])
    return sim.report(rows[-1]["close"])


def run_volatility_breakout(rows: list[dict], daily: dict[str, dict], K: float = 0.5) -> dict:
    """Larry Williams 변동성 돌파.

    당일 시초가(첫 4h open) + 전날 (high - low) × K 가 돌파선.
    당일 캔들 중 high가 돌파선 이상이면 돌파선 가격에 매수.
    다음날 첫 4h 시가에 매도 (전량).
    """
    sim = SimpleSimulator(f"Volatility Breakout (K={K})")
    dates = sorted(daily.keys())
    # date → 첫 4h row 찾기
    first_4h_by_date: dict[str, dict] = {}
    for r in rows:
        if r["date"] not in first_4h_by_date:
            first_4h_by_date[r["date"]] = r

    held_position_date = None  # 보유 시작 날짜

    for r in rows:
        d = r["date"]
        # 다음날 시가 매도: 보유 중 + 날짜 바뀜 + 첫 캔들
        if held_position_date and d != held_position_date and r is first_4h_by_date.get(d):
            sim.sell(r["open"], 1.0)
            held_position_date = None

        # 당일 진입 신호 (보유 중 아닐 때만)
        if not held_position_date:
            # 전날 daily
            d_idx = dates.index(d) if d in dates else -1
            if d_idx > 0:
                prev = daily[dates[d_idx - 1]]
                today_open = first_4h_by_date.get(d, {}).get("open")
                if today_open:
                    target = today_open + (prev["high"] - prev["low"]) * K
                    # 현재 4h 캔들의 high가 target 이상이면 돌파
                    if r["high"] >= target:
                        sim.buy(target)  # 돌파 시점 매수
                        held_position_date = d

        sim.tick(r["close"], d)

    # 마지막 보유 청산
    if held_position_date:
        sim.sell(rows[-1]["close"], 1.0)
    sim.tick(rows[-1]["close"], rows[-1]["date"])
    return sim.report(rows[-1]["close"])


def run_rsi_mean_reversion(rows: list[dict]) -> dict:
    """RSI 평균회귀: RSI<30 매수 (분할 최대 3회), RSI>70 전량 매도."""
    sim = SimpleSimulator("RSI Mean Reversion (30/70)")
    buy_count_in_position = 0
    last_action_idx = -100  # 매매 간격 (4h 캔들 단위)
    MIN_GAP = 6  # 24h 쿨다운

    for i, r in enumerate(rows):
        rsi = r["rsi"]
        if rsi < 30 and buy_count_in_position < 3 and (i - last_action_idx) >= MIN_GAP:
            if sim.buy(r["close"]):
                buy_count_in_position += 1
                last_action_idx = i
        elif rsi > 70 and sim.btc > 0 and (i - last_action_idx) >= MIN_GAP:
            sim.sell(r["close"], 1.0)
            buy_count_in_position = 0
            last_action_idx = i

        sim.tick(r["close"], r["date"])

    if sim.btc > 0:
        sim.sell(rows[-1]["close"], 1.0)
    sim.tick(rows[-1]["close"], rows[-1]["date"])
    return sim.report(rows[-1]["close"])


def run_sma_trend(rows: list[dict]) -> dict:
    """SMA20 추세 추종: golden_cross + 가격>SMA20 매수, 데드크로스 또는 가격<SMA20 매도."""
    sim = SimpleSimulator("SMA20 Trend Follow")
    in_position = False
    last_action_idx = -100
    MIN_GAP = 6  # 24h 쿨다운

    for i, r in enumerate(rows):
        price = r["close"]
        sma = r["sma20"]
        if not sma:
            sim.tick(price, r["date"]); continue
        above = price > sma
        gc = r["macd_golden"]
        if not in_position and above and gc and (i - last_action_idx) >= MIN_GAP:
            if sim.buy(price):
                in_position = True
                last_action_idx = i
        elif in_position and not above and (i - last_action_idx) >= MIN_GAP:
            sim.sell(price, 1.0)
            in_position = False
            last_action_idx = i
        sim.tick(price, r["date"])

    if sim.btc > 0:
        sim.sell(rows[-1]["close"], 1.0)
    sim.tick(rows[-1]["close"], rows[-1]["date"])
    return sim.report(rows[-1]["close"])


# ─── 메인 ─────────────────────────────────────────────────

def main():
    print("=" * 72)
    print("  검증된 단순 전략 백테스트 — 사용자 v6 비교용")
    print("  기간: 2022-01-01 ~ 2024-11-30 (약 2년 11개월)")
    print(f"  초기자금: {INITIAL_KRW:,}원, 1회 상한: {MAX_TRADE:,}원, 수수료: {FEE_RATE*100}%")
    print("=" * 72)

    print("\n[Phase 1] 데이터 로드")
    all_candles = []
    all_sims = []
    for y in [2022, 2023, 2024]:
        c, s = load_year(y)
        all_candles.extend(c)
        all_sims.extend(s)
        print(f"  {y}: candles={len(c)}, sims={len(s)}")

    print("\n[Phase 2] 시간 매칭")
    rows = merge_by_time(all_candles, all_sims)
    print(f"  매칭된 4h 캔들: {len(rows)}")

    daily = aggregate_daily(rows)
    print(f"  일별 OHLC: {len(daily)}일")

    first_price = rows[0]["close"]
    last_price = rows[-1]["close"]
    bh_pct = (last_price / first_price - 1) * 100
    print(f"\n[Phase 3] 가격 범위: {first_price:,.0f} → {last_price:,.0f} (B&H 단순 = {bh_pct:+.1f}%)")

    print("\n[Phase 4] 전략 백테스트 실행")
    results = []
    for fn, label in [
        (lambda: run_buy_and_hold(rows), "B&H"),
        (lambda: run_volatility_breakout(rows, daily, 0.5), "변동성 돌파(K=0.5)"),
        (lambda: run_volatility_breakout(rows, daily, 0.7), "변동성 돌파(K=0.7)"),
        (lambda: run_rsi_mean_reversion(rows), "RSI 평균회귀"),
        (lambda: run_sma_trend(rows), "SMA 추세"),
    ]:
        print(f"  실행 중: {label}...")
        r = fn()
        results.append(r)

    print("\n" + "=" * 72)
    print("  결과 비교")
    print("=" * 72)
    print(f"\n  {'전략':<28} {'수익률':>9} {'MDD':>7} {'Sharpe':>8} {'매수':>6} {'매도':>6} {'B:S':>7} {'승률':>7}")
    print("  " + "-" * 80)
    for r in results:
        bs = f"{r['buy_sell_ratio']:.1f}:1" if r['buy_sell_ratio'] != float('inf') else "∞:0"
        print(f"  {r['name']:<28} {r['roi']:>+8.2f}% {r['mdd']:>6.1f}% {r['sharpe']:>+7.2f} {r['buys']:>6} {r['sells']:>6} {bs:>7} {r['win_rate']:>6.1f}%")

    print("\n  [참고] 사용자 v6 (2022-01~2026-03, 약 4년 3개월)")
    print(f"  {'사용자 v6 (이전 백테스트)':<28} {'+67.26%':>9} {'-28.3%':>7} {'N/A':>8} {991:>6} {121:>6} {'8.2:1':>7} {50.4:>6.1f}%")
    print()
    print("  주의: 사용자 v6는 4년 3개월 기간 — 단순 전략(2년 11개월)보다 길어 직접 비교 어려움")
    print("       단, 2022~2024 부분만 보면 비슷한 시기. ROI 연 환산으로 보면 비교 가능")

    # 결과 JSON 저장
    out_path = PROJECT_DIR / "data" / "backtest_simple_compare.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "period": "2022-01-01 ~ 2024-11-30",
            "initial_krw": INITIAL_KRW,
            "max_trade": MAX_TRADE,
            "fee_rate": FEE_RATE,
            "strategies": results,
            "user_v6_reference": {
                "period": "2022-01-01 ~ 2026-03-23",
                "roi_pct": 67.26,
                "mdd_pct": -28.3,
                "buys": 991,
                "sells": 121,
                "buy_sell_ratio": 8.2,
                "win_rate_pct": 50.4,
            }
        }, f, ensure_ascii=False, indent=2)
    print(f"\n  결과 저장: {out_path}")


if __name__ == "__main__":
    main()
