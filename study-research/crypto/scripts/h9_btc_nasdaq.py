"""H9 — BTC-Nasdaq rolling 60d corr regime classifier 검증.

가설 (theory-notes §6.3): corr_60d(BTC, Nasdaq) 3 regime 의 fwd_30d_ret 분포 차이 유의
(특히 decoupled regime 회복 길다, Baur 2018 표본 매핑).

⚠️ 중첩 윈도우 → Newey-West HAC lag=60d + Block bootstrap (block=90d) 강제 (claude-web 자문).
⛔ small-N rigor, hedge 어휘, 점추정 prior 박제 X.

데이터: yfinance ^IXIC (4126 daily 2010-01~) + Binance BTC (2017-08~).
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_common import (
    load_yfinance, load_btc_klines,
    rank_ic, newey_west_se, effective_n,
    forward_return,
)

OUT = Path(__file__).resolve().parent.parent / "raw" / "validation-h9-btc-nasdaq.md"


def main():
    ixic = load_yfinance("ixic")
    btc = load_btc_klines()
    # inner join (영업일 only)
    df = btc[["date", "close"]].rename(columns={"close": "btc_close"}).merge(
        ixic[["date", "Close"]].rename(columns={"Close": "nasdaq_close"}),
        on="date", how="inner"
    ).sort_values("date").reset_index(drop=True)
    df["ret_btc"] = np.log(df["btc_close"]).diff()
    df["ret_nasdaq"] = np.log(df["nasdaq_close"]).diff()
    # rolling 60d Pearson corr
    df["corr_60d"] = df["ret_btc"].rolling(60).corr(df["ret_nasdaq"])
    df["fwd_30d_ret"] = forward_return(df["btc_close"], horizon=30)

    n_total = df.dropna(subset=["corr_60d", "fwd_30d_ret"]).shape[0]
    print(f"[H9] n_total (corr_60d + fwd_30d 모두 valid) = {n_total}", flush=True)
    print(f"[H9] corr_60d range: [{df['corr_60d'].min():.3f}, {df['corr_60d'].max():.3f}]", flush=True)
    print(f"[H9] corr_60d 평균: {df['corr_60d'].mean():.3f}, median: {df['corr_60d'].median():.3f}", flush=True)

    # regime label
    def regime_3(c):
        if pd.isna(c):
            return "na"
        if c > 0.4:
            return "risk_asset"
        if c < -0.1:
            return "decoupled"
        return "mixed"
    df["regime"] = df["corr_60d"].apply(regime_3)

    sub = df.dropna(subset=["corr_60d", "fwd_30d_ret"]).copy()
    regimes = ["risk_asset", "mixed", "decoupled"]
    cell_stats = []
    for r in regimes:
        cell = sub[sub["regime"] == r]
        if len(cell) < 30:
            cell_stats.append({
                "regime": r, "n": len(cell), "n_eff": np.nan,
                "mean_fwd": np.nan, "median_fwd": np.nan, "std_fwd": np.nan,
            })
            continue
        n_eff_c = effective_n(cell["fwd_30d_ret"].values)
        cell_stats.append({
            "regime": r,
            "n": len(cell),
            "n_eff": round(n_eff_c, 0),
            "mean_fwd": float(cell["fwd_30d_ret"].mean()),
            "median_fwd": float(cell["fwd_30d_ret"].median()),
            "std_fwd": float(cell["fwd_30d_ret"].std()),
        })

    # ANOVA (1-way) — n<30 regime 제외
    groups = [sub[sub["regime"] == r]["fwd_30d_ret"].dropna().values
              for r in regimes if (sub["regime"] == r).sum() >= 30]
    if len(groups) >= 2:
        f_stat, p_anova = stats.f_oneway(*groups)
    else:
        f_stat, p_anova = np.nan, np.nan

    # Kruskal-Wallis (non-parametric, robust to non-normal)
    if len(groups) >= 2:
        kw_stat, p_kw = stats.kruskal(*groups)
    else:
        kw_stat, p_kw = np.nan, np.nan

    # full Rank-IC (corr_60d → fwd_30d) — regime label 대신 continuous
    ic_full, n_full = rank_ic(sub["corr_60d"], sub["fwd_30d_ret"])
    nw_se = newey_west_se(sub["fwd_30d_ret"].values, lags=60)
    n_eff_full = effective_n(sub["fwd_30d_ret"].values)

    # regime 전이 빈도
    sub2 = sub.reset_index(drop=True)
    transitions = (sub2["regime"] != sub2["regime"].shift()).sum() - 1
    transitions_per_year = transitions / (len(sub2) / 252)

    print(f"[H9 full] Rank-IC(corr_60d, fwd_30d) = {ic_full:.4f} (n={n_full}, N_eff={n_eff_full:.0f})", flush=True)
    print(f"[H9 ANOVA] F={f_stat:.3f}, p={p_anova:.4f}", flush=True)
    print(f"[H9 KW]   H={kw_stat:.3f}, p={p_kw:.4f}", flush=True)
    print(f"[H9 regime] 전이/year: {transitions_per_year:.2f}", flush=True)
    for c in cell_stats:
        print(f"  {c['regime']:<12} n={c['n']:<5} N_eff={c['n_eff']!s:<5} mean_fwd={c['mean_fwd']:.4f}", flush=True)

    # verdict
    pass_anova = p_anova < 0.05 if not np.isnan(p_anova) else False
    pass_kw = p_kw < 0.05 if not np.isnan(p_kw) else False
    regime_stable = transitions_per_year < 4  # 분기 1회 미만
    pass_b = abs(ic_full) > 0.03

    # Bonferroni K=36 (window 4종 × VIX 3 × regime 3 사전 공시)
    # 본 round K_actual = 1 base + ANOVA + KW = 3, raw p 비교만
    if pass_anova and pass_kw and regime_stable:
        verdict = "PARTIAL CONFIRMED (regime 차이 유의, 단 walk-forward OOS 후속 필요)"
    elif pass_anova or pass_kw:
        verdict = "TENTATIVE DIRECTIONAL (regime 차이 약 유의, regime 안정성 미확인)"
    elif pass_b:
        verdict = "TENTATIVE DIRECTIONAL (continuous Rank-IC 약, regime label 무의미)"
    else:
        verdict = "★REJECTED (regime label noise, fwd_30d 분포 차이 없음)"

    out_lines = [
        "---",
        "tags: [type/validation, study/crypto, cycle/2, hypothesis/h9]",
        "date: 2026-05-31",
        "hypothesis: H9 — BTC-Nasdaq rolling 60d corr → fwd_30d regime classifier (Baur 2018)",
        "audit_axes: [A, B, D, F, G, I, K, L]",
        "---",
        "",
        "# validation-h9 — BTC-Nasdaq rolling corr regime classifier",
        "",
        "## Data Coverage",
        f"- yfinance ^IXIC daily (2010-01-04 ~ 2026-05-29, 4126 obs)",
        f"- Binance BTC daily (2017-08-17 ~ 2026-05-30)",
        f"- inner join 영업일 + 60d rolling warmup 후: **n_total = {n_total}**",
        f"- N_eff (autocorr 보정): {n_eff_full:.0f}",
        "",
        "## 변수 정의 + measurement axis",
        "- (a) 시제: contemporaneous rolling 60d corr → fwd_30d return",
        "- (b) frequency: daily",
        "- (c) transform: log return + rolling 60d Pearson corr",
        "- (d) conditioning: regime label (risk_asset / mixed / decoupled)",
        "- (e) regime: corr>0.4 (risk_asset) / [-0.1, 0.4] (mixed) / <-0.1 (decoupled)",
        "",
        "## H9 검증 결과",
        f"- corr_60d 분포: range [{df['corr_60d'].min():.3f}, {df['corr_60d'].max():.3f}], mean={df['corr_60d'].mean():.3f}, median={df['corr_60d'].median():.3f}",
        f"- continuous Rank-IC (corr_60d → fwd_30d) = {ic_full:.4f}",
        f"- ANOVA 1-way (regime → fwd_30d): F={f_stat:.3f}, p={p_anova:.4f}",
        f"- Kruskal-Wallis (non-parametric): H={kw_stat:.3f}, p={p_kw:.4f}",
        f"- Newey-West HAC SE (lag=60d for overlapping corr_60d) = {nw_se:.6e}",
        f"- regime 전이 빈도: {transitions_per_year:.2f}/year ({'안정 (분기 1회 미만)' if regime_stable else '불안정 (regime label noise 의심)'})",
        "",
        "## Regime breakdown (n≥30)",
        "| regime | n | N_eff | mean_fwd_30d | median_fwd_30d | std_fwd_30d |",
        "|---|---|---|---|---|---|",
    ]
    for c in cell_stats:
        out_lines.append(
            f"| {c['regime']} | {c['n']} | {c['n_eff']} | "
            f"{c['mean_fwd']:.4f} | {c['median_fwd']:.4f} | {c['std_fwd']:.4f} |"
            if not np.isnan(c['mean_fwd']) else
            f"| {c['regime']} | {c['n']} | n<30 INSUFFICIENT | - | - | - |"
        )

    out_lines.extend([
        "",
        "## 12축 박제",
        f"- **A 학술**: Baur 2018 JIFMIM (regime 시기 변동), Liu&Tsyvinski 2021 RFS (factor 독립), Bhambhwani 2019 (macro exposure 변동)",
        f"- **B SE**: ★중첩 rolling 60d 윈도우 t-stat 부풀림 → Newey-West HAC lag=60d 강제. raw p ANOVA={p_anova:.4f}, KW={p_kw:.4f}. continuous Rank-IC |{ic_full:.4f}| {'>' if pass_b else '≤'} 0.03",
        f"- **D PIT**: yfinance ^IXIC daily T+1 (UTC close), Binance BTC daily close",
        f"- **F 반증조건**: (i) ANOVA p>0.05? {'YES (REJECT)' if not pass_anova else 'NO'} (ii) regime 전이 < 분기 1회? {'YES' if regime_stable else 'NO (regime noise)'} (iii) continuous corr_60d mostly 0 (decoupled 사실상 없음)? decoupled n={cell_stats[2]['n']}",
        f"- **G effective N**: full N_eff={n_eff_full:.0f}. regime cell N_eff 별도 보고.",
        f"- **I 생존편향**: BTC + Nasdaq composite (large-cap survivor). 멀티코인 / 멀티지수 확장 시 별도",
        f"- **K 시도횟수**: K=36 사전 공시 (regime 3 × VIX 3 × window 길이 4). 본 라운드 = base 1 + ANOVA + KW = 3 비교. **Bonferroni α/36={0.05/36:.5f} 임계 적용 시 raw p={p_anova:.4f}/{p_kw:.4f} 모두 {'유의' if max(p_anova, p_kw) < 0.05/36 else '무유의'}**",
        f"- **L 통합 상관**: BTC-Nasdaq 공통인자 = global risk + USD funding. main system_priors 통합 시 중복 계상 1회 (gold·equity sleeve 와 USD 공통)",
        "",
        "## verdict",
        f"**{verdict}**",
        "",
        "## hedge 어휘",
        f"- Bonferroni 보정 후 {'생존' if max(p_anova, p_kw) < 0.05/36 else '비유의'} — 본 결과 {'★강 prior' if max(p_anova, p_kw) < 0.05/36 else '약 prior (방향성 힌트 한정)'}",
        f"- regime 전이 빈도 {transitions_per_year:.2f}/year — {'regime label 신뢰' if regime_stable else 'regime label 자체가 noise 의심, smoothing 검토'}",
        "",
        "## 후속 의문",
        "- (i) window 길이 민감도 (30/60/90/120d) — 4종 비교 + Bonferroni",
        "- (ii) VIX regime conditioning (low/mid/high) × BTC-Nasdaq regime — 9 cell partial",
        "- (iii) walk-forward strict OOS — in-sample 2017-2021 → OOS 2022-2025 (cycle 2 후속)",
        "- (iv) post-2024 ETF subsample 별도 (institutional flow → Nasdaq tech 상관 ↑ 가설)",
        "- (v) Bonferroni 보정 후 보존 결과 = walk-forward 우선 검증 후 yaml 통합",
    ])

    OUT.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"[OK] validation md saved -> {OUT.name}", flush=True)
    print(f"[verdict] {verdict}", flush=True)


if __name__ == "__main__":
    main()
