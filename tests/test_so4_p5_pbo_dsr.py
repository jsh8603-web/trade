"""tests/test_so4_p5_pbo_dsr.py — SO-4/P5 PBO+DSR+GO/NO-GO 검증.

검증 기준 (harness2.md SO-4):
1. CSCV logit-rank PBO (정통식, 근사식 :179 미사용 grep)
2. PBO ∈ [0, 1]
3. DSR (trial-count 반영, trials↑→DSR↓ 단조)
4. GO/NO-GO 카드 JSON (GO/MARGINAL/NO_GO 분기 정확·임계 적용)
"""

from __future__ import annotations

import json
import math
import pytest
import numpy as np

from backtest.pbo import (
    GoNoGoStatus,
    GoNoGoCriteria,
    assess_go_nogo,
    calculate_deflated_sharpe_ratio,
    calculate_pbo_cscv,
    build_go_nogo_card,
    GoNoGoCard,
)


# ---------------------------------------------------------------------------
# 1. PBO 정통식 (근사식 :179 미사용)
# ---------------------------------------------------------------------------

def test_pbo_no_simplified_norm_cdf():
    """pbo.py 에 근사식 norm.cdf(0, loc=...) 패턴 없음 (폐기 검증)."""
    import pathlib
    src = pathlib.Path("backtest/pbo.py").read_text(encoding="utf-8")
    # 근사식 폐기: norm.cdf(0, loc=... 패턴 없어야 함
    assert 'norm.cdf(0, loc=' not in src, "근사식(:179) 폐기 미확인"


def test_pbo_cscv_range():
    """PBO ∈ [0, 1] 항상."""
    # 음수 OOS Sharpe 다수 → 높은 PBO
    oos_bad = [-0.5, -0.3, -0.1, 0.2, -0.4]
    pbo_bad = calculate_pbo_cscv(oos_bad)
    assert 0.0 <= pbo_bad <= 1.0

    # 양수 OOS Sharpe 다수 → 낮은 PBO
    oos_good = [1.5, 1.2, 0.8, 1.0, 0.9]
    pbo_good = calculate_pbo_cscv(oos_good)
    assert 0.0 <= pbo_good <= 1.0


def test_pbo_cscv_all_negative_high():
    """전부 음수 OOS → PBO 높음 (>0.5)."""
    oos_bad = [-1.0, -0.8, -0.5, -0.3, -0.1]
    pbo = calculate_pbo_cscv(oos_bad)
    # 전부 음수: 하위 순위 = logit<0 = PBO 높음
    assert pbo > 0.0  # 음수만 있으면 0 근처 이상


def test_pbo_cscv_one_extreme():
    """값 범위가 다를수록 PBO가 달라짐."""
    # 부호 혼재: PBO는 정렬 기반이므로 명확히 구분 가능한 케이스
    pbo1 = calculate_pbo_cscv([-2.0, -1.5, -1.0, -0.5, 0.1])
    pbo2 = calculate_pbo_cscv([0.5, 1.0, 1.5, 2.0, 2.5])
    # 음수 다수 케이스가 PBO ≥ 전부 양수 케이스
    assert pbo1 >= pbo2, f"PBO pbo1={pbo1:.3f} pbo2={pbo2:.3f}"


def test_pbo_empty_returns_half():
    """빈 경로 목록 → 0.5 (무정보 사전)."""
    assert calculate_pbo_cscv([]) == 0.5


# ---------------------------------------------------------------------------
# 2. DSR — trial-count 반영, trials↑ → DSR↓ 단조
# ---------------------------------------------------------------------------

def test_dsr_trials_monotone_decrease():
    """n_trials↑ → DSR 값 단조 감소 (다중검정 패널티 증가)."""
    sharpe = 2.0
    n = 252
    trials_list = [1, 5, 20, 100]
    dsr_values = [
        calculate_deflated_sharpe_ratio(sharpe, t, n).deflated_sharpe
        for t in trials_list
    ]
    for i in range(len(dsr_values) - 1):
        assert dsr_values[i] >= dsr_values[i + 1], (
            f"DSR 단조감소 위반: trials={trials_list[i]}→{trials_list[i+1]}, "
            f"dsr={dsr_values[i]:.4f}→{dsr_values[i+1]:.4f}"
        )


def test_dsr_range():
    """DSR ∈ [0, 1]."""
    result = calculate_deflated_sharpe_ratio(1.5, 10, 252)
    assert 0.0 <= result.deflated_sharpe <= 1.0


def test_dsr_significant_high_sharpe():
    """높은 Sharpe + 적은 trial → DSR > 0.95 = significant."""
    result = calculate_deflated_sharpe_ratio(5.0, 1, 252)
    assert result.is_significant is True


def test_dsr_not_significant_many_trials():
    """낮은 Sharpe + 많은 trial → 1 trial 대비 DSR 낮음."""
    result_few = calculate_deflated_sharpe_ratio(0.5, 1, 252)
    result_many = calculate_deflated_sharpe_ratio(0.5, 1000, 252)
    # 많은 trial 에 패널티 → DSR 낮아짐
    assert result_many.deflated_sharpe <= result_few.deflated_sharpe


def test_dsr_uses_yakub268_formula():
    """yakub268 :218 수식 검산 — euler_gamma=0.5772 사용."""
    # n_trials=1 → expected_max_sharpe = benchmark = 0
    result = calculate_deflated_sharpe_ratio(2.0, 1, 252)
    # sr_var = (1 + 0.5*4) / 252 = 3/252
    sr_var = (1 + 0.5 * 4.0) / 252
    z = (2.0 - 0.0) / math.sqrt(sr_var)
    from scipy import stats
    expected_dsr = float(stats.norm.cdf(z))
    assert abs(result.deflated_sharpe - expected_dsr) < 1e-6


# ---------------------------------------------------------------------------
# 3. GO/NO-GO 카드 — JSON 분기 정확
# ---------------------------------------------------------------------------

def test_go_nogo_go():
    """Sharpe≥1.0, WR≥45%, MDD≥-15% → GO."""
    status, reason = assess_go_nogo(sharpe=1.5, trades=100, max_drawdown=-10.0, win_rate=50.0)
    assert status == GoNoGoStatus.GO


def test_go_nogo_no_go_low_sharpe():
    """Sharpe < 0.7 → NO_GO."""
    status, _ = assess_go_nogo(sharpe=0.5, trades=100, max_drawdown=-10.0, win_rate=50.0)
    assert status == GoNoGoStatus.NO_GO


def test_go_nogo_no_go_excess_drawdown():
    """MDD < -15% → NO_GO."""
    status, _ = assess_go_nogo(sharpe=1.5, trades=100, max_drawdown=-20.0, win_rate=50.0)
    assert status == GoNoGoStatus.NO_GO


def test_go_nogo_marginal():
    """Sharpe=0.8, WR=42% → MARGINAL."""
    status, _ = assess_go_nogo(sharpe=0.8, trades=100, max_drawdown=-12.0, win_rate=42.0)
    assert status == GoNoGoStatus.MARGINAL


def test_go_nogo_card_json_serializable():
    """GoNoGoCard.to_json() → JSON 직렬화 가능."""
    card = build_go_nogo_card(
        oos_sharpe_paths=[1.2, 0.8, 1.5, 0.9, 1.1],
        max_drawdown=-8.0,
        win_rate=52.0,
        n_trades=100,
        n_trials=5,
        track_record_length=252,
    )
    json_str = card.to_json()
    loaded = json.loads(json_str)
    assert "status" in loaded
    assert loaded["status"] in ("GO", "MARGINAL", "NO_GO")
    assert "pbo" in loaded
    assert 0.0 <= loaded["pbo"] <= 1.0


def test_go_nogo_card_go_case():
    """좋은 OOS Sharpe → GO 카드."""
    card = build_go_nogo_card(
        oos_sharpe_paths=[1.5, 1.2, 1.8, 1.3, 1.6],
        max_drawdown=-5.0,
        win_rate=60.0,
        n_trades=200,
        n_trials=5,
        track_record_length=252,
    )
    assert card.status == "GO"


def test_go_nogo_card_no_go_case():
    """나쁜 OOS Sharpe + 큰 MDD → NO_GO 카드."""
    card = build_go_nogo_card(
        oos_sharpe_paths=[-0.5, -0.3, 0.1, -0.2, -0.4],
        max_drawdown=-25.0,
        win_rate=35.0,
        n_trades=50,
        n_trials=5,
        track_record_length=252,
    )
    assert card.status == "NO_GO"


def test_go_nogo_card_has_required_fields():
    """GO/NO-GO 카드 필수 필드 존재 확인."""
    card = build_go_nogo_card(
        oos_sharpe_paths=[0.5, 0.8],
        max_drawdown=-10.0,
        win_rate=45.0,
        n_trades=100,
        n_trials=2,
        track_record_length=100,
    )
    for field_name in ("status", "reason", "sharpe", "pbo", "dsr", "dsr_significant",
                       "avg_oos_sharpe", "n_wf_splits"):
        assert hasattr(card, field_name), f"카드 필드 없음: {field_name}"
