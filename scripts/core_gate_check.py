#!/usr/bin/env python3
"""scripts/core_gate_check.py — Phase I 라이브 core/ 게이트 (WP1/2/3/4).

run_agents.sh Phase 3 가 execute_trade 직전 호출. 신규 core/ 안전 백스톱(RiskGate)+
학습 로깅(MemoryLayer.store_decision)+거시 레짐 chain(RegimeClassifier) 을 라이브 경로에 연결.

stdout: 'OK' | 'REJECTED'  (REJECTED 면 셸이 DECISION=hold 로 차단)
stderr: [core-gate] 진단 로그
예외/누락 = OK 출력(graceful, 레거시 경로 유지). 실주문/execute_trade 미변경.

usage: core_gate_check.py <decision> <amount> <volume> <market> <confidence_pct>
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def main() -> int:
    decision = sys.argv[1] if len(sys.argv) > 1 else "hold"
    amount = sys.argv[2] if len(sys.argv) > 2 else "0"
    volume = sys.argv[3] if len(sys.argv) > 3 else "0"
    market = sys.argv[4] if len(sys.argv) > 4 else "KRW-BTC"
    conf_pct = sys.argv[5] if len(sys.argv) > 5 else "0"

    if decision not in ("buy", "sell"):
        print("OK")
        return 0

    try:
        from core.risk_gate import RiskGate, VerdictType
        size = float(amount or 0) if decision == "buy" else float(volume or 0)
        verdict = RiskGate().check(action=decision, proposed_size=size)

        try:  # WP3: 결정 로깅(S9) — 학습 메모리
            from core.brain.memory_layer import MemoryLayer
            MemoryLayer().store_decision(
                decision=decision, reason="", asset=market,
                confidence=float(conf_pct or 0) / 100.0,
            )
        except Exception as me:
            sys.stderr.write(f"[core-gate] memory 로깅 예외(무시): {me}\n")

        try:  # WP4: 거시 레짐 chain (FRED 있으면 실데이터, 없으면 stub)
            from core.brain.regime_classifier import RegimeClassifier
            fk = os.environ.get("FRED_API_KEY", "")
            if fk:
                from core.brain.fred_adapter import RealFredAdapter
                clf = RegimeClassifier(usd_adapter=RealFredAdapter(api_key=fk))
            else:
                clf = RegimeClassifier()
            mv = clf.classify()
            st = getattr(getattr(mv, "status", None), "value", "?")
            sys.stderr.write(
                f"[core-gate] 거시 레짐 chain: status={st} fred={'real' if fk else 'stub'}\n"
            )
        except Exception as re:
            sys.stderr.write(f"[core-gate] 레짐 예외(무시): {re}\n")

        sys.stderr.write(f"[core-gate] RiskGate {verdict.verdict.value}: {verdict.reason}\n")
        print("REJECTED" if verdict.verdict == VerdictType.REJECTED else "OK")
    except Exception as ge:
        sys.stderr.write(f"[core-gate] 예외 → 레거시 경로 유지: {ge}\n")
        print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
