---
tags: [type/handoff, domain/inv, phase/II, track/T2, topic/assumption-lifecycle-v2, session/btn-button]
date: 2026-05-29
session: btn-button
deliver_to: btn-Codlearn (T3, 최종 통합)
design: ./DESIGN-button-v2.md
raw_consult: [./.consult-button-R1.txt, ./.consult-button-R2.txt, ./.consult-button-R3.txt, ./.consult-button-R4.txt, ./.consult-button-R5.txt]
note: btn-button(T2)의 자문 5R 결정 요약 — 메인 전달용. 설계 본문은 DESIGN-button-v2.md, raw 는 .consult-button-R{1..5}.txt. 본 문서 = 결정/계약/미해결만.
---

# 자문 결정 요약 — btn-button T2 (BB-1~5), 메인 전달용

## 1. 자문 개요
- 채널: **gemini Pro + claude Opus 4.8** 병렬 독립, Playwright 자동화. raw 5 file `.consult-button-R{1..5}.txt`.
- 라운드: R1 거시·통계 설계 → R2 instrument universe → R3 통합 아키텍처 → R4 구현 specifics → R5 완결성 비평.
- **종결**: R5(완결성 비평)에서 gemini 가 **명시적 saturation 선언**("구현 가능한 포화도 도달"). claude R5 는 브라우저 채널 경합(타 세션 동시 사용)으로 미수집 — R1~R3 full + R4 핵심으로 claude 관점 충분 반영.

## 2. 확정 결정 (BB 축별)
| 축 | 확정 설계 |
|---|---|
| **BB-1 거시 카드화** | 6 AnomalyCase → 버전드 MacroAssumptionCard. falsification = "attenuation 이 실제 regime 오판을 줄였나"를 **prequential ΔBrier + 잔차 CUSUM + mechanism-validation(ACM term premium, 결과독립)**로 채점 (소표본 precision/recall 폐기). |
| **BB-2 live 학습** | JM **filter(online) vs smoother(insample) divergence** = 버려지던 신호 → CorrectionRecord harvest → `ingest_correction` live. PIT causal mask. |
| **BB-3 regime 발견** | **BOCPD(timing, 1-D) + Hotelling T²/χ² novelty(full 다변량, σ 아님)** + 후보발행을 **online-FDR(LORD++)로 wrap** + dwell·time-separation·economic-overlay. 승격 = 사람 gate(base-layer). **DP-mixture 폐기**(numpy 불안정). bnpy seam(미설치 graceful). 재현=booster(kill 아님). |
| **BB-4 검증 cohesion** | card.kind dispatch → regime-conditional holds_now + **가정별 LORD++ FDR stream(자산클래스 격리, event-time 인덱싱)**. 부활 차단(alpha-wealth). |
| **BB-5 금융상품** | 4단 archetype 추상(primary/companion/value_trap_guard/cheapness)=전자산 보편, **value_trap = decoupling 머신 일반화**. commodity 3(carry=convenience-yield/seasonal=F-test·STL strength/inventory=variance-ratio·threshold-regression) + crypto 3(monetary_store=MVRV·realized-price/network_utility/speculative_flow). **COT 예측력 약함→companion 강등**. |

## 3. instrument 우선순위 (사용자 정정: "상품"=금융상품)
1. **crypto (BTC/ETH)** — 기준변동성 최대, 데이터 무료(CoinMetrics Community)·24/7, Upbit 보유, ETF decoupling = 최고 testbed.
2. **주식 sector-ETF** — 기존 equity archetype 전이.
3. **rates/credit** — signal layer(별 tradable 아님, FRED).
4. **FX** — risk-regime gate. 5. REITs defer. commodity = R1 설계분.
- crypto 데이터: **proxy 금지**(transition 체계오류) → CoinMetrics 무료 정식. netflow = 유료 전 guard 비활성 + band 보수. halving = Schelling prior(통계검정 금지). regime = Wyckoff 2D(trend×cost-basis).

## 4. 통합 아키텍처 결정 (R3~R5)
- **#1 레버리지 = bitemporal append-only event ledger** (11 event type, `state=reduce(pure_apply, sorted(events))`). join=(assumption_id,version). **★FDR_DECISION = decision_time 순만 재생(immutable), Brier/DM만 valid_time 재계산** — 안 그러면 online-FDR 보장 파괴.
- **calibration(static YAML)**: LORD++ crypto α0.10·macro α0.05 / BOCPD λ 1/60·1/48 / χ² 99th·95th / DM lag h-1 / Hotelling F-변환 n≥3p / prequential N90·N60.
- **data-contract gate(축D)**: ingestion↔검증엔진, 이상→HOLD_SUSPENDED(FDR 제외+사람확인). crypto netflow 5σ / commodity roll mask / macro vintage diff.
- **다중시간척도**: 모든 파라미터=event-time(resolved outcome 수), 자산클래스별 독립 FDR 스트림(풀링 금지). crypto=debounce+dependence-robust, macro=half-life 확대+archetype partial-pooling.
- **★구현 순서 = Walking Skeleton 먼저**: ledger 배선+dummy-event TDD(랜덤순서→state 100% 복원) 증명 → 통계 모듈 플러그인 → 최소 backtest 루프(crypto MVRV 7d). 로직+인프라 동시 테스트 금지.

## 5. T3(btn-Codlearn) 계약 표면 (wire 대상)
1. **카드 계약** `AssumptionCardLike` Protocol — Registry 가 macro/commodity/equity/crypto 카드 통합 보관.
2. **검증 엔진** `AssumptionValidationEngine.validate(card,...)` → `fdr_significant` → `hysteresis_and_gate`.
3. **regime 승격** `HumanApprovalGate.approve()` → regime_model_version bump → UpdateController epoch 재검증.
4. **live 루프** `LiveCorrelationLoop` harvest 호출처 = orchestrator(사이클 종료 시).
5. **event ledger 계약** = 11 event schema + (assumption_id,version) join + FDR decision_time 불변.

## 6. ★ 미해결 / 교차세션 조율 항목
- **event ledger 본체 = btn-Inv(T1) IA-1 도메인** (결정 PIT log + outcome join). btn-button 의 BB-4 는 **read-only 소비**. btn-button 은 계약 + 최소 reference stub 만 제공. → **btn-Inv 와 ledger schema 합의 필요**.
- **R5 맹점 1 cross-asset 종속성**: FDR 스트림 분리가 거시 regime 의 cross-asset 동시영향 무시 → 상위 regime 변화 시 하위 자산 cascade reset 필요. = **T3 ATMS 의존전파 + 거시 base-layer→하위 conditioning** 으로 해소 (T3 조율).
- **R5 맹점 2 Revision Drift**: 거시 사후수정 시 "결정 vs 수정된 진실" 괴리 측정 루프 부재 → revision-drift monitor 필요 (btn-Inv vintage 연계).
- crypto on-chain 데이터 소싱(CoinMetrics) = btn-Inv 데이터 도메인 의존.

> 본문 설계 = `DESIGN-button-v2.md` §10.1~10.7. 라운드별 raw = `.consult-button-R{1..5}.txt`. btn-button 은 본 결정으로 V0~V6(progress-T2 §v2) 빌드 진입.
