"""core/portfolio_orchestrator.py — Portfolio Orchestrator BL 슬리브 배분 (SO-1/P6).

WHY: Phase 0~5 산출물(AssetTrack·RiskGate·regime_classifier·macro_reasoning·regime_to_weights)을
     최상위 집계층으로 wire. 코인 라이브·Phase0~5 본체 미변경 SACRED.

설계:
- regime_classifier.classify() → macro_reasoning.enrich() → regime_to_weights() 체인
- BL 슬리브 배분: per-bloc(US주/KR주/원자재/금/채권/현금/코인)
- fallback Riskfolio HRP (BL 실패 시)
- risk_gate 통과 후 확정
- Drift Monitor: 매 사이클 최우선 밴드 이탈 감시
- §4.2 consensus: 고-스테이크스 발동 검사 (stub 경계)
- H29 macro abstain: macro unavailable → generate_candidate 신규매수 차단
- H26 FX: 야간 stale → 직전 정규장 환율 고정
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("core.portfolio_orchestrator")


# ---------------------------------------------------------------------------
# 슬리브 밴드 설정 (OPEN ZONE — 폭 튜닝 가능)
# ---------------------------------------------------------------------------

# {sleeve: (min%, max%)} — 이탈 시 Drift Monitor 감지
SLEEVE_BANDS: Dict[str, Tuple[float, float]] = {
    "us_stock":  (0.10, 0.45),
    "kr_stock":  (0.05, 0.30),
    "commodity": (0.02, 0.18),
    "gold":      (0.02, 0.18),
    "bond":      (0.10, 0.45),
    "cash":      (0.03, 0.25),
    "coin":      (0.02, 0.20),
}


# ---------------------------------------------------------------------------
# near_miss_veto 경량 레코드 (§2.2)
# ---------------------------------------------------------------------------

@dataclass
class NearMissVeto:
    """Drift 이탈 or 리스크 경계 접근 감지 레코드."""
    sleeve: str
    current_weight: float
    band_min: float
    band_max: float
    reason: str
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    action_taken: str = "rebalance_trigger"


# ---------------------------------------------------------------------------
# consensus 트리거 판정 (§4.2, SO-3 상세 구현)
# ---------------------------------------------------------------------------

def is_high_stakes(
    regime_changed: bool = False,
    allocation_change_pct: float = 0.0,
    cumulative_position_pct: float = 0.0,
    allocation_threshold: float = 0.10,
    cumulative_threshold: float = 0.25,
) -> bool:
    """§4.2 고-스테이크스 판정 — consensus 발동 여부."""
    if regime_changed:
        return True
    if allocation_change_pct >= allocation_threshold:
        return True
    if cumulative_position_pct >= cumulative_threshold:
        return True
    return False


# ---------------------------------------------------------------------------
# PortfolioOrchestrator
# ---------------------------------------------------------------------------

class PortfolioOrchestrator:
    """최상위 집계층 — BL 슬리브 배분 + Drift Monitor + consensus 검사.

    SACRED: coin 라이브·Phase0~5 본체 미변경. 집계/wire만.
    """

    def __init__(
        self,
        risk_gate=None,
        fx_rate_krw_usd: float = 1350.0,   # H26: 기준 환율 (야간 stale 방지)
        consensus_enabled: bool = True,
    ):
        self._risk_gate = risk_gate
        self._fx_rate = fx_rate_krw_usd
        self._consensus_enabled = consensus_enabled
        self._consensus_node = None        # consensus LLM 노드 lazy(env MACRO_CONSENSUS)

        # 이전 슬리브 비중 (Drift Monitor 기준)
        self._prev_weights: Dict[str, float] = {}

        # near_miss_veto 누적 (Drift Monitor)
        self._veto_log: List[NearMissVeto] = []

        # macro status 캐시 (H29 abstain 판단)
        self._macro_status: str = "fresh"

    # ------------------------------------------------------------------
    # 메인: 슬리브 배분 산출
    # ------------------------------------------------------------------

    def allocate(
        self,
        macro_view=None,
        returns_history=None,
        method: str = "weight_tilt",
        sleeve_regime_ids=None,
        as_of=None,
        fhc_card_states=None,
    ) -> Dict[str, Any]:
        """regime→macro→weights 체인 실행 → BL 슬리브 % 산출.

        Args:
            macro_view: MacroView 인스턴스 (regime_classifier + macro_reasoning 출력).
                        None 이면 IC 중립 Prior fallback.
            returns_history: pd.DataFrame 슬리브 수익률 (BL 공분산용).
            method: "weight_tilt" | "bl_returns"

        Returns:
            {
              "weights": {sleeve: pct},
              "method": str,
              "prior": {sleeve: pct},
              "status": str,
              "caution": List[str],
              "macro_abstain": bool,   # H29
            }
        """
        # H29 macro abstain 체크
        macro_abstain = False
        if macro_view is not None:
            from core.brain.macro_schema import ViewStatus
            if macro_view.status == ViewStatus.UNAVAILABLE:
                macro_abstain = True
                self._macro_status = "unavailable"
                logger.warning("H29: macro unavailable → abstain 신규매수 차단")

        # ★R15 belief b(t) 선산출 (opt-in INV_R15_WEIGHTS, 기본 off = byte-identical 무회귀).
        # ④ 배선: belief 를 regime_to_weights *호출 전* 산출 → 전달(현 동작=기록만→실사용 재배치).
        # belief + sleeve_regime_ids + returns_history 셋 다 있으면 regime_to_weights 내부에서
        # regime-conditional Σ_eff(belief-mix)를 BL 공분산으로 주입(동적 조건부 공분산). substrate
        # (sleeve_regime_ids) 부재 시 belief 만 전달돼도 기존 경로(graceful). 거시상황(macro_view)이
        # belief 를 통해 배분 공분산에 실제로 반영되는 connectivity 가 본 ④의 핵심.
        from core.study.study_register import is_r15_enabled
        r15_belief = None
        # ★게이트 통일(2026-06-08): is_r15_enabled()(on/true/1/yes 허용)와 동일 값집합.
        #   기존 =="true" 단독 비교는 운영자가 "on"으로 켤 때 belief 동적 공분산 경로만
        #   말없이 죽는 함정(coin_track_macro:75 macro_view 게이트는 "on" 통과 → 불일치).
        r15_on = (is_r15_enabled() and macro_view is not None)
        if r15_on:
            try:
                from core.brain.regime_belief_adapter import belief_from_macro_view
                r15_belief = belief_from_macro_view(macro_view)
            except Exception as exc:
                logger.warning("R15 belief 산출 예외 → 정적 배분 유지: %s", exc)

        # regime_to_weights wire
        try:
            from core.brain.regime_to_weights import regime_to_weights
            if macro_view is None:
                result = self._fallback_hrp(returns_history)
            else:
                result = regime_to_weights(
                    macro_view,
                    returns_history=returns_history,
                    method=method,
                    belief=r15_belief,
                    sleeve_regime_ids=sleeve_regime_ids,
                    as_of=as_of,
                )
        except Exception as exc:
            logger.warning("regime_to_weights 실패 → HRP fallback: %s", exc)
            result = self._fallback_hrp(returns_history)

        # BL pi 주입 불변식 검증: 슬리브 합=1
        weights = result.get("weights", {})
        total = sum(weights.values())
        if abs(total - 1.0) > 1e-4:
            logger.warning("BL 슬리브 합 이상(%.4f) → 재정규화", total)
            weights = {k: v / total for k, v in weights.items()}
            result["weights"] = weights

        # 배분 산출 자체는 게이팅 안 함 — risk_gate.check() 는 개별 트레이드 진입 시
        # 실 order path 조립 단계에서 호출자가 적용. 우회불가 enforce =
        # N-P6-FULL-INTEGRATION / N-P4-GATE (go-live, GatedOrderRouter 경유 강제).
        result["macro_abstain"] = macro_abstain

        # ★R15 belief 기록 (감사) — 산출은 regime_to_weights 호출 전(위)에서 완료, 여기선 결과 기록.
        # sleeve_regime_ids substrate 까지 있으면 regime_to_weights 가 belief 동적 Σ_eff 를 BL 공분산
        # 으로 이미 주입(method=black_litterman_returns, caution=belief_conditional_cov). 없으면 belief
        # 는 기록만 되고 배분은 정적 경로(substrate=실 FRED vintage 과거 국면 → go-live/배치 산출 게이트).
        if r15_belief is not None:
            result["r15_belief"] = r15_belief
            tag = ("belief_conditional_cov" if any(
                "belief_conditional_cov" in str(c) for c in result.get("caution", []))
                else "r15_belief_supplied(동적공분산=sleeve_regime_ids substrate 게이트)")
            if not any("r15" in str(c) or "belief" in str(c) for c in result.get("caution", [])):
                result.setdefault("caution", []).append(tag)

        # ★(C) FHC bonus → weight tilt (env FHC_BONUS opt-in, off=byte-identical 무회귀).
        #   확정(confirmed/revived)+mediator HOLDS 카드만 L1 위로 bonus(INV-5), 천장 C=밴드 상한.
        #   probationary(자본0) 카드는 size_with_bonus 가 기여 0 → weights 무변경(go-live arming 전
        #   자동 무영향). 실주문은 별도(GatedOrderRouter, go-live) — allocate 는 weight 산출만(DRY 시뮬).
        if fhc_card_states and os.environ.get("FHC_BONUS", "false").lower() == "true":
            try:
                breaker = bool(macro_abstain)        # macro unavailable = 보수(INV-9 류 fail-closed)
                old_w = result.get("weights", {})
                new_w, sized = self._apply_fhc_bonus(
                    old_w, fhc_card_states, breaker_tripped=breaker)
                # 실제 변화한 경우만 교체(probationary-only=무변화→byte-identical)
                changed = any(abs(new_w.get(k, 0.0) - old_w.get(k, 0.0)) > 1e-12
                              for k in set(new_w) | set(old_w))
                if changed:
                    result["weights"] = new_w
                    result.setdefault("caution", []).append("fhc_bonus_applied")
                    result["fhc_sizing"] = {
                        a: {"l1": s.l1, "bonus": s.bonus, "final": s.final,
                            "clipped": s.clipped, "n_cards": s.n_cards}
                        for a, s in sized.items()}
            except Exception as exc:
                logger.warning("FHC bonus wire 실패 → L1 배분 유지: %s", exc)

        # ★consensus (env MACRO_CONSENSUS off=byte-identical) — 고-스테이크스 배분 변경을 LLM 이
        #   검토 → down-only de-risk(prior 후퇴만, 증폭 불가). 실주문은 별도(GatedOrderRouter go-live).
        cnode = self._get_consensus_node()
        if cnode is not None:
            try:
                w = result.get("weights", {})
                prior = result.get("prior", {}) or w
                prev = self._prev_weights or {}
                alloc_change = (max((abs(w.get(k, 0.0) - prev.get(k, 0.0)) for k in w), default=0.0)
                                if prev else 0.0)
                regime_now = ""
                if macro_view is not None:
                    from core.brain.macro_schema import Bloc
                    _u = macro_view.regime(Bloc.USD)
                    regime_now = _u.regime_now.value if _u is not None else ""
                if is_high_stakes(regime_changed=bool(macro_abstain),
                                  allocation_change_pct=alloc_change):
                    rev = cnode.review(weights=w, prior=prior, regime_now=regime_now,
                                       trigger_detail={"alloc_change": round(alloc_change, 4)})
                    dr = rev.get("de_risk", 0.0)
                    if dr > 0:
                        from core.brain.consensus_node import apply_consensus_derisk
                        result["weights"] = apply_consensus_derisk(w, prior, dr)
                        result.setdefault("caution", []).append("consensus_derisk")
                    result["consensus"] = rev
            except Exception as exc:
                logger.warning("consensus 검토 실패 → 배분 유지: %s", exc)

        return result

    def _get_consensus_node(self):
        """consensus LLM 노드 lazy — env MACRO_CONSENSUS off=None(byte-identical, 미호출)."""
        from core.assume.loop_factory import is_macro_consensus_enabled
        if not is_macro_consensus_enabled():
            return None
        if self._consensus_node is None:
            try:
                from core.brain.consensus_node import build_consensus_node
                self._consensus_node = build_consensus_node(use_claude=True)
            except Exception as exc:
                logger.warning("consensus_node 배선 실패 → 미적용: %s", exc)
                return None
        return self._consensus_node

    def _apply_fhc_bonus(self, weights, card_states, *, breaker_tripped: bool = False):
        """(C) bonus_channel.size_with_bonus 로 L1 위 bonus tilt → 합=1 재정규화.

        천장 C = SLEEVE_BANDS 상한(risk_gate 독립산출 단일자산 천장 C 의 배분레벨 proxy). 밴드 미정의
        슬리브는 1.0(무제한 상한). size_with_bonus INV-1/3/4/5/8/9 집행 후 final 합=1 재정규화.
        반환: (new_weights{합=1}, sized{asset: AssetSizing}).
        """
        from core.assume.bonus_channel import size_with_bonus
        ceilings = {sl: SLEEVE_BANDS.get(sl, (0.0, 1.0))[1] for sl in weights}
        sized = size_with_bonus(dict(weights), card_states, ceilings,
                                breaker_tripped=breaker_tripped)
        raw = {a: s.final for a, s in sized.items()}
        for a, w in weights.items():                 # sized 에 없는 슬리브 보존
            raw.setdefault(a, w)
        total = sum(raw.values())
        if total <= 0:
            return dict(weights), sized
        new_w = {a: v / total for a, v in raw.items()}   # 합=1 재정규화(bonus tilt = relative)
        return new_w, sized

    def _fallback_hrp(self, returns_history=None) -> Dict[str, Any]:
        """Riskfolio HRP fallback. 수익률 없으면 IC 중립 Prior."""
        from core.brain.regime_to_weights import BASE_WEIGHTS, _normalize
        if returns_history is not None and len(returns_history) > 5:
            try:
                import riskfolio as rp
                port = rp.HCPortfolio(returns=returns_history)
                w = port.optimization(model="HRP", codependence="pearson",
                                      rm="MV", rf=0, linkage="ward")
                weights = w.squeeze().to_dict()
                return {"weights": weights, "method": "hrp_fallback",
                        "prior": {}, "status": "fresh", "caution": []}
            except Exception as exc:
                logger.debug("HRP fallback 실패: %s", exc)

        weights = _normalize(dict(BASE_WEIGHTS))
        return {"weights": dict(weights), "method": "ic_prior_fallback",
                "prior": dict(weights), "status": "fresh", "caution": []}

    # ------------------------------------------------------------------
    # Drift Monitor (SO-2)
    # ------------------------------------------------------------------

    def monitor_band_drift(
        self, current_weights: Dict[str, float]
    ) -> List[NearMissVeto]:
        """매 사이클 최우선 밴드 이탈 감시.

        이탈 감지 → near_miss_veto CREATE + 리밸런싱 트리거 반환.
        밴드 내 → 빈 목록.
        """
        vetoes: List[NearMissVeto] = []
        for sleeve, weight in current_weights.items():
            band = SLEEVE_BANDS.get(sleeve)
            if band is None:
                continue
            lo, hi = band
            if weight < lo or weight > hi:
                reason = (
                    f"이탈: {sleeve} {weight:.3f} "
                    f"[{lo:.2f}, {hi:.2f}]"
                )
                veto = NearMissVeto(
                    sleeve=sleeve,
                    current_weight=weight,
                    band_min=lo,
                    band_max=hi,
                    reason=reason,
                )
                vetoes.append(veto)
                self._veto_log.append(veto)
                logger.warning("Drift Monitor: %s", reason)

        self._prev_weights = dict(current_weights)
        return vetoes

    # ------------------------------------------------------------------
    # H26 FX 고정환율 (야간 stale 방지)
    # ------------------------------------------------------------------

    def get_fx_rate(self, live_rate: Optional[float] = None, is_night_hours: bool = False) -> float:
        """H26: 야간 US장 FX 미갱신 시 직전 정규장 마감율 사용.

        가짜 kill-switch(MDD 계산 오류) 방지.
        """
        if is_night_hours or live_rate is None:
            logger.debug("H26: 야간 FX stale → 직전 정규장 마감율 %.2f 사용", self._fx_rate)
            return self._fx_rate
        self._fx_rate = live_rate  # 정규장 갱신
        return live_rate

    def update_fx_rate(self, rate: float) -> None:
        """정규장 마감 시 환율 갱신."""
        self._fx_rate = rate

    # ------------------------------------------------------------------
    # consensus 검사 (§4.2, SO-3 상세 구현 예정)
    # ------------------------------------------------------------------

    def check_consensus_trigger(
        self,
        regime_changed: bool = False,
        allocation_change_pct: float = 0.0,
        cumulative_position_pct: float = 0.0,
    ) -> bool:
        """§4.2 consensus 발동 여부 판정."""
        if not self._consensus_enabled:
            return False
        return is_high_stakes(
            regime_changed=regime_changed,
            allocation_change_pct=allocation_change_pct,
            cumulative_position_pct=cumulative_position_pct,
        )

    # ------------------------------------------------------------------
    # G9 미청산 mark-to-market (기본 훅 — 상세는 SO-7)
    # ------------------------------------------------------------------

    def mark_open_positions(
        self, open_trades: list, current_prices: Dict[str, float]
    ) -> List[Dict]:
        """G9: 미청산 포지션 mark-to-market. 잠정 귀속 라벨."""
        results = []
        for trade in open_trades:
            ticker = getattr(trade, "ticker", "UNKNOWN")
            entry = getattr(trade, "entry_price", 0.0)
            qty = getattr(trade, "qty", 0.0)
            current = current_prices.get(ticker, entry)
            unrealized_pnl = (current - entry) * qty
            results.append({
                "ticker": ticker,
                "unrealized_pnl": unrealized_pnl,
                "is_provisional": True,
                "status": "open",
            })
        return results

    @property
    def veto_log(self) -> List[NearMissVeto]:
        return list(self._veto_log)

    @property
    def macro_abstain(self) -> bool:
        return self._macro_status == "unavailable"
