# -*- coding: utf-8 -*-
"""
M3 merit 지표 추가: CFTC speculative positioning(copper) → forward 수익률 상관/Rank-IC
=====================================================================================
사용자 지시(2026-05-31): merit 있으면 collector 없어도 main이 구현 → study → 12축 audit → 반영.
H8 후보(mm_net_long_oi_z) = 그동안 "CFTC collector 미구축"으로 이연됐던 merit 지표 → 직접 collector 구현.

collector: CFTC Socrata public API (무료·키불요) https://publicreporting.cftc.gov/resource/6dca-aqww.json
  = Legacy COT (Futures-only). noncommercial = 대형 투기세력(speculative) proxy.
  ★정통 H8 = Disaggregated 'Money Manager' 이나, legacy noncommercial = 더 긴 history의 speculative proxy. 라벨 정직.
copper price: IMF/PCPS via DBnomics (월).

net_spec = (noncomm_long - noncomm_short) / open_interest  → own-history z.
H8 이론(Hong-Yogo 2012): 투기 포지셔닝 = 가격 momentum/예측 신호 (부호 debated → 실측).
★5금지: 합성 금지(fetch 실패=raise) / small-N rigor(n·p·Newey-West·block bootstrap·lag별 Bonferroni).
"""
import json, urllib.request, urllib.parse
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm

CFTC = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"
DBN = "https://api.db.nomics.world/v22/series/IMF/PCPS/M.W00.PCOPP.USD?observations=1"


def fetch_cftc_copper():
    where = "contract_market_name like '%COPPER%' AND cftc_market_code='CMX'"
    params = {"$where": where, "$select": "report_date_as_yyyy_mm_dd,open_interest_all,noncomm_positions_long_all,noncomm_positions_short_all",
              "$order": "report_date_as_yyyy_mm_dd", "$limit": "5000"}
    url = CFTC + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (M3-study)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        rows = json.loads(r.read().decode("utf-8"))
    if not rows or len(rows) < 50:
        raise RuntimeError(f"CFTC copper rows={len(rows) if rows else 0} — 부족, 합성 금지 중단")
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["report_date_as_yyyy_mm_dd"])
    for c in ["open_interest_all", "noncomm_positions_long_all", "noncomm_positions_short_all"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna().sort_values("date").set_index("date")
    net_spec = (df["noncomm_positions_long_all"] - df["noncomm_positions_short_all"]) / df["open_interest_all"]
    return net_spec.rename("net_spec")


def fetch_copper():
    req = urllib.request.Request(DBN, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode("utf-8"))
    doc = d["series"]["docs"][0]
    idx = pd.to_datetime(doc.get("period_start_day") or doc["period"])
    s = pd.Series([np.nan if v is None else float(v) for v in doc["value"]], index=idx).dropna()
    return s.rename("copper")


def block_boot_ci(x, y, block, n_boot=4000, seed=11):
    rng = np.random.default_rng(seed); x = np.asarray(x, float); y = np.asarray(y, float); n = len(x)
    nb = int(np.ceil(n / block)); rhos = []
    for _ in range(n_boot):
        st = rng.integers(0, n, size=nb)
        idx = np.concatenate([(np.arange(s, s + block) % n) for s in st])[:n]
        rr = stats.spearmanr(x[idx], y[idx]).correlation
        if np.isfinite(rr): rhos.append(rr)
    return float(np.percentile(rhos, 2.5)), float(np.percentile(rhos, 97.5))


def main():
    out = {"collector": "CFTC Socrata 6dca-aqww (legacy COT, noncommercial=speculative proxy). 무료·키불요.",
           "caveat": "정통 H8=Disaggregated Money Manager. legacy noncommercial = 더 긴 history speculative proxy. 라벨 정직.",
           "series": {}, "tests": [], "meta": {}, "verdict": {}}
    try:
        net = fetch_cftc_copper(); cop = fetch_copper()
    except Exception as e:
        out["verdict"] = {"status": "INSUFFICIENT", "reason": f"실데이터 fetch 실패: {e}"}
        print(json.dumps(out, ensure_ascii=False, indent=2)); return

    out["series"]["cftc_net_spec"] = {"n_weekly": int(len(net)), "start": str(net.index[0].date()), "end": str(net.index[-1].date())}
    out["series"]["copper"] = {"n_monthly": int(len(cop)), "start": str(cop.index[0].date()), "end": str(cop.index[-1].date())}

    # 월말 정렬 + own-history z(36m rolling)
    netm = net.resample("ME").last().dropna()
    z = ((netm - netm.rolling(36, min_periods=18).mean()) / netm.rolling(36, min_periods=18).std()).dropna().rename("z")
    copm = cop.resample("ME").last().dropna()

    raw_p = []
    for fm in [1, 2, 3, 6, 12]:  # forward months
        fwd = (copm.shift(-fm) / copm - 1.0).rename("fwd")
        df = pd.concat([z, fwd], axis=1).dropna()
        if len(df) < 24:
            continue
        rho, p = stats.spearmanr(df["z"], df["fwd"]); n = len(df)
        X = sm.add_constant(df["z"].values)
        m = sm.OLS(df["fwd"].values, X).fit(cov_type="HAC", cov_kwds={"maxlags": max(fm, 3)})
        ci = m.conf_int(alpha=0.05)[1]
        try:
            lo, hi = block_boot_ci(df["z"].values, df["fwd"].values, block=max(fm, 4))
        except Exception:
            lo = hi = None
        rec = {"fwd_m": fm, "n": int(n), "spearman_rho": round(float(rho), 4), "spearman_p_raw": round(float(p), 5),
               "nw_t_hac": round(float(m.tvalues[1]), 3), "nw_p_hac": round(float(m.pvalues[1]), 5),
               "nw_ci95": [round(float(ci[0]), 5), round(float(ci[1]), 5)],
               "boot_rho_ci95": [None if lo is None else round(lo, 4), None if hi is None else round(hi, 4)]}
        out["tests"].append(rec); raw_p.append(rec["spearman_p_raw"])

    m_ = len(raw_p)
    if m_:
        bonf = 0.05 / m_
        out["meta"]["multiple_comparison"] = {
            "n_tests": m_, "bonferroni_alpha": round(bonf, 6),
            "survive_bonferroni": [(t["fwd_m"], t["spearman_rho"], t["spearman_p_raw"]) for t in out["tests"] if t["spearman_p_raw"] < bonf],
            "survive_nw_hac_p05": [(t["fwd_m"], t["nw_t_hac"], t["nw_p_hac"]) for t in out["tests"] if t["nw_p_hac"] < 0.05]}
    out["meta"]["note"] = "월별+forward overlap 자기상관 → 실질 유의=HAC p AND block bootstrap CI 0 미포함."
    out["verdict"] = {"status": "MEASURED", "note": "verdict 라벨=main 이 small-N rigor 로 판정. HAC 미생존+CI 0포함이면 structural/REJECT 격하."}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    with open("study-research/commodity/raw/m3-cftc-speculative-results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
