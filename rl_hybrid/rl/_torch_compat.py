"""torch 버전 호환 헬퍼.

torch <2.4 에는 `weights_only` 파라미터가 없으므로 TypeError가 발생한다.
모델 로드 시 동일한 try/except 패턴을 5+곳에서 반복하지 않도록 한 함수로 통합.
"""

from __future__ import annotations

from typing import Any

import torch


def safe_torch_load(path: str, *, weights_only: bool = False, **kwargs: Any) -> Any:
    """torch.load의 weights_only 호환 래퍼.

    torch >=2.4: weights_only 파라미터 사용
    torch <2.4: weights_only 미지원 → TypeError 발생 시 파라미터 빼고 재시도

    Args:
        path: 체크포인트 경로
        weights_only: 안전 로드 모드 (가능한 경우)
        **kwargs: torch.load의 나머지 인자 (map_location 등)
    """
    try:
        return torch.load(path, weights_only=weights_only, **kwargs)
    except TypeError:
        # torch <2.4: weights_only 파라미터 없음
        return torch.load(path, **kwargs)
