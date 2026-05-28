"""stock/data/fundamentals_adapter.py — announcement-date PIT 펀더멘털 어댑터 (§5.7-A).

핵심 임무: valuation.py 가 *현재 재작성값이 아닌* "그 시점에 발표된 그대로(as-reported)"
펀더멘털을 받도록 하는 어댑터 경계. pykrx/FDR 정형재무는 restated → 누수이므로,
as-reported 는 DART(rcept_no 단위 XBRL)·EDGAR(accession 단위 XBRL)에서 가져온다.

설계 근거:
- §5.7-A: (회계기간, filing timestamp, as-reported) 3-튜플. 한국=DART(정정공시는 원본
  접수일), 미국=EDGAR XBRL. dissemination lag. 백테스트는 announcement_date<=as_of 만.
- §5.7-B: 생존편향 — 상폐 포함(백테스트 유니버스만).
- §5.7-D: Layer1(기계적) PIT-clean 패리티(>=95%). Layer2(LLM)는 forward 만.

코드화 방식: ai-hedge-fund 의 `get_financial_metrics`/`search_line_items`(현재 데이터
API) 는 PIT 보장이 없다(라이브 스냅샷). 우리는 그 *형태*는 빌리되, **PIT 마스킹 계약**을
어댑터 레벨에서 강제한다 → as_of 보다 늦게 파일링된 레코드는 절대 반환 안 함.

미해결 가정:
- 실제 DART XBRL 파싱(rcept_no→재무제표)·EDGAR companyfacts 파싱은 외부 I/O 라 여기서는
  *프로토콜 인터페이스*(FundamentalsProvider)로 경계를 긋고, 구현체는 별도(network)로 둔다.
  검증 완료(사용자 메모): DART 정형재무는 restated → as-reported 는 rcept_no XBRL 파싱,
  EDGAR 는 accession 단위 PIT 선별.
- 정정공시: DART 는 *원본 접수일*을 filing_timestamp 로 써야 PIT 깨끗(정정본 접수일 X).
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, Sequence, Optional, List

from stock.contracts import Fundamentals, FilingSource, RunMode


class FundamentalsProvider(Protocol):
    """as-reported 펀더멘털 소스의 어댑터 경계 (DART / EDGAR 구현체가 만족).

    구현체는 *원본 파일링 단위*로 레코드를 돌려줘야 한다 (재작성 병합 금지):
      - DART: rcept_no(접수번호) 단위 XBRL. 정정공시는 원본 접수일 보존.
      - EDGAR: accession number 단위. 10-K/10-Q 별 as-reported.
    """

    def fetch_filings(self, ticker: str, limit: int = 8) -> Sequence[Fundamentals]:
        """ticker 의 파일링들을 최신순으로 반환 (각 레코드는 그 시점 as-reported)."""
        ...


class PITFundamentalsAdapter:
    """PIT 마스킹을 강제하는 어댑터. valuation.py 가 직접 쓰는 진입점.

    백테스트 모드: announcement_date(filing_timestamp) <= as_of 인 레코드만 통과시키고,
    RESTATED 소스는 거부한다. forward 모드: 최신 as-reported 허용(라이브는 누수 불가능).
    """

    def __init__(self, provider: FundamentalsProvider, mode: RunMode = RunMode.FORWARD):
        self._provider = provider
        self._mode = mode

    def get_pit_fundamentals(
        self,
        ticker: str,
        as_of: datetime,
        limit: int = 8,
    ) -> List[Fundamentals]:
        """as_of 시점에 가시적인 PIT-clean 펀더멘털을 최신순으로 반환.

        반환 [0] = as_of 직전 가장 최근 파일링 (DCF·멀티플 base).
        반환 [1:] = 과거 파일링 (성장률 CAGR·멀티플 밴드 산출용).

        백테스트에서 누수 차단:
          1) filing_timestamp <= as_of (그때 알 수 있던 것만)
          2) source != RESTATED (재작성값 금지, §5.7-A)
        """
        raw = list(self._provider.fetch_filings(ticker, limit=limit * 2))

        visible: List[Fundamentals] = []
        for f in raw:
            if self._mode == RunMode.BACKTEST:
                if not f.visible_at(as_of):
                    continue  # 아직 발표 안 된 미래 데이터 — 누수
                if f.source == FilingSource.RESTATED:
                    continue  # 재작성값 — 누수 (§5.7-A)
            else:
                # forward: 라이브는 미래 데이터 자체가 존재 불가. 단 RESTATED 는
                # 일관성을 위해 forward 에서도 경고만 하고 통과(라이브 갱신은 정상).
                if not f.visible_at(as_of):
                    continue
            visible.append(f)

        # 최신순 정렬 (filing_timestamp 내림차순) 후 limit
        visible.sort(key=lambda x: x.filing_timestamp, reverse=True)
        return visible[:limit]

    def pit_clean_ratio(self, fundamentals: Sequence[Fundamentals]) -> float:
        """Layer1 PIT-clean 패리티 측정 (§5.7-D, >=95% 목표).

        반환 = PIT-clean 레코드 비율. 백테스트 게이트에서 이 비율로 신뢰도 판정.
        """
        if not fundamentals:
            return 0.0
        clean = sum(1 for f in fundamentals if f.is_pit_clean())
        return clean / len(fundamentals)


# ---------------------------------------------------------------------------
# 참조용 stub provider — 테스트/백테스트 fixture (합성 데이터, §5.8-H 저작권 가드 정합)
# ---------------------------------------------------------------------------

class InMemoryFundamentalsProvider:
    """테스트/백테스트용 in-memory provider. 실제 DART/EDGAR 구현 전 경계 검증용.

    합성 데이터만 담는다 (저작권 리포트 전문 fixture 금지 — quant.md git push 위생).
    """

    def __init__(self, records: dict[str, List[Fundamentals]]):
        self._records = records

    def fetch_filings(self, ticker: str, limit: int = 8) -> Sequence[Fundamentals]:
        recs = self._records.get(ticker, [])
        recs = sorted(recs, key=lambda x: x.filing_timestamp, reverse=True)
        return recs[:limit]
