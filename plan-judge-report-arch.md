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
  - ★**자문 Q3 직교성 발권 게이트(2026-06-04 두 모델 최강 수렴)**: 정성 텍스트 촉매(예: 'HBM 공급부족')가 기존 7팩터 위장(중복)인지 진짜 잔차 알파인지 = **텍스트 공간 신규성 믿지 말고 직교화된 수익률 공간에서 증명**. 발권 게이트 = "촉매→거래가능 신호(롱숏 바스켓 r_c) → 스패닝 회귀 r_c=α+βᵀF+ε(F=7팩터). **α≈0=위장(결정론 노출에 이미 있음, 발권 X)** / α유의+잔차 forward IC=진짜 잔차 알파". ★**잔차 수익률 공간에서 α≠0 못 보이면 가설 아님**(falsifiability 사수, 우리 MOVE⊥VIX 흡수판정 공식화). 도구=FWL 잔차화(보유)+GRS(Gibbons-Ross-Shanken 1989)+wild-cluster bootstrap(소표본). ★최고가치=**조건부 검사**(무조건부 0인데 국면 내 알파=regime-switching conditional-IC와 정합, 결정론 팩터코어가 state-dependence 못 잡음) + 팩터타이밍 vs 종목선택 분해(sector-neutralize 후 생존=종목 잔차 알파 / Granger-lead=팩터타이밍 알파, sleeve 위치 다름). ★**두 모델 분기(보완 레이어)**: claude=**생성단 발권게이트**(스패닝 회귀로 위장 차단) / gemini Q3 1순위=**사이징단 팩터중립 제약**(옵티마이저가 7팩터 노출 불변 유지하며 잔여비중만 배분). 생성/사이징 다른 단이라 **양립**(bonus_channel 사이징 시 팩터중립 제약 옵션으로 보강 가능, 단 비중 0 수렴 위험 점검).
- **S5 리서치 통합** — 2-stage(소형 LLM 요약 → 임베딩 인덱싱 RAG → 대형 LLM 카드발권, PIT 스탬프). VaultVoice BGE/LanceDB 재사용. `wf: harness2`
  - ★**자문 정제(2026-06-04 gemini-web+claude-web 수렴, .gemini-web-last.md / .claude-web-basic-last.md)**:
    - **Q2 호출빈도 = "daily batch" 폐기 → 정보델타 트리거 + 생성/승격 분리**(두 모델 최강 공통 권고, 현 설계 약한 고리): ①수집·인덱싱=상시 ②**가설 생성=시계(clock) 아닌 정보델타(retrieval context 임베딩 novelty 임계 초과) 트리거**(안 바뀌면 standing hypothesis 유지) ③승격·사이징=의사결정주기(주/국면)+e-value 누적, **up/down 비대칭**(상향 지연/하향 즉시=down-only 정합) ④이벤트=가격점프 OR 정보신규성 dual-key. 효과 3마리=유령회전(phantom turnover) 제거+FDR 예산(LORD++ α-spending 매일 소진 방지)+대형 LLM 비용절감. 비공식 Nyquist=행동가능정보 변화속도(주 단위)의 2배 이상이되 FDR/회전 망가뜨리는 속도 미만. ★**재검토 정정(2026-06-06 사용자 반박, 자문 무비판 수용 교정)**: "daily batch 폐기 → 순수 델타 트리거"는 **빈도 상한(rate cap) 간과**. 새 리포트는 임베딩 거리가 늘 미세하게 멀어 게이트를 계속 통과 → 대형 LLM 발권이 daily보다 **오히려 폭증** 가능(델타=상한 없음 / batch=명확한 상한). → **정정 설계 = 시계 rate-cap(상한, 예 일/주 최대 N회) AND 델타 게이트(슬롯 내 새 정보 없으면 skip) 결합**: 시계=폭증 방지 상한, 델타=무의미 발권 필터. daily/weekly batch는 '폐기'가 아니라 **상한 역할로 유지**. ⛔'주간배치↔임계값'은 다른 축(시계 기반 vs 이벤트 기반)인데 직전 설명이 잘못 연결 — 자문 "초기 주간배치"=델타 튜닝 난도 회피용 단순 시계지 임계 구현 아님.
    - **Q1 리포트 편향 보정 = 별도 모듈 X, 기존 불변식 흡수**: ①level 금지 → surprise/revision 공간만(ΔTP vs 직전·vs 컨센서스, 등급전이 ordinal, SFR 표준화) ②**한국 매도의견 희소 → down-only invariant 매핑**(희소 Sell/TP컷=정보 비대칭 큼=저지연 음 카드 허용 / 반복 Buy=컨센서스 이기는 surprise 아니면 양 카드 불가) ③톤 정규화 2회 디민(애널리스트 baseline FE + 동시점 횡단면 디민, 범용 감성사전 금지=Loughran-McDonald 2011, 한국어 KR-FinBERT) ④선반영=발간시점 CAR 통제 후 forward residual + bitemporal(valid-time vs ingestion-time) PIT가 RAG stale-context 누수 차단. ⑤**잔차 톤(residual tone)**: 텍스트 감성 스코어에서 과거 수익률·변동성으로 설명되는 부분을 회귀 제거한 잔차만 정보로 취급(gemini Q1 대안2, Ke-Kelly-Xiu 2019 — 톤 디민과 별개 기법, 텍스트 스코어링 모델 구축 필요로 2단계 도입). affiliation 가중(Michaely-Womack 1999). 체계적 낙관·과소반응(Easterwood-Nutt 1999)·추천 사후 드리프트(Womack 1996).
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
