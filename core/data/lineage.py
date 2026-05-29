"""core/data/lineage.py — 도출 provenance + as_of replay (IA-3 lineage replay).

IA-3: 임의 as_of 의 가정체인을 재현할 수 있어야 한다. 파생값(derived parameter, 신호,
FDR 입력)은 **무엇으로부터 어떤 함수로** 나왔는지 추적 가능해야 하고, 그 체인을 그 시점에
알 수 있던 입력만으로 **재구성(replay)**할 수 있어야 한다.

설계: 각 도출 = LineageEvent(output_id, inputs[ProvenanceRef], derivation_fn_version,
config_hash, knowable_from, sys_time). append-only jsonl. `replay(output_id, as_of)` 는
as_of 에 알 수 있던 최신 도출과 그 입력 체인을 재귀 수집.

★write-time 동결(claude R3 invariant lock): knowable_from·config_hash 는 도출 시점에 동결
materialize. replay 에서 재계산 금지(재계산하면 그 시점 진실이 아닌 현재 코드로 오염).
config_hash = event_ledger 공통필드와 동일 의미(compute_delay+derivation_fn_version stamp).
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Optional, Union

AsOfLike = Union[str, date, datetime]


def _d(x: AsOfLike) -> date:
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    return datetime.fromisoformat(str(x)).date()


@dataclass(frozen=True)
class ProvenanceRef:
    """도출 입력 1건 참조. kind=raw(시장데이터)/assumption(가정 id+version)/derived(상위 도출)."""
    ref_id: str
    kind: str                 # "raw" | "assumption" | "derived"
    vintage: str = ""         # data_vintage(있으면) — event_ledger 연계
    version: str = ""         # assumption 이면 version


@dataclass(frozen=True)
class LineageEvent:
    """단일 도출 step. write-time 동결(knowable_from·config_hash)."""
    output_id: str
    inputs: tuple             # tuple[ProvenanceRef,...]
    derivation_fn_version: str
    config_hash: str
    knowable_from: date
    sys_time: date

    def to_json(self) -> str:
        d = asdict(self)
        d["knowable_from"] = self.knowable_from.isoformat()
        d["sys_time"] = self.sys_time.isoformat()
        d["inputs"] = [asdict(r) if not isinstance(r, dict) else r for r in self.inputs]
        return json.dumps(d, ensure_ascii=False, sort_keys=True)

    @classmethod
    def from_json(cls, line: str) -> "LineageEvent":
        d = json.loads(line)
        return cls(
            output_id=d["output_id"],
            inputs=tuple(ProvenanceRef(**r) for r in d["inputs"]),
            derivation_fn_version=d["derivation_fn_version"],
            config_hash=d["config_hash"],
            knowable_from=_d(d["knowable_from"]),
            sys_time=_d(d["sys_time"]),
        )


class LineageStore:
    """도출 provenance append-only 저장소 + as_of replay."""

    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path
        self._events: list[LineageEvent] = []

    def emit(
        self,
        output_id: str,
        inputs: list,
        derivation_fn_version: str,
        config_hash: str,
        knowable_from: AsOfLike,
        *,
        sys_time: Optional[AsOfLike] = None,
    ) -> LineageEvent:
        """도출 step 기록(write-time 동결). inputs = list[ProvenanceRef]."""
        kf = _d(knowable_from)
        ev = LineageEvent(
            output_id=output_id, inputs=tuple(inputs),
            derivation_fn_version=derivation_fn_version, config_hash=config_hash,
            knowable_from=kf, sys_time=_d(sys_time) if sys_time is not None else kf,
        )
        self._events.append(ev)
        if self.path is not None:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(ev.to_json() + "\n")
                fh.flush()
                os.fsync(fh.fileno())
        return ev

    def _latest(self, output_id: str, as_of: date) -> Optional[LineageEvent]:
        """as_of 에 알 수 있던(knowable≤as_of AND sys_time≤as_of) output_id 의 최신 도출."""
        cands = [e for e in self._events
                 if e.output_id == output_id and e.knowable_from <= as_of and e.sys_time <= as_of]
        if not cands:
            return None
        return max(cands, key=lambda e: (e.knowable_from, e.sys_time))

    def replay(self, output_id: str, as_of: AsOfLike) -> Optional[dict]:
        """as_of 시점 기준 output_id 의 도출 체인 재구성(재귀). 입력의 derived 는 더 파고듦.

        반환 = {output_id, fn_version, config_hash, knowable_from, inputs:[...]}.
        write-time 동결값만 사용 — 현재 코드로 재계산하지 않는다(그 시점 진실 보존).
        """
        a = _d(as_of)
        return self._replay(output_id, a, set())

    def _replay(self, output_id: str, a: date, seen: set) -> Optional[dict]:
        if output_id in seen:
            raise ValueError(f"lineage 순환 참조: {output_id}")
        ev = self._latest(output_id, a)
        if ev is None:
            return None
        seen = seen | {output_id}
        chain = []
        for ref in ev.inputs:
            node = {"ref_id": ref.ref_id, "kind": ref.kind,
                    "vintage": ref.vintage, "version": ref.version}
            if ref.kind == "derived":
                node["chain"] = self._replay(ref.ref_id, a, seen)
            chain.append(node)
        return {
            "output_id": ev.output_id, "fn_version": ev.derivation_fn_version,
            "config_hash": ev.config_hash, "knowable_from": ev.knowable_from.isoformat(),
            "inputs": chain,
        }

    @classmethod
    def load(cls, path: str) -> "LineageStore":
        st = cls(path)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if raw:
                        st._events.append(LineageEvent.from_json(raw))
        return st


if __name__ == "__main__":
    import tempfile

    st = LineageStore()

    # 도출 체인: signal_btc ← derived(cheapness_btc) + raw(price_btc)
    #            cheapness_btc ← assumption(crypto.mvrv_mean_reverts v1) + raw(mvrv_btc vintage=v20240110)
    st.emit("cheapness_btc",
            [ProvenanceRef("crypto.mvrv_mean_reverts", "assumption", version="1"),
             ProvenanceRef("mvrv_btc", "raw", vintage="v20240110")],
            derivation_fn_version="cheapness@2.1", config_hash="cfg_a1",
            knowable_from="2024-01-11")
    st.emit("signal_btc",
            [ProvenanceRef("cheapness_btc", "derived"),
             ProvenanceRef("price_btc", "raw", vintage="v20240111")],
            derivation_fn_version="signal@1.0", config_hash="cfg_b2",
            knowable_from="2024-01-11")

    # 1) replay 체인 재구성
    chain = st.replay("signal_btc", "2024-02-01")
    assert chain["output_id"] == "signal_btc" and chain["fn_version"] == "signal@1.0"
    derived = [i for i in chain["inputs"] if i["kind"] == "derived"][0]
    assert derived["chain"]["output_id"] == "cheapness_btc", derived
    assumption = [i for i in derived["chain"]["inputs"] if i["kind"] == "assumption"][0]
    assert assumption["ref_id"] == "crypto.mvrv_mean_reverts" and assumption["version"] == "1"
    print("1) replay 체인: signal_btc → cheapness_btc → {가정 v1, mvrv raw} 재귀 재구성 OK")

    # 2) ★as_of PIT: 도출 전 시점엔 None
    assert st.replay("signal_btc", "2024-01-05") is None, "도출(01-11) 전 as_of 엔 미가시"
    print("2) as_of PIT: 도출(01-11) 전 시점 replay=None OK")

    # 3) ★write-time 동결: config_hash 정정(새 sys_time) → 정정 전/후 다른 hash
    st.emit("signal_btc",
            [ProvenanceRef("cheapness_btc", "derived"),
             ProvenanceRef("price_btc", "raw", vintage="v20240111")],
            derivation_fn_version="signal@1.1", config_hash="cfg_b3",
            knowable_from="2024-01-11", sys_time="2024-03-01")
    assert st.replay("signal_btc", "2024-02-01")["config_hash"] == "cfg_b2", "정정 전 = 원본 hash"
    assert st.replay("signal_btc", "2024-03-15")["config_hash"] == "cfg_b3", "정정 후 = 새 hash"
    print("3) write-time 동결 + sys_time 정정: as_of 02-01→cfg_b2 / 03-15→cfg_b3 OK")

    # 4) 영속 round-trip
    tmp = os.path.join(tempfile.gettempdir(), "lineage_selftest.jsonl")
    if os.path.exists(tmp):
        os.remove(tmp)
    st2 = LineageStore(tmp)
    st2.emit("x", [ProvenanceRef("y", "raw", vintage="v1")], "fn@1", "h1", "2024-01-01")
    reloaded = LineageStore.load(tmp)
    assert reloaded.replay("x", "2024-06-01")["config_hash"] == "h1"
    print("4) 영속 round-trip: emit→load→replay 동일 OK")

    # 5) 순환 참조 탐지
    cyc = LineageStore()
    cyc.emit("a", [ProvenanceRef("b", "derived")], "fn", "h", "2024-01-01")
    cyc.emit("b", [ProvenanceRef("a", "derived")], "fn", "h", "2024-01-01")
    try:
        cyc.replay("a", "2024-06-01")
        raise AssertionError("순환 참조가 통과함")
    except ValueError as e:
        assert "순환" in str(e)
    print("5) 순환 참조 탐지 OK")

    print("lineage (provenance + as_of replay) self-test PASS")
