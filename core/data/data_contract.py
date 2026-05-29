"""core/data/data_contract.py — Pandera 데이터 계약 게이트 (IA-2, R11 substrate).

자문 수렴(gemini+claude): **계약 위반(스키마/범위/PIT 단조성/staleness) = 측정 incident**
이지 "가정이 틀림"이 아니다. 이 게이트는 가정 validator **앞단**에 서서, 위반 시 검증을
중단시키고 incident 를 보고한다(→ ledger 가 DATA_CONTRACT_VIOLATION emit + HOLD_SUSPENDED:
FDR 스트림 제외 + alpha 소진 중단 + 사람 확인 후 재개).

PENDING(미실현 outcome) 과 incident(계약 위반) 은 **절대 섞지 않는다** — 전자는 정상,
후자는 데이터 무결성 사고. 이 분리가 IA-2 의 핵심.

claude R3: `max_staleness` 는 **per-series cadence-aware** (글로벌 N일 상수면 주간 macro 가
false-incident). 각 도메인 series 의 발표 주기 기준으로 stale 판정.

신규 의존 = Pandera(0.31, `pandera.pandas`). 산출 ContractResult 는 ledger event payload 로 직행.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Callable, Iterable, Optional, Union

import pandas as pd

import pandera.pandas as pa
from pandera.pandas import Check, Column, DataFrameSchema

CONTRACT_SCHEMA_VERSION = "dc_v1"

# 도메인별 멀티플/지표 범위 (현실적 상한 — 초과 = 측정 오류 의심)
_RANGES = {
    "equity":    {"per": (0, 300), "pbr": (0, 100), "ev_ebitda": (0, 200), "ps": (0, 100)},
    "etf":       {"nav_premium": (-0.30, 0.30), "ps": (0, 100)},
    "commodity": {"roll_yield": (-2.0, 2.0), "carry": (-2.0, 2.0)},
    "crypto":    {"mvrv": (0, 20), "sopr": (0, 10)},
    "macro":     {},  # 거시 지표는 series 별로 다양 → 범위 Check 생략, PIT/staleness 만
}

# 도메인별 series 발표 주기(일) → max_staleness = cadence × 배수
_CADENCE_DAYS = {
    "equity": 100,      # 분기 공시(~90일) + 여유
    "etf": 5,           # 일간 NAV
    "commodity": 10,    # 주간 재고/COT
    "crypto": 2,        # 일간 on-chain
    "macro": 45,        # 월간 지표 + vintage lag
}
_STALENESS_MULT = 1.5


@dataclass
class ContractResult:
    """게이트 산출. ledger DATA_CONTRACT_VIOLATION payload + HOLD_SUSPENDED 트리거."""
    passed: bool
    domain: str
    as_of: datetime
    incidents: list[dict] = field(default_factory=list)   # {check, column, n_failed, sample}
    schema_version: str = CONTRACT_SCHEMA_VERSION

    @property
    def n_incidents(self) -> int:
        return len(self.incidents)


def _pit_checks() -> list[Check]:
    """bitemporal PIT 단조성 불변식 (전 도메인 공통)."""
    return [
        Check(lambda df: (df["sys_time"] >= df["knowable_from"]).all(),
              name="sys_time>=knowable_from", error="sys_time_before_knowable"),
        Check(lambda df: (df["knowable_from"] >= df["effective_from"]).all(),
              name="knowable_from>=effective_from", error="knowable_before_effective"),
    ]


def _build_schema(domain: str) -> DataFrameSchema:
    cols: dict[str, Column] = {
        "effective_from": Column("datetime64[ns]", nullable=False),
        "knowable_from": Column("datetime64[ns]", nullable=False),
        "sys_time": Column("datetime64[ns]", nullable=False),
    }
    for metric, (lo, hi) in _RANGES.get(domain, {}).items():
        cols[metric] = Column(float, Check.in_range(lo, hi), nullable=True, required=False)
    return DataFrameSchema(cols, checks=_pit_checks(), strict=False, coerce=False)


def _staleness_incident(panel: pd.DataFrame, as_of: datetime, domain: str) -> Optional[dict]:
    """consumer(as_of) 기준 최신 knowable_from 이 cadence×mult 보다 오래되면 stale incident."""
    if "knowable_from" not in panel.columns or panel.empty:
        return None
    kf = pd.to_datetime(panel["knowable_from"])
    latest = kf[kf <= pd.Timestamp(as_of)].max()
    if pd.isna(latest):
        return {"check": "max_staleness", "column": "knowable_from",
                "n_failed": len(panel), "sample": "as_of 이전 관측 0건"}
    cadence = _CADENCE_DAYS.get(domain, 30)
    age_days = (pd.Timestamp(as_of) - latest).days
    if age_days > cadence * _STALENESS_MULT:
        return {"check": "max_staleness", "column": "knowable_from", "n_failed": 1,
                "sample": f"최신 {latest.date()} = {age_days}일 경과 > {cadence}×{_STALENESS_MULT}"}
    return None


def check_contract(panel: pd.DataFrame, as_of: datetime, domain: str) -> ContractResult:
    """데이터 계약 게이트. passed=False 면 가정검증 중단 + 측정 incident 보고(가정틀림 아님)."""
    res = ContractResult(passed=True, domain=domain, as_of=as_of)
    schema = _build_schema(domain)
    try:
        schema.validate(panel, lazy=True)
    except pa.errors.SchemaErrors as e:
        fc = e.failure_cases
        for chk, grp in fc.groupby("check"):
            res.incidents.append({
                "check": str(chk),
                "column": str(grp["column"].iloc[0]) if "column" in grp else None,
                "n_failed": int(len(grp)),
                "sample": str(grp["failure_case"].iloc[0]) if "failure_case" in grp else None,
            })
    stale = _staleness_incident(panel, as_of, domain)
    if stale:
        res.incidents.append(stale)
    res.passed = (res.n_incidents == 0)
    return res


# ---------------------------------------------------------------------------
# ★ ingestion checksum — 외부 벤더 silent historical rewrite 탐지 (전체구조 자문 #2)
# ---------------------------------------------------------------------------
# 벤더가 REVISION 통지 없이 과거를 덮어쓰면 PIT 형식(knowable/sys_time)은 멀쩡해
# check_contract 가 못 잡는다(스키마·범위·단조성 다 통과). → 이전에 본 (series, vt) 값의
# content fingerprint 를 보관하고 재적재 시 대조. **이미 알던 과거 값이 통지 없이 변함** =
# silent_rewrite incident → DATA_CONTRACT_VIOLATION. 정상 정정은 REVISION_OBSERVED event
# 가 동반(known_revision)되므로 구분된다.

_RewriteSrc = Union[str, date, datetime]


def _iso(x: _RewriteSrc) -> str:
    """실제 타임스탬프(as_of) 정규화. 날짜형만."""
    if isinstance(x, datetime):
        return x.replace(tzinfo=None).isoformat() if x.tzinfo else x.isoformat()
    if isinstance(x, date):
        return datetime(x.year, x.month, x.day).isoformat()
    return datetime.fromisoformat(str(x)).isoformat()


def _period_key(x: _RewriteSrc) -> str:
    """vt 기간 키 정규화. 분기/월 라벨('2024-Q1','2024-03') 도 허용 — 파싱 가능하면 ISO, 아니면 원문."""
    if isinstance(x, (date, datetime)):
        return _iso(x)
    try:
        return datetime.fromisoformat(str(x)).isoformat()
    except ValueError:
        return str(x)


def _value_hash(value: float) -> str:
    """값 지문(부동소수 표기 흔들림 방어 위해 10자리 반올림 후 해시)."""
    return hashlib.sha256(repr(round(float(value), 10)).encode("utf-8")).hexdigest()[:16]


@dataclass
class FingerprintStore:
    """(series_key, vt) → 마지막 관측 값 지문 + 기록 as_of. silent rewrite 대조 SSOT."""
    _fp: dict = field(default_factory=dict)   # (series_key, vt_iso) -> (value_hash, recorded_as_of_iso)

    def record(self, series_key: str, vt: _RewriteSrc, value: float, as_of: _RewriteSrc) -> None:
        """관측 값 지문 기록/갱신(정상 ingestion 후 호출)."""
        self._fp[(series_key, _period_key(vt))] = (_value_hash(value), _period_key(as_of))

    def check(
        self, series_key: str, vt: _RewriteSrc, value: float, *, has_revision: bool = False
    ) -> Optional[dict]:
        """이전 지문과 다른 값인데 REVISION 미동반이면 silent_rewrite incident, 아니면 None.

        최초 관측(이전 지문 없음)·동일 값·정상 REVISION 동반 = incident 아님.
        """
        prev = self._fp.get((series_key, _period_key(vt)))
        if prev is None:
            return None                       # 최초 관측 = rewrite 아님
        prev_hash, prev_as_of = prev
        if _value_hash(value) == prev_hash:
            return None                       # 동일 = 정상
        if has_revision:
            return None                       # REVISION_OBSERVED 동반 = 합법 정정
        return {
            "check": "silent_rewrite", "column": series_key, "n_failed": 1,
            "sample": (f"{series_key}@{_period_key(vt)}: 이미 알던 과거값이 통지 없이 변경"
                       f"(이전기록 as_of={prev_as_of})"),
        }


def scan_for_silent_rewrite(
    store: FingerprintStore,
    rows: Iterable[tuple],           # (series_key, vt, value) 또는 (series_key, vt, value, has_revision)
    *,
    as_of: Optional[_RewriteSrc] = None,
    record_after: bool = True,
) -> list[dict]:
    """rows 일괄 대조 → silent_rewrite incident 목록. record_after=True 면 대조 후 지문 갱신.

    as_of = 이번 ingestion 시점(지문 기록용). DATA_CONTRACT_VIOLATION emit 은 ingestion
    호출부(P3)가 담당 — 이 함수는 incident 만 산출.
    """
    incidents: list[dict] = []
    stamp = as_of if as_of is not None else "ingest"
    for row in rows:
        series_key, vt, value = row[0], row[1], row[2]
        has_rev = bool(row[3]) if len(row) > 3 else False
        inc = store.check(series_key, vt, value, has_revision=has_rev)
        if inc:
            incidents.append(inc)
        if record_after:
            store.record(series_key, vt, value, as_of=stamp)
    return incidents


# ---------------------------------------------------------------------------
# ★ WeightCard 스키마 게이트 (R15 §4 btn-Inv — 가중카드 데이터 무결성)
# ---------------------------------------------------------------------------
# 가중카드(WeightAssumptionCard)의 *데이터 무결성*만 검증한다 — 비중 도출의 *타당성*
# (Ω·IC 결합·shrinkage 등)은 btn-Codlearn validator 소관. 여기는: scope 키 존재 ·
# weight finite/비영/cap · PIT 단조(knowledge_time≤decision_time) · embargo 재확인 ·
# (옵션)hash 무결성. card 는 duck-typed(WeightCardRecord 호환) — weight_card_store 역의존
# 회피 위해 hash 재계산은 recompute_hash 콜백 주입(기본 None=skip).

WEIGHT_CARD_SCHEMA_VERSION = "wc_v1"


def check_weight_card(
    card, *, max_weight_abs: float = 1.0,
    recompute_hash: Optional[Callable[[object], str]] = None,
) -> ContractResult:
    """가중카드 데이터 무결성 게이트 → ContractResult(domain='weight_card').

    incident != 0 = 측정/영속 무결성 사고(가정 틀림 아님 — IA-2 원칙 동일). card 속성:
    regime/archetype/period/weights(((k,v),...))/knowledge_time/decision_time/embargo_days
    /card_hash. recompute_hash(card)→str 주입 시 영속 hash 변조 탐지.
    """
    inc: list[dict] = []
    kt = getattr(card, "knowledge_time", None)
    dt0 = getattr(card, "decision_time", None)

    for k in ("regime", "archetype", "period"):
        if not getattr(card, k, ""):
            inc.append({"check": "scope_key_missing", "column": k, "n_failed": 1,
                        "sample": f"scope 키 '{k}' 비어있음"})

    weights = list(getattr(card, "weights", []) or [])
    vals = [float(v) for _, v in weights] if weights else []
    if not vals:
        inc.append({"check": "weights_empty", "column": "weights", "n_failed": 1,
                    "sample": "weight 0개"})
    else:
        if any(not math.isfinite(v) for v in vals):
            inc.append({"check": "weight_nan_inf", "column": "weights",
                        "n_failed": sum(1 for v in vals if not math.isfinite(v)),
                        "sample": "weight 에 NaN/inf"})
        if all(v == 0 for v in vals):
            inc.append({"check": "weights_all_zero", "column": "weights",
                        "n_failed": len(vals), "sample": "전 weight=0(degenerate)"})
        over = [v for v in vals if math.isfinite(v) and abs(v) > max_weight_abs]
        if over:
            inc.append({"check": "weight_cap", "column": "weights", "n_failed": len(over),
                        "sample": f"|w| 최대 {max(abs(v) for v in over):.4f} > cap {max_weight_abs}"})

    if kt is not None and dt0 is not None and dt0 < kt:
        inc.append({"check": "weight_pit_monotonic", "column": "decision_time", "n_failed": 1,
                    "sample": f"decision_time({dt0}) < knowledge_time({kt}) = 미래학습"})

    emb = getattr(card, "embargo_days", None)
    if kt is not None and dt0 is not None and emb is not None and (dt0 - kt).days < emb:
        inc.append({"check": "weight_embargo", "column": "decision_time", "n_failed": 1,
                    "sample": f"embargo gap {(dt0 - kt).days}일 < {emb}일"})

    if recompute_hash is not None:
        h = recompute_hash(card)
        if h != getattr(card, "card_hash", None):
            inc.append({"check": "weight_hash_mismatch", "column": "card_hash", "n_failed": 1,
                        "sample": "card_hash 재계산 불일치(영속 변조 의심)"})

    as_of = dt0 if isinstance(dt0, (date, datetime)) else datetime(1970, 1, 1)
    return ContractResult(passed=(len(inc) == 0), domain="weight_card",
                          as_of=as_of, incidents=inc,
                          schema_version=WEIGHT_CARD_SCHEMA_VERSION)


if __name__ == "__main__":
    base = {
        "effective_from": pd.to_datetime(["2024-01-01", "2024-04-01"]),
        "knowable_from": pd.to_datetime(["2024-02-15", "2024-05-15"]),
        "sys_time": pd.to_datetime(["2024-02-15", "2024-05-15"]),
        "per": [12.0, 18.0],
    }
    AS_OF = datetime(2024, 6, 1)

    # 1) clean equity panel → passed
    r = check_contract(pd.DataFrame(base), AS_OF, "equity")
    assert r.passed and r.n_incidents == 0, r.incidents
    print(f"1) clean equity: passed={r.passed} incidents={r.n_incidents}")

    # 2) 범위 위반(per=999) → incident, passed=False (측정 incident, 가정틀림 아님)
    bad = dict(base); bad["per"] = [12.0, 999.0]
    r = check_contract(pd.DataFrame(bad), AS_OF, "equity")
    assert not r.passed and any(i["check"].startswith("in_range") for i in r.incidents), r.incidents
    print(f"2) per=999 범위위반: passed={r.passed} incidents={[i['check'] for i in r.incidents]}")

    # 3) PIT 단조성 위반(sys_time < knowable_from) → incident
    bad2 = dict(base); bad2["sys_time"] = pd.to_datetime(["2024-01-01", "2024-05-15"])
    r = check_contract(pd.DataFrame(bad2), AS_OF, "equity")
    assert not r.passed and any("sys_time" in i["check"] for i in r.incidents), r.incidents
    print(f"3) sys_time<knowable_from PIT 위반: passed={r.passed} checks={[i['check'] for i in r.incidents]}")

    # 4) staleness: equity cadence 100×1.5=150일, 최신 knowable 2024-05-15 → as_of 2025-06-01(>150일) stale
    r = check_contract(pd.DataFrame(base), datetime(2025, 6, 1), "equity")
    assert not r.passed and any(i["check"] == "max_staleness" for i in r.incidents), r.incidents
    print(f"4) staleness incident: passed={r.passed} sample={[i['sample'] for i in r.incidents if i['check']=='max_staleness']}")

    # 5) crypto 도메인 mvrv 범위 (clean)
    cr = pd.DataFrame({
        "effective_from": pd.to_datetime(["2024-05-30"]),
        "knowable_from": pd.to_datetime(["2024-05-31"]),
        "sys_time": pd.to_datetime(["2024-05-31"]),
        "mvrv": [2.3],
    })
    r = check_contract(cr, AS_OF, "crypto")
    assert r.passed, r.incidents
    print(f"5) clean crypto(mvrv=2.3): passed={r.passed}")

    # 6) ★ingestion checksum: 최초 관측 = incident 아님 / 동일 재적재 = 아님
    store = FingerprintStore()
    assert store.check("CPI", "2024-01-31", 2.0) is None, "최초 관측"
    store.record("CPI", "2024-01-31", 2.0, as_of="2024-02-15")
    assert store.check("CPI", "2024-01-31", 2.0) is None, "동일 값 재적재"
    print("6) checksum: 최초 관측·동일 재적재 = incident 없음 OK")

    # 7) ★silent rewrite: 통지 없는 과거값 변경 = incident / REVISION 동반 = 정상
    inc = store.check("CPI", "2024-01-31", 2.5, has_revision=False)
    assert inc is not None and inc["check"] == "silent_rewrite", inc
    ok = store.check("CPI", "2024-01-31", 2.5, has_revision=True)
    assert ok is None, "REVISION 동반은 합법 정정"
    print(f"7) silent rewrite: 통지없는 변경=incident({inc['check']}) / REVISION 동반=정상 OK")

    # 8) scan_for_silent_rewrite 일괄: 신규·정상·silent·revision 혼합
    st2 = FingerprintStore()
    st2.record("GDP", "2024-Q1", 3.0, as_of="2024-04-30")
    st2.record("PMI", "2024-03", 51.0, as_of="2024-04-01")
    rows = [
        ("GDP", "2024-Q1", 3.0),               # 동일 = 정상
        ("PMI", "2024-03", 49.0),              # silent rewrite (통지 없음)
        ("CPI", "2024-02", 2.1),               # 신규 = 정상
        ("GDP", "2024-Q1", 3.2, True),         # 변경이나 REVISION 동반 = 정상
    ]
    incs = scan_for_silent_rewrite(st2, rows)
    assert len(incs) == 1 and incs[0]["column"] == "PMI", incs
    print(f"8) scan 일괄: silent rewrite 1건(PMI)만 탐지({len(incs)}건) OK")

    # 9) ★WeightCard 스키마 게이트 (R15) — duck-typed card
    from types import SimpleNamespace
    good = SimpleNamespace(regime="risk_off", archetype="defensive", period="2024H1",
                           weights=(("CPI", 0.4), ("RATE", 0.35), ("PMI", 0.25)),
                           knowledge_time=date(2024, 3, 31), decision_time=date(2024, 5, 1),
                           embargo_days=30, card_hash="h1")
    r = check_weight_card(good, max_weight_abs=1.0)
    assert r.passed and r.domain == "weight_card" and r.schema_version == "wc_v1", r.incidents
    print(f"9) WeightCard clean: passed={r.passed} schema={r.schema_version}")

    # 10) scope 키 누락 + weight cap 초과 + PIT 역전 동시
    bad = SimpleNamespace(regime="", archetype="x", period="p",
                          weights=(("A", 1.5), ("B", 0.2)),
                          knowledge_time=date(2024, 5, 1), decision_time=date(2024, 3, 1),
                          embargo_days=30, card_hash="h")
    r = check_weight_card(bad, max_weight_abs=1.0)
    checks = {i["check"] for i in r.incidents}
    assert not r.passed and {"scope_key_missing", "weight_cap", "weight_pit_monotonic",
                             "weight_embargo"} <= checks, checks
    print(f"10) WeightCard 위반 다중: {sorted(checks)} 탐지 OK")

    # 11) NaN weight + 전영 + hash 변조
    nan_card = SimpleNamespace(regime="r", archetype="a", period="p",
                               weights=(("A", float("nan")),),
                               knowledge_time=date(2024, 1, 1), decision_time=date(2024, 2, 1),
                               embargo_days=10, card_hash="stored")
    r = check_weight_card(nan_card, recompute_hash=lambda c: "recomputed_differs")
    checks = {i["check"] for i in r.incidents}
    assert "weight_nan_inf" in checks and "weight_hash_mismatch" in checks, checks
    print(f"11) WeightCard NaN+hash 변조: {sorted(checks)} 탐지 OK")

    print("data_contract (Pandera 게이트 + ingestion checksum + WeightCard) self-test PASS")
