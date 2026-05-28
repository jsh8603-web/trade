"""core/risk_gate.py — 공통 리스크 게이트 (Phase 2 SO-1~2 hard rule + 상관캡).

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
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
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
        if action == "hold":
            return RiskVerdict(VerdictType.APPROVED, "hold — skip risk check")

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
