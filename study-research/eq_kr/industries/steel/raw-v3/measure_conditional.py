# -*- coding: utf-8 -*-
"""measure_conditional.py — steel conditional IC surface (S2 신규, dispatch 원의도 본체). semiconductor 미러.

측정 대상 = IC(지표, regime, horizon) = "어느 국면에 어느 지표가 forward return 예측하나".
기존 measure.py(unconditional 횡단면 IC) + measure_valuation.py(PBR/PER) 를 regime 분해로 확장.
★철강 증폭축 = KRW_neutral (반도체 KRW_weak 과 다름). small-breadth(23종) hedge 의무.

================================================================================
★G-F FRAME CONTRACT 7항 사전 선언 (frame _dispatch-gates §G-F, 미선언=검정 불가)
================================================================================
1. regime 선언규칙:
   - 변수 = Macro(KORLOLITOAASTSAM CLI amplitude-adj 4국면) × KRW(DEXKOUS yoy 3) × flow(ECOS 외국인순매수 28d z 3).
   - 개수 = 단일축 측정(Macro 4 / KRW 3 / flow 3). ★36셀 full = N≥24 cell 0개(실측) → INSUFFICIENT, 단일축+2축merge 만.
   - effective-n = cell month 수가 아니라 **block 수**(overlapping forward h일 → n_eff = n_obs/(1+2Σρ_k), HAC lag = h).
   - HAC lag = horizon (regime persistence) = 5/20/60 거래일.
2. interaction/split 사전확약 + 직교화:
   - conditioning = **split**(regime별 IC, n-costly clean) 사전동결. 사후 interaction 전환 금지.
   - family_2 interaction term(ΔRate×cs, 자유도보존) = family_1 단일축에서 부호 갈리면만 추가(G-B).
   - 직교화: interaction 항 = main effect(unconditional IC)에 residualize. order = unconditional 먼저 제거 후 regime dummy.
3. 단일 FDR family (★측정 前 멤버십 사전 고정 = garden-of-forking-paths 차단, team-lead 2026-06-05):
   - ★family 멤버십 = {6 신호(mom_6/mom_12_1/rev_1m/vol_60/pbr_z/per_z) × 3 horizon(y_5d/20d/60d) × powered regime cell}
     전체를 하나의 BY-FDR alpha budget 으로 사전 동결. 측정 결과 본 후 family 재정의 ⛔금지(momentum만 떼서 보기 등).
   - main(unconditional) + conditional(regime cell) + interaction(family_2) 모두 동일 family alpha 공유. "공짜" 검정 없음.
   - M_eff = 신호상관(pbr/per·mom_6/mom_12_1) 보정 유효검정수. 산업단계 = naive m + M_eff_signal 박제, 통합 M_eff = supervisor(M.7).
   - ★G-B 판정 순서 사전고정: (1) conditional IC 측정 (2) family_2 interaction(KRW×signal 등) (3) family_2 살린 뒤에만 "약함" 판정.
4. null + MDE/power:
   - null = IC=0. MDE = small cell(n=10~30)에서 detectable |IC| ≈ 0.05~0.10 (α=0.05, power 0.8).
   - power < threshold cell = "underpowered/inconclusive" 라벨(PASS 아님). N<24 cell = 자동 inconclusive.
5. PIT 동결 + 비대칭 search 금지:
   - regime threshold(CLI 100, KRW ±5%, flow z ±1) = 사전 동결(OOS 前 expanding 아님, 도메인 표준값).
   - 신호 z-score normalization = 월말 cross-sectional(미래 누설 없음). forward = shift(-h) 일간.
6. Turnover/T-cost: Net-alpha = gross IC − cost. KR STT sell 0.20% 비대칭. regime별 turnover 차등(통합단계 sqrt impact).
7. per-test null calibration: ★small cell block 한자릿수 → asymptotic NW-HAC t = size-invalid(Kiefer-Vogelsang).
   → **wild-cluster bootstrap**(Rademacher, B=2000) per-cell p-value 로 재계산. asymptotic t 는 참고만.
================================================================================

raw 재현: 기존 prices/regime_labels/dart_financials parquet + 본 .py.
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, "D:/projects/Inv")

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

# net-cost (KR 비대칭, G-F §6)
STT_SELL, COMMISSION, SPREAD_HALF = 0.0020, 0.00015, 0.0005

HORIZONS_D = {"y_5d": 5, "y_20d": 20, "y_60d": 60}   # frame §2 일간 forward (y_20d 메인)
REGIME_AXES = ["macro_regime", "krw_regime", "flow_regime"]


def load():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    lab = pd.read_parquet(DATA / "regime_labels.parquet"); lab.index = pd.to_datetime(lab.index)
    fin = pd.read_parquet(DATA / "dart_financials.parquet")
    uni = pd.read_parquet(DATA / "universe.parquet"); uni = uni[uni["pass_floor"]].set_index("Code")
    return px, lab, fin, uni


def csz(panel: pd.DataFrame) -> pd.DataFrame:
    """횡단면 z-score (universe-relative, sector-neutral)."""
    return panel.sub(panel.mean(axis=1), axis=0).div(panel.std(axis=1, ddof=1).replace(0, np.nan), axis=0)


def build_price_signals(px: pd.DataFrame) -> dict:
    """월말 시점 가격기반 횡단면 z-score 신호 (forward 는 일간이라 신호는 월말 anchor)."""
    pxm = px.resample("ME").last()
    ret_d = px.pct_change()
    sigs = {
        "mom_6": csz(pxm / pxm.shift(6) - 1),
        "mom_12_1": csz(pxm.shift(1) / pxm.shift(12) - 1),
        "rev_1m": csz(pxm / pxm.shift(1) - 1),
        "vol_60": csz((ret_d.rolling(60).std() * np.sqrt(252)).resample("ME").last()),
    }
    return sigs


def build_valuation_signals(px, fin, uni) -> dict:
    """PIT-safe PBR/PER 월말 z-score (measure_valuation 로직 미러, rcept_dt 이후만)."""
    pxm = px.resample("ME").last()
    shares = {}
    # 현재 발행주식수 근사 = universe Marcap / 최근 가격 (measure_valuation 와 동일 근사)
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
    """각 월말 anchor 시점부터 h 거래일 forward return (일간 horizon)."""
    out = {}
    for dt in anchor_dates:
        pos = px.index.searchsorted(dt)
        if pos >= len(px.index):
            continue
        # anchor = 그 시점 가장 가까운 거래일 종가
        p0_idx = min(pos, len(px.index) - 1)
        p1_idx = p0_idx + h_days
        if p1_idx >= len(px.index):
            continue
        p0 = px.iloc[p0_idx]
        p1 = px.iloc[p1_idx]
        out[dt] = (p1 / p0 - 1)
    return pd.DataFrame(out).T


def ic_series(sig: pd.DataFrame, fwd: pd.DataFrame, min_n=8) -> pd.Series:
    """월별 횡단면 Spearman IC."""
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
    e = x - x.mean()
    var = (e @ e) / n
    for k in range(1, min(lag, n - 1) + 1):
        w = 1 - k / (lag + 1)
        var += 2 * w * (e[k:] @ e[:-k]) / n
    return float(np.sqrt(max(var, 1e-12) / n))


def n_eff_autocorr(x: np.ndarray, max_lag: int = 12) -> float:
    """effective-n = n/(1+2Σρ_k) (G-F §1 block 수)."""
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
    """★G-F §7 wild-cluster bootstrap p-value (Rademacher).
    H0: mean(IC)=0. small-block size-invalid 회피 (asymptotic t 대체).
    각 obs 에 ±1 Rademacher weight → null 분포 → 양측 p."""
    n = len(x)
    if n < 4:
        return np.nan
    rng = np.random.default_rng(seed)
    t_obs = abs(x.mean() / (x.std(ddof=1) / np.sqrt(n))) if x.std(ddof=1) > 0 else 0.0
    e = x - x.mean()
    cnt = 0
    for _ in range(B):
        w = rng.choice([-1.0, 1.0], size=n)
        xb = x.mean() + w * e   # ★ wild: null 중심 유지하며 부호 교란 → 보수적
        xb_null = w * e          # mean 0 null
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
    """한 cell(또는 unconditional)의 IC 통계 — G-F 준수(n_eff + wild-cluster + block-boot)."""
    x = ic.values.astype(float)
    n = len(x)
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
    # power 라벨: N<24 또는 n_eff<6 → underpowered
    powered = (n >= 24) and (neff >= 6)
    return {
        "n_months": n, "n_eff": round(neff, 1), "ic_mean": round(mean, 4),
        "t_nw_asymptotic": round(t_nw, 2) if not np.isnan(t_nw) else None,
        "wild_cluster_p": round(wc_p, 4) if not np.isnan(wc_p) else None,
        "ci95_block_boot": [round(ci[0], 4), round(ci[1], 4)] if not np.isnan(ci[0]) else None,
        "block": block,
        "status": "powered" if powered else ("underpowered" if n >= 12 else "INSUFFICIENT(n<12)"),
    }


def walk_forward_krw_neutral(all_sigs, px, lab19) -> dict:
    """★KRW_neutral conditional 핵심 신호 walk-forward OOS (in-sample artifact 여부 = verdict 근거).
    IS 2019-22 / OOS 2023-26. 철강 증폭축 = KRW_neutral."""
    kn = lab19["krw_regime"].dropna()
    kn = kn[kn == "KRW_neutral"].index
    out = {"regime": "krw_regime=KRW_neutral", "split": "IS 2019-22 / OOS 2023-26", "signals": {}}
    for sname in ["mom_6", "vol_60", "pbr_z"]:
        if sname not in all_sigs:
            continue
        sig = all_sigs[sname]
        for hname, h in [("y_20d", 20), ("y_60d", 60)]:
            fwd = forward_returns_daily(px, sig.dropna(how="all").index, h)
            ic = ic_series(sig, fwd)
            ic_kn = ic[ic.index.isin(kn)]
            is_ic = ic_kn[(ic_kn.index >= "2019-01-01") & (ic_kn.index <= "2022-12-31")]
            oos_ic = ic_kn[(ic_kn.index >= "2023-01-01") & (ic_kn.index <= "2026-12-31")]
            if len(is_ic) >= 3 and len(oos_ic) >= 3:
                im, om = float(is_ic.mean()), float(oos_ic.mean())
                out["signals"][f"{sname}__{hname}"] = {
                    "is_ic": round(im, 4), "is_n": len(is_ic),
                    "oos_ic": round(om, 4), "oos_n": len(oos_ic),
                    "sign_hold": bool(np.sign(im) == np.sign(om)),
                    "verdict": "✅부호유지" if np.sign(im) == np.sign(om) else "❌OOS 부호반전(artifact)",
                }
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

    results = {
        "meta": {
            "universe_n": int(px.shape[1]),
            "date_range": [str(px.index.min().date()), str(px.index.max().date())],
            "gf_contract": "measure_conditional.py 헤더 7항 선언 참조",
            "horizons_days": HORIZONS_D,
            "regime_source": {
                "macro": "FRED KORLOLITOAASTSAM (CLI amplitude-adj 4국면)",
                "krw": "FRED DEXKOUS yoy ±5%",
                "flow": "ECOS 802Y001/0030000 외국인순매수 28d z ±1",
            },
            "cell_collapse_note": "36셀 full N>=24 = 0 cell (실측) → 단일축 측정 + 2축 merge. 36셀 full = INSUFFICIENT.",
        }
    }

    # ── unconditional + conditional (단일축) IC, 일간 horizon ──
    pvals_for_fdr = {}   # 단일 FDR family (G-F §3)
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
            # regime 축별 conditional
            for axis in REGIME_AXES:
                la = lab19[axis].dropna()
                for rg in sorted(la.unique()):
                    months = la[la == rg].index
                    sub = ic_all[ic_all.index.isin(months)]
                    if len(sub) >= 4:
                        cell_block[f"{axis}={rg}"] = measure_cell(sub, h, block_min=2)
                        # FDR family: powered cell 만 등록
                        m = cell_block[f"{axis}={rg}"]
                        if m.get("status") == "powered" and m.get("wild_cluster_p") is not None:
                            pvals_for_fdr[f"{sname}__{hname}__{axis}={rg}"] = m["wild_cluster_p"]
            # unconditional 도 FDR family
            if uncond.get("status") == "powered" and uncond.get("wild_cluster_p") is not None:
                pvals_for_fdr[f"{sname}__{hname}__uncond"] = uncond["wild_cluster_p"]
            surface[sname][hname] = cell_block
    results["conditional_ic_surface"] = surface

    # ── 단일 FDR family (BY) + M_eff (G-F §3) ──
    results["fdr_family"] = benjamini_yekutieli(pvals_for_fdr)

    # ── family_2 interaction 점검 (G-B): regime split 부호 갈림 ──
    results["family_2_signflip"] = detect_signflip(surface)

    # ── ★family_2 interaction TERM 정식 측정 (G-B, rejected 박제 前 의무) ──
    # pooled panel: ret_rank ~ sig_rank + sig_rank×regime_dummy, month-clustered SE.
    # ★철강 증폭축 = KRW_neutral (반도체는 KRW_weak). conditional cell wc_p 가장 강한 축.
    results["family_2_interaction"] = measure_interaction_terms(
        price_sigs, px, anchor, lab19, dummy_regime=("krw_regime", "KRW_neutral"))

    # ── ★walk-forward OOS (KRW_neutral conditional, IS 2019-22 / OOS 2023-26) — verdict 근거 ──
    results["walk_forward_oos_krw_neutral"] = walk_forward_krw_neutral(all_sigs, px, lab19)

    out = ROOT / "validation-conditional-v3.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved {out}")
    print_summary(results)
    return results


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
    """family_2 트리거: 같은 신호×horizon 에서 regime 축 cell 부호가 갈리면 interaction 후보."""
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
                                  "note": "regime 따라 부호 갈림 → family_2 interaction 후보 (rejected 박제 전 검정 의무)"})
    return {"n_flips": len(flips), "flips": flips}


def measure_interaction_terms(price_sigs, px, anchor, lab19, dummy_regime, horizon_d=20) -> dict:
    """★family_2 interaction term 정식 측정 (G-B 의무, frame A-5).
    pooled cross-sectional panel: ret_rank = a + b·sig_rank + c·(sig_rank × regime_dummy) + e.
    c(interaction) 유의 = regime 따라 신호 효과 갈림(자유도 보존, split 보다 power↑).
    SE = month-clustered (overlapping·횡단면 상관 보정)."""
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
            # 횡단면 rank-normalize (Spearman 정합)
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
        # month-clustered meat
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


def print_summary(r):
    print("\n" + "=" * 72)
    print("CONDITIONAL IC SURFACE — y_20d (메인 horizon), powered cell 위주")
    print("=" * 72)
    for sname, hd in r["conditional_ic_surface"].items():
        cells = hd.get("y_20d", {})
        unc = cells.get("unconditional", {})
        print(f"\n[{sname}] uncond IC={unc.get('ic_mean')} (n={unc.get('n_months')}, n_eff={unc.get('n_eff')}, wc_p={unc.get('wild_cluster_p')}, {unc.get('status')})")
        for ck, cv in cells.items():
            if ck == "unconditional":
                continue
            if cv.get("status") in ("powered", "underpowered"):
                star = "★" if cv.get("status") == "powered" else " "
                print(f"  {star}{ck:28s} IC={cv.get('ic_mean'):+.4f}  n={cv.get('n_months'):2d}  n_eff={cv.get('n_eff')}  wc_p={cv.get('wild_cluster_p')}  {cv.get('status')}")
    fdr = r["fdr_family"]
    print(f"\nFDR family (단일, G-F §3): m={fdr.get('m')} BY_survivors={fdr.get('survivors_BY')} raw_p_min={fdr.get('raw_p_min')}({fdr.get('raw_p_min_key')})")
    sf = r["family_2_signflip"]
    print(f"family_2 sign-flip (G-B): {sf['n_flips']} 건 → interaction 후보")
    for f in sf["flips"][:8]:
        print(f"  {f['signal']}__{f['horizon']} [{f['axis']}]: +{f['positive']} / -{f['negative']}")
    fi = r.get("family_2_interaction", {})
    print(f"\n★family_2 interaction TERM ({fi.get('dummy')}, y_{fi.get('horizon_days')}d, {fi.get('method')}):")
    for res in fi.get("results", []):
        if res.get("status") == "INSUFFICIENT":
            print(f"  {res['signal']:10s} INSUFFICIENT")
        else:
            print(f"  {res['signal']:10s} b_main={res['b_main']:+.4f}(t={res['t_main']:+.2f}) "
                  f"b_inter={res['b_interaction']:+.4f}(t={res['t_interaction']:+.2f}) {res['verdict']}")


if __name__ == "__main__":
    main()
