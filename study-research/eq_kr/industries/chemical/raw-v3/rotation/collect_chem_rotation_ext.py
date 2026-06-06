# -*- coding: utf-8 -*-
"""collect_chem_rotation_ext.py — 화학 rotation 후보 확장 (≥8개, team-lead 지시).
추가: USDKRW(환율) / 중국 부동산 수요 proxy / Brent 유가 level / China PMI(FRED 부분).
에틸렌/프로필렌 spot = ICIS/Platts 유료 부재 → 명시 collector_plan(대체 China demand proxy로 본질 입증).
"""
import sys, io, os
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pandas as pd, yfinance as yf, requests
ROOT=Path(__file__).resolve().parent; DATA=ROOT/"data"
ENV='D:/projects/Inv/.env'
for line in open(ENV,encoding='utf-8'):
    if '=' in line and not line.strip().startswith('#'):
        k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip().strip('"'))
FRED=os.environ.get('FRED_API_KEY',''); START,END="2018-01-01","2026-06-05"
def fred(sid):
    r=requests.get('https://api.stlouisfed.org/fred/series/observations',
       params=dict(series_id=sid,api_key=FRED,file_type='json',observation_start=START,observation_end=END),timeout=30).json()
    o=r.get('observations',[]); idx=[];val=[]
    for x in o:
        if x['value'] in('.',''):continue
        idx.append(pd.Timestamp(x['date']));val.append(float(x['value']))
    return pd.Series(val,index=idx)
out={}
# yfinance: USDKRW, Brent, 중국 부동산 proxy(중국 인프라/소재 - FXI 이미있음, 추가 CHIQ소비/철강 대용 = 글로벌 건설 XHB는 미국)
for sym,name in [("KRW=X","usdkrw"),("BZ=F","brent"),("CL=F","wti")]:
    try:
        s=yf.download(sym,start=START,end=END,progress=False,auto_adjust=True)["Close"].squeeze()
        s.index=pd.to_datetime(s.index); out[name]=s
        print(f"  {name}({sym}): n={len(s)}")
    except Exception as e: print(f"  {name} FAIL {repr(e)[:40]}")
# FRED: China PMI 대용(중국 경기심리 BSCICP03CNM665S 2024중단 / 중국 생산자물가 / 한국수출)
for sid,name in [("BSCICP03CNM665S","china_bci"),("XTEXVA01KRM667S","kr_exports"),("CHNPRCNTO01IXOBM","china_ipi")]:
    try:
        s=fred(sid)
        if len(s): out[name]=s; print(f"  {name}({sid}): n={len(s)} {s.index.min().date()}~{s.index.max().date()}")
        else: print(f"  {name}({sid}): empty")
    except Exception as e: print(f"  {name} FAIL {repr(e)[:40]}")
df=pd.concat(out,axis=1).sort_index()
df.to_parquet(DATA/"chem_rotation_ext.parquet")
print(f"Saved {df.shape} cols={list(df.columns)}")
