# -*- coding: utf-8 -*-
"""_payout_interaction.py — ★STEP 1~3 (B″ 조정안, lock-blocking 게이트, defensive 최고 stakes).

REWORK-B2-adjustment-plan §STEP 1~3 + .consult-us-rework-3R-results.md (대안 B″).
★현 measure.py `regime_conditional()`(baa_aaa quintile split) = frame line 323 위반 → 신규 interaction 전환.

## STEP 1 (④ payout duration-orthogonalize → credit interaction)
1. payout-premium return R_payout,t = long-short(고payout − 저payout) factor return (월별).
2. ★직교화 선결(FWL, order 명시 = duration 먼저): α_payout,t = R_payout,t − β_dur·ΔReal_rate_t.
3. ★conditioning = continuous interaction(split 아님): payout IC_t ~ ΔReal_rate_t (mega_tech regime_interaction 이식, regime_chg=ΔReal_rate continuous).
   - 직교 전 vs 직교 후 interaction β 비교 = ★duration-in-disguise falsifier(직교 전 유의→후 소멸=spurious).
4. credit-spread(baa_aaa) 적층(직교 후).
5. ★λ = PIT expanding-window Ridge 동결(⑥). full-panel CV ⛔. λ∈{0.1λ*, λ*, 10λ*} 3점 hedge table.
6. ★effective-n = regime block 수(n_eff = n/(1+2Σρ_k)), NW-HAC lag = regime persistence.

## STEP 2 (②⑤⑦)
- ② 단일 FDR family: payout main+interaction+add = 하나의 alpha budget(e-process ledger).
- ⑤ effective-n: n_eff = n/(1+2Σρ_k) (Newey-West variance inflation).
- ⑦ ★per-test null calibration: small-block NW-HAC = size-invalid(Kiefer-Vogelsang fixed-b). asymptotic t →
  fixed-b critical value(Kiefer-Vogelsang 2005 table) + wild-cluster(block) bootstrap 병기.

## STEP 3 (⑥): λ PIT expanding-window 동결 (STEP 1-5 내장).

★verdict 어휘: "조건부 PASS(잠정), OOS 게이트 미충족 시 자동 강등"(armed-pending). ⛔confirmed/회생확실 금지.
★합성 0. EDGAR PIT filed/yfinance/FRED. INV_R15_WEIGHTS off = byte-identical(measure.py 미변경, 별 파일).
"""
from __future__ import annotations
import sys, json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure as M   # ★measure 가 sys.stdout=TextIOWrapper(utf-8) 설정 (재설정 금지)
import _b2_stats as B2   # ★공용 B″ 통계 인프라 (team-lead 지시 = cyclical 재사용)

ROOT = Path(__file__).resolve().parent

# ── ★공용 모듈 별칭 (effective_n/fixed_b_cv/wild_cluster_boot = _b2_stats 재사용) ──
effective_n = B2.effective_n
fixed_b_cv = B2.fixed_b_cv
wild_cluster_boot = B2.wild_cluster_boot
_persistence_block = B2.persistence_block


# ── payout-premium long-short factor return (월별) ──
def payout_premium_return(payout_z, fwd, q=0.2, min_n=12):
    """R_payout,t = 고payout(상위 q) − 저payout(하위 q) 동일가중 forward return. payout factor return 시계열.
    payout 양 가설이면 R>0. (단 us_defensive 실측 = anti-yield = R<0 예상)."""
    idx = payout_z.index.intersection(fwd.index)
    rets, dates = [], []
    for dt in idx:
        sv = payout_z.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
        c = sv.index.intersection(rv.index)
        if len(c) < min_n:
            continue
        sv = sv.loc[c]; rv = rv.loc[c]
        hi = rv[sv >= sv.quantile(1 - q)]; lo = rv[sv <= sv.quantile(q)]
        if len(hi) >= 2 and len(lo) >= 2:
            rets.append(hi.mean() - lo.mean()); dates.append(dt)
    return pd.Series(rets, index=dates)


# ── STEP 1: duration-orthogonalize (FWL, duration 먼저) ──
def orthogonalize_duration(R_payout, d_real_rate):
    """★FWL order = duration 먼저: α_payout,t = R_payout,t − β_dur·ΔReal_rate_t.
    R_payout ~ const + ΔReal_rate OLS → 잔차 = duration-orthogonal payout premium."""
    import statsmodels.api as sm
    df = pd.concat([R_payout.rename("R"), d_real_rate.rename("drr")], axis=1).dropna()
    if len(df) < 24:
        return None, dict(note="insufficient", n=len(df))
    X = sm.add_constant(df[["drr"]])
    m = sm.OLS(df["R"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    alpha = df["R"] - m.fittedvalues  # 잔차 = duration 제거 후 payout-specific
    return alpha, dict(beta_duration=round(float(m.params["drr"]), 4),
                       t_duration=round(float(m.tvalues["drr"]), 2),
                       alpha_mean=round(float(alpha.mean()), 4), n=len(df),
                       order="duration_first (FWL): R_payout ~ ΔReal_rate → 잔차=credit/idio 적층 base",
                       basis="ΔReal_rate (DFII10 first-diff)")


# ── STEP 1-3: continuous interaction (IC_t ~ ΔReal_rate_t), 직교 전후 비교 ──
def payout_interaction(payout_z, fwd, d_real_rate, d_baa_aaa, name="payout"):
    """★mega_tech regime_interaction 이식 (IC_t ~ regime_chg_t HAC), regime_chg=ΔReal_rate continuous.
    직교 전 interaction(payout IC ~ ΔReal_rate) vs 직교 후(잔차 IC ~ ΔReal_rate) = duration-in-disguise falsifier.
    + per-test calibration(fixed-b CV + wild-cluster) + effective-n + credit 적층."""
    import statsmodels.api as sm
    ic, _ = M.cs_ic(payout_z, fwd)
    if len(ic) < 24:
        return dict(name=name, note="insufficient", n=len(ic))

    # ── 직교 전 interaction: payout IC_t ~ ΔReal_rate_t (continuous) ──
    df0 = pd.concat([ic.rename("ic"), d_real_rate.rename("drr")], axis=1).dropna()
    if len(df0) < 24:
        return dict(name=name, note="insufficient_merge", n=len(df0))
    blk = _persistence_block(df0["ic"])
    X0 = sm.add_constant(df0[["drr"]])
    m0 = sm.OLS(df0["ic"], X0).fit(cov_type="HAC", cov_kwds={"maxlags": blk})
    eff0 = effective_n(df0["ic"].values)
    fb0 = fixed_b_cv(eff0["n"], eff0.get("nw_lag", blk))
    wc0 = wild_cluster_boot(df0["ic"], X0, "drr", block=blk)
    pre = dict(interaction_beta=round(float(m0.params["drr"]), 4), t_asymptotic=round(float(m0.tvalues["drr"]), 2),
               main_effect_const=round(float(m0.params["const"]), 4), n=len(df0),
               effective_n=eff0, fixed_b=fb0, wild_cluster=wc0,
               size_valid_sig=bool(abs(float(m0.tvalues["drr"])) > fb0["cv_5pct"]))

    # ── STEP 1-2 직교화: payout IC 를 ΔReal_rate 에 직교(duration 제거) → 잔차 IC ──
    resid_ic = df0["ic"] - m0.fittedvalues  # = ic − (const + β·drr) = duration-orthogonal payout IC
    # 직교 후 잔차가 ΔReal_rate 에 여전히 반응? (정의상 ≈0 = duration-in-disguise 판정 도구)
    Xr = sm.add_constant(df0[["drr"]])
    mr = sm.OLS(resid_ic, Xr).fit(cov_type="HAC", cov_kwds={"maxlags": blk})
    # 직교 후 잔차 IC 자체의 평균 유의성 (payout-specific alpha 존재?)
    eff_r = effective_n(resid_ic.values)
    fb_r = fixed_b_cv(eff_r["n"], eff_r.get("nw_lag", blk))
    resid_mean = float(resid_ic.mean()); resid_se = M.nw_se(resid_ic, blk)
    resid_t = resid_mean / resid_se if resid_se and resid_se > 0 else np.nan
    post = dict(resid_interaction_beta=round(float(mr.params["drr"]), 4), resid_interaction_t=round(float(mr.tvalues["drr"]), 2),
                resid_ic_mean=round(resid_mean, 4), resid_ic_t_asymptotic=round(float(resid_t), 2) if not np.isnan(resid_t) else None,
                effective_n=eff_r, fixed_b=fb_r,
                resid_size_valid_sig=bool(not np.isnan(resid_t) and abs(resid_t) > fb_r["cv_5pct"]))

    # ── duration-in-disguise 판정 ──
    pre_sig = pre["size_valid_sig"]
    post_sig = post["resid_size_valid_sig"]
    if pre_sig and not post_sig:
        disguise = "DURATION_IN_DISGUISE (직교 전 유의 → 후 소멸 = spurious, payout-specific alpha 부재)"
    elif pre_sig and post_sig:
        disguise = "PAYOUT_SPECIFIC (직교 후에도 유의 = duration 재포장 아님)"
    elif not pre_sig:
        disguise = "NO_INTERACTION (직교 전부터 비유의, fixed-b 기준)"
    else:
        disguise = "AMBIGUOUS"

    # ── STEP 1-3 credit 적층 (직교 후 잔차 IC ~ ΔReal_rate + Δbaa_aaa) ──
    credit = None
    if d_baa_aaa is not None:
        dfc = pd.concat([resid_ic.rename("ric"), df0["drr"], d_baa_aaa.rename("dbaa")], axis=1).dropna()
        if len(dfc) >= 24:
            Xc = sm.add_constant(dfc[["drr", "dbaa"]])
            mc = sm.OLS(dfc["ric"], Xc).fit(cov_type="HAC", cov_kwds={"maxlags": blk})
            credit = dict(baa_aaa_beta=round(float(mc.params["dbaa"]), 4), baa_aaa_t=round(float(mc.tvalues["dbaa"]), 2),
                          n=len(dfc), note="직교 후 잔차 IC ~ ΔReal_rate + Δbaa_aaa 적층(credit regime)")

    return dict(name=name, regime_var="ΔReal_rate (DFII10) continuous (★split 아님)",
                hac_lag_persistence=blk,
                pre_orthogonalize=pre, post_orthogonalize=post,
                duration_in_disguise_verdict=disguise, credit_stack=credit,
                note="★mega_tech regime_interaction 이식(IC~regime_chg HAC). regime_chg=ΔReal_rate continuous. "
                     "직교 전후 size-valid(fixed-b) 비교 = duration-in-disguise falsifier.")


# (★_persistence_block = _b2_stats.persistence_block 공용 별칭, 위 import 에서 연결)


# ── STEP 1-5: Ridge λ PIT (★공용 B2.ridge_lambda_pit 위임, payout IC ~ ΔReal_rate interaction) ──
def ridge_lambda_pit(payout_z, fwd, d_real_rate, train_frac=0.6):
    """★λ = expanding-window PIT 동결 + 3점 hedge. payout IC_t ~ ΔReal_rate_t interaction 정칙화.
    공용 _b2_stats.ridge_lambda_pit 위임 + main() print 호환 key(interaction_coef) 매핑."""
    ic, _ = M.cs_ic(payout_z, fwd)
    res = B2.ridge_lambda_pit(ic, d_real_rate, train_frac=train_frac)
    if "hedge_table" in res:  # key 매핑 (공용 coef → interaction_coef)
        for tag, hd in res["hedge_table"].items():
            hd["interaction_coef"] = hd.get("coef")
            hd["coef_sign"] = hd.get("sign")
    return res


def main():
    px, ed, uni, macro = M.load()
    secmap = dict(zip(uni["ticker"], uni["subcl"]))
    pxm = px.resample("ME").last()
    mm = macro.resample("ME").last()
    P = M.build_pit_panels(px, ed)
    payout_z = M.cs_z(P["payout_yield"], secmap)
    div_z = M.cs_z(P["dividend_yield"], secmap)

    d_real_rate = mm["real_rate"].diff() if "real_rate" in mm else None
    d_baa_aaa = mm["baa_aaa"].diff() if "baa_aaa" in mm else None

    out = {"design": "B″ STEP 1~3 (payout duration-orthogonalize → credit interaction). 합성 0, EDGAR PIT.",
           "frame_contract_compliance": {
               "interaction_not_split": "★continuous ΔReal_rate interaction (mega_tech regime_interaction 이식, baa_aaa quintile split 폐기)",
               "orthogonalize_order": "duration 먼저(FWL) → 잔차에 credit 적층",
               "single_fdr_family": "payout main + interaction = 하나의 alpha budget (별 family 금지)",
               "lambda_pit_frozen": "expanding-window train 60% CV → eval 40% 미접촉",
               "effective_n": "n_eff = n/(1+2Σρ_k) (NW VIF)",
               "per_test_calibration": "fixed-b CV (Kiefer-Vogelsang) + wild-cluster(block) bootstrap = size-valid",
               "verdict_lexicon": "armed-pending (조건부 PASS 잠정, OOS 미충족 자동 강등). ⛔confirmed/회생확실"}}

    for name, sig in [("payout_yield", payout_z), ("dividend_yield", div_z)]:
        for h in [12, 6]:
            fwd = pxm.shift(-h) / pxm - 1
            key = f"{name}__{h}M"
            R_payout = payout_premium_return(sig, fwd)
            alpha, orth = orthogonalize_duration(R_payout, d_real_rate) if d_real_rate is not None else (None, {})
            inter = payout_interaction(sig, fwd, d_real_rate, d_baa_aaa, name=key) if d_real_rate is not None else {}
            ridge = ridge_lambda_pit(sig, fwd, d_real_rate) if d_real_rate is not None else {}
            out[key] = dict(payout_premium_return_mean=round(float(R_payout.mean()), 4) if len(R_payout) else None,
                            duration_orthogonalize=orth, interaction=inter, ridge_lambda_pit=ridge)

    (ROOT / "_payout_interaction.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    # ── print 요약 ──
    print("=" * 96)
    print("★STEP 1~3 payout duration-orthogonalize → credit interaction (B″)")
    for name in ["payout_yield__12M", "payout_yield__6M", "dividend_yield__12M"]:
        if name not in out:
            continue
        d = out[name]; it = d.get("interaction", {})
        if "pre_orthogonalize" not in it:
            print(f"\n{name}: {it.get('note','-')}"); continue
        pre = it["pre_orthogonalize"]; post = it["post_orthogonalize"]
        print(f"\n=== {name} (R_payout mean={d['payout_premium_return_mean']}) ===")
        o = d["duration_orthogonalize"]
        print(f"  직교화(FWL duration 먼저): β_dur={o.get('beta_duration')} t={o.get('t_duration')} | α_mean={o.get('alpha_mean')}")
        print(f"  HAC lag(persistence)={it['hac_lag_persistence']} | effective_n: n={pre['effective_n']['n']} n_eff={pre['effective_n']['n_eff']} (VIF {pre['effective_n']['vif']}, ρ1 {pre['effective_n']['rho1']})")
        print(f"  ★직교 전 interaction: β={pre['interaction_beta']} t_asy={pre['t_asymptotic']} | fixed-b CV={pre['fixed_b']['cv_5pct']}(b={pre['fixed_b']['b']}) → size-valid 유의={pre['size_valid_sig']}")
        print(f"     wild-cluster p={pre['wild_cluster'].get('p_wild_cluster')}")
        print(f"  ★직교 후 잔차: interaction β={post['resid_interaction_beta']} t={post['resid_interaction_t']} | 잔차 IC mean={post['resid_ic_mean']} t_asy={post['resid_ic_t_asymptotic']} fixed-b CV={post['fixed_b']['cv_5pct']} → size-valid={post['resid_size_valid_sig']}")
        print(f"  ★판정: {it['duration_in_disguise_verdict']}")
        if it.get("credit_stack"):
            c = it["credit_stack"]; print(f"  credit 적층: Δbaa_aaa β={c['baa_aaa_beta']} t={c['baa_aaa_t']}")
        rl = d["ridge_lambda_pit"]
        if "hedge_table" in rl:
            print(f"  ★Ridge λ PIT: λ*={rl['lambda_star']} (train 60%→{rl['train_split_date']}, eval {rl['eval_start']}~) sign_stable={rl['sign_stable']}")
            for tag, hd in rl["hedge_table"].items():
                print(f"     {tag:6} λ={hd['lam']} coef={hd['interaction_coef']} sign={hd['coef_sign']} eval_corr={hd['eval_pred_corr']}")
    print("\nsaved _payout_interaction.json")


if __name__ == "__main__":
    main()
