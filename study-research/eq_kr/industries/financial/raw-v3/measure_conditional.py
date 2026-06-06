# -*- coding: utf-8 -*-
"""measure_conditional.py — financial conditional IC surface (S2 신규, dispatch 원의도 본체).

측정 대상 = IC(지표, regime, horizon) = "어느 국면에 어느 지표가 forward return 예측하나".
기존 measure.py(unconditional) + measure_valuation.py(PBR/PER) 를 ★금융특화 regime 분해로 확장.

================================================================================
★G-F FRAME CONTRACT 7항 사전 선언 (frame _dispatch-gates §G-F, 미선언=검정 불가)
================================================================================
1. regime 선언규칙:
   - ★금융특화 축 = 금리 regime 3종 (rate_regime=국고3Y 6M Δ / curve_regime=10Y-3Y term spread 분위 / credit_regime=AA−-국고3Y 분위)
     + 반도체 미러 base (macro CLI 4 / krw 3 / flow 3). 금리가 NIM 본질 driver(반도체 DRAM cycle 대응).
   - ★★cell 곱셈 금지 (team-lead 가이드 2026-06-05): base 36셀(Macro4×KRW3×flow3)에 금리축을 ⛔곱하지 않음
     (4×3×3×rate3 = 108셀 → cell N 전부 붕괴). ★각 regime 축은 **독립 1D 분해**(REGIME_AXES loop = 축별 cell 만,
     cross product 아님). 실측 cell candidate = 단일축 합 4+3+3+3+3+2 = 18 (곱셈 648 회피). base 36셀 1D 축(macro/krw/flow)
     = 12산업 공통 보존. 금리 3축 = 그 위 ★별도 1D 금융전용 보조 surface(team-lead 권고 b) + family_2 interaction(권고 a).
   - 개수 = 단일축 측정(각 독립). 금리 3축 전부 powered(N≥24) 실측. 2축 cross = supervisor 통합 또는 N 누적 후.
   - effective-n = block 수 (overlapping forward h일 → n_eff = n_obs/(1+2Σρ_k), HAC lag = h).
   - HAC lag = horizon = 5/20/60 거래일.
2. interaction/split 사전확약 + 직교화:
   - conditioning = split(regime별 IC) 사전동결. 사후 interaction 전환 금지.
   - family_2 interaction term(rate×cs / flow×value, 자유도보존) = family_1 부호 갈리면만 추가(G-B).
   - 직교화: interaction = main effect(unconditional)에 residualize. order = unconditional 먼저.
3. 단일 FDR family (★측정 前 멤버십 사전 고정 = garden-of-forking-paths 차단):
   - ★family 멤버십 = {6 신호(mom_6/mom_12_1/rev_1m/vol_60/pbr_z/per_z) × 3 horizon(y_5d/20d/60d) × powered regime cell}
     + ★sub-sector(전체/bank/securities/insurance/rate_POS/rate_NEG) 전체를 하나의 BY-FDR alpha budget 사전 동결.
     측정 결과 본 후 family 재정의 ⛔금지(은행만 떼서 보기 등).
   - main + conditional + interaction 모두 동일 family alpha 공유. "공짜" 검정 없음.
   - M_eff = 신호상관 보정 유효검정수. 산업단계 = naive m + M_eff_signal 박제, 통합 M_eff = supervisor.
   - ★G-B 판정 순서: (1) conditional IC (2) family_2 interaction (3) family_2 살린 뒤에만 "약함" 판정.
4. null + MDE/power:
   - null = IC=0. MDE = small cell(n=10~30) detectable |IC| ≈ 0.05~0.10 (α=0.05, power 0.8).
   - power < threshold cell = "underpowered" 라벨(PASS 아님). N<24 cell = 자동 inconclusive.
5. PIT 동결 + 비대칭 search 금지:
   - regime threshold(rate Δ ±0.3%p, term/credit 분위 70%, CLI 100, KRW ±5%, flow z ±1) = 사전 동결(도메인 표준).
   - 신호 z normalization = 월말 cross-sectional. forward = shift(-h) 일간. ★금리 일별 = 발표지연 無(ex-ante).
6. Turnover/T-cost: Net-alpha = gross IC − cost. KR STT sell 0.20% 비대칭. regime별 turnover 차등(supervisor sqrt).
7. per-test null calibration: ★small cell block 한자릿수 → asymptotic NW-HAC t = size-invalid(Kiefer-Vogelsang).
   → wild-cluster bootstrap(Rademacher, B=2000) per-cell p-value. asymptotic t 참고만.
================================================================================

★financial 특화 (theory-notes §0/§5.1, Gemini Q2): 은행/보험(금리+) vs 증권(금리−) 부호 반대
   → ★sub-sector 분리 측정 의무(frame §1.6, ERROR-202605302245 anchor). 전체 eq-weight = 부호 cancel 점검.

raw 재현: prices/regime_labels/dart_financials/universe parquet + 본 .py.
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

STT_SELL, COMMISSION, SPREAD_HALF = 0.0020, 0.00015, 0.0005
HORIZONS_D = {"y_5d": 5, "y_20d": 20, "y_60d": 60}
# ★금융특화 regime 축 (금리 3종 우선 + 반도체 미러)
REGIME_AXES = ["rate_regime", "curve_regime", "credit_regime",
               "krw_regime", "flow_regime", "macro_regime"]
# ★sub-sector 분리 (frame §1.6 cancel 회피). None = 전체 universe.
SUBSECTOR_GROUPS = {
    "ALL": None,
    "bank": ["bank"],
    "securities": ["securities"],
    "insurance": ["insurance"],
    "rate_POS": ["bank", "insurance", "other_fin", "credit"],  # 금리상승 수혜 그룹
    "rate_NEG": ["securities"],                                  # 금리상승 비수혜(증권)
}


def load():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    lab = pd.read_parquet(DATA / "regime_labels.parquet"); lab.index = pd.to_datetime(lab.index)
    fin = pd.read_parquet(DATA / "dart_financials.parquet")
    uni = pd.read_parquet(DATA / "universe.parquet"); uni = uni[uni["pass_floor"]].set_index("Code")
    return px, lab, fin, uni


def csz(panel):
    return panel.sub(panel.mean(axis=1), axis=0).div(panel.std(axis=1, ddof=1).replace(0, np.nan), axis=0)


def build_price_signals(px):
    pxm = px.resample("ME").last()
    ret_d = px.pct_change()
    return {
        "mom_6": csz(pxm / pxm.shift(6) - 1),
        "mom_12_1": csz(pxm.shift(1) / pxm.shift(12) - 1),
        "rev_1m": csz(pxm / pxm.shift(1) - 1),
        "vol_60": csz((ret_d.rolling(60).std() * np.sqrt(252)).resample("ME").last()),
    }


def build_valuation_signals(px, fin, uni):
    """PIT-safe PBR/PER 월말 z (rcept_dt 이후만). measure_valuation 미러."""
    pxm = px.resample("ME").last()
    shares = {}
    for code in px.columns:
        lp = px[code].dropna()
        if len(lp) and code in uni.index:
            mc = uni.loc[code, "Marcap"]
            if pd.notna(mc) and lp.iloc[-1] > 0:
                shares[code] = mc / lp.iloc[-1]
    fin = fin.copy()
    fin["rcept_dt"] = pd.to_datetime(fin["rcept_dt"], format="%Y%m%d", errors="coerce")
    pbr_panel, per_panel = {}, {}
    for code in px.columns:
        if code not in shares:
            continue
        cf = fin[fin["code"] == code].sort_values("rcept_dt")
        if len(cf) == 0:
            continue
        sh = shares[code]
        pbr_s = pd.Series(index=pxm.index, dtype=float)
        per_s = pd.Series(index=pxm.index, dtype=float)
        for dt in pxm.index:
            avail = cf[cf["rcept_dt"] <= dt]
            if len(avail) == 0 or pd.isna(pxm.loc[dt, code]):
                continue
            eq = avail["equity"].iloc[-1]; ni = avail["net_income"].iloc[-1]
            mktcap = pxm.loc[dt, code] * sh
            if eq and eq > 0:
                pbr_s[dt] = mktcap / eq
            if ni and ni > 0:
                per_s[dt] = mktcap / ni
        pbr_panel[code] = pbr_s; per_panel[code] = per_s
    return {"pbr_z": csz(pd.DataFrame(pbr_panel)), "per_z": csz(pd.DataFrame(per_panel))}


def forward_returns_daily(px, anchor_dates, h_days):
    out = {}
    for dt in anchor_dates:
        pos = px.index.searchsorted(dt)
        if pos >= len(px.index):
            continue
        p0_idx = min(pos, len(px.index) - 1); p1_idx = p0_idx + h_days
        if p1_idx >= len(px.index):
            continue
        out[dt] = (px.iloc[p1_idx] / px.iloc[p0_idx] - 1)
    return pd.DataFrame(out).T


def ic_series(sig, fwd, codes=None, min_n=8):
    """월별 횡단면 Spearman IC. codes = sub-sector 한정(None=전체)."""
    out = {}
    for dt in sig.index.intersection(fwd.index):
        sv = sig.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
        c = sv.index.intersection(rv.index)
        if codes is not None:
            c = c.intersection(codes)
        if len(c) < min_n:
            continue
        rho, _ = stats.spearmanr(sv.loc[c], rv.loc[c])
        if not np.isnan(rho):
            out[dt] = rho
    return pd.Series(out).sort_index()


def nw_se(x, lag):
    n = len(x)
    if n < 3:
        return np.nan
    e = x - x.mean(); var = (e @ e) / n
    for k in range(1, min(lag, n - 1) + 1):
        w = 1 - k / (lag + 1); var += 2 * w * (e[k:] @ e[:-k]) / n
    return float(np.sqrt(max(var, 1e-12) / n))


def n_eff_autocorr(x, max_lag=12):
    n = len(x)
    if n < 4:
        return float(n)
    e = x - x.mean(); v = (e @ e) / n
    if v <= 0:
        return float(n)
    s = 0.0
    for k in range(1, min(max_lag, n - 1) + 1):
        rk = (e[k:] @ e[:-k]) / n / v
        if rk <= 0:
            break
        s += (1 - k / (max_lag + 1)) * rk
    return float(n / (1 + 2 * s))


def wild_cluster_p(x, B=2000, seed=42):
    n = len(x)
    if n < 4:
        return np.nan
    rng = np.random.default_rng(seed)
    t_obs = abs(x.mean() / (x.std(ddof=1) / np.sqrt(n))) if x.std(ddof=1) > 0 else 0.0
    e = x - x.mean(); cnt = 0
    for _ in range(B):
        w = rng.choice([-1.0, 1.0], size=n)
        xb_null = w * e
        sb = xb_null.std(ddof=1)
        tb = abs(xb_null.mean() / (sb / np.sqrt(n))) if sb > 0 else 0.0
        if tb >= t_obs:
            cnt += 1
    return (cnt + 1) / (B + 1)


def block_boot_ci(x, block, B=2000, seed=42):
    rng = np.random.default_rng(seed); n = len(x)
    if n < block + 1:
        return (np.nan, np.nan)
    nb = int(np.ceil(n / block)); means = []
    for _ in range(B):
        starts = rng.integers(0, n - block + 1, size=nb)
        means.append(np.concatenate([x[s:s + block] for s in starts])[:n].mean())
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def measure_cell(ic, h_days, block_min=2):
    x = ic.values.astype(float); n = len(x)
    if n < 4:
        return {"n_months": n, "ic_mean": float(x.mean()) if n else np.nan, "status": "INSUFFICIENT(n<4)"}
    h_months = max(1, round(h_days / 21)); block = max(block_min, h_months)
    mean = float(x.mean()); se = nw_se(x, lag=h_months)
    t_nw = mean / se if (se and se > 0) else np.nan
    neff = n_eff_autocorr(x, max_lag=12); wc_p = wild_cluster_p(x); ci = block_boot_ci(x, block=block)
    powered = (n >= 24) and (neff >= 6)
    return {
        "n_months": n, "n_eff": round(neff, 1), "ic_mean": round(mean, 4),
        "t_nw_asymptotic": round(t_nw, 2) if not np.isnan(t_nw) else None,
        "wild_cluster_p": round(wc_p, 4) if not np.isnan(wc_p) else None,
        "ci95_block_boot": [round(ci[0], 4), round(ci[1], 4)] if not np.isnan(ci[0]) else None,
        "block": block,
        "status": "powered" if powered else ("underpowered" if n >= 12 else "INSUFFICIENT(n<12)"),
    }


def benjamini_yekutieli(pvals, q=0.10):
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    m = len(items)
    if m == 0:
        return {"m": 0, "note": "powered cell 0 → FDR family empty"}
    items.sort(key=lambda x: x[1])
    c_m = sum(1.0 / i for i in range(1, m + 1)); survivors = []
    for rank_i, (k, p) in enumerate(items, 1):
        if p <= (rank_i / m) * q / c_m:
            survivors = [items[j][0] for j in range(rank_i)]
    return {"m": m, "q": q, "by_factor": round(c_m, 3), "bonferroni_alpha": round(0.05 / m, 5),
            "survivors_BY": survivors, "raw_p_min": round(items[0][1], 5), "raw_p_min_key": items[0][0]}


def detect_signflip(surface):
    """family_2 트리거: 같은 신호×horizon×subsector 에서 regime cell 부호 갈리면 후보."""
    flips = []
    for skey, ssurf in surface.items():
        for sname, hd in ssurf.items():
            for hname, cells in hd.items():
                for axis in REGIME_AXES:
                    ac = {k: v for k, v in cells.items() if k.startswith(axis + "=")}
                    signs = {k: np.sign(v.get("ic_mean", 0)) for k, v in ac.items()
                             if v.get("ic_mean") is not None and v.get("status") in ("powered", "underpowered")}
                    pos = [k for k, s in signs.items() if s > 0]; neg = [k for k, s in signs.items() if s < 0]
                    if pos and neg:
                        flips.append({"subsector": skey, "signal": sname, "horizon": hname,
                                      "axis": axis, "positive": pos, "negative": neg})
    return {"n_flips": len(flips), "flips": flips}


def measure_interaction_terms(price_sigs, val_sigs, px, anchor, lab19, code_map,
                              dummy_regime, group_codes, horizon_d=20):
    """★family_2 interaction term (G-B 의무, frame A-5).
    pooled panel: ret_rank = a + b·sig_rank + c·(sig_rank × regime_dummy) + e. month-clustered SE.
    ★financial = rate_regime × signal (NIM conditional) + flow × value (밸류업 conditional)."""
    axis, rg_val = dummy_regime
    fwd = forward_returns_daily(px, anchor, horizon_d)
    all_sigs = {**price_sigs, **val_sigs}
    out = {"dummy": f"{axis}={rg_val}", "horizon_days": horizon_d,
           "method": "pooled panel, month-clustered SE", "group": group_codes is None and "ALL" or "subset",
           "results": []}
    for sname, sig in all_sigs.items():
        rows = []
        for dt in sig.index.intersection(fwd.index):
            if dt not in lab19.index or pd.isna(lab19.loc[dt, axis]):
                continue
            dum = 1.0 if lab19.loc[dt, axis] == rg_val else 0.0
            sv = sig.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
            common = sv.index.intersection(rv.index)
            if group_codes is not None:
                common = common.intersection(group_codes)
            if len(common) < 8:
                continue
            sr = (stats.rankdata(sv.loc[common]) / len(common) - 0.5)
            rr = (stats.rankdata(rv.loc[common]) / len(common) - 0.5)
            for i in range(len(common)):
                rows.append((dt, sr[i], rr[i], dum))
        if len(rows) < 80:
            out["results"].append({"signal": sname, "status": "INSUFFICIENT"})
            continue
        df = pd.DataFrame(rows, columns=["dt", "sig", "ret", "dum"])
        df["inter"] = df["sig"] * df["dum"]
        X = np.column_stack([np.ones(len(df)), df["sig"], df["inter"]]); y = df["ret"].values
        beta = np.linalg.lstsq(X, y, rcond=None)[0]; resid = y - X @ beta
        XtX_inv = np.linalg.inv(X.T @ X); meat = np.zeros((3, 3))
        for _, g in df.groupby("dt"):
            idx = df.index.isin(g.index); Xg = X[idx]; ug = resid[idx]
            meat += Xg.T @ np.outer(ug, ug) @ Xg
        V = XtX_inv @ meat @ XtX_inv; se = np.sqrt(np.diag(V))
        out["results"].append({
            "signal": sname, "b_main": round(beta[1], 4), "t_main": round(beta[1] / se[1], 2),
            "b_interaction": round(beta[2], 4), "t_interaction": round(beta[2] / se[2], 2),
            "n_obs": len(df), "n_months": int(df["dt"].nunique()),
            "verdict": "interaction 유의" if abs(beta[2] / se[2]) > 2 else "interaction 비유의",
        })
    return out


def main():
    px, lab, fin, uni = load()
    print(f"universe={px.shape[1]} codes  regime months={len(lab)}")
    code_map = uni["subcl"].to_dict()

    price_sigs = build_price_signals(px)
    val_sigs = build_valuation_signals(px, fin, uni)
    all_sigs = {**price_sigs, **val_sigs}
    print(f"signals: {list(all_sigs.keys())}")

    anchor = price_sigs["mom_6"].dropna(how="all").index
    lab19 = lab.loc["2019-01-01":]

    results = {"meta": {
        "universe_n": int(px.shape[1]),
        "date_range": [str(px.index.min().date()), str(px.index.max().date())],
        "gf_contract": "measure_conditional.py 헤더 7항 선언 참조",
        "horizons_days": HORIZONS_D,
        "regime_source": {
            "rate": "ECOS 817Y002 국고채3Y 6M Δ ±0.3%p (financial 특화 NIM driver)",
            "curve": "ECOS 국고채10Y-3Y term spread 1Y 분위 70%",
            "credit": "ECOS 회사채AA−-국고3Y spread 1Y 분위 70%",
            "macro": "FRED KORLOLITOAASTSAM CLI 4국면", "krw": "FRED DEXKOUS yoy ±5%",
            "flow": "ECOS 802Y001/0030000 외국인순매수 28d z ±1",
        },
        "subsector_groups": {k: (v or "ALL") for k, v in SUBSECTOR_GROUPS.items()},
        "subsector_note": "★frame §1.6 cancel 회피 — 은행/보험(금리+) vs 증권(금리−) 분리. ALL 약 → 분리 살아나면 cancel 입증.",
    }}

    # ── conditional IC surface (sub-sector × signal × horizon × regime) ──
    pvals_for_fdr = {}
    surface = {}
    for skey, scls in SUBSECTOR_GROUPS.items():
        gcodes = None if scls is None else [c for c, sc in code_map.items() if sc in scls]
        min_n = 8 if skey in ("ALL", "rate_POS") else 6  # 작은 sub-sector 완화
        surface[skey] = {}
        for sname, sig in all_sigs.items():
            surface[skey][sname] = {}
            for hname, h in HORIZONS_D.items():
                fwd = forward_returns_daily(px, anchor, h)
                ic_all = ic_series(sig, fwd, codes=gcodes, min_n=min_n)
                if len(ic_all) < 6:
                    continue
                uncond = measure_cell(ic_all, h)
                cb = {"unconditional": uncond}
                for axis in REGIME_AXES:
                    la = lab19[axis].dropna()
                    for rg in sorted(la.unique()):
                        months = la[la == rg].index
                        s2 = ic_all[ic_all.index.isin(months)]
                        if len(s2) >= 4:
                            cb[f"{axis}={rg}"] = measure_cell(s2, h)
                            m = cb[f"{axis}={rg}"]
                            if m.get("status") == "powered" and m.get("wild_cluster_p") is not None:
                                pvals_for_fdr[f"{skey}__{sname}__{hname}__{axis}={rg}"] = m["wild_cluster_p"]
                if uncond.get("status") == "powered" and uncond.get("wild_cluster_p") is not None:
                    pvals_for_fdr[f"{skey}__{sname}__{hname}__uncond"] = uncond["wild_cluster_p"]
                surface[skey][sname][hname] = cb
    results["conditional_ic_surface"] = surface

    # ── 단일 FDR family (BY) ──
    results["fdr_family"] = benjamini_yekutieli(pvals_for_fdr)
    # ── family_2 sign-flip ──
    results["family_2_signflip"] = detect_signflip(surface)

    # ── ★family_2 interaction TERM (G-B): financial 핵심 2 = rate×signal + flow×value ──
    bank_codes = [c for c, sc in code_map.items() if sc in ("bank", "insurance", "other_fin", "credit")]
    results["family_2_interaction_rate"] = measure_interaction_terms(
        price_sigs, val_sigs, px, anchor, lab19, code_map,
        dummy_regime=("rate_regime", "rate_up"), group_codes=bank_codes)  # 은행/보험 그룹 rate_up
    results["family_2_interaction_flow"] = measure_interaction_terms(
        price_sigs, val_sigs, px, anchor, lab19, code_map,
        dummy_regime=("flow_regime", "flow_strong_buy"), group_codes=None)  # 전체 밸류업 동조

    out = ROOT / "validation-conditional-v3.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved {out}")
    print_summary(results)
    return results


def print_summary(r):
    print("\n" + "=" * 78)
    print("CONDITIONAL IC SURFACE — y_20d, sub-sector별 powered cell (★cancel 점검)")
    print("=" * 78)
    for skey, ssurf in r["conditional_ic_surface"].items():
        print(f"\n##### sub-sector = {skey} #####")
        for sname, hd in ssurf.items():
            cells = hd.get("y_20d", {})
            unc = cells.get("unconditional", {})
            if not unc:
                continue
            print(f"[{sname}] uncond IC={unc.get('ic_mean')} (n={unc.get('n_months')}, wc_p={unc.get('wild_cluster_p')}, {unc.get('status')})")
            for ck, cv in cells.items():
                if ck == "unconditional" or cv.get("status") not in ("powered", "underpowered"):
                    continue
                star = "★" if cv.get("status") == "powered" else " "
                print(f"  {star}{ck:24s} IC={cv.get('ic_mean'):+.4f} n={cv.get('n_months'):2d} wc_p={cv.get('wild_cluster_p')} {cv.get('status')}")
    fdr = r["fdr_family"]
    print(f"\nFDR family (단일): m={fdr.get('m')} BY_survivors={fdr.get('survivors_BY')} raw_p_min={fdr.get('raw_p_min')}({fdr.get('raw_p_min_key')})")
    sf = r["family_2_signflip"]
    print(f"family_2 sign-flip: {sf['n_flips']} 건")
    for fi_name, fi_key in [("rate_up(은행/보험)", "family_2_interaction_rate"),
                            ("flow_strong_buy(전체)", "family_2_interaction_flow")]:
        fi = r.get(fi_key, {})
        print(f"\n★family_2 interaction TERM ({fi.get('dummy')}, {fi_name}):")
        for res in fi.get("results", []):
            if res.get("status") == "INSUFFICIENT":
                print(f"  {res['signal']:10s} INSUFFICIENT")
            else:
                print(f"  {res['signal']:10s} b_main={res['b_main']:+.4f}(t={res['t_main']:+.2f}) "
                      f"b_inter={res['b_interaction']:+.4f}(t={res['t_interaction']:+.2f}) {res['verdict']}")


if __name__ == "__main__":
    main()
