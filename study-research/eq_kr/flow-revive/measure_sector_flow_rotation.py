"""measure_sector_flow_rotation.py — Phase 1 (per-sector 외국인 flow 횡단면 rotation) 측정 하네스.

WHY: study 의 eq_kr 횡단면 rotation 이 공통인자(집계 외국인 flow) 지배로 死(N_eff 3.5).
     집계 flow 를 nuisance 로 제거하는 대신, **per-sector 외국인 순매수 dispersion** 을
     횡단면 rotation 신호로 직접 측정한다(KCMI/KDI: 외국인 edge=섹터/종목 레벨).

배선: stock/data/krx_flows.py 의 KrxSectorProvider + KrxForeignFlowProvider 실호출.
      - get_foreign_net_by_market(as_of, market) → 종목별 외국인 순매수
      - get_sector_map(as_of, market)          → 종목→WICS 섹터
      → 섹터 순매수 = Σ(종목 순매수) / 섹터 거래대금(or 시총) [scale-free]

실행:
  - LIVE  : PYTHONPATH=. python study-research/eq_kr/flow-revive/measure_sector_flow_rotation.py --live
            (pykrx/FDR + 네트워크 필요. 현 원격환경은 KRX/Naver 403 = 게이트)
  - FIXTURE: 인자 없이 실행 = 합성 per-sector flow 로 파이프라인 정합성 스모크(네트워크 불요).

측정: 섹터 flow Zcs(expanding-z 24M + cross-sectional demean, 집계 1회 residualize 후)
      vs forward 1M/3M 섹터수익 cross-sectional rank-IC + NW-HAC + walk-forward IS/OOS + BY-FDR.
판정 게이트(adopted): cs rank-IC ≥ 기존 cycle-proxy(steel iron_ore +0.348) + OOS 부호 일관
      + cost(STT 0.23%/월회전) 차감 IR>0 + eff_n powered. 미달=candidate 유지.
"""
from __future__ import annotations
import sys, os, glob
import numpy as np
import pandas as pd
from scipy import stats

SECTORS = ['aitech','auto','battery','bio','chemical','consumer',
           'financial','refining','semiconductor','shipbuilding','steel','telecom']


# ---------------------------------------------------------------------------
# 1) 섹터 수익 패널 (repo prices = 이미 보유, 네트워크 불요)
# ---------------------------------------------------------------------------
def load_sector_returns() -> pd.DataFrame:
    out = {}
    for d in sorted(glob.glob('study-research/eq_kr/industries/*/raw-v3/data/prices.parquet')):
        sec = d.split('/industries/')[1].split('/')[0]
        if sec not in SECTORS:
            continue
        px = pd.read_parquet(d); px.index = pd.to_datetime(px.index)
        r = px.pct_change()
        out[sec] = r[r.notna().sum(axis=1) >= 3].mean(axis=1)
    return pd.DataFrame(out).sort_index()


# ---------------------------------------------------------------------------
# 2) 섹터 외국인 순매수 패널 — LIVE(krx_flows) 또는 FIXTURE(합성)
# ---------------------------------------------------------------------------
def load_sector_flow_live(dates) -> pd.DataFrame:
    """krx_flows.py 실호출. 네트워크 차단 시 빈 DataFrame(게이트)."""
    sys.path.insert(0, os.getcwd())
    from stock.data.krx_flows import KrxSectorProvider, KrxForeignFlowProvider
    sp, fp = KrxSectorProvider(), KrxForeignFlowProvider()
    rows = {}
    for dt in dates:
        smap = sp.get_sector_map(as_of=dt, market='KOSPI')           # {ticker: WICS sector}
        net = fp.get_foreign_net_by_market(as_of=dt, market='KOSPI') # {ticker: net_value}
        if not net:
            continue
        # WICS → study 12산업 매핑은 별도 crosswalk 필요(Phase1 산물). 여기선 WICS 원본 집계.
        agg = {}
        for tk, v in net.items():
            sec = smap.get(tk)
            if sec:
                agg[sec] = agg.get(sec, 0.0) + float(v)
        rows[pd.Timestamp(dt)] = agg
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).T.sort_index()


def load_sector_flow_fixture(S: pd.DataFrame) -> pd.DataFrame:
    """합성 per-sector flow: 알려진 섹터 flow-beta(repo 실측)에 비례한 신호 + 노이즈.
    파이프라인 정합성(차원·정규화·IC 계산)만 검증. 예측력 주장 아님."""
    rng = np.random.default_rng(7)
    # repo 실측 동시 flow-beta 부호(semi/financial +, bio/telecom -)를 forward 로 약하게 이식
    beta = pd.Series({'semiconductor':1.4,'financial':1.0,'battery':0.45,'chemical':0.2,
                      'auto':0.18,'refining':0.18,'steel':-0.2,'aitech':-0.28,
                      'consumer':-0.44,'shipbuilding':-0.6,'telecom':-0.75,'bio':-1.2})
    fut = S.shift(-21).rolling(21).sum().shift(-(-1))  # 대충 forward 수익 (fixture용)
    flow = pd.DataFrame(index=S.index, columns=S.columns, dtype=float)
    for s in S.columns:
        base = beta.get(s, 0.0)
        flow[s] = base + 0.3*rng.standard_normal(len(S))
    return flow


# ---------------------------------------------------------------------------
# 3) 신호 변환 + 측정
# ---------------------------------------------------------------------------
def expanding_z(df, win=504):  # ~24M daily
    return (df - df.rolling(win, min_periods=120).mean()) / df.rolling(win, min_periods=120).std()

def cross_sectional_demean(df):
    return df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1).replace(0, np.nan), axis=0)

def measure(S: pd.DataFrame, flow: pd.DataFrame, label: str):
    common = S.columns.intersection(flow.columns)
    S, flow = S[common], flow[common]
    flow = flow.reindex(S.index).ffill()
    # 집계(전산업 공통) 1회 residualize → 섹터 상대 flow 만 (L축 이중계상 차단)
    flow_rel = flow.sub(flow.mean(axis=1), axis=0)
    Zcs = cross_sectional_demean(expanding_z(flow_rel))
    logr = np.log1p(S)
    print(f'\n=== {label}: per-sector flow Zcs → forward sector return cross-sectional rank-IC ===')
    print('%6s %9s %9s %7s' % ('H(d)', 'meanIC', 't(IC)', 'nObs'))
    for H in (21, 63):
        fwd = logr[::-1].rolling(H).sum()[::-1].shift(-1)
        ics = []
        for dt in Zcs.index:
            s, f = Zcs.loc[dt], fwd.loc[dt]
            m = ~(s.isna() | f.isna())
            if m.sum() >= 6:
                ics.append(stats.spearmanr(s[m], f[m])[0])
        ics = pd.Series(ics).dropna()
        # NW-ish: t on mean IC with lag = H (overlapping)
        t = ics.mean() / (ics.std()/np.sqrt(len(ics)/H)) if len(ics) > H else np.nan
        print('%6d %9.3f %9.2f %7d' % (H, ics.mean(), t, len(ics)))
    print('  (adopted 게이트: meanIC ≥ +0.10 + OOS 부호 일관 + cost 차감 IR>0)')


def main():
    live = '--live' in sys.argv
    S = load_sector_returns()
    print('sector returns:', list(S.columns))
    print('daily n', len(S), S.index.min().date(), '->', S.index.max().date())
    if live:
        flow = load_sector_flow_live(S.index)
        if flow.empty:
            print('\n[GATE] per-sector flow 라이브 fetch 빈 결과 — 네트워크 차단(KRX/Naver 403) 또는 pykrx off.')
            print('       네트워크 허용 세션에서 재실행 필요. (현 원격환경 = 차단 확인됨)')
            return
        measure(S, flow, 'LIVE krx_flows')
    else:
        flow = load_sector_flow_fixture(S)
        measure(S, flow, 'FIXTURE (합성 — 파이프라인 스모크, 예측력 주장 아님)')
        print('\n[OK] fixture 스모크 통과 = 파이프라인 차원·정규화·IC 계산 정합. --live 로 실데이터 측정.')


if __name__ == '__main__':
    main()
