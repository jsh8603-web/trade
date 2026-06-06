# -*- coding: utf-8 -*-
"""measure_rotation.py — bio 업종 ROTATION 신호 (산업 OW/UW timing, v2 data-gate 재검).

★team-lead 지시(2026-06-06): v2 rotation-analyst 가 bio 를 NO_DIRECT_CYCLE + momentum OOS flip = FAIL/
  data-gate 판정. 내(bio 전문) 이론으로 재검 = ★거시 overlay 신호(금리 duration/환율/글로벌바이오 ETF 상대)를
  bio 업종 timing 신호로 측정. v2 는 momentum 만 봤고 macro overlay 미측정 = 핵심 누락.

측정 대상 = bio 업종 forward return(20d/60d, eq-weight strict 화이트리스트 패널) vs 거시지표 시계열.
  ⛔ 종목 cross-sectional 아님(그건 selection capsule). ★업종 자체 OW/UW timing.

================================================================================
★이론 부호 사전확약 (theory-notes §3 + 증권사 바이오 리포트, HARKing 방지, 측정 前 동결)
  bio = growth / long-duration cashflow(10-15년 R&D) → discount-rate sensitive.
================================================================================
| 신호 | 이론 부호 | 메커니즘 |
| us_10y_d (US 10Y Δ)      | 음(-) | growth duration: 금리↑ → 장기 cashflow 할인↑ → bio UW (theory §3.2) |
| kr_10y_d (KR 10Y Δ)      | 음(-) | 국내 금리 duration 동일 |
| us_curve (10Y-2Y)        | 양(+) | steepening = 경기회복/risk-on → 성장주 bio OW (보조) |
| xbi_rel_mom (XBI/SPY 상대모멘텀) | 양(+) | 글로벌 바이오 강세 → 한국 bio 동조 OW (글로벌 cycle 전이) |
| ibb_rel_mom (IBB/NDX 상대모멘텀) | 양(+) | 나스닥 대비 바이오 강세 = 섹터 로테이션 유입 |
| xbi_mom (XBI 절대 모멘텀)  | 양(+) | 글로벌 바이오 ETF 모멘텀 = 산업 cycle proxy |
| usdkrw_d (원/달러 Δ)      | 약/불확정 | 수출주(삼바/셀트리온)는 약세수혜 but round-1 USDKRW REJECTED = 약 prior |
| vix_level (VIX)          | 음(-) | bio 고베타(β=+0.011 t=6.03) → risk-off(VIX↑) 시 UW |
| credit_hy (HY OAS)       | 음(-) | risk-off proxy → 성장주 bio UW |
| fda_yoy (FDA 승인 yoy)    | 양(+) | 신약 cycle peak → 한국 license-out 환경/sentiment ↑ (theory §3.4) |
================================================================================

★G-F 7항: forward=shift(-h). per-test wild-cluster(B=2000) + block-boot CI + eff-N. 단일 FDR family.
★좀비 NaN 마스킹(mask_trading_halt) = bio-audit remediation 필수(코오롱티슈진/케어젠 carry-forward).
★strict 바이오 화이트리스트 패널(삼바/셀트리온/SK바이오팜/유한양행 등 floor 38종).
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
HORIZONS_D = {"y_20d": 20, "y_60d": 60}
OOS_SPLIT = "2023-01-01"
T_BREAKEVEN = 2.802


def mask_trading_halt(px, min_run=10):
    """★거래정지 좀비 carry-forward NaN 마스킹 (bio-audit remediation)."""
    out = px.copy()
    for code in px.columns:
        valid = px[code].dropna()
        if len(valid) < min_run + 1:
            continue
        same = valid.diff() == 0
        grp = (~same).cumsum()
        run_len = same.groupby(grp).transform("sum")
        out.loc[run_len[run_len >= (min_run - 1)].index, code] = np.nan
    return out


def nw_se(x, lag):
    n = len(x)
    if n < 3:
        return np.nan
    e = x - x.mean(); var = (e @ e) / n
    for k in range(1, min(lag, n - 1) + 1):
        var += 2 * (1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n
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
    rng = np.random.default_rng(seed); sd = x.std(ddof=1)
    t_obs = abs(x.mean() / (sd / np.sqrt(n))) if sd > 0 else 0.0
    e = x - x.mean(); cnt = 0
    for _ in range(B):
        w = rng.choice([-1.0, 1.0], size=n); xn = w * e; sb = xn.std(ddof=1)
        tb = abs(xn.mean() / (sb / np.sqrt(n))) if sb > 0 else 0.0
        if tb >= t_obs:
            cnt += 1
    return (cnt + 1) / (B + 1)


def block_boot_ci(x, block, B=2000, seed=42):
    rng = np.random.default_rng(seed); n = len(x)
    if n < block + 1:
        return [np.nan, np.nan]
    nb = int(np.ceil(n / block)); means = []
    for _ in range(B):
        st = rng.integers(0, n - block + 1, size=nb)
        means.append(np.concatenate([x[s:s + block] for s in st])[:n].mean())
    return [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


def benjamini_yekutieli(pvals, q=0.10):
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    m = len(items)
    if m == 0:
        return {"m": 0}
    items.sort(key=lambda x: x[1])
    c_m = sum(1.0 / i for i in range(1, m + 1)); surv = []
    for ri, (k, p) in enumerate(items, 1):
        if p <= (ri / m) * q / c_m:
            surv = [items[j][0] for j in range(ri)]
    return {"m": m, "by_factor": round(c_m, 3), "survivors_BY": surv,
            "raw_p_min": round(items[0][1], 5), "raw_p_min_key": items[0][0],
            "bonferroni_alpha": round(0.05 / m, 5)}


def sig_forward_stat(sig, fwd, h_months, label, prior_sign):
    """업종 timing 신호 1개 forward 통계 (Spearman IC + OOS + power)."""
    common = sig.dropna().index.intersection(fwd.dropna().index)
    if len(common) < 12:
        return {"label": label, "n": len(common), "status": "INSUFFICIENT(n<12)"}
    sv, fv = sig.loc[common].values, fwd.loc[common].values
    rho, _ = stats.spearmanr(sv, fv)
    sr = stats.rankdata(sv) / len(sv) - 0.5
    fr = stats.rankdata(fv) / len(fv) - 0.5
    prod = sr * fr
    neff = n_eff_autocorr(prod); se = nw_se(prod, h_months)
    t_nw = prod.mean() / se if se and se > 0 else np.nan
    wc_p = wild_cluster_p(prod); ci = block_boot_ci(prod, max(2, h_months))
    t_power = abs(rho) * np.sqrt(max(neff, 1.0))
    powered = (len(common) >= 24) and (neff >= 6) and (t_power >= T_BREAKEVEN)
    # OOS
    is_idx = [d for d in common if str(d) < OOS_SPLIT]
    oos_idx = [d for d in common if str(d) >= OOS_SPLIT]
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
    # ★이론 부호 일치 (prior_sign: +1/-1/0)
    prior_match = None
    if prior_sign != 0:
        prior_match = bool(np.sign(rho) == np.sign(prior_sign))
    return {"label": label, "n": len(common), "n_eff": round(neff, 1),
            "spearman_rho": round(float(rho), 4), "t_nw": round(float(t_nw), 2) if not np.isnan(t_nw) else None,
            "t_power_mde": round(float(t_power), 2),
            "wild_cluster_p": round(wc_p, 4) if not np.isnan(wc_p) else None,
            "ci95_block_boot": [round(c, 5) for c in ci] if not np.isnan(ci[0]) else None,
            "prior_sign": prior_sign, "prior_match": prior_match,
            "walk_forward_oos": oos,
            "status": "powered" if powered else ("underpowered" if len(common) >= 12 else "INSUFFICIENT")}


def load_data():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    px = mask_trading_halt(px)  # ★좀비 마스킹
    cf = pd.read_parquet(DATA / "common_factors.parquet"); cf.index = pd.to_datetime(cf.index)
    rs = pd.read_parquet(DATA / "regime_series.parquet"); rs.index = pd.to_datetime(rs.index)
    gb = pd.read_parquet(DATA / "global_bio_etfs.parquet"); gb.index = pd.to_datetime(gb.index)
    kr = pd.read_parquet(DATA / "kr_rates.parquet"); kr.index = pd.to_datetime(kr.index)
    # macro_daily / fda 는 상위 bio/data/ 에 위치
    macro = pd.read_parquet(ROOT.parent / "data" / "macro_daily.parquet"); macro.index = pd.to_datetime(macro.index)
    fda = None
    fda_p = ROOT.parent / "data" / "fda_approvals_monthly.csv"
    if fda_p.exists():
        fda = pd.read_csv(fda_p)
    return px, cf, rs, gb, kr, macro, fda


def build_bio_index(px):
    """★strict 바이오 업종 index = floor 38종 eq-weight 월간 forward return.
    좀비 마스킹 후 패널 평균(skipna) = 거래정지 종목 제외 자동."""
    pxm = px.resample("ME").last()
    # 업종 월간 수익 = eq-weight 평균 (cross-sectional mean of monthly returns)
    ret_m = pxm.pct_change().mean(axis=1, skipna=True)
    cum = (1 + ret_m.fillna(0)).cumprod()
    return cum, ret_m


def build_macro_signals(cf, rs, gb, kr, macro, fda, idx):
    """거시 overlay 신호 월말 시계열 (이론 부호 사전확약 매핑)."""
    cfm = cf.resample("ME").last()
    rsm = rs.resample("ME").last()
    gbm = gb.resample("ME").last()
    macm = macro.resample("ME").last()
    krm = kr["IRLTLT01KRM156N"].resample("ME").last() if "IRLTLT01KRM156N" in kr.columns else kr.iloc[:, 0].resample("ME").last()

    sigs = {}
    # 금리 duration (growth) — Δ3M (모멘텀)
    sigs[("us_10y_d", -1)] = cfm["rate10y"].diff(3)
    sigs[("kr_10y_d", -1)] = krm.diff(3)
    # 금리커브 steepening (10Y-2Y)
    if "us_2y" in macm.columns and "us_10y" in macm.columns:
        sigs[("us_curve", +1)] = (macm["us_10y"] - macm["us_2y"])
    # 글로벌 바이오 ETF 상대모멘텀 (XBI/SPY, IBB/NDX) 3M
    xbi_rel = (gbm["XBI"] / gbm["SPY"])
    ibb_rel = (gbm["IBB"] / gbm["^NDX"])
    sigs[("xbi_rel_mom", +1)] = xbi_rel.pct_change(3)
    sigs[("ibb_rel_mom", +1)] = ibb_rel.pct_change(3)
    sigs[("xbi_mom", +1)] = gbm["XBI"].pct_change(3)
    # 환율 Δ3M
    sigs[("usdkrw_d", 0)] = rsm["usdkrw"].pct_change(3)
    # VIX / credit (risk-off)
    sigs[("vix_level", -1)] = cfm["VIX"]
    sigs[("credit_hy", -1)] = cfm["credit_hy_oas"]
    # FDA 승인 yoy
    if fda is not None:
        try:
            fda2 = fda.copy()
            # 컬럼 추정: date + count
            dcol = [c for c in fda2.columns if "date" in c.lower() or "month" in c.lower() or "ym" in c.lower()]
            ccol = [c for c in fda2.columns if "count" in c.lower() or "approv" in c.lower() or "n_" in c.lower()]
            if dcol and ccol:
                fda2["dt"] = pd.to_datetime(fda2[dcol[0]], errors="coerce")
                fser = fda2.set_index("dt")[ccol[0]].resample("ME").sum()
                sigs[("fda_yoy", +1)] = fser.pct_change(12)
        except Exception as e:
            print(f"  FDA 신호 skip: {repr(e)[:50]}")
    # 모든 신호 idx(업종 forward index) 월말에 정렬
    out = {}
    for (name, sign), ser in sigs.items():
        out[(name, sign)] = ser.reindex(idx, method="ffill")
    return out


def main():
    px, cf, rs, gb, kr, macro, fda = load_data()
    cum, ret_m = build_bio_index(px)
    cum = cum.loc["2019-01-01":]
    print(f"bio 업종 index: {cum.index.min().date()}~{cum.index.max().date()} n={len(cum)} (좀비 마스킹 후)")

    sigs = build_macro_signals(cf, rs, gb, kr, macro, fda, cum.index)
    print(f"거시 신호 후보: {[k[0] for k in sigs.keys()]} (N={len(sigs)})")

    results = {"meta": {
        "target": "bio 업종 forward return (eq-weight strict 화이트리스트 38종, 좀비 마스킹)",
        "vs": "거시 overlay 신호 (금리 duration/환율/글로벌바이오 ETF 상대/VIX/credit/FDA)",
        "horizons_days": HORIZONS_D, "oos_split": OOS_SPLIT, "t_breakeven": T_BREAKEVEN,
        "zombie_mask": "mask_trading_halt(연속 동일종가>=10일 NaN, 코오롱티슈진/케어젠 carry-forward 제거)",
        "v2_재검": "v2 rotation = NO_DIRECT_CYCLE + momentum OOS flip = FAIL. 본 측정 = 거시 overlay 추가(v2 미측정).",
        "이론_부호_사전확약": "theory-notes §3 + 증권사. growth long-duration = 금리 음/글로벌바이오 양/VIX 음.",
        "n_candidates": len(sigs),
    }, "signals": {}}

    pvals_all, pvals_oos_elig = {}, {}
    for (name, prior_sign), ser in sigs.items():
        results["signals"][name] = {"prior_sign": prior_sign, "horizons": {}}
        for hl, hd in HORIZONS_D.items():
            hm = max(1, round(hd / 21))
            fwd = cum.pct_change(hm).shift(-hm)
            st = sig_forward_stat(ser, fwd, hm, f"bio_rot__{name}__{hl}", prior_sign)
            results["signals"][name]["horizons"][hl] = st
            if st.get("status") in ("powered", "underpowered") and st.get("wild_cluster_p") is not None:
                pvals_all[f"{name}__{hl}"] = st["wild_cluster_p"]
                if st["walk_forward_oos"].get("eligible"):
                    pvals_oos_elig[f"{name}__{hl}"] = st["wild_cluster_p"]

    results["fdr_all"] = benjamini_yekutieli(pvals_all)
    results["fdr_oos_eligible"] = benjamini_yekutieli(pvals_oos_elig)

    out = ROOT / "validation-rotation-v3.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved {out}\n")
    print_summary(results)
    return results


def print_summary(r):
    print("=" * 92)
    print("bio 업종 ROTATION — 거시 overlay 신호 (이론 부호 + 통계 + OOS)")
    print("=" * 92)
    hdr = f"{'signal':14s} {'h':5s} {'rho':>7s} {'wc_p':>7s} {'prior':>6s} {'match':>6s} {'OOS_is->oos':>16s} {'elig':>5s} {'status':>12s}"
    print(hdr)
    for name, sd in r["signals"].items():
        for hl, st in sd["horizons"].items():
            if "spearman_rho" not in st:
                print(f"{name:14s} {hl:5s}  {st.get('status')}")
                continue
            oos = st["walk_forward_oos"]
            oos_str = f"{oos.get('rho_is')}->{oos.get('rho_oos')}" if "rho_is" in oos else oos.get("verdict", "")
            pm = "OK" if st.get("prior_match") else ("X" if st.get("prior_match") is False else "-")
            el = "Y" if oos.get("eligible") else ("n" if oos.get("eligible") is False else "-")
            print(f"{name:14s} {hl:5s} {st['spearman_rho']:+.3f} {str(st.get('wild_cluster_p')):>7s} "
                  f"{st['prior_sign']:+d}     {pm:>5s} {oos_str:>16s} {el:>5s} {st['status']:>12s}")
    print(f"\nFDR all: {json.dumps(r['fdr_all'], ensure_ascii=False)}")
    print(f"FDR OOS-eligible: {json.dumps(r['fdr_oos_eligible'], ensure_ascii=False)}")


if __name__ == "__main__":
    main()
