"""tests/test_sleeve_belief_cov.py — ④ 자산 배분 belief 동적 공분산 (R15 배분 레이어).

검증 대상: regime_to_weights(belief, sleeve_regime_ids) 가 regime-conditional glasso Σ_eff 를
BL 공분산으로 주입하는 경로 + portfolio_orchestrator opt-in 무회귀.

핵심 (사용자 ④): 거시상황(belief b(t))에 따라 자산 배분 공분산이 *동적으로* 바뀐다.
substrate(sleeve_regime_ids) 부재 시 기존 정적 경로로 graceful(byte-identical 무회귀).
"""

import numpy as np
import pandas as pd
import pytest

from core.brain.macro_schema import Bloc, MacroView, RegimeEstimate, RegimeLabel, ViewStatus
from core.brain.regime_to_weights import regime_to_weights, _belief_conditional_cov, SLEEVES
from core.brain.regime_history import build_sleeve_regime_ids

LABELS = ("Reflation", "Recovery", "Overheat", "Stagflation")


def _view(label, conf, stance=None):
    est = RegimeEstimate(bloc=Bloc.USD, regime_now=label, confidence_now=conf)
    return MacroView(regimes={Bloc.USD: est}, status=ViewStatus.FRESH,
                     as_of_ts=0.0, stance=stance or {})


def _synth_returns(seed=0):
    """2-regime 슬리브 수익률 (regime 0=Recovery, 1=Overheat 상관구조 상이)."""
    rng = np.random.default_rng(seed)
    n_per = 70
    cols = list(SLEEVES)
    p = len(cols)
    # regime A: us_stock↔coin 동조 / regime B: gold↔bond 동조 (조건부 상관 = regime 따라 다름)
    cA = np.eye(p) * 0.02
    cA[0, 6] = cA[6, 0] = 0.012                       # us_stock-coin
    cB = np.eye(p) * 0.02
    cB[3, 4] = cB[4, 3] = 0.012                       # gold-bond
    XA = rng.normal(size=(n_per, p)) @ np.linalg.cholesky(cA).T
    XB = rng.normal(size=(n_per, p)) @ np.linalg.cholesky(cB).T
    X = np.vstack([XA, XB])
    idx = pd.date_range("2024-01-01", periods=2 * n_per, freq="W")
    rh = pd.DataFrame(X, columns=cols, index=idx)
    # labels index: Recovery=1, Overheat=2
    ids = np.array([1] * n_per + [2] * n_per, dtype=int)
    return rh, ids


def test_belief_conditional_cov_helper_dynamic():
    """④ 핵심(결정론): belief(거시상황) 변화 → regime-conditional Σ_eff 변화.

    BL solver feasibility 와 무관하게, belief 가 자산 배분 공분산을 실제로 바꾸는지(동적성)를
    helper 레벨에서 직접 검증. 같은 returns·regime substrate 라도 belief 다르면 Σ_eff 다름.
    """
    pytest.importorskip("sklearn")
    rh, ids = _synth_returns()
    b_overheat = {"Recovery": 0.05, "Overheat": 0.9, "Reflation": 0.025, "Stagflation": 0.025}
    b_recovery = {"Recovery": 0.9, "Overheat": 0.05, "Reflation": 0.025, "Stagflation": 0.025}

    out1 = _belief_conditional_cov(rh, ids, b_overheat, LABELS)
    out2 = _belief_conditional_cov(rh, ids, b_recovery, LABELS)
    assert out1 is not None and out2 is not None       # substrate 충족 → Σ_eff 산출
    cols1, S1 = out1
    cols2, S2 = out2
    assert cols1 == cols2 and S1.shape == (len(SLEEVES), len(SLEEVES))
    assert np.allclose(S1, S1.T, atol=1e-8)            # 대칭(PD 공분산)
    assert not np.allclose(S1, S2, atol=1e-6)          # belief 변화 → Σ_eff 변화 (동적성)
    # 결정론: 동일 입력 → 동일 Σ_eff (replay)
    cols3, S3 = _belief_conditional_cov(rh, ids, b_overheat, LABELS)
    assert np.allclose(S1, S3, atol=1e-12)


def test_belief_cov_injected_into_bl_path():
    """belief + ids + returns → BL 경로 강제 + Σ_eff 주입 caution + graceful weights.

    BL solver 성공(black_litterman_returns)이든 데이터 infeasible 시 fallback(ic_prior_fallback)
    이든 예외 없이 합=1 long-only 배분을 반환해야 한다(주입 시도 connectivity + graceful).
    """
    pytest.importorskip("pypfopt")
    pytest.importorskip("sklearn")
    rh, ids = _synth_returns()
    mv = _view(RegimeLabel.OVERHEAT, 0.85, {"us_stock": 0.5, "gold": -0.3})
    belief = {"Recovery": 0.1, "Overheat": 0.85, "Reflation": 0.025, "Stagflation": 0.025}

    res = regime_to_weights(mv, returns_history=rh, belief=belief,
                            sleeve_regime_ids=ids, labels=LABELS)
    assert any("belief_conditional_cov" in str(c) for c in res["caution"]), res["caution"]
    assert res["method"] in ("black_litterman_returns", "ic_prior_fallback"), res["method"]
    w = res["weights"]
    assert abs(sum(w.values()) - 1.0) < 1e-4
    assert all(v >= -1e-9 for v in w.values())        # long-only, 예외 없이 graceful


def test_bl_feasible_belief_changes_allocation_end_to_end():
    """연율화 fix 후 BL max_sharpe feasible → belief 변화가 *배분*까지 바꾼다 (end-to-end ④).

    btn-button(T2) 진단(주간 π≪연율 rf → infeasible)을 cov 연율화로 해소. solver 가 실제 풀리면
    belief 동적 Σ_eff 가 슬리브 weights 에 반영돼 거시상황별 배분이 달라진다.
    """
    pytest.importorskip("pypfopt")
    pytest.importorskip("sklearn")
    rh, ids = _synth_returns()
    mv = _view(RegimeLabel.OVERHEAT, 0.85, {"us_stock": 0.6, "gold": -0.4, "coin": 0.3})
    b1 = {"Recovery": 0.05, "Overheat": 0.9, "Reflation": 0.025, "Stagflation": 0.025}
    b2 = {"Recovery": 0.9, "Overheat": 0.05, "Reflation": 0.025, "Stagflation": 0.025}

    r1 = regime_to_weights(mv, returns_history=rh, belief=b1, sleeve_regime_ids=ids, labels=LABELS)
    r2 = regime_to_weights(mv, returns_history=rh, belief=b2, sleeve_regime_ids=ids, labels=LABELS)
    # 적어도 한쪽은 BL solver 가 풀려야(연율화 효과) — 둘 다 fallback 이면 fix 실패.
    assert "black_litterman_returns" in (r1["method"], r2["method"]), (r1["method"], r2["method"])
    v1 = np.array([r1["weights"][s] for s in SLEEVES])
    v2 = np.array([r2["weights"][s] for s in SLEEVES])
    assert not np.allclose(v1, v2, atol=1e-4)             # belief → 배분 변화 (end-to-end)


def test_no_substrate_graceful_static_path():
    """sleeve_regime_ids 부재 → belief 만 전달돼도 기존 정적 경로 (byte-identical 무회귀)."""
    rh, ids = _synth_returns()
    stance = {"us_stock": 0.5}
    mv = _view(RegimeLabel.OVERHEAT, 0.85, stance)
    belief = {"Overheat": 0.9, "Recovery": 0.1}

    base = regime_to_weights(mv, returns_history=rh, method="weight_tilt")
    with_belief = regime_to_weights(mv, returns_history=rh, method="weight_tilt",
                                    belief=belief, sleeve_regime_ids=None, labels=LABELS)
    assert base["weights"] == with_belief["weights"]      # substrate 없음 → 동일
    assert "belief_conditional_cov" not in str(with_belief["caution"])


def test_build_sleeve_regime_ids():
    """슬리브 regime substrate 빌더: returns_history.index → classify(as_of) → int id."""
    rh, _ = _synth_returns()

    class _Est:
        def __init__(self, lab): self.regime_now = type("L", (), {"value": lab})()
    class _View:
        def __init__(self, lab): self.regimes = {"USD": _Est(lab)} if lab else {}
    class _Clf:
        def __init__(self, dates):
            self.split = dates[len(dates) // 2]
        def classify(self, as_of=None):
            return _View("Recovery" if as_of < self.split else "Overheat")

    ids = build_sleeve_regime_ids(_Clf(list(rh.index)), rh, LABELS, bloc="USD")
    assert len(ids) == len(rh)
    assert set(np.unique(ids)) <= {1, 2}                   # Recovery=1, Overheat=2
    assert (ids == 1).sum() > 0 and (ids == 2).sum() > 0


def test_orchestrator_optin_off_no_regression(monkeypatch):
    """INV_R15_WEIGHTS off(기본) → belief 미산출, 정적 배분 (무회귀)."""
    from core.portfolio_orchestrator import PortfolioOrchestrator
    monkeypatch.delenv("INV_R15_WEIGHTS", raising=False)
    rh, ids = _synth_returns()
    mv = _view(RegimeLabel.OVERHEAT, 0.85, {"us_stock": 0.5})

    orch = PortfolioOrchestrator()
    res = orch.allocate(macro_view=mv, returns_history=rh, sleeve_regime_ids=ids)
    assert "r15_belief" not in res                          # off → belief 미산출
    assert abs(sum(res["weights"].values()) - 1.0) < 1e-4


def test_ic_corr_prior_optin_off_none(monkeypatch):
    """IC1/IC2 — opt-in off → corr_prior None (RegimeGlasso np.eye, byte-identical 무회귀)."""
    from core.brain.regime_to_weights import _ic_corr_prior
    monkeypatch.delenv("INV_R15_WEIGHTS", raising=False)
    assert _ic_corr_prior(list(SLEEVES)) is None


def test_ic_corr_prior_golden_deterministic(monkeypatch):
    """IC5 — corr_prior on 경로 golden + 결정성 (byte-identical CI 게이트).

    핫패스(regime_to_weights→_ic_corr_prior→build_seed_betas→factor_implied_cross_cov)는 RNG 0
    (conditional_correlation:60 공용유틸 RNG 미사용 / block_bootstrap_se=검정 전용 seed 고정).
    Λ=eye fallback(FRED 미가용 CI 시뮬)로 golden 안정 — 실 FRED Λ 의존 제거.
    """
    import datetime
    import sys
    from core.brain.regime_to_weights import _ic_corr_prior
    r2w = sys.modules["core.brain.regime_to_weights"]   # __init__ 함수 shadowing 우회
    monkeypatch.setenv("INV_R15_WEIGHTS", "true")
    today = datetime.date.today().isoformat()
    monkeypatch.setitem(r2w._STATIC_LAMBDA_CACHE, today, None)   # Λ=None → eye fallback

    cols = list(SLEEVES)
    cp1 = _ic_corr_prior(cols)
    cp2 = _ic_corr_prior(cols)
    assert cp1 is not None
    assert np.array_equal(cp1, cp2)                    # 결정성(byte-identical replay, RNG 0)

    i = {s: k for k, s in enumerate(cols)}
    # golden: SLEEVE_AGG(us_stock←cyc0.5+def0.5, commodity, gold) W roll-up, Λ=eye.
    # ★IC10(a) batch multivariate measured β 전면 교체(2026-06-01) 후 값 — 이전 0.4372/0.5260 은
    # M3 등급값(dollar −0.55 등) 기반. measured(dollar −0.171 등 약화 + vol factor 추가)로 갱신.
    # ★IC8 fx denomination factor(2026-06-02, 외부자문 2모델+코드검증 수렴 B): USD-표시 자산 공통 환노출
    #   (fx_β=절대 denomination 1.0, GLD 포함 full) + _static_factor_lambda eye fallback Λfx 축소.
    #   ★Λfx 0.09→0.15 정밀화(2026-06-02, 자문 band 0.15~0.20 하단 + falsification 실측 F1/F2/F4):
    #   naive (σ_fx/σ_asset)²=0.33 은 realized KRW corr(+0.17~0.20) over-load → 직교 할인(R²=0.268)+F4
    #   target 재현으로 0.15 확정. → us_stock×commodity 0.2642→0.2951, us_stock×gold 0.1994→0.249.
    #   ★fx_hedge="full" → us_stock×gold 0.0832 / us_stock×commodity 0.2026 정확 복원(IC10 불변).
    assert abs(cp1[i["us_stock"], i["commodity"]] - 0.2951) < 1e-3
    assert abs(cp1[i["us_stock"], i["gold"]] - 0.249) < 1e-3
    # 미매핑 sleeve(kr_stock/bond/cash/coin) = eye 독립 (자기 대각 외 0)
    for s in ("kr_stock", "bond", "cash", "coin"):
        off = np.delete(cp1[i[s]], i[s])
        assert np.allclose(off, 0.0, atol=1e-9), f"{s} 비독립: {off}"
    assert np.linalg.eigvalsh(cp1).min() > 0            # PSD


def test_orchestrator_optin_on_supplies_belief(monkeypatch):
    """INV_R15_WEIGHTS on + substrate → belief 동적 공분산 실주입 (connectivity)."""
    pytest.importorskip("pypfopt")
    pytest.importorskip("sklearn")
    from core.portfolio_orchestrator import PortfolioOrchestrator
    monkeypatch.setenv("INV_R15_WEIGHTS", "true")
    rh, ids = _synth_returns()
    mv = _view(RegimeLabel.OVERHEAT, 0.85, {"us_stock": 0.5, "gold": -0.3})

    orch = PortfolioOrchestrator()
    res = orch.allocate(macro_view=mv, returns_history=rh, sleeve_regime_ids=ids)
    assert "r15_belief" in res
    assert abs(sum(res["r15_belief"].values()) - 1.0) < 1e-6
    # belief 동적 공분산이 실제로 산출·주입됨 (solver 성공 여부는 데이터 의존 → method 완화).
    assert any("belief_conditional_cov" in str(c) for c in res.get("caution", []))
    assert abs(sum(res["weights"].values()) - 1.0) < 1e-4
