"""사용자 v6 백테스트 — 2022-01 ~ 2024-11 (단순 전략과 동일 기간).

backtest_v6_simulation.py 의 TradingSimulator + sim_engine.BaseSimulator 재사용.
historical_2022~2024 데이터만 사용 (Upbit live API 호출 없음).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
sys.stdout.reconfigure(encoding="utf-8")

KST = timezone(timedelta(hours=9))

from scripts.backtest_v6_simulation import (
    TradingSimulator,
    load_historical_data,
    convert_historical_to_sim_format,
    fetch_historical_fgi,
    calc_sell_score,  # noqa: F401
)


def main():
    print("=" * 72)
    print("  사용자 v6 백테스트 — 단순 전략 비교용 동기간")
    print("  기간: 2022-01-01 ~ 2024-11-30 (약 2년 11개월)")
    print("  초기자금: 1,000,000원, 1회 상한: 500,000원")
    print("=" * 72)

    # 데이터 로드 (historical만 사용)
    print("\n[Phase 1] 데이터 로드")
    all_points = []
    for y in [2022, 2023, 2024]:
        hist = load_historical_data(y)
        for dp in hist:
            all_points.append(convert_historical_to_sim_format(dp))
    print(f"  총 시뮬 포인트: {len(all_points)}")

    # 2024-12 이후 제거
    cutoff = datetime(2024, 12, 1, 0, 0, tzinfo=KST)
    all_points = [p for p in all_points if p[0] < cutoff]
    print(f"  2024-12 cutoff 후: {len(all_points)}")

    if not all_points:
        print("  데이터 없음")
        return

    first_dt, first_ind, _, _ = all_points[0]
    last_dt, last_ind, _, _ = all_points[-1]
    print(f"  기간: {first_dt.date()} ~ {last_dt.date()}")
    print(f"  가격: {first_ind['current_price']:,.0f} → {last_ind['current_price']:,.0f}")

    # v6 시뮬레이터만 실행 (v5.1 비교는 생략)
    print("\n[Phase 2] v6 시뮬레이션")
    sim_v6 = TradingSimulator(initial_krw=1_000_000, version="v6")

    n = len(all_points)
    for i, (dt, ind, fgi, ext) in enumerate(all_points):
        try:
            sim_v6.step(dt, ind, fgi, ext)
        except Exception as e:
            print(f"  step {i} 예외: {e}")
            break
        # MDD 갱신 (마지막 가격)
        sim_v6.update_drawdown(ind["current_price"])
        if (i + 1) % 1000 == 0:
            print(f"  ... {i+1}/{n} v6={sim_v6.total_eval(ind['current_price']):,.0f}")

    final_price = last_ind["current_price"]
    final_eval = sim_v6.total_eval(final_price)
    roi = (final_eval / sim_v6.initial_krw - 1) * 100
    bh_pct = (last_ind["current_price"] / first_ind["current_price"] - 1) * 100

    print("\n" + "=" * 72)
    print("  사용자 v6 결과 (2022-01 ~ 2024-11)")
    print("=" * 72)
    print(f"  최종 평가액:     {final_eval:>14,.0f}원")
    print(f"  수익률 (ROI):   {roi:>+13.2f}%")
    print(f"  MDD:            {sim_v6.max_drawdown:>13.2f}%")
    print(f"  매수 횟수:      {sim_v6.total_buys:>14}")
    print(f"  매도 횟수:      {sim_v6.total_sells:>14}")
    if sim_v6.total_sells > 0:
        bs_ratio = sim_v6.total_buys / sim_v6.total_sells
        print(f"  매수:매도 비율: {bs_ratio:>13.1f}:1")
    win = sim_v6.win_trades + sim_v6.loss_trades
    if win > 0:
        wr = sim_v6.win_trades / win * 100
        print(f"  승률:           {wr:>13.1f}%")
    print(f"  총 수수료:      {sim_v6.total_fees:>14,.0f}원")
    print(f"  매도 점수제:    {sim_v6._sell_by_score}")
    print(f"  트레일링 스탑:  {sim_v6._sell_by_trailing}")
    print(f"  강제 손절:      {sim_v6._sell_by_forced}")
    print(f"  Bear 매수 차단: {sim_v6._bear_blocks}")

    print(f"\n  [참고] B&H 단순 = {bh_pct:+.2f}% (가격 변화)")

    # JSON 저장
    out_path = PROJECT_DIR / "data" / "backtest_v6_2022_2024.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "period": "2022-01-01 ~ 2024-11-30",
            "version": "v6",
            "initial_krw": 1_000_000,
            "max_trade": 500_000,
            "final_eval": final_eval,
            "roi_pct": roi,
            "mdd_pct": sim_v6.max_drawdown,
            "buys": sim_v6.total_buys,
            "sells": sim_v6.total_sells,
            "buy_sell_ratio": sim_v6.total_buys / sim_v6.total_sells if sim_v6.total_sells > 0 else None,
            "win_rate_pct": (sim_v6.win_trades / win * 100) if win > 0 else 0,
            "total_fees": sim_v6.total_fees,
            "sell_by_score": sim_v6._sell_by_score,
            "sell_by_trailing": sim_v6._sell_by_trailing,
            "sell_by_forced": sim_v6._sell_by_forced,
            "bear_blocks": sim_v6._bear_blocks,
            "bh_pct": bh_pct,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n  결과 저장: {out_path}")


if __name__ == "__main__":
    main()
