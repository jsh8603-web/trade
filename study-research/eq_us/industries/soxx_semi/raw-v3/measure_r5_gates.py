#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SOXX R5 검증 4게이트 (claude 자문 2R 수렴 — value under-claim / low_vol over-claim 정정).
1. ★IC 샘플링 주기 + NW lag 매칭 감사: measure가 daily-sampled 확인 + lag sweep.
2. ★non-overlap t (value tier PRIMARY): 60d 비겹침 obs (~47) 깨끗한 t.
   + block-boot block sweep {60,90,120,250}.
3. ★NVDA·AVGO leave-2-out: retention = IC(-2)/IC(0). ≥0.70 AND non-overlap t≥2 → moderate.
4. ★low_vol REJECTED-as-constructed: 부호 anti-BAB 확인 + pre-AI 단독 + beta·AI-mom 직교화 재추정.

재현: us_cyclical/raw-v3/data/{prices,edgar_fundamentals,macro}.parquet.
"""
import pandas as pd, numpy as np, json, sys
from scipy import stats
np.random.seed(20260608)
DATA="../../us_cyclical/raw-v3/data"
SEMI=['NVDA','AVGO','AMD','QCOM','TXN','MU','ADI','LRCX','KLAC','AMAT','INTC','MCHP']

px=pd.read_parquet(f"{DATA}/prices.parquet")[SEMI]
edg=pd.read_parquet(f"{DATA}/edgar_fundamentals.parquet");edg=edg[edg.ticker.isin(SEMI)].copy()
edg['filed']=pd.to_datetime(edg['filed']);edg=edg.sort_values('filed').drop_duplicates(['ticker','concept','end'],keep='first')
def pit(c):
    d=edg[edg.concept==c];out={}
    for tk in SEMI:
        dt=d[d.ticker==tk].sort_values('filed')
        if dt.empty:out[tk]=pd.Series(np.nan,index=px.index);continue
        s=pd.Series(dt.val.values,index=dt.filed.values);s=s[~s.index.duplicated(keep='last')].sort_index()
        out[tk]=s.reindex(s.index.union(px.index)).ffill().reindex(px.index)
    return pd.DataFrame(out)
equity=pit('equity');shares=pit('shares');op=pit('op_income');ltd=pit('lt_debt');std=pit('st_debt');cash=pit('cash');da=pit('dep_amort')
mcap=px*shares;debt=ltd.fillna(0)+std.fillna(0)
def xs_z(df,sign=1,cols=None):
    d=df if cols is None else df[cols]
    return d.sub(d.mean(axis=1),axis=0).div(d.std(axis=1),axis=0)*sign
pbr=(mcap/equity).where(equity>0)
evb=((mcap+debt-cash.fillna(0))/(op+da.fillna(0))).where((op+da.fillna(0))>0)
ret_d=px.pct_change()
beta_roll=ret_d.rolling(60).std()  # 변동성 proxy (BAB 신호 base)

def value_z(cols=None):
    return pd.concat([xs_z(pbr,-1,cols),xs_z(evb,-1,cols)]).groupby(level=0).mean()
def lowvol_z(cols=None):
    return xs_z(beta_roll,-1,cols)  # 저변동 = +z (sign −1)

fwd60=px.pct_change(60).shift(-60)
fwd20=px.pct_change(20).shift(-20)

def daily_ic(sig,f,mask=None):
    out=[];idxs=[]
    idx=sig.index if mask is None else sig.index[mask.reindex(sig.index,fill_value=False)]
    for d in idx:
        if d not in f.index:continue
        df=pd.DataFrame({'s':sig.loc[d],'r':f.loc[d]}).dropna()
        if len(df)<4:continue
        c=stats.spearmanr(df.s,df.r).correlation
        if not np.isnan(c):out.append(c);idxs.append(d)
    return pd.Series(out,index=idxs)
def nw_t(ic,lag):
    a=ic.values;n=len(a);m=a.mean();dm=a-m;g0=np.dot(dm,dm)/n;s=g0
    for k in range(1,lag+1):
        if k>=n:break
        gk=np.dot(dm[:-k],dm[k:])/n;w=1-k/(lag+1);s+=2*w*gk
    se=np.sqrt(s/n);return m,(m/se if se>0 else np.nan)

results={'meta':{'note':'R5 4게이트 — value under-claim/low_vol over-claim 정정'}}

# ── ★1. IC 샘플링 주기 감사 ──
ic_val60=daily_ic(value_z(),fwd60)
# daily 여부: IC index 간격 확인
gaps=pd.Series(ic_val60.index).diff().dt.days.dropna()
results['gate1_sampling']={
  'ic_sampling':'daily (매 거래일 cross-section IC)',
  'evidence':f'IC obs={len(ic_val60)}, median gap={gaps.median()}d (1~3 = daily 거래일)',
  'nw_lag_correct':'daily-sampled forward 60d → NW lag=60 적정 (monthly였으면 BUG). T=185 auto-bw=4 는 monthly 기준 = 부적용',
  'nw_lag_sweep':{}}
for lag in [4,20,60,90]:
    m,t=nw_t(ic_val60,lag)
    results['gate1_sampling']['nw_lag_sweep'][f'lag_{lag}']={'ic':round(m,4),'nw_t':round(t,2)}

# ── ★2. non-overlap t (value PRIMARY) + block-boot sweep ──
# 60d 비겹침: 매 60거래일 간격으로 IC sampling
nonoverlap_ic=ic_val60.iloc[::60]
m_no=nonoverlap_ic.mean();se_no=nonoverlap_ic.std(ddof=1)/np.sqrt(len(nonoverlap_ic))
t_no=m_no/se_no if se_no>0 else np.nan
p_no=2*(1-stats.t.cdf(abs(t_no),df=len(nonoverlap_ic)-1))
def block_boot(ic,block,B=2000):
    a=ic.values;n=len(a)
    if n<block+1:return [np.nan,np.nan]
    nb=int(np.ceil(n/block));ms=[]
    for _ in range(B):
        st=np.random.randint(0,n-block+1,nb);ms.append(np.concatenate([a[s:s+block] for s in st])[:n].mean())
    return list(np.round(np.percentile(ms,[2.5,97.5]),4))
results['gate2_nonoverlap']={
  'nonoverlap_n':len(nonoverlap_ic),'ic_mean':round(m_no,4),'t_nonoverlap':round(t_no,2),'p_nonoverlap':round(p_no,4),
  'verdict':'value PRIMARY tier 앵커. t≥2 면 modest-but-real',
  'block_boot_sweep':{}}
for blk in [60,90,120,250]:
    ci=block_boot(ic_val60,blk)
    results['gate2_nonoverlap']['block_boot_sweep'][f'block_{blk}']={'ci_95':ci,'crosses_0':bool(ci[0]<=0<=ci[1])}

# ── ★3. NVDA·AVGO leave-2-out (factor vs 2-name bet) ──
others=[t for t in SEMI if t not in ['NVDA','AVGO']]
ic_full=ic_val60.mean()
ic_lo2=daily_ic(value_z(cols=others),fwd60).mean()
retention=ic_lo2/ic_full if ic_full!=0 else np.nan
# non-overlap t for leave-2-out
ic_lo2_series=daily_ic(value_z(cols=others),fwd60)
no_lo2=ic_lo2_series.iloc[::60];t_lo2=no_lo2.mean()/(no_lo2.std(ddof=1)/np.sqrt(len(no_lo2))) if no_lo2.std()>0 else np.nan
results['gate3_leave2out']={
  'ic_full':round(ic_full,4),'ic_leave_NVDA_AVGO':round(ic_lo2,4),'retention':round(retention,3),
  't_nonoverlap_lo2':round(t_lo2,2),
  'verdict':('moderate(factor)' if retention>=0.70 and t_no>=2 else
             'weak-concentration-dependent' if 0.40<=retention<0.70 else 'position-not-factor 강등')}

# ── ★4. low_vol REJECTED-as-constructed ──
# 4a. 부호 확인: 신호 lowvol_z = 저변동 +z. IC 양(+) 이면 저변동→fwd+ = BAB 정상. 음(−) 이면 anti-BAB(고변동 outperform)
ic_lv60=daily_ic(lowvol_z(),fwd60)
m_lv,t_lv=nw_t(ic_lv60,60)
# ★주의: measure_conditional 에서 lowvol IC가 음수로 보고됨 → 신호 정렬 재확인
# lowvol_z sign=−1 (저변동 = +z). IC 음 = 저변동(+z) → fwd 음 = 고변동 outperform = ★anti-BAB
sign_interp = 'BAB 정상(저변동 outperform)' if m_lv>0 else '★anti-BAB(고변동 outperform) = BAB 반대'
# 4b. pre-AI 단독 재추정
preAI=px.index<=pd.Timestamp('2022-12-31')
ic_lv_pre=daily_ic(lowvol_z(),fwd60,pd.Series(preAI,index=px.index))
m_pre,t_pre=nw_t(ic_lv_pre,60) if len(ic_lv_pre)>60 else (np.nan,np.nan)
# 4c. beta·AI-momentum 직교화: lowvol 신호를 beta·mom 에 회귀 후 잔차로 IC
mom_sig=px.shift(20)/px.shift(252)-1
def orthog_ic(f,mask=None):
    """lowvol 잔차(beta·mom 직교) → fwd IC."""
    ics=[]
    idx=px.index if mask is None else px.index[mask]
    for d in idx:
        if d not in f.index:continue
        lv=lowvol_z().loc[d] if d in lowvol_z().index else None
        bt=beta_roll.loc[d];mm=mom_sig.loc[d];rr=f.loc[d]
        df=pd.DataFrame({'lv':lowvol_z().loc[d],'bt':bt,'mm':mm,'r':rr}).dropna()
        if len(df)<5:continue
        # lv ~ bt + mm 잔차
        X=np.column_stack([np.ones(len(df)),df.bt.rank(),df.mm.rank()])
        b=np.linalg.lstsq(X,df.lv.values,rcond=None)[0];res=df.lv.values-X@b
        c=stats.spearmanr(res,df.r).correlation
        if not np.isnan(c):ics.append(c)
    return pd.Series(ics)
ic_lv_orth=orthog_ic(fwd60)
m_orth,t_orth=nw_t(ic_lv_orth,60) if len(ic_lv_orth)>60 else (np.nan,np.nan)
results['gate4_lowvol']={
  'raw_ic':round(m_lv,4),'raw_nw_t':round(t_lv,2),'sign_interp':sign_interp,
  'preAI_ic':round(m_pre,4),'preAI_nw_t':round(t_pre,2),
  'orthog_ic':round(m_orth,4),'orthog_nw_t':round(t_orth,2),
  'verdict':None}  # 아래 채움

with open('validation-r5-gates.json','w',encoding='utf-8') as f:
    json.dump(results,f,indent=2,ensure_ascii=False,default=str)
sys.stderr.write("[saved] validation-r5-gates.json\n")
