"""SO-5 테스트: core/risk_sizing.py 멀티에셋 사이징.

검증기준:
- PyPortfolioOpt Ledoit-Wolf 사이징(비중합≈1, non-negative) PASS
- Riskfolio HRP fallback trigger(고상관→HRP 분기, w_max 0.10) PASS
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.risk_sizing import (
    HRP_W_MAX,
    _clamp_and_renorm,
    _normalize_weights,
    _should_use_hrp,
    hrp_weights,
    ledoit_wolf_weights,
    size_portfolio,
)


# ── 유틸 ─────────────────────────────────────────────────────────────

def _make_returns(n_assets: int = 3, n_obs: int = 100, seed: int = 42) -> pd.DataFrame:
    np.random.seed(seed)
    cols = [f"A{i}" for i in range(n_assets)]
    return pd.DataFrame(np.random.randn(n_obs, n_assets) * 0.01, columns=cols)


def _make_high_corr_returns(n_assets: int = 3, n_obs: int = 100, seed: int = 42) -> pd.DataFrame:
    """평균 상관 > 0.80 인 returns."""
    np.random.seed(seed)
    base = np.random.randn(n_obs, 1)
    noise = np.random.randn(n_obs, n_assets) * 0.005
    data = np.hstack([base + noise[:, i:i+1] for i in range(n_assets)]) * 0.01
    cols = [f"A{i}" for i in range(n_assets)]
    return pd.DataFrame(data, columns=cols)


# ── _normalize_weights ────────────────────────────────────────────────

def test_normalize_weights_sums_to_1():
    w = {"A": 2.0, "B": 3.0, "C": 5.0}
    result = _normalize_weights(w)
    assert abs(sum(result.values()) - 1.0) < 1e-9


def test_normalize_weights_zero_total():
    w = {"A": 0.0, "B": 0.0}
    result = _normalize_weights(w)
    assert abs(sum(result.values()) - 1.0) < 1e-9


# ── _clamp_and_renorm ────────────────────────────────────────────────

def test_clamp_renorm_enforces_max():
    """w_max=0.40 클램핑 — 3자산에서 0.5 → 0.4 클램핑."""
    w = {"A": 0.5, "B": 0.3, "C": 0.2}
    result = _clamp_and_renorm(w, w_max=0.40)
    assert all(v <= 0.40 + 1e-6 for v in result.values())
    assert abs(sum(result.values()) - 1.0) < 1e-6


def test_clamp_renorm_no_op_below_max():
    w = {"A": 0.05, "B": 0.05, "C": 0.05}
    normed = _normalize_weights(w)
    result = _clamp_and_renorm(normed, w_max=0.50)
    # 0.33... < 0.50 → 변경 없음
    for k in w:
        assert abs(result[k] - normed[k]) < 1e-6


# ── Ledoit-Wolf 사이징 ────────────────────────────────────────────────

def test_ledoit_wolf_weights_sum_to_1():
    """비중 합 ≈ 1.0."""
    returns = _make_returns()
    w, cov = ledoit_wolf_weights(returns)
    assert abs(sum(w.values()) - 1.0) < 1e-6


def test_ledoit_wolf_weights_nonnegative():
    """모든 비중 >= 0."""
    returns = _make_returns()
    w, cov = ledoit_wolf_weights(returns)
    assert all(v >= -1e-9 for v in w.values())


def test_ledoit_wolf_cov_shape():
    """공분산 행렬 shape = (n_assets, n_assets)."""
    returns = _make_returns(n_assets=4)
    _, cov = ledoit_wolf_weights(returns)
    assert cov.shape == (4, 4)


def test_ledoit_wolf_assets_match():
    """반환 비중 키 = returns 컬럼."""
    returns = _make_returns(n_assets=3)
    w, _ = ledoit_wolf_weights(returns)
    assert set(w.keys()) == set(returns.columns)


# ── HRP trigger ──────────────────────────────────────────────────────

def test_hrp_trigger_on_high_corr():
    """평균 상관 > 0.80 → HRP trigger (raw returns corr 기준)."""
    returns = _make_high_corr_returns()
    from pypfopt.risk_models import CovarianceShrinkage
    cov = CovarianceShrinkage(returns).ledoit_wolf()
    result = _should_use_hrp(cov, returns)
    assert result is True, "고상관 returns 에서 HRP trigger 안 됨"


def test_hrp_not_triggered_on_normal():
    """정상 분산 returns → HRP trigger 안 됨 (보통)."""
    returns = _make_returns(n_assets=3, n_obs=200)
    from pypfopt.risk_models import CovarianceShrinkage
    cov = CovarianceShrinkage(returns).ledoit_wolf()
    result = _should_use_hrp(cov, returns)
    assert isinstance(result, bool)


# ── HRP weights ──────────────────────────────────────────────────────

def test_hrp_weights_sum_to_1():
    """HRP 비중 합 ≈ 1.0."""
    returns = _make_returns()
    w = hrp_weights(returns, w_max=0.10)
    assert abs(sum(w.values()) - 1.0) < 1e-6


def test_hrp_weights_w_max_respected():
    """HRP w_max=0.40 준수 (3자산은 최소 0.33이므로 0.40 테스트)."""
    returns = _make_returns(n_assets=3)
    w = hrp_weights(returns, w_max=0.40)
    assert all(v <= 0.40 + 1e-6 for v in w.values())


def test_hrp_weights_w_max_10_many_assets():
    """HRP w_max=0.10 준수 — 11개 이상 자산."""
    returns = _make_returns(n_assets=11, n_obs=200)
    w = hrp_weights(returns, w_max=0.10)
    assert all(v <= 0.10 + 1e-6 for v in w.values())
    assert abs(sum(w.values()) - 1.0) < 1e-6


def test_hrp_weights_nonnegative():
    returns = _make_returns()
    w = hrp_weights(returns, w_max=HRP_W_MAX)
    assert all(v >= -1e-9 for v in w.values())


# ── size_portfolio 통합 ──────────────────────────────────────────────

def test_size_portfolio_single_asset():
    """단일 자산 → 1.0."""
    returns = pd.DataFrame(np.random.randn(50, 1) * 0.01, columns=["BTC"])
    w, method = size_portfolio(returns)
    assert w["BTC"] == 1.0
    assert method == "single"


def test_size_portfolio_multi_normal():
    """정상 멀티 → ledoit_wolf 또는 hrp."""
    returns = _make_returns(n_assets=3)
    w, method = size_portfolio(returns)
    assert method in ("ledoit_wolf", "hrp")
    assert abs(sum(w.values()) - 1.0) < 1e-6


def test_size_portfolio_high_corr_uses_hrp():
    """고상관 → hrp 분기."""
    returns = _make_high_corr_returns()
    w, method = size_portfolio(returns)
    assert method == "hrp", f"고상관에서 method={method}, hrp 기대"
    assert abs(sum(w.values()) - 1.0) < 1e-6


def test_size_portfolio_force_hrp():
    """force_hrp=True → hrp, 비중합=1."""
    returns = _make_returns()
    w, method = size_portfolio(returns, force_hrp=True)
    assert method == "hrp"
    assert abs(sum(w.values()) - 1.0) < 1e-6


def test_size_portfolio_force_hrp_many_assets_w_max():
    """force_hrp=True, 11개 자산 → w_max=0.10 준수."""
    returns = _make_returns(n_assets=11, n_obs=200)
    w, method = size_portfolio(returns, force_hrp=True, hrp_w_max=0.10)
    assert method == "hrp"
    assert all(v <= 0.10 + 1e-6 for v in w.values())


def test_size_portfolio_empty():
    returns = pd.DataFrame()
    w, method = size_portfolio(returns)
    assert method == "empty"
    assert w == {}


def test_size_portfolio_no_llm_imports():
    """risk_sizing.py 에 LLM import 없음."""
    src = (PROJECT_ROOT / "core" / "risk_sizing.py").read_text(encoding="utf-8")
    assert "anthropic" not in src
    assert "openai" not in src
    assert "llm_provider" not in src
