"""eq_intl 2-2-A China 정량치 cross-check.

가설: IMF Jan 2023 - MSCI China rolling β vs World 1.2 → 0.2 (2021 중반 → 2022 말)
    MS 2022-2023 - 글로벌 macro factor R² 30~40% → <10% (2018 이전 → 2022)
    AQR 2023 - 2022 KWEB DXY β ≈ 0

직접 재현: Yahoo 5y daily 의 MCHI/KWEB/EMXC/ACWI/DXY 로 12m rolling β 계산.
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


def beta_window(y_dict, x_dict, dates):
    """OLS β: y_t = a + b*x_t + e. dates = 정렬된 공통 일자."""
    if len(dates) < 30:
        return None
    xs = [x_dict[d] for d in dates]
    ys = [y_dict[d] for d in dates]
    mx, my = st.mean(xs), st.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return None
    b = num / den
    a = my - b * mx
    ss_res = sum((yi - (a + b * xi)) ** 2 for yi, xi in zip(ys, xs))
    ss_tot = sum((yi - my) ** 2 for yi in ys)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    return b, r2, len(dates)


def rolling_beta_monthly(y_dict, x_dict, window_days=252, step_months=1):
    """월말 기준 12m rolling β 시퀀스. (year, month) → (β, R², n)."""
    all_dates = sorted(set(y_dict) & set(x_dict))
    # 월말 endpoint = 각 달의 마지막 obs 일
    by_ym = defaultdict(list)
    for d in all_dates:
        by_ym[(d.year, d.month)].append(d)
    me = {ym: lst[-1] for ym, lst in by_ym.items()}
    sorted_ym = sorted(me.keys())
    out = {}
    for ym in sorted_ym:
        end = me[ym]
        idx = all_dates.index(end)
        if idx < window_days:
            continue
        window = all_dates[idx - window_days: idx + 1]
        res = beta_window(y_dict, x_dict, window)
        if res:
            out[ym] = res
    return out


prices = {a: to_dict(load(a)) for a in [
    "msci_china", "china_internet", "em_ex_china", "world", "dxy", "us_spy", "em_broad", "vix"
]}
dly = {a: log_ret(s) for a, s in prices.items()}
print(f"# Loaded {len(prices)} series, daily returns {len(dly['msci_china'])} obs (5y)\n")

# ============================================================
# CC1. MCHI vs ACWI (MSCI World) 12m rolling β — IMF "1.2 → 0.2"
# ============================================================
print("=" * 70)
print("CC1. MCHI vs ACWI (World) 12m rolling β — IMF 가설 '1.2 → 0.2'")
print("=" * 70)
rb_mchi_world = rolling_beta_monthly(dly["msci_china"], dly["world"])
print(f"{'month':<10}{'β':>10}{'R²':>8}{'n':>6}")
for ym in sorted(rb_mchi_world):
    b, r2, n = rb_mchi_world[ym]
    print(f"{ym[0]}-{ym[1]:02d}    {b:>10.3f}{r2:>8.3f}{n:>6d}")

# ============================================================
# CC2. EMXC (EM ex-China) vs ACWI 12m rolling β — 비교 baseline
# ============================================================
print("\n" + "=" * 70)
print("CC2. EMXC (EM ex-China) vs ACWI 12m rolling β — IMF claim '안정 유지' 비교")
print("=" * 70)
rb_emxc_world = rolling_beta_monthly(dly["em_ex_china"], dly["world"])
print(f"{'month':<10}{'β':>10}{'R²':>8}{'n':>6}")
for ym in sorted(rb_emxc_world):
    b, r2, n = rb_emxc_world[ym]
    print(f"{ym[0]}-{ym[1]:02d}    {b:>10.3f}{r2:>8.3f}{n:>6d}")

# ============================================================
# CC3. KWEB vs DXY 12m rolling β — AQR 2022 "≈0"
# ============================================================
print("\n" + "=" * 70)
print("CC3. KWEB vs DXY 12m rolling β — AQR 2022 가설 '≈ 0'")
print("=" * 70)
rb_kweb_dxy = rolling_beta_monthly(dly["china_internet"], dly["dxy"])
print(f"{'month':<10}{'β':>10}{'R²':>8}{'n':>6}")
for ym in sorted(rb_kweb_dxy):
    b, r2, n = rb_kweb_dxy[ym]
    print(f"{ym[0]}-{ym[1]:02d}    {b:>10.3f}{r2:>8.3f}{n:>6d}")

# ============================================================
# CC4. MCHI multi-factor R² — MS '30%→<10%'
# DXY + VIX + US10Y proxy (=SPY 로 일부 대체, FRED 없음)
# ============================================================
print("\n" + "=" * 70)
print("CC4. MCHI multi-factor R² (DXY+VIX+SPY) — MS 가설 '30%→<10%'")
print("=" * 70)


def multi_r2(y_dict, x_dicts, dates):
    """multivariate OLS R² via normal equations. x_dicts = list of dict."""
    if len(dates) < 30:
        return None
    n = len(dates)
    k = len(x_dicts)
    # X = [1, x1, x2, ...]
    X = [[1.0] + [xd[d] for xd in x_dicts] for d in dates]
    y = [y_dict[d] for d in dates]
    # XtX
    cols = k + 1
    XtX = [[0.0] * cols for _ in range(cols)]
    Xty = [0.0] * cols
    for i in range(n):
        for r in range(cols):
            Xty[r] += X[i][r] * y[i]
            for c in range(cols):
                XtX[r][c] += X[i][r] * X[i][c]
    # Solve XtX b = Xty (Gauss-Jordan)
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
    return 1 - ss_res / ss_tot if ss_tot > 0 else 0


# rolling multi-factor R² monthly
def rolling_mr2_monthly(y_dict, x_dicts, window_days=252):
    common = set(y_dict)
    for xd in x_dicts:
        common &= set(xd)
    all_dates = sorted(common)
    by_ym = defaultdict(list)
    for d in all_dates:
        by_ym[(d.year, d.month)].append(d)
    me = {ym: lst[-1] for ym, lst in by_ym.items()}
    sorted_ym = sorted(me.keys())
    out = {}
    for ym in sorted_ym:
        end = me[ym]
        idx = all_dates.index(end)
        if idx < window_days:
            continue
        window = all_dates[idx - window_days: idx + 1]
        r2 = multi_r2(y_dict, x_dicts, window)
        if r2 is not None:
            out[ym] = r2
    return out


rb_r2_mchi = rolling_mr2_monthly(dly["msci_china"], [dly["dxy"], dly["vix"], dly["us_spy"]])
print(f"{'month':<10}{'R²':>8}")
for ym in sorted(rb_r2_mchi):
    print(f"{ym[0]}-{ym[1]:02d}    {rb_r2_mchi[ym]:>8.3f}")

# 비교: EMXC R²
rb_r2_emxc = rolling_mr2_monthly(dly["em_ex_china"], [dly["dxy"], dly["vix"], dly["us_spy"]])
print(f"\nEMXC R² 비교 (= MCHI 와 같은 multi-factor):")
print(f"{'month':<10}{'R²':>8}")
for ym in sorted(rb_r2_emxc):
    print(f"{ym[0]}-{ym[1]:02d}    {rb_r2_emxc[ym]:>8.3f}")

# ============================================================
# CC5. 요약 통계
# ============================================================
print("\n" + "=" * 70)
print("CC5. cross-check 요약 통계")
print("=" * 70)
mchi_betas = [rb_mchi_world[k][0] for k in sorted(rb_mchi_world)]
emxc_betas = [rb_emxc_world[k][0] for k in sorted(rb_emxc_world)]
kweb_betas = [rb_kweb_dxy[k][0] for k in sorted(rb_kweb_dxy)]
mchi_r2s = [rb_r2_mchi[k] for k in sorted(rb_r2_mchi)]
emxc_r2s = [rb_r2_emxc[k] for k in sorted(rb_r2_emxc)]

if mchi_betas:
    print(f"MCHI β vs World: min={min(mchi_betas):.2f} max={max(mchi_betas):.2f} mean={st.mean(mchi_betas):.2f} range={max(mchi_betas)-min(mchi_betas):.2f}")
if emxc_betas:
    print(f"EMXC β vs World: min={min(emxc_betas):.2f} max={max(emxc_betas):.2f} mean={st.mean(emxc_betas):.2f} range={max(emxc_betas)-min(emxc_betas):.2f}")
if kweb_betas:
    print(f"KWEB β vs DXY  : min={min(kweb_betas):.2f} max={max(kweb_betas):.2f} mean={st.mean(kweb_betas):.2f}")
if mchi_r2s:
    print(f"MCHI multi-R² : min={min(mchi_r2s):.2f} max={max(mchi_r2s):.2f} mean={st.mean(mchi_r2s):.2f}")
if emxc_r2s:
    print(f"EMXC multi-R² : min={min(emxc_r2s):.2f} max={max(emxc_r2s):.2f} mean={st.mean(emxc_r2s):.2f}")

# 시점 별: 2022 vs 2024 비교 (IMF/MS claim 직접 검증)
print(f"\n시점 비교 (IMF/MS claim 핵심 시점):")


def near_month(out, y, m):
    keys = sorted(out)
    target = (y, m)
    for k in keys:
        if k >= target:
            return out[k]
    return out[keys[-1]] if keys else None


for label, out, kind in [
    ("MCHI β vs World", rb_mchi_world, "tuple"),
    ("EMXC β vs World", rb_emxc_world, "tuple"),
    ("MCHI multi-R²", rb_r2_mchi, "scalar"),
    ("EMXC multi-R²", rb_r2_emxc, "scalar"),
    ("KWEB β vs DXY", rb_kweb_dxy, "tuple"),
]:
    keys = sorted(out)
    if not keys:
        continue
    # 첫 가용 / 2022-12 / 마지막
    first = out[keys[0]]
    last = out[keys[-1]]
    dec22 = near_month(out, 2022, 12)
    if kind == "tuple":
        f = f"{first[0]:+.2f}"
        d22 = f"{dec22[0]:+.2f}" if dec22 else "n/a"
        l = f"{last[0]:+.2f}"
    else:
        f = f"{first:.2f}"
        d22 = f"{dec22:.2f}" if dec22 is not None else "n/a"
        l = f"{last:.2f}"
    print(f"  {label:<20} first({keys[0]})={f}  2022-12={d22}  last({keys[-1]})={l}")

print("\n# Done.")
