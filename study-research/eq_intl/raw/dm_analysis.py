"""eq_intl DM region subagent — regime별 거시민감도 + δ_regime + δ_arch.

원칙: PIT · OOS regime 라벨 · 95% CI 동반 박제 · Bonferroni 표시.
universe: europe, germany, uk, dm_exus, japan + (참고: us_spy).
epochs: Pre-E1(2021-05~2021-12), E1(2022-01~09), E2(2022-10~2023-06),
        E3(2023-07~09), E4(2023-10~2024-12), E5(2025-01~2026-05).
driver: rate=Δlevel(^TNX pp), dollar=Δlog(DXY), oil=Δlog(WTI).
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
    items = sorted(values.items())
    out = {}
    for i in range(1, len(items)):
        out[items[i][0]] = items[i][1] - items[i - 1][1]
    return out


def norm_sf(z):
    return 0.5 * math.erfc(abs(z) / math.sqrt(2))


def two_sided_p(z):
    return 2 * norm_sf(abs(z))


def inv_matrix(A):
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


def ols_full(y_dict, x_dicts, dates):
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
    XtX_inv = inv_matrix(XtX)
    if XtX_inv is None:
        return None
    b = [sum(XtX_inv[r][c] * Xty[c] for c in range(cols)) for r in range(cols)]
    yhat = [sum(b[r] * X[i][r] for r in range(cols)) for i in range(n)]
    my = st.mean(y)
    ss_res = sum((y[i] - yhat[i]) ** 2 for i in range(n))
    ss_tot = sum((y[i] - my) ** 2 for i in range(n))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    sigma2 = ss_res / (n - cols) if n > cols else 0
    se = [math.sqrt(sigma2 * XtX_inv[r][r]) if XtX_inv[r][r] > 0 else 0 for r in range(cols)]
    t = [b[r] / se[r] if se[r] > 0 else 0 for r in range(cols)]
    p = [two_sided_p(t[r]) for r in range(cols)]
    return {"coefs": b, "se": se, "t": t, "p": p, "r2": r2, "n": n, "df": n - cols}


# DM universe
DM = ["europe", "germany", "uk", "dm_exus", "japan"]
EXTRA = ["us_spy"]  # 참고용
ALL_ETFS = DM + EXTRA

prices = {a: to_dict(load(a)) for a in ALL_ETFS + ["dxy", "wti_oil", "tnx_10y_yield"]}
dly = {c: log_ret(prices[c]) for c in ALL_ETFS}
dly["dollar"] = log_ret(prices["dxy"])
dly["oil"] = log_ret(prices["wti_oil"])
dly["rate"] = level_diff(prices["tnx_10y_yield"])

# DM-sleeve-avg: 일자별 5 DM ETF 단순평균 수익률
dm_avg = {}
for d in set.intersection(*[set(dly[c]) for c in DM]):
    dm_avg[d] = sum(dly[c][d] for c in DM) / len(DM)
dly["dm_sleeve_avg"] = dm_avg

# DM archetypes
dm_europe = ["europe", "germany", "uk", "dm_exus"]
dm_japan = ["japan"]

dm_eu_avg = {}
for d in set.intersection(*[set(dly[c]) for c in dm_europe]):
    dm_eu_avg[d] = sum(dly[c][d] for c in dm_europe) / len(dm_europe)
dly["dm_europe_avg"] = dm_eu_avg

dly["dm_japan_avg"] = dly["japan"]  # 단독

# epoch
EPOCHS = [
    ("Pre-E1", date(2021, 5, 1), date(2021, 12, 31)),
    ("E1", date(2022, 1, 1), date(2022, 9, 30)),
    ("E2", date(2022, 10, 1), date(2023, 6, 30)),
    ("E3", date(2023, 7, 1), date(2023, 9, 30)),
    ("E4", date(2023, 10, 1), date(2024, 12, 31)),
    ("E5", date(2025, 1, 1), date(2026, 5, 31)),
]

all_dates_dm = sorted(set.intersection(*[set(dly[c]) for c in DM]) & set(dly["rate"]) & set(dly["dollar"]) & set(dly["oil"]))

print(f"# eq_intl DM region subagent — regime별 거시민감도 + δ_regime/δ_arch")
print(f"# DM universe: {DM}  +  참고: {EXTRA}")
print(f"# n_days (DM 공통 + factor 교집합) = {len(all_dates_dm)}")
print(f"# date range: {all_dates_dm[0]} ~ {all_dates_dm[-1]}")
print(f"# factor set = [Δrate(^TNX pp), Δlog DXY, Δlog WTI]")
print(f"# Bonferroni 75 tests (5 ETF × 3 coef × 5 epoch) → α=0.05/75=6.67e-4 → |t|>3.51 two-sided\n")

# epoch dates 분류
def filter_dates(dates, lo, hi):
    return [d for d in dates if lo <= d <= hi]

# ============================================================
# §1. 전체 5y baseline — 각 DM ETF + sleeve
# ============================================================
print("=" * 120)
print("§1. 전체 5y baseline OLS: y_ETF = α + β_rate·Δrate + β_dollar·Δlog_DXY + β_oil·Δlog_WTI")
print("=" * 120)
hdr = (f"{'ETF':<14}{'β_rate':>10}{'SE':>8}{'95% CI':>22}"
       f"{'β_dollar':>12}{'SE':>8}{'95% CI':>22}"
       f"{'β_oil':>10}{'SE':>8}{'95% CI':>22}{'R²':>7}{'n':>6}")
print(hdr)
baseline = {}
for c in DM + ["dm_sleeve_avg", "us_spy"]:
    dates_c = sorted(set(dly[c]) & set(dly["rate"]) & set(dly["dollar"]) & set(dly["oil"]))
    res = ols_full(dly[c], [dly["rate"], dly["dollar"], dly["oil"]], dates_c)
    if not res:
        continue
    baseline[c] = res
    b, se = res["coefs"], res["se"]
    ci_rate = f"[{b[1]-1.96*se[1]:+.3f},{b[1]+1.96*se[1]:+.3f}]"
    ci_doll = f"[{b[2]-1.96*se[2]:+.3f},{b[2]+1.96*se[2]:+.3f}]"
    ci_oil = f"[{b[3]-1.96*se[3]:+.3f},{b[3]+1.96*se[3]:+.3f}]"
    print(f"{c:<14}"
          f"{b[1]:>+10.4f}{se[1]:>8.4f}{ci_rate:>22}"
          f"{b[2]:>+12.4f}{se[2]:>8.4f}{ci_doll:>22}"
          f"{b[3]:>+10.4f}{se[3]:>8.4f}{ci_oil:>22}"
          f"{res['r2']:>7.3f}{res['n']:>6d}")

# ============================================================
# §2. epoch별 회귀 — 각 DM ETF + sleeve
# ============================================================
print("\n" + "=" * 120)
print("§2. epoch별 multi-OLS — β / SE / 95% CI / |t| / p / R² / n")
print("=" * 120)

epoch_results = {}  # epoch_results[etf][epoch_name] = res
for c in DM + ["dm_sleeve_avg"]:
    epoch_results[c] = {}

bonf_thr_75 = 3.51  # 5×3×5=75

for epoch_name, lo, hi in EPOCHS:
    print(f"\n--- {epoch_name} ({lo} ~ {hi}) ---")
    dates_e = filter_dates(all_dates_dm, lo, hi)
    print(f"n_days = {len(dates_e)}")
    if len(dates_e) < 30:
        print(f"  ⚠ {epoch_name} sample size {len(dates_e)} < 30, skip")
        continue
    print(f"{'ETF':<14}{'β_rate':>10}{'SE':>8}{'95% CI':>22}{'|t|':>6}{'p':>9}"
          f"{'β_dollar':>12}{'SE':>8}{'95% CI':>22}{'|t|':>6}{'p':>9}"
          f"{'β_oil':>10}{'SE':>8}{'95% CI':>22}{'|t|':>6}{'p':>9}{'R²':>7}")
    for c in DM + ["dm_sleeve_avg"]:
        dates_ec = sorted(set(dly[c]) & set(dly["rate"]) & set(dly["dollar"]) & set(dly["oil"]) & set(dates_e))
        res = ols_full(dly[c], [dly["rate"], dly["dollar"], dly["oil"]], dates_ec)
        if not res:
            continue
        epoch_results[c][epoch_name] = res
        b, se, t, p = res["coefs"], res["se"], res["t"], res["p"]
        def ci(j):
            return f"[{b[j]-1.96*se[j]:+.3f},{b[j]+1.96*se[j]:+.3f}]"
        bonf_marker = lambda j: "★" if abs(t[j]) > bonf_thr_75 else ""
        print(f"{c:<14}"
              f"{b[1]:>+10.4f}{se[1]:>8.4f}{ci(1):>22}{abs(t[1]):>6.2f}{p[1]:>9.1e}{bonf_marker(1):<1}"
              f"{b[2]:>+11.4f}{se[2]:>8.4f}{ci(2):>22}{abs(t[2]):>6.2f}{p[2]:>9.1e}{bonf_marker(2):<1}"
              f"{b[3]:>+9.4f}{se[3]:>8.4f}{ci(3):>22}{abs(t[3]):>6.2f}{p[3]:>9.1e}{bonf_marker(3):<1}"
              f"{res['r2']:>7.3f}")

# Bonferroni 생존 카운트
n_total = 0
n_surv = {"rate": 0, "dollar": 0, "oil": 0}
for c in DM:  # sleeve 제외, 개별 ETF만
    for ep_name in [e[0] for e in EPOCHS]:
        if ep_name in epoch_results.get(c, {}):
            res = epoch_results[c][ep_name]
            for j, k in enumerate(["rate", "dollar", "oil"], start=1):
                n_total += 1
                if abs(res["t"][j]) > bonf_thr_75:
                    n_surv[k] += 1

print(f"\n[Bonferroni |t|>{bonf_thr_75} 생존 카운트 — DM 5 ETF × 5 epoch × 3 coef]")
print(f"  β_rate 생존:   {n_surv['rate']:>3d} / {n_total//3}")
print(f"  β_dollar 생존: {n_surv['dollar']:>3d} / {n_total//3}")
print(f"  β_oil 생존:    {n_surv['oil']:>3d} / {n_total//3}")

# ============================================================
# §3. DM archetype 분해 — dm_europe vs dm_japan
# ============================================================
print("\n" + "=" * 120)
print("§3. DM archetype 분해 — dm_europe (europe/germany/uk/dm_exus 평균) vs dm_japan (japan 단독)")
print("=" * 120)

arch_results = {}
for arch_name, arch_y in [("dm_europe", "dm_europe_avg"), ("dm_japan", "dm_japan_avg")]:
    dates_a = sorted(set(dly[arch_y]) & set(dly["rate"]) & set(dly["dollar"]) & set(dly["oil"]))
    res = ols_full(dly[arch_y], [dly["rate"], dly["dollar"], dly["oil"]], dates_a)
    arch_results[arch_name] = res

print(f"\n[전체 5y archetype β]")
print(f"{'archetype':<14}{'β_rate':>10}{'95% CI':>22}{'β_dollar':>12}{'95% CI':>22}{'β_oil':>10}{'95% CI':>22}{'R²':>7}{'n':>6}")
for arch_name in ["dm_europe", "dm_japan"]:
    res = arch_results[arch_name]
    if not res: continue
    b, se = res["coefs"], res["se"]
    def ci(j):
        return f"[{b[j]-1.96*se[j]:+.3f},{b[j]+1.96*se[j]:+.3f}]"
    print(f"{arch_name:<14}{b[1]:>+10.4f}{ci(1):>22}{b[2]:>+12.4f}{ci(2):>22}{b[3]:>+10.4f}{ci(3):>22}{res['r2']:>7.3f}{res['n']:>6d}")

# archetype 차이 (dm_europe - dm_japan)
print(f"\n[archetype diff = β(dm_europe) - β(dm_japan), SE_diff = sqrt(SE_eu² + SE_jp²)]")
print(f"{'coef':<12}{'diff':>10}{'SE_diff':>10}{'t_diff':>8}{'p_diff':>10}{'95% CI':>22}{'verdict':>20}")
for j, k in enumerate(["rate", "dollar", "oil"], start=1):
    b_eu = arch_results["dm_europe"]["coefs"][j]
    se_eu = arch_results["dm_europe"]["se"][j]
    b_jp = arch_results["dm_japan"]["coefs"][j]
    se_jp = arch_results["dm_japan"]["se"][j]
    diff = b_eu - b_jp
    se_diff = math.sqrt(se_eu**2 + se_jp**2)
    t_diff = diff / se_diff if se_diff > 0 else 0
    p_diff = two_sided_p(t_diff)
    ci_diff = f"[{diff-1.96*se_diff:+.3f},{diff+1.96*se_diff:+.3f}]"
    verdict = "★유의" if abs(t_diff) > 1.96 else "n.s."
    print(f"β_{k:<10}{diff:>+10.4f}{se_diff:>10.4f}{t_diff:>+8.2f}{p_diff:>10.2e}{ci_diff:>22}{verdict:>20}")

# ============================================================
# §4. δ_regime 추정 (DM-sleeve-avg) — β(epoch) - β(전체 5y)
# ============================================================
print("\n" + "=" * 120)
print("§4. δ_regime = β(epoch) - β(전체 5y) for DM-sleeve-avg")
print("=" * 120)
print(f"  baseline (전체 5y, DM-sleeve-avg):")
res_base = baseline["dm_sleeve_avg"]
b_base, se_base = res_base["coefs"], res_base["se"]
for j, k in enumerate(["rate", "dollar", "oil"], start=1):
    ci_b = f"[{b_base[j]-1.96*se_base[j]:+.4f},{b_base[j]+1.96*se_base[j]:+.4f}]"
    print(f"    β_{k:<8} = {b_base[j]:+.4f}  SE={se_base[j]:.4f}  95% CI={ci_b}")

print(f"\n  δ_regime by epoch — diff = β(epoch) - β(전체 5y), SE_diff = sqrt(SE_e² + SE_base²)")
print(f"{'epoch':<10}{'coef':<10}{'β(ep)':>10}{'β(base)':>10}{'δ':>10}{'SE_δ':>10}{'t_δ':>8}{'p_δ':>10}{'95% CI(δ)':>22}{'verdict':>15}")
delta_regime = {}  # delta_regime[epoch][coef] = (δ, SE, CI)
for ep_name in [e[0] for e in EPOCHS]:
    if ep_name not in epoch_results.get("dm_sleeve_avg", {}):
        continue
    res_e = epoch_results["dm_sleeve_avg"][ep_name]
    b_e, se_e = res_e["coefs"], res_e["se"]
    delta_regime[ep_name] = {}
    for j, k in enumerate(["rate", "dollar", "oil"], start=1):
        delta = b_e[j] - b_base[j]
        se_delta = math.sqrt(se_e[j]**2 + se_base[j]**2)
        t_d = delta / se_delta if se_delta > 0 else 0
        p_d = two_sided_p(t_d)
        ci_d = f"[{delta-1.96*se_delta:+.4f},{delta+1.96*se_delta:+.4f}]"
        verdict = "★유의" if abs(t_d) > 1.96 else "n.s."
        delta_regime[ep_name][k] = (delta, se_delta, ci_d, t_d, p_d)
        print(f"{ep_name:<10}β_{k:<8}{b_e[j]:>+10.4f}{b_base[j]:>+10.4f}{delta:>+10.4f}{se_delta:>10.4f}{t_d:>+8.2f}{p_d:>10.2e}{ci_d:>22}{verdict:>15}")

# ============================================================
# §5. 누락 critical 지표 caveat (DM 한정)
# ============================================================
print("\n" + "=" * 120)
print("§5. 누락 critical 지표 caveat — DM 분석에 미친 영향")
print("=" * 120)
print("""
[블록6 요청 후보]
1. 美대비 상대 이익모멘텀 (DM forward EPS revision breadth vs US 12m)
   - DM 종목 forward EPS revision 비율(+ - 비) vs SPX 동일
   - 효과: dollar/rate 노이즈 제거 후 DM의 펀더멘털 모멘텀 분리 가능
2. forward PE 갭 (Stoxx 600 forward E/P vs SPX forward E/P)
   - 현 회귀는 valuation 변동 미흡 — 시계열 PE gap regime shift 미반영
3. 금리차/carry (Bund 10Y / Gilt 10Y / JGB 10Y vs UST 10Y)
   - β_rate (UST 만) → DM 자국 금리와의 spread 흡수 못함. japan = JGB-UST gap = USDJPY proxy
4. terms-of-trade (energy 수입국: europe, japan)
   - β_oil 회귀 → 직접 수입가 충격 (TWI-weighted oil import 비중) 미반영

DM region 에서 가장 critical 한 우선순위:
  ★★★ #3 금리차/carry: japan β 추정 시 JGB-UST spread = USDJPY 본질 driver, 미반영 시 β_dollar 의미 모호
  ★★   #4 terms-of-trade: 22년 europe 가스충격 (E1) regime amplification 의 미시 채널
""")

print("\n# Done.")
