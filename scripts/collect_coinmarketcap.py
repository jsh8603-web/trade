#!/usr/bin/env python3
"""
CoinMarketCap 기본 데이터 수집 (Basic 플랜 제한 적용)
수집 항목: BTC 글로벌 마켓 도미넌스, FGI(Fear & Greed Index), 전체 시가총액, BTC 24h 변동 등

사용법: python3 scripts/collect_coinmarketcap.py
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

CMC_API_KEY = os.getenv("CMC_API_KEY")

def fetch_cmc_data():
    if not CMC_API_KEY:
        return {"error": "CMC_API_KEY is not set in .env", "status": "disabled"}

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': CMC_API_KEY,      
    }

    try:
        # 1. 글로벌 시총 및 비트코인 도미넌스
        global_url = 'https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest'
        g_resp = requests.get(global_url, headers=headers, timeout=15)
        g_data = {}
        if g_resp.status_code == 200:
            try:
                g_data = g_resp.json().get('data', {}) or {}
            except (ValueError, json.JSONDecodeError):
                g_data = {}

        # 2. 비트코인 24시간 거래량 변동 및 시총
        btc_url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
        b_resp = requests.get(btc_url, headers=headers, params={'symbol': 'BTC'}, timeout=15)
        b_data = {}
        if b_resp.status_code == 200:
            try:
                b_json = b_resp.json()
                raw_data = b_json.get('data', {}) if isinstance(b_json, dict) else {}
                if isinstance(raw_data, dict):
                    b_data = raw_data.get('BTC', {}) or raw_data.get('1', {}) or {}
            except (ValueError, json.JSONDecodeError):
                b_data = {}
        
        # 3. 종합
        result = {
            "source": "coinmarketcap",
            "btc_dominance": g_data.get("btc_dominance"),
            "eth_dominance": g_data.get("eth_dominance"),
            "total_market_cap": g_data.get("quote", {}).get("USD", {}).get("total_market_cap") if g_data else None,
            "btc_volume_change_24h": b_data.get("quote", {}).get("USD", {}).get("volume_change_24h") if b_data else None,
            "status": "success"
        }
        return result
    except Exception as e:
        return {"error": str(e), "status": "failed"}

if __name__ == "__main__":
    print(json.dumps(fetch_cmc_data(), ensure_ascii=False, indent=2))
