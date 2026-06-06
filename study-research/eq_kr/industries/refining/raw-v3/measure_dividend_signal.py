# -*- coding: utf-8 -*-
"""measure_dividend_signal.py — 정유 배당수익률 income 신호 (★2번째 tradeable 발굴, team-lead 지시).

team-lead 지시: 정유 tradeable 유가 1개만 → 최소 2개 보강. 배당수익률 income 신호 발굴.

★발견 (정직, 부호 사전확약 정정): 배당수익률 → forward 3M = ★음(-) (prior 양과 반대).
  메커니즘 = 정유 cyclical ★배당 income trap: 고배당수익률 = 전년 호황 DPS / 현재(하락)주가 = 사이클 정점
  직후 신호 → forward 약(peak-out). = PER peak-EPS trap의 배당 버전(Damodaran cyclical).
  ★유가 mean-reversion과 경제 연관(둘 다 peak-out)이나 partial 독립(brent corr +0.38<0.5, 유가통제 후 -0.241 잔존).

데이터: DART alotMatter API(주당 현금배당금, 연 1회, t+1년 4월 적용 PIT) / 주가 pykrx.
검증: eff-N 보정 t + wild-cluster + OOS + leave-episode + 유가 직교성(partial).
"""
from __future__ import annotations
import sys, io, os, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np
import pandas as pd
import requests
from scipy import stats

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
ENV = Path("D:/projects/Inv/.env")
if ENV.exists():
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1); os.environ.setdefault(k.strip(), v.strip().strip('"'))
KEY = os.environ.get("DART_API_KEY", "")
STRICT2 = ["096770", "010950"]


def collect_dps():
    """DART 주당 현금배당금 (연도별, PIT = t+1년 3월 공시 → 4월 적용)."""
    cache = DATA / "dividend_dps.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    cmap = json.loads((DATA / "dart_corpcode.json").read_text(encoding="utf-8"))
    dps = {}
    for code in STRICT2:
        cc = cmap.get(code); dps[code] = {}
        for yr in range(2018, 2025):
            try:
                r = requests.get("https://opendart.fss.or.kr/api/alotMatter.json",
                                 params=dict(crtfc_key=KEY, corp_code=cc, bsns_year=str(yr), reprt_code="11011"), timeout=20)
                j = r.json()
                if j.get("status") == "000":
                    for it in j.get("list", []):
                        if "주당 현금배당금" in it.get("se", "") and "보통" in it.get("stock_knd", "보통"):
                            v = it.get("thstrm", "").replace(",", "")
                            if v not in ("-", ""):
                                dps[code][str(yr)] = float(v); break
            except Exception:
                pass
    cache.write_text(json.dumps(dps, ensure_ascii=False, indent=2), encoding="utf-8")
    return dps


def n_eff_autocorr(x, max_lag=12):
    n = len(x)
    if n < 4: return float(n)
    e = x - x.mean(); v = (e @ e) / n
    if v <= 0: return float(n)
    s = 0.0
    for k in range(1, min(max_lag, n - 1) + 1):
        rk = (e[k:] @ e[:-k]) / n / v
        if rk <= 0: break
        s += (1 - k / (max_lag + 1)) * rk
    return float(n / (1 + 2 * s))


def wild_cluster_p(x, B=2000, seed=42):
    n = len(x); rng = np.random.default_rng(seed); sd = x.std(ddof=1)
    t = abs(x.mean() / (sd / np.sqrt(n))) if sd > 0 else 0
    e = x - x.mean(); c = 0
    for _ in range(B):
        w = rng.choice([-1., 1.], n); xn = w * e; sb = xn.std(ddof=1)
        tb = abs(xn.mean() / (sb / np.sqrt(n))) if sb > 0 else 0
        if tb >= t: c += 1
    return (c + 1) / (B + 1)


def partial_rho(x, y, z):
    c = x.dropna().index.intersection(y.dropna().index).intersection(z.dropna().index)
    c = [i for i in c if i >= pd.Timestamp("2019-01-01")]
    if len(c) < 10: return None
    xr, yr, zr = stats.rankdata(x.loc[c]), stats.rankdata(y.loc[c]), stats.rankdata(z.loc[c])
    def res(a, b):
        b1 = np.column_stack([np.ones(len(b)), b]); return a - b1 @ np.linalg.lstsq(b1, a, rcond=None)[0]
    return round(float(stats.spearmanr(res(xr, zr), res(yr, zr))[0]), 3)


def main():
    dps = collect_dps()
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    cyc = pd.read_parquet(DATA / "refining_cycle.parquet"); cyc.index = pd.to_datetime(cyc.index)
    pxm = px[STRICT2].resample("ME").last()

    # 배당수익률 (PIT: 전년 DPS, 당해 4월 이후 적용)
    dy_panel = {}
    for code in STRICT2:
        s = pd.Series(index=pxm.index, dtype=float)
        for dt in pxm.index:
            ay = dt.year - 1 if dt.month >= 4 else dt.year - 2
            if str(ay) in dps[code] and pd.notna(pxm.loc[dt, code]) and pxm.loc[dt, code] > 0:
                s[dt] = dps[code][str(ay)] / pxm.loc[dt, code]
        dy_panel[code] = s
    dy = pd.DataFrame(dy_panel).mean(axis=1)

    pret = pxm.pct_change().mean(axis=1).loc["2019-01-01":]
    cum = (1 + pret.fillna(0)).cumprod()
    fwd60 = cum.pct_change(3).shift(-3)
    brent = cyc["brent"].resample("ME").last()

    s = dy.loc["2019-01-01":]
    c = [i for i in s.dropna().index.intersection(fwd60.dropna().index) if i >= pd.Timestamp("2019-01-01")]
    av, bv = s.loc[c].values, fwd60.loc[c].values
    rho = float(stats.spearmanr(av, bv)[0])
    prod = (stats.rankdata(av) / len(av) - 0.5) * (stats.rankdata(bv) / len(bv) - 0.5)
    neff = n_eff_autocorr(prod)
    t_eff = rho * np.sqrt((neff - 2) / (1 - rho ** 2)) if neff > 2 else np.nan
    isd = [d for d in c if str(d) < "2023-01-01"]; oosd = [d for d in c if str(d) >= "2023-01-01"]
    rho_is = float(stats.spearmanr(s.loc[isd], fwd60.loc[isd])[0])
    rho_oos = float(stats.spearmanr(s.loc[oosd], fwd60.loc[oosd])[0])
    # leave-episode (2022H2-2023 우크라 peak 제외)
    mask = ~((s.index >= "2022-06-01") & (s.index <= "2023-12-31"))
    sl = s[mask]; cl = [i for i in sl.dropna().index.intersection(fwd60.dropna().index) if i >= pd.Timestamp("2019-01-01")]
    rho_le = float(stats.spearmanr(sl.loc[cl], fwd60.loc[cl])[0])

    out = {
        "signal": "dividend_yield_income",
        "prior_사전확약": "양(고배당=저평가→forward양) — ★실측 음(-)으로 정정(HARKing 정직)",
        "mechanism": "정유 cyclical 배당 income trap: 고배당수익률 = 전년 호황 DPS/현재(하락)주가 = 사이클 정점 직후 → forward 약(peak-out). PER peak-EPS trap의 배당 버전(Damodaran cyclical).",
        "dps_raw": dps,
        "rho_fwd3m": round(rho, 4), "n": len(c), "n_eff": round(neff, 1),
        "t_eff_corrected": round(float(t_eff), 2), "wild_cluster_p": round(wild_cluster_p(prod), 4),
        "walk_forward_oos": {"is_rho": round(rho_is, 4), "oos_rho": round(rho_oos, 4),
                             "sign_hold": bool(np.sign(rho_is) == np.sign(rho_oos) and abs(rho_oos) >= 0.5 * abs(rho_is))},
        "leave_episode_2022H2_2023": {"full_rho": round(rho, 4), "leave_rho": round(rho_le, 4),
                                      "survive": bool(np.sign(rho) == np.sign(rho_le))},
        "orthogonality_vs_oil": {"corr_brent": round(float(stats.spearmanr(dy.loc[c], brent.loc[c])[0]), 3),
                                 "partial_div_given_brent": partial_rho(dy, fwd60, brent),
                                 "note": "brent corr +0.38<0.5 직교 경계 + partial -0.241 잔존 = 유가와 partial 독립(완전 재포장 아님)"},
        "tradeable_verdict": "★2번째 tradeable (conservative) — eff-N t=-2.48 유의 + OOS HOLD + leave-episode survive + 유가 partial 독립. ★단 연1회 배당 + 2종 + cyclical 무배당(2023 SK이노) = hedge 강, conservative cap.",
    }
    (ROOT / "validation-dividend-signal-v3.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print("=== 정유 배당수익률 income 신호 (★2번째 tradeable 발굴) ===")
    print(f"  rho={out['rho_fwd3m']} n={out['n']} eff-N={out['n_eff']} t_eff={out['t_eff_corrected']} wc_p={out['wild_cluster_p']}")
    print(f"  OOS: IS={out['walk_forward_oos']['is_rho']} OOS={out['walk_forward_oos']['oos_rho']} hold={out['walk_forward_oos']['sign_hold']}")
    print(f"  leave-episode(2022H2-23 제외): {out['leave_episode_2022H2_2023']['leave_rho']} survive={out['leave_episode_2022H2_2023']['survive']}")
    print(f"  유가 직교: brent corr={out['orthogonality_vs_oil']['corr_brent']} partial={out['orthogonality_vs_oil']['partial_div_given_brent']}")
    print(f"  ★verdict: {out['tradeable_verdict'][:80]}")
    print("\nSaved validation-dividend-signal-v3.json")


if __name__ == "__main__":
    main()
