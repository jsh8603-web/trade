---
tags: [type/theory-notes, domain/inv, scope/equity-kr, topic/rotation-timing, status/pre-registered]
date: 2026-06-05
owner: semi-analyst (kr-equity team, opus 1m)
purpose: ★rotation 이론(산업동향 fundamental) 수립 + 부호 사전확약. 통계는 이 이론을 검증하는 도구.
---

# 12산업 rotation 이론 베이스 + 부호 사전확약 (S1 = 가설 원천)

> ★사용자 파이프라인 확정(ckpt-202606062230): "어느 업종 살까 = 순수 통계 아니라 ★산업동향(이론·fundamental)
> 관점. 이론을 통계가 검증하는가 = 파이프라인 본질". = 12종목 capsule S1 원칙(가설 부호 사전확약 → 측정 검증
> → 일치 채택)과 동일. rotation 1차가 이 순서 건너뛰고 가격통계부터 던진 게 결함 → 본 theory-notes 로 소급 정렬.
>
> ★verdict 라벨: STRONG(이론+통계 둘 다) / TENTATIVE(이론명확+통계 underpowered) / REJECTED(이론있고 통계반증)
> / ★data-mining 의심(이론없이 통계만 = 채택불가).

## §0. rotation 이론의 본질 (sector rotation 학술 + 실무)

- **sector rotation** = 경기·cycle 국면에 따라 업종 상대수익이 갈린다 (Sassetti-Tani 2006, Stovall sector rotation model).
- ★단 학술 경고: business-cycle clock 식 기계적 rotation = myth 위험(Molchanov 2024). → ★**산업별 고유 cycle driver
  (crack/memory/철광석/리튬 등 fundamental)** 가 진짜 alpha (자문 A). 가격 momentum 단독 = 공통인자(외국인flow) 재포장 위험.
- 한국 특수: 외국인flow·USDKRW가 전 산업 공통 지배(PC1 55%) → 산업 고유 cycle 의 공통인자 직교 성분만 진짜 rotation.

## §1. 산업별 cycle driver 이론 + ★부호 사전확약 (데이터 접촉 전 동결)

| 산업 | cycle driver (fundamental) | 이론 (산업동향 메커니즘) | ★사전확약 부호 (forward) | source |
|---|---|---|---|---|
| **steel** | 철광석가 + 중국 수요(조강) | 철광석↑ = 원가↑이나 동시 철강 수요·가격 cycle 상승 동행(China property/infra). 철광석 모멘텀 = 철강 업황 상승 proxy | **양**(철광석 Δ↑ → 철강 forward↑, 업황 cycle) | TIO=F + FXI |
| **battery** | 리튬가 + EV 수요 | 리튬↑ = 2차전지 소재 cost-push이나 EV 수요·생산 cycle 상승 동행(수요 견인 국면). 리튬 cycle = 전지 업황 | **양**(리튬 yoy↑ → 2차전지 forward↑, 수요 cycle) | LIT |
| **chemical** | 유가/나프타 + 중국 PMI | ★나프타(유가)↑ = 화학 원가↑ → 마진 압박 → 화학주 약세 (cost-push, spread 압축). 유가 高 = 화학 약세 | **음**(유가/나프타 yoy↑ → 화학 forward↓, 마진압박) | CL=F + XLB |
| **refining** | 정제마진(crack) + 유가 | crack↑ = 정유 마진↑(직접). ★단 유가 level 高 = cycle 끝물 mean-reversion(자문). crack Δ = 마진 개선 | **양**(crack Δ↑ → 정유 forward↑) / 유가 level **음**(mean-reversion) | refining_cycle.parquet |
| **auto** | 글로벌 신차 판매 + USDKRW | 글로벌 자동차 수요↑ = 한국 수출차 판매↑. CARZ 모멘텀 = 업황 | **양**(글로벌차 Δ↑ → 자동차 forward↑) | CARZ |
| **shipbuilding** | 운임(BDI) + 신조선가 | 운임↑ = 해운 업황↑ → 신조선 발주↑ → 조선 수주 cycle. ★단 조선 슈퍼사이클 = re-rating(자문 valuation guard) | **양**(BDI yoy↑ → 조선 forward↑, 수주 cycle) | BDRY |
| **semiconductor** | 메모리 cycle(SOXX) + KRW | 글로벌 반도체 cycle↑(SOXX) = 한국 메모리 업황↑. ★단 capsule 종목선택이 primary | **양**(SOXX Δ↑ → 반도체 forward↑) | SOXX(=semi_ppi 일부) |
| **telecom** | (cycle 직접 부재) ARPU/5G 무료 API 부재 | ★방어주 = 반도체 cycle 약세기 상대강세(rotation into defensives). 자문: timing 보다 dividend-carry tilt primary | semi_ppi yoy **음**(반도체 cycle 약 → 통신 방어 강세) / carry tilt | momentum proxy 한계 |
| **consumer** | (cycle 직접 부재) 소매판매/K-food 무료 KR 부재 | 내수 = 경기 둔화기 방어 + 상대모멘텀 reversal(과열 되돌림) | 상대mom **음**(reversal) | momentum proxy 한계 |
| **financial** | 금리커브(ktb10y/3y) + 경기 | 경기선행↑ + 금리 steepening = NIM↑ → 금융주↑(경기 cyclical). 금리커브 = cycle | cli_chg **양**(경기↑ → 금융 forward↑, NIM) | regime_series 금리커브 |
| **bio** | (cycle 직접 부재) FDA/임상 idiosyncratic | 임상·승인 = 종목별 idiosyncratic event 지배. 산업 공통 cycle 약 → rotation 어려움 | 사전확약 부호 없음(이론상 산업 timing 부재) | 무료 부재 |
| **aitech** | hyperscaler capex(cycle 직접 어려움) | AI/IT = 반도체 cycle 연동(capex)이나 방어적 IT 성분. semi_ppi 음 = 반도체 끝물 IT 되돌림 | semi_ppi yoy **음**(약 prior) | momentum proxy 한계 |

## §2. momentum 처리 (★data-mining 차단)

- ★가격 momentum 자체 = 신호 아님. "업종 과열 되돌림(reversal) / 실적모멘텀 지속(persistence)" **이론을 검증하는 통계**.
- ★**공통인자 residualize 후 잔존 여부**가 판별 (자문 Q-a): 산업 momentum이 residualize(외국인flow/USDKRW/글로벌 cyclical 제거) 후
  **소멸** = market momentum×beta = 공통인자 재포장 = ⛔data-mining 의심(채택불가) / **잔존** = idiosyncratic 진짜 신호.
- 이론 근거: cyclical 산업 momentum = flow persistence 오염(intermediate 6-12m), 방어주 reversal = idiosyncratic.

## §3. ★사전확약 부호 동결 선언 (PIT, 데이터 fitting 금지)

본 §1 부호는 **데이터 측정 결과 보기 전 이론으로 확약** (one-sided pre-commit). 측정 후:
- **부호 일치 + 통계 통과** → STRONG / TENTATIVE(통계 약).
- **부호 반대(이론 반증)** → REJECTED (사후 부호 뒤집기 ⛔금지).
- **이론 없이 통계만 생존** → data-mining 의심 (채택불가).

## §4 source URL / 근거
- sector rotation: Stovall (1996) sector rotation model / Sassetti-Tani (2006) "Dynamic asset allocation using systematic sector rotation".
- business-cycle clock myth 경고: Molchanov (2024) — 기계적 rotation 한계.
- cost-push (chemical/유가): naphtha-ethylene spread 압축 메커니즘 (화학 업황 실무).
- 자문 RESULTS: D:/projects/Inv/.consult-kr-rotation-design-RESULTS.md §2 Q-a (고유 cycle = primary alpha).
- ⛔ 증권사 섹터 리포트 직접 정독 = 본 capsule 범위 외(무료 학술/실무 메커니즘 기반). 리포트 정독 = collector_plan(후속).
