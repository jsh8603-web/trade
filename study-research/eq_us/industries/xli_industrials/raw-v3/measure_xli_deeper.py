#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XLI FCF-yield trace deeper — 4관문 (전부 통과해야 codifiable). 미국 유일 selection 신호 확정/기각.
1. sub-sector-neutralize FCF-yield (sub-sector 내 demean 후 IC) — 부호상쇄 제거 후 생존?
2. FCF-yield 단독 leave-top2(CAT·GE) retention (결합 아닌 fcfy 단독)
3. machinery 집중 점검 (machinery 제외 후 / machinery-only)
4. BY-FDR(보수) + 생존편향 upper-bound
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
def fcfy_raw(cols):
    sh=pit('shares',cols);ocf=pit('op_cashflow',cols);capex=pit('capex',cols)
    mc=px[cols]*sh;fcf=ocf-capex.abs()
    return (fcf/mc).where(mc>0)
def xs_z(df,sign=1):return df.sub(df.mean(axis=1),axis=0).div(df.std(axis=1),axis=0)*sign
def subsec_neutral_z(fcfy,cols):
    """sub-sector 내 demean 후 z (부호상쇄 제거)."""
    out=fcfy.copy()*np.nan
    for m in fcfy.index:
        row=fcfy.loc[m]
        for ss in set(SUBSEC.get(c) for c in cols):
            scols=[c for c in cols if SUBSEC.get(c)==ss]
            if len(scols)>=2:
                out.loc[m,scols]=row[scols]-row[scols].mean()
    return xs_z(out,1)
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

results={'meta':{'target':'XLI FCF-yield trace — codifiable 4관문','signal':'FCF-yield (op_cashflow-capex)/mcap',
  'survivor_upper_bound':'현-holdings-only = 부진 편출 누락 = FCF-yield IC upward bias upper-bound'}}

# ── ★관문1: sub-sector-neutralize FCF-yield IC ──
snz=subsec_neutral_z(fcfy_raw(XLI),XLI)
g1={}
for h in [20,60]:
    fwd=px.pct_change(h).shift(-h);ic=daily_ic(snz,fwd);m,t,p,n=non_t(ic,h)
    g1[f'y_{h}d']={'ic':round(ic.mean(),4),'nonoverlap_t':t,'p':p,'n':n,'ci':bootci(ic,h),'survive_t2':bool(abs(t)>2)}
results['gate1_subsector_neutral']=g1

# ── ★관문2: FCF-yield 단독 leave-top2 (CAT·GE) ──
g2={}
for h in [20,60]:
    fwd=px.pct_change(h).shift(-h)
    ic_full=daily_ic(xs_z(fcfy_raw(XLI),1),fwd[XLI]).mean()
    others=[t for t in XLI if t not in ['CAT','GE']]
    ic_lo2=daily_ic(xs_z(fcfy_raw(others),1),fwd[others]).mean()
    ret=ic_lo2/ic_full if ic_full!=0 else np.nan
    _,t_lo2,p_lo2,_=non_t(daily_ic(xs_z(fcfy_raw(others),1),fwd[others]),h)
    g2[f'y_{h}d']={'ic_full':round(ic_full,4),'ic_lo2':round(ic_lo2,4),'retention':round(ret,3),'t_lo2':t_lo2,'p_lo2':p_lo2}
results['gate2_fcfy_leave_top2']=g2

# ── ★관문3: machinery 집중 점검 ──
mach=[t for t in XLI if SUBSEC.get(t)=='machinery']
non_mach=[t for t in XLI if SUBSEC.get(t)!='machinery']
g3={}
for h in [60]:
    fwd=px.pct_change(h).shift(-h)
    ic_all=daily_ic(xs_z(fcfy_raw(XLI),1),fwd[XLI]).mean()
    ic_nomach=daily_ic(xs_z(fcfy_raw(non_mach),1),fwd[non_mach])
    m_nm,t_nm,p_nm,_=non_t(ic_nomach,h)
    ic_machonly=daily_ic(xs_z(fcfy_raw(mach),1),fwd[mach])
    m_mo,t_mo,p_mo,_=non_t(ic_machonly,h)
    g3[f'y_{h}d']={'ic_all':round(ic_all,4),'ic_no_machinery':round(m_nm,4),'t_no_machinery':t_nm,
      'ic_machinery_only':round(m_mo,4),'t_machinery_only':t_mo,
      'machinery_only_artifact':bool(abs(t_nm)<2 and abs(t_mo)>=2)}
results['gate3_machinery']=g3

# ── ★관문4: BY-FDR + 생존편향 ──
# fcfy 검정 family: sub-sector-neutral y20/y60 + raw y20/y60 + leave-top2 y20/y60 = 6 검정
pvals=[g1['y_20d']['p'],g1['y_60d']['p'],g2['y_20d']['p_lo2'],g2['y_60d']['p_lo2']]
# raw fcfy p (from validation-xli)
for h in [20,60]:
    fwd=px.pct_change(h).shift(-h);ic=daily_ic(xs_z(fcfy_raw(XLI),1),fwd[XLI]);_,_,p,_=non_t(ic,h);pvals.append(p)
m=len(pvals);cm=sum(1/i for i in range(1,m+1));q=0.10
praw=np.array(sorted(pvals));by_surv=[]
for rank,p in enumerate(praw,1):
    if p<=(rank/m)*q/cm: by_surv.append(round(p,4))
results['gate4_byfdr']={'m':m,'c_m':round(cm,2),'pvals':[round(p,4) for p in pvals],'by_survivors':by_surv,'n_survive':len(by_surv)}

# ── ★판정 (4관문) ──
g1_pass=g1['y_60d']['survive_t2'] or g1['y_20d']['survive_t2']
g2_pass=g2['y_60d']['retention']>=0.5
g3_pass=not g3['y_60d']['machinery_only_artifact']
g4_pass=len(by_surv)>=1
allpass=g1_pass and g2_pass and g3_pass and g4_pass
results['VERDICT']={
  'gate1_subsector_neutral_pass':bool(g1_pass),'gate1_t':[g1['y_20d']['nonoverlap_t'],g1['y_60d']['nonoverlap_t']],
  'gate2_fcfy_leave_top2_pass':bool(g2_pass),'gate2_retention':g2['y_60d']['retention'],
  'gate3_not_machinery_only':bool(g3_pass),
  'gate4_byfdr_pass':bool(g4_pass),
  'ALL_PASS':bool(allpass),
  'interpretation':('★★미국 유일 selection 신호 = XLI sub-sector-neutral FCF-yield 코드화' if allpass else
    '★XLI FCF-yield = artifact → PASSIVE 확정 = 미국 GICS selection 무료데이터 전 섹터 early-stop. null result')}
with open('validation-xli-deeper.json','w',encoding='utf-8') as f:
    json.dump(results,f,indent=2,ensure_ascii=False,default=str)
sys.stderr.write("[saved] validation-xli-deeper.json\n")
