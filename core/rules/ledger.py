"""core/rules/ledger.py — 2-ledger (S4, E축: 기존 학습데이터 처리).

claude R8 / findings E축: rule 이 바뀌어도 과거 데이터를 버리지 않는다. 둘로 나눈다:
- **decision_ledger** (immutable): "이 숫자가 실제 행동(주문)을 일으켰나" = freeze.
  과거 의사결정은 그 시점 rule_version 으로 박제(PIT). 절대 재계산·mutate 안 함.
- **analysis_ledger** (recompute): counterfactual. "지금 rule 로 그때를 다시 보면?" 을
  version_basis 태그와 함께 소급 계산. 의사결정엔 영향 없음(분석 자산).

version_basis ∈ {frozen, counterfactual} — 어떤 숫자가 진짜 행동을 일으켰고(frozen)
어떤 게 사후 재계산(counterfactual)인지 항상 구분 가능해야 한다 (두 ledger 혼동 = 사고).

rule_performance: (version × regime × sector × regime_model_version) append-only.
  ★ regime_model_version 필수 — regime 정의 자체가 바뀌면 "그때 통한 rule"의 의미가 달라짐.
  dormant(휴면) rule 이 특정 regime 재도래 시 부활 후보인지 = 이 매트릭스로 판정.

불변식: ②rollback=append만(mutate 0). decision_ledger 는 freeze 라 mutate 자체가 버그.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime
from typing import Literal, Optional

VersionBasis = Literal["frozen", "counterfactual"]


@dataclass(frozen=True)
class DecisionRecord:
    """실제 행동을 일으킨 결정 — immutable freeze (PIT)."""
    decision_id: str
    ts: str
    firm: str
    sector: str
    as_of: str
    rule_version: str
    regime_id: int
    regime_model_version: str
    verdict: str               # cheap/veto/abstain/neutral
    cheapness_z: float
    action: str                # buy/sell/hold (실제 실행된 것)


class DecisionLedger:
    """append-only, frozen. 같은 decision_id 재기록 = 거부 (freeze 강제)."""

    def __init__(self):
        self._rows: dict[str, DecisionRecord] = {}

    def record(self, rec: DecisionRecord) -> None:
        if rec.decision_id in self._rows:
            raise ValueError(f"decision freeze 위반: {rec.decision_id} 재기록 금지(immutable)")
        self._rows[rec.decision_id] = rec

    def get(self, decision_id: str) -> Optional[DecisionRecord]:
        return self._rows.get(decision_id)

    def all(self) -> list[DecisionRecord]:
        return list(self._rows.values())


@dataclass
class AnalysisRecord:
    """counterfactual 재계산 — version_basis 로 frozen 과 구분."""
    decision_id: str
    version_basis: VersionBasis
    rule_version_used: str
    recomputed_z: float
    recomputed_verdict: str
    computed_at: str
    note: str = ""


class AnalysisLedger:
    """소급 재계산 결과. frozen 원본은 절대 안 건드림."""

    def __init__(self):
        self._rows: list[AnalysisRecord] = []

    def snapshot_frozen(self, dec: DecisionRecord) -> AnalysisRecord:
        """frozen 결정을 analysis 에 그대로 복사(version_basis=frozen, 기준선)."""
        ar = AnalysisRecord(dec.decision_id, "frozen", dec.rule_version,
                            dec.cheapness_z, dec.verdict, _now(), "frozen 기준선 복사")
        self._rows.append(ar)
        return ar

    def recompute(self, dec: DecisionRecord, new_rule_version: str,
                  new_z: float, new_verdict: str, note: str = "") -> AnalysisRecord:
        """새 rule 로 그때를 다시 본 counterfactual (의사결정 영향 0)."""
        ar = AnalysisRecord(dec.decision_id, "counterfactual", new_rule_version,
                            new_z, new_verdict, _now(), note or "counterfactual 재계산")
        self._rows.append(ar)
        return ar

    def for_decision(self, decision_id: str) -> list[AnalysisRecord]:
        return [r for r in self._rows if r.decision_id == decision_id]


@dataclass
class PerfRow:
    rule_version: str
    regime_id: int
    sector: str
    regime_model_version: str
    ic: float
    n: int
    logged_at: str


class RulePerformance:
    """append-only 성과 매트릭스. dormant rule 부활 판정."""

    def __init__(self):
        self._rows: list[PerfRow] = []

    def log(self, rule_version, regime_id, sector, regime_model_version, ic, n) -> None:
        self._rows.append(PerfRow(rule_version, regime_id, sector, regime_model_version,
                                  float(ic), int(n), _now()))

    def query(self, rule_version=None, regime_id=None, sector=None,
              regime_model_version=None) -> list[PerfRow]:
        out = self._rows
        if rule_version is not None:
            out = [r for r in out if r.rule_version == rule_version]
        if regime_id is not None:
            out = [r for r in out if r.regime_id == regime_id]
        if sector is not None:
            out = [r for r in out if r.sector == sector]
        if regime_model_version is not None:
            out = [r for r in out if r.regime_model_version == regime_model_version]
        return out

    def dormant_revival_candidates(self, regime_id: int, regime_model_version: str,
                                   ic_floor: float = 0.02) -> list[str]:
        """이 regime(+ 동일 regime_model_version)에서 과거 통했던 rule_version 목록.

        ⚠️ regime_model_version 일치 필수 — regime 정의가 바뀌면 과거 성과 의미가 깨짐.
        """
        rows = self.query(regime_id=regime_id, regime_model_version=regime_model_version)
        return sorted({r.rule_version for r in rows if r.ic >= ic_floor})


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


if __name__ == "__main__":
    dl = DecisionLedger()
    dec = DecisionRecord("d001", _now(), "SEMI001", "semiconductor", "2022-06-01",
                         rule_version="v1", regime_id=2, regime_model_version="rm_2024a",
                         verdict="cheap", cheapness_z=-1.8, action="buy")
    dl.record(dec)

    # 1) decision freeze: 재기록 거부
    try:
        dl.record(dec)
        raise AssertionError("freeze 위반 미검출")
    except ValueError:
        print("1) decision freeze: 재기록 거부 OK")

    # 2) analysis counterfactual: 새 rule 로 재계산, frozen 원본 불변
    al = AnalysisLedger()
    al.snapshot_frozen(dec)
    al.recompute(dec, "v2", new_z=-0.9, new_verdict="neutral", note="v2 임계 강화시 가정")
    rows = al.for_decision("d001")
    bases = {r.version_basis for r in rows}
    assert bases == {"frozen", "counterfactual"}, bases
    assert dl.get("d001").cheapness_z == -1.8   # frozen 원본 불변
    print(f"2) analysis: {[(r.version_basis, r.recomputed_z) for r in rows]} | frozen 원본 z={dl.get('d001').cheapness_z} 불변 OK")

    # 3) rule_performance + dormant 부활 (regime_model_version 필수)
    rp = RulePerformance()
    rp.log("v1", 2, "semiconductor", "rm_2024a", ic=0.05, n=120)
    rp.log("v1", 2, "semiconductor", "rm_2025b", ic=0.06, n=130)   # 다른 regime 모델
    rp.log("v3", 2, "semiconductor", "rm_2024a", ic=0.001, n=90)   # 약함
    revive = rp.dormant_revival_candidates(2, "rm_2024a")
    assert revive == ["v1"], revive   # rm_2025b 의 v1 은 다른 regime_model → 제외
    print(f"3) dormant 부활(regime2, rm_2024a): {revive} (rm_2025b·약한 v3 제외) OK")

    print("S4 ledger self-test PASS")
