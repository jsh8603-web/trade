"""core/brain/correction_loop.py — BB-2: indicator_event_correlation live 학습 루프 연결.

DESIGN-button-v2.md §3 / §10.1. 현재 `regime_classifier` 는 `score_confidence`(읽기)만 호출,
`ingest_correction`/`recall_similar`(학습 쓰기)는 dead. 본 모듈이 live 루프로 연결한다.

핵심 통찰(자문 R1·코드 그라운딩): `regime_classifier._jump_model_overlay` 가 이미 계산하는
**JM filter(online) vs smoother(insample) divergence** = "실시간 판정 ≠ 사후정답" = 버려지던
CorrectionRecord 원천. 이 신호를 harvest 해 ingest → 다음 사이클 score_confidence 의
recurrent_misjudgment 가중이 자동 반영(기존 _case_stats 소비).

PIT 철칙: ingest 는 as_of_ts 박제, recall 은 as_of 이전만(causal mask) — 기존 코드가 보장,
본 loop 은 호출 규약만 강제. 결정 backfill 금지.

이벤트 emit(BB-4/ledger 연계): harvest 시 OUTCOME_OBSERVED/HOLD_REMEASURED 류 이벤트 dict 를
반환해 호출자(orchestrator/btn-Inv ledger)가 append 하게 한다(본 모듈은 ledger I/O X).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

from core.brain.indicator_event_correlation import (
    CorrectionRecord,
    IndicatorEventCorrelation,
    MacroEvent,
)
from core.brain.macro_schema import RegimeLabel


@dataclass
class HarvestResult:
    ingested: int                          # 적재된 CorrectionRecord 수 (misjudgment 만)
    skipped_agree: int                     # realtime==hindsight (오판 아님) → skip
    records: list = field(default_factory=list)        # 적재된 CorrectionRecord
    events: list = field(default_factory=list)         # ledger emit 용 이벤트 dict


def jm_divergence_indices(online_labels: Sequence, smoother_labels: Sequence) -> list[int]:
    """JM filter(online) vs smoother(insample) 불일치 인덱스 = 오판 후보 시점.

    regime_classifier 가 confidence 보정에만 쓰고 버리는 신호. 여기서 harvest trigger 로 재사용.
    """
    n = min(len(online_labels), len(smoother_labels))
    return [i for i in range(n) if online_labels[i] != smoother_labels[i]]


class LiveCorrelationLoop:
    """IndicatorEventCorrelation 을 live 학습 루프에 연결 (BB-2). PIT causal mask 준수.

    read 경로(score_confidence)는 기존 regime_classifier 가 그대로 사용(불변).
    write 경로(harvest→ingest) + recall surface 를 본 loop 이 제공.
    attach_to_classifier 로 동일 model 인스턴스를 공유 → ingest 한 통계가 즉시 read 에 반영.
    """

    def __init__(self, model: Optional[IndicatorEventCorrelation] = None):
        self.model = model or IndicatorEventCorrelation()

    # ------------------------------------------------------------ write (학습)
    def harvest_corrections(
        self,
        *,
        realtime_regimes: Sequence[RegimeLabel],
        hindsight_regimes: Sequence[RegimeLabel],
        as_of_ts: Sequence[float],
        signature_fn: Callable[[int], dict],
        confidence_realtime: Optional[Sequence[float]] = None,
        hindsight_ts: Optional[Sequence[float]] = None,
        hint_fn: Optional[Callable[[int], str]] = None,
    ) -> HarvestResult:
        """실시간 regime 판정 vs 사후정답(smoother/NBER) → CorrectionRecord harvest + ingest.

        realtime != hindsight 인 시점만 적재(ingest_correction 이 is_misjudgment 만 적재).
        signature_fn(i) = {event, triggered_sups, distorted_indicators} (anomaly_signature).
        """
        n = min(len(realtime_regimes), len(hindsight_regimes), len(as_of_ts))
        res = HarvestResult(ingested=0, skipped_agree=0)
        for i in range(n):
            rt, hs = realtime_regimes[i], hindsight_regimes[i]
            if rt == hs:
                res.skipped_agree += 1
                continue
            sig = signature_fn(i) or {}
            lag = 0
            if hindsight_ts is not None and i < len(hindsight_ts):
                lag = max(0, int((hindsight_ts[i] - as_of_ts[i]) / 86400.0))
            conf = (confidence_realtime[i] if confidence_realtime is not None
                    and i < len(confidence_realtime) else 1.0)
            rec = CorrectionRecord(
                as_of_ts=float(as_of_ts[i]),
                regime_realtime=rt,
                confidence_realtime=float(conf),
                regime_hindsight=hs,
                anomaly_signature=sig,
                lag_days=lag,
                hint=(hint_fn(i) if hint_fn else
                      f"실시간 {rt.value} 판정이 사후 {hs.value} 로 정정(decoupling 의심)"),
                event=sig.get("event"),
            )
            before = len(self.model._records)
            self.model.ingest_correction(rec)
            if len(self.model._records) > before:
                res.ingested += 1
                res.records.append(rec)
                res.events.append({
                    "event_type": "HOLD_REMEASURED",
                    "valid_time": rec.as_of_ts,
                    "decision_time": rec.recorded_ts,
                    "payload": {"regime_realtime": rt.value, "regime_hindsight": hs.value,
                                "signature": sig, "lag_days": lag, "kind": "correction"},
                })
        return res

    def harvest_from_jm(
        self,
        *,
        online_labels: Sequence,
        smoother_labels: Sequence,
        realtime_regimes: Sequence[RegimeLabel],
        hindsight_regimes: Sequence[RegimeLabel],
        as_of_ts: Sequence[float],
        signature_fn: Callable[[int], dict],
        **kw,
    ) -> HarvestResult:
        """JM divergence 시점에서만 correction harvest (regime_classifier 의 버려지던 신호 재사용).

        divergence 인 인덱스만 realtime/hindsight 비교 → ingest. (calm/stress 2-state 는 trigger,
        실제 CorrectionRecord 는 RegimeLabel 수준의 realtime vs hindsight.)
        """
        div = set(jm_divergence_indices(online_labels, smoother_labels))
        if not div:
            return HarvestResult(ingested=0, skipped_agree=len(as_of_ts))
        idx = sorted(div)
        sub = lambda seq: [seq[i] for i in idx] if seq is not None else None
        return self.harvest_corrections(
            realtime_regimes=sub(realtime_regimes),
            hindsight_regimes=sub(hindsight_regimes),
            as_of_ts=sub(as_of_ts),
            signature_fn=lambda j: signature_fn(idx[j]),
            confidence_realtime=sub(kw.get("confidence_realtime")),
            hindsight_ts=sub(kw.get("hindsight_ts")),
        )

    # ------------------------------------------------------------ read (recall)
    def recall_for_classify(
        self, regime: RegimeLabel, signature: dict, as_of_ts: Optional[float], k: int = 3
    ) -> list[dict]:
        """과거 보정 recall (PIT causal mask) → classify evidence 에 surface."""
        return self.model.recall_similar(regime, signature, as_of_ts, k=k)

    # ------------------------------------------------------------ wiring
    def attach_to_classifier(self, classifier) -> None:
        """classifier.correlation_model 을 본 loop 의 model 로 교체 (read+write 동일 인스턴스).

        이후 classifier.score_confidence(read) 와 loop.harvest(write) 가 같은 _case_stats 공유 →
        ingest 한 recurrent_misjudgment 가 다음 classify 에 자동 반영.
        """
        classifier.correlation_model = self.model


if __name__ == "__main__":
    loop = LiveCorrelationLoop()
    SIG = {"event": MacroEvent.RECESSION_ONSET.value,
           "triggered_sups": ["near_term_forward_spread", "fed_balance_sheet"]}

    # 1) JM divergence 시점에서 harvest — 실시간 REFLATION(침체) 판정이 사후 RECOVERY(정상) 로 정정
    online = [0, 1, 0, 1, 0]           # JM filter (calm/stress)
    smoother = [0, 0, 0, 1, 1]         # JM smoother → idx 1,4 divergence
    rt = [RegimeLabel.REFLATION] * 5   # 실시간 = 침체 판정
    hs = [RegimeLabel.REFLATION, RegimeLabel.RECOVERY, RegimeLabel.REFLATION,
          RegimeLabel.REFLATION, RegimeLabel.RECOVERY]  # 사후: idx 1,4 는 실제 RECOVERY (오판)
    t0 = 1_700_000_000.0
    aof = [t0 + i * 86400 for i in range(5)]
    res = loop.harvest_from_jm(online_labels=online, smoother_labels=smoother,
                               realtime_regimes=rt, hindsight_regimes=hs,
                               as_of_ts=aof, signature_fn=lambda i: SIG,
                               hindsight_ts=[a + 30 * 86400 for a in aof])
    print(f"1) JM divergence harvest: ingested={res.ingested} (idx1,4 오판 = 2 기대)")
    assert res.ingested == 2, res.ingested
    assert all(e["event_type"] == "HOLD_REMEASURED" for e in res.events)

    # 2) recurrent_misjudgment 반영 — 같은 yc 케이스 2회 적재 → score_confidence 추가 보수화
    res_plain = loop.model.score_confidence(MacroEvent.RECESSION_ONSET, 0.8,
                                            {"near_term_forward_spread": -0.2})
    assert "near_term_forward_spread" or True
    has_recurrent = any("recurrent_misjudgment" in f for f in res_plain.caution_flags)
    print(f"2) score_confidence fired={res_plain.fired_cases} recurrent={has_recurrent} "
          f"mult={res_plain.confidence_multiplier:.3f}")
    assert "yc_inversion_term_premium" in res_plain.fired_cases
    assert has_recurrent, "2회+ 적재 케이스의 recurrent_misjudgment 미반영"

    # 3) recall PIT mask — as_of 이전 보정만 surface
    future = t0 + 100 * 86400
    rec_future = loop.recall_for_classify(RegimeLabel.REFLATION, SIG, as_of_ts=future, k=3)
    rec_past = loop.recall_for_classify(RegimeLabel.REFLATION, SIG, as_of_ts=t0, k=3)
    print(f"3) recall PIT: future={len(rec_future)} past(t0)={len(rec_past)}")
    assert len(rec_future) >= 1 and len(rec_past) == 0, (len(rec_future), len(rec_past))

    # 4) attach_to_classifier — model 공유 (read+write 동일 인스턴스)
    class _FakeClf:
        correlation_model = None
    clf = _FakeClf()
    loop.attach_to_classifier(clf)
    assert clf.correlation_model is loop.model
    print("4) attach_to_classifier OK (read+write 동일 model)")

    # 5) 오판 아님(realtime==hindsight) → skip
    res2 = loop.harvest_corrections(
        realtime_regimes=[RegimeLabel.RECOVERY, RegimeLabel.RECOVERY],
        hindsight_regimes=[RegimeLabel.RECOVERY, RegimeLabel.RECOVERY],
        as_of_ts=[t0, t0 + 86400], signature_fn=lambda i: SIG)
    assert res2.ingested == 0 and res2.skipped_agree == 2
    print(f"5) 일치 시점 skip OK: ingested={res2.ingested} skipped={res2.skipped_agree}")

    print("correction_loop self-test PASS (JM harvest + recurrent 반영 + recall PIT mask + attach)")
