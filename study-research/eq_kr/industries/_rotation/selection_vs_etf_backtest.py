"""selection_vs_etf_backtest.py — capsule signal top-K selection vs EW vs ETF 3자 (실 PIT, Phase 5+).

목적: 사용자 가설 "selection 효과 있는 sleeve = 종목선택(top-K) 유리 / 없는 sleeve = ETF 유리" 를
      capsule 측정 signal 로 직접 시험. 우리 production 경로(CheapnessSelector=가치랭크 top-K)의
      가격 기반 signal(momentum/vol) sleeve 만 재현(PBR sleeve = 시총 시계열 부재로 제외).

3 경로 비교:
  - SELECT : capsule signal(within_residual_kr SSOT) 부호 방향 top-K 균등 월리밸 = 우리 selection 동형
  - EW     : sleeve 전종목 균등(baseline, selection 안 함)
  - ETF    : 테마 ETF 1개(fallback 후보)

⛔ 실 PIT only: prices.parquet(구성종목) + FDR(ETF). signal = 가격 기반(주식수 불요) 만.
⛔ 새 IC 측정 X — capsule 측정 signal·부호를 그대로 사용(within_residual_kr CAPSULE_IC SSOT).
⛔ small-n hedge: EW/SELECT 는 survivorship+거래비용 과소 편향. 방향성 prior 만, 단정 금지.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# capsule 측정 signal (within_industry_residual_kr.CAPSULE_IC SSOT 중 가격기반만).
#   ic 부호 = forward 예측 방향. 음수 = signal 高→forward 低 (reversal/저변동 우위) → bottom-K 매수.
_PRICE_SIGNALS = {
    "steel":        {"signal": "mom_12_1", "ic": -0.181, "etf": None},      # ETF 없음(steel ledger)
    "battery":      {"signal": "mom_6",    "ic": +0.075, "etf": "305720"},
    "chemical":     {"signal": "vol_60",   "ic": -0.142, "etf": "139250"},
    "shipbuilding": {"signal": "lowvol_60","ic": -0.057, "etf": "441540"},
}
_TRADING_DAYS = 252
_TOPK_FRAC = 0.30   # 상위 30% 균등


def _signal_panel(px, kind: str):
    """가격 → signal 시계열 (월말 기준, PIT: 과거 데이터만)."""
    import numpy as np

    mret = px.resample("ME").last()
    if kind == "mom_12_1":      # 12개월 모멘텀 − 1개월(최근 반전 제거)
        return mret.pct_change(12) - mret.pct_change(1)
    if kind == "mom_6":         # 6개월 모멘텀
        return mret.pct_change(6)
    if kind == "vol_60":        # 60일 변동성(월말, 음 IC=고변동 회피)
        return px.pct_change().rolling(60).std().resample("ME").last()
    if kind == "lowvol_60":     # 저변동성(= -vol)
        return -px.pct_change().rolling(60).std().resample("ME").last()
    raise ValueError(kind)


def _select_returns(px, signal_kind: str, ic_sign: int):
    """capsule signal 부호 방향 top-K 균등 월리밸 수익 시계열 (실 PIT, 1개월 lag).

    ic_sign>0 = signal 高 매수(top) / ic_sign<0 = signal 低 매수(bottom, reversal/저변동).
    월말 signal(PIT) → 다음달 균등보유 수익. look-ahead 없음(signal[t] → ret[t+1]).
    """
    import numpy as np
    import pandas as pd

    sig = _signal_panel(px, signal_kind)
    mret = px.resample("ME").last().pct_change()   # 월수익
    out = []
    idx = []
    months = sig.index
    for i in range(len(months) - 1):
        s = sig.iloc[i].dropna()
        if len(s) < 4:
            continue
        ranked = s.sort_values(ascending=(ic_sign < 0))   # ic<0 → 오름차순(저signal 매수)
        k = max(1, int(len(ranked) * _TOPK_FRAC))
        picks = ranked.index[:k]
        nxt = mret.iloc[i + 1].reindex(picks).dropna()     # 다음달 수익(PIT)
        if len(nxt):
            out.append(float(nxt.mean()))
            idx.append(months[i + 1])
    return pd.Series(out, index=idx)


def run(sleeve: str) -> dict:
    import numpy as np
    import pandas as pd
    sys.path.insert(0, str(ROOT / "study-research" / "eq_kr" / "industries" / "_rotation"))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "etfbt", ROOT / "study-research/eq_kr/industries/_rotation/etf_fallback_backtest.py")
    etfbt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(etfbt)

    cfg = _PRICE_SIGNALS[sleeve]
    base = ROOT / "study-research" / "eq_kr" / "industries" / sleeve / "raw-v3" / "data"
    px = pd.read_parquet(base / "prices.parquet").sort_index()

    # SELECT (capsule signal top-K) + EW (전종목 월수익)
    sel = _select_returns(px, cfg["signal"], 1 if cfg["ic"] > 0 else -1)
    ew_m = px.resample("ME").last().pct_change().mean(axis=1)

    res = {"sleeve": sleeve, "signal": cfg["signal"], "ic": cfg["ic"]}
    # 공통기간 SELECT vs EW
    d = pd.DataFrame({"sel": sel, "ew": ew_m}).dropna()
    res["n_months"] = len(d)
    res["sel_cum"] = float((1 + d["sel"]).prod() - 1)
    res["ew_cum"] = float((1 + d["ew"]).prod() - 1)
    # SELECT − EW 월별 알파(selection 순효과)
    alpha = d["sel"] - d["ew"]
    res["sel_minus_ew_annual"] = float(alpha.mean() * 12)
    res["sel_alpha_t"] = float(alpha.mean() / (alpha.std() / np.sqrt(len(alpha)))) if alpha.std() > 0 else 0.0

    # ETF (있으면)
    if cfg["etf"]:
        etf_d = etfbt._load_etf_returns(cfg["etf"], px.index.min(), px.index.max())
        if etf_d is not None:
            etf_m = (1 + etf_d).resample("ME").prod() - 1
            d2 = pd.DataFrame({"sel": sel, "ew": ew_m, "etf": etf_m}).dropna()
            if len(d2):
                res["etf_cum"] = float((1 + d2["etf"]).prod() - 1)
                res["n_common"] = len(d2)
                # 동일기간 재계산
                res["sel_cum_c"] = float((1 + d2["sel"]).prod() - 1)
                res["ew_cum_c"] = float((1 + d2["ew"]).prod() - 1)
    return res


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("=== capsule signal SELECT vs EW vs ETF (실 PIT) ===")
    print(f"{'sleeve':<13}{'signal':<11}{'IC':>7}{'SELECT':>9}{'EW':>9}{'ETF':>9}  SELECT−EW alpha(연,t)")
    for s in _PRICE_SIGNALS:
        try:
            r = run(s)
        except Exception as e:
            print(f"{s:<13} ⚠️ {type(e).__name__}: {str(e)[:50]}")
            continue
        etf = f"{r.get('etf_cum'):+.0%}" if r.get("etf_cum") is not None else "—(ETF없음)"
        # 공통기간 있으면 그걸로 표시
        sc = r.get("sel_cum_c", r["sel_cum"]); ec = r.get("ew_cum_c", r["ew_cum"])
        print(f"{s:<13}{r['signal']:<11}{r['ic']:>+7.3f}{sc:>+8.0%}{ec:>+8.0%}{etf:>9}  "
              f"{r['sel_minus_ew_annual']:+.1%}/yr (t={r['sel_alpha_t']:+.2f}, n={r['n_months']}m)")
    print()
    print("★해석: SELECT−EW alpha>0 + t유의 = 종목선택이 EW 능가(selection 가치 있음).")
    print("  alpha≈0/음 = selection 무의미(EW로 충분). ETF가 SELECT·EW 모두 하회 = ETF fallback 불리.")
    print("★small-n hedge: EW/SELECT survivorship+거래비용 과소. t는 월별 IID 가정(autocorr 미보정) 상한.")
