"""core/regime/pit_regime.py — regime PIT 태깅 + regime_model_version (T2-5).

SPEC T2-5: regime = PIT 가능 경제지표(수익률곡선·PMI)로 정의 + regime_model_version.
           D1 비모수(bnpy sticky HDP-HMM·ruptures) = 후순위. 고정-K(jumpmodels) baseline.

본 모듈은 T2 가 패널의 `regime_id` 를 *어떻게 정의하는지* 의 계약을 고정한다.
- **regime_model_version**: regime 정의가 바뀌면 버전을 올린다. dormant rule 부활·재현에 필수
  (FINDINGS §8 E축: "regime_model_version 필수"). cheapness_z 의 σ 가 regime 별이라
  regime 정의 변경은 cheapness_z 재현성에 직접 영향 → 반드시 버전 태깅.
- **PIT 안전**: 모든 입력 지표는 knowable_from ≤ as_of 인 vintage 값만 (silent revision 금지).
- **production 재사용**: 무거운 분류기는 `core/brain/regime_classifier.py`(JumpModel, 이미 라이브)
  가 SSOT. 본 모듈은 그 출력을 panel `regime_id` 로 정규화하는 얇은 어댑터 + 규칙 폴백.

regime id 규약 (고정-K=3, v1):
    0 = expansion/peak     (성장↑ · 수익률곡선 정상 · PMI>임계)
    1 = contraction/trough (성장↓ · 곡선 평탄/역전 · PMI<임계)
    2 = mid/transition     (그 사이)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

REGIME_MODEL_VERSION = "pit_fixedk3_v1"   # 정의 변경 시 bump (cheapness_z σ 재현성 직결)

REGIME_EXPANSION = 0
REGIME_CONTRACTION = 1
REGIME_MID = 2
REGIME_LABELS = {0: "expansion", 1: "contraction", 2: "mid"}


@dataclass(frozen=True)
class RegimeReading:
    regime_id: int
    model_version: str
    knowable_from: pd.Timestamp     # 이 판정에 쓰인 vintage 의 PIT 시점
    confidence: float = 1.0


def classify_pit(
    yield_curve_slope: float,       # 10y − 2y (또는 3m). 음수=역전
    pmi: float,                     # 제조업 PMI (50 기준)
    knowable_from,
    pmi_threshold: float = 50.0,
    slope_invert: float = 0.0,
) -> RegimeReading:
    """PIT 경제지표 → regime_id (고정-K=3 규칙 baseline).

    수익률곡선·PMI 만으로 결정론 분류 (jumpmodels 미설치/소표본 시 graceful degrade).
    production 은 regime_classifier(JumpModel) 출력을 adapt_classifier_output() 로 정규화.
    """
    kf = pd.Timestamp(knowable_from)
    if pmi >= pmi_threshold and yield_curve_slope > slope_invert:
        rid = REGIME_EXPANSION
    elif pmi < pmi_threshold and yield_curve_slope <= slope_invert:
        rid = REGIME_CONTRACTION
    else:
        rid = REGIME_MID
    # confidence = 두 신호 일치도
    agree = (pmi >= pmi_threshold) == (yield_curve_slope > slope_invert)
    return RegimeReading(rid, REGIME_MODEL_VERSION, kf, confidence=1.0 if agree else 0.6)


def adapt_classifier_output(regime_now: str | int) -> int:
    """regime_classifier(JumpModel/Investment Clock) 라벨 → panel regime_id 정규화.

    production 에서 brain 의 regime 산출을 패널 regime_id 로 매핑. 미지 라벨 = mid.
    """
    if isinstance(regime_now, (int, np.integer)):
        return int(regime_now) if int(regime_now) in REGIME_LABELS else REGIME_MID
    s = str(regime_now).lower()
    if any(k in s for k in ("expansion", "peak", "overheat", "boom", "bull")):
        return REGIME_EXPANSION
    if any(k in s for k in ("contraction", "trough", "recession", "stress", "bear", "panic")):
        return REGIME_CONTRACTION
    return REGIME_MID


def tag_panel_regime(panel: pd.DataFrame, indicators: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """패널에 regime_id 부여. indicators(date 인덱스, slope/pmi 컬럼) 주면 classify_pit,
    없으면 기존 regime_id 보존 + model_version 컬럼만 첨부 (fixture 는 이미 regime_id 보유).
    """
    out = panel.copy()
    if indicators is not None and {"slope", "pmi"}.issubset(indicators.columns):
        def _rid(row):
            d = pd.Timestamp(row["date"])
            past = indicators[indicators.index <= d]
            if past.empty:
                return REGIME_MID
            last = past.iloc[-1]
            return classify_pit(last["slope"], last["pmi"], d).regime_id
        out["regime_id"] = out.apply(_rid, axis=1)
    out["regime_model_version"] = REGIME_MODEL_VERSION
    return out


if __name__ == "__main__":
    r1 = classify_pit(yield_curve_slope=1.2, pmi=54, knowable_from="2021-06-30")
    r2 = classify_pit(yield_curve_slope=-0.3, pmi=47, knowable_from="2023-03-31")
    r3 = classify_pit(yield_curve_slope=0.1, pmi=49, knowable_from="2019-09-30")
    for r in (r1, r2, r3):
        print(f"regime={r.regime_id}({REGIME_LABELS[r.regime_id]}) conf={r.confidence} ver={r.model_version}")
    assert adapt_classifier_output("Recession") == REGIME_CONTRACTION
    assert adapt_classifier_output("overheat") == REGIME_EXPANSION
    print("regime PIT 태깅 + classifier adapt PASS")
