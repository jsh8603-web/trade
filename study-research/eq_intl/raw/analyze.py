"""eq_intl 가설 대조 — 상관 · regime 분해 · Rank-IC · cross-country beta.

CSV in yahoo_cache/ → 통계 표 출력. raw 는 디스크 cache, 결과 = print 만.
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
        r = csv.reader(f)
        next(r)
        for d_str, px in r:
            rows.append((date.fromisoformat(d_str), float(px)))
    return rows


def to_dict(rows):
    return {d: p for d, p in rows}


def log_ret(series):
    """일별 ln(p_t / p_{t-1}). returns dict[date]→ret."""
    items = sorted(series.items())
    out = {}
    for i in range(1, len(items)):
        d0, p0 = items[i - 1]
        d1, p1 = items[i]
        if p0 > 0 and p1 > 0:
            out[d1] = math.log(p1 / p0)
    return out


def monthly_ret(prices_dict):
    """월말 종가 기준 월별 log-return. dict[(year, month)] → ret."""
    by_ym = defaultdict(list)
    for d, p in prices_dict.items():
        by_ym[(d.year, d.month)].append((d, p))
    me = {}  # month-end price
    for ym, lst in by_ym.items():
        lst.sort()
        me[ym] = lst[-1][1]
    months = sorted(me.keys())
    out = {}
    for i in range(1, len(months)):
        p0 = me[months[i - 1]]
        p1 = me[months[i]]
        if p0 > 0 and p1 > 0:
            out[months[i]] = math.log(p1 / p0)
    return out


def aligned(a, b):
    keys = sorted(set(a) & set(b))
    return [a[k] for k in keys], [b[k] for k in keys]


def pearson(xs, ys):
    if len(xs) < 5:
        return None
    mx, my = st.mean(xs), st.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def spearman(xs, ys):
    if len(xs) < 5:
        return None

    def rank(vs):
        idx = sorted(range(len(vs)), key=lambda i: vs[i])
        r = [0.0] * len(vs)
        i = 0
        while i < len(idx):
            j = i
            while j + 1 < len(idx) and vs[idx[j + 1]] == vs[idx[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[idx[k]] = avg
            i = j + 1
        return r

    return pearson(rank(xs), rank(ys))


def regress_beta(y, x):
    """univariate OLS: y = a + b*x + e. returns (beta, alpha, r2, n)."""
    if len(y) < 5 or len(y) != len(x):
        return None
    mx, my = st.mean(x), st.mean(y)
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    den = sum((xi - mx) ** 2 for xi in x)
    if den == 0:
        return None
    b = num / den
    a = my - b * mx
    ss_res = sum((yi - (a + b * xi)) ** 2 for yi, xi in zip(y, x))
    ss_tot = sum((yi - my) ** 2 for yi in y)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    return b, a, r2, len(y)


# ============================================================
# Load all series
# ============================================================
COUNTRIES = ["us_spy", "dm_exus", "japan", "germany", "uk", "em_broad", "brazil",
             "india", "china", "korea", "taiwan", "mexico", "europe"]
MACRO = ["dxy", "wti_oil", "vix"]

prices = {a: to_dict(load(a)) for a in COUNTRIES + MACRO}
print(f"# Loaded {len(prices)} series, each ~1255 daily obs (5y 2021-05~2026-05)\n")

dly = {a: log_ret(s) for a, s in prices.items()}
mly = {a: monthly_ret(s) for a, s in prices.items()}
print(f"# Daily returns: {len(dly['us_spy'])} obs. Monthly returns: {len(mly['us_spy'])} obs.\n")

# ============================================================
# H1: DXY ↔ 각 국가 ETF (일별 log-return 상관)
# ============================================================
print("=" * 70)
print("H1. DXY 일별 변화 ↔ 각 국가 ETF 일별 log-return 상관 (prior: 음수)")
print("=" * 70)
print(f"{'country':<14}{'pearson':>10}{'spearman':>12}{'n':>8}")
dxy_dly = dly["dxy"]
for c in COUNTRIES:
    xs, ys = aligned(dxy_dly, dly[c])
    p = pearson(xs, ys)
    s = spearman(xs, ys)
    print(f"{c:<14}{p:>10.3f}{s:>12.3f}{len(xs):>8d}")

# ============================================================
# H2: VIX ↔ 각 국가 ETF (risk-off 시 음수 = 하락)
# ============================================================
print("\n" + "=" * 70)
print("H2. VIX 일별 변화 ↔ 각 국가 ETF 일별 log-return 상관 (prior: 음수, EM 더 강함)")
print("=" * 70)
print(f"{'country':<14}{'pearson':>10}{'spearman':>12}{'n':>8}")
vix_dly = dly["vix"]
for c in COUNTRIES:
    xs, ys = aligned(vix_dly, dly[c])
    p = pearson(xs, ys)
    s = spearman(xs, ys)
    print(f"{c:<14}{p:>10.3f}{s:>12.3f}{len(xs):>8d}")

# ============================================================
# H3: WTI ↔ 각 국가 (commodity exporter 양수 / 수입국 음수)
# ============================================================
print("\n" + "=" * 70)
print("H3. WTI 일별 변화 ↔ 각 국가 ETF 일별 log-return (commodity exporter 양수)")
print("=" * 70)
print(f"{'country':<14}{'pearson':>10}{'spearman':>12}{'n':>8}")
wti_dly = dly["wti_oil"]
for c in COUNTRIES:
    xs, ys = aligned(wti_dly, dly[c])
    p = pearson(xs, ys)
    s = spearman(xs, ys)
    print(f"{c:<14}{p:>10.3f}{s:>12.3f}{len(xs):>8d}")

# ============================================================
# H4: Regime 분해 (VIX 30 threshold) — DXY↔EEM 상관이 regime 별로 다른가?
# ============================================================
print("\n" + "=" * 70)
print("H4. Regime 분해 — VIX 30 기준 risk-off/risk-on 분리 DXY↔EM 상관")
print("=" * 70)
# month-end VIX 로 regime split (월별 평균)
vix_me_avg = defaultdict(list)
for d, v in prices["vix"].items():
    vix_me_avg[(d.year, d.month)].append(v)
vix_me_avg = {k: st.mean(v) for k, v in vix_me_avg.items()}
risk_off_months = {k for k, v in vix_me_avg.items() if v > 25}
risk_on_months = {k for k, v in vix_me_avg.items() if v <= 25}
print(f"risk-off months (VIX>25): {len(risk_off_months)}, risk-on (≤25): {len(risk_on_months)}")

for c in ["em_broad", "brazil", "china", "korea", "japan", "europe"]:
    dxy_mly = mly["dxy"]
    c_mly = mly[c]
    keys_off = sorted(set(dxy_mly) & set(c_mly) & risk_off_months)
    keys_on = sorted(set(dxy_mly) & set(c_mly) & risk_on_months)
    p_off = pearson([dxy_mly[k] for k in keys_off], [c_mly[k] for k in keys_off]) if len(keys_off) >= 5 else None
    p_on = pearson([dxy_mly[k] for k in keys_on], [c_mly[k] for k in keys_on]) if len(keys_on) >= 5 else None
    print(f"  {c:<12} risk-off corr={p_off if p_off is None else f'{p_off:+.3f}'} (n={len(keys_off)}) | "
          f"risk-on corr={p_on if p_on is None else f'{p_on:+.3f}'} (n={len(keys_on)})")

# ============================================================
# H5: Cross-country dollar_beta (월별 OLS), oil_beta, vix_beta
# ============================================================
print("\n" + "=" * 70)
print("H5. Cross-country macro betas (월별 log-return univariate OLS)")
print("=" * 70)
print(f"{'country':<14}{'dxy_beta':>10}{'r2_dxy':>8}{'oil_beta':>10}{'r2_oil':>8}{'vix_beta':>10}{'r2_vix':>8}{'n':>5}")
betas = {}
for c in COUNTRIES:
    cm = mly[c]
    row = {"country": c}
    for macro_id in ["dxy", "wti_oil", "vix"]:
        mm = mly[macro_id]
        ks = sorted(set(cm) & set(mm))
        y = [cm[k] for k in ks]
        x = [mm[k] for k in ks]
        res = regress_beta(y, x)
        if res:
            b, a, r2, n = res
            row[f"{macro_id}_beta"] = b
            row[f"{macro_id}_r2"] = r2
            row["n"] = n
    betas[c] = row
    print(f"{c:<14}"
          f"{row.get('dxy_beta',0):>10.3f}{row.get('dxy_r2',0):>8.3f}"
          f"{row.get('wti_oil_beta',0):>10.3f}{row.get('wti_oil_r2',0):>8.3f}"
          f"{row.get('vix_beta',0):>10.3f}{row.get('vix_r2',0):>8.3f}"
          f"{row.get('n',0):>5d}")

# ============================================================
# H6: 12-1 momentum → next-month return Rank-IC (cross-country)
# ============================================================
print("\n" + "=" * 70)
print("H6. 12-1m momentum → 다음 1m return Rank-IC (cross-country, monthly)")
print("=" * 70)
# 각 월 t 에 대해, 각 국가의 t-12~t-1 cumulative log-return = momentum score
# t+1 의 log-return 과 cross-section Spearman 계산.
COUNTRY_ONLY = [c for c in COUNTRIES if c != "us_spy"]  # 횡단면 = US 제외 12개국
all_months = sorted(set.intersection(*[set(mly[c]) for c in COUNTRY_ONLY]))
ics = []
for i in range(12, len(all_months) - 1):
    mom_ym = all_months[i]
    nxt_ym = all_months[i + 1]
    moms = {}
    nxts = {}
    for c in COUNTRY_ONLY:
        cm = mly[c]
        # t-12~t-1 cum (= 12-1 momentum, exclude most recent month for short-term reversal)
        window = all_months[i - 12: i - 1]
        if not all(m in cm for m in window):
            continue
        moms[c] = sum(cm[m] for m in window)
        if nxt_ym in cm:
            nxts[c] = cm[nxt_ym]
    cs = sorted(set(moms) & set(nxts))
    if len(cs) >= 6:
        ic = spearman([moms[c] for c in cs], [nxts[c] for c in cs])
        if ic is not None:
            ics.append(ic)

if ics:
    print(f"Rank-IC (12-1 momentum → next-month return), monthly cross-section:")
    print(f"  mean IC = {st.mean(ics):+.4f}")
    print(f"  median IC = {st.median(ics):+.4f}")
    print(f"  std = {st.stdev(ics):.4f}")
    print(f"  n_months = {len(ics)}")
    print(f"  IC>0 ratio = {sum(1 for x in ics if x > 0) / len(ics):.2%}")
    icir = st.mean(ics) / st.stdev(ics) * math.sqrt(12) if st.stdev(ics) > 0 else None
    print(f"  IC-IR (annualized) ≈ {icir:+.3f}" if icir else "  IC-IR n/a")

# ============================================================
# H7: dollar_beta ↔ momentum cross-section (force_include)
# ============================================================
print("\n" + "=" * 70)
print("H7. Cross-country dollar_beta ↔ 평균 mom_12_1 (force_include 가설, prior: 음수)")
print("=" * 70)
# 각 국가의 dollar_beta (H5 에서 산출) ↔ 각 국가의 평균 12-1m momentum (전체 기간 평균)
dxy_betas = [betas[c]["dxy_beta"] for c in COUNTRY_ONLY if "dxy_beta" in betas[c]]
avg_moms = []
for c in COUNTRY_ONLY:
    cm = mly[c]
    # 전체 기간의 평균 월간 return = "장기 모멘텀 강도" proxy
    avg_moms.append(st.mean(list(cm.values())))
p = pearson(dxy_betas, avg_moms)
s = spearman(dxy_betas, avg_moms)
print(f"  pearson(dxy_beta, avg_monthly_return) = {p:+.3f}")
print(f"  spearman = {s:+.3f}")
print(f"  n_countries = {len(dxy_betas)}")
print(f"  dxy_betas: {[f'{b:+.2f}' for b in dxy_betas]}")
print(f"  countries: {COUNTRY_ONLY}")

# ============================================================
# H8: credit_beta ↔ realized_vol (force_include #2) — VIX-beta proxy
# ============================================================
print("\n" + "=" * 70)
print("H8. Cross-country vix_beta ↔ realized_vol (force_include 가설 prior: 양수)")
print("=" * 70)
vix_betas = [betas[c]["vix_beta"] for c in COUNTRY_ONLY if "vix_beta" in betas[c]]
rv = []  # 일별 log-return 의 stdev (annualized) = realized vol
for c in COUNTRY_ONLY:
    rets = list(dly[c].values())
    if len(rets) > 30:
        rv.append(st.stdev(rets) * math.sqrt(252))
p = pearson(vix_betas, rv)
s = spearman(vix_betas, rv)
print(f"  pearson(vix_beta, realized_vol_ann) = {p:+.3f}")
print(f"  spearman = {s:+.3f}")
print(f"  n_countries = {len(vix_betas)}")
for c, vb, rvi in zip(COUNTRY_ONLY, vix_betas, rv):
    print(f"    {c:<10} vix_beta={vb:+.3f} realized_vol={rvi:.2%}")

print("\n# Done.")
