"""core/asset_track.py — AssetTrack ABC + MarketState dataclass.

AssetTrack: Directional 계열 자산 추상 기반. 구현체는 3 추상메서드를 제공해야 한다.
MarketState: 수집 단계에서 raw 4종을 무손실 보존하는 컨테이너.
Decision은 agents/base_agent.py:111 dataclass를 그대로 사용(이동·복제 금지).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agents.base_agent import Decision


@dataclass
class MarketState:
    """수집 단계 raw 4종을 무손실 보존하는 컨테이너.

    raw_market_data, raw_external_data, raw_portfolio, raw_past_decisions 를
    그대로 보존하고, 파생 프로퍼티(timestamp/asset/price)는 읽기전용으로 제공.
    """

    raw_market_data: dict[str, Any] = field(default_factory=dict)
    raw_external_data: dict[str, Any] = field(default_factory=dict)
    raw_portfolio: dict[str, Any] = field(default_factory=dict)
    raw_past_decisions: list[Any] = field(default_factory=list)

    @property
    def timestamp(self) -> str | None:
        """raw_market_data 에서 파생한 타임스탬프."""
        return self.raw_market_data.get("timestamp")

    @property
    def asset(self) -> str | None:
        """raw_market_data 에서 파생한 자산 심볼."""
        return self.raw_market_data.get("market") or self.raw_market_data.get("asset")

    @property
    def price(self) -> float | None:
        """raw_market_data 에서 파생한 현재가."""
        val = self.raw_market_data.get("current_price") or self.raw_market_data.get("price")
        return float(val) if val is not None else None


class AssetTrack(ABC):
    """Directional 계열 자산 추상 기반 클래스.

    구현체(CoinTrack 등)는 세 추상메서드를 모두 제공해야 한다.
    M1 택소노미: AssetTrack = DIRECTIONAL 계열 전용.
    scalp_ml(HFT)·kimchirang(MarketNeutral)은 Strategy 계열(core/strategy.py) 별도 분리.

    nautilus_trader 추상화 패턴 참조:
      Actor.on_start / on_data / on_bar → collect_market_state / generate_candidate 대응.
    """

    @abstractmethod
    def collect_market_state(self, as_of: "datetime | None" = None) -> "MarketState":
        """시장 상태를 수집해 MarketState 로 반환.

        as_of=None: 현재 시점 수집(라이브 기본 동작, 하위호환 보존).
        as_of=<datetime>: 그 시점 PIT(point-in-time) 재구성용 진입점 — 백테스트
          리플레이가 과거 시점 환경(가격뿐 아니라 macro/FGI/sentiment)을 lookahead
          없이 재구성하도록 구현체가 PIT provider 로 분기. (WP6: provider 소비는 후속)
        실제 외부 호출(API·DB·스크립트)은 구현체가 담당.
        _evaluate_market_state()는 generate_candidate() 내부(run() 위임) 귀속이므로
        여기서 중복 호출 금지.
        """

    @abstractmethod
    def generate_candidate(self, state: "MarketState") -> "Decision":
        """MarketState 를 입력받아 매매 결정 후보를 반환.

        CoinTrack 구현체는 Orchestrator.run()을 통째로 위임(분해 금지).
        """

    @abstractmethod
    def recommended_next_check(self, state: "MarketState") -> datetime:
        """다음 점검 권장 시각을 반환(regime 기반 동적 interval).

        호출자(run_agents.py) 파이프라인은 미변경 — 이 값은 선택적 힌트.
        """
