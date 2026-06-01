#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Search FRED for Cushing / crude inventory series (authenticated search API)."""
import json
import time
from pathlib import Path
import requests


def load_fred_key():
    env = Path('D:/projects/Inv/.env')
    for line in env.read_text(encoding='utf-8', errors='ignore').splitlines():
        if line.startswith('FRED_API_KEY'):
            return line.split('=', 1)[1].strip()
    return None


KEY = load_fred_key()
BASE = "https://api.stlouisfed.org/fred/series/search"

results = {}
for q in ['Cushing crude oil stocks', 'crude oil ending stocks SPR', 'Weekly Ending Stocks Crude Cushing']:
    try:
        r = requests.get(BASE, params={
            'search_text': q, 'api_key': KEY, 'file_type': 'json',
            'limit': 10, 'order_by': 'popularity', 'sort_order': 'desc'
        }, timeout=30)
        if r.status_code == 200:
            data = r.json()
            hits = []
            for s in data.get('seriess', []):
                hits.append({
                    'id': s.get('id'),
                    'title': s.get('title', '')[:70],
                    'freq': s.get('frequency_short'),
                    'start': s.get('observation_start'),
                    'end': s.get('observation_end'),
                })
            results[q] = hits
            print(f"\n### query: {q}", flush=True)
            for h in hits:
                print(f"  {h['id']:30s} {h['freq']:4s} {h['start']}~{h['end']}  {h['title']}", flush=True)
        else:
            results[q] = {'status': r.status_code, 'body': r.text[:150]}
            print(f"  query {q}: HTTP {r.status_code} {r.text[:100]}", flush=True)
    except Exception as e:
        results[q] = {'error': str(e)[:120]}
        print(f"  query {q} ERROR: {str(e)[:90]}", flush=True)
    time.sleep(3)

Path('D:/projects/Inv/study-research/commodity/raw/probe_cushing_search_results.json').write_text(
    json.dumps(results, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
print("\nWritten probe_cushing_search_results.json", flush=True)
