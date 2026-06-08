import pandas as pd, numpy as np
from scipy import stats
def ewret(sec):
    px=pd.read_parquet(f'study-research/eq_us/industries/{sec}/raw-v3/data/prices.parquet')
    px.index=pd.to_datetime(px.index); r=px.pct_change()
    return r[r.notna().sum(axis=1)>=3].mean(axis=1)
R=pd.DataFrame({s:ewret(s) for s in ['us_cyclical','us_defensive','us_mega_tech']}).dropna()
m=pd.read_parquet('study-research/eq_us/industries/us_defensive/raw-v3/data/macro.parquet'); m.index=pd.to_datetime(m.index)
Rm=(1+R).resample('ME').prod()-1
Rm.columns=['cyc','def','meg']; Rm=Rm.loc['2015-06-30':]
M=m.resample('ME').last().reindex(Rm.index).ffill()
def ann(x): return (1+x).prod()**(12/len(x))-1
def shp(x): return x.mean()/x.std()*np.sqrt(12)
EW=(Rm.mean(axis=1)).rename('EW')

print('=== Static benchmarks (no timing) ===')
print('  EW(1/3)            ann=%+.1f%% Sharpe=%.2f'%(ann(EW)*100,shp(EW)))
for c in ['cyc','def','meg']:
    sta=0.6*Rm[c]+0.2*Rm.drop(columns=c).sum(axis=1)/1  # OW c to 0.6, others 0.2 each
    sta=0.6*Rm[c]+0.2*Rm[[x for x in Rm.columns if x!=c]].sum(axis=1)
    print('  static OW %-4s        ann=%+.1f%% Sharpe=%.2f'%(c,ann(sta)*100,shp(sta)))
print('  always 100%% meg     ann=%+.1f%% Sharpe=%.2f'%(ann(Rm['meg'])*100,shp(Rm['meg'])))

# ---- Is there genuine TIMING? credit-regime conditional spread ----
print()
print('=== Conditional sleeve spreads by regime (does the regime actually flip leadership?) ===')
hy_chg=M['hy_oas'].diff(3)
rr_chg=M['real_rate'].diff(6)
vix_z=(M['vix']-M['vix'].rolling(36,min_periods=12).mean())/M['vix'].rolling(36,min_periods=12).std()
def cond(sig_pos, name, a, b):
    # next-month return spread a-b, conditional on signal (shifted)
    s=sig_pos.shift(1).reindex(Rm.index)
    sp=(Rm[a]-Rm[b])
    hi=sp[s==True].dropna(); lo=sp[s==False].dropna()
    t,p=stats.ttest_ind(hi,lo,equal_var=False)
    print('  %-22s %s>%s: when TRUE %+.2f%%/mo vs FALSE %+.2f%%/mo  t=%.2f p=%.3f'%(name,a,b,hi.mean()*100,lo.mean()*100,t,p))
cond(hy_chg>0,'risk-off(hy↑)','def','cyc')   # expect def beats cyc in risk-off
cond(vix_z>0.5,'highVIX','def','cyc')
cond(rr_chg>0,'real_rate↑','cyc','def')      # ledger: rr↑ -> def underperforms
cond(rr_chg>0,'real_rate↑','meg','def')

# ---- continuous momentum L/S, multiple lookbacks ----
print()
print('=== sleeve relative-momentum L/S (top-bottom), net of cost ===')
for lb in [3,6,12]:
    mom=pd.DataFrame({c:(1+Rm[c]).rolling(lb).apply(np.prod,raw=True)-1 for c in Rm.columns})
    w=pd.DataFrame(0.0,index=Rm.index,columns=Rm.columns)
    for t in Rm.index:
        mm=mom.loc[t].dropna()
        if len(mm)<3: continue
        w.loc[t,mm.idxmax()]=1.0; w.loc[t,mm.idxmin()]=-1.0
    ls=(w.shift(1)*Rm).sum(axis=1).dropna()
    to=w.diff().abs().sum(axis=1).shift(1).reindex(ls.index).fillna(0)
    net=ls-to*0.0010
    print('  L/S mom%2dM   ann=%+.1f%% Sharpe=%.2f net_ann=%+.1f%% t=%.2f'%(lb,ann(ls)*100,shp(ls),ann(net)*100, ls.mean()/(ls.std()/np.sqrt(len(ls)))))
