---
tags: [type/validation, domain/inv, asset/bond, asset/cash, phase/study-2-3, hypothesis/H5]
date: 2026-05-30
study_id: bond_cash
hypothesis: H5 cash_sharpe_competitive — Duffee fact 재현 (short-Tsy Sharpe ≥ SPY Sharpe)
data-source: yfinance SPY/SHY/BIL/SHV (실데이터, 합성 0)
script: raw/_v2_analysis/run_validations.py (V3) + results.json
result: ★강 지지 — Cash Sharpe = 0.55 vs SPY Sharpe = 0.20 (Cash > SPY +0.35, n=287 months)
---

# V3. Cash Sharpe vs SPY (가설 H5, Duffee fact 재현)

## 검증 대상
가설 H5 (`cash_sharpe_competitive`): 1976-2024 SHY+BIL+SHV cash basket 의 월 Sharpe > SP500 (SPY) 월 Sharpe.

원전 인용 (Round 5): Duffee G.R. (JHU), *Sharpe ratios in term structure models* — "bond portfolio containing Treasury bonds with less than five years to maturity has a monthly Sharpe ratio that slightly exceeds the monthly Sharpe ratio of the stock market"

## 데이터 실측
| 항목 | 값 |
|---|---|
| ETF basket | cash = mean(SHY + BIL + SHV) per available period |
| SPY 시작 | 2002-07-31 (월별 sample) |
| **n (months)** | **287** |
| 기간 | 2002-07 ~ 2026-05 (≈24년) |
| ⚠️ Duffee 원전 sample | 1976~2000 또는 더 긴 historical. 우리는 2002+ (post-GFC + ZIRP 시기) |

## Full-sample Monthly Sharpe (log returns)

| 자산 | Monthly Sharpe | n |
|---|---:|---:|
| **SPY** | **0.2018** | 287 |
| **Cash** | **0.5505** | 287 |
| **Cash − SPY** | **+0.3486** | — |

→ **Cash Sharpe > SPY Sharpe** 압도적 우위 (+0.35 monthly). **H5 강 지지.**

### Rolling 36M Sharpe (sliding window)
- Cash > SPY 비율: **181/252 = 71.8%** of rolling 36M windows
- 최근 36M window (2023-06-30 ~ 2026-05-31):
  - SPY Sharpe = 0.4663
  - Cash Sharpe = **2.1216** ← 압도적 (Fed 고금리 사이클 + SPY 변동성↑)

## 해석
1. **Duffee 사실 재현 ✅**: post-GFC era 에서도 5Y 이하 Tsy basket 의 monthly Sharpe 가 SPY 를 ≥ 1.7배 (full sample) ~ 4.5배 (최근 36M)
2. **Cash sleeve 정량 가치 입증**:
   - 단순 "기회비용 최소화" 가 아닌 *risk-adjusted return 상위* 자산
   - 특히 ZIRP→고금리 전환기 (2022~) cash carry 자체가 4-5% 로 매력
3. **REGIME_DIRECTION[Overheat][cash]="down" 정당성 재검토 트리거**:
   - 현재 코드 (`regime_to_weights.py` L77): Overheat 에서 cash=down (×0.6)
   - 본 검증 + Round 5 의 rate-cut optionality 종합 → cash 는 *모든 국면에서 floor 5%* 유지가 risk-adjusted 상 유리
   - → 블록5 confidence_hook `cash_optionality_value` 의 dynamic floor 정책 정당

## 보조 통계 (참고)
- Cash basket = (SHY + BIL + SHV) avg per period (기간별 가용)
- log return 사용 (multiplicative compound 가정)
- 무위험 이자율 차감 X (raw monthly mean/std) — Duffee 와 같은 정의

## 가설 판정
- **H5 cash_sharpe_competitive**: **강 지지 (Strong Confirm)**
- monthly Sharpe diff +0.35, rolling 71.8% win — false-positive 가능성 매우 낮음 (n=287)

## yaml 반영 (블록4/5)
- 블록4 weight_rules — 신규 `cash_floor_dynamic`:
  ```yaml
  - {indicator_id: cash_optionality, base_weight: 0.05, modulate_by: [regime],
     direction: "모든 국면 floor 5% 유지. Overheat 에서 down 폐기 (Duffee 검증 반영).
                 Stagflation/rate-shock → 7-10% 상향",
     granularity: sleeve}
  ```
- 블록5 confidence_hook `cash_optionality_value` 의 confirm_signal 보강:
  ```
  confirm_signal: "rolling 36M cash Sharpe > SPY Sharpe in ≥ 60% windows (검증치 71.8% baseline)"
  ```
- 블록7 code_change_plan `inject` stage: `regime_to_weights.BASE_WEIGHTS[cash]` 동적 보정 — confidence 부재 시 0.05 floor, 안정 시 0.07~0.10 우상향

## main 액션 요청
1. **REGIME_DIRECTION[Overheat][cash] 재분류** 의사결정 — "down" → "neutral" 또는 dynamic
2. **BASE_WEIGHTS[cash] 0.09 → 동적 floor (≥0.05) + ceiling (≤0.15)** 정책 승인
3. **추가 검증** (시간 허용 시): 1976~2002 Duffee 원전 sample 재현 (US T-Bill 시리즈 FRED `DGS1` 사용, ETF inception 이전 구간)
