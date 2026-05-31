"""
M3 commodity merit indicator study — NOAA ONI (ENSO) → agri commodity prices.

가설: ENSO (El Nino/La Nina, ONI 지수) 는 농업 공급충격(가뭄·홍수)을 통해 곡물·연질 commodity
가격을 선행한다. ONI(t) 가 향후 h개월 forward return 을 예측하는가 (predictive).

데이터:
- ONI: NOAA CPC ASCII (oni.ascii.txt). ANOM 컬럼 = ONI(3개월 SST anomaly), 계절(DJF..NDJ)→중심월 매핑.
- agri price: IMF/PCPS via DBnomics (월). 패널 6종 = maize/wheat/soybean/rice/sugar/cocoa.

★5금지: 합성 금지(fetch 실패=raise) / small-N rigor(n·p·Newey-West HAC·block bootstrap·다중비교 Bonferroni).
verdict 라벨 = main 이 small-N rigor 로 판정 (이 스크립트는 MEASURED 산출만).
"""
import json, urllib.request
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm

ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
PCPS = "https://api.db.nomics.world/v22/series/IMF/PCPS/M.W00.{code}.USD?observations=1"
# ENSO 관련 agri 패널 (DBnomics 검증 완료: 전부 n=426, 1990-01~2025-06)
AGRI = {"maize": "PMAIZMT", "wheat": "PWHEAMT", "soybean": "PSOYB",
        "rice": "PRICENPQ", "sugar": "PSUGAISA", "cocoa": "PCOCO"}
# 계절 3글자 → 중심월 (DJF 중심=Jan ... NDJ 중심=Dec)
SEAS_MONTH = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
              "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12}
FWD = [3, 6, 12]  # forward window (개월)


def fetch_oni():
    req = urllib.request.Request(ONI_URL, headers={"User-Agent": "Mozilla/5.0 (M3-study)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        lines = r.read().decode("utf-8").splitlines()
    recs = []
    for ln in lines[1:]:  # header skip
        p = ln.split()
        if len(p) != 4 or p[0] not in SEAS_MONTH:
            continue
        seas, yr, _total, anom = p
        recs.append((pd.Timestamp(int(yr), SEAS_MONTH[seas], 1), float(anom)))
    if len(recs) < 200:
        raise RuntimeError(f"ONI rows={len(recs)} 부족 — 합성 금지 중단")
    s = pd.Series(dict(recs)).sort_index()
    return s.rename("oni")


def fetch_agri(code):
    url = PCPS.format(code=code)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode("utf-8"))
    doc = d["series"]["docs"][0]
    idx = pd.to_datetime(doc.get("period_start_day") or doc["period"])
    s = pd.Series([np.nan if v is None else float(v) for v in doc["value"]], index=idx).dropna()
    if len(s) < 100:
        raise RuntimeError(f"{code} obs={len(s)} 부족 — 합성 금지 중단")
    return s.rename("price")


def block_boot_ci(x, y, block, n_boot=4000, seed=11):
    rng = np.random.default_rng(seed)
    x = np.asarray(x, float); y = np.asarray(y, float); n = len(x)
    nb = int(np.ceil(n / block)); rhos = []
    for _ in range(n_boot):
        starts = rng.integers(0, n - block + 1, size=nb)
        idx = np.concatenate([np.arange(s, s + block) for s in starts])[:n]
        rr = stats.spearmanr(x[idx], y[idx]).correlation
        if not np.isnan(rr):
            rhos.append(rr)
    lo, hi = np.percentile(rhos, [2.5, 97.5])
    return round(float(lo), 4), round(float(hi), 4)


def main():
    out = {"meta": {"indicator": "noaa_oni_3m_ma (ENSO)", "source_oni": ONI_URL,
                    "source_price": "IMF/PCPS via DBnomics", "panel": list(AGRI.keys())},
           "tests": []}
    try:
        oni = fetch_oni()
    except Exception as e:
        out["error"] = f"ONI fetch 실패: {e!r}"; print(json.dumps(out, ensure_ascii=False, indent=2)); return

    raw_p = []
    for name, code in AGRI.items():
        try:
            price = fetch_agri(code)
        except Exception as e:
            out["tests"].append({"commodity": name, "error": repr(e)}); continue
        # 월말 정렬, log return
        px = price.resample("MS").last()
        on = oni.resample("MS").last()
        df0 = pd.concat([on, px], axis=1).dropna()
        df0["ret1"] = np.log(df0["price"]).diff()
        for h in FWD:
            d = df0.copy()
            # forward h개월 누적 log return (예측 대상)
            d["fwd"] = np.log(d["price"]).shift(-h) - np.log(d["price"])
            d = d[["oni", "fwd"]].dropna()
            n = len(d)
            if n < 30:
                continue
            rho, p = stats.spearmanr(d["oni"], d["fwd"])
            X = sm.add_constant(d["oni"].values)
            m = sm.OLS(d["fwd"].values, X).fit(cov_type="HAC", cov_kwds={"maxlags": max(h, 3)})
            ci = m.conf_int()[1]
            block = max(h, n // 10)
            blo, bhi = block_boot_ci(d["oni"].values, d["fwd"].values, block)
            rec = {"commodity": name, "fwd_m": h, "n": int(n),
                   "spearman_rho": round(float(rho), 4), "spearman_p_raw": round(float(p), 5),
                   "nw_t_hac": round(float(m.tvalues[1]), 3), "nw_p_hac": round(float(m.pvalues[1]), 5),
                   "nw_beta_ci95": [round(float(ci[0]), 5), round(float(ci[1]), 5)],
                   "boot_rho_ci95": [blo, bhi]}
            out["tests"].append(rec); raw_p.append(rec["spearman_p_raw"])

    m_ = len(raw_p)
    if m_:
        bonf = 0.05 / m_
        out["multiple_comparison"] = {
            "n_tests": m_, "bonferroni_alpha": round(bonf, 6),
            "survive_bonferroni": [(t["commodity"], t["fwd_m"], t["spearman_rho"], t["spearman_p_raw"])
                                   for t in out["tests"] if "spearman_p_raw" in t and t["spearman_p_raw"] < bonf],
            "survive_nw_hac_p05": [(t["commodity"], t["fwd_m"], t["nw_t_hac"], t["nw_p_hac"])
                                   for t in out["tests"] if "nw_p_hac" in t and t["nw_p_hac"] < 0.05]}
    out["meta"]["note"] = ("ONI predictive(forward h개월) · 월별 overlap 자기상관 → 실질 유의 = HAC p AND "
                           "block bootstrap CI 0 미포함 AND Bonferroni 생존. 6 commodity x 3 fwd = 다중비교.")
    out["verdict"] = {"status": "MEASURED",
                      "note": "라벨=main 판정. HAC 미생존+CI 0포함+Bonferroni 탈락이면 미채택(실측 무상관), 생존 시 채택 후보."}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    with open("m3-noaa-oni-enso-results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
