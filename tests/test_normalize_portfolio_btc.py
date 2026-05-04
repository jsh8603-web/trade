"""run_agents._normalize_portfolio_btc 단위 테스트.

운영에서 매도 결정이 30일 0건이던 근본 원인 — get_portfolio.py의 holdings list
형식과 agents/orchestrator가 기대하는 portfolio["btc"] dict 형식 미스매치.
정규화 헬퍼가 4가지 입력 형태를 모두 올바르게 처리하는지 검증.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

import pytest


@pytest.fixture(scope="module")
def normalize():
    from scripts.run_agents import _normalize_portfolio_btc
    return _normalize_portfolio_btc


class TestNormalizePortfolioBtc:
    """get_portfolio.py 출력의 holdings list → portfolio['btc'] dict 정규화."""

    def test_holdings_list_with_btc(self, normalize):
        """실제 운영 형식 — holdings list에 BTC 포함."""
        portfolio = {
            "krw_balance": 4_655_041,
            "holdings": [
                {
                    "currency": "BTC",
                    "balance": 0.005150,
                    "avg_buy_price": 116_499_951.7,
                    "current_price": 117_197_000,
                    "eval_amount": 603_587.99,
                    "profit_loss_pct": 0.6,
                },
                {"currency": "XRP", "balance": 3.4e-08},
            ],
            "total_eval": 5_258_629,
        }

        result = normalize(portfolio)

        assert result["balance"] == 0.005150
        assert result["avg_buy_price"] == 116_499_951.7
        assert result["eval_amount"] == 603_587.99
        # 별칭 키 — agents/orchestrator 호환
        assert result["profit_pct"] == 0.6
        assert result["evaluation"] == 603_587.99

    def test_holdings_list_btc_absent(self, normalize):
        """BTC 미보유 — 다른 코인만 있을 때 빈 dict."""
        portfolio = {
            "krw_balance": 5_000_000,
            "holdings": [
                {"currency": "XRP", "balance": 100, "eval_amount": 50_000},
                {"currency": "ETH", "balance": 0.1, "eval_amount": 200_000},
            ],
            "total_eval": 5_250_000,
        }

        result = normalize(portfolio)

        assert result == {}
        assert result.get("balance", 0) == 0  # agent 체크 안전

    def test_empty_holdings(self, normalize):
        """holdings 비어있음 (전부 KRW)."""
        portfolio = {
            "krw_balance": 5_000_000,
            "holdings": [],
            "total_eval": 5_000_000,
        }

        result = normalize(portfolio)

        assert result == {}

    def test_holdings_missing(self, normalize):
        """holdings 키 자체 없음 — 기존 백테스트/테스트 호환."""
        portfolio = {"krw_balance": 1_000_000, "total_eval": 1_000_000}

        result = normalize(portfolio)

        assert result == {}

    def test_legacy_coins_btc_format(self, normalize):
        """레거시 coins.BTC 형식 (백테스트 호환) — holdings 없을 때 폴백."""
        portfolio = {
            "krw_balance": 500_000,
            "coins": {
                "BTC": {
                    "balance": 0.01,
                    "avg_buy_price": 100_000_000,
                    "evaluation": 1_050_000,
                    "profit_pct": 5.0,
                },
            },
            "total_eval": 1_550_000,
        }

        result = normalize(portfolio)

        assert result["balance"] == 0.01
        assert result["evaluation"] == 1_050_000
        assert result["profit_pct"] == 5.0
        # eval_amount 미설정 시 fallback 안 함 (run_agents는 evaluation 키도 fallback)

    def test_legacy_btc_dict(self, normalize):
        """portfolio["btc"]가 이미 dict로 있는 경우."""
        portfolio = {
            "btc": {"balance": 0.02, "eval_amount": 2_000_000, "profit_pct": 10.0},
            "total_eval": 5_000_000,
        }

        result = normalize(portfolio)

        assert result["balance"] == 0.02
        assert result["eval_amount"] == 2_000_000
        assert result["profit_pct"] == 10.0
        assert result["evaluation"] == 2_000_000  # eval_amount → evaluation 별칭

    def test_holdings_takes_precedence_over_legacy(self, normalize):
        """holdings에 BTC 있으면 legacy 키보다 우선."""
        portfolio = {
            "holdings": [{"currency": "BTC", "balance": 0.5, "eval_amount": 1}],
            "btc": {"balance": 999, "eval_amount": 9999},  # 무시되어야 함
        }

        result = normalize(portfolio)

        assert result["balance"] == 0.5  # holdings 우선
        assert result["eval_amount"] == 1

    def test_alias_does_not_overwrite_existing(self, normalize):
        """기존 profit_pct/evaluation이 있으면 별칭 매핑이 덮어쓰지 않음."""
        portfolio = {
            "holdings": [{
                "currency": "BTC",
                "balance": 0.01,
                "eval_amount": 1_000_000,
                "evaluation": 999_999,  # 의도적으로 다름
                "profit_loss_pct": 5.0,
                "profit_pct": 4.0,  # 의도적으로 다름
            }],
        }

        result = normalize(portfolio)

        assert result["evaluation"] == 999_999  # 기존 값 보존
        assert result["profit_pct"] == 4.0  # 기존 값 보존

    def test_returns_copy_not_reference(self, normalize):
        """결과 dict 수정이 원본 holdings에 영향 주지 않음."""
        original_h = {"currency": "BTC", "balance": 0.01, "eval_amount": 1_000}
        portfolio = {"holdings": [original_h]}

        result = normalize(portfolio)
        result["balance"] = 999

        assert original_h["balance"] == 0.01  # 원본 보존
