#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Credential-free substitute probe for 4 credential-gated indicators.
Real 1-sample fetches only. No synthetic/estimated data.
"""
import os
import sys
import json
from pathlib import Path

results = {}


def load_fred_key():
    env = Path('D:/projects/Inv/.env')
    for line in env.read_text(encoding='utf-8', errors='ignore').splitlines():
        if line.startswith('FRED_API_KEY'):
            return line.split('=', 1)[1].strip()
    return None


FRED_KEY = load_fred_key()


def fred_info(sid):
    """get_series_info via fredapi; fallback to fredgraph CSV for n/range."""
    out = {'sid': sid}
    try:
        from fredapi import Fred
        fred = Fred(api_key=FRED_KEY)
        info = fred.get_series_info(sid)
        out['title'] = str(info.get('title', ''))[:80]
        out['observation_start'] = str(info.get('observation_start', ''))
        out['observation_end'] = str(info.get('observation_end', ''))
        out['frequency'] = str(info.get('frequency_short', ''))
        out['units'] = str(info.get('units_short', ''))
        s = fred.get_series(sid)
        s = s.dropna()
        out['n'] = int(len(s))
        if len(s):
            out['last_date'] = str(s.index[-1].date())
            out['last_value'] = float(s.iloc[-1])
            out['first_date'] = str(s.index[0].date())
        out['ok'] = True
    except Exception as e:
        out['ok'] = False
        out['error'] = f"{type(e).__name__}: {e}"
    return out


def fred_csv_probe(sid):
    """Unauthenticated fredgraph CSV fallback."""
    import requests
    import io
    import pandas as pd
    out = {'sid': sid, 'method': 'fredgraph_csv'}
    try:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
        r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        df.columns = ['date', 'value']
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df = df.dropna()
        out['n'] = int(len(df))
        if len(df):
            out['first_date'] = str(df['date'].iloc[0])
            out['last_date'] = str(df['date'].iloc[-1])
            out['last_value'] = float(df['value'].iloc[-1])
        out['ok'] = True
    except Exception as e:
        out['ok'] = False
        out['error'] = f"{type(e).__name__}: {e}"
    return out


# ============================================================
# 1. CUSHING crude inventory (EIA) -> FRED mirror series
# ============================================================
print("=== 1. CUSHING crude inventory (EIA FRED mirror) ===", flush=True)
cushing_candidates = [
    'WCESTUS1',   # Weekly US Ending Stocks Crude Oil ex SPR
    'WCRSTUS1',   # Weekly US Ending Stocks of Crude Oil
    'W_EPC0_SAX_YCUOK_MBBL',  # Cushing OK crude stocks (EIA code style)
    'WCSSTUS1',   # alt
]
results['1_cushing'] = {}
for sid in cushing_candidates:
    info = fred_info(sid)
    results['1_cushing'][sid] = info
    print(f"  {sid}: ok={info.get('ok')} n={info.get('n')} range={info.get('first_date')}~{info.get('last_date')} title={info.get('title','')[:50]}", flush=True)

# ============================================================
# 2. ROLL YIELD (futures term structure carry)
# ============================================================
print("\n=== 2. ROLL YIELD (futures term structure) ===", flush=True)
results['2_roll_yield'] = {}

# yfinance: CL=F is front-month continuous only
try:
    import yfinance as yf
    t = yf.Ticker("CL=F")
    h = t.history(period="5d")
    results['2_roll_yield']['yf_CL=F'] = {
        'ok': bool(len(h)),
        'n_rows': int(len(h)),
        'last_date': str(h.index[-1].date()) if len(h) else None,
        'last_close': float(h['Close'].iloc[-1]) if len(h) else None,
        'note': 'front-month continuous only; no multi-expiry term structure'
    }
    print(f"  yf CL=F: rows={len(h)} last_close={h['Close'].iloc[-1] if len(h) else None}", flush=True)
except Exception as e:
    results['2_roll_yield']['yf_CL=F'] = {'ok': False, 'error': f"{type(e).__name__}: {e}"}
    print(f"  yf CL=F ERROR: {e}", flush=True)

# FRED spot WTI
for sid in ['DCOILWTICO', 'DCOILBRENTEU']:
    info = fred_info(sid)
    results['2_roll_yield'][sid] = info
    print(f"  {sid}: ok={info.get('ok')} n={info.get('n')} last={info.get('last_value')}", flush=True)

# Possible curve/contango proxy on FRED? check none reliably exist; probe a couple
# (United States Oil Fund USO carries roll cost; CL front vs BZ etc are proxies, not term structure)
try:
    import yfinance as yf
    # Try fetching multiple specific-month WTI contracts (often unavailable on yahoo)
    for sym in ['CLF26.NYM', 'CLZ25.NYM']:
        try:
            hh = yf.Ticker(sym).history(period="5d")
            results['2_roll_yield'][f'yf_{sym}'] = {'ok': bool(len(hh)), 'n_rows': int(len(hh))}
            print(f"  yf {sym}: rows={len(hh)}", flush=True)
        except Exception as e2:
            results['2_roll_yield'][f'yf_{sym}'] = {'ok': False, 'error': str(e2)[:80]}
            print(f"  yf {sym} ERROR: {str(e2)[:60]}", flush=True)
except Exception:
    pass

# ============================================================
# 3. FORWARD EPS revision breadth (FINNHUB free tier)
# ============================================================
print("\n=== 3. FORWARD EPS revision breadth (FINNHUB free) ===", flush=True)
results['3_fwd_eps'] = {}


def finnhub_key():
    env = Path('D:/projects/Inv/.env')
    for line in env.read_text(encoding='utf-8', errors='ignore').splitlines():
        if line.startswith('FINNHUB_API_KEY') or line.startswith('FINNHUB'):
            return line.split('=', 1)[1].strip()
    return None


fk = finnhub_key()
results['3_fwd_eps']['finnhub_key_present'] = bool(fk)
if fk:
    import requests
    for endpoint, params in [
        ('recommendation', {'symbol': 'XLI'}),
        ('eps-estimate', {'symbol': 'AAPL', 'freq': 'quarterly'}),
    ]:
        try:
            url = f"https://finnhub.io/api/v1/stock/{endpoint}"
            p = dict(params)
            p['token'] = fk
            r = requests.get(url, params=p, timeout=20)
            results['3_fwd_eps'][endpoint] = {
                'status': r.status_code,
                'sample': str(r.json())[:200] if r.status_code == 200 else r.text[:200]
            }
            print(f"  finnhub {endpoint}: status={r.status_code} {str(r.json())[:120] if r.status_code==200 else r.text[:120]}", flush=True)
        except Exception as e:
            results['3_fwd_eps'][endpoint] = {'ok': False, 'error': str(e)[:120]}
            print(f"  finnhub {endpoint} ERROR: {str(e)[:80]}", flush=True)
else:
    print("  FINNHUB_API_KEY not in .env (free tier requires free signup)", flush=True)
    # Try anonymous to confirm gating
    try:
        import requests
        r = requests.get("https://finnhub.io/api/v1/stock/recommendation",
                         params={'symbol': 'XLI'}, timeout=15)
        results['3_fwd_eps']['anon_probe'] = {'status': r.status_code, 'body': r.text[:150]}
        print(f"  finnhub anon probe: status={r.status_code} body={r.text[:100]}", flush=True)
    except Exception as e:
        results['3_fwd_eps']['anon_probe'] = {'ok': False, 'error': str(e)[:120]}
        print(f"  finnhub anon ERROR: {str(e)[:80]}", flush=True)

# ============================================================
# 4. ISM / PMI regional Fed proxies (FRED free)
# ============================================================
print("\n=== 4. ISM/PMI regional Fed proxies (FRED) ===", flush=True)
results['4_pmi_proxy'] = {}
pmi_candidates = [
    ('GACDISA066MSFRBNY', 'Empire State Mfg General Activity'),
    ('NOCDISA066MSFRBNY', 'Empire State New Orders'),
    ('GACDFSA066MSFRBPHI', 'Philly Fed Mfg General Activity'),
    ('NOCDFSA066MSFRBPHI', 'Philly Fed New Orders'),
    ('BACTSAMFRBDAL', 'Dallas Fed Mfg General Business Activity'),
    ('KCFSI', 'KC Fed Financial Stress (control check)'),
    ('AMTMNO', 'Mfg New Orders (already loaded - ref)'),
    ('NEWORDER', 'Core capex new orders ex-aircraft (already loaded - ref)'),
]
for sid, desc in pmi_candidates:
    info = fred_info(sid)
    info['desc'] = desc
    results['4_pmi_proxy'][sid] = info
    print(f"  {sid} ({desc[:30]}): ok={info.get('ok')} n={info.get('n')} range={info.get('first_date')}~{info.get('last_date')} last={info.get('last_value')}", flush=True)

# ============================================================
out_path = Path('D:/projects/Inv/study-research/commodity/raw/probe_credential_free_results.json')
out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
print(f"\n=== Results written to {out_path} ===", flush=True)
