"""core/structure/conditional_correlation.py — R15 조건부 상관 학습 (T2 통계 본체).

분담(CONSULT-DECISIONS-weight-20260529.md §4, btn-button): §1.1 regime-conditional
Graphical Lasso + nonparanormal rank-transform + §1.2 EB shrinkage(λ floor) +
§1.6 cov-space belief-mix(Σ_eff between-dispersion → 1회 역행렬 → Ω_eff) + classifier
confidence calibration(temperature, frozen) + §1.8 IC falsification 검정력(MDE + eff-n).

확정 설계(고정)는 §1.1~1.8. 본 모듈은 그 통계 본체이며 결정 X — Ω_eff·belief·검정력
"산출"만 한다(관측≠제어). 평가기준 비중(w∝Ω·IC)·카드화·L1 주입은 T3(btn-Codlearn).

세부 구현(외부 의견 3R 수렴, .consult-r15-impl-R{1,2}):
- **Q1 glasso penalty = EBIC grid**: 소표본 n=30~100 에서 CV 는 fold 데이터 부족으로 λ 분산
  폭주 → 데이터 분할 없는 EBIC(γ=0.5) over fixed geomspace grid(결정론). graphical_lasso
  loop argmin. 비수렴 시 Ledoit-Wolf shrinkage + partial-corr threshold fallback(flag).
- **Q2 calibration = temperature**: 1-param(NLL bounded Brent, frozen). isotonic 은 OOS label
  대량 + reliability diagram 부호반전 miscalibration 일 때만 — 소표본 미충족. temperature 는
  belief 궤적을 연속 유지해 between-dispersion transition feature 와 정합(isotonic 계단 X).
- **Q3 수치안정성 = 소스 margin + 싱크 대칭화 + 측정/fix 분리**:
  · 소스: EB λ_floor 가 무조건 margin → 별도 per-regime eigenvalue floor 추가 안 함(중복).
    nonparanormal 이 λ_max≤p, identity-like prior 가 분모 → cond(Σ̂_r) ≤ p/λ_floor 보장.
  · 싱크: 대칭화 (M+Mᵀ)/2 만(roundoff 비대칭 제거).
  · 역행렬: Cholesky + fail-loud(정상 replay 에선 dead code = 데이터 의존 분기 부재 → BLAS
    버전차 replay 발산 없음). de-risk feature 는 between_term 에서 직접(top eigenvalue,
    fix 상류) → PD-fix 와 독립. fallback = Cholesky 실패 시에만 scaled diagonal loading
    ε·Tr/p·I(ε~1e-8, 발동 자체가 λ_floor 재튜닝 신호).
"""

from __future__ import annotations

import hashlib
import math
import warnings
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

# 검정력 재사용 (BB-4/V7 산출물) — 형식+POWER 게이트 동일 엔진
from core.structure.hierarchical_fdr import falsification_power, _norm_ppf, _norm_cdf

# --- scipy seam (우선) + numpy fallback (graceful degrade) -------------------
try:                                              # pragma: no cover
    from scipy import stats as _sps
    from scipy.linalg import cho_factor, cho_solve
    from scipy.optimize import minimize_scalar
    _HAS_SCIPY = True
except Exception:                                 # pragma: no cover
    _sps = None
    _HAS_SCIPY = False

# --- sklearn glasso seam ----------------------------------------------------
try:                                              # pragma: no cover
    from sklearn.covariance import graphical_lasso as _sk_glasso, ledoit_wolf as _sk_lw
    _HAS_SKLEARN = True
except Exception:                                 # pragma: no cover
    _HAS_SKLEARN = False


# ---------------------------------------------------------------------------
# 0. 공용 통계 유틸 (결정론 — RNG 미사용)
# ---------------------------------------------------------------------------

def _rankdata_avg(x: np.ndarray) -> np.ndarray:
    """평균순위(ties=average). scipy 우선, 부재 시 numpy."""
    if _HAS_SCIPY:
        return _sps.rankdata(x, method="average")
    x = np.asarray(x, float)
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), float)
    ranks[order] = np.arange(1, len(x) + 1, dtype=float)
    # ties 평균화
    _, inv, counts = np.unique(x, return_inverse=True, return_counts=True)
    sums = np.zeros(len(counts)); np.add.at(sums, inv, ranks)
    return (sums / counts)[inv]


def _norm_ppf_vec(u: np.ndarray) -> np.ndarray:
    if _HAS_SCIPY:
        return _sps.norm.ppf(u)
    return np.array([_norm_ppf(float(v)) for v in u], float)


def robust_scale_vec(X: np.ndarray) -> np.ndarray:
    """열별 MAD×1.4826 (정규 일치 robust σ). 표본 부족/0 → std 폴백."""
    X = np.asarray(X, float)
    med = np.median(X, axis=0)
    mad = np.median(np.abs(X - med), axis=0)
    s = 1.4826 * mad
    bad = s <= 1e-12
    if np.any(bad):
        std = np.std(X, axis=0)
        s = np.where(bad, np.where(std > 1e-12, std, 1.0), s)
    return s


# ---------------------------------------------------------------------------
# 1. §1.1 nonparanormal rank-transform (fat-tail robust 전처리)
# ---------------------------------------------------------------------------

def nonparanormal_transform(X: np.ndarray) -> np.ndarray:
    """열별 rank → Gaussianize Φ⁻¹ (Liu et al. nonparanormal). winsorize δ_n 로
    꼬리 Φ⁻¹ blow-up 차단. 결과 Z 의 표본상관 = fat-tail robust copula 상관 추정용.

    δ_n = 1 / (4 n^{1/4} √(π log n)) (truncation, arxiv 1202.2169).
    """
    X = np.asarray(X, float)
    n, p = X.shape
    delta = 1.0 / (4.0 * n ** 0.25 * math.sqrt(math.pi * math.log(max(n, 3))))
    Z = np.empty_like(X)
    for j in range(p):
        u = _rankdata_avg(X[:, j]) / (n + 1.0)
        u = np.clip(u, delta, 1.0 - delta)
        Z[:, j] = _norm_ppf_vec(u)
    return Z


# ---------------------------------------------------------------------------
# 2. §1.1 EBIC graphical lasso (Q1 수렴: EBIC grid, 결정론)
# ---------------------------------------------------------------------------

@dataclass
class GlassoFit:
    precision: np.ndarray       # Ω (sparse, glasso)
    covariance: np.ndarray      # Σ (glasso)
    alpha: float                # 선택된 penalty λ_glasso (fallback 시 nan)
    ebic: float
    method: str                 # "ebic" | "lw_fallback"
    converged: bool
    n_edges: int = 0


def ebic_score(emp_cov: np.ndarray, prec: np.ndarray, n: int, p: int,
               gamma: float = 0.5, tol: float = 1e-4) -> float:
    """Extended BIC (Foygel-Drton). −2·loglik + E·log n + 4γ·E·log p. γ=0.5 소표본."""
    sign, logdet = np.linalg.slogdet(prec)
    if sign <= 0:
        return float("inf")
    loglik = 0.5 * n * (logdet - float(np.trace(emp_cov @ prec)))
    n_edges = int(np.sum(np.abs(np.triu(prec, 1)) > tol))
    return -2.0 * loglik + n_edges * math.log(max(n, 2)) + 4.0 * gamma * n_edges * math.log(max(p, 2))


def _glasso_one(emp_cov: np.ndarray, alpha: float):
    """단일 alpha graphical lasso. sklearn 우선, 부재/실패 시 None."""
    if not _HAS_SKLEARN:
        return None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cov_, prec_ = _sk_glasso(emp_cov, alpha=float(alpha), max_iter=100)
        return cov_, prec_
    except Exception:
        return None


def _lw_fallback(emp_cov: np.ndarray, n: int, thr: float = 0.05) -> GlassoFit:
    """Ledoit-Wolf shrinkage(대각 타깃) + partial-corr threshold. glasso 비수렴 fallback.
    sparse 보장 X (휴리스틱) → flag(method=lw_fallback, converged=False)."""
    p = emp_cov.shape[0]
    rho = min(1.0, (p / max(n, 1)) * 0.5)           # 표본 대비 차원 비례 shrink
    target = np.diag(np.diag(emp_cov))
    cov_s = (1.0 - rho) * emp_cov + rho * target
    cov_s = 0.5 * (cov_s + cov_s.T)
    prec = np.linalg.inv(cov_s)
    # partial correlation threshold (작은 off-diag → 0 근사 sparsity)
    d = np.sqrt(np.clip(np.diag(prec), 1e-12, None))
    pcorr = -prec / np.outer(d, d)
    mask = np.abs(pcorr) < thr
    np.fill_diagonal(mask, False)
    prec = np.where(mask, 0.0, prec)
    prec = 0.5 * (prec + prec.T)
    n_edges = int(np.sum(np.abs(np.triu(prec, 1)) > 1e-4))
    return GlassoFit(prec, cov_s, float("nan"), float("nan"), "lw_fallback", False, n_edges)


def fit_glasso_ebic(emp_cov: np.ndarray, n: int, gamma: float = 0.5,
                    n_grid: int = 30) -> GlassoFit:
    """EBIC over fixed geomspace grid. grid 상한=전부 sparse 되는 max off-diag,
    하한=상한·1e-2(이론 √(log p/n) 스케일 포괄). argmin EBIC. 데이터 분할 없음=소표본 robust."""
    p = emp_cov.shape[0]
    off = emp_cov - np.diag(np.diag(emp_cov))
    amax = float(np.max(np.abs(off)))
    if amax <= 1e-12:                               # 사실상 대각 = 독립
        prec = np.linalg.inv(emp_cov + 1e-6 * np.eye(p))
        return GlassoFit(prec, emp_cov.copy(), 0.0, float("nan"), "diagonal", True, 0)
    grid = np.geomspace(amax * 1e-2, amax, n_grid)  # 고정 grid → 결정론
    best = None
    for alpha in grid:
        res = _glasso_one(emp_cov, float(alpha))
        if res is None:
            continue
        cov_, prec_ = res
        score = ebic_score(emp_cov, prec_, n, p, gamma)
        if math.isfinite(score) and (best is None or score < best[0]):
            best = (score, float(alpha), prec_, cov_)
    if best is None:
        return _lw_fallback(emp_cov, n)
    score, alpha, prec_, cov_ = best
    n_edges = int(np.sum(np.abs(np.triu(prec_, 1)) > 1e-4))
    return GlassoFit(prec_, cov_, alpha, score, "ebic", True, n_edges)


# ---------------------------------------------------------------------------
# 3. §1.2 EB shrinkage (Q3 수렴: λ_floor 가 소스 margin 담당)
# ---------------------------------------------------------------------------

def eb_shrink(corr_glasso: np.ndarray, corr_prior: np.ndarray, n_eff: int,
              n0: float = 10.0, lam_floor: float = 0.05) -> tuple[np.ndarray, float]:
    """Empirical-Bayes 상관 수축. Ĉ = λ·C_prior + (1−λ)·C_glasso, λ = max(floor, n0/(n0+n_eff)).
    floor → prior 완전제거 불가(self-confirming attractor 차단) + 소스 PD margin 무조건 확보."""
    lam = n0 / (n0 + max(n_eff, 1))
    lam = float(min(1.0, max(lam_floor, lam)))      # floor (prior 잔존) + cap
    C = lam * corr_prior + (1.0 - lam) * corr_glasso
    C = 0.5 * (C + C.T)
    np.fill_diagonal(C, 1.0)                         # 상관행렬 대각 정규화
    return C, lam


# ---------------------------------------------------------------------------
# 4. §1.1 RegimeGlasso — hard-per-regime 추정 (belief-mix 는 application 시점만)
# ---------------------------------------------------------------------------

@dataclass
class RegimeModel:
    regime_id: int
    mu: np.ndarray              # robust mean (원공간 — between-dispersion 보존)
    Sigma: np.ndarray          # post-EB covariance (원공간, PD). corr→D·C·D 재스케일
    corr: np.ndarray           # post-EB correlation (nonparanormal+glasso+EB)
    precision: np.ndarray      # Ω = inv(Sigma)
    n: int
    lam: float                 # EB 수축계수
    glasso_alpha: float
    method: str
    cond_number: float


class RegimeGlasso:
    """regime 별 조건부 상관 학습. nonparanormal→glasso(EBIC)→EB shrink→원공간 재스케일.

    상관구조는 nonparanormal latent 에서 robust 추정, μ_r·scale 은 원공간 robust 통계로
    유지(between-dispersion 항이 의미 있으려면 μ_r 이 regime 간 비교가능한 원공간이어야 함).
    """

    def __init__(self, gamma: float = 0.5, n0: float = 10.0, lam_floor: float = 0.05,
                 corr_prior: Optional[np.ndarray] = None, n_grid: int = 30,
                 transform: bool = True, min_obs: int = 10):
        self.gamma = gamma
        self.n0 = n0
        self.lam_floor = lam_floor
        self.corr_prior = corr_prior          # Investment Clock 사전상관 (None=독립 prior I)
        self.n_grid = n_grid
        self.transform = transform
        self.min_obs = min_obs
        self.models_: dict[int, RegimeModel] = {}

    def fit(self, X: np.ndarray, regime_ids: np.ndarray) -> "RegimeGlasso":
        X = np.asarray(X, float)
        regime_ids = np.asarray(regime_ids, int)
        p = X.shape[1]
        prior = self.corr_prior if self.corr_prior is not None else np.eye(p)
        self.models_ = {}
        for r in np.unique(regime_ids):
            Xr = X[regime_ids == r]
            if len(Xr) < self.min_obs:
                continue
            mu_r = np.median(Xr, axis=0)                       # robust mean (원공간)
            sd_r = robust_scale_vec(Xr)                        # robust scale (원공간)
            Zr = nonparanormal_transform(Xr) if self.transform else (Xr - mu_r) / sd_r
            emp_corr = np.corrcoef(Zr, rowvar=False)
            if not np.all(np.isfinite(emp_corr)):
                emp_corr = np.eye(p)
            gf = fit_glasso_ebic(emp_corr, n=len(Xr), gamma=self.gamma, n_grid=self.n_grid)
            # glasso 산출 covariance 를 상관으로 정규화 후 EB shrink (prior=상관공간)
            g_cov = gf.covariance
            gd = np.sqrt(np.clip(np.diag(g_cov), 1e-12, None))
            g_corr = g_cov / np.outer(gd, gd)
            corr_hat, lam = eb_shrink(g_corr, prior, n_eff=len(Xr),
                                      n0=self.n0, lam_floor=self.lam_floor)
            D = np.diag(sd_r)
            Sigma_r = D @ corr_hat @ D                         # 원공간 covariance 재스케일
            Sigma_r = 0.5 * (Sigma_r + Sigma_r.T)
            prec_r = np.linalg.inv(Sigma_r)
            cond = float(np.linalg.cond(Sigma_r))
            self.models_[int(r)] = RegimeModel(
                int(r), mu_r, Sigma_r, corr_hat, prec_r, len(Xr),
                lam, gf.alpha, gf.method, cond,
            )
        if not self.models_:
            raise ValueError(f"적합된 regime 없음 (min_obs={self.min_obs})")
        return self


# ---------------------------------------------------------------------------
# 5. §1.6 cov-space belief-mix → 1회 역행렬 → Ω_eff (Q3 수렴 스펙)
# ---------------------------------------------------------------------------

@dataclass
class EffPrecisionResult:
    Omega_eff: np.ndarray
    Sigma_eff: np.ndarray
    dispersion: float          # between-term top eigenvalue (de-risk feature, fix 상류 측정)
    within_trace: float
    between_trace: float
    cholesky_ok: bool          # True=정상경로 / False=fallback 발동(λ_floor 재튜닝 신호)
    cond_number: float


def _chol_inverse(M: np.ndarray):
    """Cholesky 역행렬 (결정론 + 비PD 시 fail-loud). scipy 우선, 부재 시 numpy."""
    if _HAS_SCIPY:
        c = cho_factor(M, lower=True, check_finite=False)
        return cho_solve(c, np.eye(M.shape[0]), check_finite=False)
    L = np.linalg.cholesky(M)                  # 비PD → LinAlgError (fail-loud)
    Linv = np.linalg.inv(L)
    return Linv.T @ Linv


def effective_precision(models: dict[int, RegimeModel], belief: dict[int, float]
                        ) -> EffPrecisionResult:
    """Σ_eff = Σ_r b_r·Σ_r + Σ_r b_r(μ_r−μ̄)(μ_r−μ̄)ᵀ → 1회 역행렬 → Ω_eff.

    이중 mix 금지(Σ 만 mix, Ω 는 한 번만). between-dispersion = transition 자동 de-risk
    feature 로 between_term 에서 직접(top eigenvalue) 측정 — PD-fix 상류라 fix 와 독립.
    """
    rids = [r for r in belief if r in models]
    if not rids:
        raise ValueError("belief 와 models 교집합 없음")
    b = np.array([belief[r] for r in rids], float)
    b = b / b.sum()                                        # simplex 정규화
    mus = np.array([models[r].mu for r in rids])          # (R, p)
    p = mus.shape[1]
    mubar = (b[:, None] * mus).sum(axis=0)               # belief-weighted mean

    within = np.zeros((p, p))
    between = np.zeros((p, p))
    for w, r, mu in zip(b, rids, mus):
        within += w * models[r].Sigma
        dm = (mu - mubar).reshape(-1, 1)
        between += w * (dm @ dm.T)

    # ① de-risk feature = between_term top eigenvalue (fix 전, 상류 측정 — fix 와 독립)
    bw = np.linalg.eigvalsh(0.5 * (between + between.T))
    dispersion = float(max(bw[-1], 0.0))

    Sigma_eff = within + between
    M = 0.5 * (Sigma_eff + Sigma_eff.T)                   # ② 대칭화(roundoff 비대칭 제거)
    try:                                                  # ③ Cholesky fail-loud (정상=dead code)
        Omega = _chol_inverse(M)
        ok = True
    except np.linalg.LinAlgError:
        # fallback: scaled diagonal loading (발동 자체가 λ_floor 재튜닝 신호)
        eps = 1e-8 * float(np.trace(M)) / p
        Omega = np.linalg.inv(M + eps * np.eye(p))
        ok = False
    Omega = 0.5 * (Omega + Omega.T)
    return EffPrecisionResult(
        Omega_eff=Omega, Sigma_eff=M, dispersion=dispersion,
        within_trace=float(np.trace(within)), between_trace=float(np.trace(between)),
        cholesky_ok=ok, cond_number=float(np.linalg.cond(M)),
    )


# ---------------------------------------------------------------------------
# 6. classifier confidence calibration (Q2 수렴: temperature, frozen)
# ---------------------------------------------------------------------------

def _softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def expected_calibration_error(probs: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
    """top-label ECE (bin 수 pin). reliability 갭의 가중평균."""
    probs = np.asarray(probs, float); labels = np.asarray(labels, int)
    conf = probs.max(axis=1)
    pred = probs.argmax(axis=1)
    correct = (pred == labels).astype(float)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece, n = 0.0, len(labels)
    for i in range(n_bins):
        m = (conf > edges[i]) & (conf <= edges[i + 1]) if i > 0 else (conf >= edges[0]) & (conf <= edges[1])
        if m.sum() == 0:
            continue
        ece += (m.sum() / n) * abs(correct[m].mean() - conf[m].mean())
    return float(ece)


@dataclass
class CalibrationResult:
    temperature: float
    ece_before: float
    ece_after: float
    nll: float
    brier: float
    n_fit: int
    n_bins: int
    pin_hash: str              # frozen 박제 (T + 메타 hash, replay pin)
    frozen: bool = True


def _fit_temperature(logits: np.ndarray, labels: np.ndarray) -> float:
    """T = argmin NLL(softmax(logits/T)). bounded Brent (결정론), T∈[0.05,20]."""
    logits = np.asarray(logits, float); labels = np.asarray(labels, int)
    idx = np.arange(len(labels))

    def nll(logT: float) -> float:
        T = math.exp(logT)
        logp = np.log(np.clip(_softmax(logits / T), 1e-12, 1.0))
        return float(-logp[idx, labels].mean())

    lo, hi = math.log(0.05), math.log(20.0)
    if _HAS_SCIPY:
        r = minimize_scalar(nll, bounds=(lo, hi), method="bounded")
        return float(math.exp(r.x))
    # numpy golden-section fallback (결정론)
    gr = (math.sqrt(5) - 1) / 2
    a, b = lo, hi
    c, d = b - gr * (b - a), a + gr * (b - a)
    for _ in range(80):
        if nll(c) < nll(d):
            b = d
        else:
            a = c
        c, d = b - gr * (b - a), a + gr * (b - a)
    return float(math.exp((a + b) / 2))


class TemperatureCalibrator:
    """regime classifier softmax confidence → belief. OOS label offline fit + frozen.

    isotonic 대신 temperature(1-param): 소표본 over-fit 최소 + belief 궤적 연속(between-
    dispersion transition feature 정합) + simplex 자동 보존. fit 후 frozen+hash-pin.
    """

    def __init__(self, n_bins: int = 10):
        self.n_bins = n_bins
        self.T_: Optional[float] = None
        self.result_: Optional[CalibrationResult] = None

    def fit(self, logits: np.ndarray, labels: np.ndarray) -> CalibrationResult:
        logits = np.asarray(logits, float); labels = np.asarray(labels, int)
        n, k = logits.shape
        T = _fit_temperature(logits, labels)
        self.T_ = T
        p_before = _softmax(logits)
        p_after = _softmax(logits / T)
        idx = np.arange(n)
        nll = float(-np.log(np.clip(p_after[idx, labels], 1e-12, 1.0)).mean())
        onehot = np.zeros_like(p_after); onehot[idx, labels] = 1.0
        brier = float(((p_after - onehot) ** 2).sum(axis=1).mean())
        ece_b = expected_calibration_error(p_before, labels, self.n_bins)
        ece_a = expected_calibration_error(p_after, labels, self.n_bins)
        meta = f"T={T:.10f}|n={n}|k={k}|bins={self.n_bins}"
        pin = hashlib.sha256(meta.encode()).hexdigest()[:16]
        self.result_ = CalibrationResult(T, ece_b, ece_a, nll, brier, n, self.n_bins, pin)
        return self.result_

    def transform(self, logits: np.ndarray) -> np.ndarray:
        """frozen T 로 belief 산출. fit 선행 필수(자체 갱신 X = replay 결정론)."""
        if self.T_ is None:
            raise RuntimeError("fit() 선행 필요 (frozen T 부재)")
        return _softmax(np.asarray(logits, float) / self.T_)


# ---------------------------------------------------------------------------
# 7. §1.8 IC falsification 검정력 (MDE + effective-n, block-bootstrap autocorr 보정)
# ---------------------------------------------------------------------------

def effective_n_ar1(series: np.ndarray) -> float:
    """AR(1) 자기상관 보정 유효표본수 n_eff = n·(1−ρ)/(1+ρ). 시계열 IC 의 독립가정 보정."""
    x = np.asarray(series, float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 3:
        return float(n)
    xc = x - x.mean()
    denom = float(np.sum(xc * xc))
    if denom <= 1e-12:
        return float(n)
    rho = float(np.sum(xc[1:] * xc[:-1]) / denom)
    rho = min(0.99, max(0.0, rho))
    return float(n * (1.0 - rho) / (1.0 + rho))


def block_bootstrap_se(series: np.ndarray, block: int = 5, n_boot: int = 500,
                       seed: int = 0) -> float:
    """이동블록 부트스트랩 평균 SE (자기상관 보존). seed 고정=결정론."""
    x = np.asarray(series, float); x = x[np.isfinite(x)]
    n = len(x)
    if n < block + 1:
        return float(np.std(x) / math.sqrt(max(n, 1)))
    rng = np.random.default_rng(seed)
    n_blocks = int(math.ceil(n / block))
    starts_max = n - block
    means = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.integers(0, starts_max + 1, n_blocks)
        sample = np.concatenate([x[s:s + block] for s in starts])[:n]
        means[b] = sample.mean()
    return float(np.std(means, ddof=1))


def mde(n_eff: float, alpha: float = 0.05, power: float = 0.8, sides: int = 2) -> float:
    """최소 탐지 효과크기 (z 근사). MDE = (z_{1−α/sides} + z_power) / √n_eff (Cohen's d 단위)."""
    if n_eff < 2:
        return float("inf")
    z_a = _norm_ppf(1.0 - alpha / sides)
    z_b = _norm_ppf(power)
    return float((z_a + z_b) / math.sqrt(n_eff))


@dataclass
class ICPowerVerdict:
    n_eff: float
    mde: float                 # 현 n_eff 로 탐지 가능 최소 effect (사전등록 대상)
    power_at_ref: float        # ref_effect 를 탐지할 검정력
    falsifiable: bool          # n_eff ≥ N_min AND power ≥ floor → kill-falsification 유의미
    reason: str


def ic_power_gate(ic_series: np.ndarray, ref_effect: float = 0.5, *,
                  n_min: int = 20, alpha: float = 0.05, power_floor: float = 0.5,
                  target_power: float = 0.8) -> ICPowerVerdict:
    """IC falsification 검정력 게이트(§1.8). e-process(T3)가 type-I 해결 → 잔여=type-II.
    MDE + effective-n 사전등록(block-bootstrap autocorr 보정). 미달=unfalsified 보호관찰.

    falsification_power(BB-4/V7) 재사용 — 형식+POWER 게이트 동형. baseline 부재는 호출측에서
    has_baseline 판정(여기선 IC 시계열 존재 = baseline 존재 가정)."""
    n_eff = effective_n_ar1(ic_series)
    mde_val = mde(n_eff, alpha, target_power)
    power = falsification_power(abs(ref_effect), int(round(n_eff)), alpha)
    ok = (n_eff >= n_min) and (power >= power_floor)
    reason = ("ok" if ok else
              f"n_eff {n_eff:.1f}<{n_min}" if n_eff < n_min else
              f"power {power:.2f}<floor {power_floor} (MDE {mde_val:.2f}) → unfalsified 보호관찰")
    return ICPowerVerdict(n_eff, mde_val, power, ok, reason)


# ===========================================================================
# self-test (스텁 금지 — 실동작 검증)
# ===========================================================================

if __name__ == "__main__":
    rng = np.random.default_rng(20260529)
    p = 6

    # 1) nonparanormal: fat-tail(t-dist) 입력 → Gaussianize → 표본 정규성 개선
    Xt = rng.standard_t(df=3, size=(200, p))
    Z = nonparanormal_transform(Xt)
    assert Z.shape == Xt.shape and np.all(np.isfinite(Z))
    # 꼬리 압축: 표본 첨도가 t(3) 보다 정규(0)에 가까워야
    kurt_raw = float(np.mean(((Xt[:, 0] - Xt[:, 0].mean()) / Xt[:, 0].std()) ** 4) - 3)
    kurt_z = float(np.mean(((Z[:, 0] - Z[:, 0].mean()) / Z[:, 0].std()) ** 4) - 3)
    print(f"1) nonparanormal: excess kurtosis raw={kurt_raw:.2f} → Z={kurt_z:.2f} (정규화)")
    assert abs(kurt_z) < abs(kurt_raw)

    # 2) EBIC glasso: 블록 상관 구조 회복 (sparse precision)
    cov_true = np.eye(p); cov_true[0, 1] = cov_true[1, 0] = 0.6; cov_true[2, 3] = cov_true[3, 2] = 0.5
    L = np.linalg.cholesky(cov_true + 0.1 * np.eye(p))
    Xg = rng.normal(size=(120, p)) @ L.T
    emp = np.corrcoef(nonparanormal_transform(Xg), rowvar=False)
    gf = fit_glasso_ebic(emp, n=120)
    print(f"2) EBIC glasso: method={gf.method} alpha={gf.alpha:.4f} edges={gf.n_edges} ebic={gf.ebic:.1f}")
    assert gf.converged and gf.precision.shape == (p, p)
    assert np.allclose(gf.precision, gf.precision.T, atol=1e-6)

    # 3) EB shrink: 소표본 n_eff 작을수록 λ↑ (prior 쪽), floor 보장
    prior = np.eye(p)
    c1, lam1 = eb_shrink(emp, prior, n_eff=10, n0=10.0, lam_floor=0.05)
    c2, lam2 = eb_shrink(emp, prior, n_eff=200, n0=10.0, lam_floor=0.05)
    print(f"3) EB shrink: n_eff=10 → λ={lam1:.3f} / n_eff=200 → λ={lam2:.3f} (floor=0.05)")
    assert lam1 > lam2 and lam2 >= 0.05 and np.allclose(np.diag(c1), 1.0)

    # 4) RegimeGlasso: regime 별 상관구조 분리 학습 + PD
    n_per = 80
    reg = np.array([0] * n_per + [1] * n_per)
    # regime 0: idx0-1 상관 / regime 1: idx2-3 상관 (조건부 상관 = regime 따라 다름)
    c0 = np.eye(p); c0[0, 1] = c0[1, 0] = 0.7
    c1m = np.eye(p); c1m[2, 3] = c1m[3, 2] = 0.7
    X0 = rng.normal(size=(n_per, p)) @ np.linalg.cholesky(c0 + 0.05 * np.eye(p)).T
    X1 = rng.normal(size=(n_per, p)) @ np.linalg.cholesky(c1m + 0.05 * np.eye(p)).T + 2.0  # 평균 이동
    X = np.vstack([X0, X1])
    rg = RegimeGlasso(lam_floor=0.05).fit(X, reg)
    m0, m1 = rg.models_[0], rg.models_[1]
    print(f"4) RegimeGlasso: r0 corr[0,1]={m0.corr[0,1]:.2f} r1 corr[2,3]={m1.corr[2,3]:.2f} "
          f"cond r0={m0.cond_number:.0f} r1={m1.cond_number:.0f}")
    assert m0.corr[0, 1] > 0.3 and m1.corr[2, 3] > 0.3       # 조건부 상관 회복
    assert np.all(np.linalg.eigvalsh(m0.Sigma) > 0)          # PD
    # cond ≤ p/λ_floor 보장 (Q3-2 수렴 부등식, 여유 포함)
    assert m0.cond_number < p / 0.05 * 5

    # 5) belief-mix: uniform belief → between-dispersion inflate (transition de-risk)
    r_onehot = effective_precision(rg.models_, {0: 0.99, 1: 0.01})
    r_uniform = effective_precision(rg.models_, {0: 0.5, 1: 0.5})
    print(f"5) belief-mix: dispersion one-hot={r_onehot.dispersion:.3f} uniform={r_uniform.dispersion:.3f} "
          f"(chol_ok={r_uniform.cholesky_ok})")
    assert r_uniform.dispersion > r_onehot.dispersion        # uniform=불확실 최대 → between↑
    assert r_uniform.cholesky_ok and r_onehot.cholesky_ok    # 정상경로 (fallback dead)
    assert np.allclose(r_uniform.Omega_eff, r_uniform.Omega_eff.T, atol=1e-8)
    # Ω_eff·Σ_eff ≈ I (역행렬 정합)
    assert np.allclose(r_uniform.Omega_eff @ r_uniform.Sigma_eff, np.eye(p), atol=1e-6)

    # 6) temperature calibration: 과신 logit(confidence≫accuracy) → T>1 + ECE 개선 + frozen
    nC = 400
    pred_cls = rng.integers(0, 3, nC)
    logits = rng.normal(0, 0.5, (nC, 3))
    logits[np.arange(nC), pred_cls] = 4.0                    # 큰 logit = 고신뢰(softmax~0.95)
    flip = rng.random(nC) < 0.4                              # 단 40% 는 실제로 틀림 = 과신
    true_y = np.where(flip, rng.integers(0, 3, nC), pred_cls)
    cal = TemperatureCalibrator()
    cr = cal.fit(logits, true_y)
    print(f"6) temperature: T={cr.temperature:.3f} ECE {cr.ece_before:.3f}→{cr.ece_after:.3f} "
          f"NLL={cr.nll:.3f} pin={cr.pin_hash}")
    assert cr.temperature > 1.0 and cr.ece_after <= cr.ece_before + 1e-9   # 과신 → T>1, ECE 개선
    b = cal.transform(logits[:5])
    assert np.allclose(b.sum(axis=1), 1.0)                   # simplex 보존

    # 7) IC power gate: 짧은 자기상관 IC → 검정력 부족 / 긴 IC → falsifiable
    ic_short = rng.normal(0.1, 1, 12)
    ic_long = rng.normal(0.5, 1, 200)
    v_short = ic_power_gate(ic_short, ref_effect=0.3)
    v_long = ic_power_gate(ic_long, ref_effect=0.5)
    print(f"7) IC power: short n_eff={v_short.n_eff:.1f} falsifiable={v_short.falsifiable} / "
          f"long n_eff={v_long.n_eff:.1f} power={v_long.power_at_ref:.2f} falsifiable={v_long.falsifiable}")
    assert not v_short.falsifiable and v_long.falsifiable

    # 8) 결정론(replay): 동일 입력 → 동일 출력
    rg2 = RegimeGlasso(lam_floor=0.05).fit(X, reg)
    r2 = effective_precision(rg2.models_, {0: 0.5, 1: 0.5})
    assert np.allclose(r2.Omega_eff, r_uniform.Omega_eff, atol=1e-10)
    cal2 = TemperatureCalibrator(); cr2 = cal2.fit(logits, true_y)
    assert abs(cr2.temperature - cr.temperature) < 1e-9 and cr2.pin_hash == cr.pin_hash
    print("8) 결정론 replay: Ω_eff·temperature·pin 동일 ✅")

    print("\nconditional_correlation self-test PASS "
          "(nonparanormal + EBIC glasso + EB shrink + RegimeGlasso + belief-mix + "
          "temperature + IC power + 결정론)")
