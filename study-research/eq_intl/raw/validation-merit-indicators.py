"""eq_intl merit-indicator 실데이터 탐구 (block6 collector_plan 4 지표).

목표: yaml block6 에 "검토만 되고 미탐구" 로 박힌 4 merit 지표를 실데이터로
fetch → 변환(spec↔code 1:1) → contemporaneous + lead-lag 상관/Spearman Rank-IC
→ Newey-West HAC t/p + 95% CI + Bonferroni/BH-FDR → half-split OOS 부호 일치.

4 지표:
  (1) JGB-UST carry/spread:  FRED IRLTLT01JPM156N (JP 10Y, M) − DGS10 (US 10Y, D→M)
                              vs EWJ(japan) 월간 log-return.
  (2) terms_of_trade / REER:  FRED BIS Real Broad EER (RBBRBIS brazil / RBMXBIS mexico /
                              RBINBIS india / RBCNBIS china) vs 해당국 ETF.
  (3) China credit impulse:  FRED QCNPAMUSDA (Total Credit to Private Non-Fin Sector, Q)
                              → credit impulse = YoY-of-YoY (2차 차분 표준 정의) vs FXI(china)
                              + lead-lag (credit lead k=1/2 분기).
  (4) fx_carry_momentum:      FRED FX (DEXxxUS) 금리차(carry, JP/US 10Y) + 환율 모멘텀(3-12m)
                              vs 해당국 ETF.

원칙: PIT 종가, OOS half-split, 합성 금지 (fetch 실패 시 raise). 월간 log-return.
변환·ADF·HAC·Bonferroni 전부 박제. 점추정 prior 박제 금지 — sign/direction prior + CI.

산출: raw/validation-merit-eq_intl-20260601.md
재현: PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python raw/validation-merit-indicators.py
"""
import os, sys, math, json, time
import statistics as st
from datetime import date

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import requests
from dotenv import load_dotenv

load_dotenv("D:/projects/Inv/.env")
FRED_KEY = os.environ["FRED_API_KEY"]
CACHE = os.path.join(os.path.dirname(__file__), "merit_cache")
os.makedirs(CACHE, exist_ok=True)


# =========================================================================
# 데이터 fetch (FRED + yfinance) — 캐시
# =========================================================================
def fred_series(sid):
    """FRED observations → {date: value}. PIT first-release 아님(revised) 주의 — caveat 박제."""
    cf = os.path.join(CACHE, f"fred_{sid}.json")
    if os.path.exists(cf):
        with open(cf, encoding="utf-8") as f:
            raw = json.load(f)
    else:
        raw = None
        for _ in range(6):
            r = requests.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params=dict(series_id=sid, api_key=FRED_KEY, file_type="json"),
                timeout=40,
            )
            if r.status_code == 429:
                time.sleep(4)
                continue
            r.raise_for_status()
            raw = r.json()["observations"]
            break
        if raw is None:
            raise RuntimeError(f"FRED fetch failed (rate-limited): {sid}")
        with open(cf, "w", encoding="utf-8") as f:
            json.dump(raw, f)
        time.sleep(1.0)
    out = {}
    for o in raw:
        v = o["value"]
        if v in (".", "", None):
            continue
        out[date.fromisoformat(o["date"])] = float(v)
    if not out:
        raise RuntimeError(f"FRED series empty: {sid}")
    return out


def yf_monthly(ticker):
    """yfinance monthly adj-close (TR). {date(year,month,1): price}."""
    cf = os.path.join(CACHE, f"yf_{ticker}.json")
    if os.path.exists(cf):
        with open(cf, encoding="utf-8") as f:
            d = json.load(f)
        return {date.fromisoformat(k): v for k, v in d.items()}
    import yfinance as yf
    h = yf.Ticker(ticker).history(period="max", interval="1mo", auto_adjust=True)
    if h is None or len(h) == 0:
        raise RuntimeError(f"yfinance empty: {ticker}")
    out = {}
    for ts, row in h.iterrows():
        px = float(row["Close"])
        if px > 0 and px == px:
            out[date(ts.year, ts.month, 1)] = px
    with open(cf, "w", encoding="utf-8") as f:
        json.dump({k.isoformat(): v for k, v in out.items()}, f)
    return out


def to_month(d):
    return date(d.year, d.month, 1)


def daily_to_monthly_last(series):
    """daily {date:val} → monthly {month_start: last obs of month}."""
    by_m = {}
    for d in sorted(series):
        by_m[to_month(d)] = series[d]  # last write wins = month-end-ish
    return by_m


def monthly_to_quarter_last(series):
    out = {}
    for d in sorted(series):
        q = date(d.year, ((d.month - 1) // 3) * 3 + 1, 1)
        out[q] = series[d]
    return out


# =========================================================================
# 통계 유틸 — Newey-West HAC, Spearman, ADF, OLS, Bonferroni
# =========================================================================
def norm_sf(z):
    return 0.5 * math.erfc(abs(z) / math.sqrt(2))


def two_sided_p(z):
    return 2 * norm_sf(abs(z))


def nw_bandwidth(n):
    return int(math.floor(4 * (n / 100.0) ** (2.0 / 9.0)))


def ols_hac(y, x):
    """단일 회귀 y = a + b·x + e, Newey-West HAC SE(b). return dict."""
    n = len(y)
    if n < 12:
        return None
    mx, my = st.mean(x), st.mean(y)
    sxx = sum((xi - mx) ** 2 for xi in x)
    if sxx <= 0:
        return None
    b = sum((x[i] - mx) * (y[i] - my) for i in range(n)) / sxx
    a = my - b * mx
    resid = [y[i] - a - b * x[i] for i in range(n)]
    xc = [x[i] - mx for i in range(n)]
    # HAC meat = Σ w_l Σ (xc_t e_t)(xc_{t-l} e_{t-l})
    L = nw_bandwidth(n)
    g = [xc[i] * resid[i] for i in range(n)]
    S = sum(gi * gi for gi in g)
    for l in range(1, L + 1):
        w = 1.0 - l / (L + 1.0)
        cov = sum(g[t] * g[t - l] for t in range(l, n))
        S += 2.0 * w * cov
    var_b = S / (sxx ** 2)
    se = math.sqrt(var_b) if var_b > 0 else float("nan")
    t = b / se if se and se == se and se > 0 else 0.0
    yhat = [a + b * x[i] for i in range(n)]
    sst = sum((yi - my) ** 2 for yi in y)
    ssr = sum((y[i] - yhat[i]) ** 2 for i in range(n))
    r2 = 1 - ssr / sst if sst > 0 else 0.0
    return {"a": a, "b": b, "se": se, "t": t, "p": two_sided_p(t),
            "ci": (b - 1.96 * se, b + 1.96 * se), "r2": r2, "n": n, "L": L}


def rank(vals):
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    r = [0.0] * len(vals)
    i = 0
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def spearman(x, y):
    """Spearman rho + HAC t (Pearson on ranks, HAC SE)."""
    rx, ry = rank(x), rank(y)
    res = ols_hac(ry, rx)
    n = len(x)
    mrx, mry = st.mean(rx), st.mean(ry)
    num = sum((rx[i] - mrx) * (ry[i] - mry) for i in range(n))
    dx = math.sqrt(sum((rx[i] - mrx) ** 2 for i in range(n)))
    dy = math.sqrt(sum((ry[i] - mry) ** 2 for i in range(n)))
    rho = num / (dx * dy) if dx > 0 and dy > 0 else 0.0
    # HAC t via rank-regression slope significance
    t = res["t"] if res else 0.0
    return rho, t, two_sided_p(t), n


def adf(series_vals, max_lag=4):
    """간이 ADF (constant, fixed lag). Δy_t = a + ρ y_{t-1} + Σφ_j Δy_{t-j} + e.
    return (t_rho, n_used). t < -2.86 (5%) → I(0). 근사 critical (MacKinnon ~ -2.86).
    """
    y = series_vals
    n = len(y)
    if n < 20:
        return None
    dy = [y[i] - y[i - 1] for i in range(1, n)]
    lag = min(max_lag, max(1, n // 15))
    start = lag
    rows_y, rows_X = [], []
    for t in range(start, len(dy)):
        depvar = dy[t]
        lvl = y[t]  # y_{t-1} aligned (dy[t] uses y[t+1]-y[t]); align level = y[t]
        feats = [1.0, lvl] + [dy[t - j] for j in range(1, lag + 1)]
        rows_y.append(depvar)
        rows_X.append(feats)
    k = len(rows_X[0])
    m = len(rows_y)
    if m < k + 5:
        return None
    # normal equations
    XtX = [[0.0] * k for _ in range(k)]
    Xty = [0.0] * k
    for i in range(m):
        for a in range(k):
            Xty[a] += rows_X[i][a] * rows_y[i]
            for b in range(k):
                XtX[a][b] += rows_X[i][a] * rows_X[i][b]
    inv = _inv(XtX)
    if inv is None:
        return None
    beta = [sum(inv[a][c] * Xty[c] for c in range(k)) for a in range(k)]
    resid = [rows_y[i] - sum(beta[a] * rows_X[i][a] for a in range(k)) for i in range(m)]
    s2 = sum(e * e for e in resid) / (m - k)
    se_rho = math.sqrt(s2 * inv[1][1]) if inv[1][1] > 0 else float("nan")
    t_rho = beta[1] / se_rho if se_rho and se_rho == se_rho and se_rho > 0 else 0.0
    return t_rho, m


def _inv(A):
    n = len(A)
    M = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(A)]
    for r in range(n):
        piv = M[r][r]
        if abs(piv) < 1e-13:
            return None
        for c in range(2 * n):
            M[r][c] /= piv
        for rr in range(n):
            if rr != r:
                f = M[rr][r]
                for c in range(2 * n):
                    M[rr][c] -= f * M[r][c]
    return [[M[r][n + c] for c in range(n)] for r in range(n)]


def log_ret_monthly(prices):
    items = sorted(prices.items())
    out = {}
    for i in range(1, len(items)):
        (d0, p0), (d1, p1) = items[i - 1], items[i]
        if p0 > 0 and p1 > 0:
            out[d1] = math.log(p1 / p0)
    return out


def yoy(monthly, lag_m=12):
    items = sorted(monthly.items())
    dd = {d: v for d, v in items}
    out = {}
    for d, v in items:
        prev = date(d.year - 1, d.month, 1)
        if prev in dd and dd[prev] != 0:
            out[d] = (v - dd[prev]) / abs(dd[prev]) * 100.0
    return out


def zscore_roll(monthly, win=36):
    items = sorted(monthly.items())
    out = {}
    for i in range(len(items)):
        lo = max(0, i - win + 1)
        window = [items[j][1] for j in range(lo, i + 1)]
        if len(window) >= 12:
            mu = st.mean(window)
            sd = st.pstdev(window)
            if sd > 0:
                out[items[i][0]] = (items[i][1] - mu) / sd
    return out


def align(a, b):
    keys = sorted(set(a) & set(b))
    return keys, [a[k] for k in keys], [b[k] for k in keys]


def lead_lag(driver_m, ret_m, lags):
    """driver leads return by k months: corr(driver_t, ret_{t+k}).
    return list of (k, rho, t, p, n)."""
    out = []
    ret_by = ret_m
    for k in lags:
        # shift driver forward: pair driver[d] with ret[d + k months]
        pairs_d, pairs_r = [], []
        for d in sorted(driver_m):
            tgt = _add_months(d, k)
            if tgt in ret_by:
                pairs_d.append(driver_m[d])
                pairs_r.append(ret_by[tgt])
        if len(pairs_d) >= 20:
            rho, t, p, n = spearman(pairs_d, pairs_r)
            out.append((k, rho, t, p, n))
    return out


def _add_months(d, k):
    m = d.month - 1 + k
    return date(d.year + m // 12, m % 12 + 1, 1)


def half_split_sign(driver_m, ret_m, transform_label):
    """half-split OOS: 전반/후반 각각 Spearman rho 부호 일치 여부."""
    keys, xv, yv = align(driver_m, ret_m)
    n = len(keys)
    if n < 40:
        return None
    mid = n // 2
    rho1, _, _, _ = spearman(xv[:mid], yv[:mid])
    rho2, _, _, _ = spearman(xv[mid:], yv[mid:])
    return rho1, rho2, (math.copysign(1, rho1) == math.copysign(1, rho2)), keys[0], keys[mid], keys[-1]


# =========================================================================
# MAIN
# =========================================================================
print("=" * 100)
print("eq_intl MERIT-INDICATOR 실데이터 탐구 (block6 4 지표) — 2026-06-01")
print("=" * 100)

ETF_T = {"japan": "EWJ", "brazil": "EWZ", "mexico": "EWW", "china": "FXI",
         "india": "INDA", "korea": "EWY", "taiwan": "EWT"}
etf_px = {a: yf_monthly(t) for a, t in ETF_T.items()}
etf_ret = {a: log_ret_monthly(etf_px[a]) for a in ETF_T}
for a in ETF_T:
    ks = sorted(etf_ret[a])
    print(f"  ETF {a:8s} ({ETF_T[a]}): {ks[0]} ~ {ks[-1]}  n_month_ret={len(ks)}")

RESULTS = {}

# -------------------------------------------------------------------------
# 지표 1: JGB-UST spread vs EWJ(japan)
#   spec: JP 10Y − US 10Y 금리차. 엔 carry/디커플 채널. spread↑(JP 상대고금리)
#         → 엔 강세 압력 but 일본 수출주 부담 = 부호 양면 → direction prior 약.
#   transform: spread level → ADF → Δspread (비정상 시). ret = EWJ monthly log-ret.
# -------------------------------------------------------------------------
print("\n" + "=" * 100)
print("§1. JGB-UST spread (FRED IRLTLT01JPM156N − DGS10) vs EWJ(japan) monthly log-return")
print("=" * 100)
jp10 = fred_series("IRLTLT01JPM156N")            # monthly, percent
us10_d = fred_series("DGS10")                     # daily, percent
us10_m = daily_to_monthly_last(us10_d)
jp10_m = {to_month(d): v for d, v in jp10.items()}
spread = {}
for m in sorted(set(jp10_m) & set(us10_m)):
    spread[m] = jp10_m[m] - us10_m[m]            # JP − US (음수 = US 고금리)
sk = sorted(spread)
print(f"  spread coverage: {sk[0]} ~ {sk[-1]}  n={len(sk)}  (JP 10Y monthly, US 10Y daily→month-last)")
adf_sp = adf([spread[k] for k in sk])
print(f"  ADF(spread level): t_rho={adf_sp[0]:+.2f} (n={adf_sp[1]})  "
      f"→ {'I(0) stationary' if adf_sp[0] < -2.86 else 'I(1) 의심 → Δ 차분 강제'}")
# spec↔code: spread 비정상이면 Δspread 사용 (return 단위 정합). EWJ monthly log-ret 와 contemporaneous + lead-lag.
d_spread = {}
ssort = sorted(spread.items())
for i in range(1, len(ssort)):
    d_spread[ssort[i][0]] = ssort[i][1] - ssort[i - 1][1]
use_level = adf_sp[0] < -2.86
drv1 = spread if use_level else d_spread
lbl1 = "spread level" if use_level else "Δspread (1차 차분, ADF I(1) → return 단위 정합)"
print(f"  [spec↔code] driver = {lbl1}; target = EWJ monthly log-return (contemporaneous + lead k).")
keys, xv, yv = align(drv1, etf_ret["japan"])
res = ols_hac(yv, xv)
rho, rt, rp, rn = spearman(xv, yv)
print(f"  contemporaneous: n={res['n']}  β={res['b']:+.5f} HAC-SE={res['se']:.5f} "
      f"t={res['t']:+.2f} p={res['p']:.3f} 95%CI=[{res['ci'][0]:+.5f},{res['ci'][1]:+.5f}] R²={res['r2']:.3f}")
print(f"  Spearman Rank-IC(contemp)={rho:+.3f} HAC-t={rt:+.2f} p={rp:.3f} n={rn}")
ll1 = lead_lag(drv1, etf_ret["japan"], [1, 3, 6])
for k, rh, t, p, n in ll1:
    print(f"  lead-lag k={k}m: Rank-IC={rh:+.3f} HAC-t={t:+.2f} p={p:.3f} n={n}")
hs1 = half_split_sign(drv1, etf_ret["japan"], lbl1)
if hs1:
    print(f"  half-split OOS: rho1={hs1[0]:+.3f} rho2={hs1[1]:+.3f} 부호일치={hs1[2]} "
          f"({hs1[3]}~{hs1[4]} | {hs1[4]}~{hs1[5]})")
RESULTS["jgb_ust"] = {"contemp": res, "rank_ic": (rho, rt, rp, rn),
                      "leadlag": ll1, "halfsplit": hs1, "transform": lbl1, "adf": adf_sp}

# -------------------------------------------------------------------------
# 지표 2: REER (terms-of-trade proxy) vs 해당국 ETF
#   spec: REER 고평가(z↑) → 미래 통화·지수 약세 prior(평균회귀) = 음 direction (장기 valuation).
#   transform: own-history rolling z (36m). target = 향후 ETF return (lead 측정).
#   원자재수출국(brazil/mexico) + 수입국(india) + china 비교.
# -------------------------------------------------------------------------
print("\n" + "=" * 100)
print("§2. REER own-history z (FRED BIS Real Broad EER) vs 해당국 ETF monthly return")
print("=" * 100)
REER = {"brazil": "RBBRBIS", "mexico": "RBMXBIS", "india": "RBINBIS", "china": "RBCNBIS",
        "korea": "RBKRBIS"}
reer_etf = {"brazil": "brazil", "mexico": "mexico", "india": "india", "china": "china",
            "korea": "korea"}
reer_res = {}
print(f"  [spec↔code] driver = REER own-history rolling z(36m); target = 해당국 ETF "
      f"forward monthly log-return (lead k=1/3/6m). prior: z↑(고평가) → 미래 return 음(평균회귀).")
n_tests_reer = 0
for cty, sid in REER.items():
    raw = fred_series(sid)
    rm = {to_month(d): v for d, v in raw.items()}
    adf_lvl = adf([rm[k] for k in sorted(rm)])
    rz = zscore_roll(rm, 36)
    et = reer_etf[cty]
    # contemporaneous (Δlog REER vs ret) + valuation lead (z vs forward ret)
    keys, xv, yv = align(rz, etf_ret[et])
    if len(keys) < 20:
        print(f"  {cty:8s}: n={len(keys)} 부족 → skip")
        continue
    rho, rt, rp, rn = spearman(xv, yv)
    ll = lead_lag(rz, etf_ret[et], [1, 3, 6])
    hs = half_split_sign(rz, etf_ret[et], "REER z")
    adf_str = f"ADF(REER lvl) t={adf_lvl[0]:+.2f}" if adf_lvl else "ADF n/a"
    print(f"  {cty:8s} ({sid}): REER {sorted(rm)[0]}~{sorted(rm)[-1]} n={len(rm)} | {adf_str}")
    print(f"     contemp Rank-IC(z, ret)={rho:+.3f} HAC-t={rt:+.2f} p={rp:.3f} n={rn}")
    for k, rh, t, p, n in ll:
        print(f"     lead k={k}m: Rank-IC={rh:+.3f} HAC-t={t:+.2f} p={p:.3f} n={n}")
        n_tests_reer += 1
    if hs:
        print(f"     half-split: rho1={hs[0]:+.3f} rho2={hs[1]:+.3f} 부호일치={hs[2]}")
    reer_res[cty] = {"contemp": (rho, rt, rp, rn), "leadlag": ll, "halfsplit": hs, "adf": adf_lvl}
RESULTS["reer"] = reer_res
RESULTS["reer_ntests"] = n_tests_reer

# -------------------------------------------------------------------------
# 지표 3: China credit impulse vs FXI(china) + EM 원자재수출국 lead-lag
#   spec: credit impulse(YoY-of-YoY 표준) ↑ → 6-12m lag 로 china/원자재수출국 지수 선행(양).
#   transform: QCNPAMUSDA(Total credit, Q) → YoY% → Δ(YoY) = impulse. lead k=1/2 quarter.
# -------------------------------------------------------------------------
print("\n" + "=" * 100)
print("§3. China credit impulse (FRED QCNPAMUSDA Total Credit, Q) vs FXI(china)/brazil")
print("=" * 100)
credit = fred_series("QCNPAMUSDA")  # quarterly level, USD bn
cm = {to_month(d): v for d, v in credit.items()}
cq = monthly_to_quarter_last(cm)
adf_c = adf([cq[k] for k in sorted(cq)])
# credit impulse = Δ(YoY growth) 표준 정의 (2차)
cyoy = yoy(cq, 12)  # quarter spaced; YoY uses same-month prior year
# proper YoY on quarterly: value vs 4 quarters ago
cqs = sorted(cq.items())
cq_yoy = {}
cdict = dict(cqs)
for d, v in cqs:
    prev = date(d.year - 1, d.month, 1)
    if prev in cdict and cdict[prev] != 0:
        cq_yoy[d] = (v - cdict[prev]) / abs(cdict[prev]) * 100.0
# impulse = Δ(YoY) quarter-over-quarter
cyoy_s = sorted(cq_yoy.items())
impulse = {}
for i in range(1, len(cyoy_s)):
    impulse[cyoy_s[i][0]] = cyoy_s[i][1] - cyoy_s[i - 1][1]
print(f"  credit level coverage: {sorted(cq)[0]} ~ {sorted(cq)[-1]} n_q={len(cq)} "
      f"| ADF(level) t={adf_c[0]:+.2f} → {'I(0)' if adf_c[0]<-2.86 else 'I(1) → YoY/Δ 사용'}")
print(f"  [spec↔code] driver = credit impulse = Δ(YoY% of total credit) (2차 차분, 표준 정의); "
      f"target = FXI(china)/EWZ(brazil) quarterly log-return. prior: impulse↑ → lag 1~2Q 후 지수↑(양).")
# build quarterly ETF returns
def quarter_ret(monthly_px):
    qpx = monthly_to_quarter_last(monthly_px)
    return log_ret_monthly(qpx)  # consecutive quarter log-ret
credit_res = {}
n_tests_credit = 0
for et in ["china", "brazil", "korea"]:
    qr = quarter_ret(etf_px[et])
    # contemporaneous (same quarter)
    keys, xv, yv = align(impulse, qr)
    if len(keys) < 20:
        print(f"  {et}: n={len(keys)} 부족"); continue
    rho, rt, rp, rn = spearman(xv, yv)
    print(f"  {et:8s}: contemp(same Q) Rank-IC={rho:+.3f} HAC-t={rt:+.2f} p={rp:.3f} n={rn}")
    # lead-lag: credit impulse leads ETF by k quarters
    ll = []
    for k in [1, 2, 3, 4]:
        pd_, pr_ = [], []
        for d in sorted(impulse):
            tgt = _add_months(d, 3 * k)
            if tgt in qr:
                pd_.append(impulse[d]); pr_.append(qr[tgt])
        if len(pd_) >= 18:
            rho2, t2, p2, n2 = spearman(pd_, pr_)
            ll.append((k, rho2, t2, p2, n2))
            print(f"     credit leads {k}Q: Rank-IC={rho2:+.3f} HAC-t={t2:+.2f} p={p2:.3f} n={n2}")
            n_tests_credit += 1
    credit_res[et] = {"contemp": (rho, rt, rp, rn), "leadlag": ll}
RESULTS["credit"] = credit_res
RESULTS["credit_adf"] = adf_c
RESULTS["credit_ntests"] = n_tests_credit
RESULTS["credit_impulse_cov"] = (sorted(impulse)[0].isoformat(), sorted(impulse)[-1].isoformat(), len(impulse))

# -------------------------------------------------------------------------
# 지표 4: fx_carry_momentum vs 해당국 ETF
#   spec: carry = 금리차(현지 10Y/policy − US), momentum = 환율 3-12m 추세.
#         carry-favourable(고금리차) + 환 모멘텀(현지통화 강세 추세) → ETF unhedged return 양.
#   여기선 환율 모멘텀 (USD/local 3m·12m log-change) 을 driver 로, 부호: USD↑(local 약세)→ETF 음.
#   FX: DEXJPUS(JPY) / DEXBZUS(BRL) / DEXINUS(INR) / DEXKOUS(KRW) / DEXMXUS(MXN).
# -------------------------------------------------------------------------
print("\n" + "=" * 100)
print("§4. fx_carry_momentum (FRED FX 환율 모멘텀 3/12m) vs 해당국 ETF monthly return")
print("=" * 100)
FX = {"japan": "DEXJPUS", "brazil": "DEXBZUS", "india": "DEXINUS",
      "korea": "DEXKOUS", "mexico": "DEXMXUS"}
print(f"  [spec↔code] driver = FX momentum = log(USD_per_local_t / USD_per_local_{{t-h}}), h=3/12m "
      f"(USD↑=local 약세). target = 해당국 ETF forward monthly log-return. "
      f"prior: USD/local 상승추세(local 약세) → unhedged ETF return 음(환손실).")
fx_res = {}
n_tests_fx = 0
for cty, sid in FX.items():
    fxd = fred_series(sid)  # daily, units = local per USD (DEXxxUS = local/USD)
    fxm = daily_to_monthly_last(fxd)
    fxlog = {d: math.log(v) for d, v in fxm.items() if v > 0}
    adf_fx = adf([fxlog[k] for k in sorted(fxlog)])
    # momentum h-month log-change of (local/USD): 상승 = local 약세
    for h in [3, 12]:
        mom = {}
        fs = sorted(fxlog)
        fdict = dict(fxlog)
        for d in fs:
            src = _add_months(d, -h)
            if src in fdict:
                mom[d] = fxlog[d] - fdict[src]
        et = cty
        # contemporaneous: 같은 달 mom vs ret
        keys, xv, yv = align(mom, etf_ret[et])
        if len(keys) < 20:
            continue
        rho, rt, rp, rn = spearman(xv, yv)
        print(f"  {cty:8s} ({sid}) mom_{h}m: contemp Rank-IC={rho:+.3f} HAC-t={rt:+.2f} "
              f"p={rp:.3f} n={rn} | ADF(logFX) t={adf_fx[0]:+.2f}")
        # lead: FX momentum leads ETF
        ll = lead_lag(mom, etf_ret[et], [1, 3])
        for k, rh, t, p, n in ll:
            print(f"     mom_{h}m leads {k}m: Rank-IC={rh:+.3f} HAC-t={t:+.2f} p={p:.3f} n={n}")
            n_tests_fx += 1
        hs = half_split_sign(mom, etf_ret[et], f"fxmom{h}")
        if hs:
            print(f"     half-split: rho1={hs[0]:+.3f} rho2={hs[1]:+.3f} 부호일치={hs[2]}")
        fx_res[f"{cty}_mom{h}"] = {"contemp": (rho, rt, rp, rn), "leadlag": ll, "halfsplit": hs}
        n_tests_fx += 1
RESULTS["fx"] = fx_res
RESULTS["fx_ntests"] = n_tests_fx

# -------------------------------------------------------------------------
# Bonferroni / BH-FDR 요약
# -------------------------------------------------------------------------
print("\n" + "=" * 100)
print("§5. 다중비교 보정 (Bonferroni + BH-FDR) — 지표별 전체 lead-lag p 풀")
print("=" * 100)


def collect_ps(name):
    ps = []
    if name == "jgb":
        ps.append(("contemp", RESULTS["jgb_ust"]["rank_ic"][2]))
        for k, rh, t, p, n in RESULTS["jgb_ust"]["leadlag"]:
            ps.append((f"lead{k}", p))
    elif name == "reer":
        for cty, r in RESULTS["reer"].items():
            ps.append((f"{cty}-contemp", r["contemp"][2]))
            for k, rh, t, p, n in r["leadlag"]:
                ps.append((f"{cty}-lead{k}", p))
    elif name == "credit":
        for et, r in RESULTS["credit"].items():
            ps.append((f"{et}-contemp", r["contemp"][2]))
            for k, rh, t, p, n in r["leadlag"]:
                ps.append((f"{et}-lead{k}Q", p))
    elif name == "fx":
        for kk, r in RESULTS["fx"].items():
            ps.append((f"{kk}-contemp", r["contemp"][2]))
            for k, rh, t, p, n in r["leadlag"]:
                ps.append((f"{kk}-lead{k}", p))
    return ps


for name in ["jgb", "reer", "credit", "fx"]:
    ps = collect_ps(name)
    m = len(ps)
    if m == 0:
        continue
    alpha = 0.05
    bonf = alpha / m
    survive_b = [(lbl, p) for lbl, p in ps if p < bonf]
    # BH-FDR
    ps_sorted = sorted(ps, key=lambda x: x[1])
    survive_bh = []
    for i, (lbl, p) in enumerate(ps_sorted, 1):
        if p <= (i / m) * alpha:
            survive_bh = ps_sorted[:i]
    print(f"\n[{name}] m={m} 비교 | Bonferroni α/m={bonf:.4f} | "
          f"raw p<0.05: {sum(1 for _, p in ps if p < 0.05)}/{m} | "
          f"Bonferroni 생존: {len(survive_b)}/{m} | BH-FDR 생존: {len(survive_bh)}/{m}")
    if survive_b:
        print(f"   Bonferroni 생존: {[f'{l}(p={p:.4f})' for l, p in survive_b]}")
    elif survive_bh:
        print(f"   BH-FDR 생존: {[f'{l}(p={p:.4f})' for l, p in survive_bh]}")

print("\n# Done. (재현: PYTHONUTF8=1 python raw/validation-merit-indicators.py)")
