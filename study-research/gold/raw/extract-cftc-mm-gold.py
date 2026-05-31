#!/usr/bin/env python3
"""CFTC f_year.txt zip 에서 gold 088691 managed-money net long 추출."""
import csv
import io
import json
import zipfile
from pathlib import Path

RAW = Path(__file__).resolve().parent
ZIPS = sorted(RAW.glob("cftc_*.zip"))
GOLD_CODE = "088691"

rows = []
for zp in ZIPS:
    with zipfile.ZipFile(zp) as zf:
        with zf.open("f_year.txt") as fh:
            txt = io.TextIOWrapper(fh, encoding="utf-8", errors="replace")
            reader = csv.DictReader(txt)
            for r in reader:
                code = r.get("CFTC_Contract_Market_Code", "").strip()
                if code != GOLD_CODE:
                    continue
                name = r.get("Market_and_Exchange_Names", "").strip()
                if "GOLD" not in name.upper():
                    continue
                date = r.get("Report_Date_as_YYYY-MM-DD", "").strip()
                try:
                    long_all = int(r.get("M_Money_Positions_Long_All", "0") or 0)
                    short_all = int(r.get("M_Money_Positions_Short_All", "0") or 0)
                    spread_all = int(r.get("M_Money_Positions_Spread_All", "0") or 0)
                    oi = int(r.get("Open_Interest_All", "0") or 0)
                except ValueError:
                    continue
                rows.append({
                    "date": date,
                    "name": name,
                    "mm_long": long_all,
                    "mm_short": short_all,
                    "mm_spread": spread_all,
                    "mm_net_long": long_all - short_all,
                    "oi": oi,
                })

rows.sort(key=lambda x: x["date"])

out_csv = RAW / "cftc_mm_gold.csv"
with out_csv.open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["date", "name", "mm_long", "mm_short", "mm_spread", "mm_net_long", "oi"])
    w.writeheader()
    w.writerows(rows)

summary = {
    "n_rows": len(rows),
    "date_min": rows[0]["date"] if rows else None,
    "date_max": rows[-1]["date"] if rows else None,
    "names_unique": sorted({r["name"] for r in rows}),
    "mm_net_long_min": min((r["mm_net_long"] for r in rows), default=None),
    "mm_net_long_max": max((r["mm_net_long"] for r in rows), default=None),
    "mm_net_long_first": rows[0]["mm_net_long"] if rows else None,
    "mm_net_long_last": rows[-1]["mm_net_long"] if rows else None,
    "out_csv": str(out_csv),
}
print(json.dumps(summary, indent=2, ensure_ascii=False))
