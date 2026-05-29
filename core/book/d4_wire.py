"""core/book/d4_wire.py — PIT substrate → D4Book populate wire (R8).

R8: d4_book 를 **실데이터로 채우는** seam. d4_book(S12) 본체는 완비(append-only PIT +
to_context). 본 모듈은 PIT substrate(vintage·패널)에서 D4Book 항목을 생성하되 **knowable_from
을 보존**해 백테스트 시 미래 지식 누수를 막는다(수기 fixture → 실 substrate 전환).

★PIT 전파 핵심: MacroPeriod.knowable_from = 그 국면을 규정한 vintage 의 vintage_knowable_from,
IndustryCharCard.knowable_from = 그 패널 row 의 knowable_from. 그래야 to_context(as_of) 가
"그 시점에 알 수 있던" 국면·특성만 노출(d4_book PIT 게이트와 정합).

⛔ 라이브 LLM 루프 주입(run_agents 경로)은 N-INT 통합 브리지(go-live) 영역 — 본 wire 는
substrate→book 데이터 seam 까지(테스트 가능). 라이브 macro 실데이터(FRED/ECOS)=go-live 게이트.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Union

from core.book.d4_book import D4Book, IndustryCharCard, MacroPeriod
from core.data.vintage import VintageStore

AsOfLike = Union[str, date, datetime]


def _d(x: AsOfLike) -> date:
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    return datetime.fromisoformat(str(x)).date()


def period_from_vintage(
    book: D4Book,
    vstore: VintageStore,
    series_id: str,
    period_label: str,
    *,
    period_id: str,
    label: str,
    start: AsOfLike,
    end: Optional[AsOfLike],
    regime_id: int,
    narrative: str = "",
) -> Optional[MacroPeriod]:
    """vintage 의 한 series×period 관측을 MacroPeriod 로 wire. knowable_from = vintage 공표 시점.

    그 국면을 규정한 거시지표가 실제로 **언제 알려졌는지**(vintage_knowable_from)를 국면의
    knowable_from 으로 전파 → to_context 가 PIT 노출. 미공표 series 면 None(국면 미생성).
    """
    # 그 period 의 최초 vintage 공표 시점 = 국면 인지 가능 시점
    cands = [o for o in vstore._candidates(series_id, period_label, None)]
    if not cands:
        return None
    kf = min(o.vintage_knowable_from for o in cands)
    final_val = max(cands, key=lambda o: (o.vintage_knowable_from, o.sys_time)).value
    p = MacroPeriod(
        period_id=period_id, label=label, start=_d(start),
        end=_d(end) if end is not None else None, regime_id=regime_id,
        reference_indicators={series_id: final_val}, narrative=narrative,
        knowable_from=kf,
    )
    book.add_period(p)
    return p


def card_from_panel_row(
    book: D4Book,
    *,
    sector: str,
    period_label: str,
    archetype: str,
    multiple_pattern: str,
    characteristic: str,
    knowable_from: AsOfLike,
    evidence: Optional[dict] = None,
    value_trap_note: str = "",
) -> IndustryCharCard:
    """패널 근거(실데이터)로 IndustryCharCard 생성. knowable_from = 패널 row knowable_from 전파."""
    c = IndustryCharCard(
        sector=sector, period_label=period_label, archetype=archetype,
        multiple_pattern=multiple_pattern, characteristic=characteristic,
        evidence=evidence or {}, value_trap_note=value_trap_note,
        knowable_from=_d(knowable_from),
    )
    book.add_industry_card(c)
    return c


if __name__ == "__main__":
    book = D4Book()
    vs = VintageStore()
    # 거시 vintage: '고금리 긴축' 국면을 규정한 CPI 2022, 속보 2022-08-10
    vs.add("CPI_YOY", "2022", 8.5, "2022-08-10")
    vs.add("CPI_YOY", "2022", 8.3, "2022-09-13")   # 개정

    # 1) vintage → MacroPeriod wire (knowable_from = vintage 공표 시점 전파)
    p = period_from_vintage(book, vs, "CPI_YOY", "2022", period_id="MP_2022_tighten",
                            label="2022 고금리 긴축", start="2022-01-01", end="2023-06-30",
                            regime_id=1, narrative="CPI 급등→연준 급속 긴축")
    assert p is not None and p.knowable_from == date(2022, 8, 10), p.knowable_from
    print(f"1) vintage→MacroPeriod: knowable_from={p.knowable_from} (CPI 속보 전파) OK")

    # 2) ★PIT 전파: 공표(08-10) 前 as_of 엔 국면 미가시
    assert book.periods_as_of("2022-07-01") == [], "공표 前 국면 미가시"
    assert len(book.periods_as_of("2022-09-01")) == 1, "공표 後 가시"
    print("2) PIT 전파: CPI 공표(08-10) 前 국면 미가시/後 가시 OK")

    # 3) 패널 근거 → IndustryCharCard wire (knowable_from 전파)
    card_from_panel_row(book, sector="semiconductor", period_label="2022 긴축",
                        archetype="cyclical", multiple_pattern="긴축기 EV/EBITDA 압축",
                        characteristic="금리↑ 할인율↑ → 멀티플 디레이팅",
                        knowable_from="2022-08-10", evidence={"ev_ebitda_median": 8.2, "source": "KRX"},
                        value_trap_note="피크 EPS 착시(정점 멀티플 낮음)")
    ctx = book.to_context("semiconductor", "2022-09-01", regime_id=1)
    assert "고금리 긴축" in ctx and "EV/EBITDA" in ctx, ctx
    print("3) 패널→IndustryCharCard wire + to_context(PIT) 소비 OK")

    # 4) ★to_context PIT: 공표 前 as_of 엔 빈 context
    ctx_early = book.to_context("semiconductor", "2022-07-01")
    assert "데이터 없음" in ctx_early, ctx_early
    print("4) to_context PIT: 공표 前 = 학습 데이터 없음 OK")

    print(f"5) book counts(periods, cards) = {book.counts}")
    print("d4_wire (substrate→D4Book PIT 전파 wire) self-test PASS")
