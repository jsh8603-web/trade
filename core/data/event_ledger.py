"""core/data/event_ledger.py — THE EVENT LEDGER (가정 라이프사이클 본체, L1).

closed-loop substrate = **단일 bitemporal append-only event ledger**. btn-button 5R 확정 +
전체구조 3R 자문(CONSULT-DECISIONS-whole §btn-Inv) 보강 반영. 본인(T1)이 ledger 본체 소유,
btn-button(T2)=read-only 소비, btn-Codlearn(T3)=lifecycle emit + state 소비.

★보강 5 (whole §btn-Inv):
1. **12 event**(11→12, +REVISION_OBSERVED). revision = 새 bitemporal fact(동 vt·새 tt·
   supersedes=원본 event_id). ⛔ OUTCOME 에 vintage 필드 mutate 금지(append-only 위반 +
   tt 순서 소실 = revised lookahead alpha 누수). as-of = 각 vt 에서 tt ≤ as-of 최신 fact.
2. **3 typed timestamp 강제**(single 금지): tt(transaction=append 불변·seq total order=저장순)
   / dt(decision=엔진 인지) / vt(valid=데이터 날짜). reduce=tt순, FDR replay=dt순, Brier=vt재계산.
3. **CQRS**: log=진실원(append-only), snapshot=tt-cut reduce projection + watermark(seq),
   순서=append→ack→project. byte-identical 보장 = reducer 결정론.
4. FDR_DECISION = immutable(dt 순 재생). late OUTCOME append = wealth 되감기 X(vt-indexed Brier만).
5. Walking Skeleton: dummy-event 랜덤순서 → tt-cut state 100% 복원 TDD 증명 전 분석로직 금지.

영속: jsonl append + fsync, snapshot = .tmp→os.replace 원자성. crc = 라인 변조/손상 탐지.
"""

from __future__ import annotations

import json
import os
import zlib
from dataclasses import asdict, dataclass, field, replace
from datetime import date, datetime, timedelta
from functools import reduce
from typing import Iterable, Optional, Union

LEDGER_SCHEMA_VERSION = "el_v1"

# 16 event types (★REVISION_OBSERVED + IC9 reject 재진입 lifecycle 4종)
EVENT_TYPES = (
    "ASSUMPTION_CREATED",
    "PREDICTION_MADE",
    "OUTCOME_OBSERVED",
    "REVISION_OBSERVED",       # ★ 12번째: 사후 정정 = 새 bitemporal fact
    "HOLD_REMEASURED",
    "CANDIDATE_PROPOSED",
    "RATIFIED",
    "FDR_DECISION",
    "TRANSITIONED",
    "RETIRED",
    "DATA_CONTRACT_VIOLATION",
    "CALIBRATION_CHANGED",
    # ★IC9(§14.6) reject 가설 재진입 lifecycle. opt-in on 경로에서만 emit(off=미발생=byte-identical,
    #   기존 reader 가 신규 type skip 하는 forward-compat fold). 신규 ledger 금지 = 본 단일 원장 확장.
    "REJECT_RECORDED",         # 기각 기록(§14.6 필드: reject_class·E_against·power·trigger 등)
    "REVIVAL_TRIGGERED",       # 재진입 트리거 발화(regime_draw/data_event/n_regime_gated)
    "SHADOW_REENTERED",        # 관찰 상태 재진입(E_for 누적 시작, risk 불변 paper)
    "REVIVED",                 # live 복귀(adopt gate 통과, 무인 자동 — §14.1 human surface 신설 X)
)

TsLike = Union[str, datetime]
_EPOCH = datetime(1970, 1, 1)
_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _ts(x: TsLike) -> datetime:
    """str/datetime → naive datetime (UTC 가정, 단일 시간축 IA-6)."""
    if isinstance(x, datetime):
        return x.replace(tzinfo=None) if x.tzinfo is not None else x
    return datetime.fromisoformat(str(x))


def _b32(value: int, length: int) -> str:
    """비음수 정수 → Crockford base32, length 자리 zero-pad (ULID 구성용, 결정적)."""
    if value < 0:
        raise ValueError(f"음수 인코딩 불가: {value}")
    out = []
    for _ in range(length):
        value, rem = divmod(value, 32)
        out.append(_CROCKFORD[rem])
    return "".join(reversed(out))


def _ulid(tt: datetime, seq: int) -> str:
    """ULID-유사 26자(시간 10 + seq 16). tt·seq 로 **결정적** 생성(테스트 재현성·정렬성).

    표준 ULID 는 시간 48bit + 랜덤 80bit. 여기선 랜덤 대신 seq 를 써 동일 입력 = 동일 id
    (replay byte-identity 의 전제). lexicographic 정렬 = (tt, seq) 정렬과 일치.
    """
    ms = int((tt - _EPOCH).total_seconds() * 1000)
    return _b32(ms, 10) + _b32(seq, 16)


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LedgerEvent:
    """단일 ledger 이벤트. frozen(append-only 불변). 생성은 make_event 팩토리 경유."""
    event_type: str
    tt: datetime               # transaction time (append, 저장순)
    dt: datetime               # decision time (엔진 인지)
    vt: datetime               # valid time (데이터 날짜)
    seq: int
    event_id: str
    crc: str
    asset_class: str = ""
    assumption_id: str = ""
    parent_event_id: str = ""
    config_hash: str = ""
    data_vintage: str = ""
    payload: dict = field(default_factory=dict)
    schema_version: str = LEDGER_SCHEMA_VERSION

    def _content_for_crc(self) -> dict:
        d = asdict(self)
        d.pop("crc", None)
        for k in ("tt", "dt", "vt"):
            d[k] = d[k].isoformat()
        return d

    def verify_crc(self) -> bool:
        return self.crc == _crc_of(self._content_for_crc())

    def to_json(self) -> str:
        d = asdict(self)
        for k in ("tt", "dt", "vt"):
            d[k] = d[k].isoformat()
        return json.dumps(d, ensure_ascii=False, sort_keys=True)

    @classmethod
    def from_json(cls, line: str) -> "LedgerEvent":
        d = json.loads(line)
        for k in ("tt", "dt", "vt"):
            d[k] = _ts(d[k])
        return cls(**d)


def _crc_of(content: dict) -> str:
    canon = json.dumps(content, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return f"{zlib.crc32(canon) & 0xFFFFFFFF:08x}"


def make_event(
    event_type: str,
    *,
    tt: TsLike,
    dt: TsLike,
    vt: TsLike,
    seq: int,
    asset_class: str = "",
    assumption_id: str = "",
    parent_event_id: str = "",
    config_hash: str = "",
    data_vintage: str = "",
    payload: Optional[dict] = None,
) -> LedgerEvent:
    """이벤트 생성 팩토리. event_id(ULID) + crc 자동 계산. 3 timestamp 강제."""
    if event_type not in EVENT_TYPES:
        raise ValueError(f"미정의 event_type: {event_type} (정의={EVENT_TYPES})")
    ttd, dtd, vtd = _ts(tt), _ts(dt), _ts(vt)
    base = dict(
        event_type=event_type, tt=ttd, dt=dtd, vt=vtd, seq=seq, event_id="", crc="",
        asset_class=asset_class, assumption_id=assumption_id,
        parent_event_id=parent_event_id, config_hash=config_hash,
        data_vintage=data_vintage, payload=dict(payload or {}),
        schema_version=LEDGER_SCHEMA_VERSION,
    )
    ev = LedgerEvent(**base)
    ev = replace(ev, event_id=_ulid(ttd, seq))
    ev = replace(ev, crc=_crc_of(ev._content_for_crc()))
    return ev


# ---------------------------------------------------------------------------
# State (read-model / snapshot)
# ---------------------------------------------------------------------------

@dataclass
class Fact:
    """series×vt 의 관측 1건(OUTCOME 또는 REVISION). as-of 해석의 단위."""
    series_key: str
    vt: datetime
    tt: datetime
    value: float
    event_id: str
    supersedes: str = ""   # REVISION 이면 원본 OUTCOME event_id


@dataclass
class LedgerState:
    """tt-cut projection 스냅샷. watermark = 포함된 최대 seq(CQRS)."""
    watermark_seq: int = -1
    watermark_tt: Optional[datetime] = None
    assumptions: dict = field(default_factory=dict)      # id -> {status, version}
    predictions: dict = field(default_factory=dict)      # event_id -> payload
    facts: dict = field(default_factory=dict)            # (series_key, vt_iso) -> [Fact...]
    fdr_log: list = field(default_factory=list)          # FDR_DECISION (tt순 적재, dt replay 대상)
    incidents: list = field(default_factory=list)        # DATA_CONTRACT_VIOLATION payload
    retired: set = field(default_factory=set)
    rejects: dict = field(default_factory=dict)          # ★IC9: hypothesis_id → reject 재진입 상태
    #   (materialized projection, §14.6). status: rejected→shadow→revived. opt-in off=빈 dict(무영향).

    # --- as-of 해석 (REVISION 반영 PIT) -------------------------------
    def resolve_fact(self, series_key: str, vt: TsLike, as_of: TsLike) -> Optional[Fact]:
        """series×vt 의 as-of 값 = tt ≤ as_of 인 fact 중 최신 tt(REVISION supersede 자동 반영)."""
        key = (series_key, _ts(vt).isoformat())
        a = _ts(as_of)
        cands = [f for f in self.facts.get(key, []) if f.tt <= a]
        if not cands:
            return None
        return max(cands, key=lambda f: f.tt)

    # --- FDR dt 순 재생 (immutable) -----------------------------------
    def fdr_replay(self) -> list:
        """FDR_DECISION 을 dt 순으로 정렬 반환. 결정 필드는 write-time 동결(재계산 X)."""
        return sorted(self.fdr_log, key=lambda e: (e["dt"], e["seq"]))

    # --- reject 재진입 상태 as-of (REVIVAL lifecycle, §14.6) -----------
    def reject_status(self, hypothesis_id: str) -> Optional[str]:
        """hypothesis_id 의 reject 상태(rejected/shadow/revived) 또는 None(reject 이력 없음).
        as-of = reduce_events(tt_cut) 가 이미 cut 시점 fold → 본 메서드는 그 projection 단순 조회."""
        r = self.rejects.get(hypothesis_id)
        return r.get("status") if r else None

    # --- assumption graduation 상태 as-of (IC4 lifecycle) ----------------
    def assumption_status(self, assumption_id: str) -> Optional[str]:
        """assumption 의 lifecycle 상태(active/candidate/ratified/transitioned/retired) 또는 None.
        IC4 graduation: CANDIDATE_PROPOSED→candidate, RATIFIED→ratified(adopted). tt_cut as-of 조회."""
        a = self.assumptions.get(assumption_id)
        return a.get("status") if a else None


# ---------------------------------------------------------------------------
# Pure reducer
# ---------------------------------------------------------------------------

def _pure_apply(state: LedgerState, ev: LedgerEvent) -> LedgerState:
    """단일 이벤트 적용(순수). tt 순 정렬 전제. state 를 in-place 갱신 후 반환."""
    et, p = ev.event_type, ev.payload
    if et == "ASSUMPTION_CREATED":
        state.assumptions[ev.assumption_id] = {
            "status": "active", "version": p.get("version", 1)}
    elif et == "PREDICTION_MADE":
        state.predictions[ev.event_id] = {
            "assumption_id": ev.assumption_id, "vt": ev.vt.isoformat(), **p}
    elif et in ("OUTCOME_OBSERVED", "REVISION_OBSERVED"):
        series = p.get("series_key", ev.assumption_id)
        key = (series, ev.vt.isoformat())
        state.facts.setdefault(key, []).append(Fact(
            series_key=series, vt=ev.vt, tt=ev.tt,
            value=float(p.get("value", 0.0)), event_id=ev.event_id,
            supersedes=p.get("supersedes", "") if et == "REVISION_OBSERVED" else "",
        ))
    elif et == "FDR_DECISION":
        # 결정 필드 동결: dt/seq + write-time decision/alpha 를 그대로 보존(재계산 금지)
        state.fdr_log.append({
            "dt": ev.dt.isoformat(), "seq": ev.seq, "event_id": ev.event_id,
            "reject": bool(p.get("reject", False)),
            "p_value": p.get("p_value"), "alpha_spent": p.get("alpha_spent"),
            "family_key": p.get("family_key", ""), "account_type": p.get("account_type", "discovery"),
        })
    elif et == "DATA_CONTRACT_VIOLATION":
        state.incidents.append({"event_id": ev.event_id, "tt": ev.tt.isoformat(), **p})
    elif et in ("RETIRED", "TRANSITIONED"):
        if ev.assumption_id in state.assumptions:
            state.assumptions[ev.assumption_id]["status"] = et.lower()
        if et == "RETIRED":
            state.retired.add(ev.assumption_id)
    elif et == "REJECT_RECORDED":
        # ★IC9(§14.6): 기각 기록 → reject pool 진입(status=rejected). reject_class·E_against·power 보존.
        hid = p.get("hypothesis_id", ev.assumption_id)
        state.rejects[hid] = {"status": "rejected", "tt": ev.tt.isoformat(), **p}
    elif et == "REVIVAL_TRIGGERED":
        # ★IC9: 재진입 트리거 발화 — trigger 타입·E_for 갱신(status=rejected 유지, shadow 전 단계).
        hid = p.get("hypothesis_id", ev.assumption_id)
        r = state.rejects.get(hid)
        if r is not None:
            r["revival_trigger"] = p.get("revival_trigger")
            if "e_for_state" in p:
                r["e_for_state"] = p["e_for_state"]
    elif et == "SHADOW_REENTERED":
        # ★IC9: 관찰 상태 재진입(E_for 누적 시작, risk 불변 paper). status=shadow.
        hid = p.get("hypothesis_id", ev.assumption_id)
        r = state.rejects.get(hid)
        if r is not None:
            r["status"] = "shadow"
            if "e_for_state" in p:
                r["e_for_state"] = p["e_for_state"]
    elif et == "REVIVED":
        # ★IC9: live 복귀(adopt gate 통과, 무인 자동 — §14.1). status=revived.
        hid = p.get("hypothesis_id", ev.assumption_id)
        r = state.rejects.get(hid)
        if r is not None:
            r["status"] = "revived"
    elif et == "CANDIDATE_PROPOSED":
        # ★IC4 graduation lifecycle: candidate 진입(검증 누적 대기). opt-in on 경로만 emit
        #   (off=미발생=byte-identical). 기존 active 가설도 candidate 로 명시 표식(졸업 후보군).
        if ev.assumption_id in state.assumptions:
            state.assumptions[ev.assumption_id]["status"] = "candidate"
        else:
            state.assumptions[ev.assumption_id] = {"status": "candidate", "version": p.get("version", 1)}
    elif et == "RATIFIED":
        # ★IC4: 5-AND graduation gate 통과 → adopted(ratified). graduation_sweep 발행(무인 자동,
        #   StudyRegister 자가승격 0 — owner=외부 평가자). reject 의 REVIVED 와 대칭(candidate→adopted).
        if ev.assumption_id in state.assumptions:
            state.assumptions[ev.assumption_id]["status"] = "ratified"
        else:
            state.assumptions[ev.assumption_id] = {"status": "ratified", "version": p.get("version", 1)}
    elif et in ("HOLD_REMEASURED", "CALIBRATION_CHANGED"):
        pass  # 골격: 라이프사이클 마커(상태 변화는 P3+ 에서 plug-in)
    # watermark 갱신
    if ev.seq > state.watermark_seq:
        state.watermark_seq = ev.seq
    if state.watermark_tt is None or ev.tt > state.watermark_tt:
        state.watermark_tt = ev.tt
    return state


def reduce_events(events: Iterable[LedgerEvent], tt_cut: Optional[TsLike] = None) -> LedgerState:
    """★순수 projection. 임의 입력순서 → (tt, seq) 정렬 후 reduce → 결정적 state.

    tt_cut 지정 시 tt ≤ tt_cut 인 이벤트만(CQRS tt-cut 스냅샷). 이것이 random-order 100%
    복원 + byte-identical replay 의 핵심: 저장순/도착순 무관하게 동일 cut → 동일 state.
    """
    evs = list(events)
    if tt_cut is not None:
        cut = _ts(tt_cut)
        evs = [e for e in evs if e.tt <= cut]
    evs.sort(key=lambda e: (e.tt, e.seq))
    return reduce(_pure_apply, evs, LedgerState())


# ---------------------------------------------------------------------------
# EventLedger — append-only log + CQRS projection (영속)
# ---------------------------------------------------------------------------

class EventLedger:
    """append-only jsonl 진실원 + tt-cut projection. append→ack→project(CQRS)."""

    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path
        self._log: list[LedgerEvent] = []
        self._max_seq = -1

    # --- append → ack -------------------------------------------------
    def append(self, ev: LedgerEvent) -> str:
        """이벤트 추가(진실원). seq monotonic 강제. 반환 = ack(event_id). 영속 후 ack."""
        if ev.seq <= self._max_seq:
            raise ValueError(f"seq 비단조: {ev.seq} ≤ watermark {self._max_seq} (append-only total order)")
        if not ev.verify_crc():
            raise ValueError(f"crc 불일치(변조 의심): {ev.event_id}")
        self._log.append(ev)
        self._max_seq = ev.seq
        if self.path is not None:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(ev.to_json() + "\n")
                fh.flush()
                os.fsync(fh.fileno())
        return ev.event_id   # ack

    def emit(self, event_type: str, **kw) -> str:
        """make_event + append 원샷. seq 미지정 시 watermark+1 자동."""
        kw.setdefault("seq", self._max_seq + 1)
        return self.append(make_event(event_type, **kw))

    # --- project (read-model) -----------------------------------------
    def project(self, tt_cut: Optional[TsLike] = None) -> LedgerState:
        """tt-cut 스냅샷(read-model). 라이브 소비는 이 projection 만 본다(로그 직접조회 금지)."""
        return reduce_events(self._log, tt_cut)

    # --- 영속 round-trip ----------------------------------------------
    @classmethod
    def load(cls, path: str) -> "EventLedger":
        """jsonl 재적재 + crc 검증. 진실원 복구."""
        led = cls(path)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                for ln, raw in enumerate(fh, 1):
                    raw = raw.strip()
                    if not raw:
                        continue
                    ev = LedgerEvent.from_json(raw)
                    if not ev.verify_crc():
                        raise ValueError(f"{path}:{ln} crc 불일치(손상/변조): {ev.event_id}")
                    led._log.append(ev)
                    led._max_seq = max(led._max_seq, ev.seq)
        return led

    def save_snapshot(self, state: LedgerState, snap_path: str) -> None:
        """tt-cut 스냅샷 영속 = .tmp→os.replace 원자성(부분쓰기 가시 차단)."""
        tmp = snap_path + ".tmp"
        snap = {
            "watermark_seq": state.watermark_seq,
            "watermark_tt": state.watermark_tt.isoformat() if state.watermark_tt else None,
            "n_assumptions": len(state.assumptions),
            "n_predictions": len(state.predictions),
            "n_facts": sum(len(v) for v in state.facts.values()),
            "n_fdr": len(state.fdr_log),
            "n_incidents": len(state.incidents),
        }
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(snap, fh, ensure_ascii=False, sort_keys=True)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, snap_path)


# ---------------------------------------------------------------------------
# Walking Skeleton self-test (분석로직 금지 — 인프라 결정론만 증명)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import random
    import tempfile

    # 더미 이벤트 배터리 (3 timestamp 명시 — 결정적)
    def mk(seq, et, tt, dt, vt, **p):
        return make_event(et, tt=tt, dt=dt, vt=vt, seq=seq, assumption_id=p.pop("aid", "A1"),
                          asset_class=p.pop("ac", "crypto"), payload=p)

    events = [
        mk(0, "ASSUMPTION_CREATED", "2024-01-01", "2024-01-01", "2024-01-01", version=1),
        mk(1, "PREDICTION_MADE",    "2024-01-02", "2024-01-02", "2024-01-02", horizon_h=168),
        mk(2, "FDR_DECISION",       "2024-01-03", "2024-01-03", "2024-01-03", reject=True,  p_value=0.01, alpha_spent=0.01, family_key="crypto:c1"),
        mk(3, "OUTCOME_OBSERVED",   "2024-01-10", "2024-01-10", "2024-01-09", series_key="A1", value=1.7),
        mk(4, "FDR_DECISION",       "2024-01-12", "2024-01-12", "2024-01-12", reject=False, p_value=0.30, alpha_spent=0.0, family_key="crypto:c1"),
        mk(5, "ASSUMPTION_CREATED", "2024-02-01", "2024-02-01", "2024-02-01", aid="A2", version=1),
    ]

    # 1) ★random-order → tt-cut state 100% 복원 (Walking Skeleton 핵심)
    canon = reduce_events(events)
    for trial in range(20):
        shuffled = events[:]
        random.shuffle(shuffled)
        got = reduce_events(shuffled)
        assert got == canon, f"random-order 복원 실패(trial {trial})"
    print(f"1) random-order(20회) → 동일 state 100% 복원 OK (watermark_seq={canon.watermark_seq})")

    # 2) ★CQRS tt-cut + watermark: cut 시점 이후 이벤트 제외
    cut_state = reduce_events(events, tt_cut="2024-01-05")
    assert cut_state.watermark_seq == 2, cut_state.watermark_seq   # seq 0,1,2 만 tt≤01-05
    assert "A2" not in cut_state.assumptions, "02-01 생성 A2 는 cut 밖"
    assert len(cut_state.fdr_log) == 1, cut_state.fdr_log          # FDR seq2 만
    print(f"2) CQRS tt-cut(2024-01-05): watermark_seq={cut_state.watermark_seq}, A2 제외, FDR 1건 OK")

    # 3) ★FDR dt 순 immutable replay
    full = reduce_events(events)
    rep = full.fdr_replay()
    assert [e["seq"] for e in rep] == [2, 4], [e["seq"] for e in rep]   # dt 순
    assert rep[0]["reject"] is True and rep[1]["reject"] is False, rep   # 동결 결정
    print(f"3) FDR dt-순 replay: seq={[e['seq'] for e in rep]} reject={[e['reject'] for e in rep]} (동결) OK")

    # 4) ★late OUTCOME append = wealth 되감기 X (FDR 시퀀스 불변)
    late = events + [mk(6, "OUTCOME_OBSERVED", "2024-03-01", "2024-03-01", "2024-01-02",
                        series_key="A1", value=2.1)]  # vt 과거(01-02)·tt 최신(03-01)
    late_state = reduce_events(late)
    assert [e["seq"] for e in late_state.fdr_replay()] == [2, 4], "late outcome 이 FDR 시퀀스 변경"
    print("4) late OUTCOME(vt 과거·tt 최신): FDR dt-시퀀스 불변(wealth 되감기 X) OK")

    # 5) ★REVISION as-of: 동 vt 정정 = 새 fact, as-of 별 다른 값
    rev_events = [
        mk(0, "OUTCOME_OBSERVED",  "2024-02-15", "2024-02-15", "2024-01-31", series_key="CPI", value=2.0),
        mk(1, "REVISION_OBSERVED", "2024-03-15", "2024-03-15", "2024-01-31", series_key="CPI", value=2.5, supersedes="_orig"),
    ]
    rs = reduce_events(rev_events)
    f_feb = rs.resolve_fact("CPI", "2024-01-31", "2024-02-20")  # 정정 전
    f_mar = rs.resolve_fact("CPI", "2024-01-31", "2024-03-20")  # 정정 후
    assert f_feb.value == 2.0 and f_mar.value == 2.5, (f_feb.value, f_mar.value)
    # OUTCOME 원본은 log 에 그대로(append-only: 같은 series×vt fact 2건 보존)
    assert len(rs.facts[("CPI", _ts("2024-01-31").isoformat())]) == 2
    print(f"5) REVISION as-of: 02-20→{f_feb.value} / 03-20→{f_mar.value} (원본 mutate X, fact 2건) OK")

    # 6) ★영속 round-trip: jsonl append→load→reduce = in-memory state
    tmp = os.path.join(tempfile.gettempdir(), "el_selftest.jsonl")
    if os.path.exists(tmp):
        os.remove(tmp)
    led = EventLedger(tmp)
    for ev in events:
        led.append(ev)
    reloaded = EventLedger.load(tmp)
    assert reduce_events(reloaded._log) == canon, "영속 round-trip state 불일치"
    snap_path = tmp + ".snap"
    led.save_snapshot(led.project(), snap_path)
    assert os.path.exists(snap_path), "snapshot os.replace 실패"
    print("6) 영속 round-trip: jsonl append→load→reduce 동일 + snapshot os.replace OK")

    # 7) ★crc 변조 탐지: 라인 payload 손상 → load 거부
    with open(tmp, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    bad = json.loads(lines[1]); bad["payload"]["horizon_h"] = 999
    lines[1] = json.dumps(bad, ensure_ascii=False, sort_keys=True) + "\n"
    bad_path = tmp + ".bad"
    with open(bad_path, "w", encoding="utf-8") as fh:
        fh.writelines(lines)
    try:
        EventLedger.load(bad_path)
        raise AssertionError("변조 라인이 load 를 통과함")
    except ValueError as e:
        assert "crc" in str(e), e
    print("7) crc 변조 탐지: payload 손상 라인 load 거부 OK")

    # 8) seq 비단조 append 거부
    led2 = EventLedger()
    led2.append(mk(5, "ASSUMPTION_CREATED", "2024-01-01", "2024-01-01", "2024-01-01"))
    try:
        led2.append(mk(3, "ASSUMPTION_CREATED", "2024-01-02", "2024-01-02", "2024-01-02"))
        raise AssertionError("seq 역행이 통과함")
    except ValueError:
        print("8) seq 비단조 append 거부 OK")

    # 9) ★property-based test (R5 유일 material 잔여 = V&V 코드정합성)
    #    랜덤 valid 이벤트열 생성 → reducer 5 불변식 검증(수식≠코드 직교, hypothesis 미설치 수동).
    rnd = random.Random(20260529)
    EV_POOL = ["ASSUMPTION_CREATED", "PREDICTION_MADE", "OUTCOME_OBSERVED",
               "REVISION_OBSERVED", "FDR_DECISION", "HOLD_REMEASURED", "RETIRED"]
    SERIES = ["S1", "S2", "S3"]
    BASE = date(2024, 1, 1)

    def _rand_stream(n):
        evs = []
        for i in range(n):
            et = rnd.choice(EV_POOL)
            off_vt = rnd.randint(0, 60)
            off_tt = off_vt + rnd.randint(0, 30)     # tt ≥ vt (인지 ≥ 데이터)
            off_dt = rnd.randint(0, off_tt)
            tt = (BASE + timedelta(days=off_tt)).isoformat()
            dt = (BASE + timedelta(days=off_dt)).isoformat()
            vt = (BASE + timedelta(days=off_vt)).isoformat()
            p = {}
            if et in ("OUTCOME_OBSERVED", "REVISION_OBSERVED"):
                p = {"series_key": rnd.choice(SERIES), "value": round(rnd.uniform(-5, 5), 4)}
                if et == "REVISION_OBSERVED":
                    p["supersedes"] = f"_r{i}"
            elif et == "FDR_DECISION":
                p = {"reject": rnd.random() < 0.4, "p_value": round(rnd.random(), 4),
                     "alpha_spent": 0.01, "family_key": rnd.choice(["f1", "f2"])}
            elif et == "ASSUMPTION_CREATED":
                p = {"version": rnd.randint(1, 3)}
            evs.append(make_event(et, tt=tt, dt=dt, vt=vt, seq=i,
                                  assumption_id=rnd.choice(["A1", "A2", "A3"]),
                                  asset_class="crypto", payload=p))
        return evs

    TRIALS = 60
    for trial in range(TRIALS):
        evs = _rand_stream(rnd.randint(5, 30))
        canon_s = reduce_events(evs)

        # 불변식 ②: 입력순서 무관 (3회 셔플 동일)
        for _ in range(3):
            sh = evs[:]; rnd.shuffle(sh)
            assert reduce_events(sh) == canon_s, f"순서무관 위반(trial {trial})"

        # 불변식 ①: tt-cut 결정성 (임의 cut 셔플 동일)
        cuts = sorted({e.tt for e in evs})
        if cuts:
            c = rnd.choice(cuts)
            sh = evs[:]; rnd.shuffle(sh)
            assert reduce_events(evs, c) == reduce_events(sh, c), f"tt-cut 결정성 위반(trial {trial})"

            # 불변식 ③: watermark 단조 (cut↑ → watermark_seq 비감소)
            prev_wm = -1
            for c2 in cuts:
                wm = reduce_events(evs, c2).watermark_seq
                assert wm >= prev_wm, f"watermark 비단조(trial {trial})"
                prev_wm = wm

        # 불변식 ④: FDR dt-순 정렬 + 안정
        fdr = canon_s.fdr_replay()
        keys = [(e["dt"], e["seq"]) for e in fdr]
        assert keys == sorted(keys), f"FDR dt-순 위반(trial {trial})"

        # 불변식 ⑤: append-only 보존 (facts 수 == OUTCOME+REVISION 이벤트 수)
        n_fact_ev = sum(1 for e in evs if e.event_type in ("OUTCOME_OBSERVED", "REVISION_OBSERVED"))
        n_facts = sum(len(v) for v in canon_s.facts.values())
        assert n_facts == n_fact_ev, f"append-only 보존 위반(trial {trial}): {n_facts}≠{n_fact_ev}"

    print(f"9) ★property-based({TRIALS} trial × 5 불변식): 순서무관·tt-cut 결정성·watermark 단조·"
          f"FDR dt-순·append-only 보존 전부 OK")

    # 10) ★IC9(§14.6) reject 재진입 lifecycle: REJECT_RECORDED→REVIVAL_TRIGGERED→SHADOW_REENTERED→REVIVED
    rj_evs = [
        mk(0, "REJECT_RECORDED", "2024-01-01", "2024-01-01", "2024-01-01", aid="H1",
           hypothesis_id="rj_abc", reject_class="regime_conditional", reason_code="credit_n4",
           e_against_at_reject=2.1, power_at_decision=0.3),
        mk(1, "REVIVAL_TRIGGERED", "2024-06-01", "2024-06-01", "2024-06-01", aid="H1",
           hypothesis_id="rj_abc", revival_trigger="regime_draw", e_for_state=5.0),
        mk(2, "SHADOW_REENTERED", "2024-06-02", "2024-06-02", "2024-06-02", aid="H1",
           hypothesis_id="rj_abc", e_for_state=12.0),
        mk(3, "REVIVED", "2024-07-01", "2024-07-01", "2024-07-01", aid="H1", hypothesis_id="rj_abc"),
    ]
    assert reduce_events(rj_evs, tt_cut="2024-03-01").reject_status("rj_abc") == "rejected"
    assert reduce_events(rj_evs, tt_cut="2024-06-15").reject_status("rj_abc") == "shadow"
    assert reduce_events(rj_evs, tt_cut="2024-08-01").reject_status("rj_abc") == "revived"
    s_trig = reduce_events(rj_evs, tt_cut="2024-06-01")        # 트리거 발화(shadow 전) → trigger 기록·status 유지
    assert s_trig.rejects["rj_abc"]["status"] == "rejected"
    assert s_trig.rejects["rj_abc"]["revival_trigger"] == "regime_draw"
    for _ in range(10):                                        # random-order 복원(tt순 결정적)
        sh = rj_evs[:]; random.shuffle(sh)
        assert reduce_events(sh, tt_cut="2024-06-15").reject_status("rj_abc") == "shadow"
    no_reject = reduce_events(events).rejects                  # ★off byte-identical: reject event 無 → rejects={}
    assert no_reject == {}, f"기존 event 만인데 rejects 비어있지 않음: {no_reject}"
    print("10) ★IC9 reject 재진입 as-of: 03-01=rejected / 06-01(trig)=rejected+regime_draw / "
          "06-15=shadow / 08-01=revived + random-order 복원 + off(reject event 無)=rejects 빈 OK")

    print("event_ledger (16event·3ts·CQRS·Walking Skeleton + property-based + IC9 reject lifecycle) self-test PASS")
