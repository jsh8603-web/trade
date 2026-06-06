"""core/assume/security_news_loop.py — 개별 종목 소식 트리거 카드 발권 오케스트레이터 (S6 골격, shadow).

사용자 요구(jsonl [17]): "개별 종목 뉴스/증권사 리포트에 새 소식 → 카드 생성." 부품(scope param·
info_delta·research_ingest·active_loop)은 다 있으나 이를 묶는 오케스트레이터가 없던 것을 채운다.

흐름: 종목 소식(raw_text, ticker) → research_ingest(scope=ticker, 중복 novelty 필터) → 유니버스 판정
  → [통과분] active_loop 발권 단계(retrieve→claim→pre-mint audit→probationary mint) 재사용, scope=ticker
  → [유니버스 밖] 임시 후보 풀 적재(즉시 발권 X) → promote_candidates 로 다음 스크린/슬롯에서만 승격.

★유니버스 정책 단계적(plan §3 S6, 사용자 확정): ①스크린 통과분 내 한정(in_universe_fn 주입=button stock/
  스크린 결과) ②유니버스 밖 신선 종목=후보 풀→슬롯 승격(발권 폭증·PIT 부하 방지) ③⛔임의 소식 즉시 카드 금지.
★유니버스 실선별(어느 주식)=button stock/ 소유 → in_universe_fn 콜백 주입식(거시 세션은 골격만).
★shadow / dormant(INV-11): 호출처 0(go-live 시 stock/ 가 소비). probationary=자본0. active_loop·
  research_ingest 무수정 재사용. in_universe_fn None → 모두 후보 풀(보수적, 즉시 발권 0).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

from core.assume.active_loop import ActiveAnalystLoop, ProbationaryCard

logger = logging.getLogger(__name__)


@dataclass
class NewsResult:
    """종목 소식 처리 결과."""
    status: str                # minted | pooled | duplicate | abstain | audit_reject
    ticker: str
    card: Optional[ProbationaryCard] = None
    reason: str = ""


@dataclass
class CandidatePool:
    """유니버스 밖 신선 종목 임시 풀 — 다음 스크린/슬롯에서만 승격(즉시 발권 X)."""
    items: list = field(default_factory=list)   # [{ticker, raw_text, release_ts, doc}]

    def add(self, ticker: str, raw_text: str, release_ts: float, doc=None) -> None:
        self.items.append({"ticker": ticker, "raw_text": raw_text,
                           "release_ts": release_ts, "doc": doc})

    def drain_eligible(self, in_universe_fn: Callable, max_slots: int) -> list:
        """현재 유니버스에 진입한 후보를 max_slots 까지 추출(승격 대상). 나머지 풀 유지."""
        promoted, kept = [], []
        for it in self.items:
            if len(promoted) < max_slots and in_universe_fn(it["ticker"]):
                promoted.append(it)
            else:
                kept.append(it)
        self.items = kept
        return promoted


class SecurityNewsCardLoop:
    """종목 소식 → 카드 발권 오케스트레이터. active_loop 발권 단계 재사용, 유니버스 게이트."""

    def __init__(
        self,
        *,
        ingest,                              # research_ingest.ResearchIngestPipeline
        active_loop: ActiveAnalystLoop,      # 발권 단계(retrieve/claim/audit/mint/write_back) 재사용
        in_universe_fn: Optional[Callable[[str], bool]] = None,   # button 스크린 통과분 주입
        candidate_pool: Optional[CandidatePool] = None,
    ):
        self.ingest = ingest
        self.active_loop = active_loop
        self.in_universe_fn = in_universe_fn
        self.pool = candidate_pool or CandidatePool()

    def _mint_for(self, ticker: str, release_ts: float) -> NewsResult:
        """active_loop 발권 단계 재사용(트리거/summon은 뉴스 도착이 대체) → scope=ticker."""
        al = self.active_loop
        reports = al.retrieve_reports(ticker, release_ts)
        claim = al.generate_claim(None, reports, "security_news")   # macro_view 무관, 종목 리포트 기반
        if not claim:
            return NewsResult("abstain", ticker, reason="claim 생성 실패(LLM abstain)")
        audit = al.pre_mint_audit(claim)
        if not audit.passed:
            return NewsResult("audit_reject", ticker, reason=audit.reason)
        card = al.mint_probationary(claim, scope=ticker, domain="equity")
        if card is None:
            return NewsResult("abstain", ticker, reason="mint 실패")
        pc = ProbationaryCard(card=card, thesis=claim.get("statement", ""),
                              counter_thesis=claim.get("counter_thesis", ""), audit=audit)
        al.write_back_card(pc)
        return NewsResult("minted", ticker, card=pc, reason=audit.reason)

    def on_news(
        self,
        ticker: str,
        raw_text: str,
        release_ts: float,
        *,
        source: str = "",
    ) -> NewsResult:
        """종목 소식 1건 처리. ⛔임의 즉시 카드 금지 — 중복 필터 + 유니버스 게이트 통과 시만 발권."""
        # 1) ingest(중복 novelty 필터). embedder 부재 시 abstain(shadow).
        doc = self.ingest.ingest(raw_text, release_ts=release_ts, scope=ticker, source=source)
        if doc is None:
            return NewsResult("duplicate", ticker, reason="중복/abstain(novelty<임계 or embedder 부재)")

        # 2) 유니버스 게이트: 통과분 내면 발권 / 밖이면 후보 풀(즉시 발권 X)
        if self.in_universe_fn is None or not self.in_universe_fn(ticker):
            self.pool.add(ticker, raw_text, release_ts, doc)
            return NewsResult("pooled", ticker, reason="유니버스 밖 → 후보 풀(다음 스크린 슬롯 승격)")

        # 3) 발권(scope=ticker)
        return self._mint_for(ticker, release_ts)

    def on_news_batch(self, items) -> list:
        """뉴스 다건 처리 — [{ticker, raw_text, release_ts, source?}] → [NewsResult].

        collect_news / 증권 리포트 어댑터가 변환한 items 소비. ticker 추출/매핑은 호출자(button)
        책임(거시 세션은 범용 batch). 각 건 on_news 로 중복필터+유니버스 게이트 통과 시만 발권.
        """
        out = []
        for it in items:
            try:
                out.append(self.on_news(
                    it["ticker"], it["raw_text"], it["release_ts"],
                    source=it.get("source", "")))
            except Exception as exc:
                logger.warning("on_news_batch 항목 실패 → skip: %s", exc)
        return out

    def promote_candidates(self, max_slots: int = 3) -> list:
        """스크린 주기 호출 — 후보 풀에서 유니버스 진입분을 max_slots 까지 발권 승격."""
        if self.in_universe_fn is None:
            return []
        eligible = self.pool.drain_eligible(self.in_universe_fn, max_slots)
        out = []
        for it in eligible:
            out.append(self._mint_for(it["ticker"], it["release_ts"]))
        return out


if __name__ == "__main__":
    import json
    import numpy as np
    from core.assume.research_ingest import ResearchIngestPipeline

    class _Emb:
        def __init__(s, seed=0): s.r = np.random.RandomState(seed); s.m = {}
        def dim(s): return 16
        def embed(s, texts):
            o = []
            for t in texts:
                if t not in s.m: s.m[t] = s.r.randn(16).tolist()
                o.append(s.m[t])
            return o

    class _LLM:
        def complete(s, system, user, json_mode=True):
            if "audit" in system.lower():
                return '{"approve": true, "reason": "ok"}'
            return json.dumps({"statement": "HBM 공급부족 수혜 종목 강세", "direction": "long_tilt",
                               "mediator_ref": "regime:USD:Overheat", "outcome_metric": "cs_rank_IC",
                               "falsification_metric": "해당 종목 3M 상대수익 < 0",
                               "counter_thesis": "공급 정상화"})

    def _mk():
        ingest = ResearchIngestPipeline(embedder=_Emb())
        al = ActiveAnalystLoop(llm=_LLM())   # _LLM 은 complete 직접 구현(어댑터 불요)
        return ingest, al

    # 1) 유니버스 내 종목 소식 → 발권(minted)
    ingest, al = _mk()
    loop = SecurityNewsCardLoop(ingest=ingest, active_loop=al, in_universe_fn=lambda t: t == "005930")
    r1 = loop.on_news("005930", "삼성전자 HBM3E 공급부족 목표가 상향", 1000.0, source="broker")
    assert r1.status == "minted" and r1.card.card.scope == "005930" and r1.card.card.domain == "equity"
    assert r1.card.card.bonus_cap == 0.0   # probationary 자본0
    print(f"1) 유니버스 내 종목 소식 → MINTED OK (scope={r1.card.card.scope}, 자본0)")

    # 2) 유니버스 밖 종목 → 후보 풀(즉시 발권 X)
    r2 = loop.on_news("999999", "잡주 급등 루머", 1001.0)
    assert r2.status == "pooled" and len(loop.pool.items) == 1
    print(f"2) 유니버스 밖 → POOLED(즉시 발권 차단) OK")

    # 3) 중복 소식 → skip
    r3 = loop.on_news("005930", "삼성전자 HBM3E 공급부족 목표가 상향", 1002.0)
    assert r3.status == "duplicate"
    print(f"3) 중복 소식 → DUPLICATE skip OK")

    # 4) 후보 풀 승격: 유니버스 확장 후 promote
    loop.in_universe_fn = lambda t: t in ("005930", "999999")   # 999999 유니버스 진입
    promoted = loop.promote_candidates(max_slots=3)
    assert len(promoted) == 1 and promoted[0].ticker == "999999" and promoted[0].status == "minted"
    assert len(loop.pool.items) == 0
    print(f"4) 유니버스 확장 → 후보 풀 승격 발권 OK")

    # 5) in_universe_fn None → 모두 후보 풀(보수적, 즉시 발권 0)
    ingest2, al2 = _mk()
    loop2 = SecurityNewsCardLoop(ingest=ingest2, active_loop=al2, in_universe_fn=None)
    r5 = loop2.on_news("000660", "SK하이닉스 신규 소식", 2000.0)
    assert r5.status == "pooled"
    print(f"5) in_universe_fn None → 보수적 POOLED(즉시 발권 0) OK")

    print("S6 security_news_loop self-test PASS "
          "(종목 소식→ingest 중복필터→유니버스 게이트→발권/후보풀 승격 · 자본0 probationary · 임의 즉시카드 차단)")
