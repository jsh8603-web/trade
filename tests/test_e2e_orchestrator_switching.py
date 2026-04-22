"""
E2E: Orchestrator 전략 전환 매트릭스 검증 (E3팀)

CLAUDE.md에 정의된 감독 에이전트(`agents/orchestrator.py`) 전환 규칙표
모든 조합을 parametrize로 커버한다. 각 테스트는 상태 파일(tempfile)로 격리,
DB 기록은 mock, 기존 test_orchestrator.py 를 건드리지 않는다.

규칙 매트릭스:
  R1  danger >= 70                               → conservative (공격→보수 직행)
  R2  danger 50~69 + moderate                    → conservative
  R3  danger 45~69 + aggressive                  → moderate
  R4  opportunity >= 60 + danger < 30            → aggressive (보수→공격 직행)
  R5  opportunity 40~59 + danger < 35 (보수/보통) → moderate / aggressive
  R6  opportunity 25~39 + danger < 30 (보수)     → moderate
  R7  횡보 (둘 다 < 25) + 중립 FGI               → moderate
  R8  FOMO: -5%+ 급락 중 공격 전환 차단
  R9  FOMO 예외: FGI<=20 + -8% 이내 → 허용
  R10 쿨다운 면제: danger>=70 또는 24h<=-7
  R11 v8.2: aggressive + opportunity<30 + 24h<-1 → moderate

작성일: 2026-04-22
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────

KST = timezone(timedelta(hours=9))


def _base_state(active: str,
                last_switch: str | None = None,
                switch_history: list | None = None,
                consecutive_losses: int = 0) -> dict:
    return {
        "active_agent": active,
        "transition_from": None,
        "transition_started": None,
        "transition_duration_min": None,
        "last_switch_time": last_switch,
        "last_trade_time": None,
        "consecutive_losses": consecutive_losses,
        "switch_history": switch_history or [],
    }


def _ms(danger_score=20, opportunity_score=20, fgi=50, rsi=50,
        price_change_24h=0.0, kimchi_pct=0.0, ls_ratio=1.0,
        consecutive_losses=0, fusion_signal="neutral", phase="neutral"):
    return {
        "danger_score": danger_score,
        "opportunity_score": opportunity_score,
        "fgi": fgi,
        "rsi": rsi,
        "price_change_24h": price_change_24h,
        "kimchi_pct": kimchi_pct,
        "ls_ratio": ls_ratio,
        "consecutive_losses": consecutive_losses,
        "fusion_signal": fusion_signal,
        "phase": phase,
    }


@pytest.fixture
def isolated_state(tmp_path, monkeypatch):
    """
    Orchestrator STATE_FILE을 tmp_path로 격리하고, DB 기록 메서드를 mock 한다.
    반환값은 (STATE_FILE_PATH, writer) 이며 writer(state_dict) 로 초기 상태 작성.
    """
    import agents.orchestrator as orch_mod

    state_file = tmp_path / "agent_state.json"
    monkeypatch.setattr(orch_mod, "STATE_FILE", state_file)
    monkeypatch.setattr(orch_mod, "AUTO_EMERGENCY_FILE",
                        tmp_path / "auto_emergency.json")

    def _write(state: dict) -> None:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(state, ensure_ascii=False),
                              encoding="utf-8")

    return state_file, _write


def _new_orchestrator(isolated_state, active: str,
                      last_switch: str | None = None,
                      switch_history: list | None = None,
                      consecutive_losses: int = 0):
    _, writer = isolated_state
    writer(_base_state(active, last_switch, switch_history, consecutive_losses))
    from agents.orchestrator import Orchestrator
    with patch("agents.orchestrator.Orchestrator._record_switch_to_db"):
        orch = Orchestrator()
    # 학습/성과 비활성화 (매트릭스 규칙만 검증)
    orch._learning_data = None
    orch._performance = {}
    # feedback bias 없음
    orch.state.pop("feedback_bias", None)
    return orch


# ────────────────────────────────────────────────────────────
# Matrix 1: danger / opportunity 기반 전환 (R1~R7, R11)
# 10 조건 x 3 전략 = 30 조합, 규칙에 따라 예상 결과 지정
# ────────────────────────────────────────────────────────────

# (test_id, current, ms_kwargs, (danger, opportunity), expected_to)
_MATRIX: list[tuple] = [
    # ── R1: danger >= 70 → conservative (공격→보수 직행) ──
    ("R1_agg_danger75", "aggressive",
     dict(danger_score=75, fgi=30, price_change_24h=-6, consecutive_losses=3,
          phase="fear"), (75, 5), "conservative"),
    ("R1_mod_danger80", "moderate",
     dict(danger_score=80, fgi=25, price_change_24h=-5, consecutive_losses=4,
          phase="fear"), (80, 5), "conservative"),
    ("R1_con_danger75", "conservative",
     dict(danger_score=75, fgi=25, consecutive_losses=3, phase="fear"),
     (75, 5), None),  # 이미 보수적 → 전환 없음

    # ── R2: danger 50~69 + moderate → conservative ──
    ("R2_mod_danger55", "moderate",
     dict(danger_score=55, fgi=35, phase="fear"), (55, 10), "conservative"),
    ("R2_mod_danger50_boundary", "moderate",
     dict(danger_score=50, fgi=35, phase="fear"), (50, 10), "conservative"),
    ("R2_mod_danger49_no_switch", "moderate",
     dict(danger_score=49, phase="neutral"), (49, 10), None),

    # ── R3: danger 45~69 + aggressive → moderate ──
    ("R3_agg_danger50", "aggressive",
     dict(danger_score=50, kimchi_pct=4, ls_ratio=1.3, phase="neutral"),
     (50, 10), "moderate"),
    ("R3_agg_danger45_boundary", "aggressive",
     dict(danger_score=45, phase="neutral"), (45, 10), "moderate"),
    ("R3_agg_danger44_no_switch", "aggressive",
     dict(danger_score=44, phase="neutral"), (44, 10), None),
    ("R3_con_danger50_no_switch", "conservative",
     dict(danger_score=50, phase="neutral"), (50, 10), None),

    # ── R4: opportunity >= 60 + danger < 30 → aggressive (보수→공격 직행) ──
    ("R4_con_opp65_direct", "conservative",
     dict(opportunity_score=65, fgi=15, rsi=25, price_change_24h=2,
          fusion_signal="strong_buy", phase="extreme_fear"),
     (10, 65), "aggressive"),
    ("R4_mod_opp60_boundary", "moderate",
     dict(opportunity_score=60, fgi=15, phase="extreme_fear"),
     (10, 60), "aggressive"),
    ("R4_opp60_danger30_blocks", "conservative",
     dict(opportunity_score=65, fgi=40, phase="neutral"),
     (30, 65), None),
    ("R4_agg_opp65_no_switch", "aggressive",
     dict(opportunity_score=65, fgi=15, phase="extreme_fear"),
     (10, 65), None),  # 이미 공격적

    # ── R5: opportunity 40~59 + danger < 35 ──
    ("R5_con_opp45_to_moderate", "conservative",
     dict(opportunity_score=45, fgi=30, rsi=35, phase="fear"),
     (10, 45), "moderate"),
    ("R5_mod_opp45_to_aggressive", "moderate",
     dict(opportunity_score=45, fgi=30, rsi=35,
          fusion_signal="buy", phase="fear"),
     (10, 45), "aggressive"),
    ("R5_opp40_boundary", "moderate",
     dict(opportunity_score=40, fgi=30, phase="fear"),
     (10, 40), "aggressive"),
    ("R5_danger35_blocks", "conservative",
     dict(opportunity_score=45, phase="neutral"), (35, 45), None),
    ("R5_opp59_edge", "conservative",
     dict(opportunity_score=59, fgi=30, phase="fear"),
     (10, 59), "moderate"),

    # ── R6: opportunity 25~39 + danger < 30 + 보수적 → moderate ──
    ("R6_con_opp30_to_moderate", "conservative",
     dict(opportunity_score=30, fgi=40, rsi=40, phase="neutral"),
     (10, 30), "moderate"),
    ("R6_con_opp25_boundary", "conservative",
     dict(opportunity_score=25, fgi=40, phase="neutral"),
     (10, 25), "moderate"),
    ("R6_opp30_danger30_blocks", "conservative",
     dict(opportunity_score=30, phase="neutral"), (30, 30), None),
    ("R6_mod_opp30_no_switch", "moderate",
     dict(opportunity_score=30, fgi=40, phase="neutral"),
     (10, 30), None),  # moderate 는 이 규칙 대상 아님

    # ── R7: 횡보 (둘 다 < 25) + 중립 FGI ≥ 36 ──
    ("R7_agg_sideways_to_moderate", "aggressive",
     dict(fgi=50, rsi=50, phase="neutral"), (10, 10), "moderate"),
    ("R7_con_sideways_to_moderate", "conservative",
     dict(fgi=50, rsi=50, price_change_24h=0.5,
          consecutive_losses=0, phase="neutral"),
     (10, 10), "moderate"),
    ("R7_mod_sideways_stays", "moderate",
     dict(fgi=50, rsi=50, phase="neutral"), (15, 15), None),
    ("R7_con_sideways_with_loss_stays", "conservative",
     dict(fgi=50, rsi=50, consecutive_losses=1, phase="neutral"),
     (10, 10), None),

    # ── R11 v8.2: aggressive + opportunity<30 + 24h<-1 → moderate ──
    ("R11_agg_opp25_down2pct_downgrade", "aggressive",
     dict(opportunity_score=25, price_change_24h=-2.0, fgi=40,
          phase="neutral"),
     (20, 25), "moderate"),
    ("R11_agg_opp29_down1_5pct_downgrade", "aggressive",
     dict(opportunity_score=29, price_change_24h=-1.5, phase="neutral"),
     (20, 29), "moderate"),
    ("R11_agg_opp30_not_triggered", "aggressive",
     dict(opportunity_score=30, price_change_24h=-2.0, fgi=40,
          phase="neutral"),
     (20, 30), None),  # opp>=30 → 규칙 비발동, 다른 규칙도 미해당
    ("R11_mod_same_conditions_no_switch", "moderate",
     dict(opportunity_score=20, price_change_24h=-2.0, phase="neutral"),
     (20, 20), None),  # moderate 는 규칙 대상 아님
]


@pytest.mark.parametrize("tid,current,ms_kwargs,scores,expected",
                         _MATRIX,
                         ids=[row[0] for row in _MATRIX])
def test_matrix_decide_target(isolated_state, tid, current, ms_kwargs,
                              scores, expected):
    """전환 매트릭스 전체: _decide_target이 예상 대상으로 수렴하는지."""
    orch = _new_orchestrator(isolated_state, active=current)
    ms = _ms(**ms_kwargs)
    danger, opportunity = scores
    target = orch._decide_target(current, ms, danger, opportunity)
    assert target == expected, (
        f"[{tid}] current={current} scores=({danger},{opportunity}) "
        f"expected={expected} got={target}"
    )


# ────────────────────────────────────────────────────────────
# Matrix 2: FOMO 차단 / 예외 (R8 / R9)
# ────────────────────────────────────────────────────────────

_FOMO: list[tuple] = [
    # (test_id, current, price_change_24h, fgi, opportunity, expected)
    ("R8_fomo_block_minus6_fgi30", "conservative", -6.0, 30, 65, None),
    ("R8_fomo_block_minus5_01", "conservative", -5.01, 30, 65, None),
    ("R8_fomo_above_minus5", "conservative", -4.9, 15, 65, "aggressive"),
    ("R9_fomo_exc_minus6_fgi15", "conservative", -6.0, 15, 65, "aggressive"),
    ("R9_fomo_exc_minus7_9_fgi20", "conservative", -7.9, 20, 65, "aggressive"),
    ("R9_fomo_no_exc_minus8_exact", "conservative", -8.0, 20, 65, None),
    ("R9_fomo_no_exc_deep_crash", "conservative", -9.0, 15, 65, None),
]


@pytest.mark.parametrize(
    "tid,current,pc24h,fgi,opp,expected", _FOMO,
    ids=[r[0] for r in _FOMO],
)
def test_fomo_rules(isolated_state, tid, current, pc24h, fgi, opp, expected):
    orch = _new_orchestrator(isolated_state, active=current)
    phase = ("extreme_fear" if fgi <= 20
             else "fear" if fgi <= 35 else "neutral")
    ms = _ms(opportunity_score=opp, fgi=fgi, rsi=25,
             price_change_24h=pc24h, fusion_signal="strong_buy", phase=phase)
    target = orch._decide_target(current, ms, 10, opp)
    assert target == expected, (
        f"[{tid}] pc24h={pc24h} fgi={fgi} opp={opp} "
        f"expected={expected} got={target}"
    )


# ────────────────────────────────────────────────────────────
# Matrix 3: 쿨다운 & 긴급 면제 (R10)
# ────────────────────────────────────────────────────────────

def _recent(minutes_ago: int) -> str:
    return (datetime.now(KST) - timedelta(minutes=minutes_ago)).isoformat()


_COOLDOWN: list[tuple] = [
    # (tid, danger, pc24h, minutes_ago, switches_today, expected_switch?)
    # 기본 2h 쿨다운
    ("CD_2h_blocks_30min",   40, -2.0, 30,  0, False),
    ("CD_2h_expires_3h",     40, -2.0, 180, 0, True),   # 3h 경과 → 해제
    # 당일 3회+ → 4h 쿨다운
    ("CD_4h_blocks_3h_3sw",  40, -2.0, 180, 3, False),
    ("CD_4h_expires_5h",     40, -2.0, 300, 3, True),
    # 긴급: danger>=70 면제
    ("CD_emergency_danger75", 75, -4.0, 30, 0, True),
    # 긴급: price_change < -7 면제
    ("CD_emergency_crash",    40, -8.0, 30, 0, True),
    # 경계: -7 정확히는 면제 아님 (코드상 < -7)
    ("CD_edge_minus7_not_emergency", 40, -7.0, 30, 0, False),
]


@pytest.mark.parametrize(
    "tid,danger,pc24h,minutes_ago,switches_today,expected_switch",
    _COOLDOWN, ids=[r[0] for r in _COOLDOWN],
)
def test_cooldown_and_emergency_bypass(isolated_state, tid, danger, pc24h,
                                       minutes_ago, switches_today,
                                       expected_switch):
    last = _recent(minutes_ago)
    history = []
    if switches_today > 0:
        # 현재 기준 오늘 날짜 기준으로 n건 기록
        now = datetime.now(KST)
        for i in range(switches_today):
            t = (now - timedelta(hours=(minutes_ago / 60.0) + i + 1))
            history.append({"timestamp": t.isoformat()})
        history.append({"timestamp": last})

    # 긴급 상황은 aggressive 에서 conservative 로 내려가는 시나리오,
    # 비긴급은 moderate 에서 danger 50~69 로 테스트
    if danger >= 70 or pc24h < -7:
        current = "aggressive"
        ms = _ms(danger_score=danger, opportunity_score=5, fgi=20,
                 price_change_24h=pc24h, consecutive_losses=3,
                 phase="extreme_fear")
    else:
        current = "moderate"
        ms = _ms(danger_score=max(danger, 55), opportunity_score=10,
                 fgi=35, price_change_24h=pc24h, phase="fear")

    orch = _new_orchestrator(
        isolated_state, active=current,
        last_switch=last, switch_history=history,
    )
    result = orch._evaluate_switch(ms)
    if expected_switch:
        assert result is not None, (
            f"[{tid}] 전환 기대했으나 쿨다운에 막힘")
    else:
        assert result is None, (
            f"[{tid}] 쿨다운이 차단해야 하지만 전환 발생: {result}")


# ────────────────────────────────────────────────────────────
# Matrix 4: _evaluate_switch 통합 (from→to 전체 파이프라인)
# 상태 파일 격리 + DB mock + 결과 키 검증
# ────────────────────────────────────────────────────────────

_EVAL_CASES: list[tuple] = [
    # (tid, current, ms_kwargs, expected_to_or_None)
    ("EVAL_R1_agg_to_con",
     "aggressive",
     dict(danger_score=75, opportunity_score=5, fgi=20,
          price_change_24h=-8, consecutive_losses=3,
          phase="extreme_fear"),
     "conservative"),
    ("EVAL_R4_con_to_agg",
     "conservative",
     dict(danger_score=10, opportunity_score=65, fgi=15, rsi=25,
          price_change_24h=2, fusion_signal="strong_buy",
          phase="extreme_fear"),
     "aggressive"),
    ("EVAL_R7_agg_sideways_to_mod",
     "aggressive",
     dict(danger_score=10, opportunity_score=10, fgi=50, rsi=50,
          phase="neutral"),
     "moderate"),
    ("EVAL_R11_v82_agg_to_mod",
     "aggressive",
     dict(danger_score=20, opportunity_score=25,
          price_change_24h=-2.0, fgi=40, phase="neutral"),
     "moderate"),
    ("EVAL_R3_agg_to_mod_danger50",
     "aggressive",
     dict(danger_score=55, opportunity_score=5, kimchi_pct=4,
          ls_ratio=1.3, phase="neutral"),
     "moderate"),
    ("EVAL_no_switch_optimal",
     "moderate",
     dict(danger_score=30, opportunity_score=30, phase="neutral"),
     None),
]


@pytest.mark.parametrize(
    "tid,current,ms_kwargs,expected_to", _EVAL_CASES,
    ids=[r[0] for r in _EVAL_CASES],
)
def test_evaluate_switch_integration(isolated_state, tid, current,
                                     ms_kwargs, expected_to):
    """_evaluate_switch 전체: 상태 로드 → 쿨다운 → 전환 판단 → 결과 dict."""
    orch = _new_orchestrator(isolated_state, active=current)
    ms = _ms(**ms_kwargs)
    result = orch._evaluate_switch(ms)
    if expected_to is None:
        assert result is None, f"[{tid}] 전환 없음 기대, got={result}"
    else:
        assert result is not None, f"[{tid}] 전환 기대, got None"
        assert result["from"] == current
        assert result["to"] == expected_to
        # 결과 dict 구조 검증
        for key in ("reason", "danger_score", "opportunity_score",
                    "market_phase", "timestamp"):
            assert key in result, f"[{tid}] 결과에 {key} 누락"


# ────────────────────────────────────────────────────────────
# 상태 파일 격리 확인: 전환 후 디스크에 반영되는지
# ────────────────────────────────────────────────────────────

def test_state_file_is_isolated(isolated_state):
    """tempfile STATE_FILE 사용 시 real data/agent_state.json 건드리지 않음."""
    state_file, _ = isolated_state
    orch = _new_orchestrator(isolated_state, active="moderate")
    assert orch._active_agent_name == "moderate"
    # 실제 프로젝트 data/ 내 agent_state.json 이 아님을 확인
    real_state = Path(__file__).resolve().parent.parent / "data" / "agent_state.json"
    assert Path(state_file).resolve() != real_state.resolve()


def test_cooldown_bypass_danger_70_end_to_end(isolated_state):
    """E2E: 쿨다운 중이라도 danger≥70 이면 즉시 보수적으로 전환."""
    recent = _recent(15)  # 15분 전 전환
    orch = _new_orchestrator(
        isolated_state, active="aggressive", last_switch=recent,
    )
    ms = _ms(danger_score=80, opportunity_score=5, fgi=15,
             price_change_24h=-5, consecutive_losses=4,
             phase="extreme_fear")
    result = orch._evaluate_switch(ms)
    assert result is not None
    assert result["to"] == "conservative"
    assert "긴급" in result["reason"] or "위험" in result["reason"]
