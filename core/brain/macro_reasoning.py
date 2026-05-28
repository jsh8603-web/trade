"""
macro_reasoning.py — LLM 거시추론 노드 (macro-trigger 시에만 enrich, 평상시 결정론 baseline).

설계 정합 (§5.8-D, §5.8 필수요건):
- regime_classifier(결정론·무료)가 매 사이클 baseline 을 채우고,
  macro_reasoning(LLM)은 *macro-trigger 시에만* macro_view 를 enrich (C3 freshness≠liveness).
- macro 노드는 thesis + **최강 반대 thesis** 동반 (§5.8-D).
- C2 abstain: LLM 확신 부족/contamination probe 실패 시 baseline 유지(조정 0).
- 입력: A(분류기) + B(IC baseline) + C(리포트, 지표와 동급) + vintage + E(과거국면).
- 출력: stance(슬리브별 tilt) — regime_to_weights 의 BL View 입력.
- 리포트(§5.8-C) 통합 hook + §5.8-H ③ 리포트 발산 채널.

설계 §4 라우팅: 평상시 Qwen 로컬, 트리거 시 Claude deep. 본 노드는 stateless 일회성 호출 (§4.1).

github 차용 (입출력 계약 확인 후 어댑트):
- TradingAgents agents/analysts/fundamentals_analyst.py:create_fundamentals_analyst
    패턴: node(state) → prompt(system_message) | llm → report 문자열을 state 에 주입.
    여기선 report 대신 *구조화 stance dict* 를 강제(JSON) → BL View 로 직접 소비.
- AlpacaTradingAgent Macro Analyst (quick/deep, Qwen/Ollama/Claude) — provider 추상화 참조.

미해결 가정:
- LLM provider 는 brain/llm_provider.py(별도, §1 스켈레톤)에 위임 — 여기선 Protocol 만 의존.
- contamination probe(§5.8-F)는 인터페이스 hook 으로 두고, 실제 익명화/코사인 계산은
  embedder + probe 유틸에 위임(아직 미구현 → probe 미제공 시 보수적으로 abstain 안 함, 로깅만).
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Optional, Protocol

from .macro_schema import Bloc, MacroView, RegimeLabel, ViewStatus
from .regime_to_weights import SLEEVES

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 의존 Protocol (느슨한 결합 — brain/llm_provider.py 가 구현)
# ---------------------------------------------------------------------------
class LLMProvider(Protocol):
    def complete(self, system: str, user: str, json_mode: bool = True) -> str:
        """stateless 일회성 호출 (§4.1). json_mode 면 JSON 문자열 반환."""
        ...


class ReportStore(Protocol):
    """§5.8-C RAG 리포트 스토어 — 백그라운드 Qwen 사전적재, trigger 시 retrieve only."""
    def retrieve(self, query: str, as_of_ts: Optional[float], k: int = 5) -> list:
        """PIT causal-mask 검색 (as_of 이전 발표분만). 각 항목 = {text, source, release_ts}."""
        ...


@dataclass
class MacroTrigger:
    """macro-trigger 컨텍스트 — 무엇이 LLM enrich 를 촉발했는가 (§3 자산배분 트리거)."""
    reason: str          # "regime_flip" | "macro_surprise" | "report_divergence" | "manual"
    detail: dict


# ---------------------------------------------------------------------------
# 거시추론 노드
# ---------------------------------------------------------------------------
class MacroReasoningNode:
    """
    baseline MacroView 를 LLM stance 로 enrich. 평상시 호출 안 됨 (baseline 그대로).

    흐름:
      1) trigger 없으면 baseline 그대로 반환 (비용 0, C3).
      2) §5.8-C 리포트 retrieve (PIT) + §5.8-H 과거 보정 메모리 retrieve.
      3) LLM 에 thesis + 최강 반대 thesis + stance(JSON) 요청.
      4) (옵션) contamination probe → 실패 시 C2 abstain (baseline 유지).
      5) stance 를 macro_view 에 주입 + caution flag 전파.
    """

    def __init__(
        self,
        llm: Optional[LLMProvider] = None,
        report_store: Optional[ReportStore] = None,
        correction_memory=None,   # IndicatorEventCorrelation (§5.8-H) — 보정 메모리 조회.
    ):
        self.llm = llm
        self.report_store = report_store
        self.correction_memory = correction_memory

    def enrich(
        self,
        baseline: MacroView,
        trigger: Optional[MacroTrigger] = None,
    ) -> MacroView:
        # (1) 평상시 — baseline 그대로 (C3 결정론 baseline).
        if trigger is None or self.llm is None:
            return baseline
        if baseline.status == ViewStatus.UNAVAILABLE:
            return baseline   # 근거 없으면 LLM 도 abstain.

        usd = baseline.regime(Bloc.USD)
        if usd is None:
            return baseline

        # (2) 리포트 + 과거 보정 메모리 retrieve (PIT).
        reports = self._retrieve_reports(baseline)
        corrections = self._retrieve_corrections(baseline)

        # (3) LLM thesis + counter-thesis + stance.
        try:
            parsed = self._call_llm(baseline, trigger, reports, corrections)
        except Exception as e:
            logger.warning("macro_reasoning LLM failed → abstain (baseline): %s", e)
            return baseline

        # (4) contamination probe hook (§5.8-F) — 미구현 시 통과(로깅).
        if not self._contamination_ok(baseline, parsed):
            logger.info("contamination probe failed → C2 abstain")
            baseline.caution_flags.append("contamination_abstain")
            return baseline

        # (5) stance 주입 + caution 전파.
        return self._apply(baseline, parsed, corrections)

    # ------------------------------------------------------------- 내부 단계
    def _retrieve_reports(self, mv: MacroView) -> list:
        if self.report_store is None:
            return []
        usd = mv.regime(Bloc.USD)
        q = f"current macro regime {usd.regime_now.value} growth inflation outlook"
        try:
            return self.report_store.retrieve(q, as_of_ts=mv.data_as_of_ts, k=5)
        except Exception:
            return []

    def _retrieve_corrections(self, mv: MacroView) -> list:
        """§5.8-H ④: 유사 거시 재현 시 과거 오판 보정을 surface → confidence 하향 입력."""
        if self.correction_memory is None:
            return []
        usd = mv.regime(Bloc.USD)
        try:
            return self.correction_memory.recall_similar(
                regime=usd.regime_now,
                signature=usd.evidence,
                as_of_ts=mv.data_as_of_ts,
            )
        except Exception:
            return []

    def _call_llm(self, mv, trigger, reports, corrections) -> dict:
        usd = mv.regime(Bloc.USD)
        krw = mv.regime(Bloc.KRW)
        system = (
            "You are a macro asset-allocation analyst. Given a deterministic Investment-Clock "
            "regime baseline plus PIT-timestamped research, output a JSON object with: "
            "thesis (str), counter_thesis (str, the STRONGEST opposing view), "
            f"stance (object mapping each of {SLEEVES} to a float tilt in [-1,1] vs baseline), "
            "confidence (float 0..1). If evidence is weak or conflicting, set stance near 0 "
            "(abstain) and lower confidence. Always provide the counter_thesis."
        )
        user = json.dumps({
            "trigger": {"reason": trigger.reason, "detail": trigger.detail},
            "regime_now_usd": usd.regime_now.value,
            "regime_forecast_usd": (usd.regime_forecast.value if usd.regime_forecast else None),
            "regime_now_krw": (krw.regime_now.value if krw else None),
            "confidence_usd": round(usd.confidence_now, 3),
            "evidence": usd.evidence,
            "reports": [r.get("text", "")[:1200] for r in reports],
            "past_corrections": [
                {"hint": c.get("hint", ""), "lag": c.get("lag")} for c in corrections
            ],
        }, ensure_ascii=False)

        raw = self.llm.complete(system, user, json_mode=True)
        parsed = json.loads(raw)
        # 스키마 방어 — stance 누락/형식오류면 빈 stance(=abstain).
        stance = parsed.get("stance", {})
        parsed["stance"] = {s: float(stance.get(s, 0.0)) for s in SLEEVES}
        parsed["confidence"] = float(parsed.get("confidence", 0.0))
        parsed.setdefault("thesis", "")
        parsed.setdefault("counter_thesis", "")
        return parsed

    def _contamination_ok(self, mv, parsed) -> bool:
        """
        §5.8-F contamination probe hook. 원본 vs 익명화 스탠스 코사인<0.7 → 그 시기 abstain.
        실제 익명화/코사인은 embedder+probe 유틸에 위임 — 미연동 시 통과(보수적 차단 아님, 로깅).
        """
        # TODO(probe): embedder 연동 후 익명화 재호출 + 코사인 비교. 현재는 항상 통과.
        return True

    def _apply(self, mv, parsed, corrections) -> MacroView:
        confidence = parsed["confidence"]
        # 과거 보정 메모리가 "이 패턴 오판 선행" 이면 confidence 하향 + caution (§5.8-H ④).
        if corrections:
            confidence *= 0.7
            mv.caution_flags.append("past_misjudgment_pattern")
            mv.caution_flags.extend(
                f"correction:{c.get('event','?')}" for c in corrections[:2]
            )

        # confidence 낮으면 stance 축소 (C2 abstain 연속화) → BL τ·Ω 확대 효과.
        stance = {s: v * confidence for s, v in parsed["stance"].items()}

        mv.stance = stance
        mv.rationale = parsed["thesis"]
        mv.counter_thesis = parsed["counter_thesis"]
        mv.as_of_ts = time.time()   # enrich 시각 갱신.
        return mv
