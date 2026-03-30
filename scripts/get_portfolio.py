#!/usr/bin/env python3
"""
Upbit 포트폴리오 조회 스크립트

조회 항목:
  - KRW 잔고
  - 보유 암호화폐 목록, 수량, 평균매수가, 현재가, 평가액, 수익률
  - 전체 포트폴리오 평가

출력: JSON (stdout)
"""

import json
import os
import sys
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
import jwt
import requests

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

UPBIT_API = "https://api.upbit.com/v1"

# ── 커넥션 재사용을 위한 세션 ──────────────────────────
_session: requests.Session | None = None


def _get_session() -> requests.Session:
    """모듈 레벨 requests.Session을 반환한다 (커넥션 풀 재사용).

    테스트에서는 get_portfolio._session = None 으로 리셋 후
    get_portfolio.requests.Session 을 mock하면 된다.
    """
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({"Accept": "application/json"})
    return _session


def make_auth_header() -> dict:
    access_key = os.environ.get("UPBIT_ACCESS_KEY", "")
    secret_key = os.environ.get("UPBIT_SECRET_KEY", "")
    if not access_key or not secret_key:
        raise ValueError("UPBIT_ACCESS_KEY / UPBIT_SECRET_KEY 환경변수가 설정되지 않았습니다")
    payload = {
        "access_key": access_key,
        "nonce": str(uuid.uuid4()),
        "timestamp": int(time.time() * 1000),
    }
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


def main():
    # 잔고 조회
    session = _get_session()
    r = session.get(
        f"{UPBIT_API}/accounts", headers=make_auth_header(), timeout=10
    )
    r.raise_for_status()
    accounts = r.json()

    krw_balance = 0.0
    holdings = []
    markets = []

    for acc in accounts:
        if acc["currency"] == "KRW":
            krw_balance = float(acc["balance"])
            continue
        bal = float(acc["balance"])
        if bal > 0:
            markets.append(f"KRW-{acc['currency']}")
            holdings.append(
                {
                    "currency": acc["currency"],
                    "balance": bal,
                    "avg_buy_price": float(acc["avg_buy_price"]),
                    "current_price": 0,
                    "eval_amount": 0,
                    "profit_loss_pct": 0.0,
                }
            )

    # 보유 종목 현재가 조회 (유효한 마켓만 필터링)
    if markets:
        valid_markets = []
        all_markets_r = session.get(f"{UPBIT_API}/market/all", timeout=10)
        if all_markets_r.ok:
            all_markets_data = all_markets_r.json()
            valid_markets = [m["market"] for m in all_markets_data if m["market"] in markets]
            del all_markets_data  # release memory

        if valid_markets:
            r2 = session.get(
                f"{UPBIT_API}/ticker",
                params={"markets": ",".join(valid_markets)},
                timeout=10,
            )
            if r2.ok:
                for t in r2.json():
                    cur = t["market"].replace("KRW-", "")
                    h = next((h for h in holdings if h["currency"] == cur), None)
                    if h:
                        h["current_price"] = t["trade_price"]
                        h["eval_amount"] = h["balance"] * t["trade_price"]
                        if h["avg_buy_price"] > 0:
                            h["profit_loss_pct"] = round(
                                (t["trade_price"] - h["avg_buy_price"])
                                / h["avg_buy_price"]
                                * 100,
                                2,
                            )

    total_eval = krw_balance + sum(h["eval_amount"] for h in holdings)
    total_invested = sum(h["balance"] * h["avg_buy_price"] for h in holdings)

    snapshot = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        "krw_balance": krw_balance,
        "holdings": holdings,
        "total_eval": total_eval,
        "total_invested": total_invested + krw_balance,
        "total_profit_loss_pct": round(
            (sum(h["eval_amount"] for h in holdings) - total_invested) / max(total_invested, 1) * 100,
            2,
        )
        if total_invested > 0
        else 0.0,
    }
    print(json.dumps(snapshot, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        json.dump({"error": str(e)}, sys.stderr, ensure_ascii=False)
        sys.exit(1)
