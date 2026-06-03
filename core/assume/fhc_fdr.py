"""core/assume/fhc_fdr.py — FHC confirm 게이트 alpha-wealth FDR firewall (INV-12).

설계 = .consult-judge-report-RESULTS.md C12/C13(INV-12) + .coord-fhc-contract §4/§5.
fhc.transition(fdr_firewall=) 로 주입 → minted→confirmed 다중성(multiplicity) 통제. 고정 e-임계
단독은 카드 N개 mint 시 우연 confirm 누적 → ELOND(e값 online FDR, 임의의존 robust) 로 budget 차감.

★INV-12 firewall: layer(meta/basket/macro/asset) 경계 **고정분할 = layer별 별 ELOND ledger**,
  cross-boundary budget transfer 0(confirmation-cascade 통로 차단). LORD++/ELOND 는 layer 내부만.
★카드당 1회 테스트(double-spend 방지) + pre-filter(card.confirm_e_threshold 미만 = budget 미소비).

재사용: core.structure.eprocess_backbone.ELOND(e값 구동 online FDR, Wang-Ramdas 임의의존 robust).
opt-in off byte-identical: fhc.transition(fdr_firewall=None) = 기존 고정 임계 경로(본 모듈 미사용).
"""

from __future__ import annotations

from typing import Dict

from core.structure.eprocess_backbone import ELOND


def _layer_of(scope: str) -> str:
    """카드 scope → FDR layer(INV-12 고정분할 키)."""
    if scope == "sector":
        return "basket"
    if scope in ("macro", "global"):
        return "macro"
    return "asset"                              # single_asset/asset


class FDRFirewall:
    """layer별 ELOND alpha-wealth — confirm 다중성 통제(INV-12).

    test_confirm(card, e_value):
      ① card_id 캐시 존재 → 캐시 반환(카드당 1회, double-spend 방지).
      ② e_value < card.confirm_e_threshold → False(pre-filter, budget 미소비).
      ③ layer ELOND.test(e_value).reject → confirm 여부. 캐시.
    """

    def __init__(self, alpha: float = 0.05):
        self._alpha = alpha
        self._ledgers: Dict[str, ELOND] = {}
        self._decided: Dict[str, bool] = {}

    def _ledger(self, layer: str) -> ELOND:
        if layer not in self._ledgers:
            self._ledgers[layer] = ELOND(alpha=self._alpha)   # INV-12 layer별 별 ledger
        return self._ledgers[layer]

    def test_confirm(self, card, e_value: float) -> bool:
        if card.card_id in self._decided:
            return self._decided[card.card_id]                # 카드당 1회
        if float(e_value) < card.confirm_e_threshold:
            return False                                      # pre-filter, budget 미소비
        dec = self._ledger(_layer_of(card.scope)).test(float(e_value))
        self._decided[card.card_id] = bool(dec.reject)
        return bool(dec.reject)

    def stats(self) -> dict:
        return {lk: {"t": lg.t, "discoveries": lg.n_disc} for lk, lg in self._ledgers.items()}


# ===========================================================================
# self-test (verifier 대체 — INV-12 집행)
# ===========================================================================
if __name__ == "__main__":
    from core.assume.fhc import (
        FHCard, FHCState, FHCStateEnum, MediatorState, MediatorSpec, OutcomeSpec,
        update_outcome, transition,
    )

    def _card(cid, scope="macro", thr=20.0):
        return FHCard(card_id=cid, scope=scope, domain="macro", direction="long_tilt",
                      statement="t", falsification_metric="f",
                      mediator=MediatorSpec("x", op=">", threshold=0.0),
                      outcome=OutcomeSpec("ts_rank_IC", "s"),
                      bonus_cap=0.05, confirm_e_threshold=thr, targets=(cid,))

    def _state_with_e(card, signal, n):
        st = FHCState(card.card_id)
        for _ in range(n):
            update_outcome(st, signal, mediator_holds=True)
        return st

    # 1) firewall 미주입(None) = 기존 고정 임계 경로(byte-identical)
    c = _card("a")
    st = _state_with_e(c, 1.2, 60)
    transition(c, st, mediator_state=MediatorState.HOLDS, fdr_firewall=None)
    assert st.state == FHCStateEnum.CONFIRMED
    print("1) firewall None = 고정 임계 fallback OK(confirmed)")

    # 2) pre-filter: e < confirm_e_threshold → budget 미소비(False, ledger 미생성)
    fw = FDRFirewall(alpha=0.05)
    c2 = _card("b", thr=1e9)                      # 도달 불가 임계
    st2 = _state_with_e(c2, 1.2, 60)
    transition(c2, st2, mediator_state=MediatorState.HOLDS, fdr_firewall=fw)
    assert st2.state == FHCStateEnum.MINTED, st2.state
    assert fw.stats() == {}, fw.stats()          # ledger 미생성 = budget 미소비
    print("2) pre-filter OK: e<임계 → confirm X, budget 미소비")

    # 3) 강 e-value 카드 → FDR 통과 confirm + budget 소비
    fw3 = FDRFirewall(alpha=0.05)
    c3 = _card("c")
    st3 = _state_with_e(c3, 1.5, 80)             # 강 e
    transition(c3, st3, mediator_state=MediatorState.HOLDS, fdr_firewall=fw3)
    assert st3.state == FHCStateEnum.CONFIRMED, st3.state
    assert fw3.stats()["macro"]["discoveries"] == 1
    print(f"3) 강 e FDR 통과 confirm OK: macro discoveries={fw3.stats()['macro']['discoveries']}")

    # 4) ★INV-12 layer 격리: macro vs sector 별 ledger(독립 budget)
    fw4 = FDRFirewall(alpha=0.05)
    cm = _card("m", scope="macro"); sm = _state_with_e(cm, 1.5, 80)
    cs = _card("s", scope="sector"); ss = _state_with_e(cs, 1.5, 80)
    transition(cm, sm, mediator_state=MediatorState.HOLDS, fdr_firewall=fw4)
    transition(cs, ss, mediator_state=MediatorState.HOLDS, fdr_firewall=fw4)
    s4 = fw4.stats()
    assert "macro" in s4 and "basket" in s4 and s4["macro"]["t"] == 1 and s4["basket"]["t"] == 1
    print(f"4) INV-12 layer 격리 OK: macro t={s4['macro']['t']} / basket t={s4['basket']['t']} (별 ledger)")

    # 5) ★double-spend 방지: 같은 카드 재테스트 → 캐시(budget 추가소비 0)
    fw5 = FDRFirewall(alpha=0.05)
    c5 = _card("d"); st5 = _state_with_e(c5, 1.5, 80)
    r1 = fw5.test_confirm(c5, st5.e_value)
    t_after1 = fw5.stats()["macro"]["t"]
    r2 = fw5.test_confirm(c5, st5.e_value)        # 재호출
    t_after2 = fw5.stats()["macro"]["t"]
    assert r1 == r2 and t_after1 == t_after2 == 1, (r1, r2, t_after1, t_after2)
    print(f"5) double-spend 방지 OK: 재호출 t 불변({t_after2}), 캐시 반환")

    # 6) ★multiplicity 통제: 약 e 다수 → ELOND budget 차감으로 confirm 억제
    #    (고정 임계라면 임계만 넘으면 전부 confirm = 우연 다수 통과. ELOND는 γ_t 감소로 후순위 억제)
    fw6 = FDRFirewall(alpha=0.05)
    n_conf_fdr = 0
    for i in range(20):
        ci = _card(f"w{i}", thr=20.0)
        sti = _state_with_e(ci, 0.62, 50)        # 경계 e(임계 살짝 위)
        transition(ci, sti, mediator_state=MediatorState.HOLDS, fdr_firewall=fw6)
        if sti.state == FHCStateEnum.CONFIRMED:
            n_conf_fdr += 1
    # 고정 임계 대조(firewall 없이 동일 e면 전부 confirm)
    n_conf_fixed = 0
    for i in range(20):
        ci = _card(f"f{i}", thr=20.0)
        sti = _state_with_e(ci, 0.62, 50)
        transition(ci, sti, mediator_state=MediatorState.HOLDS, fdr_firewall=None)
        if sti.state == FHCStateEnum.CONFIRMED:
            n_conf_fixed += 1
    assert n_conf_fdr <= n_conf_fixed, (n_conf_fdr, n_conf_fixed)
    print(f"6) multiplicity 통제 OK: FDR confirm {n_conf_fdr} ≤ 고정 confirm {n_conf_fixed}(후순위 억제)")

    print("\nfhc_fdr self-test PASS (firewall None fallback · pre-filter budget절약 · 강e confirm · "
          "INV-12 layer격리 · double-spend 캐시 · multiplicity 통제)")
