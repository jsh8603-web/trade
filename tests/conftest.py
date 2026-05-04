"""테스트 공용 픽스처.

여러 테스트 파일에서 중복되던 stub/픽스처를 한곳에 모은다.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 프로젝트 루트와 scripts/ 를 sys.path에 추가 — 모든 테스트가 동일 경로 사용
PROJECT_DIR = Path(__file__).resolve().parent.parent
for _p in (PROJECT_DIR, PROJECT_DIR / "scripts"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)


@pytest.fixture
def stub_file_exists():
    """notify_telegram.send_photo 의 파일 검증(Path.exists/is_file/stat)을 바이패스.

    텔레그램 send_photo는 v1.32.5에서 파일 존재/크기 검증을 추가했다.
    실제 파일 없이 mock_post 만으로 동작 시키려면 Path 자체를 mock해야 한다.
    """
    stat_result = MagicMock(st_size=1024)
    with patch("notify_telegram.Path") as mock_path_cls:
        inst = MagicMock()
        inst.exists.return_value = True
        inst.is_file.return_value = True
        inst.stat.return_value = stat_result
        inst.name = "chart.png"
        mock_path_cls.return_value = inst
        yield


@pytest.fixture
def force_machine_primary(monkeypatch):
    """MACHINE_ROLE=primary 강제 + utils.machine 캐시 리셋.

    매매 DB 쓰기 가드(utils.machine.skip_trade_db)를 우회하여,
    매매 로직 자체를 검증하는 테스트가 worker 스킵에 걸리지 않게 한다.
    """
    monkeypatch.setenv("MACHINE_ROLE", "primary")
    try:
        import utils.machine as _mm
        _mm.reset_cache()
    except Exception:
        pass
    yield
    try:
        import utils.machine as _mm
        _mm.reset_cache()
    except Exception:
        pass
