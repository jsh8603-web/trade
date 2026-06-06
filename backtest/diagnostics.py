"""backtest/diagnostics.py — P2-3 문제정의·벤치마크 측정 스크립트.

plan-final-test §3. 단일 수익률 금지(상수 오염 위험) → 4층 동시 산출:
  (a) 연결성  (b) 신호품질(rank-IC·hit, scale-invariant)  (c) 리스크조정(Sharpe/Sortino/MDD)
  (d) 초과수익(vs 외부 벤치)
+ per-asset attribution(★self-ref base 금지 — 외부 buy&hold base)
+ 3차 게이트(① n ② Newey-West HAC t ③ block-bootstrap CI ④ walk-forward 부호일관).

재사용(중복 0): common/metrics(sharpe/sortino/mdd/calmar/cagr/returns_from_equity),
  core.assume.weight_falsification.rank_ic, core.assume.spanning_gate._nw_lags.
신규: nw_hac_tstat(평균), block_bootstrap_ci, per_asset_attribution, confirm_gate, four_layer_metrics.

★메모리 anchor: coin rank-IC −0.10 도 overlapping 자기상관 미보정 caveat → IID 금지(block bootstrap),
  단일 측정 단정 금지(4기준 게이트 미충족 시 "문제 의심" 한정).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from common.metrics import (
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_max_drawdown,
    calculate_calmar_ratio,
    calculate_cagr,
    returns_from_equity,
)
from core.assume.weight_falsification import rank_ic
from core.assume.spanning_gate import _nw_lags


# ────────────────────────────────────────────────────────────────────
# (b) 신호품질 — scale-invariant (NAV 상수오염 면역)
# ────────────────────────────────────────────────────────────────────
def hit_rate(scores: Sequence[float], fwd_returns: Sequence[float]) -> float:
    """부호 일치율 = mean(sign(score) == sign(forward_return))."""
    s = np.asarray(scores, float)
    r = np.asarray(fwd_returns, float)
    if s.size == 0 or s.size != r.size:
        return 0.0
    return float(np.mean(np.sign(s) == np.sign(r)))


# ────────────────────────────────────────────────────────────────────
# 3차 게이트 ② Newey-West HAC t-stat (평균이 0과 다른가, 자기상관 보정)
# ────────────────────────────────────────────────────────────────────
def nw_hac_tstat(x: Sequence[float], lags: Optional[int] = None) -> tuple[float, int, int]:
    """시계열 평균의 Newey-West HAC t-stat. 반환 (t, n, lags).

    IID t-test 는 자기상관(regime persistence) 시 과대신뢰 → Bartlett 가중 HAC SE 로 보정.
    lags=None → _nw_lags(n) 자동.
    """
    a = np.asarray(x, float)
    a = a[~np.isnan(a)]
    n = a.size
    if n < 3:
        return (0.0, int(n), 0)
    L = _nw_lags(n) if lags is None else int(lags)
    L = max(0, min(L, n - 1))
    mu = a.mean()
    e = a - mu
    var = float(e @ e) / n  # gamma0
    for k in range(1, L + 1):
        w = 1.0 - k / (L + 1)            # Bartlett 커널
        gk = float(e[k:] @ e[:-k]) / n
        var += 2.0 * w * gk
    if var <= 0:
        return (0.0, int(n), int(L))
    se = float(np.sqrt(var / n))
    return ((float(mu / se) if se > 0 else 0.0), int(n), int(L))


# ────────────────────────────────────────────────────────────────────
# 3차 게이트 ③ block-bootstrap CI (IID 금지 — 자기상관 블록 보존)
# ────────────────────────────────────────────────────────────────────
def block_bootstrap_ci(
    x: Sequence[float],
    n_boot: int = 2000,
    block: Optional[int] = None,
    ci: float = 0.95,
    seed: int = 0,
) -> tuple[float, float, float]:
    """평균의 circular block-bootstrap CI. 반환 (lo, mean, hi).

    block=None → max(1, n//10) (자기상관 decay 근사). IID resample 금지(인접 자기상관 보존).
    """
    a = np.asarray(x, float)
    a = a[~np.isnan(a)]
    n = a.size
    if n < 3:
        return (0.0, float(a.mean()) if n else 0.0, 0.0)
    b = max(1, n // 10) if block is None else max(1, int(block))
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / b))
    means = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        starts = rng.integers(0, n, size=n_blocks)
        idx = np.concatenate([(np.arange(s, s + b) % n) for s in starts])[:n]
        means[i] = a[idx].mean()
    lo = float(np.quantile(means, (1 - ci) / 2))
    hi = float(np.quantile(means, 1 - (1 - ci) / 2))
    return (lo, float(a.mean()), hi)


# ────────────────────────────────────────────────────────────────────
# 3차 게이트 종합 (발견→확정: 단일 측정 단정 금지)
# ────────────────────────────────────────────────────────────────────
@dataclass
class ConfirmGate:
    mean: float
    n: int
    nw_t: float
    nw_lags: int
    boot_lo: float
    boot_hi: float
    walk_forward_consistent: Optional[bool]  # None = OOS 미제공 → 미평가
    confirmed: bool                          # 4기준 충족 (미충족 = "문제 의심" 한정)
    note: str = ""


def confirm_gate(
    excess: Sequence[float],
    oos_excess: Optional[Sequence[float]] = None,
    ci: float = 0.95,
) -> ConfirmGate:
    """3차 게이트: ① n ② NW HAC t ③ block-bootstrap CI ④ walk-forward 부호일관.

    confirmed = |nw_t|>1.96  AND  bootstrap CI 가 0 미포함  AND
                (oos 제공 시 in/out 부호일관 / 미제공 시 walk-forward 항 통과로 간주하되 note 명기).
    ★단정 금지: 미충족이면 confirmed=False = "문제 의심"(아직 단정 아님).
    """
    a = np.asarray(excess, float)
    a = a[~np.isnan(a)]
    nw_t, n, lags = nw_hac_tstat(a)
    lo, mu, hi = block_bootstrap_ci(a, ci=ci)
    wf: Optional[bool] = None
    if oos_excess is not None:
        o = np.asarray(oos_excess, float)
        o = o[~np.isnan(o)]
        if o.size >= 3:
            wf = bool((np.sign(o.mean()) == np.sign(mu)) and mu != 0.0)
    ci_excludes_0 = (lo > 0) or (hi < 0)
    confirmed = (abs(nw_t) > 1.96) and ci_excludes_0 and (wf if wf is not None else True)
    return ConfirmGate(
        mean=float(mu), n=int(n), nw_t=float(nw_t), nw_lags=int(lags),
        boot_lo=float(lo), boot_hi=float(hi), walk_forward_consistent=wf,
        confirmed=bool(confirmed),
        note=("walk-forward 미평가(OOS 미제공)" if wf is None else ""),
    )


# ────────────────────────────────────────────────────────────────────
# per-asset attribution — ★self-referential base 금지 (empirical-claim §1.8)
# ────────────────────────────────────────────────────────────────────
@dataclass
class AssetAttribution:
    asset: str
    strat_cum: float       # 전략 누적수익
    passive_cum: float     # 외부 passive buy&hold 누적 (★base = 외부)
    excess: float          # strat - passive
    rank_ic: float
    hit: float
    n: int
    suspect: bool          # 장기 음수 excess = L0~L3 귀속 조사 대상


def per_asset_attribution(
    strat_returns: Dict[str, Sequence[float]],
    passive_returns: Dict[str, Sequence[float]],
    scores: Optional[Dict[str, Sequence[float]]] = None,
) -> List[AssetAttribution]:
    """자산별 [전략 누적 / passive 누적 / excess / rank-IC / hit] 표.

    ★self-referential base 금지(empirical-claim §1.8): per-asset excess 의 base 는
      각 자산의 **외부** buy&hold(passive_returns). 측정대상들의 가중평균을 base 로 쓰면
      ∑wᵢ·excessᵢ ≡ 0 거울(자유도 N−1 → 독립 발견 아님). 호출자는 passive_returns 에
      반드시 자산 자체 buy&hold 시계열을 주입(가중평균 금지).
    장기 음수 excess 자산 = suspect=True → L1(이론) 의심·sleeve ledger 재검토 대상.
    """
    out: List[AssetAttribution] = []
    for asset, sr in strat_returns.items():
        pr = passive_returns.get(asset)
        if pr is None:
            continue
        s = np.asarray(sr, float)
        p = np.asarray(pr, float)
        strat_cum = float(np.prod(1.0 + s) - 1.0) if s.size else 0.0
        passive_cum = float(np.prod(1.0 + p) - 1.0) if p.size else 0.0
        excess = strat_cum - passive_cum
        ic, hh = 0.0, 0.0
        if scores and asset in scores:
            sc = list(scores[asset])
            m = min(len(sc), len(sr))
            if m >= 2:
                ic = rank_ic(sc[:m], list(sr)[:m])[0]
                hh = hit_rate(sc[:m], list(sr)[:m])
        out.append(AssetAttribution(
            asset=asset, strat_cum=strat_cum, passive_cum=passive_cum,
            excess=excess, rank_ic=ic, hit=hh, n=int(s.size),
            suspect=bool(excess < 0.0),
        ))
    return out


# ────────────────────────────────────────────────────────────────────
# 4층 지표 (plan §3 — 단일 수익률 금지, 4층 동시)
# ────────────────────────────────────────────────────────────────────
def four_layer_metrics(
    equity_curve: Sequence[float],
    benchmark_curve: Optional[Sequence[float]] = None,
    *,
    scores: Optional[Sequence[float]] = None,
    fwd_returns: Optional[Sequence[float]] = None,
    n_errors: int = 0,
    n_stages_disconnected: int = 0,
) -> dict:
    """4층 지표 동시 산출. (a)연결성 (b)신호품질 (c)리스크조정 (d)초과수익."""
    eq = pd.Series(list(equity_curve), dtype=float)
    rets = returns_from_equity(eq)
    has_sig = scores is not None and fwd_returns is not None
    m: dict = {
        # (a) 연결성
        "error_count": int(n_errors),
        "stages_disconnected": int(n_stages_disconnected),
        # (b) 신호품질 (scale-invariant — NAV 상수오염 면역)
        "rank_ic": (rank_ic(list(scores), list(fwd_returns))[0] if has_sig else None),
        "hit_rate": (hit_rate(scores, fwd_returns) if has_sig else None),
        # (c) 리스크조정
        "sharpe": calculate_sharpe_ratio(rets),
        "sortino": calculate_sortino_ratio(rets),
        "max_drawdown": calculate_max_drawdown(eq),
        "calmar": calculate_calmar_ratio(eq),
        # (d) 초과수익
        "cagr": calculate_cagr(eq),
    }
    if benchmark_curve is not None:
        bench = pd.Series(list(benchmark_curve), dtype=float)
        m["benchmark_cagr"] = calculate_cagr(bench)
        m["excess_cagr"] = m["cagr"] - m["benchmark_cagr"]
    return m


# ────────────────────────────────────────────────────────────────────
# self-test
# ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    rng = np.random.default_rng(42)

    # hit_rate
    assert hit_rate([1, -1, 1], [1, -1, 1]) == 1.0
    assert hit_rate([1, 1], [1, -1]) == 0.5

    # NW HAC t: 양의 평균 drift → t>0, 자기상관 있어도 유한
    drift = 0.001 + 0.01 * rng.standard_normal(300)
    t, n, lags = nw_hac_tstat(drift)
    assert n == 300 and lags >= 1, (n, lags)
    assert t > 0, t

    # block bootstrap CI: 평균 포함, lo<mean<hi
    lo, mu, hi = block_bootstrap_ci(drift, n_boot=500, seed=1)
    assert lo <= mu <= hi, (lo, mu, hi)

    # confirm_gate: 강한 양 drift = confirmed (NW t>1.96 + CI>0). OOS 동부호 일관
    g = confirm_gate(0.005 + 0.005 * rng.standard_normal(300),
                     oos_excess=0.005 + 0.005 * rng.standard_normal(60))
    assert g.confirmed is True, g
    assert g.walk_forward_consistent is True, g
    # 노이즈 평균0 = 미확정 (단정 금지)
    g0 = confirm_gate(0.0 + 0.01 * rng.standard_normal(300))
    assert g0.confirmed is False, g0
    assert g0.note.startswith("walk-forward 미평가"), g0

    # per-asset: self-ref base 금지 — 외부 passive base. 전략<passive → suspect
    strat = {"BTC": [0.01, -0.02, 0.01], "ETH": [0.02, 0.01, 0.0]}
    passive = {"BTC": [0.03, 0.01, 0.02], "ETH": [0.0, 0.0, 0.0]}
    rows = per_asset_attribution(strat, passive)
    btc = next(r for r in rows if r.asset == "BTC")
    eth = next(r for r in rows if r.asset == "ETH")
    assert btc.excess < 0 and btc.suspect is True, btc   # BTC 전략 < passive
    assert eth.excess > 0 and eth.suspect is False, eth   # ETH 전략 > passive(0)

    # 4층 지표: 상승 equity → sharpe·cagr 산출, 벤치 대비 excess
    eq = pd.Series(np.cumprod(1 + drift) * 1_000_000)
    bench = pd.Series(np.cumprod(1 + 0.0005 + 0.01 * rng.standard_normal(300)) * 1_000_000)
    fm = four_layer_metrics(eq, bench, scores=list(drift), fwd_returns=list(drift))
    assert fm["rank_ic"] is not None and "excess_cagr" in fm, fm
    assert fm["sharpe"] != 0.0, fm

    print("diagnostics self-test PASS")
