"""tests/structure/test_contracts.py — T2 인터페이스 3계약 + R8 + T2-7 게이트 잠금.

T3(btn-Codlearn)가 의존하는 표면을 회귀로부터 보호한다.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from core.structure import panel_schema as ps
from core.structure.panel_schema import (
    make_semiconductor_fixture, validate_panel, driver_columns, definition_for,
)
from core.structure.structure_model import (
    StructureModel, StructureModelConfig, AsOfResolver, IdentityAsOfResolver,
)
from core.structure import archetype as arch


# --- 계약 #1: 패널 schema + R8 ----------------------------------------------

def test_fixture_passes_schema_validation():
    df = make_semiconductor_fixture()
    assert validate_panel(df) == []
    assert len(driver_columns(df)) >= 1

def test_r8_survivorship_included():
    """R8②: 적합 표본에 상폐 기업이 포함돼야 (생존편향 방지)."""
    df = make_semiconductor_fixture()
    assert df[ps.COL_DELIST_FLAG].any(), "상폐 row 부재 = 생존편향"
    assert df.loc[df[ps.COL_DELIST_FLAG] & df[ps.COL_DELIST_RET].notna(), ps.COL_DELIST_RET].lt(0).all()

def test_r8_multiple_definition_versioned():
    """R8①: multiple 정의가 버전으로 고정되고 drift 가 추적돼야."""
    df = make_semiconductor_fixture()
    assert df[ps.COL_MULT_DEF_VER].notna().all()
    assert df[ps.COL_MULT_DEF_VER].nunique() >= 2, "정의 drift(GAAP→adj) 미반영"
    assert definition_for(pd.Timestamp("2015-06-30").date()).version == "ev_ebitda_gaap_v1"
    assert definition_for(pd.Timestamp("2021-06-30").date()).version == "ev_ebitda_adj_v2"


# --- 계약 #2: cheapness_z ---------------------------------------------------

def test_cheapness_z_signature_and_sign():
    """음수 클수록 저평가 + float 반환 + regime별 σ."""
    df = make_semiconductor_fixture()
    m = StructureModel(StructureModelConfig(purge_days=90))
    fit = m.fit(df, pd.Timestamp("2022-01-01"))
    assert fit.n_train > 0 and fit.sigma_global > 0
    assert len(fit.sigma_by_regime) >= 2  # regime별 σ 분리
    z = m.cheapness_z("SEMI001", "semiconductor", pd.Timestamp("2021-09-30"), pd.Timestamp("2022-01-01"))
    assert isinstance(z, float)
    assert -8.001 <= z <= 8.001  # clamp 범위

def test_cheapness_z_purged_oos():
    """purge: cutoff 이후 데이터는 적합에 안 들어감."""
    df = make_semiconductor_fixture()
    m = StructureModel(StructureModelConfig(purge_days=90))
    as_of = pd.Timestamp("2020-01-01")
    fit = m.fit(df, as_of)
    cutoff = as_of - pd.Timedelta(days=90)
    train = df[df[ps.COL_KNOWABLE_FROM] <= cutoff]
    assert fit.n_train == len(train)

def test_real_undervalued_cheaper_than_trap():
    """★ 핵심: real(잔차≪0)이 structural_trap(잔차≈0)보다 평균적으로 더 싼 z."""
    df = make_semiconductor_fixture()
    as_of = pd.Timestamp("2023-06-30")
    m = StructureModel(StructureModelConfig(purge_days=90))
    m.fit(df, as_of)
    eval_q = df[(df[ps.COL_DATE] == df[df[ps.COL_DATE] <= as_of][ps.COL_DATE].max())]
    z = m.cheapness_z_rows(eval_q)
    real_z = z[eval_q["label_type"].values == "real"]
    trap_z = z[eval_q["label_type"].values == "structural_trap"]
    if len(real_z) and len(trap_z):
        assert real_z.mean() < trap_z.mean(), (real_z.mean(), trap_z.mean())


# --- 계약 0: as_of resolver -------------------------------------------------

def test_as_of_resolver_protocol():
    assert isinstance(IdentityAsOfResolver(), AsOfResolver)
    class CustomResolver:
        def resolve(self, as_of):
            return pd.Timestamp(as_of) + pd.Timedelta(days=1)
    m = StructureModel(as_of_resolver=CustomResolver())
    assert isinstance(m.resolver, AsOfResolver)


# --- 계약 #3: ArchetypeCard discriminated union -----------------------------

def test_archetype_discriminated_union_all_5():
    cards = arch.load_cards_from_config()
    assert set(cards) == set(arch.ARCHETYPE_NAMES)
    for name, card in cards.items():
        assert card.archetype == name
        assert card.primary_metric
        rt = arch.parse_card(card.model_dump())
        assert rt.archetype == name

def test_compounder_expensive_trap():
    """compounder = 함정이 비싼 쪽 (claude R4)."""
    cards = arch.load_cards_from_config()
    assert cards["compounder"].cheapness_sign == "expensive_trap"
    assert cards["cyclical"].cheapness_sign == "low_multiple"

def test_sector_archetype_mapping():
    assert arch.archetype_for_sector("semiconductor") == "cyclical"
    assert arch.archetype_for_sector("banks") == "spread_driven"


# --- T2-3 드라이버 식별 -----------------------------------------------------

def test_driver_diagnostics_grouped_and_regime():
    df = make_semiconductor_fixture()
    m = StructureModel(StructureModelConfig(purge_days=90))
    m.fit(df, pd.Timestamp("2022-06-30"))
    diag = m.driver_diagnostics()
    assert set(diag["grouped_importance"]) == set(driver_columns(df))
    assert diag["ranked"][0] in diag["grouped_importance"]
    # regime-stratified = regime별 부분 상관 (국면의존)
    assert any(len(v) >= 2 for v in diag["regime_stratified_corr"].values())

def test_driver_2x2_quadrants():
    df = make_semiconductor_fixture()
    m = StructureModel(StructureModelConfig(purge_days=90))
    m.fit(df, pd.Timestamp("2022-06-30"))
    q = m.driver_2x2({"book_to_bill", "capex_to_rev"})
    assert set(q) == {"confirmed", "folklore", "unmodeled", "noise"}
    # narrative∩stat 인 드라이버는 confirmed 에
    assert any("book_to_bill" in d for d in q["confirmed"])


# --- ★ T2-7 STOP gate -------------------------------------------------------

def test_t2_7_residual_beats_raw_percentile():
    """프로젝트 전체 STOP gate: 잔차가 raw 분위를 PR-AUC 우위해야 reframe 정당화."""
    from core.structure.validate_semiconductor import run_validation
    rep = run_validation()
    assert rep.verdict in ("GO", "GO-WEAK"), rep.rationale
    assert rep.residual.pr_auc > rep.raw_percentile.pr_auc
    assert rep.lift_pr_auc > 0
