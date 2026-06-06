# -*- coding: utf-8 -*-
"""measure_chem_rotation_v2.py — 화학 rotation 후보 ≥8개 확장 + strict NCC 코어 universe robustness.

team-lead 지시: 후보 ≥8(NCC spread/나프타/에틸렌/프로필렌/China PMI/중국부동산/유가/환율/PBR밴드) +
strict 화학 화이트리스트(LG화학/롯데/금호석유 등 순수 NCC) 패널 robustness.

★에틸렌/프로필렌 spot = ICIS/Platts 유료 부재 → collector_plan 명시. 가용 proxy로 ≥8 후보 측정.
"""
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np, pandas as pd
from scipy import stats
ROOT=Path(__file__).resolve().parent; CHEM=ROOT.parent.parent; DATA=ROOT/"data"
OOS_SPLIT="2023-01-01"; T_BREAKEVEN=2.802

# ★strict NCC 코어 (순수 석유화학, 신사업·정밀화학 제외) vs full 17종
NCC_CORE=["051910","011170","009830","011780","006650","005950"]  # LG화학/롯데/한화솔/금호석유/대한유화/이수화학

def n_eff_autocorr(x,ml=12):
    n=len(x)
    if n<4: return float(n)
    e=x-x.mean();v=(e@e)/n
    if v<=0:return float(n)
    s=0.0
    for k in range(1,min(ml,n-1)+1):
        rk=(e[k:]@e[:-k])/n/v
        if rk<=0:break
        s+=(1-k/(ml+1))*rk
    return float(n/(1+2*s))
def wild_cluster_p(x,B=2000,seed=42):
    n=len(x)
    if n<4:return np.nan
    rng=np.random.default_rng(seed);sd=x.std(ddof=1)
    t=abs(x.mean()/(sd/np.sqrt(n))) if sd>0 else 0
    e=x-x.mean();c=0
    for _ in range(B):
        w=rng.choice([-1.,1.],size=n);xn=w*e;sb=xn.std(ddof=1)
        tb=abs(xn.mean()/(sb/np.sqrt(n))) if sb>0 else 0
        if tb>=t:c+=1
    return (c+1)/(B+1)
def block_boot_ci(x,bl,B=2000,seed=42):
    rng=np.random.default_rng(seed);n=len(x)
    if n<bl+1:return[np.nan,np.nan]
    nb=int(np.ceil(n/bl));m=[]
    for _ in range(B):
        st=rng.integers(0,n-bl+1,size=nb)
        m.append(np.concatenate([x[s:s+bl] for s in st])[:n].mean())
    return[float(np.percentile(m,2.5)),float(np.percentile(m,97.5))]

def fwd_h(r,h): return r.shift(-1).rolling(h).sum().shift(-(h-1)) if h>1 else r.shift(-1)

def measure(sig,ind_ret,h,label,prior):
    fwd=fwd_h(ind_ret,h)
    df=pd.concat([sig.rename("s"),fwd.rename("f")],axis=1).dropna()
    if len(df)<12: return {"label":label,"status":"INSUFFICIENT","n":len(df)}
    rho,p=stats.spearmanr(df["s"],df["f"]); n=len(df); neff=n_eff_autocorr(df["f"].values)
    prod=(stats.rankdata(df["s"])-n/2)*(stats.rankdata(df["f"])-n/2)
    wc=wild_cluster_p(prod); ci=block_boot_ci(prod,max(2,round(h)))
    is_d=df[df.index<OOS_SPLIT];oos_d=df[df.index>=OOS_SPLIT]
    ris=stats.spearmanr(is_d["s"],is_d["f"])[0] if len(is_d)>=8 else np.nan
    ros=stats.spearmanr(oos_d["s"],oos_d["f"])[0] if len(oos_d)>=8 else np.nan
    sh=not np.isnan(ris) and not np.isnan(ros) and np.sign(ris)==np.sign(ros)
    mh=sh and abs(ros)>=abs(ris)*0.5
    pm=(np.sign(rho)==(1 if prior=="양" else -1)) if not np.isnan(rho) and prior in("양","음") else None
    return {"label":label,"n":n,"n_eff":round(neff,1),"rho":round(float(rho),4),"wc_p":round(float(wc),4),
            "t_power":round(abs(rho)*np.sqrt(neff),2),"ci":[round(c,4) for c in ci],"prior":prior,
            "prior_match":(None if pm is None else bool(pm)),
            "oos":{"is":round(float(ris),3) if not np.isnan(ris) else None,"oos":round(float(ros),3) if not np.isnan(ros) else None,
                   "eligible":bool(mh),"verdict":"OOS+mag유지" if mh else("OOS부호유지 mag약" if sh else "OOS flip")},
            "status":"powered" if (n>=24 and neff>=6) else "underpowered"}

def build_signals():
    cyc=pd.read_parquet(DATA/"chem_rotation_cycle.parquet"); cyc.index=pd.to_datetime(cyc.index); cm=cyc.resample("ME").last()
    ext=pd.read_parquet(DATA/"chem_rotation_ext.parquet"); ext.index=pd.to_datetime(ext.index); em=ext.resample("ME").last()
    z=lambda s:(s-s.mean())/s.std()
    yoy=lambda s:s/s.shift(12)-1
    naph=yoy(cm["wti_naphtha"]); fxi=yoy(cm["china_fxi"]); mchi=yoy(cm["china_mchi"])
    usdkrw=yoy(em["usdkrw"]); brent=yoy(em["brent"]); krexp=yoy(em["kr_exports"])
    # ★후보 ≥8 (에틸렌/프로필렌 spot 부재 → demand/cost/spread proxy로 대체)
    return {
      "naphtha_yoy":(naph,"음"),                          # 1 cost-push (v2 baseline)
      "china_mchi_yoy":(mchi,"양"),                        # 2 중국 수요(전체)
      "china_fxi_yoy":(fxi,"양"),                          # 3 중국 수요(대형)
      "spread_china_minus_naphtha":(z(fxi)-z(naph),"양"),  # 4 NCC spread proxy(demand-cost margin)
      "spread_china_minus_brent":(z(mchi)-z(brent),"양"),  # 5 margin proxy(brent 원가)
      "usdkrw_yoy":(usdkrw,"양"),                          # 6 환율(원화약세→수출+)
      "brent_yoy":(brent,"음"),                            # 7 유가 level(cost, naphtha 동조)
      "kr_exports_yoy":(krexp,"양"),                       # 8 한국 수출(화학 전방)
    }

def ind_ret(codes=None):
    px=pd.read_parquet(CHEM/"raw-v3"/"data"/"prices.parquet"); px.index=pd.to_datetime(px.index)
    if codes: px=px[[c for c in codes if c in px.columns]]
    return px.resample("ME").last().pct_change().mean(axis=1).dropna()

def main():
    sigs=build_signals()
    out={"meta":{"n_candidates":len(sigs),"universe_full":"17종 화이트리스트","universe_strict_NCC":NCC_CORE,
                 "ethylene_propylene_note":"에틸렌/프로필렌 spot = ICIS/Platts 유료 부재 = collector_plan. demand/cost/spread proxy 대체.",
                 "prior_commit":"naphtha/brent 음(cost) / china/krexp/usdkrw 양(demand) / spread 양(margin). 데이터 접촉 前 동결."},
         "full_17":{}, "strict_NCC_6":{}}
    r_full=ind_ret(); r_ncc=ind_ret(NCC_CORE)
    for tag,rr in [("full_17",r_full),("strict_NCC_6",r_ncc)]:
        for h,hn in [(1,"y_20d"),(3,"y_60d")]:
            for sn,(sig,pr) in sigs.items():
                out[tag][f"{sn}__{hn}"]=measure(sig.dropna(),rr,h,f"chem__{tag}__{sn}__{hn}",pr)
    (ROOT/"validation-chem-rotation-v2.json").write_text(json.dumps(out,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
    print(f"후보 {len(sigs)}개 | full n={len(r_full)} / strict NCC(6종) n={len(r_ncc)}")
    for tag in ["full_17","strict_NCC_6"]:
        print(f"\n=== {tag} (y_60d) ===")
        print(f"{'signal':<32}{'rho':>8}{'match':>6}{'wc_p':>8}{'t_pwr':>6}{'OOS':>16}")
        for k,v in out[tag].items():
            if not k.endswith("y_60d") or v.get("status")=="INSUFFICIENT": continue
            pm='Y' if v['prior_match'] else ('N' if v['prior_match'] is False else '-')
            print(f"{k.replace('__y_60d',''):<32}{v['rho']:>+8.3f}{pm:>6}{v['wc_p']:>8.3f}{v['t_power']:>6.2f}  {v['oos']['verdict']:<14}")

if __name__=="__main__": main()
