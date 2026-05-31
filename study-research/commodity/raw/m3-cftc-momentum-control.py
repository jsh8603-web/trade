# -*- coding: utf-8 -*-
"""
CFTC speculative 1m forward 신호의 momentum 독립성 검정 (validated_alpha 게이트 해소).
검정: fwd_1m copper return ~ net_spec_z + momentum_12_1 (HAC). net_spec_z 계수가 momentum 통제 후
      유의 유지 → 독립 alpha(validated) / 흡수(비유의) → momentum proxy(structural 격하).
+ Spearman partial correlation (momentum 통제).
"""
import json, urllib.request, urllib.parse
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm

CFTC = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"
DBN = "https://api.db.nomics.world/v22/series/IMF/PCPS/M.W00.PCOPP.USD?observations=1"


def fetch_cftc():
    where = "contract_market_name like '%COPPER%' AND cftc_market_code='CMX'"
    p = {"$where": where, "$select": "report_date_as_yyyy_mm_dd,open_interest_all,noncomm_positions_long_all,noncomm_positions_short_all", "$order": "report_date_as_yyyy_mm_dd", "$limit": "5000"}
    req = urllib.request.Request(CFTC + "?" + urllib.parse.urlencode(p), headers={"User-Agent": "Mozilla/5.0"})
    rows = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8"))
    df = pd.DataFrame(rows); df["date"] = pd.to_datetime(df["report_date_as_yyyy_mm_dd"])
    for c in ["open_interest_all", "noncomm_positions_long_all", "noncomm_positions_short_all"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna().sort_values("date").set_index("date")
    return ((df["noncomm_positions_long_all"] - df["noncomm_positions_short_all"]) / df["open_interest_all"]).rename("net")


def fetch_copper():
    d = json.loads(urllib.request.urlopen(urllib.request.Request(DBN, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read().decode("utf-8"))
    doc = d["series"]["docs"][0]
    return pd.Series([np.nan if v is None else float(v) for v in doc["value"]], index=pd.to_datetime(doc.get("period_start_day") or doc["period"])).dropna().rename("cop")


def partial_spearman(x, y, z):
    # rank residualization
    rx = stats.rankdata(x); ry = stats.rankdata(y); rz = stats.rankdata(z)
    def resid(a, b):
        b1 = sm.add_constant(b); return a - sm.OLS(a, b1).fit().predict(b1)
    ex = resid(rx, rz); ey = resid(ry, rz)
    r, p = stats.pearsonr(ex, ey); return r, p


def main():
    net = fetch_cftc(); cop = fetch_copper()
    netm = net.resample("ME").last().dropna()
    z = ((netm - netm.rolling(36, min_periods=18).mean()) / netm.rolling(36, min_periods=18).std()).dropna()
    copm = cop.resample("ME").last().dropna()
    mom = (copm.shift(1) / copm.shift(12) - 1.0).rename("mom")   # 12-1 month momentum (skip 직전 1m, look-ahead 차단)
    fwd = (copm.shift(-1) / copm - 1.0).rename("fwd")
    df = pd.concat([z.rename("z"), mom, fwd], axis=1).dropna()
    out = {"n": int(len(df))}

    # 단변량 (baseline)
    X1 = sm.add_constant(df["z"].values)
    m1 = sm.OLS(df["fwd"].values, X1).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    out["univariate"] = {"z_beta": round(float(m1.params[1]), 5), "z_t_hac": round(float(m1.tvalues[1]), 3), "z_p_hac": round(float(m1.pvalues[1]), 5)}

    # momentum 통제 (z + mom)
    X2 = sm.add_constant(df[["z", "mom"]].values)
    m2 = sm.OLS(df["fwd"].values, X2).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    out["momentum_controlled"] = {
        "z_beta": round(float(m2.params[1]), 5), "z_t_hac": round(float(m2.tvalues[1]), 3), "z_p_hac": round(float(m2.pvalues[1]), 5),
        "mom_beta": round(float(m2.params[2]), 5), "mom_t_hac": round(float(m2.tvalues[2]), 3), "mom_p_hac": round(float(m2.pvalues[2]), 5)}

    # partial spearman (momentum 통제)
    pr, pp = partial_spearman(df["z"].values, df["fwd"].values, df["mom"].values)
    out["partial_spearman_z_fwd_given_mom"] = {"rho": round(float(pr), 4), "p": round(float(pp), 5)}

    # corr(z, mom) — 교란 강도
    cr, cp = stats.spearmanr(df["z"], df["mom"])
    out["corr_z_momentum"] = {"rho": round(float(cr), 4), "p": round(float(cp), 5)}

    surv = out["momentum_controlled"]["z_p_hac"] < 0.05
    out["verdict"] = {
        "z_survives_momentum_control_HAC_p05": bool(surv),
        "interpretation": ("독립 alpha — momentum 통제 후 net_spec_z 유의 유지 → validated_alpha=true 승격 적격"
                           if surv else
                           "momentum proxy — momentum 통제 시 net_spec_z 비유의 → structural 격하, validated_alpha=false")}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    with open("study-research/commodity/raw/m3-cftc-momentum-control-results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
