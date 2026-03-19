"""SeonbiRang DB -- Supabase REST API + 로컬 JSONL 이중 기록"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Optional

import requests

from seonbirang.config import DBConfig

logger = logging.getLogger("seonbirang.db")

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_DATA_DIR = os.path.join(PROJECT_DIR, "data", "seonbirang")


class SeonbirangDB:
    """Supabase + 로컬 JSONL 이중 기록"""

    def __init__(self, config: DBConfig):
        self._url = config.supabase_url
        self._key = config.supabase_key
        self._enabled = bool(self._url and self._key)
        os.makedirs(LOCAL_DATA_DIR, exist_ok=True)

        self._session: Optional[requests.Session] = None
        if self._enabled:
            self._session = requests.Session()
            self._session.headers.update({
                "apikey": self._key,
                "Authorization": f"Bearer {self._key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            })
        else:
            logger.warning("Supabase 미설정 -- 로컬 JSONL만 기록")

    def _post(self, table: str, row: dict) -> bool:
        from utils.machine import get_machine_name
        row.setdefault("machine_name", get_machine_name())
        if not self._enabled or self._session is None:
            return False
        try:
            resp = self._session.post(
                f"{self._url}/rest/v1/{table}",
                json=row,
                timeout=10,
            )
            if resp.status_code in (200, 201):
                return True
            logger.error(f"DB 기록 실패 ({table}): {resp.status_code} {resp.text[:200]}")
            return False
        except Exception as e:
            logger.error(f"DB 기록 오류 ({table}): {e}")
            return False

    def _save_local(self, filename: str, row: dict):
        try:
            row["_saved_at"] = datetime.now(timezone.utc).isoformat()
            path = os.path.join(LOCAL_DATA_DIR, filename)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
        except Exception as e:
            logger.error(f"로컬 저장 오류 ({filename}): {e}")

    async def record_trade(self, action: dict):
        """거래 기록"""
        row = {
            "strategy": action.get("strategy"),
            "action": action.get("action"),
            "symbol": action.get("symbol"),
            "funding_rate": action.get("funding_rate"),
            "momentum_score": action.get("momentum_score"),
            "pnl_pct": action.get("pnl_pct"),
            "pnl_usdt": action.get("pnl_usdt"),
            "size_usdt": action.get("size_usdt"),
            "reason": action.get("reason", ""),
            "dry_run": action.get("dry_run", True),
            "success": action.get("success", False),
        }
        await asyncio.to_thread(self._post, "seonbirang_trades", dict(row))
        self._save_local("trades.jsonl", row)

    async def record_snapshot(
        self,
        total_balance: float,
        funding_summary: dict,
        rotation_summary: dict,
    ):
        """포트폴리오 스냅샷"""
        row = {
            "total_balance_usdt": total_balance,
            "funding_positions": json.dumps(
                funding_summary.get("positions", []), default=str
            ),
            "rotation_positions": json.dumps(
                rotation_summary.get("positions", []), default=str
            ),
            "funding_count": funding_summary.get("position_count", 0),
            "rotation_count": rotation_summary.get("position_count", 0),
            "total_funding_collected": funding_summary.get("total_funding_collected", 0),
            "total_unrealized_pnl": rotation_summary.get("total_unrealized_pnl", 0),
        }
        await asyncio.to_thread(self._post, "seonbirang_snapshots", dict(row))
        self._save_local("snapshots.jsonl", row)

    async def record_rankings(self, scan_type: str, rankings: list):
        """코인 순위 스냅샷"""
        row = {
            "scan_type": scan_type,
            "rankings": json.dumps(rankings[:20], default=str),
            "universe_size": len(rankings),
        }
        await asyncio.to_thread(self._post, "seonbirang_coin_rankings", dict(row))
        self._save_local("rankings.jsonl", row)

    async def record_error(self, phase: str, error: str):
        row = {"error_phase": phase, "error_message": error[:500], "timestamp": time.time()}
        self._save_local("errors.jsonl", row)
