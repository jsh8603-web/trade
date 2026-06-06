# -*- coding: utf-8 -*-
"""recheck_aux_signals.py — 보조 신호 정식 재판정 (직교 독립성 + residualize).
team-lead: STRONG spread 외 살아남는 보조 ≥1 찾기. 억지 발굴 금지(살아남는 것만).
재검: mom_3(residualize) / pbr_z(valband) / naphtha 단독(cost 채널 직교) / china_mchi 단독 / fxi.
★핵심 = 채택 신호 간 직교성(같은 demand 채널이면 독립 베팅 아님). naphtha=cost 채널=demand와 직교.
"""
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np, pandas as pd
from scipy import stats
ROOT=Path(__file__).resolve().parent; CHEM=ROOT.parent.parent; DATA=ROOT/"data"
OOS="2023-01-01"
def neff(x,ml=12):
    n=len(x)
    if n<4:return float(n)
    e=x-x.mean();v=(e@e)/n
    if v<=0:return float(n)
    s=0
    for k in range(1,min(ml,n-1)+1):
        rk=(e[k:]@e[:-k])/n/v
        if rk<=0:break
        s+=(1-k/(ml+1))*rk
    return float(n/(1+2*s))
def wcp(x,B=2000,seed=42):
    n=len(x)
    if n<4:return np.nan
    rng=np.random.default_rng(seed);sd=x.std(ddof=1)
    t=abs(x.mean()/(sd/np.sqrt(n))) if sd>0 else 0;e=x-x.mean();c=0
    for _ in range(B):
        w=rng.choice([-1.,1.],size=n);xn=w*e;sb=xn.std(ddof=1)
        if (abs(xn.mean()/(sb/np.sqrt(n))) if sb>0 else 0)>=t:c+=1
    return (c+1)/(B+1)
def fwd_h(r,h): return r.shift(-1).rolling(h).sum().shift(-(h-1)) if h>1 else r.shift(-1)
def judge(sig,r,h,prior):
    f=fwd_h(r,h);df=pd.concat([sig.rename("s"),f.rename("f")],axis=1).dropna()
    if len(df)<12:return None
    rho=stats.spearmanr(df["s"],df["f"])[0];n=len(df);ne=neff(df["f"].values)
    prod=(stats.rankdata(df["s"])-n/2)*(stats.rankdata(df["f"])-n/2)
    is_d=df[df.index<OOS];oos_d=df[df.index>=OOS]
    ris=stats.spearmanr(is_d["s"],is_d["f"])[0] if len(is_d)>=8 else np.nan
    ros=stats.spearmanr(oos_d["s"],oos_d["f"])[0] if len(oos_d)>=8 else np.nan
    sh=not np.isnan(ris) and not np.isnan(ros) and np.sign(ris)==np.sign(ros)
    mh=sh and abs(ros)>=abs(ris)*0.5
    pm=np.sign(rho)==(1 if prior=="양" else -1)
    return dict(rho=round(float(rho),4),wc_p=round(float(wcp(prod)),4),t_power=round(abs(rho)*np.sqrt(ne),2),
                ris=round(float(ris),3) if not np.isnan(ris) else None,ros=round(float(ros),3) if not np.isnan(ros) else None,
                oos=("OOS+mag유지" if mh else("OOS부호유지 mag약" if sh else "OOS flip")),prior_match=bool(pm),n=n)

px=pd.read_parquet(CHEM/"raw-v3"/"data"/"prices.parquet");px.index=pd.to_datetime(px.index)
pxm=px.resample("ME").last();ind=pxm.pct_change().mean(axis=1).dropna()
# 공통인자 = 외국인flow proxy 부재 → 시장(KOSPI proxy=전종목 평균) + USDKRW로 residualize
cyc=pd.read_parquet(DATA/"chem_rotation_cycle.parquet");cyc.index=pd.to_datetime(cyc.index);cm=cyc.resample("ME").last()
ext=pd.read_parquet(DATA/"chem_rotation_ext.parquet");ext.index=pd.to_datetime(ext.index);em=ext.resample("ME").last()
z=lambda s:(s-s.mean())/s.std();yoy=lambda s:s/s.shift(12)-1
# mom_3 산업 자체
mom3=z(pxm.pct_change(3).mean(axis=1))
# ★residualize mom_3 on 시장 momentum (공통인자) — 시장 = 전체 화학 외 proxy 부재 → USDKRW+brent(공통 macro)
usdkrw_m=z(em["usdkrw"].pct_change(3)); brent_m=z(em["brent"].pct_change(3))
common=pd.concat([usdkrw_m.rename("u"),brent_m.rename("b")],axis=1)
def residualize(sig,ctrl):
    df=pd.concat([sig.rename("y"),ctrl],axis=1).dropna()
    X=np.column_stack([np.ones(len(df))]+[df[c].values for c in ctrl.columns]);y=df["y"].values
    b=np.linalg.lstsq(X,y,rcond=None)[0];res=y-X@b
    return pd.Series(res,index=df.index)
mom3_resid=residualize(mom3,common)
# pbr_z valband (from _rotation valband: 화학 pbr 업종 z) — 업종 pbr 재구성
fin=pd.read_parquet(CHEM/"raw-v3"/"data"/"dart_financials.parquet")
import FinanceDataReader as fdr
uni=pd.read_parquet(CHEM/"raw-v3"/"data"/"universe.parquet");uni=uni[uni["pass_floor"]]
lst=pd.concat([fdr.StockListing("KOSPI")[["Code","Close","Marcap"]],fdr.StockListing("KOSDAQ")[["Code","Close","Marcap"]]])
lst=lst[lst["Code"].isin(uni["Code"])].copy();lst["sh"]=lst["Marcap"]/lst["Close"];sh=dict(zip(lst["Code"],lst["sh"]))
fin=fin.copy();fin["rc"]=pd.to_datetime(fin["rcept_dt"],format="%Y%m%d",errors="coerce");fin=fin.dropna(subset=["rc"])
# 업종 aggregate PBR = sum(mktcap)/sum(equity) 월별
pbr_agg=pd.Series(index=pxm.index,dtype=float)
for dt in pxm.index:
    mc=0;eq=0
    for c in px.columns:
        if c not in sh:continue
        av=fin[(fin["code"]==c)&(fin["rc"]<=dt)]
        if len(av)==0 or pd.isna(pxm.loc[dt,c]):continue
        e=av["equity"].iloc[-1]
        if e and e>0: mc+=pxm.loc[dt,c]*sh[c]; eq+=e
    if eq>0: pbr_agg[dt]=mc/eq
pbr_z=(pbr_agg-pbr_agg.rolling(24,min_periods=12).mean())/pbr_agg.rolling(24,min_periods=12).std()

cand={
 "mom_3_raw":(mom3,"양","산업 momentum (v1 +0.359, 공통인자 재포장 의심)"),
 "mom_3_residualized":(mom3_resid,"양","mom_3 - 공통macro(usdkrw+brent) 직교 → 잔존하면 고유"),
 "pbr_z_valband":(pbr_z,"양","업종 PBR z (밸류밴드 추세, v1 valband +0.448)"),
 "naphtha_yoy_cost":(yoy(cm["wti_naphtha"]),"음","원가 채널 (demand와 직교 = 독립 보조 후보)"),
 "china_mchi_demand":(yoy(cm["china_mchi"]),"양","수요 채널 단독"),
}
out={}
print(f"{'signal':<24}{'h':>4}{'rho':>8}{'match':>6}{'wc_p':>8}{'t_pwr':>6}{'OOS':>16}")
for sn,(sig,pr,desc) in cand.items():
    for h,hn in [(1,"y20"),(3,"y60")]:
        r=judge(sig.dropna(),ind,h,pr)
        if r is None: continue
        out[f"{sn}__{hn}"]={**r,"prior":pr,"desc":desc}
        if hn=="y60":
            print(f"{sn:<24}{hn:>4}{r['rho']:>+8.3f}{('Y' if r['prior_match'] else 'N'):>6}{r['wc_p']:>8.3f}{r['t_power']:>6.2f}  {r['oos']:<14}")
# 직교성 점검: naphtha(cost) vs china(demand) vs spread corr
print("\n=== 채택 후보 직교성 (월 신호 corr) ===")
sigs_chk={"spread(china-brent)":z(yoy(cm["china_mchi"]))-z(yoy(em["brent"])),
          "china_mchi":yoy(cm["china_mchi"]),"naphtha_cost":yoy(cm["wti_naphtha"]),"pbr_z":pbr_z,"mom3_resid":mom3_resid}
sdf=pd.concat({k:v for k,v in sigs_chk.items()},axis=1).dropna()
print(sdf.corr().round(2).to_string())
(ROOT/"validation-chem-rotation-aux-v1.json").write_text(json.dumps(out,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
