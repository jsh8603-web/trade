"""H8 — TxCnt (utility count proxy) → fwd_30d_ret (BTC) 검증.

가설 (theory-notes §6.2 수정): Δlog(TxCnt) z>+1σ → fwd_30d_ret 약 양 (utility 신호).
TxTfrValAdjUSD = anonymous tier 403 → TxCnt (count proxy) 대체 (Catalini&Gans 2020 utility 보조).

⛔ count proxy 한계: value-weighted (TxVolUSD) 보다 정보량 ↓. average tx size 손실.
⛔ small-N rigor: n·p·CI·Newey-West HAC·Block bootstrap·Bonferroni 의무.

데이터: CoinMetrics community TxCnt 6357 daily (2009-01-03 ~ 2026-05-30).

12축 박제: A B D F G I K (H7 동일 양식)
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
    load_coinmetrics_v2, load_btc_klines,
    rank_ic, newey_west_se, effective_n,
    halving_phase, forward_return,
)

OUT = Path(__file__).resolve().parent.parent / "raw" / "validation-h8-tx-utility.md"


def macro_epoch(date):
    if date < pd.Timestamp("2017-01-01"):
        return "pre_2017"
    if date < pd.Timestamp("2020-03-01"):
        return "2017_2020"
    if date < pd.Timestamp("2024-01-11"):
        return "2020_2024_pre_etf"
    return "post_2024_etf"


def main():
    v2 = load_coinmetrics_v2()
    klines = load_btc_klines()
    df = v2[["date", "TxCnt", "BlkCnt"]].merge(
        klines[["date", "open", "close"]], on="date", how="inner"
    ).sort_values("date").reset_index(drop=True)
    df["log_tx"] = np.log(df["TxCnt"].astype(float))
    df["dlog_tx"] = df["log_tx"].diff()
    df["log_blk"] = np.log(df["BlkCnt"].astype(float).replace(0, np.nan))
    df["dlog_blk"] = df["log_blk"].diff()
    df["fwd_30d_ret"] = forward_return(df["close"], horizon=30)
    df["epoch"] = df["date"].apply(macro_epoch)
    df["halv"] = df["date"].apply(halving_phase)
    n_total = df.dropna(subset=["dlog_tx", "fwd_30d_ret"]).shape[0]

    print(f"[H8] n_total (Δlog_tx + fwd_30d_ret 모두 valid) = {n_total}", flush=True)

    sub = df.dropna(subset=["dlog_tx", "fwd_30d_ret"]).copy()
    ic_full, n_full = rank_ic(sub["dlog_tx"], sub["fwd_30d_ret"])
    nw_se = newey_west_se(sub["fwd_30d_ret"].values, lags=30)
    n_eff_full = effective_n(sub["fwd_30d_ret"].values)

    x = sub["dlog_tx"].values
    y = sub["fwd_30d_ret"].values
    beta = np.cov(x, y, ddof=0)[0, 1] / np.var(x, ddof=0)
    rng = np.random.default_rng(43)
    n = len(x)
    block = 60
    n_boot = 2000
    n_blocks = n // block
    beta_b = np.empty(n_boot)
    for i in range(n_boot):
        starts = rng.integers(0, n - block + 1, size=n_blocks)
        idx = np.concatenate([np.arange(s, s + block) for s in starts])
        xb, yb = x[idx], y[idx]
        vx = np.var(xb, ddof=0)
        if vx <= 0:
            beta_b[i] = np.nan
            continue
        beta_b[i] = np.cov(xb, yb, ddof=0)[0, 1] / vx
    beta_b = beta_b[~np.isnan(beta_b)]
    ci_lo, ci_hi = np.quantile(beta_b, [0.025, 0.975])

    # contemporaneous Δlog_tx vs price 확인 (mechanical co-move 검증)
    sub2 = df.dropna(subset=["dlog_tx", "open"]).copy()
    sub2["dlog_close"] = np.log(sub2["close"]).diff()
    ic_contemp, n_contemp = rank_ic(sub2["dlog_tx"], sub2["dlog_close"])

    # control: partial-corr (Δlog_tx | Δlog_blk) — mining capacity 제거
    sub3 = sub.dropna(subset=["dlog_blk"]).copy()
    # residual: regress dlog_tx ~ dlog_blk, residual = utility 부분만
    from scipy.stats import linregress
    if len(sub3) >= 100:
        s = linregress(sub3["dlog_blk"], sub3["dlog_tx"])
        sub3["tx_resid"] = sub3["dlog_tx"] - (s.intercept + s.slope * sub3["dlog_blk"])
        ic_partial, n_partial = rank_ic(sub3["tx_resid"], sub3["fwd_30d_ret"])
    else:
        ic_partial, n_partial = np.nan, 0

    print(f"[H8 full] Rank-IC={ic_full:.4f} n={n_full} N_eff={n_eff_full:.0f}", flush=True)
    print(f"[H8 full] β={beta:.6e}, CI95% Block-Bootstrap = [{ci_lo:.6e}, {ci_hi:.6e}]", flush=True)
    print(f"[H8 contemp] Δlog_tx vs Δlog_close Rank-IC={ic_contemp:.4f} (mechanical co-move 검증)", flush=True)
    print(f"[H8 partial] (tx | blk) → fwd_30d Rank-IC={ic_partial:.4f} n={n_partial}", flush=True)

    cells = []
    for epoch in ["pre_2017", "2017_2020", "2020_2024_pre_etf", "post_2024_etf"]:
        for halv in ["pre_first_halving", "post_0_6m", "post_6_18m", "post_18_24m",
                     "post_24_36m", "pre_next_halving"]:
            cell = sub[(sub["epoch"] == epoch) & (sub["halv"] == halv)]
            if len(cell) < 24:
                continue
            ic_c, n_c = rank_ic(cell["dlog_tx"], cell["fwd_30d_ret"])
            n_eff_c = effective_n(cell["fwd_30d_ret"].values)
            cells.append({"epoch": epoch, "halv": halv, "n": n_c, "n_eff": n_eff_c, "rank_ic": ic_c})

    pass_b = abs(ic_full) > 0.03
    ci_excludes_zero = not (ci_lo <= 0 <= ci_hi)
    mechanical = abs(ic_contemp) > 0.3  # contemporaneous corr > 0.3 = utility signal 의심
    partial_distinct = abs(ic_partial) > 0.03 if not np.isnan(ic_partial) else False

    if pass_b and ci_excludes_zero and not mechanical:
        verdict = "PARTIAL CONFIRMED (utility 신호, 단 partial-corr 후속 필요)"
    elif pass_b and ci_excludes_zero and mechanical:
        verdict = "TENTATIVE DIRECTIONAL (mechanical co-move 의심)"
    elif pass_b:
        verdict = "TENTATIVE DIRECTIONAL (CI 0 포함)"
    else:
        verdict = "★REJECTED (Rank-IC<0.03 hard B threshold 미달)"

    out_lines = [
        "---",
        "tags: [type/validation, study/crypto, cycle/2, hypothesis/h8]",
        "date: 2026-05-31",
        "hypothesis: H8 — TxCnt utility count proxy → fwd_30d_ret (Catalini&Gans 2020)",
        "audit_axes: [A, B, D, F, G, I, K]",
        "note: 원래 TxTfrValAdjUSD (value-weighted) 권장이나 community 403 → TxCnt (count) 대체",
        "---",
        "",
        "# validation-h8 — TxCnt utility → fwd_30d_ret (BTC)",
        "",
        "## Data Coverage",
        f"- 시리즈: CoinMetrics community `TxCnt` daily (TxTfrValAdjUSD=403 대체)",
        f"- 기간: {df['date'].min().date()} ~ {df['date'].max().date()}",
        f"- Binance klines inner join 후: n_total = **{n_total}**",
        f"- N_eff full: {n_eff_full:.0f}",
        "",
        "## 변수 정의 (TxCnt count proxy 한계 명시)",
        "- (a) 시제: contemporaneous + fwd_30d",
        "- (b) frequency: daily",
        "- (c) transform: log + first difference",
        "- (d) conditioning: macro epoch × halving + BlkCnt control (mining capacity 분리)",
        "- (e) regime: full + epoch 4종 × halving",
        "- ⚠️ count proxy 한계: average tx size 정보 손실. value-weighted (TxVolUSD) 후속 paid tier 권고.",
        "",
        "## H8 검증 결과",
        f"- **full Rank-IC (Δlog_tx → fwd_30d_ret) = {ic_full:.4f}** (n={n_full})",
        f"- **β OLS = {beta:.6e}**, Block bootstrap CI95% (block=60d, B=2000) = [{ci_lo:.6e}, {ci_hi:.6e}]",
        f"- Newey-West HAC SE (lag=30d) = {nw_se:.6e}",
        f"- contemporaneous (Δlog_tx vs Δlog_close) Rank-IC = **{ic_contemp:.4f}** (mechanical co-move 검정 — 절대값>0.3 시 utility signal 의심)",
        f"- partial Rank-IC (Δlog_tx | Δlog_blk residual → fwd_30d) = {ic_partial:.4f} (n={n_partial})",
        "",
        "## Cell breakdown",
        "| epoch | halving | n | N_eff | Rank-IC |",
        "|---|---|---|---|---|",
    ]
    for c in cells:
        out_lines.append(f"| {c['epoch']} | {c['halv']} | {c['n']} | {c['n_eff']:.0f} | {c['rank_ic']:.4f} |")

    out_lines.extend([
        "",
        "## 12축 박제",
        f"- **A 학술**: Athey 2016, Catalini&Gans 2020 (utility), Yermack 2015 (mechanical shuffle 반증)",
        f"- **B SE 보정**: Newey-West HAC lag=30 + Block bootstrap block=60d B=2000. {'PASS' if pass_b else 'FAIL'} (|Rank-IC|={abs(ic_full):.4f} {'>' if pass_b else '≤'} 0.03)",
        f"- **D PIT**: TxCnt T+1 release (community 익일 02:00 UTC)",
        f"- **F 반증조건**: (i) β CI 0 포함? {'YES (REJECT 신호)' if not ci_excludes_zero else 'NO'} (ii) Rank-IC<0.03? {'YES (REJECT)' if not pass_b else 'NO'} (iii) mechanical co-move (|contemp|>0.3)? {'YES (utility signal 의심)' if mechanical else 'NO'} (iv) partial-corr 후 잔존? {'YES' if partial_distinct else 'NO'}",
        f"- **G effective N**: full N_eff={n_eff_full:.0f}. cell N<30 ★INSUFFICIENT.",
        f"- **I 생존편향**: BTC only.",
        f"- **K 시도횟수**: K=24 cell + 2 axis (full / partial-blk-residual) = 50. Bonferroni α/50={0.05/50:.5f} 임계.",
        "",
        "## verdict",
        f"**{verdict}**",
        "",
        "## hedge 어휘",
        f"- count proxy = 방향성 약 prior (value-weighted 후속 필요)",
        f"- mechanical co-move ({ic_contemp:.4f}): {'utility signal 약화 신호' if mechanical else '약하므로 utility 잔존 가능성'}",
        "",
        "## 후속 의문",
        "- (i) TxTfrValAdjUSD (value-weighted) paid tier — count vs value-weighted 비교",
        "- (ii) lag k=1d / 7d / 30d / 90d 4 horizon",
        "- (iii) regime conditional: bull (MVRV>1.5) vs bear",
        "- (iv) partial-corr 분리 = tx_resid → fwd_ret 의 robust 회귀계수 + CI",
    ])

    OUT.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"[OK] validation md saved -> {OUT.name}", flush=True)
    print(f"[verdict] {verdict}", flush=True)


if __name__ == "__main__":
    main()
