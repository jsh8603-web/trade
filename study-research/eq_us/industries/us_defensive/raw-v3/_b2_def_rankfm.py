# -*- coding: utf-8 -*-
"""_b2_def_rankfm.py — ★Rank-based Fama-MacBeth 결정 중재 (team-lead, 2026-06-04).
Gemini over-kill 자문 1순위 권고 + audit "rank-IC robust" 확인 → rank-FM 으로 DEF-2/DEF-1 최종 판정.
매월 횡단면: fwd·z1·z2 를 rank(pct) 변환 → OLS rank(fwd)~r1+r2+(r1-.5)(r2-.5) → 교호계수 시계열 → fixed-b+wild.
outlier-robust(rank) + 연속정보 보존 + FM 다변량. 재현: python _b2_def_rankfm.py
"""
import sys; from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure as M; from _b2_stats import effective_n, fixed_b_cv, wild_cluster_boot, persistence_block
from _breadth_sweep import build_breadth_panels
ROOT=Path(__file__).resolve().parent; DATA=ROOT/"data"; H=12; SPLIT=pd.Timestamp("2022-01-01")
def stest(s):
    s=pd.Series(s).dropna(); n=len(s)
    if n<12: return dict(n=n,note="insuf")
    blk=persistence_block(s.values); eff=effective_n(s.values); mean=float(s.mean())
    x=s.values; e=x-x.mean(); g0=(e@e)/n; var=g0
    for k in range(1,min(blk,n-1)+1): var+=2*(1-k/(blk+1))*(e[k:]@e[:-k])/n
    se=float(np.sqrt(max(var,1e-12)/n)); t=mean/se if se>0 else np.nan; fb=fixed_b_cv(n,blk)
    wc=wild_cluster_boot(pd.Series(x,index=s.index),pd.DataFrame({"const":np.ones(n)},index=s.index),"const",block=blk,B=9999)
    return dict(coef=round(mean,5),n=n,n_eff=eff["n_eff"],t_nw=round(float(t),2) if not np.isnan(t) else None,
        fixed_b_cv=fb["cv_5pct"],fixed_b_sig=bool(not np.isnan(t) and abs(t)>fb["cv_5pct"]),wild_p=wc.get("p_wild_cluster"),sign=int(np.sign(mean)))
def rank_fm(z1,z2,fwd,sub=None,min_n=10):
    idx=z1.index.intersection(z2.index).intersection(fwd.index); coefs=[]
    for dt in idx:
        d=pd.DataFrame({"z1":z1.loc[dt],"z2":z2.loc[dt],"y":fwd.loc[dt]}).dropna()
        if len(d)<min_n: continue
        r1=d.z1.rank(pct=True); r2=d.z2.rank(pct=True); ry=d.y.rank(pct=True)
        ri=(r1-0.5)*(r2-0.5)
        X=sm.add_constant(pd.DataFrame({"r1":r1,"r2":r2,"ri":ri}))
        try: coefs.append((dt,float(sm.OLS(ry,X).fit().params["ri"])))
        except: pass
    return pd.Series([c[1] for c in coefs],index=[c[0] for c in coefs])
def main():
    px,ed,uni,macro=M.load(); secmap=dict(zip(uni["ticker"],uni["subcl"]))
    pxm=px.resample("ME").last(); P=M.build_pit_panels(px,ed)
    amt=pd.read_parquet(DATA/"amount.parquet"); amt.index=pd.to_datetime(amt.index); B=build_breadth_panels(px,ed,amt)
    z=lambda p: M.cs_z(p,secmap)
    ep,div,nis,opp=z(P["ep_yield"]),z(P["dividend_yield"]),z(B["net_issuance"]),z(B["op_profitability"])
    fwd=pxm.shift(-H)/pxm-1; out={"meta":{"method":"rank-based Fama-MacBeth, H=12, B=9999"}}
    for nm,z1,z2,pred in [("DEF-2",div,opp,+1),("DEF-1",nis,ep,+1)]:
        cs=rank_fm(z1,z2,fwd); full=stest(cs)
        ins=stest(cs[cs.index<SPLIT]); oos=stest(cs[cs.index>=SPLIT])
        out[nm]=dict(pred=pred,full=full,in_sample=ins,oos=oos,sign_match=bool(full.get("sign")==pred))
    (ROOT/"_b2_def_rankfm_results.json").write_text(__import__("json").dumps(out,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
    for nm in ["DEF-2","DEF-1"]:
        r=out[nm]; f=r["full"]; i=r["in_sample"]; o=r["oos"]
        print(f"{nm} pred={r['pred']:+d} sign_match={r['sign_match']}")
        print(f"  full   coef={f.get('coef')} t={f.get('t_nw')} fb_sig={f.get('fixed_b_sig')} wildP={f.get('wild_p')} n_eff={f.get('n_eff')}")
        print(f"  in≤21  coef={i.get('coef')} t={i.get('t_nw')} fb_sig={i.get('fixed_b_sig')} | OOS coef={o.get('coef')} t={o.get('t_nw')} fb_sig={o.get('fixed_b_sig')}")
main()
