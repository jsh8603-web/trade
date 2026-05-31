"""eq_intl M3 거시연관 분석 — timeline.md §4 가이드 적용.

원칙: PIT (일별 종가 = knowable_from) · OOS regime 라벨 사용 · 합성금지 (raw daily log-return).

산출: stdout (study-research/eq_intl/macro-linkage.md 박제용 표).

★main 의무: rate 직접 loading 보다 dollar 채널·국면조건부가 본질 (M1 발견 검증).
"""
import os, csv, math, statistics as st, sys
from datetime import date
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DIR = os.path.join(os.path.dirname(__file__), "yahoo_cache")


def load(alias):
    p = os.path.join(DIR, f"{alias}.csv")
    rows = []
    with open(p, encoding="utf-8") as f:
        r = csv.reader(f); next(r)
        for d_str, px in r:
            rows.append((date.fromisoformat(d_str), float(px)))
    return rows


def to_dict(rows):
    return {d: p for d, p in rows}


def log_ret(prices):
    items = sorted(prices.items())
    out = {}
    for i in range(1, len(items)):
        d0, p0 = items[i - 1]
        d1, p1 = items[i]
        if p0 > 0 and p1 > 0:
            out[d1] = math.log(p1 / p0)
    return out


def level_diff(values):
    """level Δ (yield change in pp). values = dict[date]→%."""
    items = sorted(values.items())
    out = {}
    for i in range(1, len(items)):
        out[items[i][0]] = items[i][1] - items[i - 1][1]
    return out


def pearson(xs, ys):
    if len(xs) < 5:
        return None
    mx, my = st.mean(xs), st.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx > 0 and dy > 0 else None


def multi_ols(y_dict, x_dicts, dates):
    if len(dates) < 30:
        return None
    n = len(dates)
    k = len(x_dicts)
    X = [[1.0] + [xd[d] for xd in x_dicts] for d in dates]
    y = [y_dict[d] for d in dates]
    cols = k + 1
    XtX = [[0.0] * cols for _ in range(cols)]
    Xty = [0.0] * cols
    for i in range(n):
        for r in range(cols):
            Xty[r] += X[i][r] * y[i]
            for c in range(cols):
                XtX[r][c] += X[i][r] * X[i][c]
    M = [row[:] + [Xty[r]] for r, row in enumerate(XtX)]
    for r in range(cols):
        piv = M[r][r]
        if abs(piv) < 1e-12:
            return None
        for c in range(cols + 1):
            M[r][c] /= piv
        for rr in range(cols):
            if rr != r:
                f = M[rr][r]
                for c in range(cols + 1):
                    M[rr][c] -= f * M[r][c]
    b = [M[r][cols] for r in range(cols)]
    yhat = [sum(b[r] * X[i][r] for r in range(cols)) for i in range(n)]
    my = st.mean(y)
    ss_res = sum((y[i] - yhat[i]) ** 2 for i in range(n))
    ss_tot = sum((y[i] - my) ** 2 for i in range(n))
    return {"coefs": b, "r2": 1 - ss_res / ss_tot if ss_tot > 0 else 0, "n": n}


# ============================================================
# Load
# ============================================================
COUNTRIES = ["us_spy", "dm_exus", "japan", "germany", "uk", "em_broad", "brazil",
             "india", "china", "korea", "taiwan", "mexico", "europe"]
INTL_ONLY = [c for c in COUNTRIES if c != "us_spy"]  # 12개 — within-sleeve
DRIVERS = {"rate": "tnx_10y_yield", "dollar": "dxy", "oil": "wti_oil"}

prices = {a: to_dict(load(a)) for a in COUNTRIES + ["dxy", "wti_oil", "tnx_10y_yield"]}

# returns
dly = {c: log_ret(prices[c]) for c in COUNTRIES}
dly["dollar"] = log_ret(prices["dxy"])
dly["oil"] = log_ret(prices["wti_oil"])
dly["rate"] = level_diff(prices["tnx_10y_yield"])  # Δ yield (pp)

# ============================================================
# Regime epochs (timeline §3 + E5 신규 = 2025~2026 추가 인하 + Trump 2.0 dollar)
# ============================================================
EPOCHS = [
    ("Pre-E1", date(2021, 5, 1),  date(2021, 12, 31), "COVID 회복·완화 잔류 (pre-tightening)"),
    ("E1",     date(2022, 1, 1),  date(2022, 9, 30),  "긴축충격 rate↑↑·dollar↑↑·risk-off"),
    ("E2",     date(2022, 10, 1), date(2023, 6, 30),  "전환·반등 rate 고원→완화초입, AI 성장"),
    ("E3",     date(2023, 7, 1),  date(2023, 9, 30),  "금리재상승 rate↑·oil↑"),
    ("E4",     date(2023, 10, 1), date(2024, 12, 31), "pivot·인하 rate↓·dollar↓"),
    ("E5",     date(2025, 1, 1),  date(2026, 5, 30),  "★신규: 추가 인하 + Trump 2.0 dollar regime"),
]


def epoch_dates(start, end, series_dict):
    return sorted(d for d in series_dict if start <= d <= end)


print(f"# eq_intl M3 거시연관 분석 (timeline.md §4 가이드)")
print(f"# Universe: {len(COUNTRIES)} country ETF + 3 driver (rate=^TNX Δlevel, dollar=DXY Δlog, oil=WTI Δlog)")
print(f"# 원칙: PIT 종가 · OOS regime 라벨 · 합성 X (raw daily log-return)\n")

# ============================================================
# §1. regime 별 ETF 수익률·변동성 분해
# ============================================================
print("=" * 78)
print("§1. Regime 별 수익률·변동성 (월화산: mean × 252, vol × sqrt(252))")
print("=" * 78)
print(f"{'epoch':<8}{'ETF':<14}{'ann_ret':>10}{'ann_vol':>10}{'sharpe':>8}{'n_days':>8}")
epoch_stats = {}
for ename, e_start, e_end, _ in EPOCHS:
    epoch_stats[ename] = {}
    for c in COUNTRIES:
        dates = epoch_dates(e_start, e_end, dly[c])
        if len(dates) < 10:
            continue
        rets = [dly[c][d] for d in dates]
        ann_ret = st.mean(rets) * 252
        ann_vol = st.stdev(rets) * math.sqrt(252) if len(rets) > 1 else 0
        sharpe = ann_ret / ann_vol if ann_vol > 0 else 0
        epoch_stats[ename][c] = {"ann_ret": ann_ret, "ann_vol": ann_vol, "sharpe": sharpe, "n": len(dates)}
    # 표 (sleeve avg + 핵심 ETF)
    sleeve_ret = st.mean([epoch_stats[ename][c]["ann_ret"] for c in INTL_ONLY if c in epoch_stats[ename]])
    sleeve_vol = st.mean([epoch_stats[ename][c]["ann_vol"] for c in INTL_ONLY if c in epoch_stats[ename]])
    print(f"{ename:<8}{'sleeve-avg':<14}{sleeve_ret:>+10.2%}{sleeve_vol:>10.2%}{sleeve_ret/sleeve_vol if sleeve_vol>0 else 0:>8.2f}{'':>8}")
    for c in ["em_broad", "europe", "japan", "china", "brazil", "korea"]:
        if c in epoch_stats[ename]:
            s = epoch_stats[ename][c]
            print(f"{'':<8}{c:<14}{s['ann_ret']:>+10.2%}{s['ann_vol']:>10.2%}{s['sharpe']:>8.2f}{s['n']:>8d}")
    print()

# ============================================================
# §2. 거시 driver loading (multi OLS: ETF ~ Δrate + Δlog_DXY + Δlog_WTI)
#     ★전체 + epoch 별 분해 — rate 직접 vs dollar 채널 vs 국면조건부
# ============================================================
print("=" * 78)
print("§2. Multi-driver OLS: ETF ~ α + β_rate·Δrate + β_dollar·Δlog_DXY + β_oil·Δlog_WTI")
print("=" * 78)


def fit_etf(c, dates):
    common = sorted(set(dates) & set(dly[c]) & set(dly["rate"]) & set(dly["dollar"]) & set(dly["oil"]))
    if len(common) < 30:
        return None
    return multi_ols(dly[c], [dly["rate"], dly["dollar"], dly["oil"]], common)


# 전체 5y
all_dates_intl = sorted(set.intersection(*[set(dly[c]) for c in INTL_ONLY]) & set(dly["rate"]))
print(f"\n[전체 5y, n_days≈{len(all_dates_intl)}]")
print(f"{'ETF':<14}{'β_rate':>10}{'β_dollar':>12}{'β_oil':>10}{'R²':>8}")
all_betas = {}
for c in INTL_ONLY:
    res = fit_etf(c, all_dates_intl)
    if res:
        b = res["coefs"]
        all_betas[c] = b
        print(f"{c:<14}{b[1]:>+10.4f}{b[2]:>+12.4f}{b[3]:>+10.4f}{res['r2']:>8.3f}")

# Epoch 별 (rate-up vs rate-down 국면 비교)
print(f"\n[Epoch 별 sleeve-avg β (rate / dollar / oil)]")
print(f"{'epoch':<8}{'β_rate(avg)':>14}{'β_dollar(avg)':>16}{'β_oil(avg)':>13}{'|β_dollar/β_rate|':>20}{'description':>}")
for ename, e_start, e_end, edesc in EPOCHS:
    dates = [d for d in all_dates_intl if e_start <= d <= e_end]
    if len(dates) < 30:
        print(f"{ename:<8} (skip — n_days {len(dates)} < 30)")
        continue
    rates, dolls, oils = [], [], []
    for c in INTL_ONLY:
        res = fit_etf(c, dates)
        if res:
            b = res["coefs"]
            rates.append(b[1]); dolls.append(b[2]); oils.append(b[3])
    if rates:
        r_avg = st.mean(rates); d_avg = st.mean(dolls); o_avg = st.mean(oils)
        ratio = abs(d_avg / r_avg) if abs(r_avg) > 1e-6 else float("inf")
        print(f"{ename:<8}{r_avg:>+14.4f}{d_avg:>+16.4f}{o_avg:>+13.4f}{ratio:>20.2f}  ({edesc[:40]})")

# ============================================================
# §3. ★M1 발견 검증 — rate 직접 loading 보다 dollar 채널·국면조건부가 본질?
# ============================================================
print("\n" + "=" * 78)
print("§3. ★M1 발견 검증: rate 직접 vs dollar 채널 · 국면조건부")
print("=" * 78)

# 5y 전체에서: β_rate vs β_dollar 의 absolute magnitude
all_brate = [all_betas[c][1] for c in INTL_ONLY if c in all_betas]
all_bdollar = [all_betas[c][2] for c in INTL_ONLY if c in all_betas]
print(f"5y sleeve mean |β_rate|   = {st.mean([abs(b) for b in all_brate]):.4f} (Δ yield pp 당 일별 log-ret)")
print(f"5y sleeve mean |β_dollar| = {st.mean([abs(b) for b in all_bdollar]):.4f} (Δlog DXY 당 일별 log-ret)")

# rate-up 분리 (Δrate>0 day) vs rate-down (Δrate<0 day)
rate_up = [d for d in all_dates_intl if d in dly["rate"] and dly["rate"][d] > 0]
rate_dn = [d for d in all_dates_intl if d in dly["rate"] and dly["rate"][d] < 0]
print(f"\n[rate-up vs rate-down split (full 5y)]")
print(f"rate-up days: {len(rate_up)} / rate-down days: {len(rate_dn)}")
print(f"{'ETF':<14}{'β_dollar (up)':>15}{'β_dollar (dn)':>15}{'ratio up/dn':>15}")
for c in INTL_ONLY:
    res_up = fit_etf(c, rate_up)
    res_dn = fit_etf(c, rate_dn)
    if res_up and res_dn:
        bu = res_up["coefs"][2]
        bd = res_dn["coefs"][2]
        ratio = abs(bu / bd) if abs(bd) > 1e-6 else float("inf")
        print(f"{c:<14}{bu:>+15.4f}{bd:>+15.4f}{ratio:>15.2f}")

# ============================================================
# §4. cross-asset vs within-sleeve 구분 (L축 caveat)
#     within-sleeve = 12 country ETF 간 평균 pairwise 상관
#     cross-asset  = 각 ETF↔dollar 평균 상관
# ============================================================
print("\n" + "=" * 78)
print("§4. cross-asset vs within-sleeve (L축 caveat: within-sleeve 공통은 equity factor 소관)")
print("=" * 78)

# within-sleeve pairwise correlation
pair_corrs = []
for i in range(len(INTL_ONLY)):
    for j in range(i + 1, len(INTL_ONLY)):
        ci, cj = INTL_ONLY[i], INTL_ONLY[j]
        common = sorted(set(dly[ci]) & set(dly[cj]))
        if len(common) < 100:
            continue
        c = pearson([dly[ci][d] for d in common], [dly[cj][d] for d in common])
        if c is not None:
            pair_corrs.append((ci, cj, c))
within_avg = st.mean([c for _, _, c in pair_corrs]) if pair_corrs else 0
within_max = max([c for _, _, c in pair_corrs]) if pair_corrs else 0
within_min = min([c for _, _, c in pair_corrs]) if pair_corrs else 0
top_pairs = sorted(pair_corrs, key=lambda x: -x[2])[:5]
print(f"\nwithin-sleeve (12 country ETF pairwise daily corr):")
print(f"  avg = {within_avg:.3f}, range = [{within_min:.3f}, {within_max:.3f}]")
print(f"  top-5 pairs: {[(a, b, f'{c:.3f}') for a, b, c in top_pairs]}")

# cross-asset (ETF ↔ dollar / rate / oil)
print(f"\ncross-asset (ETF ↔ driver):")
for driver in ["dollar", "rate", "oil"]:
    cross = []
    for c in INTL_ONLY:
        common = sorted(set(dly[c]) & set(dly[driver]))
        if len(common) < 100:
            continue
        v = pearson([dly[c][d] for d in common], [dly[driver][d] for d in common])
        if v is not None:
            cross.append(v)
    if cross:
        print(f"  ETF ↔ {driver:<8}: avg = {st.mean(cross):+.3f}, range [{min(cross):+.3f}, {max(cross):+.3f}]")

print(f"\n★L축 caveat 판정:")
print(f"  within-sleeve avg corr = {within_avg:.3f}")
if within_avg > 0.7:
    print(f"  → 0.7 초과 — 거시 외 equity factor 공통(M1 caveat). 거시 driver 분리 시 부분 covariance 만 설명.")
elif within_avg > 0.5:
    print(f"  → 0.5~0.7 — equity factor + 거시 driver 혼합. 거시 loading 분리는 부분 valid.")
else:
    print(f"  → 0.5 미만 — 국가별 idiosyncratic 비중 큼. 거시 driver loading 의미 큰 부분 차지.")

print("\n# Done.")
