"""stock/contracts.py — 종목(stock) 트랙 공통 타입·계약 (SSOT).

이 모듈은 valuation / value_trigger / factor_attribution 가 공유하는
**데이터 계약**을 한곳에 모은다. 외부 의존성 없음(표준 라이브러리만) — 어떤 환경에서도
import 가능해야 risk_gate·AssetTrack·백테스트가 동일 타입으로 소비한다.

설계 근거(IMPLEMENTATION_PROMPT.md):
- §5.7-A: 펀더멘털 PIT = (회계기간, filing timestamp, as-reported) **3-튜플**.
  pykrx/FDR 은 restated(재작성) → 누수. 백테스트는 announcement_date<=as_of 만.
- §1 / §3: 주식 트랙은 AssetTrack 구현체. 신호는 risk_gate 가 소비.
- G3 / §5.9-B: factor 귀속 enum (MACRO_REGIME_WRONG / SECTOR_THEME_WRONG /
  VALUE_TRAP / EXECUTION_SLIPPAGE) + 저신뢰 = unattributed.
- §5.10-A: 상품유형 정책(Tier1 영구금지 / Tier2 default-off / 코어 허용).

미해결 가정:
- AssetTrack ABC 의 정확한 시그니처는 core/asset_track.py(미작성)에 있다. 여기서는
  종목 트랙이 산출하는 Decision 의 *형태*만 고정한다. core 가 생기면 그쪽 ABC 를 import.
- 통화(KRW/USD)는 Fundamentals.currency 로 표기만 하고 환산은 상위(FX, H26)가 담당.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional


# ---------------------------------------------------------------------------
# 1. PIT 펀더멘털 3-튜플 (§5.7-A) — announcement-date point-in-time 계약
# ---------------------------------------------------------------------------

class FilingSource(enum.Enum):
    """as-reported 펀더멘털의 출처. PIT 신뢰 등급이 다르다."""
    DART_XBRL = "dart_xbrl"        # 한국: rcept_no 단위 원본 접수일 as-reported (PIT-clean)
    EDGAR_XBRL = "edgar_xbrl"      # 미국: accession 단위 PIT 선별 (PIT-clean)
    RESTATED = "restated"          # pykrx/FDR 등 재작성 값 — ⛔ 백테스트 금지 (누수)
    ESTIMATE = "estimate"          # 컨센서스 추정 (forward) — 별도 취급


@dataclass(frozen=True)
class Fundamentals:
    """announcement-date PIT 펀더멘털 입력 (§5.7-A 3-튜플 계약).

    핵심 3-튜플:
      - fiscal_period: 회계기간 (예: "2023Q4", "2023FY")
      - filing_timestamp: 공시/파일링 시각 (dissemination, PIT 마스킹 기준)
      - source: as-reported 출처 (RESTATED 면 백테스트에서 거부)

    `as_reported=True` 이고 source∈{DART_XBRL, EDGAR_XBRL} 여야 PIT-clean.
    값(매출/이익/FCF 등)은 *그 시점에 발표된 그대로*(현재 재작성값 금지).
    """
    ticker: str
    fiscal_period: str
    filing_timestamp: datetime
    source: FilingSource
    currency: str = "KRW"
    as_reported: bool = True

    # --- 손익/현금흐름 (DCF·멀티플 입력) ---
    revenue: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    ebit: Optional[float] = None
    ebitda: Optional[float] = None
    free_cash_flow: Optional[float] = None
    depreciation_amortization: Optional[float] = None
    capital_expenditure: Optional[float] = None
    interest_expense: Optional[float] = None

    # --- 재무상태 (WACC·멀티플 입력) ---
    total_debt: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    shareholders_equity: Optional[float] = None
    book_value: Optional[float] = None
    working_capital: Optional[float] = None
    outstanding_shares: Optional[float] = None

    # --- 성장/효율 (추정·캡) ---
    earnings_growth: Optional[float] = None
    revenue_growth: Optional[float] = None
    book_value_growth: Optional[float] = None
    return_on_invested_capital: Optional[float] = None
    beta: Optional[float] = None

    def is_pit_clean(self) -> bool:
        """백테스트 매수 유니버스에 쓸 수 있는 PIT-clean 데이터인가.

        §5.7-A: as-reported + DART/EDGAR XBRL 출처만 누수 없음. RESTATED 는 거부.
        """
        return self.as_reported and self.source in (
            FilingSource.DART_XBRL,
            FilingSource.EDGAR_XBRL,
        )

    def visible_at(self, as_of: datetime) -> bool:
        """as_of 시점에 *그때 알 수 있었던* 데이터인가 (announcement_date<=as_of)."""
        return self.filing_timestamp <= as_of


@dataclass(frozen=True)
class MarketQuote:
    """가격 스냅샷 (수정주가, H16 기업행위 반영 가정)."""
    ticker: str
    as_of: datetime
    price: float
    market_cap: Optional[float] = None
    # 가격 변동률 (가치 트리거 1차 게이트 입력) — 윈도우는 호출자가 채움
    price_change_pct: Optional[float] = None
    price_change_window_days: Optional[int] = None


# ---------------------------------------------------------------------------
# 2. Valuation 산출물 — 내재가치 밴드
# ---------------------------------------------------------------------------

@dataclass
class ValuationResult:
    """valuation.py 출력. 단일 점추정이 아니라 *밴드*(bear/base/bull)를 제공.

    intrinsic_value = base 시나리오 확률가중 기대값 (시가총액 단위, 통화=currency).
    valuation_gap = (intrinsic - market_cap) / market_cap. >0 이면 저평가(쌈).
    """
    ticker: str
    as_of: datetime
    currency: str
    intrinsic_value: float                 # 확률가중 기대 내재가치(시총)
    market_cap: float
    valuation_gap: float                   # (intrinsic - mcap)/mcap
    bear_value: float
    base_value: float
    bull_value: float
    wacc: float
    method_values: dict = field(default_factory=dict)   # {method: {value, weight, gap}}
    pit_clean: bool = True
    fundamentals_period: str = ""          # 추적용 (어느 회계기간 기반인지)
    notes: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# 3. Value Trigger 산출물 — 2단 게이트 (§3 / Phase 3)
# ---------------------------------------------------------------------------

class TriggerStage(enum.Enum):
    GATE1_QWEN = "gate1_qwen"          # 1차 저비용 필터 (가격변동 AND 가치 갭)
    GATE2_HEAVY = "gate2_heavy"        # 2차 heavy agent (value-trap 판정)


class ValueVerdict(enum.Enum):
    """2단 게이트 최종 판정."""
    OPPORTUNITY = "opportunity"        # 싸진 기회 → risk_gate 로 후보 전달
    VALUE_TRAP = "value_trap"          # thesis 붕괴 → 매수 금지
    PRICE_ONLY = "price_only"          # 가격만 빠짐(가치 그대로) → 관망/약후보
    REJECT = "reject"                  # 1차 게이트 미통과
    ABSTAIN = "abstain"                # 백테스트 lookahead 경계 (H22) → 판단 보류


@dataclass
class ValueTriggerResult:
    """value_trigger.py 출력. risk_gate 가 소비하는 후보 신호."""
    ticker: str
    as_of: datetime
    verdict: ValueVerdict
    passed_gate1: bool
    stage_reached: TriggerStage
    direction: str                     # "buy" / "hold" / "none"  (G2: 하향만 오버라이드)
    confidence: float                  # 0.0~1.0
    valuation_gap: float
    price_change_pct: Optional[float]
    reasoning: str = ""
    # 메타라벨링 억제 계수 (§5.8-H (a) value-trap): 0~1, 2차 모델 함정확률 기반 사이징
    metalabel_size_factor: float = 1.0
    suppressed: bool = False           # downgrade-ratchet suppress 플래그 (G2)


# ---------------------------------------------------------------------------
# 4. Factor Attribution 산출물 (G3 / §5.9-B)
# ---------------------------------------------------------------------------

class FailureReason(enum.Enum):
    """factor 귀속 enum (G3 / §5.9-B). 분해와 1:1 일치.

    β지배 = MACRO_REGIME_WRONG / 섹터지배 = SECTOR_THEME_WRONG /
    idio지배(value 가설) = VALUE_TRAP / 잔차 = EXECUTION_SLIPPAGE.
    """
    MACRO_REGIME_WRONG = "MACRO_REGIME_WRONG"
    SECTOR_THEME_WRONG = "SECTOR_THEME_WRONG"
    VALUE_TRAP = "VALUE_TRAP"
    EXECUTION_SLIPPAGE = "EXECUTION_SLIPPAGE"
    UNATTRIBUTED = "UNATTRIBUTED"       # 저신뢰(노이즈 β·소표본) → 억지 라벨 금지


@dataclass
class AttributionResult:
    """factor_attribution.py 출력. trade_reviews 확장 컬럼 + JSONB 로 저장.

    §5.9-B: enum 과 분해 일치. 저신뢰=unattributed. LLM 은 lesson 텍스트만.
    """
    trade_id: str
    ticker: str
    failure_reason: FailureReason
    attribution: dict                  # {market_beta, sector, idiosyncratic, residual} 기여
    confidence: float                  # 0~1, 낮으면 UNATTRIBUTED 로 강등
    holding_return: float
    status: str = "closed"             # "closed" / "open" (G9 mark-to-market 잠정)
    is_provisional: bool = False       # G9 잠정 라벨(청산 시 확정 갱신)
    lesson: str = ""                   # LLM 생성 (라벨 위 텍스트만)


# ---------------------------------------------------------------------------
# 5. 상품유형 정책 (§5.10-A) — admission 게이트가 참조
# ---------------------------------------------------------------------------

class ProductTier(enum.Enum):
    TIER1_FORBIDDEN = "tier1_forbidden"      # 선물·옵션·마진·CFD — 영구 금지(완화 불가)
    TIER2_DEFAULT_OFF = "tier2_default_off"  # 레버리지/인버스 ETF·ETN — default-off
    CORE_ALLOWED = "core_allowed"            # 현물 개별주·일반 ETF·금/원자재/채권 ETF


# ---------------------------------------------------------------------------
# 6. 실행 모드 — 백테스트 vs forward (H22 경계)
# ---------------------------------------------------------------------------

class RunMode(enum.Enum):
    """H22: heavy-agent(2차 게이트) 는 백테스트에서 training-data lookahead 오염.

    BACKTEST 모드에서는 heavy-agent 가 abstain stub 으로 동작 (forward 만 실제 판정).
    """
    BACKTEST = "backtest"
    FORWARD = "forward"      # 모의/실전 — heavy-agent 실제 판정


def utcnow() -> datetime:
    return datetime.utcnow()
