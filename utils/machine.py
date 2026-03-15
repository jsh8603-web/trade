"""
머신 역할 판별 유틸리티.

3대 컴퓨터가 동일 앱을 실행하므로, 매매 DB 기록은 주 컴퓨터(Mac Mini)에서만 수행한다.
학습/훈련 기록은 각 머신에서 독립적으로 기록한다.

.env 설정:
  MACHINE_ROLE=primary   # Mac Mini (매매 DB 기록 담당)
  MACHINE_ROLE=worker    # 그 외 (매매 DB 기록 스킵)
"""

import logging
import os

logger = logging.getLogger(__name__)

_role: str | None = None


def _get_role() -> str:
    global _role
    if _role is None:
        _role = os.environ.get("MACHINE_ROLE", "primary").lower().strip()
    return _role


def is_primary() -> bool:
    """이 머신이 매매 DB 기록 담당(primary)인지 반환."""
    return _get_role() == "primary"


def skip_trade_db(table: str) -> bool:
    """매매 관련 테이블 기록을 스킵해야 하면 True 반환.

    - primary 머신: 항상 False (기록 수행)
    - worker 머신: 매매 테이블이면 True (스킵), 훈련 테이블이면 False (기록)
    """
    if is_primary():
        return False

    # 훈련/학습 테이블 — 모든 머신에서 기록 허용
    TRAINING_TABLES = {
        "rl_training_log", "rl_training_cycles", "rl_training_results",
        "rl_model_versions", "rl_backtest_results",
        "scalp_training_tasks", "scalp_model_versions", "scalp_market_snapshot",
        "rag_analysis_vectors",
        "app_changelog",
    }

    if table in TRAINING_TABLES:
        return False

    # 그 외 매매 관련 테이블 → worker는 스킵
    logger.info("[DB SKIP] worker 머신 — %s 테이블 기록 스킵", table)
    return True
