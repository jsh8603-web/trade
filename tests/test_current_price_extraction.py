"""
run_agents.py 의 current_price 추출 + 경고 로그 블록(v1.32.1) 유닛 테스트.

대상 로직 (scripts/run_agents.py 라인 943-946):
    _cp_raw = market_data.get("current_price") or market_data.get("ticker", {}).get("trade_price")
    _current_price = int(_cp_raw) if _cp_raw else None
    if _current_price is None:
        log(f"[경고] current_price 누락 — market_data keys={list(market_data.keys())[:10]}")

run_agents.py는 스크립트라서 함수로 분리되어 있지 않으므로,
동일한 로직을 _extract_current_price 헬퍼에 복사하여 검증한다.
(복사 방식 — 원본 파일 변경 없음)
"""

from unittest.mock import MagicMock


def _extract_current_price(market_data, log):
    """run_agents.py 라인 943-946 로직의 복사본."""
    _cp_raw = market_data.get("current_price") or market_data.get("ticker", {}).get("trade_price")
    _current_price = int(_cp_raw) if _cp_raw else None
    if _current_price is None:
        log(f"[경고] current_price 누락 — market_data keys={list(market_data.keys())[:10]}")
    return _current_price


def test_extract_from_top_level():
    """market_data에 current_price가 있으면 그 값을 반환한다."""
    log = MagicMock()
    market_data = {"current_price": 112300000, "ticker": {"trade_price": 999}}
    result = _extract_current_price(market_data, log)
    assert result == 112300000
    log.assert_not_called()


def test_extract_from_ticker_fallback():
    """current_price 없고 ticker.trade_price 있으면 그 값을 반환한다."""
    log = MagicMock()
    market_data = {"ticker": {"trade_price": 98500000}}
    result = _extract_current_price(market_data, log)
    assert result == 98500000
    log.assert_not_called()


def test_both_missing_returns_none():
    """둘 다 없으면 None을 반환한다."""
    log = MagicMock()
    market_data = {"indicators": {"rsi_14": 50}}
    result = _extract_current_price(market_data, log)
    assert result is None
    log.assert_called_once()


def test_float_price_converted_to_int():
    """float 값은 int로 변환된다 (112300000.5 → 112300000)."""
    log = MagicMock()
    market_data = {"current_price": 112300000.5}
    result = _extract_current_price(market_data, log)
    assert result == 112300000
    assert isinstance(result, int)
    log.assert_not_called()


def test_warning_logged_when_none():
    """_current_price가 None일 때 log 호출 메시지에 '경고'가 포함된다."""
    log = MagicMock()
    market_data = {"foo": "bar"}
    result = _extract_current_price(market_data, log)
    assert result is None
    log.assert_called_once()
    logged_message = log.call_args[0][0]
    assert "경고" in logged_message
    assert "current_price" in logged_message


def test_ticker_trade_price_float_converted():
    """ticker.trade_price가 float이어도 int로 변환된다 (보너스 케이스)."""
    log = MagicMock()
    market_data = {"ticker": {"trade_price": 98500000.75}}
    result = _extract_current_price(market_data, log)
    assert result == 98500000
    assert isinstance(result, int)


def test_zero_price_treated_as_missing():
    """current_price=0 이면 falsy → None (현재 로직 동작 문서화)."""
    log = MagicMock()
    market_data = {"current_price": 0, "ticker": {"trade_price": 0}}
    result = _extract_current_price(market_data, log)
    assert result is None
    log.assert_called_once()
