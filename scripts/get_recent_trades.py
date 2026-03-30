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
    # 모든 마켓에 대해 완료된 주문(done) 조회 (전체 마켓)
    # market 파라미터를 빼면 모든 마켓에 대해 조회 가능
    params = {
        "state": "done",
        "order_by": "desc",
        "limit": 10
    }
    qs = urlencode(params)
    headers = make_auth_header(qs)
    
    r = requests.get(f"{UPBIT_API}/orders", params=params, headers=headers, timeout=10)
    r.raise_for_status()
    orders = r.json()
    
    if not orders:
        print(json.dumps({"message": "최근 체결 거래 내역이 없습니다."}, indent=2, ensure_ascii=False))
        return

    # 각 주문에 대해 상세 정보 및 체결 내역(trades) 포함하여 출력
    detailed_orders = []
    for order in orders:
        order_uuid = order['uuid']
        order_qs = urlencode({"uuid": order_uuid})
        order_headers = make_auth_header(order_qs)
        r_detail = requests.get(f"{UPBIT_API}/order", params={"uuid": order_uuid}, headers=order_headers, timeout=10)
        if r_detail.ok:
            detailed_orders.append(r_detail.json())
        else:
            detailed_orders.append(order)
            
    print(json.dumps(detailed_orders, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
