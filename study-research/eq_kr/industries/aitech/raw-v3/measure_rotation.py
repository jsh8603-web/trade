# -*- coding: utf-8 -*-
"""measure_rotation.py — ★AItech 업종 rotation 신호 측정 (어느 국면→AItech OW/UW).

team-lead 파이프라인: 이론(부호 사전확약) → 통계 검증(forward IC + OOS + G-G v2) → 채택판정.
  이론+통계 일치 = STRONG/TENTATIVE / 이론 반증 = REJECTED / 이론없이 통계만 = data-mining 채택불가.

★_rotation/measure_rotation_v2.py 미러 (aitech 단일 산업 + 고유 cycle 4종 + 좀비 마스킹).

================================================================================
★부호 사전확약 (rotation-signals.md §1, 데이터 접촉 前 동결 = PIT pre-commit):
  - rate_10y Δ → AItech forward = ★음 (growth/long-duration: 금리↑ → 멀티플 압축 약세). ★primary 이론.
  - nasdaq_qqq Δ → AItech forward = 양 (글로벌 tech cycle 동조). ★단 공통인자 재포장 의심 → residualize 후 잔존 점검.
  - ai_capex_nvda Δ → AItech forward = 양 (AI capex cycle 수혜). ★종목selection 에선 forward REJECTED.
  - soxx_semi Δ → AItech forward = 양 (반도체 cycle 연동) but 약 prior.
  - momentum (secondary) = 종목selection 에서 reversal(음) = growth continuation 반증. residualize 후 잔존 점검.
================================================================================

★G-F 7항 (measure_rotation_v2 준용): regime PIT lag / forward shift / 단일 FDR / MDE t_obs⋚2.802 /
  PIT(cycle spot 실시간, 가격 forward shift) / KR STT 0.2% / wild-cluster B=2000 + block-boot + eff-N.
★좀비 마스킹: 가격 패널 zombie(amt==0 OR 연속동일종가≥10일) NaN (G-C audit, 셀바스AI 284일 halt).
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
HORIZONS_M = {"y_20d": 1, "y_60d": 3}
OOS_SPLIT = "2023-01-01"
T_BREAKEVEN = 2.802
SEMI_PPI_LAG = 1

# ★부호 사전확약 (PIT, 데이터 접촉 전 동결)
PRIOR_SIGN = {
    "rate_10y": "음",       # growth duration: 금리↑ → AItech 약세 (★primary)
    "nasdaq_qqq": "양",     # 글로벌 tech cycle 동조 (공통인자 의심)
    "ai_capex_nvda": "양",  # AI capex cycle
    "soxx_semi": "양",      # 반도체 cycle 연동 (약 prior)
}


def nw_se(x, lag):
    n = len(x)
    if n < 3: return np.nan
    e = x - x.mean(); var = (e @ e) / n
    for k in range(1, min(lag, n - 1) + 1):
        var += 2 * (1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n
    return float(np.sqrt(max(var, 1e-12) / n))


def n_eff_autocorr(x, max_lag=12):
    n = len(x)
    if n < 4: return float(n)
    e = x - x.mean(); v = (e @ e) / n
    if v <= 0: return float(n)
    s = 0.0
    for k in range(1, min(max_lag, n - 1) + 1):
        rk = (e[k:] @ e[:-k]) / n / v
        if rk <= 0: break
        s += (1 - k / (max_lag + 1)) * rk
    return float(n / (1 + 2 * s))


def wild_cluster_p(x, B=2000, seed=42):
    n = len(x)
    if n < 4: return np.nan
    rng = np.random.default_rng(seed); sd = x.std(ddof=1)
    t_obs = abs(x.mean() / (sd / np.sqrt(n))) if sd > 0 else 0.0
    e = x - x.mean(); cnt = 0
    for _ in range(B):
        w = rng.choice([-1.0, 1.0], size=n); xn = w * e; sb = xn.std(ddof=1)
        tb = abs(xn.mean() / (sb / np.sqrt(n))) if sb > 0 else 0.0
        if tb >= t_obs: cnt += 1
    return (cnt + 1) / (B + 1)


def block_boot_ci(x, block, B=2000, seed=42):
    rng = np.random.default_rng(seed); n = len(x)
    if n < block + 1: return [np.nan, np.nan]
    nb = int(np.ceil(n / block)); means = []
    for _ in range(B):
        st = rng.integers(0, n - block + 1, size=nb)
        means.append(np.concatenate([x[s:s + block] for s in st])[:n].mean())
    return [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


def benjamini_yekutieli(pvals, q=0.10):
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    m = len(items)
    if m == 0: return {"m": 0, "note": "powered cell 0"}
    items.sort(key=lambda x: x[1])
    c_m = sum(1.0 / i for i in range(1, m + 1)); surv = []
    for ri, (k, p) in enumerate(items, 1):
        if p <= (ri / m) * q / c_m: surv = [items[j][0] for j in range(ri)]
    return {"m": m, "by_factor": round(c_m, 3), "survivors_BY": surv,
            "raw_p_min": round(items[0][1], 5), "raw_p_min_key": items[0][0], "bonferroni_alpha": round(0.05 / m, 5)}


def signal_forward_stat(sig, fwd, h_months, label, prior=None):
    common = sig.dropna().index.intersection(fwd.dropna().index)
    if len(common) < 12:
        return {"label": label, "n": len(common), "status": "INSUFFICIENT(n<12)"}
    sv, fv = sig.loc[common].values, fwd.loc[common].values
    rho, _ = stats.spearmanr(sv, fv)
    sr = stats.rankdata(sv) / len(sv) - 0.5; fr = stats.rankdata(fv) / len(fv) - 0.5
    prod = sr * fr; n = len(prod)
    neff = n_eff_autocorr(prod); se = nw_se(prod, h_months)
    t_nw = prod.mean() / se if se and se > 0 else np.nan
    wc_p = wild_cluster_p(prod); ci = block_boot_ci(prod, max(2, h_months))
    t_power = abs(rho) * np.sqrt(max(neff, 1.0))
    powered = (n >= 24) and (neff >= 6) and (t_power >= T_BREAKEVEN)
    is_idx = [d for d in common if str(d) < OOS_SPLIT]; oos_idx = [d for d in common if str(d) >= OOS_SPLIT]
    oos = {"is_n": len(is_idx), "oos_n": len(oos_idx)}
    if len(is_idx) >= 8 and len(oos_idx) >= 8:
        rho_is = stats.spearmanr(sig.loc[is_idx].values, fwd.loc[is_idx].values)[0]
        rho_oos = stats.spearmanr(sig.loc[oos_idx].values, fwd.loc[oos_idx].values)[0]
        oos.update({"rho_is": round(float(rho_is), 4), "rho_oos": round(float(rho_oos), 4)})
        sign_hold = (np.sign(rho_is) == np.sign(rho_oos)) and abs(rho_oos) >= 0.5 * abs(rho_is)
        oos["eligible"] = bool(sign_hold and abs(rho_oos) > 0.02)
        oos["verdict"] = ("OOS 부호+mag 유지" if sign_hold else
                          ("OOS 부호유지 mag약" if np.sign(rho_is) == np.sign(rho_oos) else "OOS flip"))
    else:
        oos["eligible"] = None; oos["verdict"] = "OOS n<8"
    out = {"label": label, "n": n, "n_eff": round(neff, 1), "spearman_rho": round(float(rho), 4),
           "t_power_mde": round(float(t_power), 2),
           "wild_cluster_p": round(wc_p, 4) if not np.isnan(wc_p) else None,
           "ci95_block_boot_prod": [round(c, 5) for c in ci] if not np.isnan(ci[0]) else None,
           "walk_forward_oos": oos, "status": "powered" if powered else ("underpowered" if n >= 12 else "INSUFFICIENT")}
    # ★부호 사전확약 일치 점검
    if prior:
        obs_sign = "양" if rho > 0 else "음"
        out["prior_sign"] = prior; out["obs_sign"] = obs_sign
        out["prior_match"] = (prior == obs_sign)
    return out


def zombie_mask(px, amt, dup_days=10):
    """G-C audit: 거래정지 carry-forward(셀바스AI 284일) NaN 마스킹."""
    amt_al = amt.reindex_like(px)
    zero_amt = (amt_al.fillna(0) == 0)
    same = px.eq(px.shift(1)); run = same.astype(float)
    for c in px.columns:
        s = same[c].values; cnt = 0; o = np.zeros(len(s))
        for i in range(len(s)):
            cnt = cnt + 1 if s[i] else 0; o[i] = cnt
        run[c] = o
    return px.mask(zero_amt | (run >= dup_days))


def main():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    amt = pd.read_parquet(DATA / "amount.parquet"); amt.index = pd.to_datetime(amt.index)
    rs = pd.read_parquet(DATA / "regime_series.parquet"); rs.index = pd.to_datetime(rs.index)
    cyc = pd.read_parquet(DATA / "cycle_aitech.parquet"); cyc.index = pd.to_datetime(cyc.index)

    # ★좀비 마스킹 후 업종 eq-weight 월수익
    px_clean = zombie_mask(px, amt)
    pret = px_clean.resample("ME").last().pct_change().mean(axis=1, skipna=True).loc["2019-01-01":]
    cum = (1 + pret.fillna(0)).cumprod()

    # 공통인자 (residualize): usdkrw Δ + foreign flow + semi_ppi yoy
    rsm = rs.resample("ME").last()
    F = pd.DataFrame(index=rsm.index)
    F["d_usdkrw"] = rsm["usdkrw"].pct_change()
    F["foreign"] = rsm["foreign_net_kospi"]
    if "semi_ppi" in rsm.columns:
        F["semi_ppi_yoy"] = rsm["semi_ppi"].shift(SEMI_PPI_LAG).pct_change(12)
    # residualized 업종수익 (idiosyncratic)
    commonF = pret.dropna().index.intersection(F.dropna().index)
    resid_ret = pret.copy()
    if len(commonF) >= 20:
        yy = pret.loc[commonF].values
        X = np.column_stack([np.ones(len(commonF))] + [F.loc[commonF, c].values for c in F.columns])
        beta = np.linalg.lstsq(X, yy, rcond=None)[0]
        resid_ret = pd.Series(yy - X @ beta, index=commonF)
    resid_cum = (1 + resid_ret.fillna(0)).cumprod()

    cycm = cyc.resample("ME").last()
    results = {"meta": {
        "industry": "aitech",
        "method": "AItech 업종 rotation: primary=고유 cycle 직접신호(AI capex/금리/나스닥/반도체) + secondary=momentum(raw+residualized)",
        "prior_signs": PRIOR_SIGN,
        "residualize": "업종 월수익 ~ {d_usdkrw, foreign_flow, semi_ppi_yoy} OLS 잔차 = idiosyncratic (공통인자 재포장 점검)",
        "zombie_mask": "가격 패널 amt==0 OR 연속동일종가≥10일 NaN (G-C audit, 셀바스AI 284일 halt)",
        "horizons_months": HORIZONS_M, "oos_split": OOS_SPLIT, "t_breakeven": T_BREAKEVEN,
        "n_months": int(pret.dropna().shape[0]),
    }, "primary_cycle": {}, "secondary_momentum": {}}
    fdr_all = {}

    # ───── PRIMARY: AItech 고유 cycle 직접신호 ─────
    for col in cyc.columns:
        base = cycm[col]
        prior = PRIOR_SIGN.get(col)
        # cycle 신호 변형: Δ3M(모멘텀) + (금리는 level Δ가 본질, 나머지 yoy도)
        sigs = {f"{col}_d3": base.pct_change(3) if col != "rate_10y" else base.diff(3),
                f"{col}_yoy": base.pct_change(12) if col != "rate_10y" else base.diff(12)}
        for signame, sigser in sigs.items():
            sigser = sigser.loc["2019-01-01":]
            for hl, hm in HORIZONS_M.items():
                fwd = cum.pct_change(hm).shift(-hm)
                st = signal_forward_stat(sigser, fwd, hm, f"aitech__cycle_{signame}__{hl}", prior=prior)
                results["primary_cycle"][f"{signame}__{hl}"] = st
                if st.get("status") in ("powered", "underpowered") and st.get("wild_cluster_p") is not None:
                    fdr_all[f"cyc_{signame}__{hl}"] = st["wild_cluster_p"]

    # ───── SECONDARY: momentum (raw + residualized) ─────
    for tag, c in [("raw", cum), ("resid", resid_cum)]:
        for mname, lookback in [("mom_3", 3), ("mom_6", 6)]:
            sig = c.pct_change(lookback).loc["2019-01-01":]
            for hl, hm in HORIZONS_M.items():
                fwd = cum.pct_change(hm).shift(-hm)
                st = signal_forward_stat(sig, fwd, hm, f"aitech__mom_{tag}_{mname}__{hl}")
                results["secondary_momentum"][f"{tag}_{mname}__{hl}"] = st
                if st.get("status") in ("powered", "underpowered") and st.get("wild_cluster_p") is not None:
                    fdr_all[f"mom_{tag}_{mname}__{hl}"] = st["wild_cluster_p"]

    results["fdr_all_single"] = benjamini_yekutieli(fdr_all)
    out = ROOT / "validation-rotation-v1.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Saved {out}\n")
    print_summary(results)
    return results


def print_summary(r):
    print("=" * 84)
    print("★AItech PRIMARY cycle 직접신호 (부호 사전확약 점검 + OOS)")
    print("=" * 84)
    for k, st in r["primary_cycle"].items():
        if not isinstance(st, dict) or "spearman_rho" not in st: continue
        oos = st.get("walk_forward_oos", {})
        match = st.get("prior_match")
        m = "✓일치" if match else ("✗반증" if match is False else "-")
        flag = "★" if (oos.get("eligible") and st.get("wild_cluster_p", 1) < 0.10) else " "
        print(f" {flag}{k:26s} rho={st['spearman_rho']:+.3f}({st.get('obs_sign')}/{st.get('prior_sign')}{m}) "
              f"wc_p={st.get('wild_cluster_p')} OOS{oos.get('rho_is')}->{oos.get('rho_oos')}({oos.get('verdict','')}) {st['status'][:4]}")
    print("\n" + "=" * 84)
    print("★SECONDARY momentum (raw vs residualized — 공통인자 재포장 점검)")
    print("=" * 84)
    for k, st in r["secondary_momentum"].items():
        if "spearman_rho" not in st: continue
        oos = st.get("walk_forward_oos", {})
        print(f"  {k:24s} rho={st['spearman_rho']:+.3f} wc_p={st.get('wild_cluster_p')} "
              f"OOS{oos.get('rho_is')}->{oos.get('rho_oos')}({oos.get('verdict','')}) {st['status'][:4]}")
    print(f"\nFDR all single: {json.dumps(r['fdr_all_single'], ensure_ascii=False)}")


if __name__ == "__main__":
    main()
