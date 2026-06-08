import pandas as pd, numpy as np
from scipy import stats

mkt = pd.read_parquet('/tmp/kr_mkt_ret.parquet')['mkt_ret']
rs = pd.read_parquet('study-research/eq_kr/industries/financial/raw-v3/data/regime_series.parquet')
rs.index = pd.to_datetime(rs.index)
fn = rs['foreign_net_kospi'].copy()      # daily KOSPI foreign net (억원-ish)
usdkrw = rs['usdkrw'].copy()
cli = rs['cli_kr'].copy()

# align to market trading days
df = pd.DataFrame({'mkt':mkt}).join(pd.DataFrame({'fn':fn,'usdkrw':usdkrw,'cli':cli}), how='left')
df['fn'] = df['fn'].fillna(0.0)           # no-trade day = 0 net
df['usdkrw'] = df['usdkrw'].ffill()
df['cli'] = df['cli'].ffill()
df = df.dropna(subset=['mkt'])

def nw_tstat(x, y, lags):
    # OLS y~x with Newey-West se on slope
    x = np.asarray(x); y=np.asarray(y)
    m = ~(np.isnan(x)|np.isnan(y)); x=x[m]; y=y[m]
    n=len(x)
    if n<30: return np.nan,np.nan,n
    X=np.column_stack([np.ones(n),x])
    b=np.linalg.lstsq(X,y,rcond=None)[0]
    resid=y-X@b
    XtX_inv=np.linalg.inv(X.T@X)
    S=(X*resid[:,None])
    # NW
    G=S.T@S
    for L in range(1,lags+1):
        w=1-L/(lags+1)
        Gl=S[L:].T@S[:-L]
        G+=w*(Gl+Gl.T)
    cov=XtX_inv@G@XtX_inv
    se=np.sqrt(np.diag(cov))
    t=b/se
    return b[1], t[1], n

def spearman_ic(sig, fwd):
    m=~(sig.isna()|fwd.isna())
    if m.sum()<30: return np.nan,np.nan,m.sum()
    r,p=stats.spearmanr(sig[m],fwd[m])
    return r,p,m.sum()

# Forward returns (overlapping daily, log compounded)
logr=np.log1p(df['mkt'])
for H in [5,21,63]:
    df[f'fwd{H}']=logr.shift(-1).rolling(H).sum().shift(-(H-1))  # next H days starting t+1
# correct fwd: future H-day cumulative starting next day
for H in [5,21,63]:
    fwd = logr[::-1].rolling(H).sum()[::-1].shift(-1)
    df[f'fwd{H}']=fwd

# Signals (all use info up to t, PIT-safe)
df['fn_5']  = df['fn'].rolling(5).sum()
df['fn_20'] = df['fn'].rolling(20).sum()
df['fn_60'] = df['fn'].rolling(60).sum()
# z-score of cumulative flow (expanding, min 252)
roll = df['fn'].rolling(252)
df['fn_z']  = (df['fn_20'] - df['fn_20'].rolling(252).mean())/df['fn_20'].rolling(252).std()
df['dusdkrw_20'] = -df['usdkrw'].pct_change(20)   # KRW strength (won 강세) = -dUSDKRW
df['cli_chg'] = df['cli'].diff(21)

print('=== Daily overlapping rank-IC (signal_t vs forward H-day return) ===')
print("%-12s%4s%9s%9s%8s%7s"%("signal","H","rankIC","p","NW-t","n"))
for sig in ['fn_5','fn_20','fn_60','fn_z','dusdkrw_20','cli_chg']:
    for H in [5,21,63]:
        ic,p,n=spearman_ic(df[sig],df[f'fwd{H}'])
        b,t,_=nw_tstat(df[sig].rank(pct=True),df[f'fwd{H}'],lags=H)
        print("%-12s%4d%9.3f%9.4f%8.2f%7d"%(sig,H,ic,p,t,n))
