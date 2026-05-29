"""core/data/instrument_source.py — instrument PIT 데이터 소스 (IA-4·R4데이터).

P3 minimal scope = **crypto on-chain(CoinMetrics Community 무료) MVRV PIT provider + 최소
closed-loop**(PREDICTION_MADE→OUTCOME_OBSERVED→FDR_DECISION). ETF TR forward-only / 선물
roll_adjusted_return(price 출력 부재) / NAV regime-tag 는 DESIGN-inv-v2 §2-layer2 명세,
P4 확장 박제(N-P3-ETF/N-P3-FUT).

분담: **T2(core/structure/commodity_assumptions.py)가 MVRV *통계*(mean_revert AR(1)) 소유,
본 모듈은 MVRV *PIT 데이터*(vintage·knowable_from) 소유.** 통계는 이 provider 산출을 입력받는다.

CoinMetrics Community v4(무료, credential 불요): community-api.coinmetrics.io/v4/timeseries/
asset-metrics?assets=btc&metrics=CapMVRVCur. 라이브 네트워크 왕복은 go-live PC 검증(샌드박스
504) — 본체 + fixture 경계 테스트 + 라이브 이연(N-P3-CM 박제). proxy 금지(실 realized-cap).

★PIT: on-chain 지표도 vintage 가 있다. CoinMetrics 가 과거 realized-cap 을 재계산하면 같은 vt
의 값이 바뀜 → REVISION_OBSERVED 대상. 각 관측=(vt 데이터날짜, knowable_from 공표, value),
정정은 같은 vt + 늦은 sys_time row 로 append(2중 게이트로 PIT 조회).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional, Union

from core.data.event_ledger import EventLedger, reduce_events

AsOfLike = Union[str, date, datetime]


def _d(x: AsOfLike) -> date:
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    return datetime.fromisoformat(str(x)).date()


@dataclass(frozen=True)
class OnChainObservation:
    """bitemporal on-chain 관측 1건. 정정 = 같은 (asset,metric,vt) + 늦은 sys_time."""
    asset: str
    metric: str
    vt: date              # 데이터 날짜
    value: float
    knowable_from: date   # 공표/인지 시점 (보통 vt+1)
    sys_time: date        # 기록/정정 시점


class CoinMetricsMvrvProvider:
    """CoinMetrics Community MVRV PIT provider. fixture(기본) + 라이브 fetch(go-live)."""

    METRIC = "mvrv"

    def __init__(self, observations: Optional[list[OnChainObservation]] = None) -> None:
        self._obs: list[OnChainObservation] = list(observations or [])

    # --- 적재 (fixture/ingest) ------------------------------------------
    def add(self, asset: str, vt: AsOfLike, value: float, knowable_from: AsOfLike,
            *, sys_time: Optional[AsOfLike] = None, metric: str = METRIC) -> OnChainObservation:
        kf = _d(knowable_from)
        ob = OnChainObservation(asset.lower(), metric, _d(vt), float(value), kf,
                                _d(sys_time) if sys_time is not None else kf)
        self._obs.append(ob)
        return ob

    # --- PIT 조회 -------------------------------------------------------
    def get_point(self, asset: str, vt: AsOfLike, as_of: AsOfLike, *, metric: str = METRIC) -> Optional[float]:
        """(asset,metric,vt) 의 as_of PIT 값. knowable_from≤as_of AND sys_time≤as_of, 최신 sys_time."""
        a, v = _d(as_of), _d(vt)
        cands = [o for o in self._obs
                 if o.asset == asset.lower() and o.metric == metric and o.vt == v
                 and o.knowable_from <= a and o.sys_time <= a]
        if not cands:
            return None
        return max(cands, key=lambda o: o.sys_time).value

    def latest_knowable(self, asset: str, as_of: AsOfLike, *, metric: str = METRIC) -> Optional[OnChainObservation]:
        """as_of 시점에 알 수 있던 가장 최신 vt 의 관측(결정 신호용, 미래 vt lookahead 차단)."""
        a = _d(as_of)
        cands = [o for o in self._obs
                 if o.asset == asset.lower() and o.metric == metric
                 and o.knowable_from <= a and o.sys_time <= a]
        if not cands:
            return None
        # 최신 vt, 동률이면 최신 sys_time
        return max(cands, key=lambda o: (o.vt, o.sys_time))

    # --- 라이브 fetch (go-live, 네트워크) -------------------------------
    def fetch_live(self, asset: str, start: AsOfLike, end: AsOfLike) -> list[OnChainObservation]:
        """CoinMetrics Community v4 라이브 fetch(무료 tier). 네트워크 왕복=go-live PC 검증.

        knowable_from = vt+1(익일 공표 보수 가정), sys_time = fetch 일. 라이브 이연(N-P3-CM).
        """
        import json
        import urllib.parse
        import urllib.request

        url = ("https://community-api.coinmetrics.io/v4/timeseries/asset-metrics?"
               + urllib.parse.urlencode({
                   "assets": asset.lower(), "metrics": "CapMVRVCur",
                   "start_time": _d(start).isoformat(), "end_time": _d(end).isoformat(),
                   "frequency": "1d", "page_size": "10000"}))
        fetched_at = date.today()
        out: list[OnChainObservation] = []
        with urllib.request.urlopen(url, timeout=30) as resp:  # noqa: S310 (https 고정)
            data = json.loads(resp.read().decode("utf-8"))
        for row in data.get("data", []):
            vt = _d(row["time"][:10])
            val = row.get("CapMVRVCur")
            if val is None:
                continue
            ob = OnChainObservation(asset.lower(), self.METRIC, vt, float(val),
                                    vt + timedelta(days=1), fetched_at)
            self._obs.append(ob)
            out.append(ob)
        return out


# ---------------------------------------------------------------------------
# 최소 backtest closed-loop (PREDICTION_MADE → OUTCOME_OBSERVED → FDR_DECISION)
# ---------------------------------------------------------------------------

def _binom_p_onesided(hits: int, n: int) -> float:
    """k 이상 적중이 우연(p=0.5)일 단측 p-value(정규근사). scipy 미사용."""
    if n == 0:
        return 1.0
    z = (hits - n / 2.0) / math.sqrt(n / 4.0)
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def run_mvrv_closed_loop(
    ledger: EventLedger,
    provider: CoinMetricsMvrvProvider,
    prices: dict,                         # date -> close
    decision_dates: list,                 # 결정일 리스트 (as_of = 각 결정일, PIT)
    *,
    asset: str = "btc",
    mvrv_hi: float = 2.4,
    horizon_days: int = 7,
    assumption_id: str = "crypto.mvrv_mean_reverts",
) -> dict:
    """fixture MVRV + 가격으로 최소 closed-loop. 전 단계를 ledger 에 emit(PIT 무lookahead).

    각 결정일 D: as_of=D 에 알 수 있던 최신 MVRV(knowable_from≤D) > mvrv_hi → 'down' 예측
    (mean-revert). deadline=D+horizon, realized=price[D+h]/price[D]-1. hit=(realized<0)==('down').
    누적 후 FDR_DECISION(binomial p) 1건 emit. **신호는 D 이전 knowable MVRV 만(미래 vt 차단).**
    """
    pr = {_d(k): v for k, v in prices.items()}
    ledger.emit("ASSUMPTION_CREATED", tt=decision_dates[0], dt=decision_dates[0],
                vt=decision_dates[0], asset_class="crypto", assumption_id=assumption_id,
                payload={"version": 1, "statement": "MVRV regime-median mean-revert"})
    n_pred = hits = 0
    for D in decision_dates:
        Dd = _d(D)
        ob = provider.latest_knowable(asset, Dd)
        if ob is None or ob.value <= mvrv_hi:
            continue                       # 신호 없음(관망)
        deadline = Dd + timedelta(days=horizon_days)
        if Dd not in pr or deadline not in pr:
            continue
        pred_dir = "down"                  # MVRV 고평가 → mean-revert 하락 예측
        pred_id = ledger.emit(
            "PREDICTION_MADE", tt=Dd, dt=Dd, vt=ob.vt, asset_class="crypto",
            assumption_id=assumption_id,
            payload={"direction": pred_dir, "mvrv": ob.value, "mvrv_vt": ob.vt.isoformat(),
                     "horizon_h": horizon_days * 24, "deadline": deadline.isoformat()})
        # outcome (deadline 시점, as_of=deadline PIT)
        realized = pr[deadline] / pr[Dd] - 1.0
        hit = (realized < 0) == (pred_dir == "down")
        n_pred += 1
        hits += int(hit)
        ledger.emit(
            "OUTCOME_OBSERVED", tt=deadline, dt=deadline, vt=deadline, asset_class="crypto",
            assumption_id=assumption_id, parent_event_id=pred_id,
            payload={"series_key": f"pred:{pred_id}", "value": realized, "hit": hit})
    # FDR 결정 1건 (결정 필드 = write-time 동결)
    p_val = _binom_p_onesided(hits, n_pred)
    last = _d(decision_dates[-1]) + timedelta(days=horizon_days)
    ledger.emit(
        "FDR_DECISION", tt=last, dt=last, vt=last, asset_class="crypto",
        assumption_id=assumption_id,
        payload={"reject": p_val < 0.05, "p_value": p_val, "alpha_spent": 0.05,
                 "family_key": "crypto:mvrv", "account_type": "discovery",
                 "n": n_pred, "hits": hits})
    return {"n_pred": n_pred, "hits": hits, "p_value": p_val, "reject": p_val < 0.05}


if __name__ == "__main__":
    # --- fixture: btc MVRV vintage (vt 익일 공표) + 정정 1건 ----------------
    prov = CoinMetricsMvrvProvider()
    # 정상 관측: vt 2024-01-01..01-20, knowable=vt+1
    base_dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(20)]
    mvrv_vals = [2.0, 2.1, 2.5, 2.6, 2.7, 2.3, 2.2, 2.8, 2.9, 3.0,
                 2.4, 2.3, 2.6, 2.7, 2.5, 2.1, 2.0, 2.45, 2.5, 2.6]
    for d0, mv in zip(base_dates, mvrv_vals):
        prov.add("btc", d0, mv, d0 + timedelta(days=1))

    # 1) PIT get_point: vt 2024-01-03(=2.5) 는 knowable 01-04 → 01-03 미가시 / 01-04 가시
    assert prov.get_point("btc", "2024-01-03", "2024-01-03") is None, "공표 전 미가시"
    assert prov.get_point("btc", "2024-01-03", "2024-01-04") == 2.5
    print("1) MVRV PIT get_point: vt 01-03 공표 01-04 전 미가시/후 2.5 OK")

    # 2) latest_knowable: 미래 vt lookahead 차단 (as_of 01-05 → 최신 knowable vt=01-04)
    ob = prov.latest_knowable("btc", "2024-01-05")
    assert ob is not None and ob.vt == date(2024, 1, 4), ob.vt
    print(f"2) latest_knowable(as_of 01-05): 최신 knowable vt={ob.vt} (미래 vt 차단) OK")

    # 3) REVISION: vt 2024-01-03 realized-cap 정정 2.5→2.9 (sys_time 02-01)
    prov.add("btc", "2024-01-03", 2.9, knowable_from="2024-01-04", sys_time="2024-02-01")
    assert prov.get_point("btc", "2024-01-03", "2024-01-10") == 2.5, "정정 전 as_of=원본"
    assert prov.get_point("btc", "2024-01-03", "2024-02-05") == 2.9, "정정 후 as_of=정정값"
    print("3) MVRV 정정 PIT: vt 01-03 as_of 01-10→2.5 / 02-05→2.9 (vintage 정정) OK")

    # 4) ★최소 closed-loop: PREDICTION→OUTCOME→FDR ledger emit + PIT 무lookahead
    # 가격: 고MVRV 후 하락(mean-revert 성립)하도록 fixture
    prices = {}
    px = 42000.0
    all_dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(40)]
    for i, dd in enumerate(all_dates):
        # MVRV 고점(약 i=8~10) 후 하락 추세 부여
        px *= (0.99 if 8 <= i <= 20 else 1.003)
        prices[dd] = px
    decision_dates = [date(2024, 1, 6) + timedelta(days=i) for i in range(12)]
    led = EventLedger()
    summary = run_mvrv_closed_loop(led, prov, prices, decision_dates, mvrv_hi=2.4, horizon_days=7)
    state = led.project()
    n_pred_events = sum(1 for e in led._log if e.event_type == "PREDICTION_MADE")
    n_out_events = sum(1 for e in led._log if e.event_type == "OUTCOME_OBSERVED")
    n_fdr = sum(1 for e in led._log if e.event_type == "FDR_DECISION")
    assert n_pred_events == summary["n_pred"] == n_out_events, (n_pred_events, summary, n_out_events)
    assert n_fdr == 1 and n_pred_events > 0, (n_fdr, n_pred_events)
    print(f"4) closed-loop: 예측 {summary['n_pred']}건 적중 {summary['hits']} p={summary['p_value']:.3g} "
          f"reject={summary['reject']} (PREDICTION/OUTCOME/FDR ledger emit) OK")

    # 5) ★closed-loop replay 결정성: random-order 재구성 = 동일 state + FDR dt-순 불변
    import random
    shuffled = led._log[:]
    random.shuffle(shuffled)
    assert reduce_events(shuffled) == state, "closed-loop random-order 복원 실패"
    fdr = state.fdr_replay()
    assert len(fdr) == 1 and fdr[0]["family_key"] == "crypto:mvrv", fdr
    print("5) closed-loop replay: random-order 동일 state + FDR dt-순 동결 OK")

    # 6) ★무lookahead 검증: 모든 PREDICTION 의 신호 MVRV vt < 결정일 dt (미래 미사용)
    for e in led._log:
        if e.event_type == "PREDICTION_MADE":
            mvrv_vt = _d(e.payload["mvrv_vt"])
            assert mvrv_vt < e.dt.date(), f"lookahead: mvrv_vt {mvrv_vt} >= 결정일 {e.dt.date()}"
    print("6) 무lookahead: 전 예측의 신호 MVRV vt < 결정일(knowable PIT) OK")

    print("instrument_source (crypto MVRV PIT + 최소 closed-loop) self-test PASS")
