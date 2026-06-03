---
tags: [type/consult-brief, domain/inv, scope/equity-industry-dispatch, round/2]
date: 2026-06-03
purpose: claude-web + gemini-web R2 — §K 실행 레이어(cross-sectional 종목 선택) + C2 cross 3소비자 라우팅 확정. R1(C1~C5) 수렴 후속.
---

# R2 외부검토 — 실행 레이어 + cross 라우팅 확정

> 페르소나: 멀티에셋 퀀트 리서치 디렉터. 코드어 0, 통계·실행가능성 집중. 산업 분류는 확정(검토 제외).

## §0. R1 결론 (맥락 — 매 호출 새 대화라 동봉)

R1(C1~C5)에서 두 모델(당신 + 다른 모델) 수렴:
- **C3 forward alpha**: 주식엔 실재 → forward 횡단면 IC를 산업 study **1차 산출물**로(coin의 부재 전제 폐기). horizon-tagged: PEAD 1-3M / 모멘텀 3-12M / value 3-5Y 장기(중기 아님). breadth(주식 수백 종목)가 작은 IC(0.02-0.05)도 IR로 누적시킴.
- **C1 측정축**: 과소. 주식 필수 추가 = PIT-fundamentals safety / 생존편향+delisting / 유동성-티어 IC. PEAD·발생액은 측정축이 아니라 신호 후보(signal library). intraday 제외.
- **C2 cross**: "산업=노출 보고 / 통합=single-writer 조립" 분담은 옳으나, RegimeGlasso(공분산)·Diebold-Yilmaz(FEVD 비대칭)·customer momentum(forward 예측)·I-O centrality(정적 특성)를 한 cross 구조로 조립하면 PSD 붕괴 → **3소비자 라우팅**으로 분리(§2).
- **C4 비용**: net-cost 3bps = market impact 누락(sqrt law). 한국 STT(매도 0.18-0.23%)가 지배 → 비대칭 비용. 다중검정 FDR(BY/e-process, BH 금지). 공매도 제약 → long-only-implementable IC.
- **C5 차용**: archetype 5종 > GICS(단 valid_from 사후편향 hazard → PIT 사전선언). skfolio CPCV purge+embargo 차용(현 walk-forward leakage 위험). characteristic factor model(toraniko류) = equity risk 분해 native 우월(RegimeGlasso는 cross-asset/regime). derive_weights·e-process·valuation 수식은 우리것 유지.

## §1. §K 실행 레이어 — 사용자 핵심 요구 (R1에서 미검토)

★사용자 박제: "산업별 어떤 지표가 의미있나로 끝나면 안 됨. **실제 매매가 일어나려면** 시총 몇 위 안 universe에서 해당 지표가 평균 대비 얼마나 차이 나는지로 골고루 산다든지가 있어야. PER·PBR 등 지표들의 상관계수가 계속 변하는 그림이다."

현 설계(잠정):
- **universe**: 시총 top-N (또는 섹터 내 시총 랭크).
- **cross-sectional spread**: universe(또는 섹터) 내 각 종목의 valuation 지표를 횡단면 z-score/percentile(universe 평균 대비). ⚠️ 현 코드는 own-history 시계열 분위(자기 과거 PER 대비)만 있고 cross-sectional은 gap.
- **selection**: archetype primary_metric 기준 싼 종목을 분산 매수(concentration cap = "골고루"). value-trap 게이트로 함정 종목 배제.
- **지표 유효성 시변**: PER/PBR/EV-EBITDA의 IC·상호상관이 regime따라 변함 → regime-conditional IC가 측정, derive_weights(w∝Ω·IC)가 시변 IC로 지표 가중 동적 조정.

## §2. C2 cross 3소비자 라우팅 (R1 결론 확정 검토)

R1 권고 = cross를 "3측정"이 아니라 3소비자로:
- RegimeGlasso(동시 조건부 의존) → 포트 구성용 공분산 Ω 단독.
- Diebold-Yilmaz spillover → regime·contagion 모니터 레이어(weight driver 아님).
- customer-supplier momentum → alpha 신호로 측정 14종 배터리 검증 후 IC→weight 경로.
- I-O centrality → 선택적 저빈도 정적 특성(우선순위 최하).

## §3. R2 질문

- **R2-1 (§K 실행 레이어 타당성)**: 위 cross-sectional selection 룰 양식이 실매매로 직결되나? 빠진 요소 — turnover/rebalance 주기, concentration cap 적정 수준, long-only(한국 공매도 제약) vs long-short, universe 시총 컷의 microcap 배제 기준? PER/PBR 지표 유효성 시변을 derive_weights 시변 IC로 처리하는 게 충분한가, 아니면 별도 "지표 상관 regime" 추적이 필요한가?
- **R2-2 (cross 라우팅 일관성)**: customer momentum을 cross가 아니라 alpha 신호(14종 검증)로 보내는 게 개념적으로 일관적인가? regime monitor로 격하된 DY spillover가 weight에 닿는 경로는 무엇인가(throttle overlay? de-risk 게이트?)? 이 라우팅이 사용자의 "지표 상관계수가 계속 변하는 그림"과 어떻게 연결되나?
- **R2-3 (과잉설계 최종 점검)**: §K + 3소비자 라우팅까지 더하면 산업 subagent 1기가 감당할 범위가 과한가? 산업 study(측정 14종)와 실행 레이어(§K)·cross 라우팅을 산업 subagent vs 통합 supervisor로 어떻게 분담해야 과부하 없이 실매매까지 닿나?

## §4. 원하는 답
R2-1~R2-3 각각: (a) 결함/반박 (b) 근거 (c) 양식 v3 구체 수정. 실행가능성(실제 주문 생성)과 과잉설계 경계 둘 다 점검. 분류 체계는 답하지 말 것.
