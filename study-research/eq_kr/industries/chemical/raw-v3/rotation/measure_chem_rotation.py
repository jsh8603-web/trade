# -*- coding: utf-8 -*-
"""measure_chem_rotation.py — 화학 업종 rotation 신호 측정 (naphtha cost-push vs China demand 본질 판별).

분석 unit = 화학 업종 eq-weight 월수익 (17종 prices.parquet). ★종목 cross-section 아님 = 업종 timing.
종속 = 업종 forward y_20d(1M)/y_60d(3M). 신호 = 업종 자체 시계열 예측 (rotation).

★이론 부호 사전확약 (데이터 접촉 前 동결, theory-notes 기반):
  - naphtha_yoy → forward: 음(-) [cost-push: 납사 원가↑→마진↓→비중↓]
  - china_demand(FXI yoy) → forward: 양(+) [demand-pull: 중국 전방수요↑→화학↑]
  - ★본질 가설(team-lead): naphtha 단독(_rotation v2 -0.367)보다 China demand 또는 spread(demand-cost)가 본질.
    naphtha cost-push만이면 demand 통제 후 약화 / demand-pull 본질이면 China 신호 강·OOS 유지.

게이트(G-G v2): forward Spearman IC + walk-forward OOS(IS2019-22/OOS2023-26) + wild-cluster + block-boot + MDE/power.
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np, pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
CHEM = ROOT.parent.parent  # industries/chemical/
DATA = ROOT / "data"
OOS_SPLIT = "2023-01-01"
T_BREAKEVEN = 2.802

def nw_se(x, lag):
    n=len(x)
    if n<3: return np.nan
    e=x-x.mean(); var=(e@e)/n
    for k in range(1,min(lag,n-1)+1): var+=2*(1-k/(lag+1))*(e[k:]@e[:-k])/n
    return float(np.sqrt(max(var,1e-12)/n))

def n_eff_autocorr(x, max_lag=12):
    n=len(x)
    if n<4: return float(n)
    e=x-x.mean(); v=(e@e)/n
    if v<=0: return float(n)
    s=0.0
    for k in range(1,min(max_lag,n-1)+1):
        rk=(e[k:]@e[:-k])/n/v
        if rk<=0: break
        s+=(1-k/(max_lag+1))*rk
    return float(n/(1+2*s))

def wild_cluster_p(x,B=2000,seed=42):
    n=len(x)
    if n<4: return np.nan
    rng=np.random.default_rng(seed); sd=x.std(ddof=1)
    t_obs=abs(x.mean()/(sd/np.sqrt(n))) if sd>0 else 0.0
    e=x-x.mean(); cnt=0
    for _ in range(B):
        w=rng.choice([-1.0,1.0],size=n); xn=w*e; sb=xn.std(ddof=1)
        tb=abs(xn.mean()/(sb/np.sqrt(n))) if sb>0 else 0.0
        if tb>=t_obs: cnt+=1
    return (cnt+1)/(B+1)

def block_boot_ci(x,block,B=2000,seed=42):
    rng=np.random.default_rng(seed); n=len(x)
    if n<block+1: return [np.nan,np.nan]
    nb=int(np.ceil(n/block)); means=[]
    for _ in range(B):
        st=rng.integers(0,n-block+1,size=nb)
        means.append(np.concatenate([x[s:s+block] for s in st])[:n].mean())
    return [float(np.percentile(means,2.5)),float(np.percentile(means,97.5))]

def measure_signal(sig_m, ind_ret_m, h, label, prior_sign):
    """업종 forward rolling-h IC: 신호 월값 vs 업종 forward h개월 누적수익 Spearman (시계열)."""
    fwd = ind_ret_m.shift(-1).rolling(h).sum().shift(-(h-1)) if h>1 else ind_ret_m.shift(-1)
    df = pd.concat([sig_m.rename("s"), fwd.rename("f")], axis=1).dropna()
    if len(df) < 12:
        return {"label":label,"status":"INSUFFICIENT","n":len(df)}
    rho, p = stats.spearmanr(df["s"], df["f"])
    n=len(df); neff=n_eff_autocorr(df["f"].values, max_lag=12)
    # IC 시계열 부재(단일 시계열 rho) → bootstrap CI on rho via block-boot of paired
    # block-boot on forward returns demeaned product proxy → use rho stability
    t_power = abs(rho)*np.sqrt(neff)
    # OOS split
    is_df=df[df.index<OOS_SPLIT]; oos_df=df[df.index>=OOS_SPLIT]
    rho_is=stats.spearmanr(is_df["s"],is_df["f"])[0] if len(is_df)>=8 else np.nan
    rho_oos=stats.spearmanr(oos_df["s"],oos_df["f"])[0] if len(oos_df)>=8 else np.nan
    sign_hold = (not np.isnan(rho_is) and not np.isnan(rho_oos) and np.sign(rho_is)==np.sign(rho_oos))
    mag_hold = sign_hold and abs(rho_oos)>=abs(rho_is)*0.5
    # wild-cluster on forward (proxy: sign of rho via paired demeaned product)
    prod = (stats.rankdata(df["s"])-len(df)/2)*(stats.rankdata(df["f"])-len(df)/2)
    wc_p = wild_cluster_p(prod - prod.mean() + prod.mean())  # mean test on product
    ci = block_boot_ci(prod, max(2, round(h)))
    prior_ok = (np.sign(rho)==(1 if prior_sign=="양" else -1)) if not np.isnan(rho) else False
    return {"label":label,"n":n,"n_eff":round(neff,1),"spearman_rho":round(float(rho),4),
            "p_param":round(float(p),4),"t_power_mde":round(float(t_power),2),
            "wild_cluster_p":round(float(wc_p),4),"ci95_block_boot_prod":[round(c,5) for c in ci],
            "prior_sign":prior_sign,"prior_match":bool(prior_ok),
            "walk_forward_oos":{"rho_is":round(float(rho_is),4) if not np.isnan(rho_is) else None,
                                "rho_oos":round(float(rho_oos),4) if not np.isnan(rho_oos) else None,
                                "is_n":len(is_df),"oos_n":len(oos_df),
                                "eligible":bool(mag_hold),
                                "verdict":("OOS 부호+mag 유지" if mag_hold else ("OOS 부호유지 mag약" if sign_hold else "OOS flip"))},
            "status":"powered" if (n>=24 and neff>=6) else "underpowered"}

def main():
    # 화학 업종 eq-weight 월수익
    px=pd.read_parquet(CHEM/"raw-v3"/"data"/"prices.parquet"); px.index=pd.to_datetime(px.index)
    pxm=px.resample("ME").last()
    ind_ret=pxm.pct_change().mean(axis=1).dropna()  # eq-weight 업종 월수익
    # cycle 데이터
    cyc=pd.read_parquet(DATA/"chem_rotation_cycle.parquet"); cyc.index=pd.to_datetime(cyc.index)
    cycm=cyc.resample("ME").last()
    # 신호 구성 (월말, 실시간 spot = PIT lag 불필요)
    naph_yoy = (cycm["wti_naphtha"]/cycm["wti_naphtha"].shift(12)-1)
    naph_d3  = (cycm["wti_naphtha"]/cycm["wti_naphtha"].shift(3)-1)
    fxi_yoy  = (cycm["china_fxi"]/cycm["china_fxi"].shift(12)-1)
    fxi_d3   = (cycm["china_fxi"]/cycm["china_fxi"].shift(3)-1)
    mchi_yoy = (cycm["china_mchi"]/cycm["china_mchi"].shift(12)-1)
    # ★spread proxy = china demand - naphtha cost (demand-pull minus cost-push, normalized)
    z=lambda s:(s-s.mean())/s.std()
    spread_proxy = z(fxi_yoy) - z(naph_yoy)   # demand 강 - cost 강 = margin proxy

    signals={
      "naphtha_yoy":(naph_yoy,"음"),     # cost-push (v2 baseline)
      "naphtha_d3":(naph_d3,"음"),
      "china_fxi_yoy":(fxi_yoy,"양"),    # demand-pull (심화 핵심)
      "china_fxi_d3":(fxi_d3,"양"),
      "china_mchi_yoy":(mchi_yoy,"양"),
      "spread_proxy_demand_minus_cost":(spread_proxy,"양"),  # ★본질 margin proxy
    }
    out={"meta":{"unit":"화학 업종 eq-weight 월수익 (17종)","n_months_ind":len(ind_ret),
                 "cycle_source":"wti_naphtha=CL=F / china=FXI,MCHI (yfinance). NCC spread 무료부재→China demand proxy 심화.",
                 "prior_commit":"naphtha 음(cost-push) / china 양(demand-pull) / spread=china-naphtha 양(margin). 데이터 접촉 前 동결."},
         "signals":{}}
    for h,hn in [(1,"y_20d"),(3,"y_60d")]:
        for sn,(sig,pr) in signals.items():
            r=measure_signal(sig.dropna(), ind_ret, h, f"chemical__rot_{sn}__{hn}", pr)
            out["signals"][f"{sn}__{hn}"]=r
    (ROOT/"validation-chem-rotation-v1.json").write_text(json.dumps(out,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
    # 출력
    print(f"업종 월수익 n={len(ind_ret)} {ind_ret.index.min().date()}~{ind_ret.index.max().date()}")
    print(f"{'signal':<38}{'rho':>8}{'prior':>6}{'match':>6}{'wc_p':>8}{'t_pwr':>6}{'OOS':>16}")
    for k,v in out["signals"].items():
        if v.get("status")=="INSUFFICIENT": continue
        wf=v["walk_forward_oos"]
        print(f"{k:<38}{v['spearman_rho']:>+8.3f}{v['prior_sign']:>6}{('Y' if v['prior_match'] else 'N'):>6}{v['wild_cluster_p']:>8.3f}{v['t_power_mde']:>6.2f}  {wf['verdict']:<14}")

if __name__=="__main__":
    main()
