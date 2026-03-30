#!/usr/bin/env python3
"""
Brain-Inspired Memory System — 인간 뇌 기억 구조 모방

4-tier (인간 뇌 대응):
  해마 인덱스 = data/.memory_index.json (로컬, 제목/태그만, 0.01초 검색)
  working    = MEMORY.md (항상 로드, ~40줄 핵심만)
  short_term = DB (최근 7일, 상세, 자주 접근)
  long_term  = DB (7일+, 압축/병합, 필요 시 리콜)

속도 설계:
  recall/recall-context → 먼저 로컬 인덱스 키워드 매칭 (0.01초)
                        → 못 찾으면 DB 시맨틱 검색 (fallback, ~5초)
  store/update/delete   → DB 저장 + 로컬 인덱스 자동 갱신

사용법:
  python3 scripts/memory.py recall "검색어"              # 빠른 검색 (로컬 우선)
  python3 scripts/memory.py recall --deep "검색어"       # 시맨틱 검색 강제
  python3 scripts/memory.py recall-context "작업내용"    # 대화 시작 컨텍스트
  python3 scripts/memory.py store "제목" "내용" -c project -t tag1,tag2
  python3 scripts/memory.py list [--tier short_term] [--category feedback]
  python3 scripts/memory.py get <id>                     # 상세 조회 (DB에서 content)
  python3 scripts/memory.py update <id> "새 내용" [--title "새 제목"]
  python3 scripts/memory.py delete <id>
  python3 scripts/memory.py touch <id>                   # access_count 증가
  python3 scripts/memory.py pin <id> / unpin <id>
  python3 scripts/memory.py consolidate [--dry-run]      # short→long 압축
  python3 scripts/memory.py decay                        # 관련성 감쇠
  python3 scripts/memory.py stats                        # 통계
  python3 scripts/memory.py sync-index                   # 로컬 인덱스 강제 동기화
  python3 scripts/memory.py import-md                    # .md 파일 → DB 마이그레이션
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
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
KST = timezone(timedelta(hours=9))
TABLE = "claude_memories"

MEMORY_DIR = Path.home() / ".claude" / "projects" / "-Users-drj00-workspace-blockchain" / "memory"
INDEX_FILE = PROJECT_ROOT / "data" / ".memory_index.json"


# ═══════════════════════════════════════════════════════════════════════════════
# 해마 인덱스 (Hippocampus Index) — 로컬 JSON 캐시
# 제목/태그/카테고리/요약만 저장. content/embedding 없음 → 초고속 검색
# ═══════════════════════════════════════════════════════════════════════════════

def _load_index() -> list[dict]:
    """로컬 인덱스 로드 (없으면 빈 리스트)."""
    if INDEX_FILE.exists():
        try:
            return json.loads(INDEX_FILE.read_text())
        except (json.JSONDecodeError, IOError):
            pass
    return []


def _save_index(index: list[dict]):
    """로컬 인덱스 저장."""
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=1))


def _index_entry(row: dict) -> dict:
    """DB row → 인덱스 엔트리 (경량)."""
    return {
        "id": row["id"],
        "t": row.get("title", ""),        # title
        "c": row.get("category", ""),      # category
        "tier": row.get("memory_tier", "short_term"),
        "tags": row.get("tags") or [],
        "pin": row.get("pinned", False),
        "rel": row.get("relevance_score", 1.0),
        "acc": row.get("access_count", 0),
        "sum": row.get("summary") or "",   # summary (있으면)
        "ts": (row.get("created_at") or "")[:10],  # 날짜만
    }


def _update_index_entry(mem_id: str, entry: dict):
    """인덱스에서 특정 항목 업데이트/추가."""
    index = _load_index()
    for i, e in enumerate(index):
        if e["id"] == mem_id:
            index[i] = entry
            _save_index(index)
            return
    index.append(entry)
    _save_index(index)


def _remove_from_index(mem_id: str):
    """인덱스에서 항목 제거."""
    index = _load_index()
    index = [e for e in index if e["id"] != mem_id]
    _save_index(index)


def _search_index(query: str, limit: int = 5) -> list[dict]:
    """로컬 인덱스에서 키워드 검색 (초고속).

    검색 대상: title, tags, summary, category
    스코어링: 제목 매칭 3점 + 태그 정확 매칭 5점 + 요약 매칭 1점 + pinned 보너스 2점
    """
    index = _load_index()
    if not index:
        return []

    query_lower = query.lower()
    tokens = query_lower.split()
    results = []

    for entry in index:
        score = 0.0
        title_lower = entry["t"].lower()
        tags_lower = [t.lower() for t in entry.get("tags", [])]
        summary_lower = entry.get("sum", "").lower()

        for token in tokens:
            if token in title_lower:
                score += 3.0
            if token in tags_lower:
                score += 5.0
            elif any(token in tag for tag in tags_lower):
                score += 2.0
            if token in summary_lower:
                score += 1.0

        # pinned 보너스
        if entry.get("pin"):
            score += 2.0
        # relevance 가중
        score *= entry.get("rel", 1.0)

        if score > 0:
            results.append((score, entry))

    results.sort(key=lambda x: -x[0])
    return [r[1] for r in results[:limit]]


def sync_index():
    """DB에서 전체 인덱스 동기화."""
    rows = _get({
        "select": "id,title,category,memory_tier,tags,pinned,relevance_score,access_count,summary,created_at",
        "order": "created_at.desc",
    })
    if rows is None:
        print("❌ DB 조회 실패", file=sys.stderr)
        return
    index = [_index_entry(r) for r in rows]
    _save_index(index)
    return len(index)


# ═══════════════════════════════════════════════════════════════════════════════
# Supabase REST helpers
# ═══════════════════════════════════════════════════════════════════════════════

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


def _delete_db(mem_id: str) -> bool:
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


# ═══════════════════════════════════════════════════════════════════════════════
# Gemini Embedding (느림 — fallback 전용)
# ═══════════════════════════════════════════════════════════════════════════════

def get_embedding(text: str) -> list | None:
    """Gemini embedding-001 (3072d). store 시에만 호출."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text[:8000],
            task_type="retrieval_document",
        )
        return result["embedding"]
    except Exception as e:
        print(f"[memory] 임베딩 생성 실패: {e}", file=sys.stderr)
        return None


def get_query_embedding(text: str) -> list | None:
    """쿼리용 임베딩 (느림, --deep 전용)."""
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


# ═══════════════════════════════════════════════════════════════════════════════
# Commands
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_store(args):
    """새 메모리 저장."""
    title = args.title
    content = args.content
    category = args.category or "project"
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
    pinned = args.pin

    # 임베딩 생성 (store는 백그라운드 품질 — 느려도 OK)
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
        # 로컬 인덱스 즉시 갱신
        _update_index_entry(result["id"], _index_entry(result))
        print(f"✅ 저장: {result.get('id', '?')[:8]}.. [{category}] {title}")
    else:
        print("❌ 저장 실패", file=sys.stderr)


def cmd_recall(args):
    """2단계 검색: 로컬 인덱스 → (fallback) DB 시맨틱."""
    query = args.query
    limit = args.limit or 5
    deep = args.deep

    # ── 1단계: 로컬 인덱스 키워드 검색 (즉시) ──
    if not deep:
        local_results = _search_index(query, limit)
        if local_results:
            # 로컬에서 찾음 → ID로 DB에서 content만 가져오기 (1회 조회)
            ids = [r["id"] for r in local_results]
            id_filter = ",".join(ids)
            db_rows = _get({
                "id": f"in.({id_filter})",
                "select": "id,memory_tier,category,title,summary,content,tags,relevance_score,pinned,access_count",
            })

            if db_rows:
                # ID 순서 보존
                db_map = {r["id"]: r for r in db_rows}
                merged = [db_map[rid] for rid in ids if rid in db_map]

                # access_count 일괄 갱신 (비동기 느낌으로 1회만)
                _batch_touch(ids)

                _print_recall_results(merged, limit)
                return

    # ── 2단계: DB 시맨틱 검색 (느림, fallback) ──
    print("🔍 시맨틱 검색 중...", file=sys.stderr)
    embedding = get_query_embedding(query)
    semantic_results = []
    if embedding:
        semantic_results = _rpc("match_similar_memories", {
            "query_embedding": str(embedding),
            "match_limit": limit,
        })

    if semantic_results:
        _batch_touch([r["id"] for r in semantic_results])
        _print_recall_results(semantic_results, limit)
    else:
        print(f"검색 결과 없음: '{query}'")


def cmd_recall_context(args):
    """대화 시작 컨텍스트 주입 — 로컬 인덱스 기반 (초고속)."""
    query = args.query
    limit = args.limit or 10

    index = _load_index()
    if not index:
        # 인덱스 없으면 동기화 먼저
        n = sync_index()
        print(f"(인덱스 동기화: {n}건)", file=sys.stderr)
        index = _load_index()

    # 1) pinned 항목 (항상 포함)
    pinned_entries = [e for e in index if e.get("pin")]

    # 2) 최근 7일 항목
    week_ago = (datetime.now(KST) - timedelta(days=7)).strftime("%Y-%m-%d")
    recent_entries = [e for e in index if e.get("ts", "") >= week_ago and not e.get("pin")]
    recent_entries.sort(key=lambda e: e.get("ts", ""), reverse=True)
    recent_entries = recent_entries[:5]

    # 3) 쿼리 관련 (키워드 매칭)
    query_entries = []
    if query:
        query_entries = _search_index(query, limit)
        # pinned/recent와 중복 제거
        seen = {e["id"] for e in pinned_entries + recent_entries}
        query_entries = [e for e in query_entries if e["id"] not in seen]

    # 4) content가 필요한 항목만 DB에서 가져오기 (1회 조회)
    all_ids = [e["id"] for e in pinned_entries + recent_entries + query_entries]
    if not all_ids:
        print("(리콜된 메모리 없음)")
        return

    db_rows = _get({
        "id": f"in.({','.join(all_ids)})",
        "select": "id,title,content,summary,category,pinned,tags",
    })
    db_map = {r["id"]: r for r in (db_rows or [])}

    # 5) 출력
    print("# 리콜된 메모리")
    print()

    if pinned_entries:
        print("## 📌 핵심 규칙")
        for e in pinned_entries:
            r = db_map.get(e["id"], {})
            text = _compact(r.get("content", e.get("sum", "")))
            print(f"- **{e['t']}**: {text}")
        print()

    other = recent_entries + query_entries
    if other:
        print("## 관련 컨텍스트")
        for e in other[:limit]:
            r = db_map.get(e["id"], {})
            text = r.get("summary") or _compact(r.get("content", e.get("sum", "")))
            print(f"- [{e['c']}] **{e['t']}**: {text}")
        print()

    # access_count 일괄 갱신
    _batch_touch(all_ids)


def _batch_touch(ids: list[str]):
    """여러 메모리의 access_count를 한 번에 갱신 (비동기)."""
    import requests
    now = datetime.now(timezone.utc).isoformat()
    for mid in ids[:10]:  # 최대 10건만 갱신 (속도 보호)
        try:
            requests.patch(
                f"{SUPABASE_URL}/rest/v1/{TABLE}?id=eq.{mid}",
                headers=_headers(),
                json={"last_accessed": now},
                timeout=3,
            )
        except Exception:
            pass  # touch 실패는 무시


def _print_recall_results(rows: list, limit: int):
    """recall 결과 출력."""
    for r in rows[:limit]:
        # sim = r.get("similarity", 0)  # available but unused in display
        tier = "🟢" if r.get("memory_tier") == "short_term" else "🔵"
        pin = "📌" if r.get("pinned") else ""
        cat = r.get("category", "?")[:4]
        score = r.get("relevance_score", 0)
        print(f"{tier}{pin} [{cat}] {r.get('title', '')}")
        text = r.get("summary") or (r.get("content", "")[:150] + "...")
        print(f"   {text}")
        print(f"   rel={score:.2f} acc={r.get('access_count', 0)} id={r['id'][:8]}")
        print()


def _compact(text: str, max_len: int = 200) -> str:
    """멀티라인 → 1줄 요약."""
    text = text.replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) > max_len:
        text = text[:max_len] + "..."
    return text


def cmd_list(args):
    """메모리 목록 (로컬 인덱스 사용)."""
    index = _load_index()
    if not index:
        n = sync_index()
        print(f"(인덱스 동기화: {n}건)", file=sys.stderr)
        index = _load_index()

    if args.tier:
        index = [e for e in index if e.get("tier") == args.tier]
    if args.category:
        index = [e for e in index if e.get("c") == args.category]

    # relevance 내림차순
    index.sort(key=lambda e: (-e.get("rel", 0), -e.get("acc", 0)))
    index = index[:args.limit or 20]

    if not index:
        print("메모리 없음")
        return

    for e in index:
        tier = "🟢" if e.get("tier") == "short_term" else "🔵"
        pin = "📌" if e.get("pin") else "  "
        print(f"{tier}{pin} [{e['c'][:4]}] {e['t'][:45]:<45} rel={e.get('rel',0):.2f} acc={e.get('acc',0):>3} {e.get('ts','')}  {e['id'][:8]}")


def cmd_get(args):
    """단일 메모리 조회 (DB에서 전체 content)."""
    row = _get({"id": f"eq.{args.id}", "select": "*"}, single=True)
    if not row:
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
    print("─" * 60)
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

    if "content" in data or "title" in data:
        row = _get({"id": f"eq.{args.id}", "select": "title,content"}, single=True)
        if row:
            t = args.title or row["title"]
            c = args.content or row["content"]
            emb = get_embedding(f"{t}\n{c[:2000]}")
            if emb:
                data["embedding"] = str(emb)

    if _patch(args.id, data):
        # 인덱스 갱신
        updated = _get({"id": f"eq.{args.id}", "select": "id,title,category,memory_tier,tags,pinned,relevance_score,access_count,summary,created_at"}, single=True)
        if updated:
            _update_index_entry(args.id, _index_entry(updated))
        print(f"✅ 업데이트: {args.id[:8]}")
    else:
        print(f"❌ 실패: {args.id[:8]}")


def cmd_delete(args):
    """메모리 삭제."""
    if _delete_db(args.id):
        _remove_from_index(args.id)
        print(f"🗑️ 삭제: {args.id[:8]}")
    else:
        print(f"❌ 실패: {args.id[:8]}")


def cmd_touch(args):
    """access_count 증가."""
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
    # 인덱스 갱신
    index = _load_index()
    for e in index:
        if e["id"] == args.id:
            e["pin"] = True
            break
    _save_index(index)
    print(f"📌 pinned: {args.id[:8]}")


def cmd_unpin(args):
    _patch(args.id, {"pinned": False})
    index = _load_index()
    for e in index:
        if e["id"] == args.id:
            e["pin"] = False
            break
    _save_index(index)
    print(f"📌 unpinned: {args.id[:8]}")


def cmd_consolidate(args):
    """short_term → long_term 압축."""
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
        lines = mem["content"].strip().split("\n")
        summary = " ".join(line.strip() for line in lines[:3] if line.strip())[:300]

        if args.dry_run:
            print(f"  [DRY] {mem['title'][:40]} → long_term")
            continue

        _patch(mem["id"], {
            "memory_tier": "long_term",
            "summary": summary,
            "consolidated_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        # 인덱스 갱신
        _update_index_entry(mem["id"], {
            "id": mem["id"], "t": mem["title"], "c": mem["category"],
            "tier": "long_term", "tags": mem.get("tags", []),
            "pin": False, "rel": mem.get("relevance_score", 0),
            "acc": mem.get("access_count", 0), "sum": summary,
            "ts": "",
        })
        print(f"  ✅ {mem['title'][:40]} → long_term")

    if args.dry_run:
        print("\n(dry run — --dry-run 제거하여 실행)")


def cmd_decay(args):
    """관련성 감쇠."""
    _rpc("decay_memory_relevance", {})
    # 인덱스 재동기화 (decay 후 점수 변경)
    n = sync_index()
    print(f"✅ decay 완료 (인덱스 동기화: {n}건)")


def cmd_stats(args):
    """통계 (로컬 인덱스 사용)."""
    index = _load_index()
    if not index:
        n = sync_index()
        index = _load_index()

    if not index:
        print("메모리 없음")
        return

    total = len(index)
    short = sum(1 for e in index if e.get("tier") == "short_term")
    long = sum(1 for e in index if e.get("tier") == "long_term")
    pinned = sum(1 for e in index if e.get("pin"))
    avg_rel = sum(e.get("rel", 0) for e in index) / total
    avg_acc = sum(e.get("acc", 0) for e in index) / total

    cats = {}
    for e in index:
        c = e.get("c", "?")
        cats[c] = cats.get(c, 0) + 1

    print("📊 메모리 통계")
    print(f"  전체: {total}건 (short_term: {short}, long_term: {long}, pinned: {pinned})")
    print(f"  평균 관련성: {avg_rel:.3f}, 평균 접근: {avg_acc:.1f}회")
    print(f"  인덱스 파일: {INDEX_FILE} ({INDEX_FILE.stat().st_size} bytes)")
    print("  카테고리별:")
    for c, n in sorted(cats.items()):
        print(f"    {c}: {n}건")


def cmd_sync_index(args):
    """로컬 인덱스 강제 동기화."""
    n = sync_index()
    print(f"✅ 인덱스 동기화: {n}건 ({INDEX_FILE})")


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

        existing = _get({"source_file": f"eq.{f.name}", "select": "id", "limit": "1"})
        if existing:
            print(f"  ⏭️ {f.name} (이미 존재)")
            skipped += 1
            continue

        title, description, mem_type, content = _parse_frontmatter(raw)
        category = _map_category(f.name, mem_type)
        pinned = _should_pin(f.name, mem_type)

        embed_text = f"{title}\n{content[:2000]}"
        embedding = get_embedding(embed_text)
        time.sleep(0.3)

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
            _update_index_entry(result["id"], _index_entry(result))
            pin_mark = "📌" if pinned else ""
            print(f"  ✅ {f.name} → [{category}] {title[:40]} {pin_mark}")
            migrated += 1
        else:
            print(f"  ❌ {f.name} 실패")

    print(f"\n완료: {migrated}건 마이그레이션, {skipped}건 스킵")


def _parse_frontmatter(raw: str) -> tuple[str, str, str, str]:
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1])
                content = parts[2].strip()
                return (fm.get("name", ""), fm.get("description", ""), fm.get("type", "project"), content)
            except yaml.YAMLError:
                pass
    return ("", "", "project", raw.strip())


def _map_category(filename: str, mem_type: str) -> str:
    if filename.startswith("feedback_"): return "feedback"
    if filename.startswith("user_"): return "user"
    if filename.startswith("reference_"): return "reference"
    if filename.startswith("known_issues"): return "known_issue"
    if mem_type in ("user", "feedback", "reference"): return mem_type
    return "project"


def _should_pin(filename: str, mem_type: str) -> bool:
    return filename in {
        "feedback_bot_terminology.md", "feedback_sensitive_files.md",
        "feedback_no_terminal_exit.md", "feedback_supabase_connection.md",
        "user_iphone_rc.md",
    }


def _extract_tags(filename: str, content: str) -> list[str]:
    tags = []
    stem = filename.replace(".md", "")
    parts = stem.split("_")
    if len(parts) > 1 and parts[0] in ("feedback", "project", "user", "reference"):
        tags.extend(parts[1:])
    else:
        tags.extend(parts)

    keywords = ["rc", "watchdog", "telegram", "cron", "supabase", "minirang",
                 "kimchirang", "scalping", "rl", "ml", "bug", "audit"]
    content_lower = content.lower()
    for kw in keywords:
        if kw in content_lower and kw not in tags:
            tags.append(kw)
    return tags[:10]


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Brain-Inspired Memory System")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("store")
    p.add_argument("title"); p.add_argument("content")
    p.add_argument("--category", "-c", default="project",
                   choices=["user", "feedback", "project", "reference", "known_issue"])
    p.add_argument("--tags", "-t", default=""); p.add_argument("--pin", action="store_true")

    p = sub.add_parser("recall")
    p.add_argument("query"); p.add_argument("--limit", "-n", type=int, default=5)
    p.add_argument("--deep", action="store_true", help="시맨틱 검색 강제")

    p = sub.add_parser("recall-context")
    p.add_argument("query", nargs="?", default="")
    p.add_argument("--limit", "-n", type=int, default=10)

    p = sub.add_parser("list")
    p.add_argument("--tier", choices=["short_term", "long_term"])
    p.add_argument("--category", choices=["user", "feedback", "project", "reference", "known_issue"])
    p.add_argument("--limit", "-n", type=int, default=20)

    p = sub.add_parser("get"); p.add_argument("id")
    p = sub.add_parser("update"); p.add_argument("id"); p.add_argument("content", nargs="?"); p.add_argument("--title")
    p = sub.add_parser("delete"); p.add_argument("id")
    p = sub.add_parser("touch"); p.add_argument("id")
    p = sub.add_parser("pin"); p.add_argument("id")
    p = sub.add_parser("unpin"); p.add_argument("id")

    p = sub.add_parser("consolidate"); p.add_argument("--dry-run", action="store_true")
    sub.add_parser("decay")
    sub.add_parser("stats")
    sub.add_parser("sync-index")
    sub.add_parser("import-md")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    commands = {
        "store": cmd_store, "recall": cmd_recall, "recall-context": cmd_recall_context,
        "list": cmd_list, "get": cmd_get, "update": cmd_update,
        "delete": cmd_delete, "touch": cmd_touch, "pin": cmd_pin, "unpin": cmd_unpin,
        "consolidate": cmd_consolidate, "decay": cmd_decay, "stats": cmd_stats,
        "sync-index": cmd_sync_index, "import-md": cmd_import_md,
    }

    fn = commands.get(args.command)
    if fn:
        fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
