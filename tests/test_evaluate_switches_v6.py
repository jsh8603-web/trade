#!/usr/bin/env python3
"""evaluate_switches.py null-blocking fix 단위 테스트

외부 API/DB 호출을 모두 mock하여 실행한다.
핵심 검증: price_at_switch가 null인 전환을 neutral로 마킹하여 큐에서 제거하는 로직.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

# 프로젝트 루트를 path에 추가
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from scripts.evaluate_switches import (
    get_current_price,
    evaluate_pending_switches,
    KST,
)


# ═══════════════════════════════════════════════════
# get_current_price 테스트
# ═══════════════════════════════════════════════════

class TestGetCurrentPrice:
    """Upbit 현재가 조회 함수."""

    @patch("scripts.evaluate_switches.requests.get")
    def test_returns_price(self, mock_get):
        mock_get.return_value = MagicMock(
            json=lambda: [{"trade_price": 85_000_000}]
        )
        assert get_current_price() == 85_000_000

    @patch("scripts.evaluate_switches.requests.get")
    def test_returns_zero_on_exception(self, mock_get):
        mock_get.side_effect = Exception("timeout")
        assert get_current_price() == 0

    @patch("scripts.evaluate_switches.requests.get")
    def test_returns_zero_on_empty_response(self, mock_get):
        mock_get.return_value = MagicMock(json=lambda: [])
        # IndexError -> 0
        assert get_current_price() == 0


# ═══════════════════════════════════════════════════
# null price_at_switch 블로킹 수정 테스트
# ═══════════════════════════════════════════════════

class TestNullPriceBlocking:
    """price_at_switch가 null인 레코드 처리."""

    @patch("scripts.evaluate_switches.requests.patch")
    @patch("scripts.evaluate_switches.requests.get")
    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-key",
    })
    def test_null_price_marked_as_neutral(self, mock_get, mock_patch):
        """price_at_switch가 None이면 neutral 마킹 후 스킵."""
        now = datetime.now(KST)
        five_hours_ago = (now - timedelta(hours=5)).isoformat()

        # GET: Supabase 조회 결과 (price_at_switch가 None)
        mock_get.side_effect = [
            MagicMock(
                status_code=200,
                json=lambda: [
                    {
                        "id": "aaaa-bbbb-cccc-dddd",
                        "price_at_switch": None,
                        "created_at": five_hours_ago,
                        "price_after_4h": None,
                    }
                ],
            ),
        ]
        # PATCH: neutral 마킹
        mock_patch.return_value = MagicMock(status_code=204)

        # get_current_price도 mock (null 레코드만 있으므로 실제론 호출됨)
        with patch("scripts.evaluate_switches.get_current_price", return_value=85_000_000):
            evaluate_pending_switches()

        # PATCH가 호출되었는지 확인
        assert mock_patch.called
        patch_call = mock_patch.call_args
        json_body = patch_call.kwargs.get("json") or patch_call[1].get("json")
        assert json_body["outcome"] == "neutral"
        assert "누락" in json_body["outcome_reason"]
        assert json_body["evaluated_at"] is not None

    @patch("scripts.evaluate_switches.requests.patch")
    @patch("scripts.evaluate_switches.requests.get")
    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-key",
    })
    def test_null_price_skips_pnl_calculation(self, mock_get, mock_patch):
        """null price에서 pnl 계산 없이 바로 마킹."""
        now = datetime.now(KST)
        six_hours_ago = (now - timedelta(hours=6)).isoformat()

        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {
                    "id": "null-price-id",
                    "price_at_switch": None,
                    "created_at": six_hours_ago,
                    "price_after_4h": None,
                }
            ],
        )
        mock_patch.return_value = MagicMock(status_code=204)

        with patch("scripts.evaluate_switches.get_current_price", return_value=85_000_000):
            evaluate_pending_switches()

        # PATCH body에 profit 필드가 없어야 함
        json_body = mock_patch.call_args.kwargs.get("json") or mock_patch.call_args[1].get("json")
        assert "profit_after_4h" not in json_body
        assert "profit_after_24h" not in json_body


# ═══════════════════════════════════════════════════
# 정상 평가 흐름 (4h / 24h)
# ═══════════════════════════════════════════════════

class TestNormalEvaluation:
    """price_at_switch가 있는 정상 레코드 평가."""

    @patch("scripts.evaluate_switches.requests.patch")
    @patch("scripts.evaluate_switches.requests.get")
    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-key",
    })
    def test_4h_evaluation(self, mock_get, mock_patch):
        """4시간 경과 + 24시간 미경과 -> price_after_4h만 업데이트."""
        now = datetime.now(KST)
        five_hours_ago = (now - timedelta(hours=5)).isoformat()

        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {
                    "id": "switch-4h",
                    "price_at_switch": 80_000_000,
                    "created_at": five_hours_ago,
                    "price_after_4h": None,
                }
            ],
        )
        mock_patch.return_value = MagicMock(status_code=204)

        with patch("scripts.evaluate_switches.get_current_price", return_value=82_000_000):
            evaluate_pending_switches()

        json_body = mock_patch.call_args.kwargs.get("json") or mock_patch.call_args[1].get("json")
        assert json_body["price_after_4h"] == 82_000_000
        # profit = (82M - 80M) / 80M * 100 = 2.5%
        assert json_body["profit_after_4h"] == pytest.approx(2.5)
        # 24h 평가는 아직 안됨
        assert "outcome" not in json_body

    @patch("scripts.evaluate_switches.requests.patch")
    @patch("scripts.evaluate_switches.requests.get")
    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-key",
    })
    def test_24h_evaluation_good(self, mock_get, mock_patch):
        """24시간 경과 + 수익 1%+ -> outcome=good."""
        now = datetime.now(KST)
        twenty_five_hours_ago = (now - timedelta(hours=25)).isoformat()

        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {
                    "id": "switch-24h-good",
                    "price_at_switch": 80_000_000,
                    "created_at": twenty_five_hours_ago,
                    "price_after_4h": None,  # 4h도 미평가
                }
            ],
        )
        mock_patch.return_value = MagicMock(status_code=204)

        # 82M -> +2.5% (> 1%)
        with patch("scripts.evaluate_switches.get_current_price", return_value=82_000_000):
            evaluate_pending_switches()

        json_body = mock_patch.call_args.kwargs.get("json") or mock_patch.call_args[1].get("json")
        assert json_body["outcome"] == "good"
        assert json_body["profit_after_24h"] == pytest.approx(2.5)
        assert "evaluated_at" in json_body

    @patch("scripts.evaluate_switches.requests.patch")
    @patch("scripts.evaluate_switches.requests.get")
    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-key",
    })
    def test_24h_evaluation_bad(self, mock_get, mock_patch):
        """24시간 경과 + 손실 -1% 이하 -> outcome=bad."""
        now = datetime.now(KST)
        twenty_five_hours_ago = (now - timedelta(hours=25)).isoformat()

        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {
                    "id": "switch-24h-bad",
                    "price_at_switch": 80_000_000,
                    "created_at": twenty_five_hours_ago,
                    "price_after_4h": None,
                }
            ],
        )
        mock_patch.return_value = MagicMock(status_code=204)

        # 78M -> -2.5% (< -1%)
        with patch("scripts.evaluate_switches.get_current_price", return_value=78_000_000):
            evaluate_pending_switches()

        json_body = mock_patch.call_args.kwargs.get("json") or mock_patch.call_args[1].get("json")
        assert json_body["outcome"] == "bad"
        assert json_body["profit_after_24h"] == pytest.approx(-2.5)

    @patch("scripts.evaluate_switches.requests.patch")
    @patch("scripts.evaluate_switches.requests.get")
    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-key",
    })
    def test_24h_evaluation_neutral(self, mock_get, mock_patch):
        """24시간 경과 + 변동 -1%~+1% -> outcome=neutral."""
        now = datetime.now(KST)
        twenty_five_hours_ago = (now - timedelta(hours=25)).isoformat()

        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {
                    "id": "switch-24h-neutral",
                    "price_at_switch": 80_000_000,
                    "created_at": twenty_five_hours_ago,
                    "price_after_4h": 80_100_000,
                }
            ],
        )
        mock_patch.return_value = MagicMock(status_code=204)

        # 80.5M -> +0.625% (neutral range)
        with patch("scripts.evaluate_switches.get_current_price", return_value=80_500_000):
            evaluate_pending_switches()

        json_body = mock_patch.call_args.kwargs.get("json") or mock_patch.call_args[1].get("json")
        assert json_body["outcome"] == "neutral"


# ═══════════════════════════════════════════════════
# 엣지 케이스 테스트
# ═══════════════════════════════════════════════════

class TestEdgeCases:
    """경계 조건과 에러 처리."""

    @patch("scripts.evaluate_switches.requests.get")
    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-key",
    })
    def test_no_pending_switches(self, mock_get):
        """평가할 전환이 없으면 조용히 종료."""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [],
        )
        # 예외 없이 종료
        evaluate_pending_switches()

    @patch.dict(os.environ, {"SUPABASE_URL": "", "SUPABASE_SERVICE_ROLE_KEY": ""})
    def test_missing_env_vars(self):
        """SUPABASE 환경변수 미설정 시 조기 반환."""
        # 예외 없이 종료
        evaluate_pending_switches()

    @patch("scripts.evaluate_switches.requests.get")
    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-key",
    })
    def test_api_error_status(self, mock_get):
        """Supabase 조회 실패 시 조기 반환."""
        mock_get.return_value = MagicMock(status_code=500)
        # 예외 없이 종료
        evaluate_pending_switches()

    @patch("scripts.evaluate_switches.requests.get")
    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-key",
    })
    def test_price_fetch_failure_returns_early(self, mock_get):
        """현재가 조회 실패 시 조기 반환."""
        now = datetime.now(KST)
        five_hours_ago = (now - timedelta(hours=5)).isoformat()

        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {
                    "id": "switch-no-price",
                    "price_at_switch": 80_000_000,
                    "created_at": five_hours_ago,
                    "price_after_4h": None,
                }
            ],
        )

        with patch("scripts.evaluate_switches.get_current_price", return_value=0):
            # current_price == 0 -> 조기 반환
            evaluate_pending_switches()

    @patch("scripts.evaluate_switches.requests.patch")
    @patch("scripts.evaluate_switches.requests.get")
    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-key",
    })
    def test_invalid_created_at_skipped(self, mock_get, mock_patch):
        """created_at 파싱 실패 시 해당 레코드 스킵."""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {
                    "id": "bad-date",
                    "price_at_switch": 80_000_000,
                    "created_at": "invalid-date-string",
                    "price_after_4h": None,
                }
            ],
        )

        with patch("scripts.evaluate_switches.get_current_price", return_value=82_000_000):
            evaluate_pending_switches()

        # PATCH 호출되지 않아야 함 (파싱 실패로 스킵)
        mock_patch.assert_not_called()


# ═══════════════════════════════════════════════════
# 혼합 레코드 테스트
# ═══════════════════════════════════════════════════

class TestMixedRecords:
    """null과 정상 레코드가 섞인 경우."""

    @patch("scripts.evaluate_switches.requests.patch")
    @patch("scripts.evaluate_switches.requests.get")
    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-key",
    })
    def test_mixed_null_and_valid(self, mock_get, mock_patch):
        """null price와 정상 price가 섞인 배치 처리."""
        now = datetime.now(KST)
        five_hours_ago = (now - timedelta(hours=5)).isoformat()

        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {
                    "id": "null-record",
                    "price_at_switch": None,
                    "created_at": five_hours_ago,
                    "price_after_4h": None,
                },
                {
                    "id": "valid-record",
                    "price_at_switch": 80_000_000,
                    "created_at": five_hours_ago,
                    "price_after_4h": None,
                },
            ],
        )
        mock_patch.return_value = MagicMock(status_code=204)

        with patch("scripts.evaluate_switches.get_current_price", return_value=82_000_000):
            evaluate_pending_switches()

        # 2번 PATCH (null 마킹 1회 + 4h 평가 1회)
        assert mock_patch.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
