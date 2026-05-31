"""바이오 산업 universe probe — pykrx + FDR 로 KRX 상장 바이오 종목 시총 / 섹터 분포 확인.

목적: frame.md §1 Tier 3 바이오 대표 ticker (207940 삼성바이오로직스, 068270 셀트리온, 326030 SK바이오팜) +
sub-cluster (CMO / 신약 / 바이오시밀러 / 임상단계별) 확장 후보 식별.

산출: data/universe_snapshot_{as_of}.csv (ticker, name, market, market_cap, sector_wics)
"""
from __future__ import annotations
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

OUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_DIR.mkdir(exist_ok=True)


def fetch_universe_snapshot(as_of: date) -> pd.DataFrame:
    """FDR + pykrx 로 KOSPI/KOSDAQ 전체 종목 + 시총 + WICS 섹터 매핑."""
    try:
        import FinanceDataReader as fdr
        from pykrx import stock as pk
    except ImportError as e:
        print(f"ImportError: {e}")
        return pd.DataFrame()

    # 1. FDR StockListing KRX 전체
    try:
        listing = fdr.StockListing("KRX")
        print(f"FDR KRX listing: {len(listing)} rows, cols={list(listing.columns)[:15]}")
    except Exception as e:
        print(f"FDR StockListing 실패: {e}")
        return pd.DataFrame()

    # 2. pykrx 시총 (당일 또는 직전 영업일)
    date_str = as_of.strftime("%Y%m%d")
    try:
        cap_kospi = pk.get_market_cap_by_ticker(date_str, market="KOSPI")
        cap_kosdaq = pk.get_market_cap_by_ticker(date_str, market="KOSDAQ")
        cap = pd.concat([cap_kospi, cap_kosdaq])
        cap.index.name = "Code"
        print(f"pykrx market cap: KOSPI {len(cap_kospi)} + KOSDAQ {len(cap_kosdaq)} = {len(cap)}")
    except Exception as e:
        print(f"pykrx market cap 실패: {e}")
        cap = pd.DataFrame()

    # 3. WICS 섹터 매핑 (pykrx)
    try:
        # pykrx 는 sector classification 을 산업별 코드로 제공
        # WICS 분류는 KRX 산업분류 코드 기반: 제약·바이오 = G35
        # 우선 KRX 산업분류로 fallback
        sectors = []
        for market in ["KOSPI", "KOSDAQ"]:
            try:
                df_sec = pk.get_market_sector_classifications(date_str, market=market)
                df_sec["market"] = market
                sectors.append(df_sec)
            except Exception as e:
                print(f"pykrx sector {market} 실패: {e}")
        if sectors:
            sec_df = pd.concat(sectors, ignore_index=True)
            print(f"pykrx sector: {len(sec_df)} rows, cols={list(sec_df.columns)[:10]}")
        else:
            sec_df = pd.DataFrame()
    except Exception as e:
        print(f"sector 분류 전체 실패: {e}")
        sec_df = pd.DataFrame()

    return listing, cap, sec_df


def filter_bio(listing: pd.DataFrame, cap: pd.DataFrame, sec_df: pd.DataFrame) -> pd.DataFrame:
    """바이오 후보 필터: 종목명 키워드 + WICS 제약·바이오 섹터."""
    # 종목명 키워드 (1차)
    bio_keywords = ["바이오", "제약", "팜", "셀트리온", "메디", "헬스", "신약", "임상", "백신", "유전자"]
    if "Name" in listing.columns:
        name_col = "Name"
    elif "Symbol" in listing.columns:
        name_col = "Symbol"
    else:
        print(f"종목명 컬럼 미존재: {list(listing.columns)}")
        return pd.DataFrame()

    mask_name = listing[name_col].str.contains("|".join(bio_keywords), na=False, regex=True)
    by_name = listing[mask_name].copy()

    # WICS 섹터 (2차 - 가능 시)
    if not sec_df.empty and "업종명" in sec_df.columns:
        bio_sectors = sec_df[sec_df["업종명"].str.contains("제약|바이오|의약", na=False, regex=True)]
        bio_codes = set(bio_sectors["티커"].tolist()) if "티커" in bio_sectors.columns else set()
        print(f"WICS 제약·바이오 섹터 ticker: {len(bio_codes)}")
        by_sec = listing[listing["Code"].isin(bio_codes)] if "Code" in listing.columns else pd.DataFrame()
    else:
        by_sec = pd.DataFrame()

    combined = pd.concat([by_name, by_sec]).drop_duplicates(subset="Code" if "Code" in by_name.columns else "Symbol")

    # 시총 join
    code_col = "Code" if "Code" in combined.columns else "Symbol"
    if not cap.empty and "시가총액" in cap.columns:
        combined = combined.merge(cap[["시가총액"]], left_on=code_col, right_index=True, how="left")
    return combined


if __name__ == "__main__":
    as_of = date(2026, 5, 29)  # 직전 영업일
    listing, cap, sec_df = fetch_universe_snapshot(as_of)
    if listing.empty:
        sys.exit(1)

    bio = filter_bio(listing, cap, sec_df)
    print(f"\n바이오 후보: {len(bio)}")
    if "시가총액" in bio.columns:
        bio = bio.sort_values("시가총액", ascending=False)
        print(bio.head(30)[["Code" if "Code" in bio.columns else "Symbol",
                            "Name" if "Name" in bio.columns else "Symbol",
                            "시가총액"]])
    else:
        cols = [c for c in ["Code", "Name", "Symbol", "Market"] if c in bio.columns]
        print(bio.head(30)[cols])

    out = OUT_DIR / f"universe_bio_{as_of.isoformat()}.csv"
    bio.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\n저장: {out}")
