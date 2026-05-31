---
tags: [type/candidate-ledger, domain/commodity, purpose/easy-review]
date: 2026-05-31
purpose: 그동안 자문·이론·M3에서 나온 지표 후보 전체 + 채택/미채택/이연 + 사유. 다음 세션이 "뭐가 왜 빠졌나" 한눈에.
note: direction.md / collector_plan(블록6) / theory-notes / audit 에 흩어진 걸 1파일로 집약.
---

# commodity 지표 후보 원장 (candidate ledger)

## ✅ 채택 (yaml indicators 등록 + 검증)
| 지표 | tier | 근거 |
|---|---|---|
| roll_yield | core | Theory of Storage 정의식, force-include 후보 |
| bgr_basis_momentum_12m | core | BGR 2019 검증 시그널 |
| indpro_yoy | structural | copper bellwether spearman 0.40 lag 12m (latest-vintage 잠정, SE 보정 후속) |
| convenience_yield_z | valuation | Working 1949 직접 동치 |
| days_of_supply | macro_sens | 재고 cushion (reflexive 명명 회피) |
| real_rate_dfii10 / dxy_index / vix_level | macro/risk | 거시 driver |
| momentum_12_1 / realized_vol_60d | momentum/risk | AMP 2013 |
| cross_sector_mean_corr_60d | macro_sens | H5 financialization outcome (VIX>30 corr spike 실측) |
| wti_noi_1yr | macro_sens | Hamilton NOI threshold 10% 검증 |
| **china_credit_impulse_z** | **structural_low_confidence** | ★2026-05-31 신규. 실검증 비유의(18 test Bonferroni/HAC/FDR 0 생존) → 방향성 약 prior. INDPRO 보강 conditioning 한정. **audit 충실 통과** |
| **noaa_oni_3m_ma** (ENSO) | **structural_low_confidence** | ★2026-05-31 신규. ONI(El Niño)→곡물 fwd 3-6m 수익률 음(-), wheat/maize/soybean Bonferroni α/18+HAC+block bootstrap 전관문 생존(n=423). **spurious 아님 확정**(ONI I(0) stationary·detrend 불변·placebo). **audit 부분**: predictive 라벨 과장(regime co-movement 혼재, 단 strict-future 유의)·PIT 개정/계절 look-ahead·effective-N<<423 → validated 보류. 보강3(PIT lag·predictive분해·effN) 후 승격 후보 |

## ⏳ 이연 (이론·후보 식별됐으나 collector 미구축 → 미투입)
| 후보 | 사유 (왜 안 들어갔나) | unblock 조건 |
|---|---|---|
| cushing_utilization_pct (H9 storage_limit) | EIA Open Data API collector 미구축 | EIA_API_KEY 발급 + eia_adapter.py |
| stock_to_use_ratio (WASDE, agri) | USDA collector 미구축 + survey consensus 데이터 hardest | USDA_API_KEY + consensus 소스 |
| lme_metal_stocks_z (industrial) | LME 유료 데이터, 1차 stub만 | 유료 도입 정책 결정 |
| mm_net_long_oi_z (H8 speculative) | CFTC DCOT collector 미구축 | cftc_adapter.py (무료 public API) |
| cit_long_position_z (H5 driver) | post-2015 CIT 데이터 단절 (Barclays/Bloomberg AUM 유료) | 분기 AUM 소스 |
| roll_yield/bgr 실데이터 | CME term structure collector 미구축 (현재 prior만) | commodity_futures_term.py |

## ❌ 미채택 / proxy 대체
| 후보 | 사유 |
|---|---|
| Caixin PMI (China 산업수요) | 무료 데이터 없음 → **INDPRO YoY proxy 대체**. ★china_credit_impulse_z 가 부분 보완(단 비유의) |
| StockToFlow 류 | 이론 약함 (commodity 부적합) |
| 30% NOI threshold (Hamilton 원안) | 실측 1건뿐 → 10% threshold 로 정정 채택 |

## 🔬 후속 재검증 falsifier (채택했으나 조건부)
- **china_credit_impulse_z**: BIS stock 비율 proxy 한계 → **TSF(사회융자) flow/GDP** 실데이터 확보 시 재측정. HAC p<0.05 + Bonferroni 생존 시 structural→validated 승격, 미달이면 freeze.
- **indpro_yoy**: overlapping window SE 미보정 → Newey-West/block-bootstrap + lag-selection deflation 후속.
