---
tags: [type/safety, domain/inv, topic/unattended-ops, gate/human-only]
date: 2026-05-30
session: btn-Inv
plan: ./plan-unattended-ops.md
note: 무인 자동운영에서 절대 자동화 금지 = 사람 전용 게이트(SSOT). U5 산출물.
---

# 최소 사람 게이트 — 무인 운영 안전 경계 (SSOT)

> 무인(unattended) 자동운영은 **운영 안전행동**(de-risk·halt·watchdog·reconcile)을 사람 개입 0으로 수행한다.
> 그러나 **자본·권한·신뢰경계를 넓히는 행위**는 영구히 사람 전용이다. 이 문서가 그 경계의 SSOT.
> 관련: [plan-unattended-ops.md](./plan-unattended-ops.md) · [audit-goldenrule-unattended.md](./audit-goldenrule-unattended.md)

## 핵심 원칙

> **무인은 손실을 줄이는 쪽으로만 자율적이다. 위험을 키우는 쪽은 전부 사람 게이트다.**
> de-risk(축소·정지)는 자동, re-arm(재무장)·확대·권한부여는 사람.

## 🔴 절대 자동화 금지 (사람 전용 게이트 — 4종)

| # | 게이트 | 금지되는 자동화 | 강제 메커니즘 |
|---|--------|----------------|---------------|
| G1 | **출금권한 air-gap** | 거래소 API Key에 **출금(withdraw) 권한 부여 금지**. 봇·watchdog credential은 조회+주문만. | API Key 발급 시 출금 scope 제외. 출금은 거래소 웹 UI에서 사람이 2FA로만. |
| G2 | **Base Capital 수동 배포** | 운용 원금 자동 증액·auto-compounding 금지. 수익 재투자도 사람 승인. | `MAX_TRADE_AMOUNT`/`MAX_POSITION_RATIO` 상향 = 사람만. 코드·자동 경로 없음. |
| G3 | **실거래 flip (DRY_RUN=false)** | `DRY_RUN=true→false` 전환을 어떤 자동 경로도 금지. core/ 게이트 on 전환도 사람. | `.env` 수동 편집 전용. 자율주행/FSM/orchestrator 어디서도 flip 불가. |
| G4 | **신뢰경계 확대** | 신규 거래소·신규 심볼·신규 데이터소스 자동 admission 금지. core/ off→on opt-in. | `INV_CORE_GATE` opt-in 수동. 신규 연결은 아래 admission 체크리스트 통과 후 사람 승인. |

⛔ 위 4종 중 하나라도 **도달이 임박하면 무인 루프는 정지 + 사람에게 보고**한다. 자율 범위 밖.

## 🟢 무인 자율 허용 (사람 개입 0)

| 행동 | 자율 | 근거 |
|------|:---:|------|
| de-risk-to-floor (IOC 단계청산 + frozen bag) | ✅ | 손실 축소 = 안전측. `derisk_executor` |
| HALT / SOFT_HALT / HARD_DERISK 진입 | ✅ | 위험 차단. `unattended_fsm` |
| watchdog heartbeat-loss → derisk 트리거 | ✅ | dead-man's switch |
| reconciliation break → soft-halt | ✅ | truth 우선 안전 |
| cooldown 후 자동 re-arm (hysteresis·일일상한 내) | ✅ | 단, PERMANENT_FREEZE·상한 초과 시 사람 |
| **PERMANENT_FREEZE 탈출(재무장)** | ❌ | 사람 전용 — 무인은 자정 기본값 복귀만, 실거래 재개는 G3 경유 |

## core/ 격리 admission 체크리스트 (G4 — shadow→live 승격 전 사람 확인)

shadow(core/) 시스템을 라이브로 승격하기 전, 아래를 사람이 전부 확인한다. **하나라도 미충족 = 승격 금지.**

- [ ] **API Key 비공유**: shadow와 live가 별도 credential (shadow가 live 주문권한 미보유)
- [ ] **Rate-limit 비공유**: shadow API 호출이 live de-risk의 rate budget을 잠식하지 않음 (G4 핵심 — 안전장치 마비 방지)
- [ ] **Ledger 비공유**: shadow 거래기록이 live ledger·reconciliation truth를 오염시키지 않음
- [ ] **Host 비공유 또는 격리**: shadow 장애가 live watchdog/de-risk 프로세스를 죽이지 않음
- [ ] **회귀 0**: live 경로 byte-identical 유지 확인 (core off 기본값 보존)

## strangler-fig decommission framework (레거시 → 신규 전환)

레거시 코인봇·실행경로를 신규 무인 아키텍처로 점진 교체할 때:

1. **병행 기간 명시**: 신규 경로 live 전환 시 레거시 decommission **목표 날짜**를 반드시 기재(무기한 병행 금지).
2. **shadow 비교**: 병행 기간 동안 신규 vs 레거시 의사결정 divergence 로깅. 임계 이내 수렴 확인.
3. **단일 truth**: 전환 완료 시 레거시 실행경로 제거(코드 잔존 시 dead-path가 무인 안전 추론을 오염).
4. **롤백 경로**: decommission 전까지 레거시 즉시 복귀 경로 유지(사람 게이트).

> ⚠️ 현재 이연(D1): `INV_UNATTENDED_FSM` wire가 레거시 진입점(`scripts/run_agents.py`)에 위치.
> 라이브 `agents/orchestrator.py` 실연결은 **go-live 시 사람이** strangler-fig 절차로 전환(자율 범위 밖).

## 이연 항목과의 관계 (go-live 사람 게이트)

audit-goldenrule-unattended.md §4의 이연 5건(D1~D5)은 전부 **go-live 시 사람이 수행하는 wire**다:
- D1 라이브 wire 실연결 / D2 거래소 native stop / D3 revoke_bot_api_key(SPOF fail-safe) / D4 watchdog 독립배포 / D5 reconcile cadence wire.
- 이들은 무인 코드가 **준비**(stub·모듈)는 완료했으나 **실연결은 G1·G3·G4를 건드리므로 사람 전용**이다.

## 운영 파라미터 단위 규약 (Phase Gate 품질)

- `RISK_SOFT_STOP_PCT` / `RISK_HARD_STOP_PCT` = **% 단위** (예: `-10.0` = -10%). 내부 비교가 `/100` 되므로
  ⛔ 소수(`-0.10`)로 오입력하면 stop 이 사실상 무력화(`-0.001` 과 비교)된다. env override 시 % 단위 엄수.
- `UNATTENDED_MDD_HARD` / `UNATTENDED_MDD_SOFT` / `UNATTENDED_REARM_MDD` = **소수 단위** (예: `-0.15` = -15%). 혼동 금지.
