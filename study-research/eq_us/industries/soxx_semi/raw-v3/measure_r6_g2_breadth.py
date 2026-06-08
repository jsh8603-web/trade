#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SOXX R6 G2 — breadth 확장 value IC + leave-N-out retention 재측정.
광의 universe = 현 12종(CORE) + 중소형 21종(SMALL) = 33종. XSD EW(중소형 포함, cap-weight 금지).
★핵심: breadth 확장 시 value IC 살아나나? leave-NVDA·AVGO retention 0.044→? (≥0.40 정제/≥0.70 factor)
재현: xsd_edgar_small.parquet + xsd_prices_small.parquet + us_cyclical CORE parquet.
"""
import pandas as pd, numpy as np, json, sys
from scipy import stats
np.random.seed(20260608)
DATA="../../us_cyclical/raw-v3/data"
CORE=['NVDA','AVGO','AMD','QCOM','TXN','MU','ADI','LRCX','KLAC','AMAT','INTC','MCHP']
SMALL=['MRVL','NXPI','SWKS','QRVO','MPWR','LSCC','RMBS','SLAB','POWI','DIOD','SMTC','MTSI','FORM','ACLS','UCTT','SYNA','CRUS','ON','COHU','MXL','AMBA']
ALL=CORE+SMALL

# ── 가격 병합 ──
px_core=pd.read_parquet(f"{DATA}/prices.parquet")[CORE]
px_small=pd.read_parquet("xsd_prices_small.parquet")
px=px_core.join(px_small,how='outer').sort_index()
px=px[ALL]

# ── EDGAR 병합 (CORE 기존 + SMALL 신규) ──
edg_core=pd.read_parquet(f"{DATA}/edgar_fundamentals.parquet");edg_core=edg_core[edg_core.ticker.isin(CORE)][['ticker','concept','end','val','filed']]
edg_small=pd.read_parquet("xsd_edgar_small.parquet")[['ticker','concept','end','val','filed']]
edg=pd.concat([edg_core,edg_small],ignore_index=True)
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

def build_value(cols):
    equity=pit('equity',cols);shares=pit('shares',cols);op=pit('op_income',cols)
    ltd=pit('lt_debt',cols);std=pit('st_debt',cols);cash=pit('cash',cols);da=pit('dep_amort',cols)
    mc=px[cols]*shares;debt=ltd.fillna(0)+std.fillna(0)
    pbr=(mc/equity).where(equity>0)
    evb=((mc+debt-cash.fillna(0))/(op+da.fillna(0))).where((op+da.fillna(0))>0)
    def xs_z(df,sign=1):return df.sub(df.mean(axis=1),axis=0).div(df.std(axis=1),axis=0)*sign
    return pd.concat([xs_z(pbr,-1),xs_z(evb,-1)]).groupby(level=0).mean()

def daily_ic(sig,f):
    out=[];idx=[]
    for d in sig.index:
        if d not in f.index:continue
        df=pd.DataFrame({'s':sig.loc[d],'r':f.loc[d]}).dropna()
        if len(df)<5:continue
        c=stats.spearmanr(df.s,df.r).correlation
        if not np.isnan(c):out.append(c);idx.append(d)
    return pd.Series(out,index=idx)
def nonoverlap_t(ic,h):
    no=ic.iloc[::h];m=no.mean();se=no.std(ddof=1)/np.sqrt(len(no))
    t=m/se if se>0 else np.nan;p=2*(1-stats.t.cdf(abs(t),df=len(no)-1)) if len(no)>1 else np.nan
    return round(m,4),round(t,2),round(p,4),len(no)
def avg_n(sig,f):
    ns=[]
    for d in sig.index:
        if d not in f.index:continue
        df=pd.DataFrame({'s':sig.loc[d],'r':f.loc[d]}).dropna()
        if len(df)>=5:ns.append(len(df))
    return round(np.mean(ns),1) if ns else 0

results={'meta':{'core_n':12,'small_n':21,'broad_n':33,'universe':'현12종+중소형21종(XSD EW)',
  'price_range':[str(px.index.min().date()),str(px.index.max().date())]}}

for label,cols in [('core_12',CORE),('broad_33',ALL)]:
    val=build_value(cols)
    res={}
    for h in [20,60]:
        fwd=px[cols].pct_change(h).shift(-h)
        ic=daily_ic(val,fwd)
        m,t,p,non=nonoverlap_t(ic,h)
        res[f'y_{h}d']={'daily_ic':round(ic.mean(),4),'nonoverlap_n':non,'nonoverlap_t':t,'p':p,
                        'avg_universe_n':avg_n(val,fwd),'survive_t2':bool(abs(t)>2)}
    results[label]=res

# ── ★leave-NVDA·AVGO retention (broad universe) ──
fwd60=px.pct_change(60).shift(-60)
val_broad=build_value(ALL);ic_full=daily_ic(val_broad,fwd60[ALL]).mean()
others=[t for t in ALL if t not in ['NVDA','AVGO']]
val_lo2=build_value(others);ic_lo2=daily_ic(val_lo2,fwd60[others]).mean()
retention=ic_lo2/ic_full if ic_full!=0 else np.nan
_,t_lo2,p_lo2,n_lo2=nonoverlap_t(daily_ic(val_lo2,fwd60[others]),60)
# leave-top4 (NVDA·AVGO·AMD·QCOM 대형 팹리스)
top4=['NVDA','AVGO','AMD','QCOM']
others4=[t for t in ALL if t not in top4]
val_lo4=build_value(others4);ic_lo4=daily_ic(val_lo4,fwd60[others4]).mean()
retention4=ic_lo4/ic_full if ic_full!=0 else np.nan

results['leave_n_out_broad']={
  'ic_full_broad':round(ic_full,4),
  'leave_NVDA_AVGO':{'ic':round(ic_lo2,4),'retention':round(retention,3),'nonoverlap_t':t_lo2,'p':p_lo2,'n_remain':len(others)},
  'leave_top4_fabless':{'ic':round(ic_lo4,4),'retention':round(retention4,3),'n_remain':len(others4)},
  'verdict':('factor(retention≥0.70)' if retention>=0.70 else
             'concentration-정제(0.40~0.70)' if retention>=0.40 else 'position-not-factor(<0.40)')}

# ── ★G2 판정 ──
b60=results['broad_33']['y_60d']
g2_pass = b60['survive_t2'] and retention>=0.40
results['G2_verdict']={
  'broad_y60_nonoverlap_t':b60['nonoverlap_t'],'broad_avg_n':b60['avg_universe_n'],
  'leave2_retention':round(retention,3),
  'PASS':bool(g2_pass),
  'interpretation':('★G2 PASS: breadth 확장 후 value t>2 + leave-2-out retention≥0.40 = factor/정제, G3 진행'
    if g2_pass else
    '★G2 결과: breadth 확장 후도 retention<0.40 OR t<2 = factor 미입증. 단 core(0.044) 대비 변화 확인')}
with open('validation-r6-g2.json','w',encoding='utf-8') as f:
    json.dump(results,f,indent=2,ensure_ascii=False,default=str)
sys.stderr.write("[saved] validation-r6-g2.json\n")
