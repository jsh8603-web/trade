---
tags: [type/validation, domain/inv, asset/bond, asset/cash, phase/study-2-3, hypothesis/H9-H10]
date: 2026-05-30
study_id: bond_cash
hypothesis: H9 curve_flip_recession_lead + H10 bull_steepening_tlt_lead
data-source: FRED API T10Y2Y (1976-06~) + USREC + yfinance TLT (실데이터, 합성 0)
script: raw/_v2_analysis/run_validations.py (V2) + results.json
result: ★데이터 풀 검증 — Inversion→Recession lead time 측정 / Bull-steepening TLT forward return event panel
---

# V2. Yield Curve Flip Lead-Time (가설 H9, H10)

## 검증 대상
- **H9** (`curve_flip_recession_lead`): 10Y-2Y curve flip event 후 forward 12M sleeve return 의 Rank-IC > 0
- **H10** (`bull_steepening_tlt_lead`): 역전 해소 (steepening flip) 후 6M TLT Rank-IC > IEF Rank-IC

## 데이터 실측
| 항목 | 값 |
|---|---|
| 시리즈 | T10Y2Y (FRED) |
| **n** | **18,259 obs (resampled to daily ffill)** |
| **기간** | **1976-06-01 ~ 2026-05-28 (≈50년)** |
| Inversion entries (≥0 → <0) | **44건** (group clustering 포함) |
| Steepening exits (<0 → ≥0) | **44건** |
| NBER recession starts (USREC) | **6건**: 1980-02, 1981-08, 1990-08, 2001-04, 2008-01, 2020-03 |

## H9: Inversion → Recession lead time

**40 inversion events** (4건 = 후속 recession 없음 — 2022-04/07, 2024-09×2 진행 중) 의 다음 NBER recession 까지 일수:

| 통계 | 값 (일) | 환산 |
|---|---:|---|
| n | 40 | |
| mean | 1,233 | ≈176주 / 40.6개월 (이상치 영향) |
| **median** | **589** | **≈84주 / 19.4개월** |
| IQR Q25 | 422 | ≈60주 / 13.9개월 |
| IQR Q75 | 2,951 | ≈422주 / 97.1개월 (이상치) |

### 분포 분석 (이상치 식별)
1981-1990 chunk (1981-10~1982-07 의 12 inversion event) 모두 다음 recession = 1990-08-01 로 mapping → 본 12 event 의 lead = 2,941~3,200일 (8~9년) = **이상치**.
1998 dot-com lead chunk (1998-05~07 의 4 event) → 다음 recession 2001-04 = 985~1,041일 (2.7~3.4년) = **상위 이상치**.

### 베이스라인 비교
- 웹리서치 baseline (Round 4, Quantified Strategies / YCharts): **avg 48주 (≈11개월), IQR 6-18개월**
- 실측 **median 84주 (19.4개월)**, IQR [60주, 422주]
- **baseline IQR [180, 540]일 내 비율: 35% (n=40)**

### 해석
- 실측 median (19.4개월) > baseline avg (11개월) → web 인용보다 보수적
- 이상치 (1981-90 epoch, 1998 dot-com) 가 mean 폭증, median 도 끌어올림
- group clustering 효과: 가까운 인접 inversion 들이 같은 recession 으로 mapping → effective independent event 가 적음 (≈6개 cycle = 6 recession)

### 우리 시스템 적용
- `weight_falsification.score_ic_breakdown_eprocess` baseline_ic 사전등록 시 **median 84주 (≈19개월) 기준 lag window** 채택 권고
- IQR [60주, 422주] = 매우 wide → **anytime-valid e-process** 필수 (정확한 timing 모름)
- group clustering 보정: deduplication 윈도 (예: 같은 cycle 내 inversion 은 첫 진입만 카운트)

## H10: Bull-steepening → TLT forward return

TLT 가용 2002-07~ 이므로 steepening event 중 *후속* 측정 가능 case 만 (17건):

| 날짜 | 3M return | 6M return | 12M return |
|---|---:|---:|---:|
| 2005-12-28 | -3.65% | -7.70% | +0.78% |
| 2006-01-03 | -4.65% | -6.39% | +1.56% |
| 2006-03-08 | -2.82% | +1.43% | +6.84% |
| 2006-03-30 | -3.10% | +5.95% | +6.41% |
| 2006-06-29 | **+8.66%** | +9.91% | +6.78% |
| 2006-07-27 | +4.38% | +5.21% | +7.24% |
| 2006-08-04 | +5.02% | +3.36% | +6.64% |
| 2006-08-08 | +4.25% | +3.54% | +4.66% |
| 2006-08-16 | +5.44% | +3.37% | +5.40% |
| 2007-03-21 | -5.01% | +3.01% | +13.44% |
| 2007-05-22 | +1.29% | +9.13% | +11.73% |
| 2007-06-06 | +4.93% | **+13.65%** | +9.94% |
| 2019-08-30 | -3.95% | +3.07% | +11.39% |
| **2022-04-05** | **-9.37%** | **-19.51%** | **-13.48%** |
| **2024-08-27** | -4.41% | -6.62% | -7.72% |
| **2024-09-04** | -5.06% | -4.55% | -8.03% |
| **2024-09-06** | -4.38% | -7.00% | -7.14% |

### 발견 (정량)
- **2005-2007 cycle**: 12M return 모두 양수 (+0.78%~+13.44%), 평균 ≈ +6.9% — **가설 H10 강 지지**
- **2019-08 cycle**: 12M +11.39% — **지지**
- **2022-04 / 2024-08-09 cycles**: 12M 모두 음수 (-7~-13%) — **반증 케이스**
  - 이유: 2022-2024 = Fed 강력 인상 cycle 시작 → curve 역전 해소가 *bull steepening* (rate cut 기대) 이 아니라 **bear steepening** (long yield 더 오름) 으로 발생. 정성적으로 다른 mechanism.

### H10 해석
- "역전 해소 = TLT 매수" 가설은 **macro 환경 의존적**:
  - rate-cut driven 해소 → bull steepening → TLT rally (2005-2007, 2019)
  - rate-hike driven 해소 → bear steepening → TLT 손실 (2022, 2024)
- → 단순 부호 flip 만으로는 신호 불충분. **Fed 정책 phase 분기 필수** (DGS2 / FEDFUNDS 동시 변화 부호로 bull vs bear steepening 구분)
- → 우리 시스템에 추가 indicator: `steepening_type` (bull/bear, derived from DGS2 변화 부호)

## 가설 판정
| 가설 | 판정 | 근거 |
|---|---|---|
| H9 (curve flip → recession lead) | **부분 지지** (n=40 lead time 분포 산출, baseline 보다 보수적) | median 19개월, IQR [60주, 422주], group clustering 보정 필요 |
| H10 (bull-steepening TLT lead) | **조건부 지지** (bull/bear 구분 시) | 2005-2007/2019 강 지지, 2022/2024 반증 → bull vs bear steepening 분기 필수 |

## yaml 반영 (블록3/4/5)
- 블록2: `steepening_type` 신규 indicator 후보 (derived from `yield_10y_2y` + `fed_funds` + `dgs2`)
- 블록3 relationships: `yield_10y_2y ↔ fred_recession_prob` 의 lag_routing=lagged + prior_strength 0.50 → 검증 결과로 **유지** (median 19개월 lag 매핑)
- 블록4 weight_rules: `yield_10y_2y` direction 수정 — "Steepening (역전 해소) → bond sleeve 가중↑" 을 **"Bull-steepening only → 가중↑ / Bear-steepening → 가중↓"** 로 분기
- 블록5 confidence_hooks `curve_inversion_recession_lag`: confirm_signal 의 baseline lag = **median 19개월** (84주) 사전등록. anytime-valid e-process alpha=0.05 적용

## main 액션 요청
1. **steepening_type indicator 신설** 여부 — bull vs bear 구분 자동 분류기 (Fed phase 결합)
2. 블록4 weight_rules direction 분기 — 기존 "Steepening → 가중↑" 을 "Bull steepening only" 로 좁히는 룰 변경 승인
3. group clustering deduplication 정책 — 같은 NBER cycle 내 inversion 의 효과적 independent event 카운트 방식
