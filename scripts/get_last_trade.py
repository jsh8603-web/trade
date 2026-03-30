import hashlib
import json
import os
import time
import uuid
from pathlib import Path
from urllib.parse import urlencode

from dotenv import load_dotenv
import jwt
import requests

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

UPBIT_API = "https://api.upbit.com/v1"

def make_auth_header(query_string: str = "") -> dict:
    access_key = os.environ.get("UPBIT_ACCESS_KEY", "")
    secret_key = os.environ.get("UPBIT_SECRET_KEY", "")
    if not access_key or not secret_key:
        raise ValueError("UPBIT_ACCESS_KEY / UPBIT_SECRET_KEY 환경변수가 설정되지 않았습니다")
    
    payload = {
        "access_key": access_key,
        "nonce": str(uuid.uuid4()),
        "timestamp": int(time.time() * 1000),
    }
    
    if query_string:
        payload["query_hash"] = hashlib.sha512(query_string.encode()).hexdigest()
        payload["query_hash_alg"] = "SHA512"
        
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}

def main():
    # 완료된 주문(done) 중 매수(bid) 주문 조회
    params = {
        "state": "done",
        "market": "KRW-BTC",
        "order_by": "desc"
    }
    qs = urlencode(params)
    headers = make_auth_header(qs)
    
    r = requests.get(f"{UPBIT_API}/orders", params=params, headers=headers, timeout=10)
    r.raise_for_status()
    orders = r.json()
    
    # 매수 주문만 필터링 (이미 파라미터로 처리되기도 하지만 확실히 하기 위해)
    buy_orders = [o for o in orders if o['side'] == 'bid']
    
    if not buy_orders:
        print(json.dumps({"message": "최근 매수 거래 내역이 없습니다."}, indent=2, ensure_ascii=False))
        return

    last_buy = buy_orders[0]
    
    # 상세 체결 정보 조회 (필요한 경우)
    order_uuid = last_buy['uuid']
    order_qs = urlencode({"uuid": order_uuid})
    order_headers = make_auth_header(order_qs)
    r_detail = requests.get(f"{UPBIT_API}/order", params={"uuid": order_uuid}, headers=order_headers, timeout=10)
    
    if r_detail.ok:
        detail = r_detail.json()
        print(json.dumps(detail, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(last_buy, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
