import pandas as pd, numpy as np
from scipy import stats
SEC='us_cyclical'
base=f'study-research/eq_us/industries/{SEC}/raw-v3/data'
px=pd.read_parquet(f'{base}/prices.parquet'); px.index=pd.to_datetime(px.index)
uni=pd.read_parquet(f'{base}/universe.parquet'); sect=uni.set_index('ticker')['sector']
e=pd.read_parquet(f'{base}/edgar_fundamentals.parquet')
e['filed']=pd.to_datetime(e['filed']); e['end']=pd.to_datetime(e['end'])
e=e.dropna(subset=['filed','end','val'])

def pit_stock(concept):
    """latest filed value <= as_of (balance-sheet stock concept)."""
    d=e[e['concept']==concept].sort_values('filed')
    return d
def latest_val(d, tk, asof):
    s=d[(d['ticker']==tk)&(d['filed']<=asof)]
    return s.iloc[-1]['val'] if len(s) else np.nan
def ttm_val(concept, tk, asof):
    """sum last 4 distinct-quarter filings <= asof (flow concept)."""
    d=e[(e['concept']==concept)&(e['ticker']==tk)&(e['filed']<=asof)].copy()
    if not len(d): return np.nan
    d=d.drop_duplicates('end').sort_values('end').tail(4)
    return d['val'].sum() if len(d)>=2 else np.nan

stock_c={c:pit_stock(c) for c in ['equity','assets','shares','lt_debt','st_debt','cash']}
tickers=[t for t in px.columns if t in sect.index]
asofs=px.resample('ME').last().index
asofs=asofs[(asofs>=pd.Timestamp('2012-01-01'))&(asofs<=pd.Timestamp('2024-12-31'))]

rows=[]
for asof in asofs:
    pxrow=px.loc[:asof].iloc[-1] if len(px.loc[:asof]) else None
    if pxrow is None: continue
    for tk in tickers:
        price=pxrow.get(tk)
        if not np.isfinite(price): continue
        eq=latest_val(stock_c['equity'],tk,asof); sh=latest_val(stock_c['shares'],tk,asof)
        if not (np.isfinite(eq) and np.isfinite(sh) and sh>0): continue
        mcap=price*sh
        rev=ttm_val('revenues',tk,asof)
        opi=ttm_val('op_income',tk,asof); da=ttm_val('dep_amort',tk,asof)
        debt=np.nansum([latest_val(stock_c['lt_debt'],tk,asof),latest_val(stock_c['st_debt'],tk,asof)])
        cash=latest_val(stock_c['cash'],tk,asof)
        ev=mcap+(debt if np.isfinite(debt) else 0)-(cash if np.isfinite(cash) else 0)
        ebitda=(opi+da) if (np.isfinite(opi) and np.isfinite(da)) else np.nan
        rows.append(dict(asof=asof,tk=tk,sector=sect[tk],price=price,
            pbr=mcap/eq if eq>0 else np.nan,
            sales_yield=rev/mcap if (np.isfinite(rev) and mcap>0) else np.nan,
            ev_ebitda=ev/ebitda if (np.isfinite(ebitda) and ebitda>0) else np.nan))
P=pd.DataFrame(rows)
# forward 12M return
fwd={}
logpx=np.log(px)
for tk in tickers:
    s=logpx[tk]
    fwd[tk]=s
def fret(tk,asof):
    s=px[tk]; a=s.loc[:asof]
    if not len(a): return np.nan
    p0=a.iloc[-1]; fut=s.loc[asof:asof+pd.Timedelta(days=380)]
    fut=fut[fut.index>asof]
    if len(fut)<200: return np.nan
    return fut.iloc[min(251,len(fut)-1)]/p0-1
P['fwd12']=[fret(r.tk,r.asof) for r in P.itertuples()]

# sector-neutral z per as_of
def secz(df,col):
    return df.groupby(['asof','sector'])[col].transform(lambda x:(x-x.mean())/x.std())
for c in ['pbr','sales_yield','ev_ebitda']:
    P[c+'_z']=secz(P,c)
P['pbr_sig']=-P['pbr_z']; P['ev_sig']=-P['ev_ebitda_z']; P['sy_sig']=P['sales_yield_z']

def pooled_ic(sig,ret,df):
    d=df[[sig,ret]].dropna()
    if len(d)<200: return (np.nan,np.nan,len(d))
    r,p=stats.spearmanr(d[sig],d[ret]); return (r,p,len(d))
print('panel rows',len(P),'with fwd12',P['fwd12'].notna().sum())
print()
print('=== cyclical sector-neutral pooled rank-IC vs fwd12M (DIRECT rebuild) ===')
for s,nm in [('pbr_sig','pbr(value,wired)'),('ev_sig','ev_ebitda(value,wired)'),('sy_sig','sales_yield(value,NOT wired)')]:
    ic,p,n=pooled_ic(s,'fwd12',P); print('  %-26s IC=%+.3f p=%.4f n=%d'%(nm,ic,p,n))

# incremental: residualize sales_yield on pbr+ev, then IC
d=P[['sy_sig','pbr_sig','ev_sig','fwd12']].dropna()
X=np.column_stack([np.ones(len(d)),d['pbr_sig'],d['ev_sig']])
resid=d['sy_sig'].values-X@np.linalg.lstsq(X,d['sy_sig'].values,rcond=None)[0]
r,p=stats.spearmanr(resid,d['fwd12']); 
print()
print('=== sales_yield INCREMENTAL (orthogonal to wired pbr+ev_ebitda) ===')
print('  sales_yield ⊥(pbr,ev) -> fwd12 IC=%+.3f p=%.4f n=%d'%(r,p,len(d)))
print('  corr(sales_yield, pbr_sig)=%.2f corr(sy,ev)=%.2f'%(d['sy_sig'].corr(d['pbr_sig']),d['sy_sig'].corr(d['ev_sig'])))
P.to_parquet('/tmp/equs_cyc_panel.parquet')
