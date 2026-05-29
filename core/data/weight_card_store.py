"""core/data/weight_card_store.py — WeightCard bitemporal 영속 + V(T) selector (R15 §4-2).

CONSULT-DECISIONS-weight-20260529.md §1.7 (btn-Inv 분담).

가중카드(WeightAssumptionCard, btn-Codlearn 정의)의 **저장·조회·PIT 무결성** 계층.
카드 *내용*(weight_vector 의 의미·도출)은 btn-Codlearn 소유 — 본 store 는 그 본문을
**불가지(opaque)**하게 bitemporal 영속하고 V(T) 로 꺼내준다.

★이중 시간축(§1.7):
  - knowledge_time = 학습 데이터 PIT 경계 (이 카드가 본 외부 지표 시계열의 최신 시점)
  - decision_time  = 시스템 반영 시점 (이 카드가 라이브 결정에 활성화된 시점)
  - sys_time       = 기록/정정 시점 (silent revision 방어)

★V(T) selector: `V(T) = knowledge_time ≤ T & decision_time ≤ T & purge+embargo 충족 최신 카드`.
  embargo 충족 = decision_time − knowledge_time ≥ embargo_days (학습 경계와 사용 시점 사이
  gap — 학습 데이터가 그 결정이 평가할 outcome 으로 누수되는 것을 차단). emit-time invariant
  로 강제 + select-time 재확인(이중 방어).

★hash-pin frozen(§1.7): card_hash = 결정론적 카드 지문. replay 에 pin → re-fit(신규 버전)
  이 와도 과거 T 의 replay 는 그때 활성 카드를 byte-identical 재현. append-only(기존 불변).

event_ledger 본체는 변경 0 — 카드 lifecycle event(CREATED/RATIFIED) 의 ledger emit 은
btn-Codlearn registry.event_sink 배선점 소관. 본 store 는 그 append-only/watermark/jsonl
/os.replace 패턴을 차용한 카드 본문 SSOT.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Optional, Sequence, Union

AsOfLike = Union[str, date, datetime]


def _d(x: AsOfLike) -> date:
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    return datetime.fromisoformat(str(x)).date()


def _canon_weights(weights) -> tuple:
    """weight 매핑을 결정론 정렬 tuple 로 정규화(dict/seq 모두 허용, 내용 불가지)."""
    if isinstance(weights, dict):
        items = weights.items()
    else:
        items = weights  # iterable of (key, value)
    return tuple(sorted((str(k), round(float(v), 12)) for k, v in items))


def compute_card_hash(
    card_id: str, regime: str, archetype: str, period: str,
    weights: tuple, version: int, knowledge_time: date,
    embargo_days: int, purge_days: int, model_hash: str,
) -> str:
    """결정론적 카드 지문. replay pin — 동일 내용=동일 hash, 한 필드라도 변하면 변함."""
    payload = json.dumps({
        "card_id": card_id, "regime": regime, "archetype": archetype,
        "period": period, "weights": list(weights), "version": version,
        "knowledge_time": knowledge_time.isoformat(),
        "embargo_days": embargo_days, "purge_days": purge_days,
        "model_hash": model_hash,
    }, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


@dataclass(frozen=True)
class WeightCardRecord:
    """단일 가중카드 버전 (bitemporal). weights=내용 불가지(btn-Codlearn 소유)."""
    card_id: str               # scope 식별 키 (보통 regime|archetype|period)
    regime: str
    archetype: str
    period: str                # PIT+recency scope 라벨
    weights: tuple             # ((indicator, weight), ...) 정규화 — opaque
    version: int               # re-fit = 신규 버전 (기존 불변)
    knowledge_time: date       # 학습 데이터 PIT 경계
    decision_time: date        # 시스템 반영 시점
    sys_time: date             # 기록/정정 시점
    embargo_days: int          # 학습-사용 embargo gap (decision_time − knowledge_time ≥ 이 값)
    purge_days: int            # 학습 내부 purge (CV split 파라미터 동반 기록)
    model_hash: str            # b(t)/calibration model frozen pin (§1.6)
    card_hash: str             # 결정론적 카드 지문 (replay pin)

    def to_json(self) -> str:
        d = asdict(self)
        d["weights"] = [list(w) for w in self.weights]
        for k in ("knowledge_time", "decision_time", "sys_time"):
            d[k] = getattr(self, k).isoformat()
        return json.dumps(d, ensure_ascii=False, sort_keys=True)

    @classmethod
    def from_json(cls, line: str) -> "WeightCardRecord":
        d = json.loads(line)
        return cls(
            card_id=d["card_id"], regime=d["regime"], archetype=d["archetype"],
            period=d["period"], weights=tuple(tuple(w) for w in d["weights"]),
            version=int(d["version"]),
            knowledge_time=_d(d["knowledge_time"]), decision_time=_d(d["decision_time"]),
            sys_time=_d(d["sys_time"]), embargo_days=int(d["embargo_days"]),
            purge_days=int(d["purge_days"]), model_hash=d["model_hash"],
            card_hash=d["card_hash"],
        )


class WeightCardStore:
    """가중카드 append-only bitemporal 저장소 + V(T) selector. 카드 본문 SSOT."""

    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path
        self._cards: list[WeightCardRecord] = []
        self._watermark = 0   # append 순서(seq) — event_ledger 패턴 차용

    def emit(
        self, *, card_id: str, regime: str, archetype: str, period: str,
        weights, knowledge_time: AsOfLike, decision_time: AsOfLike,
        embargo_days: int, purge_days: int = 0, model_hash: str = "",
        version: Optional[int] = None, sys_time: Optional[AsOfLike] = None,
    ) -> WeightCardRecord:
        """카드 버전 1건 append. version 미지정=같은 card_id 최대+1(re-fit). embargo 강제.

        ★emit-time invariant: decision_time − knowledge_time ≥ embargo_days (학습 경계와
        시스템 반영 사이 embargo 미충족 = 누수 위험 → 거부). knowledge_time ≤ decision_time.
        """
        kt, dt0, st = _d(knowledge_time), _d(decision_time), (
            _d(sys_time) if sys_time is not None else _d(decision_time))
        if dt0 < kt:
            raise ValueError(f"decision_time({dt0}) < knowledge_time({kt}) = 미래 학습으로 결정")
        gap = (dt0 - kt).days
        if gap < embargo_days:
            raise ValueError(
                f"embargo 위반: decision_time−knowledge_time={gap}일 < embargo {embargo_days}일 "
                f"(학습 경계가 사용 시점에 너무 가까움 = 누수 차단)")
        if version is None:
            existing = [c.version for c in self._cards if c.card_id == card_id]
            version = (max(existing) + 1) if existing else 1
        w = _canon_weights(weights)
        h = compute_card_hash(card_id, regime, archetype, period, w, version,
                              kt, embargo_days, purge_days, model_hash)
        rec = WeightCardRecord(
            card_id=card_id, regime=regime, archetype=archetype, period=period,
            weights=w, version=version, knowledge_time=kt, decision_time=dt0,
            sys_time=st, embargo_days=embargo_days, purge_days=purge_days,
            model_hash=model_hash, card_hash=h,
        )
        self._cards.append(rec)
        self._watermark += 1
        if self.path is not None:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(rec.to_json() + "\n")
                fh.flush()
                os.fsync(fh.fileno())
        return rec

    def select(
        self, card_id: str, as_of: AsOfLike, *, require_embargo: bool = True,
    ) -> Optional[WeightCardRecord]:
        """V(T) = card_id 의, knowledge_time≤T & decision_time≤T & sys_time≤T &
        (require_embargo 시) embargo 충족, 중 가장 최신(decision_time, version, sys_time).

        re-fit 으로 신규 버전이 나중에 와도 과거 T 의 select 는 그때 활성 카드를 재현(불변).
        """
        T = _d(as_of)
        cands = [
            c for c in self._cards
            if c.card_id == card_id
            and c.knowledge_time <= T and c.decision_time <= T and c.sys_time <= T
            and (not require_embargo or (c.decision_time - c.knowledge_time).days >= c.embargo_days)
        ]
        if not cands:
            return None
        return max(cands, key=lambda c: (c.decision_time, c.version, c.sys_time))

    def history(self, card_id: str) -> list:
        """card_id 의 전 버전(append 순)."""
        return [c for c in self._cards if c.card_id == card_id]

    @property
    def watermark(self) -> int:
        return self._watermark

    @classmethod
    def load(cls, path: str) -> "WeightCardStore":
        st = cls(path)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if raw:
                        st._cards.append(WeightCardRecord.from_json(raw))
                        st._watermark += 1
        return st


if __name__ == "__main__":
    import tempfile

    st = WeightCardStore()
    cid = "risk_off|defensive|2024H1"

    # v1: 학습경계 03-31, embargo 30일 → 반영 05-01 (gap 31일 ≥ 30 OK)
    c1 = st.emit(card_id=cid, regime="risk_off", archetype="defensive", period="2024H1",
                 weights={"CPI": 0.4, "RATE": 0.35, "PMI": 0.25},
                 knowledge_time="2024-03-31", decision_time="2024-05-01",
                 embargo_days=30, purge_days=5, model_hash="bt_h1")
    assert c1.version == 1 and len(c1.card_hash) == 24
    print(f"1) emit v1: hash={c1.card_hash[:10]}.. kt=03-31 dt=05-01 embargo=30 OK")

    # 2) ★V(T): 반영 전(04-15) 미가시 / 반영 후(06-01) 가시
    assert st.select(cid, "2024-04-15") is None, "decision_time(05-01) 前 미가시"
    sel = st.select(cid, "2024-06-01")
    assert sel is not None and sel.version == 1
    print("2) V(T) 이중축: 반영(05-01) 前 미가시 / 後 v1 가시 OK")

    # 3) ★embargo 위반 거부: 학습경계 06-01, 반영 06-10 (gap 9 < embargo 30)
    try:
        st.emit(card_id=cid, regime="risk_off", archetype="defensive", period="2024H2",
                weights={"CPI": 0.5}, knowledge_time="2024-06-01", decision_time="2024-06-10",
                embargo_days=30, model_hash="x")
        raise AssertionError("embargo 위반 통과")
    except ValueError as e:
        assert "embargo" in str(e), e
    print("3) embargo 위반(gap 9<30) emit 거부 OK")

    # 4) ★re-fit = 신규 버전, 기존 불변: v2 학습경계 06-30, 반영 08-01
    c2 = st.emit(card_id=cid, regime="risk_off", archetype="defensive", period="2024H1",
                 weights={"CPI": 0.3, "RATE": 0.45, "PMI": 0.25},
                 knowledge_time="2024-06-30", decision_time="2024-08-01",
                 embargo_days=30, purge_days=5, model_hash="bt_h2")
    assert c2.version == 2
    # 과거 T(07-01)=아직 v1 활성(v2 반영 08-01 前) / 미래 T(09-01)=v2
    assert st.select(cid, "2024-07-01").version == 1, "07-01 = v1 (v2 미반영)"
    assert st.select(cid, "2024-09-01").version == 2, "09-01 = v2"
    print("4) re-fit: v2 추가해도 07-01 replay=v1 / 09-01=v2 (과거 불변) OK")

    # 5) ★hash-pin frozen: 동일 내용 재계산=동일 hash / 내용 변하면 변함
    h_same = compute_card_hash(cid, "risk_off", "defensive", "2024H1",
                               _canon_weights({"CPI": 0.4, "RATE": 0.35, "PMI": 0.25}),
                               1, _d("2024-03-31"), 30, 5, "bt_h1")
    assert h_same == c1.card_hash, "동일 내용 = 동일 hash (replay 재현)"
    h_diff = compute_card_hash(cid, "risk_off", "defensive", "2024H1",
                               _canon_weights({"CPI": 0.41, "RATE": 0.35, "PMI": 0.24}),
                               1, _d("2024-03-31"), 30, 5, "bt_h1")
    assert h_diff != c1.card_hash, "weight 변하면 hash 변함"
    print("5) hash-pin frozen: 동일내용=동일hash / weight 변경=hash 변경 OK")

    # 6) jsonl round-trip + watermark
    tmp = os.path.join(tempfile.gettempdir(), "weight_card_selftest.jsonl")
    if os.path.exists(tmp):
        os.remove(tmp)
    st2 = WeightCardStore(tmp)
    st2.emit(card_id="c|a|p", regime="r", archetype="a", period="p", weights={"x": 1.0},
             knowledge_time="2024-01-01", decision_time="2024-02-01", embargo_days=10)
    reloaded = WeightCardStore.load(tmp)
    sel2 = reloaded.select("c|a|p", "2024-03-01")
    assert sel2 is not None and sel2.card_hash == st2.history("c|a|p")[0].card_hash
    assert reloaded.watermark == 1
    print("6) jsonl round-trip: emit→load→select hash 동일 + watermark=1 OK")

    # 7) 미존재 scope select=None
    assert st.select("nonexistent|x|y", "2025-01-01") is None
    print("7) 미존재 card_id select=None OK")

    print("weight_card_store (WeightCard bitemporal 영속 + V(T) selector) self-test PASS")
