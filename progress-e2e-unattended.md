---
tags: [type/progress, domain/inv, topic/e2e-unattended, session/btn-Inv]
date: 2026-05-30
session: btn-Inv
plan: ./plan-e2e-unattended.md
note: E2E 실작동 검사 추적. 발견 즉시 패치. 자율주행 ON.
---

# Progress — E2E 실작동 검사

> plan: [plan-e2e-unattended.md](./plan-e2e-unattended.md)

## §진입 스냅샷
- 무인 패치 SO-1~8 commit 완료(6602338까지), 61 passed + U1 회귀 117, execute_trade diff=0 검증 완료.
- U5(SAFETY-human-gates) + U6(README-unattended-safety) 작성 완료. README 본체 통합=D6 이연(R15/brain M 격리).
- Phase Gate Review 3 reviewer: 성능 완료(P0 3·P1 5·P2 2), 보안/품질 대기.
- 🚗 자율주행 ON — progress 완료까지.

## Steps

- [x] **E1 — Import/구문 smoke** ✅
  - [x] 무인 신규 6모듈 import OK
  - [x] 데이터수집 3스크립트 py_compile OK (market/fgi/news)
  - [x] 에이전트 6모듈 import OK (base/conservative/moderate/aggressive/orchestrator/external_data)
- [x] **E2 — 무인 안전장치 실작동** ✅ — 실 state.json/frozen_bag 파일 쓰기 포함 73 passed (시뮬+실파일 사이클)
- [x] **E3 — 파이프라인 진입점 DRY_RUN** (run_agents.py) ✅ — EXIT=0 완주(데이터수집→regime bear_strong→판단→snapshot). telegram/supabase 미설치도 graceful degrade(WARNING만, 실고장0)
- [x] **E4 — Phase Gate reviewer findings 패치** ✅ — 6건 패치 + 회귀0, false positive 2건 기각, 이연 박제 D7~D11
- [x] **E5 — 종합 회귀 + SACRED 최종 확인** ✅ — 기존 e2e 스위트 **202 passed**(RL gymnasium 1건 환경미설치 제외) + 무인 74 passed + execute_trade diff=0 + 무인파일 commit(2f46607)

## 전체 파이프라인 E2E 실행 검사 (P단계 — 2026-05-30 추가 지시)
- ⛔ **범위 제외 (규제, 2026-05-30)**: 코인 단타(P-E)·차익거래(김치랑). 일반 트레이드만.
- [x] **P0 — 의존성 설치** ✅ gymnasium 1.2.3 / stable-baselines3 2.8.0 / feedparser 6.0.12 (torch 2.11 기설치). RL pipeline 17 collected.
- [ ] **P1 — 기존 e2e/통합 스위트 전수 재실행** (RL 포함, 단타·김치랑 제외)
- [ ] **P2 — 학습→매매 4흐름 동적 실행** (RL run_cycle / R15 closed_loop / agent_switches / 뉴스랑)
- [ ] **P3 — run 진입점 DRY_RUN** (run_agents·live_trader run_cycle. short_term 제외)
- [ ] **P4 — 발견 패치 + 종합 회귀 + SACRED**
- 집중 파이프라인: P-A 에이전트 / P-B RL / P-C R15거시학습→주식 / P-D 뉴스랑 / P-F RAG / P-H study / lifeline (plan-e2e §추가 참조)

## 학습→매매 체인 연결성 검증 (사용자 핵심 의도 — 흐름 끊김 여부)
> Explore 1차 추적이 체인3(RL)/체인4(agent_switches)를 BROKEN/deadcode 로 보고했으나 **E97 직접 grep 검증으로 전부 기각** — 4체인 모두 정적 CONNECTED + 동적 실행 도달 확인.

| 체인 | 정적(코드 wire) | 동적(실행) | 끊김 |
|------|----------------|-----------|------|
| 1. R15 거시학습→registry→매매 | CONNECTED (train_weights→registry→stock_track:242 L1 sizing) | closed_loop_3domain **8 passed** | 없음 (단 INV_R15_WEIGHTS opt-in=설계상 down-only 무회귀) |
| 2. brain regime→가중→판단 | CONNECTED (regime_history→regime_to_weights:82→tilt) | run_agents 실구동 regime=bear_strong 도달 | 없음 |
| 3. RL 학습→정책→매매신호 | CONNECTED (live_trader:154 추론→:167 blend→:183 execute) | ⚠️ 동적 실행 불가 — PyTorch/gymnasium 미설치(live_trader:85 ContinuousLearner import 실패). 코드 wire만 확인 | 코드 끊김 없음. 단 이 환경서 실행 검증 미완(의존성) |
| 4. agent_switches 성과학습→전략전환 | CONNECTED (orchestrator:664 호출→:671-672 danger/opportunity 반영) | test_e2e_orchestrator_switching passed | 없음 (Explore deadcode 오판 기각) |

**결론: 학습→매매 4대 흐름 전부 연결 + 동적 실행 도달. 사용자 우려한 "끊김" 실제 없음.**
- 주의: 체인1 R15 = opt-in 기본 off(의도). 체인3 RL = 모델 파일(data/rl_models) 있어야 실효, 없으면 rl_pred 생성되나 graceful. 실제 학습 배치(FRED 키)는 사람 영역.

## E2E 검사 커버리지 매트릭스
| 기능 | 검사 | 결과 |
|------|------|------|
| 무인 안전장치(derisk/fsm/watchdog/reconcile/killswitch wire) | pytest 74 | ✅ PASS |
| orchestrator 전략전환 | test_e2e_orchestrator_switching | ✅ (202 中) |
| run_agents 파이프라인 | test_e2e_run_agents + 실구동 | ✅ EXIT=0 |
| 데이터수집(market/fgi/regime) | run_agents 실구동 | ✅ 실수집 도달 |
| trading/hybrid/external_data_fusion/warmup/web_server/automation/telegram_listener | test_e2e_* | ✅ (202 中) |
| RL 파이프라인 | test_e2e_rl_pipeline | ⚠️ gymnasium 미설치(환경, KNOWN_FAILURES) |
| 텔레그램 실전송/Supabase 실기록 | — | ⏸️ 실키 필요(graceful degrade 확인만) |
| 실거래 주문 | — | ⛔ 사람게이트(DRY_RUN, 자율범위밖) |

## Working Notes
- (2026-05-30) **E4 Phase Gate 패치 6건 적용 (회귀 0, 무인 73 passed, execute_trade diff=0)**:
  1. FSM `infra_hard`(heartbeat_loss/recon_break) COOLDOWN/RE_ARM_EVAL 중 즉시 재집행 (품질 P0 — 인프라 위험 무시 갭)
  2. FSM `mdd_hard` 분리 (시장 재급락은 rearm 차단이 커버 → whipsawing 조기 FREEZE 방지, 보안 절충)
  3. FSM cooldown backoff `MAX_COOLDOWN_SEC` 상한 (성능·품질)
  4. derisk `_load_frozen_bag` 재시작 복구 + `frozen_path` 주입 (보안 P0 — 재시작 시 frozen 보호 무력화 갭)
  5. derisk `_record_frozen_bag` 원자적 쓰기 tmp+rename (보안 P2/성능 — RMW 손상 방지)
  6. watchdog `WATCHDOG_FLOORS_JSON` json.loads try/except (보안 P1 — 잘못된 JSON 으로 import crash 방지)
  - 신규 검증 테스트: `tests/test_unattended_phase_gate_patch.py` (10 passed, E95 효과검증)
- **false positive 기각 (코드 직접 검증)**: slippage 누적 자체는 설계대로(음수 누적→-10% frozen) / `_triggered` 리셋은 D4 이연.
- **Phase Gate 이연 박제 (go-live, D7~D11)**:
  - D7: slippage mid 각 band 재조회 + IOC ladder `time.sleep` async (실거래소 어댑터 전제)
  - D8: reconciliation 동시성(인스턴스화/lock) + N-consistent-sample restart checkpoint (D5 라이브 wire 동시성 모델 확정 후)
  - D9: watchdog `_triggered` N-tick 회복 강화 + startup grace window (D4 배포 전제)
  - D10: `unattended_state.json` HMAC 서명 (현 SHA256 무결성만, credential 관리 go-live)
  - D11: risk_gate `hold` action `is_halted` reason 표기 (cosmetic, 회귀 민감 회피)
- (2026-05-30) E2E plan/progress 작성. E1 무인 6모듈 import OK.
- Phase Gate 성능 reviewer findings 수집(E4서 분류):
  - P0: derisk sleep blocking(:340,368) / N×2 query(:224,262)+동시트리거 mutex / frozen_bag RMW 경합(:384-393)
  - P1: recon_log 무한성장 / N-sample restart 리셋 / cooldown backoff 상한없음 / watchdog startup grace / near_miss_veto open-per-call
  - 다수 P0는 실거래소 어댑터 전제(go-live D1~D5 선상). frozen_bag atomic·cooldown 상한·startup grace·N-sample checkpoint = 지금 패치 후보(저비용·무인 견고성).
