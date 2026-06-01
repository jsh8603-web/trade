"""scripts/build_panel.py — bitemporal PIT 패널 빌드 turnkey (Phase2 T1, WP-T1-E).

PANEL-SCHEMA-phase2.md §1 파일 레이아웃 산출:
  panel/{market}/{vintage}.parquet + panel/_manifest/{vintage}.json

usage:
  python scripts/build_panel.py --market KR --start 2020-01 --end 2023-12 \
      --firms 005930,000660 [--freq M]

credential(DART/EDGAR/quote) 부재 시 빈 패널 + 경고(go-live N-P4 의존). 조립 로직·
PIT 보호·vintage content-hash 산출은 credential 무관(코드경로 검증 가능).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# 프로젝트 루트 import 경로
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.data.pit_panel import PanelAssembler, RoutingFundamentalsProvider  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("build_panel")

_ROOT = Path(__file__).resolve().parent.parent
_PANEL_DIR = _ROOT / "panel"


def month_ends(start: str, end: str) -> List[datetime]:
    """'YYYY-MM' 범위 → 월말 datetime 목록."""
    import pandas as pd
    rng = pd.date_range(start=f"{start}-01", end=f"{end}-28", freq="ME")
    return [d.to_pydatetime() for d in rng]


def _build_providers(market: str):
    """market 별 provider 조립 (credential 부재 시 None → 빈 결과)."""
    dart = edgar = krx = None
    try:
        from stock.data.dart_provider import DartXbrlProvider
        dart = DartXbrlProvider()
    except Exception as exc:
        logger.info("DART provider 미구성: %s", exc)
    try:
        from stock.data.edgar_provider import EdgarXbrlProvider
        edgar = EdgarXbrlProvider()
    except Exception as exc:
        logger.info("EDGAR provider 미구성: %s", exc)
    if market == "KR":
        try:
            from stock.data.krx_universe import KrxStatusProvider
            krx = KrxStatusProvider()
        except Exception as exc:
            logger.info("KRX status provider 미구성: %s", exc)
    adapter = RoutingFundamentalsProvider(dart_provider=dart, edgar_provider=edgar)
    return adapter, krx


def content_hash(df) -> str:
    """패널 내용 content-hash (재현성 vintage). 동일 입력 → 동일 vintage."""
    payload = df.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def build(
    market: str, start: str, end: str, firms: List[str],
    sys_time: Optional[datetime] = None,
) -> Path:
    adapter, krx = _build_providers(market)
    dates = month_ends(start, end)
    asm = PanelAssembler(
        fundamentals_adapter=adapter,
        krx_status_provider=krx,
        quote_fn=None,   # 실 quote provider = go-live wire (N-P4); 부재 시 멀티플 NULL
    )
    panel = asm.assemble(firms, dates, sys_time=sys_time)
    logger.info("패널 조립 완료: %d rows (firms=%d × dates=%d)",
                len(panel), len(firms), len(dates))

    vintage = content_hash(panel) if not panel.empty else "empty"
    out_dir = _PANEL_DIR / market
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{vintage}.parquet"
    panel.to_parquet(out_path, index=False)

    manifest_dir = _PANEL_DIR / "_manifest"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "market": market, "vintage": vintage, "rows": int(len(panel)),
        "firms": firms, "start": start, "end": end,
        "build_sys_time": (sys_time or datetime.utcnow()).isoformat(),
        "schema_contract": "PANEL-SCHEMA-phase2.md",
    }
    (manifest_dir / f"{vintage}.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("저장: %s (vintage=%s)", out_path, vintage)
    return out_path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="bitemporal PIT 패널 빌드")
    ap.add_argument("--market", required=True, choices=["KR", "US"])
    ap.add_argument("--start", required=True, help="YYYY-MM")
    ap.add_argument("--end", required=True, help="YYYY-MM")
    ap.add_argument("--firms", required=True, help="콤마구분 ticker")
    args = ap.parse_args(argv)
    firms = [t.strip() for t in args.firms.split(",") if t.strip()]
    build(args.market, args.start, args.end, firms)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
