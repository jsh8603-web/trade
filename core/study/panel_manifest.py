"""core/study/panel_manifest.py — study_session indicators(블록2) → 지표 패널 manifest (골격 G2).

`build_indicator_matrix`(본체 = core/data/weight_panel.py)를 *감싸* study yaml 의 indicators 를
PIT 패널로 조립한다. **본체는 한 줄도 안 고친다** — manifest 가 인자(series_ids/periods/as_of)만
공급하고, 반사성 게이트·PIT realtime 조회는 전부 본체가 수행한다.

설계 의도(STUDY-KIT §4 ① 학습 단계):
- `panel_instance_id` 로 여러 자산군 패널을 동시 관리(us 패널을 eq_us_cyclical/eq_us_defensive 가
  공유하는 식). registry 가 인스턴스를 보관 → study_register(G6)가 학습 배치에 라우팅.
- series 순서 = manifest 고정(replay 불변 — weight_card.series_ids 와 같은 순서로 정렬돼야 비교가능).
- transform/vintage_policy/lag/is_core 는 meta() 로 보관 → 학습 단계(glasso)가 참조(여기선 조립만).
- 반사성 series 는 본체 `assert_no_reflexive_series` 가 거부 — manifest 는 통과 보장만(오탐 방지 위해
  미리 거르지 않고 본체에 위임).
- provider 부재/지표 0개 graceful(빈 패널 반환, 예외 없음).

방마다 weight_panel.py 본체를 안 고치게 = 플러그인. 방은 yaml 만 주고, 패널 조립은 이 어댑터가.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

from core.study.study_loader import Indicator, StudySession


# ---------------------------------------------------------------------------
# PanelManifest — study indicators 의 패널 입력 명세 (series 순서 고정)
# ---------------------------------------------------------------------------

@dataclass
class PanelManifest:
    """한 패널 인스턴스의 series 명세. build_indicator_matrix 입력으로 변환된다.

    panel_instance_id: 패널 식별자(예: "panel.eq_us"). 여러 study 가 공유 가능.
    indicators: study_loader.Indicator 순서 보존 리스트(= series 순서 = replay 불변).
    """
    panel_instance_id: str
    study_id: str
    indicators: list = field(default_factory=list)   # list[Indicator]
    as_of: str = ""

    @property
    def series_ids(self) -> list:
        """본체 build_indicator_matrix 에 넘길 series 라벨(순서 고정)."""
        return [ind.id for ind in self.indicators if ind.id]

    def meta(self) -> dict:
        """series_id → 메타(family/transform/vintage_policy/lag/is_core/source). 학습 단계 참조용."""
        return {
            ind.id: {
                "family": ind.family,
                "transform": ind.transform,
                "vintage_policy": ind.vintage_policy,
                "lag": ind.lag,
                "is_core": ind.is_core,
                "in_our_system": ind.in_our_system,
                "source_or_collector": ind.source_or_collector,
            }
            for ind in self.indicators if ind.id
        }

    def lookahead_risk_series(self) -> list:
        """vintage_policy=final_revised 인 series(학습 입력 시 lookahead 위험). 경고용."""
        return [ind.id for ind in self.indicators
                if ind.id and ind.vintage_policy == "final_revised"]


def from_study_session(s: StudySession, *, panel_instance_id: Optional[str] = None) -> PanelManifest:
    """StudySession(블록2 indicators) → PanelManifest.

    panel_instance_id 미지정 시 f"panel.{study_id}". eq_us_cyclical/eq_us_defensive 처럼 같은
    물리 패널을 공유하려면 둘 다 panel_instance_id="panel.eq_us" 로 명시(study_register 가 결정).
    """
    pid = panel_instance_id or f"panel.{s.study_id or 'unknown'}"
    return PanelManifest(
        panel_instance_id=pid,
        study_id=s.study_id,
        indicators=list(s.indicators),
        as_of=s.as_of,
    )


def merge_manifests(manifests: Sequence[PanelManifest], *, panel_instance_id: str) -> PanelManifest:
    """여러 manifest 를 한 패널로 합친다(series 합집합, 첫 등장 순서 보존, 중복 id 제거).

    cross-sleeve 공분산(G5)·공유 패널(us cyclical+defensive)에서 쓴다. 중복 series 는
    먼저 등장한 spec 을 유지(뒤 manifest 의 동일 id 무시).
    """
    seen: set = set()
    merged: list = []
    study_ids: list = []
    as_of = ""
    for m in manifests:
        if m.study_id and m.study_id not in study_ids:
            study_ids.append(m.study_id)
        as_of = as_of or m.as_of
        for ind in m.indicators:
            if ind.id and ind.id not in seen:
                seen.add(ind.id)
                merged.append(ind)
    return PanelManifest(
        panel_instance_id=panel_instance_id,
        study_id="+".join(study_ids),
        indicators=merged,
        as_of=as_of,
    )


# ---------------------------------------------------------------------------
# 패널 조립 — build_indicator_matrix(본체) wrap. 본체 미변경.
# ---------------------------------------------------------------------------

def build_panel(manifest: PanelManifest, provider, periods: Sequence[str],
                *, as_of=None, warn=None):
    """manifest 의 series_ids 로 본체 build_indicator_matrix 호출 → IndicatorPanel.

    - 본체가 반사성 게이트(assert_no_reflexive_series)와 PIT realtime 조회를 수행.
    - series 0개 → 빈 패널 graceful(예외 없음).
    - final_revised series 있으면 warn(콜백) 으로 알림(lookahead 위험). warn=None 이면 무시.
    - as_of 미지정 시 manifest.as_of 사용. 둘 다 없으면 본체 기본(호출자 책임).
    """
    from core.data.weight_panel import build_indicator_matrix, IndicatorPanel
    import numpy as np

    sids = manifest.series_ids
    a = as_of if as_of is not None else (manifest.as_of or None)

    if not sids or not periods:
        return IndicatorPanel(
            matrix=np.empty((0, len(sids)), dtype=float),
            periods=list(periods), series_ids=list(sids), as_of=_coerce_date(a),
        )

    if warn is not None:
        lookahead = manifest.lookahead_risk_series()
        if lookahead:
            warn(f"panel {manifest.panel_instance_id}: final_revised series {lookahead} "
                 f"= 학습 입력 시 lookahead 위험(point_in_time 권장)")

    # 본체 호출(인자만 manifest 공급). 반사성 series 면 본체가 ValueError.
    return build_indicator_matrix(provider, sids, periods, a)


def _coerce_date(a):
    """빈 패널 fallback 용 as_of 정규화(본체 _d 와 무관, graceful)."""
    from datetime import date, datetime
    if a is None:
        return None
    if isinstance(a, date) and not isinstance(a, datetime):
        return a
    if isinstance(a, datetime):
        return a.date()
    try:
        return datetime.fromisoformat(str(a)).date()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# PanelManifestRegistry — panel_instance_id → manifest 보관 (study_register 가 사용)
# ---------------------------------------------------------------------------

class PanelManifestRegistry:
    """패널 인스턴스 레지스트리. 공유 패널(us cyclical+defensive)을 한 번만 학습하게."""

    def __init__(self):
        self._panels: dict = {}

    def register(self, manifest: PanelManifest) -> PanelManifest:
        """동일 panel_instance_id 가 이미 있으면 series 합집합으로 merge(공유 패널 누적)."""
        pid = manifest.panel_instance_id
        if pid in self._panels:
            self._panels[pid] = merge_manifests([self._panels[pid], manifest],
                                                panel_instance_id=pid)
        else:
            self._panels[pid] = manifest
        return self._panels[pid]

    def get(self, panel_instance_id: str) -> Optional[PanelManifest]:
        return self._panels.get(panel_instance_id)

    def instances(self) -> list:
        return list(self._panels.keys())


# ===========================================================================
# self-test (실동작 — 본체 build_indicator_matrix 를 진짜 호출)
# ===========================================================================

if __name__ == "__main__":
    import numpy as np
    from core.study.study_loader import load_study_session

    # Fake PIT provider — realtime(series, period, as_of) → 결정론 값
    class FakeProvider:
        def realtime(self, series_id, period, as_of):
            base = sum(ord(c) for c in series_id) % 7
            idx = int(str(period)[-2:]) if str(period)[-2:].isdigit() else 0
            return float(base + idx)

    # 1) study dict → manifest → build_panel(본체 호출)
    eq = {
        "study_id": "eq_us_cyclical", "asset_scope": ["equity.us"], "as_of": "2026-05-30",
        "indicators": [
            {"id": "fwd_ep", "family": "valuation", "is_core": True, "in_our_system": True,
             "transform": "own_history_z", "vintage_policy": "point_in_time"},
            {"id": "roe", "family": "quality", "is_core": True, "in_our_system": True},
            {"id": "mom_12_1", "family": "momentum", "is_core": True, "in_our_system": True},
        ],
    }
    s = load_study_session(eq)
    m = from_study_session(s)
    assert m.panel_instance_id == "panel.eq_us_cyclical"
    assert m.series_ids == ["fwd_ep", "roe", "mom_12_1"]
    assert m.meta()["fwd_ep"]["family"] == "valuation"
    print(f"1) manifest OK: id={m.panel_instance_id} series={m.series_ids}")

    periods = ["2026-01", "2026-02", "2026-03"]
    panel = build_panel(m, FakeProvider(), periods)
    assert panel.shape == (3, 3), panel.shape
    assert panel.series_ids == ["fwd_ep", "roe", "mom_12_1"]
    assert not np.isnan(panel.matrix).any()
    print(f"2) build_panel(본체 호출) OK: shape={panel.shape}")

    # 3) 공유 패널 — 명시 panel_instance_id 로 cyclical/defensive 묶기 + merge
    defn = {"study_id": "eq_us_defensive", "asset_scope": ["equity.us"], "as_of": "2026-05-30",
            "indicators": [
                {"id": "roe", "family": "quality", "is_core": True, "in_our_system": True},  # 중복
                {"id": "realized_vol", "family": "risk", "is_core": True, "in_our_system": True},
            ]}
    md = from_study_session(load_study_session(defn), panel_instance_id="panel.eq_us")
    mc = from_study_session(s, panel_instance_id="panel.eq_us")
    merged = merge_manifests([mc, md], panel_instance_id="panel.eq_us")
    assert merged.series_ids == ["fwd_ep", "roe", "mom_12_1", "realized_vol"], merged.series_ids
    print(f"3) merge(공유 패널, 중복 roe 제거) OK: {merged.series_ids}")

    # 4) registry — 동일 id 재등록 시 누적 merge
    reg = PanelManifestRegistry()
    reg.register(mc)
    reg.register(md)
    assert reg.get("panel.eq_us").series_ids == merged.series_ids
    assert reg.instances() == ["panel.eq_us"]
    print(f"4) registry 누적 merge OK: instances={reg.instances()}")

    # 5) 빈 패널 graceful (series 0개)
    empty = PanelManifest(panel_instance_id="panel.x", study_id="x", indicators=[])
    p0 = build_panel(empty, FakeProvider(), periods)
    assert p0.shape == (0, 0)
    print(f"5) 빈 패널 graceful OK: shape={p0.shape}")

    # 6) 반사성 series → 본체가 ValueError (manifest 가 막지 않고 본체에 위임)
    bad = {"study_id": "b", "asset_scope": ["macro"], "as_of": "t",
           "indicators": [{"id": "my_position_pnl", "family": "risk", "in_our_system": True}]}
    mb = from_study_session(load_study_session(bad))
    try:
        build_panel(mb, FakeProvider(), periods)
        raise AssertionError("반사성 series 가 통과됨 — 본체 게이트 미작동")
    except ValueError as exc:
        assert "반사성" in str(exc)
        print(f"6) 반사성 게이트(본체 위임) OK: 차단됨")

    # 7) lookahead 경고 콜백
    la = {"study_id": "l", "asset_scope": ["macro"], "as_of": "2026-05-30",
          "indicators": [{"id": "cpi", "family": "macro_driver", "in_our_system": True,
                          "vintage_policy": "final_revised"}]}
    ml = from_study_session(load_study_session(la))
    warns = []
    build_panel(ml, FakeProvider(), periods, warn=warns.append)
    assert any("lookahead" in w for w in warns), warns
    print(f"7) lookahead 경고 콜백 OK")

    print("\npanel_manifest self-test PASS "
          "(manifest 생성 + 본체 build_indicator_matrix wrap + merge/registry + graceful + 반사성 위임)")
