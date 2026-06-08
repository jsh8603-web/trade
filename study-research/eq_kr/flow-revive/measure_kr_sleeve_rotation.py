import pandas as pd, numpy as np, glob
from scipy import stats
SEC=['aitech','auto','battery','bio','chemical','consumer','financial','refining','semiconductor','shipbuilding','steel','telecom']
sr={}
for d in sorted(glob.glob('study-research/eq_kr/industries/*/raw-v3/data/prices.parquet')):
    s=d.split('/industries/')[1].split('/')[0]
    if s not in SEC: continue
    px=pd.read_parquet(d); px.index=pd.to_datetime(px.index); r=px.pct_change()
    sr[s]=r[r.notna().sum(axis=1)>=3].mean(axis=1)
R=pd.DataFrame(sr).sort_index()
Rm=(1+R).resample('ME').prod()-1
Rm=Rm.loc['2019-06-30':]
EW=Rm.mean(axis=1)
def ann(x):return (1+x).prod()**(12/len(x))-1
def shp(x):return x.mean()/x.std()*np.sqrt(12)
# rotation signals panel (study's own)
rsp=pd.read_parquet('study-research/eq_kr/industries/_rotation/data/rotation_signals_panel.parquet')
rsp.index=pd.to_datetime(rsp.index)
# macro
reg=pd.read_parquet('study-research/eq_kr/industries/financial/raw-v3/data/regime_series.parquet'); reg.index=pd.to_datetime(reg.index)
flow=reg['foreign_net_kospi'].resample('ME').sum(); usdkrw=reg['usdkrw'].resample('ME').last()

print('=== KR sleeve(12 ind) rotation, monthly 2019-2026 (%d mo) ==='%len(Rm))
print('  BENCHMARK EW  ann=%+.1f%% Sharpe=%.2f'%(ann(EW)*100,shp(EW)))

# A) study rotation_signals_panel cross-sectional rank-IC vs fwd1M (reproduce portfolio)
common=rsp.columns.intersection(Rm.columns)
Z=rsp[common].sub(rsp[common].mean(axis=1),axis=0).div(rsp[common].std(axis=1),axis=0)  # cs z
ics=[]
for t in Z.index:
    if t not in Rm.index: continue
    fwd=Rm.loc[Rm.index[Rm.index>t][0]] if len(Rm.index[Rm.index>t]) else None
    if fwd is None: continue
    s,f=Z.loc[t],fwd[common]; m=~(s.isna()|f.isna())
    if m.sum()>=6: ics.append(stats.spearmanr(s[m],f[m])[0])
ics=pd.Series(ics).dropna()
print('  [study panel] cs rank-IC mean=%+.3f t=%.2f n=%d'%(ics.mean(),ics.mean()/(ics.std()/np.sqrt(len(ics))),len(ics)))

# rotation portfolio: tilt proportional to cs-z (top/bottom), vs EW
def rot_perf(Zsig, label, lookback_neutral=True):
    w=pd.DataFrame(0.0,index=Rm.index,columns=common)
    for t in Rm.index:
        if t not in Zsig.index: continue
        z=Zsig.loc[t,common].dropna()
        if len(z)<6: continue
        tilt=(z/z.abs().sum())*0.5   # active tilt, gross 0.5
        w.loc[t,common]=1/len(common)+tilt.reindex(common).fillna(0)
    w=w.clip(lower=0); w=w.div(w.sum(axis=1),axis=0)
    p=(w.shift(1)*Rm[common]).sum(axis=1).dropna()
    b=EW.reindex(p.index)
    ex=(p-b).dropna()
    to=w.diff().abs().sum(axis=1).shift(1).reindex(p.index).fillna(0)
    net=p-to*0.0023
    print('  %-26s ann=%+.1f%% IRvsEW=%+.2f net_ann=%+.1f%%'%(label,ann(p)*100,ex.mean()/ex.std()*np.sqrt(12) if ex.std()>0 else 0, ann(net)*100))
    return ex
exA=rot_perf(Z,'study panel tilt')

# B) sleeve relative momentum (KR)
for lb in [3,6,12]:
    mom=pd.DataFrame({c:(1+Rm[c]).rolling(lb).apply(np.prod,raw=True)-1 for c in common})
    momz=mom.sub(mom.mean(axis=1),axis=0).div(mom.std(axis=1),axis=0)
    rot_perf(momz,f'KR sleeve mom{lb}M')

# C) foreign-flow regime conditioning: does flow regime improve study panel?
flow_z=(flow-flow.rolling(12,min_periods=6).mean())/flow.rolling(12,min_periods=6).std()
# regime: inflow vs outflow -> does panel tilt work better in one regime?
exA2=exA.copy()
fzr=flow_z.reindex(exA.index).shift(1)
inflow=exA[fzr>0]; outflow=exA[fzr<=0]
print('  [flow regime] study-tilt excess: inflow %+.2f%%/mo (n%d) vs outflow %+.2f%%/mo (n%d)'%(inflow.mean()*100,len(inflow),outflow.mean()*100,len(outflow)))

# IS/OOS for study panel tilt
half=exA.index[len(exA)//2]
for tag,sub in [('IS',exA.index[exA.index<=half]),('OOS',exA.index[exA.index>half])]:
    e=exA.loc[sub]; print('  study-tilt %s IRvsEW=%+.2f'%(tag, e.mean()/e.std()*np.sqrt(12) if e.std()>0 else 0))
