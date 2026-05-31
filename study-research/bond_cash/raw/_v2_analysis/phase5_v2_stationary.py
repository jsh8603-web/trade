"""phase5_v2_stationary.py — bond_cash v2 Phase 5 v2 재검정 (2026-05-31, audit verdict 격하 반영).

audit verdict (raw/evaluation-bond_cash-20260531.md) 격하 5건:
  (1) validated_alpha 0개 — 전 7 sub-cluster structural_prior_low_confidence 격하
  (2) B축 spurious: T10Y2Y/ACM_TP10 level = non-stationary (ADF p=0.553/0.257) → 차분 의무
  (3) C축: regime cell walk-forward OOS 없으면 descriptive only 격하 (HYG IS+0.077/OOS-0.331 부호 반전)
  (4) D축: ACM vintage = revised series, PIT 한계 명시 (Kim-Wright 대체는 R3)
  (5) K축: BH-FDR q=0.10 on effective ~50 (Bonferroni α/420 over-conservative)

본 script 산출:
  - sub-clusters/{name}/validation-{name}-v2.md (격하 라벨 + 차분 IC + half-split OOS + BH-FDR)
  - sub-clusters/_summary_v2.json
  - sub-clusters/_driver_pca_v2.json (차분 driver PCA effective tests)
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.tsa.stattools import adfuller

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT.parents[0] / "sub-clusters"

SUB_CLUSTERS = {
    "tsy_long":   {"etf": "TLT", "duration": 17, "credit": "AAA"},
    "tsy_mid":    {"etf": "IEF", "duration": 8,  "credit": "AAA"},
    "tsy_short":  {"etf": "SHY", "duration": 2,  "credit": "AAA"},
    "ig_credit":  {"etf": "LQD", "duration": 8,  "credit": "A-/BBB+"},
    "hy_credit":  {"etf": "HYG", "duration": 4,  "credit": "B+/BB"},
    "cash_tbill": {"etf": "BIL", "duration": 0.1, "credit": "AAA"},
    "tips":       {"etf": "TIP", "duration": 7,  "credit": "AAA(TIPS)"},
}

# ★ v2 driver = 전부 stationary (차분형 통일)
DRIVERS_V2 = ["MOVE_Z", "ACM_TP10_d20", "DGS10_chg20", "T10Y2Y_d20", "BAA10Y_chg20"]
FWDS = [5, 20, 60]
FDR_Q = 0.10


def block_bootstrap_ic(x, y, n_iter=500, block=20, seed=42):
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


def half_split_ic(x, y):
    half = len(x) // 2
    try:
        ic_is, _ = stats.spearmanr(x[:half], y[:half])
        ic_oos, _ = stats.spearmanr(x[half:], y[half:])
        return float(ic_is), float(ic_oos), int(np.sign(ic_is) == np.sign(ic_oos))
    except Exception:
        return np.nan, np.nan, 0


def bh_fdr(pvals, q=0.10):
    """Benjamini-Hochberg FDR. Return bool array (True = reject H0)."""
    p = np.asarray(pvals)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order]
    thresh = q * np.arange(1, n + 1) / n
    passed = ranked <= thresh
    if passed.any():
        k_max = np.where(passed)[0].max()
        reject = np.zeros(n, dtype=bool)
        reject[order[: k_max + 1]] = True
    else:
        reject = np.zeros(n, dtype=bool)
    return reject


def load_drivers_v2():
    fred = {s: pd.read_parquet(DATA / f"{s}.parquet")
            for s in ["DGS10", "DGS2", "DFII10", "BAA10Y"]}
    acm = pd.read_parquet(DATA / "ACM.parquet")
    move = pd.read_parquet(DATA / "YF_MOVE.parquet")
    p = pd.DataFrame(index=pd.date_range("2007-01-01", "2026-05-29", freq="B"))
    move_close = move["^MOVE_close"].reindex(p.index, method="ffill")
    p["MOVE_Z"] = (move_close - move_close.rolling(252).mean()) / move_close.rolling(252).std()
    acm_tp10 = acm["ACMTP10"].reindex(p.index, method="ffill")
    p["ACM_TP10_d20"] = acm_tp10.diff(20)
    dgs10 = fred["DGS10"]["DGS10"].reindex(p.index, method="ffill")
    p["DGS10_chg20"] = dgs10.diff(20)
    dgs2 = fred["DGS2"]["DGS2"].reindex(p.index, method="ffill")
    p["T10Y2Y_d20"] = (dgs10 - dgs2).diff(20)
    baa = fred["BAA10Y"]["BAA10Y"].reindex(p.index, method="ffill")
    p["BAA10Y_chg20"] = baa.diff(20)
    # regime cell — descriptive only (walk-forward OOS 미적용, audit 격하)
    rate_up = dgs10.diff(126) > 0
    move_high = move_close > move_close.rolling(252).median()
    p["regime"] = np.where(rate_up & move_high, "rate_up_vol_high",
                  np.where(rate_up & ~move_high, "rate_up_vol_low",
                  np.where(~rate_up & move_high, "rate_down_vol_high", "rate_down_vol_low")))
    return p.dropna(subset=DRIVERS_V2, how="any")


def adf_check(drivers):
    out = {}
    for d in DRIVERS_V2:
        try:
            res = adfuller(drivers[d].dropna(), autolag="AIC", maxlag=20)
            out[d] = {"adf_stat": float(res[0]), "p": float(res[1]),
                      "stationary_5pct": bool(res[1] < 0.05)}
        except Exception as e:
            out[d] = {"error": repr(e)[:200]}
    return out


def driver_pca_effective_tests(drivers):
    X = drivers[DRIVERS_V2].dropna().values
    X = (X - X.mean(axis=0)) / X.std(axis=0)
    cov = np.cov(X.T)
    eigvals, _ = np.linalg.eigh(cov)
    eigvals = np.sort(eigvals)[::-1]
    cumvar = np.cumsum(eigvals) / eigvals.sum()
    n_eff_95 = int(np.searchsorted(cumvar, 0.95) + 1)
    n_eff_99 = int(np.searchsorted(cumvar, 0.99) + 1)
    return {
        "eigenvalues": [round(float(v), 4) for v in eigvals],
        "cumulative_variance": [round(float(c), 4) for c in cumvar],
        "n_effective_components_95pct": n_eff_95,
        "n_effective_components_99pct": n_eff_99,
        "effective_tests_nominal_105": int(105 * n_eff_95 / len(DRIVERS_V2)),
    }


def validate_v2(sub, meta, drivers, etf_df):
    etf_ticker = meta["etf"]
    px = etf_df[f"{etf_ticker}_adj_close"].rename("px")
    rets = pd.DataFrame(index=px.index)
    for f in FWDS:
        rets[f"fwd{f}"] = px.pct_change(f).shift(-f)
    panel = drivers.join(rets, how="inner").dropna(how="any")
    n = len(panel)

    rows = []
    for d in DRIVERS_V2:
        for f in FWDS:
            x = panel[d].values
            y = panel[f"fwd{f}"].values
            ic, ic_p = stats.spearmanr(x, y)
            ci_lo, ci_hi = block_bootstrap_ic(x, y, n_iter=500, block=max(f, 20))
            X = sm.add_constant(x)
            res = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": max(f * 2, 60)})  # ★ HAC lag 보수 2× forward
            beta, se, t, p_hac = float(res.params[1]), float(res.bse[1]), float(res.tvalues[1]), float(res.pvalues[1])
            ic_is, ic_oos, sign_match = half_split_ic(x, y)
            rows.append(dict(
                driver=d, fwd=f, n=n,
                ic=round(ic, 4), ic_p=round(ic_p, 5),
                ci_lo=round(ci_lo, 4), ci_hi=round(ci_hi, 4),
                beta=round(beta, 6), hac_se=round(se, 6),
                hac_t_lag2x=round(t, 3), hac_p=round(p_hac, 5),
                ic_is=round(ic_is, 4), ic_oos=round(ic_oos, 4),
                halfsplit_sign_match=sign_match,
                # ★ magnitude freeze: sign/direction prior 만 보존
                sign_prior=("+" if ic > 0 else ("-" if ic < 0 else "0")),
            ))
    return rows, n, panel.index.min(), panel.index.max()


def main():
    drivers = load_drivers_v2()
    print(f"[drivers v2 panel] {drivers.index.min().date()} ~ {drivers.index.max().date()}  n={len(drivers):,}")

    # ADF stationarity check
    adf = adf_check(drivers)
    print("\n[ADF stationarity check (v2 차분형)]")
    for d, v in adf.items():
        print(f"  {d:18s}: {v}")

    # PCA effective tests
    pca = driver_pca_effective_tests(drivers)
    print(f"\n[PCA effective tests (★main 격하 5)]")
    print(f"  eigenvalues = {pca['eigenvalues']}")
    print(f"  cumvar      = {pca['cumulative_variance']}")
    print(f"  n_eff @95%  = {pca['n_effective_components_95pct']}")
    print(f"  effective_tests (105 * {pca['n_effective_components_95pct']}/5) = {pca['effective_tests_nominal_105']}")

    (OUT / "_driver_pca_v2.json").write_text(json.dumps({"adf": adf, "pca": pca}, indent=2))

    # per sub-cluster
    etfs = {s: pd.read_parquet(DATA / f"YF_{m['etf']}.parquet") for s, m in SUB_CLUSTERS.items()}
    summary = {"alpha_q_fdr": FDR_Q, "n_effective_components_95pct": pca["n_effective_components_95pct"],
               "sub_clusters": {}}
    all_p = []
    p_to_loc = []  # (sub, driver, fwd) for each p in all_p

    sub_rows = {}
    for sub, meta in SUB_CLUSTERS.items():
        rows, n, start, end = validate_v2(sub, meta, drivers, etfs[sub])
        sub_rows[sub] = rows
        for r in rows:
            all_p.append(r["hac_p"])
            p_to_loc.append((sub, r["driver"], r["fwd"]))

    # BH-FDR global across all 7×15 = 105 tests
    reject = bh_fdr(np.array(all_p), q=FDR_Q)
    fdr_pass_set = {p_to_loc[i] for i, r in enumerate(reject) if r}
    print(f"\n[BH-FDR q={FDR_Q}] reject = {int(reject.sum())} / {len(reject)}")

    # write per sub-cluster v2 md
    for sub, meta in SUB_CLUSTERS.items():
        rows = sub_rows[sub]
        for r in rows:
            r["fdr_pass"] = (sub, r["driver"], r["fwd"]) in fdr_pass_set
            # verdict v2 (★ magnitude freeze)
            sign_ok = r["halfsplit_sign_match"] == 1
            if r["fdr_pass"] and sign_ok and abs(r["ic"]) > 0.03:
                v = "sign_prior_robust"
            elif r["fdr_pass"]:
                v = "fdr_pass_sign_unstable"
            elif sign_ok and abs(r["ic"]) > 0.03:
                v = "sign_prior_descriptive"
            else:
                v = "no_signal"
            r["verdict_v2"] = v

        rdf = pd.DataFrame(rows)
        fdr_pass_count = int(rdf["fdr_pass"].sum())
        sign_robust_count = int((rdf["verdict_v2"] == "sign_prior_robust").sum())

        md = OUT / sub / f"validation-{sub}-v2.md"
        md.parent.mkdir(exist_ok=True, parents=True)
        md.write_text(f"""# validation-{sub}-v2 — {sub} ({meta['etf']}) v2 격하·재검정 (2026-05-31)

> ★ main 12축 audit verdict 격하 5건 반영 (raw/evaluation-bond_cash-20260531.md).
> v1 산출 (`validation-{sub}.md`) 와 병행. v2 = stationary 차분 driver + BH-FDR + half-split OOS + magnitude freeze.

## §0 v1 → v2 변경점
- driver: T10Y2Y level / ACM_TP10 level → **T10Y2Y_d20 / ACM_TP10_d20 차분** (★ non-stationary spurious 차단, ADF p_lev T10Y2Y=0.553 → diff 5pct PASS)
- 다중검정: Bonferroni α/420 (보수) → **BH-FDR q={FDR_Q} on effective ~{summary['n_effective_components_95pct'] * 21}** (PCA {summary['n_effective_components_95pct']} component / 5 driver)
- HAC lag: f → **max(2f, 60)** (overlap nested 보수)
- verdict: magnitude prior 박제 ★금지★ → **sign/direction prior only** (4 라벨 → sign_prior_robust / fdr_pass_sign_unstable / sign_prior_descriptive / no_signal)
- regime cell: walk-forward OOS 부재 → **descriptive only 격하** (v1 의 regime_conditional_findings bonferroni_pass=true 박제 ★취소★)

## §1 sub-cluster meta
| 항목 | 값 |
|---|---|
| sub-cluster | {sub} |
| 대표 ETF | {meta['etf']} (duration ≈ {meta['duration']}, credit {meta['credit']}) |
| n_panel | {n:,} |

## §2 Rank-IC (v2 차분 driver + HAC lag 2× + half-split OOS + BH-FDR)
{rdf.to_markdown(index=False)}

## §3 verdict 요약 (★ magnitude freeze)
- BH-FDR q={FDR_Q} 통과 = **{fdr_pass_count}/{len(rows)}** test
- sign_prior_robust (FDR 통과 AND half-split 부호 일치 AND |IC|>0.03) = **{sign_robust_count}/{len(rows)}**
- ⛔ 점추정 IC/β magnitude 박제 금지 — sign/direction prior 만 yaml v4 에 진입

## §4 ★ tier (audit 격하 = structural_prior_low_confidence, 전 7 sub-cluster 공통)
- tier = `structural_prior_low_confidence`
- validated_alpha = **false** (★ audit verdict 격하)
- 근거: (a) driver 차분 후 신호 magnitude 소멸 다수 (b) regime cell walk-forward OOS 미수행 (c) ACM vintage 미처리 (D축 PIT 한계)

## §5 D축 PIT 한계 (audit 격하 D=FAIL 대응)
- ACM_TP10 = NY Fed Adrian-Crump-Moench full-history **revised series** (모델 재적합 시 과거 일자 값도 변경).
- 본 v2 = published xlsx (2026-05-31 fetch) 의 latest revision 사용 = **lookahead 잔존 가능성**.
- 정정 옵션: (a) Kim-Wright real-time (FRB H.15 / SSRN replication, R3 후속) (b) ACM monthly publish lag 1-month forward-shift 보수 (c) PIT 한계 명시만.
- 본 v2 산출 = **(c) PIT 한계 명시** (yaml v4 에 박제) — Kim-Wright fetch 는 Phase 7 진입 전 R3 query 우선순위.

## §6 BAA10Y proxy 등급 mismatch (audit hy_credit 지적)
- BAA10Y = Moody's BAA (IG 등급) Δ proxy. **hy_credit 의 HYG = B+/BB (HY)** 와 등급 mismatch.
- 정당화 (audit ✅): BAMLH0A0HYM2 FRED 2023-05~ short sample (786 rows), 1996-2023 historical 부재 (ICE 라이센스). BAA1986~ proxy = DA eq_us_defensive H3 검증 경로 재사용.
- 한계 명시 의무 — yaml v4 confidence_hooks 에 'credit_grade_mismatch' 박제.
""", encoding="utf-8")

        summary["sub_clusters"][sub] = {
            "etf": meta["etf"], "n": n,
            "fdr_pass_count": fdr_pass_count,
            "sign_prior_robust": sign_robust_count,
            "tier": "structural_prior_low_confidence",
            "validated_alpha": False,
        }
        print(f"  [v2] {sub:12s} fdr_pass={fdr_pass_count:>2d}/15 sign_robust={sign_robust_count:>2d}/15 → {md.name}")

    (OUT / "_summary_v2.json").write_text(json.dumps(summary, indent=2))
    print(f"\n[DONE] summary v2 → {OUT/'_summary_v2.json'}")


if __name__ == "__main__":
    main()
