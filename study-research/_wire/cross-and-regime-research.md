---
title: "Cross-asset 관계 후보 (거시 외) + 자산별 regime-conditional 정의법 리서치"
tags: [study/wire, cross-asset, regime-conditional, factor-shadow, J축, read-only-research]
date: 2026-06-01
stage: "read-only 리서치 (코드/yaml 미수정, 산출 md 단독)"
scope: "다음 세션 코드화 준비 — cross-sleeve 공분산 후보 + PIT-safe regime split 후보 enumerate"
inputs:
  - "study-research/_factor_shadow/batch-std-beta-5sleeve.md (J축 batch 5 sleeve × 5 factor std β, n=5052 daily)"
  - "study-research/eq_us_cyclical/raw/validation-regime-conditional-poc.md (regime-conditional PoC: DGORDER→XLE sharpen)"
  - "study_session.yaml × 8 (gold/eq_us_cyclical/eq_intl/reit/commodity/bond_cash/crypto/eq_us_defensive)"
method: "기존 측정값(batch std β + yaml relationships prior + M3 macro-linkage) 종합 enumerate. ★신규 측정 X — 후보 도출 + 우선순위만"
hedge_note: "★전부 *후보* 수준. cross 공분산 부호는 batch same-day std β 공유 노출에서 *추론*이지 직접 cross-corr 실측 아님. forward lead-lag 후보는 PoC 의 '신호 생성 아닌 정제' 결론 + forward 전멸 패턴 경고를 prior 로 깔고 hedge."
---

# Cross-asset 관계 후보 + 자산별 regime 정의법

> ★두 작업 모두 **read-only 후보 enumerate**. 코드/yaml 미수정. 다음 세션 코드화·검증 진입점 설계용.
> 정량 단정 금지 — batch std β 는 *same-day contemporaneous* 측정이고, cross 공분산은 공유 factor 노출에서 *추론*된 후보다.

---

## 0. 두 작업의 근거 자료 요약

### 0.1 J축 batch std β (cross 공분산 후보의 정량 기반)

5 sleeve × 5 factor multivariate std β (HAC t), n≈5052 daily, 2006-01~2026-05. VIF≈1.0~1.14 (factor 거의 직교).

| sleeve / unit | rate | dollar | oil | credit | vol(VIX) |
|---|---|---|---|---|---|
| gold (GLD) | −0.215 [val] | **−0.317** [val] | +0.121 [val] | −0.014 [rej] | −0.011 [rej] |
| eq_cyclical (XLB·XLI·SOXX) | +0.105 [val] | −0.171 [val] | +0.036 [str] | −0.004 [rej] | **−0.687** [val] |
| xle_energy (XLE) ★별 unit | +0.121 [val] | −0.120 [val] | **+0.342** [val] | −0.037 [str] | −0.473 [val] |
| eq_intl (EFA·EEM) | +0.094 [val] | **−0.295** [val] | +0.043 [str] | −0.042 [str] | **−0.641** [val] |
| reit (VNQ) | −0.004 [rej] | −0.090 [val] | −0.004 [rej] | −0.025 [rej] | **−0.565** [val] |
| commodity (DBC) | +0.067 [val] | −0.205 [val] | **+0.613** [val] | −0.034 [str] | −0.141 [val] |

(gold rate/dollar/oil = SEED 재현 PASS. eq_us_defensive = batch 미포함, yaml prior 로 보완: rate XLU/XLP 음·XLF 양, VIX def_pure 음·fin 양.)

★핵심: **VIX(vol) factor 가 전 equity/reit/commodity 의 최대 공통 노출** (−0.14~−0.69). gold 만 vol reject. → cross-asset 공분산의 1차 채널 = **risk-off(VIX) 공통인자**.

### 0.2 regime-conditional PoC 결론 (regime 정의법의 prior)

- ✅ **이미 유의한 신호는 국면 조건화로 sharpen** (DGORDER→XLE k6: full +0.31 → highInfl +0.42, Bonferroni 생존).
- ❌ **dead 신호의 "국면 부활"은 대부분 다중비교/tail-snooping** (T10Y2Y→XLI: full 0 → highInfl −0.44 극적이나 보정 후 미생존 + belief-weight 소멸).
- ★결론: regime-conditional = **신호 정제(refinement) 도구이지 생성(creation) 도구 아님**. 따라서 아래 regime split 후보도 "이미 약하게라도 잡힌 관계를 또렷하게" 하는 용도로 한정 평가.
- ★PIT-safe 표준 = **expanding-median threshold + availability-month ffill** (full-sample median lookahead 차단). first-release 정렬.

---

## 작업 1: Cross-asset 관계 후보 매트릭스 (거시 외)

★분류 = (A) 공유 factor 강노출 → 공분산 후보 (B) factor 차별 → diversification/hedge 후보 (C) lead-lag forward 후보(★전멸 경고).

### 1.1 공유 factor 공분산 후보 (Σ=B·Λ·Bᵀ 의 off-diagonal)

| # | 자산쌍 | 공유 factor / 채널 | 예상 부호 (공분산) | 측정·코드화 상태 | 검증 우선순위 |
|---|---|---|---|---|---|
| C1 | **eq_cyclical ↔ eq_intl** | VIX −0.69 / −0.64 + dollar 동방향 + rate 동방향(+) | **강 양** (risk-on/off 동조) | batch β 양쪽 측정됨. SEED vol cell 신규 제안됨 (둘 다 [val]) | ★1 (가장 단단, vol pool 핵심) |
| C2 | **eq_cyclical ↔ reit** | VIX −0.69 / −0.57 (공통 risk-off) | **양** (vol 채널), 단 reit rate/oil≈0 으로 부분 차별 | batch β 측정. reit rate 는 daily 소멸(아래 R-caveat) | ★1 (vol pool, reit 가 vol pool 진입 신규) |
| C3 | **eq_intl ↔ reit** | VIX −0.64 / −0.57 + dollar 둘 다 음 | **양** | batch β 측정 | 2 |
| C4 | **commodity ↔ xle_energy** | **oil +0.613 / +0.342** (공통 oil-driven) | **강 양** (oil 채널 본체) | batch β 측정. xle = 별 unit 제안됨 | ★1 (oil pool 형성, gold↔oil 도 연결) |
| C5 | **gold ↔ commodity** | dollar −0.317 / −0.205 (둘 다 음) + oil +0.121 / +0.613 (둘 다 양, 약·강) | **양** (dollar 채널 + 약한 oil 동조) | batch β + M3 실측 gold↔oil Pearson +0.103 (약) | 2 (dollar 동조 단단, oil 동조 약·epoch 한정) |
| C6 | **gold ↔ eq_intl** | dollar −0.317 / −0.295 (둘 다 강 음) | **양** (dollar 약세 시 동반 상승) | batch β 측정. ★단 gold vol≈0 vs eq_intl vol −0.64 = risk-off 시 **분기** (아래 H1) | 2 (dollar 채널 양 / vol 채널 반대 = net 모호) |
| C6b | **gold ↔ commodity ↔ eq_intl** dollar triplet | dollar 음 노출 공유 (−0.32/−0.21/−0.30) | 3자 양 공분산 cluster | batch β | dollar factor pool 후보 |

### 1.2 factor 차별 → hedge / diversification 후보

| # | 자산쌍 | 차별 factor | 예상 부호 | 상태 | 우선순위 |
|---|---|---|---|---|---|
| C7 | **gold ↔ equity(cyclical/intl)** risk-off hedge | gold vol≈0 (reject) vs equity vol −0.6대 강음 | **risk-off 시 부의 공분산 후보** (VIX↑ → equity↓·gold flat~↑) | gold vol=reject 측정됨. ★단 gold 의 safe-haven 은 H5 TENTATIVE (panic sell 동조 위험) | ★1 (포트폴리오 hedge 핵심, 단 regime-conditional 必) |
| C8 | **bond(long Tsy) ↔ HY/equity** flight-to-quality | credit/HY OAS spike 시 Tsy↑·HY↓·equity↓ | **위기 시 부의 공분산** | bond_cash yaml relationships (HY OAS↔curve +0.55, flight-to-quality 명시). batch 미포함(bond sleeve) | ★2 (yaml prior 만, batch β 측정 필요) |
| C9 | **eq_us_defensive ↔ eq_cyclical** (def−cyc excess) | VIX: def_pure 음(yaml) vs cyclical −0.687 / XLF 양(yaml vix_term +) | **VIX↑ → cyclical↓ > defensive↓ = excess 양** (게이트의 risk regime 채널) | batch 가 def 미포함. cyclical vol cell 신규 제안. defensive 는 yaml prior | ★1 (batch SEED vol pool 채우면 def 도 equity_risk pool 통해 노출 — 본 cross 가 게이트 진입) |

### 1.3 cross-asset lead-lag (forward 예측) 후보 — ★전멸 경고 prior

| # | 후보 | 가설 | ★경고 | 우선순위 |
|---|---|---|---|---|
| C10 | commodity/oil → eq_cyclical(XLE) forward | oil 모멘텀이 energy equity 선행? | ★PoC: DGORDER(거시)→XLE 만 forward 생존, 나머지 forward 전멸. cross-asset forward 는 더 약할 가능성 | 3 (低, forward 전멸 패턴) |
| C11 | stablecoin supply → BTC (crypto 내부) | dry-powder lead | crypto yaml: Granger lag7d 유의 but **bidirectional reflexive** (BTC→supply 도 유의) | 3 (reflexive guard 必, 이미 yaml 반영) |
| C12 | HY OAS → equity forward | credit이 equity 침체 선행 | bond_cash yaml prior 만, forward IC 미측정. PoC 교훈상 contemporaneous 가 dominant | 3 |

★lead-lag 후보 전반 = PoC 의 "contemporaneous risk-on/off 가 dominant, lead alpha 부재" (eq_cyclical regime_reading 직접 인용) 를 prior 로 → **낮은 우선순위 + forward 전멸 falsifier 부착 필수**.

### 1.4 cross 후보 종합 해석

- **Σ off-diagonal 의 1차 채널 = VIX(risk-off) 공통인자** (C1·C2·C3·C9). batch 가 5 sleeve vol [val] 측정 → SEED vol cell 채우면 equity_risk pool 활성, cross 공분산이 게이트에 들어옴. ★L축 공통인자 1회 계상 + PSD 불변식 준수 의무.
- **2차 채널 = dollar pool** (C5·C6·C6b: gold/commodity/eq_intl 전부 dollar 음).
- **3차 = oil pool** (C4: commodity↔xle, gold 약 동조).
- **hedge 채널 = gold/bond 의 vol·credit 차별** (C7·C8) — 단 둘 다 위기 시 부호 불안정(gold panic sell H5 / bond은 rate-shock vs flight 분기) → regime-conditional 로만 신뢰.

---

## 작업 2: 자산별 regime-conditional 정의표 (PIT-safe)

★거시 inflation/growth 국면 외에, 각 자산 고유 regime split. PIT 표준 = **expanding-median + availability ffill** (PoC 검증). 무료 데이터(FRED/Yahoo/CoinMetrics 등) 가능성 명시.

| 자산 | regime 정의 (자산 고유) | PIT-safe 데이터 (무료) | split 가설 (어느 관계가 국면서 변하나) | 우선순위 |
|---|---|---|---|---|
| **gold** | **real-rate regime** (DFII10 상승/하락) + **risk-off(VIX) regime** + decoupling regime (자체 monitor) | FRED DFII10 (실질금리, daily, same-day market-priced) / VIXCLS / decoupling_monitor(자체) | real_rate 하락 국면 = rate β 강 음 / decoupling 발동 = real_rate 채널 약화 + cb_demand 우위. ★H5: risk-off 시 safe-haven vs panic-sell 부호 반전 | ★1 (yaml 이미 decoupling_monitor 정의, real-rate split 단단) |
| **reit** | **rate cycle regime** (long-rate 상승/하락) + **VIX regime** | FRED DGS10 / DFII10 (level·Δ, daily) / VIXCLS | ★batch: reit rate β 가 daily 소멸(−0.004) but yaml thesis = rate-duration 효과 = **lower-freq/level 효과**. → **monthly/level rate regime split 시 rate 민감 부활 가설** (daily 로는 안 잡힘) | ★1 (★daily vs monthly axis 차이 = regime split 의 직접 동기, PoC 패턴) |
| **crypto** | **FGI 5-state** (belief primary) × **halving phase 4단계** | alternative.me FGI (daily 무료) / 결정론 halving schedule (코드만) | yaml 실측: MVRV→fwd IC 가 FGI×halving cell 별 −0.03(markup) ~ −0.61(distribution). ★extreme_fear & post_18_24m = mean-revert 최강 | ★1 (yaml 이미 20 cell 측정·채택, 최성숙) |
| **eq_us_cyclical** | **investment clock early/mid/late** (= inflation 국면 PoC) + **VIX risk regime** | FRED CPIAUCSL yoy(pub-lag ~12d) / T5YIE / VIXCLS | ★PoC 검증: high-inflation 국면서 DGORDER→XLE sharpen (+0.42, 생존). VIX regime 시 cyclical−defensive excess 채널 변동 | ★1 (PoC 가 직접 입증한 유일 케이스) |
| **eq_intl** | **dollar 강/약 regime** + **EM risk regime** (risk-on/off) | FRED DTWEXBGS (broad dollar, daily) / VIXCLS / EMB-spread proxy | yaml regime_reading: [risk-on·달러약] = EM 아웃퍼폼 / [risk-off·달러강] = flight-to-quality. dollar regime 시 dollar β·momentum 가중 반전 | ★2 (dollar β 단단, EM risk split 검증 필요. ★China credit '선행' 박제 격하 prior) |
| **commodity** | **backwardation/contango** (roll regime) + **dollar regime** + **financialization(VIX>30)** | DBC/개별선물 roll yield(Yahoo 파생) / DTWEXBGS / VIXCLS | yaml: contango_flip flag 시 carry 가중 즉시 감액. VIX>30 시 Tang-Xiong financialization → cross-sector corr spike 0.37 (diversification 소멸) | ★2 (contango regime = 자산 고유·단단. financialization regime = cross 공분산 직접 변동 → C4 와 연계) |
| **bond_cash** | **yield curve 정상/역전** (T10Y2Y 부호) + **credit regime** (HY OAS) + rate-shock sub-regime | FRED T10Y2Y (daily, same-day) / BAMLH0A0HYM2 / NFCI | yaml: 역전 = 침체 선행 / 역전 해소 = recovery. risk-off(HY spike) = long Tsy 가중↑·HY↓ (flight-to-quality, C8 직접) | ★2 (curve regime = same-day knowable, PIT 쉬움. HY OAS full history 대기) |
| **eq_us_defensive** | **VIX risk regime** + **credit stress regime** (NFCI/BAA10Y) | FRED VIXCLS / NFCI / BAA10Y (daily) | yaml: credit_stress regime → def_pure excess 양 / fin excess 음. ★단 yaml v3 = credit regime n=9 INSUFFICIENT (HY OAS full 대기). VIX regime 시 def−fin 분기 | ★3 (credit regime 표본 부족, HY OAS full history 선행 의무) |

### 2.1 PIT-safe 데이터 가용성 정리

- **즉시 가능 (same-day market-priced, lookahead 無)**: VIXCLS, DFII10, DGS10, T10Y2Y, DTWEXBGS, T5YIE, FGI, BTC funding — 전부 무료 FRED/alternative.me/Binance.
- **pub-lag 있으나 PIT 처리 가능**: CPIAUCSL(~12d), NFCI, BAA10Y — first-release + availability-month ffill (PoC 표준).
- **결정론**: halving phase, contango/backwardation(선물 term structure 계산).
- **대기/부족**: HY OAS full history(1996~, ALFRED key — bond_cash/gold/defensive 공통 의존), WGC quarterly CB.

---

## 종합 우선순위 (코드화·검증 top 5)

★기준 = (1) batch β 로 이미 측정돼 단단 (2) regime PoC 가 입증한 정제 패턴 적용 가능 (3) 게이트 진입(cross 공분산 활성) 임팩트 (4) PIT-safe 데이터 즉시 가용.

| 순위 | 항목 | 종류 | 근거 | 다음 세션 액션 |
|---|---|---|---|---|
| **1** | **VIX(vol) pool 형성 → equity/reit cross 공분산** (C1·C2·C9) | cross | batch 5 sleeve vol [val] 측정, 현 SEED 전부 HOLD. pool 채우면 risk-off 공통인자 게이트 진입 | SEED vol cell 5개 신규 (batch 제안값) + def 가 equity_risk pool 통해 vol 노출 받는지 검증. ★L축 1회 계상 + PSD |
| **2** | **eq_cyclical inflation regime split** (DGORDER→XLE sharpen) | regime | PoC 가 직접 입증 (Bonferroni 생존 유일 케이스), refinement 도구로 robust | PoC 코드를 production regime-conditional 경로로 이식 (expanding-median PIT). belief-weight soft 버전 병행 |
| **3** | **crypto FGI×halving regime split** | regime | yaml 이미 20 cell 측정·채택, 최성숙. PIT 데이터 즉시 가용 | confidence_hooks 의 conditional IC 라이브 갱신 wire (yaml code_change_plan 이미 설계됨) |
| **4** | **oil pool: commodity↔xle_energy** (C4) + commodity financialization regime | cross+regime | batch oil +0.613/+0.342 강노출. xle 별 unit 제안됨. VIX>30 financialization regime 이 cross corr 직접 변동 | xle_energy SEED 별 cell 추가 + commodity↔xle oil 공분산 + financialization regime overlay |
| **5** | **dollar pool: gold↔commodity↔eq_intl** (C5·C6·C6b) | cross | 3자 dollar 음 노출 단단 (−0.32/−0.21/−0.30) | dollar pool 공분산 후보 측정. ★gold↔eq_intl 은 vol 채널 반대(C7 hedge) 라 net 부호 regime-conditional 평가 |

### 보류·低 우선순위 (falsifier 부착)
- **cross-asset forward lead-lag (C10·C11·C12)**: forward 전멸 패턴 + reflexive 위험. contemporaneous 우선, forward 는 falsifier 깔고 탐색만.
- **reit rate regime (monthly/level)**: 가설 흥미로우나(daily 소멸 vs level thesis) 측정 axis 재정식화 필요 — 우선순위 2 그룹 후반.
- **eq_us_defensive credit regime**: HY OAS full history(ALFRED) 선행 의무, n=9 INSUFFICIENT.

### ★불변식 / 주의 (코드화 시)
- **reflexive loop 차단** (belief→_macro 차단), **L축 공통인자(VIX pool) 1회 계상 + PSD**, **opt-in off 무회귀**, analyst-level lens 다운그레이드 금지 (CLAUDE.md 통합 불변식).
- batch β = **same-day contemporaneous** → cross 공분산 후보는 동조 측정이지 forward 예측 아님. 부호 단정 금지, hedge.
- regime split = **정제 도구이지 생성 도구 아님** (PoC). dead 관계의 "국면 부활"은 다중비교/snooping 의심 — Bonferroni + belief-weight 이중 게이트.

---

## 산출 메타
- 본 파일 = `study-research/_wire/cross-and-regime-research.md`.
- ★코드/yaml 미수정 (read-only). 측정 신규 X — 기존 batch β + yaml prior + PoC 결론 종합 enumerate.
- 다음 세션 = 위 top 5 부터 코드화·검증 진입.
