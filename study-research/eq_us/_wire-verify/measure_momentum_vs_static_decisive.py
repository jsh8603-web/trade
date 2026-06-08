import pandas as pd, numpy as np
paths={'semi':'soxx_semi/raw-v3/xsd_prices_small.parquet','fin':'xlf_financials/raw-v3/xlf_prices.parquet',
       'ind':'xli_industrials/raw-v3/xli_prices.parquet','def':'us_defensive/raw-v3/data/prices.parquet',
       'meg':'us_mega_tech/raw-v3/data/prices.parquet'}
sl={}
for k,p in paths.items():
    px=pd.read_parquet(f'study-research/eq_us/industries/{p}'); px.index=pd.to_datetime(px.index)
    r=px.pct_change(); sl[k]=r[r.notna().sum(axis=1)>=3].mean(axis=1)
Rm=(1+pd.DataFrame(sl).dropna()).resample('ME').prod()-1; Rm=Rm.loc['2015-06-30':]
def ann(x):return (1+x).prod()**(12/len(x))-1
def sh(x):return x.mean()/x.std()*np.sqrt(12)
EW=Rm.mean(axis=1)
# OW-top mom3M with cost + which sleeve picked
mom=pd.DataFrame({c:(1+Rm[c]).rolling(3).apply(np.prod,raw=True)-1 for c in Rm.columns})
w=pd.DataFrame(0.1,index=Rm.index,columns=Rm.columns); picks=[]
for t in Rm.index:
    s=mom.loc[t].dropna()
    if len(s)<4: picks.append(None); continue
    w.loc[t,s.idxmax()]=0.6; picks.append(s.idxmax())
w=w.div(w.sum(axis=1),axis=0)
p=(w.shift(1)*Rm).sum(axis=1).dropna()
to=w.diff().abs().sum(axis=1).shift(1).reindex(p.index).fillna(0)
net=p-to*0.0010
print('OW-top mom3M: gross ann %+.1f%% / NET ann %+.1f%% Sharpe %.2f (turnover/mo %.2f)'%(ann(p)*100,ann(net)*100,sh(net),to.mean()))
print('EW: ann %+.1f%% Sharpe %.2f'%(ann(EW)*100,sh(EW)))
# static benchmarks
for c in Rm.columns:
    st=0.6*Rm[c]+0.1*Rm.drop(columns=c).sum(axis=1)
    print('  static OW %-4s ann=%+.1f%% Sharpe=%.2f'%(c,ann(st)*100,sh(st)))
# pick distribution
pk=pd.Series([x for x in picks if x],index=[t for t,x in zip(Rm.index,picks) if x])
print('pick counts:',pk.value_counts().to_dict())
print('pick by year:')
for yr,g in pk.groupby(pk.index.year): print('  %d: %s'%(yr,g.value_counts().to_dict()))
# does momentum-rotation beat the BEST static single sleeve?
best_static=max([(sh(0.6*Rm[c]+0.1*Rm.drop(columns=c).sum(axis=1)),c) for c in Rm.columns])
print('best static OW =',best_static[1],'Sharpe %.2f'%best_static[0],'| mom-rot NET Sharpe %.2f'%sh(net))
