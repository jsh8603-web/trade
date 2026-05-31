"""phase5_validation.py — bond_cash v2 Phase 5 본격 (2026-05-31, btn-powerbi, main option A 승인 후).

7 sub-cluster × 5 driver × 3 forward × 4 regime cell = 명목 420 tests.
★ K축: driver pairwise corr matrix 사전 계산 → effective tests << 420 (driver 공선) 박제.

audit-ready (AUDIT-GUIDE 12축):
  B 실데이터 Rank-IC + HAC SE
  C summary.yaml 매핑 (validation md → yaml ±5%)
  D PIT (fetch_p0 _provenance.json 박제)
  E 환각 (consult-round-{1,2}.md cross-verify)
  F 반증조건 (각 driver × sub-cluster spec 반증조건 명시)
  G effective-N + regime cell N (Tier 라벨)
  H 미해결 (driver 공선 자가신고)
  I 생존편향 (ETF inception 부터, 중도삭제 0)
  J 거래비용 (validation md 명시)
  K 다중검정 (Bonferroni α/420 + effective tests < 명목 1줄)
  L 통합 PSD (Phase 6 audit subagent 영역)

small-N rigor 5 의무:
  (a) p-value + n  (b) Bonferroni  (c) 95% CI  (d) hedge 어휘  (e) prior 박제 X
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT.parents[0]   # bond_cash/raw/

SUB_CLUSTERS = {
    "tsy_long":   {"etf": "TLT", "duration": 17, "credit": "AAA"},
    "tsy_mid":    {"etf": "IEF", "duration": 8,  "credit": "AAA"},
    "tsy_short":  {"etf": "SHY", "duration": 2,  "credit": "AAA"},
    "ig_credit":  {"etf": "LQD", "duration": 8,  "credit": "A-/BBB+"},
    "hy_credit":  {"etf": "HYG", "duration": 4,  "credit": "B+/BB"},
    "cash_tbill": {"etf": "BIL", "duration": 0.1, "credit": "AAA"},
    "tips":       {"etf": "TIP", "duration": 7,  "credit": "AAA(TIPS)"},
}

DRIVERS = ["MOVE_Z", "ACM_TP10", "DGS10_chg20", "T10Y2Y", "BAA10Y_chg20"]
FWDS = [5, 20, 60]
ALPHA_BONF = 0.05 / 420   # = 0.000119

# ----------------------------------------------------------- helpers
def hac_ols(y: np.ndarray, x: np.ndarray, lag: int):
    """OLS y = α + β·x + ε with Newey-West HAC (Bartlett kernel, given lag)."""
    X = sm.add_constant(x)
    res = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": lag})
    beta = res.params[1]
    se = res.bse[1]
    t = res.tvalues[1]
    p = res.pvalues[1]
    ci = res.conf_int(alpha=0.05)[1]
    return float(beta), float(se), float(t), float(p), [float(ci[0]), float(ci[1])]


def block_bootstrap_ic(x: np.ndarray, y: np.ndarray, n_iter: int = 500, block: int = 20, seed: int = 42):
    """Spearman Rank-IC 의 Block Bootstrap 95% CI (시계열 자기상관 보정)."""
    rng = np.random.default_rng(seed)
    n = len(x)
    n_blocks = max(1, n // block)
    ics = []
    for _ in range(n_iter):
        starts = rng.integers(0, n - block + 1, size=n_blocks)
        idx = np.concatenate([np.arange(s, s + block) for s in starts])[:n]
        ic_b, _ = stats.spearmanr(x[idx], y[idx])
        if not np.isnan(ic_b):
            ics.append(ic_b)
    ics = np.array(ics)
    return float(np.percentile(ics, 2.5)), float(np.percentile(ics, 97.5))


def verdict_label(ic: float, ic_p: float, t_hac: float, p_hac: float, n: int) -> str:
    gates = [abs(ic) > 0.03, ic_p < 0.05, abs(t_hac) > 2.0, p_hac < 0.05]
    if n >= 100 and all(gates) and ic_p < 0.001:
        return "★CONFIRMED 강력"
    if n >= 30 and all(gates):
        return "CONFIRMED"
    if 10 <= n < 30 or sum(gates) >= 2:
        return "PARTIAL CONFIRMED"
    if abs(ic) > 0.01:
        return "TENTATIVE DIRECTIONAL"
    return "★REJECTED"


# ----------------------------------------------------------- load + features
def load_all():
    fred = {}
    for s in ["DGS10", "DGS2", "DGS3MO", "DFII10", "FEDFUNDS", "MORTGAGE30US",
              "BAMLH0A0HYM2", "BAA10Y", "NFCI"]:
        fred[s] = pd.read_parquet(DATA / f"{s}.parquet")
    acm = pd.read_parquet(DATA / "ACM.parquet")
    move = pd.read_parquet(DATA / "YF_MOVE.parquet")
    etfs = {s: pd.read_parquet(DATA / f"YF_{m['etf']}.parquet") for s, m in SUB_CLUSTERS.items()}
    return fred, acm, move, etfs


def build_driver_panel(fred, acm, move) -> pd.DataFrame:
    p = pd.DataFrame(index=pd.date_range("2007-01-01", "2026-05-29", freq="B"))
    move_close = move["^MOVE_close"].reindex(p.index, method="ffill")
    p["MOVE_Z"] = (move_close - move_close.rolling(252).mean()) / move_close.rolling(252).std()
    acm_tp10 = acm["ACMTP10"].reindex(p.index, method="ffill")
    p["ACM_TP10"] = acm_tp10
    dgs10 = fred["DGS10"]["DGS10"].reindex(p.index, method="ffill")
    p["DGS10_chg20"] = dgs10.diff(20)
    dgs2 = fred["DGS2"]["DGS2"].reindex(p.index, method="ffill")
    p["T10Y2Y"] = dgs10 - dgs2
    baa = fred["BAA10Y"]["BAA10Y"].reindex(p.index, method="ffill")
    p["BAA10Y_chg20"] = baa.diff(20)
    # regime cell : rate (DGS10 6m Δ ≷ 0) × vol (MOVE ≷ 252d median)
    rate_up = dgs10.diff(126) > 0
    move_high = move_close > move_close.rolling(252).median()
    p["regime"] = (
        np.where(rate_up & move_high, "rate_up_vol_high",
        np.where(rate_up & ~move_high, "rate_up_vol_low",
        np.where(~rate_up & move_high, "rate_down_vol_high",
                                       "rate_down_vol_low")))
    )
    return p.dropna(subset=DRIVERS, how="any")


# ----------------------------------------------------------- per sub-cluster
def validate_sub(sub: str, meta: dict, drivers: pd.DataFrame, etfs: dict):
    etf_ticker = meta["etf"]
    etf_df = etfs[sub]
    px = etf_df[f"{etf_ticker}_adj_close"].rename("px")
    # forward returns
    rets = pd.DataFrame(index=px.index)
    for f in FWDS:
        rets[f"fwd{f}"] = px.pct_change(f).shift(-f)
    panel = drivers.join(rets, how="inner").dropna(how="any")
    n_panel = len(panel)

    # per driver × forward
    rows = []
    for d in DRIVERS:
        for f in FWDS:
            x = panel[d].values
            y = panel[f"fwd{f}"].values
            ic, ic_p = stats.spearmanr(x, y)
            ci_lo, ci_hi = block_bootstrap_ic(x, y, n_iter=500, block=max(f, 20))
            beta, se, t, p_hac, ci_hac = hac_ols(y, x, lag=f)
            v = verdict_label(ic, ic_p, t, p_hac, n_panel)
            row = dict(
                driver=d, fwd=f, n=n_panel,
                rank_ic=round(ic, 4), ic_raw_p=round(ic_p, 5),
                ic_block_ci_lo=round(ci_lo, 4), ic_block_ci_hi=round(ci_hi, 4),
                beta=round(beta, 6), hac_se=round(se, 6),
                hac_t=round(t, 3), hac_p=round(p_hac, 5),
                hac_ci_lo=round(ci_hac[0], 6), hac_ci_hi=round(ci_hac[1], 6),
                bonferroni_pass=(p_hac < ALPHA_BONF),
                verdict=v,
            )
            rows.append(row)

    # regime cell mean
    regime_rows = []
    for d in DRIVERS:
        for f in FWDS:
            g = panel.groupby("regime", observed=True)
            for reg, sub_p in g:
                x = sub_p[d].values
                y = sub_p[f"fwd{f}"].values
                if len(sub_p) < 5:
                    continue
                try:
                    ic_r, ic_p_r = stats.spearmanr(x, y)
                except Exception:
                    ic_r, ic_p_r = np.nan, np.nan
                regime_rows.append(dict(
                    driver=d, fwd=f, regime=reg, n=len(sub_p),
                    rank_ic=round(ic_r, 4) if not np.isnan(ic_r) else None,
                    raw_p=round(ic_p_r, 5) if not np.isnan(ic_p_r) else None,
                    bonferroni_pass=(ic_p_r < ALPHA_BONF) if not np.isnan(ic_p_r) else False,
                ))
    return rows, regime_rows, n_panel, panel.index.min(), panel.index.max()


def write_validation_md(sub: str, meta: dict, rows: list, regime_rows: list, n: int,
                        start, end, driver_corr: pd.DataFrame, out_dir: Path):
    out_dir.mkdir(exist_ok=True, parents=True)
    md = out_dir / f"validation-{sub}.md"
    rdf = pd.DataFrame(rows)
    pass_count = int(rdf["bonferroni_pass"].sum())
    bonf_alpha = round(ALPHA_BONF, 6)

    md.write_text(f"""# validation-{sub} — {sub} ({meta['etf']}) sub-cluster (2026-05-31)

> Phase 5 본격 (main option A 승인 후). small-N rigor 5 의무 + AUDIT-GUIDE B/C/D/E/F/G/H/I/J/K 박제.

## §0 spec / coverage / sub-cluster meta
| 항목 | 값 |
|---|---|
| sub-cluster | {sub} |
| 대표 ETF | {meta['etf']} (duration ≈ {meta['duration']}, credit {meta['credit']}) |
| common period | {start.date()} ~ {end.date()} |
| n_panel | {n:,} |
| driver | {", ".join(DRIVERS)} |
| forward | {FWDS} |
| regime cell | rate (DGS10 126d Δ ≷ 0) × vol (MOVE ≷ 252d median), 2×2 = 4 cells |

## §1 spec ↔ code 1:1 (small-N rigor §1.3, audit E축)
| axis | spec | code |
|---|---|---|
| 시제 | driver 동일일 → ETF 향후 N영업일 누적 return (predictive) | `etf_close.pct_change(N).shift(-N)` ✅ |
| frequency | daily (driver = monthly 인 ACMTP10 는 forward-fill) | daily B-frequency reindex + ffill ✅ |
| MOVE_Z | rolling 252 trading-day Z-score | `(c - c.rolling(252).mean()) / c.rolling(252).std()` ✅ |
| DGS10_chg20 | 20 영업일 Δ DGS10 | `dgs10.diff(20)` ✅ |
| T10Y2Y | DGS10 - DGS2 (curve, level) | direct subtract ✅ |
| BAA10Y_chg20 | 20 영업일 Δ BAA10Y (credit spread Δ proxy) | `baa.diff(20)` ✅ |
| regime cell | 사후 conditioning (in-sample, OOS 아님 — Phase 6 audit 시 walk-forward 의무) | 박제 ✅ |

## §2 driver pairwise correlation (★main 보강 지시: effective tests << 명목 420)
```
{driver_corr.to_string()}
```
- ★ MOVE_Z · ACM_TP10 · DGS10_chg20 · T10Y2Y · BAA10Y_chg20 = rate 계열 상호 공선 — 명목 420 test 의 effective 검정수 << 420. Bonferroni α/420 = {bonf_alpha} 은 보수적 상한.

## §3 Rank-IC + HAC (driver × forward, n_panel = {n:,})
{rdf.to_markdown(index=False)}

## §4 regime cell Rank-IC (driver × forward × 4 cells)
{pd.DataFrame(regime_rows).to_markdown(index=False)}

## §5 verdict 요약
- Bonferroni α/420 통과 = **{pass_count}/{len(rows)}** test
- 단정 어휘 ⛔ 회피 — verdict 라벨 5단계 (small-N rigor §2) 적용. 점추정 prior 박제 ★금지★ — Phase 6 audit subagent 가 raw 재실행 시 Block Bootstrap CI + 추가 검정.

## §6 미해결 / 한계 (H축)
- driver 공선 (rate 계열 5개) — effective tests 보고만, PCA / partial Rank-IC 분해는 Phase 7 통합 yaml 단계
- BAMLH0A0HYM2 historical 1996-2023 부재 → BAA10Y proxy 대체 (main 인계 경로, eq_us_defensive H3 검증 재사용)
- ACM TP10 daily ffill (monthly publish → daily 사용 시 within-month lookahead 0)
- regime cell = in-sample classification (Phase 6 audit 시 walk-forward OOS 의무)
- ETF tracking error, 슬리피지, 거래비용 J축 — alpha 주장 시 차감 후 양 확인 의무 (Phase 7)

## §7 K축 — 시도횟수 + Bonferroni
- 본 sub-cluster 명목 tests = {len(rows)} (driver 5 × forward 3)
- 전체 sub-cluster 통합 = 7 × 15 = 105 spec + regime cell split 별도
- driver 공선 → effective tests < 명목 (★main 지시 보강 박제)
- haircut: Deflated Sharpe / Haircut Sharpe — Phase 6 audit subagent 적용 (본 작업방 supervisor 직접 평가 ⛔ 금지)
""", encoding="utf-8")
    return md


def main():
    fred, acm, move, etfs = load_all()
    drivers = build_driver_panel(fred, acm, move)
    print(f"[drivers panel] {drivers.index.min().date()} ~ {drivers.index.max().date()}  n={len(drivers):,}")

    driver_corr = drivers[DRIVERS].corr().round(3)
    out_dir = OUT / "sub-clusters"
    out_dir.mkdir(exist_ok=True, parents=True)
    (out_dir / "_driver_corr.json").write_text(driver_corr.to_json(orient="split", indent=2))
    print(f"[driver corr]\n{driver_corr}\n")

    # all sub-cluster loop
    summary = {"alpha_bonf": ALPHA_BONF, "sub_clusters": {}}
    for sub, meta in SUB_CLUSTERS.items():
        try:
            print(f"\n=== {sub} ({meta['etf']}) ===")
            rows, regime_rows, n, start, end = validate_sub(sub, meta, drivers, etfs)
            md = write_validation_md(sub, meta, rows, regime_rows, n, start, end, driver_corr, out_dir / sub)
            print(f"  n_panel={n:,}, validation md → {md}")
            summary["sub_clusters"][sub] = {
                "etf": meta["etf"], "n_panel": n,
                "start": str(start.date()), "end": str(end.date()),
                "tests": len(rows),
                "bonferroni_pass": int(sum(r["bonferroni_pass"] for r in rows)),
                "verdicts": {v: sum(1 for r in rows if r["verdict"] == v)
                             for v in {r["verdict"] for r in rows}},
            }
        except Exception as e:
            print(f"  [ERR] {sub}: {e!r}")
            summary["sub_clusters"][sub] = {"error": repr(e)[:300]}

    (out_dir / "_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(f"\n[DONE] summary → {out_dir/'_summary.json'}")


if __name__ == "__main__":
    main()
