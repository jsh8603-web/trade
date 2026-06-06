# -*- coding: utf-8 -*-
"""measure_cross.py — consumer(소비재) §M.3 cross 축 + PIT 보고지연 stamp.

★[2026-06-05 audit 정정] battery 코드 잔재 정정: load_consumer_index() + customer-supplier =
  소비재 supply-chain(곡물/팜유 → 음식료 마진 / 화장품 ODM). lithium/albemarle dead code 제거.
  ★dollar β 산출은 정정 전후 동일(prices.parquet = consumer 28종 eq-weight, 함수명만 battery였음).

§M.3 cross = 3소비자 라우팅 (산업 subagent = 보고만, 조립 안 함):
  (1) 공통인자 exposure β (VIX/dollar/oil/rate/credit) — contemporaneous, 통합 supervisor Σ_return 입력
  (2) customer-supplier momentum (alpha 후보) — ★소비재 upstream = 곡물(ZC=F)/팜유 → 음식료 마진 lag.
      단 소비재 upstream 다양(곡물/화학원료/면세채널) = forward-alpha 약 prior → 측정 후 null 시 skip 기록.
  ※ DY connectedness = 통합 단계 (산업별 매번 X), I-O centrality = optional 최하위 → skip.

PIT-fundamentals safety (§M.1 ⑯): DART 정기보고서 rcept_dt(제출일) vs fiscal year-end gap
  = 보고지연 stamp. 측정에 final_revised 펀더멘털 쓰면 lookahead → IC 가짜 부풀림.
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


def load_consumer_index():
    """consumer universe 28종 동일가중 월간 수익 (산업 대표 시계열)."""
    px = pd.read_parquet(DATA / "prices.parquet")
    px.index = pd.to_datetime(px.index)
    pxm = px.resample("ME").last()
    ret = pxm.pct_change().mean(axis=1)  # eq-weight 산업 수익
    return ret.dropna()


def load_common_factors():
    """공통인자 (VIX/dollar/oil/rate) 월간 변화."""
    import FinanceDataReader as fdr
    import yfinance as yf
    cache = DATA / "common_factors.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    out = {}
    # VIX, dollar(DX-Y), oil(WTI=CL=F), rate(10Y=^TNX)
    yf_map = {"VIX": "^VIX", "dollar": "DX-Y.NYB", "oil": "CL=F", "rate10y": "^TNX"}
    for name, sym in yf_map.items():
        try:
            s = yf.download(sym, start=START, end=END, progress=False, auto_adjust=True)["Close"].squeeze()
            out[name] = s
        except Exception as e:
            print(f"  {name} fail {repr(e)[:50]}")
    # credit = KR HY proxy 부재 → US BAML HY OAS via FRED
    try:
        fred_key = os.environ.get("FRED_API_KEY", "")
        if fred_key:
            import requests
            r = requests.get("https://api.stlouisfed.org/fred/series/observations",
                             params=dict(series_id="BAMLH0A0HYM2", api_key=fred_key, file_type="json",
                                         observation_start=START), timeout=30).json()
            obs = r.get("observations", [])
            cr = pd.Series({o["date"]: float(o["value"]) for o in obs if o["value"] != "."})
            cr.index = pd.to_datetime(cr.index)
            out["credit_hy_oas"] = cr
    except Exception as e:
        print(f"  credit fail {repr(e)[:50]}")
    df = pd.concat(out, axis=1)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index().ffill(limit=5)
    df.to_parquet(cache)
    return df


def common_factor_beta(consumer_ret: pd.Series, factors: pd.DataFrame):
    """consumer 월간 수익 ~ 공통인자 월간 변화 (contemporaneous β, Newey-West HAC)."""
    fm = factors.resample("ME").last()
    # 변화율: VIX level diff, dollar/oil pct, rate diff, credit diff
    feat = pd.DataFrame(index=fm.index)
    if "VIX" in fm: feat["VIX"] = fm["VIX"].diff()
    if "dollar" in fm: feat["dollar"] = fm["dollar"].pct_change()
    if "oil" in fm: feat["oil"] = fm["oil"].pct_change()
    if "rate10y" in fm: feat["rate"] = fm["rate10y"].diff()
    if "credit_hy_oas" in fm: feat["credit"] = fm["credit_hy_oas"].diff()
    df = pd.concat([consumer_ret.rename("y"), feat], axis=1).dropna()
    if len(df) < 24:
        return {"note": "insufficient", "n": len(df)}
    X = sm.add_constant(df.drop(columns="y"))
    model = sm.OLS(df["y"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    out = {}
    for f in df.columns.drop("y"):
        out[f] = dict(beta=round(float(model.params[f]), 4),
                      se=round(float(model.bse[f]), 4),
                      t=round(float(model.tvalues[f]), 2),
                      ci95=[round(float(model.conf_int().loc[f, 0]), 4),
                            round(float(model.conf_int().loc[f, 1]), 4)],
                      contemporaneous=True)
    out["_meta"] = dict(n=len(df), r2=round(float(model.rsquared), 3),
                        note="HAC(maxlags=3). credit=US HY OAS proxy(KR HY 부재). contemporaneous risk 노출.")
    return out


def customer_supplier_momentum(consumer_ret: pd.Series):
    """★[2026-06-05 정정] 소비재 supply-chain 선행: 곡물/원자재(upstream) → 음식료 마진(downstream).
    Cohen-Frazzini: 업스트림 lagged return → 다운스트림 forward 예측.
    측정 = 곡물(옥수수ZC/밀ZW/대두ZS, 음식료 COGS 60-80%) lagged momentum → consumer forward.
    ★theory §1.1 cost pass-through 60-120일 lag = upstream 곡물↑ → 음식료 마진↓(역부호 예상).
    ★소비재 upstream 다양(곡물/화학원료/면세채널) = forward-alpha 약 prior, null 시 skip 기록(§M.10 패턴)."""
    import yfinance as yf
    out = {}
    for sym, label in [("ZC=F", "corn_grain_upstream"), ("ZW=F", "wheat_grain_upstream"), ("ZS=F", "soybean_upstream")]:
        try:
            s = yf.download(sym, start=START, end=END, progress=False, auto_adjust=True)["Close"].squeeze()
            s.index = pd.to_datetime(s.index)
            sm_ = s.resample("ME").last()
            sig = sm_.pct_change(3)  # 3M upstream(곡물) momentum
            res = {}
            for lag in [0, 1, 2, 3]:
                x = sig.shift(lag)
                fwd = consumer_ret.shift(-1)  # consumer 다음달 수익
                df = pd.concat([x.rename("x"), fwd.rename("y")], axis=1).dropna()
                if len(df) < 24:
                    continue
                rho, p = stats.spearmanr(df["x"], df["y"])
                res[f"lag{lag}"] = dict(corr=round(float(rho), 3), p=round(float(p), 3), n=len(df))
            out[label] = res
        except Exception as e:
            out[label] = {"fail": repr(e)[:60]}
    out["_note"] = ("★소비재 upstream(곡물 ZC/ZW/ZS) lagged 3M momentum → consumer forward 1M (cost pass-through). "
                    "음식료 한정 driver = 산업평균엔 희석. null 시 skip(§D forward-alpha falsifier). 동조성분=RegimeGlasso Ω 흡수.")
    return out


def dart_reporting_delay():
    """DART 정기보고서 rcept_dt 분포 → 보고지연 stamp (PIT-safety)."""
    import requests
    key = os.environ.get("DART_API_KEY", "")
    if not key:
        return {"available": False, "note": "DART key missing"}
    # battery 대표 4종 corp_code 조회 후 사업보고서 제출일
    # corp_code 매핑 (DART corpCode): 알려진 종목코드 → DART 8자리 고유번호 조회
    delays = []
    # list.json 으로 정기보고서(A) 제출 — bsns 종료(12/31) 대비 제출일 gap
    for yr in range(2021, 2026):
        try:
            r = requests.get("https://opendart.fss.or.kr/api/list.json",
                             params=dict(crtfc_key=key, bgn_de=f"{yr}0301", end_de=f"{yr}0501",
                                         pblntf_detail_ty="A001", page_count=100), timeout=30).json()
            if r.get("status") == "000":
                # A001 = 사업보고서. 전 종목 제출일 분포 (battery 개별 매칭 대신 시장 전체 delay 통계)
                rcepts = [it["rcept_dt"] for it in r.get("list", []) if it.get("report_nm", "").startswith("사업보고서")]
                if rcepts:
                    # fiscal end = (yr-1)-12-31, rcept = yr-03~04
                    fy_end = pd.Timestamp(f"{yr-1}-12-31")
                    gaps = [(pd.Timestamp(d) - fy_end).days for d in rcepts]
                    delays.append({"year": yr, "n": len(gaps),
                                   "median_delay_days": int(np.median(gaps)),
                                   "max_delay_days": int(np.max(gaps))})
        except Exception as e:
            delays.append({"year": yr, "fail": repr(e)[:50]})
        time.sleep(0.4)
    return dict(available=True, annual_report_delay=delays,
                note="사업보고서 제출 median delay ~85-90일(FY-end 후). PIT: 펀더멘털 신호는 rcept_dt 이후만 사용 의무. 본 v3 가격신호는 PIT-safe(보고지연 무관).")


def main():
    consumer_ret = load_consumer_index()
    print(f"consumer industry index: n={len(consumer_ret)} months")

    print("[1/4] common factor β ...")
    factors = load_common_factors()
    cfb = common_factor_beta(consumer_ret, factors)

    print("[2/4] customer-supplier momentum (소비재 곡물 upstream) ...")
    csm = customer_supplier_momentum(consumer_ret)

    print("[3/4] DART reporting delay (PIT) ...")
    dart = dart_reporting_delay()

    results = {"common_factor_exposure": cfb, "customer_supplier_momentum": csm, "pit_reporting_delay": dart}
    out = ROOT / "validation-cross-v3.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved {out}")

    print("\n=== common factor β (contemporaneous, HAC) ===")
    for f, v in cfb.items():
        if f == "_meta": continue
        print(f"  {f:<8} β={v['beta']:+.4f} t={v['t']:+.2f} CI={v['ci95']}")
    print(f"  meta: {cfb.get('_meta')}")
    print("\n=== customer-supplier momentum (소비재 곡물 upstream → consumer fwd) ===")
    for k, v in csm.items():
        if k.startswith("_"): continue
        print(f"  {k}: {v}")
    print("\n=== PIT reporting delay ===")
    print(f"  {dart.get('annual_report_delay')}")


if __name__ == "__main__":
    main()
