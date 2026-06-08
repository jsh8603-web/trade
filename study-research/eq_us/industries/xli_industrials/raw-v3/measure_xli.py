#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XLI minimal selection 검증 (마지막 early-stop 체크).
value=EV/EBITDA·FCF-yield / quality=ROIC·gross profitability. leave-top2(CAT·GE) kill 게이트.
non-overlap t primary, block-boot CI. + cyclical-β sub-sector sign-cancel 점검.
재현: xli_prices.parquet + xli_edgar.parquet.
"""
import pandas as pd, numpy as np, json, sys
from scipy import stats
np.random.seed(20260608)
XLI=['GE','CAT','RTX','HON','UNP','BA','LMT','DE','UPS','ETN','ADP','GD','NOC','EMR','ITW','CSX','MMM','FDX','NSC','WM','PH','TT','CTAS','TDG','PCAR','CMI','PWR','RSG','JCI','AME','ROK','FAST','URI','PAYX','VRSK','EFX','DOV','XYL','WAB']
SUBSEC={'RTX':'aero_def','BA':'aero_def','LMT':'aero_def','GD':'aero_def','NOC':'aero_def','TDG':'aero_def',
 'CAT':'machinery','DE':'machinery','CMI':'machinery','PH':'machinery','DOV':'machinery','ROK':'machinery','ETN':'machinery','EMR':'machinery','ITW':'machinery','AME':'machinery','XYL':'machinery','URI':'machinery',
 'UNP':'transport','UPS':'transport','CSX':'transport','NSC':'transport','FDX':'transport','WAB':'transport','PCAR':'transport',
 'ADP':'services','PAYX':'services','VRSK':'services','EFX':'services','RSG':'services','WM':'services','CTAS':'services','FAST':'services','PWR':'services',
 'GE':'multi','HON':'multi','MMM':'multi','TT':'multi','JCI':'multi'}
px=pd.read_parquet("xli_prices.parquet")[XLI]
edg=pd.read_parquet("xli_edgar.parquet")
edg['filed']=pd.to_datetime(edg['filed']);edg['end']=pd.to_datetime(edg['end'])
edg=edg.sort_values('filed').drop_duplicates(['ticker','concept','end'],keep='first')
def pit(c,cols):
    d=edg[edg.concept==c];out={}
    for tk in cols:
        dt=d[d.ticker==tk].sort_values('filed')
        if dt.empty:out[tk]=pd.Series(np.nan,index=px.index);continue
        s=pd.Series(dt.val.values,index=dt.filed.values);s=s[~s.index.duplicated(keep='last')].sort_index()
        out[tk]=s.reindex(s.index.union(px.index)).ffill().reindex(px.index)
    return pd.DataFrame(out)
def signals(cols):
    op=pit('op_income',cols);da=pit('dep_amort',cols);ltd=pit('lt_debt',cols);std=pit('st_debt',cols);cash=pit('cash',cols)
    sh=pit('shares',cols);ocf=pit('op_cashflow',cols);capex=pit('capex',cols);eq=pit('equity',cols);assets=pit('assets',cols);gp=pit('gross_profit',cols)
    mc=px[cols]*sh;debt=ltd.fillna(0)+std.fillna(0)
    ev=mc+debt-cash.fillna(0);ebitda=op+da.fillna(0)
    evb=(ev/ebitda).where(ebitda>0)
    fcf=ocf-capex.abs();fcfy=(fcf/mc).where(mc>0)        # FCF yield
    roic=(op*4/(eq+debt)).where((eq+debt)>0)
    gpa=(gp/assets).where(assets>0)                       # gross profitability
    def z(df,sign):return df.sub(df.mean(axis=1),axis=0).div(df.std(axis=1),axis=0)*sign
    return {'value_evebitda':z(evb,-1),'value_fcfy':z(fcfy,1),'quality_roic':z(roic,1),'quality_gpa':z(gpa,1),
            'value':pd.concat([z(evb,-1),z(fcfy,1)]).groupby(level=0).mean()}
def daily_ic(sig,f):
    out=[];idx=[]
    for d in sig.index:
        if d not in f.index:continue
        df=pd.DataFrame({'s':sig.loc[d],'r':f.loc[d]}).dropna()
        if len(df)<5:continue
        c=stats.spearmanr(df.s,df.r).correlation
        if not np.isnan(c):out.append(c);idx.append(d)
    return pd.Series(out,index=idx)
def non_t(ic,h):
    no=ic.iloc[::h];m=no.mean();se=no.std(ddof=1)/np.sqrt(len(no))
    t=m/se if se>0 else np.nan;p=2*(1-stats.t.cdf(abs(t),df=len(no)-1)) if len(no)>1 else np.nan
    return round(m,4),round(t,2),round(p,4),len(no)
def bootci(ic,block,B=2000):
    a=ic.values;n=len(a)
    if n<block+1:return [np.nan,np.nan]
    nb=int(np.ceil(n/block));ms=[]
    for _ in range(B):
        st=np.random.randint(0,n-block+1,nb);ms.append(np.concatenate([a[s:s+block] for s in st])[:n].mean())
    return list(np.round(np.percentile(ms,[2.5,97.5]),4))

results={'meta':{'universe':f'XLI top-cap {len(XLI)}종(현 holdings, EW, breadth 큼)','factors':'value=EV/EBITDA·FCF-yield / quality=ROIC·gross profitability',
  'survivor_flag':'★XLI survivorship 낮은 편(M&A 적음)이나 명시 — 현-holdings-only = 부진 편출 종목 누락 = value-IC 약 upper-bound'}}
for sn in ['value','value_evebitda','value_fcfy','quality_roic','quality_gpa']:
    sig=signals(XLI)[sn];res={}
    for h in [20,60]:
        fwd=px.pct_change(h).shift(-h);ic=daily_ic(sig,fwd);m,t,p,non=non_t(ic,h)
        res[f'y_{h}d']={'daily_ic':round(ic.mean(),4),'nonoverlap_n':non,'nonoverlap_t':t,'p':p,'block_ci':bootci(ic,h),'survive_t2':bool(abs(t)>2)}
    results[sn]=res
# ★leave-top2 (CAT·GE)
TOP2=['CAT','GE'];others=[t for t in XLI if t not in TOP2]
for h in [20,60]:
    fwd=px.pct_change(h).shift(-h)
    ic_full=daily_ic(signals(XLI)['value'],fwd[XLI]).mean()
    ic_lo2=daily_ic(signals(others)['value'],fwd[others]).mean()
    ret=ic_lo2/ic_full if ic_full!=0 else np.nan
    _,t_lo2,_,_=non_t(daily_ic(signals(others)['value'],fwd[others]),h)
    results[f'leave_top2_y{h}']={'ic_full':round(ic_full,4),'ic_leave_top2':round(ic_lo2,4),'retention':round(ret,3),'nonoverlap_t_lo2':t_lo2,
      'kill_gate':'PASS(≥0.5)' if ret>=0.5 else 'FAIL(<0.5)=position 위장'}
# ★cyclical-β sub-sector sign-cancel 점검 (value IC by sub-sector, y60)
fwd60=px.pct_change(60).shift(-60)
subic={}
for ss in set(SUBSEC.values()):
    cols=[t for t in XLI if SUBSEC.get(t)==ss]
    if len(cols)>=3:
        ic=daily_ic(signals(cols)['value'],fwd60[cols])
        subic[ss]={'n_stocks':len(cols),'value_ic':round(ic.mean(),4)}
results['subsector_sign_check']={'by_subsector':subic,
  'note':'★cyclical-β bleed: sub-sector별 value IC 부호 엇갈리면 sign-cancellation(자문 R3 경고). 부호 일관성 점검'}
# ★판정
v60=results['value']['y_60d'];ret60=results['leave_top2_y60']['retention']
gate=(abs(v60['nonoverlap_t'])>=2) and (ret60>=0.5)
results['VERDICT']={'value_y60_nonoverlap_t':v60['nonoverlap_t'],'leave_top2_retention_y60':ret60,'kill':results['leave_top2_y60']['kill_gate'],
  'PASS':bool(gate),
  'interpretation':('★selection 신호 잠정 존재(retention≥0.5 AND t≥2) → main 보고' if gate else
    '★PASSIVE → XLF+XLI 둘 다 dead = 미국 GICS selection 무료데이터 전 섹터 early-stop 확정. null result')}
with open('validation-xli.json','w',encoding='utf-8') as f:
    json.dump(results,f,indent=2,ensure_ascii=False,default=str)
sys.stderr.write("[saved] validation-xli.json\n")
