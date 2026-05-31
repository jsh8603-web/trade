"""core/coin_track.py — CoinTrack(AssetTrack) BTC/KRW Directional 래퍼.

Orchestrator + ExternalDataAgent를 import+위임 방식으로 감싼다.
본체(run/decide/_evaluate_market_state) 분해·재구현 금지.
실제 외부 호출(Upbit/Supabase/Gemini)은 mock 주입으로 격리(테스트용).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from core.asset_track import AssetTrack, MarketState
from core.db import db

if TYPE_CHECKING:
    from agents.base_agent import Decision

PROJECT_DIR = Path(__file__).resolve().parent.parent

KST = timezone(timedelta(hours=9))

# regime → 권장 체크 간격(분)
_REGIME_INTERVALS: dict[str, int] = {
    "extreme_fear": 120,   # 극단 공포 → 2시간 (바닥 반등 대기)
    "fear": 240,           # 공포 → 4시간
    "neutral": 480,        # 중립 → 8시간
    "greed": 480,
    "extreme_greed": 240,  # 극단 탐욕 → 4시간 (과열 경계)
}


class CoinTrack(AssetTrack):
    """BTC/KRW Directional 에이전트 흐름 래퍼.

    SACRED: Orchestrator.run() / BaseStrategyAgent.decide() / _evaluate_market_state()
    본체 미변경 — 통째 위임(분해 금지).
    """

    def __init__(
        self,
        *,
        _market_data_override: dict | None = None,
        _portfolio_override: dict | None = None,
        _external_data_override: dict | None = None,
        _past_decisions_override: list | None = None,
    ) -> None:
        # 테스트 픽스처 주입용 override (mock-only 환경 지원)
        self._market_data_override = _market_data_override
        self._portfolio_override = _portfolio_override
        self._external_data_override = _external_data_override
        self._past_decisions_override = _past_decisions_override

    # ------------------------------------------------------------------
    # collect_market_state
    # ------------------------------------------------------------------

    def collect_market_state(self, as_of=None) -> MarketState:
        """시장 데이터 수집 → MarketState(raw 4종) 반환.

        as_of=None: 현재 시점(라이브 기본, 하위호환). as_of=<datetime>: 백테스트 PIT
          재구성 진입점 — raw_market_data["as_of"] 에 기록(PIT provider 소비는 후속 WP6).
        override 주입 시 그 값을 사용(mock 테스트용).
        실 환경에서는 subprocess로 scripts/ 호출 + ExternalDataAgent.collect_all().
        _evaluate_market_state()는 generate_candidate() 내부(run() 위임)이므로 여기서 호출 금지.
        """
        market_data = self._collect_market_data()
        portfolio = self._collect_portfolio()
        external_data = self._collect_external_data()
        past_decisions = self._load_past_decisions()

        if as_of is not None and "as_of" not in market_data:
            market_data = {**market_data, "as_of": as_of.isoformat()}

        return MarketState(
            raw_market_data=market_data,
            raw_external_data=external_data,
            raw_portfolio=portfolio,
            raw_past_decisions=past_decisions,
        )

    def _collect_market_data(self) -> dict:
        if self._market_data_override is not None:
            return self._market_data_override
        return _run_script("collect_market_data.py")

    def _collect_portfolio(self) -> dict:
        if self._portfolio_override is not None:
            return self._portfolio_override
        return _run_script("get_portfolio.py")

    def _collect_external_data(self) -> dict:
        if self._external_data_override is not None:
            return self._external_data_override
        from agents.external_data import ExternalDataAgent
        agent = ExternalDataAgent()
        return agent.collect_all()

    def _load_past_decisions(self) -> list:
        if self._past_decisions_override is not None:
            return self._past_decisions_override
        try:
            return db.select(
                "decisions",
                select="id,decision,reason,confidence,current_price,profit_loss,created_at",
                order="created_at.desc",
                limit=5,
            )
        except Exception:
            return []

    # ------------------------------------------------------------------
    # generate_candidate
    # ------------------------------------------------------------------

    def generate_candidate(self, state: MarketState) -> "Decision":
        """Orchestrator.run()을 통째로 위임해 Decision을 반환.

        run() 분해·부분 재구현 금지 = 동작분기 0.
        EMERGENCY_STOP(:179) 단락 경로도 run() 내부에서 그대로 처리된다.
        """
        from agents.orchestrator import Orchestrator  # noqa: PLC0415
        from agents.base_agent import Decision as Dec  # noqa: PLC0415

        orch = Orchestrator()
        result: dict = orch.run(
            market_data=state.raw_market_data,
            external_data=state.raw_external_data,
            portfolio=state.raw_portfolio,
            past_decisions=state.raw_past_decisions,
        )

        raw_decision = result.get("decision", {})
        if isinstance(raw_decision, Dec):
            return raw_decision

        # run()은 decision을 to_dict() 형태의 dict로 반환함 — Decision 재구성
        return Dec(
            decision=raw_decision.get("decision", "hold"),
            confidence=raw_decision.get("confidence", 0.0),
            reason=raw_decision.get("reason", ""),
            buy_score=raw_decision.get("buy_score", {}),
            trade_params=raw_decision.get("trade_params", {}),
            external_signal=raw_decision.get("external_signal_summary", {}),
            agent_name=raw_decision.get("agent_name", ""),
            timestamp=raw_decision.get("timestamp", ""),
        )

    # ------------------------------------------------------------------
    # recommended_next_check
    # ------------------------------------------------------------------

    def recommended_next_check(self, state: MarketState) -> datetime:
        """regime 기반 동적 next-check 권장 시각 반환.

        호출자(run_agents.py) 파이프라인 미변경 — 선택적 힌트.
        """
        fgi = _extract_fgi(state.raw_external_data)
        regime = _fgi_to_regime(fgi)
        interval_minutes = _REGIME_INTERVALS.get(regime, 480)
        return datetime.now(KST) + timedelta(minutes=interval_minutes)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _run_script(script_name: str) -> dict:
    """subprocess로 scripts/ 스크립트를 실행해 JSON dict 반환."""
    import subprocess  # noqa: PLC0415
    try:
        from scripts.hide_console import subprocess_kwargs  # type: ignore[import-not-found]
    except ImportError:
        def subprocess_kwargs(**extra: object) -> dict:  # type: ignore[misc]
            return dict(extra)
    try:
        result = subprocess.run(
            [sys.executable, f"scripts/{script_name}"],
            cwd=str(PROJECT_DIR),
            capture_output=True,
            text=True,
            timeout=60,
            **subprocess_kwargs(),
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        return {"error": f"{script_name} 실패 (rc={result.returncode})"}
    except Exception as exc:
        return {"error": str(exc)}


def _extract_fgi(external_data: dict) -> int:
    """external_data에서 FGI 값 추출 (기본 50)."""
    sources = external_data.get("sources", {})
    fg = sources.get("fear_greed", {})
    val = fg.get("current", {}).get("value") or external_data.get("fgi")
    try:
        return int(val)
    except (TypeError, ValueError):
        return 50


def _fgi_to_regime(fgi: int) -> str:
    if fgi <= 20:
        return "extreme_fear"
    if fgi <= 35:
        return "fear"
    if fgi <= 60:
        return "neutral"
    if fgi <= 80:
        return "greed"
    return "extreme_greed"
