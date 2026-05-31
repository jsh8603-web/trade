---
tags: [type/validation, study/eq_us_cyclical, hypothesis/H4]
date: 2026-05-30
verdict: PARTIAL (동시 공통원인 입증, 선행성 부재, EBP→VIX 흡수)
n_months: 316
period: 2000-02 ~ 2026-05
---

# H4 검증 — Credit (BAA10Y-AAA10Y 빈자 EBP) + VIX → cyclical excess (공통원인)

## 가설
"EBP(GZ 정본 또는 빈자 IG spread)가 지배적 선행 위험신호; cyclical-defensive excess return을 1~6M 선행한다. VIX 통제 후에도 partial IC 유의."

## 데이터
- **종속**: cyclical-defensive excess (월간, 316M)
- **선행**:
  - **IG spread**: BAA10Y - AAA10Y (FRED, 일별 1983/1986부터 → 월간 평균). ★빈자 EBP proxy (GZ 정본 = TRACE+Merton DD 미적재)
  - **VIX**: VIXCLS 월간 평균
  - **곡선**: T10Y2Y 월간 평균 (보조)

## 결과 (Rank-IC of Δ에 대한 ΔΔ — 차분 사용으로 정상성 확보)
| k (lead M) | d_IG IC (p) | d_VIX IC (p) | partial d_IG\|VIX | partial d_VIX\|IG |
|---|---|---|---|---|
| **k=0 (동시)** | **-0.132 (p=0.019)** ✓ | **-0.378 (p<0.001)** ✓✓ | -0.025 | **-0.343** ✓✓ |
| k=1 | -0.042 (p=0.45) | -0.048 (p=0.40) | -0.038 | -0.041 |
| k=3 | -0.023 (p=0.68) | -0.051 (p=0.37) | -0.045 | -0.031 |
| k=6 | -0.048 (p=0.40) | -0.008 (p=0.89) | -0.046 | +0.017 |

## 해석
1. **동시 효과(k=0) 강력**: ΔIG spread 확대 = cyclical excess return 동시 하락 (rho=-0.13 유의), ΔVIX 확대 = 동시 cyclical 하락 (rho=-0.38 매우 유의).
2. **★VIX가 dominant 공통원인 채널**: VIX 통제 시 IG spread partial IC = -0.025 (사실상 소실). IG 통제 시 VIX partial = -0.343 유지.
3. **lead k≥1 선행성 부재**: 1·3·6M 미래 cyclical return에 대한 신호 모두 IC < 0.05. **즉 EBP/IG spread/VIX 모두 "동시 충격 채널"이지 "선행 지표"가 아니다**.
4. direction.md H4 반증 임계 = "EBP IC < ISM IC OOS" 또는 "VIX 직교화 후 잔차 ρ>0.2 못 달성" → 후자에 가까운 결과.

## 함정 / 한계
- **빈자 EBP는 GZ 정본의 핵심 = Merton DD 정제가 빠진 버전**. 정본은 default risk를 더 정밀하게 제거하므로 잔차가 더 순수한 risk premium. **본 검증은 GZ 정본으로 재검증 시 lead 신호가 살아날 가능성 잔존**.
- BAMLH0A0HYM2(ICE BofA HY OAS)는 2023-05 이후만 가용 → 25년 시계열 검증 불가. 빈자 IG spread로 대체.
- 동시 효과 강함 → cyclical excess는 contemporaneous credit/risk shock의 반사 (forward 예측 X). **이는 timing alpha가 아니라 risk-on/off 베타**.

## 시스템 코드화 결론
- **블록3**: relationships
  - `credit_beta ↔ realized_vol` direct contemp **검증 통과** (실제로 동시 강한 음 상관).
  - 단 `credit/EBP → fwd cyclical excess` lagged direct edge **약화** (선행성 미입증) → prior_strength 0.55 → **lagged 0.2 / contemp 0.5**로 분리.
  - **VIX가 더 강한 공통원인 → glasso prior에서 VIX 노드 추가** + EBP 노드를 VIX로 conditioning.
- **블록4**: `credit_beta` 가중치는 동시 risk-off 방어 신호로 유효 (regime contraction). 그러나 **사전 lead timing alpha 아님** — direction 수정: "리스크오프 동시 cyclical 축소" (lead 기반 아닌 contemp regime detection).
- **블록5**: hypothesis_id=ebp_common_cause → **(부분 확신) flag** (동시 공통원인 통과). lead 부재로 H3/H5 가지치기는 부분만 — H3 가지치기는 안 되고 H5 일부 영향.

## 결론 — H4 verdict
**PARTIAL**: 동시 risk/credit 공통원인은 통과(VIX 지배). 단 **lead-lag forward 예측력 미입증**. 빈자 EBP의 한계와 종속 = cyclical excess의 risk-on/off 베타 성격으로 lead alpha 부재. **GZ 정본 EBP 자체산출(TRACE+Merton DD) 적재 후 재검증 필요**.
