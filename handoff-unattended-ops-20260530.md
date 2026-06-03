---
tags: [type/handoff, domain/inv, topic/unattended-ops, session/btn-Inv]
date: 2026-05-30
session: btn-Inv
consult_raw: [~/.claude/.gemini-web-last.md, ~/.claude/.claude-web-basic-last.md]
note: 무인 자동운영 전환 — readme 기반 자문 3R(gemini+claude 병렬) 수렴 + 코드 갭 조사 결과. KillSwitch 역설 P0 확정. 설계 의도·기각 대안·코드 갭 보존용.
---

# 인계 — 무인(unattended) 자동운영 안전 패치

> 트리거: 사용자 확정 제약 "완전 무인 자동운영, 운영자 개입 0. 사람 confirm/resume 경로 제거". 직전 readme 기반 자문 3R에서 P0 단일 최우선으로 합의된 "KillSwitch 역설"이 정확히 이 지점.

## 1. 자문 3R 수렴 (gemini Pro + claude Opus 4.8 병렬)

### P0 단일 최우선 — KillSwitch 역설 (양 모델 강수렴)
현 설계 `MDD-15% → HALT + 자동청산 금지 + 사람 confirm`은 "운영자가 깨어서 confirm 가능"을 전제. 무인이면 confirm할 사람이 없어 **하락장에 포지션 들고 영구 동결** → 보호하려던 바로 그 상황에서 무방비. (1인·한국시간·크립토 24/7·서킷브레이커 없음.)

### 핵심 설계 통찰 (claude R2)
**(B)KillSwitch + (F)protective-exit를 LLM이 suppress 못하게 + dead-man's switch + (D)비상 포지션 거래소 직접query = 단일 컴포넌트 `derisk_executor`로 통합.** 성격: LLM 비의존 · 거래소 truth 직접 읽기(ledger 불신) · fail-safe(모호하면 de-risk, never fail-open) · idempotent · rate-aware. 여러 트리거(MDD·heartbeat-loss·recon-break)가 이 하나를 호출.

### derisk_executor MVP 스펙 (양 모델 합의)
- **soft tier** (MDD-8% OR vol/gap spike): cancel all open orders + 신규진입 차단 + notify. 청산 안 함. (reversible)
- **hard tier** (MDD-15% OR heartbeat-loss OR recon-break): 사람 대기 없이 자동 de-risk-to-floor.
  - (a) cancel all resting orders → (b) 거래소에 venue별 실보유 query(ledger 아님, D 의존 해소) → (c) **marketable limit IOC**(naked market 금지 — Upbit 알트 thin book 슬리피지 폭발 방지)로 사전정의 floor까지 축소 → (d) re-query 체결검증 → (e) band 넓혀 retry(상한) → (f) 최대 슬리피지 도달 시 **FROZEN_BAG 마킹 + 해당 티커 매매 영구중단 + 알림**(패닉셀 -50% 덤핑보다 -10% bag-holding이 수리적으로 안전).
- **confirm 방향 반전**: 사람 confirm은 *resume(재무장)*에만, de-risk엔 절대 불필요.

### 자동 re-arm 정책 (gemini R3 — 무인 핵심)
사람 resume 불가 → 자동 재무장 필수. State machine: `NORMAL → SOFT_HALT → HARD_DERISK → COOLDOWN → RE_ARM_EVAL → (NORMAL | COOLDOWN)`.
- **Hysteresis**: 트리거 임계 ≠ 해제 임계 (예: SOFT_TRIGGER_VOL 5% vs SOFT_RELEASE_VOL 2%, 트리거 대비 ~40% 수준에서만 해제).
- **지수 backoff cooldown**: `2^(daily_triggers-1)` 시간 (1→2→4h).
- **일일 re-arm 상한 3회** 초과 시 `PERMANENT_FREEZE`(자정까지 자동복귀 불가). ⚠️ **Footgun 경고**: re-arm whipsawing(변동성 경계 진동 → 정리↔재진입 반복 수수료/슬리피지 자본잠식) = 가격하락보다 빠른 파산 경로. 일일 hard limit 필수.

### watchdog SPOF (gemini R3) — 투트랙
- **메인**: Cloud DMS(외부 serverless가 로컬 watchdog ping, 무응답 시 Cloud가 직접 거래소 cancel-all + de-risk). 로컬 H/W·네트워크 단절 완벽 대응.
- **보험**: 거래소 native stop-loss/예약매도(봇·watchdog 둘 다 죽어도 거래소 엔진 처리). 단 Upbit 현물 조건부주문 제약 큼 → flash crash 대비 floor GTC만.
- 전제 확인 필요: Cloud(Lambda/CF) 인프라 유무 — 없으면 신규 추가.

### 최소 사람 게이트 (절대 자동화 금지)
1. **API Key 출금권한 air-gap** — 거래소 키에서 출금 비활성. 피해를 거래소 내 잔고로 물리격리.
2. **Base Capital 상향 = 수동 ENV/config 배포만**. 봇 자동 복리재투자(auto-compounding) 금지 — 버그 시 max risk 무제한 통제불능.
3. (실거래 flip DRY_RUN=false on/off 자체도 사람 게이트 — 기존 golden rule.)

### 기타 수렴 (P1/P2)
- (C) down-only는 포지션 천장이지 포트폴리오 위험 천장 아님 → 감쇠 후 포트폴리오 레벨 corr cap 재산정 seam (core/-2nd-sleeve live 전).
- (G) consensus 상관오류 → "다른 입력뷰(A=뉴스텍스트/B=가격·orderflow만) + disagreement=de-risk(consensus를 confidence로 쓰지 말 것)" (core/-live 전).
- (H) PIT replay vs LLM 비결정성 → LLM 출력을 결정시점 input-hash+model-version-pin으로 캐시·영속, replay는 캐시에서만 읽고 재호출 금지 (core/-live 전).
- (I) 추정기 동조 → safety corr-cap을 sizing estimator와 다른 estimator로 분리 (core/-live 전).
- (J) 마진 없는 현물이라 cascade 청산 배제됨 → 자본배분 경합으로 약화. 슬리브별 ring-fenced KRW + auto-sweep 금지(ops).

## 2. 코드 갭 조사 (Explore, 무인 관점)

| 항목 | 상태 | 파일 | 무인 갭 |
|---|---|---|---|
| KillSwitch MDD halt 상태기계 | (A) OK | `core/risk_gate.py:304-386` | HALTED→CONFIRM_PENDING 전이 OK |
| **confirm() 호출** | **(C) ★결함** | (codebase 전수 grep) | `confirm()` 호출이 **어디에도 없음** → 무인 영구동결 |
| H27BoundedFallback | (B) 부분 | `core/fallback_policy.py:33-84` | 로직 정의(4h→25%/8h→50%, 전량금지) 있으나 **wire 없음**(테스트만) |
| heartbeat 프로토콜 | (B) 부분 | `rl_hybrid/protocol.py:111`, `config.py:16` | 정의만(`make_heartbeat`, 30s/3miss), **실감시 로직 없음** |
| watchdog/liveness | (C) 누락 | — | 프로세스 hang/crash 감지 후 자동 de-risk 전무 |
| 3-way reconciliation | (B) 부분 | `rl_hybrid/rl/live_trader.py:361-426` | R2 drift detect(5% halt) 있으나 자동보정·복구 없음. core/agents 라이브 경로 연결 불명 |
| thin-book escalation | (C) 누락 | `scripts/execute_trade.py` 등 | IOC/slippage cap/frozen bag 단계청산 전무 |
| 레거시 auto_emergency | (A) OK | `agents/orchestrator.py:1579-1753` | 발동·해제·전량매도 지시 전부 자동(무인 작동). 단 실행은 decision dict 의존 |

> ⚠️ 주의: heartbeat·drift는 `rl_hybrid/`(별도 트랙)에 있음 — 현 라이브(agents/ + core/) 경로와 연결되는지 미확인. 패치 시 라이브 경로에 실제로 닿는지 검증 필수.

## 3. 재개 포인트
- plan = `plan-unattended-ops.md`, progress = `progress-unattended-ops.md` (루트 plan.md·progress.md·progress-inv-v2.md 미변경).
- 다음: U1(KillSwitch 무인화) opus 정밀터치부터. 실거래 영향 0(DRY_RUN=true·core/ off 유지). 실거래 flip은 사람 게이트(자율 범위 밖).
