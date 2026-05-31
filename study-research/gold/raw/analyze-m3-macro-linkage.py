"""
M3 거시연관 분석 — gold sleeve 의 timeline.md §4 가이드 적용.
요구 축:
  (1) regime별 (epoch E1~E4) gold 평균수익·변동성 분해
  (2) driver loading — gold ~ Δrate(us10y bp) + r_dollar + r_oil. 전기간 + epoch 별
      ★rate 직접 loading 보다 dollar 채널·국면조건부 주목 (M1 발견)
  (3) cross-asset vs within-sleeve: gold = 단일 sleeve, within 무관, cross 만 유의
입력: fred_dgs10·dtwexbgs·wti + try_dxy.json + GLD
산출: stdout + raw/m3_result.json
"""
import json, os
import numpy as np
import pandas as pd
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant

RAW = os.path.dirname(os.path.abspath(__file__))

def load_fred(name, col):
    df = pd.read_csv(os.path.join(RAW, name)); df.columns=["date",col]
    df["date"]=pd.to_datetime(df["date"]); df[col]=pd.to_numeric(df[col], errors="coerce")
    return df.set_index("date").sort_index()

def load_yv8(name, col):
    with open(os.path.join(RAW, name), "r", encoding="utf-8") as f:
        j = json.load(f)
    r = j["chart"]["result"][0]
    return pd.DataFrame({"date": pd.to_datetime(r["timestamp"],unit="s").normalize(),
                        col: r["indicators"]["quote"][0]["close"]}).dropna().set_index("date").sort_index()

us10y = load_fred("fred_dgs10.csv", "us10y")
wti   = load_fred("fred_wti.csv", "oil")
broad = load_fred("fred_dtwexbgs.csv", "dollar_broad")
dxy   = load_yv8("try_dxy.json", "dxy")
gld   = load_yv8("try_yahoo_v8.json", "gold")

df = pd.concat([us10y, wti, broad, dxy, gld], axis=1).loc["2021-10-01":].ffill().dropna()
print(f"[load] daily n={len(df)} range={df.index.min().date()}~{df.index.max().date()}")

# Daily changes
chg = pd.DataFrame(index=df.index)
chg["d_us10y_bp"] = df["us10y"].diff() * 100
chg["r_dxy"] = np.log(df["dxy"]).diff()
chg["r_broad"] = np.log(df["dollar_broad"]).diff()
chg["r_oil"] = np.log(df["oil"]).diff()
chg["r_gold"] = np.log(df["gold"]).diff()
chg = chg.dropna()

# Quarter mapping (timeline.md 분기)
def get_epoch(d):
    if pd.Timestamp("2022-01-01") <= d <= pd.Timestamp("2022-09-30"): return "E1_긴축충격"
    if pd.Timestamp("2022-10-01") <= d <= pd.Timestamp("2023-06-30"): return "E2_전환반등"
    if pd.Timestamp("2023-07-01") <= d <= pd.Timestamp("2023-09-30"): return "E3_금리재상승"
    if pd.Timestamp("2023-10-01") <= d <= pd.Timestamp("2024-12-31"): return "E4_pivot_인하"
    return "other"
chg["epoch"] = chg.index.map(get_epoch)

# === (1) Regime별 (epoch) gold 평균수익·변동성 ===
print("\n=== (1) Epoch 별 gold 수익률 분해 (daily, annualized) ===")
print(f"{'epoch':<18} {'n':>5} {'avg ret':>10} {'ann ret':>10} {'ann vol':>10} {'sharpe':>8}")
epoch_summary = {}
for ep in ["E1_긴축충격", "E2_전환반등", "E3_금리재상승", "E4_pivot_인하"]:
    sub = chg[chg["epoch"] == ep]
    if len(sub) < 5: continue
    ar = sub["r_gold"].mean()
    av = sub["r_gold"].std()
    ann_ret = ar * 252
    ann_vol = av * np.sqrt(252)
    sharpe = ann_ret / ann_vol if ann_vol > 0 else 0
    epoch_summary[ep] = {"n": int(len(sub)), "avg_daily_ret": float(ar), "ann_ret": float(ann_ret), "ann_vol": float(ann_vol), "sharpe": float(sharpe)}
    print(f"{ep:<18} {len(sub):>5} {ar:>10.5f} {ann_ret:>9.2%} {ann_vol:>9.2%} {sharpe:>8.2f}")

# === (2) Driver loading — gold ~ Δrate + r_dollar + r_oil ===
print("\n=== (2) Driver loading: full period (2022-Q1 ~ 2024-Q4) ===")
sample = chg.loc["2022-01-01":"2024-12-31"].dropna()
def fit_loading(sub, label):
    X = sub[["d_us10y_bp", "r_dxy", "r_oil"]].values
    y = sub["r_gold"].values
    if len(sub) < 30: return None
    Xc = add_constant(X)
    res = OLS(y, Xc).fit()
    # 표준화 β (z-score 변환 후)
    z = sub[["d_us10y_bp", "r_dxy", "r_oil", "r_gold"]].apply(lambda x: (x - x.mean()) / x.std())
    res_z = OLS(z["r_gold"].values, add_constant(z[["d_us10y_bp", "r_dxy", "r_oil"]].values)).fit()
    out = {
        "label": label, "n": int(len(sub)), "r2": float(res.rsquared),
        "raw_beta_rate_bp": float(res.params[1]), "raw_beta_dollar": float(res.params[2]), "raw_beta_oil": float(res.params[3]),
        "raw_se_rate": float(res.bse[1]), "raw_se_dollar": float(res.bse[2]), "raw_se_oil": float(res.bse[3]),
        "std_beta_rate": float(res_z.params[1]), "std_beta_dollar": float(res_z.params[2]), "std_beta_oil": float(res_z.params[3]),
        "t_rate": float(res.params[1]/res.bse[1]), "t_dollar": float(res.params[2]/res.bse[2]), "t_oil": float(res.params[3]/res.bse[3]),
    }
    return out

full = fit_loading(sample, "full_2022-2024")
print(f"  full period n={full['n']} R²={full['r2']:.4f}")
print(f"  raw β: rate={full['raw_beta_rate_bp']:+.6f} (per bp, t={full['t_rate']:.2f})")
print(f"          dollar={full['raw_beta_dollar']:+.4f} (per log point, t={full['t_dollar']:.2f})")
print(f"          oil={full['raw_beta_oil']:+.4f} (per log point, t={full['t_oil']:.2f})")
print(f"  std β: rate={full['std_beta_rate']:+.3f}, dollar={full['std_beta_dollar']:+.3f}, oil={full['std_beta_oil']:+.3f}")

# Per-epoch loading
print("\n=== (2b) Driver loading per epoch ===")
print(f"{'epoch':<18} {'n':>5} {'R²':>6} {'std β_rate':>12} {'std β_dollar':>14} {'std β_oil':>12}")
epoch_loadings = {}
for ep in ["E1_긴축충격", "E2_전환반등", "E3_금리재상승", "E4_pivot_인하"]:
    sub = chg[chg["epoch"] == ep]
    out = fit_loading(sub, ep)
    if out:
        epoch_loadings[ep] = out
        print(f"{ep:<18} {out['n']:>5} {out['r2']:>6.3f} {out['std_beta_rate']:>+12.3f} {out['std_beta_dollar']:>+14.3f} {out['std_beta_oil']:>+12.3f}")

# === (3) 국면조건부 dollar 채널 — M1 발견 적용 ===
# rate-up 분기 (Δus10y_bp > 0) vs rate-down 분기 의 dollar loading
print("\n=== (3) 국면조건부 (rate-up vs rate-down): dollar loading 차이 ===")
for cond_name, cond in [("rate-up days (Δus10y>0)", chg["d_us10y_bp"] > 0),
                        ("rate-down days (Δus10y<0)", chg["d_us10y_bp"] < 0)]:
    sub = chg[cond]
    out = fit_loading(sub, cond_name)
    if out:
        print(f"  {cond_name:<28} n={out['n']} std β: rate={out['std_beta_rate']:+.3f} dollar={out['std_beta_dollar']:+.3f} oil={out['std_beta_oil']:+.3f}")

# === (4) cross-asset vs within-sleeve (gold = 단일자산) ===
print("\n=== (4) cross-asset vs within-sleeve ===")
print("  gold = 단일 자산 sleeve. within-sleeve 개념 무관 (종목 분리 X).")
print("  cross-asset linkage 만 유의:")
print(f"    gold vs us10y (Δ): Pearson = {chg['d_us10y_bp'].corr(chg['r_gold']):+.4f}")
print(f"    gold vs DXY (r): Pearson = {chg['r_dxy'].corr(chg['r_gold']):+.4f}")
print(f"    gold vs broad TWI (r): Pearson = {chg['r_broad'].corr(chg['r_gold']):+.4f}")
print(f"    gold vs oil (r): Pearson = {chg['r_oil'].corr(chg['r_gold']):+.4f}")

result = {
    "data_range": [str(chg.index.min().date()), str(chg.index.max().date())],
    "n_obs_total": int(len(chg)),
    "epoch_summary": epoch_summary,
    "full_period_loading": full,
    "epoch_loadings": epoch_loadings,
    "rate_conditional_dollar_channel": "see (3) output",
    "cross_asset_pearson": {
        "us10y_vs_gold": float(chg["d_us10y_bp"].corr(chg["r_gold"])),
        "dxy_vs_gold": float(chg["r_dxy"].corr(chg["r_gold"])),
        "broad_vs_gold": float(chg["r_broad"].corr(chg["r_gold"])),
        "oil_vs_gold": float(chg["r_oil"].corr(chg["r_gold"])),
    },
}
with open(os.path.join(RAW, "m3_result.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, default=str)
print(f"\n[save] raw/m3_result.json")
