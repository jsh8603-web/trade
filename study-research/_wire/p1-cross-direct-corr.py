"""p1-cross-direct-corr.py — P1 직접 cross-corr 실측 (cross-research C1/C2/C4/C5/C6/C9 추론 검증).

cross-research 는 "공유 factor 노출서 *추론*이지 직접 cross-corr 실측 아님" hedge.
본 스크립트 = 자산 수익률 간 **직접 Pearson 상관** (full + VIX risk-on/off regime split)을 실측해
batch β 추론 부호와 일치하는지 검증. 신규 fetch 최소화 (batch β 와 동일 yfinance source).

regime split = expanding-median(VIX) threshold + PIT-safe (full-sample median lookahead 차단).
모든 corr 에 [95% CI, n, p] + block-bootstrap CI. regime small-n 시 hedge.
★코드/yaml 미수정 (read-only 실측). 산출 = json + console.
"""
from __future__ import annotations
import json, warnings
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")
rng = np.random.default_rng(20260601)

ROOT = Path(r"D:\projects\Inv\study-research")
FRED = ROOT / "eq_us_defensive" / "raw" / "fred"
OUT = ROOT / "_wire"

# top5 직접 cross-corr 대상 페어 (sleeve 대표자산, batch β unit 정합)
SLEEVE_TICKERS = {
    "eq_cyclical": ["XLB", "XLI", "SOXX"],   # CYCLICAL_PRO
    "xle_energy": ["XLE"],
    "eq_intl": ["EFA", "EEM"],
    "reit": ["VNQ"],
    "commodity": ["DBC"],
    "gold": ["GLD"],
}
# 검증할 cross 페어 + batch β 추론 부호
PAIRS = [
    ("eq_cyclical", "eq_intl", "+", "C1 VIX+dollar 동조"),
    ("eq_cyclical", "reit", "+", "C2 VIX 공통"),
    ("eq_intl", "reit", "+", "C3 VIX+dollar"),
    ("commodity", "xle_energy", "+", "C4 oil 채널 본체"),
    ("gold", "commodity", "+", "C5 dollar 채널"),
    ("gold", "eq_intl", "?", "C6 dollar 양 / vol 반대 = net 모호"),
    ("xle_energy", "eq_cyclical", "+", "C9 def-cyc 게이트 인접(cyc 자기군)"),
    ("gold", "eq_cyclical", "?", "C7 risk-off hedge 후보(gold vol≈0)"),
]


def load_fred(name):
    df = pd.read_csv(FRED / f"{name}.csv")
    df.columns = ["date", "val"]
    df["date"] = pd.to_datetime(df["date"])
    s = pd.to_numeric(df["val"], errors="coerce")
    s.index = df["date"]
    return s.dropna()


def fetch_prices(tickers):
    import yfinance as yf
    cols = {}
    for t in tickers:
        h = yf.Ticker(t).history(period="max", auto_adjust=True)
        if len(h) == 0:
            raise RuntimeError(f"EMPTY {t}")
        px = h["Close"].copy()
        px.index = pd.to_datetime(px.index).tz_localize(None)
        cols[t] = px
    return pd.DataFrame(cols)


def sleeve_logret(px, sleeve):
    avail = [t for t in SLEEVE_TICKERS[sleeve] if t in px.columns]
    r = np.log(px[avail]).diff()
    return r.mean(axis=1).dropna()


def fisher_ci(r, n, alpha=0.05):
    if n < 4 or abs(r) >= 1:
        return (np.nan, np.nan)
    z = np.arctanh(r)
    se = 1.0 / np.sqrt(n - 3)
    zc = stats.norm.ppf(1 - alpha / 2)
    return (np.tanh(z - zc * se), np.tanh(z + zc * se))


def block_boot_ci(x, y, block=5, B=2000):
    n = len(x)
    if n < 20:
        return (np.nan, np.nan)
    x, y = np.asarray(x), np.asarray(y)
    nb = int(np.ceil(n / block))
    out = np.empty(B)
    for b in range(B):
        starts = rng.integers(0, n, size=nb)
        idx = np.concatenate([np.arange(s, s + block) % n for s in starts])[:n]
        out[b] = np.corrcoef(x[idx], y[idx])[0, 1]
    return (float(np.nanpercentile(out, 2.5)), float(np.nanpercentile(out, 97.5)))


def pearson_full(rx, ry):
    df = pd.concat([rx.rename("x"), ry.rename("y")], axis=1).dropna()
    n = len(df)
    if n < 10:
        return None
    r, p = stats.pearsonr(df["x"], df["y"])
    lo, hi = fisher_ci(r, n)
    blo, bhi = block_boot_ci(df["x"].values, df["y"].values)
    return {"r": round(float(r), 4), "p": float(p), "n": int(n),
            "ci95_fisher": [round(lo, 4), round(hi, 4)],
            "ci95_block_boot": [round(blo, 4), round(bhi, 4)]}


def main():
    all_t = sorted({t for v in SLEEVE_TICKERS.values() for t in v})
    px = fetch_prices(all_t)
    sret = {s: sleeve_logret(px, s) for s in SLEEVE_TICKERS}

    # VIX regime: expanding-median threshold (PIT-safe), daily VIX level
    vix = load_fred("VIXCLS")
    vix_d = vix.reindex(px.index).ffill()
    exp_med = vix_d.expanding(min_periods=250).median()
    riskoff = (vix_d >= exp_med)   # high-VIX = risk-off regime (PIT-safe, no full-sample median)

    n_pairs = len(PAIRS)
    bonf = 0.05 / n_pairs

    results = {"meta": {"price_source": "yfinance period=max auto_adjust",
                        "coverage": [str(px.index.min().date()), str(px.index.max().date())],
                        "regime": "VIX expanding-median (min_periods=250, PIT-safe)",
                        "n_cross_pairs": n_pairs, "bonferroni_alpha": round(bonf, 5)},
               "pairs": {}}

    print(f"coverage {results['meta']['coverage']}  Bonferroni a=0.05/{n_pairs}={bonf:.5f}\n")
    for a, b, exp_sign, note in PAIRS:
        full = pearson_full(sret[a], sret[b])
        # regime split (PIT-safe expanding-median VIX)
        df = pd.concat([sret[a].rename("x"), sret[b].rename("y"),
                        riskoff.rename("ro")], axis=1).dropna()
        ro = df[df["ro"]]
        ron = df[~df["ro"]]
        def reg_corr(d):
            if len(d) < 10:
                return {"n": int(len(d)), "verdict": "INSUFFICIENT"}
            r, p = stats.pearsonr(d["x"], d["y"])
            lo, hi = fisher_ci(r, len(d))
            return {"r": round(float(r), 4), "p": float(p), "n": int(len(d)),
                    "ci95": [round(lo, 4), round(hi, 4)]}
        rec = {"exp_sign": exp_sign, "note": note, "full": full,
               "riskoff": reg_corr(ro), "riskon": reg_corr(ron)}
        # sign-match vs inference
        if full:
            obs = "+" if full["r"] > 0 else "-"
            match = (exp_sign == "?" ) or (obs == exp_sign)
            surv = full["p"] < bonf
            rec["sign_match"] = match
            rec["bonf_survive"] = bool(surv)
        results["pairs"][f"{a}<->{b}"] = rec
        fr = full["r"] if full else None
        print(f"{a:13s}<->{b:13s} exp={exp_sign} | full r={fr} p={full['p']:.2e} n={full['n']} "
              f"CI{full['ci95_fisher']} bootCI{full['ci95_block_boot']} bonf_surv={rec['bonf_survive']}")
        print(f"   riskOFF: {rec['riskoff']}")
        print(f"   riskON : {rec['riskon']}\n")

    OUT.mkdir(exist_ok=True)
    (OUT / "p1-cross-direct-corr.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print("WROTE", OUT / "p1-cross-direct-corr.json")
    return results


if __name__ == "__main__":
    main()
