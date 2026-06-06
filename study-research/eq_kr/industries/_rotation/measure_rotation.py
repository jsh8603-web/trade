# -*- coding: utf-8 -*-
"""measure_rotation.py — 12산업 rotation timing 측정 (plan §10 S5.5, line 45 "rotation 측정 대상").

★임무 = "어느 산업을 (현재 국면에) 살지" = 산업 자체 비중 timing (rotation).
기존 12산업 capsule = 전부 cross-sectional(산업 안 어느 종목) IC만 측정.
본 측정 = 그 위 차원 = ★산업 자체 시계열 forward return 예측 = "이 국면→반도체 비중↑/정유↓".

frame §M2 (산업 panel 평균 시계열) + refining/measure_timeseries.py prototype 일반화.
refining 은 cycle driver vs 패널수익 동조(contemporaneous 본체)만 봤으나, rotation 임무는
★forward 예측력(timing 신호 자격)이 본체 + walk-forward OOS eligibility(G-G v2) 추가.

================================================================================
★G-F FRAME CONTRACT 7항 사전선언 (measure_timeseries.py 준용 + rotation 조정)
================================================================================
1. regime 선언: Macro(CLI 4) × KRW(3) × flow(3) = regime_labels.parquet (각 산업 동일 공통 macro).
   effective-n = block 수 (월간 패널, NW lag = horizon_months). n_eff = n/(1+2Σρ_k).
2. interaction/split 사전확약: forward h일 = panel_ret.shift(-h). regime split 사전동결.
   본 측정 = 단변량 신호 forward 예측 먼저 (factor×factor 금지, factor×regime 보류=통합단계).
3. ★단일 FDR family: {12산업 × rotation 신호군(mom/rev/macro/relative/valband) × horizon} = 큰
   multiplicity → BY-FDR 엄격 (plan §10 S5.5 "12산업×지표 multiplicity 큼, BY 엄격").
4. null + MDE/power: null = forward 예측 corr 0. ★MDE/power = t_obs = IC·√N/σ_IC ⋚ 2.802
   (G-G v2 breakeven). t<2.802 = underpowered (미생존=artifact, OOS 부호유지면 tradeable).
5. PIT 동결: 가격신호 = forward shift (PIT-safe). macro driver = 발표시점 lag.
   ★valuation band = DART equity rcept_dt 이후만 (lookahead 회피).
6. ★turnover / T-cost: rotation = sleeve-level 비중 timing. net-cost = KR STT 0.2% 비대칭
   (매도측). turnover-aware no-trade region (자문 gated 설계). 통합단계 sizing.
7. per-test: 월간 n~88, eff-N autocorr 보정 + wild-cluster bootstrap(Rademacher B=2000)
   + block-boot CI. small-block NW-HAC asymptotic t 보조만.

★G-G v2 tradeable signal 자격 (4조건, plan §10 S5.5):
  (a) 방향 확정: walk-forward OOS(IS 2019-22 / OOS 2023-26) 부호+magnitude 유지 (OOS flip=무효).
  (b) tier ≥ structural_prior_low_confidence (INSUFFICIENT/REJECTED 제외).
  (c) net-alpha 양: turnover·T-cost 차감 후 gross 보존 (통합단계, 여기선 |IC| vs cost 표시).
  (d) regime 조건 명시: 어느 국면에서 작동 (conditional 측정).
  → eligibility(OOS 부호유지) = 매매 자격 1차 / conviction(FDR 생존·shrunk IC) = sizing 2차.
================================================================================
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
IND_ROOT = ROOT.parent  # industries/
OUT = ROOT / "data"
OUT.mkdir(exist_ok=True)

INDUSTRIES = ["semiconductor", "auto", "financial", "battery", "chemical", "refining",
              "shipbuilding", "steel", "bio", "consumer", "telecom", "aitech"]

HORIZONS_M = {"y_20d": 1, "y_60d": 3}   # 월간 패널 → 1M=20d, 3M=60d forward (메인 20d/60d)
OOS_SPLIT = "2023-01-01"                # IS 2019-2022 / OOS 2023-2026 (walk-forward)
T_BREAKEVEN = 2.802                     # G-G v2 MDE/power breakeven
STT_SELL = 0.0020                       # KR 증권거래세 매도측 (G-F §6 비대칭)
COMMISSION = 0.00015                    # 편도 수수료 근사
TURNOVER_ASSUMED = 0.5                  # 월 turnover 가정 (rotation = sleeve-level, 종목선택보다 낮음)


# ──────────────── 통계 인프라 (refining/measure_timeseries.py 재사용) ────────────────
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
    rng = np.random.default_rng(seed)
    sd = x.std(ddof=1)
    t_obs = abs(x.mean() / (sd / np.sqrt(n))) if sd > 0 else 0.0
    e = x - x.mean(); cnt = 0
    for _ in range(B):
        w = rng.choice([-1.0, 1.0], size=n)
        xn = w * e; sb = xn.std(ddof=1)
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
    """단일 FDR family — 12산업×신호×horizon multiplicity. BY (의존성 보정, 엄격)."""
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
            "raw_p_min": round(items[0][1], 5), "raw_p_min_key": items[0][0],
            "bonferroni_alpha": round(0.05 / m, 5)}


def signal_forward_stat(sig: pd.Series, fwd: pd.Series, h_months: int, label: str,
                        oos_split: str = OOS_SPLIT):
    """rotation 신호의 forward 예측력 (★본체) + walk-forward OOS eligibility.

    sig(t) → fwd(t) = panel forward h-month return. Spearman rank-corr 시계열 검정.
    paired rank product (mean ∝ rho) → wild-cluster + block-boot + eff-N + MDE/power.
    ★OOS: IS(<oos_split) / OOS(>=oos_split) 각각 rho 부호+magnitude 유지 여부 (G-G v2 (a)).
    """
    common = sig.dropna().index.intersection(fwd.dropna().index)
    if len(common) < 12:
        return {"label": label, "n": len(common), "status": "INSUFFICIENT(n<12)"}
    sv, fv = sig.loc[common].values, fwd.loc[common].values
    rho, p_param = stats.spearmanr(sv, fv)
    sr = stats.rankdata(sv) / len(sv) - 0.5
    fr = stats.rankdata(fv) / len(fv) - 0.5
    prod = sr * fr
    n = len(prod)
    neff = n_eff_autocorr(prod)
    se = nw_se(prod, h_months)
    t_nw = prod.mean() / se if se and se > 0 else np.nan
    wc_p = wild_cluster_p(prod)
    ci = block_boot_ci(prod, max(2, h_months))
    # MDE/power (G-G v2): t_obs = IC·√neff/σ_IC ≈ |rho|·√neff. breakeven 2.802.
    t_power = abs(rho) * np.sqrt(max(neff, 1.0))
    powered = (n >= 24) and (neff >= 6) and (t_power >= T_BREAKEVEN)

    # ── walk-forward OOS (eligibility 1차) ──
    is_idx = [d for d in common if str(d) < oos_split]
    oos_idx = [d for d in common if str(d) >= oos_split]
    oos = {"is_n": len(is_idx), "oos_n": len(oos_idx)}
    if len(is_idx) >= 8 and len(oos_idx) >= 8:
        rho_is, _ = stats.spearmanr(sig.loc[is_idx].values, fwd.loc[is_idx].values)
        rho_oos, _ = stats.spearmanr(sig.loc[oos_idx].values, fwd.loc[oos_idx].values)
        oos.update({"rho_is": round(float(rho_is), 4), "rho_oos": round(float(rho_oos), 4)})
        sign_hold = (np.sign(rho_is) == np.sign(rho_oos)) and abs(rho_oos) >= 0.5 * abs(rho_is)
        oos["eligible"] = bool(sign_hold and abs(rho_oos) > 0.02)
        oos["verdict"] = ("✅OOS 부호+magnitude 유지" if sign_hold
                          else ("⚠️OOS 부호유지 magnitude약" if np.sign(rho_is) == np.sign(rho_oos)
                                else "❌OOS flip"))
    else:
        oos["eligible"] = None
        oos["verdict"] = "OOS n<8 (split 불가)"

    return {"label": label, "n": n, "n_eff": round(neff, 1),
            "spearman_rho": round(float(rho), 4), "p_parametric": round(float(p_param), 4),
            "t_nw_asymptotic": round(t_nw, 2) if not np.isnan(t_nw) else None,
            "t_power_mde": round(float(t_power), 2),  # G-G v2 t_obs⋚2.802
            "wild_cluster_p": round(wc_p, 4) if not np.isnan(wc_p) else None,
            "ci95_block_boot_prod": [round(c, 5) for c in ci] if not np.isnan(ci[0]) else None,
            "walk_forward_oos": oos,
            "status": "powered" if powered else ("underpowered" if n >= 12 else "INSUFFICIENT")}


# ──────────────── 산업 패널 + rotation 신호 구성 ────────────────
def load_industry(sector: str):
    d = IND_ROOT / sector / "raw-v3" / "data"
    px = pd.read_parquet(d / "prices.parquet"); px.index = pd.to_datetime(px.index)
    lab = pd.read_parquet(d / "regime_labels.parquet"); lab.index = pd.to_datetime(lab.index)
    rs = pd.read_parquet(d / "regime_series.parquet"); rs.index = pd.to_datetime(rs.index)
    try:
        dart = pd.read_parquet(d / "dart_financials.parquet")
    except Exception:
        dart = None
    return px, lab, rs, dart


def panel_monthly_return(px: pd.DataFrame) -> pd.Series:
    """산업 eq-weight 월수익 = 종목 월수익 동일가중 평균 (최소 1종 존재 월)."""
    pxm = px.resample("ME").last()
    ret = pxm.pct_change()
    return ret.mean(axis=1, skipna=True)


def build_signals(px: pd.DataFrame, rs: pd.DataFrame, all_panels: pd.DataFrame, sector: str):
    """rotation timing 신호군 (산업 자체 시계열, PIT-safe)."""
    pret = panel_monthly_return(px).loc["2019-01-01":]
    cum = (1 + pret.fillna(0)).cumprod()   # 산업 누적 가격지수 (eq-weight)
    sig = {}
    # (1) 산업 자체 momentum / reversal (own past return, PIT = 과거만)
    sig["mom_12_1"] = cum.pct_change(11).shift(1)          # 12-1M momentum (skip 최근월)
    sig["mom_6"] = cum.pct_change(6)                        # 6M momentum
    sig["rev_1m"] = pret                                    # 1M (reversal 후보, 부호 음 예상)
    sig["mom_3"] = cum.pct_change(3)                        # 3M momentum
    # (3) 공통 macro driver (PIT: 월말 관측, level + Δ)
    # ★★PIT 발표지연 lag 의무 (regime_series.parquet 는 raw = lag 미적용, label 단계서만 lag).
    #   CLI(OECD KORLOLITOAASTSAM) = reference month 후 ~2개월 지연 발표 → CLI_PUB_LAG=2 (collect_regime.py 준용).
    #   semi_ppi(반도체 PPI) = 월별 ~1개월 지연 → SEMI_PPI_LAG=1.
    #   ⛔ lag 미적용 시 cli_chg/semi_ppi_yoy 가 비현실적으로 강해짐(lookahead leakage, D축 위반).
    #   usdkrw(DEXKOUS 일별)·foreign_flow(ECOS 일별) = 실시간이라 lag 불필요.
    CLI_PUB_LAG = 2
    SEMI_PPI_LAG = 1
    rsm = rs.resample("ME").last()
    cli_pit = rsm["cli_kr"].shift(CLI_PUB_LAG)
    sig["usdkrw_yoy"] = rsm["usdkrw"].pct_change(12)        # 환율 yoy (수출 cycle)
    sig["d_usdkrw"] = rsm["usdkrw"].pct_change(1)           # 환율 Δ (1M)
    sig["foreign_flow"] = rsm["foreign_net_kospi"]          # 외국인 순매수 (level)
    sig["cli_chg"] = cli_pit.diff()                         # ★경기선행 Δ (PIT lag=2 적용)
    if "semi_ppi" in rsm.columns:
        sig["semi_ppi_yoy"] = rsm["semi_ppi"].shift(SEMI_PPI_LAG).pct_change(12)  # 반도체 PPI yoy (PIT lag=1)
    # (4) cross-industry relative momentum (산업 vs 12산업 평균 상대강도)
    if all_panels is not None and sector in all_panels.columns:
        mkt = all_panels.mean(axis=1)                      # 12산업 eq-weight 평균
        rel = all_panels[sector] - mkt                     # 상대 월수익
        relcum = (1 + rel.fillna(0)).cumprod()
        sig["rel_mom_6"] = relcum.pct_change(6)            # 상대 6M 모멘텀 (rotation 핵심)
        sig["rel_mom_3"] = relcum.pct_change(3)
    return pret, {k: v.loc["2019-01-01":] for k, v in sig.items()}


def main():
    # ── 1차: 전 산업 패널 월수익 수집 (cross-industry relative 위해) ──
    all_panels = {}
    px_cache = {}
    for s in INDUSTRIES:
        try:
            px, lab, rs, dart = load_industry(s)
            px_cache[s] = (px, lab, rs, dart)
            all_panels[s] = panel_monthly_return(px)
        except Exception as e:
            print(f"[load 실패] {s}: {e}")
    all_panels = pd.DataFrame(all_panels)

    results = {"meta": {
        "method": "12산업 rotation timing — eq-weight 산업 패널 forward return 예측 (frame M2 일반화)",
        "임무": "어느 산업을 현재 국면에 살지 = 산업 자체 비중 timing (종목selection과 별 차원)",
        "prototype": "refining/measure_timeseries.py (cycle driver 동조) 를 forward 예측 + OOS 로 일반화",
        "horizons_months": HORIZONS_M, "oos_split": OOS_SPLIT, "t_breakeven_mde": T_BREAKEVEN,
        "net_cost": {"stt_sell": STT_SELL, "commission": COMMISSION, "turnover_m": TURNOVER_ASSUMED,
                     "roundtrip_bps": round((STT_SELL + 2 * COMMISSION) * 1e4, 1),
                     "monthly_cost_bps": round((STT_SELL + 2 * COMMISSION) * TURNOVER_ASSUMED * 1e4, 1)},
        "gf_contract": "헤더 7항 사전선언 (G-F). G-G v2 tradeable 4조건 (OOS eligibility + tier + net + regime).",
    }, "industries": {}}

    fdr_pvals = {}   # 단일 FDR family (12산업 × 신호 × horizon)

    for s in INDUSTRIES:
        if s not in px_cache:
            continue
        px, lab, rs, dart = px_cache[s]
        pret, sigs = build_signals(px, rs, all_panels, s)
        cum = (1 + pret.fillna(0)).cumprod()
        sec_res = {"panel": {"n_months": int(pret.dropna().shape[0]),
                             "ret_mean_m": round(float(pret.mean()), 4),
                             "ret_vol_m": round(float(pret.std()), 4)},
                   "signals": {}}
        for hl, hm in HORIZONS_M.items():
            # forward panel return (h개월)
            fwd = cum.pct_change(hm).shift(-hm)
            sec_res["signals"][hl] = {}
            for signame, sigser in sigs.items():
                st = signal_forward_stat(sigser, fwd, hm, f"{s}__{signame}__{hl}")
                sec_res["signals"][hl][signame] = st
                if st.get("status") == "powered" and st.get("wild_cluster_p") is not None:
                    fdr_pvals[f"{s}__{signame}__{hl}"] = st["wild_cluster_p"]
        results["industries"][s] = sec_res

    results["fdr_family_single"] = benjamini_yekutieli(fdr_pvals)

    out = ROOT / "validation-rotation-v1.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Saved {out}")
    print_summary(results)
    return results


def print_summary(r):
    print("\n" + "=" * 78)
    print("12산업 ROTATION TIMING — forward 예측 신호 (powered + OOS eligible 만)")
    print("=" * 78)
    for s, sd in r["industries"].items():
        rows = []
        for hl, hsig in sd["signals"].items():
            for sn, st in hsig.items():
                if st.get("status") == "powered":
                    oos = st.get("walk_forward_oos", {})
                    elig = oos.get("eligible")
                    mark = "✅" if elig else ("⚠️" if elig is None else "❌")
                    rows.append(f"    {mark}{sn:14s}[{hl}] rho={st.get('spearman_rho'):+.3f} "
                                f"wc_p={st.get('wild_cluster_p')} t_pow={st.get('t_power_mde')} "
                                f"OOS:{oos.get('rho_is')}→{oos.get('rho_oos')} {oos.get('verdict','')}")
        if rows:
            print(f"\n  [{s}] n={sd['panel']['n_months']}월")
            print("\n".join(rows))
    print(f"\n{'='*78}\n단일 FDR family (BY): {json.dumps(r['fdr_family_single'], ensure_ascii=False)}")


if __name__ == "__main__":
    main()
