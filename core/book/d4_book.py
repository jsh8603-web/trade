"""core/book/d4_book.py — D4 거시·산업 기간 학습 Book (S12, 사용자 D4 핵심 누락).

사용자 D4 요구: "거시 기간정의(상황 X 가 언제~언제, 참조지표, 서사) + 산업군 특성
(예: 반도체=공정개발 주기따라 산업전반 일시 PER 상승, 기간별 실데이터) → LLM 이 분석에
활용할 지식 Book". findings §2 D4 / R3.

구성:
- MacroPeriod: 거시 국면 1개 정의 (기간·참조지표·서사·regime). ruptures 분절 → 후보 생성.
- IndustryCharCard: 산업 특성 1개 (sector × period × 멀티플 패턴 + 실데이터 근거).
- D4Book: append-only PIT 저장 + LLM context 생성(`to_context`). 무한확장(다산업·다기간).

★ LLM 활용 방식: to_context(sector, as_of) → "그 시점에 알 수 있던" 거시 국면 + 산업 특성
  서사를 텍스트로 조립 → L2 Qwen / value-trap judge 프롬프트에 주입(환각 방어=실데이터 근거 동반).
★ 무한확장 (사용자 메모): 새 산업·새 기간 카드 append → consensus(S9)·promotion_gate(S3)
  로 검증·승격. knowable_from PIT 으로 백테스트 시 미래 지식 누수 차단.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import numpy as np

from core.pit.as_of import resolve_as_of, AsOfLike

try:
    import ruptures as _rpt
    _HAS_RUPTURES = True
except Exception:
    _HAS_RUPTURES = False


@dataclass
class MacroPeriod:
    """거시 국면 1개. 기간·참조지표·서사. regime_id 로 structure model/regime 과 연결."""
    period_id: str
    label: str                          # "2020-21 팬데믹 유동성 장세"
    start: date
    end: Optional[date]
    regime_id: int
    reference_indicators: dict = field(default_factory=dict)  # {지표: 값/방향}
    narrative: str = ""
    knowable_from: date = date(1900, 1, 1)


@dataclass
class IndustryCharCard:
    """산업 특성 1개. sector × period 의 멀티플 패턴 + 실데이터 근거."""
    sector: str
    period_label: str
    archetype: str
    multiple_pattern: str               # "공정전환기 산업전반 EV/EBITDA 일시 확장"
    characteristic: str                 # 서사 설명
    evidence: dict = field(default_factory=dict)   # 실데이터 근거 {metric: value, source}
    value_trap_note: str = ""
    knowable_from: date = date(1900, 1, 1)


def segment_periods(series: np.ndarray, dates: list, *, pen: float = 10.0,
                    min_size: int = 4) -> list[tuple]:
    """ruptures 로 시계열 기간 분절 → [(start_idx, end_idx)]. 없으면 단일 구간 fallback."""
    s = np.asarray(series, float).reshape(-1, 1)
    n = len(s)
    if not _HAS_RUPTURES or n < min_size * 2:
        return [(0, n - 1)]
    try:
        algo = _rpt.Pelt(model="rbf", min_size=min_size).fit(s)
        bkps = algo.predict(pen=pen)            # 끝 인덱스 목록(마지막=n)
        out, prev = [], 0
        for b in bkps:
            out.append((prev, min(b - 1, n - 1)))
            prev = b
        return out
    except Exception:
        return [(0, n - 1)]


class D4Book:
    """거시 기간 + 산업 특성 학습 Book. append-only PIT, LLM context 생성."""

    def __init__(self):
        self._periods: list[MacroPeriod] = []
        self._cards: list[IndustryCharCard] = []

    # --- append-only (무한확장) -----------------------------------------
    def add_period(self, p: MacroPeriod) -> None:
        self._periods.append(p)

    def add_industry_card(self, c: IndustryCharCard) -> None:
        self._cards.append(c)

    # --- PIT 조회 -------------------------------------------------------
    def periods_as_of(self, as_of: AsOfLike) -> list[MacroPeriod]:
        a = resolve_as_of(as_of).date()
        return [p for p in self._periods if p.knowable_from <= a]

    def cards_as_of(self, sector: str, as_of: AsOfLike) -> list[IndustryCharCard]:
        a = resolve_as_of(as_of).date()
        return [c for c in self._cards if c.sector == sector and c.knowable_from <= a]

    # --- LLM context 생성 (지식베이스 활용) -----------------------------
    def to_context(self, sector: str, as_of: AsOfLike, regime_id: Optional[int] = None) -> str:
        """그 시점 알 수 있던 거시 국면 + 산업 특성 → LLM 프롬프트 주입 텍스트(PIT)."""
        a = resolve_as_of(as_of)
        lines = [f"# 학습 Book context (sector={sector}, as_of={a.date()})"]
        periods = self.periods_as_of(as_of)
        if regime_id is not None:
            periods = [p for p in periods if p.regime_id == regime_id]
        if periods:
            lines.append("## 거시 국면")
            for p in periods[-3:]:
                lines.append(f"- {p.label} (regime {p.regime_id}): {p.narrative} "
                             f"[지표: {p.reference_indicators}]")
        cards = self.cards_as_of(sector, as_of)
        if cards:
            lines.append(f"## {sector} 산업 특성")
            for c in cards[-5:]:
                line = f"- [{c.period_label}] {c.multiple_pattern} — {c.characteristic}"
                if c.value_trap_note:
                    line += f" ⚠️밸류트랩: {c.value_trap_note}"
                if c.evidence:
                    line += f" (근거: {c.evidence})"
                lines.append(line)
        if len(lines) == 1:
            lines.append("(해당 시점 학습 데이터 없음)")
        return "\n".join(lines)

    @property
    def counts(self) -> tuple:
        return (len(self._periods), len(self._cards))


if __name__ == "__main__":
    book = D4Book()

    # 1) 거시 기간 등록 (반도체 공정전환 맥락 포함)
    book.add_period(MacroPeriod(
        "p2020", "2020-21 팬데믹 유동성 장세", date(2020, 3, 1), date(2021, 12, 31),
        regime_id=0, reference_indicators={"fed_funds": "0%", "m2_yoy": "+25%"},
        narrative="제로금리+유동성 폭발로 성장주 멀티플 전반 확장",
        knowable_from=date(2021, 1, 1)))
    book.add_period(MacroPeriod(
        "p2022", "2022 긴축 전환", date(2022, 1, 1), None, regime_id=1,
        reference_indicators={"fed_funds": "↑", "yield_curve": "역전"},
        narrative="공격적 금리인상으로 멀티플 디레이팅",
        knowable_from=date(2022, 6, 1)))

    # 2) 산업 특성 카드 (반도체 공정전환기 PER 일시상승 — 사용자 예시)
    book.add_industry_card(IndustryCharCard(
        sector="semiconductor", period_label="2020-21 공정전환기", archetype="cyclical",
        multiple_pattern="공정전환(EUV) capex 사이클로 산업전반 EV/EBITDA 일시 확장",
        characteristic="감가상각 선반영으로 EBITDA 눌려 멀티플 높아 보이나 차세대 capa 선점",
        evidence={"sector_ev_ebitda": 16.0, "vs_hist_median": "+30%", "source": "Damodaran2021"},
        value_trap_note="capex 정점 후 ROIC 하락 시 디레이팅",
        knowable_from=date(2021, 6, 1)))

    # 3) PIT 조회: 2021-03 시점엔 p2022 안 보임
    p_early = book.periods_as_of("2021-03-01")
    assert len(p_early) == 1 and p_early[0].period_id == "p2020", [p.period_id for p in p_early]
    print(f"1-3) PIT 기간조회 2021-03: {[p.period_id for p in p_early]} (p2022 미래 제외)")

    # 4) LLM context 생성 (지식베이스 주입용)
    ctx = book.to_context("semiconductor", "2021-09-01")
    assert "공정전환" in ctx and "팬데믹" in ctx, ctx
    print("4) to_context 생성 OK (거시국면+산업특성 PIT):")
    for ln in ctx.split("\n"):
        print("   " + ln)

    # 5) 미래 지식 누수 차단: 2020-06 엔 산업카드(knowable 2021-06) 미노출
    ctx_early = book.to_context("semiconductor", "2020-06-01")
    assert "공정전환" not in ctx_early, ctx_early
    print(f"5) PIT 누수차단: 2020-06 엔 2021-06 카드 미노출 OK")

    # 6) ruptures 분절 (있으면) / fallback
    series = np.concatenate([np.zeros(8), np.ones(8) * 3, np.zeros(8)])
    segs = segment_periods(series, list(range(24)))
    print(f"6) 기간분절: {len(segs)}구간 (ruptures={_HAS_RUPTURES}) {segs[:3]}")

    print(f"counts(periods,cards)={book.counts}")
    print("S12 d4_book self-test PASS")
