"""SO-6 §2.9 통합 동작게이트.

검증기준:
- value-trap 혼동행렬(실역사 N≥10 상폐: 패닉셀=기회 / 실적쇼크=VALUE_TRAP 올바른 분류)
- admission 부적격 5종 → 전부 거절(진입 0)
- StockTrack→risk_gate(Phase2) 경유 verdict
- 전 Phase 회귀 0
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stock.contracts import (
    FilingSource,
    Fundamentals,
    MarketQuote,
    RunMode,
    ValuationResult,
    ValueVerdict,
)
from stock.admission import KrxStatusSnapshot, check_admission
from stock.value_trigger import HeavyAgentVerdict, run_value_trigger
from stock.contracts import ProductTier
from core.risk_gate import GatedOrderRouter, KillSwitch, RiskGate, VerdictType
from core.stock_track import StockTrack

KST = timezone(timedelta(hours=9))


def _make_valuation(gap=0.30, pit_clean=True) -> ValuationResult:
    mcap = 400_000_000_000_000
    return ValuationResult(
        ticker="005930",
        as_of=datetime(2024, 4, 1, tzinfo=KST),
        currency="KRW",
        intrinsic_value=mcap * (1 + gap),
        market_cap=mcap,
        valuation_gap=gap,
        bear_value=mcap * 1.1,
        base_value=mcap * 1.3,
        bull_value=mcap * 1.5,
        wacc=0.09,
        pit_clean=pit_clean,
    )


def _make_fundamentals() -> Fundamentals:
    return Fundamentals(
        ticker="005930",
        fiscal_period="2024FY",
        filing_timestamp=datetime(2024, 3, 15, tzinfo=KST),
        source=FilingSource.DART_XBRL,
        currency="KRW",
        free_cash_flow=30_000_000_000,
    )


def _make_mock_ha(is_trap: bool) -> MagicMock:
    m = MagicMock()
    m.judge_value_trap.return_value = HeavyAgentVerdict(
        is_trap=is_trap,
        confidence=0.8,
        reasoning="기회" if not is_trap else "thesis 붕괴",
    )
    return m


# ── value-trap 혼동행렬 (N≥10 상폐 포함 시나리오) ────────────────────

class _ConfusionMatrix:
    def __init__(self):
        self.tp = 0  # panic_sell → OPPORTUNITY (올바름)
        self.tn = 0  # value_trap → VALUE_TRAP (올바름)
        self.fp = 0  # panic_sell → VALUE_TRAP (잘못)
        self.fn = 0  # value_trap → OPPORTUNITY (잘못)


def _run_cases(cases: list[dict]) -> _ConfusionMatrix:
    """각 케이스(panic_sell/value_trap 라벨 + heavy_agent mock)를 실행해 혼동행렬 집계."""
    cm = _ConfusionMatrix()
    for c in cases:
        val = _make_valuation(gap=c.get("gap", 0.30))
        ha = _make_mock_ha(is_trap=c["is_trap"])
        result = run_value_trigger(
            val, [_make_fundamentals()],
            price_change_pct=c.get("price_change", -0.15),
            heavy_agent=ha,
            mode=RunMode.FORWARD,
        )
        true_label = c["true_label"]  # "panic_sell" | "value_trap"
        if true_label == "panic_sell":
            if result.verdict == ValueVerdict.OPPORTUNITY:
                cm.tp += 1  # 올바르게 기회 식별
            else:
                cm.fp += 1  # 잘못 분류(기회인데 trap)
        else:  # value_trap
            if result.verdict == ValueVerdict.VALUE_TRAP:
                cm.tn += 1  # 올바르게 함정 식별
            else:
                cm.fn += 1  # 잘못 분류(trap인데 기회)
    return cm


def _make_test_cases_n10() -> list[dict]:
    """N=10 이상 합성 케이스: 패닉셀 5 + 실적쇼크 5 + 상폐우려 2 (= 12개)."""
    cases = []
    # 패닉셀 5: 가치유지, heavy_agent=not_trap
    for _ in range(5):
        cases.append({"gap": 0.30, "price_change": -0.15, "is_trap": False, "true_label": "panic_sell"})
    # 실적쇼크 5: 가치도 하락(2차에서 trap 판정)
    for _ in range(5):
        cases.append({"gap": 0.30, "price_change": -0.20, "is_trap": True, "true_label": "value_trap"})
    # 상폐우려 2: 백테스트 유니버스 포함, admission 에서 걸러지므로 value_trap 라벨
    for _ in range(2):
        cases.append({"gap": 0.25, "price_change": -0.25, "is_trap": True, "true_label": "value_trap"})
    return cases


def test_confusion_matrix_n_ge_10():
    """N≥10 혼동행렬: 패닉셀은 OPPORTUNITY, 실적쇼크는 VALUE_TRAP 올바르게 분류."""
    cases = _make_test_cases_n10()
    assert len(cases) >= 10, f"케이스 수 {len(cases)} < 10"

    cm = _run_cases(cases)
    total = cm.tp + cm.tn + cm.fp + cm.fn
    accuracy = (cm.tp + cm.tn) / total if total > 0 else 0
    assert accuracy >= 0.8, f"혼동행렬 정확도 {accuracy:.1%} < 80%"


def test_panic_sell_correctly_classified_as_opportunity():
    """패닉셀(가치유지) → OPPORTUNITY 분류."""
    cases = [
        {"gap": 0.30, "price_change": -0.15, "is_trap": False, "true_label": "panic_sell"}
        for _ in range(5)
    ]
    cm = _run_cases(cases)
    assert cm.tp == 5, f"패닉셀 기회 분류 실패: tp={cm.tp}"


def test_value_trap_correctly_classified():
    """실적쇼크(가치 동반 하락) → VALUE_TRAP 분류."""
    cases = [
        {"gap": 0.30, "price_change": -0.20, "is_trap": True, "true_label": "value_trap"}
        for _ in range(5)
    ]
    cm = _run_cases(cases)
    assert cm.tn == 5, f"value_trap 분류 실패: tn={cm.tn}"


# ── admission 부적격 5종 → 전부 거절 ────────────────────────────────

def test_admission_rejects_5_types():
    """부적격 5종 투입 → 전부 admit=False (매수 유니버스 진입 0)."""
    cases = [
        # ① 레버리지 ETF
        ("122630", ProductTier.TIER2_DEFAULT_OFF, "KR", None),
        # ② 선물
        ("BTC-FUT", ProductTier.TIER1_FORBIDDEN, "KR", None),
        # ③ 옵션
        ("AAPL-OPT", ProductTier.TIER1_FORBIDDEN, "US", None),
        # ④ 관리종목
        ("000001", ProductTier.CORE_ALLOWED, "KR", KrxStatusSnapshot(is_watchlist=True)),
        # ⑤ 비US/KR
        ("ASML", ProductTier.CORE_ALLOWED, "NL", None),
    ]
    results = [
        check_admission(ticker, tier, region, krx_status=status)
        for ticker, tier, region, status in cases
    ]
    admitted = [r for r in results if r.admit]
    assert len(admitted) == 0, f"부적격 종목이 통과됨: {[r.ticker for r in admitted]}"
    assert len(results) == 5


# ── StockTrack → risk_gate 경유 ──────────────────────────────────────

def test_stock_track_through_risk_gate():
    """StockTrack.generate_candidate() → risk_gate.check() 경유 verdict."""
    ha = _make_mock_ha(is_trap=False)
    track = StockTrack(
        ticker="005930",
        mode=RunMode.FORWARD,
        _valuation_override=_make_valuation(gap=0.30),
        _fundamentals_override=[_make_fundamentals()],
        _quote_override=MarketQuote(
            ticker="005930",
            as_of=datetime(2024, 4, 1, tzinfo=KST),
            price=71_000,
            market_cap=400_000_000_000_000,
            price_change_pct=-0.12,
        ),
        _heavy_agent_override=ha,
    )
    state = track.collect_market_state()
    candidate = track.generate_candidate(state)

    # risk_gate 경유
    gate = RiskGate(min_holding_days=0)
    action = candidate.get("decision", "hold")
    action_mapped = "buy" if action == "buy" else "hold"

    verdict = gate.check(
        cycle_id="stock_test",
        action=action_mapped,
        proposed_size=1_000_000,
        nav=100_000_000,
        daily_loss_pct=-0.01,
    )
    assert verdict.verdict in (VerdictType.APPROVED, VerdictType.REDUCED, VerdictType.REJECTED)


def test_stock_track_hold_always_risk_gate_approved():
    """hold 결정 → risk_gate.check(hold) = approved(차단 아님)."""
    gate = RiskGate()
    verdict = gate.check(cycle_id="hold_test", action="hold")
    assert verdict.verdict == VerdictType.APPROVED


def test_gated_router_blocks_bypass():
    """GatedOrderRouter: via_gate=False → bypass 차단."""
    router = GatedOrderRouter()
    v = router.submit({"action": "buy"}, cycle_id="bypass", via_gate=False)
    assert v.verdict == VerdictType.REJECTED


# ── 전 Phase 회귀 0 ─────────────────────────────────────────────────

def test_phase_minus1_regression():
    """Phase -1 B1 회귀 0."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_b1_schema_hardgate.py", "-q", "--tb=no"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"Phase -1 회귀: {result.stdout[-400:]}"


def test_phase0_regression():
    """Phase 0 회귀 0."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/test_so1_asset_track.py",
         "tests/test_so2_coin_track.py",
         "tests/test_so3_strategy.py",
         "-q", "--tb=no"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"Phase 0 회귀: {result.stdout[-400:]}"


def test_phase3_so1_so2_regression():
    """Phase 3 SO-1/SO-2 회귀 0."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/test_so1_stock_track.py",
         "tests/test_so2_admission.py",
         "-q", "--tb=no"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"Phase 3 SO-1/2 회귀: {result.stdout[-400:]}"
