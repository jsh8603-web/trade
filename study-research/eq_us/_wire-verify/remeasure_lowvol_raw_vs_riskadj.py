import pandas as pd, numpy as np
from scipy import stats
def load(sec):
    px=pd.read_parquet(f'study-research/eq_us/industries/{sec}/raw-v3/data/prices.parquet'); px.index=pd.to_datetime(px.index)
    return px
def measure(sec):
    px=load(sec); lp=np.log(px); ret=px.pct_change()
    mkt=ret.mean(axis=1)
    vol60=ret.rolling(60).std()*np.sqrt(252)
    # rolling CAPM beta (252d)
    asof=px.resample('ME').last().index
    asof=asof[(asof>=pd.Timestamp('2016-01-01'))&(asof<=pd.Timestamp('2024-12-31'))]
    rawIC=[]; riskIC=[]; lo=[]; hi=[]
    for a in asof:
        idx=px.index[px.index<=a]
        if len(idx)<260: continue
        a2=idx[-1]
        v=vol60.loc[a2].dropna()
        # forward 12M raw return + forward realized vol
        fut=px.loc[a2:a2+pd.Timedelta(days=380)]; fut=fut[fut.index>a2]
        if len(fut)<200: continue
        fr=fut.iloc[min(251,len(fut)-1)]/px.loc[a2]-1   # fwd raw ret
        fvol=np.log(fut).diff().std()*np.sqrt(252)        # fwd realized vol
        df=pd.DataFrame({'vol':v,'fr':fr,'fvol':fvol}).dropna()
        if len(df)<10: continue
        df['risk_adj']=df['fr']/df['fvol']                # fwd Sharpe-like
        # low-vol signal = -vol ; IC vs raw and vs risk-adj
        rawIC.append(stats.spearmanr(-df['vol'],df['fr'])[0])
        riskIC.append(stats.spearmanr(-df['vol'],df['risk_adj'])[0])
        # quintile: lowest-vol 20% vs highest-vol 20%
        q=pd.qcut(df['vol'],5,labels=False,duplicates='drop')
        lo.append(df['fr'][q==0].mean()); hi.append(df['fr'][q==q.max()].mean())
    rawIC=pd.Series(rawIC).dropna(); riskIC=pd.Series(riskIC).dropna()
    lo=pd.Series(lo); hi=pd.Series(hi)
    print('=== %s (n_months=%d) ==='%(sec,len(rawIC)))
    print('  low-vol signal IC vs RAW fwd return    = %+.3f (t=%.2f)'%(rawIC.mean(),rawIC.mean()/(rawIC.std()/np.sqrt(len(rawIC)))))
    print('  low-vol signal IC vs RISK-ADJ (fwd Sh) = %+.3f (t=%.2f)'%(riskIC.mean(),riskIC.mean()/(riskIC.std()/np.sqrt(len(riskIC)))))
    print('  low-vol Q raw ret %+.1f%%/yr vs high-vol Q %+.1f%%/yr  (lowvol-highvol Sharpe of spread=%.2f)'%(
        lo.mean()*100,hi.mean()*100,(lo-hi).mean()/(lo-hi).std()*np.sqrt(1)))
    # risk-adjusted quintile (Sharpe per name): need fwd vol per quintile
    return rawIC,riskIC
for sec in ['us_cyclical','us_defensive','us_mega_tech']:
    measure(sec)
