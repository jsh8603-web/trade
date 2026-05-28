"""core/strategy.py — Strategy 인터페이스 분리(interface-only).

Strategy(ABC): 공통 추상 기반.
StrategyFamily(Enum): DIRECTIONAL / MARKET_NEUTRAL / HFT 3계열.

계열 매핑 (Phase 2까지 실제 배선 없음, 인터페이스+문서만):
  - AssetTrack (agents/ Directional 흐름) → DIRECTIONAL
  - scalp_ml/                             → HFT
  - kimchirang/                           → MARKET_NEUTRAL

INVARIANT: scalp_ml/ · kimchirang/ 코드 일절 미변경(독립 유지, import 0 보존).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum


class StrategyFamily(Enum):
    """전략 계열 택소노미.

    DIRECTIONAL  — AssetTrack 구현체 (CoinTrack 등). 방향성 매매.
    MARKET_NEUTRAL — kimchirang/. 헤지·차익 중립 전략.
    HFT          — scalp_ml/. 고빈도 단타 전략.
    """

    DIRECTIONAL = "directional"
    MARKET_NEUTRAL = "market_neutral"
    HFT = "hft"


# 계열 매핑 상수 (Phase 2 배선 전 참조용 문서)
FAMILY_MAPPING: dict[str, StrategyFamily] = {
    "AssetTrack": StrategyFamily.DIRECTIONAL,   # core/asset_track.py → CoinTrack 등
    "scalp_ml": StrategyFamily.HFT,             # scalp_ml/ (독립 모듈, Phase 2 통합)
    "kimchirang": StrategyFamily.MARKET_NEUTRAL, # kimchirang/ (독립 모듈, Phase 2 통합)
}


class Strategy(ABC):
    """전략 공통 추상 기반.

    AssetTrack 계열(Directional)은 이 인터페이스를 상속하거나 별도 구현할 수 있다.
    scalp_ml / kimchirang 은 Phase 2에서 이 계열로 통합 배선된다.
    현재 단계에서는 인터페이스 정의 + 계열 매핑 문서화만 수행.
    """

    @property
    @abstractmethod
    def family(self) -> StrategyFamily:
        """이 전략이 속하는 계열."""

    @property
    @abstractmethod
    def name(self) -> str:
        """전략 식별자."""
