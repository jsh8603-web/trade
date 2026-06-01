"""Fetch regional-Fed diffusion NEW ORDERS series for eq_us_cyclical merit follow-up.

Series (FRED, free):
  NOCDISA066MSFRBNY  - Empire State (NY Fed) new orders diffusion index  (2001-07~)
  NOCDFSA066MSFRBPHI - Philadelphia Fed new orders diffusion index       (1968-05~)

Both are diffusion indices (already 0-centered: + = expansion, - = contraction),
released at end of the SURVEY month (much more timely than census new-orders' 56-64d lag).

ALFRED first-release probe to confirm the ~current-month publication timing (live PIT).
No synthetic data: fetch failures raise.
"""
import os
import sys
import time
import json
from pathlib import Path

import requests
import pandas as pd

ROOT = Path(r'D:/projects/Inv/study-research/eq_us_cyclical/raw')
FRED_DIR = ROOT / 'fred'
FRED_DIR.mkdir(exist_ok=True)


def get_fred_key():
    for line in (Path(r'D:/projects/Inv/.env').read_text(encoding='utf-8', errors='ignore')).splitlines():
        if line.strip().startswith('FRED_API_KEY'):
            return line.split('=', 1)[1].strip().strip('"').strip("'")
    raise RuntimeError('FRED_API_KEY not found in .env')


KEY = get_fred_key()
BASE = 'https://api.stlouisfed.org/fred'

SERIES = ['NOCDISA066MSFRBNY', 'NOCDFSA066MSFRBPHI']


def fetch_series(series_id):
    url = f'{BASE}/series/observations'
    params = {'series_id': series_id, 'api_key': KEY, 'file_type': 'json'}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    obs = r.json()['observations']
    if not obs:
        raise RuntimeError(f'{series_id}: empty observations')
    df = pd.DataFrame(obs)[['date', 'value']]
    df.columns = ['observation_date', series_id]
    df[series_id] = pd.to_numeric(df[series_id], errors='coerce')
    df = df.dropna()
    out = FRED_DIR / f'{series_id}.csv'
    df.to_csv(out, index=False)
    print(f'  {series_id}: {df.observation_date.min()} -> {df.observation_date.max()} n={len(df)} -> {out.name}')
    return df


def probe_alfred_first_release(series_id, n_check=6):
    url = f'{BASE}/series/observations'
    params = {'series_id': series_id, 'api_key': KEY, 'file_type': 'json',
              'realtime_start': '1990-01-01', 'realtime_end': '9999-12-31',
              'output_type': '4'}
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        obs = r.json()['observations']
    except Exception as e:
        return {'series_id': series_id, 'error': str(e)}
    df = pd.DataFrame(obs)
    if df.empty:
        return {'series_id': series_id, 'error': 'empty vintage'}
    df['date'] = pd.to_datetime(df['date'])
    df['realtime_start'] = pd.to_datetime(df['realtime_start'])
    first = df.sort_values('realtime_start').groupby('date').first().reset_index()
    first = first.sort_values('date').tail(n_check + 24).dropna(subset=['realtime_start'])
    lags = (first['realtime_start'] - first['date']).dt.days
    return {
        'series_id': series_id,
        'median_pub_lag_days': float(lags.median()) if len(lags) else None,
        'max_pub_lag_days': float(lags.max()) if len(lags) else None,
        'min_pub_lag_days': float(lags.min()) if len(lags) else None,
        'n_vintage_obs': int(len(df)),
        'sample_recent': [
            {'period': str(d.date()), 'first_release_on': str(rs.date())}
            for d, rs in zip(first['date'].tail(n_check), first['realtime_start'].tail(n_check))
        ],
    }


if __name__ == '__main__':
    print('=== Fetch regional-Fed diffusion NEW ORDERS ===')
    for sid in SERIES:
        try:
            fetch_series(sid)
        except Exception as e:
            print(f'  !! {sid} FAILED: {e}')
            raise
        time.sleep(0.4)

    print('\n=== Probe ALFRED first-release pub lag (PIT) ===')
    pit = {}
    for sid in SERIES:
        info = probe_alfred_first_release(sid)
        pit[sid] = info
        if 'error' in info:
            print(f'  {sid}: ALFRED probe error: {info["error"]}')
        else:
            print(f'  {sid}: median pub lag {info["median_pub_lag_days"]}d '
                  f'(min {info["min_pub_lag_days"]}, max {info["max_pub_lag_days"]})')
        time.sleep(0.4)
    with open(ROOT / 'regional-fed-pit-probe.json', 'w') as f:
        json.dump(pit, f, indent=2)
    print(f'\nSaved PIT probe -> {ROOT / "regional-fed-pit-probe.json"}')
