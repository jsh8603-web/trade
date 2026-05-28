"""stock/admission.py — §5.10 적격 유니버스 게이트 (S4 앞단).

coarse + fine + 지역 3단 필터로 부적격 상품을 전부 거절한다.
LLM 이 유니버스를 확장하는 경로는 존재하지 않는다 — 유니버스=config 화이트리스트.

coarse (상품 Tier):
  TIER1_FORBIDDEN: 선물·옵션·마진·CFD → 영구 금지
  TIER2_DEFAULT_OFF: 레버리지/인버스 ETF·ETN → 기본 off (명시 허용 목록 없으면 거절)
  CORE_ALLOWED: 현물 개별주·일반 ETF → 허용

fine (KRX 상태, FDR/pykrx PIT 스냅샷):
  관리종목·투자경고·투자위험·거래정지·상장폐지우려·한정감사의견 → 거절

지역:
  US/KR 개별주만 허용 (PIT 펀더멘털 확보국)

설계 근거: IMPLEMENTATION_PROMPT.md §5.10-A/E · implementation-keys §8 정정14.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from stock.contracts import ProductTier

logger = logging.getLogger("stock.admission")


# ── 거절 사유 ─────────────────────────────────────────────────────────

class AdmissionRejectionReason(str, Enum):
    TIER1_FORBIDDEN      = "tier1_forbidden"       # 선물·옵션·마진·CFD
    TIER2_DEFAULT_OFF    = "tier2_default_off"      # 레버리지/인버스 ETF·ETN
    UNSUPPORTED_REGION   = "unsupported_region"    # 비US/KR 개별주
    KRX_WATCHLIST        = "krx_watchlist"         # 관리종목
    KRX_INVESTMENT_WARN  = "krx_investment_warn"   # 투자경고
    KRX_INVESTMENT_RISK  = "krx_investment_risk"   # 투자위험
    KRX_TRADING_HALT     = "krx_trading_halt"      # 거래정지
    KRX_DELISTING_RISK   = "krx_delisting_risk"    # 상장폐지우려
    KRX_QUALIFIED_AUDIT  = "krx_qualified_audit"   # 한정감사의견
    LLM_EXPANSION        = "llm_expansion"         # LLM 유니버스 확장 시도 차단


# ── 결과 ─────────────────────────────────────────────────────────────

@dataclass
class AdmissionResult:
    """admit=True 이면 S4 진입 허용, False 이면 거절+사유."""
    ticker: str
    admit: bool
    reason: Optional[AdmissionRejectionReason] = None
    detail: str = ""

    def __bool__(self) -> bool:
        return self.admit


# ── KRX fine 상태 스냅샷 ─────────────────────────────────────────────

@dataclass
class KrxStatusSnapshot:
    """FDR/pykrx 일별 PIT 스냅샷으로 채우는 KRX 상태 정보.

    is_watchlist=True → 관리종목
    is_invest_warn=True → 투자경고
    is_invest_risk=True → 투자위험
    is_halt=True → 거래정지
    is_delisting_risk=True → 상장폐지우려
    is_qualified_audit=True → 한정감사의견 (정정공시)
    """
    is_watchlist: bool = False
    is_invest_warn: bool = False
    is_invest_risk: bool = False
    is_halt: bool = False
    is_delisting_risk: bool = False
    is_qualified_audit: bool = False


# ── 허용 지역 ─────────────────────────────────────────────────────────

ALLOWED_REGIONS: frozenset[str] = frozenset({"US", "KR"})

# TIER2 명시 허용 목록 (관리자가 config 로 등록, 기본 비어있음)
TIER2_ALLOWLIST: frozenset[str] = frozenset()


# ── 게이트 함수 ───────────────────────────────────────────────────────

def check_admission(
    ticker: str,
    tier: ProductTier,
    region: str,
    krx_status: Optional[KrxStatusSnapshot] = None,
    tier2_allowlist: Optional[frozenset[str]] = None,
    requested_by_llm: bool = False,
) -> AdmissionResult:
    """§5.10 적격 유니버스 게이트 — 단일 종목 판정.

    Args:
        ticker: 종목 코드 (예: "005930", "AAPL")
        tier: ProductTier (contracts.py)
        region: "KR" | "US" | 기타
        krx_status: KRX 일별 상태 스냅샷 (KR 종목만 해당)
        tier2_allowlist: TIER2 명시 허용 목록 (None=기본=빈셋)
        requested_by_llm: LLM 이 유니버스 확장을 요청했는지 여부 → 즉시 차단

    Returns:
        AdmissionResult(admit=True/False, reason, detail)
    """
    t2_allow = tier2_allowlist if tier2_allowlist is not None else TIER2_ALLOWLIST

    # ① LLM 유니버스 확장 시도 차단
    if requested_by_llm:
        logger.warning("admission: LLM 유니버스 확장 시도 차단 — ticker=%s", ticker)
        return AdmissionResult(
            ticker=ticker, admit=False,
            reason=AdmissionRejectionReason.LLM_EXPANSION,
            detail="유니버스는 config 화이트리스트만. LLM 결정 불가.",
        )

    # ② coarse: 상품 Tier
    if tier == ProductTier.TIER1_FORBIDDEN:
        return AdmissionResult(
            ticker=ticker, admit=False,
            reason=AdmissionRejectionReason.TIER1_FORBIDDEN,
            detail="선물·옵션·마진·CFD — 영구 금지",
        )

    if tier == ProductTier.TIER2_DEFAULT_OFF:
        if ticker not in t2_allow:
            return AdmissionResult(
                ticker=ticker, admit=False,
                reason=AdmissionRejectionReason.TIER2_DEFAULT_OFF,
                detail="레버리지/인버스 ETF·ETN — 명시 허용 목록 없음",
            )

    # ③ 지역: US/KR 개별주만
    if region.upper() not in ALLOWED_REGIONS:
        return AdmissionResult(
            ticker=ticker, admit=False,
            reason=AdmissionRejectionReason.UNSUPPORTED_REGION,
            detail=f"지역 {region} — US/KR 개별주만 허용",
        )

    # ④ fine: KRX 상태 (KR 종목만)
    if region.upper() == "KR" and krx_status is not None:
        if krx_status.is_watchlist:
            return AdmissionResult(
                ticker=ticker, admit=False,
                reason=AdmissionRejectionReason.KRX_WATCHLIST,
                detail="KRX 관리종목",
            )
        if krx_status.is_invest_warn:
            return AdmissionResult(
                ticker=ticker, admit=False,
                reason=AdmissionRejectionReason.KRX_INVESTMENT_WARN,
                detail="KRX 투자경고",
            )
        if krx_status.is_invest_risk:
            return AdmissionResult(
                ticker=ticker, admit=False,
                reason=AdmissionRejectionReason.KRX_INVESTMENT_RISK,
                detail="KRX 투자위험",
            )
        if krx_status.is_halt:
            return AdmissionResult(
                ticker=ticker, admit=False,
                reason=AdmissionRejectionReason.KRX_TRADING_HALT,
                detail="KRX 거래정지",
            )
        if krx_status.is_delisting_risk:
            return AdmissionResult(
                ticker=ticker, admit=False,
                reason=AdmissionRejectionReason.KRX_DELISTING_RISK,
                detail="KRX 상장폐지우려",
            )
        if krx_status.is_qualified_audit:
            return AdmissionResult(
                ticker=ticker, admit=False,
                reason=AdmissionRejectionReason.KRX_QUALIFIED_AUDIT,
                detail="한정감사의견(정정공시)",
            )

    # 통과
    return AdmissionResult(ticker=ticker, admit=True, detail="적격")
