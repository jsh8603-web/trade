---
tags: [type/m4-factor-expansion, domain/inv, study/macro, phase/M4-followup]
date: 2026-05-30
study_id: macro
phase: "M4 후속 — cross-sleeve factor 축 확장 분석"
data: "VIF 실측 raw/m4_factor_vif.py(n=737 실데이터) + cross-session M3 verdict(m4-collection.md)"
note: 현 FACTORS=(rate,dollar,oil,credit) 확장안 + 직교성(VIF) + factor_betas_seed FACTORS 튜플 영향. ⛔합성無.
---

# M4 cross-sleeve factor 축 확장 분석

> 현 `core/study/factor_betas_seed.py` FACTORS=(rate, dollar, oil, credit). 거시 regime 레이어엔
> term spread·real rate·HY/IG·breakeven·NFCI 다 있으나 cross-sleeve factor 축엔 rate에 뭉뚱.
> 제약: factor 직교성(VIF) + 1회계상(L축) + 각 sleeve β OOS 실측(합성금지).

## 0. 직교성 VIF 실측 (raw/m4-vif-output.txt, n=737 실데이터)
| factor 집합 | VIF | 판정 |
|---|---|---|
| rate/dollar/oil (현 가용 3종) | 1.25 / 1.25 / 1.05 | ✅ 전부 <1.3 직교충분 |
| +vol(VIX 대용, sp500 20d 실현변동성) | rate1.25 dollar1.25 oil1.05 **vol1.00** | ✅ vol 완전직교 |
- corr(vol, rate/dollar/oil) = −0.002 / −0.027 / −0.021 = **vol 거의 완전 직교**(L축 중복 없음).
- ⚠️ corr(rate, dollar) = **+0.415** — 현 rate/dollar 도 중간 공통분산(긴축=금리↑+달러↑). rate 분리 시 이 축이 더 얽힘.

## 1. ① term spread·real rate를 rate에서 분리할 가치 — **분리 권고(collector 의존)**
### 근거 (cross-session M3 실측, m4-collection.md)
자산군이 rate의 *다른 측면*에 반응 — 단일 "rate"로 뭉뚱그리면 정보 손실:
| sleeve | rate 반응 | 채널 해석 |
|---|---|---|
| **REIT(VNQ)** | rate β **−3.82**(t−5.65, 9/10 음수유의) | level/cap-rate 직접 할인(명목·커브) |
| **gold** | rate β −0.295, **E4(인하) −0.142 절반** | anti-**real rate**(E4 decoupling=real≠nominal mechanism) |
| **주식(cyclical/intl)** | rate β ≈0 (dollar t≈4× rate) | 직접 무력, **dollar 매개** |
→ REIT=명목/커브, gold=real rate, 주식=무(dollar). **rate 단일축은 이 3 반응을 한 칸에 못 담음** → 분리 가치 확정.

### 분리안 + 직교성
- `rate` → **`real_rate`(DFII10) + `term_spread`(T10Y2Y)** 2축 분리. (명목 10Y는 = real+breakeven 회계항등이라 중복 → 명목 대신 real_rate 채택.)
- ⚠️ VIF 주의: {nominal10Y, real_rate, breakeven} 동시 포함 = 완전공선(Fisher 항등) ⛔. {real_rate, term_spread}는 더 직교(레벨 vs 기울기) — DFII10/T10Y2Y daily 확보 후 VIF 재측 필수(현 데이터 부재).
- breakeven(인플레)은 별 factor 후보지 rate 분리 대상 아님(§3).

## 2. ② credit factor β 실측 — **미측정(전 sleeve None) → collector 후 실측 의무**
- 현 seed: credit 칸 전부 None(M3 미측정). HY OAS(BAMLH0A0HYM2) daily 부재.
- 설계: HY OAS 확보 후 각 sleeve credit β OOS 실측. 경제 prior — REIT/eq_cyclical 高(risk-on 베타), gold 低/음(safe-haven), defensive 低. ⛔점추정 박제 금지(James-Stein 수축, m4 7원칙 준용).

## 3. ③ 신규 factor 후보 — 직교성·유효성 순위
| 후보 | 직교성 | cross-sleeve 유효 증거 | 판정 |
|---|---|---|---|
| **growth/industrial-demand**(copper-gold·CFNAI) | 미측(collector) | ★commodity **industrial↔precious +0.692**(dollar 통제 후 잔차=factor 미흡수 공통, m4-collection) | **1순위** — 구체적 미설명 cross-corr 직접 해소 |
| **vol**(VIX/MOVE) | ✅ **VIF 1.00 corr~0 실측** | risk-regime(위기 상관→1 수렴) | **2순위** — 직교 검증완료, 즉시 추가 가능(대용 vol 만, 실 VIX collector) |
| funding stress(SOFR-OIS·xccy) | 추정 직교(tail) | 위기 한정 sparse 신호 | 3순위 — tail-only, 상시 약 |
| RRP/준비금(유동성) | ⚠️ dollar·Fed BS 공선 의심 | 느린 추세 | 보류 — 직교성 낮음 |
- ★growth factor 가 1순위 근거: m4-collection commodity verdict 이 "industrial↔precious +0.692 = dollar 잔차 공통(산업수요) → **factor 1회계상으로 흡수 안 됨**" 명시 = rate/dollar/oil 로 못 잡는 공통분산이 *실측으로 확인된 유일* 케이스. growth(copper-gold ratio 또는 CFNAI surprise)가 이를 흡수.

## 4. factor_betas_seed.FACTORS 튜플 확장 영향
- 현: `FACTORS=("rate","dollar","oil","credit")` (4). betas 행 = (S, F=4), system_priors.factor_implied_cross_cov B(S,F)·Λ(F,F)·Bᵀ.
- 확장 시 **F↑ = sleeve당 추정 셀↑** → regime×sleeve 소표본서 over-parameterization 위험. James-Stein 수축이 noisy 셀을 pool 로 당기나 seed 정밀도 저하.
- **단계 권고(parsimony, F≤7)**:
  - **Phase A(즉시, 데이터 가용)**: `+vol` (VIF 1.00 직교 검증). `("rate","dollar","oil","credit","vol")` F=5.
  - **Phase B(collector: DFII10/T10Y2Y/HY OAS/copper)**: `rate`→`real_rate`+`term_spread` 분리 + `credit` β 실측 + `+growth`. → `("real_rate","term_spread","dollar","oil","credit","vol","growth")` F=7.
- ★튜플 확장 = **append-only + 신규 factor 기본 β=None(pool/hold)** → 기존 셀 불변(무회귀), 측정 전 노출 0 게이트 사각 회피(seed v1 TIER_HOLD 규약 재사용). FACTORS 순서 = betas 행 정렬이라 **append 만**(중간삽입 금지, 인덱스 깨짐).
- Λ(factor_cov) 차원 F×F 동반 확장 — 신규 factor 간·기존과 공분산 실측 필요(VIF 직교면 Λ 거의 대각).

## 5. 권고 요약 + 미해결
1. **즉시(Phase A)**: vol factor 추가(VIF 1.00 직교 검증완료). FACTORS append `"vol"`, β=None seed→shadow OOS 실측.
2. **collector 후(Phase B)**: rate→real_rate+term_spread 분리(REIT level vs gold real 분기 근거) + credit β 실측 + growth factor(industrial↔precious +0.692 흡수). DFII10/T10Y2Y/HY OAS/copper daily 적재 의존.
3. ⛔ **VIF 재측 의무**: real_rate/term_spread/breakeven 동시 포함 금지(Fisher 공선). collector 후 확장 factor 전체 VIF<5 재검증.
4. 미해결: 신규 factor β는 전부 OOS 실측 후 박제(현 데이터로 vol 외 측정 불가) — collector 확보가 선결.
