---
tags: [type/m1-linkage, domain/inv, study/macro, phase/M1]
date: 2026-05-30
study_id: macro
phase: "M1 거시-종목 연관성 (factor loading B + Λ 실측)"
data: "data/historical 실 일별 n=756, 2021-12~2024-12. ⛔합성無, U3 실현수익률 전용"
script: raw/m1_factor_linkage.py / output: raw/m1-output.txt
note: macro→stock factor linkage 실측 — system_priors.factor_implied_cross_cov 실증 입력 + 국면조건부성 + 설계 caveat.
---

# M1 거시-종목 연관성 — factor loading B + Λ 실측

## 해석 (M1 범위)
M1~M4 세부분담 문서 미정의 → macro 애널리스트 해석: M1 = **foundational** = 종목 sleeve 의 거시 named
factor(rate/dollar/oil/credit) loading B + 팩터공분산 Λ 실측 → `system_priors.factor_implied_cross_cov`
(B Λ Bᵀ + diag idio) 실증 입력. ★U3 reflexive 차단 준수 = 실현수익률 전용(belief/flag 不유입).

## 측정 (실데이터 n=756, factors=rate(Δus10y)/dollar(dxy r)/oil, sleeves=us_stock/tech/gold)

### 1. factor loading B (전체)
| sleeve | rate | dollar | oil | idio_var |
|---|---|---|---|---|
| us_stock(sp500) | +0.008 | **−0.879** | +0.020 | 1.1e-4 |
| tech(nasdaq) | +0.009 | **−1.079** | +0.001 | 2.0e-4 |
| gold | **−0.036** | −0.577 | +0.085 | 6.0e-5 |

- ★주식의 **rate loading ≈0** — 금리→주식 직접전이 거의 없음(앞 검증 sp500~us10y 매개와 정합). 주식은
  **dollar 채널**로 거시에 연결(loading −0.88~−1.08). gold 는 rate(−0.036)+dollar(−0.58) 양 채널 직접.

### 2. ★국면조건부성 (M1 핵심 입증) — loading 차이 rate-UP − rate-DOWN
| sleeve | Δrate | Δdollar | Δoil |
|---|---|---|---|
| us_stock | −0.025 | **−0.405** | −0.041 |
| tech | −0.037 | **−0.451** | −0.064 |
| gold | +0.014 | +0.040 | +0.060 |

- 주식의 **dollar loading 이 rate-up 국면에서 거의 2배**(us_stock −0.998 vs −0.593 / tech −1.210 vs −0.759).
  = **거시→종목 전이가 국면조건부**(M1 thesis 실증). rate-up(긴축/리스크) 국면에서 달러 충격이 주식에
  훨씬 강하게 전이. gold 는 국면 안정(거시 직접자산).

### 3. factor_implied_cross_cov 검증 (PD + implied vs 경험)
- 전 regime PD ✅ (eig_min ~1e-4).
- **implied vs 경험 sleeve 상관**:
  - us_stock~gold: implied +0.13 vs 경험 +0.09 (Δ+0.04) ✅ **cross-asset-class 잘 잡음**
  - tech~gold: implied +0.11 vs 경험 +0.07 ✅
  - us_stock~tech: implied +0.12 vs 경험 **+0.96** (Δ−0.84) ⚠️ **within-equity 공통 못 잡음**

## ★중요 설계 caveat (M1 발견 — 통합 시 반영)
거시 named factor(rate/dollar/oil)는 **cross-asset-class linkage(stock↔gold↔commodity)용**으로 적합
(implied≈경험). 그러나 **within-equity 공통(us_stock~tech 0.96)은 못 잡는다** — 이건 "equity market
factor"(broad 주식 베타·risk-on/off)이지 거시 driver 가 아니다. 함의:
1. `factor_implied_cross_cov` 의 named factor 는 **sleeve *간*(us_stock/gold/commodity/bond) 공분산**에만
   써야 정합. within-sleeve(같은 equity sleeve 내 종목간)는 해당 sleeve 자체 모델(equity 팩터) 소관.
2. credit(HY OAS) 팩터 추가 시 risk-on/off 일부 포착 가능 — daily 부재로 collector 이연(통합 시 보강).
3. 주식 sleeve 의 거시 연결은 **dollar 채널 + 국면조건부**가 본질(rate 직접 아님). cross-sleeve cov 의
   stock 행은 dollar loading 의 regime 의존을 반영해야(rate-up 시 dollar 전이 2배).

## 미해결 / 후속 (M2~M4 후보)
- credit/VIX 팩터 추가(collector DFII10/HY OAS/VIX) 후 B 재추정 — risk-on/off 채널 보강.
- kr_stock/bond/coin sleeve loading(데이터 확보 후) — 현 us_stock/gold 만.
- factor_cov Λ 의 regime 의존(rate-up Λ_rate=5.7e-3 vs down 4.0e-3 = 금리변동성 국면차) 명시 반영.
- equity market factor 를 named factor 에 추가할지(cross-sleeve 정합 위해) vs sleeve 내부 처리 — 통합 결정.
