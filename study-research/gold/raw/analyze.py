"""
Gold lens 실데이터 대조 — yaml 블록3·4 prior_strength/base_weight 미세조정 근거.
입력: raw/{fred_dfii10, fred_t10yie, fred_dtwexbgs}.csv + raw/try_yahoo_v8.json (GLD)
출력: stdout 요약 + raw/analysis_summary.json + raw/correlation_matrix.csv + raw/rolling_corr.csv
"""
import json
import os
import numpy as np
import pandas as pd

RAW = os.path.dirname(os.path.abspath(__file__))

def load_fred(name, col):
    df = pd.read_csv(os.path.join(RAW, name))
    df.columns = ["date", col]
    df["date"] = pd.to_datetime(df["date"])
    df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.set_index("date").sort_index()

def load_yahoo_v8(name, col):
    with open(os.path.join(RAW, name), "r", encoding="utf-8") as f:
        j = json.load(f)
    res = j["chart"]["result"][0]
    ts = res["timestamp"]
    close = res["indicators"]["quote"][0]["close"]
    df = pd.DataFrame({"date": pd.to_datetime(ts, unit="s"), col: close})
    df["date"] = df["date"].dt.normalize()
    df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.set_index("date").sort_index()

real = load_fred("fred_dfii10.csv", "real_rate")
brk = load_fred("fred_t10yie.csv", "breakeven")
dol = load_fred("fred_dtwexbgs.csv", "dollar")
gld = load_yahoo_v8("try_yahoo_v8.json", "gold")

# 일별 outer → 공통 forward fill (FRED 휴장/실데이터 정렬)
df = pd.concat([real, brk, dol, gld], axis=1).sort_index()
df = df.loc["2010-01-01":].ffill().dropna()
print(f"[load] merged daily rows={len(df)} range={df.index.min().date()}~{df.index.max().date()}")

# 변화율 — real_rate/breakeven 은 level diff(bp 환산), dollar/gold 는 log return
chg = pd.DataFrame(index=df.index)
chg["d_real_bp"] = df["real_rate"].diff() * 100.0   # %p → bp
chg["d_brk_bp"]  = df["breakeven"].diff() * 100.0
chg["r_dollar"]  = np.log(df["dollar"]).diff()
chg["r_gold"]    = np.log(df["gold"]).diff()
chg = chg.dropna()
print(f"[delta] rows={len(chg)} range={chg.index.min().date()}~{chg.index.max().date()}")

# 기간 분할
periods = {
    "all_2010_2026": (chg.index.min(), chg.index.max()),
    "pre_2020":      ("2010-01-01", "2019-12-31"),
    "covid_2020_21": ("2020-01-01", "2021-12-31"),
    "decoup_2022_26":("2022-01-01", chg.index.max()),
}

def pearson(x, y):
    if len(x) < 30: return float("nan")
    return float(np.corrcoef(x, y)[0, 1])

def spearman(x, y):
    if len(x) < 30: return float("nan")
    return float(pd.Series(x).rank().corr(pd.Series(y).rank()))

summary = {}
for pname, (s, e) in periods.items():
    sub = chg.loc[s:e].dropna()
    n = len(sub)
    summary[pname] = {
        "n_days": n,
        "pearson": {
            "real_rate_vs_gold": pearson(sub["d_real_bp"], sub["r_gold"]),
            "dollar_vs_gold":    pearson(sub["r_dollar"],   sub["r_gold"]),
            "breakeven_vs_gold": pearson(sub["d_brk_bp"],   sub["r_gold"]),
            "real_vs_dollar":    pearson(sub["d_real_bp"], sub["r_dollar"]),
        },
        "spearman_rank_ic": {
            "real_rate_vs_gold": spearman(sub["d_real_bp"], sub["r_gold"]),
            "dollar_vs_gold":    spearman(sub["r_dollar"],   sub["r_gold"]),
            "breakeven_vs_gold": spearman(sub["d_brk_bp"],   sub["r_gold"]),
        },
        "gold_annualized_vol": float(sub["r_gold"].std() * np.sqrt(252)),
        "gold_annualized_ret": float(sub["r_gold"].mean() * 252),
    }

# Rolling 252d Pearson real_rate↔gold (decoupling 시점 식별)
roll = pd.DataFrame(index=chg.index)
roll["rc_real_gold_252d"] = chg["d_real_bp"].rolling(252).corr(chg["r_gold"])
roll["rc_dollar_gold_252d"] = chg["r_dollar"].rolling(252).corr(chg["r_gold"])
roll_save = roll.dropna()
roll_save.to_csv(os.path.join(RAW, "rolling_corr.csv"))

# decoupling 식별 — real-gold 252d corr 의 부호반전/약화 (|corr| < 0.10 또는 부호반전)
rc = roll["rc_real_gold_252d"].dropna()
decoup_pos = rc[rc > 0.0]
decoup_weak = rc[rc.abs() < 0.10]
print(f"[rolling] real-gold 252d corr median={rc.median():.3f} min={rc.min():.3f} max={rc.max():.3f}")
if not decoup_pos.empty:
    print(f"[rolling] FIRST positive flip (corr>0): {decoup_pos.index[0].date()} corr={decoup_pos.iloc[0]:.3f}")
    print(f"[rolling] LAST positive flip: {decoup_pos.index[-1].date()} corr={decoup_pos.iloc[-1]:.3f}")
    print(f"[rolling] positive-corr days: {len(decoup_pos)} ({100*len(decoup_pos)/len(rc):.1f}%)")
if not decoup_weak.empty:
    print(f"[rolling] weak |corr|<0.10 first: {decoup_weak.index[0].date()} last: {decoup_weak.index[-1].date()} days={len(decoup_weak)}")

# 결과 출력 (콘솔)
print("\n=== PERIOD CORRELATIONS ===")
print(f"{'period':<18} {'n':>6} {'r:real-gold':>14} {'r:dol-gold':>12} {'r:brk-gold':>12} {'ic:real-gold':>14} {'gold_vol':>10}")
for p, s in summary.items():
    pc = s["pearson"]; ic = s["spearman_rank_ic"]
    print(f"{p:<18} {s['n_days']:>6} {pc['real_rate_vs_gold']:>14.3f} {pc['dollar_vs_gold']:>12.3f} {pc['breakeven_vs_gold']:>12.3f} {ic['real_rate_vs_gold']:>14.3f} {s['gold_annualized_vol']:>10.3f}")

# 종합 상관 매트릭스 (전체기간) 저장
corr_mat = chg.corr(method="pearson").round(4)
corr_mat.to_csv(os.path.join(RAW, "correlation_matrix.csv"))
print("\n=== FULL-PERIOD CORR MATRIX ===")
print(corr_mat.to_string())

# yaml 미세조정 가이드 (system_priors gold loading 대조)
sys_prior = {"real_rate": -0.5, "dollar": -0.8, "oil": 0.0, "credit": -0.2}
emp_all = summary["all_2010_2026"]["pearson"]
emp_pre = summary["pre_2020"]["pearson"]
emp_dec = summary["decoup_2022_26"]["pearson"]
print("\n=== sys_priors gold loading vs 실측 ===")
print(f"  real_rate: sys_prior={sys_prior['real_rate']:+.2f} / emp_all={emp_all['real_rate_vs_gold']:+.3f} / emp_pre2020={emp_pre['real_rate_vs_gold']:+.3f} / emp_2022_26={emp_dec['real_rate_vs_gold']:+.3f}")
print(f"  dollar:    sys_prior={sys_prior['dollar']:+.2f} / emp_all={emp_all['dollar_vs_gold']:+.3f} / emp_pre2020={emp_pre['dollar_vs_gold']:+.3f} / emp_2022_26={emp_dec['dollar_vs_gold']:+.3f}")

with open(os.path.join(RAW, "analysis_summary.json"), "w", encoding="utf-8") as f:
    json.dump({
        "merged_rows": int(len(df)),
        "date_range": [str(df.index.min().date()), str(df.index.max().date())],
        "periods": summary,
        "rolling_real_gold_252d": {
            "median": float(rc.median()),
            "min": float(rc.min()),
            "max": float(rc.max()),
            "first_positive_date": str(decoup_pos.index[0].date()) if not decoup_pos.empty else None,
            "last_positive_date":  str(decoup_pos.index[-1].date()) if not decoup_pos.empty else None,
            "positive_days_pct": float(100*len(decoup_pos)/len(rc)) if len(rc) else 0.0,
        },
        "sys_prior_check": {
            "real_rate": {"sys": -0.5, "emp_all": emp_all['real_rate_vs_gold'], "emp_pre2020": emp_pre['real_rate_vs_gold'], "emp_2022_26": emp_dec['real_rate_vs_gold']},
            "dollar":    {"sys": -0.8, "emp_all": emp_all['dollar_vs_gold'],    "emp_pre2020": emp_pre['dollar_vs_gold'],    "emp_2022_26": emp_dec['dollar_vs_gold']},
        },
    }, f, indent=2)
print("\n[save] raw/analysis_summary.json + raw/correlation_matrix.csv + raw/rolling_corr.csv")
