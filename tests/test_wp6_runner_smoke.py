"""tests/test_wp6_runner_smoke.py — WP6③ run_replay.py 오프라인 does-it-run.

네트워크 없이 fetch 를 합성 데이터로 patch → runner 가 크래시 없이 go/no-go 카드 산출 +
학습 sink(memory) 폐쇄되는지 확인. (실 네트워크 run 은 별도 수동.)
"""

from __future__ import annotations

import json

import pandas as pd
import pytest


def _synthetic_df(n=60):
    idx = pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC")
    # 변동 있는 가격(매수/매도 트리거 유발)
    closes = [100.0 + 30.0 * ((i % 20) - 10) / 10.0 for i in range(n)]
    vols = [1e9] * n
    return pd.DataFrame({"close": closes, "volume": vols}, index=idx)


def test_run_replay_offline(monkeypatch, capsys):
    import scripts.run_replay as rr

    monkeypatch.setattr(rr, "fetch_upbit_daily", lambda market, count: _synthetic_df())
    monkeypatch.setattr("sys.argv", ["run_replay.py", "--market", "KRW-BTC", "--count", "60"])

    rc = rr.main()
    assert rc == 0

    out = capsys.readouterr().out
    card = json.loads(out)
    # 카드 구조 + 파이프라인 가동 증거
    for key in ("market", "bars", "trades", "sharpe", "max_drawdown_pct",
                "go_no_go", "memory_entries", "learned_outcomes"):
        assert key in card, f"카드 키 누락: {key}"
    assert card["bars"] == 60
    assert card["go_no_go"] in ("GO", "NO_GO", "MARGINAL")


def test_rsi_track_decides():
    """RsiReplayTrack 가 워밍업 후 buy/sell/hold 를 낸다(결정론)."""
    from scripts.run_replay import RsiReplayTrack
    from core.asset_track import MarketState

    track = RsiReplayTrack()
    actions = set()
    # 급등락 시퀀스로 RSI 양극단 유발
    for i, p in enumerate([100, 90, 80, 70, 60, 50, 40, 30, 20, 10,
                           20, 40, 60, 80, 100, 120, 140, 160, 180, 200]):
        st = MarketState(raw_market_data={"price": float(p)})
        d = track.generate_candidate(st)
        actions.add(d.action)
    assert "hold" in actions  # 워밍업 구간
    assert actions & {"buy", "sell"}  # 신호 발생
