import pandas as pd, numpy as np, glob, os
from scipy import stats
# Build per-SECTOR daily returns (12 industry folders = WICS sectors)
sec_ret={}
for d in sorted(glob.glob('study-research/eq_kr/industries/*/raw-v3/data/prices.parquet')):
    sec=d.split('/industries/')[1].split('/')[0]
    px=pd.read_parquet(d); px.index=pd.to_datetime(px.index)
    r=px.pct_change()
    sec_ret[sec]=r[r.notna().sum(axis=1)>=3].mean(axis=1)   # EW sector return
S=pd.DataFrame(sec_ret).sort_index()
mkt=S.mean(axis=1)                                          # EW market
rs=pd.read_parquet('study-research/eq_kr/industries/financial/raw-v3/data/regime_series.parquet')
rs.index=pd.to_datetime(rs.index)
flow=rs['foreign_net_kospi'].reindex(S.index).fillna(0.0)
flow_s=(flow-flow.rolling(60,min_periods=20).mean())/flow.rolling(60,min_periods=20).std()  # standardized daily flow shock

print('sectors:',list(S.columns))
print('daily n', len(S), S.index.min().date(),'->',S.index.max().date())

def flow_beta(ret, flow, mkt, mask):
    y=ret[mask].values; f=flow[mask].values; m=mkt[mask].values
    ok=~(np.isnan(y)|np.isnan(f)|np.isnan(m)); y,f,m=y[ok],f[ok],m[ok]
    if len(y)<100: return np.nan
    X=np.column_stack([np.ones(len(y)),f,m])           # control for market
    b=np.linalg.lstsq(X,y,rcond=None)[0]
    return b[1]  # flow beta (flow-specific, market-controlled)

full=flow_s.notna()
betas={s:flow_beta(S[s],flow_s,mkt,full) for s in S.columns}
b=pd.Series(betas).dropna()*1e4  # scale to bp per 1sd flow shock
print()
print('=== Sector flow-beta (market-controlled, bp return per +1sd foreign flow shock) ===')
print(b.sort_values(ascending=False).round(2).to_string())
print('  cross-sectional DISPERSION: std=%.2f  range=%.2f  mean=%.2f'%(b.std(),b.max()-b.min(),b.mean()))

# split-half stability of the cross-sectional ranking
n=len(S); h1=S.index[:n//2]; h2=S.index[n//2:]
m1={s:flow_beta(S[s],flow_s,mkt,flow_s.notna()&S.index.isin(h1)) for s in S.columns}
m2={s:flow_beta(S[s],flow_s,mkt,flow_s.notna()&S.index.isin(h2)) for s in S.columns}
b1=pd.Series(m1).dropna(); b2=pd.Series(m2).dropna(); common=b1.index.intersection(b2.index)
rho,p=stats.spearmanr(b1[common],b2[common])
print()
print('=== Split-half stability of sector flow-beta ranking ===')
print('  H1 %s..%s  H2 %s..%s'%(h1.min().date(),h1.max().date(),h2.min().date(),h2.max().date()))
print('  Spearman(rank_H1, rank_H2) = %.3f  p=%.3f  n_sectors=%d'%(rho,p,len(common)))
print()
print('VERDICT: large dispersion + stable ranking => per-sector flow carries cross-sectional info (fetch worth it).')
print('         small dispersion OR unstable => per-sector flow ~ aggregate (Phase1 futile).')
