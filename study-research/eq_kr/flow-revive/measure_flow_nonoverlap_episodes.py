import pandas as pd, numpy as np
from scipy import stats
mkt = pd.read_parquet('/tmp/kr_mkt_ret.parquet')['mkt_ret']
rs = pd.read_parquet('study-research/eq_kr/industries/financial/raw-v3/data/regime_series.parquet')
rs.index=pd.to_datetime(rs.index)
df=pd.DataFrame({'mkt':mkt}).join(rs[['foreign_net_kospi']],how='left')
df['foreign_net_kospi']=df['foreign_net_kospi'].fillna(0.0)
df=df.dropna(subset=['mkt'])
logr=np.log1p(df['mkt'])
df['fn60']=df['foreign_net_kospi'].rolling(60).sum()
# NON-overlapping monthly: signal = fn60 at month-end, fwd = next month return
me=pd.DataFrame()
me['fn60']=df['fn60'].resample('ME').last()
me['ret']=logr.resample('ME').sum()
me['fwd1']=me['ret'].shift(-1)
# bottom-quintile (capitulation) months vs rest, NON-overlapping
thr=me['fn60'].quantile(0.2)
cap=me[me['fn60']<=thr]
rest=me[me['fn60']>thr]
t,p=stats.ttest_ind(cap['fwd1'].dropna(),rest['fwd1'].dropna(),equal_var=False)
print('NON-overlapping monthly: capitulation(bottom 20%% fn60) vs rest, fwd1M')
print('  cap mean=%.4f (n=%d) rest mean=%.4f (n=%d)  t=%.2f p=%.3f'%(
    cap['fwd1'].mean(),cap['fwd1'].notna().sum(),rest['fwd1'].mean(),rest['fwd1'].notna().sum(),t,p))
# episode clustering: which months are capitulation?
capmonths=cap.index.to_period('M').astype(str).tolist()
print('  capitulation months (%d):'%len(capmonths), capmonths)
# distinct episodes = consecutive runs
yrs=sorted(set(m[:4] for m in capmonths))
print('  distinct YEARS with capitulation:', yrs)
