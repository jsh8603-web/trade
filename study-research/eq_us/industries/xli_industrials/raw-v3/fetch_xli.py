#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XLI(산업재) minimal selection 검증 — universe fetch (마지막 early-stop 체크).
사전등록: XLI top-cap 39종(현 holdings, 2016이전 장기, EW). breadth 큼(메가캡 비지배).
섹터-적합 factor: value=EV/EBITDA·FCF-yield / quality=ROIC·gross profitability. (산업재=실물자본, EV 계열 우선)
EDGAR companyfacts + yfinance. SEC rate limit 준수.
"""
import urllib.request, json, time, pandas as pd, numpy as np, sys
import yfinance as yf
UA={'User-Agent':'sector-research test@example.com'}
XLI=['GE','CAT','RTX','HON','UNP','BA','LMT','DE','UPS','ETN','ADP','GD','NOC','EMR','ITW','CSX','MMM','FDX','NSC','WM','PH','TT','CTAS','TDG','PCAR','CMI','PWR','RSG','JCI','AME','ROK','FAST','URI','PAYX','VRSK','EFX','DOV','XYL','WAB']
# value=EV/EBITDA(op_income+D&A+debt-cash) + FCF-yield(op_cashflow-capex)/mcap / quality=ROIC + gross profitability(GP/assets)
CMAP={
 'op_income':['OperatingIncomeLoss'],'dep_amort':['DepreciationDepletionAndAmortization','DepreciationAmortizationAndAccretionNet'],
 'lt_debt':['LongTermDebtNoncurrent','LongTermDebt'],'st_debt':['LongTermDebtCurrent','DebtCurrent'],
 'cash':['CashAndCashEquivalentsAtCarryingValue'],'shares':['CommonStockSharesOutstanding','CommonStockSharesIssued'],
 'op_cashflow':['NetCashProvidedByUsedInOperatingActivities'],'capex':['PaymentsToAcquirePropertyPlantAndEquipment'],
 'equity':['StockholdersEquity'],'assets':['Assets'],'gross_profit':['GrossProfit'],
 'revenues':['Revenues','RevenueFromContractWithCustomerExcludingAssessedTax'],'cogs':['CostOfGoodsAndServicesSold','CostOfRevenue'],
}
req=urllib.request.Request('https://www.sec.gov/files/company_tickers.json',headers=UA)
with urllib.request.urlopen(req,timeout=30) as r:
    tk2cik={v['ticker']:str(v['cik_str']).zfill(10) for v in json.load(r).values()}
rows=[]
for i,tk in enumerate(XLI):
    cik=tk2cik.get(tk)
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
        sys.stderr.write(f"[{i+1}/{len(XLI)}] {tk} OK\n")
    except Exception as e:
        sys.stderr.write(f"{tk} ERR {str(e)[:50]}\n")
    time.sleep(0.15)
edg=pd.DataFrame(rows);edg.to_parquet('xli_edgar.parquet')
sys.stderr.write(f"[saved] xli_edgar.parquet {edg.shape} ({edg.ticker.nunique()} tk)\n")
px=yf.download(XLI,start='2014-06-01',end='2026-05-29',auto_adjust=True,progress=False)['Close']
px.to_parquet('xli_prices.parquet')
print(json.dumps({'n':len(XLI),'edgar_rows':len(edg),'edgar_tk':int(edg.ticker.nunique()),
 'concept_cov':{c:int((edg.concept==c).sum()) for c in CMAP},'price_cols':int(px.shape[1])},ensure_ascii=False))
