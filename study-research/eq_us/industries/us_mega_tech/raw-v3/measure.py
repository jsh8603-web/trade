# -*- coding: utf-8 -*-
"""measure.py — us_mega_tech §M v3 ★재작업 (S1 신호 + 자문 R2 4수정 + team-lead 코멘트 6종 + ★B″ 3R STEP 0/5).

★★B″ 3R 재분류 (2026-06-04, REWORK-B2-adjustment-plan §STEP 0/⑧ + §STEP 5/⑨):
  - STEP 0(⑧): us_mega_tech = ★verdict 없는 **exposure/timing overlay**. cross-sectional factor(family_1) = ★DIAGNOSTIC ONLY
    (유효 cross-section n≈7 = factor 추정 통계적 void → 강제 시 spurious factor 제조). verdict/PASS/FAIL 생성 폐기.
    보고 3종 = (1)factor exposure 한계기여(real_rate basket β) (2)concentration/crowding(reflexivity) (3)regime-conditional beta 안정성(family_2b).
    ★F-score/net-issuance 측정 폐기(F-score=high-BM 부실주 설계 mismatch / net-issuance=n=11 동질 buyback dispersion 고갈).
  - STEP 5(⑨): supply_chain_lead_lag +0.69 contemporaneous = ★Cohen-Frazzini 오용(동조) → ★lagged firm-pair(고객 hyper_t→공급사 semi_{t+1})
    재측정 + achieved power/MDE 동반(absence-of-evidence≠evidence-of-absence). semi↔hyperscaler 체인 한정.


frame v3 §M.1~M.12 + 자문 R2(.consult-us-method-R2.md, ★수정4 basket화) + dispatch-role-rework §2 + S1 theory-notes.md.

★측정 단위 = N=11 custom basket (compounder). ★핵심 = 자문 R2 수정4:
  - N=11 cross-sectional rank-IC = small-basket 통계력 약(Grinold IR=IC√breadth). → ★basket-level time-series
    factor exposure timing 우선 + cross-sectional 은 breadth-IR + magnitude 50~70% haircut hedge(§M.12), 단독 verdict 금지.
  - ⛔ sector-neutral z 비적용 = 단일 archetype(compounder) basket, 11종 모두 mega-tech 그룹 = peer 구조 없음
    (universe-demean = sector-neutral 동치). us_cyclical multi-sector 와 다름 (15axis G-A.5 사유 명시).

★family 측정 구조:
  - family_1 (cross-sectional unconditional 예측 IC, BY 검정) — vol_60/mom_6/mom_12_1/per_z/pbr_z/capex_z
  - family_1b (★basket-level time-series factor exposure timing) — real_rate/VIX/dollar/rate basket β + timing
  - family_2 (regime-conditional, VIX regime 사전지정, 별 m)
  - family_3 (driver β attribution, BY 제외) — basket β (family_1b _multivariate/단독 겸용)

★자문 R2 수정 1-3 (us_cyclical 이식):
  1. family 3분리 (위)
  2. M_eff (Li-Ji 2005 eigenvalue, test-stat 상관행렬) — family_1 BY threshold
  3. eff_N 이중보정 (시계열 T/h × 횡단면 N/(1+(N-1)ρ̄)), ★mega-tech ρ̄ 높아 횡단면 eff_N 급감

★team-lead 코멘트 6종:
  1. real_rate β = 최우선 multivariate 재측정 (Gormsen-Lazarus duration, defensive −0.066 보다 강 음 기대, 약하면 정직)
  2. per_z expected null 측정 (expensive_trap "가설 확인", 측정 생략 금지)
  3. capex_z 양방향 (over-investment 음 vs productive-growth 양, prior 없이 데이터 판정)
  4. vol_60 basket+cross 병행 (cross-sec small-basket hedge 강)
  5. G-B 인지 (basket-level 도 유의 0 AND 최강 raw_p > threshold×2 → 단정 ⛔ 보고)
  6. reflexivity H9 = risk overlay(신호 아님) + sector-neutral 비적용 15axis G-A.5
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
FRED = Path("D:/projects/Inv/study-research/eq_us_defensive/raw/fred")  # us_defensive FRED CSV 재사용

# US net-cost (mega-cap 최고유동성, STT 없음)
COMMISSION = 0.0005
SPREAD_HALF = 0.0002


def load():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    amt = pd.read_parquet(DATA / "amount.parquet"); amt.index = pd.to_datetime(amt.index)
    ed = pd.read_parquet(DATA / "edgar_fundamentals.parquet")
    uni = json.loads((DATA / "universe.json").read_text(encoding="utf-8"))
    return px, amt, ed, uni


# ── FRED 거시 (real_rate/VIX/dollar/rate) ──
def load_fred_series(fred_id):
    f = FRED / f"{fred_id}.csv"
    if not f.exists():
        return None
    s = pd.read_csv(f)
    datecol = s.columns[0]; valcol = s.columns[1]
    ser = pd.Series(pd.to_numeric(s[valcol], errors="coerce").values, index=pd.to_datetime(s[datecol]))
    return ser.dropna()


def macro_monthly():
    """월말 거시 level + Δ. real_rate=DFII10 / rate=DGS10 / vix=VIXCLS / dollar=DTWEXBGS."""
    out_level, out_chg = {}, {}
    specs = [("DFII10", "real_rate", "diff"), ("DGS10", "rate", "diff"),
             ("VIXCLS", "vix", "diff"), ("DTWEXBGS", "dollar", "pct")]
    for fid, name, kind in specs:
        s = load_fred_series(fid)
        if s is None:
            print(f"  ★FRED {fid} 부재 (skip {name})", flush=True); continue
        m = s.resample("ME").last()
        out_level[name] = m
        out_chg[name] = m.diff() if kind == "diff" else m.pct_change()
    return pd.DataFrame(out_level), pd.DataFrame(out_chg)


# ── EDGAR PIT 패널 (cross-sectional valuation) ──
def _ed_prep(ed):
    ed = ed.copy()
    ed["filed_dt"] = pd.to_datetime(ed["filed"], errors="coerce")
    return ed.dropna(subset=["filed_dt", "val"])


def _latest_pit(sub_concept, dt):
    av = sub_concept[sub_concept["filed_dt"] <= dt]
    return av["val"].iloc[-1] if len(av) else np.nan


def _ttm(df, dt):
    av = df[df["filed_dt"] <= dt]
    if len(av) == 0:
        return np.nan
    fy = av[av["fp"] == "FY"]
    if len(fy):
        return fy["val"].iloc[-1]
    q = av[av["fp"].isin(["Q1", "Q2", "Q3", "Q4"])].drop_duplicates("end").tail(4)
    return q["val"].sum() if len(q) >= 4 else np.nan


def build_pit_panels(px, ed):
    """월말 PIT 패널: pbr, per, capex (capex/equity intensity, H6). filed PIT(lookahead 회피)."""
    pxm = px.resample("ME").last(); midx = pxm.index
    ed = _ed_prep(ed)
    by_t = {t: ed[ed["ticker"] == t] for t in px.columns}
    panels = {k: {} for k in ["pbr", "per", "capex"]}
    for t in px.columns:
        sub = by_t[t]
        g = lambda c: sub[sub["concept"] == c].sort_values("filed_dt")
        eq, ni, sh, cx = g("equity"), g("net_income"), g("shares"), g("capex")
        ser = {k: pd.Series(index=midx, dtype=float) for k in panels}
        for dt in midx:
            price = pxm.loc[dt, t]
            if np.isnan(price):
                continue
            shares = _latest_pit(sh, dt)
            if np.isnan(shares) or shares <= 0:
                continue
            mktcap = price * shares
            equity = _latest_pit(eq, dt)
            if equity and equity > 0:
                ser["pbr"][dt] = mktcap / equity
            ttm_ni = _ttm(ni, dt)
            if ttm_ni and ttm_ni > 0:
                ser["per"][dt] = mktcap / ttm_ni
            cxttm = _ttm(cx, dt)
            if cxttm and equity and equity > 0:
                ser["capex"][dt] = cxttm / equity   # capex/equity intensity (H6)
        for k in panels:
            panels[k][t] = ser[k]
    return {k: pd.DataFrame(v) for k, v in panels.items()}


def cs_z(panel):
    """★universe-demean z. ⛔ sector-neutral 비적용 = 단일 archetype basket(peer 구조 없음).
    11종 모두 mega-tech 그룹 → sector-neutral = universe-demean 동치(별 sector factor 없음).
    (us_cyclical multi-sector 와 대조, 15axis G-A.5 사유)."""
    mu = panel.mean(axis=1); sd = panel.std(axis=1, ddof=1)
    return panel.sub(mu, axis=0).div(sd.replace(0, np.nan), axis=0)


# ── IC / SE / OOS (us_cyclical 미러, min_n=6 small-basket) ──
def cs_ic(sig, fwd, min_n=6):
    idx = sig.index.intersection(fwd.index); ics, ns, dates = [], [], []
    for dt in idx:
        sv = sig.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
        c = sv.index.intersection(rv.index)
        if len(c) < min_n:
            continue
        rho, _ = stats.spearmanr(sv.loc[c], rv.loc[c])
        if not np.isnan(rho):
            ics.append(rho); ns.append(len(c)); dates.append(dt)
    return pd.Series(ics, index=dates), pd.Series(ns, index=dates)


def nw_se(ic, lags):
    x = ic.values.astype(float); n = len(x)
    if n < 3:
        return np.nan
    e = x - x.mean(); g0 = (e @ e) / n; var = g0
    for k in range(1, min(lags, n - 1) + 1):
        w = 1 - k / (lags + 1); var += 2 * w * (e[k:] @ e[:-k]) / n
    return float(np.sqrt(max(var, 1e-12) / n))


def block_boot(x, block=6, B=2000, seed=42):
    block = max(int(block), 1)
    rng = np.random.default_rng(seed); n = len(x); nb = int(np.ceil(n / block)); m = []
    for _ in range(B):
        if n - block + 1 <= 0:
            return (np.nan, np.nan)
        st = rng.integers(0, n - block + 1, size=nb)
        m.append(np.concatenate([x[s:s+block] for s in st])[:n].mean())
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def cpcv(sig, fwd, h, n_splits=6, n_test=2):
    ic, _ = cs_ic(sig, fwd)
    if len(ic) < n_splits * 2:
        return dict(oos_hit=np.nan, n_folds=0)
    months = ic.index.tolist(); fs = len(months) // n_splits
    folds = [months[i*fs:(i+1)*fs] for i in range(n_splits)]
    from itertools import combinations
    oos = []
    for combo in combinations(range(n_splits), n_test):
        tm = set()
        for fi in combo: tm.update(folds[fi])
        sub = ic[ic.index.isin(tm)]
        if len(sub) >= 2: oos.append(sub.mean())
    oos = np.array(oos); fsign = np.sign(ic.mean())
    return dict(oos_ic_mean=float(oos.mean()), oos_hit=float((np.sign(oos) == fsign).mean()),
                n_folds=len(oos), purge_months=h)


def within_period(ic):
    if len(ic) < 12:
        return None
    by = ic.groupby(ic.index.year).mean(); fs = np.sign(ic.mean())
    return float((np.sign(by) == fs).mean())


def leave_episode(ic):
    if len(ic) < 24:
        return None
    roll = ic.rolling(12).mean(); pe = roll.idxmax()
    ps = max(0, ic.index.get_loc(pe) - 11)
    drop = ic.index[ps:ic.index.get_loc(pe) + 1]; rest = ic.drop(drop)
    return dict(full=round(float(ic.mean()), 4), ex_peak=round(float(rest.mean()), 4),
                survive=bool(np.sign(rest.mean()) == np.sign(ic.mean()) and abs(rest.mean()) > 0.3 * abs(ic.mean())))


# ── ★eff_N 이중보정 (자문 R2 수정3) ──
def eff_n_double(ic, ns, h, rho_bar):
    """시계열 eff_N ≈ T/h × 횡단면 eff_N = N/(1+(N-1)ρ̄). ★mega-tech ρ̄ 높아 횡단면 급감(small-basket degenerate)."""
    T = len(ic)
    ts_effN = T / h
    avgN = float(ns.mean()) if len(ns) else np.nan
    cross_effN = avgN / (1 + (avgN - 1) * rho_bar) if avgN and avgN > 1 else avgN
    return dict(T=T, ts_eff_n=round(ts_effN, 1),
                avg_cross_n=round(avgN, 1) if not np.isnan(avgN) else None,
                cross_eff_n=round(cross_effN, 2) if cross_effN and not np.isnan(cross_effN) else None,
                rho_bar=round(rho_bar, 3))


def breadth_ir(ic_mean, cross_eff_n, ts_eff_n):
    """breadth-IR = IC·√(유효 횡단면 breadth × 시계열 eff_N). ★ρ̄ 보정된 cross_eff_n 사용(과대 방지)."""
    return round(float(ic_mean) * np.sqrt(max(cross_eff_n or 1, 1) * max(ts_eff_n, 1)), 3)


def m_eff_liji(tstat_corr):
    """M_eff = Σ_i [I(λ_i≥1) + (λ_i - ⌊λ_i⌋)]. test-stat(IC 시계열) 상관행렬."""
    eigs = np.linalg.eigvalsh(tstat_corr)
    eigs = np.clip(eigs, 0, None)
    return float(sum((1.0 if l >= 1 else 0.0) + (l - np.floor(l)) for l in eigs))


def benjamini_yekutieli(pvals, m_override=None, q=0.10):
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    raw_m = len(items)
    if raw_m == 0:
        return {"m": 0}
    m = m_override if m_override is not None else raw_m
    items.sort(key=lambda x: x[1])
    cm = sum(1.0 / i for i in range(1, int(np.ceil(m)) + 1)); surv = []
    for r, (k, p) in enumerate(items, 1):
        if p <= (r / m) * q / cm: surv = [items[j][0] for j in range(r)]
    rank1_thr = (1.0 / m) * q / cm
    return dict(m_raw=raw_m, m_eff=round(m, 2), by_factor=round(cm, 3), survivors_BY=surv,
                raw_p_min=round(items[0][1], 5), raw_p_min_key=items[0][0],
                rank1_threshold=round(rank1_thr, 6), q=q)


def intra_basket_rho(px):
    """★횡단면 평균 pairwise 상관 ρ̄ (월간 수익). eff_N·breadth-IR 보정용."""
    retm = px.resample("ME").last().pct_change().dropna(how="all")
    cm = retm.corr().values; n = cm.shape[0]
    return float((cm.sum() - n) / (n * (n - 1))) if n > 1 else 0.0


def measure_sig_cs(sig, fwd, h, name, rho_bar):
    """family_1 cross-sectional IC + small-basket hedge(eff_N 이중보정 + breadth-IR ρ̄ 보정)."""
    ic, ns = cs_ic(sig, fwd)
    if len(ic) < 6:
        return None
    n = len(ic); mean = float(ic.mean())
    se = nw_se(ic, h); t = mean / se if se and se > 0 else np.nan
    p = float(2 * (1 - stats.t.cdf(abs(t), df=max(n-1, 1)))) if not np.isnan(t) else np.nan
    ci = block_boot(ic.values, max(3, min(h, n//3)), 2000) if n >= 6 else (np.nan, np.nan)
    effn = eff_n_double(ic, ns, h, rho_bar)
    bir = breadth_ir(mean, effn["cross_eff_n"], effn["ts_eff_n"])
    return dict(signal=name, h_months=h, ic_mean=round(mean, 4), n_months=n,
                t_nw=round(t, 2) if not np.isnan(t) else None,
                p_value_nw=round(p, 4) if not np.isnan(p) else None,
                ci95_block_boot=[round(ci[0], 4), round(ci[1], 4)],
                cpcv=cpcv(sig, fwd, h), within_period=within_period(ic),
                leave_episode=leave_episode(ic),
                avg_universe_n=effn["avg_cross_n"], cross_eff_n=effn["cross_eff_n"],
                ts_eff_n=effn["ts_eff_n"], rho_bar=effn["rho_bar"], breadth_ir=bir,
                _ic_series=ic)


# ── ★family_1b: basket-level time-series factor exposure timing (자문 R2 수정4 핵심) ──
def basket_factor_beta(basket_ret, macro_chg):
    """★basket EW 월수익 ~ 거시 Δ (multivariate HAC + 단독). real_rate/vix/dollar/rate.
    ★team-lead 코멘트1: real_rate = multivariate 재측정. Gormsen-Lazarus duration.
    family_3 attribution(BY 제외) 겸용."""
    import statsmodels.api as sm
    out = {}
    for f in macro_chg.columns:
        df = pd.concat([basket_ret.rename("y"), macro_chg[f]], axis=1).dropna()
        if len(df) < 24:
            out[f"{f}_uni"] = dict(note="insufficient", n=len(df)); continue
        X = sm.add_constant(df[[f]])
        m = sm.OLS(df["y"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
        out[f"{f}_uni"] = dict(beta=round(float(m.params[f]), 4), t=round(float(m.tvalues[f]), 2),
                               ci95=[round(float(m.conf_int().loc[f, 0]), 4), round(float(m.conf_int().loc[f, 1]), 4)],
                               n=len(df), r2=round(float(m.rsquared), 3))
    cols = list(macro_chg.columns)
    dfm = pd.concat([basket_ret.rename("y"), macro_chg[cols]], axis=1).dropna()
    if len(dfm) >= 24:
        X = sm.add_constant(dfm[cols])
        mm = sm.OLS(dfm["y"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
        out["_multivariate"] = {c: dict(beta=round(float(mm.params[c]), 4), t=round(float(mm.tvalues[c]), 2),
                                        ci95=[round(float(mm.conf_int().loc[c, 0]), 4), round(float(mm.conf_int().loc[c, 1]), 4)])
                                for c in cols}
        out["_multivariate"]["_meta"] = dict(n=len(dfm), r2=round(float(mm.rsquared), 3))
    return out


def basket_factor_timing(basket_ret, factor_chg, h, name):
    """★basket-level factor exposure TIMING: factor 변화가 basket forward 수익을 예측하는가
    (시계열 IC = Spearman(factor_signal_t, basket_fwd_ret)). real_rate↑→forward↓(음) 예상."""
    fwd = basket_ret.shift(-h).rolling(h).sum() if h > 1 else basket_ret.shift(-h)
    df = pd.concat([factor_chg.rename("sig"), fwd.rename("fwd")], axis=1).dropna()
    if len(df) < 24:
        return dict(signal=name, note="insufficient", n=len(df))
    rho, p = stats.spearmanr(df["sig"], df["fwd"])
    return dict(signal=name, h_months=h, ts_ic=round(float(rho), 4), p_value=round(float(p), 4),
                n=len(df), note="basket-level factor→forward timing (시계열 Spearman).")


def basket_beta_robustness(px, tags, macro_chg, macro_level):
    """★real_rate β robustness (team-lead 코멘트1 = 최우선 검증):
    (a) sub-basket(mag7 vs ai_semi) β 부호 일관성 (long-duration 공통이면 둘 다 음)
    (b) leave-year (단일 연도 의존 X)
    (c) level vs Δ (DFII10 Δ vs level — duration 이론은 Δreal_rate)
    (d) ★us_defensive 비교(−0.066) — mega-tech 더 강해야(이론)."""
    import statsmodels.api as sm
    pxm = px.resample("ME").last(); retm = pxm.pct_change()
    out = {}
    def _beta(ret, feat_name, chg=True):
        f = (macro_chg if chg else macro_level)[feat_name]
        df = pd.concat([ret.rename("y"), f.rename("x")], axis=1).dropna()
        if len(df) < 24:
            return None
        X = sm.add_constant(df[["x"]])
        m = sm.OLS(df["y"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
        return dict(beta=round(float(m.params["x"]), 4), t=round(float(m.tvalues["x"]), 2), n=len(df))
    # (a) sub-basket real_rate β
    for sub in ["mag7", "ai_semi"]:
        cols = [t for t, s in tags.items() if s == sub and t in retm.columns]
        if cols:
            out[f"real_rate_{sub}"] = _beta(retm[cols].mean(axis=1), "real_rate")
    # (b) leave-year (real_rate Δ, full basket)
    ew = retm.mean(axis=1)
    df = pd.concat([ew.rename("y"), macro_chg["real_rate"].rename("x")], axis=1).dropna()
    ly = {}
    for y in sorted(set(df.index.year)):
        sub = df[df.index.year != y]
        if len(sub) >= 24:
            X = sm.add_constant(sub[["x"]]); m = sm.OLS(sub["y"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
            ly[str(y)] = round(float(m.params["x"]), 4)
    out["real_rate_leave_year"] = dict(per_year_ex=ly,
                                       all_negative=bool(all(v < 0 for v in ly.values())) if ly else None,
                                       range=[min(ly.values()), max(ly.values())] if ly else None)
    # (c) level vs Δ
    out["real_rate_level_beta"] = _beta(ew, "real_rate", chg=False)
    out["real_rate_diff_beta"] = _beta(ew, "real_rate", chg=True)
    out["_note"] = ("★real_rate Δ β robustness. duration 이론(Gormsen-Lazarus) = long-duration growth 강 음. "
                    "us_defensive real_rate β=−0.066(t−6.78) 대비 mega-tech 더 강 음 기대.")
    return out


# ── family_2: regime-conditional (VIX regime 사전지정) ──
def regime_conditional(signals_cs, fwd_map, vix_level, top_q=0.6):
    if vix_level is None or len(vix_level) == 0:
        return {"note": "vix 부재"}
    thr = vix_level.quantile(top_q)
    out = {}
    for sname, sig in signals_cs.items():
        fwd = fwd_map[sname]
        ic, _ = cs_ic(sig, fwd); ic = ic.dropna()
        if len(ic) < 24:
            continue
        v_al = vix_level.reindex(ic.index).ffill()
        hi = ic[v_al >= thr]; lo = ic[v_al < thr]
        if len(hi) < 8 or len(lo) < 8:
            continue
        hci = block_boot(hi.values, 3, 1000) if len(hi) >= 6 else (np.nan, np.nan)
        lci = block_boot(lo.values, 3, 1000) if len(lo) >= 6 else (np.nan, np.nan)
        out[sname] = dict(ic_high_vix=round(float(hi.mean()), 4), n_high=len(hi),
                          ic_low_vix=round(float(lo.mean()), 4), n_low=len(lo),
                          ci_high=[round(hci[0],4), round(hci[1],4)],
                          ci_low=[round(lci[0],4), round(lci[1],4)],
                          diff=round(float(hi.mean() - lo.mean()), 4))
    return dict(regime_var="vix", high_vix_thr=round(float(thr), 2), top_q=top_q, results=out,
                note="★사전지정 regime(상위 40% VIX=risk-off). family_2 별 m. small-n hedge(block-boot CI).")


# ── ★_b2_stats 재사용 (B″ size-valid: fixed-b CV + wild-cluster, us_defensive 공용 모듈) ──
sys.path.insert(0, str(Path("D:/projects/Inv/study-research/eq_us/industries/us_defensive/raw-v3")))
try:
    from _b2_stats import fixed_b_cv, wild_cluster_boot, effective_n, persistence_block
    _HAS_B2 = True
except Exception as _e:
    _HAS_B2 = False


# ── ★family_2b: regime interaction term (G-A.5 의무 = family_1 미생존 신호 살리기) ──
def regime_interaction(sig, fwd, regime_chg, h, name, subset_mask=None):
    """★G-A.5: family_1 BY 미생존이어도 regime split 부호 갈리면 interaction term 테스트(자유도 보존).
    cross-sec IC_t ~ regime_chg_t (IC 시계열이 regime 변화에 반응하는가). per_z/capex 가 VIX regime 부호 갈림.
    ★B″ STEP 2(⑦) size-valid: 구 asymptotic HAC + ★fixed-b CV(Kiefer-Vogelsang) + wild-cluster bootstrap.
    subset_mask = post-AI(2023~) 등 small-block 부분표본 (n 한자릿수 block → size-invalid 위험)."""
    import statsmodels.api as sm
    ic, _ = cs_ic(sig, fwd)
    if len(ic) < 12:
        return dict(signal=name, note="insufficient", n=len(ic))
    df = pd.concat([ic.rename("ic"), regime_chg.rename("reg")], axis=1).dropna()
    if subset_mask is not None:
        df = df[df.index >= subset_mask]
    if len(df) < 12:
        return dict(signal=name, note="insufficient_subset", n=len(df))
    X = sm.add_constant(df[["reg"]])
    blk = persistence_block(df["ic"].values) if _HAS_B2 else 3
    m = sm.OLS(df["ic"], X).fit(cov_type="HAC", cov_kwds={"maxlags": blk})
    t_hac = float(m.tvalues["reg"])
    out = dict(signal=name, h_months=h, interaction_beta=round(float(m.params["reg"]), 4),
               t_hac=round(t_hac, 2), n=len(df), hac_lag=blk,
               note="★IC~regime_chg interaction. ★B″ size-valid 재검정(fixed-b CV + wild-cluster).")
    # ★B″ size-valid: fixed-b CV + wild-cluster
    if _HAS_B2:
        eff = effective_n(df["ic"].values)
        fb = fixed_b_cv(len(df), blk)
        out["effective_n"] = eff["n_eff"]; out["effective_n_detail"] = eff
        out["fixed_b_cv"] = fb["cv_5pct"]; out["fixed_b_b"] = fb["b"]
        out["size_valid_fixed_b"] = bool(abs(t_hac) > fb["cv_5pct"])   # ★|t|>CV = size-valid 유의
        out["asymptotic_sig"] = bool(abs(t_hac) > 1.96)
        wc = wild_cluster_boot(df["ic"], X, "reg", block=blk, B=2000)
        out["p_wild_cluster"] = wc.get("p_wild_cluster")
        out["wild_cluster_sig"] = bool(wc.get("p_wild_cluster") is not None and wc["p_wild_cluster"] < 0.05)
        out["verdict_size_valid"] = ("SURVIVE" if (out["size_valid_fixed_b"] and out["wild_cluster_sig"]) else
                                     "DIE (asymptotic artifact)" if out["asymptotic_sig"] else "n/a")
    return out


# ── ★directional spillover 후보 (★B″ STEP 5/⑨: Cohen-Frazzini lagged firm-pair, G-A.3 의무) ──
def _achieved_power_mde(n, alpha=0.05, target_power=0.80):
    """★achieved power/MDE (B″ STEP 5 = absence-of-evidence ≠ evidence-of-absence).
    Pearson corr 검정의 MDE (target_power 에서 검출 가능한 최소 |ρ|) + 관측 n 에서의 power 계산.
    Fisher-z 근사: z_r = atanh(ρ), SE = 1/√(n−3). MDE = tanh((z_α/2 + z_power)/√(n−3))."""
    from scipy.stats import norm
    if n < 5:
        return dict(mde=None, note="n<5 power 계산 불가")
    se = 1.0 / np.sqrt(n - 3)
    z_a = norm.ppf(1 - alpha / 2); z_p = norm.ppf(target_power)
    mde = float(np.tanh((z_a + z_p) * se))
    return dict(mde_rho=round(mde, 3), n=n, target_power=target_power, alpha=alpha,
                note=f"이 표본(n={n})에서 power={target_power}로 검출 가능한 최소 |ρ|={round(mde,3)}. 관측 |ρ|<MDE면 underpowered(증거부재≠부재증거).")


def _power_at_rho(n, rho, alpha=0.05):
    """관측 ρ 에서의 achieved power."""
    from scipy.stats import norm
    if n < 5 or rho is None or abs(rho) < 1e-9:
        return None
    se = 1.0 / np.sqrt(n - 3); z_a = norm.ppf(1 - alpha / 2)
    zr = np.arctanh(min(abs(rho), 0.999))
    return round(float(norm.cdf(zr / se - z_a) + norm.cdf(-zr / se - z_a)), 3)


def supply_chain_lead_lag(px, tags):
    """★B″ STEP 5/⑨ (Cohen-Frazzini 2008 RFS lagged firm-pair): 기존 +0.69 contemporaneous(k=0)는
    ★오용 = 같은 risk cluster 동조일 뿐 tradeable alpha 아님. CF = 고객 return_t → 공급사 return_{t+1}
    (고객 정보가 공급사에 느리게 반영). ★AI capex 체인: hyperscaler(MSFT/AMZN/GOOGL/META)=고객(capex로 칩 구매),
    semi(NVDA/AVGO/AMD/ASML)=공급사. → ★CF 정합 방향 = hyperscaler_t → semi_{t+1}(lagged).
    ★양방향 측정(데이터 판정) + achieved power/MDE 동반(n 작아 null=power 실패 구분). semi↔hyperscaler 체인 한정."""
    pxm = px.resample("ME").last(); retm = pxm.pct_change()
    hyper = [t for t in ["MSFT", "AMZN", "GOOGL", "META"] if t in retm.columns]
    semi = [t for t, s in tags.items() if s in ("ai_semi", "ai_semi_adr") and t in retm.columns]
    semi += [t for t in ["NVDA"] if t in retm.columns and t not in semi]
    if not hyper or not semi:
        return {"note": "그룹 부재"}
    hr = retm[hyper].mean(axis=1); sr = retm[semi].mean(axis=1)
    out = {"hyperscaler_customer": hyper, "semi_supplier": semi,
           "cf_direction": "Cohen-Frazzini = 고객(hyperscaler)_t → 공급사(semi)_{t+1} lagged. k=0=contemporaneous(오용, 동조)."}
    # ★(1) contemporaneous (k=0) = 참고만(오용 명시)
    df0 = pd.concat([hr.rename("h"), sr.rename("s")], axis=1).dropna()
    if len(df0) >= 12:
        r0, p0 = stats.spearmanr(df0["h"], df0["s"])
        out["contemporaneous_k0"] = dict(corr=round(float(r0), 4), p=round(float(p0), 4), n=len(df0),
                                         note="★오용 경고: 동시 동조(같은 risk cluster) = tradeable alpha 아님.")
    # ★(2) CF lagged: 고객(hyper)_t → 공급사(semi)_{t+1} (CF 정합 방향)
    for k in [1, 2, 3]:
        df = pd.concat([hr.shift(k).rename("h_lag"), sr.rename("s")], axis=1).dropna()
        if len(df) >= 12:
            r, p = stats.spearmanr(df["h_lag"], df["s"])
            mde = _achieved_power_mde(len(df)); pw = _power_at_rho(len(df), r)
            out[f"cf_customer_lead_{k}m"] = dict(corr=round(float(r), 4), p=round(float(p), 4), n=len(df),
                mde_rho=mde.get("mde_rho"), achieved_power=pw,
                underpowered=bool(pw is not None and pw < 0.80),
                note=f"★CF 정합: 고객(hyper)_t−{k} → 공급사(semi)_t. tradeable lagged.")
    # ★(3) 역방향 반증(semi_t → hyper_{t+1}): AI 수요 신호 선반영 가설 (데이터 판정)
    for k in [1]:
        df = pd.concat([sr.shift(k).rename("s_lag"), hr.rename("h")], axis=1).dropna()
        if len(df) >= 12:
            r, p = stats.spearmanr(df["s_lag"], df["h"])
            pw = _power_at_rho(len(df), r)
            out[f"reverse_semi_lead_{k}m"] = dict(corr=round(float(r), 4), p=round(float(p), 4), n=len(df),
                achieved_power=pw, note="★역방향 반증(semi_t → hyper_t+1). CF 아닌 수요선반영 가설.")
    out["mde_summary"] = _achieved_power_mde(len(df0) if len(df0) else 0)
    out["note"] = ("★B″ STEP 5: CF lagged firm-pair(고객 hyper_t→공급사 semi_t+1). k=0 contemporaneous=오용(동조). "
                   "achieved power/MDE 동반(absence-of-evidence≠evidence-of-absence). semi↔hyperscaler 체인 한정. DY 후보(supervisor 통합).")
    return out


# ── ★reflexivity monitor (H9, risk overlay = 신호 아님) ──
def reflexivity_monitor(px):
    ret = px.pct_change()
    corrs = []
    for i in range(60, len(ret), 5):
        window = ret.iloc[i-60:i]
        cm = window.corr().values; n = cm.shape[0]
        avg_corr = (cm.sum() - n) / (n * (n - 1)) if n > 1 else np.nan
        corrs.append((ret.index[i], avg_corr))
    corr_s = pd.Series(dict(corrs))
    pxm = px.resample("ME").last(); retm = pxm.pct_change()
    ew_3m = retm.mean(axis=1).rolling(3).sum()
    top3 = [c for c in ["NVDA", "AAPL", "MSFT"] if c in retm.columns]
    cw_3m = retm[top3].mean(axis=1).rolling(3).sum() if top3 else ew_3m
    breadth_spread = (ew_3m - cw_3m)
    cd = corr_s.dropna()
    recent = float(cd.iloc[-12:].mean()) if len(cd) else None
    return dict(
        avg_intra_corr_recent=round(recent, 3) if recent is not None else None,
        avg_intra_corr_full=round(float(cd.mean()), 3) if len(cd) else None,
        intra_corr_p75=round(float(cd.quantile(0.75)), 3) if len(cd) else None,
        breadth_spread_recent=round(float(breadth_spread.dropna().iloc[-3:].mean()), 4) if len(breadth_spread.dropna()) else None,
        n_high_corr_months=int((cd > 0.70).sum()),
        current_status="정점 아님 (corr<0.70 AND breadth 양)" if (recent is not None and recent < 0.70) else "점검",
        note="★H9 risk overlay(신호 아님 = de-risk throttle). corr>0.70-0.75 AND breadth<-3~-5%p 동시 = cap-down(supervisor).")


def main():
    px, amt, ed, uni = load()
    pxm = px.resample("ME").last()
    print(f"universe={px.shape[1]} basket, {px.shape[0]} days {px.index.min().date()}~{px.index.max().date()}", flush=True)

    rho_bar = intra_basket_rho(px)
    print(f"★intra-basket ρ̄ = {rho_bar:.3f} (eff_N·breadth-IR 보정용, mega-tech 고상관)", flush=True)

    macro_level, macro_chg = macro_monthly()
    print(f"macro factors: {list(macro_chg.columns)} (level+Δ)", flush=True)

    # ── 가격 cross-sectional 신호 (★universe-demean, sector-neutral 비적용) ──
    mom_12_1 = cs_z(pxm.shift(1) / pxm.shift(12) - 1)
    mom_6 = cs_z(pxm / pxm.shift(6) - 1)
    ret_d = px.pct_change(); vol_60 = cs_z((ret_d.rolling(60).std() * np.sqrt(252)).resample("ME").last())

    P = build_pit_panels(px, ed)
    for k, v in P.items():
        print(f"  panel {k:8} shape={v.shape} cov={int(v.notna().sum().sum())}", flush=True)
    per_z, pbr_z, capex_z = cs_z(P["per"]), cs_z(P["pbr"]), cs_z(P["capex"])

    signals_cs = {
        "vol_60": vol_60, "mom_6": mom_6, "mom_12_1": mom_12_1,
        "per_z": per_z, "pbr_z": pbr_z, "capex_z": capex_z,
    }
    horizons = {"1M": 1, "3M": 3, "6M": 6, "12M": 12, "24M_value": 24}

    # ── ★family_1: cross-sectional IC = ★B″ STEP 0(⑧) DIAGNOSTIC ONLY, verdict 생성 폐기 ──
    # ★유효 cross-section n≈7(avg 8.x, valuation 가용 7~8) = factor 추정 통계적 void → 강제 시 spurious factor 제조.
    #   → "참고 지표(diagnostic)"로만, PASS/FAIL/verdict 라벨 제거. BY/M_eff = diagnostic 참고치(verdict 근거 아님).
    eff_cross_n = round(float(pd.concat([signals_cs["per_z"], signals_cs["pbr_z"], signals_cs["capex_z"]], axis=1).notna().sum(axis=1).replace(0, np.nan).dropna().median() / 3), 1) if True else None
    indicators, pvals, ic_series = {}, {}, {}
    for sname, sig in signals_cs.items():
        for hname, h in horizons.items():
            fwd = pxm.shift(-h) / pxm - 1
            r = measure_sig_cs(sig, fwd, h, f"{sname}__{hname}", rho_bar)
            if r:
                key = f"{sname}__{hname}"
                ic_series[key] = r.pop("_ic_series")
                r["role"] = "diagnostic_no_verdict"   # ★B″ STEP 0: verdict 생성 폐기, 참고 지표만
                indicators[key] = r; pvals[key] = r["p_value_nw"]

    keys = list(ic_series.keys())
    ic_df = pd.DataFrame({k: ic_series[k] for k in keys})
    tcorr = ic_df.corr().fillna(0).values; np.fill_diagonal(tcorr, 1.0)
    m_eff = m_eff_liji(tcorr)
    by_meff = benjamini_yekutieli(pvals, m_override=m_eff)
    by_raw = benjamini_yekutieli(pvals, m_override=None)

    pvals_nd = {k: v for k, v in pvals.items() if not k.endswith("24M_value")}
    keys_nd = [k for k in keys if not k.endswith("24M_value")]
    ic_df_nd = ic_df[keys_nd]; tcorr_nd = ic_df_nd.corr().fillna(0).values; np.fill_diagonal(tcorr_nd, 1.0)
    m_eff_nd = m_eff_liji(tcorr_nd)
    by_meff_nd = benjamini_yekutieli(pvals_nd, m_override=m_eff_nd)

    # ── ★family_1b: basket-level factor timing + β (자문 수정4 핵심) ──
    basket_ret = pxm.pct_change().mean(axis=1)
    fam1b_beta = basket_factor_beta(basket_ret, macro_chg)
    fam1b_timing = {}
    for fac in macro_chg.columns:
        for h in [3, 6, 12]:
            fam1b_timing[f"{fac}__{h}M"] = basket_factor_timing(basket_ret, macro_chg[fac], h, f"{fac}__{h}M")
    # ★real_rate β robustness (team-lead 코멘트1 최우선)
    fam1b_robust = basket_beta_robustness(px, uni["tickers"], macro_chg, macro_level)

    # ★capex AI-regime split (코멘트3: over-investment vs productive growth, 2023~ AI cycle)
    capex_regime = {}
    fwd12 = pxm.shift(-12) / pxm - 1
    ic_cx, _ = cs_ic(signals_cs["capex_z"], fwd12)
    if len(ic_cx) >= 24:
        pre = ic_cx[ic_cx.index < "2023-01-01"]; post = ic_cx[ic_cx.index >= "2023-01-01"]
        capex_regime = dict(pre_ai_ic=round(float(pre.mean()), 4) if len(pre) else None, n_pre=len(pre),
                            post_ai_ic=round(float(post.mean()), 4) if len(post) else None, n_post=len(post),
                            note="★H6 capex: pre-AI vs post-AI(2023~) 12M IC. 음=over-investment penalty(Cooper-Gulen-Schill) / 양=productive growth. 부호 데이터 판정.")

    vix_level = macro_level["vix"] if "vix" in macro_level else None
    reg_signals = {s: signals_cs[s] for s in ["vol_60", "mom_6", "per_z", "capex_z"]}
    reg_fwd = {s: pxm.shift(-12) / pxm - 1 for s in reg_signals}
    fam2 = regime_conditional(reg_signals, reg_fwd, vix_level)

    # ★family_2b: regime interaction term (G-A.5 = family_1 미생존 per_z/capex 살리기)
    # ★B″ STEP 2(⑦): 구 asymptotic HAC + ★fixed-b CV + wild-cluster size-valid 재검정.
    fam2b = {}
    if "vix" in macro_chg:
        for sname in ["per_z", "capex_z", "vol_60"]:
            fam2b[sname] = regime_interaction(signals_cs[sname], fwd12, macro_chg["vix"], 12, sname)
        # ★capex post-AI(2023~) small-block (n=29) = payout 동일 size-invalid 시나리오 = 별도 size-valid 재검정
        fam2b["capex_z_postAI"] = regime_interaction(signals_cs["capex_z"], fwd12, macro_chg["vix"], 12,
                                                     "capex_z_postAI", subset_mask=pd.Timestamp("2023-01-01"))

    # ★directional spillover 후보 (G-A.3 = [] 금지, DY 선행신호 후보 보고)
    spillover = supply_chain_lead_lag(px, uni["tickers"])

    reflex = reflexivity_monitor(px)

    listing = px.notna().sum()
    survivor = dict(n_full_history=int((listing >= px.shape[0] * 0.95).sum()),
                    n_partial=int((listing < px.shape[0] * 0.95).sum()),
                    note="Mag7 basket = 현 대형주(생존). PIT 멤버십(NVDA pre/post-AI, TSLA 2020 편입) = collector_plan medium.")

    results = {
        "meta": {"universe_n": int(px.shape[1]), "intra_basket_rho_bar": round(rho_bar, 3),
                 "date_range": [str(px.index.min().date()), str(px.index.max().date())],
                 "z_method": "universe-demean (★sector-neutral 비적용 = 단일 archetype compounder basket, peer 구조 없음. us_cyclical multi-sector 대조, 15axis G-A.5).",
                 "sleeve_type": "exposure_timing_overlay",   # ★B″ STEP 0(⑧): verdict 생성 sleeve 아님 = exposure/timing overlay
                 "eff_cross_section_n": eff_cross_n,          # ★유효 cross-section n (valuation 가용 ~7) = cross-sectional factor void
                 "note": "★B″ STEP 0 재분류: us_mega_tech = ★verdict 없는 exposure/timing overlay. cross-sectional factor(family_1)=DIAGNOSTIC ONLY(유효 n≈7 = 통계적 void, 강제 시 spurious factor). 보고 3종 = (1)factor exposure 한계기여(real_rate basket β) (2)concentration/crowding(reflexivity) (3)regime-conditional beta 안정성(family_2b). F-score/net-issuance 측정 폐기(설계 mismatch). EDGAR PIT(filed). survivorship-biased(현 holdings)."},
        "survivor_bias": survivor,
        "family_1_cross_sectional": {"role": "diagnostic_no_verdict", "eff_cross_section_n": eff_cross_n, "indicators": indicators,
                                     "note": "★B″ STEP 0: cross-sectional rank-IC = ★DIAGNOSTIC ONLY(참고 지표). 유효 n≈7 = factor 추정 통계적 void → ★verdict/PASS/FAIL 생성 안 함. vol_60 등 양수 IC = 참고치(spurious factor 제조 회피)."},
        "family_1_BY": {"role": "diagnostic_no_verdict", "by_raw_m": by_raw, "by_M_eff": by_meff, "by_M_eff_nondegenerate": by_meff_nd,
                        "note": "★B″ STEP 0: BY/M_eff = diagnostic 참고치(verdict 근거 아님). n≈7 cross-section = factor void. ★sleeve verdict = exposure overlay(BY survival 로 판정 안 함)."},
        "family_1b_basket_level": {"factor_beta": fam1b_beta, "factor_timing": fam1b_timing,
                                   "real_rate_robustness": fam1b_robust, "capex_ai_regime": capex_regime,
                                   "note": "★자문 R2 수정4 = N=11 small-basket → basket-level time-series factor timing 우선. real_rate(duration)/vix(risk-on)/dollar/rate. multivariate + 단독 + forward timing + ★real_rate robustness(sub-basket/leave-year/level-vs-Δ)."},
        "family_2_regime_conditional": fam2,
        "family_2b_regime_interaction": {"results": fam2b, "note": "★G-A.5 = family_1 미생존 신호 IC~VIX_chg interaction term(살리기). β≠0=regime 따라 IC 변동."},
        "directional_spillover_candidate": spillover,
        "reflexivity_monitor": reflex,
        "net_cost": {"roundtrip_bps": round((COMMISSION + SPREAD_HALF) * 2 * 1e4, 1),
                     "monthly_cost_bps": round((COMMISSION + SPREAD_HALF) * 1e4, 1),
                     "note": "US mega-cap 최고유동성, STT 없음."},
    }
    (ROOT / "validation-metrics-v3.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    # ── print 요약 ──
    print("\n" + "=" * 104)
    print("★family_1 cross-sectional (small-basket hedge):")
    print(f"{'signal__h':<22}{'IC':>9}{'t_NW':>7}{'n_mo':>6}{'p_NW':>8}{'cpcv':>6}{'within':>7}{'avgN':>6}{'crEffN':>7}{'tsEffN':>7}{'bIR':>7}")
    for k, v in sorted(indicators.items(), key=lambda x: x[1]["p_value_nw"] if x[1]["p_value_nw"] else 1):
        print(f"{k:<22}{(v['ic_mean'] or 0):>+9.3f}{(v['t_nw'] or 0):>7.2f}{v['n_months']:>6}"
              f"{(v['p_value_nw'] or 0):>8.3f}{(v['cpcv'].get('oos_hit') or 0):>6.2f}"
              f"{(v['within_period'] or 0):>7.2f}{(v['avg_universe_n'] or 0):>6.1f}"
              f"{(v['cross_eff_n'] or 0):>7.2f}{v['ts_eff_n']:>7.1f}{v['breadth_ir']:>7.2f}")
    print(f"\n★family_1 BY: raw m={by_raw['m_raw']} | M_eff={by_meff['m_eff']} (raw_p_min={by_meff['raw_p_min']} [{by_meff['raw_p_min_key']}])")
    print(f"   threshold(rank1) raw={by_raw['rank1_threshold']} / M_eff={by_meff['rank1_threshold']}")
    print(f"   survivors_BY (M_eff)={by_meff['survivors_BY']}")
    print(f"   nondegenerate(24M strip): M_eff={by_meff_nd['m_eff']} raw_p_min={by_meff_nd['raw_p_min']} surv={by_meff_nd['survivors_BY']}")

    print("\n★family_1b basket-level factor β (★real_rate=duration 최우선):")
    print("  단독:")
    for f, v in fam1b_beta.items():
        if f == "_multivariate" or "beta" not in v:
            continue
        print(f"   {f:16} β={v['beta']:+.4f} t={v['t']:+.2f} n={v['n']} R2={v['r2']} CI={v['ci95']}")
    if "_multivariate" in fam1b_beta:
        mv = fam1b_beta["_multivariate"]; meta = mv.get("_meta", {})
        print(f"  ★multivariate (n={meta.get('n')} R2={meta.get('r2')}):")
        for c, v in mv.items():
            if c == "_meta": continue
            print(f"   {c:16} β={v['beta']:+.4f} t={v['t']:+.2f} CI={v['ci95']}")

    print("\n★family_1b basket-level factor→forward timing (시계열 IC):")
    for k, v in fam1b_timing.items():
        if "ts_ic" in v:
            print(f"   {k:16} ts_IC={v['ts_ic']:+.4f} p={v['p_value']:.3f} n={v['n']}")

    print("\n★real_rate β robustness (코멘트1 최우선):")
    rr = fam1b_robust
    for sub in ["mag7", "ai_semi"]:
        d = rr.get(f"real_rate_{sub}")
        if d: print(f"   sub-basket {sub:8} β={d['beta']:+.4f} t={d['t']:+.2f} n={d['n']}")
    lv = rr.get("real_rate_level_beta"); dd = rr.get("real_rate_diff_beta")
    if lv: print(f"   level β={lv['beta']:+.4f} t={lv['t']:+.2f} | Δ β={dd['beta']:+.4f} t={dd['t']:+.2f}")
    ly = rr.get("real_rate_leave_year", {})
    print(f"   leave-year all_negative={ly.get('all_negative')} range={ly.get('range')}")
    if capex_regime:
        print(f"\n★capex AI-regime (코멘트3): pre-AI IC={capex_regime['pre_ai_ic']}(n{capex_regime['n_pre']}) post-AI IC={capex_regime['post_ai_ic']}(n{capex_regime['n_post']})")

    print("\n★family_2 regime (VIX high vs low, 12M):")
    if "results" in fam2:
        for s, d in fam2["results"].items():
            print(f"   {s:14} hi={d['ic_high_vix']:+.3f}(n{d['n_high']}) lo={d['ic_low_vix']:+.3f}(n{d['n_low']}) diff={d['diff']:+.3f}")

    print("\n★family_2b regime interaction (G-A.5, IC~VIX_chg) — ★B″ size-valid 재검정:")
    for s, d in fam2b.items():
        if "interaction_beta" in d:
            sv = d.get("verdict_size_valid", "n/a")
            fb = d.get("fixed_b_cv"); pw = d.get("p_wild_cluster"); en = d.get("effective_n")
            print(f"   {s:16} β={d['interaction_beta']:+.4f} t_HAC={d['t_hac']:+.2f} n={d['n']} lag={d.get('hac_lag')} "
                  f"effN={en} | fixed-b CV={fb} p_wild={pw} → ★{sv}")

    print("\n★directional spillover (★B″ STEP 5: Cohen-Frazzini lagged firm-pair + MDE):")
    for k, v in spillover.items():
        if isinstance(v, dict) and "corr" in v:
            extra = ""
            if "mde_rho" in v and v.get("mde_rho") is not None:
                extra = f" MDE|ρ|={v['mde_rho']} power={v.get('achieved_power')} {'★UNDERPOWERED' if v.get('underpowered') else ''}"
            print(f"   {k:22} corr={v['corr']:+.4f} p={v['p']:.3f} n={v['n']}{extra}")
    ms = spillover.get("mde_summary", {})
    if ms.get("mde_rho"): print(f"   [MDE summary] n={ms['n']} power=0.80 검출가능 최소|ρ|={ms['mde_rho']}")

    print(f"\n★reflexivity (H9 risk overlay): intra-corr recent={reflex['avg_intra_corr_recent']} p75={reflex['intra_corr_p75']} breadth={reflex['breadth_spread_recent']} status={reflex['current_status']}")
    print(f"\n★★sleeve_type = {results['meta']['sleeve_type']} (verdict 없는 exposure/timing overlay, family_1=diagnostic n≈{eff_cross_n})")


if __name__ == "__main__":
    main()
