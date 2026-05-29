"""core/structure/validate_semiconductor.py — ★ T2-7 검증 (필수 STOP 게이트).

SPEC T2-7: 반도체(cyclical) 라벨 에피소드(2016-17·2020-21)로 **구조모델 잔차**가
밸류트랩 vs 진짜저평가를 가르는 precision/recall 을 실증. **안 갈리면 잔차 reframe
자체를 재검토**(전체 전제).

검증을 non-circular 하게 만드는 핵심 = **head-to-head**:
  claude R4 의 명제는 "raw 멀티플 분위 = 밸류트랩 양산기, 잔차가 더 낫다" 이다.
  그래서 동일 데이터·동일 라벨에서 두 신호를 맞붙인다.
    - 잔차 신호  : cheapness_z (낮을수록 싸다)
    - raw 신호   : [sector,regime] 내 멀티플 percentile (낮을수록 싸다 = 현 설계)
  **잔차가 raw 분위를 이기지 못하면 reframe 은 정당화 안 됨 → STOP.**
  cyclical 의 DGP 는 peak-EPS 가 raw 멀티플을 낮게 보이게 하는 교란을 *내장* 하므로,
  잔차가 그 교란을 걷어내 raw 를 이기는지가 진짜 시험이다.

walk-forward OOS:
  각 평가 분기 q 에 대해 as_of = q말 + lag. train = knowable_from ≤ as_of − purge.
  평가 = q 분기 row (purge 로 train 에서 제외된 진짜 OOS). 모든 q 누적 → P/R/PR-AUC.

⚠️ 정직 표기: 본 검증은 **합성 fixture** 위에서 돈다 (T1 실패널 미도착). 따라서 결과는
  "분리 가능성이 존재할 때 추정기가 raw 대비 그것을 회복하는가"(machinery + 상대우위)를
  입증할 뿐, **실데이터에서 전제가 성립함을 확정하지 않는다**. 실데이터 STOP 게이트는
  T1 반도체 패널 도착 후 동일 하니스 재실행으로 확정한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from core.structure import panel_schema as ps
from core.structure.panel_schema import make_semiconductor_fixture, FixtureSpec
from core.structure.structure_model import StructureModel, StructureModelConfig


@dataclass
class MethodScore:
    name: str
    pr_auc: float                    # average precision (불균형에 적합)
    precision_at_op: float           # 운영점(top-K% 플래그) precision
    recall_at_op: float
    f1_at_op: float
    n_flagged: int
    n_eval: int
    n_real: int


@dataclass
class ValidationReport:
    residual: MethodScore
    raw_percentile: MethodScore
    lift_pr_auc: float               # residual − raw (양수 = 잔차 우위)
    verdict: str                     # "GO" | "STOP" | "GO-WEAK"
    rationale: str
    gbm_diag: dict = field(default_factory=dict)
    detail: dict = field(default_factory=dict)


def _pr_auc(labels: np.ndarray, score_higher_is_cheaper: np.ndarray) -> float:
    """average precision. score 가 클수록 '진짜 저평가' 가능성이 높도록 정렬돼야 함."""
    from sklearn.metrics import average_precision_score
    if labels.sum() == 0 or labels.sum() == len(labels):
        return float("nan")
    return float(average_precision_score(labels, score_higher_is_cheaper))


def _op_scores(labels: np.ndarray, score: np.ndarray, top_frac: float):
    """top_frac 비율을 '싸다'로 플래그했을 때 precision/recall/f1."""
    from sklearn.metrics import precision_score, recall_score, f1_score
    n = len(score)
    k = max(1, int(round(n * top_frac)))
    thr = np.sort(score)[::-1][k - 1]      # 상위 k 번째 점수
    pred = (score >= thr).astype(int)
    p = precision_score(labels, pred, zero_division=0)
    r = recall_score(labels, pred, zero_division=0)
    f = f1_score(labels, pred, zero_division=0)
    return float(p), float(r), float(f), int(pred.sum())


def run_validation(
    panel: pd.DataFrame | None = None,
    eval_start_year: int = 2018,
    purge_days: int = 90,
    top_frac: float = 0.20,
    lift_threshold: float = 0.05,
) -> ValidationReport:
    """walk-forward OOS 로 잔차 vs raw분위 head-to-head 평가 → GO/STOP 판정."""
    if panel is None:
        panel = make_semiconductor_fixture()

    cfg = StructureModelConfig(purge_days=purge_days)
    eval_quarters = sorted(
        d for d in panel[ps.COL_DATE].unique()
        if pd.Timestamp(d).year >= eval_start_year
    )

    rows_resid, rows_raw, rows_label, rows_phase = [], [], [], []
    last_gbm = {}

    for q in eval_quarters:
        q = pd.Timestamp(q)
        as_of = q + pd.Timedelta(days=5)             # 분기말 직후 관측
        cutoff = as_of - pd.Timedelta(days=purge_days)
        train = panel[panel[ps.COL_KNOWABLE_FROM] <= cutoff]
        eval_rows = panel[panel[ps.COL_DATE] == q]
        if len(train) < cfg.min_train_rows or eval_rows.empty:
            continue

        # --- 잔차 신호 ---
        model = StructureModel(cfg)
        try:
            fit = model.fit(panel, as_of)
        except ValueError:
            continue
        last_gbm = fit.gbm_diag
        z = model.cheapness_z_rows(eval_rows)         # 낮을수록 싸다

        # --- raw 분위 baseline ([sector,regime] 내, PIT: train 분포로 채점) ---
        raw_pct = _raw_percentile(train, eval_rows)   # 낮을수록(저멀티플) 싸다 = 현 설계

        valid = np.isfinite(z) & np.isfinite(raw_pct)
        rows_resid.append(z[valid])
        rows_raw.append(raw_pct[valid])
        rows_label.append(eval_rows["label_real"].values[valid])
        rows_phase.append(eval_rows["label_cycle_phase"].values[valid])

    z_all = np.concatenate(rows_resid)
    raw_all = np.concatenate(rows_raw)
    y_all = np.concatenate(rows_label).astype(int)
    phase_all = np.concatenate(rows_phase)

    # 점수: 클수록 '진짜 저평가' 가능성 ↑ 가 되도록 부호 정렬
    resid_score = -z_all          # cheapness_z 낮을수록 싸다 → 부호 반전
    raw_score = -raw_all          # 멀티플 percentile 낮을수록 싸다 → 부호 반전

    resid = _score_method("residual(cheapness_z)", y_all, resid_score, top_frac)
    raw = _score_method("raw_percentile", y_all, raw_score, top_frac)

    lift = resid.pr_auc - raw.pr_auc
    if not np.isfinite(lift):
        verdict, rationale = "STOP", "라벨 분포 degenerate — 검증 불가"
    elif lift >= lift_threshold and resid.pr_auc > raw.pr_auc:
        verdict = "GO"
        rationale = (
            f"잔차가 raw분위를 PR-AUC +{lift:.3f} 우위 (잔차 {resid.pr_auc:.3f} vs raw {raw.pr_auc:.3f}). "
            f"cyclical peak-EPS 교란을 잔차가 걷어냄 → reframe 정당화."
        )
    elif lift > 0:
        verdict = "GO-WEAK"
        rationale = (
            f"잔차가 raw 를 이기나 마진 작음(+{lift:.3f} < {lift_threshold}). "
            f"실데이터(T1) 재검증 전 약한 GO."
        )
    else:
        verdict = "STOP"
        rationale = (
            f"잔차가 raw분위를 못 이김 (lift {lift:.3f} ≤ 0). "
            f"reframe 이 raw 대비 부가가치 없음 → 잔차 reframe 재검토 필요."
        )

    # phase별 분해 (peak=trap 다발 / trough=real 다발)
    detail = _phase_breakdown(y_all, resid_score, raw_score, phase_all)

    return ValidationReport(
        residual=resid, raw_percentile=raw, lift_pr_auc=float(lift),
        verdict=verdict, rationale=rationale, gbm_diag=last_gbm, detail=detail,
    )


def _score_method(name, y, score, top_frac) -> MethodScore:
    pr_auc = _pr_auc(y, score)
    p, r, f, nf = _op_scores(y, score, top_frac)
    return MethodScore(name=name, pr_auc=pr_auc, precision_at_op=p, recall_at_op=r,
                       f1_at_op=f, n_flagged=nf, n_eval=len(y), n_real=int(y.sum()))


def _raw_percentile(train: pd.DataFrame, eval_rows: pd.DataFrame) -> np.ndarray:
    """현 설계: [sector,regime] 내 멀티플 분위 (낮을수록 싸다). train 분포로 PIT 채점."""
    out = np.full(len(eval_rows), np.nan)
    for i, (_, row) in enumerate(eval_rows.iterrows()):
        ref = train[
            (train[ps.COL_SECTOR] == row[ps.COL_SECTOR])
            & (train[ps.COL_REGIME] == row[ps.COL_REGIME])
        ][ps.COL_MULTIPLE].values
        if len(ref) < 5:
            ref = train[train[ps.COL_SECTOR] == row[ps.COL_SECTOR]][ps.COL_MULTIPLE].values
        if len(ref) >= 3:
            out[i] = float((ref < row[ps.COL_MULTIPLE]).mean())  # 0=최저멀티플
    return out


def _phase_breakdown(y, resid_score, raw_score, phase) -> dict:
    """사이클 위상별 두 신호의 평균 점수 (peak=trap / trough=real 검증)."""
    res = {}
    for ph in ("peak", "trough", "mid"):
        m = phase == ph
        if m.sum() == 0:
            continue
        res[ph] = {
            "n": int(m.sum()),
            "n_real": int(y[m].sum()),
            "resid_mean_score_real": round(float(resid_score[m & (y == 1)].mean()) if (m & (y == 1)).any() else float("nan"), 3),
            "resid_mean_score_trap": round(float(resid_score[m & (y == 0)].mean()) if (m & (y == 0)).any() else float("nan"), 3),
            "raw_mean_score_real": round(float(raw_score[m & (y == 1)].mean()) if (m & (y == 1)).any() else float("nan"), 3),
            "raw_mean_score_trap": round(float(raw_score[m & (y == 0)].mean()) if (m & (y == 0)).any() else float("nan"), 3),
        }
    return res


def format_report(rep: ValidationReport) -> str:
    L = []
    L.append("=" * 68)
    L.append("T2-7 검증 — 반도체 cyclical 잔차 vs raw분위 (head-to-head, OOS)")
    L.append("=" * 68)
    for m in (rep.residual, rep.raw_percentile):
        L.append(
            f"  {m.name:26s} PR-AUC={m.pr_auc:.3f}  "
            f"P@{m.n_flagged}={m.precision_at_op:.3f}  R={m.recall_at_op:.3f}  F1={m.f1_at_op:.3f}"
        )
    L.append(f"  (eval n={rep.residual.n_eval}, real={rep.residual.n_real})")
    L.append(f"  lift(PR-AUC) = {rep.lift_pr_auc:+.3f}")
    L.append("-" * 68)
    L.append(f"  GBM 진단(비선형 누락): {rep.gbm_diag}")
    L.append("-" * 68)
    L.append("  위상별 평균점수 (클수록 '싸다' 신호; real 이 trap 보다 높아야 분별):")
    for ph, d in rep.detail.items():
        L.append(
            f"    {ph:7s} n={d['n']:4d} real={d['n_real']:3d} | "
            f"잔차 real={d['resid_mean_score_real']} trap={d['resid_mean_score_trap']} | "
            f"raw real={d['raw_mean_score_real']} trap={d['raw_mean_score_trap']}"
        )
    L.append("=" * 68)
    L.append(f"  ★ 판정: {rep.verdict}")
    L.append(f"     {rep.rationale}")
    L.append("=" * 68)
    return "\n".join(L)


if __name__ == "__main__":
    rep = run_validation()
    print(format_report(rep))
