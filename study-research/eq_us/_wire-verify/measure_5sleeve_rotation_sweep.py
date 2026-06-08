import pandas as pd, numpy as np
from scipy import stats
paths={'semi':'soxx_semi/raw-v3/xsd_prices_small.parquet','fin':'xlf_financials/raw-v3/xlf_prices.parquet',
       'ind':'xli_industrials/raw-v3/xli_prices.parquet','def':'us_defensive/raw-v3/data/prices.parquet',
       'meg':'us_mega_tech/raw-v3/data/prices.parquet'}
sl={}
for k,p in paths.items():
    px=pd.read_parquet(f'study-research/eq_us/industries/{p}'); px.index=pd.to_datetime(px.index)
    r=px.pct_change(); sl[k]=r[r.notna().sum(axis=1)>=3].mean(axis=1)
R=pd.DataFrame(sl).dropna()
Rm=(1+R).resample('ME').prod()-1; Rm=Rm.loc['2015-06-30':]
m=pd.read_parquet('study-research/eq_us/industries/us_defensive/raw-v3/data/macro.parquet'); m.index=pd.to_datetime(m.index)
M=m.resample('ME').last().reindex(Rm.index).ffill()
EW=Rm.mean(axis=1)
def ann(x):return (1+x).prod()**(12/len(x))-1
def sh(x):return x.mean()/x.std()*np.sqrt(12)
def ir(p,b):
    e=(p-b.reindex(p.index)).dropna(); return e.mean()/e.std()*np.sqrt(12) if e.std()>0 else 0
print('=== 5-sleeve rotation sweep (semi/fin/ind/def/meg, 2015-2026, %d mo) ==='%len(Rm))
print('  EW ann=%+.1f%% Sharpe=%.2f'%(ann(EW)*100,sh(EW)))
ewp=(Rm.mean(axis=1))
def tilt_ls(score, lab, k_top=1):
    w=pd.DataFrame(0.0,index=Rm.index,columns=Rm.columns)
    for t in Rm.index:
        s=score.loc[t].dropna()
        if len(s)<4: continue
        w.loc[t,s.nlargest(k_top).index]=1.0/k_top
        w.loc[t,s.nsmallest(k_top).index]=-1.0/k_top
    ls=(w.shift(1)*Rm).sum(axis=1).dropna()
    t_=ls.mean()/(ls.std()/np.sqrt(len(ls)))
    half=ls.index[len(ls)//2]
    isr=ls.loc[ls.index<=half]; oos=ls.loc[ls.index>half]
    print('  L/S %-22s ann=%+.1f%% Sharpe=%.2f t=%.2f | IS ann %+.1f%% OOS ann %+.1f%%'%(
        lab,ann(ls)*100,sh(ls),t_,ann(isr)*100,ann(oos)*100))
def tilt_long(score,lab):
    w=pd.DataFrame(0.1,index=Rm.index,columns=Rm.columns)
    for t in Rm.index:
        s=score.loc[t].dropna()
        if len(s)<4: continue
        w.loc[t,s.idxmax()]=0.6
    w=w.div(w.sum(axis=1),axis=0)
    p=(w.shift(1)*Rm).sum(axis=1).dropna()
    half=p.index[len(p)//2]
    print('  OW-top %-19s ann=%+.1f%% Sharpe=%.2f IRvsEW=%+.2f | IS-IR %+.2f OOS-IR %+.2f'%(
        lab,ann(p)*100,sh(p),ir(p,ewp), ir(p.loc[p.index<=half],ewp), ir(p.loc[p.index>half],ewp)))
# momentum scores
for lb in [3,6,12]:
    mom=pd.DataFrame({c:(1+Rm[c]).rolling(lb).apply(np.prod,raw=True)-1 for c in Rm.columns})
    tilt_ls(mom,f'mom{lb}M'); tilt_long(mom,f'mom{lb}M')
# risk-adj momentum
sh6=pd.DataFrame({c:Rm[c].rolling(6).mean()/Rm[c].rolling(6).std() for c in Rm.columns})
tilt_ls(sh6,'riskadj-mom6M'); tilt_long(sh6,'riskadj-mom6M')
# reversal
rev=pd.DataFrame({c:-(1+Rm[c]).rolling(1).apply(np.prod,raw=True)+1 for c in Rm.columns})
tilt_ls(rev,'1M reversal')
