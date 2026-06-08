import pandas as pd, numpy as np, glob
from scipy import stats
SEC=['aitech','auto','battery','bio','chemical','consumer','financial','refining','semiconductor','shipbuilding','steel','telecom']

# sector daily returns
sr={}
for d in sorted(glob.glob('study-research/eq_kr/industries/*/raw-v3/data/prices.parquet')):
    s=d.split('/industries/')[1].split('/')[0]
    if s not in SEC: continue
    px=pd.read_parquet(d); px.index=pd.to_datetime(px.index); r=px.pct_change()
    sr[s]=r[r.notna().sum(axis=1)>=3].mean(axis=1)
S=pd.DataFrame(sr).sort_index(); mkt=S.mean(axis=1)
rs=pd.read_parquet('study-research/eq_kr/industries/financial/raw-v3/data/regime_series.parquet')
rs.index=pd.to_datetime(rs.index)
flow=rs['foreign_net_kospi'].reindex(S.index).fillna(0.0)
fz=(flow-flow.rolling(60,min_periods=20).mean())/flow.rolling(60,min_periods=20).std()  # daily flow shock z
logr=np.log1p(S)

# ---------- Test 1: UNCONDITIONAL foreign-flow risk premium ----------
# full-sample flow-beta (market-controlled) vs full-sample mean daily return
def fbeta(y,f,m):
    ok=~(y.isna()|f.isna()|m.isna()); y,f,m=y[ok].values,f[ok].values,m[ok].values
    if len(y)<150: return np.nan
    X=np.column_stack([np.ones(len(y)),f,m]); return np.linalg.lstsq(X,y,rcond=None)[0][1]
beta={s:fbeta(S[s],fz,mkt) for s in SEC}
beta=pd.Series(beta)*1e4
meanret={s:S[s].mean()*252*100 for s in SEC}  # annualized %
mr=pd.Series(meanret)
rho,p=stats.spearmanr(beta,mr)
print('=== Test1 UNCONDITIONAL: does higher foreign-flow-beta earn higher avg return? ===')
tab=pd.DataFrame({'flow_beta_bp':beta.round(1),'ann_ret_%':mr.round(1)}).sort_values('flow_beta_bp',ascending=False)
print(tab.to_string())
print('  Spearman(beta, avg_return) = %.3f p=%.3f'%(rho,p),' => flow-exposure risk premium' if rho>0 else ' => NO/neg premium')

# ---------- Test 2: PIT rolling-beta long-short, cost-net ----------
# monthly rebalance: trailing 252d flow-beta -> tercile; forward 21d return
print()
print('=== Test2 TRADEABLE: PIT long(high-beta)-short(low-beta) sector L/S, monthly, fwd21d ===')
month_ends=S.resample('ME').last().index
def roll_beta(asof):
    win=S.loc[:asof].tail(252)
    if len(win)<200: return None
    fzw=fz.loc[win.index]; mw=mkt.loc[win.index]
    return pd.Series({s:fbeta(win[s],fzw,mw) for s in SEC})
# unconditional (always long high-beta) and flow-conditioned
res_uncond=[]; res_cond=[]
for i,me in enumerate(month_ends[:-1]):
    b=roll_beta(me)
    if b is None or b.isna().sum()>3: continue
    nb=me  # signal date
    fwd_start=S.index[S.index>me]
    if len(fwd_start)==0: continue
    fs=fwd_start[0]; fe=fs+pd.Timedelta(days=31)
    fwd=logr.loc[fs:fe].sum()  # ~21d forward sector return
    hi=b.nlargest(4).index; lo=b.nsmallest(4).index
    ls=fwd[hi].mean()-fwd[lo].mean()           # high-beta minus low-beta
    res_uncond.append(ls)
    sig=np.sign(fz.loc[:me].tail(20).mean())   # recent aggregate flow direction
    res_cond.append(sig*ls if sig!=0 else 0.0)
ru=pd.Series(res_uncond).dropna(); rc=pd.Series(res_cond).dropna()
cost=0.0023*2  # STT+fee, both legs turnover approx per rebalance
def stat(x,label):
    if len(x)<12: print('  %s n<12'%label); return
    shp=x.mean()/x.std()*np.sqrt(12)
    t=x.mean()/(x.std()/np.sqrt(len(x)))
    net=x-cost
    print('  %-26s mean=%+.4f/mo  ann=%+.1f%%  Sharpe=%+.2f  t=%+.2f  (net-cost ann=%+.1f%%)  n=%d'%(
        label,x.mean(),(np.exp(x.mean()*12)-1)*100,shp,t,(np.exp(net.mean()*12)-1)*100,len(x)))
stat(ru,'uncond long hi-beta')
stat(rc,'flow-conditioned L/S')

# IS/OOS split
half=len(ru)//2
stat(ru.iloc[:half],'uncond IS'); stat(ru.iloc[half:],'uncond OOS')
stat(rc.iloc[:half],'cond IS'); stat(rc.iloc[half:],'cond OOS')

# ---------- Test 3: lead-lag diffusion ----------
print()
print('=== Test3 LEAD-LAG: aggregate flow_t -> (hi-beta minus lo-beta) sector spread at t+k ===')
hi=beta.nlargest(4).index; lo=beta.nsmallest(4).index
spread=logr[hi].mean(axis=1)-logr[lo].mean(axis=1)
for k in [0,1,2,3,5]:
    a=fz; b2=spread.shift(-k)
    m=~(a.isna()|b2.isna())
    r,pp=stats.spearmanr(a[m],b2[m])
    print('  k=%d  corr(flow_t, spread_t+%d) = %+.3f p=%.4f'%(k,k,r,pp))
