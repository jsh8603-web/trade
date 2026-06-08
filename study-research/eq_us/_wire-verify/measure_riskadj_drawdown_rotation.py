import pandas as pd, numpy as np
def ewret(sec):
    px=pd.read_parquet(f'study-research/eq_us/industries/{sec}/raw-v3/data/prices.parquet'); px.index=pd.to_datetime(px.index)
    r=px.pct_change(); return r[r.notna().sum(axis=1)>=3].mean(axis=1)
R=pd.DataFrame({s:ewret(s) for s in ['us_cyclical','us_defensive','us_mega_tech']}).dropna()
m=pd.read_parquet('study-research/eq_us/industries/us_defensive/raw-v3/data/macro.parquet'); m.index=pd.to_datetime(m.index)
Rm=(1+R).resample('ME').prod()-1; Rm.columns=['cyc','def','meg']; Rm=Rm.loc['2015-06-30':]
M=m.resample('ME').last().reindex(Rm.index).ffill()
def stats_(x):
    ann=(1+x).prod()**(12/len(x))-1; sh=x.mean()/x.std()*np.sqrt(12)
    cum=(1+x).cumprod(); mdd=(cum/cum.cummax()-1).min()
    return ann,sh,mdd,(ann/abs(mdd) if mdd!=0 else np.nan)
def show(x,lab):
    a,s,d,c=stats_(x.dropna()); print('  %-30s ann=%+.1f%% Sharpe=%.2f MaxDD=%.1f%% Calmar=%.2f'%(lab,a*100,s,d*100,c))
EW=Rm.mean(axis=1)
print('=== Risk-adjusted / drawdown-focused sleeve rotation (2015-2026) ===')
show(EW,'EW(1/3) benchmark')

# de-risk regimes -> shift to defensive
hy=M['hy_oas']; hy_z=(hy-hy.rolling(36,min_periods=12).mean())/hy.rolling(36,min_periods=12).std()
vix=M['vix']; vix_z=(vix-vix.rolling(36,min_periods=12).mean())/vix.rolling(36,min_periods=12).std()
for sig,name in [(hy_z,'credit z>1'),(vix_z,'VIX z>1')]:
    risk_off=(sig.shift(1)>1.0).reindex(Rm.index).fillna(False)
    w=pd.DataFrame(1/3,index=Rm.index,columns=Rm.columns)
    w.loc[risk_off]=[0.10,0.80,0.10]  # de-risk to defensive
    p=(w*Rm).sum(axis=1)
    show(p,f'de-risk to DEF when {name} (n_off={risk_off.sum()})')

# risk-adjusted momentum (rank by trailing Sharpe not return)
sh6=pd.DataFrame({c:(Rm[c].rolling(6).mean()/Rm[c].rolling(6).std()) for c in Rm.columns})
w=pd.DataFrame(0.0,index=Rm.index,columns=Rm.columns)
for t in Rm.index:
    s=sh6.loc[t].dropna()
    if len(s)<3: w.loc[t]=1/3; continue
    w.loc[t,s.idxmax()]=0.5; 
    for c in Rm.columns:
        if c!=s.idxmax(): w.loc[t,c]=0.25
p=(w.shift(1)*Rm).sum(axis=1); show(p,'risk-adj momentum (Sharpe6M) OW')

# inverse-vol weighting (min-variance-ish, no return signal)
iv=pd.DataFrame({c:1/Rm[c].rolling(6).std() for c in Rm.columns})
w=iv.div(iv.sum(axis=1),axis=0); p=(w.shift(1)*Rm).sum(axis=1); show(p,'inverse-vol weight (risk parity)')

# IS/OOS for de-risk credit
print()
print('=== IS/OOS: de-risk-to-DEF on credit z>1 ===')
risk_off=(hy_z.shift(1)>1.0).reindex(Rm.index).fillna(False)
w=pd.DataFrame(1/3,index=Rm.index,columns=Rm.columns); w.loc[risk_off]=[0.10,0.80,0.10]
p=(w*Rm).sum(axis=1)
half=Rm.index[len(Rm)//2]
for tag,sub in [('IS',Rm.index[Rm.index<=half]),('OOS',Rm.index[Rm.index>half])]:
    show(p.loc[sub],f'{tag}'); show(EW.loc[sub],f'{tag} EW')
