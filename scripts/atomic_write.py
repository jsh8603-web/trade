"""
Atomic JSON write utility — write to .tmp then rename to prevent corruption.

Usage:
    from scripts.atomic_write import atomic_json_save

    atomic_json_save(Path("data/state.json"), {"key": "value"})
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def atomic_json_save(path: Path, data: dict, indent: int = 2) -> None:
    """Atomically write JSON data to a file.

    Writes to a temporary file in the same directory, then renames.
    On POSIX systems, os.replace is atomic. On Windows, it's as close
    as we can get.

    Args:
        path: Target file path
        data: Dictionary to serialize as JSON
        indent: JSON indent level
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, ensure_ascii=False, indent=indent)

    # Create temp file in the same directory (same filesystem for atomic rename)
    fd, tmp_path = tempfile.mkstemp(
        suffix=".tmp",
        prefix=path.stem + "_",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, str(path))
    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
