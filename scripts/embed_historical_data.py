#!/usr/bin/env python3
"""
기존 히스토리컬 데이터에 Gemini 임베딩 생성 + Supabase 벡터 저장

사용법:
  python scripts/embed_historical_data.py 2023        # 2023년만
  python scripts/embed_historical_data.py 2022 2023   # 둘 다 순차 처리
  python scripts/embed_historical_data.py all          # 모든 연도

이미 수집된 data/historical_{year}/ 디렉토리의 데이터를 읽어서:
  1) Gemini embedding-001로 3072d 벡터 생성
  2) Supabase rag_analysis_vectors 테이블에 저장
  3) 로컬에 embedding_vectors.json 저장 (재사용용)
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
load_dotenv(PROJECT_DIR / ".env")

# ── 설정 ──
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
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
    """Gemini embedding-001 3072d 벡터 생성."""
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)

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


def store_to_supabase(cycle_id: str, analysis_text: str, analysis_json: dict,
                      embedding: list[float], market_regime: str) -> bool:
    """Supabase rag_analysis_vectors에 저장."""
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    payload = {
        "cycle_id": cycle_id,
        "analysis_text": analysis_text,
        "analysis_json": analysis_json,
        "market_regime": market_regime,
        "embedding": embedding,
    }
    try:
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/rag_analysis_vectors",
            headers=headers,
            json=payload,
            timeout=15,
        )
        return resp.status_code in (200, 201)
    except Exception:
        return False


def check_existing_in_supabase(year: int) -> set[str]:
    """이미 저장된 cycle_id를 조회하여 중복 방지."""
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/rag_analysis_vectors",
            headers=headers,
            params={
                "select": "cycle_id",
                "cycle_id": f"like.hist_{year}_*",
                "limit": 5000,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return {r["cycle_id"] for r in resp.json()}
    except Exception:
        pass
    return set()


def determine_market_regime(fgi_val: int, rsi: float, change_24h: float) -> str:
    if fgi_val <= 20 or change_24h < -5:
        return "extreme_fear"
    elif fgi_val <= 35:
        return "fear"
    elif fgi_val >= 80 or change_24h > 5:
        return "extreme_greed"
    elif fgi_val >= 65:
        return "greed"
    elif abs(change_24h) < 1 and 40 <= rsi <= 60:
        return "sideways"
    elif rsi > 70:
        return "overbought"
    elif rsi < 30:
        return "oversold"
    else:
        return "neutral"


def process_year(year: int):
    """한 연도의 데이터에 임베딩 생성 + Supabase 저장."""
    data_dir = PROJECT_DIR / "data" / f"historical_{year}"
    points_file = data_dir / "sim_data_points.json"
    vectors_file = data_dir / "embedding_vectors.json"

    if not points_file.exists():
        print(f"  [SKIP] {points_file} 없음")
        return

    print(f"\n{'='*60}")
    print(f"  {year}년 임베딩 + Supabase 저장 시작")
    print(f"{'='*60}")

    # 데이터 로드
    with open(points_file, "r", encoding="utf-8") as f:
        data_points = json.load(f)
    print(f"  데이터 포인트: {len(data_points)}개")

    # 기존 벡터 로드 (이미 생성된 것은 재사용)
    existing_vectors = {}
    if vectors_file.exists():
        with open(vectors_file, "r", encoding="utf-8") as f:
            for item in json.load(f):
                existing_vectors[item["seq"]] = item["vector"]
        print(f"  기존 벡터: {len(existing_vectors)}개 로드 (재사용)")

    # Supabase 중복 체크
    existing_ids = set()
    if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
        existing_ids = check_existing_in_supabase(year)
        if existing_ids:
            print(f"  Supabase 기존: {len(existing_ids)}건 (중복 스킵)")

    # 임베딩 생성
    t0 = time.time()
    new_vectors = {}
    embed_ok = 0
    embed_fail = 0
    embed_reuse = 0

    print(f"\n  [Phase 1] Gemini 임베딩 생성...")
    for i, dp in enumerate(data_points):
        seq = dp["seq"]

        if seq in existing_vectors:
            embed_reuse += 1
            continue

        emb_text = dp.get("embedding_text", "")
        if not emb_text:
            embed_fail += 1
            continue

        embedding = generate_embedding(emb_text)
        if embedding:
            new_vectors[seq] = embedding
            embed_ok += 1
        else:
            embed_fail += 1

        total_done = embed_reuse + embed_ok + embed_fail
        if total_done % 50 == 0:
            elapsed = time.time() - t0
            remaining = len(data_points) - total_done
            eta_min = (elapsed / max(total_done - embed_reuse, 1)) * remaining / 60 if embed_ok > 0 else 0
            print(f"    {total_done}/{len(data_points)} (신규: {embed_ok}, 재사용: {embed_reuse}, 실패: {embed_fail}, ETA: ~{eta_min:.0f}분)")

    # 벡터 통합 저장
    all_vectors = {**existing_vectors, **new_vectors}
    with open(vectors_file, "w", encoding="utf-8") as f:
        json.dump(
            [{"seq": seq, "dim": len(vec), "vector": vec} for seq, vec in sorted(all_vectors.items())],
            f, ensure_ascii=False,
        )

    embed_total = embed_ok + embed_reuse
    print(f"\n  임베딩 완료: 총 {embed_total}건 (신규 {embed_ok}, 재사용 {embed_reuse}, 실패 {embed_fail})")

    # Supabase 저장
    sb_ok = 0
    sb_fail = 0
    sb_skip = 0

    if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY and all_vectors:
        print(f"\n  [Phase 2] Supabase 벡터 저장...")
        for i, dp in enumerate(data_points):
            seq = dp["seq"]
            if seq not in all_vectors:
                continue

            cycle_id = f"hist_{year}_{dp['datetime']}"
            if cycle_id in existing_ids:
                sb_skip += 1
                continue

            fgi_val = dp.get("fgi", {}).get("value", 50)
            rsi = dp.get("indicators", {}).get("rsi_14", 50)
            change_24h = dp.get("indicators", {}).get("price_change_24h", 0)
            market_regime = dp.get("market_regime") or determine_market_regime(fgi_val, rsi, change_24h)

            analysis_json = {
                "year": year,
                "source": "historical_simulation",
                "indicators": dp.get("indicators", {}),
                "fgi": dp.get("fgi", {}),
                "macro": dp.get("macro", {}),
                "external_summary": {
                    "news": dp.get("external", {}).get("news", {}).get("sentiment", "neutral"),
                    "whale": dp.get("external", {}).get("whale", {}).get("direction", "neutral"),
                    "sns": dp.get("external", {}).get("sns", {}).get("sentiment", "neutral"),
                    "fusion": dp.get("external", {}).get("fusion", {}).get("signal", "neutral"),
                },
            }

            ok = store_to_supabase(
                cycle_id=cycle_id,
                analysis_text=dp.get("embedding_text", ""),
                analysis_json=analysis_json,
                embedding=all_vectors[seq],
                market_regime=market_regime,
            )
            if ok:
                sb_ok += 1
            else:
                sb_fail += 1

            total_sb = sb_ok + sb_fail + sb_skip
            if total_sb % 100 == 0 and total_sb > 0:
                print(f"    {total_sb}/{len(data_points)} (저장: {sb_ok}, 스킵: {sb_skip}, 실패: {sb_fail})")

        print(f"\n  Supabase 완료: {sb_ok}건 저장, {sb_skip}건 스킵(중복), {sb_fail}건 실패")
    else:
        print("\n  Supabase 저장 스킵 (키 없음 또는 벡터 없음)")

    elapsed = time.time() - t0
    print(f"\n  {year}년 처리 완료 ({elapsed:.0f}초)")
    print(f"  임베딩: {embed_total}건 | Supabase: {sb_ok}건 저장")


def main():
    if not GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY 없음")
        sys.exit(1)

    args = sys.argv[1:]
    if not args:
        print("사용법: python embed_historical_data.py <year|all> [year2 ...]")
        print("  python embed_historical_data.py 2023")
        print("  python embed_historical_data.py 2022 2023")
        print("  python embed_historical_data.py all")
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

    print(f"처리 대상: {years}")
    print(f"Gemini: [ON] | Supabase: {'[ON]' if SUPABASE_URL else '[OFF]'}")

    for year in years:
        process_year(year)

    print(f"\n{'='*60}")
    print(f"  전체 완료! ({len(years)}개 연도)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
