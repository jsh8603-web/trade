"""
2025.01 ~ 2026.03 전체 매매 데이터 종합 분석 보고서 생성
- 전체 요약 통계
- 월별 분석
- 시장 상태별 분석 (매크로, FGI, RSI 등)
- 매매 결정 패턴 분석
- 외부 요인 상관 분석
- 수익률/성과 분석
"""

import os
import sys
import json
import math
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from dotenv import load_dotenv

load_dotenv()

from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
sb = create_client(SUPABASE_URL, SUPABASE_KEY)


def load_all_decisions():
    """전체 decisions 로드"""
    all_rows = []
    offset = 0
    while True:
        r = sb.table('decisions').select('*').order('created_at').range(offset, offset + 999).execute()
        if not r.data:
            break
        all_rows.extend(r.data)
        offset += 1000
        if len(r.data) < 1000:
            break
    return all_rows


def parse_snapshot(row):
    """market_data_snapshot 파싱"""
    snap = row.get('market_data_snapshot')
    if not snap:
        return {}
    if isinstance(snap, str):
        try:
            return json.loads(snap)
        except Exception:
            return {}
    return snap if isinstance(snap, dict) else {}


def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def extract_metrics(row):
    """row에서 분석에 필요한 주요 지표 추출 (소스별 다른 JSON 구조 대응)"""
    snap = parse_snapshot(row)
    created = row.get('created_at', '')
    source = row.get('source', '')

    # 날짜/시간
    dt = None
    if created:
        try:
            dt = datetime.fromisoformat(created.replace('+00:00', '').replace('Z', ''))
        except Exception:
            pass

    # 매매 결정
    decision = (row.get('decision') or '').lower()
    confidence = safe_float(row.get('confidence'), 0)

    # ─── 소스별 지표 추출 ───
    indicators = snap.get('indicators', {})
    buy_score = snap.get('buy_score', {})

    # BTC 가격: 여러 경로 탐색
    btc_price = 0
    # 경로1: indicators.current_price (backtest_2025h1, backtest_jan2026, backtest_mar2026)
    btc_price = safe_float(indicators.get('current_price'), 0)
    # 경로2: enriched_daily의 close
    if btc_price == 0:
        btc_price = safe_float(snap.get('close'), 0)
    # 경로3: swing의 entry_price
    if btc_price == 0:
        btc_price = safe_float(snap.get('entry_price'), 0)
    # 경로4: r6의 future_prices[0]
    if btc_price == 0:
        fp = snap.get('future_prices', [])
        if isinstance(fp, list) and len(fp) > 0:
            btc_price = safe_float(fp[0], 0)
    # 경로5: top-level
    if btc_price == 0:
        btc_price = safe_float(snap.get('btc_price') or snap.get('current_price') or snap.get('price'), 0)

    # RSI: 여러 경로
    rsi = safe_float(indicators.get('rsi_14'), 0)
    if rsi == 0:
        rsi = safe_float(buy_score.get('rsi', {}).get('value') if isinstance(buy_score.get('rsi'), dict) else 0, 0)
    if rsi == 0:
        rsi = safe_float(snap.get('rsi') or snap.get('rsi_14'), 0)

    # SMA20
    sma20 = safe_float(indicators.get('sma_20'), 0)
    if sma20 == 0:
        sma20 = safe_float(snap.get('sma20') or snap.get('sma_20'), 0)

    # SMA deviation
    sma_dev = safe_float(indicators.get('sma_deviation_pct'), 0)
    if sma_dev == 0:
        sma_dev = safe_float(buy_score.get('sma', {}).get('value') if isinstance(buy_score.get('sma'), dict) else 0, 0)

    # FGI: 여러 경로
    fgi = 0
    if isinstance(buy_score.get('fgi'), dict):
        fgi = safe_float(buy_score['fgi'].get('value'), 0)
    if fgi == 0:
        fgi = safe_float(snap.get('fgi'), 0)
    if fgi == 0:
        fgi = safe_float(snap.get('fear_greed') or snap.get('fear_greed_index'), 0)

    # 매수 점수 (에이전트 시스템 핵심 지표)
    total_buy_score = safe_float(buy_score.get('total'), 0)
    buy_threshold = safe_float(buy_score.get('threshold'), 0)
    buy_result = buy_score.get('result', '')

    # 24h 변화율
    change_24h = safe_float(indicators.get('price_change_24h'), 0)
    if change_24h == 0:
        change_24h = safe_float(snap.get('change_24h') or snap.get('price_change_24h'), 0)

    # 거래량
    volume = safe_float(indicators.get('volume'), 0)
    if volume == 0:
        volume = safe_float(snap.get('volume') or snap.get('volume_total') or snap.get('volume_24h'), 0)

    # 볼린저밴드
    bb = indicators.get('bollinger', {})
    bb_upper = safe_float(bb.get('upper'), 0)
    bb_lower = safe_float(bb.get('lower'), 0)
    if bb_upper == 0:
        bb_upper = safe_float(snap.get('bb_upper'), 0)
        bb_lower = safe_float(snap.get('bb_lower'), 0)

    # MACD
    macd_data = indicators.get('macd', {})
    macd = safe_float(macd_data.get('macd') if isinstance(macd_data, dict) else 0, 0)
    macd_signal = safe_float(macd_data.get('signal') if isinstance(macd_data, dict) else 0, 0)
    macd_golden = macd_data.get('golden_cross', False) if isinstance(macd_data, dict) else False

    # swing 수익률
    pnl_pct = safe_float(snap.get('pnl_pct'), 0)
    pnl_krw = safe_float(snap.get('pnl_krw'), 0)

    # enriched_daily 특수 필드
    whale_avg = safe_float(snap.get('whale_avg'), 0)
    sentiment_avg = safe_float(snap.get('sentiment_avg'), 0)

    # ─── 매크로 (공통: real_macro) ───
    real_macro = snap.get('real_macro', {})
    macro_score = safe_float(real_macro.get('score'), 0)
    macro_sentiment = real_macro.get('sentiment', 'unknown')

    sp500 = real_macro.get('sp500', {})
    sp500_val = safe_float(sp500.get('value'), 0)
    sp500_chg = safe_float(sp500.get('change_pct'), 0)

    dxy = real_macro.get('dxy', {})
    dxy_val = safe_float(dxy.get('value'), 0)
    dxy_chg = safe_float(dxy.get('change_pct'), 0)

    gold = real_macro.get('gold', {})
    gold_val = safe_float(gold.get('value'), 0)
    gold_chg = safe_float(gold.get('change_pct'), 0)

    us10y = real_macro.get('us10y', {})
    us10y_val = safe_float(us10y.get('value'), 0)

    # 에이전트 타입
    agent_type = snap.get('agent_type') or snap.get('active_agent') or ''

    # 수익률/이유
    trade_amount = safe_float(row.get('trade_amount') or snap.get('trade_amount'), 0)
    reason = row.get('reason', '') or ''

    return {
        'dt': dt,
        'month': dt.strftime('%Y-%m') if dt else None,
        'date': dt.strftime('%Y-%m-%d') if dt else None,
        'hour': dt.hour if dt else None,
        'decision': decision,
        'confidence': confidence,
        'btc_price': btc_price,
        'rsi': rsi,
        'sma20': sma20,
        'sma_dev': sma_dev,
        'fgi': fgi,
        'total_buy_score': total_buy_score,
        'buy_threshold': buy_threshold,
        'macro_score': macro_score,
        'macro_sentiment': macro_sentiment,
        'sp500_val': sp500_val,
        'sp500_chg': sp500_chg,
        'dxy_val': dxy_val,
        'dxy_chg': dxy_chg,
        'gold_val': gold_val,
        'gold_chg': gold_chg,
        'us10y_val': us10y_val,
        'change_24h': change_24h,
        'bb_upper': bb_upper,
        'bb_lower': bb_lower,
        'volume': volume,
        'macd': macd,
        'macd_golden': macd_golden,
        'pnl_pct': pnl_pct,
        'pnl_krw': pnl_krw,
        'whale_avg': whale_avg,
        'sentiment_avg': sentiment_avg,
        'trade_amount': trade_amount,
        'source': source,
        'agent_type': agent_type,
        'reason': reason,
    }


def avg(lst):
    valid = [x for x in lst if x and x != 0]
    return sum(valid) / len(valid) if valid else 0


def median(lst):
    valid = sorted([x for x in lst if x and x != 0])
    if not valid:
        return 0
    n = len(valid)
    if n % 2 == 0:
        return (valid[n//2 - 1] + valid[n//2]) / 2
    return valid[n//2]


def std_dev(lst):
    valid = [x for x in lst if x and x != 0]
    if len(valid) < 2:
        return 0
    mean = sum(valid) / len(valid)
    variance = sum((x - mean) ** 2 for x in valid) / (len(valid) - 1)
    return math.sqrt(variance)


def classify_fgi(fgi):
    if fgi <= 20:
        return "극단적 공포"
    elif fgi <= 40:
        return "공포"
    elif fgi <= 60:
        return "중립"
    elif fgi <= 80:
        return "탐욕"
    else:
        return "극단적 탐욕"


def classify_rsi(rsi):
    if rsi <= 30:
        return "과매도"
    elif rsi <= 40:
        return "약세"
    elif rsi <= 60:
        return "중립"
    elif rsi <= 70:
        return "강세"
    else:
        return "과매수"


def classify_macro(score):
    if score >= 8:
        return "강한 긍정"
    elif score >= 3:
        return "긍정"
    elif score >= -2:
        return "중립"
    elif score >= -7:
        return "부정"
    else:
        return "강한 부정"


def generate_report(rows):
    """종합 분석 보고서 생성"""
    metrics = [extract_metrics(r) for r in rows]
    # 날짜가 있는 것만
    metrics = [m for m in metrics if m['dt'] is not None]
    metrics.sort(key=lambda x: x['dt'])

    report = []
    report.append("=" * 80)
    report.append("# 암호화폐 자동매매 시스템 종합 분석 보고서")
    report.append(f"# 분석 기간: {metrics[0]['date']} ~ {metrics[-1]['date']}")
    report.append(f"# 총 데이터: {len(metrics)}건")
    report.append(f"# 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("=" * 80)

    # ═══════════════════════════════════════════════════════
    # 1. 전체 요약
    # ═══════════════════════════════════════════════════════
    report.append("\n\n" + "█" * 80)
    report.append("█  1. 전체 요약 통계")
    report.append("█" * 80)

    decisions = Counter(m['decision'] for m in metrics)
    report.append(f"\n### 매매 결정 분포")
    total = len(metrics)
    for dec, cnt in decisions.most_common():
        pct = cnt / total * 100
        bar = "█" * int(pct / 2)
        report.append(f"  {dec:12s}: {cnt:5d}건 ({pct:5.1f}%) {bar}")

    # BTC 가격 통계
    prices = [m['btc_price'] for m in metrics if m['btc_price'] > 0]
    if prices:
        report.append(f"\n### BTC 가격 통계")
        report.append(f"  최저가: {min(prices):>15,.0f} KRW")
        report.append(f"  최고가: {max(prices):>15,.0f} KRW")
        report.append(f"  평균가: {avg(prices):>15,.0f} KRW")
        report.append(f"  중앙값: {median(prices):>15,.0f} KRW")
        report.append(f"  표준편차: {std_dev(prices):>15,.0f} KRW")
        if prices[0] > 0 and prices[-1] > 0:
            total_return = (prices[-1] - prices[0]) / prices[0] * 100
            report.append(f"  기간 수익률: {total_return:>14.1f}%")

    # 신뢰도 통계
    confs = [m['confidence'] for m in metrics if m['confidence'] > 0]
    if confs:
        report.append(f"\n### 매매 신뢰도")
        report.append(f"  평균: {avg(confs):.1f}%")
        report.append(f"  중앙값: {median(confs):.1f}%")
        report.append(f"  최저: {min(confs):.1f}%")
        report.append(f"  최고: {max(confs):.1f}%")

    # 소스별 분포
    sources = Counter(m['source'] for m in metrics)
    report.append(f"\n### 데이터 소스 분포")
    for src, cnt in sources.most_common():
        report.append(f"  {src:30s}: {cnt:5d}건 ({cnt/total*100:.1f}%)")

    # ═══════════════════════════════════════════════════════
    # 2. 월별 분석
    # ═══════════════════════════════════════════════════════
    report.append("\n\n" + "█" * 80)
    report.append("█  2. 월별 상세 분석")
    report.append("█" * 80)

    monthly = defaultdict(list)
    for m in metrics:
        if m['month']:
            monthly[m['month']].append(m)

    report.append(f"\n{'월':>8s} | {'건수':>5s} | {'매수':>5s} | {'매도':>5s} | {'관망':>5s} | {'BTC평균가':>14s} | {'RSI':>5s} | {'FGI':>5s} | {'매크로':>6s} | {'S&P500':>8s}")
    report.append("-" * 95)

    for month in sorted(monthly.keys()):
        items = monthly[month]
        n = len(items)
        buys = sum(1 for m in items if 'buy' in m['decision'] or '매수' in m['decision'])
        sells = sum(1 for m in items if 'sell' in m['decision'] or '매도' in m['decision'])
        holds = n - buys - sells
        avg_price = avg([m['btc_price'] for m in items])
        avg_rsi = avg([m['rsi'] for m in items])
        avg_fgi = avg([m['fgi'] for m in items])
        avg_macro = avg([m['macro_score'] for m in items])
        avg_sp = avg([m['sp500_val'] for m in items])

        report.append(
            f"{month:>8s} | {n:>5d} | {buys:>5d} | {sells:>5d} | {holds:>5d} | "
            f"{avg_price:>14,.0f} | {avg_rsi:>5.1f} | {avg_fgi:>5.1f} | {avg_macro:>+6.1f} | {avg_sp:>8,.0f}"
        )

    # 각 월 상세 서술
    for month in sorted(monthly.keys()):
        items = monthly[month]
        n = len(items)
        report.append(f"\n\n--- {month} 상세 ---")

        prices_m = [m['btc_price'] for m in items if m['btc_price'] > 0]
        fgis = [m['fgi'] for m in items if m['fgi'] > 0]
        rsis = [m['rsi'] for m in items if m['rsi'] > 0]
        macros = [m['macro_score'] for m in items]
        sp_chgs = [m['sp500_chg'] for m in items if m['sp500_chg'] != 0]
        dxy_vals = [m['dxy_val'] for m in items if m['dxy_val'] > 0]
        gold_vals = [m['gold_val'] for m in items if m['gold_val'] > 0]
        us10y_vals = [m['us10y_val'] for m in items if m['us10y_val'] > 0]
        ch24 = [m['change_24h'] for m in items if m['change_24h'] != 0]

        buys = sum(1 for m in items if 'buy' in m['decision'] or '매수' in m['decision'])
        sells = sum(1 for m in items if 'sell' in m['decision'] or '매도' in m['decision'])
        holds = n - buys - sells

        report.append(f"  총 결정: {n}건 (매수: {buys}, 매도: {sells}, 관망: {holds})")
        report.append(f"  매수 비율: {buys/n*100:.1f}% | 매도 비율: {sells/n*100:.1f}% | 관망 비율: {holds/n*100:.1f}%")

        if prices_m:
            price_min = min(prices_m)
            price_max = max(prices_m)
            price_range_pct = (price_max - price_min) / price_min * 100 if price_min > 0 else 0
            report.append(f"  BTC 가격: {price_min:,.0f} ~ {price_max:,.0f} (변동폭 {price_range_pct:.1f}%)")
            if len(prices_m) >= 2:
                month_return = (prices_m[-1] - prices_m[0]) / prices_m[0] * 100
                report.append(f"  월간 수익률: {month_return:+.1f}%")

        if rsis:
            report.append(f"  RSI: 평균 {avg(rsis):.1f} (범위 {min(rsis):.0f}~{max(rsis):.0f})")
            rsi_zones = Counter(classify_rsi(r) for r in rsis)
            report.append(f"    구간: {dict(rsi_zones)}")

        if fgis:
            report.append(f"  FGI: 평균 {avg(fgis):.1f} (범위 {min(fgis):.0f}~{max(fgis):.0f})")
            fgi_zones = Counter(classify_fgi(f) for f in fgis)
            report.append(f"    구간: {dict(fgi_zones)}")

        if macros:
            report.append(f"  매크로 점수: 평균 {avg(macros):+.1f} (범위 {min(macros):+.0f}~{max(macros):+.0f})")
            macro_zones = Counter(classify_macro(m) for m in macros)
            report.append(f"    구간: {dict(macro_zones)}")

        if sp_chgs:
            pos_sp = sum(1 for s in sp_chgs if s > 0)
            neg_sp = sum(1 for s in sp_chgs if s < 0)
            report.append(f"  S&P500: 상승일 {pos_sp}, 하락일 {neg_sp}, 평균변동 {avg(sp_chgs):+.2f}%")

        if dxy_vals:
            report.append(f"  DXY: 평균 {avg(dxy_vals):.1f} (범위 {min(dxy_vals):.1f}~{max(dxy_vals):.1f})")

        if gold_vals:
            report.append(f"  금: 평균 ${avg(gold_vals):,.0f} (범위 ${min(gold_vals):,.0f}~${max(gold_vals):,.0f})")

        if us10y_vals:
            report.append(f"  미국채10Y: 평균 {avg(us10y_vals):.2f}% (범위 {min(us10y_vals):.2f}%~{max(us10y_vals):.2f}%)")

        # 월 핵심 이벤트/패턴 요약
        if ch24:
            big_drops = sum(1 for c in ch24 if c < -3)
            big_pumps = sum(1 for c in ch24 if c > 3)
            if big_drops or big_pumps:
                report.append(f"  급등/급락: 급등(+3%↑) {big_pumps}회, 급락(-3%↓) {big_drops}회")

    # ═══════════════════════════════════════════════════════
    # 3. 시장 상태별 매매 패턴 분석
    # ═══════════════════════════════════════════════════════
    report.append("\n\n" + "█" * 80)
    report.append("█  3. 시장 상태별 매매 패턴 분석")
    report.append("█" * 80)

    # 3-1. FGI 구간별
    report.append("\n### 3-1. 공포탐욕지수(FGI) 구간별 매매 결정")
    fgi_groups = defaultdict(list)
    for m in metrics:
        if m['fgi'] > 0:
            zone = classify_fgi(m['fgi'])
            fgi_groups[zone].append(m)

    for zone in ["극단적 공포", "공포", "중립", "탐욕", "극단적 탐욕"]:
        items = fgi_groups.get(zone, [])
        if not items:
            continue
        n = len(items)
        buys = sum(1 for m in items if 'buy' in m['decision'] or '매수' in m['decision'])
        sells = sum(1 for m in items if 'sell' in m['decision'] or '매도' in m['decision'])
        holds = n - buys - sells
        avg_conf = avg([m['confidence'] for m in items if m['confidence'] > 0])
        avg_price = avg([m['btc_price'] for m in items if m['btc_price'] > 0])
        report.append(f"\n  [{zone}] ({n}건)")
        report.append(f"    매수: {buys}({buys/n*100:.0f}%) | 매도: {sells}({sells/n*100:.0f}%) | 관망: {holds}({holds/n*100:.0f}%)")
        report.append(f"    평균 신뢰도: {avg_conf:.1f}% | 평균 BTC가: {avg_price:,.0f}")
        report.append(f"    평균 FGI: {avg([m['fgi'] for m in items]):.1f}")

    # 3-2. RSI 구간별
    report.append("\n### 3-2. RSI 구간별 매매 결정")
    rsi_groups = defaultdict(list)
    for m in metrics:
        if m['rsi'] > 0:
            zone = classify_rsi(m['rsi'])
            rsi_groups[zone].append(m)

    for zone in ["과매도", "약세", "중립", "강세", "과매수"]:
        items = rsi_groups.get(zone, [])
        if not items:
            continue
        n = len(items)
        buys = sum(1 for m in items if 'buy' in m['decision'] or '매수' in m['decision'])
        sells = sum(1 for m in items if 'sell' in m['decision'] or '매도' in m['decision'])
        holds = n - buys - sells
        report.append(f"\n  [{zone}] ({n}건)")
        report.append(f"    매수: {buys}({buys/n*100:.0f}%) | 매도: {sells}({sells/n*100:.0f}%) | 관망: {holds}({holds/n*100:.0f}%)")

    # 3-3. 매크로 구간별
    report.append("\n### 3-3. 매크로 점수 구간별 매매 결정")
    macro_groups = defaultdict(list)
    for m in metrics:
        zone = classify_macro(m['macro_score'])
        macro_groups[zone].append(m)

    for zone in ["강한 부정", "부정", "중립", "긍정", "강한 긍정"]:
        items = macro_groups.get(zone, [])
        if not items:
            continue
        n = len(items)
        buys = sum(1 for m in items if 'buy' in m['decision'] or '매수' in m['decision'])
        sells = sum(1 for m in items if 'sell' in m['decision'] or '매도' in m['decision'])
        holds = n - buys - sells
        avg_price = avg([m['btc_price'] for m in items if m['btc_price'] > 0])
        report.append(f"\n  [{zone}] ({n}건)")
        report.append(f"    매수: {buys}({buys/n*100:.0f}%) | 매도: {sells}({sells/n*100:.0f}%) | 관망: {holds}({holds/n*100:.0f}%)")
        report.append(f"    평균 BTC가: {avg_price:,.0f}")

    # ═══════════════════════════════════════════════════════
    # 4. 외부 매크로 요인 심층 분석
    # ═══════════════════════════════════════════════════════
    report.append("\n\n" + "█" * 80)
    report.append("█  4. 외부 매크로 요인 심층 분석")
    report.append("█" * 80)

    # 4-1. S&P500 vs BTC
    report.append("\n### 4-1. S&P500과 BTC 상관관계")
    sp_up = [m for m in metrics if m['sp500_chg'] > 0.3 and m['btc_price'] > 0]
    sp_down = [m for m in metrics if m['sp500_chg'] < -0.3 and m['btc_price'] > 0]

    if sp_up:
        btc_up_when_sp_up = sum(1 for m in sp_up if m['change_24h'] > 0)
        report.append(f"  S&P500 상승일 ({len(sp_up)}건): BTC 동반상승 {btc_up_when_sp_up}건 ({btc_up_when_sp_up/len(sp_up)*100:.0f}%)")
        buys_sp_up = sum(1 for m in sp_up if 'buy' in m['decision'] or '매수' in m['decision'])
        report.append(f"    → 매수 결정: {buys_sp_up}건 ({buys_sp_up/len(sp_up)*100:.0f}%)")

    if sp_down:
        btc_down_when_sp_down = sum(1 for m in sp_down if m['change_24h'] < 0)
        report.append(f"  S&P500 하락일 ({len(sp_down)}건): BTC 동반하락 {btc_down_when_sp_down}건 ({btc_down_when_sp_down/len(sp_down)*100:.0f}%)")
        sells_sp_down = sum(1 for m in sp_down if 'sell' in m['decision'] or '매도' in m['decision'])
        report.append(f"    → 매도 결정: {sells_sp_down}건 ({sells_sp_down/len(sp_down)*100:.0f}%)")

    # 4-2. DXY vs BTC (역상관)
    report.append("\n### 4-2. 달러 인덱스(DXY)와 BTC 관계")
    dxy_up = [m for m in metrics if m['dxy_chg'] > 0.2 and m['btc_price'] > 0]
    dxy_down = [m for m in metrics if m['dxy_chg'] < -0.2 and m['btc_price'] > 0]

    if dxy_up:
        btc_down_when_dxy_up = sum(1 for m in dxy_up if m['change_24h'] < 0)
        report.append(f"  DXY 강세일 ({len(dxy_up)}건): BTC 하락 {btc_down_when_dxy_up}건 ({btc_down_when_dxy_up/len(dxy_up)*100:.0f}%)")

    if dxy_down:
        btc_up_when_dxy_down = sum(1 for m in dxy_down if m['change_24h'] > 0)
        report.append(f"  DXY 약세일 ({len(dxy_down)}건): BTC 상승 {btc_up_when_dxy_down}건 ({btc_up_when_dxy_down/len(dxy_down)*100:.0f}%)")

    # DXY 수준별 분석
    dxy_ranges = {'100 이하': [], '100~103': [], '103~106': [], '106~109': [], '109 이상': []}
    for m in metrics:
        d = m['dxy_val']
        if d <= 0:
            continue
        elif d < 100:
            dxy_ranges['100 이하'].append(m)
        elif d < 103:
            dxy_ranges['100~103'].append(m)
        elif d < 106:
            dxy_ranges['103~106'].append(m)
        elif d < 109:
            dxy_ranges['106~109'].append(m)
        else:
            dxy_ranges['109 이상'].append(m)

    report.append(f"\n  DXY 수준별 BTC 평균가:")
    for rng, items in dxy_ranges.items():
        if items:
            avg_p = avg([m['btc_price'] for m in items if m['btc_price'] > 0])
            report.append(f"    DXY {rng:>8s}: BTC 평균 {avg_p:>14,.0f} KRW ({len(items)}건)")

    # 4-3. 금 가격 vs BTC
    report.append("\n### 4-3. 금(Gold)과 BTC 관계")
    gold_high = [m for m in metrics if m['gold_val'] > 2800]
    gold_low = [m for m in metrics if 0 < m['gold_val'] <= 2800]
    if gold_high:
        avg_btc_gold_high = avg([m['btc_price'] for m in gold_high if m['btc_price'] > 0])
        report.append(f"  금 $2800↑ ({len(gold_high)}건): BTC 평균가 {avg_btc_gold_high:,.0f}")
    if gold_low:
        avg_btc_gold_low = avg([m['btc_price'] for m in gold_low if m['btc_price'] > 0])
        report.append(f"  금 $2800↓ ({len(gold_low)}건): BTC 평균가 {avg_btc_gold_low:,.0f}")

    # 4-4. 미국채 10Y
    report.append("\n### 4-4. 미국채 10년물 금리와 BTC")
    rate_ranges = {'3.5%↓': [], '3.5~4.0%': [], '4.0~4.3%': [], '4.3~4.6%': [], '4.6%↑': []}
    for m in metrics:
        r = m['us10y_val']
        if r <= 0:
            continue
        elif r < 3.5:
            rate_ranges['3.5%↓'].append(m)
        elif r < 4.0:
            rate_ranges['3.5~4.0%'].append(m)
        elif r < 4.3:
            rate_ranges['4.0~4.3%'].append(m)
        elif r < 4.6:
            rate_ranges['4.3~4.6%'].append(m)
        else:
            rate_ranges['4.6%↑'].append(m)

    for rng, items in rate_ranges.items():
        if items:
            avg_p = avg([m['btc_price'] for m in items if m['btc_price'] > 0])
            buys = sum(1 for m in items if 'buy' in m['decision'] or '매수' in m['decision'])
            report.append(f"  금리 {rng:>8s}: BTC평균 {avg_p:>12,.0f} | 매수 {buys}/{len(items)}건 ({buys/len(items)*100:.0f}%)")

    # ═══════════════════════════════════════════════════════
    # 5. 매매 결정 패턴 심층 분석
    # ═══════════════════════════════════════════════════════
    report.append("\n\n" + "█" * 80)
    report.append("█  5. 매매 결정 패턴 심층 분석")
    report.append("█" * 80)

    # 5-1. 결정별 평균 지표
    report.append("\n### 5-1. 결정별 평균 지표 비교")
    for dec_type in ['buy', 'sell', 'hold']:
        items = [m for m in metrics if dec_type in m['decision'] or
                 (dec_type == 'buy' and '매수' in m['decision']) or
                 (dec_type == 'sell' and '매도' in m['decision']) or
                 (dec_type == 'hold' and '관망' in m['decision'])]
        if not items:
            continue
        labels = {'buy': '매수', 'sell': '매도', 'hold': '관망'}
        report.append(f"\n  [{labels.get(dec_type, dec_type)}] ({len(items)}건)")
        report.append(f"    평균 BTC가: {avg([m['btc_price'] for m in items]):>14,.0f}")
        report.append(f"    평균 RSI: {avg([m['rsi'] for m in items]):>8.1f}")
        report.append(f"    평균 FGI: {avg([m['fgi'] for m in items]):>8.1f}")
        report.append(f"    평균 매크로: {avg([m['macro_score'] for m in items]):>+8.1f}")
        report.append(f"    평균 24h변동: {avg([m['change_24h'] for m in items]):>+8.2f}%")
        report.append(f"    평균 신뢰도: {avg([m['confidence'] for m in items]):>8.1f}%")

    # 5-2. 시간대별 분석
    report.append("\n### 5-2. 시간대별 매매 패턴")
    hour_groups = defaultdict(list)
    for m in metrics:
        if m['hour'] is not None:
            # 4시간 단위로 그룹
            h_group = (m['hour'] // 4) * 4
            hour_groups[h_group].append(m)

    for h in sorted(hour_groups.keys()):
        items = hour_groups[h]
        n = len(items)
        buys = sum(1 for m in items if 'buy' in m['decision'] or '매수' in m['decision'])
        sells = sum(1 for m in items if 'sell' in m['decision'] or '매도' in m['decision'])
        report.append(f"  {h:02d}~{h+3:02d}시: {n:>5d}건 | 매수 {buys:>4d}({buys/n*100:4.0f}%) | 매도 {sells:>4d}({sells/n*100:4.0f}%)")

    # 5-3. 에이전트/소스별 성향
    report.append("\n### 5-3. 소스별 매매 성향")
    for src, cnt in sources.most_common(10):
        items = [m for m in metrics if m['source'] == src]
        if not items:
            continue
        buys = sum(1 for m in items if 'buy' in m['decision'] or '매수' in m['decision'])
        sells = sum(1 for m in items if 'sell' in m['decision'] or '매도' in m['decision'])
        holds = len(items) - buys - sells
        report.append(f"\n  [{src}] ({len(items)}건)")
        report.append(f"    매수: {buys}({buys/len(items)*100:.0f}%) | 매도: {sells}({sells/len(items)*100:.0f}%) | 관망: {holds}({holds/len(items)*100:.0f}%)")

    # ═══════════════════════════════════════════════════════
    # 6. 복합 조건 분석 (매크로+기술+심리)
    # ═══════════════════════════════════════════════════════
    report.append("\n\n" + "█" * 80)
    report.append("█  6. 복합 조건 분석 (매크로 + 기술지표 + 심리)")
    report.append("█" * 80)

    # 6-1. 최적 매수 조건
    report.append("\n### 6-1. 최적 매수 조건 탐색")
    # FGI 공포 + RSI 과매도 + 매크로 긍정
    optimal_buy = [m for m in metrics if
                   m['fgi'] > 0 and m['fgi'] <= 30 and
                   m['rsi'] > 0 and m['rsi'] <= 35 and
                   m['macro_score'] >= 3]
    report.append(f"\n  조건1: FGI≤30 + RSI≤35 + 매크로≥3 (공포+과매도+긍정)")
    if optimal_buy:
        buys = sum(1 for m in optimal_buy if 'buy' in m['decision'] or '매수' in m['decision'])
        report.append(f"    발생: {len(optimal_buy)}건, 매수: {buys}건 ({buys/len(optimal_buy)*100:.0f}%)")
        report.append(f"    평균 BTC가: {avg([m['btc_price'] for m in optimal_buy]):,.0f}")
    else:
        report.append(f"    발생: 0건")

    # FGI 공포 + RSI 중립~약세
    fear_buy = [m for m in metrics if
                m['fgi'] > 0 and m['fgi'] <= 30 and
                m['rsi'] > 0 and m['rsi'] <= 45]
    report.append(f"\n  조건2: FGI≤30 + RSI≤45 (공포+약세)")
    if fear_buy:
        buys = sum(1 for m in fear_buy if 'buy' in m['decision'] or '매수' in m['decision'])
        report.append(f"    발생: {len(fear_buy)}건, 매수: {buys}건 ({buys/len(fear_buy)*100:.0f}%)")

    # 매크로 강한긍정 + FGI 탐욕
    greedy_macro = [m for m in metrics if
                    m['fgi'] >= 70 and
                    m['macro_score'] >= 5]
    report.append(f"\n  조건3: FGI≥70 + 매크로≥5 (탐욕+긍정 = 과열 주의)")
    if greedy_macro:
        sells = sum(1 for m in greedy_macro if 'sell' in m['decision'] or '매도' in m['decision'])
        report.append(f"    발생: {len(greedy_macro)}건, 매도: {sells}건 ({sells/len(greedy_macro)*100:.0f}%)")

    # 6-2. 위험 구간
    report.append("\n### 6-2. 위험 구간 분석")
    danger = [m for m in metrics if
              m['fgi'] >= 80 and m['rsi'] >= 70]
    report.append(f"\n  FGI≥80 + RSI≥70 (극단적 탐욕 + 과매수)")
    if danger:
        sells = sum(1 for m in danger if 'sell' in m['decision'] or '매도' in m['decision'])
        report.append(f"    발생: {len(danger)}건, 매도: {sells}건 ({sells/len(danger)*100:.0f}%)")
    else:
        report.append(f"    발생: 0건")

    # S&P500 급락 + 매크로 부정
    crisis = [m for m in metrics if
              m['sp500_chg'] < -1.0 and m['macro_score'] <= -5]
    report.append(f"\n  S&P500 -1%↓ + 매크로≤-5 (글로벌 위기)")
    if crisis:
        sells = sum(1 for m in crisis if 'sell' in m['decision'] or '매도' in m['decision'])
        avg_btc = avg([m['btc_price'] for m in crisis if m['btc_price'] > 0])
        report.append(f"    발생: {len(crisis)}건, 매도: {sells}건 ({sells/len(crisis)*100:.0f}%)")
        report.append(f"    평균 BTC가: {avg_btc:,.0f}")
    else:
        report.append(f"    발생: 0건")

    # ═══════════════════════════════════════════════════════
    # 7. 가격 구간별 분석
    # ═══════════════════════════════════════════════════════
    report.append("\n\n" + "█" * 80)
    report.append("█  7. BTC 가격 구간별 분석")
    report.append("█" * 80)

    price_ranges = defaultdict(list)
    for m in metrics:
        p = m['btc_price']
        if p <= 0:
            continue
        # 1000만원 단위
        bucket = int(p / 10_000_000) * 1000
        label = f"{bucket:,}만~{bucket+1000:,}만"
        price_ranges[bucket].append(m)

    for bucket in sorted(price_ranges.keys()):
        items = price_ranges[bucket]
        n = len(items)
        buys = sum(1 for m in items if 'buy' in m['decision'] or '매수' in m['decision'])
        sells = sum(1 for m in items if 'sell' in m['decision'] or '매도' in m['decision'])
        holds = n - buys - sells
        avg_fgi = avg([m['fgi'] for m in items if m['fgi'] > 0])
        avg_rsi = avg([m['rsi'] for m in items if m['rsi'] > 0])
        label = f"{bucket:,}만~{bucket+1000:,}만"
        report.append(f"  {label:>18s}: {n:>5d}건 | 매수 {buys/n*100:4.0f}% | 매도 {sells/n*100:4.0f}% | FGI {avg_fgi:4.0f} | RSI {avg_rsi:4.0f}")

    # ═══════════════════════════════════════════════════════
    # 8. 주요 발견 및 인사이트
    # ═══════════════════════════════════════════════════════
    report.append("\n\n" + "█" * 80)
    report.append("█  8. 주요 발견 및 인사이트")
    report.append("█" * 80)

    report.append("\n### 8-1. 시장 사이클 패턴")

    # 월별 가격 트렌드 요약
    month_prices = {}
    for month in sorted(monthly.keys()):
        items = monthly[month]
        prices_m = [m['btc_price'] for m in items if m['btc_price'] > 0]
        if prices_m:
            month_prices[month] = {
                'avg': avg(prices_m),
                'min': min(prices_m),
                'max': max(prices_m),
                'first': prices_m[0],
                'last': prices_m[-1]
            }

    if month_prices:
        # 최고/최저 월
        best_month = max(month_prices.items(), key=lambda x: x[1]['avg'])
        worst_month = min(month_prices.items(), key=lambda x: x[1]['avg'])
        report.append(f"  최고 평균가 월: {best_month[0]} ({best_month[1]['avg']:,.0f} KRW)")
        report.append(f"  최저 평균가 월: {worst_month[0]} ({worst_month[1]['avg']:,.0f} KRW)")

        # 연속 상승/하락
        months_sorted = sorted(month_prices.keys())
        up_streak = 0
        down_streak = 0
        max_up = 0
        max_down = 0
        for i in range(1, len(months_sorted)):
            curr = month_prices[months_sorted[i]]['avg']
            prev = month_prices[months_sorted[i-1]]['avg']
            if curr > prev:
                up_streak += 1
                down_streak = 0
            else:
                down_streak += 1
                up_streak = 0
            max_up = max(max_up, up_streak)
            max_down = max(max_down, down_streak)
        report.append(f"  최장 연속 상승: {max_up}개월")
        report.append(f"  최장 연속 하락: {max_down}개월")

    report.append("\n### 8-2. 매크로 환경 요약")
    all_macros = [m['macro_score'] for m in metrics]
    pos_macro = sum(1 for m in all_macros if m >= 3)
    neg_macro = sum(1 for m in all_macros if m <= -3)
    neu_macro = len(all_macros) - pos_macro - neg_macro
    report.append(f"  전체 기간 매크로: 긍정 {pos_macro}건({pos_macro/len(all_macros)*100:.0f}%), "
                  f"중립 {neu_macro}건({neu_macro/len(all_macros)*100:.0f}%), "
                  f"부정 {neg_macro}건({neg_macro/len(all_macros)*100:.0f}%)")

    sp_vals = [m['sp500_val'] for m in metrics if m['sp500_val'] > 0]
    if sp_vals:
        report.append(f"  S&P500 범위: {min(sp_vals):,.0f} ~ {max(sp_vals):,.0f}")
        sp_return = (sp_vals[-1] - sp_vals[0]) / sp_vals[0] * 100
        report.append(f"  S&P500 기간 변동: {sp_return:+.1f}%")

    dxy_all = [m['dxy_val'] for m in metrics if m['dxy_val'] > 0]
    if dxy_all:
        report.append(f"  DXY 범위: {min(dxy_all):.1f} ~ {max(dxy_all):.1f}")

    gold_all = [m['gold_val'] for m in metrics if m['gold_val'] > 0]
    if gold_all:
        gold_return = (gold_all[-1] - gold_all[0]) / gold_all[0] * 100
        report.append(f"  금 가격 범위: ${min(gold_all):,.0f} ~ ${max(gold_all):,.0f} (기간 변동 {gold_return:+.1f}%)")

    report.append("\n### 8-3. 전략적 시사점")

    # 매수가 많았던 조건
    buy_items = [m for m in metrics if 'buy' in m['decision'] or '매수' in m['decision']]
    sell_items = [m for m in metrics if 'sell' in m['decision'] or '매도' in m['decision']]

    if buy_items:
        report.append(f"\n  [매수 시그널이 강했던 조건]")
        report.append(f"  평균 FGI: {avg([m['fgi'] for m in buy_items if m['fgi']>0]):.1f}")
        report.append(f"  평균 RSI: {avg([m['rsi'] for m in buy_items if m['rsi']>0]):.1f}")
        report.append(f"  평균 매크로: {avg([m['macro_score'] for m in buy_items]):+.1f}")
        report.append(f"  평균 BTC가: {avg([m['btc_price'] for m in buy_items if m['btc_price']>0]):,.0f}")

    if sell_items:
        report.append(f"\n  [매도 시그널이 강했던 조건]")
        report.append(f"  평균 FGI: {avg([m['fgi'] for m in sell_items if m['fgi']>0]):.1f}")
        report.append(f"  평균 RSI: {avg([m['rsi'] for m in sell_items if m['rsi']>0]):.1f}")
        report.append(f"  평균 매크로: {avg([m['macro_score'] for m in sell_items]):+.1f}")
        report.append(f"  평균 BTC가: {avg([m['btc_price'] for m in sell_items if m['btc_price']>0]):,.0f}")

    # ═══════════════════════════════════════════════════════
    # 9. 월간 매크로 변화 타임라인
    # ═══════════════════════════════════════════════════════
    report.append("\n\n" + "█" * 80)
    report.append("█  9. 월간 매크로 변화 타임라인")
    report.append("█" * 80)

    report.append(f"\n{'월':>8s} | {'BTC평균가':>14s} | {'S&P500':>8s} | {'DXY':>6s} | {'금':>8s} | {'10Y금리':>7s} | {'매크로':>6s} | {'FGI':>5s}")
    report.append("-" * 85)

    for month in sorted(monthly.keys()):
        items = monthly[month]
        avg_btc = avg([m['btc_price'] for m in items if m['btc_price'] > 0])
        avg_sp = avg([m['sp500_val'] for m in items if m['sp500_val'] > 0])
        avg_dxy = avg([m['dxy_val'] for m in items if m['dxy_val'] > 0])
        avg_gold = avg([m['gold_val'] for m in items if m['gold_val'] > 0])
        avg_10y = avg([m['us10y_val'] for m in items if m['us10y_val'] > 0])
        avg_macro = avg([m['macro_score'] for m in items])
        avg_fgi = avg([m['fgi'] for m in items if m['fgi'] > 0])

        report.append(
            f"{month:>8s} | {avg_btc:>14,.0f} | {avg_sp:>8,.0f} | {avg_dxy:>6.1f} | "
            f"${avg_gold:>7,.0f} | {avg_10y:>6.2f}% | {avg_macro:>+6.1f} | {avg_fgi:>5.1f}"
        )

    return "\n".join(report)


def main():
    print("데이터 로드 중...")
    rows = load_all_decisions()
    print(f"{len(rows)}건 로드 완료. 분석 중...")

    report = generate_report(rows)

    # 파일 저장
    output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'analysis_report_full.txt')
    output_path = os.path.abspath(output_path)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n보고서 저장: {output_path}")
    print(f"총 {len(report.splitlines())}줄")

    # 콘솔에도 출력 (cp949 인코딩 안전)
    try:
        print("\n" + report)
    except UnicodeEncodeError:
        for line in report.splitlines():
            try:
                print(line)
            except UnicodeEncodeError:
                print(line.encode('ascii', 'replace').decode())


if __name__ == '__main__':
    main()
