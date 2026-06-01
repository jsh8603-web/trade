#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Authenticated fredapi probe with throttling (avoid rate limit).
fredapi worked earlier (DCOILWTICO n=10168); rate-limit was the only issue.
One get_series call per sid (info skipped to halve request count), sleep between."""
import json
import time
from pathlib import Path


def load_fred_key():
    env = Path('D:/projects/Inv/.env')
    for line in env.read_text(encoding='utf-8', errors='ignore').splitlines():
        if line.startswith('FRED_API_KEY'):
            return line.split('=', 1)[1].strip()
    return None


from fredapi import Fred
fred = Fred(api_key=load_fred_key())


def probe(sid, retries=3):
    out = {'sid': sid}
    for attempt in range(retries):
        try:
            s = fred.get_series(sid).dropna()
            out['ok'] = True
            out['n'] = int(len(s))
            if len(s):
                out['first_date'] = str(s.index[0].date())
                out['last_date'] = str(s.index[-1].date())
                out['last_value'] = float(s.iloc[-1])
            return out
        except Exception as e:
            msg = str(e)
            if 'Too Many Requests' in msg and attempt < retries - 1:
                time.sleep(8)
                continue
            out['ok'] = False
            out['error'] = f"{type(e).__name__}: {msg[:80]}"
            return out
    return out


results = {}

print("=== CUSHING crude inventory candidates ===", flush=True)
results['cushing'] = {}
# Candidate FRED series for Cushing / US crude inventory
cushing = [
    'WCESTUS1',   # likely invalid (earlier 'does not exist')
    'WCRSTUS1',   # likely invalid
    'WCSSTUS1',
    'WCESTP21',   # PADD2 ex-SPR (Midwest, includes Cushing)
    'W_EPC0_SAX_YCUOK_MBBL',  # EIA Cushing native code
    'WTTSTUS1',   # total stocks
    'WCESTP31',
]
for sid in cushing:
    p = probe(sid)
    results['cushing'][sid] = p
    print(f"  {sid}: ok={p.get('ok')} n={p.get('n')} {p.get('first_date')}~{p.get('last_date')} last={p.get('last_value')} {p.get('error','')}", flush=True)
    time.sleep(2)

print("\n=== Mfg new orders (ISM substitute, confirm loaded) ===", flush=True)
results['mfg'] = {}
for sid in ['AMTMNO', 'NEWORDER', 'DGORDER', 'ACOGNO']:
    p = probe(sid)
    results['mfg'][sid] = p
    print(f"  {sid}: ok={p.get('ok')} n={p.get('n')} {p.get('first_date')}~{p.get('last_date')} last={p.get('last_value')}", flush=True)
    time.sleep(2)

print("\n=== Regional Fed PMI proxies ===", flush=True)
results['pmi'] = {}
pmi = [
    ('GACDISA066MSFRBNY', 'Empire State Mfg General Activity (diffusion)'),
    ('NOCDISA066MSFRBNY', 'Empire State New Orders'),
    ('GACDFSA066MSFRBPHI', 'Philly Fed Mfg General Activity'),
    ('NOCDFSA066MSFRBPHI', 'Philly Fed New Orders'),
    ('BACTSAMFRBDAL', 'Dallas Fed Mfg General Business Activity'),
    ('GAFDISA066MSFRBNY', 'Empire State alt'),
]
for sid, desc in pmi:
    p = probe(sid)
    p['desc'] = desc
    results['pmi'][sid] = p
    print(f"  {sid} ({desc[:32]}): ok={p.get('ok')} n={p.get('n')} {p.get('first_date')}~{p.get('last_date')} last={p.get('last_value')}", flush=True)
    time.sleep(2)

print("\n=== Brent spot ===", flush=True)
results['brent'] = probe('DCOILBRENTEU')
print(f"  DCOILBRENTEU: ok={results['brent'].get('ok')} n={results['brent'].get('n')} last={results['brent'].get('last_value')}", flush=True)

out = Path('D:/projects/Inv/study-research/commodity/raw/probe_fredapi_throttled_results.json')
out.write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
print(f"\nWritten {out}", flush=True)
