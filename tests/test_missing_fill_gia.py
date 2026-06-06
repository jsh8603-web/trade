"""WIRE3.5-Gi-A 테스트: robust_z missing_fill (결측 펀더멘털 매수편향 제거).

검증기준 (자문 R1 만장일치 2026-06-05):
- default "neutral" = 결측 z=0(중앙) — 기존 동작 byte-identical
- "sector_min" = 결측 z = present 하위 분위(음수) — 매수편향 제거, 점추정(-2) 회피
- 결측 없으면 두 모드 동일 (default off byte-identical 원칙)
- select_cross_sectional config.missing_fill 전파 → 결측 종목 rank 하락
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stock.cross_sectional_selection import (
    SelectionConfig,
    composite_cheapness_z,
    robust_z,
    select_cross_sectional,
)


def test_neutral_missing_is_zero():
    """default neutral: 결측(None) z = 0 (중앙, 기존 동작)."""
    vals = [1.0, 2.0, 3.0, 4.0, 5.0, None]
    z = robust_z(vals, missing_fill="neutral")
    assert z[-1] == 0.0


def test_sector_min_missing_is_low_quantile():
    """sector_min: 결측 z = present 하위 분위(음수) → 중앙 0 아닌 최악 근처."""
    vals = [1.0, 2.0, 3.0, 4.0, 5.0, None]
    z = robust_z(vals, missing_fill="sector_min")
    present = [zz for v, zz in zip(vals, z) if v is not None]
    assert z[-1] <= min(present) + 1e-9      # 하위 10% 분위 = 최저 근처
    assert z[-1] < 0.0                        # 매수편향 제거 (중앙 위가 아님)


def test_byte_identical_when_no_missing():
    """결측 없으면 neutral == sector_min (default off byte-identical)."""
    vals = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert robust_z(vals, missing_fill="neutral") == robust_z(vals, missing_fill="sector_min")


def test_composite_default_byte_identical():
    """composite default(neutral) = 기존 산출 동일 (결측 있어도 미지정이면 0 fill)."""
    panel = {"pbr": {"A": 1.0, "B": 2.0, "C": None}}
    base = composite_cheapness_z(panel, {"pbr": -1})
    explicit = composite_cheapness_z(panel, {"pbr": -1}, missing_fill="neutral")
    assert base == explicit
    assert base["C"] == 0.0                   # 결측 = 중앙


def test_composite_sector_min_penalizes_missing():
    """sector_min: 결측 종목 composite z 가 neutral(0) 보다 낮음 (불리)."""
    panel = {"pbr": {"A": 0.5, "B": 1.0, "C": 2.0, "D": 5.0, "E": None}}
    neu = composite_cheapness_z(panel, {"pbr": -1}, missing_fill="neutral")
    smin = composite_cheapness_z(panel, {"pbr": -1}, missing_fill="sector_min")
    # pbr sign=-1 → 저PBR 쌈. 결측 E 는 sector_min 시 "비쌈"(하위 cheapness) 강제 → z 하락
    assert smin["E"] < neu["E"]


def test_select_missing_fill_drops_rank():
    """select_cross_sectional: config.missing_fill='sector_min' 시 결측 종목 매수 후보서 밀림."""
    panel = {"pbr": {t: v for t, v in
                     [("A", 0.6), ("B", 0.8), ("C", 1.0), ("D", 1.2), ("E", 1.5),
                      ("F", 2.0), ("G", 3.0), ("H", 4.0), ("I", 5.0), ("J", 6.0),
                      ("K", 7.0), ("MISS", None)]}}
    caps = {t: 1e9 for t in panel["pbr"]}
    cfg_neu = SelectionConfig(top_k=10, market_cap_floor=0.0, missing_fill="neutral")
    cfg_min = SelectionConfig(top_k=10, market_cap_floor=0.0, missing_fill="sector_min")
    neu = {c.ticker: c.rank for c in select_cross_sectional(panel, caps, {"pbr": -1}, config=cfg_neu)}
    smin = {c.ticker: c.rank for c in select_cross_sectional(panel, caps, {"pbr": -1}, config=cfg_min)}
    # sector_min 에선 MISS rank 가 neutral 대비 같거나 더 큼(=덜 우선) — 매수편향 제거
    assert smin["MISS"] >= neu["MISS"]
