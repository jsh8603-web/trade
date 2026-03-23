#!/usr/bin/env python3
"""
2022/2023 히스토리컬 시뮬레이션 데이터를 decisions 테이블에 삽입

기존에 rag_analysis_vectors에만 저장된 데이터를 decisions에도 넣어서
match_similar_decisions RPC로 검색 가능하게 만든다.

사용법:
  python scripts/insert_historical_decisions.py 2022 2023
  python scripts/insert_historical_decisions.py all
  python scripts/insert_historical_decisions.py 2022 --dry  # 테스트
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

KST = timezone(timedelta(hours=9))

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

# Gemini rate limit
GEMINI_RPM = 10
_last_call = 0.0


def rate_limit():
    global _last_call
    min_interval = 60.0 / GEMINI_RPM
    elapsed = time.time() - _last_call
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    _last_call = time.time()


def generate_embedding(text: str) -> list[float] | None:
    """Gemini embedding-001 (3072d) -> decisions용 state_embedding에 저장."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
    except ImportError:
        return None

    rate_limit()
    try:
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type="retrieval_document",
        )
        return result["embedding"]
    except Exception as e:
        print(f"    ! 임베딩 실패: {e}")
        return None


def check_existing(year: int) -> set[str]:
    """이미 삽입된 cycle_id 확인."""
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/decisions",
            headers={**HEADERS, "Prefer": ""},
            params={
                "select": "cycle_id",
                "source": f"eq.historical_{year}",
                "limit": 5000,
            },
            timeout=15,
        )
        if r.ok:
            return {row["cycle_id"] for row in r.json() if row.get("cycle_id")}
    except Exception:
        pass
    return set()


def insert_decision(dp: dict, year: int, embedding: list[float] | None) -> bool:
    """데이터포인트를 decisions 테이블에 삽입."""
    ind = dp.get("indicators", {})
    fgi = dp.get("fgi", {})
    external = dp.get("external", {})
    macro = dp.get("macro", {})
    fusion = external.get("fusion", {})

    # 매수/매도/관망 결정 시뮬레이션 (단순 FGI 기반)
    fgi_val = fgi.get("value", 50)
    rsi_val = ind.get("rsi_14", 50)
    if fgi_val <= 25 and rsi_val <= 40:
        decision = "매수"
        confidence = 0.7
    elif fgi_val >= 75 and rsi_val >= 70:
        decision = "매도"
        confidence = 0.6
    else:
        decision = "관망"
        confidence = 0.5

    dt_str = dp.get("datetime", "")
    cycle_id = f"hist_{year}_{dt_str}"

    # 시장 데이터 스냅샷 (JSON)
    snapshot = {
        "indicators": ind,
        "fgi": fgi,
        "macro": macro,
        "external_summary": {
            "news": external.get("news", {}).get("sentiment", "neutral"),
            "whale": external.get("whale", {}).get("direction", "neutral"),
            "sns": external.get("sns", {}).get("sentiment", "neutral"),
            "fusion": fusion.get("signal", "neutral"),
        },
    }

    payload = {
        "market": "KRW-BTC",
        "decision": decision,
        "confidence": confidence,
        "reason": f"[historical_{year}] FGI={fgi_val}, RSI={rsi_val:.0f}, macro={macro.get('score', 0)}, fusion={fusion.get('signal', 'neutral')}",
        "current_price": int(ind.get("current_price", 0)),
        "fear_greed_value": fgi_val,
        "rsi_value": round(rsi_val, 2),
        "sma20_price": int(ind.get("sma_20", 0)),
        "created_at": dt_str,
        "cycle_id": cycle_id,
        "source": f"historical_{year}",
        "executed": False,
        "dry_run": True,
        "market_data_snapshot": json.dumps(snapshot, ensure_ascii=False),
        "embedding_text": dp.get("embedding_text", ""),
        "machine_name": "pc36_backfill",
    }

    if embedding:
        payload["state_embedding"] = str(embedding)

    try:
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/decisions",
            headers=HEADERS,
            json=payload,
            timeout=15,
        )
        return r.status_code in (200, 201)
    except Exception:
        return False


def process_year(year: int, dry_run: bool = False):
    """한 연도 처리."""
    data_path = PROJECT_DIR / "data" / f"historical_{year}" / "sim_data_points.json"
    vectors_path = PROJECT_DIR / "data" / f"historical_{year}" / "embedding_vectors.json"

    if not data_path.exists():
        print(f"  [SKIP] {data_path} 없음")
        return

    print(f"\n{'='*60}")
    print(f"  {year}년 decisions 테이블 삽입")
    print(f"{'='*60}")

    with open(data_path, "r", encoding="utf-8") as f:
        data_points = json.load(f)
    print(f"  데이터: {len(data_points)}개")

    # 기존 벡터 로드
    vectors = {}
    if vectors_path.exists():
        with open(vectors_path, "r", encoding="utf-8") as f:
            for item in json.load(f):
                vectors[item["seq"]] = item["vector"]
        print(f"  벡터: {len(vectors)}개 로드")

    # 중복 체크
    existing = check_existing(year)
    print(f"  기존: {len(existing)}건 (스킵)")

    if dry_run:
        print(f"  [DRY RUN] 실제 삽입하지 않음")
        sample = data_points[0]
        print(f"  샘플: {sample['datetime']}, price={sample['indicators']['current_price']}")
        return

    ok = 0
    fail = 0
    skip = 0
    t0 = time.time()

    for i, dp in enumerate(data_points):
        seq = dp["seq"]
        cycle_id = f"hist_{year}_{dp['datetime']}"

        if cycle_id in existing:
            skip += 1
            continue

        embedding = vectors.get(seq)

        success = insert_decision(dp, year, embedding)
        if success:
            ok += 1
        else:
            fail += 1

        total = ok + fail + skip
        if total % 200 == 0 and total > 0:
            elapsed = time.time() - t0
            print(f"    {total}/{len(data_points)} (삽입: {ok}, 스킵: {skip}, 실패: {fail}, {elapsed:.0f}초)")

    elapsed = time.time() - t0
    print(f"\n  완료: {ok}건 삽입, {skip}건 스킵, {fail}건 실패 ({elapsed:.0f}초)")


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: SUPABASE 환경변수 필요")
        sys.exit(1)

    args = sys.argv[1:]
    dry_run = "--dry" in args
    args = [a for a in args if a != "--dry"]

    if not args:
        print("사용법: python insert_historical_decisions.py <year|all> [--dry]")
        sys.exit(1)

    if "all" in args:
        data_root = PROJECT_DIR / "data"
        years = sorted([
            int(d.name.replace("historical_", ""))
            for d in data_root.iterdir()
            if d.is_dir() and d.name.startswith("historical_") and d.name[-4:].isdigit()
        ])
    else:
        years = [int(a) for a in args]

    print(f"대상: {years} {'[DRY RUN]' if dry_run else ''}")

    for year in years:
        process_year(year, dry_run)

    print(f"\n{'='*60}")
    print(f"  전체 완료! ({len(years)}개 연도)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
