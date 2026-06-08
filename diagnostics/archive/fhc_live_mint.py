# -*- coding: utf-8 -*-
"""FHC 발권 LIVE 단독 검증.

★정정(2026-06-06): 직전 "메인 멈춰야 429 회피"는 오진. 429 는 oauth-beta 헤더 + Claude Code
system 누락 코드문제였고 v1.39.0(7ce667d)에서 fix → 메인 활성 중 동시 호출에도 LIVE 통과.
abstain 이 나오면 429 가 아니라 audit reject(빈 falsification_metric 등 LLM 응답 품질)다.

실행(repo 루트에서): PYTHONPATH=. python diagnostics/p2-coin-study/fhc_live_mint.py
"""
import os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from core.assume.loop_factory import build_active_loop
from core.brain.macro_schema import Bloc, MacroView, RegimeEstimate, RegimeLabel, ViewStatus

est = RegimeEstimate(bloc=Bloc.USD, regime_now=RegimeLabel.STAGFLATION, confidence_now=0.3,
                     evidence={"growth_z": -0.4, "infl_z": 1.1})
view = MacroView(regimes={Bloc.USD: est}, status=ViewStatus.FRESH, as_of_ts=0.0)

loop = build_active_loop(use_claude=True)   # ClaudeProvider OAuth + 5/15/45 backoff retry
pc = loop.run_cycle(view, numeric_revision=1.0, query="stagflation macro asset allocation outlook")

if pc:
    print("=== LIVE 발권 성공 (실 Claude OAuth) ===")
    print("thesis    :", pc.thesis)
    print("direction :", pc.card.direction, "| mediator:", pc.card.mediator.observable_ref)
    print("falsif    :", pc.card.falsification_metric)
    print("counter   :", pc.counter_thesis)
    print("kind/cap  :", pc.card.kind, pc.card.bonus_cap, "(probationary=자본0)")
    print("audit     :", pc.audit.reason)
else:
    print("abstain — LLM 응답이 약해 audit reject(빈 falsification_metric 등) 또는 summon 차단.")
    print("→ 429 아님(v1.39.0 fix). reports 컨텍스트가 있으면 발권 품질↑. 메인 멈출 필요 없음.")
