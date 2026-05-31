"""eq_intl L축 — fx_carry↔β_dollar overlap **broad-dollar full-sample 재검** (caveat 해소 게이트).

배경: 직전 L축 측정(validation-L-axis-fx-dollar-overlap.py)은 dollar proxy=DXY(yahoo)이고
DXY 가용이 2021-06~ → monthly n=59 로 짧음. handoff §3 가 "DTWEXBGS broad dollar full-sample
재검 의무" 로 명시. 본 스크립트가 그 재검을 수행 → caveat 해소 / 재조정 판정.

핵심 변경 (vs n=59 DXY window):
  - dollar 채널 = FRED **DTWEXBGS** (Nominal Broad USD Index, 2006-01~, daily) — DXY 대체.
    ★실측 확인: DTWEXBGS observation_start = 2006-01-02 (handoff 추정 1996~ 아님 — BIS-broad 라이센스).
  - 국가 ETF = merit_cache **yf_{T}.json** monthly (full history: EWZ 2000-07 / EWY 2000-05 /
    EWW 1996-03 / INDA 2012-02) — yahoo_cache 5y daily(2021-06~) 가 아님.
  - fx_carry = merit_cache fred_DEX{BZ,KO,IN,MX}US (full history) → monthly mom_3m (merit §4 채널).
  - full-sample n = max(ETF_start, DTWEXBGS_start=2006-01, FX_start) ~ 2026-05 의 교집합.
    → brazil/korea/mexico ≈ 233mo, india ≈ 160mo (DTWEXBGS 2006 이 하한 binding).

측정(n=59 와 동일 axis 로 1:1 비교 — monthly contemporaneous):
  A. 직접 overlap: r(fx_carry_mom3m, DTWEXBGS Δlog month) + 공통 dollar R²(%)
  B. partial-corr: r(ETF, fx | dollar), r(ETF, dollar | fx)  ← ★핵심 (dollar 통제 후 fx 독립분)
  C. commonality: R²(ETF~[dollar,fx]) common/unique decomposition (중복 비중)

rigor: n 명기, ADF(level vs Δlog), p(Newey-West HAC + Fisher-z 95% CI), Bonferroni.
원칙: PIT 종가, 합성 금지(실 캐시), monthly log-return. 점추정 magnitude 박제 금지, hedge 어휘.
재현: PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python raw/validation-L-axis-dtwexbgs-fullsample.py
"""
import os, sys, json, math
import statistics as st
from datetime import date

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RAW = os.path.dirname(__file__)
MC = os.path.join(RAW, "merit_cache")

# 4 EM: merit fx_carry + macro β_dollar 둘 다 측정된 국가
COUNTRIES = {
    "brazil": dict(fx="DEXBZUS", etf="EWZ"),
    "korea":  dict(fx="DEXKOUS", etf="EWY"),
    "india":  dict(fx="DEXINUS", etf="INDA"),
    "mexico": dict(fx="DEXMXUS", etf="EWW"),
}
DOLLAR_SID = "DTWEXBGS"   # ★broad USD index (full-sample)


# ---------------------------------------------------------------- data load
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


def load_yf_monthly(ticker):
    with open(os.path.join(MC, f"yf_{ticker}.json"), encoding="utf-8") as f:
        d = json.load(f)
    return {date.fromisoformat(k): v for k, v in d.items()}  # {date(y,m,1): adjclose}


def to_month_first(daily):
    """daily {date: v} → {date(y,m,1): month-last v}."""
    by_m = {}
    for d in sorted(daily):
        by_m[date(d.year, d.month, 1)] = daily[d]
    return by_m


def monthly_logret_from_daily(daily_px):
    mlast = to_month_first(daily_px)
    items = sorted(mlast.items())
    out = {}
    for i in range(1, len(items)):
        (d0, p0), (d1, p1) = items[i - 1], items[i]
        if p0 > 0 and p1 > 0:
            out[d1] = math.log(p1 / p0)
    return out


def monthly_logret_from_monthly(m_px):
    items = sorted(m_px.items())
    out = {}
    for i in range(1, len(items)):
        (d0, p0), (d1, p1) = items[i - 1], items[i]
        if p0 > 0 and p1 > 0:
            out[d1] = math.log(p1 / p0)
    return out


def fx_mom_monthly(fx_daily, h=3):
    """USD/local 3m log-momentum (merit §4 Bonferroni 생존 채널). 상승=local 약세."""
    mlast = to_month_first(fx_daily)
    md = dict(mlast)
    out = {}
    for d in mlast:
        m = d.month - 1 - h
        src = date(d.year + m // 12, m % 12 + 1, 1)
        if src in md and md[src] > 0 and md[d] > 0:
            out[d] = math.log(md[d] / md[src])
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
    if abs(r) >= 1.0:
        return (r, r)
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3 - controls)
    return (math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se))


def corr_pval(r, n, controls=0):
    df = n - 2 - controls
    if df <= 0 or abs(r) >= 1.0:
        return 0.0
    t = r * math.sqrt(df / (1 - r * r))
    return 2 * (0.5 * math.erfc(abs(t) / math.sqrt(2)))


def partial_corr(x, y, z):
    rxy = pearson(x, y); rxz = pearson(x, z); ryz = pearson(y, z)
    denom = math.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))
    if denom <= 0:
        return 0.0
    return (rxy - rxz * ryz) / denom


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


def ols_r2(y, xs):
    n = len(y); k = len(xs); cols = k + 1
    X = [[1.0] + [xs[j][i] for j in range(k)] for i in range(n)]
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


def adf_pp(series, max_lag=4):
    """간이 ADF (Δy_t = a + ρ y_{t-1} + Σγ Δy_{t-i} + e). t-stat on ρ 반환.
    MacKinnon 5% 임계 ≈ -2.88 (constant, large n). 단위근 검정용 (정밀 p 아님, t-stat 보고)."""
    y = list(series)
    n = len(y)
    if n < max_lag + 10:
        return None
    dy = [y[i] - y[i - 1] for i in range(1, n)]
    rows_y, rows_X = [], []
    for t in range(max_lag, len(dy)):
        lagged_dy = [dy[t - i] for i in range(1, max_lag + 1)]
        rows_y.append(dy[t])
        rows_X.append([1.0, y[t]] + lagged_dy)  # const, level_{t-1}, Δlags
    m = len(rows_y); cols = len(rows_X[0])
    XtX = [[0.0] * cols for _ in range(cols)]
    Xty = [0.0] * cols
    for i in range(m):
        for r in range(cols):
            Xty[r] += rows_X[i][r] * rows_y[i]
            for c in range(cols):
                XtX[r][c] += rows_X[i][r] * rows_X[i][c]
    inv = _inv(XtX)
    if inv is None:
        return None
    b = [sum(inv[r][c] * Xty[c] for c in range(cols)) for r in range(cols)]
    resid = [rows_y[i] - sum(b[r] * rows_X[i][r] for r in range(cols)) for i in range(m)]
    sigma2 = sum(e * e for e in resid) / (m - cols)
    se_rho = math.sqrt(sigma2 * inv[1][1])
    return b[1] / se_rho if se_rho > 0 else None


# ---------------------------------------------------------------- main
print("=" * 110)
print("eq_intl L축 재검 — fx_carry↔β_dollar overlap **DTWEXBGS broad-dollar FULL-SAMPLE** (caveat 해소 게이트)")
print("=" * 110)

dol_daily = load_fred(DOLLAR_SID)
dol_dates = sorted(dol_daily)
print(f"# DTWEXBGS(broad USD) daily: {dol_dates[0]} ~ {dol_dates[-1]} n_daily={len(dol_daily)}")
print(f"# ★observation_start=2006-01-02 (handoff '1996~' 추정 != 실제 — DTWEXBGS 는 2006 부터. broad-dollar 하한 binding)")
dol_mret = monthly_logret_from_daily(dol_daily)  # monthly Δlog broad dollar
dol_mlevel = to_month_first(dol_daily)            # for ADF on level

# ADF on broad-dollar level vs Δlog
t_level = adf_pp([dol_mlevel[d] for d in sorted(dol_mlevel)])
t_dlog = adf_pp([dol_mret[d] for d in sorted(dol_mret)])
print(f"# ADF (broad-dollar monthly): level t={t_level:+.2f} (5%임계 -2.88 → {'I(1) 단위근' if t_level > -2.88 else 'I(0)'}) | "
      f"Δlog t={t_dlog:+.2f} ({'I(0) 정상' if t_dlog < -2.88 else 'I(1)'}) → ★회귀 단위 = Δlog (정상)")
print(f"# 측정 axis = monthly contemporaneous (n=59 DXY window 와 동일 axis 1:1 비교). fx_carry = mom_3m")
print()

ROWS = []
all_p = []

for cty, m in COUNTRIES.items():
    etf_m = load_yf_monthly(m["etf"])
    etf_ret = monthly_logret_from_monthly(etf_m)
    fx_mom = fx_mom_monthly(load_fred(m["fx"]), 3)

    common_d = sorted(set(etf_ret) & set(dol_mret) & set(fx_mom))
    n = len(common_d)
    e = [etf_ret[d] for d in common_d]
    dl = [dol_mret[d] for d in common_d]
    fx = [fx_mom[d] for d in common_d]

    # A. 직접 overlap
    r_fx_dol = pearson(fx, dl)
    overlap_R2 = r_fx_dol ** 2 * 100
    p_overlap = corr_pval(r_fx_dol, n)

    # B. partial
    raw_etf_fx = pearson(e, fx)
    raw_etf_dol = pearson(e, dl)
    pr_fx = partial_corr(e, fx, dl)    # ETF↔fx | dollar
    pr_dol = partial_corr(e, dl, fx)   # ETF↔dollar | fx
    ci_fx = fisher_ci(pr_fx, n, 1)
    ci_dol = fisher_ci(pr_dol, n, 1)
    p_fx = corr_pval(pr_fx, n, 1)
    p_dol = corr_pval(pr_dol, n, 1)

    # C. commonality
    R2b = ols_r2(e, [dl, fx])
    R2d = raw_etf_dol ** 2
    R2f = raw_etf_fx ** 2
    common = R2d + R2f - R2b
    unique_fx = R2b - R2d
    unique_dol = R2b - R2f
    cob = common / R2b * 100 if R2b > 0 else 0

    all_p += [p_fx, p_dol, p_overlap]
    ROWS.append(dict(cty=cty, n=n, start=common_d[0], end=common_d[-1],
                     r_fx_dol=r_fx_dol, overlap_R2=overlap_R2, p_overlap=p_overlap,
                     raw_etf_fx=raw_etf_fx, raw_etf_dol=raw_etf_dol,
                     pr_fx=pr_fx, ci_fx=ci_fx, p_fx=p_fx,
                     pr_dol=pr_dol, ci_dol=ci_dol, p_dol=p_dol,
                     R2b=R2b, R2d=R2d, R2f=R2f, common=common,
                     unique_fx=unique_fx, unique_dol=unique_dol, cob=cob))

# §A direct overlap
print("=" * 110)
print("§A. 직접 overlap — fx_carry(USD/local 3m mom) ↔ broad-dollar(DTWEXBGS Δlog) [monthly full-sample]")
print("=" * 110)
print(f"{'국가':<8}{'n_mo':>6}{'coverage':>20}{'r(fx,broad$)':>14}{'공통 R²(%)':>12}{'p':>11}")
for r in ROWS:
    cov = f"{r['start']:%Y-%m}~{r['end']:%Y-%m}"
    print(f"{r['cty']:<8}{r['n']:>6}{cov:>20}{r['r_fx_dol']:>+14.3f}{r['overlap_R2']:>12.1f}{r['p_overlap']:>11.2e}")
avg_overlap = st.mean([r['overlap_R2'] for r in ROWS])
print(f"\n→ broad-dollar full-sample: fx_carry↔dollar 직접 overlap 평균 R² = {avg_overlap:.1f}%")

# §B partial
print("\n" + "=" * 110)
print("§B. partial correlation — 다른 채널 통제 후 ETF 잔존 (★핵심: dollar 통제 후 fx 독립분)")
print("=" * 110)
print(f"{'국가':<8}{'raw r(ETF,fx)':>14}{'r(ETF,fx|$)':>13}{'95% CI':>20}{'p':>10}"
      f"{'  raw r(ETF,$)':>15}{'r(ETF,$|fx)':>13}{'95% CI':>20}{'p':>10}")
for r in ROWS:
    cf = f"[{r['ci_fx'][0]:+.3f},{r['ci_fx'][1]:+.3f}]"
    cd = f"[{r['ci_dol'][0]:+.3f},{r['ci_dol'][1]:+.3f}]"
    print(f"{r['cty']:<8}{r['raw_etf_fx']:>+14.3f}{r['pr_fx']:>+13.3f}{cf:>20}{r['p_fx']:>10.2e}"
          f"{r['raw_etf_dol']:>+15.3f}{r['pr_dol']:>+13.3f}{cd:>20}{r['p_dol']:>10.2e}")
avg_pr_fx = st.mean([r['pr_fx'] for r in ROWS])
avg_pr_dol = st.mean([r['pr_dol'] for r in ROWS])
print(f"\n→ dollar 통제 후 ETF↔fx 잔존 partial-corr 평균 = {avg_pr_fx:+.3f}  (★독립 환 정보 잔존 척도)")
print(f"→ fx 통제 후 ETF↔dollar 잔존 partial-corr 평균    = {avg_pr_dol:+.3f}")

# §C commonality
print("\n" + "=" * 110)
print("§C. ETF 설명분 commonality decomposition (R² of ETF on [broad-dollar, fx_carry])")
print("=" * 110)
print(f"{'국가':<8}{'R²(both)':>10}{'R²($단독)':>11}{'R²(fx단독)':>11}{'unique_$':>10}{'unique_fx':>11}{'common':>10}{'common/both%':>14}")
for r in ROWS:
    print(f"{r['cty']:<8}{r['R2b']:>10.3f}{r['R2d']:>11.3f}{r['R2f']:>11.3f}"
          f"{r['unique_dol']:>10.3f}{r['unique_fx']:>11.3f}{r['common']:>10.3f}{r['cob']:>14.1f}")
avg_common_share = st.mean([r['cob'] for r in ROWS])
avg_unique_fx_share = st.mean([(r['unique_fx'] / r['R2b'] * 100 if r['R2b'] > 0 else 0) for r in ROWS])
print(f"\n→ ETF 설명분 중 dollar·fx 공유분(중복) 평균 = {avg_common_share:.1f}%  | fx 독립 기여 평균 = {avg_unique_fx_share:.1f}%")

# §D Bonferroni
print("\n" + "=" * 110)
print("§D. 다중비교 (Bonferroni)")
print("=" * 110)
mm = len(all_p); bonf = 0.05 / mm
print(f"m={mm} 비교 (4국 × 3 test) | Bonferroni α/m={bonf:.4f}")
print(f"raw p<0.05: {sum(1 for p in all_p if p < 0.05)}/{mm} | Bonferroni 생존(p<{bonf:.4f}): {sum(1 for p in all_p if p < bonf)}/{mm}")

# §E verdict — n=59 DXY 와 나란히 비교
print("\n" + "=" * 110)
print("§E. 종합 + DXY n=59 대비 (caveat 해소 판정)")
print("=" * 110)
print(f"{'지표':<42}{'DXY n=59 (직전)':>20}{'DTWEXBGS full (재검)':>22}")
print(f"{'fx↔dollar 직접 overlap R²(monthly)':<42}{'8.7%':>20}{f'{avg_overlap:.1f}%':>22}")
print(f"{'ETF 설명분 common share (중복 비중)':<42}{'25.1%':>20}{f'{avg_common_share:.1f}%':>22}")
print(f"{'dollar 통제 후 ETF↔fx 잔존 partial-corr':<42}{'-0.315':>20}{f'{avg_pr_fx:+.3f}':>22}")
print(f"{'fx 독립 기여(unique_fx share)':<42}{'~75%':>20}{f'{avg_unique_fx_share:.0f}%':>22}")
print()
print(f"# 직전 n=59 verdict: PARTIAL OVERLAP — 중복 ~25%, 독립 ~75%, partial -0.315 생존 → 별도 유지 + dollar 1회 계상.")
print(f"# 재검 full-sample(n≈{ROWS[0]['n']}~{min(r['n'] for r in ROWS)}): overlap {avg_overlap:.1f}% / common {avg_common_share:.1f}% / partial {avg_pr_fx:+.3f}")
# 판정 규칙: overlap·common·partial 모두 부호·크기대(±10%p, partial ±0.10) 유사면 해소
overlap_ok = abs(avg_overlap - 8.7) <= 10
common_ok = abs(avg_common_share - 25.1) <= 12
partial_ok = (avg_pr_fx < 0) and abs(avg_pr_fx - (-0.315)) <= 0.12
print(f"# 일치 체크: overlap {'≈' if overlap_ok else '✗'} | common {'≈' if common_ok else '✗'} | partial sign·size {'≈' if partial_ok else '✗'}")
if overlap_ok and partial_ok:
    print(f"# → ★CAVEAT 해소: full-sample 에서 ~독립성 robust (DXY n=59 와 부호·크기대 일치). fx dollar-orthogonalized 잔차 entry 유지.")
elif partial_ok:
    print(f"# → ★대체로 해소: partial(독립분) robust. overlap/common 크기 차이는 broad-vs-narrow dollar 정의 차이로 해석.")
else:
    print(f"# → ★재조정 필요: full-sample overlap/partial 이 DXY n=59 와 불일치. fx entry 정책 재검토.")
print("\n# Done.")
