"""core/assume/bonus_channel.py — FHC bonus 사이징 채널 (S3).

설계 = .coord-fhc-contract-20260603.md §4 + .consult-judge-report-RESULTS.md C3/C4/C13(INV).
fhc.py(S1) 가 카드별 realized_bonus 를 산출 → 본 모듈이 자산별 집계 + 천장 clip + 안전 봉인.

★강화 (B)안 구현: w_final = clip(L1 + Σ bonus, 천장C). L1=보수 movable baseline, 확정카드 e-value
  만큼 L1 위로 강화 가능, 단 **risk_gate 독립산출 단일자산 천장 C 가 hard cap**(신규 파라미터 0).
  진짜 불변식 = capital-at-risk ≤ C(INV-1). L1 초과는 attenuation-only 의 의도적 relaxation(RESULTS C3).

★INV 집행:
  INV-1 hard cap : w_final ≤ C (C 는 bonus 독립·PIT-safe, 호출자=risk_gate 가 주입).
  INV-3 fail-closed: 천장 누락 / breaker / 카드 오류 → bonus 0, w → L1 이하(safe state 기본).
  INV-4 bounded : bonus ≥ 0, 카드별 ≤ bonus_cap(fhc.bonus_from_evalue 보장).
  INV-5 confirmed-only: confirmed/revived + mediator HOLDS 카드만 기여(fhc 가 0 반환).
  INV-8 recall=target-change: breaker → bonus target 0(즉시회수=target만, IOC ladder 실행은 호출자).
  INV-9 regime-primary breaker: breaker_tripped 주입(native RegimeGlasso transition, 외생 vol redundant).
  INV-11 off byte-identical: 호출처 0 = 자동 격리(go-live 시 소비). risk_gate 무수정(C 를 주입만 받음).

⛔ 본 모듈은 천장 C 를 **계산하지 않음**(risk_gate 소유). 주입만 받아 enforce. 결정론 무수정.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from core.assume.fhc import (
    FHCard, FHCState, FHCStateEnum, MediatorState, bonus_from_evalue,
)


@dataclass
class AssetSizing:
    """자산별 사이징 결과 + attribution(per-bar 진단)."""
    asset: str
    l1: float
    bonus: float
    final: float
    clipped: bool                # raw(L1+bonus)가 천장 C 에서 잘렸나
    n_cards: int                 # 기여 카드 수
    fail_closed: bool = False    # 천장 누락 / breaker → L1 fallback


def size_with_bonus(
    l1_weights: Dict[str, float],
    card_states: List[Tuple[FHCard, FHCState]],
    ceilings: Dict[str, float],
    *,
    breaker_tripped: bool = False,
) -> Dict[str, AssetSizing]:
    """자산별 w_final = clip(L1 + Σ realized_bonus, 천장 C). INV-1/3/4/5/8/9 집행.

    l1_weights : {asset: L1 보수 baseline weight}
    card_states: [(FHCard, FHCState)] — confirmed/revived + mediator HOLDS 카드만 bonus 기여(INV-5).
                 카드.targets(없으면 scope) 로 자산 매핑.
    ceilings   : {asset: C} — risk_gate 독립산출 단일자산 천장(bonus 무관·PIT-safe). 누락 → fail-closed.
    breaker_tripped: regime-primary breaker(INV-9) → 전 bonus target 0(INV-8 즉시회수).
    """
    bonus_by_asset: Dict[str, float] = {}
    cards_by_asset: Dict[str, int] = {}

    for card, st in card_states:
        if st.state not in (FHCStateEnum.CONFIRMED, FHCStateEnum.REVIVED):
            continue                                    # INV-5 confirmed-only
        if st.mediator_state != MediatorState.HOLDS:
            continue                                    # INV-5 mediator gate
        b = bonus_from_evalue(card, st)
        if b <= 0.0:
            continue
        targets = card.targets if card.targets else (card.scope,)
        for tgt in targets:
            bonus_by_asset[tgt] = bonus_by_asset.get(tgt, 0.0) + float(b)
            cards_by_asset[tgt] = cards_by_asset.get(tgt, 0) + 1

    out: Dict[str, AssetSizing] = {}
    for asset, l1 in l1_weights.items():
        C = ceilings.get(asset)
        n = cards_by_asset.get(asset, 0)

        # INV-3/8/9 fail-closed: breaker 발동 or 천장 미주입 → bonus 0, w=L1(천장 있으면 min)
        if breaker_tripped or C is None:
            safe = min(l1, C) if C is not None else l1
            out[asset] = AssetSizing(asset, l1, 0.0, safe, clipped=False,
                                     n_cards=n, fail_closed=True)
            continue

        bonus = max(0.0, bonus_by_asset.get(asset, 0.0))   # INV-4 bonus≥0
        raw = l1 + bonus
        final = min(raw, C)                                # INV-1 hard cap w≤C
        out[asset] = AssetSizing(asset, l1, bonus, final,
                                 clipped=(raw > C + 1e-12), n_cards=n)
    return out


# ===========================================================================
# self-test (verifier 대체 — INV 전 집행 검증)
# ===========================================================================
if __name__ == "__main__":
    from core.assume.fhc import MediatorSpec, OutcomeSpec, update_outcome, transition

    def _confirmed_card(asset: str, cap: float = 0.05):
        c = FHCard(
            card_id=f"fhc.{asset}", scope=asset, domain="macro", direction="long_tilt",
            statement="t", falsification_metric="f",
            mediator=MediatorSpec("x", op=">", threshold=0.0),
            outcome=OutcomeSpec("ts_rank_IC", "s"),
            bonus_cap=cap, confirm_e_threshold=20.0, targets=(asset,),
        )
        st = FHCState(c.card_id)
        for _ in range(60):
            update_outcome(st, 1.2, mediator_holds=True)
        transition(c, st, mediator_state=MediatorState.HOLDS)   # → confirmed, bonus 적립
        assert st.state == FHCStateEnum.CONFIRMED
        return c, st

    # 1) ★(B) 강화: L1 위로 bonus, 천장 C 미만 → final = L1 + bonus
    c, st = _confirmed_card("BTC", cap=0.05)
    r = size_with_bonus({"BTC": 0.10}, [(c, st)], {"BTC": 0.30})
    a = r["BTC"]
    assert a.bonus > 0 and abs(a.final - (a.l1 + a.bonus)) < 1e-9 and not a.clipped, a
    assert a.final > a.l1, "강화 실패(L1 초과 안 됨)"
    print(f"1) (B) 강화 OK: L1={a.l1} +bonus={a.bonus:.4f} → final={a.final:.4f} (천장0.30 미만)")

    # 2) ★INV-1 hard cap: L1+bonus 가 천장 초과 → C 에서 clip
    r2 = size_with_bonus({"BTC": 0.10}, [(c, st)], {"BTC": 0.105})
    a2 = r2["BTC"]
    assert abs(a2.final - 0.105) < 1e-9 and a2.clipped, a2
    print(f"2) INV-1 hard cap OK: raw={a2.l1 + a2.bonus:.4f} → clip C=0.105 (clipped={a2.clipped})")

    # 3) ★INV-9 breaker: 발동 → bonus 0, w=L1
    r3 = size_with_bonus({"BTC": 0.10}, [(c, st)], {"BTC": 0.30}, breaker_tripped=True)
    a3 = r3["BTC"]
    assert a3.bonus == 0.0 and a3.final == 0.10 and a3.fail_closed, a3
    print(f"3) INV-9 breaker OK: bonus=0 final={a3.final} fail_closed={a3.fail_closed}")

    # 4) ★INV-3 fail-closed: 천장 미주입 → L1 fallback
    r4 = size_with_bonus({"BTC": 0.10}, [(c, st)], {})
    a4 = r4["BTC"]
    assert a4.bonus == 0.0 and a4.final == 0.10 and a4.fail_closed, a4
    print(f"4) INV-3 fail-closed(천장 누락) OK: final={a4.final} fail_closed={a4.fail_closed}")

    # 5) ★INV-5: confirmed 아닌 카드(minted) → 기여 0
    c5 = FHCard(card_id="fhc.minted", scope="ETH", domain="crypto", direction="long_tilt",
                statement="t", falsification_metric="f",
                mediator=MediatorSpec("x"), outcome=OutcomeSpec(), bonus_cap=0.05, targets=("ETH",))
    st5 = FHCState(c5.card_id)                              # minted, e=1
    r5 = size_with_bonus({"ETH": 0.10}, [(c5, st5)], {"ETH": 0.30})
    assert r5["ETH"].bonus == 0.0 and r5["ETH"].n_cards == 0, r5["ETH"]
    print("5) INV-5 confirmed-only OK: minted 카드 기여 0")

    # 6) ★INV-5: confirmed 라도 mediator HOLDS 아니면 기여 0
    st.mediator_state = MediatorState.FAILS
    r6 = size_with_bonus({"BTC": 0.10}, [(c, st)], {"BTC": 0.30})
    assert r6["BTC"].bonus == 0.0, r6["BTC"]
    st.mediator_state = MediatorState.HOLDS                 # 복원
    print("6) INV-5 mediator gate OK: confirmed+fails → 기여 0")

    # 7) 다중 카드 같은 자산 → bonus 합산(천장 내)
    c7, st7 = _confirmed_card("BTC", cap=0.03)
    r7 = size_with_bonus({"BTC": 0.10}, [(c, st), (c7, st7)], {"BTC": 0.50})
    assert r7["BTC"].n_cards == 2 and r7["BTC"].bonus > a.bonus, r7["BTC"]
    print(f"7) 다중카드 합산 OK: n=2 bonus={r7['BTC'].bonus:.4f} (단일 {a.bonus:.4f} 초과)")

    print("\nbonus_channel self-test PASS (B 강화 · INV-1 cap · INV-9 breaker · INV-3 fail-closed · "
          "INV-5 confirmed-only/mediator-gate · 다중카드 합산)")
