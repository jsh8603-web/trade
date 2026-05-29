"""scripts/train_weights.py — R15 가중학습 배치 오케스트레이터 (production 배선 ②).

학습/적용 분리(자문 §1.8 교정채널=offline): glasso 학습은 **배치**(여기), 라이브 결정 경로는
registry/store 의 학습 카드를 **조회만**(stock_track ③, down-only). 매 사이클 glasso fit 금지
(무거움·반사성). 본 스크립트는 주기 실행(cron/수동) → WeightAssumptionCard 를 registry/store 에 영속.

파이프(전부 substrate 확보됨 — .env FRED/KIS key 보유, production):
  ① FRED/KIS series vintage 적재(RealFredAdapter.get_series(as_of) → VintageStore)
  ② weight_panel.build_indicator_matrix(store, as_of) → IndicatorPanel(시점×지표, PIT)
  ③ regime_history.build_regime_history(RegimeClassifier(RealFredAdapter)) → regime_id_series
  ④ 완전관측+regime 확보 행만 → GlassoWeightLearner.fit(X, ids)  (regime 별 조건부 상관 학습)
  ⑤ regime 별 belief one-hot → build_weight_card(Ω·IC) → registry.register / store.put

⛔ 라이브 미접촉(배치 전용). FRED 외부망 차단(개발 샌드박스 504) 시 classify/get_series 가
degrade → 완전관측 행 부족 → 학습 skip(카드 0). production(사용자 PC, key+망) 에선 정상 학습.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np

from core.assume.registry import AssumptionRegistry
from core.assume.weight_card import WeightAssumptionCard
from core.assume.weight_cycle import GlassoWeightLearner, build_weight_card
from core.brain.regime_belief_adapter import REGIME_LABELS
from core.brain.regime_history import build_regime_history, regime_id_series, valid_mask
from core.data.weight_panel import build_indicator_matrix


# ---------------------------------------------------------------------------
# FRED/KIS series → VintageStore 적재 (PIT vintage)
# ---------------------------------------------------------------------------

def load_series_to_store(store, fred_adapter, series_ids: Sequence[str],
                         periods: Sequence[str], as_of) -> int:
    """RealFredAdapter.get_series(as_of) → VintageStore.add. 적재 셀 수 반환.

    각 series 의 as_of 시점 vintage(발표시점값)를 period 별로 store 에 적재. get_series 가 pd.Series
    (index=date) 반환 → period(YYYY-MM) 매칭 값. 실패/결측 = skip(완전관측 행에서 자동 제외).
    """
    added = 0
    for sid in series_ids:
        try:
            ser = fred_adapter.get_series(sid, as_of=as_of)
        except Exception:
            ser = None
        if ser is None:
            continue
        for period in periods:
            try:
                # pd.Series 라벨/부분문자열 매칭(YYYY-MM). 구현체별 robust 접근.
                val = None
                if hasattr(ser, "get"):
                    val = ser.get(period)
                if val is None and hasattr(ser, "index"):
                    for idx, v in zip(ser.index, list(ser)):
                        if str(idx).startswith(str(period)):
                            val = v
                            break
                if val is not None and np.isfinite(float(val)):
                    store.add(sid, period, float(val), vintage_knowable_from=as_of)
                    added += 1
            except Exception:
                continue
    return added


@dataclass
class TrainResult:
    cards: list                      # 등록된 WeightAssumptionCard (regime 별)
    n_obs: int                       # 학습 완전관측 행 수
    regimes_learned: list            # 학습된 regime id
    skipped_reason: Optional[str] = None


def train_weight_cards(
    *,
    store,
    fred_adapter,
    classifier,
    series_ids: Sequence[str],
    periods: Sequence[str],
    returns: Sequence[float],
    as_of,
    domain: str,
    scope: str,
    registry: AssumptionRegistry,
    labels: Sequence[str] = REGIME_LABELS,
    blend_1n: float = 0.3,
    cap: float = 0.4,
) -> TrainResult:
    """배치 학습 → regime 별 WeightAssumptionCard 를 registry 에 등록.

    periods = 학습 시점(행). returns = 각 시점 forward return(IC 산출, periods 와 동일 길이).
    완전관측 AND regime 확보 행만 학습(MDE 게이트는 호출자/validator). regime 별 one-hot belief
    카드 생성(라이브 belief-mix 는 적용 시점). FRED/regime 부족 시 skip(카드 0, reason 기록).
    """
    load_series_to_store(store, fred_adapter, series_ids, periods, as_of)
    panel = build_indicator_matrix(store, series_ids, periods, as_of)

    hist = build_regime_history(classifier, periods)
    ids = regime_id_series(hist, periods, labels)

    # 완전관측(NaN 없음) AND regime 확보(id≥0) 행
    complete = ~np.isnan(panel.matrix).any(axis=1) if panel.matrix.size else np.array([], bool)
    mask = complete & valid_mask(ids)
    n_obs = int(mask.sum())
    ret = np.asarray(returns, dtype=float)
    if n_obs < 10 or ret.shape[0] != len(periods):
        return TrainResult(cards=[], n_obs=n_obs, regimes_learned=[],
                           skipped_reason=f"완전관측+regime 행 {n_obs}<10 (FRED/regime substrate 부족)")

    X = panel.matrix[mask]
    ids_v = ids[mask]
    ret_v = ret[mask]
    learner = GlassoWeightLearner(lam_floor=0.05).fit(X, ids_v)

    cards = []
    learned = sorted(set(int(r) for r in ids_v))
    for r in learned:
        belief = {rr: (0.9 if rr == r else 0.1 / max(len(learned) - 1, 1)) for rr in learned}
        card = build_weight_card(
            learner, belief, ret_v, domain=domain, scope=scope,
            series_ids=series_ids, regime_id=labels[r] if r < len(labels) else str(r),
            blend_1n=blend_1n, cap=cap, n_eff=n_obs, valid_from=as_of)
        registry.register(card)
        cards.append(card)
    return TrainResult(cards=cards, n_obs=n_obs, regimes_learned=learned)


if __name__ == "__main__":
    from core.data.vintage import VintageStore

    rng = np.random.default_rng(20260530)
    P = 5
    periods = [f"2024-{m:02d}" for m in range(1, 13)] + [f"2025-{m:02d}" for m in range(1, 13)]
    series = ["CPI", "PMI", "RATE", "UNRATE", "SPREAD"]

    # mock FRED — series 별 합성 시계열(period→값). RealFredAdapter.get_series(as_of) 인터페이스 동형.
    class _MockSeries:
        def __init__(self, mapping): self.mapping = mapping; self.index = list(mapping)
        def get(self, k): return self.mapping.get(k)
        def __iter__(self): return iter(self.mapping.values())
    class _MockFred:
        def __init__(self):
            self.data = {s: {p: float(rng.normal(0, 1)) for p in periods} for s in series}
        def get_series(self, sid, as_of=None):
            return _MockSeries(self.data.get(sid, {}))

    # mock classifier — 전반부 Overheat, 후반부 Stagflation (조건부 상관 학습 substrate)
    class _Est:
        def __init__(self, lab): self.regime_now = type("L", (), {"value": lab})()
    class _View:
        def __init__(self, lab): self.regimes = {"USD": _Est(lab)}
    class _Clf:
        def classify(self, as_of=None):
            i = periods.index(as_of) if as_of in periods else 0
            return _View("Overheat" if i < 12 else "Stagflation")

    store = VintageStore()
    fred = _MockFred()
    clf = _Clf()
    reg = AssumptionRegistry()
    ret = list(rng.normal(0, 0.02, len(periods)))

    res = train_weight_cards(
        store=store, fred_adapter=fred, classifier=clf, series_ids=series, periods=periods,
        returns=ret, as_of="2025-12-31", domain="macro", scope="macro", registry=reg)

    print(f"1) 학습: n_obs={res.n_obs} regimes={res.regimes_learned} cards={len(res.cards)} "
          f"skip={res.skipped_reason}")
    assert res.skipped_reason is None and len(res.cards) >= 1, res
    # regime 별 카드 등록 확인 + 비중 정규화
    for c in res.cards:
        assert isinstance(c, WeightAssumptionCard)
        w = c.composed_weights()
        assert abs(np.abs(w).sum() - 1.0) < 1e-6, (c.id, np.abs(w).sum())
        assert reg.get(c.id) is not None
        print(f"   카드 {c.id}: w_sum=1 series={len(c.series_ids)} belief={c.belief_vector}")
    print(f"2) regime 별 카드 registry 등록 OK ({len(res.cards)}개)")

    # 3) substrate 부족(regime 단일/완전관측 부족) → skip graceful
    class _ClfMono:
        def classify(self, as_of=None): return _View(None)   # regime 미지 → 전부 -1
    res2 = train_weight_cards(
        store=VintageStore(), fred_adapter=fred, classifier=_ClfMono(), series_ids=series,
        periods=periods, returns=ret, as_of="2025-12-31", domain="macro", scope="macro",
        registry=AssumptionRegistry())
    assert res2.cards == [] and res2.skipped_reason is not None
    print(f"3) substrate 부족 → skip graceful: {res2.skipped_reason}")

    print("production ② train_weights self-test PASS "
          "(FRED 적재→panel→regime_history→glasso fit→regime별 카드→registry 영속)")
