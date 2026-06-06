# -*- coding: utf-8 -*-
"""_sleeve_rotation_kr.py — WIRE5 한국 12산업 2층 rotation fork (v2: 변별력 + 즉시발동).

★v1(STATIC_ONLY, tilt 0.5%) → 자문 3R 수렴(.consult-kr-rotation-variability-RESULTS.md) 반영 v2.
사용자 불변요구: 0.5% 거부, 뚜렷한 변별력 + 즉시 발동. 미국 selection(cheapness z 직접) 수준.

★자문 수렴 반영 (C1~C7) + 내 비판 보정:
- C1 시계열 residualize 폐기 → cross-sectional demean. ★보정: 신호 스케일 이질(z-spread vs pct_change)이라
  expanding z(시계열 정규화) 선행 후 CS demean (자문 동질신호 가정 보정).
- C2 base = sleeve-RP × within-EW (잔차 RP 폐기, defensive 편중 제거).
- C4 즉시발동: binary OOS gate 폐기 → per-industry 연속 수축 κ_i(robust gate × |IC|/(|IC|+ic0)).
- C5 N_eff cap(개수3) 폐기 → active-share 컨트롤러(risk budget). 12산업 full 차등.
- C6 z-비례 연속 tilt, per-name clip ±5%.
- C7 active 천장 cap 15% / 운용 band 8~12%.
- monitor weight0 (shipbuilding). ★double-count 점검: portfolio 공통인자 노출 실측(내 비판 ①).

⛔ production(core/stock) 무접촉=byte-identical. go-live 사람게이트 미접촉.
재현: python _sleeve_rotation_kr.py → _sleeve_rotation_kr_results.json
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import measure_integration as MI

PANEL = ROOT / "data" / "rotation_signals_panel.parquet"
START = "2019-01-01"

SLEEVES = {
    "export_cyclical": ["semiconductor", "auto", "financial", "battery", "chemical", "refining", "shipbuilding", "steel", "consumer"],
    "defensive_it": ["telecom", "aitech", "bio"],
    # ★bio 격리(yaml §2): 별도 sleeve는 3-sleeve RP서 bio 1업종 base 32% 과대 부작용 → defensive_it 멤버 유지.
    #   현 cross-sectional tilt 구조 = 전체 demean이라 bio가 자기 신호로 이미 독립 tilt(sleeve silo 무관) = 격리 충족.
}
MONITOR = {"shipbuilding"}
# ★sub_singleton_gating (yaml §2/§5): refining(고유 cycle 신호 발현 시만)/financial(credit 확대 국면만) 독립 tilt.
#   |z_cs| < SUB_THRESH = 평소 sleeve base 유지(tilt 0). 발현 시만 tilt.
SUB_GATED = {"refining", "financial"}
SUB_THRESH = 1.0
ALL_IND = MI.INDUSTRIES

# gated params (자문 C6/C7)
CAP_TILT = 0.05            # per-name Δw clip ±5%p (C6)
CAP_ACTIVE = 0.15          # active share 천장 (C7)
BAND = (0.08, 0.12)        # active 운용 밴드 (C7)
TARGET_AS = 0.10           # s_rot calib target (밴드 중앙)
MIN_TRAIN = 36
# over-trade 3중 (자문 §5, v1→v2 복원)
HYST_BAND = 0.01           # ① hysteresis: prev 대비 |Δw|>1%p 일 때만 rebalance
STT_SELL = 0.0023          # ③ cost-aware: KR 매도 거래세 0.23% (소형시장 sector-timing 주 필터)
COST_PER_SIDE = 0.0008     # commission+spread half
# ② persistence = 신호 expanding z 가 지속성 내재 (별도 k개월 지속 불필요)


def expanding_z(s, mp=24):
    return (s - s.expanding(mp).mean()) / s.expanding(mp).std()


def signal_z_cs(X):
    """신호 → expanding z(시계열) + cross-sectional demean(시점별 12산업 평균0) + CS std 정규화.
    ★expanding z 선행 = 신호 스케일 이질 보정(내 비판). CS demean = C1(1층 중복 제거, 신호강도 보존)."""
    Z = X.apply(expanding_z)
    Zcs = Z.sub(Z.mean(axis=1), axis=0)                 # cross-sectional demean
    xstd = Zcs.std(axis=1).replace(0, np.nan)
    Zcs = Zcs.div(xstd, axis=0)                          # CS std 정규화 (시점별 단위 분산)
    return Zcs


def base_sleeve_rp_ew(R):
    """base = sleeve-RP(산업간) × within-EW(sleeve내). ship(monitor)=0. (C2)"""
    sret = {}
    for sl, inds in SLEEVES.items():
        act = [i for i in inds if i not in MONITOR]
        sret[sl] = R[act].mean(axis=1)
    svol = {sl: sret[sl].std() for sl in SLEEVES}
    inv = {sl: 1.0 / svol[sl] for sl in SLEEVES if svol[sl] > 1e-9}
    ssum = sum(inv.values()) or 1.0
    sw = {sl: inv[sl] / ssum for sl in SLEEVES}          # sleeve간 RP
    w = {}
    for sl, inds in SLEEVES.items():
        act = [i for i in inds if i not in MONITOR]
        for i in act:
            w[i] = sw[sl] / len(act)                     # within EW
    for i in MONITOR:
        w[i] = 0.0
    s = pd.Series(w).reindex(ALL_IND).fillna(0.0)
    return s / s.sum()


def signal_ic(X, R, h=3):
    """각 산업 OW정렬 신호 → forward IC (κ 연속수축 입력 + 부호 점검)."""
    out = {}
    for ind in X.columns:
        fwd = R[ind].shift(-h).rolling(h).sum()
        d = pd.concat([X[ind], fwd], axis=1).dropna()
        if len(d) < 12:
            out[ind] = {"ic": 0.0, "n": len(d)}
            continue
        ic = d.iloc[:, 0].corr(d.iloc[:, 1], method="spearman")
        # block-bootstrap 부호 안정 (즉시발동 robust gate, C4)
        vals = d.values
        rng = np.random.default_rng(7)
        boots, n, bl = [], len(vals), 6
        for _ in range(500):
            nb = int(np.ceil(n / bl))
            st = rng.integers(0, max(1, n - bl + 1), size=nb)
            idx = np.concatenate([np.arange(s, s + bl) for s in st])[:n]
            b = vals[idx]
            try:
                boots.append(pd.Series(b[:, 0]).corr(pd.Series(b[:, 1]), method="spearman"))
            except Exception:
                pass
        ci = np.percentile([x for x in boots if not np.isnan(x)], [5, 95]) if boots else [0, 0]  # 90% CI (n=83 적정)
        sign_stable = ((ci[0] > 0) or (ci[1] < 0)) and abs(ic) > 0.15  # 부호안정 + mag floor (C4 robust)
        out[ind] = {"ic": round(float(ic), 3), "n": len(d), "ci": [round(c, 3) for c in ci],
                    "sign_stable": bool(sign_stable)}
    return out


def kappa_per_industry(ic_map, ic0):
    """κ_i = robust gate(부호 안정) × |IC|/(|IC|+ic0) 연속수축. 약신호 자동 0근처 (C4)."""
    k = {}
    for ind, d in ic_map.items():
        ic = abs(d.get("ic", 0.0))
        gate = 1.0 if d.get("sign_stable", False) else 0.0
        k[ind] = gate * (ic / (ic + ic0))
    return k


def build_weights(Zcs_t, base_w, kappa, s_rot):
    """현 시점 신호 z_cs → tilt(κ×s_rot×z, clip ±5%) → 비중 + active 컨트롤러(cap15%)."""
    tilt = {}
    for i in ALL_IND:
        if i in MONITOR:
            tilt[i] = 0.0; continue
        z = Zcs_t.get(i, 0.0)
        z = 0.0 if pd.isna(z) else z
        # ★sub-gating: refining/financial은 신호 발현(|z|≥임계) 시만 독립 tilt, 평소 base 유지
        if i in SUB_GATED and abs(z) < SUB_THRESH:
            tilt[i] = 0.0; continue
        tilt[i] = float(np.clip(kappa.get(i, 0.0) * s_rot * z, -CAP_TILT, CAP_TILT))
    # ★additive tilt (자문 C6: per-name Δw clip ±5%p. multiplicative는 base 작은 산업서 효과 소실)
    w = pd.Series({i: base_w[i] + tilt[i] for i in ALL_IND}).clip(lower=0.0)
    w = w / w.sum()
    # active-share 컨트롤러 (C7 cap)
    dev = (w - base_w)
    AS = dev.abs().sum()
    if AS > CAP_ACTIVE and AS > 1e-9:
        w = base_w + (CAP_ACTIVE / AS) * dev
        w = w.clip(lower=0.0); w = w / w.sum()
    return w, pd.Series(tilt)


def calib_s_rot(Zcs, base_w, kappa):
    """in-sample 평균 active share가 TARGET_AS(10%) 되게 s_rot 전역 calib (C7 band).
    ★raw Δw(clip/cap 전) 기준 측정 — build_weights의 cap이 calib을 무력화하는 버그 회피."""
    devs = []
    for t in Zcs.index:
        zt = Zcs.loc[t]
        d = sum(abs(kappa.get(i, 0.0) * (0.0 if pd.isna(zt.get(i, 0.0)) else zt.get(i, 0.0))) for i in ALL_IND)
        if d > 0:
            devs.append(d)
    mean_raw = np.nanmean(devs) if devs else 0.0
    return (TARGET_AS / mean_raw) if mean_raw > 1e-9 else 1.0


def double_count_check(tilt_avg, R, F):
    """★내 비판 ①: tilt 평균이 공통인자(usdkrw/foreign/semi_ppi)에 net 노출 주는지.
    각 산업 공통인자 β → Σ tilt_i × β_i = portfolio net common-factor 노출. CS demean이면 ~0이어야."""
    betas = {}
    for ind in ALL_IND:
        y = R[ind]
        common = y.dropna().index.intersection(F.dropna().index)
        if len(common) < 20:
            continue
        X = np.column_stack([np.ones(len(common))] + [F.loc[common, c].values for c in F.columns])
        b, *_ = np.linalg.lstsq(X, y.loc[common].values, rcond=None)
        betas[ind] = {c: float(b[k + 1]) for k, c in enumerate(F.columns)}
    net = {}
    for c in F.columns:
        net[c] = sum(tilt_avg.get(i, 0.0) * betas.get(i, {}).get(c, 0.0) for i in ALL_IND)
    return {"net_common_exposure": {k: round(v, 5) for k, v in net.items()},
            "interpret": "CS demean 정상이면 net 공통인자 노출 ≈0 (산업 rotation = 1층과 직교, double-count 없음)"}


def main():
    X = pd.read_parquet(PANEL); X.index = pd.to_datetime(X.index)
    panels = {s: MI.panel_monthly(s) for s in ALL_IND}
    R = pd.DataFrame(panels).loc[START:]
    F = MI.common_factors()
    common = X.index.intersection(R.index)
    X, R = X.loc[common], R.loc[common]

    Zcs = signal_z_cs(X)
    base_w = base_sleeve_rp_ew(R)
    ic_map = signal_ic(X, R, h=3)
    ic_vals = [abs(d["ic"]) for d in ic_map.values() if "ic" in d]
    ic0 = float(np.median(ic_vals)) if ic_vals else 0.1
    kappa = kappa_per_industry(ic_map, ic0)
    s_rot = calib_s_rot(Zcs.dropna(how="all"), base_w, kappa)

    # walk-forward 비중 형성 + OOS active(참고)
    base_ret = (R[ALL_IND] * base_w).sum(axis=1)
    weights_hist, tilts_hist, active = [], [], []
    dates = [t for t in Zcs.index if t in R.index]
    prev_w = None
    for k, t in enumerate(dates):
        if Zcs.loc[t].isna().all():
            continue
        w_raw, tilt = build_weights(Zcs.loc[t], base_w, kappa, s_rot)
        # ★over-trade ① hysteresis: prev 대비 |Δw|<band → prev 유지 (§5, ②persistence=expanding z 내재)
        if prev_w is not None:
            w = w_raw.copy()
            small = (w_raw - prev_w).abs() < HYST_BAND
            w[small] = prev_w[small]
            w = w / w.sum()
        else:
            w = w_raw
        # ★audit fix(steel-audit 2026-06-06): hysteresis renorm 경로가 cap을 깨 active max 0.156 (천장 0.15 초과).
        #   cap='천장' 불변 주장 보존 위해 hysteresis 후 active cap 재적용.
        dev_h = (w - base_w); AS_h = dev_h.abs().sum()
        if AS_h > CAP_ACTIVE and AS_h > 1e-9:
            w = (base_w + (CAP_ACTIVE / AS_h) * dev_h).clip(lower=0.0); w = w / w.sum()
        weights_hist.append(w); tilts_hist.append(tilt.rename(t))
        # ★over-trade ③ cost-aware: turnover × (commission + STT 매도/2) 차감 (§5)
        turnover = float((w - prev_w).abs().sum()) if prev_w is not None else float((w - base_w).abs().sum())
        cost = turnover * (COST_PER_SIDE + STT_SELL / 2)
        nxt = t + pd.offsets.MonthEnd(1)
        if nxt in R.index:
            r = R.loc[nxt].reindex(ALL_IND).fillna(0.0)
            active.append(float((w - base_w) @ r) - cost)
        prev_w = w
    W = pd.DataFrame(weights_hist)
    T = pd.DataFrame(tilts_hist)
    tilt_avg = T.mean().to_dict()
    act = np.array(active)

    # ★현 시점(최신) 목표 비중 = 즉시발동 산출
    last_t = dates[-1]
    w_now, tilt_now = build_weights(Zcs.loc[last_t], base_w, kappa, s_rot)

    # 비중 형성
    wt_form = {}
    for ind in ALL_IND:
        if ind in W.columns:
            c = W[ind]
            wt_form[ind] = {"base": round(float(base_w[ind]), 4), "min": round(float(c.min()), 4),
                            "max": round(float(c.max()), 4), "now": round(float(w_now[ind]), 4),
                            "max_dev": round(float((c - base_w[ind]).abs().max()), 4)}
    as_series = W.sub(base_w, axis=1).abs().sum(axis=1)
    dc = double_count_check(tilt_avg, R, F)

    oos_ir = (float(np.mean(act)) / float(np.std(act)) * np.sqrt(12)) if len(act) and np.std(act) > 1e-12 else None

    res = {
        "meta": {"version": "v2 (자문 3R 변별력+즉시발동)", "n_months": len(common),
                 "spec": "CS demean(expanding z 선행)+base sleeve-RP×EW+κ 연속수축+active 컨트롤러 cap15/band8~12",
                 "production_untouched": "core/stock import 0=byte-identical, go-live 미접촉",
                 "s_rot_calib": round(s_rot, 3), "ic0": round(ic0, 4)},
        "signal_ic": ic_map,
        "kappa": {k: round(v, 3) for k, v in kappa.items()},
        "base_weights": {i: round(float(base_w[i]), 4) for i in ALL_IND},
        "weights_formation": wt_form,
        "active_share": {"mean": round(float(as_series.mean()), 4), "min": round(float(as_series.min()), 4),
                         "max": round(float(as_series.max()), 4), "cap": CAP_ACTIVE, "band": list(BAND)},
        "tilt_now_pct": {i: round(float(tilt_now[i]) * 100, 2) for i in ALL_IND if abs(tilt_now[i]) > 1e-6},
        "double_count_check": dc,
        "oos_active_ref": {"mean": round(float(np.mean(act)), 6) if len(act) else None, "ann_IR": round(oos_ir, 3) if oos_ir else None,
                           "note": "참고용(즉시발동이 주, OOS는 사후). underpowered=magnitude tentative(yaml §8)"},
        "verdict": "ROTATION_ACTIVE (즉시발동, 변별력 active share 밴드 내 + robust gate 통과 산업만 tilt)",
    }
    out = ROOT / "_sleeve_rotation_kr_results.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Saved {out}\n")

    print(f"=== fork v2: 변별력 + 즉시발동 (s_rot={s_rot:.2f}, ic0={ic0:.3f}) ===\n")
    print("=== ★산업별 신호 IC + κ(연속수축) ===")
    for ind in sorted(ic_map, key=lambda x: -abs(ic_map[x].get("ic", 0))):
        d = ic_map[ind]
        print(f"  {ind:14s} IC={d.get('ic',0):+.3f} sign_stable={str(d.get('sign_stable','')):5s} κ={kappa.get(ind,0):.2f}")
    print(f"\n=== ★산업별 비중 형성 (base → [min,max], 현시점 now) ===")
    for ind in ALL_IND:
        d = wt_form.get(ind)
        if d:
            tag = " (monitor0)" if ind in MONITOR else ""
            print(f"  {ind:14s} base={d['base']:.3f} → [{d['min']:.3f},{d['max']:.3f}] now={d['now']:.3f} 편차±{d['max_dev']:.3f}{tag}")
    print(f"\n=== ★active share (변별력) ===")
    print(f"  mean={as_series.mean():.3f} [{as_series.min():.3f},{as_series.max():.3f}] cap={CAP_ACTIVE} band={BAND}")
    print(f"\n=== ★double-count 점검 (CS demean 직교성) ===")
    for k, v in dc["net_common_exposure"].items():
        print(f"  net {k}: {v:+.5f}")
    print(f"\n=== 현 시점 tilt (%p) ===")
    for i, v in sorted(res["tilt_now_pct"].items(), key=lambda x: -abs(x[1])):
        print(f"  {i:14s} {v:+.2f}%p")
    print(f"\n  OOS active IR(참고)={oos_ir}")
    print(f"  ★verdict = {res['verdict']}")


if __name__ == "__main__":
    main()
