#!/usr/bin/env python3
"""
Brain-Inspired Memory System — 인간 뇌 기억 구조 모방

3-tier:
  working   = MEMORY.md (항상 로드, ~40줄 핵심만)
  short_term = DB (최근 7일, 상세, 자주 접근)
  long_term  = DB (7일+, 압축/병합, 필요 시 리콜)

사용법:
  python3 scripts/memory.py store "제목" "내용" --category feedback --tags rc,watchdog
  python3 scripts/memory.py recall "RC 좀비 판별"           # 시맨틱 검색
  python3 scripts/memory.py recall-context "워치독 수정"    # 대화 시작 시 컨텍스트 주입
  python3 scripts/memory.py list [--tier short_term] [--category feedback]
  python3 scripts/memory.py get <id>
  python3 scripts/memory.py update <id> "새 내용" [--title "새 제목"]
  python3 scripts/memory.py delete <id>
  python3 scripts/memory.py touch <id>                     # access_count 증가
  python3 scripts/memory.py pin <id> / unpin <id>
  python3 scripts/memory.py consolidate [--dry-run]        # short→long 압축
  python3 scripts/memory.py decay                          # 관련성 감쇠
  python3 scripts/memory.py stats                          # 통계
  python3 scripts/memory.py import-md                      # .md 파일 → DB 마이그레이션
"""

from __future__ import annotations

import json
import os
import sys
import time
import re
import yaml
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
KST = timezone(timedelta(hours=9))
TABLE = "claude_memories"

MEMORY_DIR = Path.home() / ".claude" / "projects" / "-Users-drj00-workspace-blockchain" / "memory"

# ─── Supabase REST helpers ───────────────────────────────────────────────────

def _headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _get(params: dict = None, single=False) -> list | dict | None:
    import requests
    url = f"{SUPABASE_URL}/rest/v1/{TABLE}"
    r = requests.get(url, headers=_headers(), params=params or {}, timeout=15)
    if not r.ok:
        print(f"[memory] GET error: {r.status_code} {r.text}", file=sys.stderr)
        return [] if not single else None
    data = r.json()
    if single:
        return data[0] if data else None
    return data


def _post(data: dict) -> dict | None:
    import requests
    url = f"{SUPABASE_URL}/rest/v1/{TABLE}"
    r = requests.post(url, headers=_headers(), json=data, timeout=15)
    if not r.ok:
        print(f"[memory] POST error: {r.status_code} {r.text}", file=sys.stderr)
        return None
    result = r.json()
    return result[0] if isinstance(result, list) and result else result


def _patch(mem_id: str, data: dict) -> bool:
    import requests
    url = f"{SUPABASE_URL}/rest/v1/{TABLE}?id=eq.{mem_id}"
    r = requests.patch(url, headers=_headers(), json=data, timeout=15)
    return r.ok


def _delete(mem_id: str) -> bool:
    import requests
    url = f"{SUPABASE_URL}/rest/v1/{TABLE}?id=eq.{mem_id}"
    r = requests.delete(url, headers=_headers(), timeout=15)
    return r.ok


def _rpc(fn_name: str, payload: dict) -> list:
    import requests
    url = f"{SUPABASE_URL}/rest/v1/rpc/{fn_name}"
    r = requests.post(url, headers=_headers(), json=payload, timeout=30)
    if not r.ok:
        print(f"[memory] RPC {fn_name} error: {r.status_code} {r.text}", file=sys.stderr)
        return []
    return r.json()


# ─── Gemini Embedding ────────────────────────────────────────────────────────

def get_embedding(text: str) -> list | None:
    """Gemini embedding-001 (3072d)."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text[:8000],  # 토큰 제한
            task_type="retrieval_document",
        )
        return result["embedding"]
    except Exception as e:
        print(f"[memory] 임베딩 생성 실패: {e}", file=sys.stderr)
        return None


def get_query_embedding(text: str) -> list | None:
    """쿼리용 임베딩 (task_type 다름)."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text[:4000],
            task_type="retrieval_query",
        )
        return result["embedding"]
    except Exception as e:
        print(f"[memory] 쿼리 임베딩 실패: {e}", file=sys.stderr)
        return None


# ─── Commands ────────────────────────────────────────────────────────────────

def cmd_store(args):
    """새 메모리 저장."""
    title = args.title
    content = args.content
    category = args.category or "project"
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
    pinned = args.pin

    # 임베딩 생성
    embed_text = f"{title}\n{content[:2000]}"
    embedding = get_embedding(embed_text)

    data = {
        "title": title,
        "content": content,
        "category": category,
        "tags": tags,
        "memory_tier": "short_term",
        "pinned": pinned,
        "relevance_score": 1.0,
    }
    if embedding:
        data["embedding"] = str(embedding)

    result = _post(data)
    if result:
        print(f"✅ 저장: {result.get('id', '?')[:8]}.. [{category}] {title}")
    else:
        print("❌ 저장 실패", file=sys.stderr)


def cmd_recall(args):
    """시맨틱 검색으로 관련 메모리 리콜."""
    query = args.query
    limit = args.limit or 5

    # 1) 시맨틱 검색
    embedding = get_query_embedding(query)
    semantic_results = []
    if embedding:
        semantic_results = _rpc("match_similar_memories", {
            "query_embedding": str(embedding),
            "match_limit": limit,
        })

    # 2) 키워드 fallback (태그 + 제목)
    keyword_results = _get({
        "or": f"(title.ilike.%{query}%,tags.cs.{{{query}}})",
        "order": "relevance_score.desc",
        "limit": str(limit),
        "select": "id,memory_tier,category,title,summary,content,tags,relevance_score,pinned,access_count,last_accessed,created_at",
    })

    # 3) 병합 + 중복 제거
    seen = set()
    merged = []
    for r in (semantic_results or []):
        if r["id"] not in seen:
            seen.add(r["id"])
            merged.append(r)
    for r in (keyword_results or []):
        if r["id"] not in seen:
            seen.add(r["id"])
            r["similarity"] = 0.0
            merged.append(r)

    # 4) access_count 갱신
    now = datetime.now(timezone.utc).isoformat()
    for r in merged[:limit]:
        _patch(r["id"], {
            "access_count": (r.get("access_count") or 0) + 1,
            "last_accessed": now,
        })

    # 5) 출력
    if not merged:
        print(f"검색 결과 없음: '{query}'")
        return

    for i, r in enumerate(merged[:limit]):
        sim = r.get("similarity", 0)
        tier = "🟢" if r["memory_tier"] == "short_term" else "🔵"
        pin = "📌" if r.get("pinned") else ""
        cat = r["category"][:4]
        score = r.get("relevance_score", 0)
        print(f"{tier}{pin} [{cat}] {r['title']}")
        # 요약이 있으면 요약, 없으면 content 첫 150자
        text = r.get("summary") or (r.get("content", "")[:150] + "...")
        print(f"   {text}")
        print(f"   sim={sim:.2f} rel={score:.2f} acc={r.get('access_count',0)} id={r['id'][:8]}")
        print()


def cmd_recall_context(args):
    """대화 시작 시 컨텍스트 주입용 리콜."""
    query = args.query
    limit = args.limit or 10

    results = []

    # 1) pinned 메모리 (항상 포함)
    pinned = _get({
        "pinned": "eq.true",
        "select": "id,title,content,category,tags",
        "order": "category",
    })
    if pinned:
        results.extend(pinned)

    # 2) 최근 24시간 short_term (최근 작업 컨텍스트)
    yesterday = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    recent = _get({
        "memory_tier": "eq.short_term",
        "created_at": f"gte.{yesterday}",
        "select": "id,title,content,category,tags",
        "order": "created_at.desc",
        "limit": "5",
    })
    if recent:
        seen_ids = {r["id"] for r in results}
        results.extend(r for r in recent if r["id"] not in seen_ids)

    # 3) 시맨틱 검색 (쿼리 관련)
    if query:
        embedding = get_query_embedding(query)
        if embedding:
            semantic = _rpc("match_similar_memories", {
                "query_embedding": str(embedding),
                "match_limit": limit,
            })
            seen_ids = {r["id"] for r in results}
            results.extend(r for r in (semantic or []) if r["id"] not in seen_ids)

    # 4) access_count 갱신
    now = datetime.now(timezone.utc).isoformat()
    for r in results:
        _patch(r["id"], {
            "access_count": (r.get("access_count") or 0) + 1,
            "last_accessed": now,
        })

    # 5) 컴팩트 출력 (컨텍스트 주입용)
    if not results:
        print("(리콜된 메모리 없음)")
        return

    print("# 리콜된 메모리")
    print()

    # pinned 먼저
    pinned_items = [r for r in results if r.get("pinned")]
    other_items = [r for r in results if not r.get("pinned")]

    if pinned_items:
        print("## 📌 핵심 규칙")
        for r in pinned_items:
            print(f"- **{r['title']}**: {_compact(r['content'])}")
        print()

    if other_items:
        print("## 관련 컨텍스트")
        for r in other_items[:limit]:
            cat = r.get("category", "?")
            text = r.get("summary") or _compact(r.get("content", ""))
            print(f"- [{cat}] **{r['title']}**: {text}")
        print()


def _compact(text: str, max_len: int = 200) -> str:
    """멀티라인 → 1줄 요약."""
    text = text.replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) > max_len:
        text = text[:max_len] + "..."
    return text


def cmd_list(args):
    """메모리 목록."""
    params = {
        "select": "id,memory_tier,category,title,tags,relevance_score,pinned,access_count,created_at",
        "order": "relevance_score.desc,created_at.desc",
        "limit": str(args.limit or 20),
    }
    if args.tier:
        params["memory_tier"] = f"eq.{args.tier}"
    if args.category:
        params["category"] = f"eq.{args.category}"

    rows = _get(params)
    if not rows:
        print("메모리 없음")
        return

    for r in rows:
        tier = "🟢" if r["memory_tier"] == "short_term" else "🔵"
        pin = "📌" if r.get("pinned") else "  "
        tags = ",".join(r.get("tags") or [])[:20]
        score = r.get("relevance_score", 0)
        acc = r.get("access_count", 0)
        created = r.get("created_at", "")[:10]
        print(f"{tier}{pin} [{r['category'][:4]}] {r['title'][:45]:<45} rel={score:.2f} acc={acc:>3} {created}  {r['id'][:8]}")


def cmd_get(args):
    """단일 메모리 조회."""
    row = _get({"id": f"eq.{args.id}", "select": "*"}, single=True)
    if not row:
        # 짧은 ID로 검색
        rows = _get({"id": f"like.{args.id}%", "select": "*", "limit": "1"})
        row = rows[0] if rows else None
    if not row:
        print(f"❌ 메모리 없음: {args.id}")
        return

    print(f"ID: {row['id']}")
    print(f"Tier: {row['memory_tier']} | Category: {row['category']} | Pinned: {row.get('pinned', False)}")
    print(f"Title: {row['title']}")
    print(f"Tags: {row.get('tags', [])}")
    print(f"Relevance: {row.get('relevance_score', 0):.3f} | Access: {row.get('access_count', 0)}")
    print(f"Created: {row.get('created_at', '')[:19]} | Last accessed: {(row.get('last_accessed') or 'never')[:19]}")
    print(f"─" * 60)
    print(row.get("content", ""))
    if row.get("summary"):
        print(f"\n📝 Summary: {row['summary']}")


def cmd_update(args):
    """메모리 업데이트."""
    data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if args.content:
        data["content"] = args.content
    if args.title:
        data["title"] = args.title

    # 임베딩 재생성
    if "content" in data or "title" in data:
        row = _get({"id": f"eq.{args.id}", "select": "title,content"}, single=True)
        if row:
            t = args.title or row["title"]
            c = args.content or row["content"]
            emb = get_embedding(f"{t}\n{c[:2000]}")
            if emb:
                data["embedding"] = str(emb)

    if _patch(args.id, data):
        print(f"✅ 업데이트: {args.id[:8]}")
    else:
        print(f"❌ 실패: {args.id[:8]}")


def cmd_delete(args):
    """메모리 삭제."""
    if _delete(args.id):
        print(f"🗑️ 삭제: {args.id[:8]}")
    else:
        print(f"❌ 실패: {args.id[:8]}")


def cmd_touch(args):
    """access_count 증가 + last_accessed 갱신."""
    row = _get({"id": f"eq.{args.id}", "select": "access_count"}, single=True)
    if not row:
        print(f"❌ 없음: {args.id[:8]}")
        return
    _patch(args.id, {
        "access_count": (row.get("access_count") or 0) + 1,
        "last_accessed": datetime.now(timezone.utc).isoformat(),
    })
    print(f"👆 touched: {args.id[:8]}")


def cmd_pin(args):
    _patch(args.id, {"pinned": True})
    print(f"📌 pinned: {args.id[:8]}")


def cmd_unpin(args):
    _patch(args.id, {"pinned": False})
    print(f"📌 unpinned: {args.id[:8]}")


def cmd_consolidate(args):
    """short_term → long_term 압축 (7일+ 경과 메모리)."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    old_memories = _get({
        "memory_tier": "eq.short_term",
        "created_at": f"lt.{cutoff}",
        "pinned": "eq.false",
        "select": "id,title,content,category,tags,access_count,relevance_score",
        "order": "category,created_at",
    })

    if not old_memories:
        print("통합 대상 없음 (7일 미경과)")
        return

    print(f"📦 통합 대상: {len(old_memories)}건")

    for mem in old_memories:
        # 요약 생성: content 첫 3줄
        lines = mem["content"].strip().split("\n")
        summary = " ".join(line.strip() for line in lines[:3] if line.strip())[:300]

        if args.dry_run:
            print(f"  [DRY] {mem['title'][:40]} → long_term (summary: {summary[:60]}...)")
            continue

        _patch(mem["id"], {
            "memory_tier": "long_term",
            "summary": summary,
            "consolidated_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        print(f"  ✅ {mem['title'][:40]} → long_term")

    if args.dry_run:
        print(f"\n(dry run — 실제 변경 없음, --dry-run 제거하여 실행)")


def cmd_decay(args):
    """관련성 감쇠 실행."""
    result = _rpc("decay_memory_relevance", {})
    print("✅ 관련성 감쇠 실행 완료")


def cmd_stats(args):
    """메모리 통계."""
    all_mems = _get({
        "select": "memory_tier,category,pinned,relevance_score,access_count",
    })
    if not all_mems:
        print("메모리 없음")
        return

    total = len(all_mems)
    short = sum(1 for m in all_mems if m["memory_tier"] == "short_term")
    long = sum(1 for m in all_mems if m["memory_tier"] == "long_term")
    pinned = sum(1 for m in all_mems if m.get("pinned"))
    avg_rel = sum(m.get("relevance_score", 0) for m in all_mems) / total if total else 0
    avg_acc = sum(m.get("access_count", 0) for m in all_mems) / total if total else 0

    cats = {}
    for m in all_mems:
        c = m["category"]
        cats[c] = cats.get(c, 0) + 1

    print(f"📊 메모리 통계")
    print(f"  전체: {total}건 (short_term: {short}, long_term: {long}, pinned: {pinned})")
    print(f"  평균 관련성: {avg_rel:.3f}, 평균 접근: {avg_acc:.1f}회")
    print(f"  카테고리별:")
    for c, n in sorted(cats.items()):
        print(f"    {c}: {n}건")


def cmd_import_md(args):
    """기존 .md 파일 → DB 마이그레이션."""
    if not MEMORY_DIR.exists():
        print(f"❌ 메모리 디렉토리 없음: {MEMORY_DIR}")
        return

    files = sorted(MEMORY_DIR.glob("*.md"))
    files = [f for f in files if f.name != "MEMORY.md"]

    print(f"📂 마이그레이션 대상: {len(files)}개 파일")
    migrated = 0
    skipped = 0

    for f in files:
        raw = f.read_text(encoding="utf-8")

        # 이미 마이그레이션된 파일 확인
        existing = _get({
            "source_file": f"eq.{f.name}",
            "select": "id",
            "limit": "1",
        })
        if existing:
            print(f"  ⏭️ {f.name} (이미 존재)")
            skipped += 1
            continue

        # frontmatter 파싱
        title, description, mem_type, content = _parse_frontmatter(raw)

        # 카테고리 매핑
        category = _map_category(f.name, mem_type)

        # pinned 판단
        pinned = _should_pin(f.name, mem_type)

        # 임베딩
        embed_text = f"{title}\n{content[:2000]}"
        embedding = get_embedding(embed_text)
        time.sleep(0.3)  # rate limit

        data = {
            "title": title or f.stem,
            "content": content,
            "category": category,
            "memory_tier": "short_term",
            "tags": _extract_tags(f.name, content),
            "source_file": f.name,
            "pinned": pinned,
            "relevance_score": 1.0,
        }
        if embedding:
            data["embedding"] = str(embedding)

        result = _post(data)
        if result:
            pin_mark = "📌" if pinned else ""
            print(f"  ✅ {f.name} → [{category}] {title[:40]} {pin_mark}")
            migrated += 1
        else:
            print(f"  ❌ {f.name} 실패")

    print(f"\n완료: {migrated}건 마이그레이션, {skipped}건 스킵")


def _parse_frontmatter(raw: str) -> tuple[str, str, str, str]:
    """YAML frontmatter 파싱."""
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1])
                content = parts[2].strip()
                return (
                    fm.get("name", ""),
                    fm.get("description", ""),
                    fm.get("type", "project"),
                    content,
                )
            except yaml.YAMLError:
                pass
    return ("", "", "project", raw.strip())


def _map_category(filename: str, mem_type: str) -> str:
    """파일명/타입 → DB 카테고리."""
    if filename.startswith("feedback_"):
        return "feedback"
    if filename.startswith("user_"):
        return "user"
    if filename.startswith("reference_"):
        return "reference"
    if filename.startswith("known_issues"):
        return "known_issue"
    if mem_type in ("user", "feedback", "reference"):
        return mem_type
    return "project"


def _should_pin(filename: str, mem_type: str) -> bool:
    """절대 규칙 파일은 pin."""
    pinned_files = {
        "feedback_bot_terminology.md",
        "feedback_sensitive_files.md",
        "feedback_no_terminal_exit.md",
        "feedback_supabase_connection.md",
        "user_iphone_rc.md",
    }
    return filename in pinned_files


def _extract_tags(filename: str, content: str) -> list[str]:
    """파일명 + 내용에서 태그 추출."""
    tags = []
    stem = filename.replace(".md", "")
    parts = stem.split("_")
    # 첫 부분(feedback/project/user/reference) 제외
    if len(parts) > 1 and parts[0] in ("feedback", "project", "user", "reference"):
        tags.extend(parts[1:])
    else:
        tags.extend(parts)

    # 내용에서 주요 키워드 추출
    keywords = ["rc", "watchdog", "telegram", "cron", "supabase", "minirang",
                 "kimchirang", "scalping", "rl", "ml", "bug", "audit"]
    content_lower = content.lower()
    for kw in keywords:
        if kw in content_lower and kw not in tags:
            tags.append(kw)

    return tags[:10]


# ─── CLI Argument Parsing ────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Brain-Inspired Memory System")
    sub = parser.add_subparsers(dest="command")

    # store
    p_store = sub.add_parser("store", help="새 메모리 저장")
    p_store.add_argument("title")
    p_store.add_argument("content")
    p_store.add_argument("--category", "-c", default="project",
                        choices=["user", "feedback", "project", "reference", "known_issue"])
    p_store.add_argument("--tags", "-t", default="")
    p_store.add_argument("--pin", action="store_true")

    # recall
    p_recall = sub.add_parser("recall", help="시맨틱 검색")
    p_recall.add_argument("query")
    p_recall.add_argument("--limit", "-n", type=int, default=5)

    # recall-context
    p_ctx = sub.add_parser("recall-context", help="대화 컨텍스트 주입")
    p_ctx.add_argument("query", nargs="?", default="")
    p_ctx.add_argument("--limit", "-n", type=int, default=10)

    # list
    p_list = sub.add_parser("list", help="목록")
    p_list.add_argument("--tier", choices=["short_term", "long_term"])
    p_list.add_argument("--category", choices=["user", "feedback", "project", "reference", "known_issue"])
    p_list.add_argument("--limit", "-n", type=int, default=20)

    # get
    p_get = sub.add_parser("get", help="단일 조회")
    p_get.add_argument("id")

    # update
    p_update = sub.add_parser("update", help="업데이트")
    p_update.add_argument("id")
    p_update.add_argument("content", nargs="?")
    p_update.add_argument("--title")

    # delete
    p_del = sub.add_parser("delete", help="삭제")
    p_del.add_argument("id")

    # touch
    p_touch = sub.add_parser("touch", help="접근 기록")
    p_touch.add_argument("id")

    # pin/unpin
    p_pin = sub.add_parser("pin", help="고정")
    p_pin.add_argument("id")
    p_unpin = sub.add_parser("unpin", help="고정 해제")
    p_unpin.add_argument("id")

    # consolidate
    p_cons = sub.add_parser("consolidate", help="short→long 통합")
    p_cons.add_argument("--dry-run", action="store_true")

    # decay
    sub.add_parser("decay", help="관련성 감쇠")

    # stats
    sub.add_parser("stats", help="통계")

    # import-md
    sub.add_parser("import-md", help=".md → DB 마이그레이션")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    commands = {
        "store": cmd_store,
        "recall": cmd_recall,
        "recall-context": cmd_recall_context,
        "list": cmd_list,
        "get": cmd_get,
        "update": cmd_update,
        "delete": cmd_delete,
        "touch": cmd_touch,
        "pin": cmd_pin,
        "unpin": cmd_unpin,
        "consolidate": cmd_consolidate,
        "decay": cmd_decay,
        "stats": cmd_stats,
        "import-md": cmd_import_md,
    }

    fn = commands.get(args.command)
    if fn:
        fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
