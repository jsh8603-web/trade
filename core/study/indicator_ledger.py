"""core/study/indicator_ledger.py — P3: 지표 후보/채택/기각 ledger (재탐구 방지).

WHY(2026-06-01 지시): study yaml 의 지표를 후보(candidate)/채택(adopted)/기각(rejected)로
한 곳에 기록 + 사유 + 리서치 링크. "어느 지표 왜 채택/기각했나"를 잃지 않게(재탐구 방지,
consult-raw-output-mapping rule). 채택분이 런타임(corr_prior/weight_card/judge)에 반영됐는지
대조의 기준점(yaml-runtime drift 감지 — adopted 인데 코드 미반영=미완 플래그).

상태: adopted=weight_rules base_weight>0 / candidate=indicators 만(미채택) / rejected=verdict
소스(audit P2)에서 주입. reason=relationships theory_basis. research_ref=study-research 경로.
"""

from __future__ import annotations

from typing import Optional


def build_indicator_ledger(s, *, rejected_ids: Optional[dict] = None) -> list:
    """StudySession → 지표 ledger.

    각 행 = {id, family, status(adopted/candidate/rejected), weight, direction, reason,
    research_ref, in_our_system}. rejected_ids: {indicator_id: reason} = audit(P2) verdict
    기각분(선택). 미지정 시 미채택 지표 = candidate.
    """
    adopted = {wr.indicator_id: wr for wr in getattr(s, "weight_rules", [])
               if getattr(wr, "base_weight", 0) > 0}
    rel_reason: dict = {}
    for e in getattr(s, "relationships", []):
        tb = getattr(e, "theory_basis", "") or ""
        if tb:
            rel_reason.setdefault(getattr(e, "node_a", ""), tb)
            rel_reason.setdefault(getattr(e, "node_b", ""), tb)
    rejected = rejected_ids or {}
    sid = getattr(s, "study_id", "")
    ledger = []
    for ind in getattr(s, "indicators", []):
        iid = getattr(ind, "id", "")
        if iid in rejected:
            status, weight, direction, reason = "rejected", 0.0, "", rejected[iid]
        elif iid in adopted:
            wr = adopted[iid]
            status = "adopted"
            weight = float(getattr(wr, "base_weight", 0.0))
            direction = getattr(wr, "direction", "")
            reason = rel_reason.get(iid, "")
        else:
            status, weight, direction = "candidate", 0.0, ""
            reason = rel_reason.get(iid, "")
        ledger.append({
            "id": iid, "family": getattr(ind, "family", ""), "status": status,
            "weight": weight, "direction": direction, "reason": reason,
            "research_ref": f"study-research/{sid}/" if sid else "",
            "in_our_system": bool(getattr(ind, "in_our_system", False)),
        })
    return ledger


def ledger_summary(ledger: list) -> dict:
    """ledger → {adopted, candidate, rejected} 카운트 + adopted_ids(런타임 반영 대조 기준)."""
    out = {"adopted": 0, "candidate": 0, "rejected": 0, "adopted_ids": []}
    for row in ledger:
        st = row.get("status", "candidate")
        out[st] = out.get(st, 0) + 1
        if st == "adopted":
            out["adopted_ids"].append(row["id"])
    return out


if __name__ == "__main__":
    from dataclasses import dataclass, field

    @dataclass
    class _Ind:
        id: str
        family: str = ""
        in_our_system: bool = False

    @dataclass
    class _WR:
        indicator_id: str
        base_weight: float = 0.0
        direction: str = ""

    @dataclass
    class _Edge:
        node_a: str
        node_b: str = ""
        theory_basis: str = ""

    @dataclass
    class _S:
        study_id: str = "macro"
        indicators: list = field(default_factory=list)
        weight_rules: list = field(default_factory=list)
        relationships: list = field(default_factory=list)

    s = _S(
        indicators=[_Ind("hy_oas", "credit", True), _Ind("y10_2", "rate", True),
                    _Ind("vix", "vol", False)],
        weight_rules=[_WR("hy_oas", 0.25, "neg"), _WR("y10_2", 0.0)],  # y10_2 weight0=미채택
        relationships=[_Edge("hy_oas", "y10_2", "리스크오프 동반")],
    )
    led = build_indicator_ledger(s, rejected_ids={"vix": "다중비교 미생존(audit)"})
    summ = ledger_summary(led)
    assert summ["adopted"] == 1 and summ["adopted_ids"] == ["hy_oas"], summ
    assert summ["candidate"] == 1 and summ["rejected"] == 1, summ
    hy = next(r for r in led if r["id"] == "hy_oas")
    assert hy["status"] == "adopted" and hy["weight"] == 0.25 and hy["reason"] == "리스크오프 동반", hy
    vix = next(r for r in led if r["id"] == "vix")
    assert vix["status"] == "rejected" and "audit" in vix["reason"], vix
    print(f"indicator_ledger self-test PASS: {summ}")
    for r in led:
        print(f"  {r['id']}: {r['status']} w={r['weight']} reason='{r['reason'][:24]}'")
