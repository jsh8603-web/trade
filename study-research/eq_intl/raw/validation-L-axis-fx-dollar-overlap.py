"""eq_intl L축 선행측정 — fx_carry 환 채널 ↔ macro β_dollar 채널 이중계상 위험 정량화.

게이트(eq_intl merit audit §6.4 미해결 의문): EM fx momentum(Rank-IC −0.43)과 macro-linkage
β_dollar(−1.1~−1.4)는 같은 'dollar/환' 채널 — J축 통합 상관행렬에서 1회 vs 2회 계상?
→ partial correlation 으로 공통 dollar 분산(R²) vs 독립 잔존분 판별.

측정 단위: macro_linkage_v2 가 β_dollar 를 측정한 **daily** window(DXY yahoo_cache 2021-06~)에서
같은 4 국가(brazil/korea/india/mexico) 의 3 변수 동시 정렬:
  (1) ETF daily log-return            (yahoo_cache/{country}.csv)
  (2) dollar 채널 = DXY Δlog          (yahoo_cache/dxy.csv) — β_dollar 와 동일 driver
  (3) fx_carry = USD/local momentum   (FRED DEXxxUS, trailing 63영업일 = 3m log-change.
      merit §4 Bonferroni 생존 채널 = mom_3m. 상승=local 약세)

★측정 3종:
  A. 직접 overlap: corr(fx_carry_mom, DXY Δlog 자체) — 두 driver 가 얼마나 같은 정보?
     + corr(fx_carry_mom, DXY 누적 level-change) — momentum 끼리 비교
  B. partial correlation:
     - r(ETF, fx_carry | dollar) = dollar 통제 후 ETF↔fx_carry 잔존
     - r(ETF, dollar  | fx_carry) = fx_carry 통제 후 ETF↔dollar 잔존
  C. 공통 dollar 분산 R²: ETF~dollar 와 ETF~fx_carry 가 공유하는 설명분.
     = R²(ETF~[dollar,fx]) 의 commonality decomposition (unique_d / unique_fx / common).

원칙: PIT 종가, 합성 금지(실 캐시), daily log-return. n 명기 + p-value + 95% CI(Fisher z) + Bonferroni.
참조 precedent: VIX↔credit R²=2.2%(거의 독립) → 별도 유지. overlap 크면(R² 높음) 1회 계상.
재현: PYTHONUTF8=1 python raw/validation-L-axis-fx-dollar-overlap.py
"""
import os, sys, csv, math, json
import statistics as st
from datetime import date, timedelta

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RAW = os.path.dirname(__file__)
YH = os.path.join(RAW, "yahoo_cache")
MC = os.path.join(RAW, "merit_cache")

# 4 국가: macro-linkage β_dollar + merit fx_carry 둘 다 측정된 EM (brazil/korea/india/mexico)
COUNTRIES = {
    "brazil": "DEXBZUS",
    "korea":  "DEXKOUS",
    "india":  "DEXINUS",
    "mexico": "DEXMXUS",
}


# ---------------------------------------------------------------- data load
def load_csv(alias):
    p = os.path.join(YH, f"{alias}.csv")
    out = {}
    with open(p, encoding="utf-8") as f:
        r = csv.reader(f); next(r)
        for d_str, px in r:
            out[date.fromisoformat(d_str)] = float(px)
    return out


def load_fred(sid):
    with open(os.path.join(MC, f"fred_{sid}.json"), encoding="utf-8") as f:
        raw = json.load(f)
    out = {}
    for o in raw:
        v = o["value"]
        if v in (".", "", None):
            continue
        out[date.fromisoformat(o["date"])] = float(v)
    return out


def log_ret(prices):
    items = sorted(prices.items())
    out = {}
    for i in range(1, len(items)):
        (d0, p0), (d1, p1) = items[i - 1], items[i]
        if p0 > 0 and p1 > 0:
            out[d1] = math.log(p1 / p0)
    return out


def fx_momentum_daily(fx_level, lookback_bd=63):
    """USD/local momentum = log(level_t / level_{t-lookback영업일}). 상승=local 약세.
    FRED DEXxxUS = local per USD → level↑ = USD 강세/local 약세. PIT-safe(가격, 개정 없음 daily)."""
    items = sorted(fx_level.items())
    out = {}
    for i in range(lookback_bd, len(items)):
        d1, p1 = items[i]
        d0, p0 = items[i - lookback_bd]
        if p0 > 0 and p1 > 0:
            out[d1] = math.log(p1 / p0)
    return out


# ---------------------------------------------------------------- stats
def pearson(x, y):
    n = len(x)
    mx, my = st.mean(x), st.mean(y)
    sxy = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    sxx = sum((x[i] - mx) ** 2 for i in range(n))
    syy = sum((y[i] - my) ** 2 for i in range(n))
    if sxx <= 0 or syy <= 0:
        return 0.0
    return sxy / math.sqrt(sxx * syy)


def fisher_ci(r, n, controls=0):
    """Fisher z 95% CI for (partial) correlation. df adj = n - 2 - controls."""
    if abs(r) >= 1.0:
        return (r, r)
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3 - controls)
    lo = math.tanh(z - 1.96 * se)
    hi = math.tanh(z + 1.96 * se)
    return (lo, hi)


def corr_pval(r, n, controls=0):
    """t-test on (partial) correlation. df = n - 2 - controls."""
    df = n - 2 - controls
    if df <= 0 or abs(r) >= 1.0:
        return 0.0
    t = r * math.sqrt(df / (1 - r * r))
    # normal approx (df large) two-sided
    return 2 * (0.5 * math.erfc(abs(t) / math.sqrt(2)))


def partial_corr(x, y, z):
    """partial correlation r(x,y | z) — z 통제 후 x↔y 잔존."""
    rxy = pearson(x, y)
    rxz = pearson(x, z)
    ryz = pearson(y, z)
    denom = math.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))
    if denom <= 0:
        return 0.0, rxy, rxz, ryz
    return (rxy - rxz * ryz) / denom, rxy, rxz, ryz


def ols_r2(y, xs):
    """multiple OLS R² of y on columns xs (list of equal-length lists). intercept incl."""
    n = len(y)
    k = len(xs)
    X = [[1.0] + [xs[j][i] for j in range(k)] for i in range(n)]
    cols = k + 1
    XtX = [[0.0] * cols for _ in range(cols)]
    Xty = [0.0] * cols
    for i in range(n):
        for r in range(cols):
            Xty[r] += X[i][r] * y[i]
            for c in range(cols):
                XtX[r][c] += X[i][r] * X[i][c]
    inv = _inv(XtX)
    if inv is None:
        return 0.0
    b = [sum(inv[r][c] * Xty[c] for c in range(cols)) for r in range(cols)]
    yhat = [sum(b[r] * X[i][r] for r in range(cols)) for i in range(n)]
    my = st.mean(y)
    ssr = sum((y[i] - yhat[i]) ** 2 for i in range(n))
    sst = sum((yi - my) ** 2 for yi in y)
    return 1 - ssr / sst if sst > 0 else 0.0


def _inv(A):
    n = len(A)
    M = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(A)]
    for r in range(n):
        piv = M[r][r]
        if abs(piv) < 1e-14:
            return None
        for c in range(2 * n):
            M[r][c] /= piv
        for rr in range(n):
            if rr != r:
                f = M[rr][r]
                for c in range(2 * n):
                    M[rr][c] -= f * M[r][c]
    return [[M[r][n + c] for c in range(n)] for r in range(n)]


# ---------------------------------------------------------------- main
print("=" * 104)
print("eq_intl L축 선행측정 — fx_carry 환 채널 ↔ macro β_dollar 채널 이중계상 위험 (partial-corr)")
print("=" * 104)

dxy_px = load_csv("dxy")
dxy_dlog = log_ret(dxy_px)  # daily Δlog DXY = macro-linkage dollar driver
# DXY 자체 63bd momentum (level momentum, fx momentum 과 동일 정의로 직접 overlap 비교용)
dxy_mom = fx_momentum_daily(dxy_px, 63)

print(f"# DXY(yahoo) daily Δlog: {sorted(dxy_dlog)[0]} ~ {sorted(dxy_dlog)[-1]} n={len(dxy_dlog)}")
print(f"# 측정 단위 = daily (macro_linkage_v2 β_dollar 와 동일 window). fx_carry = USD/local 63영업일(3m) momentum")
print(f"# Bonferroni: 4국가 × 3 partial-corr test = 12 → α=0.05/12=4.17e-3 (|t| 임계 ≈ 2.86)\n")

ROWS = []  # 결과 누적
all_p = []  # Bonferroni 풀

for cty, fxsid in COUNTRIES.items():
    etf_dlog = log_ret(load_csv(cty))
    fx_level = load_fred(fxsid)
    fx_mom = fx_momentum_daily(fx_level, 63)

    # 공통 일자 정렬 (3 변수 모두 존재)
    common = sorted(set(etf_dlog) & set(dxy_dlog) & set(fx_mom) & set(dxy_mom))
    n = len(common)
    etf = [etf_dlog[d] for d in common]
    dol = [dxy_dlog[d] for d in common]       # dollar 채널 (Δlog DXY)
    fxm = [fx_mom[d] for d in common]          # fx_carry (USD/local 3m mom)
    dxm = [dxy_mom[d] for d in common]         # DXY 자체 3m mom (직접 overlap 비교)

    # ---- A. 직접 overlap: fx_carry ↔ dollar driver ----
    r_fx_dol_dlog = pearson(fxm, dol)          # fx mom vs daily Δlog DXY (다른 시계)
    r_fx_dol_mom = pearson(fxm, dxm)           # fx mom vs DXY 3m mom (같은 시계 = 핵심 overlap)
    overlap_R2 = r_fx_dol_mom ** 2 * 100        # ★공통 dollar 분산 R²(%)

    # ---- B. partial correlation ----
    # ETF↔fx_carry 의 dollar(Δlog DXY) 통제 후 잔존
    pr_etf_fx, rxy1, _, _ = partial_corr(etf, fxm, dol)
    # ETF↔dollar 의 fx_carry 통제 후 잔존
    pr_etf_dol, rxy2, _, _ = partial_corr(etf, dol, fxm)
    raw_etf_fx = pearson(etf, fxm)
    raw_etf_dol = pearson(etf, dol)

    # ---- C. commonality decomposition (ETF 설명분) ----
    R2_both = ols_r2(etf, [dol, fxm])
    R2_dol = pearson(etf, dol) ** 2
    R2_fx = pearson(etf, fxm) ** 2
    unique_dol = R2_both - R2_fx               # fx 추가분 빼고 dollar 단독 기여
    unique_fx = R2_both - R2_dol               # dollar 추가분 빼고 fx 단독 기여
    common = R2_dol + R2_fx - R2_both          # 두 driver 공유 설명분 (>0 = 중복)

    # CI + p
    ci_fx = fisher_ci(pr_etf_fx, n, controls=1)
    ci_dol = fisher_ci(pr_etf_dol, n, controls=1)
    p_fx = corr_pval(pr_etf_fx, n, controls=1)
    p_dol = corr_pval(pr_etf_dol, n, controls=1)
    p_overlap = corr_pval(r_fx_dol_mom, n)
    all_p += [p_fx, p_dol, p_overlap]

    ROWS.append(dict(
        cty=cty, n=n,
        r_fx_dol_dlog=r_fx_dol_dlog, r_fx_dol_mom=r_fx_dol_mom, overlap_R2=overlap_R2, p_overlap=p_overlap,
        raw_etf_fx=raw_etf_fx, raw_etf_dol=raw_etf_dol,
        pr_etf_fx=pr_etf_fx, ci_fx=ci_fx, p_fx=p_fx,
        pr_etf_dol=pr_etf_dol, ci_dol=ci_dol, p_dol=p_dol,
        R2_both=R2_both, R2_dol=R2_dol, R2_fx=R2_fx,
        unique_dol=unique_dol, unique_fx=unique_fx, common=common,
    ))

# ================= A. 직접 overlap 표 =================
print("=" * 104)
print("§A. 직접 overlap — fx_carry(USD/local 3m mom) ↔ dollar driver")
print("=" * 104)
print(f"{'국가':<8}{'n':>6}{'r(fx, ΔlogDXY)':>16}{'r(fx, DXY 3m mom)':>20}{'공통 dollar R²(%)':>18}{'p(overlap)':>12}")
for r in ROWS:
    print(f"{r['cty']:<8}{r['n']:>6}{r['r_fx_dol_dlog']:>+16.3f}{r['r_fx_dol_mom']:>+20.3f}"
          f"{r['overlap_R2']:>18.1f}{r['p_overlap']:>12.2e}")
avg_overlap = st.mean([r['overlap_R2'] for r in ROWS])
print(f"\n→ fx_carry 와 DXY momentum 의 공통 dollar 분산 평균 R² = {avg_overlap:.1f}%")

# ================= B. partial corr 표 =================
print("\n" + "=" * 104)
print("§B. partial correlation — 다른 채널 통제 후 ETF 와의 잔존 부분상관")
print("=" * 104)
print(f"{'국가':<8}{'raw r(ETF,fx)':>14}{'r(ETF,fx|dol)':>15}{'95% CI':>22}{'p':>10}"
      f"{'  | raw r(ETF,dol)':>18}{'r(ETF,dol|fx)':>15}{'95% CI':>22}{'p':>10}")
for r in ROWS:
    cf = f"[{r['ci_fx'][0]:+.3f},{r['ci_fx'][1]:+.3f}]"
    cd = f"[{r['ci_dol'][0]:+.3f},{r['ci_dol'][1]:+.3f}]"
    print(f"{r['cty']:<8}{r['raw_etf_fx']:>+14.3f}{r['pr_etf_fx']:>+15.3f}{cf:>22}{r['p_fx']:>10.2e}"
          f"{r['raw_etf_dol']:>+18.3f}{r['pr_etf_dol']:>+15.3f}{cd:>22}{r['p_dol']:>10.2e}")

# ================= C. commonality decomposition =================
print("\n" + "=" * 104)
print("§C. ETF 설명분 commonality decomposition (R² of ETF on [dollar, fx_carry])")
print("=" * 104)
print(f"{'국가':<8}{'R²(both)':>10}{'R²(dol단독)':>12}{'R²(fx단독)':>12}{'unique_dol':>12}{'unique_fx':>12}{'common(중복)':>14}{'common/both(%)':>16}")
for r in ROWS:
    cob = r['common'] / r['R2_both'] * 100 if r['R2_both'] > 0 else 0
    print(f"{r['cty']:<8}{r['R2_both']:>10.3f}{r['R2_dol']:>12.3f}{r['R2_fx']:>12.3f}"
          f"{r['unique_dol']:>12.3f}{r['unique_fx']:>12.3f}{r['common']:>14.3f}{cob:>16.1f}")

avg_common_share = st.mean([(r['common'] / r['R2_both'] * 100 if r['R2_both'] > 0 else 0) for r in ROWS])
avg_unique_fx_share = st.mean([(r['unique_fx'] / r['R2_both'] * 100 if r['R2_both'] > 0 else 0) for r in ROWS])

# ================= C2. ★MONTHLY 단위 재측정 (merit Rank-IC −0.43 이 사는 축) =================
# daily 는 ETF return(빠름) vs 3m momentum(느림) 시계 불일치 → fx 기여 과소. merit §4 의 fx
# Bonferroni 생존 채널은 monthly contemporaneous mom_3m. 그 단위에서 dollar 중복 재측정.
def to_month_last(daily):
    by_m = {}
    for d in sorted(daily):
        by_m[date(d.year, d.month, 1)] = daily[d]
    return by_m

def monthly_logret(daily_px):
    mlast = to_month_last(daily_px)
    items = sorted(mlast.items())
    out = {}
    for i in range(1, len(items)):
        (d0, p0), (d1, p1) = items[i - 1], items[i]
        if p0 > 0 and p1 > 0:
            out[d1] = math.log(p1 / p0)
    return out

def fx_mom_monthly(fx_level, h=3):
    mlast = to_month_last(fx_level)  # month-last local/USD level
    items = sorted(mlast.items())
    md = dict(items)
    out = {}
    for d, _ in items:
        m = d.month - 1 - h
        src = date(d.year + m // 12, m % 12 + 1, 1)
        if src in md and md[src] > 0 and md[d] > 0:
            out[d] = math.log(md[d] / md[src])
    return out

print("\n" + "=" * 104)
print("§C2. ★MONTHLY 재측정 — merit fx Rank-IC(−0.43) 가 사는 축 (DXY window 한정, 동일 4국)")
print("=" * 104)
dxy_m_ret = monthly_logret(dxy_px)
MROWS = []
for cty, fxsid in COUNTRIES.items():
    etf_m = monthly_logret(load_csv(cty))
    fxmom_m = fx_mom_monthly(load_fred(fxsid), 3)
    cm = sorted(set(etf_m) & set(dxy_m_ret) & set(fxmom_m))
    nm = len(cm)
    if nm < 20:
        continue
    e = [etf_m[d] for d in cm]; dl = [dxy_m_ret[d] for d in cm]; fx = [fxmom_m[d] for d in cm]
    r_etf_fx = pearson(e, fx); r_etf_dol = pearson(e, dl)
    r_fx_dol = pearson(fx, dl)
    pr_fx, _, _, _ = partial_corr(e, fx, dl)   # ETF↔fx | dollar
    pr_dol, _, _, _ = partial_corr(e, dl, fx)  # ETF↔dollar | fx
    R2b = ols_r2(e, [dl, fx]); R2d = r_etf_dol ** 2; R2f = r_etf_fx ** 2
    common = R2d + R2f - R2b
    MROWS.append(dict(cty=cty, n=nm, r_etf_fx=r_etf_fx, r_etf_dol=r_etf_dol, r_fx_dol=r_fx_dol,
                      pr_fx=pr_fx, pr_dol=pr_dol, R2b=R2b, R2d=R2d, R2f=R2f, common=common,
                      overlap_fxdol_R2=r_fx_dol ** 2 * 100))
print(f"{'국가':<8}{'n_mo':>6}{'r(ETF,fx)':>11}{'r(ETF,dol)':>12}{'r(fx,dol)':>11}{'fx↔dol R²%':>11}"
      f"{'r(ETF,fx|dol)':>15}{'r(ETF,dol|fx)':>15}{'common/both%':>14}")
for r in MROWS:
    cob = r['common'] / r['R2b'] * 100 if r['R2b'] > 0 else 0
    print(f"{r['cty']:<8}{r['n']:>6}{r['r_etf_fx']:>+11.3f}{r['r_etf_dol']:>+12.3f}{r['r_fx_dol']:>+11.3f}"
          f"{r['overlap_fxdol_R2']:>11.1f}{r['pr_fx']:>+15.3f}{r['pr_dol']:>+15.3f}{cob:>14.1f}")
if MROWS:
    avg_m_overlap = st.mean([r['overlap_fxdol_R2'] for r in MROWS])
    avg_m_common = st.mean([(r['common'] / r['R2b'] * 100 if r['R2b'] > 0 else 0) for r in MROWS])
    avg_m_pr_fx = st.mean([r['pr_fx'] for r in MROWS])
    print(f"\n→ MONTHLY: fx↔dol 직접 overlap 평균 R²={avg_m_overlap:.1f}% | ETF설명분 common share 평균={avg_m_common:.1f}%")
    print(f"→ MONTHLY: dollar 통제 후 ETF↔fx 잔존 partial-corr 평균={avg_m_pr_fx:+.3f} (★독립 기여 잔존 여부)")
    print(f"  ★주의: DXY window(2021-06~) 한정 monthly n≈{MROWS[0]['n']} (작음). merit 의 full-sample n=309~362 와 별개.")

# ================= Bonferroni =================
print("\n" + "=" * 104)
print("§D. 다중비교 (Bonferroni)")
print("=" * 104)
m = len(all_p)
bonf = 0.05 / m
print(f"m={m} 비교 (4국가 × 3 test) | Bonferroni α/m={bonf:.4f}")
print(f"raw p<0.05: {sum(1 for p in all_p if p < 0.05)}/{m} | Bonferroni 생존(p<{bonf:.4f}): {sum(1 for p in all_p if p < bonf)}/{m}")

# ================= 종합 =================
print("\n" + "=" * 104)
print("§E. 종합 판정")
print("=" * 104)
print(f"평균 직접 overlap R² (fx_carry ↔ DXY mom)       = {avg_overlap:.1f}%")
print(f"평균 common share (ETF 설명분 중 dollar/fx 중복) = {avg_common_share:.1f}%")
print(f"평균 unique_fx share (fx 독립 기여)              = {avg_unique_fx_share:.1f}%")
print(f"\n# precedent: VIX↔credit R²=2.2% → 거의 독립 → 별도 유지.")
print(f"# 본 측정 overlap R² = {avg_overlap:.1f}% → ", end="")
if avg_overlap >= 30:
    print("높음 → fx_carry 와 β_dollar 는 같은 dollar 정보 → ★1회 계상(택1/합성) 권고")
elif avg_overlap >= 10:
    print("중간 → 상당 중복 but 독립분 존재 → 합성 또는 partial 후 잔차 유지 검토")
else:
    print("낮음 → 대체로 독립 → 별도 유지 가능")
print("\n# Done.")
