# -*- coding: utf-8 -*-
"""
M4 coin_macro_vol_transfer — 승격 게이트: ex-ante Markov stress-state 레짐 (달력컷 E3 대체).

가설: VIX→BTC fwd-vol 전이가 ex-ante 관측가능 stress regime 에서만 강한가?
  기존 G1 ex-ante 시도(.p2-m4-voltransfer.py L122 BTC-SPX 90d corr split)=return 동조라 부적합 기각.
  → 미답 잔여 = VIX 자체 Markov-switching(2-state, switching variance). filtered prob =
     persistence 모델 + ex-ante(smoothed=look-ahead 금지, filtered/predicted 만 사용, C10 정합).

승격 기준(모두 충족 시 ex-ante 레짐이 달력컷 E3 를 진짜 대체):
  (a) stress regime 서 VIX→fvol ⊥HAR 유의 + calm 서 약/소멸 (regime 분리)
  (b) regime label 이 calendar E3 와 독립(전 era 에 stress episode 분포) = 달력 동치 아님
  (c) horizon 일관(10/30/60) + small-n rigor(episode n·NW-HAC maxlags=45·Bonferroni·hedge)

⛔ 임시. throttle-only 후보 검정(bw=0 불변식, sizing alpha 아님). filtered(ex-ante) vs smoothed(대조용만).
실행: PYTHONUTF8=1 "<py>" .p2-m4-voltransfer-markov.py
"""
import os, importlib.util, warnings, numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats
import yfinance as yf
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cf", os.path.join(ROOT, ".p2-corrected-frame.py"))
cf = importlib.util.module_from_spec(spec); spec.loader.exec_module(cf)
H = 45  # NW-HAC maxlags (fwd 30d overlap)


def rank_z(s):
    r = stats.rankdata(s); return (r - r.mean()) / r.std()


def ic_resid(df, sig, tgt, ctrls, lag=H):
    """⊥ctrls 잔차 IC + NW-HAC. n / episode-aware."""
    cols = [sig, tgt] + ctrls
    M = df[cols].dropna().copy()
    if len(M) < 40:
        return np.nan, np.nan, len(M)
    for c in cols:
        M[c] = rank_z(M[c].values)
    rx = sm.OLS(M[sig], sm.add_constant(M[ctrls])).fit().resid
    ry = sm.OLS(M[tgt], sm.add_constant(M[ctrls])).fit().resid
    md = sm.OLS(ry.values, sm.add_constant(rx.values)).fit(cov_type="HAC", cov_kwds={"maxlags": lag})
    return float(md.params[1]), float(md.pvalues[1]), len(M)


def n_episodes(mask_series):
    """연속 True 구간(regime episode) 수 = 독립 표본 근사(overlapping 자기상관 노출)."""
    m = mask_series.fillna(False).astype(int).values
    return int(((m[1:] == 1) & (m[:-1] == 0)).sum() + (1 if len(m) and m[0] == 1 else 0))


def main():
    b = cf.build()
    # VIX fetch (기존 스크립트와 동일 경로)
    vix = yf.Ticker("^VIX").history(period="max")[["Close"]].rename(columns={"Close": "vix"})
    vix.index = pd.to_datetime(vix.index).tz_localize(None).normalize()
    b = b.merge(vix, left_on="date", right_index=True, how="left")
    b["vix"] = b["vix"].ffill()
    b["vix_z"] = (b["vix"] - b["vix"].rolling(90).mean()) / b["vix"].rolling(90).std()
    har = ["rv1", "rv5", "rv22"]

    # ---- VIX 2-state Markov-switching (switching mean; high-VIX-level = stress) ----
    # ★switching_variance=True 는 한 regime sigma2→0 degenerate 수렴 → mean-switch 채택.
    #   param=full-sample MLE(structural, 시간불변 가정), state inference 만 filtered ex-ante(smoothed 금지).
    vser = b.dropna(subset=["vix"]).copy()
    vlog = np.log(vser["vix"].values)
    mod = MarkovRegression(vlog, k_regimes=2, trend="c", switching_variance=False)
    res = mod.fit(maxiter=500, disp=False)
    pp = dict(zip(res.model.param_names, np.asarray(res.params)))
    consts = [pp["const[0]"], pp["const[1]"]]
    hi = int(np.argmax(consts))          # high-mean(VIX level) regime = stress
    filt = np.asarray(res.filtered_marginal_probabilities)[:, hi]      # ex-ante(당일까지)
    pred = np.asarray(res.predicted_marginal_probabilities)[:, hi]     # one-step-ahead(완전 ex-ante)
    # predicted 는 길이 n+1 → 마지막 forecast 컷
    pred = pred[:len(filt)]
    vser["p_stress_filt"] = filt
    vser["p_stress_pred"] = pred
    b = b.merge(vser[["date", "p_stress_filt", "p_stress_pred"]], on="date", how="left")
    # regime label: stress if p>0.5. ★ex-ante 강화 = shift(1)(어제까지 정보로 오늘 라벨)
    b["regime_filt"] = (b["p_stress_filt"] > 0.5)
    b["regime_pred_lag"] = (b["p_stress_pred"].shift(1) > 0.5)

    print("=" * 100)
    print("M4 macro_vol_transfer 승격게이트 — VIX 2-state Markov stress-regime (ex-ante 달력컷 대체)")
    mean_dur = vser.assign(s=vser["p_stress_filt"] > 0.5)["s"].sum()
    p_stay = pp.get(f"p[{hi}->{hi}]", 1.0 - pp.get(f"p[{hi}->{1-hi}]", np.nan))
    print(f"  VIX Markov fit: const(log-VIX)={[round(c,3) for c in consts]} → exp={[round(float(np.exp(c)),1) for c in consts]} "
          f"hi-state={hi} | stress일수={int(mean_dur)}/{len(vser)} ({100*mean_dur/len(vser):.0f}%)  P(stay|stress)={p_stay:.3f}")
    print("=" * 100)

    # ---- (a) regime 분리: stress vs calm 에서 VIX→fvol ⊥HAR ----
    print("\n[(a) regime 분리] VIX z → fvol30 ⊥HAR | stress(filt>0.5) vs calm")
    res_a = {}
    for lab, col in (("filtered", "regime_filt"), ("predicted_lag1", "regime_pred_lag")):
        hi_df = b[b[col] == True]; lo_df = b[b[col] == False]
        bh, ph, nh = ic_resid(hi_df, "vix_z", "fvol30", har)
        bl, pl, nl = ic_resid(lo_df, "vix_z", "fvol30", har)
        eh = n_episodes(b[col]);
        print(f"  [{lab:13s}] STRESS β{bh:+.3f} p{ph:.4f} n{nh}(ep≈{eh})  vs  CALM β{bl:+.3f} p{pl:.4f} n{nl}")
        res_a[lab] = (bh, ph, nh, eh, bl, pl, nl)

    # ---- (b) calendar 독립: regime label vs epoch 교차 (달력 동치 검정) ----
    print("\n[(b) calendar 독립] stress-regime 이 epoch(E1/E2/E3) 전반 분포하나 (E3 동치면 대체 의미 없음)")
    ct = pd.crosstab(b["epoch"], b["regime_filt"])
    for e in ("E1", "E2", "E3"):
        if e in ct.index:
            tot = ct.loc[e].sum(); st = ct.loc[e].get(True, 0)
            print(f"   {e}: stress {st}/{tot} ({100*st/tot:.0f}%)")
    # E3 외 stress 비중 = 달력 독립성 지표
    nonE3_stress = b[(b["epoch"] != "E3") & (b["regime_filt"] == True)].shape[0]
    allstress = b[b["regime_filt"] == True].shape[0]
    print(f"   ★stress 중 non-E3 비중 = {nonE3_stress}/{allstress} ({100*nonE3_stress/max(1,allstress):.0f}%) "
          f"— 높을수록 달력 E3 와 독립(ex-ante 레짐이 진짜 추가정보)")

    # ---- (c) horizon 일관 (stress regime, filtered) + Bonferroni ----
    print("\n[(c) horizon 일관] STRESS(filt) VIX z → fvol{10,30,60} ⊥HAR")
    for h in (10, 30, 60):
        b[f"fvol{h}"] = b["lr"].shift(-h).rolling(h).std() * np.sqrt(365)
    hi_df = b[b["regime_filt"] == True]
    cells = []
    for h in (10, 30, 60):
        bb, pp, nn = ic_resid(hi_df, "vix_z", f"fvol{h}", har, lag=max(20, int(h * 1.5)))
        cells.append(f"fvol{h}:β{bb:+.3f} p{pp:.4f} n{nn}")
    print("   " + "  ".join(cells))

    # ---- small-n rigor verdict ----
    bh, ph, nh, eh, bl, pl, nl = res_a["filtered"]
    bhp, php, nhp, ehp, blp, plp, nlp = res_a["predicted_lag1"]
    m_tests = 2  # stress filtered + predicted (signal=vix only)
    bonf = 0.05 / m_tests
    print("\n" + "-" * 100)
    print(f"[small-n rigor] m={m_tests} 비교 Bonferroni α/{m_tests}={bonf:.4f} | episode≈{eh}(stress filtered)")
    sep_filt = (not np.isnan(ph) and ph < bonf) and (np.isnan(pl) or pl > 0.10)
    sep_pred = (not np.isnan(php) and php < bonf) and (np.isnan(plp) or plp > 0.10)
    indep = 100 * nonE3_stress / max(1, allstress)
    print(f"   (a) regime 분리: filtered STRESS p{ph:.4f}{'<' if ph<bonf else '≥'}Bonf & CALM p{pl:.4f} → {'분리 O' if sep_filt else '분리 X'}")
    print(f"                    predicted(lag1) STRESS p{php:.4f} & CALM p{plp:.4f} → {'분리 O' if sep_pred else '분리 X'}")
    print(f"   (b) 달력독립: stress 중 non-E3 {indep:.0f}% → {'독립 O(전era 분포)' if indep>=20 else '독립 X(E3 편중=달력동치)'}")
    print("   verdict(hedge): " + (
        "ex-ante Markov stress-state 가 VIX→vol 전이를 조건화 — 달력컷 E3 대체 *시사*(throttle-only, bw=0 유지). 잠정."
        if (sep_filt or sep_pred) and indep >= 20 else
        "ex-ante Markov 레짐 분리 비유의 OR 달력 E3 편중 — 승격 보류, candidate 유지(달력컷 한계 박제). 방향성 약 prior."))
    print("=" * 100)


if __name__ == "__main__":
    main()
