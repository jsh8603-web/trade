"""SO-2 테스트: stock/admission.py §5.10 적격 유니버스 게이트.

검증기준:
- 적격 현물 개별주 → admit PASS
- 레버리지/인버스 ETF → 거절(TIER2) PASS
- 선물/옵션 → 거절(TIER1) PASS
- 비US/KR → 거절(지역) PASS
- 관리종목(FDR 스냅샷) → 거절(fine) PASS
- LLM 유니버스 확장 시도 → 거부 PASS
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stock.admission import (
    AdmissionRejectionReason,
    AdmissionResult,
    KrxStatusSnapshot,
    check_admission,
)
from stock.contracts import ProductTier


# ── 기본 구조 ────────────────────────────────────────────────────────

def test_admission_result_bool_true():
    r = AdmissionResult(ticker="005930", admit=True)
    assert bool(r) is True


def test_admission_result_bool_false():
    r = AdmissionResult(ticker="FUTURE01", admit=False, reason=AdmissionRejectionReason.TIER1_FORBIDDEN)
    assert bool(r) is False


# ── 적격 현물 개별주 → admit ─────────────────────────────────────────

def test_kr_individual_stock_admitted():
    """KR 현물 개별주 → admit=True."""
    result = check_admission("005930", ProductTier.CORE_ALLOWED, "KR")
    assert result.admit is True


def test_us_individual_stock_admitted():
    """US 현물 개별주 → admit=True."""
    result = check_admission("AAPL", ProductTier.CORE_ALLOWED, "US")
    assert result.admit is True


def test_kr_normal_etf_admitted():
    """일반 ETF(CORE_ALLOWED) → admit=True."""
    result = check_admission("069500", ProductTier.CORE_ALLOWED, "KR")
    assert result.admit is True


# ── 레버리지/인버스 ETF → 거절(TIER2) ───────────────────────────────

def test_leverage_etf_rejected():
    """레버리지 ETF(TIER2) → admit=False."""
    result = check_admission("122630", ProductTier.TIER2_DEFAULT_OFF, "KR")
    assert result.admit is False
    assert result.reason == AdmissionRejectionReason.TIER2_DEFAULT_OFF


def test_inverse_etf_rejected():
    """인버스 ETF(TIER2) → admit=False."""
    result = check_admission("SQQQ", ProductTier.TIER2_DEFAULT_OFF, "US")
    assert result.admit is False
    assert result.reason == AdmissionRejectionReason.TIER2_DEFAULT_OFF


def test_tier2_allowlist_override():
    """TIER2 명시 허용 목록에 있으면 admit=True."""
    result = check_admission(
        "122630", ProductTier.TIER2_DEFAULT_OFF, "KR",
        tier2_allowlist=frozenset({"122630"}),
    )
    assert result.admit is True


# ── 선물/옵션/마진/CFD → 거절(TIER1) ────────────────────────────────

def test_futures_rejected():
    """선물(TIER1) → admit=False."""
    result = check_admission("BTC-FUT", ProductTier.TIER1_FORBIDDEN, "KR")
    assert result.admit is False
    assert result.reason == AdmissionRejectionReason.TIER1_FORBIDDEN


def test_options_rejected():
    """옵션(TIER1) → admit=False."""
    result = check_admission("AAPL-OPT", ProductTier.TIER1_FORBIDDEN, "US")
    assert result.admit is False
    assert result.reason == AdmissionRejectionReason.TIER1_FORBIDDEN


def test_tier1_no_allowlist_override():
    """TIER1 은 허용 목록 있어도 항상 거절."""
    result = check_admission(
        "FUTURE01", ProductTier.TIER1_FORBIDDEN, "KR",
        tier2_allowlist=frozenset({"FUTURE01"}),  # 무효
    )
    assert result.admit is False
    assert result.reason == AdmissionRejectionReason.TIER1_FORBIDDEN


# ── 비US/KR → 거절(지역) ─────────────────────────────────────────────

def test_jp_stock_rejected():
    """일본 주식 → admit=False."""
    result = check_admission("7203", ProductTier.CORE_ALLOWED, "JP")
    assert result.admit is False
    assert result.reason == AdmissionRejectionReason.UNSUPPORTED_REGION


def test_cn_stock_rejected():
    """중국 주식 → admit=False."""
    result = check_admission("600519", ProductTier.CORE_ALLOWED, "CN")
    assert result.admit is False
    assert result.reason == AdmissionRejectionReason.UNSUPPORTED_REGION


def test_eu_stock_rejected():
    result = check_admission("ASML", ProductTier.CORE_ALLOWED, "NL")
    assert result.admit is False
    assert result.reason == AdmissionRejectionReason.UNSUPPORTED_REGION


# ── KRX fine: 관리종목 → 거절 ───────────────────────────────────────

def test_krx_watchlist_rejected():
    """관리종목 → admit=False."""
    status = KrxStatusSnapshot(is_watchlist=True)
    result = check_admission("000001", ProductTier.CORE_ALLOWED, "KR", krx_status=status)
    assert result.admit is False
    assert result.reason == AdmissionRejectionReason.KRX_WATCHLIST


def test_krx_invest_warn_rejected():
    """투자경고 → admit=False."""
    status = KrxStatusSnapshot(is_invest_warn=True)
    result = check_admission("000002", ProductTier.CORE_ALLOWED, "KR", krx_status=status)
    assert result.admit is False
    assert result.reason == AdmissionRejectionReason.KRX_INVESTMENT_WARN


def test_krx_halt_rejected():
    """거래정지 → admit=False."""
    status = KrxStatusSnapshot(is_halt=True)
    result = check_admission("000003", ProductTier.CORE_ALLOWED, "KR", krx_status=status)
    assert result.admit is False
    assert result.reason == AdmissionRejectionReason.KRX_TRADING_HALT


def test_krx_delisting_risk_rejected():
    """상장폐지우려 → admit=False."""
    status = KrxStatusSnapshot(is_delisting_risk=True)
    result = check_admission("000004", ProductTier.CORE_ALLOWED, "KR", krx_status=status)
    assert result.admit is False
    assert result.reason == AdmissionRejectionReason.KRX_DELISTING_RISK


def test_krx_qualified_audit_rejected():
    """한정감사의견 → admit=False."""
    status = KrxStatusSnapshot(is_qualified_audit=True)
    result = check_admission("000005", ProductTier.CORE_ALLOWED, "KR", krx_status=status)
    assert result.admit is False
    assert result.reason == AdmissionRejectionReason.KRX_QUALIFIED_AUDIT


def test_krx_clean_status_admitted():
    """KRX 상태 이상 없음 → admit=True."""
    status = KrxStatusSnapshot()  # 모두 False
    result = check_admission("005930", ProductTier.CORE_ALLOWED, "KR", krx_status=status)
    assert result.admit is True


def test_us_stock_no_krx_fine():
    """US 종목은 KRX fine 미적용 — 상태 이상해도 통과."""
    status = KrxStatusSnapshot(is_watchlist=True)
    result = check_admission("AAPL", ProductTier.CORE_ALLOWED, "US", krx_status=status)
    assert result.admit is True  # US는 KRX fine 무시


# ── LLM 유니버스 확장 시도 → 차단 ───────────────────────────────────

def test_llm_expansion_rejected():
    """LLM 이 유니버스 확장 요청 → 차단."""
    result = check_admission(
        "EXOTIC01", ProductTier.CORE_ALLOWED, "KR",
        requested_by_llm=True,
    )
    assert result.admit is False
    assert result.reason == AdmissionRejectionReason.LLM_EXPANSION


def test_llm_expansion_blocked_even_if_valid():
    """LLM 요청이면 정상 종목도 차단 (유니버스=config만)."""
    result = check_admission(
        "005930", ProductTier.CORE_ALLOWED, "KR",
        requested_by_llm=True,
    )
    assert result.admit is False
    assert result.reason == AdmissionRejectionReason.LLM_EXPANSION
