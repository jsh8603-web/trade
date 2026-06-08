#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SOXX 반도체 R3 conditional IC surface — 한국 conditional_ic_surface 양식 복제.
IC(지표, regime, horizon) = "어느 국면에 어느 지표가 forward return 예측하나".
- 지표: value(PBR/EV-EBITDA z 평균) / quality(ROIC) / momentum 12-1 / rev_1m / low_vol(BAB)
- regime: rate10y(★nominal 10y, NOT DFII10 — 데이터 라벨 정정) × credit(Baa-Aaa). 각 tercile (한국 KRW3×flow3 대응).
- horizon: y_5d / y_20d / y_60d daily forward (★한국 동일, 단일 horizon 누락 보완).
- family-2 interaction: signal × regime_dummy pooled panel, month-clustered SE.
- walk-forward OOS: IS 2015-21 / OOS 2022-26.
- N<24 cell = collapse fallback + underpowered 정직 라벨. 점추정 박제금지(CI+wc_p+n+OOS+tier).

★freeze 판정 금지(이번엔, team-lead). conditional surface + family-2 + walk-forward 전체 본 뒤 재판정.
재현: us_cyclical/raw-v3/data/{prices,edgar_fundamentals,macro}.parquet (SOXX 12종).
"""
import pandas as pd, numpy as np, json, sys
from scipy import stats
np.random.seed(20260608)

DATA="../../us_cyclical/raw-v3/data"
SEMI=['NVDA','AVGO','AMD','QCOM','TXN','MU','ADI','LRCX','KLAC','AMAT','INTC','MCHP']
SUB={'NVDA':'fabless','AVGO':'fabless','AMD':'fabless','QCOM':'fabless','MU':'memory',
     'LRCX':'equip','KLAC':'equip','AMAT':'equip','TXN':'analog_idm','ADI':'analog_idm','INTC':'analog_idm','MCHP':'analog_idm'}
IS_END=pd.Timestamp('2021-12-31')

# ── 가격 (daily) + forward 5/20/60d return ──
px=pd.read_parquet(f"{DATA}/prices.parquet")[SEMI]
fwd={h:px.pct_change(h).shift(-h) for h in [5,20,60]}   # t일 신호 → t+h forward return

# ── EDGAR PIT 펀더멘털 → daily ffill ──
edg=pd.read_parquet(f"{DATA}/edgar_fundamentals.parquet");edg=edg[edg.ticker.isin(SEMI)].copy()
edg['filed']=pd.to_datetime(edg['filed']);edg=edg.sort_values('filed').drop_duplicates(['ticker','concept','end'],keep='first')
def pit(c):
    d=edg[edg.concept==c];out={}
    for tk in SEMI:
        dt=d[d.ticker==tk].sort_values('filed')
        if dt.empty: out[tk]=pd.Series(np.nan,index=px.index);continue
        s=pd.Series(dt.val.values,index=dt.filed.values);s=s[~s.index.duplicated(keep='last')].sort_index()
        out[tk]=s.reindex(s.index.union(px.index)).ffill().reindex(px.index)
    return pd.DataFrame(out)
equity=pit('equity');shares=pit('shares');op=pit('op_income');ltd=pit('lt_debt');std=pit('st_debt');cash=pit('cash');da=pit('dep_amort')
mcap=px*shares; debt=ltd.fillna(0)+std.fillna(0)

# ── 신호 (daily cross-section z) ──
def xs_z(df,sign=1): return df.sub(df.mean(axis=1),axis=0).div(df.std(axis=1),axis=0)*sign
pbr=(mcap/equity).where(equity>0)
evb=((mcap+debt-cash.fillna(0))/(op+da.fillna(0))).where((op+da.fillna(0))>0)
value=pd.concat([xs_z(pbr,-1),xs_z(evb,-1)]).groupby(level=0).mean()
quality=xs_z(op/(equity+debt),1)
mom=xs_z(px.shift(20)/px.shift(252)-1,1)        # 12-1 (≈252-20 거래일)
rev=xs_z(px.shift(1)/px.shift(20)-1,-1)          # 1M 단기 reversal (sign -1)
lowvol=xs_z(px.pct_change().rolling(60).std(),-1) # 저변동 (sign -1 = 저변동 +)
SIGS={'value':value,'quality':quality,'mom_12_1':mom,'rev_1m':rev,'low_vol':lowvol}

# ── regime: rate10y(nominal) × credit(baa_aaa) tercile ──
mac=pd.read_parquet(f"{DATA}/macro.parquet")
rate=mac['rate10y'].reindex(px.index).ffill()
credit=mac['baa_aaa'].reindex(px.index).ffill()
def tercile(s):
    q=s.quantile([1/3,2/3])
    return pd.cut(s,[-np.inf,q.iloc[0],q.iloc[1],np.inf],labels=['low','mid','high'])
rate_r=tercile(rate); credit_r=tercile(credit)

# ── IC helper ──
def daily_ic(sig,f,mask=None):
    ics=[]
    idx=sig.index if mask is None else sig.index[mask.reindex(sig.index,fill_value=False)]
    for d in idx:
        if d not in f.index: continue
        df=pd.DataFrame({'s':sig.loc[d],'r':f.loc[d]}).dropna()
        if len(df)<4: continue
        c=stats.spearmanr(df.s,df.r).correlation
        if not np.isnan(c): ics.append(c)
    return pd.Series(ics)
def eff_n(ic):
    a=ic.values;n=len(a)
    if n<10: return n
    ac=[]
    for k in range(1,min(n//4,60)):
        c=np.corrcoef(a[:-k],a[k:])[0,1]
        if np.isnan(c) or c<0: break
        ac.append(c)
    return n/max(1+2*sum(ac),1)
def bootci(ic,block=20,B=1000):
    a=ic.values;n=len(a)
    if n<block+1: return [np.nan,np.nan]
    nb=int(np.ceil(n/block));ms=[]
    for _ in range(B):
        st=np.random.randint(0,n-block+1,nb);ms.append(np.concatenate([a[s:s+block] for s in st])[:n].mean())
    return list(np.round(np.percentile(ms,[2.5,97.5]),4))
def wcp(ic,block=20,B=1000):
    a=ic.values;n=len(a)
    if n<block+1: return np.nan
    o=a.mean();dm=a-o;nb=int(np.ceil(n/block));c=0
    for _ in range(B):
        w=np.repeat(np.random.choice([-1,1],nb),block)[:n]
        if abs((dm*w).mean())>=abs(o): c+=1
    return round(c/B,4)
def cell(sig,f,mask):
    ic=daily_ic(sig,f,mask)
    if len(ic)<24: return {'ic':round(ic.mean(),4) if len(ic) else None,'n_days':len(ic),'status':'underpowered(N<24d)'}
    en=eff_n(ic)
    return {'ic':round(ic.mean(),4),'ci':bootci(ic),'wc_p':wcp(ic),'n_days':len(ic),'eff_n':round(en,1),
            'status':'powered' if en>=24 else 'underpowered(eff_N<24)'}

results={'meta':{'universe':SEMI,'n_stocks':12,'regime':'rate10y(★nominal 10y, NOT DFII10)×credit(Baa-Aaa) tercile',
    'horizon':['y_5d','y_20d','y_60d'],'survivor_bias':'PARTIAL(현 holdings, historical 무료부재)→TENTATIVE 상한',
    'data_note':'★rate10y 컬럼 = nominal 10y(값 0.52~4.98 음수0 = DGS10, NOT DFII10 TIPS). round-1 "실질금리 DFII10" 라벨 정정 필요',
    'note':'점추정 박제금지 CI+wc_p+n+OOS+tier. N<24 underpowered 정직 라벨'}}

# ── 1. unconditional × 3 horizon ──
results['unconditional']={}
for sn,sig in SIGS.items():
    results['unconditional'][sn]={f'y_{h}d':cell(sig,fwd[h],None) for h in [5,20,60]}

# ── 2. conditional: rate regime × horizon (single-axis, 한국 single-axis 대응) ──
results['conditional_rate']={}
for sn,sig in SIGS.items():
    results['conditional_rate'][sn]={}
    for rv in ['low','mid','high']:
        mask=(rate_r==rv)
        results['conditional_rate'][sn][f'rate_{rv}']={f'y_{h}d':cell(sig,fwd[h],mask) for h in [20]}  # y_20d 메인
# ── 3. conditional: credit regime × horizon ──
results['conditional_credit']={}
for sn,sig in SIGS.items():
    results['conditional_credit'][sn]={}
    for cv in ['low','mid','high']:
        mask=(credit_r==cv)
        results['conditional_credit'][sn][f'credit_{cv}']={f'y_{h}d':cell(sig,fwd[h],mask) for h in [20]}

# ── 4. family-2 interaction: signal × regime_dummy (high) pooled panel ──
def interaction(sig,f,regime_r,hi_label):
    rows=[]
    for d in sig.index:
        if d not in f.index: continue
        s=sig.loc[d];r=f.loc[d];reg=regime_r.loc[d] if d in regime_r.index else np.nan
        if pd.isna(reg): continue
        df=pd.DataFrame({'s':s,'r':r}).dropna()
        if len(df)<4: continue
        df['sr']=df.s.rank(pct=True);df['rr']=df.r.rank(pct=True)
        df['hi']=1 if reg==hi_label else 0; df['day']=d
        rows.append(df)
    if not rows: return None
    P=pd.concat(rows)
    X=np.column_stack([np.ones(len(P)),P.sr,P.hi,P.sr*P.hi]); y=P.rr.values
    try: b=np.linalg.lstsq(X,y,rcond=None)[0]
    except: return None
    resid=y-X@b
    # day-clustered SE (간이)
    XtX_inv=np.linalg.inv(X.T@X)
    meat=np.zeros((4,4))
    for d,g in P.groupby('day'):
        Xg=np.column_stack([np.ones(len(g)),g.sr,g.hi,g.sr*g.hi]); rg=resid[P.day==d]
        sc=Xg.T@rg; meat+=np.outer(sc,sc)
    V=XtX_inv@meat@XtX_inv; se=np.sqrt(np.diag(V))
    return {'b_main':round(b[1],4),'t_main':round(b[1]/se[1],2),
            'b_interaction':round(b[3],4),'t_interaction':round(b[3]/se[3],2),
            'n_obs':len(P),'n_days':P.day.nunique()}
results['family_2_interaction']={'rate_high':{},'credit_high':{}}
for sn,sig in SIGS.items():
    results['family_2_interaction']['rate_high'][sn]=interaction(sig,fwd[20],rate_r,'high')
    results['family_2_interaction']['credit_high'][sn]=interaction(sig,fwd[20],credit_r,'high')

# ── 5. walk-forward OOS (value y_20d, IS/OOS) ──
def split_ic(sig,f,lo,hi):
    mask=pd.Series(True,index=sig.index)
    if lo is not None: mask&=(sig.index>=lo)
    if hi is not None: mask&=(sig.index<=hi)
    ic=daily_ic(sig,f,mask)
    return {'ic':round(ic.mean(),4) if len(ic) else None,'n_days':len(ic),
            'ci':bootci(ic) if len(ic)>=24 else None,'wc_p':wcp(ic) if len(ic)>=24 else None}
results['walk_forward']={}
for sn,sig in SIGS.items():
    results['walk_forward'][sn]={
        'IS_2015_2021':split_ic(sig,fwd[20],None,IS_END),
        'OOS_2022_2026':split_ic(sig,fwd[20],pd.Timestamp('2022-01-01'),None)}

with open('validation-conditional-v1.json','w',encoding='utf-8') as f:
    json.dump(results,f,indent=2,ensure_ascii=False,default=str)
sys.stderr.write("[saved] validation-conditional-v1.json\n")
