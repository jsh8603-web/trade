"""★우선 2: internal glasso effective-N gate 영구폐쇄 위험 검증.

direction.md D4: internal RegimeGlasso 인스턴스 신설 (X=[MVRV, FGI, funding, OI, dominance, RSI, SMA_dev, SOPR, fwd_ret], regime_ids=vol×macro).
stability gate = per-regime effective N threshold + bootstrap edge stability.

★검증 목적: funding-limited (2020-09~) + 일봉 autocorr 로 per-regime effective N 이 gate 상시 못 넘는지.
방법:
- regime: FGI 5단계 × vol regime 3단계 = 15 regime
- 각 regime 의 complete-case window 길이 + autocorrelation-adjusted N_eff
- threshold 후보 (50, 100, 200) 별 admit 빈도

기각 조건: N_eff threshold 200 에서 admit 빈도 < 10% = gate 영구폐쇄 위험 HIGH
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
import pandas as pd
from lib_common import (
    load_funding, load_coinmetrics, load_stablecoin, load_btc_klines, load_fgi,
    fgi_regime, halving_phase, effective_n
)

OUT = Path(__file__).resolve().parent.parent / "raw" / "validation-eff-n-gate.md"

def main():
    klines = load_btc_klines()
    klines["log_ret_1d"] = np.log(klines["close"]/klines["close"].shift(1))
    klines["vol_30d"] = klines["log_ret_1d"].rolling(30).std()
    # vol regime: tertile
    try:
        klines["vol_regime"] = pd.qcut(klines["vol_30d"], 3, labels=["low_vol", "mid_vol", "high_vol"])
    except ValueError:
        # duplicates 발생 시 라벨 자동 부여
        klines["vol_regime"] = pd.qcut(klines["vol_30d"], 3, duplicates="drop").astype(str)

    fgi = load_fgi()
    klines = klines.merge(fgi[["date", "fgi"]], on="date", how="left")
    klines["fgi_regime"] = klines["fgi"].apply(fgi_regime)
    klines["halving_phase"] = klines["date"].apply(halving_phase)

    # funding ETF cohort
    try:
        fund = load_funding()
        fund["date"] = fund["datetime"].dt.normalize()
        fund_daily = fund.groupby("date")["funding_rate"].mean().reset_index().rename(columns={"funding_rate": "funding_mean"})
        df = klines.merge(fund_daily, on="date", how="left")
    except Exception:
        df = klines.copy()
        df["funding_mean"] = np.nan

    # stablecoin
    try:
        sc = load_stablecoin()
        sc["log_supply"] = np.log(sc["total_supply"])
        sc["supply_g7d"] = sc["log_supply"].diff(7)
        df = df.merge(sc[["date", "supply_g7d"]], on="date", how="left")
    except Exception:
        df["supply_g7d"] = np.nan

    # CoinMetrics MVRV (있을 때만)
    try:
        cm = load_coinmetrics()
        cm["mvrv"] = cm["CapMVRVCur"]
        df = df.merge(cm[["date", "mvrv"]], on="date", how="left")
    except FileNotFoundError:
        df["mvrv"] = np.nan
    except Exception:
        df["mvrv"] = np.nan

    # 가용 indicator 명단
    indicator_cols = [c for c in ["mvrv", "fgi", "funding_mean", "supply_g7d", "log_ret_1d"] if c in df.columns]
    df["complete_case"] = df[indicator_cols].notna().all(axis=1)

    lines = []
    def w(s=""): lines.append(s)

    w("# 우선 2 — Internal glasso effective-N gate 영구폐쇄 위험 검증")
    w()
    w(f"as_of: {pd.Timestamp.utcnow().isoformat()}")
    w(f"indicator 후보 (가용): {indicator_cols}")
    w(f"전체 일수: {len(df)}, complete-case 일수: {int(df['complete_case'].sum())} ({df['complete_case'].mean():.3%})")
    w(f"complete-case 기간: {df[df['complete_case']]['date'].min()} ~ {df[df['complete_case']]['date'].max()}")
    w()

    # ===== 1. complete-case 가용 시작 일자 =====
    w("## 1. Indicator 별 가용 시작 일자 (joint complete-case window 제약)")
    for c in indicator_cols:
        first = df[df[c].notna()]["date"].min()
        last = df[df[c].notna()]["date"].max()
        n = int(df[c].notna().sum())
        w(f"- {c}: {first.date()} ~ {last.date()}, n={n}")
    w(f"- ★joint complete-case 시작 = {df[df['complete_case']]['date'].min() if df['complete_case'].any() else 'never'}")
    w()

    # ===== 2. Regime cell N (FGI × vol) =====
    w("## 2. Regime cell 분포 (FGI 5 × vol 3 = 15 cell)")
    cd = df[df["complete_case"]].copy()
    cell_n = cd.groupby(["fgi_regime", "vol_regime"], observed=True).size().unstack(fill_value=0)
    w("```")
    w(cell_n.to_string())
    w("```")
    w()

    # ===== 3. 각 regime cell 의 effective N =====
    w("## 3. Cell 별 effective N (autocorr-adjusted, log_ret_1d 기준)")
    cell_eff = []
    for (fg, vol), sub in cd.groupby(["fgi_regime", "vol_regime"], observed=True):
        if len(sub) < 10:
            cell_eff.append({"fgi": fg, "vol": vol, "n_raw": len(sub), "n_eff": len(sub)})
            continue
        eff = effective_n(sub["log_ret_1d"].dropna().values)
        cell_eff.append({"fgi": fg, "vol": vol, "n_raw": len(sub), "n_eff": eff})
    edf = pd.DataFrame(cell_eff)
    edf = edf.sort_values(["fgi", "vol"]).reset_index(drop=True)
    w("```")
    w(edf.round(1).to_string(index=False))
    w("```")
    w()

    # ===== 4. Threshold 별 admit rate =====
    w("## 4. Threshold 별 admit rate (gate 영구폐쇄 위험 평가)")
    total_cells = len(edf)
    for thr in [24, 50, 100, 200, 500]:
        admit = int((edf["n_eff"] >= thr).sum())
        rate = admit / total_cells if total_cells > 0 else 0
        verdict = "OK" if rate >= 0.5 else ("WARN" if rate >= 0.2 else "★HIGH 영구폐쇄 위험")
        w(f"- effective N >= {thr}: {admit}/{total_cells} cells ({rate:.1%}) - {verdict}")
    w()

    # ===== 5. 가설 판정 =====
    w("## 5. 가설 판정 (direction.md §5 의문 #4)")
    eff_200 = edf["n_eff"] >= 200
    eff_100 = edf["n_eff"] >= 100
    eff_50 = edf["n_eff"] >= 50
    admit_200 = eff_200.mean()
    admit_100 = eff_100.mean()
    admit_50 = eff_50.mean()
    w(f"- threshold 50  admit rate = {admit_50:.1%}")
    w(f"- threshold 100 admit rate = {admit_100:.1%}")
    w(f"- threshold 200 admit rate = {admit_200:.1%}")
    if admit_200 < 0.1:
        w("- ★결론: threshold 200 admit < 10% = **gate 영구폐쇄 위험 HIGH**")
        w("  -> direction.md D4 hybrid 의 internal glasso 부분 *보류* + offline 표만 활용 권고")
    elif admit_100 < 0.3:
        w("- ★결론: threshold 100 admit < 30% = **gate 운용 어려움**")
        w("  -> threshold 를 50 또는 cell 통합 (FGI 5->3 단계 축소) 후 재평가 권고")
    else:
        w("- ★결론: gate 통과 cell 충분 -> direction.md D4 hybrid 권고 유지 가능")
    w()

    w("## 6. 미해결 의문")
    w("- effective N = AR(1) 가정 단순 보정. 실제 autocorr 구조가 복잡 (MA/GARCH/regime-switching)")
    w("- vol regime tertile 은 in-sample 분류 (post-hoc) -> 실시간 적용 시 lookahead 위험 주의")
    w("- joint complete-case 시작 = funding (2020-09) 의 제약. CoinMetrics MVRV 가 합류하면 더 짧아짐")
    w("- bootstrap edge stability 시뮬은 미수행 (긴 연산) — gate 통과 cell 에 한해 별도 검증 권고")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] eff_n_gate -> {OUT}")


if __name__ == "__main__":
    main()
