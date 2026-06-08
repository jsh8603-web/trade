import pandas as pd, numpy as np
from scipy import stats
def ewret(sec):
    px=pd.read_parquet(f'study-research/eq_us/industries/{sec}/raw-v3/data/prices.parquet')
    px.index=pd.to_datetime(px.index); r=px.pct_change()
    return r[r.notna().sum(axis=1)>=3].mean(axis=1)
sl={s:ewret(s) for s in ['us_cyclical','us_defensive','us_mega_tech']}
R=pd.DataFrame(sl).dropna()
m=pd.read_parquet('study-research/eq_us/industries/us_defensive/raw-v3/data/macro.parquet')
m.index=pd.to_datetime(m.index)
# monthly
Rm=(1+R).resample('ME').prod()-1
M=m.resample('ME').last().reindex(Rm.index).ffill()
Rm=Rm.loc['2015-06-30':]
M=M.loc[Rm.index]
cols={'cyc':'us_cyclical','def':'us_defensive','meg':'us_mega_tech'}
Rm=Rm.rename(columns={v:k for k,v in cols.items()})

def perf(w_df, label, bench):
    # w_df: weights per month (index aligned to signal month t), applied to t+1 return
    port=(w_df.shift(1)*Rm).sum(axis=1).dropna()
    common=port.index.intersection(bench.index)
    port,bench2=port.loc[common],bench.loc[common]
    ann=(1+port).prod()**(12/len(port))-1
    shp=port.mean()/port.std()*np.sqrt(12)
    excess=port-bench2
    ir=excess.mean()/excess.std()*np.sqrt(12) if excess.std()>0 else np.nan
    # turnover cost
    to=w_df.diff().abs().sum(axis=1).shift(1).reindex(port.index).fillna(0)
    net=port-to*0.0010
    net_ann=(1+net).prod()**(12/len(net))-1
    print('  %-28s ann=%+.1f%% Sharpe=%.2f IRvsEW=%+.2f net_ann=%+.1f%% (n=%d)'%(label,ann*100,shp,ir,net_ann*100,len(port)))
    return port

EW=pd.DataFrame(1/3,index=Rm.index,columns=['cyc','def','meg'])
ewport=(EW.shift(1)*Rm).sum(axis=1).dropna()
print('=== eq_us sleeve rotation backtest (monthly, 2015-2026, %d mo) ==='%len(Rm))
print('  BENCHMARK EW(1/3) ann=%+.1f%% Sharpe=%.2f'%(((1+ewport).prod()**(12/len(ewport))-1)*100, ewport.mean()/ewport.std()*np.sqrt(12)))

# signals (PIT, info up to month t)
hy=M['hy_oas']; hy_z=(hy-hy.rolling(36,min_periods=12).mean())/hy.rolling(36,min_periods=12).std()
hy_chg=hy.diff(3)
vix=M['vix']; vix_z=(vix-vix.rolling(36,min_periods=12).mean())/vix.rolling(36,min_periods=12).std()
rr=M['real_rate']; rr_chg=rr.diff(6); rr_z=(rr-rr.rolling(36,min_periods=12).mean())/rr.rolling(36,min_periods=12).std()
mom={k:(R[cols[k]].add(1).resample('ME').prod().rolling(6).apply(np.prod)-1) for k in ['cyc','def','meg']}
Mom=pd.DataFrame({k:(1+Rm[k]).rolling(6).apply(np.prod,raw=True)-1 for k in Rm.columns})

def tilt(fav_when):
    # fav_when: Series of dict weights per month
    return fav_when

# A) Credit regime: hy_oas rising (risk-off) -> defensive; falling -> cyclical+mega
wA=pd.DataFrame(index=Rm.index,columns=['cyc','def','meg'],dtype=float)
ro=(hy_chg>0)  # risk-off
wA.loc[ro]=[0.15,0.70,0.15]; wA.loc[~ro]=[0.45,0.10,0.45]; wA=wA.fillna(1/3)
# B) VIX regime
wB=pd.DataFrame(index=Rm.index,columns=['cyc','def','meg'],dtype=float)
hi=(vix_z>0.5); wB.loc[hi]=[0.15,0.70,0.15]; wB.loc[~hi]=[0.40,0.20,0.40]; wB=wB.fillna(1/3)
# C) real_rate change: rising real rate -> underweight defensive (ledger sign)
wC=pd.DataFrame(index=Rm.index,columns=['cyc','def','meg'],dtype=float)
up=(rr_chg>0); wC.loc[up]=[0.45,0.10,0.45]; wC.loc[~up]=[0.20,0.60,0.20]; wC=wC.fillna(1/3)
# D) sleeve relative momentum: overweight top-momentum sleeve
wD=pd.DataFrame(0.0,index=Rm.index,columns=['cyc','def','meg'])
for t in Rm.index:
    mm=Mom.loc[t].dropna()
    if len(mm)<3: wD.loc[t]=1/3; continue
    top=mm.idxmax(); w={c:0.2 for c in ['cyc','def','meg']}; w[top]=0.6; wD.loc[t]=[w['cyc'],w['def'],w['meg']]
# E) combined: credit + momentum
wE=(wA+wD)/2

for w,lab in [(wA,'A credit(hy_oas) regime'),(wB,'B VIX regime'),(wC,'C real_rate change'),(wD,'D sleeve momentum'),(wE,'E credit+momentum')]:
    perf(w,lab,ewport)

# IS/OOS for best-looking
print()
print('=== IS/OOS split (momentum D & credit A) ===')
half=Rm.index[len(Rm)//2]
for w,lab in [(wA,'A credit'),(wD,'D momentum')]:
    for tag,sub in [('IS',Rm.index[Rm.index<=half]),('OOS',Rm.index[Rm.index>half])]:
        p=(w.shift(1)*Rm).sum(axis=1).loc[sub].dropna()
        b=ewport.loc[sub]
        ex=(p-b.reindex(p.index)).dropna()
        print('  %-12s %s ann=%+.1f%% IRvsEW=%+.2f'%(lab,tag,((1+p).prod()**(12/len(p))-1)*100, ex.mean()/ex.std()*np.sqrt(12) if ex.std()>0 else 0))
