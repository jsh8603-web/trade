"""core/brain/regime_history.py — 시점별 regime 시계열 substrate 빌더 (CL-W production 배선 ①).

R15 동적 가중학습(RegimeGlasso.fit(X, regime_ids))의 핵심 입력 = **각 학습 시점이 어느 거시
국면이었는지**(regime_ids). 이전엔 이 substrate 가 없어 라이브에서 동적 학습 불가였다.

해소: RegimeClassifier.classify(as_of=과거) 가 PIT 로 과거 시점 국면을 재구성한다
(RealFredAdapter.get_series(as_of) = ALFRED vintage 발표시점값, lookahead 차단). 이를 패널 각
행 날짜에 반복 호출 → 시점별 regime label 시계열 → RegimeGlasso regime_ids.

★PIT: classify(as_of=d) 는 d 시점에 발표돼 있던 데이터만 본다(vintage). 같은 period 라도 as_of
다르면 다른 regime(개정 반영). lookahead 누수 차단 = 학습이 미래 국면을 미리 못 봄.

⛔ FRED key 필요(production). 키 없거나 외부망 차단 시 classify 가 unavailable/last-good →
빌더가 None 라벨로 degrade(호출자가 완전관측 행만 학습). 환경 검증제약 ≠ 기능 부재.
"""

from __future__ import annotations

from typing import Optional, Sequence

import numpy as np


def build_regime_history(
    classifier,
    as_of_dates: Sequence,
    *,
    bloc=None,
) -> dict:
    """classify(as_of) 반복 → {as_of: regime_label or None}. RegimeGlasso regime_ids substrate.

    classifier = RegimeClassifier(RealFredAdapter). as_of_dates = 패널 행 날짜(PIT 학습 시점).
    각 시점 거시 국면을 vintage 로 재구성. classify 실패/unavailable → None(degrade, 호출자 제외).
    """
    try:
        from core.brain.macro_schema import Bloc
    except Exception:
        Bloc = None
    history: dict = {}
    for d in as_of_dates:
        try:
            mv = classifier.classify(as_of=d)
        except Exception:
            history[d] = None
            continue
        regimes = getattr(mv, "regimes", None) or {}
        key = bloc
        if key is None:
            key = (Bloc.USD if (Bloc is not None and Bloc.USD in regimes)
                   else (next(iter(regimes)) if regimes else None))
        est = regimes.get(key) if key is not None else None
        now = getattr(est, "regime_now", None)
        history[d] = getattr(now, "value", now) if est is not None else None
    return history


def regime_id_series(
    history: dict,
    panel_dates: Sequence,
    labels: Sequence[str],
) -> np.ndarray:
    """패널 각 행 날짜 → regime label → int id (RegimeGlasso regime_ids 입력).

    history[date] 가 labels 에 있으면 그 index, 없으면(None/미지) -1(호출자가 완전관측만 학습 시 제외).
    labels 순서 = effective_precision belief 키 순서와 일치(정합 필수).
    """
    label_to_id = {lab: i for i, lab in enumerate(labels)}
    out = np.full(len(panel_dates), -1, dtype=int)
    for i, d in enumerate(panel_dates):
        lab = history.get(d)
        if lab in label_to_id:
            out[i] = label_to_id[lab]
    return out


def valid_mask(regime_ids: np.ndarray) -> np.ndarray:
    """regime label 확보된 행(id≥0) 마스크. RegimeGlasso 는 미지 regime 행 제외 학습."""
    return np.asarray(regime_ids) >= 0


def build_sleeve_regime_ids(
    classifier,
    returns_history,
    labels: Sequence[str],
    *,
    bloc=None,
) -> np.ndarray:
    """슬리브 returns_history 각 행 날짜 → classify(as_of) → regime int id 배열 (④ 배선 a).

    R15 동적 가중(종목 판정)이 *지표* 패널에 regime substrate 를 붙였듯, 자산 배분(슬리브)도
    각 과거 시점이 어느 거시 국면이었는지 알아야 regime-conditional 공분산(Σ_eff)을 학습한다.
    returns_history.index(슬리브 수익률 시점) 를 PIT 학습 시점으로 보고 국면을 재구성한다.

    반환 = regime_to_weights(sleeve_regime_ids=) substrate. ⛔ 라이브 allocate 가 매 사이클 과거
    전체를 classify 하는 것은 무겁다(설계원칙 5: 학습=배치/적용=조회) → 배치 산출분을 조회 주입.
    classify 실패/미지 시점 → -1(RegimeGlasso 제외, graceful).
    """
    dates = list(getattr(returns_history, "index", returns_history))
    hist = build_regime_history(classifier, dates, bloc=bloc)
    return regime_id_series(hist, dates, labels)


if __name__ == "__main__":
    from datetime import date

    # mock classifier — FRED 없이 빌더 로직 검증(production 은 RegimeClassifier(RealFredAdapter)).
    class _MockEst:
        def __init__(self, label): self.regime_now = type("L", (), {"value": label})()
    class _MockView:
        def __init__(self, label): self.regimes = {"USD": _MockEst(label)} if label else {}
    class _MockClf:
        def __init__(self, mapping): self.mapping = mapping
        def classify(self, as_of=None): return _MockView(self.mapping.get(as_of))

    labels = ("Reflation", "Recovery", "Overheat", "Stagflation")
    dates = [date(2024, m, 1) for m in range(1, 7)]
    # 2024-01~03 Overheat, 04~05 Stagflation, 06 미지(None=데이터 부재)
    clf = _MockClf({dates[0]: "Overheat", dates[1]: "Overheat", dates[2]: "Overheat",
                    dates[3]: "Stagflation", dates[4]: "Stagflation", dates[5]: None})

    # 1) build_regime_history: 시점별 국면 재구성
    hist = build_regime_history(clf, dates, bloc="USD")
    assert hist[dates[0]] == "Overheat" and hist[dates[3]] == "Stagflation" and hist[dates[5]] is None
    print(f"1) build_regime_history OK: {[hist[d] for d in dates]}")

    # 2) regime_id_series: label → int id (labels 순서)
    ids = regime_id_series(hist, dates, labels)
    assert list(ids) == [2, 2, 2, 3, 3, -1], list(ids)   # Overheat=2, Stagflation=3, None=-1
    print(f"2) regime_id_series OK: {list(ids)} (Overheat=2 Stagflation=3 미지=-1)")

    # 3) valid_mask: 미지 regime 행 제외
    m = valid_mask(ids)
    assert list(m) == [True, True, True, True, True, False]
    assert int(m.sum()) == 5
    print(f"3) valid_mask OK: 완전관측 {int(m.sum())}/6 행 (미지 1행 제외)")

    # 4) classify 예외 → None degrade (환경 제약 graceful)
    class _BoomClf:
        def classify(self, as_of=None): raise RuntimeError("FRED 504")
    hist_b = build_regime_history(_BoomClf(), dates[:2])
    assert all(v is None for v in hist_b.values())
    print(f"4) classify 예외(FRED 504) → None degrade OK (환경제약 graceful)")

    print("CL-W regime_history self-test PASS "
          "(classify(as_of) PIT 반복 → 시점별 regime substrate → RegimeGlasso regime_ids)")
