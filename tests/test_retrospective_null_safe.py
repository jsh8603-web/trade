"""
Unit tests for scripts/retrospective.py — v1.32.1 null-safety fixes.

Targets:
  - UTF-8 reconfigure block (lines 25-31): must not crash when stdout.encoding
    is None or when reconfigure() is missing.
  - f-string NULL defense in report() (lines 514-553): current_price,
    outcome_1h/4h/24h_pct, trade_amount may be None — formatting must not
    raise TypeError.

Run:
  python -m pytest tests/test_retrospective_null_safe.py -v
"""

from __future__ import annotations

import importlib
import io
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════


def _import_retrospective():
    """Import (or re-import) scripts.retrospective fresh."""
    if "scripts.retrospective" in sys.modules:
        del sys.modules["scripts.retrospective"]
    return importlib.import_module("scripts.retrospective")


def _build_db_select_side_effect(accuracy=None, missed=None, bad=None):
    """
    Construct a side_effect for core.db.db.select that routes by the
    requested view (table name) to the three views queried in report().

    db.select(table, *, filters=None, order=None, limit=None, select=...)
    """
    accuracy = accuracy if accuracy is not None else []
    missed = missed if missed is not None else []
    bad = bad if bad is not None else []

    def _side_effect(table, *args, **kwargs):
        if table == "v_decision_accuracy":
            return accuracy
        if table == "v_missed_opportunities":
            return missed
        if table == "v_bad_trades":
            return bad
        return []

    return _side_effect


# ═══════════════════════════════════════════════════════════════
# f-string NULL defense tests (report() — lines 514-553)
# ═══════════════════════════════════════════════════════════════


class TestReportNullSafety:
    """report() 함수가 None 값을 포함한 행을 받아도 TypeError 없이 출력."""

    def test_report_row_with_null_current_price(self, capsys):
        """current_price=None 인 v_missed_opportunities 행이 와도 크래시하지 않음."""
        mod = _import_retrospective()

        missed = [
            {
                "created_at": "2026-04-20T10:30:00+09:00",
                "current_price": None,  # ← NULL
                "outcome_24h_pct": 5.2,
                "fear_greed_value": 25,
                "rsi_value": 32,
                "reason": "극공포 매수 관망 결정",
            }
        ]
        bad = [
            {
                "created_at": "2026-04-20T11:00:00+09:00",
                "current_price": None,  # ← NULL
                "outcome_4h_pct": -2.1,
                "trade_amount": 50000,
                "reason": "고점 매수",
            }
        ]

        with patch.object(
            mod.db, "select",
            side_effect=_build_db_select_side_effect(missed=missed, bad=bad),
        ):
            mod.report()

        captured = capsys.readouterr().out
        # 크래시 없이 섹션이 출력되어야 함
        assert "놓친 기회" in captured
        assert "잘못된 매수" in captured
        # None이 0으로 fallback 되어 "0" 가격으로 포맷됨
        assert "가격: 0" in captured

    def test_report_row_with_null_trade_amount(self, capsys):
        """trade_amount=None 인 v_bad_trades 행도 '{:,}' 포맷 깨지지 않음."""
        mod = _import_retrospective()

        bad = [
            {
                "created_at": "2026-04-20T12:00:00+09:00",
                "current_price": 130000000,
                "outcome_4h_pct": -3.5,
                "trade_amount": None,  # ← NULL
                "reason": "손절 실패 케이스",
            }
        ]

        with patch.object(
            mod.db, "select",
            side_effect=_build_db_select_side_effect(bad=bad),
        ):
            mod.report()  # TypeError가 나면 여기서 터짐

        captured = capsys.readouterr().out
        assert "잘못된 매수" in captured
        # trade_amount None → 0 fallback, "금액: 0" 포함
        assert "금액: 0" in captured

    def test_report_row_with_null_outcome_pcts(self, capsys):
        """outcome_1h_pct / outcome_4h_pct / outcome_24h_pct 셋 다 None 동시."""
        mod = _import_retrospective()

        accuracy = [
            {
                "decision": "buy",
                "source": "agent",
                "total": 10,
                "accuracy_1h": None,   # ← NULL
                "avg_1h_pct": None,    # ← NULL
                "accuracy_4h": None,   # ← NULL
                "avg_4h_pct": None,    # ← NULL
                "accuracy_24h": None,  # ← NULL
                "avg_24h_pct": None,   # ← NULL
            }
        ]
        missed = [
            {
                "created_at": "2026-04-20T13:00:00+09:00",
                "current_price": 130000000,
                "outcome_24h_pct": None,  # ← NULL
                "fear_greed_value": None,
                "rsi_value": None,
                "reason": None,
            }
        ]
        bad = [
            {
                "created_at": "2026-04-20T14:00:00+09:00",
                "current_price": None,
                "outcome_4h_pct": None,
                "trade_amount": None,
                "reason": None,
            }
        ]

        with patch.object(
            mod.db, "select",
            side_effect=_build_db_select_side_effect(
                accuracy=accuracy, missed=missed, bad=bad
            ),
        ):
            # 이 호출이 TypeError 없이 완주해야 한다
            mod.report()

        captured = capsys.readouterr().out
        # 세 섹션 모두 출력되어야 하고, 대시("-") fallback 사용
        assert "결정 정확도" in captured
        assert "놓친 기회" in captured
        assert "잘못된 매수" in captured
        # accuracy None 값들은 "-"로 치환되어야 함
        assert "-" in captured


# ═══════════════════════════════════════════════════════════════
# UTF-8 reconfigure block tests (lines 25-31)
# ═══════════════════════════════════════════════════════════════


class TestUtf8ReconfigureSafety:
    """import 단계의 stdout.reconfigure 블록이 어떤 stdout 상태에서도 안 터짐."""

    def test_utf8_reconfigure_doesnt_crash_when_stdout_has_no_encoding(self):
        """
        stdout.encoding 이 None 이거나 reconfigure 가 없어도 import 단계에서
        예외가 발생하면 안 된다.

        검증 방법: 서브프로세스에서 sys.stdout을 encoding=None / reconfigure
        없음으로 치환한 뒤 retrospective 모듈을 import 시도한다.
        """
        project_dir = str(PROJECT_DIR)

        # Case 1: stdout.encoding is None
        code_none_encoding = (
            "import sys, io\n"
            "sys.path.insert(0, r'" + project_dir + "')\n"
            "class FakeStdout:\n"
            "    encoding = None\n"
            "    def write(self, s): pass\n"
            "    def flush(self): pass\n"
            "sys.stdout = FakeStdout()\n"
            "import scripts.retrospective\n"
            "print('OK', file=sys.stderr)\n"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code_none_encoding],
            capture_output=True, text=True, timeout=30,
        )
        assert proc.returncode == 0, (
            f"import crashed with encoding=None.\n"
            f"stdout={proc.stdout!r}\nstderr={proc.stderr!r}"
        )

        # Case 2: stdout has no reconfigure() attribute (e.g. older wrappers)
        code_no_reconfigure = (
            "import sys\n"
            "sys.path.insert(0, r'" + project_dir + "')\n"
            "class FakeStdout:\n"
            "    encoding = 'cp949'  # triggers reconfigure attempt\n"
            "    def write(self, s): pass\n"
            "    def flush(self): pass\n"
            "    # 의도적으로 reconfigure 없음\n"
            "sys.stdout = FakeStdout()\n"
            "sys.stderr = FakeStdout()\n"
            "import scripts.retrospective\n"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code_no_reconfigure],
            capture_output=True, text=True, timeout=30,
        )
        assert proc.returncode == 0, (
            f"import crashed when stdout lacks reconfigure().\n"
            f"stdout={proc.stdout!r}\nstderr={proc.stderr!r}"
        )

    def test_utf8_reconfigure_inline_reload_is_safe(self):
        """
        같은 프로세스에서 importlib.reload로 재import 해도 문제가 없어야 한다.
        (UTF-8 블록이 예외를 swallow 하는지 확인)
        """
        import scripts.retrospective as retro_mod

        # stdout을 encoding 없는 fake로 교체하고 reload
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        try:
            class FakeStdout(io.StringIO):
                encoding = None  # type: ignore[assignment]

            sys.stdout = FakeStdout()
            sys.stderr = FakeStdout()
            # reload 자체가 예외 없이 성공해야 함
            importlib.reload(retro_mod)
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
