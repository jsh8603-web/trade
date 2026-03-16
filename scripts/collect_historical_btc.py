#!/usr/bin/env python3
"""
BTC 7년 역사 데이터 수집기 (2019-01 ~ 2026-02)

Binance 글로벌 OHLCV API로 장기 데이터를 수집하고,
Fear & Greed Index 역사 데이터를 병합한다.

수집 데이터:
  - BTC/USDT 4시간봉 (Binance) → ~15,330개 캔들
  - BTC/USDT 일봉 (Binance) → ~2,600개 캔들
  - Fear & Greed Index 일별 (Alternative.me) → ~2,600일
  - 주요 이벤트 레이블 (COVID, 반감기, 전쟁, FTX 등)

출력: data/historical/btc_4h_2019_2026.json
      data/historical/btc_1d_2019_2026.json
      data/historical/fgi_2019_2026.json
      data/historical/btc_events_labeled.json

사용법:
  python scripts/collect_historical_btc.py              # 전체 수집
  python scripts/collect_historical_btc.py --interval 4h  # 4시간봉만
  python scripts/collect_historical_btc.py --interval 1d  # 일봉만
  python scripts/collect_historical_btc.py --fgi-only     # FGI만
"""

from __future__ import annotations

import io
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Windows cp949 방지
if sys.stdout and sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requests

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "data" / "historical"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Binance API ──────────────────────────────────────────
BINANCE_API = "https://api.binance.com/api/v3"
BINANCE_KLINE_LIMIT = 1000  # 1회 최대


def fetch_binance_klines(
    symbol: str = "BTCUSDT",
    interval: str = "4h",
    start_date: str = "2019-01-01",
    end_date: str = "2026-03-01",
) -> list[dict]:
    """Binance에서 장기 OHLCV 데이터를 페이지네이션으로 수집한다.

    Args:
        symbol: 거래쌍 (BTCUSDT)
        interval: 1h, 4h, 1d
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)

    Returns:
        [{"timestamp", "open", "high", "low", "close", "volume", "volume_usdt"}, ...]
    """
    start_ms = int(datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)
    end_ms = int(datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)

    all_candles = []
    current_start = start_ms
    session = requests.Session()

    print(f"  Binance {symbol} {interval} 수집 중 ({start_date} ~ {end_date})...")

    while current_start < end_ms:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": current_start,
            "endTime": end_ms,
            "limit": BINANCE_KLINE_LIMIT,
        }

        try:
            resp = session.get(f"{BINANCE_API}/klines", params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  [ERROR] Binance API: {e}", file=sys.stderr)
            time.sleep(2)
            continue

        if not data:
            break

        for k in data:
            ts_ms = k[0]
            candle = {
                "timestamp": datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
                "volume_usdt": float(k[7]),
            }
            all_candles.append(candle)

        # 다음 페이지 시작 = 마지막 캔들 + 1ms
        current_start = data[-1][0] + 1

        # 진행률
        pct = min(100, (current_start - start_ms) / (end_ms - start_ms) * 100)
        print(f"    {len(all_candles):,}개 수집 ({pct:.0f}%)", end="\r")
        time.sleep(0.1)  # rate limit

    print(f"\n  완료: {len(all_candles):,}개 캔들")
    return all_candles


def convert_usdt_to_krw_approx(candles: list[dict]) -> list[dict]:
    """USDT 가격을 대략적 KRW로 변환 (훈련용, 정확도 불필요).

    환율: 시기별 대략적 USD/KRW 적용
    """
    for c in candles:
        year = int(c["timestamp"][:4])
        # 시기별 대략적 환율
        if year <= 2019:
            rate = 1150
        elif year == 2020:
            rate = 1180
        elif year == 2021:
            rate = 1150
        elif year == 2022:
            rate = 1300
        elif year == 2023:
            rate = 1300
        elif year == 2024:
            rate = 1350
        else:
            rate = 1400

        c["close_krw"] = round(c["close"] * rate)
        c["open_krw"] = round(c["open"] * rate)
        c["high_krw"] = round(c["high"] * rate)
        c["low_krw"] = round(c["low"] * rate)
        c["volume_krw"] = round(c["volume_usdt"] * rate)
    return candles


# ── Fear & Greed Index ───────────────────────────────────

def fetch_fgi_history(days: int = 2600) -> list[dict]:
    """Alternative.me에서 FGI 역사 데이터를 가져온다.

    Args:
        days: 조회 일수 (최대 ~2600일)

    Returns:
        [{"date": "YYYY-MM-DD", "value": int, "classification": str}, ...]
    """
    print(f"  Fear & Greed Index 역사 데이터 수집 중 (최근 {days}일)...")

    try:
        resp = requests.get(
            f"https://api.alternative.me/fng/?limit={days}&format=json",
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
    except Exception as e:
        print(f"  [ERROR] FGI API: {e}", file=sys.stderr)
        return []

    result = []
    for entry in data:
        ts = int(entry["timestamp"])
        result.append({
            "date": datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d"),
            "value": int(entry["value"]),
            "classification": entry["value_classification"],
        })

    # 시간순 정렬
    result.reverse()
    print(f"  완료: {len(result)}일")
    return result


# ── 주요 이벤트 레이블링 ─────────────────────────────────

MAJOR_EVENTS = [
    # 2019
    {"start": "2019-01-01", "end": "2019-04-01", "label": "crypto_winter_end", "regime": "bear_strong",
     "description": "크립토 윈터 종료기, BTC $3,200 바닥"},
    {"start": "2019-04-02", "end": "2019-06-26", "label": "2019_spring_rally", "regime": "bull_strong",
     "description": "2019 봄 랠리, $3,200→$13,800"},
    {"start": "2019-06-27", "end": "2019-12-31", "label": "2019_correction", "regime": "bear_weak",
     "description": "2019 하반기 조정, $13,800→$7,200"},

    # 2020
    {"start": "2020-01-01", "end": "2020-03-12", "label": "pre_covid", "regime": "sideways",
     "description": "COVID 이전 횡보"},
    {"start": "2020-03-12", "end": "2020-03-16", "label": "covid_crash", "regime": "bear_strong",
     "description": "COVID 블랙 스완, BTC -50% ($9,100→$3,800)"},
    {"start": "2020-03-17", "end": "2020-05-11", "label": "covid_recovery", "regime": "bull_weak",
     "description": "COVID 반등, $3,800→$9,500"},
    {"start": "2020-05-11", "end": "2020-05-12", "label": "halving_2020", "regime": "volatile",
     "description": "3차 반감기 (6.25 BTC)"},
    {"start": "2020-05-13", "end": "2020-10-07", "label": "post_halving_consolidation", "regime": "sideways",
     "description": "반감기 후 횡보, $9,000~$12,000"},
    {"start": "2020-10-08", "end": "2020-12-31", "label": "institutional_rally_start", "regime": "bull_strong",
     "description": "기관 매수 시작 (MicroStrategy, PayPal), $10,500→$29,000"},

    # 2021
    {"start": "2021-01-01", "end": "2021-04-14", "label": "2021_bull_run_1", "regime": "bull_strong",
     "description": "1차 불런, $29,000→$64,800 (코인베이스 상장)"},
    {"start": "2021-04-15", "end": "2021-05-19", "label": "china_crackdown", "regime": "bear_strong",
     "description": "중국 채굴 금지 + 테슬라 BTC 결제 중단, -50%"},
    {"start": "2021-05-20", "end": "2021-07-20", "label": "2021_summer_fear", "regime": "bear_weak",
     "description": "FGI 10대, $30,000~$35,000 횡보"},
    {"start": "2021-07-21", "end": "2021-11-10", "label": "2021_bull_run_2", "regime": "bull_strong",
     "description": "2차 불런, $29,000→$69,000 (ATH)"},
    {"start": "2021-11-11", "end": "2021-12-31", "label": "2021_year_end_correction", "regime": "bear_weak",
     "description": "ATH 후 조정, $69,000→$46,000"},

    # 2022
    {"start": "2022-01-01", "end": "2022-05-08", "label": "2022_bear_start", "regime": "bear_weak",
     "description": "약세장 시작, $46,000→$36,000"},
    {"start": "2022-05-09", "end": "2022-05-13", "label": "luna_crash", "regime": "bear_strong",
     "description": "LUNA/UST 폭락, BTC -30%"},
    {"start": "2022-05-14", "end": "2022-06-17", "label": "3ac_celsius_crash", "regime": "bear_strong",
     "description": "3AC/Celsius 파산, BTC $17,500"},
    {"start": "2022-06-18", "end": "2022-11-07", "label": "2022_bear_consolidation", "regime": "sideways",
     "description": "약세장 횡보, $18,000~$25,000"},
    {"start": "2022-11-08", "end": "2022-11-21", "label": "ftx_crash", "regime": "bear_strong",
     "description": "FTX 파산, BTC $15,500 (사이클 바닥)"},
    {"start": "2022-11-22", "end": "2022-12-31", "label": "ftx_aftermath", "regime": "bear_weak",
     "description": "FTX 후폭풍, $16,000~$17,000"},

    # 2023
    {"start": "2023-01-01", "end": "2023-03-12", "label": "2023_recovery_start", "regime": "bull_weak",
     "description": "회복 시작, $16,500→$24,000"},
    {"start": "2023-03-13", "end": "2023-03-19", "label": "svb_crash", "regime": "volatile",
     "description": "SVB 은행 위기, 역설적 BTC 상승"},
    {"start": "2023-03-20", "end": "2023-06-30", "label": "2023_etf_speculation", "regime": "bull_weak",
     "description": "BlackRock ETF 신청, $24,000→$31,000"},
    {"start": "2023-07-01", "end": "2023-10-15", "label": "2023_summer_sideways", "regime": "sideways",
     "description": "ETF 기대감 횡보, $26,000~$30,000"},
    {"start": "2023-10-16", "end": "2023-12-31", "label": "2023_etf_rally", "regime": "bull_strong",
     "description": "ETF 승인 기대 랠리, $27,000→$42,000"},

    # 2024
    {"start": "2024-01-10", "end": "2024-01-11", "label": "spot_etf_approval", "regime": "volatile",
     "description": "BTC 현물 ETF 승인 (BlackRock, Fidelity 등 11개)"},
    {"start": "2024-01-12", "end": "2024-03-14", "label": "etf_inflow_rally", "regime": "bull_strong",
     "description": "ETF 자금 유입 랠리, $42,000→$73,800 (ATH)"},
    {"start": "2024-03-15", "end": "2024-04-19", "label": "pre_halving_correction", "regime": "bear_weak",
     "description": "반감기 전 조정, $73,800→$60,000"},
    {"start": "2024-04-20", "end": "2024-04-20", "label": "halving_2024", "regime": "volatile",
     "description": "4차 반감기 (3.125 BTC)"},
    {"start": "2024-04-21", "end": "2024-08-04", "label": "post_halving_sideways", "regime": "sideways",
     "description": "반감기 후 횡보, $58,000~$72,000"},
    {"start": "2024-08-05", "end": "2024-08-06", "label": "japan_carry_unwind", "regime": "bear_strong",
     "description": "일본 캐리 트레이드 청산 + 글로벌 폭락"},
    {"start": "2024-08-07", "end": "2024-11-05", "label": "election_uncertainty", "regime": "sideways",
     "description": "미국 대선 불확실성, $54,000~$70,000"},
    {"start": "2024-11-06", "end": "2024-12-31", "label": "trump_rally", "regime": "bull_strong",
     "description": "트럼프 당선 랠리, $69,000→$108,000"},

    # 2025
    {"start": "2025-01-01", "end": "2025-02-28", "label": "2025_consolidation", "regime": "sideways",
     "description": "$90,000~$108,000 고점 횡보"},
    {"start": "2025-03-01", "end": "2025-04-06", "label": "trade_war_correction", "regime": "bear_weak",
     "description": "미중 관세전쟁 불확실성 + 연준 금리 동결 우려"},

    # 2025-2026
    {"start": "2025-04-07", "end": "2025-12-31", "label": "tariff_crash_2025", "regime": "bear_strong",
     "description": "트럼프 관세 폭탄 (전세계 상호 관세), 글로벌 증시 폭락, BTC 급락"},
    {"start": "2026-01-01", "end": "2026-02-28", "label": "2026_uncertainty", "regime": "volatile",
     "description": "관세전쟁 장기화, 경기침체 우려, 높은 변동성"},
]


def label_candles_with_events(candles: list[dict]) -> list[dict]:
    """각 캔들에 이벤트 레이블을 추가한다."""
    for c in candles:
        ts = c["timestamp"][:10]  # YYYY-MM-DD
        c["event_label"] = "normal"
        c["event_regime"] = "sideways"
        c["event_description"] = ""

        for event in MAJOR_EVENTS:
            if event["start"] <= ts <= event["end"]:
                c["event_label"] = event["label"]
                c["event_regime"] = event["regime"]
                c["event_description"] = event["description"]
                break

    return candles


def align_fgi_to_candles(candles: list[dict], fgi_data: list[dict]) -> list[dict]:
    """FGI 일별 데이터를 캔들에 매핑 (forward-fill)."""
    fgi_map = {f["date"]: f["value"] for f in fgi_data}

    last_fgi = 50  # 기본값
    for c in candles:
        date = c["timestamp"][:10]
        if date in fgi_map:
            last_fgi = fgi_map[date]
        c["fgi"] = last_fgi

    return candles


# ── 메인 ─────────────────────────────────────────────────

def collect_all(interval: str = "4h", fgi_only: bool = False):
    """전체 수집 파이프라인"""
    if fgi_only:
        fgi = fetch_fgi_history(2600)
        fgi_path = OUTPUT_DIR / "fgi_2019_2026.json"
        with open(fgi_path, "w", encoding="utf-8") as f:
            json.dump(fgi, f, ensure_ascii=False)
        print(f"\n  FGI 저장: {fgi_path} ({len(fgi)}일)")
        return

    # 1. Binance 캔들 수집
    candles = fetch_binance_klines(
        symbol="BTCUSDT",
        interval=interval,
        start_date="2019-01-01",
        end_date="2026-03-01",
    )

    # 2. KRW 근사 변환
    candles = convert_usdt_to_krw_approx(candles)

    # 3. FGI 수집 + 매핑
    fgi = fetch_fgi_history(2600)
    candles = align_fgi_to_candles(candles, fgi)

    # 4. 이벤트 레이블링
    candles = label_candles_with_events(candles)

    # 5. 저장
    candle_path = OUTPUT_DIR / f"btc_{interval}_2019_2026.json"
    with open(candle_path, "w", encoding="utf-8") as f:
        json.dump(candles, f, ensure_ascii=False)

    fgi_path = OUTPUT_DIR / "fgi_2019_2026.json"
    with open(fgi_path, "w", encoding="utf-8") as f:
        json.dump(fgi, f, ensure_ascii=False)

    events_path = OUTPUT_DIR / "btc_events.json"
    with open(events_path, "w", encoding="utf-8") as f:
        json.dump(MAJOR_EVENTS, f, ensure_ascii=False, indent=2)

    print(f"\n=== 수집 완료 ===")
    print(f"  캔들: {candle_path} ({len(candles):,}개)")
    print(f"  FGI:  {fgi_path} ({len(fgi)}일)")
    print(f"  이벤트: {events_path} ({len(MAJOR_EVENTS)}개)")

    # 6. 통계
    if candles:
        prices = [c["close"] for c in candles]
        print(f"\n=== BTC 7년 통계 (USDT) ===")
        print(f"  기간: {candles[0]['timestamp'][:10]} ~ {candles[-1]['timestamp'][:10]}")
        print(f"  최저가: ${min(prices):,.0f}")
        print(f"  최고가: ${max(prices):,.0f}")
        print(f"  시작가: ${prices[0]:,.0f}")
        print(f"  종료가: ${prices[-1]:,.0f}")
        print(f"  총 수익률: {(prices[-1] / prices[0] - 1) * 100:+.1f}%")

    return candles, fgi


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="BTC 7년 역사 데이터 수집")
    parser.add_argument("--interval", default="4h", choices=["1h", "4h", "1d"])
    parser.add_argument("--fgi-only", action="store_true")
    args = parser.parse_args()

    collect_all(interval=args.interval, fgi_only=args.fgi_only)
