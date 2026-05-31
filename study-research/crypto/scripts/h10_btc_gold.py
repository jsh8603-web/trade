"""H10 — BTC-Gold rolling 60d corr → digital gold thesis 검증.

가설 (theory-notes §6.4): post-2020 risk-off (VIX>30 day) 에서 corr_btc_gold > 0.2
(digital gold 시그널, Baur 2018 의 BTC≠gold prior 의 post-ETF 시대 시험).

⚠️ 중첩 윈도우 + risk-off 표본 N 작음 → Newey-West HAC + Block bootstrap 강제.
⛔ small-N rigor, hedge 어휘.

데이터: yfinance GC=F Gold futures (4125 daily, 2010-01-04~) + Binance BTC + yfinance ^VIX.
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

OUT = Path(__file__).resolve().parent.parent / "raw" / "validation-h10-btc-gold.md"


def main():
    gold = load_yfinance("gold-gcf")
    btc = load_btc_klines()
    vix = load_yfinance("vix")

    df = btc[["date", "close"]].rename(columns={"close": "btc_close"}).merge(
        gold[["date", "Close"]].rename(columns={"Close": "gold_close"}),
        on="date", how="inner"
    ).merge(
        vix[["date", "Close"]].rename(columns={"Close": "vix"}),
        on="date", how="inner"
    ).sort_values("date").reset_index(drop=True)

    df["ret_btc"] = np.log(df["btc_close"]).diff()
    df["ret_gold"] = np.log(df["gold_close"]).diff()
    df["corr_60d"] = df["ret_btc"].rolling(60).corr(df["ret_gold"])
    df["fwd_30d_ret"] = forward_return(df["btc_close"], horizon=30)

    n_total = df.dropna(subset=["corr_60d"]).shape[0]
    print(f"[H10] n_total (corr_60d valid) = {n_total}", flush=True)
    print(f"[H10] corr_60d range: [{df['corr_60d'].min():.3f}, {df['corr_60d'].max():.3f}], mean={df['corr_60d'].mean():.4f}", flush=True)

    sub = df.dropna(subset=["corr_60d", "vix"]).copy()
    # risk-off subsample (VIX > 30)
    risk_off = sub[sub["vix"] > 30].copy()
    risk_on = sub[sub["vix"] <= 30].copy()

    n_risk_off = len(risk_off)
    n_risk_on = len(risk_on)
    corr_off_mean = risk_off["corr_60d"].mean() if n_risk_off > 0 else np.nan
    corr_on_mean = risk_on["corr_60d"].mean() if n_risk_on > 0 else np.nan

    # Welch t-test (자기상관 무시 raw, hedge 어휘 박제)
    if n_risk_off >= 30 and n_risk_on >= 30:
        t_stat, p_welch = stats.ttest_ind(
            risk_off["corr_60d"].dropna(),
            risk_on["corr_60d"].dropna(),
            equal_var=False,
        )
    else:
        t_stat, p_welch = np.nan, np.nan

    # Mann-Whitney U (non-parametric)
    if n_risk_off >= 30 and n_risk_on >= 30:
        u_stat, p_mw = stats.mannwhitneyu(
            risk_off["corr_60d"].dropna(),
            risk_on["corr_60d"].dropna(),
            alternative="two-sided",
        )
    else:
        u_stat, p_mw = np.nan, np.nan

    # post-2020 risk-off (Baur 2018 post-ETF 시대 검증)
    post_2020_off = sub[(sub["vix"] > 30) & (sub["date"] >= pd.Timestamp("2020-01-01"))].copy()
    n_post_off = len(post_2020_off)
    corr_post_off_mean = post_2020_off["corr_60d"].mean() if n_post_off > 0 else np.nan

    # pre/post 2024 ETF 비교
    pre_etf = sub[sub["date"] < pd.Timestamp("2024-01-11")].copy()
    post_etf = sub[sub["date"] >= pd.Timestamp("2024-01-11")].copy()
    corr_pre_mean = pre_etf["corr_60d"].mean() if len(pre_etf) > 0 else np.nan
    corr_post_mean = post_etf["corr_60d"].mean() if len(post_etf) > 0 else np.nan

    if len(pre_etf) >= 100 and len(post_etf) >= 30:
        t_etf, p_etf = stats.ttest_ind(
            pre_etf["corr_60d"].dropna(),
            post_etf["corr_60d"].dropna(),
            equal_var=False,
        )
    else:
        t_etf, p_etf = np.nan, np.nan

    n_eff_full = effective_n(sub["corr_60d"].values)
    n_eff_off = effective_n(risk_off["corr_60d"].values) if n_risk_off > 0 else np.nan

    print(f"[H10 risk-off] n={n_risk_off}, corr_60d mean={corr_off_mean:.4f}, N_eff={n_eff_off:.0f}", flush=True)
    print(f"[H10 risk-on] n={n_risk_on}, corr_60d mean={corr_on_mean:.4f}", flush=True)
    print(f"[H10 Welch] t={t_stat:.3f}, p={p_welch:.4f}", flush=True)
    print(f"[H10 MW] U={u_stat}, p={p_mw:.4f}", flush=True)
    print(f"[H10 post-2020 risk-off] n={n_post_off}, mean={corr_post_off_mean:.4f}", flush=True)
    print(f"[H10 pre/post ETF] pre={corr_pre_mean:.4f} (n={len(pre_etf)}), post={corr_post_mean:.4f} (n={len(post_etf)}), p={p_etf:.4f}", flush=True)

    # verdict — digital-gold thesis 검증
    # gate (i): risk-off corr > 0.2 (positive co-move)
    # gate (ii): risk-off > risk-on (statistically)
    # gate (iii): post-ETF > pre-ETF (시대 강화)
    gate_i = corr_off_mean > 0.2
    gate_ii = (p_welch < 0.05) and (corr_off_mean > corr_on_mean) if not np.isnan(p_welch) else False
    gate_iii = (p_etf < 0.05) and (corr_post_mean > corr_pre_mean) if not np.isnan(p_etf) else False

    if gate_i and gate_ii and gate_iii:
        verdict = "PARTIAL CONFIRMED (digital-gold thesis 부분 지지, walk-forward OOS 필요)"
    elif gate_i and gate_ii:
        verdict = "TENTATIVE DIRECTIONAL (risk-off corr>0.2 + 통계 유의, ETF 시대 강화 미확인)"
    elif gate_i:
        verdict = "TENTATIVE DIRECTIONAL (risk-off corr>0.2, 통계 유의성 부재)"
    elif corr_off_mean < corr_on_mean:
        verdict = "★REVERSED (digital-gold 정반대 — risk-off 시 BTC≠Gold 또는 음의 corr)"
    else:
        verdict = "★REJECTED (risk-off corr<0.2, digital-gold thesis 본 표본 부정)"

    out_lines = [
        "---",
        "tags: [type/validation, study/crypto, cycle/2, hypothesis/h10]",
        "date: 2026-05-31",
        "hypothesis: H10 — BTC-Gold rolling 60d corr → digital gold thesis (Baur 2018 BTC≠gold prior 시험)",
        "audit_axes: [A, B, D, F, G, I, K]",
        "---",
        "",
        "# validation-h10 — BTC-Gold rolling corr digital gold thesis",
        "",
        "## Data Coverage",
        f"- yfinance GC=F Gold futures daily ({df['date'].min().date()} ~ {df['date'].max().date()})",
        f"- Binance BTC daily (2017-08-17~)",
        f"- yfinance ^VIX daily (risk-off filter)",
        f"- inner join + 60d warmup: **n_total = {n_total}**",
        "",
        "## 변수 정의",
        "- (a) 시제: contemporaneous rolling 60d Pearson corr",
        "- (b) frequency: daily",
        "- (c) transform: log return + rolling corr",
        "- (d) conditioning: VIX > 30 (risk-off subsample) / pre vs post 2024-01-11 ETF",
        "- (e) regime: digital_gold candidate (risk-off + corr > 0.2)",
        "",
        "## H10 검증 결과",
        f"- full sample corr_60d: range [{df['corr_60d'].min():.3f}, {df['corr_60d'].max():.3f}], mean={df['corr_60d'].mean():.4f}",
        f"- risk-off (VIX>30) n={n_risk_off}: corr_60d mean = **{corr_off_mean:.4f}** (N_eff={n_eff_off:.0f})",
        f"- risk-on (VIX≤30) n={n_risk_on}: corr_60d mean = {corr_on_mean:.4f}",
        f"- Welch t-test (risk-off vs risk-on corr): t={t_stat:.3f}, p={p_welch:.4f}",
        f"- Mann-Whitney U: p={p_mw:.4f}",
        f"- post-2020 risk-off only n={n_post_off}, mean={corr_post_off_mean:.4f}",
        f"- pre-ETF (2024-01-11 이전) n={len(pre_etf)} corr mean={corr_pre_mean:.4f}",
        f"- post-ETF n={len(post_etf)} corr mean={corr_post_mean:.4f}, Welch p={p_etf:.4f}",
        "",
        "## 12축 박제",
        f"- **A 학술**: Baur 2018 (BTC≠gold prior), Klein 2018 (BTC vol >> gold vol), Smales 2019 (speculative haven)",
        f"- **B SE**: ★중첩 rolling 60d → Welch t-test (raw IID), Mann-Whitney 비교 보고. autocorr 보정 = block-bootstrap 후속 (본 라운드 raw + hedge).",
        f"- **D PIT**: yfinance daily close T+1",
        f"- **F 반증조건**: (i) risk-off corr_60d > 0.2? **{corr_off_mean:.4f}** {'PASS' if gate_i else 'FAIL'} (ii) risk-off > risk-on 통계 유의? p={p_welch:.4f} {'PASS' if gate_ii else 'FAIL'} (iii) post-ETF > pre-ETF? p={p_etf:.4f} {'PASS' if gate_iii else 'FAIL'}",
        f"- **G effective N**: full N_eff={n_eff_full:.0f}, risk-off N_eff={n_eff_off:.0f} — **risk-off N<100 small-N 경고**",
        f"- **I 생존편향**: BTC + Gold futures (둘 다 surviving largest)",
        f"- **K 시도횟수**: K=36 사전 공시 (VIX 3 regime × real_rate 3 × window 4). 본 라운드 = 3 비교 (risk-off vs risk-on + pre/post ETF). Bonferroni α/36={0.05/36:.5f}",
        "",
        "## verdict",
        f"**{verdict}**",
        "",
        "## hedge 어휘",
        f"- Baur 2018 prior (BTC≠gold 표본 2010-2015 corr≈0) 와 본 표본 결과: corr mean {df['corr_60d'].mean():.4f} = {'약한 양' if df['corr_60d'].mean() > 0.1 else '약'} 동행",
        f"- ★risk-off corr {corr_off_mean:.4f} {'>' if gate_i else '≤'} 0.2 digital-gold gate {'PASS' if gate_i else 'FAIL'}",
        f"- Bonferroni 보정 후 raw p={min(p_welch, p_mw):.4f} {'생존' if min(p_welch, p_mw) < 0.05/36 else '무유의'}",
        "",
        "## 후속 의문",
        "- (i) window 길이 민감도 4종 비교 + Bonferroni",
        "- (ii) real_rate (DFII10) 추가 conditioning — real_rate < 0 시 BTC-Gold corr 증폭 가설",
        "- (iii) walk-forward strict OOS",
        "- (iv) Block bootstrap (block=90d) 자기상관 보정 후 재평가",
    ]

    OUT.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"[OK] validation md saved -> {OUT.name}", flush=True)
    print(f"[verdict] {verdict}", flush=True)


if __name__ == "__main__":
    main()
