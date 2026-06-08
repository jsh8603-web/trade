# KR EW market-return proxy builder (330 stocks across 12 industry raw-v3 prices).
# Output: /tmp/kr_mkt_ret.parquet  (used by the measure_*.py scripts here)
import pandas as pd, numpy as np, glob
frames=[]
for p in glob.glob('study-research/eq_kr/industries/*/raw-v3/data/prices.parquet'):
    df=pd.read_parquet(p); df.index=pd.to_datetime(df.index); frames.append(df)
allpx=pd.concat(frames,axis=1); allpx=allpx.loc[:,~allpx.columns.duplicated()].sort_index()
rets=allpx.pct_change(); mkt=rets.mean(axis=1,skipna=True)
mkt=mkt[rets.notna().sum(axis=1)>=10]
mkt.to_frame('mkt_ret').to_parquet('/tmp/kr_mkt_ret.parquet')
print('KR EW proxy:', len(mkt),'days, cum', round((1+mkt).cumprod().iloc[-1],3))
