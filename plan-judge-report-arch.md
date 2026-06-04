---
tags: [plan, inv, judge, report, architecture]
date: 2026-06-03
session: btn-Inv
status: design-confirmed
consult: .consult-judge-report-RESULTS.md
---

# Plan — judge 재설계 + 리서치 통합 의사결정 아키텍처 (FHC)

> 설계 SSOT = [.consult-judge-report-RESULTS.md](./.consult-judge-report-RESULTS.md) (5R gemini+claude 수렴 C1~C16).
> 본 plan = 그 설계의 구현 명세. **거시=현 세션 / 주식 구현=button 세션**(동일 FHC 틀).
> ⛔ go-live=사람 게이트. push 금지. 결정론 코어·risk_gate 상수 무수정(오버레이만).

## 0. 한 줄 요지 (전/후)
- **전**: 결정론 L1=침범불가 천장 + bge/qwen=down-only 감쇠 + Claude consensus=뼈대만(테스트에서만 호출, approve/hold/reduce, 리서치 안 읽음).
- **후**: L1=보수 movable anchor / 독립산출 천장 C=진짜 불변식 / 그 아래 **확정·반증생존 FHC**만 e-value 비례로 천장까지 **강화(陽)** + 5중봉인. 리서치=매일 카드발권→임베딩검색→가설 가점→falsify 시 회수.

## 1. 핵심 설계 결정 (확정, RESULTS 참조)
| # | 결정 | RESULTS |
|---|---|---|
| D1 | primitive = FHC(LLM은 카드 mint만, 미등록=사이징 영향 0) | C1 |
| D2 | 2-leg: mediator vacate(전제 미성립=보너스 회수, 보류) ≠ outcome reject(전제성립·무수익=영구근접) | C2 |
| D3 | 강화 (B)안: L1 초과 가능·천장 C가 hard cap(신규 파라미터 0). 진짜 불변식=capital-at-risk≤C | C3 |
| D4 | per-asset headroom=(C−L1). 전역 풀 기각(BL 이중배분) | C3 |
| D5 | confidence 방화벽: self-conf→attention만 / e-value→capital. gate=AND, size=log-additive | C5 |
| D6 | 종목=룰코어 분산바스켓 스크린→딥모델 비교선택(바스켓 틸트 카드, ordinal). universe 밖 못 끌어옴 | C6 |
| D7 | 메타카드(시변 지표중요도, upstream 스크린 성형)·바스켓카드(downstream tilt) 2-leg+원장 분리 | C7 |
| D8 | 리서치=2-stage(매일 카드발권+임베딩검색 VaultVoice 재사용), grep fallback, 별도 consensus 엔진 금지 | C8 |
| D9 | mediator=study state-space filtered-only 구독(versioned, covariance 노출) | C10 |
| D10 | whipsaw=evidence-gated(τ_in/τ_out dead-band+cost gate), 달력 기각 | C11 |
| D11 | alpha-wealth: meta/basket 고정분할 firewall, LORD++ layer 내부만 | C12 |

## 2. 안전 불변식 = INV-1..16 (RESULTS C13). load-bearing core=INV-1·3·11·16.

## 3. 구현 단계 (RESULTS C14 sign-off)

> 매 단계 게이트 = **INV-11**(judge/bonus OFF 시 byte-identical 무회귀) + **INV-3**(fault-injection fail-closed 통과). go-live 경계 = §4.

- **S0 [현 세션·이미 plan-test-readiness P2]** 결정론 baseline 수익률 테스트(judge off) = INV-11 기준선. `model: opus`
- **S1 FHC 안전 인프라** — 카드 5-state machine(minted→confirmed→vacated→rejected→revived) + kill-switch + cooldown + fail-closed. lifecycle 전이조건·invariant(minted→vacated 금지, rejected absorbing, revival_count cap). `wf: harness2`
- **S2 mediator wiring** — study room state-space posterior **filtered-only** 구독(versioned, covariance/entropy 노출). capital-at-risk 미증가. `wf: harness2`
- **S3 bonus 채널** — ★4a/4b 분할:
  - **S3a** breaker(regime-primary)+recall path(IOC ladder)+fail-closed 선배선 [chaos/fault-injection 통과 필수]. `wf: harness2`
  - **S3b** bonus emission(L1+bonus≤C, e-value monotone map, 시간감쇠). `wf: harness2`
- **S4 능동 애널리스트 루프** — 7-step(저신뢰 트리거→summon gate→scoped PIT 검색→falsifiable claim→Opus pre-mint audit→probationary mint→write-back). `wf: harness2`
  - ★존재이유 = **C9 결정론이 못 푸는 6유형**(RESULTS C9): ①regime-break로 구조모델 자체 무효 ②value-trap 판별(일시 dislocation vs 영구 impairment) ③cross-source 합성 ④신규 가설 생성 ⑤스케줄된 이산 이벤트 ⑥instrument 선택. 이 6유형 = LLM 카드발권이 결정론보다 우위인 유일 영역(나머지는 결정론 코어가 처리).
- **S5 리서치 통합** — 2-stage(매일 카드발권 LLM + RAG 하이브리드 daily batch/event-driven, PIT 스탬프). VaultVoice BGE/LanceDB 재사용. `wf: harness2`
- **S6 [button 세션]** 종목 바스켓 — 룰코어 top-N×지표편차 스크린 + 딥모델 비교선택 + 메타카드. KIS equity. `→ button`

## 4. go-live 경계 (RESULTS C14)
- S0~S4(4b 포함) 전부 dry-run/shadow. → go-live = 능동루프 shadow 지속통과 직후 **coin bot부터**(최소·이미 live) incremental arming → 종목 바스켓(KIS)은 S5 후 최후. ⛔ 전 구간 사람 게이트.

## 5. 미서명/Open items (RESULTS, [측정] 대상)
- τ_in/τ_out 구체 수치 + cost gate turnover 비용 모델 소스(슬리피지 vs 가정).
- realized_bonus e→bonus map 곡률 per-card-type 확장(base=단일).
- bonus baseline 초과 = (B) 확정(사용자 의도), 단 C 독립산출 4조건(C5 RESULTS) 구현시 증명 필수.
- FHC "안전 인프라" vs "FDR Hierarchy Controller" 명칭 — S1=전자(safety machine), FDR controller는 S3b/S5 내부.

## 6. scope
- 거시(macro)=현 세션 S0~S5. 주식(stock) 구현 S6=button 세션(설계 공유).
