# audit-goldenrule-unattended.md — GOLDEN RULE 감사 게이트 (Phase Unattended)

작성자: Worker (harness2-wf SO-8)
기준: taskspec-phase-unattended.txt SO-8 + plan-unattended-ops.md U2~U4 + 자문 3R 수렴 결과

---

## §1. 자문 수렴 5축 1:1 커버 대조

| 축 | 자문 수렴 결론 | 구현 산출물 | 커버 여부 |
|----|----------------|-------------|-----------|
| ① derisk_executor | LLM 독립 IOC 단계청산 + fail-safe (절대 fail-open 금지) | `core/derisk_executor.py` (SO-1+3) — DeriskExecutor.cancel_only / derisk_to_floor / _escalate_liquidation | ✅ COVERED |
| ② re-arm FSM | 6상태 + hysteresis + 지수backoff + PERMANENT_FREEZE 무인탈출 + fail-safe(load실패=HARD_DERISK) | `core/unattended_fsm.py` (SO-2) — UnattendedStateMachine 6상태 전이 + 원자적 state.json + checksum | ✅ COVERED |
| ③ watchdog | 독립 프로세스 + 봇과 독립 credential + heartbeat stale→derisk + SPOF 완화 stub | `scripts/watchdog.py` (SO-4) — WatchdogProcess + write_heartbeat + register_native_stop stub + revoke_bot_api_key stub | ✅ COVERED |
| ④ reconciliation | 3-way(intended/ledger/truth) + ⛔ A3 단일샘플 overwrite 금지 (sanity-check + N회 연속) | `core/reconciliation.py` (SO-5) — reconcile() + _validate_truth_sample(N-consistent) + quarantine | ✅ COVERED |
| ⑤ thin-book frozen bag | IOC band 확대 + 누적 슬리피지 -10% → frozen bag 마킹 + 매매중단 | `core/derisk_executor.py:_escalate_liquidation` (SO-3) — LADDER_BANDS + MAX_SLIPPAGE + _record_frozen_bag | ✅ COVERED |

**결론: 자문 수렴 5축 전부 1:1 커버. 누락 없음.**

---

## §2. plan-unattended-ops.md U2~U4 대조

| 계획 항목 | 내용 | 구현 확인 |
|-----------|------|-----------|
| U2 | DeriskExecutor (cancel_only + derisk_to_floor + IOC ladder) | SO-1+3 완료 (9c88c2e + 1b1fa6b) |
| U2 | UnattendedStateMachine (6상태 FSM + hysteresis + backoff) | SO-2 완료 (1b1fa6b) |
| U3 | watchdog / heartbeat dead-man's switch | SO-4 완료 (42fb6c2) |
| U4 | reconciliation (3-way + N-consistent + recon_log) | SO-5 완료 (d9d79fc) |
| U1/U2 | KillSwitch.auto_derisk_due → FSM wire | SO-6 완료 (711b5c5 + a3ef21b) |
| U2/U4 | H27 record_halt_entry 무인 anchor | SO-6 완료 (711b5c5) |
| — | E2E 통합 동작게이트 (사람 개입 0 자율 완주) | SO-7 완료 (ac9e50b) |

**결론: U2~U4 전 항목 구현 완료.**

---

## §3. SACRED 준수 확인

| SACRED 항목 | 기준 | 실제 확인 |
|-------------|------|-----------|
| execute_trade.py 미변경 | git diff HEAD -- scripts/execute_trade.py = "" | ✅ diff=0 (E2E-6 pytest 검증) |
| live_trader run_cycle 미변경 | rl_hybrid/rl/live_trader.py 미변경 | ✅ 이 Phase 에서 미변경 |
| 전량 시장가 청산 금지 유지 | naked market order 사용 금지 | ✅ submit_ioc_limit 만 사용 (market order 0) |
| de-risk LLM 독립 | brain/judge/llm/consensus/HRP import 0 | ✅ derisk_executor + unattended_fsm + watchdog + reconciliation 전부 LLM import 0 (AST 정적검사 pytest 통과) |
| DRY_RUN 기본값 보존 | .env DRY_RUN=true 기본 | ✅ 코드 변경 없음, 안전장치 변수 존재 확인 (E2E-5) |
| 실거래 flip 사람 게이트 | DRY_RUN=false 자동화 금지 | ✅ 이 Phase 에서 flip 없음 (SACRED 범위 밖) |
| M파일 6종 혼입 금지 | README/core/brain/* /portfolio_orchestrator/progress*.md | ✅ git add 격리 — M파일 6종 add/commit 0 |
| core/ off 기본 byte-identical | INV_CORE_GATE 기본 off | ✅ 기본 off 보존, 옵트인 구조 |

**결론: SACRED 전 항목 준수.**

---

## §4. 이연 항목 (Worker 확인 — Supervisor 박제 전담)

아래 항목은 구현 범위 밖으로 이연. Supervisor가 `progress-unattended-ops.md ## 이연 항목` 에 박제.

| # | 이연 항목 | 사유 |
|---|-----------|------|
| D1 | **INV_UNATTENDED_FSM wire 라이브 경로 실연결** | 현재 wire 가 `scripts/run_agents.py`(레거시 LLM 진입점) INV_CORE_GATE 블록 내에 위치. 라이브 파이프라인 `run_agents.sh → agents/orchestrator.py` 에 직접 연결 필요. go-live 시 추가 (SACRED: 실거래 flip=사람 게이트, 현 DRY_RUN·core off 범위 밖). |
| D2 | **거래소 native stop 실연결** (register_native_stop) | Upbit 현물 조건부주문 제약 / KIS stop-loss 제약 → go-live 이연. stub 경계 문서화됨 (`scripts/watchdog.py:register_native_stop`). |
| D3 | **revoke_bot_api_key 실연결** (SPOF A4 궁극 fail-safe) | master credential 분리 필요 → go-live 이연. stub 경계 문서화됨 (`scripts/watchdog.py:revoke_bot_api_key`). |
| D4 | **watchdog 독립 프로세스 배포** | 실 credential(WATCHDOG_UPBIT_KEY/SECRET) + 프로세스 관리(systemd/supervisor) 설정 필요 → go-live 이연. |
| D5 | **reconciliation cadence wire** | 매 cycle + 매 fill 이벤트 후 reconcile() 호출 → 라이브 경로 직접 wire 필요 (현재 독립 모듈로 완성, 호출 지점 go-live 연결 이연). |

---

## §5. 커버리지 요약

- SO-1~7 신규 테스트: 54 passed
- U1 회귀 (risk_gate/kill/fallback): 117 passed
- GOLDEN RULE 5축 커버: 5/5 ✅
- SACRED 항목: 8/8 ✅
- 이연 항목: 5건 (D1~D5, Supervisor 박제 전담)
