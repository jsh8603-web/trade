#!/usr/bin/env python3
"""
RL 모델 다양성 검증 — 앙상블 품질 및 상관관계 분석

기능:
  1. 최근 7일 decisions에서 rl_advisory 모델별 action을 추출
  2. 모델 간 Spearman 순위 상관계수 계산 (중복 모델 감지)
  3. 이상치 모델 감지 (앙상블 평균에서 2σ 이상 이탈)
  4. 에코 챔버 / 저분산 경고
  5. data/model_diversity.json에 결과 저장

사용법:
  python scripts/model_diversity.py              # 다양성 분석 실행
  python scripts/model_diversity.py --json       # JSON 출력

파이프라인 통합:
  run_agents.py Phase 14에서 자동 호출
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
load_dotenv(PROJECT_DIR / ".env")

from core.db import db

KST = timezone(timedelta(hours=9))
DIVERSITY_FILE = PROJECT_DIR / "data" / "model_diversity.json"

MODELS = ["sb3", "dt", "multi_agent", "offline", "historical"]


def _fetch_decisions(days: int = 7) -> list[dict]:
    """로컬 DB에서 최근 N일 decisions를 조회한다."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    try:
        return db.select(
            "decisions",
            filters={"created_at": f"gte.{cutoff}"},
            order="created_at.desc",
            limit=500,
            select="market_data_snapshot,created_at",
        ) or []
    except Exception as e:
        print(f"[model_diversity] DB 조회 실패: {e}", file=sys.stderr)
        return []


def _extract_model_actions(decisions: list[dict]) -> list[dict[str, float]]:
    """decisions에서 모델별 action 값을 추출한다.

    Returns:
        [{model_name: action_value, ...}, ...] — rl_advisory가 있는 행만
    """
    rows = []
    for d in decisions:
        snapshot = d.get("market_data_snapshot")
        if not snapshot:
            continue
        if isinstance(snapshot, str):
            try:
                snapshot = json.loads(snapshot)
            except (json.JSONDecodeError, TypeError):
                continue
        if not isinstance(snapshot, dict):
            continue

        rl = snapshot.get("rl_advisory")
        if not rl or not isinstance(rl, dict):
            continue

        actions = {}
        for model in MODELS:
            key = f"{model}_action"
            if key in rl:
                try:
                    actions[model] = float(rl[key])
                except (ValueError, TypeError):
                    continue

        # 최소 2개 모델의 action이 있어야 비교 가능
        if len(actions) >= 2:
            rows.append(actions)

    return rows


def _rank(values: list[float]) -> list[float]:
    """값 리스트를 순위로 변환한다 (동순위는 평균 순위)."""
    n = len(values)
    indexed = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n

    i = 0
    while i < n:
        j = i
        while j < n - 1 and values[indexed[j + 1]] == values[indexed[j]]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1  # 1-based rank
        for k in range(i, j + 1):
            ranks[indexed[k]] = avg_rank
        i = j + 1

    return ranks


def _spearman_correlation(x: list[float], y: list[float]) -> float | None:
    """두 리스트 간 Spearman 순위 상관계수를 계산한다."""
    if len(x) != len(y) or len(x) < 3:
        return None

    rx = _rank(x)
    ry = _rank(y)
    n = len(x)

    mean_rx = sum(rx) / n
    mean_ry = sum(ry) / n

    num = sum((rx[i] - mean_rx) * (ry[i] - mean_ry) for i in range(n))
    den_x = math.sqrt(sum((rx[i] - mean_rx) ** 2 for i in range(n)))
    den_y = math.sqrt(sum((ry[i] - mean_ry) ** 2 for i in range(n)))

    if den_x == 0 or den_y == 0:
        return None

    return num / (den_x * den_y)


def compute_correlation_matrix(decisions: list[dict]) -> dict:
    """모델 간 Spearman 순위 상관 행렬을 계산한다.

    Args:
        decisions: _extract_model_actions 결과 리스트

    Returns:
        {
            "matrix": {model_a: {model_b: correlation, ...}, ...},
            "highly_correlated": [(model_a, model_b, corr), ...],
            "near_identical": [(model_a, model_b, corr), ...],
            "mean_abs_correlation": float
        }
    """
    if len(decisions) < 3:
        return {
            "matrix": {},
            "highly_correlated": [],
            "near_identical": [],
            "mean_abs_correlation": 0.0,
        }

    # 모델별 action 시계열 추출
    model_series: dict[str, list[float]] = {m: [] for m in MODELS}
    valid_indices: list[int] = []

    for i, row in enumerate(decisions):
        # 모든 모델이 존재하는 행만 사용
        if all(m in row for m in MODELS):
            valid_indices.append(i)
            for m in MODELS:
                model_series[m].append(row[m])

    # 유효한 행이 부족하면 available 모델만으로 계산
    if len(valid_indices) < 3:
        # 2개 이상 공통 존재하는 모델 쌍으로 fallback
        available_models = [m for m in MODELS if sum(1 for r in decisions if m in r) >= 3]
        if len(available_models) < 2:
            return {
                "matrix": {},
                "highly_correlated": [],
                "near_identical": [],
                "mean_abs_correlation": 0.0,
            }

        model_series = {m: [] for m in available_models}
        for row in decisions:
            for m in available_models:
                if m in row:
                    model_series[m].append(row[m])
                else:
                    model_series[m].append(0.0)  # 미존재 시 neutral
    else:
        available_models = MODELS

    # 상관 행렬 계산
    matrix: dict[str, dict[str, float | None]] = {}
    abs_corrs: list[float] = []
    highly_correlated: list[tuple[str, str, float]] = []
    near_identical: list[tuple[str, str, float]] = []

    for i, m1 in enumerate(available_models):
        matrix[m1] = {}
        for j, m2 in enumerate(available_models):
            if i == j:
                matrix[m1][m2] = 1.0
                continue
            if j < i:
                # 이미 계산됨
                matrix[m1][m2] = matrix[m2][m1]
                continue

            corr = _spearman_correlation(model_series[m1], model_series[m2])
            matrix[m1][m2] = round(corr, 4) if corr is not None else None

            if corr is not None:
                abs_c = abs(corr)
                abs_corrs.append(abs_c)
                if abs_c > 0.95:
                    near_identical.append((m1, m2, round(corr, 4)))
                elif abs_c > 0.85:
                    highly_correlated.append((m1, m2, round(corr, 4)))

    mean_abs = sum(abs_corrs) / len(abs_corrs) if abs_corrs else 0.0

    return {
        "matrix": matrix,
        "highly_correlated": highly_correlated,
        "near_identical": near_identical,
        "mean_abs_correlation": round(mean_abs, 4),
    }


def detect_outlier_models(decisions: list[dict]) -> list[dict]:
    """앙상블 평균에서 2sigma 이상 이탈하는 모델을 감지한다.

    Args:
        decisions: _extract_model_actions 결과 리스트

    Returns:
        [{"model": str, "outlier_rate": float, "outlier_count": int, "total": int, "unstable": bool}, ...]
    """
    if not decisions:
        return []

    outlier_counts: dict[str, int] = {m: 0 for m in MODELS}
    total_counts: dict[str, int] = {m: 0 for m in MODELS}

    for row in decisions:
        available = [m for m in MODELS if m in row]
        if len(available) < 2:
            continue

        values = [row[m] for m in available]
        n = len(values)
        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / n
        std = math.sqrt(variance) if variance > 0 else 0.0

        for m in available:
            total_counts[m] += 1
            if std > 0 and abs(row[m] - mean) > 2 * std:
                outlier_counts[m] += 1

    results = []
    for m in MODELS:
        total = total_counts[m]
        if total == 0:
            continue
        count = outlier_counts[m]
        rate = count / total
        results.append({
            "model": m,
            "outlier_rate": round(rate, 4),
            "outlier_count": count,
            "total": total,
            "unstable": rate > 0.30,
        })

    return results


def _check_overconfidence(decisions: list[dict]) -> dict:
    """에코 챔버 및 저분산 경고를 확인한다.

    Returns:
        {
            "echo_chamber": bool,
            "echo_chamber_rate": float,
            "low_variance": bool,
            "low_variance_rate": float,
            "warnings": [str, ...]
        }
    """
    if not decisions:
        return {
            "echo_chamber": False,
            "echo_chamber_rate": 0.0,
            "low_variance": False,
            "low_variance_rate": 0.0,
            "warnings": [],
        }

    agree_count = 0
    low_var_count = 0
    valid_count = 0

    for row in decisions:
        available = [m for m in MODELS if m in row]
        if len(available) < 3:
            continue

        valid_count += 1
        values = [row[m] for m in available]

        # 방향 분류: buy(>0.3), sell(<-0.3), hold
        directions = []
        for v in values:
            if v > 0.3:
                directions.append("buy")
            elif v < -0.3:
                directions.append("sell")
            else:
                directions.append("hold")

        # 전부 같은 방향이면 echo chamber
        if len(set(directions)) == 1:
            agree_count += 1

        # 표준편차 체크
        n = len(values)
        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / n
        std = math.sqrt(variance) if variance > 0 else 0.0
        if std < 0.1:
            low_var_count += 1

    echo_rate = agree_count / valid_count if valid_count > 0 else 0.0
    low_var_rate = low_var_count / valid_count if valid_count > 0 else 0.0

    warnings = []
    echo_chamber = echo_rate > 0.80
    low_variance = low_var_rate > 0.50

    if echo_chamber:
        warnings.append(f"Echo chamber: 전체 모델 동의율 {echo_rate:.0%} (>80%) — 독립성 부족")
    if low_variance:
        warnings.append(f"Low variance: 앙상블 표준편차 <0.1 비율 {low_var_rate:.0%} (>50%) — 다양성 부족")

    return {
        "echo_chamber": echo_chamber,
        "echo_chamber_rate": round(echo_rate, 4),
        "low_variance": low_variance,
        "low_variance_rate": round(low_var_rate, 4),
        "warnings": warnings,
    }


def get_diversity_score(correlation_result: dict | None = None,
                        overconfidence: dict | None = None) -> float:
    """앙상블 다양성 점수 (0~100)를 계산한다. 높을수록 다양함.

    diversity = (1 - mean(|correlations|)) * 100
    에코 챔버/저분산 시 감점 적용.
    """
    if correlation_result is None:
        return 50.0  # 데이터 없으면 중립

    mean_abs = correlation_result.get("mean_abs_correlation", 0.0)
    base_score = (1.0 - mean_abs) * 100

    # near-identical 쌍 수에 따른 감점
    near_identical_count = len(correlation_result.get("near_identical", []))
    base_score -= near_identical_count * 10

    # 에코 챔버 / 저분산 감점
    if overconfidence:
        if overconfidence.get("echo_chamber"):
            base_score -= 15
        if overconfidence.get("low_variance"):
            base_score -= 10

    return round(max(0.0, min(100.0, base_score)), 1)


def get_diversity_summary(report: dict | None = None) -> dict:
    """사람이 읽기 쉬운 다양성 요약을 반환한다."""
    if report is None:
        return {
            "status": "NO_DATA",
            "message": "RL 어드바이저리 데이터 없음",
            "score": None,
        }

    score = report.get("diversity_score", 50.0)
    warnings = report.get("overconfidence", {}).get("warnings", [])
    highly = report.get("correlation", {}).get("highly_correlated", [])
    near_id = report.get("correlation", {}).get("near_identical", [])
    outliers = [o for o in report.get("outliers", []) if o.get("unstable")]

    if score >= 70:
        status = "HEALTHY"
        message = "앙상블 다양성 양호"
    elif score >= 40:
        status = "WARNING"
        message = "앙상블 다양성 주의"
    else:
        status = "CRITICAL"
        message = "앙상블 다양성 위험 — 모델 중복/편향 심각"

    details = []
    for m1, m2, corr in near_id:
        details.append(f"거의 동일: {m1} <-> {m2} (r={corr})")
    for m1, m2, corr in highly:
        details.append(f"높은 상관: {m1} <-> {m2} (r={corr})")
    for o in outliers:
        details.append(f"불안정 모델: {o['model']} (이상치율 {o['outlier_rate']:.0%})")
    details.extend(warnings)

    return {
        "status": status,
        "message": message,
        "score": score,
        "details": details,
    }


def check_diversity(cached_decisions: list[dict] | None = None) -> dict | None:
    """메인 다양성 검증 함수.

    Args:
        cached_decisions: phase_cache에서 전달받은 캐시 데이터 (None이면 직접 조회)

    Returns:
        전체 다양성 리포트 dict 또는 RL 데이터 없으면 None
    """
    # 데이터 소스: 캐시 우선, 없으면 직접 조회
    if cached_decisions is not None:
        raw_decisions = cached_decisions
    else:
        raw_decisions = _fetch_decisions(days=7)

    if not raw_decisions:
        return None

    # 모델별 action 추출
    model_actions = _extract_model_actions(raw_decisions)
    if not model_actions:
        return None  # rl_advisory 데이터 없음 — graceful 종료

    # 상관 분석
    correlation = compute_correlation_matrix(model_actions)

    # 이상치 감지
    outliers = detect_outlier_models(model_actions)

    # 과신 경고
    overconfidence = _check_overconfidence(model_actions)

    # 다양성 점수
    score = get_diversity_score(correlation, overconfidence)

    report = {
        "diversity_score": score,
        "sample_count": len(model_actions),
        "correlation": correlation,
        "outliers": outliers,
        "overconfidence": overconfidence,
        "last_updated": datetime.now(KST).isoformat(),
    }

    # 상태 파일 저장
    try:
        from scripts.atomic_write import atomic_json_save
        atomic_json_save(DIVERSITY_FILE, report)
    except ImportError:
        DIVERSITY_FILE.parent.mkdir(parents=True, exist_ok=True)
        DIVERSITY_FILE.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        print(f"[model_diversity] 저장 실패: {e}", file=sys.stderr)

    return report


# ── CLI ──────────────────────────────────────────────────

if __name__ == "__main__":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    json_mode = "--json" in sys.argv

    report = check_diversity()

    if report is None:
        if json_mode:
            print(json.dumps({"status": "NO_DATA"}, ensure_ascii=False))
        else:
            print("RL 어드바이저리 데이터 없음 — 다양성 분석 스킵")
        sys.exit(0)

    if json_mode:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        sys.exit(0)

    # 사람 친화적 출력
    summary = get_diversity_summary(report)
    score = report["diversity_score"]
    samples = report["sample_count"]

    print("=== RL 모델 다양성 검증 ===\n")
    print(f"  다양성 점수: {score}/100 [{summary['status']}]")
    print(f"  분석 샘플: {samples}건 (최근 7일)\n")

    # 상관 행렬
    corr = report["correlation"]
    matrix = corr.get("matrix", {})
    if matrix:
        print("  상관 행렬:")
        models_in_matrix = list(matrix.keys())
        header = "          " + "  ".join(f"{m:>10s}" for m in models_in_matrix)
        print(f"  {header}")
        for m1 in models_in_matrix:
            vals = []
            for m2 in models_in_matrix:
                v = matrix[m1].get(m2)
                vals.append(f"{v:>10.3f}" if v is not None else f"{'N/A':>10s}")
            print(f"  {m1:>10s}  {'  '.join(vals)}")
        print()

    # 경고
    for m1, m2, c in corr.get("near_identical", []):
        print(f"  [!] 거의 동일: {m1} <-> {m2} (r={c})")
    for m1, m2, c in corr.get("highly_correlated", []):
        print(f"  [!] 높은 상관: {m1} <-> {m2} (r={c})")

    # 이상치
    for o in report["outliers"]:
        flag = " [불안정]" if o["unstable"] else ""
        print(f"  {o['model']}: 이상치율 {o['outlier_rate']:.0%} ({o['outlier_count']}/{o['total']}){flag}")

    # 과신
    oc = report["overconfidence"]
    for w in oc.get("warnings", []):
        print(f"  [!] {w}")

    print(f"\n  저장: {DIVERSITY_FILE}")
