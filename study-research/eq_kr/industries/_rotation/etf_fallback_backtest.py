"""etf_fallback_backtest.py — 약변별 sleeve ETF fallback on/off 성과 비교 (Phase 5, 실 PIT).

목적: 약변별 sleeve(예 financial) 에서 "테마 ETF 1개" vs "구성종목 EW basket" 의 실 PIT 성과를
      비교한다. ETF fallback 이 EW 대비 (a) 추종 충실(TE 작음) (b) 비용 우위(ETF wrapper vs 다종목
      리밸 슬리피지) 인지 실측. shadow-EW 디커플링(core.assume.etf_beta_lock)을 같이 누적.

⛔ 실 PIT 데이터만 (합성·시뮬 금지):
  - 구성종목: study-research/eq_kr/industries/{sleeve}/raw-v3/data/prices.parquet (실 일별 종가)
  - ETF: FDR DataReader (실 일별 종가)
  - 슬리피지: backtest.engine.calculate_slippage (거래대금 비례 임팩트) 재사용
⛔ small-n hedge: 성과 차이는 점추정 단독 박제 금지 — TE/연환산은 표본기간·n 명시 + 방향성 prior.

usage: PYTHONPATH=. python study-research/eq_kr/industries/_rotation/etf_fallback_backtest.py [sleeve] [etf_ticker]
       기본 = financial / 091170(KODEX 은행).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]   # _rotation/industries/eq_kr/study-research/Inv
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtest.engine import CostConfig, calculate_slippage  # noqa: E402
from core.assume.etf_beta_lock import EtfBetaLock  # noqa: E402

_TRADING_DAYS = 252
_REBAL_FREQ_DAYS = 21   # 월 1회 리밸 가정 (EW basket 비중 복원)


def _load_sleeve_ew_returns(sleeve: str):
    """구성종목 prices.parquet → 일별 EW + VW basket 수익률 (실 PIT).

    EW = 균등가중(소형주 = 대형주 동일비중 → size factor 노출). VW = 시총가중(ETF 와 동형 비교군,
    size factor 중립). EW≫ETF 인데 VW≈ETF 면 → EW 우위 = size factor(소형주)지 selection 알파 아님.
    """
    import pandas as pd

    base = ROOT / "study-research" / "eq_kr" / "industries" / sleeve / "raw-v3" / "data"
    px = pd.read_parquet(base / "prices.parquet")
    px = px.sort_index()
    rets = px.pct_change().dropna(how="all")
    # 균등가중 (당일 가용 종목만 평균 = survivorship 보수, 결측 제외)
    ew = rets.mean(axis=1, skipna=True)
    # 시총가중 = universe.parquet Marcap(현재 스냅샷) 고정 비중 buy-and-hold.
    #   ⚠️ 현재 시총 비중을 과거에 적용 = look-ahead(진단 한정, 실거래 비중 아님). ETF 가 대형주
    #   가중이므로 VW≈ETF 면 → EW 우위 = 소형주(size) 효과지 selection 알파 아님(분리 진단).
    vw = None
    try:
        uni = pd.read_parquet(base / "universe.parquet")
        mcap = {str(r["Code"]).zfill(6): float(r["Marcap"]) for _, r in uni.iterrows()
                if r.get("Marcap")}
        cols = [c for c in px.columns if str(c).zfill(6) in mcap]
        if cols:
            wv = pd.Series({c: mcap[str(c).zfill(6)] for c in cols})
            wv = wv / wv.sum()
            vw = (rets[cols] * wv).sum(axis=1, skipna=True)
    except Exception:
        vw = None
    return ew, vw, px.columns.tolist()


def _load_etf_returns(etf_ticker: str, start, end):
    """ETF FDR 실 PIT 일별 수익률 (graceful: 부재 시 None)."""
    try:
        import FinanceDataReader as fdr
        df = fdr.DataReader(etf_ticker, str(start)[:10], str(end)[:10])
        if df is None or len(df) == 0:
            return None
        return df["Close"].pct_change().dropna()
    except Exception as exc:
        print(f"[graceful] ETF {etf_ticker} fetch 실패: {exc}")
        return None


def _annualized(cum_ret: float, n_days: int) -> float:
    if n_days <= 0 or cum_ret <= -1:
        return 0.0
    return (1.0 + cum_ret) ** (_TRADING_DAYS / n_days) - 1.0


def _max_drawdown(equity) -> float:
    peak = equity.cummax()
    dd = (equity - peak) / peak
    return float(dd.min())


def run_backtest(sleeve: str = "financial", etf_ticker: str = "091170") -> dict:
    import numpy as np
    import pandas as pd

    ew_ret, vw_ret, codes = _load_sleeve_ew_returns(sleeve)
    etf_ret = _load_etf_returns(etf_ticker, ew_ret.index.min(), ew_ret.index.max())
    if etf_ret is None:
        return {"ok": False, "reason": "ETF 실 PIT 시세 부재(graceful)", "sleeve": sleeve}

    # 공통 거래일 정렬 (inner join — 양쪽 실측 존재일만)
    cols = {"ew": ew_ret, "etf": etf_ret}
    if vw_ret is not None:
        cols["vw"] = vw_ret
    df = pd.DataFrame(cols).dropna()
    if len(df) < 60:
        return {"ok": False, "reason": f"공통 표본 부족 n={len(df)}", "sleeve": sleeve}

    n = len(df)
    cost = CostConfig()

    # 슬리피지: EW basket = 리밸마다 다종목 교체(거래대금 비례), ETF = 단일 instrument 1회.
    # 보수 근사: EW 리밸 1회 비용 = 종목수 가중 평균 슬리피지, ETF = 1 instrument 슬리피지.
    n_rebal = n // _REBAL_FREQ_DAYS
    # 거래대금 proxy: EW 다종목 분산 → 종목당 거래액 작음(임팩트↑) / ETF 집중 → 임팩트↓.
    ew_slip_1 = calculate_slippage(trade_value=1e8 / max(len(codes), 1), market_volume=1e9, config=cost)
    etf_slip_1 = calculate_slippage(trade_value=1e8, market_volume=5e10, config=cost)
    ew_cost = n_rebal * ew_slip_1 * 2     # 매수+매도 양방향
    etf_cost = n_rebal * etf_slip_1 * 2

    ew_cum = float((1.0 + df["ew"]).prod() - 1.0) - ew_cost
    etf_cum = float((1.0 + df["etf"]).prod() - 1.0) - etf_cost
    ew_eq = (1.0 + df["ew"]).cumprod()
    etf_eq = (1.0 + df["etf"]).cumprod()
    vw_cum = float((1.0 + df["vw"]).prod() - 1.0) - ew_cost if "vw" in df else None

    # tracking error (ETF vs EW 일별 잔차 연환산 표준편차)
    resid = df["etf"] - df["ew"]
    te_annual = float(resid.std() * np.sqrt(_TRADING_DAYS))

    # shadow-EW 디커플링 e-process (etf_beta_lock). ★월별(21일) 집계 resid 로 betting —
    # 일별 잔차는 noise std ≫ signal → betting variance drag 로 양 leg 소멸(검출력 손실).
    # 월별 평균은 일별 noise 평균화 → 지속 디커플링 신호 검출력 회복(empirical-claim autocorr 안전).
    lock = EtfBetaLock(sleeve)
    for i in range(0, n, _REBAL_FREQ_DAYS):
        chunk = df.iloc[i:i + _REBAL_FREQ_DAYS]
        if len(chunk) >= 5:
            lock.observe_decoupling(float(chunk["etf"].mean()), float(chunk["ew"].mean()))

    return {
        "ok": True, "sleeve": sleeve, "etf_ticker": etf_ticker,
        "n_days": n, "n_codes": len(codes),
        "period": f"{str(df.index.min())[:10]} ~ {str(df.index.max())[:10]}",
        "ew_cum": ew_cum, "etf_cum": etf_cum, "vw_cum": vw_cum,
        "vw_annual": _annualized(vw_cum, n) if vw_cum is not None else None,
        "ew_annual": _annualized(ew_cum, n), "etf_annual": _annualized(etf_cum, n),
        "ew_mdd": _max_drawdown(ew_eq), "etf_mdd": _max_drawdown(etf_eq),
        "tracking_error_annual": te_annual,
        "ew_rebal_cost": ew_cost, "etf_rebal_cost": etf_cost,
        "n_rebal": n_rebal,
        "decoupled": lock.decoupled(), "decoupling_reason": lock.decoupling_reason(),
        "e_over": lock.e_over, "e_under": lock.e_under,
    }


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    sleeve = sys.argv[1] if len(sys.argv) > 1 else "financial"
    etf = sys.argv[2] if len(sys.argv) > 2 else "091170"

    print(f"=== ETF fallback 백테스트 (실 PIT): {sleeve} / {etf} ===")
    r = run_backtest(sleeve, etf)
    if not r["ok"]:
        print(f"⚠️ {r['reason']}")
        sys.exit(0)

    print(f"표본: {r['period']} (n={r['n_days']}일, 구성종목 {r['n_codes']}종, 리밸 {r['n_rebal']}회)")
    print(f"누적수익  EW={r['ew_cum']:+.1%}  ETF={r['etf_cum']:+.1%}")
    print(f"연환산    EW={r['ew_annual']:+.1%}  ETF={r['etf_annual']:+.1%}")
    print(f"MDD       EW={r['ew_mdd']:+.1%}  ETF={r['etf_mdd']:+.1%}")
    print(f"추종오차(TE annual): {r['tracking_error_annual']:.2%}")
    print(f"리밸 슬리피지  EW={r['ew_rebal_cost']:.2%}  ETF={r['etf_rebal_cost']:.2%} (ETF wrapper 비용 우위)")
    print(f"shadow-EW 디커플링: {r['decoupling_reason']} (e_over={r['e_over']:.1f}, e_under={r['e_under']:.1f})")
    print()
    print("★small-n hedge: 단일 sleeve·표본기간 한정 방향성 prior. TE/비용은 표본 의존 — 다 sleeve OOS 필요.")
