"""eq_intl EM region subagent — regime별 macro 민감도 + R² 잔차분산 idio 분해 + DM/EM 차이.

원칙:
  - PIT 종가, OOS regime epoch, 합성 금지 (raw daily log-return)
  - 점추정 박제 금지 (95% CI 동반)
  - Bonferroni multiple-testing 보정
  - ★ EM 약가중 정당화 근거: R² 차이 금지. 잔차분산 σ_idio gap만 사용.

Task A: regime별 EM ETF + EM-sleeve-avg multi-OLS (β / SE / t / p / 95% CI / R²)
Task B: EM archetype (commodity / tech / domestic / em_china / em_broad) β 분해
Task C: ★ R² 잔차분산 분해 — systematic share vs idio share + σ_idio (annualized)
Task D: DM vs EM β_dollar paired diff t-test + idio σ gap
Task E: EM critical 누락 지표 caveat
Task F: md 박제
"""
import os, csv, math, statistics as st, sys
from datetime import date

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
        d0, p0 = items[i - 1]; d1, p1 = items[i]
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
    """OLS — β / SE / t / p / R² / n / df / σ²_resid / σ²_total."""
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
    sigma2 = ss_res / (n - cols)
    sigma2_total = ss_tot / (n - 1)
    se = [math.sqrt(sigma2 * XtX_inv[r][r]) for r in range(cols)]
    t = [b[r] / se[r] if se[r] > 0 else 0 for r in range(cols)]
    p = [two_sided_p(t[r]) for r in range(cols)]
    return {
        "coefs": b, "se": se, "t": t, "p": p, "r2": r2,
        "n": n, "df": n - cols,
        "sigma2_resid": sigma2, "sigma2_total": sigma2_total,
    }


# -------- 데이터 로드 --------
EM = ["em_broad", "brazil", "india", "china", "korea", "taiwan", "mexico", "em_ex_china", "msci_china"]
DM = ["us_spy", "dm_exus", "japan", "germany", "uk", "europe"]
ALL = EM + DM
DRIVERS = ["dxy", "wti_oil", "tnx_10y_yield"]

prices = {a: to_dict(load(a)) for a in ALL + DRIVERS}
dly = {c: log_ret(prices[c]) for c in ALL}
dly["dollar"] = log_ret(prices["dxy"])
dly["oil"] = log_ret(prices["wti_oil"])
dly["rate"] = level_diff(prices["tnx_10y_yield"])

common = sorted(set.intersection(*[set(dly[c]) for c in ALL]) & set(dly["rate"]) & set(dly["dollar"]) & set(dly["oil"]))

print(f"# EM region subagent analysis")
print(f"# data span: {common[0]} ~ {common[-1]}  ({len(common)} days)")
print(f"# EM universe: {EM}")
print(f"# DM universe (for diff): {DM}")
print(f"# factor set: [Δrate(^TNX pp), Δlog DXY, Δlog WTI]\n")

# -------- regime epoch (timeline.md §3 + E5) --------
EPOCHS = [
    ("Pre-E1", date(2021, 5, 1), date(2021, 12, 31)),
    ("E1 긴축충격", date(2022, 1, 1), date(2022, 9, 30)),
    ("E2 전환·반등", date(2022, 10, 1), date(2023, 6, 30)),
    ("E3 금리재상승", date(2023, 7, 1), date(2023, 9, 30)),
    ("E4 pivot·인하", date(2023, 10, 1), date(2024, 12, 31)),
    ("E5 신규", date(2025, 1, 1), date(2026, 5, 30)),
]

epoch_dates = {}
for name, d0, d1 in EPOCHS:
    ds = [d for d in common if d0 <= d <= d1]
    epoch_dates[name] = ds
    print(f"# {name:<18} {d0} ~ {d1}  →  {len(ds)} days")
print()


# ================================================================
# Task A: regime별 EM ETF + EM-sleeve-avg multi-OLS
# ================================================================
print("=" * 130)
print("§A. regime별 EM ETF multi-OLS (β / SE / t / p / 95% CI / R²)")
print("=" * 130)

# EM-sleeve-avg: EM 9개 평균 daily log-return → synthetic
em_sleeve_dly = {}
for d in common:
    em_sleeve_dly[d] = st.mean([dly[c][d] for c in EM])
dly["em_sleeve_avg"] = em_sleeve_dly
EM_PLUS_SLEEVE = EM + ["em_sleeve_avg"]

# DM-sleeve-avg (DM ex-US 평균 — diff test 용)
dm_sleeve_dly = {}
DM_EXUS = ["dm_exus", "japan", "germany", "uk", "europe"]
for d in common:
    dm_sleeve_dly[d] = st.mean([dly[c][d] for c in DM_EXUS])
dly["dm_sleeve_avg"] = dm_sleeve_dly

# Bonferroni: 9 EM ETF × 3 coef × 6 epoch ≈ 162 tests → α=0.05/162≈3.09e-4 → |t|>3.61
# 사용자 spec = 7 ETF × 3 coef × 5 epoch ≈ 105 tests → |t|>3.55. Adopt 사용자 임계.
BONF_THR = 3.55

regime_results = {}  # {epoch: {etf: ols_result}}
for ename, _, _ in EPOCHS:
    ds = epoch_dates[ename]
    regime_results[ename] = {}
    if len(ds) < 30:
        print(f"\n[{ename}] n_days={len(ds)} — too few, skip.")
        continue
    print(f"\n[{ename}]  n_days = {len(ds)}")
    print(f"{'ETF':<14}{'β_rate':>9}{'SE':>7}{'t':>6}{'CI_rate':>22}"
          f"{'β_dollar':>10}{'SE':>7}{'t':>6}{'CI_dollar':>22}"
          f"{'β_oil':>9}{'SE':>7}{'t':>6}{'CI_oil':>22}{'R²':>7}")
    for c in EM_PLUS_SLEEVE:
        res = ols_full(dly[c], [dly["rate"], dly["dollar"], dly["oil"]], ds)
        if not res:
            print(f"{c:<14}  --- n too few ---")
            continue
        regime_results[ename][c] = res
        b, se, t = res["coefs"], res["se"], res["t"]
        ci = lambda j: f"[{b[j]-1.96*se[j]:+.3f},{b[j]+1.96*se[j]:+.3f}]"
        print(f"{c:<14}"
              f"{b[1]:>+9.3f}{se[1]:>7.3f}{t[1]:>+6.2f}{ci(1):>22}"
              f"{b[2]:>+10.3f}{se[2]:>7.3f}{t[2]:>+6.2f}{ci(2):>22}"
              f"{b[3]:>+9.3f}{se[3]:>7.3f}{t[3]:>+6.2f}{ci(3):>22}"
              f"{res['r2']:>7.3f}")

# Bonferroni 생존 카운트 — EM ETF만 (sleeve 제외)
print(f"\n[Bonferroni |t|>{BONF_THR:.2f} 생존 카운트 (EM 9 ETF × 3 coef × 6 epoch)]")
print(f"{'ETF':<14}{'β_rate':>10}{'β_dollar':>10}{'β_oil':>10}")
for c in EM:
    rs = sum(1 for e in regime_results if c in regime_results[e] and abs(regime_results[e][c]["t"][1]) > BONF_THR)
    ds = sum(1 for e in regime_results if c in regime_results[e] and abs(regime_results[e][c]["t"][2]) > BONF_THR)
    os_ = sum(1 for e in regime_results if c in regime_results[e] and abs(regime_results[e][c]["t"][3]) > BONF_THR)
    print(f"{c:<14}{rs:>10}/6{ds:>9}/6{os_:>9}/6")


# ================================================================
# Task B: EM archetype 분해 — 5 archetype 평균 β + 95% CI
# ================================================================
print("\n" + "=" * 130)
print("§B. EM archetype 분해 (full 5y 회귀, archetype 평균 β + 95% CI)")
print("=" * 130)

ARCH = {
    "commodity_exporter": ["brazil", "mexico"],
    "tech_exporter": ["korea", "taiwan"],
    "domestic_demand": ["india"],
    "em_china": ["china", "msci_china"],
    "em_broad_basket": ["em_broad", "em_ex_china"],
}

# full 5y OLS for each EM ETF
full_results = {}
for c in EM + DM_EXUS + ["em_sleeve_avg", "dm_sleeve_avg"]:
    res = ols_full(dly[c], [dly["rate"], dly["dollar"], dly["oil"]], common)
    if res:
        full_results[c] = res

print(f"{'archetype':<24}{'ETFs':<26}{'β_rate (mean)':>16}{'95% CI':>22}"
      f"{'β_dollar (mean)':>18}{'95% CI':>22}{'β_oil (mean)':>15}{'95% CI':>22}")
for arch_name, etfs in ARCH.items():
    valid = [c for c in etfs if c in full_results]
    if not valid:
        continue
    # 평균 β (단순 평균) + 95% CI = mean ± 1.96 · SE_mean
    # SE_mean = sqrt(sum(SE_i²)/k²)  (가정: 잔차 cross-section 독립, 보수적)
    b_rate = [full_results[c]["coefs"][1] for c in valid]
    se_rate = [full_results[c]["se"][1] for c in valid]
    b_doll = [full_results[c]["coefs"][2] for c in valid]
    se_doll = [full_results[c]["se"][2] for c in valid]
    b_oil = [full_results[c]["coefs"][3] for c in valid]
    se_oil = [full_results[c]["se"][3] for c in valid]
    k = len(valid)
    mean_rate = sum(b_rate) / k
    mean_doll = sum(b_doll) / k
    mean_oil = sum(b_oil) / k
    se_mean_rate = math.sqrt(sum(s ** 2 for s in se_rate) / k ** 2)
    se_mean_doll = math.sqrt(sum(s ** 2 for s in se_doll) / k ** 2)
    se_mean_oil = math.sqrt(sum(s ** 2 for s in se_oil) / k ** 2)
    ci_r = f"[{mean_rate-1.96*se_mean_rate:+.3f},{mean_rate+1.96*se_mean_rate:+.3f}]"
    ci_d = f"[{mean_doll-1.96*se_mean_doll:+.3f},{mean_doll+1.96*se_mean_doll:+.3f}]"
    ci_o = f"[{mean_oil-1.96*se_mean_oil:+.3f},{mean_oil+1.96*se_mean_oil:+.3f}]"
    print(f"{arch_name:<24}{','.join(valid):<26}"
          f"{mean_rate:>+16.4f}{ci_r:>22}"
          f"{mean_doll:>+18.4f}{ci_d:>22}"
          f"{mean_oil:>+15.4f}{ci_o:>22}")


# ================================================================
# Task C: ★ R² 잔차분산 분해 — idio share + σ_idio (annualized)
# ================================================================
print("\n" + "=" * 130)
print("§C. ★ R² 잔차분산 분해 — systematic share vs idio share + σ_idio (annualized)")
print("=" * 130)

# DM-sleeve idio σ 기준선 — DM 5개 ETF avg
dm_idio_sigmas = []
em_idio_sigmas = []

# 각 ETF: σ²_total, σ²_resid (= σ²_idio), idio share = σ²_resid / σ²_total · df/(n-1)
# annualization = sqrt(252) · σ_daily
ANN = math.sqrt(252)

print(f"{'ETF':<16}{'R² (sys)':>10}{'idio share':>12}"
      f"{'σ_resid daily':>15}{'σ_idio ann%':>14}"
      f"{'σ_total daily':>15}{'σ_total ann%':>14}{'n':>6}")

table_c = []
for c in EM + DM_EXUS:
    res = full_results.get(c)
    if not res:
        continue
    s2_r = res["sigma2_resid"]
    s2_t = res["sigma2_total"]
    sig_r = math.sqrt(s2_r)
    sig_t = math.sqrt(s2_t)
    # idio share = σ²_resid / σ²_total adjusted to compare with R²
    # systematic share = R² (= 1 - SS_res/SS_tot = 1 - sigma2_resid·df/(sigma2_total·(n-1)))
    sys_share = res["r2"]
    idio_share = 1 - sys_share
    ann_idio = sig_r * ANN * 100  # 단위 %
    ann_tot = sig_t * ANN * 100
    region = "EM" if c in EM else "DM"
    table_c.append((c, region, sys_share, idio_share, sig_r, ann_idio, sig_t, ann_tot, res["n"]))
    print(f"{c:<16}{sys_share:>10.3f}{idio_share:>12.3f}"
          f"{sig_r:>15.5f}{ann_idio:>14.2f}"
          f"{sig_t:>15.5f}{ann_tot:>14.2f}{res['n']:>6}")
    if c in EM:
        em_idio_sigmas.append(ann_idio)
    elif c in DM_EXUS:
        dm_idio_sigmas.append(ann_idio)

em_mean_idio = st.mean(em_idio_sigmas) if em_idio_sigmas else 0
dm_mean_idio = st.mean(dm_idio_sigmas) if dm_idio_sigmas else 0
em_idio_sd = st.stdev(em_idio_sigmas) if len(em_idio_sigmas) > 1 else 0
dm_idio_sd = st.stdev(dm_idio_sigmas) if len(dm_idio_sigmas) > 1 else 0

print(f"\n  EM-sleeve  mean σ_idio ann = {em_mean_idio:.2f}%  (SD = {em_idio_sd:.2f}%, n={len(em_idio_sigmas)})")
print(f"  DM-sleeve  mean σ_idio ann = {dm_mean_idio:.2f}%  (SD = {dm_idio_sd:.2f}%, n={len(dm_idio_sigmas)})")
print(f"  gap (EM - DM) = {em_mean_idio - dm_mean_idio:+.2f}%p")

# ================================================================
# Task D: DM vs EM paired diff (β_dollar) + idio σ gap
# ================================================================
print("\n" + "=" * 130)
print("§D. DM vs EM 상대가중 input")
print("=" * 130)

# EM-sleeve vs DM-sleeve β_dollar (full 5y)
em_sleeve_res = full_results.get("em_sleeve_avg")
dm_sleeve_res = full_results.get("dm_sleeve_avg")

if em_sleeve_res and dm_sleeve_res:
    bd_em = em_sleeve_res["coefs"][2]
    se_em = em_sleeve_res["se"][2]
    bd_dm = dm_sleeve_res["coefs"][2]
    se_dm = dm_sleeve_res["se"][2]
    diff = bd_em - bd_dm
    se_diff = math.sqrt(se_em ** 2 + se_dm ** 2)
    t_diff = diff / se_diff if se_diff > 0 else 0
    p_diff = two_sided_p(t_diff)
    print(f"  EM-sleeve β_dollar = {bd_em:+.4f}  95% CI [{bd_em-1.96*se_em:+.4f},{bd_em+1.96*se_em:+.4f}]  |t|={abs(em_sleeve_res['t'][2]):.2f}")
    print(f"  DM-sleeve β_dollar = {bd_dm:+.4f}  95% CI [{bd_dm-1.96*se_dm:+.4f},{bd_dm+1.96*se_dm:+.4f}]  |t|={abs(dm_sleeve_res['t'][2]):.2f}")
    print(f"  diff (EM-DM) = {diff:+.4f}  SE_diff = {se_diff:.4f}  t = {t_diff:+.2f}  p = {p_diff:.3e}")
    verdict = "★ EM β_dollar significantly more negative" if t_diff < -1.96 else (
              "EM β_dollar marginally more negative" if t_diff < -1.645 else
              "n.s. — EM/DM β_dollar 동급 dollar 민감도")
    print(f"  → verdict: {verdict}")

# EM vs DM idio σ paired diff (per-archetype mean compared with DM mean)
# Welch's t-test for two independent samples
def welch_t(x, y):
    n1, n2 = len(x), len(y)
    if n1 < 2 or n2 < 2:
        return None
    mx, my = st.mean(x), st.mean(y)
    vx, vy = st.variance(x), st.variance(y)
    se = math.sqrt(vx / n1 + vy / n2)
    if se <= 0:
        return None
    t = (mx - my) / se
    return {"diff": mx - my, "se": se, "t": t, "p": two_sided_p(t)}

idio_test = welch_t(em_idio_sigmas, dm_idio_sigmas)
if idio_test:
    print(f"\n  EM-sleeve σ_idio ann: mean = {em_mean_idio:.2f}%  SD = {em_idio_sd:.2f}%  n = {len(em_idio_sigmas)}")
    print(f"  DM-sleeve σ_idio ann: mean = {dm_mean_idio:.2f}%  SD = {dm_idio_sd:.2f}%  n = {len(dm_idio_sigmas)}")
    print(f"  Welch's t-test diff (EM-DM): {idio_test['diff']:+.2f}%p  SE = {idio_test['se']:.2f}  t = {idio_test['t']:+.2f}  p = {idio_test['p']:.3e}")
    verdict_idio = ("★ EM σ_idio significantly larger" if idio_test['t'] > 1.96 else
                    "EM σ_idio marginally larger" if idio_test['t'] > 1.645 else
                    "n.s.")
    print(f"  → verdict: {verdict_idio}")

print(f"\n★ EM 약가중 정당화 input:")
print(f"   - β_dollar 비교: 위 t-test 결과 (시그널 직접 비교)")
print(f"   - σ_idio gap: EM idio σ = {em_mean_idio:.2f}% vs DM idio σ = {dm_mean_idio:.2f}% → {em_mean_idio/dm_mean_idio:.2f}배")
print(f"   - ⛔ R² 차이는 정당화 근거 X — systematic share/idio share 만 표시 (mechanism 박제용)")

# ================================================================
# Task E: 누락 critical 지표 caveat
# ================================================================
print("\n" + "=" * 130)
print("§E. 누락 critical 지표 caveat — 우리 yahoo_cache 없음, 블록6 요청")
print("=" * 130)
print("""
EM 의사결정 4 critical 지표 (현재 수집기 부재):
  1. 美대비 상대 이익모멘텀 (MSCI EM forward EPS revision vs SP500)
     → 글로벌 EPS revision 데이터 (Refinitiv/IBES, Bloomberg) 필요
  2. forward PE 갭 (MSCI EM forward E/P vs SP500 forward E/P)
     → 저평가 매력도 측정. MSCI factsheet (월간 publish) or Bloomberg
  3. 금리차/carry (EM 정책금리 - US FFR, country별)
     → Bra/Mex/Ind/Kor 정책금리 — IMF IFS API or central bank 직접
  4. terms-of-trade (commodity export/수입 비율, country별)
     → 특히 brazil/mexico critical — IMF terms-of-trade index

★ 본 study 에서 가장 critical: #4 terms-of-trade for brazil/mexico (commodity_exporter archetype).
   현 분석 = β_oil 만 측정 가능. ToT 변동은 oil 외 다양한 commodity basket 영향 미반영.
   → 블록6 (data sourcing extension) 에 요청 박제 필요.
""")

print("\n# Done.")
