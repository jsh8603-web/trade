---
tags: [type/progress, domain/inv, topic/unattended-ops, session/btn-Inv]
date: 2026-05-30
session: btn-Inv
plan: ./plan-unattended-ops.md
handoff: ./handoff-unattended-ops-20260530.md
note: 무인 자동운영 안전 패치 진행 추적. 루트 progress.md·progress-inv-v2.md 미변경(격리 신규 파일).
---

# Progress — 무인 자동운영 안전 패치

> plan: [plan-unattended-ops.md](./plan-unattended-ops.md) · 인계: [handoff-unattended-ops-20260530.md](./handoff-unattended-ops-20260530.md)

## §진입 스냅샷
- 다음 작업: **harness2 SO-1~8 자율 구동 중** — dispatch 완료(Worker-2/Verifier-2/StandbyA·B/watchdogU, model sonnet/haiku). SR Pre-Review C ACCEPT(A1~A5 하드닝 taskspec SO-2/4/5 반영). Supervisor IDLE, watchdog phase_complete 완료알림 대기.
- ⛔ 작업트리 격리: R15/brain 미커밋 M파일 6종(README·core/brain/regime_*·portfolio_orchestrator·progress·progress-inv-v2) = 타작업, Worker/Standby add 금지(taskspec + Worker/Standby.prompt 박음).
- 🚗 **자율주행 ON (2026-05-30 사용자 지시, progress 완료까지)**: harness2 SO-1~8 → U5 → U6 readme → 압축 → U7 E2E 실기능 자율 완주. flag=`.harness2/.autopilot-unattended`. 실거래 flip·자본상향·출금권한 도달 시만 정지+보고.
- U1 완료(KillSwitch.unattended+auto_derisk_due, 회귀 0). U5·U6=sonnet direct(harness 후).
- 전제: DRY_RUN=true·core/ off 유지. 실거래 영향 0. 실거래 flip=사람 게이트(범위 밖).
- 자문 3R 수렴 완료(gemini+claude). 코드 갭 조사 완료(Explore).
- harness2 팀명 재사용: h2wf-Inv-p0 (기존). SACRED: execute_trade.py·live_trader 미변경, 전량청산 금지 유지, de-risk LLM 독립.

## Steps

- [x] **U1 — KillSwitch 무인화** · `model: opus` · P0 ✅ (2026-05-30)
  - `core/risk_gate.py` KillSwitch: `unattended` 플래그(env RISK_UNATTENDED 기본 true) + `auto_derisk_due()` 즉시 트리거 신호 추가. SACRED 주석 재정의(전량 시장가 청산 금지 유지 + 무인 de-risk-to-floor는 U2 derisk_executor 집행). confirm()은 attended resume 경로로 잔존.
  - 검증: 스모크 4/4 PASS(무인 HALTED→auto_derisk_due=True / attended confirm 경로 유지 / env override). 회귀: pytest risk_gate·kill·fallback 116 passed 0 fail. (H27 wire는 U2 derisk_executor에서 anchor 전환과 함께.)
- [ ] **U2 — derisk_executor 신규** · `model: opus` (골격) → 분량 시 `wf: harness2` · P0
  - LLM비의존 통합 de-risk 집행기 + soft/hard tier + 자동 re-arm 상태기계(hysteresis·지수backoff·일일상한).
  - 검증: 무인 HALT→de-risk→re-arm 사이클 시뮬, whipsawing 가드, 회귀 0.
- [ ] **U3 — dead-man's switch / watchdog** · `wf: harness2` · P0~P1
  - heartbeat 실감시 daemon + 끊기면 derisk_executor 트리거 + 거래소 native stop 보험.
  - 검증: heartbeat-loss→자동 de-risk 트리거, watchdog 다중화.
- [ ] **U4 — reconciliation + thin-book escalation** · `wf: harness2` · P1
  - 3-way reconcile(truth-authoritative) + thin-book IOC ladder/frozen bag(U2 통합).
  - 검증: recon-break→soft-halt, thin-book→frozen bag.
- [ ] **U5 — 최소 사람 게이트 명문화** · `model: sonnet` · P1
  - 출금 air-gap·capital 수동·core/격리 admission·strangler-fig 문서/config.
- [ ] **U6 — readme.md patch** · `model: sonnet`
  - 무인 운영 안전 아키텍처 readme 반영(KillSwitch 자동화·derisk_executor·watchdog·reconciliation·신규 불변식·사람 게이트).
- [ ] **압축** · U6 완성 판단 후 (사용자 지시 2026-05-30: unit 테스트 통과+readme 갱신=완성 판단 시)
- [ ] **U7 — 압축 후 E2E 실기능 검증 + 즉시 패치** · `model: sonnet` · 마지막
  - 주요 기능 DRY_RUN 실작동 테스트(데이터수집·에이전트·orchestrator·de-risk·watchdog·reconciliation·KillSwitch wire) — SO-7 무인 시뮬과 별개 실시스템 E2E. 발견 즉시 고장 패치(detect→patch). 회귀 0 + SACRED 유지.
  - 압축 후 resume 진입점 = 본 U7 (자율주행 ON 지속).

## Working Notes
> [ckpt-202605300825:btn-Inv]
> - **마지막 결정**: SO-7 PASS(7/8). 무인 SO-1~7 신규 54 passed, U1 회귀 117 passed, execute_trade.py diff=0. commit: SO-1+3 9c88c2e / SO-2 1b1fa6b / SO-4 42fb6c2 / SO-5 d9d79fc / SO-6 711b5c5(wire)+a3ef21b(risk_gate U1) / SO-7 ac9e50b. 검증=Supervisor 흡수(Verifier in-process idle 반복). 인프라 fix 3건: watchdog stale 360→1200 + silent-death 비활성(h2-watchdog.sh), race tmo 300→900+blocked전 재확인(teammate-spawn.sh+Worker.prompt).
> - **다음 의도**: StandbyA SO-8(GOLDEN RULE 감사 audit-goldenrule-unattended.md + test_unattended_golden_rule.py + ev:phase_complete) 검증요청 처리 → SO-8 PASS=phase_complete → Phase Gate Review(security/quality/perf 3 reviewer Agent model:sonnet 병렬) + SR Post(mode A spawn-one) → U5(최소 사람게이트 명문화 sonnet)/U6(readme patch sonnet)/압축/U7(E2E 실기능 테스트+즉시패치).
> - **동기화 필요**: ⛔ 라이브 wire 미연결 — INV_UNATTENDED_FSM 이 run_agents.py 레거시 진입점, 라이브 orchestrator.py 실연결은 go-live 이연(SO-8 박제). autopilot ON(.harness2/.autopilot-unattended). 팀 h2wf-Inv-p0, active Worker=StandbyA(Worker-2 stall 종료), watchdog 다수 사망(stale fix 후 cap 정상). 검증 흐름=StandbyA commit→Supervisor 검증요청 SendMessage→Supervisor pytest 독립검증+다음 SO 지시. 작업트리 R15/brain M파일 6종 격리 유지(README·core/brain/*·portfolio_orchestrator·progress·progress-inv-v2).
- (2026-05-30) 자문 3R 수렴 + 코드 갭 확정. plan/progress/handoff 작성.
- (2026-05-30) U1 코드 정밀 확인 완료 — 설계방향 확정:
  - `risk_gate.py:372` `confirm()` 호출 주체 부재 → 무인 영구동결. `fallback_policy.py:63` H27 `_last_confirm_ts is None` → 무인은 confirm 없어 타임아웃 영원히 미발동.
  - **U1 설계방향**: (a) SACRED `자동 전량청산 금지` **유지**(전량 시장가 투매 footgun 보존), (b) `자동 de-risk-to-floor`(단계 부분축소+IOC+frozen bag) 추가 = 양립, (c) H27 anchor를 `confirm`→`HALT 진입 시점`(`_halted_since`)으로 전환해 무인 자동발동, (d) KillSwitch에 `unattended` 모드 플래그 + 자동 de-risk 트리거 신호 경로. 실 IOC 집행/re-arm 상태기계는 U2 derisk_executor.
  - ✅ (2026-05-30) 사용자 승인: **(1) 전량 시장가 청산 금지 유지 + 단계 자동 de-risk-to-floor(IOC+frozen bag) 추가**. 분량 큰 작업(U2~U4)은 전부 harness2.
  - 라우팅 재확정: U1=opus 직접(1파일) / U2·U3·U4=harness2(분량 大) / U5·U6=sonnet direct.
  - U1 구현: KillSwitch에 `unattended` 플래그 + `auto_derisk_due()` 즉시 트리거 신호. 시간로직 미포함(결합도↓), 실집행은 U2 derisk_executor.
- ⛔ 제약: 루트 progress.md·plan.md·progress-inv-v2.md 미변경. execute_trade.py diff=0. DRY_RUN/실거래 flip 미변경.
- 라우팅: U1·U2골격 = opus 정밀터치(설계). U2본체~U4 = harness2-wf 검토(신규 구축 대규모). U5·U6 = sonnet.
