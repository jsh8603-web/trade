---
tags: [type/validation, study/eq_us_cyclical, hypothesis/H3]
date: 2026-05-30
verdict: REJECT (선행성 미입증)
n_months: 315-316
period: 2000-02 ~ 2026-05
---

# H3 검증 — ISM proxy → cyclical-defensive excess return lead-lag

## 가설
"ISM(New Orders - Inventories) 스프레드가 cyclical-defensive 상대수익을 k=1~3M 선행한다. HY OAS·곡선 통제 후 partial IC > 0.10."

## 데이터
- **종속**: 월간 (XLY+XLI+XLB+XLE+XLF)/5 - (XLP+XLU+XLV)/3 = cyclical excess return (yfinance, 2000-2026, 316 month)
- **선행**: 5개 후보 (FRED, ALFRED PIT 정렬은 본 1차 검증엔 미적용 = release-date 미반영, 결과 보수적으로 해석)
  - AMTMNO_YoY (Manufacturers' New Orders YoY)
  - CFNAI (Chicago Fed National Activity Index, ★vintage 미보정)
  - AMTMNO/BUSINV YoY (NO-Inv ratio)
  - NEWORDER_YoY (core capex)
  - DGORDER_YoY (내구재 신규주문)

## 결과 (Rank-IC, k = lead lag in months)
| Lead | n | k=0 | k=1 | k=3 | k=6 |
|---|---|---|---|---|---|
| AMTMNO_YoY | 315 | +0.013 (p=0.82) | +0.015 | -0.038 | -0.046 |
| **CFNAI** | 316 | +0.058 | +0.066 | **+0.099** | +0.018 |
| NO_INV_RATIO_YoY | 315 | +0.057 | +0.057 | +0.025 | -0.032 |
| NEWORDER_YoY | 316 | +0.006 | +0.011 | -0.055 | -0.021 |
| DGORDER_YoY | 316 | +0.053 | +0.080 | +0.027 | +0.017 |

## 평가
- **모든 ISM proxy lead-lag IC < 0.10**. CFNAI k=3M가 +0.099로 최대지만 **p=0.301 (유의 X)**.
- direction.md H3 반증 임계 = "Granger Causality 또는 hit ratio < 60%". 본 단순 IC도 임계 미달.
- 316 month = 26년 표본은 시계열 검정력으로 충분(Newey-West q≥3 보정해도 t-stat 안 살아남는 수준).

## 부분 통과 가능 시나리오 (추후 정밀 검증 필요)
1. **종속 변수 재정의**: 일반 cyclical excess가 아닌 **개별 섹터 = Industrials(XLI) 단독** 또는 **revision breadth 직접 측정** 시 ISM 선행성이 살아날 가능성. 본 평균화가 신호를 희석시킬 수 있음.
2. **ALFRED vintage 보정**: 본 검증은 reference-date 정렬 (실 release-date 미반영). PIT 정렬 시 결과 보수 방향으로 더 약해지지만 정확.
3. **regime conditional**: 평탄한 전체 IC가 contraction 국면 부분 IC로 분해 시 유의해질 가능성 (단 본 검증의 시점-pooling에서는 안 보임).

## 시스템 코드화 결론 (블록3 / 블록4 / 블록5)
- **블록3**: relationships에서 `ism_pmi_sensitivity → fwd_eps_momentum` lagged 가설은 우리 데이터로 **재검증 후 prior_strength 0.6 → 0.3 하향** 또는 conditioning_set 강화 검토. **direct edge 약화**, common_cause 분해 검토.
- **블록4**: `ism_pmi_sensitivity base_weight` 0.06 이하 cap (시스템 leverage 약함 인정). regime modulate 효과 미입증.
- **블록5**: hypothesis_id=ism_pmi_drives_cyclical_eps → **(거부 후보) flag 우세**. confirm 가능성은 (i) 종속을 revision breadth로 (ii) 종속을 산업별 ETF로 분해 (iii) regime conditional 시.

## 결론 — H3 verdict
**REJECT (단순 cyclical excess 선행성 미입증)**. 단 종속 재정의(섹터 단독 / fwd EPS revision / regime conditional)에서 재검증 가능. 시스템 leverage 작아 우선순위 하향.
