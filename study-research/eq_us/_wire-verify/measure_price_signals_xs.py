import pandas as pd, numpy as np
from scipy import stats
def run(SEC):
    base=f'study-research/eq_us/industries/{SEC}/raw-v3/data'
    px=pd.read_parquet(f'{base}/prices.parquet'); px.index=pd.to_datetime(px.index)
    uni=pd.read_parquet(f'{base}/universe.parquet'); sect=uni.set_index('ticker')['sector']
    tk=[t for t in px.columns if t in sect.index]
    px=px[tk]; lp=np.log(px)
    asof=px.resample('ME').last().index
    asof=asof[(asof>=pd.Timestamp('2012-01-01'))&(asof<=pd.Timestamp('2024-12-31'))]
    # signals at month-end
    mom_12_1=(lp.shift(21)-lp.shift(252))      # 12-1 momentum
    mom_6=(lp.shift(0)-lp.shift(126))
    rev_1m=-(lp-lp.shift(21))                   # 1M reversal
    vol_60=lp.diff().rolling(60).std()*np.sqrt(252)
    lowvol=-vol_60
    fwd12=px.shift(-252)/px-1
    sigs={'mom_12_1':mom_12_1,'mom_6':mom_6,'rev_1m':rev_1m,'lowvol':lowvol}
    def secz(row_df):
        # row_df: index=ticker, with sector -> z within sector
        s=pd.Series(sect[row_df.index].values,index=row_df.index)
        out=row_df.copy()
        for col in row_df.columns:
            out[col]=row_df.groupby(s)[col].transform(lambda x:(x-x.mean())/x.std())
        return out
    recs=[]
    for a in asof:
        if a not in px.index:  # align to nearest trading day
            idx=px.index[px.index<=a]
            if not len(idx): continue
            a2=idx[-1]
        else: a2=a
        df=pd.DataFrame({k:v.loc[a2] for k,v in sigs.items()})
        df['fwd12']=fwd12.loc[a2]
        df=df.dropna(subset=['fwd12'])
        if len(df)<10: continue
        z=secz(df[list(sigs)])
        z['fwd12']=df['fwd12']
        recs.append(z)
    A=pd.concat(recs)
    print(f'=== {SEC} sector-neutral pooled rank-IC vs fwd12M (n_obs={len(A)}) ===')
    for k in sigs:
        d=A[[k,'fwd12']].dropna()
        r,p=stats.spearmanr(d[k],d['fwd12'])
        print('  %-10s IC=%+.3f p=%.4f n=%d'%(k,r,p,len(d)))
for SEC in ['us_cyclical','us_defensive','us_mega_tech']:
    try: run(SEC)
    except Exception as ex: print(SEC,'ERR',ex)
