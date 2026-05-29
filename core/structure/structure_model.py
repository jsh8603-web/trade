"""core/structure/structure_model.py — cheapness_z 구조모델 (T2-1, ★게이팅).

게임체인저: "싸다" = raw 멀티플 분위가 아니라 **구조모델 잔차**.

    cheapness_z(firm, sector, date, as_of) = (actual − E[multiple|drivers,sector,regime]) / σ_resid
    → 음수 클수록 저평가. 잔차 ≈ 0 = 밸류트랩 (drivers 가 낮은 멀티플을 다 설명).

설계 결정 (claude R8 + SPEC T2-1):
- **계층 부분풀링**: pymc/numpyro 부재 → statsmodels RLM(robust fixed effects) +
  섹터별 empirical-Bayes shrinkage(James-Stein) 로 부분풀링을 구현. 섹터 표본부족
  (섹터당 30~100종목)일수록 grand mean 으로 강하게 수축 → 패널 OLS 의 불안정 회피.
- **GBM = 진단기로만** (claude R8): HistGradientBoosting 으로 OOS R² 를 재서 비선형/
  교호작용 누락을 *진단*만 한다. cheapness_z 의 producer 로 쓰지 않는다 (과적합 위험).
- **Robust (Huber)**: 패닉장 이상치가 정상 학습을 깨지 않도록 RLM HuberT.
- **regime별 σ 분리**: σ_resid 를 regime 마다 따로 (패닉 regime 의 큰 분산이 정상장
  잔차의 z 를 희석하지 않게). MAD×1.4826 robust scale.
- **purged/expanding OOS 적합**: as_of 시점 fit 은 knowable_from ≤ as_of − purge_gap 만.
  in-sample 적합 시 잔차가 0 근방으로 수축 → "전부 안 싸다" (R7~8 경고) 회피.
- **estimand 분리 (T2-2)**: 이 모델은 descriptive(멀티플 *수준* 설명)이지 forward
  return 예측(prescriptive)이 아니다. 둘을 한 회귀에 섞지 않는다.
- **R8 ①**: multiple_def_version 을 fixed-effect 더미로 흡수 (GAAP/non-GAAP drift).
- **R8 ②**: delisted 기업 row 도 적합 표본에 포함 (생존편향 방지). delist_ret 은
  종속변수가 아니라 표본 포함 자체가 핵심 — "죽은 기업의 멀티플"도 정상수준 추정에 반영.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Optional, Protocol, runtime_checkable

import numpy as np
import pandas as pd

from core.structure import panel_schema as ps


# ---------------------------------------------------------------------------
# 계약 0 — canonical as_of resolver (T3=btn-Codlearn 가 SSOT 구현, T2 는 경유만)
# ---------------------------------------------------------------------------

@runtime_checkable
class AsOfResolver(Protocol):
    """transaction-time as_of 의 *정규화* 의미론. (claude R7: 자체 해석 시 reconcile 발산.)

    T2 의 cheapness_z(...,as_of) 는 as_of 를 직접 해석하지 않고 이 resolver 를 경유한다.
    T3 가 프로젝트 공통 resolver 를 구현해 주입하면 T2 는 그 의미론을 그대로 따른다.
    """
    def resolve(self, as_of) -> pd.Timestamp: ...


class IdentityAsOfResolver:
    """기본 passthrough resolver (T2 단독 개발용). ⚠️ production 은 T3 resolver 주입 필수.

    자체 해석을 *하지 않음* 을 명시 — Timestamp 정규화만 하고 의미는 호출자 입력 그대로 둔다.
    """
    def resolve(self, as_of) -> pd.Timestamp:
        return pd.Timestamp(as_of)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import statsmodels.api as sm
    from statsmodels.robust.norms import HuberT


# ---------------------------------------------------------------------------

@dataclass
class StructureModelConfig:
    purge_days: int = 90             # OOS purge gap (filing → tradeable lag + 누수 차단)
    shrinkage_tau: float = 1.0       # 섹터 effect 분산 prior (작을수록 강한 풀링)
    min_train_rows: int = 50         # 적합 최소 표본
    robust: bool = True              # RLM HuberT (False=OLS)
    regime_sigma: bool = True        # regime별 σ 분리
    use_def_version_fe: bool = True  # R8① multiple_def_version fixed-effect


@dataclass
class FittedStructure:
    """적합 결과 (purged OOS, as_of 시점). cheapness_z 산출에 필요한 모든 상태."""
    as_of: pd.Timestamp
    beta: pd.Series                  # fixed-effect 계수 (design 컬럼 index)
    design_cols: list[str]
    sector_effect: dict[str, float]  # 섹터별 shrunk 절편 (부분풀링)
    sigma_by_regime: dict[int, float]
    sigma_global: float
    n_train: int
    y_lo: float = 0.0                # 적합 표본 멀티플 하한 밴드 (외삽 차단)
    y_hi: float = 0.0                # 상한 밴드
    z_clip: float = 8.0              # cheapness_z 절대값 상한 (8σ 초과 = 비현실)
    gbm_diag: dict = field(default_factory=dict)  # 진단: {linear_r2, gbm_r2, lift}
    notes: list[str] = field(default_factory=list)


class StructureModel:
    """cheapness_z 구조모델. fit(as_of) → FittedStructure → cheapness_z(row)."""

    def __init__(
        self,
        config: StructureModelConfig | None = None,
        as_of_resolver: Optional[AsOfResolver] = None,
    ):
        self.cfg = config or StructureModelConfig()
        # 계약 0: as_of 는 항상 resolver 경유 (자체 해석 금지). 미주입 시 passthrough.
        self.resolver: AsOfResolver = as_of_resolver or IdentityAsOfResolver()
        self.fitted_: Optional[FittedStructure] = None
        self._panel: Optional[pd.DataFrame] = None

    # --- design matrix ----------------------------------------------------

    def _build_design(self, df: pd.DataFrame, fit_cols: Optional[list[str]] = None):
        """드라이버 + regime 더미 + (R8①) def_version 더미 → design matrix X.

        fit_cols 주어지면 그 컬럼에 reindex (예측 시 fit 시점 컬럼과 정렬, 결측=0).
        """
        drivers = ps.driver_columns(self._panel)
        X = df[drivers].copy()
        # regime 더미
        reg_d = pd.get_dummies(df[ps.COL_REGIME].astype(int), prefix="regime")
        X = pd.concat([X, reg_d], axis=1)
        # R8① 정의 버전 더미
        if self.cfg.use_def_version_fe:
            ver_d = pd.get_dummies(df[ps.COL_MULT_DEF_VER].astype(str), prefix="defver")
            X = pd.concat([X, ver_d], axis=1)
        X = sm.add_constant(X, has_constant="add")
        X = X.astype(float)
        if fit_cols is not None:
            X = X.reindex(columns=fit_cols, fill_value=0.0)
        return X

    # --- fit (purged OOS, expanding) --------------------------------------

    def fit(self, panel: pd.DataFrame, as_of: pd.Timestamp) -> FittedStructure:
        """as_of 시점 purged/expanding OOS 적합.

        train = knowable_from ≤ as_of − purge_days (PIT + purge). delisted row 포함(R8②).
        """
        self._panel = panel
        as_of = self.resolver.resolve(as_of)        # 계약 0: 공통 resolver 경유
        cutoff = as_of - timedelta(days=self.cfg.purge_days)
        train = panel[panel[ps.COL_KNOWABLE_FROM] <= cutoff].copy()
        notes: list[str] = []
        if len(train) < self.cfg.min_train_rows:
            raise ValueError(
                f"적합 표본 부족: {len(train)} < {self.cfg.min_train_rows} "
                f"(as_of={as_of.date()}, cutoff={cutoff.date()})"
            )

        y = train[ps.COL_MULTIPLE].astype(float).values
        X = self._build_design(train)
        design_cols = list(X.columns)

        # --- robust fixed-effect 적합 (Huber) ---
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if self.cfg.robust:
                res = sm.RLM(y, X.values, M=HuberT()).fit()
            else:
                res = sm.OLS(y, X.values).fit()
        beta = pd.Series(res.params, index=design_cols)

        fitted_fe = X.values @ beta.values
        resid_fe = y - fitted_fe

        # --- 섹터 부분풀링 (empirical-Bayes shrinkage of group residual mean) ---
        # 섹터별 잔차 평균을 grand mean(0)으로 수축. n_s 클수록 덜 수축.
        sector_effect: dict[str, float] = {}
        sectors = train[ps.COL_SECTOR].values
        resid_var = float(np.var(resid_fe)) or 1.0
        for sec in pd.unique(sectors):
            mask = sectors == sec
            n_s = int(mask.sum())
            raw_mean = float(np.mean(resid_fe[mask]))
            # shrinkage λ = n_s / (n_s + τ²ratio);  τ small → strong pooling
            tau2_ratio = self.cfg.shrinkage_tau * resid_var / max(resid_var, 1e-9)
            lam = n_s / (n_s + max(tau2_ratio, 1e-9) * 10.0)
            sector_effect[str(sec)] = lam * raw_mean

        # 풀링 후 잔차 (cheapness_z 의 기준)
        sec_adj = np.array([sector_effect.get(str(s), 0.0) for s in sectors])
        resid = y - (fitted_fe + sec_adj)

        # --- regime별 robust σ (MAD×1.4826) ---
        sigma_global = _robust_scale(resid)
        sigma_by_regime: dict[int, float] = {}
        if self.cfg.regime_sigma:
            regs = train[ps.COL_REGIME].astype(int).values
            for r in np.unique(regs):
                rs = resid[regs == r]
                sigma_by_regime[int(r)] = _robust_scale(rs) if len(rs) >= 10 else sigma_global
        notes.append(f"train={len(train)} rows, delisted={int(train[ps.COL_DELIST_FLAG].sum())} (R8② 포함)")

        # --- 외삽 차단 밴드 (소표본 OOS RLM blow-up 방지) ---
        y_scale = _robust_scale(y)
        y_lo = float(np.min(y)) - 3.0 * y_scale
        y_hi = float(np.max(y)) + 3.0 * y_scale

        # --- GBM 진단 (claude R8: 진단기로만) ---
        gbm_diag = self._gbm_diagnostic(X.values, y, resid_fe)

        self.fitted_ = FittedStructure(
            as_of=as_of, beta=beta, design_cols=design_cols,
            sector_effect=sector_effect, sigma_by_regime=sigma_by_regime,
            sigma_global=sigma_global, n_train=len(train),
            y_lo=y_lo, y_hi=y_hi,
            gbm_diag=gbm_diag, notes=notes,
        )
        return self.fitted_

    def _gbm_diagnostic(self, X: np.ndarray, y: np.ndarray, resid_fe: np.ndarray) -> dict:
        """GBM OOS R² vs 선형모델 R² 비교 (비선형/교호작용 누락 진단). producer 아님."""
        try:
            from sklearn.ensemble import HistGradientBoostingRegressor
            from sklearn.model_selection import cross_val_score
            ss_tot = float(np.var(y)) * len(y)
            ss_res = float(np.sum(resid_fe ** 2))
            linear_r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
            gbm = HistGradientBoostingRegressor(max_iter=80, max_depth=3, random_state=0)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                gbm_r2 = float(np.mean(cross_val_score(gbm, X, y, cv=3, scoring="r2")))
            return {
                "linear_r2": round(linear_r2, 4),
                "gbm_cv_r2": round(gbm_r2, 4),
                "lift": round(gbm_r2 - linear_r2, 4),
                "flag_nonlinearity": bool(gbm_r2 - linear_r2 > 0.10),
            }
        except Exception as e:  # 진단 실패가 본체를 막지 않음
            return {"error": str(e)}

    # --- cheapness_z (계약 #2) --------------------------------------------

    def expected_multiple(self, rows: pd.DataFrame) -> np.ndarray:
        """E[multiple | drivers, sector, regime] (적합 후)."""
        if self.fitted_ is None:
            raise RuntimeError("fit() 선행 필요")
        f = self.fitted_
        X = self._build_design(rows, fit_cols=f.design_cols)
        fe = X.values @ f.beta.values
        sec = rows[ps.COL_SECTOR].map(lambda s: f.sector_effect.get(str(s), 0.0)).values
        e_mult = fe + sec
        # 외삽 차단: 적합 표본 멀티플 밴드로 clip (소표본 RLM extrapolation blow-up 방지)
        if f.y_hi > f.y_lo:
            e_mult = np.clip(e_mult, f.y_lo, f.y_hi)
        return e_mult

    def cheapness_z_rows(self, rows: pd.DataFrame) -> np.ndarray:
        """행 단위 cheapness_z. (actual − E[mult]) / σ_resid[regime]. 음수=싸다."""
        if self.fitted_ is None:
            raise RuntimeError("fit() 선행 필요")
        f = self.fitted_
        e_mult = self.expected_multiple(rows)
        actual = rows[ps.COL_MULTIPLE].astype(float).values
        resid = actual - e_mult
        regs = rows[ps.COL_REGIME].astype(int).values
        sig = np.array([
            f.sigma_by_regime.get(int(r), f.sigma_global) if self.cfg.regime_sigma else f.sigma_global
            for r in regs
        ])
        sig = np.where(sig <= 1e-9, f.sigma_global if f.sigma_global > 1e-9 else 1.0, sig)
        z = resid / sig
        return np.clip(z, -f.z_clip, f.z_clip)  # 8σ 초과 = 비현실 → clamp

    # --- T2-3 드라이버 식별 (grouped + regime-stratified + 서사×통계 2×2) ----

    def driver_diagnostics(self) -> dict:
        """드라이버 식별 진단 (claude R4 A1: SHAP 그대로 X → grouped·regime-stratified).

        - grouped importance = |표준화 계수| (공선성 하에서도 partial effect, raw SHAP 함정 회피).
        - regime-stratified = regime 별 드라이버↔멀티플 부분기울기 (국면의존 노출, A1 4 함정 중 하나).
        통계 축만 제공 — 서사 축(LLM 키워드)은 driver_2x2() 에 외부 입력으로 결합.
        """
        if self.fitted_ is None or self._panel is None:
            raise RuntimeError("fit() 선행 필요")
        f = self.fitted_
        drivers = ps.driver_columns(self._panel)
        train = self._panel[self._panel[ps.COL_KNOWABLE_FROM] <= (f.as_of - timedelta(days=self.cfg.purge_days))]
        y = train[ps.COL_MULTIPLE].astype(float)
        sd_y = float(y.std()) or 1.0

        grouped, regime_strat = {}, {}
        for d in drivers:
            coef = float(f.beta.get(d, 0.0))
            sd_d = float(train[d].std()) or 1.0
            grouped[d] = round(abs(coef) * sd_d / sd_y, 4)        # 표준화 importance
            per_reg = {}
            for r in sorted(train[ps.COL_REGIME].unique()):
                sub = train[train[ps.COL_REGIME] == r]
                if len(sub) >= 20 and sub[d].std() > 1e-9:
                    per_reg[int(r)] = round(float(np.corrcoef(sub[d], sub[ps.COL_MULTIPLE])[0, 1]), 3)
            regime_strat[d] = per_reg
        ranked = sorted(grouped, key=grouped.get, reverse=True)
        return {"grouped_importance": grouped, "regime_stratified_corr": regime_strat, "ranked": ranked}

    def driver_2x2(self, narrative_drivers: set[str], stat_threshold: float = 0.05) -> dict:
        """서사×통계 2×2 (claude R4 A1: 정보 최대 = 합의 아닌 불일치).

        confirmed   = 서사○ 통계○ (진짜 드라이버)
        folklore    = 서사○ 통계X (사후 정당화 편향 — rule 로 착각 금지)
        unmodeled   = 서사X 통계○ (미반영 변수 — alpha 원천 가능)
        noise       = 서사X 통계X
        """
        diag = self.driver_diagnostics()
        imp = diag["grouped_importance"]
        out = {"confirmed": [], "folklore": [], "unmodeled": [], "noise": []}
        for d, v in imp.items():
            stat = v >= stat_threshold
            narr = d.replace(ps.DRIVER_PREFIX, "") in narrative_drivers or d in narrative_drivers
            key = ("confirmed" if narr and stat else "folklore" if narr else "unmodeled" if stat else "noise")
            out[key].append(d)
        return out

    def cheapness_z(self, firm: str, sector: str, date, as_of) -> float:
        """계약 #2: `StructureModel.cheapness_z(firm,sector,date,as_of) -> float`.

        PIT: as_of 시점에 알 수 있던 (firm, ≤date) 최신 row 로 산출. 미적합/미관측 → NaN.
        """
        if self.fitted_ is None or self._panel is None:
            raise RuntimeError("fit() 선행 필요")
        as_of = self.resolver.resolve(as_of)        # 계약 0: 공통 resolver 경유 (자체 해석 금지)
        date = pd.Timestamp(date)
        p = self._panel
        m = (
            (p[ps.COL_FIRM] == firm)
            & (p[ps.COL_SECTOR] == sector)
            & (p[ps.COL_DATE] <= date)
            & (p[ps.COL_KNOWABLE_FROM] <= as_of)
        )
        sub = p[m]
        if sub.empty:
            return float("nan")
        row = sub.sort_values(ps.COL_DATE).iloc[[-1]]
        return float(self.cheapness_z_rows(row)[0])


def _robust_scale(x: np.ndarray) -> float:
    """MAD × 1.4826 (정규 일치 robust σ). 표본 부족 시 std 폴백."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 3:
        return float(np.std(x)) if len(x) else 1.0
    med = np.median(x)
    mad = np.median(np.abs(x - med))
    s = 1.4826 * mad
    return float(s) if s > 1e-9 else (float(np.std(x)) or 1.0)


if __name__ == "__main__":
    from core.structure.panel_schema import make_semiconductor_fixture
    panel = make_semiconductor_fixture()
    as_of = pd.Timestamp("2022-01-01")
    model = StructureModel()
    fit = model.fit(panel, as_of)
    print(f"n_train={fit.n_train}  notes={fit.notes}")
    print(f"σ_global={fit.sigma_global:.3f}  σ_regime={ {k: round(v,3) for k,v in fit.sigma_by_regime.items()} }")
    print(f"GBM 진단: {fit.gbm_diag}")
    print(f"섹터 effect: { {k: round(v,3) for k,v in fit.sector_effect.items()} }")
    # 단일 firm cheapness_z
    z = model.cheapness_z("SEMI001", "semiconductor", pd.Timestamp("2021-09-30"), as_of)
    print(f"SEMI001 cheapness_z @2021Q3 = {z:.3f}")
