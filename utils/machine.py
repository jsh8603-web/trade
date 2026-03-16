"""
머신 역할/이름 판별 유틸리티.

4대 컴퓨터가 동일 앱을 실행하므로, 매매 DB 기록은 주 컴퓨터(Mac Mini)에서만 수행한다.
학습/훈련 기록은 각 머신에서 독립적으로 기록한다.
단타/초단타/김치랑 실행 데이터에는 MACHINE_NAME 태그를 붙여 중복 방지 + 머신별 성과 비교.

.env 설정:
  MACHINE_ROLE=primary   # Mac Mini (매매 DB 기록 담당)
  MACHINE_ROLE=worker    # 그 외 (매매 DB 기록 스킵)
  MACHINE_NAME=pc128     # 머신 식별자 (pc128, pc36, mac-mini, jsh8603)
"""

import logging
import os
import platform

logger = logging.getLogger(__name__)

_role: str | None = None
_name: str | None = None


def _get_role() -> str:
    global _role
    if _role is None:
        _role = os.environ.get("MACHINE_ROLE", "primary").lower().strip()
    return _role


def get_machine_name() -> str:
    """머신 이름 반환. MACHINE_NAME 환경변수 → hostname 자동 감지."""
    global _name
    if _name is None:
        _name = os.environ.get("MACHINE_NAME", "").strip()
        if not _name:
            # 자동 감지: hostname 기반
            hostname = platform.node().lower()
            if "128" in hostname or "hospital" in hostname:
                _name = "pc128"
            elif "36" in hostname or "drjay" in hostname:
                _name = "pc36"
            elif "mac" in hostname or "mini" in hostname:
                _name = "mac-mini"
            elif "jsh" in hostname:
                _name = "jsh8603"
            else:
                _name = hostname[:20] or "unknown"
        logger.info(f"머신 이름: {_name}")
    return _name


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
