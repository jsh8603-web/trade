"""H4 ETF net flow probation — Farside Investors daily HTML parse + post-2024 검증.

가설: BTC ETF net inflow 5d 누적 > 0 -> 30d 가격 상승 (digital-gold demand)
반증조건: post-2024 OOS Rank-IC e-CUSUM 단측 붕괴 OR partial-corr | SPX 0 포함
- prior = observe-only 0.05 (probation, claude r3 정정)
- short sample N ≈ 1.5yr 명시
"""
from __future__ import annotations
import sys
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
import pandas as pd
from scipy import stats
from lib_common import load_btc_klines, rank_ic, block_bootstrap_ci, effective_n

OUT = Path(__file__).resolve().parent.parent / "raw" / "validation-h4-etf-flow.md"
HTML = Path(__file__).resolve().parent.parent / "raw" / "data" / "farside-etf-raw.html"


def parse_farside_html(html_text: str) -> pd.DataFrame:
    """Farside HTML table -> daily DataFrame (date, total_net_flow_musd).

    farside.co.uk 의 BTC ETF flow 표는 매일 (Date, IBIT, FBTC, BITB, ARKB, BTCO, EZBC, BRRR, HODL, BTCW, GBTC, BTC, Total) 형식.
    Total 칼럼이 net flow (USD million, 단위는 표 footer 명시).
    """
    # 간이 정규식 파싱 (BeautifulSoup 없이)
    rows = []
    # tbody 의 tr 행 추출
    tr_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
    td_pattern = re.compile(r"<td[^>]*>(.*?)</td>", re.S | re.I)
    tag_strip = re.compile(r"<[^>]+>")

    for tr_match in tr_pattern.finditer(html_text):
        cells = [tag_strip.sub("", c).strip() for c in td_pattern.findall(tr_match.group(1))]
        if not cells or len(cells) < 3:
            continue
        # 첫 셀이 날짜 (DD MMM YYYY)
        date_str = cells[0]
        # 마지막 셀 = Total
        try:
            date = pd.to_datetime(date_str, format="%d %b %Y", errors="coerce")
        except Exception:
            continue
        if pd.isna(date):
            continue
        # Total 시도 (마지막 numeric 칼럼)
        total = cells[-1].replace(",", "").replace("(", "-").replace(")", "")
        try:
            total_val = float(total)
        except ValueError:
            continue
        rows.append({"date": date, "total_flow_musd": total_val, "n_cells": len(cells)})

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).drop_duplicates("date").sort_values("date").reset_index(drop=True)
    return df


def main():
    lines = []
    def w(s=""): lines.append(s)

    w("# H4 ETF net flow probation — 실데이터 검증")
    w()
    w(f"as_of: {pd.Timestamp.utcnow().isoformat()}")

    if not HTML.exists():
        w(f"[FAIL] Farside HTML 미수집 ({HTML.name})")
        w("→ 본 가설 검증 보류, prior=observe-only 0.05 유지")
        OUT.write_text("\n".join(lines), encoding="utf-8")
        print(f"[OK] H4 -> {OUT} (no data)")
        return

    html_text = HTML.read_text(encoding="utf-8", errors="replace")
    etf = parse_farside_html(html_text)

    if etf.empty:
        w(f"[FAIL] Farside HTML 파싱 실패 (HTML 구조 변경 가능)")
        w("→ 본 가설 검증 보류, prior=observe-only 0.05 유지")
        OUT.write_text("\n".join(lines), encoding="utf-8")
        print(f"[OK] H4 -> {OUT} (parse failed)")
        return

    w(f"data: Farside Investors daily ETF flow (musd)")
    w(f"  n={len(etf)}, {etf['date'].min().date()} ~ {etf['date'].max().date()}")
    w(f"  total cumulative inflow = {etf['total_flow_musd'].sum():+,.1f} M USD")
    w()

    # ===== 1. 기본 통계 =====
    w("## 1. ETF net flow 분포")
    desc = etf["total_flow_musd"].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])
    w("```")
    w(desc.to_string())
    w("```")
    w(f"- 양 inflow 일수: {(etf['total_flow_musd'] > 0).sum()} / {len(etf)}")
    w(f"- 음 outflow 일수: {(etf['total_flow_musd'] < 0).sum()}")
    w()

    # ===== 2. BTC price merge & forward return =====
    klines = load_btc_klines()
    df = klines.merge(etf, on="date", how="inner")
    df["log_ret_7d_fwd"] = np.log(df["close"].shift(-7) / df["close"])
    df["log_ret_30d_fwd"] = np.log(df["close"].shift(-30) / df["close"])
    df["flow_5d_cum"] = df["total_flow_musd"].rolling(5).sum()

    w("## 2. ETF flow vs BTC forward return")
    w(f"- merged n={len(df)} (Binance klines ∩ Farside)")
    w(f"- post-2024-01 N effective = ~{(df['date'] >= '2024-01-11').sum()}d (probation)")

    for h_col in ["log_ret_7d_fwd", "log_ret_30d_fwd"]:
        rho, n = rank_ic(df["total_flow_musd"], df[h_col])
        w(f"- daily flow -> {h_col}: Rank-IC = {rho:+.4f}, n={n}")
        rho_cum, n_cum = rank_ic(df["flow_5d_cum"], df[h_col])
        w(f"- 5d cum flow -> {h_col}: Rank-IC = {rho_cum:+.4f}, n={n_cum}")
        valid = df[["flow_5d_cum", h_col]].dropna()
        if len(valid) > 100:
            def stat_rho(idx):
                idx = np.asarray(idx, dtype=int) % len(valid)
                return stats.spearmanr(valid["flow_5d_cum"].values[idx], valid[h_col].values[idx])[0]
            lo, mu, hi = block_bootstrap_ci(np.arange(len(valid)).astype(float), stat_rho, n_boot=300, block_len=20)
            w(f"  block-bootstrap 95% CI = ({lo:+.4f}, {hi:+.4f})")
    w()

    # ===== 3. cumulative inflow 5d > 0 -> fwd 30d 양 hit rate =====
    w("## 3. Hit rate — flow_5d_cum > 0 진입 후 fwd_30d > 0")
    sig = df["flow_5d_cum"] > 0
    sub = df[sig & df["log_ret_30d_fwd"].notna()]
    n = len(sub)
    if n >= 5:
        hits = int((sub["log_ret_30d_fwd"] > 0).sum())
        rate = hits / n
        p = stats.binomtest(hits, n, 0.5, alternative="greater").pvalue
        w(f"- n={n}, hits={hits}, rate={rate:.4f}, binomial p(>0.5)={p:.4f}")
    w()

    # ===== 4. Effective N =====
    w("## 4. Effective N (autocorr-adjusted)")
    eff = effective_n(df["total_flow_musd"].dropna().values)
    w(f"- ETF flow effective N = {eff:.1f} (raw N = {df['total_flow_musd'].notna().sum()})")
    w(f"- 1.5~2yr sample 짧음 명시 -> observe-only prior 0.05 유지")
    w()

    # ===== 5. 가설 판정 =====
    w("## 5. 가설 판정")
    w("- Rank-IC 양 + CI 0 미포함 + binomial p<0.05 = 1차 검증 (단 N 작음 강조)")
    w("- prior = observe-only 0.05 (probation) 유지 -- 데이터 누적 시 confidence_hooks 가 OOS reject_signal 발화")
    w()
    w("## 6. 미해결 의문")
    w("- post-2024 1.5~2yr 만 -> effective N 적음, CI 매우 넓음")
    w("- Farside 단일 free source 의존 (스키마 변동 위험)")
    w("- 역인과 위험: ETF flow 가 price-chasing (reflexive) 일 수 있음 -> 후속 lead-lag 검증 권고")
    w("- OTC / non-US ETF / futures basis 누락 -> 'institutional demand' 전체 아님")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] H4 -> {OUT}")


if __name__ == "__main__":
    main()
