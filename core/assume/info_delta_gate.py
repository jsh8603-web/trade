"""core/assume/info_delta_gate.py — S5 정보델타 발권 트리거 게이트 (Q2 정정 설계).

대형 LLM 가설 발권을 '언제' 부를지 = 시계(clock) batch 도 순수 델타도 아닌 **결합**:
  ★rate-cap(시계 상한) AND 델타 게이트(슬롯 내 새 정보 없으면 skip)  (plan §3 S5 Q2 정정, 2026-06-06)

  - **델타만**(순수)의 함정: 새 리포트는 임베딩 거리가 늘 미세하게 멀어 게이트를 계속 통과 →
    대형 LLM 발권이 daily batch 보다 **오히려 폭증**(델타=상한 없음). → 시계 rate-cap 으로 상한.
  - **batch만**의 함정: 유령회전(phantom turnover) + FDR 예산(LORD++ α-spending) 매일 소진. → 델타로 무의미 발권 필터.
  결합: rate-cap=폭증 방지 상한 / 델타=무의미 발권 필터. daily/weekly batch 는 '폐기' 아니라 상한 역할로 유지.

판정 신호(LLM 추론 무관 = 순수 임베딩 거리 + 수치 파싱):
  ① novelty   = retrieval-context 임베딩 cosine 거리(코퍼스 최근접 대비 신규성)
  ② numeric_revision = 수치 리비전(ΔTP·등급전이·컨센서스 surprise) 크기
  ③ rate_cap  = 시계 슬롯(일/주)별 발권 상한 카운터

★additive(INV-11): 임베딩 벡터는 호출자(VaultVoice BGE) 주입, 본 모듈은 거리·카운터 순수 함수.
  호출처 0(go-live 시 대형 LLM 발권 트리거로 소비). 외부 의존 0(numpy만).
⛔ go-live 미접촉: fire=True 여도 본 모듈은 '부를 자격' 판정만, 실제 LLM 호출은 downstream(사람 게이트).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

import numpy as np


def cosine_novelty(emb_new: Sequence[float], corpus_embs: Optional[Sequence[Sequence[float]]]) -> float:
    """신규 임베딩의 코퍼스 대비 novelty = 1 − max_i cos(emb_new, corpus_i). [0,2], 보통 [0,1].

    코퍼스 비면(첫 정보) novelty=1.0(최대 신규). 정규화는 내부 처리(0-norm 방어).
    """
    v = np.asarray(emb_new, dtype=float).reshape(-1)
    nv = np.linalg.norm(v)
    if nv < 1e-12:
        return 0.0
    v = v / nv
    if corpus_embs is None:
        return 1.0
    C = np.asarray(corpus_embs, dtype=float)
    if C.ndim == 1:
        C = C.reshape(1, -1)
    if C.shape[0] == 0:
        return 1.0
    norms = np.linalg.norm(C, axis=1)
    ok = norms > 1e-12
    if not ok.any():
        return 1.0
    sims = (C[ok] / norms[ok].reshape(-1, 1)) @ v
    return float(1.0 - np.max(sims))


@dataclass
class RateCapState:
    """시계 슬롯별 발권 상한 카운터(폭증 방지 상한). slot_fn(tick)→슬롯 키, 슬롯당 cap_per_slot 회."""
    cap_per_slot: int = 3
    slot_fn: Callable[[float], object] = lambda tick: int(tick) // 1   # 기본 1tick=1슬롯
    _counts: dict = field(default_factory=dict)

    def remaining(self, tick: float) -> int:
        return max(0, self.cap_per_slot - self._counts.get(self.slot_fn(tick), 0))

    def consume(self, tick: float) -> bool:
        """슬롯 여유 있으면 1 차감 후 True, 소진이면 False(차감 안 함)."""
        key = self.slot_fn(tick)
        used = self._counts.get(key, 0)
        if used >= self.cap_per_slot:
            return False
        self._counts[key] = used + 1
        return True


@dataclass
class DeltaDecision:
    fire: bool
    reason: str
    novelty: Optional[float] = None
    numeric_revision: float = 0.0
    rate_remaining: Optional[int] = None


def delta_gate(
    emb_new: Optional[Sequence[float]] = None,
    corpus_embs: Optional[Sequence[Sequence[float]]] = None,
    *,
    novelty_min: float = 0.15,
    numeric_revision: float = 0.0,
    numeric_revision_min: float = 0.0,
    rate_cap: Optional[RateCapState] = None,
    tick: float = 0.0,
    consume_on_fire: bool = True,
) -> DeltaDecision:
    """rate-cap(시계 상한) AND 델타(novelty OR 수치 리비전) 결합 게이트.

    판정 순서:
      1. rate-cap 소진(슬롯 상한 도달) → skip(폭증 방지 상한, 델타 무관)
      2. 델타 없음(novelty<min AND |수치리비전|≤min) → skip(무의미 발권 필터)
      3. else → FIRE(novelty 임계 초과 OR 수치 리비전) + rate-cap 1 차감
    emb_new=None → novelty 판정 생략(수치 리비전만으로 판단).
    """
    remaining = rate_cap.remaining(tick) if rate_cap is not None else None
    if rate_cap is not None and remaining <= 0:
        return DeltaDecision(fire=False, reason="rate-cap 슬롯 상한 도달(폭증 방지)",
                             novelty=None, numeric_revision=numeric_revision, rate_remaining=0)

    nov = cosine_novelty(emb_new, corpus_embs) if emb_new is not None else None
    nov_pass = (nov is not None) and (nov >= novelty_min)
    rev_pass = abs(numeric_revision) > numeric_revision_min

    if not nov_pass and not rev_pass:
        return DeltaDecision(fire=False, reason="델타 없음(novelty<임계 AND 수치 리비전 무) → 무의미 skip",
                             novelty=nov, numeric_revision=numeric_revision, rate_remaining=remaining)

    if rate_cap is not None and consume_on_fire:
        if not rate_cap.consume(tick):
            return DeltaDecision(fire=False, reason="rate-cap 동시 소진(race) → skip",
                                 novelty=nov, numeric_revision=numeric_revision, rate_remaining=0)
        remaining = rate_cap.remaining(tick)

    trg = []
    if nov_pass:
        trg.append(f"novelty={nov:.3f}≥{novelty_min}")
    if rev_pass:
        trg.append(f"수치리비전={numeric_revision:.3f}")
    return DeltaDecision(fire=True, reason="발권 트리거: " + " / ".join(trg),
                         novelty=nov, numeric_revision=numeric_revision, rate_remaining=remaining)


if __name__ == "__main__":
    rng = np.random.RandomState(1)
    dim = 32
    corpus = [rng.randn(dim) for _ in range(5)]

    # 1) 신규 정보(코퍼스와 직교) + rate 여유 → fire
    novel = rng.randn(dim)
    d1 = delta_gate(novel, corpus, novelty_min=0.15)
    assert d1.fire, d1
    print(f"1) 신규 정보 → FIRE (novelty={d1.novelty:.3f}) OK")

    # 2) 중복 정보(코퍼스 한 항목 근접, 리비전 무) → skip
    dup = corpus[0] + rng.randn(dim) * 1e-3
    d2 = delta_gate(dup, corpus, novelty_min=0.15)
    assert not d2.fire and "무의미" in d2.reason, d2
    print(f"2) 중복 정보 → SKIP (novelty={d2.novelty:.3f}) OK")

    # 3) novelty 낮아도 수치 리비전 크면 → fire (ΔTP·등급전이)
    d3 = delta_gate(dup, corpus, novelty_min=0.15, numeric_revision=-0.25, numeric_revision_min=0.05)
    assert d3.fire and "수치리비전" in d3.reason, d3
    print(f"3) 수치 리비전(ΔTP) → FIRE (novelty 낮아도) OK")

    # 4) rate-cap 소진 → skip (폭증 방지 상한)
    rc = RateCapState(cap_per_slot=2, slot_fn=lambda t: int(t) // 10)
    fires = [delta_gate(rng.randn(dim), corpus, rate_cap=rc, tick=3).fire for _ in range(4)]
    assert fires == [True, True, False, False], fires
    print(f"4) rate-cap(슬롯당 2) → {fires} 3번째부터 SKIP (폭증 방지) OK")

    # 5) 다음 슬롯 → 카운터 리셋(새 상한)
    assert delta_gate(rng.randn(dim), corpus, rate_cap=rc, tick=15).fire
    print(f"5) 다음 시계 슬롯(tick=15) → 카운터 리셋 FIRE OK")

    # 6) 코퍼스 빈(첫 정보) → novelty=1.0 fire
    d6 = delta_gate(novel, [], novelty_min=0.15)
    assert d6.fire and d6.novelty == 1.0
    print(f"6) 빈 코퍼스(첫 정보) → novelty=1.0 FIRE OK")

    # 7) emb 없이 수치 리비전만 → fire / 둘 다 없으면 skip
    assert delta_gate(None, numeric_revision=0.3, numeric_revision_min=0.05).fire
    assert not delta_gate(None, numeric_revision=0.0).fire
    print(f"7) 임베딩 없이 수치 리비전 단독 판정 OK")

    print("S5 info_delta_gate self-test PASS "
          "(novelty·수치리비전 델타 AND rate-cap 상한 결합 · 폭증방지 · 슬롯리셋 · 무의미 필터)")
