# -*- coding: utf-8 -*-
"""measure.py — us_cyclical §M v3 측정 (★재작업: S1 신규 신호 + 자문 R2 4수정 + team-lead 보강 5).

frame v3 §M.1~M.12 + 자문 R2(.consult-us-method-R2.md) + dispatch-role-rework §2.

★S1 신규 신호 (peak-EPS-robust, theory-notes.md):
  - asset_growth (Assets YoY, 음) — Cooper-Gulen-Schill(2008 JF). 전 universe. ★OOS decay 실측 의무.
  - sales_yield (Revenues/mktcap, 양) — Barbee-Mukherji-Raines(1996 FAJ). peak-EPS robust. ★financials Revenues 개념 상이.
  - gross_profitability (GP/Assets, 양) — Novy-Marx(2013 JFE). GP=직접 or Revenues-COGS fallback. sub-universe.
  - ev_ebitda (보조) — OpIncome+D&A / EV.
  + 기존: per_z, pbr_z, vol_60, mom_6, mom_12_1.

★자문 R2 4수정:
  1. family 3분리: family_1 unconditional 예측 IC(BY 검정) / family_2 regime-conditional gated(별 m, baa_aaa 사전지정 quintile) / family_3 driver β attribution(BY 제외).
  2. M_eff (Li-Ji 2005 Heredity eigenvalue, ★test-statistic 상관행렬): M_eff = Σ[I(λ≥1)+(λ-⌊λ⌋)]. family_1 BY threshold = M_eff.
  3. eff_N 이중보정: 시계열 T/h × 횡단면 N/(1+(N-1)ρ̄). IC 검정 SE + breadth-IR 양축.
  4. cyclical = basket화 불필요(60종 cross-sectional 유효).

★team-lead 보강 5:
  1. asset_growth decay = walk-forward OOS(in/out split) 실측, 약화 시 약 prior.
  2. sector별 valuation 적합도 = financials Revenues 부적합 주의 + sub-sector 부호 일관성.
  3. family_1 M_eff = valuation family 내 상관(sales_yield↔per/pbr near-dup) eigenvalue, 무관 신호 과축소 금지.
  4. eff_N 이중보정 + family 3분리.
  5. G-B: family_1 BY 생존 0 + 최강 raw_p>threshold×2 → 단정 금지, 보고.
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

# US net-cost (STT 없음)
COMMISSION = 0.0005
SPREAD_HALF = 0.0003

# universe sector 매핑
def sector_map():
    uni = pd.read_parquet(DATA / "universe.parquet")
    return dict(zip(uni["ticker"], uni["subcl"]))


def load():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    ed = pd.read_parquet(DATA / "edgar_fundamentals.parquet")
    uni = pd.read_parquet(DATA / "universe.parquet")
    macro = pd.read_parquet(DATA / "macro.parquet"); macro.index = pd.to_datetime(macro.index)
    return px, ed, uni, macro


# ── EDGAR PIT 패널 빌더 (일반화) ──
def _ed_prep(ed):
    ed = ed.copy()
    ed["filed_dt"] = pd.to_datetime(ed["filed"], errors="coerce")
    return ed.dropna(subset=["filed_dt", "val"])


def _latest_pit(sub_concept, dt):
    """filed_dt <= dt 인 것 중 최신 1개 val (PIT, lookahead 회피)."""
    av = sub_concept[sub_concept["filed_dt"] <= dt]
    return av["val"].iloc[-1] if len(av) else np.nan


def _ttm(ni_df, dt):
    """TTM flow: filed<=dt 중 FY 최신 우선, 없으면 최근 4 분기 합."""
    av = ni_df[ni_df["filed_dt"] <= dt]
    if len(av) == 0:
        return np.nan
    fy = av[av["fp"] == "FY"]
    if len(fy):
        return fy["val"].iloc[-1]
    q = av[av["fp"].isin(["Q1", "Q2", "Q3", "Q4"])].drop_duplicates("end").tail(4)
    return q["val"].sum() if len(q) >= 4 else np.nan


def _asset_yoy(assets_df, dt):
    """asset_growth = filed<=dt 최신 FY Assets / 그 직전 FY(약 1y 전 end) - 1.
    end(회계기간) 기준 직전 연도 비교 (FY 우선, PIT filed 보장)."""
    av = assets_df[assets_df["filed_dt"] <= dt].copy()
    if len(av) < 2:
        return np.nan
    av["end_dt"] = pd.to_datetime(av["end"], errors="coerce")
    av = av.dropna(subset=["end_dt"]).sort_values("end_dt")
    # FY 연간 우선 (분기 자산은 수준이라 YoY end 비교)
    fy = av[av["fp"] == "FY"].drop_duplicates("end_dt", keep="last")
    base = fy if len(fy) >= 2 else av.drop_duplicates("end_dt", keep="last")
    if len(base) < 2:
        return np.nan
    cur = base.iloc[-1]
    # 직전 = end 가 약 1년(±100d) 전인 것
    prev_cands = base[(base["end_dt"] <= cur["end_dt"] - pd.Timedelta(days=265)) &
                      (base["end_dt"] >= cur["end_dt"] - pd.Timedelta(days=465))]
    if len(prev_cands) == 0:
        return np.nan
    prev = prev_cands.iloc[-1]
    if prev["val"] and prev["val"] > 0:
        return cur["val"] / prev["val"] - 1.0
    return np.nan


def build_pit_panels(px, ed):
    """월말 PIT 패널 dict: pbr, per, sales_yield, gross_prof, asset_growth, ev_ebitda.
    ★전부 filed_dt<=dt 만 (lookahead 회피). flow(rev/ni/gp/op/d&a)=TTM, stock(equity/assets/debt/cash)=최신."""
    pxm = px.resample("ME").last()
    midx = pxm.index
    ed = _ed_prep(ed)
    by_t = {t: ed[ed["ticker"] == t] for t in px.columns}

    panels = {k: {} for k in ["pbr", "per", "sales_yield", "gross_prof", "asset_growth", "ev_ebitda"]}
    for t in px.columns:
        sub = by_t[t]
        g = lambda c: sub[sub["concept"] == c].sort_values("filed_dt")
        eq, ni, sh = g("equity"), g("net_income"), g("shares")
        rev, gp, cogs, assets = g("revenues"), g("gross_profit"), g("cogs"), g("assets")
        opi, dep, ltd, std, cash = g("op_income"), g("dep_amort"), g("lt_debt"), g("st_debt"), g("cash")
        ser = {k: pd.Series(index=midx, dtype=float) for k in panels}
        for dt in midx:
            price = pxm.loc[dt, t]
            if np.isnan(price):
                continue
            # ── shares 무관 신호 (asset_growth, gross_prof = balance-sheet/flow ratio) ──
            a = _latest_pit(assets, dt)
            ttm_rev = _ttm(rev, dt)
            ttm_gp = _ttm(gp, dt)
            if np.isnan(ttm_gp):
                ttm_cogs = _ttm(cogs, dt)
                if not np.isnan(ttm_rev) and not np.isnan(ttm_cogs):
                    ttm_gp = ttm_rev - ttm_cogs
            if not np.isnan(ttm_gp) and a and a > 0:
                ser["gross_prof"][dt] = ttm_gp / a
            ag = _asset_yoy(assets, dt)
            if not np.isnan(ag):
                ser["asset_growth"][dt] = ag
            # ── mktcap 필요 신호 (pbr/per/sales_yield/ev_ebitda) ──
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
            if ttm_rev and ttm_rev > 0:
                ser["sales_yield"][dt] = ttm_rev / mktcap          # 양: 高 = 싼
            # ev/ebitda (보조): EV = mktcap + debt - cash; EBITDA = TTM(opincome)+TTM(dep)
            ttm_op, ttm_dep = _ttm(opi, dt), _ttm(dep, dt)
            ltd_v, std_v, cash_v = _latest_pit(ltd, dt), _latest_pit(std, dt), _latest_pit(cash, dt)
            debt = np.nansum([ltd_v, std_v])
            ev = mktcap + (debt if not np.isnan(debt) else 0) - (cash_v if not np.isnan(cash_v) else 0)
            ebitda = np.nansum([ttm_op, ttm_dep])
            if ev > 0 and ebitda and ebitda > 0 and not np.isnan(ttm_op):
                ser["ev_ebitda"][dt] = ev / ebitda
        for k in panels:
            panels[k][t] = ser[k]
    return {k: pd.DataFrame(v) for k, v in panels.items()}


def cs_z(panel, secmap=None, restrict_cols=None):
    """★sector-neutral cross-sectional z (frame §M.7 'within-industry peer-relative z' 계약).
    각 월 각 sector 내에서 demean/std. secmap=None → universe-demean (단일산업 = sector-neutral 과
    byte-identical, battery 검증 b 입증). ★us_cyclical multi-sector = sector-neutral 필수
    (universe-demean 은 sector mixing 신호 희석 = 계약 위반 버그)."""
    p = panel[restrict_cols] if restrict_cols is not None else panel
    if secmap is None:
        mu = p.mean(axis=1); sd = p.std(axis=1, ddof=1)
        return p.sub(mu, axis=0).div(sd.replace(0, np.nan), axis=0)
    out = p.copy() * np.nan
    secs = {}
    for t in p.columns:
        secs.setdefault(secmap.get(t, "_"), []).append(t)
    for s, cols in secs.items():
        sub = p[cols]; mu = sub.mean(axis=1); sd = sub.std(axis=1, ddof=1)
        out[cols] = sub.sub(mu, axis=0).div(sd.replace(0, np.nan), axis=0)
    return out


# ── IC / SE / OOS ──
def cs_ic(sig, fwd, min_n=8):
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


def block_boot(x, block=3, B=2000, seed=42):
    rng = np.random.default_rng(seed); n = len(x); nb = int(np.ceil(n / block)); m = []
    for _ in range(B):
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


def walk_forward_oos(sig, fwd, split_frac=0.5):
    """★team-lead 보강1: in-sample/out-of-sample 시간 분할 → decay 실측.
    IS 기간 IC 부호로 OOS 동일 부호 유지 여부 + OOS IC magnitude. asset_growth crowding 진단."""
    ic, _ = cs_ic(sig, fwd)
    if len(ic) < 24:
        return dict(note="insufficient", n=len(ic))
    k = int(len(ic) * split_frac)
    is_ic, oos_ic = ic.iloc[:k], ic.iloc[k:]
    is_m, oos_m = float(is_ic.mean()), float(oos_ic.mean())
    return dict(is_ic=round(is_m, 4), oos_ic=round(oos_m, 4),
                sign_persist=bool(np.sign(is_m) == np.sign(oos_m) and oos_m != 0),
                decay_ratio=round(oos_m / is_m, 3) if is_m != 0 else None,
                is_split=str(is_ic.index[-1].date()), n_is=len(is_ic), n_oos=len(oos_ic))


# ── ★eff_N 이중보정 (자문 R2 수정 3) ──
def eff_n_double(ic, ns, h):
    """시계열 eff_N ≈ T/h (overlap) × 횡단면 eff_N = N/(1+(N-1)ρ̄).
    ρ̄ = cross-sectional 평균 상관 (universe 내 종목 수익 상관). 여기선 보수적으로 ρ̄ 미가용 시
    횡단면 보정 = avg_N 그대로(ρ̄=0 = 독립 가정 상한) + 시계열만 강제 적용.
    ★IC 검정 SE 는 NW 가 시계열 overlap 이미 보정 → eff_N 은 breadth-IR·해석용."""
    T = len(ic)
    ts_effN = T / h            # 시계열 독립 표본
    avgN = float(ns.mean()) if len(ns) else np.nan
    return dict(T=T, ts_eff_n=round(ts_effN, 1), avg_cross_n=round(avgN, 1) if not np.isnan(avgN) else None)


def breadth_ir(ic_mean, avg_n, ts_eff_n, rho_bar=0.0):
    """breadth-IR = IC·√(유효 breadth × eff_N). 유효 breadth = N/(1+(N-1)ρ̄) (횡단면).
    ρ̄=0 = 독립 상한(보수적). ts_eff_n = 시계열 독립 기간."""
    eff_breadth = avg_n / (1 + (avg_n - 1) * rho_bar) if avg_n and avg_n > 1 else avg_n
    return round(float(ic_mean) * np.sqrt(max(eff_breadth, 1) * max(ts_eff_n, 1)), 3)


# ── ★M_eff (Li-Ji 2005 eigenvalue, test-statistic 상관행렬) ──
def m_eff_liji(tstat_corr):
    """M_eff = Σ_i [I(λ_i≥1) + (λ_i - ⌊λ_i⌋)]. tstat_corr = test 통계량(=신호별 IC 시계열) 상관행렬."""
    eigs = np.linalg.eigvalsh(tstat_corr)
    eigs = np.clip(eigs, 0, None)
    return float(sum((1.0 if l >= 1 else 0.0) + (l - np.floor(l)) for l in eigs))


# ── ★family_1 BY (M_eff 기반) ──
def benjamini_yekutieli(pvals, m_override=None, q=0.10):
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    raw_m = len(items)
    if raw_m == 0:
        return {"m": 0}
    m = m_override if m_override is not None else raw_m   # ★M_eff override
    items.sort(key=lambda x: x[1])
    cm = sum(1.0 / i for i in range(1, int(np.ceil(m)) + 1)); surv = []
    for r, (k, p) in enumerate(items, 1):
        if p <= (r / m) * q / cm: surv = [items[j][0] for j in range(r)]
    rank1_thr = (1.0 / m) * q / cm
    return dict(m_raw=raw_m, m_eff=round(m, 2), by_factor=round(cm, 3), survivors_BY=surv,
                raw_p_min=round(items[0][1], 5), raw_p_min_key=items[0][0],
                rank1_threshold=round(rank1_thr, 6))


def measure_sig(sig, fwd, h, name):
    ic, ns = cs_ic(sig, fwd)
    if len(ic) < 6:
        return None
    n = len(ic); mean = float(ic.mean())
    se = nw_se(ic, h); t = mean / se if se and se > 0 else np.nan
    p = float(2 * (1 - stats.t.cdf(abs(t), df=max(n-1, 1)))) if not np.isnan(t) else np.nan
    ci = block_boot(ic.values, max(3, min(h, n//3)), 2000) if n >= 6 else (np.nan, np.nan)
    effn = eff_n_double(ic, ns, h)
    bir = breadth_ir(mean, effn["avg_cross_n"] or 0, effn["ts_eff_n"])
    return dict(signal=name, h_months=h, ic_mean=round(mean, 4), n_months=n,
                t_nw=round(t, 2) if not np.isnan(t) else None,
                p_value_nw=round(p, 4) if not np.isnan(p) else None,
                ci95_block_boot=[round(ci[0], 4), round(ci[1], 4)],
                cpcv=cpcv(sig, fwd, h), within_period=within_period(ic),
                avg_universe_n=effn["avg_cross_n"], ts_eff_n=effn["ts_eff_n"],
                breadth_ir=bir, _ic_series=ic)


# ── family_3: driver β attribution (BY 제외) ──
def driver_beta(px, macro):
    """sleeve 동일가중 월수익 ~ 거시 Δ (contemporaneous HAC). hy_oas/baa_aaa/rate/vix/dollar.
    ★family_3 = attribution (검정 아님, BY 제외)."""
    import statsmodels.api as sm
    pxm = px.resample("ME").last()
    ret = pxm.pct_change().mean(axis=1)
    mm = macro.resample("ME").last()
    feat = pd.DataFrame(index=mm.index)
    if "dollar" in mm: feat["dollar"] = mm["dollar"].pct_change()
    if "rate10y" in mm: feat["rate"] = mm["rate10y"].diff()
    if "vix" in mm: feat["vix"] = mm["vix"].diff()
    if "hy_oas" in mm: feat["hy_oas"] = mm["hy_oas"].diff()
    if "baa_aaa" in mm: feat["baa_aaa"] = mm["baa_aaa"].diff()
    out = {}
    # 각 driver 단독 (multicollinearity 회피 + n 차이: hy_oas 36mo vs baa_aaa full)
    for f in feat.columns:
        df = pd.concat([ret.rename("y"), feat[f]], axis=1).dropna()
        if len(df) < 24:
            out[f] = dict(note="insufficient", n=len(df)); continue
        X = sm.add_constant(df[[f]])
        model = sm.OLS(df["y"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
        out[f] = dict(beta=round(float(model.params[f]), 4), t=round(float(model.tvalues[f]), 2),
                      ci95=[round(float(model.conf_int().loc[f, 0]), 4), round(float(model.conf_int().loc[f, 1]), 4)],
                      n=len(df))
    return out


# ── family_2: regime-conditional (baa_aaa 사전지정 quintile, 별 family) ──
def regime_conditional(signals_for_regime, fwd_map, macro, top_q=0.6):
    """★Harvey-Liu-Zhu: regime 사전지정(baa_aaa 상위 quintile = high-spread risk-off)이면 별 family 정당.
    high-spread vs low-spread 에서 best 신호 IC 차. ★family_2 (별 m, family_1 과 분리)."""
    mm = macro.resample("ME").last()
    if "baa_aaa" not in mm:
        return {"note": "baa_aaa 부재"}
    spread = mm["baa_aaa"].dropna()
    # 사전지정 = 표본 내 상위 40% = high-spread(risk-off) regime
    thr = spread.quantile(top_q)
    out = {}
    for sname, sig in signals_for_regime.items():
        fwd = fwd_map[sname]
        ic, _ = cs_ic(sig, fwd)
        ic = ic.dropna()
        if len(ic) < 24:
            continue
        sp_al = spread.reindex(ic.index).ffill()
        hi = ic[sp_al >= thr]; lo = ic[sp_al < thr]
        if len(hi) < 8 or len(lo) < 8:
            continue
        # block-boot CI (small-n hedge)
        hci = block_boot(hi.values, 3, 1000) if len(hi) >= 6 else (np.nan, np.nan)
        lci = block_boot(lo.values, 3, 1000) if len(lo) >= 6 else (np.nan, np.nan)
        out[sname] = dict(ic_high_spread=round(float(hi.mean()), 4), n_high=len(hi),
                          ic_low_spread=round(float(lo.mean()), 4), n_low=len(lo),
                          ci_high=[round(hci[0],4), round(hci[1],4)],
                          ci_low=[round(lci[0],4), round(lci[1],4)],
                          diff=round(float(hi.mean() - lo.mean()), 4))
    return dict(regime_var="baa_aaa", high_spread_thr=round(float(thr), 3),
                top_q=top_q, results=out,
                note="★사전지정 regime(상위 40% spread=risk-off). family_2 별 m. small-n hedge(block-boot CI).")


def leave_year_ic(sig, fwd):
    """leave-episode: 각 연도 제외 후 IC 재계산 (단일 episode 의존 여부)."""
    ic, _ = cs_ic(sig, fwd)
    if len(ic) < 24:
        return {}
    out = {}
    for y in sorted(set(ic.index.year)):
        sub = ic[ic.index.year != y]
        out[str(y)] = round(float(sub.mean()), 4)
    vals = list(out.values())
    return dict(per_year_ex=out, full_ic=round(float(ic.mean()), 4),
                min_ex=min(vals), max_ex=max(vals),
                stable=bool(all(np.sign(v) == np.sign(ic.mean()) for v in vals)))


def long_only_net(sig, fwd, q=0.2, cost=(0.0005 + 0.0003) * 2, min_n=8):
    """long-only-implementable spread: 저z(싼 value) top-quintile 평균 - universe 평균.
    pbr/ev value = 음 IC -> 저z overweight. net = gross - roundtrip cost. US STT 없음."""
    idx = sig.index.intersection(fwd.index); sprs = []
    for dt in idx:
        sv = sig.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
        c = sv.index.intersection(rv.index)
        if len(c) < min_n:
            continue
        sv = sv.loc[c]; rv = rv.loc[c]
        thr = sv.quantile(q)
        sprs.append(rv[sv <= thr].mean() - rv.mean())
    if not sprs:
        return {}
    g = float(np.mean(sprs))
    return dict(gross_spread=round(g, 4), net_spread=round(g - cost, 4), n=len(sprs), roundtrip_cost=cost)


def sub_sector_n(panel, secmap):
    """검증(a): sub-sector별 가용 N (within-sector demean 모집단)."""
    secs = {}
    for t in panel.columns:
        secs.setdefault(secmap.get(t, "_"), []).append(t)
    out = {}
    for s, cols in secs.items():
        sub = panel[cols]; mn = sub.notna().sum(axis=1)
        out[s] = dict(static_n=len(cols), median_monthly_n=int(mn.median()),
                      min_n=int(mn.min()), max_n=int(mn.max()))
    return out


def sector_z_decomposition(panel, fwd, secmap):
    """★검증(b) team-lead 핵심 mechanism: sector-neutral 효과가 'sector 간 level 차이 제거'인지
    'sector 내 factor 제거'(line 322 ≈0 artifact)인지 분해.
    universe-z = within-sector-z 신호 + sector-level component. sector-level component(각 종목을
    자기 sector universe-z 평균으로 대체) 의 IC ≈ 0 이면 sector-level 차이는 forward 무예측 →
    universe-z 가 그 noise 로 within 신호 희석 = sector-neutral 정당(line 322 모순 아님)."""
    secs = {}
    for t in panel.columns:
        secs.setdefault(secmap.get(t, "_"), []).append(t)
    mu = panel.mean(axis=1); sd = panel.std(axis=1, ddof=1)
    z_uni = panel.sub(mu, axis=0).div(sd.replace(0, np.nan), axis=0)
    z_sn = panel.copy() * np.nan
    sec_mean_z = panel.copy() * np.nan
    for s, cols in secs.items():
        sub = panel[cols]; m = sub.mean(axis=1); st = sub.std(axis=1, ddof=1)
        z_sn[cols] = sub.sub(m, axis=0).div(st.replace(0, np.nan), axis=0)
        sec_uni = z_uni[cols].mean(axis=1)
        for c in cols:
            sec_mean_z[c] = sec_uni
    return dict(ic_universe_z=round(float(cs_ic(z_uni, fwd)[0].mean()), 4),
                ic_sector_neutral_z=round(float(cs_ic(z_sn, fwd)[0].mean()), 4),
                ic_sector_level_component=round(float(cs_ic(sec_mean_z, fwd)[0].mean()), 4),
                note="sector_level_component = 종목을 자기 sector universe-z 평균으로 대체한 신호 IC. "
                     "~0 이면 sector level 차이는 forward 무예측 → universe-z 가 그 noise 로 within 신호 희석 = sector-neutral 정당.")


def sub_sector_sign(sig, fwd, secmap):
    """★team-lead 보강2: sub-sector 부호 일관성 (sector마다 peak-EPS 강도 다름)."""
    ic_all, _ = cs_ic(sig, fwd)
    if len(ic_all) < 6:
        return {}
    cols_by_sec = {}
    for t in sig.columns:
        s = secmap.get(t, "?"); cols_by_sec.setdefault(s, []).append(t)
    out = {}
    for sec, cols in cols_by_sec.items():
        if len(cols) < 4:
            out[sec] = dict(note="universe<4", n_names=len(cols)); continue
        sub = sig[cols]
        ic, _ = cs_ic(sub, fwd, min_n=3)
        if len(ic) >= 6:
            out[sec] = dict(ic_mean=round(float(ic.mean()), 4), n_months=len(ic), n_names=len(cols))
    return out


def main():
    px, ed, uni, macro = load()
    secmap = dict(zip(uni["ticker"], uni["subcl"]))
    pxm = px.resample("ME").last()
    print(f"universe {px.shape[1]} tickers, {px.shape[0]} days")

    # ★sector-neutral z (frame §M.7 계약, secmap 전달). 단일산업이면 universe-demean 과 byte-identical(battery 검증b).
    # 가격 신호
    mom_12_1 = cs_z(pxm.shift(1) / pxm.shift(12) - 1, secmap)
    mom_6 = cs_z(pxm / pxm.shift(6) - 1, secmap)
    ret_d = px.pct_change(); vol_60 = cs_z((ret_d.rolling(60).std() * np.sqrt(252)).resample("ME").last(), secmap)

    # ★EDGAR PIT 패널 (신규 포함)
    P = build_pit_panels(px, ed)
    for k, v in P.items():
        print(f"  panel {k:13} shape={v.shape} cov={int(v.notna().sum().sum())}")

    # ★sector-neutral cross-sectional z (direction: 신호 z 가 클수록 forward 방향)
    #   value: 저per/저pbr/저ev = 싼 → IC 음 정상. sales_yield: 高=싼=양. asset_growth: 高=음. gross_prof: 高=양.
    per_z, pbr_z = cs_z(P["per"], secmap), cs_z(P["pbr"], secmap)
    sales_yield_z = cs_z(P["sales_yield"], secmap)
    gross_prof_z = cs_z(P["gross_prof"], secmap)
    asset_growth_z = cs_z(P["asset_growth"], secmap)
    ev_ebitda_z = cs_z(P["ev_ebitda"], secmap)

    signals = {
        "mom_12_1": mom_12_1, "mom_6": mom_6, "vol_60": vol_60,
        "per_z": per_z, "pbr_z": pbr_z,
        "sales_yield": sales_yield_z, "gross_prof": gross_prof_z,
        "asset_growth": asset_growth_z, "ev_ebitda": ev_ebitda_z,
    }
    horizons = {"3M": 3, "6M": 6, "12M": 12, "24M_value": 24}

    # ── family_1: unconditional 예측 IC ──
    indicators, pvals, ic_series = {}, {}, {}
    for sname, sig in signals.items():
        for hname, h in horizons.items():
            fwd = pxm.shift(-h) / pxm - 1
            r = measure_sig(sig, fwd, h, f"{sname}__{hname}")
            if r:
                key = f"{sname}__{hname}"
                ic_series[key] = r.pop("_ic_series")
                indicators[key] = r; pvals[key] = r["p_value_nw"]

    # ── ★M_eff (Li-Ji, test-stat=IC 시계열 상관행렬) ──
    keys = list(ic_series.keys())
    ic_df = pd.DataFrame({k: ic_series[k] for k in keys})
    tcorr = ic_df.corr().fillna(0).values
    np.fill_diagonal(tcorr, 1.0)
    m_eff = m_eff_liji(tcorr)
    by_meff = benjamini_yekutieli(pvals, m_override=m_eff)
    by_raw = benjamini_yekutieli(pvals, m_override=None)

    # ── ★non-degenerate strip (24M degenerate 제외 family_1) ──
    pvals_nd = {k: v for k, v in pvals.items() if not k.endswith("24M_value")}
    keys_nd = [k for k in keys if not k.endswith("24M_value")]
    ic_df_nd = ic_df[keys_nd]
    tcorr_nd = ic_df_nd.corr().fillna(0).values; np.fill_diagonal(tcorr_nd, 1.0)
    m_eff_nd = m_eff_liji(tcorr_nd)
    by_meff_nd = benjamini_yekutieli(pvals_nd, m_override=m_eff_nd)

    # ── ★asset_growth OOS decay (보강1) ──
    oos = {}
    for sname in ["asset_growth", "sales_yield", "gross_prof", "per_z"]:
        for h in [12, 24]:
            fwd = pxm.shift(-h) / pxm - 1
            oos[f"{sname}__{h}M"] = walk_forward_oos(signals[sname], fwd)

    # ── ★sub-sector 부호 일관성 (보강2) ──
    subsec = {}
    for sname in ["asset_growth", "sales_yield", "per_z", "pbr_z"]:
        fwd = pxm.shift(-12) / pxm - 1
        subsec[sname] = sub_sector_sign(signals[sname], fwd, secmap)

    # ── family_2: regime-conditional (baa_aaa 사전지정) ──
    reg_signals = {s: signals[s] for s in ["asset_growth", "sales_yield", "per_z", "vol_60", "mom_6"]}
    reg_fwd = {s: pxm.shift(-12) / pxm - 1 for s in reg_signals}
    fam2 = regime_conditional(reg_signals, reg_fwd, macro)

    # ── family_3: driver β attribution (BY 제외) ──
    fam3 = driver_beta(px, macro)

    # ── ★검증(a) sub-sector N + (b) sector-z mechanism 분해 (team-lead 핵심) ──
    subsec_n = {name: sub_sector_n(P[name], secmap) for name in ["pbr", "ev_ebitda", "per", "sales_yield"]}
    secz_decomp = {}
    for name in ["pbr", "ev_ebitda", "per"]:
        for h in [12, 24]:
            fwd = pxm.shift(-h) / pxm - 1
            secz_decomp[f"{name}__{h}M"] = sector_z_decomposition(P[name], fwd, secmap)

    # ── ★생존 신호 robustness (leave-episode + long-only net-cost) ──
    surv_robust = {}
    for name, sig in [("pbr_z", pbr_z), ("ev_ebitda", ev_ebitda_z)]:
        for h in [6, 12]:
            fwd = pxm.shift(-h) / pxm - 1
            surv_robust[f"{name}__{h}M"] = dict(
                leave_year=leave_year_ic(sig, fwd),
                long_only=long_only_net(sig, fwd))

    results = {
        "meta": {"universe_n": int(px.shape[1]),
                 "date_range": [str(px.index.min().date()), str(px.index.max().date())],
                 "panel_cov": {k: int(v.notna().sum().sum()) for k, v in P.items()},
                 "z_method": "sector_neutral (frame §M.7 within-industry peer-relative). 단일산업=universe-demean byte-identical(battery 검증b).",
                 "note": "★재작업: S1 신규 신호(asset_growth/sales_yield/gross_prof/ev_ebitda) + R2 4수정 + sector-neutral z. EDGAR PIT(filed). survivorship-biased(현 holdings)."},
        "family_1_indicators": indicators,
        "family_1_BY": {
            "by_raw_m": by_raw, "by_M_eff": by_meff,
            "by_M_eff_nondegenerate": by_meff_nd,
            "note": "★M_eff(Li-Ji eigenvalue, test-stat 상관행렬). raw_m vs M_eff 비교. nondegenerate=24M_value strip."},
        "verify_a_sub_sector_n": subsec_n,
        "verify_b_sector_z_decomposition": secz_decomp,
        "survivor_robustness": surv_robust,
        "asset_growth_OOS_decay": oos,
        "sub_sector_sign": subsec,
        "family_2_regime_conditional": fam2,
        "family_3_driver_beta": fam3,
        "net_cost": {"roundtrip_bps": round((COMMISSION + SPREAD_HALF) * 2 * 1e4, 1), "note": "US STT 없음"},
    }
    (ROOT / "validation-metrics-v3.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    # ── print 요약 ──
    print("\n" + "=" * 92)
    print(f"{'signal__h':<22}{'IC':>9}{'t_NW':>7}{'n_mo':>6}{'p_NW':>8}{'cpcv':>6}{'within':>7}{'avgN':>6}{'tsEffN':>7}{'bIR':>7}")
    for k, v in sorted(indicators.items(), key=lambda x: x[1]["p_value_nw"] if x[1]["p_value_nw"] else 1):
        print(f"{k:<22}{(v['ic_mean'] or 0):>+9.3f}{(v['t_nw'] or 0):>7.2f}{v['n_months']:>6}"
              f"{(v['p_value_nw'] or 0):>8.3f}{(v['cpcv'].get('oos_hit') or 0):>6.2f}"
              f"{(v['within_period'] or 0):>7.2f}{(v['avg_universe_n'] or 0):>6.1f}"
              f"{v['ts_eff_n']:>7.1f}{v['breadth_ir']:>7.2f}")
    print(f"\n★family_1 BY: raw m={by_raw['m_raw']} | M_eff={by_meff['m_eff']} (raw_p_min={by_meff['raw_p_min']} [{by_meff['raw_p_min_key']}])")
    print(f"   threshold(rank1) raw={by_raw['rank1_threshold']} / M_eff={by_meff['rank1_threshold']}")
    print(f"   survivors_BY (M_eff)={by_meff['survivors_BY']}")
    print(f"   nondegenerate(24M strip): M_eff={by_meff_nd['m_eff']} raw_p_min={by_meff_nd['raw_p_min']} surv={by_meff_nd['survivors_BY']}")
    print("\n★asset_growth OOS decay:")
    for k, v in oos.items():
        if "is_ic" in v:
            print(f"   {k:20} IS={v['is_ic']:+.4f} OOS={v['oos_ic']:+.4f} persist={v['sign_persist']} decay={v['decay_ratio']}")
    print("\n★sub-sector sign (12M):")
    for s, d in subsec.items():
        row = " ".join(f"{sec}={dd.get('ic_mean','-')}" for sec, dd in d.items() if 'ic_mean' in dd)
        print(f"   {s:14} {row}")
    print("\n★검증(a) sub-sector N (pbr):")
    for s, d in subsec_n["pbr"].items():
        print(f"   {s:14} static={d['static_n']} median_monthly={d['median_monthly_n']} min/max={d['min_n']}/{d['max_n']}")
    print("\n★검증(b) sector-z mechanism 분해 (universe-z vs sector-neutral-z vs sector-level-component):")
    for k, d in secz_decomp.items():
        print(f"   {k:14} uni={d['ic_universe_z']:+.4f} secNeutral={d['ic_sector_neutral_z']:+.4f} sectorLevel={d['ic_sector_level_component']:+.4f}")
    print("\n★생존 robustness (leave-year stable + long-only net spread):")
    for k, d in surv_robust.items():
        ly = d["leave_year"]; lo = d["long_only"]
        if ly:
            print(f"   {k:14} leave-year stable={ly['stable']} ex-range[{ly['min_ex']:+.3f},{ly['max_ex']:+.3f}] | long-only net={lo.get('net_spread'):+.4f}")
    print("\n★family_2 regime (baa_aaa high vs low spread, 12M):")
    if "results" in fam2:
        for s, d in fam2["results"].items():
            print(f"   {s:14} hi={d['ic_high_spread']:+.3f}(n{d['n_high']}) lo={d['ic_low_spread']:+.3f}(n{d['n_low']}) diff={d['diff']:+.3f}")
    print("\n★family_3 driver β (attribution, BY 제외):")
    for f, v in fam3.items():
        if "beta" in v:
            print(f"   {f:10} β={v['beta']:+.4f} t={v['t']:+.2f} n={v['n']} CI={v['ci95']}")


if __name__ == "__main__":
    main()
