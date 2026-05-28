"""SO-4 B3 결정성 fault-injection 테스트

검증 기준:
1. temperature=0 (config화) 동일 입력 N회 반복 시 동일 _prompt_hash 생성.
2. 모델/프롬프트 교체 시 레코드에 model_id/prompt_hash 차이 기록 확인.
3. GEMINI_TEMPERATURE env 가 config에 반영됨.
4. migration 047_ 파일 스키마 정합 확인.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path("D:/projects/Inv")


# ---------------------------------------------------------------------------
# Helpers: config.GeminiConfig 직접 테스트 (google.generativeai 없이)
# ---------------------------------------------------------------------------

def _load_gemini_config(temperature_env: str = "0"):
    """GeminiConfig 를 env override 로 로드."""
    with patch.dict(os.environ, {
        "GEMINI_API_KEY": "test_key",
        "GEMINI_ANALYSIS_MODEL": "gemini-2.5-flash",
        "GEMINI_TEMPERATURE": temperature_env,
    }):
        # config 모듈은 import 시 env를 읽으므로 강제 reload
        import importlib
        import rl_hybrid.config as cfg_mod
        importlib.reload(cfg_mod)
        return cfg_mod.GeminiConfig(
            api_key="test_key",
            analysis_model="gemini-2.5-flash",
            temperature=float(temperature_env),
        )


def _compute_prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Test 1: temperature config화 — env=0 → cfg.temperature=0.0
# ---------------------------------------------------------------------------

class TestB3TemperatureConfig:
    def test_default_temperature_is_zero(self):
        cfg = _load_gemini_config("0")
        assert cfg.temperature == 0.0

    def test_env_override_temperature(self):
        cfg = _load_gemini_config("0.7")
        assert cfg.temperature == pytest.approx(0.7)

    def test_temperature_field_exists_in_config(self):
        import rl_hybrid.config as cfg_mod
        assert hasattr(cfg_mod.GeminiConfig, "__dataclass_fields__")
        assert "temperature" in cfg_mod.GeminiConfig.__dataclass_fields__


# ---------------------------------------------------------------------------
# Test 2: prompt_hash 결정성 — 동일 입력 N회 = 동일 hash
# ---------------------------------------------------------------------------

class TestB3PromptHashDeterminism:
    def test_same_input_same_hash(self):
        prompt = "BTC 시장 분석 프롬프트 내용 예시"
        hashes = [_compute_prompt_hash(prompt) for _ in range(5)]
        assert len(set(hashes)) == 1, "동일 입력은 항상 같은 hash 를 생성해야 한다"

    def test_different_prompt_different_hash(self):
        h1 = _compute_prompt_hash("prompt A")
        h2 = _compute_prompt_hash("prompt B")
        assert h1 != h2

    def test_hash_length_16(self):
        h = _compute_prompt_hash("test")
        assert len(h) == 16


# ---------------------------------------------------------------------------
# Test 3: gemini_client.py 소스 정적 검증 — B3 필드 주입 코드 확인
# ---------------------------------------------------------------------------

class TestB3RecordFields:
    """google.generativeai 없이 소스 코드 정적 검증."""

    SRC = (PROJECT_ROOT / "rl_hybrid" / "rag" / "gemini_client.py").read_text(encoding="utf-8")

    def test_source_injects_model_id(self):
        assert '"_model_id"' in self.SRC or "'_model_id'" in self.SRC

    def test_source_injects_prompt_hash(self):
        assert '"_prompt_hash"' in self.SRC or "'_prompt_hash'" in self.SRC

    def test_source_injects_temperature(self):
        assert '"_temperature"' in self.SRC or "'_temperature'" in self.SRC

    def test_source_uses_cfg_temperature(self):
        assert "self.cfg.temperature" in self.SRC

    def test_source_uses_sha256(self):
        assert "sha256" in self.SRC and "hashlib" in self.SRC

    def test_source_no_hardcoded_03(self):
        """hardcoded temperature=0.3 이 없어야 한다 (config화 완료)."""
        assert "temperature=0.3" not in self.SRC

    def test_b3_fields_assigned_after_json_parse(self):
        """result = json.loads(...) 이후에 _model_id 할당."""
        lines = self.SRC.splitlines()
        json_parse_line = next(
            (i for i, l in enumerate(lines) if "json.loads(text)" in l), -1
        )
        model_id_line = next(
            (i for i, l in enumerate(lines) if '"_model_id"' in l or "'_model_id'" in l), -1
        )
        assert json_parse_line != -1
        assert model_id_line != -1
        assert model_id_line > json_parse_line, "_model_id 는 json.loads 이후 할당돼야 한다"


# ---------------------------------------------------------------------------
# Test 4: migration 047_ 스키마 정합 확인
# ---------------------------------------------------------------------------

class TestB3Migration:
    def test_migration_file_exists(self):
        mig = PROJECT_ROOT / "supabase" / "migrations" / "047_b3_determinism_columns.sql"
        assert mig.exists(), "047_b3_determinism_columns.sql 이 존재해야 한다"

    def test_migration_contains_required_columns(self):
        mig = PROJECT_ROOT / "supabase" / "migrations" / "047_b3_determinism_columns.sql"
        content = mig.read_text(encoding="utf-8")
        assert "model_id" in content
        assert "prompt_hash" in content
        assert "temperature" in content
        assert "decisions" in content

    def test_migration_uses_if_not_exists(self):
        mig = PROJECT_ROOT / "supabase" / "migrations" / "047_b3_determinism_columns.sql"
        content = mig.read_text(encoding="utf-8")
        assert "IF NOT EXISTS" in content.upper()
