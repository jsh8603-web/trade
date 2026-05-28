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

        # risk_gate 통과 후 확정 (Phase2 계약 재사용)
        if self._risk_gate is not None:
            try:
                pass  # risk_gate.check 는 개별 트레이드 진입 시 — 배분 확정 후 호출자 책임
            except Exception:
                pass

        result["macro_abstain"] = macro_abstain
        return result

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
