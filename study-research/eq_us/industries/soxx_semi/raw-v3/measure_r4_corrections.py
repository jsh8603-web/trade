#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SOXX R4 보정 — tier 확정. team-lead 지시 4 보정 중 3개(현 데이터 가능):
1. ★FDR BY 보정: 45셀 + family-2. M_eff(신호 상관) + Benjamini-Yekutieli (의존성 보정).
2. ★y_60d overlapping 자기상관 보정: Newey-West HAC(lag=60) + eff_N 겹침배수(/60) → family-2 t 재계산.
3. ★AI capex episode 교란: pre-AI sub-sample(2015-2022)에서 value rate-extreme conditional 재현되나?
   (#3 DFII10 재fetch = sandbox 네트워크 timeout → data-gate, nominal 유지 + 라벨 정직)

재현: us_cyclical/raw-v3/data/{prices,edgar_fundamentals,macro}.parquet.
"""
import pandas as pd, numpy as np, json, sys
from scipy import stats
np.random.seed(20260608)
DATA="../../us_cyclical/raw-v3/data"
SEMI=['NVDA','AVGO','AMD','QCOM','TXN','MU','ADI','LRCX','KLAC','AMAT','INTC','MCHP']

px=pd.read_parquet(f"{DATA}/prices.parquet")[SEMI]
fwd={h:px.pct_change(h).shift(-h) for h in [5,20,60]}
edg=pd.read_parquet(f"{DATA}/edgar_fundamentals.parquet");edg=edg[edg.ticker.isin(SEMI)].copy()
edg['filed']=pd.to_datetime(edg['filed']);edg=edg.sort_values('filed').drop_duplicates(['ticker','concept','end'],keep='first')
def pit(c):
    d=edg[edg.concept==c];out={}
    for tk in SEMI:
        dt=d[d.ticker==tk].sort_values('filed')
        if dt.empty:out[tk]=pd.Series(np.nan,index=px.index);continue
        s=pd.Series(dt.val.values,index=dt.filed.values);s=s[~s.index.duplicated(keep='last')].sort_index()
        out[tk]=s.reindex(s.index.union(px.index)).ffill().reindex(px.index)
    return pd.DataFrame(out)
equity=pit('equity');shares=pit('shares');op=pit('op_income');ltd=pit('lt_debt');std=pit('st_debt');cash=pit('cash');da=pit('dep_amort')
mcap=px*shares;debt=ltd.fillna(0)+std.fillna(0)
def xs_z(df,sign=1):return df.sub(df.mean(axis=1),axis=0).div(df.std(axis=1),axis=0)*sign
pbr=(mcap/equity).where(equity>0)
evb=((mcap+debt-cash.fillna(0))/(op+da.fillna(0))).where((op+da.fillna(0))>0)
value=pd.concat([xs_z(pbr,-1),xs_z(evb,-1)]).groupby(level=0).mean()
quality=xs_z(op/(equity+debt),1)
mom=xs_z(px.shift(20)/px.shift(252)-1,1)
rev=xs_z(px.shift(1)/px.shift(20)-1,-1)
lowvol=xs_z(px.pct_change().rolling(60).std(),-1)
SIGS={'value':value,'quality':quality,'mom_12_1':mom,'rev_1m':rev,'low_vol':lowvol}
mac=pd.read_parquet(f"{DATA}/macro.parquet")
rate=mac['rate10y'].reindex(px.index).ffill();credit=mac['baa_aaa'].reindex(px.index).ffill()
def terc(s):
    q=s.quantile([1/3,2/3]);return pd.cut(s,[-np.inf,q.iloc[0],q.iloc[1],np.inf],labels=['low','mid','high'])
rate_r=terc(rate);credit_r=terc(credit)

def daily_ic_series(sig,f,mask=None):
    ics=[];idx=sig.index if mask is None else sig.index[mask.reindex(sig.index,fill_value=False)]
    for d in idx:
        if d not in f.index:continue
        df=pd.DataFrame({'s':sig.loc[d],'r':f.loc[d]}).dropna()
        if len(df)<4:continue
        c=stats.spearmanr(df.s,df.r).correlation
        if not np.isnan(c):ics.append(c)
    return np.array(ics)

# ── 1. ★overlapping 보정: Newey-West HAC t (lag=horizon) ──
def nw_tstat(ic, lag):
    """mean IC t-stat with Newey-West HAC SE (overlapping return 자기상관 보정)."""
    n=len(ic);m=ic.mean();dm=ic-m
    g0=np.dot(dm,dm)/n
    s=g0
    for k in range(1,lag+1):
        if k>=n:break
        gk=np.dot(dm[:-k],dm[k:])/n
        w=1-k/(lag+1)  # Bartlett
        s+=2*w*gk
    se=np.sqrt(s/n)
    return m, se, (m/se if se>0 else np.nan), n, n/lag  # eff_N ≈ n/lag (겹침배수)

results={'meta':{'note':'R4 보정: FDR BY + overlapping NW-HAC + AI episode. DFII10 재fetch=sandbox timeout→data-gate',
    'rate_label':'★nominal 10y(NOT DFII10 실질, fetch timeout). regime=nominal 금리 국면'}}

# overlapping 보정 적용: unconditional 핵심 셀 (value/low_vol y_60d, y_20d)
results['overlapping_corrected']={}
for sn in ['value','low_vol','quality','mom_12_1','rev_1m']:
    results['overlapping_corrected'][sn]={}
    for h in [20,60]:
        ic=daily_ic_series(SIGS[sn],fwd[h])
        m,se,t,n,en=nw_tstat(ic,lag=h)
        results['overlapping_corrected'][sn][f'y_{h}d']={'ic':round(m,4),'nw_se':round(se,4),'nw_t':round(t,2),
            'n_days':n,'eff_n_overlap':round(en,1),'sig_nw':'유의' if abs(t)>2 else '비유의'}

# ── 2. ★family-2 interaction overlapping 보정 (day-cluster 이미 했으나, day-cluster 가 overlap 미흡 → block 60d cluster) ──
def interaction_blockcluster(sig,f,regime_r,hi_label,block=60):
    rows=[]
    for d in sig.index:
        if d not in f.index:continue
        reg=regime_r.loc[d] if d in regime_r.index else np.nan
        if pd.isna(reg):continue
        df=pd.DataFrame({'s':sig.loc[d],'r':f.loc[d]}).dropna()
        if len(df)<4:continue
        df['sr']=df.s.rank(pct=True);df['rr']=df.r.rank(pct=True);df['hi']=1 if reg==hi_label else 0;df['day']=d
        rows.append(df)
    if not rows:return None
    P=pd.concat(rows).reset_index(drop=True)
    X=np.column_stack([np.ones(len(P)),P.sr,P.hi,P.sr*P.hi]);y=P.rr.values
    b=np.linalg.lstsq(X,y,rcond=None)[0];resid=y-X@b
    # block-cluster by 60d block (overlapping 자기상관 흡수)
    days=sorted(P.day.unique());blk={d:i//block for i,d in enumerate(days)}
    P['blk']=P.day.map(blk)
    XtX_inv=np.linalg.inv(X.T@X);meat=np.zeros((4,4))
    for bk,g in P.groupby('blk'):
        idx=g.index.values;Xg=X[idx];rg=resid[idx];sc=Xg.T@rg;meat+=np.outer(sc,sc)
    V=XtX_inv@meat@XtX_inv;se=np.sqrt(np.diag(V))
    return {'b_interaction':round(b[3],4),'t_inter_blockcluster':round(b[3]/se[3],2),
            'n_blocks':P.blk.nunique(),'sig':'유의' if abs(b[3]/se[3])>2 else '비유의'}
results['family2_overlap_corrected']={}
for sn,reg,hi in [('value',rate_r,'high'),('mom_12_1',rate_r,'high'),('low_vol',credit_r,'high'),('rev_1m',credit_r,'high')]:
    results['family2_overlap_corrected'][f'{sn}_x_{"rate" if reg is rate_r else "credit"}_high']=interaction_blockcluster(SIGS[sn],fwd[20],reg,hi)

# ── 3. ★FDR BY 보정 (45 conditional 셀 raw p → M_eff + Benjamini-Yekutieli) ──
# raw p 수집: unconditional 15 (5신호×3h) + conditional rate 15 + credit 15 = 45
def wcp(ic,block=20,B=1000):
    n=len(ic)
    if n<block+1:return np.nan
    o=ic.mean();dm=ic-o;nb=int(np.ceil(n/block));c=0
    for _ in range(B):
        w=np.repeat(np.random.choice([-1,1],nb),block)[:n]
        if abs((dm*w).mean())>=abs(o):c+=1
    return c/B
pvals={}
for sn in SIGS:
    for h in [5,20,60]:
        ic=daily_ic_series(SIGS[sn],fwd[h])
        if len(ic)>20: pvals[f'{sn}|uncond|y{h}']=wcp(ic)
for sn in SIGS:
    for rv in ['low','mid','high']:
        ic=daily_ic_series(SIGS[sn],fwd[20],rate_r==rv)
        if len(ic)>20: pvals[f'{sn}|rate_{rv}|y20']=wcp(ic)
for sn in SIGS:
    for cv in ['low','mid','high']:
        ic=daily_ic_series(SIGS[sn],fwd[20],credit_r==cv)
        if len(ic)>20: pvals[f'{sn}|credit_{cv}|y20']=wcp(ic)
keys=list(pvals);praw=np.array([pvals[k] for k in keys]);m=len(praw)
# Benjamini-Yekutieli (의존성): threshold = (i/m) * q / c(m), c(m)=sum(1/i)
q=0.10;cm=sum(1/i for i in range(1,m+1))
order=np.argsort(praw);by_survivors=[]
for rank,idx in enumerate(order,1):
    thr=(rank/m)*q/cm
    if praw[idx]<=thr: by_survivors.append((keys[idx],round(praw[idx],4),round(thr,5)))
results['fdr_by']={'m_total':m,'q':q,'c_m':round(cm,2),'method':'Benjamini-Yekutieli(의존성 보정)',
    'survivors':by_survivors,'n_survivors':len(by_survivors),
    'note':'45셀 raw wild-cluster p → BY-FDR q=0.10. 우연 기대 45×0.05≈2.3. M_eff 미통합(보수적=naive m).'}

# ── 4. ★AI capex episode 교란: pre-AI(2015-2022) vs AI(2023-2026) value rate-extreme 재현 ──
def ic_period_regime(sig,f,regime_r,rv,lo,hi):
    mask=(regime_r==rv)
    if lo is not None: mask&=(sig.index>=lo)
    if hi is not None: mask&=(sig.index<=hi)
    ic=daily_ic_series(sig,f,mask)
    return {'ic':round(ic.mean(),4) if len(ic) else None,'n':len(ic),'wc_p':round(wcp(ic),4) if len(ic)>20 else None}
AI=pd.Timestamp('2023-01-01')
results['ai_episode_check']={}
for rv in ['low','mid','high']:
    results['ai_episode_check'][f'value_rate_{rv}']={
        'preAI_2015_2022':ic_period_regime(value,fwd[20],rate_r,rv,None,pd.Timestamp('2022-12-31')),
        'AI_2023_2026':ic_period_regime(value,fwd[20],rate_r,rv,AI,None)}
# low_vol도 점검
for cv in ['high']:
    results['ai_episode_check'][f'low_vol_credit_{cv}']={
        'preAI_2015_2022':ic_period_regime(lowvol,fwd[20],credit_r,cv,None,pd.Timestamp('2022-12-31')),
        'AI_2023_2026':ic_period_regime(lowvol,fwd[20],credit_r,cv,AI,None)}

with open('validation-r4-corrections.json','w',encoding='utf-8') as f:
    json.dump(results,f,indent=2,ensure_ascii=False,default=str)
sys.stderr.write("[saved] validation-r4-corrections.json\n")
