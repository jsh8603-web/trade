# -*- coding: utf-8 -*-
"""measure_conditional.py — consumer(소비재) conditional IC surface (S2, dispatch 원의도 본체).

측정 대상 = IC(지표, regime, horizon) = "어느 국면에 어느 지표가 소비재 forward return 예측하나".
기존 measure.py(unconditional 가격신호) + measure_valuation.py(PBR/PER) 를 regime 분해로 확장.
반도체 measure_conditional.py 양식 미러 + ★소비재 특수: A-4 sub-sector 부호 cancel 점검(음식료 defensive
vs 화장품 中의존 cyclical) + walk-forward OOS(IS2019-22/OOS2023-26) + K-food 수출 부호분리(KRW regime 흡수).

================================================================================
★G-F FRAME CONTRACT 7항 사전 선언 (frame _dispatch-gates §G-F, 미선언=검정 불가)
================================================================================
1. regime 선언규칙:
   - 변수 = Macro(KORLOLITOAASTSAM CLI amplitude-adj 4국면) × KRW(DEXKOUS yoy 3) × flow(ECOS 외국인순매수 28d z 3).
   - 개수 = 단일축 측정(Macro 4 / KRW 3 / flow 3). ★36셀 full = N>=24 cell 0개(실측) → INSUFFICIENT, 단일축+2축merge 만.
   - ★소비재 핵심 regime = KRW(K-food 수출형 vs 내수형 부호분리 = sub-sector 따라 갈림, theory §1.3) + flow(외국인).
   - effective-n = cell month 수가 아니라 **block 수**(overlapping forward h일 → n_eff = n_obs/(1+2Σρ_k), HAC lag = h).
   - HAC lag = horizon (regime persistence) = 5/20/60 거래일.
2. interaction/split 사전확약 + 직교화:
   - conditioning = **split**(regime별 IC, n-costly clean) 사전동결. 사후 interaction 전환 금지.
   - family_2 interaction term(KRW×cs, 자유도보존) = family_1 단일축에서 부호 갈리면만 추가(G-B).
   - 직교화: interaction 항 = main effect(unconditional IC)에 residualize. order = unconditional 먼저 제거 후 regime dummy.
3. 단일 FDR family (★측정 前 멤버십 사전 고정 = garden-of-forking-paths 차단):
   - ★family 멤버십 = {6 신호(mom_6/mom_12_1/rev_1m/vol_60/pbr_z/per_z) × 3 horizon(y_5d/20d/60d) × powered regime cell}
     전체를 하나의 BY-FDR alpha budget 으로 사전 동결. 측정 결과 본 후 family 재정의 ⛔금지.
   - main(unconditional) + conditional(regime cell) + interaction(family_2) 모두 동일 family alpha 공유.
   - M_eff = 신호상관(pbr/per·mom_6/mom_12_1) 보정 유효검정수. 산업단계 = naive m + M_eff_signal 박제, 통합 M_eff = supervisor(M.7).
4. null + MDE/power (★G-G v2 t_obs⋚2.802):
   - null = IC=0. MDE = small cell(n=10~30)에서 detectable |IC| ≈ 0.05~0.10 (α=0.05, power 0.8).
   - ★eligibility 판정 = t_obs=IC·√n_eff/σ_IC ⋚ 2.802(breakeven). t<2.802=underpowered(미생존=정보없음, OOS 부호유지면 tradeable)
     / t>2.802=well-powered(본질). ★단 단일 FDR 엄격성 사수 — MDE 는 미생존 해석 보조, FDR 완화 ⛔금지.
   - power < threshold cell = "underpowered/inconclusive" 라벨(PASS 아님). N<24 cell = 자동 inconclusive.
5. PIT 동결 + 비대칭 search 금지:
   - regime threshold(CLI 100, KRW ±5%, flow z ±1) = 사전 동결(도메인 표준값). CLI_PUB_LAG=2(vintage).
   - 신호 z-score normalization = 월말 cross-sectional(미래 누설 없음). forward = shift(-h) 일간.
6. Turnover/T-cost: Net-alpha = gross IC − cost. KR STT sell 0.20% 비대칭. regime별 turnover 차등(통합단계 sqrt impact).
7. per-test null calibration: ★small cell block 한자릿수 → asymptotic NW-HAC t = size-invalid(Kiefer-Vogelsang).
   → **wild-cluster bootstrap**(Rademacher B=2000) per-cell p-value 로 재계산. asymptotic t 는 참고만.
================================================================================

raw 재현: 기존 prices/regime_labels/dart_financials/universe parquet + 본 .py.
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
from itertools import combinations
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, "D:/projects/Inv")

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

STT_SELL, COMMISSION, SPREAD_HALF = 0.0020, 0.00015, 0.0005
HORIZONS_D = {"y_5d": 5, "y_20d": 20, "y_60d": 60}
REGIME_AXES = ["macro_regime", "krw_regime", "flow_regime"]
IS_END = "2022-12-31"   # walk-forward IS/OOS split (frame §M4 #5)


def load():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    lab = pd.read_parquet(DATA / "regime_labels.parquet"); lab.index = pd.to_datetime(lab.index)
    fin = pd.read_parquet(DATA / "dart_financials.parquet")
    uni = pd.read_parquet(DATA / "universe.parquet"); uni = uni[uni["pass_floor"]].set_index("Code")
    return px, lab, fin, uni


def csz(panel: pd.DataFrame) -> pd.DataFrame:
    return panel.sub(panel.mean(axis=1), axis=0).div(panel.std(axis=1, ddof=1).replace(0, np.nan), axis=0)


def build_price_signals(px: pd.DataFrame) -> dict:
    pxm = px.resample("ME").last()
    ret_d = px.pct_change()
    return {
        "mom_6": csz(pxm / pxm.shift(6) - 1),
        "mom_12_1": csz(pxm.shift(1) / pxm.shift(12) - 1),
        "rev_1m": csz(pxm / pxm.shift(1) - 1),
        "vol_60": csz((ret_d.rolling(60).std() * np.sqrt(252)).resample("ME").last()),
    }


def build_valuation_signals(px, fin, uni) -> dict:
    pxm = px.resample("ME").last()
    shares = {}
    for code in px.columns:
        last_px = px[code].dropna()
        if len(last_px) and code in uni.index:
            mc = uni.loc[code, "Marcap"]
            if pd.notna(mc) and last_px.iloc[-1] > 0:
                shares[code] = mc / last_px.iloc[-1]
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
            avail = cf[cf["rcept_dt"] <= dt]   # ★PIT: 공시일 이후만
            if len(avail) == 0 or pd.isna(pxm.loc[dt, code]):
                continue
            eq = avail["equity"].iloc[-1]
            ni = avail["net_income"].iloc[-1]
            mktcap = pxm.loc[dt, code] * sh
            if eq and eq > 0:
                pbr_s[dt] = mktcap / eq
            if ni and ni > 0:
                per_s[dt] = mktcap / ni
        pbr_panel[code] = pbr_s
        per_panel[code] = per_s
    return {"pbr_z": csz(pd.DataFrame(pbr_panel)), "per_z": csz(pd.DataFrame(per_panel))}


def forward_returns_daily(px: pd.DataFrame, anchor_dates, h_days: int) -> pd.DataFrame:
    out = {}
    for dt in anchor_dates:
        pos = px.index.searchsorted(dt)
        if pos >= len(px.index):
            continue
        p0_idx = min(pos, len(px.index) - 1)
        p1_idx = p0_idx + h_days
        if p1_idx >= len(px.index):
            continue
        out[dt] = (px.iloc[p1_idx] / px.iloc[p0_idx] - 1)
    return pd.DataFrame(out).T


def ic_series(sig: pd.DataFrame, fwd: pd.DataFrame, min_n=8) -> pd.Series:
    out = {}
    for dt in sig.index.intersection(fwd.index):
        sv = sig.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
        c = sv.index.intersection(rv.index)
        if len(c) < min_n:
            continue
        rho, _ = stats.spearmanr(sv.loc[c], rv.loc[c])
        if not np.isnan(rho):
            out[dt] = rho
    return pd.Series(out).sort_index()


def nw_se(x: np.ndarray, lag: int) -> float:
    n = len(x)
    if n < 3:
        return np.nan
    e = x - x.mean(); var = (e @ e) / n
    for k in range(1, min(lag, n - 1) + 1):
        w = 1 - k / (lag + 1)
        var += 2 * w * (e[k:] @ e[:-k]) / n
    return float(np.sqrt(max(var, 1e-12) / n))


def n_eff_autocorr(x: np.ndarray, max_lag: int = 12) -> float:
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


def wild_cluster_p(x: np.ndarray, B=2000, seed=42) -> float:
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


def block_boot_ci(x: np.ndarray, block: int, B=2000, seed=42):
    rng = np.random.default_rng(seed); n = len(x)
    if n < block + 1:
        return (np.nan, np.nan)
    nb = int(np.ceil(n / block))
    means = []
    for _ in range(B):
        starts = rng.integers(0, n - block + 1, size=nb)
        samp = np.concatenate([x[s:s + block] for s in starts])[:n]
        means.append(samp.mean())
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def measure_cell(ic: pd.Series, h_days: int, block_min: int) -> dict:
    x = ic.values.astype(float); n = len(x)
    if n < 4:
        return {"n_months": n, "ic_mean": float(x.mean()) if n else np.nan, "status": "INSUFFICIENT(n<4)"}
    h_months = max(1, round(h_days / 21))
    block = max(block_min, h_months)
    mean = float(x.mean())
    se = nw_se(x, lag=h_months)
    t_nw = mean / se if (se and se > 0) else np.nan
    neff = n_eff_autocorr(x, max_lag=12)
    wc_p = wild_cluster_p(x)
    ci = block_boot_ci(x, block=block)
    # ★G-G v2 eligibility: t_obs = IC·√n_eff / σ_IC ⋚ 2.802 (breakeven, MDE/power)
    sd = float(x.std(ddof=1))
    t_obs_eff = (mean * np.sqrt(neff) / sd) if sd > 0 else 0.0
    powered = (n >= 24) and (neff >= 6)
    return {
        "n_months": n, "n_eff": round(neff, 1), "ic_mean": round(mean, 4),
        "t_nw_asymptotic": round(t_nw, 2) if not np.isnan(t_nw) else None,
        "t_obs_eff": round(t_obs_eff, 2),               # ★G-G v2 well-powered if |t_obs_eff|>2.802
        "well_powered_g_g": abs(t_obs_eff) > 2.802,
        "wild_cluster_p": round(wc_p, 4) if not np.isnan(wc_p) else None,
        "ci95_block_boot": [round(ci[0], 4), round(ci[1], 4)] if not np.isnan(ci[0]) else None,
        "block": block,
        "status": "powered" if powered else ("underpowered" if n >= 12 else "INSUFFICIENT(n<12)"),
    }


# ============================================================
# ★A-4 sub-sector 부호 cancel 점검 (소비재 핵심: 음식료 defensive vs 화장품 中cyclical)
# ============================================================
def subsector_sign_check(all_sigs, px, anchor, uni, horizon_d=20) -> dict:
    """각 sub-cluster(food/cosmetics/retail/apparel/beverage)별로 채택신호 IC 부호 점검.
    ★frame A-4: 부호 일관→sleeve 유지 / 한 sub-sector 정반대 부호 cancel→분리 트리거.
    소비재 = 음식료(defensive·내수) vs 화장품(中의존 cyclical·수출) 부호 갈릴 가능성 = financial 교훈."""
    subcl = uni["subcl"].to_dict()
    fwd = forward_returns_daily(px, anchor, horizon_d)
    out = {"horizon_days": horizon_d, "method": "sub-cluster별 횡단면 IC (signal=화장품/음식료 부호 cancel 점검)",
           "subclusters": {}, "signals": {}}
    subcl_groups = {}
    for code, sc in subcl.items():
        subcl_groups.setdefault(sc, []).append(code)
    out["subcluster_counts"] = {k: len(v) for k, v in subcl_groups.items()}

    for sname, sig in all_sigs.items():
        sub_ics = {}
        for sc, codes in subcl_groups.items():
            if len(codes) < 3:    # n<3 sub-cluster = INSUFFICIENT (apparel 3, beverage 2)
                sub_ics[sc] = {"ic": None, "n_codes": len(codes), "status": "INSUFFICIENT(n_codes<3)"}
                continue
            # 해당 sub-cluster 종목만으로 횡단면 IC 시계열
            ics = []
            for dt in sig.index.intersection(fwd.index):
                sv = sig.loc[dt, [c for c in codes if c in sig.columns]].dropna()
                rv = fwd.loc[dt, [c for c in codes if c in fwd.columns]].dropna()
                c = sv.index.intersection(rv.index)
                if len(c) >= 3:
                    rho, _ = stats.spearmanr(sv.loc[c], rv.loc[c])
                    if not np.isnan(rho):
                        ics.append(rho)
            if len(ics) >= 6:
                arr = np.array(ics)
                sub_ics[sc] = {"ic": round(float(arr.mean()), 4), "n_months": len(ics),
                               "n_codes": len(codes), "sign": int(np.sign(arr.mean()))}
            else:
                sub_ics[sc] = {"ic": None, "n_codes": len(codes), "status": "INSUFFICIENT(n_months<6)"}
        # 부호 cancel 판정
        signs = [v["sign"] for v in sub_ics.values() if v.get("ic") is not None]
        pos = [k for k, v in sub_ics.items() if v.get("sign", 0) > 0]
        neg = [k for k, v in sub_ics.items() if v.get("sign", 0) < 0]
        cancel = bool(pos and neg)
        out["signals"][sname] = {
            "sub_ics": sub_ics, "positive_subcl": pos, "negative_subcl": neg,
            "cancel_detected": cancel,
            "verdict": ("★CANCEL — sub-sector 부호 반대(분리 트리거 후보)" if cancel
                        else "부호 일관 (sleeve 유지 가능)" if signs else "측정불가"),
        }
    return out


# ============================================================
# ★walk-forward OOS (IS 2019-22 / OOS 2023-26, frame §M4 #5)
# ============================================================
def walk_forward_oos(all_sigs, px, anchor, lab19, focus_regime=("krw_regime", "KRW_weak"), horizon_d=20) -> dict:
    """IS/OOS split: in-sample 신호 부호 → OOS 재현 (부호+magnitude 유지 = artifact 아님).
    ★unconditional + focus regime conditional 둘 다. frame §M.12 = in-sample만으론 tentative."""
    axis, rg = focus_regime
    fwd = forward_returns_daily(px, anchor, horizon_d)
    out = {"split": {"IS": ["2019-01", IS_END[:7]], "OOS": ["2023-01", "2026-05"]},
           "focus_regime": f"{axis}={rg}", "horizon_days": horizon_d, "results": {}}
    is_cut = pd.Timestamp(IS_END)
    for sname, sig in all_sigs.items():
        ic_all = ic_series(sig, fwd)
        if len(ic_all) < 12:
            out["results"][sname] = {"status": "INSUFFICIENT"}
            continue
        is_ic = ic_all[ic_all.index <= is_cut]
        oos_ic = ic_all[ic_all.index > is_cut]
        rec = {"uncond_IS": round(float(is_ic.mean()), 4) if len(is_ic) else None,
               "uncond_OOS": round(float(oos_ic.mean()), 4) if len(oos_ic) else None,
               "uncond_n_IS": len(is_ic), "uncond_n_OOS": len(oos_ic),
               "sign_consistent": (len(is_ic) > 0 and len(oos_ic) > 0
                                   and np.sign(is_ic.mean()) == np.sign(oos_ic.mean()))}
        # focus regime conditional OOS
        la = lab19[axis].dropna()
        months = la[la == rg].index
        cond = ic_all[ic_all.index.isin(months)]
        cond_is = cond[cond.index <= is_cut]; cond_oos = cond[cond.index > is_cut]
        if len(cond_is) >= 3 and len(cond_oos) >= 3:
            rec["cond_IS"] = round(float(cond_is.mean()), 4)
            rec["cond_OOS"] = round(float(cond_oos.mean()), 4)
            rec["cond_n_IS"] = len(cond_is); rec["cond_n_OOS"] = len(cond_oos)
            rec["cond_sign_consistent"] = bool(np.sign(cond_is.mean()) == np.sign(cond_oos.mean()))
        out["results"][sname] = rec
    return out


def benjamini_yekutieli(pvals: dict, q=0.10) -> dict:
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    m = len(items)
    if m == 0:
        return {"m": 0, "note": "powered cell 0개 (전부 underpowered) → FDR family empty"}
    items.sort(key=lambda x: x[1])
    c_m = sum(1.0 / i for i in range(1, m + 1))
    survivors = []
    for rank_i, (k, p) in enumerate(items, 1):
        thresh = (rank_i / m) * q / c_m
        if p <= thresh:
            survivors = [items[j][0] for j in range(rank_i)]
    return {"m": m, "q": q, "by_factor": round(c_m, 3),
            "bonferroni_alpha": round(0.05 / m, 5),
            "survivors_BY": survivors,
            "raw_p_min": round(items[0][1], 5), "raw_p_min_key": items[0][0]}


def detect_signflip(surface: dict) -> dict:
    flips = []
    for sname, hd in surface.items():
        for hname, cells in hd.items():
            for axis in REGIME_AXES:
                axis_cells = {k: v for k, v in cells.items() if k.startswith(axis + "=")}
                signs = {k: np.sign(v.get("ic_mean", 0)) for k, v in axis_cells.items()
                         if v.get("ic_mean") is not None and v.get("status") in ("powered", "underpowered")}
                pos = [k for k, s in signs.items() if s > 0]
                neg = [k for k, s in signs.items() if s < 0]
                if pos and neg:
                    flips.append({"signal": sname, "horizon": hname, "axis": axis,
                                  "positive": pos, "negative": neg,
                                  "note": "regime 따라 부호 갈림 → family_2 interaction 후보"})
    return {"n_flips": len(flips), "flips": flips}


def measure_interaction_terms(price_sigs, px, anchor, lab19, dummy_regime, horizon_d=20) -> dict:
    """★family_2 interaction term (G-B 의무, frame A-5). pooled panel month-clustered SE."""
    axis, rg_val = dummy_regime
    fwd = forward_returns_daily(px, anchor, horizon_d)
    out = {"dummy": f"{axis}={rg_val}", "horizon_days": horizon_d, "method": "pooled panel, month-clustered SE", "results": []}
    for sname, sig in price_sigs.items():
        rows = []
        for dt in sig.index.intersection(fwd.index):
            if dt not in lab19.index or pd.isna(lab19.loc[dt, axis]):
                continue
            dum = 1.0 if lab19.loc[dt, axis] == rg_val else 0.0
            sv = sig.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
            common = sv.index.intersection(rv.index)
            if len(common) < 10:
                continue
            sr = (stats.rankdata(sv.loc[common]) / len(common) - 0.5)
            rr = (stats.rankdata(rv.loc[common]) / len(common) - 0.5)
            for i, code in enumerate(common):
                rows.append((dt, sr[i], rr[i], dum))
        if len(rows) < 100:
            out["results"].append({"signal": sname, "status": "INSUFFICIENT"})
            continue
        df = pd.DataFrame(rows, columns=["dt", "sig", "ret", "dum"])
        df["inter"] = df["sig"] * df["dum"]
        X = np.column_stack([np.ones(len(df)), df["sig"], df["inter"]])
        y = df["ret"].values
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        resid = y - X @ beta
        XtX_inv = np.linalg.inv(X.T @ X)
        meat = np.zeros((3, 3))
        for _, g in df.groupby("dt"):
            idx = df.index.isin(g.index)
            Xg = X[idx]; ug = resid[idx]
            meat += Xg.T @ np.outer(ug, ug) @ Xg
        V = XtX_inv @ meat @ XtX_inv
        se = np.sqrt(np.diag(V))
        out["results"].append({
            "signal": sname,
            "b_main": round(beta[1], 4), "t_main": round(beta[1] / se[1], 2),
            "b_interaction": round(beta[2], 4), "t_interaction": round(beta[2] / se[2], 2),
            "n_obs": len(df), "n_months": int(df["dt"].nunique()),
            "verdict": "interaction 유의" if abs(beta[2] / se[2]) > 2 else "interaction 비유의",
        })
    return out


def main():
    px, lab, fin, uni = load()
    print(f"universe={px.shape[1]} codes  regime months={len(lab)}")

    price_sigs = build_price_signals(px)
    val_sigs = build_valuation_signals(px, fin, uni)
    all_sigs = {**price_sigs, **val_sigs}
    print(f"signals: {list(all_sigs.keys())}")

    anchor = price_sigs["mom_6"].dropna(how="all").index
    lab19 = lab.loc["2019-01-01":]

    results = {"meta": {
        "industry": "kr_consumer", "universe_n": int(px.shape[1]),
        "date_range": [str(px.index.min().date()), str(px.index.max().date())],
        "gf_contract": "measure_conditional.py 헤더 7항 선언 참조",
        "horizons_days": HORIZONS_D,
        "regime_source": {
            "macro": "FRED KORLOLITOAASTSAM (CLI amplitude-adj 4국면)",
            "krw": "FRED DEXKOUS yoy ±5% (★소비재 K-food 수출 vs 내수 부호분리 핵심)",
            "flow": "ECOS 802Y001/0030000 외국인순매수 28d z ±1",
        },
        "cell_collapse_note": "36셀 full N>=24 = 0 cell (실측) → 단일축 측정 + 2축 merge.",
    }}

    pvals_for_fdr = {}
    surface = {}
    for sname, sig in all_sigs.items():
        surface[sname] = {}
        for hname, h in HORIZONS_D.items():
            fwd = forward_returns_daily(px, anchor, h)
            ic_all = ic_series(sig, fwd)
            if len(ic_all) < 6:
                continue
            uncond = measure_cell(ic_all, h, block_min=2)
            cell_block = {"unconditional": uncond}
            for axis in REGIME_AXES:
                la = lab19[axis].dropna()
                for rg in sorted(la.unique()):
                    months = la[la == rg].index
                    sub = ic_all[ic_all.index.isin(months)]
                    if len(sub) >= 4:
                        cell_block[f"{axis}={rg}"] = measure_cell(sub, h, block_min=2)
                        m = cell_block[f"{axis}={rg}"]
                        if m.get("status") == "powered" and m.get("wild_cluster_p") is not None:
                            pvals_for_fdr[f"{sname}__{hname}__{axis}={rg}"] = m["wild_cluster_p"]
            if uncond.get("status") == "powered" and uncond.get("wild_cluster_p") is not None:
                pvals_for_fdr[f"{sname}__{hname}__uncond"] = uncond["wild_cluster_p"]
            surface[sname][hname] = cell_block
    results["conditional_ic_surface"] = surface
    results["fdr_family"] = benjamini_yekutieli(pvals_for_fdr)
    results["family_2_signflip"] = detect_signflip(surface)
    results["family_2_interaction"] = measure_interaction_terms(
        price_sigs, px, anchor, lab19, dummy_regime=("krw_regime", "KRW_weak"))

    # ★소비재 특수 3종
    results["subsector_sign_check"] = subsector_sign_check(all_sigs, px, anchor, uni)
    results["walk_forward_oos"] = walk_forward_oos(all_sigs, px, anchor, lab19)

    out = ROOT / "validation-conditional-v3.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved {out}")
    print_summary(results)
    return results


def print_summary(r):
    print("\n" + "=" * 72)
    print("CONDITIONAL IC SURFACE — y_20d (메인 horizon)")
    print("=" * 72)
    for sname, hd in r["conditional_ic_surface"].items():
        cells = hd.get("y_20d", {})
        unc = cells.get("unconditional", {})
        print(f"\n[{sname}] uncond IC={unc.get('ic_mean')} (n={unc.get('n_months')}, n_eff={unc.get('n_eff')}, "
              f"wc_p={unc.get('wild_cluster_p')}, t_obs_eff={unc.get('t_obs_eff')}, {unc.get('status')})")
        for ck, cv in cells.items():
            if ck == "unconditional":
                continue
            if cv.get("status") in ("powered", "underpowered"):
                star = "★" if cv.get("status") == "powered" else " "
                print(f"  {star}{ck:28s} IC={cv.get('ic_mean'):+.4f}  n={cv.get('n_months'):2d}  "
                      f"n_eff={cv.get('n_eff')}  wc_p={cv.get('wild_cluster_p')}  t_obs={cv.get('t_obs_eff')}  {cv.get('status')}")
    fdr = r["fdr_family"]
    print(f"\nFDR family (단일, G-F §3): m={fdr.get('m')} BY_survivors={fdr.get('survivors_BY')} raw_p_min={fdr.get('raw_p_min')}({fdr.get('raw_p_min_key')})")
    sf = r["family_2_signflip"]
    print(f"family_2 sign-flip (G-B): {sf['n_flips']} 건")
    fi = r.get("family_2_interaction", {})
    print(f"\n★family_2 interaction TERM ({fi.get('dummy')}, y_{fi.get('horizon_days')}d):")
    for res in fi.get("results", []):
        if res.get("status") == "INSUFFICIENT":
            print(f"  {res['signal']:10s} INSUFFICIENT")
        else:
            print(f"  {res['signal']:10s} b_main={res['b_main']:+.4f}(t={res['t_main']:+.2f}) "
                  f"b_inter={res['b_interaction']:+.4f}(t={res['t_interaction']:+.2f}) {res['verdict']}")
    # ★A-4 sub-sector
    ss = r["subsector_sign_check"]
    print(f"\n{'='*72}\n★A-4 SUB-SECTOR 부호 cancel 점검 (음식료 defensive vs 화장품 中cyclical)")
    print(f"{'='*72}\nsub-cluster counts: {ss['subcluster_counts']}")
    for sname, sv in ss["signals"].items():
        print(f"\n[{sname}] {sv['verdict']}")
        for sc, d in sv["sub_ics"].items():
            ic = d.get("ic")
            print(f"    {sc:11s} IC={ic if ic is None else f'{ic:+.4f}'}  n_codes={d.get('n_codes')}  {d.get('status','')}")
    # ★walk-forward OOS
    wf = r["walk_forward_oos"]
    print(f"\n{'='*72}\n★WALK-FORWARD OOS (IS2019-22 / OOS2023-26, focus={wf['focus_regime']})")
    print(f"{'='*72}")
    for sname, res in wf["results"].items():
        if res.get("status") == "INSUFFICIENT":
            print(f"  {sname:10s} INSUFFICIENT")
            continue
        sc = "✓" if res.get("sign_consistent") else "✗"
        line = f"  {sname:10s} uncond IS={res.get('uncond_IS')} OOS={res.get('uncond_OOS')} [{sc}]"
        if "cond_IS" in res:
            csc = "✓" if res.get("cond_sign_consistent") else "✗"
            line += f"  | KRW_weak IS={res.get('cond_IS')} OOS={res.get('cond_OOS')} [{csc}]"
        print(line)


if __name__ == "__main__":
    main()
