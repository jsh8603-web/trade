"""ETF fallback alpha→beta 4중 잠금 테스트 (약변별 sleeve, 2026-06-06).

검증기준 (core/assume/etf_beta_lock.py):
① expected-alpha=0 선언 + falsification_metric 동반
② shadow-EW e-CUSUM: ETF≈EW 미발산 / 알파 발생·TE 드래그 발산 + 방향 식별
③ 대칭 promote-demote gate + hysteresis(ic_high>ic_low)
④ return-rank counterfactual 로깅(채택 X) + divergence rate
"""

from __future__ import annotations

import random
import sys
from datetime import datetime
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.assume.etf_beta_lock import EXPECTED_ALPHA, EtfBetaLock  # noqa: E402


def test_expected_alpha_zero_declaration():
    lock = EtfBetaLock("financial")
    assert lock.expected_alpha == 0.0 == EXPECTED_ALPHA
    assert lock.falsification_metric.strip()   # 반증불가=가정 아님


def test_decoupling_no_divergence_when_etf_tracks_ew():
    rng = random.Random(7)
    lock = EtfBetaLock("financial")
    for _ in range(80):
        ew = rng.gauss(0.0, 0.01)
        etf = ew + rng.gauss(0.0, 0.0005)   # TE 작음
        lock.observe_decoupling(etf, ew)
    assert not lock.decoupled()
    assert lock.decoupling_reason() == "none"


def test_decoupling_alpha_emergence_diverges():
    rng = random.Random(7)
    lock = EtfBetaLock("battery")
    for _ in range(80):
        ew = rng.gauss(0.0, 0.01)
        lock.observe_decoupling(ew + 0.004, ew)   # 지속 초과(알파)
    assert lock.decoupled()
    assert "alpha_emergence" in lock.decoupling_reason()
    assert lock.e_over > lock.e_under


def test_decoupling_te_drag_diverges():
    rng = random.Random(7)
    lock = EtfBetaLock("bio")
    for _ in range(80):
        ew = rng.gauss(0.0, 0.01)
        lock.observe_decoupling(ew - 0.004, ew)   # 지속 미달(TE 드래그)
    assert lock.decoupled()
    assert "te_drag" in lock.decoupling_reason()
    assert lock.e_under > lock.e_over


def test_symmetric_promote_demote_hysteresis():
    assert EtfBetaLock.promote_demote(0.50) == "promote"   # 변별력 회복
    assert EtfBetaLock.promote_demote(0.45) == "promote"   # 경계 포함
    assert EtfBetaLock.promote_demote(0.20) == "demote"    # 변별력 약
    assert EtfBetaLock.promote_demote(0.25) == "demote"
    assert EtfBetaLock.promote_demote(0.35) == "hold"      # deadband(whipsaw 차단)
    with pytest.raises(ValueError):
        EtfBetaLock.promote_demote(0.3, ic_high=0.2, ic_low=0.4)   # hysteresis 위반


def test_counterfactual_logging_no_adoption():
    lock = EtfBetaLock("auto")
    t = datetime(2026, 6, 6)
    e1 = lock.log_counterfactual(t, "KODEX 자동차", "KODEX 자동차")     # 동일
    e2 = lock.log_counterfactual(t, "KODEX 자동차", "KODEX 레버리지")   # 갈림
    assert e1.diverged is False and e2.diverged is True
    assert lock.counterfactual_divergence_rate == 0.5
    # 로깅만 — 채택(target_weight 등) 영향 없음(엔트리는 기록 전용 dataclass)
    assert len(lock.counterfactuals) == 2
