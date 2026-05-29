"""core/risk_gate.py — 공통 리스크 게이트 (Phase 2 SO-1~3 hard rule + 상관캡 + kill switch).

우회불가 백스톱 — 전 트랙(coin·stock) 거래의 최종 안전 게이트.
consensus/LLM 과 무관하게 항상-on. 결정론(LLM import 0).

hard rule (SO-1):
  - per-position stop: -5% soft / -10% hard (이중)
  - 일일 손실한도 초과 → 전트랙 halt
  - max weight: 단일 종목 10%, 섹터 30%
  - max turnover: 1회 거래 상한
  - min_holding: 최소 보유기간(세금/수수료 최적화)

상관 규칙 (SO-2):
  - corr > 0.7 캡: 신규 진입 차단(rejected)
  - corr >= 0.8: size 0.7x 축소(reduced) — ai-hedge-fund risk_manager:301 패턴
  - 0.6 <= corr < 0.8: size 0.85x
  - corr < 0.6: 영향 없음

reuse: nautilus_trader risk/engine.pyx:359 max_notional_per_order 패턴.
       ai-hedge-fund src/agents/risk_manager.py:301 calculate_correlation_multiplier.
near_miss_veto: logs/executions/near_miss_veto.jsonl (llm_worker 형식 일관).

SACRED: LLM import 0, 코인 라이브 경로 미변경, Phase0/1 본체 미변경.
"""

from __future__ import annotations

import json
import logging
import math
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger("core.risk_gate")

KST = timezone(timedelta(hours=9))

# ── 기본 파라미터 ─────────────────────────────────────────────────────

SOFT_STOP_PCT  = float(os.environ.get("RISK_SOFT_STOP_PCT",  "-5.0"))   # -5%
HARD_STOP_PCT  = float(os.environ.get("RISK_HARD_STOP_PCT",  "-10.0"))  # -10%
DAILY_LOSS_CAP = float(os.environ.get("RISK_DAILY_LOSS_CAP", "-0.05"))  # -5% NAV
MAX_WEIGHT_SINGLE  = float(os.environ.get("RISK_MAX_WEIGHT_SINGLE",  "0.10"))  # 10%
MAX_WEIGHT_SECTOR  = float(os.environ.get("RISK_MAX_WEIGHT_SECTOR",  "0.30"))  # 30%
MAX_TURNOVER_SINGLE = float(os.environ.get("RISK_MAX_TURNOVER", "0.20"))       # 20% NAV
MIN_HOLDING_DAYS    = int(os.environ.get("RISK_MIN_HOLDING_DAYS", "1"))

# SO-2: 상관캡
CORR_CAP_THRESHOLD  = float(os.environ.get("RISK_CORR_CAP", "0.7"))   # 초과 시 차단
CORR_HIGH_THRESHOLD = float(os.environ.get("RISK_CORR_HIGH", "0.8"))  # 이상 시 0.7x

_LOG_DIR = Path(os.environ.get("PROJECT_ROOT", str(Path(__file__).resolve().parents[1]))) / "logs" / "executions"
_LOG_DIR.mkdir(parents=True, exist_ok=True)


# ── Verdict ──────────────────────────────────────────────────────────

class VerdictType(str, Enum):
    APPROVED = "approved"
    REDUCED  = "reduced"
    REJECTED = "rejected"


@dataclass
class RiskVerdict:
    """risk_gate.check() 반환값."""
    verdict: VerdictType
    reason: str
    adjusted_size: float | None = None   # reduced 시 조정된 사이즈(비율 또는 금액)
    triggered_rules: list[str] = field(default_factory=list)

    @property
    def approved(self) -> bool:
        return self.verdict == VerdictType.APPROVED


# ── near_miss_veto 기록 ──────────────────────────────────────────────

def _log_near_miss_veto(
    cycle_id: str,
    reason: str,
    raw: Any,
    rule: str = "",
) -> None:
    """거절/축소 이벤트를 near_miss_veto.jsonl 에 기록 (llm_worker 형식 일관)."""
    try:
        entry = {
            "event": "near_miss_veto",
            "cycle_id": cycle_id,
            "reason": reason,
            "raw_snippet": str(raw)[:300],
            "rule": rule,
            "timestamp": datetime.now(KST).isoformat(),
        }
        with (_LOG_DIR / "near_miss_veto.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error("near_miss_veto 기록 실패: %s", e)


# ── SO-2: 상관 multiplier ────────────────────────────────────────────

def calculate_correlation_multiplier(avg_correlation: float) -> float:
    """평균 상관계수 → 사이즈 조정 배수.

    reuse: ai-hedge-fund src/agents/risk_manager.py:301.
      >= 0.80 → 0.70x  (고상관 축소)
      >= 0.60 → 0.85x
      >= 0.40 → 1.00x  (중립)
      >= 0.20 → 1.05x
      <  0.20 → 1.10x  (저상관 확대)
    """
    if avg_correlation >= 0.80:
        return 0.70
    if avg_correlation >= 0.60:
        return 0.85
    if avg_correlation >= 0.40:
        return 1.00
    if avg_correlation >= 0.20:
        return 1.05
    return 1.10


# ── RiskGate ──────────────────────────────────────────────────────────

class RiskGate:
    """공통 리스크 게이트 — hard rule 순차 적용.

    check() 는 결정론(외부 IO 없음, LLM 의존 0).
    """

    def __init__(
        self,
        soft_stop_pct: float = SOFT_STOP_PCT,
        hard_stop_pct: float = HARD_STOP_PCT,
        daily_loss_cap: float = DAILY_LOSS_CAP,
        max_weight_single: float = MAX_WEIGHT_SINGLE,
        max_weight_sector: float = MAX_WEIGHT_SECTOR,
        max_turnover: float = MAX_TURNOVER_SINGLE,
        min_holding_days: int = MIN_HOLDING_DAYS,
        corr_cap: float = CORR_CAP_THRESHOLD,
        corr_high: float = CORR_HIGH_THRESHOLD,
    ) -> None:
        self.soft_stop_pct    = soft_stop_pct
        self.hard_stop_pct    = hard_stop_pct
        self.daily_loss_cap   = daily_loss_cap
        self.max_weight_single = max_weight_single
        self.max_weight_sector = max_weight_sector
        self.max_turnover     = max_turnover
        self.min_holding_days = min_holding_days
        self.corr_cap         = corr_cap
        self.corr_high        = corr_high

    def check(
        self,
        *,
        cycle_id: str = "",
        # 제안 거래
        action: str = "buy",          # "buy" | "sell" | "hold"
        proposed_size: float = 0.0,   # 거래 금액 또는 비율
        # 현재 포지션
        position_pnl_pct: float = 0.0,   # 현 포지션 수익률 (예: -0.06 = -6%)
        holding_days: int = 0,            # 현 포지션 보유일
        current_weight: float = 0.0,     # 현 포지션 포트폴리오 비중 (0~1)
        sector_weight: float = 0.0,      # 섹터 합산 비중 (0~1)
        # 포트폴리오 수준
        nav: float = 1.0,                # 순자산가치 (정규화, 1=기준)
        ytd_realized_pnl_pct: float = 0.0,  # 당일 실현 손익 (NAV 대비)
        daily_loss_pct: float = 0.0,        # 당일 누적 손실 (NAV 대비, 음수)
        is_halted: bool = False,         # 상위 halt 상태(kill switch 등)
        # SO-2: 상관 (avg_correlation = 현 포지션과의 평균 상관계수)
        avg_correlation: float = 0.0,
        # 부가 정보
        raw_payload: Any = None,
    ) -> RiskVerdict:
        """hard rule 순차 검사 → RiskVerdict 반환.

        SACRED: 이 함수는 LLM 호출 없음. 결정론 순수 함수에 가깝게 유지.
        """
        # 입력 정규화 + 검증 (fail-closed: 비정상 입력 = 차단)
        action = (action or "").strip().lower()
        if action not in ("buy", "sell", "hold"):
            reason = f"알 수 없는 action: {action!r} — 차단"
            _log_near_miss_veto(cycle_id, reason, raw_payload, "invalid_action")
            return RiskVerdict(VerdictType.REJECTED, reason, triggered_rules=["invalid_action"])

        if action == "hold":
            return RiskVerdict(VerdictType.APPROVED, "hold — skip risk check")

        if not math.isfinite(nav) or nav <= 0:
            reason = f"비정상 NAV: {nav!r} — 차단"
            _log_near_miss_veto(cycle_id, reason, raw_payload, "invalid_nav")
            return RiskVerdict(VerdictType.REJECTED, reason, triggered_rules=["invalid_nav"])
        if not all(math.isfinite(x) for x in (
            proposed_size, position_pnl_pct, daily_loss_pct,
            current_weight, sector_weight, avg_correlation, ytd_realized_pnl_pct,
        )):
            reason = "비정상 수치 입력 (NaN/inf) — 차단"
            _log_near_miss_veto(cycle_id, reason, raw_payload, "invalid_numeric")
            return RiskVerdict(VerdictType.REJECTED, reason, triggered_rules=["invalid_numeric"])

        triggered: list[str] = []

        # ① 상위 halt (kill switch / 일일손실) 전달
        if is_halted:
            reason = "상위 halt 상태 — 신규 진입 차단"
            _log_near_miss_veto(cycle_id, reason, raw_payload, "halt_propagation")
            return RiskVerdict(VerdictType.REJECTED, reason, triggered_rules=["halt_propagation"])

        # ② 일일 손실한도 초과 → 전트랙 halt
        if daily_loss_pct <= self.daily_loss_cap:
            reason = f"일일 손실한도 초과: {daily_loss_pct:.2%} <= {self.daily_loss_cap:.2%}"
            _log_near_miss_veto(cycle_id, reason, raw_payload, "daily_loss_halt")
            return RiskVerdict(VerdictType.REJECTED, reason, triggered_rules=["daily_loss_halt"])

        # ③ per-position hard stop -10%
        if position_pnl_pct <= self.hard_stop_pct / 100:
            reason = f"per-position hard stop: {position_pnl_pct:.2%} <= {self.hard_stop_pct:.1f}%"
            _log_near_miss_veto(cycle_id, reason, raw_payload, "per_pos_hard_stop")
            return RiskVerdict(VerdictType.REJECTED, reason, triggered_rules=["per_pos_hard_stop"])

        # ④ per-position soft stop -5% (매수 추가 차단만, 매도는 허용)
        if action == "buy" and position_pnl_pct <= self.soft_stop_pct / 100:
            reason = f"per-position soft stop: {position_pnl_pct:.2%} <= {self.soft_stop_pct:.1f}%"
            _log_near_miss_veto(cycle_id, reason, raw_payload, "per_pos_soft_stop")
            return RiskVerdict(VerdictType.REJECTED, reason, triggered_rules=["per_pos_soft_stop"])

        # ⑤ min_holding — 최소 보유기간 미충족 (매도 시 체크)
        if action == "sell" and holding_days < self.min_holding_days:
            reason = f"min_holding 위반: {holding_days}일 < {self.min_holding_days}일"
            _log_near_miss_veto(cycle_id, reason, raw_payload, "min_holding")
            return RiskVerdict(VerdictType.REJECTED, reason, triggered_rules=["min_holding"])

        # ⑤-b SO-2: 상관캡 (매수 시만 적용)
        if action == "buy" and avg_correlation > self.corr_cap:
            reason = f"상관캡 초과: avg_corr={avg_correlation:.3f} > {self.corr_cap:.1f} → 신규 진입 차단"
            _log_near_miss_veto(cycle_id, reason, raw_payload, "corr_cap")
            return RiskVerdict(VerdictType.REJECTED, reason, triggered_rules=["corr_cap"])

        # SO-2: 상관 multiplier (0.7 이하이지만 0.6 이상이면 축소)
        corr_mult = calculate_correlation_multiplier(avg_correlation) if action == "buy" else 1.0
        if action == "buy" and corr_mult < 1.0:
            adjusted = proposed_size * corr_mult
            reason = f"상관 multiplier 축소: avg_corr={avg_correlation:.3f} → ×{corr_mult:.2f} ({proposed_size:.0f}→{adjusted:.0f})"
            _log_near_miss_veto(cycle_id, reason, raw_payload, "corr_multiplier")
            triggered.append("corr_multiplier")
            proposed_size = adjusted

        # ⑥ max weight (매수 시 비중 초과 → 축소)
        adjusted = proposed_size
        if action == "buy" and current_weight + (proposed_size / nav) > self.max_weight_single:
            allowed = max(0.0, (self.max_weight_single - current_weight) * nav)
            reason = f"max weight 단일 초과: {current_weight + proposed_size/nav:.2%} > {self.max_weight_single:.0%} → {allowed:.0f}으로 축소"
            _log_near_miss_veto(cycle_id, reason, raw_payload, "max_weight_single")
            if allowed <= 0:
                return RiskVerdict(VerdictType.REJECTED, reason, triggered_rules=["max_weight_single"])
            adjusted = allowed
            triggered.append("max_weight_single")

        if action == "buy" and sector_weight + (adjusted / nav) > self.max_weight_sector:
            allowed = max(0.0, (self.max_weight_sector - sector_weight) * nav)
            reason = f"max weight 섹터 초과: 섹터비중 {sector_weight:.2%} → {allowed:.0f}으로 축소"
            _log_near_miss_veto(cycle_id, reason, raw_payload, "max_weight_sector")
            if allowed <= 0:
                return RiskVerdict(VerdictType.REJECTED, reason, triggered_rules=triggered + ["max_weight_sector"])
            adjusted = min(adjusted, allowed)
            triggered.append("max_weight_sector")

        # ⑦ max turnover
        if adjusted / max(nav, 1e-9) > self.max_turnover:
            allowed = self.max_turnover * nav
            reason = f"max turnover 초과: {adjusted/nav:.2%} > {self.max_turnover:.0%} → {allowed:.0f}으로 축소"
            _log_near_miss_veto(cycle_id, reason, raw_payload, "max_turnover")
            adjusted = allowed
            triggered.append("max_turnover")

        if triggered:
            return RiskVerdict(
                VerdictType.REDUCED,
                f"사이즈 축소: {', '.join(triggered)}",
                adjusted_size=adjusted,
                triggered_rules=triggered,
            )

        return RiskVerdict(VerdictType.APPROVED, "all rules passed", adjusted_size=proposed_size)


# ── SO-3: KillSwitch (MDD, H27) ──────────────────────────────────────

class KillSwitchState(str, Enum):
    ACTIVE          = "active"           # 정상 운용
    HALTED          = "halted"           # MDD 초과 → 신규 진입 차단, 청산 보류
    CONFIRM_PENDING = "confirm_pending"  # 청산 컨펌 대기 중
    # 해제: MDD 회복 → ACTIVE 복귀


MDD_THRESHOLD = float(os.environ.get("RISK_MDD_THRESHOLD", "-0.15"))  # -15%


class KillSwitch:
    """MDD 기반 kill switch — H27 보완 + 무인(unattended) 자동 de-risk.

    SACRED:
      - 자동 전량 시장가 청산 금지 (⛔ full market liquidation) — 유지.
        thin-book 덤핑(-50%) footgun 방지. 비상 축소는 derisk_executor(U2)가
        IOC 단계청산 + 슬리피지 상한 frozen bag 으로 집행 (전량청산 아님).
      - attended 모드: 청산은 confirm() 호출 후에만 (사람 게이트).
      - unattended 모드: 사람 confirm 부재 → auto_derisk_due()=True 즉시.
        derisk_executor(U2)가 de-risk-to-floor 자동 집행 → 무인 영구동결 해소.
      - 수동 EMERGENCY_STOP(orchestrator.py:179) 과 독립.
    """

    def __init__(
        self,
        mdd_threshold: float = MDD_THRESHOLD,
        unattended: bool | None = None,
    ) -> None:
        self.mdd_threshold = mdd_threshold
        # 무인 운영 기본 True. RISK_UNATTENDED=false 시 attended(사람 confirm) 모드.
        if unattended is None:
            unattended = os.environ.get("RISK_UNATTENDED", "true").lower() != "false"
        self.unattended = unattended
        self._state: KillSwitchState = KillSwitchState.ACTIVE
        self._alert_flag: bool = False      # 알림 플래그 (외부 모니터링용)
        self._pending_liquidation: bool = False

    @property
    def state(self) -> KillSwitchState:
        return self._state

    @property
    def alert_flag(self) -> bool:
        return self._alert_flag

    @property
    def is_halted(self) -> bool:
        return self._state in (KillSwitchState.HALTED, KillSwitchState.CONFIRM_PENDING)

    def update_mdd(self, current_mdd: float, cycle_id: str = "") -> KillSwitchState:
        """MDD 갱신 → 상태 전이.

        current_mdd: 음수 (예: -0.16 = -16% MDD).
        MDD 초과 → HALTED + alert, 회복 → ACTIVE.
        """
        if current_mdd <= self.mdd_threshold:
            if self._state == KillSwitchState.ACTIVE:
                self._state = KillSwitchState.HALTED
                self._alert_flag = True
                _log_near_miss_veto(
                    cycle_id,
                    f"kill switch 발동: MDD={current_mdd:.2%} <= {self.mdd_threshold:.2%}",
                    {"mdd": current_mdd},
                    "kill_switch_mdd",
                )
                logger.warning(
                    "KillSwitch HALTED: MDD=%.2f%% threshold=%.2f%%",
                    current_mdd * 100, self.mdd_threshold * 100,
                )
        else:
            # MDD 회복 → ACTIVE (청산 컨펌 대기 중이어도 회복 시 해제)
            if self._state != KillSwitchState.ACTIVE:
                self._state = KillSwitchState.ACTIVE
                self._alert_flag = False
                self._pending_liquidation = False
                logger.info("KillSwitch RECOVERED: MDD=%.2f%%", current_mdd * 100)
        return self._state

    def request_liquidation(self) -> bool:
        """청산 요청 — HALTED 상태일 때만 CONFIRM_PENDING 으로 전이.

        Returns True if transition succeeded.
        ⛔ 자동 청산 금지 — confirm() 후에만 실제 청산.
        """
        if self._state == KillSwitchState.HALTED:
            self._state = KillSwitchState.CONFIRM_PENDING
            self._pending_liquidation = True
            return True
        return False

    def confirm(self) -> bool:
        """청산 컨펌 — CONFIRM_PENDING → liquidation 실행 허가 (attended 전용).

        Returns True 시 호출자가 청산 로직을 수행해야 함.
        ⚠️ unattended 모드에서는 사람 confirm 부재 → auto_derisk_due() 경로 사용.
        """
        if self._state == KillSwitchState.CONFIRM_PENDING:
            self._pending_liquidation = False
            return True
        return False

    def auto_derisk_due(self) -> bool:
        """무인 자동 de-risk 발동 여부 (사람 confirm 부재 시 영구동결 해소).

        unattended 모드 + HALTED/CONFIRM_PENDING → True (즉시, 사람 대기 없음).
        derisk_executor(U2)가 이 신호를 소비해 de-risk-to-floor(IOC 단계청산
        + frozen bag 상한)를 자동 집행한다. 전량 시장가 청산이 아니라 SACRED 와 양립.
        attended 모드(unattended=False)는 False → confirm()/H27 타임아웃 경로 유지.
        """
        return self.unattended and self.is_halted

    def reset(self) -> None:
        """강제 리셋 (테스트/수동 복구용)."""
        self._state = KillSwitchState.ACTIVE
        self._alert_flag = False
        self._pending_liquidation = False


# ── SO-4: §6 Precedence 격자 ─────────────────────────────────────────

class PrecedenceLevel(int, Enum):
    """충돌 해소 우선순위 (낮을수록 먼저)."""
    KILL_SWITCH   = 1   # ① kill switch/halt
    SAFETY_STOP   = 2   # ② per-position stop, 일일 손실한도
    PORTFOLIO_CAP = 3   # ③ 상관캡, max weight
    TAX_HOLDING   = 4   # ④ min_holding (세금/수수료)
    REBALANCE     = 5   # ⑤ regime flip, turnover


# 규칙명 → 격자 레벨 매핑
_RULE_PRECEDENCE: dict[str, PrecedenceLevel] = {
    "halt_propagation": PrecedenceLevel.KILL_SWITCH,
    "kill_switch_mdd":  PrecedenceLevel.KILL_SWITCH,
    "daily_loss_halt":  PrecedenceLevel.SAFETY_STOP,
    "per_pos_hard_stop": PrecedenceLevel.SAFETY_STOP,
    "per_pos_soft_stop": PrecedenceLevel.SAFETY_STOP,
    "corr_cap":          PrecedenceLevel.PORTFOLIO_CAP,
    "corr_multiplier":   PrecedenceLevel.PORTFOLIO_CAP,
    "max_weight_single": PrecedenceLevel.PORTFOLIO_CAP,
    "max_weight_sector": PrecedenceLevel.PORTFOLIO_CAP,
    "max_turnover":      PrecedenceLevel.REBALANCE,
    "min_holding":       PrecedenceLevel.TAX_HOLDING,
    "regime_flip":       PrecedenceLevel.REBALANCE,
    "turnover_limit":    PrecedenceLevel.REBALANCE,
}


def resolve_precedence(
    verdicts: list[RiskVerdict],
    cycle_id: str = "",
    raw_payload: Any = None,
) -> RiskVerdict:
    """다중 RiskVerdict 충돌 → 격자 순서로 단일 verdict 해소.

    §6 precedence: ① kill switch ② 안전 스톱 ③ 포트폴리오 캡 ④ 세금 ⑤ 리밸런스.
    같은 레벨 내 = 가장 제한적인 verdict 우선(rejected > reduced > approved).
    충돌 항목 전체 near_miss_veto 기록.
    """
    if not verdicts:
        return RiskVerdict(VerdictType.APPROVED, "no rules — approved")

    # 거절 규칙 중 최고 우선순위 찾기
    rejected = [v for v in verdicts if v.verdict == VerdictType.REJECTED]
    if rejected:
        # 가장 높은 우선순위(낮은 레벨 숫자) 선택
        best = min(
            rejected,
            key=lambda v: min(
                (_RULE_PRECEDENCE.get(r, PrecedenceLevel.REBALANCE) for r in v.triggered_rules),
                default=PrecedenceLevel.REBALANCE,
            ),
        )
        # 충돌 항목 전체 기록
        all_rules = [r for v in verdicts for r in v.triggered_rules]
        if len(all_rules) > len(best.triggered_rules):
            _log_near_miss_veto(
                cycle_id,
                f"precedence 충돌 해소: {best.triggered_rules} 우선 / 전체={all_rules}",
                raw_payload,
                "precedence_conflict",
            )
        return best

    # 축소 규칙 중 최소 adjusted_size
    reduced = [v for v in verdicts if v.verdict == VerdictType.REDUCED]
    if reduced:
        sizes = [v.adjusted_size for v in reduced if v.adjusted_size is not None]
        min_size = min(sizes) if sizes else None
        all_rules = [r for v in reduced for r in v.triggered_rules]
        return RiskVerdict(
            VerdictType.REDUCED,
            f"precedence 격자 축소: {all_rules}",
            adjusted_size=min_size,
            triggered_rules=all_rules,
        )

    # 전부 approved
    return RiskVerdict(VerdictType.APPROVED, "precedence: all approved")


# ── SO-6: 우회불가 백스톱 + 프로세스 격리 ────────────────────────────

class GatedOrderRouter:
    """nautilus engine.pyx:492 _deny_order_list 패턴 — 우회불가 최종 관문.

    모든 거래가 risk_gate.check() 를 반드시 경유하도록 강제.
    LLM/실행 프로세스는 이 wrapper 를 통해서만 주문 접근 가능.

    SACRED:
      - LLM 이 직접 execute 호출하는 경로 차단 (결정론 격리)
      - B1 하드게이트(Phase -1 SO-3)와 경계 분리 유지
    """

    def __init__(
        self,
        gate: RiskGate | None = None,
        kill_switch: KillSwitch | None = None,
    ) -> None:
        self._gate = gate or RiskGate()
        self._ks = kill_switch or KillSwitch()
        self._bypassed_attempts: int = 0

    def submit(
        self,
        order: dict[str, Any],
        *,
        cycle_id: str = "",
        via_gate: bool = False,  # 반드시 True 로 호출해야 함
        **gate_kwargs: Any,
    ) -> RiskVerdict:
        """주문 제출 — risk_gate.check() 경유 강제.

        via_gate=False (우회 시도) → 즉시 REJECTED + near_miss_veto.
        via_gate=True → RiskGate.check() 실행 후 verdict 반환.
        """
        if not via_gate:
            self._bypassed_attempts += 1
            reason = f"우회 시도 차단: risk_gate 미경유 주문 (총 {self._bypassed_attempts}회)"
            _log_near_miss_veto(cycle_id, reason, order, "bypass_attempt")
            logger.warning("GatedOrderRouter: %s", reason)
            return RiskVerdict(
                VerdictType.REJECTED,
                reason,
                triggered_rules=["bypass_attempt"],
            )

        is_halted = self._ks.is_halted
        return self._gate.check(
            cycle_id=cycle_id,
            is_halted=is_halted,
            **gate_kwargs,
        )

    @property
    def bypassed_attempts(self) -> int:
        return self._bypassed_attempts
