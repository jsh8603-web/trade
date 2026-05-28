"""stock/_smoke_test.py — 핵심 모듈 동작 검증 (외부 의존성 0, 표준 라이브러리만).

설계 계약이 실제로 *동작*하는지 확인:
  1) PIT 어댑터가 백테스트에서 미래/restated 데이터 차단
  2) valuation 이 내재가치 밴드 산출
  3) value_trigger 2단 게이트 — 기회 vs value-trap vs 가격만빠짐 구분 + H22 abstain
  4) factor_attribution 회귀 + enum + 메타라벨링 + 군집
"""

from __future__ import annotations

from datetime import datetime, timedelta

from stock.contracts import (
    Fundamentals, FilingSource, MarketQuote, RunMode, FailureReason, ValueVerdict,
)
from stock.data.fundamentals_adapter import (
    PITFundamentalsAdapter, InMemoryFundamentalsProvider,
)
from stock.valuation import value_stock
from stock.value_trigger import (
    run_value_trigger, HeavyAgent, HeavyAgentVerdict, to_track_decision,
)
from stock.factor_attribution import (
    attribute_trade, ValueTrapMetaLabeler, triple_barrier_label,
    daily_volatility, detect_value_factor_regime,
)


def _mk_fund(ticker, period, ts, source=FilingSource.DART_XBRL, fcf=1e9, rev_g=0.10, ni=8e8):
    return Fundamentals(
        ticker=ticker, fiscal_period=period, filing_timestamp=ts, source=source,
        currency="KRW", as_reported=True,
        revenue=1e10, operating_income=1.2e9, net_income=ni, ebit=1.1e9, ebitda=1.5e9,
        free_cash_flow=fcf, depreciation_amortization=3e8, capital_expenditure=4e8,
        interest_expense=5e7, total_debt=2e9, cash_and_equivalents=1e9,
        shareholders_equity=8e9, book_value=8e9, working_capital=5e8,
        outstanding_shares=1e7, earnings_growth=rev_g, revenue_growth=rev_g,
        book_value_growth=0.04, return_on_invested_capital=0.12, beta=1.1,
    )


# --- Mock heavy agents ---
class OpportunityAgent:
    def judge_value_trap(self, valuation, fundamentals, price_change_pct, context):
        return HeavyAgentVerdict(is_trap=False, confidence=0.8, reasoning="thesis 견고, 패닉셀")


class TrapAgent:
    def judge_value_trap(self, valuation, fundamentals, price_change_pct, context):
        return HeavyAgentVerdict(is_trap=True, confidence=0.9, reasoning="실적쇼크 thesis 붕괴")


def test_pit_adapter():
    as_of = datetime(2023, 6, 1)
    recs = {
        "005930": [
            _mk_fund("005930", "2023Q1", datetime(2023, 5, 15)),         # 가시
            _mk_fund("005930", "2023Q2", datetime(2023, 8, 15)),         # 미래 → 차단
            _mk_fund("005930", "2022Q4", datetime(2023, 3, 1), source=FilingSource.RESTATED),  # restated → 차단
            _mk_fund("005930", "2022Q4", datetime(2023, 3, 1)),          # as-reported 가시
        ]
    }
    adapter = PITFundamentalsAdapter(InMemoryFundamentalsProvider(recs), mode=RunMode.BACKTEST)
    out = adapter.get_pit_fundamentals("005930", as_of)
    periods = [(f.fiscal_period, f.source.value) for f in out]
    assert all(f.visible_at(as_of) for f in out), "미래 데이터 누수!"
    assert all(f.source != FilingSource.RESTATED for f in out), "restated 누수!"
    assert out[0].fiscal_period == "2023Q1", "최신순 정렬 실패"
    print(f"  [PIT] 백테스트 마스킹 OK — 통과 레코드={periods}")


def test_valuation():
    as_of = datetime(2023, 6, 1)
    funds = [_mk_fund("005930", f"2023Q{i}", datetime(2023, 5, 1) - timedelta(days=90 * i))
             for i in range(1, 5)]
    # market_cap 을 낮춰 valuation_gap >= 25% 가 나오도록 (강한 저평가 시나리오)
    quote = MarketQuote("005930", as_of, price=50000, market_cap=6.5e9,
                        price_change_pct=-0.15, price_change_window_days=20)
    vr = value_stock(funds, quote)
    assert vr is not None, "valuation None"
    assert vr.bear_value < vr.base_value < vr.bull_value, "밴드 순서 깨짐"
    print(f"  [VAL] intrinsic={vr.intrinsic_value:,.0f} gap={vr.valuation_gap:.1%} "
          f"WACC={vr.wacc:.1%} 밴드=[{vr.bear_value:,.0f},{vr.bull_value:,.0f}] "
          f"methods={list(vr.method_values.keys())}")
    return vr, funds


def test_value_trigger(vr, funds):
    ml = ValueTrapMetaLabeler(prior_trap_rate=0.2)

    # 1) 기회 (가격↓ + 가치갭 + heavy=기회)
    r_opp = run_value_trigger(vr, funds, price_change_pct=-0.15,
                              heavy_agent=OpportunityAgent(), metalabeler=ml,
                              mode=RunMode.FORWARD)
    # 2) value-trap (heavy=trap)
    r_trap = run_value_trigger(vr, funds, price_change_pct=-0.15,
                               heavy_agent=TrapAgent(), metalabeler=ml,
                               mode=RunMode.FORWARD)
    # 3) 가격 안 빠짐 → 1차 reject
    r_rej = run_value_trigger(vr, funds, price_change_pct=-0.02,
                              heavy_agent=OpportunityAgent(), metalabeler=ml,
                              mode=RunMode.FORWARD)
    # 4) H22 백테스트 → abstain
    r_bt = run_value_trigger(vr, funds, price_change_pct=-0.15,
                             heavy_agent=OpportunityAgent(), metalabeler=ml,
                             mode=RunMode.BACKTEST)

    assert r_opp.verdict == ValueVerdict.OPPORTUNITY and r_opp.direction == "buy", r_opp.verdict
    assert r_trap.verdict == ValueVerdict.VALUE_TRAP and r_trap.direction == "none", r_trap.verdict
    assert r_rej.verdict == ValueVerdict.REJECT, r_rej.verdict
    assert r_bt.verdict == ValueVerdict.ABSTAIN, r_bt.verdict
    # wiring: risk_gate 가 소비하는 Decision dict 변환
    dec = to_track_decision(r_opp)
    assert dec["decision"] == "buy" and dec["_is_buy_candidate"] is True
    assert dec["trade_params"]["ticker"] == "005930"
    dec_trap = to_track_decision(r_trap)
    assert dec_trap["decision"] == "hold" and dec_trap["_is_buy_candidate"] is False

    print(f"  [TRG] opportunity(buy,conf={r_opp.confidence:.2f}) / value_trap(none) / "
          f"reject(가격미달) / backtest=abstain(H22) — 4분기 OK")
    print(f"  [WIRE] to_track_decision: opp={dec['decision']}(candidate={dec['_is_buy_candidate']}) "
          f"trap={dec_trap['decision']} — risk_gate 입력 형태 OK")


def test_attribution():
    # market-β 지배 시나리오: 자산수익이 market 과 강상관
    T = 24
    market = [0.01 * ((-1) ** i) - 0.002 for i in range(T)]
    y_macro = [1.5 * m + 0.0005 * ((-1) ** i) for i, m in enumerate(market)]  # β지배
    a1 = attribute_trade("t1", "AAPL", y_macro, market, holding_return_total=-0.08)

    # idio 지배 (value trap): market 무관, 종목 자체 급락
    y_idio = [0.001 * ((-1) ** i) for i in range(T)]
    y_idio[10] -= 0.15; y_idio[11] -= 0.10   # 종목특이 충격
    a2 = attribute_trade("t2", "XYZ", y_idio, market, holding_return_total=-0.20)

    # 소표본 → unattributed
    a3 = attribute_trade("t3", "ABC", [0.01, -0.01, 0.02], [0.01, 0.0, 0.01],
                         holding_return_total=0.01)

    print(f"  [ATT] macro={a1.failure_reason.value}(r2={a1.confidence:.2f}) / "
          f"idio={a2.failure_reason.value}(r2={a2.confidence:.2f}) / "
          f"small={a3.failure_reason.value}")
    assert a1.failure_reason in (FailureReason.MACRO_REGIME_WRONG, FailureReason.EXECUTION_SLIPPAGE)
    assert a2.failure_reason in (FailureReason.VALUE_TRAP, FailureReason.EXECUTION_SLIPPAGE), \
        f"idio 손실은 VALUE_TRAP/EXECUTION 이어야: {a2.failure_reason}"
    assert a3.failure_reason == FailureReason.UNATTRIBUTED, "소표본은 unattributed 여야"
    return [a1, a2]


def test_metalabel_and_regime(attrs):
    # triple-barrier 라벨
    fwd = [100, 101, 103, 106]   # 상단 익절 먼저
    lbl = triple_barrier_label(100, fwd, volatility=0.02, k_up=2.0, k_down=1.0, side=1)
    vol = daily_volatility([100, 102, 99, 101, 103, 98, 100])
    assert lbl in (0, 1)
    # 스타일 레짐 군집 (VALUE_TRAP 다수)
    from stock.contracts import AttributionResult
    traps = [AttributionResult("x", "t", FailureReason.VALUE_TRAP, {}, 0.5, -0.1)
             for _ in range(6)]
    others = [AttributionResult("y", "t", FailureReason.MACRO_REGIME_WRONG, {}, 0.5, -0.1)
              for _ in range(4)]
    regime = detect_value_factor_regime(traps + others, cluster_threshold=0.4)
    print(f"  [META] tb_label={lbl} daily_vol={vol:.4f} / "
          f"value_regime ratio={regime['value_trap_ratio']} "
          f"unfavorable={regime['regime_unfavorable']} "
          f"haircut={regime['recommended_confidence_haircut']}")
    assert regime["regime_unfavorable"] is True


if __name__ == "__main__":
    print("=== stock brain smoke test ===")
    test_pit_adapter()
    vr, funds = test_valuation()
    test_value_trigger(vr, funds)
    attrs = test_attribution()
    test_metalabel_and_regime(attrs)
    print("=== ALL PASS ===")
