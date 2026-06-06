"""fair_cost_backtest.py — 공정 맞대결 백테스트 (자문 R1 반영, 2026-06-06).

자문(gemini-web+claude-web R1) 핵심: EW>ETF 우위는 survivorship + 소형주 매매비용 누락 착시.
공정 비교 = PIT 비용모델로 EW·SELECT·ETF 를 net-of-everything 으로 재대결.

반영한 보정 (자문 Q2):
- √임팩트 모델: cost ≈ spread/2 + σ_daily·c·√(참여율), 참여율 = 주문금액/ADV (amount.parquet 실측)
- ★ADV 캡(자문 "단일 최강 보정"): 참여율 > CAP 종목은 주문 축소(= 백테스트 수익 만든 비유동 종목 제거)
- 증권거래세(STT): 직접주식 매도 0.18%. ETF 는 면제(설정/환매 in-kind).
- survivorship haircut: 상폐 backfill 불가 → EW/SELECT 에 연 HAIRCUT% 드래그(자문 차선책)
- ETF: 단일·고유동 → 임팩트 작음 + STT 면제 + NAV 내부비용은 시세에 이미 반영(이중계상 금지)

⛔ 소액 AUM 가정(개인 운용, 기본 sleeve당 1억). 참여율은 AUM 의존 → AUM↑ 시 EW 비용 초선형 증가.
⛔ haircut/AUM 은 가정 — 점추정 단정 금지(자문: financial류 일부 생존 / bio류 붕괴 예측 검증).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_TRADING_DAYS = 252
_REBAL_DAYS = 21
_STT_SELL = 0.0018            # 증권거래세 매도 0.18%(직접주식). ETF 면제.
_IMPACT_C = 0.8              # √임팩트 계수(보수)
_SPREAD_HALF = 0.0010        # 호가 절반 스프레드 0.10%(소형주 보수)
_ADV_CAP = 0.10             # 참여율 상한 10%(초과분 주문 축소)
_SURV_HAIRCUT_ANNUAL = 0.04  # survivorship 차선 haircut 연 4%(자문 권고 3~5% 중앙)
_SLEEVE_AUM = 1e8           # 소액 가정 sleeve당 1억원


def _sqrt_impact_cost(participation: float, sigma_daily: float) -> float:
    """편도 √임팩트 비용률 = spread/2 + σ·c·√(참여율)."""
    return _SPREAD_HALF + sigma_daily * _IMPACT_C * (max(0.0, participation) ** 0.5)


def _ew_net_returns(px, amt, *, aum: float, apply_haircut: bool):
    """EW 월리밸 net 수익 — 종목별 √임팩트 + ADV캡 + STT + (haircut) 반영."""
    import numpy as np
    import pandas as pd

    mret = px.resample("ME").last().pct_change()
    sigma_d = px.pct_change().rolling(_REBAL_DAYS).std().resample("ME").last()
    adv = amt.rolling(_REBAL_DAYS).mean().resample("ME").last()   # 월말 기준 ADV(원)

    out, idx = [], []
    months = mret.index
    for i in range(1, len(months)):
        r = mret.iloc[i].dropna()
        if len(r) < 4:
            continue
        n = len(r)
        order_per = aum / n                       # 종목당 주문금액
        adv_i = adv.iloc[i].reindex(r.index)
        sig_i = sigma_d.iloc[i].reindex(r.index).fillna(0.02)
        gross = float(r.mean())
        # 종목별 참여율 + ADV캡(초과분 미체결=주문 축소 → 비중 하향, 잔여는 현금)
        part = (order_per / adv_i).clip(upper=None)
        eff = part.clip(upper=_ADV_CAP)            # 캡 적용 실제 체결 참여율
        # 편도 비용(매수+매도 양방향), turnover=리밸마다 전량 교체 가정(보수 상한)
        cost_each = eff.index.to_series().map(
            lambda t: _sqrt_impact_cost(float(eff.get(t, 0.0)), float(sig_i.get(t, 0.02))))
        roundtrip = 2 * float(cost_each.mean()) + _STT_SELL    # 매수+매도 임팩트 + 매도 STT
        net = gross - roundtrip / _REBAL_DAYS * _REBAL_DAYS    # 월 비용(리밸 1회/월)
        net = gross - roundtrip
        if apply_haircut:
            net -= _SURV_HAIRCUT_ANNUAL / 12.0     # 월 haircut
        out.append(net); idx.append(months[i])
    return pd.Series(out, index=idx)


def _etf_net_returns(etf_ret):
    """ETF net 수익 — 단일·고유동 → 임팩트 무시 가능 + STT 면제(in-kind). 월수익만."""
    return (1 + etf_ret).resample("ME").prod() - 1


def run(sleeve: str, etf_ticker: str, *, aum: float = _SLEEVE_AUM) -> dict:
    import numpy as np
    import pandas as pd
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "etfbt", ROOT / "study-research/eq_kr/industries/_rotation/etf_fallback_backtest.py")
    etfbt = importlib.util.module_from_spec(spec); spec.loader.exec_module(spec_obj := etfbt)

    base = ROOT / "study-research" / "eq_kr" / "industries" / sleeve / "raw-v3" / "data"
    px = pd.read_parquet(base / "prices.parquet").sort_index()
    amt = pd.read_parquet(base / "amount.parquet").sort_index()
    amt = amt.reindex(columns=px.columns)

    ew_net = _ew_net_returns(px, amt, aum=aum, apply_haircut=True)
    ew_gross = px.resample("ME").last().pct_change().mean(axis=1)
    etf_ret = etfbt._load_etf_returns(etf_ticker, px.index.min(), px.index.max())
    if etf_ret is None:
        return {"ok": False, "sleeve": sleeve}
    etf_net = _etf_net_returns(etf_ret)

    # size proxy = EW(균등=소형틸트) − VW(시총=대형). market = ETF(beta).
    ew_g2, vw, _ = spec_obj._load_sleeve_ew_returns(sleeve)
    size = (ew_g2 - vw) if vw is not None else None

    d = pd.DataFrame({"ew_gross": ew_gross, "ew_net": ew_net, "etf": etf_net}).dropna()
    if len(d) < 12:
        return {"ok": False, "sleeve": sleeve, "reason": f"n={len(d)}"}
    spread = d["ew_net"] - d["etf"]
    res = {
        "ok": True, "sleeve": sleeve, "n": len(d), "aum": aum,
        "ew_gross_cum": float((1 + d["ew_gross"]).prod() - 1),
        "ew_net_cum": float((1 + d["ew_net"]).prod() - 1),
        "etf_cum": float((1 + d["etf"]).prod() - 1),
        "ew_net_minus_etf_annual": float(spread.mean() * 12),
        "spread_t": float(spread.mean() / (spread.std() / np.sqrt(len(spread)))) if spread.std() > 0 else 0.0,
    }
    # C9 attribution(자문 R1): 스프레드 ~ market(ETF) + size(EW−VW) OLS. 잔차 절편 = 설명 안 되는 alpha.
    #   R²↑ + size beta 유의 = 격차가 size 틸트로 설명(구현 alpha 아님, 더 싼 size-ETF로 대체 가능).
    if size is not None:
        a = pd.DataFrame({"spread": spread, "mkt": d["etf"], "size": size.reindex(d.index)}).dropna()
        if len(a) >= 12:
            X = np.column_stack([np.ones(len(a)), a["mkt"].values, a["size"].values])
            beta, *_ = np.linalg.lstsq(X, a["spread"].values, rcond=None)
            yhat = X @ beta
            ss_res = float(((a["spread"].values - yhat) ** 2).sum())
            ss_tot = float(((a["spread"].values - a["spread"].mean()) ** 2).sum())
            res["attrib_r2"] = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
            res["attrib_alpha_annual"] = float(beta[0] * 12)   # 절편 = size·market 설명 후 잔차 alpha
            res["attrib_size_beta"] = float(beta[2])
    return res


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    picks = {"financial": "091170", "battery": "305720", "bio": "244580",
             "shipbuilding": "441540", "consumer": "266390", "chemical": "139250", "auto": "091180"}
    print("=== 공정 맞대결: EW(gross→net) vs ETF (자문 보정 반영, AUM=1억) ===")
    print(f"{'sleeve':<13}{'EW_net':>9}{'ETF':>8}{'net−ETF(t)':>14}{'attrib: R²/size_β/잔차α':>26}")
    for s, t in picks.items():
        r = run(s, t)
        if not r.get("ok"):
            print(f"{s:<13} ⚠️ {r.get('reason','ETF 부재')}"); continue
        att = (f"R²={r.get('attrib_r2',0):.2f} sizeβ={r.get('attrib_size_beta',0):+.2f} "
               f"α={r.get('attrib_alpha_annual',0):+.1%}/yr") if "attrib_r2" in r else "—"
        print(f"{s:<13}{r['ew_net_cum']:>+8.0%}{r['etf_cum']:>+7.0%}"
              f"{r['ew_net_minus_etf_annual']:>+9.1%}(t={r['spread_t']:+.1f}){att:>26}")
    print()
    print("★net−ETF>0+t유의 = 비용보정 후에도 EW 우위 / ≈0·음 = 착시.")
    print("★attribution(자문 C9): R²↑+size_β 유의 = 격차가 size 틸트로 설명(구현 alpha 아님, size-ETF 대체가능).")
    print("  잔차 α = size·market 설명 후 남는 진짜 격차. α≈0 = 순수 팩터, α유의 = ETF 트래커 부실 등 구조적.")
