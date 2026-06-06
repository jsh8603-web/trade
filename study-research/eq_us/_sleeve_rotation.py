# -*- coding: utf-8 -*-
"""_sleeve_rotation.py — 2층 sub-sleeve allocation 실측 (자문 3R 확정 spec, 2026-06-04).

매매 완전형 3층 中 2층: us_stock 안 cyclical/defensive/mega 비중을 regime 따라 tilt.
★자문 3R(gemini+claude) 수렴 spec 구현:
- per-sleeve 기계론축(sign 고정): mega←real_rate(−) / cyclical←credit baa_aaa(−) / defensive←dollar(+)
- predictive single-slope (excess_{i,t+1} ~ β·x_{i,t}), x = expanding z of macro level (lagged)
- pooled λ: 3 sleeve 동일 기울기 (sign·z stack 단일 β), fixed-b(Kiefer-Vogelsang) t
- target = excess return (R_sleeve − R_base), base = shrunk inverse-vol (target 1/3)
- tilt = base + g·clip(cross-sleeve demean(predicted excess z), ±cap)  [predict→demean→cap→re-demean]
- incremental = active_t = r(tilt) − r(base) 단일계열 fixed-b t (1df)
- walk-forward OOS gate = binding (positive OOS mean active + IR). 탈락 → static only.
- contemporaneous 별도 측정(기술통계, signal 아님 — Stambaugh/measurement-as-signal 구분)

★자문 사전확률: predictive 소멸 → static only 가 modal outcome (n=137mo). OOS gate 탈락 = 정상.

재현: python _sleeve_rotation.py → _sleeve_rotation_results.json
"""
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path("D:/projects/Inv/study-research/eq_us/industries")
sys.path.insert(0, str(BASE / "us_defensive" / "raw-v3"))
from _b2_stats import effective_n, fixed_b_cv  # noqa: E402

SLEEVES = ["us_cyclical", "us_defensive", "us_mega_tech"]
# 기계론축 (sign 고정 = β 크기 보기 전 mechanism freeze)
AXIS = {
    "us_cyclical":  ("baa_aaa",  -1),  # credit spread↑ = stress → cyclical(earnings-levered)↓
    "us_defensive": ("dollar",   +1),  # 강달러 = 긴축 → defensive 상대 강 (yield-trap 분리)
    "us_mega_tech": ("real_rate", -1), # real_rate↑ = duration 할인 → long-duration growth(mega)↓
}
MACRO_PATH = BASE / "us_defensive" / "raw-v3" / "data" / "macro.parquet"  # real_rate 포함 6컬럼


def load_sleeve_monthly_ret() -> pd.DataFrame:
    """3 sleeve equal-weight monthly return (month-end)."""
    out = {}
    for sl in SLEEVES:
        px = pd.read_parquet(BASE / sl / "raw-v3" / "data" / "prices.parquet")
        m = px.resample("ME").last()
        ew = m.pct_change().mean(axis=1)  # equal-weight sleeve return
        out[sl] = ew
    df = pd.DataFrame(out).dropna()
    return df  # index=month-end, cols=sleeves


def load_macro_monthly() -> pd.DataFrame:
    mac = pd.read_parquet(MACRO_PATH)
    mac = mac[~mac.index.duplicated(keep="last")].sort_index()
    m = mac.resample("ME").last()
    return m


def shrunk_inverse_vol(ret: pd.DataFrame, shrink: float = 0.5) -> np.ndarray:
    """base = shrink·(1/3) + (1−shrink)·inverse-vol. risk-neutral mandate (자문 R3)."""
    vol = ret.std().values
    inv = (1.0 / vol) / (1.0 / vol).sum()
    eq = np.ones(len(vol)) / len(vol)
    w = shrink * eq + (1 - shrink) * inv
    return w / w.sum()


def expanding_z(s: pd.Series, min_periods: int = 36) -> pd.Series:
    """expanding z-score (burn-in min_periods). look-ahead 없음 (t까지만)."""
    mu = s.expanding(min_periods=min_periods).mean()
    sd = s.expanding(min_periods=min_periods).std()
    return ((s - mu) / sd)


def fixed_b_t(x: np.ndarray) -> dict:
    """단일계열 평균의 fixed-b t (Kiefer-Vogelsang). _b2_stats 재사용."""
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n < 10:
        return {"mean": float(np.mean(x)) if n else 0.0, "n": n, "t": None, "fixed_b_sig": None}
    mean = float(np.mean(x))
    en = effective_n(x)                       # dict(n, n_eff, vif, rho1, nw_lag)
    lag = int(en["nw_lag"])
    demean = x - mean
    gamma0 = np.mean(demean ** 2)
    s = gamma0
    for k in range(1, lag + 1):
        w = 1 - k / (lag + 1)
        cov = np.mean(demean[k:] * demean[:-k])
        s += 2 * w * cov
    se = np.sqrt(s / n)
    t = mean / se if se > 1e-12 else 0.0
    cvd = fixed_b_cv(n, lag)                   # dict(b, cv_5pct, ...)
    cv = float(cvd["cv_5pct"])
    return {"mean": mean, "n": n, "n_eff": float(en["n_eff"]), "nw_lag": lag, "t": float(t),
            "fixed_b_cv": cv, "fixed_b_sig": bool(abs(t) > cv)}


def build_panel():
    ret = load_sleeve_monthly_ret()
    mac = load_macro_monthly()
    # 공통 기간 정렬
    idx = ret.index.intersection(mac.index)
    ret = ret.loc[idx]
    mac = mac.loc[idx]
    # predictor z (expanding, sign 적용)
    xz = {}
    for sl, (col, sign) in AXIS.items():
        if col not in mac.columns:
            raise KeyError(f"{col} not in macro {list(mac.columns)}")
        xz[sl] = sign * expanding_z(mac[col])
    xz = pd.DataFrame(xz).reindex(ret.index)
    return ret, xz


def pooled_predictive(ret, xz, base_w):
    """stack 3 sleeve (x_t, excess_{t+1}) → pooled β fixed-b. + contemporaneous 비교."""
    base_ret = (ret * base_w).sum(axis=1)
    excess = ret.sub(base_ret, axis=0)  # R_sleeve − R_base
    # predictive: x_t (shift 0) vs excess_{t+1} (shift -1)
    rows_pred, rows_contemp = [], []
    for sl in SLEEVES:
        x = xz[sl]
        ex_next = excess[sl].shift(-1)   # t+1
        ex_now = excess[sl]              # t (contemporaneous)
        d_pred = pd.concat([x, ex_next], axis=1).dropna()
        d_con = pd.concat([x, ex_now], axis=1).dropna()
        rows_pred.append(d_pred.values)
        rows_contemp.append(d_con.values)
    P = np.vstack(rows_pred); C = np.vstack(rows_contemp)
    # pooled OLS β (single slope, no intercept on demeaned)
    def slope(M):
        xx, yy = M[:, 0], M[:, 1]
        xx = xx - xx.mean(); yy = yy - yy.mean()
        b = (xx @ yy) / (xx @ xx) if (xx @ xx) > 1e-12 else 0.0
        resid = yy - b * xx
        return b, xx, resid
    b_pred, xp, rp = slope(P)
    b_con, xc, rc = slope(C)
    # fixed-b t on β: β의 series 기여 = x·y product, 단순화 = (x*y) 계열 평균 검정
    prod_pred = (P[:, 0] - P[:, 0].mean()) * (P[:, 1] - P[:, 1].mean())
    prod_con = (C[:, 0] - C[:, 0].mean()) * (C[:, 1] - C[:, 1].mean())
    return {
        "predictive_beta": float(b_pred),
        "predictive_test": fixed_b_t(prod_pred),
        "contemporaneous_beta": float(b_con),
        "contemporaneous_test": fixed_b_t(prod_con),
        "excess": excess, "base_ret": base_ret,
    }


def walk_forward_active(ret, xz, base_w, g=0.10, cap=0.10, min_train=60):
    """walk-forward OOS: train(expanding)서 pooled β, test(t+1)서 tilt active return."""
    base_ret = (ret * base_w).sum(axis=1)
    excess = ret.sub(base_ret, axis=0)
    dates = ret.index
    active = []
    for i in range(min_train, len(dates) - 1):
        tr = slice(0, i)
        # pooled β on train
        Xtr, Ytr = [], []
        for sl in SLEEVES:
            x = xz[sl].iloc[tr]; y = excess[sl].shift(-1).iloc[tr]
            d = pd.concat([x, y], axis=1).dropna()
            if len(d):
                Xtr.append(d.values[:, 0]); Ytr.append(d.values[:, 1])
        if not Xtr:
            continue
        Xtr = np.concatenate(Xtr); Ytr = np.concatenate(Ytr)
        Xc = Xtr - Xtr.mean(); Yc = Ytr - Ytr.mean()
        b = (Xc @ Yc) / (Xc @ Xc) if (Xc @ Xc) > 1e-12 else 0.0
        # predict excess at t (for t+1 return), cross-sleeve demean → cap → re-demean
        xt = np.array([xz[sl].iloc[i] for sl in SLEEVES])
        if np.any(np.isnan(xt)):
            continue
        pred = b * xt
        pred = pred - pred.mean()                  # cross-sleeve demean (∑=0)
        pred = np.clip(pred, -cap / g, cap / g)     # cap on tilt
        tilt = pred - pred.mean()                   # re-demean
        w = base_w + g * tilt
        w = np.clip(w, 0, None); w = w / w.sum()    # long-only renorm
        r_next = ret.iloc[i + 1].values
        active.append(float((w - base_w) @ r_next))  # active = (tilt) · r_{t+1}
    return np.array(active)


def main():
    ret, xz = build_panel()
    base_w = shrunk_inverse_vol(ret)
    n = len(ret)
    res = {"meta": {"n_months": n, "period": [str(ret.index[0])[:10], str(ret.index[-1])[:10]],
                    "sleeves": SLEEVES, "axis": {k: list(v) for k, v in AXIS.items()},
                    "base_weights": {sl: float(w) for sl, w in zip(SLEEVES, base_w)}}}
    # in-sample predictive vs contemporaneous
    pp = pooled_predictive(ret, xz, base_w)
    res["in_sample"] = {
        "predictive_beta": pp["predictive_beta"], "predictive_test": pp["predictive_test"],
        "contemporaneous_beta": pp["contemporaneous_beta"], "contemporaneous_test": pp["contemporaneous_test"],
    }
    # walk-forward OOS active
    act = walk_forward_active(ret, xz, base_w)
    res["oos_active"] = fixed_b_t(act)
    res["oos_active"]["ann_IR"] = (float(np.mean(act)) / float(np.std(act)) * np.sqrt(12)
                                   if len(act) and np.std(act) > 1e-12 else None)
    # verdict
    pred_sig = res["in_sample"]["predictive_test"].get("fixed_b_sig")
    oos_sig = res["oos_active"].get("fixed_b_sig")
    oos_pos = res["oos_active"].get("mean", 0) > 0
    res["verdict"] = ("ROTATION_LIVE" if (pred_sig and oos_sig and oos_pos)
                      else "STATIC_ONLY (rotation gate 탈락 → base=shrunk inverse-vol)")
    out = Path("D:/projects/Inv/study-research/eq_us/_sleeve_rotation_results.json")
    out.write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    print(json.dumps(res, indent=2, default=str))


if __name__ == "__main__":
    main()
