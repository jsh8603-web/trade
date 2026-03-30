"""
전체 decisions 야후 매크로 삽입 + machine_name 통일 (pc36)

대상: 2024-12-31 ~ 2026-03-22 전체 decisions (4,087건+)
작업:
  1. real_macro 없는 레코드 → Yahoo Finance 실제값 삽입 + 임베딩 재생성
  2. real_macro 있는 레코드 → machine_name만 pc36으로 업데이트
  3. 전체 machine_name → "pc36" 통일
  4. RAG vectors 매크로 보강
"""

import os
import json
import re
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

import yfinance as yf
import pandas as pd
from supabase import create_client

# Gemini 임베딩
import google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
sb = create_client(SUPABASE_URL, SUPABASE_KEY)

BATCH_SIZE = 10  # Gemini 임베딩 배치
EMBED_MODEL = "models/gemini-embedding-001"
TARGET_MACHINE = "pc36"


# ─── 1. Yahoo Finance 매크로 데이터 수집 ───

def fetch_macro_data():
    """전체 기간 매크로 데이터 수집 및 날짜별 dict 생성"""
    print("[1/5] Yahoo Finance 매크로 데이터 수집...")

    tickers = {
        'sp500': '^GSPC',
        'dxy': 'DX-Y.NYB',
        'gold': 'GC=F',
        'wti': 'CL=F',
        'us10y': '^TNX'
    }

    all_data = {}
    for name, ticker in tickers.items():
        df = yf.download(ticker, start='2024-12-15', end='2026-03-23', progress=False)
        if hasattr(df.columns, 'levels'):
            df.columns = df.columns.get_level_values(0)
        all_data[name] = df
        print(f"  {name}: {len(df)}행 ({df.index[0].date()} ~ {df.index[-1].date()})")

    # 날짜별 매크로 dict 생성 (주말/공휴일은 직전 거래일 값 사용)
    macro_by_date = {}
    all_dates = pd.date_range('2024-12-15', '2026-03-22', freq='D')

    prev_values = {}
    for dt in all_dates:
        date_str = dt.strftime('%Y-%m-%d')
        entry = {}

        for name, df in all_data.items():
            mask = df.index <= dt
            if mask.any():
                row = df.loc[mask].iloc[-1]
                val = float(row['Close'])
                change_pct = 0.0
                if name in prev_values:
                    prev = prev_values[name]
                    if prev > 0:
                        change_pct = round((val - prev) / prev * 100, 2)
                prev_values[name] = val
                entry[name] = {
                    'value': round(val, 2),
                    'change_pct': change_pct
                }
            elif name in prev_values:
                entry[name] = {
                    'value': round(prev_values[name], 2),
                    'change_pct': 0.0
                }

        macro_by_date[date_str] = entry

    print(f"  날짜별 매크로 데이터: {len(macro_by_date)}일분 준비 완료")
    return macro_by_date


def compute_macro_score(macro):
    """실제 매크로 데이터 기반 점수 계산 (-20 ~ +20)"""
    score = 0

    sp = macro.get('sp500', {})
    sp_chg = sp.get('change_pct', 0)
    if sp_chg > 0.5:
        score += 5
    elif sp_chg > 0:
        score += 2
    elif sp_chg < -1.0:
        score -= 5
    elif sp_chg < -0.3:
        score -= 2

    dxy = macro.get('dxy', {})
    dxy_chg = dxy.get('change_pct', 0)
    if dxy_chg < -0.3:
        score += 4
    elif dxy_chg < 0:
        score += 1
    elif dxy_chg > 0.5:
        score -= 4
    elif dxy_chg > 0.2:
        score -= 1

    gold = macro.get('gold', {})
    gold_chg = gold.get('change_pct', 0)
    if gold_chg > 1.0:
        score += 3
    elif gold_chg > 0.3:
        score += 1
    elif gold_chg < -1.0:
        score -= 2

    wti = macro.get('wti', {})
    wti_chg = wti.get('change_pct', 0)
    if wti_chg > 2.0:
        score -= 3
    elif wti_chg < -2.0:
        score += 2

    us10y = macro.get('us10y', {})
    us10y_chg = us10y.get('change_pct', 0)
    if us10y_chg > 2.0:
        score -= 5
    elif us10y_chg > 0.5:
        score -= 2
    elif us10y_chg < -1.0:
        score += 4
    elif us10y_chg < -0.3:
        score += 2

    return max(-20, min(20, score))


def macro_sentiment(score):
    """매크로 점수 -> 감성 텍스트"""
    if score >= 8:
        return "strong_positive"
    elif score >= 3:
        return "positive"
    elif score >= -2:
        return "neutral"
    elif score >= -7:
        return "negative"
    else:
        return "strong_negative"


# ─── 2. 전체 Decisions 로드 (source 필터 없음) ───

def load_all_decisions():
    """전체 decisions 로드 (source/machine 무관)"""
    print("[2/5] Supabase에서 전체 decisions 로드...")

    all_rows = []
    offset = 0
    while True:
        r = sb.table('decisions').select(
            'id,created_at,source,machine_name,market_data_snapshot,embedding_text'
        ).order('created_at').range(offset, offset + 999).execute()

        if not r.data:
            break
        all_rows.extend(r.data)
        offset += 1000
        if len(r.data) < 1000:
            break

    # source별 통계
    from collections import Counter
    src_counts = Counter(r.get('source', '(null)') for r in all_rows)
    mn_counts = Counter(r.get('machine_name') or '(null)' for r in all_rows)

    print(f"  총 {len(all_rows)}건 로드 완료")
    print(f"  source별: {dict(src_counts.most_common())}")
    print(f"  machine_name별: {dict(mn_counts.most_common())}")

    # real_macro 유무 분류
    needs_macro = []
    has_macro = []
    for row in all_rows:
        snap = row.get('market_data_snapshot')
        if snap and 'real_macro' in str(snap):
            has_macro.append(row)
        else:
            needs_macro.append(row)

    print(f"  real_macro 필요: {len(needs_macro)}건")
    print(f"  real_macro 있음 (machine_name만 변경): {len(has_macro)}건")

    return needs_macro, has_macro


# ─── 3. 매크로 데이터 업데이트 ───

def get_macro_for_date(dt, macro_by_date):
    """날짜에 해당하는 매크로 데이터 찾기 (최대 7일 이전까지)"""
    date_str = dt.strftime('%Y-%m-%d')
    macro = macro_by_date.get(date_str)
    if not macro:
        for i in range(1, 8):
            prev_date = (dt - timedelta(days=i)).strftime('%Y-%m-%d')
            macro = macro_by_date.get(prev_date)
            if macro:
                break
    return macro, date_str


def build_macro_text(macro, macro_score, sentiment):
    """매크로 임베딩 텍스트 생성"""
    sp_val = macro.get('sp500', {}).get('value', 0)
    sp_chg = macro.get('sp500', {}).get('change_pct', 0)
    dxy_val = macro.get('dxy', {}).get('value', 0)
    dxy_chg = macro.get('dxy', {}).get('change_pct', 0)
    gold_val = macro.get('gold', {}).get('value', 0)
    gold_chg = macro.get('gold', {}).get('change_pct', 0)
    wti_val = macro.get('wti', {}).get('value', 0)
    wti_chg = macro.get('wti', {}).get('change_pct', 0)
    us10y_val = macro.get('us10y', {}).get('value', 0)

    return (
        f"매크로(실제): {sentiment} (점수 {macro_score}) | "
        f"S&P500: {sp_val:,.0f} ({sp_chg:+.1f}%) | "
        f"DXY: {dxy_val:.1f} ({dxy_chg:+.1f}%) | "
        f"금: ${gold_val:,.0f} ({gold_chg:+.1f}%) | "
        f"유가: ${wti_val:.1f} ({wti_chg:+.1f}%) | "
        f"미국채10Y: {us10y_val:.2f}%"
    )


def update_decision_macro(row, macro_by_date):
    """단일 decision의 매크로 데이터 업데이트"""
    created = row['created_at']
    if 'T' in created:
        dt = datetime.fromisoformat(created.replace('+00:00', '').replace('Z', ''))
    else:
        dt = datetime.fromisoformat(created)

    macro, date_str = get_macro_for_date(dt, macro_by_date)
    if not macro:
        return None, None

    macro_score = compute_macro_score(macro)
    sentiment = macro_sentiment(macro_score)

    # market_data_snapshot 업데이트
    snap = row.get('market_data_snapshot')
    if isinstance(snap, str):
        try:
            snap = json.loads(snap)
        except (json.JSONDecodeError, TypeError):
            snap = {}
    if not isinstance(snap, dict):
        snap = {}

    snap['real_macro'] = {
        'source': 'yahoo_finance',
        'date': date_str,
        'sp500': macro.get('sp500', {}),
        'dxy': macro.get('dxy', {}),
        'gold': macro.get('gold', {}),
        'wti': macro.get('wti', {}),
        'us10y': macro.get('us10y', {}),
        'score': macro_score,
        'sentiment': sentiment
    }

    # embedding_text 매크로 부분 교체/추가
    emb = row.get('embedding_text', '') or ''
    real_macro_text = build_macro_text(macro, macro_score, sentiment)

    # 기존 매크로 텍스트 패턴 교체 (시뮬레이션/실제 모두)
    # 패턴1: "매크로: positive (점수 16)"
    emb = re.sub(r'매크로:\s*\w+\s*\(점수\s*-?\d+\.?\d*\)', real_macro_text, emb)
    # 패턴2: "매크로(실제): positive (점수 5)" (이미 실제로 교체된 것 갱신)
    emb = re.sub(r'매크로\(실제\):\s*\w+\s*\(점수\s*-?\d+\.?\d*\)\s*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|[^|]*%', real_macro_text, emb)

    # 매크로 텍스트가 없으면 끝에 추가
    if '매크로' not in emb and 'macro' not in emb.lower():
        emb = emb.rstrip() + ' | ' + real_macro_text

    return snap, emb


def generate_embeddings_batch(texts, retries=3):
    """Gemini 임베딩 배치 생성"""
    for attempt in range(retries):
        try:
            result = genai.embed_content(
                model=EMBED_MODEL,
                content=texts,
                task_type="RETRIEVAL_DOCUMENT"
            )
            return result['embedding']
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"    임베딩 재시도 ({attempt+1}/{retries}): {e}, {wait}초 대기")
                time.sleep(wait)
            else:
                print(f"    임베딩 실패: {e}")
                return None


# ─── 4. 매크로 삽입 + 임베딩 재생성 (real_macro 없는 레코드) ───

def process_needs_macro(rows, macro_by_date):
    """real_macro 없는 레코드: 매크로 삽입 + 임베딩 재생성 + machine_name 변경"""
    print(f"[3/5] 매크로 삽입 + 임베딩 재생성 ({len(rows)}건)...")

    updates = []  # (id, snapshot_json, new_embedding_text)
    for row in rows:
        snap, emb = update_decision_macro(row, macro_by_date)
        if snap is not None:
            updates.append((row['id'], snap, emb))

    print(f"  매크로 매칭 완료: {len(updates)}건 (미매칭: {len(rows)-len(updates)}건)")

    total = len(updates)
    success = 0
    failed = 0

    for i in range(0, total, BATCH_SIZE):
        batch = updates[i:i+BATCH_SIZE]
        texts = [u[2] for u in batch]

        embeddings = generate_embeddings_batch(texts)
        if embeddings is None:
            failed += len(batch)
            print(f"  [{i+len(batch)}/{total}] 배치 임베딩 실패, 스킵")
            continue

        for j, (row_id, snap, emb) in enumerate(batch):
            try:
                sb.table('decisions').update({
                    'market_data_snapshot': json.dumps(snap, ensure_ascii=False),
                    'embedding_text': emb,
                    'state_embedding': embeddings[j],
                    'machine_name': TARGET_MACHINE
                }).eq('id', row_id).execute()
                success += 1
            except Exception as e:
                failed += 1
                if failed <= 5:
                    print(f"    DB 업데이트 실패 [{row_id[:8]}...]: {e}")

        done = i + len(batch)
        if done % 100 == 0 or done == total:
            print(f"  [{done}/{total}] 완료 (성공: {success}, 실패: {failed})")

        time.sleep(0.5)

    return success, failed


# ─── 5. machine_name만 변경 (real_macro 이미 있는 레코드) ───

def update_machine_name_only(rows):
    """real_macro 있는 레코드: machine_name만 pc36으로 업데이트"""
    print(f"[4/5] machine_name → '{TARGET_MACHINE}' 일괄 변경 ({len(rows)}건)...")

    # 이미 pc36인 것은 스킵
    needs_update = [r for r in rows if r.get('machine_name') != TARGET_MACHINE]
    already_ok = len(rows) - len(needs_update)
    print(f"  이미 pc36: {already_ok}건, 변경 필요: {len(needs_update)}건")

    success = 0
    failed = 0
    total = len(needs_update)

    # 50건씩 배치 업데이트 (임베딩 불필요, 빠름)
    for i in range(0, total, 50):
        batch = needs_update[i:i+50]
        for row in batch:
            try:
                sb.table('decisions').update({
                    'machine_name': TARGET_MACHINE
                }).eq('id', row['id']).execute()
                success += 1
            except Exception as e:
                failed += 1
                if failed <= 3:
                    print(f"    machine_name 변경 실패 [{row['id'][:8]}...]: {e}")

        done = i + len(batch)
        if done % 500 == 0 or done == total:
            print(f"  [{done}/{total}] 완료 (성공: {success}, 실패: {failed})")

    return success + already_ok, failed


# ─── 6. RAG vectors 업데이트 ───

def update_rag_vectors(macro_by_date):
    """rag_analysis_vectors의 analysis_text에도 매크로 추가 + 재임베딩"""
    print("[5/5] RAG analysis vectors 매크로 업데이트...")

    all_rag = []
    offset = 0
    while True:
        r = sb.table('rag_analysis_vectors').select(
            'id,cycle_id,analysis_text,created_at'
        ).order('created_at').range(offset, offset + 499).execute()
        if not r.data:
            break
        all_rag.extend(r.data)
        offset += 500
        if len(r.data) < 500:
            break

    print(f"  RAG vectors: {len(all_rag)}건 로드")

    if not all_rag:
        return 0, 0

    updates = []
    for row in all_rag:
        created = row.get('created_at', '')
        text = row.get('analysis_text', '')

        dt = None
        if created:
            try:
                dt = datetime.fromisoformat(created.replace('+00:00', '').replace('Z', ''))
            except Exception:
                pass

        if not dt:
            continue

        macro, _ = get_macro_for_date(dt, macro_by_date)
        if not macro:
            continue

        macro_score = compute_macro_score(macro)
        sentiment = macro_sentiment(macro_score)
        sp = macro.get('sp500', {})
        dxy = macro.get('dxy', {})
        gold = macro.get('gold', {})

        macro_append = (
            f" | 실제매크로: S&P500 {sp.get('value',0):,.0f}({sp.get('change_pct',0):+.1f}%), "
            f"DXY {dxy.get('value',0):.1f}, Gold ${gold.get('value',0):,.0f}, "
            f"매크로점수 {macro_score}({sentiment})"
        )

        # 이미 실제매크로가 있으면 스킵
        if '실제매크로' in text or 'S&P500' in text:
            continue

        new_text = text + macro_append
        updates.append((row['id'], new_text))

    print(f"  RAG 매크로 추가 대상: {len(updates)}건")

    success = 0
    failed = 0

    for i in range(0, len(updates), BATCH_SIZE):
        batch = updates[i:i+BATCH_SIZE]
        texts = [u[1] for u in batch]

        embeddings = generate_embeddings_batch(texts)
        if embeddings is None:
            failed += len(batch)
            continue

        for j, (row_id, new_text) in enumerate(batch):
            try:
                sb.table('rag_analysis_vectors').update({
                    'analysis_text': new_text,
                    'embedding': embeddings[j]
                }).eq('id', row_id).execute()
                success += 1
            except Exception as e:
                failed += 1
                if failed <= 3:
                    print(f"    RAG 업데이트 실패: {e}")

        done = i + len(batch)
        if done % 50 == 0 or done == len(updates):
            print(f"  RAG [{done}/{len(updates)}] (성공: {success}, 실패: {failed})")

        time.sleep(0.5)

    return success, failed


# ─── Main ───

def main():
    print("=" * 70)
    print("전체 decisions 야후 매크로 삽입 + machine_name 통일 (pc36)")
    print("대상: 전체 기간 / 모든 source / 모든 machine")
    print("=" * 70)

    # 1. 매크로 데이터 수집
    macro_by_date = fetch_macro_data()

    # 2. 전체 decisions 로드 및 분류
    needs_macro, has_macro = load_all_decisions()

    # 3. real_macro 없는 레코드: 매크로 삽입 + 임베딩 + machine_name
    macro_ok, macro_fail = process_needs_macro(needs_macro, macro_by_date)

    # 4. real_macro 있는 레코드: machine_name만 변경
    mn_ok, mn_fail = update_machine_name_only(has_macro)

    # 5. RAG vectors 매크로 보강
    rag_ok, rag_fail = update_rag_vectors(macro_by_date)

    # 결과 요약
    total = len(needs_macro) + len(has_macro)
    print()
    print("=" * 70)
    print("완료!")
    print(f"  전체 decisions: {total}건")
    print(f"  매크로 삽입 + 재임베딩: {macro_ok}건 성공, {macro_fail}건 실패 / {len(needs_macro)}건")
    print(f"  machine_name 통일: {mn_ok}건 성공, {mn_fail}건 실패 / {len(has_macro)}건")
    print(f"  RAG Vectors: {rag_ok}건 성공, {rag_fail}건 실패")
    print(f"  machine_name: 전체 → '{TARGET_MACHINE}'")
    print("=" * 70)


if __name__ == '__main__':
    main()
