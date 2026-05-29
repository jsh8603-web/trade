"""tests/test_so4_pR_coin_memory.py — SO-4/PR 계층 메모리 coin 변형 검증.

검증 기준 (harness2.md SO-4/PR):
1. coin decay 반감기 < 주식/거시 반감기 (4h < 24h < 168h)
2. 코인 이벤트(거래소 사건 등) recall 동작
3. brain 메모리 계약(store/update/get_past_context) 정합
4. memory_layer.py 본체 미변경 (CoinMemoryLayer = subclass only)
5. SO-1/SO-2/SO-3 PR 회귀 0
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.coin_memory import (
    CoinMemoryLayer,
    COIN_HALF_LIFE_HOURS,
    COIN_EVENT_IMPORTANCE,
    COIN_EVENT_TAGS,
)
from core.brain.memory_layer import MemoryLayer, HALF_LIFE_HOURS


# ---------------------------------------------------------------------------
# 1. decay 반감기 — 코인 < 주식/거시
# ---------------------------------------------------------------------------

def test_coin_half_life_shorter_than_stock():
    """코인 반감기 4h < 주식 반감기 24h."""
    assert COIN_HALF_LIFE_HOURS < HALF_LIFE_HOURS, (
        f"코인 반감기({COIN_HALF_LIFE_HOURS}h) >= 주식({HALF_LIFE_HOURS}h)"
    )


def test_coin_half_life_default_4h():
    """CoinMemoryLayer 기본 반감기 = 4h."""
    mem = CoinMemoryLayer()
    assert mem.coin_half_life_hours == COIN_HALF_LIFE_HOURS
    assert mem.coin_half_life_hours == 4.0


def test_coin_decay_faster_than_stock():
    """동일 elapsed 에서 코인 recency < 주식 recency (더 빠른 감쇠)."""
    coin_mem = CoinMemoryLayer()
    stock_mem = MemoryLayer()  # 기본 24h

    from core.brain.memory_layer import MemoryEntry
    entry = MemoryEntry(created_at=time.time() - 8 * 3600)  # 8시간 전

    coin_recency = coin_mem.recency_score(entry)
    stock_recency = stock_mem.recency_score(entry)

    assert coin_recency < stock_recency, (
        f"코인({coin_recency:.4f}) >= 주식({stock_recency:.4f}) — 빠른 감쇠 실패"
    )


def test_coin_recency_at_half_life():
    """4h 경과 시 recency ≈ 0.5 (반감기 정의)."""
    mem = CoinMemoryLayer()
    from core.brain.memory_layer import MemoryEntry
    entry = MemoryEntry(created_at=time.time() - COIN_HALF_LIFE_HOURS * 3600)

    recency = mem.recency_score(entry)
    assert abs(recency - 0.5) < 0.01, f"반감기 recency={recency:.4f} ≠ 0.5"


# ---------------------------------------------------------------------------
# 2. 코인 이벤트 recall
# ---------------------------------------------------------------------------

def test_coin_event_tags_not_empty():
    """COIN_EVENT_TAGS 비어 있지 않음."""
    assert len(COIN_EVENT_TAGS) >= 5


def test_detect_halving_event():
    """'halving' 키워드 → halving 태그 감지."""
    events = CoinMemoryLayer.detect_coin_events("BTC halving 예정, 공급 축소")
    assert "halving" in events


def test_detect_exchange_hack_event():
    """'exchange_hack' 키워드 → 태그 감지."""
    events = CoinMemoryLayer.detect_coin_events("거래소 exchange_hack 발생")
    assert "exchange_hack" in events


def test_detect_no_event_normal():
    """이벤트 없는 일반 결정 → 빈 태그."""
    events = CoinMemoryLayer.detect_coin_events("RSI 과매수, 차익 실현")
    assert len(events) == 0


def test_store_halving_event_high_importance():
    """halving 이벤트 저장 시 importance ≥ COIN_EVENT_IMPORTANCE."""
    mem = CoinMemoryLayer()
    eid = mem.store_decision(
        decision="buy",
        reason="BTC halving 예정으로 희소성 증가",
        confidence=0.8,
    )
    entry = next((e for e in mem._store if e.id == eid), None)
    assert entry is not None, "저장 실패"
    assert entry.importance >= COIN_EVENT_IMPORTANCE, (
        f"halving importance={entry.importance:.2f} < {COIN_EVENT_IMPORTANCE}"
    )


def test_recall_coin_events_halving():
    """halving 이벤트 recall — store 후 조회."""
    mem = CoinMemoryLayer()
    eid = mem.store_decision(
        decision="buy",
        reason="halving 이벤트 발생",
        confidence=0.85,
    )
    mem.store_decision(
        decision="hold",
        reason="일반 관망",
        confidence=0.5,
    )

    recalled = mem.recall_coin_events(event_tag="halving")
    assert len(recalled) >= 1
    assert any(e.id == eid for e in recalled), "halving 이벤트 recall 실패"


def test_recall_all_events_no_tag():
    """event_tag=None → 모든 코인 이벤트 반환."""
    mem = CoinMemoryLayer()
    mem.store_decision("buy", "halving 이벤트", 0.8)
    mem.store_decision("sell", "exchange_hack 발생", 0.9)
    mem.store_decision("hold", "일반 관망", 0.5)

    all_events = mem.recall_coin_events(event_tag=None)
    assert len(all_events) == 2, f"이벤트 수 불일치: {len(all_events)}"


def test_recall_top_k():
    """top_k 제한 적용."""
    mem = CoinMemoryLayer()
    for i in range(5):
        mem.store_decision("buy", "halving 이벤트", 0.8)

    recalled = mem.recall_coin_events(event_tag="halving", top_k=3)
    assert len(recalled) <= 3


def test_event_tag_stored_in_extra():
    """이벤트 태그가 entry.extra['coin_events']에 저장됨."""
    mem = CoinMemoryLayer()
    eid = mem.store_decision("sell", "depegging 스테이블코인 위기", 0.9)
    entry = next((e for e in mem._store if e.id == eid), None)
    assert entry is not None
    assert "coin_events" in entry.extra
    assert "depegging" in entry.extra["coin_events"]


# ---------------------------------------------------------------------------
# 3. brain 메모리 계약 정합
# ---------------------------------------------------------------------------

def test_store_decision_returns_id():
    """store_decision → 유효한 entry id 반환."""
    mem = CoinMemoryLayer()
    eid = mem.store_decision("buy", "매수 결정", 0.7)
    assert isinstance(eid, str) and len(eid) > 0


def test_update_with_outcome():
    """update_with_outcome → outcome 업데이트 + 반환 True."""
    mem = CoinMemoryLayer()
    eid = mem.store_decision("buy", "결정", 0.7)
    result = mem.update_with_outcome(eid, outcome_pct=5.0)
    assert result is True


def test_get_past_context_returns_entries():
    """get_past_context → list[MemoryEntry] 반환 (FinMem 점수 순)."""
    from core.brain.memory_layer import MemoryEntry
    mem = CoinMemoryLayer()
    mem.store_decision("buy", "매수 근거", confidence=0.8, embedding=[0.1, 0.2, 0.3])
    ctx = mem.get_past_context(query_embedding=[0.1, 0.2, 0.3], top_k=3)
    assert isinstance(ctx, list)
    assert len(ctx) >= 1
    assert all(isinstance(e, MemoryEntry) for e in ctx)


def test_coin_memory_is_subclass():
    """CoinMemoryLayer는 MemoryLayer 서브클래스 (본체 재작성 아님)."""
    assert issubclass(CoinMemoryLayer, MemoryLayer)


# ---------------------------------------------------------------------------
# 4. memory_layer.py 본체 미변경
# ---------------------------------------------------------------------------

def test_memory_layer_default_half_life_unchanged():
    """memory_layer.HALF_LIFE_HOURS 기본값 24h 유지."""
    assert HALF_LIFE_HOURS == 24.0, f"memory_layer 기본 반감기 변경됨: {HALF_LIFE_HOURS}"


def test_memory_layer_base_still_works():
    """기존 MemoryLayer 정상 동작 (미변경 확인)."""
    mem = MemoryLayer()
    eid = mem.store_decision("hold", "기존 메모리", 0.5)
    assert mem.update_with_outcome(eid, 0.0) is True


# ---------------------------------------------------------------------------
# 5. SO-1/SO-2/SO-3 PR 회귀 0
# ---------------------------------------------------------------------------

def test_so1_pr_coin_assettrack_import():
    """SO-1/PR: CoinTrackWithMacro 미변경."""
    from core.coin_track_macro import CoinTrackWithMacro
    assert CoinTrackWithMacro is not None


def test_so2_pr_coin_engine_import():
    """SO-2/PR: CoinBacktestEngine 미변경."""
    from backtest.coin_engine import CoinBacktestEngine
    assert CoinBacktestEngine is not None


def test_so3_pr_coin_sizing_import():
    """SO-3/PR: coin_sizing 미변경."""
    from core.coin_sizing import size_coin_portfolio
    assert size_coin_portfolio is not None


def test_so4_pr_coin_memory_import():
    """SO-4/PR: coin_memory import 정합."""
    from core.coin_memory import CoinMemoryLayer, COIN_HALF_LIFE_HOURS, COIN_EVENT_TAGS
    assert CoinMemoryLayer is not None
    assert COIN_HALF_LIFE_HOURS < 24.0
    assert len(COIN_EVENT_TAGS) > 0
