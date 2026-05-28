"""SO-3 테스트: core/strategy.py Strategy ABC + StrategyFamily enum."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
for _p in (PROJECT_DIR,):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

from core.strategy import Strategy, StrategyFamily


class _ConcreteStrategy(Strategy):
    @property
    def family(self) -> StrategyFamily:
        return StrategyFamily.DIRECTIONAL

    @property
    def name(self) -> str:
        return "test_strategy"


def test_import_ok():
    from core.strategy import Strategy, StrategyFamily  # noqa: F401


def test_abstract_instantiation_raises():
    with pytest.raises(TypeError):
        Strategy()  # type: ignore[abstract]


def test_concrete_instantiation_ok():
    s = _ConcreteStrategy()
    assert isinstance(s, Strategy)


def test_strategy_family_three_members():
    members = {f.value for f in StrategyFamily}
    assert "directional" in members
    assert "market_neutral" in members
    assert "hft" in members
    assert len(members) == 3


def test_strategy_family_enum_access():
    assert StrategyFamily.DIRECTIONAL == StrategyFamily("directional")
    assert StrategyFamily.MARKET_NEUTRAL == StrategyFamily("market_neutral")
    assert StrategyFamily.HFT == StrategyFamily("hft")


def test_concrete_family_correct():
    s = _ConcreteStrategy()
    assert s.family == StrategyFamily.DIRECTIONAL
    assert s.name == "test_strategy"


def test_scalp_ml_dir_unchanged():
    """scalp_ml/ 디렉토리 파일 git diff 0 — SO-3에서 미변경 확인."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "scalp_ml/"],
        cwd=str(PROJECT_DIR),
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == "", f"scalp_ml/ 변경됨: {result.stdout}"


def test_kimchirang_dir_unchanged():
    """kimchirang/ 디렉토리 파일 git diff 0 — SO-3에서 미변경 확인."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "kimchirang/"],
        cwd=str(PROJECT_DIR),
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == "", f"kimchirang/ 변경됨: {result.stdout}"
