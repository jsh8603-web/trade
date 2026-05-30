---
tags: [type/reference, domain/inv, topic/unattended-ops, layer/safety-architecture]
date: 2026-05-30
session: btn-Inv
plan: ./plan-unattended-ops.md
human_gates: ./SAFETY-human-gates-unattended.md
audit: ./audit-goldenrule-unattended.md
note: 무인 운영 안전 아키텍처 SSOT (U6). README.md 본체 통합은 R15/brain M 해소 후 이연(D6).
---

# 무인(Unattended) 운영 안전 아키텍처

> 운영자 개입 0의 완전 무인 자동운영을 안전하게 만드는 레이어.
> 핵심 = **사람 confirm/resume 경로 제거 + fail-safe 자동 de-risk** + **LLM 독립 보호경로**.
> 사람 전용 게이트: [SAFETY-human-gates-unattended.md](./SAFETY-human-gates-unattended.md)

## 설계 원칙

> **무인은 손실을 줄이는 쪽으로만 자율적이다.** de-risk(축소·정지)는 자동, 위험 확대·재무장·권한부여는 사람.

| 불변식 | 내용 |
|--------|------|
| 보호경로 LLM 독립 | de-risk/halt/watchdog/reconcile 경로는 LLM 가용성·출력과 **완전 독립**. LLM은 줄이거나 veto만, 보호행동을 trigger 요구·suppress 불가. (brain/judge/consensus/HRP import = 0, AST 정적검사 게이트) |
| 전량 시장가 청산 금지 | naked market order 금지. **IOC 단계청산(ladder) + frozen bag -10% 상한**만 허용. |
| fail-safe (no fail-open) | 예외·타임아웃·상태파손 시 거래 계속 금지. 안전측(HARD_DERISK)으로 수렴. state load 실패 = HARD_DERISK 기본값. |
| idempotent | de-risk 중복 호출 안전(`_triggered` 가드). |

## 컴포넌트 맵

```
core/risk_gate.py        KillSwitch.unattended + auto_derisk_due()  ← 무인 트리거 신호
   │ (auto_derisk_due True)
   ▼
core/unattended_fsm.py   6상태 FSM (재무장 상태기계)
   NORMAL → SOFT_HALT → HARD_DERISK → COOLDOWN → RE_ARM_EVAL → (NORMAL | PERMANENT_FREEZE)
   │ hysteresis(트리거≠해제) · 지수 backoff(2^n h) · 일일상한(3회→FREEZE) · 원자적 state.json+checksum
   ▼
core/derisk_executor.py  LLM 비의존 집행기
   cancel_only → query 실보유 → IOC marketable limit floor 축소(LADDER_BANDS -1/-3/-5%)
   → re-query 검증 → MAX_SLIPPAGE(-10%) 도달 시 FROZEN_BAG 마킹 + 매매중단

scripts/watchdog.py      dead-man's switch (독립 프로세스)
   heartbeat 감시 → stale 시 derisk_executor 트리거
   + register_native_stop(거래소 native 보험, stub) + revoke_bot_api_key(궁극 fail-safe, stub)

core/reconciliation.py   3-way 대조 (intended / ledger / 거래소 truth)
   truth-authoritative overwrite (단, N-consistent-sample 가드 — transient stale 방어)
   break → soft-halt, 대형 delta → hard_derisk, append-only recon_log

core/fallback_policy.py  H27BoundedFallback
   halt-anchor 무인발동 (confirm 대기 대신 HALT 진입시점 anchor → timeout 자동축소)
```

## KillSwitch 자동화 (U1)

기존: MDD −15% → HALTED → **사람 confirm 대기** → (무인 시 영구동결, footgun).
무인: HALTED 도달 시 `auto_derisk_due()` = True 신호 → `derisk_executor` 자동 호출.
- `confirm()` 은 **resume(재무장) 경로에만** 잔존 (de-risk엔 불필요).
- `RISK_UNATTENDED` env(기본 true)로 모드 제어.

## 재무장 상태기계 (FSM)

| 상태 | 의미 | 전이 |
|------|------|------|
| NORMAL | 정상 운영 | 트리거 → SOFT_HALT |
| SOFT_HALT | 신규 매수 차단, 기존 유지 | 악화 → HARD_DERISK / 완화 → COOLDOWN |
| HARD_DERISK | de-risk-to-floor 집행 | 완료 → COOLDOWN |
| COOLDOWN | 지수 backoff 대기(2^(n-1)h) | 만료 → RE_ARM_EVAL |
| RE_ARM_EVAL | 재무장 조건 평가(hysteresis) | 충족 → NORMAL / 일일상한 초과 → PERMANENT_FREEZE |
| PERMANENT_FREEZE | 동결 | 자정(KST) 기본값 복귀(무인 탈출), 실거래 재개는 사람 게이트(G3) |

- **Hysteresis**: 트리거 임계 ≠ 해제 임계 → whipsawing 방지.
- **일일 re-arm 상한**(MAX_REARM_PER_DAY=3): 초과 시 PERMANENT_FREEZE.
- **원자적 영속**: `unattended_state.json` tmp+fsync+rename + checksum. load 실패 = HARD_DERISK 기본값(fail-safe).

## de-risk 집행 (IOC ladder + frozen bag)

1. cancel_only (모든 미체결 취소)
2. 거래소 실보유 query (truth 직접)
3. IOC marketable limit으로 floor까지 축소 — LADDER_BANDS = -1% → -3% → -5% 점진 확대
4. 각 band 후 re-query 검증
5. 누적 슬리피지 **MAX_SLIPPAGE(-10%)** 도달 시 → FROZEN_BAG 마킹 + 매매중단(naked market 투매 금지)

## watchdog / dead-man's switch

- 봇과 **독립 프로세스 + 독립 credential**(WATCHDOG_UPBIT_KEY).
- heartbeat 파일 stale → de-risk 트리거.
- 거래소 native stop-loss 보험 병용(flash crash floor) — `register_native_stop` (go-live 실연결 이연 D2).
- 궁극 fail-safe: `revoke_bot_api_key` (SPOF A4, master credential 분리 후 실연결 이연 D3).

## reconciliation (3-way)

- intended(의도) / ledger(장부) / exchange truth(거래소 실측) 대조.
- truth-authoritative overwrite — 단 **N-consistent-sample**(연속 N회 일치) 통과 후만 덮어씀(transient stale 1회 오염 방어), 불일치 시 quarantine.
- break → soft-halt, 대형 delta → hard_derisk. append-only `recon_log.jsonl`.

## 검증 커버리지

- 무인 신규 테스트: **61 passed** (derisk_executor / unattended_fsm / watchdog / reconciliation / so7 E2E / golden_rule).
- U1 회귀(risk_gate/kill/fallback): 117 passed.
- SACRED: execute_trade.py diff=0 · LLM import 0(AST) · market order 0 · DRY_RUN 보존.
- GOLDEN RULE 5축 1:1 커버 (audit-goldenrule-unattended.md).

## go-live 이연 (사람 게이트 — SAFETY 문서 G1·G3·G4)

| # | 이연 | 사유 |
|---|------|------|
| D1 | INV_UNATTENDED_FSM 라이브 wire 실연결 | 현재 레거시 진입점(run_agents.py)에 위치. orchestrator.py 실연결은 strangler-fig 전환(사람). |
| D2 | 거래소 native stop 실연결 | Upbit/KIS 조건부주문 제약 → go-live. |
| D3 | revoke_bot_api_key 실연결 | master credential 분리 필요 → go-live. |
| D4 | watchdog 독립 프로세스 배포 | 실 credential + 프로세스 관리(systemd) → go-live. |
| D5 | reconciliation cadence wire | 매 cycle/fill 후 호출 라이브 연결 → go-live. |
| D6 | **README.md 본체 통합** | README.md가 R15/brain 작업 M상태로 소유 중 → 충돌 회피 위해 본 문서로 분리. R15/brain 머지 후 README §🛡️ 안전장치 요약에 KillSwitch 자동화 반영 + 본 문서 링크. |
