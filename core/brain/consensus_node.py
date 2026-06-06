"""core/brain/consensus_node.py — 고-스테이크스 배분 변경 LLM 합의 검토 (down-only de-risk).

§4.2 consensus(SO-3): portfolio_orchestrator.is_high_stakes 가 고-스테이크스(regime 전환·배분
≥10% 변경·누적 ≥25%)를 결정론으로 감지한 뒤, 본 노드가 LLM 으로 그 변경의 타당성을 검토한다.

★down-only(FHC/judge 철학 정합 — RESULTS C3 attenuation-only): LLM 은 배분을 prior(보수 baseline)
  쪽으로 **후퇴(de-risk)만** 할 수 있고 증폭은 불가. 즉 LLM 환각이 비중을 키우는 경로가 봉인된다.
★off/llm None/오류 → approve(de_risk=0) = baseline(byte-identical). 실주문은 별도(사람 게이트).
"""
from __future__ import annotations

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ConsensusNode:
    """고-스테이크스 배분 변경 LLM 검토 → {approve, de_risk(0..1), reason}. down-only."""

    def __init__(self, llm=None):
        self.llm = llm

    def review(self, *, weights: dict, prior: dict, regime_now: str = "",
               trigger_detail: Optional[dict] = None) -> dict:
        if self.llm is None:
            return {"approve": True, "de_risk": 0.0, "reason": "abstain(no llm)"}
        try:
            system = (
                "You are a risk committee reviewing a HIGH-STAKES allocation change before it is "
                "applied. Output JSON: approve(bool), de_risk(float 0..1 = how much to retreat "
                "toward the conservative prior), reason(str). ★DOWN-ONLY: you may ONLY de-risk "
                "(pull weights toward the prior), NEVER amplify or add new bets. If the change is "
                "well-justified, de_risk=0. If it is over-concentrated, weakly-evidenced, or "
                "chases momentum into a high-stakes regime, raise de_risk toward 1."
            )
            user = json.dumps({
                "regime_now": regime_now,
                "proposed_weights": weights,
                "conservative_prior": prior,
                "trigger": trigger_detail or {},
            }, ensure_ascii=False)
            raw = self.llm.complete(system, user, json_mode=True)
            p = json.loads(raw) if isinstance(raw, str) else raw
            if not isinstance(p, dict):
                return {"approve": True, "de_risk": 0.0, "reason": "parse_fail"}
            dr = float(p.get("de_risk", 0.0))
            dr = 0.0 if dr < 0 else (1.0 if dr > 1 else dr)   # clip [0,1] = down-only 봉인
            return {"approve": bool(p.get("approve", True)), "de_risk": dr,
                    "reason": str(p.get("reason", ""))[:300]}
        except Exception as e:
            logger.warning("consensus review 실패 → approve(de_risk 0): %s", e)
            return {"approve": True, "de_risk": 0.0, "reason": f"error:{e}"}


def apply_consensus_derisk(weights: dict, prior: dict, de_risk: float) -> dict:
    """down-only 적용 — w' = (1-de_risk)·w + de_risk·prior → 합=1 재정규화.

    de_risk=0 → weights 그대로 / de_risk=1 → prior 완전 후퇴. 증폭 없음(prior 쪽 단방향).
    """
    if de_risk <= 0:
        return dict(weights)
    raw = {k: (1.0 - de_risk) * weights.get(k, 0.0) + de_risk * prior.get(k, weights.get(k, 0.0))
           for k in weights}
    tot = sum(raw.values())
    return {k: v / tot for k, v in raw.items()} if tot > 0 else dict(weights)


def build_consensus_node(*, use_claude: bool = True) -> ConsensusNode:
    """ConsensusNode 실배선 — ClaudeProvider(OAuth) 어댑터 주입. 실패/off → llm None(abstain)."""
    llm = None
    if use_claude:
        try:
            from core.assume.loop_factory import GenerateToComplete
            from core.brain.llm_provider import ClaudeProvider
            llm = GenerateToComplete(ClaudeProvider())
            logger.info("ConsensusNode LLM 실배선: Claude(OAuth)")
        except Exception as e:
            logger.warning("ConsensusNode llm 배선 실패 → abstain: %s", e)
            llm = None
    return ConsensusNode(llm=llm)


if __name__ == "__main__":
    # 1) llm None → approve, de_risk 0(baseline)
    n0 = ConsensusNode(llm=None)
    r0 = n0.review(weights={"us_stock": 0.5, "bond": 0.5}, prior={"us_stock": 0.3, "bond": 0.7})
    assert r0["approve"] and r0["de_risk"] == 0.0
    print("1) llm None → approve de_risk 0(baseline) OK")

    # 2) down-only de-risk 적용
    w = {"us_stock": 0.6, "bond": 0.4}
    prior = {"us_stock": 0.3, "bond": 0.7}
    out = apply_consensus_derisk(w, prior, 0.5)
    assert abs(sum(out.values()) - 1.0) < 1e-9 and out["us_stock"] < w["us_stock"]
    print(f"2) down-only de-risk OK: us_stock {w['us_stock']}→{out['us_stock']:.3f} (prior 후퇴)")

    # 3) de_risk=0 → 무변경 / de_risk=1 → prior
    assert apply_consensus_derisk(w, prior, 0.0) == w
    full = apply_consensus_derisk(w, prior, 1.0)
    assert abs(full["us_stock"] - 0.3) < 1e-9
    print("3) de_risk 0=무변경 / 1=prior 완전후퇴 OK")

    # 4) fake LLM clip(증폭 시도 차단)
    class _LLM:
        def complete(self, system, user, json_mode=True):
            return json.dumps({"approve": False, "de_risk": 1.5, "reason": "over-concentrated"})
    n = ConsensusNode(llm=_LLM())
    r = n.review(weights=w, prior=prior, regime_now="Stagflation")
    assert r["de_risk"] == 1.0 and not r["approve"]   # 1.5 → clip 1.0(down-only 봉인)
    print(f"4) LLM de_risk clip OK: 1.5→{r['de_risk']} (증폭 불가)")

    print("consensus_node self-test PASS (down-only de-risk · clip · abstain · baseline)")
