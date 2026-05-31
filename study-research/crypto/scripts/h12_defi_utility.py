"""H12 — DefiLlama TVL Δlog z → BTC fwd_30d (Cong 2022 DeFi utility 매개).

★H3 stablecoin supply Δ 와 multicollinearity 강함 — partial-corr 직교화 후 잔존 신호만 valid.
⛔ 점추정 prior 박제 X.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import linregress

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_common import (
    load_btc_klines, load_stablecoin, rank_ic, newey_west_se, effective_n,
    forward_return,
)

OUT = Path(__file__).resolve().parent.parent / "raw" / "validation-h12-defi-utility.md"
DATA = Path(__file__).resolve().parent.parent / "raw" / "data"


def main():
    tvl = pd.read_csv(DATA / "defillama-tvl-total.csv")
    tvl["date"] = pd.to_datetime(tvl["date_utc"], format="%Y-%m-%d")
    tvl["tvl"] = pd.to_numeric(tvl["tvl_total"], errors="coerce")
    tvl = tvl.dropna(subset=["tvl"]).sort_values("date").reset_index(drop=True)
    tvl["log_tvl"] = np.log(tvl["tvl"].replace(0, np.nan))
    tvl["dlog_tvl"] = tvl["log_tvl"].diff()
    tvl["tvl_z"] = (tvl["dlog_tvl"] - tvl["dlog_tvl"].rolling(252).mean()) / tvl["dlog_tvl"].rolling(252).std()

    stable = load_stablecoin()
    stable["log_stable"] = np.log(stable["total_supply"].replace(0, np.nan))
    stable["dlog_stable"] = stable["log_stable"].diff()
    stable["stable_z"] = (stable["dlog_stable"] - stable["dlog_stable"].rolling(252).mean()) / stable["dlog_stable"].rolling(252).std()

    btc = load_btc_klines()
    df = btc[["date", "close"]].merge(
        tvl[["date", "tvl_z"]], on="date", how="inner"
    ).merge(
        stable[["date", "stable_z"]], on="date", how="inner"
    )
    df = df.sort_values("date").reset_index(drop=True)
    df["fwd_30d_ret"] = forward_return(df["close"], horizon=30)
    n_total = df.dropna(subset=["tvl_z", "stable_z", "fwd_30d_ret"]).shape[0]

    print(f"[H12] n_total = {n_total}", flush=True)

    sub = df.dropna(subset=["tvl_z", "stable_z", "fwd_30d_ret"]).copy()
    ic_marg, n_marg = rank_ic(sub["tvl_z"], sub["fwd_30d_ret"])
    nw_se = newey_west_se(sub["fwd_30d_ret"].values, lags=30)
    n_eff_full = effective_n(sub["fwd_30d_ret"].values)
    ic_collin, _ = rank_ic(sub["tvl_z"], sub["stable_z"])

    s = linregress(sub["stable_z"], sub["tvl_z"])
    sub["tvl_resid"] = sub["tvl_z"] - (s.intercept + s.slope * sub["stable_z"])
    ic_partial, n_partial = rank_ic(sub["tvl_resid"], sub["fwd_30d_ret"])

    print(f"[H12 marginal] TVL z → fwd_30d Rank-IC={ic_marg:.4f} (n={n_marg}, N_eff={n_eff_full:.0f})", flush=True)
    print(f"[H12 collin] corr(TVL z, stablecoin z) = {ic_collin:.4f}", flush=True)
    print(f"[H12 partial] (TVL | stable) → fwd_30d Rank-IC={ic_partial:.4f}", flush=True)

    pass_marg = abs(ic_marg) > 0.03
    pass_partial = abs(ic_partial) > 0.03
    multicollin = abs(ic_collin) > 0.7

    if pass_partial and not multicollin:
        verdict = "PARTIAL CONFIRMED (partial-corr 잔존 신호, walk-forward 후속)"
    elif pass_marg and pass_partial:
        verdict = "TENTATIVE DIRECTIONAL (marginal + partial 둘 다 신호)"
    elif pass_marg and not pass_partial:
        verdict = "★REJECTED (marginal 신호는 stablecoin multicollin 효과)"
    else:
        verdict = "★REJECTED (Rank-IC<0.03 hard B 미달)"

    out_lines = [
        "---",
        "tags: [type/validation, study/crypto, cycle/2, hypothesis/h12]",
        "date: 2026-05-31",
        "hypothesis: H12 — DefiLlama TVL z → BTC fwd_30d (Cong 2022 DeFi utility, partial-corr stablecoin 직교화)",
        "audit_axes: [A, B, D, F, G, I, K, L]",
        "---",
        "",
        "# validation-h12 — DefiLlama TVL utility → BTC",
        "",
        "## Data Coverage",
        f"- DefiLlama TVL daily 3169 obs (2017-09 ~ 2026-05)",
        f"- DefiLlama stablecoin total 3105 obs (2017-11 ~ 2026-05)",
        f"- Binance BTC daily (2017-08~)",
        f"- inner join + 252d z-score warmup 후: **n_total = {n_total}**",
        "",
        "## H12 검증 결과",
        f"- marginal TVL z → fwd_30d Rank-IC = **{ic_marg:.4f}** (n={n_marg}, N_eff={n_eff_full:.0f})",
        f"- multicollin Rank-IC (TVL z vs stable z) = **{ic_collin:.4f}** ({'강함' if multicollin else '약함'})",
        f"- partial Rank-IC (TVL_resid | stable → fwd_30d) = **{ic_partial:.4f}**",
        f"- Newey-West HAC SE (lag=30d) = {nw_se:.6e}",
        "",
        "## 12축 박제",
        f"- **A 학술**: Cong et al 2022 JFE, Aramonte 2021 BIS, Schär 2021 FRBSL",
        f"- **B SE**: NW HAC lag=30d. partial |{ic_partial:.4f}| {'>' if pass_partial else '≤'} 0.03",
        f"- **D PIT**: DefiLlama daily T+1",
        f"- **F 반증조건**: (i) partial CI 0 포함 신호 부재 (ii) multicollin>0.7? {'YES' if multicollin else 'NO'} (iii) BTC 직접 vs ETH 매개 ETH dominant? cycle 3",
        f"- **G effective N**: full N_eff={n_eff_full:.0f}",
        f"- **I 생존편향**: surviving DeFi protocols TVL only (★상폐 protocols 누락)",
        f"- **K 시도횟수**: K=12. 본 라운드 = marginal + partial + collin = 3. Bonferroni α/12={0.05/12:.5f}",
        f"- **L 통합 상관**: TVL ↔ stablecoin 공통인자 (USD funding) — main 통합 중복 회피 박제",
        "",
        "## verdict",
        f"**{verdict}**",
        "",
        "## 후속 의문",
        "- (i) ETH 매개 검증 (BTC 자체 DeFi 작음)",
        "- (ii) DEX volume 별도 (TVL stock vs flow)",
        "- (iii) walk-forward strict OOS",
    ]

    OUT.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"[OK] -> {OUT.name}", flush=True)
    print(f"[verdict] {verdict}", flush=True)


if __name__ == "__main__":
    main()
