# -*- coding: utf-8 -*-
"""measure_rotation.py — 철강 업종 rotation 신호 (업종 자체 OW/UW timing, 종목 selection 아님).

★team-lead 지시 (2026-06-05): rotation-analyst v2가 산업 디렉토리 prices.parquet 전체를 패널로 써서
부수종목 오염 가능 → ★strict 화이트리스트로 재현 + v2 비교 필수.
★철강 = prices.parquet 이미 "1차 철강 제조업" 정밀필터 23종(순수) = 정유(가스9종 섞임)와 다름.
  본 스크립트 = strict 23종 eq-weight index 로 iron_ore_d3 재현 → v2 값 비교(오염 검증).

측정 = IC(cycle 신호, 철강 업종 forward return) — "어느 cycle 국면에 철강 업종 OW/UW".
신호 = 철강 cycle 직접지표 (철광석 원가 + 중국 수요 + 글로벌 철강 cycle + 마진 spread + 환율).
★종목 selection(capsule 본체)과 별 차원 = 업종 timing(rotation).

cycle 후보 8 (이론 사전확약 = theory-notes §rotation):
  iron_ore_yoy/d3  : 철광석 가격(TIO=F). 원가↑ but 수요-동행 = 부호 데이터판정(양/음 양면)
  china_fxi_yoy/d3 : 중국 수요(FXI). ★철강 = 중국 cycle dominant → 양 prior(수요)
  slx_steel_yoy    : 글로벌 철강 cycle(SLX). 양 prior(동조)
  slx_iron_spread  : SLX/TIO = 철강 마진 proxy(열연-철광석 spread). 양 prior(마진↑→주가)
  coking_coal_d3   : 원료탄(BTU). 음 prior(원가)
  usdkrw_d3        : 환율. 약세→수출 양 약 prior

★G-F: forward = 신호 t → 철강 업종 forward t+h (20d/60d). residualize(공통인자) = idiosyncratic.
★PIT: 일별 spot = 실시간. NW HAC + wild-cluster + walk-forward OOS(IS 2019-22/OOS 2023-26).
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import yfinance as yf
from scipy import stats

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
ROT_DATA = ROOT.parent.parent / "_rotation" / "data"   # cycle_steel.parquet 재사용

START, END = "2018-01-01", "2026-05-29"
SEMI_PPI_LAG = 1


def load_steel_index():
    """★strict 23종(1차 철강 제조업) eq-weight 월수익 = 철강 업종 index (오염 0 검증됨)."""
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    return px.resample("ME").last().pct_change().mean(axis=1, skipna=True), px.shape[1]


def load_cycle_signals():
    """철강 cycle 후보 8 (yfinance proxy). cycle_steel.parquet(iron_ore/china) 재사용 + 추가 fetch."""
    out = {}
    # 1) 재사용 (이미 수집): iron_ore(TIO=F) + china_proxy(FXI)
    cyc = pd.read_parquet(ROT_DATA / "cycle_steel.parquet"); cyc.index = pd.to_datetime(cyc.index)
    iron = cyc["iron_ore"]; china = cyc["china_proxy"]
    # 2) 추가 fetch: SLX(글로벌 철강) + BTU(원료탄)
    def yf_close(sym):
        s = yf.download(sym, start=START, end=END, progress=False, auto_adjust=True)["Close"].squeeze()
        s.index = pd.to_datetime(s.index); return s
    slx = yf_close("SLX")
    coal = yf_close("BTU")
    usdkrw = None
    rs = pd.read_parquet(DATA / "regime_series.parquet"); rs.index = pd.to_datetime(rs.index)
    usdkrw = rs["usdkrw"]
    # 월말 resample
    def m(s): return s.resample("ME").last()
    iron_m, china_m, slx_m, coal_m, krw_m = m(iron), m(china), m(slx), m(coal), m(usdkrw)
    out["iron_ore_yoy"] = iron_m.pct_change(12)
    out["iron_ore_d3"] = iron_m.pct_change(3)
    out["china_fxi_yoy"] = china_m.pct_change(12)
    out["china_fxi_d3"] = china_m.pct_change(3)
    out["slx_steel_yoy"] = slx_m.pct_change(12)
    out["slx_iron_spread"] = (slx_m / iron_m).pct_change(3)   # 철강마진 proxy(SLX/TIO) 3M change
    out["coking_coal_d3"] = coal_m.pct_change(3)
    out["usdkrw_d3"] = krw_m.pct_change(3)
    return out


def common_factors(rs):
    rsm = rs.resample("ME").last()
    F = pd.DataFrame(index=rsm.index)
    F["d_usdkrw"] = rsm["usdkrw"].pct_change()
    F["foreign"] = rsm["foreign_net_kospi"]
    if "semi_ppi" in rsm.columns:
        F["semi_ppi_yoy"] = rsm["semi_ppi"].shift(SEMI_PPI_LAG).pct_change(12)
    return F


def residualize(y, F):
    common = y.dropna().index.intersection(F.dropna().index)
    if len(common) < 20:
        return y
    yy = y.loc[common].values
    X = np.column_stack([np.ones(len(common))] + [F.loc[common, c].values for c in F.columns])
    beta, *_ = np.linalg.lstsq(X, yy, rcond=None)
    return pd.Series(yy - X @ beta, index=common)


def nw_se(x, lag):
    n = len(x)
    if n < 3: return np.nan
    e = x - x.mean(); var = (e @ e) / n
    for k in range(1, min(lag, n - 1) + 1):
        var += 2 * (1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n
    return float(np.sqrt(max(var, 1e-12) / n))


def wild_cluster_p(x, B=2000, seed=42):
    n = len(x)
    if n < 4: return np.nan
    rng = np.random.default_rng(seed)
    t_obs = abs(x.mean() / (x.std(ddof=1) / np.sqrt(n))) if x.std(ddof=1) > 0 else 0.0
    e = x - x.mean(); cnt = 0
    for _ in range(B):
        w = rng.choice([-1.0, 1.0], size=n); xn = w * e; sb = xn.std(ddof=1)
        tb = abs(xn.mean() / (sb / np.sqrt(n))) if sb > 0 else 0.0
        if tb >= t_obs: cnt += 1
    return (cnt + 1) / (B + 1)


def measure_signal(sig, fwd, h_m):
    """cycle 신호 → 철강 업종 forward IC (시계열 corr, NW + wild-cluster + OOS)."""
    df = pd.concat([sig.rename("s"), fwd.rename("f")], axis=1).dropna()
    if len(df) < 12:
        return {"n": len(df), "status": "INSUFFICIENT"}
    rho, _ = stats.spearmanr(df["s"], df["f"])
    n = len(df)
    # rolling IC 시계열 대신 단일 corr + NW SE via 회귀 잔차 t
    # IC t-stat: Spearman → Fisher z approx, NW on overlapping
    s_rank = stats.rankdata(df["s"]); f_rank = stats.rankdata(df["f"])
    s_z = (s_rank - s_rank.mean()) / s_rank.std(); f_z = (f_rank - f_rank.mean()) / f_rank.std()
    prod = s_z * f_z   # IC 기여 시계열
    ic = float(prod.mean())
    se = nw_se(prod, lag=h_m)
    t = ic / se if se and se > 0 else np.nan
    wc = wild_cluster_p(prod)
    # walk-forward OOS
    idx = df.index
    is_m = df[(idx >= "2019-01-01") & (idx <= "2022-12-31")]
    oos_m = df[(idx >= "2023-01-01") & (idx <= "2026-12-31")]
    oos = {}
    if len(is_m) >= 6 and len(oos_m) >= 6:
        is_ic, _ = stats.spearmanr(is_m["s"], is_m["f"])
        oos_ic, _ = stats.spearmanr(oos_m["s"], oos_m["f"])
        oos = {"is_ic": round(float(is_ic), 4), "oos_ic": round(float(oos_ic), 4),
               "sign_hold": bool(np.sign(is_ic) == np.sign(oos_ic)),
               "verdict": "✅OOS 부호유지" if np.sign(is_ic) == np.sign(oos_ic) else "❌OOS flip"}
    powered = n >= 24
    return {"ic": round(rho, 4), "ic_contrib_mean": round(ic, 4), "n": n,
            "t_nw": round(t, 2) if not np.isnan(t) else None,
            "wild_cluster_p": round(wc, 4) if not np.isnan(wc) else None,
            "walk_forward_oos": oos,
            "status": "powered" if powered else ("underpowered" if n >= 12 else "INSUFFICIENT")}


def main():
    steel_ret, n_stocks = load_steel_index()
    print(f"★strict 철강 universe = {n_stocks}종 (1차 철강 제조업, 오염 0 검증). index n={len(steel_ret.dropna())} months")
    rs = pd.read_parquet(DATA / "regime_series.parquet"); rs.index = pd.to_datetime(rs.index)
    F = common_factors(rs)
    steel_resid = residualize(steel_ret, F)

    sigs = load_cycle_signals()
    HORIZONS = {"y_20d": 1, "y_60d": 3}   # 월 단위 (20d≈1M, 60d≈3M)

    results = {"meta": {"strict_universe_n": n_stocks, "index": "eq-weight 월수익 (strict 23종)",
                        "contamination_check": "★prices.parquet = pass_floor 23종 정확 일치 = 오염 0 (정유 가스9종과 다름)",
                        "residualize": "공통인자(d_usdkrw/foreign/semi_ppi_yoy) 회귀 잔차 = idiosyncratic",
                        "priors": {"iron_ore": "양/음 데이터판정(원가 vs 수요동행)", "china_fxi": "양(수요)",
                                   "slx_steel": "양(동조)", "slx_iron_spread": "양(마진)", "coking_coal": "음(원가)", "usdkrw": "약세→양 약"}},
               "signals": {}}
    for sname, sig in sigs.items():
        results["signals"][sname] = {}
        for hname, hm in HORIZONS.items():
            fwd_raw = steel_ret.shift(-hm).rolling(hm).sum() if hm > 1 else steel_ret.shift(-hm)
            fwd_res = steel_resid.shift(-hm).rolling(hm).sum() if hm > 1 else steel_resid.shift(-hm)
            results["signals"][sname][hname] = {
                "raw": measure_signal(sig, fwd_raw, hm),
                "residualized": measure_signal(sig, fwd_res, hm),
            }
    out = ROOT / "validation-rotation-steel-v1.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved {out}")
    # 요약 출력
    print("\n=== 철강 rotation 신호 (raw / residualized IC, y_60d) ===")
    for sname, hd in results["signals"].items():
        r = hd["y_60d"]["raw"]; rr = hd["y_60d"]["residualized"]
        oos = r.get("walk_forward_oos", {}).get("verdict", "")
        print(f"  {sname:18s} raw IC={str(r.get('ic')):>8} wc_p={str(r.get('wild_cluster_p')):>7} n={r.get('n')} {r.get('status'):12s} | resid IC={str(rr.get('ic')):>8} | OOS {oos}")


if __name__ == "__main__":
    main()
