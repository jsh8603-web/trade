#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SOXX R6 G2 — XSD 광의 반도체 universe fetch (현 12종 + 중소형 21종 = breadth 확장).
EDGAR companyfacts(무료) value 신호 concept + yfinance 가격. SEC rate limit 준수(10 req/s).
★사전등록: XSD(SPDR S&P Semiconductor, EW, 중소형 포함). cap-weight 금지. 2018 이전 상장 = 장기.
산출: xsd_prices.parquet + xsd_edgar.parquet (raw-v3/).
"""
import urllib.request, json, time, pandas as pd, numpy as np, sys
import yfinance as yf

UA={'User-Agent':'sector-research test@example.com'}
# 현 12종 + 중소형 21종 (2018 이전 상장, G2 scope 확인됨)
CORE=['NVDA','AVGO','AMD','QCOM','TXN','MU','ADI','LRCX','KLAC','AMAT','INTC','MCHP']
SMALL=['MRVL','NXPI','SWKS','QRVO','MPWR','LSCC','RMBS','SLAB','POWI','DIOD','SMTC','MTSI','FORM','ACLS','UCTT','SYNA','CRUS','ON','COHU','MXL','AMBA']
ALL=CORE+SMALL
# value 신호 concept (fallback 태그 포함)
CMAP={
 'equity':['StockholdersEquity'],
 'op_income':['OperatingIncomeLoss'],
 'shares':['CommonStockSharesOutstanding','CommonStockSharesIssued'],
 'cash':['CashAndCashEquivalentsAtCarryingValue','CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents'],
 'lt_debt':['LongTermDebtNoncurrent','LongTermDebt'],
 'st_debt':['LongTermDebtCurrent','DebtCurrent'],
 'dep_amort':['DepreciationDepletionAndAmortization','DepreciationAmortizationAndAccretionNet'],
 'assets':['Assets'],'revenues':['Revenues','RevenueFromContractWithCustomerExcludingAssessedTax'],
 'cogs':['CostOfGoodsAndServicesSold','CostOfRevenue'],'gross_profit':['GrossProfit'],
 'net_income':['NetIncomeLoss'],
}

# ── SEC CIK 매핑 ──
req=urllib.request.Request('https://www.sec.gov/files/company_tickers.json',headers=UA)
with urllib.request.urlopen(req,timeout=30) as r:
    tk2cik={v['ticker']:str(v['cik_str']).zfill(10) for v in json.load(r).values()}

rows=[]
for i,tk in enumerate(SMALL):  # CORE는 기존 parquet 재사용, SMALL만 신규 fetch
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
                                rows.append({'ticker':tk,'concept':concept,'end':v['end'],'val':v['val'],
                                             'filed':v['filed'],'form':v.get('form','')})
                    break  # 첫 가용 태그만
        sys.stderr.write(f"[{i+1}/{len(SMALL)}] {tk} OK\n")
    except Exception as e:
        sys.stderr.write(f"{tk} ERR {str(e)[:60]}\n")
    time.sleep(0.15)  # SEC 10 req/s 준수

edg=pd.DataFrame(rows)
edg.to_parquet('xsd_edgar_small.parquet')
sys.stderr.write(f"[saved] xsd_edgar_small.parquet {edg.shape} ({edg.ticker.nunique()} tickers)\n")

# ── 가격 (SMALL만, CORE는 기존 재사용) ──
px=yf.download(SMALL,start='2014-06-01',end='2026-05-29',auto_adjust=True,progress=False)['Close']
px.to_parquet('xsd_prices_small.parquet')
sys.stderr.write(f"[saved] xsd_prices_small.parquet {px.shape}\n")
print(json.dumps({'small_n':len(SMALL),'edgar_rows':len(edg),'edgar_tickers':int(edg.ticker.nunique()),
                  'price_cols':list(px.columns),'price_range':[str(px.index.min().date()),str(px.index.max().date())]},
                 ensure_ascii=False))
