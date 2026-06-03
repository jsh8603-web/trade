---
tags: [type/plan, domain/inv, topic/unattended-ops, session/btn-Inv]
date: 2026-05-30
session: btn-Inv
handoff: ./handoff-unattended-ops-20260530.md
note: 무인 자동운영 전환 안전 패치. 자문 3R 수렴 + 코드 갭 기반. 루트 plan.md 미변경(격리 신규 파일).
---

# Plan — 무인(unattended) 자동운영 안전 패치

> 인계: [handoff-unattended-ops-20260530.md](./handoff-unattended-ops-20260530.md) (자문 3R 수렴·코드 갭 전문)

## 목표
운영자 개입 0의 완전 무인 자동운영을 안전하게 만든다. 핵심 = **사람 confirm/resume 경로 제거 + fail-safe 자동 de-risk**. 자문 P0 = KillSwitch 역설(MDD-15%→사람confirm 대기→무인 영구동결).

## 불변식 (유지/재정의)
- **유지**: down-only, falsification, PIT replay, floor 분리, 학습/적용 분리, opt-in off, `DRY_RUN`/`execute_trade.py` 미변경, 실거래 flip=사람 게이트.
- **재정의**(자문 수렴 근거): "자동 전량청산 금지(사람 confirm)" → **"자동 de-risk-to-floor(IOC 단계청산 + frozen bag 상한)"**. 전량 시장가 투매 footgun도 막고 무인도 충족(양립). confirm은 *resume(재무장)*에만.
- **신규 불변식**: 보호행동(de-risk) 경로는 LLM 가용성/출력과 완전 독립. LLM은 줄이거나 veto만, 보호행동을 trigger 요구하거나 suppress 불가.

## 범위 경계
- 현재 DRY_RUN=true·core/ off·레거시 코인봇만 라이브. 이 패치는 **go-live 준비**이지 당장 실거래 영향 0.
- `rl_hybrid/`에 heartbeat/drift 프로토콜 정의가 있으나 라이브 경로(agents/+core/) 연결 미확인 → 패치가 실제 라이브 경로에 닿는지 검증 필수.

## 작업 단계 (우선순위 = 치명도 순)

### U1 — KillSwitch 무인화 (P0, opus 정밀터치)
`core/risk_gate.py` KillSwitch 상태기계 개조 + `core/fallback_policy.py` H27 wire.
- confirm 영구동결 해소: HALTED 도달 시 사람 confirm 대기 대신 `derisk_executor` 자동 호출 경로.
- H27BoundedFallback(timeout 자동축소)을 실제 라이브 경로에 wire. timeout 값 env 주입화.
- confirm()은 *resume*에만 잔존(de-risk엔 불필요).
- **설계 판단**(불변식 재정의·상태전이) → opus 직접. 1~2파일.

### U2 — derisk_executor 신규 컴포넌트 (P0, opus 골격 → 분량 시 harness2)
LLM 비의존·거래소 truth 직접query·fail-safe·idempotent·rate-aware 통합 de-risk 집행기.
- soft/hard tier + 자동 re-arm 상태기계(NORMAL→SOFT_HALT→HARD_DERISK→COOLDOWN→RE_ARM_EVAL).
- Hysteresis(트리거≠해제 임계) + 지수 backoff cooldown(2^n h) + 일일 re-arm 상한 3회→PERMANENT_FREEZE.
- hard 동작 (a)cancel all →(b)거래소 실보유 query →(c)IOC marketable limit floor 축소 →(d)re-query 검증 →(e)band retry 상한 →(f)FROZEN_BAG.
- ⚠️ re-arm whipsawing footgun 가드(일일 hard limit).
- **opus가 상태기계·불변식 골격 설계, 구현 분량 크면 harness2-wf로 본체 + 테스트.**

### U3 — dead-man's switch / watchdog (P0~P1, harness2 후보)
heartbeat 실감시 daemon + 끊기면 derisk_executor 트리거.
- rl_hybrid heartbeat 프로토콜을 라이브 경로에 실연결 OR 신규 로컬 watchdog.
- 거래소 native stop-loss(Upbit/KIS) 보험 병용 — flash crash floor GTC.
- Cloud DMS는 인프라 전제(Lambda/CF 유무 확인) → 없으면 로컬 다중화 우선.
- **신규 구축 대규모 → harness2-wf.**

### U4 — reconciliation 보강 + thin-book escalation (P1, harness2 후보)
- 3-way reconciliation: intended/ledger/거래소 truth 대사 + truth-authoritative overwrite + break 시 soft-halt. rl_hybrid R2 drift를 라이브 경로에 연결·확장.
- thin-book escalation ladder(-1%→-3%→-5% IOC, 최대 슬리피지 도달 시 FROZEN_BAG) — U2 derisk_executor의 (c)~(f)와 통합.
- **신규 구축 → harness2-wf.**

### U5 — 최소 사람 게이트 명문화 (P1, 문서/config)
- API Key 출금권한 air-gap 가이드(.env.example/문서). Base Capital 수동 배포·auto-compounding 금지 명시.
- core/ 격리 admission(shadow는 live와 API키/rate-limit/ledger/host 비공유). strangler-fig decommission 날짜 framework.

### U6 — readme.md patch (마지막, 사용자 명시)
무인 운영 안전 아키텍처를 readme에 반영:
- KillSwitch 자동화(자동 de-risk-to-floor) + derisk_executor + soft/hard tier + 자동 re-arm.
- watchdog/dead-man's switch + 거래소 native 보험. reconciliation. thin-book escalation/frozen bag.
- 신규 불변식(보호경로 LLM 독립). 최소 사람 게이트(출금 air-gap·capital 수동).
- 안전장치 요약표·디렉토리맵 갱신.

## 검증 게이트
- 각 U 단계: self-test/pytest 회귀 0. DRY_RUN=true·core/ off 유지 확인(레거시 byte-identical).
- 무인 시나리오 시뮬: HALT→자동 de-risk→re-arm 사이클, heartbeat-loss→watchdog 트리거, recon-break→soft-halt, thin-book→frozen bag.
- ⛔ `execute_trade.py` diff=0, 실거래 flip 미수행.

## 테스트 계획 (2단계 — 사용자 확정 2026-05-30)

### 1단계 — Unit (harness2 내, 각 SO Verifier 독립 게이트 = 코드 commit 단위 검증)
- SO-1 `tests/test_derisk_executor.py`: floor 축소·fail-safe(no fail-open)·idempotent·LLM import 0.
- SO-2 `tests/test_unattended_fsm.py`: re-arm 1사이클·hysteresis·PERMANENT_FREEZE·whipsawing 정지·영속 / **SR 반영**: state 파손→HARD_DERISK 기본값·monotonic cooldown·FREEZE 무인탈출.
- SO-3 thin-book ladder: IOC band 확대·-10% frozen·매매중단·market order 미사용.
- SO-4 `tests/test_watchdog.py`: heartbeat stale→derisk 트리거·정상시 0·봇/LLM import 무의존.
- SO-5 `tests/test_reconciliation.py`: truth overwrite·tolerance·**N-consistent-sample(transient stale 방어)**·대형 delta→hard_derisk·append-only.
- SO-6 wire: auto_derisk_due→executor·H27 halt-anchor 무인발동·U1 회귀 0(116 passed).
- SO-7 무인 E2E pytest: 급락→HALT→de-risk→cooldown→hysteresis re-arm→NORMAL 전 사이클 사람개입 0 + 전체 회귀 0 + diff0.
- SO-8 GOLDEN RULE 감사(문서 게이트).
- **합격 = 각 SO Verifier verdict=PASSED(git_head 매칭) + 전체 pytest 회귀 0.**

### 2단계 — 압축 후 E2E 실기능 검증 (U7, 압축 이후 자율 진행)
- 주요 기능 **DRY_RUN 실작동** 테스트(SO-7 의 무인 사이클 시뮬과 별개 = 실시스템 파이프라인): 데이터 수집(market/fgi/news)·에이전트(conservative/moderate/aggressive)·orchestrator 전략전환·de-risk_executor·watchdog·reconciliation·KillSwitch/H27 wire.
- **발견 즉시 고장 패치**(detect→patch 루프). 회귀 0 + SACRED 유지(execute_trade diff0·전량청산 금지·DRY_RUN).

## 자율주행 (사용자 확정 2026-05-30 — progress 완료까지 ON)
- progress 의 전 단계(harness2 SO-1~8 → U5 → U6 readme → 압축 → U7 E2E)를 **사용자 확인 없이 자율 완주**. flag = `.harness2/.autopilot-unattended`.
- 막힘 해소도 자율: Verifier FAIL→Worker rework / retry≥3→Healer / 중재→Supervisor / 9이벤트→외부자문. watchdog 완료알림이 phase 경계 wake.
- ⛔ 자율 범위 밖(절대 자동화 금지, 사람 전용): 실거래 flip(DRY_RUN=false)·자본 상향·API 출금권한. 이들 도달 시 정지+보고.
