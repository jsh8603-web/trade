---
tags: [type/plan, domain/inv, topic/e2e-unattended, session/btn-Inv]
date: 2026-05-30
session: btn-Inv
progress: ./progress-e2e-unattended.md
parent: ./plan-unattended-ops.md
note: 무인 패치 + 주요 파이프라인 E2E 실작동 검사. SO-7 무인 시뮬과 별개 = 실시스템 DRY_RUN 실행. 발견 즉시 패치.
---

# Plan — E2E 실작동 검사 (주요 파이프라인 + 무인 안전장치)

> 사용자 지시(2026-05-30): "주요 파이프라인 돌아가는지 e2e 검사 + 검사 plan/progress 만들고 끝날때까지 자율주행."
> SO-7 pytest 무인 시뮬과 별개 = **실시스템 파이프라인을 DRY_RUN으로 실제 구동**. detect→patch 루프.

## 목표
주요 기능이 실제로 import·실행·연결되는지 DRY_RUN 실작동으로 확인하고, 발견되는 고장을 즉시 패치한다. 회귀 0 + SACRED 유지.

## 불변식 (SACRED)
- ⛔ execute_trade.py diff=0, live_trader run_cycle 미변경, 전량 시장가 청산 금지.
- ⛔ DRY_RUN=true 유지, 실거래 flip 금지. 실주문 0.
- ⛔ R15/brain M파일 6종(README.md·core/brain/regime_*·portfolio_orchestrator·progress.md·progress-inv-v2.md) 미변경.
- de-risk 경로 LLM 독립 유지. core/ off 기본 보존.

## 검사 단계 (Phase)

### E1 — Import/구문 smoke (전 핵심 모듈 import + __main__ self-test)
- 무인 신규: derisk_executor·unattended_fsm·watchdog·reconciliation·risk_gate·fallback_policy
- 데이터수집: collect_market_data·collect_fear_greed·collect_news (구문/import만, 외부 API 미호출 또는 graceful)
- 에이전트: base_agent·conservative·moderate·aggressive·orchestrator·external_data
- 합격: import 0 error, self-test 있는 모듈 통과. 실패 → 즉시 패치.

### E2 — 무인 안전장치 실작동 (실파일·실상태 사이클)
- derisk_executor: stub exchange로 cancel→query→IOC ladder→frozen bag 실호출(DRY_RUN). frozen_bag.json 실기록.
- unattended_fsm: 실 state.json 원자쓰기·checksum·load실패→HARD_DERISK·6상태 1사이클·PERMANENT_FREEZE 자정탈출.
- watchdog: heartbeat 실파일 stale→derisk 트리거(트리거 함수 mock). startup grace.
- reconciliation: 3-way 실대조·N-consistent·truth overwrite·recon_log 실기록.
- KillSwitch/H27 wire: auto_derisk_due→FSM 실연결(run_agents.py 진입점 DRY_RUN 경로).
- 합격: 각 사이클 실파일 산출 + 예외 0. 발견 → 즉시 패치.

### E3 — 파이프라인 진입점 DRY_RUN (run_agents.py 레거시 경로)
- run_agents.py를 DRY_RUN=true로 구동(외부 API graceful degrade 허용). orchestrator 전략전환 로직 도달 확인.
- KillSwitch wire가 파이프라인서 실호출되는지 확인.
- 합격: 진입점이 crash 없이 의사결정까지 도달(실주문 0). 발견 → 즉시 패치.

### E4 — Phase Gate 반영 패치 (reviewer findings)
- 보안/품질/성능 reviewer P0/P1 중 "지금 패치" 분류분 적용. go-live 의존분(실거래소 어댑터)은 D1~D5 이연.
- 각 패치 후 회귀(무인 61 + U1 117) 재확인.

### E5 — 종합 회귀 + SACRED 최종 확인
- 전체 무인 테스트 + U1 회귀 재실행, execute_trade diff=0 재확인, M파일 6종 혼입 0.

## 자율주행
- progress-e2e-unattended.md 완료까지 사용자 확인 없이 자율 완주. 발견 즉시 패치(detect→patch).
- 자율 범위 밖: 실거래 flip·자본상향·출금권한·외부 실 API 키 필요 작업 → 도달 시 정지+보고.

---

## 추가: 전체 파이프라인 E2E 실행 검사 (P 단계 — 2026-05-30 사용자 추가 지시)

> "파이프라인이 더 있는지 보고 e2e 파이프라인들을 테스트할 계획 + 의존성 설치해서 run 확인."
> 기존 mock e2e(202 passed)와 별개 = **실제 흐름이 끝까지 안 끊기고 도는지** 동적 실행.

### 파이프라인 인벤토리 (6 run 스크립트 + 22 e2e/통합 테스트)
> ⛔ **범위 제외 (규제 — 사용자 확정 2026-05-30)**: 코인 단타(P-E)·차익거래(김치랑 김프). 일반 트레이드만 검사.

| # | 파이프라인 | 진입점 | 흐름 성격 | 범위 |
|---|-----------|--------|---------------|:---:|
| P-A | 에이전트 자율매매 | `scripts/run_agents.py` | orchestrator 전략전환 + agent_switches 성과학습 → 매매 | ✅ |
| P-B | RL 하이브리드 | `rl_hybrid/rl/live_trader.py` run_cycle | RL 학습→추론→DecisionBlender 융합→매매 | ✅ |
| P-C | 거시/지표 학습(R15) | `scripts/train_weights.py` + stock_track | FRED→glasso→registry→stock_track L1 sizing | ✅ |
| P-D | 뉴스랑 외부수집 | `agents/external_data.py` + collect_rss/x/social | 11소스 병렬수집→data fusion 점수 | ✅ |
| P-E | ~~단타봇~~ | ~~short_term_trader.py~~ | ~~뉴스/급등락/고래 3전략~~ | ⛔ 규제제외 |
| P-F | RAG embed chain | `scripts/run_embed_chain.sh` | 임베딩→메모리→RAG PIT | ✅ |
| P-G | ~~김치랑(차익)~~ / lifeline | ~~kimchirang~~ / lifeline_e2e | ~~김프 차익~~ / 생존 모니터 | ⛔김치랑 / ✅lifeline |
| P-H | study pipeline | `scripts/build_panel.py` + study | 패널 빌드→통계 검증 | ✅ |

### P0 — 의존성 설치 ✅ (완료 2026-05-30: gymnasium 1.2.3 / stable-baselines3 2.8.0 / feedparser 6.0.12, torch 2.11 기설치)
### P1 — 기존 e2e/통합 스위트 전수 재실행 (RL 포함, 단타·김치랑 제외, KNOWN_FAILURES 외 0 fail)
### P2 — 학습→매매 4흐름 동적 실행 (RL run_cycle / R15 closed_loop / agent_switches penalty / 뉴스랑 fusion)
### P3 — run 스크립트 진입점 DRY_RUN (run_agents·live_trader run_cycle, 실주문 0. short_term 제외)
### P4 — 발견 패치 + 종합 회귀 + SACRED (execute_trade diff=0, live_trader run_cycle 본체 미변경, R15/brain M파일 6종 격리)

### 제약
- 외부 실 API 키(Upbit/Telegram/Supabase/FRED) 없으면 graceful degrade 확인까지(실전송·실주문=사람게이트).
- ⛔ SACRED 유지. 발견 고장 즉시 패치(detect→patch). 완료까지 자율주행.
