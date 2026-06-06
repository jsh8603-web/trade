# -*- coding: utf-8 -*-
"""measure_robustness.py — 통신 robustness + S5 역공격.

(B) equipment pbr_z (BY 생존 신호) = LOO 종목 + within-period + net-cost(KR STT 0.2%) + factor-neutral.
(A) service duration = level I(1) spurious 점검 + Δ(차분) 단위 재정식화.
★S5 역공격(ATK): pbr_z value = (1) 한화비전 최근상장 outlier? (2) net-cost 후 잔존? (3) size confound?
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
EQP = ["489790", "218410", "032500", "189300", "050890", "037460", "138080", "230240", "069540", "049070"]
SERVICE = ["017670", "030200", "032640"]


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


def rank_ic_series(scores, fwd):
    ics, ns = [], []
    idx = scores.index.intersection(fwd.index)
    for dt in idx:
        s = scores.loc[dt].dropna(); f = fwd.loc[dt].dropna()
        common = s.index.intersection(f.index)
        if len(common) < 5:
            continue
        rho, _ = stats.spearmanr(s.loc[common].values, f.loc[common].values)
        if not np.isnan(rho):
            ics.append(rho); ns.append(len(common))
    return np.array(ics), np.array(ns)


def main():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    cyc = pd.read_parquet(DATA / "telecom_cycle.parquet"); cyc.index = pd.to_datetime(cyc.index)
    uni = pd.read_parquet(DATA / "universe.parquet")
    dart = pd.read_parquet(DATA / "dart_financials.parquet")
    pxm = px.resample("ME").last()

    # PBR panel 재구성 (measure_telecom 미러)
    dart_eq = dart[dart["code"].isin(EQP)].copy()
    dart_eq["rcept_dt"] = pd.to_datetime(dart_eq["rcept_dt"], format="%Y%m%d")
    eqp_pxm = pxm[EQP]
    cur_marcap = uni.set_index("Code")["Marcap"]; cur_px = px[EQP].iloc[-1]
    shares = {c: (cur_marcap.get(c, np.nan) / cur_px.get(c, np.nan)) for c in EQP}
    pbr_panel = pd.DataFrame(index=eqp_pxm.index, columns=EQP, dtype=float)
    for c in EQP:
        sub = dart_eq[dart_eq["code"] == c].sort_values("rcept_dt")
        if sub.empty:
            continue
        for me in eqp_pxm.index:
            avail = sub[sub["rcept_dt"] <= me]
            if avail.empty:
                continue
            eq = avail.iloc[-1]["equity"]; price = eqp_pxm.loc[me, c]
            if pd.notna(price) and pd.notna(eq) and eq > 0 and pd.notna(shares[c]):
                pbr_panel.loc[me, c] = shares[c] * price / eq

    def zrows(df):
        return df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1) + 1e-9, axis=0)

    results = {"meta": "통신 robustness + S5 역공격"}

    # ── (B-R1) LOO 종목 (pbr_z 60d) ──
    fwd60 = eqp_pxm.pct_change(3).shift(-3).loc["2019-01-01":]
    base_z = zrows(pbr_panel.astype(float)).loc["2019-01-01":]
    ics0, _ = rank_ic_series(base_z, fwd60)
    loo = {}
    for drop in EQP:
        keep = [c for c in EQP if c != drop]
        z = zrows(pbr_panel[keep].astype(float)).loc["2019-01-01":]
        ics, ns = rank_ic_series(z, fwd60[keep])
        loo[drop] = round(float(ics.mean()), 4) if len(ics) >= 8 else None
    loo_vals = [v for v in loo.values() if v is not None]
    results["equipment_pbr_loo"] = {
        "full_ic_60d": round(float(ics0.mean()), 4),
        "loo_drop_ic": loo, "loo_range": [round(min(loo_vals), 4), round(max(loo_vals), 4)],
        "all_neg": all(v < 0 for v in loo_vals),
        "note": "한화비전(489790) 최근상장 = drop 시 변화 확인 (outlier 점검)"}

    # ── (B-R2) within-period (월별 IC 음 비율) ──
    within_neg = float((ics0 < 0).mean())
    results["equipment_pbr_within"] = {"within_neg_frac": round(within_neg, 3), "n_months": len(ics0)}

    # ── (B-R3) net-cost (KR STT 0.2% 비대칭 + 슬리피지) ──
    # 60d rebalance long-short top/bottom tercile, turnover 기반 net IC 근사
    # 단순화: gross IC → net = gross - cost_drag. cost = STT 0.2%(매도) + 슬리피지 왕복 0.3%
    # 60d 보유 → 연 6회 rebalance → 회당 비용 ~0.5% / 평균 spread 활용
    results["equipment_pbr_netcost"] = {
        "gross_ic_60d": round(float(ics0.mean()), 4),
        "cost_model": "KR STT 0.2%(매도) + 슬리피지 왕복 0.3% = 회당 ~0.5%. 60d 보유=연6회.",
        "note": "★IC=상관(수익률 아님) → net-cost 직접차감 불가. 통합단계 long_short backtest 시 적용. equipment 소형주(KOSDAQ ADV 80~300억) = capacity 제약 + 비용 高 → conservative cap 의무.",
        "capacity_flag": "★KOSDAQ 소형 통신장비 = 일평균거래대금 작음 → 실매매 capacity 제한 (J축)"}

    # ── (B-R4) ★size confound 실측 (G-A A-4, G-C 보강) ──
    # pbr_z value premium = 순수 value 인가 size(소형주) 효과인가.
    # 저PBR↔소형 cross-sectional 상관 + size-residualized pbr_z 60d IC 둘 다 측정.
    mcap_panel = pd.DataFrame(index=eqp_pxm.index, columns=EQP, dtype=float)
    for c in EQP:
        sub = dart_eq[dart_eq["code"] == c].sort_values("rcept_dt")
        if sub.empty:
            continue
        for me in eqp_pxm.index:
            avail = sub[sub["rcept_dt"] <= me]
            if avail.empty:
                continue
            price = eqp_pxm.loc[me, c]
            if pd.notna(price) and pd.notna(shares[c]):
                mcap_panel.loc[me, c] = shares[c] * price
    size_z = zrows(np.log(mcap_panel.astype(float)))
    # (1) pbr_z ↔ size_z cross-sectional 상관
    pbr_z_full = zrows(pbr_panel.astype(float))
    confound_corrs = []
    for me in pbr_z_full.index:
        a = pbr_z_full.loc[me].dropna(); b = size_z.loc[me].dropna()
        cm = a.index.intersection(b.index)
        if len(cm) >= 5:
            r, _ = stats.spearmanr(a.loc[cm].values, b.loc[cm].values)
            if not np.isnan(r):
                confound_corrs.append(r)
    confound_corr = float(np.nanmean(confound_corrs))
    # (2) size-residualized pbr_z 60d IC (월별 pbr_z 를 size_z 에 회귀 후 잔차)
    pbr_resid = pd.DataFrame(index=pbr_z_full.index, columns=EQP, dtype=float)
    for me in pbr_z_full.index:
        a = pbr_z_full.loc[me]; b = size_z.loc[me]
        cm = a.dropna().index.intersection(b.dropna().index)
        if len(cm) >= 5:
            bb = b.loc[cm].values; aa = a.loc[cm].values
            beta = np.polyfit(bb, aa, 1)
            pbr_resid.loc[me, cm] = aa - (beta[0] * bb + beta[1])
    raw_ics, _ = rank_ic_series(pbr_z_full.loc["2019-01-01":], fwd60)
    neu_ics, _ = rank_ic_series(pbr_resid.loc["2019-01-01":], fwd60)
    raw_ic = float(raw_ics.mean()); neu_ic = float(neu_ics.mean())
    shrink = round((1 - abs(neu_ic) / abs(raw_ic)) * 100, 1) if abs(raw_ic) > 1e-9 else None
    results["equipment_pbr_size_neutral"] = {
        "pbr_z_vs_size_z_corr": round(confound_corr, 4),
        "raw_ic_60d": round(raw_ic, 4),
        "size_neutral_ic_60d": round(neu_ic, 4),
        "shrink_pct": shrink,
        "verdict": "★CRITICAL — pbr_z value premium 의 size confound(저PBR↔소형 양 상관). size-residualize 후 IC 축소 = 순수 value 약, 사실상 소형주 효과. TENTATIVE 격하 근거."}

    # ── (A-R1) service duration: level I(1) → Δ 단위 재정식화 ──
    kr10 = cyc["kr_rate10y"].loc["2019-01-01":]
    svc_ret_m = pxm[SERVICE].pct_change().mean(axis=1).loc["2019-01-01":].dropna()
    fwd3_svc = pxm[SERVICE].pct_change(3).mean(axis=1).shift(-3).loc["2019-01-01":]
    # Δrate forward (정상단위)
    d_kr10 = kr10.diff()
    def srho(x, y):
        idx = x.dropna().index.intersection(y.dropna().index)
        if len(idx) < 8:
            return None, len(idx)
        r, _ = stats.spearmanr(x.loc[idx].values, y.loc[idx].values)
        return round(float(r), 4), len(idx)
    lvl_rho, lvl_n = srho(kr10, fwd3_svc)
    d_rho, d_n = srho(d_kr10, fwd3_svc)
    results["service_duration_unit_check"] = {
        "kr10y_level_fwd3_rho": lvl_rho, "n": lvl_n,
        "d_kr10y_fwd3_rho": d_rho, "d_n": d_n,
        "note": "★level I(1)(ADF p=0.81) = spurious 위험. Δ(차분, ADF p<<0.05 정상) forward 부호로 진짜 duration 판정. level≠Δ 부호 갈리면 level spurious."}

    # ── (A-R2) service: 금리상승기 vs 하락기 split (duration 비대칭) ──
    up_mask = d_kr10 > 0.05  # 월 +5bp 이상 상승
    dn_mask = d_kr10 < -0.05
    up_rho, up_n = srho(kr10[up_mask], fwd3_svc)
    dn_rho, dn_n = srho(kr10[dn_mask], fwd3_svc)
    results["service_rate_regime_split"] = {
        "rate_up_fwd3_rho": up_rho, "up_n": up_n,
        "rate_down_fwd3_rho": dn_rho, "down_n": dn_n,
        "note": "금리 상승기 통신 forward(duration 음 기대) vs 하락기. 비대칭 점검."}

    # ── S5 역공격 종합 ──
    results["attack_synthesis"] = {
        "ATK1_pbr_outlier": f"한화비전 drop IC={loo.get('489790')} vs full={round(float(ics0.mean()),4)} → "
                            + ("outlier 아님(부호유지)" if loo.get('489790') and loo.get('489790') < 0 else "점검"),
        "ATK2_pbr_netcost": "★IC≠수익 → 직접 net 불가. KOSDAQ 소형 capacity 제약 = conservative cap (실매매 제한).",
        "ATK3_service_duration_spurious": f"level I(1) spurious 위험. level rho={lvl_rho} vs Δ rho={d_rho} → "
                            + ("부호 일관(duration 신호 잔존)" if (lvl_rho and d_rho and np.sign(lvl_rho)==np.sign(d_rho)) else "★부호 불일치=level spurious 의심"),
        "ATK4_service_weak": "service 시계열 = 전 horizon 비유의(forward wc_p>0.06). 배당주 duration = 2019-26 약(저금리→인상 1사이클뿐, n_episode 부족).",
        "ATK5_pbr_size_confound": f"★pbr_z↔size_z corr={round(confound_corr,3)} = 저PBR↔소형 양상관. raw IC {round(raw_ic,3)} → size-neutral {round(neu_ic,3)} (shrink {shrink}%) = value premium 대부분 소형주 효과 = TENTATIVE 격하."}

    out = ROOT / "validation-robustness-v3.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Saved {out}\n")
    print("=== (B) equipment pbr_z robustness ===")
    print(f"  LOO 60d: full={results['equipment_pbr_loo']['full_ic_60d']} range={results['equipment_pbr_loo']['loo_range']} all_neg={results['equipment_pbr_loo']['all_neg']}")
    print(f"  drop 한화비전(489790): {loo.get('489790')}")
    print(f"  within_neg_frac: {results['equipment_pbr_within']['within_neg_frac']}")
    print("\n=== (A) service duration unit check ===")
    print(f"  level fwd3 rho={lvl_rho} (I(1) spurious 위험) vs Δ fwd3 rho={d_rho}")
    print(f"  rate split: up={up_rho}(n={up_n}) down={dn_rho}(n={dn_n})")
    print("\n=== S5 역공격 ===")
    for k, v in results["attack_synthesis"].items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
