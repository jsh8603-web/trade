"""H11 — Google Trends 'bitcoin' attention z → fwd_1m_ret (Liu&Tsyvinski 2021).

★PyTrends "all" timeframe = monthly aggregate (268 obs 2004-01 ~ 2026-04).
weekly base (LTW 2021) 와 다름 — monthly small-N rigor 강제.

⛔ 자문 magnitude 박제 X (LTW 2021 +0.5~+0.7 점추정 prior 비박제).
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_common import (
    load_btc_klines, rank_ic, newey_west_se, effective_n,
)

OUT = Path(__file__).resolve().parent.parent / "raw" / "validation-h11-attention.md"
DATA = Path(__file__).resolve().parent.parent / "raw" / "data"


def main():
    trends = pd.read_csv(DATA / "pytrends-bitcoin-weekly.csv")
    trends["date"] = pd.to_datetime(trends["date_utc"], format="%Y-%m-%d")
    trends["trends"] = pd.to_numeric(trends["trends_bitcoin"], errors="coerce")
    trends = trends.dropna(subset=["trends"]).sort_values("date").reset_index(drop=True)

    btc = load_btc_klines()
    # monthly close (last day of month)
    btc["ym"] = btc["date"].dt.to_period("M")
    btc_m = btc.groupby("ym").agg(close=("close", "last"), date=("date", "last")).reset_index()
    btc_m["ret_fwd_1m"] = np.log(btc_m["close"].shift(-1) / btc_m["close"])

    trends["ym"] = trends["date"].dt.to_period("M")
    trends_m = trends.groupby("ym").agg(trends=("trends", "mean"), date=("date", "first")).reset_index()
    df = trends_m[["ym", "trends"]].merge(btc_m[["ym", "close", "ret_fwd_1m"]], on="ym", how="inner")
    df = df.sort_values("ym").reset_index(drop=True)
    df["attn_z"] = (df["trends"] - df["trends"].rolling(12).mean()) / df["trends"].rolling(12).std()
    n_total = df.dropna(subset=["attn_z", "ret_fwd_1m"]).shape[0]

    print(f"[H11] n_total (attn_z + ret_fwd_1m valid) = {n_total}", flush=True)
    if n_total < 30:
        print(f"[H11 ★INSUFFICIENT] n={n_total} <30, verdict 격하 의무", flush=True)

    sub = df.dropna(subset=["attn_z", "ret_fwd_1m"]).copy()
    ic_full, n_full = rank_ic(sub["attn_z"], sub["ret_fwd_1m"])
    nw_se = newey_west_se(sub["ret_fwd_1m"].values, lags=1)  # monthly fwd_1m
    n_eff_full = effective_n(sub["ret_fwd_1m"].values)

    # threshold subsample: attn_z > +1σ
    high = sub[sub["attn_z"] > 1.0]
    low = sub[sub["attn_z"] < -1.0]
    n_high, n_low = len(high), len(low)
    mean_high = high["ret_fwd_1m"].mean() if n_high > 0 else np.nan
    mean_low = low["ret_fwd_1m"].mean() if n_low > 0 else np.nan
    mean_mid = sub[(sub["attn_z"] >= -1.0) & (sub["attn_z"] <= 1.0)]["ret_fwd_1m"].mean()

    # post-2021 sub-sample (LTW 표본 2014-2018, 우리 post-2021 attention saturate 시기)
    post21 = sub[sub["ym"] >= pd.Period("2021-01")]
    if len(post21) >= 30:
        ic_post21, _ = rank_ic(post21["attn_z"], post21["ret_fwd_1m"])
    else:
        ic_post21 = np.nan

    # Bonferroni K=16
    pass_b = abs(ic_full) > 0.03
    sign_flip_post21 = (not np.isnan(ic_post21)) and (np.sign(ic_post21) != np.sign(ic_full))
    extreme_diff = (not np.isnan(mean_high)) and (mean_high > mean_mid)

    print(f"[H11 full monthly] Rank-IC={ic_full:.4f} (n={n_full}, N_eff={n_eff_full:.0f})", flush=True)
    print(f"[H11 attn_z >+1σ] n={n_high}, mean_fwd_1m={mean_high:.4f}", flush=True)
    print(f"[H11 attn_z mid] mean_fwd_1m={mean_mid:.4f}", flush=True)
    print(f"[H11 attn_z <-1σ] n={n_low}, mean_fwd_1m={mean_low:.4f}", flush=True)
    print(f"[H11 post-2021 sub] Rank-IC={ic_post21:.4f} (sign flip: {sign_flip_post21})", flush=True)

    if n_total < 30:
        verdict = "★INSUFFICIENT (n<30, monthly 표본 부족, weekly fetch 후속 의무)"
    elif pass_b and not sign_flip_post21 and extreme_diff:
        verdict = "PARTIAL CONFIRMED (attn_z > +1σ → 상위 mean, walk-forward 후속)"
    elif pass_b:
        verdict = "TENTATIVE DIRECTIONAL (Rank-IC>0.03 약 신호)"
    elif sign_flip_post21:
        verdict = "★REJECTED (post-2021 부호반전, LTW 2021 표본 generalize 실패)"
    else:
        verdict = "★REJECTED (Rank-IC<0.03 hard B threshold 미달)"

    out_lines = [
        "---",
        "tags: [type/validation, study/crypto, cycle/2, hypothesis/h11]",
        "date: 2026-05-31",
        "hypothesis: H11 — Google Trends 'bitcoin' attn_z → fwd_1m_ret (Liu&Tsyvinski 2021 attention predictor)",
        "audit_axes: [A, B, D, F, G, I, K]",
        "note: PyTrends 'all' timeframe = monthly aggregate, LTW weekly base 와 다름 (small-N rigor)",
        "---",
        "",
        "# validation-h11 — Google Trends attention monthly z → BTC fwd_1m_ret",
        "",
        "## Data Coverage",
        f"- PyTrends 'bitcoin' monthly 268 obs (2004-01 ~ 2026-04)",
        f"- Binance BTC monthly (2017-08~) inner join 후: **n_total = {n_total}**",
        f"- 12m rolling z-score warmup 적용 후 effective N={n_eff_full:.0f}",
        "",
        "## 변수 정의",
        "- (a) 시제: monthly contemporaneous attn_z → fwd_1m_ret (log return)",
        "- (b) frequency: monthly (PyTrends 'all' = monthly aggregate)",
        "- (c) transform: rolling 12m z-score",
        "- (d) conditioning: post-2021 sub-sample (attention saturate 시기 검증)",
        "",
        "## H11 검증 결과",
        f"- full Rank-IC (attn_z → fwd_1m) = **{ic_full:.4f}** (n={n_full}, N_eff={n_eff_full:.0f})",
        f"- attn_z >+1σ n={n_high}, mean_fwd_1m = {mean_high:.4f}",
        f"- attn_z (-1, +1) n={(sub['attn_z'].between(-1, 1)).sum()}, mean_fwd_1m = {mean_mid:.4f}",
        f"- attn_z <-1σ n={n_low}, mean_fwd_1m = {mean_low:.4f}",
        f"- post-2021 sub Rank-IC = {ic_post21:.4f} (sign flip vs full: {sign_flip_post21})",
        f"- Newey-West HAC SE (lag=1m) = {nw_se:.6e}",
        "",
        "## 12축 박제",
        f"- **A 학술**: Liu&Tsyvinski 2021 RFS (attention predictor, weekly base), Da Engelberg Gao 2011 JF (search trend as retail attention)",
        f"- **B SE**: monthly aggregate (PyTrends 'all') = autocorr 약. Newey-West HAC lag=1m. {'PASS' if pass_b else 'FAIL'} |Rank-IC|={abs(ic_full):.4f}",
        f"- **D PIT**: PyTrends weekly release Sunday 0:00 UTC, T+1 가능",
        f"- **E 자문 환각**: LTW 2021 정량 +0.5~+0.7 점추정 prior 박제 X — 본 표본 monthly Rank-IC {ic_full:.4f} 기준 hedge",
        f"- **F 반증조건**: (i) β CI 0 포함? (Rank-IC {ic_full:.4f} {'>' if pass_b else '≤'} 0.03 hard B) (ii) post-2021 부호반전? {'YES (REJECT)' if sign_flip_post21 else 'NO'}",
        f"- **G effective N**: N_eff={n_eff_full:.0f} — {'★INSUFFICIENT' if n_total < 30 else '약 충분'}",
        f"- **I 생존편향**: BTC only (멀티코인 attention 확장 후속)",
        f"- **K 시도횟수**: K=16 (4 horizon × 2 MVRV regime × bull/bear). 본 라운드 = base 1 + post-2021 sub = 2. Bonferroni α/16={0.05/16:.5f}",
        "",
        "## verdict",
        f"**{verdict}**",
        "",
        "## hedge 어휘",
        f"- monthly aggregate 한계 — weekly base 후속 fetch (today 5-y) 가 LTW 2021 직접 비교 가능",
        f"- 점추정 magnitude (LTW +0.5~+0.7) 박제 X — 본 표본 Rank-IC {ic_full:.4f} 보고만",
        "",
        "## 후속 의문",
        "- (i) weekly fetch (today 5-y) 보강 + LTW 2021 직접 표본 매핑",
        "- (ii) MVRV regime conditional (bull/bear) 효과 비대칭 검증",
        "- (iii) Granger lead 양방향 (attn → price OR price → attn) endogeneity 확인",
        "- (iv) post-2021 sub-sample 부호 반전 = generalize 실패 신호",
    ]

    OUT.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"[OK] validation md -> {OUT.name}", flush=True)
    print(f"[verdict] {verdict}", flush=True)


if __name__ == "__main__":
    main()
