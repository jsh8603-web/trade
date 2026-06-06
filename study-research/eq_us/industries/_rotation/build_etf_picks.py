# -*- coding: utf-8 -*-
"""build_etf_picks.py — 약변별 sleeve 테마 ETF 선정 (Phase 1-2, 2026-06-06).

★자문 D2 선정 기준 = 대표성 + 유동성(MarCap≈AUM, Amount=거래대금) + 저비용. ★과거 리턴(EarningRate) 배제.
레버리지/인버스/액티브/채권 제외(1차 look-through). 대표 ETF 1개 = MarCap(AUM) 최대.
⛔ TER/realized-TE/tax-FX 정밀 + look-through passive 여부 = Phase 1-3/2 (운용사 공시 fetch). 본 1차 = AUM/유동성.
산출 = etf-picks-20260606.json (construction.build_sleeve_decisions etf_picks 입력).
"""
from __future__ import annotations
import json
from pathlib import Path
import warnings; warnings.filterwarnings("ignore")
import FinanceDataReader as fdr

ROOT = Path(__file__).resolve().parent

# 한국 ETF fallback sleeve → 테마 키워드 (ledger 라우팅 "ETF")
THEME_KW = {
    "financial": "은행", "battery": "2차전지", "bio": "바이오",
    "shipbuilding": "조선", "consumer": "소비재", "chemical": "화학", "auto": "자동차",
}
# 1차 look-through 제외 (passive broad basket 아님 = active/factor tilt·집중·파생·해외 추종)
EXCLUDE = [
    "레버리지", "인버스", "2X", "3X", "액티브", "채권", "커버드콜", "TR", "선물",          # 파생/active
    "고배당", "배당", "TOP10", "TOP3", "TOP5", "플러스", "동일가중", "가치", "성장", "모멘텀",  # factor/집중 tilt
    "미국", "차이나", "중국", "글로벌", "일본", "유럽", "인도", "S&P", "나스닥", "선진국",        # 해외 추종(한국 sleeve)
]
# 미국 defensive sub-sector (yfinance, SPDR sector ETF = passive cap-weighted)
US_DEFENSIVE = {"staples": "XLP", "utilities": "XLU", "healthcare": "XLV", "comm_mature": "XLC"}


def pick_kr(etf, kw):
    m = etf[etf["Name"].str.contains(kw, na=False)]
    for ex in EXCLUDE:
        m = m[~m["Name"].str.contains(ex, na=False)]
    if m.empty:
        return None
    # ★대표성+유동성 = MarCap(AUM 근사) 최대. ★리턴(EarningRate) 배제.
    m = m.sort_values("MarCap", ascending=False)
    top = m.iloc[0]
    cands = m.head(3)[["Symbol", "Name", "MarCap", "Amount"]].to_dict("records")
    return {
        "ticker": str(top["Symbol"]), "name": str(top["Name"]),
        "aum_marcap": float(top["MarCap"]), "amount": float(top["Amount"]),
        "nav": float(top["NAV"]), "holdings_source": "FDR",
        "look_through": "passive 추정(액티브/파생 제외 필터). Phase 1-3 운용사 PDF 확정",
        "candidates_top3": cands,
    }


def main():
    etf = fdr.StockListing("ETF/KR")
    picks = {}
    for sleeve, kw in THEME_KW.items():
        p = pick_kr(etf, kw)
        picks[sleeve] = p

    # 미국 defensive sub-sector (ticker 고정 = SPDR passive)
    us = {}
    try:
        import yfinance as yf
        for sub, tk in US_DEFENSIVE.items():
            info = yf.Ticker(tk).get_info()
            us[sub] = {"ticker": tk, "aum": info.get("totalAssets"),
                       "name": info.get("longName", tk), "holdings_source": "yfinance"}
    except Exception as e:
        us = {"error": str(e), "tickers": US_DEFENSIVE}

    out = {
        "meta": {
            "purpose": "약변별 sleeve 테마 ETF 1차 선정 (Phase 1-2)",
            "기준": "대표성+유동성(MarCap≈AUM, Amount), ★리턴(EarningRate) 배제, 레버리지/인버스/액티브 제외",
            "미완": "TER/realized-TE/tax-FX + look-through passive 확정 = Phase 1-3/2 (운용사 PDF)",
        },
        "kr_picks": picks,
        "us_defensive_subsector": us,
    }
    fp = ROOT / "etf-picks-20260606.json"
    fp.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    import sys; sys.stdout.reconfigure(encoding="utf-8")
    print(f"Saved {fp}\n")
    print("=== 한국 약변별 sleeve 테마 ETF 1차 선정 (AUM 최대, 리턴 배제) ===")
    for sl, p in picks.items():
        if p:
            print(f"  {sl:12s} → {p['ticker']} {p['name'][:24]:24s} AUM={p['aum_marcap']:>7.0f}억 Amt={p['amount']:>8.0f}")
        else:
            print(f"  {sl:12s} → ★ETF 부재 (EW fallback)")
    print("\n=== 미국 defensive sub-sector ETF ===")
    if "error" not in us:
        for sub, p in us.items():
            aum = p.get("aum"); aum_s = f"{aum/1e9:.1f}B" if aum else "?"
            print(f"  {sub:12s} → {p['ticker']} AUM={aum_s}")
    else:
        print(f"  yfinance fetch 실패: {us['error'][:60]} → ticker 고정 {us['tickers']}")


if __name__ == "__main__":
    main()
