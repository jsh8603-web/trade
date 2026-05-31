"""바이오 Layer 3 산업 특화 지표 fetch.

frame.md §3 바이오 Layer 3 후보:
- CMO 가동률 (× 무료 source 없음 → 삼바·셀트리온 분기 IR/공시 수치 필요, 데이터 sparse)
- FDA 승인 이벤트 (○ openFDA drugsfda API 무료)
- 글로벌 임상 진행 단계 (clinicaltrials.gov API 무료)
- 신약 pipeline IND/NDA 이벤트 (△ FDA + DART 한국 임상 IND)
- USDKRW (○ 이미 fetch)

본 단계: FDA 승인 이벤트 (월별 신규 NDA approval count) + KOSPI 헬스케어 sector index (^KS200 health 또는 KRX 헬스케어).

★ 데이터 제약: 한국 specific 무료 industry cycle 지표 가용성 낮음. 본 단계 = 글로벌 proxy (FDA approval / KRX healthcare ETF).
"""
from __future__ import annotations
from pathlib import Path
import json
import time
import sys
from urllib.request import Request, urlopen
from urllib.parse import urlencode

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
START = "2014-01-01"
END = "2026-05-29"


def fetch_fda_approvals_monthly():
    """openFDA drugsfda API → 월별 신규 NDA approval count.

    Endpoint: https://api.fda.gov/drug/drugsfda.json?search=submissions.submission_status_date:[20140101+TO+20260601]&count=submissions.submission_status_date
    """
    print("=== FDA approvals (월별) ===")
    out_path = DATA_DIR / "fda_approvals_monthly.csv"
    if out_path.exists():
        print(f"  cache hit: {out_path}")
        return pd.read_csv(out_path, parse_dates=["date"])

    base = "https://api.fda.gov/drug/drugsfda.json"
    # count=submissions.submission_status_date → 일별 count facets
    params = {
        "search": "submissions.submission_status:AP",  # AP = Approved
        "count": "submissions.submission_status_date",
        "limit": 1000,
    }
    url = f"{base}?{urlencode(params)}"
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (research-bot)"})
        with urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
        results = data.get("results", [])
        if not results:
            print(f"  empty: {data}")
            return pd.DataFrame()
        # raw: [{"time": "20140101", "count": N}, ...]
        df = pd.DataFrame(results)
        df["date"] = pd.to_datetime(df["time"], format="%Y%m%d", errors="coerce")
        df = df.dropna(subset=["date"])
        df = df.set_index("date").sort_index()
        # 월별 합계
        monthly = df["count"].resample("ME").sum().to_frame("fda_approvals_count")
        monthly.index.name = "date"
        monthly.reset_index().to_csv(out_path, index=False)
        print(f"  저장: {out_path} (rows={len(monthly)}, range={monthly.index.min()} ~ {monthly.index.max()})")
        return monthly.reset_index()
    except Exception as e:
        print(f"  FDA API 실패: {e}")
        return pd.DataFrame()


def fetch_clinical_trials_monthly():
    """clinicaltrials.gov API v2 → 월별 신규 study 등록 count.

    한국 sponsor 임상 = 한국 바이오 pipeline proxy.
    API v2: https://clinicaltrials.gov/api/v2/studies?query.cond=&query.term=&filter.overallStatus=&fields=&pageSize=
    """
    print("\n=== clinicaltrials.gov 신규 등록 (월별) ===")
    out_path = DATA_DIR / "clinical_trials_monthly.csv"
    if out_path.exists():
        print(f"  cache hit: {out_path}")
        return pd.read_csv(out_path, parse_dates=["date"])

    # v2 API: studies endpoint 의 firstPostDate facet — direct facet 없으므로 연도별 pagination
    # 간이 방법: 글로벌 신규 등록 count (월별 aggregate 가 직접 facet API 미제공)
    # → 대신 yearly count 만 fetch, 후속 분석은 yearly aggregate 사용
    base = "https://clinicaltrials.gov/api/v2/stats/size"
    try:
        req = Request(base, headers={"User-Agent": "Mozilla/5.0 (research-bot)"})
        with urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
        print(f"  stats total: {data.get('totalStudies', 'NA')}")
        # facet API 부재 → manual yearly count 통계 사용 (논문 인용)
        # 글로벌 신규 등록 = ~30k/y, monthly proxy = total / 12
        # 본 분석은 yearly 단위만 가능 → frame.md 5게이트 N gate 미달 (월간 N<24 어려움)
        # → 본 지표 skip + 차후 KRX 헬스케어 ETF 로 대체
        print(f"  WARN: clinicaltrials.gov v2 facet API 미제공 → 본 지표 skip (Tier 3 데이터 sparse)")
        return pd.DataFrame()
    except Exception as e:
        print(f"  실패: {e}")
        return pd.DataFrame()


def fetch_krx_healthcare_etf():
    """KODEX 헬스케어 ETF (266420) 또는 TIGER 헬스케어 (143860) → 산업 평균 proxy."""
    print("\n=== KRX 헬스케어 ETF (산업 proxy) ===")
    import FinanceDataReader as fdr

    etfs = {
        "266420": "kodex_healthcare",  # KODEX 헬스케어
        "143860": "tiger_healthcare",  # TIGER 헬스케어
        "227540": "tiger_kor_bio",     # TIGER 200 헬스케어 (구 250)
        "395160": "kbstar_kbiocon",    # KBSTAR 코스닥150 바이오테크
        "364980": "tiger_kbiocon",     # TIGER 코스닥150 바이오테크
    }
    frames = []
    for tk, name in etfs.items():
        try:
            df = fdr.DataReader(tk, START, END)
            if df.empty:
                print(f"  {tk} {name}: empty")
                continue
            df = df[["Close"]].copy()
            df.columns = [name]
            frames.append(df)
            print(f"  {tk} {name}: {len(df)} rows ({df.index.min().date()} ~ {df.index.max().date()})")
        except Exception as e:
            print(f"  {tk} {name}: ERROR {e}")
        time.sleep(0.1)

    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, axis=1)
    out.index.name = "date"
    out_path = DATA_DIR / "healthcare_etfs.parquet"
    out.to_parquet(out_path)
    print(f"  저장: {out_path} (shape={out.shape})")
    return out


if __name__ == "__main__":
    fda = fetch_fda_approvals_monthly()
    if isinstance(fda, pd.DataFrame) and not fda.empty:
        print(f"  최신 6개월:\n{fda.tail(6).to_string(index=False)}")

    fetch_clinical_trials_monthly()
    fetch_krx_healthcare_etf()
