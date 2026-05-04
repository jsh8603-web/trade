"""보상 함수 공용 유틸.

reward.py / reward_v7.py / reward_v8.py 가 공통으로 사용하는
0 나눗셈 방어 패턴을 한곳에 모은다.
"""

from __future__ import annotations

_EPS = 1e-8


def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    """분모가 0(또는 거의 0)이면 default 반환.

    포트폴리오 가치/MDD 계산에서 파산(value=0) 케이스를 방어한다.
    """
    if denominator > _EPS:
        return numerator / denominator
    return default
