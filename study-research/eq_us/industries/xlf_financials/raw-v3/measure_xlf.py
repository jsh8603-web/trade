#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XLF minimal selection 검증. 섹터-적합 factor: value=P/B·P/TBV / quality=ROE·ROIC.
★leave-top2-out retention = 1차 kill 게이트(<0.5 → 반도체식 position 위장 = PASSIVE).
Rank-IC 1m(20d)·3m(60d), ★non-overlap t primary, block-boot CI, BY-FDR.
★생존편향 flag: 현-holdings-only = 파산은행(SVB/Signature/FRC) 누락 = value-IC upper-bound.
재현: xlf_prices.parquet + xlf_edgar.parquet.
"""
import pandas as pd, numpy as np, json, sys
from scipy import stats
np.random.seed(20260608)
XLF=['BRK-B','JPM','V','MA','BAC','GS','MS','WFC','C','AXP','SPGI','BLK','SCHW','CB','PGR','AON','ICE','CME','PNC','USB','TFC','COF','MET','AIG','TRV','PRU','AFL','ALL','BK']
px=pd.read_parquet("xlf_prices.parquet")[XLF]
edg=pd.read_parquet("xlf_edgar.parquet")
edg['filed']=pd.to_datetime(edg['filed']);edg['end']=pd.to_datetime(edg['end'])
edg=edg.sort_values('filed').drop_duplicates(['ticker','concept','end'],keep='first')
def pit(c,cols):
    d=edg[edg.concept==c];out={}
    for tk in cols:
        dt=d[d.ticker==tk].sort_values('filed')
        if dt.empty:out[tk]=pd.Series(np.nan,index=px.index);continue
        s=pd.Series(dt.val.values,index=dt.filed.values);s=s[~s.index.duplicated(keep='last')].sort_index()
        out[tk]=s.reindex(s.index.union(px.index)).ffill().reindex(px.index)
    return pd.DataFrame(out)
def signals(cols):
    eq=pit('equity',cols);sh=pit('shares',cols);ni=pit('net_income',cols)
    gw=pit('goodwill',cols);intan=pit('intangibles',cols);op=pit('op_income',cols);ltd=pit('lt_debt',cols)
    mc=px[cols]*sh
    tbv=eq-gw.fillna(0)-intan.fillna(0)  # tangible book
    pb=(mc/eq).where(eq>0)
    ptbv=(mc/tbv).where(tbv>0)
    roe=(ni*4/eq).where(eq>0)            # 분기 NI annualize 근사
    roic=(op*4/(eq+ltd.fillna(0))).where((eq+ltd.fillna(0))>0)
    def z(df,sign):return df.sub(df.mean(axis=1),axis=0).div(df.std(axis=1),axis=0)*sign
    return {'value_pb':z(pb,-1),'value_ptbv':z(ptbv,-1),'quality_roe':z(roe,1),'quality_roic':z(roic,1),
            'value':pd.concat([z(pb,-1),z(ptbv,-1)]).groupby(level=0).mean()}

def daily_ic(sig,f):
    out=[];idx=[]
    for d in sig.index:
        if d not in f.index:continue
        df=pd.DataFrame({'s':sig.loc[d],'r':f.loc[d]}).dropna()
        if len(df)<5:continue
        c=stats.spearmanr(df.s,df.r).correlation
        if not np.isnan(c):out.append(c);idx.append(d)
    return pd.Series(out,index=idx)
def non_t(ic,h):
    no=ic.iloc[::h];m=no.mean();se=no.std(ddof=1)/np.sqrt(len(no))
    t=m/se if se>0 else np.nan;p=2*(1-stats.t.cdf(abs(t),df=len(no)-1)) if len(no)>1 else np.nan
    return round(m,4),round(t,2),round(p,4),len(no)
def bootci(ic,block,B=2000):
    a=ic.values;n=len(a)
    if n<block+1:return [np.nan,np.nan]
    nb=int(np.ceil(n/block));ms=[]
    for _ in range(B):
        st=np.random.randint(0,n-block+1,nb);ms.append(np.concatenate([a[s:s+block] for s in st])[:n].mean())
    return list(np.round(np.percentile(ms,[2.5,97.5]),4))

results={'meta':{'universe':f'XLF top-cap {len(XLF)}종(현 holdings, EW 기준)','factors':'value=P/B·P/TBV / quality=ROE·ROIC',
  'survivor_flag':'★현-holdings-only = 2023 SVB/Signature/FRC 파산은행 누락 = value-IC upward bias = ★upper-bound',
  'subindustry_caveat':'★V/MA(결제네트워크)=자본경량 P/B 무의미 / 은행(JPM/BAC/WFC/C)=P/B 유효 / 보험=P/TBV 유효 = 이질성'}}

# ── 신호별 IC (1m/3m), value primary ──
for sn in ['value','value_pb','value_ptbv','quality_roe','quality_roic']:
    sig=signals(XLF)[sn]
    res={}
    for h in [20,60]:
        fwd=px.pct_change(h).shift(-h)
        ic=daily_ic(sig,fwd)
        m,t,p,non=non_t(ic,h)
        res[f'y_{h}d']={'daily_ic':round(ic.mean(),4),'nonoverlap_n':non,'nonoverlap_t':t,'p':p,
                        'block_ci':bootci(ic,h),'survive_t2':bool(abs(t)>2)}
    results[sn]=res

# ── ★leave-top2-out retention (1차 kill 게이트) — top2 = BRK-B, JPM ──
TOP2=['BRK-B','JPM']
others=[t for t in XLF if t not in TOP2]
for h in [20,60]:
    fwd_full=px.pct_change(h).shift(-h)
    ic_full=daily_ic(signals(XLF)['value'],fwd_full[XLF]).mean()
    ic_lo2=daily_ic(signals(others)['value'],fwd_full[others]).mean()
    ret=ic_lo2/ic_full if ic_full!=0 else np.nan
    _,t_lo2,p_lo2,n_lo2=non_t(daily_ic(signals(others)['value'],fwd_full[others]),h)
    results[f'leave_top2_y{h}']={'ic_full':round(ic_full,4),'ic_leave_top2':round(ic_lo2,4),
      'retention':round(ret,3),'nonoverlap_t_lo2':t_lo2,'kill_gate':'PASS(≥0.5)' if ret>=0.5 else 'FAIL(<0.5)=position 위장'}

# ── ★판정 (3m=y60 primary, value) ──
v60=results['value']['y_60d'];ret60=results['leave_top2_y60']['retention']
gate_pass = (abs(v60['nonoverlap_t'])>=2) and (ret60>=0.5)
results['VERDICT']={
  'value_y60_nonoverlap_t':v60['nonoverlap_t'],'leave_top2_retention_y60':ret60,
  'kill_gate':results['leave_top2_y60']['kill_gate'],
  'PASS':bool(gate_pass),
  'interpretation':('★selection 신호 잠정 존재(retention≥0.5 AND t≥2, upper-bound 감안) → main 보고 후 deeper 결정'
    if gate_pass else
    '★PASSIVE 확정(retention<0.5 OR t<2) = XLF도 position 위장/무신호 = early-stop 후보. null result')}
with open('validation-xlf.json','w',encoding='utf-8') as f:
    json.dump(results,f,indent=2,ensure_ascii=False,default=str)
sys.stderr.write("[saved] validation-xlf.json\n")
