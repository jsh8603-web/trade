#!/usr/bin/env python3
"""
2018~2021 decisions 테이블 백필 스크립트

sim_data_points.json + embedding_vectors.json을 읽어서
에이전트 매매 로직을 시뮬레이션하고, Supabase decisions 테이블에 백필한다.

- 매 4시간봉마다 매수/매도/관망 결정을 시뮬레이션
- 1h/4h/24h 후 가격으로 outcome 자동 계산
- Gemini 3072d 임베딩 포함
- source='backfill', dry_run=true, machine_name='backfill'

사용법:
  python scripts/backfill_decisions_2018_2021.py --year 2018
  python scripts/backfill_decisions_2018_2021.py --all
  python scripts/backfill_decisions_2018_2021.py --all --dry-run  # DB 저장 안 함
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

# ── UTF-8 출력 설정 ──
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
load_dotenv(PROJECT_DIR / ".env", override=True)

KST = timezone(timedelta(hours=9))

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

VALID_YEARS = [2017, 2018, 2019, 2020, 2021]

# ── 매매 시뮬레이션 파라미터 (에이전트 로직 기반) ──
# Moderate agent 기준: buy_threshold=50, tp=+10%, sl=-5%
BUY_THRESHOLD = 50
SELL_TP_PCT = 10.0
SELL_SL_PCT = -5.0


def calc_buy_score(dp: dict) -> tuple[int, str]:
    """에이전트 base_agent.py의 점수제 매수 로직을 시뮬레이션한다.
    Returns (score, reason_text)."""
    ind = dp["indicators"]
    fgi = dp["fgi"]
    ext = dp["external"]
    macro = dp.get("macro", {})

    score = 0
    reasons = []

    rsi = ind["rsi_14"]
    sma_dev = ind["sma_deviation_pct"]
    change_24h = ind["price_change_24h"]
    fgi_val = fgi["value"]
    fusion = ext["fusion"]
    news = ext["news"]
    whale = ext["whale"]
    binance = ext["binance"]

    # RSI 기반 (최대 25점)
    if rsi < 30:
        score += 25
        reasons.append(f"RSI 극과매도({rsi:.0f})")
    elif rsi < 40:
        score += 15
        reasons.append(f"RSI 과매도({rsi:.0f})")
    elif rsi < 50:
        score += 5
        reasons.append(f"RSI 중립하단({rsi:.0f})")
    elif rsi > 70:
        score -= 15
        reasons.append(f"RSI 과매수({rsi:.0f})")

    # FGI 기반 (최대 20점)
    if fgi_val <= 20:
        score += 20
        reasons.append(f"극공포(FGI {fgi_val})")
    elif fgi_val <= 35:
        score += 10
        reasons.append(f"공포(FGI {fgi_val})")
    elif fgi_val >= 75:
        score -= 10
        reasons.append(f"탐욕(FGI {fgi_val})")

    # SMA 이탈 (최대 15점)
    if sma_dev < -5:
        score += 15
        reasons.append(f"SMA20 대폭 하회({sma_dev:+.1f}%)")
    elif sma_dev < -2:
        score += 10
        reasons.append(f"SMA20 하회({sma_dev:+.1f}%)")
    elif sma_dev > 5:
        score -= 10
        reasons.append(f"SMA20 대폭 상회({sma_dev:+.1f}%)")

    # 24h 변동 (최대 10점)
    if change_24h < -5:
        score += 10
        reasons.append(f"24h 급락({change_24h:+.1f}%)")
    elif change_24h < -2:
        score += 5
        reasons.append(f"24h 하락({change_24h:+.1f}%)")
    elif change_24h > 5:
        score -= 5
        reasons.append(f"24h 급등({change_24h:+.1f}%)")

    # Data Fusion (최대 20점)
    fusion_bonus = fusion.get("strategy_bonus", 0)
    score += fusion_bonus
    if fusion_bonus != 0:
        reasons.append(f"Fusion {fusion['signal']}({fusion_bonus:+d})")

    # 뉴스 감성 (최대 5점)
    if news["score"] > 0.3:
        score += 5
        reasons.append("뉴스 긍정")
    elif news["score"] < -0.3:
        score -= 5
        reasons.append("뉴스 부정")

    # 고래 동향 (최대 5점)
    if whale["direction"] == "bullish":
        score += 5
        reasons.append("고래 매수")
    elif whale["direction"] == "bearish":
        score -= 5
        reasons.append("고래 매도")

    # 매크로 (최대 5점)
    macro_score = macro.get("score", 0)
    if macro_score >= 5:
        score += 5
        reasons.append(f"매크로 우호({macro_score:+d})")
    elif macro_score <= -5:
        score -= 5
        reasons.append(f"매크로 불리({macro_score:+d})")

    # 김치프리미엄 (최대 5점)
    kimchi = binance.get("kimchi_premium_pct", 0)
    if kimchi < -1:
        score += 5
        reasons.append(f"김프 할인({kimchi:+.1f}%)")
    elif kimchi > 3:
        score -= 5
        reasons.append(f"김프 과열({kimchi:+.1f}%)")

    score = max(0, min(100, score))
    return score, ", ".join(reasons) if reasons else "특이사항 없음"


def simulate_decisions(data_points: list[dict]) -> list[dict]:
    """전체 데이터 포인트에 대해 매매 결정을 시뮬레이션한다."""
    decisions = []
    holding = False
    entry_price = 0
    # entry_idx tracking removed (unused)

    for i, dp in enumerate(data_points):
        ind = dp["indicators"]
        price = ind["current_price"]
        rsi = ind["rsi_14"]
        buy_score, reason_parts = calc_buy_score(dp)

        if holding:
            # 보유 중 - 매도 판단
            pnl_pct = (price - entry_price) / entry_price * 100
            if pnl_pct >= SELL_TP_PCT:
                decision = "매도"
                confidence = min(0.95, 0.7 + pnl_pct * 0.01)
                reason = f"익절({pnl_pct:+.1f}%), {reason_parts}"
                holding = False
            elif pnl_pct <= SELL_SL_PCT:
                decision = "매도"
                confidence = 0.8
                reason = f"손절({pnl_pct:+.1f}%), {reason_parts}"
                holding = False
            elif rsi > 80 and pnl_pct > 3:
                decision = "매도"
                confidence = 0.65
                reason = f"RSI 과매수 익절({pnl_pct:+.1f}%), {reason_parts}"
                holding = False
            else:
                decision = "관망"
                confidence = 0.5
                reason = f"보유 중(PnL {pnl_pct:+.1f}%), {reason_parts}"
        else:
            # 미보유 - 매수 판단
            if buy_score >= BUY_THRESHOLD:
                decision = "매수"
                confidence = min(0.95, buy_score / 100)
                reason = f"매수점수 {buy_score}점, {reason_parts}"
                holding = True
                entry_price = price
            else:
                decision = "관망"
                confidence = max(0.3, 1.0 - buy_score / 100)
                reason = f"매수점수 {buy_score}점(기준 미달), {reason_parts}"

        decisions.append({
            "index": i,
            "decision": decision,
            "confidence": round(confidence, 2),
            "reason": reason,
            "buy_score": buy_score,
        })

    return decisions


def calc_outcomes(data_points: list[dict], idx: int) -> dict:
    """1h/4h/24h 후 가격과 outcome을 계산한다."""
    price = data_points[idx]["indicators"]["current_price"]
    # decision will be set by caller
    result = {}

    # 4시간봉 기준: 1h 후 = 없음(근사치로 다음봉의 중간), 4h = +1봉, 24h = +6봉
    # 실제로는 4h봉이므로 1h 후 가격은 근사 (현재봉과 다음봉의 가중평균)
    n = len(data_points)

    # 1h 후 (4h봉이므로 다음봉과 현재봉의 25% 지점 근사)
    if idx + 1 < n:
        next_price = data_points[idx + 1]["indicators"]["current_price"]
        price_1h = int(price * 0.75 + next_price * 0.25)
        result["price_1h_after"] = price_1h
        result["outcome_1h_pct"] = round((price_1h - price) / price * 100, 3)
    else:
        result["price_1h_after"] = None
        result["outcome_1h_pct"] = None

    # 4h 후 = 다음 봉
    if idx + 1 < n:
        price_4h = int(data_points[idx + 1]["indicators"]["current_price"])
        result["price_4h_after"] = price_4h
        result["outcome_4h_pct"] = round((price_4h - price) / price * 100, 3)
    else:
        result["price_4h_after"] = None
        result["outcome_4h_pct"] = None

    # 24h 후 = 6봉 뒤
    if idx + 6 < n:
        price_24h = int(data_points[idx + 6]["indicators"]["current_price"])
        result["price_24h_after"] = price_24h
        result["outcome_24h_pct"] = round((price_24h - price) / price * 100, 3)
    else:
        result["price_24h_after"] = None
        result["outcome_24h_pct"] = None

    return result


def calc_was_correct(decision: str, outcome_pct: float | None) -> bool | None:
    """결정이 올바랐는지 판단한다."""
    if outcome_pct is None:
        return None
    if decision == "매수":
        return outcome_pct > 0
    elif decision == "매도":
        return outcome_pct < 0
    else:  # 관망
        return abs(outcome_pct) < 2  # 2% 이내면 관망이 맞았음


def store_decisions_batch(decisions_batch: list[dict]) -> tuple[int, int]:
    """Supabase decisions 테이블에 배치 저장한다."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return 0, len(decisions_batch)

    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    ok = 0
    fail = 0

    # 50개씩 배치
    batch_size = 50
    for start in range(0, len(decisions_batch), batch_size):
        batch = decisions_batch[start:start + batch_size]
        try:
            resp = requests.post(
                f"{SUPABASE_URL}/rest/v1/decisions",
                headers=headers,
                json=batch,
                timeout=30,
            )
            if resp.status_code in (200, 201):
                ok += len(batch)
            else:
                print(f"  ! Supabase 배치 실패 (HTTP {resp.status_code}): {resp.text[:200]}")
                fail += len(batch)
        except Exception as e:
            print(f"  ! Supabase 배치 오류: {e}")
            fail += len(batch)

    return ok, fail


def backfill_year(year: int, dry_run: bool = False):
    """1개 연도의 decisions을 백필한다."""
    data_dir = PROJECT_DIR / "data" / f"historical_{year}"
    points_path = data_dir / "sim_data_points.json"
    vectors_path = data_dir / "embedding_vectors.json"

    if not points_path.exists():
        print(f"ERROR: {points_path} 없음 - collect_2018_2021_data.py를 먼저 실행하세요")
        return

    t0 = time.time()
    print(f"\n{'='*60}")
    print(f"  {year}년 decisions 백필 시작")
    print(f"  데이터: {data_dir}")
    print(f"  dry_run: {dry_run}")
    print(f"{'='*60}\n")

    # 1) 데이터 로드
    print("[1/4] 데이터 로드 중...")
    with open(points_path, "r", encoding="utf-8") as f:
        data_points = json.load(f)
    print(f"  sim_data_points: {len(data_points)}개")

    # 임베딩 벡터 로드 (있으면)
    embedding_map = {}
    if vectors_path.exists():
        with open(vectors_path, "r", encoding="utf-8") as f:
            vectors = json.load(f)
        for v in vectors:
            embedding_map[v["seq"]] = v["embedding"]
        print(f"  embedding_vectors: {len(embedding_map)}개")
    else:
        print("  embedding_vectors: 없음 (임베딩 없이 진행)")

    # 2) 매매 결정 시뮬레이션
    print("[2/4] 매매 결정 시뮬레이션 중...")
    sim_decisions = simulate_decisions(data_points)

    buy_count = sum(1 for d in sim_decisions if d["decision"] == "매수")
    sell_count = sum(1 for d in sim_decisions if d["decision"] == "매도")
    hold_count = sum(1 for d in sim_decisions if d["decision"] == "관망")
    print(f"  매수: {buy_count}, 매도: {sell_count}, 관망: {hold_count}")

    # 3) decisions 레코드 생성
    print("[3/4] decisions 레코드 생성 중...")
    records = []
    for i, (dp, dec) in enumerate(zip(data_points, sim_decisions)):
        ind = dp["indicators"]
        fgi = dp["fgi"]
        price = int(ind["current_price"])
        dt_str = dp["datetime"]

        # outcome 계산
        outcomes = calc_outcomes(data_points, i)

        # was_correct 계산
        was_correct_1h = calc_was_correct(dec["decision"], outcomes["outcome_1h_pct"])
        was_correct_4h = calc_was_correct(dec["decision"], outcomes["outcome_4h_pct"])
        was_correct_24h = calc_was_correct(dec["decision"], outcomes["outcome_24h_pct"])

        record = {
            "market": "KRW-BTC",
            "decision": dec["decision"],
            "confidence": dec["confidence"],
            "reason": dec["reason"],
            "fear_greed_value": fgi["value"],
            "rsi_value": ind["rsi_14"],
            "current_price": price,
            "sma20_price": int(ind["sma_20"]),
            "executed": False,
            "created_at": dt_str,
            "cycle_id": f"hist_{year}_{dp['seq']:04d}_{dp['date'].replace('-', '')}",
            "source": "backfill",
            "dry_run": True,
            "machine_name": "backfill",
            # outcome tracking
            "price_1h_after": outcomes["price_1h_after"],
            "price_4h_after": outcomes["price_4h_after"],
            "price_24h_after": outcomes["price_24h_after"],
            "outcome_1h_pct": outcomes["outcome_1h_pct"],
            "outcome_4h_pct": outcomes["outcome_4h_pct"],
            "outcome_24h_pct": outcomes["outcome_24h_pct"],
            "was_correct_1h": was_correct_1h,
            "was_correct_4h": was_correct_4h,
            "was_correct_24h": was_correct_24h,
            "aftermath_updated_at": dt_str,
            # embedding
            "embedding_text": dp.get("embedding_text", ""),
        }

        # 임베딩 벡터 (있으면)
        seq = dp["seq"]
        if seq in embedding_map:
            record["state_embedding"] = json.dumps(embedding_map[seq])

        # market_data_snapshot (축약 JSON)
        snapshot = {
            "price": price,
            "rsi": ind["rsi_14"],
            "sma20": ind["sma_20"],
            "sma_dev": ind["sma_deviation_pct"],
            "change_24h": ind["price_change_24h"],
            "fgi": fgi["value"],
            "regime": dp.get("market_regime", ""),
            "fusion": dp["external"]["fusion"]["signal"],
            "fusion_score": dp["external"]["fusion"]["score"],
            "macro_score": dp["macro"]["score"],
            "buy_score": dec["buy_score"],
        }
        record["market_data_snapshot"] = json.dumps(snapshot, ensure_ascii=False)

        records.append(record)

    print(f"  {len(records)}개 레코드 생성 완료")

    # 정확도 통계
    correct_counts = {"1h": 0, "4h": 0, "24h": 0}
    total_counts = {"1h": 0, "4h": 0, "24h": 0}
    for r in records:
        for period in ["1h", "4h", "24h"]:
            val = r.get(f"was_correct_{period}")
            if val is not None:
                total_counts[period] += 1
                if val:
                    correct_counts[period] += 1

    for period in ["1h", "4h", "24h"]:
        total = total_counts[period]
        correct = correct_counts[period]
        pct = (correct / total * 100) if total > 0 else 0
        print(f"  {period} 정확도: {correct}/{total} ({pct:.1f}%)")

    # 4) Supabase 저장
    if dry_run:
        print("[4/4] DRY RUN - Supabase 저장 건너뜀")
        ok, fail = 0, 0
    else:
        print(f"[4/4] Supabase decisions 테이블 저장 중... ({len(records)}개)")
        ok, fail = store_decisions_batch(records)
        print(f"  저장 성공: {ok}개, 실패: {fail}개")

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"  {year}년 decisions 백필 완료!")
    print(f"  총 레코드: {len(records)}개")
    print(f"  매수 {buy_count} / 매도 {sell_count} / 관망 {hold_count}")
    print(f"  Supabase: 성공 {ok} / 실패 {fail}")
    print(f"  소요시간: {elapsed:.0f}초")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="2018~2021 decisions 테이블 백필"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--year", type=int, choices=VALID_YEARS)
    group.add_argument("--all", action="store_true")
    parser.add_argument("--dry-run", action="store_true",
                        help="DB 저장 없이 시뮬레이션만 실행")
    args = parser.parse_args()

    years = VALID_YEARS if args.all else [args.year]

    t0 = time.time()
    for year in years:
        backfill_year(year, dry_run=args.dry_run)

    if len(years) > 1:
        print(f"\n{'#'*60}")
        print(f"  전체 {len(years)}개 연도 백필 완료!")
        print(f"  총 소요시간: {time.time() - t0:.0f}초")
        print(f"{'#'*60}")


if __name__ == "__main__":
    main()
