"""core/reconciliation.py — 3-way 포지션 대조 (Phase Unattended SO-5).

설계 원칙:
  - 3뷰(intended / ledger / exchange_truth) pairwise delta → drift 분류.
  - 거래소 truth authoritative — ledger overwrite 시 N-consistent-sample 안전장치.
  - ⛔ A3 단일샘플 overwrite 금지: sanity-check → N회 연속 일치 → 의심 시 quarantine.
  - 모든 스냅샷 recon_log.jsonl append-only (immutable).
  - LLM/brain import 0 (독립 fail-safe).

action 분류:
  "none"        — 허용 오차 이내
  "soft_halt"   — recon_break 감지 (재매매 차단, de-risk 미실행)
  "hard_derisk" — 대형 delta(>RECON_HARD_PCT) or 연속 N회 확정 break
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ── 환경 변수 파라미터 ────────────────────────────────────────────────

RECON_TOL_PCT = float(os.environ.get("UNATTENDED_RECON_TOL_PCT", "0.001"))   # 0.1%
RECON_TOL_ABS = float(os.environ.get("UNATTENDED_RECON_TOL_ABS", "0.0001"))  # 절대 허용치
RECON_HARD_PCT = float(os.environ.get("UNATTENDED_RECON_HARD_PCT", "0.05"))  # 5% → hard_derisk

# A3: N-consistent-sample overwrite 안전장치
RECON_CONFIRM_N = int(os.environ.get("UNATTENDED_RECON_CONFIRM_N", "2"))     # 연속 N회 일치
RECON_SANITY_PCT = float(os.environ.get("UNATTENDED_RECON_SANITY_PCT", "0.5"))  # 50% 급변 = 의심

_RECON_LOG_PATH = Path(os.environ.get("UNATTENDED_RECON_LOG_PATH", "data/recon_log.jsonl"))


# ── 데이터 클래스 ─────────────────────────────────────────────────────

@dataclass
class ReconResult:
    """3-way 대조 결과."""
    breaks: list[dict]          # [{symbol, delta, drift_type, action_reason}]
    overwritten: dict           # {symbol: new_qty} — ledger 를 truth 로 덮어쓴 항목
    action: str                 # "none" / "soft_halt" / "hard_derisk"
    quarantined: list[str] = field(default_factory=list)  # 의심 truth → overwrite 보류 symbol


# ── 내부 상태 (N-consistent-sample 추적) ──────────────────────────────

@dataclass
class _TruthSample:
    """symbol 별 연속 일치 추적."""
    qty: float
    count: int = 1             # 동일 qty 연속 관측 횟수
    last_ts: float = 0.0


# Module-level state (단일 프로세스 내 persistent — 재시작 시 리셋)
_truth_samples: dict[str, _TruthSample] = {}
_prev_truth: dict[str, float] = {}  # 직전 truth (sanity-check용)


def reset_state() -> None:
    """테스트 격리용 상태 리셋."""
    global _truth_samples, _prev_truth
    _truth_samples = {}
    _prev_truth = {}


# ── 유틸 ──────────────────────────────────────────────────────────────

def _is_within_tolerance(a: float, b: float) -> bool:
    """두 값이 허용 오차(상대 + 절대) 이내인지."""
    if a == 0.0 and b == 0.0:
        return True
    ref = max(abs(a), abs(b))
    if ref == 0.0:
        return abs(a - b) <= RECON_TOL_ABS
    return abs(a - b) / ref <= RECON_TOL_PCT or abs(a - b) <= RECON_TOL_ABS


def _classify_drift(
    symbol: str,
    intended: float | None,
    ledger: float | None,
    truth: float | None,
) -> str:
    """drift 원인 분류 (휴리스틱)."""
    if intended is None:
        return "phantom"  # 의도하지 않은 포지션
    if ledger is None or truth is None:
        return "missing_view"
    delta_il = abs((intended or 0.0) - (ledger or 0.0))
    delta_lt = abs((ledger or 0.0) - (truth or 0.0))
    if delta_il > RECON_TOL_ABS and delta_lt <= RECON_TOL_ABS:
        return "unfilled_intent"
    if delta_lt > RECON_TOL_ABS and delta_il <= RECON_TOL_ABS:
        return "partial_fill_or_fee"
    return "unknown_drift"


def _append_log(entry: dict, path: Path = _RECON_LOG_PATH) -> None:
    """recon_log.jsonl append-only 기록."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


# ── A3: N-consistent-sample overwrite 안전장치 ───────────────────────

def _validate_truth_sample(
    symbol: str,
    truth_qty: float,
    ledger_qty: float | None,
    now: float,
) -> tuple[bool, str]:
    """truth 단일샘플 overwrite 여부 결정.

    Returns:
        (can_overwrite, reason)
        can_overwrite=True → N회 연속 일치 확인됨, overwrite 안전.
        can_overwrite=False → quarantine (의심 or 미확정).
    """
    # (1) sanity-check: truth==0 or 직전 대비 급변(>RECON_SANITY_PCT)
    prev = _prev_truth.get(symbol)
    if truth_qty == 0.0 and (ledger_qty or 0.0) > RECON_TOL_ABS:
        # truth 가 갑자기 0 → transient zero 의심
        _prev_truth[symbol] = truth_qty
        _truth_samples.pop(symbol, None)
        return False, "sanity_zero"

    if prev is not None and prev != 0.0:
        change_pct = abs(truth_qty - prev) / abs(prev)
        if change_pct > RECON_SANITY_PCT:
            _prev_truth[symbol] = truth_qty
            _truth_samples.pop(symbol, None)
            return False, f"sanity_jump({change_pct:.2f})"

    _prev_truth[symbol] = truth_qty

    # (2) 연속 N회 일치 추적
    sample = _truth_samples.get(symbol)
    if sample is None:
        _truth_samples[symbol] = _TruthSample(qty=truth_qty, count=1, last_ts=now)
        if RECON_CONFIRM_N <= 1:
            return True, "confirmed_n1"
        return False, "pending_n1"

    if abs(sample.qty - truth_qty) <= RECON_TOL_ABS:
        sample.count += 1
        sample.last_ts = now
    else:
        # 값이 바뀜 → 카운터 리셋
        _truth_samples[symbol] = _TruthSample(qty=truth_qty, count=1, last_ts=now)
        return False, "count_reset"

    if sample.count >= RECON_CONFIRM_N:
        return True, f"confirmed_n{sample.count}"
    return False, f"pending_n{sample.count}"


# ── 메인 reconcile ────────────────────────────────────────────────────

def reconcile(
    intended: dict[str, float],
    ledger: dict[str, float],
    exchange_truth: dict[str, float],
    now: float | None = None,
    log_path: Path = _RECON_LOG_PATH,
) -> ReconResult:
    """3-way 포지션 대조.

    Args:
        intended: 전략이 의도한 포지션 {symbol: qty}.
        ledger:   내부 장부 {symbol: qty}.
        exchange_truth: 거래소 실보유 (truth) {symbol: qty}.
        now: 타임스탬프 (테스트 주입용).
        log_path: recon_log.jsonl 경로.

    Returns:
        ReconResult — breaks, overwritten, action, quarantined.
    """
    if now is None:
        now = time.time()

    all_symbols = set(intended) | set(ledger) | set(exchange_truth)
    breaks: list[dict] = []
    overwritten: dict[str, float] = {}
    quarantined: list[str] = []
    action = "none"

    for symbol in sorted(all_symbols):
        i_qty = intended.get(symbol, 0.0)
        l_qty = ledger.get(symbol, 0.0)
        t_qty = exchange_truth.get(symbol, 0.0)

        # pairwise delta
        delta_it = abs(i_qty - t_qty)  # intended vs truth
        delta_lt = abs(l_qty - t_qty)  # ledger vs truth
        delta_il = abs(i_qty - l_qty)  # intended vs ledger

        max_delta = max(delta_it, delta_lt, delta_il)

        if _is_within_tolerance(l_qty, t_qty) and _is_within_tolerance(i_qty, t_qty):
            # 허용 오차 이내 — log only
            _append_log({
                "ts": now, "symbol": symbol, "event": "ok",
                "intended": i_qty, "ledger": l_qty, "truth": t_qty,
            }, log_path)
            continue

        # recon break 감지
        drift_type = _classify_drift(symbol, intended.get(symbol), ledger.get(symbol), exchange_truth.get(symbol))

        # A3: truth 단일샘플 overwrite 안전장치
        can_overwrite, confirm_reason = _validate_truth_sample(symbol, t_qty, l_qty, now)

        break_entry: dict[str, Any] = {
            "symbol": symbol,
            "delta_lt": delta_lt,
            "delta_it": delta_it,
            "delta_il": delta_il,
            "drift_type": drift_type,
            "intended": i_qty,
            "ledger": l_qty,
            "truth": t_qty,
            "can_overwrite": can_overwrite,
            "confirm_reason": confirm_reason,
        }

        if can_overwrite:
            # truth authoritative → ledger overwrite
            overwritten[symbol] = t_qty
            break_entry["action_reason"] = "ledger_overwritten"

            # 대형 delta → hard_derisk
            ref = max(abs(l_qty), abs(t_qty))
            if ref > 0 and (delta_lt / ref) > RECON_HARD_PCT:
                break_entry["action_reason"] = "hard_derisk(large_delta)"
                action = "hard_derisk"
            elif action != "hard_derisk":
                action = "soft_halt"
        else:
            # 의심 truth → quarantine, 재매매 차단
            quarantined.append(symbol)
            break_entry["action_reason"] = f"quarantine({confirm_reason})"
            if action != "hard_derisk":
                action = "soft_halt"

        breaks.append(break_entry)
        _append_log({"ts": now, "symbol": symbol, "event": "break", **break_entry}, log_path)

    result = ReconResult(
        breaks=breaks,
        overwritten=overwritten,
        action=action,
        quarantined=quarantined,
    )
    return result
