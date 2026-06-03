# -*- coding: utf-8 -*-
"""measure_cross.py — auto(자동차) §M.3 cross 축 + PIT 보고지연. battery/반도체 미러.

§M.3 cross = 3소비자 라우팅 (산업 subagent = 보고만):
  (1) 공통인자 exposure β (VIX/dollar/oil/rate/credit) — contemporaneous, Σ_return 입력
  (2) customer-supplier momentum (alpha 후보) — 자동차 supply-chain:
      ★완성차 ← 부품/원자재. proxy = CARZ(글로벌 자동차 수요) + SLX(철강 원가). lagged momentum → 한국 자동차 forward.
  ※ DY/I-O = 통합 단계 skip.

PIT-fundamentals (§M.1 ⑯): DART rcept_dt vs fiscal year-end gap = 보고지연 stamp.
"""
from __future__ import annotations
import sys, io, os, json, time
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

ENV = Path("D:/projects/Inv/.env")
if ENV.exists():
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))

START, END = "2019-01-01", "2026-05-29"


def load_auto_index():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    pxm = px.resample("ME").last()
    return pxm.pct_change().mean(axis=1).dropna()


def load_common_factors():
    import yfinance as yf
    cache = DATA / "common_factors.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    out = {}
    yf_map = {"VIX": "^VIX", "dollar": "DX-Y.NYB", "oil": "CL=F", "rate10y": "^TNX"}
    for name, sym in yf_map.items():
        try:
            s = yf.download(sym, start=START, end=END, progress=False, auto_adjust=True)["Close"].squeeze()
            out[name] = s
        except Exception as e:
            print(f"  {name} fail {repr(e)[:50]}")
    try:
        fred_key = os.environ.get("FRED_API_KEY", "")
        if fred_key:
            import requests
            r = requests.get("https://api.stlouisfed.org/fred/series/observations",
                             params=dict(series_id="BAMLH0A0HYM2", api_key=fred_key, file_type="json",
                                         observation_start=START), timeout=30).json()
            obs = r.get("observations", [])
            cr = pd.Series({o["date"]: float(o["value"]) for o in obs if o["value"] != "."})
            cr.index = pd.to_datetime(cr.index); out["credit_hy_oas"] = cr
    except Exception as e:
        print(f"  credit fail {repr(e)[:50]}")
    df = pd.concat(out, axis=1); df.index = pd.to_datetime(df.index)
    df = df.sort_index().ffill(limit=5); df.to_parquet(cache)
    return df


def common_factor_beta(auto_ret, factors):
    fm = factors.resample("ME").last()
    feat = pd.DataFrame(index=fm.index)
    if "VIX" in fm: feat["VIX"] = fm["VIX"].diff()
    if "dollar" in fm: feat["dollar"] = fm["dollar"].pct_change()
    if "oil" in fm: feat["oil"] = fm["oil"].pct_change()
    if "rate10y" in fm: feat["rate"] = fm["rate10y"].diff()
    if "credit_hy_oas" in fm: feat["credit"] = fm["credit_hy_oas"].diff()
    df = pd.concat([auto_ret.rename("y"), feat], axis=1).dropna()
    if len(df) < 24:
        return {"note": "insufficient", "n": len(df)}
    X = sm.add_constant(df.drop(columns="y"))
    model = sm.OLS(df["y"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    out = {}
    for f in df.columns.drop("y"):
        out[f] = dict(beta=round(float(model.params[f]), 4), se=round(float(model.bse[f]), 4),
                      t=round(float(model.tvalues[f]), 2),
                      ci95=[round(float(model.conf_int().loc[f, 0]), 4), round(float(model.conf_int().loc[f, 1]), 4)],
                      contemporaneous=True)
    out["_meta"] = dict(n=len(df), r2=round(float(model.rsquared), 3),
                        note="HAC(maxlags=3). credit=US HY OAS proxy(KR HY 부재). ★자동차=경기소비재 = credit/dollar(수출) 민감 예상.")
    return out


def customer_supplier_momentum(auto_ret):
    """자동차 supply-chain: 글로벌 자동차 수요(CARZ) / 철강 원가(SLX) lagged → 한국 자동차 forward."""
    import yfinance as yf
    out = {}
    for sym, label in [("CARZ", "global_auto_demand"), ("SLX", "steel_input_cost")]:
        try:
            s = yf.download(sym, start=START, end=END, progress=False, auto_adjust=True)["Close"].squeeze()
            s.index = pd.to_datetime(s.index)
            sm_ = s.resample("ME").last(); sig = sm_.pct_change(3)
            res = {}
            for lag in [0, 1, 2, 3]:
                x = sig.shift(lag); fwd = auto_ret.shift(-1)
                df = pd.concat([x.rename("x"), fwd.rename("y")], axis=1).dropna()
                if len(df) < 24:
                    continue
                rho, p = stats.spearmanr(df["x"], df["y"])
                res[f"lag{lag}"] = dict(corr=round(float(rho), 3), p=round(float(p), 3), n=len(df))
            out[label] = res
        except Exception as e:
            out[label] = {"fail": repr(e)[:60]}
    out["_note"] = ("global auto demand(CARZ)/steel cost(SLX) lagged 3M → 한국 자동차 forward 1M. "
                    "alpha 후보 = 측정 17종 검증 후 IC→weight. 동조성분은 RegimeGlasso Ω 흡수.")
    return out


def dart_reporting_delay():
    import requests
    key = os.environ.get("DART_API_KEY", "")
    if not key:
        return {"available": False, "note": "DART key missing"}
    delays = []
    for yr in range(2021, 2026):
        try:
            r = requests.get("https://opendart.fss.or.kr/api/list.json",
                             params=dict(crtfc_key=key, bgn_de=f"{yr}0301", end_de=f"{yr}0501",
                                         pblntf_detail_ty="A001", page_count=100), timeout=30).json()
            if r.get("status") == "000":
                rcepts = [it["rcept_dt"] for it in r.get("list", []) if it.get("report_nm", "").startswith("사업보고서")]
                if rcepts:
                    fy_end = pd.Timestamp(f"{yr-1}-12-31")
                    gaps = [(pd.Timestamp(d) - fy_end).days for d in rcepts]
                    delays.append({"year": yr, "n": len(gaps), "median_delay_days": int(np.median(gaps)), "max_delay_days": int(np.max(gaps))})
        except Exception as e:
            delays.append({"year": yr, "fail": repr(e)[:50]})
        time.sleep(0.4)
    return dict(available=True, annual_report_delay=delays,
                note="사업보고서 median delay ~108-120일. PIT: 펀더멘털 신호는 rcept_dt 이후만. 가격신호는 PIT-safe.")


def main():
    auto_ret = load_auto_index()
    print(f"auto industry index: n={len(auto_ret)} months")
    print("[1/3] common factor beta ...")
    factors = load_common_factors(); cfb = common_factor_beta(auto_ret, factors)
    print("[2/3] customer-supplier momentum ...")
    csm = customer_supplier_momentum(auto_ret)
    print("[3/3] DART reporting delay (PIT) ...")
    dart = dart_reporting_delay()
    results = {"common_factor_exposure": cfb, "customer_supplier_momentum": csm, "pit_reporting_delay": dart}
    (ROOT / "validation-cross-v3.json").write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved validation-cross-v3.json")
    print("\n=== common factor beta ===")
    for f, v in cfb.items():
        if f == "_meta": continue
        print(f"  {f:<8} b={v['beta']:+.4f} t={v['t']:+.2f} CI={v['ci95']}")
    print(f"  meta: {cfb.get('_meta')}")
    print("\n=== customer-supplier momentum ===")
    for k, v in csm.items():
        if not k.startswith("_"): print(f"  {k}: {v}")
    print(f"\n=== PIT delay: {dart.get('annual_report_delay')}")


if __name__ == "__main__":
    main()
