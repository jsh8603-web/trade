#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XLF(금융) minimal selection 검증 — universe fetch.
사전등록: XLF top-cap 29종(현 holdings 기준, 2016 이전 장기). EW 기준(cap-weight 금지).
섹터-적합 factor: value=P/B·P/TBV / quality=ROE·ROIC. ⛔EV/EBITDA 금융 무의미.
EDGAR companyfacts(무료) + yfinance 가격. SEC rate limit 준수.
★생존편향 flag: 현-holdings-only = 2023 SVB·Signature·First Republic 등 파산은행 누락 = value-IC upper-bound.
산출: xlf_prices.parquet + xlf_edgar.parquet.
"""
import urllib.request, json, time, pandas as pd, numpy as np, sys
import yfinance as yf
UA={'User-Agent':'sector-research test@example.com'}
XLF=['BRK-B','JPM','V','MA','BAC','GS','MS','WFC','C','AXP','SPGI','BLK','SCHW','CB','PGR','AON','ICE','CME','PNC','USB','TFC','COF','MET','AIG','TRV','PRU','AFL','ALL','BK']
# P/B·P/TBV·ROE·ROIC concept (금융 적합 + tangible book용 goodwill/intangibles)
CMAP={
 'equity':['StockholdersEquity'],
 'net_income':['NetIncomeLoss'],
 'shares':['CommonStockSharesOutstanding','CommonStockSharesIssued'],
 'goodwill':['Goodwill'],
 'intangibles':['IntangibleAssetsNetExcludingGoodwill','FiniteLivedIntangibleAssetsNet'],
 'assets':['Assets'],
 'op_income':['OperatingIncomeLoss'],
 'lt_debt':['LongTermDebtNoncurrent','LongTermDebt'],
}
req=urllib.request.Request('https://www.sec.gov/files/company_tickers.json',headers=UA)
with urllib.request.urlopen(req,timeout=30) as r:
    tk2cik={v['ticker']:str(v['cik_str']).zfill(10) for v in json.load(r).values()}
# BRK-B → BRK ticker 매핑 보정
alias={'BRK-B':'BRK-B','BRK.B':'BRK-B'}
rows=[]
for i,tk in enumerate(XLF):
    sec_tk=tk.replace('-B','').replace('.B','') if tk.startswith('BRK') else tk
    cik=tk2cik.get(tk) or tk2cik.get(sec_tk)
    if not cik: sys.stderr.write(f"{tk} CIK 부재\n");continue
    try:
        req=urllib.request.Request(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json',headers=UA)
        with urllib.request.urlopen(req,timeout=30) as r:
            gaap=json.load(r).get('facts',{}).get('us-gaap',{})
        for concept,tags in CMAP.items():
            for tag in tags:
                if tag in gaap:
                    for unit,vals in gaap[tag].get('units',{}).items():
                        for v in vals:
                            if 'end' in v and 'val' in v and v.get('filed'):
                                rows.append({'ticker':tk,'concept':concept,'end':v['end'],'val':v['val'],'filed':v['filed']})
                    break
        sys.stderr.write(f"[{i+1}/{len(XLF)}] {tk} OK\n")
    except Exception as e:
        sys.stderr.write(f"{tk} ERR {str(e)[:50]}\n")
    time.sleep(0.15)
edg=pd.DataFrame(rows)
edg.to_parquet('xlf_edgar.parquet')
sys.stderr.write(f"[saved] xlf_edgar.parquet {edg.shape} ({edg.ticker.nunique()} tk)\n")
px=yf.download(XLF,start='2014-06-01',end='2026-05-29',auto_adjust=True,progress=False)['Close']
px.to_parquet('xlf_prices.parquet')
print(json.dumps({'n':len(XLF),'edgar_rows':len(edg),'edgar_tk':int(edg.ticker.nunique()),
 'concept_cov':{c:int((edg.concept==c).sum()) for c in CMAP},
 'price_cols':int(px.shape[1]),'price_range':[str(px.index.min().date()),str(px.index.max().date())]},ensure_ascii=False))
