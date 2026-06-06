"""ETF look-through 테스트 (약변별 sleeve fallback, 자문 D3 안전장치, 2026-06-06).

검증기준:
- core/risk_gate.etf_lookthrough_exposures: 섹터 분해 + 단일발행체 direct+via-ETF 합산 + 미커버 잔차 보수
- core/risk_gate.holdings_pit_stale: max-lag 초과/비-datetime → stale(보수 True)
- stock/order_assembly: env ETF_FALLBACK off → 기존 경로 byte-identical / on → look-through gate_kwargs override
  · 신선 holdings → 섹터·단일발행체 분해
  · stale/holdings 부재 → wrapper 통째 1섹터 보수(=tw)
  · 단일발행체 direct+via-ETF 합산 cap 초과 → rejected
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.risk_gate import (  # noqa: E402
    GatedOrderRouter,
    RiskGate,
    etf_lookthrough_exposures,
    holdings_pit_stale,
)
from stock.admission import check_admission, classify_etf_tier  # noqa: E402
from stock.contracts import ProductTier  # noqa: E402
from stock.order_assembly import assemble_stock_orders  # noqa: E402


# ── look-through 분해 단위 ────────────────────────────────────────────

def test_lookthrough_sector_and_issuer_decomposition():
    hold = [
        {"ticker": "105560", "weight": 22.0, "sector": "금융"},
        {"ticker": "055550", "weight": 18.0, "sector": "금융"},
        {"ticker": "005930", "weight": 10.0, "sector": "IT"},
    ]
    r = etf_lookthrough_exposures(0.08, hold, direct_holdings={"005930": 0.02})
    assert abs(r["covered"] - 0.50) < 1e-9
    # 금융 = 0.08×(0.22+0.18) = 0.032
    assert abs(r["by_sector"]["금융"] - 0.032) < 1e-9
    assert abs(r["by_sector"]["IT"] - 0.008) < 1e-9
    # 미커버 50% → unclassified 잔차 0.08×0.5 = 0.04 (정규화 X, 보수 보존)
    assert abs(r["by_sector"]["unclassified"] - 0.04) < 1e-9
    # 단일발행체 005930 = direct 0.02 + via 0.08×0.10 = 0.028
    assert abs(r["by_issuer"]["005930"] - 0.028) < 1e-9
    assert r["top_issuer"][0] == "005930"


def test_lookthrough_pct_and_fraction_autonormalize():
    # weight 가 fraction(0.22)이어도 %(22)와 동일 처리
    r_pct = etf_lookthrough_exposures(0.10, [{"ticker": "A", "weight": 22.0, "sector": "X"}])
    r_frac = etf_lookthrough_exposures(0.10, [{"ticker": "A", "weight": 0.22, "sector": "X"}])
    assert abs(r_pct["by_issuer"]["A"] - r_frac["by_issuer"]["A"]) < 1e-9


def test_lookthrough_empty_holdings_conservative_wrapper():
    r = etf_lookthrough_exposures(0.08, [])
    assert abs(r["by_sector"]["unclassified"] - 0.08) < 1e-9   # wrapper 통째
    assert r["top_issuer"] is None
    assert r["covered"] == 0.0


def test_holdings_pit_stale():
    asof = datetime(2026, 6, 4)
    assert holdings_pit_stale(datetime(2026, 5, 5), asof, 20) is True    # 30일 > 20
    assert holdings_pit_stale(datetime(2026, 5, 30), asof, 20) is False  # 5일 <= 20
    assert holdings_pit_stale(None, asof, 20) is True                    # 비-datetime 보수
    assert holdings_pit_stale(datetime(2026, 5, 30), None, 20) is True


# ── order_assembly wire (env gated) ──────────────────────────────────

_HOLD = [
    {"ticker": "105560", "weight": 22.0, "sector": "금융"},
    {"ticker": "055550", "weight": 18.0, "sector": "금융"},
]


def _run(decision, *, current_weight=0.0, sector_weight=0.0, asof=datetime(2026, 6, 4)):
    router = GatedOrderRouter(gate=RiskGate())
    return assemble_stock_orders(
        [decision], router=router, dry_run=True,
        nav=1.0, current_weight=current_weight, sector_weight=sector_weight, asof=asof,
    )[0]


def test_order_assembly_etf_off_byte_identical(monkeypatch):
    monkeypatch.delenv("ETF_FALLBACK", raising=False)
    dec = {"ticker": "091170", "target_weight": 0.08, "instrument_type": "ETF",
           "holdings": _HOLD, "holdings_asof": datetime(2026, 6, 1)}
    rec = _run(dec)
    # env off → look-through 미작동(기존 경로) → lookthrough 키 부재
    assert "lookthrough" not in rec


def test_order_assembly_etf_on_fresh_decompose(monkeypatch):
    monkeypatch.setenv("ETF_FALLBACK", "on")
    dec = {"ticker": "091170", "target_weight": 0.08, "instrument_type": "ETF",
           "holdings": _HOLD, "holdings_asof": datetime(2026, 6, 1)}
    rec = _run(dec)
    lt = rec["lookthrough"]
    assert lt["stale"] is False
    # 부분 holdings(covered=0.4) → 미커버 0.6 이 unclassified(0.08×0.6=0.048)로 최대 섹터(보수).
    assert abs(lt["covered"] - 0.4) < 1e-9
    assert abs(lt["max_sector_eff"] - 0.048) < 1e-9
    assert lt["top_issuer"] == "105560"
    assert abs(lt["top_issuer_eff"] - 0.0176) < 1e-9  # 0.08×0.22


def test_order_assembly_etf_on_stale_conservative(monkeypatch):
    monkeypatch.setenv("ETF_FALLBACK", "on")
    dec = {"ticker": "091170", "target_weight": 0.08, "instrument_type": "ETF",
           "holdings": _HOLD, "holdings_asof": datetime(2026, 1, 1)}  # 90일 초과
    rec = _run(dec)
    assert rec["lookthrough"]["stale"] is True
    assert abs(rec["lookthrough"]["max_sector_eff"] - 0.08) < 1e-9   # wrapper 통째 보수
    assert "top_issuer" not in rec["lookthrough"]   # stale → 단일발행체 미합산


def test_order_assembly_etf_on_no_holdings_conservative(monkeypatch):
    monkeypatch.setenv("ETF_FALLBACK", "on")
    dec = {"ticker": "XLP", "target_weight": 0.08, "instrument_type": "ETF",
           "holdings_asof": datetime(2026, 6, 1)}
    rec = _run(dec)
    assert rec["lookthrough"]["covered"] == 0.0
    assert abs(rec["lookthrough"]["max_sector_eff"] - 0.08) < 1e-9


def test_order_assembly_etf_on_issuer_cap_breach_rejected(monkeypatch):
    monkeypatch.setenv("ETF_FALLBACK", "on")
    dec = {"ticker": "091170", "target_weight": 0.08, "instrument_type": "ETF",
           "holdings": _HOLD, "holdings_asof": datetime(2026, 6, 1)}
    # 직접 9% 보유 + via-ETF 1.76% → current_weight 합산 후 proposed 8% → max_weight_single 10% 초과
    rec = _run(dec, current_weight=0.09)
    assert str(rec["verdict"]).endswith("REJECTED") or rec["status"] == "rejected"


# ── admission tier 분류 (Phase 4-3) ──────────────────────────────────

def test_classify_etf_tier_passive_vs_leverage():
    # 약변별 fallback = 일반 passive → CORE_ALLOWED
    for name in ("KODEX 은행", "KODEX 2차전지산업", "KODEX 바이오",
                 "HANARO Fn조선해운", "KODEX 자동차", "TIGER 200 에너지화학"):
        assert classify_etf_tier(name) == ProductTier.CORE_ALLOWED, name
    # 레버리지/인버스/ETN → TIER2_DEFAULT_OFF (거절 보존)
    for name in ("KODEX 레버리지", "KODEX 인버스2X", "KODEX 200선물인버스2X",
                 "TIGER 미국S&P500 레버리지", "신한 ETN 곱버스"):
        assert classify_etf_tier(name) == ProductTier.TIER2_DEFAULT_OFF, name


def test_admission_passive_etf_admitted_leverage_rejected():
    # passive ETF (CORE_ALLOWED) → admit
    r1 = check_admission("091170", ProductTier.CORE_ALLOWED, "KR", krx_status=None)
    assert bool(r1) is True
    # 레버리지 ETF (TIER2, allowlist 없음) → 거절
    r2 = check_admission("122630", ProductTier.TIER2_DEFAULT_OFF, "KR", krx_status=None)
    assert bool(r2) is False
