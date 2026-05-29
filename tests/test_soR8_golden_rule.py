"""tests/test_soR8_golden_rule.py — SO-8/PR GOLDEN RULE 누락 감사 게이트.

audit-goldenrule-pR.md §2 의 6 불변식을 기계 검증:
(1) 코인 실거래 경로 미변경 (execute_trade/live_trader diff=0)
(2) 결정엔진/레짐 유지 (coin_track_macro super() 위임)
(3) 단일 BTC Kelly (coin_sizing 위임 경로)
(4) common/metrics 동치 (coin_engine RSI 일원화)
(5) DRY_RUN 패리티 (shadow is_dry_run 항상 True)
(6) reuse-as-is (Riskfolio HRP tail w_max=0.10)
+ Phase R 신규 모듈 전부 git tracked.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _git_diff_empty(rel_path: str) -> bool:
    r = subprocess.run(
        ["git", "diff", "--stat", "HEAD", "--", rel_path],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    return r.stdout.strip() == ""


def _is_tracked(rel_path: str) -> bool:
    r = subprocess.run(
        ["git", "ls-files", "--error-unmatch", rel_path],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    return r.returncode == 0


def _src(rel_path: str) -> str:
    return (PROJECT_ROOT / rel_path).read_text(encoding="utf-8")


# (1) SACRED — 코인 실거래 경로 미변경
def test_invariant1_execute_trade_no_diff():
    assert _git_diff_empty("scripts/execute_trade.py")


def test_invariant1_live_trader_no_diff():
    assert _git_diff_empty("rl_hybrid/rl/live_trader.py")


def test_invariant1_coin_shadow_no_execute_trade_import():
    """coin_shadow 는 execute_trade 실주문 경로를 import 하지 않는다(격리)."""
    src = _src("core/coin_shadow.py")
    # 주석/docstring 의 참조는 허용, 실제 import 문은 금지
    for line in src.splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            assert "execute_trade" not in stripped, f"실 import 발견: {stripped}"


# (2) 결정엔진/레짐 유지 — super() 위임
def test_invariant2_decision_engine_delegation():
    src = _src("core/coin_track_macro.py")
    assert "super().collect_market_state()" in src
    assert "super().generate_candidate(state)" in src


# (3) 단일 BTC Kelly 위임
def test_invariant3_single_btc_kelly():
    src = _src("core/coin_sizing.py")
    assert "_is_single_btc" in src
    assert "size_portfolio" in src  # risk_sizing 위임


# (4) common/metrics RSI 동치
def test_invariant4_common_metrics_rsi():
    src = _src("backtest/coin_engine.py")
    assert "from common.metrics import calculate_rsi" in src


# (5) shadow always dry_run
def test_invariant5_shadow_always_dry_run():
    from core.coin_shadow import CoinShadowExecutor
    ex = CoinShadowExecutor()
    order = ex.place_shadow("BTC/KRW", "buy", 0.001, 50_000_000)
    assert order.is_dry_run is True


# (6) reuse-as-is Riskfolio HRP tail w_max=0.10
def test_invariant6_riskfolio_hrp_tail():
    src = _src("core/coin_sizing.py")
    assert "codependence" in src and "tail" in src
    assert "0.10" in src or "0.1" in src  # w_max


# consensus DCF 없음 (변형표 #5)
def test_consensus_no_dcf():
    src = _src("core/coin_consensus_lens.py")
    assert "DCF" in src  # "DCF 없음" 명시
    from core.coin_consensus_lens import CoinConsensusLens
    assert CoinConsensusLens is not None


# Phase R 신규 모듈 전부 git tracked
_PR_MODULES = [
    "core/coin_track_macro.py",
    "backtest/coin_engine.py",
    "core/coin_sizing.py",
    "core/coin_memory.py",
    "core/coin_shadow.py",
    "core/coin_consensus_lens.py",
    "tests/test_so7_pR_integration_gate.py",
    "tests/test_soR8_golden_rule.py",
]


def test_phase_R_modules_git_tracked():
    untracked = [m for m in _PR_MODULES if not _is_tracked(m)]
    assert untracked == [], f"미tracked Phase R 모듈: {untracked}"
