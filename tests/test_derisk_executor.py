"""tests/test_derisk_executor.py — SO-1 + SO-3 검증 게이트.

검증 항목:
  1. FakeExchange derisk_to_floor → floor 이하 축소
  2. query_live_positions 예외 → cancel 호출 + fail-open 아님
  3. 2회 연속 derisk_to_floor → idempotent (2회째 변화 0)
  4. import 정적검사 — brain/judge/llm/consensus/HRP import 0
  5. SO-3: IOC band 단계 확대 → -10% 도달 시 frozen_bag 마킹
  6. SO-3: frozen 후 해당 symbol submit 호출 0건
  7. SO-3: submit_ioc_limit 만 호출, market order 미사용
"""

from __future__ import annotations

import ast
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# 프로젝트 루트를 sys.path 에 추가
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.derisk_executor import (  # noqa: E402
    DeriskExecutor,
    FakeExchange,
    FillResult,
    Orderbook,
)


# ── 픽스처 ────────────────────────────────────────────────────────────

@pytest.fixture
def simple_exchange():
    """BTC 1.0 보유 FakeExchange (호가 충분, fill_ratio=1.0)."""
    return FakeExchange(positions={"BTC": 1.0}, mid_price=50_000.0)


@pytest.fixture
def executor(simple_exchange):
    return DeriskExecutor(simple_exchange)


# ── SO-1 테스트 ───────────────────────────────────────────────────────

class TestDeriskToFloor:
    def test_reduces_below_floor(self, executor, simple_exchange):
        """derisk_to_floor → BTC 잔여가 floor(0.3) 이하로 축소."""
        result = executor.derisk_to_floor({"BTC": 0.3}, reason="test")
        remaining = simple_exchange.query_live_positions().get("BTC", 0.0)
        assert remaining <= 0.3 + 1e-9, f"잔여={remaining} > floor=0.3"

    def test_query_failure_cancel_called_not_fail_open(self, tmp_path):
        """query_live_positions 예외 → cancel 호출됐고 fail-open(no-op) 아님."""
        exc_exchange = FakeExchange(positions={"BTC": 1.0}, raise_on_query=True)
        ex = DeriskExecutor(exc_exchange)

        result = ex.derisk_to_floor({"BTC": 0.0}, reason="failsafe_test")

        # cancel 호출 증명 (at least 1 — cancel_only + derisk 각 1)
        assert exc_exchange.cancelled_orders >= 1, "cancel_all_open_orders 미호출"
        # fail-open 아님: reason 에 query_failed 포함 (동작 기록)
        assert result is not None, "result None = fail-open"

    def test_idempotent_second_call_no_change(self, executor, simple_exchange):
        """2회 연속 derisk_to_floor → 2회째 reduced 변화 0 (idempotent)."""
        r1 = executor.derisk_to_floor({"BTC": 0.3}, reason="first")
        pos_after_1 = dict(simple_exchange._positions)

        r2 = executor.derisk_to_floor({"BTC": 0.3}, reason="second")
        pos_after_2 = dict(simple_exchange._positions)

        # 2회째: 이미 floor 이하 → 포지션 추가 변화 없음
        for sym, qty in pos_after_2.items():
            assert abs(qty - pos_after_1.get(sym, 0.0)) < 1e-9, (
                f"{sym}: 2회째 추가 감소 발생 {pos_after_1[sym]:.6f} → {qty:.6f}"
            )

    def test_cancel_only_blocks_entry(self, executor):
        """cancel_only → entry_blocked=True."""
        result = executor.cancel_only(reason="soft_halt")
        assert executor.entry_blocked
        assert result.fully_done is False

    def test_clear_entry_block(self, executor):
        """clear_entry_block → entry_blocked=False."""
        executor.cancel_only(reason="soft")
        executor.clear_entry_block()
        assert not executor.entry_blocked


# ── SO-1 import 정적 검사 ─────────────────────────────────────────────

class TestImportStaticCheck:
    FORBIDDEN = {"brain", "judge", "llm", "consensus", "hrp"}

    def test_no_forbidden_imports(self):
        """derisk_executor.py 에 brain/judge/llm/consensus/HRP import 0."""
        src = (PROJECT_ROOT / "core" / "derisk_executor.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.lower())
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.add(node.module.lower())
        violations = [f for f in self.FORBIDDEN if any(f in imp for imp in imported)]
        assert not violations, f"forbidden imports found: {violations}"


# ── SO-3 테스트: IOC ladder + frozen bag ─────────────────────────────

class TestEscalateLiquidation:
    def test_ioc_ladder_expands_and_frozen_bag_on_slippage(self, tmp_path, monkeypatch):
        """얕은 호가(fill_ratio=0.5) + 슬리피지 강제 → -10% 도달 시 frozen_bag 마킹.

        LADDER_BANDS=-0.01,-0.03,-0.05 (기본).
        각 band fill 후 누적 슬리피지가 MAX_SLIPPAGE(-0.10)를 넘으면 frozen.
        여기서는 슬리피지를 크게 만들기 위해 mid_price 대비 limit_price 차이를 강제.
        """
        frozen_path = tmp_path / "frozen_bag.json"
        monkeypatch.setattr("core.derisk_executor._FROZEN_BAG_PATH", frozen_path)
        # 슬리피지를 크게 만들기 위해 MAX_SLIPPAGE 를 작게 조정 (-0.005 = -0.5%)
        monkeypatch.setattr("core.derisk_executor.MAX_SLIPPAGE", -0.005)
        # ladder step 대기 0으로 단축
        monkeypatch.setattr("core.derisk_executor.LADDER_STEP_SEC", 0.0)

        # mid=100 / limit=99(-1%) / fill_ratio=1.0 → slippage=-0.01 per band
        ex = FakeExchange(positions={"BTC": 1.0}, mid_price=100.0, fill_ratio=1.0)
        executor = DeriskExecutor(ex)

        filled, frozen = executor._escalate_liquidation("BTC", 0.5, time.time())

        # frozen bag 마킹 확인
        assert frozen, "슬리피지 초과 시 frozen=True 기대"
        assert "BTC" in executor._frozen_symbols

        # frozen_bag.json 기록 확인
        assert frozen_path.exists(), "frozen_bag.json 파일 미생성"
        data = json.loads(frozen_path.read_text())
        symbols = [e["symbol"] for e in data]
        assert "BTC" in symbols, f"frozen_bag.json에 BTC 없음: {data}"

    def test_frozen_symbol_no_submit(self, tmp_path, monkeypatch):
        """frozen 처리된 symbol은 derisk_to_floor 재호출 시 submit 0건."""
        frozen_path = tmp_path / "frozen_bag.json"
        monkeypatch.setattr("core.derisk_executor._FROZEN_BAG_PATH", frozen_path)
        monkeypatch.setattr("core.derisk_executor.MAX_SLIPPAGE", -0.005)
        monkeypatch.setattr("core.derisk_executor.LADDER_STEP_SEC", 0.0)

        ex = FakeExchange(positions={"BTC": 1.0}, mid_price=100.0, fill_ratio=1.0)
        executor = DeriskExecutor(ex)

        # 1회: frozen 트리거
        executor.derisk_to_floor({"BTC": 0.0}, reason="first")
        call_count_after_first = len(ex.submit_calls)

        # 2회: BTC 는 frozen → submit 추가 0건
        executor.derisk_to_floor({"BTC": 0.0}, reason="second")
        new_calls = len(ex.submit_calls) - call_count_after_first

        assert new_calls == 0, f"frozen symbol 에 submit 발생: {new_calls}건"

    def test_only_ioc_limit_no_market_order(self, simple_exchange, executor):
        """submit_ioc_limit 만 호출, market order(side=market 류) 미사용."""
        executor.derisk_to_floor({"BTC": 0.0}, reason="ioc_check")
        for call in simple_exchange.submit_calls:
            # limit_price > 0 = IOC 지정가 (market=price 없음 or 0)
            assert call.get("limit_price", 0.0) > 0.0, f"market order 의심: {call}"
            assert call.get("side") == "sell"


# ── 통합: cancel_only + derisk_to_floor 연계 ─────────────────────────

class TestCancelOnlyAndDerisk:
    def test_cancel_only_then_derisk(self, simple_exchange):
        """cancel_only 후 derisk_to_floor 호출 시 정상 집행."""
        ex = simple_exchange
        executor = DeriskExecutor(ex)
        executor.cancel_only(reason="soft")
        result = executor.derisk_to_floor({"BTC": 0.2}, reason="hard")
        remaining = ex.query_live_positions().get("BTC", 0.0)
        assert remaining <= 0.2 + 1e-9
