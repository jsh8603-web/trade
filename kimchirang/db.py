"""Kimchirang DB -- Supabase REST API + 로컬 JSONL 이중 기록"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db import db

from kimchirang.config import DBConfig
from kimchirang.execution import ExecutionResult
from kimchirang.kp_engine import KPSnapshot

logger = logging.getLogger("kimchirang.db")

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_DATA_DIR = os.path.join(PROJECT_DIR, "data", "kimchirang")


class KimchirangDB:
    """core.db 어댑터 + 로컬 JSONL 이중 기록

    DB 테이블이 없거나 연결 실패해도 로컬 JSONL에 항상 저장한다.
    """

    def __init__(self, config: DBConfig):
        os.makedirs(LOCAL_DATA_DIR, exist_ok=True)

    def _post(self, table: str, row: dict) -> bool:
        """동기 INSERT (asyncio.to_thread에서 호출)"""
        from utils.machine import skip_trade_db, get_machine_name
        if skip_trade_db(table):
            return False
        # 머신 태그 자동 추가
        row.setdefault("machine_name", get_machine_name())
        try:
            db.insert(table, row, returning=False)
            return True
        except Exception as e:
            # machine_name 컬럼 미존재 등 스키마 불일치 — 제거 후 재시도
            if "machine_name" in str(e):
                row.pop("machine_name", None)
                try:
                    db.insert(table, row, returning=False)
                    return True
                except Exception as e2:
                    logger.error(f"DB 기록 오류 ({table}): {e2}")
                    return False
            logger.error(f"DB 기록 오류 ({table}): {e}")
            return False

    def _save_local(self, filename: str, row: dict):
        """로컬 JSONL 파일에 1행 추가"""
        try:
            row["_saved_at"] = datetime.now(timezone.utc).isoformat()
            path = os.path.join(LOCAL_DATA_DIR, filename)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
        except Exception as e:
            logger.error(f"로컬 저장 오류 ({filename}): {e}")

    async def record_trade(
        self,
        result: ExecutionResult,
        snapshot: KPSnapshot,
        pnl: Optional[float] = None,
        stats: Optional[dict] = None,
        hold_duration_min: Optional[float] = None,
        is_stop_loss: bool = False,
    ):
        """차익거래 기록 (Supabase + 로컬 이중 저장)"""
        action = result.action
        if is_stop_loss and action == "exit":
            action = "stop_loss"

        row = {
            "action": action,
            "kp_at_execution": result.kp_at_execution,
            "entry_kp": snapshot.entry_kp,
            "exit_kp": snapshot.exit_kp,
            "pnl_pct": pnl,
            "upbit_order_id": result.upbit_leg.order_id,
            "upbit_side": result.upbit_leg.side,
            "upbit_price": int(result.upbit_leg.filled_price) if result.upbit_leg.filled_price else None,
            "upbit_qty": result.upbit_leg.filled_qty,
            "binance_order_id": result.binance_leg.order_id,
            "binance_side": result.binance_leg.side,
            "binance_price": result.binance_leg.filled_price,
            "binance_qty": result.binance_leg.filled_qty,
            "fx_rate": snapshot.fx_rate,
            "funding_rate": snapshot.funding_rate,
            "spread_cost": (snapshot.upbit_spread_pct + snapshot.binance_spread_pct),
            "latency_ms": int(result.total_latency_ms),
            "dry_run": result.dry_run,
            "both_success": result.both_success,
            "hold_duration_min": hold_duration_min,
            "kp_stats": stats,
        }

        # Supabase 먼저 시도 (_save_local이 _saved_at 추가하기 전에)
        await asyncio.to_thread(self._post, "kimchirang_trades", dict(row))
        # 로컬 항상 저장
        self._save_local("trades.jsonl", row)

    async def record_kp_snapshot(self, snapshot: KPSnapshot, stats: dict):
        """KP 스냅샷 기록 (1분 간격 히스토리)"""
        row = {
            "mid_kp": snapshot.mid_kp,
            "entry_kp": snapshot.entry_kp,
            "exit_kp": snapshot.exit_kp,
            "kp_ma_1m": stats.get("kp_ma_1m", 0),
            "kp_ma_5m": stats.get("kp_ma_5m", 0),
            "kp_z_score": stats.get("kp_z_score", 0),
            "kp_velocity": stats.get("kp_velocity", 0),
            "spread_cost": stats.get("spread_cost", 0),
            "funding_rate": stats.get("funding_rate", 0),
            "upbit_bid": int(snapshot.upbit_bid) if snapshot.upbit_bid else None,
            "upbit_ask": int(snapshot.upbit_ask) if snapshot.upbit_ask else None,
            "binance_bid": snapshot.binance_bid,
            "binance_ask": snapshot.binance_ask,
            "fx_rate": snapshot.fx_rate,
        }

        # Supabase 먼저 시도 (_save_local이 _saved_at 추가하기 전에)
        await asyncio.to_thread(self._post, "kimchirang_kp_history", dict(row))
        # 로컬 항상 저장
        self._save_local("kp_history.jsonl", row)

    async def record_error(self, phase: str, error: str):
        """에러 기록

        kimchirang_trades의 CHECK 제약조건은 ('enter','exit','stop_loss')만 허용하므로
        에러는 별도 로컬 파일에만 기록한다. Supabase에는 넣지 않는다.
        """
        row = {
            "error_phase": phase,
            "error_message": error[:500],
            "timestamp": time.time(),
        }
        self._save_local("errors.jsonl", row)

    async def record_rl_model(self, model_info: dict):
        """RL 모델 성과 기록"""
        await asyncio.to_thread(self._post, "kimchirang_rl_models", dict(model_info))
        self._save_local("rl_models.jsonl", model_info)
