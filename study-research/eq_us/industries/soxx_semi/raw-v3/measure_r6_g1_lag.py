#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SOXX R6 G1 — lag 감사 (최우선). y_60d 59일 겹침 → block=20 과소보정 의심.
(a) non-overlap(60거래일 간격) IC mean+t 재계산
(b) block=60 재보정 (bootci + wcp)
(c) t>2 생존 판정
★브리핑 "t=3.24"는 R4 nw_tstat(lag=20, y_20d). y_60d NW-HAC lag=60 t=2.73. 본 G1 = y_60d non-overlap 엄밀 재검.
재현: us_cyclical/raw-v3/data.
"""
import pandas as pd, numpy as np, json, sys
from scipy import stats
np.random.seed(20260608)
DATA="../../us_cyclical/raw-v3/data"
SEMI=['NVDA','AVGO','AMD','QCOM','TXN','MU','ADI','LRCX','KLAC','AMAT','INTC','MCHP']
px=pd.read_parquet(f"{DATA}/prices.parquet")[SEMI]
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

def daily_ic(sig,f):
    out=[];idx=[]
    for d in sig.index:
        if d not in f.index:continue
        df=pd.DataFrame({'s':sig.loc[d],'r':f.loc[d]}).dropna()
        if len(df)<4:continue
        c=stats.spearmanr(df.s,df.r).correlation
        if not np.isnan(c):out.append(c);idx.append(d)
    return pd.Series(out,index=idx)
def bootci(ic,block,B=3000):
    a=ic.values;n=len(a)
    if n<block+1:return [np.nan,np.nan]
    nb=int(np.ceil(n/block));ms=[]
    for _ in range(B):
        st=np.random.randint(0,n-block+1,nb);ms.append(np.concatenate([a[s:s+block] for s in st])[:n].mean())
    return list(np.round(np.percentile(ms,[2.5,97.5]),4))
def wcp(ic,block,B=3000):
    a=ic.values;n=len(a)
    if n<block+1:return np.nan
    o=a.mean();dm=a-o;nb=int(np.ceil(n/block));c=0
    for _ in range(B):
        w=np.repeat(np.random.choice([-1,1],nb),block)[:n]
        if abs((dm*w).mean())>=abs(o):c+=1
    return round(c/B,4)

results={'meta':{'gate':'G1 lag 감사','horizon':'y_60d (59거래일 겹침)',
  'brief_t324_source':'★브리핑 t=3.24 = R4 nw_tstat(lag=20, y_20d). y_60d = NW-HAC lag=60 t=2.73 (별도)',
  'block20_issue':'★R3 conditional bootci/wcp block=20 < 60겹침 = 과소보정(CI 좁고 wc_p 낙관). G1 = block=60 재보정'}}

for h in [20,60]:
    fwd=px.pct_change(h).shift(-h)
    ic=daily_ic(value,fwd)
    # (a) non-overlap (h거래일 간격)
    no=ic.iloc[::h]
    m_no=no.mean();se_no=no.std(ddof=1)/np.sqrt(len(no));t_no=m_no/se_no if se_no>0 else np.nan
    p_no=2*(1-stats.t.cdf(abs(t_no),df=len(no)-1)) if len(no)>1 else np.nan
    # (b) block=h 재보정 (full daily IC, block=horizon)
    ci_b20=bootci(ic,20);ci_bh=bootci(ic,h)
    wcp_b20=wcp(ic,20);wcp_bh=wcp(ic,h)
    # NW-HAC lag=h
    a=ic.values;n=len(a);mm=a.mean();dm=a-mm;g0=np.dot(dm,dm)/n;s=g0
    for k in range(1,h+1):
        if k>=n:break
        gk=np.dot(dm[:-k],dm[k:])/n;w=1-k/(h+1);s+=2*w*gk
    nw_se=np.sqrt(s/n);nw_t=mm/nw_se if nw_se>0 else np.nan
    results[f'y_{h}d']={
      'daily_ic_mean':round(mm,4),'daily_n':n,
      'non_overlap':{'n':len(no),'ic':round(m_no,4),'t':round(t_no,2),'p':round(p_no,4),
                     'survive_t2':bool(abs(t_no)>2)},
      'block_recalib':{'block20_ci':ci_b20,'block20_wcp':wcp_b20,
                       f'block{h}_ci':ci_bh,f'block{h}_wcp':wcp_bh,
                       'wcp_inflation':f'block20={wcp_b20} → block{h}={wcp_bh}',
                       f'block{h}_ci_crosses0':bool(ci_bh[0]<=0<=ci_bh[1])},
      'nw_hac':{'lag':h,'nw_t':round(nw_t,2)}}

# ★G1 판정 (y_60d primary, non-overlap t)
y60=results['y_60d']
g1_pass = y60['non_overlap']['survive_t2'] and not y60['block_recalib']['block60_ci_crosses0']
results['G1_verdict']={
  'value_y60_nonoverlap_t':y60['non_overlap']['t'],
  'value_y60_block60_ci':y60['block_recalib']['block60_ci'],
  'value_y60_block60_wcp':y60['block_recalib']['block60_wcp'],
  'PASS':bool(g1_pass),
  'interpretation':('G1 PASS: non-overlap t>2 + block60 CI 0배제 = lag artifact 아님, G2 진행' if g1_pass
    else 'G1 보류/약: non-overlap t 또는 block60 CI 0포함 = t artifact 의심. 단 fragile=코드화 보류, breadth(G2) 필요')}
with open('validation-r6-g1.json','w',encoding='utf-8') as f:
    json.dump(results,f,indent=2,ensure_ascii=False,default=str)
sys.stderr.write("[saved] validation-r6-g1.json\n")
