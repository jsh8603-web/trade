---
tags: [type/raw, domain/inv, asset/bond, asset/cash, phase/study, round/1]
date: 2026-05-30
round: 1
topic: 채권 가격결정 원리 — Duration·Convexity·Carry 분해
source: WebSearch (native fallback, 자문채널 경합 회피)
---

# Round 1 — 채권 가격결정 원리 (Duration·Convexity·Carry decomposition)

## 검색어
`bond pricing duration convexity carry return decomposition fixed income textbook`

## 원천 (URL hyperlink)
- [Decomposing long bond returns: A decentralized modeling approach (Carr/NYU)](https://engineering.nyu.edu/sites/default/files/2021-06/DecomposingLongBondReturns-Carr.pdf)
- [Duration & Convexity — Fixed Income Bond Basics (Raymond James)](https://www.raymondjames.com/wealth-management/advice-products-and-services/investment-solutions/fixed-income/bond-basics/duration-and-convexity)
- [Understanding duration and convexity of fixed income securities (Vinod Kothari)](https://vinodkothari.com/wp-content/uploads/2014/01/duration-and-conexity.pdf)
- [Bond Risk & Return: Duration & Convexity (AnalystPrep CFA L1)](https://analystprep.com/cfa-level-1-exam/fixed-income/bond-risk-and-return-using-duration-and-convexity/)
- [Bond Price Change Using Duration & Convexity (AnalystPrep)](https://analystprep.com/cfa-level-1-exam/fixed-income/bonds-percentage-price-change-using-curve-based-duration-and-convexity/)
- [Duration and Convexity Effect on Price Change (AnalystPrep)](https://analystprep.com/cfa-level-1-exam/fixed-income/percentage-price-change-bond-duration-convexity/)
- [Duration & Convexity of a Bond Portfolio (AnalystPrep)](https://analystprep.com/cfa-level-1-exam/fixed-income/duration-and-convexity-of-a-bond-portfolio/)

## 핵심 정제

### 1) Return 분해 (3-component)
채권 수익률은 세 요소로 분해된다:
- **Carry effect** = yield 가 변하지 않을 때 보유로 얻는 return (쿠폰 + roll-down)
- **Duration effect** = -D · Δy (yield 변화에 대한 1차 선형 노출)
- **Convexity effect** = +0.5 · C · (Δy)² (비선형 항, 항상 양수 → 투자자에게 유리)

### 2) Duration·Convexity 정의 (zero-coupon)
- Zero-coupon: Duration = time-to-maturity, Convexity = (maturity)²
- Coupon bond: cash-flow 별 value-weighted 평균. Modified duration = 가격 변화의 % 형태 표현.

### 3) Convexity 의 본질
- Higher yield volatility → higher expected return (convexity gain)
- 양의 convexity = yield 하락 시 가격상승 > yield 상승 시 가격하락 (asymmetric, 투자자 우호)
- 큰 yield shock 일수록 duration 만으로는 가격 예측 오차 커짐 → convexity 항 필요

## 우리 시스템 매핑

| 개념 | 우리 indicator 대응 | 코드 위치 |
|---|---|---|
| Carry (쿠폰+roll-down) | `roll_carry_yield` (DGS10 − DGS2 + level) | 블록2 indicators (미in_our_system) |
| Duration 1차 | `duration_bucket_id` × Δ`yield_10y_nominal` | 블록3 force-include 후보 |
| Convexity 2차 | (Δy)² 항 — long-duration 일수록 의미 큼 | 현재 미모델링, 부재 → collector_plan |
| Coupon-bond duration | ETF 단위 라벨 (TLT≈17, IEF≈8, SHY≈2) | 블록2 archetype |

## 가설 초안 (라운드 1)

**H1-A**: 일별 ETF return ≈ -D · Δy + 0.5·C·(Δy)² + carry/252. 잔차는 idiosyncratic + credit.
   - 반증: TLT 일별 return regress on Δ(DGS10), Δ(DGS10)² 의 R² < 0.7 OR D̂ sign 양수.

**H1-B**: Convexity premium = E[0.5·C·(Δy)²] > 0. long-duration 일수록 크다.
   - 반증: TLT vs SHY 의 일평균 양의 convexity gain 이 통계적 유의 0 (t-test).

**H1-C**: Carry-to-total-return 비율은 평탄커브에서 감소, steepening 에서 증가.
   - 반증: rolling 60일 carry beta 가 steepening regime 에서 음 OR 평탄커브에서 양수 분리 안 됨.

## 검증 방향 초안 (라운드 1)
- Bond ETF (TLT/IEF/SHY/BIL/HYG/LQD) 일별가 + FRED DGS10/DGS2 → ΔP/P 의 (Δy, Δy²) 회귀.
- breakeven 분해: nominal Δy = Δ(real) + Δ(breakeven) 분리. real 변동 vs breakeven 변동 의 ETF 영향 비교.
- shock window event study (FOMC 일 ±5d).

## Gap / 라운드 2 로 넘길 질문
1. Investment Clock 4국면별 채권 거동의 *수치적* 비교가 필요 (R2 검색어 후속)
2. credit cycle (HY OAS) 의 carry-vs-spread-widening trade-off (R3)
3. 검증 방법론 (Rank-IC, e-process) 의 채권 strategy 적용 사례 (R4)
4. cash sleeve optionality 정량화 (R5)
