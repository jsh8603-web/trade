"""liq-incremental.py — M3 유동성 factor 증분 가치 판정 (adopt vs 이중계상 reject).

외부 자문 "유동성 1순위 누락" framing 을 무비판 수용 X — 코드/데이터로 검증.
방법론 = batch-std-beta-9factor.py 미러(z-score std β · HAC NW=5 · VIF · uni+multi · ADF) +
FWL 직교화 incremental β + Newey-West HAC + Bonferroni + James-Stein tier(점추정 박제 금지).

★채택 게이트(cross-regime-ledger §6-Y5): covariance-prior factor 는 univariate screen 부족 →
joint incremental 통과 필수(기존 factor set 조건부 생존 + cross-sleeve 공분산 증분).
MOVE/slope 가 이 게이트서 drop(univariate 유의 → joint VIX 흡수 β→0).

후보 3: Net Liquidity(WALCL−WTREGEN−RRPONTSYD), NFCI, M2SL.
기준 production factor 7종(factor_returns.FACTOR_SERIES): real/dollar/oil/credit(HY OAS)/vol/breakeven/fx.
★credit(BAMLH0A0HYM2 HY OAS)=FRED 2023-06~만(BofA 라이센스). full-window robustness=BAA-AAA proxy 병행.

off-path 산출 전용. core/study 미수정.
"""
from __future__ import annotations

import json
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tsa.stattools import adfuller

warnings.filterwarnings("ignore")
os.environ.setdefault("PYTHONUTF8", "1")
from dotenv import load_dotenv
load_dotenv("D:/projects/Inv/.env")

ROOT = Path(r"D:\projects\Inv\study-research")
FRED = ROOT / "eq_us_defensive" / "raw" / "fred"
LIQ = ROOT / "_factor_shadow" / "_liq_cache"
OUT = ROOT / "_factor_shadow"

# production factor 7종 (factor_returns.FACTOR_SERIES). credit 변형 2 경로(HY OAS vs BAA-AAA proxy).
BASE_FACTORS = ["real", "dollar", "oil", "credit", "vol", "breakeven", "fx"]
LIQ_CANDS = ["net_liq", "nfci", "m2"]

SLEEVE_TICKERS = {  # sleeve_returns.SLEEVE_TICKERS 와 일치(us_stock·bond·gold·commodity·coin 등)
    "us_stock": "SPY", "kr_stock": "EWY", "commodity": "DBC",
    "gold": "GLD", "bond": "BND", "coin": "BTC-USD",
}


def _load_fred(name: str, folder=FRED) -> pd.Series:
    df = pd.read_csv(folder / f"{name}.csv")
    df.columns = ["date", "val"]
    df["date"] = pd.to_datetime(df["date"])
    s = pd.to_numeric(df["val"], errors="coerce")
    s.index = df["date"]
    return s.dropna()


def _load_liq(name: str) -> pd.Series:
    df = pd.read_csv(LIQ / f"{name}.csv", index_col=0, parse_dates=True)
    return pd.to_numeric(df["val"], errors="coerce").dropna()


def build_base_factors(credit_mode: str = "hyoas") -> pd.DataFrame:
    """production 7-factor (일별 혁신). credit_mode: 'hyoas'(BAMLH0A0HYM2, 2023-06~) | 'proxy'(BAA-AAA)."""
    dfii10 = _load_liq("DGS2") * 0  # placeholder unused
    dfii10 = _load_fred("DFII10")
    dxy = _load_fred("DTWEXBGS")
    oil = _load_fred("DCOILWTICO"); oil = oil[oil > 0]
    vix = _load_fred("VIXCLS")
    t5yie = _load_liq("T5YIE")
    fx = _load_liq("DEXKOUS")  # KRW per USD
    if credit_mode == "hyoas":
        credit = _load_liq("BAMLH0A0HYM2")
        credit_ret = credit.diff()
    else:
        baa = _load_fred("BAA10Y"); aaa = _load_fred("AAA10Y")
        credit_ret = (baa - aaa).dropna().diff()
    f = pd.DataFrame({
        "real": dfii10.diff(),
        "dollar": np.log(dxy).diff(),
        "oil": np.log(oil).diff(),
        "credit": credit_ret,
        "vol": vix.diff(),
        "breakeven": t5yie.diff(),
        "fx": np.log(fx).diff(),
    })
    return f.dropna()


def build_liq_candidates() -> pd.DataFrame:
    """유동성 후보 3 (일별 혁신). 주별/월별 → 일별 ffill 후 diff (계단 변화)."""
    walcl = _load_liq("WALCL")           # $M weekly
    wtregen = _load_liq("WTREGEN")       # $M weekly
    rrp = _load_liq("RRPONTSYD")         # $B daily
    nfci = _load_liq("NFCI")             # index weekly
    m2 = _load_liq("M2SL")               # $B monthly

    # Net Liquidity = WALCL($M) - WTREGEN($M) - RRP($B*1000) → $M. 일별 index 로 ffill.
    idx = pd.date_range("2003-01-01", "2026-06-01", freq="D")
    walcl_d = walcl.reindex(idx, method="ffill")
    wtregen_d = wtregen.reindex(idx, method="ffill")
    rrp_d = rrp.reindex(idx, method="ffill")
    net_liq_level = walcl_d - wtregen_d - rrp_d * 1000.0
    # Δlog (자산 가격류 — 잔액 변화율). 음수 가능성 없음(net liq>0).
    net_liq = np.log(net_liq_level.clip(lower=1)).diff()

    nfci_d = nfci.reindex(idx, method="ffill")
    nfci_ret = nfci_d.diff()             # NFCI 는 index(z류) → first-diff (level=tight/loose state)

    m2_d = m2.reindex(idx, method="ffill")
    m2_ret = np.log(m2_d).diff()         # Δlog M2

    out = pd.DataFrame({"net_liq": net_liq, "nfci": nfci_ret, "m2": m2_ret}, index=idx)
    # ffill-diff 는 변화 없는 날 0 → 실제 갱신일만 비0. 회귀선 0-inflation 완화 위해 그대로 두되 n 보고.
    return out


def fetch_prices(tickers: list) -> pd.DataFrame:
    import yfinance as yf
    cols = {}
    for t in tickers:
        h = yf.Ticker(t).history(period="max", auto_adjust=True)
        if len(h) == 0:
            raise RuntimeError(f"yfinance EMPTY for {t}")
        px = h["Close"].copy()
        px.index = pd.to_datetime(px.index).tz_localize(None)
        cols[t] = px
    return pd.DataFrame(cols)


def adf_p(s: pd.Series) -> float:
    s = s.dropna()
    if len(s) < 20:
        return float("nan")
    try:
        return float(adfuller(s.values, regression="c", autolag="AIC")[1])
    except Exception:
        return float("nan")


def zscore(s: pd.Series) -> pd.Series:
    sd = s.std(ddof=0)
    return (s - s.mean()) / sd if sd > 0 else s * 0.0


def hac_reg(y: pd.Series, X: pd.DataFrame, maxlags: int = 5):
    yz = zscore(y)
    Xz = X.apply(zscore)
    Xc = sm.add_constant(Xz)
    model = sm.OLS(yz.values, Xc.values).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})
    names = ["const"] + list(X.columns)
    out = {nm: (float(model.params[i]), float(model.bse[i]), float(model.tvalues[i]),
                float(model.pvalues[i])) for i, nm in enumerate(names)}
    out["_n"] = int(model.nobs); out["_r2"] = float(model.rsquared)
    return out


def compute_vif(X: pd.DataFrame) -> dict:
    Xz = X.apply(zscore)
    Xc = sm.add_constant(Xz).values
    cols = ["const"] + list(X.columns)
    return {cols[i]: float(variance_inflation_factor(Xc, i)) for i in range(1, len(cols))}


def tier_suggest(t, p, bonf_alpha):
    if not np.isfinite(t):
        return "hold"
    at = abs(t)
    if at >= 2.0 and p <= bonf_alpha:
        return "validated"
    if at >= 1.6:
        return "structural"
    return "reject"


def analyze(y: pd.Series, base: pd.DataFrame, liq: pd.DataFrame, cand: str,
            bonf_alpha: float) -> dict:
    """기존 7 + 후보 1 = 8 joint. 후보의 univariate / joint β / VIF / FWL incremental."""
    facs = BASE_FACTORS + [cand]
    X = base.join(liq[[cand]], how="inner")
    df = X.join(y.rename("y"), how="inner").dropna()
    if len(df) < 100:
        return {"n": len(df), "error": "insufficient"}
    yy = df["y"]; XX = df[facs]

    # univariate (후보 단독)
    ur = hac_reg(yy, XX[[cand]])
    uni = {"beta": round(ur[cand][0], 4), "se": round(ur[cand][1], 4),
           "t": round(ur[cand][2], 3), "p": round(ur[cand][3], 6), "n": ur["_n"]}

    # joint 8-factor multivariate
    mr = hac_reg(yy, XX)
    multi = {f: {"beta": round(mr[f][0], 4), "t": round(mr[f][2], 3), "p": round(mr[f][3], 6)}
             for f in facs}
    multi["_n"] = mr["_n"]; multi["_r2"] = round(mr["_r2"], 4)

    # VIF (8-factor) — 이중계상 검정
    vif = {k: round(v, 3) for k, v in compute_vif(XX).items()}

    # FWL incremental: 후보를 기존 7 에 회귀 → 잔차(직교 part) → y 에 회귀
    cand_on_base = sm.OLS(zscore(XX[cand]).values,
                          sm.add_constant(XX[BASE_FACTORS].apply(zscore)).values).fit()
    cand_orth = pd.Series(cand_on_base.resid, index=df.index)
    orth_var_share = float(np.var(cand_orth) / np.var(zscore(XX[cand]).values))
    inc = hac_reg(yy, cand_orth.to_frame("orth"))
    incremental = {"beta": round(inc["orth"][0], 4), "t": round(inc["orth"][2], 3),
                   "p": round(inc["orth"][3], 6), "orth_var_share": round(orth_var_share, 4)}

    # corr of candidate with each base factor (어느 factor 가 흡수하나)
    corr = {f: round(float(np.corrcoef(XX[cand], XX[f])[0, 1]), 3) for f in BASE_FACTORS}

    # tier (joint β 기준 — 점추정 박제 금지: t/p/Bonferroni 게이트)
    jt, jp = multi[cand]["t"], multi[cand]["p"]
    tier = tier_suggest(jt, jp, bonf_alpha)
    # 이중계상 추가 게이트: VIF≥5 또는 FWL incremental t<2 → reject 강등
    cand_vif = vif[cand]
    if cand_vif >= 5.0:
        tier = "reject_doublecount"
    elif abs(incremental["t"]) < 2.0 and tier in ("validated", "structural"):
        tier = "reject_absorbed"

    return {"coverage": [str(df.index.min().date()), str(df.index.max().date())], "n": len(df),
            "univariate": uni, "joint": {cand: multi[cand], "_n": multi["_n"], "_r2": multi["_r2"]},
            "joint_full": multi, "vif": vif, "incremental_fwl": incremental,
            "corr_with_base": corr, "tier": tier}


def main():
    results = {"_meta": {"title": "M3 유동성 factor 증분 판정 (adopt vs 이중계상)",
                         "date": "2026-06-02",
                         "method": "z-score std β · HAC NW=5 · VIF · FWL incremental · Bonferroni · James-Stein tier",
                         "base_factors": BASE_FACTORS, "liq_candidates": LIQ_CANDS,
                         "gate": "cross-regime-ledger §6-Y5: joint incremental 필수(univariate 부족)"},
               "credit_modes": {}}

    px = fetch_prices(list(SLEEVE_TICKERS.values()))
    ret = np.log(px).diff()
    tick_to_sleeve = {v: k for k, v in SLEEVE_TICKERS.items()}
    ret = ret.rename(columns=tick_to_sleeve)

    liq = build_liq_candidates()
    adf_liq = {c: round(adf_p(liq[c]), 6) for c in LIQ_CANDS}
    print(f"ADF(liq cand)={adf_liq}")
    print(f"liq cand non-zero days: " +
          ", ".join(f"{c}={int((liq[c].abs()>1e-12).sum())}" for c in LIQ_CANDS))

    for credit_mode in ["hyoas", "proxy"]:
        base = build_base_factors(credit_mode)
        adf_base = {f: round(adf_p(base[f]), 6) for f in BASE_FACTORS}
        print(f"\n##### credit_mode={credit_mode} base coverage "
              f"{base.index.min().date()}~{base.index.max().date()} n={len(base)}")
        print(f"ADF(base)={adf_base}")
        # Bonferroni: 6 sleeve × 3 candidate = 18 비교
        n_comp = len(SLEEVE_TICKERS) * len(LIQ_CANDS)
        bonf_alpha = 0.05 / n_comp
        mode_out = {"credit_mode": credit_mode,
                    "base_coverage": [str(base.index.min().date()), str(base.index.max().date())],
                    "base_n": len(base), "adf_base": adf_base, "adf_liq": adf_liq,
                    "bonferroni_alpha": round(bonf_alpha, 6), "n_comparisons": n_comp,
                    "sleeves": {}}
        for sleeve in SLEEVE_TICKERS:
            if sleeve not in ret.columns:
                continue
            y = ret[sleeve].dropna()
            mode_out["sleeves"][sleeve] = {}
            for cand in LIQ_CANDS:
                res = analyze(y, base, liq, cand, bonf_alpha)
                mode_out["sleeves"][sleeve][cand] = res
                if "error" in res:
                    print(f"  {sleeve:9s}/{cand:8s} INSUFFICIENT n={res['n']}")
                    continue
                u = res["univariate"]; j = res["joint"][cand]; fwl = res["incremental_fwl"]
                print(f"  {sleeve:9s}/{cand:8s} n={res['n']:5d} "
                      f"uni β={u['beta']:+.3f} t={u['t']:+.2f} | "
                      f"joint β={j['beta']:+.3f} t={j['t']:+.2f} | "
                      f"VIF={res['vif'][cand]:.2f} | "
                      f"FWL β={fwl['beta']:+.3f} t={fwl['t']:+.2f} orth={fwl['orth_var_share']:.2f} "
                      f"-> {res['tier']}")
        results["credit_modes"][credit_mode] = mode_out

    OUT.mkdir(exist_ok=True)
    (OUT / "liq-incremental.json").write_text(json.dumps(results, indent=2, ensure_ascii=False),
                                              encoding="utf-8")
    print("\nWROTE", OUT / "liq-incremental.json")
    return results


if __name__ == "__main__":
    main()
