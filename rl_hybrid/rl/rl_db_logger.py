"""RL DB 로거 — 모든 RL 훈련/추론/모델 버전을 DB에 기록

모든 RL 모듈이 이 모듈을 통해 DB에 기록한다.
core.db 어댑터(INV_DB_BACKEND=sqlite 기본) 경유 — 백엔드 무관.
"""

import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.db import db

logger = logging.getLogger("rl.db_logger")


def _clean(data: dict) -> dict:
    """None 값 필터링 + datetime → ISO 문자열. dict/list 는 어댑터가 직렬화."""
    clean = {}
    for k, v in data.items():
        if v is None:
            continue
        if isinstance(v, datetime):
            clean[k] = v.isoformat()
        else:
            clean[k] = v
    return clean


def _post(table: str, data: dict) -> Optional[dict]:
    """단일 레코드 삽입 (core.db 어댑터)"""
    try:
        return db.insert(table, _clean(data))
    except Exception as e:
        logger.error(f"DB insert 예외 [{table}]: {e}")
        return None


def _patch(table: str, match: dict, data: dict) -> bool:
    """레코드 업데이트 (core.db 어댑터)"""
    clean = {k: (v.isoformat() if isinstance(v, datetime) else v)
             for k, v in data.items() if v is not None}
    if not clean:
        return False
    try:
        n = db.update(table, match, clean)
        return n > 0
    except Exception as e:
        logger.error(f"DB update 예외 [{table}]: {e}")
        return False


# ============================================================
# 1. 훈련 사이클 기록
# ============================================================

def log_training_start(
    cycle_type: str,
    algorithm: str,
    module: str,
    training_steps: int = None,
    training_epochs: int = None,
    data_days: int = None,
    data_count: int = None,
    obs_dim: int = 42,
    morl_enabled: bool = False,
    interval: str = "4h",
    training_meta: dict = None,
) -> Optional[str]:
    """훈련 시작 기록 — cycle_id 반환

    Args:
        training_meta: 메타 결정 정보 (왜 이 훈련이 선택되었는지, 효과 분석 결과 등)
    """
    cycle_id = str(uuid.uuid4())
    result = _post("rl_training_cycles", {
        "id": cycle_id,
        "cycle_type": cycle_type,
        "algorithm": algorithm,
        "module": module,
        "training_steps": training_steps,
        "training_epochs": training_epochs,
        "data_days": data_days,
        "data_count": data_count,
        "obs_dim": obs_dim,
        "morl_enabled": morl_enabled,
        "interval": interval,
        "training_meta": training_meta,
        "status": "running",
        "started_at": datetime.now(timezone.utc),
    })
    if result:
        logger.info(f"훈련 사이클 시작 기록: {cycle_id[:8]}... [{algorithm}/{module}]")
        return cycle_id
    return cycle_id  # DB 실패해도 ID는 반환


def log_training_complete(
    cycle_id: str,
    avg_return_pct: float = None,
    avg_sharpe: float = None,
    avg_mdd: float = None,
    avg_trades: float = None,
    policy_loss: float = None,
    value_loss: float = None,
    entropy: float = None,
    direction_accuracy: float = None,
    q_loss: float = None,
    cql_penalty: float = None,
    best_eval_loss: float = None,
    n_sequences: int = None,
    context_length: int = None,
    model_version: str = None,
    model_path: str = None,
    baseline_sharpe: float = None,
    improved: bool = None,
    elapsed_seconds: float = None,
    status: str = "completed",
    error_message: str = None,
):
    """훈련 완료/실패 기록"""
    _patch("rl_training_cycles", {"id": cycle_id}, {
        "avg_return_pct": avg_return_pct,
        "avg_sharpe": avg_sharpe,
        "avg_mdd": avg_mdd,
        "avg_trades": avg_trades,
        "policy_loss": policy_loss,
        "value_loss": value_loss,
        "entropy": entropy,
        "direction_accuracy": direction_accuracy,
        "q_loss": q_loss,
        "cql_penalty": cql_penalty,
        "best_eval_loss": best_eval_loss,
        "n_sequences": n_sequences,
        "context_length": context_length,
        "model_version": model_version,
        "model_path": model_path,
        "baseline_sharpe": baseline_sharpe,
        "improved": improved,
        "elapsed_seconds": elapsed_seconds,
        "status": status,
        "error_message": error_message,
        "completed_at": datetime.now(timezone.utc),
    })
    logger.info(f"훈련 사이클 완료 기록: {cycle_id[:8]}... [status={status}]")


# ============================================================
# 2. 추론 예측 기록
# ============================================================

def log_prediction(
    decision_id: str = None,
    cycle_id: str = None,
    ensemble_action: float = None,
    ensemble_direction: str = None,
    num_models: int = None,
    sb3_action: float = None,
    sb3_version: str = None,
    dt_action: float = None,
    dt_version: str = None,
    multi_agent_action: float = None,
    multi_agent_direction: str = None,
    multi_agent_scalp_action: float = None,
    multi_agent_swing_action: float = None,
    offline_action: float = None,
    offline_version: str = None,
    btc_price: float = None,
    rsi_14: float = None,
    fgi: int = None,
    danger_score: float = None,
    opportunity_score: float = None,
) -> Optional[str]:
    """RL 앙상블 추론 결과 기록"""
    pred_id = str(uuid.uuid4())
    result = _post("rl_model_predictions", {
        "id": pred_id,
        "decision_id": decision_id,
        "cycle_id": cycle_id,
        "ensemble_action": ensemble_action,
        "ensemble_direction": ensemble_direction,
        "num_models": num_models,
        "sb3_action": sb3_action,
        "sb3_version": sb3_version,
        "dt_action": dt_action,
        "dt_version": dt_version,
        "multi_agent_action": multi_agent_action,
        "multi_agent_direction": multi_agent_direction,
        "multi_agent_scalp_action": multi_agent_scalp_action,
        "multi_agent_swing_action": multi_agent_swing_action,
        "offline_action": offline_action,
        "offline_version": offline_version,
        "btc_price": btc_price,
        "rsi_14": rsi_14,
        "fgi": fgi,
        "danger_score": danger_score,
        "opportunity_score": opportunity_score,
    })
    if result:
        logger.info(f"추론 기록: {pred_id[:8]}... [dir={ensemble_direction}, models={num_models}]")
    return pred_id


def update_prediction_outcome(
    prediction_id: str,
    price_after_4h: float = None,
    price_after_24h: float = None,
    btc_price_at_prediction: float = None,
):
    """사후 평가 업데이트 (4h/24h 후 가격)"""
    data = {}
    if price_after_4h is not None:
        data["price_after_4h"] = price_after_4h
        if btc_price_at_prediction:
            ret = (price_after_4h - btc_price_at_prediction) / btc_price_at_prediction * 100
            data["return_after_4h"] = round(ret, 4)
    if price_after_24h is not None:
        data["price_after_24h"] = price_after_24h
        if btc_price_at_prediction:
            ret = (price_after_24h - btc_price_at_prediction) / btc_price_at_prediction * 100
            data["return_after_24h"] = round(ret, 4)

    if data:
        _patch("rl_model_predictions", {"id": prediction_id}, data)


# ============================================================
# 3. 모델 버전 기록
# ============================================================

def log_model_version(
    version_id: str,
    algorithm: str,
    model_path: str = None,
    sharpe_ratio: float = None,
    total_return_pct: float = None,
    max_drawdown: float = None,
    eval_episodes: int = None,
    training_steps: int = None,
    training_days: int = None,
    training_config: dict = None,
    is_active: bool = False,
    notes: str = None,
    promoted_from: str = None,
) -> Optional[str]:
    """모델 버전 등록 (registry.json → DB 미러링)"""
    result = _post("rl_model_versions", {
        "version_id": version_id,
        "algorithm": algorithm,
        "model_path": model_path,
        "sharpe_ratio": sharpe_ratio,
        "total_return_pct": total_return_pct,
        "max_drawdown": max_drawdown,
        "eval_episodes": eval_episodes,
        "training_steps": training_steps,
        "training_days": training_days,
        "training_config": training_config,
        "is_active": is_active,
        "notes": notes,
        "promoted_from": promoted_from,
    })
    if result:
        logger.info(f"모델 버전 DB 기록: {version_id} [{algorithm}]")
    return version_id


def update_model_version(version_id: str, **kwargs):
    """모델 버전 정보 업데이트 (is_active, live 성과 등)"""
    _patch("rl_model_versions", {"version_id": version_id}, kwargs)


def deactivate_all_models():
    """모든 모델 비활성화 (새 모델 승격 전)"""
    try:
        db.update(
            "rl_model_versions",
            {"is_active": "eq.true"},
            {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()},
        )
    except Exception as e:
        logger.error(f"모델 비활성화 실패: {e}")


# ============================================================
# 4. 파라미터 튜닝 기록
# ============================================================

def log_parameter_tuning(
    parameter_name: str,
    old_value: float,
    new_value: float,
    change_reason: str = "auto_tuning",
    before_sharpe: float = None,
    after_sharpe: float = None,
    before_return: float = None,
    after_return: float = None,
    approved: bool = None,
    rolled_back: bool = False,
    rollback_reason: str = None,
):
    """Self-Tuning 파라미터 변경 기록"""
    _post("rl_parameter_tuning", {
        "parameter_name": parameter_name,
        "old_value": old_value,
        "new_value": new_value,
        "change_reason": change_reason,
        "before_sharpe": before_sharpe,
        "after_sharpe": after_sharpe,
        "before_return": before_return,
        "after_return": after_return,
        "approved": approved,
        "rolled_back": rolled_back,
        "rollback_reason": rollback_reason,
    })
    logger.info(
        f"파라미터 튜닝 기록: {parameter_name} "
        f"{old_value:.6f} → {new_value:.6f} [{change_reason}]"
    )


# ============================================================
# 5. 쿼리 헬퍼
# ============================================================

def get_recent_training_cycles(
    algorithm: str = None,
    module: str = None,
    limit: int = 20,
) -> list[dict]:
    """최근 훈련 사이클 조회"""
    filters = {}
    if algorithm:
        filters["algorithm"] = f"eq.{algorithm}"
    if module:
        filters["module"] = f"eq.{module}"
    try:
        return db.select(
            "rl_training_cycles",
            filters=filters or None,
            order="created_at.desc",
            limit=limit,
        )
    except Exception:
        return []


def get_training_impact_analysis(days: int = 30) -> dict:
    """훈련 효과 분석: 알고리즘별 훈련 후 PnL 변화를 추적한다.

    rl_training_cycles + portfolio_snapshots를 조인하여
    훈련 후 24h/72h 실제 성과를 분석한다.

    Returns:
        {
            "algorithms": {algo: {"trainings": N, "avg_pnl_24h": X, "avg_pnl_72h": Y, "improved_rate": Z}},
            "recommended_priority": [algo1, algo2, ...],  # 효과 큰 순
            "skip_candidates": [algo, ...],  # 3회 이상 훈련 + 개선율 < 30%
        }
    """
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    try:
        # 1) 최근 훈련 사이클 조회 (완료된 것만)
        cycles = db.select(
            "rl_training_cycles",
            select="id,algorithm,module,avg_sharpe,avg_return_pct,completed_at,pnl_24h_after,pnl_72h_after",
            filters={"status": "eq.completed", "created_at": f"gte.{cutoff}"},
            order="completed_at.desc",
            limit=100,
        )
        if not cycles:
            return {"algorithms": {}, "recommended_priority": [], "skip_candidates": []}

        # 2) 알고리즘별 집계
        algo_stats: dict[str, dict] = {}
        for c in cycles:
            algo = c.get("algorithm", "unknown")
            if algo not in algo_stats:
                algo_stats[algo] = {
                    "trainings": 0,
                    "pnl_24h_list": [],
                    "pnl_72h_list": [],
                    "sharpe_list": [],
                    "improved_count": 0,
                }
            stats = algo_stats[algo]
            stats["trainings"] += 1

            pnl_24h = c.get("pnl_24h_after")
            pnl_72h = c.get("pnl_72h_after")
            sharpe = c.get("avg_sharpe")

            if pnl_24h is not None:
                stats["pnl_24h_list"].append(pnl_24h)
                if pnl_24h > 0:
                    stats["improved_count"] += 1
            if pnl_72h is not None:
                stats["pnl_72h_list"].append(pnl_72h)
            if sharpe is not None:
                stats["sharpe_list"].append(sharpe)

        # 3) 요약 계산
        algorithms = {}
        for algo, stats in algo_stats.items():
            pnl_24h_list = stats["pnl_24h_list"]
            pnl_72h_list = stats["pnl_72h_list"]
            n = stats["trainings"]
            improved_rate = stats["improved_count"] / len(pnl_24h_list) if pnl_24h_list else 0.5

            algorithms[algo] = {
                "trainings": n,
                "avg_pnl_24h": round(sum(pnl_24h_list) / len(pnl_24h_list), 4) if pnl_24h_list else None,
                "avg_pnl_72h": round(sum(pnl_72h_list) / len(pnl_72h_list), 4) if pnl_72h_list else None,
                "avg_sharpe": round(sum(stats["sharpe_list"]) / len(stats["sharpe_list"]), 4) if stats["sharpe_list"] else None,
                "improved_rate": round(improved_rate, 4),
                "data_points": len(pnl_24h_list),
            }

        # 4) 우선순위 정렬: improved_rate 기준 내림차순
        ranked = sorted(
            algorithms.items(),
            key=lambda x: (x[1].get("improved_rate", 0), x[1].get("avg_pnl_24h") or 0),
            reverse=True,
        )
        recommended_priority = [algo for algo, _ in ranked]

        # 5) 스킵 후보: 3회 이상 훈련 + 개선율 < 30%
        skip_candidates = [
            algo for algo, s in algorithms.items()
            if s["trainings"] >= 3 and s["data_points"] >= 3 and s["improved_rate"] < 0.3
        ]

        return {
            "algorithms": algorithms,
            "recommended_priority": recommended_priority,
            "skip_candidates": skip_candidates,
        }

    except Exception as e:
        logger.error(f"훈련 효과 분석 예외: {e}")
        return {"algorithms": {}, "recommended_priority": [], "skip_candidates": []}


def get_model_prediction_accuracy(version_id: str = None) -> dict:
    """모델 예측 정확도 조회"""
    sql = ("SELECT prediction_quality FROM rl_model_predictions "
           "WHERE prediction_quality IS NOT NULL")
    params: tuple = ()
    if version_id:
        sql += (" AND (sb3_version = ? OR dt_version = ? OR offline_version = ?)")
        params = (version_id, version_id, version_id)

    try:
        results = db.execute_raw(sql, params)
        total = len(results)
        correct = sum(1 for r in results if r["prediction_quality"] == "correct")
        return {
            "total": total,
            "correct": correct,
            "accuracy": correct / total if total > 0 else 0,
        }
    except Exception:
        return {}
