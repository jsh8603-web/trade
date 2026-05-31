"""eq_intl 2-3 walk-forward OOS 검증 — H1/H2/H5/H7.

★의무: factor set 고정 (DXY+VIX+SPY) + train 24m / test 1m / refit 1m.
       block 4 weight freeze during test, in-sample 과적합 회피.

산출: stdout (validation-*.md 박제용 표) + raw/walkforward-output.txt.
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


def beta_univariate(y, x):
    if len(y) < 30:
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
    return b, r2


def multi_r2(y_dict, x_dicts, dates):
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
    return (1 - ss_res / ss_tot if ss_tot > 0 else 0), b


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

    rx, ry = rank(xs), rank(ys)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    return num / (dx * dy) if dx > 0 and dy > 0 else None


# ============================================================
COUNTRIES = ["us_spy", "dm_exus", "japan", "germany", "uk", "em_broad", "brazil",
             "india", "china", "korea", "taiwan", "mexico", "europe"]
MACRO = ["dxy", "vix", "msci_china", "em_ex_china"]
FACTOR_SET = ["dxy", "vix", "us_spy"]   # ★고정

prices = {a: to_dict(load(a)) for a in COUNTRIES + MACRO}
dly = {a: log_ret(s) for a, s in prices.items()}

# 월말 endpoints
all_dates_global = sorted(set.intersection(*[set(dly[a]) for a in dly]))
by_ym = defaultdict(list)
for d in all_dates_global:
    by_ym[(d.year, d.month)].append(d)
me = {ym: lst[-1] for ym, lst in by_ym.items()}
sorted_ym = sorted(me.keys())

print(f"# Universe = {len(COUNTRIES) + len(MACRO)} series, {len(all_dates_global)} common daily obs")
print(f"# FACTOR_SET 고정 = {FACTOR_SET}")
print(f"# Month-ends = {len(sorted_ym)} (2021-05 ~ 2026-05)")
print(f"# Train = 24m (rolling), Test = 1m forward, Refit = 1m\n")

WIN_DAYS = 504  # ≈24 month
TEST_DAYS = 21  # ≈1m


def get_window(end_date, lookback_days):
    idx = all_dates_global.index(end_date)
    if idx < lookback_days:
        return None
    return all_dates_global[idx - lookback_days + 1: idx + 1]


def get_forward_dates(end_date, fwd_days):
    idx = all_dates_global.index(end_date)
    if idx + fwd_days >= len(all_dates_global):
        return None
    return all_dates_global[idx + 1: idx + 1 + fwd_days]


# ============================================================
# H1. Dollar dominance — walk-forward Rank-IC
#     매 월 t : train 24m → dxy_β_i (each country) → test 1m → realized return.
#     Rank-IC = Spearman(-dxy_β, fwd_return) cross-country (β 음수 클수록 USD↓ 시 수익↑).
# ============================================================
print("=" * 70)
print("H1. Dollar dominance walk-forward Rank-IC (factor=DXY only, train=24m, test=1m)")
print("=" * 70)
print(f"{'month_t':<10}{'IC':>10}{'IC>0':>8}{'n_country':>12}")
ic_h1 = []
for ym in sorted_ym:
    end = me[ym]
    train = get_window(end, WIN_DAYS)
    test = get_forward_dates(end, TEST_DAYS)
    if not train or not test:
        continue
    betas = {}
    fwd = {}
    dxy_train = [dly["dxy"][d] for d in train]
    for c in COUNTRIES:
        y = [dly[c][d] for d in train]
        res = beta_univariate(y, dxy_train)
        if res:
            betas[c] = res[0]
        fwd_test = [dly[c][d] for d in test if d in dly[c]]
        if len(fwd_test) > 10:
            fwd[c] = sum(fwd_test)  # cumulative log-return in test window
    common = sorted(set(betas) & set(fwd))
    if len(common) >= 6:
        # IC = Spearman(-β, fwd_return) — β 음수 클수록 fwd↑
        ic = spearman([-betas[c] for c in common], [fwd[c] for c in common])
        if ic is not None:
            ic_h1.append(ic)
            print(f"{ym[0]}-{ym[1]:02d}     {ic:>10.3f}{'+' if ic > 0 else '-':>8}{len(common):>12d}")

if ic_h1:
    print(f"\nH1 summary: mean IC={st.mean(ic_h1):+.4f}, median={st.median(ic_h1):+.4f}, "
          f"std={st.stdev(ic_h1):.4f}, n_months={len(ic_h1)}, IC>0={sum(1 for x in ic_h1 if x > 0) / len(ic_h1):.2%}")
    icir = st.mean(ic_h1) / st.stdev(ic_h1) * math.sqrt(12) if st.stdev(ic_h1) > 0 else None
    print(f"IC-IR (annualized) = {icir:+.3f}" if icir else "")
    pos_t = sum(1 for x in ic_h1 if x > 0)
    print(f"binomial test: {pos_t}/{len(ic_h1)} pos months (random=50%)")

# ============================================================
# H2. Regime amplification — risk-off vs risk-on β 분리, OOS
#     매 월 t: train 24m, daily 별로 risk-on/off (VIX>25) split → dxy↔EM corr 각각 계산.
#     검증: dxy↔EM corr (risk-off) < dxy↔EM corr (risk-on) (음수 더 강함) 통계 유의.
# ============================================================
print("\n" + "=" * 70)
print("H2. Regime amplification — train 24m 의 risk-off vs risk-on DXY↔EM corr 차이 (OOS 시점별 검증)")
print("=" * 70)
print(f"{'month_t':<10}{'corr_off':>10}{'corr_on':>10}{'n_off':>8}{'n_on':>8}{'amplified':>12}")
diffs_h2 = []
for ym in sorted_ym[::6]:  # 6m 간격으로 출력 압축 (전체 다는 ic_h1 처럼 누적)
    end = me[ym]
    train = get_window(end, WIN_DAYS)
    if not train:
        continue
    dxy_r = [dly["dxy"][d] for d in train]
    em_r = [dly["em_broad"][d] for d in train]
    vix_r = [prices["vix"][d] for d in train]
    off_idx = [i for i, v in enumerate(vix_r) if v > 25]
    on_idx = [i for i, v in enumerate(vix_r) if v <= 25]
    if len(off_idx) < 15 or len(on_idx) < 15:
        continue
    dxy_off = [dxy_r[i] for i in off_idx]
    em_off = [em_r[i] for i in off_idx]
    dxy_on = [dxy_r[i] for i in on_idx]
    em_on = [em_r[i] for i in on_idx]
    res_off = beta_univariate(em_off, dxy_off)
    res_on = beta_univariate(em_on, dxy_on)
    if res_off and res_on:
        # corr ≈ β_yx * std(x)/std(y), simplified to direct pearson
        def pearson(xs, ys):
            mx, my = st.mean(xs), st.mean(ys)
            num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
            dx = math.sqrt(sum((a - mx) ** 2 for a in xs))
            dy = math.sqrt(sum((b - my) ** 2 for b in ys))
            return num / (dx * dy) if dx > 0 and dy > 0 else None

        c_off = pearson(dxy_off, em_off)
        c_on = pearson(dxy_on, em_on)
        amp = (c_off is not None and c_on is not None and c_off < c_on)  # 음수 더 강함
        diffs_h2.append((c_off, c_on))
        print(f"{ym[0]}-{ym[1]:02d}     {c_off:>+10.3f}{c_on:>+10.3f}{len(off_idx):>8d}{len(on_idx):>8d}{'✓' if amp else '✗':>12}")

if diffs_h2:
    off_avg = st.mean([d[0] for d in diffs_h2])
    on_avg = st.mean([d[1] for d in diffs_h2])
    print(f"\nH2 summary: train-window risk-off mean corr = {off_avg:+.3f}, risk-on = {on_avg:+.3f}, "
          f"diff = {off_avg - on_avg:+.3f} (negative = amplification)")
    amp_ratio = sum(1 for c_off, c_on in diffs_h2 if c_off < c_on) / len(diffs_h2)
    print(f"amplification frequency: {amp_ratio:.1%} of windows")

# ============================================================
# H5 (재정의). China idio dominance — MCHI multi-R² 강한 OOS 측정
#     factor set 고정 = DXY + VIX + SPY. 매월 t train 24m, R² 측정.
#     검증: MCHI_R² < EMXC_R² 가 OOS 시점별 일관 유지.
# ============================================================
print("\n" + "=" * 70)
print("H5 (재정의). China idio dominance — MCHI vs EMXC multi-R² (factor=DXY+VIX+SPY 고정)")
print("=" * 70)
print(f"{'month_t':<10}{'MCHI_R²':>10}{'EMXC_R²':>10}{'diff':>10}{'flag':>8}")
mchi_r2s = []
emxc_r2s = []
for ym in sorted_ym:
    end = me[ym]
    train = get_window(end, WIN_DAYS)
    if not train:
        continue
    x_dicts = [dly[f] for f in FACTOR_SET]
    res_mchi = multi_r2(dly["msci_china"], x_dicts, train)
    res_emxc = multi_r2(dly["em_ex_china"], x_dicts, train)
    if res_mchi and res_emxc:
        m_r2 = res_mchi[0]
        e_r2 = res_emxc[0]
        mchi_r2s.append(m_r2)
        emxc_r2s.append(e_r2)
        diff = e_r2 - m_r2  # 양수 = EMXC > MCHI (가설 지지)
        flag = "✓" if diff > 0.15 else ("△" if diff > 0 else "✗")
        # 6m 간격으로만 print (가독성)
        if sorted_ym.index(ym) % 6 == 0:
            print(f"{ym[0]}-{ym[1]:02d}     {m_r2:>10.3f}{e_r2:>10.3f}{diff:>+10.3f}{flag:>8}")

if mchi_r2s and emxc_r2s:
    print(f"\nH5 summary: MCHI R² mean={st.mean(mchi_r2s):.3f} (min={min(mchi_r2s):.3f}, max={max(mchi_r2s):.3f})")
    print(f"            EMXC R² mean={st.mean(emxc_r2s):.3f} (min={min(emxc_r2s):.3f}, max={max(emxc_r2s):.3f})")
    print(f"            mean diff (EMXC-MCHI) = {st.mean(emxc_r2s) - st.mean(mchi_r2s):+.3f}")
    consistent = sum(1 for m, e in zip(mchi_r2s, emxc_r2s) if e > m) / len(mchi_r2s)
    print(f"            consistency: EMXC>MCHI in {consistent:.1%} of windows (OOS)")
    strong = sum(1 for m, e in zip(mchi_r2s, emxc_r2s) if e - m > 0.15) / len(mchi_r2s)
    print(f"            strong (diff>0.15): {strong:.1%} of windows")

# ============================================================
# H7. TSM self-momentum (Moskowitz-Ooi-Pedersen 2012 country adapt)
#     매월 t : 각 국가 ETF 의 [t-12, t-1] cum log-return = momentum.
#     test = t+1 의 sign hit rate.
# ============================================================
print("\n" + "=" * 70)
print("H7. TSM self-momentum hit rate — 각 국가 ETF 12m self-return → 다음 1m sign hit")
print("=" * 70)


def monthly_ret_dict(prices_dict):
    by_ym = defaultdict(list)
    for d, p in prices_dict.items():
        by_ym[(d.year, d.month)].append((d, p))
    mep = {ym: sorted(lst)[-1][1] for ym, lst in by_ym.items()}
    months = sorted(mep.keys())
    out = {}
    for i in range(1, len(months)):
        if mep[months[i - 1]] > 0 and mep[months[i]] > 0:
            out[months[i]] = math.log(mep[months[i]] / mep[months[i - 1]])
    return out


mly = {c: monthly_ret_dict(prices[c]) for c in COUNTRIES + ["msci_china", "em_ex_china"]}
print(f"{'country':<14}{'hit_rate':>10}{'n':>6}{'mom_mean':>12}{'next_mean':>12}")
for c in COUNTRIES + ["msci_china", "em_ex_china"]:
    cm = mly[c]
    months = sorted(cm.keys())
    hits = 0
    tot = 0
    moms = []
    nexts = []
    for i in range(12, len(months) - 1):
        window = months[i - 12: i]  # past 12m exclude current
        if not all(m in cm for m in window):
            continue
        mom = sum(cm[m] for m in window)
        nxt = cm[months[i + 1]] if months[i + 1] in cm else None
        if nxt is None:
            continue
        tot += 1
        moms.append(mom)
        nexts.append(nxt)
        if (mom > 0 and nxt > 0) or (mom < 0 and nxt < 0):
            hits += 1
    if tot > 0:
        print(f"{c:<14}{hits/tot:>10.2%}{tot:>6d}{st.mean(moms) if moms else 0:>+12.4f}{st.mean(nexts) if nexts else 0:>+12.4f}")

print("\n# Done.")
