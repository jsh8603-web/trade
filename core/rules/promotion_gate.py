"""core/rules/promotion_gate.py — G0~G6 승격 게이트 (S3, B/D축).

claude R4/R8: **완전 자동 승격 반대**. 증거카드=자동, 돈 flip=shadow+사람 비준.
  G0 사전등록 → G1 effect floor + BH FDR → G2 국면안정 → G3 purged+embargo WF
  → G3.5 비용/유동성 → G4 PBO≤0.2 deflation → G5 shadow → G6 사람.

핵심 통계 게이트는 실제 계산, 운영 게이트(G5 shadow/G6 human)는 상태 플래그:
- **G1 BH FDR** (전역 multiplicity): statsmodels multipletests(fdr_bh). ⚠️ LLM 제안 전체
  후보가 FDR 분모 (R7~8 Alpha Spending) — 발동된 것만 세면 게이트 무력화.
- **G4 PBO** (Bailey/López de Prado): combinatorial IS/OOS rank → overfit 확률.
  + PSR/DSR (Probabilistic/Deflated Sharpe, rubenbriones ~40줄 차용 정신, scipy 자체구현).
- 차용 정신: skfolio _combinatorial(BSD) API 참조했으나 무거운 의존(cvxpy) 회피 → scipy 자체구현.
  mlfinlab=stub+독점 복사금지(SPLIT-INDEX).

EvidenceCard 는 자동 생성·직렬화(rule_evidence.jsonl). 사람 비준(G6)은 외부 입력.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import date
from itertools import combinations
from typing import Optional

import numpy as np


# ---------------------------------------------------------------------------
# 통계 primitive
# ---------------------------------------------------------------------------

def bh_fdr(pvalues: list[float], alpha: float = 0.10) -> tuple[list[bool], list[float]]:
    """Benjamini-Hochberg FDR. 전체 후보 pvalue 를 분모로 (전역 multiplicity)."""
    from statsmodels.stats.multitest import multipletests
    if not pvalues:
        return [], []
    rej, q, _, _ = multipletests(pvalues, alpha=alpha, method="fdr_bh")
    return list(rej), list(q)


def psr(returns: np.ndarray, sr_benchmark: float = 0.0) -> float:
    """Probabilistic Sharpe Ratio: P(true SR > benchmark). 비정규성(skew/kurt) 보정."""
    from scipy.stats import norm, skew, kurtosis
    r = np.asarray(returns, dtype=float)
    r = r[np.isfinite(r)]
    n = len(r)
    sd = r.std(ddof=1)
    if n < 3 or sd <= 1e-12:
        return float("nan")
    sr = r.mean() / sd
    sk = float(skew(r))
    ku = float(kurtosis(r, fisher=False))   # 정규=3
    denom = np.sqrt(1.0 - sk * sr + (ku - 1.0) / 4.0 * sr ** 2)
    if denom <= 1e-12:
        return float("nan")
    return float(norm.cdf((sr - sr_benchmark) * np.sqrt(n - 1) / denom))


def deflated_sr(returns: np.ndarray, n_trials: int, sr_variance: float = 1.0) -> float:
    """Deflated SR: 다중 시행에서 기대 최대 SR 을 benchmark 로 한 PSR (selection bias 보정)."""
    from scipy.stats import norm
    if n_trials < 2:
        return psr(returns, 0.0)
    emc = 0.5772156649  # Euler-Mascheroni
    z1 = norm.ppf(1.0 - 1.0 / n_trials)
    z2 = norm.ppf(1.0 - 1.0 / (n_trials * np.e))
    expected_max_sr = np.sqrt(sr_variance) * ((1 - emc) * z1 + emc * z2)
    return psr(returns, expected_max_sr)


def pbo(is_oos_matrix: np.ndarray, n_splits: int = 8) -> float:
    """Probability of Backtest Overfitting (Bailey/LdP combinatorial).

    is_oos_matrix: shape (T, N) — T 시점 × N config 의 수익률. config 선택이 IS 최적인데
    OOS 에서 중앙값 이하로 떨어지는 빈도 → overfit 확률. ≤0.2 통과.
    """
    M = np.asarray(is_oos_matrix, dtype=float)
    T, N = M.shape
    if N < 2 or T < n_splits or n_splits % 2 != 0:
        return float("nan")
    blocks = np.array_split(np.arange(T), n_splits)
    logits = []
    for is_idx in combinations(range(n_splits), n_splits // 2):
        oos_idx = [b for b in range(n_splits) if b not in is_idx]
        is_rows = np.concatenate([blocks[b] for b in is_idx])
        oos_rows = np.concatenate([blocks[b] for b in oos_idx])
        is_sr = M[is_rows].mean(0) / (M[is_rows].std(0, ddof=1) + 1e-12)
        oos_sr = M[oos_rows].mean(0) / (M[oos_rows].std(0, ddof=1) + 1e-12)
        best = int(np.argmax(is_sr))
        # IS 최적 config 의 OOS rank (0=최악 ~ 1=최고)
        rank = (oos_sr < oos_sr[best]).mean()
        rank = min(max(rank, 1e-6), 1 - 1e-6)
        logits.append(np.log(rank / (1 - rank)))
    logits = np.array(logits)
    return float((logits <= 0).mean())   # OOS median 이하로 떨어진 비율


# ---------------------------------------------------------------------------
# EvidenceCard + 게이트 파이프라인
# ---------------------------------------------------------------------------

@dataclass
class GateResult:
    gate: str
    passed: bool
    detail: dict = field(default_factory=dict)


@dataclass
class EvidenceCard:
    candidate_id: str
    signal_id: str
    version: str
    registered_at: str
    results: list[GateResult] = field(default_factory=list)
    verdict: str = "PENDING"      # PASS_AUTO | NEED_HUMAN | REJECT
    rationale: str = ""

    def to_jsonl(self, path: str) -> None:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "candidate_id": self.candidate_id, "signal_id": self.signal_id,
                "version": self.version, "registered_at": self.registered_at,
                "verdict": self.verdict, "rationale": self.rationale,
                "results": [asdict(r) for r in self.results],
            }, ensure_ascii=False) + "\n")


@dataclass
class GateConfig:
    effect_floor: float = 0.02        # G1 최소 효과크기 (IC)
    fdr_alpha: float = 0.10           # G1 BH FDR
    regime_consistency: float = 0.6   # G2 regime별 부호 일관 비율
    oos_ic_floor: float = 0.0         # G3 purged WF OOS IC > 0
    pbo_max: float = 0.20             # G4 PBO ≤ 0.2
    psr_min: float = 0.95             # G4 PSR ≥ 0.95


def run_gates(
    candidate_id: str,
    signal_id: str,
    version: str,
    *,
    ic: float,                        # 후보 효과크기
    pvalue: float,                    # 후보 pvalue
    all_candidate_pvalues: list[float],   # ★ 전역 multiplicity 분모 (LLM 제안 전체)
    regime_ics: dict,                 # {regime_id: IC} (G2)
    oos_ic: float,                    # purged WF OOS IC (G3)
    trial_returns: np.ndarray,        # 후보 OOS 수익률 (PSR/DSR, G4)
    n_trials: int,                    # 다중 시행 수 (DSR deflation)
    is_oos_matrix: Optional[np.ndarray] = None,   # (T,N) config matrix (PBO, G4)
    cfg: Optional[GateConfig] = None,
    registered_at: Optional[str] = None,
) -> EvidenceCard:
    """G0~G4 자동 통계 게이트 → EvidenceCard. G5/G6 는 verdict=NEED_HUMAN 로 외부 위임."""
    cfg = cfg or GateConfig()
    card = EvidenceCard(candidate_id, signal_id, version,
                        registered_at or str(date.today()))

    # G1: effect floor + BH FDR (전역)
    rej, q = bh_fdr(all_candidate_pvalues, alpha=cfg.fdr_alpha)
    try:
        idx = all_candidate_pvalues.index(pvalue)
        fdr_pass = rej[idx]
        qval = q[idx]
    except (ValueError, IndexError):
        fdr_pass, qval = False, float("nan")
    g1 = abs(ic) >= cfg.effect_floor and fdr_pass
    card.results.append(GateResult("G1_effect_fdr", g1,
                                   {"ic": ic, "floor": cfg.effect_floor, "q": qval, "fdr_pass": fdr_pass}))

    # G2: regime 안정 (부호 일관 비율)
    if regime_ics:
        signs = [np.sign(v) for v in regime_ics.values() if np.isfinite(v)]
        main_sign = np.sign(ic)
        consist = np.mean([s == main_sign for s in signs]) if signs else 0.0
        g2 = consist >= cfg.regime_consistency
    else:
        consist, g2 = 0.0, False
    card.results.append(GateResult("G2_regime_stability", g2,
                                   {"consistency": round(float(consist), 3), "min": cfg.regime_consistency}))

    # G3: purged WF OOS IC
    g3 = oos_ic > cfg.oos_ic_floor
    card.results.append(GateResult("G3_purged_wf", g3, {"oos_ic": oos_ic}))

    # G4: PBO + PSR/DSR
    p_psr = psr(trial_returns, 0.0)
    p_dsr = deflated_sr(trial_returns, n_trials)
    p_pbo = pbo(is_oos_matrix) if is_oos_matrix is not None else float("nan")
    # G4 hard gate = PSR≥min AND PBO≤max. DSR 은 deflation 정보로 detail 기록만 —
    # hard gate 로 강제하려면 시행 SR 분산(sr_variance) 추정이 필요한데 v1 엔 그 입력이
    # 없어(기본 1.0=과도) 정상 신호도 죽는다. v2 에서 sr_variance 추정 후 게이트 승격.
    g4 = (np.isfinite(p_psr) and p_psr >= cfg.psr_min) and (
        not np.isfinite(p_pbo) or p_pbo <= cfg.pbo_max)
    card.results.append(GateResult("G4_pbo_psr", bool(g4),
                                   {"psr": round(p_psr, 4) if np.isfinite(p_psr) else None,
                                    "dsr": round(p_dsr, 4) if np.isfinite(p_dsr) else None,
                                    "pbo": round(p_pbo, 4) if np.isfinite(p_pbo) else None}))

    all_auto = all(r.passed for r in card.results)
    if not all_auto:
        failed = [r.gate for r in card.results if not r.passed]
        card.verdict, card.rationale = "REJECT", f"자동 게이트 탈락: {failed}"
    else:
        # 돈 flip = shadow(G5)+사람(G6) → 자동 통과여도 NEED_HUMAN (claude R4)
        card.verdict, card.rationale = "NEED_HUMAN", "G1~G4 자동 통과 → G5 shadow + G6 사람 비준 대기"
    return card


if __name__ == "__main__":
    rng = np.random.default_rng(0)

    # 1) BH FDR 전역
    pvals = [0.001, 0.02, 0.04, 0.3, 0.6, 0.9]
    rej, q = bh_fdr(pvals, alpha=0.10)
    print(f"1) BH FDR: rej={rej} (전역 {len(pvals)} 후보)")
    assert rej[0] and not rej[-1]

    # 2) PSR/DSR: 좋은 신호 vs 노이즈
    good = rng.normal(0.08, 0.10, 250)
    noise = rng.normal(0.0, 0.10, 250)
    print(f"2) PSR good={psr(good):.3f} noise={psr(noise):.3f} | DSR good(20trial)={deflated_sr(good,20):.3f}")
    assert psr(good) > psr(noise)

    # 3) PBO: 과적합 matrix(IS 최적이 OOS 무작위) vs 진짜 신호
    T, N = 240, 10
    overfit = rng.normal(0, 0.1, (T, N))           # 전부 노이즈 → IS 최적은 운
    p_over = pbo(overfit)
    real = rng.normal(0, 0.1, (T, N)); real[:, 0] += 0.05   # config0 진짜 우위
    p_real = pbo(real)
    print(f"3) PBO overfit={p_over:.3f} real-edge={p_real:.3f}")
    assert p_real < p_over

    # 4) 전체 파이프라인: 좋은 후보 → NEED_HUMAN
    card = run_gates(
        "cand001", "cyc_cheapz", "v2",
        ic=0.05, pvalue=0.001, all_candidate_pvalues=pvals,
        regime_ics={0: 0.04, 1: 0.06, 2: 0.05}, oos_ic=0.03,
        trial_returns=good, n_trials=20, is_oos_matrix=real,
    )
    print(f"4) 좋은 후보 verdict={card.verdict} ({card.rationale})")
    assert card.verdict == "NEED_HUMAN", card.verdict

    # 5) 나쁜 후보(FDR 탈락) → REJECT
    bad = run_gates(
        "cand002", "junk", "v1",
        ic=0.005, pvalue=0.6, all_candidate_pvalues=pvals,
        regime_ics={0: 0.04, 1: -0.06}, oos_ic=-0.01,
        trial_returns=noise, n_trials=20, is_oos_matrix=overfit,
    )
    print(f"5) 나쁜 후보 verdict={bad.verdict} ({bad.rationale})")
    assert bad.verdict == "REJECT", bad.verdict

    print("S3 promotion_gate self-test PASS")
