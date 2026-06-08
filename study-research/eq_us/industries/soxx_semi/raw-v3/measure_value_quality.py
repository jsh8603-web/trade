#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SOXX 반도체 R3 측정 — within-sector value + quality 결합 sector-neutral z → forward-IC.
★primary = value(PBR/EV-EBITDA) + quality(ROIC) 결합. value-trap 회피(Novy-Marx other-side-of-value).
측정 3단: (a) full-sample (b) IS 2015-2021 / OOS 2022-2026 walk-forward (c) sub-industry-neutral robustness.
+ momentum 12-1 부호 falsifier + decomposition γ.
점추정 박제 금지 = block-bootstrap CI + wild-cluster bootstrap p + OOS + tier.

데이터(재사용): us_cyclical/raw-v3/data/{prices,edgar_fundamentals}.parquet (SOXX 12종).
★PIT: EDGAR (ticker,concept,end)별 최초 filed 이후만 사용. 시총=Close×shares(PIT shares).
★생존편향(I축): 현 12종 = 현 holdings → PARTIAL(historical membership 무료부재). TENTATIVE 상한.
"""
import pandas as pd, numpy as np, json, sys
from scipy import stats

np.random.seed(20260608)
DATA = "../../us_cyclical/raw-v3/data"
SEMI = ['NVDA','AVGO','AMD','QCOM','TXN','MU','ADI','LRCX','KLAC','AMAT','INTC','MCHP']
SUB = {'NVDA':'fabless','AVGO':'fabless','AMD':'fabless','QCOM':'fabless',
       'MU':'memory',
       'LRCX':'equip','KLAC':'equip','AMAT':'equip',
       'TXN':'analog_idm','ADI':'analog_idm','INTC':'analog_idm','MCHP':'analog_idm'}
IS_END = '2021-12-31'   # IS 2015-2021 / OOS 2022-2026

# ── 1. 가격 → monthly + forward 1M return ──
px = pd.read_parquet(f"{DATA}/prices.parquet")[SEMI]
pxm = px.resample('ME').last()
ret_fwd = pxm.pct_change().shift(-1)   # t 시점 신호 → t+1 forward return (PIT-safe)

# ── 2. EDGAR PIT 펀더멘털: (ticker,concept,end) 최초 filed → as-of monthly ffill ──
edg = pd.read_parquet(f"{DATA}/edgar_fundamentals.parquet")
edg = edg[edg.ticker.isin(SEMI)].copy()
edg['end'] = pd.to_datetime(edg['end']); edg['filed'] = pd.to_datetime(edg['filed'])
# 최초 filed (restatement/중복 제거): (ticker,concept,end) 그룹 최소 filed
edg = edg.sort_values('filed').drop_duplicates(['ticker','concept','end'], keep='first')

def pit_series(concept):
    """concept별 PIT monthly panel: filed 시점 이후 가장 최근 end 값 ffill."""
    d = edg[edg.concept==concept][['ticker','filed','val']].copy()
    out = {}
    months = pxm.index
    for tk in SEMI:
        dt = d[d.ticker==tk].sort_values('filed')
        if dt.empty:
            out[tk] = pd.Series(np.nan, index=months); continue
        # as-of: 각 월말에 filed<=월말 중 최신 val
        s = pd.Series(dt.val.values, index=dt.filed.values)
        s = s[~s.index.duplicated(keep='last')].sort_index()
        out[tk] = s.reindex(s.index.union(months)).ffill().reindex(months)
    return pd.DataFrame(out)

equity   = pit_series('equity')
op_inc   = pit_series('op_income')
lt_debt  = pit_series('lt_debt')
st_debt  = pit_series('st_debt')
cash     = pit_series('cash')
dep_amort= pit_series('dep_amort')
shares   = pit_series('shares')

mcap = pxm * shares   # PIT 시총
debt = lt_debt.fillna(0) + st_debt.fillna(0)

# ── 3. 신호 구성 ──
# value 1: PBR = mcap/equity → 저PBR = cheap. 신호 = -PBR (높을수록 cheap=fwd+ 가설). predicted IC(raw PBR)=음.
pbr = mcap / equity
# value 2: EV/EBITDA. EV=mcap+debt-cash, EBITDA=op_income+dep_amort (dep_amort 0 종목=EBIT proxy)
ev = mcap + debt - cash.fillna(0)
ebitda = op_inc + dep_amort.fillna(0)
ev_ebitda = ev / ebitda
ev_ebitda = ev_ebitda.where(ebitda>0)   # 음 EBITDA = 무의미 제거
# quality: ROIC = op_income / (equity+debt)
roic = op_inc / (equity + debt)
# momentum 12-1
mom = pxm.shift(1) / pxm.shift(12) - 1

def xs_z(df, sign=1):
    """월별 cross-section z-score (sector-neutral = universe-relative). sign 곱."""
    z = df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1), axis=0)
    return z * sign

# value z (cheap = 높은 값): 저PBR/저EV-EBITDA = cheap → z 부호 음(낮을수록 cheap) → -z 로 'cheap 높음' 정렬
val_pbr_z = xs_z(pbr, sign=-1)        # 저PBR=cheap → +z
val_ev_z  = xs_z(ev_ebitda, sign=-1)  # 저EV/EBITDA=cheap → +z
value_z = pd.concat([val_pbr_z, val_ev_z]).groupby(level=0).mean()  # 두 value 평균
quality_z = xs_z(roic, sign=1)        # 고ROIC → +z
mom_z = xs_z(mom, sign=1)

# 결합 signal: value + quality (동일 방향 평균 z)
vq_z = pd.concat([value_z, quality_z]).groupby(level=0).mean()

# ── 4. Rank-IC (Spearman) 월별 시계열 ──
def monthly_ic(signal_z, fwd):
    """월별 cross-section Spearman rank-IC. signal_z 높음 → fwd 높음 = 양 IC."""
    ics, ns, idx = [], [], []
    for m in signal_z.index:
        s = signal_z.loc[m]; r = fwd.loc[m] if m in fwd.index else None
        if r is None: continue
        df = pd.DataFrame({'s':s,'r':r}).dropna()
        if len(df) < 4: continue
        ic = stats.spearmanr(df.s, df.r).correlation
        if np.isnan(ic): continue
        ics.append(ic); ns.append(len(df)); idx.append(m)
    return pd.Series(ics, index=idx), pd.Series(ns, index=idx)

def block_boot_ci(ics, block=3, B=2000):
    """block bootstrap CI (자기상관 보정)."""
    arr = ics.values; n = len(arr)
    if n < block+1: return (np.nan, np.nan)
    nb = int(np.ceil(n/block))
    means = []
    for _ in range(B):
        starts = np.random.randint(0, n-block+1, nb)
        samp = np.concatenate([arr[s:s+block] for s in starts])[:n]
        means.append(samp.mean())
    return tuple(np.percentile(means, [2.5, 97.5]))

def wild_cluster_p(ics, block=3, B=2000):
    """wild-cluster(block) bootstrap p-value (H0: mean IC=0). Rademacher block weights."""
    arr = ics.values; n=len(arr); obs=arr.mean()
    if n < block+1: return np.nan
    demean = arr - obs
    nb = int(np.ceil(n/block))
    cnt=0
    for _ in range(B):
        w = np.repeat(np.random.choice([-1,1], nb), block)[:n]
        star = (demean * w).mean()
        if abs(star) >= abs(obs): cnt+=1
    return cnt/B

def eff_n(ics):
    """effective N = n/(1+2*sum rho_k) (시계열 자기상관 보정, fixed-b 정신)."""
    arr=ics.values; n=len(arr)
    if n<5: return n
    ac=[1.0]
    for k in range(1,min(n//4,12)):
        c=np.corrcoef(arr[:-k],arr[k:])[0,1]
        if np.isnan(c) or c<0: break
        ac.append(c)
    denom=1+2*sum(ac[1:])
    return n/max(denom,1)

def summarize(signal_z, fwd, label):
    ic, n = monthly_ic(signal_z, fwd)
    if len(ic)==0:
        return {'label':label,'ic_mean':None,'n_months':0}
    m=ic.mean(); ci=block_boot_ci(ic); wcp=wild_cluster_p(ic); en=eff_n(ic)
    se=ic.std()/np.sqrt(max(en,1)); t=m/se if se>0 else np.nan
    return {'label':label,'ic_mean':round(m,4),'ci_95':[round(ci[0],4),round(ci[1],4)],
            'wc_p':round(wcp,4),'n_months':len(ic),'eff_n':round(en,1),
            't_fixedb':round(t,2),'avg_universe_n':round(n.mean(),1)}

# ── 측정 실행 ──
results={'meta':{'universe':SEMI,'n_stocks':12,'split':'IS 2015-2021 / OOS 2022-2026',
                 'survivor_bias':'PARTIAL — 현 holdings only, historical membership 무료부재. TENTATIVE 상한',
                 'note':'value=저PBR/저EV-EBITDA z 평균, quality=ROIC z, vq=value+quality 결합'}}

masks={'full':slice(None),
       'IS':slice(None,IS_END),
       'OOS':slice('2022-01-01',None)}

for split,msk in masks.items():
    fwd = ret_fwd.loc[msk]
    res={}
    for sig_name, sig in [('value',value_z),('quality',quality_z),('value+quality',vq_z),('momentum_12_1',mom_z)]:
        res[sig_name]=summarize(sig.loc[msk], fwd, f"{sig_name}__{split}")
    results[split]=res

# ── sub-industry-neutral robustness (그룹내 demean 후 z) ──
def sub_neutral(df):
    out=df.copy()*np.nan
    grp=pd.Series(SUB)
    for m in df.index:
        row=df.loc[m]
        for g in set(SUB.values()):
            cols=[c for c in df.columns if SUB[c]==g]
            if len(cols)>=2:  # n=1 그룹(memory)은 demean시 0 → NaN 처리(정보소실 명시)
                out.loc[m,cols]=row[cols]-row[cols].mean()
    return out

vq_subneutral = pd.concat([xs_z(sub_neutral(pbr),-1), xs_z(sub_neutral(ev_ebitda),-1),
                           xs_z(sub_neutral(roic),1)]).groupby(level=0).mean()
results['sub_industry_neutral']={'value+quality':summarize(vq_subneutral, ret_fwd, 'vq__sub_neutral_full'),
    'note':'memory(MU) n=1 = demean시 신호소실(NaN). N_eff=8 MDE 0.091. ★robustness only'}

# ── decomposition γ: forward ~ value+quality (within), macro 통제는 단순화(시장초과) ──
# pooled panel OLS: ret_fwd_demean ~ vq_z, month-clustered. γ = vq_z 계수
def decomp_gamma(signal_z, fwd):
    rows=[]
    for m in signal_z.index:
        if m not in fwd.index: continue
        s=signal_z.loc[m]; r=fwd.loc[m]
        df=pd.DataFrame({'s':s,'r':r}).dropna()
        if len(df)<4: continue
        # within-month demean (시장공통 제거 = within-sector 성분)
        df['r_dm']=df.r-df.r.mean(); df['s_dm']=df.s-df.s.mean()
        rows.append(df[['r_dm','s_dm']].assign(month=m))
    if not rows: return None
    P=pd.concat(rows)
    # OLS slope + month-clustered SE (간이)
    x=P.s_dm.values; y=P.r_dm.values
    b=np.sum(x*y)/np.sum(x*x)
    resid=y-b*x
    # cluster by month
    Pp=P.assign(resid=resid,x=x)
    meat=Pp.groupby('month').apply(lambda g:(g.x*g.resid).sum(), include_groups=False)
    bread=1/np.sum(x*x)
    var=bread**2 * np.sum(meat**2)
    se=np.sqrt(var); t=b/se if se>0 else np.nan
    return {'gamma':round(b,5),'t_clustered':round(t,2),'n_obs':len(P),'n_months':P.month.nunique()}

results['decomposition']={'value+quality':decomp_gamma(vq_z, ret_fwd),
    'note':'within-month demean = within-sector 예측성분 γ. null(CI 0 or t<2) → (C) freeze'}

print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
with open('validation-vq-v1.json','w',encoding='utf-8') as f:
    json.dump(results,f,indent=2,ensure_ascii=False,default=str)
sys.stderr.write("\n[saved] validation-vq-v1.json\n")
