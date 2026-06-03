"""scripts/wire_study_falsification.py — study falsification 결선 runner (production 배선 ③).

train_weights.py(배선 ②)는 FRED→VintageStore→build_indicator_matrix(panel)→GlassoWeightLearner.fit
→ **카드 생성·registry 등록까지만** 하고 falsification(청산/재적합)이 없었다. weight_cycle.run_weight_cycle
은 카드→주입→score IC→DUAL falsification→route_lifecycle(청산)까지 **닫힌 함수**지만 production 호출처가
self-test 뿐이었다. 둘이 production 에서 한 번도 안 만나, study 의 confidence_hooks(hy_oas_risk_regime·
real_rate_duration_penalty 등)가 dead — score IC 실측이 confidence 로 누적 안 되고 prior 에 동결.

이 스크립트가 그 결선(배선 ③)이다:
  FRED(RealFredAdapter) → load_series_to_store(VintageStore) → build_indicator_matrix(PIT panel)
  → RegimeClassifier.classify(as_of) → regime_history(regime_ids) → GlassoWeightLearner.fit
  → StudyRegister.wire_falsification(= run_weight_cycle → route_lifecycle 청산 + dead-hook emit)

흐름: train_weights 의 substrate 빌드 절차를 그대로 재사용해 learner 를 만들고, study_register.
wire_falsification 으로 falsification cycle 을 닫는다. 그 결과 study hook 이 실 IC 로 활성된다.

⛔ 합성/데모 패널 금지(시스템 invariant). panel 은 실 FRED vintage. forward return 도 실 자산
   시계열에서만 — returns_provider 인자로 외부 주입(macro study 자체는 sleeve 가 없는 regime 엔진이라
   forward return 소스가 sleeve study/실 수익률에 의존, 이 경계는 호출자가 채운다).
⛔ opt-in(INV_R15_WEIGHTS) off = byte-identical. wire_falsification 이 off 면 즉시 None.
⛔ FRED key/외부망 부재 시 graceful skip(panel 빈/완전관측 부족 → 학습 skip). 환경 제약 ≠ 기능 부재.

실행:
  INV_R15_WEIGHTS=1 python scripts/wire_study_falsification.py \\
      --study study-research/macro/study_session.yaml --as-of 2026-05-30
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from core.assume.registry import AssumptionRegistry  # noqa: E402
from core.assume.update_controller import UpdateController  # noqa: E402
from core.assume.dag import AssumptionDAG  # noqa: E402
from core.assume.weight_cycle import GlassoWeightLearner  # noqa: E402
from core.brain.fred_adapter import RealFredAdapter, FRED_SERIES  # noqa: E402
from core.brain.regime_belief_adapter import REGIME_LABELS  # noqa: E402
from core.brain.regime_history import (  # noqa: E402
    build_regime_history, regime_id_series, valid_mask,
)
from core.data.vintage import VintageStore  # noqa: E402
from core.data.weight_panel import build_indicator_matrix  # noqa: E402
from core.study.study_register import StudyRegister, is_r15_enabled  # noqa: E402
from scripts.train_weights import load_series_to_store  # noqa: E402


# yaml indicator id → FRED series id 역매핑(fred_adapter.FRED_SERIES 는 fred_id→logical_name).
_NAME_TO_FRED = {name: fred_id for fred_id, name in FRED_SERIES.items()}


def _resolve_fred_ids(series_names: Sequence[str]) -> tuple[list, list]:
    """study weight_rules indicator(logical name) → FRED series id. 매핑 없는 건 분리 반환.

    (fred_ids, unmapped_names). unmapped = FRED 외 소스(FxStore dxy 등) → 실 panel 에서 제외(seam).
    """
    fred_ids, unmapped = [], []
    for nm in series_names:
        fid = _NAME_TO_FRED.get(nm)
        if fid is not None:
            fred_ids.append(fid)
        else:
            unmapped.append(nm)
    return fred_ids, unmapped


def wire_one_study(
    study_path: str,
    *,
    as_of: str,
    returns_provider=None,
    periods: Optional[Sequence[str]] = None,
    fred_api_key: Optional[str] = None,
    belief: Optional[dict] = None,
) -> dict:
    """study_session.yaml 1개를 결선 — 실 FRED panel → learner → wire_falsification.

    returns_provider(periods)->np.ndarray: 패널 행별 forward return 공급(실 자산 수익률). 미주입 시
      forward return 부재 → 학습/결선 skip(합성 금지). macro 처럼 sleeve 없는 regime 엔진은 호출자가
      downstream sleeve 실 수익률을 주입해야 결선 완결(이 경계가 sleeve study 의존 seam).
    periods: 학습 시점(YYYY-MM 행). 미주입 시 최근 36개월 기본 생성.
    belief: {regime_id(int): 확신도}. 미주입 시 {0:0.6, 1:0.4} 기본.

    반환: 결선 결과 dict(decision/dead-hook emit/n_obs) 또는 skip 사유.
    """
    if not is_r15_enabled():
        return {"skipped": "INV_R15_WEIGHTS off — production 경로 미개통(byte-identical 무회귀)"}

    reg = AssumptionRegistry()
    sr = StudyRegister(assumption_registry=reg)
    rep = sr.register(study_path)
    if not rep.ok:
        return {"skipped": "study 검증 실패(raw 게이트 등)", "errors": rep.errors}

    study_id = next(iter(sr.sessions))
    s = sr.sessions[study_id]

    # weight_rules indicator(dedup 순서) = learner 패널 series 순서(wire_falsification 과 정합).
    rules = [wr for wr in s.weight_rules if wr.indicator_id]
    order: list = []
    for wr in rules:
        if wr.indicator_id not in order:
            order.append(wr.indicator_id)
    fred_ids, unmapped = _resolve_fred_ids(order)
    if not fred_ids:
        return {"skipped": "FRED 매핑 indicator 0개(전부 외부 소스)", "unmapped": unmapped}

    # periods 기본: 최근 36개월(as_of 기준 역산).
    if periods is None:
        y, m = int(as_of[:4]), int(as_of[5:7])
        periods = []
        for _ in range(36):
            periods.append(f"{y:04d}-{m:02d}")
            m -= 1
            if m == 0:
                y, m = y - 1, 12
        periods = list(reversed(periods))

    # ① 실 FRED → VintageStore → PIT panel (합성 금지). 외부망/키 부재 시 panel 빈 → skip.
    fred = RealFredAdapter(api_key=fred_api_key or os.environ.get("FRED_API_KEY"),
                           pit_mode="vintage")
    if not fred.is_available():
        return {"skipped": "FRED unavailable(키/외부망 부재) — 환경 제약 ≠ 기능 부재. "
                           "team-lead PC(key+망)에서 재현 시 결선 자동 통과",
                "fred_ids": fred_ids, "unmapped": unmapped}

    store = VintageStore()
    added = load_series_to_store(store, fred, fred_ids, periods, as_of)
    panel = build_indicator_matrix(store, fred_ids, periods, as_of)

    # ② regime substrate(PIT classify) — 완전관측 AND regime 확보 행만 학습.
    from core.brain.regime_classifier import RegimeClassifier
    clf = RegimeClassifier(usd_adapter=fred)
    hist = build_regime_history(clf, periods)
    ids = regime_id_series(hist, periods, REGIME_LABELS)
    complete = ~np.isnan(panel.matrix).any(axis=1) if panel.matrix.size else np.array([], bool)
    mask = complete & valid_mask(ids)
    n_obs = int(mask.sum())
    if n_obs < 10:
        return {"skipped": f"완전관측+regime 행 {n_obs}<10(FRED/regime substrate 부족)",
                "added_cells": added, "n_obs": n_obs}

    # ③ forward return — 실 자산 수익률(returns_provider). 미주입 = 결선 미완(합성 금지).
    if returns_provider is None:
        return {"skipped": "returns_provider 미주입 — forward return(실 sleeve 수익률) 소스 필요. "
                           "macro=regime 엔진이라 downstream sleeve 실 수익률 의존(sleeve study seam)",
                "n_obs": n_obs, "panel_shape": list(panel.shape), "fred_ids": fred_ids}
    returns = np.asarray(returns_provider(periods), dtype=float)
    if returns.shape[0] != len(periods):
        return {"skipped": f"returns 길이 {returns.shape[0]} ≠ periods {len(periods)}"}

    # ④ learner.fit(실 panel 완전관측 행) → 결선(run_weight_cycle → 청산 + dead-hook emit)
    X = panel.matrix[mask]
    ids_v = ids[mask]
    ret_v = returns[mask]
    learner = GlassoWeightLearner(lam_floor=0.05).fit(X, ids_v)
    learned = sorted(set(int(r) for r in ids_v))
    b = belief or {r: (0.6 if r == learned[0] else 0.4 / max(len(learned) - 1, 1))
                   for r in learned}
    regime_id = (REGIME_LABELS[learned[0]] if learned[0] < len(REGIME_LABELS)
                 else str(learned[0]))
    uc = UpdateController(reg, validator=None, dag=AssumptionDAG(reg))

    out = sr.wire_falsification(
        study_id, learner, belief=b, returns=ret_v, regime_id=regime_id,
        uc=uc, as_of=as_of)
    return {"wired": True, "study_id": study_id, "n_obs": n_obs,
            "fred_ids": fred_ids, "unmapped_seam": unmapped, "regime_id": regime_id,
            "result": out}


def main() -> int:
    ap = argparse.ArgumentParser(description="study falsification 결선 runner(배선 ③)")
    ap.add_argument("--study", default="study-research/macro/study_session.yaml")
    ap.add_argument("--as-of", default="2026-05-30")
    args = ap.parse_args()

    res = wire_one_study(args.study, as_of=args.as_of)
    # Windows 콘솔 cp949 유니코드 깨짐 회피 — stdout UTF-8 강제(가능 시).
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(json.dumps(res, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
