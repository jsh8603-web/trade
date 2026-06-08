import pandas as pd, numpy as np
from scipy import stats
mkt = pd.read_parquet('/tmp/kr_mkt_ret.parquet')['mkt_ret']
rs = pd.read_parquet('study-research/eq_kr/industries/financial/raw-v3/data/regime_series.parquet')
rs.index = pd.to_datetime(rs.index)
df = pd.DataFrame({'mkt':mkt}).join(rs[['foreign_net_kospi','usdkrw']],how='left')
df['foreign_net_kospi']=df['foreign_net_kospi'].fillna(0.0)
df['usdkrw']=df['usdkrw'].ffill()
df=df.dropna(subset=['mkt'])
logr=np.log1p(df['mkt'])

# ---- Monthly non-overlapping ----
mdf=pd.DataFrame()
mdf['ret']=logr.resample('ME').sum()
mdf['fn_m']=df['foreign_net_kospi'].resample('ME').sum()      # monthly net flow
mdf['fn_cum3']=mdf['fn_m'].rolling(3).sum()                   # 3M cumulative flow (signal at month end)
mdf['won_str']=-df['usdkrw'].resample('ME').last().pct_change()  # KRW strength this month
mdf['fwd1']=mdf['ret'].shift(-1)
def ic(a,b):
    m=~(a.isna()|b.isna())
    if m.sum()<24: return (np.nan,np.nan,m.sum())
    r,p=stats.spearmanr(a[m],b[m]); return (r,p,m.sum())
print('=== Monthly NON-overlapping: signal_t -> fwd 1M return ===')
for s in ['fn_m','fn_cum3','won_str']:
    r,p,n=ic(mdf[s],mdf['fwd1']); print('  %-10s IC=%+.3f p=%.3f n=%d'%(s,r,p,n))

# ---- Extreme-flow STATE conditional (contrarian capitulation) ----
print()
print('=== State-conditional fwd 21d return by foreign-flow 60d-sum quintile ===')
df['fn60']=df['foreign_net_kospi'].rolling(60).sum()
df['fwd21']=logr[::-1].rolling(21).sum()[::-1].shift(-1)
q=pd.qcut(df['fn60'],5,labels=['Q1 heavy SELL','Q2','Q3','Q4','Q5 heavy BUY'])
g=df.groupby(q,observed=True)['fwd21'].agg(['mean','median','count'])
g['ann%']=(np.exp(g['mean']*12)-1)*100
print(g.round(4))
# Long-short Q1(sell) minus Q5(buy) since contrarian
q1=df.loc[q=='Q1 heavy SELL','fwd21'].dropna(); q5=df.loc[q=='Q5 heavy BUY','fwd21'].dropna()
t,p=stats.ttest_ind(q1,q5,equal_var=False)
print('  Q1(capitulation) vs Q5(crowded buy) fwd21: t=%.2f p=%.3f  (contrarian if Q1>Q5)'%(t,p))

# ---- Won strength state ----
print()
print('=== fwd 21d by KRW 20d-strength quintile (won 강세 = risk-on proxy) ===')
df['won20']=-df['usdkrw'].pct_change(20)
q2=pd.qcut(df['won20'].rank(method='first'),5,labels=['Q1 won weak','Q2','Q3','Q4','Q5 won strong'])
g2=df.groupby(q2,observed=True)['fwd21'].agg(['mean','count'])
g2['ann%']=(np.exp(g2['mean']*12)-1)*100
print(g2.round(4))
