"""core/coin_memory.py — 계층 메모리 coin 변형 (SO-4/PR).

WHY: 코인 변동성은 주식/거시보다 빠름 → decay 반감기 짧게(4h 기본).
     코인 이벤트(반감기·거래소 사건) 태그 → 높은 importance + recall.
     메모리 본체(memory_layer.py) 재작성 금지 — decay 파라미터·이벤트 태그만 변형.

변형표 #3 (Phase R):
- COIN_HALF_LIFE_HOURS = 4.0  (주식 24h, 거시 168h vs 코인 4h)
- 코인 이벤트 태그: "halving", "exchange_hack", "delisting", "depegging", "regulatory"
- 이벤트 recall: importance 가중치 높게 (0.8+)
- brain 메모리 계약(store_decision/update_with_outcome/get_past_context) 정합 유지

SACRED:
- memory_layer.py 본체 미변경 (subclass로 변형만)
- execute_trade.py 실주문·run_cycle 미변경
- Phase0~6 본체 미변경
"""

from __future__ import annotations

import time
from typing import Any, List, Optional

from core.brain.memory_layer import MemoryLayer, MemoryEntry

# ── 코인 전용 파라미터 ───────────────────────────────────────────────
COIN_HALF_LIFE_HOURS = 4.0      # 코인: 4h (주식 24h, 거시 168h보다 짧음)
COIN_ALPHA_DECAY    = 0.5       # 동일 밑수, 반감기만 단축
COIN_EVENT_IMPORTANCE = 0.85    # 코인 이벤트 메모리 중요도

# 코인 이벤트 태그 목록
COIN_EVENT_TAGS = frozenset({
    "halving",           # BTC/LTC 반감기
    "exchange_hack",     # 거래소 해킹 (Mt.Gox, FTX 류)
    "delisting",         # 상폐 사건
    "depegging",         # 스테이블코인 디페깅
    "regulatory",        # 규제 이슈 (SEC, 중국 금지 등)
    "whale_move",        # 고래 대규모 이동
    "listing",           # 메이저 거래소 신규 상장
})


class CoinMemoryLayer(MemoryLayer):
    """계층 메모리 코인 변형.

    memory_layer.MemoryLayer 상속 — decay 파라미터·이벤트 태그만 변형.
    brain 계약(store_decision/update_with_outcome/get_past_context) 완전 호환.
    """

    def __init__(
        self,
        max_entries: int = 200,
        half_life_hours: float = COIN_HALF_LIFE_HOURS,
        alpha: float = COIN_ALPHA_DECAY,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            max_entries=max_entries,
            half_life_hours=half_life_hours,
            alpha=alpha,
            **kwargs,
        )

    # ── 이벤트 태그 감지 ─────────────────────────────────────────────

    @staticmethod
    def detect_coin_events(reason: str, extra: Optional[dict] = None) -> List[str]:
        """reason/extra 에서 코인 이벤트 태그를 감지."""
        text = reason.lower() + " " + str(extra or "").lower()
        return [tag for tag in COIN_EVENT_TAGS if tag in text]

    # ── store_decision 오버라이드 — 이벤트 importance 강화 ────────────

    def store_decision(
        self,
        decision: str,
        reason: str = "",
        confidence: float = 0.0,
        importance: float = 0.5,
        embedding: Optional[list] = None,
        **extra_kwargs: Any,
    ) -> str:
        """코인 이벤트 감지 시 importance 자동 강화.

        memory_layer.store_decision(**extra) 시그니처 유지.
        """
        events = self.detect_coin_events(reason, extra_kwargs)
        if events:
            importance = max(importance, COIN_EVENT_IMPORTANCE)
            extra_kwargs["coin_events"] = events

        return super().store_decision(
            decision=decision,
            reason=reason,
            confidence=confidence,
            importance=importance,
            embedding=embedding,
            **extra_kwargs,
        )

    # ── 이벤트 전용 recall ───────────────────────────────────────────

    def recall_coin_events(
        self,
        event_tag: Optional[str] = None,
        top_k: int = 5,
    ) -> List[MemoryEntry]:
        """코인 이벤트 태그로 메모리 조회.

        event_tag=None → 모든 코인 이벤트 반환.
        """
        results = []
        for entry in self._store:
            # store_decision의 **extra가 entry.extra dict에 직접 저장됨
            tags = entry.extra.get("coin_events", [])
            if not tags:
                continue
            if event_tag is None or event_tag in tags:
                results.append(entry)

        # importance + recency 혼합 정렬
        now = time.time()
        results.sort(
            key=lambda e: (
                e.importance * 0.6
                + self.recency_score(e, now) * 0.4
            ),
            reverse=True,
        )
        return results[:top_k]

    @property
    def coin_half_life_hours(self) -> float:
        """현재 coin 반감기 반환."""
        return self.half_life_hours
