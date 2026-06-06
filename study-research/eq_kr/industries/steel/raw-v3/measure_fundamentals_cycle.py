# -*- coding: utf-8 -*-
"""measure_fundamentals_cycle.py — 철강 신규 cycle 지표 forward IC 측정 (S2, ★이연 금지). semiconductor 미러. ★capex_ratio = dispatch 최우선.

사용자 박제: 신규 발굴 지표(재고/CAPEX/R&D) 지금 측정 + verdict 박제(tentative라도) + 현 가능 검증 전부.

신호 (DART dart_extended.parquet, PIT rcept_dt 이후만):
  - inv_ratio    = 재고자산/총자산 (재고순환, ★음 prior: 高재고→주가 양forward, Chen-NovyMarx-Zhang 2010)
  - inv_yoy      = 재고자산 yoy (재고 증가율, 음 prior)
  - capex_ratio  = 유형자산/총자산 (asset growth, ★음 prior: 과잉투자, Cooper-Gulen-Schill 2008)
  - ppe_yoy      = 유형자산 yoy (CAPEX cycle, 음 prior)
  - rnd_ratio    = 무형자산/총자산 (R&D proxy, ★양 prior: 기술경쟁력)

측정 = cross-sectional z → forward IC (horizon y_5d/20d/60d 일간) + regime conditional + G-F(wild-cluster).
★분기 빈도 → 월말 forward-fill (rcept_dt PIT). G-F 7항 = measure_conditional.py 헤더 준용(단일 FDR family 합산은 supervisor).
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


def csz(panel):
    return panel.sub(panel.mean(axis=1), axis=0).div(panel.std(axis=1, ddof=1).replace(0, np.nan), axis=0)


def nw_se(x, lag):
    n = len(x)
    if n < 3:
        return np.nan
    e = x - x.mean(); var = (e @ e) / n
    for k in range(1, min(lag, n - 1) + 1):
        var += 2 * (1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n
    return float(np.sqrt(max(var, 1e-12) / n))


def wild_cluster_p(x, B=2000, seed=42):
    n = len(x)
    if n < 4:
        return np.nan
    rng = np.random.default_rng(seed)
    t_obs = abs(x.mean() / (x.std(ddof=1) / np.sqrt(n))) if x.std(ddof=1) > 0 else 0.0
    e = x - x.mean(); cnt = 0
    for _ in range(B):
        w = rng.choice([-1.0, 1.0], size=n)
        xn = w * e; sb = xn.std(ddof=1)
        tb = abs(xn.mean() / (sb / np.sqrt(n))) if sb > 0 else 0.0
        if tb >= t_obs:
            cnt += 1
    return (cnt + 1) / (B + 1)


def block_boot_ci(x, block=3, B=2000, seed=42):
    rng = np.random.default_rng(seed); n = len(x)
    if n < block + 1:
        return [np.nan, np.nan]
    nb = int(np.ceil(n / block)); means = []
    for _ in range(B):
        st = rng.integers(0, n - block + 1, size=nb)
        means.append(np.concatenate([x[s:s + block] for s in st])[:n].mean())
    return [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


def build_fundamental_panel(ext, px, monthly_idx):
    """PIT-safe 분기 펀더멘털 → 월말 패널 (rcept_dt 이후만, forward-fill)."""
    ext = ext.copy()
    ext["rcept_dt"] = pd.to_datetime(ext["rcept_dt"], format="%Y%m%d", errors="coerce")
    ext = ext.dropna(subset=["rcept_dt"])
    sigs = {"inv_ratio": {}, "inv_yoy": {}, "capex_ratio": {}, "ppe_yoy": {}, "rnd_ratio": {}}
    for code in px.columns:
        cf = ext[ext["code"] == code].sort_values("rcept_dt")
        if len(cf) < 4:
            continue
        # 시계열(연도 기준 yoy 용)
        cf = cf.drop_duplicates(subset=["rcept_dt"], keep="last")
        # ★yoy = year-quarter 매칭 (분기 누락 robust, iloc[-5] 대신 (year-1, 같은 quarter) lookup)
        cf_key = cf.set_index(["year", "quarter"]) if {"year", "quarter"}.issubset(cf.columns) else None
        s_inv_r = pd.Series(index=monthly_idx, dtype=float)
        s_inv_y = pd.Series(index=monthly_idx, dtype=float)
        s_cap_r = pd.Series(index=monthly_idx, dtype=float)
        s_ppe_y = pd.Series(index=monthly_idx, dtype=float)
        s_rnd_r = pd.Series(index=monthly_idx, dtype=float)
        for dt in monthly_idx:
            av = cf[cf["rcept_dt"] <= dt]   # ★PIT
            if len(av) == 0:
                continue
            last = av.iloc[-1]
            assets = last.get("assets")
            if assets and assets > 0:
                if pd.notna(last.get("inventory")):
                    s_inv_r[dt] = last["inventory"] / assets
                if pd.notna(last.get("ppe")):
                    s_cap_r[dt] = last["ppe"] / assets
                if pd.notna(last.get("intangible")):
                    s_rnd_r[dt] = last["intangible"] / assets
            # ★yoy = year-quarter 매칭 (분기 누락 robust): (현재 year-1, 같은 quarter) lookup
            if cf_key is not None:
                cur_y, cur_q = last["year"], last["quarter"]
                try:
                    prev_row = cf_key.loc[(cur_y - 1, cur_q)]
                    if hasattr(prev_row, "iloc"):  # 중복 시 첫 행
                        prev_row = prev_row.iloc[0] if prev_row.ndim > 1 else prev_row
                    cur_inv, prev_inv = last.get("inventory"), prev_row.get("inventory")
                    if cur_inv and prev_inv and prev_inv > 0:
                        s_inv_y[dt] = cur_inv / prev_inv - 1
                    cur_ppe, prev_ppe = last.get("ppe"), prev_row.get("ppe")
                    if cur_ppe and prev_ppe and prev_ppe > 0:
                        s_ppe_y[dt] = cur_ppe / prev_ppe - 1
                except (KeyError, TypeError):
                    pass
        sigs["inv_ratio"][code] = s_inv_r
        sigs["inv_yoy"][code] = s_inv_y
        sigs["capex_ratio"][code] = s_cap_r
        sigs["ppe_yoy"][code] = s_ppe_y
        sigs["rnd_ratio"][code] = s_rnd_r
    return {k: csz(pd.DataFrame(v)) for k, v in sigs.items()}


def forward_daily(px, anchor, h):
    out = {}
    for dt in anchor:
        pos = px.index.searchsorted(dt)
        if pos + h < len(px.index):
            out[dt] = px.iloc[pos + h] / px.iloc[min(pos, len(px.index) - 1)] - 1
    return pd.DataFrame(out).T


def ic_series(sig, fwd, min_n=8):
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


def measure_cell(ic, h_days):
    x = ic.values.astype(float); n = len(x)
    if n < 4:
        return {"n": n, "ic_mean": round(float(x.mean()), 4) if n else None, "status": "INSUFFICIENT"}
    h_m = max(1, round(h_days / 21))
    mean = float(x.mean()); se = nw_se(x, h_m)
    return {"n": n, "ic_mean": round(mean, 4),
            "t_nw_asymptotic": round(mean / se, 2) if se and se > 0 else None,
            "wild_cluster_p": round(wild_cluster_p(x), 4),
            "ci95_block_boot": [round(v, 4) for v in block_boot_ci(x, max(2, h_m))],
            "status": "powered" if n >= 24 else ("underpowered" if n >= 12 else "INSUFFICIENT")}


PRIOR = {"inv_ratio": "음", "inv_yoy": "음", "capex_ratio": "음", "ppe_yoy": "음", "rnd_ratio": "양"}
HORIZONS = {"y_5d": 5, "y_20d": 20, "y_60d": 60}


def main():
    ext_path = DATA / "dart_extended.parquet"
    if not ext_path.exists():
        print("dart_extended.parquet 없음 — collect_dart_extended.py 먼저 실행"); return
    ext = pd.read_parquet(ext_path)
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    lab = pd.read_parquet(DATA / "regime_labels.parquet"); lab.index = pd.to_datetime(lab.index)
    pxm = px.resample("ME").last()
    print(f"dart_extended: {len(ext)} rows {ext['code'].nunique()} codes")
    cov = ext[["inventory", "ppe", "intangible", "cogs"]].notna().mean()
    print("coverage:", cov.round(2).to_dict())

    sigs = build_fundamental_panel(ext, px, pxm.index)
    # ★DRAM ASP 신호 추가 (반도체 PPI yoy = 메모리 cycle 직접, 수집완료 regime_series). cross-sectional 아닌 산업 cycle = 시점 공통 → 종목 신호 X.
    # DRAM ASP 는 regime/timing 신호라 cross-sectional IC 부적합 → regime conditioning 변수로만 활용(별 측정), 본 파일 = 종목 cross-sectional 펀더멘털 only.
    lab19 = lab.loc["2019-01-01":]
    results = {"meta": {"source": "DART dart_extended.parquet (재고/유형/무형자산 PIT rcept_dt)",
                        "priors": PRIOR, "horizons": HORIZONS,
                        "regime_axes": "Macro4 × KRW3 × flow3 (measure_conditional 동일, 단일 FDR family 합산용)",
                        "note": "신규 cycle 지표(★이연 금지). 분기→월말 PIT forward-fill. G-F wild-cluster. 같은 conditional 양식(regime×horizon)."},
               "indicators": {}}
    pvals_fundamentals = {}   # ★신규지표 → 단일 FDR family 합산용 (team-lead 순서3)
    for sname, sig in sigs.items():
        cov_cells = int(sig.notna().sum().sum())
        results["indicators"][sname] = {"prior_부호": PRIOR[sname], "panel_cells": cov_cells, "horizons": {}}
        for hname, h in HORIZONS.items():
            fwd = forward_daily(px, sig.dropna(how="all").index, h)
            ic = ic_series(sig, fwd)
            if len(ic) < 6:
                results["indicators"][sname]["horizons"][hname] = {"status": "INSUFFICIENT(IC n<6)"}
                continue
            uncond = measure_cell(ic, h)
            cell = {"unconditional": uncond}
            if uncond.get("status") == "powered" and uncond.get("wild_cluster_p") is not None:
                pvals_fundamentals[f"{sname}__{hname}__uncond"] = uncond["wild_cluster_p"]
            # ★3축 regime conditional (measure_conditional 양식 동일)
            for axis in ["macro_regime", "krw_regime", "flow_regime"]:
                la = lab19[axis].dropna()
                for rg in sorted(la.unique()):
                    months = la[la == rg].index
                    sub = ic[ic.index.isin(months)]
                    if len(sub) >= 4:
                        c = measure_cell(sub, h)
                        cell[f"{axis}={rg}"] = c
                        if c.get("status") == "powered" and c.get("wild_cluster_p") is not None:
                            pvals_fundamentals[f"{sname}__{hname}__{axis}={rg}"] = c["wild_cluster_p"]
            # ★walk-forward OOS (team-lead: 신규지표도 IS/OOS split verdict)
            is_ic = ic[(ic.index >= "2019-01-01") & (ic.index <= "2022-12-31")]
            oos_ic = ic[(ic.index >= "2023-01-01") & (ic.index <= "2026-12-31")]
            if len(is_ic) >= 3 and len(oos_ic) >= 3:
                im, om = float(is_ic.mean()), float(oos_ic.mean())
                cell["walk_forward"] = {
                    "is_ic": round(im, 4), "is_n": len(is_ic),
                    "oos_ic": round(om, 4), "oos_n": len(oos_ic),
                    "sign_hold": bool(np.sign(im) == np.sign(om)),
                    "verdict": ("OOS 부호유지" if np.sign(im) == np.sign(om) else "OOS 부호반전(artifact)"),
                }
            results["indicators"][sname]["horizons"][hname] = cell

    # ★단일 FDR family 합산 (team-lead 순서3): 기존 가격/valuation family(m=105) + 신규지표 = 통합 m
    results["fdr_family_fundamentals_only"] = _by(pvals_fundamentals)
    results["fdr_family_note"] = ("★신규지표 powered cell = 별 산출. 통합 단일 FDR family(가격+valuation+신규) = "
                                  "supervisor 통합단계 합산(m_total = 105 + 신규 powered). 산업단계 = 각 family + 통합 m 박제.")
    results["fundamentals_pvals"] = pvals_fundamentals   # 통합 family 합산 입력

    out = ROOT / "validation-fundamentals-cycle-v3.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved {out}")
    print("\n=== 신규 cycle 지표 forward IC (y_20d, uncond + KRW_weak) ===")
    for sname, d in results["indicators"].items():
        h20 = d["horizons"].get("y_20d", {})
        u = h20.get("unconditional", {})
        kw = h20.get("krw_regime=KRW_weak", {})
        print(f"  {sname:12s} (prior {d['prior_부호']}): uncond IC={u.get('ic_mean')} wc_p={u.get('wild_cluster_p')} n={u.get('n')} {u.get('status')} | "
              f"KRW_weak IC={kw.get('ic_mean')} n={kw.get('n')} | panel {d['panel_cells']}")
    print(f"\nFDR family (신규지표 only): {results['fdr_family_fundamentals_only']}")


def _by(pvals, q=0.10):
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    m = len(items)
    if m == 0:
        return {"m": 0, "note": "powered cell 0"}
    items.sort(key=lambda x: x[1])
    c_m = sum(1.0 / i for i in range(1, m + 1))
    surv = []
    for ri, (k, p) in enumerate(items, 1):
        if p <= (ri / m) * q / c_m:
            surv = [items[j][0] for j in range(ri)]
    return {"m": m, "by_factor": round(c_m, 3), "survivors_BY": surv,
            "raw_p_min": round(items[0][1], 5), "raw_p_min_key": items[0][0]}


if __name__ == "__main__":
    main()
