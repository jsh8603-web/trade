"""core/rules/consensus.py — 변경 트리거 + Proposer-Challenger-Arbiter (S9, D축).

findings D축 / claude R7 / gemini R7:
- 변경 트리거 = 잔차 drift(PSI+0근방 질량) → **재검토 큐(자동변경 X)**. 텍스트 토론으로
  상수를 바꾸지 않는다. **백테스트 OOS 개선 증명(promotion_gate G1~G4) 시에만**.
- ⚠️ **regime 먼저 판별 → 동일 regime 내 drift 만** (R7 무한루프 방지). regime 이 바뀐 거면
  그건 regime 전환이지 rule drift 가 아니다 → 재학습 대상 아님(regime_classifier 경로).
- 변경폭 cap(±1std 또는 ±20%) + hysteresis(최근 변경 후 쿨다운).
- 토너먼트 가지치기(연산 절감, gemini R4 역질문 답): T1 유사도 필터 → T2 빠른 t-stat
  → T3 full backtest top-5%. subagent rule seed 폭주를 단계적으로 좁힌다.

⛔ 기존 `core/consensus.py`(코인 primitive)와 별개. 이건 rule 거버넌스용(SPEC T3 산출물).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np


@dataclass
class ChangeRequest:
    signal_id: str
    current_version: str
    reason: str
    regime_id: int
    residual_psi: float


class ChangeQueue:
    """drift 트리거를 재검토 큐에 쌓기만. 자동 변경 금지(사람/게이트가 처리)."""
    def __init__(self):
        self._q: list[ChangeRequest] = []

    def enqueue(self, req: ChangeRequest) -> None:
        self._q.append(req)

    def pending(self) -> list[ChangeRequest]:
        return list(self._q)


def detect_change_trigger(
    signal_id: str,
    current_version: str,
    regime_now: int,
    regime_at_fit: int,
    residual_psi: float,
    psi_threshold: float = 0.25,
) -> Optional[ChangeRequest]:
    """동일 regime 내 잔차 drift 만 rule 재검토 트리거 (R7 무한루프 방지).

    regime_now ≠ regime_at_fit → None (regime 전환은 rule drift 아님, 별도 경로).
    """
    if regime_now != regime_at_fit:
        return None
    if residual_psi <= psi_threshold:
        return None
    return ChangeRequest(signal_id, current_version,
                         f"동일 regime({regime_now}) 내 잔차 drift PSI={residual_psi:.3f}",
                         regime_now, residual_psi)


def cap_change(old: float, proposed: float, std: float,
               max_std: float = 1.0, max_frac: float = 0.20) -> tuple[float, bool]:
    """변경폭 제한: ±1std 와 ±20% 중 더 좁은 쪽으로 clip. (capped_value, was_capped)."""
    lim_std = max_std * std
    lim_frac = abs(old) * max_frac
    lim = min(lim_std, lim_frac) if (std > 0 and old != 0) else max(lim_std, lim_frac)
    lo, hi = old - lim, old + lim
    capped = float(np.clip(proposed, lo, hi))
    return capped, (capped != proposed)


@dataclass
class Verdict:
    accepted: bool
    final_value: float
    reason: str


class ProposerChallengerArbiter:
    """제안→반박→판정. 상수 변경은 OOS 개선 증명(gate_fn) + cap 통과 시에만."""

    def __init__(self, gate_fn: Callable[[float], bool], hysteresis_quarters: int = 1):
        self.gate_fn = gate_fn        # proposed 값이 OOS 개선을 내는가(promotion_gate 위임)
        self.hysteresis = hysteresis_quarters
        self._last_change_q: dict[str, int] = {}

    def decide(self, signal_id: str, old: float, proposed: float, std: float,
               quarter: int) -> Verdict:
        # hysteresis: 최근 변경 후 쿨다운
        lastq = self._last_change_q.get(signal_id)
        if lastq is not None and quarter - lastq < self.hysteresis:
            return Verdict(False, old, f"hysteresis 쿨다운(최근변경 Q{lastq})")
        # Challenger: cap
        capped, was_capped = cap_change(old, proposed, std)
        # Arbiter: OOS 개선 게이트 (텍스트 토론 아님, 백테스트)
        if not self.gate_fn(capped):
            return Verdict(False, old, "OOS 개선 미입증 → 기각(텍스트 토론으론 변경 불가)")
        self._last_change_q[signal_id] = quarter
        note = "OOS 개선 입증" + (" +cap 적용" if was_capped else "")
        return Verdict(True, capped, note)


def tournament_prune(
    candidates: list[dict],
    t1_keep_frac: float = 0.5,
    t2_tstat_min: float = 2.0,
    t3_keep_frac: float = 0.05,
) -> list[dict]:
    """rule seed 폭주 → 단계적 가지치기 (연산 절감).

    각 candidate dict: {id, similarity(중복도 0~1), tstat, backtest_score}.
    T1 유사도 필터(중복 제거) → T2 빠른 t-stat → T3 full backtest top-frac.
    """
    if not candidates:
        return []
    # T1: 유사도 높은(중복) 것 제거 — 상위 (1-keep) 중복 컷
    by_sim = sorted(candidates, key=lambda c: c.get("similarity", 0.0))
    t1 = by_sim[: max(1, int(len(by_sim) * t1_keep_frac))] if len(by_sim) > 2 else by_sim
    # T2: 빠른 t-stat 컷
    t2 = [c for c in t1 if c.get("tstat", 0.0) >= t2_tstat_min]
    # T3: full backtest top-frac (비쌈 — 마지막에만)
    by_bt = sorted(t2, key=lambda c: c.get("backtest_score", 0.0), reverse=True)
    keep = max(1, int(len(by_bt) * t3_keep_frac)) if by_bt else 0
    return by_bt[:keep]


if __name__ == "__main__":
    # 1) regime 전환 → 트리거 안 함(R7)
    assert detect_change_trigger("s", "v1", regime_now=3, regime_at_fit=2, residual_psi=0.9) is None
    print("1) regime 전환 시 trigger 없음(무한루프 방지) OK")

    # 2) 동일 regime + drift → 재검토 큐
    req = detect_change_trigger("s", "v1", regime_now=2, regime_at_fit=2, residual_psi=0.4)
    assert req is not None
    q = ChangeQueue(); q.enqueue(req)
    print(f"2) 동일 regime drift → 큐 적재: {len(q.pending())}건 ({req.reason})")

    # 3) 변경폭 cap: old=-1.0, proposed=-3.0, std=0.5 → ±min(0.5, 0.2)=±0.2 → -1.2
    capped, was = cap_change(-1.0, -3.0, std=0.5)
    assert abs(capped - (-1.2)) < 1e-9 and was, (capped, was)
    print(f"3) cap: old=-1.0 proposed=-3.0 → {capped} (capped={was})")

    # 4) Proposer-Challenger-Arbiter: OOS 개선 입증 시만 + hysteresis
    pca = ProposerChallengerArbiter(gate_fn=lambda v: v <= -1.1, hysteresis_quarters=2)
    v1 = pca.decide("s", old=-1.0, proposed=-1.5, std=0.5, quarter=10)  # cap→-1.2, gate(-1.2<=-1.1) pass
    assert v1.accepted and abs(v1.final_value - (-1.2)) < 1e-9, v1
    print(f"4a) 수락: {v1.final_value} ({v1.reason})")
    v2 = pca.decide("s", old=-1.2, proposed=-1.5, std=0.5, quarter=11)  # hysteresis 쿨다운
    assert not v2.accepted, v2
    print(f"4b) hysteresis 기각: {v2.reason}")

    # 5) 토너먼트 가지치기
    cands = [{"id": f"c{i}", "similarity": i / 20, "tstat": 3.0 if i % 2 == 0 else 1.0,
              "backtest_score": (20 - i) / 20} for i in range(20)]
    top = tournament_prune(cands)
    assert len(top) >= 1 and all(c["tstat"] >= 2.0 for c in top), top
    print(f"5) 토너먼트: 20→{len(top)} (T1 유사도→T2 t-stat≥2→T3 top5%) winner={top[0]['id']}")

    print("S9 consensus self-test PASS")
