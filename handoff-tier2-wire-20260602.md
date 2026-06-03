---
tags: [handoff, inv, tier2, wire, test-readiness, self-contained]
date: 2026-06-02
session: btn-Inv
purpose: Tier2 Phase1(W1~W4 engine 배선) 완료 핸드오프 — clear 후 이 파일로 재개. 다음=P2 Test2a
entry: 이 파일 1독 → progress-test-readiness.md(Tier2) → plan-test-readiness.md §P1/P2
---

# 핸드오프 — Tier2 Phase1(engine 배선) 완료, 다음 P2 Test2a (자기완결)

> **push 금지**(사용자 지시 유지). Python=`/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe`.

## 0. 한 줄 현황
수익률 테스트 마스터플랜 **Tier2 Phase1(W1~W4 배선) 완료** — `backtest/engine.py`가 이제 결정→사이징→게이트→judge 진짜 설계경로를 탐(harness2-wf, 24/24 passed, 도메인 회귀 delta=0). 다음 = **P2 Test2a**(시계열 주입 수익률 → 방법론 vs 코드 진단).

## 1. 큰 그림 (왜)
- **목표**(사용자): 수익률 손실 시 "방법론 결함"인지 "코드(상수/가중치) 결함"인지 원인 분리.
- Test1(둔갑 자문)=방법론 OK(Tier1 완료). Test2=코드 진단. **Test2 선결=배선**(engine이 95% 박기만 하던 것 → 진짜 로직). ← **Phase1으로 완료**.
- 다음 P2 = 결정론 경로(LLM no-op)로 시계열 주입 수익률 시뮬 → 손실이 (a) 방법론(W0 자문 OK 받음) vs (b) 코드 상수/가중치 과도 중 무엇인지 attribution.

## 2. ★Phase1 완료 내역 (W1~W4, harness2-wf)
W0 자문(gemini+claude 수렴+코드 falsify) → 설계 확정 → harness2 4 SO 구현. 전 SO Verifier PASSED + O12 git_head 매칭.

| SO | commit | 결과 |
|---|---|---|
| W1 사이징 | `34f0e1e` | use_risk_pipeline hard-branch(`_run_legacy` verbatim 동결=off byte-identical) + gross×weight 합성(`gross=clip(target_vol/realized_vol,lo,hi)`, `trade_value=capital*gross*weights[asset]`). G1 7/7, mutation-kill |
| W2 게이트 | `3db9162` | PortfolioState 회계객체 + GatedOrderRouter.submit(via_gate=True) 매 거래. REJECT→skip. NAV 2분리(prev_close/intra_bar). 13/13, G4 |
| W3 judge | `9a24eb1` | 공통 judge hook 매 bar 호출 + coin bypass a=1.0(fail-open). 천장 final≤L1. 18/18, G5 sensitivity |
| W4 golden+gates | `9cf742c` | golden-master + per-bar state-vector checksum(SHA-256[:16] 6필드) + G1~G7 통합. 24/24, 도메인 회귀 delta=0 |

- **테스트**: `tests/test_engine_wire.py` 24/24 passed.
- **Sacred 준수**: `_run_legacy` 동결 / 부품(size_portfolio·RiskGate·GatedOrderRouter·judge) 무수정(호출만) / judge 천장 / go-live·execute_trade 미접촉.
- **SR Pre-Review(C) ACCEPT 보강 반영**: per-bar state-vector checksum(G1/G2 oracle, Test2a attribution 재사용) / mutation-kill(G3/G5, size_portfolio 죽은stub mutant→G3 FAIL로 tautology 차단) / NAV-basis 2분리 / entry_bar off-by-one 방지.
- ★engine 동작: `use_risk_pipeline=False`(기본)=`_run_legacy` 옛 코드 그대로(byte-identical) / `True`=신 파이프라인. P2는 `True`로 돌림.

## 3. ★다음 = P2 Test2a (착수점)
> progress-test-readiness.md "Phase P2". `model: opus`.
- **무엇**: coin/거시 substrate on + `use_risk_pipeline=True` + 과거 시계열 주입 → BacktestEngine.run → equity_curve / 수익률 / MDD.
- **진단**: 손실 시 (a) 방법론(W0 자문 OK 받은 설계) vs (b) 코드 상수/가중치 과도. ★per-bar state-vector checksum으로 "어느 bar에서 divergence"인지 bar단위 attribution(신호 vs 사이징 vs 게이트).
- **산출**: 결정론 경로 성능 리포트 + 진단(어느 상수·가중치 의심인지).
- 이후 P3(judge 재설계, down-only 완화 분기 자문)·P4(주식 full)·P5(리포트).

## 4. harness2 부산물 (자산화됨)
재사용성 버그 3종 근본 fix(`lib/teammate-spawn.sh`): SACRED vaultvoice 잔재 동적화 / watchdog KICKOFF Bash 실제 invoke 강제 / watchdog Bash timeout=590000 명시. → promotion-log K(2026-06-02) + `.harness2/improvement-registry.md`.

## 5. 진입 (다음 세션)
1. 이 파일 → 2. `progress-test-readiness.md`(Phase1 [x]·P2 체크리스트) → 3. `plan-test-readiness.md §P2` → 4. `backtest/engine.py`(use_risk_pipeline 경로) + `tests/test_engine_wire.py`.
- **첫 작업 = P2 Test2a** 설계(시계열 fixture·substrate on·checksum attribution). ⛔ go-live(DRY_RUN=false·execute_trade)=사람 게이트.
