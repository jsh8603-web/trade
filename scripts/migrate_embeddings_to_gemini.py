#!/usr/bin/env python3
"""임베딩 없는 실매매 decisions 전체를 Gemini 3072d로 벡터화

사용법:
  python3 scripts/migrate_embeddings_to_gemini.py          # 실행
  python3 scripts/migrate_embeddings_to_gemini.py --dry     # 드라이런
  python3 scripts/migrate_embeddings_to_gemini.py --all     # 훈련 데이터 포함 전체

대상: source가 agent, short_term, llm, manual, agent+rl인 실매매 decisions
제외: pc128 훈련 데이터 (--all 옵션으로 포함 가능)
"""

import os
import sys
import time
import base64
import subprocess as sp
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
PROJECT_REF = "REDACTED_PROJECT_REF"

# 실매매 소스만 (훈련 데이터 제외)
REAL_TRADE_SOURCES = ["agent", "short_term", "llm", "manual", "agent+rl"]


def _get_mgmt_token() -> str:
    try:
        raw = sp.check_output(
            ["security", "find-generic-password", "-s", "Supabase CLI", "-a", "supabase", "-w"],
            text=True, stderr=sp.DEVNULL,
        ).strip()
        if raw.startswith("go-keyring-base64:"):
            return base64.b64decode(raw.split(":", 1)[1]).decode()
        return raw
    except Exception:
        return ""


def get_decisions_without_embedding(include_all: bool = False) -> list[dict]:
    """임베딩 없는 decisions 조회."""
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    params = {
        "select": "id,decision,created_at,source,current_price,rsi_value,fear_greed_value,sma20_price,embedding_text,reason,profit_loss",
        "state_embedding": "is.null",
        "order": "created_at.asc",
        "limit": "2000",
    }
    if not include_all:
        params["source"] = f"in.({','.join(REAL_TRADE_SOURCES)})"

    r = requests.get(f"{SUPABASE_URL}/rest/v1/decisions", headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def build_embedding_text_from_row(row: dict) -> str:
    """DB 행의 필드에서 임베딩 텍스트를 재구성."""
    # 이미 embedding_text가 있으면 그대로 사용
    if row.get("embedding_text"):
        return row["embedding_text"]

    # DB 필드에서 재구성
    from scripts.save_decision import build_embedding_text
    market_data = {
        "current_price": row.get("current_price"),
        "rsi_14": row.get("rsi_value"),
        "fear_greed_value": row.get("fear_greed_value"),
        "sma_20": row.get("sma20_price"),
    }
    text = build_embedding_text(market_data)

    # reason 필드에서 추가 정보 추출 (PC128 훈련 데이터 등)
    reason = row.get("reason", "")
    if reason:
        import re
        # momentum, volume, maxPnL, maxDD 등 숫자 지표 추출
        extras = []
        mom = re.search(r'mom=([+\-]?[\d.]+%)', reason)
        if mom:
            extras.append(f"Momentum {mom.group(1)}.")
        vol = re.search(r'vol=([\d.]+x)', reason)
        if vol:
            extras.append(f"Volume ratio {vol.group(1)}.")
        pnl = re.search(r'maxPnL=([+\-]?[\d.]+%)', reason)
        if pnl:
            extras.append(f"Max PnL {pnl.group(1)}.")
        dd = re.search(r'maxDD=([+\-]?[\d.]+%)', reason)
        if dd:
            extras.append(f"Max drawdown {dd.group(1)}.")
        # profit_loss가 있으면 추가
        pl = row.get("profit_loss")
        if pl is not None:
            extras.append(f"Realized PnL {float(pl):+.2f}%.")
        if extras:
            text = (text + " " + " ".join(extras)).strip()

    # decision 정보 추가
    decision = row.get("decision", "")
    if decision and decision not in text:
        text = f"Decision: {decision}. {text}"

    return text


def generate_gemini_embedding(text: str) -> list[float] | None:
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type="retrieval_document",
        )
        return result["embedding"]
    except Exception as e:
        print(f"  [ERROR] 임베딩 생성 실패: {e}", file=sys.stderr)
        return None


def update_embedding_mgmt(token: str, decision_id: str, embedding: list[float], emb_text: str) -> bool:
    vec_str = "[" + ",".join(str(v) for v in embedding) + "]"
    safe_text = emb_text.replace("'", "''")
    sql = (
        f"UPDATE decisions SET state_embedding = '{vec_str}'::vector, "
        f"embedding_text = '{safe_text}' WHERE id = '{decision_id}'"
    )
    r = requests.post(
        f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"query": sql},
        timeout=30,
    )
    return r.ok


def main():
    dry_run = "--dry" in sys.argv
    include_all = "--all" in sys.argv

    print("=" * 60)
    print("임베딩 일괄 생성: Gemini embedding-001 (3072d)")
    print(f"대상: {'전체' if include_all else '실매매만 (agent/short_term/llm/manual)'}")
    print("=" * 60)

    token = _get_mgmt_token()
    if not token and not dry_run:
        print("[ERROR] Management API 토큰 없음", file=sys.stderr)
        sys.exit(1)

    decisions = get_decisions_without_embedding(include_all)
    print(f"\n임베딩 대상: {len(decisions)}건")

    if not decisions:
        print("모든 decisions에 임베딩이 있습니다.")
        return

    # source별 통계
    from collections import Counter
    source_dist = Counter(r.get("source", "?") for r in decisions)
    for s, c in source_dist.most_common():
        print(f"  {s}: {c}건")

    success = 0
    failed = 0
    skipped = 0

    for i, row in enumerate(decisions, 1):
        did = row["id"]
        date = row.get("created_at", "")[:16]
        decision = row.get("decision", "?")
        source = row.get("source", "?")

        # 임베딩 텍스트 생성
        emb_text = build_embedding_text_from_row(row)
        if not emb_text:
            if i <= 5 or i % 50 == 0:
                print(f"[{i}/{len(decisions)}] {date} {decision} ({source}) — 데이터 부족, 건너뜀")
            skipped += 1
            continue

        if i <= 10 or i % 50 == 0:
            print(f"[{i}/{len(decisions)}] {date} {decision} ({source}) — {emb_text[:60]}...")

        # Gemini 임베딩 생성
        embedding = generate_gemini_embedding(emb_text)
        if not embedding:
            failed += 1
            continue

        # DB 저장
        if dry_run:
            success += 1
        else:
            if update_embedding_mgmt(token, did, embedding, emb_text):
                success += 1
            else:
                failed += 1
                print(f"  [FAIL] {did[:8]}...")

        # Gemini rate limit (분당 1500 요청 가능하지만 안전하게)
        if i % 10 == 0:
            time.sleep(1)

    print(f"\n{'=' * 60}")
    print(f"결과: 성공 {success}건, 실패 {failed}건, 건너뜀 {skipped}건")
    if dry_run:
        print("(드라이런 — 실제 DB 변경 없음)")
    print("=" * 60)


if __name__ == "__main__":
    main()
