"""바이오 universe 정제 — Marcap (FDR listing) + 키워드 + sub-cluster 분류.

목적:
1. FDR Marcap 기반 시총순 정렬 → 상위 20개 main universe + 30개 extended (총 50)
2. sub-cluster 4분류: CMO·CDMO / 신약 / 바이오시밀러 / 의료기기·진단
3. 대표 ticker (207940, 068270, 326030) 포함 확인
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

IN = Path(__file__).resolve().parent.parent / "data" / "universe_bio_2026-05-29.csv"
OUT = Path(__file__).resolve().parent.parent / "data" / "universe_bio_filtered.csv"


# sub-cluster 키워드 사전 (한국 KRX 상장 바이오 통례 매핑)
CLUSTER_KEYWORDS = {
    "CMO_CDMO": ["삼성바이오로직스", "에스티팜", "프레스티지바이오로직스", "바이넥스", "이엔코퍼레이션"],
    "biosimilar": ["셀트리온", "셀트리온헬스케어", "동아에스티"],
    "novel_drug": ["SK바이오팜", "한미약품", "유한양행", "한올바이오파마", "HLB",
                   "큐로셀", "툴젠", "지놈앤컴퍼니", "메지온", "에이비엘바이오"],
    "diagnostic_device": ["씨젠", "인바디", "수젠텍", "랩지노믹스", "EDGC", "엠지메드"],
    "traditional_pharma": ["JW중외제약", "녹십자", "대웅제약", "동국제약", "광동제약", "보령", "종근당", "일양약품", "환인제약"],
}


def classify(name: str) -> str:
    """종목명 → sub-cluster 분류 (1차 키워드, 미매칭 = 'other_bio')."""
    for cluster, kws in CLUSTER_KEYWORDS.items():
        for kw in kws:
            if kw in name:
                return cluster
    # 후속: 키워드 일반화
    if any(k in name for k in ["바이오", "신약"]):
        return "novel_drug"  # 디폴트 신약 후보
    if any(k in name for k in ["제약"]):
        return "traditional_pharma"
    if any(k in name for k in ["메디", "헬스", "진단"]):
        return "diagnostic_device"
    return "other_bio"


def main():
    df = pd.read_csv(IN, encoding="utf-8-sig", dtype={"Code": str})
    # Marcap 정렬 + 상위 50
    df = df.sort_values("Marcap", ascending=False).reset_index(drop=True)
    df["cluster"] = df["Name"].apply(classify)
    df["rank"] = df.index + 1

    # 시총 단위: 원
    df["marcap_b_krw"] = (df["Marcap"] / 1e9).round(1)  # 십억원

    keep = df.head(50)[["Code", "Name", "Market", "cluster", "marcap_b_krw", "rank"]].copy()
    keep.to_csv(OUT, index=False, encoding="utf-8-sig")

    print(f"\n바이오 universe (Top 50, 시총순):")
    print(keep.to_string(index=False))

    print("\n\nCluster 별 분포:")
    print(keep.groupby("cluster").agg(n=("Code", "count"), total_b=("marcap_b_krw", "sum")).sort_values("total_b", ascending=False))

    # 대표 ticker 확인
    repr_tks = ["207940", "068270", "326030"]
    print("\n대표 ticker 확인:")
    for tk in repr_tks:
        row = keep[keep["Code"] == tk]
        if not row.empty:
            r = row.iloc[0]
            print(f"  {tk} {r['Name']}: rank={r['rank']}, cluster={r['cluster']}, cap={r['marcap_b_krw']}B KRW")
        else:
            print(f"  {tk}: top 50 외")


if __name__ == "__main__":
    main()
