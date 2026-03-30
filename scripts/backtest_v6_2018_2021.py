#!/usr/bin/env python3
"""
v6 백테스트: 2018-2021 히스토리컬 데이터
- 기존 sim_data_points.json 활용 (Upbit API 호출 없음)
- v6 매도 점수제 + 트레일링 스탑 + Bear/Crisis 매수 차단
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from agents.base_agent import BaseStrategyAgent
from scripts.sim_engine import BaseSimulator

KST = timezone(timedelta(hours=9))
INITIAL_KRW = 1_000_000
MAX_TRADE_AMOUNT = 500_000
FEE_RATE = 0.0005        # Upbit 수수료 0.05% per trade
# v7.2: 레짐별 1회 매매 상한 (상승장 확대, 하락장 축소)
V7_MAX_TRADE = {"bull": 3_000_000, "early_bull": 2_000_000, "sideways": 300_000,
                "bear": 100_000, "crisis": 0}

REGIME_FILTER_INTENSITY = {
    "bull": {"fgi_block": 5, "red_candle_block": 5, "bear_max_daily": 10,
             "sma_filter": False, "macro_penalty": 0, "buy_score_bonus": 0,
             "tp_multiplier": 1.5, "sl_multiplier": 1.0},
    "early_bull": {"fgi_block": 8, "red_candle_block": 4, "bear_max_daily": 8,
                   "sma_filter": False, "macro_penalty": 0, "buy_score_bonus": 0,
                   "tp_multiplier": 1.3, "sl_multiplier": 1.0},
    "sideways": {"fgi_block": 10, "red_candle_block": 3, "bear_max_daily": 5,
                 "sma_filter": True, "macro_penalty": -5, "buy_score_bonus": 5,
                 "tp_multiplier": 1.0, "sl_multiplier": 1.0},
    "bear": {"fgi_block": 15, "red_candle_block": 3, "bear_max_daily": 2,
             "sma_filter": True, "macro_penalty": -15, "buy_score_bonus": 10,
             "tp_multiplier": 1.0, "sl_multiplier": 0.7},
    "crisis": {"fgi_block": 20, "red_candle_block": 2, "bear_max_daily": 1,
               "sma_filter": True, "macro_penalty": -20, "buy_score_bonus": 15,
               "tp_multiplier": 1.0, "sl_multiplier": 0.7},
}


def load_all_data(years):
    """sim_data_points.json 로드 + 포맷 변환."""
    all_points = []
    for year in years:
        path = PROJECT_DIR / "data" / f"historical_{year}" / "sim_data_points.json"
        if not path.exists():
            print(f"  ! {path} not found")
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"  {year}: {len(data)} points")
        for dp in data:
            dt = datetime.fromisoformat(dp["datetime"])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=KST)
            indicators = dp["indicators"]
            fgi = dp["fgi"]
            ext = dp.get("external", {})
            news = ext.get("news", {})
            binance = ext.get("binance", {})
            macro_obj = dp.get("macro", {})
            fusion = ext.get("fusion", {})

            macro_score = macro_obj.get("score", 0)
            fusion_signal = fusion.get("signal", fusion.get("classification", "neutral"))
            fusion_score = fusion.get("score", fusion.get("value", 0))
            external_bonus = {"strong_buy": 20, "buy": 10, "neutral": 0,
                              "sell": -5, "strong_sell": -10}.get(fusion_signal, 0)
            news_sentiment = news.get("sentiment", "neutral")

            ext_formatted = {
                "external_signal": {
                    "total_score": fusion_score,
                    "strategy_bonus": external_bonus,
                    "fusion": {"signal": fusion_signal, "score": fusion_score},
                },
                "sources": {
                    "news_sentiment": {"overall_sentiment": news_sentiment,
                                       "score": news.get("score", 0)},
                    "binance_sentiment": {
                        "kimchi_premium": {"premium_pct": binance.get("kimchi_premium_pct", 0)},
                        "top_trader_long_short": {"current_ratio": binance.get("long_short_ratio", 1.0)},
                        "funding_rate": {"current_rate": binance.get("funding_rate", 0)},
                    },
                    "macro": {"analysis": {"macro_score": macro_score,
                                           "sentiment": macro_obj.get("sentiment", "neutral")}},
                },
                "_external_bonus": external_bonus,
                "_news_negative": news_sentiment == "negative",
                "_fgi_value": fgi.get("value", 50),
                "_macro_score": macro_score,
            }
            all_points.append((dt, indicators, fgi, ext_formatted))

    all_points.sort(key=lambda x: x[0])
    return all_points


class Simulator(BaseSimulator):
    """v6 + v5.1 + B&H 동시 시뮬레이터. BaseSimulator 상속."""

    def __init__(self, version: str):
        super().__init__(float(INITIAL_KRW), version)
        # 하위 호환 별칭
        self._blocked = 0

    def step(self, dt, indicators, fgi, ext):
        price = indicators["current_price"]
        fgi_val = ext["_fgi_value"]
        sma_dev = indicators.get("sma_deviation_pct", 0)
        change_24h = indicators.get("price_change_24h", 0)
        macro_score = ext["_macro_score"]
        atr = indicators.get("atr_4h", 1.0)

        danger = self.calc_danger(indicators, ext)
        opportunity = self.calc_opportunity(indicators, ext)
        self.apply_switch(danger, opportunity)
        agent = self.agent

        # v7.2 레짐 판별 (#6: 연속 상승 감지)
        consecutive_up_days = self.update_consecutive_up(change_24h)

        regime = BaseStrategyAgent.detect_regime(sma_dev, fgi_val, change_24h, atr,
                                                  consecutive_up_days=consecutive_up_days)
        self._market_regime = regime
        rf = REGIME_FILTER_INTENSITY.get(regime, REGIME_FILTER_INTENSITY["sideways"])

        # 매수 점수
        eb = ext["_external_bonus"]
        nn = ext["_news_negative"]
        if rf.get("sma_filter", True):
            sma20 = indicators.get("sma_20", price)
            if sma_dev < -1.0 and price < sma20 * 0.99: eb -= 15
        if macro_score <= -10: eb += rf.get("macro_penalty", -10)

        macd = indicators.get("macd", {})
        buy_score = agent.calculate_buy_score(
            fgi=fgi["value"], rsi=indicators.get("rsi_14", 50),
            sma_deviation=sma_dev, news_negative=nn,
            external_bonus=eb,
            macd_golden_cross=macd.get("golden_cross", False),
            fast=True,
        )

        self.check_new_date(dt)

        decision = "hold"
        reason = ""
        trade_amount = 0
        trade_volume = 0.0

        # === 매도 ===
        if self.btc > 0:
            pnl_pct = ((price / self.avg_buy_price) - 1) * 100
            if price > self._position_peak:
                self._position_peak = price

            if self.version == "v6":
                bs = ext["sources"]["binance_sentiment"]
                kimchi_pct = bs["kimchi_premium"]["premium_pct"]
                sell_score = BaseStrategyAgent.calculate_sell_score(
                    pnl_pct=pnl_pct, rsi=indicators.get("rsi_14", 50),
                    fgi_val=fgi_val, sma_dev=sma_dev, change_24h=change_24h,
                    danger=danger, news_negative=nn, macro_score=macro_score,
                    kimchi_pct=kimchi_pct, fast=True,
                )
                threshold = {
                    "bull": 85, "early_bull": 85, "sideways": 50,
                    "bear": 40, "crisis": 40,
                }.get(regime, 50)
                if sell_score["total"] >= threshold:
                    if regime in ("bull", "early_bull"):
                        decision = "sell_partial"
                    else:
                        decision = "sell"
                    reason = f"sell_score {sell_score['total']}>={threshold}"
                    self._sell_by_score += 1
                if decision == "hold" and self._position_peak > 0 and pnl_pct > 0:
                    trail = ((price / self._position_peak) - 1) * 100
                    trail_th = {"bull": -15.0, "early_bull": -12.0, "sideways": -4.0,
                                "bear": -1.5, "crisis": -1.5}.get(regime, -4.0)
                    if trail <= trail_th:
                        decision = "sell"
                        reason = f"trailing {trail:.1f}%<={trail_th}%"
                        self._sell_by_trailing += 1
                if decision == "hold":
                    forced = agent.forced_stop_loss_pct * rf.get("sl_multiplier", 1.0)
                    if pnl_pct <= forced:
                        decision = "sell"
                        reason = f"forced_stop {pnl_pct:.1f}%"
                        self._sell_by_forced += 1
            else:
                # v5.1
                tp_mult = rf.get("tp_multiplier", 1.0)
                sl_mult = rf.get("sl_multiplier", 1.0)
                eff_target = agent.target_profit_pct * tp_mult
                eff_forced = agent.forced_stop_loss_pct * sl_mult
                eff_stop = agent.stop_loss_pct * sl_mult
                if pnl_pct >= eff_target: decision = "sell"; reason = f"target {pnl_pct:.1f}%"
                elif pnl_pct <= eff_forced: decision = "sell"; reason = f"forced {pnl_pct:.1f}%"
                elif pnl_pct <= eff_stop and danger >= 50: decision = "sell"; reason = f"stop D={danger}"
                elif indicators.get("rsi_14", 50) >= agent.sell_rsi_threshold and fgi["value"] >= agent.sell_fgi_threshold:
                    decision = "sell"; reason = "overbought"

            if decision in ("sell", "sell_partial"):
                if decision == "sell_partial":
                    trade_volume = self.btc / 4
                else:
                    trade_volume = self.btc
                trade_amount = int(trade_volume * price)

        # === 매수 ===
        if decision == "hold" and buy_score["result"] == "buy":
            blocked = False
            if self.version == "v6" and regime in ("bear", "crisis"):
                blocked = True; self._bear_blocks += 1; self._blocked += 1
            if not blocked:
                bonus = rf.get("buy_score_bonus", 0)
                if buy_score["total"] < agent.buy_score_threshold + bonus:
                    blocked = True; self._blocked += 1
            if not blocked:
                cr = indicators.get("consecutive_red", 0)
                if cr >= rf.get("red_candle_block", 3): blocked = True; self._blocked += 1
                elif fgi_val <= rf.get("fgi_block", 15): blocked = True; self._blocked += 1
                elif sma_dev < -1.0 and fgi_val < 25 and self._daily_buy_count >= rf.get("bear_max_daily", 2):
                    blocked = True; self._blocked += 1
                elif macro_score <= -15 and sma_dev < -2.0 and regime not in ("bull", "early_bull"):
                    blocked = True; self._blocked += 1
                elif regime == "sideways" and indicators.get("rsi_14", 50) >= 55 and fgi_val >= 50:
                    blocked = True; self._blocked += 1
            if not blocked:
                v7_ratios = {"bull": 0.50, "early_bull": 0.35, "sideways": 0.10,
                             "bear": 0.03, "crisis": 0.00}
                if self.version == "v6":
                    trade_ratio = v7_ratios.get(regime, 0.15)
                    max_amt = V7_MAX_TRADE.get(regime, MAX_TRADE_AMOUNT)
                else:
                    trade_ratio = agent.max_trade_ratio
                    max_amt = MAX_TRADE_AMOUNT
                available = min(self.krw * trade_ratio, max_amt)
                if available >= 5000:
                    decision = "buy"
                    trade_amount = int(available)
                    trade_volume = trade_amount * (1 - FEE_RATE) / price

        # === 실행 (BaseSimulator 헬퍼 활용) ===
        year_key = dt.strftime("%Y")
        ys = self.ensure_yearly_stats(year_key, price)

        pnl_realized = 0.0
        if decision == "buy" and trade_amount > 0:
            self.execute_buy(price, trade_amount)
            ys["buys"] += 1
        elif decision in ("sell", "sell_partial") and trade_volume > 0:
            pnl_realized = self.execute_sell(price, trade_volume, partial=(decision == "sell_partial"))
            ys["sells"] += 1
            ys["pnl"] += pnl_realized

        current_eval = self.update_drawdown(price)
        ys["end_eval"] = current_eval

        if decision in ("buy", "sell", "sell_partial"):
            self.trade_log.append({
                "dt": dt.isoformat(), "decision": decision, "reason": reason,
                "price": int(price), "pnl": round(pnl_realized),
                "agent": agent.name, "regime": regime,
            })


def main():
    print("=" * 70)
    print("  v6 Backtest: 2017-2021 Historical Data")
    print("=" * 70)

    print("\n[1] Loading data...")
    points = load_all_data([2017, 2018, 2019, 2020, 2021])
    if not points:
        print("No data found!")
        return
    print(f"  Total: {len(points)} points")

    first_price = points[0][1]["current_price"]
    last_price = points[-1][1]["current_price"]
    bh_roi = ((last_price / first_price) - 1) * 100
    print(f"  Period: {points[0][0].strftime('%Y-%m-%d')} ~ {points[-1][0].strftime('%Y-%m-%d')}")
    print(f"  Price: {first_price:,.0f} -> {last_price:,.0f} KRW")
    print(f"  B&H ROI: {bh_roi:+.1f}%")

    print("\n[2] Running simulations...")
    sim_v6 = Simulator("v6")
    sim_v51 = Simulator("v5.1")

    for i, (dt, indicators, fgi, ext) in enumerate(points):
        sim_v6.step(dt, indicators, fgi, ext)
        sim_v51.step(dt, indicators, fgi, ext)
        if (i + 1) % 2000 == 0:
            price = indicators["current_price"]
            print(f"  ... {i+1}/{len(points)} | "
                  f"v6={sim_v6.total_eval(price)/INITIAL_KRW*100-100:+.1f}% "
                  f"v5.1={sim_v51.total_eval(price)/INITIAL_KRW*100-100:+.1f}%")

    final_price = points[-1][1]["current_price"]

    print(f"\n{'=' * 70}")
    print("  RESULTS (2017-2021)")
    print(f"{'=' * 70}")
    print(f"  B&H ROI: {bh_roi:+.1f}%")

    for label, sim in [("v6", sim_v6), ("v5.1", sim_v51)]:
        roi = (sim.total_eval(final_price) / INITIAL_KRW - 1) * 100
        wr = sim.win_trades / sim.total_sells * 100 if sim.total_sells > 0 else 0
        print(f"\n  --- {label} ---")
        print(f"  ROI: {roi:+.1f}%  (eval={sim.total_eval(final_price):,.0f} KRW)")
        print(f"  MDD: {sim.max_drawdown:.1f}%")
        print(f"  Buys: {sim.total_buys}, Sells: {sim.total_sells}")
        print(f"  Win Rate: {wr:.1f}% ({sim.win_trades}W/{sim.loss_trades}L)")
        print(f"  Total Fees: {sim.total_fees:,.0f} KRW")
        print(f"  Filter Blocked: {sim._blocked}")
        if label == "v6":
            print(f"  Sell by: score={sim._sell_by_score}, trailing={sim._sell_by_trailing}, forced={sim._sell_by_forced}")
            print(f"  Bear blocks: {sim._bear_blocks}")
            btc_r = (sim.btc * final_price) / sim.total_eval(final_price) * 100 if sim.total_eval(final_price) > 0 else 0
            print(f"  Final State: KRW={sim.krw:,.0f}, BTC={sim.btc:.8f} (ratio={btc_r:.1f}%)")

        print("\n  Yearly:")
        for year in sorted(sim.yearly_stats.keys()):
            ys = sim.yearly_stats[year]
            if ys["start_eval"] > 0:
                yr_roi = (ys["end_eval"] / ys["start_eval"] - 1) * 100
            else:
                yr_roi = 0
            print(f"    {year}: ROI {yr_roi:+.1f}%  B={ys['buys']} S={ys['sells']} PnL={ys['pnl']:+,.0f}")

    # B&H yearly
    print("\n  --- B&H Yearly ---")
    # prev_price tracking removed (unused)
    for year in [2017, 2018, 2019, 2020, 2021]:
        year_points = [(dt, ind) for dt, ind, _, _ in points if dt.year == year]
        if year_points:
            year_start = year_points[0][1]["current_price"]
            year_end = year_points[-1][1]["current_price"]
            yr_roi = (year_end / year_start - 1) * 100
            print(f"    {year}: ROI {yr_roi:+.1f}%  ({year_start:,.0f} -> {year_end:,.0f})")

    # Save results
    results = {
        "period": "2017-2021",
        "total_points": len(points),
        "bh_roi": round(bh_roi, 2),
        "v6": {
            "roi": round((sim_v6.total_eval(final_price) / INITIAL_KRW - 1) * 100, 2),
            "mdd": round(sim_v6.max_drawdown, 2),
            "buys": sim_v6.total_buys, "sells": sim_v6.total_sells,
            "win_rate": round(sim_v6.win_trades / sim_v6.total_sells * 100, 1) if sim_v6.total_sells > 0 else 0,
            "total_fees": round(sim_v6.total_fees),
            "sell_by_score": sim_v6._sell_by_score,
            "sell_by_trailing": sim_v6._sell_by_trailing,
            "bear_blocks": sim_v6._bear_blocks,
            "yearly": sim_v6.yearly_stats,
            # 연결 테스트용 최종 상태
            "final_state": {
                "krw": round(sim_v6.krw),
                "btc": sim_v6.btc,
                "avg_buy_price": round(sim_v6.avg_buy_price),
                "total_eval": round(sim_v6.total_eval(final_price)),
                "last_price": final_price,
                "agent": sim_v6.active_agent_name,
                "consecutive_losses": sim_v6.consecutive_losses,
                "peak_eval": sim_v6.peak_eval,
                "position_peak_price": getattr(sim_v6, '_position_peak', 0),
                "consecutive_up_candles": sim_v6._consecutive_up_candles,
                "market_regime": sim_v6._market_regime,
            },
        },
        "v51": {
            "roi": round((sim_v51.total_eval(final_price) / INITIAL_KRW - 1) * 100, 2),
            "mdd": round(sim_v51.max_drawdown, 2),
            "buys": sim_v51.total_buys, "sells": sim_v51.total_sells,
            "yearly": sim_v51.yearly_stats,
        },
    }
    out_path = PROJECT_DIR / "data" / "backtest_v6_2018_2021.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n  Saved: {out_path}")


if __name__ == "__main__":
    main()
