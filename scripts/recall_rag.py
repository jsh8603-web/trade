#!/usr/bin/env python3
"""
RAG 기반 과거 거래 리콜 -- 현재 시장과 가장 유사한 과거 경험 조회

사용법:
  python3 scripts/recall_rag.py                    # 현재 시장 데이터 자동 수집
  python3 scripts/recall_rag.py data/snapshots/market.json  # JSON 파일에서 로드
  python3 scripts/recall_rag.py --top 5            # 상위 5건 조회 (기본 3건)
  python3 scripts/recall_rag.py --json             # JSON 구조화 출력

출력: 토큰 절약형 한 줄 요약 (파이프라인 프롬프트 주입용)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from scripts.hide_console import subprocess_kwargs
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
KST = timezone(timedelta(hours=9))


def _get_venv_python() -> str:
    venv = PROJECT_ROOT / ".venv" / "bin" / "python3"
    return str(venv) if venv.exists() else "python3"


def collect_current_market_data() -> dict:
    """collect_market_data.py와 collect_fear_greed.py를 실행하여 현재 시장 데이터를 수집."""
    python = _get_venv_python()
    result = {}

    # 시장 데이터 수집
    try:
        proc = subprocess.run(
            [python, "scripts/collect_market_data.py"],
            capture_output=True, text=True, timeout=30,
            cwd=str(PROJECT_ROOT),
            **subprocess_kwargs(),
        )
        if proc.returncode == 0:
            result = json.loads(proc.stdout)
    except Exception as e:
        print(f"[recall_rag] 시장 데이터 수집 실패: {e}", file=sys.stderr)

    # 공포탐욕지수 수집
    try:
        proc = subprocess.run(
            [python, "scripts/collect_fear_greed.py"],
            capture_output=True, text=True, timeout=15,
            cwd=str(PROJECT_ROOT),
            **subprocess_kwargs(),
        )
        if proc.returncode == 0:
            fgi_data = json.loads(proc.stdout)
            result["fear_greed"] = fgi_data
            # fear_greed_value를 최상위에도 배치 (build_embedding_text 호환)
            current = fgi_data.get("current", {})
            if current.get("value"):
                result["fear_greed_value"] = current["value"]
    except Exception as e:
        print(f"[recall_rag] FGI 수집 실패: {e}", file=sys.stderr)

    return result


def get_embedding(text: str) -> list | None:
    """Gemini API로 텍스트 임베딩(3072d)을 생성."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type="retrieval_query",
        )
        return result["embedding"]
    except Exception as e:
        print(f"[recall_rag] 임베딩 생성 실패: {e}", file=sys.stderr)
        return None


def query_similar_decisions(embedding: list, limit: int = 3) -> list[dict]:
    """core.db rpc_match 로 유사 결정을 조회 (decisions.state_embedding 코사인).

    백엔드 무관 (INV_DB_BACKEND=sqlite 기본). 임베딩은 raw float list 그대로.
    """
    try:
        from core.db import db
        rows = db.rpc_match(
            "decisions", embedding,
            column="state_embedding", k=limit,
        )
        for r in rows:
            sim = r.pop("_similarity", None)
            if sim is not None:
                r["similarity"] = sim
        return rows
    except Exception as e:
        print(f"[recall_rag] rpc_match 예외: {e}", file=sys.stderr)
        return []


def format_result_line(row: dict) -> str:
    """한 건의 유사 결정을 한 줄 요약으로 포맷."""
    similarity = row.get("similarity", 0)
    pct = int(similarity * 100) if similarity <= 1 else int(similarity)

    created = row.get("created_at", "")
    if isinstance(created, datetime):
        date_str = created.strftime("%Y-%m-%d")
    elif isinstance(created, str):
        date_str = created[:10]
    else:
        date_str = "unknown"

    decision = row.get("decision", "?")
    rsi = row.get("rsi_value", row.get("rsi_14"))
    fgi = row.get("fear_greed_value", row.get("fgi_value"))
    profit = row.get("profit_loss")

    # 지표 요약
    indicators = []
    if rsi is not None:
        indicators.append(f"RSI {int(float(rsi))}")
    if fgi is not None:
        indicators.append(f"FGI {int(float(fgi))}")
    ind_str = ", ".join(indicators) if indicators else "지표 없음"

    # 성과 요약
    if profit is not None:
        profit = float(profit)
        if profit > 0:
            perf = f"수익 +{profit:.1f}%"
        elif profit < 0:
            perf = f"손실 {profit:.1f}%"
        else:
            perf = "변동 없음"
    else:
        perf = "성과 미측정"

    # 사유 요약 (최대 30자)
    reason = row.get("reason", "")
    if reason and len(reason) > 30:
        reason = reason[:27] + "..."
    reason_str = f" ({reason})" if reason else ""

    return f"[유사도 {pct}%] {date_str} {decision}: {ind_str} → {perf}{reason_str}"


def main():
    parser = argparse.ArgumentParser(description="RAG 기반 과거 거래 리콜")
    parser.add_argument("market_json", nargs="?", help="시장 데이터 JSON 파일 경로")
    parser.add_argument("--top", type=int, default=3, help="조회 건수 (기본 3)")
    parser.add_argument("--json", action="store_true", help="JSON 구조화 출력")
    args = parser.parse_args()

    # 1. 시장 데이터 로드
    if args.market_json:
        try:
            with open(args.market_json) as f:
                market_data = json.load(f)
        except Exception as e:
            print(f"[recall_rag] JSON 파일 로드 실패: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        market_data = collect_current_market_data()
        if not market_data:
            print("[recall_rag] 시장 데이터 수집 실패", file=sys.stderr)
            sys.exit(1)

    # 2. 임베딩 텍스트 생성 (save_decision.py와 동일한 함수 사용)
    try:
        from scripts.save_decision import build_embedding_text
        text = build_embedding_text(market_data)
    except (ImportError, ModuleNotFoundError) as e:
        print(f"[recall_rag] build_embedding_text import 실패, 폴백 사용: {e}", file=sys.stderr)
        parts = []
        for key in ("current_price", "change_rate_24h", "volume_24h", "market"):
            if key in market_data:
                parts.append(f"{key}={market_data[key]}")
        indicators = market_data.get("indicators", {})
        for key in ("rsi_14", "sma_20", "macd"):
            if key in indicators:
                parts.append(f"{key}={indicators[key]}")
        text = " ".join(parts) if parts else None
    if not text:
        print("[recall_rag] 임베딩 텍스트 생성 불가 (데이터 부족)", file=sys.stderr)
        sys.exit(1)

    # 3. 임베딩 벡터 생성
    embedding = get_embedding(text)
    if not embedding:
        print("[recall_rag] 임베딩 벡터 생성 실패", file=sys.stderr)
        sys.exit(1)

    # 4. 유사 결정 조회
    results = query_similar_decisions(embedding, args.top)

    if not results:
        msg = "과거 임베딩 데이터 없음 -- 거래 이력이 쌓이면 유사 경험을 조회할 수 있습니다."
        if args.json:
            print(json.dumps({"status": "no_data", "message": msg, "query_text": text}, ensure_ascii=False))
        else:
            print(msg)
        return

    # 5. 출력
    if args.json:
        output = {
            "status": "ok",
            "query_text": text,
            "results": [],
        }
        for row in results:
            output["results"].append({
                "similarity": round(float(row.get("similarity", 0)), 4),
                "date": str(row.get("created_at", ""))[:10],
                "decision": row.get("decision"),
                "reason": row.get("reason", ""),
                "profit_loss": float(row["profit_loss"]) if row.get("profit_loss") is not None else None,
                "rsi": float(row["rsi_value"]) if row.get("rsi_value") is not None else None,
                "fgi": int(row["fear_greed_value"]) if row.get("fear_greed_value") is not None else None,
                "confidence": float(row["confidence"]) if row.get("confidence") is not None else None,
            })
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        for row in results:
            print(format_result_line(row))


if __name__ == "__main__":
    main()
