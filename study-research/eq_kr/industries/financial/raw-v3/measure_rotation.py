# -*- coding: utf-8 -*-
"""measure_rotation.py — financial 업종 rotation timing 신호 (team-lead 지시 2026-06-05).

★임무 = 금융 업종 ★자체 rotation(어느 국면 → 금융 비중 OW/UW). 종목selection(완료)과 별 차원.
★핵심 판별 (rotation-analyst v2 = financial cli_chg type=MACRO 분류 정정):
   금리커브/credit가 금융 ★고유 rotation 신호인가 vs 시장 전체 timing인가?
   = ★상대수익률(financial eq-weight − KOSPI) 예측하면 금융 고유 / 절대수익만 예측하면 시장 timing.

이론 (theory-notes rotation §, Gemini 리서치 + 증권사 금융전략):
  Q1 term spread(10Y-3Y) 확대 → 금융 상대수익 ★양(+) OW [금융 고유 strong, Flannery-James 1984]
  Q2 credit spread(AA−-국고3Y) 확대 → 금융 상대수익 ★음(−) UW [금융 고유 strong, Merton 1974]
  Q3 대출성장(ECOS 총대출금 yoy) → 금융 상대수익 양(+) OW [moderate 후행]
  Q4 침체/금리하락 → 금융 상대수익 음(−) UW [시장 timing, cyclical beta]
  Q5 momentum → 시장 momentum×beta (data mining, 채택불가 판별)

측정 설계 (rotation-analyst 미러):
  - 분석 unit = financial eq-weight 패널 월수익 (종목 cross-section 아님).
  - ★종속변수 2종: (a) 절대 forward(financial eq-weight) (b) ★상대 forward(financial − KOSPI) ← 판별 핵심.
  - 신호 = term_spread_d / credit_spread_d / loan_growth_yoy / mom_3·mom_6 (절대·상대).
  - 게이트 G-G v2: forward IC(20d/60d) + walk-forward OOS(IS2019-22/OOS2023-26) + wild-cluster + MDE/power + 단일 FDR(BY).
  - ★판별: 상대수익 IC 유의 + 부호 일치 = 금융 고유 채택 / 절대만 유의 = 시장 timing / 이론없이 통계만 = data mining 채택불가.

raw 재현: prices/regime_labels parquet + ECOS 대출 + FDR KS11 + 본 .py.
"""
from __future__ import annotations
import sys, io, os, json, time
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

ENV = Path("D:/projects/Inv/.env")
if ENV.exists():
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1); os.environ.setdefault(k.strip(), v.strip().strip('"'))
ECOS_KEY = os.environ.get("ECOS_API_KEY", "")

HORIZONS_M = {"y_20d": 1, "y_60d": 3}   # 월단위 (rotation = 월 패널)


def ecos_monthly_loan() -> pd.Series:
    """ECOS 104Y016 총대출금(BDCA1) 월별 → 대출성장 yoy."""
    pieces = []
    url = (f"https://ecos.bok.or.kr/api/StatisticSearch/{ECOS_KEY}/json/kr/1/1000/"
           f"104Y016/M/201801/202605/BDCA1")
    try:
        j = __import__("requests").get(url, timeout=40).json()
        for row in j.get("StatisticSearch", {}).get("row", []):
            t = row.get("TIME", ""); dv = row.get("DATA_VALUE", "")
            if t and dv not in ("", None):
                pieces.append((pd.Timestamp(f"{t[:4]}-{t[4:6]}-01") + pd.offsets.MonthEnd(0), float(dv)))
    except Exception as e:
        print(f"  ECOS loan FAIL {repr(e)[:60]}")
    if not pieces:
        return pd.Series(dtype=float)
    return pd.Series(dict(pieces)).sort_index()


def load():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    lab = pd.read_parquet(DATA / "regime_labels.parquet"); lab.index = pd.to_datetime(lab.index)
    uni = pd.read_parquet(DATA / "universe.parquet"); uni = uni[uni["pass_floor"]].set_index("Code")
    return px, lab, uni


def build_panels(px, lab):
    """financial eq-weight 월수익 + KOSPI 월수익 + 상대수익."""
    pxm = px.resample("ME").last()
    fin_ret = pxm.pct_change().mean(axis=1)   # eq-weight 월수익 (종목 평균)
    # KOSPI 벤치마크
    import FinanceDataReader as fdr
    ks = fdr.DataReader("KS11", "2018-01-01", "2026-05-29")["Close"]
    ks.index = pd.to_datetime(ks.index)
    ks_m = ks.resample("ME").last()
    ks_ret = ks_m.pct_change()
    rel_ret = fin_ret - ks_ret.reindex(fin_ret.index)   # ★상대수익 (financial − KOSPI)
    return fin_ret, ks_ret, rel_ret, pxm


def build_signals(lab, px):
    """rotation 신호 (월말 시점, ex-ante). 금융 고유 cycle + momentum."""
    pxm = px.resample("ME").last()
    fin_ret = pxm.pct_change().mean(axis=1)
    fin_idx = (1 + fin_ret.fillna(0)).cumprod()   # financial eq-weight 지수
    m = lab.resample("ME").last()
    sigs = {}
    # Q1 term spread 변화 (3M Δ) — 금융 고유 NIM
    term = m["term_spread"]
    sigs["term_spread_d3"] = term - term.shift(3)
    # Q2 credit spread 변화 (3M Δ) — 금융 고유 신용위험 (부호 음 예상)
    cs = m["credit_spread"]
    sigs["credit_spread_d3"] = cs - cs.shift(3)
    # Q3 대출성장 yoy
    loan = ecos_monthly_loan()
    if len(loan):
        loan_yoy = loan / loan.shift(12) - 1
        sigs["loan_growth_yoy"] = loan_yoy.reindex(m.index, method="ffill")
    # Q5 momentum (절대·상대) — data mining 차단 대상
    sigs["mom_3"] = fin_idx / fin_idx.shift(3) - 1
    sigs["mom_6"] = fin_idx / fin_idx.shift(6) - 1
    return sigs


def forward_ret(ret_series, anchor, h_m):
    """anchor 월말부터 h개월 forward 누적수익."""
    cum = (1 + ret_series.fillna(0)).cumprod()
    out = {}
    for dt in anchor:
        if dt not in cum.index:
            continue
        pos = cum.index.get_loc(dt)
        if pos + h_m >= len(cum.index):
            continue
        out[dt] = cum.iloc[pos + h_m] / cum.iloc[pos] - 1
    return pd.Series(out)


def ts_ic(sig, fwd):
    """시계열 Spearman corr (rotation = 시계열 예측)."""
    common = sig.dropna().index.intersection(fwd.dropna().index)
    if len(common) < 10:
        return None
    rho, _ = stats.spearmanr(sig.loc[common], fwd.loc[common])
    return {"rho": rho, "n": len(common)}


def wild_cluster_p_ts(sig, fwd, B=2000, seed=42):
    """시계열 rho wild-cluster p (Rademacher block)."""
    common = sig.dropna().index.intersection(fwd.dropna().index)
    n = len(common)
    if n < 10:
        return None
    x = sig.loc[common].rank().values; y = fwd.loc[common].rank().values
    x = x - x.mean(); y = y - y.mean()
    rho_obs = abs((x @ y) / (np.sqrt((x @ x) * (y @ y)) + 1e-12))
    rng = np.random.default_rng(seed); cnt = 0
    for _ in range(B):
        w = rng.choice([-1.0, 1.0], size=n)
        yb = w * y
        rb = abs((x @ yb) / (np.sqrt((x @ x) * (yb @ yb)) + 1e-12))
        if rb >= rho_obs:
            cnt += 1
    return (cnt + 1) / (B + 1)


def mde_check(sig, fwd, n_eff=None):
    """MDE/power (G-G v2): detectable |rho| at n. t_obs ⋚ 2.802."""
    common = sig.dropna().index.intersection(fwd.dropna().index)
    n = len(common) if n_eff is None else n_eff
    if n < 10:
        return None
    rho = stats.spearmanr(sig.loc[common], fwd.loc[common])[0]
    t_obs = rho * np.sqrt((n - 2) / (1 - rho**2 + 1e-9))
    mde = 2.802 / np.sqrt(n)   # detectable rho at power 0.8
    return {"rho": round(rho, 4), "t_obs": round(t_obs, 2), "mde": round(mde, 4),
            "powered": abs(t_obs) >= 2.802, "detectable": abs(rho) >= mde}


def walk_forward(sig, ret_series, h_m):
    """IS(2019-22)/OOS(2023-26) 시계열 rho 부호유지."""
    cum = (1 + ret_series.fillna(0)).cumprod()
    anchor = sig.dropna().index
    fwd = forward_ret(ret_series, anchor, h_m)
    IS = [d for d in fwd.index if d.year <= 2022]
    OOS = [d for d in fwd.index if d.year >= 2023]
    def rho_sub(idx):
        c = sig.loc[idx].dropna().index.intersection(fwd.loc[idx].dropna().index) if idx else []
        if len(c) < 6:
            return None
        return float(stats.spearmanr(sig.loc[c], fwd.loc[c])[0])
    r_is = rho_sub(IS); r_oos = rho_sub(OOS)
    return {"IS_rho": round(r_is, 4) if r_is is not None else None,
            "OOS_rho": round(r_oos, 4) if r_oos is not None else None,
            "sign_hold": bool(r_is is not None and r_oos is not None and np.sign(r_is) == np.sign(r_oos))}


def benjamini_yekutieli(pvals, q=0.10):
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    m = len(items)
    if m == 0:
        return {"m": 0}
    items.sort(key=lambda x: x[1])
    c_m = sum(1.0 / i for i in range(1, m + 1)); survivors = []
    for rank_i, (k, p) in enumerate(items, 1):
        if p <= (rank_i / m) * q / c_m:
            survivors = [items[j][0] for j in range(rank_i)]
    return {"m": m, "by_factor": round(c_m, 3), "survivors_BY": survivors,
            "raw_p_min": round(items[0][1], 5) if items else None, "raw_p_min_key": items[0][0] if items else None}


def main():
    px, lab, uni = load()
    fin_ret, ks_ret, rel_ret, pxm = build_panels(px, lab)
    sigs = build_signals(lab, px)
    print(f"signals: {list(sigs.keys())}")
    print(f"  financial eq-weight 월수익 n={fin_ret.notna().sum()}, KOSPI n={ks_ret.notna().sum()}")

    results = {"meta": {
        "임무": "financial 업종 rotation timing (어느 국면→금융 OW/UW)",
        "판별": "★상대수익(financial−KOSPI) 예측=금융고유 / 절대만=시장timing / 이론없이=data mining",
        "이론": "Q1 term spread+ (Flannery-James 1984) / Q2 credit spread− (Merton 1974) / Q3 loan growth+ / Q4 침체− cyclical / Q5 momentum=market×beta",
        "rotation_analyst_v2": "financial cli_chg +0.482 type=MACRO(N_eff≈1 시장timing) → 본 측정 = 금융 고유 driver(금리커브/credit/대출) 판별",
    }}

    targets = {"absolute": fin_ret, "relative": rel_ret}   # ★판별 핵심: 절대 vs 상대
    surface = {}
    pvals = {}
    for sname, sig in sigs.items():
        surface[sname] = {}
        for tname, tgt in targets.items():
            surface[sname][tname] = {}
            for hname, h in HORIZONS_M.items():
                anchor = sig.dropna().index
                fwd = forward_ret(tgt, anchor, h)
                ic = ts_ic(sig, fwd)
                if ic is None:
                    continue
                wc = wild_cluster_p_ts(sig, fwd)
                mde = mde_check(sig, fwd)
                wf = walk_forward(sig, tgt, h)
                surface[sname][tname][hname] = {
                    "rho": round(ic["rho"], 4), "n": ic["n"], "wild_cluster_p": round(wc, 4) if wc else None,
                    "mde": mde, "walk_forward": wf,
                }
                if wc is not None:
                    pvals[f"{sname}__{tname}__{hname}"] = wc
    results["rotation_surface"] = surface
    results["fdr_family"] = benjamini_yekutieli(pvals)

    out = ROOT / "validation-rotation-v3.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved {out}")
    print_summary(results)
    return results


def print_summary(r):
    print("\n" + "=" * 80)
    print("FINANCIAL ROTATION — 절대 vs ★상대(financial−KOSPI) 판별")
    print("=" * 80)
    for sname, td in r["rotation_surface"].items():
        print(f"\n[{sname}]")
        for tname in ["absolute", "relative"]:
            for hname, cv in td.get(tname, {}).items():
                mde = cv.get("mde", {})
                star = "★" if tname == "relative" else " "
                pw = "POWERED" if mde.get("powered") else "underpow"
                print(f"  {star}{tname:9s} {hname}: rho={cv['rho']:+.4f} n={cv['n']} wc_p={cv['wild_cluster_p']} t={mde.get('t_obs')} {pw} | OOS {cv['walk_forward']['OOS_rho']} hold={cv['walk_forward']['sign_hold']}")
    fdr = r["fdr_family"]
    print(f"\nFDR family: m={fdr.get('m')} BY_survivors={fdr.get('survivors_BY')} raw_p_min={fdr.get('raw_p_min')}({fdr.get('raw_p_min_key')})")


if __name__ == "__main__":
    main()
